# Decisions — MIN-126

Task này là **bản mẫu để duyệt** — theo chỉ đạo MIN-123/MIN-126, các lựa chọn
nghiệp vụ chưa chốt được **đề xuất** trong bản mẫu nhưng không được coi là
quyết định. Mục "Đã chọn trong phạm vi task" chỉ gồm quyết định kỹ thuật của
chính bản mẫu.

## Đã chọn trong phạm vi task (kỹ thuật — có thể đổi ở P4)

### 2026-09-28 — Vanilla HTML/CSS/JS, không framework
- **Chọn:** 6 file thuần (`index.html` + 1 css + 4 js), không import runtime.
- **Lý do:** bản mẫu cần mở `file://` được, không build; tránh kéo React/React
  Flow của renderer cũ vào prototype (MIN-126 cấm transplant logic cũ).
- **Nguồn:** yêu cầu MIN-126 "standalone, không dependency mới".

### 2026-09-28 — Ánh xạ tay tokens.json → CSS var
- **Chọn:** copy giá trị token (proposed) vào `:root` trong `prototype.css`.
- **Lý do:** `tokens.json` không được sửa (P1 chưa chốt); bản mẫu phải độc lập,
  không đọc JSON lúc runtime để `file://` hoạt động.
- **Hệ quả:** nếu owner chỉnh token, phải sync tay vào `prototype.css` hoặc đợi
  P4 wire thật.

### 2026-09-28 — Hai panel Upload luôn mounted
- **Chọn:** cả Audit + Quét render cùng lúc, tab chỉ lật `display`.
- **Lý do:** yêu cầu "chuyển tab giữ trạng thái + vị trí cuộn"; giữ DOM là cách
  đơn giản nhất demo đúng hành vi đó (bản thật có thể khác — ví dụ keep-alive).

## ĐỀ XUẤT CHỜ OWNER CHỐT (không tự quyết — ghi lại để duyệt)

Các mục dưới đây bản mẫu hiển thị **một** phương án cụ thể để duyệt được —
phương án đó là đề xuất, không phải SOT:

| # | Chủ đề | Đề xuất trong bản mẫu | Chờ |
|---|---|---|---|
| 1 | Chip số `1 2 3` trên node | số = thứ tự cột tài sản; 2 hàng `Chủ đất`/`Nhận đất` | P2 (MIN-125) + owner |
| 2 | Drop lên chỗ/node đã có người | **swap** — hai người đổi chỗ | owner |
| 3 | `Hủy thay đổi` | chỉ revert Stage draft về bản đã commit, giữ Diagram draft | owner (spec cũ chưa rõ phạm vi) |
| 4 | `Áp dụng` trong dialog Loại đất | ghi vào **draft** Stage → hiện dirty → `Cập nhật` mới commit | owner |
| 5 | `Mở rộng` | overlay ~toàn màn trong app, Esc/× đóng, trả focus | owner |
| 6 | Rail icon vs sidebar nhãn | rail sáng 60px theo ảnh approved | owner |
| 7 | Breakpoint responsive | 1000px xếp dọc Stage; 800px compact | owner |
| 8 | Hai bên 30 chỗ | A = chỗ 1–15, B = 16–30; card = Chỗ N + tên | owner/P2 |
| 9 | Token values | toàn bộ `proposed` — bản mẫu chỉ minh họa | owner duyệt trên bản mẫu |
| 10 | Focus vào dialog | control đầu trong body (đã implement); Esc đóng + trả opener | owner |
| 11 | Toast cho lỗi retryable | toast 4s + banner inline tồn tại; không modal | owner |
| 12 | Zalo | hiển thị **disabled + tooltip** (không ẩn) | owner |

Ràng buộc đã tuân: không backend/IPC/website thật; không sửa contract/schema/
DESIGN/EXPERIENCE/tokens/runtime; Zalo không ẩn; Word giữ vị trí nút, không
thiết kế popup mới; chú thích chờ duyệt nằm trong comment/README/task files —
không rải text giải thích lên UI.
