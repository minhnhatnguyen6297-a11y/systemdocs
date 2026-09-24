// JobTracker — sidecar restart/resync (MIN-69 T5).
// Bao phu: instance change -> job non-terminal thanh failed
// {engine_restarted}; resync theo job_id lay lai terminal snapshot that
// tu journal ben cua sidecar moi; resync that bai giu engine_restarted;
// terminal cuc bo la bat bien (snapshot non-terminal tre khong mo lai).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { JobTracker } = require('../src/main/job-tracker.js');

function makeSidecar({ jobs } = {}) {
  const s = new EventEmitter();
  s.state = 'ready';
  s.client = jobs ? {
    getJob: async (id) => {
      const j = jobs.get(id);
      if (!j) { const e = new Error('not found'); e.status = 404; throw e; }
      return j;
    },
  } : null;
  return s;
}

function snap(jobId, status, extra = {}) {
  return {
    contract_version: 'desktopcommand.v1',
    job_id: jobId,
    command_id: 'cmd-' + jobId,
    command: 'diag.slow_task',
    status,
    waiting_on: null,
    progress: null,
    result: null,
    error: null,
    updated_at: new Date().toISOString(),
    ...extra,
  };
}

const logger = { info() {}, warn() {}, error() {} };
const tick = () => new Promise((r) => setImmediate(r));

test('instance change: non-terminal -> engine_restarted, roi resync lay terminal that', async () => {
  // Sidecar moi giu journal: j_ok da succeeded TRUOC khi process cu chet.
  const remote = new Map([['j_ok', snap('j_ok', 'succeeded',
    { result: { kind: 'ok', data: {} } })]]);
  const sidecar = makeSidecar({ jobs: remote });
  const t = new JobTracker({ sidecar, logger });
  t.stop();
  sidecar.emit('instance', 'instance-1');   // ket noi ban dau
  t.track(snap('j_ok', 'running'));
  t.track(snap('j_gone', 'running'));

  sidecar.emit('instance', 'instance-2');   // sidecar restart
  // Danh dau cuc bo ngay lap tuc (khong cho resync).
  assert.equal(t.jobs.get('j_ok').error.code, 'engine_restarted');
  assert.equal(t.jobs.get('j_gone').error.code, 'engine_restarted');

  await tick(); await tick();
  // j_ok: journal ben tra terminal that → tracker dung snapshot do.
  assert.equal(t.jobs.get('j_ok').status, 'succeeded');
  assert.equal(t.jobs.get('j_ok').error, null);
  // j_gone: khong co trong journal → giu engine_restarted.
  assert.equal(t.jobs.get('j_gone').status, 'failed');
  assert.equal(t.jobs.get('j_gone').error.code, 'engine_restarted');
});

test('instance change: job da terminal cuc bo khong bi danh lai', async () => {
  const sidecar = makeSidecar({ jobs: new Map() });
  const t = new JobTracker({ sidecar, logger });
  t.stop();
  sidecar.emit('instance', 'instance-1');
  t.track(snap('j_done', 'succeeded', { result: { kind: 'ok', data: {} } }));
  sidecar.emit('instance', 'instance-2');
  await tick();
  assert.equal(t.jobs.get('j_done').status, 'succeeded');
});

test('terminal cuc bo bat bien: snapshot non-terminal tre bi bo qua', () => {
  const sidecar = makeSidecar();
  const t = new JobTracker({ sidecar, logger });
  t.stop();
  t.track(snap('j_t', 'succeeded'));
  t.track(snap('j_t', 'running'));   // stale/loi — khong duoc mo lai
  assert.equal(t.jobs.get('j_t').status, 'succeeded');
});

test('unavailable: danh dau engine_unavailable cho moi job con chay', () => {
  const sidecar = makeSidecar();
  const t = new JobTracker({ sidecar, logger });
  t.stop();
  t.track(snap('j_a', 'running'));
  t.track(snap('j_b', 'succeeded'));
  sidecar.emit('unavailable', { code: 'engine_unavailable' });
  assert.equal(t.jobs.get('j_a').status, 'failed');
  assert.equal(t.jobs.get('j_a').error.code, 'engine_unavailable');
  assert.equal(t.jobs.get('j_b').status, 'succeeded');
});
