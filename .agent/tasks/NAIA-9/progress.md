# NAIA-9 — tiến độ

04/10/2026: hoàn thành kho timeline local theo plan administrative-timeline.

- Ledger version 1.0: 3.355 units, 34 tỉnh, 3.321 xã, 0 huyện; 35 nguồn/snapshot
  raw có SHA-256. Ngày tải scratch chỉ ghi 2026-10-04, ngày hiệu lực giữ null.
- 136 quan sát giữ nguyên; 3.219 mentions/events pending; 161 dòng partial.
  Chưa phân tích văn xuôi thành danh tính lịch sử. Không tìm lịch sử cũ thay Owner.
- CLI import offline/refresh public/update revision/validate/query; giữ bằng
  chứng bất biến và lịch sử curator, atomically thay ledger khi hợp lệ.
- 27 tests timeline passed: rename A→B→C→D, merge/split/abolition, ba cấp,
  pending, same-name, code reuse, invalid refs/dates/cycle/overlap, failed write,
  manual retention, source corruption, full real data, JSON example.
- Spec Vietnamese và parent links hoàn tất, có hướng mở rộng chưa triển khai.
  Word/MIN-141, office DB, address UI và DOCX intake không đổi.

Root sẽ review diff và theo dõi phần tích hợp địa chỉ sau; record này không
thay trạng thái Linear hoặc tự xác nhận ngày/danh tính lịch sử.
