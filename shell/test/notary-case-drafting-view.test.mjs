// View behavior tests cho workspace Soạn hồ sơ (MIN-129) — chay tren
// DOM stub (test/dom-stub.mjs), khong can Electron.
// Cover: action bar (Zalo disabled), asset col/person row tables,
// add/remove/reorder + Ctrl+Arrow, focus+value retention, cancel
// draft-only, land dialog draft-only, Pool committed-only, stageDirty
// gate cho evaluate/save diagram.
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

function fid(root, v) {
  return collect(root, (e) => e.dataset && e.dataset.fid === v)[0] || null;
}

// Build view + model voi client stub ghi lai moi command call (de chung
// minh apply/cancel KHONG goi command ra ngoai).
function build(t, { draft = true, confirm = true } = {}) {
  const { document } = makeDom();
  global.document = document;
  global.window = {
    G1_NOTARY_MODEL: M, G1_NOTARY_VIEW: VIEW,
    G1_NOTARY_INTAKE: INTAKE, G1_NOTARY_DIAGRAM: DIAGRAM,
    G1_NOTARY_WORD: WORD,
  };
  const calls = [];
  const client = {
    run: async (cmd, payload) => {
      calls.push([cmd, payload]);
      return { ok: true, data: {} };
    },
  };
  const model = M.createModel({ client });
  const view = VIEW.createNotaryModuleView({
    model, lib: L, notify: () => {},
    confirm: async () => confirm,
    pickFiles: async () => ({ ok: true, data: { files: [] } }),
    openPath: async () => ({ ok: true }),
    registerDroppedFile: null,
    cancelJob: async () => ({ ok: true }),
    runCommand: client.run,
  });
  // Gan vao body de isConnected/focus semantics giong renderer that.
  document.body.append(view.el);
  if (draft) {
    model.newDraft('inheritance');
  } else {
    seedExistingCase(model);
    model.dismissNotice();       // emit → render workspace
  }
  t.after(() => { delete global.document; delete global.window; });
  return { model, view, document, calls };
}

// Gia lap case da ton tai (committed data) — kieu model.state sau
// openCase thanh cong, khong can mock wire day du.
function seedExistingCase(model) {
  const s = model.state;
  s.status = 'ready';
  s.caseId = 42;
  s.caseInfo = { id: 42, case_type: 'inheritance',
                 document_type: 'khai_nhan', status: 'active',
                 locked: false, revision: 3 };
  s.backendMode = 'real';
  s.revision = 3;
  s.locked = false;
  s.unsupported = false;
  s.capabilities = { intake: ['image'], diagram: true,
                     word_export: true };
  s.committed = {
    people: [{ row_id: 'c1', ho_ten: 'Người Đã Lưu',
               ngay_sinh: '1955-01-01', so_giay_to: '001234' }],
    assets: [{ row_id: 'cA1', so_serial: 'S-001' }],
  };
  s.stage = structuredClone(s.committed);
  s.stage.owner_row_id = 'c1';
  s.committedDiagram = { version: 3, domain: 'inheritance', nodes: [] };
  s.diagram = structuredClone(s.committedDiagram);
}

// ---------- action bar ----------

test('action bar: Zalo visible + disabled; Hủy/Cập nhật/Nhập file/case-type đủ', () => {
  const { view } = build(test, { draft: true });
  const btns = collect(view.el, (e) => e.tagName === 'BUTTON');
  const zalo = btns.find((b) => b.textContent === 'Zalo');
  assert.ok(zalo, 'thiếu nút Zalo — phải visible, không ẩn');
  assert.equal(zalo.disabled, true, 'Zalo phải disabled');
  assert.ok(btns.some((b) => b.textContent === 'Nhập file'));
  assert.ok(btns.some((b) => b.textContent === 'Hủy thay đổi'));
  // nhap moi → nut chinh la "Lưu hồ sơ"; case thật la "Cập nhật".
  assert.ok(btns.some((b) => b.textContent === 'Lưu hồ sơ'));
  assert.ok(collect(view.el, (e) =>
    e.tagName === 'SELECT' &&
    e.getAttribute('aria-label') === 'Loại việc').length === 1);
});

