---
title: 'Gom toàn bộ tài liệu notary_v2 vào cây spec chung'
type: 'refactor'
ticket: ''
created: '2026-09-29'
status: 'built'
route: 'full'
route_source: 'auto'
baseline_revision: '5c5897005e059507aae840c85d314696de3eb21c'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
context:
  - 'AGENTS.md'
  - 'README.md'
  - 'docs/spec/README.md'
  - 'docs/spec/notary_v2/README.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `notary_v2/docs/` còn 38 file và tự chia theo `domains/platform/superpowers`, nên người đọc vẫn phải chọn giữa cây này và `docs/spec/notary_v2/`. Một số file là SOT cũ, bản nháp, kế hoạch hoặc bằng chứng lịch sử nhưng nằm cạnh nhau như tài liệu đang dùng.

**Approach:** Chuyển nội dung còn giá trị vào cấp nhỏ nhất trong `docs/spec/notary_v2/`, record task hoặc contract/source tương ứng; sau đó xóa toàn bộ `notary_v2/docs/` và sửa các đường dẫn đang dùng.

## Boundaries & Constraints

**Always:** Giữ nguyên trạng thái Active/Draft/Superseded, lý do, ví dụ, ngoại lệ, nguồn và ngày; bản Draft không được nâng thành Approved. Một quy tắc chỉ có một nơi sở hữu. Phụ lục lớn phải được README cha giải thích rõ.

**Never:** Không đổi hành vi sản phẩm, contract hoặc code runtime; không tự giải quyết mâu thuẫn nghiệp vụ thừa kế; không sửa record task cũ để làm sai lịch sử; không tạo cây tài liệu song song mới.

## I/O & Edge-Case Matrix

| Trường hợp | Trạng thái đầu vào | Kết quả |
|---|---|---|
| Quy tắc đang dùng | Active/đã duyệt | Nhập vào spec feature gần nhất, giữ nguồn |
| Đề xuất chưa duyệt | Draft/proposed | Giữ trong spec gần nhất với nhãn Draft hoặc `[CONFIRM]` |
| Phụ lục lớn | Catalog, rule field, engine, provenance | Giữ file con có vai trò rõ và link từ README cha |
| Kế hoạch/bằng chứng thực thi | Plan, audit snapshot, validation log | Tóm tắt vào task record phù hợp hoặc Git history; không làm SOT |
| Hai file mâu thuẫn | Không có nguồn chốt | Ghi rõ mâu thuẫn, không chọn thay owner |

</frozen-after-approval>

## Code Map

- `notary_v2/docs/**` -- 38 file nguồn: khoảng 6.000 dòng; gồm spec thật, Draft, tài liệu kỹ thuật và lịch sử lẫn nhau.
- `docs/spec/notary_v2/**` -- SOT đích hiện có theo flow Input → Stage → Pool → Diagram → Word.
- `notary_v2/docs/domains/inheritance/**` -- nghiệp vụ lớn nhất; `workflow.md` là hiện trạng web, hai bản business spec vẫn Draft, technical/research chứa phụ lục và bằng chứng.
- `notary_v2/docs/platform/**` -- intake, workspace, Word, fast-audit và consumer Zalo; nhiều phần đã được tóm tắt nhưng chưa chuyển hết.
- `notary_v2/docs/superpowers/**` -- kế hoạch và bản nháp lịch sử; không được tiếp tục làm SOT.
- `contracts/**`, `shell/**`, `zalo/docs/**`, `notary_v2/zalo_connector/README.md` -- các nơi đang trỏ vào đường cũ.
- `notary_v2/tests/test_docs_structure.py` -- test hiện còn bắt buộc cây `notary_v2/docs`; phải đổi sang cây trung tâm.

## Tasks & Acceptance

**Execution:**
- [x] `docs/spec/notary_v2/input/**` -- nhập spec OCR thủ công, quy tắc tài sản và CAP/T consumer Zalo; giữ `property-rules.md` là phụ lục lớn.
- [x] `docs/spec/notary_v2/{README.md,stage.md,pool.md,diagram/**}` -- nhập workspace, workflow, UI riêng, Stage-sync và câu hỏi mở vào đúng feature.
- [x] `docs/spec/notary_v2/diagram/inheritance/**` -- đổi feature thừa kế thành thư mục; giữ một bản business-rules Draft mới nhất, engine và catalog/provenance là phụ lục; ghi rõ mâu thuẫn chưa chốt.
- [x] `docs/spec/notary_v2/word-output.md` và `fast-text-audit.md` -- hợp nhất hành vi Word/renderer vào một spec; đưa CLI audit độc lập vào bản đồ module.
- [x] `.agent/tasks/**` và `docs/spec/**` -- giữ kết luận POC/audit/plan cần truy vết ở record phù hợp; phần thô đã có Git history không tiếp tục nằm trong cây sản phẩm.
- [x] `notary_v2/docs/**` -- xóa sau khi lập bảng đối chiếu nguồn → đích và xác nhận không mất quy tắc có hiệu lực.
- [x] `contracts/**`, `shell/**`, `zalo/docs/**`, `notary_v2/**` -- thay mọi đường dẫn đang dùng; không sửa câu mô tả lịch sử trong record task cũ.
- [x] `notary_v2/tests/test_docs_structure.py` -- kiểm cây trung tâm tồn tại, `notary_v2/docs` không còn, và các link local không gãy.

