import test from 'node:test';
import assert from 'node:assert/strict';

import { redactString, redactObject, makeLogger } from '../src/main/redact.js';

test('redactString mask username trong path', () => {
  assert.equal(
    redactString('loi doc C:\\Users\\minh\\ho so\\a.docx'),
    'loi doc C:\\Users\\<user>\\ho so\\a.docx');
  assert.equal(
    redactString('D:/Users/Minh Nhat/x'), 'D:/Users/<user>/x');
});

test('redactString mask bearer token', () => {
  assert.equal(redactString('Authorization: Bearer abc123xyz'),
               'Authorization: <redacted> <redacted>');
  assert.equal(redactString('token=deadbeef ok'), 'token=<redacted> ok');
});

test('redactObject mask key nhay cam de quy', () => {
  const out = redactObject({
    a: 1,
    nested: { nd_password: 'x', list: [{ session_id: 's' }] },
    path: 'C:\\Users\\minh\\f.docx',
  });
  assert.equal(out.nested.nd_password, '<redacted>');
  assert.equal(out.nested.list[0].session_id, '<redacted>');
  assert.equal(out.path, 'C:\\Users\\<user>\\f.docx');
  assert.equal(out.a, 1);
});

test('makeLogger ghi JSON da redact', () => {
  const chunks = [];
  const stream = { write: (s) => chunks.push(s) };
  const log = makeLogger(stream);
  log.info('spawn sidecar C:\\Users\\minh\\app', { token: 'SECRET' });
  const line = JSON.parse(chunks[0]);
  assert.equal(line.meta.token, '<redacted>');
  assert.match(line.msg, /<user>/);
});
