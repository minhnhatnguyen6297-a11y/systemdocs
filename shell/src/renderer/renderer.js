/* Renderer — G1 shell navigation + trang thai dung chung (MIN-67, MIN-32).

   Nguyen tac:
   - Moi module view la mot DOM subtree PERSISTENT trong `views` — chuyen
     module khong huy form/file da chon/job dang xem/scroll (SM-07). Job
     chay o sidecar + tracker phia main; doi view khong cham vao job.
   - Chi goi window.desktop.v1 (preload allowlist). Khong Node, khong fetch
     sidecar (CSP connect-src 'none').
   - Moi hien thi trang thai qua descriptor cua lib.js (STATUS_LABEL,
     faces, WAITING_CTA) — khong tu suy luan vocabulary.
   - Nav allowlist = G1_LIB.NAV_SPEC; id ngoai danh sach bi tu choi.
*/

const api = window.desktop && window.desktop.v1;
const L = window.G1_LIB;

// Fail-visible: thieu bridge/lib thi bao loi ro thay vi man hinh trang.
if (!api || !L) {
  const v = document.getElementById('view');
  v.textContent = 'Lỗi khởi tạo shell: ' +
    (!api ? 'preload bridge (desktop.v1) không có. ' : '') +
    (!L ? 'display lib (G1_LIB) không có.' : '');
  throw new Error('renderer init failed: bridge/lib missing');
}

const view = document.getElementById('view');
const moduleList = document.getElementById('module-list');

let modules = [];
let modulesById = {};
let sidecarStatus = { state: 'starting' };
let activeId = 'overview';

const views = new Map();       // nav id -> {el, refresh(), scroll}
const jobs = new Map();        // job_id -> snapshot (desktopcommand.v1)
const jobPayloads = new Map(); // job_id -> {command, payload} cho retry that
const cancelPending = new Set();

// ---------- helpers ----------

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = text;
  return e;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function notify(text, isError) {
  let box = document.getElementById('toast');
  if (!box) {
    box = el('div', ''); box.id = 'toast';
    document.body.append(box);
  }
  const item = el('div', `toast-item${isError ? ' toast-error' : ''}`, text);
  box.append(item);
  setTimeout(() => item.remove(), 6000);
}

function setStatus(s) {
  document.getElementById('engine-state').textContent =
    `engine: ${L.engineStateLabel(s.state)}`;
  document.getElementById('engine-version').textContent =
    s.engine_version || '';
  document.getElementById('contract').textContent = s.contract_version || '';
}

// ---------- faces (MIN-32 §3) ----------

function faceEl(f, actions) {
  const box = el('div', `face face-${f.kind}`);
  box.append(el('div', 'face-title', f.title));
  if (f.detail) box.append(el('div', 'face-detail', f.detail));
  if (f.hint) box.append(el('div', 'face-hint muted', f.hint));
  if (actions) {
    const row = el('div', 'face-actions');
    for (const a of actions) row.append(a);
    box.append(row);
  }
  return box;
}

function errorFaceEl(err, onRetry) {
  const f = L.faceError(err);
  const box = faceEl(f);
  if (f.nextAction) {
    box.append(el('div', 'face-hint muted', `Gợi ý: ${f.nextAction}`));
  }
  const row = el('div', 'face-actions');
  if (f.retryable && onRetry) {
    const b = el('button', '', 'Thử lại');
    b.onclick = onRetry;
    row.append(b);
  }
  box.append(row);
  box.append(el('div', 'face-hint muted', f.diagnosticsHint));
  return box;
}

// ---------- modal confirm ----------

function confirmModal({ title, body, confirmLabel, cancelLabel }) {
  return new Promise((resolve) => {
    const wrap = el('div', 'modal-backdrop');
    const box = el('div', 'modal');
    box.append(el('div', 'modal-title', title));
    if (body) box.append(el('div', 'modal-body', body));
    const row = el('div', 'modal-actions');
    const cancel = el('button', '', cancelLabel || 'Quay lại');
    const ok = el('button', 'primary danger', confirmLabel || 'Xác nhận');
    const done = (v) => { wrap.remove(); resolve(v); };
    cancel.onclick = () => done(false);
    ok.onclick = () => done(true);
    wrap.onclick = (e) => { if (e.target === wrap) done(false); };
    row.append(cancel, ok);
    box.append(row);
    wrap.append(box);
    document.body.append(wrap);
    ok.focus();
  });
}

// ---------- jobs ----------

function breakdownEl(bd) {
  const box = el('div', 'breakdown muted');
  const ok = (bd.succeeded || []).length;
  const bad = (bd.failed || []).length;
  box.textContent = `Một phần: ${ok} thành công · ${bad} thất bại`;
  return box;
}

async function confirmCancel(d) {
  // Spec §4: cancel hien o accepted/running/waiting_user, co confirm neu
  // hau qua, va KHONG BAO GIO trigger Finalize.
  const yes = await confirmModal({
    title: 'Hủy job đang chạy?',
    body: `Job ${d.command} (${d.jobId}). Phần đã xử lý giữ nguyên ở draft; ` +
      'hủy không thực hiện bước Finalize nào.',
    confirmLabel: 'Hủy job',
  });
  if (!yes) return;
  if (cancelPending.has(d.jobId)) return;
  cancelPending.add(d.jobId);
  const r = await api.cancelJob(d.jobId);
  cancelPending.delete(d.jobId);
  if (!r.ok) notify(`${r.error.code}: ${r.error.message}`, true);
}

