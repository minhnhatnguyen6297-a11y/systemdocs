# Lựa chọn công nghệ — SOT toàn hệ thống

**Đây là file agent phải đọc TRƯỚC KHI ra quyết định kiến trúc hoặc chọn công
nghệ mới trong bất kỳ repo nào.**

Lý do file này tồn tại: ba repo sẽ **gộp thành một hệ thống dùng chung database**
ở giai đoạn sau. Nếu mỗi repo tự chọn công nghệ khác nhau cho cùng một việc (ví
dụ repo này OCR bằng Qwen, repo kia OCR bằng thứ khác), lúc gộp sẽ phải viết lại.
Chọn khác là được — nhưng phải **có lý do và ghi vào đây**, không chọn theo quán
tính.

Cập nhật: 10/09/2026

---

## 1. Bảng công nghệ đang dùng thật

| Việc | Công nghệ đã chọn | Đang dùng ở | Ghi chú |
|---|---|---|---|
| **OCR ảnh giấy tờ** | **Qwen-VL-OCR** qua DashScope (`qwen-vl-ocr-2025-11-20`) | `notary_v2` (`routers/ocr_ai.py`) | Base URL `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`. Có nhánh fallback OpenAI-compatible và biến `GEMINI_API_KEY` trong `.env` — **Qwen là lựa chọn chính** |
| **Đọc `.docx`** | `python-docx` | `notary_v2`, `upload_lab` | Phải giữ thứ tự đoạn + bảng, nếu không sẽ trộn Bên A / Bên B |
| **Đọc `.doc` cũ** | **Windows IFilter (`query.dll`)** | `upload_lab`; `notaryoffice` (dự kiến) | Không cần cài Word. Đọc được cả khi Word đang giữ file. `notary_v2` **không** dùng |
| **Đọc PDF / render ảnh** | `PyMuPDF` (`fitz`) | `notary_v2` | |
| **Đọc QR / barcode** | `zxing-cpp` | `notary_v2` (`routers/ocr_local.py`) | |
| **Sinh file Word** | `python-docx` + template placeholder | `notary_v2` (`services/word_engine.py`) | |
| **Đọc/ghi Excel** | `openpyxl` | `notary_v2`, `upload_lab` | |
| **So khớp chuỗi mờ** | `rapidfuzz` | `notary_v2` (fast audit) | Dùng cho soát chính tả, **không** dùng để ghép hồ sơ |
| **Web backend** | **Python FastAPI** | `notary_v2`; `notaryoffice` Central Hub (dự kiến) | |
| **ORM** | SQLAlchemy 2.x | `notary_v2` | |
| **Database** | **SQLite** | `notary_v2` (`notary.db`, `ocr_jobs.db`), `upload_lab` (`registry.sqlite3`) | Xem mục 3 về giai đoạn gộp |
| **Job nền / queue** | Celery, broker là SQLAlchemy trên SQLite | `notary_v2` (`celery_app.py`) | |
| **UI web** | Jinja2 template + static (không SPA framework) | `notary_v2` (`frontend/`) | |
| **UI desktop** | **PySide6 / Qt** | `upload_lab` (`ui_qt/`) | |
| **Tự động hóa web nhà nước** | **Playwright** (Chromium) | `upload_lab` | Session lưu ở `nd_storage_state.json` |
| **Agent trên máy trạm** | **C# .NET 8** | `notaryoffice` (dự kiến) | Ràng buộc: <30MB RAM, <0.5% CPU |
| **Nhận media từ Zalo** | `zca-js` (Node) như connector thay thế được | `notary_v2` (Zalo Document Inbox) | Xem mục 4 |
| **Test** | `pytest`; `playwright` cho e2e | cả `notary_v2` và `upload_lab` | |

**API key và secret:** đặt trong `.env` của từng repo, đã `.gitignore`. Không bao
giờ ghi key vào tài liệu, không commit `.env`. Mẫu biến ở `.env.example`.

---

## 2. Quy tắc chọn công nghệ mới

Trước khi thêm một thư viện/dịch vụ mới, agent phải kiểm tra theo thứ tự:

