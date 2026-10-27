---
id: decision-owner-diagram-rules-v2-20261027
title: "Luật sơ đồ v2 — ô do engine sở hữu, gỡ thẻ và Hoàn tác"
date: '2026-10-27'
status: accepted
---

## Nguồn và phạm vi

Owner duyệt plan sửa luật sơ đồ Thừa kế v2 ngày 27/10/2026, mục 0, (b)
và phần `Approved answers` Q1–Q4. Phiên này chỉ WP0: sửa spec/contract,
chạy validator ví dụ; không sửa code, rebase, migrate dữ liệu hoặc triển khai
WP1–WP8. Spec mới không phải bằng chứng runtime đã tuân thủ.

## Quyết định thay thế ngày 17/10/2026

Thay [“B - gỡ cả nhánh”](decision-owner-inheritance-remove-entire-branch-20261017.md)
bằng **gỡ thẻ**: ô là chỗ trống chỉ engine tạo/xóa; thẻ là người được gán.
Người dùng chỉ thả/di chuyển/gỡ thẻ, tích Chủ/Nhận. Không có nút tạo/xóa ô,
nối quan hệ hoặc menu thêm cha/mẹ/con.

Sau mọi thay đổi, kể cả sửa ngày mất/còn sống ở Stage, engine chạy tới ổn
định: thêm ô thiếu, bỏ ô trống thừa im lặng, thẻ trong ô thừa về Pool.
Gỡ chủ đất trả mọi người trong ô sinh ra từ chủ đất về Pool, **kể cả vợ/chồng**.
Không xóa Người ở Stage, không tự reparent, không autosave. Không modal;
chỉ khi có người khác bị đẩy về Pool mới hiện `Đã đưa N người về Pool · Hoàn tác`
khoảng 5 giây. Hoàn tác khôi phục nguyên trạng trước thay đổi.

Bỏ phương án xác nhận trước mutation, chỉ duyệt cạnh cha/mẹ để gỡ nhánh và
lưu tombstone mới. Lý do: người dùng thao tác thẻ, tập ô thuộc engine;
Hoàn tác bảo vệ thao tác cascade mà không chặn luồng.

## D-041 — sửa đổi ngày 27/10/2026

Repo hiện tại không có bản ghi mang mã D-041; amendment này ghi theo plan
đã duyệt, không tự khôi phục các nội dung khác từ nhánh B.

WP-S (27/10/2026) thay cách hiểu **“cạnh cha-con tách riêng khỏi ô vợ/chồng”**
bằng **luồng theo cặp**: ô Con thuộc về một cặp (người gốc + ô vợ/chồng), không
thuộc riêng người gốc. Luật đang áp dụng:

- **A. Sinh ô theo cặp.** Thả một người đã chết (chủ đất, hoặc người chết sau
  chủ đất) thì sinh: Cha, Mẹ; ô Vợ/chồng số 1 + một ô vợ/chồng dự phòng; và
  **một ô Con thuộc cặp (người đó + ô Vợ/chồng số 1)**, kể cả khi ô vợ/chồng số 1
  còn trống. Con thả vào ô đó được ghi nhận cả cha lẫn mẹ; thả vợ/chồng số 1 vào
  sau thì cha/mẹ còn thiếu được điền tự động. Mỗi vợ/chồng tiếp theo thả vào ô dự
  phòng có ô Con riêng của cặp đó và sinh thêm một ô vợ/chồng dự phòng mới. Mỗi ô
  Con được thả thì sinh lại một ô dự phòng. Nút `Con riêng` trên thẻ con xóa
  cha/mẹ được điền tự động. Người vợ/chồng đặt cuối là hợp pháp; vợ/chồng đặt
  trước bị làm nhạt nhưng con của họ vẫn là người thừa kế của người gốc. Chủ đất
  còn sống chỉ có nhóm Vợ/chồng (+1 dự phòng), không có Cha/Mẹ/Con. Người chết
  trước chủ đất chỉ có ô Con (thế vị, tối đa tới chắt).
- **B. Con chết SAU chủ đất (chuyển tiếp)** là con của cặp đang có trên sơ đồ:
  gắn vào đúng hai ô đó, **không sinh Cha/Mẹ mới**. Không sinh ô cho quan hệ đã
  có trên sơ đồ. (Lỗi cũ: ba cha/mẹ làm sơ đồ đứng, lưu báo
  `Quan hệ cha/mẹ không hợp lệ`.)
- **C. Vợ/chồng chết sau chủ đất:** con chung đã nằm dưới cặp đó là con của
  người này nên không sinh ô Con trùng; người này có Cha/Mẹ riêng, còn vợ/chồng
  là chủ đất đã có trên sơ đồ — chỉ gắn, không sinh ô vợ/chồng mới.
- **D. Nhãn ô không chứa UUID/ID thô:** `Cha của …`, `Mẹ của …`,
  `Vợ/chồng của …`, `Con của … và …`.
- **E. Sau `Hoàn tác`**, engine chạy lại trên dữ liệu hiện tại và bỏ những ô vừa
  khôi phục mà luật hiện hành không cho phép.
- **F. Ngày chỉ có năm = 01/01 của năm đó** khi engine so trước/sau; hiển thị
  đúng như nhập. Con `2020` so với chủ đất 01/06/2020 là chết trước → nhánh thế vị.
- **G. Ngày không hợp lệ/thiếu phần** (`06/2001`, `31/02/2001`): lỗi tiếng Việt
  ngay tại ô ngày; thẻ có ngày không hợp lệ **không thả được** (Stage hoặc Pool)
  và có tooltip ngắn nêu lý do. Sửa một thẻ đã đặt thành ngày không hợp lệ không
  được xóa sơ đồ: đánh giá không fail toàn cục, giữ trạng thái hợp lệ cuối của
  những người khác và chỉ hiện lỗi ở field đó.