async function retryJob(jobId) {
  // Retry that su: command_id MOI (action moi), payload cu tu bookkeeping
  // renderer — khong bao gio reuse command_id cua job da terminal (se chi
  // tra job cu, khong chay lai — idempotency §5).
  const ctx = jobPayloads.get(jobId);
  if (!ctx) {
    notify('Không còn payload để chạy lại (shell đã tải lại) — chọn lại thao tác.', true);
    return;
  }
  await submit(ctx.command, ctx.payload, crypto.randomUUID());
}

function jobCardEl(job) {
  const d = L.jobDisplay(job);
  const card = el('div', 'job-card');
  const head = el('div', 'job-head');
  head.append(el('span', `badge tone-${d.tone}`, d.label));
  head.append(el('span', 'muted', ` ${d.command} · ${d.jobId}`));
  card.append(head);

  if (d.waiting) {
    const b = el('div', 'waiting-banner');
    b.append(el('strong', '', `Chờ người dùng (${d.waiting.on}): `));
    b.append(document.createTextNode(d.waiting.cta));
    card.append(b);
  }
  if (d.progressText) card.append(el('div', 'muted', d.progressText));
  if (d.error) {
    card.append(errorBlock(d.error,
      d.error.retryable ? () => retryJob(d.jobId) : null));
  }
  if (d.breakdown) card.append(breakdownEl(d.breakdown));
  if (d.resultJson) {
    const det = el('details', 'job-result');
    det.append(el('summary', '', 'Kết quả'));
    det.append(el('pre', '', d.resultJson));
    card.append(det);
  }
  if (d.cancelable) {
    const b = el('button', '', 'Hủy');
    b.onclick = () => confirmCancel(d);
    card.append(b);
  }
  return card;
}

function errorBlock(err, onRetry) {
  const box = el('div', 'job-error');
  box.append(el('div', 'error', `${err.code}: ${err.message}`));
  const meta = [];
  if (err.retryable) meta.push('có thể thử lại');
  if (err.next_action) meta.push(`gợi ý: ${err.next_action}`);
  if (meta.length) box.append(el('div', 'muted', meta.join(' · ')));
  if (onRetry) {
    const b = el('button', '', 'Thử lại');
    b.onclick = onRetry;
    box.append(b);
  }
  return box;
}

function jobsForModule(mod) {
  // Job khong gan module trong snapshot — loc theo command namespace.
  if (!mod || !mod.namespaces || !mod.namespaces.length) {
    return [...jobs.values()];
  }
  return [...jobs.values()].filter(
    (j) => mod.namespaces.includes(String(j.command || '').split('.')[0]));
}

function renderJobs(box, mod) {
  box.innerHTML = '';
  const list = jobsForModule(mod)
    .sort((a, b) => String(b.updated_at || '')
      .localeCompare(String(a.updated_at || '')));
  if (!list.length) {
    box.append(faceEl(L.faceEmpty('Chưa có job.')));
    return;
  }
  for (const j of list) box.append(jobCardEl(j));
}

async function submit(command, payload, commandId) {
  // commandId on dinh cho cung mot hanh dong nguoi dung → retry khong
  // nhan doi side effect (idempotency, contract §5).
  const r = await api.submitCommand(command, payload, commandId);
  if (!r.ok) {
    notify(`${r.error.code}: ${r.error.message}`, true);
    return null;
  }
  jobs.set(r.data.job_id, r.data);
  jobPayloads.set(r.data.job_id, { command, payload });
  refreshAll();
  return r.data;
}

// ---------- shared blocks ----------

function engineSlotEl() {
  // Banner engine trong module: loading khi starting/restarting,
  // unavailable khi stopped/unavailable (spec §3 — khong gia progress).
  const st = sidecarStatus.state || 'stopped';
  if (st === 'ready') return null;
  if (st === 'starting' || st === 'restarting') {
    return faceEl(L.faceLoading(`Engine ${L.engineStateLabel(st)}…`));
  }
  const retry = el('button', '', 'Thử lại kết nối');
  retry.onclick = async () => {
    const r = await api.restartEngine();
    if (!r.ok) notify(`${r.error.code}: ${r.error.message}`, true);
  };
  return faceEl(
    L.faceUnavailable('Engine',
      st === 'unavailable' ? 'engine_unavailable' : st,
      'Job không chạy được khi engine chưa sẵn sàng.'),
    [retry]);
}

function connCardEl() {
  const st = sidecarStatus || {};
  const card = el('div', 'conn-card');
  const grid = el('div', 'kv');
  const row = (k, v) => {
    grid.append(el('span', 'kv-k', k));
    grid.append(el('span', 'kv-v', v));
  };
  row('Kết nối', L.engineStateLabel(st.state));
  row('Engine', st.engine_version || '—');
  row('Contract', st.contract_version || '—');
  row('Instance', st.engine_instance_id || '—');
  row('Restart', String(st.restart_count ?? 0));
  card.append(grid);
  const slot = engineSlotEl();
  if (slot) card.append(slot);
  return card;
}

