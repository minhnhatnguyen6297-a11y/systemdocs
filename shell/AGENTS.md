# AGENTS.md — shell

Module vỏ desktop của monorepo: Electron main/renderer + Python FastAPI
sidecar. Sở hữu shell/lifecycle/navigation — **không sở hữu nghiệp vụ** và
không tự ghi DB của module nghiệp vụ.

## Sources of truth
- `docs/SPEC.md` — **SOT duy nhất** về vai trò, kiến trúc và ràng buộc của shell
- `README.md` — cách chạy/build
- `../contracts/desktop-command.md` — contract `desktopcommand.v1` APPROVED
- `../contracts/g1-module-data.md` — contract `g1.module.v1` APPROVED
- `sidecar/g1-shell-sidecar.spec` — spec sidecar

## Rules
- Renderer chỉ nói với main qua `contextBridge` allowlist; không expose API
  tùy ý.
- Sidecar chỉ listen loopback, token/port do Electron main cấp.
- Sidecar gọi engine `notary_v2`/`upload_lab` bằng import in-process qua
  `sys.path` (`sidecar/engine_roots.py`) — đây là kênh được duyệt, **không phải
  API giữa các module nghiệp vụ**. Không thêm đường gọi trực tiếp
  module ↔ module.
- Không thêm command mới ngoài contract đã duyệt; thay đổi contract phải đi
  theo quy trình `../contracts/README.md` (duyệt trước, implement sau).
- Không đọc/ghi trực tiếp `notary.db`, `registry.sqlite3` — mọi truy cập qua
  adapter + engine code của module chủ sở hữu.
- `upload_lab/poc/desktop_command/` là POC `v0.experimental` đã hết hạn — không
  backport shape của nó vào sidecar.

## Cross-module context (read only when needed)
Tài liệu cấp repo ở `../`: `../SYSTEM_ARCHITECTURE.md` §5/§6 (ranh giới shell),
`../TECH_STACK.md` (bắt buộc trước khi thêm/đổi công nghệ),
`../OPEN_DECISIONS.md` (không tự chốt). Nghiệp vụ engine:
`../notary_v2/docs/SPEC.md`, `../upload_lab/docs/SPEC.md`.

## Kiểm chứng trước khi báo xong
- Sửa code: chạy test/contract-test của module (xem `README.md`/`package.json`).
- Sửa contract example trong `../contracts/`: chạy
  `python ../contracts/g1/validate_examples.py`.
