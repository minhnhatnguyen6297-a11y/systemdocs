import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';

const require = createRequire(import.meta.url);
const { createModel } = require('../src/renderer/notary/case-drafting-model.js');
const root = fileURLToPath(new URL('../../', import.meta.url));
// Exercise the client against authoritative requirements rather than a second
// JavaScript implementation of the inheritance rules. The engine is stdlib-only.
const engine = `import sys,json
sys.path.insert(0, 'notary_v2')
from services.inheritance_engine import run_inheritance_case
p=json.load(sys.stdin)
nodes=p['diagram']['state']['nodes']
for n in nodes:
 n['isLandOwner']=bool(n.get('ownPositions'))
 n['willReceive']=bool(n.get('receivePositions'))
print(json.dumps(run_inheritance_case({'version':2,'nodes':nodes}, {r['row_id']:r for r in p['stage']['people']})))`;

function setup() {
  let evaluations = 0;
  const model = createModel({ uuid: randomUUID, reconcileEngine: true, client: { async run(command, payload) {
    if (command !== 'notary.diagram_evaluate') return { ok: true, data: {} };
    evaluations++;
    const render_model = JSON.parse(execFileSync(process.env.G1_PYTHON || 'python3', ['-c', engine], {
      cwd: root, input: JSON.stringify(payload), encoding: 'utf8',
    }));
    return { ok: true, data: { render_model } };
  } } });
  return { model, evaluations: () => evaluations };
}

async function family() {
  const setupResult = setup();
  const { model } = setupResult;
  await model.newDraft('inheritance');
  const people = Object.fromEntries(['A', 'B', 'C', 'D'].map((ho_ten) =>
    [ho_ten, model.addPerson({ ho_ten })]));
  model.addAsset({ so_thua: '1', so_to: '2' });
  model.movePerson(people.A.row_id, 'owner');
  await model.evaluateDiagram();
  return { ...setupResult, people };
}
const ids = (model) => model.state.diagram.nodes.map((n) => n.id).sort();
const owner = (model) => model.state.diagram.nodes.find((n) => n.id === 'owner');
const children = (model, anchor = 'owner') => model.state.diagram.nodes.filter((n) => n.parentSlotIds.includes(anchor));

// Count the actual model notifications consumed by the view coordinator.
test('living → dead → living restores identical stable slots, one redraw per change', async () => {
  const { model, people } = await family();
  const living = ids(model);
  let draws = 0;
  model.subscribe(() => draws++);
  model.updatePersonField(people.A.row_id, 'ngay_chet', '2020');
  assert.equal((await model.evaluateDiagram()).ok, true);
  assert.equal(draws, 1);
  assert.equal(children(model).length, 2);
  const dead = ids(model);
  await model.evaluateDiagram();
  assert.deepEqual(ids(model), dead);
  draws = 0;
  model.updatePersonField(people.A.row_id, 'ngay_chet', '');
  await model.evaluateDiagram();
  assert.equal(draws, 1);
  assert.deepEqual(ids(model), living);
  await model.evaluateDiagram();
  assert.deepEqual(ids(model), living);
});

test('Stage death edit spawns representation; living A returns C/D to Pool without deleting Stage', async () => {
  const { model, people } = await family();
  model.updatePersonField(people.A.row_id, 'ngay_chet', '2020');
  await model.evaluateDiagram();
  model.movePerson(people.B.row_id, owner(model).spouseSlotIds[0]);
  await model.evaluateDiagram();
  model.movePerson(people.C.row_id, children(model).find((n) => !n.personId).id);
  await model.evaluateDiagram();
  model.movePerson(people.D.row_id, children(model).find((n) => !n.personId).id);
  await model.evaluateDiagram();
  let draws = 0;
  model.subscribe(() => draws++);
  model.updatePersonField(people.C.row_id, 'ngay_chet', '2001');
  await model.evaluateDiagram();
  assert.equal(draws, 1);
  const c = model.state.diagram.nodes.find((n) => n.personId === people.C.row_id);
  assert.equal(children(model, c.id).length, 2);
  assert.deepEqual(c.spouseSlotIds, []);
  assert.equal(people.C.ngay_chet, '2001');
  draws = 0;
  model.updatePersonField(people.A.row_id, 'ngay_chet', '');
  const result = await model.evaluateDiagram();
  assert.equal(draws, 1);
  assert.deepEqual(result.returnedToPool.sort(), [people.C.row_id, people.D.row_id].sort());
  assert.equal(model.state.stage.people.length, 4);
  assert.deepEqual(new Set(model.state.diagram.nodes.map((n) => n.id)), new Set(['owner', ...owner(model).spouseSlotIds]));
  assert.equal(model.state.diagram.nodes.find((n) => n.personId === people.B.row_id).id, owner(model).spouseSlotIds.at(-1));
});

