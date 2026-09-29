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

Còn mở: bộ văn bản cho domain mới và mapping per-asset phải được duyệt; không
nhân bản logic từ template hiện có.

## 8. Nguồn

- `contracts/notary-case-drafting.md` §8.
- `notary_v2/docs/domains/inheritance/word-export.md`.
- `notary_v2/word_templates/placeholder_mapping.md`.
