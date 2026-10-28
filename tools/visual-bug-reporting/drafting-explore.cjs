'use strict';
// Drafting EXPLORATORY break-tests (X1–X5) — reuses drafting-e2e helpers. Report only.
// Synthetic data only. Run: tools/visual-bug-reporting/run-drafting-e2e.sh
// Env: G1_PYTHON (venv python with playwright+notary deps), E2E_OUT (evidence
// dir, default /workspace/e2e-run/<ts>), E2E_ONLY="T1,T3" (subset),
// E2E_KIT (dir with mau-word/ and nhap-file/ synthetic .docx).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const repo = path.resolve(__dirname, '../..');
const isWin = process.platform === 'win32';
const python = process.env.G1_PYTHON ||
  path.join(repo, 'notary_v2/venv', isWin ? 'Scripts/python.exe' : 'bin/python');
const pwPkg = (() => {
  const out = execFileSync(python, ['-c',
    'import playwright,os;print(os.path.join(os.path.dirname(playwright.__file__),"driver","package"))'],
  { encoding: 'utf8' }).trim();
  return out;
})();
const { _electron } = require(pwPkg);
const electronBin = path.join(repo, 'shell/node_modules/electron/dist',
  isWin ? 'electron.exe' : 'electron');
const ts = new Date().toISOString().replace(/[:.]/g, '-');
const OUT = process.env.E2E_OUT || path.join('/workspace/e2e-run', ts);
const KIT = process.env.E2E_KIT || '/workspace/windows-test-kit';
const ONLY = (process.env.E2E_ONLY || '').split(',').filter(Boolean);
fs.mkdirSync(OUT, { recursive: true });

const results = { started: new Date().toISOString(), out: OUT, tests: {}, notes: [] };
let cur = null;               // current test id
let shotN = 0;
function rec(id) { return (results.tests[id] ||= { checks: [], records: {}, shots: [] }); }
function check(name, pass, detail) {
  const r = rec(cur); r.checks.push({ name, pass: !!pass, detail: detail === undefined ? null : detail });
  console.log(`${pass ? 'PASS' : 'FAIL'} [${cur}] ${name}${detail !== undefined && !pass ? ' :: ' + JSON.stringify(detail).slice(0, 400) : ''}`);
  return !!pass;
}
function record(key, val) { rec(cur).records[key] = val; console.log(`REC  [${cur}] ${key} = ${JSON.stringify(val).slice(0, 500)}`); }

// ---------------- app lifecycle ----------------
let A = null; // {app,page,profile,console:[],pageErrors:[]}
async function launch(tag) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), `drafting-e2e-${tag}-`));
  for (const d of ['notary', 'upload', 'output']) fs.mkdirSync(path.join(profile, d), { recursive: true });
  const env = { ...process.env, G1_PYTHON: python,
    G1_NOTARY_DATA_DIR: path.join(profile, 'notary'), G1_UPLOAD_DATA_DIR: path.join(profile, 'upload'),
    G1_OUTPUT_DIR: path.join(profile, 'output'), G1_NOTARY_V2_ROOT: path.join(repo, 'notary_v2'),
    G1_UPLOAD_LAB_ROOT: path.join(repo, 'upload_lab') };
  delete env.ELECTRON_RUN_AS_NODE; delete env.G1_DEV_NOTARY_MOCK;
  const args = [path.join(repo, 'shell'), '--user-data-dir=' + path.join(profile, 'ud')];
  if (!isWin) args.unshift('--no-sandbox');
  const app = await _electron.launch({ executablePath: electronBin, args, env, timeout: 90000 });
  const page = await app.firstWindow();
  page.setDefaultTimeout(15000);
  const st = { app, page, profile, console: [], pageErrors: [] };
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) st.console.push({ t: cur, type: m.type(), text: m.text() }); });
  page.on('pageerror', (e) => st.pageErrors.push({ t: cur, text: String(e && e.stack || e) }));
  await app.evaluate(({ BrowserWindow }) => { const w = BrowserWindow.getAllWindows()[0]; w.setSize(1600, 1000); });
  await page.setViewportSize({ width: 1600, height: 1000 }).catch(() => {});
  await page.waitForFunction(() => document.querySelector('#rail-logo')?.dataset.engineState === 'ready', null, { timeout: 90000 });
  await page.waitForTimeout(1500);
  A = st;
  return st;
}
async function close() {
  if (!A) return;
  collectLogs();
  await A.app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().forEach((w) => w.destroy())).catch(() => {});
  await A.app.close().catch(() => {});
  results.notes.push({ profile: A.profile });
  A = null;
}
function collectLogs() {
  const log = path.join(A.profile, 'ud', 'logs', 'main.log');
  let lines = [];
  try { lines = fs.readFileSync(log, 'utf8').split(/\n/); } catch { /* none */ }
  const bad = lines.filter((l) => /"level":"(error|warn)"/.test(l) &&
    !/"msg":"sidecar exit"/.test(l) && /Traceback|Error|error|exception|500/.test(l));
  results.logs ||= { console: [], pageErrors: [], sidecar: [] };
  results.logs.console.push(...A.console);
  results.logs.pageErrors.push(...A.pageErrors);
  results.logs.sidecar.push(...bad.map((l) => l.slice(0, 600)));
}
async function shot(name) {
  const f = path.join(OUT, `${String(++shotN).padStart(3, '0')}-${cur}-${name}.png`);
  await A.page.screenshot({ path: f, fullPage: true }).catch(() => {});
  rec(cur).shots.push(f);
  return f;
}
function db(sql, params = []) {
  const dbp = path.join(A.profile, 'notary', 'notary.db');
  const code = 'import sqlite3,json,sys\nc=sqlite3.connect(sys.argv[1]);c.row_factory=sqlite3.Row\n' +
    'print(json.dumps([dict(r) for r in c.execute(sys.argv[2], json.loads(sys.argv[3]))], ensure_ascii=False))';
  return JSON.parse(execFileSync(python, ['-c', code, dbp, sql, JSON.stringify(params)], { encoding: 'utf8' }));
}

