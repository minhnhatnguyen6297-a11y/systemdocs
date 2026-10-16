import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const Ajv=require('ajv');
const base=new URL('../../contracts/notary-case-drafting/',import.meta.url);
const ajv=new Ajv({allErrors:true});
for(const name of ['common.schema.json','workspace.schema.json','draft-v2.schema.json','word-export.schema.json','workspace-convert-type.schema.json'])ajv.addSchema(JSON.parse(fs.readFileSync(new URL(name,base),'utf8')));
const payload=ajv.compile({$ref:'https://systemdocs/contracts/notary-case-drafting/workspace-convert-type.schema.json#/definitions/payload'});
const valid={case_id:1,base_revision:2,case_type:'inheritance',document_type:'thoa_thuan',confirm_diagram_reset:true,owner_row_id:'11111111-1111-4111-8111-111111111111'};
test('conversion schema requires explicit target enum, acknowledgement and domain-specific owner',()=>{
  assert.equal(payload(valid),true,JSON.stringify(payload.errors));
  for(const key of Object.keys(valid)) {const copy={...valid};delete copy[key];assert.equal(payload(copy),false,key);}
  for(const patch of [{document_type:'tang_cho'},{confirm_diagram_reset:false},{owner_row_id:null},{extra:1},{case_type:'other'}])assert.equal(payload({...valid,...patch}),false,JSON.stringify(patch));
  const two={...valid,case_type:'two_party',document_type:'dat_coc'};delete two.owner_row_id;
  assert.equal(payload(two),true,JSON.stringify(payload.errors));
  assert.equal(payload({...two,owner_row_id:valid.owner_row_id}),false);
});
