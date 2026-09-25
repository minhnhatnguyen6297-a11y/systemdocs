'use strict';

// G1 shell — Electron main entry (desktopcommand.v1 consumer).
// Security: renderer sandbox + contextIsolation + no nodeIntegration;
// sidecar token/port chi trong main; preload expose IPC allowlist versioned.

const path = require('path');
const fs = require('fs');
const { app, BrowserWindow, dialog, ipcMain } = require('electron');

const { sidecarCommand, SHELL_VERSION } = require('./config');
const { makeLogger, redactString } = require('./redact');
const { SidecarManager } = require('./sidecar');
const { JobTracker } = require('./job-tracker');
const { registerIpc } = require('./ipc');

const SHELL_ROOT = path.join(__dirname, '..', '..');
const SMOKE = process.env.G1_SMOKE === '1'; // packaged smoke: chay probe roi thoat

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}

let win = null;
let sidecar = null;
let tracker = null;
let log = makeLogger();
let logPath = null;
let allowClose = false;

// Duong mo file an toan — chi nhung loai tai lieu renderer can mo.
const OPEN_ALLOWED_EXTS = new Set([
  '.doc', '.docx', '.xls', '.xlsx', '.xlsm', '.pdf',
  '.txt', '.log', '.md', '.json', '.csv',
]);

// Test seam (MIN-69 e2e): G1_E2E_PICK_FILES chi vao file JSON
// {"files": ["D:/path/a.xlsx", ...]} — thay dialog that, chi hoat dong
// khi env duoc dat. Ket qua van qua cung filter/validate nhu dialog.
function e2ePickOverride(opts) {
  // Master guard: ban packaged KHONG BAO GIO stub file dialog — env
  // G1_E2E_PICK_FILES con sot tren may user khong duoc bien moi picker
  // thanh doc file JSON.
  if (app.isPackaged) return null;
  const spec = process.env.G1_E2E_PICK_FILES;
  if (!spec) return null;
  let list;
  try {
    const raw = JSON.parse(fs.readFileSync(spec, 'utf8'));
    list = Array.isArray(raw) ? raw : (raw && raw.files) || [];
  } catch (e) {
    log.warn('G1_E2E_PICK_FILES khong doc duoc', { err: String(e) });
    return [];
  }
  // Ap filter extension nhu dialog that — file ngoai filter "khong chon
  // duoc" (khong tra ve).
  const allowed = [];
  if (!opts.directory && Array.isArray(opts.filters)) {
    for (const f of opts.filters) {
      for (const ext of (f && f.extensions) || []) {
        allowed.push(String(ext).toLowerCase());
      }
    }
  }
  const out = [];
  for (const item of list) {
    const p = typeof item === 'string' ? item : (item && item.path);
    if (typeof p !== 'string' || !p) continue;
    if (allowed.length &&
        !allowed.includes(path.extname(p).slice(1).toLowerCase())) {
      continue;
    }
    try {
      const st = fs.statSync(p);
      out.push({
        path: p, scope: 'machine_local',
        size_bytes: st.isFile() ? st.size : null,
        is_dir: st.isDirectory(),
      });
    } catch (e) { /* bo qua path khong ton tai */ }
  }
  return out;
}

async function pickFiles(opts = {}) {
  const stub = e2ePickOverride(opts);
  if (stub !== null) return stub;
  const properties = opts.directory
    ? ['openDirectory']
    : opts.multi === false ? ['openFile'] : ['openFile', 'multiSelections'];
  const res = await dialog.showOpenDialog(win, { properties, filters: opts.filters });
  if (res.canceled) return [];
  // file_ref machine_local theo contract §6 — path tuyet doi tu native dialog
  return res.filePaths.map((p) => {
    const st = fs.statSync(p);
    return {
      path: p,
      scope: 'machine_local',
      size_bytes: st.isFile() ? st.size : null,
      is_dir: st.isDirectory(),
    };
  });
}

async function openPath(opts = {}) {
  // Mo file san pham (docx da export, log, ...) bang app mac dinh.
  // Validate boundary: scope machine_local, tuyet doi, ton tai, khong UNC,
  // phan mo rong nam trong allowlist — file_ref §6.
  if (opts.scope !== undefined && opts.scope !== 'machine_local') {
    throw Object.assign(
      new Error(`scope ${opts.scope} khong duoc mo`),
      { code: 'file_scope_not_supported' });
  }
  const p = typeof opts.path === 'string' ? opts.path : '';
  const unc = p.startsWith('\\\\') ||
    /^\\\\\?\\(UNC\\|\\\\)/i.test(p);
  if (!p || unc || !/^[A-Za-z]:[\\/]/.test(p) && !p.startsWith('\\\\?\\')) {
    throw Object.assign(new Error('path khong hop le'),
      { code: 'file_scope_not_supported' });
  }
  const ext = path.extname(p).toLowerCase();
  if (!OPEN_ALLOWED_EXTS.has(ext)) {
    throw Object.assign(
      new Error(`khong mo loai file ${ext || '(khong phan mo rong)'}`),
      { code: 'file_scope_not_supported' });
  }
  if (!fs.existsSync(p) || !fs.statSync(p).isFile()) {
    throw Object.assign(new Error('file khong ton tai'),
      { code: 'file_not_found' });
  }
  // Test seam (MIN-69 e2e): G1_E2E_OPEN_LOG chi vao file text — moi lan
  // openPath hop le ghi mot dong path thay vi mo app that (tran dep Word
  // trong test). Cung guard nhu pick seam: packaged khong bao gio stub.
  const openLog = !app.isPackaged && process.env.G1_E2E_OPEN_LOG;
  if (openLog) {
    fs.appendFileSync(openLog, `${p}\n`, 'utf8');
    return { opened: p };
  }
  const { shell } = require('electron');
  const err = await shell.openPath(p);
  if (err) {
    throw Object.assign(new Error(err), { code: 'open_failed' });
  }
  return { opened: p };
}

