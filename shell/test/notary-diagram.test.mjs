// Diagram canvas tests (MIN-130 P7) — chay tren DOM stub, khong can
// Electron. Cover: canvas inheritance (card gon + 2 hang chip doc lap +
// edges SVG + requiredSlots), canvas hai ben (30 cho canonical, p16 dau
// Ben B, swap, ve Pool, khong compact), zoom/pan/Mo rong, save/open
// round-trip qua mock adapter, 60 node van render.
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { makeDom, collect } from './dom-stub.mjs';

const require = createRequire(import.meta.url);
const L = require('../src/renderer/lib.js');
const M = require('../src/renderer/notary/case-drafting-model.js');
const VIEW = require('../src/renderer/notary/case-drafting-view.js');
const INTAKE = require('../src/renderer/notary/intake-dialog.js');
const DIAGRAM = require('../src/renderer/notary/relationship-diagram.js');
const WORD = require('../src/renderer/notary/word-export-dialog.js');

if (typeof globalThis.crypto?.randomUUID !== 'function') {
  const { webcrypto } = require('node:crypto');
  globalThis.crypto = webcrypto;
}

// ---- helpers ----

function findBtns(root, label) {
  return collect(root, (e) =>
    (e.tagName === 'BUTTON') && e.textContent.includes(label));
}

function byCls(root, cls) {
  return collect(root, (e) => e.classList.contains(cls));
}

function personPayload(rowId) {
  return {
    preventDefault() {},
    dataTransfer: {
      getData: () => JSON.stringify({ kind: 'person', row_id: rowId }),
    },
  };
}

// Case da ton tai (committed) — giong seedExistingCase cua view test
// nhung param hoa domain/people/diagram.
function seedCase(model, { caseType = 'inheritance', people = [],
                           assets = [], nodes = [], domain = null } = {}) {
  const s = model.state;
  s.status = 'ready';
  s.caseId = 42;
  s.caseInfo = { id: 42, case_type: caseType,
                 document_type: 'khai_nhan', status: 'active',
                 locked: false, revision: 3 };
  s.backendMode = 'real';
  s.revision = 3;
  s.locked = false;
  s.unsupported = false;
  s.capabilities = { intake: [], diagram: true, word_export: true };
  s.committed = { people: structuredClone(people),
                  assets: structuredClone(assets) };
  s.stage = structuredClone(s.committed);
  if (caseType === 'inheritance') s.stage.owner_row_id = null;
  const dom = domain || caseType;
  s.committedDiagram = { version: 3, domain: dom,
                         nodes: structuredClone(nodes) };
  s.diagram = structuredClone(s.committedDiagram);
}

function tpNodes() {
  return M.TWO_PARTY_IDS.map((id) =>
    ({ id, personId: null, hidden: false, deleted: false }));
}

// Bo 7 slot LEGACY (MIN-133 era) — case cu da persist van con dang
// nay; test giu de kiem render/layout/edges tren du lieu cu. Draft MOI
// (MIN-136) chi seed 1 o 'owner' — xem test "draft moi: 1 o khoi tao".
function seedSlots() {
  const mk = (id, parents = []) =>
    ({ id, personId: null, parentSlotIds: parents, spouseSlotIds: [],
       spouseSlotId: null, spouseSuggestionId: null,
       ownPositions: [], receivePositions: [], hidden: false, deleted: false });
  const nodes = [
    mk('father'), mk('mother'),
    mk('spouse_father'), mk('spouse_mother'),
    mk('owner', ['father', 'mother']),
    mk('spouse', ['spouse_father', 'spouse_mother']),
    mk('child_1', ['owner', 'spouse']),
  ];
  nodes.find((n) => n.id === 'owner').spouseSlotIds = ['spouse'];
  nodes.find((n) => n.id === 'owner').spouseSlotId = 'spouse';
  return structuredClone(nodes);
}

async function build(t, { mode = 'draft-inh', seed = {}, client, reconcileEngine } = {}) {
  const { document } = makeDom();
  global.document = document;
  const memStore = new Map();
  global.window = {
    G1_NOTARY_MODEL: M, G1_NOTARY_VIEW: VIEW,
    G1_NOTARY_INTAKE: INTAKE, G1_NOTARY_DIAGRAM: DIAGRAM,
    G1_NOTARY_WORD: WORD,
    localStorage: {
      getItem: (k) => memStore.get(k) ?? null,
      setItem: (k, v) => { memStore.set(k, String(v)); },
      removeItem: (k) => { memStore.delete(k); },
      clear: () => { memStore.clear(); },
    },
  };
  const calls = [];
  const cl = client || {
    run: async (cmd, payload) => {
      calls.push([cmd, payload]);
      return { ok: true, data: {} };
    },
  };
  const model = M.createModel({ client: cl, reconcileEngine });
  const view = VIEW.createNotaryModuleView({
    model, lib: L, notify: () => {},
    confirm: async () => true,
    pickFiles: async () => ({ ok: true, data: { files: [] } }),
    openPath: async () => ({ ok: true }),
    registerDroppedFile: null,
    cancelJob: async () => ({ ok: true }),
    runCommand: cl.run,
  });
  document.body.append(view.el);
  if (mode === 'draft-inh') await model.newDraft('inheritance');
  else if (mode === 'draft-tp') await model.newDraft('two_party');
  else {
    seedCase(model, seed);
    model.dismissNotice();          // emit → render workspace
  }
  t.after(() => { delete global.document; delete global.window; });
  return { model, view, document, calls };
}

const INH_PEOPLE = [
  { row_id: 'c1', ho_ten: 'Người Đã Lưu', ngay_sinh: '1955-01-01',
    ngay_chet: '2020-05-10' },
  { row_id: 'c2', ho_ten: 'Vợ Hai', ngay_sinh: '1960' },
  { row_id: 'c3', ho_ten: 'Con Ba', ngay_sinh: '1985-03-02' },
];

// ---------- inheritance canvas: seed + card + edges ----------

test('draft moi inheritance: DUNG 1 o owner trong (MIN-136)', async () => {
  const { view } = await build(test, { mode: 'draft-inh' });
  const cards = byCls(view.el, 'cd-node');
  assert.equal(cards.length, 1, 'draft moi chi co 1 o khoi tao');
  const owner = collect(view.el, (e) =>
    e.dataset.nodeId === 'owner')[0];
  assert.ok(owner, 'thieu o owner');
  assert.ok(owner.classList.contains('cd-node-empty'),
    'o khoi tao phai la node trong');
  assert.match(owner.getAttribute('aria-label'), /Chủ đất/);
  // Khong co edges khi chi co 1 node.
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-edge')).length, 0);
});

test('legacy 7 slot (case cu): card + edges van render; node trống không chữ', async () => {
  const { view } = await build(test, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  const cards = byCls(view.el, 'cd-node');
  assert.equal(cards.length, 7, 'case cu 7 slot van render du');
  // Edges SVG (MIN-133): khong marker mui ten; cha/me→con =
  // cd-edge-parent (cap vo/chong ve 1 edge chung tu giua doan), vo/chong
  // = cd-edge-spouse net dut.
  const svg = collect(view.el, (e) =>
    e.classList.contains('cd-canvas-edges'))[0];
  assert.ok(svg, 'thieu svg edges');
  const paths = collect(svg, (e) => e.tagName === 'PATH');
  const cls = (p) => p.getAttribute('class') || '';
  // 5 cha-con (father→owner, mother→owner, sf→spouse, sm→spouse,
  // owner+spouse→child_1 ve 1 edge) + 1 vo-chong.
  assert.equal(paths.filter((p) => cls(p).includes('cd-edge-parent'))
    .length, 5, `so edge cha-con = 5, dang ${paths.length}`);
  assert.equal(paths.filter((p) => cls(p).includes('cd-edge-spouse'))
    .length, 1, 'thieu edge vo/chong');
  assert.ok(paths.every((p) => !p.getAttribute('marker-end')),
    'edges khong con marker mui ten');
  // Node TRONG (D7): khong nhan vai tro/hint/chip trong textContent —
  // chi ô viền đứt; vai tro doc qua aria-label; van la drop target.
  const father = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  assert.ok(father, 'thieu node father');
  assert.ok(father.classList.contains('cd-node-empty'));
  assert.ok(!/Trống — thả thẻ|cha\/mẹ của/.test(father.textContent),
    'node trong khong duoc hien role/hint');
  assert.equal(collect(father, (e) =>
    e.classList.contains('cd-posrow')).length, 0,
    'node trong khong co hang chip');
  assert.match(father.getAttribute('aria-label'), /cha\/mẹ của/,
    'aria-label node trong phai mo ta vai tro');
  // owner trong: aria-label giu vai tro "Người để lại".
  const owner = collect(view.el, (e) =>
    e.dataset.nodeId === 'owner')[0];
  assert.match(owner.getAttribute('aria-label'), /Chủ đất/);
});

test('card truoc/sau gan: trong → day du ten+nam+role+chips+bo gan', async () => {
  const { model, view } = await build(test, {
    mode: 'case', seed: {
      people: INH_PEOPLE, assets: [{ row_id: 'a1', so_serial: 'S1' }],
      nodes: seedSlots() } });
  // Drop c1 vao node 'father'.
  const father = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  father.dispatch('drop', personPayload('c1'));
  assert.equal(
    model.state.diagram.nodes.find((n) => n.id === 'father').personId,
    'c1');
  // Rebuild (MIN-133 D7): card gon — ten + nam + 2 hang chip
  // "Chủ"/"Nhận"; hanh dong trong .cd-node-acts (→ gan lai, ↩ bo gan,
  // × xoa slot); vai tro qua aria-label/title.
  const after = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  assert.match(after.textContent, /Người Đã Lưu/);
  assert.match(after.textContent, /1955 – 2020/);
  assert.match(after.getAttribute('aria-label'), /Người Đã Lưu — cha\/mẹ/);
  const rows = collect(after, (e) => e.classList.contains('cd-posrow'));
  assert.equal(rows.length, 2, 'node da gan co 2 hang chip');
  assert.match(rows[0].textContent, /Chủ/);
  assert.match(rows[1].textContent, /Nhận/);
  assert.equal(byCls(after, 'js-node-unassign').length, 1,
    'can nut ↩ bo gan ve Pool');
  assert.ok(findBtns(after, '→').length === 1,
    'can nut → cho duong ban phim');
});


test('spouse drops append without swapping; last is lawful and pool removal promotes previous', async () => {
  const nodes = seedSlots();
  nodes.find((n) => n.id === 'owner').personId = 'c1';
  nodes.find((n) => n.id === 'spouse').personId = 'c2';
  nodes.find((n) => n.id === 'owner').spouseSlotIds = ['spouse'];
  nodes.find((n) => n.id === 'owner').spouseSlotId = 'spouse';
  const { model, view } = await build(test, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes } });
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  const spouse = collect(view.el, (e) => e.dataset.nodeId === 'spouse')[0];
  spouse.dispatch('drop', personPayload('c3'));
  const appendedId = owner.spouseSlotIds[1];
  assert.equal(model.state.diagram.nodes.find((n) =>
    n.id === appendedId).personId, 'c3');
  assert.equal(model.state.diagram.nodes.find((n) =>
    n.id === 'spouse').personId, 'c2', 'occupied spouse is never swapped');
  assert.equal(byCls(view.el, 'modal').length, 0, 'drop opens no dialog');
  spouse.dispatch('drop', personPayload('c2'));
  assert.deepEqual(owner.spouseSlotIds, [appendedId, 'spouse'],
    'dropping an existing candidate moves it to the end');
  const last = collect(view.el, (e) => e.dataset.nodeId === 'spouse')[0];
  assert.ok(last.classList.contains('cd-node-spouse-lawful'));
  assert.match(last.textContent, /Vợ\/chồng hợp pháp/);
  const earlier = collect(view.el, (e) =>
    e.dataset.nodeId === appendedId)[0];
  assert.ok(earlier.classList.contains('cd-node-spouse-faded'));
  const pool = byCls(view.el, 'cd-pool-box')[0];
  pool.dispatch('drop', personPayload('c2'));
  assert.deepEqual(owner.spouseSlotIds, ['spouse', appendedId]);
  assert.equal(owner.spouseSlotId, appendedId);
  pool.dispatch('drop', personPayload('c3'));
  const originalSlot = collect(view.el, (e) => e.dataset.nodeId === 'spouse')[0];
  originalSlot.dispatch('drop', personPayload('c2'));
  assert.equal(owner.spouseSlotIds.at(-1), 'spouse');
  assert.equal(owner.spouseSlotId, 'spouse');
  assert.ok(collect(view.el, (e) => e.dataset.nodeId === 'spouse')[0]
    .classList.contains('cd-node-spouse-lawful'),
  'refilling the original empty slot must retain its spouse role');
});

