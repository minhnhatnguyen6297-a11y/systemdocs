// Display logic test — lib.js la nguon duy nhat cho vocabulary trang thai,
// nav spec va 4 mat trang thai (MIN-67 / MIN-32). Chay bang node --test,
// khong can DOM.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const L = require('../src/renderer/lib.js');

test('nav spec co dung 7 muc theo thu tu MIN-32 §1', () => {
  assert.deepEqual(L.NAV_SPEC.map((n) => n.id), [
    'overview', 'upload', 'document-review', 'excel-word',
    'office', 'search', 'status',
  ]);
  // placeholder van hien trong nav — khong bi an
  assert.ok(L.NAV_SPEC.some((n) => n.id === 'office'));
});

test('navEntry: id trong allowlist tra entry, ngoai bi tu choi', () => {
  assert.equal(L.navEntry('upload').title, 'Upload/Audit');
  assert.equal(L.navEntry('__proto__'), null);
  assert.equal(L.navEntry('notary_v2'), null);      // id cu khong hop le
  assert.equal(L.navEntry(''), null);
  assert.equal(L.navEntry('../../etc/passwd'), null);
});

test('status label phu het trang thai contract + waiting', () => {
  for (const s of ['accepted', 'running', 'waiting_user', 'partial',
                   'succeeded', 'failed', 'canceled']) {
    assert.ok(L.STATUS_LABEL[s], `thieu label cho ${s}`);
    assert.notEqual(L.statusLabel(s), s);
  }
  // waiting_user hien thi la cho nguoi, KHONG phai loi
  assert.equal(L.STATUS_TONE.waiting_user, 'warn');
  assert.equal(L.STATUS_TONE.failed, 'error');
});

test('WAITING_CTA phu het enum waiting_on cua contract', () => {
  for (const w of ['login', 'review', 'finalize', 'confirm']) {
    assert.ok(L.WAITING_CTA[w], `thieu CTA cho ${w}`);
  }
});

test('jobDisplay: waiting_user -> banner CTA, khong phai error', () => {
  const d = L.jobDisplay({
    job_id: 'j_1', command: 'upload.start_login',
    status: 'waiting_user', waiting_on: 'login', error: null,
  });
  assert.equal(d.waiting.on, 'login');
  assert.match(d.waiting.cta, /Chromium/);
  assert.equal(d.tone, 'warn');
  assert.equal(d.cancelable, true);   // cancel hien o waiting_user
  assert.equal(d.terminal, false);
});

test('jobDisplay: terminal + cancelable theo contract', () => {
  for (const s of ['accepted', 'running', 'waiting_user']) {
    assert.equal(L.jobDisplay({ status: s }).cancelable, true, s);
  }
  for (const s of ['succeeded', 'failed', 'canceled', 'partial']) {
    const d = L.jobDisplay({ status: s });
    assert.equal(d.terminal, true, s);
    assert.equal(d.cancelable, false, s);
  }
});

test('jobDisplay: partial phai co breakdown nhom completed', () => {
  const d = L.jobDisplay({
    status: 'partial',
    result: { kind: 'x', data: { breakdown: { succeeded: ['a'],
                                              failed: ['b'] } } },
  });
  assert.equal(d.label, 'Hoàn tất một phần');
  assert.deepEqual(d.breakdown.failed, ['b']);
});

test('jobDisplay: null/error-safe — renderer khong crash tren job thieu', () => {
  const d = L.jobDisplay(null);
  assert.equal(d.jobId, '');
  assert.equal(d.waiting, null);
  const d2 = L.jobDisplay({ status: 'failed', error: {
    code: 'engine_restarted', message: 'x', retryable: true } });
  assert.equal(d2.error.code, 'engine_restarted');
});

test('moduleFace: placeholder/unavailable/ready', () => {
  assert.equal(L.moduleFace({ kind: 'placeholder' }), 'placeholder');
  assert.equal(L.moduleFace(
    { status: 'unavailable', reason: 'not_implemented' }), 'placeholder');
  assert.equal(L.moduleFace({ status: 'unavailable' }), 'unavailable');
  assert.equal(L.moduleFace({ status: 'available' }), 'ready');
  assert.equal(L.moduleFace(null), 'unavailable');
});

test('faces: 4 mat trang thai co du truong toi thieu', () => {
  assert.equal(L.faceLoading('x').kind, 'loading');
  assert.equal(L.faceEmpty('x').kind, 'empty');
  const e = L.faceError({ code: 'file_locked', message: 'm',
                          retryable: true, next_action: 'retry' });
  assert.equal(e.kind, 'error');
  assert.equal(e.retryable, true);
  assert.ok(e.diagnosticsHint);
  const u = L.faceUnavailable('Văn phòng', 'not_implemented');
  assert.equal(u.kind, 'unavailable');
  assert.match(u.detail, /Chưa triển khai/);
});

test('moduleHealth: danh dau placeholder ro, khong an', () => {
  const rows = L.moduleHealth([
    { id: 'upload', title: 'upload_lab', kind: 'engine',
      status: 'available' },
    { id: 'office', title: 'notaryoffice', kind: 'placeholder',
      status: 'unavailable', reason: 'not_implemented' },
  ]);
  assert.equal(rows[0].face, 'ready');
  assert.equal(rows[1].face, 'placeholder');
  assert.equal(rows[1].reason, 'Chưa triển khai');
});
