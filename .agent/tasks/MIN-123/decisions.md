# Decisions — MIN-123

## 2026-09-27 — Đích gộp

Chỉ dẫn mới nhất của chủ dự án: commit monorepo trước, merge nhánh hiện tại vào đó; lấy AGENTS.md của monorepo.
Đã thực hiện tại D:\systemdocs trên consolidate/monorepo. Không gộp runtime vào main.

## 2026-09-27 — Cách tổ chức kế hoạch

Linear giữ mô tả/điều kiện hoàn thành: parent MIN-123, con MIN-124–MIN-132.
plan.md là tài liệu điều phối thực thi, không là bản spec nghiệp vụ thay cho docs module.

## 2026-09-27 — Thiết kế được dùng

Dùng hai ảnh tham chiếu đã duyệt trong references, cùng quyết định mới nhất trong MIN-123.
P1 chuyển chúng vào bộ thiết kế dài hạn. Ảnh không quyết định mặc định dữ liệu; xem ghi chú ở plan.md.

## 2026-09-27 — Thứ tự công việc

Tách contract khỏi runtime; tách UI dùng chung khỏi worker module; Stage/Pool trước diagram vì đang dùng chung file.
Chủ dự án duyệt contract theo contracts/README.md trước P5. Việc duyệt hướng giao diện hiện tại không tự duyệt các thay đổi schema.

## 2026-09-27 — Word

Chủ dự án để phần xuất Word làm sau. Không triển khai popup/template/engine/đánh số xuất trong đợt UI này.
P2 chỉ xác định cách dữ liệu mới đứng cạnh khả năng xuất hiện có, để tránh dùng sai dữ liệu mới.
