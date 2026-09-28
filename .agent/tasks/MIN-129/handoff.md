# Handoff — MIN-129 (P6 của MIN-123)

**Dựng vùng nhập tài sản/người, bảng loại đất và Pool** theo bản mẫu đã
duyệt (`docs/product/ui/prototypes/` + `approved-drafting.png` +
`approved-land-types.png`), contract v2 §13, giữ ranh giới sở hữu P6/P7.

## Commits

- `848cb23` — task records (brief/progress/decisions khởi tạo).
- **<sẽ điền>** — implementation P6 + tests (commit cuối của task này).

## Files đã đổi

| File | Thay đổi |
|---|---|
| `shell/src/renderer/notary/case-drafting-view.js` | Rewrite: actionbar 1 hàng (back/title/case-type select-pill/save-state/Nhập file/Zalo disabled/Hủy/Cập nhật), openModal canonical, transposed asset table (max 3 col, drag+Ctrl arrows, delete confirm), land-types wide modal (draft-only Áp dụng), people row table (owner radio, drag+Ctrl arrows, delete), data-fid focus/value retention, syncChromeUI, cancelDraft (newDraft cho nháp / restore committed cho case), card-level field errors. |
| `shell/src/renderer/notary/case-drafting.css` | Rewrite: toàn bộ scoped `.cd-root`/`cd-*`, token P4 (`--accent`, `--fs-*`, `--row-h`, `--btn-h`, `--pool-bg`…); không `:root`, không re-khai shared class; bổ sung rule cho word-export dialog legacy + intake. |
| `shell/src/renderer/notary/relationship-diagram.js` | Chỉ phần Pool + khung rel-card: `cd-rel-card` (head tools sm / `.cd-rel-body` pool-pane + diagram region / `.cd-rel-foot` Lưu sơ đồ+Xuất Word), pool `.cd-pool`→`.cd-pool-box`→`.cd-pool-card`(drag-handle+`.cd-pool-nm`+`.cd-pool-sub`+`→`), committed-only source, stageDirty gate (pill "Cập nhật Stage trước"), openAssignMenu canonical modal. Canvas/nodes/edges giữ nguyên markup hiện hữu (P7). |
| `shell/src/renderer/notary/intake-dialog.js` | Canonical modal-head/body/foot; `cd-src-*`→`cd-intake-*`, `cd-dropzone-on`→shared `.drop-hint`. Luồng/wire `file_token` không đổi. |
| `shell/test/dom-stub.mjs` | MỚI — DOM stub dùng chung cho view tests. |
| `shell/test/notary-case-drafting-view.test.mjs` | MỚI — 17 test hành vi view. |
| `shell/test/notary-case-drafting-static.test.mjs` | Cập nhật test Zalo (placeholder disabled được phép) + test CSS (token P4/scope). |

`case-drafting-model.js` **không đổi**. Không đổi `index.html`,
`renderer.js`, `styles.css`.

## Test

```
cd shell && node --test test/*.test.mjs     → 239/239 pass (222 cũ + 17 mới)
cd shell && node --test test/notary-case-drafting-view.test.mjs → 17/17
git diff --check                            → clean
```

## Model API đã dùng

`openCase`, `newDraft`, `updateCaseMeta`, `saveDraft`, `commitStage`,
`addPerson`, `addAsset`, `updatePersonField`, `updateAssetField`,
`moveAsset`, `setOwnerRow`, `removeStageRow`, `fieldErrorsFor`,
`canWrite`, `hasUnsaved`, `dismissNotice`, `subscribe`, `state`,
`assignPerson`, `movePerson`, `addSlot`, `setNodeRelation`,
`toggleNodePosition`, `removeNode`, `saveDiagram`, `evaluateDiagram`,
`intakeAnalyze`, `acceptSuggestion`, `discardSuggestion`,
`resolveConflict`, `mockBanner`, `diagramDomain`, `documentTypesFor`,
`capabilities`/`caseInfo`/`locked`/`unsupported`/`stale`/`conflict`/
`busy`/`fieldErrors`/`diagramErrors`/`diagramWarnings`/`renderModel`/
`evaluatedRevision`/`wordBusy`/`suggestions`/`intakeErrors`/`backendMode`.

## Model API gaps (đề xuất bổ sung — view đang workaround)

