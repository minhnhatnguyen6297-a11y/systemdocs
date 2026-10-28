# AGENTS.md — luật làm việc trong systemdocs

## Dùng BMAD

- Dùng workflow BMAD và customization của repo trong `_bmad/custom/`; đọc skill
  tương ứng trước khi dùng. Không dựng flow song song.
- Code tối giản; artifact và handoff ngắn gọn; trao đổi với user dễ hiểu - vibecoder.

## Nguồn chuẩn

- Đầu phiên, đọc [nền sản phẩm và khái niệm chung](_bmad-output/specs/README.md),
  rồi đọc [sổ tay sản phẩm theo màn hình](_bmad-output/specs/product-overview.md)
  để tìm UI và việc đang mở. Cập nhật sổ tay khi UI, trạng thái module hoặc việc
  đang mở đổi.

| Nội dung | Nơi lưu |
|---|---|
| Hành vi | `_bmad-output/specs/` |
| Issue/task, trạng thái và tiêu chí hoàn thành | `_bmad-output/backlog/` |
| Quyết định: đã chọn, lý do, phương án đã loại/chốt bỏ qua | `_bmad-output/decisions/` |
| Artifact workflow | `_bmad-output/` |
| Lịch sử | `_bmad-output/archive/` |
| Quan hệ code | `graphify-out/` |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `_bmad-output/decisions/` trong phiên hiện tại.
  Kế hoạch thực hiện, handoff và file tạm nằm trong `_bmad-output/tmp/`;
  issue/task cần giữ lâu dài nằm trong backlog. Ghi nhận issue chưa phải duyệt làm.
- Đọc `graphify-out/` trước khi dò code thủ công.

## Bất biến dữ liệu toàn hệ thống

- Mọi luồng nghiệp vụ xoay quanh ba đối tượng **Người, Tài sản, Hồ sơ**.
  Mọi chức năng đều sử dụng dữ liệu đã chuẩn hóa của ba đối tượng, không dựng bộ trường
  nghiệp vụ riêng cho từng màn hình/văn bản.
- Bộ trường canonical đã duyệt là chuẩn cố định cho lần triển khai:
  mọi input nghiệp vụ sau chuẩn hóa phải ánh xạ tường minh vào đúng trường;
  mọi output nghiệp vụ dùng đúng trường, kiểu, định dạng và nhóm đó.
  Không tạo dữ liệu nghiệp vụ mồ côi, không nhét dữ liệu khác nghĩa vào ghi chú,
  không tự đổi tên/thêm trường hoặc dùng alias chưa được duyệt.
- Tham chiếu [entities](contracts/entities.md),
  [contract theo module](contracts/README.md) và
  [quy tắc dữ liệu](_bmad-output/specs/shared/data-rules.md).
  Thiếu mapping hoặc cần mở rộng bộ trường: không tự xử lý phần phụ thuộc;
  ghi issue đúng loại để chốt nghiệp vụ/schema sau, tiếp tục các file/phần đã rõ.
  **Sau gate #41** không dừng cả lô vì gap từng file. Quy tắc này vẫn cho phép
  mở rộng được duyệt trong tương lai.
- File/chữ raw, bằng chứng và `source_refs` là provenance kỹ thuật phải giữ
  nguyên; không buộc raw đã có schema DB và không coi chúng là đối tượng nghiệp
  vụ mồ côi. Chuẩn hóa không tự xác nhận dữ liệu hay cho phép gộp Case/liên module.