test('moving between owner and spouse keeps the pointer and lawful spouse synchronized', async () => {
  const { model } = await build(test, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  model.assignPerson('owner', 'c1');
  const spouse = model.addSlot('branch_spouse');
  model.setNodeRelation('child_1', { spouseSlotIds: [spouse.id] });
  assert.equal(model.state.stage.owner_row_id, 'c1');

  assert.equal(model.movePerson('c1', spouse.id), true);
  assert.equal(model.state.stage.owner_row_id, null);
  assert.equal(model.state.diagram.nodes.find((n) => n.id === 'owner').personId, null);
  assert.equal(spouse.personId, 'c1');
  const previous = model.addSlot('branch_first');
  model.assignPerson(previous.id, 'c3');
  model.setNodeRelation('child_1', { spouseSlotIds: [previous.id, spouse.id] });
  assert.equal(model.movePerson('c1', 'owner'), true);
  assert.equal(model.state.stage.owner_row_id, 'c1');
  assert.equal(spouse.personId, null);
  assert.equal(model.state.diagram.nodes.find((n) => n.id === 'child_1')
    .spouseSlotIds.at(-1), previous.id);
});

test('last spouse is highlighted and earlier candidate stays faded', async () => {
  const nodes = seedSlots();
  const owner = nodes.find((n) => n.id === 'owner');
  owner.personId = 'c1';
  owner.spouseSlotIds = ['spouse', 'spouse_2'];
  owner.spouseSlotId = 'spouse_2';
  nodes.find((n) => n.id === 'spouse').personId = 'c2';
  nodes.push({ id: 'spouse_2', personId: 'c3', parentSlotIds: [],
    spouseSlotIds: [], spouseSlotId: null, spouseSuggestionId: null,
    ownPositions: [], receivePositions: [], hidden: false, deleted: false });
  const { model, view } = await build(test, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes } });
  const earlier = collect(view.el, (e) =>
    e.dataset.nodeId === 'spouse')[0];
  const lawful = collect(view.el, (e) =>
    e.dataset.nodeId === 'spouse_2')[0];
  assert.ok(earlier.classList.contains('cd-node-spouse-faded'));
  assert.match(earlier.textContent, /Không phải vợ\/chồng hợp pháp/);
  assert.ok(lawful.classList.contains('cd-node-spouse-lawful'));
});

test('death date prefills an existing spouse suggestion', async () => {
  const nodes = seedSlots();
  const owner = nodes.find((n) => n.id === 'owner');
  owner.personId = 'c1';
  owner.spouseSlotIds = [];
  owner.spouseSlotId = null;
  owner.spouseSuggestionId = 'spouse';
  const { model } = await build(test, { mode: 'case',
    seed: { people: [{ row_id: 'c1', ho_ten: 'Người chết' }], nodes } });
  model.updatePersonField('c1', 'ngay_chet', '2020-01-01');
  const savedOwner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(savedOwner.spouseSlotIds, ['spouse']);
  assert.equal(savedOwner.spouseSlotId, 'spouse');
  assert.equal(savedOwner.spouseSuggestionId, null);
});

test('living person never receives a required spouse slot', async () => {
  const client = { run: async (cmd) => cmd === 'notary.diagram_evaluate'
    ? { ok: true, data: { evaluated_revision: 3,
      render_model: { requiredSlots: [{
        anchorSlotId: 'owner', slotTypes: ['spouse'],
      }] } } } : { ok: true, data: {} } };
  const nodes = [{ id: 'owner', personId: 'c1', parentSlotIds: [],
    spouseSlotIds: [], spouseSlotId: null, spouseSuggestionId: null,
    ownPositions: [], receivePositions: [], hidden: false, deleted: false }];
  const { model, view } = await build(test, { mode: 'case', client,
    seed: { people: [{ row_id: 'c1', ho_ten: 'Người sống' }], nodes } });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  assert.deepEqual(model.state.diagram.nodes[0].spouseSlotIds, []);
  assert.equal(model.state.diagram.nodes.length, 1);
});
test('chip own/receive doc lap, multi-select, disable > so asset', async () => {
  // MIN-133: chip chi hien tren node DA GAN nguoi (node trong la o
  // trong) — seed case co father da gan c1 + 2 asset (pos 3 disabled).
  const { model, view } = await build(test, { mode: 'case', seed: {
    people: INH_PEOPLE,
    assets: [{ row_id: 'a1', so_serial: 'S1' },
             { row_id: 'a2', so_serial: 'S2' }],
    nodes: seedSlots().map((n) =>
      n.id === 'father' ? { ...n, personId: 'c1' } : n) } });
  const node = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  const rows = collect(node, (e) => e.classList.contains('cd-posrow'));
  assert.equal(rows.length, 2);
  const chipsOf = (r) => collect(r, (e) =>
    e.classList.contains('cd-poschip'));
  assert.equal(chipsOf(rows[0]).length, M.POSITIONS.length);
  assert.equal(chipsOf(rows[1]).length, M.POSITIONS.length);
  // Positions beyond the two current assets stay visible but disabled.
  assert.equal(chipsOf(rows[0])[2].disabled, true);
  assert.equal(chipsOf(rows[0])[4].disabled, true);
  // Toggle receive/1 → own khong doi.
  chipsOf(rows[1])[0].click();
  let n = model.state.diagram.nodes.find((x) => x.id === 'father');
  assert.deepEqual(n.receivePositions, [1]);
  assert.deepEqual(n.ownPositions, []);
  // Toggle own/2 → receive giu nguyen (doc lap).
  const node2 = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  const rows2 = collect(node2, (e) => e.classList.contains('cd-posrow'));
  chipsOf(rows2[0])[1].click();
  n = model.state.diagram.nodes.find((x) => x.id === 'father');
  assert.deepEqual(n.ownPositions, [2]);
  assert.deepEqual(n.receivePositions, [1]);
  // Toggle off receive/1.
  const node3 = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  collect(node3, (e) => e.classList.contains('cd-posrow'))[1]
    && collect(collect(node3, (e) =>
      e.classList.contains('cd-posrow'))[1],
      (e) => e.classList.contains('cd-poschip'))[0].click();
  n = model.state.diagram.nodes.find((x) => x.id === 'father');
  assert.deepEqual(n.receivePositions, []);
});

// ---------- layoutInheritance (pure) ----------

test('layoutInheritance: gen tu parentSlotIds, spouse ke nhau', () => {
  const { layoutInheritance } = DIAGRAM._internals;
  const lay = layoutInheritance(seedSlots());
  assert.equal(lay.pos.father.gen, -1);
  assert.equal(lay.pos.mother.gen, -1);
  assert.equal(lay.pos.owner.gen, 0);
  assert.equal(lay.pos.spouse.gen, 0);
  assert.equal(lay.pos.child_1.gen, 1);
  // owner + spouse ke nhau tren truc X.
  const gap = Math.abs(lay.pos.owner.x - lay.pos.spouse.x);
  assert.ok(gap <= DIAGRAM._internals.NODE_W +
    DIAGRAM._internals.GAP_X + 1,
    'cap vo/chong phai dung canh nhau');
  assert.ok(lay.w > 0 && lay.h > 0);
});