function healthTableEl() {
  const box = el('div', 'health-table');
  for (const h of L.moduleHealth(modules)) {
    const rowEl = el('div', 'health-row');
    rowEl.append(el('span', 'health-title', h.title));
    rowEl.append(el('span', 'muted', h.kind));
    const [tone, text] = h.face === 'ready'
      ? ['ok', 'sẵn sàng']
      : h.face === 'placeholder'
        ? ['muted', 'Chưa triển khai']
        : ['warn', h.reason || 'Không khả dụng'];
    rowEl.append(el('span', `badge tone-${tone}`, text));
    box.append(rowEl);
  }
  return box;
}

// ---------- module views ----------

function buildOverview() {
  const s = el('section');
  s.append(el('h2', '', 'Tổng quan'));
  const conn = el('div', 'slot');
  s.append(conn);
  s.append(el('h3', '', 'Module'));
  const health = el('div', 'slot');
  s.append(health);
  s.append(el('h3', '', 'Job'));
  const jobsBox = el('div', 'slot');
  s.append(jobsBox);
  return {
    el: s,
    refresh() {
      conn.innerHTML = ''; conn.append(connCardEl());
      health.innerHTML = ''; health.append(healthTableEl());
      renderJobs(jobsBox, null);
    },
  };
}

function buildEngineView(entry, mod) {
  const s = el('section');
  s.append(el('h2', '',
    `${entry.title} (${mod ? mod.title : entry.id})`));
  const eng = el('div', 'slot');
  s.append(eng);

  const tools = el('div', 'tools');
  const pickBtn = el('button', '', 'Chọn file…');
  const inspectBtn = el('button', 'primary', 'Inspect');
  inspectBtn.disabled = true;
  const slowBtn = el('button', '', 'Chẩn đoán: tác vụ chậm');
  const waitBtn = el('button', '', 'Chẩn đoán: chờ người dùng');
  tools.append(pickBtn, inspectBtn, slowBtn, waitBtn);
  s.append(tools);
  s.append(el('div', 'muted', 'Command read-only gọi engine thật ' +
    '(docx/pdf/txt preview + sha256). Business commands ở lát cắt sau.'));

  const filesBox = el('div', 'files');
  s.append(filesBox);
  s.append(el('h3', '', 'Job'));
  const jobsBox = el('div', 'slot');
  s.append(jobsBox);

  const ctx = { files: [] };

  function renderFiles() {
    filesBox.innerHTML = '';
    if (!ctx.files.length) {
      const b = el('button', '', 'Chọn file…');
      b.onclick = () => pickBtn.click();
      filesBox.append(faceEl(
        L.faceEmpty('Chưa chọn file nào.'), [b]));
      return;
    }
    for (const f of ctx.files) {
      filesBox.append(el('div', 'file-row', f.path));
    }
  }

  function refreshButtons() {
    const ready = sidecarStatus.state === 'ready';
    inspectBtn.disabled = ready ? ctx.files.length === 0 : true;
    slowBtn.disabled = !ready;
    waitBtn.disabled = !ready;
  }

  pickBtn.onclick = async () => {
    const r = await api.pickFiles({ multi: true });
    if (!r.ok) {
      filesBox.innerHTML = '';
      filesBox.append(errorFaceEl(r.error));
      return;
    }
    ctx.files = r.data.files;
    // command_id on dinh theo file: bam Inspect lai khong nhan doi job.
    for (const f of ctx.files) f._cmdId = crypto.randomUUID();
    renderFiles();
    refreshButtons();
  };
  inspectBtn.onclick = () => {
    for (const f of ctx.files) {
      submit('file.inspect',
        { file: { path: f.path, scope: f.scope } }, f._cmdId);
    }
  };
  slowBtn.onclick = () =>
    submit('diag.slow_task', { steps: 20 }, crypto.randomUUID());
  waitBtn.onclick = () =>
    submit('diag.waiting_task', { wait_seconds: 30 }, crypto.randomUUID());

  renderFiles();
  return {
    el: s,
    refresh() {
      eng.innerHTML = '';
      const slot = engineSlotEl();
      if (slot) eng.append(slot);
      refreshButtons();
      renderJobs(jobsBox, mod);
    },
  };
}

// ---------- business view helpers (MIN-68/69) ----------

function tableEl(columns, rows) {
  const t = el('table', 'tbl');
  const thead = el('thead');
  const tr = el('tr');
  for (const c of columns) tr.append(el('th', '', c.label));
  thead.append(tr);
  t.append(thead);
  const tb = el('tbody');
  if (!rows.length) {
    const r = el('tr');
    const td = el('td', 'muted', '—');
    td.colSpan = columns.length;
    r.append(td); tb.append(r);
  }
  for (const row of rows) {
    const r = el('tr');
    for (const c of columns) {
      const v = typeof c.fmt === 'function' ? c.fmt(row) : row[c.key];
      const td = el('td', '', (v === null || v === undefined || v === '') ? '—' : String(v));
      if (c.onClick) {
        td.classList.add('clk');
        td.onclick = () => c.onClick(row);
      }
      r.append(td);
    }
    tb.append(r);
  }
  t.append(tb);
  return t;
}

function inputEl(placeholder, value) {
  const i = el('input');
  i.placeholder = placeholder || '';
  if (value !== undefined) i.value = value;
  return i;
}

function formRow(labelText, ...controls) {
  const row = el('div', 'form-row');
  row.append(el('label', 'muted', labelText));
  for (const c of controls) row.append(c);
  return row;
}

