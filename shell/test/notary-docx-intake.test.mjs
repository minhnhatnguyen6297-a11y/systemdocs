import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { webcrypto } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
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

test('failed and throwing detach restores source and dirty state for retry without restoring another case', async () => {
  for (const failure of ['result', 'exception', 'switch']) {
    let calls = 0;
    const model = M.createModel({client:{run:async(command,payload)=>{
      calls++;
      if (calls === 1) {
        if (failure === 'switch') { model.newDraft(); return {ok:false,error:{code:'conflict'}}; }
        if (failure === 'exception') throw new Error('interrupted');
        return {ok:false,error:{code:'conflict',message:'Thử lại'}};
      }
      return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
    }}});
    model.newDraft(); model.state.caseId = 1; model.state.revision = 2;
    model.state.stageDirty = false; model.state.diagramDirty = false; model.state.metaDirty = false;
    model.state.docxImport = {version:1,sources:[{source_id:uuid(),label:'A.docx',records:[],bindings:[]}]};
    const before = structuredClone(model.state.docxImport);
    const {ctx,box} = dialogContext(model); WORD.createWordDialog(ctx).open();
    await button(box,'Gỡ nguồn Word').onclick();
    if (failure === 'switch') { assert.deepEqual(model.state.docxImport.sources,[]); continue; }
    assert.deepEqual(model.state.docxImport,before); assert.equal(model.state.stageDirty,false);
    assert.ok(button(box,'Gỡ nguồn Word'));
    await button(box,'Gỡ nguồn Word').onclick();
    assert.deepEqual(model.state.docxImport.sources,[]); assert.equal(button(box,'Gỡ nguồn Word'),undefined);
  }
});

test('JSON download keeps original schema-valid result after review and invalid pending edits', async () => {
  const candidate = suggestion('person');
  candidate.fields.ngay_sinh = {raw_value:'1/2/1980',normalized_value:'1980-02-01',observation_state:'normalized',confidence:null,source_refs:[{kind:'docx',span:[20,30]}]};
  const result = {schema_version:'notary.case-drafting.v1',suggestions:[candidate],errors:[]};
  const original = structuredClone(result);
  const model = M.createModel({client:{run:async()=>({ok:true,data:result})}}); model.newDraft();
  const {ctx,box}=dialogContext(model);ctx.lib.faceEmpty=x=>x;
  INTAKE.createIntakeDialog(ctx).open();
  collect(box,e=>e.tagName==='TEXTAREA')[0].value='Phân tích'; await button(box,'Phân tích').onclick();
  model.reviewSuggestion(candidate.suggestion_id,'ho_ten','Tên mới');
  model.reviewSuggestion(candidate.suggestion_id,'ngay_sinh','31/02/1980');
  let blob;
  const create = URL.createObjectURL, revoke = URL.revokeObjectURL;
  URL.createObjectURL = b => {blob=b;return 'blob:synthetic';}; URL.revokeObjectURL=()=>{};
  try { button(box,'Tải JSON').onclick(); } finally { URL.createObjectURL=create;URL.revokeObjectURL=revoke; }
  const downloaded = await blob.text(); assert.deepEqual(JSON.parse(downloaded),original);
  assert.match(box.textContent,/sửa đổi được lưu vào Stage/);
  const root = fileURLToPath(new URL('../../',import.meta.url));
  execFileSync(process.env.NOTARY_TEST_PYTHON || 'python',['-c',
    "import json,sys; from pathlib import Path; from jsonschema import Draft7Validator; from referencing import Registry,Resource; p=Path(sys.argv[1])/'contracts/notary-case-drafting'; ss=[json.loads(f.read_text(encoding='utf-8')) for f in p.glob('*.schema.json')]; reg=Registry().with_resources([(s['$id'],Resource.from_contents(s)) for s in ss]); s=next(s for s in ss if s['$id'].endswith('/intake.schema.json')); Draft7Validator({'$ref':s['$id']+'#/definitions/result_data'},registry=reg).validate(json.load(sys.stdin))",root],{input:downloaded});
});

