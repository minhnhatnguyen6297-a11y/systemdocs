---
title: 'Sửa thông báo lỗi sơ đồ và kiểm thử đúng cách nạp Electron'
type: 'bugfix'
ticket: ''
created: '2026-10-09'
status: 'draft'
baseline_revision: 'e7094312e212578e0d129d599edd5617ca0adf64'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'auto'
lenses_ran: []
review_loop_iteration: 0
execution_authorized: false
context:
  - '_bmad-output/specs/notary_v2/README.md'
  - '_bmad-output/specs/notary_v2/diagram/README.md'
  - 'contracts/notary-case-drafting.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Sơ đồ lấy hàm `.relErrText` không tồn tại từ danh mục lỗi. Khi đánh giá, dựng danh sách lỗi hoặc lưu bị lỗi, màn hình ném `TypeError` thay vì thông báo. Test hiện tại vẫn xanh vì đi qua hàm dự phòng.

**Approach:** Giữ tên biến `relErrText`, lấy hàm `.errText` có sẵn; thêm test nạp đúng danh mục lỗi và kiểm chứng trong Electron thật. Khôi phục cách báo lỗi đã có, không đổi nghiệp vụ.

## Boundaries & Constraints

**Always:** Giữ dữ liệu người dùng đang nhập; giữ các trường hợp xử lý riêng của `diagram_invalid_state` và `workspace_conflict`; dùng dữ liệu giả, thư mục thử riêng; tuân thủ AGENTS.md và BMAD. Điều phối chỉ dùng Orca nếu cần.

**Never:** Đổi biến ngoài cùng thành `errText`; thêm export `.relErrText`; dùng catch rỗng để che lỗi; đổi engine, schema, Stage/Pool, bố cục hoặc công cụ báo lỗi. Không đóng 12 report thiếu mô tả. Không reset, stash, dọn worktree, commit file người khác, push hoặc merge.

## I/O & Edge-Case Matrix

| Tình huống | Đầu vào | Kết quả cần giữ |
|---|---|---|
| Đánh giá lỗi | `ok:false`, `stage_validation_error` | Thông báo từ danh mục lỗi; không TypeError |
| Tự đánh giá sau thao tác | Cùng lỗi, chạy sau 500 ms | Không Promise lỗi bị bỏ mặc |
| Dựng danh sách lỗi | `diagramErrors` có phần tử | Hiện lỗi và giữ màn hình soạn |
| Lưu lỗi thông thường | `workspace_locked` trả sau khi bấm | Thông báo; bản nháp còn nguyên |
| Sơ đồ chưa hợp lệ | `diagram_invalid_state` | Lỗi dưới sơ đồ; không toast riêng |
| Lưu xung đột phiên bản | `workspace_conflict` | Luồng xung đột hiện có; không toast riêng |
| Thành công | evaluate/save `ok:true` | Giữ kết quả tính và cách lưu hiện có |
| Hai bên A/B | `domain:two_party` | Không tự đánh giá bằng engine thừa kế |
| Nạp độc lập trong Node | Không có `window`/danh mục lỗi | Hàm dự phòng còn dùng được |

</frozen-after-approval>

## Code Map

- `shell/src/renderer/index.html:25–28`: nạp error-catalog trước sơ đồ trong cùng phạm vi script.
- `shell/src/renderer/notary/error-catalog.js:250–260`: export thật có `errText`; chỉ đọc.
- `shell/src/renderer/notary/relationship-diagram.js:47–49`: chỗ sửa; ba nơi dùng ở 312, 1278, 1333.
- `shell/src/renderer/notary/case-drafting-model.js:1334–1423`: lưu trạng thái lỗi/draft; `emit:451–469` nuốt lỗi từ hàm dựng màn hình. Chỉ đọc, không mở rộng sửa.
- `shell/test/notary-diagram.test.mjs:11–17,91–98`: cách require hiện tại che lỗi; tái dùng `dom-stub.mjs`, không thay toàn bộ bộ test.
- `shell/test/notary-case-drafting-static.test.mjs:407–440`: đã có chặn trùng tên và kiểm tra thứ tự script.
- [Checklist kiểm chứng](./diagram-error-fix-20261009/acceptance.md), [report còn mở](./diagram-error-fix-20261009/open-reports.md), [bằng chứng đã tái hiện](./diagram-error-fix-20261009/review-evidence.json).

## Tasks & Acceptance

Làm tuần tự; giữ log trước/sau từng bước dưới `_bmad-output/tmp/diagram-error-fix-20261009/` trong checkout đang sửa.