async function awaitJob(jobId, timeoutMs = 120000) {
  // Cho job toi terminal hoac waiting_user — khong an state giua chung.
  let cur = jobs.get(jobId);
  const deadline = Date.now() + timeoutMs;
  while (cur && !L.isTerminal(cur.status) && Date.now() < deadline) {
    if (cur.status === 'waiting_user') return cur;
    await sleep(400);
    const g = await api.getJob(cur.job_id);
    if (g.ok) { cur = g.data; jobs.set(cur.job_id, cur); }
  }
  return cur;
}

function resultData(jobMapEntry, command) {
  // Result moi nhat (succeeded/partial) cua mot command — cho panel ket qua.
  const list = [...jobMapEntry.values()]
    .filter((j) => j.command === command &&
      ['succeeded', 'partial'].includes(j.status) && j.result)
    .sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')));
  return list.length ? list[0].result.data : null;
}

function openPathBtn(path, label) {
  const b = el('button', '', label || 'Mở file');
  b.onclick = async () => {
    const r = await api.openPath(path);
    if (!r.ok) notify(`${r.error.code}: ${r.error.message}`, true);
  };
  return b;
}

// ---------- upload_lab view (MIN-69) ----------
// View Upload Lab tach thanh module rieng: upload/{index,state,client,
// audit,scan-upload}.js + upload.css expose `window.G1_UPLOAD`. Renderer chi
// uy quyen va truyen dependency qua tham so — khong giu logic nghiep vu.

function buildUploadView(entry, mod) {
  const U = window.G1_UPLOAD;
  if (!U || typeof U.buildView !== 'function') {
    const s = el('section');
    s.append(el('h2', '', `${entry.title} (${mod ? mod.title : entry.id})`));
    s.append(faceEl(L.faceUnavailable(entry.title, 'module_script_missing')));
    return { el: s, refresh() {} };
  }
  return window.G1_UPLOAD.buildView({
    api, L, jobs, notify, entry, module: mod, submit,
    // Accessor (khong snapshot gia tri): upload view can biet instance
    // sidecar hien tai de refetch catalog sau restart (contract §5).
    engineInstanceId: () => sidecarStatus.engine_instance_id || null,
    h: { el, sleep, faceEl, errorFaceEl, tableEl, inputEl, formRow,
         engineSlotEl, renderJobs, resultData, openPathBtn, awaitJob,
         confirmModal },
  });
}

// ---------- notary_v2 view (MIN-68) ----------

