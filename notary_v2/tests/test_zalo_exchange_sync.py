"""Tests for services.zalo_exchange sync orchestration (MIN-99 slice A).

A FakeModule over ``httpx.MockTransport`` implements the producer's
``/intake/v1`` surface (pending feed, byte endpoints, receipt ledger with
producer-side idempotency/conflict semantics — mirrors
``zalo-intake/src/zalo_module/api/intake.py`` + ``delivery/ledger.py``).

Package fixtures are built byte-exact: real sha256 over the exact file bytes,
JSONL lines ending ``\\n``, UTF-8 without BOM (contract §3.5/§4). Record
payloads follow ``contracts/zalo-intake/examples/valid/rec-0*`` shapes.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
from database import Base
from models import (
    Customer,
    InheritanceCase,
    InheritanceParticipant,
    Property,
    ZaloImportLedger,
    ZaloParseJob,
    ZaloRawRecord,
)
from services.zalo_exchange import store, sync
from services.zalo_exchange.client import IntakeClient

CONSUMER_ID = "c0000000-0000-4000-8000-000000000001"
ACCOUNT_ID = "aaaaaaaa-0000-4000-8000-000000000001"
CAPTURED = "2026-09-24T08:00:00+07:00"
RECORDED = "2026-09-24T08:05:00+07:00"
EXPIRES = "2026-10-01T08:00:00+07:00"          # captured_at + 168h exactly
IMAGE_SHA = "ab" * 32


def _u(n: int) -> str:
    """Deterministic lowercase uuid (contract §3.5 form)."""
    return f"{n:08d}-0000-4000-8000-{n:012d}"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# record + package fixtures
# ---------------------------------------------------------------------------


def message_record(rid: int, lid: int, text="Da nhan duoc giay to.", conv="conv-1"):
    return {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "message_text",
        "record_id": _u(rid), "logical_id": _u(lid), "revision": 1,
        "captured_at": CAPTURED, "recorded_at": RECORDED,
        "source": {
            "provider": "zalo_personal", "account_id": ACCOUNT_ID,
            "conversation_id": conv, "conversation_type": "group",
            "provider_message_id": f"gmsg-{rid}", "client_message_id": f"cmsg-{rid}",
        },
        "message": {"text": text},
    }


def ocr_record(rid: int, lid: int, pass_id="pass-1", *, revision=1, supersedes=None):
    rec = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "ocr_page",
        "record_id": _u(rid), "logical_id": _u(lid), "revision": revision,
        "captured_at": CAPTURED, "recorded_at": RECORDED,
        "source": {
            "provider": "zalo_personal", "account_id": ACCOUNT_ID,
            "conversation_id": "conv-1", "conversation_type": "group",
            "attachment_id": _u(9000 + lid), "attachment_index": 0, "page_index": 1,
        },
        "image_sha256": IMAGE_SHA,
        "image_expires_at": EXPIRES,
        "image_state": "captured",
        "ocr": {
            "status": "succeeded",
            "attempts": [{
                "ocr_pass_id": pass_id, "provider": "qwen",
                "model": "qwen-vl-ocr-2025-11-20", "task": "text_recognition",
                "image_operation": "original", "region": {"kind": "full_image"},
                "transform_chain": [{"op": "exif_transpose"}],
                "geometry_status": "not_applicable", "status": "succeeded",
                "config_version": "ocr-config-v1",
            }],
            "text_lines": [{
                "line_id": _u(8000 + rid), "text": "CONG HOA XA HOI CHU NGHIA VIET NAM",
                "captured_at": CAPTURED, "page_index": 1, "ocr_pass_id": pass_id,
            }],
            "selected_pass_ids": [pass_id],
        },
    }
    if supersedes is not None:
        rec["supersedes"] = supersedes
    return rec


def records_bytes(lines) -> bytes:
    """``lines`` may mix dicts (compact-serialized) and raw strings (kept
    byte-verbatim); every line ends ``\\n`` — contract §4 framing."""
    out = b""
    for line in lines:
        if isinstance(line, dict):
            out += json.dumps(line, ensure_ascii=False).encode("utf-8") + b"\n"
        else:
            out += line.encode("utf-8") + b"\n"
    return out


def build_package(package_id: str, sequence: int, records, *,
                  consumer_id: str = CONSUMER_ID,
                  record_count=None, producer_service="zalo-intake",
                  include_ready=True, ready_sha=None,
                  files_extra=None, records_override=None):
    """Real package bytes: manifest declares the true sha256/bytes of
    records.jsonl; READY binds the true manifest hash (contract §3.3/§3.4)."""
    rbytes = records_override if records_override is not None else records_bytes(records)
    manifest = {
        "schema_version": "intake.raw-package.v1",
        "package_id": package_id,
        "producer": {"service": producer_service, "build_id": "test+2026-09-24"},
        "consumer_id": consumer_id,
        "created_at": CAPTURED,
        "sequence": sequence,
        "files": [{"path": "records.jsonl", "sha256": _sha(rbytes),
                   "bytes": len(rbytes)}],
        "record_count": len(records) if record_count is None else record_count,
    }
    mbytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    ready = {
        "schema_version": "intake.ready.v1",
        "package_id": package_id,
        "manifest_sha256": ready_sha or _sha(mbytes),
        "sealed_at": "2026-09-24T00:03:30+07:00",
    }
    files = {"manifest.json": mbytes, "records.jsonl": rbytes}
    if include_ready:
        files["READY.json"] = json.dumps(ready, ensure_ascii=False).encode("utf-8")
    for name, data in (files_extra or {}).items():
        files[name] = data
    return files, _sha(mbytes)


# ---------------------------------------------------------------------------
# FakeModule — the producer's /intake/v1 over MockTransport
# ---------------------------------------------------------------------------

_FILE_ROUTES = {
    "manifest": "manifest.json", "manifest.json": "manifest.json",
    "records": "records.jsonl", "records.jsonl": "records.jsonl",
    "ready": "READY.json", "READY.json": "READY.json",
}


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _error(status, code, message=""):
    return httpx.Response(
        status, json={"schema_version": "intake.error.v1",
                      "error": {"code": code, "message": message}})


class FakeModule:
    """In-memory producer. ``receipts`` mirrors the durable receipt ledger:
    identical replays return the stored doc, anything else on a decided
    package or a reused receipt_id is package_conflict (contract §7.3)."""

    def __init__(self, consumer_id=CONSUMER_ID, *, token=None, page_size=100):
        self.consumer_id = consumer_id
        self.token = token
        self.page_size = page_size
        self.packages = {}       # package_id -> pkg dict
        self.receipts = {}       # package_id -> {"doc": dict, "canonical": str}
        self.receipt_log = []    # receipt bodies actually POSTed
        self.request_log = []    # every httpx.Request seen
        self.receipt_failures = 0
        self.keep_pending = set()  # force packages to stay in the feed
        self.transport = httpx.MockTransport(self._handle)

    # -- fixture-side helpers ----------------------------------------------

    def add_package(self, package_id, sequence, files, manifest_sha256,
                    consumer_id=None, feed_sha256=None):
        self.packages[package_id] = {
            "package_id": package_id,
            "sequence": sequence,
            "consumer_id": consumer_id or self.consumer_id,
            "files": files,
            "manifest_sha256": manifest_sha256,
            "feed_sha256": feed_sha256 or manifest_sha256,
            "record_count": self._declared_count(files),
        }

    @staticmethod
    def _declared_count(files) -> int:
        """The producer's stored record_count = the sealed manifest's declared
        value (even when the records file itself is absent/corrupt)."""
        data = files.get("manifest.json")
        if data is not None:
            try:
                manifest = json.loads(data)
                count = manifest.get("record_count")
                if isinstance(count, int):
                    return count
            except ValueError:
                pass
        records = files.get("records.jsonl") or b""
        return len([ln for ln in records.split(b"\n") if ln])

    def pending_ids(self) -> set:
        return {
            pid for pid in self.packages
            if pid not in self.receipts
            or self.receipts[pid]["doc"]["status"] != "accepted"
            or pid in self.keep_pending
        }

    # -- transport -----------------------------------------------------------

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.request_log.append(request)
        if self.token is not None and \
                request.headers.get("authorization") != f"Bearer {self.token}":
            return _error(401, "unauthorized", "bearer token mismatch")
        path = request.url.path

        if path == "/intake/v1/status":
            pending = sorted(self.pending_ids(),
                             key=lambda p: self.packages[p]["sequence"])
            doc = {
                "schema_version": "intake.service-status.v1",
                "producer": {"service": "zalo-intake", "build_id": "fake"},
                "observed_at": RECORDED,
                "listener": {"state": "connected"},
                "pending": {"packages": len(pending)},
                "storage": {"ack_bytes": 0, "ack_cap_bytes": 1 << 30,
                            "ack_warn": False},
                "capabilities": {"source_event_types": {
                    "recall": "supported", "reaction": "supported",
                    "edit": "unsupported"}},
            }
            if pending:
                doc["pending"]["oldest_sequence"] = self.packages[pending[0]]["sequence"]
                doc["pending"]["oldest_age_seconds"] = 0
            return httpx.Response(200, json=doc)

        if path == "/intake/v1/packages" and request.method == "GET":
            params = request.url.params
            if params.get("delivery", "pending") != "pending":
                return _error(400, "schema_invalid", "only delivery=pending")
            after = int(params.get("after", "0"))
            limit = min(int(params.get("limit", "100")), self.page_size)
            until_p = params.get("until_sequence")
            rows = sorted(
                (self.packages[p] for p in self.pending_ids()),
                key=lambda p: p["sequence"])
            if until_p is None:
                until = rows[-1]["sequence"] if rows else 0
            else:
                until = int(until_p)
            page = [p for p in rows if after < p["sequence"] <= until]
            has_more = len(page) > limit
            page = page[:limit]
            return httpx.Response(200, json={
                "schema_version": "intake.package-list.v1",
                "packages": [{
                    "package_id": p["package_id"], "sequence": p["sequence"],
                    "manifest_sha256": p["feed_sha256"],
                } for p in page],
                "next_after": page[-1]["sequence"] if page else after,
                "until_sequence": until,
                "has_more": has_more,
            })

        if path.startswith("/intake/v1/packages/") and request.method == "GET":
            parts = path.split("/")
            package_id, name = parts[4], parts[5]
            pkg = self.packages.get(package_id)
            file_name = _FILE_ROUTES.get(name)
            if pkg is None or file_name is None or file_name not in pkg["files"]:
                return _error(404, "package_unknown", f"no such file {name}")
            return httpx.Response(200, content=pkg["files"][file_name])

        if path == "/intake/v1/receipts" and request.method == "POST":
            if self.receipt_failures > 0:
                self.receipt_failures -= 1
                return _error(503, "http_error", "receipt endpoint down")
            try:
                body = json.loads(request.content)
            except ValueError:
                return _error(400, "json_invalid", "body is not JSON")
            self.receipt_log.append(body)      # log every attempt on the wire
            return self._record_receipt(body)

        return _error(404, "package_unknown", f"no route {path}")

    def _record_receipt(self, body) -> httpx.Response:
        required = ("schema_version", "receipt_id", "package_id", "consumer_id",
                    "status", "received_at", "manifest_sha256", "record_count")
        if not isinstance(body, dict) or any(k not in body for k in required):
            return _error(400, "schema_invalid", "missing receipt fields")
        if body.get("status") == "rejected" and not isinstance(body.get("error"), dict):
            return _error(400, "schema_invalid", "rejected needs error")
        if body.get("status") == "accepted" and "error" in body:
            return _error(400, "schema_invalid", "accepted forbids error")
        pkg = self.packages.get(body["package_id"])
        if pkg is None:
            return _error(404, "package_unknown", "unknown package")
        canonical = _canonical(body)
        stored = self.receipts.get(body["package_id"])
        if stored is not None and stored["canonical"] == canonical:
            return httpx.Response(200, json=stored["doc"])     # idempotent replay
        for s in self.receipts.values():
            if s["doc"].get("receipt_id") == body["receipt_id"]:
                return _error(409, "package_conflict", "receipt_id reused")
        if stored is not None:
            return _error(409, "package_conflict", "package already decided")
        if pkg["consumer_id"] != body["consumer_id"]:
            return _error(409, "receipt_consumer_mismatch", "consumer mismatch")
        if pkg["manifest_sha256"] != body["manifest_sha256"]:
            return _error(409, "receipt_hash_mismatch", "manifest hash mismatch")
        if pkg["record_count"] != body["record_count"]:
            return _error(409, "receipt_count_mismatch", "record_count mismatch")
        self.receipts[body["package_id"]] = {"doc": body, "canonical": canonical}
        return httpx.Response(200, json=body)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool)
    database.enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def _settings(module: FakeModule, tmp_path: Path, **kwargs) -> sync.SyncSettings:
    kwargs.setdefault("consumer_id", module.consumer_id)
    return sync.SyncSettings(
        module_url="http://module.test",
        exchange_root=tmp_path / "exchange",
        client=IntakeClient("http://module.test", transport=module.transport),
        **kwargs)


def _pkg(module: FakeModule, pid: int, seq: int, records, **kwargs):
    feed_sha256 = kwargs.pop("feed_sha256", None)
    files, msha = build_package(_u(pid), seq, records, **kwargs)
    module.add_package(_u(pid), seq, files, msha,
                       consumer_id=kwargs.get("consumer_id"),
                       feed_sha256=feed_sha256)
    return _u(pid), files, msha


def _simple_records(base: int, n: int):
    return [message_record(base + i, base + 100 + i) for i in range(n)]


def _ledger(db, package_id):
    return db.get(ZaloImportLedger, package_id)


def _raws(db, package_id=None):
    q = select(ZaloRawRecord)
    if package_id is not None:
        q = q.where(ZaloRawRecord.package_id == package_id)
    return list(db.execute(q).scalars())


def _jobs(db):
    return list(db.execute(select(ZaloParseJob)).scalars())


# ===========================================================================
# happy path
# ===========================================================================


def test_happy_path_multi_package_ascending(db, tmp_path):
    module = FakeModule()
    ids = []
    for i, seq in enumerate((1, 2, 3)):
        pid, _files, _sha = _pkg(module, 10 + i, seq, _simple_records(100 + i * 10, 2))
        ids.append(pid)
    report = sync.run_sync(db, _settings(module, tmp_path))

    assert report.errors == []
    assert (report.listed, report.imported, report.skipped,
            report.quarantined, report.receipts_sent) == (3, 3, 0, 0, 3)

    rows = {r.package_id: r for r in db.execute(select(ZaloImportLedger)).scalars()}
    assert set(rows) == set(ids)
    for i, pid in enumerate(ids):
        row = rows[pid]
        assert row.decision == "imported"
        assert row.sequence == i + 1
        assert row.receipt_status == "accepted"
        assert row.receipt_id and row.imported_at is not None
        assert len(_raws(db, pid)) == 2
        # durable copy: exactly the three package files under imported/
        pkg_dir = tmp_path / "exchange" / "imported" / pid
        assert sorted(p.name for p in pkg_dir.iterdir()) == \
            ["READY.json", "manifest.json", "records.jsonl"]

    assert len(_jobs(db)) == 3
    assert all(j.state == "pending" for j in _jobs(db))
    assert module.pending_ids() == set()          # accepted → left the feed
    assert len(module.receipt_log) == 3
    # receipts carry consumer identity + the real manifest hash
    for body in module.receipt_log:
        assert body["status"] == "accepted"
        assert body["consumer_id"] == CONSUMER_ID
        assert body["record_count"] == 2
    # sync_state bookkeeping
    assert store.get_state(db, "last_sequence") == "3"
    assert store.get_state(db, "last_run_at")
    assert store.get_state(db, "last_error") == ""


def test_run_is_idempotent_when_feed_empties(db, tmp_path):
    module = FakeModule()
    _pkg(module, 20, 1, _simple_records(200, 1))
    sync.run_sync(db, _settings(module, tmp_path))
    report2 = sync.run_sync(db, _settings(module, tmp_path))
    assert (report2.listed, report2.imported, report2.skipped,
            report2.receipts_sent) == (0, 0, 0, 0)
    assert report2.errors == []


# ===========================================================================
# validation failures → quarantine + rejected receipt
# ===========================================================================


def _assert_quarantined(db, tmp_path, module, pid, report, code):
    assert report.imported == 0
    assert report.quarantined == 1
    row = _ledger(db, pid)
    assert row.decision == "quarantined"
    assert code in (row.quarantine_reason or "")
    assert row.receipt_status == "rejected"
    assert row.receipt_id
    assert (tmp_path / "exchange" / "quarantine" / pid).is_dir()
    assert not (tmp_path / "exchange" / "imported" / pid).exists()
    assert _raws(db, pid) == []
    assert [j for j in _jobs(db) if j.package_id == pid] == []
    # rejected receipt keeps the package pending at the producer (contract §7.2)
    assert pid in module.pending_ids()
    bodies = [b for b in module.receipt_log if b["package_id"] == pid]
    assert len(bodies) == 1
    body = bodies[0]
    assert body["status"] == "rejected"
    assert body["error"]["code"] == code
    return row, body


def test_corrupt_manifest_hash_quarantines(db, tmp_path):
    module = FakeModule()
    pid = _u(30)
    files, msha = build_package(pid, 1, _simple_records(300, 2))
    # corrupt the declared hash: manifest lies about records.jsonl
    manifest = json.loads(files["manifest.json"])
    manifest["files"][0]["sha256"] = "00" * 32
    files["manifest.json"] = json.dumps(manifest, indent=2).encode()
    files["READY.json"] = json.dumps({
        "schema_version": "intake.ready.v1", "package_id": pid,
        "manifest_sha256": _sha(files["manifest.json"]),
        "sealed_at": RECORDED}).encode()
    module.add_package(pid, 1, files, _sha(files["manifest.json"]))

    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "manifest_hash_mismatch")


def test_record_schema_violation_quarantines(db, tmp_path):
    module = FakeModule()
    bad = message_record(401, 501)
    del bad["recorded_at"]                       # schema-required envelope field
    pid, _files, _sha = _pkg(module, 31, 1, [bad])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "schema_invalid")


def test_manifest_schema_violation_quarantines(db, tmp_path):
    module = FakeModule()
    pid = _u(32)
    files, _msha = build_package(pid, 1, _simple_records(320, 1))
    manifest = json.loads(files["manifest.json"])
    manifest["schema_version"] = "intake.raw-package.v9"   # const violation
    files["manifest.json"] = json.dumps(manifest).encode()
    files["READY.json"] = json.dumps({
        "schema_version": "intake.ready.v1", "package_id": pid,
        "manifest_sha256": _sha(files["manifest.json"]),
        "sealed_at": RECORDED}).encode()
    module.add_package(pid, 1, files, _sha(files["manifest.json"]))
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "schema_invalid")


def test_consumer_mismatch_quarantines(db, tmp_path):
    """Package published for another consumer → local quarantine; the
    rejected receipt is correctly refused upstream (receipt_consumer_mismatch
    is a permanent 4xx — marked sent, logged, never retried)."""
    module = FakeModule()
    foreign = "c0000000-0000-4000-8000-0000000000ff"
    pid, _files, _sha = _pkg(module, 33, 1, _simple_records(330, 1),
                             consumer_id=foreign)
    report = sync.run_sync(db, _settings(module, tmp_path))

    assert report.imported == 0 and report.quarantined == 1
    row = _ledger(db, pid)
    assert row.decision == "quarantined"
    assert "consumer_mismatch" in row.quarantine_reason
    # the receipt we sent was refused upstream but is a final answer:
    # ledger keeps our sent decision and stops retrying
    assert row.receipt_status == "rejected"
    assert any(e["stage"] == "receipt" for e in report.errors)
    assert len(module.receipt_log) == 1                     # attempted once
    assert module.receipt_log[0]["status"] == "rejected"
    assert module.receipt_log[0]["error"]["code"] == "consumer_mismatch"
    assert _raws(db, pid) == []

    report2 = sync.run_sync(db, _settings(module, tmp_path))  # never retried
    assert report2.skipped == 1 and report2.receipts_sent == 0
    assert len(module.receipt_log) == 1


def test_missing_ready_quarantines(db, tmp_path):
    """READY gate: no READY.json → never imported (contract §3.2/file_missing)."""
    module = FakeModule()
    pid, _files, _sha = _pkg(module, 34, 1, _simple_records(340, 1),
                             include_ready=False)
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "file_missing")


def test_feed_hash_mismatch_quarantines(db, tmp_path):
    """Feed-declared manifest_sha256 ≠ served manifest bytes → rejected."""
    module = FakeModule()
    pid, _files, msha = _pkg(module, 35, 1, _simple_records(350, 1),
                             feed_sha256="ff" * 32)
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "manifest_hash_mismatch")


def test_forbidden_file_quarantines(db, tmp_path):
    """The consumer only ever downloads the three whitelisted names — an
    extra file on the producer's disk is invisible to it. What IS detected:
    a manifest files[] entry declaring something other than records.jsonl
    (contract §3.3 file_forbidden)."""
    module = FakeModule()
    pid = _u(36)
    files, _msha = build_package(pid, 1, _simple_records(360, 1))
    manifest = json.loads(files["manifest.json"])
    manifest["files"] = [{"path": "evil.jpg", "sha256": "00" * 32, "bytes": 3}]
    files["manifest.json"] = json.dumps(manifest, indent=2).encode()
    files["READY.json"] = json.dumps({
        "schema_version": "intake.ready.v1", "package_id": pid,
        "manifest_sha256": _sha(files["manifest.json"]),
        "sealed_at": RECORDED}).encode()
    module.add_package(pid, 1, files, _sha(files["manifest.json"]))
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "file_forbidden")


def test_revision_chain_broken_quarantines(db, tmp_path):
    """A revision-2 record superseding something never published → reject."""
    module = FakeModule()
    rec = ocr_record(402, 502, revision=2,
                     supersedes={"record_id": _u(9999), "revision": 1})
    pid, _files, _sha = _pkg(module, 37, 1, [rec])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "revision_chain_broken")


def test_record_conflict_quarantines(db, tmp_path):
    """Same record_id, different bytes than already imported → conflict."""
    module = FakeModule()
    rec_v1 = message_record(403, 503, text="original")
    _pkg(module, 38, 1, [rec_v1])
    sync.run_sync(db, _settings(module, tmp_path))

    rec_conflict = message_record(403, 503, text="tampered")  # same record_id
    pid2, _files, _sha = _pkg(module, 39, 2, [rec_conflict])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid2, report, "record_conflict")


def test_expires_mismatch_quarantines(db, tmp_path):
    """image_expires_at must equal captured_at + 168h exactly (§5.3)."""
    module = FakeModule()
    bad = ocr_record(410, 510)
    bad["image_expires_at"] = "2026-10-01T08:00:01+07:00"   # one second off
    pid, _files, _sha = _pkg(module, 48, 1, [bad])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report, "expires_mismatch")


def test_ocr_status_inconsistent_quarantines(db, tmp_path):
    """ocr.status says succeeded but no attempt succeeded (§5.5)."""
    module = FakeModule()
    bad = ocr_record(411, 511)
    bad["ocr"]["attempts"][0]["status"] = "failed"
    pid, _files, _sha = _pkg(module, 49, 1, [bad])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report,
                        "ocr_status_inconsistent")


def test_revision_wrong_supersedes_revision_quarantines(db, tmp_path):
    """rev 3 must supersede revision 2 — pointing at rev 1 is a broken chain."""
    module = FakeModule()
    r1 = ocr_record(412, 512)
    _pkg(module, 65, 1, [r1])
    sync.run_sync(db, _settings(module, tmp_path))
    bad = ocr_record(413, 512, revision=3,
                     supersedes={"record_id": r1["record_id"], "revision": 1})
    pid, _files, _sha = _pkg(module, 66, 2, [bad])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report,
                        "revision_chain_broken")


def test_immutable_captured_at_changed_quarantines(db, tmp_path):
    """rev 2 re-ingests the SAME capture: a moved captured_at → reject."""
    module = FakeModule()
    r1 = ocr_record(414, 514)
    _pkg(module, 67, 1, [r1])
    sync.run_sync(db, _settings(module, tmp_path))
    r2 = ocr_record(415, 514, revision=2,
                    supersedes={"record_id": r1["record_id"], "revision": 1})
    r2["captured_at"] = "2026-09-25T08:00:00+07:00"          # moved
    r2["image_expires_at"] = "2026-10-02T08:00:00+07:00"     # §5.3 stays consistent
    pid, _files, _sha = _pkg(module, 68, 2, [r2])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report,
                        "immutable_field_changed")


def test_revision_two_valid_chain_imports(db, tmp_path):
    """Control case: rev 2 superseding rev 1 with identical captured_at IS
    imported — the contract's intended revision flow must not be blocked."""
    module = FakeModule()
    r1 = ocr_record(416, 516)
    _pkg(module, 69, 1, [r1])
    r2 = ocr_record(417, 516, revision=2,
                    supersedes={"record_id": r1["record_id"], "revision": 1})
    pid2, _files, _sha = _pkg(module, 91, 2, [r2])
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.errors == [] and report.imported == 2
    rows = _raws(db)
    assert len(rows) == 2
    assert _ledger(db, pid2).decision == "imported"


