# Nền sản phẩm

**Cập nhật:** 21/10/2026. Đọc đầu phiên để hiểu sản phẩm; sau đó đọc sổ tay và spec module đang làm. Quy tắc dưới đây mô tả điều cần có, không chứng minh code đã hoàn thành.

## 1. Người dùng và công việc

Sản phẩm dành cho nhân viên, chuyên viên văn phòng công chứng. Công việc xoay quanh soạn văn bản, số hóa văn bản đã soạn và theo dõi công việc tiếp tục phát sinh quanh Người, Tài sản và Hồ sơ.

Máy giảm việc đánh máy lại: lấy tối đa thông tin có căn cứ từ nguồn, đặt vào đúng trường chuẩn để người dùng kiểm tra, sửa và sử dụng. Không đoán dữ liệu cho đủ ô. Ba module hỗ trợ ba nhóm việc, không mặc định tự chuyển hồ sơ hoặc dùng chung một mã hồ sơ.

## 2. Soạn thảo — notary_v2

Soạn hồ sơ là chức năng trung tâm. Người dùng nhận giấy tờ/file/chữ → kiểm tra thông tin Người/Tài sản → bổ sung vai trò, quan hệ khi cần → xuất Word theo mẫu.

| Thành phần | Vai trò |
|---|---|
| Danh sách hồ sơ | Tìm và mở hồ sơ đang/đã soạn. Đây là tên mong muốn thay Tổng quan; nhãn, tìm kiếm và bộ lọc còn cần chốt chi tiết. |
| Input | Đọc ảnh, PDF, Word, Excel hoặc chữ thành gợi ý có nguồn. Phạm vi từng định dạng theo spec module, không hứa đọc mọi file. |
| Stage | Kiểm tra/sửa thông tin Người và Tài sản. Bấm Cập nhật mới lưu và áp dụng cho các phần sử dụng. |
| Pool | Những người đã lưu trong Stage nhưng chưa được gán lên Diagram đang xem; không phải kho riêng. |
| Diagram | Gán vai trò và quan hệ bằng kéo thả/chọn trong thẻ; có Hai bên và Thừa kế. Không sửa thông tin Người/Tài sản thay Stage. |
| Xuất Word | Điền dữ liệu đã lưu vào placeholder — vị trí đánh dấu trong mẫu. |

**Triết lý: điền dần, không ép hoàn tất mọi bước.** Có dữ liệu nào thì điền trường đó; trường hợp lệ chưa có dữ liệu để trống. Một văn bản chỉ cần Stage không phải dựng sơ đồ không cần thiết. Chỉ chặn hoặc hỏi xác nhận khi có nguy cơ cụ thể như dùng dữ liệu chưa cập nhật, làm gãy quan hệ hoặc không thể tạo file đúng. Điều kiện chặn hiện hành còn phải đồng bộ theo định hướng này; không coi việc sửa docs là đã sửa chương trình.

Tab Word riêng dự kiến giúp nhập văn bản, đề xuất placeholder, tải về sửa rồi nhập lại để lưu mẫu lâu dài. Tab này chưa có spec chi tiết/chưa triển khai; khác nút Xuất Word đang nằm trong Soạn hồ sơ.

## 3. Upload — upload_lab

Đọc kho Word trên máy, đối chiếu với dữ liệu chính thức từ website, chọn hồ sơ còn thiếu, bóc trường và điền sẵn biểu mẫu trên trình duyệt. Người dùng tự kiểm tra và quyết định có Lưu; dữ liệu đã được website ghi nhận chính thức là nguồn sự thật. App không suy hoặc theo dõi kết quả Lưu từ tín hiệu browser cục bộ.

Số công chứng được đối chiếu theo năm và nguồn website; phải báo số thiếu, lỗi và trùng. Mỗi website có bộ xử lý riêng cho đăng nhập, lấy sổ, đối chiếu đầu vào và điền form.

Owner đánh giá module tương đối hoàn thiện; hướng tiếp theo chủ yếu là chất lượng regex và website mới. Đánh giá này không thay bằng chứng kiểm chức năng.

## 4. NotaryOffice — theo dõi công việc

