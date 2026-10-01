# Regex Workbench (dev tool)

Công cụ độc lập cho dev: dán một văn bản công chứng hoàn chỉnh, chạy profile
regex, xem cấu trúc vùng và các trường trích xuất kèm provenance. UI tham
khảo Regex101. Không phụ thuộc `upload_lab`, `shell`, `notary_v2`; chỉ dùng
thư viện chuẩn Python.

## Chạy

```bat
python tools\regex_workbench\serve.py
```

Mở `http://127.0.0.1:8765/` (server tự mở trình duyệt; `--no-browser` để tắt,
`--port` để đổi cổng). Ba cột: văn bản nguồn + highlight | rule editor |
bảng trường + đương sự + JSON. Nút Run / Export / Import / Reset profile.

## Kiến trúc

1. **Zoning first** (`engine/zoner.py`): nhận loại văn bản từ tiêu đề
   (và câu mở đầu), rồi cắt tuần tự `header -> parties -> asset -> clauses
   -> notary`. Thân văn bản không tự quyết định loại.
2. **Field extraction second** (`engine/extractor.py`): regex chỉ chạy trong
   vùng của nó — trường Người trong `parties`, trường Thửa đất/Serial trong
   `asset`, v.v.
3. **Provenance**: mọi zone/field/person trả về `span` `[start, end]` trên
   văn bản gốc + `raw_snippet` + `rule_id`.
4. **Honest states**: `matched` | `ambiguous` (nhiều nghiệm, không tự chọn)
   | `warning_nonstandard` (giữ raw + cảnh báo) | `missing` | `error`
   (regex hỏng/timeout).

## Quy ước pattern

Pattern trong profile viết trên **văn bản đã fold**: chữ thường, bỏ dấu
(`hợp đồng` -> `hop dong`), `đ` -> `d`. Engine match trên bản fold rồi ánh
xạ span về văn bản gốc qua index map — `value`/`raw_snippet` giữ nguyên dấu.
Validator trong `fields[].validators` chạy trên **raw** (giữ hoa/thường,
dùng cho kiểm tra serial `[A-Z]{2}`).

## Profile `transfer.json`

- `title`: `scan_lines`, `candidate_prefixes`, `continuation_prefixes`,
  `stop_prefixes`, `kind_rules` (`priority` cao thắng — `dinh chinh` = 100
  để văn bản đính chính không bị coi là hợp đồng chuyển nhượng chính).
- `zones`: danh sách có thứ tự; `implicit_start` cho `header`; mỗi zone có
  `start_markers`; zone cuối có thể có `end_markers`.
- `parties`: `side_markers` (side + role + pattern, vd `dong su dung` gắn
  side A — fix bug bỏ sót người đồng sử dụng), `person_delimiter`,
  `person_fields` (mỗi người một chunk riêng — `ho_ten` dừng trước `sinh`
  nên không lẫn năm sinh vào tên).
- `fields`: `rule_id`, `name`, `zone` (`any` = toàn văn bản), `group`,
  `expect` (`one`/`many`), `value_template` (`{1}/{2}/{3}`), `validators`.
- `regex_timeout_ms`: ngưỡng báo lỗi khi regex chạy quá lâu.

## Test

```bat
python -m pytest tools\regex_workbench\tests -q
```

Fixtures trong `tests/fixtures/` là dữ liệu giả lập (không PII khách thật),
mô phỏng 4 ca lỗi baseline: Đồng sử dụng, Sinh năm lẫn họ tên, Đính chính,
Serial một chữ cái.

## Giới hạn đã biết

- Người không có danh xưng Ông/Bà/Cụ đứng sau nhãn (vd `Đồng sử dụng:
  Nguyễn Thị X`) cần thêm delimiter trong profile.
- Timeout regex là best-effort: engine báo `error` cho rule đó nhưng không
  hủy được thread match của `re`.
