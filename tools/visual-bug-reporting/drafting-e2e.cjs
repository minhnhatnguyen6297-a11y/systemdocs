'use strict';
// Drafting E2E (T1–T9) — Playwright-Electron, REAL sidecar + fresh temp DB.
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

// ---------------- tests ----------------
const T = {};
T.T1 = async () => {
  await buildABED();
  await shot('filled');
  await typeField(pf('ngay_chet'), 1, '03/03/2020');
  const typedOk = (await P().locator(pf('ngay_sinh')).nth(1).inputValue()) === '01/01/1950';
  check('B birth date kept after typing death date', typedOk);
  await shot('death-date');
  const r = await save('after-save');
  record('save', { busy: r.busy, ok: r.ok, error: r.error, ms: r.ms, after: r.after, errs: r.errs });
  check('save shows spinner (busy)', r.busy);
  check('save success tick', r.ok && !r.error, r.errs);
  check('pill says Đã lưu', /Đã lưu/.test(r.after.pill || ''), r.after.pill);
  check('no red/warn banner', r.errs.banners.length === 0, r.errs.banners);
  check('no visible error text', r.errs.errors.length === 0, r.errs.errors);
  const txt = await visibleText();
  const internal = txt.split('\n').filter((l) => /entity_id|row_id|person_id|case_id|node_id|\[object Object\]|undefined|Traceback/.test(l));
  check('no internal-id text on screen', internal.length === 0, internal);
  const rawCodes = (await uiErrors()).toasts.filter((t) => /^[a-z_]+:/.test(t));
  check('no raw error-code toast (e.g. engine_unavailable:)', rawCodes.length === 0, rawCodes);
  const assetRed = await P().evaluate(() => { const c = document.querySelector('.card.cd-assets'); if (!c) return null; const cs = getComputedStyle(c); return { border: cs.borderColor, cls: c.className, err: [...c.querySelectorAll('.error,.is-error,[aria-invalid="true"],.cd-invalid,.cd-card-errslot:not(:empty)')].map((e) => e.textContent || e.getAttribute('data-fid')) }; });
  record('assetCard', assetRed);
  check('asset card not red', assetRed && assetRed.err.length === 0 && !/rgb\((2[0-5]\d|1[89]\d), ?([0-9]|[1-9]\d), ?([0-9]|[1-9]\d)\)/.test(assetRed.border), assetRed);
  const c = lastCase();
  const rows = db('select ho_ten, ngay_sinh, ngay_chet from case_person_rows where case_id=? order by vitri', [c.id]);
  record('dbPersons', rows);
  check('DB has 4 persons, B dates', rows.length === 4 && rows.some((x) => x.ho_ten === NAMES.B && x.ngay_sinh === '1950-01-01' && x.ngay_chet === '2020-03-03'), rows);
  const assets = db('select so_thua_dat, so_to_ban_do from case_asset_rows where case_id=?', [c.id]);
  check('DB asset 123/45', assets.length === 1 && assets[0].so_thua_dat === '123' && assets[0].so_to_ban_do === '45', assets);
  results.caseT1 = c.id;
};
T.T2 = async () => {
  await buildABED();
  await save();
  let rev0 = lastCase().workspace_revision;
  record('rev0', rev0);
  const revs = []; const fails = [];
  for (let i = 0; i < 10; i++) {
    await typeField(pf('ngay_chet'), 1, i % 2 === 0 ? '03/03/2020' : '');
    const r = await save(i === 0 || i === 9 ? `toggle-${i}` : null);
    const c = lastCase();
    const dbDeath = db('select ngay_chet from case_person_rows where case_id=? and ho_ten=?', [c.id, NAMES.B])[0]?.ngay_chet ?? null;
    revs.push({ i, ok: r.ok, rev: c.workspace_revision, death: dbDeath, ms: r.ms, errs: r.errs.errors.concat(r.errs.banners) });
    if (!r.ok || r.error) fails.push(i);
  }
  record('rounds', revs);
  check('10/10 saves succeeded', fails.length === 0, fails);
  const inc = revs.every((x, i) => x.rev === (i === 0 ? rev0 : revs[i - 1].rev) + 1);
  check('revision increments by 1 each save', inc, revs.map((x) => x.rev));
  check('DB death date toggles', revs.every((x) => (x.i % 2 === 0 ? x.death === '2020-03-03' : !x.death)), revs.map((x) => x.death));
};
T.T3 = async () => {
  await buildABED();
  await typeField(pf('ngay_chet'), 1, '03/03/2020');
  const n0 = await diagramNodes();
  record('initialNodes', n0);
  await shot('diagram-initial');
  const empties = await emptyNodeIds();
  const decSlot = n0.find((n) => /để lại/i.test(n.label || '') || /decedent|owner|nguoi_de_lai/.test(n.id))?.id || empties[0];
  record('decedentSlot', decSlot);
  const rounds = []; let firstClickFails = 0;
  const seq = [
    ['A first', async () => { await dragPoolToNode(NAMES.A, decSlot); }],
    ['A back to pool', async () => { const id = await nodeOf(NAMES.A); if (id) await dragNodeToPool(id); }],
    ['B then remove then A', async () => { await dragPoolToNode(NAMES.B, decSlot); const id = await nodeOf(NAMES.B); if (id) await dragNodeToPool(id); await dragPoolToNode(NAMES.A, decSlot); }],
    ['A off, B on (deceased)', async () => { const id = await nodeOf(NAMES.A); if (id) await dragNodeToPool(id); await dragPoolToNode(NAMES.B, decSlot); }],
  ];
  for (let round = 0; round < 3; round++) {
    for (const [label, fn] of seq) {
      let err = null;
      try { await fn(); } catch (e) { err = String(e.message).slice(0, 200); }
      const nodes = await diagramNodes();
      const pool = await poolNames();
      const r = await save(round === 0 ? `r0-${label.replace(/\W+/g, '_')}` : null);
      if (!r.ok) firstClickFails++;
      rounds.push({ round, label, err, ok: r.ok, ms: r.ms, dirtyAfter: r.dirtyAfter, placed: nodes.filter((n) => !n.empty).map((n) => n.id + '=' + n.text), pool, errs: r.errs.errors.concat(r.errs.banners) });
    }
  }
  record('rounds', rounds);
  check('every drag op without exception', rounds.every((x) => !x.err), rounds.filter((x) => x.err));
  check('save works on first click every time', firstClickFails === 0, firstClickFails);
  check('not dirty right after save', rounds.every((x) => !x.dirtyAfter), rounds.filter((x) => x.dirtyAfter).map((x) => x.label));
  const expectPool = { 'A back to pool': [NAMES.A], 'B then remove then A': [NAMES.B], 'A off, B on (deceased)': [NAMES.A] };
  const wrong = rounds.filter((x) => (expectPool[x.label] || []).some((nm) => !x.pool.includes(nm)) || (x.label === 'A first' && x.pool.includes(NAMES.A)));
  check('placements/unassignments actually applied each step', wrong.length === 0, wrong.map((x) => [x.round, x.label, x.placed, x.pool]));
  const last = rounds[rounds.length - 1];
  check('final state: B placed on decedent slot', last.placed.some((p) => p.includes(NAMES.B)), last.placed);
  const nodes = await diagramNodes();
  record('finalNodes', nodes);
  const leaks = nodes.filter((n) => /[a-z]+_[a-z]+/.test(n.label || ''));
  check('slot labels/tooltips have no internal ids', leaks.length === 0, leaks.map((n) => n.label));
  await shot('final-deceased-B');
  const hasFather = nodes.some((n) => /Cha/.test(n.label || n.text));
  const hasMother = nodes.some((n) => /Mẹ/.test(n.label || n.text));
  const hasSpouse = nodes.some((n) => /Vợ\/chồng/.test(n.label || n.text));
  const hasChild = nodes.some((n) => /Con/.test(n.label || n.text));
  check('deceased placed person has father/mother/spouse/child slots', hasFather && hasMother && hasSpouse && hasChild, nodes.map((n) => n.label || n.text));
  const c = lastCase();
  const cs = JSON.parse(c.case_state_json || '{}');
  record('caseStateKeys', Object.keys(cs));
  const parts = db('select vai_tro, case_person_row_id from inheritance_participants where ho_so_id=?', [c.id]);
  record('participantsDb', parts);
  check('DB persisted decedent', c.nguoi_chet_id != null || parts.some((p) => /chet|de_lai|decedent/i.test(p.vai_tro || '')) || JSON.stringify(cs).includes('owner'), { nguoi_chet_id: c.nguoi_chet_id, parts });
};
T.T4 = async () => {
  await newCase();
  await addPerson();
  await typeField(pf('ho_ten'), 0, 'Hoàng Văn Một');
  await addAsset();
  await typeField(af('so_thua_dat'), 0, '77');
  await typeField(af('so_to_ban_do'), 0, '8');
  const before = await stageSnapshot();
  const r = await save('minimal-saved');
  check('minimal case saves', r.ok, r.errs);
  const c = lastCase();
  await newCase();
  const fresh = await stageSnapshot();
  record('newCaseAfterSave', fresh);
  // Spec (README §4 vòng 2, data-rules): hồ sơ mới chép Stage (Người+Tài sản) của hồ sơ Done gần nhất — có chủ ý.
  // Chỉ meta/Diagram/provenance phải trống. Việc chép Stage ghi là decision item.
  record('newCaseCopiesStage(by spec)', (fresh['p:ho_ten'] || []).length > 0);
  check('new case: no previous meta', ['meta:noi_niem_yet', 'meta:ngay_lap_ho_so', 'meta:nguoi_nhan_uy_quyen', 'meta:noi_dung_viec'].every((k) => (fresh[k] || ['']).every((v) => !v)), fresh);
  check('new case: diagram has no previous placements', (await diagramNodes()).every((n) => n.empty), await diagramNodes());
  check('new case: no case id / not marked saved', !/HS-\d+ · Đã lưu/.test(await P().locator('body').innerText()));
  await shot('new-case-empty');
  await openCaseFromOverview(c.id);
  const after = await stageSnapshot();
  await shot('reopened');
  record('before', before); record('after', after);
  const diff = Object.keys({ ...before, ...after }).filter((k) => JSON.stringify(before[k] || []) !== JSON.stringify(after[k] || []));
  check('reopen equals saved (empty stays empty)', diff.length === 0, diff.map((k) => [k, before[k], after[k]]));
  // inheritance case without decedent / owner
  await newCase();
  const nRows = await P().locator(pf('ho_ten')).count();
  if (!nRows) await addPerson();
  await typeField(pf('ho_ten'), 0, 'Đỗ Thị Hai');
  await addPerson(); await typeField(pf('ho_ten'), nRows ? nRows : 1, 'Đỗ Văn Ba');
  const r2 = await save('no-decedent-saved');
  check('inheritance case without decedent saves', r2.ok, r2.errs);
};
T.T5 = async () => {
  await buildABED();
  const b = P().locator('.js-calc-eval');
  check('Xem cách tính enabled', !(await b.isDisabled()));
  await b.click();
  await P().waitForTimeout(2500);
  await shot('calc');
  const modal = await P().evaluate(() => { const m = [...document.querySelectorAll('.modal, .cd-calc, [role="dialog"]')].filter((e) => e.offsetWidth); return m.map((e) => e.innerText); });
  const txt = await visibleText();
  const calcLines = txt.split('\n').filter((l) => /tính|điều kiện|Chưa|thiếu|Không/i.test(l)).slice(0, 30);
  record('modalText', modal); record('calcLines', calcLines);
  check('not blocked: something shown', modal.length > 0 || calcLines.length > 0);
  check('not-computable state shown (Chưa đủ điều kiện, not Không hợp lệ)', /Chưa đủ/i.test(modal.join('\n')) && !/Không hợp lệ/.test(modal.join('\n')), modal);
  check('calc modal status consistent with inline status', !(/Không hợp lệ/.test(modal.join('')) && /Chưa đủ điều kiện/.test(txt.replace(modal.join(''), ''))));
  const pageErr = A.pageErrors.filter((e) => e.t === 'T5');
  check('no page errors', pageErr.length === 0, pageErr);
  await P().keyboard.press('Escape');
};
async function wordExport(mode, destDir) {
  // mode: 'folder' | 'original'
  await P().locator('button', { hasText: 'Xuất Word' }).locator('visible=true').first().click();
  await P().waitForSelector('.cd-word-modal', { timeout: 10000 });
  await P().waitForTimeout(500);
  if (mode === 'folder') {
    await stubDialogs([[path.join(KIT, 'mau-word')], [destDir]]);
    await P().locator('.cd-word-modal button', { hasText: 'Chọn thư mục mẫu' }).click();
    await P().waitForTimeout(2500);
  } else {
    await stubDialogs([[destDir]]);
    const b = P().locator('.cd-word-modal button', { hasText: 'Dùng hợp đồng Word đã nhập' });
    if (!(await b.count())) return { error: 'no original-source button' };
    await b.first().click();
    await P().waitForTimeout(4000);
    // Spec: vị trí Word gốc phải được xác nhận tường minh trước khi xuất.
    const ap = P().locator('.cd-word-modal button', { hasText: 'Áp dụng vị trí đã chọn' });
    const maps = P().locator('.cd-word-modal label', { hasText: '→' }).locator('input[type=checkbox]:not([disabled])');
    for (let i = 0; i < await maps.count(); i++) await maps.nth(i).check().catch(() => {});
    if (await ap.count()) { await ap.first().click(); await P().waitForTimeout(1500); }
  }
  await shot(`word-${mode}-options`);
  const dialogText = await P().locator('.cd-word-modal').innerText();
  await P().locator('.cd-word-modal button', { hasText: 'Chọn thư mục đích' }).click();
  await P().waitForTimeout(500);
  await P().locator('.cd-word-modal .js-word-export').click();
  let resText = '';
  for (let i = 0; i < 60; i++) {
    resText = await P().locator('.cd-word-modal').innerText();
    if (/Đã lưu|Lỗi|Bỏ qua/.test(resText.split('Xuất Word — nhiều văn bản').pop())) { if (!/Đang/.test(resText)) break; }
    await P().waitForTimeout(500);
  }
  await shot(`word-${mode}-result`);
  const missing = resText.split('\n').filter((l) => /thiếu:/.test(l));
  return { dialogText, resText, missing, files: listDocx(destDir) };
}
function analyzeDocx(files, present, absent = []) {
  const out = [];
  for (const f of files) {
    const t = docxText(f);
    const ph = t.match(PLACEHOLDER_RX) || [];
    out.push({ file: path.basename(f), present: present.filter((p) => t.includes(p)), missingPresent: present.filter((p) => !t.includes(p)), absentFound: absent.filter((p) => t.includes(p)), placeholders: [...new Set(ph)].slice(0, 20), sample: t.slice(0, 300) });
  }
  return out;
}
T.T6 = async () => {
  await buildABED();
  await typeField(pf('ngay_chet'), 1, '03/03/2020');
  // single action: no explicit save — export must save itself
  const dest = path.join(A.profile, 'export-folder'); fs.mkdirSync(dest, { recursive: true });
  const r1 = await wordExport('folder', dest);
  record('folderMode', { missing: r1.missing, files: r1.files.map((f) => path.basename(f)), resTail: r1.resText.slice(-800), error: r1.error });
  check('folder mode: docx created', r1.files.length > 0, r1.resText && r1.resText.slice(-500));
  const an1 = analyzeDocx(r1.files, [NAMES.B, '123', '45']);
  record('folderDocx', an1);
  check('folder mode: present data filled (B name/thửa/tờ in some file)', an1.some((a) => a.missingPresent.length === 0), an1.map((a) => [a.file, a.missingPresent]));
  check('folder mode: no leftover placeholders', an1.every((a) => a.placeholders.length === 0), an1.map((a) => [a.file, a.placeholders]));
  const c = lastCase();
  check('export saved the case in same action', !!c && !String((await saveState()).aria || '').includes('chưa lưu'), c && c.id);
  await P().keyboard.press('Escape'); await P().waitForTimeout(300);
  const closeBtn = P().locator('.cd-word-modal button', { hasText: 'Đóng' });
  if (await closeBtn.count()) await closeBtn.first().click();
  // mode 2: import original Word via Nhập file
  await stubDialogs([[path.join(KIT, 'nhap-file', 'Hop dong goc thu nghiem.docx')]]);
  await P().locator('button', { hasText: 'Nhập file' }).locator('visible=true').first().click();
  await P().waitForTimeout(600);
  await P().locator('button', { hasText: 'Chọn file…' }).locator('visible=true').first().click();
  await P().waitForTimeout(600);
  await P().locator('.js-intake-run').click();
  await P().waitForTimeout(8000);
  await shot('intake-result');
  const intakeTxt = await P().locator('.modal').last().innerText().catch(() => '');
  record('intakeText', intakeTxt.slice(0, 1500));
  const put = P().locator('button', { hasText: 'Đưa vào Stage' }).locator('visible=true');
  record('intakePutButtons', await put.count());
  // Nguồn Word gốc chỉ gắn vào hồ sơ khi đưa ít nhất một gợi ý vào Stage.
  const putIn = P().locator('.modal').last().locator('button', { hasText: 'Đưa vào Stage' });
  if (await putIn.count()) { await putIn.first().click(); await P().waitForTimeout(800); }
  const rawKeys = intakeTxt.split('\n').filter((l) => /^[a-z]+_[a-z_]+$/.test(l.trim()));
  check('intake labels have no raw snake_case field names', rawKeys.length === 0, rawKeys);
  // close intake dialog
  const cl = P().locator('.modal button', { hasText: 'Đóng' }).locator('visible=true');
  if (await cl.count()) await cl.last().click();
  await P().waitForTimeout(500);
  const dest2 = path.join(A.profile, 'export-original'); fs.mkdirSync(dest2, { recursive: true });
  const r2 = await wordExport('original', dest2);
  record('originalMode', { missing: r2.missing, files: (r2.files || []).map((f) => path.basename(f)), resTail: (r2.resText || '').slice(-800), error: r2.error });
  check('original mode: docx created', (r2.files || []).length > 0, r2.error || (r2.resText || '').slice(-500));
  if ((r2.files || []).length) {
    const an2 = analyzeDocx(r2.files, [NAMES.B]);
    record('originalDocx', an2);
    check('original mode: no leftover placeholders', an2.every((a) => a.placeholders.length === 0), an2.map((a) => a.placeholders));
  }
};
T.T7 = async () => {
  await buildABED();
  await typeField(pf('ngay_chet'), 1, '03/03/2020');
  const decSlot = (await diagramNodes()).find((n) => /để lại/i.test(n.label || '') || n.id === 'owner')?.id || (await emptyNodeIds())[0];
  await dragPoolToNode(NAMES.B, decSlot);
  const nodes = await diagramNodes();
  record('nodesAfterB', nodes);
  const spouse = nodes.find((n) => n.empty && /Vợ\/chồng/.test(n.label || n.text));
  record('spouseSlot', spouse || null);
  if (!check('spouse slot exists after deceased placed', !!spouse, nodes)) return;
  await dragPoolToNode(NAMES.A, spouse.id);
  let r = await save('spouse-X');
  check('save with spouse X', r.ok, r.errs);
  const idA = await nodeOf(NAMES.A); if (idA) await dragNodeToPool(idA);
  const targetSpouse = (await diagramNodes()).find((n) => n.empty && /Vợ\/chồng/.test(n.label || n.text));
  await dragPoolToNode(NAMES.E, targetSpouse.id);
  r = await save('spouse-Y');
  check('save with spouse Y', r.ok, r.errs);
  const placed = (await diagramNodes()).filter((n) => !n.empty);
  record('placed', placed);
  check('spouse slot holds Y (E)', placed.some((n) => n.id === targetSpouse.id && n.text.includes(NAMES.E)), placed);
  const dest = path.join(A.profile, 'export-t7'); fs.mkdirSync(dest, { recursive: true });
  const w = await wordExport('folder', dest);
  const an = analyzeDocx(w.files, [NAMES.E], [NAMES.A]);
  record('docx', an);
  check('Word: Y present', an.some((a) => a.present.includes(NAMES.E)), an.map((a) => [a.file, a.present]));
  const roleLines = w.files.flatMap((f) => docxText(f).split('\n').filter((l) => /vợ\/chồng/i.test(l)));
  record('spouseRoleLines', roleLines);
  check('Word: spouse role line names Y', roleLines.some((l) => l.includes(NAMES.E)) || roleLines.includes('Là vợ/chồng.'), roleLines);
  check('Word: X not in spouse role', roleLines.every((l) => !l.includes(NAMES.A)), roleLines);
};
T.T8 = async () => {
  await buildABED();
  const txt = await visibleText();
  const btns = await P().evaluate(() => [...document.querySelectorAll('button')].filter((b) => b.offsetWidth).map((b) => b.innerText.trim()).filter(Boolean));
  record('buttons', btns);
  check("no 'Cập nhật' button", !btns.some((b) => /Cập nhật/.test(b)), btns.filter((b) => /Cập nhật/.test(b)));
  check("no 'Lưu nháp' button", !btns.some((b) => /Lưu nháp/.test(b)));
  check('no Zalo in drafting', !/Zalo/i.test(txt));
  const longText = await P().evaluate(() => [...document.querySelectorAll('.cd-root p, .cd-root .muted, .cd-root .hint, .cd-root div, .cd-root span')].filter((e) => e.offsetWidth && e.children.length === 0 && e.textContent.trim().length > 90).map((e) => e.textContent.trim()));
  record('longStaticTexts', longText);
  check('no long static help text (>90 chars)', longText.length === 0, longText);
  const sel = await P().evaluate(() => { const s = document.querySelector('.cd-diagram-type'); if (!s) return null; const head = s.closest('.cd-dg-head, .cd-diagram-head, header, .toolbar, .cd-toolbar'); return { inHead: !!head, headCls: head && head.className, parentCls: s.parentElement.className }; });
  record('diagramTypeSelector', sel);
  check('diagram type selector in diagram header', sel && (sel.inHead || /head|bar/.test(sel.parentCls)), sel);
  const b0 = await layoutBox('.js-save-diagram'); const s0 = await layoutBox('.cd-diagram-type');
  const r = await save();
  check('success = tick (not long text)', r.ok && (r.after.text || '').length < 40, r.after);
  const b1 = await layoutBox('.js-save-diagram'); const s1 = await layoutBox('.cd-diagram-type');
  check('layout not shifted after save', b0 && b1 && Math.abs(b0.y - b1.y) < 2 && Math.abs(b0.x - b1.x) < 40 && Math.abs(s0.y - s1.y) < 2, { b0, b1, s0, s1 });
  // field-level error: invalid date
  await typeField(pf('ngay_sinh'), 0, '99/99/2020');
  await P().waitForTimeout(300);
  const errs = await uiErrors();
  await shot('invalid-date');
  record('invalidDateErrors', errs);
  const fieldErr = await P().evaluate(() => { const i = document.querySelectorAll('[data-fid^="p:"][data-fid$=":ngay_sinh"]')[0]; return { title: i.title, invalid: i.getAttribute('aria-invalid'), cls: i.className, near: i.closest('td') && i.closest('td').innerText }; });
  record('invalidDateField', fieldErr);
  check('invalid date error at field, short', !!(fieldErr.title || fieldErr.invalid === 'true' || /err|invalid/.test(fieldErr.cls)) && errs.banners.length === 0, { fieldErr, errs });
  const r2 = await save('save-with-invalid-date');
  record('saveWithInvalid', { ok: r2.ok, error: r2.error, errs: r2.errs });
  const msgs = [...r2.errs.errors, ...r2.errs.toasts];
  check('error messages short (<=120 chars, single sentence)', msgs.every((m) => m.length <= 120), msgs);
};
T.T9 = async () => {
  await newCase();
  let n = 0;
  for (let i = 0; i < 8; i++) { if (await addAsset()) n++; else break; }
  record('assetLimitReached', n);
  const addBtn = P().locator('button', { hasText: '+ Tài sản' }).locator('visible=true').first();
  const st = { disabled: await addBtn.isDisabled().catch(() => null), title: await addBtn.getAttribute('title').catch(() => null) };
  record('addButtonState', st);
  await shot('asset-limit');
  const txt = await visibleText();
  record('limitText', txt.split('\n').filter((l) => /tối đa|giới hạn|5|3 tài sản/i.test(l)).slice(0, 10));
  check('asset limit = 5 (D-036)', n === 5, n);
  check('limit reported to user', !!st.title || /tối đa/i.test(txt), st);
  for (let i = 0; i < n; i++) await typeField(af('so_thua_dat'), i, String(100 + i));
  const r0 = await save('assets-partial-saved');
  record('saveWithOnlyThua', { ok: r0.ok, errs: r0.errs });
  // Owner S5b (decision-owner-gate-inventory-rulings-20261023): tài sản bắt buộc số thửa + số tờ → chặn Lưu, lỗi tại ô.
  check('save blocked when Tờ bản đồ empty, error at field (S5b)', !r0.ok && r0.errs.errors.some((e) => /Tờ bản đồ/.test(e)), r0.errs.errors);
  check('S5b error text short per asset', r0.errs.errors.every((e) => e.length <= 400), r0.errs.errors);
  for (let i = 0; i < n; i++) await typeField(af('so_to_ban_do'), i, String(10 + i));
  const r = await save('assets-saved');
  check('save with max assets', r.ok, r.errs);
  const c = lastCase();
  record('dbAssets', db('select count(*) n from case_asset_rows where case_id=?', [c.id])[0].n);
};
T.T9b = async () => {
  // T9 bước 2–4: 30 người giả, lưu; Xuất Word chỉ bị chặn khi chưa chọn mẫu; xuất với 30 người.
  await newCase();
  for (let i = 0; i < 30; i++) await addPerson();
  for (let i = 0; i < 30; i++) await typeField(pf('ho_ten'), i, `Người Thử Số ${String(i + 1).padStart(2, '0')}`);
  await addAsset();
  await typeField(af('so_thua_dat'), 0, '901'); await typeField(af('so_to_ban_do'), 0, '09');
  const r = await save('30-people-saved');
  check('save with 30 people', r.ok, r.errs);
  const c = lastCase();
  const n = c ? db('select count(*) n from case_person_rows where case_id=?', [c.id])[0].n : 0;
  check('DB has 30 persons', n === 30, n);
  check('no exception class names on save', !r.errs.errors.some((e) => /[A-Z][a-zA-Z]+Error:/.test(e)), r.errs.errors);
  await P().locator('button', { hasText: 'Xuất Word' }).locator('visible=true').first().click();
  await P().waitForSelector('.cd-word-modal', { timeout: 10000 });
  await P().locator('.cd-word-modal .js-word-export').click();
  await P().waitForTimeout(800);
  const txt = await visibleText();
  await shot('export-no-template');
  check('export without template blocked with clear message', /Chưa chọn thư mục chứa file mẫu/.test(txt), txt.split('\n').filter((l) => /Chưa|chọn/.test(l)).slice(0, 5));
  await P().locator('.cd-word-modal button', { hasText: 'Đóng' }).first().click().catch(() => {});
  await P().waitForTimeout(300);
  const dest = path.join(A.profile, 'export-30'); fs.mkdirSync(dest, { recursive: true });
  const w = await wordExport('folder', dest);
  // Spec word-templates.md §trần slot: Thừa kế >20 người → word.too_many_people theo từng văn bản, báo rõ, không treo/crash.
  const res = (w.resText || '') + '\n' + (w.dialogText || '');
  record('export30', { files: w.files.map((f) => path.basename(f)), tail: res.slice(-600) });
  check('export with 30 people: clear per-document outcome (file or "quá … người" message)', w.files.length > 0 || /20 người|quá nhiều người|vượt/i.test(res), res.slice(-400));
  check('export 30: no exception class names shown', !/[A-Z][a-zA-Z]+Error:/.test(res), res.slice(-300));
  const an = analyzeDocx(w.files, []);
  check('30-people docx: no leftover placeholders', an.every((a) => a.placeholders.length === 0), an.map((a) => [a.file, a.placeholders]));
};
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
const emptyOf = (nodes, role, ofName) => nodes.filter((n) => n.empty && (n.emptyRole === role || (n.emptyRole || '').startsWith(role + ' của ')) && (!ofName || (n.label || '').includes(`của ${ofName})`)));
const byName = (nodes, nm) => nodes.find((n) => !n.empty && n.name === nm);
async function dropInto(name, role, ofName) {
  const t = emptyOf(await diagramNodes(), role, ofName)[0];
  if (!t) { check(`empty ${role} slot of ${ofName || '?'} available for ${name}`, false, null); return false; }
  await dragPoolToNode(name, t.id); return true;
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

T.T10 = async () => {
  await newCase();
  await stagePeople(U_DATA.slice(0, 4));
  await dragPoolToNode(U.A, 'owner');
  let nodes = await diagramNodes();
  record('nodesAfterA', nodes);
  check('dead owner A → 1 Cha + 1 Mẹ', emptyOf(nodes, 'Cha', U.A).length === 1 && emptyOf(nodes, 'Mẹ', U.A).length === 1, nodes.map((n) => n.label));
  check('dead owner A → 2 Vợ/chồng slots (1 + spare)', emptyOf(nodes, 'Vợ/chồng', U.A).length === 2, nodes.map((n) => n.label));
  check('dead owner A → 2 Con slots (1 + spare)', emptyOf(nodes, 'Con', U.A).length === 2, nodes.map((n) => n.label));
  await dropInto(U.B, 'Vợ/chồng', U.A);
  nodes = await diagramNodes();
  check('B (died 1997, before A) generates no slots of her own', !nodes.some((n) => n.empty && (n.label || '').includes(`của ${U.B})`)), nodes.map((n) => n.label));
  check('after B: spare Vợ/chồng slot still present', emptyOf(nodes, 'Vợ/chồng', U.A).length === 1, nodes.map((n) => n.label));
  await dropInto(U.C, 'Con', U.A);
  await dropInto(U.D, 'Con', U.A);
  nodes = await diagramNodes();
  record('nodesFinal', nodes);
  await shot('T10-user-scenario');
  const [a, b, c, d] = [U.A, U.B, U.C, U.D].map((nm) => byName(nodes, nm));
  check('A, B, C, D all placed', a && b && c && d, nodes.map((n) => n.name));
  if (!(a && b && c && d)) return;
  check('C (died 2001, before A) → Con slot(s) under C (thế vị)', emptyOf(nodes, 'Con', U.C).length >= 1, nodes.map((n) => n.label));
  check('C → no Vợ/chồng slot (Điều 652)', emptyOf(nodes, 'Vợ/chồng', U.C).length === 0 && emptyOf(nodes, 'Cha', U.C).length === 0 && emptyOf(nodes, 'Mẹ', U.C).length === 0, nodes.map((n) => n.label));
  check('D (living, non-owner) → no slots', !nodes.some((n) => n.empty && (n.label || '').includes(`của ${U.D})`)), nodes.map((n) => n.label));
  check('A keeps a spare Con slot', emptyOf(nodes, 'Con', U.A).length === 1, emptyOf(nodes, 'Con', U.A));
  check('A keeps a spare Vợ/chồng slot', emptyOf(nodes, 'Vợ/chồng', U.A).length === 1, emptyOf(nodes, 'Vợ/chồng', U.A));
  check('only A ticked Chủ by default', a.ownChecked && ![b, c, d].some((n) => n.ownChecked), [a, b, c, d].map((n) => [n.name, n.ownChecked]));
  check('nobody ticked Nhận by default', ![a, b, c, d].some((n) => n.receiveChecked), [a, b, c, d].map((n) => [n.name, n.receiveChecked]));
  const cha = emptyOf(nodes, 'Cha', U.A)[0];
  const spare = emptyOf(nodes, 'Vợ/chồng', U.A)[0];
  check('generation rows: Cha above A, B same row as A, C/D below', cha && cha.y < a.y && b.y === a.y && c.y > a.y && c.y === d.y, { cha: cha && cha.y, a: a.y, b: b.y, c: c.y, d: d.y });
  check('B directly beside A, spare spouse after B', b.x > a.x && spare && spare.y === a.y && spare.x > b.x && !nodes.some((n) => n.y === a.y && n.x > a.x && n.x < b.x), { a: a.x, b: b.x, spare: spare && spare.x });
  check('children ordered by birth (C 1975 left of D 1977)', c.x < d.x, { c: c.x, d: d.x });
  const uuidRx = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-/i;
  check('no internal ids (uuid) in node labels/tooltips', !nodes.some((n) => uuidRx.test(n.label) || uuidRx.test(n.text)), nodes.filter((n) => uuidRx.test(n.label)).map((n) => n.label));
  const r = await save('T10-saved');
  check('save scenario ok', r.ok, r.errs);
};

T.T11 = async () => {
  await buildUserScenario();
  await setDeath(U.A, '');
  const nodes = await diagramNodes();
  record('nodesAfterALiving', nodes);
  const ts = await toastState();
  record('toast', ts);
  await shot('T11-A-living');
  const pool = await poolNames();
  record('pool', pool);
  check('living A: no Cha/Mẹ/Con slots', ['Cha', 'Mẹ', 'Con'].every((r) => emptyOf(nodes, r).length === 0) && !nodes.some((n) => (n.label || '').includes(`của ${U.C})`)), nodes.map((n) => n.label));
  check('living A: Vợ/chồng slot exists', nodes.some((n) => /Vợ\/chồng/.test(n.emptyRole || '') || n.name === U.B), nodes.map((n) => n.label));
  check('C and D returned to Pool', pool.includes(U.C) && pool.includes(U.D), pool);
  check('toast "Đã đưa N người về Pool" with Hoàn tác', ts.n >= 1 && ts.undo && /về Pool/.test(ts.text.join(' ')), ts);
  await setDeath(U.A, '2020');
  const back = await diagramNodes();
  check('A dead again → Cha/Mẹ/Con slots return', emptyOf(back, 'Cha', U.A).length === 1 && emptyOf(back, 'Con', U.A).length >= 1, back.map((n) => n.label));
};

T.T12 = async () => {
  await buildUserScenario();
  // leaf removal: D → silent
  await removeCard(U.D);
  let ts = await toastState();
  check('removing D (no cascade) → no toast', ts.n === 0, ts);
  await dropInto(U.D, 'Con', U.A);
  record('poolAfterReDropD', await poolNames());
  await P().waitForTimeout(5500); // let any toast expire
  await removeCard(U.A);
  ts = await toastState();
  let pool = await poolNames();
  await shot('T12-remove-A-toast');
  check('removing A → B, C, D back to Pool (incl. spouse)', [U.A, U.B, U.C, U.D].every((n) => pool.includes(n)), pool);
  check('cascade → toast with Hoàn tác', ts.n >= 1 && ts.undo && /3 người/.test(ts.text.join(' ')), ts);
  check('no generated slots remain', (await diagramNodes()).every((n) => n.id === 'owner'), (await diagramNodes()).map((n) => n.label));
  await P().locator('.js-toast-undo').first().click();
  await P().waitForTimeout(800);
  const nodes = await diagramNodes();
  pool = await poolNames();
  await shot('T12-undo');
  check('Hoàn tác restores A, B, C, D exactly', [U.A, U.B, U.C, U.D].every((nm) => byName(nodes, nm)) && pool.length === 0, { pool, names: nodes.map((n) => n.name) });
  // silent toggle
  await P().waitForTimeout(5500);
  await P().locator('.js-toggle-notify-on-remove').first().uncheck();
  await removeCard(U.A);
  ts = await toastState();
  pool = await poolNames();
  check('toggle off → cascade still happens', [U.A, U.B, U.C, U.D].every((n) => pool.includes(n)), pool);
  check('toggle off → no toast', ts.n === 0, ts);
  await P().locator('.js-toggle-notify-on-remove').first().check();
};

T.T13 = async () => {
  await buildUserScenario({ cLiving: true });
  let nodes = await diagramNodes();
  check('C living → no slots under C', !nodes.some((n) => n.empty && (n.label || '').includes(`của ${U.C})`)), nodes.map((n) => n.label));
  await setDeath(U.C, '2001');
  nodes = await diagramNodes();
  record('nodesAfterCDead', nodes);
  await shot('T13-C-dead-stage');
  check('Stage edit C dead 2001 → "Con" slot of C appears', emptyOf(nodes, 'Con', U.C).length >= 1, nodes.map((n) => n.label));
  check('… and no Vợ/chồng slot for C', emptyOf(nodes, 'Vợ/chồng', U.C).length === 0, nodes.map((n) => n.label));
  const c = byName(nodes, U.C); const cc = emptyOf(nodes, 'Con', U.C)[0];
  check('Con của C one row below C', c && cc && cc.y > c.y, { c: c && c.y, cc: cc && cc.y });
};

T.T14 = async () => {
  await newCase();
  await stagePeople(U_DATA);
  await dragPoolToNode(U.A, 'owner');
  await dropInto(U.B, 'Vợ/chồng', U.A);
  await dropInto(U.E, 'Vợ/chồng', U.A);
  const nodes = await diagramNodes();
  record('nodes', nodes);
  await shot('T14-second-spouse');
  check('2nd spouse into spare → a new spare Vợ/chồng slot', emptyOf(nodes, 'Vợ/chồng', U.A).length === 1, nodes.map((n) => n.label));
  const txt = (nm) => (byName(nodes, nm) || {}).text || '';
  check('last placed (E) = Vợ/chồng hợp pháp', /Vợ\/chồng hợp pháp/.test(txt(U.E)) && !/Không phải/.test(txt(U.E)), txt(U.E));
  check('earlier (B) = Không phải vợ/chồng hợp pháp', /Không phải vợ\/chồng hợp pháp/.test(txt(U.B)), txt(U.B));
  const a = byName(nodes, U.A), b = byName(nodes, U.B), e = byName(nodes, U.E);
  check('both spouses on A\'s row', a && b && e && a.y === b.y && a.y === e.y, [a, b, e].map((n) => n && n.y));
};

T.T15 = async () => {
  await newCase();
  await stagePeople(U_DATA.slice(0, 1));
  const ms = [];
  for (let i = 0; i < 20; i++) {
    const t = await P().evaluate(async () => {
      const card = document.querySelector('.cd-pool-card');
      const target = document.querySelector('.cd-node[data-node-id="owner"]');
      const dt = new DataTransfer();
      card.dispatchEvent(new DragEvent('dragstart', { bubbles: true, dataTransfer: dt }));
      target.dispatchEvent(new DragEvent('dragenter', { bubbles: true, cancelable: true, dataTransfer: dt }));
      target.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: dt }));
      const t0 = performance.now();
      target.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt }));
      card.dispatchEvent(new DragEvent('dragend', { bubbles: true, dataTransfer: dt }));
      const ok = () => [...document.querySelectorAll('.cd-empty-label')].some((e) => e.textContent.trim() === 'Cha');
      while (!ok()) { if (performance.now() - t0 > 5000) return -1; await new Promise((r) => requestAnimationFrame(r)); }
      return performance.now() - t0;
    });
    ms.push(t);
    await removeCard(U.A);
    await P().waitForFunction(() => ![...document.querySelectorAll('.cd-empty-label')].some((e) => e.textContent.trim() === 'Cha'), null, { timeout: 5000 }).catch(() => {});
  }
  const ok = ms.filter((x) => x >= 0).sort((x, y) => x - y);
  const p95 = ok[Math.ceil(ok.length * 0.95) - 1];
  record('dropToSlotMs', ms.map((x) => Math.round(x)));
  record('p95', p95);
  check('all 20 drops produced slots', ok.length === 20, ms);
  check(`drop → slots p95 ≤ 200ms (got ${Math.round(p95)}ms)`, p95 <= 200, { p95, median: ok[10] });
};