**Acceptance Criteria:**
- Given người đọc bắt đầu ở root README, when đi tới một feature `notary_v2`, then chỉ có một đường đọc dưới `docs/spec/notary_v2/`.
- Given một nội dung cũ là Draft hoặc lịch sử, when được chuyển, then trạng thái và nguồn vẫn rõ và không được hiểu là quy tắc đã duyệt.
- Given thay đổi hoàn tất, when tìm đường `notary_v2/docs`, then không còn tham chiếu vận hành hoặc SOT và thư mục đó không còn tồn tại.
- Given test và validator hiện có chạy, when kiểm tra tài liệu/contract, then tất cả đều đạt và runtime không đổi hành vi.

## Implementation Notes

## Plan Change Log

## Review Triage Log

| Lens / vị trí | Verdict | Bằng chứng và xử lý |
|---|---|---|
| Blind `README.md:23` | low / patch | Cây chỉ `zalo.md` đã chuyển; sửa thành `zalo/`. |
| Blind `contracts/README.md:89` | medium / patch | Dẫn nguồn tới spec không chứa quy tắc; giữ quy tắc cấp hệ thống ngay tại đây. |
| Blind `zalo/docs/spec-producer.md:4` | low / patch | CAP-01..16 không còn ở consumer §2; ghi rõ file cũ và Git baseline. |
| Blind `inheritance/README.md:3` | medium / patch | Contract Approved khác `engine.md` thiết kế đích; ghi rõ trạng thái và mâu thuẫn `incomplete` chưa chốt, không đổi hành vi. |
| Blind `word-output.md:36` | medium / patch | Chưa có gate status trong contract Word; ghi câu hỏi mở, không tự thêm cổng chặn. |
| Blind `web-workflow.md:13,28` | low / patch | `plan.md` và `drafting-tab.md` đã chuyển/xóa; dẫn Git, task và `workspace-detail.md`. |
| Blind `visual-reference.md:75,116` | low / patch | Tên `drafting-tab.md` cũ; dẫn `workspace-detail.md` đúng mục. |
| Blind `business-rules.md:598` | low / patch | Chỉ dẫn thêm case vào catalog cũ; đổi tới `examples.md`, giữ tên lịch sử trong bảng phản biện. |
| Blind `examples.md:15` | low / patch | Tên provenance và fixture tương đối cũ; đổi tới vị trí hiện tại. |
| Blind `test_docs_structure.py:51` | medium / patch | Test chỉ quét năm README và `.md`; mở rộng mọi Markdown/link local trong cây module. |
| Edge `contracts/README.md:89` | medium / patch | Cùng vấn đề nguồn quy tắc của Blind; đã sửa. |
| Edge `test_docs_structure.py:56` | medium / patch | Cùng lỗ hổng link của Blind; đã sửa. |
| Edge `open-issues-v1-legacy.md` | low / patch | Zalo note nói file vẫn ở `notary_v2`; đổi thành chỉ còn ở Git baseline. |
| Verify `README.md:23` | low / patch | Cùng đường dẫn cây của Blind; đã sửa. |
| Verify `baseline-open-issues.md:7` | low / patch | Cùng ghi chú lịch sử Zalo của Edge; đã sửa. |
| Intent `đường đọc` | medium / patch | Cây chung đã có; các đường dẫn chữ thuần còn sống được rà bằng `rg` và sửa; đường lịch sử ghi rõ baseline. |
| Intent `giữ ý nghĩa 38 file` | maybe-false / defer | Mapping ở handoff; không có phép kiểm tự động chứng minh ngữ nghĩa của mọi đoạn. Cần owner duyệt nội dung trước khi coi các Draft là hiệu lực; không tự chốt trong lần gom tài liệu. |
| Intent `test chưa bao phủ phụ lục` | medium / patch | Mở rộng test link toàn cây module; kiểm thủ công nội dung và status vẫn cần thiết. |

## Design Notes

Không sao chép nguyên 6.000 dòng. Mỗi file nguồn được đối chiếu: phần có hiệu lực được nhập, phần trùng bị bỏ, phần lịch sử chỉ giữ kết luận và đường truy vết Git/task. Kết quả ưu tiên ít file nhưng không biến một README thành kho hỗn hợp.

## Verification

**Commands:**
- `rg` kiểm không còn đường dẫn vận hành tới `notary_v2/docs`.
- `python -m pytest notary_v2/tests/test_docs_structure.py -q` -- test cấu trúc đạt.
- Ba validator trong `contracts/g1`, `contracts/notary-case-drafting`, `contracts/zalo-intake` -- không có kết quả bất ngờ.
- Kiểm toàn bộ link local trong Markdown thay đổi và `git diff --check` -- không lỗi.
