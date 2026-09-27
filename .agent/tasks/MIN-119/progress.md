# Progress — MIN-119

## Trạng thái: xong code + verify CDP — 2026-09-27

- [x] Node `draggable` khi có personId + canWrite
      (`relationship-diagram.js` `diagramNodeEl`, payload
      `{kind:'person', row_id}` giong pool card)
- [x] Drop node→node: move/swap qua `model.movePerson` (drop handler
      node doi tu `assignPerson` sang `movePerson`)
- [x] Pool drop target: `.cd-pool .cd-card-body` nhan drop →
      `movePerson(row_id, null)` = unassign
- [x] Verify CDP headless + regression pool rong person

## Verify — `.agent/scratch/cdp_min119.mjs` (9/9 PASS)

Electron dev + `G1_DEV_NOTARY_MOCK=1`, CDP qua WebSocket noi bo node
(khong can playwright). Mo case #47 (6/7 node da gan — kich ban "pool
het nguoi" cua issue):

- node da gan: draggable=6/6
- node→node: owner ↔ spouse swap dung
- node→Pool: spouse trong, nguoi quay lai Pool
- Pool→node: gan lai duoc
- "Gán vị trí…" (keyboard) con nguyen

Nguon nen `movePerson` (swap/unassign/duplicate-guard) thuoc MIN-122.
