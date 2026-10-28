---
title: 'Merge complete visual debug flow into monorepo'
type: 'feature'
ticket: ''
baseline_revision: '212073972fe02f261c1232c124eb07a6ced2acaa'
created: '2026-10-11'
status: 'built'
route: 'full'
route_source: 'auto'
review: 'thorough'
review_source: 'independent-parent'
lenses_ran: ['independent-parent-source-review']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — approved mapping in delegated session">

## Intent

**Problem:** The source branch previously merged only documentation and the common launcher. Its debug hooks and launcher were dirty/untracked, while the working implementation remained ignored scratch code. The monorepo therefore cannot launch the requested reporting flow.

**Approach:** Track the complete implementation and checks in `tools/visual-bug-reporting`, point the Electron hooks there, and make root `run-dev.bat` delegate to `run.bat`. Merge a scoped source commit into `consolidate/monorepo`, demonstrate the actual target BAT and report save, and leave the source branch with no unmerged commits.

## Boundaries & Constraints

**Always:** Preserve the unpackaged-plus-explicit-flag gate and sandbox. Reports remain private/ignored and notes remain verbatim. Historical reports and SQLite/WAL/SHM are archived before cutover without overwrite. Default runtime and reports use ignored `docs/tmp/visual-bug-reporting`. Independent parent review clears merge. Keep arguments and exit codes through the shared launcher.

**Never:** Push, delete the branch/worktree, reset/stash/clean unrelated changes, copy binaries/caches, migrate archival data into incompatible active profiles, rerun the skill renderer, or rerun the known failing full renderer suite.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Debug launcher | Unpackaged app, run-dev.bat | Bridge/picker/IPC enabled; local v2 JSON and wireframe PNG | Visible fixed save/capture failure |
| Normal or packaged app | Flag absent or packaged | No reporting bridge, injection, or IPC | Existing app behavior |
| Worktree launch | Missing local installed dependencies | Shared Git root runtime, current worktree source | Existing run.bat missing-runtime message |
| Ownership mapping | Known fid/class versus unknown identifiers | Known normalized identity and live JS/CSS anchors; default-deny unknown values | Missing anchors stale, never guessed |
| Preservation | Existing source private runtime/reports | Exclusive namespaced archive with SHA256 and byte equality | Abort on collision or source mutation |

</frozen-after-approval>

## Code Map

- `run.bat`: existing Git shared-root dependency resolution and argument propagation; reuse rather than duplicate.
- `run-dev.bat`: untracked hardcoded launcher to replace with a call to the common launcher.
- `shell/src/main/main.js`: existing dirty guarded hook; update implementation path only.
- `shell/src/preload/preload.js`: existing opt-in bridge; retain gate argument contract.
- `docs/tmp/visual-bug-spike/custom/`: verified v2 implementation and checks; relocate maintained sources, not private data.
- `shell/package.json`: explicit package globs exclude root tools; no second product or installer build.
- `docs/specs/shared/visual-bug-spike.md`, `dev-launcher.md`: authoritative behavior and privacy boundaries; update durable paths.
- `code-graphs/README.md`: existing graph snapshots are old child-repo navigation, not authority for these new shell hooks.

## Tasks & Acceptance

**Execution:**
- Preserve user artifacts and source private runtime in approved ignored target archive, with manifest and Vietnamese HTML readiness inventory.
- Track core implementation, portable check/e2e/image/regression scripts and documentation under `tools/visual-bug-reporting`; isolate all generated evidence and profiles outside source code.
- Update hooks, BAT/PowerShell launchers, relevant specs and README consumers.
- Run scoped unit/anchor/privacy checks and current Electron e2e, then parent independently reviews the patch.
- Commit only cutover files, merge only after clearance, exercise target BAT with fresh profile/sink and a real Notary control, and record exact commit relationship.
- Remove only superseded scratch executables after proof and archive; keep historical reports/runtime and unrelated artifacts.

**Acceptance Criteria:**
- Given target monorepo, when actual run-dev.bat is launched, then Ctrl+Shift+B selects a real Notary control and saves v2 note/owner/CSS JSON and PNG under target ignored storage.
- Given normal run.bat or packaged policy, when reporting is not authorized, then reporting stays absent.
- Given source branch after merge, when exact target..source commits are counted, then ahead is zero and tracked source changes are clean.
- Given source deletion planning, when the HTML inventory is opened, then preserved versus excluded files and unrelated artifacts are explicit, without claiming private data migrated into active app storage.

## Implementation Notes

- Approved archive completed: 555 files, 3,142,230 bytes (531 ignored candidates plus 24 untracked evaluation/render artifacts). Exact bytes and SHA256 match; source stable across copy. Original files unchanged. Existing target normal app uses external AppData profile; no source spike writer observed.

## Plan Change Log

## Review Triage Log

- Independent parent approved portable hook/launcher/storage design, source code and scoped commit+merge on 2026-10-11. Named model-lens subagents unavailable; no claim they ran.
- Patch: Windows cmd quoting needs `windowsVerbatimArguments`; source BAT smoke initially failed before window, corrected.
- Patch: harness draft cleanup must not block native close. Real UI discard plus existing renderer dirty-state bridge clears only harness draft; final source normal/debug BAT exit codes both zero, no forced kill on success.
- Source verification: focused checks PASS, Electron 19/19 checks with 11 reports PASS, native PNG PASS; actual source BAT smoke `launcher-1791730173794/result.json` PASS four checks.
- Original ten source/doc files match their archive bytes before retiring nine obsolete executables. Historical 69 JSON/PNG hashes unchanged after verification. Old README marked archival; reports/runtime left in place.
- Target BAT evidence and canonical merge/ahead/clean relation are recorded in ignored `docs/tmp/debug-monorepo-cutover.html`, not mixed into source private reports.

## Verification

- `node tools/visual-bug-reporting/check.cjs`: policy, packaging gate, live and stale anchors, structural scope and privacy.
- `node tools/visual-bug-reporting/e2e.cjs`: scoped current Electron checks in fresh private test directory.
- `python tools/visual-bug-reporting/check_image.py`: actual wireframe PNG privacy.
- Actual target `cmd /c run-dev.bat` with fresh runtime/sink and remote debugging: keyboard, real Notary control, note, persisted owner/CSS and image.
- Exact `git rev-list --count consolidate/monorepo..spike/visual-bug-reporting`: zero after merge.
