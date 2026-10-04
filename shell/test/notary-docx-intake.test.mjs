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

test('each ambiguous land cell requires its own review and deletion preserves original land identity', () => {
  const model = M.createModel({ client: { run: async () => ({ ok: true }) } }); model.newDraft();
  const sug = suggestion();
  sug.fields.land_rows.normalized_value = JSON.stringify([
    {loai_dat:null,dien_tich:null,thoi_han:'Lâu dài'}, {loai_dat:'CLN',dien_tich:20,thoi_han:'2050'}]);
  sug.fields.land_rows.source_refs = [
    {core_state:'ambiguous',land_row:1,land_field:'loai_dat',raw_snippet:'ONT'},
    {core_state:'ambiguous',land_row:1,land_field:'dien_tich',raw_snippet:'50'},
    {core_state:'ambiguous',land_row:2,land_field:'dien_tich',raw_snippet:'70'}];
  model.state.suggestions.push(sug);
  const {ctx,box} = dialogContext(model); INTAKE.createIntakeDialog(ctx).open();
  const firstType = collect(box, (e) => e.tagName==='INPUT' && e.getAttribute('aria-label')==='Loại đất')[0];
  firstType.value='ONT'; firstType.onchange();
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null, 'editing one cell cannot approve another');
  button(box,'Bỏ dòng').onclick();
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null, 'remaining ambiguous row still needs review');
  // The surviving row is original row 2; clicking original row 1 evidence must do nothing.
  const evidence = collect(box, e => e.tagName==='BUTTON' && e.textContent==='Chọn giá trị này');
  evidence[1].onclick();
  assert.deepEqual(JSON.parse(sug.fields.land_rows.normalized_value),[{loai_dat:'CLN',dien_tich:20,thoi_han:'2050'}]);
  evidence[3].onclick();
  const row=model.acceptSuggestion(sug.suggestion_id);
  assert.equal(row.land_rows[0].dien_tich,70);
  assert.deepEqual(model.state.docxImport.sources[0].records[0].land_rows,[2]);
  model.updateAssetField(row.row_id,'land_rows',[{...row.land_rows[0],dien_tich:80}]);
  assert.deepEqual(model.state.docxImport.sources[0].records[0].land_rows,[2]);
});

test('raw selected dates normalize before Stage and invalid dates stay unreviewed', () => {
  const model=M.createModel({client:{run:async()=>({ok:true})}}); model.newDraft();
  const sug=suggestion('person');
  sug.fields.ngay_sinh={raw_value:'1/2/1980',normalized_value:null,source_refs:[{kind:'docx',raw_snippet:'1/2/1980',core_state:'ambiguous'}]};
  model.state.suggestions.push(sug);
  const {ctx,box}=dialogContext(model); INTAKE.createIntakeDialog(ctx).open();
  collect(box,e=>e.tagName==='BUTTON' && e.textContent==='Chọn giá trị này')[1].onclick();
  assert.equal(sug.fields.ngay_sinh.normalized_value,'1980-02-01');
  assert.equal(model.reviewSuggestion(sug.suggestion_id,'ngay_sinh','31/02/1980'),false);
  assert.equal(model.acceptSuggestion(sug.suggestion_id).ngay_sinh,'1980-02-01');
});

test('ninth source cannot mutate Stage and explicit detach allows recovery with empty context on commit', async () => {
  const calls=[];
  const model=M.createModel({client:{run:async(command,payload)=>{calls.push([command,payload]);return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};}}});
  model.newDraft();
  for(let i=0;i<8;i++){const s=suggestion('person');model.state.suggestions.push(s); assert.ok(model.acceptSuggestion(s.suggestion_id));}
  const ninth=suggestion('person');model.state.suggestions.push(ninth);
  assert.equal(model.acceptSuggestion(ninth.suggestion_id),null);
  assert.equal(model.state.stage.people.length,8); assert.equal(model.state.suggestions.length,1);
  model.detachOriginalSource(model.state.docxImport.sources[0].source_id);
  assert.ok(model.acceptSuggestion(ninth.suggestion_id));
  assert.equal(model.state.stage.people.length,9);
  for(const s of [...model.state.docxImport.sources]) model.detachOriginalSource(s.source_id);
  model.state.caseId=1;model.state.revision=2;
  await model.commitStage();
  assert.deepEqual(calls.at(-1)[1].docx_import,{version:1,sources:[]});
});

