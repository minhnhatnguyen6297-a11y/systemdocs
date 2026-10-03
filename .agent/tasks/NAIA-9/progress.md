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

04/10/2026 — sửa review loop 1: pending edge không truyền confirmed history;
resolved mention tìm pending evidence; kiểm parent kết thúc và xung đột toàn bộ
cùng ngày; exact ISO date/maximum date; province header đủ 5 trường; atomic raw
snapshot và schema pattern có anchor/length. Thêm tests lock/current observation.
49 timeline tests passed. Giữ nguyên 35 snapshots, 3.355 IDs, observations và
dataset hashes; chỉ sửa helper/schema/test/docs, không viết lại ledger.

04/10/2026 — sửa review loop 2: partial reciprocal movements không là whole
succession cycle; tên confirmed không span rename; whole reported_transition
kết thúc input vắng khỏi output. Guard source-key level/missing-store/patch type.
Trước curation lưu compressed previous-ledger revision bất biến; lỗi archive
dừng update. 64 timeline tests passed, có strict full import/rejection, actual
CLI subprocess và boundary ngày đổi tên. Docs nói rõ name-only query, lock
recovery, confidence độc lập, baseline source counts và long-graph limits.