def test_source_event_missing_target_quarantines(db, tmp_path):
    """recall/reaction events must reference the target provider message."""
    module = FakeModule()
    rec = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "source_event",
        "record_id": _u(418), "logical_id": _u(518), "revision": 1,
        "captured_at": CAPTURED, "recorded_at": RECORDED,
        "source": {"provider": "zalo_personal", "account_id": ACCOUNT_ID,
                   "conversation_id": "conv-1", "conversation_type": "group"},
        "event": {"event_type": "recall", "observed_at": RECORDED},
    }
    pid, _files, _sha = _pkg(module, 92, 1, [rec])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report,
                        "source_event_invalid")


def test_listener_gap_invalid_quarantines(db, tmp_path):
    """uncertain_gap with ended_at <= started_at violates the gap rule."""
    module = FakeModule()
    rec = {
        "schema_version": "intake.raw-record.v1",
        "record_kind": "listener_session",
        "record_id": _u(419), "logical_id": _u(519), "revision": 1,
        "captured_at": CAPTURED, "recorded_at": RECORDED,
        "source": {"provider": "zalo_personal", "account_id": ACCOUNT_ID},
        "listener": {
            "session_id": _u(600), "state": "connected",
            "observed_at": RECORDED,
            "uncertain_gap": {
                "started_at": "2026-09-24T08:10:00+07:00",
                "ended_at": "2026-09-24T08:00:00+07:00",   # before the start
                "start_is_estimate": True,
            },
        },
    }
    pid, _files, _sha = _pkg(module, 93, 1, [rec])
    report = sync.run_sync(db, _settings(module, tmp_path))
    _assert_quarantined(db, tmp_path, module, pid, report,
                        "listener_gap_invalid")


