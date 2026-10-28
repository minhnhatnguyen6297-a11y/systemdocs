# Nội dung để người dùng copy giao cho worker

```text
Tôi giao bạn sửa lỗi thông báo sơ đồ theo plan:
D:/systemdocs/docs/plans/plan-diagram-error-fix-20261009.md

Tôi duyệt phạm vi sửa relErrText, thêm test chống tái phát và kiểm chứng Electron theo plan. Đọc plan cùng acceptance.md, open-reports.md, review-evidence.json trong thư mục diagram-error-fix-20261009 cạnh plan. Chuyển plan từ Draft sang ready-for-dev rồi thực hiện theo BMAD; không hỏi lại việc sửa đã giao nếu scope không đổi.

Giữ alias relErrText, đổi nguồn hàm sang .errText; test phải nạp catalog thật trước sơ đồ. Chứng minh test mới bắt lỗi trước sửa và đạt sau sửa. Kiểm tra evaluate, tự evaluate sau thao tác, render danh sách lỗi, save lỗi, ngoại lệ invalid_state/conflict và lưu thành công mở lại trong Electron thật. Giữ dữ liệu chưa lưu.

Tôn trọng AGENTS.md. Kiểm tra branch/file bẩn trước khi làm; không ghi đè hay commit công việc người khác. Nếu cần tách worktree/agent thì chỉ dùng Orca. Tạo evidence dưới docs/tmp/diagram-error-fix-20261009/ trong checkout đang sửa. Không thêm dependency hoặc test hook production chỉ để kiểm tra.

Không sửa công cụ báo lỗi/engine/nghiệp vụ/bố cục theo phỏng đoán. Giữ 12 report mất mô tả ở trạng thái còn mở. Không kết luận sửa xong mọi lỗi trong 37 report.

Hoàn thành thì review, commit riêng thay đổi của task và trả: commit SHA, file đã sửa, lệnh chạy lại, log trước/sau, kết quả Electron từng ca, ảnh, hạn chế và report còn mở. Không push hoặc merge. Nếu thiếu native check hoặc gặp thay đổi ngoài scope, báo đúng chỗ vướng; không báo Done chỉ vì test Node xanh.
```

Nội dung trên là mẫu giao việc; chưa có worker nào được khởi chạy hoặc nhận lệnh trong phiên lập kế hoạch.
