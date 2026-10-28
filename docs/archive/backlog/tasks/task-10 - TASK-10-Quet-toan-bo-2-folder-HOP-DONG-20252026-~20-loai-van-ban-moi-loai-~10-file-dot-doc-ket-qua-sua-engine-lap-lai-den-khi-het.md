---
id: TASK-10
title: >-
  TASK-10: Quet toan bo 2 folder HOP DONG 2025+2026 (~20 loai van ban) - moi
  loai ~10 file/dot, doc ket qua, sua engine, lap lai den khi het
status: In Progress
assignee: []
created_date: '2026-10-06 18:48'
updated_date: '2026-10-08 04:29'
labels: []
dependencies: []
ordinal: 10000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Moi loai van ban da chay it nhat 1 dot ~10 file qua engine + validator
- [ ] #2 Loi phat hien duoc sửa hoặc ghi nhan vao spec/backlog
- [ ] #3 Bao cao tong ket theo loai van ban
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
- [ ] #4 Spec regex-*.md cap nhat theo loai ho tro thuc te
- [ ] #5 Decision ghi lai quyet dinh khi sua engine
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
sweep-17 (offset 160): (a) '| |' split si?t la?i — chi t?ch tru?c nhan danh xung Ong:/Ba: (tranh be 'Tôi tên là: X; | | Sinh ngày'); (b) tien to 'Mẹ đẻ tôi:'/'Bố đẻ ông X là bà Y' + '+ Bà:' bullet; (c) ranh tên 'có' + so (Thăng có 01), '-sinh' dính; (d) dedupe tuong thich nam: '01/01/1932' vs '1932' gop. Ca 'Đơn xác nhận ông Hạnh': Cường+Vân+Nhi?u d?y d?; 'Khang-Phòng': Đằng+Thái them; danh sách l?p Sinh năm g?p. Tests 95+7.

TASK-10.1 Done: chuẩn luật trường + đáp án ở docs/spec/upload_lab/regex-fields.md và regex-expected-results.md; sửa phần closed, hai suite406/196 pass và Word4x7 mỗi bên. F01/F04/F05 vẫn pending theo regex-fields§8, không tính đạt. Chưa tiếp tục sweep; Hưng theo evidence cũ còn20 gap +185 cuối. Bàn giao .agents/task-10.1/RESULT.md.

TASK-10.2 và10.3 Done: Hưng3930–3979 kiểm từng trường/rerun50nguồn;76người/13mô tả đất;48file khớp trường đã kiểm,2source_review chữ dính. Quyết định74/spec regex-acceptance.md; engine2026-10-08-bounded-correctness. Mốc tiếp3980 (~135file);gap3910–3929 chưa kiểm từng trường và20coveragegapvịtrí10–29 giữ riêng. F01/F04/F05 Pending; folder2025khác/2026 chưa hoàn tất. Stage hiện có giữ chữ/sửa/lưu/mở lại đã kiểm; no new UI/typo rules. Chi tiết .agents/task-10.3/RESULT.md. Workingtree chưa commit; không dùng counts170 hoặc mốc3930 lịch sử làm hiện trạng.
<!-- SECTION:NOTES:END -->
