---
id: 18
type: spike
title: "Khôi phục bằng chứng và phân loại 12 report mất ghi chú"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Khôi phục bằng chứng và phân loại 12 report mất ghi chú

## Description

Giữ riêng mười hai UUID lịch sử và khôi phục phần bằng chứng còn lấy được. Chỉ hỏi người báo phần triệu chứng thực sự đã mất; đây là một việc lập kế hoạch/bằng chứng, không là mười hai bug đoán ra.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C17
- source — _bmad-output/tmp/review-37-reports-20261009/inventory.json, 12 non-E2E selections
- source — _bmad-output/implementation-artifacts/diagram-error-fix-20261009/open-reports.md, individual records and recovery limits
- source — bản gốc private còn dùng được (base pattern, dùng nguyên văn không rút gọn): `_bmad-output/tmp/debug-spike-source-backup/spike-visual-bug-reporting/_bmad-output/tmp/visual-bug-spike/custom/reports/<uuid>.json` và `_bmad-output/tmp/debug-spike-source-backup/spike-visual-bug-reporting/_bmad-output/tmp/visual-bug-spike/custom/reports/<uuid>.png`
- source — `_bmad-output/tmp/debug-spike-source-backup/spike-visual-bug-reporting/_bmad-output/tmp/visual-bug-linkage-evidence.json` (mục `omissions`, `implications`, `counts`)
- source — `_bmad-output/tmp/issues-reconciliation-20261015/report-inventory.json` (`missing_sources`, corpus có nhãn `historical-report-note-lost`)
- source — `_bmad-output/tmp/debug-spike-source-backup/spike-visual-bug-reporting/_bmad-output/tmp/bug-report-inventory.html`, `_bmad-output/tmp/debug-spike-source-backup/spike-visual-bug-reporting/_bmad-output/tmp/bug-repo/user12.txt`
- decision — decision-76 "Spike visual bug ghi chu nguoi dung nguyen van vao report local…" (accepted 10/10/2026; report cũ giữ nguyên, không sửa, không thể phục hồi) và decision-77 "visual-bug-report-phai-giu-vi-tri-va-comment" — trích theo **tiêu đề** vì `_bmad-output/decisions/` có hai file cùng `id: decision-76` và hai file cùng `id: decision-77`
- ledger — `_bmad-output/tmp/issue-18-report-note-triage/evidence.md`, `_bmad-output/tmp/issue-18-report-note-triage/static-ledger.json` (che dữ liệu, theo UUID), `_bmad-output/tmp/issue-18-report-note-triage/canonical.diff`

## Notes

