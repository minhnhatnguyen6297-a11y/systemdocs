# Regex Workbench (dev tool)

Công cụ độc lập cho dev: dán một văn bản công chứng hoàn chỉnh, chạy profile
regex, xem cấu trúc vùng và các trường trích xuất kèm provenance. UI tham
khảo Regex101. Không phụ thuộc `upload_lab`, `shell`, `notary_v2`.

## Cài đặt

```bat
pip install -r tools\regex_workbench\requirements.txt
```

Engine match dùng module `regex` (thay `re`) vì nó hỗ trợ `timeout=` thật:
quá hạn raise `TimeoutError` ngay trong match. `re` + ThreadPoolExecutor
không ngắt được match đang chạy nên đã bị loại bỏ.

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
  - `person_delimiter` gồm 2 nhánh: (1) người có danh xưng Ông/Bà/Cụ đứng
    sau đầu dòng/`;`/`,`/`:` — `:` cho phép `Đồng sử dụng: Bà: ...` trên cùng
    dòng; (2) người KHÔNG danh xưng — dòng mới bắt đầu bằng tên (chữ cái
    đầu, không phải nhãn dữ liệu) rồi theo sau là bằng chứng người
    (`sinh` + số, hoặc nhãn căn cước/CCCD/CMND), chỉ ở đầu dòng hoặc sau
    `;`. Nhánh (2) giải quyết ca "bỏ danh xưng vẫn không bỏ người".
  - `person_fields` khớp NHIỀU lần trong chunk: >1 kết quả khác nhau
    (vd hai số CCCD trong một người) -> `ambiguous` kèm `candidates`,
    không tự chọn số đầu.
  - `ho_ten` có danh xưng optional để bóc tên trong chunk do nhánh (2) tạo.
- `fields`: `rule_id`, `name`, `zone` (`any` = toàn văn bản), `group`,
  `expect` (`one`/`many`), `value_template` (`{1}/{2}/{3}`), `validators`.
- `regex_timeout_ms`: ngưỡng báo lỗi khi regex chạy quá lâu — áp cho MỌI
  pattern trong profile (title `kind_rules`, zone `start_markers`/`end_markers`,
  `fields`, `side_markers`, `person_delimiter`, `person_fields`, `validators`).
  Quá hạn → `TimeoutError` trong engine → state `error` kèm `rule_id`, ghi
  vào `errors[]`; không nuốt lỗi thành `missing`.
- **Lỗi cấu hình báo rõ theo rule**: regex sai cú pháp trong `kind_rules`
  → `title.state=error` + `doc_kind=unknown` (rule ưu tiên cao không đánh
  giá được nên kết quả kind không đáng tin); sai trong zone marker → zone
  `error`; sai trong field/validator/side marker/person rule → field/
  parties `error` kèm `rule_id` trong `errors[]`.
- **Contract HTTP** (`serve.py`): `validate_profile` kiểm tra shape trước —
  sai kiểu (vd `fields: null`) → `400` + `problems[]`; body không phải JSON
  → `400`; engine ném lỗi bất ngờ → `500` JSON (request không rơi).

## Span & Unicode

Mọi `span`/`raw_snippet` trỏ vào **văn bản nguồn người dùng nhập** (raw),
không phải bản đã chuẩn hóa: pipeline giữ map 2 tầng raw→normalized→folded
(`textnorm.make_span_mapper`). Input NFD (combining mark) hay `\r\n` vẫn cắt
đúng đoạn gốc; span end tự phủ hết combining mark của cluster cuối.
Ký tự ngoài BMP = 1 code point trong span — UI tô highlight bằng slicing
theo code point (`Array.from`), không dùng offset UTF-16 của JS.

## Test

```bat
python -m pytest tools\regex_workbench\tests -q
```

Ba lớp test:

- `test_workbench.py` — engine + profile + fixtures giả lập; test timeout
  chạy qua process con (`tests/_timeout_probe.py`) có `subprocess timeout`
  cứng — suite không thể treo kể cả khi cơ chế ngắt hỏng.
- `test_serve.py` — server HTTP thật (`ThreadingHTTPServer` cổng ngẫu
  nhiên): contract 400 shape/JSON lỗi, 200 + result, 404.
- `test_ui_dom.py` + `tests/_ui_dom_probe.mjs` — chạy `ui/app.js` THẬT trong
  DOM giả lập bằng Node (không cần trình duyệt): escape attribute, highlight
  code-point sau emoji, bỏ qua response cũ khi sửa source giữa chừng, import
  lỗi/đúng, export, hiển thị `problems`. Skip khi máy không có Node.

Fixtures trong `tests/fixtures/` là dữ liệu giả lập (không PII khách thật),
mô phỏng 4 ca lỗi baseline: Đồng sử dụng, Sinh năm lẫn họ tên, Đính chính,
Serial một chữ cái.

## Giới hạn đã biết

- Người không danh xưng chỉ được tách khi dòng tên đứng đầu dòng/sau `;`
  và đi kèm bằng chứng (`sinh` + số hoặc nhãn căn cước/CCCD); người không
  danh xưng mà chunk cũng không có trường ngày sinh/CCCD vẫn chưa tách
  được — cần thêm quy tắc trong profile.
- Timeout của `regex` tính theo mỗi lần match-attempt; một rule sinh nhiều
  match nhỏ nhanh không bị chặn theo tổng thời gian rule.
