# Ghi nhận dọn dẹp module ngày 2026-09-25

Tài liệu này ghi lại đợt dọn dẹp cấu trúc cho `notary_v2` và `upload_lab`.
Đây là bản ghi dài hạn để agent sau biết phần nào đã chuyển, phần nào đã bỏ
và phần nào chưa được phép xóa.

## Đã làm

- Đổi `upload_lab/ui/services/` thành `upload_lab/upload_services/` để không
  đụng namespace `services.*` của `notary_v2` khi hai engine chạy chung trong
  sidecar.
- Chuyển công cụ regex vào `upload_lab/tools/` và cập nhật cách chạy CLI.
- Chuyển dependency POC vào đúng thư mục:
  - `notary_v2/tools/document_conversion_poc/requirements.txt`.
  - `upload_lab/poc/conversion_benchmark/requirements.txt`.
- Cập nhật allowlist đóng gói sidecar và script standalone theo các đường dẫn
  mới.
- Gỡ tooling agent sao chép trong module: `notary_v2/.agents/`,
  `upload_lab/.opencode/`, `notary_v2/skills-lock.json`, `notary_v2/IDEA.md`
  và `notary_v2/memory-bank/`.
- Các ghi chép vận hành hiện dùng `.agent/tasks/<ID>/brief.md`,
  `progress.md`, `decisions.md` và `handoff.md`. Memory-bank cũ chỉ giữ trong
  Git history và bản sao ngoài repo để khôi phục khi cần.
- Skill dùng chung được quản lý ở thư viện skill của môi trường agent; không
  tạo lại `.agents/`, `.opencode/` hay `skills-lock.json` riêng trong module.

## Dữ liệu được giữ

Không xóa hoặc đổi nội dung các nhóm dữ liệu sau:

- `notary_v2/notary.db`.
- `upload_lab/registry.sqlite3`.
- `shell/output/**`.
- `notary_v2/word_templates/**`.
- `upload_lab/regex_review_samples/**`, gồm `input/`, `golden/` và
  `reports/`.
- Fixture và contract examples trong `shell/test/fixtures/` và
  `contracts/`.

Bản sao bảo toàn trước dọn dẹp nằm ngoài repo tại:
`D:\systemdocs-cleanup-backups\20260925-231550`.
Manifest và hash chi tiết nằm trong
`.agent/scratch/module-cleanup-backup-manifest-2026-09-25.md`.
Không sao chép `.env`, token, cookie hoặc session đăng nhập vào backup.

## Chưa xóa trong đợt này

`upload_lab/ui_qt/`, các launcher Qt (`run_ui.bat`, `bootstrap_ui.py`,
`ui_runner.py`) và frontend web cũ của `notary_v2` vẫn được giữ làm đường lui.
Muốn xóa nhóm này cần một lượt riêng có đủ bằng chứng cutover Electron,
smoke hai module trên package Windows và test thay thế; việc dọn namespace ở
trên không tự chứng minh được launcher đã chuyển hẳn.

`notaryoffice/` và engine Zalo không thuộc phạm vi thay đổi.

## Kiểm tra đã chạy

- Upload Lab: 44 test nghiệp vụ/regex bằng pytest; 20 test cấu trúc Qt bằng
  venv Upload Lab.
- Shell Python adapter/workflow: 122 test pass.
- Sidecar contract: 27 test pass.
- Electron Node tests: 184 test pass.
- CLI regex chạy được từ vị trí mới; dữ liệu mẫu không bị đổi.
- Stage engine đã chứa `upload_services/`; import động từ stage và import từ
  bản standalone tạm đều pass.

Khi tiếp tục, còn cần chạy full package Windows/E2E trên máy sạch trước khi
xóa đường lui Qt/web.
