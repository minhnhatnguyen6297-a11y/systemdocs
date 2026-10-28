# Notary System — Tổng quan dành cho developer

**Bản giới thiệu · cập nhật 02/10/2026.** Tổng hợp từ tài liệu sản phẩm trong `docs/spec/`; không thay thế spec chi tiết hoặc quyết định còn chờ duyệt. Mức độ hoàn thiện dưới đây theo tài liệu, không phải kết quả chạy thử toàn bộ ứng dụng.

## Ý tưởng trong một phút

Notary System là hệ thống hỗ trợ văn phòng công chứng, tập trung vào giải quyết 3 bài toán - 3 module chính trong repo:
- Soạn thảo tự động: Mọi input: image, pdf, excel, raw text,... -> Xuất thành các trường dữ lieu chuẩn. VD: "name","date_of_birth",... -> xuất thành file word. Chuyển work flow từ soạn thủ công thành flow kéo thả.
- Upload tự động: Hệ thống công chứng phải upload mọi hồ sơ trong quá trình hoạt động lên website của nhà nước. Flow: Scan file word trong máy, trích xuất thành các trường thông tin -> upload tự động lên web bằng api request hoặc playwright (nếu web không có api)
- Quản lý văn phòng: Mỗi máy nhân viên được cài 1 listener soi diff file word và excel. Nhân viên soạn thảo hồ sơ nào -> xuất thành 1 record lưu trữ. Lifecycle của 1 hồ sơ đất đai có thể rất dài, qua nhiều bước nhưng hệ thống công chứng hiện không có phần mềm quản lý, nếu có cũng yêu cầu nhập lieu chi tiết -> Flow mới: tự trích xuất việc nhân viên làm, xuất thành 1 record trong 1 chuỗi tiến độ -> Quản lý hồ sơ thời gian dài.

Đích dài hạn là một ứng dụng desktop, giao diện chung và cơ sở dữ liệu nghiệp vụ chung. Hiện tại các module còn giữ dữ liệu và phần xử lý riêng. Sản phẩm phát triển theo hướng dùng dữ liệu tại văn phòng, kết hợp một số kết nối bên ngoài được cho phép.

## 1. notary_v2 — Soạn hồ sơ mới

### Các chức năng chính

- Nhận ảnh, PDF, Word, Excel và văn bản dán vào.
- Đọc chữ trong ảnh bằng OCR — công nghệ biến ảnh giấy tờ thành chữ — rồi bóc thông tin người và tài sản.
- Cho chuyên viên kiểm tra, sửa và xác nhận dữ liệu trong bảng.
- Sắp xếp người vào sơ đồ quan hệ hoặc hai bên của hợp đồng.
- Với thừa kế: tính kết quả từ quan hệ và dữ kiện đã nhập, kèm giải thích và cảnh báo thiếu thông tin.
- Tạo một hoặc nhiều văn bản Word từ mẫu và dữ liệu đã lưu.

### Luồng soạn hồ sơ

```text
Ảnh / PDF / DOCX / XLSX / text
    → Đọc chữ và bóc trường
    → Gợi ý để chuyên viên xem, sửa
    → Stage: bảng Người và Tài sản
    → Bấm Cập nhật để lưu dữ liệu đã kiểm tra
    → Pool: danh sách người chưa được xếp vào sơ đồ
    → Diagram: sơ đồ quan hệ và vai trò
    → Xem cách tính, bổ sung thông tin, lưu sơ đồ
    → Chọn mẫu và thư mục → xuất Word
```

### Luồng phụ: soát Word với bản scan

Một công cụ chạy bằng dòng lệnh nhận thư mục hồ sơ, đọc bản scan và Word, so các trường như tên, số giấy tờ, ngày, thửa đất và diện tích, rồi xuất báo cáo. Công cụ này độc lập với luồng soạn hồ sơ và không ghi cơ sở dữ liệu. Nó kiểm tra chữ và chuỗi dữ liệu, không đưa ra kết luận pháp lý.

**Đọc tiếp:** [Module](./notary_v2/README.md), [Nhập liệu](./notary_v2/input/README.md), [Stage](./notary_v2/stage.md), [Pool](./notary_v2/pool.md), [Diagram](./notary_v2/diagram/README.md), [Word](./notary_v2/word-output.md), [Soát văn bản](./notary_v2/fast-text-audit.md).

## 2. upload_lab — Số hóa và chuẩn bị upload hồ sơ cũ

### Vì sao cần module này?