// ---------------- UI helpers ----------------
const P = () => A.page;
async function confirmModalIfAny() {
  const m = P().locator('.modal button.primary, .modal button.danger').locator('visible=true');
  if (await m.count()) { await m.first().click(); await P().waitForTimeout(300); }
}
async function gotoDrafting() { await P().click('.cd-tab[data-tab="drafting"]'); await P().waitForTimeout(200); }
async function newCase() {
  await gotoDrafting();
  let nb = P().locator('button', { hasText: '+ Hồ sơ mới' }).locator('visible=true');
  if (!(await nb.count())) { await P().click('.cd-tab[data-tab="overview"]'); await P().waitForTimeout(300); nb = P().locator('button', { hasText: '+ Hồ sơ mới' }).locator('visible=true'); }
  await nb.first().click();
  await P().waitForTimeout(400);
  await confirmModalIfAny();
  await P().waitForSelector('.js-save-diagram', { timeout: 10000 });
}
async function addPerson() {
  const first = P().locator('button', { hasText: '+ Thêm người đầu tiên' }).locator('visible=true');
  if (await first.count()) await first.first().click();
  else await P().locator('button', { hasText: '+ Người' }).locator('visible=true').first().click();
  await P().waitForTimeout(150);
}
async function addAsset() {
  const before = await P().locator('input[data-fid$=":so_thua_dat"]').count();
  const first = P().locator('button', { hasText: '+ Thêm tài sản đầu tiên' }).locator('visible=true');
  if (await first.count()) await first.first().click();
  else {
    const b = P().locator('button', { hasText: '+ Tài sản' }).locator('visible=true').first();
    if (await b.isDisabled()) return false;
    await b.click();
  }
  await P().waitForTimeout(150);
  return (await P().locator('input[data-fid$=":so_thua_dat"]').count()) > before;
}
// type like a user: click, select all, type, Tab
async function typeField(sel, idx, value) {
  const el = P().locator(sel).nth(idx);
  await el.click();
  await el.press('Control+a');
  if (value === '') await el.press('Delete'); else await el.type(value, { delay: 5 });
  await el.press('Tab');
  await P().waitForTimeout(120);
}
const pf = (k) => `[data-fid^="p:"][data-fid$=":${k}"]`;
const af = (k) => `[data-fid^="a:"][data-fid$=":${k}"]`;
async function personIndex(name) {
  const vals = await P().locator(pf('ho_ten')).evaluateAll((els) => els.map((e) => e.value));
  return vals.indexOf(name);
}
const INTERNAL_RX = /entity_id|row_id|person_id|node_id|case_id|_id\b|undefined|null\b|NaN|\[object Object\]|Traceback|stage_|snake_case|[a-z]+_[a-z]+_[a-z]+/;
async function visibleText() { return P().evaluate(() => document.body.innerText); }
async function uiErrors() {
  return P().evaluate(() => {
    const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
    const pick = (sel) => [...document.querySelectorAll(sel)].filter(vis).map((e) => e.textContent.trim()).filter(Boolean);
    return {
      banners: pick('.banner.err, .banner.error, .banner.warn, .banner.danger, .cd-notice-top'),
      errors: pick('.error, .cd-err, .is-error, .field-error, [role="alert"], .cd-card-errslot'),
      toasts: pick('.toast, #toast, .toasts > *'),
      invalid: [...document.querySelectorAll('[aria-invalid="true"], .invalid, .cd-invalid, .has-error')].filter(vis).map((e) => e.getAttribute('data-fid') || e.className),
    };
  });
}
async function saveState() {
  return P().evaluate(() => {
    const b = document.querySelector('.js-save-diagram');
    const pill = [...document.querySelectorAll('.cd-topbar *, .cd-case-pill, .cd-ident')].map((e) => e.textContent).find((t) => /HS-\d+|Nháp|Đã lưu/.test(t || '')) || null;
    return b ? { cls: b.className, aria: b.getAttribute('aria-label'), text: b.textContent, disabled: b.disabled, busy: b.getAttribute('aria-busy'), pill } : null;
  });
}
// click Lưu hồ sơ once; observe spinner -> tick and outcome
async function save(label) {
  const t0 = Date.now();
  const before = await saveState();
  await P().click('.js-save-diagram');
  const seen = { busy: false, ok: false, error: false };
  let st;
  for (let i = 0; i < 100; i++) {
    st = await saveState();
    if (/is-busy/.test(st.cls)) seen.busy = true;
    if (/is-ok/.test(st.cls) || /✓/.test(st.text)) { seen.ok = true; break; }
    if (/is-error/.test(st.cls)) { seen.error = true; break; }
    await P().waitForTimeout(100);
  }
  const ms = Date.now() - t0;
  const errs = await uiErrors();
  if (label) await shot(label);
  await P().waitForTimeout(200);
  const after = await saveState();
  return { ...seen, ms, before, after, errs, dirtyAfter: /chưa lưu/.test(after.aria || '') };
}
function lastCase() { return db('select id, workspace_revision, case_state_json, nguoi_chet_id, noi_dung_viec from inheritance_cases order by id desc limit 1')[0]; }
async function openCaseFromOverview(id) {
  await P().click('.cd-tab[data-tab="overview"]');
  await P().locator('button', { hasText: 'Làm mới danh sách' }).first().click();
  await P().waitForSelector(`.cd-case-row:has([data-case-id="${id}"]) .cd-case-open`, { timeout: 15000 });
  await P().click(`.cd-case-row:has([data-case-id="${id}"]) .cd-case-open`);
  await P().waitForTimeout(500);
  await confirmModalIfAny();
  await gotoDrafting();
  await P().waitForSelector('.js-save-diagram');
  await P().waitForTimeout(500);
}
async function stageSnapshot() {
  return P().evaluate(() => {
    const val = (e) => (e.tagName === 'SELECT' ? e.value : e.value);
    const out = {};
    document.querySelectorAll('[data-fid^="p:"], [data-fid^="a:"], [data-fid^="meta:"]').forEach((e) => {
      if (!('value' in e) || e.tagName === 'BUTTON') return;
      const parts = e.getAttribute('data-fid').split(':');
      const key = parts[0] === 'meta' ? 'meta:' + parts[1] : parts[0] + ':' + parts[parts.length - 1];
      (out[key] ||= []).push(val(e));
    });
    return out;
  });
}
async function diagramNodes() {
  return P().evaluate(() => [...document.querySelectorAll('.cd-node[data-node-id], .cd-tp-slot[data-slot-id]')].map((e) => {
    const empty = e.classList.contains('cd-node-empty') || (!e.classList.contains('filled') && !!e.dataset.slotId);
    const nameEl = e.querySelector('.cd-node-name');
    const emptyEl = e.querySelector('.cd-empty-label');
    const rows = e.querySelectorAll('.cd-posrow');
    const ownChips = rows[0] ? [...rows[0].querySelectorAll('.cd-poschip.on')] : [];
    const recChips = rows[1] ? [...rows[1].querySelectorAll('.cd-poschip.on')] : [];
    const x = parseFloat(e.style.left) || 0;
    const y = parseFloat(e.style.top) || 0;
    return {
      id: e.dataset.nodeId || e.dataset.slotId,
      empty,
      label: e.getAttribute('aria-label') || '',
      text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 80),
      name: nameEl ? nameEl.textContent.trim() : null,
      emptyRole: emptyEl ? emptyEl.textContent.trim() : null,
      x,
      y,
      ownChecked: ownChips.length > 0,
      receiveChecked: recChips.length > 0,
    };
  }));
}
async function poolNames() { return P().locator('.cd-pool-card .cd-pool-nm').evaluateAll((els) => els.map((e) => e.firstChild ? e.firstChild.textContent.trim() : e.textContent.trim())); }
async function dragPoolToNode(name, nodeId) {
  const card = P().locator('.cd-pool-card', { hasText: name }).first();
  const target = P().locator(`.cd-node[data-node-id="${nodeId}"], .cd-tp-slot[data-slot-id="${nodeId}"]`).first();
  await card.dragTo(target, { sourcePosition: { x: 6, y: 8 } });
  await P().waitForTimeout(1800); // evaluate debounce → generated slots
}
async function dragNodeToPool(nodeId) {
  // HTML5 DnD: dùng dragTo (Playwright giả lập dataTransfer); cầm ở góc trên-trái để tránh chip/nút.
  const card = P().locator(`.cd-node[data-node-id="${nodeId}"]`).first();
  await card.dragTo(P().locator('.cd-pool-box'), { sourcePosition: { x: 6, y: 8 }, targetPosition: { x: 30, y: 10 } });
  await P().waitForTimeout(1800);
}
async function nodeOf(name) {
  return P().evaluate((nm) => { const n = [...document.querySelectorAll('.cd-node[data-node-id]')].find((e) => e.innerText.includes(nm)); return n ? n.dataset.nodeId : null; }, name);
}
async function emptyNodeIds() { return (await diagramNodes()).filter((n) => n.empty).map((n) => n.id); }
async function layoutBox(sel) { return P().locator(sel).first().boundingBox().catch(() => null); }

