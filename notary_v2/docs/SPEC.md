# SPEC — notary_v2 (Nguồn SOT nghiệp vụ duy nhất)

Đặc tả nghiệp vụ của module `notary_v2` trong monorepo `systemdocs`
(nhánh `consolidate/monorepo`). Mọi mô tả nghiệp vụ ở nơi khác
(`docs/domains/`, `docs/platform/`, root docs) là chi tiết hóa của file này;
nếu xung đột, **file này + code thật** thắng, và file này phải được sửa.

Quy tắc viết: chỉ ghi điều đã kiểm chứng bằng file thật; phân biệt rõ **hiện
trạng** và **dự định**. Cập nhật: 16/09/2026 (sau khi gộp monorepo).

## 1. Bài toán

Chuyên viên công chứng gõ lại bằng tay thông tin đã nằm sẵn trên giấy tờ
khách hàng (CCCD, sổ đỏ/GCN, giấy khai tử, đăng ký kết hôn) vào mẫu hợp đồng
Word — mỗi hồ sơ một lần, mỗi lần vài chục trường. Sai một số thửa hay một số
CCCD trong hợp đồng công chứng là lỗi nặng.

`notary_v2` đọc giấy tờ ra dữ liệu có cấu trúc, cho người dùng soát, rồi sinh
thẳng file Word.

## 2. Phạm vi nghiệp vụ (hiện trạng)

- **Intake giấy tờ bằng Cloud OCR** — upload ảnh/PDF giấy tờ, trích trường
  (họ tên, CCCD, ngày cấp, serial GCN, thửa/tờ, địa chỉ, diện tích) qua
  Qwen-VL-OCR trên DashScope + parser regex (`routers/ocr_ai.py`).
  **Người dùng soát trước khi dùng** — kết quả OCR không bao giờ tự thành
  dữ liệu nghiệp vụ.
- **Case Workspace (Stage / Pool / Diagram)** — gom giấy tờ theo hồ sơ, sơ đồ
  quan hệ đương sự (`routers/cases.py`, `frontend/` Jinja2 + ReactFlow).
- **Engine thừa kế** (`services/inheritance_engine.py`) — dựng hàng thừa kế,
  phần chia, sinh văn bản thừa kế. Workspace hiện inheritance-first.
- **Sinh văn bản Word** (`services/word_engine.py` + `word_templates/`) —
  điền dữ liệu vào template placeholder `{{...}}`, giữ định dạng.
- **Zalo Document Inbox** — nhận text/media qua connector Node `zca-js`
  (`zalo_connector/`, được `routers/zalo_inbox.py` spawn như subprocess),
  chọn lô ảnh, ghi vào hồ sơ. Ranh giới quyền riêng tư: `../../OPEN_DECISIONS.md` B2
  (tài khoản chung của văn phòng, chỉ chạy trên máy chủ).
- **Fast text audit** (`services/fast_audit/`, CLI `tools/run_fast_audit.py`)
  — soát sai lệch giữa văn bản Word đã soạn và dữ liệu gốc bằng `rapidfuzz`.
  Độc lập với luồng OCR.
- **POC conversion** (`tools/document_conversion_poc/`) — harness MarkItDown
  + golden fixtures; **chưa phải production**, chờ gate golden dataset.

## 3. Dữ liệu module sở hữu

SQLite `notary.db` (neo theo `__file__` trong `database.py`), SQLAlchemy +
`create_all` + 5 hàm migrate tay (`migrate_*`). Bảng nghiệp vụ
(`models.py`):

| Nhóm | Bảng |
|---|---|
| Nghiệp vụ hồ sơ | `customers`, `properties`, `inheritance_cases`, `inheritance_case_properties`, `inheritance_participants`, `word_templates`, `extracted_documents` |
| Zalo Inbox | `zalo_connector_accounts`, `zalo_sources`, `zalo_media`, `zalo_message_texts`, `zalo_data_sync_runs`, `zalo_batches` |

Quyền ghi `notary.db` thuộc module này; `shell/sidecar` dùng chung qua
`notary_adapter.py` (import trong-process, tự chạy lại migration khi engine
root trỏ vào đây).

## 4. Điểm gọi ra ngoài

| Đích | Gửi gì | Ghi chú |
|---|---|---|
| DashScope (Alibaba) — Qwen-VL-OCR | ảnh giấy tờ khách | quyết định có chủ ý, phạm vi Nghị định 13/2023; key trong `.env` |
| Server Zalo | tin nhắn/ảnh tài khoản chung văn phòng | qua `zalo_connector` (zca-js), receive-only |

## 5. KHÔNG phải / đã loại

- **Không còn Celery / `ocr_jobs.db` / local OCR stack** — đã gỡ khi merge
  (xem `memory-bank/`: `routers/ocr_local.py`, `celery_app.py`, GPU reqs bị
  xóa). Tài liệu cũ mô tả Celery là **lỗi thời**.
- **Không phải "core platform"** cho module khác — `upload_lab` không import
  code này; `shell` chỉ tiếp cận qua sidecar adapter.
- **Không nhận dữ liệu từ `upload_lab`** — không có luồng nào; Word do người
  dùng lưu thủ công là điểm nối duy nhất.
- **Local OCR parked** — mở lại cần redesign được duyệt riêng
  (`../../OPEN_DECISIONS.md` mục D).

## 6. Bản đồ tài liệu trong module

| Cần | Đọc |
|---|---|
| Domain thừa kế (spec, workflow, word export) | `docs/domains/inheritance/` |
| Intake giấy tờ + quy tắc trường tài sản | `docs/platform/document-intake/` |
| Stage/Pool/Case Workspace | `docs/platform/case-workspace/` |
| Sinh Word | `docs/platform/document-generation/` |
| Fast audit | `docs/platform/fast-text-audit/` |
| Zalo inbox | `docs/platform/zalo-document-inbox/` |
| ADR | `docs/architecture/decisions/` |
| Trạng thái phiên làm việc | `memory-bank/CURRENT.md` |
| Chạy/kiểm tra | `run.bat`, `verify.bat`, `tests/` |

## 7. Công nghệ (tóm tắt — SOT đầy đủ ở root `TECH_STACK.md`)

FastAPI + uvicorn, Jinja2 server-rendered (không SPA), SQLAlchemy/SQLite,
PyMuPDF + Pillow, `python-docx`, `openpyxl`, `rapidfuzz`, `zca-js` (Node
connector), pytest + `node --test` cho `*.test.mjs`.
