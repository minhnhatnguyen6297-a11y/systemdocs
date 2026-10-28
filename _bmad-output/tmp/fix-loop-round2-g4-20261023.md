# Biên bản vòng 2 — lát G4 (Soạn hồ sơ một bản đang sửa, một lần Lưu hồ sơ)

- **Nhánh:** `agent/omp/drafting-e2e-fixes`
- **Base lát G4:** `1bd248d` (G3 tiếp); HEAD khi viết: `ea719a9`
- **Phạm vi:** G4 — bỏ nút Cập nhật/Lưu nháp, Stage/Pool/Diagram/evaluate dùng chung bản đang sửa; chỉ `notary.workspace_save_case` ghi snapshot soạn thảo; Word detach/bind thành sửa local; giữ guard mất dữ liệu hiện có.
- **Quyết định:** [`decision-owner-drafting-single-save-20261023.md`](../decisions/decision-owner-drafting-single-save-20261023.md) (commit `59b8778`).
- **Thiết kế:** [`g4-design-20261023.md`](g4-design-20261023.md) (commit `198f66f`), §7.4 là kỳ vọng test vòng 1 phải giữ, §8 là G6/E2E chưa mở gate.
- **Phương pháp:** test tự động trước (Node + pytest, đối chiếu tên fail với worktree baseline `198f66f`), E2E sau — mục E2E để §7. Không sửa code/test trong lượt khôi phục này; mọi số liệu lấy từ chạy thật, file thô ở [`g4-test-compare.txt`](g4-test-compare.txt).

## §1. Quyết định và tài liệu đã đồng bộ

| Commit | Nội dung |
|---|---|
| `59b8778` | Decision owner: Soạn hồ sơ dùng một trạng thái đang sửa; **Lưu hồ sơ** là lần ghi DB duy nhất của luồng soạn; nêu phương án đã loại (giữ Cập nhật, autosave khi rời). |
| `080ab2d` | Đồng bộ contract `contracts/notary-case-drafting.md` và spec `_bmad-output/specs/{README, notary_v2/README, notary_v2/diagram-rules, notary_v2/word-templates, product-overview, shared/data-rules, ui/README}.md` theo một lần lưu. |
| `198f66f` | Thiết kế G4 đầy đủ (model/view/Word/test/E2E) + chỉnh contract liên quan. |

Spec/decision ghi trực tiếp quy tắc đang áp dụng; biên bản này chỉ là bằng chứng triển khai và test, không thay nguồn chuẩn.

## §2. Bản đồ đường ghi DB sau thay đổi

Bằng chứng cắt caller renderer cũ (phải rỗng):

```text
grep -rn "commitStage\|saveDraft\|saveDiagram\|js-cd-update" shell/src/renderer
(empty)
```

Các lệnh ghi còn tới được từ màn Soạn hồ sơ:

| Lệnh | Điểm vào UI / code | Payload, guard |
|---|---|---|
| `notary.workspace_save_case` | Nút **Lưu hồ sơ** duy nhất trên header card Sơ đồ: `relationship-diagram.js:1452` → `case-drafting-view.js:337` (`onSaveCase`) → `runSaveCase:475` → `case-drafting-model.js:905 saveCase`. | Một snapshot `case` (meta) + `stage` (`stageForWire`) + `diagram.state` + `docx_import` khi đổi. **Case mới:** `idempotency_key = state.draftId` (uuid sinh một lần, giữ qua retry) — không còn `workspace_create`. **Case đã có ID:** `case_id + base_revision`. Đây là đường ghi dữ liệu soạn thảo **duy nhất**. |
| `notary.workspace_update` | Ô **Nơi niêm yết** trong dialog xuất Word: `word-export-dialog.js:354` → `case-drafting-model.js:802 saveCaseMeta`. | Chỉ case đã có ID; `{case_id, base_revision, case:{noi_niem_yet}}`. Draft chưa có ID chỉ sửa local, ghi ở lần Lưu hồ sơ. Đây là meta riêng của luồng xuất, không ghi Stage/Diagram. |
| `notary.workspace_convert_type` | Nút **Đổi loại** (`case-drafting-view.js:599`) → `openConversionDialog:495` → `case-drafting-model.js:867 convertCaseType`. | `{case_id, base_revision, case_type, document_type, confirm_diagram_reset, owner_row_id?}`. Guard chặn khi Stage/meta dirty, busy, conflict/stale, không ghi được hoặc chưa có case. |
| `notary.workspace_duplicate` | Từ danh sách hồ sơ (ngoài màn soạn): `case-drafting-view.js:838 duplicateCaseFlow` → `case-drafting-model.js:966 duplicateCase`. | `{source_case_id, idempotency_key}`; key sinh một lần cho ý định, giữ qua lỗi hạ tầng. |

