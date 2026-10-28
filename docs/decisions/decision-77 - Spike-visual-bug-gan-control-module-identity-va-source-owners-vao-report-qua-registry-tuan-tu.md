---
id: decision-77
title: >-
  Spike-visual-bug schema v2: gan control/module identity + source owners vao
  report qua registry tuan tu, KHONG phan tich DOM tu doan
date: '2026-10-11'
status: accepted
---
## Context

Report visual-bug spike v1 chi nhan dien phan tu duoc chon qua ancestor id shell
(generic/rail-logo/stage/module-tabs), nen 12 muc tieu notary that deu nhan cung
6 dong generic shell (ke ca dong upload), khong co component JS notary/upload,
khong co CSS, va upload tab id la im lang miss (selector `#ul-tab-*` khong bao
gio match). Evidence: `docs/tmp/visual-bug-linkage-evidence.json`,
`docs/tmp/visual-bug-code-linkage.html`,
`docs/tmp/visual-bug-source-linkage/matrix.json`.

## Decision

1. Picker gui them dinh danh cau truc (schema v2): `data-fid` gan nhat, class
   tokens cua chinh phan tu (classList, khong doc value/aria-label/text), va
   module root class (`cd-root`/`upload-lab`), tokens cua table gan nhat va
   co structural cell (`th`/`td`). Chi facet khop registry duoc persist;
   row id chuan hoa `{row}`/`{tabId}`, fid/id/class la bi bo mac dinh.
2. `linkage.cjs` la registry tuan tu nho: fid pattern / own-id pattern / class
   token -> component JS (symbol) + CSS selector co so (base rule only). Duong
   dong tim bang scan truc tiep tai moi save (cache chi trong mot save);
   anchor la declaration/selector, mat thi `stale:true`, khong doan/ghim dong.
3. Confidence ladder: `explicit-control-map` > `component-ancestry` >
   `module-ancestry` > `heuristic-static-id` > `unmapped`.
   Own token/fid co `scope: exact`; hit `th`/`td` co the map table to tien
   voi `scope: ancestor-table`. Control tuong tac la nam trong table chi co
   `component-ancestry` + `container`, khong nhan exact control id.
   `source.candidates` (ancestor tier) giu
   nguyen va la tier rieng; owners phat bieu "ai render/style phan tu nay",
   KHONG phai vi tri nguyen nhan loi.
4. CSS anchor phai la selector chinh xac co khoa mo (`'.cd-root {'`,
   `'.ul-tab {'`) de tranh match nhoi `.cd-root-outer`/`.ul-tablist`.
   `cd-stage-tbl` gan cho CA assetTableEl va peopleTableEl; dia chi (a:/p:)
   phan biet qua fid chu khong qua class walk vi suggestion div la sibling.
5. KHONG phan tich DOM heuristics tu doan (phan tich lop HTML de doan chu dong
   JS) — chi registry tuan tu duoc kiem chung boi nguoi/agent verification;
   ngoai registry thi context ro rang (component/module-ancestry) hoac unmapped.

## Consequences

- Report moi co `source.control` + `source.owners` + `source.confidence`; report
  cu (37 JSON, 32 PNG) giu nguyen byte-for-byte (schema cu khong doi).
- Registry phai duoc cap nhat khi them control notary/upload moi — chi phi thap
  (mot entry) va that bai la an tuong (stale) thay vi im lang sai.
- E2E sink tach rieng `docs/tmp/visual-bug-source-linkage/smoke-reports/`
  de ban ghi test khong lan voi ban ghi reporter.
- Gioi han: owners la ownership render, khong phai chan doan nguyen nhan; layout
  wireframe van khong chan doan loi font/color.
- Evidence chay that va gioi han: `docs/tmp/visual-bug-source-linkage/report.html`.
  Khong rollout production; khong rerun full suite co loi token-file da biet.
- Final scoped verification: check.cjs PASS; Electron `passed: true`, 19 checks/
  11 reports; PNG PASS. Tat ca 69 SHA-256 report cu khong doi (37 JSON, 32 PNG).
