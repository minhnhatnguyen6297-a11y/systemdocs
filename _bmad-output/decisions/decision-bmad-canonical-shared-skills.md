# Một nơi cài BMAD cho các agent

Ngày: 2026-10-12

## LÀ GÌ

User chốt `C:\Users\MINH\.agents\skills` là nơi chứa BMAD chuẩn. Các agent trỏ tới cùng bản tại đây, không duy trì bản BMAD độc lập trong thư mục riêng của Codex hay agent khác.

Giữ BMAD làm workflow coding. Ticket bao gồm cài lại bản mới, thống nhất vị trí tích hợp HTML Plan và rút gọn AGENTS.md bằng cách bỏ chỉ dẫn flow trùng với BMAD.

## TẠI SAO

Các bản cài độc lập dễ lệch nội dung. Flow đã được BMAD quy định không cần sao chép vào AGENTS.md, tránh hai nơi ra chỉ dẫn khác nhau.

## Giới hạn quyết định

- Đây là yêu cầu được ghi vào ticket; chưa thực hiện cài lại, chuyển link hoặc sửa AGENTS.md.
- Giữ cấu trúc HTML Plan Thariq đã chốt và không xây flow song song.
- Cách tích hợp được đề xuất trong ticket: dùng override Build/Spec hiện có; không sửa trực tiếp installed skill và không dùng AGENTS.md làm nơi điều phối HTML.
