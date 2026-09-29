# notary_v2 — Soạn hồ sơ

**Trạng thái:** Active · **Phạm vi:** module `notary_v2`

## 1. Mục tiêu và flow chính

Biến giấy tờ hoặc chữ người dùng cung cấp thành dữ liệu hồ sơ đã kiểm tra, mô
tả quan hệ trên Diagram, rồi xuất văn bản Word.

```text
Input → gợi ý chờ duyệt → Stage → Pool → Diagram → Word
```

| Bước | Spec | Vai trò |
|---|---|---|
| Input | [`input/`](./input/README.md) | Nhận file, text hoặc gói OCR; phân tích thành gợi ý |
| Stage | [`stage.md`](./stage.md) | Nguồn dữ liệu người/tài sản đã commit của hồ sơ |
| Pool | [`pool.md`](./pool.md) | Phần tử Stage chưa được gán lên Diagram |
| Diagram | [`diagram/`](./diagram/README.md) | Quan hệ, vai trò và đầu vào engine |
| Word | [`word-output.md`](./word-output.md) | Dựng nhiều văn bản từ snapshot đã lưu |

Ngoài flow chính, [`fast-text-audit.md`](./fast-text-audit.md) mô tả CLI độc
lập để so Word với scan. Công cụ này không ghi Stage, Diagram hoặc database.

## 2. Bất biến của module

- Input chỉ tạo gợi ý; người dùng phải xác nhận trước khi vào Stage.
- Stage sở hữu dữ liệu Người và Tài sản của hồ sơ.
- Pool được tính từ Stage và Diagram; không lưu như nguồn riêng.
- Diagram chỉ tham chiếu phần tử đã commit trong Stage; không sửa dữ liệu Stage.
- Python sở hữu tính nghiệp vụ và `renderModel.requiredSlots`; frontend không
  tự tính kết quả thừa kế.
- Mọi write dùng `base_revision`; revision cũ phải báo xung đột.
- Lỗi validate không được lưu nửa chừng hoặc xóa draft người dùng.

## 3. Kiến trúc module

Electron renderer hiển thị và nhận thao tác. Electron main giữ quyền hệ thống
như chọn file. Sidecar chuyển `notary.*` command tới dịch vụ Python. Python đọc,
validate, tính và ghi database. Contract được duyệt tại
[`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md).

Hai domain hiện có:

- `inheritance`: đã có engine, Stage/Pool/Diagram và Word.
- `two_party`: contract v2 định nghĩa layout 30 vị trí; engine nghiệp vụ đầy đủ
  chưa được suy ra từ thừa kế.

## 4. Trạng thái và dữ liệu

- `row_id`: định danh ổn định của dòng Stage qua commit/reload.
- `revision`: phiên bản workspace; tăng sau write thành công.
- `case_state_json`: snapshot Stage, Diagram input và kết quả backend cho hồ sơ
  thừa kế hiện hành.
- `engine_state_json`: chỉ là nguồn đọc legacy khi cần migrate; không phải SOT
  mới.
- Contract v2 dùng `notary.case-drafting.v2`; trường legacy như
  `isLandOwner`/`willReceive` không được tự mang sang shape v3 nếu schema cấm.

## 5. Giao diện chung

- Stage luôn sửa trực tiếp được; không tạo modal cho thao tác thường xuyên.
- Pool và Diagram phản ánh dữ liệu đã commit, đồng thời giữ draft Diagram riêng.
- Nút phải nói đúng tác dụng: `Cập nhật` commit Stage; `Lưu sơ đồ` lưu Diagram;
  `Xuất Word` chỉ xuất từ trạng thái hợp lệ.
- Lỗi xuất hiện gần nơi gây lỗi, không làm mất dữ liệu vừa nhập.

Quy tắc màu, chữ, khoảng cách và thao tác dùng chung nằm tại
[`../ui/`](../ui/README.md). Quy tắc riêng phải ghi ngay trong spec feature.

## 6. Câu hỏi và lịch sử module

### Đã chốt

- Flow Electron giữ Stage/Pool/Diagram, không port engine Python sang JavaScript.
- Stage commit gồm Người + Tài sản trong một transaction.
- Xóa phần tử Stage rồi commit phải prune tham chiếu Diagram trong cùng
  transaction.

### Còn mở

- Từ điển dữ liệu Người đầy đủ: ai nhập/xem/sửa, nguồn, công thức, nơi lưu và
  placeholder nào dùng. Không suy ngược từ code hay template Word.
- Quy tắc per-asset, contract A/B và owner scope chưa được suy từ các flag cũ.

## 7. Nguồn khi sửa code

Các phụ lục lớn lưu chi tiết có nguồn của một giai đoạn triển khai; quy tắc
hiện hành vẫn nằm ở spec của feature và contract được dẫn từ đó:

- [`workspace-detail.md`](./workspace-detail.md): bản chi tiết MIN-104 về
  Stage/Pool/Diagram và lệnh Electron, kèm bảng so web cũ với đích.
- [`visual-reference.md`](./visual-reference.md): bố cục Notary theo ảnh được
  duyệt; giá trị chưa có nguồn duyệt vẫn là đề xuất.
- [`diagram/inheritance/web-workflow.md`](./diagram/inheritance/web-workflow.md):
  hành vi màn web thừa kế còn dùng để đối chiếu cho tới cutover.
- [`word-output-detail.md`](./word-output-detail.md): placeholder và khác biệt
  giữa web cũ với xuất nhiều file trên Electron.
- [`input/ocr-detail.md`](./input/ocr-detail.md): endpoint OCR upload thủ công
  và lịch sử lựa chọn Qwen; phần Zalo trong đó là ghi nhận thiết kế Draft.

- Intake: [`input/`](./input/README.md).
- Workspace: [`stage.md`](./stage.md), [`pool.md`](./pool.md) và
  [`diagram/`](./diagram/README.md).
- Thừa kế: [`diagram/inheritance/`](./diagram/inheritance/README.md).
- Word: [`word-output.md`](./word-output.md).
- Contract máy đọc: [`contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md).

Source và test chỉ chứng minh hiện trạng. Nếu chúng mâu thuẫn với spec, dừng và
sửa mâu thuẫn trong cùng task; không tạo lại một cây tài liệu dưới module.
