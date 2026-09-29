# Tab Soạn hồ sơ (Electron) — hành vi và mô hình dữ liệu

**Spec đích cho tab `Soạn hồ sơ` trên Electron — owner đã duyệt qua [MIN-104](https://linear.app/minhnotary/issue/MIN-104) ngày 24/09/2026; runtime đã triển khai qua MIN-106…MIN-112, verify MIN-113 (chờ owner duyệt cutover).**
Ngày: 24/09/2026 · Owner: platform/case-workspace · Spec: MIN-104 · Goal triển khai: MIN-107…MIN-112

> **Cập nhật MIN-138 (29/09/2026):** file này là nguồn chi tiết để đối chiếu
> **hành vi/dữ liệu**; SOT dài hạn nằm trong
> [`docs/spec/notary_v2/`](./README.md). Lớp
> **thị giác/bố cục mới** (bảng chuyển vị Tài sản,
> dialog loại đất, chip vị trí trên node, action bar) nằm ở
> [`visual-reference.md`](./visual-reference.md) +
> [`docs/spec/ui/`](../ui/README.md) — phần đó
> là hướng đã duyệt bằng ảnh và token trong `docs/spec/ui/`. Khi nội dung hai
> lớp trông mâu thuẫn (vd hình thức card Tài sản, nút `Chủ đất`/`Nhận` ↔
> chip số), **hành vi/dữ liệu lấy file này làm chuẩn**, hình thức lấy
> `visual-reference.md`. Các quyết định nghiệp vụ mới (chip vị trí ↔ tài sản,
> `Hủy thay đổi`, Apply loại đất) đã được **owner duyệt tại
> `contracts/notary-case-drafting.md` §13 (`notary.case-drafting.v2`,
> APPROVED 27/09/2026, MIN-125)** và đã triển khai qua MIN-128/MIN-129/
> MIN-130 — renderer Electron emit v2 theo §13.1.

## 1. Vai trò tài liệu và ranh giới

- File này giữ **chi tiết đã duyệt để đối chiếu** của tab `Soạn hồ sơ`
  (đích Electron): mô hình Stage/Pool/Diagram, semantics commit và
  revision/conflict, draft trong phiên, suggestion, gating `case_type`, và
  map hành vi → command đích.
- Quyết định **cấp sản phẩm/UX** (taxonomy module/tab, luồng, bố cục, bảng
  nút, danh mục trạng thái UI, UX xuất Word, loại trừ) thuộc
[`docs/spec/notary_v2/README.md`](./README.md) —
  file này tham chiếu, không chép lại.
- **Thị giác/bố cục đích** (palette, token, bảng chuyển vị, dialog loại
đất, node chip, zoom sơ đồ) nằm ở `visual-reference.md` cùng thư mục +
[`docs/spec/ui/`](../ui/README.md) — file này không định nghĩa
màu/kích thước.
- **Wire contract** `desktopcommand.v1` cho các command đích đã publish tại
  `contracts/notary-case-drafting.md`: §1–12 là `notary.case-drafting.v1`
  (owner duyệt 24/09/2026 qua [MIN-105](https://linear.app/minhnotary/issue/MIN-105),
  rev 1.1 additive MIN-121 — vẫn hợp lệ cho consumer legacy); §13 là
  `notary.case-drafting.v2` (APPROVED 27/09/2026, MIN-125) — contract
  runtime của luồng Electron mới (MIN-128 trở đi). File `contract.md` cạnh file này là ghi chú cơ
  chế domain *provisional, non-normative*, **không phải** wire contract; ba
  invariant trong đó (Stage sở hữu người đã commit; Pool derived; Pool/Diagram
  không mutate Stage) trùng khớp spec này.
- [`diagram/inheritance/web-workflow.md`](./diagram/inheritance/web-workflow.md) giữ bằng chứng **hiện trạng web**
  (`frontend/templates/cases/form.html`, bản fallback đến cutover). File này
  mô tả **đích Electron**; khác biệt liệt kê có bằng chứng ở §9. Không giả
  định backend đã có gì ngoài bằng chứng nêu tại §9.
- Nghiệp vụ tính thừa kế: [`diagram/inheritance/business-rules.md`](./diagram/inheritance/business-rules.md) là DRAFT chưa
  duyệt — chỉ trích ở mức đích nghiệp vụ; điểm tranh chấp công thức
  `Người không nhận` đã được owner chốt giữ workflow.md (§6).
- Rule "không tách shared abstraction cho Stage/Pool đến khi có domain thật
  thứ hai" (README L10) vẫn giữ — spec này mô tả hành vi inheritance-first,
  không đề xuất abstraction mới.

## 2. Mô hình dữ liệu: Stage / Pool / Diagram / Draft

- **Stage** là nguồn chuẩn đã xác nhận của hồ sơ, gồm **Người và Tài sản**.
  Mỗi dòng Stage mang `row_id` (do UI tạo, ổn định qua commit/reload, dùng để
  gắn lỗi đúng dòng) và `entity_id` (ID DB, `null` trước lần commit đầu).
  Kiểu/giá trị chính xác của các khóa này →
  `contracts/notary-case-drafting.md` (đã publish, MIN-105); spec này chỉ khóa
  semantics.
- **Pool** là projection, **không được lưu** như nguồn dữ liệu riêng:

  ```text
  Pool = Stage đã commit − phần tử đang được gán trên Diagram
  ```

  Pool chỉ tính lại khi Stage commit thành công hoặc draft Diagram đổi.
- **Diagram** lưu gán quan hệ/vai trò giữa các phần tử của Stage đã commit:
  person→slot/node, quan hệ, chủ đất, người nhận cho tài sản hiện tại, render
  metadata. Diagram chỉ được tham chiếu `row_id`/`entity_id` tồn tại trong
  Stage đã commit, và **không sửa** dữ liệu Người/Tài sản của Stage (§6).
- **Draft** là mọi thay đổi chưa commit: dòng Stage thêm/sửa/xóa chưa
  `Cập nhật`, gán trên Diagram chưa `Lưu sơ đồ`. Draft chỉ sống trong phiên
  (§4), không phải nguồn dữ liệu.
- **Suggestion** là kết quả intake chờ người xác nhận — không phải Stage,
  không phải draft (§5).

## 3. Commit Stage — atomic, revision, conflict

- `Cập nhật` = commit **toàn bộ Stage** (Người + Tài sản) trong **một
  transaction**: validate → upsert/link → prune Diagram → tăng `revision` →
  commit. Một dòng sai → Stage không đổi; không có trạng thái half-saved.
- Lỗi validation trả về gắn **`row_id` + field**; UI tô lỗi ngay đúng dòng
  (UX → spec UX §5).
- Mọi thao tác ghi kèm `base_revision` (số nguyên ≥ 1) chống ghi đè thay đổi
  mới hơn. Server có `revision` mới hơn `base_revision` → lỗi
  `workspace_conflict`: UI cho tải bản mới hoặc giữ bản nháp để sao chép;
  **không có nút ghi đè cưỡng bức** (UX conflict → spec UX §6).
- Xóa một người/tài sản khỏi Stage rồi `Cập nhật` → backend prune mọi tham
  chiếu Diagram tới phần tử đó trong cùng transaction (giữ metadata hợp lệ;
  tiền lệ `_prune_engine_state` `routers/cases.py:1348-1404`).
- Hồ sơ `locked` → mọi write bị từ chối; UI toàn màn chỉ đọc (vẫn xem/sao
  chép). Hiện trạng đã có guard `cases.py:803`.
- Commit Stage thành công là điều kiện duy nhất làm Pool tính lại; commit
  Diagram **không** đổi Stage.

## 4. Draft chỉ sống trong phiên

- Draft **chỉ tồn tại trong phiên UI**: không persist draft chứa PII vào
  `localStorage`, log, diagnostics hay file tạm. Hiện trạng web giữ OCR
  staging draft trong `localStorage` (`form.html:11084-11085` `_stagingKey()`)
  — đích Electron **bỏ** cơ chế này.
- Rời màn/đổi module/đóng app khi còn draft → cảnh báo có thay đổi chưa lưu
  (hình thức dialog → spec UX §6). Đổi module không được mất draft đang mở
  (SM-07 — state giữ ở renderer).
- Poll/refresh job từ sidecar không ghi đè field người đang sửa (merge
  field-level theo convention chung).

## 5. Suggestion từ intake — không bao giờ `confirmed`

- Intake thủ công đích nhận năm loại nguồn: **`image`, `pdf`, `docx`,
  `xlsx`, `text`** (ảnh giấy tờ/PDF qua OCR, DOCX/XLSX/text parse), qua
  `notary.intake_analyze` (§8). Excel import là một nguồn intake trong tab —
  đích đưa Excel qua **cùng đường review** như các nguồn khác (khác hiện
  trạng ghi DB ngay, §9).
- Mọi kết quả intake là **gợi ý**: `observation_state` ∈
  `{observed, normalized, inferred}`, kèm `raw_value`, `normalized_value`,
  `confidence`, `source_refs`, warning/lỗi theo từng nguồn.
- Suggestion **không bao giờ** mang trạng thái `confirmed`; response không
  có field `confirmed=true`. Xác nhận duy nhất = người dùng đưa gợi ý vào
  Stage (thành draft) rồi bấm `Cập nhật` (commit §3).
- Suggestion không được tự: ghi vào hồ sơ, tạo quan hệ trên Diagram, chọn
  người nhận, hay xuất Word.
- Không có nút/popup/command/trạng thái Zalo trong tab — câu loại trừ duy
  nhất (chi tiết ranh giới → spec UX §8).

## 6. Diagram — chỉ gán quan hệ, không sửa Stage

- Diagram chỉ **gán**: person→slot/node, quan hệ, `Chủ đất`, `Nhận` cho tài
  sản hiện tại; lưu render metadata. Lưu Diagram (`diagram_save`) không đổi
  Stage; sửa Người/Tài sản chỉ qua Stage.
- Trên card chỉ có hai quyết định: `Chủ đất` và `Nhận`; **không có** `★`,
  `Từ chối`, hay nút unset riêng (giữ rule workflow.md §6). `Người từ chối`
  chỉ đến từ dữ liệu pháp lý xác nhận riêng, không suy ra từ `Nhận`.
- Xóa thẻ khỏi Diagram → trả thẻ về Pool **chỉ nếu** Stage vẫn còn phần tử
  đó; thao tác Pool/Diagram không được xóa phần tử khỏi Stage.
- `Xem cách tính` chỉ **đọc** output engine; UI/JavaScript không tự tính tỷ
  lệ hay rule thừa kế. Tính toán chạy phía Python qua `diagram_evaluate`
  (đánh giá draft, không persist) và `diagram_save` (§8).
- Persist đích: Diagram state lưu assignment/quan hệ/render metadata do người
  tạo; output tính toán (allocations/warnings) là dữ liệu engine trả về lúc
  evaluate/save — shape persist chính xác → `contracts/notary-case-drafting.md`. Hiện trạng
  web persist `engineState` lẫn trong `diagram` (`form.html:8474-8483`).
- **Đã chốt (owner 24/09/2026):** giữ công thức `Người không nhận = Tất cả
  người trên Diagram − Chủ đất − Người nhận` (workflow.md L146). Tranh cãi với
  `diagram/inheritance/business-rules.md` §11.3 (DRAFT — đánh dấu sai vì bỏ sót
  chủ đất sống đã tắt `Nhận` ở vòng khác và không phân biệt `chưa quyết`) được
  owner quyết định theo phương án giữ công thức hiện tại; §11.3 nếu được duyệt
  sau này phải sửa lại cho khớp quyết định này.

## 7. `case_type` — V1 chỉ thừa kế

- Backend thật V1 chỉ cam kết `case_type = inheritance`. Contract có
  `case_type` + `capabilities` để mở rộng sau; loại việc chưa có engine phải
  hiện **`Chưa hỗ trợ`** — không chạy logic giả, không giả kết quả.
- `Chưa hỗ trợ` ở đây là nhãn **cấp loại việc** (UI gating khi mở hồ sơ),
  khác `unsupported` **cấp kết quả engine** trong spec.md §8 (DRAFT) — hai
  tầng riêng, spec này không gộp.
- `capabilities` trong workspace response cho UI biết intake/diagram/
  word_export phần nào bật cho hồ sơ hiện tại (shape →
  `contracts/notary-case-drafting.md`).

## 8. Map hành vi → command đích (envelope `desktopcommand.v1`)

| Hành vi tab | Command đích | Tính chất |
|---|---|---|
| Tải workspace khi mở hồ sơ (case + Stage + Diagram + revision + capabilities) | `notary.workspace_get` | read-only |
| Phân tích file/text thành gợi ý (§5) | `notary.intake_analyze` | long-running, không commit |
| `Cập nhật` Stage (§3) | `notary.workspace_commit_stage` | atomic write, `base_revision` |
| Đánh giá/tính thử draft Diagram (§6) | `notary.diagram_evaluate` | read-only theo DB, không persist draft |
| `Lưu sơ đồ` (§6) | `notary.diagram_save` | atomic write, `base_revision` |
| Liệt kê văn bản/mẫu sẵn sàng hoặc bị chặn khi mở popup Xuất Word | `notary.word_export_options` | read-only |
| Tạo nhiều DOCX vào folder đích (UX → spec UX §7) | `notary.word_export_batch` | long-running, per-item result |
| `Lưu hồ sơ` lần đầu của nháp mới (spec UX §2) | `notary.workspace_create` | atomic write, idempotent, `idempotency_key` |

- `notary.intake_analyze` và `notary.diagram_evaluate` hỗ trợ **chế độ
  nháp** (không `case_id`): intake trả suggestion không gắn hồ sơ;
  evaluate nhận `stage` trong payload và trả `evaluated_revision: null`
  — không ghi DB. `case_id: null` tường minh là lỗi validation.

- Envelope `desktopcommand.v1` đã APPROVED (`contracts/desktop-command.md`):
  request `contract_version`/`command_id` (uuid v4)/`command`/`payload`/
  `client_meta`; job status `accepted|running|waiting_user|partial|
  succeeded|failed|canceled`; `partial` bắt buộc `result.data.breakdown`;
  error `code/message/retryable/next_action/details`. File này chỉ viện dẫn,
  không định nghĩa lại.
- Version theo domain đặt **trong** `result.data.schema_version` =
  `notary.case-drafting.v1` (convention đã chốt ở MIN-105 — envelope không
  quy định).
- Wire contract chính thức = `contracts/notary-case-drafting.md` +
  schema/examples — **đã publish trong MIN-105** (rev 1.1 additive MIN-121).
  Namespace `notary.*` đã được module `document-review` claim
  (`shell/src/main/registry.js:18`) — giữ namespace này.
- Hiện trạng shell (đã cập nhật sau MIN-106…112): ngoài 12 command cũ
  (`notary.case_get/case_create/customer_list/customer_create/
  property_list/property_create/participant_add/word_templates/
  export_word`, `ocr.analyze`, `zalo.status` — `zalo.status` là bằng chứng
  loại trừ: command tồn tại ở shell nhưng tab này không dùng), 7 command
  §8 **đã tồn tại** và route qua `notary_gateway.dispatch`
  (`command_registry.py` `COMMANDS.update` cuối file); `case_list` cũng
  qua gateway để mock parity. `notary_gateway.py` chọn
  `notary_mock_adapter.py` chỉ khi `G1_DEV_NOTARY_MOCK=1` **và** không
  packaged (`sys.frozen`) — packaged luôn real.

## 9. Hiện trạng web ↔ đích Electron (theo khối, có bằng chứng)

| Khối | Hiện trạng web/shell (file:line) | Đích Electron |
|---|---|---|
| Nguồn intake | 3 kênh không đối xứng: ảnh OCR (`form.html:2405` `accept="image/*"`; `routers/ocr_ai.py:2641-2644` chỉ nhận ảnh); Excel **ghi DB ngay** không review (`routers/customers.py:356-358`, `:387-413`); nhập tay: Người → draft Stage (`form.html:7950-7959`) nhưng Tài sản → DB ngay (`form.html:8107-8149` `/properties/inline-create`). Không có PDF/DOCX/text; markitdown chỉ POC (`tools/document_conversion_poc/`). | 5 loại `image/pdf/docx/xlsx/text` qua `notary.intake_analyze`; mọi nguồn — kể cả Excel và `+ Tài sản` — đều thành suggestion/draft, commit một lần qua `Cập nhật` |
| Suggestion/review | OCR có review trước khi vào Stage: raw text readonly (`form.html:10411-10414`), card editable (`:10428+`), `Lưu` → `saveOcrResultsToStage` (`:10612-10621`) → `addToOcrStaging` (`:11682-11818`). Không có `observation_state`/`confidence`/`source_refs`. Excel/Property bypass review. | Mọi suggestion mang `observed|normalized|inferred` + confidence + source_refs; không `confirmed` (§5) |
| Stage commit | Person ghi per-row trước (`/customers/inline-create`, `/quick-update` — `form.html:11974`) rồi snapshot `case_state_json` qua `POST /cases/{cid}/stage-update` (`routers/cases.py:800-835`): atomic ở mức JSON nhưng không gồm person upsert, không `base_revision`. `case_state_json.stage` chỉ chứa **người** (`form.html:8474-8483`); tài sản nằm ở `InheritanceCaseProperty` link. | `workspace_commit_stage` gom mọi write + prune Diagram + tăng revision trong **một transaction**; Stage = Người **và** Tài sản; lỗi theo `row_id`/field (§3) |
| Pool | Đã đúng ý tưởng derived: `getPoolCandidateCustomerIds` (`form.html:5781-5785`) trừ `getDiagramAssignedStageIds` (`:5761-5765`); không persist. | Giữ nguyên tắc; contract hóa là projection (§2) |
| Diagram + engine | ReactFlow gán person→slot, `isLandOwner`/`willReceive` (`ReactFlowApp.jsx:317`, `:700-708`); **`frontend/static/inheritance_engine.js` THIẾU FILE** (`form.html:8638` load nhưng file không tồn tại → fallback `engine_missing`, share `0.00` — `ReactFlowApp.jsx:743-748`); engine Python `services/inheritance_engine.py` (`ENGINE_VERSION=2`, `:17`) **không router nào gọi**; `engineState` persist lẫn trong `diagram` (`form.html:8474-8483`); prune refs khi Stage xóa (`cases.py:1348-1404`). | Engine Python tính qua `diagram_evaluate`/`diagram_save`; Diagram persist chỉ assignment/render (§6); không engine JS phía client |
| Revision/conflict | Không có `workspace_revision`/`updated_at` trên `InheritanceCase` (`models.py:92-107`); hai tab sửa cùng case = last-write-wins. | `revision`/`base_revision` + `workspace_conflict` (§3) |
| Locked | `trang_thai`/`is_locked` (`models.py:106-107`); guard `cases.py:803`, `participants.py:24-25`; badge `detail.html:10-28`. | Giữ: locked → toàn màn chỉ đọc, vẫn xem/sao chép |
| Word export | 1 template → 1 DOCX browser download (`routers/cases.py:1610-1663`; `form.html:3896-3903`; `detail.html:29-31`); preview/export-draft cũng một file. | Batch nhiều văn bản → một folder, per-file result (UX → spec UX §7); `word_export_options`/`word_export_batch` |
| Draft persist | OCR staging draft trong `localStorage` (`form.html:11084-11085`). | Bỏ — draft chỉ trong phiên (§4) |
| Zalo trong màn hồ sơ | `form.html` có **0** tham chiếu Zalo (grep toàn file); `zalo.status` tồn tại ở shell command surface nhưng tab không gọi — bằng chứng loại trừ, không phải control của tab. | Giữ: không nút/popup/command/trạng thái Zalo trong tab (§5) |
| Shell command surface | 12 command qua `notary_adapter.py` — 10 `notary.*` + `ocr.analyze` + `zalo.status` (bằng chứng loại trừ, tab không dùng — `command_registry.py:187-216`); directory picker `pickFiles({directory:true})` đã end-to-end (`shell/src/main/main.js:32-48`, `ipc.js:67-71`, dùng ở `renderer.js:522`); `is_dir` chưa nằm trong FileRef contract (`contracts/desktop-command.md` §6). | 7 command §8 đã publish trong `contracts/notary-case-drafting.md` (MIN-105; `workspace_create` thêm ở rev 1.1/MIN-121); pin `is_dir` cho directory FileRef vẫn là điểm mở ở envelope |

## 10. Điểm mở và ngoài phạm vi

Điểm mở ban đầu đã được chốt: MIN-125 (P2) đưa đề xuất vào
`contracts/notary-case-drafting.md` §13 và §13 đã **APPROVED 27/09/2026**
(`notary.case-drafting.v2`), triển khai ở MIN-128…MIN-130; các quyết định
đã duyệt:

- Ngữ nghĩa **chip vị trí ↔ tài sản** trên node sơ đồ: đề xuất §13.4 —
  `ownPositions`/`receivePositions` ⊆ {1,2,3} thay `isLandOwner`/
  `willReceive`; dấu chọn bám **vị trí**, không bám `row_id` khi reorder/
  xóa (Q4). Cài đặt ở P7 (MIN-130); xem `visual-reference.md` §5.
- Mô hình **hai bên 30 vị trí**: đề xuất §13.5 — domain `two_party`, node
  cố định `p1..p30` (bên suy từ số, `p16` = ghế đầu bên B), ô trống giữ
  nguyên không dồn; `word_export` = `case_type_unsupported`, `evaluate` =
  `unsupported` (không đi vào engine thừa kế). Cài đặt P7.
- `Hủy thay đổi`: đề xuất §13.2 — client-only, restore **cả** Stage lẫn
  Diagram về committed (Q2); xóa row trong draft không prune diagram
  ngay, prune chỉ ở `Cập nhật`.
- `Áp dụng` trong dialog loại đất: theo đề xuất §13.2/§13.3 — apply ghi
  vào `land_rows` của **draft buffer** (chỉ persist qua `Cập nhật`),
  không commit riêng.
- `stage.owner_row_id` (chỉ định người để lại trong Stage) + create
  không cần diagram — đề xuất §13.6/Q1 phá vòng phụ thuộc Pool của hồ
  sơ mới.
- Giới hạn intake (số file/trang/byte/độ dài text) và chính sách retry
  từng adapter — backend; wire-level đã có ở contract, giới hạn số chưa
  chốt.
- `document_key` danh mục văn bản cụ thể cho từng `case_type`/`document_type`
  — spec nghiệp vụ + contract; với `two_party` xem Q11 tại §13.13
  (danh mục `document_type` mới chờ chốt với NV2).
- Tập đầy đủ câu hỏi và quyết định (Q1–Q12 đã duyệt; C1–C4 xử lý theo
  §13.13): `.agent/tasks/MIN-125/decisions.md`.

Ngoài phạm vi file này:

- Quyết định UX/layout/trạng thái màn hình → spec UX cấp sản phẩm.
- Parser/ghép/nhóm hồ sơ từ nguồn Zalo — module Zalo riêng
  (`input/zalo/README.md`); tab này chỉ có câu loại trừ.
- Loại việc ngoài thừa kế ngoài việc hiện `Chưa hỗ trợ`.
  (Luồng "nháp mới" đã được chốt vào phạm vi qua MIN-121/122 — xem §8.)
- Web cũ `form.html` giữ nguyên làm fallback; không đưa logic mới vào đó —
  nếu phải sửa để tương thích, chỉ gọi service mới (plan §3).