Ngoại lệ có chủ đích đã chốt trong decision: `workspace_update` của Nơi niêm yết, đổi loại, nhân bản là thao tác nghiệp vụ riêng — không dùng làm autosave Stage/Diagram. Không có lệnh ghi nào khác từ màn soạn.

`notary.diagram_evaluate` là read-only: `case-drafting-model.js:1548` gửi `{case:{case_type}, stage, diagram:{state}}`, **không** `case_id`/`base_revision`, không ghi DB.

## §3. Nơi còn dùng `workspace_commit_stage`

Không xóa API server vì renderer Soạn hồ sơ đã bỏ nút; consumer khác còn dùng:

| Nơi | Neo | Lý do giữ |
|---|---|---|
| Registry sidecar | `shell/sidecar/command_registry.py:258–259` | Command vẫn được đăng ký cho consumer ngoài renderer. |
| Adapter thật | `shell/sidecar/notary_adapter.py:839–865` | Chuyển commit Stage tới service; backend contract riêng. |
| Mock adapter | `shell/sidecar/notary_mock_adapter.py:2120–2164` | Phục vụ consumer/test dùng command này. |
| REST routers | `notary_v2/routers/cases.py:563–581` (`_commit_case_form`), `:645–667` (`POST /{cid}/stage-update`) | Form/REST khác vẫn ghi Stage qua commit. |
| Test Python | `shell/test/test_notary_adapter_contract.py:303–309, 463–616`, `shell/test/test_notary_mock_adapter.py`, `shell/test/test_sidecar_contract.py` | Bảo vệ API backend, không phải caller renderer. |
| Fixture/test renderer | `shell/test/fixtures/notary-case-drafting/conflict.json:42`, các assertion phủ định trong `notary-case-drafting-view.test.mjs` | Chỉ còn để chứng minh màn soạn **không** gọi lệnh này; không phải production caller. |

## §4. Copy/wording

Theo chỉ đạo triết lý không-chặn, trạng thái copy được đưa về **tối thiểu hiện có** ở commit `be5ebf8` (sau `eaaeaff` đã thêm câu dài hơn):

- `renderer.js` `canLeave`: trả lại "Stage/Sơ đồ còn bản nháp chưa lưu — rời màn hình sẽ giữ nháp trong phiên nhưng không ghi vào hồ sơ."
- `main.js` close guard: trả lại message "Stage/Sơ đồ còn bản nháp chưa lưu." và detail "Thoát sẽ dừng engine (job chuyển canceled) và mất bản nháp chưa lưu trong phiên."
- `case-drafting-view.js` new/duplicate/open: trả lại câu "Bản nháp hiện tại còn thay đổi chưa lưu — … sẽ mất bản nháp này." / "Stage/Sơ đồ còn bản nháp chưa lưu — mở hồ sơ khác sẽ mất bản nháp hiện tại."
- `word-export-dialog.js`: "Đã gỡ nguồn Word; dữ liệu Stage vẫn được giữ", nút "Áp dụng vị trí đã chọn", notify "Đã áp dụng vị trí vào hồ sơ đang sửa."
- Xóa tooltip dài ở nút xóa dòng, còn "Xóa dòng (hiệu lực khi Lưu hồ sơ)".

> **Các wording hướng dẫn quanh canLeave/rời hồ sơ: CHỜ kết quả thống kê chốt chặn + owner duyệt — giữ tối thiểu hiện có, không mở rộng ở lát này.**

Ngoại lệ bớt thông báo sai của phần 1: với case **đã có ID**, `saveCase` không dùng câu "Hồ sơ đã tồn tại (đã mở lại)"; câu này chỉ còn ở nhánh tạo mới khi server trả `created:false` (retry cùng `draftId`) — `case-drafting-model.js:956–958`.

