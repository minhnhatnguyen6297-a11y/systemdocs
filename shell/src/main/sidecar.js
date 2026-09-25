'use strict';

// SidecarManager — spawn/health/restart/shutdown theo contract §7.
// Token + port nam trong main; khong bao gio di qua IPC.
// Restart: toi da 3 lan backoff 1s/3s/10s; version mismatch = fatal (khong retry).

const { spawn } = require('child_process');
const crypto = require('crypto');
const net = require('net');
const path = require('path');
const { EventEmitter } = require('events');

const {
  HEALTHZ_TIMEOUT_MS,
  HEALTHZ_POLL_MS,
  RESTART_BACKOFF_MS,
  SHUTDOWN_GRACE_MS,
  CONTRACT_VERSION,
} = require('./config');
const { CommandClient } = require('./command-client');

function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function _defaultOutputDir() {
  // require('electron') tra string path khi chay duoi node thuong (tests).
  try {
    const { app } = require('electron');
    if (app && typeof app.getPath === 'function') {
      return path.join(app.getPath('userData'), 'output');
    }
  } catch { /* plain node */ }
  return path.join(__dirname, '..', '..', 'output');
}

function _defaultUploadDataDir() {
  // Vung du lieu upload.workflow.v1 (plan §3.2): userData/upload_lab khi
  // packaged — khong bao gio mac dinh vao thu muc cai dat/engine root.
  // Dev/test (node thuong): <shell>/output/upload_lab (gitignored).
  try {
    const { app } = require('electron');
    if (app && typeof app.getPath === 'function') {
      return path.join(app.getPath('userData'), 'upload_lab');
    }
  } catch { /* plain node */ }
  return path.join(_defaultOutputDir(), 'upload_lab');
}

function _defaultNotaryDataDir() {
  // notary.db khi engine root bundled read-only (F4): sibling cua output
  // (<userData>/engine-data/notary_v2) — KHONG nam trong output/ (output
  // la file san pham export). Dev khong dat env — data dir la engine
  // root (repo) nhu cu.
  try {
    const { app } = require('electron');
    if (app && typeof app.getPath === 'function') {
      return path.join(app.getPath('userData'), 'engine-data', 'notary_v2');
    }
  } catch { /* plain node */ }
  return path.join(_defaultOutputDir(), '..', 'engine-data', 'notary_v2');
}

// Env cua interpreter Python ma packaged spawn phai loai bo (F3):
// frozen exe ke thua PYTHONPATH/PYTHONHOME/PYTHONSTARTUP/PYTHONUSERBASE
// tu moi truong user → sitecustomize/e2e fixture hook co the tu chay
// trong production sidecar neu PYTHONPATH tro vao test harness dir;
// PYTHONUSERBASE redirect user site-packages (cung lop injection).
// Dev spawn (python that) giu lai — e2e dev hook dua vao PYTHONPATH
// (test_upload_e2e.py).
const PYTHON_INHERIT_DENYLIST = [
  'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE',
];

class VersionMismatchError extends Error {}

class SidecarManager extends EventEmitter {
  constructor({ command, logger }) {
    super();
    this.command = command;      // {cmd, args, cwd}
    this.log = logger;
    this.child = null;
    this.token = null;
    this.baseUrl = null;
    this.client = null;
    this.instanceId = null;
    this.engineVersion = null;
    this.stopping = false;
    this.restartCount = 0;
    this.state = 'stopped';      // stopped|starting|ready|restarting|unavailable
    this._restartTimer = null;
    this._spawnGen = 0;          // generation de loai bo event tu child cu
    this._spawnInflight = null;  // promise cua _spawnAndWait dang chay
  }

  async start() {
    this.stopping = false;
    this.restartCount = 0;
    await this._spawnAndWait();
  }

  _spawnAndWait() {
    const p = this._doSpawnAndWait().finally(() => {
      if (this._spawnInflight === p) this._spawnInflight = null;
    });
    this._spawnInflight = p;
    return p;
  }

