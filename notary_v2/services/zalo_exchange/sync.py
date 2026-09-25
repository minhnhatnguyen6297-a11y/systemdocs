"""Sync orchestration — pull pending raw packages from the Zalo module,
validate, import durably, then ACK (contract §7, decision sheet MIN-99).

One ``run_sync`` pass:

1. Page the pending feed ``GET /intake/v1/packages`` from ``after=0``; the
   first response pins ``until_sequence`` and later pages reuse it. The
   accumulated ``package_id``/``manifest_sha256`` list is persisted to
   ``zalo_sync_state`` before turning each page (contract §7.2.4).
2. Per package, ascending sequence:
   - ledger hit → never re-import; only re-send the stored receipt document
     when its POST is still unconfirmed (lost-ACK replay, same receipt_id).
   - ``sequence <= last imported`` → skip (idempotent, never an error).
   - download manifest/records/ready bytes into ``staging/<package_id>/``
     (staging is rebuildable — crashes just re-download).
   - ``validate_package`` → on any error: move to ``quarantine/<id>/``,
     ledger ``decision=quarantined`` + stored rejected-receipt doc in ONE
     commit, then POST the receipt.
   - clean → move ``staging`` → ``ready`` → ONE commit (ledger imported +
     raw rows verbatim + parse job + stored accepted-receipt doc) → move
     ``ready`` → ``imported`` → POST accepted receipt.
3. ACK is sent only AFTER the durable commit (contract §7.3). Parser jobs
   are enqueued in the same commit; a parser failure can never un-ACK.

Exchange layout under ``settings.exchange_root`` (all file writes stay in
this subtree):

    staging/<package_id>/    downloading/validating (wiped on reuse)
    ready/<package_id>/      validated, awaiting import commit
    imported/<package_id>/   durable copy of an ACKed package
    quarantine/<package_id>/ rejected package + evidence
"""
from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from . import store, validate
from .client import IntakeClient, IntakeClientError

# package_id is used as a directory name — a non-uuid value is refused before
# it can become a path segment (contract §3.5 ids are canonical uuids).
_PACKAGE_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")

FETCH_ORDER = ("manifest", "records", "ready")
_FILE_NAMES = {"manifest": "manifest.json", "records": "records.jsonl",
               "ready": "READY.json"}
STATE_PENDING_LIST = "pending_list"
STATE_LAST_RUN_AT = "last_run_at"
STATE_LAST_ERROR = "last_error"
STATE_LAST_SEQUENCE = "last_sequence"


@dataclass
class SyncSettings:
    """Everything ``run_sync`` needs. ``client`` may be pre-built (tests inject
    a MockTransport client); otherwise one is created from module_url/token."""

    module_url: str = "http://127.0.0.1:8765"
    token: str | None = None
    consumer_id: str = ""
    exchange_root: Path | str = Path("data/zalo_exchange")
    timeout: float = 30.0
    page_limit: int = 200            # clamped to the contract cap of 100 on the wire
    client: IntakeClient | None = None

    @classmethod
    def from_env(cls, env: dict | None = None) -> "SyncSettings":
        env = os.environ if env is None else env
        return cls(
            module_url=env.get("ZALO_MODULE_URL") or "http://127.0.0.1:8765",
            token=env.get("ZALO_INTAKE_API_TOKEN") or None,
            consumer_id=env.get("ZALO_CONSUMER_ID") or "",
            exchange_root=Path(env.get("ZALO_EXCHANGE_ROOT") or "data/zalo_exchange"),
        )


