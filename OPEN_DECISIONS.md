# Quyết định — đã chốt và chưa chốt

Danh sách các câu hỏi **xuyên sản phẩm** hoặc **có thể thay đổi thiết kế**.
Nếu một task chạm vào mục còn 🔴, agent phải **dừng và hỏi**, không được chọn giúp.
Mục 🟢 là đã chốt — giữ lại để không ai đề xuất lại.

Cập nhật: 10/09/2026

Ký hiệu: 🔴 chưa có dữ liệu · 🟡 có khuyến nghị, chờ duyệt · 🟢 đã chốt

---

## A. Phải đi đo trên máy thật, không suy luận được trên giấy

Nguồn: `notaryoffice/gioi-thieu-du-an.md` §7. Mỗi câu 1–2 ngày kiểm tra, mỗi câu
có thể thay đổi thiết kế `notaryoffice`.

| # | Câu hỏi | Trạng thái | Hệ quả |
|---|---|---|---|
| A1 | Đọc được nội dung tài liệu khi Word đang giữ file không? | 🔴 chưa đo | Nếu không: phải đổi cách đọc, chậm hơn, vẫn khả thi |
| A2 | Print Spooler có cho biết **số bản in** không? | 🟢 **KHÔNG** | Xem ràng buộc bên dưới |
| A3 | Ổ mạng chung (Z:) có phát sự kiện đổi file đầy đủ không? | 🔴 chưa đo | Nếu không: thêm job quét đối chiếu định kỳ → tăng khối lượng |
| A4 | 6 máy dùng tài khoản Windows **riêng** hay **chung**? | 🔴 chưa đi xem | Nếu chung: bỏ hẳn tính năng theo dõi bàn giao giữa chuyên viên |

**A2 đã chốt = Không.** Print Spooler không cung cấp số bản in. Ràng buộc thiết kế
kéo theo:

- Số bản in **phải suy ra từ số trang** trong event (tổng trang ÷ số trang tài
  liệu), và con số đó là **suy đoán, không phải sự thật**.
- Vì vậy **không được** dùng số bản in làm điều kiện cứng để phân biệt
  `DRAFT_PRINTED` vs `FINAL_PRINTED`. Phải dựa vào tín hiệu khác (thời điểm in so
  với lần sửa cuối, có/không sửa file sau khi in, số lần in).
- Nếu một tính năng chỉ chạy được khi biết chính xác số bản in → tính năng đó
  không khả thi, đừng thiết kế quanh nó.

**A4 vẫn là câu quan trọng nhất và không cần kỹ thuật để trả lời** — chỉ cần đi
xem 6 máy. Agent không được giả định là tài khoản riêng.

---

## B. Chủ dự án đã quyết định

| # | Câu hỏi | Trạng thái |
|---|---|---|
| B1 | Văn phòng có phần mềm quản lý hồ sơ đang dùng? Có đọc được dữ liệu ra? | 🟢 **Có phần mềm, NHƯNG không có API để đọc dữ liệu ra** |
| B2 | Phạm vi đọc Zalo | 🟢 **Làm ngay, không hoãn** — theo ranh giới bên dưới |
| B3 | Thông báo cho nhân viên + đưa vào nội quy lao động | 🟢 **Có**, phải xong **trước** khi triển khai |
| B4 | Chọn 2 chuyên viên cho giai đoạn thử nghiệm | 🟢 Chủ dự án tự chọn |

### B1 — vì sao `upload_lab` tồn tại

Văn phòng **đã có** phần mềm quản lý hồ sơ công chứng, nhưng nó **không có API để
lấy dữ liệu ra**. Đây chính là **lý do `upload_lab` ra đời**: không đọc được dữ
liệu từ phần mềm đó, nên phải đi đường khác — trích xuất từ chính các file Word
mà chuyên viên đã soạn.

Hệ quả cho agent:

- **Đóng phương án "đọc DB/API của phần mềm hiện có trước mọi thứ khác".** Không
  khả thi. Đừng đề xuất lại, đừng thiết kế tính năng dựa trên nó.
- Nguồn dữ liệu thật của hệ thống là: **file Word chuyên viên soạn**, **ảnh giấy
  tờ khách hàng**, và **dấu vết thao tác trên máy trạm** — không phải phần mềm cũ.
- Nếu sau này nhà cung cấp phần mềm cũ mở API, đó là thay đổi lớn → phải hỏi lại.

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

Ghi chú: mục này gộp cả phần Zalo của `notaryoffice` và Zalo Document Inbox của
`notary_v2` — cùng một ranh giới, cùng một tài khoản chung, cùng chạy trên server.

---

## C. Rủi ro lớn nhất — không phải rủi ro kỹ thuật

**Nhân viên bấm "Đúng" theo phản xạ.**

Nếu mỗi người phải xác nhận 20 thông báo/ngày, họ sẽ bấm Đúng hết mà không đọc.
Dữ liệu trông đẹp nhưng sai, và hệ thống "học" theo cái sai đó.

Biện pháp đã chốt 🟢 (`gioi-thieu-du-an.md` §7):
- Giới hạn **cứng** tối đa **3 thông báo/người/ngày**; phần còn lại gom vào một
  màn hình xem lại cuối ngày.
- Đo thời gian bấm; bấm dưới **1,5 giây** liên tục = dấu hiệu bấm không đọc.

Agent không được nới giới hạn này để "tăng độ phủ dữ liệu".

---

## D. Đã chốt — đừng đề xuất lại

| Phương án | Vì sao loại |
|---|---|
| Đọc API/DB của phần mềm quản lý hồ sơ hiện có | Không có API (B1) |
| Server-centric FileWatcher: 1 server tự watch hết ổ mạng | Nghẽn băng thông LAN, bỏ sót sự kiện trên ổ local (~20% file) |
| Full edge-processing: xử lý toàn bộ ngay trên máy con | Agent nặng, khó cập nhật logic trên 6 máy, ảnh hưởng máy nhân viên |
| Auto-link chặt: chỉ ghép khi điểm ≥ 90, dưới ngưỡng thì bỏ | Mất quá nhiều dữ liệu. Đã đổi sang **xếp hạng ứng viên** rồi hỏi người 1 lần (`session_summary.md`) |
| Dùng số bản in từ Print Spooler | Spooler không cung cấp (A2) |
| Đọc Zalo cá nhân của nhân viên | Ranh giới quyền riêng tư đã chốt (B2) |
| Local OCR trong `notary_v2` | Đang **parked**, cần redesign được duyệt riêng mới mở lại |
| Thêm OCR provider thứ hai song song với Qwen | Xem [`TECH_STACK.md`](./TECH_STACK.md) mục 2 |

Chi tiết ba phương án kiến trúc bị loại: `notaryoffice/intent_v2.md`.

---

## E. Về việc gộp hệ thống — không còn là câu hỏi mở

Định hướng đã rõ: **gộp thành một hệ thống thống nhất, dùng chung database.** Ba
repo là các công cụ xử lý dữ liệu theo mục đích khác nhau trong cùng hệ thống đó.

Giai đoạn hiện tại: **làm tốt từng phần, chưa vội gộp.** Xem
[`VISION.md`](./VISION.md) mục 4 và [`TECH_STACK.md`](./TECH_STACK.md) mục 3 cho
các ràng buộc thiết kế phải tuân theo từ bây giờ để lúc gộp không xung đột.

Điều này **không** có nghĩa agent được tự ý nối hai repo lại. Nối = tích hợp =
phải có contract được duyệt trước (`contracts/README.md`).