Ngoài soạn văn bản còn có chuỗi việc dài như nộp hồ sơ chuyển nhượng, chỉnh lý giấy chứng nhận, đo đạc, cập nhật địa chỉ. Module giúp trả lời “Hồ sơ đang ở đâu, chờ việc gì?” bằng dấu vết công việc thay vì chỉ dựa vào trí nhớ.

Hướng chính: thay đổi nội dung Word trong phạm vi được phép → bóc Người/Tài sản/Hồ sơ liên quan → thẻ đề xuất ngắn → nhân viên xác nhận/sửa → dòng thời gian. Dấu vết sửa Word chưa chứng minh một thủ tục đã hoàn tất. Đây là công cụ hỗ trợ, không áp quy trình quản lý doanh nghiệp cứng nhắc. Thiết kế chi tiết còn Draft, chưa có runtime đã nghiệm thu.

## 5. Zalo và công nghệ chung

Zalo ban đầu được định hướng làm nguồn Input. Hiện nghiên cứu riêng do vấn đề pháp lý cần làm rõ; không tự nối vào hệ thống. Các đề xuất tích hợp cũ không phải quyền triển khai.

OCR chuyển ảnh thành chữ: hiện dùng Qwen-VL-OCR qua đường cloud đã duyệt; OCR local là hướng dài hạn. Regex bóc chữ thành trường. Đọc Word tùy luồng: IFilter cho DOC; python-docx cho Upload DOCX; Document Intake đọc XML bằng lxml để giữ vị trí. Playwright hỗ trợ điền trình duyệt. SQLite theo module là hiện trạng tài liệu; database nghiệp vụ chung là đích, engine chung và cách chuyển dữ liệu chưa chốt.

Electron là vỏ ứng dụng; Python/FastAPI xử lý nghiệp vụ. Module giữ quyền ghi dữ liệu của mình; dùng chung ứng dụng không cho phép tự nối hoặc gộp dữ liệu.

## 6. Khái niệm và nguyên tắc

- Hồ sơ là đơn vị công việc trong từng module. CCCD, GCN, cặp thửa/tờ, số công chứng là bằng chứng đối chiếu, không tự trở thành mã hồ sơ chung.
- **Policy bền vững cho mọi task — owner 21/10/2026:** engine xử lý dữ liệu,
  không quyết định thay người dùng; sản phẩm pháp lý để người dùng chịu trách
  nhiệm ở bước quan trọng. Không tự thêm code/quy tắc chặn luồng hoặc đổi hành
  vi chưa báo và được owner duyệt. UX chưa rõ ghi issue để owner chọn, không
  biến thành gate mới. Ưu tiên thiết kế tối thiểu: kết quả 80% tốt hơn 90%
  cộng 10 thao tác; không có nghĩa chấp nhận dữ liệu sai hay xóa provenance.
  Chưa kiểm kê/xác minh các blocker hiện có; không tự gỡ safeguard hoặc claim
  đã audit. Không dùng policy này để tự bỏ kiểm tra wire/security/FK/atomicity.
- **Điểm neo — owner 21/10 mới nhất, thiết kế chưa triển khai:** Người tự dùng
  cùng ID khi **tên + số giấy tờ đồng thời giống nhau**; ngày cấp/địa chỉ khác
  vẫn cùng ID. Đổi tên hoặc số chấp nhận ID khác. Tài sản gom theo **serial**
  nguyên văn. Người sống/chết cùng bảng. Tìm Người để xem các Hồ sơ đã làm;
  lấy dữ liệu vào Hồ sơ mới mặc định bộ mới nhất, không chọn liên kết/phiên bản.
  Policy gợi ý CCCD/user chọn/bỏ qua tạo ID mới ở #44 đã bị thay thế; không
  khôi phục CCCD UNIQUE/chặn luồng. **Owner 22/10:** tên đối chiếu không phân
  biệt dấu/hoa-thường, giữ tên gốc. Nguồn là Hồ sơ done lưu gần nhất, không
  draft. ID trùng cũ giữ nguyên, lấy bộ cuối; cùng serial dù khác thửa vẫn
  cùng ID. Thiếu neo không gom; Nhân bản toàn bộ. Lifecycle ID khi nhập dở
  và cấu trúc bảng còn rà soát, chưa implemented.
  [Quyết định](../decisions/decision-owner-entity-anchors-case-snapshots-20261021.md).
