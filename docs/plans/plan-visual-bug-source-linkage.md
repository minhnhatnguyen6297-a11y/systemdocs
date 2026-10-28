---
title: 'Visual bug spike: map actual notary/upload controls to owner JS and relevant CSS'
type: 'bugfix'
ticket: ''
created: '2026-10-11'
status: 'built'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'inventory-worker'
lenses_ran: ['independent-source-linkage-verification']
review_loop_iteration: 3
context: []
baseline_revision: '20c3d597a5335f8fcb9a7bed381f3d70472d4acd'
---

Historical plan and verification below retain the original scratch paths as evidence.
The maintained implementation and current commands moved to
`tools/visual-bug-reporting/`; see [cutover plan](./plan-debug-monorepo-cutover.md).
Do not execute retired scratch paths.

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Saved visual-bug reports identify the picked element only through shell ancestor ids, so all 12 real notary targets receive the same 6 generic shell lines (even an upload line), no notary/upload component JS, no CSS, and upload tab ids are a silent miss. A debugging agent cannot tell which component owns the control or which stylesheet styles it.

**Approach:** At save time, capture stable control identity from the picked element (nearest `data-fid`, own class list, module-root class) with row identifiers normalized to `{row}` placeholders in main before persisting. Resolve identity against one small explicit registry of known notary/upload controls (asset vs person address, case meta fields, stage tables, upload tabs/module root, rail logo) and emit `source.owners` (component JS + relevant CSS) by locating registry anchors in the actual files at save time. Keep the existing `source.candidates` unchanged as an honest separate ancestor-context tier with a confidence ladder (`explicit-control-map` > `module-ancestry` > `heuristic-static-id` > `unmapped`); owners state rendering ownership, never a causal fix location. Historical 37 JSON + 32 PNG stay byte-for-byte.

</frozen-after-approval>

## Code Map

- `docs/tmp/visual-bug-spike/custom/main.cjs` — save handler; add `linkage.cjs` require, `resolveOwnership` call, `source.owners`+`source.confidence`+`source.control` into report; normalize ids before persist.
- `docs/tmp/visual-bug-spike/custom/linkage.cjs` — NEW: `IDENTITY` registry (fid patterns/class tokens → component anchors), `resolveOwnership(identity, readSources)` returns `{control, confidence, owners}`; anchors are symbols/selectors, lines found by live bounded scan.
- `docs/tmp/visual-bug-spike/custom/picker.js` — extend payload: nearest `data-fid` (≤100 chars), own className tokens (first 20, ≤40 chars each), module-root class (`.cd-root`/`.upload-lab`/none) read without values.
- `docs/tmp/visual-bug-spike/custom/policy.cjs` — validate new optional fields; keep 8192-byte cap and existing checks.
- `docs/tmp/visual-bug-spike/custom/e2e.cjs` — new targets: notary asset address input, person address input, stage table, upload tab; assert owners present/distinct + privacy sentinels + unmapped fallback; SINK `docs/tmp/visual-bug-source-linkage/smoke-reports/`.
- `docs/tmp/visual-bug-spike/custom/check.cjs` — assert `resolveOwnership` distinguishes `a:*:dia_chi` vs `p:*:dia_chi` vs unknown, normalization `{row}`.
- `docs/tmp/visual-bug-spike/custom/README.md`, `docs/specs/shared/visual-bug-spike.md`, `docs/decisions/decision-77...md` — spec-first update, decision record.
- Renderer SOT (read-only): `shell/src/renderer/notary/case-drafting-view.js` (`assetTableEl` :1105 dia_chi :1218-1230, `peopleTableEl` :1375 dia_chi :1464-1470, `fillTopActions` :525 `top:case_type` :542, `caseMetaEl` :1543 `meta:*` :1559-1632), `shell/src/renderer/upload/index.js` (`buildView` :71 `upload-lab`, :83-88 `ul-tab-*`), `renderer.js` (`buildNotaryView` :584 `cd-root-outer` :611, `buildUploadView` :560), `index.html` (:14-21 shell), CSS `case-drafting.css` `.cd-root .cd-stage-tbl .cd-cell` :271, `.cd-root .cd-address-suggestion` :950, `.cd-root .cd-lookup-row` :954, `:224` `.cd-root table.cd-stage-tbl`; `upload.css` `:18 .upload-lab`, `:36 .ul-tablist`, `:41 .ul-tab`, `:47 [aria-selected]`; `styles.css` :129 `.rail-logo`.
- Previous evidence: `docs/tmp/visual-bug-code-linkage.html`, `docs/tmp/visual-bug-linkage-evidence.json`, `docs/tmp/visual-bug-source-linkage/matrix.json`.

## Verification

