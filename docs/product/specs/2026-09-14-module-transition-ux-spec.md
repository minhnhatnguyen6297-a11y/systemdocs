# SPEC — UX chuyển module & trạng thái chung cho shell Electron (MIN-32 slice, G1-SM)

> **Trạng thái: DRAFT — chờ owner duyệt (gate D2).**
>
> Phạm vi: UX dùng chung của shell một máy — navigation, trạng thái chuẩn,
> loading/empty/error/unavailable, `waiting_user`, cancel, dữ liệu chưa lưu,
> cửa sổ Chromium headed và focus. Không chọn framework renderer, không widget
> PySide6, không code.
>
> Phân chia SOT (cập nhật 24/09/2026, MIN-104): file này giữ UX **chung của
> shell**. Spec hiện hành cho tab `Soạn hồ sơ` của module `notary_v2` —
> taxonomy module/tab, luồng, bố cục, nút, trạng thái UI, UX xuất Word — là
> [2026-09-24-notary-v2-case-drafting-electron-ux.md](2026-09-24-notary-v2-case-drafting-electron-ux.md);
> hành vi/dữ liệu tab (Stage/Pool/Diagram, revision/conflict, suggestion) là
> SOT của `notary_v2/docs/platform/case-workspace/drafting-tab.md`.

## 1. Navigation và layout

- Nav trái cố định theo taxonomy đích (MIN-104): ba **module nghiệp vụ**
  `notary_v2`, `upload_lab`, `notaryoffice` (placeholder "Chưa triển khai",
  vẫn hiển thị không ẩn) + hai **tiện ích shell** `Tra cứu` và
  `Trạng thái/Cài đặt`. Bên trong `notary_v2` có ba tab con `Tổng quan hồ
  sơ` / `Soạn hồ sơ` / `Word`; Excel import là tính năng nhập **trong** tab
  `Soạn hồ sơ`, không phải module/mục nav chính. Taxonomy đầy đủ → spec
  `2026-09-24-notary-v2-case-drafting-electron-ux.md` §1. ID kỹ thuật cũ
  `document-review`/`excel-word` giữ tương thích một chu kỳ chuyển đổi,
  không còn là nhãn nav.
- Window mặc định 1280×820; vẫn dùng được ở snap tối thiểu 760×520. Light
  theme trước; dark không bắt buộc trong G1-SM.
- **Đổi module không mất state/job** (SM-07): rời module A sang B rồi quay lại
  → A giữ nguyên form đang nhập, job đang chạy, vị trí scroll. State giữ ở
  renderer hoặc job phía sidecar; không reload mất nhập liệu.

## 2. Trạng thái chuẩn (display vocabulary MIN-32)

```text
idle → checking → running → waiting_user → running → completed
              │         │          │
              │         │          └─→ canceling → canceled
              │         └─→ canceling → canceled
              └─→ failed            (bất kỳ đâu: engine_restarted → failed)
```

- `waiting_user` là trạng thái chờ người (đăng nhập portal, review OCR,
  Finalize) — **không phải lỗi**, hiển thị banner + CTA rõ hành động cần làm.
- `partial` hiển thị trong `completed`-nhóm với breakdown thành công/thất bại.
- `unavailable` (module-level, khác job): engine/stack không có (vd local OCR
  parked) → trạng thái riêng "Không khả dụng" + lý do, không cho chạy job.

## 3. Bốn mặt trạng thái màn hình

| Mặt | Khi nào | Nội dung tối thiểu |
|---|---|---|
| Loading | lần đầu fetch/đang checking | skeleton/spinner + label việc đang làm; không giả progress |
| Empty | chưa có dữ liệu | mô tả trống + hành động đầu tiên (vd "Chọn thư mục") |
| Error | job/screen lỗi | `error.code` + message + retryable + next_action; nút Retry chỉ khi retryable; link diagnostics |
| Unavailable | capability thiếu | tên capability + lý do + (nếu có) cách bật |

## 4. waiting_user, cancel, dữ liệu chưa lưu

- **waiting_user:** banner nổi bật trong module (không chiếm toàn app): nêu
  việc người cần làm ("Đăng nhập trên cửa sổ Chromium", "Rà soát 3 trường",
  "Quyết định Finalize"). Job vẫn hiển thị running-context phía sau.
- **Cửa sổ Chromium headed** (Playwright, Python-owned): khi job vào
  `waiting_user:login` shell đưa cửa sổ Chromium lên trước **một lần có chủ
  đích**; sau đó không giật focus lặp lại. Khi user quay lại shell, shell không
  giật Chromium về. Không focus-stealing nói chung (invariant bàn giao).
- **Cancel:** nút Hủy hiện ở accepted/running/waiting_user. Bấm → confirm
  dialog nêu hậu quả ("hồ sơ đã prepare sẽ giữ draft, chưa upload"). Xác nhận
  → `canceling` → `canceled`. Cancel **không bao giờ** trigger Finalize.
- **Dữ liệu chưa lưu:** form dirty + user rời module/đóng app → chặn bằng
  dialog "Lưu/Bỏ/Hủy". Refresh nền/poll job **không ghi đè** field user đang
  sửa (merge theo field-level: field đang focus/dirty không bị overwrite).
