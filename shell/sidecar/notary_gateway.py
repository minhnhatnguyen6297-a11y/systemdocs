"""Gateway chon backend cho command notary.* case-drafting (MIN-106) +
notary.case_list dung cho tab Tong quan ho so (MIN-112 — mock parity).

Contract SOT: contracts/notary-case-drafting.md (notary.case-drafting.v1).

Chon mock khi env G1_DEV_NOTARY_MOCK=1 VA sidecar KHONG packaged
(khong phai PyInstaller exe — sys.frozen). Mac dinh luon real.

Packaged + flag co mat -> bo qua flag va warning da redact (khong log gia
tri env, khong log path) — mock chi la cong cu dev cho frontend (MIN-111).

Real backend cua 7 command nay duoc them vao notary_adapter o MIN-107..110;
trong luc chua co, dispatch tra engine_not_installed (structured, khong
retry) — khong crash sidecar.
"""
import os
import sys

from errors import CommandError

MOCK_ENV = "G1_DEV_NOTARY_MOCK"

_warned_packaged = False


def _is_packaged():
    """Sidecar chay duoi PyInstaller exe = ban packaged cua Electron."""
    return bool(getattr(sys, "frozen", False))


def use_mock():
    """True khi dev bat mock: env=1 va khong packaged."""
    global _warned_packaged
    if os.environ.get(MOCK_ENV) != "1":
        return False
    if _is_packaged():
        if not _warned_packaged:
            _warned_packaged = True
            # redact: chi ten bien + quyet dinh, khong gia tri/path
            print(f"WARN: {MOCK_ENV} bi bo qua tren ban packaged "
                  "(backend real)", file=sys.stderr)
        return False
    return True


def _adapter():
    if use_mock():
        import notary_mock_adapter
        return notary_mock_adapter
    import notary_adapter
    return notary_adapter


def dispatch(fn_name, job, payload):
    """Route mot handler notary.* case-drafting sang backend da chon."""
    fn = getattr(_adapter(), fn_name, None)
    if fn is None:
        raise CommandError(
            "engine_not_installed",
            f"backend that chua ho tro notary.{fn_name} (MIN-107+); "
            "dev: dat G1_DEV_NOTARY_MOCK=1 de dung mock",
            retryable=False)
    return fn(job, payload)
