"""Multi-source document intake service (notary.case-drafting.v1, MIN-108).

Năm source kinds (image/pdf/docx/xlsx/text) → contract suggestions với
provenance + observation metadata. Kết quả là *gợi ý* — user commit sau qua
Stage workflow; intake không bao giờ coi OCR là confirmed truth.

Shared với:
- Electron sidecar (`notary.intake_analyze`)
- OCR pipeline (services/document_intake/ocr_pipeline.py — lõi chung với
  routers/ocr_ai.py)
- Excel parser (excel_parse.py — lõi chung với routers/customers.py)
"""

from .models import (
    FILE_SOURCE_KINDS,
    MAX_FILE_BYTES,
    MAX_PDF_PAGES,
    MAX_SOURCES,
    MAX_TEXT_CHARS,
    OBSERVATION_STATES,
    SCHEMA_VERSION,
    SOURCE_KINDS,
    SUGGESTION_TARGETS,
    AdapterContext,
    IntakeCancelled,
    IntakeError,
    IntakeOutcome,
    SourceFailed,
    SourceSpec,
)
from .service import analyze, analyze_async

__all__ = [
    "AdapterContext",
    "FILE_SOURCE_KINDS",
    "IntakeCancelled",
    "IntakeError",
    "IntakeOutcome",
    "MAX_FILE_BYTES",
    "MAX_PDF_PAGES",
    "MAX_SOURCES",
    "MAX_TEXT_CHARS",
    "OBSERVATION_STATES",
    "SCHEMA_VERSION",
    "SOURCE_KINDS",
    "SUGGESTION_TARGETS",
    "SourceFailed",
    "SourceSpec",
    "analyze",
    "analyze_async",
]
