"""Lõi luật chung — một đường luật duy nhất cho Word.

Module luật: `contract_extract` (nguồn: `engine/contract_extract.py`).
Consumer gọi qua adapter của mình (Upload: `upload_lab/extraction_adapter.py`;
Document Intake: `notary_v2/services/document_intake/adapters/docx.py`).
Không còn pipeline profile/zoning riêng — mọi luật nằm trong `contract_extract`.
"""

from .contract_extract import ENGINE_ID, ENGINE_VERSION, extract_text

__all__ = ["ENGINE_ID", "ENGINE_VERSION", "extract_text"]
