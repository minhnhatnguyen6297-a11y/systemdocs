'use strict';

const path = require('path');

const CONTRACT_VERSION = 'desktopcommand.v1';
const SHELL_VERSION = require('../../package.json').version;

const HEALTHZ_TIMEOUT_MS = 30_000; // PyInstaller cold start ~3-6s (P1)
const HEALTHZ_POLL_MS = 250;
const RESTART_BACKOFF_MS = [1_000, 3_000, 10_000]; // toi da 3 lan (contract §7)
// Phai lon hon worst-case cua _stop() ben sidecar (app.py):
//   timer 0.2s + store.drain(timeout=2s) + worker().shutdown(timeout=2s)
//   — reconcile + join CHIA 2s do, khong cong doi, xem
//   upload_session._BrowserWorker.shutdown — + uvicorn should_exit ~
//   0.3s ≈ 4.5s. 6s = bound ~4.5s + ~1.5s headroom. SIGKILL som hon se
//   chem reconcile/close giua chung — dung luc bang chung 'da Luu' can
//   duoc ghi nhat (MIN-69 T5 fix1).
const SHUTDOWN_GRACE_MS = 6_000;
const JOB_POLL_MS = 1_000;

function sidecarCommand(appIsPackaged, resourcesPath, shellRoot) {
  if (appIsPackaged) {
    return {
      cmd: path.join(resourcesPath, 'sidecar', 'g1-shell-sidecar',
                     'g1-shell-sidecar.exe'),
      args: [],
      cwd: path.join(resourcesPath, 'sidecar', 'g1-shell-sidecar'),
    };
  }
  const python = process.env.G1_PYTHON || 'python';
  return {
    cmd: python,
    args: [path.join(shellRoot, 'sidecar', 'app.py')],
    cwd: path.join(shellRoot, 'sidecar'),
  };
}

module.exports = {
  CONTRACT_VERSION,
  SHELL_VERSION,
  HEALTHZ_TIMEOUT_MS,
  HEALTHZ_POLL_MS,
  RESTART_BACKOFF_MS,
  SHUTDOWN_GRACE_MS,
  JOB_POLL_MS,
  sidecarCommand,
};
