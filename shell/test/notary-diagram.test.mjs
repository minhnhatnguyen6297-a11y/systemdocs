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

function seedSlots() {
  return structuredClone(M.seedDiagramSlots([]));
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

test('inheritance canvas: seed 7 slot → card + edges + hint + role', () => {
  const { view } = build(test, { mode: 'draft-inh' });
  const cards = byCls(view.el, 'cd-node');
  assert.equal(cards.length, 7, 'seed phai co 7 slot cards');
  // Edges SVG: 6 cha-con + 1 vo-chong.
  const svg = collect(view.el, (e) =>
    e.classList.contains('cd-canvas-edges'))[0];
  assert.ok(svg, 'thieu svg edges');
  // Path canh co marker-end; path mui ten nam trong <defs><marker>.
  const paths = collect(svg, (e) =>
    e.tagName === 'PATH' && e.getAttribute('marker-end'));
  assert.equal(paths.length, 7,
    `so edge path = 6 cha-con + 1 vo-chong, dang ${paths.length}`);
  assert.ok(paths.some((p) =>
    p.getAttribute('class') === 'cd-edge-spouse'), 'thieu edge vo/chong');
  // Card trong: hint tha the + role label.
  const father = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  assert.ok(father, 'thieu node father');
  assert.match(father.textContent, /Trống — thả thẻ Pool vào đây/);
  assert.match(father.textContent, /cha\/mẹ của/);
  // owner card: nhan "Người để lại" + 2 hang chip.
  const owner = collect(view.el, (e) =>
    e.dataset.nodeId === 'owner')[0];
  assert.match(owner.textContent, /Người để lại/);
  const rows = collect(owner, (e) =>
    e.classList.contains('cd-posrow'));
  assert.equal(rows.length, 2, 'phai co 2 hang chip');
  assert.match(rows[0].textContent, /Chủ đất/);
  assert.match(rows[1].textContent, /Nhận đất/);
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
  // Rebuild: card gio co ten + nam sinh–mat + vai tro + bo gan + →.
  const after = collect(view.el, (e) =>
    e.dataset.nodeId === 'father')[0];
  assert.match(after.textContent, /Người Đã Lưu/);
  assert.match(after.textContent, /1955 – 2020/);
  assert.ok(findBtns(after, 'Bỏ gán').length === 1);
  assert.ok(findBtns(after, '→').length === 1,
    'can nut → cho duong ban phim');
  assert.ok(!/Trống — thả thẻ/.test(after.textContent));
});

test('chip own/receive doc lap, multi-select, disable > so asset', () => {
  const { model, view } = build(test, { mode: 'draft-inh' });
  model.addAsset(); model.addAsset();         // positions 1,2 enabled
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
  const evalBtn = findBtns(view.el, 'Đánh giá thử')[0];
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
  await findBtns(view.el, 'Đánh giá thử')[0].onclick();
  assert.equal(model.state.diagram.nodes.length, 7,
    'anchor trong khong duoc sinh slot moi');
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
  for (let i = 0; i < 53; i += 1) model.addSlot();
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
