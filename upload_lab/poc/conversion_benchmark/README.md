# POC conversion benchmark

Đây là POC, không phải pipeline production của Electron. Bộ mẫu trong
`golden/` là fixture tổng hợp và được kiểm tra hash bằng `golden_manifest.json`.

Nếu cần cài dependency riêng cho POC, chạy từ thư mục `upload_lab/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r poc\conversion_benchmark\requirements.txt
```

Chạy test POC:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_markitdown_conversion_poc.py -q
```

Kết quả POC không tự thay đổi parser, OCR hay contract production.
