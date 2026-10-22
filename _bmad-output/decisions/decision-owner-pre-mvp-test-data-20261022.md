---
id: decision-owner-pre-mvp-test-data-20261022
title: "Owner xác nhận tiền MVP: dữ liệu hiện tại là test, bỏ trạng thái locked, dựng bộ hồ sơ giả lập"
date: '2026-10-22'
status: accepted
---

## Các quyết định owner đã trả lời

1. Sản phẩm **chưa xong MVP**; toàn bộ dữ liệu Hồ sơ hiện có trong app chỉ
   là dữ liệu test. Khi chuyển sang cấu trúc lưu phương án B
   (`decision-owner-case-storage-b-20261022.md`), **được xóa bỏ dữ liệu cũ**,
   không cần migration bảo toàn dữ liệu thật và không cần giữ tương thích
   đọc dữ liệu cũ như dữ liệu production.
2. **Trạng thái `locked` cũ bỏ hẳn.** Hệ trạng thái Hồ sơ chỉ còn
   `draft`/`done` theo quyết định B. Câu hỏi mở "dữ liệu locked cũ chuyển
   thành done hay giữ khóa" trong plan triển khai issue 13 **đã đóng**:
   không giữ nghĩa khóa, không mở trạng thái khóa riêng.
3. Owner yêu cầu **dựng một bộ hồ sơ giả lập ổn định** (dữ liệu tổng hợp tự
   tạo, không dùng dữ liệu khách thật) để dùng test lặp lại và tìm lỗi khi
   phát triển. Bộ giả lập phải có đáp án kỳ vọng xác định trước cho từng ca
   để đối chiếu kết quả code, giữ nguyên tắc test của repo và gate #41
   (chỉ input tổng hợp/cô lập).

## Hệ quả kỹ thuật (Muse đã chốt hướng, ghi để triển khai bám theo)

- Cutover sang dòng case-owned của B làm theo hướng đơn giản tiền MVP: tạo
  cấu trúc mới, dữ liệu test cũ không phải gánh bảo toàn; vẫn giữ raw/lịch
  sử kỹ thuật trong repo theo luật chung, không xóa tài liệu/evidence.
- Bộ hồ sơ giả lập là fixture tổng hợp trong môi trường test cô lập; đáp án
  kỳ vọng chốt trước khi xem output code (không lấy output làm đáp án).
