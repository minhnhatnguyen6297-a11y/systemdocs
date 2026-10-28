import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import crypto from 'node:crypto';
const require = createRequire(import.meta.url);
const { createModel } = require('../src/renderer/notary/case-drafting-model.js');

const pause = () => new Promise(resolve => setTimeout(resolve, 20));

async function setup() {
  const calls = [];
  const pending = [];
  const client = { run(command, payload) {
    calls.push([command, payload]);
    return new Promise(resolve => pending.push(resolve));
  }};
  const model = createModel({ client, uuid: () => crypto.randomUUID() });
  // Issue 13: newDraft đọc nguồn Done mới nhất trước khi 'ready'. Trả nguồn
  // rỗng rồi xóa lịch sử gọi để test chỉ thấy lệnh address_lookup.
  const opened = model.newDraft('inheritance');
  assert.deepEqual(calls.map(c => c[0]), ['notary.workspace_source_latest']);
  pending.shift()({ ok: true, data: { stage: { people: [], assets: [] } } });
  await opened;
  calls.length = 0;
  const person = model.addPerson({ ho_ten: 'Synthetic', dia_chi: 'Xa A, Tinh P' });
  const asset = model.addAsset({ dia_chi: 'Xa A, Tinh P' });
  return { model, person, asset, calls, pending };
}

const rowB = { unit_id: 'B', level: 'commune', name: 'Xa B',
  province: { unit_id: 'P', name: 'Tinh P' }, source_text: 'Xa B',
  display: 'xa B, tinh P', observation_id: 'obs-b', evidence: [] };
const rowC = { unit_id: 'C', level: 'commune', name: 'Xa C',
  province: { unit_id: 'P', name: 'Tinh P' }, source_text: 'Xa C',
  display: 'xa C, tinh P', observation_id: 'obs-c', evidence: [] };
const draftingFound = { ok: true, data: {
  schema_version: 'notary.address-lookup.v2', status: 'found',
  presentation: 'drafting', total: 2, results: [rowB, rowC],
  dataset_version: 'v2', revision: 1 } };
const draftingTooMany = { ok: true, data: {
  schema_version: 'notary.address-lookup.v2', status: 'too_many',
  presentation: 'drafting', total: 12, results: [],
  dataset_version: 'v2', revision: 1 } };
const fullFound = { ok: true, data: {
  schema_version: 'notary.address-lookup.v2', status: 'found',
  presentation: 'full', total: 2, results: [rowB, rowC],
  dataset_version: 'v2', revision: 1 } };

test('P5: changing source removes ready results without sending another lookup', async () => {
  const { model, person, calls, pending } = await setup();
  await tra(model, pending, 'person', person.row_id);
  model.updatePersonField(person.row_id, 'dia_chi', 'Query B');
  assert.equal(model.state.addressSlots['person:' + person.row_id].result, null);
  assert.equal(calls.length, 1);
});

test('P9: malformed v2 responses become communication errors', async () => {
  for (const change of [
    { presentation: 'full' }, { total: -1 }, { results: [null, rowC] },
    { results: [{ ...rowB, province: null }, rowC] }, { total: 3 },
    { status: 'unknown' }, { revision: -1 },
  ]) {
    const { model, person, pending } = await setup();
    await tra(model, pending, 'person', person.row_id,
      { ok: true, data: { ...draftingFound.data, ...change } });
    assert.equal(model.state.addressSlots['person:' + person.row_id].phase, 'error');
    assert.equal(model.state.addressSlots['person:' + person.row_id].result, undefined);
  }
});

test('P9: both full entry points reject wrong presentation and malformed rows', async () => {
  for (const change of [{ presentation: 'drafting' }, { results: [null, rowC] }]) {
    const { model, person, pending } = await setup();
    await tra(model, pending, 'person', person.row_id, draftingTooMany);
    model.openFullFromSlot('person', person.row_id);
    pending.shift()({ ok: true, data: { ...fullFound.data, ...change } });
    await pause();
    assert.equal(model.state.addressFull.phase, 'error');
    assert.equal(model.state.addressFull.result, null);
    model.requestFull('Full query');
    pending.shift()({ ok: true, data: { ...fullFound.data, ...change } });
    await pause();
    assert.equal(model.state.addressFull.phase, 'error');
    assert.equal(model.state.addressFull.result, null);
  }
});

