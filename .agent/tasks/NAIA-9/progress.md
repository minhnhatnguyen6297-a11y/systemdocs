# NAIA-9 — tiến độ

04/10/2026 (tiếp nhận) — kiểm chứng và vá sau review 4 lens:

- Probe Electron cách ly chạy thật PASS: lookup person, áp dụng giữ nguyên văn +
  `(nay là …)` không lặp, tài sản chia tách trả đủ ứng viên, niêm yết theo tài
  sản chọn, lưu/mở lại giữ giá trị, DB gốc và DOCX gốc bất biến.
- Bug thật tìm được: (a) rebuild bị hoãn khi đang gõ nuốt luôn refresh ô gợi ý —
  vá `refreshAddressBoxes`; (b) gõ lại đúng ngày `dd/mm/yyyy` đang hiển thị
  không bắn `change` → model giữ raw → save bị từ chối — vá commit ở `blur`.
- Service: parse-error trả `invalid_input` rõ; lỗi kho (KeyError/khóa/thiếu
  trường) trả `reload_failed`; nhánh chia tách confirmed một phần vẫn trả ứng
  viên với coverage `insufficient_confirmed_history`.
- Model: `address` ưu tiên khi có cả `province`/`commune`; issuer gate nhận
  `ubnd` không dấu; ignore trong lúc chờ chặn response đè; dọn timer/request
  khi đổi hồ sơ. View: issuer input hiện khi có `noi_cap` sót; idPrefix chống
  trùng id giữa view chính và dialog Word; CSS dùng token thay màu cứng.
- Contract: thêm `notary.address_lookup` làm command thứ 10 + §14 + ngoại lệ
  schema_version; example `job.address-lookup.valid.json` + siết validator
  (kiểu/độ dài text, `dataset_version`/`revision`, enum `coverage.kind`).
- Tests: 22+1 py address, 79 timeline, 81 contract examples, 248 node
  (thêm regression blur-normalize + raw→ISO payload + pin tên command +
  ignore in-flight), 5 scaffolding (thêm dispatch envelope gateway).
- Spec `administrative-address.md` thêm mục lỗi/ngoại lệ, precedence payload,
  ghi nhận kết quả probe thật. Chưa commit; chưa cập nhật Linear.

Vá vòng 2 sau lens adversarial/verification-gaps (13 findings, triage xong):

- Service: `SUFFIX` chịu ngoặc trong tên đích (`.*` thay `[^()]*`); nối
  "Tỉnh X - Y" có gạch ngang (Bà Rịa - Vũng Tàu); nhận cấp huyện theo
  prefix bất kể mốc 2025; đảo thứ tự khi user viết tỉnh trước xã sau;
  nhánh bị `abolish` không hậu duệ giữ terminal → coverage insufficient
  thay vì confirmed_history giả; `target<source` trả coverage kind
  `invalid_input`; qualifier Bando chỉ lọc khi thực sự là tên huyện
  ("(mới)" không loại ứng viên); seeds/candidates sắp xếp deterministic.
- Model: kiểm `schema_version`/`status`/`candidates` của response trước
  khi tin (chống "undefined, undefined"); guard field string của
  candidate khi apply; regex suffix JS đồng bộ service.
- Tests mới: parser hyphen/3-cấp-sau-2025/đảo thứ tự, abolished branch,
  qualifier không phải huyện, target<source coverage, suffix paren cả
  py lẫn mjs, response malformed.
- Deferred: không cancel job lookup bị thay thế (read-only, rẻ; guard
  identity đã bỏ response) — ghi nhận, không vá.
- Kết quả sau vá: 29+1 py address, 233 py timeline+adapter, 81 contract
  examples, 250 node — tất cả xanh.

04/10/2026 — tiếp tục phần dùng kho trong hồ sơ (NAIA-14–21): service
`administrative_address.py`, command `notary.address_lookup`, gợi ý địa chỉ
Người/Tài sản, nơi niêm yết chọn tài sản rõ và nơi cấp giấy khai tử riêng đang
triển khai/kiểm tra. Spec sử dụng kho tại `docs/spec/notary_v2/administrative-address.md`.
Kho lịch sử vẫn là SOT duy nhất; tên cũ tách từ Bando chỉ là chỉ mục quan sát,
không tự thành danh tính hoặc lịch sử confirmed. Chưa nghiệm thu phần giao diện.

Root kết thúc review 04/10/2026: 79 timeline + 5 docs checks passed, 1 docs skip
vốn có; validate toàn kho hợp lệ, 28 links module/feature kiểm riêng. Sửa cuối
tại a3b33dc: ID continuing/unknown không thành kế thừa toàn phần, reparent span,
abolition semantics, query source hashes, duplicate patch IDs, curator/source
ownership và HTTP refresh thật qua fixture local. Spec có hướng phát triển và
khôi phục, không có SOT song song. Data gốc/35 snapshots/3355IDs vẫn nguyên.

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