@dataclass
class SyncReport:
    """Per-run counters; ``errors`` holds ``{package_id?, stage, message}``."""

    listed: int = 0
    imported: int = 0
    skipped: int = 0
    quarantined: int = 0
    receipts_sent: int = 0
    errors: list = field(default_factory=list)

    def add_error(self, stage: str, message: str, package_id: str | None = None):
        entry = {"stage": stage, "message": str(message)[:500]}
        if package_id:
            entry["package_id"] = package_id
        self.errors.append(entry)

    def as_dict(self) -> dict:
        return {
            "listed": self.listed,
            "imported": self.imported,
            "skipped": self.skipped,
            "quarantined": self.quarantined,
            "receipts_sent": self.receipts_sent,
            "errors": list(self.errors),
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.move(str(src), str(dst))


# ---------------------------------------------------------------------------
# feed paging
# ---------------------------------------------------------------------------


def _collect_pending(client: IntakeClient, db: Session,
                     settings: SyncSettings, report: SyncReport) -> list:
    """Drain the pending feed; persist the accumulated list before each
    page turn so a mid-paging crash replays cleanly (contract §7.2)."""
    pending: list = []
    seen: set = set()
    after, until = 0, None
    while True:
        page = client.list_packages(after_sequence=after,
                                    until_sequence=until, limit=settings.page_limit)
        until = page.get("until_sequence", until)
        for entry in page.get("packages") or []:
            pid = entry.get("package_id") if isinstance(entry, dict) else None
            if pid in seen:
                continue
            seen.add(pid)
            pending.append(entry)
        store.set_state(db, STATE_PENDING_LIST,
                        json.dumps(pending, ensure_ascii=False))
        db.commit()
        if not page.get("has_more"):
            return pending
        next_after = page.get("next_after", after)
        if not isinstance(next_after, int) or next_after <= after:
            # Producer bug: has_more without cursor progress — stop instead of
            # paging forever; unclaimed packages retry next sync.
            report.add_error(
                "feed", f"pagination stalled at after={after} "
                "(has_more without next_after progress)")
            return pending
        after = next_after


# ---------------------------------------------------------------------------
# receipt send + replay
# ---------------------------------------------------------------------------


def _send_stored_receipt(db: Session, client: IntakeClient,
                         ledger_row, report: SyncReport) -> None:
    """(Re-)POST the persisted receipt document for a ledgered package.

    The document is replayed byte-identically: receipt_id + body are the
    producer's idempotency pair, so re-sending after a lost response is safe.
    """
    doc = store.load_receipt_doc(db, ledger_row.package_id)
    if doc is None:
        report.add_error(
            "receipt",
            "ledger row has no stored receipt document; cannot replay "
            f"(decision={ledger_row.decision})",
            ledger_row.package_id)
        return
    try:
        client.send_receipt(doc)
    except IntakeClientError as e:
        report.add_error("receipt", f"receipt send failed: {e.code} {e.message}",
                         ledger_row.package_id)
        # A 4xx error envelope is a definitive upstream answer (producer
        # decisions are immutable — replaying the identical doc can never
        # succeed); mark the ledger sent so we do not retry forever.
        # Transport/5xx failures stay unmarked and retry next sync.
        if e.status is not None and 400 <= e.status < 500:
            store.mark_receipt(db, ledger_row.package_id, doc.get("status"))
            db.commit()
        return
    store.mark_receipt(db, ledger_row.package_id, doc.get("status"))
    db.commit()
    report.receipts_sent += 1


# ---------------------------------------------------------------------------
# per-package pipeline
# ---------------------------------------------------------------------------


def _download(client: IntakeClient, package_id: str, staging: Path) -> bool:
    """Fetch the three package files. Returns False when an endpoint answered
    404 (file absent → validation will report file_missing). Transport-level
    failures raise IntakeClientError to the caller."""
    ok = True
    for logical in FETCH_ORDER:
        try:
            data = client.fetch_bytes(package_id, logical)
        except IntakeClientError as e:
            if e.status == 404:
                ok = False
                continue
            raise
        (staging / _FILE_NAMES[logical]).write_bytes(data)
    return ok


def _record_count_for_receipt(vrep: validate.PackageReport) -> int:
    if isinstance(vrep.manifest_raw, dict) \
            and isinstance(vrep.manifest_raw.get("record_count"), int):
        return vrep.manifest_raw["record_count"]
    if vrep.records is not None:
        return len(vrep.records)
    return 0


def _build_receipt(ledger_row, *, status: str, error: dict | None = None) -> dict:
    doc = {
        "schema_version": "intake.receipt.v1",
        "receipt_id": ledger_row.receipt_id,
        "package_id": ledger_row.package_id,
        "consumer_id": ledger_row.consumer_id,
        "status": status,
        "received_at": _now().isoformat(),
        "manifest_sha256": ledger_row.manifest_sha256,
        "record_count": ledger_row.record_count,
    }
    if error is not None:
        doc["error"] = {"code": str(error.get("code") or "schema_invalid")[:64],
                        "message": str(error.get("message") or "")[:500]}
    return doc


def _quarantine(db: Session, client: IntakeClient, settings: SyncSettings,
                root: Path, staging: Path, package_id: str, sequence: int,
                vrep: validate.PackageReport, report: SyncReport) -> None:
    _move(staging, root / "quarantine" / package_id)
    first_code, first_detail = vrep.errors[0]
    reason = "; ".join(f"{code}: {detail}" for code, detail in vrep.errors[:8])
    ledger_row = store.add_ledger_row(
        db, package_id=package_id, consumer_id=settings.consumer_id,
        sequence=sequence, manifest_sha256=vrep.manifest_sha256 or "",
        record_count=_record_count_for_receipt(vrep),
        decision=store.DECISION_QUARANTINED,
        sealed_at=store._parse_iso((vrep.ready or {}).get("sealed_at")),
        quarantine_reason=reason[:1500])
    receipt = _build_receipt(
        ledger_row, status=store.RECEIPT_REJECTED,
        error={"code": first_code, "message": first_detail})
    store.store_receipt_doc(db, package_id, receipt)
    db.commit()  # durable decision BEFORE the receipt is sent
    _send_stored_receipt(db, client, ledger_row, report)
    report.quarantined += 1


def _import(db: Session, client: IntakeClient, settings: SyncSettings,
            root: Path, staging: Path, vrep: validate.PackageReport,
            report: SyncReport) -> None:
    manifest = vrep.manifest
    package_id = manifest["package_id"]
    ready_dir = root / "ready" / package_id
    _move(staging, ready_dir)

    ledger_row = store.add_ledger_row(
        db, package_id=package_id, consumer_id=settings.consumer_id,
        sequence=manifest["sequence"], manifest_sha256=vrep.manifest_sha256,
        record_count=manifest["record_count"],
        decision=store.DECISION_IMPORTED,
        sealed_at=store._parse_iso(vrep.ready.get("sealed_at")))
    pairs = list(zip(vrep.records or [], vrep.record_lines or []))
    errors, to_insert = store.check_record_conflicts(db, pairs)
    if errors:
        # Cross-record rule failure (revision chain / conflicts): treat like a
        # validation failure — undo the staged import, quarantine instead.
        db.rollback()
        for code, detail in errors:
            vrep.errors.append((code, detail))
        _move(ready_dir, root / "staging" / package_id)
        _quarantine(db, client, settings, root,
                    root / "staging" / package_id, package_id,
                    manifest["sequence"], vrep, report)
        return
    store.insert_raw_records(
        db, to_insert, package_id=package_id,
        package_sequence=manifest["sequence"])
    store.enqueue_parse_job(db, package_id)
    receipt = _build_receipt(ledger_row, status=store.RECEIPT_ACCEPTED)
    store.store_receipt_doc(db, package_id, receipt)
    db.commit()  # ledger + raw rows + parse job + receipt doc — ONE commit
    _move(ready_dir, root / "imported" / package_id)
    _send_stored_receipt(db, client, ledger_row, report)
    report.imported += 1


def _sync_one(db: Session, client: IntakeClient, settings: SyncSettings,
              root: Path, entry: dict, report: SyncReport) -> None:
    package_id = entry.get("package_id")
    sequence = entry.get("sequence")
    feed_hash = entry.get("manifest_sha256")

    if not isinstance(package_id, str) or not _PACKAGE_ID_RE.match(package_id):
        report.add_error("feed", f"invalid package_id in feed: {package_id!r}")
        return

    ledger_row = store.ledger_get(db, package_id)
    if ledger_row is not None:
        if feed_hash and ledger_row.manifest_sha256 != feed_hash:
            report.add_error(
                "feed",
                f"package_conflict: ledgered package_id re-listed under a "
                f"different manifest_sha256 ({ledger_row.manifest_sha256} "
                f"!= {feed_hash}) — decision stands, not re-imported",
                package_id)
        # Lost-ACK replay: a decision is durable; re-send its stored receipt
        # only when the previous POST was never confirmed.
        if ledger_row.receipt_status not in (store.RECEIPT_ACCEPTED,
                                             store.RECEIPT_REJECTED):
            _send_stored_receipt(db, client, ledger_row, report)
        report.skipped += 1
        return

    last_imported = store.last_imported_sequence(db)
    if isinstance(sequence, int) and sequence <= last_imported:
        # Out-of-order re-publish below the cursor — idempotent skip, not a
        # quarantine (the feed is allowed to show already-covered sequences).
        # Surface it: a *new* package_id reusing an old sequence is a producer
        # sequencing bug (contract `sequence_invalid`), worth a diagnostic.
        report.add_error(
            "feed",
            f"sequence_invalid: sequence {sequence} <= last_imported "
            f"{last_imported} — skipped",
            package_id)
        report.skipped += 1
        return

    staging = root / "staging" / package_id
    _reset_dir(staging)
    try:
        _download(client, package_id, staging)
    except IntakeClientError as e:
        report.add_error("fetch", f"download failed: {e.code} {e.message}",
                         package_id)
        return
    except OSError as e:
        report.add_error("fetch", f"staging write failed: {e}", package_id)
        return

    vrep = validate.validate_package(staging, consumer_id=settings.consumer_id)

    manifest = vrep.manifest_raw or {}
    if manifest and manifest.get("package_id") != package_id:
        vrep.errors.append(
            ("package_conflict",
             f"manifest package_id {manifest.get('package_id')} != feed "
             f"package_id {package_id}"))
    if vrep.manifest_sha256 is not None and feed_hash \
            and vrep.manifest_sha256 != feed_hash:
        vrep.errors.append(
            ("manifest_hash_mismatch",
             "manifest bytes differ from the feed-declared manifest_sha256"))

    if vrep.errors:
        seq = sequence if isinstance(sequence, int) else \
            (manifest.get("sequence") if isinstance(manifest.get("sequence"), int) else 0)
        _quarantine(db, client, settings, root, staging, package_id,
                    seq, vrep, report)
        return

    _import(db, client, settings, root, staging, vrep, report)


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------


def run_sync(db: Session, settings: SyncSettings) -> SyncReport:
    """One sync pass over the module's pending feed. Crash-safe at every
    boundary: staging/ready are rebuilt, the ledger is the durable state."""
    report = SyncReport()
    if not settings.consumer_id:
        # consumer_id rong -> moi manifest deu consumer_mismatch -> quarantine
        # hang loat. Fail fast thay vi lam ban ledger.
        report.add_error(
            "config",
            "consumer_id chua cau hinh (ZALO_CONSUMER_ID) — bo qua luot sync")
        return report
    root = Path(settings.exchange_root)
    for name in ("staging", "ready", "imported", "quarantine"):
        (root / name).mkdir(parents=True, exist_ok=True)

    client = settings.client or IntakeClient(
        settings.module_url, token=settings.token, timeout=settings.timeout)
    own_client = settings.client is None
    try:
        try:
            pending = _collect_pending(client, db, settings, report)
        except IntakeClientError as e:
            report.add_error("feed", f"pending feed unavailable: {e.code} {e.message}")
            pending = []
        report.listed = len(pending)

        def _seq(e):
            s = e.get("sequence")
            return s if isinstance(s, int) and not isinstance(s, bool) else 1 << 60

        for entry in sorted(pending, key=_seq):
            try:
                _sync_one(db, client, settings, root, entry, report)
            except Exception as e:  # per-package isolation: log, roll back, continue
                db.rollback()
                report.add_error(
                    "package", f"unhandled error: {type(e).__name__}: {e}",
                    entry.get("package_id") if isinstance(entry, dict) else None)

        store.set_state(db, STATE_LAST_RUN_AT, _now().isoformat())
        store.set_state(db, STATE_LAST_SEQUENCE,
                        str(store.last_imported_sequence(db)))
        store.set_state(db, STATE_PENDING_LIST, "[]")
        store.set_state(db, STATE_LAST_ERROR,
                        report.errors[-1]["message"] if report.errors else "")
        db.commit()
    finally:
        if own_client:
            client.close()
    return report