- **Không auto Save/Finalize; không tự điền lựa chọn trống** (invariant bàn
  giao) — mọi nút quyết định nghiệp vụ do người bấm.

## 5. Hai luồng nghiệp vụ đầu tiên (acceptance per module)

### 5.1 upload_lab: website → env/login → sổ Excel (tab Audit) → scan → queue → prepare từng đợt → người dùng Lưu

Module Upload Lab có đúng hai tab (spec `upload_lab/docs/spec_UI.md`): *Audit
Sổ Công Chứng* và *Quét & Upload Hồ Sơ*. Không có trang nhật ký/cấu hình riêng;
kiểm tra môi trường hiển thị inline đầu tab Audit.

| Bước | Trạng thái | UX bắt buộc |
|---|---|---|
| Chọn website | idle | dropdown `nam_dinh` dùng chung hai tab; không ô nhập URL; website chưa đăng ký bị từ chối |
| Preflight env | checking | checklist pass/fail từng mục inline đầu tab Audit; fail → Error state + hướng dẫn |
| Login portal | waiting_user (login) | đưa Chromium headed lên trước 1 lần; xác nhận gắn đúng job |
| Tải/chọn + audit sổ Excel | running→completed | bốn KPI + hai bảng `STT|Ngày|Số công chứng|Ghi chú` (MIN-77); tự nạp sau tải/chọn |
| Chọn folder/nguồn | idle | native file dialog qua Electron main |
| Scan/extract | running | progress `done/total`, tên file đang xử; cancel được |
| Queue hồ sơ | idle (bảng) | bảng `✓|STT|Ngày|Số công chứng|Ghi chú|Địa chỉ file`; chọn mặc định số thiếu khi có Excel |
| Prepare từng đợt | running→waiting_user (review) | tối đa N tab/đợt; app chỉ điền sẵn — **người dùng tự bấm Lưu trong Chromium**, không có nút Finalize trong app |
| Kết quả | completed/partial/failed | breakdown theo `record_id`+stage; retry chỉ retryable; không duplicate upload; chưa xác minh → Cần đối chiếu |

### 5.2 notary_v2: case → intake/OCR → review/confirm → workspace → Word

> UX cấp sản phẩm và hành vi chi tiết của tab `Soạn hồ sơ` (Stage/Pool/
> Diagram, intake đa nguồn, commit/revision/conflict, xuất Word nhiều văn
> bản) là SOT của `2026-09-24-notary-v2-case-drafting-electron-ux.md` +
> `notary_v2/docs/platform/case-workspace/drafting-tab.md`. Bảng dưới chỉ
> giữ acceptance theo vocabulary trạng thái chung của shell.

| Bước | Trạng thái | UX bắt buộc |
|---|---|---|
| Danh sách/tạo case | idle/running | list rỗng → Empty state |
| OCR intake | running→waiting_user | kết quả theo lớp RAW→…→INFERRED + source_ref |
| Review/confirm | waiting_user | từng trường: raw vs normalized; confirm = hành động người; unconfirmed không vào business truth |
| Soạn hồ sơ (Case Workspace) | idle | Stage/Pool/Diagram; draft không mất khi đổi module — chi tiết → spec `2026-09-24` + `drafting-tab.md` |
| Word export | running→completed/partial | Đích (spec `2026-09-24` §7): popup chọn **nhiều** văn bản → **một** folder đích qua native directory picker → mỗi văn bản một `.docx` độc lập; trùng tên tự thêm `_2`/`_3`; kết quả `Đã lưu`/`Lỗi` theo từng file |
| Local OCR | **unavailable** | hiển thị "Không khả dụng (stack parked)" — D0-3 pending |

- **Zalo (ngoài luồng tab — quyết định owner 24/09):** tab `Soạn hồ sơ`
  **không có** nút/popup/command/trạng thái Zalo. Module Zalo là phần mềm
  riêng, trao đổi với máy chính qua contract riêng — spec giao tiếp hiện ở
  `notary_v2/docs/platform/zalo-document-inbox/` trong giai đoạn chuyển
  tiếp; không tải hoặc xem trước ảnh Zalo trong app.

## 6. Diagnostics & error surface

- Trạng thái/Settings có panel diagnostics: env check (P1 contract_book
  env service tương đương), phiên bản shell/sidecar, trạng thái helper,
  log đã redact. Credential/cookie/token không bao giờ hiển thị.
- Mọi error surface theo shape MIN-64 §2.2 (`code/message/retryable/
  next_action`); không hiển thị stack trace cho người dùng cuối — stack chỉ
  trong diagnostics.

## 7. Checklist nghiệm thu (MIN-32 slice)

- [ ] Mỗi module có flow + acceptance cho idle/checking/running/
      waiting_user/canceling/failed/completed (+unavailable).
- [ ] Đổi module không mất state/job — có test chuyển đổi ở P5/P6.
- [ ] waiting_user phân biệt login/review/finalize; không focus-stealing.
- [ ] Cancel không Finalize; retry không duplicate; refresh nền không đè dữ liệu.
- [ ] Layout 1280×820, usable 760×520, light theme.
- [ ] Owner duyệt trước implementation (P5/P6).
