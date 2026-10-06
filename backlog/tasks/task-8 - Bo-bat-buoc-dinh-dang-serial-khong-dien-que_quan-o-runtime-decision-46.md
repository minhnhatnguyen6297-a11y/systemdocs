---
id: TASK-8
title: Bo bat buoc dinh dang serial + khong dien que_quan o runtime (decision-46)
status: To Do
assignee: []
created_date: '2026-10-06 16:35'
labels:
  - decision-46
dependencies: []
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Owner 06/10: serial nguyen van o moi tang (extraction, Stage, DB, schema, validator) - bo pattern [A-Z]{2}+so, bo bat buoc, cho phep trung. place_of_origin giu truong de doc snapshot cu nhung intake/extraction khong dien. SOT da cap nhat (entities.md, contract, schemas). Con phai sua runtime: notary_mock_adapter.py (~SERIAL_RX/required/dup check), notary_v2/services/case_workspace.py (so_n_format), normalization.py, ocr_pipeline.py, frontend templates/properties/form.html + cases/form.html, regex_workbench profile rule so_serial, shell/sidecar, tests lien quan.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Khong con cho nao bat buoc format serial hoac coi serial trong la loi;place_of_origin khong duoc dien boi intake/extraction nhung van doc duoc du lieu cu;tests lien quan cap nhat va pass
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [ ] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [ ] #3 Tests pass
<!-- DOD:END -->