test('action bar: case thật có nút Cập nhật (không có Lưu hồ sơ)', () => {
  const { view } = build(test, { draft: false });
  assert.ok(findBtns(view.el, 'Cập nhật').length >= 1);
  assert.equal(findBtns(view.el, 'Lưu hồ sơ').length, 0);
});

// ---------- asset columns ----------

test('asset table: add tạo cột Tài sản N + input data-fid; tối đa 3', () => {
  const { model, view } = build(test);
  const addBtn = findBtns(view.el, '+ Tài sản')[0];
  for (let i = 0; i < 3; i++) addBtn.onclick();
  assert.equal(model.state.stage.assets.length, 3);
  const cols = collect(view.el,
    (e) => e.classList.contains('cd-asset-col'));
  assert.equal(cols.length, 3);
  const a0 = model.state.stage.assets[0];
  assert.ok(fid(view.el, `a:${a0.row_id}:so_thua_dat`),
    'thiếu input data-fid cho so_thua_dat');
  assert.ok(fid(view.el, `a:${a0.row_id}:land`),
    'thiếu land chip data-fid');
  const addBtn2 = findBtns(view.el, '+ Tài sản')[0];
  assert.equal(addBtn2.disabled, true, 'quá 3 cột vẫn cho thêm');
  // Không render field v1.
  assert.ok(!collect(view.el, (e) =>
    /is_primary|isLandOwner|willReceive/.test(e.textContent)).length);
});

test('asset col: Ctrl+→ reorder qua model.moveAsset + giữ focus grip', () => {
  const { model, view, document } = build(test);
  model.addAsset(); model.addAsset();
  const [a, b] = model.state.stage.assets.map((x) => x.row_id);
  const grip = fid(view.el, `adrag:${a}`);
  assert.ok(grip, 'thiếu drag handle cột 1');
  grip.focus();
  grip.dispatch('keydown',
    { key: 'ArrowRight', ctrlKey: true, preventDefault() {} });
  assert.deepEqual(model.state.stage.assets.map((x) => x.row_id),
    [b, a], 'moveAsset không đổi thứ tự');
  // Sau rebuild focus quay lại grip CÙNG row_id (data-fid restore).
  const ae = document.activeElement;
  assert.ok(ae && ae.dataset.fid === `adrag:${a}`,
    'focus không quay lại grip của cùng asset');
});

test('asset delete: icon-x xóa đúng draft row', async () => {
  const { model, view } = build(test);
  model.addAsset(); model.addAsset();
  const [a] = model.state.stage.assets.map((x) => x.row_id);
  const del = fid(view.el, `adel:${a}`);
  // confirm tra true — xoa tai san giua co the doi vi tri cac cot sau.
  await del.onclick();
  assert.equal(model.state.stage.assets.length, 1);
  assert.equal(model.state.stage.assets[0].row_id !== a, true);
});

// ---------- people rows ----------

test('people table: add/remove row; Ctrl+↓ reorder giữ focus', () => {
  const { model, view, document } = build(test);
  model.addPerson(); model.addPerson();
  const [p1, p2] = model.state.stage.people.map((x) => x.row_id);
  const grip = fid(view.el, `pdrag:${p1}`);
  grip.focus();
  grip.dispatch('keydown',
    { key: 'ArrowDown', ctrlKey: true, preventDefault() {} });
  assert.deepEqual(model.state.stage.people.map((x) => x.row_id),
    [p2, p1], 'reorder hàng không đổi thứ tự stage');
  assert.equal(model.state.stageDirty, true);
  assert.ok(document.activeElement.dataset.fid === `pdrag:${p1}`,
    'focus không quay lại grip đúng row');
  const del = fid(view.el, `pdel:${p2}`);
  del.onclick();
  assert.equal(model.state.stage.people.length, 1);
});