1. **Bảng mục 1 đã có công nghệ cho việc này chưa?** Có → dùng nó.
2. Nếu muốn dùng thứ khác: viết được **một câu lý do kỹ thuật** vì sao cái đang
   có không đủ (không phải "cái này quen hơn", "cái này mới hơn").
3. Nếu vẫn muốn đổi → **dừng, hỏi chủ dự án**, rồi cập nhật bảng mục 1 kèm lý do.
4. Việc chưa có trong bảng → chọn, rồi **thêm dòng vào bảng** trong cùng task.

**Không được** đưa vào một OCR provider thứ hai, một ORM thứ hai, một cơ chế
queue thứ hai, hay một framework UI thứ ba mà không qua bước 3.

---

## 3. Ràng buộc thiết kế để lúc gộp không xung đột

Định hướng: gộp thành **một hệ thống, một database dùng chung**; các repo trở
thành công cụ xử lý dữ liệu theo mục đích riêng. Chưa làm bây giờ. Nhưng từ giờ,
mỗi repo nên tuân theo mấy điều dưới đây để lúc gộp không phải viết lại:

- **Khóa định danh hồ sơ chuẩn hóa giống nhau.** Đây là điều kiện quan trọng
  nhất. Xem `contracts/entities.md`. Hai repo lưu CCCD khác định dạng thì lúc
  gộp không join được.
- **SQLite là mặc định hiện tại; đừng dùng tính năng riêng của SQLite ở tầng
  nghiệp vụ.** DB chung sau này có thể là PostgreSQL. Cụ thể: đi qua SQLAlchemy
  hoặc SQL chuẩn, tránh `rowid` ẩn, tránh dựa vào kiểu lỏng của SQLite, không
  lưu số/ngày dưới dạng chuỗi tự do.
- **ID phải không trùng giữa các repo.** Đừng dùng số tự tăng bắt đầu từ 1 làm
  khóa nghiệp vụ nếu record đó sẽ đi vào DB chung. Dùng UUID hoặc tiền tố nguồn.
- **Ngày tháng lưu ISO-8601, giờ lưu kèm múi giờ hoặc quy ước rõ ràng.** Không
  lưu `dd/mm/yyyy` vào cột dữ liệu (hiển thị thì tùy).
- **Tên trường cho cùng một thứ phải giống nhau khi tạo bảng mới.** Đang có sẵn
  từ `notary_v2/docs/platform/document-intake/property-rules.md`: `so_serial`,
  `so_vao_so`, `so_thua_dat`, `so_to_ban_do`, `dia_chi`, `ngay_cap`,
  `co_quan_cap`, `dien_tich`. Repo khác tạo bảng tài sản thì dùng đúng các tên
  này.
- **Không hard-code đường dẫn tuyệt đối và không hard-code môi trường.** Cấu
  hình qua `.env`.

---

## 4. Điểm gọi ra ngoài văn phòng — danh sách đầy đủ

Mặc định hệ thống chạy trong LAN. Mọi lần gọi ra Internet phải nằm trong danh
sách này; thêm điểm mới là quyết định kiến trúc, phải hỏi.

| Điểm | Ra đâu | Gửi gì | Repo |
|---|---|---|---|
| Cloud OCR | DashScope (Alibaba) | ảnh giấy tờ khách hàng | `notary_v2` |
| Upload CSDL công chứng | web tỉnh Nam Định | dữ liệu hồ sơ đã hoàn tất | `upload_lab` |
| Zalo | server Zalo | tin nhắn/ảnh của tài khoản văn phòng | `notary_v2`; `notaryoffice` (dự kiến) |

`notaryoffice` Sentinel trên máy trạm: **không gọi Internet**, chỉ gửi JSON về
Hub trong LAN.

Lưu ý pháp lý: ảnh CCCD gửi ra dịch vụ OCR nước ngoài thuộc phạm vi **Nghị định
13/2023**. Đây là quyết định đã có chủ ý, không phải mặc định — đừng mở thêm
điểm gọi ra ngoài mà không hỏi.
