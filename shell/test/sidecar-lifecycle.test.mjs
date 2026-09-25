// Lifecycle test cho SidecarManager — fake sidecar bang node script.
// Bao phu: spawn error, exit-before-health, restart exhaustion (3 lan),
// shutdown giua luc spawn, shutdown sau khi child da chet, version mismatch.
// Luu y: test chay tuan tu; FAKE_MODE truyen qua process.env cho child.
import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { SidecarManager } = require('../src/main/sidecar.js');

const FIXTURE = path.join(path.dirname(fileURLToPath(import.meta.url)),
                          'fixtures', 'fake_sidecar.mjs');

const _SANITIZE_ENV = [
  'FAKE_MODE', 'FAKE_DUMP',
  'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE',
  // Bien the hoa/thuong — tren *nix la key rieng, tren Windows delete
  // theo uppercase da phu nhung liet ke cho ro.
  'PythonPath', 'PythonHome', 'pythonstartup', 'pythonhome',
  'pythonuserbase',
  'G1_NOTARY_DATA_DIR', 'G1_UPLOAD_DATA_DIR', 'G1_OUTPUT_DIR',
  'G1_BUILD_LABEL',
];
afterEach(() => { for (const k of _SANITIZE_ENV) delete process.env[k]; });

function makeLogger() {
  const counts = { spawn: 0, restart: 0 };
  const logger = {
    info: (msg) => { if (msg === 'spawn sidecar') counts.spawn += 1; },
    warn: (msg) => { if (msg === 'restart sidecar') counts.restart += 1; },
    error: () => {},
  };
  return { logger, counts };
}

function fakeManager(mode) {
  const { logger, counts } = makeLogger();
  process.env.FAKE_MODE = mode;              // child ke thua qua spawn env
  const m = new SidecarManager({
    command: { cmd: process.execPath, args: [FIXTURE],
               cwd: path.dirname(FIXTURE) },
    logger,
  });
  return { m, counts };
}

test('ok: start -> ready, shutdown -> sidecar exit sach', async () => {
  const { m } = fakeManager('ok');
  const states = [];
  m.on('state', (s) => states.push(s));
  await m.start();
  assert.equal(m.state, 'ready');
  assert.ok(m.instanceId.startsWith('fake-'));
  await m.shutdown();
  assert.equal(m.state, 'stopped');
  assert.deepEqual(states, ['starting', 'ready', 'stopped']);
});

test('missing exe: start reject nhanh; shutdown huy restart timer', async () => {
  const { logger, counts } = makeLogger();
  const m = new SidecarManager({
    command: { cmd: 'C:/khong-ton-tai-sidecar.exe', args: [], cwd: '.' },
    logger,
  });
  await assert.rejects(m.start());
  await m.shutdown();
  const spawns = counts.spawn;
  await new Promise((r) => setTimeout(r, 1500));
  assert.equal(counts.spawn, spawns); // khong spawn them sau shutdown
});

test('exit truoc khi healthy: dung 3 restart roi unavailable', async () => {
  const { m, counts } = fakeManager('exit');
  let unavailable = 0;
  m.on('unavailable', () => { unavailable += 1; });
  await assert.rejects(m.start());
  // cho chu ky restart het: 1s + 3s + 10s + margin
  await new Promise((r) => setTimeout(r, 16000));
  assert.equal(unavailable, 1);
  assert.equal(m.state, 'unavailable');
  assert.equal(counts.restart, 3);
  assert.equal(counts.spawn, 4);           // 1 lan dau + 3 restart
}, { timeout: 30000 });

test('version mismatch: fatal ngay, khong retry', async () => {
  const { m, counts } = fakeManager('badver');
  let reason = null;
  m.on('unavailable', (r) => { reason = r; });
  await assert.rejects(m.start());
  assert.equal(m.state, 'unavailable');
  assert.equal(reason && reason.code, 'engine_version_mismatch');
  await new Promise((r) => setTimeout(r, 1500));
  assert.equal(counts.spawn, 1);           // khong spawn lai
  await m.shutdown();
});

test('shutdown giua luc spawn: khong orphan, khong crash', async () => {
  const { m } = fakeManager('ok');
  const startP = m.start().catch(() => {}); // co the reject vi stopping
  await m.shutdown();
  await startP;
  assert.equal(m.state, 'stopped');
  assert.equal(m.child, null);
});

test('shutdown sau khi child da exit: clean', async () => {
  const { m } = fakeManager('exit');
  const startP = m.start().catch(() => {});
  await new Promise((r) => setTimeout(r, 500)); // child da chet
  await m.shutdown();                          // khong throw
  await startP;
  assert.equal(m.state, 'stopped');
});

