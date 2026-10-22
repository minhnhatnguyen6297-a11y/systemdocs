---
id: decision-owner-802-diagram-height-20261016
title: "Owner chốt report 802: tăng CHIỀU CAO vùng Sơ đồ + Pool 50%"
date: '2026-10-16'
status: accepted
---
## Bối cảnh
Report 802 (`802bd69e-0b20-44df-8f83-7c83431fcd75`) ghi "tăng chiều dài của vùng sơ đồ + pool lên thêm 50%", đo tại viewport 1920×983 được rect 1603×484 (đúng vùng diagram của bố cục lúc đó). Trong #2, câu hỏi chặn là chốt "trục" tăng — chiều cao hay chiều rộng; assessment §1 (`_bmad-output/tmp/notary-flow-remediation/assessment-plan.md`) đề xuất diễn giải "chiều dài" = chiều cao, mục tiêu 726px từ 484px, nhưng ghi rõ đó là proposal chưa duyệt.
## Quyết định (owner trả lời '1')
- Owner chọn rõ: tăng CHIỀU CAO của vùng Sơ đồ + Pool (khu dưới Người/Tài sản) thêm 50%; KHÔNG tăng chiều rộng.
- Mốc 726px là SỐ KỸ THUẬT SUY RA, không phải một lệnh thứ hai của owner: lấy baseline đo được trong chính report 802 — 484px tại viewport report (1920×983) — nhân 1.5 → 726px. Đây là sàn (min-height) cho vùng, không phải chiều cao cố định.
- Viewport thấp: trang cuộn/pan như hiện có; không thu chữ/node.
- Giữ nguyên: cuộn/pan canvas, 30 chỗ Hai bên `p1..p30`, responsive (≤900px xếp dọc), và 5 report đã làm trong #2 (nhãn theo bằng chứng, bỏ nút Hủy thay đổi, Pool 224/240, ô Hai bên 202×52, thông báo tạm trong thanh trên).
- Không đổi quy tắc nghiệp vụ/pháp lý, schema, hay Word eligibility.
## Hệ quả
- Câu hỏi chặn của #2 (trục 802) đã được giải; phần 802 tiếp tục theo mốc trên trong cùng phase.
- Sàn chiều cao vùng (min-height 726px) là fix 802; phần tăng chiều cao do nội dung (ô Hai bên cao lên) KHÔNG được tính là fix 802.
- Điều kiện chứng minh bằng hình học thật trên chương trình default với dữ liệu tổng hợp tách riêng:
  1. Hồ sơ thừa kế nội dung thưa: vùng diagram được nâng lên đúng sàn 726px tại viewport report (fixture smoke đo trước fix 236px → sau fix 726px; khối gộp `.cd-rel-body` 244 → 734px). Mốc "+50%" là so với baseline 484px của chính report (484 × 1.5 = 726), không phải so với mọi fixture — fixture nào trước fix dưới sàn sẽ tăng nhiều hơn 50%.
  2. Hồ sơ Hai bên nội dung lớn: vùng giữ nguyên theo nội dung (fixture smoke đo 907px vùng / 874px world ở viewport probe) — không bị thu nhỏ, và KHÔNG cộng thêm 50% lần nữa.
  3. Sàn là mức tối thiểu: nội dung cao hơn vẫn quyết định chiều cao; canvas vẫn cuộn/pan; `p1..p30` và xếp dọc ≤900px giữ nguyên.
