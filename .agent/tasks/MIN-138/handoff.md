# Handoff — MIN-138

## Trạng thái khi bàn giao — 2026-09-29

Đã hoàn tất cấu trúc lại và review diff. Linear MIN-138 có thể chuyển `Done`
sau khi local commit được tạo.

## Kết quả

- `README.md`: bản đồ duy nhất của cây spec.
- `AGENTS.md`: luật đọc gốc → cha → lá và chọn nơi ghi theo phạm vi.
- `docs/spec/`: SOT dài hạn mới theo hệ thống/module/flow/feature.
- `docs/spec/ui/`: giữ token, prototype và ảnh duyệt như phụ lục.
- `docs/architecture`, `docs/product`, `docs/maintenance` và ADR rời trong
  `notary_v2/docs/architecture`: đã xóa sau khi chuyển nội dung còn hiệu lực.
- Link liên quan trong module, contract, shell và template đã đổi sang cây mới.

## Cách verify

- `rtk git diff --check`
- Tìm các đường cũ bằng `rtk rg`.
- Kiểm link local của toàn bộ Markdown thay đổi/mới.
- Xem cây trong `README.md`, rồi đi tới từng spec lá.

## Việc còn lại / rủi ro

- Bản rút gọn đã qua 4 review lens; các gap cụ thể về lý do, trạng thái Draft,
  UI, DB, Internet và contract đã được bổ sung. Lịch sử đầy đủ vẫn có trong Git.
- Không đổi runtime behavior hoặc schema contract. File runtime chỉ đổi comment
  dẫn tài liệu; contract chỉ sửa mô tả/link để giữ đúng trạng thái hiện có.

## File tạm đã dọn

- Script kiểm link tạm trong `.agent/scratch/` đã xóa.
