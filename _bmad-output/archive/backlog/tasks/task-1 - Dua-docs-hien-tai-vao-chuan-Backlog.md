---
id: TASK-1
title: Dua docs hien tai vao chuan Backlog
status: Done
assignee:
  - '@devin'
created_date: '2026-10-04 14:43'
updated_date: '2026-10-05 04:06'
labels:
  - docs backlog
dependencies: []
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
docs/ dang viet tay (spec, docs, quyet dinh). Can dua vao cau truc backlog: doc + decision, giu docs/spec lam SOT.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Liet ke du file trong docs/ (notaryoffice, notary_v2, ui, upload_lab + README)
- [x] #2 Moi tai lieu lau dai co 1 backlog doc tro dung file goc
- [x] #3 Moi quyet dinh kien truc co 1 backlog decision (Context, Decision, Consequences)
- [x] #4 docs/spec van la SOT, khong mat noi dung khi chua duyet
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Spec trong docs/spec đã cập nhật hoặc thêm mới
- [x] #2 Quyết định đã ghi vào backlog decision (là gì, tại sao)
- [x] #3 Tests pass
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Quet cay docs/ va doc header tung file. 2. Tao backlog doc pointer cho moi tai lieu lau dai (doc-1..38) + doc-39 inventory. 3. Trich quyet dinh kien truc tu spec thanh backlog decision-22..39 (bo trung 1..21). 4. Them dong vao docs/spec/README.md muc 9 ghi ro backlog chi la lop con tro, docs/spec van SOT.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Da tao 38 doc pointer (doc-1..doc-38) duoi backlog/docs/spec/ mirror cau truc docs/spec; moi doc ghi File goc + Trang thai + Dung cho. doc-39 la inventory du file ke ca asset nhi phan. Da tao decision-22..39 cho quyet dinh kien truc he thong/module trich tu spec (Electron shell dich, pipeline sidecar, chuoi du lieu 5 lop, LAN/Internet egress, stack chung, rang buoc gop DB, ranh gioi module, Stage v2 revision, khong port engine JS, portal tu bam Luu, POC ITERATE, Bando kho local, Sentinel+Hub/A2, UI tokens/CSS prefix, quy uoc backlog=pointer/spec=SOT). CLI khong ho tro body decision nen title mang context+quyet dinh+ly do theo convention repo; 8 title ban dau qua 255 ky tu duong dan Windows nen rut ngan lai. Chung minh: 'grep -rl File-goc backlog/docs' = 38; 'backlog doc list' = 39 docs; 'backlog decision list' = 39; 'backlog doctor' sach; git status chi them file moi, docs/spec chi +3 dong README.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Dua docs/ vao chuan Backlog: 38 doc pointer (doc-1..38) + 1 inventory (doc-39) liet ke du moi file ke ca asset; 18 decision moi (decision-22..39) trich quyet dinh kien truc tu spec, them vao 21 decision cu; docs/spec/README.md them 1 dong muc 9 khang dinh docs/spec van la SOT va backlog chi la lop con tro. Verify: backlog doctor sach, doc list=39, decision list=39, grep File-goc=38 pointer, git diff chi them dong vao README khong mat noi dung. Task la docs-only nen khong co test suite; check thay the = backlog doctor + git status.
<!-- SECTION:FINAL_SUMMARY:END -->
