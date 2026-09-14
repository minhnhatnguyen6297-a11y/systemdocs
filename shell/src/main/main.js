'use strict';

// G1 shell — Electron main entry (desktopcommand.v1 consumer).
// Security: renderer sandbox + contextIsolation + no nodeIntegration;
// sidecar token/port chi trong main; preload expose IPC allowlist versioned.

const path = require('path');
const fs = require('fs');
const { app, BrowserWindow, dialog, ipcMain } = require('electron');

const { sidecarCommand } = require('./config');
const { makeLogger } = require('./redact');
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

async function pickFiles(opts = {}) {
  const res = await dialog.showOpenDialog(win, {
    properties: opts.multi === false ? ['openFile'] : ['openFile', 'multiSelections'],
    filters: opts.filters,
  });
  if (res.canceled) return [];
  // file_ref machine_local theo contract §6 — path tuyet doi tu native dialog
  return res.filePaths.map((p) => ({
    path: p,
    scope: 'machine_local',
    size_bytes: fs.statSync(p).size,
  }));
}

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
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

async function start() {
  app.setName('g1-shell');
  // packaged app khong co terminal — ghi diagnostics ra file (da redact)
  const logDir = path.join(app.getPath('userData'), 'logs');
  fs.mkdirSync(logDir, { recursive: true });
  const fileStream = fs.createWriteStream(
    path.join(logDir, 'main.log'), { flags: 'a' });
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

  registerIpc(ipcMain, { sidecar, tracker, pickFiles, logger: log });
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
