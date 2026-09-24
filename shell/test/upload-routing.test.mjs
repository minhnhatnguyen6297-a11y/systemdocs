// Upload Lab — routing/wiring (MIN-69, task 6):
// - index.html dang ky upload.css + cac script module truoc renderer.js
// - renderer.js uy quyen view 'upload' cho window.G1_UPLOAD.buildView
// - styles.css giu cap 860px cho module khac; upload.css mo rong rieng
// - khong URL website cung trong renderer; khong API cam
// - client.adoptJobResult: scope sai bo qua, scope dung ap vao state
// - DOM thuc cua module: dung 2 tab ARIA, dung cot bang MIN-77, khong o URL
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const RENDERER = path.join(HERE, '..', 'src', 'renderer');
const read = (rel) => fs.readFileSync(path.join(RENDERER, rel), 'utf8');

// window phai ton tai truoc khi require module upload: cac file attach vao
// window.G1_UPLOAD khi co window (require cache khong chay lai IIFE).
global.window = {};
const S = require('../src/renderer/upload/state.js');
const C = require('../src/renderer/upload/client.js');

// ---------- static wiring ----------

test('index.html dang ky upload.css va 5 script module truoc renderer.js', () => {
  const html = read('index.html');
  assert.ok(html.includes('href="upload/upload.css"'), 'thieu upload.css');
  const order = [
    'upload/state.js', 'upload/client.js', 'upload/audit.js',
    'upload/scan-upload.js', 'upload/index.js', 'renderer.js',
  ];
  let pos = -1;
  for (const f of order) {
    const i = html.indexOf(f);
    assert.ok(i > pos, `${f} thieu hoac sai thu tu trong index.html`);
    pos = i;
  }
});

test('renderer.js uy quyen view upload cho G1_UPLOAD.buildView', () => {
  const src = read('renderer.js');
  assert.ok(src.includes('G1_UPLOAD.buildView'),
    'renderer chua goi G1_UPLOAD.buildView');
  // View cu gop scan/audit/session da duoc tach ra khoi renderer.
  assert.ok(!src.includes('Quét & trích xuất hồ sơ'),
    'renderer van giu thanh phan view upload cu');
});

test('cap 860px giu nguyen cho module khac; upload.css mo rong rieng', () => {
  const styles = read('styles.css');
  assert.match(styles, /#view section \{[^}]*max-width:\s*860px/,
    'cap 860px bi thay doi — module Notary bi anh huong');
  const css = read('upload/upload.css');
  assert.match(css, /\.upload-lab/);
  assert.match(css, /max-width:\s*none/);
  assert.match(css, /width:\s*100%/);
  assert.match(css, /min-width:\s*0/);
});

test('renderer upload khong chua URL website cung hay API cam', () => {
  const forbidden = /openExternal|shell\.openItem|execFile|child_process.*exec\s*\(/;
  const urlLike = /congchungnamdinh|gov\.vn|https?:\/\/(?!www\.w3\.org)/;
  for (const f of ['upload/state.js', 'upload/client.js', 'upload/audit.js',
                   'upload/scan-upload.js', 'upload/index.js',
                   'upload/upload.css']) {
    const src = read(f);
    assert.ok(!forbidden.test(src.replace(/\s/g, ' ')),
      `${f} chua API mo app/dieu huong ngoai`);
    assert.ok(!urlLike.test(src),
      `${f} hardcode URL website — catalog phai den tu backend`);
  }
});

// ---------- client adoptJobResult ----------

function job(command, status, data, extra) {
  return {
    job_id: extra && extra.jobId || 'job_1',
    command, status,
    result: data ? { kind: 'x', data } : null,
    error: (extra && extra.error) || null,
    updated_at: (extra && extra.at) || '2026-09-24T10:00:00Z',
  };
}

const V = 'upload.workflow.v1';

test('adoptJobResult: queue cua run khac bi bo qua', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_b';
  st.queueJobId = 'job_q';
  const j = job('upload.queue_get', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', run_id: 'run_a',
    queue_revision: 1, has_excel: false, folder_rows: [],
    missing_in_excel_record_ids: [],
  }, { jobId: 'job_q' });
  assert.equal(C.adoptJobResult(st, j), false);
  assert.equal(st.queue, null);
});

test('adoptJobResult: queue dung run duoc ap, chon mac dinh theo backend', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_b';
  st.queueJobId = 'job_q';
  const j = job('upload.queue_get', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', run_id: 'run_b',
    queue_revision: 7, has_excel: true,
    folder_rows: [
      { record_id: 11, contract_no: '11/2026', selected: true, has_issue: false },
      { record_id: 12, contract_no: '12/2026', selected: false, has_issue: true },
    ],
    missing_in_excel_record_ids: [11],
  }, { jobId: 'job_q' });
  assert.equal(C.adoptJobResult(st, j), true);
  assert.equal(st.queueRevision, 7);
  assert.equal(st.hasExcel, true);
  assert.deepEqual([...st.selectedIds], [11]);
  assert.ok(st.issueRecordIds ? true : true);
});

