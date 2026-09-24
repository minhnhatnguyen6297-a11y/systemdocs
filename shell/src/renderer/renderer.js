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
let activeId = 'notary_v2';

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

// ---------- command client seam cho case-drafting model (MIN-111) ----------
// Model nhan client inject: run(command, payload) → cho job toi terminal,
// tra {ok:true,data}|{ok:false,error}. Runtime noi that o MIN-112; seam
// nay chay duoc ngay voi mock backend (G1_DEV_NOTARY_MOCK=1).
function makeCommandRunner() {
  return {
    async run(command, payload) {
      const job = await submit(command, payload, crypto.randomUUID());
      if (!job) {
        return { ok: false, error: { code: 'submit_failed',
          message: 'không gửi được command', retryable: true } };
      }
      const final = await awaitJob(job.job_id, 300000);
      if (!final) {
        return { ok: false, error: { code: 'engine_unavailable',
          message: 'job không phản hồi', retryable: true } };
      }
      if (final.status === 'succeeded' || final.status === 'partial') {
        return { ok: true, data: (final.result && final.result.data) || {},
                 partial: final.status === 'partial', job: final };
      }
      return { ok: false, job: final,
               error: final.error || { code: final.status,
                 message: `job ${final.status}`, retryable: false } };
    },
  };
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

function buildUploadView(entry, mod) {
  const s = el('section');
  s.append(el('h2', '', `${entry.title} (${mod ? mod.title : entry.id})`));
  const eng = el('div', 'slot');
  s.append(eng);
  s.append(el('div', 'muted',
    'Engine: upload_lab (Python). Dry-run mặc định — shell không tự ' +
    'Finalize, người dùng lưu trong Chromium.'));

  const ctx = { folder: null, excel: null, scanJobId: null, auditJobId: null,
                selected: new Set() };

  // --- Quet thu muc ---
  const scanSec = el('details', 'biz-sec');
  scanSec.open = true;
  scanSec.append(el('summary', '', 'Quét & trích xuất hồ sơ'));
  const folderRow = el('div', 'tools');
  const pickFolder = el('button', '', 'Chọn thư mục…');
  const scanBtn = el('button', 'primary', 'Quét');
  scanBtn.disabled = true;
  const folderLabel = el('span', 'muted', 'Chưa chọn thư mục');
  folderRow.append(pickFolder, scanBtn, folderLabel);
  scanSec.append(folderRow);
  const scanOut = el('div', 'slot');
  scanSec.append(scanOut);
  s.append(scanSec);

  pickFolder.onclick = async () => {
    const r = await api.pickFiles({ directory: true });
    if (!r.ok) { notify(`${r.error.code}: ${r.error.message}`, true); return; }
    if (!r.data.files.length) return;
    ctx.folder = r.data.files[0];
    folderLabel.textContent = ctx.folder.path;
    scanBtn.disabled = false;
  };
  scanBtn.onclick = async () => {
    ctx.scanJobId = crypto.randomUUID();
    const job = await submit('upload.scan',
      { folder: { path: ctx.folder.path, scope: 'machine_local' } },
      ctx.scanJobId);
    if (job) ctx.scanJobId = job.job_id;
  };

  function renderScan() {
    scanOut.innerHTML = '';
    const data = resultData(jobs, 'upload.scan');
    if (!data) {
      scanOut.append(faceEl(L.faceEmpty('Chưa có kết quả quét.')));
      return;
    }
    const stats = data.stats || {};
    scanOut.append(el('div', 'muted',
      `run ${data.run_id || '—'} · hỗ trợ ${stats.total_supported_files ?? '?'} · ` +
      `xử lý ${stats.processed_files ?? '?'} · lỗi ${stats.error_files ?? 0}`));
    const rows = data.records || [];
    const cols = [
      { key: 'record_id', label: 'ID' },
      { key: 'contract_no', label: 'Số công chứng' },
      { key: 'status', label: 'Trạng thái' },
      { key: 'reason', label: 'Ghi chú', fmt: (r) => r.reason || r.last_error || '' },
      { key: 'file_path', label: 'Địa chỉ file' },
    ];
    const t = tableEl(cols, rows);
    // Tick chon record cho prepare dry-run (status hop le).
    const theadRow = t.querySelector('thead tr');
    theadRow.prepend(el('th', '', '✓'));
    [...t.tBodies[0].rows].forEach((tr, i) => {
      const r = rows[i];
      const td = el('td');
      if (r && r.record_id != null) {
        const cb = el('input');
        cb.type = 'checkbox';
        cb.checked = ctx.selected.has(r.record_id);
        cb.onchange = () => {
          if (cb.checked) ctx.selected.add(r.record_id);
          else ctx.selected.delete(r.record_id);
        };
        td.append(cb);
      }
      tr.prepend(td);
    });
    scanOut.append(t);
  }

  // --- Audit so Excel ---
  const auditSec = el('details', 'biz-sec');
  auditSec.append(el('summary', '', 'Audit sổ công chứng (Excel)'));
  const auditRow = el('div', 'tools');
  const pickExcel = el('button', '', 'Chọn file Excel…');
  const excelLabel = el('span', 'muted', 'Chưa chọn file');
  const yr = new Date().getFullYear();
  const fromIn = inputEl('từ ngày', `${yr}-01-01`);
  const toIn = inputEl('đến ngày', `${yr}-12-31`);
  const auditBtn = el('button', 'primary', 'Audit');
  auditBtn.disabled = true;
  auditRow.append(pickExcel, excelLabel, fromIn, toIn, auditBtn);
  auditSec.append(auditRow);
  const auditOut = el('div', 'slot');
  auditSec.append(auditOut);
  s.append(auditSec);

  pickExcel.onclick = async () => {
    const r = await api.pickFiles({
      multi: false,
      filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }],
    });
    if (!r.ok) { notify(`${r.error.code}: ${r.error.message}`, true); return; }
    if (!r.data.files.length) return;
    ctx.excel = r.data.files[0];
    excelLabel.textContent = ctx.excel.path;
    auditBtn.disabled = false;
  };
  auditBtn.onclick = async () => {
    const job = await submit('upload.audit_excel', {
      file: { path: ctx.excel.path, scope: 'machine_local' },
      from_date: fromIn.value.trim(), to_date: toIn.value.trim(),
    }, crypto.randomUUID());
    if (job) ctx.auditJobId = job.job_id;
  };

  function renderAudit() {
    auditOut.innerHTML = '';
    const data = resultData(jobs, 'upload.audit_excel');
    if (!data) {
      auditOut.append(faceEl(L.faceEmpty('Chưa chạy audit.')));
      return;
    }
    // Cot chuan MIN-77: STT | Ngay | So cong chung | Ghi chu
    const cols = [
      { key: 'stt', label: 'STT' }, { key: 'ngay', label: 'Ngày' },
      { key: 'so_cong_chung', label: 'Số công chứng' },
      { key: 'ghi_chu', label: 'Ghi chú' },
    ];
    auditOut.append(el('h4', '', `Số thiếu (${(data.missing || []).length})`));
    auditOut.append(tableEl(cols, data.missing || []));
    auditOut.append(el('h4', '', `Vùng lỗi (${(data.issues || []).length})`));
    auditOut.append(tableEl(cols, data.issues || []));
  }

  // --- Phien upload Chromium ---
  const sessSec = el('details', 'biz-sec');
  sessSec.append(el('summary', '', 'Phiên upload (Chromium — đăng nhập tay)'));
  const sessRow = el('div', 'tools');
  const startBtn = el('button', '', 'Bắt đầu đăng nhập');
  const confirmBtn = el('button', 'primary', 'Xác nhận đã đăng nhập');
  const statusBtn = el('button', '', 'Trạng thái phiên');
  const prepBtn = el('button', '', 'Chuẩn bị upload (dry-run)');
  const finishBtn = el('button', '', 'Xong kiểm tra');
  const closeBtn = el('button', 'danger', 'Đóng phiên');
  sessRow.append(startBtn, confirmBtn, statusBtn, prepBtn, finishBtn, closeBtn);
  sessSec.append(sessRow);
  const sessOut = el('div', 'slot');
  sessSec.append(sessOut);
  s.append(sessSec);

  startBtn.onclick = () =>
    submit('upload.session_start', null, crypto.randomUUID());
  confirmBtn.onclick = () =>
    submit('upload.confirm_login', null, crypto.randomUUID());
  statusBtn.onclick = () =>
    submit('upload.session_status', null, crypto.randomUUID());
  closeBtn.onclick = () =>
    submit('upload.session_close', null, crypto.randomUUID());
  finishBtn.onclick = () =>
    submit('upload.finish_review', null, crypto.randomUUID());
  prepBtn.onclick = () => {
    if (!ctx.selected.size) {
      notify('Chưa tick record nào ở bảng quét — tick record để chuẩn bị.', true);
      return;
    }
    submit('upload.prepare', { record_ids: [...ctx.selected] },
      crypto.randomUUID());
  };

  function renderSession() {
    sessOut.innerHTML = '';
    const data = resultData(jobs, 'upload.session_status') ||
      resultData(jobs, 'upload.session_start');
    if (!data) {
      sessOut.append(faceEl(L.faceEmpty('Chưa có phiên. Chromium mở khi ' +
        'bấm "Bắt đầu đăng nhập".')));
      return;
    }
    sessOut.append(el('pre', '', JSON.stringify(data, null, 2)));
  }

  // --- Tools nen (inspect + diag giu nguyen) ---
  const toolsSec = el('details', 'biz-sec');
  toolsSec.append(el('summary', '', 'Công cụ nền (file.inspect / diag)'));
  const toolsRow = el('div', 'tools');
  const slowBtn = el('button', '', 'Chẩn đoán: tác vụ chậm');
  const waitBtn = el('button', '', 'Chẩn đoán: chờ người dùng');
  toolsRow.append(slowBtn, waitBtn);
  toolsSec.append(toolsRow);
  s.append(toolsSec);
  slowBtn.onclick = () =>
    submit('diag.slow_task', { steps: 20 }, crypto.randomUUID());
  waitBtn.onclick = () =>
    submit('diag.waiting_task', { wait_seconds: 30 }, crypto.randomUUID());

  s.append(el('h3', '', 'Job'));
  const jobsBox = el('div', 'slot');
  s.append(jobsBox);

  return {
    el: s,
    refresh() {
      eng.innerHTML = '';
      const slot = engineSlotEl();
      if (slot) eng.append(slot);
      renderScan(); renderAudit(); renderSession();
      renderJobs(jobsBox, mod);
    },
  };
}

