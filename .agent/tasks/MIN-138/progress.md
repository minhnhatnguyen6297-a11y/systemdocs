# Progress — MIN-138

## Trạng thái: hoàn tất triển khai, chờ review — 2026-09-29

## Đã làm

- Kiểm kê 33 file Markdown dưới `docs/` và các đường dẫn từ module.
- Chốt nguyên tắc: một cây spec; kiến trúc, giao diện, câu hỏi và lịch sử nằm tại cấp nhỏ nhất mà chúng ảnh hưởng.
- Dựng cây `docs/spec/` theo hệ thống → module → flow → feature.
- Tạo spec cho `notary_v2` theo `Input → Stage → Pool → Diagram → Word`, cùng
  spec `upload_lab`, `notaryoffice` và UI chung.
- Viết lại `README.md` thành bản đồ duy nhất; `AGENTS.md` thành luật đặt nội
  dung theo phạm vi và mẫu feature nhỏ.
- Chuyển prototype, ảnh duyệt và token sang `docs/spec/ui/`.
- Sửa link ở module, contract, shell và mẫu task.
- Xóa 31 file cũ dưới `docs/architecture`, `docs/product`, `docs/maintenance`
  và 3 ADR rời trong `notary_v2/docs/architecture`; rule agent còn hiệu lực đã
  nhập vào `AGENTS.md`. Lịch sử vẫn khôi phục được từ Git/Linear.

## Đã làm ngày 30/09/2026 (theo feedback owner)

- Cập nhật `AGENTS.md` và `docs/spec/README.md`: loại bỏ tham chiếu `main` lỗi thời; xác định `consolidate/monorepo` là nhánh default duy nhất chứa runtime Electron và tài liệu.
- Gỡ bỏ mục "Phối hợp và khôi phục công việc" trong `AGENTS.md`: tinh giản các quy tắc chia worktree/task record để tuân thủ cơ chế điều phối của Multica.

## Bước tiếp theo

- Đẩy commit lên remote `origin/consolidate/monorepo`.
- Báo cáo kết quả và chuyển issue sang `in_review`.

## Check đã chạy

- `git status --short --branch`: sạch trước khi bắt đầu.
- `rtk git diff --check`: sạch.
- Tìm toàn repo trên Markdown, JSON, HTML, CSS, JavaScript và Python: không còn
  tham chiếu `docs/architecture`, `docs/product`, `docs/maintenance` hoặc tên
  SOT cũ trong file đang dùng.
- Kiểm 46 file Markdown thay đổi/mới: không có link local trỏ tới file thiếu.
- `notary_v2/tests/test_docs_structure.py`: 4 passed, 1 skipped.
- Validator contract: G1 10/10; Notary 68/68; Zalo Draft 100/100, không có kết
  quả bất ngờ.
- Review 4 góc nhìn: mọi phát hiện đã được kiểm và sửa hoặc bác bỏ có bằng
  chứng; không có việc hoãn lại.