// stub native dialogs: queue of path arrays for showOpenDialog
async function stubDialogs(queue) {
  await A.app.evaluate(({ dialog }, q) => {
    globalThis.__e2eQ = q.slice();
    globalThis.__e2eCalls = globalThis.__e2eCalls || [];
    dialog.showOpenDialog = async (...a) => { const opts = a[a.length - 1]; globalThis.__e2eCalls.push(opts); const p = globalThis.__e2eQ.shift(); return p ? { canceled: false, filePaths: p } : { canceled: true, filePaths: [] }; };
    dialog.showSaveDialog = async () => { const p = globalThis.__e2eQ.shift(); return p ? { canceled: false, filePath: p[0] } : { canceled: true }; };
    dialog.showMessageBox = async () => ({ response: 1 });
  }, queue);
}
function docxText(file) {
  const code = 'import sys,docx,json\nd=docx.Document(sys.argv[1])\nt=[p.text for p in d.paragraphs]\n' +
    'for tb in d.tables:\n  for r in tb.rows:\n    for c in r.cells: t.append(c.text)\nprint(json.dumps("\\n".join(t), ensure_ascii=False))';
  return JSON.parse(execFileSync(python, ['-c', code, file], { encoding: 'utf8' }));
}
function listDocx(dir) { const out = []; const walk = (d) => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) walk(p); else if (/\.docx$/i.test(f.name)) out.push(p); } }; if (fs.existsSync(dir)) walk(dir); return out; }
const PLACEHOLDER_RX = /\{\{[^}]*\}\}|\{[A-Za-z_][\w.]*\}|\[\[[^\]]*\]\]|«[^»]*»|<<[^>]*>>|\$\{[^}]*\}|__\w+__/g;

// build a standard case: persons A,B,E,D, asset 123/45
const NAMES = { A: 'Nguyễn Văn An', B: 'Trần Thị Bích', E: 'Lê Văn Em', D: 'Phạm Văn Dũng' };
async function buildABED() {
  await newCase();
  for (let i = 0; i < 4; i++) await addPerson();
  const order = ['A', 'B', 'E', 'D'];
  for (let i = 0; i < 4; i++) await typeField(pf('ho_ten'), i, NAMES[order[i]]);
  await typeField(pf('ngay_sinh'), 1, '01/01/1950');
  await addAsset();
  await typeField(af('so_thua_dat'), 0, '123');
  await typeField(af('so_to_ban_do'), 0, '45');
}

