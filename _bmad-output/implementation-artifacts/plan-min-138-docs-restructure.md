---
title: 'MIN-138 - Gom spec theo tính năng và rút gọn tài liệu'
type: 'refactor'
ticket: 'MIN-138'
created: '2026-09-29'
status: 'built'
route: 'full'
route_source: 'auto'
baseline_revision: 'ac3d2341a9a61735aa90e04cc19742c4a9347a73'
review: 'thorough'
review_source: 'auto'
lenses_ran:
  - 'blind-hunter'
  - 'edge-case-hunter'
  - 'verification-gap'
  - 'intent-alignment'
review_loop_iteration: 0
context:
  - 'D:/systemdocs/AGENTS.md'
  - 'D:/systemdocs/README.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Tài liệu hiện chia theo loại file và issue. Muốn hiểu một tính năng, agent phải ghép nhiều nơi, dễ dùng nhầm bản nháp hoặc làm mất lý do nghiệp vụ.

**Approach:** Dựng một cây `docs/spec/` theo hệ thống → module → flow → tính năng nhỏ. Kiến trúc, giao diện, câu hỏi mở và lịch sử lựa chọn nằm ngay trong spec ở cấp nhỏ nhất mà chúng ảnh hưởng. `README.md` là bản đồ duy nhất; `AGENTS.md` chỉ giữ luật tìm và cập nhật đúng cấp.

## Boundaries & Constraints

**Always:** Viết ngắn, rõ, bằng tiếng Việt. Giữ nguyên ý owner, ví dụ, ngoại lệ, nguồn, ngày và trạng thái duyệt. Một quy tắc chỉ có một nơi sở hữu. Đặt thông tin tại cấp nhỏ nhất chứa đủ phạm vi ảnh hưởng: feature, nhóm flow, module hoặc toàn hệ thống. Đọc từ README gốc qua các cấp cha tới spec lá trước khi sửa.

**Never:** Không tạo file riêng chỉ vì nội dung mang tên architecture, design, decision hoặc open question. Không đổi runtime, contract đã duyệt hoặc hành vi sản phẩm. Không coi draft, plan hay code là quyết định đã duyệt. Không xóa kiến thức chỉ để giảm số file. Không tạo bản đồ thứ hai ngoài `README.md`.

## I/O & Edge-Case Matrix

| Tình huống | Đầu vào / trạng thái | Kết quả cần có | Cách xử lý |
|---|---|---|---|
| Tra một tính năng | Tên module hoặc feature | `README.md` dẫn thẳng tới một spec chính | Link sai hoặc vòng lặp làm kiểm tra thất bại |
| Kiến trúc/câu hỏi của một feature | Chỉ ảnh hưởng một chức năng | Ghi thành mục trong spec của chức năng đó | Không đẩy lên module hoặc tạo file riêng |
| Kiến trúc/câu hỏi dùng chung | Ảnh hưởng nhiều feature hoặc module | Ghi tại README của cấp cha gần nhất | Nêu rõ phạm vi; không chép xuống từng con |
| Quyết định cũ | Nội dung đã chốt, draft hoặc đã thay thế | Giữ trạng thái, lý do và lịch sử ngắn trong spec sở hữu | Không rõ nguồn thì ghi `[CONFIRM]`, không tự chốt |
| Chi tiết lớn | Bảng trường, contract, bằng chứng kiểm thử | Tách file tham chiếu, spec chính giải thích vai trò | Không chép lại thành SOT thứ hai |

</frozen-after-approval>

## Code Map

- `AGENTS.md` -- luật cấp monorepo; hiện chứa cả bản đồ và mô tả repo cần chuyển sang README.
- `README.md` -- cửa vào hiện tại; sẽ thành bản đồ duy nhất cho module, feature, trạng thái và nơi sở hữu.
- `docs/architecture/*.md` -- tầm nhìn, kiến trúc, công nghệ, bản đồ và quyết định sẽ nhập vào cấp spec tương ứng.
- `docs/product/*.md`, `docs/product/specs/*.md`, `docs/product/plans/*.md` -- spec hiện hành, draft, baseline và plan theo issue đang nằm chung.
- `docs/product/ui/**` -- quy tắc giao diện dùng chung hoặc riêng; nhập vào cấp hệ thống, module hoặc feature tương ứng. Prototype và ảnh vẫn là tài sản tham chiếu.
- `notary_v2/docs/**`, `upload_lab/docs/**`, `notaryoffice/intent.md`, `zalo/docs/**` -- nguồn chi tiết để đối chiếu; chỉ sửa cửa vào/link khi quyền sở hữu chuyển.
- `contracts/**` -- contract giữ nguyên nội dung; chỉ cập nhật link sau di chuyển.
- `.agent/templates/**`, `.agent/tasks/MIN-138/**` -- mẫu đường dẫn và hồ sơ thực thi của task.

## Tasks & Acceptance

