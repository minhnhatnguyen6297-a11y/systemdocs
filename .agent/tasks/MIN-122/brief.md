# MIN-122 — FIX: Soạn hồ sơ/Tổng quan (nháp mới, nhập chung, sửa trực tiếp, tự sinh node, danh sách)

Linear: MIN-122 (parent MIN-68, In Review, blockedBy MIN-121). Làm lại từ
đầu — implementation trước mất cùng worktree. Scope = handoff MIN-68
P1–P5 (Linear description).

## Scope

- **Modal CSS fix**: selector `.cd-root, .cd-modal-backdrop`; margin/padding
  bleed chỉ trên `.cd-root`. Sửa chung intake/conflict/menu/Word dialog.
- **Nhập dữ liệu chung**: gộp `Nhập Excel` + `OCR giấy tờ` thành một nút
  `Nhập dữ liệu` (không preset); Tài sản dùng cùng dialog. Một pipeline
  chung image/PDF/DOCX/XLSX/text. Không thêm MarkItDown.
- **Sửa trực tiếp**: ô nhập hiện ngay trên dòng (bỏ bấm-mở-detail), nhãn
  luôn thấy, lỗi đúng trường, gõ không mất focus (rerender đã defer khi
  focus trong panel — giữ). Tài sản = biểu mẫu **nhóm trường xếp dọc**
  (diễn giải 26/09, thắng hướng "cột" của MIN-120). Thêm model method sửa
  `land_rows`. Luôn đúng một `is_primary` khi assets không rỗng; xóa tài
  sản chính → promote asset đầu còn lại.
- **Tự sinh node** (port V2 tối thiểu từ ReactFlowApp.jsx): seed idempotent
  `father`, `mother`, `spouse_father`, `spouse_mother`, `owner`, `spouse`,
  `child_1`; luôn đúng một `child_N` trống kế tiếp khi các child đã có
  người. KHÔNG port resolveSubRelations/engine JS/heuristic ngày chết.
- **Nháp mới + Lưu hồ sơ** (MIN-121): status `chưa mở`/`nháp mới`/`đã lưu`;
  `Lưu hồ sơ` → `workspace_create` lần đầu; lỗi giữ nháp nguyên vẹn; sau
  lưu chuyển sang luồng revision; retry không tạo trùng (`idempotency_key`
  phiên); đổi hồ sơ reset toàn bộ state (stage/diagram/intake/Word/conflict)
  + bỏ job response về trễ của case cũ.
- **Tổng quan**: auto-load khi vào tab; `Làm mới danh sách`; lọc `q` ở
  query trước limit (adapter hiện limit 50 rồi mới lọc); hiển thị
  loading/rỗng/lỗi/số hồ sơ.
- **`movePerson`** model op: `{kind:'person', row_id, source_node_id?}` →
  target node: trống = move, có người = swap; target null (Pool) = unassign.
  Nền MIN-119.

## Backend/adapter

- `CaseWorkspaceService.create()` — transaction: InheritanceCase +
  Customer upsert + Property upsert + InheritanceCaseProperty link +
  case_state_json + engine_state_json + revision=1. Owner node `owner`
  personId → `nguoi_chet_id`. Idempotency bằng `idempotency_key` persist.
- `InheritanceWorkspaceService.evaluate_draft()` — validate V2 + personId
  ⊆ draft stage, chạy `run_inheritance_case`, không persist.
- Adapter: `notary.workspace_create` handler, intake/evaluate nhận
  `case_id` absent (draft), `case_list` `q` filter trước limit.
- Mock adapter parity đầy đủ + `backend_mode:"mock"`.

## Verify

`npm test` (shell) + `pytest` adapter/mock/contract + `verify.bat`
(notary_v2) + `git diff --check`. Baseline: 184 test pass.