const T = {};
// ---- v2 rules (plan WP8): user scenario A/B/C/D ----
const U = { A: 'Nguyễn Văn A', B: 'Trần Thị B', C: 'Nguyễn Văn C', D: 'Nguyễn Thị D', E: 'Lê Thị E' };
const U_DATA = [
  { name: U.A, birth: '1950', death: '2020' },
  { name: U.B, birth: '1955', death: '1997' },
  { name: U.C, birth: '1975', death: '2001' },
  { name: U.D, birth: '1977', death: '' },
  { name: U.E, birth: '1958', death: '' },
];
async function stagePeople(rows) {
  for (let i = 0; i < rows.length; i++) await addPerson();
  for (let i = 0; i < rows.length; i++) {
    await typeField(pf('ho_ten'), i, rows[i].name);
    if (rows[i].birth) await typeField(pf('ngay_sinh'), i, rows[i].birth);
    if (rows[i].death) await typeField(pf('ngay_chet'), i, rows[i].death);
  }
  await addAsset();
  await typeField(af('so_thua_dat'), 0, '100');
  await typeField(af('so_to_ban_do'), 0, '10');
}
const emptyOf = (nodes, role, ofName) => nodes.filter((n) => {
  if (!n.empty) return false;
  const er = n.emptyRole || '';
  if (!(er === role || er.startsWith(role + ' của '))) return false;
  if (!ofName) return true;
  return `${n.label || ''} ${er}`.includes(ofName);
});
const byName = (nodes, nm) => nodes.find((n) => !n.empty && n.name === nm);
async function dropInto(name, role, ofName) {
  // Chờ engine sinh ô (không phải thử thả lại): tối đa ~10s.
  let t = null;
  for (let i = 0; i < 50 && !t; i++) {
    t = emptyOf(await diagramNodes(), role, ofName)[0];
    if (!t) await new Promise((r) => setTimeout(r, 200));
  }
  if (!t) {
    check(`empty ${role} slot of ${ofName || '?'} available for ${name}`, false, null);
    return false;
  }
  // Một lần kéo có thể trượt (engine re-layout sau drop trước); thử lại đúng một lần.
  for (let attempt = 0; attempt < 2; attempt++) {
    if (attempt > 0) {
      t = emptyOf(await diagramNodes(), role, ofName)[0];
      if (!t) break;
    }
    await dragPoolToNode(name, t.id);
    if (!(await poolNames()).includes(name)) return true;
    await P().waitForTimeout(500);
  }
  check(`drop ${name} into ${role} slot of ${ofName || '?'}`, false, null);
  return false;
}
function slotRole(label) {
  return String(label || '').replace(/^Ô trống:\s*/, '').split(' của ')[0];
}
async function setDeath(name, value) { await typeField(pf('ngay_chet'), await personIndex(name), value); await P().waitForTimeout(1000); }
async function removeCard(name) {
  const b = P().locator('.cd-node', { hasText: name }).locator('.js-card-remove').first();
  record('removeBtn:' + name, await b.count());
  await b.click();
  await P().waitForTimeout(600);
}
async function toastState() {
  return P().evaluate(() => {
    const t = [...document.querySelectorAll('.toast-undo')].filter((e) => e.offsetWidth || e.offsetHeight);
    return { n: t.length, text: t.map((e) => e.innerText.replace(/\s+/g, ' ').trim()), undo: t.some((e) => !!e.querySelector('.js-toast-undo')) };
  });
}
async function buildUserScenario({ cLiving = false } = {}) {
  await newCase();
  const rows = U_DATA.slice(0, 4).map((r) => ({ ...r }));
  if (cLiving) rows[2].death = '';
  await stagePeople(rows);
  await dragPoolToNode(U.A, 'owner');
  await dropInto(U.B, 'Vợ/chồng', U.A);
  await dropInto(U.C, 'Con', U.A);
  await dropInto(U.D, 'Con', U.A);
}

// ===================== EXPLORATORY (X*) =====================
const fsNotes = (s) => { try { fs.appendFileSync('/workspace/explore-notes.md', `- ${new Date().toTimeString().slice(0, 8)} [${cur}] ${s}\n`); } catch { /* */ } };
async function snap(label, { shotIt = true } = {}) {
  await P().waitForTimeout(400);
  const nodes = await diagramNodes();
  const pool = await poolNames();
  const ts = await toastState();
  const geo = await P().evaluate(() => {
    const rs = [...document.querySelectorAll('.cd-node')].filter((e) => e.offsetWidth).map((e) => { const r = e.getBoundingClientRect(); return { id: e.dataset.nodeId || e.dataset.slotId, x: r.x, y: r.y, w: r.width, h: r.height, t: e.innerText.replace(/\s+/g, ' ').slice(0, 30) }; });
    const ov = [];
    for (let i = 0; i < rs.length; i++) for (let j = i + 1; j < rs.length; j++) { const a = rs[i], b = rs[j]; if (a.x < b.x + b.w - 1 && b.x < a.x + a.w - 1 && a.y < b.y + b.h - 1 && b.y < a.y + a.h - 1) ov.push([a.t, b.t]); }
    const badges = [...document.querySelectorAll('.cd-node .cd-badge')].map((e) => e.closest('.cd-node').querySelector('.cd-node-name')?.textContent.trim() + ':' + e.textContent.trim());
    const status = [...document.querySelectorAll('.cd-diagram-status, .cd-diag-err, .cd-eval-status, .cd-status')].filter((e) => e.offsetWidth).map((e) => e.innerText.trim()).join(' | ').slice(0, 300);
    return { overlaps: ov, badges, status };
  });
  const ids = nodes.map((n) => n.id);
  const dupIds = ids.filter((x, i) => ids.indexOf(x) !== i);
  const placedNames = nodes.filter((n) => !n.empty).map((n) => n.name);
  const dupPeople = placedNames.filter((x, i) => placedNames.indexOf(x) !== i);
  const uuidRx = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-/i;
  check(`${label} D no uuid in labels`, !nodes.some((n) => uuidRx.test(n.label) || uuidRx.test(n.text) || uuidRx.test(n.emptyRole || '')));
  check(`${label} J no overlapping cards`, geo.overlaps.length === 0, geo.overlaps);
  const s = { label, empties: nodes.filter((n) => n.empty).map((n) => `${n.label}#${n.id.slice(0, 8)}`), placed: nodes.filter((n) => !n.empty).map((n) => `${n.name}@${n.id.slice(0, 8)}${n.ownChecked ? '[Chủ]' : ''}${n.receiveChecked ? '[Nhận]' : ''}`), pool, toast: ts, dupIds, dupPeople, ...geo, errs: A.pageErrors.length, cons: A.console.filter((c) => c.type === 'error').length };
  if (shotIt) s.shot = await shot(label.replace(/[^\w-]+/g, '_').slice(0, 50));
  record('S:' + label, s);
  return s;
}
const emptiesOf = (s, nm) => s.empties.filter((e) => e.includes(`của ${nm})`)).map((e) => e.split(' (')[0]);
async function clickOwn(name, pos = 1) {
  // Chip chọn "Chủ" ở vị trí `pos` trên thẻ `name` — bấm bằng Playwright
  // locator thật (hit-test, như người dùng). Không dùng page.evaluate +
  // el.click() nữa: lần trước là workaround cho chip bị cắt mép.
  const card = P().locator('.cd-node',
    { has: P().locator('.cd-node-name', { hasText: name }) }).first();
  const chip = card.locator('.cd-posrow').first()
    .locator('.cd-poschip').nth(pos - 1);
  await chip.waitFor({ state: 'visible', timeout: 5000 });
  const rect = await chip.boundingBox();
  const disabled = await chip.isDisabled().catch(() => null);
  await chip.click();
  record('clickOwn:' + name, { ok: true, disabled,
    rect: rect && { x: Math.round(rect.x), y: Math.round(rect.y),
      w: Math.round(rect.width), h: Math.round(rect.height) } });
  // Bỏ Chủ cuối cùng (N>0) giờ hỏi xác nhận → explore chọn "Tiếp tục".
  const dlg = P().getByRole('alertdialog');
  if (await dlg.waitFor({ state: 'visible', timeout: 700 }).then(() => true, () => false)) {
    record('confirmLastOwner:' + name, (await dlg.innerText()).trim());
    await dlg.getByRole('button', { name: 'Tiếp tục' }).click();
  }
  await P().waitForTimeout(900);
}
async function waitToastGone() { await P().waitForTimeout(5600); }
async function moveCardTo(name, role, ofName) {
  const t = emptyOf(await diagramNodes(), role, ofName)[0];
  const src = P().locator('.cd-node', { has: P().locator('.cd-node-name', { hasText: name }) }).first();
  if (!t) return false;
  await src.dragTo(P().locator(`.cd-node[data-node-id="${t.id}"]`).first(), { sourcePosition: { x: 6, y: 8 } });
  await P().waitForTimeout(1500); return true;
}
const V = { A: 'Ngô Văn Chủ', B: 'Đặng Thị Vợ', E: 'Võ Thị Vợhai', C: 'Ngô Văn Contruoc', G: 'Ngô Thị Chau', D: 'Ngô Văn Consong', F: 'Ngô Văn Consau', H: 'Ngô Thị Chausau' };
const V_DATA = [
  { name: V.A, birth: '01/01/1950', death: '01/06/2020' },
  { name: V.B, birth: '1955', death: '' },
  { name: V.C, birth: '01/01/1975', death: '01/01/2001' },
  { name: V.G, birth: '01/01/1998', death: '' },
  { name: V.D, birth: '01/01/1977', death: '' },
  { name: V.F, birth: '01/01/1979', death: '01/01/2022' },
  { name: V.H, birth: '01/01/2005', death: '' },
  { name: V.E, birth: '01/01/1960', death: '' },
];
async function buildV(keys) {
  await newCase();
  await stagePeople(V_DATA.filter((r) => keys.includes(Object.keys(V).find((k) => V[k] === r.name))));
  await dragPoolToNode(V.A, 'owner');
  if (keys.includes('B')) await dropInto(V.B, 'Vợ/chồng', V.A);
  if (keys.includes('E')) await dropInto(V.E, 'Vợ/chồng', V.A);
  if (keys.includes('C')) await dropInto(V.C, 'Con', V.A);
  if (keys.includes('G')) await dropInto(V.G, 'Con', V.C);
  if (keys.includes('D')) await dropInto(V.D, 'Con', V.A);
  if (keys.includes('F')) await dropInto(V.F, 'Con', V.A);
  if (keys.includes('H')) await dropInto(V.H, 'Con', V.F);
}

