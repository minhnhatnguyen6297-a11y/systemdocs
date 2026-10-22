# Quy tắc dữ liệu và ranh giới hệ thống

**Cập nhật:** 21/10/2026. Quy tắc có hiệu lực được viết tại đây; mục ghi Draft vẫn chưa được duyệt.

## 4. Chuỗi dữ liệu chung

```text
SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED
```

| Lớp | Ý nghĩa | Quy tắc |
|---|---|---|
| `SOURCE` | File, ảnh, tin nhắn hoặc sự kiện gốc | Giữ hash, thời gian và nguồn |
| `RAW` | Chữ OCR hoặc sự kiện máy quan sát | Không sửa để che lỗi |
| `NORMALIZED` | Giá trị chuẩn hóa bằng rule | Truy ngược được về RAW |
| `INFERRED` | Ứng viên, phân loại hoặc quan hệ suy ra | Giữ rule/model và độ tin cậy |
| `CONFIRMED` | Dữ liệu đã được người có quyền xác nhận | Người dùng có thẩm quyền xác nhận; module có quyền ghi mới lưu |

Nói gọn: giữ giấy tờ gốc, lấy phần chữ đọc được, chuẩn hóa, tạo suy đoán khi
cần, rồi để người có quyền xác nhận; máy không tự biến chữ đọc được thành dữ
liệu đã xác nhận.

Không được đi thẳng từ OCR/LLM tới dữ liệu `CONFIRMED`. Giá trị thiếu bằng
chứng phải để trống hoặc cảnh báo, không tự điền.

**Snapshot và lịch sử nghiệp vụ — owner 21/10/2026:** record nghiệp vụ là
Hồ sơ (ai, tài sản gì, làm gì); mỗi Hồ sơ chỉ giữ một snapshot hiện hành.
Lưu lại cùng Hồ sơ cập nhật snapshot đó, không tự tạo Hồ sơ mới hay giữ
snapshot từng lần lưu/lịch sử sửa từng ô. Lịch sử Người/Tài sản là các Hồ sơ
liên quan cùng ID theo điểm neo bên dưới. Mỗi Hồ sơ đã lưu giữ bộ thông tin
riêng, chỉ user sửa thủ công; không tự cập nhật theo danh mục hoặc Hồ sơ khác.
Khi lấy Người/Tài sản vào Hồ sơ mới mặc định bộ mới nhất, không chọn phiên bản.
Các bộ thông tin khác nhau vẫn giữ qua những Hồ sơ đó. Không mặc định thêm bảng
phiên bản Người/Tài sản hoặc bitemporal. Một snapshot logic không bắt buộc
một dòng JSON: cấu trúc bảng/cột còn thiết kế. Bộ đếm revision chống ghi đè
khác với lưu nhiều snapshot. Raw, nguồn, `source_refs` và lịch sử kỹ thuật
đã có vẫn giữ; không cấp quyền xóa lịch sử hoặc tạo logging mới.
[Quyết định](../../decisions/decision-owner-case-snapshot-as-history-20261021.md).

### 4.1 `IdentityEvidence` — bản nháp dùng để đối chiếu

**Trạng thái:** Draft từ MIN-62, chưa phải contract xuyên sản phẩm đã publish.
G1 từng dùng shape này làm tham chiếu; không được hiểu nó là Case ID chung.

| Trường | Bắt buộc | Ý nghĩa |
|---|---:|---|
| `evidence_id` | Có | ID bất biến trong phạm vi producer |
| `subject_type` | Có | `person`, `property` hoặc `case` |
| `kind` | Có | Loại bằng chứng như `cccd`, `gcn_serial`, `land_parcel`, `map_sheet`, `notary_number`, `locality` |
| `raw_value` | Có | Giá trị nguyên dạng; có thể chứa lỗi OCR |
| `normalized_value` | Khi chuẩn hóa được | Giá trị theo `contracts/entities.md`; chưa chắc thì `null` |
| `source_ref` | Có | Vị trí nguồn: file, trang, đoạn, sheet hoặc cell |
| `observation_state` | Có | `observed`, `normalized`, `inferred` hoặc `confirmed` |
| `confidence` | Khi máy suy ra | Điểm/bucket của producer; không phải xác nhận pháp lý |
| `observed_at` | Có | ISO-8601 có múi giờ |

