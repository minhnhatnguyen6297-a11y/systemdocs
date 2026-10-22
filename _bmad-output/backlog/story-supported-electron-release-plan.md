---
title: 'Move the desktop shell to a supported Electron release'
type: 'chore'
ticket: '17'
created: '2026-10-16'
status: 'built'
baseline_revision: '5025d2f0f090164b1f66a30b758c847d5c5f1eed'
route: 'full'
route_source: 'pinned'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - _bmad-output/backlog/story-supported-electron-release.md
  - shell/README.md
  - _bmad-output/specs/product-overview.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The shell declares Electron `^31.0.2` and locks `31.7.7`; this is below the current official stable `44.7.2`. A desktop-runtime failure can block startup, IPC, local file selection, or the Python sidecar and can cross user-data boundaries.

**Approach:** Move only the Electron range, its exact npm `allowScripts` key, and lock to `44.7.2`; keep `electron-builder` at `24.13.3` unless an actual package failure proves it incompatible. Prove the production and test packages on this Windows x64 host, including real sidecar work and a real native file picker.

## Boundaries & Constraints

**Always:** Keep the production/test package boundary, real IPC and sidecar contract, and all writes within the isolated packaged `userData`; test with synthetic files and retain actual failure traces. Use the official stable release and Windows 10+ x64 support evidence. Preserve the existing npm install-script allowlist for the exact Electron artifact.

**Never:** Do not upgrade builder without a reproduced incompatibility; no blanket audit/fix, source pins, new test hooks, security/API migrations, debug/token bypasses, or unrelated code changes. Do not modify user-owned `.agent/` or `docs/`; do not claim the deferred Upload `file_token` mismatch is fixed.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Install | Clean `shell` install from lock | Electron resolves to supported `44.7.2`; allowScripts key matches; builder stays `24.13.3` | Keep install log and diagnose only the concrete install failure |
| Production package | Production sidecar/assets, isolated `userData` | Packaged runtime starts; existing smoke reaches ready sidecar and a successful `file.inspect`; install tree is unchanged | Capture exit, logs, and artifact state; no test-package fallback |
| Test package | Existing test package and fixture portal | Packaged Upload suite and bundled Chromium loopback probe pass | Preserve full E2E trace; do not mask a deferred `file_token` mismatch |
| Native picker | Synthetic workbook; production app with no picker seam | Actual Win32 open dialog returns the selected path through the real IPC flow | Record picker and downstream result separately; never bypass tokens or claim an existing mismatch fixed |

</frozen-after-approval>

## Code Map

- `shell/package.json` and `shell/package-lock.json` — Electron range, allowScripts, builder, and package scripts; keep changes limited to Electron resolution.
- `shell/sidecar/build_sidecar.ps1` and `shell/test/build-upload-test.ps1` — production/test sidecar and resource staging consumed by the two directory packages.
- `shell/src/main/main.js` — existing packaged smoke, picker IPC, and test-seam package guard.
- `shell/test/test_upload_e2e.py` — production offline install-write check and test-package Upload/Chromium flow; no source/test changes unless an actual runtime regression requires one.
- `tools/visual-bug-reporting/check.cjs` — existing dev-only debug-reporting boundary check.
- `_bmad-output/backlog/story-supported-electron-release.md` — authoritative #17 acceptance; do not narrow it.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/specs/shell/electron-runtime-support.md` — record target release, Windows support, package/runtime contract, and verification matrix before package changes.
- [x] `shell/package.json` — change only Electron to `^44.7.2` and its exact `allowScripts` key; leave builder unchanged absent a proven break.
- [x] `shell/package-lock.json` — update the minimal lock entries produced by the package manager; no unrelated dependency churn.
- [x] `shell/README.md`, `_bmad-output/backlog/README.md`, and the spec — record tested runtime/build versions, outcomes, and observed limits without claiming an unrelated Upload fix.
- [x] Existing verification: shell Node tests, Notary/adapter tests, debug-boundary check, package builds/E2E, packaged Notary-module and native-picker checks. Failures and incomplete acceptance are recorded below.

