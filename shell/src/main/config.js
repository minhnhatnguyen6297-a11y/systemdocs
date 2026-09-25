'use strict';

const fs = require('fs');
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
const NOTARY_MOCK_ENV = 'G1_DEV_NOTARY_MOCK'; // dev-only mock notary (MIN-106)

function stripNotaryMockEnv(appIsPackaged, log) {
  // Sidecar ke thua process.env (sidecar.js spawn env) — dev: flag =1 di
  // thang xuong sidecar, gateway chon mock. Packaged: strip flag khoi env
  // con + warning redact (chi ten bien, khong gia tri) — mock khong bao gio
  // chay tren ban dong goi.
  if (!appIsPackaged) return;
  if (process.env[NOTARY_MOCK_ENV] === undefined) return;
  delete process.env[NOTARY_MOCK_ENV];
  if (log && typeof log.warn === 'function') {
    log.warn(`${NOTARY_MOCK_ENV} bi bo qua tren ban packaged — backend real`);
  }
}

function sidecarCommand(appIsPackaged, resourcesPath, shellRoot, opts = {}) {
  if (appIsPackaged) {
    return {
      cmd: path.join(resourcesPath, 'sidecar', 'g1-shell-sidecar',
                     'g1-shell-sidecar.exe'),
      args: [],
      cwd: path.join(resourcesPath, 'sidecar', 'g1-shell-sidecar'),
      env: {
        // MIN-69 T9: engine code ship dang source trong
        // resources/engine/<key> — engine_roots resolve qua env nay;
        // khong con phu thuoc repo dev.
        G1_ENGINE_DIR: path.join(resourcesPath, 'engine'),
        // Chromium pinned theo playwright cua build — resources/
        // playwright-browsers/chromium-<rev>; khong tai luc runtime.
        PLAYWRIGHT_BROWSERS_PATH:
          path.join(resourcesPath, 'playwright-browsers'),
        // Nhan build production|test — healthz quang bao cho harness.
        G1_BUILD_LABEL: opts.buildLabel || 'production',
      },
    };
  }
  // Dev: G1_PYTHON override; khong set thi thu venv engine cua monorepo
  // (notary_v2/venv co san deps sidecar: fastapi/uvicorn/sqlalchemy...)
  // truoc khi roi ve 'python' tren PATH.
  let python = process.env.G1_PYTHON;
  if (!python) {
    const venv = path.join(shellRoot, '..', 'notary_v2', 'venv',
                           'Scripts', 'python.exe');
    python = fs.existsSync(venv) ? venv : 'python';
  }
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
  NOTARY_MOCK_ENV,
  sidecarCommand,
  stripNotaryMockEnv,
};
