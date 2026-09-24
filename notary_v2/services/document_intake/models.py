"""Contract-shaped models for notary.case-drafting.v1 document intake.

Wire-level shape is fixed by contracts/notary-case-drafting/intake.schema.json:
- suggestions carry raw + normalized values with observation metadata;
  `confirmed` does not exist here — intake never asserts truth.
- per-source failures land in errors[] and never destroy other sources.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

SCHEMA_VERSION = "notary.case-drafting.v1"

SOURCE_KINDS = ("image", "pdf", "docx", "xlsx", "text")
FILE_SOURCE_KINDS = ("image", "pdf", "docx", "xlsx")
OBSERVATION_STATES = ("observed", "normalized", "inferred")
SUGGESTION_TARGETS = ("person", "asset")

# Server-side limits (contract §5.2) — enforced regardless of client claims.
MAX_SOURCES = 8
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_TEXT_CHARS = 100_000


class IntakeError(Exception):
    """Job-level intake violation → mapped to CommandError(code) by the sidecar."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class SourceFailed(Exception):
    """Per-source failure → errors[] entry; other sources keep processing."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class IntakeCancelled(Exception):
    """Wraps the caller's cancellation exception so it is never swallowed by
    per-source error handling — service re-raises `.original` unchanged."""

    def __init__(self, original: Optional[BaseException] = None):
        super().__init__(str(original) if original is not None else "cancelled")
        self.original = original


@dataclass
class SourceSpec:
    """Validated internal view of one intake source."""

    source_id: str
    kind: str
    text: Optional[str] = None
    path: Optional[str] = None
    filename: str = ""
    declared_size: Optional[int] = None


@dataclass
class AdapterContext:
    """Runtime shared by all adapters for one intake call."""

    api_key: str
    model: str
    client: Any  # httpx.AsyncClient
    semaphore: Any  # asyncio.Semaphore
    ocr_call: Optional[Callable] = None  # injectable OCR (tests)
    check_cancel: Optional[Callable[[], None]] = None
    read_file: Optional[Callable[[SourceSpec], bytes]] = None


def make_suggestion(
    *,
    source_id: str,
    target: str,
    fields: dict[str, dict],
    warnings: list[dict],
) -> dict:
    """Build one contract-shaped suggestion dict."""
    if target not in SUGGESTION_TARGETS:
        raise ValueError(f"unsupported suggestion target: {target}")
    return {
        "suggestion_id": str(uuid.uuid4()),
        "source_id": source_id,
        "target": target,
        "fields": fields,
        "warnings": warnings,
    }


def make_source_error(*, source_id: str, code: str, message: str) -> dict:
    """Contract intake_error — chỉ {source_id, code, message}
    (additionalProperties:false — filename đi trong message nếu cần)."""
    return {
        "source_id": source_id,
        "code": code,
        "message": message,
    }


@dataclass
class IntakeOutcome:
    """Aggregate result of one intake_analyze call.

    status theo contract §5.3: succeeded | partial (intake không có
    `failed`/`intake_batch_failed` — mọi nguồn lỗi vẫn là partial với
    breakdown.failed đầy đủ)."""

    status: str  # "succeeded" | "partial"
    suggestions: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def result_data(self) -> dict:
        data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "suggestions": self.suggestions,
            "errors": self.errors,
        }
        if self.failed:
            data["breakdown"] = {
                "succeeded": list(self.succeeded),
                "failed": list(self.failed),
            }
        return data
