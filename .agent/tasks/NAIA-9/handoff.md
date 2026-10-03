# NAIA-9 — bàn giao kho timeline

**Hoàn thành 04/10/2026:** kho và CLI local; chưa tích hợp runtime giao diện.

Nguồn chính: `notary_v2/data/administrative_units/ledger.json` và snapshots.
Giải thích đầy đủ: [spec timeline](../../../docs/spec/notary_v2/administrative-timeline.md).
Schema: [ledger.schema.json](../../../contracts/administrative-timeline/ledger.schema.json).
Helper: [administrative_timeline.py](../../../notary_v2/administrative_timeline.py).

Đã kiểm 3.355 đơn vị / 35 raw sources; 34 tỉnh, 3.321 xã, 0 huyện.
136 giữ nguyên, 3.219 pending transitions, 161 partial rows. Tất cả event dates
nguồn Bando là null; không có lịch sử cũ hay parent/code cũ bị tự dựng.

27 focused tests passed, gồm schema/invariants/full snapshot, test mất ghi
file/nguồn hỏng không thay ledger, refresh idempotent và giữ lịch sử manual;
ví dụ JSON trong spec thực sự dùng được. Chạy từ root:

```powershell
python -m pytest notary_v2/tests/test_administrative_timeline.py -q
python -m notary_v2.administrative_timeline validate
```

Owner bổ sung lịch sử qua patch có `base_revision` + `upsert` và nguồn. Tên/mã
không là identity lịch sử; malk chỉ khóa quan sát nguồn hiện tại. Resolve mention
không sửa phrase/evidence. Thêm các events confirmed riêng với ngày có nguồn.
Query giữ pending tách khỏi chronological confirmed; date lookup thiếu dữ liệu
trả insufficient_confirmed_history. Hướng scale/index/schema migration nằm cùng spec.

Còn thiếu: identity/date/history có nguồn do Owner cung cấp, huyện, parser văn
xuôi, contract và UI consumer. CLI hiện load/validate/quét local theo lần chạy;
chưa hứa tối ưu per-keystroke. API Bando chưa có cam kết version ổn định. Sau
process crash có thể cần kiểm/xóa stale `.write.lock`; snapshot raw bị thừa sau
lỗi ghi không làm đổi ledger. Không thay DB văn phòng, Word hay DOCX.

Review loop 1 đã sửa validator/query/raw write: 49 focused timeline tests passed.
Query nối confirmed events; resolved identity chỉ giúp tìm pending evidence,
không biến quan hệ chờ thành confirmed. Parent period không vượt ngày cha kết
thúc; chặn whole-consumption/rename-abolition xung đột cùng ngày. Exact dates,
schema anchors/length, province header, lock/current-observation filtering có
regression tests. Raw snapshot xuất bản qua file tạm rồi replace; retry sau lỗi
không mắc file hash viết dở. Merge output không tự có formation date; composite
mention không resolve thành một unit ID. Dữ liệu đã tải giữ nguyên byte và hash.

Review loop 2: 64 timeline tests passed. Partial movement không làm identity
kết thúc/false successor cycle; whole reported_transition confirmed áp end rules.
Tên confirmed không span rename dù chưa gắn event_id. Guard patch type, missing
store và source key reused across levels. Manual correction lưu ledger trước đó
dạng immutable gzip revision; archive failure aborts update. Archive là recovery
evidence, ledger hiện tại vẫn là SOT duy nhất. Có tests strict full import/reject,
CLI subprocess và exact rename boundary. Name-only query và extreme-depth graph
limit, baseline count revalidation, lock recovery được ghi rõ trong spec.
