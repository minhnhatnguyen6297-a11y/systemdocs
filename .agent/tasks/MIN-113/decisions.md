# Decisions — MIN-113

## D1. Thêm fixture `full-flow.json` thay vì sửa `ready.json`

`ready.json` (case 42) chỉ có 4 người — thiếu tiêu chí nghiệm thu "≥6
người, 2 tài sản, sơ đồ, 3 văn bản Word". Chọn thêm scenario mới
`full-flow` (case 47) vì:

- Giữ nguyên fixture cũ cho test hiện có (không phá baseline 113/100).
- Mock adapter đã hỗ trợ nhiều scenario theo fixture dir — chỉ thêm file.
- Case ID 47 không đụng dãy 42–46 đang dùng.

Không sửa contract, không sửa adapter code.

## D2. Không fix defect `word_export_batch` + dest read-only hang trong task này

Fault injection phát hiện defect thật (progress §4b): backend thật hang
trong `tempfile.mkstemp` retry loop tại `word_batch_export.py:242` khi
dest bị ACL deny write — job không terminal, không cancel được.

Quyết định: **ghi nhận, không sửa** — MIN-113 là VERIFY-only (brief
cấm feature/contract change), defect nằm ở `notary_v2` runtime (repo con
khác ownership). Hướng fix đề xuất cho issue follow-up:

1. Probe writability của dest trước khi render (try tạo/xóa file tạm một
   lần, fail fast `file_not_found`/`file_locked`).
2. Check `job.cancel_requested` giữa các vòng retry.
3. Hoặc render temp ra `%TEMP%` rồi copy publish (đổi giả định
   same-volume — cần owner cân nhắc atomicity).

Đây là **blocker tiềm năng cho cutover** — đưa vào checklist owner.

## D3. Packaged real-engine chưa verify được — ghi giới hạn thay vì che

Sidecar PyInstaller chạy được, nhưng import engine thật fail
(`sqlalchemy`/`sqlite3` thiếu trong bundle) kể cả khi có
`G1_NOTARY_V2_ROOT`. Quyết định: ghi rõ giới hạn trong progress/handoff
thay vì đánh dấu "packaged export Word" là pass. Verify được phần
controlled-error (`engine_not_installed`/`engine_unavailable`).

Follow-up đề xuất: task packaging riêng — bundle engine deps vào
PyInstaller spec (hidden imports: sqlalchemy, sqlite3, docx, fitz...) hoặc
ship engine kèm venv/embedded Python ngoài sidecar exe.

## D4. Doc drift cập nhật tối thiểu, chỉ chỗ sai thật

- `notary_v2/docs/platform/case-workspace/drafting-tab.md` §8 + header:
  phần "hiện trạng shell chưa có 7 command / gateway chưa tồn tại" đã
  stale sau MIN-106/107–112 → cập nhật sang hiện trạng đúng.
- `shell/README.md`: nav "7 mục" (MIN-67) → 5 mục taxonomy MIN-104; bổ
  sung gateway + mock dev flag + 8 command drafting.
- `docs/architecture/ELECTRON_G1_PLAN.md`: plan-level, nội dung còn đúng
  (G1.6 packaged smoke chính là task này) → không sửa.
- `contracts/`, Zalo, default entry: không đụng — đúng ràng buộc.
