# Contracts giữa các module

Thư mục này chỉ chứa **những gì đã được cả hai bên đồng ý**. Nó không phải nơi
đề xuất ý tưởng tích hợp.

## Trạng thái: contract kênh shell↔engine đã publish; chưa có contract xuyên-module-nghiệp-vụ

Các module nghiệp vụ vẫn **độc lập về nghiệp vụ** — không có API trực tiếp giữa
chúng, không đọc DB của nhau, không file trao đổi tự động. `shell/` là kênh
tích hợp duy nhất đã duyệt: sidecar import engine in-process và gọi từng module
riêng lẻ — nó **không tạo** đường dữ liệu module↔module. Đó là trạng thái của
**giai đoạn hiện tại**, không phải đích đến: hệ thống sẽ gộp lại và dùng chung
database ([`../VISION.md`](../VISION.md) mục 4).

Đã publish theo lộ trình G1 một máy (owner duyệt 14/09/2026, spec P2):

| File | Nội dung | Trạng thái |
|---|---|---|
| [`desktop-command.md`](./desktop-command.md) | `desktopcommand.v1` — kênh lệnh Electron main ↔ Python sidecar trên một máy: auth, lifecycle, idempotency, waiting_user, error, file_ref machine-scope | APPROVED v1 |
| [`g1-module-data.md`](./g1-module-data.md) | `g1.module.v1` — shape dữ liệu trong payload/result/error (FileRef, JobResult, ErrorObject, IdentityEvidence, ownership) | APPROVED v1 |
| [`g1/examples/`](./g1/examples/) + [`g1/validate_examples.py`](./g1/validate_examples.py) | valid/invalid JSON + validator kiểm chứng được | kiểm: `python contracts/g1/validate_examples.py` |

Hai contract trên là **kênh nội bộ shell↔engine** — không phải contract giữa ba
module nghiệp vụ. ConversionEnvelope/Evidence/DraftCase dùng chung xuyên module
vẫn theo Gate A–D của `../docs/g1/MIN62_DATA_CONTRACT_DRAFT.md` (trước đây trên
branch `min-62-data-contract-draft`) và chưa được publish tại đây.

Các shape `v0.experimental` trong `SYSTEM_ARCHITECTURE.md` mục 6 chỉ dùng để
review/POC. Chúng **không phải contract đã duyệt**, không được dùng làm lý do tạo
runtime integration và vì vậy chưa được đặt thành file riêng trong thư mục này.

Nhưng "sau này sẽ gộp" **không phải giấy phép** để nối bừa bây giờ. Mỗi kết nối
vẫn phải có contract được duyệt trước. Xem
[`../SYSTEM_ARCHITECTURE.md`](../SYSTEM_ARCHITECTURE.md) mục 5.

Vì vậy, ngoài hai contract kênh shell↔engine ở trên, thư mục này chỉ thêm một
file **vocabulary** — nó không mô tả luồng dữ liệu mà mô tả **cách gọi tên dữ
liệu**:

| File | Nội dung | Trạng thái |
|---|---|---|
| [`entities.md`](./entities.md) | Định nghĩa & chuẩn hóa các khóa định danh hồ sơ (CCCD, số GCN, thửa/tờ, số công chứng) | Bắt buộc tham chiếu, mỗi module tự implement |
| [`../TECH_STACK.md`](../TECH_STACK.md) | Công nghệ đã chọn cho từng việc + ràng buộc để lúc gộp DB không xung đột | Bắt buộc đọc trước khi chọn công nghệ mới |

## Quy tắc: contract trước, code sau

Khi hai module cần nối với nhau:

1. Viết một file contract trong thư mục này: ai gọi ai, dữ liệu gì, ai sở hữu,
   xử lý lỗi thế nào, ai chịu trách nhiệm khi schema đổi.
2. Người dùng (chủ dự án) duyệt.
3. Rồi mới viết code ở hai module.

Không viết code tích hợp trước rồi mô tả lại sau. Không agent nào được tự tạo
contract mới rồi tự implement trong cùng một task.

## Tại sao chưa có "shared core library"

Định nghĩa dùng chung ≠ code dùng chung. Ba module cùng cần trích CCCD nhưng ba
ngữ cảnh khác nhau (ảnh OCR / text Word / text IFilter theo thời gian thực), độ
chịu lỗi khác nhau. Gộp thành thư viện chung lúc này sẽ khóa cả ba vào một
abstraction chưa ai chứng minh được.

Lưu ý phân biệt: **gộp hệ thống ≠ gộp code.** Đích đến là chung **dữ liệu và định
nghĩa**; thư viện code dùng chung là chuyện riêng, chỉ làm khi có domain thật thứ
hai chứng minh được contract.

Nguyên tắc đã chốt trong `notary_v2`
(`docs/platform/case-workspace/README.md`): **không tách abstraction dùng chung
cho tới khi có domain thật thứ hai chứng minh contract.** Áp dụng cho toàn hệ
thống.

## Ba mục trong file cũ đã bị xóa vì sai

File `contracts/README.md` trước đây liệt kê ba contract không tồn tại. Ghi lại
để không ai dựng lại chúng từ ký ức:

- ~~"OCR Extraction Contract: output JSON của pipeline OCR (`upload_lab_repo`)
  nạp vào `notary_v2`"~~ — `upload_lab` không làm OCR ảnh (đầu vào là file
  Word) và không có luồng nạp sang `notary_v2`.
- ~~"Case Schema chuẩn dùng chung"~~ — chưa từng được thống nhất. Mỗi module có
  mô hình riêng. Xem `entities.md` cho phần *thật sự* cần khớp nhau.
- ~~"Legal Audit Contract: `notary_v2` truy vấn dịch vụ pháp lý từ
  `researchskill`"~~ — `researchskill` là skill hỗ trợ coding, không phải dịch
  vụ tra cứu pháp luật, và nằm ngoài phạm vi hệ thống công chứng.
