---
id: 24
type: story
title: "Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
---

# Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần

## Description

Đồng bộ readiness với hướng điền dần đã chọn: dữ liệu hợp lệ chưa có có thể trống, mẫu chỉ cần Stage không đòi Diagram hoàn chỉnh không liên quan. Giữ rõ lỗi mẫu/nguồn, bảo vệ nháp và giới hạn slot chưa giải quyết.

## Acceptance Criteria

1. **Mẫu chỉ cần Stage**
   **Given** mẫu hợp lệ dùng field Stage đã lưu, có vài giá trị hợp lệ chưa có
   **When** chuyên viên xuất khi Diagram chưa hoàn thiện không liên quan
   **Then** điền phần có và để trống phần được phép; không chặn vì chưa hoàn tất nghiệp vụ không phục vụ mẫu
2. **Giữ blocker cụ thể**
   **Given** token không hỗ trợ, nguồn/mẫu hỏng, nháp khác bản lưu, stale revision hoặc slot ngoài ranh giải quyết hiện hành
   **When** chuyên viên xuất
   **Then** báo đúng điều kiện không an toàn và giữ chặn theo contract, không coi là field trống
3. **Kết quả từng mode/file**
   **Given** folder/legacy trong phạm vi blocker được chọn rõ
   **When** xuất nhiều văn bản có một file lỗi
   **Then** mỗi file dùng bản đã lưu, báo đã lưu/lỗi/bỏ qua riêng và không ghi đè nguồn

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C23
- source — _bmad-output/specs/notary_v2/README.md, §6, §9
- source — _bmad-output/specs/notary_v2/word-templates.md, §1, §3.3
- evidence — _bmad-output/tmp/issue-24-word-readiness/evidence/ (before/after engine 523608a, UI packaged non-native picker, tests, runtime restore)

## Notes

- Tracking: C23; **built 2026-10-16** (implementation + proof xong; Quick t1 finding vá nhãn readiness rồi recheck clean) theo uỷ quyền liên tục (không chờ duyệt plan). #1 chỉ tracking, không chạy cùng leaf. Independent Quick đã chạy: t1 PATCH (nhãn readiness) → vá + recheck clean; chưa commit (chờ coordinator).
- Risk: high — Nới nhầm guard có thể xuất sai nguồn/slot hoặc dữ liệu chưa lưu thay vì chỉ để trống trường hợp lệ. Đã khoanh bằng: phân loại gate theo registry key mẫu thực dùng (không đoán chuỗi con), giữ nguyên unresolved-slot/người được ủy quyền/giới hạn kỹ thuật, và before/after với engine 523608a.
- Đã rõ (thay Unknown cũ): phạm vi nới = gate nhóm `no_landowner`/`no_deceased_landowner`/`no_receiver` (thừa kế) và `no_diagram` hai bên theo token mẫu; catalog legacy theo mẫu từng `document_key`; folder mode giữ nhóm thiếu để trống; các blocker kỹ thuật và unsafe-slot không đổi. Spec `word-templates.md` §1/§3.3/§3.5 và contract §8.1 đã đồng bộ trước code.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.

### Measured evidence — 2026-10-16