// X1: death-date toggles at owner/spouse/child/thế-vị grandchild
T.X1 = async () => {
  await buildV(['A', 'B', 'C', 'G', 'D']);
  const s0 = await snap('X1-base');
  const steps = [
    [V.A, ''], [V.A, '01/06/2020'],
    [V.B, '01/01/2021'], [V.B, '01/01/1990'], [V.B, ''],
    [V.D, '01/01/2010'], [V.D, '01/01/2022'], [V.D, ''],
    [V.G, '01/01/2005'], [V.G, '01/01/2023'], [V.G, ''],
    [V.C, ''], [V.C, '01/01/2001'],
  ];
  for (const [nm, v] of steps) {
    if ((await personIndex(nm)) < 0) continue;
    await setDeath(nm, v);
    const s = await snap(`X1-${nm.split(' ').pop()}-${v || 'living'}`);
    if (nm === V.B && v === '01/01/1990') check('I spouse who died before has no own slots', emptiesOf(s, V.B).length === 0, emptiesOf(s, V.B));
    if (nm === V.B && v === '01/01/2021') {
      const roles = emptiesOf(s, V.B);
      check('C spouse who died after has Cha and Mẹ', roles.some((e) => slotRole(e) === 'Cha') && roles.some((e) => slotRole(e) === 'Mẹ'), roles);
      check('C spouse who died after has no spouse or duplicate Con slot', !roles.some((e) => slotRole(e) === 'Vợ/chồng' || slotRole(e) === 'Con'), roles);
    }
    fsNotes(`${nm} death=${v || '∅'} → empties ${JSON.stringify(s.empties.map((e) => e.split('#')[0]))} pool=${JSON.stringify(s.pool)} toast=${s.toast.n}`);
    if (s.toast.n && nm === V.A && !v) {
      // Undo after a Stage-caused cascade
      await P().locator('.js-toast-undo').first().click(); await P().waitForTimeout(1200);
      const u = await snap('X1-undo-after-A-living');
      const deathA = await P().locator(pf('ngay_chet')).nth(await personIndex(V.A)).inputValue();
      record('undoAfterStageEdit', { pool: u.pool, placed: u.placed, deathA });
      check('E undo restores the death date', deathA === '01/06/2020', deathA);
      const namesOf = (rows) => rows.map((p) => p.split('@')[0]).sort();
      check('E undo brings people back from the pool',
        JSON.stringify(namesOf(u.placed)) === JSON.stringify(namesOf(s0.placed))
        && JSON.stringify([...u.pool].sort()) === JSON.stringify([...s0.pool].sort()),
        { pool: u.pool, placed: u.placed, basePool: s0.pool });
    }
  }
  // stable IDs: A's slots before vs after full cycle
  const sBack = await snap('X1-after-cycle', { shotIt: false });
  record('idStability', { before: s0.empties, after: sBack.empties });
  // rapid toggles on D (12x, no settle wait)
  const idx = await personIndex(V.D);
  for (let i = 0; i < 12; i++) {
    const el = P().locator(pf('ngay_chet')).nth(idx);
    await el.click(); await el.press('Control+a');
    if (i % 2 === 0) await el.type('01/01/2022', { delay: 0 }); else await el.press('Delete');
    await el.press('Tab');
  }
  await P().waitForTimeout(2500);
  const r = await snap('X1-rapid-12-final(D living)');
  record('rapidFinalD', { dEmpties: emptiesOf(r, V.D), deathD: await P().locator(pf('ngay_chet')).nth(idx).inputValue() });
  // odd count again ends dead
  for (let i = 0; i < 11; i++) {
    const el = P().locator(pf('ngay_chet')).nth(idx);
    await el.click(); await el.press('Control+a');
    if (i % 2 === 0) await el.type('01/01/2022', { delay: 0 }); else await el.press('Delete');
    await el.press('Tab');
  }
  await P().waitForTimeout(2500);
  const r2 = await snap('X1-rapid-11-final(D dead after)');
  record('rapidFinalD2', { dEmpties: emptiesOf(r2, V.D) });
  const sv = await save('X1-saved');
  record('save', { ok: sv.ok, errs: sv.errs });
  const c = lastCase();
  const pre = await snap('X1-pre-reopen', { shotIt: false });
  await newCase();
  await openCaseFromOverview(c.id);
  const post = await snap('X1-reopened');
  record('reopenDiff', { placedPre: pre.placed, placedPost: post.placed, emptPre: pre.empties.length, emptPost: post.empties.length, poolPre: pre.pool, poolPost: post.pool });
};