**Execution:**
- [x] `.agent/tasks/MIN-138/` -- tạo `brief.md`, `progress.md`, `decisions.md`, `handoff.md`; ghi tiến độ và bằng chứng.
- [x] `AGENTS.md`, `README.md` -- rút luật; dựng cây spec duy nhất; bắt buộc agent đọc đường từ gốc tới spec lá và ghi kiến trúc/câu hỏi vào cấp cha gần nhất bao phủ phạm vi.
- [x] `README.md` -- ghi cấu trúc chuẩn của feature nhỏ: công dụng, người dùng/thao tác, input, output, flow, quy tắc và “Tại sao?”, trạng thái/dữ liệu, contract, kiến trúc/công nghệ, giao diện, lỗi/ngoại lệ, ví dụ, câu hỏi mở, lịch sử và nguồn.
- [x] `docs/spec/README.md` -- gom tầm nhìn, mục tiêu, ranh giới, flow, kiến trúc, công nghệ, câu hỏi và lịch sử ở cấp toàn hệ thống.
- [x] `docs/spec/notary_v2/**` -- tổ chức theo `Input → Stage → Pool → Diagram → Word`; feature lớn thành thư mục, feature nhỏ thành một spec; tích hợp nghiệp vụ, UI, dữ liệu, kiến trúc và quyết định tại đúng cấp.
- [x] `docs/spec/upload_lab/**`, `docs/spec/notaryoffice/**` -- tổ chức theo flow thật của từng module bằng cùng quy tắc phạm vi.
- [x] `docs/spec/**` -- giữ prototype, ảnh, bảng trường hoặc catalog lớn như tài sản/phụ lục chỉ khi spec chính giải thích rõ vai trò; không biến chúng thành SOT thứ hai.
- [x] `docs/architecture/**`, `docs/product/**`, `docs/maintenance/**` -- chuyển nội dung có giá trị, bỏ bản lặp và plan cũ khỏi tài liệu dài hạn; không để hai SOT cùng hiệu lực.
- [x] `notary_v2/**`, `upload_lab/**`, `notaryoffice/**`, `zalo/**`, `shell/**`, `contracts/**`, `.agent/templates/**` -- cập nhật link và lời chỉ đường bị ảnh hưởng.
- [x] `.agent/tasks/MIN-138/progress.md`, `.agent/tasks/MIN-138/handoff.md` -- ghi kết quả, kiểm tra và phần chưa chắc.

**Acceptance Criteria:**
- Given tên một feature, when đọc cây trong `README.md`, then người đọc đi qua đúng các cấp cha tới một spec chính mà không phải tự chọn giữa nhiều SOT.
- Given kiến trúc hoặc câu hỏi mới, when xác định phạm vi ảnh hưởng, then agent ghi vào spec lá hoặc README cha gần nhất; không tạo file architecture/decision riêng.
- Given một feature nhỏ như Nhập liệu, when mở spec, then có đủ công dụng, thao tác, input/output, flow, quy tắc, dữ liệu, contract, công nghệ, lỗi, ví dụ, câu hỏi, lịch sử và nguồn.
- Given tài liệu cũ có lý do, ví dụ, ngoại lệ hoặc trạng thái, when đối chiếu bản mới, then các ý đó còn nguyên nghĩa và có nguồn.
- Given toàn repo sau di chuyển, when chạy kiểm tra link và tìm đường dẫn cũ, then không còn link Markdown hỏng hoặc tham chiếu SOT cũ chưa xử lý.
- Given thay đổi MIN-138, when xem diff, then không có file runtime hoặc contract semantics bị sửa.

## Implementation Notes

- Tạo 15 spec/README mới dưới `docs/spec/`; chuyển nguyên trạng asset UI.
- Xóa 31 Markdown cũ ở root docs và 3 ADR rời sau khi nhập rule còn hiệu lực;
  lịch sử giữ trong Git/Linear.
- Contract chỉ đổi lời dẫn/link, không đổi schema hoặc semantics.
- Kiểm tra: `git diff --check` sạch; stale-path search sạch; Markdown đổi/mới
  không có link local thiếu; docs structure 4 passed/1 skipped; validator G1,
  Notary và Zalo Draft có 0 kết quả bất ngờ. Review không hoãn việc nào.

## Plan Change Log

## Review Triage Log

