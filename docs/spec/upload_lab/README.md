# upload_lab — Số hóa và chuẩn bị upload hồ sơ cũ

**Trạng thái:** Active; Electron migration đang theo contract riêng

## 1. Mục tiêu và lý do

Đọc hồ sơ Word chuyên viên đã soạn, biến thành dữ liệu có cấu trúc, đối chiếu
sổ Excel từ portal và chuẩn bị form upload để người dùng kiểm tra.

**Tại sao đọc Word:** phần mềm quản lý cũ của văn phòng không có API lấy dữ
liệu. Vì vậy nguồn thực tế là file Word công việc. Nếu nhà cung cấp mở API/DB,
phải hỏi lại owner trước khi đổi hướng.

## 2. Flow chính

```text
Word .doc/.docx
→ quét, phân loại, bóc trường
→ JSON + registry.sqlite3 + run manifest
→ tải/nạp Excel portal và audit
→ phân loại hàng đợi
→ Playwright điền sẵn form
→ người dùng kiểm tra và tự bấm Lưu
→ ghi nhận kết quả
```

## 3. Quét và trích xuất

- `.docx`: `python-docx`, giữ thứ tự đoạn và bảng để không trộn Bên A/B.
- `.doc`: Windows IFilter, không cần mở Word.
- Phân loại: chuyển nhượng, cam kết tài sản riêng, thế chấp, phân chia/từ chối
  di sản và generic.
- Bóc trường: đương sự, người yêu cầu, tài sản, số/ngày công chứng, công chứng
  viên và nhóm hợp đồng.
- Lưu JSON, registry SQLite và manifest của đúng lượt quét.

Catalog regex lớn nằm tại `upload_lab/docs/regex-rules.md`; spec này sở hữu ý
nghĩa flow, catalog chỉ sở hữu chi tiết pattern.

## 4. Audit Excel

- Nạp Excel do portal cung cấp hoặc tải qua browser đã đăng nhập.
- Chuẩn hóa số công chứng về `xxx/yyyy`.
- Tìm số thiếu, lỗi, trùng và sai năm theo khoảng ngày.
- Kết quả cũ phải đánh dấu chưa cập nhật khi nguồn hoặc khoảng ngày đổi.
- Nạp lỗi không được trình bày KPI cũ như kết quả nguồn mới.

## 5. Hàng đợi và upload

- Chưa có trên Excel: gợi ý chọn upload.
- Đã có: bỏ chọn để tránh trùng.
- Sai format/năm/không có số: cảnh báo người dùng.
- Người dùng chọn 1–30 tab mỗi đợt; mỗi tab gắn một `record_id`.
- App điền sẵn rồi dừng trước nút Lưu.
- Người dùng tự kiểm tra và tự bấm Lưu; app không bấm thay.
- Chỉ sau phản hồi lưu thành công hoặc điều hướng tương đương mới ghi
  `uploaded_success` và bỏ dòng khỏi bảng.

**Tại sao:** portal là hệ thống bên ngoài và dữ liệu có ý nghĩa pháp lý. Người
dùng phải giữ quyền kiểm tra cuối; tự điền không đồng nghĩa tự ghi.

## 6. Giao diện

Electron đích có hai tab toàn chiều rộng:

1. `Audit Sổ Công Chứng`.
2. `Quét & Upload Hồ Sơ`.

Không có trang Cấu hình hoặc Nhật ký riêng. Website và kiểm tra môi trường nằm
đầu tab Audit; lỗi/kết quả hiển thị tại vùng liên quan. Chuyển tab/module phải
giữ nguồn, bộ lọc, kết quả, lựa chọn và tiến độ tác vụ.

Audit dùng hai bảng 4 cột: `STT | Ngày | Số công chứng | Ghi chú`.
Upload dùng bảng 6 cột: `✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ file`.

Quy tắc nhìn chung ở [`../ui/`](../ui/README.md); hành vi chi tiết hiện hành
được đối chiếu tại `upload_lab/docs/spec_UI.md`.

## 7. Kiến trúc và contract

- Engine Python sở hữu scan, audit, browser session và registry.
- Electron gửi command và hiển thị state; không chứa parser hoặc Playwright.
- Một Chromium headed dùng chung cho đăng nhập, tải Excel và chuẩn bị upload.
- Không lưu username/password; session browser dùng storage state cục bộ.
- Contract shell↔engine: [`contracts/upload-workflow.md`](../../../contracts/upload-workflow.md).

## 8. Lỗi và khôi phục

- Scan/extract lỗi ghi theo record, không làm mất record khác.
- Browser chưa đăng nhập: chuyển `waiting_user`, không giả `completed`.
- File đang mở, path dài, Unicode và quyền đọc/ghi phải có lỗi rõ.
- Không để luồng legacy và Electron cùng chiếm browser hoặc ghi registry.
- Rollback giữ dữ liệu legacy gốc và bản Electron để đối chiếu.

## 9. Câu hỏi và lịch sử

### Đã chốt

- Nguồn chính là Word vì phần mềm cũ không có API.
- Người dùng tự bấm Lưu trên portal.
- Hai tab Electron; bỏ trang Nhật ký.

### Còn mở

- Website thứ hai chỉ thêm khi có contract/selectors thật.
- A1 về IFilter khi Word đang mở và A3 về ổ mạng phải đo trên máy thật khi
  chúng ảnh hưởng flow Upload.

## 10. Nguồn

- `upload_lab/README.md`.
- `upload_lab/docs/spec_UI.md`.
- `upload_lab/docs/handoff-login-handshake.md`.
- `upload_lab/docs/regex-rules.md`.
