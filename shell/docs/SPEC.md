# SPEC — shell (Nguồn SOT nghiệp vụ duy nhất)

Đặc tả nghiệp vụ/phạm vi của module `shell` — vỏ desktop Electron + Python
sidecar trong monorepo `systemdocs` (nhánh `consolidate/monorepo`). Hợp đồng
kênh lệnh ở `../../contracts/desktop-command.md` (`desktopcommand.v1`, APPROVED) và
`../../contracts/g1-module-data.md` (`g1.module.v1`, APPROVED) — hai file đó là SOT
cho wire format; file này là SOT cho **shell sở hữu gì / không sở hữu gì**.

Cập nhật: 16/09/2026. Tiền thân: POC `upload_lab/poc/desktop_command/`
(`v0.experimental`, không tương thích ngầm).

## 1. Vai trò

Shell thống nhất cho hệ thống công chứng trên **một máy Windows** (G1-SM:
loopback `127.0.0.1`, không LAN). Shell sở hữu **vỏ/UI/lifecycle/navigation**;
**không sở hữu nghiệp vụ** — nghiệp vụ vẫn do `notary_v2` / `upload_lab` giữ,
sidecar chỉ gọi vào.

## 2. Kiến trúc kênh lệnh

```text
renderer (sandbox, không Node/fetch)
  → window.desktop.v1.* (preload contextBridge, allowlist có version)
  → Electron main (giữ token, spawn sidecar port động, poll /healthz ≤30s)
  → HTTP loopback + Bearer → sidecar FastAPI (sidecar/app.py)
  → command_registry (lệnh namespaced, idempotent theo command_id)
  → engine adapter → import engine module qua sys.path (engine_roots.py)
```

- Renderer **không bao giờ** gọi sidecar; token chỉ trong memory của main.
- Engine resolve theo thứ tự: env `G1_NOTARY_V2_ROOT`/`G1_UPLOAD_LAB_ROOT` →
  `shell/engine-roots.json` (gitignored) → thư mục bundled cùng repo
  (`../notary_v2`, `../upload_lab`).
- Job là async: `POST /v1/commands` → `job_id`; client poll
  `GET /v1/jobs/{id}`; cancel qua `/cancel`; `waiting_user` nghĩa là engine
  chờ người (login/review/finalize/confirm) — **shell không tự hoàn thành**,
  đặc biệt không auto-Finalize.
- `file_ref` chỉ `machine_local` (absolute path, chặn UNC); file vào engine
  chỉ qua `desktop.v1.pickFiles` của Electron main.

## 3. Nghiệp vụ đi qua shell (qua adapter, owner vẫn là module)

| Namespace | Adapter | Gọi tới |
|---|---|---|
| `notary.*` (10 lệnh: case/customer/property/participant, `word_templates`, `export_word`) + `ocr.analyze` + `zalo.status` (12 lệnh tổng) | `sidecar/notary_adapter.py` | `notary_v2` models + router handlers + `services.word_engine`/`ocr_ai`; OCR trả `observed`, chưa confirm không thành truth |
| `upload.*` (10 lệnh: scan, audit_excel, env_check, session_start/prepare/finish_review, download_export) | `sidecar/upload_adapter.py` + `upload_session.py` | `upload_lab` `batch_scan`, `contract_book_audit`, `environment_check_service`, `NamDinhUploaderSession` (Chromium headed trên thread `g1-upload-browser`) |
| `diag.*` | sidecar | chẩn đoán (progress/cancel/waiting/env), không phải nghiệp vụ |

`notary_adapter` tự chạy migration + `create_all` của `notary_v2` → sidecar
là owner ghi `notary.db` khi chạy trong monorepo. Upload ở shell vẫn là
**dry-run**: người dùng bấm Lưu trong Chromium.

## 4. UI shell (navigation & trạng thái)

- Nav trái 7 mục: Tổng quan · Upload/Audit · Hồ sơ · Excel/Word · Văn phòng
  (placeholder "Chưa triển khai") · Tìm kiếm · Trạng thái/Cài đặt.
- Mỗi module view là DOM subtree persistent — đổi module không mất file đã
  chọn/job/scroll; job tiếp tục ở sidecar + job tracker.
- 4 mặt trạng thái chung: `loading / empty / error / unavailable`;
  `waiting_user` là banner + CTA trong module, không phải lỗi.
- Cancel có confirm, chỉ ở `accepted/running/waiting_user`; retry tạo
  `command_id` mới. Đóng app khi còn job → confirm (shutdown sẽ cancel job).
- Renderer reload không mất job: `desktop.v1.listJobs` nối lại snapshot.
- `desktop.v1.openPath` mở file sản phẩm bằng app mặc định (validate absolute,
  tồn tại, không UNC).

## 5. KHÔNG phải / ranh giới

- **Không chứa business logic** — không port nghiệp vụ Python sang JS; không
  tự ghi DB module ngoài qua adapter đã định.
- **Không mở app legacy bên ngoài**; navigation ngoài `NAV_SPEC` bị từ chối.
- **Không LAN, không auto-update** trong G1-SM; update = thay thư mục.
- **Local OCR parked**: route liên quan trả `failed{engine_not_installed}`.
- Log/diagnostics phải redact token, cookie, username trong path
  (`src/main/redact.js`).

## 6. Vận hành (tóm tắt — chi tiết ở `shell/README.md`)

`npm install` → `npm start` (dev: `python sidecar/app.py`); package:
`npm run build:sidecar` (PyInstaller → `sidecar/dist/`) + `npm run dist`.
Test: `npm test` (node --test) + `python test/test_sidecar_contract.py`
(contract conformance với uvicorn thật) + `test_engine_adapters.py`
(cần engine-roots).