- **Before/after engine (cô lập, không reset repo):** bản 523608a chạy từ bản sao `services/` riêng vs engine sau patch, cùng fixture + mẫu: builtin + thiếu người nhận `word.no_receiver` → ready + saved; two_party mẫu Stage-only chưa có diagram state `word.no_diagram`/failed → ready + saved (cả nhánh folder static); mẫu dùng ghế `Bên A` giữ `word.no_diagram`; builtin không chủ đất chết giữ `word.no_deceased_landowner`; mẫu hỏng trước báo nhầm `word.no_receiver` → sau `word.render_failed` ở cả readiness lẫn batch; route adapter `export_word` trước raise blanket → sau mẫu Stage-only build mapping OK (mẫu dùng nhóm Người nhận vẫn raise). Xem [before-after-summary.json](../tmp/issue-24-word-readiness/evidence/before-after-summary.json), [before-engine-523608a.json](../tmp/issue-24-word-readiness/evidence/before-engine-523608a.json), [after-engine-patched.json](../tmp/issue-24-word-readiness/evidence/after-engine-patched.json).
- **Tests sau patch:** `test_word_batch_export.py` + `test_word_engine.py` **153 passed, 2 skipped**; `shell/test/test_notary_adapter_contract.py` **83 passed**; mock adapter + `test_word_template_migration.py` **228 passed, 5 skipped**; renderer node **159 passed** (log [tests-after-word.txt](../tmp/issue-24-word-readiness/evidence/tests-after-word.txt), [tests-after-adapter.txt](../tmp/issue-24-word-readiness/evidence/tests-after-adapter.txt), [tests-after-mock-migration.txt](../tmp/issue-24-word-readiness/evidence/tests-after-mock-migration.txt), [tests-after-node.txt](../tmp/issue-24-word-readiness/evidence/tests-after-node.txt)).
- **UI thật, gói default (`shell/dist-app/win-unpacked/g1-shell.exe`), profile cách ly + DB thật + sidecar thật:** picker là **seam test non-native** (marker test-build + app.asar staging — không phải picker native, không claim native). Case two_party chưa có diagram state seed qua `notary.workspace_create` thật: folder options `stage_only`/`auth_slot`/`unknown_token` ready, `hong` bị chặn `word.render_failed`; "Nơi niêm yết" dirty chặn Xuất (0 kết quả) rồi phục hồi bình thường; Xuất → **1 saved/2 lỗi đúng từng file** (`word.missing_authorized_person`, `word.unresolved_placeholders`); DOCX `stage_only_HS-1.docx` điền `Lê Văn A và Phạm Thị B` + để trống `Ngày cấp`, không còn token; mẫu nguồn không đổi. Xem [ui-smoke-24.json](../tmp/issue-24-word-readiness/evidence/ui-smoke-24.json) + ảnh `24-01-dialog-open.png`…`24-04-export-results.png`.
- **Packaging/runtime:** hai file engine Python đã sync repo → `shell/build/engine` + `resources/engine` (hash khớp — [packaging-sync.json](../tmp/issue-24-word-readiness/evidence/packaging-sync.json)); app.asar **phục hồi nguyên bản** cho lượt smoke đầu (sha256 `d8aa8301…` khớp trước/sau, marker gỡ — [runtime-restore.json](../tmp/issue-24-word-readiness/evidence/runtime-restore.json)); sau finding Quick t1, `word-export-dialog.js` được vá nhãn readiness (UI hiển thị tiếng Việt thay mã trần) và **app.asar production được dựng lại từ source có patch nhãn** (sha mới `ecc4ed2a…`, không còn hook smoke — [ui-smoke-24-labels.json](../tmp/issue-24-word-readiness/evidence/ui-smoke-24-labels.json), ảnh `24-01…24-04`); default sau đó khởi động OK.
- **Sidecar/legacy route (public `notary.export_word`):** xác nhận `notary_adapter` nằm trong PYZ của `g1-shell-sidecar.exe` (bundle không có `.py`; `command_registry`/`notary_gateway` import lazy) → rebuild sidecar-only (PyInstaller, không Electron/ASAR), sync `resources/sidecar/g1-shell-sidecar` (exe cũ `72c5a312…` → mới `0af89f86…`, backup đủ 2186 file). Probe qua app default/DB cách ly: trước — hồ sơ không người nhận vẫn `validation_error` "Không có người nhận…"; sau — xuất được `ho_so_thua_ke_1.docx` (20.698B, có tên chủ đất); hồ sơ thiếu chủ đất chết vẫn `validation_error` như cũ. [adapter-sidecar-cutover.json](../tmp/issue-24-word-readiness/evidence/adapter-sidecar-cutover.json), [legacy-probe-before.json](../tmp/issue-24-word-readiness/evidence/legacy-probe-before.json), [legacy-probe-after.json](../tmp/issue-24-word-readiness/evidence/legacy-probe-after.json).
- **Giới hạn còn lại:** picker native không automate được (theo #9, không thử lại); seam `G1_E2E_PICK_FILES` trong repo trả path trần (thiếu token) nên chưa dùng được cho đường token — smoke đã dùng bản staged chỉ trong artifact, **không sửa source seam**; độ dài đường dẫn/CDP profile dùng `.tmp/shortpaths`.