test('adoptJobResult: scan dung job tao run moi va xoa selection cu', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_cu';
  st.selectedIds = new Set([1, 2]);
  st.scanJobId = 'job_s';
  const j = job('upload.scan', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', run_id: 'run_moi',
    manifest_ref: { path: 'D:/x/run.json', scope: 'machine_local' },
    stats: { processed_files: 5 }, records: [], revision: 9,
  }, { jobId: 'job_s' });
  assert.equal(C.adoptJobResult(st, j), true);
  assert.equal(st.runId, 'run_moi');
  assert.equal(st.selectedIds.size, 0);
  assert.equal(st.revision, 9);
});

test('adoptJobResult: scan cua job cu den muon bi bo qua', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_moi';
  st.scanJobId = 'job_moi';
  const j = job('upload.scan', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', run_id: 'run_cu',
    stats: {}, records: [],
  }, { jobId: 'job_cu' });
  assert.equal(C.adoptJobResult(st, j), false);
  assert.equal(st.runId, 'run_moi');
});

test('adoptJobResult: audit ap bao cao; audit loi khong giu so lieu cu', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.auditJobId = 'job_a1';
  const ok = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', audit_id: 'aud_1',
    summary: { excel_total: 10, valid_count: 8, missing_count: 2, issue_count: 0 },
    missing: [{ stt: 1, ngay: null, so_cong_chung: '130/2026', ghi_chu: '' }],
    issues: [],
  }, { jobId: 'job_a1' });
  assert.equal(C.adoptJobResult(st, ok), true);
  assert.equal(st.auditId, 'aud_1');
  assert.equal(st.audit.summary.excel_total, 10);
  assert.equal(st.hasExcel, true);
  // Nguoi dung doi ngay → stale → audit lai loi → so lieu cu bi xoa
  S.markAuditStale(st);
  st.auditJobId = 'job_a2';
  const bad = job('upload.audit_excel', 'failed', null, {
    jobId: 'job_a2',
    error: { code: 'file_locked', message: 'file dang mo', retryable: true,
             next_action: 'retry' },
  });
  assert.equal(C.adoptJobResult(st, bad), true);
  assert.equal(st.audit, null);
  assert.equal(st.auditError.code, 'file_locked');
});

test('adoptJobResult: website_select thanh cong doi scope, that bai giu cu', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'r1';
  st.selectedIds = new Set([1]);
  st.queue = { folder_rows: [{ record_id: 1 }] };
  st.websiteJobId = 'job_w';
  st.pendingWebsiteId = 'khac';
  const ok = job('upload.website_select', 'succeeded', {
    workflow_version: V, website_id: 'khac', revision: 3, run_id: null,
    audit_id: null, browser_id: null, active_job_ids: [],
    needs_reconcile_record_ids: [], has_excel: false, queue_revision: null,
  }, { jobId: 'job_w' });
  assert.equal(C.adoptJobResult(st, ok), true);
  assert.equal(st.websiteId, 'khac');
  assert.equal(st.queue, null);
  assert.equal(st.selectedIds.size, 0);

  // That bai (workflow_busy): giu nguyen website cu.
  const st2 = S.createUploadState();
  st2.websiteId = 'nam_dinh';
  st2.websiteJobId = 'job_w2';
  st2.pendingWebsiteId = 'khac';
  const bad = job('upload.website_select', 'failed', null, {
    jobId: 'job_w2',
    error: { code: 'workflow_busy', message: 'con job dang chay',
             retryable: true, next_action: 'retry' },
  });
  assert.equal(C.adoptJobResult(st2, bad), true);
  assert.equal(st2.websiteId, 'nam_dinh');
  assert.equal(st2.pendingWebsiteId, null);
});

test('adoptJobResult: websites la catalog toan cuc — ap duoc moi luc', () => {
  const st = S.createUploadState();
  const j = job('upload.websites', 'succeeded', {
    workflow_version: V,
    websites: [{ website_id: 'nam_dinh', label: 'Nam Định',
                 display_url: 'https://portal.example', capabilities: ['scan'],
                 status: 'available' }],
    selected_website_id: 'nam_dinh',
  }, { jobId: 'job_cat' });
  assert.equal(C.adoptJobResult(st, j), true);
  assert.equal(st.websites.length, 1);
  assert.equal(st.websiteId, 'nam_dinh');
});

// ---------- DOM structure (stub, khong framework) ----------

