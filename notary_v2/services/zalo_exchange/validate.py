"""Zalo raw-package validation — contract intake.*.v1 (stdlib-only).

Contract SOT: ``contracts/zalo-intake/zalo-intake.md`` §3 (package files,
hashes, canonical form, limits), §4 (byte/JSONL rules), §5 (raw record), §11
(error catalog). Schemas: ``notary_v2/schemas/zalo-intake/`` — vendored
byte-identical copies, DO NOT EDIT.

``jsonschema`` is NOT in requirements.txt, so this module vendors the same
strict JSON Schema draft-2020-12 **subset** engine the producer module uses
(``zalo-intake/src/zalo_module/delivery/_schema.py``, itself a port of
``contracts/zalo-intake/_validator/schema_subset.py``). The strict byte/JSONL
readers port ``contracts/zalo-intake/_validator/io.py`` and the package-level
checks port ``contracts/zalo-intake/_validator/rules_package.py``, so the
consumer runs the identical rule set against identical schema bytes. No new
dependency was added.

Public surface:
    validate_package(pkg_dir, consumer_id=None, ...) -> PackageReport
    read_json_bytes(data) / read_jsonl_records(data) / sha256_hex / canonical_sha256
    load_schema(path) / validate(instance, schema)  (the schema engine)
    ContractDataError(code, detail)

`PackageReport.errors` is a sorted-stable list of ``(code, detail)`` tuples
using the contract §11 catalog. A package with ``errors == []`` passed every
consumer-side intake check (file whitelist, size limits, strict JSON/JSONL
framing, manifest+READY+every-record schema, byte hashes, record_count,
producer/consumer identity, READY↔manifest binding, payload scans).
"""
from __future__ import annotations

import codecs
import hashlib
import json
import math
import operator
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

JSON_INVALID = "json_invalid"
RECORDS_FORMAT_INVALID = "records_format_invalid"
SCHEMA_INVALID = "schema_invalid"

# Repo-rooted vendored schemas — byte-identical to contracts/zalo-intake/*.
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas" / "zalo-intake"

# Quantitative limits — contract §3.6.
MAX_MANIFEST_BYTES = 64 * 1024
MAX_READY_BYTES = 64 * 1024
MAX_RECORDS_BYTES = 16 * 1024 * 1024
MAX_RECORD_COUNT = 1000
MAX_RECEIPT_BYTES = 16 * 1024
MAX_OCR_REQUEST_BYTES = 16 * 1024

# A v1 raw package is exactly three flat files (contract §3.2).
PACKAGE_FILES = ("manifest.json", "records.jsonl", "READY.json")

# manifest.files[] can only ever declare records.jsonl: a manifest cannot hash
# itself, and READY.json is written after the manifest is final (contract §3.3).
DECLARABLE = frozenset({"records.jsonl"})

_PACKAGE_NAMES_LOWER = {n.lower() for n in PACKAGE_FILES}

# Names that carry protocol meaning elsewhere and must never sit inside a
# package (results.json is the retired pre-v1 payload; receipt.json is an API
# object — contract §3.2/§7.3).
_FORBIDDEN_NAMES_LOWER = {"results.json", "receipt.json"}

# Packages carry OCR text/status/metadata only — never image bytes.
_IMAGE_EXT = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff",
    ".heic", ".heif", ".svg", ".ico",
})
# Executables/scripts inside a data package are a security problem, not a
# format deviation — hence file_forbidden rather than file_unexpected.
_EXEC_EXT = frozenset({
    ".exe", ".dll", ".com", ".scr", ".msi", ".msp", ".bat", ".cmd", ".ps1",
    ".psm1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta", ".jar",
    ".apk", ".py", ".pyc", ".pyo", ".sh", ".cpl", ".msc", ".reg",
})


# ============================================================================
# Strict byte/JSON profile — port of contracts/zalo-intake/_validator/io.py
# (contract §4). Documents are handled as bytes; parsing enforces UTF-8
# without BOM, unique object keys and finite numbers.
# ============================================================================


