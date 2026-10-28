> **Lịch sử trước đợt gom 15/10/2026. Không phải nguồn hành vi hiện hành; không nạp mặc định đầu phiên. Trạng thái Draft/đã duyệt trong bản gốc được giữ nguyên.**

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

Tài liệu trích Word:

- [Core](regex-core.md): phạm vi và vòng kiểm tra.
- [Quy tắc từng trường](regex-fields.md): một nguồn cho tên/giới tính/ngày/giấy tờ/đất; điểm chưa chốt ghi riêng.
- [Đáp án đích](regex-expected-results.md): mẫu nguồn, trường phải kiểm, Closed/Pending.
- [Ranh giới chấp nhận](regex-acceptance.md): lỗi máy, lỗi nguồn, ngoài phạm vi và cách báo kết quả từng phần.
- [Thừa kế](regex-thua-ke.md): loại/vùng và đầu-cuối bản ghi.
- [Catalog](regex-rules.md): các cấu trúc/loại khác, dẫn tới luật trường.

Trang README này sở hữu flow; các trang trên không tự thay contract Stage.

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
- Workflow v1 hiện chỉ ghi `uploaded_success` sau `POST /api/hoso` trả HTTP
  2xx; điều hướng đơn thuần hoặc đóng tab chưa rõ phải đối chiếu lại. Legacy
  không truyền `workflow_version` còn cho fallback điều hướng. Xem phạm vi,
  giới hạn kiểm chứng và contract Draft tại [phiên portal](portal-session.md).

**Tại sao:** portal là hệ thống bên ngoài và dữ liệu có ý nghĩa pháp lý. Người
dùng phải giữ quyền kiểm tra cuối; tự điền không đồng nghĩa tự ghi.

## 6. Giao diện

Electron đích có hai tab toàn chiều rộng:

1. `Audit Sổ Công Chứng`.
2. `Quét & Upload Hồ Sơ`.

Không có trang Cấu hình hoặc Nhật ký riêng. Website và kiểm tra môi trường nằm
đầu tab Audit; lỗi/kết quả hiển thị tại vùng liên quan. Chuyển tab/module phải
giữ nguồn, bộ lọc, kết quả, lựa chọn và tiến độ tác vụ.

NAIA-4 Word-first hiện dùng dialog Nhập file và Xuất Word của Soạn hồ sơ,
không phát hành tab Upload thứ ba. Lõi regex NAIA-3 là nguồn quy tắc chung;
parser DOCX và bằng chứng thuộc Document Intake, binding/xuất thuộc Word.
Xem [`luồng DOCX`](../notary_v2/input/docx-import.md).

Audit dùng hai bảng 4 cột: `STT | Ngày | Số công chứng | Ghi chú`.
Upload dùng bảng 6 cột: `✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ file`.

Quy tắc nhìn chung ở [`../ui/`](../../../specs/ui/README.md); hành vi chi tiết hiện hành
được đối chiếu tại [`ui.md`](ui.md). Ảnh mockup và UI cũ nằm trong
[`references/`](../../../specs/upload_lab/references) để tham khảo, không tự thành bản duyệt Electron.

## 7. Kiến trúc và contract

- Engine Python sở hữu scan, audit, browser session và registry.
- Electron gửi command và hiển thị state; không chứa parser hoặc Playwright.
- Một Chromium headed dùng chung cho đăng nhập, tải Excel và chuẩn bị upload.
- Không lưu username/password; session browser dùng storage state cục bộ.
- Contract shell↔engine: [`contracts/upload-workflow.md`](../../../../contracts/upload-workflow.md).
- Đăng nhập thủ công và dấu hiệu nhận biết Lưu: [`portal-session.md`](portal-session.md).

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

### POC DesktopCommand 11/09/2026 — chỉ là bằng chứng

POC FastAPI loopback + Electron giả lập kết luận **ITERATE**, không phải quyết
định đưa vào production. Smoke dùng fake worker, không mở portal, không có
thông tin khách. Mẫu đo một máy: Electron + sidecar 2,6 giây tới cửa sổ,
341,4 MiB idle; Qt 0,5 giây quan sát, 179,1 MiB idle. Chưa đo browser đang
upload, restart/shutdown ổn định hoặc flow thật. Report và kế hoạch gốc ở Git
baseline `072870e`; phải đo lại theo cùng quy trình trước quyết định áp dụng.

## 10. Nguồn

- `upload_lab/README.md`.
- [`ui.md`](ui.md) — hành vi/bố cục và phần thị giác Proposed.
- [`portal-session.md`](portal-session.md) — đăng nhập và nhận diện Lưu.
- [regex-fields.md](regex-fields.md) — quy tắc từng trường.
- [regex-expected-results.md](regex-expected-results.md) — đáp án đích và phạm vi chấm.
- [regex-rules.md](regex-rules.md) — catalog cấu trúc/loại.
