# Decisions — MIN-132

Chỉ ghi quyết định phát sinh trong task. Quyết định nghiệp vụ/UX đã chốt ở
các phase trước (`MIN-125/decisions.md` Q1–Q12 + §13 contract, `MIN-126/
decisions.md` duyệt bản mẫu) — file này không lặp lại.

## D1 — Không có sửa code tích hợp nào trong P9

- Bối cảnh: probe Electron ban đầu báo một số "fail" (gán two-party p16, save
  two-party, đếm node >30, dialog conflict, Enter mở dialog).
- Quyết định: truy lần lượt từng case bằng DOM/console trước khi kết luận lỗi
  app. Tất cả đều là lỗi driver/harness (modal chồng chưa dọn, click qua
  element bị che, mở sai module/case, Enter dispatch thiếu `char`). Chạy lại
  đúng cách → pass toàn bộ.
- Hệ quả: **không sửa dòng code nào của app trong P9**; thay đổi repo chỉ gồm
  task record + đối chiếu docs trạng thái. Việc này có chủ đích: P9 không được
  "bốc thuốc" khi chưa chứng minh lỗi nằm ở app.

## D2 — Docs chỉ sửa ngôn ngữ trạng thái, không đổi semantics

- Bối cảnh: owner yêu cầu dọn tham chiếu v1→v2 và marker "proposed/pending"
  đã lỗi thời sau khi §13 APPROVED + P4–P8 triển khai.
- Quyết định: mọi chỉnh sửa ở `contracts/README.md`, `shell/README.md`,
  `notary_v2/docs/platform/case-workspace/{drafting-tab,visual-design}.md`,
  `upload_lab/docs/{spec_UI,visual-design}.md`, `docs/product/ui/*` chỉ thay
  "chờ duyệt/DRAFT/PENDING/chưa có" bằng trạng thái thật (APPROVED
  27/09/2026 / đã triển khai ở Pk). **Không** di chuyển SOT, không đổi giá trị
  token nào trong `tokens.json` (chỉ sửa `note`), không đổi contract text.
- Marker **còn đúng** được giữ nguyên: `upload.workflow.v1` vẫn DRAFT;
  `domains/inheritance/spec.md` vẫn DRAFT; C1–C4 §13.13 vẫn mở; schema/
  examples v1 giữ nguyên (v1 còn hợp lệ cho consumer legacy).

## D3 — Electron viewport kiểm bằng emulation, ghi rõ giới hạn DPI/OS

- Bối cảnh: yêu cầu checklist 1280×800/1366×768/1920×1080 + DPI 125%/150%.
- Quyết định: chạy `Emulation.setDeviceMetricsOverride` qua CDP cho các cỡ
  trên; **không** claim đã kiểm DPI Windows thật — OS scaling không đổi được
  trong phiên, và CDP `Browser.getWindowForTarget` vắng trên bản Electron 31
  nên không resize cửa sổ OS được. Kết quả ghi "CSS pixels + DPR emulated",
  phần DPI thật đánh dấu chưa kiểm chứng.

## D4 — Word chỉ kiểm regression + biên, không claim tính năng mới

- Bối cảnh: plan P9 nói rõ "không triển khai Word mới; chỉ kiểm không hồi quy".
- Quyết định: xác nhận tab Word/dialog mở đúng trên case thừa kế, two-party
  bị khóa đúng theo §13.5 (`case_type_unsupported`), giới hạn 5 tài sản/20
  người vẫn là rule contract/backend — và ghi tường minh trong handoff: P9
  **không** bàn giao/claim hoàn tất chức năng xuất Word.