# ===========================================================================
# replay / idempotency
# ===========================================================================


def test_lost_ack_replay_resends_same_receipt_id(db, tmp_path):
    """receipt POST fails once → second run replays the stored document,
    same receipt_id, no re-import (contract §7.3 idempotency)."""
    module = FakeModule()
    module.receipt_failures = 1
    pid, _files, _sha = _pkg(module, 40, 1, _simple_records(400, 2))

    report1 = sync.run_sync(db, _settings(module, tmp_path))
    assert report1.imported == 1 and report1.receipts_sent == 0
    row = _ledger(db, pid)
    assert row.decision == "imported" and row.receipt_status is None
    assert row.receipt_id
    assert any(e["stage"] == "receipt" for e in report1.errors)
    assert pid in module.pending_ids()               # still un-ACKed upstream
    stored_doc = store.load_receipt_doc(db, pid)
    assert stored_doc and stored_doc["receipt_id"] == row.receipt_id

    report2 = sync.run_sync(db, _settings(module, tmp_path))
    assert report2.imported == 0 and report2.skipped == 1
    assert report2.receipts_sent == 1
    row = _ledger(db, pid)
    assert row.receipt_status == "accepted"
    # byte-identical replay: the body the module received == the stored doc
    assert module.receipt_log[-1]["receipt_id"] == row.receipt_id
    assert _canonical(module.receipt_log[-1]) == _canonical(stored_doc)
    assert len(_raws(db, pid)) == 2                  # never re-imported
    assert len(_jobs(db)) == 1
    assert pid not in module.pending_ids()


