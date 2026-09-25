# Brief — MIN-91

**Linear:** https://linear.app/minhnotary/issue/MIN-91/goal-zalo-repo-djoc-lap-xu-ly-giay-to-djen-input-soan-ho-so · **Ngày bắt đầu:** 2026-09-24 · **Nhánh plan:** consolidate/monorepo

## Mục tiêu

Điều phối goal triển khai Zalo độc lập bằng 12 task MIN-92..103 theo [plan](../../../docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md); MIN-93 dựng scaffold, MIN-103 chuyển engine Zalo thành module thứ tư. Lượt này chỉ cập nhật tài liệu và giao việc, chưa triển khai runtime.

## Phạm vi

- Spec tổng thể/draft giao tiếp ở `docs/product/specs/`; spec nội bộ ở `notary_v2/docs/platform/zalo-document-inbox/`.
- Repo module đề xuất `D:/zalo-intake` là đầu ra tương lai của MIN-93, chưa có trong lượt plan.
- Giao tiếp contract trước code; hai repo không chia DB/source/ảnh. Bot gọi Qwen OCR gần ảnh và chỉ giao raw/status/nguồn; Document Intake trong Soạn hồ sơ bóc trường và ghép/nhóm sau Sync.

## Bằng chứng nghiệm thu lượt plan

Linear có goal, task/quan hệ phụ thuộc và mô tả; plan có file/interface/gates/tests; kiểm link/JSON/diff và review consistency. Goal triển khai MIN-91 vẫn Todo cho đến khi runtime/đánh giá/UI đạt.
