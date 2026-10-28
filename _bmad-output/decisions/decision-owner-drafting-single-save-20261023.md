---
id: decision-owner-drafting-single-save-20261023
title: "Soạn hồ sơ dùng một trạng thái đang sửa, chỉ Lưu hồ sơ ghi DB"
date: '2026-10-23'
status: accepted
---

## Quyết định owner

Owner chốt trong chat 23/10/2026: **bỏ hẳn nút Cập nhật**, kể cả nhãn Lưu nháp của nút đó. Stage, Pool và Diagram dùng chung trạng thái đang sửa của hồ sơ đang mở; sửa Stage phải phản ánh ngay ở Pool, khả năng gán người, nhãn node và evaluate, không đợi ghi database.

**Lưu hồ sơ** là lần ghi database duy nhất của luồng soạn: một transaction `workspace_save_case` ghi Stage + metadata Hồ sơ + Diagram + `docx_import` thay đổi và chuyển `draft` → `done`. Hồ sơ mới đang Nháp ở client không ghi DB vội. Baseline “đã lưu gần nhất” chỉ phục vụ wire/identity hint, diff và xác định thay đổi; không là nguồn dữ liệu hiển thị thứ hai.

Khi đóng/rời hồ sơ chưa Lưu, thay đổi trong bộ nhớ sẽ mất; hệ quả này đã báo owner. Dùng cơ chế `canLeave` và window-close guard hiện có để cảnh báo rõ, không ghi DB ngầm, không thêm localStorage/file khôi phục. Mất điện hoặc tiến trình bị kết thúc cưỡng bức không được bảo đảm khôi phục.

## Nguồn và lý do

- Chỉ đạo owner trong chat 23/10/2026 của lát G4.
- Recon §2, §4 G4/G6, §5 — file `e2e-drafting-bug-recon-20261023.md` trong thư mục tmp của worktree `e2e-drafting-recon` (ngoài repo này): mô hình hai lần ghi Cập nhật/Lưu hồ sơ khiến Stage đang sửa khác Pool/Diagram theo committed; người vừa thêm không gán được và nhãn cũ còn trong phiên. Đây là gốc G4. G6 đã quan sát nhưng điều kiện kích hoạt chưa được cô lập; không suy việc đổi thiết kế là proof đã sửa runtime.

## Phương án đã loại

- Giữ Cập nhật để ghi Stage trung gian: giữ hai mốc ghi và hai nguồn hiển thị, trái luồng owner chọn.
- Tự lưu nháp ngầm khi rời/đóng: trái yêu cầu Nháp chưa ghi DB và biến thao tác rời thành ghi dữ liệu không được user chọn.

## Hệ quả và ranh giới

- Lưu lần đầu đi nhánh tạo-mới của `workspace_save_case`, giữ `draftId` làm `idempotency_key` qua retry để chống trùng; không gọi `workspace_create` từ nút lưu của màn soạn nữa.
- Giữ `base_revision`, hộp thoại xung đột và trạng thái đang sửa khi ghi lỗi; cửa sổ giữa hai lần ghi có thể dài hơn, không tự ghi đè DB.
- `workspace_commit_stage` vẫn tồn tại ở server/adapter/REST cho consumer khác; renderer Soạn hồ sơ không gọi. Không xóa API server vì bỏ nút.
- Gỡ nguồn Word và xác nhận binding chuyển thành sửa `docx_import` trong phiên, ghi cùng Lưu hồ sơ. Options/xuất Word vẫn đọc Hồ sơ đã lưu từ server; cần Lưu trước khi dùng thay đổi đó để xuất, không thay DB bằng payload xuất mới.
- `saveCaseMeta` → `workspace_update` cho Nơi niêm yết trong dialog xuất Word là đường ghi riêng của luồng xuất được giữ nguyên, không phải tự lưu Stage/Diagram khi rời. Tạo danh bạ ủy quyền, nhân bản, đổi loại và xóa hồ sơ là các lệnh nghiệp vụ riêng, không bị gọi ngầm thay Lưu hồ sơ.
- Giữ các bất biến [vòng 1](../tmp/fix-loop-round1-20261023.md): `positionTouched`, `syncPositionDefaults()` tại `saveCase`, `applyStageWriteError` và dọn lỗi theo mutator, toast lỗi sơ đồ/G5, identity hint khi lưu. Không đổi schema/điểm neo, không mở gate #41/mẫu thật.
- Lượt này chỉ sửa decision/contract/spec và thiết kế; chưa sửa hoặc nghiệm thu runtime G4/G6.