class ContractDataError(Exception):
    """Document bytes break the contract's byte/JSON rules; `code` is a stable error code."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ContractDataError(JSON_INVALID, f"duplicate object key {json.dumps(key)}")
        obj[key] = value
    return obj


def _no_constant(token):
    raise ContractDataError(JSON_INVALID, f"non-finite number {token}")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ContractDataError(JSON_INVALID, "non-finite number (overflow)")
    return value


def _loads(text: str, syntax_code: str, line: int | None = None):
    """json.loads with the strict profile (unique keys, finite numbers); `line` = JSONL line number."""
    try:
        return json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_no_constant,
                          parse_float=_finite_float)
    except json.JSONDecodeError as e:
        raise ContractDataError(syntax_code, f"line {line or e.lineno} column {e.colno}: {e.msg}") from None
    except ContractDataError as e:
        if line is None:
            raise
        raise ContractDataError(e.code, f"line {line}: {e.detail}") from None


def read_json_bytes(data: bytes):
    """Parse one JSON document: UTF-8 without BOM, unique keys, no NaN/Infinity, no trailing data."""
    if data.startswith(codecs.BOM_UTF8):
        raise ContractDataError(JSON_INVALID, "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ContractDataError(JSON_INVALID, f"invalid UTF-8 at byte {e.start}") from None
    return _loads(text, JSON_INVALID)


def _records_error(line: int, why: str) -> ContractDataError:
    return ContractDataError(RECORDS_FORMAT_INVALID, f"line {line}: {why}")


def read_jsonl_records(data: bytes) -> list:
    """Parse JSON Lines into ``[(parsed_object, raw_line_text)]``.

    Contract §4 framing: UTF-8 without BOM, every line (the last too) ends
    with ``\\n``, no ``\\r``, no empty line, each line exactly one JSON
    object. An empty file has no records. `raw_line_text` is the verbatim
    line (newline stripped) — stored unchanged as ZaloRawRecord.payload_json.
    """
    if data.startswith(codecs.BOM_UTF8):
        raise _records_error(1, "UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise _records_error(data.count(b"\n", 0, e.start) + 1, "invalid UTF-8") from None
    if "\r" in text:
        raise _records_error(text.count("\n", 0, text.index("\r")) + 1, "carriage return is not allowed")
    lines = text.split("\n")
    if lines[-1]:
        raise _records_error(len(lines), "missing final newline")
    records = []
    for number, line in enumerate(lines[:-1], 1):
        if not line:
            raise _records_error(number, "empty line")
        value = _loads(line, RECORDS_FORMAT_INVALID, number)
        if not isinstance(value, dict):
            raise _records_error(number, "not a JSON object")
        records.append((value, line))
    return records


def read_jsonl_bytes(data: bytes) -> list:
    """JSON Lines → list of parsed objects (same framing rules)."""
    return [obj for obj, _ in read_jsonl_records(data)]


def sha256_hex(data: bytes) -> str:
    """Lowercase hex SHA-256 of the exact bytes (contract §3.5)."""
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj) -> str:
    """SHA-256 of the sorted-key, compact, UTF-8 JSON of obj (Python json, not RFC 8785)."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256_hex(text.encode("utf-8"))


# ============================================================================
# JSON Schema subset engine — port of the contract validator
# (contracts/zalo-intake/_validator/schema_subset.py) exactly as vendored by
# the producer module (zalo-intake/src/zalo_module/delivery/_schema.py).
# Supported keywords: annotations, $defs/$ref (same-file or relative-file),
# type/enum/const, object/array/string/number keywords, allOf/anyOf/oneOf/
# not/if/then/else, x-error-code, formats date-time + uuid. Anything else is
# rejected at schema-load time — never silently ignored.
# ============================================================================


class SchemaError(Exception):
    """The schema file itself is broken (bad JSON, bad values, unresolvable $ref)."""


class UnsupportedSchemaKeyword(SchemaError):
    """The schema uses a keyword/format/ref form outside the supported subset."""


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
            doc = read_json_bytes(path.read_bytes())
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


# ============================================================================
# Vendored schema registry — schemas/zalo-intake/*.schema.json, lazy + cached.
# ============================================================================

_schemas: dict = {}


def _schema(name: str) -> Schema:
    """Load a vendored schema by file name (e.g. "manifest.schema.json")."""
    schema = _schemas.get(name)
    if schema is None:
        schema = load_schema(SCHEMAS_DIR / name)
        _schemas[name] = schema
    return schema


