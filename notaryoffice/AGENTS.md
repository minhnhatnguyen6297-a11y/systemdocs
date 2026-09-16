# AGENTS.md — notaryoffice

**Trạng thái: tài liệu, chưa có code.** Đừng mô tả nó như hệ thống đang chạy.
Module này nằm trong monorepo — repo cũ trên GitHub chỉ còn archive.

## Source of truth
1. `docs/SPEC.md` — Nguồn Chân lý Duy nhất: Tầm nhìn, nghiệp vụ, Hybrid Pipeline, Evidence Record, Draft Case, 14 bảng DB, quyết định đã chốt, phương án đã loại, lộ trình & chi phí. (Trước đây là `intent.md`.)

## Rules
- Trước khi viết code: A1 / A3 / A4 ở `../OPEN_DECISIONS.md` phải có câu
  trả lời thật (A2 đã chốt = Không).
- Print Spooler **không cho biết số bản in**. Không thiết kế feature nào cần con
  số đó.
- Không đề xuất lại các phương án đã loại trong `docs/SPEC.md`.
- Không quay màn hình, không keylogger, không dùng cho chấm công.
- Zalo: chỉ tài khoản chung của Văn phòng, chỉ trên máy chủ. Không đọc tài khoản
  Zalo của nhân viên.
- Giới hạn cứng 3 popup xác nhận/người/ngày — không nới.

## Cross-module context (read only when needed)
Tài liệu cấp repo ở thư mục gốc monorepo. Chỉ đọc khi task chạm ranh giới
module hoặc khóa định danh dùng chung: `../SYSTEM_ARCHITECTURE.md`,
`../contracts/entities.md`, `../OPEN_DECISIONS.md`.

**Bắt buộc đọc `../TECH_STACK.md` trước khi** chọn công nghệ cho bất kỳ tầng nào
(Sentinel, Hub, DB, OCR, queue, UI). Module này chưa có code nên đây là nơi dễ
chọn lệch nhất — hệ thống sẽ gộp về một database dùng chung.
