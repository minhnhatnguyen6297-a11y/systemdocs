# MIN-137 — Regex Workbench (handoff)

## Nguồn

- Linear MIN-137 / issue NAIA-3 (Multica). Kiến trúc do Owner duyệt, Mika
  chốt phạm vi trong comment 01a0f4f4 (2026-10-01).

## Đã làm

- `tools/regex_workbench/engine/`: `textnorm` (fold dấu + index map),
  `zoner` (title -> kind; cắt vùng header/parties/asset/clauses/notary),
  `extractor` (field rules theo zone, side markers -> blocks -> persons,
  validators, ambiguous cho nhiều kết quả trong một người), `runner`
  (`run(text, profile)`, `validate_profile`, `lint_profile`).
- `engine/profiles/transfer.json` v1.0.0 — xử lý 4 ca lỗi baseline:
  đồng sử dụng (kể cả nhãn cùng dòng và người không danh xưng), sinh năm
  lẫn họ tên, đính chính ≠ hợp đồng chính, serial một chữ cái giữ raw +
  `warning_nonstandard`.
- `ui/` + `serve.py`: dev server stdlib (8765), UI 3 cột kiểu Regex101,
  Run/Export/Import/Reset profile, highlight zone + trạng thái trường;
  validate shape profile -> 400 có `problems`, engine lỗi -> 500 JSON.
- `tests/` — 6 fixture giả lập (không PII), 37 test: engine/unit +
  timeout qua subprocess probe + HTTP thật (test_serve) + UI DOM stub
  Node (test_ui_dom).

## Quyết định

- Pattern profile viết dạng folded; validator chạy trên raw (giữ hoa) —
  cần thiết để kiểm tra serial `[A-Z]{2}`.
- Timeout regex = engine `regex` (requirements.txt), `timeout=` trên mọi
  match của profile — TimeoutError ngay trong match, ngắt thật. Đã loại bỏ
  ThreadPoolExecutor (không hủy được match `re` đang chạy). Lint
  `_NESTED_QUANTIFIER` giữ vai trò cảnh báo sớm, không phải cơ chế chặn.
- Lỗi timeout/cú pháp truyền đầy đủ: field → `error` kèm rule_id;
  side_markers/person_delimiter → `parties.state=error`; person_fields →
  field `error`; validators → `error` + warning + `errors[]`; zone marker →
  zone `error` + `errors[]`; kind_rule → `title.state=error` +
  `doc_kind=unknown` (rule ưu tiên cao không đánh giá được → kết quả kind
  không đáng tin).
- `person_delimiter` 2 nhánh (sau review f48a762): danh xưng sau đầu
  dòng/`;`/`,`/`:` (cho phép `Đồng sử dụng: Bà:` cùng dòng) + nhánh người
  không danh xưng có bằng chứng (`sinh`+số hoặc nhãn CCCD) ở đầu dòng hoặc
  sau `;`. `ho_ten` nhận danh xưng optional.
- `person_fields` khớp nhiều lần trong chunk: >1 kết quả → `ambiguous` +
  `candidates` (hai CCCD trong một người không tự chọn số đầu).
- `validate_profile` (runner.py) kiểm tra shape trước lint/run — contract
  chung runner+HTTP: serve trả `400` kèm `problems[]` khi shape sai
  (`fields: null`, `zones` string, ...); engine ném lỗi bất ngờ → `500`
  JSON. Engine `or []`/`or {}` tolerant khi gọi trực tiếp.
- UI `app.js`: `esc()` escape cả `'`/`"` cho attribute; `runEngine` chụp
  snapshot source lúc gửi — sửa source giữa chừng → bỏ qua response cũ;
  import JSON lỗi → báo trong `profile-status` (không reject ngầm).
- Provenance trỏ về raw input: `normalize_with_index_map` (char_ranges) +
  `fold_with_index_map` (fold_map) + `make_span_mapper` hợp map folded→raw;
  end span mở rộng phủ combining mark — input NFD/CRLF/ngoài BMP đều đúng.
- UI `app.js` slice highlight theo code point (`Array.from`) vì span là
  code-point index — JS UTF-16 slicing sẽ lệch với ký tự ngoài BMP.

## Kiểm chứng

`python -m pytest tools/regex_workbench/tests -q` → 37 passed
(engine/fixture + 3 timeout qua subprocess probe `tests/_timeout_probe.py`
có giới hạn ngoài tiến trình + 3 test span NFD/CRLF/non-BMP +
`test_serve.py` HTTP thật 7 ca + `test_ui_dom.py` chạy app.js thật qua DOM
stub Node — 10 check import/export/highlight/esc/stale-guard; skip khi
thiếu node).

Baseline 20 thư mục (results.json worktree notaryoffice-bmad-brainstorm):
94 file, 86 đọc được, 8 bỏ qua (word lock) — khớp baseline. Engine:
doc_kind transfer=13, correction=2, asset_commitment=6, generic=47,
unknown=18; errors=0; persons/doc max=3 (không tách ảo trên dữ liệu thật);
runtime avg 5.4ms/file. Chi tiết: `baseline_eval.py` (chỉ tổng hợp).

## Mở

- Người không danh xưng chỉ tách được khi dòng tên đứng đầu dòng/sau `;`
  và có bằng chứng (`sinh`+số hoặc nhãn CCCD); chunk người không chứa
  trường nào vẫn chưa tách được.
- Phần lớn baseline là giấy ủy quyền/loại khác nên coverage trường chuyển
  nhượng thấp là đúng kỳ vọng; ground truth chưa có nhãn đúng tay — đối
  chiếu mới ở mức phân bố, chưa phải độ chính xác tuyệt đối.