def manifest_schema() -> Schema:
    return _schema("manifest.schema.json")


def ready_schema() -> Schema:
    return _schema("ready.schema.json")


def raw_record_schema() -> Schema:
    return _schema("raw-record.schema.json")


def receipt_schema() -> Schema:
    return _schema("receipt.schema.json")


def package_list_schema() -> Schema:
    return _schema("package-list.schema.json")


def service_status_schema() -> Schema:
    return _schema("service-status.schema.json")


def ocr_request_schema() -> Schema:
    return _schema("ocr-request.schema.json")


def ocr_request_status_schema() -> Schema:
    return _schema("ocr-request-status.schema.json")


# ============================================================================
# Record-level payload scans — ported from the contract validator
# (rules_record.py): image bytes/URL/path and provider raw-payload keys are
# contract violations anywhere in a record, not data to ignore (§1, §11.3).
# Kind-body exclusivity (§5.4) is a context-free rule and also enforced here.
# ============================================================================

_PROVIDER_KEYS = frozenset({"provider_raw", "provider_response", "raw_response"})
_IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".pdf")
_BASE64 = re.compile(r"[A-Za-z0-9+/=]+\Z")

_BODY_KEYS = ("message", "ocr", "status", "event", "listener",
              "image_sha256", "image_expires_at", "image_state")
_KIND_BODIES = {
    "message_text": frozenset({"message"}),
    "ocr_page": frozenset({"ocr", "image_sha256", "image_expires_at",
                           "image_state"}),
    "processing_status": frozenset({"status"}),
    "source_event": frozenset({"event"}),
    "listener_session": frozenset({"listener"}),
}


def _is_image_payload(value: str) -> bool:
    low = value.lower()
    if "data:image" in low:
        return True
    for token in value.split():
        t = token.lower()
        # URL ending in an image/document extension
        if t.startswith(("http://", "https://")) and t.endswith(_IMG_EXTS):
            return True
        # filesystem path ("/" or "\\" inside) ending in an image/document extension
        if ("/" in t or "\\" in t) and t.endswith(_IMG_EXTS):
            return True
    # long pure-base64 blob (whitespace tolerated for wrapped encodings)
    compact = re.sub(r"\s", "", value)
    return len(compact) >= 128 and bool(_BASE64.fullmatch(compact))


def _scan_payloads(node, ptr, out):
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{ptr}/{key}"
            if isinstance(key, str) and key.lower() in _PROVIDER_KEYS:
                out.append(("provider_payload_forbidden",
                            f"{child}: provider payload key is not allowed in a record"))
            _scan_payloads(value, child, out)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _scan_payloads(value, f"{ptr}/{i}", out)
    elif isinstance(node, str) and _is_image_payload(node):
        out.append(("image_payload_forbidden",
                    f"{ptr or '(root)'}: image bytes/URL/path are not allowed in a record"))


# ---------------------------------------------------------------------------
# Relational/semantic rules — context-free part of rules_record._record_rules
# (port). Rules that need store context — supersedes target membership,
# revision dedupe — live in services.zalo_exchange.store.check_record_conflicts.
# ---------------------------------------------------------------------------

IMAGE_TTL = timedelta(hours=168)   # image_expires_at == captured_at + 168h (§5.3)

_ISO = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.([0-9]+))?(Z|[+-][0-9]{2}:[0-9]{2})\Z")


def _parse_iso(value):
    """Contract ISO-8601 -> aware datetime, or None (mirrors _is_datetime's
    profile; falls back to fromisoformat so rules stay total on bad input)."""
    if not isinstance(value, str):
        return None
    m = _ISO.match(value)
    if not m:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    year, month, day, hh, mm, ss = (int(g) for g in m.groups()[:6])
    frac = m.group(7) or ""
    micro = int((frac + "000000")[:6]) if frac else 0
    off = m.group(8)
    if off == "Z":
        tz = timezone.utc
    else:
        sign = 1 if off[0] == "+" else -1
        tz = timezone(sign * timedelta(hours=int(off[1:3]), minutes=int(off[4:6])))
    try:
        return datetime(year, month, day, hh, mm, ss, micro, tzinfo=tz)
    except ValueError:
        return None


