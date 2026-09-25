"""MIN-97 implements the OCR request ledger (accept pipeline §9.3). Boundary only."""

from datetime import datetime


def submit_ocr_request(
    request_id: str,
    consumer_id: str,
    logical_id: str,
    observed_revision: int,
    variant: str,
    preset: str | None,
    reason_code: str,
    requested_at: datetime,
) -> dict:
    """Signature per plan §3.1 — full quota/dedupe pipeline lands in MIN-97."""
    raise NotImplementedError("MIN-97")