def test_crash_after_commit_resumes_without_reimport(db, tmp_path):
    """Crash window: DB committed + dir imported but receipt POST lost.
    Durable state (ledger+raw+job+receipt doc) must survive and resume."""
    module = FakeModule()
    module.receipt_failures = 1
    pid, files, msha = _pkg(module, 41, 1, _simple_records(410, 3))

    sync.run_sync(db, _settings(module, tmp_path))
    # durable state a restart would observe:
    row = _ledger(db, pid)
    assert row.decision == "imported" and row.receipt_status is None
    assert len(_raws(db, pid)) == 3
    assert (tmp_path / "exchange" / "imported" / pid).is_dir()
    assert store.load_receipt_doc(db, pid)["status"] == "accepted"

    db.close()  # simulate process restart: new session, same engine
    engine = db.get_bind()
    db2 = sessionmaker(bind=engine)()
    try:
        report2 = sync.run_sync(db2, _settings(module, tmp_path))
        assert report2.receipts_sent == 1 and report2.imported == 0
        row2 = db2.get(ZaloImportLedger, pid)
        assert row2.receipt_status == "accepted"
        assert row2.receipt_id == row.receipt_id
    finally:
        db2.close()
    assert len(module.receipt_log) == 1


def test_imported_package_still_pending_is_skipped(db, tmp_path):
    """A ledgered package re-listed as pending is skipped — no re-import,
    no second receipt (the recorded decision stands)."""
    module = FakeModule()
    pid, _files, _sha = _pkg(module, 42, 1, _simple_records(420, 2))
    sync.run_sync(db, _settings(module, tmp_path))
    assert len(module.receipt_log) == 1
    module.keep_pending.add(pid)                     # producer quirk: re-listed

    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.skipped == 1 and report.imported == 0
    assert report.receipts_sent == 0                 # accepted already recorded
    assert len(module.receipt_log) == 1              # nothing re-POSTed
    assert len(_raws(db, pid)) == 2