## §5. Mâu thuẫn triết lý không-chặn (chỉ ghi nhận, không tự gỡ)

Tự rà trong các file G4 đã chạm (`case-drafting-model.js`, `case-drafting-view.js`, `relationship-diagram.js`, `word-export-dialog.js`, `renderer.js`, `main.js`). Các mục dưới vẫn **chặn** thao tác người dùng; không mục nào bị gỡ trong lát này.

1. **Guard đổi loại khi dirty.**
   - `case-drafting-model.js:867–874 convertCaseType`: `"Hãy Lưu hồ sơ và xử lý xung đột trước khi đổi loại."`
   - `case-drafting-view.js:507–512 openConversionDialog`: `"Stage hoặc thông tin hồ sơ có thay đổi chưa lưu. Hãy đóng dialog và bấm Lưu hồ sơ trước khi đổi loại."` — chỉ còn nút Đóng.
   - Đánh giá: chặn thật, nhưng design §6 giữ có chủ đích vì đổi loại reset Diagram; chưa có quyết định thay bằng autosave.

2. **Guard chưa lưu khi gắn vị trí Word / xuất original.**
   - `word-export-dialog.js:436`: `"Hãy Lưu hồ sơ trước khi gắn vị trí."`
   - `case-drafting-model.js:2014–2016 exportWord`: `"Hãy Lưu hồ sơ trước khi xuất."`
   - `word-export-dialog.js:154–156 refreshScanLock`: khóa nút Xuất khi `mappingDirty` hoặc `!model.canWrite()`.
   - `word-export-dialog.js:236`: `"Hãy áp dụng vị trí đã chọn trước khi xuất"`
   - `word-export-dialog.js:237–240`: `"Nơi niêm yết đã thay đổi. Hãy bấm “Lưu nơi niêm yết” trước khi xuất."`
   - Đánh giá: các chặn này bảo vệ tính nhất quán vì options/xuất đọc DB; design §4 giữ. Không phải autosave, nhưng là chặn luồng.

3. **Hộp xác nhận khi thay buffer (mở hồ sơ khác/tạo mới/nhân bản) và rời/đóng.**
   - `case-drafting-view.js:811–819 newDraftFlow`: title `"Thay đổi chưa lưu"`, body `"Bản nháp hiện tại còn thay đổi chưa lưu — tạo hồ sơ mới sẽ mất bản nháp này."`, nút `"Bỏ nháp, tạo mới"` / `"Ở lại"`.
   - `case-drafting-view.js:838–847 duplicateCaseFlow`: `"Bản nháp hiện tại còn thay đổi chưa lưu — nhân bản hồ sơ khác sẽ mất bản nháp này."`, nút `"Bỏ nháp, nhân bản"` / `"Ở lại"`.
   - `case-drafting-view.js:2114–2124 openCaseInDrafting`: `"Stage/Sơ đồ còn bản nháp chưa lưu — mở hồ sơ khác sẽ mất bản nháp hiện tại."`, nút `"Bỏ nháp và mở"` / `"Ở lại"`.
   - `renderer.js:625–633 canLeave`: `"Stage/Sơ đồ còn bản nháp chưa lưu — rời màn hình sẽ giữ nháp trong phiên nhưng không ghi vào hồ sơ."`, nút `"Rời màn hình"` / `"Ở lại"`.
   - `main.js:208–231` close guard: message `"Stage/Sơ đồ còn bản nháp chưa lưu."`, detail `"Thoát sẽ dừng engine (job chuyển canceled) và mất bản nháp chưa lưu trong phiên."`, nút `"Hủy"` / `"Vẫn thoát"`.
   - Đánh giá: modal chặn điều hướng/đóng; design §5 giữ vì buffer chưa ghi sẽ mất thật. Chữ đã tối giản theo `be5ebf8`, không mở rộng.

4. **Khóa lưu đồng thời.**
   - `case-drafting-model.js:906–909 saveCase`: trả `"Đang lưu hồ sơ"` khi `savingCase`; `canWrite:1020–1027` false khi `savingCase`/`duplicating`/đang convert.
   - `relationship-diagram.js` `syncSaveButton`: disable khi lệnh GHI đang chạy (`model.isWriteBusy()`), thiếu capability Diagram hoặc `!canWrite()`; không khoá vì lệnh đọc `diagram_evaluate` (§7.1).
   - `case-drafting-view.js:475–479 runSaveCase`: early-return khi `savingCase`/`!canWrite()`.
   - Đánh giá: chặn tạm thời để bảo đảm một snapshot; không chặn nhập liệu lâu dài.