| ID | Verdict | Evidence và xử lý |
|---|---|---|
| VG-1 | medium · patch | Ba comment `.py/.js` còn trỏ cây cũ; đã đổi sang `docs/spec` và mở rộng stale-path check cho JS/Python. |
| BH-1 | high · patch | Header contract Zalo ghi Draft nhưng tài liệu mới gọi Approved; đã đồng bộ mọi nơi về Draft MIN-92 và cấm code production trước publish. |
| BH-2 | high · patch | `word_export_batch` schema cấm `base_revision`; đã bỏ field khỏi Word spec. |
| BH-3 | high · patch | Contract cho phép render result `incomplete`; đã sửa spec: chỉ `invalid` chặn save. |
| BH-4 | high · patch | `IdentityEvidence` bị gọi là đã publish dù nguồn MIN-62 là Draft; đã khôi phục field set Draft ở spec hệ thống và sửa binding G1. |
| BH-5 | medium · patch | Ba link chỉ sai mục 3 thay vì mục 4; đã sửa số mục. |
| BH-6 | medium · patch | Domain `two_party` thiếu rule đã duyệt; đã thêm spec riêng về A/B, 30 slot, giữ slot, swap, no-inheritance và Word unsupported. |
| BH-7 | medium · patch | `notaryoffice/intent.md` tự nhận SOT song song; đã hạ thành phụ lục chi tiết và route về spec mới. |
| BH-8 | medium · patch | Case Workspace cũ vẫn tự nhận SOT; đã đổi thành nguồn chi tiết/đối chiếu và route quyền sở hữu về cây mới. |
| BH-9 | medium · patch | Trạng thái UI/token và button 36 px mâu thuẫn; đã tách rõ phần Approved/Proposed và dùng button 32/28 px. |
| BH-10 | medium · patch | UI spec mới thiếu dirty/conflict/busy/partial/four faces; đã nhập các rule này vào `docs/spec/ui/README.md`. |
| BH-11 | medium · patch | Ràng buộc DB hội tụ bị mất; đã nhập lại rule SQLite-portable, UUID, ISO time, field names và config. |
| BH-12 | high · patch | Danh sách đường Internet và cảnh báo dữ liệu CCCD bị mất; đã nhập lại whitelist, owner và đánh dấu pháp lý `[CONFIRM]`. |
| BH-13 | medium · patch | Notaryoffice không có trạng thái duyệt rõ; đã ghi Draft `[CONFIRM]`, nguồn/ngày và thiếu bằng chứng duyệt toàn bộ. |
| EH-1 | high · patch | Stage spec thiếu retry key cho `workspace_create`; đã thêm UUID v4 ổn định để chống tạo Case trùng. |
| EH-2 | medium · patch | Diagram spec trộn input evaluate/save; đã tách payload và bỏ `case_type` tự do. |
| EH-3 | high · patch | Cùng lỗi Word `base_revision` như BH-2; đã kiểm với contract/schema và sửa. |
| EH-4 | medium · patch | Quota popup không xác định khi dùng chung Windows account; đã ràng buộc rule vào A4 và giữ câu hỏi mở. |
| EH-5 | high · patch | File hoạt động còn dẫn `DESIGN` đã xóa; đã chuyển toàn bộ ref/comment/token note sang spec UI mới. |
| EH-6 | high · patch | Rule từ `EXPERIENCE` bị xóa khỏi owner spec; đã nhập lại và đổi mọi ref cũ. |
| EH-7 | medium · patch | Cùng xung đột SOT Case Workspace như BH-8; đã sửa quyền sở hữu. |
| EH-8 | low · patch | Input spec thiếu ví dụ; đã thêm suggestion có `source_refs` và ví dụ job `partial`. |
| EH-9 | high · patch | Cùng lỗi `IdentityEvidence` như BH-4; đã khôi phục trạng thái Draft và field set. |
| EH-10 | false | Chỉ comment/link trong file runtime đổi; không dòng thực thi hay hành vi runtime đổi. Handoff được diễn đạt rõ là “runtime behavior”. |
| IA-1 | medium · patch | Spec mới còn dựa vào nhiều file cũ tự nhận SOT; đã demote chúng thành phụ lục/bằng chứng và bổ sung các rule thiếu được reviewer nêu. |
| IA-2 | high · patch | Nén tài liệu làm mất một số lý do/trạng thái/ràng buộc; đã phục hồi các mục cụ thể về contract Draft, UI, DB, Internet và golden gate. |
| IA-3 | high · patch | Wording contract G1 làm đổi quyền sở hữu `IdentityEvidence`; đã trả về Draft cross-product và chỉ giữ binding G1. |
| IA-4 | false | User cho phép feature nhỏ nằm trong một file và chỉ tách khi cần; Upload/Notaryoffice hiện vẫn đủ nhỏ, còn Notary đã tách flow/feature. |
| SELF-1 | medium · patch | Test link module giả định mọi link nằm trong `notary_v2`; đã tìm Git root để kiểm được link sang cây spec monorepo. |

## Design Notes

Thư mục thể hiện phạm vi; README của thư mục là spec chung cho các con. Chỉ tạo file hoặc thư mục con khi có một chức năng độc lập đáng tra cứu. Không tách theo loại thông tin. Contract/schema máy đọc vẫn ở `contracts/`; spec sở hữu giải thích ý nghĩa và dẫn link.

## Verification

**Commands:**
- `rtk git diff --check` -- không có lỗi khoảng trắng.
- `rtk rg -n "docs/(architecture|product|maintenance)" -g "*.md" -g "*.json" -g "*.html" -g "*.css" -g "*.js" -g "*.py" .` -- mọi đường cũ còn lại đều được giải thích hoặc loại bỏ.
- Kiểm tra toàn bộ link Markdown nội bộ -- mọi đích file và anchor tồn tại.
- `rtk git diff --name-only` -- không có runtime ngoài thay đổi link tài liệu đã dự kiến.
