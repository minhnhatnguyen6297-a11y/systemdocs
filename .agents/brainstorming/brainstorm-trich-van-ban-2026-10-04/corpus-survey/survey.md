# Khảo sát corpus văn bản mẫu

Bản đi cùng commit bàn giao là [inventory-summary.json](inventory-summary.json): đường dẫn, mã băm, kích thước, trạng thái đọc và số đoạn/bảng từ khảo sát ban đầu. `inventory.json` đầy đủ với vị trí/nhãn chi tiết chỉ giữ cục bộ; không đóng gói toàn bộ dữ liệu trung gian. Bản này không thay bộ đáp án từng trường đã được duyệt.

## Phạm vi và cách đọc

Khảo sát 571 tệp; Word COM mở .doc, .docx, .docm ở chế độ chỉ đọc, tắt macro và không lưu. Ghi lại đoạn, bảng, tiêu đề, nhãn an toàn, dấu hiệu vai trò và vị trí đoạn. Ảnh/PDF/Excel/DB/tệp hỗ trợ chỉ kiểm kê định dạng và SHA-256, không đọc nội dung/OCR. Không dựa vào tên tệp hay thư mục để gán loại.

## Số liệu

- Tệp vật lý: 571; hash SHA-256 duy nhất: 523; nhóm trùng hash: 34.
- Word theo phần mở rộng: 517; dấu khóa/tạm ~$: 44 (không mở); Word không mang dấu khóa đã mở và đọc: 473; lỗi đọc nguồn: 0; chưa khảo sát nội dung Word: 0.
- Phần mở rộng: .db 4, .doc 140, .docm 4, .docx 373, .ini 1, .jpg 22, .pdf 15, .tmp 7, .xlsb 4, .xlsx 1.
- Word có dấu hiệu tiêu đề văn bản: 443 tệp; có từ hai dấu hiệu trở lên: 340 tệp; tổng dấu hiệu: 1274. Đây không phải số văn bản đã xác nhận: vùng chứng nhận có thể lặp, và một tệp có thể ghép nhiều biểu mẫu/phụ lục.
- Nhãn thư mục dossier: 133 giá trị; đó là nhãn thư mục, không phải loại văn bản.

## Nhóm loại theo dấu hiệu tiêu đề trong nội dung

Đếm tệp và hash duy nhất có ít nhất một heading khớp từ khóa. Nhóm có thể chồng lấp; tiêu đề chứng nhận lặp không được tính thành văn bản riêng. Đây là dấu hiệu mô tả corpus, không phải loại đã xác minh.

| Dấu hiệu loại | Tệp | Hash Word duy nhất |
|---|---:|---:|
| Chuyển nhượng nhà đất | 8 | 8 |
| Tặng cho nhà đất | 9 | 9 |
| Thế chấp nhà đất | 97 | 91 |
| Ủy quyền | 135 | 119 |
| Thừa kế - di chúc | 4 | 4 |
| Thừa kế - phân chia di sản | 18 | 17 |
| Thừa kế - từ chối di sản | 24 | 24 |
| Đơn/phiếu/tờ khai | 70 | 65 |
| Biên bản | 20 | 20 |
| Cam kết tài sản riêng | 24 | 24 |
| Giao dịch nhà đất khác | 10 | 10 |
| Xe/tài sản ngoài nhà đất | 6 | 6 |

Tiêu đề cụ thể gồm hợp đồng chuyển nhượng/tặng cho/thế chấp quyền sử dụng đất; hợp đồng ủy quyền và ủy quyền xử lý tài sản bảo đảm; di chúc, phân chia hoặc từ chối nhận di sản; đơn đăng ký biến động, phiếu yêu cầu đăng ký và tờ khai thuế/lệ phí. “Giấy”, “Văn bản”, “Chứng nhận” thường là nhãn chung, giấy tờ được dẫn chiếu hoặc vùng chứng nhận; không đủ để suy ra văn bản độc lập.

## Cấu trúc và dấu hiệu quan sát

- Word đã đọc có 715 bảng, 1745 hàng bảng. Số đoạn và vị trí heading/nhãn được lưu từng tệp trong inventory.json. Tệp có thể ghép nhiều đơn/phiếu/tờ khai với hợp đồng chính; ranh giới đôi khi chưa rõ.
- Dấu hiệu tài sản, không phải phân loại pháp lý: đất: 361 tệp, 4580 vị trí; nhà: 165 tệp, 719 vị trí; xe: 8 tệp, 130 vị trí; tàu/thuyền: 4 tệp, 30 vị trí. Nhà/đất là nhóm ưu tiên; xe/tàu được tách là quan sát ngoài phạm vi giai đoạn.
- Nhãn trường lặp nhiều (số tệp; tên đơn vị đã ẩn): Căn cước công dân số (249); Tại Văn phòng Công chứng [đơn vị], địa chỉ (231); CHỨNG NHẬN (224); Số công chứng (185); Thường trú tại (167); Số chứng thực (96); Thời gian ủy quyền (89); Địa chỉ (89); Các ông/bà có tên sau đây (86); Căn cước số (81).

Mẫu thể hiện bên chuyển nhượng/bên nhận, bên tặng cho/bên nhận tặng cho, người ủy quyền/người được ủy quyền và người đại diện; hồ sơ thừa kế có người để lại di sản/người thừa kế. Người làm chứng/công chứng viên thường ở phần ký/chứng nhận. Trong ủy quyền ký hợp đồng, A (ủy quyền) và B (ký thay) là hai người cần phân biệt; người làm chứng/công chứng viên không phải nhóm người giao dịch trích xuất.
Dấu căn cước/CCCD và CMND có thể cùng xuất hiện. Khi có nhãn rõ, CMND cũ, ngày cấp, nơi cấp là thông tin riêng với CCCD hiện tại; có mẫu để trống, không suy từ thứ tự chữ. Theo quyết định nghiệp vụ đã cung cấp, chỉ dùng vùng dữ liệu chính, không dùng vùng ký/chứng nhận để tìm bù, xác nhận hay đối chiếu. Người thiếu thông tin vẫn có thể là dòng riêng để người dùng bổ sung/xóa ở Stage.

Các cấu trúc có thể lặp: thông tin các bên/giấy tờ, thông tin nhà đất, điều khoản giao dịch, chứng nhận cuối văn bản. Di chúc, thừa kế, ủy quyền và biểu mẫu đăng ký có trình tự/vai trò khác nhau. Đây chỉ là dấu hiệu, chưa kết luận ranh giới hay cách dùng chung.

## Giới hạn

Đọc thành công chỉ nghĩa là lấy được chữ/cấu trúc bằng đường đọc đã thử, không chứng minh mọi trường đúng. Ba tệp đại diện (.docx, .doc, tệp có bảng) đã đi hết mở–đọc–chuẩn hóa–ghi JSON–đọc lại. Không có đáp án gán nhãn nên không tính phần trăm chính xác. Heading có thể thiếu hoặc lặp; số văn bản bên trong từng tệp chưa được xác minh độc lập. Inventory lưu đường dẫn tương đối, phần mở rộng, hash, trạng thái, số đoạn/bảng, vị trí heading/nhãn và vùng mơ hồ; giá trị định danh trong heading/nhãn đã được lược.
