# Native OCR: GCN và trường riêng giấy chết — owner 30/10/2026

Nguồn: yêu cầu trực tiếp trong phiên, nhánh `agent/input-ocr/gcn-death-fields`.

- Đo trước rồi sửa trên dữ liệu tổng hợp; giữ ca cũ, thêm nhiều layout GCN và giấy chết. Không đọc hồ sơ thật, không gọi OCR cloud, không commit/stash.
- Phạm vi thay đổi là parser native OCR và phép đo, không đổi schema/contract hoặc luồng bóc Word. Chuẩn ngày OCR DD/MM/YYYY và diện tích chuỗi dot-decimal giữ nguyên.
- Giấy chết có `so_trich_luc_khai_tu`, `noi_cap_khai_tu`, `ngay_ky`, `noi_chet`, `noi_thuong_tru_cuoi` riêng. Số giấy chết không còn đè `so_giay_to`; số này chỉ là CCCD/định danh in đúng vùng người chết hoặc rỗng. `noi_cap/ngay_cap` Người rỗng, loại giấy giữ canonical hiện có.
- Giữ ngoại lệ địa chỉ được user cho phép: `dia_chi` theo chính sách có sẵn khi một nguồn địa chỉ rõ, khác nhau thì trống; luôn giữ riêng hai trường địa điểm mới. Không tự chọn giữa hai giá trị mâu thuẫn.
- Không đổi tên key cũ, không thêm alias. Năm trường OCR chưa có mapping downstream được duyệt; báo rõ hạn chế thay vì sửa contracts hoặc nhét sang ghi chú.
- Không chọn thêm dependency hoặc engine mới. Đã tìm pattern GitHub: https://github.com/thehmfpk/Certificate-OCR-Based-Document-Processing-System và https://github.com/Tuprott991/Vietnamese-OCR-with-Correction . Không đưa code/dependency từ các repo đó vào; tái dùng deterministic helpers trong repo.

Quy tắc đang áp dụng: `../specs/shared/extraction-rules.md` §2.3. Hành vi Word/DB theo quyết định 21/10 giữ nguyên ngoài ngoại lệ native OCR này.
