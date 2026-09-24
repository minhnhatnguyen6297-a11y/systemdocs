# Decisions — MIN-106

- Contract `notary.case-drafting.v1` là SOT wire (APPROVED 24/09/2026) — mọi shape/error code bám contract, không tự chế.
- Gateway chọn backend ở **sidecar** (`notary_gateway.use_mock`): điều kiện `G1_DEV_NOTARY_MOCK=1` + `not sys.frozen`. Packaged (PyInstaller) → flag bị strip ngay ở Electron main (`config.js stripNotaryMockEnv` — sidecar kế thừa `process.env`) + warning redact ở cả hai tầng. Không đụng `sidecar.js` (ngoài file list).
- Real backend 7 command chưa tồn tại (MIN-107..110) → gateway dispatch trả `engine_not_installed` (code có sẵn trong contract §9, retryable=false) thay vì crash — cho phép tắt mock chạy dev vẫn an toàn.
- Fixture JSON trong `shell/test/fixtures/` là "database giả" của mock; `reset_backend(seed)` cho phép test seed scenario riêng; merge mặc định theo `_FIXTURE_PRIORITY` (ready thắng cho case 42).
- `word_export_options` là read-only → KHÔNG raise `workspace_locked`/`case_type_unsupported` (chỉ `word_export_batch` — command export — raise, theo §2.4/§2.5 "command ghi/evaluate/export"). Block_reason tính từ validation thật của Stage/Diagram.
- Idempotency dùng cơ chế `command_id` của `JobStore` hiện có — mock không tự chế; cancel giữa batch: file đã ghi giữ lại, file chưa bắt đầu không tạo (check_cancel đầu mỗi vòng lặp).
- Per-file `skipped` khi cancel không thể đi vào `result` vì jobstore set `result=null` cho canceled — ghi nhận là giới hạn platform, test assert trên đĩa.