async function tra(model, pending, kind, rowId, answer = draftingFound) {
  const p = model.requestLookup(kind, rowId);
  await pause();
  pending.shift()(answer);
  await p;
  await pause();
}

test('Tra sends drafting payload with live input text; re-Tra same text sends again', async () => {
  const { model, person, calls, pending } = await setup();
  await tra(model, pending, 'person', person.row_id);
  await tra(model, pending, 'person', person.row_id);
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[0], ['notary.address_lookup',
    { query: 'Xa A, Tinh P', presentation: 'drafting' }]);
  assert.deepEqual(calls[1], ['notary.address_lookup',
    { query: 'Xa A, Tinh P', presentation: 'drafting' }]);
  const slot = model.state.addressSlots['person:' + person.row_id];
  assert.equal(slot.phase, 'ready');
  assert.equal(slot.result.results.length, 2);
});

test('no auto lookup on edits; lookup never mutates rows or meta', async () => {
  const { model, person, asset, calls, pending } = await setup();
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa B, Tinh P');
  model.updateCaseMeta('noi_niem_yet', 'Manual value');
  await pause();
  assert.equal(calls.length, 0);
  const beforePerson = person.dia_chi;
  await tra(model, pending, 'person', person.row_id);
  assert.equal(person.dia_chi, beforePerson);
  assert.equal(asset.dia_chi, 'Xa A, Tinh P');
  assert.equal(model.state.caseInfo.noi_niem_yet, 'Manual value');
});

test('posting query uses the posting box itself, not an asset address', async () => {
  const { model, asset, calls, pending } = await setup();
  model.updateCaseMeta('noi_niem_yet', 'Xa Posting, Tinh P');
  model.updateAssetField(asset.row_id, 'dia_chi', 'Xa Asset Khac, Tinh P');
  await tra(model, pending, 'posting', 'posting');
  assert.deepEqual(calls[0][1],
    { query: 'Xa Posting, Tinh P', presentation: 'drafting' });
});

test('issuer query uses the deceased address, not the noi_cap box', async () => {
  const { model, person, calls, pending } = await setup();
  model.updatePersonField(person.row_id, 'ngay_chet', '2020-01-01');
  model.updatePersonField(person.row_id, 'noi_cap', 'UBND Xa Cu, Tinh P');
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa Moi, Tinh P');
  await tra(model, pending, 'issuer', person.row_id);
  assert.deepEqual(calls[0][1],
    { query: 'Xa Moi, Tinh P', presentation: 'drafting' });
});

test('stale response dropped on new Tra, on source edit, and on A-B-A', async () => {
  const { model, person, pending } = await setup();
  const key = 'person:' + person.row_id;
  const first = model.requestLookup('person', person.row_id);
  await pause();
  const resolveFirst = pending.shift();
  const second = model.requestLookup('person', person.row_id);
  await pause();
  resolveFirst(draftingFound);
  await first;
  await pause();
  assert.ok(model.state.addressSlots[key].phase !== 'ready' ||
    model.state.addressSlots[key].result !== draftingFound.data);
  pending.shift()(draftingFound);
  await second;
  await pause();
  assert.equal(model.state.addressSlots[key].result, draftingFound.data);

  // A -> B -> A: the old A response stays invalid.
  const a1 = model.requestLookup('person', person.row_id);
  await pause();
  const resolveA1 = pending.shift();
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa B, Tinh P');
  await pause();
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa A, Tinh P');
  await pause();
  resolveA1(draftingFound);
  await a1;
  await pause();
  assert.ok(!model.state.addressSlots[key].result ||
    model.state.addressSlots[key].result !== draftingFound.data);
});

test('switching case drops in-flight lookup', async () => {
  const { model, person, pending } = await setup();
  const p = model.requestLookup('person', person.row_id);
  await pause();
  const resolve = pending.shift();
  model.newDraft('inheritance');
  resolve(draftingFound);
  await p;
  await pause();
  assert.deepEqual(model.state.addressSlots, {});
  assert.equal(model.state.addressFull, null);
});

