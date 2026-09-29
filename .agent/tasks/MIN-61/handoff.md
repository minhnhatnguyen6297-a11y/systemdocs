# Handoff — MIN-61 MarkItDown/Qwen POC

## Trạng thái record

Record này được rút ngày 29/09/2026 từ plan/result cũ trong
`notary_v2/docs/superpowers/`; trạng thái Linear chưa được kiểm lại `[CONFIRM]`.
Đây là bằng chứng thực thi, không phải spec sản phẩm hay contract production.

## Kết luận

- POC nằm riêng tại `notary_v2/tools/document_conversion_poc/`; không đổi OCR
  production, database hoặc native DashScope endpoint.
- DOCX/XLSX/text PDF đi local; raster/scanned PDF chỉ là OCR candidate. Cloud bị
  chặn nếu không có quyết định allow rõ ràng.
- MarkItDown chạy với plugin tắt. Batch giữ lỗi theo từng fixture và ghi report
  nguyên khối qua file tạm + `os.replace`.
- `ConversionEnvelope v0.experimental` chưa được publish. Kết luận hiện tại là
  `ITERATE`; chỉ được `ADOPT` sau golden dataset của ít nhất hai consumer và
  cloud smoke được duyệt.

## Kiểm lại

```powershell
cd notary_v2
python -m pytest tests/test_document_conversion_poc.py -q
python -m tools.document_conversion_poc.harness --help
```

Không commit fixture khách hàng, credential, raw prompt, ảnh hoặc OCR response.
Chi tiết cũ vẫn truy được trong Git trước commit dọn tài liệu này.
