# Bạn đã đánh dấu chỗ nào trong app?

**Câu trả lời quan trọng:** công cụ chỉ còn giữ vị trí bạn chọn. Nó đã bỏ lời bạn gõ và chữ trên ảnh. Vì vậy có thể tìm lại tên ô/nút, nhưng không thể khôi phục chính xác câu “ô này bị lỗi gì” của bạn.

Bản mô tả trước dùng số hàng/cột và tên file nên khó nhận ra chức năng. Bảng này dùng tên trong giao diện. Số R01–R12 chỉ để trao đổi dễ hơn, theo thứ tự file được tạo.

## Lỗi đã kiểm chứng: chức năng sơ đồ thừa kế báo lỗi không đúng

**Ở đâu:** phần Sơ đồ thừa kế, khi sắp xếp người vào sơ đồ, bấm **Xem cách tính** hoặc **Lưu sơ đồ**.

**Lỗi là gì:** nếu việc kiểm tra/lưu sơ đồ bị từ chối, app có thể phát sinh lỗi kỹ thuật khi định hiện lời giải thích. Người dùng không nhận được thông báo nổi đúng; nếu có danh sách lỗi dưới sơ đồ thì việc vẽ lại màn hình cũng có thể hỏng.

**Ví dụ đã thử bằng dữ liệu giả:** app phát hiện dữ liệu người/tài sản chưa hợp lệ. Đáng lẽ thông báo “Dữ liệu Stage chưa hợp lệ — Sửa các ô/dòng đánh dấu đỏ rồi lưu lại”, nhưng phần hiển thị thông báo lại bị lỗi.

Đây là lỗi tìm được khi điều tra. Chưa biết nó có phải điều bạn muốn phản ánh trong từng report hay không. Bốn report gần nhất có cùng dấu lỗi, nhưng công cụ có thể chép lại lỗi của thao tác trước. Không được coi lỗi này là lời giải thích cho mọi ô bạn đã chọn.

## 12 vị trí bạn đã đánh dấu

Trong tất cả các dòng dưới đây, **lời mô tả vấn đề của bạn không còn trong file**. Tên vị trí không đồng nghĩa với tên bug đã xác nhận.

| Số | Chức năng | Chỗ được đánh dấu | Điều còn xác định được |
|---|---|---|---|
| R01 | Màn hình notary_v2 | Toàn vùng nội dung bên phải thanh menu | Bạn chọn cả màn hình, chưa chỉ được một ô/nút cụ thể. |
| R02 | Cửa sổ nổi đang mở trên màn hình Soạn hồ sơ | Phần nội dung giữa cửa sổ | Đường chọn thuộc thân một popup. Có thể là popup **Loại đất**, nơi nhập Loại đất / Diện tích / Thời hạn; file không giữ tiêu đề để xác nhận chắc tên popup. |
| R03 | Lưu hồ sơ | Nút **Lưu hồ sơ** ở góc trên bên phải | Đây là nút lưu toàn hồ sơ, khác nút Lưu sơ đồ. Ở hồ sơ đã lưu, nút cùng vị trí có tên Cập nhật. |
| R04 | Tra cứu địa chỉ của tài sản | Dòng “Tìm thấy … dòng — Copy dòng phù hợp rồi dán vào ô” dưới ô Địa chỉ | Bạn chọn phần lời hướng dẫn sau khi có kết quả tra cứu. Số dòng và kết quả địa chỉ gốc đã bị bỏ. |
| R05 | Địa chỉ của tài sản | Cả ô Địa chỉ, gồm ô nhập và phần kết quả tra cứu phía dưới | Bạn chọn toàn khối địa chỉ; file không nói vì khối quá cao, sai nội dung hay thao tác có vấn đề. |
| R06 | Thông tin giấy chứng nhận của tài sản | Ô nhập **Loại sổ** | Đây là ô Loại sổ, không phải ô Loại đất. Giá trị bạn nhập đã bị bỏ. |
| R07 | Thông tin hồ sơ | Dòng **Người nhận ủy quyền** bên dưới bảng Tài sản | Vùng này có ô chọn/nhập tên và nút + Danh bạ. Bạn chọn cả dòng, chưa biết riêng ô hay nút bị gì. |
| R08 | Thông tin người | Ô **Giới tính** của người đầu tiên | Ô chọn trống / Nam / Nữ. File không nói sai lựa chọn, sai chiều rộng hay không chọn được. |
| R09 | Tra cứu địa chỉ của người | Dòng thông báo dưới ô Địa chỉ của người đầu tiên | Đây là lời phản hồi khi tra địa chỉ, có thể là đang tra / thất bại / nhiều kết quả / trạng thái khác. Không còn chữ thật để biết là dòng nào. |
| R10 | Nơi cấp giấy tờ của người | Ô **Nơi cấp giấy tờ / Nơi cấp giấy khai tử**, nằm dưới ô Địa chỉ | Đây là ô nhập cơ quan cấp giấy, không phải ô địa chỉ chính. Tên cụ thể phụ thuộc người đó sống hay đã mất; dữ liệu gốc không được giữ. |
| R11 | Sơ đồ thừa kế | Thẻ của một người trong sơ đồ | Thẻ có tên/năm sinh–mất và các lựa chọn Chủ / Nhận. File không giữ tên người hay lời phản ánh, nên chưa biết thẻ sai quan hệ, sai hiển thị hay không bấm được. |
| R12 | Thông báo trên màn hình Soạn hồ sơ | Dải thông báo nằm phía trên hai bảng Tài sản / Người | Bạn chọn cả dải. Nó có thể là thông báo dữ liệu lỗi, thông báo thao tác hoặc chế độ thử; không còn nội dung chữ để phân biệt. |

