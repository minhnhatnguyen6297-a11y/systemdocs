# Spec hệ thống công chứng

**Trạng thái:** Active · **Cập nhật:** 15/10/2026 · **Phạm vi:** toàn hệ thống

Trang này giữ phần dùng chung cho nhiều module. Chi tiết thuộc một module hoặc
feature phải ghi ở thư mục con gần nhất, không chép lại tại đây.

Đọc trang này trước để nắm nền sản phẩm và các khái niệm chung. Sau đó mở
[sổ tay sản phẩm theo màn hình](./product-overview.md) để tìm UI, tài liệu và
việc đang mở. Các spec module bên dưới mới quyết định hành vi chi tiết.

**Ghi chép lịch sử — gom nhánh 05/10/2026, TASK-6:** lúc đó tài liệu regex và địa chỉ cùng nằm trên
`consolidate/monorepo`; tên các file `.agents/` đã dọn được liệt kê tại
[`removed-agents-files.md`](../../_bmad-output/archive/removed-agents-files.md); nội dung các file gốc không còn trong repo.
Quyết định: giữ trạng thái duyệt của từng tài liệu, không coi thao tác gom/commit
là nghiệm thu tính năng. Tại sao: spec địa chỉ đã duyệt nhưng runtime chưa theo
v2; bộ quy tắc regex từ 20 mẫu còn chờ duyệt và chưa là spec triển khai mới.

## 1. Tầm nhìn và mục tiêu

Hệ thống giảm ba việc nhập lại dữ liệu:

1. `notary_v2` soạn hồ sơ mới từ giấy tờ và dữ liệu người dùng xác nhận.
2. `upload_lab` đọc kho Word cũ và hỗ trợ nhập lên CSDL công chứng tỉnh.
3. `notaryoffice` theo dõi hồ sơ đang ở đâu và đang chờ việc gì.

### Sản phẩm dành cho ai và giúp việc gì

Người dùng chính là chuyên viên và nhân viên văn phòng công chứng. Sản phẩm
nhằm giảm việc gõ lại thông tin từ giấy tờ, hồ sơ Word và sổ Excel; người dùng
vẫn kiểm tra dữ liệu trước khi xác nhận hoặc lưu. Đây là ba kết quả thuộc ba
module riêng, không phải một dây chuyền tự nối dữ liệu:

| Việc | Kết quả và hiện trạng | Nguồn |
|---|---|---|
| Soạn hồ sơ mới | `notary_v2` nhận giấy tờ/chữ, tạo gợi ý để người dùng kiểm tra, lập quan hệ và xuất Word; đang phát triển. | [Spec notary_v2](./notary_v2/README.md) |
| Xử lý hồ sơ Word cũ | `upload_lab` đọc Word, đối chiếu Excel và điền sẵn form portal; người dùng tự kiểm tra, tự bấm Lưu; đang phát triển. | [Spec upload_lab](./upload_lab/README.md) |
| Theo dõi công việc văn phòng | `notaryoffice` dự kiến gom dấu vết thành ứng viên để người dùng xác nhận; hiện là thiết kế Draft, chưa có chương trình chạy. | [Spec notaryoffice](./notaryoffice/README.md) |

### Câu chuyện công việc

- Khi soạn một hồ sơ mới, chuyên viên đưa giấy tờ vào `notary_v2`, xem và sửa
  gợi ý, đưa thông tin vào Stage nháp rồi bấm `Cập nhật` để lưu. Sau đó họ sắp
  quan hệ trên Diagram và lưu sơ đồ riêng trước khi xuất Word.
- Khi xử lý kho Word cũ, nhân viên dùng `upload_lab` để quét tài liệu, đối
  chiếu sổ Excel và chuẩn bị form portal. Đây là công việc riêng với kho cũ;
  người dùng tự kiểm tra và lưu trên portal.
- Việc biết hồ sơ đang ở đâu thuộc hướng `notaryoffice` dự kiến. Thiết kế này
  chưa chạy và chưa có nghĩa là hồ sơ từ hai module kia tự chuyển sang đây.

### Khái niệm dùng chung

