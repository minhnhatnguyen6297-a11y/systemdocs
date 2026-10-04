import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import crypto from 'node:crypto';
const require = createRequire(import.meta.url);
const { createModel } = require('../src/renderer/notary/case-drafting-model.js');
const pause = () => new Promise(resolve => setTimeout(resolve, 20));
function setup() {
  const calls = [];
  const pending = [];
  const client = { run(command, payload) {
    calls.push([command, payload]);
    return new Promise(resolve => pending.push(resolve));
  }};
  const model = createModel({ client, uuid: () => crypto.randomUUID(), addressDebounceMs: 0 });
  model.newDraft('inheritance');
  model.updateCaseMeta('ngay_lap_ho_so', '2026-10-04');
  const person = model.addPerson({ho_ten: 'Synthetic', dia_chi: '  Thôn A, Xã A, Tỉnh P  ', ngay_cap: '2020-01-01'});
  const asset = model.addAsset({dia_chi: 'Xã A, Tỉnh P', ngay_cap: '2021-01-01'});
  return { model, person, asset, calls, pending };
}
const answer = (historical = false) => ({ok: true, data: {
  schema_version: 'notary.address-lookup.v1', status: 'ambiguous', coverage: {historical},
  candidates: [{unit_id: 'B', commune: 'Xã B', province: 'Tỉnh P', address: 'Xã B, Tỉnh P', historical},
               {unit_id: 'C', commune: 'Xã C', province: 'Tỉnh P', address: 'Xã C, Tỉnh P', historical}] }});

test('background lookup never mutates source; explicit choice keeps original exact bytes and replaces suffix', async () => {
  const {model, person, pending} = setup();
  const original = person.dia_chi;
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  pending.shift()(answer()); await pause();
  assert.equal(person.dia_chi, original);
  assert.equal(model.applyAddressSuggestion('person', person.row_id, 'B'), true);
  assert.equal(person.dia_chi, original + ' (nay là Xã B, Tỉnh P)');
  model.ensureAddressSuggestion('person', person.row_id); await pause(); pending.shift()(answer()); await pause();
  model.applyAddressSuggestion('person', person.row_id, 'C');
  assert.equal(person.dia_chi, original + ' (nay là Xã C, Tỉnh P)');
});

for (const field of ['dia_chi', 'ngay_cap']) test('late response discarded after source ' + field + ' edit', async () => {
  const {model, person, pending} = setup();
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  const first = pending.shift();
  model.updatePersonField(person.row_id, field, field === 'dia_chi' ? 'Xã Changed, Tỉnh P' : '2022-01-01');
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  first(answer()); await pause();
  assert.equal(model.state.addressSuggestions['person:' + person.row_id].result, undefined);
  pending.shift()(answer()); await pause();
  assert.ok(model.state.addressSuggestions['person:' + person.row_id].result);
});

test('late response discarded after case date edit and case switch', async () => {
  const {model, person, pending} = setup();
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  const first = pending.shift();
  model.updateCaseMeta('ngay_lap_ho_so', '2025-10-04');
  first(answer()); await pause();
  assert.equal(model.state.addressSuggestions['person:' + person.row_id].result, undefined);
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  model.newDraft('inheritance');
  pending.shift()(answer()); await pause();
  assert.deepEqual(model.state.addressSuggestions, {});
});

test('model holding raw dd/mm/yyyy still sends ISO payload', async () => {
  const {model, person, calls, pending} = setup();
  // dateCellInput go raw vao model (MIN-136); lookup phai tu chuan hoa.
  model.updateCaseMeta('ngay_lap_ho_so', '04/10/2026');
  model.updatePersonField(person.row_id, 'ngay_cap', '01/06/2024');
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 'notary.address_lookup');
  assert.equal(calls[0][1].source_date, '2024-06-01');
  assert.equal(calls[0][1].target_date, '2026-10-04');
  pending.shift()(answer()); await pause();
});

test('posting uses selected land date; no background save or manual overwrite', async () => {
  const {model, asset, calls, pending} = setup();
  model.updateCaseMeta('noi_niem_yet', 'UBND manually entered');
  model.ensureAddressSuggestion('posting', asset.row_id); await pause();
  assert.equal(calls[0][1].source_date, '2021-01-01');
  assert.equal(calls[0][1].target_date, '2026-10-04');
  pending.shift()(answer()); await pause();
  assert.equal(model.state.caseInfo.noi_niem_yet, 'UBND manually entered');
  model.applyAddressSuggestion('posting', asset.row_id, 'C');
  assert.equal(model.state.caseInfo.noi_niem_yet, 'Xã C, Tỉnh P');
  assert.equal(calls.length, 1);
});

