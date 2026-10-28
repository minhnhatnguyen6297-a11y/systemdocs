# Delegation mặc định theo harness; Orca chỉ khi user yêu cầu

> **Bị thay bởi [decision-81](decision-81%20-%20Bo-BMAD-thu-Superpowers-docs-chuyen-sang-docs.md) (28/10/2026).** Giữ để tra lịch sử.

## LÀ GÌ

- Bỏ luật Orca-only. Mặc định dùng cơ chế subagent của harness hiện tại (OMP hoặc agent khác).
- Chỉ dùng Orca để spawn/điều phối khi user yêu cầu rõ; lúc đó theo skill và guide Orca hiện hành.
- Quyết định này thay thế riêng yêu cầu transport Orca trong decision-79 và các quyết định trước; không thay lịch sử thực thi.
- Giữ coordinator sở hữu delegation, topology phẳng, một implementation worker và một reviewer mặc định, test trước review và chạy lại sau patch, lens phụ theo rủi ro.
- Khi user yêu cầu tự làm trong phiên hiện tại, thực hiện trực tiếp thay vì bắt spawn worker; vẫn kiểm chứng và báo rõ nếu không có review độc lập.

## TẠI SAO

User yêu cầu bỏ luật Orca-only và sẽ nói rõ khi cần Orca. Ép một transport tạo mâu thuẫn với subagent sẵn có của harness và thêm lớp cầu nối không cần thiết. User cũng yêu cầu trực tiếp hoàn tất thay đổi này trong phiên hiện tại.
