/* Renderer thuan UI — khong Node, khong fetch sidecar (CSP connect-src none).
   Moi tuong tac qua window.desktop.v1 (preload allowlist). */

const api = window.desktop.v1;
const view = document.getElementById('view');
const moduleList = document.getElementById('module-list');
let modules = [];
let activeModule = 'overview';
let pickedFiles = [];
const jobs = new Map();

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
              "'": '&#39;' }[c]));
}

function setStatus(s) {
  document.getElementById('engine-state').textContent = `engine: ${s.state}`;
  document.getElementById('engine-version').textContent =
    s.engine_version || '';
  document.getElementById('contract').textContent = s.contract_version || '';
}

async function refreshStatus() {
  const r = await api.getStatus();
  if (r.ok) setStatus(r.data);
}

function renderSidebar() {
  moduleList.innerHTML = '';
  // 'Tổng quan' la view shell co dinh — khong nam trong module registry (spec §6)
  const items = [{ id: 'overview', title: 'Tổng quan', status: 'available' },
                 ...modules];
  for (const m of items) {
    const li = document.createElement('li');
    li.textContent = m.title;
    li.dataset.id = m.id;
    if (m.status !== 'available') li.classList.add('unavailable');
    if (m.id === activeModule) li.classList.add('active');
    li.onclick = () => {
      if (m.status !== 'available') return;
      activeModule = m.id;
      renderSidebar();
      renderView();
    };
    moduleList.appendChild(li);
  }
}

function jobCard(job) {
  const e = job.error;
  return `<div class="job-card" data-job="${esc(job.job_id)}">
    <div><span class="status">${esc(job.status)}</span>
      <span class="muted"> ${esc(job.job_id)} · ${esc(job.command_id)}</span></div>
    ${job.waiting_on ? `<div>cho nguoi dung: <b>${esc(job.waiting_on)}</b></div>` : ''}
    ${job.progress ? `<div class="muted">${esc(job.progress.current_label)} — ${esc(job.progress.done)}/${esc(job.progress.total)}</div>` : ''}
    ${e ? `<div class="error">${esc(e.code)}: ${esc(e.message)}${e.retryable ? ' (retry duoc)' : ''}</div>` : ''}
    ${job.result ? `<pre>${esc(JSON.stringify(job.result, null, 2))}</pre>` : ''}
    ${!['succeeded', 'failed', 'canceled', 'partial'].includes(job.status)
      ? `<button data-cancel="${esc(job.job_id)}">Hủy</button>` : ''}
  </div>`;
}

function renderJobs() {
  const cards = [...jobs.values()].map(jobCard).join('');
  const el = document.getElementById('jobs');
  if (el) el.innerHTML = cards || '<div class="muted">Chưa có job.</div>';
  for (const btn of document.querySelectorAll('[data-cancel]')) {
    btn.onclick = () => api.cancelJob(btn.dataset.cancel);
  }
}

async function submit(command, payload, commandId) {
  // commandId on dinh cho cung mot hanh dong nguoi dung → retry khong
  // nhan doi side effect (idempotency, contract §5)
  const r = await api.submitCommand(command, payload, commandId);
  if (r.ok) {
    jobs.set(r.data.job_id, r.data);
    renderJobs();
  } else {
    alert(`${r.error.code}: ${r.error.message}`);
  }
}

function renderView() {
  if (activeModule === 'overview') {
    view.innerHTML = `<h2>Tổng quan</h2>
      <p class="muted">Kết nối loopback + engine Python qua desktopcommand.v1.</p>
      <div id="jobs"></div>`;
    renderJobs();
    return;
  }
  if (activeModule === 'upload' || activeModule === 'document-review') {
    view.innerHTML = `<h2>${esc(modules.find((m) => m.id === activeModule).title)}</h2>
      <p class="muted">P4 foundation: command read-only <code>file.inspect</code>
      goi engine that (docx/pdf/txt preview + sha256).</p>
      <button id="pick">Chọn file…</button>
      <button id="inspect" class="primary" disabled>Inspect</button>
      <button id="slow">Diag: slow task (cancel test)</button>
      <div id="files"></div>
      <div id="jobs"></div>`;
    document.getElementById('pick').onclick = async () => {
      const r = await api.pickFiles({ multi: true });
      if (r.ok) {
        pickedFiles = r.data.files;
        for (const f of pickedFiles) f._cmdId = crypto.randomUUID();
        document.getElementById('files').innerHTML = pickedFiles
          .map((f) => `<div class="file-row">${esc(f.path)}</div>`).join('');
        document.getElementById('inspect').disabled = pickedFiles.length === 0;
      }
    };
    document.getElementById('inspect').onclick = () => {
      for (const f of pickedFiles) {
        submit('file.inspect', { file: f }, f._cmdId);
      }
    };
    document.getElementById('slow').onclick = () =>
      submit('diag.slow_task', { steps: 20 });
    renderJobs();
    return;
  }
  if (activeModule === 'office') {
    view.innerHTML = '<h2>notaryoffice</h2><p>Chưa triển khai.</p>';
    return;
  }
  view.innerHTML = `<h2>${esc(activeModule)}</h2>
    <p class="muted">Shell module — noi dung o P5+.</p>`;
}

api.onJobUpdate((job) => {
  jobs.set(job.job_id, job);
  renderJobs();
});
api.onStatusUpdate(setStatus);

(async () => {
  const r = await api.getModules();
  if (r.ok) {
    modules = r.data.modules;
    setStatus(r.data.sidecar);
  }
  renderSidebar();
  renderView();
  setInterval(refreshStatus, 3000);
})();
