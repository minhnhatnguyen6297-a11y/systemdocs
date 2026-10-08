# Catalog cấu trúc và loại văn bản Word

**Trạng thái:** Active cho loại/vùng/cấu trúc. Quy tắc giá trị trường có một nguồn tại [regex-fields.md](regex-fields.md); đáp án mẫu ở [regex-expected-results.md](regex-expected-results.md). Các thuật toán F01/F04/F05 chưa chốt không có ưu tiên theo tuổi tài liệu.

## 0. Core nằm ở đâu (đọc trước khi sửa)

**Owner 06/10/2026:** lõi regex dùng chung là
`tools/regex_workbench/engine` (zoning-first, provenance, trạng thái
matched/ambiguous/missing — Owner NAIA-4 02/10/2026 chọn). Lõi phục vụ cả
trích xuất và đề xuất placeholder cho mẫu Word chưa gắn template.
`upload_lab/extract_contract.py` là **engine thừa kế đang chạy**, giữ vai
trò nguồn kiến thức trường để port sang profile workbench — không còn
là bản gốc của core dùng chung.

| Thứ | File |
|---|---|
| Lõi regex dùng chung | `tools/regex_workbench/engine/` + profile JSON |
| Engine thừa kế đang chạy (nguồn port sang profile) | `upload_lab/extract_contract.py` (docstring đầu file dẫn tiếp) |
| Test giữ hành vi | `upload_lab/tests/test_upload_lab_extract_contract.py` |
| Tool test giao diện (chọn 1 file Word → xem Người/Thửa/JSON) | `upload_lab/tools/regex_test_tool.py` (chạy bằng `upload_lab/run_regex_test.bat`) |
| Luật kiểm tra kết quả (R00..R10, R12 tài sản chưa hỗ trợ, R13 dữ liệu mơ hồ/thiếu căn cứ; R11 lời chứng đã xóa theo decision-46) | `upload_lab/kiem_tra_trich_xuat.py` + test `tests/test_kiem_tra_trich_xuat.py` |
| Quét hàng loạt bằng luật trên | `upload_lab/tools/quet_kiem_tra.py` (`--loc`, `--offset/--limit`, `--ca-doc`) |
| Repo test cho nhân viên (Test 1 file + Test cả thư mục + Xem log, log cố định) | `regex-test-tool/tool/` tất cả trong 1 folder (chạy bằng `tool/run.bat`) |
| Catalog cấu trúc này | `docs/spec/upload_lab/regex-rules.md` |
| Báo cáo từng loại văn bản (kết quả test + nguyên tắc bằng lời) | `.agents/` (file tạm, không commit) |

Phạm vi core (quyết định owner 05/10/2026): core chỉ trích **xuất**
người + tài sản bằng regex; đối chiếu thuộc tầng kiểm tra. Quyết định 06/10
về không trích người trong Lời chứng và phạm vi gộp hiện hành ở
[core](regex-core.md) và [quy tắc trường](regex-fields.md); không dùng câu
tóm tắt lịch sử này để chốt F01/F04/F05.
`so_cong_chung` vẫn được đọc để phục vụ upload/audit portal nhưng
không còn là tiêu chí đủ/thiếu của core.

Catalog dẫn tới loại, vùng và cấu trúc; giá trị trường do regex-fields.md
sở hữu. [Bản trước TASK-10.1](references/regex-rules-before-field-standardization.md)
giữ biến thể/lý do làm tham khảo, không tái áp luật đang chờ.

---

## 1. Chọn nguồn quy tắc

| Câu hỏi | Nơi quyết định |
|---|---|
| Flow, cách kiểm và phạm vi engine | [regex-core.md](regex-core.md) |
| Tên, giới tính, ngày, giấy tờ, địa chỉ, thửa/diện tích/chi tiết | [regex-fields.md](regex-fields.md) |
| Đầu vào và đáp án từng ca | [regex-expected-results.md](regex-expected-results.md) |
| Loại/vùng/đầu-cuối thừa kế | [regex-thua-ke.md](regex-thua-ke.md) |
| Loại/vùng khác chưa có spec riêng | Các mục 2.1–2.4 dưới đây |

