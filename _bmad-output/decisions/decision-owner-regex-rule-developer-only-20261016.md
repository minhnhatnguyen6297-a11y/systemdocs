---
id: decision-owner-regex-rule-developer-only-20261016
title: "Owner chốt: rule regex văn bản và rule upload theo website do developer quản lý"
date: '2026-10-16'
status: accepted
---
## Bối cảnh
#8 (spike vòng đời rule) hỏi ai được công bố rule đã thử, nguồn rule có quyền ghi ở đâu, ghi nhận kích hoạt version/hash và rollback thế nào, duyệt khác biệt chạy lại ra sao mà không ghi đè Stage/binding đã xác nhận (`_bmad-output/backlog/spike-regex-rule-lifecycle.md`, Notes). Trong phiên 16/10/2026, owner trả lời ở mức phạm vi (nguyên văn):

> "tôi không chắc câu bạn hỏi, nhưng nếu là về vấn đề: rule regex văn bản và rule upload lên các web khác nhau thì đây là phân biệt dành cho developers, có phân biệt phiên bản để nhận biết. Users không được dùng tính năng này"

## Quyết định
- Rule regex văn bản và rule upload theo từng website thuộc phạm vi developer; rule có phân biệt phiên bản để nhận biết.
- Người dùng sản phẩm không dùng tính năng quản lý rule: không có thử, công bố, chọn phiên bản hoặc rollback rule trên UI người dùng.
- Người dùng vẫn xem và sửa kết quả bóc tách trước khi nhận vào Stage như quy tắc hiện hành; phần bị loại là quản lý rule, không phải duyệt kết quả.
- Các lựa chọn kỹ thuật còn lại — nơi lưu rule, định dạng, ghi nhận version/hash, kích hoạt/quay lui nội bộ, phạm vi chạy lại — do developer quyết định khi triển khai; decision này không chốt sẵn thuật toán và không thêm role/permission mới.

## Hệ quả
- #8: câu hỏi nghiệp vụ đã được trả lời bởi decision này; phần còn lại là kỹ thuật của developer, không phải câu hỏi nghiệp vụ cho owner.
- #23: superseded — mục tiêu đưa thử/công bố/chọn phiên bản/chạy lại-duyệt vào flow người dùng bị loại; leaf giữ làm lịch sử, không triển khai.
- #22 (parity core chung) vẫn nguyên hiệu lực, không đổi phạm vi.
- Cách diễn đạt lịch sử "chỉnh dần khi test" / "chỉnh quy tắc rồi chạy lại" ([decision tổng 13/10](decision-notary-flow-consolidated-remediation.md): "tích hợp vào flow thật để chỉnh dần khi test"; [#1](../backlog/bug-notary-flow-ui-regex-word.md) Description, AC6, Notes 13/10) được hiểu là developer chỉnh/thử rule, không phải tính năng người dùng; luồng người dùng thật vẫn dùng regex core chung và xem/sửa kết quả bóc tách trước khi nhận vào Stage.
- Spec cập nhật cùng phiên: `_bmad-output/specs/README.md` §6, `_bmad-output/specs/shared/extraction-rules.md` §7.2, `_bmad-output/specs/upload_lab/README.md` §2.4; sổ tay `_bmad-output/specs/product-overview.md`; catalog backlog C07/C21/C22.
