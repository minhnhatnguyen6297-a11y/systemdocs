# Core regex trích xuất Người + Tài sản

**Trạng thái:** Active · **Cập nhật:** 06/10/2026 · **Phạm vi:** `upload_lab`
(engine, test, validator, tool test) + repo test cho nhân viên
(`regex-test-tool/`)

Trang này là bản đồ duy nhất của core regex: tool là gì, làm việc
thế nào, sửa lỗi ra sao, tinh thần nào giữ xuyên suốt, owner đã
chốt gì. Chi tiết pattern từng loại văn bản nằm ở file riêng
(`regex-thua-ke.md`, ...); catalog tra nhanh nằm ở
[`regex-rules.md`](./regex-rules.md).

## 1. Core là gì, không là gì

Core regex chỉ làm đúng 1 việc: **đọc văn bản Word, xuất dữ liệu
người + tài sản** (regex, tất định, không AI).

Core **không** làm: so sánh, đối chiếu, gộp hồ sơ, phán quyết pháp
lý. Quy tắc của owner: **có người nào xuất dữ liệu người đó** —
kể cả người trong Lời chứng khác đầu văn bản. Việc đối chiếu đúng
sai là của tầng khác (người kiểm tra + validator).

Core chịu trách nhiệm đúng 2 nhóm: **người** (sống, đã chết, lời
chứng) và **tài sản** (đất từng thửa, sổ tiết kiệm/tài khoản, bảo
hiểm). Số công chứng vẫn được đọc để phục vụ upload/audit nhưng
không còn là tiêu chí đủ/thiếu của core.

## 2. Hai flow (không lẫn nhau)

| | Flow người dùng | Flow phát triển (việc đang làm) |
|---|---|---|
| Ai | Nhân viên văn phòng | Agent + owner |
| Làm gì | Mở tool → import file/thư mục → xem bảng → gửi log | Đọc mẫu → viết/sửa regex → test → báo cáo |
| Ra gì | Log `.jsonl` gửi về | Code + test xanh + báo cáo vòng |
| Chuẩn đúng sai | Bảng trong tool (ô vàng = thiếu) | Mã luật R00..R11 trong code |

## 3. Cách làm việc (vòng lặp bắt buộc)

```text
mẫu thật → đáp án (comment/field-list) → chạy engine → đối chiếu
→ sửa code → test giữ hành vi → quét hàng loạt → báo cáo vòng
```

1. Mỗi vòng làm **1 loại văn bản** (thừa kế trước, thế chấp tiếp).
2. Đáp án lấy từ file mẫu của owner (comment Word với `.docx`,
   danh sách trường cuối file với `.doc`).
3. Không commit khi test đỏ. Không đoán số liệu trôi nổi: pattern
   nào cũng phải có nhãn neo (`Sinh năm`, `Số thửa`, ...).
4. Số liệu giữ nguyên chữ trong văn bản (diện tích tuyệt đối chính
   xác, không làm tròn). Thiếu căn cứ thì để trống + gắn cờ, không
   tự bịa, không tự suy mã.

## 4. Cách sửa lỗi

1. Lỗi chỉ công nhận khi **mã trong code** báo:
   `upload_lab/kiem_tra_trich_xuat.py` (R00 bỏ qua, R01 sai loại,
   R02 0 người, R03 thiếu trường người, R04 tên bẩn, R05 trùng tên,
   R06 thiếu người chết, R07 thiếu trường người chết, R08 mất khối
   tài sản, R09 không tách tài sản, R10 lệch diện tích tuyệt đối,
   R11 lời chứng khác). Agent/LLM chỉ đọc mã, không tự đặt tên lỗi.
2. Sửa ở engine (`upload_lab/extract_contract.py`), thêm test giữ
   hành vi, chạy toàn bộ suite.
3. Quét lại hàng loạt bằng `upload_lab/tools/quet_kiem_tra.py`
   (cùng bộ luật, không chấm tay).
4. Ghi quyết định mới vào mục 7 dưới đây + spec loại văn bản.

## 5. Tinh thần giữ xuyên suốt

- Máy đề xuất, người quyết định cuối; thiếu bằng chứng thì để
  trống, không tự điền.
- Có người nào xuất người đó; trùng/khác thì gắn cờ cho người kiểm,
  core không tự gộp, không tự loại.
- Tương thích ngược: thêm field mới không xóa field cũ; đổi hành vi
  phải có test mới + cập nhật catalog cùng thay đổi.
