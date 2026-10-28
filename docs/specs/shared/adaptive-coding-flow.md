# Luồng code thích ứng: việc ngắn-rõ và việc khó

## Công dụng và lý do

Owner chốt: việc **ngắn, rõ** đi luồng ngắn — todo, **một** implementation worker,
test thật, **một** reviewer độc lập; việc **khó** mới mở full workflow. Mục đích:
việc nhỏ không phải gánh ceremony của full, việc khó vẫn được kiểm soát đầy đủ, và
bốn review lens không tự chạy cho việc ngắn.

Spec này quyết định hành vi; code và override chỉ chứng minh hiện trạng.

## Hành vi

### Quyền thực thi và transport

- Mặc định coordinator giao implementation cho một subagent của harness hiện tại.
- User yêu cầu tự làm trong phiên thì coordinator implement và verify trực tiếp.
  Đây chỉ là lựa chọn người implement, **không** tự bỏ review độc lập.
- Chỉ bỏ review khi user chủ động chọn `none`/không review. Nếu reviewer không
  khả dụng, báo blocked tại bước review; không coi tự kiểm tra là review độc lập.
- Chỉ dùng Orca khi user yêu cầu rõ. Nếu không dùng được Orca, báo nguyên nhân và
  chờ khả năng thực thi hoặc user cho phép đổi transport; không âm thầm fallback.
- Coordinator là authority duy nhất; worker/reviewer không spawn thêm agent.

### Chọn route theo độ rõ, không theo số dòng

- Khảo sát repo và khám phá yêu cầu trước khi chọn route; chưa khảo sát rủi ro
  không tự nó là lý do ép full. Brainstorm khi cần làm rõ ý tưởng; viết spec khi
  ý định đã đủ rõ. Code review dùng cho code, artifact khác dùng review phù hợp.
- Việc khó mở full nhưng chỉ dùng các bước cần thiết, không tự thêm mọi bước.

- Route `oneshot` khi mọi điều đúng: yêu cầu rõ; đã biết mẫu/quy ước để theo; đã
  biết cách kiểm chứng; không còn quyết định hệ quả nào chưa chốt; rủi ro thấp.
- Route `full` khi sau inspect còn lựa chọn hành vi/kiến trúc cần chốt, chưa biết
  cách triển khai/kiểm chứng, hoặc có rủi ro cụ thể cần thiết kế trước. Ví dụ:
  migration có thể mất dữ liệu, đổi auth/quyền truy cập, hoặc shared contract chưa
  thống nhất. Nêu tác động và điểm còn thiếu, không chỉ ghi “rủi ro cao”.
- Chạm nhiều owner không tự ép full nếu contract đã rõ. Đổi tên hàng loạt theo
  mẫu đã biết có thể dùng oneshot; sửa ít dòng quyền truy cập chưa chốt cần full.
- Số dòng/số file chỉ là tín hiệu phụ, không phải tiêu chí quyết định. Nêu lý do
  chọn route trong một dòng; chưa đủ rõ thì nói rõ còn thiếu gì.

### Planning theo điểm còn thiếu

| Điểm còn thiếu sau inspect | Bước dùng | Điều kiện thoát |
|---|---|---|
| Chưa rõ vấn đề/kết quả mong đợi | Khám phá, brainstorm khi cần | Có hướng đề xuất, mục tiêu và non-goals rõ |
| Thiếu dữ kiện ngoài repo | Research | Có nguồn trả lời câu hỏi; ghi rõ dữ kiện còn chưa biết |
| Hành vi cần hợp đồng bền vững | Tạo/cập nhật spec | Capabilities, constraints và nghiệm thu đủ rõ |
| Trải nghiệm UI thay đổi đáng kể | UX/minh họa | Luồng và trạng thái cần triển khai đã rõ |
| Shared contract hoặc quyết định nền tảng chưa thống nhất | Architecture | Quyết định cần chia sẻ, trade-off và constraints đã chốt |
| Còn lựa chọn hệ quả thuộc user | Human gate | User chốt lựa chọn; không implement phần phụ thuộc trước đó |

- Không chạy bảng như checklist. Chỉ kích hoạt bước giải quyết điểm thiếu thực tế.
  Phần độc lập với lựa chọn đang mở có thể tiếp tục; không đoán phần phụ thuộc.
- Đang làm nhẹ mà worker thấy sai giả định/phạm vi hoặc thiếu cách kiểm chứng:
  dừng phần bị ảnh hưởng, báo bằng chứng; coordinator inspect bổ sung rồi tiếp tục
  hoặc nâng route. Không tự mở rộng task theo ý tưởng reviewer.

### Một implementation worker

- Coordinator giao **một** worker todo/plan tự chứa: mục tiêu, nguồn hành vi/spec,
  file/entrypoint liên quan, phạm vi và điều không được đổi, nghiệm thu quan sát
  được, cách kiểm tra. Không dựa vào việc worker có lịch sử hội thoại.
