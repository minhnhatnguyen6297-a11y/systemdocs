// Hoi quy hanh vi: thong bao loi So do lay dung formatter tu catalog that.
// index.html nap error-catalog.js TRUOC relationship-diagram.js (dong 25-28);
// binding cua pane doc window.G1_NOTARY_ERRORS ngay luc nap. Test nay nap
// dung thu tu do tren source that: truoc ban sua, ca ba nhanh loi (evaluate,
// render diagramErrors, save) nem `relErrText is not a function`.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { makeDom, collect } from './dom-stub.mjs';

const require = createRequire(import.meta.url);
const R = (p) => '../src/renderer/notary/' + p;

const L = require('../src/renderer/lib.js');
const M = require(R('case-drafting-model.js'));
const VIEW = require(R('case-drafting-view.js'));
const INTAKE = require(R('intake-dialog.js'));
const WORD = require(R('word-export-dialog.js'));

if (typeof globalThis.crypto?.randomUUID !== 'function') {
  const { webcrypto } = require('node:crypto');
  globalThis.crypto = webcrypto;
}

function catalog() { return require(R('error-catalog.js')); }

// window dung nhu index.html: catalog da co truoc khi so do duoc nap;
// thieu catalog = truong hop nap tach file trong Node (nhanh du phong).
function loadDiagram({ withCatalog = true } = {}) {
  const win = { G1_NOTARY_MODEL: M, G1_NOTARY_VIEW: VIEW,
                G1_NOTARY_INTAKE: INTAKE, G1_NOTARY_WORD: WORD };
  if (withCatalog) win.G1_NOTARY_ERRORS = catalog();
  global.window = win;
  delete require.cache[require.resolve(R('relationship-diagram.js'))];
  const DIAGRAM = require(R('relationship-diagram.js'));
  win.G1_NOTARY_DIAGRAM = DIAGRAM;
  return DIAGRAM;
}

const PEOPLE = [
  { row_id: 'c1', ho_ten: 'Người Một', ngay_sinh: '1955-01-01',
    ngay_chet: '2020-05-10' },
  { row_id: 'c2', ho_ten: 'Người Hai', ngay_sinh: '1985-03-02' },
];

function ownerNode() {
  return { id: 'owner', personId: 'c1', parentSlotIds: [], spouseSlotId: null,
           ownPositions: [], receivePositions: [],
           hidden: false, deleted: false };
}

function childNode() {
  return { id: 'child_1', personId: null, parentSlotIds: ['owner'],
           spouseSlotId: null, ownPositions: [], receivePositions: [],
           hidden: false, deleted: false };
}

// Sua diagram ma KHONG dung Stage (owner la du lieu Stage —
// setOwnerRow() bat stageDirty, khien nut Luu bi gate "Cap nhat Stage").
function dirtyDiagram(model) {
  return model.movePerson('c2', 'child_1');
}

// Case da ton tai, ghi duoc, co diagram — de nut Luu du dieu kien bat.
function seedCase(model) {
  const s = model.state;
  s.status = 'ready';
  s.caseId = 42;
  s.caseInfo = { id: 42, case_type: 'inheritance', document_type: 'khai_nhan',
                 status: 'active', locked: false, revision: 3 };
  s.backendMode = 'real';
  s.revision = 3;
  s.locked = false;
  s.unsupported = false;
  s.capabilities = { intake: [], diagram: true, word_export: true };
  s.committed = { people: structuredClone(PEOPLE), assets: [] };
  s.stage = structuredClone(s.committed);
  s.stage.owner_row_id = 'c1';
  s.committedDiagram = { version: 3, domain: 'inheritance',
                         nodes: [ownerNode(), childNode()] };
  s.diagram = structuredClone(s.committedDiagram);
  model.dismissNotice();
}

