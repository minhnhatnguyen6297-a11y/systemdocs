"""Contract boundary types — implementation plan §3.1 (verbatim declarations).

Only the module-side interface is declared here. The notary-side functions
(parse_records, assemble_result, replay_raw, propose_ocr_request,
import_package, preview_apply, stage_review, commit_draft_input) belong to
notary_v2 Document Intake and are NOT declared in this module — see
systemdocs docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md §3.1.

These are interface declarations for later tasks (MIN-94/95/97); nothing is
implemented here.
"""

from datetime import datetime
from typing import Any, TypedDict

JsonObject = dict[str, Any]
CaptureEvent = JsonObject      # journal schema nội bộ, có captured_at + source key
RawRecord = JsonObject         # validate bằng intake.raw-record.v1
RawPackage = JsonObject        # manifest và bytes records/READY đã kiểm
ParsedDocument = JsonObject    # loại giấy + field candidates + source_refs, local
ProcessedResult = JsonObject   # người/tài sản/nhóm + revision, chỉ local


class ImportReceipt(TypedDict):
    package_id: str
    manifest_sha256: str
    status: str
    imported_at: str


# Module: adapter Qwen trả records cho từng trang, kể cả status lỗi.
def capture_event(event: CaptureEvent) -> str:
    ...  # ID bền vững; replay trả cùng ID


def ocr_attachment(attachment_id: str) -> list[RawRecord]:
    ...


def submit_ocr_request(
    request_id: str,
    consumer_id: str,
    logical_id: str,
    observed_revision: int,
    variant: str,
    preset: str | None,
    reason_code: str,
    requested_at: datetime,
) -> JsonObject:
    ...


def run_ocr_variant(
    logical_id: str, variant: str, preset: str | None
) -> RawRecord:
    ...  # nội bộ bot, MIN-97 chỉ gọi từ job đã duyệt


def publish_package(records: list[RawRecord], consumer_id: str) -> str:
    ...  # delegates to delivery.package.build_package


def expire_media(now: datetime) -> int:
    ...  # số tệp đã xóa, không xóa raw
