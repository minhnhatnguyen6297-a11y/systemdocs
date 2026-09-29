# Input — Nhập dữ liệu hồ sơ

**Trạng thái:** Active cho upload thủ công; Zalo Sync còn các phần contract mở

## 1. Công dụng

Nhận dữ liệu từ ảnh, PDF, Word, Excel hoặc text; đọc thành gợi ý Người/Tài sản
có nguồn để người dùng kiểm tra trước khi đưa vào Stage.

## 2. Nguồn vào và giới hạn

| Nguồn | Cách nhận | Công nghệ |
|---|---|---|
| Ảnh/PDF giấy tờ | Chọn file | PyMuPDF + Qwen-VL-OCR |
| DOCX | Chọn file | `python-docx` |
| XLSX | Chọn file | `openpyxl` |
| Text | Dán hoặc nhập | Parser tất định |
| Zalo | Sync gói raw đã công bố | Xem [`zalo.md`](./zalo.md) |

Contract `notary.intake_analyze` nhận tối đa 8 nguồn; mỗi file tối đa 20 MB,
PDF tối đa 50 trang và text tối đa 100.000 ký tự. Backend được siết chặt hơn,
không được nới các giới hạn này.

## 3. Flow

```text
Nguồn
→ đọc/OCR thành RAW
→ chuẩn hóa tất định
→ phân loại và bóc trường
→ tạo suggestion kèm source_refs, warning, confidence
→ người dùng xem/sửa
→ đưa vào Stage draft
→ bấm Cập nhật để commit Stage
```

Input không tự tạo quan hệ, chọn người nhận hoặc xuất Word. Kết quả chỉ có
`observed`, `normalized` hoặc `inferred`; không được emit `confirmed`.

## 4. Output

Mỗi suggestion có:

- `suggestion_id`, `source_id`;
- `target`: `person` hoặc `asset`;
- raw value và normalized value theo field;
- trạng thái quan sát, confidence khi suy luận;
- `source_refs` về trang, ô hoặc dòng nguồn;
- warning và lỗi riêng cho từng nguồn.

Lỗi một nguồn không làm mất kết quả nguồn khác. Job có thể `succeeded` hoặc
`partial`; `partial` phải liệt kê nguồn thành công và thất bại.

## 5. Quy tắc nghiệp vụ

- Giữ raw và provenance; normalize không được ghi đè raw.
- Chỉ rule chắc chắn mới tự áp dụng. Suy đoán phải hiện để người dùng duyệt.
- CCCD, tên hoặc thửa đất trùng chỉ là bằng chứng ghép, không tự tạo Case.
- Không tự gán vai trò hợp đồng hoặc thừa kế từ OCR.
- Đếm riêng ảnh, giấy tờ, người ứng viên và người đã duyệt.
- Parser tài sản phân biệt serial GCN với thửa/tờ; một GCN có thể có nhiều thửa.

Danh mục regex tài sản chi tiết vẫn ở
`notary_v2/docs/platform/document-intake/property-rules.md`; đây là phụ lục lớn,
không phải spec flow thứ hai.

## 6. Giao diện và thao tác

- Người dùng thấy từng nguồn, suggestion, cảnh báo và lỗi ngay tại nguồn đó.
- `Đưa vào Stage` chỉ sửa Stage draft; chưa ghi database.
- Ảnh upload thủ công có thể xem lại. Nguồn Zalo không có ảnh/thumbnail trên
  máy chính; người dùng đối chiếu trong Zalo thật.
- Không lưu PII của draft vào localStorage hoặc log.

## 7. Contract và nơi lưu

- Wire contract: `notary.case-drafting.v1/v2`, command
  `notary.intake_analyze`.
- Suggestion chỉ sống trong phiên hoặc vùng nháp chuyên dụng; không dùng
  `case_state_json.stage` làm vùng OCR chưa xác nhận.
- Chỉ Stage commit mới ghi Customer/Property và workspace revision.

## 8. Lỗi và ngoại lệ

- File quá lớn, loại file không hỗ trợ hoặc text quá dài: từ chối đúng code.
- Qwen lỗi: giữ nguồn/trạng thái; không cứu ngầm bằng local OCR.
- Dữ liệu mơ hồ: giữ raw, cảnh báo, để người dùng sửa.
- File có nhiều người/tài sản: tạo nhiều ứng viên, không mặc định cùng hồ sơ.

Ví dụ một suggestion tối thiểu:

```json
{
  "suggestion_id": "<uuid>",
  "source_id": "<uuid-file>",
  "target": "person",
  "fields": {
    "ho_ten": {
      "raw_value": "NGUYEN VAN A",
      "normalized_value": "NGUYỄN VĂN A",
      "observation_state": "normalized",
      "source_refs": [{ "page": 1, "line": 3 }]
    }
  },
  "warnings": []
}
```

Nếu file thứ hai OCR lỗi, job có thể `partial`: suggestion trên vẫn được trả,
đồng thời breakdown ghi rõ source thứ hai thất bại. Người dùng chưa duyệt thì
không field nào được đổi thành `confirmed`.

## 9. Kiến trúc và lịch sử

- Cloud OCR hiện hành là Qwen-only. QR/local OCR đã rời active path; không tự
  khôi phục khi sửa lỗi chung.
- Hướng normalize hiện tại: Qwen đọc raw, backend normalize sau để dễ test và
  audit. Phần xác suất chỉ là gợi ý.
- Adapter MarkItDown là POC, chưa là runtime production.

## 10. Câu hỏi mở

- Bộ từ điển/rule chuẩn hóa tiếng Việt nào đủ tin cậy để auto-apply?
- Field nào thuộc từ điển Người dùng chung và owner của từng field?
- Các fallback classifier chưa có negative test không được nâng thành contract.

## 11. Nguồn

- Contract: [`contracts/notary-case-drafting.md`](../../../../contracts/notary-case-drafting.md).
- Hiện trạng chi tiết: `notary_v2/docs/platform/document-intake/`.
- Mã chính: `notary_v2/routers/ocr_ai.py`.
