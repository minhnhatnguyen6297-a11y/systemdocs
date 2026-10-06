---
id: TASK-8
title: Xu ly not cac mau thuan SOT (decision-46 + kiem ke 06/10)
status: To Do
assignee: []
created_date: '2026-10-06 16:35'
updated_date: '2026-10-06 16:48'
labels:
  - decision-46
dependencies: []
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Gom moi mau thuan con lai tu .agents/sot-inventory-20261006.md vao 1 task. Da chot: (1) serial nguyen van o moi tang — con runtime can don: notary_mock_adapter.py (required/invalid_format/dup check ~L985-995), notary_v2/services/case_workspace.py (so_n_format), normalization.py, ocr_pipeline.py, frontend templates/properties/form.html + cases/form.html, regex_workbench profile rule so_serial, shell/sidecar, tests. (2) place_of_origin giu truong de doc snapshot cu nhung intake/extraction khong dien — ra word_engine.py, zalo_inbox.py, cases.py, forms, tests. (3) Thong tin chung (so cong chung, ngay, cong chung vien) chua co truong trong contract — can quyet dinh contract truoc khi code; huong an toan owner da noi = bang thong tin ho so. Da xong trong engine thua ke: bo loi chung, nguoi chet = truong Nguoi, STK/BH gan co chua ho tro, khong suy gioi tinh, dien tich dau cham mo ho.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Khong con cho nao bat buoc format serial hoac coi serial trong la loi;place_of_origin khong duoc dien boi intake/extraction nhung van doc duoc du lieu cu;tests lien quan cap nhat va pass
- [ ] #2 Khong con cho nao bat buoc/doi format serial hoac coi serial trong/trung la loi;place_of_origin khong duoc dien boi intake/extraction nhung van doc duoc du lieu cu;Contract co (hoac quyet dinh ro khong co) truong thong tin chung: so cong chung, ngay, cong chung vien;Tests lien quan cap nhat va pass
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->
