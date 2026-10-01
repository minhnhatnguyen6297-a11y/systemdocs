"""Chuẩn hóa văn bản và fold dấu tiếng Việt với index map.

Engine match regex trên bản đã fold (lowercase, bỏ dấu, đ -> d) để profile
chỉ cần viết pattern một lần cho cả văn bản có dấu lẫn không dấu.

Provenance hai tầng, span cuối cùng trỏ về ĐÚNG văn bản người dùng nhập:

  raw input --normalize_with_index_map--> s1 --fold_with_index_map--> folded
           (char_ranges: s1 char -> raw range)    (fold_map: folded char -> s1)

`make_span_mapper` hợp hai tầng thành map folded-span -> raw-span. Vì span
trỏ về raw input, input NFD hay chứa ký tự ngoài BMP đều cắt đúng đoạn nguồn
(với NFD, end span tự mở rộng phủ hết combining mark của cluster cuối).
"""

from __future__ import annotations

import unicodedata

REPLACEMENTS = {
    "\r": "\n",
    "\x0b": "\n",
    "\x0c": "\n",
    "\xa0": " ",
    "\t": " ",
}


def normalize_with_index_map(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Chuẩn hóa khoảng trắng/xuống dòng, giữ map về văn bản gốc.

    Trả về (normalized, char_ranges): normalized[i] chiếm raw
    [char_ranges[i][0], char_ranges[i][1]). Chỉ `\\r\\n` co 2 ký tự thành 1;
    các thay thế còn lại 1->1. Không NFC tổng thể — bước fold phía sau đã
    xử lý NFD per-char nên folded text đồng nhất với mọi form Unicode, còn
    span giữ được offset của input thật.
    """
    raw = str(text or "")
    chars: list[str] = []
    char_ranges: list[tuple[int, int]] = []
    i, n = 0, len(raw)
    while i < n:
        ch = raw[i]
        if ch == "\r" and i + 1 < n and raw[i + 1] == "\n":
            chars.append("\n")
            char_ranges.append((i, i + 2))
            i += 2
            continue
        repl = REPLACEMENTS.get(ch)
        chars.append(repl if repl is not None else ch)
        char_ranges.append((i, i + 1))
        i += 1
    return "".join(chars), char_ranges


def normalize_text(text: str) -> str:
    """Dạng chuẩn hóa chỉ có khoảng trắng (giữ nguyên form Unicode gốc)."""
    return normalize_with_index_map(text)[0]


def fold_with_index_map(text: str) -> tuple[str, list[int]]:
    """Fold văn bản: NFD, bỏ dấu (Mn), đ/Đ -> d, lowercase.

    Trả về (folded_text, fold_map) trong đó fold_map[i] là offset trong
    `text` của ký tự folded thứ i.
    """
    source = str(text or "")
    folded_chars: list[str] = []
    fold_map: list[int] = []
    for idx, char in enumerate(source):
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.category(part) == "Mn":
                continue
            if part in ("đ", "Đ"):
                part = "d"
            folded_chars.append(part.lower())
            fold_map.append(idx)
    return "".join(folded_chars), fold_map


def make_span_mapper(fold_map: list[int], char_ranges: list[tuple[int, int]]):
    """Dựng hàm span_of(fold_start, fold_end) -> (raw_start, raw_end) | None.

    End span mở rộng tới đầu của ký tự folded kế tiếp trong s1: như vậy các
    combining mark bị fold bỏ qua (không có entry trong fold_map) vẫn được
    tính vào phần cuối của span — input NFD cho raw_snippet đủ cụm ký tự.
    """
    s1_len = len(char_ranges)

    def span_of(fold_start: int, fold_end: int) -> tuple[int, int] | None:
        if fold_start < 0 or fold_end <= fold_start or fold_end > len(fold_map):
            return None
        s1_start = fold_map[fold_start]
        s1_end = fold_map[fold_end] if fold_end < len(fold_map) else s1_len
        return char_ranges[s1_start][0], char_ranges[s1_end - 1][1]

    return span_of


def map_span(index_map: list[int], fold_start: int, fold_end: int) -> tuple[int, int] | None:
    """Ánh xạ span trong văn bản folded về span trong văn bản gốc.

    Giữ lại cho tương thích; map một tầng (folded -> input của fold) và không
    mở rộng qua combining mark — code mới nên dùng `make_span_mapper`.
    """
    if not index_map or fold_start < 0 or fold_end <= fold_start or fold_end > len(index_map):
        return None
    return index_map[fold_start], index_map[fold_end - 1] + 1