Phần mềm quản lý cũ của văn phòng chưa có API, tức cổng để phần mềm khác lấy dữ liệu trực tiếp. Nguồn có thể khai thác là các file Word chuyên viên đã soạn. Upload Lab đọc nguồn đó để giảm việc nhập lại lên portal — website cơ sở dữ liệu công chứng của tỉnh.

### Luồng A: quét kho Word

```text
Thư mục .doc / .docx
    → Đọc nội dung theo thứ tự đoạn và bảng
    → Nhận diện loại văn bản
    → Bóc đương sự, tài sản, số/ngày công chứng, công chứng viên...
    → Lưu dữ liệu có cấu trúc và kết quả từng lượt quét
```

Các nhóm được tài liệu mô tả gồm chuyển nhượng, thế chấp, cam kết tài sản riêng, phân chia/từ chối di sản và nhóm văn bản chung. Quy tắc bóc trường nằm trong catalog regex — tập mẫu nhận diện chữ, ví dụ tìm số công chứng theo cấu trúc `xxx/yyyy`.

### Luồng B: đối chiếu sổ Excel

```text
Excel tải từ portal hoặc do người dùng cung cấp
    → Chuẩn hóa số công chứng
    → Kiểm tra theo khoảng ngày
    → Báo số thiếu, trùng, sai định dạng hoặc sai năm
    → Đối chiếu với kho Word đã quét
```

### Luồng C: chuẩn bị upload

```text
Chọn hồ sơ cần nhập
    → Mở browser đã đăng nhập
    → Điền sẵn form, mỗi tab gắn với một hồ sơ
    → Người dùng kiểm tra và tự bấm Lưu
    → Nhận phản hồi lưu thành công
    → Cập nhật kết quả và hàng đợi
```

Mỗi đợt có thể chọn 1–30 tab. Hồ sơ đã xuất hiện trong Excel được bỏ chọn mặc định để tránh nhập trùng. App chỉ đánh dấu thành công khi nhận được bằng chứng portal đã lưu.

Giao diện Electron có hai tab: **Audit Sổ Công Chứng** và **Quét & Upload Hồ Sơ**. “Audit” ở đây nghĩa là kiểm tra, đối chiếu dữ liệu. Trạng thái quét, bộ lọc và lựa chọn được giữ khi đổi tab.

**Đọc tiếp:** [Module](./upload_lab/README.md), [Quy tắc trích xuất](./upload_lab/regex-rules.md), [Phiên portal](./upload_lab/portal-session.md), [Giao diện](./upload_lab/ui.md).

## 3. notaryoffice — Theo dõi vận hành văn phòng

**Đây là ý tưởng đã được viết thành thiết kế nháp, chưa có phần mềm chạy.**

Mục tiêu là trả lời: “Hồ sơ nào đang xử lý? Ai đang giữ? Đang ở bước nào? Chờ bổ sung việc gì?”. Hệ thống dự kiến tận dụng dấu vết công việc được phép thu nhận, như thay đổi nội dung Word và sự kiện in, để giảm nhập nhật ký thủ công.

### Luồng dự kiến

```text
Dấu vết Word / in / nguồn được phép
    → Bản ghi có nguồn và thời gian
    → Nhóm các hoạt động có thể liên quan
    → Đề xuất hồ sơ nháp
    → Chuyên viên xác nhận, sửa, gộp hoặc bỏ qua
    → Hồ sơ vận hành đã xác nhận
    → Tìm kiếm và xem lịch sử xử lý
```

Ví dụ: một file Word vừa thay đổi thông tin tài sản rồi được in. Hệ thống có thể đề xuất rằng hoạt động này liên quan đến hồ sơ X, kèm nguồn để chuyên viên kiểm tra. Sự kiện in chỉ là dấu hiệu tiến trình; số bản in không được coi là dữ kiện đáng tin cậy.

### Chức năng và cấu trúc dự kiến

- Một chương trình nhỏ trên mỗi máy làm việc thu dấu vết được phép và giữ tạm khi mất mạng.
- Một máy trung tâm trong mạng nội bộ nhận dữ liệu, đối chiếu và dựng gợi ý hồ sơ.
- Chuyên viên kiểm tra gợi ý trước khi hồ sơ trở thành dữ liệu đã xác nhận.
- Tìm theo tên, số giấy tờ, giấy chứng nhận, thửa/tờ và chuyên viên; xem lịch sử hồ sơ theo thời gian.
- Phân biệt rõ kết quả dự đoán với kết quả đã xác nhận.