test('people table: inheritance có cột Để lại radio → setOwnerRow', () => {
  const { model, view } = build(test);
  model.addPerson(); model.addPerson();
  const [p1] = model.state.stage.people.map((x) => x.row_id);
  const radio = fid(view.el, `p:${p1}:owner`);
  assert.ok(radio, 'thiếu radio Để lại');
  assert.equal(radio.type, 'radio');
  radio.onchange();
  assert.equal(model.state.stage.owner_row_id, p1);
});

test('typing giữ focus+value: emit nền không rebuild input đang gõ', () => {
  const { model, view, document } = build(test);
  model.addPerson();
  const rid = model.state.stage.people[0].row_id;
  const inp = fid(view.el, `p:${rid}:ho_ten`);
  inp.value = 'Nguyễn Văn';
  inp.setSelectionRange(3, 8);
  inp.focus();
  // Emit tu action khac (them nguoi) trong luc dang go → defer rebuild.
  model.addPerson();
  assert.ok(inp.isConnected,
    'input đang gõ bị rebuild mất (focus/value bị hủy)');
  assert.equal(inp.value, 'Nguyễn Văn');
  // Sau khi roi focus, emit ke tiep rebuild moi — nguoi moi xuat hien.
  document.activeElement = null;
  model.dismissNotice();
  const rid2 = model.state.stage.people[1].row_id;
  assert.ok(fid(view.el, `p:${rid2}:ho_ten`),
    'rebuild sau khi blur không có dòng mới');
});

// ---------- cancel draft ----------

test('cancel: case thật restore Stage+Diagram về committed — không gọi command', async () => {
  const { model, view, calls } = build(test, { draft: false });
  calls.length = 0;
  // Dirty: them nguoi vao stage draft + diagram node.
  model.addPerson();
  model.addSlot('owner');
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.diagramDirty, true);
  const undo = findBtns(view.el, 'Hủy thay đổi')[0];
  await undo.onclick();
  assert.equal(model.state.stage.people.length, 1,
    'stage không về committed');
  assert.equal(model.state.stage.people[0].row_id, 'c1');
  assert.equal(model.state.stageDirty, false);
  assert.equal(model.state.diagramDirty, false);
  assert.equal(model.state.diagram.nodes.length, 0,
    'diagram draft không về committed');
  assert.equal(calls.length, 0,
    'Hủy gọi command ra ngoài — phải client-only');
});

test('cancel: nháp mới reset về nháp trống cùng loại việc', async () => {
  const { model, view } = build(test);
  model.addPerson();
  model.updateCaseMeta('document_type', 'thoa_thuan');
  const undo = findBtns(view.el, 'Hủy thay đổi')[0];
  await undo.onclick();
  assert.equal(model.state.stage.people.length, 0);
  assert.equal(model.state.caseInfo.case_type, 'inheritance');
  assert.equal(model.state.caseId, null);
  assert.equal(model.state.stageDirty, false);
});

test('cancel: confirm=false không đụng draft', async () => {
  const { model, view } = build(test, { confirm: false });
  model.addPerson();
  const undo = findBtns(view.el, 'Hủy thay đổi')[0];
  await undo.onclick();
  assert.equal(model.state.stage.people.length, 1,
    'người dùng chọn Ở lại mà draft vẫn mất');
});

// ---------- land dialog ----------

test('land dialog: Áp dụng chỉ ghi draft Stage (dirty, không command)', async () => {
  const { model, view, calls } = build(test);
  calls.length = 0;
  model.addAsset();
  const rid = model.state.stage.assets[0].row_id;
  fid(view.el, `a:${rid}:land`).onclick();
  const modal = collect(view.el,
    (e) => e.classList.contains('modal'))[0];
  assert.ok(modal, 'land chip không mở modal');
  findBtns(modal, '+ Loại đất')[0].onclick();     // + 1 cột trong draft
  findBtns(modal, 'Áp dụng')[0].onclick();
  const rows = model.state.stage.assets[0].land_rows;
  assert.equal(rows.length, 1, 'Áp dụng không ghi land_rows vào draft');
  assert.equal(rows[0].loai_dat, 'ONT');
  assert.equal(model.state.stageDirty, true);
  assert.equal(calls.filter(([c]) =>
    /workspace|commit|stage/.test(c)).length, 0,
    'Áp dụng phải draft-only — không gọi command ra ngoài');
});

