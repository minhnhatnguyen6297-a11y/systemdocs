import test from 'node:test';
import assert from 'node:assert/strict';

import { ALLOWLIST, HANDLERS, validateCommandArgs, resolveFileTokens }
  from '../src/main/ipc.js';
import { moduleForCommand, listModules } from '../src/main/registry.js';
import { makeFileTokenStore, pickedEntry }
  from '../src/main/file-tokens.js';

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

// ---------- opaque file token (MIN-112) ----------

function depsReady(captured) {
  return {
    sidecar: {
      state: 'ready', status: () => ({}),
      client: {
        submitCommand: async (command, payload, moduleId, commandId) => {
          captured.push({ command, payload, moduleId, commandId });
          return { job_id: 'j_t1', status: 'accepted' };
        },
      },
    },
    tracker: { track() {} },
    fileTokens: makeFileTokenStore(),
    pickFiles: async () => [],
    logger: { error() {} },
  };
}

test('fileTokenStore: issue/resolve tra FileRef; entry cho renderer khong co path', () => {
  const store = makeFileTokenStore();
  const stat = { isFile: () => true, isDirectory: () => false, size: 99 };
  const entry = pickedEntry(store, 'D:\\in\\anh1.png', stat);
  // entry di ve renderer: file_token + name + size + is_dir — KHONG path
  assert.ok(entry.file_token);
  assert.equal(entry.name, 'anh1.png');
  assert.equal(entry.size_bytes, 99);
  assert.equal(entry.is_dir, false);
  assert.equal('path' in entry, false);
  assert.equal('scope' in entry, false);
  // resolve tra FileRef that (scope machine_local)
  const ref = store.resolve(entry.file_token);
  assert.equal(ref.path, 'D:\\in\\anh1.png');
  assert.equal(ref.scope, 'machine_local');
  assert.equal(ref.size_bytes, 99);
  assert.equal(ref.is_dir, false);
  // token la → null
  assert.equal(store.resolve('khong-co'), null);
  // clear → token het han (window close/reload)
  store.clear();
  assert.equal(store.resolve(entry.file_token), null);
});

test('submitCommand thay file_token o sources[].file_ref (intake_analyze)', async () => {
  const captured = [];
  const deps = depsReady(captured);
  const t = deps.fileTokens.issue(
    { path: 'D:\\in\\a.png', size_bytes: 12, is_dir: false });
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'notary.intake_analyze',
    payload: {
      case_id: 42,
      sources: [
        { source_id: '11111111-1111-4111-8111-111111111111',
          kind: 'image', file_ref: { file_token: t } },
        { source_id: '22222222-2222-4222-8222-222222222222',
          kind: 'text', text: 'ghi chu' },
      ],
    } });
  assert.equal(r.ok, true);
  const sent = captured[0].payload;
  assert.equal(sent.sources[0].file_ref.path, 'D:\\in\\a.png');
  assert.equal(sent.sources[0].file_ref.scope, 'machine_local');
  assert.equal(sent.sources[0].file_ref.size_bytes, 12);
  assert.equal('file_token' in sent.sources[0].file_ref, false);
  assert.equal(sent.sources[1].kind, 'text');   // text source nguyen ven
});

test('submitCommand thay file_token o destination (word_export_batch)', async () => {
  const captured = [];
  const deps = depsReady(captured);
  const t = deps.fileTokens.issue(
    { path: 'D:\\out-dir', size_bytes: null, is_dir: true });
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'notary.word_export_batch',
    payload: { case_id: 42, document_keys: ['khai_nhan_di_san'],
               destination: { file_token: t } } });
  assert.equal(r.ok, true);
  const dest = captured[0].payload.destination;
  assert.equal(dest.path, 'D:\\out-dir');
  assert.equal(dest.scope, 'machine_local');
  assert.equal(dest.is_dir, true);
  assert.equal('file_token' in dest, false);
});