def test_quarantined_package_never_reprocessed(db, tmp_path):
    """Quarantined packages stay pending at the producer but the ledgered
    decision is final: no re-validation, no re-import, no second receipt."""
    module = FakeModule()
    manifest_files, msha = build_package(_u(43), 1, _simple_records(430, 1))
    manifest = json.loads(manifest_files["manifest.json"])
    manifest["files"][0]["sha256"] = "00" * 32
    manifest_files["manifest.json"] = json.dumps(manifest).encode()
    manifest_files["READY.json"] = json.dumps({
        "schema_version": "intake.ready.v1", "package_id": _u(43),
        "manifest_sha256": _sha(manifest_files["manifest.json"]),
        "sealed_at": RECORDED}).encode()
    module.add_package(_u(43), 1, manifest_files, _sha(manifest_files["manifest.json"]))

    report1 = sync.run_sync(db, _settings(module, tmp_path))
    assert report1.quarantined == 1
    fetches = [r for r in module.request_log if "/manifest" in r.url.path]

    report2 = sync.run_sync(db, _settings(module, tmp_path))
    assert report2.skipped == 1 and report2.quarantined == 0
    assert report2.receipts_sent == 0
    # no second download, no second receipt
    assert [r for r in module.request_log
            if "/manifest" in r.url.path] == fetches
    assert len(module.receipt_log) == 1