def _ocr_rules(rec, out):
    """OCR internal consistency — port of rules_record._ocr_rules."""
    ocr = rec.get("ocr")
    if not isinstance(ocr, dict):
        return
    attempts = [a for a in (ocr.get("attempts") or []) if isinstance(a, dict)]
    lines = [l for l in (ocr.get("text_lines") or []) if isinstance(l, dict)]
    by_pass = {}
    for a in attempts:
        pid = a.get("ocr_pass_id")
        if isinstance(pid, str) and pid not in by_pass:
            by_pass[pid] = a

    for a in attempts:
        where = f"/ocr/attempts (ocr_pass_id={a.get('ocr_pass_id')!r})"
        pls = a.get("provider_lines")
        if a.get("task") == "text_recognition" and (
                a.get("geometry_status") != "not_applicable" or pls):
            out.append(("geometry_invalid",
                        f"{where}: task text_recognition cannot carry geometry — "
                        "geometry_status must be not_applicable and provider_lines absent"))
        gs = a.get("geometry_status")
        if gs in ("not_applicable", "absent") and pls:
            out.append(("geometry_invalid",
                        f"{where}: geometry_status {gs} cannot carry provider_lines"))
        if isinstance(gs, str) and gs.startswith("present_") and (
                not isinstance(a.get("submitted_frame"), dict) or not pls):
            out.append(("geometry_frame_mismatch",
                        f"{where}: geometry_status {gs} requires submitted_frame and a "
                        "non-empty provider_lines"))

    status = ocr.get("status")
    any_succeeded = any(a.get("status") == "succeeded" for a in attempts)
    if status == "succeeded":
        if not lines:
            out.append(("ocr_status_inconsistent",
                        "/ocr/status: succeeded but text_lines is empty/absent"))
        if not any_succeeded:
            out.append(("ocr_status_inconsistent",
                        "/ocr/status: succeeded but no attempt succeeded"))
    if status == "failed" and (lines or any_succeeded):
        out.append(("ocr_status_inconsistent",
                    "/ocr/status: failed but the record still carries text_lines or a "
                    "succeeded attempt"))
    if lines and not any_succeeded:
        out.append(("ocr_status_inconsistent",
                    "/ocr/text_lines: lines present but no attempt succeeded"))

    for i, pid in enumerate(ocr.get("selected_pass_ids") or []):
        if pid not in by_pass:
            out.append(("line_pass_ref_unknown",
                        f"/ocr/selected_pass_ids/{i}: {pid!r} is not an "
                        "ocr_pass_id of this record"))

    for i, line in enumerate(lines):
        pid = line.get("ocr_pass_id")
        att = by_pass.get(pid)
        if att is None:
            out.append(("line_pass_ref_unknown",
                        f"/ocr/text_lines/{i}/ocr_pass_id: {pid!r} is not an "
                        "ocr_pass_id of this record"))
            continue
        valid_idx = {p.get("element_index") for p in (att.get("provider_lines") or [])
                     if isinstance(p, dict)}
        for j, ref in enumerate(line.get("provider_refs") or []):
            if ref not in valid_idx:
                out.append(("provider_ref_unknown",
                            f"/ocr/text_lines/{i}/provider_refs/{j}: element_index "
                            f"{ref!r} not in provider_lines of pass {pid!r}"))


def _source_event_rules(rec, out):
    """Port of rules_record._source_event_rules."""
    if rec.get("record_kind") != "source_event":
        return
    ev = rec.get("event")
    if not isinstance(ev, dict):
        return
    if not ev.get("target_provider_message_id"):
        out.append(("source_event_invalid",
                    "/event/target_provider_message_id: recall/reaction events must "
                    "reference the target provider message"))
    etype = ev.get("event_type")
    if etype == "reaction":
        icon = ev.get("reaction_icon")
        if not isinstance(icon, str) or not 1 <= len(icon) <= 64:
            out.append(("source_event_invalid",
                        "/event/reaction_icon: reaction events must carry an icon of "
                        "1-64 characters"))
    elif etype == "recall" and "reaction_icon" in ev:
        out.append(("source_event_invalid",
                    "/event/reaction_icon: only allowed on reaction events"))