test('submitCommand tu choi token la/het han — validation_error, khong forward', async () => {
  const captured = [];
  const deps = depsReady(captured);
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'notary.intake_analyze',
    payload: { case_id: 42, sources: [
      { source_id: 'x', kind: 'image',
        file_ref: { file_token: 'deadbeef-0000-4000-8000-000000000000' } } ] } });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'validation_error');
  assert.equal(captured.length, 0);             // khong forward len sidecar
});

test('submitCommand tu choi FileRef tho {path} khong co file_token — khong forward', async () => {
  const captured = [];
  const deps = depsReady(captured);
  // Boundary cung (review MIN-112): renderer khong duoc tu khai raw path —
  // moi FileRef bat buoc qua token tu picker/drop.
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'file.inspect',
    payload: { file: { path: 'D:\\x', scope: 'machine_local' } } });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'validation_error');
  assert.equal(captured.length, 0);
  // raw path o sau trong mang/nested cung bi chan
  const r2 = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'notary.intake_analyze',
    payload: { case_id: 1, sources: [
      { source_id: 's', kind: 'image',
        file_ref: { path: 'D:\\evil.png', scope: 'machine_local' } } ] } });
  assert.equal(r2.ok, false);
  assert.equal(r2.error.code, 'validation_error');
  assert.equal(captured.length, 0);
});

test('submitCommand: node {file_token hop le, path gia} — resolve token, sibling path bi bo qua', async () => {
  const captured = [];
  const deps = depsReady(captured);
  const t = deps.fileTokens.issue({ path: 'D:\\real.png' });
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'file.inspect',
    payload: { file: { file_token: t, path: 'D:\\evil.png' } } });
  assert.equal(r.ok, true);
  assert.equal(captured[0].payload.file.path, 'D:\\real.png');
  assert.equal('file_token' in captured[0].payload.file, false);
});

test('resolveFileTokens: object co path string khong token → reject; path non-string qua duoc', () => {
  const store = makeFileTokenStore();
  assert.equal(
    resolveFileTokens(store, { f: { path: 'D:\\a' } }).ok, false);
  assert.equal(resolveFileTokens(store,
    { list: [{ file_ref: { path: 'D:\\a', scope: 'machine_local' } }] })
    .ok, false);
  // path khong phai string → khong phai FileRef-like, giu nguyen
  const ok = resolveFileTokens(store, { meta: { path: 5 } });
  assert.equal(ok.ok, true);
  assert.equal(ok.value.meta.path, 5);
});

test('submitCommand: payload thuong (khong file_token) nguyen ven', async () => {
  const captured = [];
  const deps = depsReady(captured);
  const r = await HANDLERS['desktop.v1.submitCommand'](deps, {
    command: 'notary.workspace_get', payload: { case_id: 42 } });
  assert.equal(r.ok, true);
  assert.deepEqual(captured[0].payload, { case_id: 42 });
});

test('pickFiles handler tra shape token; registerDroppedFile + setDirtyState co trong allowlist', async () => {
  assert.ok(ALLOWLIST.includes('desktop.v1.pickFiles'));
  assert.ok(ALLOWLIST.includes('desktop.v1.registerDroppedFile'));
  assert.ok(ALLOWLIST.includes('desktop.v1.setDirtyState'));
  const deps = {
    pickFiles: async (opts) => opts.directory
      ? [{ file_token: 't-dir', name: 'out', size_bytes: null,
           is_dir: true }]
      : [{ file_token: 't-f', name: 'a.png', size_bytes: 5,
           is_dir: false }],
    logger: { error() {} },
  };
  const r = await HANDLERS['desktop.v1.pickFiles'](deps, { directory: true });
  assert.equal(r.ok, true);
  assert.equal(r.data.files[0].is_dir, true);   // directory pick co is_dir
  assert.equal('path' in r.data.files[0], false);
});

