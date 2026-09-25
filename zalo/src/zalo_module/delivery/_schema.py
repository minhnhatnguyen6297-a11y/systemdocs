"""Vendored JSON Schema subset validator — port of the contract's
``_validator/schema_subset.py`` (contracts/zalo-intake, draft 2020-12 subset),
stdlib-only so the module validates raw records with **the same engine** the
contract validator uses, against the byte-identical schemas in ``schemas/``.

Differences from the contract original: the ``.io`` helpers
(``read_json_bytes``/``ContractDataError``) are inlined as
``_read_schema_bytes`` — only needed to parse trusted local schema files —
and the module exposes ``load_schema``/``validate`` identically.
"""
from __future__ import annotations

import codecs
import json
import math
import operator
import re
import urllib.parse
from datetime import date
from pathlib import Path

SCHEMA_INVALID = "schema_invalid"


class SchemaError(Exception):
    """The schema file itself is broken (bad JSON, bad values, unresolvable $ref)."""


class UnsupportedSchemaKeyword(SchemaError):
    """The schema uses a keyword/format/ref form outside the supported subset."""


class ContractDataError(Exception):
    """Schema file bytes break strict JSON rules; `code` is a stable code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ContractDataError(
                "json_invalid", f"duplicate object key {json.dumps(key)}"
            )
        obj[key] = value
    return obj


def _no_constant(token):
    raise ContractDataError("json_invalid", f"non-finite number {token}")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ContractDataError("json_invalid", "non-finite number (overflow)")
    return value


def _read_schema_bytes(data: bytes):
    """Parse one trusted schema document under the contract strict profile."""
    if data.startswith(codecs.BOM_UTF8):
        raise ContractDataError("json_invalid", "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ContractDataError(
            "json_invalid", f"invalid UTF-8 at byte {e.start}"
        ) from None
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_keys,
            parse_constant=_no_constant,
            parse_float=_finite_float,
        )
    except json.JSONDecodeError as e:
        raise ContractDataError(
            "json_invalid", f"line {e.lineno} column {e.colno}: {e.msg}"
        ) from None


ANNOTATIONS = frozenset({"$schema", "$id", "$comment", "title", "description",
                         "examples", "default"})
SUBSCHEMA_ONE = frozenset({"additionalProperties", "propertyNames", "items",
                           "not", "if", "then", "else"})
SUBSCHEMA_SEQ = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
SUBSCHEMA_MAP = frozenset({"properties", "patternProperties", "$defs"})
NONNEG_INT = frozenset({"minProperties", "maxProperties", "minItems", "maxItems",
                        "minLength", "maxLength"})
NUMBER_BOUND = frozenset({"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"})
SCALARS = frozenset({"type", "enum", "const", "required", "dependentRequired",
                     "uniqueItems", "pattern", "format", "$ref"})
KNOWN = ANNOTATIONS | SUBSCHEMA_ONE | SUBSCHEMA_SEQ | SUBSCHEMA_MAP | NONNEG_INT | NUMBER_BOUND | SCALARS

TYPE_NAMES = ("null", "boolean", "object", "array", "number", "string", "integer")
FORMATS = ("date-time", "uuid")

_TYPES = {
    "null": lambda v: v is None,
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: (isinstance(v, int) and not isinstance(v, bool))
                         or (isinstance(v, float) and v.is_integer()),
}

_BOUNDS = (("minimum", operator.ge), ("maximum", operator.le),
           ("exclusiveMinimum", operator.gt), ("exclusiveMaximum", operator.lt))
_COUNTS = {"str": (("minLength", operator.ge), ("maxLength", operator.le)),
           "list": (("minItems", operator.ge), ("maxItems", operator.le)),
           "dict": (("minProperties", operator.ge), ("maxProperties", operator.le))}

_DATETIME = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})\Z")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def _is_datetime(value):
    m = _DATETIME.match(value)
    if not m:
        return False
    year, month, day, hour, minute, second = (int(g) for g in m.groups()[:6])
    offset = m.group(7)
    try:
        date(year, month, day)
    except ValueError:
        return False
    if not (hour <= 23 and minute <= 59 and second <= 59):
        return False
    if offset != "Z" and not (int(offset[1:3]) <= 23 and int(offset[4:6]) <= 59):
        return False
    return True


def _is_uuid(value):
    return bool(_UUID.match(value))


_FORMAT_CHECKS = {"date-time": _is_datetime, "uuid": _is_uuid}


def _escape(name: str) -> str:
    return name.replace("~", "~0").replace("/", "~1")


def _render(ptr: str) -> str:
    return ptr or "(root)"


def _normkey(v):
    """Hashable, type-strict JSON key: ("num", 1) == ("num", 1.0) but != ("bool", True)."""
    if v is None:
        return ("null",)
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float)):
        return ("num", v)
    if isinstance(v, str):
        return ("str", v)
    if isinstance(v, list):
        return ("arr", tuple(_normkey(i) for i in v))
    return ("obj", frozenset((k, _normkey(val)) for k, val in v.items()))


def _json_equal(a, b):
    return _normkey(a) == _normkey(b)


class Schema:
    """A checked schema document set: nodes per file plus resolved $ref targets."""

    def __init__(self, path, nodes, ref_targets):
        self.path = path
        self.root = nodes[path][""]
        self._nodes = nodes            # Path -> {schema-pointer: schema node}
        self._ref_targets = ref_targets  # id(node) -> (Path, schema-pointer)

    def validate(self, instance):
        """Same as module-level validate(instance, self)."""
        return validate(instance, self)

    def _eval(self, inst, node, loc, code, out):
        if node is True:
            return
        if node is False:
            out.append((code, f"{_render(loc)}: false"))
            return
        code = node.get("x-error-code") or code

        def add(keyword, ptr=None):
            out.append((code, f"{_render(loc if ptr is None else ptr)}: {keyword}"))

        ref = self._ref_targets.get(id(node))
        if ref is not None:
            tfile, tptr = ref
            self._eval(inst, self._nodes[tfile][tptr], loc, code, out)

        t = node.get("type")
        if t is not None:
            names = (t,) if isinstance(t, str) else tuple(t)
            if not any(_TYPES[name](inst) for name in names):
                add("type")
        if "enum" in node and not any(_json_equal(inst, v) for v in node["enum"]):
            add("enum")
        if "const" in node and not _json_equal(inst, node["const"]):
            add("const")

        for sub in node.get("allOf") or ():
            self._eval(inst, sub, loc, code, out)
        if "anyOf" in node and not any(self._passes(inst, sub, loc, code)
                                       for sub in node["anyOf"]):
            add("anyOf")
        if "oneOf" in node:
            good = sum(self._passes(inst, sub, loc, code) for sub in node["oneOf"])
            if good != 1:
                add("oneOf")
        if "not" in node and self._passes(inst, node["not"], loc, code):
            add("not")
        if "if" in node:
            branch = node.get("then") if self._passes(inst, node["if"], loc, code) \
                else node.get("else")
            if branch is not None:
                self._eval(inst, branch, loc, code, out)

        if isinstance(inst, dict):
            self._eval_object(inst, node, loc, code, out, add)
        elif isinstance(inst, list):
            self._eval_array(inst, node, loc, code, out, add)
        elif isinstance(inst, str):
            n = len(inst)
            for kw, op in _COUNTS["str"]:
                if kw in node and not op(n, node[kw]):
                    add(kw)
            if "pattern" in node and not re.search(node["pattern"], inst):
                add("pattern")
            fmt = node.get("format")
            if fmt is not None and not _FORMAT_CHECKS[fmt](inst):
                add("format")
        elif isinstance(inst, (int, float)) and not isinstance(inst, bool):
            for kw, op in _BOUNDS:
                if kw in node and not op(inst, node[kw]):
                    add(kw)

    def _passes(self, inst, sub, loc, code):
        out = []
        self._eval(inst, sub, loc, code, out)
        return not out

    def _eval_object(self, inst, node, loc, code, out, add):
        n = len(inst)
        for kw, op in _COUNTS["dict"]:
            if kw in node and not op(n, node[kw]):
                add(kw)
        props = node.get("properties") or {}
        pats = {p: re.compile(p) for p in (node.get("patternProperties") or {})}
        for key, sub in props.items():
            if key in inst:
                self._eval(inst[key], sub, f"{loc}/{_escape(key)}", code, out)
        for key, value in inst.items():
            for p, rx in pats.items():
                if rx.search(key):
                    self._eval(value, node["patternProperties"][p],
                               f"{loc}/{_escape(key)}", code, out)
        for name in node.get("required") or ():
            if name not in inst:
                add("required", f"{loc}/{_escape(name)}")
        for name, needed in (node.get("dependentRequired") or {}).items():
            if name in inst:
                for other in needed:
                    if other not in inst:
                        add("dependentRequired", f"{loc}/{_escape(other)}")
        if "propertyNames" in node:
            for key in inst:
                sub_errors = []
                self._eval(key, node["propertyNames"],
                           f"{loc}/{_escape(key)}", code, sub_errors)
                for c, _ in sub_errors:
                    out.append((c, f"{_render(loc + '/' + _escape(key))}: propertyNames"))
        if "additionalProperties" in node:
            extra = node["additionalProperties"]
            for key, value in inst.items():
                if key in props or any(rx.search(key) for rx in pats.values()):
                    continue
                ptr = f"{loc}/{_escape(key)}"
                if extra is False:
                    add("additionalProperties", ptr)
                else:
                    self._eval(value, extra, ptr, code, out)

    def _eval_array(self, inst, node, loc, code, out, add):
        n = len(inst)
        for kw, op in _COUNTS["list"]:
            if kw in node and not op(n, node[kw]):
                add(kw)
        prefix = node.get("prefixItems") or ()
        for i, sub in enumerate(prefix[:n]):
            self._eval(inst[i], sub, f"{loc}/{i}", code, out)
        if "items" in node:
            for i in range(len(prefix), n):
                self._eval(inst[i], node["items"], f"{loc}/{i}", code, out)
        if node.get("uniqueItems"):
            seen = set()
            for i, value in enumerate(inst):
                key = _normkey(value)
                if key in seen:
                    add("uniqueItems", f"{loc}/{i}")
                else:
                    seen.add(key)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class _Loader:
    def __init__(self):
        self.nodes = {}        # Path -> {schema-pointer: node}
        self.ref_targets = {}  # id(node) -> (Path, schema-pointer)

    def load(self, path: Path):
        if path in self.nodes:
            return
        try:
            doc = _read_schema_bytes(path.read_bytes())
        except (OSError, ContractDataError) as e:
            raise SchemaError(f"{path}: {e}") from e
        self.nodes[path] = {}
        pending = []
        self._walk(path, doc, "", pending)
        for ptr, ref in pending:
            self._resolve(path, ptr, ref)

    def _walk(self, file, node, ptr, pending):
        if isinstance(node, bool):
            self.nodes[file][ptr] = node
            return
        if not isinstance(node, dict):
            raise SchemaError(f"{file.name}#{ptr or '/'}: a schema must be an object or boolean")
        self.nodes[file][ptr] = node
        for key, value in node.items():
            where = f"{file.name}#{ptr or '/'}"
            if key == "$id":
                if ptr:
                    raise UnsupportedSchemaKeyword(
                        f"{where}: $id is only supported at a schema file root")
                continue
            if key == "x-error-code":
                if not (isinstance(value, str) and value):
                    raise SchemaError(f"{where}: x-error-code must be a non-empty string")
                continue
            if key.startswith("x-") or key in ANNOTATIONS - {"$id"}:
                continue
            if key not in KNOWN:
                raise UnsupportedSchemaKeyword(f"{where}: unsupported keyword {key!r}")
            self._check_value(key, value, where)
            if key == "$ref":
                pending.append((ptr, value))
            elif key in SUBSCHEMA_ONE:
                self._walk(file, value, f"{ptr}/{key}", pending)
            elif key in SUBSCHEMA_SEQ:
                for i, sub in enumerate(value):
                    self._walk(file, sub, f"{ptr}/{key}/{i}", pending)
            elif key in SUBSCHEMA_MAP:
                for name, sub in value.items():
                    self._walk(file, sub, f"{ptr}/{key}/{_escape(name)}", pending)

    def _check_value(self, key, value, where):
        bad = SchemaError(f"{where}: invalid {key} value {value!r}")
        if key == "$ref":
            if not isinstance(value, str):
                raise bad
        elif key == "type":
            names = [value] if isinstance(value, str) else \
                value if isinstance(value, list) else None
            if names is None or not names or len(set(names)) != len(names) or \
                    any(name not in TYPE_NAMES for name in names):
                raise bad
        elif key == "enum":
            if not isinstance(value, list):
                raise bad
        elif key == "required":
            if not (isinstance(value, list) and all(isinstance(s, str) for s in value)
                    and len(set(value)) == len(value)):
                raise bad
        elif key == "dependentRequired":
            if not (isinstance(value, dict) and all(
                    isinstance(k, str) and isinstance(v, list)
                    and all(isinstance(s, str) for s in v)
                    for k, v in value.items())):
                raise bad
        elif key in SUBSCHEMA_SEQ:
            if not (isinstance(value, list) and value):
                raise bad
        elif key in SUBSCHEMA_MAP:
            if not isinstance(value, dict):
                raise bad
            if key == "patternProperties":
                for p in value:
                    try:
                        re.compile(p)
                    except re.error:
                        raise SchemaError(f"{where}: patternProperties key {p!r} does not compile")
        elif key in SUBSCHEMA_ONE:
            pass  # shape checked by _walk
        elif key in NONNEG_INT:
            if not (_is_int(value) and value >= 0):
                raise bad
        elif key in NUMBER_BOUND:
            if not (isinstance(value, (int, float)) and not isinstance(value, bool)):
                raise bad
        elif key == "uniqueItems":
            if not isinstance(value, bool):
                raise bad
        elif key == "pattern":
            if not isinstance(value, str):
                raise bad
            try:
                re.compile(value)
            except re.error:
                raise bad
        elif key == "format":
            if not isinstance(value, str):
                raise bad
            if value not in FORMATS:
                raise UnsupportedSchemaKeyword(
                    f"{where}: unsupported format {value!r} (supported: {', '.join(FORMATS)})")

    def _resolve(self, file, ptr, ref):
        where = f"{file.name}#{ptr or '/'}"
        parts = urllib.parse.urlsplit(ref)
        if parts.scheme or parts.netloc or parts.query:
            raise UnsupportedSchemaKeyword(
                f"{where}: $ref must be '#...' or a relative file, got {ref!r}")
        target = file if not parts.path else (file.parent / urllib.parse.unquote(parts.path)).resolve()
        frag = urllib.parse.unquote(parts.fragment)
        if not frag:
            tptr = ""
        elif frag.startswith("/"):
            tptr = frag
        else:
            raise UnsupportedSchemaKeyword(
                f"{where}: named-anchor $ref {ref!r} is not supported")
        self.load(target)
        if tptr not in self.nodes[target]:
            raise SchemaError(f"{where}: $ref {ref!r} does not point at a schema")
        self.ref_targets[id(self.nodes[file][ptr])] = (target, tptr)


def load_schema(path) -> Schema:
    """Load and fully check the schema file at `path` (resolves + caches referenced files)."""
    loader = _Loader()
    loader.load(Path(path).resolve())
    return Schema(Path(path).resolve(), loader.nodes, loader.ref_targets)


def validate(instance, schema: Schema) -> list:
    """Return sorted, de-duplicated [(code, detail)] failures; [] means the instance is valid."""
    out = []
    schema._eval(instance, schema.root, "", SCHEMA_INVALID, out)
    return sorted(set(out))
