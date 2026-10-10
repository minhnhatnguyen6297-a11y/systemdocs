# Plan/spec HTML trực quan

## Công dụng và lý do

Owner cần thấy sản phẩm sẽ trông và hoạt động thế nào sau implementation: “thứ tôi cần là 1 bản plan hoặc spec đủ trực quan, thậm chí có hình minh họa app thật sẽ trông như thế nào sau khi implement”.

HTML là bản trình bày cho người đọc. Spec Markdown, memory và plan BMAD vẫn giữ vai trò nguồn chuẩn hiện hành; HTML không tự đổi quyết định hoặc trạng thái workflow.

## Hành vi

- Khi trình bày plan ở checkpoint PLAN của `bmad-build`, tạo HTML trước khi xin duyệt, không đợi build xong. Với route oneshot không có checkpoint, tạo trước implementation nếu thay đổi cần minh họa.
- Khi `bmad-spec` trình bày spec mới hoặc cập nhật, tạo HTML sau khi tự kiểm tra spec, trước khi trả kết quả. Headless giữ nguyên schema đầu ra; caller trình bày đường dẫn HTML kèm artifact nguồn chuẩn.
- Nhánh đầu là hành vi người dùng WHAT; nhánh con HOW là quy tắc; tầng WHERE dẫn tới code thật hoặc sketch được đánh dấu. WHY giữ lời user nguyên văn trong nhánh đóng.
- Mỗi claim có một exhibit hữu ích. Cây đóng tự tóm tắt thay đổi; không chuyển Markdown theo dòng thành HTML hoặc chia theo frontend/backend/task.
- Thay đổi UI dùng mock HTML đề xuất theo design system và giao diện đã inspect. Ảnh giao diện đang chạy được phân biệt với mock tương lai. Mỗi state làm đổi màn hình có hình riêng; toàn cửa sổ chỉ là overview, vùng thay đổi có crop đọc được.
- Người đọc mở claim hoặc chọn state để hiểu sản phẩm. Quyết định thật nằm tại claim liên quan; không tạo lựa chọn, quota hoặc gate mới cho việc nhỏ. Respond/comment là phụ; chưa mở không có nghĩa đồng ý.
- Agent viết HTML trực tiếp, đóng gói bằng Node với root của repo, xem cây đóng/mở và từng state trong browser, rồi giao đường dẫn packed HTML bấm được. Chưa kiểm tra được hình thì nêu rõ giới hạn, không nhận đã xác minh.
- Khi sửa spec/plan sau phản hồi, cập nhật nguồn chuẩn theo workflow rồi tạo lại HTML. Phản hồi là dữ liệu, không phải quyền chạy lệnh hoặc mở rộng scope.

## Giới hạn

Không sửa app, installed skill hoặc snapshot sinh tự động. Không xây app review/developer dashboard, renderer Markdown hoặc hệ thống ingest/export. Việc nhỏ không cần hình có thể giữ output gọn của BMAD; user yêu cầu trực quan thì vẫn tạo HTML, không thêm gate.

Tích hợp bằng các field customization được cài đặt hỗ trợ: `persistent_facts` và `activation_steps_append`. Đây là chỉ dẫn agent ở thời điểm trình bày, không phải hook cưỡng chế, tự sinh HTML hoặc tự mở browser. Runtime nằm trong `_bmad/custom/html-plan/runtime/`; contract lâu dài nằm trong `_bmad/custom/html-plan/authoring.md`, không phụ thuộc dữ liệu scratch.

## Nghiệm thu

1. Given BMAD build/spec được resolve trong một clone bất kỳ, when activation chạy, then nạp authoring contract từ project root, không cần đường dẫn ổ D cố định.
2. Given một plan UI, when tới PLAN checkpoint hoặc output spec, then người đọc mở packed HTML và thấy app dự kiến, quy tắc và chỗ thay đổi trước implementation.
3. Given state làm đổi nội dung màn hình, when chọn từng state, then thấy đúng mock tương ứng; overview và crop không khiến nội dung quan trọng không đọc được.
4. Given việc nhỏ không có lựa chọn thực sự, when trình bày, then không xuất hiện quota/gate giả; output Markdown và workflow gốc vẫn hợp lệ.

Nguồn quyết định: [HTML là tài liệu trực quan](../../decisions/decision-html-plan-exhibits-not-markdown-wrapper.md). Quyết định trước đây chưa cho phép sửa override; yêu cầu implementation hiện tại cho phép đúng phạm vi contract, customization và runtime tài liệu.