function buildDocReviewView(entry, mod) {
  const s = el('section');
  s.append(el('h2', '', `${entry.title} (${mod ? mod.title : entry.id})`));
  const eng = el('div', 'slot');
  s.append(eng);
  s.append(el('div', 'muted',
    'Engine: notary_v2 @ codex/zalo-document-inbox-v2 — DB/Word/OCR/Zalo ' +
    'do Python so huu. Du lieu chua confirm khong thanh truth.'));

  const ctx = { caseId: null, images: [] };

  // --- Ho so thua ke ---
  const caseSec = el('details', 'biz-sec');
  caseSec.open = true;
  caseSec.append(el('summary', '', 'Hồ sơ thừa kế'));
  const caseRow = el('div', 'tools');
  const loadCases = el('button', 'primary', 'Tải danh sách');
  const caseQ = inputEl('lọc theo từ khóa');
  caseRow.append(loadCases, caseQ);
  caseSec.append(caseRow);
  const caseOut = el('div', 'slot');
  caseSec.append(caseOut);
  const detailOut = el('div', 'slot');
  caseSec.append(detailOut);
  s.append(caseSec);

  loadCases.onclick = () =>
    submit('notary.case_list', { query: caseQ.value.trim() },
      crypto.randomUUID());

  function caseDetailCard(d) {
    const card = el('div', 'kv-card');
    const kv = el('div', 'kv');
    const row = (k, v) => {
      kv.append(el('span', 'kv-k', k));
      kv.append(el('span', 'kv-v', v));
    };
    row('Hồ sơ', `#${d.id} — ${d.loai_van_ban} (${d.trang_thai})`);
    row('Người chết', d.nguoi_chet ? d.nguoi_chet.ho_ten : '—');
    row('Tài sản', d.tai_san
      ? `${d.tai_san.so_serial} — ${d.tai_san.dia_chi}` : '—');
    row('Ngày lập', d.ngay_lap_ho_so || '—');
    row('Nơi niêm yet', d.noi_niem_yet || '—');
    row('Tổng tỷ lệ', `${d.tong_ty_le ?? 0}%`);
    card.append(kv);
    if (d.participants && d.participants.length) {
      card.append(el('h4', '', `Đương sự (${d.participants.length})`));
      card.append(tableEl([
        { key: 'ho_ten', label: 'Họ tên',
          fmt: (p) => p.customer ? p.customer.ho_ten : '—' },
        { key: 'vai_tro', label: 'Vai trò' },
        { key: 'hang_thua_ke', label: 'Hàng' },
        { key: 'co_nhan_tai_san', label: 'Nhận TS',
          fmt: (p) => p.co_nhan_tai_san ? 'có' : 'từ chối' },
        { key: 'ty_le', label: 'Tỷ lệ %' },
      ], d.participants));
    }
    const btnRow = el('div', 'tools');
    const exportBtn = el('button', 'primary', 'Xuất Word');
    exportBtn.onclick = () => submit('notary.export_word',
      { case_id: d.id }, crypto.randomUUID());
    btnRow.append(exportBtn);
    const wd = resultData(jobs, 'notary.export_word');
    if (wd && wd.output_file) {
      btnRow.append(openPathBtn(wd.output_file.path,
        `Mở ${wd.output_file.path.split(/[\\/]/).pop()}`));
    }
    card.append(btnRow);
    return card;
  }

  function renderCases() {
    caseOut.innerHTML = '';
    detailOut.innerHTML = '';
    const data = resultData(jobs, 'notary.case_list');
    if (!data) {
      caseOut.append(faceEl(L.faceEmpty(
        'Chưa tải danh sách hồ sơ.'), [loadCases.cloneNode(true)]));
      caseOut.querySelector('button').onclick = loadCases.onclick;
      return;
    }
    const rows = data.cases || [];
    caseOut.append(tableEl([
      { key: 'id', label: 'ID' },
      { key: 'nguoi_chet', label: 'Người chết',
        fmt: (c) => c.nguoi_chet ? c.nguoi_chet.ho_ten : '—',
        onClick: (c) => selectCase(c.id) },
      { key: 'tai_san', label: 'Tài sản',
        fmt: (c) => c.tai_san ? c.tai_san.so_serial : '—',
        onClick: (c) => selectCase(c.id) },
      { key: 'ngay_lap_ho_so', label: 'Ngày lập',
        onClick: (c) => selectCase(c.id) },
      { key: 'trang_thai', label: 'TT',
        onClick: (c) => selectCase(c.id) },
    ], rows));
    const det = resultData(jobs, 'notary.case_get');
    if (det && ctx.caseId === det.id) detailOut.append(caseDetailCard(det));
    const wd = resultData(jobs, 'notary.export_word');
    if (wd && wd.output_file && det && ctx.caseId === det.id) {
      detailOut.append(el('div', 'muted',
        `Word: ${wd.output_file.path}`));
    }
  }

  async function selectCase(id) {
    ctx.caseId = id;
    await submit('notary.case_get', { case_id: id }, crypto.randomUUID());
  }

  // --- Tao du lieu (case/customer/property/participant) ---
  const createSec = el('details', 'biz-sec');
  createSec.append(el('summary', '', 'Tạo dữ liệu (ghi qua engine thật)'));

  const cForm = el('div');
  const cName = inputEl('họ tên *'), cCccd = inputEl('số giấy tờ (CCCD)'),
    cBirth = inputEl('ngày sinh'), cDeath = inputEl('ngày chết'),
    cAddr = inputEl('địa chỉ');
  const cBtn = el('button', '', 'Tạo khách hàng');
  cForm.append(formRow('Khách hàng', cName, cCccd, cBirth, cDeath, cAddr, cBtn));
  cBtn.onclick = () => submit('notary.customer_create', {
    ho_ten: cName.value.trim(), so_giay_to: cCccd.value.trim() || null,
    ngay_sinh: cBirth.value.trim() || null,
    ngay_chet: cDeath.value.trim() || null,
    dia_chi: cAddr.value.trim() || null,
  }, crypto.randomUUID());
  createSec.append(cForm);

  const pForm = el('div');
  const pSerial = inputEl('số serial GCN *'), pAddr = inputEl('địa chỉ *'),
    pThua = inputEl('thửa'), pTo = inputEl('tờ bản đồ'),
    pLoai = inputEl('loại sổ');
  const pBtn = el('button', '', 'Tạo tài sản');
  pForm.append(formRow('Tài sản', pSerial, pAddr, pThua, pTo, pLoai, pBtn));
  pBtn.onclick = () => submit('notary.property_create', {
    so_serial: pSerial.value.trim(), dia_chi: pAddr.value.trim(),
    so_thua_dat: pThua.value.trim() || null,
    so_to_ban_do: pTo.value.trim() || null,
    loai_so: pLoai.value.trim() || null,
  }, crypto.randomUUID());
  createSec.append(pForm);

  const kForm = el('div');
  const kNguoi = inputEl('id người chết *'), kTs = inputEl('id tài sản *'),
    kNgay = inputEl('ngày lập yyyy-mm-dd'),
    kNoi = inputEl('nơi niêm yết');
  const kLoai = el('select');
  for (const [v, t] of [['khai_nhan', 'Khai nhận di sản'],
                        ['thoa_thuan', 'Thỏa thuận phân chia']]) {
    const o = el('option', '', t); o.value = v; kLoai.append(o);
  }
  const kBtn = el('button', '', 'Tạo hồ sơ');
  kForm.append(formRow('Hồ sơ', kNguoi, kTs, kLoai, kNgay, kNoi, kBtn));
  kBtn.onclick = () => submit('notary.case_create', {
    nguoi_chet_id: kNguoi.value.trim(), tai_san_id: kTs.value.trim(),
    loai_van_ban: kLoai.value,
    ngay_lap_ho_so: kNgay.value.trim() || null,
    noi_niem_yet: kNoi.value.trim() || null,
  }, crypto.randomUUID());
  createSec.append(kForm);

  const ptForm = el('div');
  const ptCase = inputEl('id hồ sơ *'), ptCust = inputEl('id khách hàng *'),
    ptRole = inputEl('vai trò *'), ptHang = inputEl('hàng (1)'),
    ptTyLe = inputEl('tỷ lệ %');
  const ptBtn = el('button', '', 'Thêm đương sự');
  ptForm.append(formRow('Đương sự', ptCase, ptCust, ptRole, ptHang, ptTyLe, ptBtn));
  ptBtn.onclick = () => submit('notary.participant_add', {
    case_id: ptCase.value.trim(), customer_id: ptCust.value.trim(),
    vai_tro: ptRole.value.trim(),
    hang_thua_ke: ptHang.value.trim() || 1,
    ty_le: ptTyLe.value.trim() || 0, co_nhan_tai_san: true,
  }, crypto.randomUUID());
  createSec.append(ptForm);
  s.append(createSec);

  // --- Khach hang / tai san list ---
  const listSec = el('details', 'biz-sec');
  listSec.append(el('summary', '', 'Khách hàng & Tài sản'));
  const listRow = el('div', 'tools');
  const loadCust = el('button', '', 'Tải khách hàng');
  const loadProp = el('button', '', 'Tải tài sản');
  listRow.append(loadCust, loadProp);
  listSec.append(listRow);
  const listOut = el('div', 'slot');
  listSec.append(listOut);
  s.append(listSec);

  loadCust.onclick = () =>
    submit('notary.customer_list', null, crypto.randomUUID());
  loadProp.onclick = () =>
    submit('notary.property_list', null, crypto.randomUUID());

  function renderLists() {
    listOut.innerHTML = '';
    const cust = resultData(jobs, 'notary.customer_list');
    if (cust) {
      listOut.append(el('h4', '', `Khách hàng (${cust.total})`));
      listOut.append(tableEl([
        { key: 'id', label: 'ID' }, { key: 'ho_ten', label: 'Họ tên' },
        { key: 'so_giay_to', label: 'Giấy tờ' },
        { key: 'ngay_sinh', label: 'Ngày sinh' },
        { key: 'ngay_chet', label: 'Ngày chết' },
        { key: 'dia_chi', label: 'Địa chỉ' },
      ], cust.customers || []));
    }
    const prop = resultData(jobs, 'notary.property_list');
    if (prop) {
      listOut.append(el('h4', '', `Tài sản (${prop.total})`));
      listOut.append(tableEl([
        { key: 'id', label: 'ID' }, { key: 'so_serial', label: 'Serial GCN' },
        { key: 'so_thua_dat', label: 'Thửa' },
        { key: 'so_to_ban_do', label: 'Tờ' },
        { key: 'dia_chi', label: 'Địa chỉ' },
        { key: 'dien_tich', label: 'Diện tích' },
      ], prop.properties || []));
    }
    if (!cust && !prop) {
      listOut.append(faceEl(L.faceEmpty('Chưa tải dữ liệu.')));
    }
  }

  // --- OCR intake ---
  const ocrSec = el('details', 'biz-sec');
  ocrSec.append(el('summary', '', 'OCR giấy tờ (cloud Qwen — kết quả observed)'));
  const ocrRow = el('div', 'tools');
  const pickImg = el('button', '', 'Chọn ảnh…');
  const ocrBtn = el('button', 'primary', 'OCR');
  ocrBtn.disabled = true;
  const imgLabel = el('span', 'muted', 'Chưa chọn ảnh');
  ocrRow.append(pickImg, ocrBtn, imgLabel);
  ocrSec.append(ocrRow);
  const ocrOut = el('div', 'slot');
  ocrSec.append(ocrOut);
  s.append(ocrSec);

  pickImg.onclick = async () => {
    const r = await api.pickFiles({
      multi: true,
      filters: [{ name: 'Ảnh giấy tờ', extensions: ['jpg', 'jpeg', 'png'] }],
    });
    if (!r.ok) { notify(`${r.error.code}: ${r.error.message}`, true); return; }
    ctx.images = r.data.files;
    imgLabel.textContent = `${ctx.images.length} ảnh`;
    ocrBtn.disabled = !ctx.images.length;
  };
  ocrBtn.onclick = () => submit('ocr.analyze', {
    files: ctx.images.map((f) => ({ path: f.path, scope: f.scope })),
  }, crypto.randomUUID());

  function renderOcr() {
    ocrOut.innerHTML = '';
    const data = resultData(jobs, 'ocr.analyze');
    if (!data) {
      ocrOut.append(faceEl(L.faceEmpty(
        'Chưa chạy OCR. Kết quả luôn là observed — cần người confirm.')));
      return;
    }
    const sm = data.summary || {};
    ocrOut.append(el('div', 'muted',
      `model ${data.model || sm.model || '—'} · ${sm.total_images ?? '?'} ảnh · ` +
      `${(data.persons || []).length} người · ${(data.properties || []).length} tài sản` +
      (sm.total_ms ? ` · ${Math.round(sm.total_ms)}ms` : '')));
    if ((data.persons || []).length) {
      ocrOut.append(tableEl([
        { key: 'ho_ten', label: 'Họ tên' },
        { key: 'so_giay_to', label: 'Giấy tờ', fmt: (p) => p.so_giay_to || p.id12 || '—' },
        { key: 'ngay_sinh', label: 'Ngày sinh' },
        { key: 'dia_chi', label: 'Địa chỉ' },
      ], data.persons));
    }
    if ((data.properties || []).length) {
      ocrOut.append(tableEl([
        { key: 'so_serial', label: 'Serial' },
        { key: 'dia_chi', label: 'Địa chỉ' },
      ], data.properties));
    }
    if ((data.errors || []).length) {
      ocrOut.append(el('pre', '', JSON.stringify(data.errors, null, 2)));
    }
    ocrOut.append(el('div', 'muted warn-text',
      'observed — chưa confirm, chưa ghi vào hồ sơ.'));
  }

  // --- Zalo ---
  const zaloSec = el('details', 'biz-sec');
  zaloSec.append(el('summary', '', 'Zalo Inbox (tài khoản văn phòng)'));
  const zaloRow = el('div', 'tools');
  const zaloBtn = el('button', '', 'Tải trạng thái');
  zaloRow.append(zaloBtn);
  zaloSec.append(zaloRow);
  const zaloOut = el('div', 'slot');
  zaloSec.append(zaloOut);
  s.append(zaloSec);

  zaloBtn.onclick = () => submit('zalo.status', null, crypto.randomUUID());

  function renderZalo() {
    zaloOut.innerHTML = '';
    const data = resultData(jobs, 'zalo.status');
    if (!data) {
      zaloOut.append(faceEl(L.faceEmpty(
        'Chưa tải. Connector Node zca-js chạy riêng trên server.')));
      return;
    }
    const t = data.totals || {};
    zaloOut.append(el('div', 'muted',
      `${t.accounts ?? 0} tài khoản · ${t.sources ?? 0} nguồn · ` +
      `${t.media ?? 0} media · ${t.message_texts ?? 0} text`));
    if ((data.accounts || []).length) {
      zaloOut.append(tableEl([
        { key: 'bound_zalo_id', label: 'Zalo ID' },
        { key: 'session_state', label: 'Session' },
        { key: 'connector_state', label: 'Connector' },
        { key: 'last_seen_at', label: 'Last seen' },
      ], data.accounts));
    }
  }

  s.append(el('h3', '', 'Job'));
  const jobsBox = el('div', 'slot');
  s.append(jobsBox);

  return {
    el: s,
    refresh() {
      eng.innerHTML = '';
      const slot = engineSlotEl();
      if (slot) eng.append(slot);
      renderCases(); renderLists(); renderOcr(); renderZalo();
      renderJobs(jobsBox, mod);
    },
  };
}

