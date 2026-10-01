"""Chuẩn hóa văn bản và fold dấu tiếng Việt với index map.

Engine match regex trên bản đã fold (lowercase, bỏ dấu, đ -> d) để profile
chỉ cần viết pattern một lần cho cả văn bản có dấu lẫn không dấu.
Index map giữ ánh xạ từng ký tự folded -> offset ký tự gốc, nhờ đó mọi
span trả về luôn trỏ đúng vào văn bản nguồn (provenance).
"""

from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Đưa văn bản nguồn về dạng chuẩn trước khi xử lý."""
    normalized = str(text or "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\x0b", "\n").replace("\x0c", "\n")
    normalized = normalized.replace("\xa0", " ").replace("\t", " ")
    return unicodedata.normalize("NFC", normalized)


def fold_with_index_map(text: str) -> tuple[str, list[int]]:
    """Fold văn bản: NFD, bỏ dấu (Mn), đ/Đ -> d, lowercase.

    Trả về (folded_text, index_map) trong đó index_map[i] là offset trong
    văn bản gốc của ký tự folded thứ i.
    """
    source = str(text or "")
    folded_chars: list[str] = []
    index_map: list[int] = []
    for idx, char in enumerate(source):
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.category(part) == "Mn":
                continue
            if part in ("đ", "Đ"):
                part = "d"
            folded_chars.append(part.lower())
            index_map.append(idx)
    return "".join(folded_chars), index_map


def map_span(index_map: list[int], fold_start: int, fold_end: int) -> tuple[int, int] | None:
    """Ánh xạ span trong văn bản folded về span trong văn bản gốc."""
    if not index_map or fold_start < 0 or fold_end <= fold_start or fold_end > len(index_map):
        return None
    return index_map[fold_start], index_map[fold_end - 1] + 1
