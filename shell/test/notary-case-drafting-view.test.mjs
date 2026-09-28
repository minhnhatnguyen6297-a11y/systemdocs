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
function build(t, { draft = true, confirm = true, respond = null } = {}) {
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
      const r = respond && respond(cmd, payload);
      return r || { ok: true, data: {} };
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


// ---------- MIN-133 W2: thanh trên + Stage mật độ cao ----------

function topbar(root) {
  return collect(root, (e) => e.classList.contains('cd-topbar'))[0];
}

test('MIN-133 D5: một thanh trên = tab cục bộ + hành động (không actionbar riêng)', () => {
  const { view } = build(test, { draft: true });
  const bars = collect(view.el, (e) => e.classList.contains('cd-topbar'));
  assert.equal(bars.length, 1, 'phải có đúng một .cd-topbar');
  const bar = bars[0];
  assert.equal(bar.parentElement, view.el,
    'thanh trên nằm trực tiếp dưới .cd-root');
  const nav = collect(bar, (e) => e.classList.contains('cd-localnav'))[0];
  assert.ok(nav, 'tab cục bộ phải nằm trong thanh trên');
  assert.deepEqual(collect(nav, (e) => e.classList.contains('cd-tab'))
    .map((b) => b.textContent), ['Tổng quan hồ sơ', 'Soạn hồ sơ', 'Word']);
  const actions = collect(bar,
    (e) => e.classList.contains('cd-topbar-actions'))[0];
  assert.ok(actions && !actions.hidden);
  const labels = collect(actions, (e) =>
    e.tagName === 'BUTTON' || e.tagName === 'SELECT')
    .map((e) => e.tagName === 'SELECT' ? 'select' : e.textContent);
  assert.deepEqual(labels,
    ['select', 'Nhập file', 'Zalo', 'Hủy thay đổi', 'Lưu hồ sơ']);
  assert.equal(collect(view.el,
    (e) => e.classList.contains('actionbar')).length, 0,
    'còn .actionbar riêng — phải gộp vào thanh trên');
});

test('MIN-133 D4: không nút ‹, tiêu đề, pill Nháp, nhãn trạng thái lưu', () => {
  const { model, view } = build(test, { draft: true });
  model.addPerson();                          // dirty
  const all = collect(view.el, () => true);
  assert.ok(!all.some((e) => e.classList.contains('ab-back')), 'còn nút back');
  assert.ok(!all.some((e) => e.classList.contains('ab-title')), 'còn tiêu đề');
  assert.ok(!all.some((e) => e.classList.contains('save-state')),
    'còn nhãn trạng thái lưu');
  const txt = view.el.textContent;
  for (const bad of ['Soạn văn bản', 'Nháp — chưa lưu', 'Chưa lưu hồ sơ',
                     'Chưa lưu:', 'Đã lưu · phiên bản']) {
    assert.ok(!txt.includes(bad), `còn chuỗi "${bad}"`);
  }
  // Tín hiệu duy nhất: chấm dirty trên nút Lưu hồ sơ.
  const save = findBtns(topbar(view.el), 'Lưu hồ sơ')[0];
  assert.equal(collect(save,
    (e) => e.classList.contains('dirty-dot')).length, 1);
  assert.match(save.getAttribute('aria-label'), /có thay đổi chưa lưu/);
});

test('MIN-133 D4: case thật — chấm dirty theo stageDirty; pill loại · HS', () => {
  const { model, view } = build(test, { draft: false });
  const upd = () => findBtns(topbar(view.el), 'Cập nhật')[0];
  const dots = (b) => collect(b, (e) => e.classList.contains('dirty-dot'));
  assert.equal(dots(upd()).length, 0);
  assert.equal(collect(topbar(view.el), (e) =>
    e.classList.contains('cd-case-pill') &&
    e.textContent === 'Thừa kế · HS-42').length, 1);
  assert.equal(collect(topbar(view.el), (e) => e.tagName === 'SELECT').length,
    0, 'case thật không cho đổi loại việc');
  model.addPerson();
  assert.equal(dots(upd()).length, 1);
});

test('MIN-133: đang gõ trong Stage — nút Cập nhật vẫn hiện chấm dirty (defer rebuild)', () => {
  const { model, view } = build(test, { draft: false });
  const rid = model.state.stage.people[0].row_id;
  const inp = fid(view.el, `p:${rid}:ho_ten`);
  inp.focus();
  inp.value = 'Người Đã Sửa';
  inp.oninput();
  assert.ok(inp.isConnected, 'input đang gõ bị rebuild');
  const upd = findBtns(topbar(view.el), 'Cập nhật')[0];
  assert.equal(upd.disabled, false);
  assert.equal(collect(upd,
    (e) => e.classList.contains('dirty-dot')).length, 1);
});

test('MIN-133: tab Tổng quan — ẩn phần hành động của thanh trên', () => {
  const { view } = build(test, { draft: true });
  const bar = topbar(view.el);
  const actions = collect(bar,
    (e) => e.classList.contains('cd-topbar-actions'))[0];
  findBtns(bar, 'Tổng quan hồ sơ')[0].onclick();
  assert.equal(actions.hidden, true);
  assert.equal(findBtns(bar, 'Lưu hồ sơ').length, 0);
  findBtns(bar, 'Soạn hồ sơ')[0].onclick();
  assert.equal(actions.hidden, false);
  assert.equal(findBtns(bar, 'Lưu hồ sơ').length, 1);
});

test('MIN-133: đổi Loại việc trên thanh trên → Stage dựng lại ngay, select giữ focus', () => {
  const { model, view, document } = build(test, { draft: true });
  model.addPerson();
  const sel = collect(topbar(view.el), (e) =>
    e.tagName === 'SELECT' && e.classList.contains('cd-case-type'))[0];
  assert.ok(sel, 'thiếu select cd-case-type');
  const ownerCols = () => collect(view.el,
    (e) => e.classList.contains('cd-owner-col')).length;
  assert.equal(ownerCols(), 1);
  sel.focus();
  sel.value = 'two_party';
  sel.onchange();
  assert.equal(model.state.caseInfo.case_type, 'two_party');
  // Stage KHÔNG bị hoãn dù select đang focus (select nằm ngoài panel).
  assert.equal(ownerCols(), 0, 'đổi sang Hai bên mà cột Để lại vẫn còn');
  // Select đang focus không bị thay node (dropdown không đóng).
  assert.ok(sel.isConnected);
  assert.equal(document.activeElement, sel);
});

test('MIN-133 D2: không card Thông tin hồ sơ; Lưu hồ sơ vẫn gửi meta mặc định đủ', async () => {
  const respond = (cmd, p) => cmd === 'notary.workspace_create'
    ? { ok: true, data: {
        created: true, backend_mode: 'real',
        case: { id: 77, case_type: p.case.case_type,
                document_type: p.case.document_type, status: 'active',
                locked: false, revision: 1 },
        capabilities: { intake: [], diagram: true, word_export: true },
        stage: p.stage, diagram: { state: p.diagram.state } } }
    : null;
  const { model, view, calls } = build(test, { draft: true, respond });
  assert.ok(!view.el.textContent.includes('Thông tin hồ sơ'),
    'còn card Thông tin hồ sơ');
  for (const lbl of ['Loại văn bản', 'Ngày lập hồ sơ', 'Nơi niêm yết',
                     'Ghi chú']) {
    assert.equal(collect(view.el,
      (e) => e.getAttribute('aria-label') === lbl).length, 0,
      `còn ô "${lbl}"`);
  }
  const owner = model.addPerson({ ho_ten: 'Người Để Lại' });
  model.setOwnerRow(owner.row_id);
  model.addAsset({ so_serial: 'AA000001' });
  calls.length = 0;
  await findBtns(topbar(view.el), 'Lưu hồ sơ')[0].onclick();
  const call = calls.find(([c]) => c === 'notary.workspace_create');
  assert.ok(call, 'Lưu hồ sơ không gọi workspace_create');
  const meta = call[1].case;
  assert.deepEqual(Object.keys(meta).sort(), ['case_type', 'document_type',
    'ghi_chu', 'ngay_lap_ho_so', 'noi_niem_yet']);
  assert.equal(meta.case_type, 'inheritance');
  assert.equal(meta.document_type, 'khai_nhan',
    'document_type phải = mặc định model');
  assert.equal(meta.ngay_lap_ho_so, null, 'ngay_lap_ho_so để backend tự điền');
  assert.equal(meta.noi_niem_yet, null);
  assert.equal(meta.ghi_chu, null);
  assert.equal(call[1].stage.owner_row_id, owner.row_id);
  assert.equal(model.state.caseId, 77, 'saveDraft không thành công');
  assert.equal(findBtns(topbar(view.el), 'Cập nhật').length, 1,
    'sau lưu nút chính phải chuyển sang Cập nhật');
});

test('MIN-133 D1: bảng Người 7 cột theo DB Customer + colgroup cố định', () => {
  const { model, view } = build(test);
  model.addPerson();
  const t = collect(view.el, (e) => e.classList.contains('cd-ptbl'))[0];
  assert.ok(t.classList.contains('cd-stage-tbl'));
  const heads = collect(t, (e) => e.tagName === 'TH')
    .map((e) => e.textContent);
  assert.deepEqual(heads, ['', 'Để lại', 'Họ tên', 'Giới tính', 'Ngày sinh',
    'Ngày mất', 'Số giấy tờ', 'Ngày cấp', 'Địa chỉ', '']);
  const cols = collect(t, (e) => e.tagName === 'COL').map((c) => c.className);
  assert.deepEqual(cols, ['cd-pcol-drag', 'cd-pcol-owner', 'cd-pcol-ho_ten',
    'cd-pcol-gioi_tinh', 'cd-pcol-ngay_sinh', 'cd-pcol-ngay_chet',
    'cd-pcol-so_giay_to', 'cd-pcol-ngay_cap', 'cd-pcol-dia_chi',
    'cd-pcol-del']);
  const rid = model.state.stage.people[0].row_id;
  for (const k of ['noi_cap', 'place_of_origin']) {
    assert.equal(fid(view.el, `p:${rid}:${k}`), null, `còn ô ${k}`);
  }
  assert.ok(!view.el.textContent.includes('Nơi cấp'));
  assert.ok(!view.el.textContent.includes('Nguyên quán'));
  // ô nhập dùng .cd-cell (nằm trong ô, không nền) + tooltip = giá trị.
  const inp = fid(view.el, `p:${rid}:dia_chi`);
  assert.ok(inp.classList.contains('cd-cell'));
  inp.value = 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An';
  inp.oninput();
  assert.equal(inp.title, inp.value);
});

test('MIN-133 D1: two_party — colgroup khớp số cột (không Để lại)', () => {
  const { model, view } = build(test);
  model.updateCaseMeta('case_type', 'two_party');
  model.addPerson();
  const t = collect(view.el, (e) => e.classList.contains('cd-ptbl'))[0];
  const cols = collect(t, (e) => e.tagName === 'COL');
  const ths = collect(t, (e) => e.tagName === 'TH');
  assert.equal(cols.length, ths.length, 'colgroup lệch số cột header');
  assert.equal(cols.length, 9);
});

test('MIN-133 D1: noi_cap/place_of_origin cũ giữ nguyên trên row và lên wire khi Cập nhật', async () => {
  const { model, view, calls, document } = build(test, { draft: false });
  const row = model.state.stage.people[0];
  row.noi_cap = 'Cục CS QLHC về TTXH';
  row.place_of_origin = 'Hà Nội';
  model.state.committed.people[0].noi_cap = row.noi_cap;
  model.state.committed.people[0].place_of_origin = row.place_of_origin;
  model.dismissNotice();                     // rerender
  const inp = fid(view.el, `p:${row.row_id}:ho_ten`);
  inp.value = 'Người Đã Sửa Tên';
  inp.oninput();
  document.activeElement = null;
  calls.length = 0;
  await findBtns(topbar(view.el), 'Cập nhật')[0].onclick();
  const call = calls.find(([c]) => c === 'notary.workspace_commit_stage');
  assert.ok(call, 'Cập nhật không gọi workspace_commit_stage');
  const sent = call[1].stage.people[0];
  assert.equal(sent.ho_ten, 'Người Đã Sửa Tên');
  assert.equal(sent.noi_cap, 'Cục CS QLHC về TTXH', 'mất noi_cap trên wire');
  assert.equal(sent.place_of_origin, 'Hà Nội', 'mất place_of_origin trên wire');
});

test('MIN-133: lỗi trường không có ô (noi_cap) vẫn hiện ở đầu card Người', () => {
  const { model, view } = build(test, { draft: false });
  model.state.fieldErrors = [{ row_id: 'c1', field: 'noi_cap',
                               code: 'invalid', message: 'Nơi cấp sai' }];
  model.dismissNotice();
  const card = collect(view.el, (e) => e.classList.contains('cd-people'))[0];
  assert.match(card.textContent, /Nơi cấp sai/);
});

test('MIN-133: bảng Tài sản colgroup nhãn + mỗi tài sản một cột', () => {
  const { model, view } = build(test);
  model.addAsset(); model.addAsset();
  const t = collect(view.el, (e) => e.classList.contains('cd-tbl'))[0];
  assert.ok(t.classList.contains('cd-stage-tbl'));
  assert.deepEqual(collect(t, (e) => e.tagName === 'COL')
    .map((c) => c.className), ['cd-acol-label', 'cd-acol', 'cd-acol']);
  const a0 = model.state.stage.assets[0].row_id;
  assert.ok(fid(view.el, `a:${a0}:dia_chi`).classList.contains('cd-cell'));
});
