---
id: TASK-8
title: Xu ly not cac mau thuan SOT (decision-46 + kiem ke 06/10)
status: To Do
assignee: []
created_date: '2026-10-06 16:35'
updated_date: '2026-10-06 17:23'
labels:
  - decision-46
dependencies: []
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Gom moi mau thuan con lai tu .agents/sot-inventory-20261006.md vao 1 task. CON LAI (runtime): (1) serial bat buoc/format/chong trung: notary_mock_adapter.py (~L985-995), notary_v2/services/case_workspace.py (so_n_format), normalization.py, ocr_pipeline.py, form.html + cases/form.html, regex_workbench profile rule so_serial, shell/sidecar, tests lien quan. (2) place_of_origin: giu truong doc snapshot cu nhung intake/extraction khong dien: word_engine.py, zalo_inbox.py, cases.py, forms, tests. (3) Thong tin chung (so cong chung, ngay, cong chung vien): chua co truong trong contract — can quyet dinh contract truoc khi code (huong owner: bang thong tin ho so). DA XONG: engine thua ke + spec regex-thua-ke v1.1 da chuan hoa — bo loi chung/R11, nguoi chet = truong Nguoi (so_giay_to/ngay_cap/noi_cap/dia_chi), STK/BH chi gan co tai_san_chua_ho_tro + R12, khong suy gioi tinh (trong -> R13), dien tich mo ho -> R13; regex_lab fingerprint gom ca validator, compare so tung truong va tu choi cache cu/dap an rong/JSON hong.
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
