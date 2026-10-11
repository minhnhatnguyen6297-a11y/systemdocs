# Luồng code thích ứng: việc ngắn-rõ và việc khó

## Công dụng và lý do

Owner chốt: việc **ngắn, rõ** đi luồng ngắn — todo, **một** implementation worker,
test thật, **một** reviewer độc lập; việc **khó** mới mở full workflow. Mục đích:
việc nhỏ không phải gánh ceremony của full, việc khó vẫn được kiểm soát đầy đủ, và
bốn review lens không tự chạy cho việc ngắn.

Spec này quyết định hành vi; code và override chỉ chứng minh hiện trạng.

## Hành vi

### Chọn route theo độ rõ, không theo số dòng

- Khảo sát repo và khám phá yêu cầu trước khi chọn route; chưa khảo sát rủi ro
  không tự nó là lý do ép full. Brainstorm khi cần làm rõ ý tưởng; viết spec khi
  ý định đã đủ rõ. Code review dùng cho code, artifact khác dùng review phù hợp.
- Việc khó mở full nhưng chỉ dùng các bước cần thiết, không tự thêm mọi bước.

- Route `oneshot` khi mọi điều đúng: yêu cầu rõ; đã biết mẫu/quy ước để theo; đã
  biết cách kiểm chứng; không còn quyết định hệ quả nào chưa chốt; rủi ro thấp.
- Route `full` khi bất kỳ điều nào đúng: có lựa chọn hành vi/kiến trúc cần người
  quyết; chưa biết cách triển khai; chưa có cách kiểm chứng tin được; thay đổi rủi
  ro cao hoặc chạm nhiều owner; còn quyết định hệ quả chưa chốt.
- Số dòng/số file chỉ là tín hiệu phụ, không phải tiêu chí quyết định. Nêu lý do
  chọn route trong một dòng; chưa đủ rõ thì nói rõ còn thiếu gì.

### Một implementation worker

- Coordinator giao todo/plan cho **đúng một** implementation worker qua subagent của
  harness hiện tại; dùng Orca chỉ khi user yêu cầu rõ.
- Việc ngắn mặc định: coordinator không tự viết code; sau khi có plan/todo, dispatch một
  worker chạy phần implement của oneshot.
- Việc khó: handoff của full cũng dispatch đúng một worker đó.
- Worker chạy test/smoke thật **trước review** rồi báo lại. Worker **không** spawn ai.
- Sau mỗi patch từ review, giao chính implementation worker ban đầu sửa và chạy
  lại test/smoke liên quan; không hoàn tất nếu chưa có bằng chứng chạy lại đạt.
  Luật này áp dụng cho oneshot, full và việc áp dụng patch trong review riêng.

### Coordinator sở hữu review

- Coordinator chạy bước review và tự dispatch reviewer; implementation worker không
  tự review.
- Mặc định **một** quick reviewer cho cả hai route. Chọn thorough vẫn có Quick
  không điều kiện, bốn lens có điều kiện chỉ là phần thêm. Chỉ bỏ review khi user
  chủ động chọn none; không được bỏ vì danh sách có điều kiện rỗng.
- Mỗi lens đã chạy phải có kết quả riêng: finding được chấp nhận, finding bị bác
  kèm bằng chứng, hoặc không có finding. Ghi kết luận từng finding theo bằng chứng;
  không thay kết quả riêng của lens sạch bằng một tổng kết chung.
- Chỉ thêm lens có tên khi có **lý do rủi ro cụ thể**: công bố lý do trước khi chạy,
  và sau khi lens trả về ghi lại kết luận theo bằng chứng cho từng finding.
- Blind-hunter không còn quota số finding; kết quả sạch là hợp lệ.
- Reviewer độc lập, không dùng skill, không spawn.

### Transport theo yêu cầu

- Mặc định dùng cơ chế subagent của harness hiện tại (OMP hoặc agent khác).
- Chỉ dùng Orca khi user yêu cầu rõ; theo skill/guide Orca hiện hành lúc đó.
- Coordinator là authority duy nhất; worker và reviewer không spawn thêm agent.
- User yêu cầu tự làm trong phiên hiện tại thì làm trực tiếp, vẫn test/smoke và
  báo rõ nếu không có review độc lập; không ép spawn worker để thỏa checklist.

### Giữ nguyên các luật hiện hành

- Đổi hành vi thì nạp và cập nhật spec liên quan trong `_bmad-output/specs/` trước
  khi code.
- Giữ contract HTML plan/spec và ngoại lệ việc nhỏ; không tạo HTML cho báo cáo/chat
  thường.

## Giới hạn

- Override là chỉ dẫn agent tại thời điểm chạy, không phải hook cưỡng chế.
- Không sửa installed skill hoặc snapshot sinh tự động; chỉ dùng field customization
  được cài đặt hỗ trợ.

## Nghiệm thu

1. Given một việc ngắn-rõ không có yêu cầu tự làm trực tiếp, when build chạy, then chỉ một implementation worker được
   dispatch, test thật chạy, và đúng một reviewer độc lập chạy.
2. Given một việc khó, when build chạy, then mở full workflow nhưng vẫn một worker và
   mặc định một reviewer.
3. Given không có lý do rủi ro cụ thể, when review chạy, then không lens phụ nào chạy
   và kết quả sạch được chấp nhận.
4. Given override được resolve trong một clone bất kỳ, when render, then workflow
   chứa luật thích ứng và không còn ngưỡng 100 dòng làm tiêu chí.

Nguồn quyết định:
[decision-79](../../decisions/decision-79-adaptive-flow-short-clear-one-worker-todo-test-one-review.md).
- Quyết định transport mới:
  [native subagents, Orca on request](../../decisions/decision-native-subagents-orca-on-request.md)
  thay thế riêng yêu cầu Orca trong decision-79.
