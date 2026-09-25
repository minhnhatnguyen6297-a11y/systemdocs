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
  assert.deepEqual([...S.issueRecordIds(st)].sort((a, b) => a - b), [12]);
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

test('view: syncTbody empty→non-empty→empty khong de dong placeholder thua',
  async () => {
    const { document } = makeDom();
    const U = loadModule(document);
    const L = require('../src/renderer/lib.js');
    const jobs = new Map();
    const view = U.buildView({
      api: fakeApi(), L, jobs, notify: () => {},
      entry: { id: 'upload', title: 'Upload Lab' },
      module: { id: 'upload', namespaces: ['upload'], status: 'available' },
      h: fakeHelpers(document, L),
      submit: async () => null,
    });
    view.refresh();
    const scanPanel = findById(view.el, 'ul-panel-scan-upload');
    const qt = collect(scanPanel, (e) => e.tagName === 'TBODY')[0];
    assert.ok(qt, 'khong tim thay tbody bang queue');
    // Rong: dung 1 dong placeholder.
    assert.equal(qt.children.length, 1);
    assert.match(qt.children[0].textContent, /Chưa có hồ sơ/);

    // Workspace + queue co dong → placeholder phai bien mat hoan toan.
    jobs.set('job_ws1', job('upload.workspace_get', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', revision: 1,
      run_id: 'run_1', audit_id: null, browser_id: null,
      has_excel: true, queue_revision: 1,
      needs_reconcile_record_ids: [], active_job_ids: ['job_q'],
    }, { jobId: 'job_ws1', at: '2026-09-24T10:00:01Z' }));
    jobs.set('job_q', job('upload.queue_get', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', run_id: 'run_1',
      queue_revision: 2, has_excel: true,
      folder_rows: [
        { record_id: 1, contract_no: '1/2026', selected: true },
        { record_id: 2, contract_no: '2/2026', selected: false },
      ],
      missing_in_excel_record_ids: [],
    }, { jobId: 'job_q', at: '2026-09-24T10:00:02Z' }));
    view.refresh();
    assert.equal(qt.children.length, 2);
    for (const tr of qt.children) {
      assert.ok(tr.dataset.k && tr.dataset.k !== '__empty__',
        'dong placeholder thua nam lai tren du lieu that');
      assert.ok(!/Chưa có hồ sơ/.test(tr.textContent),
        'chu placeholder con nam trong bang');
    }

    // Queue moi rong → tro lai dung 1 dong placeholder.
    jobs.set('job_ws2', job('upload.workspace_get', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', revision: 2,
      run_id: 'run_1', audit_id: null, browser_id: null,
      has_excel: true, queue_revision: 3,
      needs_reconcile_record_ids: [],
      active_job_ids: ['job_q', 'job_q2'],
    }, { jobId: 'job_ws2', at: '2026-09-24T10:00:03Z' }));
    jobs.set('job_q2', job('upload.queue_get', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', run_id: 'run_1',
      queue_revision: 3, has_excel: true,
      folder_rows: [],
      missing_in_excel_record_ids: [],
    }, { jobId: 'job_q2', at: '2026-09-24T10:00:04Z' }));
    view.refresh();
    assert.equal(qt.children.length, 1);
    assert.match(qt.children[0].textContent, /Chưa có hồ sơ/);
  });

test('adoptJobResult: waiting_user ngoai scope khong pin waitingBanner', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_b';
  // Job waiting cua website khac, khong thuoc activeJobIds → khong banner.
  const stale = job('upload.session_start', 'waiting_user', {
    workflow_version: V, website_id: 'khac', browser_id: 'br_cu',
  }, { jobId: 'job_la' });
  stale.waiting_on = 'login';
  C.adoptJobResult(st, stale);
  assert.equal(st.waitingBanner, null);
  // Job waiting cua chinh view (activeJobIds) → banner duoc pin.
  st.sessionJobId = 'job_ss';
  const mine = job('upload.session_start', 'waiting_user', null,
    { jobId: 'job_ss' });
  mine.waiting_on = 'login';
  C.adoptJobResult(st, mine);
  assert.deepEqual(st.waitingBanner, { on: 'login', jobId: 'job_ss' });
});

