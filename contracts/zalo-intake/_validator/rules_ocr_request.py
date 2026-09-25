"""Slice C — intake.ocr-request.v1 + intake.ocr-request-status.v1.

kind `ocr_request` (case dir holds request.json) simulates the producer's
accept/reject decision against a pure-data context:

    context = {
      "now":               ISO-8601 with offset (producer clock),
      "authenticated":     bool — consumer presented a valid bearer token,
      "config_version":    str — producer OCR config id used for dedupe
                           (default: no entry can dedupe-match),
      "sources":           {logical_id: {"captured_at", "current_revision",
                                         "image_available", "enabled"}},
      "quota_used":        {"key_jobs": int,   # supplementary jobs spent on
                           #   this logical_id inside the 168 h window (cap 2)
                           "day_calls": int,   # Qwen calls by this consumer in
                           #   the sliding 24 h window (cap 100)
                           "concurrent": int}, # jobs currently running (cap 2)
      "existing_requests": [{"request_id", "body_canonical_sha256", "job_id",
                             "state", "logical_id"?, "variant"?, "preset"?,
                             "config_version"?}]
    }

Check order — the first stage that produces codes is the answer (a stage may
emit more than one code when independent sub-checks fail together):

  1. auth: authenticated is not true -> unauthorized
  2. screening (union of three independent views of the same bytes):
       a. schema validation -> schema_invalid or the x-error-code carried by
          the failing subschema (unsupported_variant, missing_preset)
       b. body bytes > 16 KiB -> request_too_large
       c. request_forbidden_field scan: banned key names at any depth
          (image*/path/url/prompt/token/secret/key/password/data, matched on
          full name or any _-separated segment) and banned string values
          (data: URIs, image URLs/paths/file names, long base64 blobs)
     The forbidden scan deliberately runs even when the schema check already
     failed: additionalProperties:false makes a smuggled key a schema error
     too, but the dedicated code is kept so the rejection is greppable as an
     injection attempt, not a typo.
  3. logical_id absent from sources -> unknown_source;
     source.enabled is not true -> source_not_enabled
  4. idempotency: an existing_requests entry with the same request_id ->
     same body_canonical_sha256 = replay, accepted ([]);
     different hash -> request_conflict
  5. dedupe: an existing_requests entry in state queued|running|completed
     with the same (logical_id, variant, preset, config_version) -> accepted
     (returns the old job, spends no new quota)
  6. observed_revision < sources[logical_id].current_revision -> stale_revision
  7. now >= captured_at + 168 h -> source_image_expired;
     image_available is not true -> source_image_unavailable
  8. quota: key_jobs >= 2 -> budget_exceeded;
     day_calls >= 100 -> rate_limited; concurrent >= 2 -> rate_limited

kind `ocr_request_status` (case dir holds status.json): schema validation,
then state consistency — completed requires result whose package_id must be
listed in context.existing_packages (else package_reference_invalid), result
is forbidden on other states; rejected|failed require error, error is
forbidden on other states; attempt <= max_attempts <= 3. Violations of the
state rules carry status_invalid.
"""
import re
from datetime import datetime, timedelta

from . import CONTRACT_DIR
from .cases import register, register_error_codes
from .io import canonical_sha256, read_json_bytes
from .schema_subset import load_schema, validate

REQUEST_SCHEMA = load_schema(CONTRACT_DIR / "ocr-request.schema.json")
STATUS_SCHEMA = load_schema(CONTRACT_DIR / "ocr-request-status.schema.json")

REQUEST_MAX_BYTES = 16 * 1024
IMAGE_TTL = timedelta(hours=168)
QUOTA_KEY_JOBS = 2          # supplementary jobs per logical_id per image lifetime
QUOTA_DAY_CALLS = 100       # provider calls per consumer per sliding 24 h
QUOTA_CONCURRENT = 2        # simultaneous jobs
MAX_ATTEMPTS = 3            # provider-error retry cap per job
DEDUPE_STATES = frozenset({"queued", "running", "completed"})

register_error_codes([
    "unauthorized", "unknown_source", "source_not_enabled",
    "unsupported_variant", "missing_preset", "stale_revision",
    "source_image_expired", "source_image_unavailable",
    "budget_exceeded", "rate_limited", "request_conflict",
    "provider_failed", "request_forbidden_field", "request_too_large",
    "package_reference_invalid", "status_invalid",
])