5. **Chặn lưu khi ngày sai.**
   - `case-drafting-view.js:483–486 runSaveCase`: `"Ngày không hợp lệ — sửa ô được đánh dấu trước khi lưu hồ sơ."`
   - Đánh giá: validation trước IPC, không để dữ liệu sai xuống DB; chặn có điều kiện.

6. **Case khóa/loại chưa hỗ trợ.**
   - `case-drafting-model.js:911–916 saveCase` (và `saveCaseMeta`, `canWrite`): `"Hồ sơ đã khóa — chỉ đọc"` / `"Loại việc chưa hỗ trợ"`.
   - Đánh giá: read-only theo nghiệp vụ, không phải chặn do dirty; evaluate vẫn chạy read-only trên buffer.

7. **`stageGate` / pill bắt Cập nhật — ĐÃ GỠ (đã xử lý).**
   - Bằng chứng: `grep -rn "stageGate\|Cập nhật Stage trước\|js-cd-update" shell/src/renderer` rỗng; `evaluateDiagram` dùng payload draft cho mọi case (`case-drafting-model.js:1548–1563`).

8. **Không tìm thấy mục chặn nào khác** trong các file G4 đã chạm ngoài các nhóm trên. `stageGate` và pill Cập nhật không còn tồn tại; các chuỗi "cập nhật" còn lại thuộc upload/phiên bản engine/audit, không thuộc luồng soạn.

Ghi nhận thêm (không phải chặn, nhưng là nợ comment trong file G4 đã chạm): `case-drafting-model.js:752–754` còn câu "ghi qua workspace_create.payload.case … ghi cung commit Stage"; `case-drafting-view.js:666–670` còn "Meta nháp mới đi lên workspace_create". Đây là comment mô tả đường ghi cũ, không ảnh hưởng hành vi; chưa sửa vì lượt này không sửa code.

## §6. Kết quả test tự động

Chi tiết và danh sách tên fail: [`g4-test-compare.txt`](g4-test-compare.txt). Baseline tên-từng-tên lấy từ worktree tạm `198f66f`; lưu ý môi trường shell có proxy `NO_PROXY` chứa `[::1]` làm httpx lỗi, nên các số "canonical" chạy với biến proxy đã unset.

| Bộ test | Baseline `198f66f` | Sau G4 (`ea719a9`) | Kết luận |
|---|---|---|---|
| Node full `node --test test/*.test.mjs` | 429 test — 381 pass / 48 fail / 0 skip | 428 test — 404 pass / 24 fail / 0 skip | **0 fail mới**; 24 fail còn lại đều có ở baseline (5 thiếu `locked.json`, 17 address-lookup/fileToken, 2 DOCX thiếu module python hệ thống). Chênh 1 test do bỏ test API `commitStage` cũ. |
| `notary-case-drafting-model.test.mjs` | 125 / 120 pass / 5 fail | 124 / 119 / 5 | 5 fail fixture `locked.json` như cũ. |
| `notary-case-drafting-view.test.mjs` | 85 / 85 / 0 | 85 / 85 / 0 | 0 fail. |
| `notary-diagram.test.mjs` | 25 / 20 / 5 | 25 / 25 / 0 | 5 fail cũ đã pass sau cutover, 0 fail mới. |
| `notary-diagram-errors.test.mjs` | 13 / 13 / 0 | 13 / 13 / 0 | 0 fail. |
| `notary-docx-intake.test.mjs` | 27 / 8 / 19 | 27 / 25 / 2 | 2 fail do python hệ thống thiếu `httpx`/`referencing` (có ở baseline). |
| `notary-wire-payload-schema.test.mjs` | 4 / 2 / 2 | 4 / 4 / 0 | 0 fail mới. |
| pytest `notary_v2/tests` (canonical, proxy unset) | 52 fail / 1206 pass / 7 skip (chạy lại đúng 5 file chứa fail: 52/220/6) | 52 fail / 1206 pass / 7 skip | Tập tên fail trùng khít (51 ID): **0 fail mới**. Không tái lập số vòng 1 (1137/118/10) do môi trường/phụ thuộc; `notary_v2` không đổi source từ `1bd248d`. |
| pytest `notary_v2` (có proxy shell) | 76 / 1182 / 7 | 76 / 1182 / 7 | Trùng khít tên; 24 fail thêm là `httpx.InvalidURL` do `NO_PROXY [::1]`. |
| pytest shell 4 file (canonical, proxy unset) | 5 fail / 267 pass / 28 skip / 22 subtests | 5 fail / 267 pass / 28 skip / 22 subtests | **0 fail mới**; 3 fail engine + 2 sidecar `KeyError: 'job_id'` (Windows-only path) đều có ở baseline. |
| pytest shell 4 file (có proxy shell) | 3 fail / 242 pass / 28 skip / 26 errors | 3 fail / 243 pass / 28 skip / 26 errors | 26 error `httpx.InvalidURL` có ở baseline; 0 fail mới. |

