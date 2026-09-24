'use strict';

// G1 shell — Electron main entry (desktopcommand.v1 consumer).
// Security: renderer sandbox + contextIsolation + no nodeIntegration;
// sidecar token/port chi trong main; preload expose IPC allowlist versioned.

const path = require('path');
const fs = require('fs');
const { app, BrowserWindow, dialog, ipcMain } = require('electron');

const { sidecarCommand, SHELL_VERSION, stripNotaryMockEnv } =
  require('./config');
const { makeLogger, redactString } = require('./redact');
const { SidecarManager } = require('./sidecar');
const { JobTracker } = require('./job-tracker');
const { registerIpc } = require('./ipc');
const { makeFileTokenStore, pickedEntry } = require('./file-tokens');
const { openPathBlockReason } = require('./open-path');

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
// Opaque file tokens (MIN-112): renderer chi nhan {file_token,name,...};
// map token->FileRef song trong main, xoa khi window dong/reload/quit.
const fileTokens = makeFileTokenStore();
// Dirty flag renderer bao qua desktop.v1.setDirtyState — window-close
// guard chan khi con nhap Stage/So do chua luu.
let rendererDirty = false;

async function pickFiles(opts = {}) {
  const properties = opts.directory
    ? ['openDirectory']
    : opts.multi === false ? ['openFile'] : ['openFile', 'multiSelections'];
  const res = await dialog.showOpenDialog(win, { properties, filters: opts.filters });
  if (res.canceled) return [];
  // file_ref machine_local theo contract §6 — path tuyet doi tu native
  // dialog chi song trong main; renderer nhan opaque token + basename.
  return res.filePaths.map(
    (p) => pickedEntry(fileTokens, p, fs.statSync(p)));
}

function registerDroppedFile(p) {
  // File keo-tha: path den tu webUtils.getPathForFile (preload) — stat o
  // main roi cap token nhu picker. Tra null khi khong doc duoc.
  try {
    return pickedEntry(fileTokens, p, fs.statSync(p));
  } catch (err) {
    return null;
  }
}

async function openPath(opts = {}) {
  // Mo file san pham (docx da export, log, ...) bang app mac dinh.
  // Validate boundary: tuyet doi, ton tai, khong UNC — file_ref §6.
  const p = typeof opts.path === 'string' ? opts.path : '';
  const unc = p.startsWith('\\\\') ||
    /^\\\\\?\\(UNC\\|\\\\)/i.test(p);
  if (!p || unc || !/^[A-Za-z]:[\\/]/.test(p) && !p.startsWith('\\\\?\\')) {
    throw Object.assign(new Error('path khong hop le'),
      { code: 'file_scope_not_supported' });
  }
  if (!fs.existsSync(p) || !fs.statSync(p).isFile()) {
    throw Object.assign(new Error('file khong ton tai'),
      { code: 'file_not_found' });
  }
  // Whitelist extension: chi mo tai lieu/san pham engine — khong cho
  // renderer shell.openPath executable/script (.exe/.bat/.lnk...).
  const block = openPathBlockReason(p);
  if (block) {
    throw Object.assign(new Error(block.message), { code: block.code });
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
    // Quit giua luc job con chay se drain sidecar -> job chet engine_shutdown;
    // quit giua luc con nhap chua luu se mat draft (chi song trong phien).
    // Chan de user quyet dinh (spec §4/§6 — khong mat du lieu vi thao tac
    // dong).
    if (allowClose || SMOKE) return;
    const active = tracker ? tracker.listActive().length : 0;
    if (active === 0 && !rendererDirty) return;
    e.preventDefault();
    const r = await dialog.showMessageBox(win, {
      type: 'warning',
      buttons: ['Hủy', 'Vẫn thoát'],
      defaultId: 0,
      cancelId: 0,
      title: active ? 'Còn job đang chạy' : 'Thay đổi chưa lưu',
      message: [
        active ? `Còn ${active} job chưa kết thúc.` : null,
        rendererDirty ? 'Stage/Sơ đồ còn bản nháp chưa lưu.' : null,
      ].filter(Boolean).join(' '),
      detail: 'Thoát sẽ dừng engine (job chuyển canceled) và mất bản nháp ' +
        'chưa lưu trong phiên.',
    });
    if (r.response === 1) {
      allowClose = true;
      win.close();
    }
  });
  win.on('closed', () => {
    win = null;
    rendererDirty = false;
    fileTokens.clear();      // token chet cung window — khong reuse cross-session
  });
  // Renderer reload (Ctrl+R/F5 trong dev) huy map token — entry cu khong
  // resolve duoc nua (token map chi song trong main, khong persist).
  // Draft Stage/So do cung mat theo renderer cu → reset dirty flag de
  // close-guard khong canh bao bong ma.
  win.webContents.on('did-start-navigation', () => {
    fileTokens.clear();
    rendererDirty = false;
  });
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
  // G1_DEV_NOTARY_MOCK (MIN-106): dev truyen xuong sidecar qua env ke thua;
  // packaged luon strip truoc khi spawn — mock khong bao gio chay packaged.
  stripNotaryMockEnv(app.isPackaged, log);
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
    fileTokens,
    registerDroppedFile,
    setDirty: (d) => { rendererDirty = !!d; },
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
  fileTokens.clear();
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
