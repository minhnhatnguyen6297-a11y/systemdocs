# Decisions — MIN-125

Bảng A = quyết định đã có trong contract publish / hồ sơ nguồn (giữ nguyên). Bảng B = đề xuất P2 đã viết vào `contracts/notary-case-drafting.md` §13 với nhãn **DRAFT — chờ owner duyệt** (Q-id tham chiếu trong văn bản §13.13).

## A. Đã chốt / không thay đổi

| # | Quyết định | Nguồn |
|---|------------|-------|
| A1 | `workspace_commit_stage` nguyên khối + `base_revision`; conflict cả chiều → `workspace_conflict` kèm `server_revision`; không ép ghi | contracts §6, §2.3 |
| A2 | Xóa row Stage đã commit → server gỡ tham chiếu diagram **trong cùng giao dịch** Cập nhật | contracts §6.1; case_workspace.py:907 |
| A3 | 1 người chỉ gán 1 node đang hiệu lực (`duplicate_person`) — draft P2 giữ cho cả hai domain | inheritance_workspace.py:152 |
| A4 | Engine Python NV2 (v3) là SOT cho phân chia; UI chỉ gửi diagram state | contracts §9; inheritance_workspace.py |
| A5 | Word: `MAX_WORD_ASSETS = 5`; `person` >20 → `word.too_many_people`; `[Tài sản N - field]` = thứ tự 1..5; `[Người N]` theo nhóm phụ lục; KHÔNG đưa sơ đồ hai bên vào engine thừa kế | word_engine.py:31,:825,:966; SOT §7 |
| A6 | `serial` hợp lệ theo `entities.md` (`[A-Z]{2}\d{6,8}`); phân biệt ID gốc / vị trí hiển thị | entities.md §10,§12 |
| A7 | Revision phủ cả Stage lẫn diagram; idempotent create bằng `idempotency_key`; `command_id` dedup ở envelope; late response bị bỏ ở client theo phiên | contracts §2.2–2.3; diagram_save A10; EXPERIENCE.md §6 |

## B. Đề xuất trong DRAFT §13 — CHỜ OWNER