- Tracking: C17; `refined: false` — **không** phải việc built/done và chưa chốt được phân loại. Điều tra phần lấy được **đã ghi xong** (17/10/2026); phần còn lại chỉ là chờ đầu vào người báo ("không còn cần" cũng là câu trả lời hợp lệ) → 12 record giữ **UNVERIFIED**, **0** record đóng. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Gộp hoặc đóng nhầm record làm mất dấu phản ánh người dùng; không sửa runtime.
- **Status (17/10/2026): REACHABLE INVESTIGATION RECORDED / 12 UNVERIFIED.** Điều tra phần lấy được đã xong; đây **không** phải #18 built/done, **không** đóng record nào, **không** phải quyết định nghiệp vụ owner. Điều kiện còn thiếu là **đầu vào từ người báo gốc** (điều kiện ngoài repo).
- Open question (**đã soạn, chưa gửi cho người báo — chưa ai trả lời**): người báo gốc **có thể** cung cấp thu hồi trí nhớ — triệu chứng + kết quả mong đợi — cho từng dòng R01–R12, hoặc đánh dấu "không còn cần". Không yêu cầu tên người, nội dung giấy tờ hay dữ liệu cá nhân; R11 chỉ cần triệu chứng, **không** cần tên người. Không phát lại để bác bỏ phản ánh; không đoán 12 bug.
- Ai chờ: việc phân loại/đóng đúng mười hai record này chờ câu trả lời trên. Nơi ghi đáp án canonical: Notes này + bảng 12 dòng ở [README C17](../backlog/README.md#mười-hai-report-lịch-sử-mất-ghi-chú--c17--18); bằng chứng chi tiết che dữ liệu ở ledger `_bmad-output/tmp/issue-18-report-note-triage/`. Việc độc lập không phải chờ: xem mục "Không thuộc #18" bên dưới.
- **Không thuộc #18:** flow lưu comment tự gõ đã built **riêng** (`_bmad-output/implementation-artifacts/plan-visual-bug-comment-capture.md`; harness hiện hành `tools/visual-bug-reporting/` giữ note nguyên văn; spec `_bmad-output/specs/shared/visual-bug-spike.md`). Lỗi console dòng 312 đã built **riêng** ở #4/C03; decision-77 chỉ ghi hai bug **độc lập**, **không** loại trừ dòng 312 khỏi 12 record này — **không đủ căn cứ để quy nguyên nhân cho từng record này hoặc suy nguyên nhân chung**. Không mở lại hai việc đó ở đây.

### Kết quả điều tra (17/10/2026) — bounded: nguồn leaf dẫn + bản sao private còn dùng được

- **AC1 — bằng chứng còn lấy được:** chỉ **vị trí** — `selector` + `rect` (x,y,w,h) + `viewport`, kèm `mtime` file. Mười hai record giữ đúng **12 UUID**, không gộp, **không đủ căn cứ suy nguyên nhân chung**.
- **AC1b — phần thật sự không lấy được:** lời mô tả tự gõ **không được lưu** vào report: field `note` của đúng 12 record này (và 7 fixture) chỉ còn marker `[note omitted: synthetic vocabulary only]` — **19/37** file report đã lưu giữ nguyên chuỗi marker này, nên **không có văn bản nào khôi phục được trong 4 nguồn đã kiểm**. Cơ chế "thay note khác 3 câu mẫu bằng marker" là **ghi chép lịch sử** (decision-77, hai mục ghi ngày 09/10/2026: "Bản thử hiện tại…" dòng 15 và "Code đã đối chiếu" dòng 22), **không** phải suy ra từ file policy hiện có: hai bản `custom/policy.cjs` còn dùng được trong repo (cây backup và `tools/visual-bug-reporting/`) là bản **post-fix**, cùng nội dung (chỉ khác CRLF), truyền `input.note` nguyên văn và **không** có mã thay marker → **không** chứng minh code cũ; nhánh cũ `D:/systemdocs-spike-visual-bug/…` (decision-77 dẫn) không còn tồn tại trên máy này (đã kiểm). Bốn nguồn đã kiểm đều là **bản sao dẫn xuất** (bản sao trong repo của 37 JSON — sha256 khớp 37/37 bản export review; `inventory.json`; corpus reconciliation; `bug-report-inventory.html`/`user12.txt`), **không** phải ground truth độc lập; kết luận **không** suy rộng thành "không còn bản nào ở mọi nơi".
- **AC1c — giới hạn phải nói đúng:** ảnh đã lưu là **wireframe không chữ/không màu/không giá trị** (đã xem trực tiếp) → nhãn "vị trí UI" trong bảng là **suy từ DOM**, **chưa** xác nhận triệu chứng. Không có timestamp trong report (chỉ `elapsedMs`); mốc trong bảng là **mtime file** (đổi múi giờ khi sao chép), **không** phải thời điểm report; `context.tab` luôn `unknown`. `synthetic: true` do công cụ gắn cho **cả 37** record → không chứng minh record do script bấm. `source.candidates` chỉ là tổ tiên/chrome (bộ 6 dòng giống nhau cho cả 12), không trỏ code phần tử được bấm.
- **AC1d — console không đủ căn cứ để quy nguyên nhân:** 4 record R09–R12 có cùng một dòng `error @ shell/src/renderer/notary/relationship-diagram.js:312`; bộ đệm console **dùng chung, không timestamp**, lỗi không bị xóa sau save/reload → **không đủ căn cứ để quy nguyên nhân cho từng record hoặc suy nguyên nhân chung** (không chứng minh được sự kiện riêng cho từng record). Dòng 312 đã built **riêng** ở #4/C03; decision-77 chỉ ghi hai bug **độc lập** với nhau và **không** loại trừ dòng 312 khỏi 12 record này. 8 record còn lại có console rỗng.
- **AC2 — bên chờ / nơi ghi / việc độc lập:** bên chờ là **người báo gốc** (cung cấp thu hồi trí nhớ; điều kiện ngoài repo) — **không** phải gate nghiệp vụ owner và **không** phụ thuộc Office (#14 deferred 17/10). Nơi ghi: Notes này + bảng 12 dòng ở README C17 + ledger che dữ liệu. Việc độc lập không chờ: flow lưu comment (đã built riêng) và #4/C03 (đã built).
- **AC3 — người nhận đúng phạm vi (đã soạn, **chưa gửi**):** câu hỏi một lần dạng bảng R01–R12 (vị trí đọc được theo tên chức năng, không cần nhớ mã file) **đã soạn xong nhưng chưa gửi** cho người báo — parent gửi ở bước cuối sau khi canonical/review xong, và **chưa có xác nhận đã nhận** nào được ghi ở đây. Người thao tác/reviewer nhận **bằng chứng đo** (rect/viewport/selector/console + các giới hạn trên). Mười hai record **giữ nguyên UNVERIFIED**; không phần Draft/Pending nào bị nâng trạng thái.

### Mười hai record độc lập (giữ nguyên trạng thái, chưa đóng)

Số R theo thứ tự file được tạo (khớp `report-map-readable.md`); nhãn vị trí là **suy từ DOM**. Giữ từng record chưa xác minh; **không đủ căn cứ để quy nguyên nhân cho từng record hoặc suy nguyên nhân chung**. Chi tiết rect/viewport/selector từng dòng: bảng ở [README C17](../backlog/README.md#mười-hai-report-lịch-sử-mất-ghi-chú--c17--18) và `static-ledger.json`.

| # | UUID | Trạng thái | Cần ở người báo |
|---|---|---|---|
| R01 | `534545cf-f020-4e22-8e03-362294f72508` | UNVERIFIED | màn đó gặp vấn đề gì |
| R02 | `377d8486-e885-4a21-8e84-497241546eaa` | UNVERIFIED | khối/popup lệch, quá cao hay thiếu nội dung |
| R03 | `bb496551-82b6-4f72-bd80-77df2e396e2f` | UNVERIFIED | bấm Lưu hồ sơ thì kết quả khác mong muốn thế nào |
| R04 | `0d1b1ff1-73ce-4e8b-a6bf-2c695f06dd3f` | UNVERIFIED | phần gợi ý địa chỉ sai thế nào |
| R05 | `60e02a79-727d-4de3-be7f-488b3f1a39ee` | UNVERIFIED | ô Địa chỉ bị kéo cao / sai nội dung / thao tác |
| R06 | `2f352897-ab9b-4f11-84e4-a44c43145bf0` | UNVERIFIED | ô Loại sổ: sai giá trị / không nhập được / sai bố cục |
| R07 | `b5999b39-dce5-48dc-954a-66d231cce6ee` | UNVERIFIED | Người nhận ủy quyền: ô tên hay nút bị gì |
| R08 | `5db58074-cf8b-4a67-ab5a-09c0dd449a94` | UNVERIFIED | ô Giới tính: sai lựa chọn / sai kích thước / không chọn được |
| R09 | `643496a0-c4a4-4e5a-ab2f-bbbfa39d438a` | UNVERIFIED | dòng Địa chỉ người hiện chữ gì và sai ở đâu |
| R10 | `e3bba3ef-0f1f-4730-a505-cf0d282b75b1` | UNVERIFIED | Nơi cấp giấy tờ: giấy nào, mong hiện/tra thế nào |
| R11 | `aaf29f16-68b4-4a92-b15c-b811043d9c80` | UNVERIFIED | thẻ Sơ đồ: sai nhánh / bị che / không bấm được (không cần tên người) |
| R12 | `6714de6f-0049-4b4c-8d0d-2a2b179f15d9` | UNVERIFIED | dải thông báo: nội dung là gì, muốn đổi thế nào |

### Review độc lập

- **Independent Quick (retained t1 → t3), doc-only, 17/10/2026:** t1 — ba phát hiện của lượt review đầu ("không phải nguyên nhân" như một chứng minh phi nhân quả; AC3 nói "người báo nhận" khi câu hỏi chưa được gửi; Tracking "chưa duyệt bắt đầu" mâu thuẫn với điều tra đã ghi) — đã vá. t2 — provenance cơ chế: note mất theo **ghi chép lịch sử** (decision-77 dòng 15/22) + **19/37** marker đã lưu, **không** suy từ file policy còn dùng được (hai bản `custom/policy.cjs` là bản **post-fix**). t3 **CLEAN** sau khi vá nốt một dòng JSON residual trong ledger tmp (bỏ khẳng định "picker chỉ đưa 3 câu mẫu" mà decision-77 dòng 15 không hỗ trợ → thay bằng luật giữ lại ba chuỗi mẫu).
- **Trạng thái sau review:** 12 record giữ **UNVERIFIED**, **0** record đóng; **phân loại NOT done**; câu hỏi một lần **đã soạn nhưng chưa gửi** — chỉ gửi khi parent chốt bước cuối, và **không** ghi nhận đã nhận/đã trả lời. Giới hạn thuần docs — không runtime/code/test/đo lại, không đóng 12 record, không nâng Draft/Pending.