function buildExcelWord(entry) {
  const s = el('section');
  s.append(el('h2', '', entry.title));
  s.append(faceEl(L.faceEmpty(
    'Module Excel → Word chưa có luồng nào trong G1.2 — ' +
    'chuyển đổi ở lát cắt sau (MIN-68).')));
  return { el: s, refresh() {} };
}

function buildOffice(entry) {
  const s = el('section');
  s.append(el('h2', '', entry.title));
  s.append(faceEl({
    kind: 'unavailable',
    title: 'notaryoffice — Chưa triển khai',
    detail: 'Module dự kiến sau G1. Không có dữ liệu giả.',
    hint: null,
  }));
  return { el: s, refresh() {} };
}

function buildSearch(entry) {
  const s = el('section');
  s.append(el('h2', '', entry.title));
  s.append(faceEl(L.faceEmpty(
    'Tìm kiếm dùng chung sẽ khả dụng khi model dữ liệu chung ổn định ' +
    '(sau G1). Chưa có nguồn dữ liệu để tìm.')));
  return { el: s, refresh() {} };
}

function buildStatus(entry) {
  const s = el('section');
  s.append(el('h2', '', entry.title));

  s.append(el('h3', '', 'Kết nối & phiên bản'));
  const conn = el('div', 'slot');
  s.append(conn);

  s.append(el('h3', '', 'Môi trường engine'));
  const envBox = el('div', 'slot');
  s.append(envBox);
  const envBtn = el('button', '', 'Kiểm tra môi trường');
  envBtn.onclick = () => runEnvCheck(envBox, envBtn);
  s.append(envBtn);

  s.append(el('h3', '', 'Diagnostics'));
  const diagBox = el('div', 'slot');
  s.append(diagBox);
  const diagBtn = el('button', '', 'Tải diagnostics');
  diagBtn.onclick = () => loadDiagnostics(diagBox, diagBtn);
  s.append(diagBtn);

  s.append(el('h3', '', 'Cài đặt'));
  s.append(el('div', 'muted',
    'G1-SM: light theme; cấu hình server/LAN sẽ có ở G1.5. ' +
    'Dữ liệu app nằm ngoài thư mục cài đặt (%APPDATA%/g1-shell).'));

  return {
    el: s,
    refresh() {
      conn.innerHTML = ''; conn.append(connCardEl());
      // giu disabled khi mot env check dang chay (job update goi refresh)
      envBtn.disabled = envBtn._busy ||
        sidecarStatus.state !== 'ready';
    },
  };
}

