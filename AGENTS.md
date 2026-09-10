# AGENTS.md — systemdocs

Folder tài liệu cấp cha. **Không có code, không có runtime.**

## Quyền hạn của folder này

Được mô tả: quan hệ giữa các sản phẩm, vocabulary/khóa định danh dùng chung,
quyết định kiến trúc xuyên sản phẩm, câu hỏi mở.

Không được mô tả: hành vi nội bộ của một sản phẩm. Đó là việc của docs trong
repo đó. Khi xung đột, **repo con thắng** — và mâu thuẫn phải được sửa ở đây.

## Quy tắc khi sửa folder này

- Mọi mô tả repo con phải **kiểm chứng bằng file thật** (đường dẫn + số dòng),
  không viết theo suy luận. Tài liệu cũ ở đây từng sai nhiều vì lý do này.
- Ghi rõ **cái gì KHÔNG có** ngang với cái gì có. Phần lớn lỗi cũ là giả định
  tồn tại một luồng dữ liệu không tồn tại.
- Phân biệt rõ **hiện trạng** và **dự định**. `notaryoffice` chưa có code.
- Không tự chốt mục nào đang mở (🔴) trong `OPEN_DECISIONS.md`.
- Mọi lựa chọn công nghệ ghi ở `TECH_STACK.md`, không rải trong file khác. Thêm
  công nghệ mới cho một việc đã có công nghệ: phải qua 4 bước ở `TECH_STACK.md` §2.
- Đích đến là **một hệ thống dùng chung database**. Đừng viết lại các mô tả kiểu
  "ba sản phẩm độc lập vĩnh viễn" — phân biệt *hiện trạng* với *đích đến*.
- Không tạo contract tích hợp mới rồi tự implement trong cùng một task.

## Bản đồ file

| File | Nội dung |
|---|---|
| `README.md` | Chỉ mục, ba sản phẩm, đọc gì khi nào |
| `VISION.md` | Bài toán, nguyên tắc chung, điều cố tình không làm |
| `SYSTEM_ARCHITECTURE.md` | Ranh giới sản phẩm, sở hữu dữ liệu, kiến trúc dự kiến `notaryoffice` |
| `PROJECTS.md` | Từng repo: giải bài toán gì — feature gì — công nghệ gì |
| `TECH_STACK.md` | Công nghệ đã chọn + quy tắc thêm công nghệ mới + ràng buộc để gộp DB không xung đột |
| `contracts/entities.md` | Chuẩn hóa khóa định danh hồ sơ |
| `contracts/README.md` | Quy tắc contract-trước-code |
| `OPEN_DECISIONS.md` | Câu hỏi chưa chốt + phương án đã loại |
| `HANDOFF.md` | Gói việc giao cho agent từng repo |