  async _doSpawnAndWait() {
    const gen = ++this._spawnGen;
    this._setState(this.restartCount > 0 ? 'restarting' : 'starting');
    this.token = crypto.randomBytes(32).toString('hex');
    const port = await freePort();
    this.baseUrl = `http://127.0.0.1:${port}`;
    this.log.info('spawn sidecar', { port, cmd: this.command.cmd });
    const env = {
      ...process.env,
      SIDECAR_PORT: String(port),
      SIDECAR_TOKEN: this.token,
      // Output sidecar so huu (word export, tai ve) — userData cho ban
      // packaged; dev/test dung <shell>/output (gitignored).
      G1_OUTPUT_DIR: process.env.G1_OUTPUT_DIR || _defaultOutputDir(),
      // Data root upload.workflow.v1 (websites/<id>/ + workspace.sqlite3)
      // — tach khoi engine root, khong bao gio install dir.
      G1_UPLOAD_DATA_DIR:
        process.env.G1_UPLOAD_DATA_DIR || _defaultUploadDataDir(),
      // Packaged-only: notary.db redirect sang userData khi engine root
      // bundled read-only (F4). Dev KHONG dat — data dir la engine root
      // (repo) nhu cu, dung chung voi notary_v2 app.
      ...(this.command.env
        ? {
            G1_NOTARY_DATA_DIR:
              process.env.G1_NOTARY_DATA_DIR || _defaultNotaryDataDir(),
          }
        : {}),
      // Env packaged-only tu sidecarCommand (engine dir, playwright
      // browsers, build label) — dev khong dat.
      ...(this.command.env || {}),
    };
    if (this.command.env) {
      // Packaged spawn: chan env interpreter Python ke thua tu user —
      // PYTHONPATH tro vao test hook dir se auto-import sitecustomize
      // (fixture portals) hoac giai `import e2e_fixture_hook` trong
      // production (F3). Dev spawn can PYTHONPATH → giu nguyen.
      // Windows env var case-insensitive voi tien trinh con — `PythonPath`
      // van chay vao frozen exe → so khop theo uppercase tren key that.
      for (const key of Object.keys(env)) {
        if (PYTHON_INHERIT_DENYLIST.includes(key.toUpperCase())) {
          delete env[key];
        }
      }
    }
    const child = spawn(this.command.cmd, this.command.args, {
      cwd: this.command.cwd,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    this.child = child;
    child.stdout.on('data', (d) =>
      this.log.info('sidecar.out', { line: String(d).trim() }));
    child.stderr.on('data', (d) =>
      this.log.warn('sidecar.err', { line: String(d).trim() }));
    const onDead = (info) => {
      if (gen !== this._spawnGen || child !== this.child) return; // stale
      this.child = null;
      this.log.warn('sidecar exit', info);
      if (!this.stopping) this._failOrRestart();
    };
    child.once('exit', (code, signal) => onDead({ code, signal }));
    child.once('error', (err) => onDead({ error: String(err) }));
    this.client = new CommandClient({
      baseUrl: this.baseUrl, token: this.token,
    });
    try {
      await this._waitHealthy();
    } catch (err) {
      if (gen !== this._spawnGen) return;          // da bi thay the
      if (this._restartTimer) throw err;           // restart da duoc len lich
      this._killChild(child);                      // khong de orphan
      if (err instanceof VersionMismatchError) {
        this._setState('unavailable');             // loi tat dinh — khong retry
        this.emit('unavailable', { code: 'engine_version_mismatch' });
        throw err;
      }
      if (this.restartCount > 0) throw err;        // restart attempt fail → timer catch lo tiep
      this._setState('unavailable');
      this.emit('unavailable');
      throw err;
    }
    if (gen !== this._spawnGen) return;
    this._setState('ready');
    this.restartCount = 0;
    this.emit('instance', this.instanceId);
  }

  async _waitHealthy() {
    const deadline = Date.now() + HEALTHZ_TIMEOUT_MS;
    for (;;) {
      try {
        const h = await this.client.healthz();
        if (h && h.ok !== false) {
          if (!h.supported_versions ||
              !h.supported_versions.includes(CONTRACT_VERSION)) {
            throw new VersionMismatchError(
              `engine_version_mismatch: ${JSON.stringify(h.supported_versions)}`);
          }
          if (!h.engine_instance_id) {
            // can de danh dau engine_restarted cho job in-flight (contract §5)
            throw new VersionMismatchError(
              'engine_version_mismatch: thieu engine_instance_id');
          }
          this.engineVersion = h.engine_version;
          this.instanceId = h.engine_instance_id;
          this.log.info('sidecar healthy', {
            engine: this.engineVersion, instance: this.instanceId,
          });
          return;
        }
      } catch (err) {
        if (err instanceof VersionMismatchError) throw err;
        // chua san sang — poll tiep
      }
      if (this.stopping) throw new Error('shutdown giua luc spawn');
      if (Date.now() > deadline) {
        throw new Error('sidecar khong healthy trong 30s');
      }
      if (!this.child) throw new Error('sidecar exit truoc khi healthy');
      await sleep(HEALTHZ_POLL_MS);
    }
  }

  _killChild(child) {
    // gen/child-identity check o onDead la lop dedup chinh; khong dong stopping
    try { child.kill(); } catch { /* da chet */ }
    if (child === this.child) this.child = null;
  }

  _failOrRestart() {
    if (this._restartTimer || this.stopping) return;
    if (this.restartCount >= RESTART_BACKOFF_MS.length) {
      this._setState('unavailable');
      this.emit('unavailable');
      this.log.error('sidecar unavailable sau 3 lan restart');
      return;
    }
    const delay = RESTART_BACKOFF_MS[this.restartCount];
    this.restartCount += 1;
    this.log.warn('restart sidecar', { attempt: this.restartCount, delay });
    this._setState('restarting');
    this._restartTimer = setTimeout(() => {
      this._restartTimer = null;
      if (this.stopping) return;
      this._spawnAndWait().catch((err) => {
        this.log.error('restart sidecar loi', { err: String(err) });
        // mismatch/timeout da mark unavailable; con lai → thu lai theo budget
        if (!(err instanceof VersionMismatchError) &&
            this.state !== 'unavailable') {
          this._failOrRestart();
        }
      });
    }, delay);
  }

  async shutdown() {
    this.stopping = true;
    if (this._restartTimer) {
      clearTimeout(this._restartTimer);
      this._restartTimer = null;
    }
    // quit giua luc dang spawn: cho spawn xong roi moi kill duoc
    if (this._spawnInflight) {
      await this._spawnInflight.catch(() => {});
    }
    const child = this.child;
    if (child && child.exitCode === null) {
      try {
        await this.client.shutdown();
      } catch {
        // sidecar co the da chet — kill duoi
      }
      const exited = await Promise.race([
        new Promise((r) => child.once('exit', () => r(true))),
        sleep(SHUTDOWN_GRACE_MS).then(() => false),
      ]);
      if (!exited) {
        this.log.warn('sidecar khong thoat trong grace — kill');
        child.kill();
      }
    }
    this._setState('stopped');
  }

  _setState(s) {
    this.state = s;
    this.emit('state', s);
  }

  status() {
    return {
      state: this.state,
      engine_version: this.engineVersion,
      engine_instance_id: this.instanceId,
      contract_version: CONTRACT_VERSION,
      restart_count: this.restartCount,
    };
  }
}

module.exports = { SidecarManager, freePort };