| Từ | Nghĩa và ví dụ | Phạm vi, nguồn |
|---|---|---|
| Hồ sơ | Một đơn vị công việc trong module, ví dụ hồ sơ đang soạn ở `notary_v2` hoặc ứng viên theo dõi ở `notaryoffice`. Hai nơi không mặc định dùng chung một hồ sơ hay mã hồ sơ. | Theo từng module; [ranh giới hệ thống](./README.md#3-ranh-giới-sản-phẩm), [notaryoffice](./notaryoffice/README.md) |
| Người, Tài sản | Dữ liệu được giữ trong hồ sơ soạn mới. CCCD, số giấy chứng nhận, thửa/tờ và số công chứng giúp đối chiếu; tự chúng không phải mã hồ sơ chung và không đủ để tự gộp hồ sơ. | [Stage](./notary_v2/stage.md), [định danh chung (mục 7)](../../contracts/entities.md) |
| Input | Nơi nhận file hoặc chữ và tạo gợi ý cho hồ sơ mới; ví dụ thông tin OCR đọc từ ảnh CCCD. Nhận gợi ý đưa dữ liệu vào Stage nháp, chưa lưu. | `notary_v2`; [spec Input](./notary_v2/input/README.md), [chuỗi dữ liệu](#4-chuỗi-dữ-liệu-chung) |
| Stage | Bảng Người/Tài sản của hồ sơ soạn mới. Sửa trên màn hình là bản nháp; chỉ thao tác `Cập nhật` thành công mới lưu Stage. | `notary_v2`; [spec Stage](./notary_v2/stage.md) |
| Pool | Danh sách người đã lưu trong Stage nhưng chưa được đặt lên Diagram. Ví dụ kéo một người từ Pool vào vị trí trên sơ đồ. Pool được tính từ Stage và Diagram, không phải kho riêng. | `notary_v2`; [spec Pool](./notary_v2/pool.md) |
| Diagram | Nơi xếp người vào vai trò/quan hệ của hồ sơ. Diagram có bản nháp riêng; `Lưu sơ đồ` mới lưu thay đổi. Xuất Word dùng Stage và Diagram đã lưu, nhưng bản Word chỉ là văn bản được tạo, không chứng minh việc pháp lý đã hoàn tất. | `notary_v2`; [spec Diagram](./notary_v2/diagram/README.md), [Xuất Word](./notary_v2/word-output.md) |
| Bản nháp | Từ này phải đọc theo đúng nơi dùng: Stage/Diagram có bản sửa chưa lưu; Draft Case của `notaryoffice` là ứng viên chưa xác nhận; `draft` của hồ sơ `notary_v2` là trạng thái hồ sơ được spec cho phép xóa. Ba nghĩa này không thay thế nhau. | [Stage](./notary_v2/stage.md), [Diagram](./notary_v2/diagram/README.md), [notaryoffice](./notaryoffice/README.md), [quy tắc xóa](./notary_v2/README.md#6-câu-hỏi-và-lịch-sử-module) |
| Mẫu Word | File mẫu dùng khi xuất văn bản từ hồ sơ mới; không phải kho Word hồ sơ cũ mà `upload_lab` đọc. | [Xuất Word](./notary_v2/word-output.md), [upload_lab](./upload_lab/README.md) |
| `record_id` | Mã bản ghi Upload dùng để gắn và theo dõi tab đang chuẩn bị upload với hồ sơ tương ứng; không phải mã hồ sơ dùng chung giữa các module. | `upload_lab`; [phiên portal](./upload_lab/portal-session.md), [flow upload](./upload_lab/README.md#5-hàng-đợi-và-upload) |

Đích dài hạn là một ứng dụng, giao diện chung và database nghiệp vụ chung.
Ba module vẫn giữ owner riêng cho dữ liệu của mình. `zalo` là nguồn thu nhận kỹ
thuật có runtime, phiên và database riêng; nó không phải module nghiệp vụ thứ tư.

## 2. Nguyên tắc chung

- Không bắt người dùng nhập lại dữ liệu đã tồn tại.
- Máy đề xuất; người có thẩm quyền xác nhận.
- Rule tất định (quy tắc cho kết quả cố định khi đầu vào giống nhau) trước, AI
  sau, người quyết định cuối.
- Không ép chuyên viên đổi thói quen làm việc đang cần cho nghiệp vụ.
- Dữ liệu ở lại văn phòng; gọi cloud chỉ tại điểm đã được duyệt.
- Không tự động hóa phán quyết pháp lý.
- Không giám sát nhân viên, quay màn hình hoặc ghi phím.
- Không nối hai module trước khi contract được hai bên duyệt.
- Đầu ra bóc tách nghiệp vụ theo bộ trường, cấu trúc, kiểu, định dạng, nhóm
  và đích lưu đã chốt cho chức năng nhận dữ liệu; xem
  [nguyên tắc đầu ra](../decisions/decision-extraction-output-data-contract.md).

**Tại sao:** Trong công chứng, một lần gán sai làm mất lòng tin nhiều hơn nhiều
lần gán đúng. OCR, suy luận và điểm tin cậy không được tự trở thành sự thật.

Ở đây, **contract** là quy ước để các phần thống nhất cách gửi và nhận dữ liệu.

## 3. Ranh giới sản phẩm

| Phần | Sở hữu | Không sở hữu |
|---|---|---|
| `notary_v2` | Intake, Stage, Pool, Diagram, nghiệp vụ hồ sơ, xuất Word | Kho Word cũ; theo dõi vận hành văn phòng |
| `upload_lab` | Đọc Word cũ, audit Excel, chuẩn bị upload portal | Soạn hồ sơ mới; tự bấm Lưu trên portal |
| `notaryoffice` | Evidence, Draft Case và trạng thái vận hành dự kiến | Phán quyết pháp lý; dữ liệu đã xác nhận của module khác |
| `zalo` | Phiên Zalo, media tạm, Qwen OCR, gói raw chưa ACK | Parser nghiệp vụ, Stage, người/tài sản đã xác nhận |
| `shell` | Cửa sổ Electron, navigation, lifecycle và gọi sidecar | Nghiệp vụ hoặc quyền ghi DB của module |

`notary_v2`, `notaryoffice` và `upload_lab` cùng nói về hồ sơ ở ba thời điểm,
nhưng không mặc định dùng cùng record. CCCD định danh người; GCN/thửa-tờ giúp
đối chiếu tài sản; chúng không phải khóa chính của Case và không đủ để tự gộp.

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
| `CONFIRMED` | Dữ liệu đã được người có quyền xác nhận | Chỉ owner nghiệp vụ được ghi |

Nói gọn: giữ giấy tờ gốc, lấy phần chữ đọc được, chuẩn hóa, tạo suy đoán khi
cần, rồi để người có quyền xác nhận; máy không tự biến chữ đọc được thành dữ
liệu đã xác nhận.

Không được đi thẳng từ OCR/LLM tới dữ liệu `CONFIRMED`. Giá trị thiếu bằng
chứng phải để trống hoặc cảnh báo, không tự điền.

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
- Contract đã duyệt nằm trong [`contracts/`](../../contracts/README.md).

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
- Ngày lưu ISO-8601; thời điểm có múi giờ hoặc quy ước rõ.
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
[`administrative-timeline.md`](./notary_v2/administrative-timeline.md); luật tra
tại [`shared/administrative-lookup.md`](./shared/administrative-lookup.md).

Agent máy trạm `notaryoffice` không được gọi Internet, chỉ gửi về Hub trong
LAN. Ảnh CCCD gửi tới OCR nước ngoài thuộc phạm vi bảo vệ dữ liệu cá nhân theo
Nghị định 13/2023 `[CONFIRM]`; đây là ngoại lệ có chủ ý, không phải quyền mở
thêm cloud.

## 8. Câu hỏi và lịch sử cấp hệ thống

### Đã chốt

- Electron là shell đích, owner chốt 14/09/2026.
- Một hệ thống, UI chung và database nghiệp vụ chung là đích; chưa tự ý gộp khi
  contract và ownership chưa rõ.
- Zalo giữ ảnh và gọi Qwen tại nơi có ảnh; máy chính chỉ nhận raw OCR, trạng
  thái và nguồn, không nhận ảnh.
- Không tạo shared core trước khi ít nhất hai consumer chứng minh cùng contract.
  **Ngoại lệ (Owner 05/10/2026, TASK-2):**
  [lõi tra cứu tên đơn vị hành chính](./shared/administrative-lookup.md) là
  shared core ngay từ đầu. *Tại sao:* mọi ô địa chỉ, tool tra cứu và module
  sau này cần cùng một câu trả lời từ cùng một kho; tách riêng từng nơi sẽ lệch.
  Module ngoài `notary_v2` chỉ gọi khi có contract được duyệt.

### Còn mở

- Engine DB chung và migration vật lý.
- Phép đo máy thật A1/A3/A4 thuộc spec `notaryoffice`.
- Contract Zalo MIN-92 hiện vẫn Draft theo chính file contract; không code như
  contract production trước khi owner duyệt/publish.
- `IdentityEvidence`/`ConversionEnvelope` xuyên sản phẩm vẫn là Draft. MIN-61
  giữ kết luận `ITERATE`: MarkItDown chỉ là POC cho tới khi hai consumer kiểm
  cùng một golden dataset có cùng hash và owner duyệt chuyển sang `ADOPT`.

## 9. Nguồn và cách cập nhật

- Contract máy đọc: [`contracts/`](../../contracts/README.md).
- Định danh chung: [`contracts/entities.md`](../../contracts/entities.md).
- Code là bằng chứng về hiện trạng chạy thật; spec quyết định hành vi phải có.
- Backlog giữ task, tiêu chí hoàn thành và quyết định; `.agent/tasks/` là tiến độ
  lịch sử. Không dùng ghi chép Linear cũ thay task đang có hiệu lực.
- **TASK-1 (05/10/2026):** `backlog/docs/` chỉ chứa con trỏ tới file trong
  `_bmad-output/specs/` (xem doc-39 inventory); nội dung SOT vẫn ở file gốc. Quyết định
  kiến trúc trích từ spec đã ghi thành `backlog/decisions/` decision-22…39.
- **Owner 05/10/2026, TASK-7:** tiếp tục từ `D:\systemdocs`, nhánh
  `consolidate/monorepo`. *Tại sao:* một bộ spec/task chung sau khi gom các
  worktree. Danh sách tên file `.agents/` đã dọn nằm tại
  [`removed-agents-files.md`](../../_bmad-output/archive/removed-agents-files.md); nội dung file gốc không còn trong repo.
  Việc gom không đổi yêu cầu sản phẩm hoặc duyệt các quy tắc regex còn Draft.

Khi thay đổi chỉ ảnh hưởng một module hoặc feature, cập nhật spec con. Chỉ sửa
trang này khi nhiều module cùng bị ảnh hưởng.
