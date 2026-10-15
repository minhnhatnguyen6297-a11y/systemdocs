# Quy tắc dữ liệu và ranh giới hệ thống

**Cập nhật:** 15/10/2026. Quy tắc có hiệu lực được viết tại đây; mục ghi Draft vẫn chưa được duyệt.

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
