# SPEC — notary_v2

Cập nhật: 17/09/2026. Chủ dự án quyết định nghiệp vụ; agent tổ chức tài liệu.
Đây là **SOT nghiệp vụ duy nhất của module**, gồm file này và các chương được
chỉ định ở §1. Các chương không phải nguồn có thẩm quyền độc lập.

Các quyết định mới trong phiên ngày 17/09/2026 là **yêu cầu đích đã chốt**, không
phải tuyên bố code đã đáp ứng. Những quy tắc tính thừa kế còn nháp vẫn chưa được duyệt.

## 1. Sửa yêu cầu ở đúng một nơi

| Chủ đề cần thay đổi | File duy nhất cần sửa nghiệp vụ |
|---|---|
| Phạm vi module; Hồ sơ, Người, Tài sản; nguyên tắc và trạng thái tổng thể | [SPEC.md](SPEC.md) §2–§7 |
| Nguồn nhập, cửa sổ OCR, phân loại và ghép mặt giấy tờ | [Tiếp nhận dữ liệu](platform/document-intake/spec.md) |
| Stage, Cập nhật toàn cục, Pool, đồng bộ và ảnh hưởng đến Diagram | [Stage / Pool / Diagram](platform/case-workspace/contract.md) |
| Thuật toán, tình huống và quy tắc chia thừa kế | [Dự thảo thừa kế](domains/inheritance/spec.md) — CHƯA DUYỆT |
| Bố trí, thao tác hiển thị riêng của sơ đồ | [Dự thảo UX Diagram](domains/inheritance/ux.md) — CHƯA DUYỆT; không đặt lại quy tắc Stage |
| Mẫu, xem trước, xuất Word và ý nghĩa nhóm dữ liệu trong văn bản | [Xuất Word](domains/inheritance/word-export.md) |
| Zalo như một nguồn input: kết nối, chọn nguồn, lô ảnh, đầu ra | [Zalo input](platform/zalo-document-inbox/spec.md) |
| Soát sai lệch văn bản độc lập | [Fast text audit](platform/fast-text-audit/technical.md) — phần nghiệp vụ; kỹ thuật là tham khảo |

Quy tắc cập nhật:
1. Sửa chương sở hữu chủ đề; không lập bản SPEC có ngày mới để cạnh tranh với nó.
2. Nếu yêu cầu đụng nhiều chủ đề, mỗi quy tắc chỉ viết ở chương sở hữu và dẫn
   liên kết từ chương sử dụng. Ví dụ Zalo dẫn quy tắc duyệt ở Stage, không tự đặt nút duyệt khác.
3. Ghi riêng **trạng thái duyệt** và **trạng thái code**; giữ câu hỏi mở tại chương
   sở hữu. Không biến nội dung nháp/lịch sử thành quyết định đã duyệt.
4. Cập nhật bảng này khi thêm/đổi chương; cập nhật gap ở §7 nếu hiện trạng thay đổi.
   Khi đổi đường dẫn, sửa README, AGENTS và liên kết tới file cũ.
5. Tài liệu technical, research, kế hoạch và bản cũ chỉ giải thích hoặc lưu bằng
   chứng; không sửa chúng để thay nghiệp vụ. Không suy quyền duyệt từ ngày cập nhật mới hơn.
6. Nếu chương còn lệch file này hoặc quyết định người dùng: báo phần lệch, không
   tự chọn một nguồn rồi triển khai. Đổi tài liệu không cấp quyền đổi code/schema/contract.

## 2. Module giúp làm việc gì?

Giảm nhập lại dữ liệu giấy tờ, tập hợp người và tài sản vào hồ sơ, hỗ trợ nghiệp
vụ và tạo văn bản. Giao diện hướng tới ba nhóm đơn giản: **Hồ sơ — Người — Tài sản**.

Hồ sơ là trung tâm. Input, Stage, Pool và Diagram là các vùng/bước làm việc,
không phải bốn module ngang hàng với Hồ sơ, Người, Tài sản.

Hiện code tập trung vào hồ sơ thừa kế. Giữ khả năng thêm loại hồ sơ; chuyển
nhượng và các loại khác phát triển sau, không coi là nghiệp vụ đã hoàn chỉnh.
Không xây framework hoặc thay schema chỉ để chuẩn bị cho mọi loại hồ sơ tương lai.

## 3. Hồ sơ

Hồ sơ trả lời: **Người nào làm gì với tài sản nào?**
Ví dụ định hướng: A, B, C, D ký hợp đồng chuyển nhượng tài sản X.

- Có loại hồ sơ, người tham gia, vai trò/quan hệ theo loại việc, tài sản và văn bản.
- Một hồ sơ có thể liên quan nhiều người và nhiều tài sản.
- Hồ sơ liên kết tới bản ghi Người/Tài sản; không đồng nhất hồ sơ với một người,
  một số CCCD, một sổ đỏ hay một thửa đất.
