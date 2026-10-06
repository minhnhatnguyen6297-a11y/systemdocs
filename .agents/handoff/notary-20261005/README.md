# Bàn giao Notary — 05/10/2026

**Nhánh nhận:** `consolidate/monorepo`. Đây là chỉ mục tiến độ; spec sản phẩm ở
`docs/spec`, task và plan có hiệu lực ở Backlog. Không triển khai runtime trong
lượt gom này. Spec/plan từng bị Owner yêu cầu rút vẫn là lịch sử, không có hiệu lực.

## Từng việc và bước tiếp theo

| Việc | Tình trạng | Task/plan/spec và tham chiếu |
|---|---|---|
| Tra cứu địa chỉ cũ/mới | Spec/contract v2 đã duyệt; runtime còn v1. TASK-3 In Progress thuộc Devin; chưa có bằng chứng hoàn tất implementation. | [Spec chung](../../../docs/spec/shared/administrative-lookup.md), [consumer](../../../docs/spec/notary_v2/administrative-address.md), [contract](../../../contracts/notary-case-drafting.md), [schema v2](../../../contracts/notary-case-drafting/address-lookup.v2.schema.json), [TASK-3](../../../backlog/tasks/task-3%20-%20Triển-khai-lõi-tra-cứu-hành-chính-theo-spec-contract-v2.md), [plan](../../../_bmad-output/implementation-artifacts/plan-task-3-administrative-lookup-v2.md) |
| Nút Tra, popup và tool địa chỉ | TASK-4 To Do; theo spec mới chỉ tra khi bấm nút, kết quả copy, không tự ghi/nối vào ô. Không bật lại debounce cũ. | [TASK-4](../../../backlog/tasks/task-4%20-%20Tích-hợp-tra-cứu-vào-trình-soạn-thảo-nút-Tra-popup-xác-nhận-tool-full-dạng-overlay.md), spec chung mục 8–9 |
| Bộ trích Word/regex theo cấu trúc | Đã có dàn ý 13 hạng mục, bảng dấu hiệu, ranh giới và 20 mẫu S01–S20. Quy tắc chi tiết/đáp án vẫn chờ Owner duyệt; chưa có spec triển khai engine mới. | [TASK-5](../../../backlog/tasks/task-5%20-%20Duyệt-bộ-quy-tắc-trích-Word-từ-mẫu-và-chốt-spec-triển-khai.md), [bảng quy tắc](../../review/sample-rules-20261005/README.md), [56 nhóm dấu hiệu](../../review/field-recognition-20261005.md), [tham khảo repo](../../review/external-rules/parent-summary.md) |
| Luồng DOCX đang chạy | Giữ spec hiện trạng để so với đích mới; không coi test xanh là đã đạt độ chính xác trên hồ sơ thật. | [DOCX](../../../docs/spec/notary_v2/input/docx-import.md), [Input](../../../docs/spec/notary_v2/input/README.md), [Stage](../../../docs/spec/notary_v2/stage.md) |
| Xuất Word, serial/diện tích và nút danh bạ | Có bằng chứng lỗi và quyết định Owner; chưa giao lại các task sửa đã rút. | [Báo cáo điều tra](../../review-plan-20261004/investigation-report.md), [trạng thái rút](../../review-plan-20261004/WITHDRAWN.md), [Word](../../../docs/spec/notary_v2/word-output.md) |
| Gom worktree | TASK-6; kiểm kê, bản sao và phạm vi đã nhận nằm trong bàn giao riêng. | [Bàn giao gom nhánh](../worktree-consolidation-20261005/README.md) |

## Regex: quyết định đã có và phần còn mở

Quyết định Owner được giữ tại [memlog](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/.memlog.md)
và TASK-5: xử lý từng file; bỏ CCV/người làm chứng; không tìm bù/xác nhận qua vùng ký
hay file khác; lời chứng độc lập có vùng chính riêng; dòng thiếu vẫn trả; kết quả
gốc chỉ đọc, chọn từng dòng vào Stage và sửa ở Stage. Một Người có nhiều bản ghi
giấy tờ; liên kết CMND 9 số/căn cước 12 số chỉ khi nguồn nói rõ. Mỗi thửa một tài
sản, serial tự do/không bắt buộc/có thể trùng, tổng diện tích độc lập. Ngân hàng
trích riêng, tên nguyên cụm; xe/tàu chưa hỗ trợ. Lớp cuối chỉ báo kết quả, không tự
học/chạy lại. "Sai format" ở trao đổi này nghĩa là loại văn bản chưa hỗ trợ.

Còn chờ duyệt: tên dẫn chiếu, khối lặp, cán bộ trong biên bản, nhiều văn bản/một
file, nhiều giá trị cho một ô Stage, chỗ lưu ngân hàng, UX nhiều giấy và cách đánh
giá cuối. Không tự giải quyết bằng gộp theo tên/số giấy hoặc bỏ dòng thiếu.

**Thứ tự tiếp tục TASK-5:** duyệt bảng loại/vùng/đầu-cuối → duyệt đáp án từng
vùng/trường → ghi các phần được duyệt vào spec và decisions → tạo task/plan
implementation riêng → agent khác implement → parent review cuối. Đây là lộ
trình duyệt, không phải plan giao code khi chưa có spec.

## Mẫu và giới hạn

[Manifest 20 mẫu](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/selected-samples.json)
giữ đường dẫn/mã băm. Kho nguồn: `D:\systemdocs\.agent\scratch\Dữ liệu mẫu word test`.
Git chỉ nhận bảng dấu hiệu và ghi chú không chứa giá trị giấy tờ cá nhân. Đáp án
đọc tay đầy đủ/inventory nguồn được giữ tại `.agents/local-only/notary-20261005/`
trong checkout đã gom; xem [chỉ mục đáp án](../../brainstorming/brainstorm-trich-van-ban-2026-10-04/sample-answers/answers-draft.md).
20 mẫu chưa được chấm bằng engine; khảo sát khả năng đọc toàn kho không phải tỷ
lệ trích đúng. Source tham khảo invoice2data/Dedoc vẫn là nghiên cứu, không phải
thư viện đã chọn hoặc dependency sản phẩm.
