# MIN-113 — VERIFY: Parity, packaged smoke và cutover tab Soạn hồ sơ

Linear: MIN-113 (parent MIN-68). Plan §14 (Task 10) + Definition of Done.
Base `6799886` — toàn bộ backend + frontend đã merge. Đây là task VERIFY, không phải feature.

## Phạm vi (Linear + plan §14)

1. **Fixture hoàn chỉnh**: mock fixtures đã có case 42–46; verify có đủ ≥6 người, 2 tài sản, sơ đồ thừa kế, 3 văn bản Word — nếu fixture chưa đủ thì bổ sung vào `shell/sidecar/notary_mock_adapter.py` + `shell/test/fixtures/notary-case-drafting/` (được phép sửa mock/fixture vì là test asset; KHÔNG sửa contract).
2. **Full flow** (mock trước): mở hồ sơ → intake → Stage commit → Pool/Diagram → save → reload → export Word. Có thể scripted qua gateway dispatch + model tests; UI thật smoke bằng Electron.
3. **Fault injection**: Qwen thiếu key (`QWEN_API_KEY` absent → `intake.ocr_unavailable` hoặc tương đương), sidecar restart, revision conflict, locked case, template hỏng, destination read-only, cancel batch giữa chừng.
4. **Privacy**: grep log output — không họ tên/CCCD/raw OCR/path username chưa redact.
5. **Packaged**: `npm install` → `npm run build:sidecar` (PyInstaller) → `npm run dist` (electron-builder --dir) → launch packaged exe → smoke mở/đóng + export Word. Packaged KHÔNG được dùng mock (flag bị strip).
6. **Parity**: cùng flow chạy mock và real (real cần DB — nếu không có DB test thì verify qua adapter contract tests + scripted gateway, ghi rõ giới hạn).
7. **Đối chiếu web cũ**: ghi danh sách khác biệt có chủ ý vào progress.md.
8. **Cutover**: KHÔNG tự đổi default entry — owner duyệt UI trước. Chuẩn bị sẵn danh sách "cần owner duyệt" + kế hoạch rollback (web cũ giữ 1 chu kỳ).
9. **Docs**: cập nhật `shell/README.md` (nếu cần), `docs/architecture/ELECTRON_G1_PLAN.md` (trạng thái), `notary_v2/docs/platform/case-workspace/drafting-tab.md` (nếu có drift thật).

## Môi trường

- Worktree `D:\systemdocs-min-113`; shell chưa có `node_modules` → `npm install` trước (electron ~100MB).
- Python venv: `D:\systemdocs\notary_v2\venv\Scripts\python.exe`.
- Windows desktop thật — Electron có thể mở window; packaged build qua electron-builder `--dir`.
- Sidecar build: `powershell -ExecutionPolicy Bypass -File shell/sidecar/build_sidecar.ps1`.

## Ràng buộc

- KHÔNG sửa contracts/, KHÔNG đụng Zalo, KHÔNG ghi DB người dùng (fixture/output test chỉ ở DB/folder tạm).
- KHÔNG tự đổi default entry/cutover — đó là quyền owner.
- Nếu packaged build fail do môi trường (thiếu tool, network), ghi evidence + workaround; không silently skip.

## Verify outputs → progress.md (dán output thật)

- `npm --prefix shell test` (113 baseline)
- `pytest shell/test/test_notary_mock_adapter.py test/test_notary_adapter_contract.py` (100)
- `pytest notary_v2/tests/test_case_workspace.py test_document_intake.py test_inheritance_workspace.py test_word_batch_export.py test_inheritance_engine.py test_word_engine.py` (venv)
- `python contracts/notary-case-drafting/validate_examples.py` (34/0)
- `python shell/test/test_sidecar_contract.py`
- Packaged smoke log + screenshot/evidence nếu có thể.
