# Quyết định — đã chốt và chưa chốt

Danh sách các câu hỏi **xuyên sản phẩm** hoặc **có thể thay đổi thiết kế**.
Nếu một task chạm vào mục còn 🔴, agent phải **dừng và hỏi**, không được chọn giúp.
Mục 🟢 là đã chốt — giữ lại để không ai đề xuất lại.

Cập nhật định tuyến SOT: 28/09/2026. Các quyết định gốc có ngày và phạm vi
riêng trong file sở hữu; ngày này không có nghĩa chúng vừa được quyết định lại.

Ký hiệu: 🔴 chưa có dữ liệu · 🟡 có khuyến nghị, chờ duyệt · 🟢 đã chốt

---

## A. Phải đi đo trên máy thật, không suy luận được trên giấy

**A1–A4 thuộc `notaryoffice`.** Trạng thái, hệ quả và lý do của từng câu chỉ
được cập nhật ở [notaryoffice/intent.md §10.1](../../notaryoffice/intent.md).
Mục A này giữ tên mã cũ để các link hiện có vẫn dẫn người đọc tới nguồn sở hữu;
không duy trì bảng trạng thái thứ hai tại đây.

---

## B. Chủ dự án đã quyết định

| # | Câu hỏi | Trạng thái |
|---|---|---|
| B1 | Văn phòng có phần mềm quản lý hồ sơ đang dùng? Có đọc được dữ liệu ra? | ↗ [upload_lab/README.md](../../upload_lab/README.md) sở hữu kết luận và lý do |
| B2 | Phạm vi đọc Zalo | 🟢 **Làm ngay, không hoãn** — theo ranh giới bên dưới |
| B3 | Thông báo cho nhân viên + đưa vào nội quy lao động | ↗ [notaryoffice/intent.md §10.1](../../notaryoffice/intent.md) sở hữu kết luận |
| B4 | Chọn 2 chuyên viên cho giai đoạn thử nghiệm | ↗ [notaryoffice/intent.md §10.1](../../notaryoffice/intent.md) sở hữu kết luận |

### B1 — vì sao `upload_lab` tồn tại

Kết luận, lý do ngành và điều kiện hỏi lại thuộc [upload_lab/README.md](../../upload_lab/README.md).
Mục B1 giữ mã cũ để các link lịch sử tiếp tục dẫn tới nơi sở hữu; không cập
nhật một bản giải thích song song ở đây.

### B2 — ranh giới đọc Zalo (đã chốt)

Làm ngay, không hoãn. Nhưng đúng phạm vi sau, không rộng hơn:

| Được | Không được |
|---|---|
| Dùng **một tài khoản Zalo chung của Văn phòng** | Dùng tài khoản Zalo **của nhân viên** |
| Đọc tin nhắn trong **nhóm** mà tài khoản đó tham gia | Đọc tin nhắn riêng của bất kỳ nhân viên nào |
| Đọc **tin nhắn riêng gửi đến chính tài khoản văn phòng** | |
| Chạy **chỉ trên máy chủ** | Chạy trên máy trạm của chuyên viên |

Ba điều kiện này là **ranh giới quyền riêng tư**, không phải chi tiết triển khai.
Agent không được nới ra để "tăng độ phủ dữ liệu". Muốn đổi → hỏi.
Lý do gốc ghi trong `notaryoffice/intent.md` trước khi định tuyến SOT: ranh giới
này bảo vệ sự riêng tư của nhân viên, tuân thủ pháp luật và tránh nguy cơ tài
khoản Zalo cá nhân của nhân viên bị khóa. Nguồn lời owner nguyên văn cho lý do
này chưa được dẫn trong tài liệu hiện có.

Ghi chú: mục này gộp cả phần Zalo của `notaryoffice` và Zalo Document Inbox của
`notary_v2` — cùng một ranh giới, cùng một tài khoản chung; đích vận hành là
server, còn bước phát triển local được chốt bên dưới.