Phân loại fail còn lại: **toàn bộ là nợ cũ** (fixture locked, address lookup/fileToken, Windows-path trên Linux, thiếu module python hệ thống, proxy env) — **không có fail mới do G4**.

## §7. E2E trên app thật (điều phối viên bổ sung)

Phương pháp: app Electron thật + sidecar Python thật, DB/profile cô lập (`/tmp/e2e-g4-data`, `/tmp/e2e-g4-profile`, CDP 9222; instance stress riêng CDP 9223), điều khiển qua CDP (chuột thật cho chip, DragEvent cho kéo/thả), KHÔNG shim. Kiểm chứng chéo bằng job log (`window.desktop.v1.listJobs()`) và đọc trực tiếp SQLite. Ảnh: thư mục `e2e-fix-shots/` (cùng thư mục biên bản này). Harness: `e2e-harness/` (`e2e-scenario-a.mjs`, `e2e-scenario-b2.mjs`, `e2e-scenario-g6.mjs`, `e2e-stress.mjs`).

**Kịch bản A (nguyên văn ca owner) — ĐẠT toàn bộ theo tiêu chí vòng 2:**
- Mọi bước: `commitBtn: null` — không còn nút Cập nhật/Lưu nháp trên UI.
- A3 Lưu khi chưa thả owner: chặn đúng `workspace_owner_required`; A4 thả owner vào node → banner biến mất ngay; A5 thiếu tài sản: hộp cảnh báo nổi bật "Hồ sơ chưa có tài sản nào — thêm ít nhất một tài sản rồi lưu lại."; A6 thêm tài sản → Lưu thành công ngay lần đầu → HS-1 "Đã lưu".
- A7 sửa chết→sống: nhãn node owner đổi trong phiên ("1950 – …") TRƯỚC khi lưu; Lưu thành công.
- A8 bấm "Cập nhật": NOBTN (nút đã gỡ). A9 ba vòng gỡ/thả owner + Lưu: ổn định, không treo banner.

**Kịch bản B (viết lại theo luồng mới) — ĐẠT:**
- B2-1 đổi tên chỉ bằng sự kiện `input` (chưa blur): nhãn node owner đổi ngay sang tên mới, ô nhập giữ focus/caret — Pool/Sơ đồ đọc bản đang sửa.
- Đặt ngày chết + "Xem cách tính": engine sinh các node father/mother/spouse/child_owner ngay trong phiên.
- Thêm người mới: Pool hiện ngay (chưa cần thao tác lưu trung gian); kéo/thả thẳng vào node thường (`father`) thành công; Lưu một lần thành công, người mới được ghi kèm gán node.
- Nhiều vòng chết→sống→chết, mỗi vòng Lưu một lần: đều thành công; gán node của người thứ hai được giữ nguyên qua các vòng.
- Audit job toàn phiên: chỉ `workspace_save_case` + lệnh đọc + `diagram_evaluate`; **0** `workspace_commit_stage` / `workspace_create` / `diagram_save`.

**Kịch bản C (Chủ đất):** giữ nguyên kết quả vòng 1 (biên bản `fix-loop-round1-20261023.md`); vòng 2 không đổi hành vi `ownPositions`/`syncPositionDefaults`, chỉ đổi nguồn đọc sang bản đang sửa — các test model tương ứng vẫn pass (124 test, §6).