def _listener_rules(rec, out):
    """Port of rules_record._listener_rules."""
    if rec.get("record_kind") != "listener_session":
        return
    lis = rec.get("listener")
    if not isinstance(lis, dict):
        return
    gap = lis.get("uncertain_gap")
    if not isinstance(gap, dict):
        return
    if lis.get("state") != "connected":
        out.append(("listener_gap_invalid",
                    "/listener/uncertain_gap: only allowed when state is connected"))
    if gap.get("start_is_estimate") is not True:
        out.append(("listener_gap_invalid",
                    "/listener/uncertain_gap/start_is_estimate: must be true — a gap "
                    "start after a crash is always an estimate"))
    start, end = _parse_iso(gap.get("started_at")), _parse_iso(gap.get("ended_at"))
    if start is None or end is None or not start < end:
        out.append(("listener_gap_invalid",
                    "/listener/uncertain_gap: started_at must be before ended_at"))


def _record_rules(rec, out):
    """Context-free semantic rules for a schema-clean record — port of
    rules_record._record_rules minus its context (ctx) lookups."""
    if not isinstance(rec, dict):
        return

    allowed = _KIND_BODIES.get(rec.get("record_kind"))
    if allowed is not None:
        for key in _BODY_KEYS:
            if key not in allowed and rec.get(key) is not None:
                out.append(("kind_body_mismatch",
                            f"/{key}: not allowed on record_kind "
                            f"{rec.get('record_kind')} (non-null)"))

    # image_expires_at == captured_at + 168h exactly
    if "image_expires_at" in rec:
        cap = _parse_iso(rec.get("captured_at"))
        exp = _parse_iso(rec.get("image_expires_at"))
        if cap is None or exp is None or exp - cap != IMAGE_TTL:
            out.append(("expires_mismatch",
                        "/image_expires_at: must equal captured_at + 168h "
                        f"(captured_at={rec.get('captured_at')!r}, "
                        f"image_expires_at={rec.get('image_expires_at')!r})"))

    # revision/supersedes chain — the context-free half (schema already
    # requires supersedes when revision>1); target membership is checked
    # against the store by store.check_record_conflicts.
    rev = rec.get("revision")
    sup = rec.get("supersedes")
    if isinstance(rev, int) and not isinstance(rev, bool):
        if rev > 1:
            if not isinstance(sup, dict) or sup.get("revision") != rev - 1:
                out.append(("revision_chain_broken",
                            f"/supersedes: revision {rev} must point at revision "
                            f"{rev - 1} of a known prior record"))
        elif sup is not None:
            out.append(("revision_chain_broken",
                        "/supersedes: a revision 1 record has nothing to supersede"))

    _ocr_rules(rec, out)
    _source_event_rules(rec, out)
    _listener_rules(rec, out)


def validate_record(rec) -> list:
    """Schema + payload scans + context-free semantic rules for one record.

    Mirrors contract check_record ordering: schema structure first, payload
    scans next (they guard free-form fields the schema cannot see), then the
    semantic rules run only when the record is clean so far. Cross-record
    rules (supersedes target membership, revision dedupe against the store)
    are the importer's job — see store.check_record_conflicts.
    """
    errors = []
    for code, detail in validate(rec, raw_record_schema()):
        errors.append((code, f"record {detail}"))
    if isinstance(rec, dict):
        _scan_payloads(rec, "", errors)
    if errors:
        return errors
    _record_rules(rec, errors)
    return errors


# ============================================================================
# Package envelope checks — port of rules_package._check_package_dir plus
# per-record validation (the consumer gate checks record content, the
# contract `package` kind only checks framing — decision sheet requires more).
# ============================================================================


@dataclass
class PackageReport:
    """Outcome of validate_package(): parsed documents + structured errors."""
    errors: list = field(default_factory=list)   # [(code, detail)]
    manifest: dict | None = None                 # schema-valid manifest or None
    manifest_raw: dict | None = None             # parsed (maybe schema-invalid) manifest
    manifest_bytes: bytes | None = None
    ready: dict | None = None
    records: list | None = None                  # parsed record objects (framing ok)
    record_lines: list | None = None             # verbatim line text per record

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def manifest_sha256(self) -> str | None:
        if self.manifest_bytes is None:
            return None
        return sha256_hex(self.manifest_bytes)

    @property
    def record_count(self) -> int:
        if self.records is not None:
            return len(self.records)
        return 0