// ---------- notary_v2 view — tab Soạn hồ sơ (MIN-111) ----------
// Local nav: Tổng quan hồ sơ / Soạn hồ sơ / Word (taxonomy spec §1).
// Chi Soạn hồ sơ co noi dung task nay; model giu state, view render tu
// model.state. Khong Zalo, khong input ID ky thuat trong production view.

function buildNotaryView(entry, mod) {
  const runner = makeCommandRunner();
  const model = window.G1_NOTARY_MODEL.createModel({ client: runner });
  const view = window.G1_NOTARY_VIEW.createNotaryModuleView({
    model,
    lib: L,
    notify,
    confirm: confirmModal,
    pickFiles: (opts) => api.pickFiles(opts),
    openPath: (p) => api.openPath(p),
    runCommand: runner.run.bind(runner),
  });
  const s = el('section', 'cd-root-outer');
  const eng = el('div', 'slot');
  s.append(eng);
  s.append(view.el);
  return {
    el: s,
    refresh() {
      eng.innerHTML = '';
      const slot = engineSlotEl();
      if (slot) eng.append(slot);
      view.refresh();
    },
    // Chan roi module khi con draft chua luu (spec UX §6).
    async canLeave() {
      if (!view.hasUnsaved()) return true;
      return confirmModal({
        title: 'Thay đổi chưa lưu',
        body: 'Stage/Sơ đồ còn bản nháp chưa lưu — rời màn hình sẽ giữ ' +
          'nháp trong phiên nhưng không ghi vào hồ sơ.',
        confirmLabel: 'Rời màn hình',
        cancelLabel: 'Ở lại',
      });
    },
  };
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

  // Suc khoe module + job (tru day 'Tổng quan' cu gop vao tien ich nay).
  s.append(el('h3', '', 'Module'));
  const health = el('div', 'slot');
  s.append(health);

  s.append(el('h3', '', 'Job'));
  const jobsBox = el('div', 'slot');
  s.append(jobsBox);

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
      health.innerHTML = ''; health.append(healthTableEl());
      renderJobs(jobsBox, null);
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
    case 'notary_v2': return buildNotaryView(entry, mod);
    case 'upload': return buildUploadView(entry, mod);
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

async function showModule(id) {
  const entry = L.navEntry(id);
  if (!entry) {
    // Nav ngoai allowlist bi tu choi (MIN-67 acceptance).
    notify(`Điều hướng bị từ chối: ${id}`, true);
    return;
  }
  const cur = views.get(activeId);
  if (cur) {
    // Chan roi module khi view con nhap chua luu (MIN-111 UX spec).
    if (entry.id !== activeId && cur.canLeave &&
        !(await cur.canLeave())) return;
    cur.scroll = view.scrollTop;
  }
  activeId = entry.id;
  let v = views.get(entry.id);
  if (!v) {
    v = buildView(entry);
    views.set(entry.id, v);
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
  showModule('notary_v2');
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
