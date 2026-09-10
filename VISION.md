# Tầm nhìn hệ thống

## 1. Bài toán

Một văn phòng công chứng có ba nhóm việc tốn người nhất, và cả ba đều là việc
gõ lại dữ liệu đã tồn tại ở đâu đó:

1. **Soạn thảo hồ sơ mới** — chuyên viên gõ lại thông tin từ CCCD, sổ đỏ, giấy
   khai tử vào mẫu Word, mỗi hồ sơ mỗi lần.
2. **Số hóa hồ sơ giấy cũ** — hàng nghìn file Word đã lưu trên ổ đĩa phải được
   đọc lại bằng mắt để nhập lên web cơ sở dữ liệu công chứng của tỉnh.
3. **Biết hồ sơ đang ở đâu** — mỗi chuyên viên giữ 30–70 hồ sơ; không ai giữ
   được toàn bộ tình trạng trong đầu và không ai có thời gian ghi chép.

Ba bài toán này khác nhau về bản chất, nên **hiện tại** được làm thành ba công cụ
riêng. Đích đến là **một hệ thống thống nhất dùng chung database**, trong đó ba
công cụ này là ba đường xử lý dữ liệu cho ba mục đích khác nhau. Xem mục 4.

## 2. Nguyên tắc chung xuyên suốt

Ba công cụ khác nhau về code nhưng cùng một triết lý:

**Không bắt người dùng nhập lại dữ liệu đã tồn tại.**
Dữ liệu đã nằm trong ảnh giấy tờ, trong file Word cũ, trong dấu vết thao tác
hằng ngày. Việc của phần mềm là đọc ra, không phải mở form cho người gõ.

**Máy đề xuất, người xác nhận.**
Không công cụ nào được tự ghi nhận kết quả suy đoán là sự thật. OCR ra dữ liệu
thì người dùng soát trước khi dùng; ghép dấu vết thành hồ sơ thì gắn nhãn
"nháp/ứng viên" cho tới khi có người bấm xác nhận. Trong nghề công chứng, một
lần gán sai gây mất lòng tin nhiều hơn hai mươi lần gán đúng mang lại.

**Tất định trước, AI sau, người cuối.**
Regex và rule xử lý phần lớn khối lượng, chạy cục bộ, rẻ và giải thích được.
LLM chỉ vào các ca mơ hồ. Người chỉ được hỏi khi độ tin cậy thấp.

**Không ép đổi thói quen làm việc.**
Chuyên viên vẫn soạn Word, vẫn in, vẫn lưu vào ổ chung. Phần mềm thích ứng với
hành vi thật, không yêu cầu học quy trình mới.

**Dữ liệu ở lại văn phòng.**
Mặc định chạy trong LAN. Khi phải gọi dịch vụ ngoài (Cloud OCR), đó là quyết
định có chủ ý ở một điểm cụ thể, không phải trạng thái mặc định của hệ thống.

## 3. Ba công cụ nói về cùng một thứ

Cả ba đều nói về **hồ sơ (Case)** — chỉ khác thời điểm trong vòng đời của nó:

- `notary_v2` sinh ra hồ sơ mới và tài liệu của nó.
- `notaryoffice` theo dõi hồ sơ đang chạy đi đâu, ai đang giữ, đang chờ gì.
- `upload_lab` đưa hồ sơ đã hoàn tất lên hệ thống nhà nước, và trên đường đó biến
  kho Word cũ thành dữ liệu có cấu trúc.

**đang soạn → đang chạy → đã xong và lưu trữ.**

Vì cùng nói về một thực thể, điều kiện tiên quyết để gộp được là
**định danh hồ sơ giống nhau ở cả ba** (CCCD, số GCN, thửa/tờ, số công chứng). Nếu
ba công cụ cùng nhận ra "đây là hồ sơ bà Gái, thửa 125", việc nối lại là chuyện kỹ
thuật nhỏ. Nếu không, không có tích hợp nào cứu được. Chuẩn ở
[`contracts/entities.md`](./contracts/entities.md).

## 4. Lộ trình: làm tốt từng phần trước, gộp sau

**Đích đến:** một hệ thống phần mềm thống nhất, **dùng chung một database**. Ba
repo trở thành các công cụ xử lý dữ liệu theo mục đích riêng trong hệ thống đó.

**Giai đoạn hiện tại:** tập trung làm tốt **từng phần**, chưa vội kết hợp. Mỗi
repo còn đang tự chứng minh giá trị của nó; gộp sớm sẽ khóa cả ba vào một thiết kế
chưa ai kiểm chứng.

**Việc phải làm ngay từ bây giờ** không phải là gộp, mà là **không để chúng phân
kỳ** — để lúc gộp không phải viết lại:

| Không được phân kỳ | Nơi ghi chuẩn |
|---|---|
| Cách chuẩn hóa khóa định danh (CCCD, GCN, thửa/tờ, số công chứng) | [`contracts/entities.md`](./contracts/entities.md) |
| Lựa chọn công nghệ cho cùng một việc (OCR, đọc Word, DB, backend…) | [`TECH_STACK.md`](./TECH_STACK.md) |
| Tên trường cho cùng một dữ liệu, kiểu ngày/số, cách sinh ID | [`TECH_STACK.md`](./TECH_STACK.md) mục 3 |

Ví dụ cụ thể phải tránh: `notary_v2` đang OCR bằng **API Qwen**. Nếu một dự án
khác trong hệ thống lại chọn một công nghệ OCR khác vì "quen hơn", lúc gộp sẽ có
hai đường OCR cho cùng một việc, hai định dạng kết quả, hai chỗ phải bảo trì. Đó
là loại xung đột file `TECH_STACK.md` tồn tại để ngăn.

**Vì vậy: agent của bất kỳ repo nào phải đọc `systemdocs` TRƯỚC KHI ra quyết định
kiến trúc hoặc chọn công nghệ mới.** Đây là nơi lưu tài liệu SOT.

Gộp thì gộp, nhưng **không tự ý gộp**: nối hai repo là tích hợp, phải có contract
được duyệt trước ([`contracts/README.md`](./contracts/README.md)).

## 5. Điều cố tình KHÔNG làm

- **Không tự động hóa phán quyết pháp lý.** Phần mềm chuẩn bị dữ liệu và tài liệu;
  công chứng viên chịu trách nhiệm nội dung.
- **Không giám sát nhân viên.** `notaryoffice` quan tâm đến hồ sơ, không quan tâm
  đến người: không quay màn hình, không keylogger, không dùng để chấm công.
- **Không xây một "core library" dùng chung trước khi có hai domain thật chứng
  minh được contract.** Nguyên tắc này đã chốt trong `notary_v2`
  (`docs/platform/case-workspace/README.md`) và áp dụng cho cả hệ thống. Lưu ý:
  điều này **không** mâu thuẫn với việc gộp hệ thống — gộp là thống nhất **dữ
  liệu và định nghĩa**, không nhất thiết là gộp **code**.
- **Không nối hai repo trước khi có contract được duyệt.**

## 6. Ràng buộc pháp lý cần nhớ

Cả ba sản phẩm đều xử lý CCCD và thông tin tài sản của khách hàng → thuộc phạm
vi **Nghị định 13/2023** về bảo vệ dữ liệu cá nhân. Riêng `notaryoffice` còn
ghi nhận hoạt động của nhân viên → phải thông báo và đưa vào nội quy lao động
trước khi triển khai, không phải sau.