Không ghi đè raw bằng normalized. Không nhận dạng được vẫn giữ raw và nguồn.
CCCD, GCN, thửa/tờ và số công chứng chỉ là bằng chứng đối chiếu; chúng không tự
tạo Case hoặc quan hệ sở hữu. Muốn publish shape xuyên sản phẩm phải có owner
duyệt và contract/schema riêng.

### 4.2 Nguyên tắc đầu ra bóc tách

**Phạm vi toàn hệ thống — owner 19/10/2026:** mọi luồng nghiệp vụ xoay quanh
**Người, Tài sản, Hồ sơ**. Mỗi chức năng sử dụng dữ liệu chuẩn hóa của ba đối
tượng; mọi input nghiệp vụ sau chuẩn hóa phải ánh xạ vào đúng bộ trường
canonical đã duyệt, và mọi output nghiệp vụ dùng đúng trường/kiểu/định dạng/
cách nhóm đó. Không để dữ liệu nghiệp vụ mồ côi hoặc đẩy vào ghi chú khác nghĩa;
ngoại lệ hẹp duy nhất là cụm trường phụ website theo hướng owner cho phép có điều kiện
theo mục dưới, không phải lý do chung để giữ dữ liệu chưa map. Bộ trường là cố
định đối với lần triển khai; cần mở rộng phải chốt trước, không tự tạo trường.
Raw, bằng chứng và `source_refs` giữ vai trò provenance kỹ thuật,
không buộc raw đã mang schema DB; quy tắc này không tạo entity nghiệp vụ thứ tư,
Case chung hoặc quyền tích hợp liên module.