test('adoptJobResult: audit terminal khong error (canceled) xoa du lieu cu',
  () => {
    const st = S.createUploadState();
    st.websiteId = 'nam_dinh';
    st.audit = { audit_id: 'aud_cu', summary: { excel_total: 9 } };
    st.auditJobId = 'job_ac';
    const j = job('upload.audit_excel', 'canceled', null,
      { jobId: 'job_ac' });
    assert.equal(C.adoptJobResult(st, j), true);
    assert.equal(st.audit, null);
    assert.equal(st.auditStale, false);
    assert.equal(st.auditError.code, 'job_canceled');
  });

// ---------- task 7: audit wiring ----------

test('adoptJobResult: audit ap dung mot lan — re-adopt khong xoa stale/queueFor', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'r1';
  st.excelFile = { path: 'D:/x/so.xlsx', scope: 'machine_local' };
  st.auditJobId = 'job_a1';
  const ok = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', audit_id: 'aud_1',
    from_date: st.fromDate, to_date: st.toDate,
    summary: { excel_total: 5, valid_count: 3, missing_count: 1, issue_count: 1 },
    missing: [], issues: [],
  }, { jobId: 'job_a1' });
  ok.result.source_files = [{ path: 'D:/x/so.xlsx', scope: 'machine_local' }];
  assert.equal(C.adoptJobResult(st, ok), true);
  assert.equal(st.auditAppliedFor, 'job_a1');
  st.queueFor = { runId: 'r1', auditId: 'aud_1' };
  S.markAuditStale(st);
  assert.equal(st.auditStale, true);
  // Cung job_id den lai tren nhip refresh sau → khong ap lai: nhan
  // "chua cap nhat" va moc queueFor do nguoi dung tao phai giu nguyen.
  assert.equal(C.adoptJobResult(st, ok), false);
  assert.equal(st.auditStale, true);
  assert.deepEqual(st.queueFor, { runId: 'r1', auditId: 'aud_1' });
  // Job audit MOI ap binh thuong va lam sach nhan stale khi bo loc khop.
  st.auditJobId = 'job_a2';
  const ok2 = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', audit_id: 'aud_2',
    from_date: st.fromDate, to_date: st.toDate,
    summary: { excel_total: 6 }, missing: [], issues: [],
  }, { jobId: 'job_a2' });
  assert.equal(C.adoptJobResult(st, ok2), true);
  assert.equal(st.auditAppliedFor, 'job_a2');
  assert.equal(st.auditStale, false);
});

test('adoptJobResult: audit cua bo loc/file cu ap len van danh dau chua cap nhat', () => {
  // Audit chay theo bo loc A; nguoi dung doi ngay giua luc chay → result
  // ve ap duoc nhung PHAI danh dau chua cap nhat (spec §2).
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.auditJobId = 'job_a1';
  st.fromDate = '2026-04-01';
  st.toDate = '2026-04-30';
  const j = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', audit_id: 'aud_1',
    from_date: '2026-03-01', to_date: '2026-03-31',
    summary: { excel_total: 5 }, missing: [], issues: [],
  }, { jobId: 'job_a1' });
  assert.equal(C.adoptJobResult(st, j), true);
  assert.equal(st.auditStale, true, 'result cua bo loc cu phai stale');

  // Doi file giua luc chay → result ap nhung stale.
  const st2 = S.createUploadState();
  st2.websiteId = 'nam_dinh';
  st2.auditJobId = 'job_b1';
  st2.excelFile = { path: 'D:/x/moi.xlsx', scope: 'machine_local' };
  const j2 = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', audit_id: 'aud_2',
    from_date: st2.fromDate, to_date: st2.toDate,
    summary: { excel_total: 2 }, missing: [], issues: [],
  }, { jobId: 'job_b1' });
  j2.result.source_files = [{ path: 'D:/x/cu.xlsx', scope: 'machine_local' }];
  assert.equal(C.adoptJobResult(st2, j2), true);
  assert.equal(st2.auditStale, true, 'result cua file cu phai stale');
});

test('adoptJobResult: audit cua website khac bi tu choi', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.auditJobId = 'job_a';
  const j = job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'khac', audit_id: 'aud_x',
    summary: { excel_total: 9 }, missing: [], issues: [],
  }, { jobId: 'job_a' });
  assert.equal(C.adoptJobResult(st, j), false);
  assert.equal(st.audit, null);
  assert.equal(st.auditAppliedFor, null);
});

