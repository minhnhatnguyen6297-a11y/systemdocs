# MIN-137 — Regex Workbench (handoff)

## Nguồn

- Linear MIN-137 / issue NAIA-3 (Multica). Kiến trúc do Owner duyệt, Mika
  chốt phạm vi trong comment 01a0f4f4 (2026-10-01).

## Đã làm

- `tools/regex_workbench/engine/`: `textnorm` (fold dấu + index map),
  `zoner` (title -> kind; cắt vùng header/parties/asset/clauses/notary),
  `extractor` (field rules theo zone, side markers -> blocks -> persons,
  validators), `runner` (`run(text, profile)`, `lint_profile`).
- `engine/profiles/transfer.json` v1.0.0 — xử lý 4 ca lỗi baseline:
  đồng sử dụng, sinh năm lẫn họ tên, đính chính ≠ hợp đồng chính, serial
  một chữ cái giữ raw + `warning_nonstandard`.
- `ui/` + `serve.py`: dev server stdlib (8765), UI 3 cột kiểu Regex101,
  Run/Export/Import/Reset profile, highlight zone + trạng thái trường.
- `tests/` — 6 fixture giả lập (không PII), 14 test pytest/unittest.

## Quyết định

- Pattern profile viết dạng folded; validator chạy trên raw (giữ hoa) —
  cần thiết để kiểm tra serial `[A-Z]{2}`.
- Timeout regex = ThreadPoolExecutor + `result(timeout)`; lỗi rõ ràng nhưng
  thread `re` không hủy được — kèm lint tĩnh nested-quantifier.

## Kiểm chứng

`python -m pytest tools/regex_workbench/tests -q` → 14 passed.

## Mở

- Người không danh xưng sau nhãn `Đồng sử dụng:` cần delimiter riêng.
- Cần chạy profile trên 20 thư mục thật (baseline artifacts nằm ở worktree
  `notaryoffice-bmad-brainstorm`, chưa có trong nhánh này).