- **H. Con sinh sau khi người chết:** không luật, không cảnh báo.
- **I. Vợ/chồng chết trước chủ đất:** không sinh ô (Điều 652 BLDS 2015); nhánh
  chỉ có ô Con thế vị, tối đa tới chắt (D-012). Giữ luật này.
- **J. Bố cục:** không chồng thẻ (thẻ vợ/chồng không che ô Con đang trống và
  không đè thẻ con); vợ/chồng nằm ngay cạnh người gốc; ô Con của cặp nằm dưới
  đúng cặp; mỗi thế hệ một hàng.
- Ghi chú: thẻ chủ đất không tích `Chủ` vẫn giữ nguyên vị trí; trần tài sản vẫn 5.
- WP-S ghi luật này vào `contracts/notary-case-drafting.md` §13.4 và
  `_bmad-output/specs/notary_v2/diagram-rules.md` §9.2/§9.6/§9.7/§9.9/§11;
  engine spec duy nhất vẫn nằm trong archive nên luật engine viết tại §11.
- Plan chọn state v4 `spouseSlotIds`, người cuối hợp pháp và migrate v3→v4
  ở gói sau. WP0 không đổi schema/fixture/wire v3 hiện có; không coi bản ghi
  này là đã triển khai migration hoặc đưa code nhánh B vào nhánh hiện tại.

## Mặc định, đối chiếu và bố cục

- Ô chủ đất mặc định `ownPositions` = mọi vị trí hiện có, `receivePositions=[]`.
  Mọi ô khác `ownPositions=[]`, `receivePositions=[]` (= từ chối trong văn bản).
  Không tự tích Nhận. Khi thêm tài sản, chỉ người đã tích được nối vị trí mới
  vào đúng loại đã tích; người chưa tích không tự điền. Quyết định này thay
  phần mặc định Nhận/đồng bộ mảng rỗng của G1 phương án B ngày 22–23/10.
- Giữ lựa chọn đã lưu, kể cả `receivePositions`; mặc định mới chỉ người mới
  thả. Mở hồ sơ cũ đối chiếu tập ô và ghi chú một lần `N người đã về Pool do
  luật sơ đồ mới`. Tombstone cũ bỏ qua khi đọc, dọn khi lưu; ID `slot_n` ánh
  xạ sang ID ổn định khi migrate. Không mất Người khỏi Stage.
- ID ô ổn định theo (người gốc, vai trò, thứ tự). Mỗi thế hệ một hàng:
  cha/mẹ trên, vợ/chồng ngay cạnh cùng hàng, con dưới theo ngày sinh;
  dự phòng cuối nhóm, ô trống có nhãn vai trò.
- Thả/gỡ không debounce; gõ chữ khoảng 300ms. Thả → ô ≤200ms p95;
  sửa sống/chết ở Stage → đối chiếu ô ≤200ms; một lần vẽ mỗi thay đổi.
- Input luôn hiển thị đúng như nhập. App không suy loại giao dịch,
  không suy tài sản chung, không cảnh báo vợ/chồng.

## Q1–Q4 — đáp án đã duyệt

| Câu | Quyết định |
|---|---|
| Q1 — thiếu/không so được ngày mất | Chưa sinh ô cho người đó tới khi nhập đủ ngày; hiện `thiếu ngày mất` trên thẻ. Không đoán trước/sau chủ đất từ ngày quy ước. |
| Q2 — nhiều vợ hợp pháp | Giữ D-041: người đặt cuối là hợp pháp; ca nhiều vợ hợp pháp hoãn sang đợt sau. |
| Q3 — đoạn Word từ chối | Đợt này chỉ đổi mặc định sơ đồ; đoạn Word từ chối hoãn sang đợt Word sau. Văn bản xuất có thể thiếu đoạn này; không tuyên bố đã hoàn tất Word hoặc bịa dữ kiện từ chối. |
| Q4 — công tắc thông báo gỡ | Mặc định **bật** toast + Hoàn tác, chỉ khi cascade đưa người khác về Pool; tắt thì hoàn toàn im lặng. |

## Hàng 2/3 — gác lại

D-038/R-32 gác sau **`ENABLE_LATER_LINES=False`**, mặc định tắt. Sơ đồ chỉ
hàng 1 + thế vị + chuyển tiếp; thiếu hàng 1 trả `unsupported` / **Chưa hỗ trợ**,
không sinh ô hàng 2/3. Giữ code hàng 2/3 sau cờ ở gói sau; test riêng bật cờ
để phần đã giữ không mục. Không triển khai cờ hoặc chạy test hàng 2/3 ở WP0.

## Nguồn hành vi và kiểm tra WP0

Contract `contracts/notary-case-drafting.md` §13.4; spec
`_bmad-output/specs/notary_v2/diagram-rules.md` §9; engine spec duy nhất đang
nằm trong archive `specs-before-consolidation-20261015/notary_v2/diagram/inheritance/engine.md`
được đính chính có giới hạn, không nâng toàn bộ bản Draft cũ thành đã duyệt.
Đối chiếu đủ bảng năm trường hợp và các câu thay thế mục (b); kiểm tra ví dụ
bằng `contracts/notary-case-drafting/validate_examples.py`. Validator chỉ
chứng minh ví dụ wire hiện có hợp lệ, không nghiệm thu engine/UI luật mới.

Kết quả WP0 ngày 27/10/2026:
`/workspace/venv/bin/python contracts/notary-case-drafting/validate_examples.py`
→ **121 files, 0 unexpected outcomes**. Có cảnh báo deprecation hiện có của
`jsonschema.RefResolver`; không sửa validator/code trong phạm vi WP0.