// X2: owner flip on placed cards
T.X2 = async () => {
  await buildV(['A', 'B', 'D', 'F']);
  await snap('X2-base');
  await clickOwn(V.A); await snap('X2-A-untick-Chu');
  await clickOwn(V.A); await snap('X2-A-retick-Chu');
  // Bỏ tick Chủ đưa người thân về Pool; tick lại không kéo họ lên.
  await dropInto(V.B, 'Vợ/chồng', V.A);
  await dropInto(V.D, 'Con', V.A);
  await dropInto(V.F, 'Con', V.A);
  await clickOwn(V.B); await snap('X2-B-living-spouse-ticked-Chu(2 owners)');
  await clickOwn(V.D); await snap('X2-D-living-child-ticked-Chu(3 owners)');
  await clickOwn(V.D); await snap('X2-D-untick');
  await clickOwn(V.B); await snap('X2-B-untick');
  // Bỏ tick Chủ cuối: isLandOwner = false → ô quan hệ rụng, thẻ chủ đất còn.
  await clickOwn(V.A);
  const noOwner = await snap('X2-A-untick-again(no owner)');
  check('untick last Chủ keeps the owner card', noOwner.placed.some((p) => p.startsWith(V.A + '@')), noOwner.placed);
  check('untick last Chủ returns relatives to the pool', noOwner.pool.includes(V.B) && noOwner.pool.includes(V.D), noOwner.pool);
  // living owner in owner slot
  await newCase();
  await stagePeople([{ name: V.D, birth: '01/01/1977', death: '' }, { name: V.E, birth: '01/01/1980', death: '' }]);
  await dragPoolToNode(V.D, 'owner');
  const liveOwner = await snap('X2b-living-owner');
  check('A living owner has only spouse slots', liveOwner.empties.every((e) => /Vợ\/chồng/.test(e)) && liveOwner.empties.length === 2, liveOwner.empties);
  await dropInto(V.E, 'Vợ/chồng', V.D);
  await snap('X2b-living-owner+spouse');
  await clickOwn(V.D); await snap('X2b-living-owner-untick(spouse slot should vanish)');
  await clickOwn(V.D); await snap('X2b-retick');
};

// X3: removals mid-branch
async function removalCase(tag, who) {
  await buildV(['A', 'B', 'E', 'C', 'G', 'D', 'F', 'H']);
  await waitToastGone();
  const pre = await snap(`X3-${tag}-pre`, { shotIt: tag === 'F' });
  await removeCard(who);
  const ts = await toastState();
  const post = await snap(`X3-${tag}-after-remove`);
  record(`X3:${tag}`, { removed: who, toast: ts, pool: post.pool, remaining: post.placed });
  fsNotes(`remove ${who}: pool=${JSON.stringify(post.pool)} toast=${JSON.stringify(ts.text)}`);
  if (ts.undo) { await P().locator('.js-toast-undo').first().click(); await P().waitForTimeout(1000); const u = await snap(`X3-${tag}-undo`, { shotIt: false }); record(`X3:${tag}:undoEq`, JSON.stringify(u.placed.sort()) === JSON.stringify(pre.placed.sort()) && u.pool.length === pre.pool.length); }
}
T.X3 = async () => {
  await removalCase('F', V.F);
  await removalCase('B', V.B);
  await removalCase('C', V.C);
  await removalCase('E', V.E);
  await removalCase('A', V.A);
};

// X4: usability
T.X4 = async () => {
  await newCase();
  await stagePeople([{ name: V.A, birth: '', death: '' }, { name: V.D, birth: '', death: '' }]);
  // year-only
  await typeField(pf('ngay_mat'.replace('mat', 'chet')), 0, '2001');
  await typeField(pf('ngay_sinh'), 0, '1940');
  const yr = { death: await P().locator(pf('ngay_chet')).nth(0).inputValue(), birth: await P().locator(pf('ngay_sinh')).nth(0).inputValue(), errs: await uiErrors() };
  record('yearOnly', yr);
  await shot('X4-year-only');
  // REAL mouse drag Pool -> owner
  const card = await P().locator('.cd-pool-card', { hasText: V.A }).first().boundingBox();
  const tgt = await P().locator('.cd-node[data-node-id="owner"]').first().boundingBox();
  const m = P().mouse;
  await m.move(card.x + 10, card.y + 10); await m.down();
  for (let i = 1; i <= 20; i++) await m.move(card.x + 10 + (tgt.x + tgt.width / 2 - card.x - 10) * i / 20, card.y + 10 + (tgt.y + tgt.height / 2 - card.y - 10) * i / 20);
  await m.up(); await P().waitForTimeout(1800);
  const s1 = await snap('X4-real-mouse-pool-to-owner');
  record('realMousePool', { placed: s1.placed, pool: s1.pool });
  // Stage grip -> owner (real mouse)
  if (s1.placed.length) await removeCard(V.A);
  const grips = await P().evaluate(() => [...document.querySelectorAll('[draggable="true"]')].filter((e) => e.offsetWidth).map((e) => ({ cls: e.className, t: e.innerText.slice(0, 30) })));
  record('draggables', grips);
  const grip = P().locator('.cd-stage [draggable="true"], .cd-people [draggable="true"], table [draggable="true"]').first();
  if (await grip.count()) {
    const g = await grip.boundingBox();
    await m.move(g.x + g.width / 2, g.y + g.height / 2); await m.down();
    for (let i = 1; i <= 20; i++) await m.move(g.x + (tgt.x + tgt.width / 2 - g.x) * i / 20, g.y + (tgt.y + tgt.height / 2 - g.y) * i / 20);
    await m.up(); await P().waitForTimeout(1800);
    const s2 = await snap('X4-real-mouse-stage-to-owner');
    record('realMouseStage', { placed: s2.placed, pool: s2.pool });
  }
  // first click on + Người while input focused
  const n0 = await P().locator(pf('ho_ten')).count();
  const inp = P().locator(pf('ho_ten')).nth(1);
  await inp.click(); await inp.type('x', { delay: 0 });
  await P().locator('button', { hasText: '+ Người' }).locator('visible=true').first().click();
  await P().waitForTimeout(400);
  const n1 = await P().locator(pf('ho_ten')).count();
  const a0 = await P().locator(af('so_thua_dat')).count();
  const ai = P().locator(af('so_thua_dat')).nth(0);
  await ai.click(); await ai.type('9', { delay: 0 });
  await P().locator('button', { hasText: '+ Tài sản' }).locator('visible=true').first().click();
  await P().waitForTimeout(400);
  const a1 = await P().locator(af('so_thua_dat')).count();
  record('firstClick', { persons: [n0, n1], assets: [a0, a1] });
  // tab order
  await P().locator(pf('ho_ten')).nth(0).click();
  const order = [];
  for (let i = 0; i < 40; i++) { order.push(await P().evaluate(() => { const e = document.activeElement; return (e.getAttribute('data-fid') || '').replace(/^([pa]):[^:]*:/, '$1:') || (e.tagName + '.' + String(e.className).split(' ')[0] + ':' + (e.textContent || '').trim().slice(0, 12)); })); await P().keyboard.press('Tab'); }
  record('tabOrder', order);
  await shot('X4-tab-end');
};