- Thao tác tạo, mở, sửa, lưu hồ sơ, khóa/mở khóa và xóa hồ sơ phải có phạm vi rõ.
  Xóa hồ sơ không được hiểu ngầm là xóa người/tài sản trong kho dùng chung.
- Phân biệt Cập nhật dữ liệu Stage, lưu quan hệ Diagram và lưu hồ sơ. Hai hành
  động sau không được dùng làm đường cập nhật riêng lẻ để lách quy tắc Stage.
- Trạng thái code hiện có là hồ sơ thừa kế nháp/khóa; chưa có vòng đời chung
  cho mọi loại hồ sơ. Không đặt thêm trạng thái hoàn tất nghiệp vụ trong lần dọn docs này.

## 4. Người

- Lưu thông tin nhận diện của một người: họ tên, giới tính, ngày sinh/ngày chết,
  giấy tờ, ngày/nơi cấp và địa chỉ theo khả năng của đầu vào.
- Có thể nhập mới hoặc tìm/chọn người đã có.
- Thông tin cá nhân khác với vai trò của người đó trong từng hồ sơ.
- Khóa liên kết ổn định là mã người, không phải tên, số CCCD hay vị trí hàng.
  Đổi tên/CCCD không được làm mất gán của người trên sơ đồ.
- Dữ liệu nháp và bản đã cập nhật tuân theo chương Stage. Quan hệ, Chủ đất/Nhận
  thuộc Diagram; không sửa ngược thông tin cá nhân.
- Không tự gộp người chỉ vì thông tin OCR giống nhau. Cách xử lý xung đột
  bản ghi trùng trong kho và sửa người dùng ở nhiều hồ sơ vẫn cần chốt (§7).