Thiết kế không thu màn hình hay phím bấm và không dùng để chấm công. Khả năng đọc Word khi đang mở, nhận sự kiện trên ổ mạng và xác định người dùng Windows còn cần khảo sát hoặc đo trên máy thật.

**Đọc tiếp:** [Module](./notaryoffice/README.md), [Lập luận và thiết kế gốc — Draft](./notaryoffice/intent-source.md).

## 4. Nguồn nhập liệu Zalo

Nguồn Zalo có phần mềm thu nhận ở repo riêng; hợp đồng trao đổi dữ liệu với hệ thống chính vẫn là bản nháp, chưa đủ cơ sở giới thiệu như tích hợp hoàn chỉnh.

```text
Tài khoản Zalo chung của văn phòng
    → Thu tin/ảnh thuộc phạm vi cho phép
    → Giữ ảnh tạm và gọi OCR tại nơi có ảnh
    → Gửi chữ OCR gốc, trạng thái và thông tin nguồn về máy chính
    → Máy chính phân loại và bóc thông tin
    → Chuyên viên đối chiếu trong Zalo, xác nhận
    → Đưa vào bảng dữ liệu hồ sơ
```

Máy chính không nhận ảnh hoặc đường dẫn tải ảnh từ luồng này. Việc báo “đã nhận dữ liệu” chỉ có nghĩa đã lưu chữ gốc, chưa có nghĩa nội dung đã được chuyên viên duyệt. Tài khoản cá nhân và tin riêng của nhân viên nằm ngoài phạm vi.

**Đọc tiếp:** [Nhập liệu từ Zalo](./notary_v2/input/zalo/README.md).

## Công nghệ và cách các phần nối với nhau

### Kiến trúc ứng dụng desktop

```text
Giao diện Electron: bảng, sơ đồ, thao tác người dùng
    ↓
Phần điều phối Electron: cửa sổ, chọn file, quyền hệ thống
    ↓ Lệnh có định dạng và phiên bản thống nhất
Python + FastAPI chạy cùng ứng dụng trên máy
    ↓
Bộ nối của từng module
    ↓
Xử lý nghiệp vụ, đọc tài liệu, tạo Word, điều khiển browser
    ↓
Cơ sở dữ liệu và file do từng module quản lý
```

Chương trình Python chạy kèm được gọi là **sidecar**: có thể hình dung Electron là quầy thao tác, còn Python là bộ phận xử lý phía sau. Giao diện gửi yêu cầu và hiển thị kết quả; quy tắc nghiệp vụ và việc lưu dữ liệu nằm ở Python.

### Bộ công nghệ

| Thành phần | Công nghệ | Dùng để làm gì? |
|---|---|---|
| Ứng dụng desktop | Electron, JavaScript, HTML/CSS | Cửa sổ và giao diện chung; shell hiện tại không khai báo React trong package của nó |
| Xử lý phía sau | Python + FastAPI | Nhận yêu cầu từ app, điều phối và xử lý nghiệp vụ trên máy |
| Lưu dữ liệu hiện tại | SQLite theo module | Dữ liệu hồ sơ và sổ theo dõi xử lý; loại DB chung cuối cùng chưa chốt |
| Đọc chữ trong ảnh | Qwen-VL-OCR qua DashScope | Đọc giấy tờ ở các luồng được cho phép gửi ảnh ra ngoài |
| Đọc/tạo Word mới | `python-docx` | Xử lý `.docx`, đoạn, bảng và mẫu văn bản |
| Đọc Word cũ | Windows IFilter | Lấy chữ từ `.doc` |
| Xử lý PDF | PyMuPDF | Đọc và chuẩn bị trang PDF cho nhập liệu |
| Xử lý Excel | `openpyxl` | Đọc sổ Excel, đối chiếu dữ liệu |
| Điều khiển portal | Playwright + Chromium có cửa sổ | Đăng nhập, tải Excel và điền sẵn form |

Một số tài liệu cũ nhắc React hoặc giao diện Qt. Khi tìm hiểu ứng dụng tích hợp hiện tại, nên bắt đầu từ `shell/` và đọc tiếp phần chuyển đổi của từng module. MarkItDown hiện chỉ là thử nghiệm, chưa là công nghệ mặc định của sản phẩm.

### Các nguyên tắc dữ liệu cần hiểu trước khi đóng góp

