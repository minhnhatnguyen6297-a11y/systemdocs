# TASK-3 / TASK-4 — kết quả làm lại sau audit 05/10/2026

Người sửa: @opencode. Phạm vi: đúng 5 điểm R1/R2/R3/R5/R6 trong
`.agents/audit-task3-4-20261005/REVIEW.md`. R4 giữ nguyên theo quyết định
(Owner đã nêu rõ trong giao việc). Không đụng luật đã chốt, không commit/push,
giữ mọi thay đổi dở (đặc biệt TASK-1).

## Đã sửa gì

- **R1** (`notary_v2/services/administrative_address.py`): nhánh raw khớp
  trước đây dừng ở observation đầu tiên. Giờ trả riêng **mọi** observation
  có raw khớp (tên khớp vẫn trả mọi observation của đơn vị); chỉ bỏ trùng
  cùng cặp `(unit_id, observation_id)` qua `emit()`. Thứ tự kho giữ nguyên.
- **R2** (cùng file): `official_name`/`province_id` lấy `rows[0]` (bản cũ
  nhất). Giờ chọn bản ghi đúng `dataset_version` đang hoạt động qua id mang
  version (`name:<16 ký tự>:<uid>`, importer sinh tại
  `administrative_timeline.py:406/409`); không có id version (fixture cũ)
  mới dùng bản ghi cuối. Không chọn đầu/cuối tùy tiện.
- **R3** (model): response đến muộn khi nguồn đã đổi mà chưa có lần Tra mới
  thì dọn `loading` treo, báo "Nội dung đã đổi sau khi bấm Tra. Bấm Tra lại."
  (trước đây treo `loading` mãi). Dấu thay đổi (`lookupSeq`) chỉ tăng khi
  sửa `dia_chi`/`noi_cap`/`noi_niem_yet`, thêm/xóa dòng, đổi case — sửa họ
  tên/ngày tháng/sắp xếp không làm request hết hiệu lực nữa.
  (view): `refreshAddressBoxes` vẽ lại tại chỗ từng ô kết quả (không input
  bên trong nên an toàn cả khi đang gõ); bỏ việc kéo focus về nút Tra khi
  kết quả về.
- **R5** (view): nhớ ô **thật sự** đang sửa qua `focusin` (bàn phím) +
  `mousedown` trên nút Tra (chuột, chạy trước khi focus đổi). Hủy câu hỏi và
  đóng full đều phục hồi đúng ô + vùng chọn (+ scroll khi đóng full) bằng
  `restoreLookupFocus` chung.
- **R6** (model): slot giữ `gen` (dấu thay đổi lúc bấm Tra);
  `openFullFromSlot` đòi `slot.gen === lookupSeq` thêm vào so chữ — A→B→A
  (chữ về cũ nhưng dấu đã nhích) trả `stale`, không gửi `full`.
- Stub test `dom-stub.mjs`: thêm `replaceWith` còn thiếu (DOM thật có sẵn).

## Test đã thêm/chạy

- Lõi (`notary_v2/tests/test_administrative_address.py`, +4): raw khớp 2/11
  observation cùng unit; tên khớp trả cả 11 dòng; 11 dòng → `too_many`
  `total=11`, `full` trả đủ 11; importer thật hai snapshot đổi tên + tỉnh
  cha (theo đúng probe audit).
- Model (`shell/test/notary-address-lookup.test.mjs`, +3): A-B-A trước xác
  nhận → `stale`; nguồn đổi khi chờ → slot `error` có hướng dẫn; sửa họ tên
  không ảnh hưởng lookup.
- View (`shell/test/notary-case-drafting-view.test.mjs`, +3): kết quả về khi
  sửa ô khác vẫn hiện, focus ở yên; Hủy phục hồi ô+vùng chọn+scroll; đóng
  full khi sửa ô khác đích phục hồi ô đó. Câu hỏi `too_many` đúng từng chữ
  đã có assert từ trước.
- Kết quả: **Python 211 pass/3 skip** (basetemp mới `.agents/rework-pytest-2`;
  skip: thiếu `jsonschema`, 2 ca symlink thiếu quyền — như nền audit),
  **renderer 79 pass**, **validator 82 files/0 unexpected**, `git diff --check`
  sạch. Nền audit: 207/3, 73, 82/0, npm 385/1 (lỗi intake thiếu jsonschema,
  ngoài phạm vi — không sửa để che).
- Probe audit gốc **cố ý assert lỗi cũ** nên sau sửa chúng rớt đúng như dự
  kiến (core dừng ở assert R2-dòng 50, model dừng ở assert R6-dòng 34) —
  đây là bằng chứng sửa có hiệu lực, không phải suy thoái. Bằng chứng gốc
  trong `.agents/audit-task3-4-20261005/` giữ nguyên.

## Electron thật (harness sao chép sang `.agents/rework-electron/`)

Chạy `electron.exe` với bản sao harness (bản gốc không đụng), Electron/
Chromium thật, click chuột thật qua `sendInputEvent`, 1280×800 và 1366×768:
- Kết quả về khi sửa ô khác: hiện đủ + 1 nút Copy, focus ở yên ô họ tên.
- Hủy `too_many`: focus + vùng chọn về đúng ô đang sửa, 0 gọi `full`.
- Đóng full khi chờ (ô địa chỉ lẫn ô họ tên): đúng ô + vùng chọn
  `[1,4,backward]`, nháp giữ nguyên, response muộn không mở lại dialog.
- Issuer gửi địa chỉ người chết; posting gửi nội dung ô niêm yết.
- Sửa query trong overlay không tự tra; bấm Tra mới gửi.
- R4 giữ: danh sách lần Tra A vẫn hiện khi đang gõ B (chỉ có hiệu lực sau
  bấm Tra) — không phải lỗi.

## Còn thiếu (giữ TASK-4 chưa Done)

- **Copy ra clipboard hệ điều hành**: cửa sổ kiểm tra chạy ẩn
  (`document.hasFocus() === false`) nên `writeText` không ghi được (đã thử
  click thật trúng nút + chờ 800ms + đọc clipboard: vẫn nội dung cũ của máy).
  Logic báo Copy thành công/thất bại đã có test stub. Cần cửa sổ thật đang
  focus để kiểm nốt.
- Bản đóng gói sidecar và review độc lập diff.
- Sidecar nối kho thật đã có bằng chứng qua `test_notary_mock_adapter.py`
  (đi qua adapter → service → ledger thật).