- [ ] **T0 — Kiểm tra checkout:** đọc AGENTS.md, RTK.md, graphify và spec. Ghi HEAD, branch, trạng thái file; so lại ba chỗ gọi. Ba file bẩn của phiên trước nằm ở tài liệu spike; không đụng chúng. Nếu source/test mục tiêu có thay đổi người khác, chọn worktree do Orca quản lý hoặc báo vướng; không ghi đè.
- [ ] **T1 — Chứng minh test bắt được lỗi:** tạo `shell/test/notary-diagram-errors.test.mjs`. Nạp source thật bằng môi trường mới có `window.G1_NOTARY_ERRORS` thật **trước** sơ đồ; kiểm tra đánh giá, render lỗi, lưu lỗi. Trên source chưa sửa, test phải thất bại đúng `relErrText is not a function`; lưu log. Không dùng bộ export giả hay source đã sửa trong bộ nhớ cho test chính.
- [ ] **T2 — Sửa đúng gốc:** trong `relationship-diagram.js`, đổi duy nhất `window.G1_NOTARY_ERRORS.relErrText` thành `window.G1_NOTARY_ERRORS.errText`. Giữ tên alias và ba nơi gọi. Chạy lại test mới; phải đạt.
- [ ] **T3 — Kiểm tra ngoại lệ:** bổ sung kiểm tra các hàng còn lại của matrix vào test mới, tái dùng test cũ khi đã phủ đúng hành vi. Đối chiếu cả thông điệp và trạng thái; không chỉ kiểm tra “không throw”.
- [ ] **T4 — Kiểm chứng Electron:** tạo harness tạm `electron-check.cjs`, mở **shell thật của checkout đang sửa**, dùng mock dev và dữ liệu riêng. Làm đủ các bước ở acceptance.md; lưu ảnh, log, phiên bản và kết quả từng ca. Chrome probe cũ chỉ là bằng chứng tham khảo.
- [ ] **T5 — Review và bàn giao:** chạy bộ Node toàn shell, `git diff --check`, review BMAD phạm vi source/test. Ghi lệnh, kết quả, hạn chế và trạng thái 12 report. Commit riêng source/test cùng cập nhật plan thuộc task; không đưa file tạm vào commit.

**Acceptance Criteria:**

- Given script nạp theo index.html, when gây lỗi ở ba nơi gọi, then có thông điệp đúng và không `TypeError`/lỗi trùng tên.
- Given màn hình soạn có dữ liệu chưa lưu, when evaluate/save thất bại, then dữ liệu và trạng thái chưa lưu giữ nguyên; không ghi DB thành công giả.
- Given lỗi sơ đồ cần hiện dưới màn hình, when model phát cập nhật, then vùng soạn và danh sách lỗi thật vẫn hiện; không chỉ có state nhưng DOM trắng.
- Given test mới chạy trước bản sửa, when gọi hàm lỗi, then test thất bại đúng nguyên nhân; after sửa, các test đó đạt.
- Given Electron thật và dữ liệu thử riêng, when chạy checklist, then ca lỗi và ca lưu thành công có bằng chứng đầy đủ.
- Given kết quả bàn giao, when chủ dự án đọc, then thấy lỗi đã sửa và 12 report còn mở, không bị kết luận tất cả 37 đã hết lỗi.

## Design Notes

Sửa một thuộc tính vì cả ba nơi cùng dùng alias này. Tên alias riêng tránh trùng hàm toàn cục `errText`. Không đổi hành vi đã được spec chốt nên không cần thêm rule nghiệp vụ; nếu worker phát hiện cần đổi hành vi, ghi đề xuất riêng trước khi sửa.

## Verification

Chạy tại `<checkout>/shell`, mỗi lệnh riêng:

```powershell
rtk proxy node --test test/notary-diagram-errors.test.mjs
rtk proxy node --test test/notary-diagram.test.mjs test/notary-case-drafting-static.test.mjs test/notary-case-drafting-model.test.mjs test/notary-case-drafting-view.test.mjs
rtk npm test
```

Chạy harness Electron từ gốc checkout; nó phải tự suy ra checkout đang sửa:

```powershell
rtk proxy node _bmad-output/tmp/diagram-error-fix-20261009/electron-check.cjs
rtk git diff --check
rtk git status --short
```

Thiếu Electron/Playwright hoặc không chạy được ca native thì ghi **chưa đủ kiểm chứng**, không đánh dấu `done`. Nếu lỗi kiểm thử không liên quan, lưu bằng chứng đối chiếu trước/sau thay vì sửa lan ra ngoài phạm vi.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Quyền thực hiện và bàn giao

Đây là **Draft** lập theo yêu cầu giao việc, chưa bắt đầu sửa. User gửi nội dung trong `worker-message.md` là phê duyệt phạm vi cho worker; worker chuyển `ready-for-dev`, rồi thực hiện. Phiên lập plan không khởi chạy worker.

Baseline ngày 09/10/2026: `D:/systemdocs`, nhánh `consolidate/monorepo`, HEAD như frontmatter. Source gốc có hash trong review-evidence.json. Kiểm lại live; không giả định HEAD vẫn giữ nguyên khi worker bắt đầu.

Bàn giao cuối: commit SHA, danh sách file sửa, log test bắt lỗi trước/sau, kết quả Electron từng ca, ảnh lỗi và lưu thành công, lệnh chạy lại, các hạn chế, danh sách report còn mở. Giữ plan và hai log append-only ở trạng thái đúng với mức hoàn thành thực tế.