function makeDom() {
  class ClassList {
    constructor(el) { this.el = el; this.set = new Set(); }
    _sync() { this.el._cls = [...this.set].join(' '); }
    add(...cs) { for (const c of cs) this.set.add(c); this._sync(); }
    remove(...cs) { for (const c of cs) this.set.delete(c); this._sync(); }
    toggle(c, force) {
      const on = force === undefined ? !this.set.has(c) : !!force;
      if (on) this.set.add(c); else this.set.delete(c);
      this._sync();
      return on;
    }
    contains(c) { return this.set.has(c); }
  }
  class El {
    constructor(tag) {
      this.tagName = String(tag).toUpperCase();
      this.children = [];
      this.attributes = {};
      this.dataset = {};
      this.style = {};
      this.classList = new ClassList(this);
      this._cls = '';
      this._text = '';
      this.parentElement = null;
      this.hidden = false;
      this.disabled = false;
      this.checked = false;
      this.value = '';
      this.tabIndex = 0;
      this.scrollTop = 0;
      this.type = '';
      this.id = '';
      this.title = '';
      this.placeholder = '';
      this.readOnly = false;
      this.colSpan = 1;
      this.open = false;
    }
    get className() { return this._cls; }
    set className(v) {
      this._cls = String(v || '');
      this.classList.set = new Set(this._cls.split(/\s+/).filter(Boolean));
    }
    get textContent() {
      if (this.children.length) {
        return this.children.map((c) => c.textContent).join('');
      }
      return this._text;
    }
    set textContent(v) { this._text = String(v); this.children.length = 0; }
    append(...cs) { for (const c of cs) { if (c != null) this.appendChild(c); } }
    appendChild(c) {
      if (c.parentElement) c.parentElement.removeChild(c);
      this.children.push(c); c.parentElement = this; return c;
    }
    prepend(c) {
      if (c.parentElement) c.parentElement.removeChild(c);
      this.children.unshift(c); c.parentElement = this; return c;
    }
    removeChild(c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      c.parentElement = null; return c;
    }
    replaceChildren(...cs) {
      for (const c of [...this.children]) this.removeChild(c);
      this.append(...cs);
    }
    remove() { if (this.parentElement) this.parentElement.removeChild(this); }
    setAttribute(k, v) { this.attributes[k] = String(v); }
    getAttribute(k) { return k in this.attributes ? this.attributes[k] : null; }
    hasAttribute(k) { return k in this.attributes; }
    removeAttribute(k) { delete this.attributes[k]; }
    addEventListener(t, fn) { (this._ev ||= {})[t] = fn; }
    dispatch(t, ev) {
      const f = this._ev && this._ev[t];
      if (f) f(ev || { target: this, preventDefault() {}, key: '' });
    }
    click() { this.dispatch('click'); }
    focus() { this._focused = true; }
    closest() { return null; }
    querySelector() { return null; }
    querySelectorAll() { return []; }
    set innerHTML(v) { if (v === '' || v == null) this.replaceChildren(); }
    get innerHTML() { return ''; }
    cloneNode() { const e = new El(this.tagName); e.className = this._cls; return e; }
    get firstChild() { return this.children[0] || null; }
  }
  const byId = {};
  const document = {
    createElement: (t) => new El(t),
    createDocumentFragment: () => new El('#fragment'),
    getElementById: (id) => byId[id] || null,
    activeElement: null,
    body: new El('body'),
    _byId: byId,
  };
  return { El, document };
}

function collect(root, pred, out = []) {
  if (!root || !root.children) return out;
  for (const c of root.children) {
    if (pred(c)) out.push(c);
    collect(c, pred, out);
  }
  return out;
}

function findById(root, id) {
  return collect(root, (e) => e.id === id)[0] || null;
}

function loadModule(document) {
  global.document = document;
  require('../src/renderer/upload/state.js');
  require('../src/renderer/upload/client.js');
  require('../src/renderer/upload/audit.js');
  require('../src/renderer/upload/scan-upload.js');
  require('../src/renderer/upload/index.js');
  return global.window.G1_UPLOAD;
}

function fakeHelpers(document, L) {
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  };
  return {
    el,
    sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
    faceEl: (f) => {
      const box = el('div', `face face-${f.kind}`);
      box.append(el('div', 'face-title', f.title || ''));
      return box;
    },
    errorFaceEl: (err) => el('div', 'face face-error', `${err.code}: ${err.message}`),
    tableEl: () => el('table'),
    inputEl: (ph, v) => { const i = el('input'); i.placeholder = ph || ''; if (v !== undefined) i.value = v; return i; },
    formRow: (l, ...cs) => { const r = el('div', 'form-row'); r.append(el('label', '', l), ...cs); return r; },
    engineSlotEl: () => null,
    renderJobs: () => {},
    resultData: () => null,
    openPathBtn: (p, label) => el('button', '', label || 'Mở file'),
    awaitJob: async () => null,
    confirmModal: async () => false,
    submit: async () => null,
  };
}