**G6 (sơ đồ dirty + Stage sửa rồi Lưu một lần) — ĐẠT:**
- Trong phiên: đổi tên owner (input-only), thêm người C, thả C vào node `mother` → sơ đồ dirty (nút Lưu hồ sơ có chấm + aria "có thay đổi chưa lưu").
- "Xem cách tính" trên bản đang sửa: `diagram_evaluate` thành công, payload draft (không `case_id`), không phát sinh lệnh ghi.
- Bấm Lưu đúng một lần: đúng 1 job `workspace_save_case` succeeded, 0 lệnh ghi cấm.
- Đối chiếu DB sau lưu (SQLite): 3 dòng người khớp từng trường với trạng thái đã thấy trong phiên (owner tên mới + ngày chết 2023-07-07; B ở `father`; C ở `mother`), trạng thái `done`, `workspace_revision` tăng đúng.

**Biến thể stress (agent con, instance riêng) — kết quả gốc: S1/S3/S4 ĐẠT, S2 THẤT BẠI (đã sửa, xem §7.1 và §7.2):**
- S1 bấm Lưu 10 lần liên tiếp không sửa xen giữa: 10/10 succeeded, đúng 10 job `workspace_save_case`, 0 lệnh cấm, revision tăng đều 1→11, không banner treo.
- S2 thả/gỡ node owner 5 vòng rồi Lưu: **THẤT BẠI ở cả 2 lượt chạy** (kết quả giống hệt nhau): sau khi bấm Lưu, banner `workspace_owner_required` hiện dù node owner vẫn hiển thị người và Pool rỗng; đối chiếu revision DB của phiên stress (13 thay vì 14) xác nhận lần Lưu S2 không ghi được. Điều phối viên tái hiện sạch độc lập (DB mới, `e2e-s2-clean.mjs`) và chẩn đoán ra 2 lỗi D1/D2 — đã sửa ở commit `1d1ec3f`, chi tiết §7.1; kiểm chứng sau sửa ở §7.2.
- S3 thay TOÀN BỘ thông tin một người (tên, số giấy tờ, ngày sinh, ngày cấp, địa chỉ, ngày chết) → Lưu → mở lại: đọc lại khớp cả 6 trường (MATCH). Đối chiếu DB: mọi trường đã xuống DB, revision/status đúng.
- S4: 2 người + 2 tài sản (2 dòng đất) → Lưu thành công, sơ đồ đúng; mở được hộp thoại xuất Word và danh sách mẫu. DỪNG TRUNG THỰC tại bước chọn mẫu/hộp chọn file native của HĐH (tự động hoá không qua được) — chưa thực thi xuất Word; ghi nhận là giới hạn môi trường tự động hoá, không phải lỗi app. Toàn phiên S4: 0 lệnh ghi cấm.

**Sự cố khi kiểm chứng (minh bạch, không phải lỗi app):**
- Hai lần script E2E lấy nhầm dòng người vì truy vấn DOM quá sớm trong lúc máy đang tải nặng bởi các bộ test chạy song song (render chậm vài giây). Điều phối viên hoàn tất các bước còn lại tương tác trực tiếp với cùng tiêu chí; harness đã sửa sang cơ chế poll chờ dòng mới (40 × 500ms) để chạy lại được về sau.
- Một lần thao tác tay của điều phối viên bấm nhầm nút xóa dòng của người thứ nhất trong BẢN ĐANG SỬA (chưa lưu) — kiểm chứng SQLite xác nhận DB không hề bị ảnh hưởng (chỉ "Lưu hồ sơ" mới ghi), mở lạnh lại app cho trạng thái đúng từ DB. Sự cố này vô tình chứng minh thêm tiêu chí "chưa Lưu thì DB không đổi".

**Phát hiện phụ F1 (nhỏ, ghi nhận — chưa sửa ở lát này):** khi một ô Stage đang giữ focus, cơ chế làm mới hẹp (chỉ khung quan hệ) không vẽ lại trang trí lỗi của bảng Stage, nên ô vừa sửa đúng vẫn còn vệt đỏ cho tới lần phát tín hiệu thay đổi tiếp theo sau khi rời ô (hoặc lần Lưu). Trạng thái model đã dọn lỗi ngay khi sửa (hàm `clearRowFieldError`), lần Lưu vẫn thành công và giao diện sạch sau lưu. Đề xuất lát nhỏ sau: vẽ lại trang trí lỗi trong đường làm mới hẹp.