// X5: edge cases
T.X5 = async () => {
  await buildV(['A', 'C', 'D']);
  // move placed D onto another empty Con slot (no duplicate) & onto occupied C (swap?)
  await moveCardTo(V.D, 'Con', V.A); const m1 = await snap('X5-move-D-to-spare');
  record('move', { dupPeople: m1.dupPeople, placed: m1.placed });
  const cId = await nodeOf(V.C);
  await P().locator('.cd-node', { has: P().locator('.cd-node-name', { hasText: V.D }) }).first().dragTo(P().locator(`.cd-node[data-node-id="${cId}"]`).first(), { sourcePosition: { x: 6, y: 8 } });
  await P().waitForTimeout(1500);
  const m2 = await snap('X5-drop-D-onto-occupied-C');
  record('dropOnOccupied', { placed: m2.placed, pool: m2.pool, dup: m2.dupPeople });
  // Điều 619 same date
  await setDeath(V.C, '01/06/2020'); const e1 = await snap('X5-C-same-date-as-A');
  record('sameDate', emptiesOf(e1, V.C));
  // year-only same year as owner
  await setDeath(V.C, '2020'); const e2 = await snap('X5-C-year-2020-vs-A-01-06-2020');
  const yearInput = await P().locator(pf('ngay_chet')).nth(await personIndex(V.C)).inputValue();
  record('yearSameYear', { cSlots: emptiesOf(e2, V.C), badges: e2.badges, input: yearInput });
  check('F year-only is displayed as typed', yearInput === '2020', yearInput);
  check('F year-only 2020 is before 01/06/2020 so C has Con slots', emptiesOf(e2, V.C).some((e) => e.includes('Con')), emptiesOf(e2, V.C));
  await setDeath(V.C, '2001'); const e3 = await snap('X5-C-year-2001');
  record('year2001', { cSlots: emptiesOf(e3, V.C), badges: e3.badges });
  await setDeath(V.C, '06/2001'); const e4 = await snap('X5-C-month-year');
  record('monthYear', { cSlots: emptiesOf(e4, V.C), badges: e4.badges, input: await P().locator(pf('ngay_chet')).nth(await personIndex(V.C)).inputValue() });
  await setDeath(V.C, '31/02/2001'); const e5 = await snap('X5-C-invalid-31-02');
  record('invalidDate', { cSlots: emptiesOf(e5, V.C), badges: e5.badges, status: e5.status });
  check('G invalid date does not wipe the owner', e5.placed.some((p) => p.startsWith(V.A)), e5.placed);
  const badMsg = await P().evaluate(() => [...document.querySelectorAll('.cd-date-msg')].map((e) => e.textContent).join(' '));
  check('G invalid date shows Ngày không hợp lệ', badMsg.includes('Ngày không hợp lệ'), badMsg);
  await setDeath(V.C, '01/01/2001');
  // child born after parent died
  await typeField(pf('ngay_sinh'), await personIndex(V.D), '01/01/2023');
  const b1 = await snap('X5-D-born-after-A-death');
  record('posthumous', { status: b1.status, badges: b1.badges, errs: await uiErrors() });
  check('H no posthumous-child warning', !/sinh sau khi người chết|posthumous/i.test(`${b1.status} ${JSON.stringify(b1.badges)} ${await visibleText()}`));
  // undo after another edit
  await waitToastGone();
  await removeCard(V.A);
  const t1 = await toastState();
  await dragPoolToNode(V.D, 'owner');
  await P().waitForTimeout(300);
  const t2 = await toastState();
  if (t2.undo) { await P().locator('.js-toast-undo').first().click(); await P().waitForTimeout(1200); }
  const u = await snap('X5-undo-after-other-edit');
  record('undoAfterEdit', { toastBefore: t1, toastStillThere: t2, placed: u.placed, pool: u.pool, dup: u.dupPeople });
  // >5 assets
  for (let i = 0; i < 6; i++) record('addAsset' + i, await addAsset());
  record('assetCount', await P().locator(af('so_thua_dat')).count());
  await shot('X5-assets');
  // 32 people
  for (let i = 0; i < 30; i++) await addPerson();
  record('personCount', await P().locator(pf('ho_ten')).count());
  const sv = await save('X5-32-people-save');
  record('save32', { ok: sv.ok, errs: sv.errs });
};

