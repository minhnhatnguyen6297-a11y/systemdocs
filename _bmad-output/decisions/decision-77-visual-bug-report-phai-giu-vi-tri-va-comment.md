# Quyết định: report lỗi phải giữ vị trí và comment người dùng

**Trạng thái:** Owner đã chốt yêu cầu tối thiểu ngày 09/10/2026. Code chưa sửa.

## LÀ GÌ

- Mỗi report hợp lệ phải có **vị trí người dùng chọn** và **comment người dùng nhập**.
- Giữ nội dung comment để người đọc biết người dùng đang phản ánh vấn đề gì. Không thay comment tự gõ bằng câu mẫu hoặc chuỗi `note omitted` rồi coi report đã đủ thông tin.
- Chỉ lưu vị trí mà mất comment là **flow báo lỗi hỏng**, không đạt điều kiện sử dụng.
- Kiểm chứng phải đi đủ đường: chọn vị trí → nhập comment tự do → Save → đọc file report. Comment trong file phải khớp comment đã nhập; thêm vị trí đúng chưa đủ để nghiệm thu.

## TẠI SAO

- Vị trí cho biết người dùng chọn chỗ nào; comment cho biết chỗ đó bị gì. Thiếu một phần thì worker phải đoán hoặc hỏi lại.
- Bản thử hiện tại chỉ giữ ba chuỗi comment mẫu. Comment khác bị thay bằng `[note omitted: synthetic vocabulary only]`, nên 12 report ngoài mẫu E2E mất mô tả vấn đề.
- Bug của chức năng Báo lỗi này độc lập với bug hiển thị thông báo trong Sơ đồ thừa kế. Sửa `relErrText` không khôi phục hoặc làm flow lưu comment hoạt động.

## Nguồn

Owner: “tối thiểu phải là: vị trí, comment của tôi. Nếu chỉ lưu vị trí mà không có report của tôi thì flow hỏng”.

Code đã đối chiếu: `D:/systemdocs-spike-visual-bug/_bmad-output/tmp/visual-bug-spike/custom/policy.cjs:16–18` thay comment; `main.cjs:77–83,98–99` ghi report và trả Save thành công.

Yêu cầu này chốt đầu ra tối thiểu. Cách triển khai và kiểm chứng sửa flow cần task riêng; chưa sửa code hoặc tự thay quy tắc thu thập dữ liệu khác trong phiên ghi quyết định.