function build(t, { withCatalog = true, client } = {}) {
  const { document } = makeDom();
  global.document = document;
  loadDiagram({ withCatalog });
  const notices = [];
  const calls = [];
  const run = client || (async () => ({ ok: true, data: {} }));
  const cl = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    return run(cmd, payload);
  } };
  const model = M.createModel({ client: cl });
  const view = VIEW.createNotaryModuleView({
    model, lib: L, notify: (msg, isErr) => notices.push([msg, isErr]),
    confirm: async () => true,
    pickFiles: async () => ({ ok: true, data: { files: [] } }),
    openPath: async () => ({ ok: true }),
    registerDroppedFile: null,
    cancelJob: async () => ({ ok: true }),
    runCommand: cl.run,
  });
  document.body.append(view.el);
  seedCase(model);
  t.after(() => { delete global.window; delete global.document; });
  return { model, view, document, notices, calls, CAT: catalog() };
}

function findBtns(root, label) {
  return collect(root, (e) =>
    e.tagName === 'BUTTON' && e.textContent.includes(label));
}

function byCls(root, cls) {
  return collect(root, (e) => e.classList.contains(cls));
}

const EVAL_ERR = { code: 'stage_validation_error', message: 'synthetic' };

function errorClient(perCommand) {
  return async (cmd) => (perCommand[cmd] || { ok: true, data: {} });
}

// ---------- danh gia loi ----------

function errSlot(view) {
  return byCls(view.el, 'cd-diagram-errslot')[0];
}
function stageSlot(view) {
  return byCls(view.el, 'cd-stage-status')[0];
}
function errLines(view) {
  const slot = errSlot(view);
  return slot ? byCls(slot, 'error').map((e) => e.textContent) : [];
}

test('R12/R13 evaluate lỗi: một dòng trong vùng sơ đồ, không toast', async () => {
  const { view, model, notices, CAT } = build(test, {
    client: errorClient({ 'notary.diagram_evaluate':
      { ok: false, error: { ...EVAL_ERR } } }) });
  const evalBtn = findBtns(view.el, 'Xem cách tính')[0];
  assert.ok(evalBtn, 'thieu nut Xem cach tinh');
  await evalBtn.onclick();
  assert.deepEqual(notices, [], 'lỗi hiện tại chỗ, không toast');
  assert.deepEqual(errLines(view), [CAT.errText(EVAL_ERR)]);
  assert.doesNotMatch(errLines(view)[0], /stage_validation_error/,
    'R12: không in mã');
  assert.equal(stageSlot(view).textContent, '',
    'không lặp cùng lỗi ở card Stage');
  assert.equal(model.state.busy, null, 'model con busy sau loi');
  assert.equal(model.state.error.code, 'stage_validation_error');
});

test('tu danh gia sau thao tac (debounce ~500ms): một dòng lỗi, không bỏ mặc Promise',
  async () => {
    const { view, model, notices, CAT } = build(test, {
      client: errorClient({ 'notary.diagram_evaluate':
        { ok: false, error: { ...EVAL_ERR } } }) });
    // Thao tac phai KHONG qua Stage gate: bo gan tren node owner bat
    // stageDirty (owner la du lieu Stage) nen debounce se bi bo qua.
    assert.equal(model.movePerson('c2', 'child_1'), true);
    const card = collect(view.el, (e) => e.dataset.nodeId === 'child_1')[0];
    assert.ok(card, 'thieu card child_1');
    const un = byCls(card, 'js-node-unassign')[0];
    assert.ok(un, 'thieu nut bo gan tren card co nguoi');
    const rejections = [];
    const onRej = (e) => rejections.push(String(e && e.message || e));
    process.on('unhandledRejection', onRej);
    test.after(() => process.off('unhandledRejection', onRej));
    un.click();
    assert.deepEqual(notices, [], 'chua het debounce thi chua co loi');
    await new Promise((r) => setTimeout(r, 650));
    assert.deepEqual(notices, [], 'debounce cũng không toast');
    assert.deepEqual(errLines(view), [CAT.errText(EVAL_ERR)],
      'tự đánh giá báo lỗi đúng một lần tại vùng sơ đồ');
    assert.deepEqual(rejections, [],
      'promise danh gia khong duoc bo mac (unhandled rejection)');
  });

// ---------- dung danh sach loi ----------

