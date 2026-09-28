# Progress — MIN-131

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: đang làm

## Đã làm
- Đọc xong spec/design/prototype + P4 handoff + toàn bộ 4 file renderer upload.
- Liệt kê xong DOM hook bắt buộc giữ (xem brief.md — trích từ `upload-routing.test.mjs` + `test_upload_e2e.py`).
- `.slot` trên jobsBox là class marker không style (e2e `dump_debug` dùng `.upload-lab .slot *`) — giữ nguyên.
- `window.addEventListener` KHÔNG tồn tại trong node test (`global.window = {}`) → mọi handler window-level phải guard `typeof window.addEventListener === 'function'`.

## Đang làm dở
- Refactor `audit.js`/`scan-upload.js`/`index.js` sang `.card`/`.ul-row` gọn + `upload.css` viết lại theo token.

## Bước tiếp theo
- Viết code → chạy 2 test mjs bắt buộc → `git diff --check` → commit theo lô → `handoff.md`.

## Check đã chạy
- (chưa — sẽ ghi sau mỗi lần chạy)
