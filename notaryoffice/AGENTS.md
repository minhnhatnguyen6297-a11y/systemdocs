# AGENTS.md — notaryoffice

**Trạng thái: tài liệu, chưa có code.** Đừng mô tả nó như hệ thống đang chạy.

## Source of truth
1. `intent.md` — Nguồn Chân lý Duy nhất: Tầm nhìn, nghiệp vụ, Hybrid Pipeline, Evidence Record, Draft Case, 14 bảng DB, quyết định đã chốt, phương án đã loại, lộ trình & chi phí.

## Rules
- Trước khi viết code: A1 / A3 / A4 ở systemdocs `OPEN_DECISIONS.md` phải có câu
  trả lời thật (A2 đã chốt = Không).
- Print Spooler **không cho biết số bản in**. Không thiết kế feature nào cần con
  số đó.
- Không đề xuất lại các phương án đã loại trong `intent.md`.
- Không quay màn hình, không keylogger, không dùng cho chấm công.
- Zalo: chỉ tài khoản chung của Văn phòng, chỉ trên máy chủ. Không đọc tài khoản
  Zalo của nhân viên.
- Giới hạn cứng 3 popup xác nhận/người/ngày — không nới.

## Cross-product context (read only when needed)
`D:\systemdocs` — tài liệu cấp cha. Chỉ đọc khi task chạm ranh giới
sản phẩm hoặc khóa định danh dùng chung: `PROJECTS.md`,
`contracts/entities.md`, `OPEN_DECISIONS.md`.

**Bắt buộc đọc `TECH_STACK.md` trước khi** chọn công nghệ cho bất kỳ tầng nào
(Sentinel, Hub, DB, OCR, queue, UI). Repo này chưa có code nên đây là nơi dễ
chọn lệch nhất — hệ thống sẽ gộp về một database dùng chung.
