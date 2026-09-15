// Navigation + shared-shell invariants (MIN-67):
// - NAV_SPEC khop module registry (moi muc engine co module, placeholder hien)
// - IPC allowlist co handler moi (listJobs/restartEngine/getDiagnostics)
// - shell khong mo app legacy ben ngoai (khong openExternal/shell.openPath)
// - restartEngine/listJobs/getDiagnostics handler semantics
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const L = require('../src/renderer/lib.js');
const { ALLOWLIST, HANDLERS } = require('../src/main/ipc.js');
const { listModules } = require('../src/main/registry.js');

const HERE = path.dirname(fileURLToPath(import.meta.url));

test('moi muc nav engine/placeholder deu co module trong registry', () => {
  const mods = listModules();
  const ids = new Set(mods.map((m) => m.id));
  for (const n of L.NAV_SPEC) {
    if (n.registry === null) continue;            // overview la view shell
    assert.ok(ids.has(n.registry),
      `nav ${n.id} tro toi module khong ton tai: ${n.registry}`);
  }
  // office placeholder phai unavailable trong registry (hien "Chua trien khai")
  const office = mods.find((m) => m.id === 'office');
  assert.equal(office.status, 'unavailable');
  assert.equal(office.reason, 'not_implemented');
});

test('module registry khong co muc nao "mo app legacy ben ngoai"', () => {
  for (const m of listModules()) {
    assert.notEqual(m.kind, 'external');
    assert.ok(!String(m.id).includes('..'));
  }
});

test('main/preload/renderer khong mo app legacy hay dieu huong ngoai', () => {
  const forbidden = new RegExp(
    'openExternal|shell\\.openPath|shell\\.openItem|execFile|' +
    'child_process.*exec\\s*\\(');
  for (const f of ['src/main/main.js', 'src/main/ipc.js',
                   'src/preload/preload.js', 'src/renderer/renderer.js',
                   'src/renderer/lib.js']) {
    const src = fs.readFileSync(path.join(HERE, '..', f), 'utf8')
      .replace(/\s/g, ' ');
    assert.ok(!forbidden.test(src),
      `${f} chua API mo app/dieu huong ngoai`);
  }
});

test('IPC allowlist co cac channel moi cua MIN-67', () => {
  for (const ch of ['desktop.v1.listJobs', 'desktop.v1.restartEngine',
                    'desktop.v1.getDiagnostics']) {
    assert.ok(ALLOWLIST.includes(ch), `thieu ${ch}`);
    assert.match(ch, /^desktop\.v1\./);
  }
});

test('listJobs tra snapshot tu tracker (reconnect sau renderer reload)', async () => {
  const snap = { job_id: 'j_1', status: 'running' };
  const deps = {
    tracker: { jobs: new Map([['j_1', snap]]), track() {} },
    sidecar: { status: () => ({}) },
    logger: { error() {} },
  };
  const r = await HANDLERS['desktop.v1.listJobs'](deps);
  assert.equal(r.ok, true);
  assert.deepEqual(r.data.jobs, [snap]);
});

test('listJobs chiu duoc tracker thieu map (mock)', async () => {
  const deps = { tracker: { track() {} },
                 sidecar: { status: () => ({}) },
                 logger: { error() {} } };
  const r = await HANDLERS['desktop.v1.listJobs'](deps);
  assert.equal(r.ok, true);
  assert.deepEqual(r.data.jobs, []);
});

test('restartEngine: ready thi no-op, unavailable thi goi start', async () => {
  let started = 0;
  const ready = {
    sidecar: { state: 'ready',
               status: () => ({ state: 'ready' }),
               start: async () => { started += 1; } },
    logger: { error() {} },
  };
  const r1 = await HANDLERS['desktop.v1.restartEngine'](ready);
  assert.equal(r1.ok, true);
  assert.equal(started, 0);                     // khong restart khi dang ready

  const down = {
    sidecar: { state: 'unavailable',
               status: () => ({ state: 'unavailable' }),
               start: async () => { started += 1; } },
    logger: { error() {} },
  };
  const r2 = await HANDLERS['desktop.v1.restartEngine'](down);
  assert.equal(r2.ok, true);
  assert.equal(started, 1);
});

test('getDiagnostics gop diagnostics() + sidecar + modules', async () => {
  const deps = {
    sidecar: { status: () => ({ state: 'ready',
                                engine_version: 'eng/1' }) },
    diagnostics: () => ({ shell_version: '9.9.9', log_tail: ['x'] }),
    logger: { error() {} },
  };
  const r = await HANDLERS['desktop.v1.getDiagnostics'](deps);
  assert.equal(r.ok, true);
  assert.equal(r.data.shell_version, '9.9.9');
  assert.equal(r.data.sidecar.state, 'ready');
  assert.ok(Array.isArray(r.data.modules));
});

test('submitCommand van tu choi command ngoai module allowlist', async () => {
  const deps = {
    sidecar: { state: 'ready', client: {}, status: () => ({}) },
    tracker: { track() {} },
    logger: { error() {} },
  };
  for (const cmd of ['shell.exec', 'office.run', 'excel.macro',
                     'legacy.launch']) {
    const r = await HANDLERS['desktop.v1.submitCommand'](
      deps, { command: cmd, payload: {} });
    assert.equal(r.ok, false, cmd);
    assert.equal(r.error.code, 'command_unknown', cmd);
  }
});