async function runEnvCheck(box, btn) {
  btn.disabled = true;
  btn._busy = true;
  box.innerHTML = '';
  box.append(faceEl(L.faceLoading('Đang kiểm tra môi trường engine…')));
  const job = await submit('diag.env_check', null, crypto.randomUUID());
  if (!job) { btn.disabled = false; btn._busy = false; return; }
  let cur = job;
  const deadline = Date.now() + 30_000;
  while (!L.isTerminal(cur.status) && Date.now() < deadline) {
    await sleep(600);
    const g = await api.getJob(cur.job_id);
    if (!g.ok) break;
    cur = g.data;
  }
  box.innerHTML = '';
  btn.disabled = false;
  btn._busy = false;
  if (cur.status === 'succeeded' || cur.status === 'partial') {
    const d = cur.result && cur.result.data || {};
    const list = el('div', 'kv');
    for (const c of d.checks || []) {
      list.append(el('span', 'kv-k', c.name));
      list.append(el('span', `kv-v ${c.ok ? '' : 'error'}`,
        `${c.ok ? 'OK' : 'THIẾU'} — ${c.detail}`));
    }
    box.append(list);
    for (const w of cur.result.warnings || []) {
      box.append(el('div', 'muted', `cảnh báo: ${w.code} — ${w.message}`));
    }
  } else {
    box.append(errorFaceEl(cur.error || { code: cur.status }));
  }
}