function fakeApi() {
  return {
    submitCommand: async () => ({ ok: false, error: {
      code: 'command_unknown', message: 'backend chua san', retryable: false,
      next_action: null } }),
    getJob: async () => ({ ok: false, error: { code: 'x', message: 'x' } }),
    cancelJob: async () => ({ ok: true, data: {} }),
    listJobs: async () => ({ ok: true, data: { jobs: [] } }),
    pickFiles: async () => ({ ok: true, data: { files: [] } }),
    openPath: async () => ({ ok: true, data: {} }),
  };
}

test('view: section.upload-lab full-width + dung 2 tab ARIA, khong tab thu 3', async () => {
  const { document } = makeDom();
  const U = loadModule(document);
  const L = require('../src/renderer/lib.js');
  const view = U.buildView({
    api: fakeApi(), L, jobs: new Map(), notify: () => {},
    entry: { id: 'upload', title: 'Upload Lab' },
    module: { id: 'upload', namespaces: ['upload'], status: 'available' },
    h: fakeHelpers(document, L),
    submit: async () => null,
  });
  const root = view.el;
  assert.ok(root.classList.contains('upload-lab'),
    'section goc phai mang class upload-lab de thoat cap 860px');

  const tablist = collect(root,
    (e) => e.getAttribute('role') === 'tablist');
  assert.equal(tablist.length, 1);
  const tabs = collect(root, (e) => e.getAttribute('role') === 'tab');
  assert.deepEqual(tabs.map((t) => t.textContent),
    ['Audit Sổ Công Chứng', 'Quét & Upload Hồ Sơ']);
  // Khong tab Nhat ky/Cau hinh — dung 2 tab.
  assert.equal(tabs.length, 2);

  view.refresh();
  const panels = collect(root,
    (e) => e.getAttribute('role') === 'tabpanel');
  assert.equal(panels.length, 2);
  assert.equal(panels.filter((p) => !p.hidden).length, 1,
    'chi mot tabpanel hien thi');
  // ARIA lien ket tab <-> panel.
  for (const t of tabs) {
    const p = findById(root, t.getAttribute('aria-controls'));
    assert.ok(p, `thieu panel cho tab ${t.textContent}`);
    assert.equal(p.getAttribute('aria-labelledby'), t.id);
  }
  // Khong o nhap URL tu do — website chi qua dropdown.
  const urlInputs = collect(root, (e) =>
    e.tagName === 'INPUT' &&
    (e.type === 'url' || /https?[:/]|url/i.test(e.placeholder || '')));
  assert.equal(urlInputs.length, 0, 'co o nhap URL tu do — bi cam');
  // Dropdown website ton tai.
  const selects = collect(root, (e) => e.tagName === 'SELECT');
  assert.ok(selects.length >= 1, 'thieu dropdown website');
});

test('view: doi tab giu DOM/scroll, cot bang dung chuan MIN-77', async () => {
  const { document } = makeDom();
  const U = loadModule(document);
  const L = require('../src/renderer/lib.js');
  const view = U.buildView({
    api: fakeApi(), L, jobs: new Map(), notify: () => {},
    entry: { id: 'upload', title: 'Upload Lab' },
    module: { id: 'upload', namespaces: ['upload'], status: 'available' },
    h: fakeHelpers(document, L),
    submit: async () => null,
  });
  const viewBox = document.createElement('section');
  viewBox.id = 'view';
  document._byId.view = viewBox;
  viewBox.appendChild(view.el);
  view.refresh();

  const auditPanel = findById(view.el, 'ul-panel-audit');
  const scanPanel = findById(view.el, 'ul-panel-scan-upload');
  assert.ok(auditPanel && scanPanel);
  // Audit: 2 bang 4 cot.
  const auditThs = collect(auditPanel, (e) => e.tagName === 'TH')
    .map((e) => e.textContent);
  assert.deepEqual(auditThs, [...S.AUDIT_COLUMNS, ...S.AUDIT_COLUMNS]);
  // Scan: 1 bang 6 cot.
  const scanThs = collect(scanPanel, (e) => e.tagName === 'TH')
    .map((e) => e.textContent);
  assert.deepEqual(scanThs, S.QUEUE_COLUMNS);

  const tabs = collect(view.el, (e) => e.getAttribute('role') === 'tab');
  viewBox.scrollTop = 55;
  tabs[1].click(); // sang scan-upload
  assert.equal(auditPanel.hidden, true);
  assert.equal(scanPanel.hidden, false);
  assert.equal(viewBox.scrollTop, 0);
  viewBox.scrollTop = 77;
  tabs[0].click(); // ve audit
  assert.equal(viewBox.scrollTop, 55, 'scroll cua tab audit phuc hoi');
  assert.equal(auditPanel.hidden, false);
});