**Bổ sung owner 19/10/2026:** **chủ đất là trường Hồ sơ**, không là thuộc tính
chủ sở hữu cố định của Tài sản hoặc mặc định node `owner`/`owner_row_id` Thừa kế.
Thông tin công chứng thuộc Hồ sơ, độc lập ngày tạo hồ sơ. Phải inventory đủ
số/ngày công chứng, công chứng viên, thư ký và mọi trường nghiệp vụ bóc tách/form
Upload xuyên module trước khi chốt catalog; không giới hạn theo cột Notary hiện
có. Key/kiểu/format/nhóm/cardinality và DB-wire-output còn thiếu phải refine
trong [#41](../../backlog/story-upload-business-field-standardization.md).
Không xóa trường Upload cần thiết cho vừa schema hiện tại; mở rộng canonical
Hồ sơ có căn cứ và được duyệt khi cần, không coi định hướng là duyệt cột mới.

Owner làm rõ sau đó: **“người được gán chủ đất trong diagram”**.
Nguồn `chudat` là `ownPositions` đã lưu trỏ tài sản hiện có, loại hidden/deleted,
tên snapshot Stage theo `personId`; không tự lấy slot owner/người chết,
GCN hoặc Bên A. Upload không có Diagram là null. Catalog metadata Case đã
triển khai ở `contracts/entities.md` §9.4; phần Person/Asset/parties của #41
chưa hoàn thành nên gate mẫu vẫn **ĐÓNG**.

Không bóc/chuẩn hóa thông tin giao dịch (giá, đặt cọc, tiền thuê, khoản vay,
lãi suất, điều khoản thanh toán) hoặc thời hạn nghiệp vụ. **Giữ thời hạn sử dụng
đất** đúng cụm `land_rows[].thoihan` và timeout kỹ thuật. Nếu portal yêu cầu
trường bị loại, ghi xung đột consumer để refine, không âm thầm giữ extraction,
bịa/default hoặc tự quyết bước nhập tay mới. Giữ nguyên raw/lịch sử; docs-only
là giới hạn lượt ghi nhận trước, không cấm runtime slice owner đã giao.

**Gate toàn hệ thống trước mọi lượt quét/đọc mẫu thực mới, corpus và vòng E2E
theo mẫu:** #41 phải được nghiệm thu cả chuẩn DB/contract đã duyệt, cutover mọi
consumer bị ảnh hưởng và proof luồng thật; bảng mapping/local Draft không đủ.
Verification riêng #41 khi được giao có thể dùng input tổng hợp/kiểm soát và
DB/profile cô lập, không phụ thuộc khảo sát corpus owner đang bị gate. Sau gate,
khi được giao chạy mẫu, thiếu mapping từng file thì giữ pending/ghi #39, tiếp
tục file đã rõ. Không tắt production Scan/Upload; quyền runtime đã chốt là lệnh owner riêng.

**Người chết — owner 21/10/2026, đã chốt nghiệp vụ và giao runtime hẹp:**
- `Nơi chết` và cư trú cuối dùng một `dia_chi` Người hiện có, không thêm
  trường; không chọn ngầm khi giá trị mâu thuẫn. Ba loại đúng nguyên văn:
  `Trích lục khai tử`, `Trích lục khai tử (bản sao)`, `Giấy chứng tử`;
  `Giấy chứng tử (bản sao)` nguồn quy về `Giấy chứng tử`.
- Số giữ nguyên giá trị, nhãn ngoài số. Ngày cấp của chính giấy quyết định
  mốc tên cơ quan; giữ loại đơn vị xã/phường/thị trấn, không ép xã, không đổi
  sang hiện hành hoặc tự bù lịch sử chưa xác nhận.
- Mỗi văn bản độc lập: **không đề xuất bổ sung, không tự ghép giữa văn bản**,
  kể cả cùng bộ; không mượn trường thiếu hoặc chọn bản đầy nhất/mới nhất.
  Không gợi ý sinh/chết/giấy tờ Người từ `Đơn xin xác nhận`, không đi vòng
  qua inferred/normalized. Đây không xóa raw/history, liên kết Case/ID đã
  có hoặc cấm địa chỉ chung rõ phạm vi trong **cùng** văn bản.
  Luật này không cấm gom ID theo điểm neo ở policy bên dưới; không đồng nghĩa
  cho phép mượn trường thiếu giữa văn bản hoặc tự đổi Hồ sơ đã lưu.
- Thiếu ngày chết chỉ là không có thông tin: giữ null/rỗng, điền độc lập các
  trường có căn cứ được phép; không chặn Người vì thiếu ngày/giấy, tự coi
  còn sống, bịa ngày/01/01, Boolean hoặc trạng thái mới.
- Không đổi câu Word/trường tĩnh/placeholder. Runtime workstream Người chết
  **BUILT bounded**, actual proof implementer-run fresh+migrated DB/Word;
  #41 OPEN/chưa nghiệm thu toàn bộ, #42 chưa duyệt model, gate chung ĐÓNG/
  không đọc mẫu mới. Số giấy lưu thật, index không UNIQUE, identity theo ID
  chọn rõ/row_id chính hồ sơ, không auto lookup theo số/tên hoặc ghép giữa
  file. Snapshot không borrow master khi đã có key, kể cả null.
- **Policy owner 21/10 mới nhất, chưa triển khai:** tự gom Người cùng ID khi
  **tên + số giấy tờ đồng thời giống nhau**; ngày cấp/địa chỉ khác vẫn cùng ID.
  Chỉ trùng một trường không đủ; đổi tên hoặc số thì chấp nhận ID khác.
  Tài sản gom theo **serial** giữ nguyên văn. Không đòi user bấm liên kết hoặc
  chọn phiên bản. Tìm Người để xem các Hồ sơ đã làm. Một bảng Người cho sống/chết.
  Khi lấy vào Hồ sơ mới mặc định bộ mới nhất; Hồ sơ đã lưu không tự cập nhật.
  **Owner 22/10:** bộ mới nhất theo Hồ sơ được lưu gần nhất, chỉ nguồn `done`,
  loại `draft`; không theo ngày giấy hoặc độ đầy đủ. Tên đối chiếu không phân
  biệt dấu/hoa-thường, giữ nguyên tên gốc; không tự mở thành so gần đúng tùy ý.
  Thiếu điểm neo không gom và không chặn lưu Nháp. ID trùng cũ giữ nguyên,
  không tự hợp nhất, lấy bộ cuối cùng; lịch sử user xử lý. Cùng serial vẫn gom
  cùng ID dù khác thửa, không thêm điều kiện thửa/tờ. Nhân bản toàn bộ nội dung.
  Cách giữ/đổi ID khi bổ sung neo, hai bước ghi và schema đang rà soát; chưa code.
  Không tự ghép trường giữa nhiều Hồ sơ/văn bản.
  Policy gợi ý CCCD/user chọn/bỏ qua tạo ID mới và kho “thông tin liên kết”
  trước đó đã bị thay thế; [#44](../../backlog/story-person-cccd-suggestion-link.md)
  chưa sẵn sàng triển khai theo tiêu chí cũ. Không khôi phục CCCD UNIQUE/chặn
  luồng. Runtime cũ chưa thực hiện điểm neo mới; giữ Case links/raw/history/
  snapshot null. #41 OPEN/gate mẫu ĐÓNG, #42 độc lập.
  [Quyết định](../../decisions/decision-owner-entity-anchors-case-snapshots-20261021.md).
  [Làm rõ 22/10 và yêu cầu dừng code](../../decisions/decision-owner-data-entry-save-rules-20261022.md).
- **Địa chỉ cũ–mới — owner kết phiên 21/10:** tạm thời giữ cách hiện tại.
  Chưa chốt mô hình mới; đề xuất danh mục/quan hệ chuyển đổi và mã tham chiếu
  từ các trường địa chỉ chưa được duyệt. Không đổi cấu trúc/hành vi theo đề
  xuất đó, không tự cập nhật địa chỉ trong Hồ sơ đã lưu.
- **Nguyên tắc bền vững cho task hiện tại/tương lai:** engine xử lý dữ liệu,
  không quyết định thay người dùng chịu trách nhiệm pháp lý. Không tự thêm
  business/UX gate hoặc đổi hành vi chưa báo và được owner duyệt; UX chưa rõ
  ghi issue để owner chọn, không tạo gate mới. Ưu tiên thiết kế tối thiểu:
  80% kết quả tốt hơn 90% cộng 10 thao tác, không đánh đổi tính đúng/nguồn.
  Các blocker hiện có chưa kiểm kê/xác minh; không claim audit hoặc tự gỡ
  kiểm tra tên/ngày/revision/khóa hồ sơ hay wire/security/FK/atomicity.

**Một Người nhiều giấy tờ và nhiều địa chỉ** là
[#42 riêng](../../backlog/story-person-multiple-identities-addresses.md).
Model hiện hành một bộ giấy tờ/một địa chỉ không phải hỗ trợ đa trị; model,
schema/migration/chọn dùng/extraction/export tương lai chưa chọn. Child records
trong Người có thể được thiết kế sau; trong phạm vi #42 hiện tại không thêm đối tượng thứ tư;
bảng pháp nhân tương lai là hướng riêng phải thiết kế/chốt sau, không bị quy tắc #42 này cấm;
không tự đặt #42 làm prerequisite #41 hoặc gate mẫu.
Lý do và supersession: [quyết định owner](../../decisions/decision-owner-upload-field-standardization-20261019.md).

**Bổ sung owner 20/10/2026 — pháp nhân, cụm trường phụ website và quan hệ:**

- **Pháp nhân không thuộc Người.** Không thêm loại pháp nhân vào Person, không
  tự phân loại tổ chức thành thể nhân. Policy **người dùng nhập tay** chung
  có ngoại lệ ngân hàng thế chấp app tự lấy bên dưới; hướng bảng riêng tương
  lai **chưa duyệt schema/bảng/cột/migration hay triển khai**; nếu làm sau, đây là schema riêng
  phải thiết kế/chốt riêng. Phạm vi ba đối tượng hiện tại không đổi; bảng pháp
  nhân tương lai là hướng owner cho phép, không bị quy tắc hiện tại cấm. Hồ sơ
  thế chấp là trường hợp mặc định có pháp nhân; loại khác ít xảy ra. Sự có mặt
  đó không đồng nghĩa đã biết hoặc được phép tự điền tên ngân hàng/chi nhánh/
  người đại diện hoặc coi một bên là mặc định; chỉ dùng dữ kiện nguồn nêu rõ.
  Pháp nhân khác không được âm thầm bỏ mất hoặc tự xếp loại; giữ nguồn và để
  người dùng nhập tay. R05 alias và D04 lời phức tạp có lựa chọn nhập/sửa tay
  riêng bên dưới; không mở thành fallback cho mọi dữ liệu chưa rõ nghĩa.
- **Cụm trường phụ website là ngoại lệ hẹp có điều kiện.** Khi chọn cụm (phức
  tạp, không lặp lại, thuộc một ô nhập của một website cụ thể) phải xác định
  website/phạm vi ô, nghĩa nghiệp vụ, lý do không tách, kiểu lưu và
  provenance; ưu tiên tái dùng trường canonical Người/Tài sản/Hồ sơ đã biết;
  chỉ hỏi owner khi có quyết định nghiệp vụ thực sự chưa rõ, chi tiết kỹ thuật
  do implementation sở hữu theo contract/rule đã duyệt. Không dùng `ghiChu` chung
  hoặc JSON bag chung thay trường; raw capture chỉ là provenance, không thay
  trường nghiệp vụ. Không tự đặt canonical key/tên/kiểu/nhóm/storage; không tự
  coi mọi editor là block; chỉ tự lấy cụm ngân hàng trong ngoại lệ đã chốt. Cụm có thể là
  trường riêng theo ô website; phần tái dùng được vẫn map canonical, không mặc
  định coi cụm là dữ liệu chưa map/orphan.
- **Quan hệ Người–Tài sản–Hồ sơ:** nhiều người/nhiều tài sản chưa chọn model,
  cardinality, quan hệ/FK hay schema. D06+D07 chuyển một
  [#43 riêng](../../backlog/spike-case-people-assets-relationships.md), làm ngay
  sau rõ các ô Nam Định §7, không chờ toàn #41 xong/#42. #41 nhận đáp án cho
  cutover quan hệ; không coi model trước đã duyệt hoặc đổi gate.
- Hiện Person/Asset/parties chưa canonical cutover; `nguoi_yeu_cau`/`duong_su`/
  `taisan` vẫn là output trình bày; chưa có bảng/key canonical pháp nhân.
  Projection requester text persist hợp lệ qua JSON hiện có, không đồng nghĩa
  normalized cutover. Bounded proof/fresh bank-auto review CLEAN; raw/provenance giữ nguyên.

**Đáp án #43 — owner 20/10/2026, phạm vi requester Nam Định/Upload:** bao gồm
cá nhân sống thuộc Bên A, Bên B, đại diện theo ủy quyền; không đưa người chết,
công chứng viên, nhân viên vào requester output. Không xóa Person chết hoặc
đối tượng Hồ sơ thừa kế/Stage/raw/snapshot/lịch sử/metadata nhân sự. Cá nhân
thông thường dùng chuẩn R06, một lần mỗi identity xác nhận theo thứ tự nguồn;
không lookup/firstperson/ưu tiên B/prose. R05 alias nhập tay, D04/D08 không tự
điền lời phức tạp; không mở fallback tay cho mọi gap.

Ngân hàng trong hợp đồng thế chấp hiện **cả cụm**, không đưa tổ chức vào Người.
**BANKMODE đã chốt “app tự lấy”**: chỉ thế chấp, toàn cụm ngân hàng/chi nhánh/
định danh/địa chỉ/đại diện/ủy quyền có nguồn tại vị trí nguồn trong requester
đầy đủ; không lặp đại diện đã trong cụm. Cá nhân khác chỉ dữ kiện chuẩn.
`web_form.nguoi_yeu_cau` → payload JSON → queue → editor là persistence
projection hợp lệ; không key canonical/bảng/entity mới hoặc blanket raw editor.
Giữ raw/person arrays/provenance/history. Q1/Q2/BANKMODE đủ đáp án, #43 bàn
giao #41; bounded proof/fresh review CLEAN; #43 phân tích done, không toàn normalized/#41 complete.

**A/B đã chốt:** ủy quyền A=người ủy quyền/B=người được ủy quyền; một bên
không gán A/B; hai nguồn trái nhau giữ conflict và xác nhận phần nhóm, không
tự chọn nguồn thắng hoặc thu hẹp requester. Chữ “nhận” không universal regex.
Requester không lọc theo tag A/B đã gán: cá nhân sống của văn bản một bên/
đại diện ủy quyền vẫn vào output khi nhóm không gán hoặc conflict.

W05 giữ loại đất có tài sản/nhà dù thiếu mẫu/rule chi tiết, không tự tạo schema;
A10 chỉ giữ xe/sổ tiết kiệm/bảo hiểm ở nhận diện/pending structured. A09 đã chốt
A: không residual field/block; asset editor chỉ render canonical/placeholder,
raw/history retained không auto-fill. Toàn đoạn tài sản ghép từ dữ kiện chuẩn
không đồng nghĩa lời dư chưa map; [SOT §7](../upload_lab/nam-dinh-website-sot.md#owner-review)
có trường thật/ví dụ tổng hợp. **Owner 20/10/2026 chốt chỉ dùng placeholder và trường tĩnh**; không
mở trường tầng 2 động/tính toán, persisted text canonical từ suy ra, engine
công thức hoặc framework điều kiện. Đề xuất hai tầng chỉ là lịch sử chưa triển
khai. Quyền có điều kiện cho cụm **text tĩnh** đã duyệt khác giữ nguyên; **A09 đã chốt A**
không residual field, chỉ render canonical/placeholder. Dữ kiện nguồn tĩnh tách
khỏi định dạng output. Policy đích không là runtime đã đổi.

**Kết quả audit catalog 19/10/2026:** báo cáo ổn định
`D:\testcase\BAO_CAO_KHAO_SAT.md` đã liệt kê trường nền Người/Tài sản/Hồ sơ,
kiểu, đích wire/DB, thứ tự/cụm và nguồn thẩm quyền trong phạm vi catalog nền.
**Catalog đó chưa đủ bộ trường Hồ sơ/Upload xuyên module** và không chứng minh
mọi biến thể đã có mapping hoặc code tuân thủ hết; #41 đóng phần thiếu này.
Serial GCN
nguyên văn/rỗng/trùng **đã được owner chốt**; validator/ràng buộc DB/projection
khác chuẩn là [gap implementation tĩnh #40](../../backlog/bug-stage-raw-gcn-serial-contract.md),
không phải câu hỏi duyệt lại field. Chưa tái hiện runtime trong lượt này.
Ngày quy ước master + snapshot giữ `YYYY` theo #6 không tự là bug; ngày lập
hồ sơ optional ở wire versus default DB phải phân biệt tầng/ngữ nghĩa.
Global UNIQUE/lookup số Người cũ đã cutover trong workstream Người chết
21/10. Thiết kế CCCD UNIQUE sau đó đã bị owner thay bằng gợi ý/liên kết
không chặn; không còn prerequisite lưu loại để làm unique index.
Xem `contracts/entities.md` §8.3 và #44 cho hành vi chưa triển khai.

Owner xác nhận 15/10/2026: bộ trường và định dạng DB đã duyệt là chuẩn đích;
engine phải tuân theo hoặc ánh xạ tường minh tới chuẩn đó. Trước khi triển khai,
chốt bộ trường, kiểu dữ liệu, định dạng, cách nhóm và nơi lưu cho chức năng nhận.
Cùng một đối tượng dùng cùng chuẩn đích trong
suốt luồng; điều này không buộc raw OCR phải mang schema DB và không tạo schema
dùng chung hay Case liên module. Giữ riêng và nguyên vẹn giá trị gốc (raw) cùng
vị trí nguồn. Chuẩn hóa giá trị đầu ra theo quy tắc của từng trường; trường nào
yêu cầu nguyên văn thì giữ nguyên. Mục đích là tránh cùng thông tin cho kết quả
khác nhau giữa các trường hoặc khiến trường cần thiết không điền/lưu được, mà
không tự thêm quy tắc ngoài những gì đã chốt. Đặt dữ liệu đúng người, tài sản
hoặc cụm đất; không tạo field riêng hay nhét dữ liệu vào ghi chú để né bộ trường
đã chốt. Thiếu căn cứ thì để trống và gắn cờ theo quy ước. Nếu cần field mới,
đề xuất và chốt trước khi làm. Dữ liệu đúng cấu trúc chưa đồng nghĩa đã được
xác nhận hoặc được tự ghi DB. Tên nghiệp vụ như `ten` và tên cột đã ánh xạ như
`ho_ten` giữ đúng ánh xạ; thời hạn đất thuộc cụm và tài sản tương ứng, không đổ
vào `thoi_han` chung.

Ngày phải lưu và hiển thị đúng độ đầy đủ của dữ liệu nhập: năm riêng giữ năm,
ngày đầy đủ giữ ngày đầy đủ. Ngày quy ước cho tính toán nằm riêng trong bước
tính, không ghi đè giá trị nhập hoặc trở thành ngày đã biết.

Đây là nguyên tắc cho quyết định đầu ra, không nâng `IdentityEvidence` ở §4.1
từ Draft thành contract xuyên sản phẩm.

## 5. Kiến trúc hiện tại và đích

### Hiện tại

- Nhánh `consolidate/monorepo` chứa snapshot module, Electron shell và sidecar
  FastAPI loopback.
- `notary_v2` và `upload_lab` có runtime; `notaryoffice` mới có thiết kế.
- Repo nguồn Zalo là `D:\zalo-intake`; `zalo/` ở đây là snapshot một chiều.
- Contract đã duyệt nằm trong [`contracts/`](../../../contracts/README.md).

### Đích

```text
Electron renderer
  → Electron main
  → DesktopCommand có version
  → Python sidecar
  → adapter của module
  → engine nghiệp vụ và database do module sở hữu
```

Thứ tự bắt buộc: quyết định → spec/contract → nền tảng → chuyển nghiệp vụ →
kiểm chứng → cutover. POC chỉ là bằng chứng; chạy được không đồng nghĩa production
contract đã được duyệt.

Database nghiệp vụ chung là đích sau khi model ổn định. Dùng chung DB không cho
module này ghi vào bảng do module khác sở hữu. Engine DB vật lý cuối chưa chốt.

## 6. Công nghệ dùng chung

| Việc | Lựa chọn hiện tại | Lưu ý |
|---|---|---|
| Desktop shell | Electron | Vỏ ứng dụng tích hợp trên nhánh default `consolidate/monorepo` |
| Backend | Python + FastAPI sidecar | Loopback; shell không chứa nghiệp vụ |
| DB hiện tại | SQLite theo module | DB chung và engine đích chưa duyệt |
| OCR giấy tờ | Qwen-VL-OCR qua DashScope | Ảnh chỉ gửi cloud tại đường được phép |
| `.docx` | `python-docx` | Giữ thứ tự đoạn và bảng |
| `.doc` cũ | Windows IFilter | Khả năng đọc khi Word đang mở còn phải đo |
| PDF | PyMuPDF | `notary_v2` |
| Excel | `openpyxl` | `upload_lab` |
| Điều khiển portal | Playwright, Chromium headed | Người dùng tự bấm Lưu |

Muốn chọn công nghệ khác cho cùng một việc phải ghi tại cấp spec bị ảnh hưởng:
phạm vi, lý do, phương án bỏ, cách kiểm chứng và tác động khi hợp nhất.

### Ràng buộc để sau này gộp không phải viết lại

- Không dùng `rowid` ẩn, kiểu dữ liệu lỏng riêng của SQLite hoặc số/ngày lưu
  dạng text tự do trong logic nghiệp vụ; ưu tiên SQLAlchemy/SQL chuẩn.
- Record có thể đi qua nhiều module phải dùng UUID hoặc tiền tố nguồn, không
  dùng số tự tăng cục bộ làm khóa nghiệp vụ chung.
- Ngày đầy đủ lưu ISO-8601; năm riêng vẫn giữ YYYY, không tự thêm ngày/tháng. Thời điểm có múi giờ hoặc quy ước rõ.
- Tài sản dùng tên field chung: `so_serial`, `so_vao_so`, `so_thua_dat`,
  `so_to_ban_do`, `dia_chi`, `ngay_cap`, `co_quan_cap`, `dien_tich`.
- Không hard-code đường dẫn tuyệt đối, secret hoặc môi trường; cấu hình qua
  biến môi trường/file cấu hình được bảo vệ.

## 7. Quyền riêng tư và an toàn

- Dữ liệu CCCD/tài sản thuộc phạm vi bảo vệ dữ liệu cá nhân.
- Zalo chỉ dùng tài khoản chung của văn phòng, nhóm mà tài khoản đó tham gia và
  tin riêng gửi tới chính tài khoản văn phòng.
- Không đọc tài khoản hoặc tin riêng của nhân viên.
- Đích vận hành Zalo là server; giai đoạn phát triển đầu chạy repo local riêng.
- Không ghi PII, cookie, secret, ảnh giấy tờ hoặc raw OCR vào log rộng.

Mặc định hệ thống chạy trong LAN. Chỉ các đường dưới được gọi Internet; thêm
đường mới phải hỏi owner và cập nhật spec cấp hệ thống:

| Đường ra | Dữ liệu | Owner |
|---|---|---|
| DashScope/Qwen OCR | Ảnh giấy tờ tại luồng được duyệt | `notary_v2` |
| DashScope/Qwen OCR cho ảnh Zalo | Ảnh do module Zalo đang giữ tạm | `zalo` |
| Portal CSDL công chứng | Dữ liệu hồ sơ người dùng đã kiểm tra | `upload_lab` |
| Server Zalo | Tin/ảnh của tài khoản chung văn phòng | `zalo` |
| Bando — tải danh mục/bảng xã và tỉnh | Dữ liệu hành chính công khai; không gửi hồ sơ hoặc địa chỉ khách hàng | `notary_v2` |

Owner cho phép lấy Bando trong chat 03–04/10/2026. Đường này chỉ phục vụ
cập nhật kho hành chính bằng CLI; tra cứu dùng kho cục bộ, không gọi website.
Cách lưu nguồn, bổ sung lịch sử và mở rộng nằm tại
[`administrative-timeline.md`](administrative-lookup.md#timeline); luật tra
tại [`shared/administrative-lookup.md`](administrative-lookup.md#lookup).

Agent máy trạm `notaryoffice` không được gọi Internet, chỉ gửi về Hub trong
LAN. Ảnh CCCD gửi tới OCR nước ngoài thuộc phạm vi bảo vệ dữ liệu cá nhân theo
Nghị định 13/2023 `[CONFIRM]`; đây là ngoại lệ có chủ ý, không phải quyền mở
thêm cloud.

### Còn mở

- Engine DB chung và migration vật lý.
- Phép đo máy thật A1/A3/A4 thuộc spec `notaryoffice`.
- Contract Zalo MIN-92 hiện vẫn Draft theo chính file contract; không code như
  contract production trước khi owner duyệt/publish.
- `IdentityEvidence`/`ConversionEnvelope` xuyên sản phẩm vẫn là Draft. MIN-61
  giữ kết luận `ITERATE`: MarkItDown chỉ là POC cho tới khi hai consumer kiểm
  cùng một golden dataset có cùng hash và owner duyệt chuyển sang `ADOPT`.

## Tách và dùng chung

Không tự tạo shared core trước khi có ít nhất hai bên dùng chứng minh cùng quy ước. Lõi tra địa chỉ là ngoại lệ đã được owner duyệt dùng chung ngay từ đầu; module mới vẫn cần quy ước giao tiếp được duyệt. Quyền gọi cloud của nguồn Zalo cũ chỉ là ranh giới nghiên cứu, không phải quyền nối Zalo vào luồng chính đang tách riêng.
