# Một nơi cài BMAD cho các agent

> **Bị thay bởi [decision-81](decision-81%20-%20Bo-BMAD-thu-Superpowers-docs-chuyen-sang-docs.md) (28/10/2026).** Giữ để tra lịch sử.

Ngày: 2026-10-12

## LÀ GÌ

User chốt `C:\Users\MINH\.agents\skills` là nơi chứa BMAD chuẩn. Các agent trỏ tới cùng bản tại đây, không duy trì bản BMAD độc lập trong thư mục riêng của Codex hay agent khác.

Giữ BMAD làm workflow coding. Ticket bao gồm cài lại bản mới, thống nhất vị trí tích hợp HTML Plan và rút gọn AGENTS.md bằng cách bỏ chỉ dẫn flow trùng với BMAD.

## TẠI SAO

Các bản cài độc lập dễ lệch nội dung. Flow đã được BMAD quy định không cần sao chép vào AGENTS.md, tránh hai nơi ra chỉ dẫn khác nhau.

## Giới hạn quyết định

- User yêu cầu “xử lý luôn”: thực thi ticket trong phiên này.
- Giữ cấu trúc HTML Plan Thariq đã chốt và không xây flow song song.
- HTML Plan gắn trực tiếp vào Build/Spec qua override hiện có; không tạo skill HTML lẻ, không patch installed skill và không dùng AGENTS.md làm nơi điều phối HTML.

## Bản cài được chọn

- Dòng BMAD skills preview, version `6.13.0-next`, upstream `main` tại commit `9f1987169a2e5626e5ccb31bb9cee051fdb3df20`; không chuyển sang kiến trúc installer stable v6.
- Giữ tập skills đang dùng; đổi `bmad-preview-ticketing` thành `bmad-ticket`. Không cài thêm module tùy chọn.
- Installer: `npx skills`; project scripts được cập nhật bằng `bmad setup`. Customization ở `_bmad/custom/`, không sửa trực tiếp skill được cài.
- Bản bảo lưu trước thay thế: `docs/tmp/bmad-shared-migration/backup-before-install/`. Bằng chứng runtime: `docs/tmp/bmad-shared-migration/smoke-proof.json`.
