# Supported Electron runtime

## Decision

For story #17, use Electron `^44.7.2`; the lockfile must resolve `44.7.2`.
The npm `allowScripts` entry must name `electron@44.7.2`.
This was the latest stable in the Electron registry and npm `latest` metadata on 2026-10-16.
The official release reports Chromium `152.0.7977.149` and Node `24.21.0`.

The official v44.7.2 README states Windows 10 and newer are supported and lists
Windows x64/amd64 and arm64 binaries.
Target: Windows x64. Host reports `win32`, x64, version `10.0.26200`.
This records the observed host, not a particular Windows 10 product release.

Sources:

- [Electron stable releases](https://releases.electronjs.org/releases/stable)
- [Electron npm latest metadata](https://registry.npmjs.org/electron/latest)
- [Electron v44.7.2 README](https://github.com/electron/electron/blob/v44.7.2/README.md)
- [Electron release timeline](https://www.electronjs.org/docs/latest/tutorial/electron-timelines)

## Compatibility contract

- Keep `electron-builder` at `^24.13.3` / locked `24.13.3` unless the actual Windows package build demonstrates a specific incompatibility. A builder upgrade is not presumed.
- Preserve the existing main/preload/renderer IPC contract, packaged Python sidecar launch, engine resources, bundled Playwright Chromium, and native `dialog.showOpenDialog` path.
- Preserve the production/test package boundary: production must not expose the test portal, file-picker seam, mock adapter, or dev-only debug behavior. Retain the existing `tools/visual-bug-reporting/check.cjs` guard.
- Keep all packaged application data under a fresh isolated `userData`; run and record the existing offline package test. Report its actual outcome, distinguishing any independent startup/IPC snapshot proof from the still-unproven full offline Upload scenario. Use synthetic fixtures only.
- The known deferred Upload `file_token` mismatch is outside this runtime decision. Do not bypass it or describe it as repaired; report an observed failure with its trace.

## Verification contract

Use existing `shell` package commands: `npm ci`, `npm test`, and `npm run build:sidecar`.
Also run `npm run dist` and `npm run dist:test`.
Run production `test_upload_e2e.py --case offline` and test-package `--case all`.
Keep the latter's real packaged Chromium-to-loopback probe.
Run Notary/adapter regressions and `node tools/visual-bug-reporting/check.cjs`.
Use the documented working directories.
In production, open Notary and verify its renderer module loads.
Verify an initial response comes from the real sidecar.
Launch production with an isolated profile and use a synthetic workbook.
Open the actual Windows native picker with `G1_E2E_PICK_FILES` unset.
PowerShell 5.1 provides `UIAutomationClient`/`UIAutomationTypes`, `AutomationElement`,
`ValuePattern`, and `InvokePattern`; control IDs are candidates only.
Inspect only the dialog owned by the app PID; record actual identifiers.
Capture a screenshot and bound dialog automation to 20 seconds.
Capture runtime Electron version, sidecar/result, picker observation, process exit, and actual limits.

## Verification results (2026-10-16)

Verified host: Windows 11 x64, build `10.0.26200`; official Electron v44.7.2 README supports Windows 10+ x64/arm64. The packaged production UA reported `Electron/44.7.2 Chrome/152.0.7977.149`. `electron-builder` remained `24.13.3`.

- `npm ci`; `npm exec -- electron --version` → `v44.7.2`; `npm test` → 408 passed.
- `npm run build:sidecar`, `npm run dist`, and `npm run dist:test` succeeded. Sidecar build used Python 3.12.10 / PyInstaller 6.22.3 and bundled Chromium revision 1243.
- Notary suite from `notary_v2` with `PYTHONPATH=D:\systemdocs`: 1115 passed, 2 skipped, 115 warnings, 2 subtests. Adapter checks: 239 passed, 2 skipped, 32 warnings. `node tools/visual-bug-reporting/check.cjs`: 6 checks passed.
- Production package `G1_SMOKE` reached the packaged sidecar and completed `file.inspect`; packaged Notary `case_list` and `customer_list` requests succeeded. No test/mock seam variables were present in the production launch environment.
- Test package's existing `diag.fixture_browser_launch` probe separately succeeded headless at `http://127.0.0.1:56442` using its bundled Chromium. The full `--case all` run did not reach that step.

### Observed limits

- Production `test_upload_e2e.py --case offline` reached the real packaged sidecar but failed at `upload.scan` with `file phai chon qua hop thoai — file_token het han/khong hop le hoac path tho bi tu choi`; that run stopped before its own final install-tree snapshot comparison.
- A separate fresh-profile production `G1_SMOKE` probe used the existing `_tree_snapshot` helper around the packaged executable: 2,975 files before and after, zero changed paths, exit code 0, smoke `ok`, sidecar `ready`, and `file.inspect` succeeded. This proves install-tree immutability only for that startup/IPC smoke, not the failed offline Upload path. Result: `.tmp/p17-install-snapshot-h5853qut/snapshot-result.json`.
- Test-package `--case all` successfully completed `upload.download_export` but timed out waiting for visible `#ul-panel-audit .ul-audit-head`; the head remained hidden. It did not reach the bundled Chromium probe or later Upload workflow. This observed timeout is not attributed to Electron without baseline comparison.
- Production picker was launched through the app's actual button with `G1_E2E_PICK_FILES` unset. The owned native dialog was HWND `23398458`, PID `15432`, class `#32770`, title `Open`, owner HWND `25429102`.
  Screenshot: `.tmp/p17-native/picker-dialog.png`. The initial 20-second RootElement-child UIA search saw only the app main window and timed out; a targeted foreground HWND/owner-PID check found the dialog. UI Automation exposed no filename/Open controls or candidate IDs `1001`/`1148`/`1`.
  The subsequent SendKeys process had a 15-second outer bound (20-second internal deadline), but dialog-open-to-selection spanned multiple bounded helpers and exceeded one 20-second window. The real `upload.audit_excel` sidecar job failed with `validation_error: file_ref.path rong/khong phai chuoi`; dialog opening is proven, successful file-ref delivery is not.
- Separate production public-API picker probe used a fresh synthetic `synthetic.xlsx` in `.tmp/p17-picker-api-j29eq2di`; before selection it existed with size 4,847 bytes and SHA-256 `46061229d062139e45658b2c0a17314ada99730f0096577523bbddc3439b8981`. The real owned dialog was HWND `23923836`, PID `16668`, class `#32770`, title `Open`, owner HWND `7081066`; one PID-scoped SendKeys action completed within 15 seconds. Public `desktop.v1.pickFiles` returned one registered ref (`file_token` redacted, name `synthetic.xlsx`, size 4,847, `is_dir=false`). Passing only `{file_token}` through `desktop.v1.submitCommand('file.inspect', ...)` produced succeeded job `j_4673aa7e3681`; returned size and SHA-256 matched the pre-selection fixture. No raw path was sent or token persisted. This proves the public picker/registration/real-sidecar read boundary, not the still-failing Upload UI consumer. Sanitized evidence: `.tmp/p17-picker-api-j29eq2di/picker-api-evidence.json`; dialog screenshot: `.tmp/p17-picker-api-j29eq2di/picker-dialog.png`.
- Python-dependent commands used a process-local `notary_v2/venv/Scripts` PATH because the default `python` lacked `jsonschema` and `playwright`; no global environment was modified.

