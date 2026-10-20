---
id: decision-owner-upload-field-standardization-20261019
title: "Chuẩn hóa trường Upload trước quét mẫu; Người nhiều giấy tờ và địa chỉ là issue riêng"
date: '2026-10-19'
status: accepted
---

## Nguồn và phạm vi được giao

Owner báo trường Hồ sơ còn thiếu: Upload đang bóc văn bản thành trường để điền web nhưng hệ thống còn trường nghiệp vụ mồ côi. Đây là quan sát của owner, không yêu cầu chạy Upload để chứng minh lại. Owner yêu cầu **ghi quyết định và hai issue độc lập**, chưa giao triển khai, đọc mẫu, tạo Word/corpus hoặc chạy parser/app/test/E2E.

## Quyết định hiện hành

- Chuẩn hóa **toàn bộ trường nghiệp vụ bóc tách và biểu mẫu Upload**, đối chiếu xuyên module với chuẩn DB/contract của **Người, Tài sản, Hồ sơ**. Không giới hạn vào cột workspace Notary hiện có. Catalog nền trước đây chưa chứng minh bộ trường Hồ sơ hoặc mapping Upload đã đủ.
- **Chủ đất là trường của Hồ sơ**, không phải thuộc tính chủ sở hữu cố định của Tài sản. Chưa chọn key, kiểu, cardinality, quan hệ/FK hay schema danh sách. Không đồng nhất với node `owner`/`owner_row_id` của Diagram Thừa kế.
- **Thông tin công chứng thuộc Hồ sơ**, độc lập với ngày tạo hồ sơ. Inventory phải gồm số/ngày công chứng, công chứng viên, thư ký và mọi trường Upload khác trước khi chốt đủ; không suy tất cả đã là cột DB được duyệt.
- **Bỏ qua thông tin giao dịch khi bóc tách và chuẩn hóa**: giá, đặt cọc, tiền thuê, khoản vay, lãi suất, điều khoản thanh toán. **Bỏ qua thời hạn nghiệp vụ**. Không áp dụng việc bỏ qua này cho thời hạn sử dụng đất trong `land_rows[].thoihan`, hoặc timeout kỹ thuật.
- Nếu portal thực sự yêu cầu trường đã loại, ghi xung đột consumer và câu hỏi refinement. Không âm thầm tiếp tục bóc, bịa/default hoặc tự quyết bước nhập tay mới. Quyết định này không cho xóa/sửa raw, bằng chứng lịch sử hay code/runtime nghiệp vụ trong lượt tài liệu.
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
  bảng nối hay schema cho nhiều người–nhiều tài sản hoặc các tổ hợp khác. Không
  coi mô hình quan hệ trước đó là đã được owner chấp nhận. Đây là phần phải làm kỹ
  trong refinement/inventory canonical của #41 trước implementation; lượt này không
  tạo ticket mới, không đổi gate và không cấp quyền sửa code/schema.
- **Pháp nhân:** không đưa vào Người, không thêm loại pháp nhân vào Person,
  không tự phân loại tổ chức thành thể nhân. Theo policy, **người dùng nhập tay**;
  đây là policy nhập liệu, không phải extraction hay default; code hiện tại chưa
  cutover. Hướng “sau này chuẩn hóa thành một bảng riêng” là định hướng của owner,
  **chưa duyệt bảng/cột/migration/contract hoặc triển khai** trong lượt này; nếu
  làm sau, đây là schema riêng phải thiết kế/chốt riêng; phạm vi ba đối tượng
  hiện tại không đổi, còn bảng pháp nhân tương lai là hướng owner cho phép và
  không bị quy tắc hiện tại cấm. Hồ sơ thế chấp là trường hợp mặc định có pháp
  nhân; loại khác ít xảy ra. Sự có mặt đó không đồng nghĩa đã biết hoặc được
  phép tự điền tên ngân hàng, chi nhánh, người đại diện hay coi một bên là mặc
  định; chỉ dùng dữ kiện nguồn nêu rõ. Pháp nhân khác không được âm thầm bỏ mất
  hoặc tự xếp loại; giữ nguồn và để người dùng nhập tay. Manual entry chỉ áp cho
  pháp nhân, không mở rộng thành cơ chế cho dữ liệu chưa rõ nghĩa.
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
  không dùng cụm để tự bóc pháp nhân. Cụm có thể là trường riêng theo ô website;
  phần tái dùng được vẫn map canonical, không mặc định coi cụm là dữ liệu chưa
  map/orphan.
- **Không xin owner duyệt từng chi tiết kỹ thuật** như một gate mới. Phần chưa
  có nghĩa nghiệp vụ hoặc chưa chọn ô website phải được ghi rõ là chưa chọn;
  không được giả định rồi triển khai.

### Hiện trạng và giới hạn

- Đường đang implement vẫn là 8 key Case metadata; Person/Asset/parties chưa
  canonical cutover. `nguoi_yeu_cau`/`duong_su`/`taisan` vẫn là output trình
  bày từ nguồn, chưa phải canonical block field. Chưa có bảng pháp nhân và chưa
  có trường lưu cụm được duyệt/triển khai. Các quy tắc trên là policy đích và
  ranh giới, không chứng minh runtime đã đổi.
- Raw, bằng chứng, file và `source_refs` giữ nguyên vai trò provenance kỹ thuật;
  không sửa raw/lịch sử để đạt chuẩn hóa. Lượt này chỉ tài liệu: không sửa code,
  schema, migration, runtime, test hoặc tạo bảng tương lai.
- #41 vẫn mở, `refined:false`, gate khảo sát mẫu vẫn **ĐÓNG**; #42 vẫn chỉ cho
  nhiều giấy tờ/địa chỉ của một Người và không tự thành prerequisite.