# ---------------------------------------------------------------------------
# request_forbidden_field screening
# ---------------------------------------------------------------------------

# A request must never carry image bytes/references, provider prompts or
# credentials — the closed parameter set is all the schema allows. A key is
# banned when its lowercase name, or any [_-separated] segment of it, is in
# this set ("image_base64" -> segment "image"; "metadata" stays clean).
_BANNED_KEY_PARTS = frozenset({
    "image", "base64", "url", "uri", "href", "link",
    "path", "file", "prompt", "token", "secret", "key",
    "password", "credential", "data", "payload", "blob", "bytes",
})
_KEY_SEGMENTS = re.compile(r"[^a-z0-9]+")
_IMAGE_EXT = r"(?:jpe?g|png|gif|bmp|webp|tiff?|heic|heif)"
# any whitespace-free token ending in an image extension (covers URLs, UNC and
# POSIX/Windows paths and bare file names in one sweep)
_RE_IMAGE_REF = re.compile(r"\S+\." + _IMAGE_EXT + r"(?:[?#]\S*)?(?=\s|$)", re.I)
# a data: URI anywhere in the value (data:image/..., data:*;base64, ...)
_RE_DATA_URI = re.compile(r"data:\s*[a-z0-9.+-]+/[a-z0-9.+-]+", re.I)
# a long unbroken run of base64-alphabet characters = smuggled bytes
_RE_B64_BLOB = re.compile(r"[A-Za-z0-9+/]{256,}={0,3}")


def _key_banned(key):
    low = key.lower()
    return any(part in _BANNED_KEY_PARTS for part in _KEY_SEGMENTS.split(low))