test('invalid source scalar and each land cell require correction; evidence shows span; over20 is capacity', () => {
  const model=M.createModel({client:{run:async()=>({ok:true})}});model.newDraft();
  const sug=suggestion();sug.fields.dien_tich={raw_value:'-50',normalized_value:null,source_refs:[{kind:'docx',core_state:'error',span:[10,13],raw_snippet:'-50'}]};
  sug.fields.land_rows.source_refs=[{core_state:'error',land_row:1,land_field:'dien_tich',span:[40,43],raw_snippet:'-50'}];
  sug.fields.land_rows.normalized_value='[{"loai_dat":"ONT","dien_tich":null}]';model.state.suggestions.push(sug);
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
  assert.equal(model.reviewSuggestion(sug.suggestion_id,'dien_tich','-50'),false);
  assert.equal(model.reviewSuggestion(sug.suggestion_id,'dien_tich','1.234,5'),true);
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
  const {ctx,box}=dialogContext(model);INTAKE.createIntakeDialog(ctx).open();assert.match(box.textContent,/vị trí 40–43/);
  assert.equal(model.reviewSuggestion(sug.suggestion_id,'land_rows','[{"loai_dat":"ONT","dien_tich":25}]',{identity:[1],cell:'1:dien_tich'}),true);
  assert.equal(sug.fields.dien_tich.normalized_value,1234.5);
  assert.equal(model.acceptSuggestion(sug.suggestion_id).land_rows[0].dien_tich,25);
  const many=suggestion();many.fields.land_rows.normalized_value=JSON.stringify(Array.from({length:21},()=>({loai_dat:'ONT',dien_tich:1})));
  model.state.suggestions.push(many);assert.equal(model.acceptSuggestion(many.suggestion_id),null);assert.match(model.state.notice,/tối đa 20/);
});

test('binding save failure restores clean context, retains choices and allows retry; selection locks during save', async () => {
  let finish, commits = 0;
  const sourceId = uuid();
  const proposal = {candidate_id:uuid(), occurrence_id:uuid(), field_key:'ho_ten', slot:'[Người 1 - Họ tên]',
    raw_snippet:'Tên gốc', row_id:uuid(), row_label:'Tên đã lưu', value:'Tên đã lưu', supported:true, selected:false};
  const model = M.createModel({client:{run:async(command,payload)=>{
    if(command === 'notary.word_export_options') return {ok:true,data:{documents:[{document_key:'original.docx',ready:true}], binding_proposals:[{...proposal,selected:commits > 1}]}};
    commits++;
    if(commits === 1) return new Promise(resolve=>{finish=resolve;});
    return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
  }}});
  model.newDraft(); model.state.caseId=1; model.state.revision=2;
  model.state.stageDirty=false;model.state.diagramDirty=false;model.state.metaDirty=false;
  model.state.docxImport={version:1,sources:[{source_id:sourceId,label:'A.docx',records:[],bindings:[]}]};
  const before=structuredClone(model.state.docxImport);
  const {ctx,box}=dialogContext(model);WORD.createWordDialog(ctx).open();
  await button(box,'Dùng hợp đồng Word đã nhập').onclick();
  const choice=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc'))[0];
  choice.checked=true;choice.onchange();
  const pending=button(box,'Xác nhận và lưu').onclick();
  assert.equal(choice.disabled,true);
  finish({ok:false,error:{code:'file_locked',message:'Thử lại'}});await pending;
  assert.equal(model.state.stageDirty,false);
  assert.deepEqual(model.state.docxImport,before);
  assert.equal(choice.checked,true);assert.equal(choice.disabled,false);
  await button(box,'Xác nhận và lưu').onclick();
  assert.equal(commits,2);assert.equal(model.state.docxImport.sources[0].bindings.length,1);
  assert.equal(choice.checked,true);assert.equal(choice.disabled,false);
});

