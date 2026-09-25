"""Generates the slice-C example cases (req-*, rstat-*) under examples/{valid,invalid}.

Run from anywhere:  python examples/_build/build_slice_c.py
Writes JSON as UTF-8 without BOM. canonical_sha256 values inside case.json
contexts are computed from the same dicts that become request.json, so
idempotent-replay and request_conflict fixtures stay in sync.
"""
import json
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STAGE))
from _validator.io import canonical_sha256, sha256_hex  # noqa: E402

EXAMPLES = STAGE / "examples"

CONSUMER_ID = "10000000-0000-4000-8000-000000000003"
LOGICAL_ID = "20000000-0000-4000-8000-000000000002"
CONFIG_VERSION = "ocr-config-v1"
NOW = "2026-09-24T08:05:00+07:00"
CAPTURED_AT = "2026-09-23T09:00:00+07:00"     # +168 h = 2026-09-30T09:00+07:00

_req_seq = [0]


def request_body(**over):
    _req_seq[0] += 1
    body = {
        "schema_version": "intake.ocr-request.v1",
        "request_id": f"50000000-0000-4000-8000-{over.pop('seq', _req_seq[0]):012d}",
        "consumer_id": CONSUMER_ID,
        "logical_id": LOGICAL_ID,
        "variant": "crop_bottom",
        "preset": "bottom_42pct",
        "reason_code": "truncated_footer",
        "observed_revision": 1,
        "submitted_at": "2026-09-24T08:01:00+07:00",
    }
    for key, value in over.items():
        if value is ...:
            body.pop(key, None)
        else:
            body[key] = value
    return body


def base_context(**over):
    ctx = {
        "now": NOW,
        "authenticated": True,
        "config_version": CONFIG_VERSION,
        "sources": {LOGICAL_ID: {"captured_at": CAPTURED_AT, "current_revision": 1,
                                 "image_available": True, "enabled": True}},
        "quota_used": {"key_jobs": 0, "day_calls": 0, "concurrent": 0},
        "existing_requests": [],
    }
    for key, value in over.items():
        ctx[key] = value
    return ctx


def status_body(**over):
    body = {
        "schema_version": "intake.ocr-request-status.v1",
        "request_id": "50000000-0000-4000-8000-000000000001",
        "job_id": "70000000-0000-4000-8000-000000000001",
        "state": "queued",
        "attempt": 0,
        "max_attempts": 3,
        "accepted_at": "2026-09-24T08:01:05+07:00",
        "deduplicated": False,
    }
    for key, value in over.items():
        if value is ...:
            body.pop(key, None)
        else:
            body[key] = value
    return body


PACKAGE_ID = "60000000-0000-4000-8000-000000000001"
MANIFEST_SHA = sha256_hex(b"example manifest bytes for slice C")


def status_context(**over):
    ctx = {
        "existing_packages": [{"package_id": PACKAGE_ID,
                               "manifest_sha256": MANIFEST_SHA,
                               "record_count": 2}],
        "existing_requests": [{"request_id": "50000000-0000-4000-8000-000000000001",
                               "job_id": "70000000-0000-4000-8000-000000000001",
                               "state": "running"}],
    }
    ctx.update(over)
    return ctx


