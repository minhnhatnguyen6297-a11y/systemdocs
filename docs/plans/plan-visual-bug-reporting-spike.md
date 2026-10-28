---
title: 'Visual bug reporting spike for Electron'
type: 'feature'
ticket: ''
created: '2026-10-08'
status: 'draft'
route: 'full'
route_source: 'auto'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Báo lỗi UI/UX trên Electron app hiện tốn nhiều thao tác tay (chụp màn hình, đánh dấu, mô tả bằng lời) trước khi agent đủ context để sửa và tự kiểm chứng.

**Approach:** Spike trên worktree riêng: khảo sát stack thực tế, thử ready-made (Agentation, React Grab) trong cửa sổ Electron thật, dựng DevMode prototype tối thiểu (chọn element + ghi chú → bug report có cấu trúc), test end-to-end để ra so sánh, khuyến nghị, kiến trúc và plan triển khai.

## Boundaries & Constraints

**Always:** Reuse tối đa, tối giản, kiến trúc sạch; chỉ kích hoạt ở development mode; không thu thập secret/PII (tận dụng redaction sẵn có); không đổi production behavior; làm trên worktree/branch `spike/visual-bug-reporting`; dọn dependency/code thử không cần sau spike.

**Never:** Xây framework báo lỗi hoàn chỉnh hay production feature; mang React-only tooling vào renderer vanilla; bật DevTools/CDP hay nới lỏng sandbox/CSP ở production; giữ lại code thử nghiệm sau đánh giá.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Báo lỗi happy-path | DevMode bật, click 1 element, ghi chú ngắn | Report JSON+MD có screenshot, DOM path, rect, console errors, diagnostics tail, state subset | No error expected |
| Element không định danh được | Renderer vanilla, không data-testid | Report vẫn ghi CSS path + outerHTML rút gọn + cảnh báo thiếu mapping | Ghi `unmapped:true`, không crash |
| Screenshot bị chặn | desktopCapturer từ chối hoặc CSP chặn | Report vẫn đầy đủ context text, đánh dấu `screenshot:missing` + lý do | Fallback CDP trong harness test, không chặn flow |
| Secret lọt vào report | State/log chứa token, đường dẫn user | Redaction loại bỏ trước khi ghi file | Áp `redact.js`, verify bằng test quét secret |

## Decisions

- DevMode entry: gắn vào menu dev sẵn có (không dùng hotkey tạm).
- Report sink: `docs/tmp/bug-reports/` trong worktree.
- Screenshot: ưu tiên thử `desktopCapturer` trong app, CDP chỉ làm fallback ở harness test.

</frozen-after-approval>

## Code Map

- `D:/systemdocs-spike-visual-bug/shell/src/main/main.js` -- BrowserWindow sandbox/contextIsolation, IPC register, `collectDiagnostics()` tail 40 dòng log đỏ.
- `D:/systemdocs-spike-visual-bug/shell/src/preload/preload.js` -- allowlist `desktop.v1.*` qua contextBridge; nơi mở thêm kênh DevMode dev-only.
- `D:/systemdocs-spike-visual-bug/shell/src/renderer/` (`renderer.js`, `upload/state.js`, `notary/case-drafting-*.js`, `notary/error-catalog.js`) -- renderer vanilla, state hand-rolled, catalog lỗi VI; overlay DevMode bám vào đây.
- `D:/systemdocs-spike-visual-bug/shell/src/main/redact.js` -- `makeLogger`, `redactString/Object`; reuse cho report.
- `D:/systemdocs-spike-visual-bug/shell/test/test_upload_e2e.py`, `test_upload_browser_workflow.py` -- mẫu Playwright `connect_over_cdp`; reuse cho tái hiện e2e.
- `D:/systemdocs-spike-visual-bug/shell/package.json` -- `electron ^31`, `node --test`, `electron-builder --dir`; không thêm dep production.

## Tasks & Acceptance

**Execution:**
- [ ] `shell/src/renderer/devmode/bug-overlay.js` -- overlay chọn element (highlight, CSS path, rect, outerHTML rút gọn, ô ghi chú) -- rationale: entry UX "chỉ vào lỗi, nói một câu".
- [ ] `shell/src/preload/preload.js` -- thêm kênh DevMode dev-only (bật/tắt, gửi report, lấy console buffer) sau allowlist hiện tại -- rationale: giữ sandbox, không mở IPC rộng.
- [ ] `shell/src/main/devmode-report.js` -- nhận context, áp `redact.js` + `collectDiagnostics()`, ghi report JSON+MD ra `docs/tmp/bug-reports/` -- rationale: agent đọc trực tiếp qua filesystem.
- [ ] `shell/test/bug-report-spike.test.mjs` -- test redaction, schema report, mapping element thiếu định danh -- rationale: kiểm chứng không secret, không crash.
- [ ] `shell/test/bug-report-e2e.py` -- Playwright CDP mở app, click 1 element mẫu, sinh report giả lập, assert agent đọc được component/source -- rationale: chứng minh loop tái hiện.
- [ ] `docs/tmp/bug-report-spike-comparison.html` -- so sánh A/B/C + evidence + recommendation + arch + plan -- rationale: deliverable đọc nhanh thay vì text dài.

**Acceptance Criteria:**
- Given app chạy dev-mode trên worktree, when bật DevMode chọn 1 element và ghi chú ngắn, then sinh report JSON+MD dưới 2 phút thao tác với screenshot (hoặc `screenshot:missing` có lý do) và đủ field để xác định file nguồn.
- Given report mẫu không giải thích thêm, when agent đọc, then chỉ ra đúng file/component liên quan và đề xuất bước tái hiện bằng Playwright.
- Given report chứa token giả và đường dẫn user, when chạy test quét, then không còn secret trong file output.
- Given build production, when kiểm tra DevMode, then overlay/IPC mới không tồn tại hoặc bị vô hiệu hóa.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Design Notes

Luồng đề xuất: user chọn element → overlay thu DOM context + note → preload chuyển qua IPC dev-only → main enrich (diagnostics tail, state subset an toàn, screenshot) → redact → ghi `docs/tmp/bug-reports/<id>.json|.md` → coordinator/worker đọc file, tái hiện bằng Playwright CDP. Ready-made chỉ dùng nếu chạy được trong cửa sổ Electron thật; React Grab loại sớm vì renderer vanilla không có component map.

## Verification

**Commands:**
- `node --test test/bug-report-spike.test.mjs` -- expected: toàn bộ test pass, không secret trong fixture output.
- `python test/bug-report-e2e.py` -- expected: mở app qua CDP, sinh 1 report mẫu, agent xác định đúng file nguồn.
- Mở app dev -- expected: menu DevMode chỉ hiện ở dev, production không đổi.
