# SPEC — Product Flow và Electron UX tab Soạn hồ sơ (MIN-104)

> **Trạng thái: APPROVED — owner duyệt 24/09/2026. Spec này là cổng duyệt đã
> qua trước [MIN-105](https://linear.app/minhnotary/issue/MIN-105) (CONTRACT).
> Không code, không contract, không Figma trong task MIN-104.**
>
> Phạm vi: quyết định **cấp sản phẩm/UX** cho tab `Soạn hồ sơ` của module
> `notary_v2` trong shell Electron một máy — taxonomy module/tab, luồng sản
> phẩm, bố cục, bảng nút và màn hình con, danh mục trạng thái UI, nguyên tắc
> privacy/mock, ngữ nghĩa UX xuất Word nhiều văn bản.
>
> Ranh giới SOT: quyết định **hành vi/dữ liệu** của tab (semantics
> Stage/Pool/Diagram, `base_revision`/conflict, suggestion, `case_type`,
> map hành vi → command) thuộc
> [drafting-tab.md](../../../notary_v2/docs/platform/case-workspace/drafting-tab.md)
> — file này link sang, không chép lại. Wire contract `desktopcommand.v1` cho
> các command đích publish trong MIN-105 (`contracts/notary-case-drafting.md`,
> chưa tồn tại); task này không viết contract.
>
> Nguồn: §1 + Global Constraints của [implementation plan](../plans/2026-09-24-notary-v2-case-drafting-tab-implementation-plan.md)
> (quyết định owner 23–24/09/2026). Hiện trạng đối chiếu theo ba audit
> read-only ngày 24/09/2026 (`.agent/scratch/min-104-audit-*.md`); mọi claim
> hiện trạng kèm file:line.

## 1. Taxonomy module — đã khóa

Ba **module nghiệp vụ chính** trên UI: `notary_v2`, `upload_lab`,
`notaryoffice`. Bên trong `notary_v2` có ba **tab con**: `Tổng quan hồ sơ`,
`Soạn hồ sơ`, `Word`. Excel import là một nguồn nhập **bên trong** tab
`Soạn hồ sơ`, không phải module/tab chính. `Tra cứu` và `Trạng thái/Cài đặt`
là **tiện ích shell**, không phải module nghiệp vụ.

| Thành phần UI | Loại | Ghi chú |
|---|---|---|
| `notary_v2` | Module nghiệp vụ | Chứa ba tab con bên dưới |
| `upload_lab` | Module nghiệp vụ | Số hóa + upload (spec riêng) |
| `notaryoffice` | Module nghiệp vụ | Placeholder — chưa có code |
| `Tổng quan hồ sơ` | Tab con của `notary_v2` | Danh sách/mở hồ sơ; entry point của `Soạn hồ sơ` |
| `Soạn hồ sơ` | Tab con của `notary_v2` | **Phạm vi của spec này** |
| `Word` | Tab con của `notary_v2` | Surface văn bản của module; nội dung chi tiết tab này **không** nằm trong spec này — điểm vào xuất Word nằm trong `Soạn hồ sơ` (§7) |
| Excel import | Nguồn nhập trong `Soạn hồ sơ` | Không là module/tab chính |
| `Tra cứu` | Tiện ích shell | Không phải module nghiệp vụ |
| `Trạng thái/Cài đặt` | Tiện ích shell | Trạng thái engine, diagnostics đã redact |

- `Excel → Word` **không còn** là mục nav chính. Hiện trạng renderer có nav 7
  mục (`shell/src/renderer/lib.js:8-19`: Tổng quan, Upload/Audit, Hồ sơ,
  Excel/Word, Văn phòng, Tìm kiếm, Trạng thái/Cài đặt) — đích gom theo
  taxonomy trên; ID kỹ thuật `document-review` giữ tương thích một chu kỳ
  (plan, Task 8).
- `excelTK` là dự án riêng, ngoài phạm vi hệ thống (AGENTS.md).
- Module Zalo là phần mềm riêng — chỉ xuất hiện trong câu loại trừ ở §8.

## 2. Luồng sản phẩm đã khóa (đích Electron)

```text
Mở hồ sơ từ Tổng quan
  → tải Workspace
  → nhập file / dán text / nhập Excel / thêm tay
  → kiểm tra các gợi ý Người và Tài sản
  → đưa gợi ý đã chọn vào Stage (vẫn là draft UI)
  → bấm Cập nhật Stage
  → backend kiểm tra và commit toàn bộ Stage
  → Pool tự tính lại
  → kéo thả hoặc chọn menu để gán quan hệ trên sơ đồ
  → backend đánh giá, báo thiếu/sai, trả kết quả tính
  → bấm Lưu sơ đồ
  → bấm Xuất Word
  → chọn nhiều văn bản + một folder đích
  → tạo từng DOCX độc lập
  → hiển thị Đã lưu/Lỗi cho từng văn bản
```

- Điểm vào là **hồ sơ có sẵn** mở từ `Tổng quan hồ sơ`. V1 Electron không có
  đường "hồ sơ mới qua hidden state" như web hiện hành
  (`notary_v2/docs/domains/inheritance/workflow.md` L105); tạo hồ sơ là luồng
  riêng, ngoài spec này.
- Mọi kết quả nhập từ file/text/Excel/OCR là **gợi ý chờ người kiểm tra**;
  đưa vào Stage và bấm `Cập nhật` mới là xác nhận. Không có bước nào tự ghi
  vào hồ sơ (semantics suggestion → `drafting-tab.md` §5).
- Pool và sơ đồ nằm cùng một màn hình dưới Stage — không có màn hình/bước
  wizard riêng cho quan hệ.

## 3. Bố cục desktop đã khóa (đích)

- **Thanh ngữ cảnh trên cùng:** nút quay lại, mã/tên hồ sơ, loại việc, trạng
  thái lưu. Không có breadcrumb dài, không thẻ thống kê.
- **Tầng Stage** ngay dưới thanh ngữ cảnh:
  - card `Tài sản` bên trái, rộng khoảng **36%**; đầu card có `Nhập dữ liệu`,
    `+ Tài sản`;
  - card `Người` bên phải, rộng khoảng **64%**; đầu card có `Nhập Excel`,
    `OCR giấy tờ`, `+ Người`, `Cập nhật`;
  - chỉ hiện trường quan trọng trên dòng; bấm dòng mở phần chi tiết.
- **Tầng quan hệ** ngay dưới Stage:
  - `Pool` bên trái khoảng **22%** — danh sách thẻ Người/Tài sản chưa được
    gán trên sơ đồ (định nghĩa chuẩn của Pool → `drafting-tab.md` §2);
  - sơ đồ bên phải khoảng **78%**;
  - toolbar gọn: `Lưu sơ đồ`, `Xem cách tính`, `Xuất Word`, menu `⋯`.
- **Breakpoint:** cửa sổ hẹp dưới **1.000 px** → hai card Stage xếp dọc;
  Pool và sơ đồ vẫn giữ cuộn ngang thay vì ép thẻ quá nhỏ.
- **Design tokens:**

  | Token | Giá trị |
  |---|---|
  | Nền | `#f3f4f8` |
  | Card | trắng, viền `#dfe3e9`, radius 16 px |
  | Rail/nav tối | `#121418` |
  | Màu chính (accent) | `#d9f76a` |
  | Cảnh báo | `#ffe4d6` |
  | Control radius | 12 px |
  | Vùng bấm tối thiểu | 44 px |

## 4. Nút và màn hình con — đã khóa

| Vị trí | Nút/thao tác | Màn hình con/kết quả | Dữ liệu được phép đổi |
|---|---|---|---|
| Tài sản | `Nhập dữ liệu` | Popup nhận ảnh/PDF/Word/text | Chỉ tạo gợi ý; chưa đổi Stage |
| Người | `Nhập Excel` | Cùng popup intake, lọc `.xlsx` | Chỉ tạo gợi ý; chưa đổi Stage |
| Người | `OCR giấy tờ` | Chọn ảnh/PDF → review kết quả | Chỉ tạo gợi ý; chưa đổi Stage |
| Stage | `+ Người`, `+ Tài sản` | Drawer/form ngắn | Thêm dòng draft UI |
| Stage | `✕` trên dòng | Không mở popup | Xóa dòng draft; chỉ có hiệu lực sau `Cập nhật` |
| Stage | `Cập nhật` | Lỗi nằm ngay đúng dòng; thành công cập nhật Pool | Commit Stage theo một transaction |
| Pool | Kéo thả thẻ | Gợi ý slot trên Diagram | Chỉ đổi draft Diagram |
| Pool | Menu `Gán vị trí` | Popup chọn vai trò/quan hệ | Cách thay thế kéo thả, cùng kết quả |
| Diagram | `Chủ đất`, `Nhận` | Trạng thái ngay trên card | Chỉ đổi draft Diagram cho tài sản hiện tại |
| Diagram | `Lưu sơ đồ` | Banner thành công/lỗi | Commit Diagram, không đổi Stage |
| Diagram | `Xem cách tính` | Panel thu gọn trong vùng sơ đồ | Chỉ đọc output engine |
| Toolbar | `Xuất Word` | Popup chọn nhiều văn bản và folder | Chỉ tạo file đầu ra |
| Popup | `×` | Đóng/ẩn | Không tự lưu, không tự xóa kết quả |

## 5. Danh mục trạng thái UI bắt buộc

Tên trạng thái hiển thị dùng đúng vocabulary chung của shell
(`2026-09-14-module-transition-ux-spec.md` §2–3: `idle`, `checking`,
`running`, `waiting_user`, `canceling`, `canceled`, `failed`, `completed`
— `partial` hiển thị trong nhóm `completed` kèm breakdown; `unavailable`
là trạng thái module-level — cùng bốn mặt màn hình Loading/Empty/Error/
Unavailable). Wire status `desktopcommand.v1` map sang display một chiều:
`succeeded` → `completed`; `partial`/`failed`/`canceled` trùng tên. Tab
này không chế tên trạng thái riêng.

| # | Trạng thái | Mặt hiển thị | Hành vi bắt buộc |
|---|---|---|---|
| 1 | Đang tải Workspace | Loading | Skeleton/spinner + label; không giả progress |
| 2 | Hồ sơ không tồn tại | Error | `error.code` + message + nút quay lại Tổng quan |
| 3 | Hồ sơ đã khóa | Read-only | Toàn bộ trường chỉ đọc; vẫn xem/sao chép được; mọi nút ghi bị vô hiệu |
| 4 | Stage rỗng / Pool rỗng / Diagram chưa gán | Empty | Mô tả trống + hành động đầu tiên (`Nhập dữ liệu`, `+ Người`, `+ Tài sản`) |
| 5 | Có draft chưa cập nhật | Dirty indicator | Badge trên `Cập nhật`; rời màn → cảnh báo (§6) |
| 6 | OCR/import thành công một phần | `partial` theo từng nguồn | Nguồn lỗi báo đúng nguồn đó; gợi ý thành công vẫn hiển thị để review |
| 7 | Stage validation lỗi | Error inline | Lỗi nằm ngay đúng dòng/trường; Stage không đổi nếu còn lỗi |
| 8 | `workspace_conflict` (revision cũ) | Conflict dialog | Cho tải bản mới hoặc giữ bản nháp để sao chép; không nút "ghi đè cưỡng bức" |
| 9 | Engine/Qwen không khả dụng | Unavailable | Tên capability + lý do; không cho chạy job tương ứng |
| 10 | Sơ đồ có cảnh báo nghiệp vụ / trường hợp chưa hỗ trợ | Warning + `Chưa hỗ trợ` | Cảnh báo hiển thị riêng, không trình bày như kết quả đã tính |
| 11 | Xuất Word đang chạy | Running + progress | Progress theo văn bản; hủy được (file đã lưu không bị xóa) |
| 12 | Xuất Word xong | completed / `partial` / failed | `Đã lưu`/`Lỗi` theo từng văn bản + breakdown (§7) |

## 6. Nguyên tắc privacy, draft, mock — đã khóa

- **Không PII trong log/diagnostics/localStorage:** không lưu CCCD, dữ liệu
  OCR, raw text hay ảnh giấy tờ vào log, diagnostics hay `localStorage`.
  Diagnostics chỉ hiển thị log đã redact; không stack trace cho người dùng
  cuối (theo `module-transition-ux-spec` §6).
- **Draft và cảnh báo rời màn:** thay đổi chưa commit chỉ là draft của phiên
  (semantics → `drafting-tab.md` §4). Khi rời màn/đổi module/đóng app mà còn
  thay đổi chưa lưu → chặn bằng dialog cảnh báo; refresh nền/poll job không
  ghi đè field đang sửa (convention chung, `module-transition-ux-spec` §4).
- **Conflict UX:** khi `workspace_conflict`, UI cho **tải bản mới** hoặc
  **giữ bản nháp để sao chép**; không có nút "ghi đè cưỡng bức"
  (`base_revision` mechanics → `drafting-tab.md` §3).
- **Không auto-*:** không tự ghi gợi ý vào hồ sơ, không tự tạo quan hệ,
  không tự chọn người nhận, không tự xuất Word. Mọi xác nhận nghiệp vụ là
  hành động của người dùng.
- **Mock:** backend giả chỉ chạy ở chế độ phát triển và phải hiện nhãn
  `Dữ liệu mô phỏng`; bản đóng gói production luôn dùng backend thật hoặc
  báo không khả dụng — không âm thầm fallback sang mock.

## 7. Xuất Word nhiều văn bản — UX đã khóa (đích)

- Điểm vào: `Xuất Word` trong toolbar sơ đồ (§3–§4).
- Popup gồm: danh sách **checkbox nhiều văn bản** (mỗi văn bản một
  `document_key`) + chọn **một folder đích** qua native directory picker của
  Electron main. Directory picker đã có end-to-end
  (`shell/src/main/main.js:32-48`, `shell/src/main/ipc.js:67-71`; đang dùng
  cho `upload.scan` ở `shell/src/renderer/renderer.js:522`). Ý định: folder
  đích là FileRef thư mục (`is_dir=true`); việc pin `is_dir` vào contract
  FileRef thuộc MIN-105 — hiện FileRef contract
  (`contracts/desktop-command.md` §6) chưa có field này.
- Mỗi văn bản đã chọn tạo **một `.docx` riêng** trong folder đã chọn.
- **Không ZIP; không ghi đè** file có sẵn — trùng tên tự thêm `_2`, `_3`, …
- Kết quả **theo từng văn bản**: `Đã lưu` kèm tên file thật, hoặc `Lỗi` kèm
  lý do đúng văn bản đó; file lỗi không làm mất các file đã thành công;
  popup không tự đóng khi còn lỗi.
- Trạng thái hiển thị khi job xong (wire→display theo §5): tất cả thành
  công → `completed` (wire `succeeded`); hỗn hợp → `partial` kèm breakdown
  thành công/thất bại; tất cả lỗi → `failed`. Hủy giữa lượt chỉ dừng các
  file chưa bắt đầu; file đã lưu không bị xóa.
- Điều kiện nghiệp vụ trước khi xuất (Stage có người, Diagram đã lưu, có chủ
  đất/người nhận/tài sản) và quy tắc placeholder giữ SOT ở
  `notary_v2/docs/domains/inheritance/word-export.md` — spec này không định
  nghĩa lại.
- Hai command đích `notary.word_export_options` và
  `notary.word_export_batch` (map hành vi → `drafting-tab.md` §8; wire shape
  → MIN-105). Tên file kết quả (`actual_filename`) do backend quyết, UI chỉ
  hiển thị.
- **Hiện trạng:** một template → một DOCX qua browser download
  (`notary_v2/routers/cases.py:1610-1663`,
  `frontend/templates/cases/form.html:3896-3903`,
  `frontend/templates/cases/detail.html:29-31`). Luồng cũ giữ làm fallback
  web đến cutover — không xóa trong plan này.

## 8. Loại trừ

- **Zalo:** không có nút, popup, command hay trạng thái Zalo trong tab
  `Soạn hồ sơ`. Zalo là phần mềm riêng (module độc lập; spec hành vi tại
  `notary_v2/docs/platform/zalo-document-inbox/`); nguồn dữ liệu trao đổi
  trong tương lai đi qua contract riêng, không làm UI Zalo quay lại tab này.
  Spec này chỉ nhắc Zalo trong ngữ cảnh loại trừ/tham chiếu ranh giới (ở đây
  và pointer ở §1) — không spec hành vi Zalo.
- Không có trong spec/task này: wire contract/schema JSON (MIN-105);
  framework UI mới, thư viện sơ đồ mới, database mới (tech stack hiện hữu
  theo `docs/architecture/TECH_STACK.md`); Figma artifact; xóa
  `frontend/templates/cases/form.html` (fallback đến cutover); LAN/đa máy
  (G1-LAN); dark theme bắt buộc.

## 9. Hiện trạng ↔ đích (tóm tắt cấp sản phẩm)

| Quyết định đích | Hiện trạng web/shell (bằng chứng) | Khoảng cách |
|---|---|---|
| 3 module + 3 tab con; Excel import trong `Soạn hồ sơ` | Nav 7 mục có `Excel/Word` riêng (`shell/src/renderer/lib.js:8-19`); view `document-review` phẳng, chưa có Stage/Pool/Diagram | Taxonomy §1 là chuẩn nav mới |
| Intake thủ công 5 loại `image/pdf/docx/xlsx/text` | Chỉ ảnh (`form.html:2405` `accept="image/*"`; `routers/ocr_ai.py:2641-2644`) + Excel ghi DB ngay (`routers/customers.py:356-358`) + nhập tay; không PDF/DOCX/text | Đa nguồn, mọi nguồn đều là gợi ý qua review |
| Commit Stage atomic + `base_revision` | Snapshot `case_state_json` qua `/stage-update` (`routers/cases.py:800-835`) atomic ở mức JSON nhưng person ghi per-row trước đó (`form.html:11974`); không `base_revision` (`models.py:92-107` không có revision) | Transaction duy nhất + optimistic lock |
| Diagram gán quan hệ, engine Python tính | ReactFlow đã có nhưng `inheritance_engine.js` **thiếu file** (`form.html:8638` → fallback `engine_missing`, share `0.00` — `ReactFlowApp.jsx:743-748`); engine Python `services/inheritance_engine.py` không router nào gọi | Engine Python qua command evaluate/save |
| Word export nhiều văn bản → một folder | 1 template → 1 DOCX browser download (`routers/cases.py:1610-1663`) | `word_export_batch` + per-file result (§7) |
| `workspace_conflict` | Không có — hai tab sửa cùng case là last-write-wins | Conflict dialog §5–§6 |

Bảng hiện trạng ↔ đích chi tiết theo khối hành vi (kèm file:line đầy đủ) nằm
ở `drafting-tab.md` §9.

## 10. Nguồn tham chiếu và nghiệm thu

- Plan: `docs/product/plans/2026-09-24-notary-v2-case-drafting-tab-implementation-plan.md`
  (§1 là nguồn nội dung đã khóa; §2 chỉ để tham chiếu tên command).
- Spec hành vi/dữ liệu tab: `notary_v2/docs/platform/case-workspace/drafting-tab.md`.
- UX chung shell (vocabulary trạng thái, cancel, dirty, diagnostics):
  `docs/product/specs/2026-09-14-module-transition-ux-spec.md`.
- SOT hiện trạng web (fallback): `notary_v2/docs/domains/inheritance/workflow.md`.
- Nghiệp vụ xuất Word (placeholder, điều kiện xuất):
  `notary_v2/docs/domains/inheritance/word-export.md`.
- Envelope đã duyệt: `contracts/desktop-command.md` (`desktopcommand.v1`).
- Wire contract đích: `contracts/notary-case-drafting.md` — MIN-105, chưa tồn tại.

Nghiệm thu (MIN-104):

- [ ] Owner duyệt spec này và `drafting-tab.md` trước khi mở MIN-105.
- [ ] Không còn quyết định UI mở hoặc mâu thuẫn giữa các spec (mỗi quyết định
      một nguồn chuẩn — phân chia SOT ghi ở header).
- [ ] Chỉ thay tài liệu; không sửa runtime, DB, `contracts/`, Figma.