def write_case(group, name, case, files):
    case_dir = EXAMPLES / group / name
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "case.json").write_bytes(
        (json.dumps(case, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    for rel, data in files.items():
        payload = data if isinstance(data, bytes) else \
            (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        (case_dir / rel).write_bytes(payload)


def req_case(group, name, description, body, context, expected=None):
    case = {"kind": "ocr_request", "description": description, "context": context}
    if expected:
        case["expected_errors"] = expected
    write_case(group, name, case, {"request.json": body})


def rstat_case(group, name, description, body, context, expected=None):
    case = {"kind": "ocr_request_status", "description": description,
            "context": context}
    if expected:
        case["expected_errors"] = expected
    write_case(group, name, case, {"status.json": body})


# ---------------------------------------------------------------------------
# valid ocr_request cases
# ---------------------------------------------------------------------------

req_case("valid", "req-01-crop-bottom",
         "crop_bottom + bottom_42pct on an enabled, in-lifetime source",
         request_body(), base_context())

req_case("valid", "req-02-rotate-auto",
         "rotate with preset auto (provider enable_rotate)",
         request_body(variant="rotate", preset="auto",
                      reason_code="suspected_rotation"), base_context())

req_case("valid", "req-03-full-res",
         "full_res with explicit preset null",
         request_body(variant="full_res", preset=None,
                      reason_code="insufficient_text"), base_context())

_replay_body = request_body()
req_case("valid", "req-04-idempotent-replay",
         "same request_id + same canonical body -> replay of the stored decision",
         _replay_body,
         base_context(existing_requests=[{
             "request_id": _replay_body["request_id"],
             "body_canonical_sha256": canonical_sha256(_replay_body),
             "job_id": "70000000-0000-4000-8000-000000000009",
             "state": "running"}]))

_dedupe_request = request_body(seq=5)
_old_job_body = request_body(request_id="50000000-0000-4000-8000-000000000099",
                             submitted_at="2026-09-23T10:00:00+07:00")
req_case("valid", "req-05-dedupe-existing-job",
         "new request_id but same logical_id+variant+preset+config_version as a "
         "completed job -> answered with the existing job, no new quota",
         _dedupe_request,
         base_context(existing_requests=[{
             "request_id": _old_job_body["request_id"],
             "body_canonical_sha256": canonical_sha256(_old_job_body),
             "job_id": "70000000-0000-4000-8000-000000000010",
             "state": "completed",
             "logical_id": _old_job_body["logical_id"],
             "variant": _old_job_body["variant"],
             "preset": _old_job_body["preset"],
             "config_version": CONFIG_VERSION}]))

# ---------------------------------------------------------------------------
# valid ocr_request_status cases
# ---------------------------------------------------------------------------

rstat_case("valid", "rstat-01-queued",
           "queued job before the first provider attempt",
           status_body(), status_context())

rstat_case("valid", "rstat-02-completed",
           "completed job; result points at a package published to the consumer",
           status_body(state="completed", attempt=1,
                       started_at="2026-09-24T08:01:20+07:00",
                       finished_at="2026-09-24T08:02:40+07:00",
                       result={"package_id": PACKAGE_ID,
                               "manifest_sha256": MANIFEST_SHA,
                               "new_revision": 2}),
           status_context())

rstat_case("valid", "rstat-03-rejected",
           "rejected at intake (budget spent); error object required and present",
           status_body(state="rejected",
                       finished_at="2026-09-24T08:01:06+07:00",
                       error={"code": "budget_exceeded",
                              "message": "2 supplementary jobs already used for "
                                         "this page in the image lifetime",
                              "retryable": False}),
           status_context())

# ---------------------------------------------------------------------------
# invalid ocr_request cases
# ---------------------------------------------------------------------------

req_case("invalid", "req-06-unauthorized",
         "consumer bearer token missing/invalid -> unauthorized",
         request_body(), base_context(authenticated=False),
         ["unauthorized"])

req_case("invalid", "req-07-unknown-source",
         "logical_id never delivered to this consumer -> unknown_source",
         request_body(), base_context(sources={}),
         ["unknown_source"])

req_case("invalid", "req-08-source-disabled",
         "logical_id exists but the source is disabled -> source_not_enabled",
         request_body(),
         base_context(sources={LOGICAL_ID: {"captured_at": CAPTURED_AT,
                                            "current_revision": 1,
                                            "image_available": True,
                                            "enabled": False}}),
         ["source_not_enabled"])

req_case("invalid", "req-09-bad-variant",
         "variant outside the closed enum -> unsupported_variant (x-error-code)",
         request_body(variant="mirror", preset=...),
         base_context(), ["unsupported_variant"])

req_case("invalid", "req-10-missing-preset",
         "crop_bottom without preset -> missing_preset (x-error-code on then)",
         request_body(preset=...), base_context(), ["missing_preset"])

req_case("invalid", "req-11-preset-wrong-variant",
         "full_res must not carry a crop preset -> unsupported_variant",
         request_body(variant="full_res"), base_context(),
         ["unsupported_variant"])

req_case("invalid", "req-12-bad-reason",
         "reason_code outside the enum -> schema_invalid",
         request_body(reason_code="wrong_doc_kind"), base_context(),
         ["schema_invalid"])

req_case("invalid", "req-13-stale-revision",
         "consumer analyzed revision 1 while the producer already published "
         "revision 2 -> stale_revision",
         request_body(),
         base_context(sources={LOGICAL_ID: {"captured_at": CAPTURED_AT,
                                            "current_revision": 2,
                                            "image_available": True,
                                            "enabled": True}}),
         ["stale_revision"])

req_case("invalid", "req-14-source-expired",
         "now is past captured_at + 168 h -> source_image_expired",
         request_body(), base_context(now="2026-10-01T10:00:00+07:00"),
         ["source_image_expired"])

req_case("invalid", "req-15-source-unavailable",
         "still inside 168 h but the image file is gone -> source_image_unavailable",
         request_body(),
         base_context(sources={LOGICAL_ID: {"captured_at": CAPTURED_AT,
                                            "current_revision": 1,
                                            "image_available": False,
                                            "enabled": True}}),
         ["source_image_unavailable"])

req_case("invalid", "req-16-budget-exceeded",
         "2 supplementary jobs already spent on this logical_id -> budget_exceeded",
         request_body(),
         base_context(quota_used={"key_jobs": 2, "day_calls": 5, "concurrent": 0}),
         ["budget_exceeded"])

req_case("invalid", "req-17-rate-limit-day",
         "100 provider calls already used by the consumer in 24 h -> rate_limited",
         request_body(),
         base_context(quota_used={"key_jobs": 0, "day_calls": 100,
                                  "concurrent": 0}),
         ["rate_limited"])

req_case("invalid", "req-18-rate-limit-concurrent",
         "2 jobs already running -> rate_limited",
         request_body(),
         base_context(quota_used={"key_jobs": 0, "day_calls": 5, "concurrent": 2}),
         ["rate_limited"])

_conflict_body = request_body()
_conflict_other = dict(_conflict_body, note="different body, same request_id")
req_case("invalid", "req-19-request-conflict",
         "same request_id re-sent with a different canonical body -> request_conflict",
         _conflict_body,
         base_context(existing_requests=[{
             "request_id": _conflict_body["request_id"],
             "body_canonical_sha256": canonical_sha256(_conflict_other),
             "job_id": "70000000-0000-4000-8000-000000000011",
             "state": "queued"}]),
         ["request_conflict"])

req_case("invalid", "req-20-forbidden-field",
         "smuggled image_base64 key: additionalProperties makes it a schema "
         "error AND the key scan flags request_forbidden_field",
         request_body(image_base64="QUJDQUJD"), base_context(),
         ["schema_invalid", "request_forbidden_field"])

req_case("invalid", "req-21-forbidden-url",
         "data:image URI inside the note value -> request_forbidden_field "
         "(schema sees a legal string; the rule catches the payload)",
         request_body(note="anh kem theo: data:image/jpeg;base64,QUJDQUJDQUJD"),
         base_context(), ["request_forbidden_field"])

# req-22: schema-clean body padded past 16 KiB with legal JSON whitespace
_big = request_body()
_big_bytes = json.dumps(_big, ensure_ascii=False, indent=2).encode("utf-8")
pad = b" " * (17 * 1024)
_big_bytes = _big_bytes.replace(b'"request_id"', pad + b'"request_id"', 1)
assert len(_big_bytes) > 16 * 1024
_big_case = {"kind": "ocr_request",
             "description": "schema-clean request padded past the 16 KiB body "
                            "limit -> request_too_large (whitespace is legal JSON)",
             "context": base_context(),
             "expected_errors": ["request_too_large"]}
write_case("invalid", "req-22-oversize", _big_case,
           {"request.json": _big_bytes})

req_case("invalid", "req-23-missing-observed-revision",
         "observed_revision is required -> schema_invalid",
         request_body(observed_revision=...), base_context(),
         ["schema_invalid"])

# ---------------------------------------------------------------------------
# invalid ocr_request_status cases
# ---------------------------------------------------------------------------

rstat_case("invalid", "rstat-04-completed-no-result",
           "completed without result -> status_invalid",
           status_body(state="completed", attempt=1,
                       started_at="2026-09-24T08:01:20+07:00",
                       finished_at="2026-09-24T08:02:40+07:00"),
           status_context(), ["status_invalid"])

rstat_case("invalid", "rstat-05-bad-package-ref",
           "completed result points at a package never published to this "
           "consumer -> package_reference_invalid",
           status_body(state="completed", attempt=1,
                       started_at="2026-09-24T08:01:20+07:00",
                       finished_at="2026-09-24T08:02:40+07:00",
                       result={"package_id": "60000000-0000-4000-8000-000000000099",
                               "manifest_sha256": MANIFEST_SHA,
                               "new_revision": 2}),
           status_context(), ["package_reference_invalid"])

rstat_case("invalid", "rstat-06-attempt-over-max",
           "attempt 4 with max_attempts 3 -> status_invalid "
           "(provider retry cap is 3)",
           status_body(state="failed", attempt=4,
                       started_at="2026-09-24T08:01:20+07:00",
                       finished_at="2026-09-24T08:04:00+07:00",
                       error={"code": "provider_failed",
                              "message": "provider 5xx after retries",
                              "retryable": True}),
           status_context(), ["status_invalid"])

rstat_case("invalid", "rstat-07-bad-state",
           "state outside the enum -> schema_invalid",
           status_body(state="cancelled"),
           status_context(), ["schema_invalid"])

print("slice C fixtures written under", EXAMPLES)
