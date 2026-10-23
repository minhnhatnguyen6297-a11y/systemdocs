---
id: decision-participant-role-projection-scope-20261023
title: "Vai trò participant: re-projection mỗi lần Lưu; tạm dừng neo cặp vợ–chồng"
date: '2026-10-23'
status: accepted
---

## Bối cảnh

Owner (truyền qua Muse) đang thảo luận trực tiếp mô hình quan hệ trong sơ đồ:
nhiều vợ theo thứ tự, con theo từng cặp vợ–chồng, phân biệt con chung/con
riêng. Mô hình này có thể thay thế thiết kế “neo cặp vợ–chồng theo nhánh” mà
issue #45 đề xuất. Vì vậy lát 5 của đợt sửa lỗi E2E được chia hai.

## Quyết định

1. **Làm ngay — re-projection vai trò.** Vai trò suy từ sơ đồ
   (`inheritance_participants.vai_tro`, `hang_thua_ke`) được ghi lại theo
   Diagram đã lưu gần nhất ở mọi lần Lưu, kể cả dòng đã tồn tại. Phần này cần
   cho mọi mô hình quan hệ nên không phụ thuộc kết luận sắp tới.
2. **Phân biệt hai nguồn vai trò không cần cột mới.** Bộ vai trò suy-từ-sơ-đồ
   là hữu hạn (`Vợ/Chồng`, `Cha`, `Mẹ`, `Cha_vc`, `Me_vc`, `Con_dau_re`,
   `Con`, `Anh/Chị/Em`, `Cháu`, `Khac`). Giá trị `vai_tro` ngoài tập này là vai
   trò gán tay (vd `Người được ủy quyền`) và được giữ nguyên. Đã cân nhắc thêm
   cột `vai_tro_nguon` và loại: không cần thiết vì dấu hiệu nguồn đã có trong
   dữ liệu, thêm cột kéo theo migration + wire + nguy cơ lệch hai nguồn.
3. **Tạm dừng — neo cặp vợ–chồng theo nhánh (TC3).** Không thiết kế, không
   thêm trường/storage mới cho neo cặp ở lát này. Chờ kết luận thảo luận mô
   hình quan hệ của owner với Muse. Vé #45 giữ mở cho TC3.

## Hệ quả đã chấp nhận

- Một dòng chỉ mang một `vai_tro`: người vừa có vị trí quan hệ vừa được gán
  tay vai trò khác thì vai trò gán tay thắng ở cột này (Word vẫn đọc vị trí
  sơ đồ cho các nhóm khác). Hệ quả phụ: nếu người được gán tay
  `Người được ủy quyền` đang giữ vị trí vợ/chồng thì slot Word “vợ/chồng”
  trống cho tới khi có nguồn quan hệ riêng — thuộc phạm vi TC3 đang mở.
- Người không còn node (gỡ/ẩn/xóa) vẫn bị xóa khỏi bảng participant như trước.
- Vai trò gán tay trùng đúng chuỗi của bộ suy-từ-sơ-đồ (vd gán tay `Con`)
  không phân biệt được và do sơ đồ quyết định; quy tắc này ghi trong
  contract §13.19 và spec sơ đồ §4.

## Nguồn

- Issue: [#45](../backlog/bug-participant-role-projection-stale-spouse-anchor.md).
- Contract: `contracts/notary-case-drafting.md` §13.19.
- Spec: `_bmad-output/specs/notary_v2/diagram-rules.md` §4.
