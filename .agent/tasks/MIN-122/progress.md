# Progress — MIN-122

## Trạng thái: đang làm lại — 2026-09-27

Implementation trước mất cùng worktree. Contract MIN-121 phải xong trước
(đang rebuild song song theo thứ tự: contract → backend → adapter/mock →
model → view → MIN-119 drag).

## Checklist

- [x] `CaseWorkspaceService.create()` + idempotency (66/66 service tests)
- [x] `InheritanceWorkspaceService.evaluate_draft()`
- [x] Adapter real: workspace_create / draft intake / draft evaluate /
      case_list q (q đã có sẵn từ MIN-112, giữ nguyên)
- [x] Mock adapter parity (87/87 mock tests)
- [x] Model: newDraft/saveDraft/updateCaseMeta/movePerson/seed slot/
      next empty child/land_rows/is_primary/guard đổi case (50/50)
- [x] View: overview auto-load + q filter + Nhập dữ liệu chung + inline
      edit + Lưu hồ sơ + asset form dọc + modal CSS fix
- [x] Test mới + verify đủ bộ (xem Log 2026-09-27b)

## Log 2026-09-27b (model + view + verify)

- Model (`case-drafting-model.js`): `newDraft`/`saveDraft`/
  `updateCaseMeta`/`movePerson`/`seedDiagramSlots`/`isDraft`/`isStageEmpty`,
  `CASE_META_FIELDS`/`CASE_DOCUMENT_TYPES`; draft evaluate/intake omit
  `case_id`; session counter chan response cu ghi de draft moi.
- View (`case-drafting-view.js`): tab Tổng quan auto-load + q filter +
  dem so ho so + "+ Hồ sơ mới" (confirm khi co unsaved); meta card nhap
  moi (document_type/ngay_lap_ho_so/noi_niem_yet/ghi_chu); 1 nut "Nhập
  dữ liệu" chung (preset=null) cho ca Nguoi/Tai san; nut "Lưu hồ sơ"
  thay "Cập nhật" khi nhap; person detail du truong; asset form nhom
  truong dung `.cd-field-stack` + `land_rows` editor + checkbox primary.
- Diagram (`relationship-diagram.js`): drop node dung `movePerson`
  (swap/unassign); Pool la drop target; "Lưu sơ đồ" disable tren nhap;
  `personName` doc stage nhap khi chua co case.
- CSS: token `.cd-root, .cd-modal-backdrop` (modal mount o body);
  `.cd-field-stack`/`.cd-landrows`/`.cd-landrow` (form dung, MIN-120
  direction da chot); landrow input 44px qua var(--cd-tap).
- Verify: npm test 197/197 (gom +13 model draft tests); static 72/72;
  shell py 303/303; services 66/66; contract validator 44 files 0
  unexpected; git diff --check sach; verify.ps1 completed (khong co
  watch-list cho services — skip hop le).
- CDP headless: `.agent/scratch/cdp_min119.mjs` — 9/9 PASS cho
  node<->node swap, node->Pool unassign, Pool->node (xem MIN-119).

## Log 2026-09-27 (backend xong)

- `InheritanceCase.workspace_idempotency_key` + migration map
  `database.py` ("workspace_idempotency_key": VARCHAR(64)).
- `workspace_get` case object giờ trả thêm
  `ngay_lap_ho_so`/`noi_niem_yet`/`ghi_chu`.
- Adapter: `workspace_create` handler; `intake_analyze` +
  `diagram_evaluate` có draft branch (`case_id` absent → bỏ kiểm tra
  case, `stage` bắt buộc ở evaluate; `null` → validation_error).
- Registry: `notary.workspace_create` qua `_notary_drafting`.
- Mock: `_MockState._idempotency`, `workspace_create` parity (validate
  meta/stage/diagram, assign entity_id, render, created flag),
  `_workspace_data()` dùng chung get/create, draft branches.
- Tests: +16 adapter contract (765 dòng file), +12 mock. Tổng shell
  suite: 303/303 pass.