test('registerDroppedFile handler: deps thieu → loi; deps co → tra token entry', async () => {
  const r0 = await HANDLERS['desktop.v1.registerDroppedFile'](
    { logger: { error() {} } }, { path: 'D:\\x.png' });
  assert.equal(r0.ok, false);
  const r = await HANDLERS['desktop.v1.registerDroppedFile']({
    registerDroppedFile: async (p) => ({ file_token: 't1', name: 'a.png',
      size_bytes: 1, is_dir: false, _p: p }),
    logger: { error() {} },
  }, { path: 'D:\\a.png' });
  assert.equal(r.ok, true);
  assert.equal(r.data.file.file_token, 't1');
  assert.equal(r.data.file._p, 'D:\\a.png');
  // loi ben trong → errEnvelope, khong throw
  const rErr = await HANDLERS['desktop.v1.registerDroppedFile']({
    registerDroppedFile: async () => {
      throw Object.assign(new Error('khong ton tai'),
                          { code: 'file_not_found' });
    },
    logger: { error() {} },
  }, { path: 'D:\\none.png' });
  assert.equal(rErr.ok, false);
  assert.equal(rErr.error.code, 'file_not_found');
});

test('registerDroppedFile: relative/UNC path bi tu choi truoc khi stat', async () => {
  let called = 0;
  const deps = { registerDroppedFile: async () => { called++; return null; },
                 logger: { error() {} } };
  for (const p of ['x.png', 'in\\a.png', '.\\a.png',
                   '\\\\server\\share\\a.png', '\\\\?\\UNC\\sv\\a.png',
                   '\\\\?\\D:\\a.png', '']) {
    const r = await HANDLERS['desktop.v1.registerDroppedFile'](
      deps, { path: p });
    assert.equal(r.ok, false, `path ${JSON.stringify(p)} phai bi tu choi`);
    assert.equal(r.error.code, 'validation_error');
  }
  assert.equal(called, 0);   // khong cham stat cho path khong hop le
  // path tuyet doi local hop le van qua
  const ok = await HANDLERS['desktop.v1.registerDroppedFile']({
    registerDroppedFile: async (p) =>
      ({ file_token: 't9', name: p, size_bytes: 1, is_dir: false }),
    logger: { error() {} },
  }, { path: 'D:\\in\\a.png' });
  assert.equal(ok.ok, true);
  assert.equal(ok.data.file.file_token, 't9');
});

test('openPath handler: ext ngoai whitelist bi tu choi — khong goi shell', async () => {
  let called = 0;
  const deps = { openPath: async () => { called++; return { opened: 1 }; },
                 logger: { error() {} } };
  for (const p of ['D:\\x\\evil.exe', 'D:\\x\\s.bat', 'D:\\x\\a.lnk',
                   'D:\\x\\run.ps1', 'D:\\x\\noext']) {
    const r = await HANDLERS['desktop.v1.openPath'](deps, { path: p });
    assert.equal(r.ok, false, `path ${p} phai bi chan`);
    assert.equal(r.error.code, 'open_failed');
  }
  assert.equal(called, 0);
  // ext tai lieu hop le van qua toi deps.openPath
  const ok = await HANDLERS['desktop.v1.openPath'](deps,
    { path: 'D:\\out\\a.DOCX' });
  assert.equal(ok.ok, true);
  assert.equal(ok.data.opened, 1);
  assert.equal(called, 1);
});

test('setDirtyState handler: ghi flag renderer dirty len deps.setDirty', async () => {
  let cur = null;
  const deps = { setDirty: (d) => { cur = d; }, logger: { error() {} } };
  const r = await HANDLERS['desktop.v1.setDirtyState'](deps, { dirty: true });
  assert.equal(r.ok, true);
  assert.equal(cur, true);
  await HANDLERS['desktop.v1.setDirtyState'](deps, { dirty: false });
  assert.equal(cur, false);
});

test('resolveFileTokens: nested/array — token o sau van duoc thay', () => {
  const store = makeFileTokenStore();
  const t = store.issue({ path: 'D:\\f.docx', size_bytes: 7 });
  const r = resolveFileTokens(store, {
    a: [{ b: { file_token: t } }],
    c: 'plain',
  });
  assert.equal(r.ok, true);
  assert.equal(r.value.a[0].b.path, 'D:\\f.docx');
  assert.equal(r.value.c, 'plain');
  const bad = resolveFileTokens(store, { x: { file_token: 'la' } });
  assert.equal(bad.ok, false);
});