test('config: SHUTDOWN_GRACE_MS bao phu worst-case _stop() cua sidecar', () => {
  // app.py _stop(): timer 0.2s + store.drain(timeout=2) +
  // worker().shutdown(timeout=2) — reconcile + join chia 2s do (xem
  // upload_session._BrowserWorker.shutdown) — + uvicorn exit ~0.3s
  // ≈ 4.5s. Grace nho hon bound nay → SIGKILL giet reconcile/close giua
  // chung, dung luc do chac chan 'da Luu' can duoc ghi nhat.
  const { SHUTDOWN_GRACE_MS } = require('../src/main/config.js');
  assert.equal(SHUTDOWN_GRACE_MS, 6_000);
  assert.ok(SHUTDOWN_GRACE_MS > 4_500,
            'grace phai vuot worst-case _stop() ~4.5s voi headroom');
});

// ---- F3/F4 (T9 review): spawn env isolation ----

test('packaged spawn: strip PYTHON* (ke ca case variant) + dat ' +
     'G1_NOTARY_DATA_DIR ngoai output', async () => {
  const dump = path.join(
    os.tmpdir(), `g1-fake-dump-${process.pid}-${Date.now()}.json`);
  process.env.FAKE_MODE = 'envdump';
  process.env.FAKE_DUMP = dump;
  // Bien the hoa/thuong: Windows env var case-insensitive voi child —
  // `PythonPath` van chay vao frozen exe neu strip chi dung exact-case.
  // (delete truoc de Windows tao key dung case variant, khong bi giu
  // case cua var co san.)
  delete process.env.PYTHONPATH;
  process.env.PythonPath = 'C:/hook-dir';       // sitecustomize/fixture hook
  delete process.env.PYTHONHOME;
  process.env.PythonHome = 'C:/pyhome';
  delete process.env.PYTHONSTARTUP;
  process.env.pythonstartup = 'C:/startup.py';
  process.env.PYTHONUSERBASE = 'C:/pybase';
  const { logger } = makeLogger();
  const m = new SidecarManager({
    command: { cmd: process.execPath, args: [FIXTURE],
               cwd: path.dirname(FIXTURE),
               env: { G1_ENGINE_DIR: 'C:/engine',
                      G1_BUILD_LABEL: 'production' } },
    logger,
  });
  await m.start();
  assert.equal(m.state, 'ready');
  await m.shutdown();
  const d = JSON.parse(fs.readFileSync(dump, 'utf8'));
  fs.unlinkSync(dump);
  // F3: env interpreter Python cua user KHONG duoc chay vao packaged —
  // ke ca bien the hoa/thuong (PythonPath/pythonstartup/PythonHome) va
  // PYTHONUSERBASE. python_keys rong = khong key denylist nao sot lai.
  assert.equal(d.pythonpath, null);
  assert.equal(d.pythonhome, null);
  assert.equal(d.pythonstartup, null);
  assert.equal(d.pythonuserbase, null);
  assert.deepEqual(d.python_keys, []);
  // F4: notary data duoi engine-data/ cua userData — KHONG duoi output/
  // (output la cho file export), KHONG trong install dir.
  assert.ok(d.notary_data, 'packaged phai dat G1_NOTARY_DATA_DIR');
  const norm = d.notary_data.replace(/\//g, path.sep);
  assert.ok(norm.endsWith(path.join('engine-data', 'notary_v2')),
            `G1_NOTARY_DATA_DIR phai ket thuc bang engine-data/notary_v2: ` +
            norm);
  assert.ok(!norm.includes(path.join('output', 'engine-data')),
            `notary data khong duoc nam duoi output/: ${norm}`);
  assert.ok(d.upload_data, 'packaged phai dat G1_UPLOAD_DATA_DIR');
  assert.ok(d.output, 'packaged phai dat G1_OUTPUT_DIR');
  assert.equal(d.engine_dir, 'C:/engine');
  assert.equal(d.build_label, 'production');
}, { timeout: 15000 });

test('dev spawn: giu PYTHONPATH, khong dat G1_NOTARY_DATA_DIR', async () => {
  const dump = path.join(
    os.tmpdir(), `g1-fake-dump-${process.pid}-${Date.now()}.json`);
  process.env.FAKE_MODE = 'envdump';
  process.env.FAKE_DUMP = dump;
  process.env.PYTHONPATH = 'C:/hook-dir';
  delete process.env.PYTHONHOME;
  process.env.pythonhome = 'C:/pyhome-dev';  // case variant — dev giu lai
  const { logger } = makeLogger();
  const m = new SidecarManager({
    command: { cmd: process.execPath, args: [FIXTURE],
               cwd: path.dirname(FIXTURE) },   // khong env → dev spawn
    logger,
  });
  await m.start();
  await m.shutdown();
  const d = JSON.parse(fs.readFileSync(dump, 'utf8'));
  fs.unlinkSync(dump);
  // Dev hook test_upload_e2e can PYTHONPATH — giu nguyen, ke ca bien the
  // hoa/thuong cua cac bien denylist khac.
  assert.equal(d.pythonpath, 'C:/hook-dir');
  assert.equal(d.pythonhome, 'C:/pyhome-dev');
  assert.ok(d.python_keys.includes('pythonhome'),
            'dev spawn phai giu ca key denylist dang hoa/thuong khac');
  // Dev: notary data dir = engine root (repo) nhu cu — KHONG dat env.
  assert.equal(d.notary_data, null);
}, { timeout: 15000 });