| Q | Đề xuất trong draft | Phương án khác (nếu owner đổi) |
|---|----------------------|-------------------------------|
| Q1 | **Phá vòng phụ thuộc hồ sơ mới**: `Cập nhật` trên draft = `workspace_create` nguyên khối; payload create cho `diagram` trở thành **optional**; chủ/người để lại được chỉ định bằng **`stage.owner_row_id`** (person row) — backend suy `nguoi_chet_id` từ đó, `tai_san_id` = asset vị trí 1; không đổi schema DB. Node `owner` trên diagram trở thành slot mirror (server gán/căn `personId = owner_row_id`; mismatch → `diagram_owner_mismatch`). | (B) "commit phiên" cục bộ cho draft — Pool đọc snapshot in-session, `workspace_create` vẫn đòi diagram owner khi `Lưu hồ sơ`; không thêm `owner_row_id`. (C) cho `nguoi_chet_id`/`tai_san_id` nullable — đụng DB, tác động engine/Word. |
| Q2 | **Nút Hủy** = thao tác client (không command mới): phục hồi buffer Stage **và** buffer diagram về đúng snapshot đã commit. Xóa row trong draft **không** prune diagram ngay — prune chỉ ở Cập nhật (server, A2); với hồ sơ mới: prune ảo chỉ xảy ra tại `workspace_create`. | Tách 2 nút Hủy cho Stage và Diagram độc lập (P6 quyết UX). |
| Q3 | **Tài sản**: tối đa **3**; **vị trí = thứ tự mảng** (1..3); bỏ `is_primary` khỏi wire (vị trí 1 = primary trong engine). Thêm asset thứ 4 → `stage_validation_error{code:asset_limit}`. Reorder đổi nghĩa vị trí; `row_id` vẫn ổn định. | Giữ `is_primary` dư thừa cạnh vị trí — bị loại vì hai nguồn sự thật mâu thuẫn. |
| Q4 | **Dấu chọn tài sản theo vị trí**: node v3 thay `isLandOwner`/`willReceive` bằng `ownPositions`/`receivePositions` (mảng con của {1,2,3}). Reorder/delete asset KHÔNG tự chuyển dấu theo `row_id` — số vị trí giữ nguyên nghĩa; vị trí vượt số asset hiện có bị prune lúc commit. | Chọn theo `asset_id` thay vị trí — bị loại vì "không tự chuyển dấu chọn theo ID tài sản cũ" (MIN-125) và phải theo dõi ánh xạ riêng. |
| Q5 | **Mặc định**: khi gán người vào slot thừa kế → `receivePositions` mặc định = tất cả vị trí đang có; node `owner` → `ownPositions` = tất cả vị trí (đề "chủ mặc định cả 3"). Thêm asset sau KHÔNG tự mở rộng vùng chọn đã có. | Mặc định `receivePositions=[]` (phải tích tay) — an toàn hơn về pháp lý nhưng thêm thao tác. |
| Q6 | **Legacy → v3**: `isLandOwner:true`→`ownPositions=[1..min(3,N)]`; `willReceive:true`→`receivePositions=[1..min(3,N)]` (giữ nghĩa "nhận hết" hiện tại); `false`→`[]`. Engine vẫn nhận projection boolean. Hồ sơ cũ >3 asset → đọc được, emit cảnh báo `stage.legacy_asset_overflow`; `stage_editable:false` cho tới khi giảm ≤3. | `willReceive`→`[]` + cảnh báo (an toàn hơn) — chưa chọn vì đổi nghĩa hồ sơ cũ trên wire. |
| Q7 | **Sơ đồ hai bên**: domain `two_party`, `diagram_state.version=3`, node id cố định `p1..p30` (A=1..15, B=16..30 suy từ số — không hệ đánh số thứ hai), state luôn đủ 30 node, `personId` nullable (ô trống không dồn số), cấm trường quan hệ. `diagram_evaluate` → `render_model{status:"unsupported"}`; `word_export` → `case_type_unsupported`; capabilities `word_export:false`. Stage people ≤30 (`people_limit`). | Không nối `p1..p30` vào `position` người trong Stage (giữ tách — §12 quan hệ suy ra cần chốt riêng ở P5). |
| Q8 | **Đổi loại hồ sơ**: `case_type` immutable sau khi tạo; draft (chưa tạo) đổi loại → reset diagram buffer theo domain mới (client rule). | Cho phép đổi `case_type` qua commit meta — phức tạp migration, loại. |
| Q9 | **Drop lên ô đã có người**: hoán đổi vị trí (cả hai domain); người đang gán không thể đi Pool. | Từ chối drop / tách — chưa chọn vì trái hành vi kéo-thả tự nhiên. |
| Q10 | **Nhiều người chọn cùng một vị trí tài sản**: hợp lệ (đồng sở hữu / nhận chung) — cả `ownPositions` lẫn `receivePositions` trên nhiều node trùng vị trí không vi phạm. | — |
| Q11 | `document_type` cho `two_party` (draft registry): `chuyen_nhuong`, `tang_cho`, `cho_thue`, `dat_coc` — **danh sách chờ owner chốt** với NV2. | — |
| Q12 | `version` trong `diagram_state` bump lên **3** cho v2 (cả hai domain); `domain` bắt buộc trong state (mirror `result.diagram.domain` giữ nguyên). | — |

## C. Câu hỏi KHÔNG đề xuất — cần owner/nhóm khác trả lời

| # | Câu hỏi | Vì sao chưa chốt |
|---|---------|-----------------|
| C1 | `two_party` có cần trường "đại diện mỗi bên" trong Stage không? | Phạm vi dữ liệu nghiệp vụ của NV2; contract chỉ chốt khung, không tự thêm trường nghiệp vụ. |
| C2 | Danh mục `loai_dat`/`thoi_han` cho land_rows nâng cấp (P6) — đóng hay mở? | Cần chốt với owner theo thực tế GCN. |
| C3 | Người đã `deleted` trong Stage: gỡ luôn person_id liên kết hay giữ để Hủy hoàn tác? (liên quan `entity_id` sau commit) | Hành vi persistence chi tiết → P5; draft đã quy ước tôn trọng `entity_id` giữ nguyên. |
| C4 | `two_party` Word exporter (bundle mới, `{{Người 16}}`…) | Task Word riêng — P2 chỉ ghi ý định đánh số (§13.10). |