def _classify_file(name):
    """Whitelist verdict for one top-level package file -> (code, why) | (None, '')."""
    if set(name) <= {"."} or ".." in name:
        return "file_forbidden", "dot-segment names are not safe basenames"
    if name in PACKAGE_FILES:
        return None, ""
    low = name.lower()
    if low in _PACKAGE_NAMES_LOWER:
        return "file_forbidden", "case-variant of a package file name breaks on Windows"
    if low in _FORBIDDEN_NAMES_LOWER:
        return "file_forbidden", "protocol payload that must not travel inside a package"
    ext = low[low.rfind("."):] if "." in low else ""
    if ext in _IMAGE_EXT:
        return "file_forbidden", "image bytes never travel inside a package"
    if ext in _EXEC_EXT:
        return "file_forbidden", "executable/script content is not package data"
    return "file_unexpected", "not one of the three raw package files"


def _parse_json_file(data, label, max_bytes, schema, errors):
    """Size limit + strict JSON + schema for one document file.

    Appends errors and returns (parsed_object, n_schema_errors); parsed_object
    is None when the size limit or strict-JSON read failed.
    """
    if len(data) > max_bytes:
        errors.append(("size_limit_exceeded",
                       f"{label} is {len(data)} bytes (limit {max_bytes})"))
        return None, 0
    try:
        obj = read_json_bytes(data)
    except ContractDataError as e:
        errors.append((e.code, f"{label}: {e.detail}"))
        return None, 0
    schema_errors = validate(obj, schema)
    for code, detail in schema_errors:
        errors.append((code, f"{label} {detail}"))
    return obj, len(schema_errors)


def _parse_records_file(data, errors):
    """Size limit + JSONL framing + per-record schema/rules.

    Returns ``[(obj, raw_line)]`` or None. Record content validation is the
    consumer gate (decision sheet): every line must satisfy the raw-record
    schema plus the context-free payload/kind-body rules.
    """
    if len(data) > MAX_RECORDS_BYTES:
        errors.append(("size_limit_exceeded",
                       f"records.jsonl is {len(data)} bytes (limit {MAX_RECORDS_BYTES})"))
        return None
    try:
        records = read_jsonl_records(data)
    except ContractDataError as e:
        errors.append((e.code, f"records.jsonl: {e.detail}"))
        return None
    if len(records) > MAX_RECORD_COUNT:
        errors.append(("size_limit_exceeded",
                       f"records.jsonl holds {len(records)} records (limit {MAX_RECORD_COUNT})"))
    for number, (rec, _raw) in enumerate(records, 1):
        for code, detail in validate_record(rec):
            errors.append((code, f"records.jsonl line {number}: {detail}"))
    return records