test('WP6 node tests: y(spouse)==y(partner); children x ordered by birth; empty slots labelled', async (t) => {
  const { layoutInheritance, emptySlotRole } = DIAGRAM._internals;

  // 1. y(spouse) == y(partner), spare spouse slot last
  const mk = (id, parents = [], spouses = []) => ({
    id, personId: null, parentSlotIds: parents, spouseSlotIds: spouses,
    spouseSlotId: spouses.at(-1) || null, ownPositions: [], receivePositions: [],
    hidden: false, deleted: false,
  });
  const nodes = [
    { ...mk('father'), personId: 'p_fa' },
    { ...mk('mother'), personId: 'p_mo' },
    { ...mk('owner', ['father', 'mother'], ['spouse_1', 'spouse_spare']), personId: 'p_owner' },
    { ...mk('spouse_1'), personId: 'p_sp1' },
    { ...mk('spouse_spare'), personId: null },
    { ...mk('child_1960', ['owner', 'spouse_1']), personId: 'p_c1960' },
    { ...mk('child_1980', ['owner', 'spouse_1']), personId: 'p_c1980' },
    { ...mk('child_unk', ['owner', 'spouse_1']), personId: 'p_cunk' },
    { ...mk('child_spare', ['owner', 'spouse_1']), personId: null },
    { ...mk('grandchild', ['child_1960']), personId: 'p_gc' },
    { ...mk('great_grandchild', ['grandchild']), personId: 'p_ggc' },
  ];
  const people = [
    { row_id: 'p_fa', ho_ten: 'Ông Cha' },
    { row_id: 'p_mo', ho_ten: 'Bà Mẹ' },
    { row_id: 'p_owner', ho_ten: 'Chủ đất A' },
    { row_id: 'p_sp1', ho_ten: 'Bà Vợ 1' },
    { row_id: 'p_c1960', ho_ten: 'Con 1960', ngay_sinh: '1960-05-10' },
    { row_id: 'p_c1980', ho_ten: 'Con 1980', ngay_sinh: '1980-02-01' },
    { row_id: 'p_cunk', ho_ten: 'Con Không Ngày Sinh' },
    { row_id: 'p_gc', ho_ten: 'Cháu' },
    { row_id: 'p_ggc', ho_ten: 'Chắt' },
  ];

  const lay = layoutInheritance(nodes, people);

  // Check generational rows: parents -1, holder+spouses 0, children +1, grandchildren +2, chắt +3
  assert.equal(lay.pos.father.gen, -1);
  assert.equal(lay.pos.mother.gen, -1);
  assert.equal(lay.pos.owner.gen, 0);
  assert.equal(lay.pos.spouse_1.gen, 0);
  assert.equal(lay.pos.spouse_spare.gen, 0);
  assert.equal(lay.pos.child_1960.gen, 1);
  assert.equal(lay.pos.child_1980.gen, 1);
  assert.equal(lay.pos.child_unk.gen, 1);
  assert.equal(lay.pos.child_spare.gen, 1);
  assert.equal(lay.pos.grandchild.gen, 2);
  assert.equal(lay.pos.great_grandchild.gen, 3);

  // y(spouse) == y(partner)
  assert.equal(lay.pos.spouse_1.y, lay.pos.owner.y, 'y(spouse_1) phai bang y(owner)');
  assert.equal(lay.pos.spouse_spare.y, lay.pos.owner.y, 'y(spouse_spare) phai bang y(owner)');

  // spouse slots immediately beside partner, spare spouse slot last
  assert.ok(lay.pos.owner.x < lay.pos.spouse_1.x);
  assert.ok(lay.pos.spouse_1.x < lay.pos.spouse_spare.x, 'spare spouse slot last');

  // children ordered by birth date (unknown last, stable), spare child slot last
  assert.ok(lay.pos.child_1960.x < lay.pos.child_1980.x, 'child 1960 phai dung truoc child 1980');
  assert.ok(lay.pos.child_1980.x < lay.pos.child_unk.x, 'child known birth phai dung truoc child unknown birth');
  assert.ok(lay.pos.child_unk.x < lay.pos.child_spare.x, 'child unknown phai dung truoc spare child slot');

  const boxes = Object.values(lay.pos);
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i], b = boxes[j];
      const overlap = a.x < b.x + b.w - 0.5 && b.x < a.x + a.w - 0.5 &&
        a.y < b.y + b.h - 0.5 && b.y < a.y + a.h - 0.5;
      assert.equal(overlap, false, `overlap ${JSON.stringify(a)} ${JSON.stringify(b)}`);
    }
  }
  assert.ok(lay.pos.child_1960.y > lay.pos.owner.y + lay.pos.owner.h - 1,
    'Con nằm dưới hàng của cặp');

  // 2. empty slots labelled
  const emptyOwner = mk('owner');
  const emptyFa = mk('father');
  const emptyMo = mk('mother');
  const emptySp = mk('spouse_new');
  const emptyCh = mk('child_new', ['owner']);
  const cRep = { ...mk('c_anchor'), personId: 'p_crep' };
  const emptyRepChild = mk('rep_child_new', ['c_anchor']);
  const testNodes = [
    emptyOwner, emptyFa, emptyMo, emptySp, emptyCh, cRep, emptyRepChild,
  ];
  emptyOwner.parentSlotIds = [emptyFa.id, emptyMo.id];
  emptyOwner.spouseSlotIds = [emptySp.id];
  const testPeople = [
    { row_id: 'p_crep', ho_ten: 'Nguyễn Văn C' },
  ];

  assert.equal(emptySlotRole(emptyOwner, testNodes, testPeople), 'Chủ đất');
  assert.equal(emptySlotRole(emptyFa, testNodes, testPeople), 'Cha');
  assert.equal(emptySlotRole(emptyMo, testNodes, testPeople), 'Mẹ');
  assert.equal(emptySlotRole(emptySp, testNodes, testPeople), 'Vợ/chồng');
  assert.equal(emptySlotRole(emptyCh, testNodes, testPeople), 'Con');
  assert.equal(emptySlotRole(emptyRepChild, testNodes, testPeople), 'Con của Nguyễn Văn C');
  const uuid = '11111111-1111-4111-8111-111111111111';
  const namedOwner = { id: 'owner', personId: 'p_owner', parentSlotIds: [uuid],
    spouseSlotIds: [] };
  const uuidFather = { id: uuid, personId: null, parentSlotIds: [] };
  assert.equal(emptySlotRole(uuidFather, [namedOwner, uuidFather],
    [{ row_id: 'p_owner', ho_ten: 'Người để lại' }]), 'Cha của Người để lại');
  assert.doesNotMatch(emptySlotRole(uuidFather, [namedOwner, uuidFather],
    [{ row_id: 'p_owner', ho_ten: 'Người để lại' }]), /[0-9a-f]{8}-/i);

  // Check DOM rendering in view
  const { view } = await build(t, { mode: 'case', seed: {
    people: testPeople,
    assets: [{ row_id: 'a1' }],
    nodes: testNodes,
  }});
  const emptyCards = collect(view.el, (e) => e.classList.contains('cd-node-empty'));
  const labels = emptyCards.map((c) => {
    const lbl = collect(c, (el) => el.classList.contains('cd-empty-label'))[0];
    return [c.dataset.nodeId, lbl ? lbl.textContent : ''];
  });
  const labelMap = Object.fromEntries(labels);
  assert.equal(labelMap.owner, 'Chủ đất');
  assert.equal(labelMap.father, 'Cha');
  assert.equal(labelMap.mother, 'Mẹ');
  assert.equal(labelMap.spouse_new, 'Vợ/chồng');
  assert.equal(labelMap.child_new, 'Con');
  assert.equal(labelMap.rep_child_new, 'Con của Nguyễn Văn C');
});

// ---------- MIN-133: nut so do len head, kich thuoc mockup ----------

test('MIN-133 D6: Lưu hồ sơ + Xuất Word trong card-head, không còn footer', async () => {
  const { model, view } = await build(test, { mode: 'draft-inh' });
  assert.equal(byCls(view.el, 'cd-rel-foot').length, 0,
    'footer so do da bo theo mockup');
  const head = collect(view.el, (e) =>
    e.classList.contains('card-head') &&
    /Sơ đồ thừa kế/.test(e.textContent))[0];
  assert.ok(head, 'khong tim thay card-head vung so do');
  assert.equal(findBtns(head, 'Lưu hồ sơ').length, 1);
  assert.equal(findBtns(head, 'Xuất Word').length, 1);
  // Dirty aria sống trên chính nút trong card-head.
  model.updateCaseMeta('noi_niem_yet', 'Xã Mới');
  const headNow = collect(view.el, (e) =>
    e.classList.contains('card-head') &&
    /Sơ đồ thừa kế/.test(e.textContent))[0];
  const save = findBtns(headNow, 'Lưu hồ sơ')[0];
  assert.equal(byCls(save, 'dirty-dot').length, 1);
  assert.match(save.getAttribute('aria-label'), /có thay đổi chưa lưu/);
});

test('MIN-133 D7: hang layout theo mockup (node 173 / trong 88x24)', () => {
  const { NODE_W, NODE_H, GAP_X } = DIAGRAM._internals;
  assert.equal(NODE_W, 173);
  assert.equal(NODE_H, 87);
  assert.equal(GAP_X, 14);
  const lay = DIAGRAM._internals.layoutInheritance(seedSlots());
  // pos gio mang w/h theo trang thai node.
  assert.equal(lay.pos.owner.w, 88);
  assert.equal(lay.pos.owner.h, 24);
});

// ---------- two_party canvas ----------

test('two_party: 30 cho canonical, p16 dau Ben B, khong compact', async () => {
  const { model, view } = await build(test, {
    mode: 'case',
    seed: { caseType: 'two_party',
            people: INH_PEOPLE, nodes: tpNodes() } });
  const slots = byCls(view.el, 'cd-tp-slot');
  assert.equal(slots.length, 30, 'phai render dung 30 cho');
  const cols = byCls(view.el, 'cd-side-col');
  assert.equal(cols.length, 2);
  assert.match(cols[0].textContent, /Bên A \(p1–p15\)/);
  assert.match(cols[1].textContent, /Bên B \(p16–p30\)/);
  // p16 = slot dau tien cua cot B — canonical, khong theo thu tu stage.
  const colBSlots = collect(cols[1], (e) =>
    e.classList.contains('cd-tp-slot'));
  assert.equal(colBSlots[0].dataset.slotId, 'p16');
  assert.match(colBSlots[0].textContent, /Chỗ 16/);
  // Khong co card thua ke / edges / chip tren domain nay.
  assert.equal(byCls(view.el, 'cd-node').length, 0);
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-canvas-edges')).length, 0);
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-poschip')).length, 0);
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-posrow')).length, 0);
  // Gan nguoi → cho van 30 (khong compact/don lo).
  const p1 = collect(view.el, (e) => e.dataset.slotId === 'p1')[0];
  p1.dispatch('drop', personPayload('c1'));
  assert.equal(byCls(view.el, 'cd-tp-slot').length, 30);
  const filled = model.state.diagram.nodes.find((n) => n.id === 'p1');
  assert.equal(filled.personId, 'c1');
});