test('adoptJobResult: download ap file_ref mot lan; loi ra downloadError', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.downloadJobId = 'job_d1';
  const ok = job('upload.download_export', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', browser_id: 'br1',
    file_ref: { path: 'D:/x/so.xlsx', scope: 'machine_local', sha256: 'x' },
    from_date: st.fromDate, to_date: st.toDate,
  }, { jobId: 'job_d1' });
  assert.equal(C.adoptJobResult(st, ok), true);
  assert.equal(st.excelFile.path, 'D:/x/so.xlsx');
  assert.equal(st.downloadAppliedFor, 'job_d1');
  // Nguoi dung chon file khac, roi job cu den lai → khong ghi de.
  st.excelFile = { path: 'D:/x/picked.xlsx', scope: 'machine_local' };
  assert.equal(C.adoptJobResult(st, ok), false);
  assert.equal(st.excelFile.path, 'D:/x/picked.xlsx');
  // Download cua bo loc ngay cu → file ap nhung danh dau chua cap nhat.
  const st3 = S.createUploadState();
  st3.websiteId = 'nam_dinh';
  st3.downloadJobId = 'job_d3';
  st3.audit = { audit_id: 'aud_cu', summary: { excel_total: 1 } };
  const okLate = job('upload.download_export', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', browser_id: 'br1',
    file_ref: { path: 'D:/x/old.xlsx', scope: 'machine_local' },
    from_date: '2026-01-01', to_date: '2026-01-31',
  }, { jobId: 'job_d3' });
  assert.equal(C.adoptJobResult(st3, okLate), true);
  assert.equal(st3.auditStale, true);
  // Loi tai → downloadError rieng, khong dung vao auditError.
  const st2 = S.createUploadState();
  st2.websiteId = 'nam_dinh';
  st2.downloadJobId = 'job_d2';
  const bad = job('upload.download_export', 'failed', null, {
    jobId: 'job_d2',
    error: { code: 'login_required', message: 'chua dang nhap',
             retryable: true, next_action: 'login_required' },
  });
  assert.equal(C.adoptJobResult(st2, bad), true);
  assert.equal(st2.downloadError.code, 'login_required');
  assert.equal(st2.excelFile, null);
  assert.equal(st2.auditError, null);
});

test('adoptJobResult: loi select/session/confirm → siteError co retry hint', () => {
  // website_select bi tu choi → siteError + _retry tro ve website dich.
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.websiteJobId = 'job_w';
  st.pendingWebsiteId = 'khac';
  const bad = job('upload.website_select', 'failed', null, {
    jobId: 'job_w',
    error: { code: 'workflow_busy', message: 'con job dang chay',
             retryable: true, next_action: 'retry' },
  });
  assert.equal(C.adoptJobResult(st, bad), true);
  assert.equal(st.siteError.code, 'workflow_busy');
  assert.equal(st.siteError._retry.kind, 'website');
  assert.equal(st.siteError._retry.websiteId, 'khac');
  assert.equal(st.pendingWebsiteId, null);

  // session_start failed → siteError(_retry=session).
  const st2 = S.createUploadState();
  st2.websiteId = 'nam_dinh';
  st2.sessionJobId = 'job_s';
  const badS = job('upload.session_start', 'failed', null, {
    jobId: 'job_s',
    error: { code: 'engine_unavailable', message: 'khong mo duoc',
             retryable: true, next_action: 'retry' },
  });
  assert.equal(C.adoptJobResult(st2, badS), true);
  assert.equal(st2.siteError.code, 'engine_unavailable');
  assert.equal(st2.siteError._retry.kind, 'session');
  // session_start thanh cong → siteError sach + login ap.
  st2.sessionJobId = 'job_s2';
  const okS = job('upload.session_start', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', browser_id: 'br1',
    login: { status: 'authenticated' },
  }, { jobId: 'job_s2' });
  assert.equal(C.adoptJobResult(st2, okS), true);
  assert.equal(st2.siteError, null);
  assert.equal(st2.login.status, 'authenticated');
  assert.equal(st2.browserId, 'br1');

  // confirm_login sai job → siteError(_retry=confirm), login khong doi.
  st2.confirmJobId = 'job_c';
  const badC = job('upload.confirm_login', 'failed', null, {
    jobId: 'job_c',
    error: { code: 'wrong_job', message: 'job khong cho login',
             retryable: false, next_action: null },
  });
  assert.equal(C.adoptJobResult(st2, badC), true);
  assert.equal(st2.siteError.code, 'wrong_job');
  assert.equal(st2.siteError._retry.kind, 'confirm');
  assert.equal(st2.login.status, 'authenticated');
});