test('dirty original export calls no backend; clean export includes source and saved revision', async () => {
  const calls=[];
  const model=M.createModel({client:{run:async(command,payload)=>{calls.push([command,payload]);return {ok:true,data:{documents:[]}};}}});
  model.newDraft();model.state.caseId=12;model.state.revision=7;
  const sourceId=uuid(); const dest={file_token:uuid()};
  model.state.stageDirty=true;
  assert.equal((await model.exportWord(['original.docx'],dest,{originalSourceId:sourceId})).ok,false);
  model.state.stageDirty=false;model.state.diagramDirty=true;
  assert.equal((await model.exportWord(['original.docx'],dest,{originalSourceId:sourceId})).ok,false);
  assert.equal(calls.length,0);
  model.state.diagramDirty=false;
  await model.exportWord(['original.docx'],dest,{originalSourceId:sourceId});
  assert.equal(calls[0][1].original_source_id,sourceId); assert.equal(calls[0][1].base_revision,7);
});

test('mapping reopens saved choices, disables empty slot with reason, clears all and identifies sources', async () => {
  const id=uuid(), calls=[];
  const proposals=[{candidate_id:uuid(),occurrence_id:uuid(),field_key:'ho_ten',slot:'[Người 1 - Họ tên]',
    raw_snippet:'Tên gốc',row_id:uuid(),row_label:'Tên đã lưu',value:'Tên đã lưu',supported:true,selected:true},
    {candidate_id:uuid(),occurrence_id:uuid(),field_key:'dia_chi',slot:'[Người 1 - Địa chỉ]',
      raw_snippet:'Nhà cũ',row_id:uuid(),row_label:'Tên đã lưu',value:'',supported:false,selected:false,reason:'Vị trí chưa có giá trị đã lưu'}];
  const model={state:{docxImport:{sources:[{source_id:id,label:'Mẫu A.docx'},{source_id:uuid(),label:'Mẫu B.docx'}]},
    wordBindingProposals:proposals,committedCaseInfo:{},caseInfo:{},wordOptions:[]},
    canWrite:()=>true,hasUnsaved:()=>false,
    loadWordOptions:async()=>{model.state.wordOptions=[{document_key:'original.docx',ready:true}];return {ok:true};},
    confirmOriginalBindings:(_id,bindings)=>{calls.push(bindings);return true;},commitStage:async()=>({ok:true}),
    detachOriginalSource:sourceId=>{calls.push(sourceId);return true;}};
  const {ctx,box}=dialogContext(model);WORD.createWordDialog(ctx).open();
  assert.match(box.textContent,/Mẫu A.docx/);assert.match(box.textContent,/Mẫu B.docx/);
  await button(box,'Dùng hợp đồng Word đã nhập: Mẫu A.docx').onclick();
  const choice=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc'))[0];
  const blank=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Nhà cũ'))[0];
  assert.equal(choice.checked,true);assert.equal(blank.disabled,true);
  assert.match(box.textContent,/Vị trí chưa có giá trị đã lưu/);
  choice.checked=false;
  choice.onchange();
  assert.equal(button(box,'Xuất').disabled,true,'unsaved choices cannot misdescribe the export');
  await button(box,'Xác nhận và lưu').onclick();
  assert.deepEqual(calls[0],[]);
  await button(box,'Gỡ nguồn Word: Mẫu B.docx').onclick();
  assert.equal(calls.length,2);
  assert.match(box.textContent,/Dùng hợp đồng Word đã nhập: Mẫu A.docx/);
});
