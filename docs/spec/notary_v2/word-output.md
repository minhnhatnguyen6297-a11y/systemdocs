# Word output — Xuất văn bản

**Trạng thái:** Active cho hồ sơ thừa kế hiện hành

## 1. Công dụng

Dựng một hoặc nhiều file DOCX từ snapshot Stage, Diagram, tài sản và lựa chọn
văn bản đã lưu. Word chỉ trình bày; không tự quyết quan hệ hoặc kết quả pháp lý.

## 2. Flow

```text
Chọn văn bản + thư mục đích
→ kiểm workspace và loại hồ sơ
→ đọc Stage và Diagram đã lưu
→ backend dựng placeholder
→ tạo từng DOCX
→ trả kết quả saved/failed/skipped theo file
```

## 3. Input và output

Input: `case_id`, danh sách `document_keys` và thư mục đích local đã tồn tại.
Command này không nhận `base_revision`. Output liệt kê từng document, tên file
thực, path, trạng thái và lỗi; breakdown luôn có `succeeded`, `failed`,
`skipped`.

## 4. Quy tắc dữ liệu

| Nội dung | Nguồn |
|---|---|
| Thông tin cá nhân | Stage |
| Quan hệ | Diagram |
| Kết quả/phân số | Engine result Python |
| Tài sản | Stage assets + vị trí Diagram |
| Mẫu và placeholder | Catalog/template backend |

Không lấy dữ liệu chưa commit hoặc kết quả frontend tự tính. Placeholder chưa
giải quyết phải làm file đó thất bại, không âm thầm để sót trong văn bản.

`incomplete`/`unsupported` ở cấp engine hiện chưa có cổng chặn xuất Word
thống nhất trong contract hiện hành. Draft nghiệp vụ đề xuất cho xem/xuất
`incomplete` với nhãn rõ, còn thiết kế engine đích đề xuất chặn lưu. Đây là
câu hỏi cần owner chốt trước khi thay đổi hành vi xuất; không được xem việc
lưu thành công là bằng chứng hồ sơ đã tính xong.

### Placeholder và context

- Placeholder mới dùng `[Tên danh sách N - Trường]`; alias cũ chỉ để mở
  template cũ, không làm chuẩn đặt tên mới.
- Context phân loại một lần thành `Người`, `Chủ đất sống`, `Chủ đất chết`,
  `Người nhận`, `Người không nhận`; `Người từ chối` chỉ có khi có bằng chứng
  pháp lý xác nhận riêng.
- Tầng 1 lấy field trực tiếp. Tầng 2 dựng trọn câu/dòng và trả rỗng toàn bộ khi
  không áp dụng, tránh để lại dấu câu rác. Chưa có block `if/for` cho template.
- Resolver không được đoán nghiệp vụ từ tên placeholder. Catalog hiện hành nằm
  cạnh template tại `notary_v2/word_templates/placeholder_mapping.md`.

## 5. File và an toàn

- Tên: `<filename_stem>_HS-<case_id>[_n].docx`.
- Không ghi đè file có sẵn; trùng tên tăng `_2`, `_3`, ...
- Output phải nằm trong thư mục người dùng chọn; cấm UNC/path traversal theo
  contract hiện hành.
- Cancel giữ file đã lưu, đánh dấu file chưa bắt đầu là `skipped`.
- File đang ghi dở phải được dọn khi có thể.

## 6. Lỗi

- Không chọn văn bản, key lạ/lặp, thiếu template, placeholder còn sót, file bị
  khóa hoặc path sai đều có code riêng.
- Một file lỗi không bắt buộc làm mất file khác đã tạo.
- Tất cả file lỗi: job `word_batch_failed`; trộn kết quả: `partial`.

## 7. Kiến trúc, câu hỏi và lịch sử

Backend/Python sở hữu template catalog, mapping và tên file. Electron chỉ chọn
thư mục, gửi command, hiển thị kết quả và mở file khi người dùng yêu cầu.

Renderer phải xử lý placeholder trong paragraph, table, header/footer và khi
Word tách một placeholder thành nhiều run. Router chỉ điều phối; logic dựng
`WordExportContext` và thay placeholder thuộc service Word.

Còn mở: bộ văn bản cho domain mới và mapping per-asset phải được duyệt; không
nhân bản logic từ template hiện có.

## 8. Nguồn

- `contracts/notary-case-drafting.md` §8.
- `notary_v2/word_templates/placeholder_mapping.md`.
- `notary_v2/services/word_engine.py` và tests Word.
- [`word-output-detail.md`](./word-output-detail.md) giữ ví dụ placeholder,
  flow web cũ và các kiểm tra renderer chi tiết.