test('picker Excel chi quang ba .xlsx/.xlsm — .xls khong trong filter', () => {
  const src = read('upload/index.js');
  assert.match(src, /extensions:\s*\[\s*'xlsx'\s*,\s*'xlsm'\s*\]/,
    'filter pick Excel phai gom dung xlsx + xlsm');
  assert.ok(!/extensions:[^\]]*'xls'/.test(src),
    "'.xls' con trong filter — backend tu choi .xls");
});

test('view: nut Audit theo capability/dang nhap/busy; ngay DD/MM/YYYY; confirm dung luc cho', async () => {
  const { document } = makeDom();
  const U = loadModule(document);
  const L = require('../src/renderer/lib.js');
  const jobs = new Map();
  const view = U.buildView({
    api: fakeApi(), L, jobs, notify: () => {},
    entry: { id: 'upload', title: 'Upload Lab' },
    module: { id: 'upload', namespaces: ['upload'], status: 'available' },
    h: fakeHelpers(document, L),
    submit: async () => null,
  });
  view.refresh();
  const auditPanel = findById(view.el, 'ul-panel-audit');
  const btn = (t) => collect(auditPanel,
    (e) => e.tagName === 'BUTTON' && e.textContent === t)[0];
  const dl = btn('Tải Excel từ Web');
  const pick = btn('Chọn tệp Excel...');
  const load = btn('Nạp dữ liệu');
  const login = btn('Mở đăng nhập');
  const env = btn('Kiểm tra môi trường');
  const confirmB = collect(auditPanel,
    (e) => e.classList && e.classList.contains('ul-login-confirm'))[0];
  const dates = collect(auditPanel,
    (e) => e.classList && e.classList.contains('ul-date'));
  assert.equal(dates.length, 2);
  // Ngay nhap/hien DD/MM/YYYY (khong phai input type=date native).
  for (const d of dates) {
    assert.equal(d.type, 'text');
    assert.match(d.value, /^\d{2}\/\d{2}\/\d{4}$/,
      `o ngay phai hien DD/MM/YYYY, duoc '${d.value}'`);
  }

  // Chua co website → moi nut tac dong khoa.
  assert.equal(pick.disabled, true);
  assert.equal(dl.disabled, true);
  assert.equal(load.disabled, true);
  assert.equal(login.disabled, true);
  assert.equal(env.disabled, true);
  assert.equal(confirmB.hidden, true, 'confirm chi hien khi waiting login');

  // Catalog co fake voi day du capability → select/en check mo.
  jobs.set('cat', job('upload.websites', 'succeeded', {
    workflow_version: V,
    websites: [{ website_id: 'fake_portal', label: 'Gia lap',
                 display_url: 'http://127.0.0.1:9',
                 capabilities: ['login', 'download_export', 'audit_excel'],
                 status: 'available' }],
    selected_website_id: 'fake_portal',
  }, { jobId: 'cat', at: '2026-09-24T10:00:01Z' }));
  view.refresh();
  assert.equal(pick.disabled, false);
  assert.equal(env.disabled, false);
  assert.equal(login.disabled, false);
  assert.equal(dl.disabled, true, 'chua dang nhap → tai khoa');
  assert.equal(load.disabled, true, 'chua chon file → nap khoa');

  // Workspace dua browser_id + job ids → session_status adopt duoc
  // (scope browserId khop) va waiting job nam trong activeJobIds.
  jobs.set('ws', job('upload.workspace_get', 'succeeded', {
    workflow_version: V, website_id: 'fake_portal', revision: 1,
    run_id: null, audit_id: null, browser_id: 'br1', has_excel: false,
    queue_revision: null, needs_reconcile_record_ids: [],
    active_job_ids: ['job_sess'],
  }, { jobId: 'ws', at: '2026-09-24T10:00:02Z' }));
  // Dang nhap xong → tai mo; nap van khoa vi chua co file.
  jobs.set('ss', job('upload.session_status', 'succeeded', {
    workflow_version: V, website_id: 'fake_portal', browser_id: 'br1',
    login: { status: 'authenticated' },
  }, { jobId: 'ss', at: '2026-09-24T10:00:03Z' }));
  view.refresh();
  assert.equal(dl.disabled, false);
  assert.equal(login.disabled, true, 'da dang nhap → khong mo lai');
  assert.equal(load.disabled, true);

  // Waiting login → confirm hien va enable khi da co browser_id.
  const waiting = job('upload.session_start', 'waiting_user', null,
    { jobId: 'job_sess', at: '2026-09-24T10:00:04Z' });
  waiting.waiting_on = 'login';
  jobs.set('job_sess', waiting);
  // Job dang cho → website select khoa (busy), login khoa.
  view.refresh();
  assert.equal(confirmB.hidden, false, 'confirm phai hien luc cho login');
  assert.equal(confirmB.disabled, false);
  assert.equal(login.disabled, true, 'dang cho → khong mo phien khac');
});

