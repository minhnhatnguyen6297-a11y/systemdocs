# Progress — MIN-131

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: xong — chờ review (2026-09-28)

## Đã làm
- Đọc spec/design/prototype/P4-handoff + 4 file renderer + test hooks.
- Refactor xong `audit.js`, `scan-upload.js`, `index.js`, `upload.css` theo
  prototype đã duyệt; giữ mọi DOM hook test (xem `brief.md` + `decisions.md`).
- `state.js`/`client.js` KHÔNG đổi.
- Commit `f82443a` (docs task) + `29295aa` (feat code); docs cuối sau khi
  ghi xong file này + `handoff.md`.

## Đang làm dở
- (không — hoàn tất)

## Bước tiếp theo
- P9/MIN-132: chạy e2e + manual acceptance (xem handoff §"Chưa verify").

## Check đã chạy
- `node --check` 3 file JS — OK.
- `cd shell && node --test test/upload-state.test.mjs` — 19/19 pass.
- `cd shell && node --test test/upload-routing.test.mjs` — 45/45 pass.
- `python test/test_upload_workspace.py` — 27/27 OK.
- `python test/test_upload_workflow.py` — 22/22 OK.
- `python test/test_upload_recovery.py` — 16/16 OK.
- `git diff --check` — sạch.
- `git show --stat` 2 commit — chỉ file sở hữu.
