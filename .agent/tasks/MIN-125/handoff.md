# Handoff — MIN-125

## Kết quả
P2 (MIN-123) hoàn thành ở mức **contract DRAFT + ví dụ**; runtime chưa đụng —
đúng scope "chỉ thiết kế contract". Phần II `notary.case-drafting.v2` nằm ở
`contracts/notary-case-drafting.md` §13 với nhãn **DRAFT — chờ owner duyệt**;
contract `v1` (§1–§12) không đổi, vẫn APPROVED duy nhất.

## Thay đổi
- `contracts/notary-case-drafting.md` — header ghi §13 DRAFT; thêm §13.1–13.15.
- `contracts/notary-case-drafting/draft-v2.schema.json` — schema tham chiếu
  (asset_row_v2, stage_v2, node_v3 ×2 domain, payload v2).
- `contracts/notary-case-drafting/validate_examples.py` — mở rộng additive;
  v1 không đổi hành vi.
- `contracts/notary-case-drafting/examples/draft-v2/` — 24 fixtures (12 valid +
  12 invalid), mỗi file có `fixture_context.draft_v2:true`.
- `notary_v2/docs/platform/case-workspace/drafting-tab.md` — header + §10 trỏ
  §13 DRAFT.
- `notary_v2/docs/platform/case-workspace/visual-design.md` — marker PENDING
  trỏ §13, giữ trạng thái chờ duyệt.
- `.agent/tasks/MIN-125/` — brief/progress/decisions/handoff.

## Quyết định đã chốt trong draft (tóm tắt — đầy đủ ở decisions.md)
- **Q1** phá vòng phụ thuộc hồ sơ mới: `Cập nhật` đầu = `workspace_create`;
  owner qua `stage.owner_row_id`; `tai_san_id` = asset vị trí 1; diagram
  optional; không sửa schema DB.
- **Q2** `Hủy` client-only, restore cả Stage lẫn Diagram buffer về committed;
  xóa row draft không prune diagram ngay.
- **Q3/Q4** assets ≤3, vị trí = index+1; bỏ `is_primary`; dấu chọn bám vị trí
  (không bám `row_id` khi reorder/xóa); prune out-of-range tại commit.
- **Q5** mặc định nhận/sở hữu = tất cả vị trí hiện có lúc gán; thêm asset sau
  không tự mở rộng.
- **Q6** legacy: `isLandOwner`/`willReceive` true → mảng đủ vị trí hiện có;
  >3 asset → đọc được + cảnh báo, commit bị chặn.
- **Q7** `two_party`: `p1..p30` cố định, bên suy từ số (`p16` = B đầu), ô trống
  không dồn; evaluate → `unsupported`, word → `case_type_unsupported`.
- **Q8/Q9/Q10** `case_type` immutable; drop lên ô có người = swap; nhiều người
  chọn cùng vị trí hợp lệ.
- **Q12** `diagram_state.version` → 3 + `domain` bắt buộc.
- Giữ nguyên: commit atomic + `base_revision`; `duplicate_person`; engine
  Python là SOT tính toán; Word 5 asset/20 người; intake §5.

## Chờ owner (đầy đủ + phương án thay thế → decisions.md bảng B/C)
- Nổi bật: Q1 (owner_row_id vs "commit phiên" cục bộ), Q5/Q6 (mặc định &
  migrate `willReceive`), Q11 (danh mục `document_type` two_party), C1–C4
  (đại diện bên, danh mục loại đất, entity_id khi xóa, exporter Word hai bên).

## Kiểm chứng
- `rtk proxy python contracts/notary-case-drafting/validate_examples.py` →
  **68 files, 0 unexpected outcomes**.
- `git diff --check` sạch; `git status` chỉ gồm đường dẫn sở hữu MIN-125 +
  file lạ của worker P3 (không stage).

## Commit
`(điền hash sau khi commit)`

## Cạm bẫy
- §13 là DRAFT — không implement runtime cho tới khi owner duyệt (P5/MIN-128).
- Không stage `.agent/tasks/MIN-126/` hay `docs/product/ui/prototypes/`
  (vùng P3 chạy song song).
- `land_rows` giữ shape v1 — đã đủ cấu trúc (mục đích/diện tích/thời hạn);
  danh mục giá trị `loai_dat` là câu hỏi mở C2.
