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
const ERRORS = require('../src/renderer/notary/error-catalog.js');
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
function build(t, { draft = true, confirm = true, confirmSeen = null, respond = null } = {}) {
  const { document } = makeDom();
  global.document = document;
  global.window = {
    G1_NOTARY_MODEL: M, G1_NOTARY_VIEW: VIEW,
    G1_NOTARY_INTAKE: INTAKE, G1_NOTARY_DIAGRAM: DIAGRAM,
    G1_NOTARY_WORD: WORD, G1_NOTARY_ERRORS: ERRORS,
  };
  const calls = [];
  const notifications = [];
  const client = {
    run: async (cmd, payload) => {
      calls.push([cmd, payload]);
      const r = respond && respond(cmd, payload);
      return r || { ok: true, data: {} };
    },
  };
  const model = M.createModel({ client });
  const view = VIEW.createNotaryModuleView({
    model, lib: L, notify: (message) => notifications.push(message),
    confirm: async (args) => { if (confirmSeen) confirmSeen.push(args); return confirm; },
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
  return { model, view, document, calls, notifications };
}

// Gia lap case da ton tai (committed data) — kieu model.state sau
// openCase thanh cong, khong can mock wire day du.
function seedExistingCase(model) {
  const s = model.state;
  s.status = 'ready';
  s.caseId = 42;
  s.caseInfo = { id: 42, case_type: 'inheritance',
                 document_type: 'khai_nhan', status: 'active',
                 locked: false, revision: 3,
                 ngay_lap_ho_so: '2024-05-01', noi_niem_yet: 'xã Cũ',
                 nguoi_nhan_uy_quyen: 'Người Nhận Gốc',
                 nguoi_nhan_uy_quyen_id: 7, noi_dung_viec: 'Việc gốc',
                 ghi_chu: null };
  // đợt 3 (MIN-141): baseline de Huy khoi phuc meta — applyWorkspace
  // that gan tu data.case; test seed truc tiep.
  s.committedCaseInfo = structuredClone(s.caseInfo);
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

test('MIN-136: bảng Người KHÔNG còn cột Để lại — owner chọn qua sơ đồ', () => {
  const { model, view } = build(test);
  model.addPerson(); model.addPerson();
  const [p1] = model.state.stage.people.map((x) => x.row_id);
  // Khong con radio/input owner tren bang Nguoi.
  assert.equal(fid(view.el, `p:${p1}:owner`), null,
    'con radio/oi Để lại');
  const t = collect(view.el, (e) => e.classList.contains('cd-ptbl'))[0];
  assert.ok(!t.textContent.includes('Để lại'),
    'con header/cell Để lại');
  // owner_row_id van set duoc qua model (so do gan vao node owner) va
  // hang owner van duoc to mau.
  model.setOwnerRow(p1);
  assert.equal(model.state.stage.owner_row_id, p1);
  let row = fid(view.el, `p:${p1}:ho_ten`);
  while (row && row.tagName !== 'TR') row = row.parentElement;
  assert.ok(row && row.classList.contains('cd-row-owner'),
    'hang owner khong duoc highlight sau khi chon qua so do');
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
  // đợt 3 (MIN-141): customer_list nap danh ba uy quyen luc render la
  // hop le — "client-only" nghia la Hủy khong goi command ghi/workspace.
  assert.equal(calls.filter(([c]) =>
    /workspace|diagram|commit|intake|word/.test(c)).length, 0,
    'Hủy gọi command workspace ra ngoài — phải client-only');
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

// ---------- MIN-141 review: bỏ thoi_han LẺ cấp tài sản ----------

test('MIN-141: asset table KHÔNG còn ô Thời hạn lẻ; dialog cụm đất vẫn có', () => {
  const { model, view } = build(test);
  model.addAsset();
  const rid = model.state.stage.assets[0].row_id;
  assert.equal(fid(view.el, `a:${rid}:thoi_han`), null,
    'còn input thoi_han lẻ cấp tài sản');
  const tbl = collect(view.el, (e) => e.classList.contains('cd-tbl'))[0];
  assert.equal(collect(tbl, (e) => e.tagName === 'TD' &&
    e.textContent.trim() === 'Thời hạn').length, 0,
    'còn hàng nhãn "Thời hạn" lẻ trong bảng tài sản');
  // Thời hạn chỉ sống trong popup Loại đất theo từng cụm.
  fid(view.el, `a:${rid}:land`).onclick();
  const modal = collect(view.el,
    (e) => e.classList.contains('modal'))[0];
  findBtns(modal, '+ Loại đất')[0].onclick();
  assert.ok(modal.textContent.includes('Thời hạn'),
    'dialog cụm đất mất ô Thời hạn');
});

test('MIN-141: commit Stage KHÔNG gửi thoi_han lẻ; land_rows.thoi_han giữ', async () => {
  const { model, view, calls } = build(test, { draft: false });
  // Giả lập tài sản committed mang giá trị lẻ lịch sử + 1 cụm đất.
  const asset = model.state.stage.assets[0];
  asset.thoi_han = 'Lâu dài';
  asset.land_rows = [{ loai_dat: 'ONT', dien_tich: '50',
                       thoi_han: 'Lâu dài' }];
  model.state.stageDirty = true;
  calls.length = 0;
  await findBtns(topbar(view.el), 'Cập nhật')[0].onclick();
  const call = calls.find(([c]) => c === 'notary.workspace_commit_stage');
  assert.ok(call, 'Cập nhật không gọi workspace_commit_stage');
  const sent = call[1].stage.assets[0];
  assert.equal('thoi_han' in sent, false,
    'wire vẫn gửi thoi_han lẻ như dữ liệu mới');
  assert.equal(sent.land_rows[0].thoi_han, 'Lâu dài',
    'mất thoi_han của cụm đất trên wire');
});

// ---------- Pool committed-only ----------

test('Pool case thật = committed − đã gán; KHÔNG có thẻ tài sản (MIN-136)', () => {
  const { model, view } = build(test, { draft: false });
  // Draft stage co them nguoi MOI chua commit → KHONG lo vao Pool
  // (case that van lay committed lam nguon — §2).
  model.addPerson();
  model.state.stage.people[1].ho_ten = 'Nháp Chưa Cập Nhật';
  const names = collect(view.el,
    (e) => e.classList.contains('cd-pool-nm'))
    .map((e) => e.textContent);
  assert.ok(names.some((n) => n.includes('Người Đã Lưu')),
    'thiếu người committed trong Pool');
  assert.ok(!names.some((n) => n.includes('Nháp Chưa Cập Nhật')),
    'Pool lộ draft Stage — vi phạm committed-only');
  // MIN-136: Pool chi con nguoi — asset khong xuong Pool vi khong co
  // flow keo-tha tai san (dead UI).
  assert.equal(collect(view.el,
    (e) => e.classList.contains('cd-pool-card')).length, 1);
  const pane = collect(view.el, (e) => e.classList.contains('cd-pool'))[0];
  assert.ok(!/Tài sản/.test(pane.textContent),
    'Pool van hien the tai san');
});

test('MIN-136: Pool nháp mới lấy stage.people — thả được ngay chưa lưu', () => {
  const { model, view } = build(test);
  // Stage trong → huong dan them nguoi (khong phai "Cap nhat truoc"
  // vi nhap moi khong co gi de cap nhat).
  let pane = collect(view.el, (e) => e.classList.contains('cd-pool'))[0];
  assert.match(pane.textContent, /Chưa có người — thêm ở bảng Người/);
  // Them nguoi vao stage nhap → xuat hien trong Pool ngay.
  model.addPerson();
  model.state.stage.people[0].ho_ten = 'Người Nháp Mới';
  model.dismissNotice();
  pane = collect(view.el, (e) => e.classList.contains('cd-pool'))[0];
  const card = collect(pane, (e) =>
    e.classList.contains('cd-pool-card') &&
    /Người Nháp Mới/.test(e.textContent))[0];
  assert.ok(card, 'nguoi nhap moi khong xuat hien trong Pool');
  // Gan vao o owner → ra khoi Pool + owner_row_id sync.
  const ownerNode = collect(view.el, (e) =>
    e.dataset.nodeId === 'owner')[0];
  card.dispatch('dragstart', {
    dataTransfer: { setData() {} } });
  const rid = model.state.stage.people[0].row_id;
  model.assignPerson('owner', rid);
  assert.equal(model.state.stage.owner_row_id, rid);
  assert.equal(collect(view.el, (e) =>
    e.classList.contains('cd-pool-card')).length, 0,
    'nguoi da gan van con trong Pool');
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

test('stageDirty gate: Xem cách tính/Lưu sơ đồ disabled khi Stage chưa cập nhật', () => {
  const { model, view } = build(test, { draft: false });
  model.addSlot('owner');            // diagramDirty → save enable được
  model.state.stageDirty = true;     // stage chưa cập nhật
  model.dismissNotice();
  // MIN-136: nut "Danh gia thu" da bo — gate nam tren "Xem cach tinh".
  assert.equal(findBtns(view.el, 'Đánh giá thử').length, 0,
    'con nút Đánh giá thử');
  assert.equal(findBtns(view.el, '+ Slot').length, 0,
    'con nút + Slot');
  const evalBtn = findBtns(view.el, 'Xem cách tính')[0];
  const save = findBtns(view.el, 'Lưu sơ đồ')[0];
  assert.equal(evalBtn.disabled, true,
    'Xem cách tính vẫn bấm được khi stageDirty');
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
  sel.focus();
  sel.value = 'two_party';
  sel.onchange();
  assert.equal(model.state.caseInfo.case_type, 'two_party');
  // Stage dung lai ngay du select dang focus: canvas hai ben 30 cho.
  assert.equal(collect(view.el,
    (e) => e.classList.contains('cd-tp-slot')).length, 30,
    'đổi sang Hai bên mà sơ đồ không dựng lại');
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
  // MIN-141 đợt 3: meta hồ sơ quay lại — 3 dòng trong card Tài sản
  // (không phải card riêng). Chỉ Nơi niêm yết / Người nhận ủy quyền /
  // Nội dung việc; NAIA-9 thêm Ngày lập hồ sơ để chọn ngày tra cứu.
  const metaBox = collect(view.el,
    (e) => e.classList.contains('cd-casemeta'))[0];
  assert.ok(metaBox, 'thiếu block .cd-casemeta dưới card Tài sản');
  for (const lbl of ['Loại văn bản', 'Ghi chú']) {
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
    'ghi_chu', 'ngay_lap_ho_so', 'nguoi_nhan_uy_quyen',
    'nguoi_nhan_uy_quyen_id', 'noi_dung_viec', 'noi_niem_yet']);
  assert.equal(meta.case_type, 'inheritance');
  assert.equal(meta.document_type, 'khai_nhan',
    'document_type phải = mặc định model');
  assert.equal(meta.ngay_lap_ho_so, null, 'ngay_lap_ho_so để backend tự điền');
  assert.equal(meta.noi_niem_yet, null);
  assert.equal(meta.ghi_chu, null);
  // MIN-141 đợt 3: ba truong meta moi cung di trong payload.case.
  assert.equal(meta.nguoi_nhan_uy_quyen, null);
  assert.equal(meta.nguoi_nhan_uy_quyen_id, null);
  assert.equal(meta.noi_dung_viec, null);
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
  assert.deepEqual(heads, ['', 'Họ tên', 'Giới tính', 'Ngày sinh',
    'Ngày mất', 'Số giấy tờ', 'Ngày cấp', 'Địa chỉ', '']);
  const cols = collect(t, (e) => e.tagName === 'COL').map((c) => c.className);
  assert.deepEqual(cols, ['cd-pcol-drag', 'cd-pcol-ho_ten',
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

// ---------- MIN-136: error catalog, dd/mm/yyyy, chrome ----------

test('MIN-136 error catalog: code → thông điệp thân thiện + rule ẩn', () => {
  const d = ERRORS.describeError({ code: 'workspace_owner_required',
    message: 'stage.owner_row_id phải là row_id ...' });
  assert.match(d.title, /Chưa chọn người để lại/);
  assert.match(d.hint, /ô khởi tạo/);
  assert.equal(d.code, 'workspace_owner_required');
  // errText: title chính + code mờ trong ngoặc — khong troi snake_case.
  const t = ERRORS.errText({ code: 'submit_failed' });
  assert.match(t, /Không gửi được lệnh tới engine/);
  assert.match(t, /\(submit_failed\)$/);
  // Code khong co trong catalog → fallback message backend, khong troi
  // code trang (title != code).
  const u = ERRORS.describeError({ code: 'totally_new_code_xyz',
    message: 'Backend said something odd' });
  assert.equal(u.title, 'Backend said something odd');
  // Toan bo ma backend/adapter da biet phai co title tieng Viet
  // (khong fallback ve code).
  const KNOWN = ['submit_failed', 'engine_unavailable', 'case_not_found',
    'workspace_locked', 'workspace_conflict', 'workspace_owner_required',
    'stage_validation_error', 'validation_error', 'diagram_invalid_state',
    'diagram_owner_mismatch', 'diagram_domain_mismatch',
    'diagram_reference_outside_stage', 'case_type_unsupported',
    'missing_land_owner', 'no_valid_heir', 'duplicate_person',
    'ancestry_cycle', 'spouse_conflict', 'self_parent', 'self_spouse',
    'dangling_parent', 'dangling_spouse', 'too_many_parents',
    'invalid_death_date', 'invalid_nodes', 'invalid_version',
    'intake_unsupported_source', 'intake_too_many_sources',
    'intake_text_too_long', 'intake_source_too_large',
    'word_no_documents_selected', 'word_unknown_document_key',
    'word_duplicate_document_key', 'file_not_found', 'file_locked',
    'unconfirmed', 'ocr', 'engine_shutdown', 'command_unknown',
    'engine_version_mismatch', 'invalid_boolean', 'invalid_domain',
    'invalid_node_id', 'invalid_parent', 'invalid_spouse',
    'invalid_position', 'missing_position', 'duplicate_node',
    'duplicate_parent', 'missing_node_id', 'word_batch_failed',
    'user_canceled', 'extraction_failed', 'unknown_website'];
  for (const c of KNOWN) {
    const dd = ERRORS.describeError({ code: c });
    assert.notEqual(dd.title, c, `ma ${c} thieu title than thien`);
    assert.ok(!/^[a-z_]+$/.test(dd.title) || dd.title === 'Lỗi không xác định',
      `ma ${c} title van la snake_case`);
  }
});

test('MIN-136 date: ISO ↔ dd/mm/yyyy; loai ngay khong ton tai', () => {
  const { fmtDisplayDate, parseDisplayDate } = VIEW._internals;
  assert.equal(fmtDisplayDate('1990-06-05'), '05/06/1990');
  assert.equal(fmtDisplayDate('1990'), '1990');          // year-only
  assert.equal(fmtDisplayDate(''), '');
  assert.equal(fmtDisplayDate(null), '');
  // Parse day-first: 05/06/1990 = 5 thang 6 — KHONG mo ho mm/dd.
  assert.deepEqual(parseDisplayDate('05/06/1990', true),
    { iso: '1990-06-05' });
  assert.deepEqual(parseDisplayDate('5/6/1990', true),
    { iso: '1990-06-05' });
  assert.deepEqual(parseDisplayDate('05.06.1990', true),
    { iso: '1990-06-05' });
  assert.deepEqual(parseDisplayDate('05-06-1990', true),
    { iso: '1990-06-05' });
  assert.deepEqual(parseDisplayDate('05061990', true),
    { iso: '1990-06-05' });
  assert.deepEqual(parseDisplayDate('1990', true), { iso: '1990' });
  assert.deepEqual(parseDisplayDate('', true), { iso: null });
  // Ngay khong ton tai / sai format.
  for (const bad of ['31/02/1990', '29/02/1990', '30/02/2024',
                     '06/31/1990', '1990/06/05', '05-06-90']) {
    assert.deepEqual(parseDisplayDate(bad, true), { error: 'invalid' },
      `${bad} phai bi tu choi`);
  }
  assert.deepEqual(parseDisplayDate('29/02/2000', true),
    { iso: '2000-02-29' });                              // nam nhuan hop le
  // Asset (allowYear=false): year-only bi tu choi.
  assert.deepEqual(parseDisplayDate('1990', false), { error: 'invalid' });
});

test('MIN-136: ô ngày Stage hiển dd/mm/yyyy, nhập dd/mm → wire ISO', () => {
  const { model, view } = build(test);
  const p = model.addPerson({ ho_ten: 'A' });
  const rid = p.row_id;
  const inp = fid(view.el, `p:${rid}:ngay_sinh`);
  assert.ok(inp, 'thiếu ô ngày sinh');
  assert.notEqual(inp.getAttribute('type'), 'date',
    'ô ngày không được dùng type=date (format theo locale OS)');
  // Nhap dd/mm/yyyy → onchange chuyen ISO vao model.
  inp.value = '05/06/1990';
  inp.onchange();
  assert.equal(model.state.stage.people[0].ngay_sinh, '1990-06-05');
  assert.equal(inp.value, '05/06/1990',
    'hien thi lai phai la dd/mm/yyyy');
  // ISO co san → hien dd/mm/yyyy.
  model.state.stage.people[0].ngay_chet = '2020-05-10';
  model.dismissNotice();
  const chet = fid(view.el, `p:${rid}:ngay_chet`);
  assert.equal(chet.value, '10/05/2020');
  // Nhap sai → danh do inline, giu text cho user sua.
  chet.value = '31/02/2020';
  chet.onchange();
  assert.ok(chet.classList.contains('cd-input-bad'));
  assert.equal(chet.value, '31/02/2020');
  assert.equal(model.state.stage.people[0].ngay_chet, '2020-05-10',
    'ngay sai khong duoc ghi vao model');
  // Go lai DUNG chuoi dang hien: 'change' khong ban (value khong doi)
  // nhung 'blur' van chuan hoa — raw khong duoc con lai trong model.
  model.state.stage.people[0].ngay_chet = '2020-05-10';
  model.dismissNotice();
  const chet2 = fid(view.el, `p:${rid}:ngay_chet`);
  chet2.value = '10/05/2020';
  chet2.oninput();
  assert.equal(model.state.stage.people[0].ngay_chet, '10/05/2020',
    'oninput ghi raw vao model (dirty live)');
  chet2.onblur();
  assert.equal(model.state.stage.people[0].ngay_chet, '2020-05-10',
    'blur chuan hoa raw → ISO ke ca khi change khong ban');
});

test('MIN-136: empty-state Soạn hồ sơ có nút + Hồ sơ mới', async () => {
  const { model, view } = build(test);
  model.state.status = 'idle';
  model.dismissNotice();
  const btnNew = findBtns(view.el, '+ Hồ sơ mới')[0];
  assert.ok(btnNew, 'thiếu nút + Hồ sơ mới ở empty-state');
  await btnNew.onclick();
  assert.equal(model.state.caseId, null);
  assert.equal(model.state.status, 'ready');
  // Sau tao moi → workspace drafting hien (khong con idle).
  assert.ok(collect(view.el, (e) =>
    e.classList.contains('cd-workspace')).length >= 1);
});

test('MIN-136: Nhập file mở được trên nháp mới (capabilities đủ 5 loại)', () => {
  const { view } = build(test);
  const intake = findBtns(view.el, 'Nhập file')[0];
  assert.ok(intake, 'thiếu nút Nhập file');
  assert.equal(intake.disabled, false,
    'Nhập file bi disable trên nháp mới — capabilities.intake rỗng');
});

test('MIN-136: nhãn tài sản viết tắt Hình thức SD', () => {
  const { model, view } = build(test);
  model.addAsset();
  const t = collect(view.el, (e) => e.classList.contains('cd-tbl'))[0];
  assert.match(t.textContent, /Hình thức SD/);
  assert.ok(!/Hình thức sử dụng/.test(t.textContent));
});

test('MIN-136 F-1: conflict hiện NGAY khi đang gõ trong Stage', () => {
  const { model, view } = build(test, { draft: false });
  const rid = model.state.stage.people[0].row_id;
  const inp = fid(view.el, `p:${rid}:ho_ten`);
  inp.focus();
  // Server tu choi commit → status conflict trong luc input con focus.
  model.state.status = 'conflict';
  model.state.conflict = { server_revision: 9, client_revision: 3 };
  model.dismissNotice();                  // emit nen → defer rebuild
  const modal = collect(view.el, (e) => e.classList.contains('modal'))[0];
  assert.ok(modal, 'dialog conflict bi emit-defer nuot khi dang go');
  assert.match(modal.textContent, /đã thay đổi trên máy chủ/);
});

test('MIN-136: case_list retry khi infra error + message thân thiện', async (t) => {
  // Lan dau submit_failed (sidecar chua ready) → tu retry sau 1.5s
  // va hien message catalog, khong troi ma loi.
  let n = 0;
  const respond = (cmd) => {
    if (cmd === 'notary.case_list') {
      n += 1;
      if (n === 1) {
        return { ok: false, error: { code: 'submit_failed',
          message: 'engine chua san sang' } };
      }
      return { ok: true, data: { cases: [], total: 0 } };
    }
    return null;
  };
  const { view, calls } = build(t, { respond });
  await new Promise((r) => setTimeout(r, 40));
  const faceBox = collect(view.el, (e) =>
    e.classList.contains('face-error'))[0];
  assert.ok(faceBox, 'lỗi infra không hiện face lỗi');
  assert.match(faceBox.textContent, /Không gửi được lệnh tới engine/);
  assert.ok(!/submit_failed/.test(faceBox.textContent.split('(')[0] || ''),
    'mã submit_failed trồi lên làm nội dung chính');
  // Sau ~1.5s retry tu dong → case_list lan 2 thanh cong.
  await new Promise((r) => setTimeout(r, 1700));
  const listCalls = calls.filter(([c]) => c === 'notary.case_list');
  assert.ok(listCalls.length >= 2, 'khong tu retry case_list');
  assert.ok(collect(view.el, (e) =>
    e.classList.contains('face-error')).length === 0,
    'face loi con sau khi retry thanh cong');
});

// ---------- MIN-141 đợt 3: block meta hồ sơ dưới card Tài sản ----------

test('đợt3: ba dòng meta nằm trong card Tài sản, nhập → updateCaseMeta', () => {
  const { model, view } = build(test, { draft: true });
  const assets = collect(view.el,
    (e) => e.classList.contains('cd-assets'))[0];
  const meta = collect(assets,
    (e) => e.classList.contains('cd-casemeta'))[0];
  assert.ok(meta, 'meta block phai nam TRONG card Tai san');
  const labels = collect(meta,
    (e) => e.classList.contains('cd-casemeta-label'))
    .map((e) => e.textContent);
  assert.deepEqual(labels,
    ['Nơi niêm yết', 'Ngày lập hồ sơ', 'Người nhận ủy quyền', 'Nội dung việc']);
  // Nhap noi niem yet → caseInfo + metaDirty.
  const ny = fid(view.el, 'meta:noi_niem_yet');
  ny.value = 'xã Yên Sở';
  ny.oninput();
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Yên Sở');
  assert.equal(model.state.metaDirty, true);
  // Rong → null (khong phai chuoi trong).
  ny.value = '   ';
  ny.oninput();
  assert.equal(model.state.caseInfo.noi_niem_yet, null);
  // Nguoi nhan UQ co datalist danh ba + nut + Danh ba.
  const uq = fid(view.el, 'meta:nguoi_nhan_uy_quyen');
  assert.ok(uq.getAttribute('list'), 'input UQ thieu datalist');
  assert.ok(fid(view.el, 'meta:uq_add_catalog'), 'thieu nut + Danh bạ');
});

test('đợt3: meta-only dirty bat nut Cập nhật; Hủy khoi phuc baseline', async () => {
  const { model, view } = build(test, { draft: false });
  const upd = () => findBtns(topbar(view.el), 'Cập nhật')[0];
  const dots = (b) => collect(b, (e) => e.classList.contains('dirty-dot'));
  assert.equal(dots(upd()).length, 0);
  // Chi sua meta → nut Cap nhat bat (dirty dot).
  model.updateCaseMeta('noi_niem_yet', 'xã Khác');
  model.updateCaseMeta('nguoi_nhan_uy_quyen', 'Người Khác');
  model.dismissNotice();
  assert.equal(model.state.metaDirty, true);
  assert.equal(dots(upd()).length, 1,
    'sua meta phai bat dirty tren nut Cap nhat');
  // Huy → meta ve baseline committedCaseInfo (khong goi command ghi).
  const undo = findBtns(view.el, 'Hủy thay đổi')[0];
  await undo.onclick();
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Cũ',
    'Huy phai khoi phuc noi_niem_yet baseline');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen,
    'Người Nhận Gốc');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen_id, 7);
  assert.equal(model.state.metaDirty, false);
});

test('đợt3: Cập nhật gui payload.case kem stage khi meta dirty', async () => {
  const { model, view, calls } = build(test, { draft: false });
  model.updateCaseMeta('noi_dung_viec', 'Khai nhận nhà đất');
  model.updateCaseMeta('nguoi_nhan_uy_quyen', 'Người UQ Mới');
  calls.length = 0;
  await findBtns(topbar(view.el), 'Cập nhật')[0].onclick();
  const call = calls.find(
    ([c]) => c === 'notary.workspace_commit_stage');
  assert.ok(call, 'Cập nhật khong goi workspace_commit_stage');
  assert.ok(call[1].case, 'meta dirty ma payload thieu case');
  assert.equal(call[1].case.noi_dung_viec, 'Khai nhận nhà đất');
  assert.equal(call[1].case.nguoi_nhan_uy_quyen, 'Người UQ Mới');
  // Baseline 2024-05-01/xã Cũ van day du trong block meta gui di.
  assert.equal(call[1].case.noi_niem_yet, 'xã Cũ');
});

test('đợt3: case locked → 3 ô meta disabled, khong goi customer_list', async () => {
  const { model, view, calls } = build(test, { draft: false });
  model.state.locked = true;
  model.state.status = 'locked';
  model.state.uqCatalog = null;      // reset de test trigger lai
  await new Promise((r) => setTimeout(r, 5));   // flush load cu (neu co)
  calls.length = 0;
  model.dismissNotice();
  for (const f of ['meta:noi_niem_yet', 'meta:nguoi_nhan_uy_quyen',
                   'meta:noi_dung_viec']) {
    const inp = fid(view.el, f);
    assert.ok(inp && inp.disabled, `${f} phai disabled khi locked`);
  }
  await new Promise((r) => setTimeout(r, 5));
  assert.equal(calls.filter(([c]) => c === 'notary.customer_list')
    .length, 0, 'locked ma van goi customer_list');
});


// ---------- NAIA-8: Word export dialog — folder templates ----------

// openModal stub theo shape view: build(box, close), box append vao body.
function modalCapture(document) {
  let lastBox = null;
  const openModal = (build) => {
    const box = document.createElement('div');
    box.className = 'modal';
    document.body.append(box);
    lastBox = box;
    build(box, () => box.remove());
  };
  return { openModal, get box() { return lastBox; } };
}

function wordDialogCtx(t, { model, pickFiles, notify }) {
  const { document } = makeDom();
  global.document = document;
  global.window = {};
  t.after(() => { delete global.document; delete global.window; });
  const h = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  };
  const btn = (label, cls, onClick) => {
    const b = h('button', (cls || '').trim(), label);
    b.type = 'button';
    if (onClick) b.onclick = onClick;
    return b;
  };
  const face = (f) => {
    const e = h('div', `face face-${f.kind}`, f.title);
    if (f.detail) e.append(h('span', 'muted', f.detail));
    return e;
  };
  const cap = modalCapture(document);
  const notes = [];
  const ctx = {
    model, lib: L,
    notify: notify || ((msg, isErr) => notes.push({ msg, isErr })),
    h, btn, face,
    openModal: cap.openModal, pickFiles,
    openPath: async () => ({ ok: true }),
    cancelJob: async () => ({ ok: true }),
  };
  return { ctx, document, cap, notes };
}

function wordModelStub(overrides = {}) {
  const calls = [];
  const state = {
    wordOptions: null, wordResult: null, wordBusy: false,
    caseInfo: { id: 42, noi_niem_yet: 'xã Yên Sở', locked: false },
    committedCaseInfo: { id: 42, noi_niem_yet: 'xã Yên Sở', locked: false },
  };
  return {
    calls, state,
    canWrite: () => true,
    saveCaseMeta: async (patch) => {
      calls.push(['update', patch]);
      state.caseInfo.noi_niem_yet = patch.noi_niem_yet;
      state.committedCaseInfo.noi_niem_yet = patch.noi_niem_yet;
      return { ok: true };
    },
    loadWordOptions: async (templateDir) => {
      calls.push(['options', templateDir]);
      state.wordOptions = [
        { document_key: 'Mau thue nha.docx', display_name: 'Mau thue nha',
          ready: true, block_reason: null },
        { document_key: 'To cam ket.docx', display_name: 'To cam ket',
          ready: true, block_reason: null },
        { document_key: 'Huy.docx', display_name: 'Huy',
          ready: false, block_reason: 'word.template_missing' },
      ];
      return { ok: true };
    },
    exportWord: async (keys, dest, opts) => {
      calls.push(['batch', { keys, dest, opts }]);
      state.wordResult = {
        schema_version: 'v1', destination: { path: 'D:/out' },
        documents: keys.map((k) => ({
          document_key: k, display_name: k, status: 'saved',
          actual_filename: `${k}_HS-42.docx`,
          output_file: { path: `D:/out/${k}_HS-42.docx` },
          error: null })),
        breakdown: { succeeded: keys, failed: [], skipped: [] },
      };
      return { ok: true };
    },
    ...overrides,
  };
}

test('NAIA-8 word dialog: chon folder → list → select all/none → export', async (t) => {
  const model = wordModelStub();
  const picks = [];
  // Hai token KHAC NHAU cho thu muc mau/dich — test bat duoc loi noi
  // nham day (wiring) gui template token lam destination (review B4).
  const pickFiles = async (opts) => {
    picks.push(opts);
    const tok = picks.length === 1 ? 'tok-tpl' : 'tok-dest';
    const nm = picks.length === 1 ? 'templates' : 'output';
    return { ok: true, data: { files: [
      { file_token: tok, name: nm, is_dir: true }] } };
  };
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  const dlg = WORD.createWordDialog(ctx);
  dlg.open();
  const box = cap.box;
  assert.ok(box, 'dialog khong mo');

  // Chon thu muc mau → pickFiles({directory:true}) → options co 3 file.
  const pickTpl = findBtns(box, 'Chọn thư mục mẫu')[0];
  assert.ok(pickTpl, 'thieu nut chon thu muc mau');
  await pickTpl.onclick();
  assert.equal(picks.length, 1);
  assert.equal(picks[0].directory, true);
  assert.deepEqual(model.calls[0], ['options', { file_token: 'tok-tpl' }]);

  const isDocCb = (e) => e.tagName === 'INPUT' && e.type === 'checkbox' &&
    !(e.getAttribute('aria-label') || '').includes('thư mục con');
  const checkboxes = collect(box, isDocCb);
  // 2 file ready + 1 blocked (disabled, khong check).
  assert.equal(checkboxes.length, 3);
  assert.equal(checkboxes[0].checked, true);
  assert.equal(checkboxes[1].checked, true);
  assert.equal(checkboxes[2].disabled, true);
  assert.equal(checkboxes[2].checked, false);
  assert.match(box.textContent, /Văn bản không còn mẫu/);

  // Bo chon → tat ca off; Chon tat ca → chi file ready on.
  await findBtns(box, 'Bỏ chọn')[0].onclick();
  assert.ok(checkboxes.every((c) => !c.checked));
  await findBtns(box, 'Chọn tất cả')[0].onclick();
  assert.equal(checkboxes[0].checked, true);
  assert.equal(checkboxes[2].checked, false,
    'file blocked khong duoc tick boi Chon tat ca');

  // Chon dich + subdir → Xuat: keys dung, payload co templateDir+subdir.
  await findBtns(box, 'Chọn thư mục đích')[0].onclick();
  const subdir = collect(box, (e) => e.tagName === 'INPUT' &&
    e.type === 'checkbox' && e.getAttribute('aria-label') &&
    e.getAttribute('aria-label').includes('thư mục con'))[0];
  assert.ok(subdir, 'thieu checkbox tao thu muc con');
  subdir.checked = true;
  await findBtns(box, 'Xuất')[0].onclick();
  const [, batch] = model.calls.find(([k]) => k === 'batch');
  assert.deepEqual(batch.keys, ['Mau thue nha.docx', 'To cam ket.docx']);
  assert.deepEqual(batch.dest, { file_token: 'tok-dest' });
  assert.deepEqual(batch.opts.templateDir, { file_token: 'tok-tpl' });
  assert.equal(batch.opts.createCaseSubdir, true);
  // Ket qua per-doc hien thi: 2 saved + mo file.
  assert.match(box.textContent, /Thành công 2/);
  assert.ok(findBtns(box, 'Mở file').length >= 2);
});

test('NAIA-8 word dialog: doi folder mau → selection cu bi xoa', async (t) => {
  const model = wordModelStub();
  const pickFiles = async () => ({ ok: true, data: { files: [
    { file_token: 'tok-2', name: 'other', is_dir: true }] } });
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await findBtns(box, 'Bỏ chọn')[0].onclick();
  // Doi folder → loadWordOptions lan 2 → checkbox rebuilt, ready-mac-dinh on.
  await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  const cbs = collect(box, (e) => e.tagName === 'INPUT' &&
    e.type === 'checkbox' &&
    !(e.getAttribute('aria-label') || '').includes('thư mục con'));
  assert.equal(cbs[0].checked, true);
  assert.equal(model.calls.filter(([k]) => k === 'options').length, 2);
});

test('NAIA-8 word dialog: huy picker giu im; xuat thieu chon bao loi', async (t) => {
  const model = wordModelStub();
  let n = 0;
  const pickFiles = async () => {
    n += 1;
    if (n === 1) return { ok: true, data: { files: [] } };  // cancel
    return { ok: true, data: { files: [
      { file_token: 'tok-3', name: 'd', is_dir: true }] } };
  };
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  // Cancel picker mau → khong goi options, list giu placeholder.
  await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  assert.equal(model.calls.length, 0);
  assert.match(box.textContent, /Chọn thư mục chứa file mẫu/);
  // Xuat khi chua chon gi → khong goi batch.
  await findBtns(box, 'Xuất')[0].onclick();
  assert.equal(model.calls.filter(([k]) => k === 'batch').length, 0);
});

// Flush mot macrotask — onclick async (await pickFiles → loadWordOptions)
// can vai tick truoc khi DOM/state hieu ung hien ra.
const tick = () => new Promise((r) => setImmediate(r));

test('NAIA-8 word dialog: dang quet → list rong ngay + Xuat/Chon khoa', async (t) => {
  // Scan treo: selection phai mat NGAY + nut bi khoa, khong cho xuat
  // voi danh sach cua folder cu (review B1/B3).
  let resolveScan;
  const model = wordModelStub({ loadWordOptions: (td) => {
    model.calls.push(['options', td]);
    return new Promise((res) => { resolveScan = res; });
  } });
  const pickFiles = async () => ({ ok: true, data: { files: [
    { file_token: 'tok-a', name: 'mau', is_dir: true }] } });
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  const scan1 = findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await tick();
  await tick();
  // Dang quet: khong con checkbox nao, Xuat/Chon tat ca/Bo chon disabled.
  const goBtn = findBtns(box, 'Xuất')[0];
  const allBtn = findBtns(box, 'Chọn tất cả')[0];
  const noneBtn = findBtns(box, 'Bỏ chọn')[0];
  assert.equal(goBtn.disabled, true);
  assert.equal(allBtn.disabled, true);
  assert.equal(noneBtn.disabled, true);
  const cbs = collect(box, (e) => e.tagName === 'INPUT' &&
    e.type === 'checkbox' &&
    !(e.getAttribute('aria-label') || '').includes('thư mục con'));
  assert.equal(cbs.length, 0, 'selection cu phai bi xoa ngay khi quet');
  assert.match(box.textContent, /Đang quét thư mục mẫu/);
  // Scan xong → mo khoa + list moi hien.
  model.state.wordOptions = [
    { document_key: 'new.docx', display_name: 'new',
      ready: true, block_reason: null }];
  resolveScan({ ok: true });
  await scan1;
  assert.equal(goBtn.disabled, false);
  assert.equal(allBtn.disabled, false);
  assert.equal(noneBtn.disabled, false);
});

test('NAIA-8 word dialog: folder trung basename — token phan biet, response cu khong de list moi', async (t) => {
  // Hai folder cung ten "mau", token khac nhau. Scan A treo; doi sang B
  // (cung basename) → B ve truoc hien list B; A ve sau (stale) KHONG duoc
  // de lai list — neu khong co scan guard thi UI chi thay "mau" nhu nhau.
  const dA = {};
  const dB = {};
  dA.p = new Promise((res) => { dA.res = res; });
  dB.p = new Promise((res) => { dB.res = res; });
  const scans = [];
  const model = wordModelStub({ loadWordOptions: (td) => {
    model.calls.push(['options', td]);
    return td.file_token === 'tok-A' ? dA.p : dB.p;
  } });
  let n = 0;
  const pickFiles = async () => {
    n += 1;
    return { ok: true, data: { files: [
      { file_token: n === 1 ? 'tok-A' : 'tok-B',
        name: 'mau', is_dir: true }] } };   // TRUNG basename
  };
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  const sA = findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await tick();
  const sB = findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await tick();
  scans.push(...model.calls.filter(([k]) => k === 'options'));
  assert.equal(scans.length, 2);
  assert.equal(scans[0][1].file_token, 'tok-A');
  assert.equal(scans[1][1].file_token, 'tok-B');
  // B ve truoc → list B.
  model.state.wordOptions = [
    { document_key: 'B.docx', display_name: 'B',
      ready: true, block_reason: null }];
  dB.res({ ok: true });
  await sB;
  // A tre ve sau (stale — model da danh dau) → list giu nguyen B.
  dA.res({ ok: true, stale: true });
  await sA;
  const cbs = collect(box, (e) => e.tagName === 'INPUT' &&
    e.type === 'checkbox' &&
    !(e.getAttribute('aria-label') || '').includes('thư mục con'));
  assert.equal(cbs.length, 1);
  assert.equal(cbs[0].getAttribute('aria-label'), 'B');
  assert.match(box.textContent, /Thư mục mẫu: mau/);
});

for (const initialDraft of [true, false]) {
  test(`Word posting ${initialDraft ? 'initial draft' : 'dialog edit'} must be saved before export`, async (t) => {
    const model = wordModelStub();
    if (initialDraft) model.state.caseInfo.noi_niem_yet = 'xã Chưa Lưu';
    const pickFiles = async () => ({ ok: true, data: { files: [
      { file_token: 'tok-folder', name: 'folder', is_dir: true }] } });
    const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
    WORD.createWordDialog(ctx).open();
    const box = cap.box;
    await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
    await findBtns(box, 'Chọn thư mục đích')[0].onclick();
    const input = collect(box, (e) => e.tagName === 'INPUT' &&
      e.getAttribute('aria-label') === 'Nơi niêm yết')[0];
    assert.equal(input.value, initialDraft ? 'xã Chưa Lưu' : 'xã Yên Sở');
    if (!initialDraft) {
      input.value = 'xã Chưa Lưu';
      input.oninput();
    }
    assert.match(box.textContent, /Hãy bấm “Lưu nơi niêm yết” trước khi xuất/);
    await findBtns(box, 'Xuất')[0].onclick();
    assert.equal(model.calls.filter(([k]) => k === 'batch').length, 0);
    assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Yên Sở');
    await findBtns(box, 'Lưu nơi niêm yết')[0].onclick();
    assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Chưa Lưu');
    await findBtns(box, 'Xuất')[0].onclick();
    assert.equal(model.calls.filter(([k]) => k === 'batch').length, 1);
  });
}

test('NAIA-8 word dialog: Noi niem yet — nap gia tri da luu, luu ok/loi ro', async (t) => {
  const model = wordModelStub();
  const pickFiles = async () => ({ ok: true, data: { files: [] } });
  const { ctx, cap, notes } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  const input = collect(box, (e) => e.tagName === 'INPUT' &&
    e.type === 'text' &&
    e.getAttribute('aria-label') === 'Nơi niêm yết')[0];
  assert.ok(input, 'thieu input Noi niem yet');
  // Gia tri hien tai cua ho so nap san (workspace_get).
  assert.equal(input.value, 'xã Yên Sở');
  input.value = 'phường Mới  ';
  await findBtns(box, 'Lưu nơi niêm yết')[0].onclick();
  const upd = model.calls.find(([k]) => k === 'update');
  assert.deepEqual(upd[1], { noi_niem_yet: 'phường Mới' });
  assert.match(box.textContent, /Đã lưu\./);

  // Loi luu → thong bao ro rang tai cho + notify loi.
  model.saveCaseMeta = async () => ({ ok: false, error: {
    code: 'workspace_conflict', message: 'revision khac server',
    retryable: false } });
  input.value = 'xã Khác';
  await findBtns(box, 'Lưu nơi niêm yết')[0].onclick();
  assert.match(box.textContent, /Lưu thất bại: revision khac server/);
  assert.ok(notes.some((m) => m.isErr &&
    /workspace_conflict/.test(m.msg)));

  // Case locked → input + nut luu bi khoa.
  model.state.caseInfo.locked = true;
  model.canWrite = () => false;
  WORD.createWordDialog(ctx).open();
  const box2 = cap.box;
  const input2 = collect(box2, (e) => e.tagName === 'INPUT' &&
    e.getAttribute('aria-label') === 'Nơi niêm yết')[0];
  assert.equal(input2.disabled, true);
  assert.equal(findBtns(box2, 'Lưu nơi niêm yết')[0].disabled, true);
});

test('NAIA-8 word dialog: dang luu Noi niem yet → Xuat/input/Luu khoa (pending-save)', async (t) => {
  // Review NAIA-8 (cao): bam Luu roi Xuat khi save con pending → batch
  // chay voi gia tri cu. Phai khoa Xuat + input + Luu lap den khi save
  // xong; mo lai theo quyen hien tai ca success lan error.
  let finishSave;
  const model = wordModelStub({
    saveCaseMeta: (patch) => {
      model.calls.push(['update', patch]);
      return new Promise((res) => {
        finishSave = () => {
          model.state.caseInfo.noi_niem_yet = patch.noi_niem_yet;
          model.state.committedCaseInfo.noi_niem_yet = patch.noi_niem_yet;
          res({ ok: true });
        };
      });
    },
  });
  const pickFiles = async () => ({ ok: true, data: { files: [
    { file_token: 'tok-m', name: 'mau', is_dir: true }] } });
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await findBtns(box, 'Chọn thư mục đích')[0].onclick();
  const goBtn = findBtns(box, 'Xuất')[0];
  const input = collect(box, (e) => e.tagName === 'INPUT' &&
    e.getAttribute('aria-label') === 'Nơi niêm yết')[0];
  const saveBtn = findBtns(box, 'Lưu nơi niêm yết')[0];
  assert.equal(goBtn.disabled, false);
  input.value = 'phường Mới';
  const save = saveBtn.onclick();
  await tick();
  // Pending-save: Xuat + input + Luu lap deu khoa; goi onclick truc tiep
  // (stub bo qua disabled) cung khong dispatch batch nho guard trong go.
  assert.equal(goBtn.disabled, true, 'Xuat phai khoa khi meta dang luu');
  assert.equal(input.disabled, true, 'input phai khoa khi meta dang luu');
  assert.equal(saveBtn.disabled, true, 'Luu lap phai khoa khi dang luu');
  await goBtn.onclick();
  assert.equal(model.calls.filter(([k]) => k === 'batch').length, 0,
    'khong duoc dispatch batch khi meta save con pending');
  // Save xong → mo lai dung quyen; Xuat gio moi duoc phep.
  finishSave();
  await save;
  assert.equal(goBtn.disabled, false);
  assert.equal(input.disabled, false);
  assert.equal(saveBtn.disabled, false);
  assert.match(box.textContent, /Đã lưu\./);
  await goBtn.onclick();
  assert.ok(model.calls.some(([k]) => k === 'batch'),
    'batch phai chay sau khi save hoan tat');
});

test('NAIA-8 word dialog: pending-save loi → mo lai theo quyen hien tai', async (t) => {
  // Loi thuong (validation) → mo lai input/Luu/Xuat vi canWrite giu
  // nguyen; loi lam case locked (canWrite → false) → giu khoa.
  for (const locked of [false, true]) {
    let finishSave;
    const model = wordModelStub({
      saveCaseMeta: () => new Promise((res) => {
        finishSave = () => {
          if (locked) model.canWrite = () => false;
          res({ ok: false, error: {
            code: locked ? 'workspace_locked' : 'validation_error',
            message: 'loi luu', retryable: false } });
        };
      }),
    });
    const pickFiles = async () => ({ ok: true, data: { files: [
      { file_token: 'tok-m', name: 'mau', is_dir: true }] } });
    const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
    WORD.createWordDialog(ctx).open();
    const box = cap.box;
    await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
    const goBtn = findBtns(box, 'Xuất')[0];
    const input = collect(box, (e) => e.tagName === 'INPUT' &&
      e.getAttribute('aria-label') === 'Nơi niêm yết')[0];
    const saveBtn = findBtns(box, 'Lưu nơi niêm yết')[0];
    const save = saveBtn.onclick();
    await tick();
    finishSave();
    await save;
    assert.equal(input.disabled, locked,
      `locked=${locked}: input.disabled`);
    assert.equal(saveBtn.disabled, locked,
      `locked=${locked}: save.disabled`);
    assert.equal(goBtn.disabled, locked,
      `locked=${locked}: Xuat.disabled`);
    assert.match(box.textContent, /Lưu thất bại/);
  }
});

test('NAIA-8 word dialog: Huy xuat an/hien theo batch + scope cd-word-modal', async (t) => {
  // Review NAIA-8 (nhe): `button{display:inline-flex}` thang [hidden] →
  // Huy xuat van hien sau khi xong. Dialog phai mang .cd-word-modal de
  // rule `.cd-word-modal [hidden]` ap dung — test state transition tren
  // DOM + class scope; visibility computed that kiem qua E2E Electron.
  let finishExport;
  const model = wordModelStub({ exportWord: (keys, dest, opts) => {
    model.calls.push(['batch', { keys, dest, opts }]);
    return new Promise((res) => {
      finishExport = () => {
        model.state.wordResult = {
          destination: { path: 'D:/out' }, documents: [],
          breakdown: { succeeded: [], failed: [], skipped: [] } };
        res({ ok: true });
      };
    });
  } });
  const pickFiles = async () => ({ ok: true, data: { files: [
    { file_token: 'tok-w', name: 'mau', is_dir: true }] } });
  const { ctx, cap } = wordDialogCtx(t, { model, pickFiles });
  WORD.createWordDialog(ctx).open();
  const box = cap.box;
  assert.ok(box.classList.contains('cd-word-modal'),
    'dialog phai mang scope cd-word-modal cho rule an [hidden]');
  const cancel = findBtns(box, 'Hủy xuất')[0];
  assert.equal(cancel.hidden, true, 'cancel an truoc khi xuat');
  await findBtns(box, 'Chọn thư mục mẫu')[0].onclick();
  await findBtns(box, 'Chọn thư mục đích')[0].onclick();
  const exp = findBtns(box, 'Xuất')[0].onclick();
  await tick();
  assert.equal(cancel.hidden, false, 'cancel hien khi dang xuat');
  finishExport();
  await exp;
  assert.equal(cancel.hidden, true, 'cancel an lai sau khi batch xong');

});

// ---------- TASK-3: renderer ngu dong (khong tu tra) ----------

test('TASK-3: render/go/refresh khong goi lookup, khong sua du lieu', async () => {
  const answer = { ok: true, data: {
    schema_version: 'notary.address-lookup.v2', status: 'found',
    presentation: 'drafting', total: 1,
    results: [{
      unit_id: 'B', level: 'commune', name: 'Xã B',
      province: { unit_id: 'P', name: 'Tỉnh P' },
      source_text: 'Xã B', display: 'xã B, tỉnh P',
      observation_id: 'obs-b', evidence: [] }],
    dataset_version: 'v2', revision: 1 }};
  const { model, view, calls } = build(test, {
    respond: (cmd) => cmd === 'notary.address_lookup' ? answer : null });
  model.updateCaseMeta('ngay_lap_ho_so', '2026-10-04');
  const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P',
                              ngay_cap: '2020-01-01' });
  const before = model.state.stage.people[0].dia_chi;
  await new Promise(r => setTimeout(r, 450));
  const box = collect(view.el,
    (e) => e.id === `address-person-${p.row_id}`)[0];
  assert.ok(box, 'thiếu ô tra cứu địa chỉ person');
  assert.equal(box.textContent, '');
  assert.ok(!calls.some(([c]) => c === 'notary.address_lookup'),
    'render khong duoc goi notary.address_lookup');
  assert.ok(!fid(view.el, `address-apply:person:${p.row_id}:B`),
    'ngu dong khong co nut ap dung');
  assert.equal(model.state.stage.people[0].dia_chi, before);
});

test('NAIA-9: issuer input + suggestion box chỉ hiện khi ngay_chet có', async () => {
  const { model, view } = build(test);
  const alive = model.addPerson({ ho_ten: 'Sống' });
  const dead = model.addPerson({ ho_ten: 'Chết', ngay_chet: '2020-01-01' });
  assert.ok(!collect(view.el,
    (e) => e.id === `address-issuer-${alive.row_id}`).length,
    'người còn sống không được có ô nơi cấp khai tử');
  assert.ok(collect(view.el,
    (e) => e.id === `address-issuer-${dead.row_id}`).length,
    'người chết phải có ô gợi ý nơi cấp khai tử');
  assert.ok(fid(view.el, `p:${dead.row_id}:noi_cap`),
    'thiếu input nhập địa chỉ UBND trên giấy khai tử');
});

test('existing issuer input labels distinguish living identity papers from death certificates and remain editable', () => {
  const {model, view} = build(test);
  const alive = model.addPerson({ho_ten:'Người Mẫu', noi_cap:'Bộ Coongan'});
  const dead = model.addPerson({ho_ten:'Người Mẫu Đã Mất', ngay_chet:'2020-01-01', noi_cap:'UBND Mẫu'});
  const liveInput = fid(view.el, `p:${alive.row_id}:noi_cap`);
  const deadInput = fid(view.el, `p:${dead.row_id}:noi_cap`);
  assert.equal(liveInput.placeholder, 'Cơ quan cấp giấy tờ');
  assert.equal(liveInput.getAttribute('aria-label'), 'Nơi cấp giấy tờ — Người Mẫu');
  assert.equal(deadInput.placeholder, 'UBND trên giấy khai tử');
  assert.equal(deadInput.getAttribute('aria-label'), 'Nơi cấp giấy khai tử — Người Mẫu Đã Mất');
  liveInput.value = 'Cơ quan sửa tay'; liveInput.oninput();
  deadInput.value = 'UBND sửa tay'; deadInput.oninput();
  assert.equal(model.state.stage.people.find(p=>p.row_id===alive.row_id).noi_cap, 'Cơ quan sửa tay');
  assert.equal(model.state.stage.people.find(p=>p.row_id===dead.row_id).noi_cap, 'UBND sửa tay');
});

// ---------- TASK-4: nut Tra thu cong + overlay full ----------

const ltick = (ms = 30) => new Promise(r => setTimeout(r, ms));

function lookupResponders(mode) {
  const mk = (status, presentation, total, results) => ({ ok: true, data: {
    schema_version: 'notary.address-lookup.v2', status, presentation,
    total, results, dataset_version: 'v2', revision: 1 } });
  const fullRows = [
    { unit_id: 'U1', level: 'commune', name: 'Xã A',
      province: { unit_id: 'P', name: 'Tỉnh P' },
      source_text: 'Xã A (nguồn một)', display: 'Xã A = Xã A (nguồn một), Tỉnh P',
      observation_id: 'obs-1', evidence: [] },
    { unit_id: 'U1', level: 'commune', name: 'Xã A',
      province: { unit_id: 'P', name: 'Tỉnh P' },
      source_text: 'Xã A (nguồn hai)', display: 'Xã A = Xã A (nguồn hai), Tỉnh P',
      observation_id: 'obs-2', evidence: [] },
  ];
  return (cmd, payload) => {
    if (cmd !== 'notary.address_lookup') return null;
    if (payload.presentation === 'full') {
      return mk('found', 'full', fullRows.length, fullRows);
    }
    if (mode === 'too_many') return mk('too_many', 'drafting', 12, []);
    if (mode === 'not_found') return mk('not_found', 'drafting', 0, []);
    return mk('found', 'drafting', 2, fullRows.map((r) => ({
      ...r, display: 'xã A, tỉnh P' })));
  };
}

function panelOf(el, root) {
  let n = el;
  while (n && n.parentElement && n.parentElement !== root) n = n.parentElement;
  return n;
}

test('TASK-4: moi o co nut Tra; go/dan/blur khong gui lenh', async () => {
  const { model, view, calls } = build(test,
    { respond: lookupResponders('found') });
  const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P',
    ngay_chet: '2020-01-01', noi_cap: 'UBND Xã A' });
  const a = model.addAsset({ dia_chi: 'Xã A, Tỉnh P' });
  model.updateCaseMeta('noi_niem_yet', 'Xã A, Tỉnh P');
  await ltick(400);
  assert.ok(fid(view.el, `lookup-tra:person:${p.row_id}`), 'thiếu Tra person');
  assert.ok(fid(view.el, `lookup-tra:asset:${a.row_id}`), 'thiếu Tra asset');
  assert.ok(fid(view.el, `lookup-tra:issuer:${p.row_id}`), 'thiếu Tra issuer');
  assert.ok(fid(view.el, 'lookup-tra:posting:posting'), 'thiếu Tra posting');
  assert.ok(!calls.some(([c]) => c === 'notary.address_lookup'),
    'render/go khong duoc tu gui lookup');
  // Go them vao o dia chi cung khong gui.
  const inp = fid(view.el, `p:${p.row_id}:dia_chi`);
  inp.value = 'Xã A sửa, Tỉnh P';
  inp.oninput();
  await ltick(400);
  assert.ok(!calls.some(([c]) => c === 'notary.address_lookup'),
    'go khong duoc tu gui lookup');
});

test('TASK-4: bam Tra gui drafting, hien ket qua + Copy, khong sua du lieu', async () => {
  const copied = [];
  Object.defineProperty(globalThis, 'navigator',
    { value: { clipboard: { writeText: async (t) => { copied.push(t); } } },
      configurable: true });
  try {
    const { model, view, calls } = build(test,
      { respond: lookupResponders('found') });
    const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
    const before = model.state.stage.people[0].dia_chi;
    fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
    await ltick(200);
    assert.ok(calls.some(([c, pl]) => c === 'notary.address_lookup' &&
      pl.presentation === 'drafting' && pl.query === 'Xã A, Tỉnh P'));
    const box = collect(view.el,
      (e) => e.id === `address-person-${p.row_id}`)[0];
    assert.ok(box.textContent.includes('Tìm thấy 2 dòng'));
    // Cung unit_id hien rieng hai dong, moi dong mot Copy.
    const c0 = fid(view.el, `lookup-copy:person:${p.row_id}:0`);
    const c1 = fid(view.el, `lookup-copy:person:${p.row_id}:1`);
    assert.ok(c0 && c1, 'moi dong mot Copy rieng');
    await c0.onclick();
    assert.deepEqual(copied, ['xã A, tỉnh P']);
    assert.equal(model.state.stage.people[0].dia_chi, before);
    // Copy khong dong hop, khong sua o.
    assert.ok(fid(view.el, `lookup-copy:person:${p.row_id}:0`));
    assert.equal(c0.textContent, 'Đã copy');
  } finally {
    delete globalThis.navigator;
  }
});

test('TASK-4: Copy loi bao loi, khong bao da copy', async () => {
  Object.defineProperty(globalThis, 'navigator',
    { value: { clipboard: { writeText: async () => {
      throw new Error('denied'); } } }, configurable: true });
  try {
    const { model, view } = build(test,
      { respond: lookupResponders('found') });
    const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
    fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
    await ltick(200);
    const c0 = fid(view.el, `lookup-copy:person:${p.row_id}:0`);
    await c0.onclick();
    assert.equal(c0.textContent, 'Copy');
    const box = collect(view.el,
      (e) => e.id === `address-person-${p.row_id}`)[0];
    assert.ok(box.textContent.includes('Copy thất bại'));
  } finally {
    delete globalThis.navigator;
  }
});

test('TASK-4: issuer tra dia chi nguoi chet; posting tra o niem yet', async () => {
  const { model, view, calls } = build(test,
    { respond: lookupResponders('found') });
  const p = model.addPerson({ ho_ten: 'Chết', ngay_chet: '2020-01-01',
    dia_chi: 'Xã Chết, Tỉnh P', noi_cap: 'UBND Xã Cũ' });
  const a = model.addAsset({ dia_chi: 'Xã Tài sản, Tỉnh P' });
  model.updateCaseMeta('noi_niem_yet', 'Nơi niêm yết thật');
  await ltick(100);
  fid(view.el, `lookup-tra:issuer:${p.row_id}`).onclick();
  await ltick(200);
  fid(view.el, 'lookup-tra:posting:posting').onclick();
  await ltick(200);
  const queries = calls.filter(([c]) => c === 'notary.address_lookup')
    .map(([, pl]) => pl.query);
  assert.ok(queries.includes('Xã Chết, Tỉnh P'),
    'issuer phai tra dia chi nguoi chet, thay: ' + JSON.stringify(queries));
  assert.ok(queries.includes('Nơi niêm yết thật'),
    'posting phai tra noi dung o niem yet, khong lay dia chi tai san');
  assert.ok(!queries.includes('Xã Tài sản, Tỉnh P'));
});

test('TASK-4: too_many Huy khong goi full; Dong y mo overlay dung query', async () => {
  const b1 = build(test, { confirm: false, respond: lookupResponders('too_many') });
  b1.model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
  const p1 = b1.model.state.stage.people[0].row_id;
  await ltick(100);
  fid(b1.view.el, `lookup-tra:person:${p1}`).onclick();
  await ltick(200);
  assert.equal(b1.calls.filter(([c, pl]) => c === 'notary.address_lookup' &&
    pl.presentation === 'full').length, 0, 'Huy khong duoc goi full');
  assert.equal(collect(b1.view.el,
    (e) => e.dataset && e.dataset.fid === 'lookup-full-list').length, 0);

  const seen = [];
  const b2 = build(test, { confirm: true, confirmSeen: seen,
    respond: lookupResponders('too_many') });
  const p2 = b2.model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  fid(b2.view.el, `lookup-tra:person:${p2.row_id}`).onclick();
  await ltick(300);
  const fullCalls = b2.calls.filter(([c, pl]) => c === 'notary.address_lookup' &&
    pl.presentation === 'full');
  assert.equal(fullCalls.length, 1);
  assert.equal(fullCalls[0][1].query, 'Xã A, Tỉnh P');
  assert.equal(seen.length, 1);
  assert.equal(seen[0].title, 'Nhiều kết quả khớp. Xem đầy đủ?');
  const list = fid(b2.view.el, 'lookup-full-list');
  assert.ok(list, 'thieu danh sach overlay');
  assert.ok(list.textContent.includes('nguồn một'));
  assert.ok(list.textContent.includes('nguồn hai'));
  assert.ok(fid(b2.view.el, 'lookup-full-query'));
  assert.ok(fid(b2.view.el, 'lookup-full-tra'));
  assert.ok(fid(b2.view.el, 'lookup-full-close'));
});

test('TASK-4: sua query trong overlay khong tu tra; Tra moi gui full', async () => {
  const { model, view, calls } = build(test,
    { confirm: true, respond: lookupResponders('too_many') });
  const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
  await ltick(300);
  const n0 = calls.length;
  const q = fid(view.el, 'lookup-full-query');
  q.value = 'Xã A sửa, Tỉnh P';
  await ltick(200);
  assert.equal(calls.length, n0, 'sua query khong duoc tu gui');
  fid(view.el, 'lookup-full-tra').onclick();
  await ltick(200);
  assert.equal(calls.length, n0 + 1);
  assert.deepEqual(calls[calls.length - 1][1],
    { query: 'Xã A sửa, Tỉnh P', presentation: 'full' });
});

test('TASK-4: dong overlay giu nhap, caret, scroll; late response bi bo', async () => {
  const { model, view, calls } = build(test,
    { confirm: true, respond: lookupResponders('too_many') });
  const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  const inp = fid(view.el, `p:${p.row_id}:dia_chi`);
  inp.setSelectionRange(2, 5);
  const dp = panelOf(inp, view.el);
  dp.scrollTop = 55;
  fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
  await ltick(300);
  assert.ok(fid(view.el, 'lookup-full-list'), 'overlay chua mo');
  // Doi chu trong luc overlay mo van giu trong model (nhap chua luu).
  assert.equal(model.state.stage.people[0].dia_chi, 'Xã A, Tỉnh P');
  fid(view.el, 'lookup-full-close').onclick();
  await ltick(100);
  assert.equal(collect(view.el,
    (e) => e.dataset && e.dataset.fid === 'lookup-full-list').length, 0);
  const inp2 = fid(view.el, `p:${p.row_id}:dia_chi`);
  assert.ok(inp2, 'mat o nhap sau khi dong');
  assert.equal(inp2.value, 'Xã A, Tỉnh P');
  assert.equal(document.activeElement, inp2);
  assert.deepEqual([inp2.selectionStart, inp2.selectionEnd], [2, 5]);
  const dp2 = panelOf(inp2, view.el);
  assert.equal(dp2.scrollTop, 55);
  assert.ok(!calls.some(([c, pl]) => c === 'notary.address_lookup' &&
    pl.presentation === 'full' && pl.query !== 'Xã A, Tỉnh P'));
});

function fireMouseDown(el) {
  for (const f of (el._ev && el._ev.mousedown) || []) f();
}

test('R3: ket qua ve khi dang sua o khac van hien, khong giut focus', async () => {
  const { model, view } = build(test,
    { respond: lookupResponders('found') });
  const p = model.addPerson({ ho_ten: 'A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  const tra = fid(view.el, `lookup-tra:person:${p.row_id}`);
  const nameInp = fid(view.el, `p:${p.row_id}:ho_ten`);
  nameInp.focus();
  fireMouseDown(tra);
  tra.onclick();
  // Nguoi dung chuyen sang sua o Ho ten trong luc cho (nguon khong doi).
  await ltick(50);
  assert.equal(document.activeElement, nameInp);
  await ltick(300);
  const box = collect(view.el,
    (e) => e.id === `address-person-${p.row_id}`)[0];
  assert.ok(box.textContent.includes('Tìm thấy 2 dòng'),
    'ket qua phai hien du dang sua o khac, thay: ' + box.textContent);
  assert.ok(fid(view.el, `lookup-copy:person:${p.row_id}:0`));
  assert.equal(document.activeElement, nameInp,
    'khong duoc keo con tro ve nut Tra');
});

test('R5: Huy cau hoi phuc hoi dung o dang sua, vung chon va scroll', async () => {
  const { model, view, calls } = build(test,
    { confirm: false, respond: lookupResponders('too_many') });
  const p = model.addPerson({ ho_ten: 'Nguyen Van A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  const nameInp = fid(view.el, `p:${p.row_id}:ho_ten`);
  nameInp.focus();
  nameInp.setSelectionRange(1, 4);
  const dp = panelOf(nameInp, view.el);
  dp.scrollTop = 42;
  const tra = fid(view.el, `lookup-tra:person:${p.row_id}`);
  fireMouseDown(tra);
  tra.onclick();
  await ltick(300);
  assert.equal(calls.filter(([c, pl]) => c === 'notary.address_lookup' &&
    pl.presentation === 'full').length, 0);
  const nameInp2 = fid(view.el, `p:${p.row_id}:ho_ten`);
  assert.equal(document.activeElement, nameInp2,
    'Huy phai tra focus ve o Ho ten dang sua');
  assert.deepEqual([nameInp2.selectionStart, nameInp2.selectionEnd], [1, 4]);
  assert.equal(panelOf(nameInp2, view.el).scrollTop, 42);
});

test('R5: dong full khi dang sua o khac dich phuc hoi o do', async () => {
  const { model, view } = build(test,
    { confirm: true, respond: lookupResponders('too_many') });
  const p = model.addPerson({ ho_ten: 'Nguyen Van A', dia_chi: 'Xã A, Tỉnh P' });
  await ltick(100);
  const nameInp = fid(view.el, `p:${p.row_id}:ho_ten`);
  nameInp.focus();
  nameInp.setSelectionRange(0, 6);
  const tra = fid(view.el, `lookup-tra:person:${p.row_id}`);
  fireMouseDown(tra);
  tra.onclick();
  await ltick(300);
  assert.ok(fid(view.el, 'lookup-full-list'), 'overlay chua mo');
  fid(view.el, 'lookup-full-close').onclick();
  await ltick(100);
  const nameInp2 = fid(view.el, `p:${p.row_id}:ho_ten`);
  assert.equal(document.activeElement, nameInp2);
  assert.deepEqual([nameInp2.selectionStart, nameInp2.selectionEnd], [0, 6]);
  assert.equal(nameInp2.value, 'Nguyen Van A');
});

test('P4: reversed replies from two Tra clicks open just one confirmation', async () => {
  const pending = [], seen = [];
  let finishConfirm;
  const confirmation = new Promise(resolve => { finishConfirm = resolve; });
  const { model, view } = build(test, { confirm: confirmation, confirmSeen: seen,
    respond: (cmd) => cmd === 'notary.address_lookup' ? new Promise(r => pending.push(r)) : null });
  const p = model.addPerson({ dia_chi: 'Query A' });
  fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
  fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
  pending[1](lookupResponders('too_many')('notary.address_lookup', { presentation: 'drafting' }));
  await ltick();
  pending[0](lookupResponders('too_many')('notary.address_lookup', { presentation: 'drafting' }));
  await ltick();
  try {
    assert.equal(seen.length, 1);
  } finally {
    finishConfirm(false);
    await ltick();
  }
  assert.equal(model.state.addressSlots['person:' + p.row_id], undefined);
});

test('P7: background replies preserve full Copy node, focus and scroll', async () => {
  const pending = [];
  const { model, view, document } = build(test, { respond: (cmd, payload) => {
    if (cmd !== 'notary.address_lookup') return null;
    if (payload.query === 'Delayed') return new Promise(r => pending.push(r));
    return lookupResponders('too_many')(cmd, payload);
  }});
  const p = model.addPerson({ dia_chi: 'Delayed' });
  const a = model.addAsset({ dia_chi: 'Open full' });
  fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
  fid(view.el, `lookup-tra:asset:${a.row_id}`).onclick();
  await ltick();
  const copy = fid(view.el, 'lookup-full-copy:0'), list = fid(view.el, 'lookup-full-list');
  copy.focus(); list.scrollTop = 55;
  pending[0](lookupResponders('found')('notary.address_lookup', { presentation: 'drafting' }));
  await ltick();
  assert.equal(fid(view.el, 'lookup-full-copy:0'), copy);
  assert.equal(document.activeElement, copy);
  assert.equal(list.scrollTop, 55);
});

test('P8: delayed clipboard failure remains visible after re-Tra', async () => {
  let fail;
  Object.defineProperty(globalThis, 'navigator', { configurable: true,
    value: { clipboard: { writeText: () => new Promise((_, reject) => { fail = reject; }) } } });
  try {
    const { model, view } = build(test, { respond: lookupResponders('found') });
    const p = model.addPerson({ dia_chi: 'Query A' });
    fid(view.el, `lookup-tra:person:${p.row_id}`).onclick(); await ltick();
    const copying = fid(view.el, `lookup-copy:person:${p.row_id}:0`).onclick();
    fid(view.el, `lookup-tra:person:${p.row_id}`).onclick(); await ltick();
    fail(new Error('denied')); await copying;
    assert.ok(view.el.textContent.includes('Copy thất bại'));
  } finally { delete globalThis.navigator; }
});

test('P12: keyboard Tra cancel restores previous input and selection without mousedown', async () => {
  const { model, view, document } = build(test, { confirm: false, respond: lookupResponders('too_many') });
  const p = model.addPerson({ ho_ten: 'Keyboard name', dia_chi: 'Query A' });
  const name = fid(view.el, `p:${p.row_id}:ho_ten`);
  name.focus(); name.setSelectionRange(2, 6);
  const tra = fid(view.el, `lookup-tra:person:${p.row_id}`);
  tra.focus(); tra.onclick(); await ltick();
  assert.equal(document.activeElement.dataset.fid, name.dataset.fid);
  assert.deepEqual([document.activeElement.selectionStart, document.activeElement.selectionEnd], [2, 6]);
});

test('P11: terminal lookup messages remove Copy in drafting and full', async () => {
  for (const [status, message] of [['not_found', 'Không tìm thấy'],
    ['invalid_input', 'Chuỗi tra chưa hợp lệ'], ['reload_failed', 'Không đọc được bảng địa chỉ cục bộ']]) {
    let mode = 'found';
    const { model, view } = build(test, { respond: (cmd, payload) => {
      if (cmd !== 'notary.address_lookup') return null;
      if (mode === 'found' || mode === 'too_many') return lookupResponders(mode)(cmd, payload);
      return { ok: true, data: { schema_version: 'notary.address-lookup.v2', status,
        presentation: payload.presentation, total: 0, results: [], dataset_version: 'v2', revision: 1 } };
    }});
    const p = model.addPerson({ dia_chi: 'Query A' });
    const tra = () => fid(view.el, `lookup-tra:person:${p.row_id}`).onclick();
    tra(); await ltick();
    mode = 'error'; tra(); await ltick();
    assert.ok(collect(view.el, e => e.id === `address-person-${p.row_id}`)[0].textContent.includes(message));
    assert.equal(fid(view.el, `lookup-copy:person:${p.row_id}:0`), null);
    mode = 'too_many'; tra(); await ltick();
    mode = 'error'; fid(view.el, 'lookup-full-tra').onclick(); await ltick();
    assert.ok(fid(view.el, 'lookup-full-note').textContent.includes(message));
    assert.equal(fid(view.el, 'lookup-full-copy:0'), null);
    fid(view.el, 'lookup-full-close').onclick();
  }
});

test('P6: Word posting Tra uses its own draft and Copy does not save; full suspends Word', async () => {
  let mode = 'found';
  Object.defineProperty(globalThis, 'navigator', { configurable: true,
    value: { clipboard: { writeText: async () => {} } } });
  try {
    const { model, view, calls, document } = build(test, { draft: false,
      respond: (cmd, payload) => lookupResponders(mode)(cmd, payload) });
    findBtns(view.el, 'Xuất Word')[0].onclick(); await ltick();
    const input = fid(view.el, 'word-posting-input');
    assert.ok(input);
    input.value = 'Word draft query'; input.oninput(); input.focus(); input.setSelectionRange(1, 5);
    const wordBox = input.closest('.cd-word-modal');
    const lookupRow = input.parentElement;
    assert.ok(lookupRow.classList.contains('cd-lookup-row'));
    assert.ok(input.classList.contains('cd-cell'));
    assert.equal(lookupRow.children[0], input);
    assert.equal(lookupRow.children[1], fid(wordBox, 'word-lookup-tra:posting:posting'));
    const postingRegion = lookupRow.parentElement;
    assert.ok(!postingRegion.classList.contains('cd-toolbar'));
    const resultRegion = collect(wordBox, e => e.id === 'address-dlg-posting-posting')[0].parentElement;
    assert.equal(resultRegion.parentElement, postingRegion);
    assert.ok(postingRegion.children.indexOf(resultRegion) > postingRegion.children.indexOf(lookupRow));
    const tra = () => fid(wordBox, 'word-lookup-tra:posting:posting').onclick();
    tra(); await ltick();
    assert.deepEqual(calls.filter(([cmd]) => cmd === 'notary.address_lookup')[0][1],
      { query: 'Word draft query', presentation: 'drafting' });
    await fid(wordBox, 'word-lookup-copy:posting:posting:0').onclick();
    const identifiers = collect(view.el, e => !!e.dataset.fid).map(e => e.dataset.fid);
    assert.equal(new Set(identifiers).size, identifiers.length);
    assert.ok(!calls.some(([cmd]) => ['notary.workspace_update', 'notary.workspace_commit_stage'].includes(cmd)));
    mode = 'too_many'; tra(); await ltick();
    assert.ok(fid(view.el, 'lookup-full-list'));
    assert.equal(wordBox.parentElement.hidden, true);
    assert.equal(collect(view.el, e => e.getAttribute('role') === 'dialog').length, 1);
    const lastFull = fid(view.el, 'lookup-full-close');
    const firstFull = fid(view.el, 'lookup-full-query').closest('.modal')
      .querySelector('button, input, textarea, select, [tabindex]');
    lastFull.focus();
    document.dispatch('keydown', { key: 'Tab', preventDefault() {} });
    assert.equal(document.activeElement, firstFull);
    firstFull.focus();
    document.dispatch('keydown', { key: 'Tab', shiftKey: true, preventDefault() {} });
    assert.equal(document.activeElement, lastFull);
    document.dispatch('keydown', { key: 'Escape' });
    assert.equal(wordBox.parentElement.hidden, false);
    assert.equal(document.activeElement, input);
    assert.deepEqual([input.selectionStart, input.selectionEnd], [1, 5]);
    assert.equal(input.value, 'Word draft query');
    const wordItems = wordBox.querySelectorAll('button, input, textarea, select, [tabindex]')
      .filter(e => !e.disabled && !e.hidden);
    wordItems.at(-1).focus();
    document.dispatch('keydown', { key: 'Tab', preventDefault() {} });
    assert.equal(document.activeElement, wordItems[0]);
    document.dispatch('keydown', { key: 'Tab', shiftKey: true, preventDefault() {} });
    assert.equal(document.activeElement, wordItems.at(-1));
    document.dispatch('keydown', { key: 'Escape' });
    assert.equal(wordBox.isConnected, false);
  } finally { delete globalThis.navigator; }
});

test('Word focused Copy refreshes changed slot and keeps delayed failure in Word', async () => {
  let fail;
  Object.defineProperty(globalThis, 'navigator', { configurable: true,
    value: { clipboard: { writeText: () => new Promise((_, reject) => { fail = reject; }) } } });
  try {
    const { model, view, calls } = build(test, { draft: false, respond: lookupResponders('found') });
    findBtns(view.el, 'Xuất Word')[0].onclick(); await ltick();
    const input = fid(view.el, 'word-posting-input'), word = input.closest('.cd-word-modal');
    const tra = () => fid(word, 'word-lookup-tra:posting:posting').onclick();
    tra(); await ltick();
    const copy = fid(word, 'word-lookup-copy:posting:posting:0'); copy.focus();
    model.dismissNotice();
    assert.equal(fid(word, 'word-lookup-copy:posting:posting:0'), copy);
    const copying = copy.onclick();
    model.updateCaseMeta('noi_niem_yet', 'Changed source');
    assert.equal(fid(word, 'word-lookup-copy:posting:posting:0'), null);
    fail(new Error('denied')); await copying;
    assert.ok(word.textContent.includes('Copy thất bại'));
    const main = collect(view.el, e => e.id === 'address-posting-posting')[0];
    assert.ok(!main.textContent.includes('Copy thất bại'));
    assert.ok(!calls.some(([cmd]) => cmd === 'notary.workspace_update'));
  } finally { delete globalThis.navigator; }
});

test('disposed Word origin cannot open full over reopened Word; disposed Copy notifies', async () => {
  const pending = [], seen = [];
  let fail;
  Object.defineProperty(globalThis, 'navigator', { configurable: true,
    value: { clipboard: { writeText: () => new Promise((_, reject) => { fail = reject; }) } } });
  try {
    let delayed = false;
    const { view, document, notifications } = build(test, { draft: false, confirmSeen: seen,
      respond: (cmd, payload) => cmd === 'notary.address_lookup' && delayed
        ? new Promise(r => pending.push(r)) : lookupResponders('found')(cmd, payload) });
    const open = async () => { findBtns(view.el, 'Xuất Word')[0].onclick(); await ltick();
      return fid(view.el, 'word-posting-input').closest('.cd-word-modal'); };
    const oldWord = await open();
    fid(oldWord, 'word-lookup-tra:posting:posting').onclick(); await ltick();
    const copying = fid(oldWord, 'word-lookup-copy:posting:posting:0').onclick();
    delayed = true;
    fid(oldWord, 'word-lookup-tra:posting:posting').onclick();
    document.dispatch('keydown', { key: 'Escape' });
    const newWord = await open();
    pending.shift()(lookupResponders('too_many')('notary.address_lookup', { presentation: 'drafting' }));
    await ltick();
    assert.equal(seen.length, 0);
    assert.equal(fid(view.el, 'lookup-full-list'), null);
    assert.equal(newWord.parentElement.hidden, false);
    fail(new Error('denied')); await copying;
    assert.ok(notifications.some(msg => msg.includes('Copy thất bại')));
    assert.ok(!newWord.textContent.includes('Copy thất bại'));
  } finally { delete globalThis.navigator; }
});
