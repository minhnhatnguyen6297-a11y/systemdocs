# Visual bug reporting — local development

Run `run-dev.bat` at the repository root (or `tools/visual-bug-reporting/run.ps1`). It delegates to `run.bat`, so it uses the current checkout's shell and resolves installed Electron/Python locally first, then from the shared Git root. No absolute workstation path or `rtk` is required. This is the same app, not a separate developer product.

Ctrl+Shift+B → click a control → enter a short note (1–240 characters) → Save report. Escape/Cancel leaves picking mode. After save, the picker re-arms and shows a toast. The note is stored verbatim: sanitize it before publishing.

Default private storage is outside maintained code:

- `docs/tmp/visual-bug-reporting/reports/`: schema-v2 JSON and native wireframe PNG.
- `docs/tmp/visual-bug-reporting/runtime/`: isolated synthetic Notary, Upload, output and Electron profile.
- `docs/tmp/visual-bug-reporting/checks/`: test profiles, reports and evidence.

These directories are Git-ignored. `G1_VISUAL_SPIKE_RUNTIME` and `G1_VISUAL_SPIKE_SINK` override runtime/report roots for trusted local tests; `G1_VISUAL_SPIKE_TEST_DIR` selects a separate test evidence root. Historical source profiles/reports are archival backups, not automatically imported into active app storage. The current prototype uses synthetic Notary data and wireframe screenshots; it cannot diagnose typography/color fidelity.

The main hook loads these tools only when `!app.isPackaged` and `G1_VISUAL_BUG_SPIKE=1`. Normal `run.bat` does not enable the flag. Package globs do not include root tools. Sandbox/context isolation remain enabled.

## Scoped checks

From the repository root:

```powershell
node tools/visual-bug-reporting/check.cjs
node tools/visual-bug-reporting/e2e.cjs
# Use the same Python venv selected by run.bat (Playwright and Pillow required).
notary_v2/venv/Scripts/python.exe tools/visual-bug-reporting/check_image.py
node tools/visual-bug-reporting/launcher-smoke.cjs
```

The test dependency resolver follows the launcher's local/shared-root preference and respects `G1_PYTHON`. Test artifacts never mix with reporter records. `launcher-smoke.cjs` invokes the actual BAT with fresh profiles, checks normal-mode absence and debug-mode real Notary selection/save. Packaging is checked through the real main-entry gate with mocked packaging status, not a newly built installer.

`regression.cjs` is the optional broad shell-suite runner. Do not rerun the known pre-existing missing `docs/spec/ui/tokens.json` failure merely to confirm it.

## Source ownership and privacy

Schema v2 persists only matched registry identities (normalized `{row}`/`{tabId}`); unknown fid/id/class values are omitted. Known own-token/fid picks use `scope: exact`. Structural th/td picks may map an ancestor stage table with `scope: ancestor-table`; unknown interactive nodes inside that table are container context, not exact controls.

Confidence: `explicit-control-map` > `component-ancestry` > `module-ancestry` > `heuristic-static-id` > `unmapped`. JS declarations and CSS anchors are scanned live per save; missing anchors are `stale:true`, never guessed lines. Owners are rendering ownership/context, not causal fix locations. Source candidates remain a separate ancestor-context tier.

Authoritative behavior: `../../docs/specs/shared/visual-bug-spike.md`. Historical source-linkage evidence remains under ignored `docs/tmp/visual-bug-source-linkage/` in the source archive; it is not current cutover verification.
