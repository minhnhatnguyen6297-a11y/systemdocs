---
title: 'Bản đồ tri thức theo bốn sản phẩm'
type: 'chore'
ticket: ''
created: '2026-09-28'
status: 'built'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'auto'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
baseline_revision: '155d6e4cb4b3da079099ea5d5a393730c6fb31b0'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Chỉ mục theo từng quyết định vừa tạo làm tài liệu vụn vặt và có nguy cơ thành SOT song song; agent chưa có luật buộc tra bản đồ trước khi tạo doc mới.

**Approach:** Gỡ `DECISION_INDEX.md`; biến `KNOWLEDGE.md` thành bản đồ duy nhất theo bốn phần owner nêu, mỗi phần có hạng mục, flow, nguồn quyết định và khoảng trống. `AGENTS.md` bắt buộc chọn owner, cập nhật file hiện có trước và đăng ký file mới vào bản đồ. Root README chỉ dẫn tới bản đồ. Giữ lời giải thích gốc của owner.

</frozen-after-approval>

## Implementation Notes

- Tài liệu thuần, phạm vi gọn, đi thẳng một lượt theo route oneshot.
- Tạo chỉ mục 12 mục, tách lý do diễn giải và lời gốc; ghi thiếu từ điển Người và lệch câu về vị trí repo Zalo để không suy diễn.
- Link từ `KNOWLEDGE.md`; ghi record trong `.agent/tasks/MIN-135/`.
- Owner bác cấu trúc chỉ mục theo quyết định, yêu cầu bốn trục sản phẩm và luật khống chế tạo docs; lần triển khai này thay thế kết quả trước, không thêm kho tài liệu mới.
- Đã thay `KNOWLEDGE.md` bằng bản đồ bốn phần, xóa `DECISION_INDEX.md`, cập nhật `AGENTS.md`/README và định tuyến Zalo snapshot theo nguồn hiện có. Không tạo spec module mới khi các file sở hữu đã tồn tại.
- Quick review nêu va chạm A1–A4 giữa root và Notary Office, cùng mô tả Zalo cũ. Chuyển lý do A2/rủi ro xác nhận về Office, B1 về Upload, để root làm pointer; sửa mô tả repo Zalo theo README của snapshot.
- Lượt rà soát lại tìm bảng phương án loại ở root và đoạn A2 trong kiến trúc còn lặp kết luận. Đã chuyển chúng thành pointer tới nơi sở hữu, cập nhật ngày định tuyến SOT và kiểm tra link.

## Plan Change Log

- 2026-09-28: Owner chỉ rõ chỉ mục theo từng quyết định tạo phân mảnh và tranh chấp SOT. Thay ý định bằng bản đồ bốn phần, loại bỏ `DECISION_INDEX.md`, thêm cổng tạo file vào `AGENTS.md`; giữ nguyên yêu cầu lưu “tại sao”.

## Review Triage Log

- Quick review: 1 finding `medium` — thiếu `.agent/tasks/MIN-135/handoff.md` theo `AGENTS.md`; đã bổ sung file bàn giao.
- Quick review lần sửa cấu trúc: `medium` — A1–A4 có hai bảng kết luận trong `OPEN_DECISIONS.md` và `notaryoffice/intent.md`; chuyển về Office, root chỉ dẫn, giữ lý do A2.
- Quick review lần sửa cấu trúc: `medium` — mục B2 cấp hệ thống còn nói repo/folder Zalo chưa có; sửa theo `zalo/README.md` và `zalo/docs/repo-ownership.md`.
- Quick review lại: `medium` — `OPEN_DECISIONS.md` §D còn bảng quyết định lặp B1/A2 và lựa chọn Office; đổi thành mục đường dẫn tới file sở hữu.
- Quick review lại: `medium` — `SYSTEM_ARCHITECTURE.md` còn ghi đầy đủ A2 và trỏ nguồn cũ; rút thành mô tả tín hiệu và link thẳng tới `notaryoffice/intent.md`.
- Quick review lại: `low` — ngày cập nhật định tuyến trong `OPEN_DECISIONS.md` còn 10/09; đổi thành 28/09 và giải thích đây không phải ngày chốt lại quyết định gốc.

## Verification

**Commands:**
- `git diff --check` — không có lỗi định dạng.
- Kiểm tra từng link file trong bản đồ tồn tại, không còn link tới `DECISION_INDEX.md`, và root README chỉ dẫn tới bản đồ.
