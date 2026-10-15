---
id: decision-p1-sequential-loose-tickets
title: Giữ ticket rời và triển khai P1 tuần tự theo plan riêng
date: '2026-10-15'
status: accepted
---

## Quyết định

Người dùng chọn rõ phương án A bằng câu trả lời “a”: giữ các ticket rời trong `_bmad-output/backlog/`, lập plan riêng cho từng ticket và thực hiện tuần tự. Bắt đầu #11 → #4 → #6 → #7 → #5, sau đó đến các P1 còn lại theo phạm vi và điều kiện của từng ticket.

Không đổi config hoặc tạo initiative để thực hiện lựa chọn này. Thứ tự trên là trình tự thực thi đã chọn, không tự thêm dependency nghiệp vụ vào các ticket.

## Ranh giới

Khi thiếu thông tin nghiệp vụ cần thiết, dừng và hỏi người dùng trước khi chọn thay. Lựa chọn triển khai P1 không duyệt hàng loạt semantics còn mở, không biến spike thành quyền sửa sản phẩm và không bỏ điều kiện riêng của từng ticket.

Route được BMAD xác định riêng cho từng issue theo điều tra và rủi ro, giữ các checkpoint tương ứng của workflow. #11 hiện dùng full route vì kế thừa mức rủi ro high, không phải vì người dùng yêu cầu mọi ticket dùng full. Lựa chọn A chỉ chốt ticket rời, plan riêng và thứ tự; không cấm oneshot cho issue sau nếu đủ điều kiện rủi ro thấp theo workflow.

## Nguồn và hệ quả

Nguồn: yêu cầu triển khai sửa lỗi ưu tiên cấp 1 và câu trả lời “a” của người dùng trong phiên 15/10/2026; catalog `_bmad-output/backlog/README.md` giữ phạm vi P1 và trạng thái quyết định/bằng chứng.

#11 được phân giải bằng folder backlog tường minh; không cần đặt active initiative. Quyết định này ghi cách tổ chức và trình tự làm việc, không tuyên bố ticket nào đã hoàn tất hoặc đã có bằng chứng runtime.