test('diagram_invalid_state: loi hien mot dong duoi so do, khong toast rieng',
  async () => {
    const inner = { code: 'diagram_invalid_state', message: 'vong quan he' };
    const { view, notices, CAT } = build(test, {
      client: errorClient({ 'notary.diagram_evaluate': { ok: false, error: {
        code: 'diagram_invalid_state', message: 'synthetic',
        details: { errors: [{ ...inner }] } } } }) });
    assert.ok(byCls(view.el, 'cd-rel-card')[0], 'thieu card so do');
    await findBtns(view.el, 'Xem cách tính')[0].onclick();
    assert.deepEqual(notices, [], 'invalid_state khong duoc toast rieng');
    assert.deepEqual(errLines(view), [CAT.errText(inner)],
      'loi duoi so do phai dung errText cua catalog that');
  });

// ---------- luu loi thuong ----------

test('luu diagram_invalid_state: mot dong duoi so do, giu nhap', async () => {
  const inner = { code: 'missing_land_owner',
                  message: 'Chưa có người để lại tài sản trên sơ đồ' };
  const { view, model, notices, CAT } = build(test, {
    client: errorClient({ 'notary.workspace_save_case': { ok: false, error: {
      code: 'diagram_invalid_state', message: 'synthetic',
      details: { errors: [{ ...inner }] } } } }) });
  assert.equal(dirtyDiagram(model), true, 'mutation không đổi draft');
  const save = findBtns(view.el, 'Lưu hồ sơ')[0];
  assert.ok(save, 'thiếu nút Lưu sơ đồ');
  await save.onclick();
  assert.deepEqual(notices, [], 'không toast trùng');
  assert.equal(model.state.diagramDirty, true, 'nháp còn nguyên');
  assert.equal(model.state.revision, 3, 'revision không đổi khi bị từ chối');
  assert.deepEqual(errLines(view), [CAT.errText(inner)],
    'lỗi dưới sơ đồ phải đúng errText của catalog thật');
  assert.equal(stageSlot(view).textContent, '',
    'cùng lỗi không được lặp ở Stage');
});

test('luu loi workspace_locked: một dòng tại Stage, nhap con nguyen',
  async () => {
    const err = { code: 'workspace_locked', message: 'phien khac dang mo' };
    const { view, model, notices, CAT } = build(test, {
      client: errorClient({ 'notary.workspace_save_case': { ok: false, error: err } }) });
    assert.equal(dirtyDiagram(model), true, 'mutation khong doi draft');
    const save = findBtns(view.el, 'Lưu hồ sơ')[0];
    assert.ok(save, 'thieu nut Luu so do');
    assert.equal(save.disabled, false, 'nut luu phai bat truoc khi bam');
    await save.onclick();
    assert.deepEqual(notices, [], 'không toast trùng');
    assert.equal(stageSlot(view).textContent, CAT.errText(err));
    assert.deepEqual(errLines(view), [],
      'lỗi không thuộc sơ đồ không hiện ở vùng sơ đồ');
    assert.equal(model.state.diagramDirty, true, 'nhap bi mat sau loi luu');
    assert.equal(model.state.revision, 3, 'revision khong duoc doi khi loi');
    assert.equal(model.state.diagram.nodes
      .find((n) => n.id === 'child_1').personId, 'c2',
    'draft vua sua phai con nguyen');
});

// ---------- xung dot phien ban ----------

test('luu xung dot: luong conflict hien co, khong toast rieng', async () => {
  const { view, model, notices } = build(test, {
    client: errorClient({ 'notary.workspace_save_case': { ok: false, error: {
      code: 'workspace_conflict', details: { server_revision: 9 } } } }) });
  assert.equal(dirtyDiagram(model), true);
  await findBtns(view.el, 'Lưu hồ sơ')[0].onclick();
  assert.deepEqual(notices, [], 'conflict khong duoc toast rieng');
  const modal = byCls(view.el, 'modal')[0];
  assert.ok(modal, 'thieu hop thoai xung dot hien co');
  assert.match(modal.textContent, /đã thay đổi trên máy chủ/);
  assert.equal(model.state.diagramDirty, true, 'nhap phai con');
  assert.equal(model.state.revision, 3, 'khong duoc ghi de');
});

// ---------- thanh cong ----------

