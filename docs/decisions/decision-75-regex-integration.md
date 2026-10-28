---
id: decision-75
title: Gộp regex sweep vào nhánh chính, giữ cấu trúc BMAD và dữ liệu kiểm nguồn
date: '2026-10-08'
status: accepted
---

## Quyết định

Owner yêu cầu commit và gộp nhánh regex vào `consolidate/monorepo`, xử lý xung đột. Yêu cầu này thay giới hạn không commit của TASK-10.3.

Giữ cấu trúc của nhánh chính: spec tại `docs/specs/`, quyết định tại `docs/decisions/`, task Backlog cũ tại archive. Không phục hồi cây SOT `docs/spec`, Backlog đang hoạt động hoặc các thư mục agent cũ.

Giữ toàn bộ sửa lỗi đã kiểm và nhãn nơi cấp giấy tờ trên Stage. F01/F04/F05 vẫn Pending. Không tạo luật sửa lỗi nguồn hoặc chức năng mới. Hai engine, validator và fixture dùng cùng xuống dòng LF để bản sao không lệch do Git trên Windows.

Quyết định nhập từ nhánh regex có mã cũ trùng nhánh chính được giữ riêng: `regex-decision-46`, `regex-decision-47`, `regex-sweep-48`. Các decision-46/47/48 của nhánh chính giữ nguyên.

## Tại sao

Nhánh chính đã chuyển SOT theo decision-48, trong khi nhánh regex phát triển trên cấu trúc cũ. Gộp cần giữ cả sửa lỗi sản phẩm và cấu trúc tài liệu đã duyệt; không dùng một bên để ghi đè toàn bộ bên kia. Mã riêng tránh hiểu nhầm hai quyết định khác nội dung là một.

Corpus và bằng chứng cá nhân giữ tại máy trong worktree gốc; không commit Word thật, database, môi trường test hoặc bản trích cá nhân. Spec và test lâu dài dùng nguồn tổng hợp. Chỉ gộp cục bộ, không push.