test('too_many confirm flow: full uses captured query; overlay edit only sends on Tra', async () => {
  const { model, person, calls, pending } = await setup();
  await tra(model, pending, 'person', person.row_id, draftingTooMany);
  assert.equal(calls.length, 1);
  const opened = model.openFullFromSlot('person', person.row_id);
  assert.equal(opened.ok, true);
  await pause();
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[1][1],
    { query: 'Xa A, Tinh P', presentation: 'full' });
  // Source changed while the question was open -> stale, no overlay.
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa Khac, Tinh P');
  const stale = model.openFullFromSlot('person', person.row_id);
  assert.deepEqual(stale, { ok: false, stale: true });
  assert.equal(calls.length, 2);
  pending.shift()(fullFound); // drain the first full request (dropped)
  await pause();
  await pause();
  // Overlay query edit sends only via requestFull.
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa A, Tinh P');
  await tra(model, pending, 'person', person.row_id, draftingTooMany);
  assert.equal(model.openFullFromSlot('person', person.row_id).ok, true);
  await pause();
  pending.shift()(fullFound);
  await pause();
  await pause();
  assert.equal(model.state.addressFull.result, fullFound.data);
  const n = calls.length;
  model.requestFull('Xa Sua, Tinh P');
  await pause();
  assert.equal(calls.length, n + 1);
  assert.deepEqual(calls[calls.length - 1][1],
    { query: 'Xa Sua, Tinh P', presentation: 'full' });
  pending.shift()(fullFound);
  await pause();
  await pause();
  assert.equal(model.state.addressFull.query, 'Xa Sua, Tinh P');
});

test('closing overlay drops late full responses', async () => {
  const { model, person, pending } = await setup();
  await tra(model, pending, 'person', person.row_id, draftingTooMany);
  assert.equal(model.openFullFromSlot('person', person.row_id).ok, true);
  await pause();
  const resolveFull = pending.shift();
  model.closeFull();
  resolveFull(fullFound);
  await pause();
  await pause();
  assert.equal(model.state.addressFull, null);
});

test('malformed and transport failures store messages, never results', async () => {
  const { model, person, pending } = await setup();
  const key = 'person:' + person.row_id;
  let p = model.requestLookup('person', person.row_id);
  await pause();
  pending.shift()({ ok: true, data: { status: 'match', candidates: [] } });
  await p;
  await pause();
  assert.ok(model.state.addressSlots[key].message);
  assert.equal(model.state.addressSlots[key].result, undefined);
  p = model.requestLookup('person', person.row_id);
  await pause();
  pending.shift()({ ok: false, error: { message: 'boom' } });
  await p;
  await pause();
  assert.equal(model.state.addressSlots[key].message, 'boom');
});

test('empty query sends nothing', async () => {
  const { model, person, calls } = await setup();
  model.updatePersonField(person.row_id, 'dia_chi', '   ');
  await model.requestLookup('person', person.row_id);
  assert.equal(calls.length, 0);
  assert.equal(model.state.addressSlots['person:' + person.row_id].phase, 'error');
});

test('R6: A-B-A before confirm keeps the old Tra invalid', async () => {
  const { model, person, calls, pending } = await setup();
  await tra(model, pending, 'person', person.row_id, draftingTooMany);
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa B, Tinh P');
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa A, Tinh P');
  const opened = model.openFullFromSlot('person', person.row_id);
  assert.deepEqual(opened, { ok: false, stale: true });
  assert.equal(calls.filter(([, pl]) => pl.presentation === 'full').length, 0);
});

test('R3: source change while pending ends stale with guidance, not loading', async () => {
  const { model, person, pending } = await setup();
  const key = 'person:' + person.row_id;
  const p = model.requestLookup('person', person.row_id);
  await pause();
  model.updatePersonField(person.row_id, 'dia_chi', 'Xa B, Tinh P');
  pending.shift()(draftingFound);
  await p;
  await pause();
  const slot = model.state.addressSlots[key];
  assert.equal(slot.phase, 'error');
  assert.ok(slot.message.includes('Bấm Tra lại'));
});

test('R3: editing an unrelated field does not invalidate the lookup', async () => {
  const { model, person, pending } = await setup();
  const key = 'person:' + person.row_id;
  const p = model.requestLookup('person', person.row_id);
  await pause();
  model.updatePersonField(person.row_id, 'ho_ten', 'Ten Moi');
  pending.shift()(draftingFound);
  await p;
  await pause();
  assert.equal(model.state.addressSlots[key].phase, 'ready');
});