- **Snapshot — owner 21/10:** record nghiệp vụ là Hồ sơ; mỗi Hồ sơ một snapshot
  hiện hành. Lưu lại thay snapshot đó, không lưu lịch sử từng ô/lần lưu. Các
  bộ thông tin khác nhau của cùng ID giữ qua những Hồ sơ liên quan. Hồ sơ cũ
  chỉ user sửa thủ công, không tự đổi theo dữ liệu mới nơi khác. Nháp được lưu
  DB dù nhập thiếu, nhãn Nháp rõ. Owner 22/10 yêu cầu Lưu hồ sơ ghi Diagram và
  draft→done, đang dừng trước code để rà soát hai bước Cập nhật/Lưu hồ sơ;
  cách tính từng báo cáo chưa chốt.
  Raw/nguồn/history kỹ thuật đã có vẫn giữ; #41 OPEN/gate mẫu ĐÓNG, #42 độc lập.
- **Địa chỉ cũ–mới — owner kết phiên 21/10:** tạm giữ cách hiện tại; mô hình
  mới chưa chốt. Đề xuất danh mục/quan hệ chuyển đổi và mã tham chiếu từ các
  trường địa chỉ chưa duyệt, không đổi cấu trúc/hành vi theo đề xuất đó.
- **Toàn bộ luồng nghiệp vụ xoay quanh Người, Tài sản, Hồ sơ** (owner 19/10/2026). Chức năng dùng dữ liệu chuẩn hóa của ba đối tượng; mọi input nghiệp vụ sau chuẩn hóa ánh xạ vào bộ trường canonical đã duyệt, mọi output nghiệp vụ dùng đúng bộ trường đó. Không tạo dữ liệu mồ côi hoặc nhét khác nghĩa vào ghi chú; ngoại lệ hẹp là cụm trường phụ website theo hướng owner cho phép có điều kiện, không phải ghi chú chung; raw capture chỉ là provenance, không thay trường nghiệp vụ. Thiếu mapping/cần trường mới thì chốt nghiệp vụ/schema trước, không tự mở rộng. Raw/bằng chứng/`source_refs` là provenance kỹ thuật, không buộc có schema DB và không tự tạo quyền gộp Case hay tích hợp liên module.
- **Owner 19/10/2026 — bổ sung trường Hồ sơ:** chủ đất là trường **Hồ sơ**,
  không là thuộc tính sở hữu cố định của Tài sản, không mặc định node `owner`
  Thừa kế. Thông tin công chứng thuộc Hồ sơ, độc lập ngày tạo hồ sơ; inventory
  phải đủ số/ngày công chứng, công chứng viên, thư ký và mọi trường Upload.
  Không bóc/chuẩn hóa giá/cọc/thuê/vay/lãi/điều khoản thanh toán hoặc thời hạn
  nghiệp vụ; vẫn giữ thời hạn sử dụng đất đúng cụm và timeout kỹ thuật. Portal
  cần trường bị loại thì ghi xung đột để refine, không bịa/default hoặc tự chọn
  bước nhập tay. Key/kiểu/cardinality/DB-wire-output chưa được chọn chỉ từ định
  hướng này. [#41](../backlog/story-upload-business-field-standardization.md)
  chuẩn hóa toàn bộ trường Upload xuyên module, có thể mở rộng canonical Hồ sơ
  có căn cứ và được duyệt, không xóa trường cần thiết cho vừa schema Notary.
  [#42](../backlog/story-person-multiple-identities-addresses.md) riêng cho một
  Người nhiều giấy tờ và địa chỉ; model tương lai chưa chọn, không tự là gate.
- **Làm rõ tiếp theo của owner 19/10:** chủ đất là **“người được gán chủ đất
  trong diagram”**. `chudat` lấy lựa chọn Chủ `ownPositions` đã lưu, trỏ tài
  sản hiện có, không hidden/deleted; tên snapshot Stage theo ID, không đồng
  nhất slot owner/người chết. Upload không có Diagram là null. Metadata Case
  BUILT theo entities §9.4, verification cô lập đạt và Quick code sạch sau
  sửa selected-only prepare; fix được Quick độc lập chấp nhận, tài liệu cuối
  hoàn tất. Không thay phạm vi Person/Asset/parties: **toàn #41 chưa xong,
  gate mẫu ĐÓNG**.
- **Gate hiện hành trước quy trình theo mẫu:** mọi lượt khảo sát/quét mẫu thực
  mới, corpus và vòng E2E theo mẫu phải chờ **#41 được nghiệm thu đầy đủ** chuẩn
  DB/contract, cutover và proof consumer thật, không chỉ bảng mapping. Proof riêng
  #41 có thể dùng input tổng hợp/kiểm soát cô lập khi được giao, không cần khảo
  sát corpus owner để đóng gate. Sau gate và khi được giao mới chạy **LLM đọc
  mẫu → nhận diện cấu trúc → so spec/code → sửa có căn cứ → test/lặp** đến đủ đúng.
  Khi đó văn bản lạ/gap từng file giữ pending qua #39, tiếp tục file đã rõ.
  Không tắt Scan/Upload production hoặc cấp quyền cloud mới. Docs-only là mốc
  ghi nhận trước; owner đã giao runtime Nam Định đã chốt, gồm BANKMODE bên dưới.
  [Quyết định](../decisions/decision-owner-upload-field-standardization-20261019.md).
- **Người chết — owner 21/10/2026 đã chốt sáu câu, đã giao runtime hẹp:** một `dia_chi`
  dùng chung Nơi chết/cư trú cuối; `Giấy chứng tử (bản sao)` quy về
  `Giấy chứng tử`, vẫn đúng ba loại cùng `Trích lục khai tử` và
  `Trích lục khai tử (bản sao)`. Cơ quan giữ xã/phường/thị trấn tại ngày
  cấp chính giấy, không ép xã hoặc suy lịch sử chưa xác nhận. Không đề xuất
  bổ sung/tự ghép giữa văn bản; không gợi ý từ Đơn xin xác nhận. Thiếu ngày
  chết chỉ là không có thông tin, có trường hợp lệ nào điền trường đó,
  không chặn Người/tự coi còn sống/tạo field mới. Không đổi logic câu Word.
  Luật nội dung giấy tờ này không cấm gom ID theo điểm neo ở trên, cũng không
  cho phép tự mượn trường thiếu giữa văn bản hoặc đổi Hồ sơ đã lưu ở nơi khác.
  Owner tiếp tục “trien khai”: workstream Người chết **đã BUILT bounded**,
  actual proof implementer-run đạt fresh+migrated DB/Word và DOM legacy giới
  hạn; #41 vẫn OPEN/gate chung ĐÓNG, không mở #42/A04/quan hệ hoặc lô mẫu.
- Bản nháp Stage/Diagram là sửa chưa lưu. Draft Case của Office là ứng viên chưa xác nhận. Trạng thái hồ sơ `draft` phục vụ quy tắc quản lý hồ sơ. Ba nghĩa không thay thế nhau.
- Nguồn gốc → chữ đọc được → dữ liệu chuẩn hóa → gợi ý suy ra nếu cần → người có thẩm quyền xác nhận. Không phải dữ liệu nào cũng cần suy luận.
- Giữ nguồn và giá trị gốc; không sửa raw để che lỗi. Máy không tự nâng OCR/AI thành dữ liệu đã xác nhận.
- Đầu ra nghiệp vụ phải theo trường, kiểu, định dạng, cách nhóm và đích lưu đã chốt trong DB/contract. Raw không bắt buộc mang schema DB. Không sinh trường mồ côi hoặc nhét sai nghĩa vào ghi chú. Trường mới phải được chốt trước; ngoại lệ hẹp là cụm trường phụ website theo hướng owner cho phép có điều kiện, không phải ghi chú chung; raw capture chỉ là provenance.
- **Owner 20/10/2026 — pháp nhân, cụm trường phụ và quan hệ:** pháp nhân **không đưa vào Người**; policy nhập tay chung có ngoại lệ ngân hàng thế chấp app tự lấy dưới đây. Bảng riêng tương lai chưa duyệt schema/build. Cụm trường phụ theo website/ô cụ thể, phức tạp, không lặp lại, ưu tiên canonical đã có và giữ provenance; không generic bag/`ghiChú`. Quan hệ nhiều người/nhiều tài sản chưa chọn model/cardinality. [Dữ liệu chung](shared/data-rules.md) · [Quyết định](../decisions/decision-owner-upload-field-standardization-20261019.md).
- **Đáp án #43 — phạm vi requester Nam Định/Upload:** lấy cá nhân sống A/B/
  đại diện ủy quyền, không người chết/CCV/nhân viên trong output đó; không xóa
  Person chết, Stage/Hồ sơ thừa kế/raw/snapshot/lịch sử. Ngân hàng thế chấp
  hiện cả cụm là ngoại lệ output, không Person; **BANKMODE đã chốt “app tự lấy”**:
  chỉ thế chấp, app lấy toàn cụm ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/
  ủy quyền có nguồn tại vị trí nguồn, không lặp đại diện đã trong cụm.
  Cá nhân khác vẫn dữ kiện chuẩn. `web_form.nguoi_yeu_cau` → payload JSON →
  queue → editor là persistence projection hợp lệ, không key/schema canonical mới.
  Ủy quyền A=ủy quyền/B=được ủy quyền; một bên không gán; nguồn trái nhau giữ
  conflict/xác nhận phần nhóm, không tự winner. Q1/Q2/BANKMODE đủ đáp án,
  #43 phân tích done/bàn giao #41; #41 mở/gate mẫu ĐÓNG, bounded proof/fresh review CLEAN.
  Requester không cần tag A/B đã gán; cá nhân sống một bên/đại diện ủy quyền
  vẫn được đưa vào khi nhóm không gán hoặc conflict.
- Ngày nhập/hiển thị giữ đúng độ đầy đủ: năm riêng vẫn là năm. Ngày quy ước chỉ dùng trong tính toán, không ghi đè thành dữ kiện đã biết.
- Máy hỗ trợ thao tác; người dùng kiểm tra và chịu trách nhiệm xác nhận. Không tự động hóa phán quyết pháp lý.
- Thiết kế gọn, tối ưu xử lý; không tự thêm chức năng, cơ chế dự phòng hoặc bộ công cụ kiểm thử ngoài phạm vi được phép.
- Rule regex văn bản và rule upload theo từng website do developer quản lý, có phân biệt phiên bản để nhận biết (owner 16/10/2026; [decision](../decisions/decision-owner-regex-rule-developer-only-20261016.md)); người dùng sản phẩm không có chức năng thử, công bố, chọn phiên bản hoặc quay lui rule.
- Không ép chuyên viên đổi thói quen cần cho nghiệp vụ. Không quay màn hình, ghi phím hoặc chấm công bằng dấu vết hồ sơ.
- Dữ liệu ở lại văn phòng; chỉ gọi dịch vụ ngoài tại điểm đã duyệt. Không ghi giấy tờ, raw OCR, cookie hoặc secret vào log rộng.
- Quy ước sản phẩm phục vụ phần mềm không phải kết luận về pháp luật.

## 7. Đọc và cập nhật

Đầu phiên: AGENTS → bản nền này → sổ tay → spec module liên quan. Chỉ đọc quy tắc chuyên sâu khi làm đúng phần đó; không nạp lịch sử mặc định.

Spec viết liền mạch hành vi đang áp dụng, kể cả trùng quyết định. Decision lưu điều đã chọn, lý do và phương án đã loại/chốt bỏ qua. Backlog giữ issue/task và trạng thái; sổ tay tóm tắt việc hiện tại, không là bản sao backlog. Khi quyết định đổi, cập nhật cả spec và decision.

| Đọc tiếp khi cần | Nội dung |
|---|---|
| [Sổ tay](product-overview.md) | Việc hiện tại, màn hình và điểm vào code |
| [Soạn thảo](notary_v2/README.md) | Luồng sử dụng đầy đủ |
| [Upload](upload_lab/README.md) | Đối chiếu và điền website |
| [NotaryOffice](notaryoffice/README.md) | Theo dõi công việc dự kiến |
| [Dữ liệu chung](shared/data-rules.md) | Đầu ra, quyền ghi và ranh giới hệ thống |
| [Bóc tách](shared/extraction-rules.md) | Quy tắc trường và nguồn Word |
| [Backlog](../backlog) | Ghi nhận việc chưa làm; ghi nhận không phải duyệt triển khai |
| [Electron runtime](shell/electron-runtime-support.md) | Bản hỗ trợ, package matrix và kết quả/giới hạn kiểm chứng |

