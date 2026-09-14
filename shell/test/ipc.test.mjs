import test from 'node:test';
import assert from 'node:assert/strict';

import { ALLOWLIST, HANDLERS, validateCommandArgs }
  from '../src/main/ipc.js';
import { moduleForCommand, listModules } from '../src/main/registry.js';

test('allowlist chi gom desktop.v1.* da dang ky', () => {
  assert.ok(ALLOWLIST.length >= 5);
  for (const ch of ALLOWLIST) assert.match(ch, /^desktop\.v1\./);
  // channel ngoai allowlist khong co handler
  assert.equal(HANDLERS['desktop.v1.exec'], undefined);
  assert.equal(HANDLERS['shell.openExternal'], undefined);
});

test('validateCommandArgs tu choi input xau', () => {
  assert.equal(validateCommandArgs(null).ok, false);
  assert.equal(validateCommandArgs('file.inspect').ok, false);
  assert.equal(validateCommandArgs({ command: 'noDot' }).ok, false);
  assert.equal(validateCommandArgs({ command: 'File.Inspect' }).ok, false);
  assert.equal(validateCommandArgs(
    { command: 'file.inspect', payload: [1] }).ok, false);
  assert.equal(validateCommandArgs(
    { command: 'file.inspect', payload: { file: {} } }).ok, true);
  // multi-dot namespace + command_id uuid
  assert.equal(validateCommandArgs({ command: 'a.b.c' }).ok, true);
  assert.equal(validateCommandArgs(
    { command: 'file.inspect', command_id: 'not-uuid' }).ok, false);
  assert.equal(validateCommandArgs(
    { command: 'file.inspect',
      command_id: '8f3d2c10-6b4a-4e21-9c77-2a1b9d5f3e40' }).ok, true);
});

test('module registry co 7 muc theo spec §6, office placeholder', () => {
  const mods = listModules();
  assert.equal(mods.length, 7);
  for (const id of ['upload', 'document-review', 'excel-word', 'search',
                    'status', 'settings', 'office']) {
    assert.ok(mods.some((m) => m.id === id), `thieu module ${id}`);
  }
  const office = mods.find((m) => m.id === 'office');
  assert.equal(office.status, 'unavailable');
  assert.equal(office.reason, 'not_implemented');
});

test('moduleForCommand map namespace dung module', () => {
  assert.equal(moduleForCommand('file.inspect').id, 'upload');
  assert.equal(moduleForCommand('notary.ocr_analyze').id, 'document-review');
  assert.equal(moduleForCommand('unknown.thing'), null);
});

test('submitCommand tu choi khi sidecar chua ready', async () => {
  const deps = {
    sidecar: { state: 'starting', client: null, status: () => ({}) },
    tracker: { track() {} },
    pickFiles: async () => [],
    logger: { error() {} },
  };
  const r = await HANDLERS['desktop.v1.submitCommand'](
    deps, { command: 'file.inspect', payload: {} });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'engine_unavailable');
});

test('submitCommand tu choi command khong thuoc module nao', async () => {
  const deps = {
    sidecar: { state: 'ready', client: {}, status: () => ({}) },
    tracker: { track() {} },
    pickFiles: async () => [],
    logger: { error() {} },
  };
  const r = await HANDLERS['desktop.v1.submitCommand'](
    deps, { command: 'hack.run', payload: {} });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'command_unknown');
});
