# Spec hệ thống công chứng

**Trạng thái:** Active · **Cập nhật:** 29/09/2026 · **Phạm vi:** toàn hệ thống

Trang này giữ phần dùng chung cho nhiều module. Chi tiết thuộc một module hoặc
feature phải ghi ở thư mục con gần nhất, không chép lại tại đây.

## 1. Tầm nhìn và mục tiêu

Hệ thống giảm ba việc nhập lại dữ liệu:

1. `notary_v2` soạn hồ sơ mới từ giấy tờ và dữ liệu người dùng xác nhận.
2. `upload_lab` đọc kho Word cũ và hỗ trợ nhập lên CSDL công chứng tỉnh.
3. `notaryoffice` theo dõi hồ sơ đang ở đâu và đang chờ việc gì.

Đích dài hạn là một ứng dụng, giao diện chung và database nghiệp vụ chung.
Ba module vẫn giữ owner riêng cho dữ liệu của mình. `zalo` là nguồn thu nhận kỹ
thuật có runtime, phiên và database riêng; nó không phải module nghiệp vụ thứ tư.

## 2. Nguyên tắc chung

- Không bắt người dùng nhập lại dữ liệu đã tồn tại.
- Máy đề xuất; người có thẩm quyền xác nhận.
- Rule tất định trước, AI sau, người quyết định cuối.
- Không ép chuyên viên đổi thói quen làm việc đang cần cho nghiệp vụ.
- Dữ liệu ở lại văn phòng; gọi cloud chỉ tại điểm đã được duyệt.
- Không tự động hóa phán quyết pháp lý.
- Không giám sát nhân viên, quay màn hình hoặc ghi phím.
- Không nối hai module trước khi contract được hai bên duyệt.

**Tại sao:** Trong công chứng, một lần gán sai làm mất lòng tin nhiều hơn nhiều
lần gán đúng. OCR, suy luận và điểm tin cậy không được tự trở thành sự thật.

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
| Desktop shell | Electron | Runtime hệ thống không vào nhánh `main` tài liệu |
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
- Linear giữ task và acceptance criteria; `.agent/tasks/` giữ tiến độ thực thi.

Khi thay đổi chỉ ảnh hưởng một module hoặc feature, cập nhật spec con. Chỉ sửa
trang này khi nhiều module cùng bị ảnh hưởng.
