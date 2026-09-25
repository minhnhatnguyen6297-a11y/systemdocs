# MIN-93 Implementation Plan — Scaffold repo Zalo độc lập

> Thực thi theo subagent-driven-development: 4 slice song song (file rời nhau
> qua decision-sheet), controller tích hợp + review + commit scaffold.

**Goal:** Repo local `D:\zalo-intake` chạy được độc lập: `cli replay` ghi journal
+ nguồn vào DB riêng, `serve` lên FastAPI status, `migrate` tạo schema; test
subprocess chứng minh không cần notary/PYTHONPATH/DB notary; restart giữ
`captured_at`. Không chuyển baseline connector/Qwen (MIN-103), không ảnh thật,
không secret.

**Spec:** `D:\systemdocs\docs\product\plans\2026-09-24-zalo-independent-implementation-plan.md`
§MIN-93 + Linear MIN-93 (acceptance trong `brief.md`).

**Contract SOT:** `D:\systemdocs\contracts\zalo-intake\` (intake.*.v1, đã publish).

**Interface chốt:** `D:\systemdocs\.agent\scratch\MIN-93\decision-sheet.md` —
mọi agent đọc trước; tên hàm/bảng/env ở đó là bắt buộc.

**Tech:** Python 3.12.10, FastAPI 0.111.0, SQLAlchemy 2.0.47, pytest; Node ≥20
(chỉ stub connector); SQLite file trong `runtime/` gitignored.

## Global constraints

- Không chuyển code/session/media/Qwen từ notary (MIN-103). Không xóa legacy.
- Không nested `.git`/submodule trong `D:\systemdocs\zalo\`; không remote/deploy.
- Không secret/`.env`/cookie/session/DB/ảnh thật trong git. `runtime/` gitignored.
- Không dep ngoài baseline `notary_v2/requirements.txt` (không alembic/pydantic).
- Không `import notary*`, không đọc file ngoài repo (trừ copy contract schemas).
- Runtime paths chỉ dưới `runtime/`; `audit.record_access` ghi mọi file mở.
- Job states đúng literal: `queued|running|retry_wait|succeeded|failed|expired`.
- `image_expires_at = captured_at + 168h` đúng tuyệt đối.
- Contract là SOT — scaffold không sửa contract, không re-implement validator.
- Agent không `git commit`; controller commit sau review.

## Slices (wave 1 — song song, file ownership theo decision-sheet §1)

| Slice | Agent owns | Produces |
|---|---|---|
| A | root + connector/ + docs/repo-ownership + schemas/ + settings/audit/types | nền repo, config, contract vendor |
| B | database.py + models.py + migrations/ + test_migrations | DB schema + migrate idempotent |
| C | intake/journal + storage/* + jobs/worker + 3 unit test | capture_event idempotent, 168h, lease |
| D | delivery/* + api/* + ocr/* stub + test_package_bytes | gói raw byte-exact, API status/feed/receipt/OCR-request |

Wave 2 (sau khi 4 slice merge + review): **E** — cli.py + app.py + conftest +
fixtures + integration test + docs/local-runbook.md + chạy verify.ps1.

## Verify (task-level)

```powershell
cd D:\zalo-intake
python -m pytest tests -q                                   # unit + integration
python -m zalo_module.cli migrate
python -m zalo_module.cli replay tests\fixtures\synthetic\event_text_message.json
python -m zalo_module.cli status
.\verify.ps1                                                # tổng hợp
```

Acceptance MIN-93 (Linear): replay synthetic subprocess, notary tắt + không trên
PYTHONPATH; restart giữ captured_at/identity; runtime paths chỉ trong module;
không secret trong git; verify chạy được không account live; bàn giao commit
scaffold + quyết định ownership + ranh giới MIN-103.

## Sau khi xong

Controller: chạy verify đầy đủ → reviewer cuối → `git add -A && git commit`
scaffold (một commit) → cập nhật progress/handoff/decisions + ledger → báo
owner. Không đụng `D:\systemdocs\zalo\` (MIN-103 tạo snapshot).