T.T16 = async () => {
  await buildUserScenario();
  await shot('T16-no-delete');
  const r = await P().evaluate(() => {
    const nodes = [...document.querySelectorAll('.cd-node')];
    const btns = nodes.flatMap((n) => [...n.querySelectorAll('button')].map((b) => ({ t: b.textContent.trim(), cls: b.className, aria: b.getAttribute('aria-label') || '' })));
    const emptyBtns = [...document.querySelectorAll('.cd-node-empty button')].length;
    const body = document.body.innerText;
    return { btns, emptyBtns, menu: /Quan hệ|Thêm cha\/mẹ|Thêm con|Xóa ô|Xoá ô|Thêm ô/.test(body) };
  });
  record('nodeButtons', [...new Set(r.btns.map((b) => b.t + '|' + b.aria.replace(/ .*/, '')))]);
  check('no × / delete-slot button on any node', !r.btns.some((b) => /^[×✕x]$/.test(b.t) || /xóa|xoá|delete/i.test(b.aria + b.cls)), r.btns.filter((b) => /×|xóa|xoá/i.test(b.t + b.aria)));
  check('empty (engine) slots have no buttons', r.emptyBtns === 0, r.emptyBtns);
  check('no relationship menu / add-slot actions', !r.menu, null);
};

T.PROBE = async () => {
  await buildABED();
  await dragPoolToNode(NAMES.A, 'owner');
  record('afterPlace', await poolNames());
  const node = P().locator('.cd-node[data-node-id="owner"]').first();
  record('draggableAttr', await node.getAttribute('draggable'));
  // synthetic HTML5 DnD with a shared DataTransfer
  await P().evaluate(() => {
    const src = document.querySelector('.cd-node[data-node-id="owner"]');
    const box = document.querySelector('.cd-pool-box');
    const dt = new DataTransfer();
    src.dispatchEvent(new DragEvent('dragstart', { bubbles: true, dataTransfer: dt }));
    box.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: dt }));
    box.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt }));
    src.dispatchEvent(new DragEvent('dragend', { bubbles: true, dataTransfer: dt }));
  });
  await P().waitForTimeout(1500);
  record('afterSyntheticDrop', await poolNames());
  await dragPoolToNode(NAMES.A, 'owner');
  await dragNodeToPool('owner');
  record('afterPlaywrightDrag', await poolNames());
  const nb = await P().locator('.cd-node[data-node-id="owner"]').first().boundingBox();
  const bb = await P().locator('.cd-pool-box').boundingBox();
  const m = P().mouse;
  await m.move(nb.x + 30, nb.y + 30); await m.down();
  for (let i = 1; i <= 15; i++) await m.move(nb.x + 30 + (bb.x + 30 - nb.x - 30) * i / 15, nb.y + 30 + (bb.y + bb.height - 20 - nb.y - 30) * i / 15);
  await m.up(); await P().waitForTimeout(1500);
  record('afterManualMouse(center)', await poolNames());
  record('nodeBox', nb);
  await shot('probe');
};
(async () => {
  const ids = Object.keys(T).filter((k) => ONLY.length ? ONLY.includes(k) : k !== 'PROBE');
  for (const id of ids) {
    cur = id;
    const t0 = Date.now();
    try {
      await launch(id);
      await T[id]();
    } catch (e) {
      check('test ran to completion', false, String(e && e.stack || e).slice(0, 800));
      if (A) await shot('crash');
    }
    if (A) {
      const pe = A.pageErrors.filter((x) => x.t === id);
      check('no uncaught page exceptions', pe.length === 0, pe);
    }
    await close();
    rec(id).ms = Date.now() - t0;
  }
  // exploratory sanity summary
  cur = 'SANITY';
  const L = results.logs || { console: [], pageErrors: [], sidecar: [] };
  record('consoleErrors', L.console.filter((c) => c.type === 'error').slice(0, 40));
  record('sidecarErrors', L.sidecar.slice(0, 40));
  check('no console errors', !L.console.some((c) => c.type === 'error'), L.console.filter((c) => c.type === 'error').length);
  check('no sidecar errors in logs', L.sidecar.length === 0, L.sidecar.length);
  const summary = {};
  for (const [id, r] of Object.entries(results.tests)) summary[id] = { pass: r.checks.filter((c) => c.pass).length, fail: r.checks.filter((c) => !c.pass).length, verdict: r.checks.every((c) => c.pass) ? 'ĐẠT' : 'KHÔNG ĐẠT' };
  results.summary = summary;
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results, null, 2));
  console.log('SUMMARY ' + JSON.stringify(summary));
  console.log('EVIDENCE ' + OUT);
  process.exitCode = Object.values(summary).every((s) => s.fail === 0) ? 0 : 1;
})();
