# Decisions — MIN-128

Quyết định implementation trong phạm vi P5 (không thay contract; mọi behavior
wire-level theo `contracts/notary-case-drafting.md` §13 đã duyệt 27/09/2026).

## D1 — `case_type` không thêm DB column

- Wire `case.case_type` derive từ `loai_van_ban`: doc thuộc tập two-party
  (`DOC_TYPES_TWO_PARTY`) → `two_party`; doc thuộc nhóm thừa kế → `inheritance`;
  còn lại → case-type không hỗ trợ (giữ behavior `case_type_unsupported`).
- Lý do: `loai_van_ban` đã là SOT legacy cho Word engine + web; thêm column =
  hai nguồn sự thật. Persist `case_type` vào `case_state_json` (schemaVersion 3)
  để read-path không cần suy lại khi loai_van_ban lạ.

## D2 — Legacy projections giữ nguyên

- `InheritanceCaseProperty.is_primary` = (index==0) — thứ tự mảng assets là SOT.
- `tai_san_id` = entity asset[0]; `nguoi_chet_id` = entity của `owner_row_id`
  (inheritance) hoặc people[0] (two_party).
- `engine_state_json` + payload keys `engineInput/engineState/engineResult/
  assignments` giữ shape legacy v2 chỉ cho domain inheritance; two_party không
  ghi engine projections.
- Web cũ/Word engine không đổi.

## D3 — Node v3 ↔ legacy flags

- v3→legacy (persist/engine input): `isLandOwner = ownPositions ≠ []`,
  `willReceive = receivePositions ≠ []`.
- legacy→v3 (migration-on-read): flag true → positions `[1..min(len(assets),3)]`.
- Seed mặc định client: owner `ownPositions=[1]`, spouse/children
  `receivePositions=[1]` — UI convenience, P6/P7 chỉnh được.

## D4 — Commit prune vs save reject (theo contract)

- Commit stage: personId ngoài stage mới → prune khỏi committed diagram
  (cả hai domain); positions > len(assets) → prune + `diagram.selection_pruned`.
- Diagram save/evaluate: personId ∉ stage → `diagram_reference_outside_stage`
  (reject); positions ∉ {1,2,3}/trùng → `diagram_validation_error`;
  positions > len(assets) tại save → prune + warning (không reject).
- Model client: `removeStageRow` KHÔNG prune draft diagram ngay (§13.2/Q2 —
  Hủy phải restore được); prune mirror chỉ khi `commitStage` thành công.

## D5 — `cancelDraft()` (Hủy thay đổi)

- Restore cả Stage lẫn Diagram draft về committed baseline, clear dirty flags +
  fieldErrors. Case mới (draft): reset về baseline rỗng/seed, giữ `draftId`
  (idempotency key không đổi).

## D6 — Two-party Word/intake boundaries

- `word_export_options`/`word_export_batch` trên two_party → `case_type_unsupported`.
- `intake_analyze` trên two_party → cho phép (capabilities.intake đầy đủ).
- Real adapter thêm check `loai_van_ban ∈ DOC_TYPES_TWO_PARTY` trong `_word_case`
  (batch) + options — trước đây "unreachable" vì chỉ có inheritance.

## D7 — Pool non-empty hạ `status: incomplete` (real↔mock parity)

- `evaluate_diagram`/`commit_stage` (real): stage person chưa gán node nào →
  warning `diagram.unassigned_pool_person` + nếu engine trả `status:"complete"`
  thì hạ xuống `"incomplete"`; status khác (`invalid`/`unsupported`) giữ nguyên.
- Lý do: parity với v1 + mock adapter (mock suite assert `incomplete`);
  contract cho phép `incomplete` và Pool non-empty nghĩa là draft chưa trọn.

## D8 — Thứ tự check trong `diagram_save`/`workspace_create`

- Lock → domain → validate wire v3 → owner mirror (`diagram_owner_mismatch`)
  → personId refs (`diagram_reference_outside_stage`). Hệ quả test: muốn hit
  `outside_stage` phải gán personId lạ vào node KHÔNG phải `owner`.
- `commit_stage` two_party KHÔNG suy assignment p1..p30 từ stage.people —
  assignments thuộc `diagram_save`; Stage commit chỉ canonicalize + preserve.
