# Temporary Electron visual reporting spike

Source: implementation-artifacts/plan-visual-bug-electron-evaluation.md.

- Enabled only by `G1_VISUAL_BUG_SPIKE=1` in unpackaged Electron. Main loads
  scratch implementation outside package globs; absent flag loads nothing.
- Main fixes profile, Notary, Upload and output directories inside
  `_bmad-output/tmp/visual-bug-spike/custom/runtime/`; synthetic mock Notary only.
- Ctrl+Shift+B starts element picking; pointer highlights; click selects without
  activating the app action; Escape/cancel exits; submit writes local JSON/PNG.
- Export the reporter's verbatim note (<=240 chars), structural tag/nth-child
  selector, rectangle, allowlisted module/tab/engine flags, source candidates and
  confidence, console severity/source line only, and main lifecycle event names.
  No DOM text, attribute values, storage, state objects, log bodies, paths to
  documents, or console message bodies.
- Schema v2 adds control identity and ownership linkage: the picker also sends
  the nearest `data-fid`, the picked element's own class tokens, its module
  root class (`cd-root`/`upload-lab`), nearest-table tokens and a `th`/`td`
  structural-cell flag — no input values, text or labels are read.
  Only matched registry identities are persisted; row ids are normalized to
  `{row}`/`{tabId}` and unknown fid/id/class values are omitted by default.
  `linkage.cjs` resolves identity against an explicit registry of
  known notary/upload controls (asset vs person address, case meta, stage
  tables, upload tabs, rail logo) and emits `source.control`,
  `source.owners` (component JS symbols + relevant base CSS selectors, lines
  located by live anchored scan; `stale:true` when an anchor disappears —
  never a pinned or guessed line) and a confidence ladder:
  `explicit-control-map` > `component-ancestry` > `module-ancestry` >
  `heuristic-static-id` > `unmapped`. Known own tokens/fids have `scope: exact`.
  A structural `th`/`td` hit may explicitly map its nearest stage table with
  `scope: ancestor-table`; it is not the picked node's own class identity.
  An unknown interactive control within that table gets only
  `component-ancestry`, `container` context and `scope: ancestor-table`,
  never an exact control id. Outside the registry, module fallback is context.
  Owners state rendering ownership/context, not a causal fix location;
  `source.candidates` remain the unchanged ancestor-context tier.
- Privacy-first prototype: native screenshot of an opaque wireframe drawn over
  the actual window. Original text, images, backgrounds and controls are hidden.
  This sacrifices typography/color fidelity and cannot diagnose those bugs.
- Short notes (<=240 chars) capture the reporter's own words verbatim and are the
  one intentionally raw field: user-authored, never scraped, not anonymized. The
  picker requires a non-empty note before saving. Reports stay local and
  git-ignored; sanitize the note before any publication.
- Structural selectors replay only against unchanged DOM. Static source search
  yields candidate lines, never exact ownership; unknown identifiers are omitted.
- Main validates sender window/frame, exact local URL, payload size/schema and
  selector grammar. One report at a time. Fixed sink; no renderer path input.
- Capture failure produces JSON with missing image and safe failure code. Save
  failure is visible. Reload resets picker. No production delivery or telemetry.
- Runtime failure switches and the report sink (`G1_VISUAL_SPIKE_SINK`, harness-only)
  are trusted environment variables; packaged gate stays off. The sink defaults to
  `reports/`; the E2E harness points it at
  `_bmad-output/tmp/visual-bug-source-linkage/smoke-reports/` so test records
  never mix with reporter records. Packaged behavior is unit-tested, not
  certified through a new installer build.
- Verification evidence: `_bmad-output/tmp/visual-bug-source-linkage/report.html`
  and the current spike `custom/evidence/e2e-results.json` / `image-check.json`.
  This remains a local development spike, not a production rollout.
- Final scoped verification: `check.cjs` PASS; Electron smoke `passed: true`
  (19 checks, 11 reports); current native PNG PASS. All 69 historical report
  hashes unchanged (37 JSON, 32 PNG); separate smoke sink only.
