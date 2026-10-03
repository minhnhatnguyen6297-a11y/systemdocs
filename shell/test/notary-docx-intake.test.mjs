import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { webcrypto } from 'node:crypto';
import { makeDom, collect } from './dom-stub.mjs';
const require = createRequire(import.meta.url);
const M = require('../src/renderer/notary/case-drafting-model.js');
const INTAKE = require('../src/renderer/notary/intake-dialog.js');
const WORD = require('../src/renderer/notary/word-export-dialog.js');
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const uuid = () => webcrypto.randomUUID();

function suggestion(target = 'asset', ambiguous = false) {
  const sourceId = uuid(), candidate = uuid();
  return { suggestion_id: candidate, source_id: uuid(), target, warnings: [], fields: {
    [target === 'person' ? 'ho_ten' : 'so_serial']: { raw_value: 'ZZ123456', normalized_value: ambiguous ? null : 'ZZ123456',
      observation_state: 'observed', confidence: null, source_refs: [{ kind: 'docx', source_id: sourceId,
        candidate_id: candidate, source_sha256: 'a'.repeat(64), occurrence_id: uuid(), core_state: ambiguous ? 'ambiguous' : 'matched',
        raw_snippet: 'ZZ123456', span: [0, 8], docx_refs: [] }] },
    ...(target === 'asset' ? { land_rows: { raw_value: 'ONT', normalized_value: '[{"loai_dat":"ONT","dien_tich":10,"thoi_han":"Lâu dài"}]', source_refs: [] } } : {}),
  } };
}

test('capacity retains cards; ambiguous value requires review; land rows decode and source context travels on create', async () => {
  const calls = [];
  const model = M.createModel({ client: { run: async (command, payload) => {
    calls.push([command, payload]); return { ok: false, error: { code: 'stage_validation_error' } };
  } } });
  model.newDraft('inheritance');
  const candidate = suggestion('asset', true); model.state.suggestions.push(candidate);
  assert.equal(model.acceptSuggestion(candidate.suggestion_id), null);
  assert.equal(model.state.suggestions.length, 1);
  model.reviewSuggestion(candidate.suggestion_id, 'so_serial', 'YY123456');
  const row = model.acceptSuggestion(candidate.suggestion_id);
  assert.equal(row.so_serial, 'YY123456');
  assert.equal(row.land_rows[0].loai_dat, 'ONT');
  model.addAsset({ so_serial: 'AA123456' }); model.addAsset({ so_serial: 'BB123456' });
  const overflow = suggestion(); model.state.suggestions.push(overflow);
  assert.equal(model.acceptSuggestion(overflow.suggestion_id), null);
  assert.equal(model.state.suggestions.length, 1);
  await model.saveDraft();
  assert.equal(calls[0][1].docx_import.sources[0].records[0].row_id, row.row_id);
  assert.equal(candidate.fields.so_serial.raw_value, 'ZZ123456');
  model.newDraft(); assert.deepEqual(model.state.docxImport.sources, []);
});

test('case switch ignores late intake response; original export blocks uncommitted rows', async () => {
  let finish;
  const model = M.createModel({ client: { run: () => new Promise((resolve) => { finish = resolve; }) } });
  model.newDraft();
  const pending = model.intakeAnalyze([{ kind: 'docx' }]);
  model.newDraft(); finish({ ok: true, data: { suggestions: [suggestion()] } });
  const result = await pending;
  assert.equal(result.stale, true);
  assert.deepEqual(model.state.suggestions, []);
});

function dialogContext(model) {
  const { document } = makeDom(); globalThis.document = document;
  const box = document.createElement('div');
  const ctx = { model, lib: { faceError: (e) => e.message || e.code }, face: (x) => x,
    h: (tag, cls = '', text = '') => { const e = document.createElement(tag); e.className = cls; e.textContent = text; return e; },
    btn: (text, cls, action) => { const e = document.createElement('button'); e.textContent = text; e.onclick = action; return e; },
    openModal: (render) => render(box, () => {}), notify: () => {} };
  return { ctx, box };
}
const button = (box, label) => collect(box, (e) => e.tagName === 'BUTTON' && e.textContent.includes(label))[0];

test('review dialog displays evidence and capacity rejection keeps the visible card', () => {
  const model = M.createModel({ client: { run: async () => ({ ok: true }) } }); model.newDraft();
  for (let i = 0; i < 3; i++) model.addAsset({ so_serial: 'AA123456' });
  model.state.suggestions.push(suggestion());
  const { ctx, box } = dialogContext(model); INTAKE.createIntakeDialog(ctx).open();
  assert.match(box.textContent, /Xem chữ gốc và vị trí/);
  button(box, 'Đưa vào Stage').onclick();
  assert.match(box.textContent, /Đưa vào Stage/);
  assert.equal(model.state.suggestions.length, 1);
});

test('original template mapping is explicitly selected and persisted before enabling export', async () => {
  const sourceId = uuid(); const calls = [];
  const proposal = { candidate_id: uuid(), occurrence_id: uuid(), field_key: 'ho_ten', slot: '[Người 1 - Họ tên]',
    raw_snippet: 'Tên gốc', row_id: uuid(), row_label: 'Tên đã sửa', value: 'Tên đã sửa', supported: true };
  const model = { state: { docxImport: { sources: [{ source_id: sourceId }] }, wordBindingProposals: [proposal],
      committedCaseInfo: {}, caseInfo: {}, wordOptions: [] },
    canWrite: () => true, hasUnsaved: () => false,
    loadWordOptions: async (_dir, id) => { calls.push(['load', id]); model.state.wordOptions = [{document_key:'original.docx',ready:false}]; return {ok:true}; },
    confirmOriginalBindings: (id, bindings) => { calls.push(['confirm', id, bindings]); return true; },
    commitStage: async () => { calls.push(['commit']); return {ok:true}; },
  };
  const { ctx, box } = dialogContext(model); WORD.createWordDialog(ctx).open();
  await button(box, 'Dùng hợp đồng Word đã nhập').onclick();
  assert.match(box.textContent, /Tên gốc → Tên đã sửa/);
  const choice = collect(box, (e) => e.tagName === 'INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc'))[0];
  assert.ok(!choice.checked, 'no implicit binding confirmation'); choice.checked = true;
  await button(box, 'Xác nhận và lưu').onclick();
  assert.deepEqual(calls.map((c) => c[0]), ['load','confirm','commit','load']);
});