**Quyết định mới nhất của owner 24/09/2026:** module nghiên cứu Zalo được phát
triển trước trong **thư mục/repo local riêng** (đề xuất `D:\zalo-intake`), sau
đó mới chạy độc lập trên Windows server; chưa triển khai server ở giai đoạn
này. Dữ liệu công chứng ở một máy chính dùng chung, được phép tắt. Hai repo chỉ
kết nối qua giao diện trao đổi dữ liệu. Xem [draft MIN-89](../product/specs/2026-09-24-zalo-independent-intake.md).
Sau [MIN-103](https://linear.app/minhnotary/issue/MIN-103/migrate-engine-zalo-thanh-module-thu-tu-trong-repo-rieng-va-zalo),
repo nguồn `D:\zalo-intake` **đã có** và `zalo/` trong monorepo là snapshot một
chiều. Tài liệu producer đã chuyển sang repo nguồn và snapshot `zalo/docs/`;
Notary giữ tài liệu consumer/Sync riêng. Xem [quyền sở hữu repo](../../zalo/docs/repo-ownership.md)
và [cửa vào Notary](../../notary_v2/docs/platform/zalo-document-inbox/README.md)
trước khi sửa engine; không tạo hai nguồn spec engine cùng quyền quyết định.
Owner đã chốt **phương án A**: module Zalo nhận/giữ ảnh, thực hiện bước chuẩn
bị ảnh cần byte ảnh và gọi Qwen OCR API; không build engine OCR riêng. Module
bàn giao **chữ OCR thô, trạng thái xử lý, thời gian và dấu vết nguồn**, không
gửi ảnh. **Soạn hồ sơ/Document Intake sở hữu và chạy** regex, phân loại, bóc
trường, ghép mặt giấy tờ/người/tài sản và gợi ý nhóm hồ sơ từ chữ đã Sync.
Đây là cùng năng lực xử lý đầu vào nghiệp vụ cho các nguồn, không tạo parser
nghiệp vụ thứ hai trong bot. Kết quả máy phân tích chỉ là đề xuất; người dùng
kiểm tra/xác nhận trước khi đưa vào đầu vào soạn thảo. MIN-92 chốt schema gói
raw và nguồn đối chiếu, không yêu cầu bot xuất `results.json` đã xử lý.
Owner đã chọn giữ **gói file raw trong folder máy chính** để kiểm tra sai sót;
máy chính vẫn chủ động Sync và ACK sau khi lưu raw. Khi parser cần thêm chữ,
Soạn hồ sơ được yêu cầu bot OCR một biến thể định sẵn theo ID ảnh trong hạn
168 giờ; bot chỉ trả raw revision mới, không chuyển ảnh hoặc hiểu trường nghiệp
vụ. Contract MIN-92 chốt enum, giới hạn lượt, quyền và chống lặp; kết quả nội
bộ/DraftInput thuộc MIN-102.
Máy chính không tải/lưu ảnh Zalo; người dùng đối chiếu ảnh trong Zalo thật ngoài
hệ thống. Ảnh trong module xóa sau **7 ngày từ `captured_at`**, là lúc bot bắt
tin; `source_sent_at` và `imported_at` chỉ là mốc phụ. Gói OCR raw chưa ACK phải
giữ; raw trên bot sau ACK phải có hạn dọn hữu hạn trước khi dùng dữ liệu thật;
kết quả xử lý trên máy chính theo chính sách dữ liệu hồ sơ.
Giai đoạn đầu giả định bot thu đủ sự kiện, **chưa có bằng chứng xác minh đủ**;
khôi phục khi nguồn không giao sự kiện thuộc MIN-90, để giai đoạn sau.

Chi tiết giao tiếp chưa APPROVED. Còn mở trong MIN-89/MIN-92: schema/version
của gói OCR raw, endpoint/xác thực, enum và mức giới hạn OCR lại, lưu lượng/
dung lượng, số ngày giữ raw sau ACK và nơi nhận cảnh báo ban đêm. Vị trí chạy parser đã chốt là Document Intake trên
máy chính; khả năng history/OA để lấy bù nguồn cần thử
ở MIN-90. Không dùng quyết định một máy chính này để tự chốt A1/A3/A4 về Word,
ổ mạng hoặc Windows user của `notaryoffice`.

---

## C. Rủi ro lớn nhất — không phải rủi ro kỹ thuật

Rủi ro bấm xác nhận theo phản xạ, lý do ngành và giới hạn thông báo thuộc
[notaryoffice/intent.md §10.2](../../notaryoffice/intent.md). Mục C giữ tên cũ
để các link lịch sử còn dẫn được tới nguồn sở hữu; không cập nhật con số tại đây.

---

## D. Đã chốt — đừng đề xuất lại

Mục này giữ đường vào lịch sử, **không còn là bảng quyết định riêng**:

- Đọc API/DB phần mềm cũ → [Upload Lab README, B1](../../upload_lab/README.md).
- FileWatcher tập trung, xử lý toàn bộ trên máy con, tự ghép hồ sơ bằng điểm →
  [notaryoffice/intent.md §6.3](../../notaryoffice/intent.md).
- Số bản in Print Spooler → [notaryoffice/intent.md §10.1, A2](../../notaryoffice/intent.md).
- Zalo cá nhân của nhân viên → [B2 trong file này](#b2--ranh-giới-đọc-zalo-đã-chốt).
- Local OCR của Notary đang để ngoài luồng hiện hành →
  [Document Intake README](../../notary_v2/docs/platform/document-intake/README.md).
- OCR provider thứ hai → [TECH_STACK.md §2](TECH_STACK.md).

---

## E. Về việc gộp hệ thống — không còn là câu hỏi mở

Định hướng đã rõ: **gộp thành một hệ thống thống nhất, dùng chung database
nghiệp vụ** cho `notary_v2`, `upload_lab` và `notaryoffice`. Module Zalo thứ tư
thu nhận nguồn, được giữ DB/session/runtime riêng và giao tiếp qua contract;
`shell` là hạ tầng giao diện.

Giai đoạn hiện tại: **làm tốt từng phần, chưa vội gộp.** Xem
[`VISION.md`](./VISION.md) mục 4 và [`TECH_STACK.md`](./TECH_STACK.md) mục 3 cho
các ràng buộc thiết kế phải tuân theo từ bây giờ để lúc gộp không xung đột.

Điều này **không** có nghĩa agent được tự ý nối hai repo lại. Nối = tích hợp =
phải có contract được duyệt trước (`contracts/README.md`).
