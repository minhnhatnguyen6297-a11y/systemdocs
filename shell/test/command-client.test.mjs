import test from 'node:test';
import assert from 'node:assert/strict';

import { CommandClient, CommandHttpError } from '../src/main/command-client.js';

function fakeFetch(routes) {
  const calls = [];
  const fn = async (url, opts = {}) => {
    calls.push({ url, opts });
    const key = `${opts.method || 'GET'} ${url.replace(/^https?:\/\/[^/]+/, '')}`;
    const hit = routes[key];
    if (!hit) {
      return { ok: false, status: 404,
               json: async () => ({ error: { code: 'job_not_found',
                                            message: 'nf' } }) };
    }
    return { ok: hit.ok !== false, status: hit.status || 200,
             json: async () => hit.body };
  };
  fn.calls = calls;
  return fn;
}

test('submitCommand gui dung request shape v1', async () => {
  const f = fakeFetch({
    'POST /v1/commands': { body: { job_id: 'j_1', status: 'accepted' } },
  });
  const c = new CommandClient({ baseUrl: 'http://127.0.0.1:9', token: 'T',
                                fetchImpl: f });
  const job = await c.submitCommand('file.inspect', { file: { path: 'D:/x' } },
                                    'upload');
  assert.equal(job.job_id, 'j_1');
  const sent = JSON.parse(f.calls[0].opts.body);
  assert.equal(sent.contract_version, 'desktopcommand.v1');
  assert.match(sent.command_id, /^[0-9a-f-]{36}$/);
  assert.equal(sent.command, 'file.inspect');
  assert.equal(sent.client_meta.module, 'upload');
  assert.equal(f.calls[0].opts.headers.authorization, 'Bearer T');
});

test('loi HTTP map sang CommandHttpError co code', async () => {
  const f = fakeFetch({
    'POST /v1/jobs/j_9/cancel': {
      ok: false, status: 409,
      body: { error: { code: 'job_already_terminal', message: 'x',
                       retryable: false } },
    },
  });
  const c = new CommandClient({ baseUrl: 'http://x', token: 't', fetchImpl: f });
  await assert.rejects(() => c.cancelJob('j_9'), (err) => {
    assert.ok(err instanceof CommandHttpError);
    assert.equal(err.code, 'job_already_terminal');
    assert.equal(err.httpStatus, 409);
    return true;
  });
});

test('sidecar chet → engine_unavailable retryable', async () => {
  const c = new CommandClient({
    baseUrl: 'http://x', token: 't',
    fetchImpl: async () => { throw new Error('ECONNREFUSED'); },
  });
  await assert.rejects(() => c.getJob('j_1'), (err) => {
    assert.equal(err.code, 'engine_unavailable');
    assert.equal(err.retryable, true);
    return true;
  });
});
