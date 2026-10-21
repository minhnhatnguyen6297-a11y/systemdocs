---
id: decision-owner-persistent-case-drafts-20261021
title: "Owner duyệt: Hồ sơ nháp lưu database, nhãn Nháp rõ ràng"
date: '2026-10-21'
status: accepted
---

## Bối cảnh

Trong brainstorming thiết kế dữ liệu, owner cần giữ Hồ sơ đang làm dở để
mai tiếp tục, kể cả mới nhập được 2/6 trường Người. Owner ưu tiên cách đơn
giản: yêu cầu lưu khi đóng; nếu phục hồi tắt đột ngột phức tạp thì giữ lưu
thủ công. Hướng UI Nhân bản Hồ sơ đang được bàn, chưa có thiết kế đầy đủ.

## Quyết định đã duyệt

Owner: “tôi duyệt phần hồ sơ nháp vẫn lưu database nhưng đóng nhãn nháp rõ
để tránh lẫn khi thực hiện thống kê báo cáo”.

- Hồ sơ nháp được lưu bền trong database ứng dụng để mở lại làm tiếp.
- Trạng thái Nháp phải được giữ khi lưu/đọc lại và thể hiện rõ khi hiển thị,
  thống kê hoặc báo cáo có chứa Hồ sơ nháp; không gộp mà làm mất phân biệt Nháp.
- Lưu tiến độ phải giữ được dữ liệu còn thiếu, kể cả chỉ 2/6 trường Người;
  không ép nhập đủ bộ trường chỉ để giữ nháp. Không tự điền dữ liệu cho đủ.

## Phần còn mở

- Mốc nghiệp vụ chuyển khỏi Nháp; từng loại thống kê/báo cáo tính Nháp ra
  sao, tiêu chí lọc và mặc định hiển thị. Nhãn rõ không tự quyết đáp án này.
- Bảng/cột/cấu trúc lưu nháp, thời điểm tạo liên kết Người/Tài sản, ranh giới
  ghi danh bạ dùng chung và nội dung được lấy khi Nhân bản. Chưa duyệt schema.
- Chi tiết tương tác lưu/đóng; ưu tiên lưu thủ công theo chỉ dẫn đơn giản
  của owner, chưa yêu cầu tích hợp chặn Windows shutdown hay AutoRecover.

## Hiện trạng và hiệu lực

Đọc source: `shell/src/renderer/notary/case-drafting-model.js` giữ nháp chưa
lưu trong object của phiên; `saveDraft()` gọi `workspace_create`. Đường
`notary_v2/services/case_workspace.py` hiện tạo cả master, Hồ sơ `draft`,
liên kết và snapshot, với các điều kiện lưu hiện có. `_validate_stage`
chỉ bắt buộc tên Người, các trường khác nhận null; chưa có bằng chứng rule
ép đủ sáu giá trị trong đường này. Đây là đọc tĩnh, chưa audit mọi màn.

Quyết định này là yêu cầu thiết kế cần triển khai sau; trạng thái `draft`
hiện có không chứng minh đã đáp ứng lưu tiến độ mới. Phiên hiện tại tiếp tục
brainstorming, không sửa code/contract/schema, chạy migration hoặc test mẫu.
#41 vẫn mở/gate mẫu đóng. Spec module và sổ tay được đồng bộ cùng phiên.
