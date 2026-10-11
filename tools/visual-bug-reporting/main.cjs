'use strict';
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { randomUUID } = require('crypto');
const { validate } = require('./policy.cjs');
const { resolveOwnership } = require('./linkage.cjs');
const ROOT = __dirname;
const LOCAL = path.resolve(ROOT, '../../_bmad-output/tmp/visual-bug-reporting');
function isolate(app, shellRoot) {
  const runtime = path.resolve(process.env.G1_VISUAL_SPIKE_RUNTIME || path.join(LOCAL, 'runtime'));
  const profile = path.join(runtime, 'profile');
  fs.mkdirSync(profile, { recursive: true });
  app.setPath('userData', profile);
  app.setPath('sessionData', profile);
  for (const [key, sub] of Object.entries({ G1_NOTARY_DATA_DIR: 'notary',
    G1_UPLOAD_DATA_DIR: 'upload', G1_OUTPUT_DIR: 'output' })) {
    process.env[key] = path.join(runtime, sub);
  }
  process.env.G1_NOTARY_V2_ROOT = path.join(shellRoot, '..', 'notary_v2');
  process.env.G1_UPLOAD_LAB_ROOT = path.join(shellRoot, '..', 'upload_lab');
  process.env.G1_DEV_NOTARY_MOCK = '1';
}
function sourceIndex(root) {
  const index = new Map();
  function walk(dir) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const file = path.join(dir, e.name);
      if (e.isDirectory()) walk(file);
      else if (/\.(js|html)$/.test(e.name)) {
        fs.readFileSync(file, 'utf8').split('\n').forEach((line, n) => {
          for (const m of line.matchAll(/(?:\bid\s*=\s*|getElementById\()['"]([a-z][a-z0-9_-]*)['"]/gi)) {
            const hits = index.get(m[1]) || [];
            hits.push({ file: 'shell/src/renderer/' + path.relative(root, file).replaceAll('\\', '/'), line: n + 1 });
            index.set(m[1], hits);
          }
        });
      }
    }
  }
  walk(root); return index;
}
function attach(win, ipcMain, shellRoot) {
  const rendererRoot = path.join(shellRoot, 'src', 'renderer');
  const url = pathToFileURL(path.join(rendererRoot, 'index.html')).href;
  const sources = sourceIndex(rendererRoot);
  const errors = [], events = [];
  let busy = false;
  win.webContents.on('console-message', (_e, level, _message, line, source) => {
    if (level < 2) return;
    let location = 'unmapped';
    try {
      const relative = path.relative(rendererRoot, require('url').fileURLToPath(source));
      if (!relative.startsWith('..') && !path.isAbsolute(relative) && fs.existsSync(path.join(rendererRoot, relative))) {
        location = 'shell/src/renderer/' + relative.replaceAll('\\', '/');
      }
    } catch {}
    errors.push({ severity: level === 2 ? 'warning' : 'error', location,
      line: Number.isInteger(line) && line >= 0 ? line : 0 });
    if (errors.length > 20) errors.shift();
  });
  win.webContents.on('did-finish-load', async () => {
    events.push({ event: 'renderer_loaded' });
    if (events.length > 10) events.shift();
    try { await win.webContents.executeJavaScript(fs.readFileSync(path.join(ROOT, 'picker.js'), 'utf8')); }
    catch { events.push({ event: 'picker_load_failed' }); }
  });
  ipcMain.handle('visual-bug-spike.save', async (event, input) => {
    let data;
    try { data = validate(event, win, url, input); }
    catch (err) { return { ok: false, error: err.message }; }
    if (busy) return { ok: false, error: 'busy' };
    busy = true;
    const start = Date.now(), id = randomUUID();
    let cssKey;
    try {
      const snapshot = await win.webContents.executeJavaScript(`(${snapshotAndMask})(${JSON.stringify(data.selector)})`);
      const candidates = data.sourceIds.flatMap(id => sources.get(id) || []).slice(0, 12);
      // Schema v2: resolve control identity against the registry. Row ids are
      // normalized to {row}/{tabId} placeholders BEFORE any persistence, so
      // the report never carries a live row id. The line cache is per-save so
      // anchor lines always reflect the files as they are NOW (a lifetime
      // cache would pin pre-edit lines after the user edits a source file).
      // Registry paths are renderer-relative ("shell/src/renderer/...");
      // resolve against rendererRoot.
      const srcCache = new Map();
      const readSources = (rel) => {
        const abs = path.join(rendererRoot, rel.split('/').slice(3).join(path.sep));
        let lines = srcCache.get(abs);
        if (lines === undefined) {
          try { lines = fs.readFileSync(abs, 'utf8').split(/\r?\n/); } catch { lines = null; }
          srcCache.set(abs, lines);
        }
        return lines;
      };
      const linkage = resolveOwnership(
        { fid: data.fid || '', ownId: data.ownId || '',
          classes: data.classes, tableTokens: data.tableTokens,
          cellLike: data.cellLike === true, moduleRoot: data.moduleRoot },
        readSources,
      );
      const report = { schema: 'visual-bug-spike.v2', id,
        note: data.note, selector: data.selector, rect: snapshot.rect,
        viewport: snapshot.viewport, context: snapshot.context,
        source: {
          confidence: linkage.confidence,
          control: linkage.control,
          owners: linkage.owners,
          candidates,
        },
        console: errors.slice(), logEvents: events.slice(),
        privacy: "opaque structural wireframe; DOM text and pixels omitted; ids normalized to {row}/{tabId} placeholders; note is the reporter's own raw local text",
        screenshot: { status: 'missing', reason: 'capture_failed' } };
      const sink = process.env.G1_VISUAL_SPIKE_SINK || path.join(LOCAL, 'reports');
      fs.mkdirSync(sink, { recursive: true });
      try {
        cssKey = await win.webContents.insertCSS('* { visibility: hidden !important; } html { background: #ffffff !important; } #vb-capture-mask { visibility: visible !important; }');
        await win.webContents.executeJavaScript('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
        if (process.env.G1_VISUAL_SPIKE_CAPTURE_FAIL === '1') throw new Error('injected');
        const shot = await win.webContents.capturePage();
        if (shot.isEmpty()) throw new Error('empty');
        if (process.env.G1_VISUAL_SPIKE_SAVE_FAIL === '1') throw new Error('injected');
        fs.writeFileSync(path.join(sink, id + '.png'), shot.toPNG());
        report.screenshot = { status: 'saved', file: id + '.png' };
      } catch { /* Safe fixed reason; never serialize exception messages. */ }
      report.elapsedMs = Date.now() - start;
      if (process.env.G1_VISUAL_SPIKE_SAVE_FAIL === '1') throw new Error('injected');
      fs.writeFileSync(path.join(sink, id + '.json'), JSON.stringify(report, null, 2));
      return { ok: true, id, screenshot: report.screenshot.status };
    } catch { return { ok: false, error: 'save_failed' }; }
    finally {
      try {
        await win.webContents.executeJavaScript("document.getElementById('vb-capture-mask')?.remove()");
        if (cssKey) await win.webContents.removeInsertedCSS(cssKey);
      } catch {}
      busy = false;
    }
  });
}
// Runs only via main in the actual renderer; reads geometry/enumerated flags only.
function snapshotAndMask(selector) {
  const target = document.querySelector(selector);
  if (!target || target.closest('#vb-panel')) throw new Error('target_missing');
  const rectOf = e => { const r = e.getBoundingClientRect();
    return Object.fromEntries(['x', 'y', 'width', 'height'].map(k => [k, Math.round(r[k])])); };
  const rect = rectOf(target);
  const canvas = document.createElement('canvas');
  canvas.id = 'vb-capture-mask'; canvas.width = innerWidth; canvas.height = innerHeight;
  Object.assign(canvas.style, { position: 'fixed', inset: '0', width: '100vw', height: '100vh',
    zIndex: '2147483647', background: '#fff', pointerEvents: 'none' });
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#b0b0b0'; ctx.lineWidth = 1;
  for (const e of document.querySelectorAll('nav,main,section,button,input,select,textarea')) {
    if (e.closest('#vb-panel')) continue;
    const r = rectOf(e);
    if (r.width > 0 && r.height > 0) ctx.strokeRect(r.x + .5, r.y + .5, r.width, r.height);
  }
  ctx.strokeStyle = '#ff0000'; ctx.lineWidth = 3;
  ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
  document.body.append(canvas);
  const allow = (value, choices) => choices.includes(value) ? value : 'unknown';
  return { rect, viewport: { width: innerWidth, height: innerHeight, scale: devicePixelRatio },
    context: {
      module: allow(document.querySelector('.rail-btn.active')?.dataset.id,
        ['notary_v2', 'upload', 'office', 'search', 'status']),
      tab: allow(document.querySelector('[role=tab][aria-selected=true]')?.id,
        ['ul-tab-audit', 'ul-tab-scan-upload']),
      engine: allow(document.querySelector('#rail-logo')?.dataset.engineState,
        ['ready', 'starting', 'restarting', 'stopped', 'unavailable']),
      notaryMock: true,
    } };
}
module.exports = { isolate, attach, sourceIndex };