test('evaluate + luu thanh cong: khong toast loi, revision tang mot lan',
  async () => {
    let saved = null;
    const { view, model, notices } = build(test, { client: async (cmd, p) => {
      if (cmd === 'notary.diagram_evaluate') {
        return { ok: true, data: { evaluated_revision: 3, render_model: {
          engineVersion: 2, status: 'ok', allocations: {}, breakdowns: [],
          requiredSlots: [], warnings: [], errors: [],
          unresolvedEstates: [], conservation: {} } } };
      }
      if (cmd === 'notary.workspace_save_case') {
        saved = structuredClone(p.diagram.state);
        return { ok: true, data: {
          case: { id: 42, case_type: 'inheritance',
                  document_type: 'khai_nhan', status: 'done',
                  locked: false, revision: 4 },
          backend_mode: 'real',
          capabilities: { intake: [], diagram: true, word_export: true },
          stage: structuredClone(p.stage),
          diagram: { state: structuredClone(saved), render_model: null },
          warnings: [] } };
      }
      return { ok: true, data: {} };
    } });
    await findBtns(view.el, 'Xem cách tính')[0].onclick();
    assert.deepEqual(notices, [], 'evaluate thanh cong khong duoc toast');
    assert.equal(model.state.renderModel.status, 'ok');
    dirtyDiagram(model);
    await findBtns(view.el, 'Lưu hồ sơ')[0].onclick();
    assert.deepEqual(notices, [], 'luu thanh cong khong duoc toast loi');
    assert.equal(model.state.revision, 4, 'revision phai tang dung mot lan');
    assert.equal(model.state.diagramDirty, false, 'dirty phai sach sau luu');
    assert.equal(saved.nodes.find((n) => n.id === 'child_1').personId, 'c2',
      'state gui len phai la draft vua sua');
  });

// ---------- nap tach file trong Node (khong catalog) ----------

test('khong co catalog khi nap: nhanh du phong van mot cau, khong ma', async () => {
  const { view, notices } = build(test, { withCatalog: false,
    client: errorClient({ 'notary.diagram_evaluate':
      { ok: false, error: { ...EVAL_ERR } } }) });
  await findBtns(view.el, 'Xem cách tính')[0].onclick();
  assert.deepEqual(notices, [], 'không toast trùng');
  assert.deepEqual(errLines(view), ['synthetic'],
    'fallback dùng message, không in mã');
});

test('R12 missing_land_owner: một câu nói chuyện gì, không dạy thao tác', () => {
  const CAT = catalog();
  const error = { code: 'missing_land_owner' };
  const text = CAT.errText(error);
  assert.equal(text, 'Chưa đánh dấu Chủ đất cho người để lại tài sản');
  assert.doesNotMatch(text, /chip "Chủ"/);
  assert.doesNotMatch(text, /missing_land_owner/);
  assert.match(CAT.describeError(error).title, /đánh dấu Chủ đất/);
});

for (const draft of [false, true]) {
  for (const withDetails of [true, false]) {
    test(`${draft ? 'nhap moi' : 'case cu'}: mot dong loi diagram dau tien, details=${withDetails}`, async (t) => {
      const first = { code: 'missing_land_owner' };
      const error = { code: 'diagram_invalid_state',
        ...(withDetails ? { details: { errors: [first, { code: 'duplicate_person' }] } } : {}) };
      const command = 'notary.workspace_save_case';
      const { model, view, notices, CAT } = build(t, {
        client: errorClient({ [command]: { ok: false, error } }),
      });
      if (draft) await model.newDraft('inheritance');
      const button = findBtns(view.el, 'Lưu hồ sơ')[0];
      assert.ok(button);
      await button.onclick();
      assert.deepEqual(notices, [], 'không toast trùng');
      // Mỗi lỗi engine một dòng (không toast/banner trùng): details có
      // 2 lỗi thì vùng sơ đồ có đúng 2 dòng.
      assert.deepEqual(errLines(view), withDetails
        ? [CAT.errText(first), CAT.errText({ code: 'duplicate_person' })]
        : [CAT.errText(error)]);
    });
  }
}