test('view: audit head khop audit_id/website; KPI + bang tu state.audit', async () => {
  const { document } = makeDom();
  const U = loadModule(document);
  const L = require('../src/renderer/lib.js');
  const jobs = new Map();
  const view = U.buildView({
    api: fakeApi(), L, jobs, notify: () => {},
    entry: { id: 'upload', title: 'Upload Lab' },
    module: { id: 'upload', namespaces: ['upload'], status: 'available' },
    h: fakeHelpers(document, L),
    submit: async () => null,
  });
  jobs.set('cat', job('upload.websites', 'succeeded', {
    workflow_version: V,
    websites: [{ website_id: 'fake_portal', label: 'Gia lap',
                 display_url: 'http://127.0.0.1:9',
                 capabilities: ['audit_excel'], status: 'available' }],
    selected_website_id: 'fake_portal',
  }, { jobId: 'cat', at: '2026-09-24T10:00:01Z' }));
  jobs.set('ws', job('upload.workspace_get', 'succeeded', {
    workflow_version: V, website_id: 'fake_portal', revision: 1,
    run_id: null, audit_id: null, browser_id: null, has_excel: false,
    queue_revision: null, needs_reconcile_record_ids: [],
    active_job_ids: ['job_a'],
  }, { jobId: 'ws', at: '2026-09-24T10:00:01Z' }));
  jobs.set('job_a', job('upload.audit_excel', 'succeeded', {
    workflow_version: V, website_id: 'fake_portal', audit_id: 'aud_9',
    from_date: '2026-04-01', to_date: '2026-04-30',
    summary: { excel_total: 5, valid_count: 3, missing_count: 2,
               issue_count: 2, duplicate_count: 2 },
    missing: [
      { stt: 1, ngay: null, so_cong_chung: '103/2026', ghi_chu: 'Thieu that' },
      { stt: 2, ngay: null, so_cong_chung: '104/2026', ghi_chu: 'Co trong vung loi: trung_so' },
    ],
    issues: [
      { stt: 1, ngay: '2026-04-18', so_cong_chung: '104/2026', ghi_chu: 'trung_so: dup' },
      { stt: 2, ngay: '2026-04-18', so_cong_chung: '104/2026', ghi_chu: 'trung_so: dup' },
    ],
  }, { jobId: 'job_a', at: '2026-09-24T10:00:02Z' }));
  view.refresh();
  const auditPanel = findById(view.el, 'ul-panel-audit');
  const head = collect(auditPanel,
    (e) => e.classList && e.classList.contains('ul-audit-head'))[0];
  assert.ok(head && !head.hidden, 'audit head phai hien khi co ket qua');
  assert.match(head.textContent, /Gia lap/);
  assert.match(head.textContent, /fake_portal/);
  assert.match(head.textContent, /aud_9/);
  assert.match(head.textContent, /01\/04\/2026/);

  const kpis = {};
  for (const c of collect(auditPanel,
    (e) => e.dataset && e.dataset.kpi)) {
    kpis[c.dataset.kpi] = collect(c,
      (e) => e.classList && e.classList.contains('ul-kpi-v'))[0].textContent;
  }
  assert.deepEqual(kpis, { total: '5', valid: '3', missing: '2', issue: '2' });

  const tbodies = collect(auditPanel, (e) => e.tagName === 'TBODY');
  assert.equal(tbodies.length, 2);
  assert.equal(tbodies[0].children.length, 2, 'bang thieu 2 dong');
  assert.match(tbodies[0].children[0].textContent, /103\/2026/);
  assert.equal(tbodies[1].children.length, 2, 'bang loi 2 dong');
  assert.match(tbodies[1].children[0].textContent, /104\/2026/);
  // Ngay trong bang loi hien DD/MM/YYYY (isoToDisplay).
  assert.match(tbodies[1].children[0].textContent, /18\/04\/2026/);
});