Mô tả trường mong muốn không chứng minh đã có cột lưu tương ứng. Ví dụ code
hiện tính `noi_cap` qua thuộc tính của Customer, không lưu như trường nhập độc lập
([models.py:46](../models.py#L46)).

## 5. Tài sản và giấy chứng nhận

**Quyết định chủ dự án ngày 17/09/2026:**

- Mỗi sổ đỏ/giấy chứng nhận có thể chứa nhiều tài sản.
- Mỗi tài sản được lưu thành bản ghi riêng. Một hồ sơ có thể có nhiều tài sản.
- Các tài sản có thể cùng sổ hoặc khác sổ; có thể trùng số serial, chủ sử dụng,
  địa chỉ và các thông tin chung. Trùng các thông tin này không phải lý do gộp
  hoặc từ chối lưu các tài sản khác nhau.
- **Stage hiển thị mỗi tài sản một cột**, không phải mỗi sổ một cột.
- Trong bài toán đất đang mô tả, cần phân biệt thửa đất với các dòng loại đất/
  diện tích thuộc cùng tài sản; không tự biến mỗi dòng loại đất thành một tài sản.
- Thông tin sổ/ảnh nguồn phải giúp nhận ra các tài sản cùng giấy chứng nhận;
  cách tổ chức bảng và liên kết cụ thể cần thiết kế triển khai riêng.

Chưa chốt khóa chống trùng cho cùng một tài sản qua nhiều lần nhập, biến động/
cấp lại giấy chứng nhận, hoặc cập nhật tài sản được dùng ở nhiều hồ sơ.
Cho phép tài sản khác nhau trùng thông tin không có nghĩa tự nhân đôi tài sản
khi nhận lại cùng một đầu vào.

## 6. Luồng sử dụng và ranh giới

1. Chọn nguồn: file, Excel, nhập tay, dữ liệu đã có hoặc Zalo.
2. Với giấy tờ cần OCR: xem ảnh và kết quả tại cửa sổ OCR; xử lý riêng từng loại.
3. Đưa dữ liệu về các vùng Stage phù hợp; người dùng sửa tại đây.
4. Bấm Cập nhật toàn cục để duyệt Người, Tài sản và giấy tờ khác đang có trong
   vùng làm việc. Chương Stage quy định kiểm tra, lưu và xử lý lỗi.
5. Pool/Diagram sử dụng dữ liệu đã cập nhật. Thừa kế có quan hệ và tính toán riêng.
6. Xem trước và xuất Word từ dữ liệu đã duyệt; không nhập lại người nhận ở màn xuất.

Ranh giới giữ nguyên:
- Stage là nguồn chuẩn của dữ liệu nhập đã duyệt; Diagram giữ quan hệ và quyết
  định nghiệp vụ. “Một SOT dữ liệu” không có nghĩa cấm Diagram giữ dữ liệu riêng.
- Zalo là nguồn input, không có quy trình sửa/duyệt OCR riêng; xem chương Zalo.
- Quy tắc tính thừa kế chưa duyệt không được hợp thức hóa qua sơ đồ hoặc mẫu Word.
- Soát văn bản là công cụ độc lập, không tự chạy sau mọi lần xuất Word.
- QR giấy tờ và OCR giấy tờ khác để sau. QR đăng nhập Zalo là việc khác.
- Cửa sổ OCR chung là yêu cầu có điều kiện; chưa đủ bằng chứng phân loại tự động
  thì chưa chuyển UI. Chi tiết gate tại chương tiếp nhận.
- `shell/` gọi engine thật qua adapter đã duyệt; không có luồng tự động
  `notary_v2 → upload_lab`. Thay đổi liên quan shell cần task đánh giá tương thích riêng.
- Chưa có DB chung toàn hệ thống; đích đến vẫn là một hệ thống dùng chung DB.
- Công nghệ: [TECH_STACK.md](../../TECH_STACK.md). Quyền riêng tư Zalo:
  [OPEN_DECISIONS.md B2](../../OPEN_DECISIONS.md#b2--ranh-giới-đọc-zalo-đã-chốt).
  Không thêm provider, mở lại local OCR hay tạo contract tích hợp trong task tài liệu.

## 7. Yêu cầu đích so với code và câu hỏi còn mở

Bằng chứng là đọc source tại worktree ngày 17/09/2026, **không phải nghiệm thu UI**.
Các đường dẫn/số dòng dưới đây là mốc đối chiếu, phải kiểm tra lại khi code đổi.

| Chủ đề | Hiện trạng/bằng chứng | Yêu cầu hoặc giới hạn |
|---|---|---|
| Nhiều loại hồ sơ | [models.py:83](../models.py#L83) dùng InheritanceCase | Các loại khác là hướng phát triển |
| Nhiều tài sản một hồ sơ | [models.py:114](../models.py#L114) có bảng liên kết | Không chứng minh gán người nhận riêng từng tài sản |
| Trùng serial | [models.py:62](../models.py#L62) unique; [properties.py:85](../routers/properties.py#L85) chặn trùng | Chưa đáp ứng §5 |
| Stage tài sản một cột/tài sản | [form.html:8107](../frontend/templates/cases/form.html#L8107) có handler thêm tài sản riêng | Chưa xác minh có Stage tài sản đúng yêu cầu |
| OCR chỉ xem | [form.html:10374](../frontend/templates/cases/form.html#L10374) tạo ô sửa OCR | Chưa đáp ứng chương tiếp nhận |
| Đóng OCR giữ cache | [form.html:4865](../frontend/templates/cases/form.html#L4865) xóa tạm sổ đỏ khi đóng | Chưa đáp ứng chương tiếp nhận |
| Cập nhật toàn cục | [form.html:11974](../frontend/templates/cases/form.html#L11974) ghi từng người; [form.html:12181](../frontend/templates/cases/form.html#L12181) loại hàng lỗi khỏi snapshot | Chưa có bằng chứng commit nguyên tử Người + Tài sản + giấy tờ |
| Stage → Diagram | [cases.py:801](../routers/cases.py#L801) và [ReactFlowApp.jsx:2180](../frontend/static/ReactFlowApp.jsx#L2180) có xử lý đồng bộ/dọn tham chiếu | User báo chuỗi thao tác còn gãy; chưa tái hiện/nghiệm thu trong task này |
| Trùng người | [customers.py:439](../routers/customers.py#L439) có tự cập nhật theo CCCD; [models.py:17](../models.py#L17) unique | Còn lệch yêu cầu không tự gộp; không tự bỏ ràng buộc DB |
| Zalo về Stage | Luồng duyệt modal được mô tả ở bản Zalo cũ; source tại [zalo_inbox.py](../routers/zalo_inbox.py) | Định hướng mới đã chốt; chưa triển khai trong task này |
| Thừa kế | Hai bản draft ngày 22/08 và 24/08 vẫn chưa được duyệt toàn bộ | Không tuyên bố luật tính đã hoàn chỉnh |
| Word | [word-export.md](domains/inheritance/word-export.md) giới hạn V1 | Thay Stage không tự sửa file Word đã tải; cần xuất lại |

Câu hỏi mở không chặn việc ghi nhận các quyết định đã chốt:
- Phạm vi sửa Người/Tài sản dùng chung nhiều hồ sơ; khóa chống trùng của từng loại.
- Thời hạn và khả năng khôi phục nháp sau reload/đóng app; không đánh đồng với đóng modal.
- Trường bắt buộc/validation cho Stage Tài sản và giấy tờ khác; chưa tự đặt schema.
- Tiêu chí số liệu và bộ mẫu để duyệt engine phân loại tự động đủ tốt.
- Zalo xuất dữ liệu độc lập dùng Stage trong ngữ cảnh nào; chưa ép tạo Hồ sơ.
- Workflow cũ nói nút Nhận theo tài sản hiện chọn, nhưng Word V1 áp dụng cùng
  nhóm người nhận cho mọi tài sản trong văn bản. Cần chốt phạm vi gán trước khi
  triển khai per-asset, không ngầm mở rộng quy tắc Word V1.
- Quy tắc thừa kế còn nháp, cảnh báo hay chặn lưu/xuất trong từng tình huống.

Các câu hỏi ở [OPEN_DECISIONS.md](../../OPEN_DECISIONS.md) cấp hệ thống vẫn giữ
thẩm quyền riêng; bảng này không tự chốt thay chúng.
