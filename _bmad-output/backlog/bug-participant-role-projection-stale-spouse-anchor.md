---
id: 45
type: bug
title: "Vai trò quan hệ trong DB không cập nhật theo sơ đồ đã sửa và thiếu neo cặp vợ–chồng theo nhánh"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Vai trò quan hệ trong DB không cập nhật theo sơ đồ đã sửa và thiếu neo cặp vợ–chồng theo nhánh

## Description

Phát hiện khi kiểm chứng câu hỏi S10 của owner (bản thống kê chốt chặn Soạn hồ
sơ, 23/10/2026; biên bản `_bmad-output/tmp/feasibility-r7-s10-s17-r11-20261023.md`
mục 2): quan hệ trên sơ đồ thừa kế (cha/mẹ/vợ-chồng/con) được chiếu xuống bảng
chuẩn `inheritance_participants` mỗi lần Lưu, và engine Word đọc bảng này để
điền các placeholder quan hệ (vợ/chồng, người nhận…). Cơ chế chiếu có hai lỗ
hổng khiến dữ liệu chuẩn có thể sai lệch với sơ đồ hiện tại:

1. **Vai trò bị đóng băng sau lần lưu đầu.** Trong
   `notary_v2/services/case_workspace.py` (`_sync_participants_and_owner`,
   khoảng dòng 2239–2241): khi dòng participant đã tồn tại, `vai_tro` cũ được
   giữ nguyên và không bao giờ ghi lại theo hình dạng sơ đồ mới; chỉ
   `hang_thua_ke` được tính lại — theo chính vai trò cũ. Hệ quả: đổi quan hệ
   trên sơ đồ (đổi người làm vợ/chồng, dời một người sang nhánh khác) rồi Lưu
   lại, DB vẫn giữ vai trò cũ và Word điền placeholder quan hệ theo DB cũ —
   sai người trong văn bản. Nguyên nhân gốc: một cột `vai_tro` đang gánh cả
   hai loại vai trò khác nhau — vai trò suy từ vị trí sơ đồ và vai trò gán tay
   (ví dụ "Người được ủy quyền", chỉ sống ở cột này) — nên đường ghi không
   dám ghi đè.
2. **Thiếu neo cặp vợ–chồng theo nhánh.** `_project_role_nodes`
   (`case_workspace.py:528`) tính được "vợ/chồng của node nào" trong bộ nhớ
   nhưng không ghi xuống: dòng participant không có trường neo spouse theo
   cặp. Với vợ/chồng của người để lại còn suy lại được qua owner của hồ sơ;
   với vợ/chồng thuộc nhánh (vai trò con dâu/rể), cặp cụ thể chỉ còn tồn tại
   trong `case_state_json` của chính hồ sơ, không có ở tầng trường chuẩn.

Issue này chỉ ghi nhận và chờ chốt cách xử lý; chưa phải duyệt triển khai.

## Acceptance Criteria

1. **Vai trò suy từ sơ đồ luôn khớp sơ đồ đã lưu gần nhất** — **BUILT
   23/10/2026** (TC1: `fce15bd`)
   Verify: với một hồ sơ thừa kế tổng hợp (không dữ liệu cá nhân), đổi quan
   hệ trên sơ đồ sau lần lưu đầu — đổi người giữ vai trò vợ/chồng và dời một
   người sang vai trò khác — rồi Lưu lại; đọc `inheritance_participants` thấy
   `vai_tro` và `hang_thua_ke` của mọi dòng khớp hình dạng sơ đồ mới, và xuất
   Word điền placeholder vợ/chồng đúng người theo sơ đồ mới.
2. **Vai trò gán tay không bị ghi đè mất** — **BUILT 23/10/2026** (TC2:
   `fce15bd`)
   Verify: một dòng đã mang vai trò gán tay (ví dụ "Người được ủy quyền")
   vẫn giữ vai trò đó sau các lần Lưu có thay đổi sơ đồ không liên quan; cách
   phân biệt hai loại vai trò được ghi rõ trong spec/contract liên quan thay
   vì suy luận ngầm.
3. **Cặp vợ–chồng theo nhánh có trường chuẩn truy được** — **TẠM DỪNG
   23/10/2026**: phần neo cặp vợ–chồng tạm dừng — chờ kết luận thảo luận mô
   hình quan hệ của owner với Muse (nhiều vợ theo thứ tự, con theo từng cặp,
   con chung/con riêng). Không thiết kế, không thêm trường/storage mới ở lát
   này.
   Verify: với sơ đồ tổng hợp có vợ/chồng thuộc nhánh (con dâu/rể), trường
   chuẩn của hồ sơ xác định được cặp cụ thể (người này là vợ/chồng của
   người nào) mà không cần mở `case_state_json`; placeholder cần đúng cặp
   theo nhánh lấy được đúng người.
4. **Không hồi quy các đường đang đúng** — **BUILT 23/10/2026** (TC4:
   `fce15bd`)
   Verify: vai trò vợ/chồng của người để lại, neo cha/mẹ qua
   `parent_case_person_row_id`, và luồng xuất Word legacy (slot chủ đất/vợ
   chồng/người nhận) vẫn cho kết quả như trước trên các ca kiểm chứng
   hiện có.

## Notes

- 2026-10-23 — **Phần vai_tro built, vé CHƯA đóng.** Owner (qua Muse) chia lát
  5 đợt sửa lỗi E2E: làm re-projection vai trò (TC1/TC2/TC4) ngay vì cần cho
  mọi mô hình quan hệ; **TC3 (neo cặp vợ–chồng) tạm dừng** chờ owner chốt mô
  hình quan hệ với Muse. [Decision](../decisions/decision-participant-role-projection-scope-20261023.md).
- Cách phân biệt hai nguồn vai trò (ghi ở contract §13.19 + spec sơ đồ §4):
  bộ vai trò suy-từ-sơ-đồ hữu hạn — `Vợ/Chồng`, `Cha`, `Mẹ`, `Cha_vc`,
  `Me_vc`, `Con_dau_re`, `Con`, `Anh/Chị/Em`, `Cháu`, `Khac`; giá trị ngoài
  tập này là gán tay và được giữ. Không thêm cột nguồn/migration.
- Code: `notary_v2/services/case_workspace.py` — `_DIAGRAM_ROLES`,
  `_is_manual_role`, `_sync_participants_and_owner`.
- Proof: `notary_v2/tests/test_case_workspace.py`
  (`test_commit_stage_reprojects_derived_roles_to_latest_diagram`,
  `test_commit_stage_preserves_manual_participant_role`,
  `test_commit_stage_projects_full_family_with_parent_anchor_and_word_slots`);
  bộ pytest lõi 6 file 290 passed/0 failed (baseline đầu đợt 287, +3 test mới).
- Còn mở khi làm TC3: người được gán tay `Người được ủy quyền` đang giữ vị
  trí vợ/chồng thì cột `vai_tro` chỉ còn vai trò gán tay → slot Word
  vợ/chồng trống; cần nguồn quan hệ riêng (cùng phạm vi TC3).