**Acceptance Criteria:**
- Given the official stable registry and Windows compatibility evidence, when the package manifest and lock are updated, then the declared range supports the chosen release, lock resolves `44.7.2`, the allowlist matches that exact artifact, and builder remains `24.13.3` unless a reproduced packaging break requires otherwise.
- Given production sidecar and resources are built, when the production directory package launches with isolated `userData`, then the running app reports Electron `44.7.2`, the real sidecar reaches ready and completes the existing smoke file inspection, and no package-install directory write occurs.
- Given the production package is open, when the user selects Notary, then its renderer module loads and its initial request receives a response from the real sidecar; no test provider or mock path is active.
- Given the test package is built, when its existing `--case all` flow runs, then Upload fixture workflows and the packaged Playwright Chromium loopback launch pass without runtime browser download; production contains no test portal/debug seam.
- Given a synthetic workbook and the production package, when the user invokes file selection, then an actual Windows native dialog opens and the chosen path reaches the existing real IPC/picker flow without `G1_E2E_PICK_FILES`; any downstream `file_token` mismatch is reported with its real trace and is not bypassed or represented as fixed.
- Given the upgrade is complete, when the existing shell, Notary, and debug-boundary checks run, then their outcomes and the exact tested Electron/builder/OS versions and limitations are recorded in the spec, shell README, and backlog.

## Implementation Notes

- Package/build: Electron `^44.7.2`, matching exact `allowScripts` key, lock `44.7.2`; builder unchanged at `^24.13.3` / `24.13.3`. `npm ci`, sidecar build, `dist`, and `dist:test` succeeded.
- Regression: `npm test` 408 passed; Notary 1115 passed/2 skipped; adapters 239 passed/2 skipped; debug-boundary check 6/6.
- Packaged production: UA reported Electron `44.7.2` / Chromium `152.0.7977.149`; `G1_SMOKE` completed real sidecar `file.inspect`; Notary initial requests succeeded.
- Separate packaged test `diag.fixture_browser_launch` succeeded headless at `http://127.0.0.1:56442` using bundled Chromium.

- Environment: Python-dependent commands required process-local PATH to `notary_v2/venv/Scripts` because default `python` lacked `jsonschema`/`playwright`; no global environment change.

- Remaining acceptance limits:
  - Production `--case offline` failed at `upload.scan` with `file phai chon qua hop thoai — file_token het han/khong hop le hoac path tho bi tu choi`; its own final snapshot comparison did not run. A separate fresh-profile `G1_SMOKE` plus existing `_tree_snapshot` comparison found 2,975 files before/after and zero changed paths, proving only startup/sidecar `file.inspect` immutability, not the full offline Upload path. Evidence: `.tmp/p17-install-snapshot-h5853qut/snapshot-result.json`.
  - Test `--case all` timed out waiting for visible `.ul-audit-head` after `upload.download_export` succeeded, so the run did not reach the packaged diagnostic or later Upload steps. The separate Chromium probe does not make `--case all` pass.
  - The actual production Upload UI picker (seam unset) still triggered `upload.audit_excel` with `validation_error: file_ref.path rong/khong phai chuoi`; no bypass or fix is claimed. Its first UIA child search timed out at 20 seconds; a separate public-API picker probe used a fresh fixture, verified its pre-selection size/hash, selected it through its owned dialog in one PID-scoped 15-second automation, then passed only the returned `file_token` to public `file.inspect`; the succeeded sidecar result matched size and SHA-256. Evidence: `.tmp/p17-picker-api-j29eq2di/picker-api-evidence.json` and `picker-dialog.png`. This proves native picker registration and real file read, not the Upload UI consumer.



## Plan Change Log


## Review Triage Log
- 2026-10-16 — Q1 (low, reject): The all-pass expectation at frozen plan lines 41/68 is additional to canonical #17 AC2; rejected per step04 rule66 because correcting it would edit the approved build plan. Canonical #17 AC2 controls; the `--case all` failure remains explicit and is not claimed as passing.
- 2026-10-16 — Q2 (low, patched): Runtime spec line 27 now requires running and recording the original offline result, while separating the independent startup/IPC snapshot proof from the still-unproven full offline Upload scenario. The failed offline result remains explicit.
- 2026-10-16 — Independent Quick t2 recheck: CLEAN (no findings); Q2 corrected. Q1 low remains rejected per step04 rule66; frozen text is unchanged.
- 2026-10-16 — Cleanup complete: owned `p17-plan-preview` and `exhibit-server` services are exited; no active probe app/process or executable helper script remained. Shared `omp.browser.headless` was left untouched. JSON/log/screenshots/HTML plans retained.