- Việc ngắn dùng todo gọn; full dùng plan. Ngoại lệ tự làm áp dụng theo mục quyền
  thực thi phía trên; không buộc spawn để thỏa checklist.
- Worker chạy test/smoke **trước review**. Bằng chứng gồm lệnh, kết quả và hành vi/
  tiêu chí được chứng minh; lệnh xanh không liên quan không đủ. Coordinator đối
  chiếu nghiệm thu và phần vừa đổi trước khi giao review; lỗi test phải xử lý.
- Sau patch, ưu tiên người implement ban đầu sửa và chạy lại kiểm tra liên quan.
  Nếu worker mất phiên/không hoạt động, coordinator inspect partial state trước;
  chỉ một người mutate tại một thời điểm. Thay worker bằng bàn giao diff, task,
  kiểm tra đã/chưa chạy và finding còn mở; không chờ worker cũ vô hạn.
- Nếu chưa có cách kiểm chứng tin được, quay lại giải quyết khoảng trống; không
  báo task hoàn tất chỉ vì đã viết code. Áp dụng cả review riêng có apply-patches.

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
- Reviewer không khởi động, mất phiên hoặc không trả kết quả: inspect trạng thái,
  thử phục hồi hoặc thay reviewer với cùng phạm vi. Lỗi lặp lại thì báo blocked,
  không lặp dispatch vô hạn và không coi thiếu report là report sạch.
- Finding được chấp nhận phải được sửa hoặc defer minh bạch: lý do, tác động,
  owner/việc tiếp theo. Không defer lỗi làm nghiệm thu không đạt để báo xong.
- Sau sửa chạy lại verification; review lại phần rủi ro còn tồn tại, không chạy
  lại mọi lens mặc định. Nếu cùng lỗi nền tảng còn lặp sau hai vòng sửa có ý nghĩa,
  dừng vòng patch và quay lại intent/spec/plan để sửa nguyên nhân.


### Giữ nguyên các luật hiện hành

- Đổi hành vi thì nạp và cập nhật spec liên quan trong `docs/specs/` trước
  khi code.
- Giữ contract HTML plan/spec và ngoại lệ việc nhỏ; không tạo HTML cho báo cáo/chat
  thường.

## Giới hạn

- Override là chỉ dẫn agent tại thời điểm chạy, không phải hook cưỡng chế.
- Không sửa installed skill hoặc snapshot sinh tự động; chỉ dùng field customization
  được cài đặt hỗ trợ.

## Hoàn tất một task

- Nghiệm thu quan sát được đạt; không còn quyết định đang mở ảnh hưởng kết quả.
- Verification liên quan đã chạy đạt trên thay đổi cuối cùng, kể cả sau patch.
- Review đã có kết quả và disposition từng lens/finding, hoặc user chủ động bỏ
  review; không còn finding cản nghiệm thu. Deferred được công bố rõ.
- Code/spec/docs liên quan nhất quán; báo kết quả, bằng chứng và giới hạn thực.
- Nếu thiếu prerequisites/verification/review thì báo blocked và phần đã làm;
  không gắn “done”. Đây không phải yêu cầu thêm dashboard hoặc hệ thống state.

## Nghiệm thu cấu hình flow

| Kịch bản | Kết quả cần có |
|---|---|
| Ngắn-rõ, không yêu cầu tự làm | Todo → một implementer → verification → một reviewer |
| Task khó | Full, chỉ planning cần thiết; baseline một reviewer |
| Không có rủi ro cần lens phụ | Không fan-out phụ; clean result hợp lệ |
| User yêu cầu tự implement | Main implement; review vẫn độc lập trừ explicit none |
| Có patch hoặc worker cần thay | Bàn giao đúng phạm vi; verification trên thay đổi cuối |
| Đang làm phát hiện intent/contract chưa rõ | Dừng phần phụ thuộc; inspect/replan hoặc human gate |
| Reviewer không có kết quả / Orca được yêu cầu nhưng không dùng được | Blocked, không clean/done hay đổi transport ngầm |
| Resolve/render override | Luật contract xuất hiện; không dùng 100 dòng làm tiêu chí |

Render chứng minh chỉ dẫn đã được nạp, không chứng minh mọi phiên agent tuân thủ.

Nguồn quyết định:
[decision-79](../../decisions/decision-79-adaptive-flow-short-clear-one-worker-todo-test-one-review.md).
- Quyết định transport mới:
  [native subagents, Orca on request](../../decisions/decision-native-subagents-orca-on-request.md)
  thay thế riêng yêu cầu Orca trong decision-79.
- Làm rõ chuyển bước và hoàn tất:
  [decision](../../decisions/decision-adaptive-flow-transitions-and-completion.md).