test('two_party: swap occupied + keo ve Pool + card chi ten+cho', async () => {
  const { model, view } = await build(test, {
    mode: 'case',
    seed: { caseType: 'two_party', people: INH_PEOPLE,
            nodes: tpNodes().map((n) =>
              n.id === 'p5' ? { ...n, personId: 'c1' }
              : n.id === 'p20' ? { ...n, personId: 'c2' } : n) } });
  const nodes = () => model.state.diagram.nodes;
  const get = (id) => nodes().find((n) => n.id === id);
  // Card p5: ten + "Chỗ 5" — khong co vai tro/chip thua ke.
  const s5 = collect(view.el, (e) => e.dataset.slotId === 'p5')[0];
  assert.match(s5.textContent, /Người Đã Lưu/);
  assert.match(s5.textContent, /Chỗ 5/);
  assert.ok(!/Chủ đất|Nhận đất|vợ\/chồng|cha\/mẹ/.test(s5.textContent));
  // Drop c2 (dang o p20) len p5 (occupied) → SWAP.
  s5.dispatch('drop', personPayload('c2'));
  assert.equal(get('p5').personId, 'c2');
  assert.equal(get('p20').personId, 'c1', 'swap phai doi cho');
  // Keo nguoi tu slot ve Pool → bo gan.
  const poolBox = collect(view.el, (e) =>
    e.classList.contains('cd-pool-box'))[0];
  poolBox.dispatch('drop', personPayload('c2'));
  assert.equal(get('p5').personId, null, 've Pool phai bo gan');
  assert.equal(byCls(view.el, 'cd-tp-slot').length, 30);
});

test('two_party: assign menu du 30 cho + swap bang ban phim', async () => {
  const { model, view } = await build(test, {
    mode: 'case',
    seed: { caseType: 'two_party', people: INH_PEOPLE,
            nodes: tpNodes().map((n) =>
              n.id === 'p7' ? { ...n, personId: 'c2' } : n) } });
  // Pool card '→' mo menu cho c1 (chua gan).
  const poolCard = collect(view.el, (e) =>
    e.classList.contains('cd-pool-card') &&
    /Người Đã Lưu/.test(e.textContent))[0];
  findBtns(poolCard, '→')[0].click();
  const modal = collect(view.el, (e) =>
    e.classList.contains('modal'))[0];
  assert.ok(modal, 'menu gan vi tri khong mo');
  // 30 nut cho: trong hien so, occupied hien "so — ten".
  assert.ok(findBtns(modal, '7 — Vợ Hai').length === 1,
    'menu phai liet ke cho co nguoi de swap');
  findBtns(modal, '17')[0].click();            // cho trong
  const nodes = model.state.diagram.nodes;
  assert.equal(nodes.find((n) => n.id === 'p17').personId, 'c1');
  // Menu cua nguoi dang o slot (c2 o p7): swap sang cho co nguoi.
  const s7 = collect(view.el, (e) => e.dataset.slotId === 'p7')[0];
  findBtns(s7, '→')[0].click();
  const modal2 = collect(view.el, (e) =>
    e.classList.contains('modal'))[0];
  findBtns(modal2, '17 — Người Đã Lưu')[0].click();
  assert.equal(nodes.find((n) => n.id === 'p17').personId, 'c2');
  assert.equal(nodes.find((n) => n.id === 'p7').personId, 'c1',
    'swap bang ban phim khong dung');
});

