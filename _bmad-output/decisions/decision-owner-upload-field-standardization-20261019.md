---
id: decision-owner-upload-field-standardization-20261019
title: "Chuẩn hóa trường Upload trước quét mẫu; Người nhiều giấy tờ và địa chỉ là issue riêng"
date: '2026-10-19'
status: accepted
---

## Nguồn và phạm vi được giao

Owner báo trường Hồ sơ còn thiếu: Upload đang bóc văn bản thành trường để điền web nhưng hệ thống còn trường nghiệp vụ mồ côi. Đây là quan sát của owner, không yêu cầu chạy Upload để chứng minh lại. **Mốc giao ban đầu (lịch sử):** ghi quyết định và hai issue độc lập, chưa giao triển khai/đọc mẫu/parser/app/test. Quyền runtime Nam Định bổ sung về sau, gồm đáp án BANKMODE cuối tài liệu, thay giới hạn docs-only cho slice được duyệt; gate mẫu vẫn giữ.

## Quyết định hiện hành

- Chuẩn hóa **toàn bộ trường nghiệp vụ bóc tách và biểu mẫu Upload**, đối chiếu xuyên module với chuẩn DB/contract của **Người, Tài sản, Hồ sơ**. Không giới hạn vào cột workspace Notary hiện có. Catalog nền trước đây chưa chứng minh bộ trường Hồ sơ hoặc mapping Upload đã đủ.
- **Chủ đất là trường của Hồ sơ**, không phải thuộc tính chủ sở hữu cố định của Tài sản. Chưa chọn key, kiểu, cardinality, quan hệ/FK hay schema danh sách. Không đồng nhất với node `owner`/`owner_row_id` của Diagram Thừa kế.
- **Thông tin công chứng thuộc Hồ sơ**, độc lập với ngày tạo hồ sơ. Inventory phải gồm số/ngày công chứng, công chứng viên, thư ký và mọi trường Upload khác trước khi chốt đủ; không suy tất cả đã là cột DB được duyệt.
- **Bỏ qua thông tin giao dịch khi bóc tách và chuẩn hóa**: giá, đặt cọc, tiền thuê, khoản vay, lãi suất, điều khoản thanh toán. **Bỏ qua thời hạn nghiệp vụ**. Không áp dụng việc bỏ qua này cho thời hạn sử dụng đất trong `land_rows[].thoihan`, hoặc timeout kỹ thuật.
- Nếu portal thực sự yêu cầu trường đã loại, ghi xung đột consumer và câu hỏi refinement. Không âm thầm tiếp tục bóc, bịa/default hoặc tự quyết bước nhập tay mới. Giữ raw/lịch sử; giới hạn không runtime ở lượt tài liệu ban đầu không freeze slice Nam Định được giao về sau.
- Không xóa trường Upload còn cần chỉ để vừa schema Notary hiện tại. Sau catalog có căn cứ, refine/chốt phần mở rộng canonical Hồ sơ thực sự cần trước khi triển khai. Chưa chọn engine DB vật lý chung, shared Case ID, gộp DB hay tích hợp liên module.
- Issue [chuẩn hóa trường Upload #41](../backlog/story-upload-business-field-standardization.md) chỉ hoàn thành khi chuẩn DB/contract được duyệt, triển khai và cutover mọi adapter/writer/reader/consumer/output bị ảnh hưởng với bằng chứng luồng thật. Chỉ lập bảng hoặc sửa nhãn/key không đủ; không shim, ghi chú chung hoặc raw capture thay trường nghiệp vụ.
- **Gate mới toàn hệ thống:** mọi lượt quét/đọc nội dung mẫu thực mới, batch owner-sample, corpus và vòng test/E2E theo mẫu phải chờ #41 được nghiệm thu đầy đủ. Viết bảng mapping không mở gate. Qua gate vẫn cần được giao thực thi; sau đó quy tắc pending từng file/#39 không chặn file đã rõ tiếp tục áp dụng. Không tắt Scan/Upload production đang có hoặc tạo feature flag từ tài liệu này.
- Verification riêng của #41 khi được giao có thể dùng input tổng hợp/kiểm soát và DB/profile cô lập qua consumer thật; không yêu cầu đọc/quét corpus `D:\testcase` trước khi đóng issue. Inventory source tĩnh trong lượt ghi ticket không phải lô khảo sát mẫu; lượt này không chạy verification runtime.
- **Một Người có nhiều giấy tờ định danh và nhiều địa chỉ** được ghi thành [một issue riêng #42](../backlog/story-person-multiple-identities-addresses.md). Hiện model là một bộ giấy tờ và một địa chỉ. Model/schema/migration/chọn bản dùng/bóc tách/xuất tương lai cần thiết kế; child records trong Người được xem xét nhưng chưa chọn. Không thêm đối tượng nghiệp vụ thứ tư, không ép chuỗi/ô hiện có thành đa trị. #42 không tự trở thành prerequisite của #41 hoặc gate quét mẫu.

## Giữ nguyên và thay thế rõ phạm vi

- Quy tắc cũ “gap từng file không dừng cả lô” trong [quyết định context](decision-owner-case-context-standard-data-20261019.md) và [quy trình theo mẫu](decision-owner-sample-first-iteration-20261019.md) giữ lịch sử; nay chỉ áp dụng **sau gate #41**. Không dùng chúng để bắt đầu quét mẫu khi chưa chuẩn hóa xong.
- Quyết định [Danh sách hồ sơ #20](decision-owner-case-list-redesign-deferred-20261017.md) vẫn DEFERRED; phần trước đây chưa chốt vị trí chủ đất nay được thay bằng lựa chọn **thuộc Hồ sơ**, không duyệt whitelist UI/search/filter hoặc schema cụ thể.
- [#40](../backlog/bug-stage-raw-gcn-serial-contract.md) là gap serial Stage/persistence riêng, chưa sửa; #41 không nhận trùng hoặc tuyên bố đã sửa nó.
- Website chính thức vẫn là SOT; người dùng tự kiểm tra/bấm Lưu; rule regex và website có version do developer quản lý. Raw/provenance/file/cookie/cấu hình tab là dữ liệu kỹ thuật, không tự là trường nghiệp vụ mồ côi.

## Những lựa chọn chưa được thực hiện

Key/kiểu/format/nhóm/cardinality và cột DB/wire mới của các trường Hồ sơ còn thiếu phải được chốt trong #41 từ catalog đầy đủ. Việc ghi issue không duyệt schema hoặc implementation. Chi tiết mô hình đa giấy tờ/đa địa chỉ để #42 thiết kế, không hỏi owner duyệt lại các lựa chọn nghiệp vụ đã nêu ở đây.

## Bổ sung owner — triển khai metadata Hồ sơ

- Owner trả lời nguyên văn: **“người được gán chủ đất trong diagram”**.
  Lựa chọn này thay các phương án người đứng tên GCN hoặc bên chuyển giao.
- `chudat` thuộc Hồ sơ, lấy tên Người đã commit được đánh dấu **Chủ** trên
  Diagram (`ownPositions` có giá trị); không đồng nhất với `owner_row_id`
  hoặc slot `owner` là người để lại di sản. Không suy từ Word, GCN hay Bên A.
- Dùng tham chiếu `personId` hiện có để đọc tên snapshot Người; output là một
  trường text tên, mỗi người một dòng theo thứ tự Stage, không gộp theo tên.
  Chưa gán/không có Diagram (Upload, Hai bên) là `null`; không thêm quan hệ mới.
- Giao triển khai metadata Case gồm tiêu đề, nhóm portal, loại nhận diện,
  số/ngày công chứng, công chứng viên, thư ký và `chudat`; giữ riêng enum
  văn bản Notary. Không mở rộng Person/Asset/parties hoặc nghiệm thu toàn #41.
- Giữ nguồn, JSON lịch sử, website SOT và người dùng tự Lưu. Proof dùng
  DOCX tổng hợp, DB/profile cô lập; không đọc corpus owner hoặc ghi chéo DB.

## Bổ sung owner 20/10/2026 — SOT cấu trúc website

- **Nam Định trước**, tại `https://congchungnamdinh.ninhbinh.gov.vn/`,
  là website thứ nhất trong hai website Upload Lab cần khảo sát. Website thứ
  hai chưa được định danh/khảo sát trong lượt này; không dùng cấu trúc hoặc
  catalog Nam Định thay website đó.
- Giữ **SOT cấu trúc website lâu dài** trong spec Upload: route/màn hình,
  biểu mẫu/widget, danh mục dropdown và đường mapping extraction → chuẩn
  Người–Tài sản–Hồ sơ → DB/wire → API/selector website. Ghi ngày, nguồn và
  giới hạn kiểm chứng; cập nhật tại cùng nguồn khi website hoặc adapter đổi.
  Nguồn bền vững: [SOT Nam Định](../specs/upload_lab/nam-dinh-website-sot.md);
  README module/sổ tay dẫn tới đây, không phụ thuộc evidence tmp.
- Có thể cần trường phụ theo website, nhưng **chưa duyệt schema mới**.
  Phân loại riêng ID/nhãn catalog, cấu hình/policy/default portal, provenance
  kỹ thuật và dữ liệu nghiệp vụ thật chưa có mapping. Không tự tạo canonical
  key/cột DB hoặc nhét vào ghi chú. Phí/ghi chú/status đã có policy hiện tại
  chốt bên dưới; các mở rộng tương lai và trường giao dịch bị loại vẫn phải xét đúng nghĩa.
- Cấu trúc/options/API quan sát trên web chỉ là bằng chứng về website;
  `contracts/entities.md` và contract được duyệt vẫn quyết định chuẩn app.
  Catalog không nâng Upload workflow Draft thành approved hoặc mở gate #41.
  Case 8 key đã implement; Person/Asset/parties chưa cutover đầy đủ.
- Tại mốc khảo sát website, chỉ tài liệu và bằng chứng an toàn: không sửa code/
  schema, không ghi DB, không đọc testcase/corpus owner, không bấm Lưu hợp đồng
  hoặc dùng credential ngoài quyền được cấp. Quyền runtime bổ sung ghi bên dưới.

## Bổ sung owner 20/10/2026 — policy phí, ghi chú và trạng thái Nam Định

- Owner: **“4 khoản phí hiện tại chưa triển khai, mặc định bỏ qua không điền / ghi chú: bỏ qua / tất cả hợp đồng được upload lên đều là "đã công chứng" mặc định”**.
- Áp dụng hiện tại: bỏ qua/không điền `chiphi.phicongchung`, `chiphi.thulaoCongchung`, `chiphi.phiDvNgoaicongchung`, `chiphi.phikhac` và Ghi chú `ghichu`. Không ghi 0, không xóa default portal, không thêm extraction/cột phí hoặc quy trình nhập tay.
- Tổng chi phí là display/derived, không input thứ năm; không persistence riêng. Giữ nguyên inventory/quan sát và gap mapping phí như hiện trạng ngoài scope, không còn câu hỏi chờ owner chọn triển khai.
- Mọi hợp đồng upload Nam Định mặc định **`DACONGCHUNG` / “Đã công chứng”**. Đây là policy portal, không dữ kiện trích xuất và không mapping trạng thái Notary draft/locked.
- Tại mốc chốt policy, docs không xác nhận runtime đã triển khai; quyền triển khai được bổ sung ở mục dưới. Mở rộng tương lai cần duyệt và giao riêng; chưa duyệt business schema, toàn #41 chưa xong, gate mẫu **ĐÓNG**.


## Bổ sung owner 20/10/2026 — thực thi liên tục phần đã chốt

- Owner: **“triển khai liên tục, chỉ dừng khi cần tôi chốt”**. Giao runtime Nam Định/#41 theo policy đã chốt, không dừng xin technical approval; chỉ hỏi khi thực sự cần quyết định nghiệp vụ/schema chưa có nguồn chuẩn.
- Slice đầu: bỏ phí/ghi chú khỏi mọi đường điền, status Đã công chứng, gỡ click-Lưu/prime và nguy cơ Enter submit, đưa attachment nguồn kỹ thuật vào preSave; không đoán mapping nghiệp vụ hoặc metadata POST.
- Verification dùng input/form/SQLite/browser cô lập và consumer thật; không corpus owner, portal thật upload/Save, production DB, session/credential import hoặc cloud/provider mới. Session authenticated do browser worker chuyên trách, không runtime implementer điều khiển.
- Worker bàn giao trước commit; parent tổ chức review/fix độc lập rồi commit. Không tuyên bố toàn #41 hoàn tất hoặc mở gate mẫu từ slice này; #42 không prerequisite.

- Kết quả slice preparation: implementer và reviewer độc lập cùng xác nhận Upload **42 pass, không skip**, sidecar **60 pass**; **review CLEAN**. Smoke consumer harden sau review: thiếu source dù text filename hiện trên trang vẫn attachment false/partial, affected suite **5 pass, không skip**. Owner giao commit đúng 13 paths, không push/packaging; giữ AGENTS và foreign changes. Không nâng bằng chứng cô lập thành portal/backend/ID-conversion acceptance hoặc hoàn thành #41.

## Bổ sung owner 20/10/2026 — quan hệ ba đối tượng, pháp nhân và cụm trường website

**Nguyên văn owner:**

> 1. “quan hệ người - tài sản - hồ sơ: là 1 quan hệ phức tạp, cần làm kỹ. Nhất là trong trường hợp nhiều người, nhiều tài sản”.
> 2. “Pháp nhân không đưa vào người, hiện tại chỉ có hồ sơ thế chấp mặc định có pháp nhân, còn lại ít xảy ra - trường thông tin pháp nhân còn chưa đồng nhất - ghi lại đây là quyết định của tôi: pháp nhân để user nhập tay, sau này sẽ chuẩn hóa thành 1 bảng riêng”.
> 3. “Đối với một số cụm thông tin có tính phức tạp nhưng không lặp lại (1 số ô nhập trên web) - có thể dùng thêm 1 trường để bóc tách cả cụm thay vì làm cồng kềnh hệ thống - web khác lại có yêu cầu khác”.

**Đề xuất trước bị bác (phạm vi hẹp):** việc đưa pháp nhân vào **Người** bị owner bác,
**không phải quyết định đã được chấp nhận** và không được dùng làm tiền đề. Lý do:
pháp nhân không phải thể nhân, trường pháp nhân chưa đồng nhất; ép vào Person sẽ
phân loại sai và trộn nghĩa. Đề xuất mô hình parties rộng hoặc mô hình quan hệ
đơn giản trước đây cũng **chưa được chấp nhận**, nhưng owner **không bác mọi khái
niệm parties/ordered participation**: quan hệ nhiều người/nhiều tài sản là bài
toán riêng, owner yêu cầu làm kỹ, chưa chọn model/cardinality/schema. Không có
“phương án cũ đã duyệt” để kế thừa.

### Quy tắc áp dụng

- **Quan hệ Người–Tài sản–Hồ sơ:** chưa chọn model, cardinality, quan hệ/FK,
  bảng nối hay schema nhiều người–nhiều tài sản. Chỉ đạo mới ở mục “Trả lời ma
  trận” bên dưới thay yêu cầu trước “làm trong #41, không tạo ticket”: D06+D07
  chuyển một issue riêng #43, làm ngay sau rõ các ô, không chờ toàn #41 xong.
  Không coi model cũ đã duyệt hoặc mở gate/schema canonical quan hệ; ngoại lệ runtime projection ngân hàng đã được giao ở đáp án cuối.
- **Pháp nhân:** không đưa vào Người, không thêm loại pháp nhân vào Person,
  không tự phân loại tổ chức thành thể nhân. Policy **người dùng nhập tay** chung
  có ngoại lệ ngân hàng thế chấp **app tự lấy** ở đáp án cuối. Không bịa/default;
  hướng bảng riêng tương lai vẫn là định hướng của owner,
  **chưa duyệt bảng/cột/migration/contract hoặc triển khai** trong lượt này; nếu
  làm sau, đây là schema riêng phải thiết kế/chốt riêng; phạm vi ba đối tượng
  hiện tại không đổi, còn bảng pháp nhân tương lai là hướng owner cho phép và
  không bị quy tắc hiện tại cấm. Hồ sơ thế chấp là trường hợp mặc định có pháp
  nhân; loại khác ít xảy ra. Sự có mặt đó không đồng nghĩa đã biết hoặc được
  phép tự điền tên ngân hàng, chi nhánh, người đại diện hay coi một bên là mặc
  định; chỉ dùng dữ kiện nguồn nêu rõ. Pháp nhân khác không được âm thầm bỏ mất
  hoặc tự xếp loại; giữ nguồn và để người dùng nhập tay. Ngoài pháp nhân, chỉ
  alias R05 và lời phức tạp D04 có lựa chọn nhập/sửa tay cụ thể bên dưới;
  không mở thành cơ chế cho mọi dữ liệu chưa rõ nghĩa.
- **Cụm trường phụ website:** owner cho phép **có điều kiện** thêm một trường
  để giữ cả cụm khi cụm phức tạp, không lặp lại và thuộc một ô nhập của một
  website cụ thể, thay vì làm cồng kềnh hệ thống. Đây không phải quyết định rằng
  ba editor `nguoi_yeu_cau`/`duong_su`/`taisan` hay mọi ô web đều thành block/
  trường phụ. Khi chọn cụm phải xác định website/phạm vi ô, nghĩa nghiệp vụ,
  lý do không tái dùng trường canonical Người/Tài sản/Hồ sơ đã biết, kiểu lưu và
  provenance; chỉ hỏi owner khi có quyết định nghiệp vụ thực sự chưa rõ, chi tiết
  kỹ thuật do implementation sở hữu theo contract/rule đã duyệt. Không dùng
  `ghiChu` chung hoặc JSON bag chung thay trường; raw capture chỉ là provenance,
  không thay trường nghiệp vụ. Không tự đặt canonical key/tên/kiểu/nhóm/storage;
  chỉ tự lấy ngân hàng trong ngoại lệ đã chốt ở cuối, không tự bóc pháp nhân khác. Cụm có thể là trường riêng theo ô website;
  phần tái dùng được vẫn map canonical, không mặc định coi cụm là dữ liệu chưa
  map/orphan.
- **Không xin owner duyệt từng chi tiết kỹ thuật** như một gate mới. Phần chưa
  có nghĩa nghiệp vụ hoặc chưa chọn ô website phải được ghi rõ là chưa chọn;
  không được giả định rồi triển khai.

### Hiện trạng và giới hạn

- Đường đang implement vẫn là 8 key Case metadata; Person/Asset/parties chưa
  canonical cutover. `nguoi_yeu_cau`/`duong_su`/`taisan` vẫn là output trình
  bày từ nguồn, chưa phải canonical block field. Chưa có bảng/key canonical
  pháp nhân mới; projection requester text persist qua payload JSON có sẵn là
  hợp lệ, không hoàn tất normalized cutover. Runtime slice mới còn chờ proof cuối.
- Raw, bằng chứng, file và `source_refs` giữ vai trò provenance kỹ thuật;
  không sửa raw/lịch sử. Giới hạn chỉ tài liệu ở mốc cũ là lịch sử; đáp án cuối
  cho tiếp tục runtime slice đã chốt, không mở schema/bảng tương lai.
- #41 vẫn mở, `refined:false`, gate khảo sát mẫu vẫn **ĐÓNG**; #42 vẫn chỉ cho
  nhiều giấy tờ/địa chỉ của một Người và không tự thành prerequisite.

## Trả lời ma trận Nam Định §7 — owner 20/10/2026

Nguồn: owner trả lời trực tiếp các dòng trong [SOT §7](../specs/upload_lab/nam-dinh-website-sot.md#owner-review).
Ma trận đề xuất trước và lần làm rõ pháp nhân trước đó là lịch sử phương án,
không phải approval toàn bảng. Các lựa chọn dưới đây là **spec nghiệp vụ đích**,
không chứng minh runtime đã cutover; không sửa raw/lịch sử.

- **W05:** owner đồng ý hướng dựng lựa chọn portal từ tập tài sản có căn cứ.
  Giữ loại live **ID 1 Đất đai có tài sản**, thường nhà ở trên đất: chưa có hợp
  đồng mẫu để rút rule regex **không có nghĩa loại không tồn tại**. Chưa có
  rule chọn một ô cho tổ hợp nhiều loại hoặc catalog/rule nhà chi tiết; giữ
  thiếu nguồn/rule rõ ràng, không tự tạo schema/regex, đọc corpus hoặc chọn
  đầu/Khác/loại bao quát không căn cứ.
- **R05:** “bỏ tên gọi khác – nếu có user điền tay”. Loại auto-fill alias và
  mở rộng chuẩn hóa alias khỏi đích hiện tại; không nối alias vào `ten`, không
  tạo field alias mới hoặc mở #42. Raw/history vẫn giữ.
- **R06:** owner đổi business spec: **“Người yêu cầu công chứng = tất cả người
  có trong hồ sơ”**. Điền dữ liệu chuẩn của mọi Người trong Hồ sơ; không Bên A,
  Bên B, con đẻ, chức vụ, tư cách hay lời mô tả phụ. Lookup/ưu tiên B/người
  đầu trước đây chỉ là hiện trạng cũ, **không còn authority nghiệp vụ đích**.
  Không cắt tên hoặc suy thêm người thiếu. Phạm vi requester đã được owner
  trả lời trong mục “Đáp án #43” bên dưới; không dùng đoạn lịch sử này để
  đưa người chết/nhân sự vào output requester hoặc xóa Person khỏi Hồ sơ.
- **D04:** “lời văn phức tạp loại bỏ - user tự sửa thủ công”. Dữ liệu chuẩn cá
  nhân vẫn dùng; lời tư cách/căn cứ phức tạp bỏ khỏi tự động điền, user sửa tay.
  Không duyệt block D04, không xóa nguồn hay mở manual fallback cho mọi gap.
- **D05:** “Chỉ gán vào Bên A hoặc bên B nói chung”; quan sát **“Gần như 100%
  Bên B luôn có chữ nhận”** không là luật 100% hoặc regex. Nguồn hiện có phân
  biệt chuyển/nhận chuyển nhượng, thế chấp/nhận thế chấp; ủy quyền/được ủy quyền
  không nhất thiết có chữ nhận; thừa kế có văn bản một bên. Các ngoại lệ đã
  được trả lời ở mục “Đáp án #43” bên dưới; không suy mọi còn lại=A và
  không áp nhóm A/B để thu hẹp requester đã chốt.
- **D06+D07:** tạo **một [#43 riêng](../backlog/spike-case-people-assets-relationships.md)**
  về nhiều người/nhiều tài sản, membership/vai trò/thứ tự và scope người↔tài
  sản. Xử lý **ngay sau làm rõ các ô**, không chờ toàn #41 nghiệm thu để tránh
  vòng phụ thuộc; #41 tiếp nhận kết quả trước cutover quan hệ. #42 không là
  prerequisite. Nay phân tích 16 ca/Q1/Q2/BANKMODE đủ đáp án, bàn giao #41; chưa duyệt model/FK/cardinality quan hệ.
- **D08:** owner “đã trả lời ở R06”. Chỉ dữ liệu chuẩn Người, không lời quan
  hệ/tư cách/chức vụ trong requester; không duyệt residual prose block D08,
  không hỏi lại lựa chọn này.
- **A09:** owner yêu cầu rõ trường nào tạo cụm và có ví dụ lưu lại. SOT §7.5.1
  lưu bảng trường thực và ví dụ đất/GCN tổng hợp, không PII. Phân biệt **đoạn
  trình bày ghép từ chuẩn** với **lời dư thật chưa map**; chưa duyệt field
  A09, storage hoặc block tài sản/nhà. Wire/model/mapper gap vẫn ghi rõ.
- **A10:** duyệt giữ xe/sổ tiết kiệm/bảo hiểm ở nhận diện + nguồn, pending
  structured support; chưa mở rộng hiện tại, #29 vẫn DEFERRED. Không áp loại
  này cho đất có tài sản/nhà của W05.

### Phương án hai tầng — lịch sử cân nhắc, đã bị thay bởi quyết định bên dưới

Owner nhận xét Người + Tài sản thường nối tự nhiên thành đoạn; cân nhắc tầng 1
dữ kiện tĩnh, tầng 2 đoạn suy ra từ dữ kiện, có thể có điều kiện. Owner yêu cầu
**cân nhắc thật kỹ**, độ tùy biến sâu đổi lấy độ đơn giản/ổn định thế nào.
Đây là **phương án đã cân nhắc, chưa từng được chọn hoặc triển khai**; nội dung
mục này giữ làm bằng chứng lịch sử, không phải định hướng hiện hành. Chỉ dùng
ví dụ tổng hợp trong Git, không chép tên/ID user đưa.

## Bổ sung owner 20/10/2026 — chốt chỉ placeholder và trường tĩnh

**Nguyên văn owner:** “chốt chỉ dùng placeholder và trường tĩnh, tiếp tục”.

**Quyết định hiện hành (thay phần chọn kiến trúc còn treo ở mục trên):**

- Chốt **chỉ dùng placeholder và trường tĩnh**. Không mở **trường tầng 2 động/
  tính toán**, **text/đoạn canonical persisted từ suy ra**, **engine công thức**
  hoặc **framework điều kiện/cấu hình**. Không có scope trường động mới và
  không tạo gate xin duyệt kỹ thuật mới cho hướng đó; owner yêu cầu tiếp tục
  phần đã chốt. Đây là giới hạn **trường nghiệp vụ mới**, không phải lệnh gỡ
  cơ chế placeholder/block token mà Word đang có.
- **Phân biệt nguồn và đầu ra:** dữ kiện nghiệp vụ **tĩnh, ghi nhận từ nguồn**
  (trường canonical/trường đã chốt, kể cả giá trị text) khác **định dạng output**
  lúc xuất (placeholder, formatter và bố cục Word hiện có). Việc thay placeholder
  bằng giá trị không tự biến placeholder/formatter thành trường nghiệp vụ mới.
  Quyết định này **không cấm** trường tĩnh nhận giá trị là một đoạn/cụm text có nguồn.
- **Quyền có điều kiện trước đó cho cụm text tĩnh vẫn giữ:** một trường giữ cả
  cụm khi cụm phức tạp, không lặp lại và thuộc một ô nhập của một website cụ thể
  vẫn là ngoại lệ được owner cho phép, vì đây là **dữ kiện tĩnh có nguồn**, không
  phải tầng động/tính toán. Vẫn phải xác định website/ô, nghĩa, lý do không tách,
  kiểu lưu và provenance, và được chốt theo quy trình hiện có. **A09 vẫn chưa
  duyệt field**, không dùng quyết định này để tự tạo block/field nhà.
- `nguoi_yeu_cau`/`duong_su`/`taisan` tiếp tục là **output trình bày từ nguồn**,
  không mặc nhiên thành canonical block field. Placeholder/formatting hiện có
  của Word giữ nguyên; không suy từ quyết định này rằng mọi đoạn có thể lưu thành
  trường nghiệp vụ hoặc mọi editor thành block.
- **Không xóa hoặc sửa** block token do code Word định nghĩa sẵn, alias cũ,
  formatter hiện có hay mẫu Word đang hỗ trợ. Các tính năng legacy-supported giữ
  nguyên hiện trạng: quyết định này không phê duyệt framework block mới và cũng
  không cấp quyền gỡ tính năng đang chạy.
- Giới hạn **chỉ tài liệu** là mốc ghi nhận này trong lịch sử; lệnh liên tục và
  đáp án BANKMODE bên dưới cho runtime slice đã chốt. #41 mở/refined:false, gate mẫu **ĐÓNG**.

## Đáp án #43 — membership requester và nhóm A/B, owner 20/10/2026

**Nguyên văn owner:**

> 1. Người trong hồ sơ:
> Người sống: Bên A, Bên B, người đại diện theo ủy quyền, Ngân hàng (đối với hợp đồng thế chấp) – dán cả cụm,
> Không đưa vào: người chết, công chứng viên, nhân viên
> 2. Gán A/b:
> - ủy quyền: đồng ý
> - chỉ có 1 bên: Không gán gì
> - 2 nguồn A/b trái nhau: đồng ý

**Đã chọn — phạm vi Nam Định/Upload requester/output hiện tại:**

- Cá nhân sống thuộc Bên A, Bên B và người đại diện theo ủy quyền được đưa
  vào requester. Người chết, công chứng viên và nhân viên **không đưa vào
  requester output**. Không tự đưa tên thân nhân chỉ được nhắc vào danh sách.
  Đây không là lệnh xóa Người chết/Người liên quan khỏi Stage, Hồ sơ thừa kế,
  raw, snapshot hoặc lịch sử; trường Person hợp lệ và metadata nhân sự giữ nguyên.
  “Thuộc Bên A/B” chỉ tư cách tham gia nguồn, **không là điều kiện có tag A/B
  đã gán**: cá nhân sống của văn bản một bên và đại diện ủy quyền vẫn vào
  requester khi nhóm chưa gán hoặc đang conflict; chỉ phần nhãn nhóm chờ xác nhận.
- Cá nhân thông thường vẫn chỉ dữ kiện chuẩn R06, mỗi identity đã xác nhận
  một lần theo thứ tự nguồn; không B-priority/firstperson/lookup. Alias nhập
  tay, D04/D08 không prose tự động, không mở fallback cho mọi gap.
- Ủy quyền: **A = người ủy quyền, B = người được ủy quyền** theo phương án
  owner đồng ý trong trao đổi trước đáp án. Văn bản chỉ một bên **không gán
  A/B**; không mặc định A hoặc dựng B giả. Hai nguồn A/B trái nhau giữ xung
  đột và xác nhận phần nhóm bị ảnh hưởng, không tự chọn nguồn thắng hoặc
  đổi tập requester. Chữ “nhận” không là regex phổ quát.
- Ngân hàng trong hợp đồng thế chấp được yêu cầu hiện **cả cụm** như ngoại lệ
  output, **không là Person**. Policy pháp nhân không thuộc Người/bảng riêng
  tương lai vẫn giữ. **Owner đã trả lời BANKMODE: “app tự lấy”.** App tự lấy
  cả cụm ngân hàng thế chấp từ nguồn và điền requester, không user-paste-only.
  Đây là ngoại lệ output nguồn tĩnh được duyệt, không Person/bảng pháp nhân
  hoặc trường tầng động. Cá nhân khác giữ dữ kiện chuẩn, không blanket raw.
  Dùng đích output có sẵn `web_form.nguoi_yeu_cau`, lưu payload JSON và reader/
  consumer hiện có; không cần entity/key canonical mới để lưu projection.
  Cụm chỉ ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/căn cứ ủy quyền có nguồn,
  giữ vị trí nguồn trong requester đầy đủ của mọi cá nhân sống thực sự tham gia;
  không xuất lặp đại diện đã trong cụm. Giữ raw/person arrays/provenance/history,
  không nuốt tài sản, giá/cọc/vay/lãi/thanh toán/thời hạn nghiệp vụ hoặc mở prose cá nhân.

Q1/Q2/BANKMODE đã trả lời đủ; không còn owner gate trong phân tích #43.
Chỉ đạo liên tục cho phép triển khai slice ngân hàng #41, không docs-only freeze.
Model/cutover toàn #41 chưa hoàn tất; gate mẫu vẫn ĐÓNG. Chỉ verification tổng
hợp/cô lập được giao; không hồ sơ thật, portal writes/Save/upload hoặc production DB.
Không chạm phiên Chrome đã đăng nhập; review độc lập sau proof trước commit scope.
Kế hoạch trước sửa code nằm ở [#43 plan §6.1](../backlog/spike-case-people-assets-relationships-plan.md).
Đường projection hiện có là persistence hợp lệ, không toàn normalized #41.
Bounded proof/fresh bank-auto review CLEAN/Ticket PASS đã có; #43 phân tích done theo quyền parent, không toàn #41 BUILT/đóng gate.
