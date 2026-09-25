"""Regenerate every slice-A example case (pkg-*, seq-*, rcpt-*, status-*).

Byte-exact: all writes go through _validator.io.write_bytes_exact — never text mode —
so records.jsonl keeps LF-only framing and manifest/READY hashes match real bytes.

Run from the contract dir:
    python examples/_build/build_slice_a.py
"""
import json
import sys
from pathlib import Path

CONTRACT_DIR = Path(__file__).resolve().parents[2]
if str(CONTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_DIR))

from _validator.io import sha256_hex, write_bytes_exact  # noqa: E402

EXAMPLES = CONTRACT_DIR / "examples"

# Stable fake identifiers — canonical lowercase UUIDs, no real data anywhere.
CONSUMER = "c0000000-0000-4000-8000-000000000001"
OTHER_CONSUMER = "c0000000-0000-4000-8000-000000000099"
PKG1 = "a0000000-0000-4000-8000-000000000001"
PKG2 = "a0000000-0000-4000-8000-000000000002"
PKG3 = "a0000000-0000-4000-8000-000000000003"
RCPT1 = "e0000000-0000-4000-8000-000000000001"
SESSION = "5e550000-0000-4000-8000-000000000001"
BUILD = "zalo-intake+2026-09-24.demo"
T0 = "2026-09-24T00:03:00+07:00"
T1 = "2026-09-24T00:03:30+07:00"
T2 = "2026-09-24T08:05:00+07:00"
ZERO_HASH = "0" * 64


def dump(obj) -> bytes:
    """Pretty JSON, UTF-8, no BOM, trailing newline."""
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def package_bytes(records: bytes, sequence: int, package_id: str,
                  consumer_id: str = CONSUMER, record_count=None,
                  schema_version: str = "intake.raw-package.v1",
                  service: str = "zalo-intake",
                  declared_path: str = "records.jsonl",
                  declared_sha256: str = None, declared_bytes=None) -> dict:
    """Return {name: bytes} for the three package files, hashes over real bytes."""
    rec_sha = sha256_hex(records)
    if record_count is None:
        record_count = len(records.split(b"\n")) - 1 if records else 0
    manifest = {
        "schema_version": schema_version,
        "package_id": package_id,
        "producer": {"service": service, "build_id": BUILD},
        "consumer_id": consumer_id,
        "created_at": T0,
        "sequence": sequence,
        "files": [{
            "path": declared_path,
            "sha256": declared_sha256 if declared_sha256 is not None else rec_sha,
            "bytes": declared_bytes if declared_bytes is not None else len(records),
        }],
        "record_count": record_count,
    }
    mbytes = dump(manifest)
    ready = {
        "schema_version": "intake.ready.v1",
        "package_id": package_id,
        "manifest_sha256": sha256_hex(mbytes),
        "sealed_at": T1,
    }
    return {"manifest.json": mbytes, "records.jsonl": records, "READY.json": dump(ready)}


def write_case(group: str, name: str, case: dict, files: dict) -> None:
    """files: {posix relative path inside the case dir -> bytes}."""
    cdir = EXAMPLES / group / name
    write_bytes_exact(cdir / "case.json", dump(case))
    for rel, data in files.items():
        write_bytes_exact(cdir / rel, data)


def pkg_case(description, context=None, expected=None):
    case = {"kind": "package", "description": description}
    if expected:
        case["expected_errors"] = expected
    if context is not None:
        case["context"] = context
    return case


def seq_case(description, context=None, expected=None):
    case = {"kind": "package_sequence", "description": description}
    if expected:
        case["expected_errors"] = expected
    if context is not None:
        case["context"] = context
    return case


def rcpt_case(description, context, expected=None):
    case = {"kind": "receipt", "description": description, "context": context}
    if expected:
        case["expected_errors"] = expected
    return case


def status_case(description, expected=None):
    case = {"kind": "service_status", "description": description}
    if expected:
        case["expected_errors"] = expected
    return case


def receipt(package_id=PKG1, consumer_id=CONSUMER, status="accepted",
            manifest_sha256=ZERO_HASH, record_count=2, error=None,
            drop=()) -> bytes:
    doc = {
        "schema_version": "intake.receipt.v1",
        "receipt_id": RCPT1,
        "package_id": package_id,
        "consumer_id": consumer_id,
        "status": status,
        "received_at": T2,
        "manifest_sha256": manifest_sha256,
        "record_count": record_count,
    }
    if error is not None:
        doc["error"] = error
    for key in drop:
        doc.pop(key, None)
    return dump(doc)