test('cach tinh hien hang 2/3 va du 7 vai tieng Viet, giu nguyen phan so engine', async (t) => {
  const client = {
    run: async () => ({ ok: true, data: { evaluated_revision: 3,
      render_model: {
        status: 'complete',
        allocations: { c3: { finalShare: '29/51', displayPercent: '56.86' } },
        breakdowns: [{ personId: 'c3', total: '29/51', terms: [
          { kind: 'base', fraction: '1/51' },
          { kind: 'inheritance', fraction: '2/17', sourcePersonId: 'c1',
            heirRank: 2, relationshipRoles: ['grandparent', 'sibling', 'grandchild'],
            viaBranchPersonIds: [] },
          { kind: 'inheritance', fraction: '7/51', sourcePersonId: 'c2',
            heirRank: 3, relationshipRoles: ['great_grandparent',
              'parent_sibling', 'sibling_child', 'great_grandchild'],
            viaBranchPersonIds: [] },
          { kind: 'representation', fraction: '5/17', sourcePersonId: 'c1',
            heirRank: 1, viaBranchPersonIds: ['c2'] },
        ] }],
        requiredSlots: [], warnings: [], errors: [], unresolvedEstates: [],
      } } }),
  };
  const { view } = await build(t, { mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  const lines = byCls(view.el, 'cd-explain').map((e) => e.textContent);
  assert.equal(lines[0], 'base: 1/51');
  assert.match(lines[1], /inheritance: 2\/17 · từ Người Đã Lưu · hàng 2/);
  for (const role of ['ông/bà nội/ngoại', 'anh/chị/em ruột',
    'cháu ruột (người để lại là ông/bà)']) assert.ok(lines[1].includes(role));
  assert.match(lines[2], /inheritance: 7\/51 · từ Vợ Hai · hàng 3/);
  for (const role of ['cụ nội/ngoại', 'bác/chú/cậu/cô/dì ruột',
    'cháu ruột (người để lại là bác/chú/cậu/cô/dì)', 'chắt ruột']) {
    assert.ok(lines[2].includes(role));
  }
  assert.ok(!lines[1].includes('qua ') && !lines[2].includes('qua '),
    'hang 2/3 la nhan truc tiep, khong phai the vi');
  assert.equal(lines[3], 'representation: 5/17 · từ Người Đã Lưu · qua Vợ Hai');
  assert.match(byCls(view.el, 'cd-calc')[0].textContent, /56.86%phần cuối 29\/51/);
});

// ---------- requiredSlots → tu sinh slot ----------

test('requiredSlots (engine slots[]): tao father/mother/spouse/child voi ID on dinh', async () => {
  const required = [{ anchorSlotId: 'owner', reason: 'active_estate',
    slotTypes: ['father', 'mother', 'spouse', 'child'],
    minimumEmptyChildSlots: 1, minimumEmptySpouseSlots: 1,
    slots: [
      { id: 's_father', role: 'father', ordinal: 0 },
      { id: 's_mother', role: 'mother', ordinal: 0 },
      { id: 's_spouse_0', role: 'spouse', ordinal: 0 },
      { id: 's_spouse_1', role: 'spouse', ordinal: 1 },
      { id: 's_child_0', role: 'child', ordinal: 0 },
      { id: 's_child_1', role: 'child', ordinal: 1 }] }];
  const client = {
    run: async (cmd) => cmd === 'notary.diagram_evaluate'
      ? { ok: true, data: { evaluated_revision: 3, render_model: {
          engineVersion: 2, status: 'incomplete', allocations: {},
          breakdowns: [], requiredSlots: required, warnings: [],
          errors: [], unresolvedEstates: [], conservation: {} } } }
      : { ok: true, data: {} },
  };
  const nodes = seedSlots().map((n) => ({ ...n }));
  for (const n of nodes) {
    if (n.id === 'owner') {
      n.personId = 'c1'; n.parentSlotIds = []; n.spouseSlotIds = [];
      n.spouseSlotId = null;
    } else {
      n.deleted = true;
    }
  }
  const { model, view } = await build(test, {
    mode: 'case', client, reconcileEngine: true,
    seed: { people: INH_PEOPLE, nodes } });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  const after = model.state.diagram.nodes.filter((n) => !n.deleted);
  assert.deepEqual(new Set(after.map((n) => n.id)), new Set(
    ['owner', 's_father', 's_mother', 's_spouse_0', 's_spouse_1',
     's_child_0', 's_child_1']));
  const owner = after.find((n) => n.id === 'owner');
  assert.deepEqual(owner.parentSlotIds, ['s_father', 's_mother']);
  assert.deepEqual(owner.spouseSlotIds, ['s_spouse_0', 's_spouse_1']);
  assert.equal(owner.spouseSlotId, 's_spouse_1');
  for (const kid of ['s_child_0', 's_child_1']) {
    assert.deepEqual(
      after.find((n) => n.id === kid).parentSlotIds, ['owner', 's_spouse_0']);
  }
  assert.equal(model.state.renderModel.requiredSlots, required);
});

test('requiredSlots bo qua anchor trong (mock dev) — khong no canvas', async () => {
  const client = {
    run: async (cmd) => {
      if (cmd === 'notary.diagram_evaluate') {
        return { ok: true, data: {
          evaluated_revision: 3,
          render_model: {
            engineVersion: 2, status: 'invalid', allocations: {},
            breakdowns: [],
            requiredSlots: [{
              anchorSlotId: 'father', reason: 'active_estate',
              slotTypes: ['father', 'mother', 'spouse', 'child'],
              minimumEmptyChildSlots: 1 }],
            warnings: [], errors: [], unresolvedEstates: [],
            conservation: {} } } };
      }
      return { ok: true, data: {} };
    },
  };
  const { model, view } = await build(test, {
    mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  assert.equal(model.state.diagram.nodes.length, 7,
    'anchor trong khong duoc sinh slot moi');
});
test('Pool drag starts a compatible move and first drop assigns the person', async (t) => {
  const { model, view } = await build(t, { mode: 'case', seed: {
    people: [{ row_id: 'c1', ho_ten: 'Người A' }],
    nodes: [{ id: 'owner', personId: null, parentSlotIds: [],
      spouseSlotId: null, ownPositions: [], receivePositions: [],
      hidden: false, deleted: false }],
  } });
  const poolCard = byCls(view.el, 'cd-pool-card')[0];
  const owner = collect(view.el,
    (e) => e.dataset.nodeId === 'owner')[0];
  const values = {};
  const transfer = {
    effectAllowed: 'uninitialized', dropEffect: 'none',
    setData(type, value) { values[type] = value; },
    getData(type) { return values[type] || ''; },
  };
  poolCard.dispatch('dragstart', { dataTransfer: transfer });
  assert.equal(transfer.effectAllowed, 'move');
  assert.equal(transfer.getData('text/plain'),
    JSON.stringify({ kind: 'person', row_id: 'c1' }));
  let prevented = false;
  owner.dispatch('dragover', {
    dataTransfer: transfer,
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  assert.equal(transfer.dropEffect, 'move');
  owner.dispatch('drop', {
    dataTransfer: transfer,
    preventDefault() {},
  });
  assert.equal(model.state.diagram.nodes[0].personId, 'c1');
  assert.equal(model.state.stage.owner_row_id, 'c1');
  // Drop schedules an evaluation debounce; a new draft must cancel it.
  const before = model.state.diagram.nodes;
  const newCase = model.newDraft('inheritance');
  await newCase;
  await new Promise((resolve) => setTimeout(resolve, 400));
  assert.notEqual(model.state.diagram.nodes, before);
  assert.equal(model.state.diagram.nodes[0].personId, null);
});

test('deceased owner evaluate response creates its required relationship slots', async (t) => {
  const required = [{ anchorSlotId: 'owner', reason: 'active_estate',
    slotTypes: ['father', 'mother', 'spouse', 'child'],
    minimumEmptyChildSlots: 1, minimumEmptySpouseSlots: 1,
    slots: [
      { id: 's_father', role: 'father', ordinal: 0 },
      { id: 's_mother', role: 'mother', ordinal: 0 },
      { id: 's_spouse_0', role: 'spouse', ordinal: 0 },
      { id: 's_child_0', role: 'child', ordinal: 0 }] }];
  const client = {
    run: async (cmd) => cmd === 'notary.diagram_evaluate'
      ? { ok: true, data: { render_model: { requiredSlots: required } } }
      : { ok: true, data: {} },
  };
  const { model, view } = await build(t, {
    mode: 'case', client, reconcileEngine: true,
    seed: {
      people: [{ row_id: 'c1', ho_ten: 'Người A', ngay_chet: '2020-01-01' }],
      assets: [{ row_id: 'a1' }],
      nodes: [{ id: 'owner', personId: 'c1', parentSlotIds: [],
        spouseSlotId: null, ownPositions: [1], receivePositions: [],
        hidden: false, deleted: false }],
    },
  });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.equal(model.state.renderModel.requiredSlots, required);
  assert.deepEqual(owner.parentSlotIds, ['s_father', 's_mother']);
  assert.ok(owner.spouseSlotId);
  const child = model.state.diagram.nodes.find((n) => n.id === 's_child_0');
  assert.ok(child && !child.personId);
  assert.deepEqual(child.parentSlotIds, ['owner', 's_spouse_0']);
});
test('stale evaluate response cannot apply its required slots to a changed diagram', async (t) => {
  let resolveEvaluate;
  const client = {
    run: (cmd) => cmd === 'notary.diagram_evaluate'
      ? new Promise((resolve) => { resolveEvaluate = resolve; })
      : Promise.resolve({ ok: true, data: {} }),
  };
  const { model, view } = await build(t, {
    mode: 'case', client,
    seed: {
      people: [{ row_id: 'c1', ho_ten: 'Người A' }],
      nodes: [{ id: 'owner', personId: null, parentSlotIds: [],
        spouseSlotId: null, ownPositions: [], receivePositions: [],
        hidden: false, deleted: false }],
    },
  });
  const oldRender = { requiredSlots: [{
    anchorSlotId: 'owner', slotTypes: ['father'], minimumEmptyChildSlots: 0,
  }] };
  model.state.renderModel = oldRender;
  const evaluation = findBtns(view.el, 'Xem cách tính')[0].onclick();
  model.movePerson('c1', 'owner');
  const evaluated = { requiredSlots: [{
    anchorSlotId: 'owner', slotTypes: ['father', 'mother'],
    minimumEmptyChildSlots: 0,
  }] };
  resolveEvaluate({ ok: true, data: { render_model: evaluated } });
  await evaluation;
  assert.equal(model.state.renderModel, oldRender);
  assert.equal(model.state.diagram.nodes.some((n) => n.id === 'father'), false);
});

test('MIN-136: chủ đất sống → hint điền Ngày mất; đã mất → không hint', async () => {
  const { model, view } = await build(test, { mode: 'case', seed: {
    people: [{ row_id: 'c1', ho_ten: 'Chủ Sống', ngay_sinh: '1950' }],
    nodes: [{ id: 'owner', personId: 'c1', parentSlotIds: [],
              spouseSlotId: null, ownPositions: [], receivePositions: [],
              hidden: false, deleted: false }] } });
  const hint = collect(view.el, (e) => e.classList.contains('cd-hint'))[0];
  assert.ok(hint, 'thiếu hint chủ đất còn sống');
  assert.match(hint.textContent, /Ngày mất/);
  // Chu dat da co ngay mat → engine co the spawn nhanh → khong hint.
  model.state.stage.people[0].ngay_chet = '2020-01-01';
  model.state.committed.people[0].ngay_chet = '2020-01-01';
  model.dismissNotice();
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-hint')).length, 0,
    'hint vẫn còn khi chủ đất đã có ngày mất');
});

// ---------- zoom / pan / Mo rong ----------

test('zoom cluster: −/+ doi label; Mo rong mo overlay co canvas', async () => {
  const { view, document } = await build(test, { mode: 'draft-inh' });
  const minus = collect(view.el, (e) =>
    e.tagName === 'BUTTON' &&
    e.getAttribute('aria-label') === 'Thu nhỏ sơ đồ')[0];
  minus.click();
  const lbl = collect(view.el, (e) =>
    e.classList.contains('cd-zoom-label'))[0];
  assert.equal(lbl.textContent, '90%');
  // Mo rong → overlay .cd-expand chua canvas rieng.
  const expand = findBtns(view.el, 'Mở rộng')[0];
  expand.click();
  const overlay = collect(view.el, (e) =>
    e.classList.contains('cd-expand'))[0];
  assert.ok(overlay, 'overlay Mo rong khong mo');
  assert.ok(collect(overlay, (e) =>
    e.classList.contains('cd-canvas-wrap')).length === 1,
    'overlay phai chua canvas rieng');
  // Esc dong overlay (openModal xu ly).
  document.dispatch('keydown',
    { key: 'Escape', preventDefault() {} });
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-expand')).length, 0,
    'Esc khong dong overlay');
});

test('pan: keo nen canvas → scrollLeft/Top doi, mouseup ket thuc', async () => {
  const { view, document } = await build(test, { mode: 'draft-inh' });
  const wrap = collect(view.el, (e) =>
    e.classList.contains('cd-canvas-wrap'))[0];
  wrap.dispatch('mousedown',
    { target: wrap, clientX: 200, clientY: 100, preventDefault() {} });
  assert.ok(wrap.classList.contains('panning'));
  document.dispatch('mousemove', { clientX: 150, clientY: 80 });
  assert.equal(wrap.scrollLeft, 50);
  assert.equal(wrap.scrollTop, 20);
  document.dispatch('mouseup', {});
  assert.ok(!wrap.classList.contains('panning'));
});

// ---------- 60 node ----------

test('60 node thua ke: moi card render + layout khac nhau', async () => {
  const { model, view } = await build(test, { mode: 'draft-inh' });
  // MIN-136: draft seed 1 node owner → them 59 slot de du 60.
  for (let i = 0; i < 59; i += 1) model.addSlot();
  assert.equal(model.state.diagram.nodes.length, 60);
  const cards = byCls(view.el, 'cd-node');
  assert.equal(cards.length, 60, '60 node phai render du');
  const xs = new Set(cards.map((c) => c.style.left));
  const ys = new Set(cards.map((c) => c.style.top));
  assert.ok(xs.size > 1 || ys.size > 1,
    'cac card phai co vi tri layout khac nhau');
  const world = collect(view.el, (e) =>
    e.classList.contains('cd-canvas-world'))[0];
  assert.ok(parseInt(world.style.width, 10) > 0 &&
    parseInt(world.style.height, 10) > 0,
    'world phai co kich thuoc de cuon/pan');
  // Khong ep nho chu: khong co font-size inline nao.
  assert.ok(cards.every((c) => !c.style.fontSize),
    'khong duoc co chu node de nhet them');
});

// ---------- save/open round-trip ----------

test('save → openCase round-trip: vi tri + quan he giu nguyen', async () => {
  const store = { saved: null, revision: 4 };
  const client = {
    run: async (cmd, payload) => {
      if (cmd === 'notary.workspace_save_case') {
        store.revision += 1;
        store.saved = structuredClone(payload.diagram.state);
        const c = payload.case || {};
        return { ok: true, data: {
          created: payload.case_id == null,
          case: { id: payload.case_id != null ? payload.case_id : 42,
                  case_type: c.case_type || 'inheritance',
                  document_type: c.document_type || 'khai_nhan',
                  status: 'active', locked: false,
                  revision: store.revision },
          backend_mode: 'real',
          capabilities: { intake: [], diagram: true, word_export: true },
          stage: structuredClone(payload.stage),
          diagram: { state: structuredClone(store.saved),
                     render_model: null },
          warnings: [] } };
      }
      if (cmd === 'notary.workspace_get') {
        return { ok: true, data: {
          case: { id: 42, case_type: 'inheritance',
                  document_type: 'khai_nhan', status: 'active',
                  locked: false, revision: store.revision },
          backend_mode: 'real',
          capabilities: { intake: [], diagram: true,
                          word_export: true },
          stage: { people: structuredClone(INH_PEOPLE),
                   assets: [{ row_id: 'a1', so_serial: 'S1' }],
                   owner_row_id: 'c1' },
          diagram: { state: structuredClone(store.saved),
                     render_model: null },
          warnings: [] } };
      }
      if (cmd === 'notary.diagram_evaluate') {
        return { ok: true, data: {
          evaluated_revision: store.revision, render_model: null } };
      }
      return { ok: true, data: {} };
    },
  };
  const nodes = seedSlots().map((n) => ({ ...n }));
  nodes.find((n) => n.id === 'owner').personId = 'c1';
  nodes.find((n) => n.id === 'spouse').personId = 'c2';
  nodes.push({ id: 'spouse_2', personId: 'c3', parentSlotIds: [],
    spouseSlotIds: [], spouseSlotId: null, spouseSuggestionId: null,
    ownPositions: [], receivePositions: [], hidden: false, deleted: false });
  nodes.find((n) => n.id === 'owner').spouseSlotIds = ['spouse', 'spouse_2'];
  nodes.find((n) => n.id === 'owner').spouseSlotId = 'spouse_2';
  const { model } = await build(test, {
    mode: 'case', client,
    seed: { people: INH_PEOPLE, assets: [{ row_id: 'a1' }], nodes } });
  // Doi positions + them slot con → save.
  model.toggleNodePosition('owner', 'own', 1);
  model.toggleNodePosition('spouse', 'receive', 1);
  const sp = model.state.diagram.nodes.find((n) => n.id === 'spouse');
  sp.parentSlotIds = ['spouse_father', 'spouse_mother'];
  const r = await model.saveCase();
  assert.equal(r.ok, true, 'saveCase loi');
  assert.ok(store.saved, 'adapter khong nhan state');
  // Mo lai qua model khac cung adapter → state diagram giong ban da luu.
  const model2 = M.createModel({ client });
  await model2.openCase(42);
  const reopened = model2.state.diagram;
  assert.deepEqual(reopened, store.saved,
    'diagram mo lai khong giong ban da save');
  const owner = reopened.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(owner.ownPositions, [1]);
  const spouse = reopened.nodes.find((n) => n.id === 'spouse');
  assert.deepEqual(spouse.receivePositions, [1]);
  assert.deepEqual(spouse.parentSlotIds,
    ['spouse_father', 'spouse_mother'],
    'quan he cha/me khong giu qua round-trip');
  assert.equal(spouse.personId, 'c2');
  assert.deepEqual(owner.spouseSlotIds, ['spouse', 'spouse_2'],
    'thu tu spouse khong duoc sap xep khi save/load');
});

test('two_party: assign → save → reopen giu 30 cho + nguoi dung cho', async () => {
  const store = { saved: null, revision: 4 };
  const client = {
    run: async (cmd, payload) => {
      if (cmd === 'notary.workspace_save_case') {
        store.revision += 1;
        store.saved = structuredClone(payload.diagram.state);
        const c = payload.case || {};
        return { ok: true, data: {
          created: payload.case_id == null,
          case: { id: payload.case_id != null ? payload.case_id : 42,
                  case_type: c.case_type || 'two_party',
                  document_type: c.document_type || 'chuyen_nhuong',
                  status: 'active', locked: false,
                  revision: store.revision },
          backend_mode: 'real',
          capabilities: { intake: [], diagram: true, word_export: false },
          stage: structuredClone(payload.stage),
          diagram: { state: structuredClone(store.saved),
                     render_model: null },
          warnings: [] } };
      }
      if (cmd === 'notary.workspace_get') {
        return { ok: true, data: {
          case: { id: 42, case_type: 'two_party',
                  document_type: 'chuyen_nhuong', status: 'active',
                  locked: false, revision: store.revision },
          backend_mode: 'real',
          capabilities: { intake: [], diagram: true,
                          word_export: false },
          stage: { people: structuredClone(INH_PEOPLE), assets: [] },
          diagram: { state: structuredClone(store.saved),
                     render_model: null },
          warnings: [] } };
      }
      return { ok: true, data: {} };
    },
  };
  const nodes = tpNodes();
  nodes.find((n) => n.id === 'p16').personId = 'c1';
  nodes.find((n) => n.id === 'p3').personId = 'c2';
  const { model } = await build(test, {
    mode: 'case', client,
    seed: { caseType: 'two_party', people: INH_PEOPLE, nodes } });
  // Seeded case co diagramDirty=false — can mot mutation de save
  // khong noop.
  model.assignPerson('p7', 'c3');
  const r = await model.saveCase();
  assert.equal(r.ok, true);
  const model2 = M.createModel({ client });
  await model2.openCase(42);
  assert.equal(model2.state.diagram.nodes.length, 30);
  assert.equal(model2.state.diagram.nodes
    .find((n) => n.id === 'p16').personId, 'c1');
  assert.equal(model2.state.diagram.nodes
    .find((n) => n.id === 'p3').personId, 'c2');
});

// ---------- cue chỉ-đọc sau lưu / mở lại (story #5) ----------

test('save thiếu dữ liệu: cue chỉ-đọc hiện, không sinh slot', async () => {
  const calls = [];
  const stored = {
    engineVersion: 2, status: 'incomplete', allocations: {}, breakdowns: [],
    requiredSlots: [{ anchorSlotId: 'owner', reason: 'active_estate',
                      slotTypes: ['father', 'mother', 'spouse', 'child'],
                      minimumEmptyChildSlots: 1 }],
    warnings: [{ code: 'diagram.unassigned_pool_person',
                 message: 'Người trong Stage chưa được gán trên sơ đồ' }],
    errors: [], unresolvedEstates: [], conservation: {} };
  const client = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    if (cmd === 'notary.workspace_save_case') {
      const c = payload.case || {};
      return { ok: true, data: {
        created: false,
        case: { id: payload.case_id, case_type: c.case_type,
                document_type: c.document_type, status: 'active',
                locked: false, revision: 4 },
        backend_mode: 'real',
        capabilities: { intake: [], diagram: true, word_export: true },
        stage: structuredClone(payload.stage),
        diagram: { state: structuredClone(payload.diagram.state),
                   render_model: structuredClone(stored) },
        warnings: [] } };
    }
    return { ok: true, data: {} };
  } };
  const { model, view } = await build(test, { mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  model.movePerson('c2', 'child_1');       // dirty → nút Lưu bật
  const before = model.state.diagram.nodes.length;
  const save = findBtns(view.el, 'Lưu hồ sơ')[0];
  assert.ok(save, 'thiếu nút Lưu hồ sơ');
  await save.onclick();
  // Nút Lưu hồ sơ = workspace_save_case; cue đọc render_model trả về.
  assert.equal(
    calls.filter(([c]) => c === 'notary.workspace_save_case').length, 1);
  assert.equal(model.state.diagram.nodes.length, before,
    'không sinh slot từ requiredSlots khi lưu');
  assert.equal(
    calls.filter(([c]) => c === 'notary.diagram_evaluate').length, 0,
    'lưu không được gọi evaluate (tránh vòng lặp)');
  assert.equal(model.state.diagramDirty, false, 'dirty sạch sau lưu');
  const warn = byCls(view.el, 'warn-text').map((e) => e.textContent)
    .join('\n');
  assert.match(warn, /Chưa đủ điều kiện/);
  assert.match(warn, /Người trong Stage chưa được gán trên sơ đồ/);
  assert.match(warn, /Cần bổ sung Cha, Mẹ, Vợ\/chồng, Con/);
});

test('mở lại case thiếu dữ liệu: graph giữ nguyên, cue từ render_model', async () => {
  const calls = [];
  const state = { version: 3, domain: 'inheritance', nodes: [
    { id: 'owner', personId: 'c1', parentSlotIds: [], spouseSlotId: null,
      ownPositions: [1], receivePositions: [], hidden: false, deleted: false },
    { id: 'child_1', personId: null, parentSlotIds: ['owner'],
      spouseSlotId: null, ownPositions: [], receivePositions: [],
      hidden: false, deleted: false }] };
  const rm = {
    engineVersion: 2, status: 'incomplete', allocations: {}, breakdowns: [],
    requiredSlots: [{ anchorSlotId: 'owner', reason: 'active_estate',
                      slotTypes: ['spouse', 'child'],
                      minimumEmptyChildSlots: 1 }],
    warnings: [{ code: 'diagram.unassigned_pool_person',
                 message: 'Người trong Stage chưa được gán trên sơ đồ' }],
    errors: [], unresolvedEstates: [], conservation: {} };
  const client = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    if (cmd === 'notary.workspace_get') {
      return { ok: true, data: {
        case: { id: 42, case_type: 'inheritance',
                document_type: 'khai_nhan', status: 'active',
                locked: false, revision: 4 },
        backend_mode: 'real',
        capabilities: { intake: [], diagram: true, word_export: true },
        stage: { people: structuredClone(INH_PEOPLE), assets: [],
                 owner_row_id: 'c1' },
        diagram: { state: structuredClone(state),
                   render_model: structuredClone(rm) },
        warnings: [] } };
    }
    return { ok: true, data: {} };
  } };
  const { model, view } = await build(test, { mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: [] } });
  const r = await model.openCase(42);
  assert.equal(r.ok, true, 'openCase lỗi');
  assert.deepEqual(model.state.diagram, state,
    'mở lại không thêm/đổi node');
  assert.equal(model.state.diagramDirty, false, 'mở lại không đánh dấu sửa');
  assert.equal(
    calls.filter(([c]) => c === 'notary.diagram_evaluate').length, 0,
    'mở lại không tự evaluate');
  assert.equal(byCls(view.el, 'cd-node').length, 2, 'không sinh ô mới');
  const warn = byCls(view.el, 'warn-text').map((e) => e.textContent)
    .join('\n');
  assert.match(warn, /Chưa đủ điều kiện/);
  assert.match(warn, /Cần bổ sung Vợ\/chồng, Con/);
});

test('cue trạng thái: chuyển sang complete thì xoá dòng thiếu', async () => {
  const calls = [];
  let phase = 0;
  const rmIncomplete = {
    engineVersion: 2, status: 'incomplete', allocations: {}, breakdowns: [],
    requiredSlots: [{ anchorSlotId: 'owner', reason: 'active_estate',
                      slotTypes: ['spouse', 'child'],
                      minimumEmptyChildSlots: 1 }],
    warnings: [{ code: 'diagram.unassigned_pool_person',
                 message: 'Người trong Stage chưa được gán trên sơ đồ' }],
    errors: [], unresolvedEstates: [], conservation: {} };
  const rmComplete = { ...structuredClone(rmIncomplete),
                       status: 'complete', requiredSlots: [], warnings: [] };
  const client = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    if (cmd === 'notary.workspace_save_case') {
      phase += 1;
      const c = payload.case || {};
      return { ok: true, data: {
        created: false,
        case: { id: payload.case_id, case_type: c.case_type,
                document_type: c.document_type, status: 'active',
                locked: false, revision: 2 + phase },
        backend_mode: 'real',
        capabilities: { intake: [], diagram: true, word_export: true },
        stage: structuredClone(payload.stage),
        diagram: { state: structuredClone(payload.diagram.state),
                   render_model: structuredClone(
                     phase === 1 ? rmIncomplete : rmComplete) },
        warnings: [] } };
    }
    return { ok: true, data: {} };
  } };
  const { model, view } = await build(test, { mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  model.movePerson('c2', 'child_1');
  await findBtns(view.el, 'Lưu hồ sơ')[0].onclick();
  const warn1 = byCls(view.el, 'warn-text').map((e) => e.textContent)
    .join('\n');
  assert.match(warn1, /Chưa đủ điều kiện/);
  assert.match(warn1, /Cần bổ sung Vợ\/chồng, Con/);

  model.movePerson('c2', null);            // dirty lần nữa
  await findBtns(view.el, 'Lưu hồ sơ')[0].onclick();
  const warn2 = byCls(view.el, 'warn-text').map((e) => e.textContent)
    .join('\n');
  assert.match(warn2, /Hoàn chỉnh/, 'complete phải hiện trạng thái');
  assert.doesNotMatch(warn2, /Cần bổ sung/, 'dòng thiếu phải biến mất');
  assert.equal(model.state.diagramDirty, false, 'dirty sạch sau lưu');
  assert.equal(
    calls.filter(([c]) => c === 'notary.diagram_evaluate').length, 0,
    'cue không gọi evaluate');
});

// ---------- evaluate khong goi tren two_party ----------

test('two_party: assign/drop KHONG goi diagram_evaluate', async () => {
  const { model, view, calls } = await build(test, {
    mode: 'case',
    seed: { caseType: 'two_party', people: INH_PEOPLE,
            nodes: tpNodes() } });
  const p1 = collect(view.el, (e) => e.dataset.slotId === 'p1')[0];
  p1.dispatch('drop', personPayload('c1'));
  assert.equal(model.state.diagram.nodes
    .find((n) => n.id === 'p1').personId, 'c1');
  assert.equal(
    calls.filter(([c]) => c === 'notary.diagram_evaluate').length, 0,
    'two_party khong duoc goi engine evaluate');
});

test('WP4: remove D → no toast; remove A → B,C,D to Pool + toast; Hoàn tác restores identical state; toggle off → no toast; no slot delete button rendered', async (t) => {
  const rootDir = fileURLToPath(new URL('../../', import.meta.url));
  const engineScript = `import sys,json
sys.path.insert(0, 'notary_v2')
from services.inheritance_engine import run_inheritance_case
p=json.load(sys.stdin)
nodes=p['diagram']['state']['nodes']
for n in nodes:
 n['isLandOwner']=bool(n.get('ownPositions'))
 n['willReceive']=bool(n.get('receivePositions'))
print(json.dumps(run_inheritance_case({'version':2,'nodes':nodes}, {r['row_id']:r for r in p['stage']['people']})))`;

  const client = {
    run: async (cmd, payload) => {
      if (cmd !== 'notary.diagram_evaluate') return { ok: true, data: {} };
      const render_model = JSON.parse(execFileSync(process.env.G1_PYTHON || 'python3', ['-c', engineScript], {
        cwd: rootDir, input: JSON.stringify(payload), encoding: 'utf8',
      }));
      return { ok: true, data: { render_model } };
    },
  };

  const { model, view, document } = await build(t, {
    mode: 'draft-inh',
    client,
    reconcileEngine: true,
  });

  // Setup family: A (owner, deceased 2020), B (spouse, deceased 1997), C (child, deceased 2001), D (child, living)
  const pA = model.addPerson({ ho_ten: 'Người A', ngay_chet: '2020' });
  const pB = model.addPerson({ ho_ten: 'Người B', ngay_chet: '1997' });
  const pC = model.addPerson({ ho_ten: 'Người C', ngay_chet: '2001' });
  const pD = model.addPerson({ ho_ten: 'Người D' });
  model.addAsset({ so_thua: '1', so_to: '2' });

  // 1. Assign A to owner slot
  model.movePerson(pA.row_id, 'owner');
  await model.evaluateDiagram();

  // Find required slots for spouse and children
  const spouseSlotId = model.state.diagram.nodes.find(n => n.id === 'owner')?.spouseSlotIds?.[0];
  assert.ok(spouseSlotId, 'Phải có ô vợ/chồng cho A');
  model.movePerson(pB.row_id, spouseSlotId);
  await model.evaluateDiagram();

  const childSlots = model.state.diagram.nodes.filter(n => !n.deleted && n.parentSlotIds.includes('owner') && !n.personId);
  assert.ok(childSlots.length >= 2, 'Phải có ít nhất 2 ô con');
  model.movePerson(pC.row_id, childSlots[0].id);
  await model.evaluateDiagram();

  const nextChildSlot = model.state.diagram.nodes.filter(n => !n.deleted && n.parentSlotIds.includes('owner') && !n.personId)[0];
  assert.ok(nextChildSlot, 'Phải có ô con tiếp theo cho D');
  model.movePerson(pD.row_id, nextChildSlot.id);
  await model.evaluateDiagram();

  // (1) No slot delete button rendered anywhere on diagram
  const cards = byCls(view.el, 'cd-node');
  assert.ok(cards.length > 0);
  for (const card of cards) {
    assert.equal(findBtns(card, '×').length, 0, 'Không được có nút × trên ô sơ đồ');
  }

  // (2) Remove D → no toast
  const cardD = collect(view.el, e => e.dataset.nodeId && model.state.diagram.nodes.find(n => n.id === e.dataset.nodeId && n.personId === pD.row_id))[0];
  assert.ok(cardD, 'Phải tìm thấy thẻ D');
  const unassignD = findBtns(cardD, '↩')[0];
  assert.ok(unassignD, 'Phải có nút bỏ gán ↩ trên thẻ D');
  await unassignD.onclick();

  // D is in pool, no toast rendered
  assert.equal(model.state.diagram.nodes.find(n => n.personId === pD.row_id), undefined);
  assert.equal(byCls(document, 'toast').length, 0, 'Gỡ D không làm ai khác về Pool → không hiện toast');

  // Put D back for next test
  const emptyChildSlot = model.state.diagram.nodes.find(n => !n.deleted && n.parentSlotIds.includes('owner') && !n.personId);
  model.movePerson(pD.row_id, emptyChildSlot.id);
  await model.evaluateDiagram();

  // (3) Remove A → B,C,D to Pool + toast
  const beforeA = structuredClone(model.state.diagram);
  const cardA = collect(view.el, e => e.dataset.nodeId === 'owner')[0];
  assert.ok(cardA, 'Phải tìm thấy thẻ A trên ô owner');
  const unassignA = findBtns(cardA, '↩')[0];
  assert.ok(unassignA, 'Phải có nút bỏ gán ↩ trên thẻ A');
  await unassignA.onclick();

  // Check: B, C, D to Pool via reconcile
  const activeNodes = model.state.diagram.nodes.filter(n => !n.deleted);
  assert.deepEqual(activeNodes.map(n => n.id), ['owner'], 'Chỉ còn lại ô owner trống');
  assert.equal(activeNodes[0].personId, null, 'Ô owner phải trống');
  assert.equal(byCls(view.el, 'cd-pool-card').length, 4, 'Cả 4 người A, B, C, D đều đã về Pool');

  // Toast shown: "Đã đưa 3 người về Pool · Hoàn tác"
  const toasts = byCls(document, 'toast');
  assert.equal(toasts.length, 1, 'Phải hiện đúng 1 toast khi cascade');
  assert.match(toasts[0].textContent, /Đã đưa 3 người về Pool · Hoàn tác/);

  // (4) Hoàn tác restores identical state
  const undoBtn = findBtns(toasts[0], 'Hoàn tác')[0];
  assert.ok(undoBtn, 'Phải có nút Hoàn tác trong toast');
  undoBtn.click();

  assert.equal(byCls(document, 'toast').length, 0, 'Toast phải đóng sau khi Hoàn tác');
  assert.deepEqual(model.state.diagram, beforeA, 'Hoàn tác phải khôi phục y nguyên sơ đồ trước khi gỡ');

  // (5) Toggle off → no toast
  const toggle = collect(view.el, e => e.tagName === 'INPUT' && e.type === 'checkbox' && e.getAttribute('aria-label') === 'Thông báo khi gỡ')[0];
  assert.ok(toggle, 'Phải có công tắc Thông báo khi gỡ');
  assert.equal(toggle.checked, true, 'Mặc định công tắc phải bật');
  toggle.checked = false;
  toggle.onchange();

  const cardA2 = collect(view.el, e => e.dataset.nodeId === 'owner')[0];
  await findBtns(cardA2, '↩')[0].onclick();

  assert.equal(byCls(document, 'toast').length, 0, 'Công tắc tắt → gỡ cascade hoàn toàn im lặng, không toast');
  assert.deepEqual(model.state.diagram.nodes.filter(n => !n.deleted).map(n => n.id), ['owner']);

  // Reset toggle back to default
  DIAGRAM.setRemovalNotifyEnabled(true);
});

test('removed child branch prunes; evaluate recreates required child slot with stable id', async (t) => {
  const mk = (id, personId, parents = [], extra = {}) => ({
    id, personId, parentSlotIds: parents, spouseSlotId: null,
    ownPositions: [], receivePositions: [], hidden: false, deleted: false, ...extra,
  });
  const client = { run: async (cmd) => ({ ok: true, data: cmd === 'notary.diagram_evaluate'
    ? { render_model: { requiredSlots: [{ anchorSlotId: 'owner',
        slotTypes: ['child'], minimumEmptyChildSlots: 1,
        slots: [{ id: 'child_stable', role: 'child', ordinal: 0 }] }] } }
    : {} }) };
  const { model, view } = await build(t, { mode: 'case', client, reconcileEngine: true, seed: {
    people: INH_PEOPLE, assets: [{ row_id: 'asset' }],
    nodes: [mk('owner', 'c1', [], { ownPositions: [1] }),
      mk('child_owner', 'c2', ['owner']), mk('gc', 'c3', ['child_owner'])],
  } });
  const card = collect(view.el, e => e.dataset.nodeId === 'child_owner')[0];
  await findBtns(card, '↩')[0].onclick();
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  const active = model.state.diagram.nodes.filter((n) => !n.deleted);
  const fresh = active.find(n => n.id === 'child_stable');
  assert.ok(fresh && !fresh.personId);
  assert.deepEqual(fresh.parentSlotIds, ['owner']);
  assert.ok(!active.some(n => n.id === 'gc'),
    'nhánh da go khong duoc tai hien sau doi chieu');
  collect(view.el, e => e.dataset.nodeId === fresh.id)[0]
    .dispatch('drop', personPayload('c2'));
  // reconcileEngine defers emit; wait for microtask reconcile + re-render.
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(fresh.personId, 'c2');
  assert.deepEqual(fresh.receivePositions, [], 'WP5: non-owner default is unticked (= từ chối)');
  const assigned = collect(view.el, e => e.dataset.nodeId === fresh.id)[0];
  const receive = byCls(assigned, 'cd-posrow')[1];
  byCls(receive, 'cd-poschip')[0].click();
  // After toggle + reconcile, the node object may be replaced; re-find.
  const afterToggle = model.state.diagram.nodes.find(n => n.id === fresh.id);
  assert.deepEqual(afterToggle.receivePositions, [1]);
});

test('last owner untick → confirm modal; Tiếp tục applies, Hủy giữ nguyên', async (t) => {
  const mk = (id, personId, parents = [], extra = {}) => ({
    id, personId, parentSlotIds: parents, spouseSlotId: null,
    ownPositions: [], receivePositions: [], hidden: false, deleted: false, ...extra,
  });
  const { model, view, document } = await build(t, { mode: 'case', seed: {
    people: INH_PEOPLE, assets: [{ row_id: 'asset' }],
    nodes: [mk('owner', 'c1', [], { ownPositions: [1] }),
      mk('child_owner', 'c2', ['owner'])],
  } });
  const card = collect(view.el, e => e.dataset.nodeId === 'owner')[0];
  const ownRow = byCls(card, 'cd-posrow')[0];
  const chip = byCls(ownRow, 'cd-poschip')[0];   // own/1 đang on
  assert.ok(chip.classList.contains('on'));
  chip.click();
  // Modal xuất hiện: chỉ c2 về Pool (owner node giữ c1) → N=1.
  const modal = byCls(document, 'cd-confirm-owner')[0];
  assert.ok(modal, 'modal phai xuat hien khi bo tick Chu cuoi cung');
  assert.match(modal.textContent, /Tiếp tục/);
  assert.match(modal.textContent, /1/);
  // Hủy → giữ nguyên tick
  byCls(document, 'cd-confirm-cancel')[0].click();
  assert.equal(byCls(document, 'cd-confirm-owner').length, 0);
  const n1 = model.state.diagram.nodes.find(n => n.id === 'owner');
  assert.deepEqual(n1.ownPositions, [1]);
  // Tiếp tục → toggle áp dụng
  const chip2 = byCls(byCls(collect(view.el,
    e => e.dataset.nodeId === 'owner')[0], 'cd-posrow')[0], 'cd-poschip')[0];
  chip2.click();
  byCls(document, 'cd-confirm-continue')[0].click();
  const n2 = model.state.diagram.nodes.find(n => n.id === 'owner');
  assert.deepEqual(n2.ownPositions, []);
});

test('inheritance labels never expose slot ids; spouse empty slot names its spouse', async (t) => {
  const nodes = [
    { id: 'owner', personId: 'c1', parentSlotIds: ['father', 'mother'],
      spouseSlotId: 'spouse', ownPositions: [], receivePositions: [] },
    { id: 'father', personId: null, parentSlotIds: [],
      spouseSlotId: null, ownPositions: [], receivePositions: [] },
    { id: 'mother', personId: null, parentSlotIds: [],
      spouseSlotId: null, ownPositions: [], receivePositions: [] },
    { id: 'spouse', personId: null, parentSlotIds: [],
      spouseSlotId: 'owner', ownPositions: [], receivePositions: [] },
    { id: 'child_owner', personId: null,
      parentSlotIds: ['owner', 'spouse'], spouseSlotId: null,
      ownPositions: [], receivePositions: [] },
  ];
  const { view } = await build(t, { mode: 'case', seed: {
    people: [{ row_id: 'c1', ho_ten: 'Người để lại',
      ngay_chet: '2020-01-01' }],
    assets: [{ row_id: 'a1', so_serial: 'S1' }],
    nodes,
  } });
  const spouse = collect(view.el, (e) =>
    e.dataset.nodeId === 'spouse')[0];
  assert.match(spouse.getAttribute('aria-label'), /vợ\/chồng của Người để lại/);
  const internalId = /[a-z]+_[a-z]+/;
  for (const node of byCls(view.el, 'cd-node')) {
    assert.doesNotMatch(node.textContent, internalId);
    for (const el of collect(node, () => true).concat(node)) {
      for (const attr of ['label', 'aria-label', 'title']) {
        assert.doesNotMatch(el.getAttribute(attr) || '', internalId);
      }
    }
  }
});

test('missing-data invalid status renders as incomplete in cue and calc panel', async (t) => {
  const incomplete = {
    engineVersion: 2, status: 'invalid', allocations: {}, breakdowns: [],
    requiredSlots: [], warnings: [],
    errors: [{ code: 'missing_land_owner' },
      { code: 'invalid_death_date' }],
    unresolvedEstates: [], conservation: {},
  };
  const { model, view } = await build(t, { mode: 'case',
    client: { run: async (cmd) => ({ ok: true, data:
      cmd === 'notary.diagram_evaluate'
        ? { render_model: structuredClone(incomplete) } : {} }) },
    seed: { people: [
      { row_id: 'c1', ho_ten: 'Người chưa đặt lên sơ đồ', ngay_chet: null },
    ], assets: [{ row_id: 'a1' }], nodes: seedSlots() },
  });
  model.state.renderModel = incomplete;
  view.refresh();
  assert.match(view.el.textContent,
    /Trạng thái tính: Chưa đủ điều kiện/);
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  assert.match(view.el.textContent,
    /Trạng thái tính: Chưa đủ điều kiện/);
  assert.doesNotMatch(view.el.textContent,
    /Trạng thái tính: Không hợp lệ/);
});
// ---------- R16/N2/N3/N5/N6: nhãn hiển thị tối giản ----------

test('N3/N5/N6: tên trống một nhãn, năm sống chỉ năm sinh, không badge %', async () => {
  const people = [
    { row_id: 'c1', ho_ten: 'Người Đã Lưu', ngay_sinh: '1955-01-01',
      ngay_chet: '2020-05-10' },
    { row_id: 'c2', ho_ten: 'Vợ Hai', ngay_sinh: '1960' },
    { row_id: 'c4', ho_ten: '', ngay_sinh: null },
  ];
  const { view } = await build(test, { mode: 'case', seed: {
    people, assets: [{ row_id: 'a1', so_serial: 'S1' }],
    nodes: seedSlots().map((n) =>
      n.id === 'father' ? { ...n, personId: 'c1' }
        : n.id === 'spouse' ? { ...n, personId: 'c2' } : n) } });
  const father = collect(view.el, (e) => e.dataset.nodeId === 'father')[0];
  const fatherMeta = collect(father,
    (e) => e.classList.contains('cd-node-meta'))[0];
  assert.equal(fatherMeta.textContent, '1955 – 2020');
  const spouse = collect(view.el, (e) => e.dataset.nodeId === 'spouse')[0];
  const spouseMeta = collect(spouse,
    (e) => e.classList.contains('cd-node-meta'))[0];
  assert.equal(spouseMeta.textContent, '1960',
    'còn sống chỉ hiện năm sinh, không "…"');
  assert.equal(byCls(view.el, 'cd-badge-alloc').length, 0,
    'N6: không còn badge % trên node');
  // N3: người chưa có tên trong Pool dùng đúng một nhãn.
  const pool = byCls(view.el, 'cd-pool')[0];
  assert.ok(/\(chưa có tên\)/.test(pool.textContent),
    'Pool phải dùng nhãn tên trống thống nhất');
  // R16: title ô trống không còn câu dạy thả người.
  const empty = byCls(view.el, 'cd-node-empty')[0];
  assert.ok(empty);
  assert.doesNotMatch(empty.getAttribute('aria-label'),
    /thả người từ Pool/);
});


test('Q1: missing death date is labeled on the affected card only', async (t) => {
  const { model, view } = await build(t, { mode: 'case', seed: {
    people: [{ row_id: 'A', ho_ten: 'A', ngay_chet: '2020' },
             { row_id: 'C', ho_ten: 'C', loai_giay_to: 'Giấy chứng tử' }],
    nodes: [{ id: 'owner', personId: 'A', parentSlotIds: [], spouseSlotIds: [] },
            { id: 'child', personId: 'C', parentSlotIds: ['owner'], spouseSlotIds: [] }],
  } });
  model.state.renderModel = { status: 'incomplete', requiredSlots: [], warnings: [
    { code: 'missing_death_date', personId: 'C', anchorSlotId: 'child' },
  ] };
  model.dismissNotice();
  const child = collect(view.el, (e) => e.dataset.nodeId === 'child')[0];
  const owner = collect(view.el, (e) => e.dataset.nodeId === 'owner')[0];
  assert.match(child.textContent, /thiếu ngày mất/);
  assert.doesNotMatch(owner.textContent, /thiếu ngày mất/);
  assert.equal(model.state.stage.people[0].ngay_chet, '2020');
});

test('WP7: drop triggers evaluate immediately without timer delay, text typing debounce ~300ms', async (t) => {
  const evaluateTimes = [];
  const client = {
    run: async (cmd, payload) => {
      if (cmd === 'notary.diagram_evaluate') {
        evaluateTimes.push(Date.now());
        return { ok: true, data: { render_model: { requiredSlots: [], status: 'complete' } } };
      }
      return { ok: true, data: {} };
    },
  };
  const { model, view } = await build(t, {
    mode: 'case',
    seed: {
      people: [{ row_id: 'p1', ho_ten: 'A', ngay_chet: '2020-01-01' }],
      assets: [{ row_id: 'a1' }],
      nodes: [{ id: 'owner', personId: null, ownPositions: [1], parentSlotIds: [], spouseSlotIds: [] }],
    },
    client,
    reconcileEngine: true,
  });

  // Drop triggers evaluate immediately without timer delay
  const ownerEl = collect(view.el, (e) => e.dataset.nodeId === 'owner')[0];
  const start = Date.now();
  ownerEl.dispatch('drop', {
    preventDefault: () => {},
    dataTransfer: {
      getData: () => JSON.stringify({ kind: 'person', row_id: 'p1' }),
    },
  });

  // After 40ms (microtasks settled), evaluate has already been called
  await new Promise((r) => setTimeout(r, 40));
  assert.ok(evaluateTimes.length >= 1, 'Drop phải kích hoạt evaluate ngay lập tức không có timer delay');
  const delay = evaluateTimes[0] - start;
  assert.ok(delay < 150, `Drop evaluate không được có debounce timer (thực tế: ${delay}ms)`);

  // Text typing triggers reconcile with ~300ms debounce
  evaluateTimes.length = 0;
  model.updatePersonField('p1', 'ngay_chet', '2022-01-01');
  // At 50ms, evaluate has not fired yet because of 300ms typing debounce
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(evaluateTimes.length, 0, 'Text typing phải có debounce ~300ms, chưa được gọi ở 50ms');

  // After 350ms, evaluate has fired
  await new Promise((r) => setTimeout(r, 350));
  assert.equal(evaluateTimes.length, 1, 'Sau ~300ms debounce, evaluate phải được gọi');
});