async function loadDiagnostics(box, btn) {
  btn.disabled = true;
  box.innerHTML = '';
  box.append(faceEl(L.faceLoading('Đang đọc diagnostics…')));
  const r = await api.getDiagnostics();
  box.innerHTML = '';
  btn.disabled = false;
  if (!r.ok) {
    box.append(errorFaceEl(r.error));
    return;
  }
  const d = r.data;
  const kv = el('div', 'kv');
  const row = (k, v) => {
    kv.append(el('span', 'kv-k', k)); kv.append(el('span', 'kv-v', v));
  };
  row('Shell', d.shell_version || '—');
  row('Engine', (d.sidecar && d.sidecar.engine_version) || '—');
  row('Contract', (d.sidecar && d.sidecar.contract_version) || '—');
  row('User data', d.user_data || '—');
  row('Log', d.log_path || '—');
  box.append(kv);
  box.append(el('div', 'muted',
    'Log đã redact — credential/cookie/token không hiển thị.'));
  const det = el('details', 'job-result');
  det.append(el('summary', '', 'main.log (40 dòng cuối)'));
  det.append(el('pre', '', (d.log_tail || []).join('\n') || '(trống)'));
  box.append(det);
}

function buildView(entry) {
  const mod = entry.registry ? modulesById[entry.registry] : null;
  switch (entry.id) {
    case 'overview': return buildOverview();
    case 'upload': return buildUploadView(entry, mod);
    case 'document-review': return buildDocReviewView(entry, mod);
    case 'excel-word': return buildExcelWord(entry);
    case 'office': return buildOffice(entry);
    case 'search': return buildSearch(entry);
    case 'status': return buildStatus(entry);
    default: {
      const s = el('section');
      s.append(faceEl(L.faceUnavailable(entry.title, 'no_view')));
      return { el: s, refresh() {} };
    }
  }
}

// ---------- navigation ----------

function showModule(id) {
  const entry = L.navEntry(id);
  if (!entry) {
    // Nav ngoai allowlist bi tu choi (MIN-67 acceptance).
    notify(`Điều hướng bị từ chối: ${id}`, true);
    return;
  }
  const cur = views.get(activeId);
  if (cur) cur.scroll = view.scrollTop;
  activeId = id;
  let v = views.get(id);
  if (!v) {
    v = buildView(entry);
    views.set(id, v);
  }
  view.innerHTML = '';
  view.append(v.el);
  view.scrollTop = v.scroll || 0;
  v.refresh();
  renderSidebar();
}

function renderSidebar() {
  moduleList.innerHTML = '';
  for (const n of L.NAV_SPEC) {
    const mod = n.registry ? modulesById[n.registry] : null;
    const face = n.registry ? L.moduleFace(mod) : 'ready';
    const li = el('li', '', n.title);
    li.dataset.id = n.id;
    // Placeholder/unavailable van hien thi va mo duoc (spec §1 — khong an).
    if (face !== 'ready') li.classList.add('unavailable');
    if (n.id === activeId) li.classList.add('active');
    li.onclick = () => showModule(n.id);
    moduleList.append(li);
  }
}

function refreshAll() {
  for (const v of views.values()) v.refresh();
  renderSidebar();
}

// ---------- events ----------

api.onJobUpdate((job) => {
  jobs.set(job.job_id, job);
  for (const v of views.values()) v.refresh();
});
api.onStatusUpdate((s) => {
  sidecarStatus = s;
  setStatus(s);
  refreshAll();
});

// ---------- init ----------

(async () => {
  const [mods, st, lj] = await Promise.all([
    api.getModules(), api.getStatus(), api.listJobs()]);
  if (mods.ok) {
    modules = mods.data.modules;
    modulesById = Object.fromEntries(modules.map((m) => [m.id, m]));
    sidecarStatus = mods.data.sidecar || sidecarStatus;
  }
  if (st.ok) sidecarStatus = st.data;
  setStatus(sidecarStatus);
  if (lj.ok) {
    // Noi lai job sau renderer reload — sidecar/tracker van giu (contract §5).
    for (const j of lj.data.jobs) jobs.set(j.job_id, j);
  }
  renderSidebar();
  showModule('overview');
  setInterval(async () => {
    const r = await api.getStatus();
    if (r.ok) {
      const changed = r.data.state !== sidecarStatus.state ||
        r.data.engine_instance_id !== sidecarStatus.engine_instance_id;
      sidecarStatus = r.data;
      setStatus(r.data);
      if (changed) refreshAll();
    }
  }, 3000);
})();