### §7.1. Vòng sửa S2 — evaluate debounce nuốt click Lưu + banner owner_required treo

Tái hiện sạch trên app thật (DB mới, 1 hồ sơ): sau 5 vòng thả/gỡ node owner (~700ms/vòng) rồi bấm **Lưu hồ sơ**, nút đang disabled → click mất trắng, không có job `workspace_save_case`, revision DB không đổi; banner `workspace_owner_required` cũ treo lại dù evaluate mới nhất succeeded. Harness: `e2e-harness/e2e-s2-clean.mjs` (§7).

**Chẩn đoán (đã xác nhận trong code trước khi sửa):**

- **D1 — nút Lưu khoá vì lệnh ĐỌC.** `relationship-diagram.js` `syncSaveButton` và `case-drafting-view.js` `syncChromeUI` đều đặt `disabled = !!s.busy || …`. `evaluateDiagram()` đặt `state.busy='notary.diagram_evaluate'` suốt round-trip (chỉ đọc) và `scheduleEvaluate` debounce ~500ms sau mỗi lần kéo/thả; click Lưu trong cửa sổ busy bị nuốt không phản hồi. Nút Lưu chỉ được khoá vì lệnh GHI (`workspace_save_case`/`savingCase`, `workspace_convert_type`, `workspace_duplicate`, `workspace_update`) hoặc không ghi được.
- **D2 — response evaluate cũ ghi đè trạng thái mới.** `evaluateDiagram()` chỉ guard theo `session`, không theo phiên bản sơ đồ: response gửi lúc sơ đồ chưa có owner về sau khi người dùng đã gán owner (và `setOwnerRow` đã dọn banner) vẫn đặt lại `state.error`/`state.diagramErrors` từ payload cũ. Response evaluate thành công đến sau đó không dọn `state.error` do evaluate đặt.

**Sửa (commit `1d1ec3f`):**

- `case-drafting-model.js`: thêm `isWriteBusy()` — nguồn duy nhất cho việc khoá nút Lưu theo lệnh GHI (`savingCase`, `duplicating`, `busy` thuộc tập `workspace_save_case/update/convert_type/duplicate`), export cho view/diagram dùng; cả hai điểm disable bỏ `!!s.busy`.
- `evaluateDiagram()`: mỗi lần gọi có `evaluateSeq` + `diagramMutation` (đếm mutation: `touchDiagram`, gán/gỡ owner, xoá dòng có tham chiếu node, thay wholesale khi mở/lưu/đổi loại/nháp mới). Response không phải lần mới nhất hoặc sơ đồ đã đổi từ lúc gửi → chỉ dọn `busy` nếu là của chính nó, không đụng `error`/`diagramErrors`/`renderModel`/`diagramWarnings`. Kết quả còn hiệu lực tự dọn `state.error` **chỉ khi** đó là error object do evaluate đặt (đánh dấu bằng tham chiếu nội bộ); lỗi đường ghi (`applyStageWriteError`/`saveCase`/duplicate) giữ nguyên. Hành vi `diagram_invalid_state` (đặt `diagramErrors`) giữ như cũ cho response còn hiệu lực.

**Test mới (`node --test`):**

| Test | File | Kiểm |
|---|---|---|
| `evaluateDiagram: response cu ve sau khi gan owner bi bo — khong dat lai error/renderModel` (T1) | `notary-case-drafting-model.test.mjs` | A gửi lúc chưa owner → gán owner → B gửi → B success trước → A fail `workspace_owner_required` sau: `state.error` vẫn null, `renderModel` của B giữ nguyên. |
| `evaluateDiagram: evaluate moi thanh cong don loi do evaluate dat truoc` (T2) | nt | Evaluate còn hiệu lực fail → sơ đồ sửa qua `touchDiagram` → evaluate mới success → `state.error` được dọn. |
| `evaluateDiagram: evaluate thanh cong KHONG don loi cua duong ghi` (T2b) | nt | Lỗi từ lệnh ghi (`workspace_duplicate` fail) không bị evaluate thành công dọn. |
| `Lưu hồ sơ: khóa khi lệnh GHI chạy, KHÔNG khóa vì diagram_evaluate` (T3) | `notary-case-drafting-view.test.mjs` | `busy=diagram_evaluate` → nút bật; `savingCase`/`busy=workspace_save_case`/`busy=workspace_update` → nút khoá. |

