# TASK-4 handoff — Tra thủ công + overlay full (triển khai xong)

Ngày: 05/10/2026. Nhận đúng model/view sau TASK-3 (v2, ngủ đông), không
sửa luật tìm kiếm/contract/schema.

## Model (`case-drafting-model.js`)
- `addressContext`: posting ← `caseInfo.noi_niem_yet`; issuer ← `dia_chi`
  người chết (không phải `noi_cap`); person/asset ← `dia_chi` dòng đó.
  Trả `{query, presentation:'drafting'}` hoặc null khi trống.
- `requestLookup(kind,rowId)` (thay `ensureAddressSuggestion`): mỗi lần bấm
  là `callId` mới, luôn gửi (kể cả trùng chuỗi); `lookupSeq` đơn điệu tăng
  tại mọi `touchStage`/`updateCaseMeta`/đổi case/lần Tra mới. Response bị bỏ
  khi: khác session, sai `callId`, `seq` đổi (bắt cả A→B→A), query hiện tại
  khác lúc bấm. Kết quả vào `state.addressSlots[key]` (`loading/ready/error`).
- `openFullFromSlot` sau xác nhận `too_many`: kiểm lại slot + query hiện tại,
  stale → `{ok:false, stale:true}` (view báo "Bấm Tra lại", không mở overlay);
  ok → gửi ngay yêu cầu `full` đầu tiên bằng query đã chụp.
- `requestFull(queryText)` chỉ gửi khi bấm Tra trong overlay; `closeFull()`
  null phiên + tăng seq để response muộn bị bỏ.
- `dismissLookupSlot` (sau Hủy), `markLookupStale` (báo query đã cũ).

## View (`case-drafting-view.js` + `case-drafting.css`)
- Nút Tra (`lookup-tra:kind:rowId`) bên phải ô person/asset/issuer/posting;
  kết quả (`address-kind-rowId`) ngay dưới ô. Không gửi khi gõ/dán/blur/
  render/refresh. Không nút Áp dụng/Chọn; mỗi dòng một Copy
  (`lookup-copy:...`), Copy lỗi báo lỗi, không báo láo; Copy không đóng gì,
  không sửa dữ liệu.
- `too_many`: hỏi đúng câu "Nhiều kết quả khớp. Xem đầy đủ?" qua confirm
  chung; Hủy → xóa slot, không gọi `full`; Đồng ý → `full` đúng query đã chụp.
- Overlay full: query sửa được + Tra phía trên; danh sách cuộn
  (`.cd-lookup-list`, tối đa 40vh); mỗi dòng Copy riêng; Đóng + × + Esc +
  click nền; một dialog tại một thời điểm (xác nhận đóng trước khi mở full).
  Đóng giữ: chữ/nháp (model đã đồng bộ khi gõ), scroll dp, focus + caret
  (kể cả issuer: focus về ô `noi_cap`, query từ `dia_chi`). Rerender khi
  overlay mở không cướp focus, giữ scroll, refresh danh sách.
- Giữ nguyên mọi dòng nguồn cùng `unit_id`/`display` (nhận diện hiển thị
  theo index; domain không thêm ID).

## Test
- `shell/test/notary-address-lookup.test.mjs` 10 test: nguồn query từng ô,
  bấm lại cùng chuỗi, A→B→A, đổi case, stale sau xác nhận, full đúng query
  chụp, sửa query overlay không tự gửi, đóng overlay bỏ response muộn.
- `shell/test/notary-case-drafting-view.test.mjs` +7 test TASK-4: vị trí nút,
  không tự tra, Copy thành công/thất bại, nguồn issuer/posting, Hủy/Đồng ý
  too_many, overlay giữ nháp/caret/scroll.
- Chạy: `node --test test/notary-address-lookup.test.mjs
  test/notary-case-drafting-view.test.mjs` → 73 pass.
- Python + validator không đổi sau TASK-3: 207 passed/3 skipped, 0 lỗi.

## Chưa kiểm (ghi rõ, không nhận đã xong GUI)
- Mở app Electron thật ở 1280×800 / 1366×768, bấm Tra/đóng/mở/copy tay,
  kiểm focus/caret/scroll và luồng nơi cấp khai tử: KHÔNG thực hiện được ở
  máy triển khai (không có hiển thị). Cần người hoặc worker có GUI kiểm lại
  trước khi tick Done TASK-4.
- `npm test` đầy đủ vẫn rớt sẵn tại `notary-docx-intake.test.mjs` (ngoài
  phạm vi, tồn tại trước TASK-3).