test('posting result cannot apply after manual value changes', async () => {
  const {model, asset, pending} = setup();
  model.ensureAddressSuggestion('posting', asset.row_id); await pause();
  pending.shift()(answer()); await pause();
  model.updateCaseMeta('noi_niem_yet', 'Manual new');
  assert.equal(model.applyAddressSuggestion('posting', asset.row_id, 'C'), false);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'Manual new');
});

test('death issuer independent explicit office/date; undated candidates cannot apply', async () => {
  const {model, person, calls, pending} = setup();
  model.updatePersonField(person.row_id, 'ngay_chet', '2020-01-01');
  model.ensureAddressSuggestion('issuer', person.row_id); await pause();
  assert.equal(calls.length, 0);
  model.updatePersonField(person.row_id, 'noi_cap', 'UBND xã A, tỉnh P');
  model.ensureAddressSuggestion('issuer', person.row_id); await pause();
  assert.equal(calls[0][1].source_date, '2020-01-01');
  assert.equal(calls[0][1].target_date, '2020-01-01');
  pending.shift()(answer()); await pause();
  assert.equal(model.applyAddressSuggestion('issuer', person.row_id, 'B'), false);
  assert.equal(person.noi_cap, 'UBND xã A, tỉnh P');
  model.updatePersonField(person.row_id, 'noi_cap', 'UBND xã Changed, tỉnh P');
  model.ensureAddressSuggestion('issuer', person.row_id); await pause();
  pending.shift()(answer(true)); await pause();
  assert.equal(model.applyAddressSuggestion('issuer', person.row_id, 'B'), true);
  assert.equal(person.noi_cap, 'UBND Xã B, Tỉnh P');
});

test('ignore during in-flight response stays dismissed', async () => {
  const {model, person, pending} = setup();
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  model.ignoreAddressSuggestion('person', person.row_id);
  // Response den sau khi Bo qua — khong duoc de len co ignored.
  pending.shift()(answer()); await pause();
  assert.deepEqual(model.state.addressSuggestions['person:' + person.row_id],
    { ignored: true });
  // Doi input → identity doi → suggestion moi duoc phep hien lai.
  model.updatePersonField(person.row_id, 'dia_chi', 'Xã Khác, Tỉnh P');
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  pending.shift()(answer()); await pause();
  assert.ok(model.state.addressSuggestions['person:' + person.row_id].result);
});

test('malformed lookup response never becomes an applicable result', async () => {
  const {model, person, pending} = setup();
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  // Thieu schema_version → hien loi, khong cho ap "undefined, undefined".
  pending.shift()({ok: true, data: {status: 'match', candidates: [{unit_id: 'B'}]}}); await pause();
  assert.ok(model.state.addressSuggestions['person:' + person.row_id].message);
  assert.equal(model.applyAddressSuggestion('person', person.row_id, 'B'), false);
});

test('paren inside destination name never duplicates suffix', async () => {
  const {model, person, pending} = setup();
  model.updatePersonField(person.row_id, 'dia_chi',
    'Thôn A, Xã A, Tỉnh P (nay là Xã Cũ (mới), Tỉnh P)');
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  pending.shift()(answer()); await pause();
  assert.equal(model.applyAddressSuggestion('person', person.row_id, 'B'), true);
  assert.equal(person.dia_chi.match(/nay là/g).length, 1);
  assert.ok(person.dia_chi.endsWith('(nay là Xã B, Tỉnh P)'));
});

test('issuer gate accepts unaccented "ubnd" spelling', async () => {
  const {model, person, calls} = setup();
  model.updatePersonField(person.row_id, 'ngay_chet', '2020-01-01');
  model.updatePersonField(person.row_id, 'noi_cap', 'ubnd xa A, tinh P');
  model.ensureAddressSuggestion('issuer', person.row_id); await pause();
  assert.equal(calls.length, 1,
    'gate phai nhan ca spelling khong dau nhu service normalize()');
});

test('missing full date blocks lookup; ignoring candidates leaves direct input intact', async () => {
  const {model, person, calls, pending} = setup();
  model.updatePersonField(person.row_id, 'ngay_cap', '2020');
  model.ensureAddressSuggestion('person', person.row_id); await pause();
  assert.equal(calls.length, 0);
  model.updatePersonField(person.row_id, 'ngay_cap', '2020-01-01');
  model.ensureAddressSuggestion('person', person.row_id); await pause(); pending.shift()(answer()); await pause();
  const source = person.dia_chi;
  model.ignoreAddressSuggestion('person', person.row_id);
  assert.equal(model.applyAddressSuggestion('person', person.row_id, 'B'), false);
  assert.equal(person.dia_chi, source);
});
