# MIN-112 — FRONTEND: Nối Intake, Stage, Diagram và Word export

Linear: MIN-112 (parent MIN-68). Plan §13 (Task 9). Base: MIN-111 đã merge `6aa74bf`.
SOT: spec `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`
+ `notary_v2/docs/platform/case-workspace/drafting-tab.md`.
Contract `contracts/notary-case-drafting.md` (READ-ONLY).

## Files (plan §13)
- Create `shell/src/renderer/notary/intake-dialog.js`
- Create `shell/src/renderer/notary/relationship-diagram.js`
- Create `shell/src/renderer/notary/word-export-dialog.js`
- Modify `case-drafting-model.js`, `case-drafting-view.js`, `case-drafting.css`
- Modify `shell/src/preload/preload.js`, `shell/src/main/ipc.js`, `shell/src/main/main.js`
- Modify `shell/test/ipc.test.mjs`, `notary-case-drafting-model.test.mjs`, `notary-case-drafting-static.test.mjs`

## Deferred từ MIN-111 (phải làm ở đây)
- `notary.case_list` mock parity — hiện route real adapter; overview cần list case mock.
- App-close unsaved guard (main.js close handler + canLeave).
- Word dialog per-doc progress + cancel.
- Modal focus-trap nếu rẻ.

## OPAQUE FILE TOKEN — yêu cầu bảo mật cốt lõi
`pickFiles` hiện trả path thật → renderer forge được. Phải đổi:
- `pickFiles` trả `{file_token, name, size_bytes, is_dir}` — KHÔNG trả `path` cho renderer.
- Main giữ Map token→FileRef thật (crypto UUID), chỉ tạo từ native dialog; clear khi app đóng/reload window; KHÔNG đưa vào log/storage.
- `submitCommand` trong `ipc.js`: quét payload, thay `{file_token}` tại vị trí `sources[].file_ref` (intake_analyze) và `destination` (word_export_batch) bằng FileRef thật; token lạ/đã hết hạn → `validation_error` trước khi forward.
- `openPath` giữ nguyên (path đến từ `output_file` backend result, đã validate).
- Static test: renderer source không chứa `.path` gửi lên; ipc test: token substitution đúng, token lạ reject.

## Nghiệm thu (Linear + plan)
1. Intake: picker theo loại (image/pdf/docx/xlsx), drop zone, paste text, danh sách source, progress + cancel, review cards, lỗi từng source riêng.
2. `Đưa vào Stage` chỉ tạo draft row; đóng popup giữ kết quả phiên; intake chạy lại thêm lên đầu, không xóa ngầm.
3. Stage: inline trường chính + drawer chi tiết; remove chỉ đổi draft; `Cập nhật` gửi full snapshot + `base_revision`; `field_errors` gắn đúng row/field.
4. Pool derive committed Stage − Diagram assignments; search/filter chỉ đổi hiển thị.
5. Diagram: render backend `render_model` (HTML/SVG, không ReactFlow); drag/drop chỉ draft; menu `Gán vị trí` keyboard; debounce evaluate; `Lưu sơ đồ` persist; xóa node KHÔNG xóa Stage.
6. `Xem cách tính` hiển thị nguyên văn engine explanation — JS không tính pháp lý.
7. Word popup: `word_export_options` → checkbox nhiều văn bản → `pickFiles({directory:true})` (token is_dir) → submit 1 lần → track job → per-doc `Đã lưu`+path+nút mở / `Lỗi`+reason; popup KHÔNG tự đóng khi có lỗi; cancel được.
8. Rời tab/app với draft chưa lưu → confirm (cả module switch lẫn window close).
9. Mock và real chạy CÙNG component — cấm `if mock` trong business UI; swap qua seam `makeCommandRunner`.

## Ràng buộc
- Không deps mới, không framework/bundler, không Zalo, không sửa contracts/ hoặc backend Python.
- Không log PII; token không vào log.
- Giữ 44px/focus-visible/ARIA.

## Verify
- `cd D:\systemdocs-min-112\shell && npm test`
- `python -m pytest shell/test/test_notary_mock_adapter.py shell/test/test_notary_adapter_contract.py -q` (venv `D:\systemdocs\notary_v2\venv\Scripts\python.exe`)
- Directory picker phải trả `is_dir=true`; ipc test chứng minh renderer không gửi path tùy ý.
