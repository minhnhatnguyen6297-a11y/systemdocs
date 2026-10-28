---
title: 'Visual bug spike: capture the reporter comment end-to-end'
type: 'bugfix'
ticket: ''
created: '2026-10-10'
status: 'built'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'inventory-worker'
lenses_ran: ['quick']
review_loop_iteration: 1
context: []
baseline_revision: '3975c73910c18a073f9ec99b0800a89df77097e3'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Saved visual-bug reports carry the picked location but lose the reporter's comment. `custom/policy.cjs` replaces any note that is not exactly one of three hardcoded synthetic sentences with `[note omitted: synthetic vocabulary only]`, and the picker only offers those three sentences. 19 of 37 saved reports have an omitted note, so a debugging agent cannot tell what the reporter saw. Historical reports cannot be repaired and must not be edited.

**Approach:** Capture the reporter's own freeform note verbatim and persist it in the local report JSON so the debugging agent reads it. The note is the single intentionally raw field (user-authored, never scraped); DOM text, attribute values, storage, state, log bodies and paths stay omitted. The picker requires a non-empty note before saving and no longer prefills or restricts the text. Reports remain local and git-ignored; publishing requires sanitizing the note. This is a separate fix; the frozen `plan-visual-bug-electron-evaluation.md` intent is preserved.

</frozen-after-approval>

## Implementation Notes

- Route oneshot: ~25 changed lines across `policy.cjs` / `picker.js` / `main.cjs`, plus test and doc updates.
- Fix is spec-first: `docs/specs/shared/visual-bug-spike.md` updated before code, decision recorded in `docs/decisions/decision-76`.
- Note length cap kept at 240 (matches picker `maxLength`); oversize still rejected as `invalid_payload`.
- Old `reports/*.json` with omitted notes are left untouched (historical, not fabricated).
- Files changed (all under the git-ignored spike dir unless noted): `custom/policy.cjs`, `custom/picker.js`, `custom/main.cjs`, `custom/check.cjs`, `custom/e2e.cjs`, `custom/README.md`; spec `docs/specs/shared/visual-bug-spike.md`; decision `docs/decisions/decision-76 ...md`; this plan.
- Empty note is now refused in the picker and rejected by `validate` (`note.length === 0`), so a saved report always carries a comment.
- Harness sink: `main.cjs` now honours a trusted, harness-only `G1_VISUAL_SPIKE_SINK` (default `reports/`); `e2e.cjs` points it at `smoke-reports/` and `check_image.py` derives the screenshot dir from the recorded report path, so smoke runs never add records to the reporter `reports/` directory. Reporter reports are byte-for-byte untouched (37 JSONs, sha256 roll-up `962ba5e6...`); the 4 records from the first smoke run were moved to `smoke-reports/`.
- Smoke evidence labels (explicit, not "fully green"): changed paths pass — `check.cjs` 2/2, `e2e.cjs` 12/12, `check_image.py` PASS after the sink-path fix (passing output archived at `docs/tmp/visual-bug-comment-capture/check-image-pass.txt`); the repo test suite still has its 1 pre-existing failure (`shell-chrome.test.mjs`, missing `docs/spec/ui/tokens.json`), unchanged by this fix. `final-smoke.txt` shows `rc=1` for the pre-fix check_image run and `rc=0` for regression — the latter is a shell-pipeline artifact (`| tail` masked node's real exit code), not a suite pass; `regression.cjs` itself propagates the child's exit status (`process.exitCode = result.status`), so no wrapper change was warranted.
- Review: the independent quick lens is run by the inventory worker via the parent, reading this plan, the refreshed diff `C:/Users/MINH/AppData/Local/Temp/visual-bug-comment-capture-latest.diff` (supersedes `-1791649375.diff`; includes the sink/isolation and `check_image.py` changes) and `review-prompt-visual-bug-comment-capture.md`. Status stays `in-review` until findings are resolved, then moves to `built`.
- The coordinator's existing `plan-visual-bug-electron-evaluation.md` is preserved untouched; the shell hooks (`shell/src/main/main.js`, `shell/src/preload/preload.js`) are the user's prior change and are not part of this fix.

## Plan Change Log

- 2026-10-10: post-review fix — removed hardcoded `synthetic: true` from report objects (`main.cjs`), per Review Triage F1. No schema consumers read the field; no other changes.

## Review Triage Log

- F1 (substantive, ACCEPTED): `main.cjs:77` hardcoded `synthetic: true` on every report contradicts decision-76 (note is the reporter's own raw text) and misleads report consumers about provenance. Spec mandates no such field and no consumer reads it (`e2e.cjs`/`check_image.py` assert nothing about it). Fixed minimally: constant removed; no provenance feature built. Harness evidence `evidence/e2e-results.json` keeps its own accurate `synthetic: true`. Historical reports untouched.
- F2 (substantive, REJECTED): `check_image.py` indexes `results['reports'][1]` positionally. The e2e harness is sequential and deterministic; the current `[1]` entry is the 240-char report with a saved PNG (check passes). If the index ever resolved to a `capture_failed` entry, `Image.open` throws — a loud failure, never silent mis-validation. Validating only harness exports is the checker's designed scope; expanding coverage to `reports/` is unrequested scope.
- F3 (minor, REJECTED): strict palette/magic-pixel assertions are pre-existing checker strictness; they pass today and the 100%-display-scale limit is already documented in the spec. Deriving palette from fixture rects is speculative hardening.
- F4 (minor, REJECTED — finding is false): `#vb-note` is created with `maxLength = 240`, so the browser cannot hold or submit a >240-char value from the picker; the `invalid_payload` length path is unreachable from the UI and exists only as IPC defense-in-depth (`check.cjs` proves 241 rejected at the boundary). On any save failure the panel stays open and `note.value` is never cleared (picker.js save handler), so the text is preserved. The 240-char e2e check proves byte-identical save with no truncation.
- F5 (minor, REJECTED): console noise (`unmapped:11`, `relationship-diagram.js:312`) originates in the demo fixture app itself, predates this fix, and is expected dev-spike behavior; filtering or labelling console entries is an unrequested change outside this bug.
- F6 (process, CLOSED): the masked regression exit code came from the collection pipeline's `| tail`, was already documented in Implementation Notes; `regression.cjs:13` propagates the child exit status correctly. No code change.
- F7 (verified-good): reviewer confirmed note preservation, sender/frame/URL validation, 8192-byte cap, selector and sourceIds caps all intact — matches this plan's verification results.

## Verification

**Commands:**
- `node tools/visual-bug-reporting/check.cjs` -- expected: policy, note boundaries, sender/frame/URL, packaging, registry and anchors PASS.
- `node tools/visual-bug-reporting/e2e.cjs` -- expected: verbatim note and privacy checks PASS in the separate ignored test sink.
- `node tools/visual-bug-reporting/regression.cjs` -- optional broad suite; known pre-existing missing-token failure, not rerun for the cutover.
- `python tools/visual-bug-reporting/check_image.py` -- use the launcher's Python venv (Pillow installed); expected: wireframe pixel check PASS.