- PII (tên, CCCD) chỉ ở máy nội bộ và file log gửi tay; không ghi
  log rộng, không đăng mạng.

## 6. File và vị trí (để agent sau tìm đúng)

| Thứ | File |
|---|---|
| Engine (code duy nhất) | `upload_lab/extract_contract.py` (`ENGINE_VERSION`) |
| Luật kiểm tra R00..R11 | `upload_lab/kiem_tra_trich_xuat.py` |
| Quét hàng loạt chuẩn | `upload_lab/tools/quet_kiem_tra.py` |
| Test giữ hành vi | `upload_lab/tests/test_upload_lab_extract_contract.py` + `test_kiem_tra_trich_xuat.py` |
| Catalog tra nhanh | `docs/spec/upload_lab/regex-rules.md` |
| Chi tiết từng loại (SOT theo loại) | `docs/spec/upload_lab/regex-<loai>.md` |
| Báo cáo từng vòng (tạm, không commit) | `.agent/scratch/regex-core/bao-cao-NN-*.md` |
| Repo test cho nhân viên | `regex-test-tool/tool/` tất cả trong 1 folder (engine snapshot + `ENGINE_VERSION`, log đóng dấu bản) |

Mỗi lần đổi engine: sửa ở `upload_lab`, tăng `ENGINE_VERSION`,
copy snapshot sang `regex-test-tool/tool/` (ghi đè `extract_contract.py` + `kiem_tra_trich_xuat.py`).

## 7. Quyết định của owner (nguồn sự thật cho code)

| Ngày | Quyết định |
|---|---|
| 05/10/2026 | Tài sản nhiều thửa thì tách, mỗi thửa 1 dòng |
| 05/10/2026 | Số công chứng ra khỏi tiêu chí đủ/thiếu của core (vẫn đọc cho upload/audit) |
| 05/10/2026 | Core chỉ trích xuất, không so sánh/gộp |
| 05/10/2026 | Core vẫn nằm trong `upload_lab`, ghi rõ vị trí cho agent sau |
| 06/10/2026 | Người chỉ có năm sinh thì xuất đúng `YYYY` + cờ `chi_co_nam_sinh`, không tự thêm `01/01` |
| 06/10/2026 | Chuột phải copy ngay ô đang bấm (không menu); nút riêng cuối dòng copy cả dòng |
| 06/10/2026 | Quét thư mục không cần phân loại trước; lỗi 1 file không dừng đợt; log là bản giao |
| 06/10/2026 | Diện tích tuyệt đối chính xác, không làm tròn (epsilon 1e-9 chỉ trừ sai số máy) |
| 06/10/2026 | `loai_dat` giữ chữ gốc trong văn bản, không tự suy mã khi thiếu căn cứ |

## 8. Câu hỏi mở và cảnh báo

- [CONFIRM] `loai_tai_san` của bảo hiểm để `Tài sản khác` vì portal
  chưa có enum bảo hiểm — có cần thêm enum trên portal?
- [CONFIRM] Người đã từ chối nhưng vẫn đứng tên ở mở đầu văn bản
  (Uy/Thúy...) hiện vẫn xuất ở đương sự + cờ R11 — có cần mục
  riêng "người liên quan đã từ chối"?
- Cảnh báo: văn bản thật có lỗi đánh máy của chuyên viên (sai tên
  bố mẹ, Lời chứng khác đầu văn bản, tổng diện tích thiếu) —
  engine bóc đúng như văn bản viết và gắn cờ, người kiểm tra văn
  bản gốc, không đổ lỗi cho tool.
- Cảnh báo: file `.doc` đọc chậm (IFilter) và hay dồn bảng; code đã
  giữ TAB thành `|` nhưng văn bản quá nát vẫn cần người đọc lại.
- Chưa xong: các loại văn bản ngoài thừa kế (chuyển nhượng, tặng
  cho, thế chấp, cam kết, ủy quyền...) — làm tiếp từng loại.

## 9. Nguồn

- Spec hệ thống: [`README.md`](./README.md) (flow),
  [`../README.md`](../README.md) (nguyên tắc chung).
- Contract DB: [`../../contracts/notary-case-drafting.md`](../../contracts/notary-case-drafting.md)
  (shape `asset_row.land_rows`, `person_row` chấp nhận `YYYY`).
- Định danh: [`../../contracts/entities.md`](../../contracts/entities.md).
- Code là bằng chứng hiện trạng; spec quyết định hành vi phải có.