def validate_package(pkg_dir, *, consumer_id=None, expected_sequence=None,
                     previously_imported=None, ignore=frozenset()) -> PackageReport:
    """Run every consumer-side intake check on one package directory.

    Order and codes follow contract §11 (rules_package port): file whitelist,
    byte limits, strict JSON/JSONL framing, manifest/READY/record schema,
    manifest-declared hashes and sizes, record_count, producer/consumer
    identity, READY↔manifest binding and the optional sync context
    (expected_sequence, previously_imported for package_conflict).

    Never raises on bad input — a malformed package yields errors, not
    exceptions. I/O failures reading directory entries surface as
    ``file_missing``/``file_unexpected`` style errors where possible.
    """
    pkg_dir = Path(pkg_dir)
    report = PackageReport()
    errors = report.errors

    # --- inventory: flat whitelist, forbidden names, nested paths ----------
    present = {}
    for path in sorted(p for p in pkg_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(pkg_dir).as_posix()
        if rel in ignore:
            continue
        if "/" in rel:
            errors.append(("file_forbidden",
                           f"{rel}: package files must be flat (no directories)"))
            continue
        try:
            present[rel] = path.read_bytes()
        except OSError as e:
            errors.append(("file_missing", f"{rel}: unreadable ({e})"))
            continue
        code, why = _classify_file(rel)
        if code:
            errors.append((code, f"{rel}: {why}"))
    for entry in sorted(pkg_dir.iterdir(), key=lambda e: e.name):
        if entry.is_dir():
            errors.append(("file_forbidden",
                           f"{entry.name}/: directories are not allowed inside a package"))
    for name in PACKAGE_FILES:
        if name not in present:
            errors.append(("file_missing", f"{name}: required package file is absent"))

    # --- parse the three documents ------------------------------------------
    manifest_bytes = present.get("manifest.json")
    report.manifest_bytes = manifest_bytes
    manifest = None
    if manifest_bytes is not None:
        manifest_raw, n_err = _parse_json_file(
            manifest_bytes, "manifest.json", MAX_MANIFEST_BYTES,
            manifest_schema(), errors)
        report.manifest_raw = manifest_raw if isinstance(manifest_raw, dict) else None
        if isinstance(manifest_raw, dict) and n_err == 0:
            manifest = manifest_raw
    report.manifest = manifest

    records = None
    if "records.jsonl" in present:
        records = _parse_records_file(present["records.jsonl"], errors)
    if records is not None:
        report.records = [obj for obj, _raw in records]
        report.record_lines = [raw for _obj, raw in records]

    ready = None
    if "READY.json" in present:
        ready_raw, n_err = _parse_json_file(
            present["READY.json"], "READY.json", MAX_READY_BYTES,
            ready_schema(), errors)
        if isinstance(ready_raw, dict) and n_err == 0:
            ready = ready_raw
    report.ready = ready

    # --- manifest-driven checks (only on a schema-valid manifest) -----------
    if manifest is not None:
        declared = set()
        for entry in manifest["files"]:
            path = entry["path"]
            if path not in DECLARABLE:
                errors.append(("file_forbidden",
                               f"manifest.json files[] entry {path!r}: "
                               "only records.jsonl may be declared"))
                continue
            declared.add(path)
            data = present.get(path)
            if data is None:
                errors.append(("file_missing",
                               f"{path}: declared in manifest but absent from the package"))
                continue
            if sha256_hex(data) != entry["sha256"]:
                errors.append(("manifest_hash_mismatch",
                               f"{path}: sha256 does not match manifest"))
            if len(data) != entry["bytes"]:
                errors.append(("size_mismatch",
                               f"{path}: manifest declares {entry['bytes']} "
                               f"bytes, file holds {len(data)}"))
        for name in DECLARABLE:
            if name in present and name not in declared:
                errors.append(("file_unexpected",
                               f"{name}: on disk but not declared in manifest files[]"))
        if records is not None and manifest["record_count"] != len(records):
            errors.append(("record_count_mismatch",
                           f"manifest record_count is {manifest['record_count']} "
                           f"but records.jsonl has {len(records)} lines"))
        if consumer_id is not None and manifest["consumer_id"] != consumer_id:
            errors.append(("consumer_mismatch",
                           f"manifest consumer_id {manifest['consumer_id']} "
                           f"!= expected {consumer_id}"))
        if manifest["producer"].get("service") != "zalo-intake":
            errors.append(("producer_mismatch",
                           f"producer.service is {manifest['producer'].get('service')!r}, "
                           "expected 'zalo-intake'"))
        if expected_sequence is not None and manifest["sequence"] != expected_sequence:
            errors.append(("sequence_invalid",
                           f"manifest sequence is {manifest['sequence']}, "
                           f"expected {expected_sequence}"))
        for prev in previously_imported or []:
            if not isinstance(prev, dict):
                continue
            if prev.get("package_id") == manifest["package_id"] \
                    and prev.get("manifest_sha256") != sha256_hex(manifest_bytes):
                errors.append(("package_conflict",
                               f"package_id {manifest['package_id']} was already "
                               "imported under a different manifest hash"))

    # --- READY binds the manifest bytes (independent of manifest validity) --
    if ready is not None and manifest_bytes is not None:
        if ready["manifest_sha256"] != sha256_hex(manifest_bytes):
            errors.append(("ready_hash_mismatch",
                           "READY.json manifest_sha256 does not equal sha256(manifest.json)"))
        elif report.manifest_raw is not None \
                and report.manifest_raw.get("package_id") is not None \
                and ready["package_id"] != report.manifest_raw["package_id"]:
            errors.append(("ready_hash_mismatch",
                           "READY.json package_id does not match manifest.json package_id"))

    return report
