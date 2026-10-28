---
id: decision-owner-case-storage-b-20261022
title: "Owner chốt phương án B cho lưu Hồ sơ và Lưu hồ sơ lưu tất cả (issue 13)"
date: '2026-10-22'
status: accepted
---

## Các quyết định owner đã trả lời

1. **Chọn phương án B làm cách lưu Hồ sơ** (issue 13): mỗi Người/Tài sản là
   một dòng riêng thuộc Hồ sơ; ghi đúng dòng thay đổi. **Không** chọn A
   (khối Hồ sơ duy nhất) và **không** bổ sung phần C (không giữ một bản
   "đã chốt" riêng tách khỏi dòng đang làm).
2. **Sửa Hồ sơ đã done là thay luôn nội dung hiện hành.** Mở Hồ sơ done ra
   sửa thì nội dung đang sửa chính là nội dung của Hồ sơ đó; xuất văn bản và
   lấy bộ thông tin làm nguồn cho Hồ sơ mới dùng bản hiện tại, không có bản
   done cũ nào được giữ riêng để dùng thay. Tình huống "Sửa Done → Cập nhật,
   chưa Lưu hồ sơ" ở §7 của spike vì vậy chốt theo hướng **thay Done ngay**,
   không theo hướng giữ Done + bản làm việc kiểu C.
3. **Lưu hồ sơ đồng thời lưu luôn tất cả:** bấm **Lưu hồ sơ** khi đang gõ dở
   một ô (chưa bấm **Cập nhật**) thì ô đang sửa cũng được ghi trong cùng một
   lượt Lưu hồ sơ. Không được báo đã lưu xong khi nội dung mới gõ chưa được
   lưu. Tình huống "Gõ thêm → Lưu hồ sơ trước Cập nhật" ở §7 của spike chốt
   theo đề xuất này.

## Hệ quả

- §6 và §9 của `spike-shared-data-transfer-boundary.md`: câu hỏi chọn A/B/C
  và câu hỏi nguồn khi sửa Done chưa Lưu hồ sơ **đã đóng** theo quyết định
  này. Trạng thái spike cập nhật tương ứng.
- Cùng các quyết định 22/10 trong
  `decision-owner-data-entry-save-rules-20261022.md`, hai câu trả lời này gỡ
  phần chờ của rà soát cấu trúc dữ liệu do owner đặt ra; phần tạm dừng code
  chờ quyết định A/B/C **kết thúc ở quyết định này**. Triển khai cụ thể vẫn
  theo quy trình thường lệ (spec trước, code sau, duyệt theo nhánh).

## Vẫn còn mở (không suy từ quyết định này)

- Thời điểm cấp/đối chiếu ID dùng chung (tại Cập nhật, tại Lưu hồ sơ hay mốc
  khác), xử lý Done thiếu neo, đổi/xóa neo, nhiều ID cũ trùng: vẫn theo
  nguyên tắc đã chốt 22/10 (không tự gom, không tự hợp nhất) và chờ chốt ở
  lượt thiết kế vật lý; quyết định này không tự chọn.
- Engine DB vật lý và migration: chưa chọn, không suy từ việc chọn B.
- Cách tính các báo cáo theo Nháp/Done: chưa chốt (giữ nguyên trạng thái ở
  decision 22/10).

## Ranh giới

- Chỉ ghi quyết định và cập nhật trạng thái spike; không sửa code, spec hành
  vi, schema hoặc migration trong lượt này.
- Một Hồ sơ một snapshot hiện hành; không tạo bảng phiên bản/lịch sử từng lần
  lưu (nhất quán quyết định 22/10 và việc loại phần C).