test('view: loi nap hien tai cho voi huong dan; thanh cong xoa loi cu', async () => {
  const { document } = makeDom();
  const U = loadModule(document);
  const L = require('../src/renderer/lib.js');
  const jobs = new Map();
  const view = U.buildView({
    api: fakeApi(), L, jobs, notify: () => {},
    entry: { id: 'upload', title: 'Upload Lab' },
    module: { id: 'upload', namespaces: ['upload'], status: 'available' },
    h: fakeHelpers(document, L),
    submit: async () => null,
  });
  jobs.set('cat', job('upload.websites', 'succeeded', {
    workflow_version: V,
    websites: [{ website_id: 'fake_portal', label: 'Gia lap',
                 display_url: 'http://127.0.0.1:9',
                 capabilities: ['audit_excel'], status: 'available' }],
    selected_website_id: 'fake_portal',
  }, { jobId: 'cat', at: '2026-09-24T10:00:01Z' }));
  jobs.set('ws', job('upload.workspace_get', 'succeeded', {
    workflow_version: V, website_id: 'fake_portal', revision: 1,
    run_id: null, audit_id: null, browser_id: null, has_excel: false,
    queue_revision: null, needs_reconcile_record_ids: [],
    active_job_ids: ['job_af'],
  }, { jobId: 'ws', at: '2026-09-24T10:00:01Z' }));
  jobs.set('job_af', job('upload.audit_excel', 'failed', null, {
    jobId: 'job_af', at: '2026-09-24T10:00:02Z',
    error: { code: 'file_locked', message: 'file dang mo o Excel',
             retryable: true, next_action: 'retry' },
  }));
  view.refresh();
  const auditPanel = findById(view.el, 'ul-panel-audit');
  const srcMsg = collect(auditPanel,
    (e) => e.classList && e.classList.contains('ul-src-msg'))[0];
  assert.match(srcMsg.textContent, /file dang mo o Excel/);
  assert.match(srcMsg.textContent, /file_locked/);
  // KPI ve 0 — khong giu so lieu cu (spec §2).
  const total = collect(auditPanel,
    (e) => e.dataset && e.dataset.kpi === 'total')[0];
  assert.equal(collect(total,
    (e) => e.classList && e.classList.contains('ul-kpi-v'))[0].textContent,
    '0');
});

// ---------- task 7 fix1: review findings ----------

test('latestJob: cung updated_at → job chen SAU thang (pin >=)', () => {
  const jobs = new Map();
  jobs.set('a', { job_id: 'a', command: 'upload.websites',
                  status: 'succeeded', updated_at: '2026-09-24T10:00:00Z' });
  jobs.set('b', { job_id: 'b', command: 'upload.websites',
                  status: 'failed', updated_at: '2026-09-24T10:00:00Z' });
  jobs.set('c', { job_id: 'c', command: 'upload.scan',
                  status: 'succeeded', updated_at: '2026-09-24T11:00:00Z' });
  // updated_at chi co do phan giai giay — hai job cung giay hoa nhau; job
  // submit sau (vao map muon = y dinh moi hon) phai thang.
  assert.equal(C.latestJob(jobs, 'upload.websites').job_id, 'b');
  // Job co updated_at CU hon chen sau cung khong duoc thang.
  jobs.set('d', { job_id: 'd', command: 'upload.websites',
                  status: 'succeeded', updated_at: '2026-09-24T09:00:00Z' });
  assert.equal(C.latestJob(jobs, 'upload.websites').job_id, 'b');
  // Command khac khong lien quan; command khong co → null.
  assert.equal(C.latestJob(jobs, 'upload.scan').job_id, 'c');
  assert.equal(C.latestJob(jobs, 'upload.prepare'), null);
});

