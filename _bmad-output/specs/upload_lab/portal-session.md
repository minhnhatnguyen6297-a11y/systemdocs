# Phiên portal — đăng nhập thủ công và nhận diện Lưu hồ sơ

**Trạng thái:** Quy tắc đăng nhập/Lưu hiện hành; mục **Cách dùng** mô tả UI Qt
cũ, không phải bố cục đích Electron. Bố cục đích ở [`ui.md`](./ui.md) và
[`README.md`](./README.md). **Nguồn:** `upload_lab/docs/handoff-login-handshake.md`
trước đợt gom 29/09/2026; MIN-31.

**Input:** website đã chọn, phiên Chromium do Python quản lý, mỗi tab gắn một
`record_id`. **Output:** trạng thái đăng nhập/storage state cục bộ; sau tín
hiệu Lưu thành công mới đổi record sang `uploaded_success`. Không lưu mật
khẩu, không tự bấm Lưu, không suy thành công chỉ vì đã điền form.

## Mục tiêu đã chốt

- App không lưu tên đăng nhập hoặc mật khẩu.
- Người dùng tự đăng nhập trong Chromium do app mở. App nhận ra đăng nhập khi web có `access_token` trong local storage và đã rời trang `/dang-nhap`.
- Một Chromium được dùng chung cho đăng nhập, tải Excel và chuẩn bị upload.
- Sau khi người dùng bấm **Lưu** trên một tab hồ sơ, app tự nhận biết và chuyển hồ sơ thành `uploaded_success`. Dòng đó tự biến khỏi bảng.
- Người dùng chọn số tab mở mỗi đợt ngay trên màn hình Folder Scan & Upload, từ 1 đến 30.

## Cách dùng

Các bước dưới là đường thao tác trong UI Qt/Fluent cũ. Electron đích đặt
chọn website và mở đăng nhập ở đầu tab Audit, không có trang Cấu hình riêng.

1. Bấm **Cấu hình**.
2. Nhập địa chỉ web nếu cần, rồi bấm **Mở trình duyệt đăng nhập**.
3. Đăng nhập trên Chromium. App tự báo đã đăng nhập; nút **Tôi đã đăng nhập** chỉ là cách kiểm tra ngay nếu cần.
4. Quét folder, chọn hồ sơ và bấm Upload.
5. Kiểm tra thông tin trong từng tab Chromium rồi tự bấm **Lưu** trên web.
6. App tự đóng tab đã Lưu và bỏ dòng hồ sơ đó khỏi bảng. Bấm **Tiếp tục N số tiếp theo** để mở đợt mới.

## Kiểm tra môi trường khi đăng nhập lần đầu

- Trước lần mở đăng nhập đầu tiên, app cần có nút **Kiểm tra môi trường và mở đăng nhập**. Bộ kiểm tra chạy nền, không được làm app tự thoát khi lỗi.
- Phải kiểm tra: quyền ghi thư mục app, dung lượng đĩa, thư viện Playwright, Chromium đi kèm, mạng/DNS, HTTPS đến trang đăng nhập và việc Chromium thật mở được URL.
- Chrome cài sẵn không phải điều kiện bắt buộc vì app dùng Chromium của Playwright. Chỉ ghi nhận phiên bản Chrome/Edge để chẩn đoán hoặc khi người dùng chủ động chọn dùng chúng.
- Windows 10 cần được ghi là **tương thích có kiểm tra**: Playwright hiện hỗ trợ chính thức Windows 11+; không tự nâng cấp Playwright/Chromium trên máy Windows 10.
- Kết quả phải chỉ rõ bước nào lỗi, có nút Thử lại/Sao chép chẩn đoán, và chỉ lưu log đã bỏ token, cookie, mật khẩu và URL có query.

Đặc tả đầy đủ, gồm mức chặn/cảnh báo và tiêu chí chấp nhận, nằm trong [Linear MIN-31](https://linear.app/minhnotary/issue/MIN-31/upload-lab-fluent-ui-redesign-specification-windows-11).

## Quy tắc kỹ thuật quan trọng

- URL mặc định là `https://congchungnamdinh.ninhbinh.gov.vn`.
- Route đăng nhập và tạo nhanh được tự suy ra từ địa chỉ web. Có thể đặt `ND_LOGIN_URL` hoặc `ND_CREATE_URL` trong `.env` nếu web đổi route.
- Token đăng nhập nằm trong local storage, không phải cookie. Playwright lưu lại storage state sau khi phát hiện đăng nhập thành công.
- Phải phân biệt hai luồng, đối chiếu source ngày 15/10/2026: workflow v1
  chỉ đánh dấu đã Lưu khi tab nhận `POST /api/hoso` trả HTTP 2xx; chỉ rời trang
  tạo mới thì chuyển sang cần đối chiếu (`needs_reconcile`). Luồng legacy
  không truyền `workflow_version` còn nhận cả dấu hiệu rời trang. Không áp
  fallback của legacy cho v1; [contract workflow](../../../contracts/upload-workflow.md)
  vẫn Draft, việc mô tả code ở đây không nâng trạng thái duyệt của contract.
- Mỗi tab gắn một `record_id`. Với v1, đóng tab/browser trước khi có kết quả
  đã xác minh phải đối chiếu lại; không tự mở lại hoặc gửi lại hồ sơ chưa rõ.
  Luồng legacy cũ có thể cho chuẩn bị lại khi tab đóng.
- Engine dùng sự kiện phản hồi trên tab do app mở, rồi kiểm tra khoảng 0,5
  giây khi rảnh; thao tác đang chạy có thể làm chậm vòng kiểm tra. Không có
  thời hạn tự coi hồ sơ chưa bấm Lưu là đã Lưu. Máy ngủ không được kiểm tra;
  sau gián đoạn cần đối chiếu các hồ sơ chưa rõ, không bảo đảm giữ nội dung
  form chưa Lưu qua lần đóng browser hoặc khởi động lại app.
- Giới hạn hiện tại: code kiểm phương thức/path/mã HTTP, chưa kiểm nội dung
  phản hồi, hostname hoặc tính đầy đủ của từng trường. Chưa có bằng chứng cổng
  thật luôn dùng HTTP lỗi cho lỗi nghiệp vụ. Một lần POST 2xx được tính cho cả
  hồ sơ; engine không xác minh từng trường đã lưu đủ hay chỉ lưu một phần.
- Đã tái hiện bằng mô phỏng: nhận phản hồi Lưu rồi đóng tab trước vòng kiểm
  tra tiếp theo có thể vẫn bị ghi là `closed`/cần đối chiếu, vì code kiểm tab
  đóng trước cờ phản hồi. Nếu mất phản hồi mà vẫn ở trang tạo mới, tab có thể
  tiếp tục chờ vô thời hạn. Cần kiểm cổng thật và các tình huống gián đoạn
  trước khi kết luận tín hiệu này đủ tin cậy; chưa sửa engine trong phiên docs.
- Log mạng chỉ ghi phương thức, URL không có query string và mã trạng thái; không ghi token, cookie hay nội dung request.

## Không làm trong phạm vi này

- Không nhúng Chrome vào giao diện app.
- Không gửi hồ sơ bằng REST API thay cho Playwright.
- Không tự bấm nút Lưu thay người dùng.
- Không tự mở ngay đợt kế tiếp sau khi phát hiện Lưu.