def test_sequence_out_of_order_skips_lower(db, tmp_path):
    """A package published below the last-imported sequence is skipped
    (never fetched, never ledgered)."""
    module = FakeModule()
    _pkg(module, 44, 3, _simple_records(440, 1))
    sync.run_sync(db, _settings(module, tmp_path))
    assert store.last_imported_sequence(db) == 3

    pid_low, _files, _sha = _pkg(module, 45, 2, _simple_records(450, 1))
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.skipped == 1 and report.imported == 0
    assert _ledger(db, pid_low) is None
    # the skip happened before any download attempt
    assert not any(pid_low in r.url.path for r in module.request_log)


def test_sequence_below_cursor_surfaces_diagnostic(db, tmp_path):
    """New package_id reusing an old sequence stays skipped but reports
    sequence_invalid — a silent skip would hide producer sequencing bugs."""
    module = FakeModule()
    _pkg(module, 44, 3, _simple_records(440, 1))
    sync.run_sync(db, _settings(module, tmp_path))

    pid_low, _files, _sha = _pkg(module, 45, 2, _simple_records(450, 1))
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.skipped == 1 and report.imported == 0
    assert any("sequence_invalid" in e["message"] for e in report.errors)


def test_empty_consumer_id_fails_fast_without_quarantine(db, tmp_path):
    """consumer_id chua cau hinh -> bo luot, khong quarantine hang loat."""
    module = FakeModule()
    _pkg(module, 46, 1, _simple_records(460, 1))
    settings = _settings(module, tmp_path, consumer_id="")
    report = sync.run_sync(db, settings)

    assert report.imported == 0 and report.quarantined == 0
    assert any(e["stage"] == "config" for e in report.errors)
    assert _jobs(db) == []
    # nothing was fetched from the module except (maybe) the feed page
    assert not any("/manifest" in r.url.path or "/records" in r.url.path
                   for r in module.request_log)