test('adoptJobResult: catalog rong van danh catalogLoaded (gate derive)', () => {
  const st = S.createUploadState();
  const j = job('upload.websites', 'succeeded', {
    workflow_version: V, websites: [], selected_website_id: null,
  }, { jobId: 'job_cat' });
  assert.equal(C.adoptJobResult(st, j), true);
  assert.equal(st.catalogLoaded, true,
    'catalog rong la ket qua hop le — derive khong duoc submit lai');
  assert.equal(st.websites.length, 0);
  assert.equal(st.workflowReady, true);
});

test('adoptJobResult: wsAppliedFor song sot setWebsite — khong ap lai', () => {
  const st = S.createUploadState();   // websiteId null → setWebsite path
  const j = job('upload.workspace_get', 'succeeded', {
    workflow_version: V, website_id: 'nam_dinh', revision: 3,
    run_id: 'r1', audit_id: null, browser_id: 'br1', has_excel: true,
    queue_revision: 2, needs_reconcile_record_ids: [], active_job_ids: [],
  }, { jobId: 'job_ws' });
  assert.equal(C.adoptJobResult(st, j), true);
  // Marker ghi SAU setWebsite → clearWebsiteScope (null→nam_dinh) khong
  // xoa duoc; snapshot ap dung mot lan.
  assert.equal(st.wsAppliedFor, 'job_ws');
  assert.equal(st.wsTried, true);
  assert.equal(st.runId, 'r1');
  assert.equal(st.browserId, 'br1');
  st.runId = 'run_khac';
  assert.equal(C.adoptJobResult(st, j), false,
    're-adopt cung job_id phai bi tu choi');
  assert.equal(st.runId, 'run_khac', 'snapshot cu khong duoc keo runId lui');
});

test('adoptJobResult: select tra website khac dich → mo pending + siteError',
  () => {
    const st = S.createUploadState();
    st.websiteId = 'nam_dinh';
    st.websiteJobId = 'job_w';
    st.pendingWebsiteId = 'khac';
    const j = job('upload.website_select', 'succeeded', {
      workflow_version: V, website_id: 'khac_hon', revision: 5,
      run_id: null, audit_id: null, browser_id: null, has_excel: false,
      queue_revision: null, needs_reconcile_record_ids: [],
      active_job_ids: [],
    }, { jobId: 'job_w' });
    assert.equal(C.adoptJobResult(st, j), true);
    assert.equal(st.pendingWebsiteId, null,
      'terminal mismatch phai mo khoa pending — neu khong dropdown ket');
    assert.equal(st.websiteId, 'nam_dinh', 'khong ap website khac dich');
    assert.equal(st.siteError.code, 'website_mismatch');
    assert.equal(st.siteError._retry.websiteId, 'khac');
  });

test('adoptJobResult: session_status theo login hieu luc — closed tat active',
  () => {
    const st = S.createUploadState();
    st.websiteId = 'nam_dinh';
    st.browserId = 'br1';
    st.uploadSessionActive = true;
    st.login = { status: 'authenticated', checked_at: '2026-09-24T10:00:00Z' };
    // Snapshot closed MOI hon → ap + tat active.
    const j = job('upload.session_status', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', browser_id: 'br1',
      login: { status: 'closed', checked_at: '2026-09-24T10:05:00Z' },
    });
    assert.equal(C.adoptJobResult(st, j), true);
    assert.equal(st.login.status, 'closed');
    assert.equal(st.uploadSessionActive, false);

    // Snapshot closed CU HON (regresses) → giu authenticated + active.
    const st2 = S.createUploadState();
    st2.websiteId = 'nam_dinh';
    st2.browserId = 'br1';
    st2.uploadSessionActive = true;
    st2.login = { status: 'authenticated',
                  checked_at: '2026-09-24T10:05:00Z' };
    const stale = job('upload.session_status', 'succeeded', {
      workflow_version: V, website_id: 'nam_dinh', browser_id: 'br1',
      login: { status: 'closed', checked_at: '2026-09-24T10:00:00Z' },
    });
    assert.equal(C.adoptJobResult(st2, stale), true);
    assert.equal(st2.login.status, 'authenticated');
    assert.equal(st2.uploadSessionActive, true,
      'snapshot closed cu khong duoc tat phien dang authenticated');
  });

