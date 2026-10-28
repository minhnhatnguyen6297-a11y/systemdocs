---
id: 10
type: spike
title: "Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word

## Description

Spec Word hiện đã quy định ngoặc vuông, tên nhóm dễ đọc cho mẫu mới, các tên viết liền được hỗ trợ và alias cũ. Chỉ còn đối chiếu phạm vi câu bắt buộc tên viết liền ở entities §9.1 với hướng dẫn mẫu mới ở Word §4.1. Không mở tính năng cú pháp hoặc phát hiện literal mới.

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
- tracking — _bmad-output/backlog/README.md, C09
- source — _bmad-output/specs/notary_v2/word-templates.md, §4
- source — contracts/entities.md, §9.1
- source — _bmad-output/tmp/notary-word-recheck/syntax-evidence.md, historical parser evidence
- source — _bmad-output/tmp/notary-word-recheck/smoke-proof.json, real_api, direct_real_engine

## Notes

- Tracking: C09; answered 16/10/2026 ở DOC closeout (`entities.md` §9.1 nêu rõ phạm vi + cross-ref Word §4.1; không cần quyết định owner mới, không đổi parser/mapping). #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Hướng dẫn tên không rõ có thể khiến người viết mẫu dùng sai quy ước; không thay parser hay mapping.
- Open question (đã trả lời 16/10/2026): Quy định tên viết liền bắt buộc tại entities §9.1 chỉ áp cho tên trường nghiệp vụ hay cả placeholder và có lấn hướng dẫn Word §4.1 không? Đối chiếu nguồn đã có trước; chỉ hỏi owner nếu đúng điểm thẩm quyền này còn thiếu căn cứ.
- Đã rõ: ngoặc vuông và hỗ trợ tên dễ đọc/viết liền theo Word §4.1. Không mở câu hỏi hay implementation cho ngoặc nhọn, migration hoặc tự phát hiện literal. Ai chờ: chỉ sửa hướng dẫn đặt tên mâu thuẫn; #9 và dùng token hiện có không chờ. Nơi ghi: Notes và đúng đoạn Word/entities cần làm rõ nếu có.
- Trả lời (16/10/2026): câu blanket `contracts/entities.md` §9.1 nguyên văn bắt buộc viết liền và **nêu cả placeholder**, nên rộng hơn Word §4.1 hiện hành — đây là xung đột câu chữ thật, không phải suy diễn. Hành vi hiện hành theo spec canonical Word §4.1 (mẫu mới `[Tên danh sách N - Trường]`; tên viết liền canonical + alias cũ được thay/slot legacy); thẩm quyền: `AGENTS.md` (Hành vi → `_bmad-output/specs/`; spec quyết định hành vi), `_bmad-output/specs/notary_v2/word-templates.md` §3.3/§4.1, `_bmad-output/backlog/README.md` C09 (16/10/2026), `notary_v2/word_templates/placeholder_mapping.md`.
- Căn chỉnh (16/10/2026): `contracts/entities.md` §9.1 nêu rõ phạm vi — quy ước viết liền đặt tên **trường/khóa canonical + họ token compact**; mặt chữ placeholder **mẫu mới** theo Word §4.1 (thêm cross-ref ngắn tại Word §4.1). **Không** đổi parser/mapping/cú pháp; alias + ngoặc vuông giữ nguyên; **không** thêm/migrate/dò literal; **không** có quyết định owner mới và **không** tạo decision authority giả.
- Bằng chứng đo (16/10/2026): `_bmad-output/tmp/issue-10-word-naming-authority/evidence.md` (đối chiếu có ngày theo từng câu hỏi, nguồn/vùng dòng, phần không lấy được từ repo) + diff closeout `_bmad-output/tmp/issue-10-word-naming-authority/closeout.diff`.
- Ai chờ: **không ai** — không còn lựa chọn sản phẩm treo cho #10; #9/#24/#22/#25 và token hiện có không chờ. Independent review: `word-naming-authority-review` t1 nêu 2 finding (đều đã sửa) → **t2 CLEAN**; review docs-only, link đã kiểm, không có claim runtime.
