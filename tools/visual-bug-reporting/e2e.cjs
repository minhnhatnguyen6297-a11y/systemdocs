'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const { repo, python, playwright, electron, testRoot } = require('./test-runtime.cjs');
const { _electron } = require(playwright);
const ROOT = testRoot;
const SINK = path.join(ROOT, 'smoke-reports');
const evidence = path.join(ROOT, 'evidence'); fs.mkdirSync(evidence, { recursive: true });
const results = { synthetic: true, checks: [], reports: [], measurements: [], limitations: [
  'Wireframe exports cannot show typography/colors.', 'Reporter note is freeform local text; sanitize reports before publishing.',
  'Packaged gate tested as policy and mocked app.isPackaged, no installer build.',
  'Startup samples are observations, not benchmark or long-running memory proof.' ] };
function ok(name) { results.checks.push({ name, passed: true }); console.log('PASS: ' + name); }
async function launch(mode, extra = {}) {
  const started = performance.now();
  const profile = path.join(ROOT, 'runtime', mode);
  fs.mkdirSync(profile, { recursive: true });
  const env = { ...process.env, G1_PYTHON: python,
    G1_DEV_NOTARY_MOCK: '1', G1_NOTARY_DATA_DIR: path.join(profile, 'notary'),
    G1_UPLOAD_DATA_DIR: path.join(profile, 'upload'), G1_OUTPUT_DIR: path.join(profile, 'output'),
    G1_NOTARY_V2_ROOT: path.join(repo, 'notary_v2'), G1_UPLOAD_LAB_ROOT: path.join(repo, 'upload_lab'),
    G1_VISUAL_BUG_SPIKE: mode === 'disabled' ? '0' : '1',
    G1_VISUAL_SPIKE_RUNTIME: profile, G1_VISUAL_SPIKE_SINK: SINK, ...extra };
  delete env.ELECTRON_RUN_AS_NODE;
  if (mode === 'disabled') delete env.G1_VISUAL_BUG_SPIKE;
  const app = await _electron.launch({ executablePath: electron,
    args: [path.join(repo, 'shell'), '--user-data-dir=' + profile], env, timeout: 60000 });
  const page = await app.firstWindow();
  page.setDefaultTimeout(30000);
  await page.waitForSelector('.rail-btn.active');
  results.measurements.push({ mode, windowReadyMs: Math.round(performance.now() - started) });
  return { app, page };
}
async function select(page, selector) {
  await page.keyboard.press('Control+Shift+B');
  await page.locator(selector).hover();
  assert(await page.locator('#vb-highlight').isVisible());
  await page.locator(selector).click();
  await page.locator('#vb-panel').waitFor();
}
async function writeNote(page, text) { await page.fill('#vb-note', text); }
async function save(page) {
  await page.click('#vb-save');
  await page.waitForFunction(() => /^(Saved|Save failed)/.test(
    document.querySelector('#vb-toast')?.textContent || document.querySelector('#vb-status')?.textContent || ''));
  const text = await page.evaluate(() =>
    document.querySelector('#vb-toast')?.textContent || document.querySelector('#vb-status')?.textContent || '');
  assert(/^(Saved|Save failed)/.test(text), text);
  return text;
}
async function loadReport(page) {
  const text = await save(page);
  const id = /^Saved ([a-f0-9-]+);/.exec(text)?.[1]; assert(id, text);
  const file = path.join(SINK, id + '.json');
  const report = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.equal(await page.locator(report.selector).count(), 1);
  const bounds = await page.locator(report.selector).boundingBox();
  assert.equal(Math.round(bounds.x), report.rect.x);
  for (const owner of [...report.source.owners.components, ...report.source.owners.styles]) {
    assert.equal(owner.stale, false, JSON.stringify(owner));
    assert(Number.isInteger(owner.line) && owner.line > 0);
    const line = fs.readFileSync(path.join(repo, owner.file), 'utf8').split(/\r?\n/)[owner.line - 1].trim();
    if (owner.selector) assert(line.startsWith(owner.selector), JSON.stringify(owner));
    else if (owner.symbol === 'rail-logo') assert(line.startsWith('<div id="rail-logo"'));
    else if (owner.symbol === 'NS.buildView') assert(line.startsWith('NS.buildView ='));
    else assert(line.startsWith(`function ${owner.symbol}(`), JSON.stringify(owner));
  }
  results.reports.push(path.relative(ROOT, file).replaceAll('\\', '/'));
  results.measurements.push({ report: id, exportMs: report.elapsedMs });
  return report;
}
(async () => {
  let current;
  try {
    current = await launch('disabled');
    assert.equal(await current.page.evaluate(() => typeof window.visualBugSpike), 'undefined');
    await current.page.keyboard.press('Control+Shift+B');
    assert.equal(await current.page.locator('#vb-highlight').count(), 0);
    assert.equal(await current.app.evaluate(({ ipcMain }) => ipcMain._invokeHandlers.has('visual-bug-spike.save')), false);
    ok('flag absent: no bridge, picker, or IPC'); await current.app.close(); current = null;

    current = await launch('enabled');
    const { app, page } = current;
    await page.waitForFunction(() => document.querySelector('#rail-logo')?.dataset.engineState === 'ready', null, { timeout: 60000 });
    results.versions = await app.evaluate(() => process.versions);
    const prefs = await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences());
    assert(prefs.sandbox && prefs.contextIsolation && !prefs.nodeIntegration && prefs.webSecurity);
    ok('real sidecar ready; sandbox/contextIsolation retained');
    await select(page, '#rail-logo');
    await page.keyboard.press('Escape'); assert.equal(await page.locator('#vb-panel').count(), 0);
    await select(page, '#rail-logo'); await page.click('#vb-cancel');
    assert.equal(await page.locator('#vb-panel').count(), 0); ok('keyboard and button cancel');
    await select(page, '#rail-logo');
    await page.click('#vb-save');
    assert.equal(await page.locator('#vb-status').textContent(), 'Enter a short note first.');
    assert.equal(await page.locator('#vb-panel').count(), 1);
    ok('empty note refused before save');
    await page.click('#vb-cancel');
    assert.equal(await page.locator('#vb-panel').count(), 0);

    await select(page, '#rail-logo');
    assert.equal(await page.getAttribute('#vb-note', 'maxlength'), '240');
    const longNote = 'Ghi chu dai '.repeat(20).slice(0, 240);
    await writeNote(page, longNote);
    const longReport = await loadReport(page);
    assert.equal(longReport.note, longNote); assert.equal(longReport.note.length, 240);
    ok('240-char note saved byte-identical, no silent truncation');

    await select(page, '#rail-logo');
    await writeNote(page, 'Logo rail overlaps the status bar.');
    await page.screenshot({ path: path.join(evidence, 'synthetic-picker-ui.png') });
    const first = await loadReport(page); assert.equal(first.screenshot.status, 'saved');
    assert.equal(first.note, 'Logo rail overlaps the status bar.');
    assert(first.source.candidates.length > 0); ok('note captured verbatim, native capture, source candidates and selector replay');
    assert.equal(await page.locator('#vb-panel').count(), 0);
    assert(await page.locator('#vb-toast').isVisible());
    await page.locator('#rail-logo').hover();
    assert(await page.locator('#vb-highlight').isVisible());
    await page.locator('#rail-logo').click();
    await page.locator('#vb-panel').waitFor();
    await page.click('#vb-cancel');
    assert.equal(await page.locator('#vb-panel').count(), 0);
    ok('save closes ticket and picker re-arms for next item without hotkey');

    // Synthetic defect and privacy sentinels. No real records or accounts.
    await page.evaluate(() => {
      const fixture = document.createElement('div'); fixture.id = 'private-person-sentinel';
      Object.assign(fixture.style, { position: 'fixed', left: '180px', top: '180px', width: '300px', height: '160px', background: '#ff00ff' });
      fixture.textContent = 'PRIVATE_PERSON_987';
      const input = document.createElement('input'); input.value = 'PRIVATE_PASSWORD_987'; fixture.append(input);
      const button = document.createElement('button'); button.textContent = 'PRIVATE_BUTTON_987';
      Object.assign(button.style, { position: 'absolute', left: '0', top: '0', width: '140px', height: '35px' });
      fixture.append(button); document.body.append(fixture);
      window.privateState = { name: 'PRIVATE_STATE_987' };
      localStorage.setItem('private', 'PRIVATE_STORAGE_987');
      console.error('PRIVATE_LOG_987');
    });
    await select(page, '#private-person-sentinel > button');
    await writeNote(page, 'Save button is cut off at 1024px.');
    const second = await loadReport(page); assert.equal(second.source.confidence, 'unmapped');
    assert.equal(second.note, 'Save button is cut off at 1024px.');
    assert(!JSON.stringify(second).includes('PRIVATE_')); assert(!JSON.stringify(second).includes('private-person'));
    assert(second.console.some(e => e.severity === 'error')); ok('note captured; DOM/state/storage/log/ID privacy; unmapped fallback');
    assert.equal(second.source.control.classes.length, 0, 'unknown classes must be omitted');
    assert.equal(second.source.control.id, null, 'unknown ids must be omitted');
    assert.equal(await page.locator('#vb-panel').count(), 0);
    await page.reload(); await page.waitForFunction(() => window.__visualPickerLoaded);
    await select(page, '#rail-logo');
    await writeNote(page, 'Panel is too narrow on this screen.');
    const third = await loadReport(page); assert.equal(third.screenshot.status, 'saved');
    assert.equal(third.note, 'Panel is too narrow on this screen.');
    ok('three reports; repeated use and reload');


    // Enter a fresh draft and seed one asset + one person so the stage
    // tables (and their dia_chi inputs) exist in the DOM.
    // Ensure the drafting tab page is active (default tab may be overview).
    const draftTab = page.locator('.cd-tab[data-tab="drafting"]');
    if (await draftTab.count()) await draftTab.first().click();
    await page.locator('button', { hasText: '+ Hồ sơ mới' }).locator('visible=true').first().click();
    // Persistent profile: run 3's partial draft may trigger the unsaved-changes
    // confirm (modal with primary.danger OK). Accept it to proceed.
    const dlg = page.locator('.modal-overlay button.primary.danger');
    try { await dlg.first().waitFor({ state: 'visible', timeout: 3000 }); } catch {}
    if (await dlg.count()) { await dlg.first().click(); await page.waitForTimeout(800); }
    await page.locator('button', { hasText: '+ Thêm tài sản đầu tiên' }).locator('visible=true').first().click();
    await page.waitForSelector('.cd-tbl input[data-fid$=":dia_chi"]', { timeout: 20000 });
    await page.locator('button', { hasText: '+ Thêm người đầu tiên' }).locator('visible=true').first().click();
    await page.waitForSelector('.cd-ptbl input[data-fid$=":dia_chi"]', { timeout: 20000 });
    // Schema v2: control/module identity + owner linkage on real module views.
    // T1/T2: asset vs person dia_chi — same ancestor shell tier, but distinct
    // owning components (assetTableEl vs peopleTableEl) and shared suggestion CSS.
    await select(page, '.cd-tbl input[data-fid$=":dia_chi"]');
    await writeNote(page, 'Asset address input overflows its cell.');
    const tAsset = await loadReport(page);
    assert.equal(tAsset.schema, 'visual-bug-spike.v2');
    assert.equal(tAsset.source.confidence, 'explicit-control-map');
    assert.equal(tAsset.source.control.controlId, 'notary.asset.address');
    assert.equal(tAsset.source.control.module, 'notary_v2');
    assert.equal(tAsset.source.control.fid, 'a:{row}:dia_chi');
    assert(!/"a:\d+:/.test(JSON.stringify(tAsset)), 'raw row id must not persist');
    assert(tAsset.source.owners.components.some(c => c.symbol === 'assetTableEl' && c.stale === false));
    assert(tAsset.source.owners.components.some(c => c.symbol === 'addressSuggestionEl' && c.stale === false));
    assert(tAsset.source.owners.styles.some(s => s.selector === '.cd-root .cd-address-suggestion {' && s.stale === false));
    assert(tAsset.source.candidates.length > 0, 'ancestor candidates tier unchanged');
    ok('asset dia_chi: explicit-control-map, assetTableEl + suggestion CSS owners, {row} normalized');

    await select(page, '.cd-ptbl input[data-fid$=":dia_chi"]');
    await writeNote(page, 'Person address dropdown renders below the fold.');
    const tPerson = await loadReport(page);
    assert.equal(tPerson.source.control.controlId, 'notary.person.address');
    assert.equal(tPerson.source.control.fid, 'p:{row}:dia_chi');
    assert(tPerson.source.owners.components.some(c => c.symbol === 'peopleTableEl' && c.stale === false));
    const aSyms = tAsset.source.owners.components.map(c => c.symbol);
    const pSyms = tPerson.source.owners.components.map(c => c.symbol);
    assert(!aSyms.includes('peopleTableEl') && !pSyms.includes('assetTableEl'), 'a:/p: owners must be distinct');
    ok('person dia_chi distinct from asset dia_chi (peopleTableEl, not assetTableEl)');

    // T3: stage table — the table itself is never a hit target (border
    // collapse), so a real structural pick lands on a th. The picker's
    // nearest-ancestor-table tokens let the class-token branch fire.
    await page.keyboard.press('Control+Shift+B');
    await page.locator('.cd-tbl thead th').first().click({ force: true });
    await page.locator('#vb-panel').waitFor();
    await writeNote(page, 'Stage table header columns misalign.');
    const tTable = await loadReport(page);
    assert.equal(tTable.source.control.controlId, 'notary.stage_table');
    assert.equal(tTable.source.confidence, 'explicit-control-map');
    assert.equal(tTable.source.control.scope, 'ancestor-table');
    assert.deepEqual(tTable.source.control.classes, ['cd-stage-tbl']);
    const tSyms = tTable.source.owners.components.map(c => c.symbol);
    assert(tSyms.includes('assetTableEl') && tSyms.includes('peopleTableEl'));
    assert(tTable.source.owners.styles.some(s => s.selector === '.cd-root table.cd-stage-tbl {'));
    assert.equal(await page.locator(tTable.selector).evaluate(e => e.tagName), 'TH');
    ok('stage table TH hit: ancestor-table scope, both table builders + base CSS');

    // An unknown interactive node inside the same table is container context,
    // never an exact mapped control; private identity facets must stay omitted.
    await page.evaluate(() => {
      const input = document.createElement('input');
      input.id = 'PRIVATE_ID_987'; input.dataset.fid = 'PRIVATE_FID_987';
      input.className = 'private-secret-token'; input.value = 'PRIVATE_VALUE_987';
      document.querySelector('.cd-tbl tbody td:last-child').append(input);
    });
    await select(page, '#PRIVATE_ID_987');
    await writeNote(page, 'Unknown input inside stage table.');
    const contained = await loadReport(page);
    assert.equal(contained.source.confidence, 'component-ancestry');
    assert.equal(contained.source.control.scope, 'ancestor-table');
    assert.equal(contained.source.control.controlId, undefined);
    assert.equal(contained.source.control.container.classToken, 'cd-stage-tbl');
    assert.equal(contained.source.control.fid, null);
    assert.equal(contained.source.control.id, null);
    assert.deepEqual(contained.source.control.classes, []);
    assert(!JSON.stringify(contained).includes('PRIVATE_'));
    assert(!JSON.stringify(contained).includes('private-secret-token'));
    assert(contained.source.owners.components.every(c => c.role.startsWith('container:')));
    ok('unknown interactive table target: component-ancestry only; private identity omitted');
    await page.evaluate(() => document.getElementById('PRIVATE_ID_987').remove());

    // T5: rail logo keeps candidates tier and now resolves owner CSS by class.
    assert(first.source.candidates.length > 0);
    assert.equal(first.source.control.controlId, 'shell.rail_logo');
    assert.equal(first.source.owners.components.length, 2);
    assert(first.source.owners.components.some(c => c.symbol === 'rail-logo' && c.file.endsWith('index.html') && c.stale === false));
    assert(first.source.owners.components.some(c => c.symbol === 'setStatus' && c.file.endsWith('renderer.js') && c.stale === false));
    assert(first.source.owners.styles.some(s => s.selector === '.rail-logo {'));
    ok('rail logo: candidates unchanged, .rail-logo CSS owner resolved');

    // T4: upload tab — own-id pattern branch after module navigation.
    await page.keyboard.press('Escape'); // leave the re-armed picker before navigating
    await page.click('.rail-btn[data-id="upload"]');
    await page.getByRole('button', { name: 'Rời màn hình', exact: true }).click();
    await page.waitForSelector('.upload-lab .ul-tablist .ul-tab', { timeout: 20000 });
    await select(page, '#ul-tab-audit');
    await writeNote(page, 'Upload tab highlight clipped.');
    const tTab = await loadReport(page);
    assert.equal(tTab.source.control.controlId, 'upload.tab');
    assert.equal(tTab.source.control.module, 'upload');
    assert.equal(tTab.source.control.id, 'ul-tab-{tabId}');
    assert(tTab.source.owners.components.some(c => c.symbol === 'NS.buildView' && c.stale === false));
    assert(tTab.source.owners.styles.some(s => s.selector === '.ul-tab {'));
    ok('upload tab: id-pattern branch, buildView + .ul-tab CSS, {tabId} normalized');
    // Select a real root hit (gap/padding), not a descendant accidentally
    // clicked at the centre of this flex container.
    const rootHit = await page.evaluate(() => {
      const root = document.querySelector('.upload-lab'), r = root.getBoundingClientRect();
      for (let y = Math.max(r.top + 1, 1); y < Math.min(r.bottom, innerHeight); y += 3) {
        for (let x = Math.max(r.left + 1, 1); x < Math.min(r.right, innerWidth); x += 12) {
          if (document.elementFromPoint(x, y) === root) return { x, y };
        }
      }
      throw new Error('upload_root_hit_missing');
    });
    await page.keyboard.press('Control+Shift+B');
    await page.mouse.click(rootHit.x, rootHit.y);
    await page.locator('#vb-panel').waitFor();
    await writeNote(page, 'Upload module spacing is uneven.');
    const tRoot = await loadReport(page);
    assert.equal(tRoot.source.control.controlId, 'upload.module_root');
    assert.equal(tRoot.source.control.scope, 'exact');
    assert.deepEqual(tRoot.source.control.classes, ['upload-lab']);
    assert(tRoot.source.owners.components.some(c => c.symbol === 'NS.buildView'));
    assert(tRoot.source.owners.styles.some(s => s.selector === '.upload-lab {' && s.line > 0 && s.stale === false));
    ok('upload module root: real root hit, NS.buildView + exact base CSS');


    const invalid = await page.evaluate(() => window.visualBugSpike.save({ selector: '#private', note: 'x'.repeat(9000), sourceIds: [] }));
    assert.equal(invalid.error, 'invalid_payload');
    const denied = await app.evaluate(async ({ ipcMain, BrowserWindow }) => {
      const handler = ipcMain._invokeHandlers.get('visual-bug-spike.save');
      const wc = BrowserWindow.getAllWindows()[0].webContents;
      return handler({ sender: wc, senderFrame: { url: wc.getURL() } }, {});
    });
    assert.equal(denied.error, 'sender_denied'); ok('real handler denies oversized and unexpected frame');
    assert.equal(await page.locator('#vb-panel').count(), 0);
    await app.evaluate(() => { process.env.G1_VISUAL_SPIKE_CAPTURE_FAIL = '1'; });
    await select(page, '#rail-logo');
    await writeNote(page, 'Capture failure path.');
    const failedCapture = await loadReport(page); assert.equal(failedCapture.screenshot.status, 'missing');
    assert.equal(failedCapture.screenshot.reason, 'capture_failed'); ok('capture rejection recorded safely');
    assert.equal(await page.locator('#vb-panel').count(), 0);
    await app.evaluate(() => { delete process.env.G1_VISUAL_SPIKE_CAPTURE_FAIL; process.env.G1_VISUAL_SPIKE_SAVE_FAIL = '1'; });
    await select(page, '#rail-logo'); await writeNote(page, 'Save failure path.');
    assert.equal(await save(page), 'Save failed: save_failed');
    assert.equal(await page.locator('#vb-capture-mask').count(), 0); ok('visible save failure and mask cleanup');
    await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().forEach(w => w.destroy())).catch(() => {});
    await app.close(); current = null;
    results.passed = true;
  } catch (err) { results.passed = false; results.failure = String(err.stack); process.exitCode = 1; }
  finally {
    if (current) {
      // This harness owns a synthetic unsaved draft. Destroy only its windows
      // so a native dirty-close confirmation cannot hang failure teardown.
      await current.app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().forEach(w => w.destroy())).catch(() => {});
      await current.app.close().catch(() => {});
    }
    fs.writeFileSync(path.join(evidence, 'e2e-results.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results, null, 2));
  }
})();
