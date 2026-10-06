import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
import { makeDom, collect } from '../../shell/test/dom-stub.mjs';
const require = createRequire(import.meta.url);
const L=require('../../shell/src/renderer/lib.js');
const M=require('../../shell/src/renderer/notary/case-drafting-model.js');
const V=require('../../shell/src/renderer/notary/case-drafting-view.js');
const { document } = makeDom();
global.document=document;
global.window={G1_NOTARY_MODEL:M,G1_NOTARY_VIEW:V,
 G1_NOTARY_INTAKE:require('../../shell/src/renderer/notary/intake-dialog.js'),
 G1_NOTARY_DIAGRAM:require('../../shell/src/renderer/notary/relationship-diagram.js'),
 G1_NOTARY_WORD:require('../../shell/src/renderer/notary/word-export-dialog.js'),
 G1_NOTARY_ERRORS:require('../../shell/src/renderer/notary/error-catalog.js')};
const calls=[];
const client={run:async(cmd,payload)=>{calls.push([cmd,payload]);return {ok:true,data:{customers:[]}};}};
const model=M.createModel({client});
const view=V.createNotaryModuleView({model,lib:L,notify:()=>{},confirm:async()=>true,
 pickFiles:async()=>({ok:true,data:{files:[]}}),openPath:async()=>({ok:true}),
 registerDroppedFile:null,cancelJob:async()=>({ok:true}),runCommand:client.run});
document.body.append(view.el);
model.newDraft('inheritance');
model.addPerson({ho_ten:'Người sống mẫu',ngay_cap:'2024-12-13',ngay_chet:null,noi_cap:'Bộ Công an',dia_chi:null});
await new Promise(r=>setTimeout(r,15));
const fid=v=>collect(view.el,e=>e.dataset?.fid===v)[0];
const row=model.state.stage.people[0];
const result={living_person:{data:row,address_value:fid(`p:${row.row_id}:dia_chi`).value,
 issuer_value:fid(`p:${row.row_id}:noi_cap`)?.value,
 issuer_label:fid(`p:${row.row_id}:noi_cap`)?.getAttribute('aria-label')}};
let uq=fid('meta:nguoi_nhan_uy_quyen');
result.catalog={initial_disabled:fid('meta:uq_add_catalog').disabled};
uq.focus(); uq.value='Nguyễn Văn Danh Bạ';uq.oninput();
result.catalog.after_typing_disabled=fid('meta:uq_add_catalog').disabled;
uq.onchange();
result.catalog.after_change_disabled=fid('meta:uq_add_catalog').disabled;
document.activeElement=null;
result.catalog.after_focus_lost_disabled=fid('meta:uq_add_catalog').disabled;
model.dismissNotice();
result.catalog.after_unrelated_emit_disabled=fid('meta:uq_add_catalog').disabled;
result.catalog.calls=calls.map(c=>c[0]);
console.log(JSON.stringify(result,null,2));
writeFileSync('artifacts/investigation-20261004/ui-probes.json',JSON.stringify(result,null,2));