T.X6 = async () => {
  await buildV(['A', 'B', 'D']);
  await snap('X6-base');
  await clickOwn(V.A); await snap('X6-A-untick(no owner)');
  await clickOwn(V.A); await snap('X6-A-retick');
  await dropInto(V.B, 'Vợ/chồng', V.A);
  await dropInto(V.D, 'Con', V.A);
  await clickOwn(V.B); await snap('X6-B-living-spouse-Chu(2 owners)');
  await clickOwn(V.D); await snap('X6-D-living-child-Chu(3 owners)');
  await clickOwn(V.D); await snap('X6-D-untick');
  await clickOwn(V.B); await snap('X6-B-untick');
  await clickOwn(V.A);
  const noOwner = await snap('X6-A-untick-last-Chu');
  check('untick last Chủ keeps the owner card', noOwner.placed.some((p) => p.startsWith(V.A + '@')), noOwner.placed);
  check('untick last Chủ returns relatives to the pool', noOwner.pool.includes(V.B), noOwner.pool);
  const sv = await save('X6-saved'); record('save', { ok: sv.ok, errs: sv.errs });
};
T.X7 = async () => {
  await buildV(['A', 'F']);
  const s = await snap('X7-child-died-after');
  const fRoles = emptiesOf(s, V.F);
  check('B child who died after has no Cha/Mẹ', !fRoles.some((e) => e.includes('Cha') || e.includes('Mẹ')), fRoles);
  const sv = await save('X7-save'); record('saveWithAfterChild', { ok: sv.ok, errs: sv.errs });
  check('B saving the child who died after succeeds', sv.ok, sv.errs);
  await setDeath(V.F, ''); const s2 = await snap('X7-F-living(should drop F slots)');
  record('afterLiving', emptiesOf(s2, V.F));
  // clean toggle cycle (no after-child) then save + reopen
  await buildV(['A', 'B', 'C', 'G', 'D']);
  for (const [nm, v] of [[V.D, '01/01/2010'], [V.D, ''], [V.G, '01/01/2005'], [V.G, ''], [V.C, ''], [V.C, '01/01/2001'], [V.A, ''], [V.A, '01/06/2020']]) { await setDeath(nm, v); const x = await snap(`X7-${nm.split(' ').pop()}-${v || 'living'}`, { shotIt: false }); fsNotes(`${nm}=${v || '∅'} → ${JSON.stringify(x.empties.map((e) => e.split(' (')[0].replace('Ô trống: ', '')))} pool=${JSON.stringify(x.pool)}`); }
  await waitToastGone();
  for (const nm of [V.C, V.D]) await dropInto(nm, 'Con', V.A);
  await dropInto(V.G, 'Con', V.C);
  const pre = await snap('X7-pre-save');
  const sv2 = await save('X7-saved'); record('save2', { ok: sv2.ok, errs: sv2.errs });
  const c = lastCase();
  if (c) { await newCase(); await openCaseFromOverview(c.id); const post = await snap('X7-reopened'); record('reopen', { same: JSON.stringify(pre.placed.sort()) === JSON.stringify(post.placed.sort()) && pre.empties.length === post.empties.length, pre: pre.placed, post: post.placed, pe: pre.empties.length, po: post.empties.length, dates: await stageSnapshot() }); }
};

T.X8 = async () => {
  await buildV(['A', 'B', 'C', 'G', 'D']);
  const idx = await personIndex(V.D);
  const base = await snap('X8-base', { shotIt: false });
  for (const n of [12, 11]) {
    for (let i = 0; i < n; i++) { const el = P().locator(pf('ngay_chet')).nth(idx); await el.click(); await el.press('Control+a'); if (i % 2 === 0) await el.type('01/01/2010', { delay: 0 }); else await el.press('Delete'); await el.press('Tab'); }
    await P().waitForTimeout(2500);
    const r = await snap(`X8-rapid-${n}`);
    record('rapid' + n, { dSlots: emptiesOf(r, V.D), input: await P().locator(pf('ngay_chet')).nth(idx).inputValue(), dup: r.dupIds, toast: r.toast, idsStable: base.empties.every((e) => r.empties.includes(e)) });
  }
};

async function removalCase2(tag, who, keys) {
  await buildV(keys);
  await waitToastGone();
  const pre = await snap(`X9-${tag}-pre`, { shotIt: tag === 'C' });
  await removeCard(who);
  const ts = await toastState();
  const post = await snap(`X9-${tag}-after-remove`);
  record(`X9:${tag}`, { removed: who, toast: ts.text, pool: post.pool, remaining: post.placed, empties: post.empties.map((e) => e.split('#')[0].replace('Ô trống: ', '')) });
  fsNotes(`X9 remove ${who}: pool=${JSON.stringify(post.pool)} toast=${JSON.stringify(ts.text)}`);
  if (ts.undo) { await P().locator('.js-toast-undo').first().click(); await P().waitForTimeout(1200); const u = await snap(`X9-${tag}-undo`, { shotIt: false }); record(`X9:${tag}:undoEq`, { eq: JSON.stringify(u.placed.slice().sort()) === JSON.stringify(pre.placed.slice().sort()), u: u.placed, pool: u.pool }); }
}
T.X9 = async () => {
  const K = ['A', 'B', 'E', 'C', 'G', 'D'];
  await removalCase2('C', V.C, K);
  await removalCase2('B', V.B, K);
  await removalCase2('E', V.E, K);
  await removalCase2('A', V.A, K);
  await removalCase2('D', V.D, K);
};

(async () => {
  const ids = Object.keys(T).filter((k) => /^X/.test(k) && (!ONLY.length || ONLY.includes(k)));
  for (const id of ids) {
    cur = id; fsNotes('start');
    const t0 = Date.now();
    try { await launch(id); await T[id](); } catch (e) { check('ran to completion', false, String(e && e.stack || e).slice(0, 800)); if (A) await shot('crash'); }
    if (A) { record('pageErrors', A.pageErrors.filter((x) => x.t === id)); record('consoleErrors', A.console.filter((c) => c.t === id && c.type === 'error').slice(0, 20)); }
    await close();
    rec(id).ms = Date.now() - t0;
    fs.writeFileSync(path.join(OUT, `results-${id}.json`), JSON.stringify(results.tests[id], null, 2));
    fsNotes(`done in ${Math.round((Date.now() - t0) / 1000)}s → ${OUT}/results-${id}.json`);
  }
  results.sidecar = (results.logs || {}).sidecar;
  const summary = {};
  for (const [id, r] of Object.entries(results.tests)) summary[id] = { pass: r.checks.filter((c) => c.pass).length, fail: r.checks.filter((c) => !c.pass).length, verdict: r.checks.every((c) => c.pass) ? 'ĐẠT' : 'KHÔNG ĐẠT' };
  results.summary = summary;
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results, null, 2));
  console.log('SUMMARY ' + JSON.stringify(summary));
  console.log('EVIDENCE ' + OUT);
  process.exitCode = Object.values(summary).every((s) => s.fail === 0) ? 0 : 1;
})();