test('land dialog: Hủy không đụng draft Stage', () => {
  const { model, view } = build(test);
  model.addAsset();
  const rid = model.state.stage.assets[0].row_id;
  model.state.stageDirty = false;
  fid(view.el, `a:${rid}:land`).onclick();
  const modal = collect(view.el,
    (e) => e.classList.contains('modal'))[0];
  findBtns(modal, '+ Loại đất')[0].onclick();     // sửa draft dialog
  findBtns(modal, 'Hủy')[0].onclick();
  const a = model.state.stage.assets[0];
  assert.equal((a.land_rows || []).length, 0,
    'Hủy vẫn ghi land_rows vào Stage draft');
});

// ---------- Pool committed-only ----------

test('Pool chỉ đọc committed — draft Stage mới không lộ vào Pool', () => {
  const { model, view } = build(test, { draft: false });
  // Draft stage co them nguoi MOI chua commit.
  model.addPerson();
  model.state.stage.people[1].ho_ten = 'Nháp Chưa Cập Nhật';
  const names = collect(view.el,
    (e) => e.classList.contains('cd-pool-nm'))
    .map((e) => e.textContent);
  assert.ok(names.some((n) => n.includes('Người Đã Lưu')),
    'thiếu người committed trong Pool');
  assert.ok(!names.some((n) => n.includes('Nháp Chưa Cập Nhật')),
    'Pool lộ draft Stage — vi phạm committed-only');
  // Asset committed hien trong pool.
  assert.ok(collect(view.el,
    (e) => e.classList.contains('cd-pool-card')).length >= 2);
});

test('Pool nháp mới: chưa commit → face hướng dẫn Cập nhật', () => {
  const { model, view } = build(test);
  model.addPerson();
  const pane = collect(view.el,
    (e) => e.classList.contains('cd-pool'))[0];
  assert.ok(pane);
  assert.match(pane.textContent, /Cập nhật Stage trước/);
  assert.equal(collect(pane,
    (e) => e.classList.contains('cd-pool-card')).length, 0,
    'nháp mới vẫn render pool card — lộ draft');
});

test('Pool card payload giữ text/plain {kind,row_id} cho P7', () => {
  const { view } = build(test, { draft: false });
  const card = collect(view.el,
    (e) => e.classList.contains('cd-pool-card'))[0];
  const sent = [];
  card.dispatch('dragstart', {
    dataTransfer: {
      setData: (t, v) => sent.push([t, v]),
    },
  });
  assert.equal(sent.length, 1);
  assert.equal(sent[0][0], 'text/plain');
  assert.deepEqual(JSON.parse(sent[0][1]),
    { kind: 'person', row_id: 'c1' });
});

// ---------- stageDirty gate ----------

test('stageDirty gate: Đánh giá/Lưu sơ đồ disabled khi Stage chưa cập nhật', () => {
  const { model, view } = build(test, { draft: false });
  model.addSlot('owner');            // diagramDirty → save enable được
  model.state.stageDirty = true;     // stage chưa cập nhật
  model.dismissNotice();
  const evalBtn = findBtns(view.el, 'Đánh giá thử')[0];
  const save = findBtns(view.el, 'Lưu sơ đồ')[0];
  assert.equal(evalBtn.disabled, true,
    'Đánh giá vẫn bấm được khi stageDirty');
  assert.equal(save.disabled, true,
    'Lưu sơ đồ vẫn bấm được khi stageDirty');
  assert.ok(collect(view.el, (e) =>
    e.textContent === 'Cập nhật Stage trước').length >= 1,
    'thiếu pill báo gate');
});