def _scan_forbidden(node, ptr, out):
    """Append request_forbidden_field findings for banned keys/values at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{ptr}/{key}"
            if _key_banned(key):
                out.append(("request_forbidden_field",
                            f"{here}: key name is not allowed in an OCR request"))
            _scan_forbidden(value, here, out)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _scan_forbidden(value, f"{ptr}/{i}", out)
    elif isinstance(node, str):
        if _RE_DATA_URI.search(node):
            out.append(("request_forbidden_field",
                        f"{ptr}: data: URI / inline bytes are not allowed"))
        elif _RE_IMAGE_REF.search(node):
            out.append(("request_forbidden_field",
                        f"{ptr}: image URL/path/file name is not allowed"))
        elif _RE_B64_BLOB.search(node):
            out.append(("request_forbidden_field",
                        f"{ptr}: base64-looking payload is not allowed"))


def _parse_dt(value):
    """ISO-8601 string -> aware datetime, or None. Accepts trailing Z."""
    if not isinstance(value, str):
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


# ---------------------------------------------------------------------------
# kind: ocr_request
# ---------------------------------------------------------------------------

@register("ocr_request")
def check_ocr_request(case_dir, case):
    ctx = case.get("context") or {}

    # 1. auth before anything touches the body
    if ctx.get("authenticated") is not True:
        return [("unauthorized", "context.authenticated is not true")]

    raw = (case_dir / "request.json").read_bytes()
    doc = read_json_bytes(raw)                      # json_invalid escapes via execute()

    # 2. screening — schema, size and the forbidden-field scan are independent
    #    views of the same bytes; their findings are unioned.
    errors = validate(doc, REQUEST_SCHEMA)
    if len(raw) > REQUEST_MAX_BYTES:
        errors.append(("request_too_large",
                       f"request.json is {len(raw)} bytes (> {REQUEST_MAX_BYTES})"))
    if isinstance(doc, (dict, list)):
        _scan_forbidden(doc, "", errors)
    if errors:
        return errors

    # 3. the source must exist and be enabled for this consumer
    src = (ctx.get("sources") or {}).get(doc["logical_id"])
    if src is None:
        return [("unknown_source",
                 f"logical_id {doc['logical_id']} is not a delivered, in-scope source")]
    if src.get("enabled") is not True:
        return [("source_not_enabled",
                 f"logical_id {doc['logical_id']} belongs to a disabled source")]

    # 4. idempotent replay vs request_conflict on the same request_id
    body_sha = canonical_sha256(doc)
    existing = ctx.get("existing_requests") or []
    for entry in existing:
        if entry.get("request_id") == doc["request_id"]:
            if entry.get("body_canonical_sha256") == body_sha:
                return []                            # replay of a stored decision
            return [("request_conflict",
                     f"request_id {doc['request_id']} was already used with a "
                     "different body")]

    # 5. dedupe on (logical_id, variant, preset, config_version) against jobs
    #    that are still useful; the producer answers with the existing job.
    cfg = ctx.get("config_version")
    for entry in existing:
        if (entry.get("state") in DEDUPE_STATES
                and entry.get("logical_id") == doc["logical_id"]
                and entry.get("variant") == doc["variant"]
                and entry.get("preset") == doc.get("preset")
                and entry.get("config_version") == cfg):
            return []

    # 6. the consumer must have analyzed the newest delivered revision
    current = src.get("current_revision")
    if current is not None and doc["observed_revision"] < current:
        return [("stale_revision",
                 f"observed_revision {doc['observed_revision']} < "
                 f"current_revision {current}; sync and re-analyze first")]

    # 7. the source image must still be inside its 168 h lifetime and present
    now = _parse_dt(ctx.get("now"))
    captured = _parse_dt(src.get("captured_at"))
    if now is not None and captured is not None and now >= captured + IMAGE_TTL:
        return [("source_image_expired",
                 f"now is past captured_at + 168 h ({(captured + IMAGE_TTL).isoformat()})")]
    if src.get("image_available") is not True:
        return [("source_image_unavailable",
                 "the source image is not retrievable on the module")]

    # 8. quota — the three limits are independent; report every violation
    quota = ctx.get("quota_used") or {}
    errors = []
    if quota.get("key_jobs", 0) >= QUOTA_KEY_JOBS:
        errors.append(("budget_exceeded",
                       f"key_jobs {quota['key_jobs']} >= {QUOTA_KEY_JOBS} supplementary "
                       "jobs for this logical_id in the image lifetime"))
    if quota.get("day_calls", 0) >= QUOTA_DAY_CALLS:
        errors.append(("rate_limited",
                       f"day_calls {quota['day_calls']} >= {QUOTA_DAY_CALLS} provider "
                       "calls in the sliding 24 h window"))
    if quota.get("concurrent", 0) >= QUOTA_CONCURRENT:
        errors.append(("rate_limited",
                       f"concurrent {quota['concurrent']} >= {QUOTA_CONCURRENT} "
                       "simultaneous jobs"))
    return errors


# ---------------------------------------------------------------------------
# kind: ocr_request_status
# ---------------------------------------------------------------------------

@register("ocr_request_status")
def check_ocr_request_status(case_dir, case):
    ctx = case.get("context") or {}
    doc = read_json_bytes((case_dir / "status.json").read_bytes())

    errors = validate(doc, STATUS_SCHEMA)
    if errors:
        return errors

    state = doc["state"]
    if state == "completed":
        result = doc.get("result")
        if result is None:
            errors.append(("status_invalid",
                           "state completed requires a result object"))
        else:
            known = {p if isinstance(p, str) else p.get("package_id")
                     for p in (ctx.get("existing_packages") or [])}
            if result["package_id"] not in known:
                errors.append(("package_reference_invalid",
                               f"result.package_id {result['package_id']} is not a "
                               "package published to this consumer"))
    elif "result" in doc:
        errors.append(("status_invalid",
                       f"result is only allowed when state is completed, not {state}"))

    if state in ("rejected", "failed"):
        if "error" not in doc:
            errors.append(("status_invalid",
                           f"state {state} requires an error object"))
    elif "error" in doc:
        errors.append(("status_invalid",
                       f"error is only allowed when state is rejected or failed, "
                       f"not {state}"))

    if doc["attempt"] > doc["max_attempts"]:
        errors.append(("status_invalid",
                       f"attempt {doc['attempt']} exceeds max_attempts "
                       f"{doc['max_attempts']}"))
    if doc["max_attempts"] > MAX_ATTEMPTS:
        errors.append(("status_invalid",
                       f"max_attempts {doc['max_attempts']} exceeds the contract "
                       f"retry cap of {MAX_ATTEMPTS}"))
    return errors
