# 12 report còn mở — không đóng theo bản sửa relErrText

**Trạng thái:** chờ mô tả triệu chứng. JSON không lưu người tạo; nhóm này chỉ được suy là thao tác tay vì không khớp mẫu E2E.

Kiểm kê đúng: **37 JSON = 18 logo + 7 nút fixture + 12 ngoài E2E**. Có 32 PNG; 5 thiếu ảnh thuộc 18 logo. Tổng 25 report khớp E2E đã gồm 5 thiếu ảnh.

Cả 12 bên dưới mất lời mô tả tự gõ. Nguồn công cụ chỉ giữ ba câu mẫu, không có cách khôi phục lời gốc từ file hiện tại. Không tự bỏ bộ lọc riêng tư của spike trong task sửa sơ đồ.

| ID đầy đủ | Vùng đã chọn / suy từ code | Câu cần người dùng bổ sung |
|---|---|---|
| 534545cf-f020-4e22-8e03-362294f72508 | Toàn vùng nội dung #view 1204×755; bị bỏ sót trong bản điều tra cũ | Toàn màn đó gặp vấn đề gì? |
| 377d8486-e885-4a21-8e84-497241546eaa | Khối div 1100×197 tại (82,276) | Khối này lệch, quá cao, hay thiếu nội dung? |
| bb496551-82b6-4f72-bd80-77df2e396e2f | Nút thứ 7 trên thanh hành động | Bạn bấm nút nào; kết quả thực tế khác mong muốn thế nào? |
| 0d1b1ff1-73ce-4e8b-a6bf-2c695f06dd3f | Khối con bảng hàng 6, cột 2; có khả năng gợi ý địa chỉ tài sản | Phần gợi ý địa chỉ hiện hoặc hoạt động sai thế nào? |
| 60e02a79-727d-4de3-be7f-488b3f1a39ee | Ô bảng hàng 6, cột 2, cao 213 px; có khả năng Địa chỉ tài sản | Ô bị kéo cao hay danh sách kết quả có vấn đề? |
| 2f352897-ab9b-4f11-84e4-a44c43145bf0 | Input bảng hàng 7, cột 2; có khả năng Loại sổ | Sai giá trị, không nhập được, hay sai bố cục? |
| b5999b39-dce5-48dc-954a-66d231cce6ee | Khối 388×38 dưới vùng tài sản; chưa định danh chắc | Nội dung hoặc thao tác nào trong khối đó bị sai? |
| 5db58074-cf8b-4a67-ab5a-09c0dd449a94 | Ô Người hàng đầu, cột 3; có khả năng Giới tính | Sai lựa chọn hay sai kích thước? |
| 643496a0-c4a4-4e5a-ab2f-bbbfa39d438a | Span trong gợi ý Địa chỉ Người | Dòng đó hiện chữ gì và sai ở đâu? |
| e3bba3ef-0f1f-4730-a505-cf0d282b75b1 | Input nơi cấp giấy tờ/giấy khai tử trong cột Địa chỉ Người | Là nơi cấp trên giấy nào; bạn mong hiện/tra thế nào? |
| aaf29f16-68b4-4a92-b15c-b811043d9c80 | Khối card sơ đồ 144×89 | Thẻ sai nhánh, bị che, hay không bấm được? |
| 6714de6f-0049-4b4c-8d0d-2a2b179f15d9 | Dải đầu workspace 1827×44; chưa phân biệt banner mock/notice/error | Nội dung dải đó là gì; bạn muốn nó đổi thế nào? |

## Quy tắc tiếp tục điều tra

1. Có mô tả thì ghi nguyên ý người dùng cùng ID vào hồ sơ điều tra mới; không sửa JSON gốc.
2. Tái hiện trên code sau bản sửa relErrText. Ghi thao tác, dữ liệu giả tối thiểu, kết quả mong muốn và kết quả thực tế.
3. Console của spike là bộ đệm chung không có timestamp. Bốn report cuối cùng có dòng 312 không chứng minh cùng nguyên nhân hay sự kiện mới.
4. Nếu triệu chứng hết sau sửa thì ghi bằng chứng tái hiện trước/sau đúng triệu chứng; mới đề xuất đóng ID đó. Nếu còn lỗi, lập task riêng có spec/AC trước khi đổi hành vi.
5. Ảnh chỉ có khung trống, không chứng minh lỗi chữ, màu hay nội dung. Source candidate là gợi ý từ cấu trúc, không phải mapping component chính xác.
6. Nguồn giờ của bản cũ là mtime UTC: 16:38–16:51 ngày 08/10 = 23:38–23:51 Việt Nam; 00:51–00:54 ngày 09/10 = 07:51–07:54 Việt Nam. Đây là thời gian sửa file, không phải timestamp ứng dụng.

## Nơi đọc file gốc trên máy hiện tại

- JSON/PNG: `D:/systemdocs-spike-visual-bug/_bmad-output/tmp/visual-bug-spike/custom/reports/`.
- Bảng 37 file: `D:/systemdocs/_bmad-output/tmp/review-37-reports-20261009/inventory.json`.
- Report HTML có ảnh theo từng ID: `D:/systemdocs/_bmad-output/tmp/review-37-reports-20261009/review.html`.
- Điều tra cũ: `C:/Users/MINH/.opencode/plan/bug-investigation-20261009.html`.

Các đường dẫn tạm không nằm trong git. Worker ở worktree khác vẫn đọc được từ đường dẫn tuyệt đối trên cùng máy. Nếu nguồn mất, báo thiếu nguồn; không bịa nội dung hoặc tự tái tạo lịch sử report.
