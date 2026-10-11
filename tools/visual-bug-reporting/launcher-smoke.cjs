'use strict';
const fs = require('fs');
const path = require('path');
const net = require('net');
const assert = require('assert/strict');
const { spawn, spawnSync } = require('child_process');
const { repo, playwright, testRoot } = require('./test-runtime.cjs');
const { chromium } = require(playwright);
const root = path.join(testRoot, 'launcher-' + Date.now());
fs.mkdirSync(root, { recursive: true });
const results = { syntheticData: true, actualBat: true, repo, checks: [], reports: [], passed: false };
async function freePort() {
  const server = net.createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
async function exercise(debug) {
  const mode = debug ? 'debug' : 'normal';
  const runtime = path.join(root, mode, 'runtime');
  const sink = path.join(root, mode, 'reports');
  const profile = path.join(runtime, 'profile');
  fs.mkdirSync(profile, { recursive: true });
  const port = await freePort();
  const env = { ...process.env, G1_VISUAL_SPIKE_RUNTIME: runtime, G1_VISUAL_SPIKE_SINK: sink,
    G1_DEV_NOTARY_MOCK: '1', G1_NOTARY_DATA_DIR: path.join(runtime, 'notary'),
    G1_UPLOAD_DATA_DIR: path.join(runtime, 'upload'), G1_OUTPUT_DIR: path.join(runtime, 'output') };
  delete env.G1_VISUAL_BUG_SPIKE;
  // Deliberately inherit this conflicting flag: run.bat must clear it.
  env.ELECTRON_RUN_AS_NODE = '1';
  const bat = path.join(repo, debug ? 'run-dev.bat' : 'run.bat');
  const command = `"${bat}" --remote-debugging-port=${port} --user-data-dir="${profile}"`;
  const child = spawn(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', `"${command}"`],
    { cwd: root, env, windowsHide: true, windowsVerbatimArguments: true });
  let output = '', browser;
  child.stdin.end();
  child.stdout.on('data', data => { output += data; });
  child.stderr.on('data', data => { output += data; });
  const exited = new Promise(resolve => child.once('exit', (code, signal) => resolve({ code, signal })));
  try {
    const deadline = Date.now() + 60000;
    let ready = false;
    while (Date.now() < deadline) {
      if (child.exitCode !== null) throw new Error('BAT exited before window: ' + output);
      try { const response = await fetch(`http://127.0.0.1:${port}/json/version`); if (response.ok) { ready = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    assert(ready, 'BAT did not expose a live Electron window: ' + output);
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
    const context = browser.contexts()[0];
    const page = context.pages()[0] || await context.waitForEvent('page');
    page.setDefaultTimeout(30000);
    await page.waitForSelector('.rail-btn.active');
    assert.equal(new URL(page.url()).pathname.replaceAll('\\', '/').toLowerCase(),
      new URL(require('url').pathToFileURL(path.join(repo, 'shell/src/renderer/index.html'))).pathname.toLowerCase());
    if (!debug) {
      assert.equal(await page.evaluate(() => typeof window.visualBugSpike), 'undefined');
      await page.keyboard.press('Control+Shift+B');
      assert.equal(await page.locator('#vb-highlight').count(), 0);
      results.checks.push('actual run.bat: no reporting bridge/picker; arguments and Electron mode retained');
    } else {
      await page.waitForFunction(() => window.__visualPickerLoaded && document.querySelector('#rail-logo')?.dataset.engineState === 'ready', null, { timeout: 60000 });
      const tab = page.locator('.cd-tab[data-tab="drafting"]');
      if (await tab.count()) await tab.first().click();
      await page.getByRole('button', { name: '+ Hồ sơ mới', exact: true }).click();
      await page.getByRole('button', { name: '+ Thêm tài sản đầu tiên', exact: true }).click();
      const control = page.locator('.cd-tbl input[data-fid$=":dia_chi"]').first();
      await control.waitFor();
      await page.keyboard.press('Control+Shift+B');
      await control.click();
      await page.locator('#vb-panel').waitFor();
      const note = 'Kiểm tra monorepo: chọn ô địa chỉ tài sản và giữ nguyên ghi chú này.';
      await page.fill('#vb-note', note);
      await page.click('#vb-save');
      await page.waitForFunction(() => /^Saved /.test(document.querySelector('#vb-toast')?.textContent || ''));
      const toast = await page.locator('#vb-toast').textContent();
      const id = /^Saved ([a-f0-9-]+);/.exec(toast)?.[1];
      assert(id, toast);
      const file = path.join(sink, id + '.json');
      const report = JSON.parse(fs.readFileSync(file, 'utf8'));
      assert.equal(report.schema, 'visual-bug-spike.v2');
      assert.equal(report.note, note);
      assert.equal(report.source.control.controlId, 'notary.asset.address');
      assert.equal(report.source.control.fid, 'a:{row}:dia_chi');
      assert(report.source.owners.components.some(owner => owner.symbol === 'assetTableEl' && !owner.stale));
      assert(report.source.owners.styles.some(owner => owner.selector === '.cd-root .cd-address-suggestion {' && !owner.stale));
      for (const owner of [...report.source.owners.components, ...report.source.owners.styles]) {
        assert(owner.line > 0 && !owner.stale);
        const line = fs.readFileSync(path.join(repo, owner.file), 'utf8').split(/\r?\n/)[owner.line - 1].trim();
        assert(owner.selector ? line.startsWith(owner.selector) : line.startsWith(`function ${owner.symbol}(`));
      }
      assert.equal(report.screenshot.status, 'saved');
      assert(fs.statSync(path.join(sink, report.screenshot.file)).size > 0);
      results.reports.push(file);
      results.checks.push('actual run-dev.bat: CtrlShiftB, real Notary address control, verbatim Vietnamese note, v2 owner/CSS anchors, native PNG under target private sink');
      // Discard only this fresh harness-owned draft through the real UI.
      await page.keyboard.press('Escape');
      await page.locator('button.js-cd-undo').click();
      await page.locator('.modal-overlay').getByRole('button', { name: 'Hủy thay đổi', exact: true }).click();
      await page.waitForFunction(() => !document.querySelector('.cd-tbl input[data-fid$=":dia_chi"]'));
      // Clear only the harness-owned synthetic draft's native close notification.
      await page.evaluate(() => window.desktop.v1.setDirtyState(false));
    }
    const session = await browser.newBrowserCDPSession();
    await Promise.race([
      session.send('Browser.close').catch(() => {}),
      new Promise(resolve => setTimeout(resolve, 3000)),
    ]);
    const exit = await Promise.race([exited, new Promise(resolve => setTimeout(() => resolve(null), 10000))]);
    results[mode + 'Exit'] = exit;
    assert(exit && exit.code === 0, 'BAT exit did not succeed: ' + JSON.stringify(exit));
    results.checks.push(mode + ' BAT exit code 0');
  } finally {
    if (browser) await Promise.race([
      browser.close().catch(() => {}),
      new Promise(resolve => setTimeout(resolve, 3000)),
    ]);
    if (child.exitCode === null) spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true });
    fs.writeFileSync(path.join(root, mode + '-launch.log'), output);
  }
}
(async () => {
  try { await exercise(false); await exercise(true); results.passed = true; }
  catch (error) { results.failure = String(error.stack); process.exitCode = 1; }
  finally {
    fs.writeFileSync(path.join(root, 'result.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify({ ...results, evidence: path.join(root, 'result.json') }, null, 2));
  }
})();