.docx giữ thứ tự đoạn/bảng; .doc qua IFilter có thể giữ TAB hoặc dồn nhiều hàng chung một dòng. Khi sửa cách đọc phải kiểm cả hai đường. Nội dung không được đọc thì báo trạng thái đọc, không được tính như đáp án không có người/tài sản.

Trang phụ Lời chứng/Trang sửa lỗi kỹ thuật/Đính chính nhận loại và vùng riêng theo mẫu; không tự coi nội dung chỉ dẫn chiếu là đương sự. Các biến thể ký tự, marker và nhãn cũ xem tham khảo lịch sử; luật trường vẫn ở regex-fields.

## 2. Catalog theo loại

### 2.1. Hợp đồng chuyển nhượng (`DOC_KIND_TRANSFER`)
- **Nhóm HĐ**: `Chuyển nhượng - Mua bán`
- **Tiêu đề canonical**: `Hợp đồng chuyển nhượng quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự**:
  - `Bên A`: Bên chuyển nhượng
  - `Bên B`: Bên nhận chuyển nhượng
  - Người yêu cầu công chứng: Ưu tiên Bên B (Bên nhận chuyển nhượng).
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `Đối tượng của Hợp đồng này là...`
  - *Điểm kết thúc*: Dừng trước `1.2`, `Điều 2`, `Giá chuyển nhượng`, `Phương thức thanh toán`, `Bằng Hợp đồng này`.

### 2.2. Văn bản cam kết tài sản riêng (`DOC_KIND_ASSET_COMMITMENT`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết`
- **Tiêu đề canonical**: `Văn bản cam kết tài sản riêng`
- **Đương sự**:
  - Gồm cả 2 vợ chồng (Người chồng - Ông ... / Người vợ - Bà ...).
  - Người yêu cầu công chứng: Người đứng tên cam kết tài sản riêng.
- **Tài sản**:
  - *Điểm bắt đầu*: `quyền sử dụng đất ... có địa chỉ tại:` hoặc `hiện đang sở hữu Tài Sản là` / `Tài Sản là`.
  - *Điểm kết thúc*: Dừng trước `Bằng văn bản này chúng tôi xác định`, `Hai vợ chồng chúng tôi cam kết`, `Chúng tôi công nhận`.

### 2.3. Văn bản thỏa thuận hủy bỏ / sửa đổi / bổ sung (`DOC_KIND_TRANSFER_CANCELLATION`)
- **Nhóm HĐ**: `Thoả thuận - Cam kết` (hoặc `Phụ lục hợp đồng - văn bản sửa đổi`)
- **Tiêu đề canonical**: `Văn bản thỏa thuận về việc hủy bỏ hợp đồng chuyển nhượng quyền sử dụng đất`
- **Đương sự**: 2 bên tham gia thỏa thuận hủy bỏ.
- **Tài sản**: Đoạn trích tham chiếu thông tin thửa đất/GCN từ hợp đồng gốc, dừng trước `và được Công chứng viên chứng nhận`, `số công chứng`.

### 2.4. Hợp đồng thế chấp (`DOC_KIND_MORTGAGE`)
- **Nhóm HĐ**: `Cầm cố - Thế chấp - Vay`
- **Tiêu đề canonical**: `Hợp đồng thế chấp quyền sử dụng đất` (hoặc kèm tài sản gắn liền với đất)
- **Đương sự**:
  - `Bên A`: Bên thế chấp (cá nhân/hộ gia đình).
  - `Bên B`: Bên nhận thế chấp (thường là Ngân hàng / Pháp nhân / Chi nhánh + Người đại diện ký).
  - Không có heading `BÊN NHẬN THẾ CHẤP` thì phần mở đầu trước `BÊN THẾ CHẤP` (ngân hàng + đại diện, mẫu Lời chứng Agribank/VB sửa đổi) được coi là Bên B (11/10/2026).
  - Người yêu cầu công chứng: Người đại diện ngân hàng (Bên B).
