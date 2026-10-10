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
  `reports/`; the E2E harness points it at `smoke-reports/` so test records never mix
  with reporter records. Packaged behavior is unit-tested, not certified through a
  new installer build.