Đối chứng trước khi sửa: chạy đúng 2 file test trên worktree tạm tại HEAD `7f099b6` (source cũ) — T1, T2, T3 fail; T2b pass (là guard chống dọn quá tay, không phải test tái hiện lỗi). Sau sửa: cả 4 pass.

**Số liệu suite sau sửa (`node --test test/*.test.mjs`):**

| Thời điểm | tests | pass | fail | Ghi chú |
|---|---|---|---|---|
| Trước (HEAD `7f099b6`) | 428 | 404 | 24 | §6 |
| Sau (`1d1ec3f`) | 432 | 408 | 24 | +4 test mới (3 model, 1 view) |

24 tên fail trùng đúng danh sách nợ cũ ở §6/`g4-test-compare.txt` (5 thiếu `locked.json`, 17 address lookup/fileToken, 2 DOCX thiếu module python hệ thống): **0 fail mới**. Target 4 file model/view/diagram/diagram-errors: 251 test, 246 pass, 5 fail — đúng 5 nợ fixture `locked.json`.

**E2E sau sửa: xem §7.2 (điều phối viên bổ sung).**

### §7.2. Kiểm chứng E2E sau sửa S2 (điều phối viên)

Chạy trên bản đã sửa (HEAD `80867ff`), app Electron thật + sidecar thật, DB/profile mới:

- **Tái hiện sạch `e2e-s2-clean.mjs` (đúng kịch bản từng fail):** trước khi bấm Lưu — `saveDisabled: false`, `banners: []` (không còn banner treo, nút không bị khóa vì lệnh đọc); delta jobs gồm `workspace_save_case succeeded`; **revision DB 1 → 2** — lần Lưu ghi thật. So với trước sửa: `saveDisabled: true` tại thời điểm bấm, 0 job save_case, revision đứng nguyên.
- **Script stress nguyên bản `e2e-stress.mjs` (instance riêng CDP 9223, DB mới):** S1 10/10 succeeded; S2 state sau Lưu `banners: []`, Lưu thành công; S3 MATCH cả 6 trường; S4 đạt, 0 lệnh ghi cấm. **Revision cuối phiên = 14** (setup 1 + S1 10 + S2 1 + S3 1 + S4 1) — mọi lần Lưu đều xuống DB, đúng phần trước sửa bị thiếu (13).
- **Hồi quy kịch bản A nguyên văn (instance + DB mới):** đạt toàn bộ như §7 (chặn đúng khi chưa thả owner, Lưu thành công sau khi thêm tài sản, nhãn node đổi trong phiên khi sửa chết→sống, "Cập nhật" = NOBTN).

## §8. Commit list toàn lát G4

| Commit | Nội dung |
|---|---|
| `59b8778` | Decision owner single-save |
| `080ab2d` | Đồng bộ contract/spec theo một lần lưu |
| `198f66f` | Thiết kế G4 + chỉnh contract |
| `3fb885c` | Model: một nguồn Stage, persist chỉ bằng saveCase |
| `05d069c` | View: bỏ nút commit trên, refresh quan hệ live |
| `eaaeaff` | Word: detach/bind local, copy rời màn hình |
| `5e2076b` | Docs: bỏ link recon ngoài repo |
| `be5ebf8` | Copy tối thiểu, không thêm chặn |
| `6729949` | Test view theo một Lưu hồ sơ |
| `97e62c7` | Test diagram/DOCX/wire theo save_case |
| `ea719a9` | Dọn comment commit_stage còn sót |
| `1d1ec3f` | Sửa S2: Lưu không khoá vì lệnh đọc, bỏ response evaluate cũ (§7.1) |
| (commit biên bản này) | Biên bản vòng 2 G4 + `g4-test-compare.txt` |
| (commit bổ sung của điều phối viên) | Điền §7 E2E trên app thật vào biên bản |
| `80867ff` | Ghi vòng sửa S2 (D1/D2, test, số liệu suite) vào biên bản |
| (commit đính chính của điều phối viên) | Đính chính kết quả stress S2 trong §7 + bổ sung §7.2 kiểm chứng sau sửa |