- **Tài sản**:
  - Trích xuất thông tin thửa đất / GCN từ phần mô tả tài sản hoặc trích xuất tối thiểu `Quyền sử dụng đất`.

### 2.5. Phân chia di sản

Nhóm Thừa kế (khai nhận - phân chia di sản thừa kế ); tiêu đề Văn bản phân chia di sản. Vùng người/tài sản và marker tại [thừa kế §1–4](regex-thua-ke.md). Tên, danh xưng, ngày, giấy tờ, địa chỉ và dữ liệu đất tại [quy tắc trường](regex-fields.md).

### 2.6. Từ chối nhận di sản

Nhóm Từ chối nhận di sản thừa kế; tiêu đề Văn bản từ chối nhận di sản. Tôi là/Chúng tôi là hoặc Văn bản từ chối nhận di sản này được lập bởi mở nhóm người từ chối; dừng trước Nay, tôi/chúng tôi tự nguyện lập Văn bản này hoặc Theo quy định của pháp luật. Tài sản có thể nhiều mục Tài sản thứ N, mở từ mô tả di sản; dừng trước Bằng Văn bản này ... từ chối, Tôi xin cam đoan, Người từ chối hưởng di sản, Lời chứng. Trường dùng luật chung; phạm vi người chết chỉ-năm theo [spec loại](regex-thua-ke.md).

### 2.7. Khai nhận di sản

Tiêu đề chứa khai nhận di sản; nhóm thừa kế. Marker mở dùng chung với phân chia; nhãn NGƯỜI KHAI NHẬN DI SẢN. Xem [spec loại](regex-thua-ke.md), không chép lại luật trường.

### 2.8. Sổ tiết kiệm/tài khoản và 2.9. Bảo hiểm

Theo decision-46, chỉ nhận diện [tài sản chưa hỗ trợ](regex-fields.md#7-trường-chưa-hỗ-trợ-và-phạm-vi) và R12; không trích dòng tiền/sổ/quyền lợi đầy đủ. Mô tả bóc chi tiết trong catalog cũ là lịch sử đã bị thay thế, không phải luật hiện hành.

## 3. Quy trình thêm loại văn bản mới

Khi cần bổ sung thêm một loại văn bản mới vào hệ thống:
1. **Cập nhật catalog**: Thêm tên loại văn bản, marker tiêu đề, nhóm HĐ, quy tắc đương sự và tài sản vào file này.
2. **Khai báo `DOC_KIND_*`**: Khai báo hằng số trong `extract_contract.py`.
3. **Cập nhật hàm nhận diện**: Thêm rule vào `_detect_document_kind_and_title()`.
4. **Cập nhật hàm trích xuất**:
   - Nếu đương sự có cấu trúc mới $\rightarrow$ Bổ sung hàm parse đương sự và cập nhật `_fmt_duong_su_by_kind()`.
   - Nếu tài sản có marker đặc thù $\rightarrow$ Bổ sung `_find_tai_san_<kind>()` và tích hợp vào `_find_tai_san_by_kind()`.
5. **Thêm Unit Test**: Bổ sung test case vào `tests/test_upload_lab_extract_contract.py`.
6. **Chạy đối chiếu mẫu thực tế**: Đặt file vào `regex_review_samples/input/` và chạy `tools/review_regex_samples.py`.

## Future runtime LLM

Có thể nghiên cứu chế độ `regex` / `hybrid` / `llm` trả về span offsets có cấu trúc, không nhận free text. Mặc định phải tắt; khi timeout hoặc lỗi phải fallback về regex. Dữ liệu có PII nên chỉ được xử lý trong ranh giới bảo mật đã phê duyệt. Đây chỉ là ý tưởng, chưa triển khai runtime.
