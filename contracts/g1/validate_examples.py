"""Validator cho contracts/g1/examples — stdlib-only, không dep ngoài.

Chạy:  python contracts/g1/validate_examples.py
Quy tắc: mọi *.valid.json phải pass hết rule; mọi *.invalid.json phải vi phạm
ít nhất một rule VÀ khai báo expected_error khớp code trong contract.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EX = HERE / "examples"

STATUSES = {"accepted", "running", "waiting_user", "partial",
            "succeeded", "failed", "canceled"}
WAITING_ON = {"login", "review", "finalize", "confirm", None}
VERSION = "desktopcommand.v1"

SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|credential|cookie|auth|session|"
    r"storage_state|api_key|bearer", re.I)

CANON = {
    "cccd": re.compile(r"^\d{12}$"),
    "gcn_serial": re.compile(r"^[A-Z]{2}\d{6,8}$"),
    "notary_number": re.compile(r"^\d+/\d{4}$"),
}

ERRORS = {"file_scope_not_supported", "payload_rejected_sensitive_key",
          "unsupported_contract_version", "evidence_invalid",
          "validation_error"}


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "/" + str(k), k, v
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def violations(doc):
    """Return list of (error_code, detail) the contract rules."""
    v = []

    if doc.get("contract_version") != VERSION:
        v.append(("unsupported_contract_version",
                  f"contract_version={doc.get('contract_version')!r}"))

    for path, k, val in walk_keys(doc.get("payload", {})):
        if SENSITIVE_KEY.search(str(k)):
            v.append(("payload_rejected_sensitive_key", f"key {path}"))

    for path, k, val in walk_keys(doc):
        if k == "scope" and val != "machine_local":
            v.append(("file_scope_not_supported", f"{path} scope={val!r}"))
        if k == "path" and isinstance(val, str):
            if val.startswith("\\\\") and not val.startswith("\\\\?\\"):
                v.append(("file_scope_not_supported", f"UNC path {path}"))
            elif not (re.match(r"^[A-Za-z]:[\\/]", val)
                      or val.startswith("\\\\?\\")):
                v.append(("file_scope_not_supported",
                          f"non-absolute path {path}"))

        # empty string where null semantics required (normalized_value)
        if k == "normalized_value" and val == "":
            v.append(("validation_error", f"{path} empty-string-as-null"))

    # job-level rules
    if "status" in doc:
        if doc["status"] not in STATUSES:
            v.append(("validation_error", f"status={doc['status']!r}"))
        if doc.get("waiting_on") not in WAITING_ON:
            v.append(("validation_error", f"waiting_on={doc.get('waiting_on')!r}"))
        if doc["status"] == "waiting_user" and not doc.get("waiting_on"):
            v.append(("validation_error", "waiting_user without waiting_on"))
        if doc["status"] in ("failed", "canceled") and not doc.get("error"):
            v.append(("validation_error", "failed/canceled without error"))
        if doc["status"] == "partial":
            bd = (doc.get("result") or {}).get("data", {}).get("breakdown")
            if not isinstance(bd, dict) or "succeeded" not in bd:
                v.append(("validation_error", "partial without breakdown"))

    # evidence canonical rules
    res = doc.get("result") or {}
    for i, ev in enumerate(res.get("evidence") or []):
        state = ev.get("observation_state")
        nv = ev.get("normalized_value")
        if state in ("normalized", "inferred", "confirmed"):
            kind = ev.get("kind")
            rx = CANON.get(kind)
            if rx and not (isinstance(nv, str) and rx.match(nv)):
                v.append(("evidence_invalid",
                          f"evidence[{i}] {kind} normalized={nv!r}"))
            if nv is None:
                v.append(("evidence_invalid",
                          f"evidence[{i}] normalized_value null at {state}"))
    return v


def main():
    files = sorted(EX.glob("*.json"))
    if not files:
        print("no examples found"); return 1
    bad = 0
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        viols = violations(doc)
        name = f.name
        if ".invalid." in name:
            exp = doc.get("expected_error")
            ok = bool(viols) and exp in ERRORS and any(c == exp for c, _ in viols)
            status = "REJECTED-CORRECTLY" if ok else "!! NOT REJECTED AS EXPECTED"
            print(f"[invalid] {name}: expected={exp} "
                  f"got={[c for c, _ in viols]} -> {status}")
        else:
            ok = not viols
            print(f"[valid]   {name}: violations={viols} -> "
                  f"{'PASS' if ok else '!! FAIL'}")
        bad += 0 if ok else 1
    print(f"\n{len(files)} files, {bad} unexpected outcomes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