- Owner 19/10/2026: **chủ đất thuộc Hồ sơ**, không phải thuộc tính cố định
  của Tài sản hoặc mặc định node `owner` Thừa kế; thông tin công chứng thuộc
  Hồ sơ, độc lập ngày tạo hồ sơ. Key/kiểu/cardinality còn phải chốt trong
  [#41](_bmad-output/backlog/story-upload-business-field-standardization.md),
  inventory toàn bộ trường bóc tách/form Upload xuyên module, không chỉ Notary.
- Owner làm rõ sau đó: **“người được gán chủ đất trong diagram”**.
  Lấy lựa chọn Chủ `ownPositions` của Diagram đã lưu (vị trí tài sản hiện có,
  không hidden/deleted), tên snapshot Stage theo `personId`; không đồng nhất
  slot `owner`/`owner_row_id`, không suy từ GCN/Bên A. Upload không có Diagram
  thì `chudat=null`. Quy tắc này thay phần chưa chọn nguồn chủ đất ở trên;
  slice metadata Case không khép toàn #41 hoặc mở gate mẫu.
- Không bóc/chuẩn hóa thông tin giao dịch (giá, cọc, thuê, vay, lãi, điều khoản
  thanh toán) hoặc thời hạn nghiệp vụ. **Giữ thời hạn sử dụng đất** đúng cụm
  `land_rows[].thoihan` và timeout kỹ thuật. Portal cần trường đã loại thì ghi
  xung đột để refine, không bịa/default hay tự quyết bước nhập tay mới.
  Không xóa raw/lịch sử hoặc sửa runtime trong lượt ghi tài liệu.
- Một Người nhiều giấy tờ **và** địa chỉ là
  [#42 riêng](_bmad-output/backlog/story-person-multiple-identities-addresses.md);
  model tương lai chưa chọn, không thêm đối tượng nghiệp vụ thứ tư hoặc tự
  ép ô đơn thành đa trị; không tự đặt #42 làm prerequisite quét mẫu.

## Context hồ sơ thử nghiệm

- Folder owner chuẩn bị là `D:\testcase`; đọc
  [README chung](file:///D:/testcase/README.md) trước khi làm việc với hồ sơ thử,
  rồi đọc context loại văn bản trong
  [README Notary](_bmad-output/specs/notary_v2/README.md#context-ho-so-thu).
- Hiện owner chỉ cho ghi định hướng/context/README; chờ chỉ dẫn tiếp trước khi
  tạo Word, corpus, chạy test/E2E hoặc tự triển khai. Bản nháp ở
  `testdata/notary-e2e/v1/` trước lệnh dừng không phải corpus được duyệt;
  không tự tiếp tục, chuyển hoặc xóa.
- **Gate trước mọi lượt quét/đọc mẫu thực mới, corpus hoặc vòng test/E2E theo
  mẫu:** chờ #41 được nghiệm thu đầy đủ chuẩn DB/contract, cutover consumer
  và proof luồng thật; có bảng mapping không đủ. Verification riêng của #41
  khi được giao dùng input tổng hợp/kiểm soát cô lập, không cần quét corpus
  owner để mở gate. Sau gate vẫn chờ được giao thực thi; không tắt Scan/Upload
  production hoặc coi docs là quyền triển khai.

## Quy tắc test bắt buộc, lưu dùng cho các phiên sau

- Khi được giao bắt đầu: **LLM đọc hàng loạt file mẫu thực → nhận diện cấu trúc
  trước → so sánh spec/code → điều chỉnh code có căn cứ → test lại → sai thì lặp lại
  cho tới khi xuất đủ, đúng thông tin hợp đồng**.
  Mục tiêu là xuất **đủ, đúng thông tin hợp đồng** theo Người–Tài sản–Hồ sơ,
  không chỉ tạo được file hoặc so byte/hash.
- Chốt nhãn/đáp án đối chiếu từ mẫu trước khi xem kết quả code; giữ raw và
  bằng chứng vị trí. Không lấy output parser làm đáp án để tự báo đạt.
- Loại đã biết nhưng cấu trúc chưa chốt: issue riêng theo loại văn bản.
  Văn bản lạ/không tự quyết được hoặc thiếu mapping: thêm nguồn, phần chưa rõ
  và bằng chứng vào [issue tổng hợp xem sau](_bmad-output/backlog/spike-unfamiliar-document-review-queue.md),
  dẫn issue theo loại nếu có; không đoán field/nghiệp vụ. **Sau gate #41**,
  phần chưa rõ từng file không dừng các file đã rõ.
- LLM có thể là agent đọc file cục bộ; chỉ dẫn này không cấp quyền gửi hồ sơ
  cho provider cloud chưa được duyệt hoặc dựng tích hợp LLM mới.
- Đây là quy trình cho lượt thực thi được giao sau. Lượt ghi định hướng hiện
  vẫn chỉ tài liệu, không tự đọc mẫu khách hàng/chạy lô/sửa code/test.
- Đây là quy tắc bền vững, không yêu cầu owner nhắc lại ở phiên sau. Đọc
  `D:\testcase\README.md` và [spec vòng test](_bmad-output/specs/shared/extraction-rules.md#sample-iteration)
  trước khi tạo fixture; không tự khôi phục kế hoạch mười ca cũ. Phần unresolved
  phải giữ pending, không tính pass hoặc âm thầm loại để báo toàn bộ đã đạt.
- Trước lô mới đọc [báo cáo ổn định](file:///D:/testcase/BAO_CAO_KHAO_SAT.md);
  sau **mỗi lô** cập nhật chính file đó, giữ kết quả cũ và điểm tiếp tục.
  Không chỉ lưu ở tmp hoặc ghi đè mất lịch sử khảo sát.
- Chỉ được gọi chuẩn trường “đã rõ” sau audit tên/kiểu/format/nhóm có thứ tự/
  đích DB-wire/ràng buộc và nguồn thẩm quyền cho Người–Tài sản–Hồ sơ; tách
  defined, Draft, ambiguous/unmapped, không suy mọi biến thể đã rõ từ code/key.
  Báo cáo là audit hiện tại, không thay contract. Coverage file-body chưa đọc là 0,
  không được biến kiểm danh mục/metadata thành khảo sát nội dung.
- Raw/PII giữ owner-local theo quyền hiện có. Issue repo chỉ dẫn nguồn an toàn
  và bằng chứng cấu trúc đã che dữ liệu cá nhân; không chép raw Word, CCCD hoặc
  thông tin khách vào Git/log rộng. Không tạo logging/telemetry mới.

## Viết spec

- Mỗi module một file chính; Soạn thảo có thêm quy tắc sơ đồ và mẫu Word.
  Viết theo luồng người dùng, ngắn gọn nhưng đủ mục đích, hành vi, giới hạn và ngoại lệ.
- Spec ghi trực tiếp quyết định đang áp dụng, kể cả trùng decision. Không dùng link
  thay cho quy tắc cần hiểu; link chỉ tra thêm. Decision giữ lý do và phương án bỏ.
- Không tách mỗi feature nhỏ thành file mới. Chỉ mở tài liệu chuyên sâu khi cần;
  không nạp archive mặc định và không nâng Draft thành đã duyệt khi gom tài liệu.
- Khi quyết định đổi, cập nhật spec và decision cùng phiên; tiến độ để trong backlog.

## Trình bày

- Chỉ tạo file HTML trong `_bmad-output/tmp/` cho plan, spec, brainstorming hoặc
  minh họa cấu trúc; chat, trạng thái, phân tích, review và báo cáo thường trả lời
  trong hội thoại.
- HTML plan/spec là lớp trình bày; Markdown và artifact BMAD vẫn là nguồn chuẩn.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

## Luật cho coder agent

- **Review bắt buộc trước khi báo xong**: chạy Superpowers `requesting-code-review`
  hoặc agent Reviewer trên diff; xử lý góp ý hoặc ghi lý do.
- Không dùng `git stash` (dùng commit WIP hoặc worktree riêng). Không code trên `main`.
- **Tìm trên GitHub trước** khi tự viết công cụ/pattern; ghi URL đã tham khảo.
- Quyết định nhỏ: tự quyết và ghi lại. Thay đổi kiến trúc, schema/contract hoặc
  dependency: dừng, báo các phương án + đánh đổi, chờ owner.
- Báo cáo phải có lệnh đã chạy + output (kể cả lỗi, bước bị bỏ qua), tách đã kiểm
  chứng / chưa kiểm chứng, và nêu giả định.
- Không skip test để cho xanh: lỗi đã biết ghi vào `tools/ci/known-failures-*.txt`
  kèm issue ref. Chuẩn "xong": `docs/definition-of-done.md`.