Các tên R03–R10 đã được đối chiếu với cây giao diện dựng từ source hiện tại bằng dữ liệu giả. Điều đó giúp xác định ô/nút. Nó không khôi phục dữ liệu và lời mô tả gốc. Riêng R02, R11, R12 phải giữ mức khái quát như bảng, không lấy tiêu đề/người/thông báo của dữ liệu giả làm nội dung gốc.

## Những vấn đề chúng ta chưa biết

Không có chứng cứ để nói bạn đã báo “ô bị tràn chữ”, “nút không bấm được”, “tra ra sai địa chỉ” hoặc “quan hệ thừa kế tính sai”. Những câu đó chỉ là các khả năng để bạn nhớ lại, chưa phải kết luận.

Bạn có thể bổ sung bằng tên chức năng, không cần nhớ mã file. Ví dụ mẫu, **không phải lời report gốc**: “Loại sổ: ô nhập quá hẹp”, hoặc “Người nhận ủy quyền: bấm + Danh bạ không thấy kết quả”. Khi bạn mô tả lại, ghi vào đúng số R rồi mới điều tra bug tương ứng.

## 25 file còn lại

Chúng khớp thao tác tự kiểm thử: 18 lần chọn logo G1 và 7 lần chọn nút giả do script tạo. Năm file thiếu ảnh nằm trong nhóm logo. Các câu như “button overlaps…” ở đây là câu mẫu mà script dùng, không được dùng để kết luận bạn phản ánh nút chồng nhau.

## Đối chiếu số R với file gốc

| Số | ID gốc | Mốc sửa file, giờ Việt Nam |
|---|---|---|
| R01 | 534545cf-f020-4e22-8e03-362294f72508 | 08/10 23:07 |
| R02 | 377d8486-e885-4a21-8e84-497241546eaa | 08/10 23:38 |
| R03 | bb496551-82b6-4f72-bd80-77df2e396e2f | 08/10 23:39 |
| R04 | 0d1b1ff1-73ce-4e8b-a6bf-2c695f06dd3f | 08/10 23:39 |
| R05 | 60e02a79-727d-4de3-be7f-488b3f1a39ee | 08/10 23:41 |
| R06 | 2f352897-ab9b-4f11-84e4-a44c43145bf0 | 08/10 23:44 |
| R07 | b5999b39-dce5-48dc-954a-66d231cce6ee | 08/10 23:47 |
| R08 | 5db58074-cf8b-4a67-ab5a-09c0dd449a94 | 08/10 23:51 |
| R09 | 643496a0-c4a4-4e5a-ab2f-bbbfa39d438a | 09/10 07:51 |
| R10 | e3bba3ef-0f1f-4730-a505-cf0d282b75b1 | 09/10 07:52 |
| R11 | aaf29f16-68b4-4a92-b15c-b811043d9c80 | 09/10 07:53 |
| R12 | 6714de6f-0049-4b4c-8d0d-2a2b179f15d9 | 09/10 07:54 |

Giờ là mốc sửa file để hỗ trợ nhớ lại, không phải thời điểm app ghi thao tác. JSON/PNG gốc nằm ở `D:/systemdocs-spike-visual-bug/_bmad-output/tmp/visual-bug-spike/custom/reports/`.

## Bằng chứng giới hạn của công cụ

`policy.cjs` chỉ giữ nguyên ba chuỗi note mẫu; mọi câu tự gõ được thay bằng `[note omitted: synthetic vocabulary only]`. Ảnh chỉ lưu khung bố cục, không giữ chữ và màu gốc. Vì vậy phần mất thông tin đến từ cách công cụ lưu report, không chỉ do cách viết lại báo cáo điều tra.