function createWindow() {
  // 1280x820 mac dinh, usable toi thieu 760x520 (MIN-32 §1)
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 760,
    minHeight: 520,
    show: !SMOKE,
    webPreferences: {
      preload: path.join(__dirname, '..', 'preload', 'preload.js'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      nodeIntegrationInWorker: false,
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
  });
  win.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
  win.on('close', async (e) => {
    // Quit giua luc job con chay se drain sidecar -> job chet engine_shutdown.
    // Chan de user quyet dinh (spec §4 — khong mat job vi thao tac dong).
    if (allowClose || SMOKE) return;
    const active = tracker ? tracker.listActive().length : 0;
    if (active === 0) return;
    e.preventDefault();
    const r = await dialog.showMessageBox(win, {
      type: 'warning',
      buttons: ['Hủy', 'Vẫn thoát'],
      defaultId: 0,
      cancelId: 0,
      title: 'Còn job đang chạy',
      message: `Còn ${active} job chưa kết thúc.`,
      detail: 'Thoát sẽ dừng engine; các job chuyển canceled (engine_shutdown).',
    });
    if (r.response === 1) {
      allowClose = true;
      win.close();
    }
  });
  win.on('closed', () => { win = null; });
  // tat ca content la local — chan cua so moi va dieu huong ra ngoai
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (e) => e.preventDefault());
}

async function smokeProbe() {
  // Packaged/dev smoke: cho sidecar ready, goi file.inspect len chinh no,
  // ghi ket qua ra G1_SMOKE_LOG roi thoat. Khong can terminal tuong tac.
  const out = process.env.G1_SMOKE_LOG ||
    path.join(app.getPath('userData'), 'smoke.json');
  const record = { steps: [] };
  const step = (name, data) => { record.steps.push({ name, data }); };
  try {
    const deadline = Date.now() + 40_000;
    while (sidecar.state !== 'ready' && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 250));
    }
    step('sidecar_state', sidecar.status());
    if (sidecar.state !== 'ready') throw new Error('sidecar not ready');
    // file that: exe cua chinh app — ton tai trong ca dev (node_modules
    // electron) va packaged (g1-shell.exe); khong nam trong asar
    const target = app.isPackaged
      ? process.execPath
      : path.join(SHELL_ROOT, 'package.json');
    const job = await sidecar.client.submitCommand('file.inspect', {
      file: { path: target, scope: 'machine_local' },
    }, 'overview');
    step('submit', job);
    let cur = job;
    while (!['succeeded', 'failed', 'canceled', 'partial'].includes(cur.status)
           && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 300));
      cur = await sidecar.client.getJob(job.job_id);
    }
    step('final', cur);
    record.ok = cur.status === 'succeeded';
  } catch (err) {
    record.ok = false;
    record.error = String(err && err.stack || err);
  }
  fs.writeFileSync(out, JSON.stringify(record, null, 2));
  await sidecar.shutdown();
  app.exit(record.ok ? 0 : 1);
}

function collectDiagnostics() {
  // Panel diagnostics (MIN-32 §6): version, helper status, log da redact.
  // Credential/cookie/token khong bao gio hien thi — doc log xong van redact
  // lai tung dong (belt-and-suspenders).
  const tail = [];
  try {
    if (logPath && fs.existsSync(logPath)) {
      const raw = fs.readFileSync(logPath, 'utf8');
      const lines = raw.trim().split('\n').slice(-40);
      for (const line of lines) tail.push(redactString(line));
    }
  } catch (err) {
    tail.push(`<khong doc duoc log: ${err.message}>`);
  }
  return {
    shell_version: SHELL_VERSION,
    user_data: app.getPath('userData'),
    log_path: logPath,
    log_tail: tail,
  };
}

async function start() {
  app.setName('g1-shell');
  // packaged app khong co terminal — ghi diagnostics ra file (da redact)
  const logDir = path.join(app.getPath('userData'), 'logs');
  fs.mkdirSync(logDir, { recursive: true });
  logPath = path.join(logDir, 'main.log');
  const fileStream = fs.createWriteStream(logPath, { flags: 'a' });
  const stderr = process.stderr;
  log = makeLogger({ write: (s) => { fileStream.write(s); stderr.write(s); } });
  const cmd = sidecarCommand(
    app.isPackaged, process.resourcesPath, SHELL_ROOT);
  sidecar = new SidecarManager({ command: cmd, logger: log });
  tracker = new JobTracker({ sidecar, logger: log });
  tracker.on('job', (job) => {
    if (win) win.webContents.send('desktop.v1.jobUpdate', job);
  });
  sidecar.on('state', () => {
    if (win) win.webContents.send('desktop.v1.statusUpdate', sidecar.status());
  });

  registerIpc(ipcMain, {
    sidecar, tracker, pickFiles, openPath, logger: log,
    diagnostics: () => collectDiagnostics(),
  });
  createWindow();

  sidecar.start().catch((err) => {
    log.error('sidecar start loi', { err: String(err) });
  });

  if (SMOKE) await smokeProbe();
}

app.whenReady().then(start);

app.on('second-instance', () => {
  if (win) {
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

app.on('before-quit', async (event) => {
  if (sidecar && sidecar.state !== 'stopped' && !sidecar.stopping) {
    event.preventDefault();
    tracker && tracker.stop();
    await sidecar.shutdown();
    app.quit();
  }
});

app.on('window-all-closed', () => {
  app.quit();
});
