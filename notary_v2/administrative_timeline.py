"""Local administrative ledger. No customer data, DB access, or third party deps."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import date, datetime
import hashlib
import gzip
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FOLDER = Path(__file__).parent / "data" / "administrative_units"
SCHEMA = ROOT / "contracts" / "administrative-timeline" / "ledger.schema.json"
COLLECTIONS = ("sources", "units", "names", "parents", "codes", "mentions", "events", "observations")
BASE_URL = "https://sapnhap.bando.com.vn"


class LedgerError(ValueError):
    """Input cannot safely be recorded."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def empty_ledger() -> dict:
    return {"schema_version": "1.0", "revision": 0, "dataset_version": None,
            "coverage": {}, **{key: [] for key in COLLECTIONS}}


def read_ledger(folder: Path, *, initialize=False) -> dict:
    path = folder / "ledger.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if initialize:
        return empty_ledger()
    raise LedgerError(f"stored ledger missing: {path}; initialize with import-bando")


def _shape(value, schema, definitions, path="ledger"):
    if "$ref" in schema:
        schema = definitions[schema["$ref"].split("/")[-1]]
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    predicates = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
                  "string": lambda x: isinstance(x, str), "integer": lambda x: type(x) is int,
                  "null": lambda x: x is None, "boolean": lambda x: type(x) is bool}
    if kinds and not any(predicates[k](value) for k in kinds):
        raise LedgerError(f"{path}: expected {kinds}")
    if "enum" in schema and value not in schema["enum"]:
        raise LedgerError(f"{path}: invalid value {value!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise LedgerError(f"{path}: empty string")
        if len(value) > schema.get("maxLength", len(value)):
            raise LedgerError(f"{path}: string too long")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise LedgerError(f"{path}: invalid format")
    if type(value) is int and value < schema.get("minimum", value):
        raise LedgerError(f"{path}: below minimum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        missing = set(schema.get("required", [])) - value.keys()
        if missing or (schema.get("additionalProperties") is False and value.keys() - props.keys()):
            raise LedgerError(f"{path}: missing/unknown fields {missing or value.keys() - props.keys()}")
        for key, item in value.items():
            if key in props:
                _shape(item, props[key], definitions, f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise LedgerError(f"{path}: too few items")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            raise LedgerError(f"{path}: repeated items")
        for index, item in enumerate(value):
            _shape(item, schema.get("items", {}), definitions, f"{path}[{index}]")


def _day(value):
    if value is not None:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise LedgerError(f"invalid date {value}: use YYYY-MM-DD")
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise LedgerError(f"invalid date {value}") from exc


def _overlap(a, b):
    # Only bounded-start confirmed periods support confident overlap checking.
    return a["valid_from"] is not None and b["valid_from"] is not None and (
        (b["valid_to"] is None or a["valid_from"] < b["valid_to"]) and
        (a["valid_to"] is None or b["valid_from"] < a["valid_to"]))


def validate(ledger: dict, folder: Path | None = None) -> dict:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    _shape(ledger, schema, schema["$defs"])
    indexes = {}
    for key in COLLECTIONS:
        indexes[key] = {row["id"]: row for row in ledger[key]}
        if len(indexes[key]) != len(ledger[key]):
            raise LedgerError(f"{key}: duplicate id")
    units, sources = indexes["units"], indexes["sources"]
    source_keys = [u["source_key"] for u in units.values() if u["source_key"] is not None]
    if len(source_keys) != len(set(source_keys)):
        raise LedgerError("duplicate current source_key; do not infer historical identity")
    for source in sources.values():
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["retrieved_at"]):
                date.fromisoformat(source["retrieved_at"])
            else:
                parsed = datetime.fromisoformat(source["retrieved_at"])
                if parsed.utcoffset() is None:
                    raise ValueError("timezone required")
        except ValueError as exc:
            raise LedgerError(f"{source['id']}: invalid retrieval timestamp") from exc
        snapshot = source["snapshot"]
        if snapshot is not None:
            relative = Path(snapshot)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "snapshots":
                raise LedgerError("unsafe snapshot path")
            if folder is not None:
                path = folder / relative
                if not path.is_file() or digest(path.read_bytes()) != source["sha256"]:
                    raise LedgerError(f"{source['id']}: snapshot missing/hash mismatch")
    for key in COLLECTIONS[1:]:
        for row in ledger[key]:
            for evidence in row["evidence"]:
                if evidence["source_id"] not in sources:
                    raise LedgerError(f"{row['id']}: dangling source")
            if key != "units" and "unit_id" in row and row["unit_id"] not in units:
                raise LedgerError(f"{row['id']}: dangling unit")
            for field in ("valid_from", "valid_to", "effective_on"):
                if field in row:
                    _day(row[field])
            if "valid_from" in row and row["valid_from"] and row["valid_to"] and row["valid_from"] >= row["valid_to"]:
                raise LedgerError(f"{row['id']}: empty/reversed interval")
            if key in ("names", "parents", "codes") and row["status"] == "confirmed" and row["valid_from"] is None:
                raise LedgerError(f"{row['id']}: confirmed period needs sourced start date")
            if key == "mentions" and row["resolved_unit_id"] is not None and row["resolved_unit_id"] not in units:
                raise LedgerError(f"{row['id']}: dangling resolved mention")
            if key == "mentions" and row["status"] == "confirmed" and row["resolved_unit_id"] is None:
                raise LedgerError(f"{row['id']}: confirmed mention requires explicit resolved identity")
            if key == "parents":
                if row["parent_id"] not in units:
                    raise LedgerError(f"{row['id']}: dangling parent")
                rank = {"province": 0, "district": 1, "commune": 2}
                if rank[units[row["parent_id"]]["level"]] >= rank[units[row["unit_id"]]["level"]]:
                    raise LedgerError(f"{row['id']}: parent level/cycle invalid")
    for key, groupfield in (("names", "unit_id"), ("parents", "unit_id"), ("codes", "unit_id")):
        grouped = {}
        for row in ledger[key]:
            if row["event_id"] is not None and row["event_id"] not in indexes["events"]:
                raise LedgerError(f"{row['id']}: dangling event")
            if row["event_id"] is not None:
                event_refs = indexes["events"][row["event_id"]]
                if not any(r == {"kind": "unit", "id": row["unit_id"]} for r in event_refs["from"] + event_refs["to"]):
                    raise LedgerError(f"{row['id']}: assertion unit unrelated to event")
            if row["status"] == "confirmed":
                group = grouped.setdefault(row[groupfield], [])
                if any(_overlap(row, old) for old in group):
                    raise LedgerError(f"{row['id']}: overlapping confirmed {key}")
                group.append(row)
    code_groups = {}
    for row in ledger["codes"]:
        if row["status"] == "confirmed":
            group = code_groups.setdefault((units[row["unit_id"]]["level"], row["value"]), [])
            if any(old["unit_id"] != row["unit_id"] and _overlap(row, old) for old in group):
                raise LedgerError(f"{row['id']}: overlapping code reuse")
            group.append(row)
    graph = {}
    confirmed_events = []
    for event in ledger["events"]:
        for side in ("from", "to"):
            for ref in event[side]:
                target = indexes["units" if ref["kind"] == "unit" else "mentions"].get(ref["id"])
                if target is None:
                    raise LedgerError(f"{event['id']}: dangling {side} reference")
        if event["status"] != "confirmed":
            continue
        confirmed_events.append(event)
        if event["effective_on"] is None or any(r["kind"] != "unit" for r in event["from"] + event["to"]):
            raise LedgerError(f"{event['id']}: confirmed event needs date and verified units")
        incoming, outgoing = {r["id"] for r in event["from"]}, {r["id"] for r in event["to"]}
        if len({units[x]["level"] for x in incoming | outgoing}) > 1:
            raise LedgerError(f"{event['id']}: incompatible levels")
        kind = event["type"]
        if kind in ("rename", "reparent") and (len(incoming) != 1 or incoming != outgoing):
            raise LedgerError(f"{event['id']}: rename/reparent must preserve unit identity")
        if kind in ("rename", "reparent"):
            uid = next(iter(incoming))
            periods = ledger["names" if kind == "rename" else "parents"]
            for period in periods:
                if period["unit_id"] == uid and period["status"] == "confirmed" and period["valid_from"] < event["effective_on"] and (
                        period["valid_to"] is None or period["valid_to"] > event["effective_on"]):
                    raise LedgerError(f"{period['id']}: period spans confirmed {kind} {event['id']}")
        if kind == "merge" and (len(incoming) < 2 or len(outgoing) != 1):
            raise LedgerError(f"{event['id']}: invalid merge cardinality")
        if kind == "split" and (len(incoming) != 1 or len(outgoing) < 2):
            raise LedgerError(f"{event['id']}: invalid split cardinality")
        if kind == "abolish" and (not incoming or outgoing or event["territory"] != "whole"):
            raise LedgerError(f"{event['id']}: invalid abolition")
        if kind == "reported_transition" and (not incoming or not outgoing):
            raise LedgerError(f"{event['id']}: confirmed reported_transition requires both sides")
        if event["valid_from"] and event["effective_on"] < event["valid_from"] or event["valid_to"] and event["effective_on"] >= event["valid_to"]:
            raise LedgerError(f"{event['id']}: effective date outside interval")
        for assertion in ledger["names"] + ledger["parents"] + ledger["codes"]:
            if assertion["event_id"] == event["id"] and assertion["status"] == "confirmed":
                if assertion["valid_from"] != event["effective_on"]:
                    raise LedgerError(f"{assertion['id']}: date contradicts event")
        if event["territory"] == "whole":
            for origin in incoming - outgoing:
                for target in outgoing:
                    graph.setdefault(origin, []).append((target, event["effective_on"]))
    def visit(node, ancestors, earliest=None):
        if node in ancestors:
            raise LedgerError(f"confirmed transition cycle at {node}")
        for target, day in graph.get(node, []):
            if earliest is not None and day <= earliest:
                raise LedgerError(f"timeline date contradiction at {node}")
            visit(target, ancestors | {node}, day)
    for node in graph:
        visit(node, set())
    endings = {}
    for event in confirmed_events:
        if event["type"] == "abolish" or event["type"] in ("merge", "split", "reported_transition") and event["territory"] == "whole":
            outgoing = {r["id"] for r in event["to"]}
            for ref in event["from"]:
                if ref["id"] not in outgoing:
                    endings.setdefault(ref["id"], []).append(event)
    for uid, ending_events in endings.items():
        ending = min(ending_events, key=lambda e: (e["effective_on"], e["id"]))
        end = ending["effective_on"]
        for event in confirmed_events:
            refers_to_unit = any(r["id"] == uid for r in event["from"] + event["to"])
            conflicts_at_end = event["id"] != ending["id"] and event["effective_on"] == end and (
                event["type"] in ("rename", "reparent", "abolish") or
                event["type"] in ("merge", "split", "reported_transition") and event["territory"] == "whole" and
                any(r["id"] == uid for r in event["from"]))
            if refers_to_unit and (event["effective_on"] > end or conflicts_at_end):
                raise LedgerError(f"{event['id']}: event uses abolished/consumed unit {uid}")
        for assertion in ledger["names"] + ledger["parents"] + ledger["codes"]:
            if assertion["unit_id"] == uid and assertion["status"] == "confirmed" and (assertion["valid_to"] is None or assertion["valid_to"] > end):
                raise LedgerError(f"{assertion['id']}: period outlives abolished/consumed unit")
        for parent in ledger["parents"]:
            if parent["parent_id"] == uid and parent["status"] == "confirmed" and (parent["valid_to"] is None or parent["valid_to"] > end):
                raise LedgerError(f"{parent['id']}: relationship outlives abolished/consumed parent")
    return {"valid": True, "units": len(units), "events": len(ledger["events"]),
            "pending_events": sum(e["status"] == "pending" for e in ledger["events"]),
            "coverage": ledger["coverage"]}


def atomic_write(folder: Path, ledger: dict):
    validate(ledger, folder)
    folder.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".ledger-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, folder / "ledger.json")
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_snapshot(target: Path, content: bytes):
    """Publish a complete immutable snapshot, never a partially written hash path."""
    if target.exists():
        if target.read_bytes() != content:
            raise LedgerError("immutable snapshot collision")
        return
    fd, name = tempfile.mkstemp(prefix=".snapshot-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / ".write.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise LedgerError("ledger is being written; retry or inspect stale lock") from exc
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink()


def _catalog(raw):
    try:
        rows = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise LedgerError("malformed catalog") from exc
    if not isinstance(rows, list) or not rows:
        raise LedgerError("empty/non-array catalog")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k] for k in ("ma", "ten", "magoc", "malk", "truocsapnhap")):
            raise LedgerError("catalog row missing string fields")
        if row["ma"] in seen:
            raise LedgerError("duplicate current code")
        seen.add(row["ma"])
    province_codes = {r["ma"] for r in rows if r["magoc"] == "0"}
    if any(r["magoc"] != "0" and r["magoc"] not in province_codes for r in rows):
        raise LedgerError("catalog dangling province")
    if len({r["malk"] for r in rows}) != len(rows):
        raise LedgerError("duplicate map identity")
    return rows


def import_bando(folder: Path, raw: bytes, retrieved_at: str, tables: dict[str, bytes], strict=True) -> dict:
    rows = _catalog(raw)
    provinces = [r for r in rows if r["magoc"] == "0"]
    if strict and (len(provinces), len(rows) - len(provinces)) != (34, 3321):
        raise LedgerError("full catalog must contain 34 provinces / 3321 communes")
    payloads = [("catalog", raw, "/p.co_dvhc", "ma=0")]
    details = {}
    for province in provinces:
        code = province["ma"]
        if code not in tables:
            raise LedgerError(f"missing full public table {code}")
        table = tables[code]
        try:
            head, body = table.decode("utf-8").strip().split(".synt.", 1)
            header = json.loads(head)
            children = json.loads(body)
            if not isinstance(header, dict) or header["ma"] != code:
                raise ValueError("province header mismatch")
            for key in ("ma", "ten", "magoc", "malk", "truocsapnhap"):
                if header[key] != province[key]:
                    raise ValueError(f"province table/catalog differ: {code} {key}")
            expected = {r["ma"]: r for r in rows if r["magoc"] == code}
            if len(children) != len(expected) or {r["ma"] for r in children} != expected.keys():
                raise ValueError("commune code set mismatch")
            for child in children:
                for key in ("ma", "ten", "magoc", "malk", "truocsapnhap"):
                    if child[key] != expected[child["ma"]][key]:
                        raise ValueError(f"table/catalog differ: {child['ma']} {key}")
                details[child["malk"]] = child
            details[province["malk"]] = header
        except (ValueError, UnicodeError, KeyError, TypeError) as exc:
            raise LedgerError(f"malformed/corrupt province table {code}: {exc}") from exc
        payloads.append((f"table-{code}", table, "/p.co_bangbieu", f"ma={province['malk']}"))
    version = digest("".join(digest(item[1]) for item in payloads).encode())
    with locked(folder):
        ledger = read_ledger(folder, initialize=True)
        validate(ledger, folder)
        if ledger["dataset_version"] == version:
            return validate(ledger, folder)
        result = deepcopy(ledger)
        existing_ids = {key: {row["id"] for row in result[key]} for key in COLLECTIONS}
        def retain(key, record):
            if record["id"] not in existing_ids[key]:
                result[key].append(record)
                existing_ids[key].add(record["id"])
        sources = {}
        for label, content, endpoint, request_body in payloads:
            sha = digest(content)
            source_id = f"bando:{sha}"
            sources[label] = source_id
            if source_id not in {s["id"] for s in result["sources"]}:
                result["sources"].append({"id": source_id, "provider": "Bando", "url": BASE_URL + endpoint,
                    "protocol": "HTTPS POST", "request_body": request_body, "retrieved_at": retrieved_at,
                    "sha256": sha, "snapshot": f"snapshots/{sha}.raw", "description": "Public full catalog/table"})
        known = {u["source_key"]: u["id"] for u in result["units"] if u["source_key"] is not None}
        known_levels = {u["source_key"]: u["level"] for u in result["units"] if u["source_key"] is not None}
        for row in rows:
            expected_level = "province" if row["magoc"] == "0" else "commune"
            if row["malk"] in known_levels and known_levels[row["malk"]] != expected_level:
                raise LedgerError(f"{row['malk']}: source key reused across administrative levels")
        ids = {r["malk"]: known.get(r["malk"], "unit:bando:" + digest(r["malk"].encode())[:24]) for r in rows}
        province_ids = {r["ma"]: ids[r["malk"]] for r in provinces}
        report = {"province": len(provinces), "commune": len(rows)-len(provinces), "district": 0,
                  "partial_rows": 0, "unchanged_rows": 0, "unparsed_rows": 0,
                  "retrieved_at": retrieved_at, "effective_dates_known": 0}
        for row in rows:
            uid = ids[row["malk"]]
            evidence = [{"source_id": sources["catalog"], "row_key": row["malk"]},
                        {"source_id": sources["table-" + (row["ma"] if row["magoc"] == "0" else row["magoc"])], "row_key": row["malk"]}]
            if uid not in existing_ids["units"]:
                retain("units", {"id": uid, "level": "province" if row["magoc"] == "0" else "commune",
                                        "source_key": row["malk"], "evidence": evidence})
            suffix = f"{version[:16]}:{uid}"
            period = {"unit_id": uid, "valid_from": None, "valid_to": None, "status": "observed",
                      "event_id": None, "evidence": evidence}
            retain("names", {"id": "name:"+suffix, "value": row["ten"], **period})
            retain("codes", {"id": "code:"+suffix, "value": row["ma"], **period})
            if row["magoc"] != "0":
                retain("parents", {"id": "parent:"+suffix, "parent_id": province_ids[row["magoc"]], **period})
            phrase = row["truocsapnhap"]
            unchanged = bool(re.fullmatch(r"\s*giữ nguyên[.!]?\s*", phrase, re.IGNORECASE))
            partial = bool(re.search(r"một phần|phần còn lại", phrase, re.IGNORECASE))
            report["partial_rows"] += partial
            report["unchanged_rows"] += unchanged
            retain("observations", {"id": "observation:"+suffix, "unit_id": uid,
                "kind": "unchanged" if unchanged else "reported_predecessor", "raw_phrase": phrase,
                "details": details[row["malk"]], "dataset_version": version, "evidence": evidence})
            if unchanged:
                continue
            report["unparsed_rows"] += 1
            mid = "mention:"+suffix
            retain("mentions", {"id": mid, "raw_phrase": phrase, "candidate_names": [],
                "resolved_unit_id": None, "status": "pending", "evidence": evidence})
            retain("events", {"id": "event:"+suffix, "type": "reported_transition",
                "from": [{"kind": "mention", "id": mid}], "to": [{"kind": "unit", "id": uid}],
                "effective_on": None, "valid_from": None, "valid_to": None, "status": "pending",
                "territory": "partial" if partial else "unknown", "notes": phrase, "evidence": evidence})
        result["dataset_version"] = version
        result["coverage"] = report
        result["revision"] += 1
        validate(result)
        snapshot_folder = folder / "snapshots"
        snapshot_folder.mkdir(exist_ok=True)
        for _, content, _, _ in payloads:
            target = snapshot_folder / (digest(content)+".raw")
            atomic_snapshot(target, content)
        atomic_write(folder, result)
        return validate(result, folder)


def manual_update(folder: Path, patch: dict) -> dict:
    if not isinstance(patch, dict) or set(patch) != {"base_revision", "upsert"} or not isinstance(patch["upsert"], dict):
        raise LedgerError("patch requires base_revision and upsert")
    if set(patch["upsert"]) - set(COLLECTIONS):
        raise LedgerError("unknown patch collection")
    for rows in patch["upsert"].values():
        if not isinstance(rows, list):
            raise LedgerError("upsert collections must be arrays")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise LedgerError("upsert row requires id")
            if row["id"] in seen:
                raise LedgerError(f"duplicate upsert id: {row['id']}")
            seen.add(row["id"])
    def importer_owned(key, row):
        return (key == "observations" or row["id"].startswith(("bando:", "unit:bando:")) or
                bool(re.match(r"^(name|code|parent|event|mention|observation):[0-9a-f]{16}:", row["id"])) or
                key == "units" and row.get("source_key") is not None)
    with locked(folder):
        ledger = read_ledger(folder)
        validate(ledger, folder)
        if type(patch["base_revision"]) is not int or patch["base_revision"] != ledger["revision"]:
            raise LedgerError("stale base_revision; reload before updating")
        result = deepcopy(ledger)
        for key, rows in patch["upsert"].items():
            if not isinstance(rows, list):
                raise LedgerError("upsert collections must be arrays")
            index = {r["id"]: i for i, r in enumerate(result[key])}
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                    raise LedgerError("upsert row requires id")
                if row["id"] in index:
                    old = result[key][index[row["id"]]]
                    protected = key == "sources" or importer_owned(key, old)
                    if key == "mentions" and importer_owned(key, old):
                        # Identity resolution is curator-owned; preserve every source field.
                        protected = any(row.get(field) != value for field, value in old.items()
                                        if field not in ("resolved_unit_id", "status"))
                    if protected and row != old:
                        raise LedgerError("immutable source evidence; add separate curated records")
                    result[key][index[row["id"]]] = deepcopy(row)
                else:
                    if importer_owned(key, row):
                        raise LedgerError("reserved importer record requires importer")
                    if key == "sources" and row.get("provider") == "Bando":
                        raise LedgerError("Bando sources require importer")
                    index[row["id"]] = len(result[key])
                    result[key].append(deepcopy(row))
        result["revision"] += 1
        validate(result, folder)
        # Retain exact prior bytes before replacing curator records. Archive failure
        # aborts the update; this immutable recovery evidence is not a second ledger.
        prior = (folder / "ledger.json").read_bytes()
        revisions = folder / "revisions"
        revisions.mkdir(exist_ok=True)
        archive = revisions / f"revision-{ledger['revision']:08d}-{digest(prior)}.json.gz"
        atomic_snapshot(archive, gzip.compress(prior, mtime=0))
        atomic_write(folder, result)
        return validate(result, folder)


def query(ledger: dict, unit_id: str, as_on: str | None = None) -> dict:
    validate(ledger)
    if unit_id not in {u["id"] for u in ledger["units"]}:
        raise LedgerError("unknown unit_id")
    _day(as_on)
    mentions = {m["id"]: m for m in ledger["mentions"]}
    def unit_refs(event, resolve_mentions=False):
        refs = set()
        for ref in event["from"] + event["to"]:
            if ref["kind"] == "unit":
                refs.add(ref["id"])
            elif resolve_mentions:
                mention = mentions[ref["id"]]
                if mention["status"] == "confirmed":
                    refs.add(mention["resolved_unit_id"])
        return refs
    connected = {unit_id}
    while True:
        before = len(connected)
        for event in ledger["events"]:
            if event["status"] != "confirmed":
                continue
            refs = unit_refs(event)
            if refs & connected:
                connected.update(refs)
        if len(connected) == before:
            break
    events = [e for e in ledger["events"] if unit_refs(e, resolve_mentions=True) & connected]
    names = [r for r in ledger["names"] if r["unit_id"] == unit_id]
    answer = [r for r in names if r["status"] == "confirmed" and as_on is not None and
              r["valid_from"] <= as_on and (r["valid_to"] is None or as_on < r["valid_to"])]
    return {"unit_id": unit_id, "as_on": as_on, "confirmed_name_at_date": answer,
            "current_source_observations": [o for o in ledger["observations"] if o["unit_id"] == unit_id and o["dataset_version"] == ledger["dataset_version"]],
            "names": names, "chronological_events": sorted([e for e in events if e["status"] == "confirmed"], key=lambda e: (e["effective_on"], e["id"])),
            "pending_evidence": [e for e in events if e["status"] != "confirmed"],
            "date_lookup": "confirmed" if answer else "insufficient_confirmed_history"}


def fetch_public(endpoint: str, value: str) -> bytes:
    request = Request(BASE_URL + endpoint, data=urlencode({"ma": value}).encode(),
                      headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}, method="POST")
    with urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise LedgerError("public source returned non-200")
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=DEFAULT_FOLDER)
    sub = parser.add_subparsers(dest="command", required=True)
    offline = sub.add_parser("import-bando")
    offline.add_argument("--catalog", type=Path, required=True)
    offline.add_argument("--tables", type=Path, required=True)
    offline.add_argument("--retrieved-at", required=True)
    sub.add_parser("refresh-bando")
    sub.add_parser("validate")
    update = sub.add_parser("update")
    update.add_argument("patch", type=Path)
    lookup = sub.add_parser("query")
    lookup.add_argument("unit_id")
    lookup.add_argument("--as-on")
    args = parser.parse_args()
    try:
        if args.command in ("import-bando", "refresh-bando"):
            if args.command == "import-bando":
                raw = args.catalog.read_bytes()
                tables = {r["ma"]: (args.tables / f"province-{r['ma']}.txt").read_bytes() for r in _catalog(raw) if r["magoc"] == "0"}
                timestamp = args.retrieved_at
            else:
                raw = fetch_public("/p.co_dvhc", "0")
                tables = {r["ma"]: fetch_public("/p.co_bangbieu", r["malk"]) for r in _catalog(raw) if r["magoc"] == "0"}
                timestamp = datetime.now().astimezone().isoformat()
            output = import_bando(args.folder, raw, timestamp, tables)
        elif args.command == "update":
            output = manual_update(args.folder, json.loads(args.patch.read_text(encoding="utf-8")))
        elif args.command == "query":
            ledger = read_ledger(args.folder)
            validate(ledger, args.folder)
            output = query(ledger, args.unit_id, args.as_on)
        else:
            output = validate(read_ledger(args.folder), args.folder)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (LedgerError, OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
