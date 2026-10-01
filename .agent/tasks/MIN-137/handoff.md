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
- Timeout regex = engine `regex` (requirements.txt), `timeout=` trên mọi
  match của profile — TimeoutError ngay trong match, ngắt thật. Đã loại bỏ
  ThreadPoolExecutor (không hủy được match `re` đang chạy). Lint
  `_NESTED_QUANTIFIER` giữ vai trò cảnh báo sớm, không phải cơ chế chặn.
- Lỗi timeout truyền đầy đủ: field → `error` kèm rule_id; side_markers/
  person_delimiter → `parties.state=error`; person_fields → field `error`;
  validators timeout → `error` + warning; zone/kind marker → `errors[]`.
- Provenance trỏ về raw input: `normalize_with_index_map` (char_ranges) +
  `fold_with_index_map` (fold_map) + `make_span_mapper` hợp map folded→raw;
  end span mở rộng phủ combining mark — input NFD/CRLF/ngoài BMP đều đúng.
- UI `app.js` slice highlight theo code point (`Array.from`) vì span là
  code-point index — JS UTF-16 slicing sẽ lệch với ký tự ngoài BMP.

## Kiểm chứng

`python -m pytest tools/regex_workbench/tests -q` → 20 passed
(3 timeout qua subprocess probe `tests/_timeout_probe.py` có giới hạn ngoài
tiến trình; 3 test NFD/CRLF/non-BMP; 14 test cũ giữ nguyên).

Baseline 20 thư mục (results.json worktree notaryoffice-bmad-brainstorm):
94 file, 86 đọc được, 8 bỏ qua (word lock) — khớp baseline. Engine: doc_kind
transfer=13, generic=47, unknown=18, asset_commitment=6, correction=2;
errors=0; runtime avg 5.6ms/file. Chi tiết: `baseline_eval.py` (chỉ tổng hợp).

## Mở

- Người không danh xưng sau nhãn `Đồng sử dụng:` cần delimiter riêng.
- Phần lớn baseline là giấy ủy quyền/loại khác nên coverage trường chuyển
  nhượng thấp là đúng kỳ vọng; ground truth chưa có nhãn đúng tay — đối chiếu
  mới ở mức phân bố, chưa phải độ chính xác tuyệt đối.
