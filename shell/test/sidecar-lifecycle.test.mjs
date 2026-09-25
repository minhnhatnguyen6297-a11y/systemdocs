// Lifecycle test cho SidecarManager — fake sidecar bang node script.
// Bao phu: spawn error, exit-before-health, restart exhaustion (3 lan),
// shutdown giua luc spawn, shutdown sau khi child da chet, version mismatch.
// Luu y: test chay tuan tu; FAKE_MODE truyen qua process.env cho child.
import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { SidecarManager } = require('../src/main/sidecar.js');

const FIXTURE = path.join(path.dirname(fileURLToPath(import.meta.url)),
                          'fixtures', 'fake_sidecar.mjs');

afterEach(() => { delete process.env.FAKE_MODE; });

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
