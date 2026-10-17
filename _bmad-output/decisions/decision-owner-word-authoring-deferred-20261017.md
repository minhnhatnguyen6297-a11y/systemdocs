---
id: decision-owner-word-authoring-deferred-20261017
title: "Owner để tab Word tạo/lưu mẫu làm sau, cần spec kỹ"
date: '2026-10-17'
status: accepted
---

## Nguồn

Sau khi coordinator đã gửi câu hỏi nguồn vào/giữ bố cục của #19 trong hội thoại, owner trả lời nguyên văn:

> chức năng này tôi sẽ tự làm sau, cần spec kỹ. Chuyển issue khác

## Quyết định

- Tab Word tương lai để tạo/lưu mẫu lâu dài **DEFERRED**; owner sẽ tự làm sau. Cần **spec chi tiết trước implementation tương lai**. Không giao viết spec chi tiết hoặc triển khai trong lượt này.
- Chỉ áp cho #19/C18, không phải Xuất Word hiện có hoặc original-DOCX intake. Các luồng hiện có không bị dừng.
- Đáp án chốt **hoãn phạm vi**, không chọn A/B (DOCX giữ bố cục hay chỉ chữ dán), storage/catalog hoặc tiêu chí nghiệm thu. Các yêu cầu đó vẫn chưa chốt để đặc tả sau; không hỏi tiếp lúc này.
- Giữ leaf #19, Draft và `refined: false`; spike đã nhận đáp án phạm vi, không phải feature built. Không tạo UI, prototype hoặc quyết định sản phẩm thay owner.
- Chuyển tiếp #20 theo thứ tự đang làm; #19 không còn business gate đang chờ trả lời. Không thay phạm vi Office DEFERRED.

## Lịch sử

Commit `169e4faf9dfa6f4f6373009cfb25640b66af4c10` ghi câu hỏi PREPARED đúng thời điểm công bố. Sau đó câu hỏi đã được gửi trong parent final, owner trả lời hoãn như trên. Không sửa lại lịch sử thành đã chọn nguồn/bố cục.