test('drop, move and remove card reconcile automatically with one notification', async () => {
  const { model, people } = await family();
  let draws = 0;
  model.subscribe(() => draws++);
  const slot = owner(model).spouseSlotIds[0];
  model.movePerson(people.B.row_id, slot);
  await model.evaluateDiagram();
  assert.equal(draws, 1);
  draws = 0;
  model.movePerson(people.B.row_id, null);
  await model.evaluateDiagram();
  assert.equal(draws, 1);
  assert.equal(model.state.stage.people.length, 4);
  draws = 0;
  model.movePerson(people.A.row_id, null);
  const result = await model.evaluateDiagram();
  assert.equal(draws, 1);
  assert.deepEqual(ids(model), ['owner']);
  assert.deepEqual(result.returnedToPool, []);
});

test('Q1 preserves entered partial date and exposes missing-date status for its card', async () => {
  const { model, people } = await family();
  model.updatePersonField(people.A.row_id, 'loai_giay_to', 'Giấy chứng tử');
  await model.evaluateDiagram();
  assert.deepEqual(ids(model), ['owner']);
  assert.ok(model.state.renderModel.warnings.some((w) => w.code === 'missing_death_date' && w.personId === people.A.row_id));
  assert.equal(people.A.ngay_chet, null);
  model.updatePersonField(people.A.row_id, 'ngay_chet', '2020');
  await model.evaluateDiagram();
  assert.equal(people.A.ngay_chet, '2020');
  assert.equal(children(model).length, 2);
});

test('legacy IDs migrate without losing co-parents, selections or lawful spouse order', async () => {
  const { model, people } = await family();
  model.updatePersonField(people.A.row_id, 'ngay_chet', '2020');
  await model.evaluateDiagram();
  model.movePerson(people.B.row_id, owner(model).spouseSlotIds[0]);
  await model.evaluateDiagram();
  model.movePerson(people.D.row_id, owner(model).spouseSlotIds[0]);
  await model.evaluateDiagram();
  const b = model.state.diagram.nodes.find((n) => n.personId === people.B.row_id);
  const d = model.state.diagram.nodes.find((n) => n.personId === people.D.row_id);
  assert.equal(owner(model).spouseSlotIds.at(-1), d.id);
  const child = children(model)[0];
  model.movePerson(people.C.row_id, child.id);
  await model.evaluateDiagram();
  model.setNodeRelation(child.id, { parentSlotIds: ['owner', b.id] });
  await model.evaluateDiagram();
  const stable = ids(model);
  await model.evaluateDiagram();
  assert.deepEqual(ids(model), stable);
  assert.equal(owner(model).spouseSlotIds.at(-1), d.id);
  assert.deepEqual(model.state.diagram.nodes.find((n) => n.personId === people.C.row_id).parentSlotIds, ['owner', b.id]);
  // Simulate an already-saved diagram with legacy slot IDs.
  const mapping = new Map(model.state.diagram.nodes.map((n, i) => [n.id, n.id === 'owner' ? 'owner' : `slot_${i}`]));
  for (const n of model.state.diagram.nodes) {
    n.id = mapping.get(n.id);
    n.parentSlotIds = n.parentSlotIds.map((id) => mapping.get(id));
    n.spouseSlotIds = n.spouseSlotIds.map((id) => mapping.get(id));
    n.spouseSlotId = n.spouseSlotIds.at(-1) || null;
  }
  const cLegacy = model.state.diagram.nodes.find((n) => n.personId === people.C.row_id);
  model.state.positionTouched.add(`${cLegacy.id}:receive`);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);
  assert.deepEqual(r.returnedToPool, []);
  const c = model.state.diagram.nodes.find((n) => n.personId === people.C.row_id);
  assert.ok(model.state.positionTouched.has(`${c.id}:receive`));
  assert.equal(c.parentSlotIds.length, 2);
  assert.equal(model.state.diagram.nodes.find((n) => n.id === owner(model).spouseSlotIds.at(-1)).personId, people.D.row_id);
});

test('non-convergent requirements stop at the bound and report an error once', async () => {
  let calls = 0;
  const model = createModel({ reconcileEngine: true, client: { async run(cmd) {
    if (cmd !== 'notary.diagram_evaluate') return { ok: true, data: {} };
    return { ok: true, data: { render_model: { requiredSlots: [{
      anchorSlotId: 'owner', slots: [{ id: `changing_${calls++}`, role: 'spouse' }],
    }] } } };
  } } });
  await model.newDraft('inheritance');
  let draws = 0;
  model.subscribe(() => draws++);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'diagram_reconcile_limit');
  assert.equal(calls, 16);
  assert.equal(draws, 1);
  assert.equal(model.state.busy, null);
});