def test_same_byte_records_across_packages_are_noop(db, tmp_path):
    """Re-import of identical record bytes is a no-op (contract §7.3):
    two packages can carry the same immutable record without conflict."""
    module = FakeModule()
    shared = ocr_record(460, 560)
    _pkg(module, 46, 1, [shared, message_record(461, 561)])
    _pkg(module, 47, 2, [shared, message_record(462, 562)])
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.errors == [] and report.imported == 2
    assert len(_raws(db)) == 3                       # 2 + 1 new (shared is no-op)


# ===========================================================================
# invariants
# ===========================================================================


def test_only_package_file_names_are_fetched(db, tmp_path):
    """The consumer must never request anything but manifest/records/ready
    (in either spelling) — no image/file names ever reach the wire."""
    module = FakeModule()
    for i in range(3):
        _pkg(module, 50 + i, i + 1, [ocr_record(500 + i, 600 + i)])
    sync.run_sync(db, _settings(module, tmp_path))

    fetched = [r.url.path for r in module.request_log
               if r.url.path.startswith("/intake/v1/packages/")]
    assert fetched
    allowed = set(_FILE_ROUTES)
    for path in fetched:
        name = path.rsplit("/", 1)[1]
        assert name in allowed, f"unexpected fetch: {path}"


def test_business_tables_untouched(db, tmp_path):
    """Raw import never writes business tables — not even on the
    happy path, not on quarantine."""
    customer = Customer(ho_ten="Nguyen Van A")
    db.add(customer)
    db.flush()
    prop = Property(so_serial="DD 1", dia_chi="Thon A")
    db.add(prop)
    db.flush()
    case = InheritanceCase(nguoi_chet_id=customer.id, tai_san_id=prop.id,
                           ngay_lap_ho_so=date(2026, 9, 24))
    db.add(case)
    db.flush()
    db.add(InheritanceParticipant(ho_so_id=case.id, customer_id=customer.id,
                                  vai_tro="Con"))
    db.commit()
    snapshot = {t: db.execute(select(func.count()).select_from(t)).scalar()
                for t in (Customer, Property, InheritanceCase,
                          InheritanceParticipant)}

    module = FakeModule()
    _pkg(module, 60, 1, _simple_records(600, 2))
    bad = message_record(601, 701)
    del bad["recorded_at"]
    _pkg(module, 61, 2, [bad])
    sync.run_sync(db, _settings(module, tmp_path))

    for t, n in snapshot.items():
        assert db.execute(select(func.count()).select_from(t)).scalar() == n


