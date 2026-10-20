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
- Lượt này chỉ tài liệu và bằng chứng website an toàn: không sửa code/schema,
  không ghi DB, không đọc testcase/corpus owner, không bấm Lưu hợp đồng hoặc
  dùng credential ngoài quyền được cấp. Chờ review độc lập trước commit.

## Bổ sung owner 20/10/2026 — policy phí, ghi chú và trạng thái Nam Định

- Owner: **“4 khoản phí hiện tại chưa triển khai, mặc định bỏ qua không điền / ghi chú: bỏ qua / tất cả hợp đồng được upload lên đều là "đã công chứng" mặc định”**.
- Áp dụng hiện tại: bỏ qua/không điền `chiphi.phicongchung`, `chiphi.thulaoCongchung`, `chiphi.phiDvNgoaicongchung`, `chiphi.phikhac` và Ghi chú `ghichu`. Không ghi 0, không xóa default portal, không thêm extraction/cột phí hoặc quy trình nhập tay.
- Tổng chi phí là display/derived, không input thứ năm; không persistence riêng. Giữ nguyên inventory/quan sát và gap mapping phí như hiện trạng ngoài scope, không còn câu hỏi chờ owner chọn triển khai.
- Mọi hợp đồng upload Nam Định mặc định **`DACONGCHUNG` / “Đã công chứng”**. Đây là policy portal, không dữ kiện trích xuất và không mapping trạng thái Notary draft/locked.
- Docs ghi quy tắc đích đã chốt, **không xác nhận runtime mới đã triển khai** và không giao code/schema/browser/Save/upload/DB/test. Mở rộng tương lai cần duyệt và giao riêng; chưa duyệt business schema, toàn #41 chưa xong, gate mẫu **ĐÓNG**.