1. **`model.cancelDraft()`** — không có. View thực hiện bằng
   `cancelDraftState(state)` (mutate field public) + `dismissNotice()`
   để emit; nháp mới dùng `newDraft()`. Nên export hàm chính thức +
   emit, để `onUnsavedChange`/session guard chuẩn.
2. **`model.movePersonRow(rowId, toIndex)`** — không có (chỉ
   `moveAsset`). View splice `state.stage.people` +
   `fieldErrors` filter + `stageDirty` qua `movePersonRowState`.
   Reorder people ảnh hưởng thứ tự phụ lục [Người N] — nếu đây là
   nghiệp vụ có ý nghĩa thì nên là API model.
3. **`model.committedPool()`** — `pool()` dùng `state.stage` khi
   `caseId == null` → vi phạm "Pool chỉ committed". View tự tính từ
   `state.committed`; model nên expose nguồn committed rõ ràng (hoặc
   `pool()` nên luôn committed-only).
4. **Emit-only API** — cả 2 workaround trên đều cần `dismissNotice()`
   làm emit trigger; một `model._emit()`/`touch()` chính thức sẽ sạch
   hơn.

## Pool contract (cho P7 / MIN-130)

- **Payload:** `dragstart` → `dataTransfer.setData('text/plain',
  JSON.stringify({ kind: 'person'|'asset', row_id }))` — **không đổi**.
- **Drop xuống node:** `{kind:'person', row_id}` →
  `model.movePerson(row_id, nodeId)`; drop xuống `.cd-pool-box` →
  `model.movePerson(row_id, null)` (bỏ gán). `.drop-hint` khi hover.
- **DOM/classes P7 dùng:** `.cd-pool` (pane), `.cd-pool-box` (drop
  target + list), `.cd-pool-card` (`.dragging` khi kéo),
  `.cd-pool-card .cd-pool-nm` (tên), `.cd-pool-sub` (meta phân biệt
  trùng tên), nút `→` (menu `Gán vị trí` — keyboard alternative).
- **Nguồn dữ liệu:** `state.committed` trừ `personId` đã gán trên
  `state.diagram.nodes` — committed-only, KHÔNG phải `model.pool()`.
- **Bên ngoài Pool (P7 sở hữu):** `.cd-diagram` region trong
  `.cd-rel-body` — markup nodes/edges/calc hiện hữu giữ nguyên;
  `.cd-rel-foot` chứa `Lưu sơ đồ`(secondary, `.js-save-diagram`,
  dirty-dot) + `Xuất Word`(primary). Gate `stageDirty` disable
  evaluate/calc/save — nếu P7 đổi UX gate, giữ nguyên tắc "evaluate/
  save không chạy khi Stage chưa cập nhật trên case thật".

## Ranh giới chưa verify / cần kiểm tra tay

- **Chưa chạy Electron thật** — DOM stub pass, layout pixel chưa so
  với PNG ở viewport thật (1280×800/1440×900). Đặc biệt: bảng Người 9
  cột cuộn ngang, sticky `.cd-rowlabel` chồng z-index với sticky
  header `table.grid` (z1 vs z2 — cố ý, cần xem mắt).
- `getBoundingClientRect` drop-above/below cho hàng người chỉ kiểm
  bằng stub (rect giả) — cần thử kéo-thả thật.
- `structuredClone` trong renderer — Electron 28+ có sẵn (Node ≥17);
  nếu target cũ hơn, đổi lại clone helper.
- Modal append vào `.cd-root` (không `document.body`) — `position:
  fixed` vẫn phủ viewport; kiểm tra khi `.cd-root` nằm trong vùng
  `transform`/`overflow` của shell (không có ở layout hiện tại).
- Focus restore qua `data-fid`: caret chỉ khôi phục cho input text
  (`setSelectionRange`); select/radio chỉ khôi phục focus.
- `word-export-dialog.js` vẫn dùng `openModal` không-bare → padding
  `.cd-modal` — kiểm tra nhanh dialog Word khi P7 làm việc tiếp.
- Các class `cd-tp-slots`/`cd-tp-slot`/`cd-diagram-canvas`/`cd-node-*`
  giữ lại trong CSS cho markup hiện hữu — P7 có thể thay khi làm
  canvas thật.
