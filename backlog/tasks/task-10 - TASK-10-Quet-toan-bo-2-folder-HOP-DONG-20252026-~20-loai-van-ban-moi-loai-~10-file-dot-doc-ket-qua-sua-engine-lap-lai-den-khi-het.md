---
id: TASK-10
title: >-
  TASK-10: Quet toan bo 2 folder HOP DONG 2025+2026 (~20 loai van ban) - moi
  loai ~10 file/dot, doc ket qua, sua engine, lap lai den khi het
status: In Progress
assignee: []
created_date: '2026-10-06 18:48'
updated_date: '2026-10-06 21:27'
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
<!-- SECTION:NOTES:END -->