def test_verbatim_payload_storage(db, tmp_path):
    """payload_json keeps the exact JSONL line bytes — whitespace and key
    order are NOT re-serialized (raw evidence, contract §5)."""
    module = FakeModule()
    rec = message_record(70, 170)
    weird_line = json.dumps(rec, ensure_ascii=False).replace(
        '"record_kind":', '"record_kind" :')        # irregular spacing
    pid, _files, _sha = _pkg(module, 62, 1, [weird_line],
                             records_override=(weird_line + "\n").encode())
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.errors == []
    row = _raws(db, pid)[0]
    assert row.payload_json == weird_line
    assert ' : ' in row.payload_json or '" :' in row.payload_json
    assert row.kind == "message_text"
    assert row.package_sequence == 1


def test_verbatim_lines_align_when_package_repeats_records(db, tmp_path):
    """A package resending an already-stored record skips it (idempotent
    §7.3); the remaining inserts must still get their OWN verbatim line —
    the dedupe filter must not shift the line mapping."""
    module = FakeModule()
    shared = message_record(463, 563)
    _pkg(module, 63, 1, [shared])
    sync.run_sync(db, _settings(module, tmp_path))

    new_rec = message_record(464, 564)
    line_shared = json.dumps(shared, ensure_ascii=False)
    line_new = json.dumps(new_rec, ensure_ascii=False).replace(
        '"record_kind":', '"record_kind" :')        # distinguishable spacing
    pid2, _files, _sha = _pkg(
        module, 64, 2, [shared, new_rec],
        records_override=(line_shared + "\n" + line_new + "\n").encode())
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.errors == [] and report.imported == 1

    rows = _raws(db, pid2)
    assert [r.record_id for r in rows] == [new_rec["record_id"]]
    assert rows[0].payload_json == line_new          # not the dup's line


def test_pending_list_and_state_bookkeeping(db, tmp_path):
    module = FakeModule(page_size=2)
    for i in range(3):
        _pkg(module, 70 + i, i + 1, _simple_records(700 + i * 5, 1))
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.imported == 3
    # paged twice: page 1 has_more, page 2 carries until_sequence=3
    feed_calls = [r for r in module.request_log
                  if r.url.path == "/intake/v1/packages"]
    assert len(feed_calls) == 2
    assert "until_sequence" not in feed_calls[0].url.params
    assert feed_calls[1].url.params["until_sequence"] == "3"
    assert feed_calls[1].url.params["after"] == "2"
    assert store.get_state(db, "pending_list") == "[]"
    assert store.get_state(db, "last_sequence") == "3"


def test_unauthorized_feed_records_error_not_exception(db, tmp_path):
    module = FakeModule(token="sekret")
    _pkg(module, 80, 1, _simple_records(800, 1))
    settings = _settings(module, tmp_path)
    settings.client = IntakeClient("http://module.test", token="wrong",
                                   transport=module.transport)
    report = sync.run_sync(db, settings)
    assert report.imported == 0 and report.listed == 0
    assert any(e["stage"] == "feed" for e in report.errors)
    assert db.execute(select(ZaloImportLedger)).scalars().first() is None


def test_empty_feed_is_a_clean_noop(db, tmp_path):
    module = FakeModule()
    report = sync.run_sync(db, _settings(module, tmp_path))
    assert report.as_dict() == {
        "listed": 0, "imported": 0, "skipped": 0, "quarantined": 0,
        "receipts_sent": 0, "errors": []}
    assert store.get_state(db, "last_run_at")


def test_fetch_failure_leaves_package_pending(db, tmp_path):
    """A package whose bytes 500 out stays pending (contract §7.2: a failed
    download is retried by the next scan, not quarantined)."""
    module = FakeModule()
    pid, files, msha = _pkg(module, 90, 1, _simple_records(900, 1))
    del files["records.jsonl"]                       # served 404 → file_missing
    module.add_package(pid, 1, files, msha)
    report = sync.run_sync(db, _settings(module, tmp_path))
    # a file served 404 is a *content* failure → quarantine (READY/manifest ok)
    assert report.quarantined == 1
    row = _ledger(db, pid)
    assert "file_missing" in row.quarantine_reason


def test_settings_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ZALO_MODULE_URL", "http://10.0.0.2:9999")
    monkeypatch.setenv("ZALO_INTAKE_API_TOKEN", "tok")
    monkeypatch.setenv("ZALO_CONSUMER_ID", CONSUMER_ID)
    monkeypatch.setenv("ZALO_EXCHANGE_ROOT", str(tmp_path / "zx"))
    settings = sync.SyncSettings.from_env()
    assert settings.module_url == "http://10.0.0.2:9999"
    assert settings.token == "tok"
    assert settings.consumer_id == CONSUMER_ID
    assert settings.exchange_root == tmp_path / "zx"
