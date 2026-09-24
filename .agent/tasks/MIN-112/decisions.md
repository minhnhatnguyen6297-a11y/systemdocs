# Decisions — MIN-112

## 2026-10 — Opaque file token: resolve ở main ngay trước forward sidecar

- **Chọn:** renderer chỉ giữ `{file_token,name,size_bytes,is_dir}`; main
  giữ `Map token→FileRef` (UUID, `scope:'machine_local'`);
  `submitCommand` walk đệ quy payload thay mọi node `{file_token}` —
  token lạ → `validation_error`, không forward.
- **Lý do:** brief MIN-112 ghi rõ pickFiles trả path thật là renderer
  forge được; resolve đệ quy (không hardcode `sources[].file_ref`/
  `destination`) chịu được mọi vị trí token mà không leak path.
- **Loại bỏ:** resolve ở preload (không có quyền stat/giữ map) hoặc gửi
  `file_token` thẳng lên sidecar (sidecar là process khác, phải resolve
  trước; đẩy token-store vào sidecar làm rỗng boundary).
- **Nguồn:** brief MIN-112 "OPAQUE FILE TOKEN — yêu cầu bảo mật cốt lõi".

## 2026-10 — Sibling key trong `{file_token}` node bị bỏ qua khi resolve

- **Chọn:** node resolved chỉ chứa `{path, scope, size_bytes?, is_dir?}`
  lấy từ store — `name`/`size_bytes` renderer tự khai không forward.
- **Lý do:** chặn renderer khai sai metadata file (size_bytes ảnh hưởng
  intake routing phía sidecar).
- **Nguồn:** cùng ràng buộc bảo mật trên; shape forward khớp FileRef
  contract desktopcommand §6.

## 2026-10 — `registerDroppedFile` trả `data:{file:entry}`

- **Chọn:** shape `{ok:true,data:{file:{file_token,...}}}` — cùng mô
  típ `pickFiles` → `data.files[]`; renderer dùng chung `addEntry`.
- **Lý do:** preload comment + intake-dialog đã assume `r.data.file`;
  đồng nhất shape giảm nhánh.
- **Nguồn:** fix trong phiên sau khi phát hiện mismatch handler↔renderer.

## 2026-10 — `notary.case_list` chuyển route qua notary gateway

- **Chọn:** `COMMANDS["notary.case_list"] = _notary_drafting("case_list")`
  thay `_notary("case_list")`; mock adapter implement `case_list` +
  `_mock_case_row` cùng shape/ordering/query-semantics real
  (`_case_row`, `id DESC`, substring filter trên serialized row).
- **Lý do:** deferred MIN-111 yêu cầu mock parity cho overview tab;
  gateway là seam mock/real đã có — không thêm seam mới.
- **Loại bỏ:** mock riêng ở renderer (cấm — một component chung, swap
  qua backend seam theo brief).
- **Nguồn:** brief MIN-112 mục "Deferred từ MIN-111".

## 2026-10 — `onUnsavedChange` emit từ `model.emit()` thay vì per-action

- **Chọn:** `emit()` so `stageDirty||diagramDirty` với `lastUnsaved`,
  gọi `deps.onUnsavedChange(u)` khi đổi.
- **Lý do:** mọi mutation draft đều đi qua emit (touch*/commit/save/
  applyWorkspace/resolveConflict) — một điểm duy nhất không sót
  transition; renderer chỉ forward sang `desktop.v1.setDirtyState`.
- **Loại bỏ:** bắt `beforeunload` trong renderer (Electron renderer
  unload không chặn được window close — phải qua main close guard).

## 2026-10 — Reload renderer reset `rendererDirty` + clear token

- **Chọn:** `did-start-navigation` → `fileTokens.clear()` +
  `rendererDirty=false`.
- **Lý do:** reload giết draft cùng renderer cũ; flag cũ để lại làm
  close-guard cảnh báo bóng ma. `will-navigate` đã prevent → navigation
  bị chặn không tới `did-start-navigation`, không clear oan.
- **Nguồn:** brief: clear token khi "app đóng/reload window".

## 2026-10 — Word result normalize ở model, không ở dialog

- **Chọn:** `normalizeWordResult` trong model gom 3 nguồn
  (`job.result.data`, `error.details.documents` compact,
  `breakdown.skipped`→row tổng hợp) về một shape; dialog chỉ render.
- **Lý do:** contract §8.4 có 3 dạng wire (success/partial/
  word_batch_failed/canceled); normalize ở model để test model cover
  được và dialog giữ pure-render.
- **Nguồn:** contract §8.4 + MIN-115 (jobstore giữ result khi cancel).
