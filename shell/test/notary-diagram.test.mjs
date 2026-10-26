// Diagram canvas tests (MIN-130 P7) — chay tren DOM stub, khong can
// Electron. Cover: canvas inheritance (card gon + 2 hang chip doc lap +
// edges SVG + requiredSlots), canvas hai ben (30 cho canonical, p16 dau
// Ben B, swap, ve Pool, khong compact), zoom/pan/Mo rong, save/open
// round-trip qua mock adapter, 60 node van render.
import test from 'node:test';
import assert from 'node:assert/strict';
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
  const mk = (id, parents = [], spouse = null) =>
    ({ id, personId: null, parentSlotIds: parents,
       spouseSlotId: spouse, ownPositions: [], receivePositions: [],
       hidden: false, deleted: false });
  return structuredClone([
    mk('father'), mk('mother'),
    mk('spouse_father'), mk('spouse_mother'),
    mk('owner', ['father', 'mother'], 'spouse'),
    mk('spouse', ['spouse_father', 'spouse_mother'], 'owner'),
    mk('child_1', ['owner', 'spouse']),
  ]);
}

function build(t, { mode = 'draft-inh', seed = {}, client } = {}) {
  const { document } = makeDom();
  global.document = document;
  global.window = {
    G1_NOTARY_MODEL: M, G1_NOTARY_VIEW: VIEW,
    G1_NOTARY_INTAKE: INTAKE, G1_NOTARY_DIAGRAM: DIAGRAM,
    G1_NOTARY_WORD: WORD,
  };
  const calls = [];
  const cl = client || {
    run: async (cmd, payload) => {
      calls.push([cmd, payload]);
      return { ok: true, data: {} };
    },
  };
  const model = M.createModel({ client: cl });
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
  if (mode === 'draft-inh') model.newDraft('inheritance');
  else if (mode === 'draft-tp') model.newDraft('two_party');
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

test('draft moi inheritance: DUNG 1 o owner trong (MIN-136)', () => {
  const { view } = build(test, { mode: 'draft-inh' });
  const cards = byCls(view.el, 'cd-node');
  assert.equal(cards.length, 1, 'draft moi chi co 1 o khoi tao');
  const owner = collect(view.el, (e) =>
    e.dataset.nodeId === 'owner')[0];
  assert.ok(owner, 'thieu o owner');
  assert.ok(owner.classList.contains('cd-node-empty'),
    'o khoi tao phai la node trong');
  assert.match(owner.getAttribute('aria-label'), /Người để lại/);
  // Khong co edges khi chi co 1 node.
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-edge')).length, 0);
});

test('legacy 7 slot (case cu): card + edges van render; node trống không chữ', () => {
  const { view } = build(test, { mode: 'case',
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
  assert.match(owner.getAttribute('aria-label'), /Người để lại/);
});

test('card truoc/sau gan: trong → day du ten+nam+role+chips+bo gan', () => {
  const { model, view } = build(test, {
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

test('chip own/receive doc lap, multi-select, disable > so asset', () => {
  // MIN-133: chip chi hien tren node DA GAN nguoi (node trong la o
  // trong) — seed case co father da gan c1 + 2 asset (pos 3 disabled).
  const { model, view } = build(test, { mode: 'case', seed: {
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
  assert.equal(chipsOf(rows[0]).length, 3);
  assert.equal(chipsOf(rows[1]).length, 3);
  // Chip pos 3 disabled (chi co 2 asset).
  assert.equal(chipsOf(rows[0])[2].disabled, true);
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
  assert.equal(lay.pos.father.gen, 0);
  assert.equal(lay.pos.mother.gen, 0);
  assert.equal(lay.pos.owner.gen, 1);
  assert.equal(lay.pos.spouse.gen, 1);
  assert.equal(lay.pos.child_1.gen, 2);
  // owner + spouse ke nhau tren truc X.
  const gap = Math.abs(lay.pos.owner.x - lay.pos.spouse.x);
  assert.ok(gap <= DIAGRAM._internals.NODE_W +
    DIAGRAM._internals.GAP_X + 1,
    'cap vo/chong phai dung canh nhau');
  assert.ok(lay.w > 0 && lay.h > 0);
});

// ---------- MIN-133: nut so do len head, kich thuoc mockup ----------

test('MIN-133 D6: Lưu sơ đồ + Xuất Word trong card-head, không còn footer', () => {
  const { view } = build(test, { mode: 'draft-inh' });
  assert.equal(byCls(view.el, 'cd-rel-foot').length, 0,
    'footer so do da bo theo mockup');
  const head = collect(view.el, (e) =>
    e.classList.contains('card-head') &&
    /Sơ đồ thừa kế/.test(e.textContent))[0];
  assert.ok(head, 'khong tim thay card-head vung so do');
  assert.equal(findBtns(head, 'Lưu sơ đồ').length, 1);
  assert.equal(findBtns(head, 'Xuất Word').length, 1);
});

test('MIN-133 D7: hang layout theo mockup (node 144 / trong 88x24)', () => {
  const { NODE_W, NODE_H, GAP_X } = DIAGRAM._internals;
  assert.equal(NODE_W, 144);
  assert.equal(NODE_H, 87);
  assert.equal(GAP_X, 14);
  const lay = DIAGRAM._internals.layoutInheritance(seedSlots());
  // pos gio mang w/h theo trang thai node.
  assert.equal(lay.pos.owner.w, 88);
  assert.equal(lay.pos.owner.h, 24);
});

// ---------- two_party canvas ----------

test('two_party: 30 cho canonical, p16 dau Ben B, khong compact', () => {
  const { model, view } = build(test, {
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

test('two_party: swap occupied + keo ve Pool + card chi ten+cho', () => {
  const { model, view } = build(test, {
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

test('two_party: assign menu du 30 cho + swap bang ban phim', () => {
  const { model, view } = build(test, {
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

// ---------- Quan he tuong minh: chi o trong, khong tao ho so ----------

function relationMenu(view, nodeId) {
  const card = collect(view.el, (e) => e.dataset.nodeId === nodeId)[0];
  assert.ok(card, `thieu card ${nodeId}`);
  const control = byCls(card, 'js-node-relations')[0];
  assert.ok(control, `thieu menu quan he ${nodeId}`);
  assert.match(control.getAttribute('aria-label'), /Quan hệ của/);
  control.onclick();
  return byCls(view.el, 'modal')[0];
}

function chooseParent(dialog, nodeId, checked = true) {
  const input = collect(dialog, (e) =>
    e.tagName === 'INPUT' && e.type === 'checkbox' && e.value === nodeId)[0];
  assert.ok(input, `thieu lua chon cha/me ${nodeId}`);
  assert.equal(input.disabled, false);
  assert.equal(input.parentElement.tagName, 'LABEL', 'checkbox can label');
  input.checked = checked;
  input.onchange();
  return input;
}

test('quan he tung nguoi: them toi da 2 cha/me TRONG va chon lai o co san', (t) => {
  const nodes = seedSlots();
  nodes.find((n) => n.id === 'owner').personId = 'c1';
  nodes.find((n) => n.id === 'child_1').personId = 'c3';
  nodes.find((n) => n.id === 'child_1').parentSlotIds = [];
  const { model, view } = build(t, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes } });
  const stageBefore = structuredClone(model.state.stage);
  const child = model.state.diagram.nodes.find((n) => n.id === 'child_1');
  for (let i = 0; i < 2; i += 1) {
    const dialog = relationMenu(view, child.id);
    assert.equal(findBtns(dialog, 'Thêm cha/mẹ')[0].disabled, false);
    findBtns(dialog, 'Thêm cha/mẹ')[0].onclick();
    const parent = model.state.diagram.nodes.at(-1);
    assert.equal(parent.personId, null, 'khong duoc tu tao/gan nguoi');
    assert.ok(child.parentSlotIds.includes(parent.id));
  }
  let dialog = relationMenu(view, child.id);
  const full = findBtns(dialog, 'Thêm cha/mẹ')[0];
  assert.equal(full.disabled, true);
  const count = model.state.diagram.nodes.length;
  full.onclick(); // Handler cung giu gioi han khi goi truc tiep.
  assert.equal(model.state.diagram.nodes.length, count);
  findBtns(dialog, 'Chọn lại cha/mẹ')[0].onclick();
  dialog = byCls(view.el, 'modal')[0];
  assert.equal(collect(dialog, (e) => e.tagName === 'INPUT' &&
    e.value === child.id).length, 0, 'khong chon chinh minh lam cha/me');
  for (const id of [...child.parentSlotIds]) chooseParent(dialog, id, false);
  assert.equal(findBtns(dialog, 'Áp dụng')[0].disabled, true);
  chooseParent(dialog, 'owner');
  chooseParent(dialog, 'mother'); // O cha/me co san, chua gan nguoi.
  const third = collect(dialog, (e) => e.tagName === 'INPUT' &&
    e.value === 'father')[0];
  assert.equal(third.disabled, true, 'khong duoc chon qua 2 cha/me');
  findBtns(dialog, 'Áp dụng')[0].onclick();
  assert.deepEqual(child.parentSlotIds, ['owner', 'mother']);
  assert.deepEqual(model.state.stage, stageBefore, 'chi doi diagram, khong doi Stage');
});

test('them con: chon ro 1–2 cha/me, khong mac dinh vo/chong, huy khong tao o', (t) => {
  const nodes = seedSlots();
  nodes.find((n) => n.id === 'owner').personId = 'c1';
  nodes.find((n) => n.id === 'spouse').personId = 'c2';
  const { model, view } = build(t, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes } });
  const before = model.state.diagram.nodes.length;
  let dialog = relationMenu(view, 'owner');
  findBtns(dialog, 'Thêm con')[0].onclick();
  dialog = byCls(view.el, 'modal')[0];
  assert.ok(collect(dialog, (e) => e.tagName === 'INPUT')
    .every((e) => !e.checked), 'khong duoc tu chon cha/me');
  assert.equal(findBtns(dialog, 'Thêm ô con trống')[0].disabled, true);
  findBtns(dialog, 'Hủy')[0].onclick();
  assert.equal(model.state.diagram.nodes.length, before);
  for (const parentIds of [['owner'], ['owner', 'spouse']]) {
    dialog = relationMenu(view, 'owner');
    findBtns(dialog, 'Thêm con')[0].onclick();
    dialog = byCls(view.el, 'modal')[0];
    for (const id of parentIds) chooseParent(dialog, id);
    findBtns(dialog, 'Thêm ô con trống')[0].onclick();
    const child = model.state.diagram.nodes.at(-1);
    assert.equal(child.personId, null);
    assert.deepEqual(child.parentSlotIds, parentIds);
    assert.equal(child.spouseSlotId, null);
  }
  assert.equal(model.state.stage.people.length, INH_PEOPLE.length);
});

test('nhap du ong ba, cu, anh chi em, co chu, chau va chat qua menu va Pool', (t) => {
  const ids = ['source', 'parent', 'grandparent', 'great_grandparent',
    'sibling', 'parent_sibling', 'sibling_child', 'child', 'grandchild',
    'great_grandchild'];
  const people = ids.map((id) => ({ row_id: id, ho_ten: `Người ${id}` }));
  const owner = seedSlots().find((n) => n.id === 'owner');
  owner.personId = 'source';
  owner.parentSlotIds = [];
  owner.spouseSlotId = null;
  const { model, view } = build(t, { mode: 'case',
    seed: { people, nodes: [owner] } });
  const slotFor = { source: 'owner' };
  const add = (anchorPerson, personId, parent) => {
    let dialog = relationMenu(view, slotFor[anchorPerson]);
    findBtns(dialog, parent ? 'Thêm cha/mẹ' : 'Thêm con')[0].onclick();
    if (!parent) {
      dialog = byCls(view.el, 'modal')[0];
      chooseParent(dialog, slotFor[anchorPerson]);
      findBtns(dialog, 'Thêm ô con trống')[0].onclick();
    }
    const node = model.state.diagram.nodes.at(-1);
    assert.equal(node.personId, null);
    const poolCard = byCls(view.el, 'cd-pool-card')
      .find((c) => c.textContent.includes(`Người ${personId}`));
    assert.ok(poolCard);
    if (parent) {
      findBtns(poolCard, '→')[0].onclick();
      const assignDialog = byCls(view.el, 'modal')[0];
      findBtns(assignDialog, `Gán vào “${node.id}”`)[0].onclick();
    } else {
      const card = collect(view.el, (e) => e.dataset.nodeId === node.id)[0];
      card.dispatch('drop', personPayload(personId));
    }
    assert.equal(node.personId, personId);
    slotFor[personId] = node.id;
  };
  add('source', 'parent', true);
  add('parent', 'grandparent', true);
  add('grandparent', 'great_grandparent', true);
  add('parent', 'sibling', false);
  add('grandparent', 'parent_sibling', false);
  add('sibling', 'sibling_child', false);
  add('source', 'child', false);
  add('child', 'grandchild', false);
  add('grandchild', 'great_grandchild', false);
  const parentPeople = (pid) => model.state.diagram.nodes
    .find((n) => n.personId === pid).parentSlotIds
    .map((slot) => model.state.diagram.nodes.find((n) => n.id === slot).personId);
  assert.deepEqual(parentPeople('source'), ['parent']);
  assert.deepEqual(parentPeople('parent'), ['grandparent']);
  assert.deepEqual(parentPeople('grandparent'), ['great_grandparent']);
  assert.deepEqual(parentPeople('sibling'), ['parent']);
  assert.deepEqual(parentPeople('parent_sibling'), ['grandparent']);
  assert.deepEqual(parentPeople('sibling_child'), ['sibling']);
  assert.deepEqual(parentPeople('grandchild'), ['child']);
  assert.deepEqual(parentPeople('great_grandchild'), ['grandchild']);
  assert.equal(model.state.stage.people.length, ids.length);
  assert.equal(byCls(view.el, 'cd-pool-card').length, 0);
  assert.equal(byCls(view.el, 'cd-edge-parent').length, ids.length - 1);
});

test('menu quan he khong hien tren ho so khoa va two_party', (t) => {
  const nodes = seedSlots();
  nodes.find((n) => n.id === 'owner').personId = 'c1';
  const { model, view } = build(t, { mode: 'case',
    seed: { people: INH_PEOPLE, nodes } });
  assert.equal(byCls(view.el, 'js-node-relations').length, 1);
  model.state.locked = true;
  model.dismissNotice();
  assert.equal(byCls(view.el, 'js-node-relations').length, 0);
  model.newDraft('two_party');
  assert.equal(byCls(view.el, 'js-node-relations').length, 0);
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
  const { view } = build(t, { mode: 'case', client,
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

test('requiredSlots: engine yeu cau → tao father/mother/spouse/child', async () => {
  const client = {
    run: async (cmd) => {
      if (cmd === 'notary.diagram_evaluate') {
        return { ok: true, data: {
          evaluated_revision: 3,
          render_model: {
            engineVersion: 2, status: 'incomplete', allocations: {},
            breakdowns: [],
            requiredSlots: [
              { anchorSlotId: 'owner', reason: 'active_estate',
                slotTypes: ['father', 'mother', 'spouse', 'child'],
                minimumEmptyChildSlots: 1 },
              { anchorSlotId: 'child_1', reason: 'representation_branch',
                slotTypes: ['spouse', 'child'],
                minimumEmptyChildSlots: 1 }],
            warnings: [], errors: [], unresolvedEstates: [],
            conservation: {} } } };
      }
      return { ok: true, data: {} };
    },
  };
  const nodes = seedSlots().map((n) => ({ ...n }));
  // Owner da gan nguoi (da mat) nhung THIEU cha/me + vo/chong + con:
  // xoa quan he seed de engine yeu cau tat ca.
  for (const n of nodes) {
    if (n.id === 'owner') {
      n.personId = 'c1'; n.parentSlotIds = []; n.spouseSlotId = null;
    }
    if (n.id === 'father' || n.id === 'mother' ||
        n.id === 'spouse' || n.id === 'spouse_father' ||
        n.id === 'spouse_mother' || n.id === 'child_1') {
      n.deleted = true;            // gia lap bi xoa → required moi
    }
  }
  const { model, view } = build(test, {
    mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes } });
  // MIN-136: khong con nut "Đánh giá thử" — "Xem cách tính" trigger
  // evaluate + mo panel breakdown.
  const evalBtn = findBtns(view.el, 'Xem cách tính')[0];
  await evalBtn.onclick();
  const after = model.state.diagram.nodes.filter((n) => !n.deleted);
  const ids = new Set(after.map((n) => n.id));
  // owner can father+mother+spouse+child: seed ids 'father','mother',
  // 'spouse','child_1' bi deleted → id moi theo pattern <kind>_owner.
  const owner = after.find((n) => n.id === 'owner');
  assert.equal((owner.parentSlotIds || []).length, 2,
    'owner phai co 2 slot cha/me tu requiredSlots');
  for (const pid of owner.parentSlotIds) {
    assert.ok(ids.has(pid), `parent slot ${pid} khong duoc tao`);
  }
  const spouse = after.find((n) => n.spouseSlotId === 'owner');
  assert.ok(spouse, 'phai tao slot spouse tro ve owner');
  const kids = after.filter((n) =>
    !n.personId && (n.parentSlotIds || []).includes('owner'));
  assert.ok(kids.length >= 1, 'phai co ≥1 slot con trong cua owner');
  assert.ok(kids.every((n) => n.parentSlotIds.length === 1),
    'requiredSlots khong duoc suy vo/chong thanh cha/me thu hai');
  // Anchor child_1 bi deleted → request cua no bi bo qua.
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
  const { model, view } = build(test, {
    mode: 'case', client,
    seed: { people: INH_PEOPLE, nodes: seedSlots() } });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  assert.equal(model.state.diagram.nodes.length, 7,
    'anchor trong khong duoc sinh slot moi');
});

test('MIN-136: chủ đất sống → hint điền Ngày mất; đã mất → không hint', () => {
  const { model, view } = build(test, { mode: 'case', seed: {
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

test('zoom cluster: −/+ doi label; Mo rong mo overlay co canvas', () => {
  const { view, document } = build(test, { mode: 'draft-inh' });
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

test('pan: keo nen canvas → scrollLeft/Top doi, mouseup ket thuc', () => {
  const { view, document } = build(test, { mode: 'draft-inh' });
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

test('60 node thua ke: moi card render + layout khac nhau', () => {
  const { model, view } = build(test, { mode: 'draft-inh' });
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
      if (cmd === 'notary.diagram_save') {
        store.revision += 1;
        store.saved = structuredClone(payload.diagram.state);
        return { ok: true, data: {
          revision: store.revision,
          diagram: { state: structuredClone(store.saved),
                     render_model: null } } };
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
  const { model } = build(test, {
    mode: 'case', client,
    seed: { people: INH_PEOPLE, assets: [{ row_id: 'a1' }], nodes } });
  // Doi positions + them slot con → save.
  model.toggleNodePosition('owner', 'own', 1);
  model.toggleNodePosition('spouse', 'receive', 1);
  const sp = model.state.diagram.nodes.find((n) => n.id === 'spouse');
  sp.parentSlotIds = ['spouse_father', 'spouse_mother'];
  const r = await model.saveDiagram();
  assert.equal(r.ok, true, 'saveDiagram loi');
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
});

test('two_party: assign → save → reopen giu 30 cho + nguoi dung cho', async () => {
  const store = { saved: null, revision: 4 };
  const client = {
    run: async (cmd, payload) => {
      if (cmd === 'notary.diagram_save') {
        store.revision += 1;
        store.saved = structuredClone(payload.diagram.state);
        return { ok: true, data: {
          revision: store.revision,
          diagram: { state: structuredClone(store.saved),
                     render_model: null } } };
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
  const { model } = build(test, {
    mode: 'case', client,
    seed: { caseType: 'two_party', people: INH_PEOPLE, nodes } });
  // Seeded case co diagramDirty=false — can mot mutation that de save
  // khong noop (model.saveDiagram skip khi khong dirty).
  model.assignPerson('p7', 'c3');
  const r = await model.saveDiagram();
  assert.equal(r.ok, true);
  const model2 = M.createModel({ client });
  await model2.openCase(42);
  assert.equal(model2.state.diagram.nodes.length, 30);
  assert.equal(model2.state.diagram.nodes
    .find((n) => n.id === 'p16').personId, 'c1');
  assert.equal(model2.state.diagram.nodes
    .find((n) => n.id === 'p3').personId, 'c2');
});

// ---------- evaluate khong goi tren two_party ----------

test('two_party: assign/drop KHONG goi diagram_evaluate', () => {
  const { model, view, calls } = build(test, {
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