test('derive: catalog khong resubmit nong — retry paced 4s + live-job guard',
  async (t) => {
    const { document } = makeDom();
    const U = loadModule(document);
    const L = require('../src/renderer/lib.js');
    const jobs = new Map();
    let submits = 0;
    const api = fakeApi();
    api.submitCommand = async (command) => {
      submits += 1;
      return { ok: true, data: {
        job_id: `job_${submits}`, command, status: 'accepted',
        result: null, error: null,
        updated_at: '2026-09-24T10:00:00Z' } };
    };
    const h = fakeHelpers(document, L);
    // awaitJob tra snapshot trong jobs map — job con 'accepted' (chua
    // terminal) tuc chua xong → done=false.
    h.awaitJob = async (jobId) => jobs.get(jobId);
    const view = U.buildView({
      api, L, jobs, notify: () => {},
      entry: { id: 'upload', title: 'Upload Lab' },
      module: { id: 'upload', namespaces: ['upload'], status: 'available' },
      h, submit: async () => null,
    });
    t.mock.timers.enable({ apis: ['setTimeout'] });
    const flush = () => new Promise((r) => setImmediate(r));

    view.refresh();
    await flush();
    assert.equal(submits, 1, 'lan dau submit catalog');
    view.refresh();
    view.refresh();
    await flush();
    assert.equal(submits, 1,
      'inflight + retry timer chua het → khong submit nong');
    // Het 4s → release → refresh; nhung job_1 VAN non-terminal → guard
    // liveJob chan resubmit chong (tranh pile-up job >30s).
    t.mock.timers.tick(4000);
    await flush();
    assert.equal(submits, 1,
      'job non-terminal con trong map → khong chong job moi');
    // Job terminal-failed → nhip derive sau moi duoc submit lai (retry
    // da paced, khong phai vong lap nong).
    jobs.get('job_1').status = 'failed';
    view.refresh();
    await flush();
    assert.equal(submits, 2, 'job terminal → retry submit lai mot lan');
  });

test('derive: engine_instance_id doi → catalogLoaded reset, refetch mot lan',
  async (t) => {
    const { document } = makeDom();
    const U = loadModule(document);
    const L = require('../src/renderer/lib.js');
    const jobs = new Map();
    let inst = 'inst_a';
    let submits = 0;
    const api = fakeApi();
    api.submitCommand = async (command) => {
      submits += 1;
      return { ok: true, data: {
        job_id: `job_${submits}`, command, status: 'accepted',
        result: null, error: null,
        updated_at: '2026-09-24T10:00:01Z' } };
    };
    // Catalog cu da load xong (ke ca rong).
    jobs.set('cat', job('upload.websites', 'succeeded', {
      workflow_version: V, websites: [], selected_website_id: null,
    }, { jobId: 'cat', at: '2026-09-24T10:00:00Z' }));
    const view = U.buildView({
      api, L, jobs, notify: () => {},
      entry: { id: 'upload', title: 'Upload Lab' },
      module: { id: 'upload', namespaces: ['upload'], status: 'available' },
      h: fakeHelpers(document, L), submit: async () => null,
      engineInstanceId: () => inst,
    });
    const flush = () => new Promise((r) => setImmediate(r));
    view.refresh();
    await flush();
    assert.equal(submits, 0, 'catalog da load → khong submit them');
    inst = 'inst_b';   // sidecar restart — instance moi
    view.refresh();
    await flush();
    assert.equal(submits, 1,
      'instance doi → catalog refetch dung mot lan');
    // Job moi con non-terminal → refresh tiep khong chong.
    view.refresh();
    await flush();
    assert.equal(submits, 1);
  });
