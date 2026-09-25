# Đặc tả UI — Upload Lab trong Electron shell

Tài liệu này là **nguồn sự thật duy nhất** về bố cục và hành vi giao diện của
Upload Lab khi chuyển sang shell Electron (MIN-69). Nó thay thế mô tả ba
bảng/năm cột trước đây trong chính file này — cấu trúc bảng hiện hành là chuẩn
[MIN-77](https://linear.app/minhnotary/issue/MIN-77/bug-chuan-hoa-cot-3-vung-audit-excel-va-rut-gon-cot-bang-upload)
(đã Done) và khớp `ui_qt/main_window.py` hiện tại.

Hành vi nghiệp vụ giữ nguyên từ bản Fluent UI/Qt đang chạy (`run.bat` →
`ui_runner.py` → `ui_qt/main_window.py`) trừ khi spec này nói khác. Giao tiếp
UI ↔ backend theo contract `upload.workflow.v1`
(`../../contracts/upload-workflow.md`).

## 1. Điều hướng và không gian bảng

Shell có một module chính tên **Upload Lab** (module id nội bộ `upload`). Bên
trong có đúng hai tab:

1. **Audit Sổ Công Chứng**
2. **Quét & Upload Hồ Sơ**

- Mỗi tab chiếm **toàn bộ chiều rộng** phần nội dung còn lại của shell.
- Không có sidebar thứ hai trong Upload Lab; không xếp Audit và Upload cạnh
  nhau; không gộp thành một trang dài nhiều khối đóng/mở.
- **Không có tab Cấu hình và không có tab/trang Nhật ký riêng.** Chức năng
  cấu hình/kiểm tra môi trường nằm đầu tab Audit (mục 2); log chẩn đoán chỉ
  tồn tại ở backend đã lọc, không hiển thị thành trang.
- Bỏ trang Nhật ký **không có nghĩa** mất thông báo kết quả hay dữ liệu phục
  hồi: kết quả/lỗi hiển thị inline tại vùng liên quan và trạng thái khôi phục
  vẫn được backend lưu trữ.

### Giữ trạng thái khi chuyển đổi

Đổi tab hoặc sang module khác rồi quay lại phải giữ nguyên:

- website đang chọn, khoảng ngày, đường dẫn file Excel/thư mục đã chọn;
- kết quả audit, kết quả quét và phân loại đang hiển thị;
- ô chọn hồ sơ, lựa chọn đã lọc, vị trí cuộn;
- tác vụ đang chạy (scan, tải Excel, prepare) và tiến độ của nó.

Bảng có vùng cuộn riêng và tiêu đề cột cố định. Đường dẫn file dài được cắt
gọn trong ô nhưng **không kéo vỡ bố cục**; xem đủ đường dẫn bằng tooltip và
mở file gốc trực tiếp từ dòng đó (mở bằng ứng dụng mặc định của Windows, qua
Electron main).

## 2. Tab Audit Sổ Công Chứng

Thứ tự các vùng từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Chọn website | Dropdown tên website; trạng thái kết nối/đăng nhập; nút kiểm tra môi trường và mở đăng nhập. Địa chỉ website có thể hiển thị chỉ-đọc để nhận biết. Không có ô nhập URL tự do. |
| Nguồn sổ | `Từ ngày`, `Đến ngày` (hiển thị `DD/MM/YYYY`), nút `Tải Excel từ Web`; ô đường dẫn + `Chọn tệp Excel...` và `Nạp dữ liệu`. |
| Số liệu | Bốn thẻ KPI: **Tổng số đã nạp**, **Hợp lệ trong sổ**, **Số còn thiếu**, **Lỗi / Trùng lặp**. |
| Bảng | Hai vùng **Số còn thiếu** và **Số lỗi, trùng** xếp trên/dưới, cùng toàn chiều rộng, kéo chia chiều cao được. |

Cả hai bảng dùng đúng **bốn cột** (chuẩn MIN-77):

`STT | Ngày | Số công chứng | Ghi chú`

- Không đưa lại bảng "Danh sách Excel"/số hợp lệ; không có cột `Số dòng`,
  `Năm`, `Loại lỗi`, `Số chuẩn`, `Số gốc` — đã loại ở MIN-77.
- Ô không có ngày hoặc ghi chú hiển thị trống. Số thiếu do chính nó lỗi/trùng
  chỉ nằm ở bảng lỗi, không lặp lại ở bảng thiếu.

### Quy tắc nạp và làm mới

- Chọn file trên máy hoặc tải Excel thành công → **tự nạp và audit** theo
  khoảng ngày đang chọn (giữ hành vi Qt); người dùng vẫn có `Nạp dữ liệu` để
  chạy lại sau khi đổi ngày.
- Đổi ngày hoặc đổi file → kết quả cũ được đánh dấu *chưa cập nhật*; không
  được trình bày kết quả cũ như kết quả của bộ lọc mới.
- Nạp lỗi → vùng hiện tại báo lỗi rõ ngay tại chỗ, **không giữ số liệu cũ**
  dưới nguồn mới.
- Thông báo kiểm tra môi trường hiển thị ở khối đầu trang khi cần (checklist
  đạt/cảnh báo/bị chặn + hướng dẫn đã lọc); trạng thái bình thường chỉ chiếm
  một hàng gọn. Ưu tiên chiều cao cho hai bảng.

## 3. Tab Quét & Upload Hồ Sơ

Thứ tự các vùng từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Ngữ cảnh | Tên website đang dùng, trạng thái đăng nhập, nguồn Excel/khoảng ngày đang đối chiếu; nút quay sang tab Audit để đổi website. |
| Nguồn và nhân sự | `Chọn thư mục`/`Bắt đầu Quét`; Công chứng viên (dropdown), Thư ký (nhập tay), `Cập nhật danh sách`; `Số tab mỗi đợt` từ **1 đến 30**, mặc định **10** nếu chưa có giá trị đã lưu. |
| Tiến độ | Tiến độ quét và tiến độ chuẩn bị biểu mẫu là **hai thanh riêng**; nút `Dừng` bật theo trạng thái đang chạy. |
| Thanh thao tác | `Chọn tất cả`, `Bỏ chọn tất cả`, `Lọc số lỗi`/`Hoàn tác lọc`, `Số thiếu trong Excel`, `Upload file đã chọn (N)`, `Tiếp tục N số tiếp theo`, `Đóng browser upload`. |
| Bảng | Một bảng hồ sơ toàn chiều rộng, cột đúng thứ tự bên dưới. |

Bảng hồ sơ dùng đúng **sáu cột** (chuẩn MIN-77):

`✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ file`

### Quy tắc chọn và phân loại (giữ nguyên từ hiện hành)

- **Chưa có Excel**: vẫn cho quét và xem hồ sơ; không tự chọn là "thiếu trên
  web".
- **Có Excel cùng website**: chọn mặc định các số hợp lệ chưa có trong sổ;
  giữ ghi chú cho số sai format, sai năm, thiếu trường, trùng trong folder.
- Người dùng bỏ chọn thủ công → poll/cập nhật nền **không tự chọn lại**; chỉ
  bỏ khỏi bảng các hồ sơ đã xác minh **Lưu thành công** trên portal.
- `Lọc số lỗi` giữ cơ chế chọn-tạm-thời và `Hoàn tác lọc` của Qt; không đổi
  thành tìm kiếm tự do, không xóa vĩnh viễn dòng khác.
- Dòng đã chọn xếp lên đầu; mọi thao tác dùng **`record_id` thật** — không
  dùng số thứ tự hiển thị (STT) làm định danh.
- Quét nguồn mới tạo ngữ cảnh lượt quét mới (`run_id` mới) và bỏ các ID đã
  chọn của lượt cũ; kết quả của job cũ đến muộn không ghi đè lượt đang xem.

### Quy tắc đợt chuẩn bị (dry-run, người dùng tự Lưu)

- Mỗi đợt mở tối đa **N** tab (`Số tab mỗi đợt`). Đợt sau chỉ bắt đầu khi
  người dùng bấm `Tiếp tục N số tiếp theo`; app **không tự mở đợt kế tiếp**.
- App chỉ điền sẵn biểu mẫu rồi dừng trước nút Lưu; người dùng kiểm tra trực
  quan và tự bấm Lưu trong Chromium. Không có nút "Finalize" trong app.
- `Dừng` kết thúc sau đơn vị đang xử lý theo khả năng engine; trạng thái "đã
  yêu cầu dừng" không đồng nghĩa browser đã ngừng ngay.
- `Đã điền sẵn`, `Đang chờ kiểm tra`, `Đã lưu trên web`, `Lỗi` là các trạng
  thái **khác nhau** trên dòng/trạng thái job. Nút "Xong kiểm tra"
  (`finish_review`) chỉ kết thúc bước chờ — không phải bằng chứng đã Lưu.
- Hồ sơ có thể đã Lưu nhưng chưa xác minh được phải vào nhóm **Cần đối
  chiếu**, hiển thị ngay trong bảng/thanh trạng thái; không được gửi lại cho
  tới khi đối chiếu xong (sổ mới hoặc xác nhận người dùng).

## 4. Dropdown website dùng chung

- Hiện chỉ có một mục hoạt động: **`nam_dinh` — "Nam Định"**, địa chỉ
  `https://congchungnamdinh.ninhbinh.gov.vn` (lấy từ code hiện tại). Nhãn và
  tên miền có thể đổi sau; `website_id` không đổi.
- Danh sách website và thao tác đã hỗ trợ do **backend cung cấp**; frontend
  không chứa danh sách URL hay nhánh nghiệp vụ theo tỉnh, không ô nhập URL.
- Website được chọn quyết định bộ xử lý đăng nhập, tải file, đọc cấu trúc sổ
  và điền biểu mẫu; cùng một lựa chọn áp cho cả hai tab.
- Chỉ cho đổi website khi không có tác vụ/đợt chuẩn bị đang hoạt động hoặc
  tab đang chờ kiểm tra — backend kiểm lại điều kiện, không chỉ khóa
  dropdown ở UI. Đổi website hiển thị trạng thái của website mới; không giữ
  sổ/ô chọn của website cũ dưới tên mới.
- `website_id` không đăng ký bị từ chối (`unknown_website`); không quay về
  Nam Định ngầm. Website thứ hai chỉ được bật khi có bộ xử lý và mẫu file
  thật; không cần thay cấu trúc hai tab.

## 5. Quy tắc hiển thị chung

- **Ngôn ngữ**: toàn bộ nhãn/nút/thông báo là tiếng Việt **có dấu** (chuẩn
  Việt hóa trước đây vẫn giữ: `Từ ngày`, `Đến ngày`, `Số còn thiếu`,
  `Số lỗi, trùng`, `hợp lệ`, `thiếu`, `lỗi`, `trùng`...).
- **Ngày**: trên dây truyền/backend dùng ISO `YYYY-MM-DD`; UI hiển thị
  `DD/MM/YYYY`; bộ xử lý website chuyển sang định dạng portal. Giá trị không
  có là `null` → hiển thị trống/"—", không hiển thị `null` hay `""`.
- **Trạng thái chờ người** (`waiting_user`): banner trong module nêu rõ việc
  cần làm ("Đăng nhập trên cửa sổ Chromium", "Kiểm tra các tab đã điền");
  không phải lỗi. Chromium do Python quản lý chỉ được đưa lên trước **một
  lần có chủ đích**, không giật focus lặp lại.
- **Lỗi**: hiển thị inline tại vùng liên quan theo shape lỗi của contract
  (code + message + retryable + next_action); nút Thử lại chỉ khi
  `retryable: true`. **Không in JSON, tên command, hay stack trace** cho
  người dùng.
- **Không tự hoàn thành bước của người**: không auto-Save, không tự xác nhận
  đăng nhập/review, không tự điền lựa chọn còn trống.
- **Hủy**: có ở trạng thái đang chạy/chờ; hủy không hoàn tác một lần Lưu đã
  xảy ra và không tự đóng các tab người dùng đang kiểm tra.

## 6. Tài liệu liên quan

| Tài liệu | Vai trò |
|---|---|
| `contracts/upload-workflow.md` | Contract `upload.workflow.v1` — command, schema, lỗi, scope/revision giữa shell và sidecar |
| `contracts/desktop-command.md` + `contracts/g1-module-data.md` | Envelope `desktopcommand.v1` và shape `g1.module.v1` mà workflow chạy bên trong |
| `upload_lab/README.md` | Kiến trúc nghiệp vụ/engine và cấu trúc codebase hiện tại |
| `docs/handoff-login-handshake.md` | Hợp đồng luồng đăng nhập thủ công & nhận diện Lưu |
| `docs/regex-rules.md` | Catalog quy tắc regex trích xuất |
| [MIN-69](https://linear.app/minhnotary/issue/MIN-69/migrate-uploadaudit-vao-electron) | Task chuyển sang shell — kế hoạch ở `docs/product/plans/2026-09-24-upload-lab-shell-migration-plan.md` |
| [MIN-77](https://linear.app/minhnotary/issue/MIN-77/bug-chuan-hoa-cot-3-vung-audit-excel-va-rut-gon-cot-bang-upload) | Chuẩn cột bảng đã chốt (đã Done) |
