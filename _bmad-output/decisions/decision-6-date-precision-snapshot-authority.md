---
id: decision-6-date-precision-snapshot-authority
title: 'Độ đầy đủ ngày Người: snapshot hồ sơ là nguồn, không đổi schema'
date: '2026-10-16'
status: accepted
---

## Bối cảnh

Owner 15/10/2026 (`contracts/entities.md` §8.1, `specs/README.md` §6) chốt:
lưu/đọc lại và hiển thị phải phân biệt `2010` với ngày thật `01/01/2010`;
ngày quy ước chỉ phục vụ tính toán nội bộ; “cách giữ dữ liệu nhập/độ đầy đủ
trong lưu trữ phải kiểm riêng khi triển khai”. Issue #6 (`story-preserve-year-only-precision.md`)
ghi refinement chọn cách lưu/migration; Boundaries cấm thêm schema.

## Quyết định

`case_state_json.stage[]` là **nguồn bằng chứng cho độ đầy đủ ngày Người**
(`ngay_sinh`/`ngay_chet`/`ngay_cap`) trên đường soạn hồ sơ:

- `workspace_get`/`create`/`commit_stage` và Word emit/đọc theo **key-presence**:
  key có trong snapshot là nguồn (kể cả `null` → chặn fallback); key vắng
  (snapshot cũ) → fallback master `customers`.
- Fallback master là `date` (cột `Date`, `models.py:43`) → **ghi nhận dạng
  đầy đủ** `dd/mm/yyyy`; không hạ ngày Jan-1 thành chỉ-năm trên đường case.
- Formatter render theo độ đầy đủ đã lưu: chuỗi `YYYY` → năm,
  `YYYY-MM-DD` → `dd/mm/yyyy`; token `Năm sinh`/`Năm chết` chỉ in năm.
- **Không** đổi schema, **không** migration, **không** tái tạo precision đã
  mất; master vẫn là danh bạ chia sẻ và vẫn ghi như cũ (`_upsert_people`).

## Phương án đã loại

1. **Thêm cột/biểu diễn precision vào master `customers`** (schema + migration):
   cần backfill cho dữ liệu cũ mà `date(y,1,1)` không phân biệt được “cả năm”
   với “01/01 thật” → vi phạm Boundaries “không schema” và lệnh cấm tái tạo.
2. **Giữ đọc master trước cho tiện** — chính là defect: `2010` → `2010-01-01`
   khi mở lại, và lần Cập nhật sau ghi ngược giá trị đã phình vào snapshot.
3. **Hạ ngày master Jan-1 xuống chỉ-năm để “đối xứng”** — tự tạo dữ kiện
   không có bằng chứng; owner cấm đoán.

## Bằng chứng (phiên 16/10/2026)

- Trước sửa (probe SQLite tạm + test đỏ): commit wire `["2010","2010-01-01"]`
  → get `["2010-01-01","2010-01-01"]`; sau “sửa ô khác + Cập nhật” snapshot
  thành cả hai `"2010-01-01"`; `diagram_save` cũng ghi lại snapshot qua
  `_compose_stage`; Word hai người không phân biệt, rò ISO trong câu dựng sẵn.
- Sau sửa: round-trip giữ `"2010"` vs `"2010-01-01"`; export DOCX thật cho
  `2010` / `01/01/2010`; fallback master Jan-1 ra `01/01/1980`.
  Log: `_bmad-output/tmp/issue-6-year-only-precision/01-red-before.log`,
  `02-green-focused.log`, `03-focused-regression.log`, `04-probe-after.json`.

## Ranh giới

- Web cũ (`notary_v2/routers/cases.py`, có `_fmt_birth_or_year` riêng) và
  Danh bạ `customers` ngoài phạm vi: không phải nguồn của đường case, không đụng.
- Danh bạ master có giới hạn biểu diễn (cột `Date`); đây là giới hạn của
  danh bạ dùng chung, không phải quyền làm mất precision của hồ sơ.
- Giữ nguyên validation/retry/security và revision/ghi nguyên tử hiện hành.