test('invalid numeric land edits block acceptance until corrected and preserve other reviewed cells', () => {
  const model=M.createModel({client:{run:async()=>({ok:true})}});model.newDraft();
  const sug=suggestion();model.state.suggestions.push(sug);
  const {ctx,box}=dialogContext(model);INTAKE.createIntakeDialog(ctx).open();
  const type=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Loại đất')[0];
  type.value='CLN';type.onchange();
  const area=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Diện tích')[0];
  for(const invalid of ['-1','Infinity','NaN','1e309']) {
    area.value=invalid;area.onchange();
    assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
    assert.equal(area.value,invalid);
    assert.equal(area.getAttribute('aria-invalid'),'true');
    assert.match(box.textContent,/Diện tích cần/);
  }
  area.value='25.5';area.onchange();
  assert.deepEqual(sug.fields.land_rows.reviewed_cells,['1:loai_dat','1:dien_tich']);
  assert.equal(model.acceptSuggestion(sug.suggestion_id).land_rows[0].dien_tich,25.5);
});

test('later intake success, failure and cancel retain earlier cards and pending typed reviews', async () => {
  const first=suggestion('person'), second=suggestion('person');let calls=0;
  const model=M.createModel({client:{run:async()=>{
    calls++;
    if(calls<3) return {ok:true,data:{suggestions:[calls===1?first:second],errors:[]}};
    return {ok:false,error:{code:calls===3?'intake.parse_failed':'user_canceled',message:'Nguồn lỗi'}};
  }}});model.newDraft();
  const {ctx,box}=dialogContext(model);ctx.lib.faceEmpty=x=>x;ctx.face=x=>ctx.h('div','error',x);INTAKE.createIntakeDialog(ctx).open();
  const ta=collect(box,e=>e.tagName==='TEXTAREA')[0];
  ta.value='Lần một';await button(box,'Phân tích').onclick();
  const input=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Kiểm tra Họ tên')[0];
  input.value='Đang sửa chưa rời ô';
  for(let n=2;n<=4;n++) {
    ta.value=`Lần ${n}`;await button(box,'Phân tích').onclick();
    assert.equal(collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Kiểm tra Họ tên')[0],input);
    assert.equal(input.value,'Đang sửa chưa rời ô');
    assert.equal(collect(box,e=>e.className==='cd-suggest-card').length,2);
  }
});

test('reopening Intake exposes pending ambiguity for correction without another analysis', () => {
  let backendCalls=0;
  const model=M.createModel({client:{run:async()=>{backendCalls++;return {ok:true};}}});model.newDraft();
  const sug=suggestion('asset',true);model.state.suggestions.push(sug);
  const first=dialogContext(model);INTAKE.createIntakeDialog(first.ctx).open();
  const badArea=collect(first.box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Diện tích')[0];
  badArea.value='-5';badArea.onchange();
  // Leave the original dialog without accepting, then reopen using the same workspace tray.
  button(first.box,'Đóng').onclick();
  const reopened=dialogContext(model);INTAKE.createIntakeDialog(reopened.ctx).open();
  assert.equal(collect(reopened.box,e=>e.className==='cd-suggest-card').length,1);
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
  const area=collect(reopened.box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Diện tích')[0];
  assert.equal(area.value,'-5');assert.match(reopened.box.textContent,/Diện tích cần/);
  area.value='10';area.onchange();
  const serial=collect(reopened.box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Kiểm tra Serial giấy chứng nhận')[0];
  serial.value='YY123456';serial.onchange();
  button(reopened.box,'Đưa vào Stage').onclick();
  assert.equal(model.state.stage.assets[0].so_serial,'YY123456');
  assert.equal(model.state.suggestions.length,0);assert.equal(backendCalls,0);
});

test('old original export returns stale and cannot clear busy or results of new case export', async () => {
  const resolves=[];
  const model=M.createModel({client:{run:()=>new Promise(resolve=>resolves.push(resolve))}});
  model.newDraft();model.state.caseId=1;
  model.state.stageDirty=false;model.state.diagramDirty=false;
  const old=model.exportWord(['original.docx'],{}, {originalSourceId:uuid()});
  model.newDraft();model.state.caseId=2;
  model.state.stageDirty=false;model.state.diagramDirty=false;
  const current=model.exportWord(['original.docx'],{}, {originalSourceId:uuid()});
  resolves[0]({ok:true,data:{documents:[{document_key:'old',status:'saved'}]}});
  assert.equal((await old).stale,true);
  assert.equal(model.state.wordBusy,true);assert.equal(model.state.wordResult,null);
  resolves[1]({ok:true,data:{documents:[{document_key:'current',status:'saved'}]}});await current;
  assert.equal(model.state.wordBusy,false);assert.equal(model.state.wordResult.documents[0].document_key,'current');
});

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
  const dateInput=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Kiểm tra Ngày sinh')[0];
  dateInput.value='31/02/1980'; dateInput.onchange();
  assert.equal(sug.fields.ngay_sinh.normalized_value,null);
  assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
  assert.equal(model.state.stage.people.length,0);
  assert.equal(model.state.suggestions.length,1);
  assert.match(box.textContent,/Ngày không hợp lệ/);
  assert.equal(dateInput.getAttribute('aria-invalid'),'true');
  dateInput.value='2/3/1980'; dateInput.onchange();
  assert.equal(dateInput.getAttribute('aria-invalid'),'false');
  assert.equal(model.acceptSuggestion(sug.suggestion_id).ngay_sinh,'1980-03-02');
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
  assert.ok(button(box,'Xác nhận và lưu'),'mapping remains available after save');
  assert.equal(collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc')).length,1);
  await button(box,'Gỡ nguồn Word: Mẫu B.docx').onclick();
  assert.equal(calls.length,2);
  assert.match(box.textContent,/Dùng hợp đồng Word đã nhập: Mẫu A.docx/);
});

test('detach holds the save lock until commit finishes', async () => {
  let finish; let detachCount=0, commitCount=0;
  const model={state:{docxImport:{sources:[{source_id:uuid(),label:'A.docx'},{source_id:uuid(),label:'B.docx'}]},
    committedCaseInfo:{},caseInfo:{},wordOptions:[]},canWrite:()=>true,hasUnsaved:()=>false,
    detachOriginalSource:()=>{detachCount++;return true;},
    commitStage:()=>{commitCount++;return new Promise(resolve=>{finish=resolve;});}};
  const {ctx,box}=dialogContext(model);WORD.createWordDialog(ctx).open();
  const pending=button(box,'Gỡ nguồn Word: A.docx').onclick();
  await button(box,'Gỡ nguồn Word: B.docx').onclick();
  assert.equal(detachCount,1);assert.equal(commitCount,1);
  finish({ok:true});await pending;
  assert.match(box.textContent,/B.docx/);
});

test('localized area evidence uses complete number normalization', () => {
  const model=M.createModel({client:{run:async()=>({ok:true})}});model.newDraft();
  const sug=suggestion();sug.fields.land_rows.source_refs=[{core_state:'ambiguous',land_row:1,land_field:'dien_tich',raw_snippet:'1.234,5'}];
  model.state.suggestions.push(sug);const {ctx,box}=dialogContext(model);INTAKE.createIntakeDialog(ctx).open();
  collect(box,e=>e.tagName==='BUTTON' && e.textContent==='Chọn giá trị này').at(-1).onclick();
  assert.equal(model.acceptSuggestion(sug.suggestion_id).land_rows[0].dien_tich,1234.5);
});

test('localized typed area survives text input and deleting all land rows commits empty identity', async () => {
  const calls=[];
  const model=M.createModel({client:{run:async(command,payload)=>{
    calls.push(payload);return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
  }}});model.newDraft();
  const sug=suggestion();model.state.suggestions.push(sug);
  const {ctx,box}=dialogContext(model);INTAKE.createIntakeDialog(ctx).open();
  const area=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Diện tích')[0];
  assert.equal(area.type,'text');assert.equal(area.getAttribute('inputmode'),'decimal');
  area.value='1.234,5';area.onchange();
  assert.equal(JSON.parse(sug.fields.land_rows.normalized_value)[0].dien_tich,1234.5);
  button(box,'Bỏ dòng').onclick();
  const row=model.acceptSuggestion(sug.suggestion_id);
  assert.ok(row);assert.deepEqual(row.land_rows,[]);
  assert.deepEqual(model.state.docxImport.sources[0].records[0].land_rows,[]);
  model.state.caseId=1;model.state.revision=2;await model.commitStage();
  assert.deepEqual(calls[0].stage.assets[0].land_rows,[]);
  assert.deepEqual(calls[0].docx_import.sources[0].records[0].land_rows,[]);
});

test('invalid source dates block accept until correction then commit canonical date with original evidence', async () => {
  for(const raw of ['31/02/1980','1980-02-31']) {
    let saved;
    const model=M.createModel({client:{run:async(_command,payload)=>{
      saved=payload;return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
    }}});model.newDraft();
    const sug=suggestion('person');sug.fields.ngay_sinh={raw_value:raw,normalized_value:null,
      source_refs:[{kind:'docx',core_state:'error',raw_snippet:raw}]};model.state.suggestions.push(sug);
    assert.equal(model.acceptSuggestion(sug.suggestion_id),null);
    const {ctx,box}=dialogContext(model);INTAKE.createIntakeDialog(ctx).open();
    const date=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')==='Kiểm tra Ngày sinh')[0];
    date.value='1980-02-29';date.onchange();
    assert.equal(model.acceptSuggestion(sug.suggestion_id).ngay_sinh,'1980-02-29');
    assert.equal(sug.fields.ngay_sinh.raw_value,raw);
    model.state.caseId=1;model.state.revision=2;await model.commitStage();
    assert.equal(saved.stage.people[0].ngay_sinh,'1980-02-29');
  }
});

test('saved bindings survive options reload failure and source retry; stale source proposals disappear immediately', async () => {
  for(const failure of ['result','throw']) {
    let loads=0, finish;
    const id=uuid(), proposal={candidate_id:uuid(),occurrence_id:uuid(),field_key:'ho_ten',slot:'[Người 1 - Họ tên]',
      raw_snippet:'Tên gốc',row_id:uuid(),row_label:'Tên đã lưu',value:'Tên đã lưu',supported:true,selected:false};
    const model=M.createModel({client:{run:async(command,payload)=>{
      if(command==='notary.word_export_options') {
        loads++;
        if(loads===2) {if(failure==='throw') throw new Error('reload failed');return {ok:false,error:{code:'reload_failed'}};}
        if(loads===3) return new Promise((resolve,reject)=>{finish=()=>failure==='throw'
          ? reject(new Error('retry failed')) : resolve({ok:false,error:{code:'retry_failed'}});});
        return {ok:true,data:{documents:[{document_key:'original.docx',ready:true}],binding_proposals:[{...proposal,selected:loads>3}]}};
      }
      return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
    }}});model.newDraft();model.state.caseId=1;model.state.revision=2;
    model.state.stageDirty=false;model.state.diagramDirty=false;model.state.metaDirty=false;
    model.state.docxImport={version:1,sources:[{source_id:id,label:'A.docx',records:[],bindings:[]}]};
    const {ctx,box}=dialogContext(model);const notices=[];ctx.notify=t=>notices.push(t);WORD.createWordDialog(ctx).open();
    await button(box,'Dùng hợp đồng Word đã nhập').onclick();
    const choice=collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc'))[0];
    choice.checked=true;choice.onchange();await button(box,'Xác nhận và lưu').onclick();
    assert.equal(model.state.revision,3);assert.equal(model.state.stageDirty,false);
    assert.equal(model.state.docxImport.sources[0].bindings.length,1);
    assert.match(box.textContent,/Đã lưu vị trí Word, nhưng chưa tải lại/);
    assert.ok(notices.some(t=>/Đã lưu.*thất bại/.test(t)));
    assert.equal(button(box,'Xác nhận và lưu'),undefined);
    assert.deepEqual(model.state.wordBindingProposals,[]);
    const pending=button(box,'Dùng hợp đồng Word đã nhập').onclick();
    assert.match(box.textContent,/Đang tải/);assert.doesNotMatch(box.textContent,/Tên gốc →/);
    assert.equal(button(box,'Xuất').disabled,true);finish();await pending;
    assert.doesNotMatch(box.textContent,/Tên gốc →/);assert.match(box.textContent,/chọn lại nguồn để thử lại/);
    await button(box,'Dùng hợp đồng Word đã nhập').onclick();
    assert.ok(button(box,'Xác nhận và lưu'));
    assert.equal(collect(box,e=>e.tagName==='INPUT' && e.getAttribute('aria-label')?.includes('Tên gốc'))[0].checked,true);
  }
});

test('real model commit and get restore original land identity after server removes UI-only keys', async () => {
  let saved, revision=1;const calls=[];
  const model=M.createModel({client:{run:async(command,payload)=>{
    calls.push([command,payload]);
    if(command==='notary.workspace_commit_stage'){
      assert.equal(payload.stage.assets[0].land_rows[0]._source_land_row,undefined);
      saved=structuredClone({stage:payload.stage,docx_import:payload.docx_import});revision++;
      return {ok:true,data:{...saved,revision}};
    }
    return {ok:true,data:{...structuredClone(saved),case:{id:1,revision,case_type:'inheritance',locked:false}}};
  }}});model.newDraft();
  const sug=suggestion();sug.fields.land_rows.land_identity=[21];model.state.suggestions.push(sug);
  const row=model.acceptSuggestion(sug.suggestion_id);model.state.caseId=1;model.state.revision=1;
  await model.commitStage();
  assert.equal(model.state.stage.assets[0].land_rows[0]._source_land_row,21);
  await model.openCase(1);
  assert.equal(model.state.stage.assets[0].land_rows[0]._source_land_row,21);
  model.updateAssetField(row.row_id,'land_rows',[{...model.state.stage.assets[0].land_rows[0],dien_tich:77}]);
  await model.commitStage();
  assert.deepEqual(saved.docx_import.sources[0].records[0].land_rows,[21]);
  assert.equal(saved.stage.assets[0].land_rows[0].dien_tich,77);
  assert.deepEqual(calls.map(c=>c[0]),['notary.workspace_commit_stage','notary.workspace_get','notary.workspace_commit_stage']);
});

test('case switch during saved mapping reload never updates the new case dialog state', async () => {
  let finish,loads=0;
  const id=uuid(),proposal={candidate_id:uuid(),occurrence_id:uuid(),field_key:'ho_ten',slot:'[Người 1 - Họ tên]',
    raw_snippet:'Tên gốc',row_id:uuid(),row_label:'Tên đã lưu',value:'Tên đã lưu',supported:true};
  const model=M.createModel({client:{run:async(command,payload)=>{
    if(command==='notary.word_export_options') {
      if(++loads===2) return new Promise(resolve=>{finish=resolve;});
      return {ok:true,data:{documents:[],binding_proposals:[proposal]}};
    }
    return {ok:true,data:{revision:3,stage:payload.stage,docx_import:payload.docx_import}};
  }}});model.newDraft();model.state.caseId=1;model.state.revision=2;
  model.state.stageDirty=false;model.state.diagramDirty=false;model.state.metaDirty=false;
  model.state.docxImport={version:1,sources:[{source_id:id,label:'A.docx',records:[],bindings:[]}]};
  const {ctx,box}=dialogContext(model);const notices=[];ctx.notify=t=>notices.push(t);WORD.createWordDialog(ctx).open();
  await button(box,'Dùng hợp đồng Word đã nhập').onclick();
  const pending=button(box,'Xác nhận và lưu').onclick();
  await Promise.resolve();await Promise.resolve();
  model.newDraft();model.state.caseId=2;model.state.revision=7;
  model.state.wordOptions=[{document_key:'new-case.docx',ready:true}];
  finish({ok:false,error:{code:'reload_failed'}});await pending;
  assert.equal(model.state.revision,7);assert.deepEqual(model.state.docxImport.sources,[]);
  assert.equal(model.state.wordOptions[0].document_key,'new-case.docx');
  assert.deepEqual(notices,[]);assert.doesNotMatch(box.textContent,/Đã lưu vị trí Word, nhưng/);
});