1. **Giữ được đường về nguồn.** Giá trị trích xuất cần biết đến từ file, trang, đoạn hoặc ô nào; chữ gốc và chữ đã chuẩn hóa được giữ riêng.
2. **Máy gợi ý, người xác nhận.** Nhận diện bằng OCR hoặc AI chưa phải dữ liệu đã duyệt.
3. **Ưu tiên quy tắc rõ ràng.** AI hỗ trợ chỗ mơ hồ; không tự quyết kết luận pháp lý.
4. **Mỗi module quản lý phần dữ liệu của mình.** Cùng nói về một hồ sơ không có nghĩa các module được tự gộp bản ghi hoặc ghi đè dữ liệu của nhau.
5. **Lưu theo phiên bản.** Khi hai nơi sửa cùng hồ sơ, app phát hiện bản cũ để tránh ghi đè mất thay đổi.
6. **Chạy chủ yếu tại văn phòng.** OCR cloud, Zalo và portal là các kết nối có phạm vi cụ thể, không phải quyền gửi mọi dữ liệu ra ngoài.

Đường đi chung là: **nguồn gốc → chữ/sự kiện gốc → chuẩn hóa → gợi ý → xác nhận**.

## Cấu trúc repository

```text
systemdocs/
├── shell/                 # Ứng dụng Electron và Python chạy kèm
├── notary_v2/             # Soạn hồ sơ, xử lý dữ liệu, thừa kế và Word
├── upload_lab/            # Đọc Word cũ, kiểm Excel, chuẩn bị upload
├── notaryoffice/          # Phần dành cho module theo dõi; chưa có runtime
├── zalo/                  # Bản sao một chiều từ repo thu nhận riêng
├── contracts/             # Định dạng trao đổi dữ liệu và schema đã duyệt
├── docs/spec/
│   ├── README.md          # Tầm nhìn, ranh giới và kiến trúc toàn hệ thống
│   ├── notary_v2/         # Tài liệu theo bước trong luồng soạn hồ sơ
│   ├── upload_lab/        # Tài liệu quét, đối chiếu và portal
│   ├── notaryoffice/      # Thiết kế nháp của luồng theo dõi văn phòng
│   └── ui/                # Giao diện chung, mẫu thử và ảnh tham chiếu
└── .agent/tasks/           # Ghi chép thực hiện từng task
```

**Contract** là thỏa thuận về dữ liệu gửi/nhận giữa các phần, giống việc thống nhất các cột trong một biểu mẫu. Tài liệu sản phẩm giải thích ý nghĩa; schema trong `contracts/` giúp máy kiểm tra cấu trúc. Có cả contract nháp, nên luôn đọc trạng thái trước khi dùng.

Đường đọc đề nghị: [README gốc](../../README.md) → [Spec toàn hệ thống](./README.md) → README module → tài liệu chức năng → contract → source/test liên quan. Task và điều kiện nghiệm thu được quản lý ở Linear; tài liệu sản phẩm dài hạn nằm trong `docs/spec/`.

## Các hướng phát triển để trao đổi với dev

Đây là các phạm vi hợp lý để thảo luận, chưa phải danh sách task đã được giao:

- Hoàn thiện luồng soạn hồ sơ trên Electron, giữ dữ liệu ổn định khi sửa, lưu và mở lại.
- Nâng chất lượng bóc trường từ giấy tờ và Word, kiểm tra bằng mẫu thực tế có nguồn đối chiếu.
- Hoàn thiện bộ vai trò và văn bản cho hợp đồng hai bên.
- Kiểm chứng thao tác portal, khả năng khôi phục khi lỗi và chất lượng dữ liệu trước upload.
- Duyệt hợp đồng Zalo và kiểm chứng việc gửi lại dữ liệu, xử lý lỗi OCR, mất kết nối.
- Khảo sát máy văn phòng trước khi triển khai thử `notaryoffice`.
- Chốt mô hình dữ liệu và cách chuyển sang DB chung khi các module đủ ổn định.

## Khi chia sẻ theo phong cách dự án nguồn mở

Bản này có thể dùng làm phần giới thiệu ý tưởng và cấu trúc dự án. Trước khi công bố repo theo hình thức nguồn mở, cần chốt giấy phép sử dụng mã nguồn, hướng dẫn cài/chạy và bộ dữ liệu mẫu đã bỏ thông tin cá nhân. Bản tổng quan không tự xác nhận dự án đã có giấy phép nguồn mở hoặc đã sẵn sàng dùng chính thức.

Nguồn chính: [Spec hệ thống](./README.md), [Notary](./notary_v2/README.md), [Upload Lab](./upload_lab/README.md), [Notary Office](./notaryoffice/README.md), [UI chung](./ui/README.md). Công nghệ shell được đối chiếu thêm với [package hiện tại](../../shell/package.json).
