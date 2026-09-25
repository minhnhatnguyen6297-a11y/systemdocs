"""Slice B rules for zalo-intake v1 — registers case kinds ``record`` and ``listener_gap``.

record       — the case dir holds ``record.json`` (one raw record document) and the case
               context may carry prior state:
                 existing_records   = [{record_id, canonical_sha256}]
                 existing_revisions = [{logical_id, revision, canonical_sha256, captured_at?}]
                 supersedes_targets = [{record_id, revision}]
listener_gap — the case dir holds ``records.jsonl`` of listener_session records in order
               and the context carries
                 expected_gaps = [{started_at, ended_at, start_is_estimate}]
               (the shape MIN-94 reuses to assert crash-recovery gaps).

Validation layers: schema structure first (schema_subset + x-error-code), then payload
scans (they guard the places the schema cannot see — free-form params, plain strings),
then relational/semantic rules on schema-clean records only.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import CONTRACT_DIR
from .cases import CaseError, register, register_error_codes
from .io import canonical_sha256, read_json_bytes, read_jsonl_bytes
from .schema_subset import load_schema, validate

register_error_codes([
    "record_conflict", "source_revision_conflict", "revision_chain_broken",
    "missing_captured_at", "missing_line_id", "expires_mismatch",
    "immutable_field_changed", "line_pass_ref_unknown", "provider_ref_unknown",
    "geometry_invalid", "geometry_frame_mismatch", "ocr_status_inconsistent",
    "image_payload_forbidden", "provider_payload_forbidden",
    "listener_gap_invalid", "source_event_invalid", "kind_body_mismatch",
])

_SCHEMA = load_schema(CONTRACT_DIR / "raw-record.schema.json")
IMAGE_TTL = timedelta(hours=168)

_ISO = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.([0-9]+))?(Z|[+-][0-9]{2}:[0-9]{2})\Z")


def _parse_iso(value):
    """Contract ISO-8601 string -> aware datetime, or None when unparseable.

    Mirrors the schema's date-time profile (seconds + explicit offset); falls back to
    fromisoformat so rule code stays total on schema-invalid documents.
    """
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


# ---------------------------------------------------------------------------
# Payload scans — run on every document, independent of schema verdict.
# ---------------------------------------------------------------------------

_PROVIDER_KEYS = frozenset({"provider_raw", "provider_response", "raw_response"})
_IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".pdf")
_BASE64 = re.compile(r"[A-Za-z0-9+/=]+\Z")


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
# Relational/semantic rules — schema-clean records only.
# ---------------------------------------------------------------------------

# Per-kind non-null body keys: a record may carry only its own kind's body
# (envelope fields aside). Draft intent — non-applicable bodies stay null.
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


def _record_rules(rec, ctx):
    out = []
    if not isinstance(rec, dict):
        return out

    # kind-body exclusivity: foreign bodies must be absent or null
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

    # revision / supersedes chain (the schema already forces supersedes when revision>1)
    rev = rec.get("revision")
    sup = rec.get("supersedes")
    if isinstance(rev, int) and not isinstance(rev, bool):
        if rev > 1:
            targets = {(t.get("record_id"), t.get("revision"))
                       for t in ctx.get("supersedes_targets", []) if isinstance(t, dict)}
            if (not isinstance(sup, dict)
                    or sup.get("revision") != rev - 1
                    or (sup.get("record_id"), sup.get("revision")) not in targets):
                out.append(("revision_chain_broken",
                            f"/supersedes: revision {rev} must point at revision {rev - 1} "
                            "of a known prior record (context.supersedes_targets)"))
        elif sup is not None:
            out.append(("revision_chain_broken",
                        "/supersedes: a revision 1 record has nothing to supersede"))

    # dedupe / immutability against context prior state
    digest = canonical_sha256(rec)
    for e in ctx.get("existing_records", []):
        if (isinstance(e, dict) and e.get("record_id") == rec.get("record_id")
                and e.get("canonical_sha256") != digest):
            out.append(("record_conflict",
                        f"/record_id: {rec.get('record_id')} already imported with a "
                        "different canonical_sha256"))
    for e in ctx.get("existing_revisions", []):
        if not isinstance(e, dict) or e.get("logical_id") != rec.get("logical_id"):
            continue
        erev = e.get("revision")
        if erev == rev and e.get("canonical_sha256") != digest:
            out.append(("source_revision_conflict",
                        f"/logical_id: (logical_id {rec.get('logical_id')}, revision {rev}) "
                        "already imported with a different canonical_sha256"))
        if (isinstance(erev, int) and not isinstance(erev, bool)
                and isinstance(rev, int) and erev < rev and "captured_at" in e):
            old, new = _parse_iso(e.get("captured_at")), _parse_iso(rec.get("captured_at"))
            same = (e.get("captured_at") == rec.get("captured_at")
                    or (old is not None and new is not None and old == new))
            if not same:
                out.append(("immutable_field_changed",
                            f"/captured_at: differs between revision {erev} and {rev} of "
                            f"logical_id {rec.get('logical_id')}"))

    _ocr_rules(rec, out)
    _source_event_rules(rec, out)
    _listener_rules(rec, out)
    return out


def _ocr_rules(rec, out):
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


# ---------------------------------------------------------------------------
# Case-kind validators
# ---------------------------------------------------------------------------

@register("record")
def check_record(case_dir, case):
    path = Path(case_dir) / "record.json"
    if not path.is_file():
        raise CaseError(f"{Path(case_dir).name}: missing record.json")
    record = read_json_bytes(path.read_bytes())
    errors = list(validate(record, _SCHEMA))
    _scan_payloads(record, "", errors)
    if errors:
        return errors
    return _record_rules(record, case.get("context") or {})


def _same_gap(got, want):
    """True when an observed uncertain_gap dict matches an expected_gaps entry:
    same ISO instants for started_at/ended_at and same start_is_estimate flag."""
    if not isinstance(want, dict):
        return False
    if got.get("start_is_estimate") != want.get("start_is_estimate"):
        return False
    for key in ("started_at", "ended_at"):
        a, b = _parse_iso(got.get(key)), _parse_iso(want.get(key))
        if a is None or b is None:
            if got.get(key) != want.get(key):
                return False
        elif a != b:
            return False
    return True


@register("listener_gap")
def check_listener_gap(case_dir, case):
    path = Path(case_dir) / "records.jsonl"
    if not path.is_file():
        raise CaseError(f"{Path(case_dir).name}: missing records.jsonl")
    records = read_jsonl_bytes(path.read_bytes())
    out = []
    gaps = []
    for rec in records:
        errs = list(validate(rec, _SCHEMA))
        out += errs
        if errs:
            continue
        out += _record_rules(rec, {})
        lis = rec.get("listener")
        if (rec.get("record_kind") == "listener_session" and isinstance(lis, dict)
                and lis.get("state") == "connected"
                and isinstance(lis.get("uncertain_gap"), dict)):
            gap = lis["uncertain_gap"]
            gaps.append({"started_at": gap.get("started_at"),
                         "ended_at": gap.get("ended_at"),
                         "start_is_estimate": gap.get("start_is_estimate")})
    expected = (case.get("context") or {}).get("expected_gaps") or []
    if len(gaps) != len(expected) or not all(
            _same_gap(g, e) for g, e in zip(gaps, expected)):
        out.append(("listener_gap_invalid",
                    f"observed uncertain gaps {gaps!r} do not match "
                    f"context.expected_gaps {expected!r}"))
    return out
