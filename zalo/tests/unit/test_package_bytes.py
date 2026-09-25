"""MIN-93 sheet §8 (slice D) — byte-level checks for ``delivery.build_package``.

The DB is built with raw-SQL DDL matching decision-sheet §4 (only the
``packages`` table that ``build_package`` touches) so this test exercises
slice-D code against a real SQLAlchemy session without depending on slice B's
migration runner. The ``Package`` ORM model still comes from the real
``zalo_module.models`` (pinned interface).
"""

import hashlib
import json
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from zalo_module.delivery.package import build_package
from zalo_module.settings import get_settings

# Raw DDL copied verbatim from decision-sheet §4 — `packages` table only.
PACKAGES_DDL = """\
CREATE TABLE packages (
  package_id TEXT PRIMARY KEY, consumer_id TEXT NOT NULL,
  sequence INTEGER NOT NULL, manifest_sha256 TEXT NOT NULL,
  record_count INTEGER NOT NULL, dir_rel_path TEXT NOT NULL,
  created_at TEXT NOT NULL, sealed_at TEXT, status TEXT NOT NULL DEFAULT 'pending',
  receipt_json TEXT, UNIQUE(consumer_id, sequence));
"""

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"
ACCOUNT_ID = "a0000000-0000-4000-8000-000000000099"


def _record(text: str) -> dict:
    """Minimal well-formed intake.raw-record.v1, record_kind=message_text
    (envelope per contract §5.1, source per §5.2, body per §5.4)."""
    return {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": str(uuid.uuid4()),
        "logical_id": str(uuid.uuid4()),
        "revision": 1,
        "captured_at": "2026-09-25T01:00:00+00:00",
        "recorded_at": "2026-09-25T01:00:01+00:00",
        "source": {
            "provider": "zalo_personal",
            "account_id": ACCOUNT_ID,
            "conversation_id": "syn-thread-1",
            "conversation_type": "user",
            "provider_message_id": "syn-msg-0001",
            "client_message_id": "syn-cli-0001",
            "sender_id": "syn-user-1",
            "sender_display_name": "Synthetic User",
            "source_sent_at": "2026-09-25T00:59:59+00:00",
            "attachment_id": None,
            "attachment_index": None,
            "page_index": None,
        },
        "message": {"text": text},
    }


def _setup(tmp_path):
    """Settings with a tmp runtime root + a sqlite file DB holding `packages`."""
    settings = get_settings({"ZALO_INTAKE_RUNTIME_DIR": str(tmp_path)})
    engine = sa.create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    )
    with engine.begin() as conn:
        conn.execute(sa.text(PACKAGES_DDL))
    return settings, engine


def _canonical(record: dict) -> str:
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def test_package_bytes(tmp_path):
    settings, engine = _setup(tmp_path)
    records = [
        _record("day la tin nhan gia lap"),
        _record("tin thu hai có dấu tiếng việt"),
    ]

    with Session(engine) as session:
        pid1 = build_package(records, CONSUMER_ID, settings, session)
        pid2 = build_package(records, CONSUMER_ID, settings, session)
        session.commit()

    pkg_dir = settings.runtime_root / "packages" / pid1

    # Whitelist: exactly the three contract files, nothing else.
    assert sorted(p.name for p in pkg_dir.iterdir()) == [
        "READY.json",
        "manifest.json",
        "records.jsonl",
    ]

    raw_records = (pkg_dir / "records.jsonl").read_bytes()
    manifest_bytes = (pkg_dir / "manifest.json").read_bytes()
    ready_bytes = (pkg_dir / "READY.json").read_bytes()

    # Byte rules: UTF-8 no BOM, LF only, every line terminated by \n.
    for blob in (raw_records, manifest_bytes, ready_bytes):
        assert not blob.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in blob
        assert blob.endswith(b"\n")

    # Each JSONL line is exactly one canonical JSON object.
    lines = raw_records.split(b"\n")[:-1]  # trailing \n leaves an empty tail
    assert len(lines) == 2
    assert all(line for line in lines)  # no empty lines
    for line, record in zip(lines, records):
        assert line.decode("utf-8") == _canonical(record)
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        assert parsed == record

    manifest = json.loads(manifest_bytes)
    assert manifest["schema_version"] == "intake.raw-package.v1"
    assert manifest["package_id"] == pid1
    assert manifest["producer"]["service"] == "zalo-intake"
    assert manifest["consumer_id"] == CONSUMER_ID
    assert manifest["sequence"] == 1
    assert manifest["record_count"] == 2
    assert len(manifest["files"]) == 1
    entry = manifest["files"][0]
    assert entry["path"] == "records.jsonl"
    assert entry["sha256"] == hashlib.sha256(raw_records).hexdigest()
    assert entry["bytes"] == len(raw_records)

    ready = json.loads(ready_bytes)
    assert ready["schema_version"] == "intake.ready.v1"
    assert ready["package_id"] == pid1
    assert ready["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()

    # Two consecutive packages get sequences 1, 2 for the same consumer.
    manifest2 = json.loads(
        (settings.runtime_root / "packages" / pid2 / "manifest.json")
        .read_bytes()
    )
    assert manifest2["sequence"] == 2

    with engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT sequence, status, record_count, dir_rel_path "
                "FROM packages WHERE consumer_id = :c ORDER BY sequence"
            ),
            {"c": CONSUMER_ID},
        ).fetchall()
    assert [r[0] for r in rows] == [1, 2]
    # Sealed = READY.json published + ledger row committed; the package then
    # sits in the pending feed until a receipt ACK flips it to "acked".
    assert all(r[1] == "sealed" for r in rows)
    assert all(r[2] == 2 for r in rows)
    # dir_rel_path is relative to runtime_root.
    assert rows[0][3] == f"packages/{pid1}"
