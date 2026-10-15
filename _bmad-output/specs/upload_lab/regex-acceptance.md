# Ranh giới chấp nhận kết quả regex

**Trạng thái:** Active. **Nguồn:** Owner trong chat TASK-10.3, 08/10/2026.

**Quyết định:** sửa lỗi máy đọc sai cấu trúc đã hỗ trợ; không theo đuổi đọc đúng mọi văn bản. Lỗi gõ trong nguồn được giữ để người dùng sửa. Mẫu ngoài phạm vi cần bằng chứng và được xem xét riêng, không tự coi là đã hỗ trợ.
**Tại sao:** test xanh hoặc ít cờ không chứng minh dữ liệu đúng; cũng không nên đoán sửa chữ người dùng để tăng số đạt.

## 1. Phân loại trước khi sửa

| Loại | Cách xử lý | Có tính là máy đọc đúng? |
|---|---|---|
| Đáp án thiếu/sai, bộ chấm bỏ qua trường hoặc dùng output cũ | Sửa bộ chấm; sửa đáp án bằng bằng chứng nguồn, lưu lớp đính chính riêng | Chỉ các trường đã kiểm lại |
| Nhãn/vùng rõ thuộc loại đã hỗ trợ nhưng mất người, đất hoặc lấy nhầm trường | Sửa engine chung, kiểm cả đầu vào và đầu ra thật | Sau khi so đúng trường và số bản ghi |
| Nguồn dính chữ, sai chính tả hoặc giá trị không hợp lệ | Giữ phần regex lấy được; người dùng kiểm/sửa tại các ô Stage hiện có | Ghi cần kiểm nguồn, không biến thành đạt |
| Không đủ ranh nhóm/nhãn hoặc bố cục khác ngoài phạm vi công bố | Giữ nguồn, ghi lý do; đề xuất mẫu/phiên bản riêng nếu cần | Chưa hỗ trợ, không tính đạt |
| Quyết định nghiệp vụ chưa chốt | Giữ Pending, không chọn nghĩa hộ owner | Không |

Không đặt tỷ lệ 90/95% hay mục tiêu hoàn hảo. Mỗi lượt báo rõ số file, số bản ghi, trường đã kiểm, lỗi máy, nguồn cần sửa, ngoài phạm vi và Pending. Kết quả đúng một phần phải gọi là **khớp các trường đã kiểm**, không gọi cả file đạt.

## 2. Đợt 50 file Hưng 3930–3979

E1/E2/E3 là nhãn đại diện rõ, kể cả thiếu dấu hai chấm, chức danh sau dấu gạch hoặc ô TAB. Giữ đúng bên A/B bất kể thứ tự; không gán địa chỉ người thế chấp cho đại diện ngân hàng.

E5 là các mục GCN đánh số rõ: giữ mỗi mô tả tài sản riêng dù không có số thửa; không suy số lượng thửa pháp lý. E6 giữ địa chỉ đứng trước số thửa trong cùng vùng. E7 mở đúng vùng tài sản của cam kết hai dòng; parser đất hiện có đọc được dòng gạch. Không đọc toàn văn rồi mượn CCCD/địa chỉ văn phòng làm dữ liệu đất. Đây là lỗi engine, không có căn cứ đẩy sang mẫu ngoài phạm vi.

E4 có token dính `036064005865do` ngay trong byte Word: lỗi nguồn có thể kiểm tay. Nhưng lấy cơ quan cấp GCN để điền nơi cấp CCCD vẫn là lỗi engine phải chặn. Thiếu bằng chứng thì giữ trống/phần đọc được; không đoán hoặc sửa “Bộ Coongan” thành “Bộ Công an”.

Đáp án 3970 thiếu đuôi `, tỉnh Ninh Bình`; đính chính phải dựa trên dòng nguồn, giữ nguyên bộ đáp án TASK-10.2 để truy lại. Batch này chưa kiểm các mẫu F04/F05; phần phân biệt thửa/cấu trúc đầu ra đã được owner làm rõ 15/10/2026 tại regex-fields, chưa duyệt lại đáp án các mẫu mâu thuẫn.

## 3. Kết quả cho người dùng sửa

Owner chốt: **không thêm chức năng hoặc luật sửa lỗi nguồn**. Regex lấy được gì thì điền vào kết quả tương ứng trong Stage hiện có. Số giấy tờ/nơi cấp là chữ tự do; giữ chữ nguồn, không vứt giá trị chỉ vì sai chính tả hoặc khác mẫu. Chỉ gắn cảnh báo khi có căn cứ xác định trường cần kiểm; không hứa phát hiện mọi lỗi.

Không thêm ô nguyên văn, bảng hay nút mới; không dán dữ liệu vào một trường khác nghĩa. Bằng chứng gốc vẫn thuộc nguồn nhập. Nhiều giá trị chưa chọn hoặc ngày/diện tích không hợp lệ vẫn theo quy tắc kiểm hiện hành trước khi nhận/lưu, không lấy một giá trị tùy ý.

## 4. Bộ chấm

- `null`/thiếu là chưa trả lời; `""`/`[]` là đã kiểm và cần rỗng. Giữ riêng hai nghĩa.
- Kiểm tên có dấu, cờ năm sinh cả true/false, từng trường người chết và chi tiết đất đã trả lời; so mỗi bản ghi một lần, không dùng một thửa để khớp hai đáp án.
- Lỗi extract không được thành đạt. Báo số trường đã kiểm/chưa kiểm; ca chỉ có một trường không chứng minh cả file đúng.
- Output phải gắn hash nguồn, engine, validator, bộ chấm, đáp án và lớp đính chính. Đổi bất kỳ phần nào thì chạy mới; không gắn tên engine mới cho output cũ.
- Giữ 50 đường dẫn trong mẫu số kể cả bản sao giống byte. Đáp án đọc từ nguồn, không sửa để khớp máy.

Luật trường ở [regex-fields.md](regex-fields.md); đáp án và Pending ở [regex-expected-results.md](regex-expected-results.md). Luồng Stage ở [nhập DOCX](../notary_v2/input/docx-import.md).