def status_doc(state="connected", packages=2, oldest=True,
               ack_bytes=200_000_000, ack_cap=1_073_741_824, ack_warn=False) -> bytes:
    pending = {"packages": packages}
    if oldest:
        pending["oldest_sequence"] = 4
        pending["oldest_age_seconds"] = 3600
    doc = {
        "schema_version": "intake.service-status.v1",
        "producer": {"service": "zalo-intake", "build_id": BUILD},
        "observed_at": "2026-09-24T08:00:00+07:00",
        "listener": {
            "state": state,
            "last_heartbeat_at": "2026-09-24T07:59:45+07:00",
            "session_id": SESSION,
        },
        "pending": pending,
        "storage": {
            "ack_bytes": ack_bytes,
            "ack_cap_bytes": ack_cap,
            "ack_warn": ack_warn,
        },
        "capabilities": {
            "source_event_types": {
                "recall": "supported",
                "reaction": "supported",
                "edit": "unsupported",
            }
        },
    }
    return dump(doc)


def known_pkg(package_id=PKG1, manifest_sha256=ZERO_HASH, record_count=2):
    return {"package_id": package_id,
            "manifest_sha256": manifest_sha256,
            "record_count": record_count}


def main() -> int:
    two_records = b'{}\n{"x": 1}\n'
    two_hash = sha256_hex(two_records)

    # ----------------------------- valid/ -----------------------------
    write_case("valid", "pkg-01-basic",
               pkg_case("Well-formed package: 3 files, 2 JSONL records, all hashes match.",
                        context={"consumer_id": CONSUMER,
                                 "expected_sequence": 1,
                                 "previously_imported": []}),
               package_bytes(two_records, sequence=1, package_id=PKG1))

    write_case("valid", "pkg-02-empty-records",
               pkg_case("Package with an empty records.jsonl (0 records).",
                        context={"consumer_id": CONSUMER, "expected_sequence": 2}),
               package_bytes(b"", sequence=2, package_id=PKG2))

    seq_files = {}
    for i, pid in enumerate((PKG1, PKG2, PKG3), start=1):
        for name, data in package_bytes(two_records, sequence=i,
                                        package_id=pid).items():
            seq_files[f"package_{i}/{name}"] = data
    write_case("valid", "seq-01-three",
               seq_case("Three packages with consecutive sequences 1, 2, 3.",
                        context={"consumer_id": CONSUMER, "expected_start": 1}),
               seq_files)

    write_case("valid", "rcpt-01-accepted",
               rcpt_case("Accepted receipt matching the known package hash and count.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]}),
               {"receipt.json": receipt()})

    write_case("valid", "rcpt-02-rejected",
               rcpt_case("Rejected receipt carrying a well-formed error object.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]}),
               {"receipt.json": receipt(
                   status="rejected",
                   error={"code": "manifest_hash_mismatch",
                          "message": "declared sha256 does not match file bytes",
                          "retryable": True})})

    write_case("valid", "status-01-normal",
               status_case("Healthy status: connected, 2 pending, storage at ~19%."),
               {"status.json": status_doc()})

    write_case("valid", "status-02-storage-warn",
               status_case("ack_bytes at ~84% of cap, so ack_warn is true."),
               {"status.json": status_doc(ack_bytes=900_000_000, ack_warn=True)})

    # ----------------------------- invalid/ -----------------------------
    write_case("invalid", "pkg-03-manifest-hash-mismatch",
               pkg_case("manifest declares a wrong sha256 for records.jsonl.",
                        context={"consumer_id": CONSUMER},
                        expected=["manifest_hash_mismatch"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             declared_sha256="f" * 64))

    files = package_bytes(two_records, sequence=1, package_id=PKG1)
    del files["READY.json"]
    write_case("invalid", "pkg-04-missing-ready",
               pkg_case("READY.json absent: the package is not sealed.",
                        context={"consumer_id": CONSUMER},
                        expected=["file_missing"]),
               files)

    files = package_bytes(two_records, sequence=1, package_id=PKG1)
    files["results.json"] = dump({"note": "legacy field that must never ship"})
    write_case("invalid", "pkg-05-extra-results-json",
               pkg_case("Package carrying results.json — forbidden payload file.",
                        context={"consumer_id": CONSUMER},
                        expected=["file_forbidden"]),
               files)

    files = package_bytes(two_records, sequence=1, package_id=PKG1)
    files["notes.txt"] = b"operator scratch file, not part of the package\n"
    write_case("invalid", "pkg-06-unexpected-file",
               pkg_case("Package carrying a stray non-whitelisted file.",
                        context={"consumer_id": CONSUMER},
                        expected=["file_unexpected"]),
               files)

    write_case("invalid", "pkg-07-path-escape",
               pkg_case("manifest files[].path is '../x' — path escape attempt.",
                        context={"consumer_id": CONSUMER},
                        expected=["path_escape"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             declared_path="../x"))

    write_case("invalid", "pkg-08-bad-schema-version",
               pkg_case("manifest schema_version is not intake.raw-package.v1.",
                        context={"consumer_id": CONSUMER},
                        expected=["schema_invalid"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             schema_version="intake.raw-package.v0"))

    write_case("invalid", "pkg-09-count-mismatch",
               pkg_case("record_count says 5 but records.jsonl has 2 lines.",
                        context={"consumer_id": CONSUMER},
                        expected=["record_count_mismatch"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             record_count=5))

    write_case("invalid", "pkg-10-size-mismatch",
               pkg_case("manifest declares a wrong byte size for records.jsonl.",
                        context={"consumer_id": CONSUMER},
                        expected=["size_mismatch"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             declared_bytes=len(two_records) + 1))

    write_case("invalid", "pkg-11-consumer-mismatch",
               pkg_case("manifest.consumer_id belongs to a different consumer.",
                        context={"consumer_id": CONSUMER},
                        expected=["consumer_mismatch"]),
               package_bytes(two_records, sequence=1, package_id=PKG1,
                             consumer_id=OTHER_CONSUMER))

    write_case("invalid", "pkg-12-package-conflict",
               pkg_case("same package_id already imported under a different manifest hash.",
                        context={"consumer_id": CONSUMER,
                                 "previously_imported": [known_pkg(PKG1, "b" * 64, 2)]},
                        expected=["package_conflict"]),
               package_bytes(two_records, sequence=1, package_id=PKG1))

    write_case("invalid", "pkg-13-jsonl-missing-final-newline",
               pkg_case("records.jsonl does not end with a newline.",
                        context={"consumer_id": CONSUMER},
                        expected=["records_format_invalid"]),
               package_bytes(b'{}\n{"x": 1}', sequence=1, package_id=PKG1,
                             record_count=2))

    write_case("invalid", "pkg-14-jsonl-cr",
               pkg_case("records.jsonl uses CRLF line endings.",
                        context={"consumer_id": CONSUMER},
                        expected=["records_format_invalid"]),
               package_bytes(b'{}\r\n{"x": 1}\r\n', sequence=1,
                             package_id=PKG1, record_count=2))

    # ~18 MiB of well-formed JSONL (600 long lines < 1000 records, over the byte cap).
    fat_line = b'{"pad": "' + b"x" * 30000 + b'"}\n'
    oversize = fat_line * 600
    assert len(oversize) > 16 * 1024 * 1024
    write_case("invalid", "pkg-15-oversize-records",
               pkg_case("records.jsonl exceeds the 16 MiB package limit.",
                        context={"consumer_id": CONSUMER},
                        expected=["size_limit_exceeded"]),
               package_bytes(oversize, sequence=1, package_id=PKG1,
                             record_count=600))

    write_case("invalid", "pkg-16-sequence-invalid",
               pkg_case("consumer expected sequence 9, manifest says 4.",
                        context={"consumer_id": CONSUMER, "expected_sequence": 9},
                        expected=["sequence_invalid"]),
               package_bytes(two_records, sequence=4, package_id=PKG1))

    gap_files = {}
    for dirname, seq, pid in (("package_1", 1, PKG1), ("package_2", 3, PKG3)):
        for name, data in package_bytes(two_records, sequence=seq,
                                        package_id=pid).items():
            gap_files[f"{dirname}/{name}"] = data
    write_case("invalid", "seq-02-gap",
               seq_case("Sequences jump 1 -> 3; the expected next sequence was 2.",
                        context={"consumer_id": CONSUMER, "expected_start": 1},
                        expected=["sequence_invalid"]),
               gap_files)

    write_case("invalid", "rcpt-03-unknown-package",
               rcpt_case("receipt names a package_id the consumer never saw.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]},
                         expected=["package_unknown"]),
               {"receipt.json": receipt(package_id=PKG3)})

    write_case("invalid", "rcpt-04-hash-mismatch",
               rcpt_case("receipt manifest_sha256 differs from the imported package.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]},
                         expected=["receipt_hash_mismatch"]),
               {"receipt.json": receipt(manifest_sha256="c" * 64)})

    write_case("invalid", "rcpt-05-count-mismatch",
               rcpt_case("receipt record_count differs from the imported package.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]},
                         expected=["receipt_count_mismatch"]),
               {"receipt.json": receipt(record_count=7)})

    write_case("invalid", "rcpt-06-consumer-mismatch",
               rcpt_case("receipt.consumer_id is not the consumer of this session.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]},
                         expected=["receipt_consumer_mismatch"]),
               {"receipt.json": receipt(consumer_id=OTHER_CONSUMER)})

    write_case("invalid", "rcpt-07-schema",
               rcpt_case("receipt.json is missing received_at.",
                         context={"consumer_id": CONSUMER,
                                  "existing_packages": [known_pkg()]},
                         expected=["schema_invalid"]),
               {"receipt.json": receipt(drop=("received_at",))})

    write_case("invalid", "status-03-bad",
               status_case("listener.state is not in the enum.",
                           expected=["schema_invalid"]),
               {"status.json": status_doc(state="connecting")})

    write_case("invalid", "status-04-warn-inconsistent",
               status_case("ack_bytes ~47% of cap but ack_warn is true.",
                           expected=["status_invalid"]),
               {"status.json": status_doc(ack_bytes=500_000_000, ack_warn=True)})

    print("slice-A fixtures written under", EXAMPLES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
