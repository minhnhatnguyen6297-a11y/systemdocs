"""Independent-runtime acceptance — MIN-93 decision sheet section 8.

Every module action runs in a subprocess whose PYTHONPATH is exactly
``<repo>/src`` (see conftest.ModuleProcess), proving the module works with
zero access to notary code. The DB and access log are read back from the
test process as an outside observer.
"""
from __future__ import annotations

import json
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "synthetic"
    / "event_text_message.json"
)


def test_replay_without_notary(module_process):
    """Replay captures durably; a restart loses nothing; nothing touched notary."""
    first = module_process.replay(FIXTURE)
    assert first["created"] is True
    before = module_process.get_capture(first["capture_id"])
    assert before is not None

    module_process.restart()

    after = module_process.get_capture(first["capture_id"])
    assert after is not None
    assert after["captured_at"] == before["captured_at"]
    assert module_process.notary_accesses() == []


def test_replay_idempotent(module_process):
    """Replaying the same event across a restart returns the same capture_id."""
    first = module_process.replay(FIXTURE)

    module_process.restart()

    second = module_process.replay(FIXTURE)
    assert second["capture_id"] == first["capture_id"]
    assert second["source_key"] == first["source_key"]
    assert second["created"] is False
    assert module_process.journal_entry_count() == 1


def test_no_notary_import(module_process):
    """sys.path inside the isolated env contains no notary path."""
    out = module_process.python(
        "import json, sys; print(json.dumps(sys.path))"
    )
    paths = json.loads(out.stdout)
    assert not any("notary" in p.lower() for p in paths), paths


def test_status_smoke(module_process):
    """``cli status`` prints a valid intake.service-status.v1 document."""
    module_process.replay(FIXTURE)
    doc = module_process.status()
    assert doc["schema_version"] == "intake.service-status.v1"
    assert doc["listener"]["state"] == "disconnected"
    assert doc["pending"]["packages"] == 0
    assert doc["storage"]["ack_cap_bytes"] == 1 << 30
    assert doc["capabilities"]["source_event_types"] == {
        "recall": "supported",
        "reaction": "supported",
        "edit": "unsupported",
    }