**Commands:**
- `rtk proxy node docs/tmp/visual-bug-spike/custom/check.cjs` — expected: PASS lines incl. a/p dia_chi distinct owners, normalization, unknown→module-ancestry.
- `rtk proxy node docs/tmp/visual-bug-spike/custom/e2e.cjs` — expected: all groups pass; asset vs person address and upload tab report distinct `source.owners` JS/CSS with correct confidence; rail-logo unchanged tier; sentinel `unmapped`; no `PRIVATE_`/raw row ids in JSON; 37 reporter JSONs byte-identical (sha256 roll-up before/after).
- `rtk proxy D:/systemdocs/notary_v2/venv/Scripts/python.exe docs/tmp/visual-bug-spike/custom/check_image.py` — expected: PASS (index [1] must remain a saved-PNG report).

## Implementation Notes

- Oneshot route: single-goal change concentrated in the spike directory (~120 lines), reusing the existing policy/picker/report skeleton; no production renderer code is modified.
- Registry design locked per source-verification feedback: control resolution keyed on fid pattern OR own-id pattern OR class token (any hit → `explicit-control-map`); `ul-tab-{tabId}` resolves via id-pattern branch; address-suggestion CSS owners derive from fid branch only (suggestion div is a sibling, not ancestor); CSS owner search uses class selectors only (`.rail-logo`, `.ul-tab` — no `#ul-tab-*`/`#rail-logo`); `cd-stage-tbl` maps to both assetTableEl+peopleTableEl; base CSS rule per role only (`.cd-address-suggestion` :950, `.cd-cell` :271 — no variant rules); `aria-describedby` never read.
- Final scope rule: known own-token/fid/id matches have `scope: exact`; a real `th`/`td` hit maps its nearest stage table with `scope: ancestor-table`. Unknown interactive controls inside that table have only `component-ancestry` + `container`, never an exact control id. Unknown persisted identity facets are omitted by default.
- Picker declares bounded `tableTokens`; policy validates/forwards `cellLike`; main forwards both and uses a per-save source-line cache. T3 uses a real TH hit, not an unattainable table-centre assumption.
- Verification harness now checks every emitted owner against the actual declaration/selector at its reported line, T3 structural scope, unknown interactive table downgrade/privacy, and a real Upload root hit in addition to T1/T2/T4/T5/T6.

## Review Triage Log

- High, patched: unknown fid/own-id/class facets could leak row identifiers; only matched normalized registry facets now persist.
- High, patched: bare-symbol fallback matched Upload comments and masked missing declarations; exact declaration anchors now resolve `NS.buildView` and report stale when removed.
- High, patched: nonexistent `buildRail` owner; rail markup and `setStatus` are the actual owners.
- High, patched: missing `tableTokens` declaration and dropped `cellLike` broke the real picker-to-main path; current wiring forwards both.
- Medium, patched: ancestor table token could falsely label unknown interactive controls as exact; component-ancestry/container scope now separates that context.
- High, patched during finalization: residual e2e `tSyms` was undefined; derive it from the saved T3 report before asserting both table builders.
- High, patched during actual smoke: re-armed picker intercepted business navigation to Upload; Escape now exits picking before navigation. Native dirty-draft close guard hung harness failure teardown; teardown destroys only the harness-owned synthetic windows. Page waits are bounded to 30 seconds with PASS stage diagnostics.
- Harness-only, patched: actual dirty-module transition requires the visible `Rời màn hình` confirmation; Upload has two real tabs, so T4 uses unique `#ul-tab-audit` instead of an ambiguous class locator. Real business controls remain the smoke targets.


## Verification Evidence

- `node docs/tmp/visual-bug-spike/custom/check.cjs`: PASS (policy, registry/privacy, live source anchors, packaged gate via mocked main-entry).
- Actual Electron 31.7.7 smoke: final `e2e-results.json` has `passed: true`, 19 checks and 11 reports in a separate `visual-bug-source-linkage/smoke-reports` sink. Covers T1 asset, T2 person, T3 real TH plus unknown interactive table context, T4 actual Upload tab/root, T5 rail, T6 unknown/privacy and failure paths. Final run completed in 7.90 seconds.
- `python docs/tmp/visual-bug-spike/custom/check_image.py`: PASS on the current native PNG; wireframe-only pixels and white private fixture.
- Bounded in-memory live probes: unknown fid/id/class omitted; Upload JS declaration line 55, exact base CSS line 18, rail markup line 16 and `setStatus` line 67; commented/removed Upload declaration stays stale.
- Original reports unchanged: all 69 per-file SHA-256 values match (37 JSON, 32 PNG). Original `sha256sum *.json | sha256sum` rollup remains `55dbcbd278e8b9ec2d2df8c0c382faccc98282196a7ae0fce4ee9fde126da4ed`.
- Vietnamese final evidence: `docs/tmp/visual-bug-source-linkage/report.html`; final review summary: `review-findings.json`. Worker-created three probe-draft scripts removed; no production rollout or full-suite rerun.
