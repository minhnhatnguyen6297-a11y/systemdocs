'use strict';

/* Case-drafting model — state machine thuan cho tab Soạn hồ sơ (MIN-111).
 *
 * SOT hanh vi: notary_v2/docs/platform/case-workspace/drafting-tab.md
 * Wire shape: contracts/notary-case-drafting.md (notary.case-drafting.v1).
 *
 * - Khong DOM, khong Node API bat buoc: chay trong renderer (<script>) va
 *   node --test. Export UMD: window.G1_NOTARY_MODEL + module.exports.
 * - Command client inject qua deps.client.run(command, payload):
 *     Promise<{ok:true, data, partial?} | {ok:false, error}>
 *   o renderer runCommand adapter boc submitCommand+getJob toi terminal.
 * - Draft chi song trong phien (drafting-tab §4): khong localStorage,
 *   khong log — state giu trong object nay.
 * - Khong bao gio tu commit: Cập nhật/Lưu sơ đồ la hanh dong nguoi dung.
 */

const SUPPORTED_CASE_TYPE = 'inheritance';
const MOCK_BANNER = 'Dữ liệu mô phỏng';
const DIAGRAM_VERSION = 2;

// Field whitelist theo contract §4.1/§4.2 — strip field la truoc khi gui.
const PERSON_FIELDS = ['ho_ten', 'gioi_tinh', 'ngay_sinh', 'ngay_chet',
  'so_giay_to', 'ngay_cap', 'noi_cap', 'dia_chi', 'place_of_origin'];
const ASSET_FIELDS = ['is_primary', 'so_serial', 'so_vao_so',
  'so_thua_dat', 'so_to_ban_do', 'dia_chi', 'loai_so',
  'hinh_thuc_su_dung', 'thoi_han', 'nguon_goc', 'ngay_cap', 'co_quan_cap'];
const NODE_BOOL_FIELDS = ['isLandOwner', 'willReceive', 'hidden', 'deleted'];

function clone(v) {
  return v === undefined ? undefined : JSON.parse(JSON.stringify(v));
}

function defaultUuid() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback cho moi truong thieu crypto (khong dung cho du lieu that).
  return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g,
    () => Math.floor(Math.random() * 16).toString(16));
}

function errObj(code, message, details) {
  return { code, message: message || code, retryable: false,
           next_action: null, details: details || null };
}

function isInfraError(code) {
  return /^engine_|^file_scope|^unsupported_contract/.test(code || '') ||
    code === 'engine_unavailable';
}

function newPersonRow(uuid, fields) {
  const row = { row_id: uuid(), entity_id: null };
  for (const f of PERSON_FIELDS) row[f] = null;
  for (const [k, v] of Object.entries(fields || {})) {
    if (PERSON_FIELDS.includes(k)) row[k] = v;
  }
  return row;
}

function newAssetRow(uuid, fields) {
  const row = { row_id: uuid(), entity_id: null, land_rows: [] };
  for (const f of ASSET_FIELDS) row[f] = null;
  row.is_primary = false;
  for (const [k, v] of Object.entries(fields || {})) {
    if (k === 'land_rows') {
      row.land_rows = Array.isArray(v) ? clone(v) : [];
    } else if (ASSET_FIELDS.includes(k)) {
      row[k] = v;
    }
  }
  return row;
}

function newNode(id) {
  return { id, personId: null, parentSlotIds: [], spouseSlotId: null,
           isLandOwner: false, willReceive: false,
           hidden: false, deleted: false };
}

function createModel(deps) {
  deps = deps || {};
  const client = deps.client;
  if (!client || typeof client.run !== 'function') {
    throw new Error('createModel can deps.client.run(command, payload)');
  }
  const uuid = deps.uuid || defaultUuid;
  const subs = new Set();

  const state = {
    // idle | loading | ready | locked | conflict | error | unavailable
    status: 'idle',
    caseId: null,
    backendMode: null,           // 'mock' → banner "Dữ liệu mô phỏng"
    caseInfo: null,              // {id, case_type, document_type, status...}
    unsupported: false,          // case_type ngoai 'inheritance'
    locked: false,
    stale: false,                // giu nhap sau conflict — server da doi
    revision: 0,
    capabilities: { intake: [], diagram: false, word_export: false },
    committed: { people: [], assets: [] },   // Stage da commit (nguon Pool)
    stage: { people: [], assets: [] },       // draft Stage (UI edit)
    stageDirty: false,
    fieldErrors: [],             // [{row_id, field, code, message}]
    diagram: { version: DIAGRAM_VERSION, nodes: [] },  // draft
    committedDiagram: { version: DIAGRAM_VERSION, nodes: [] },
    renderModel: null,           // output engine gan nhat (evaluate/save)
    diagramWarnings: [],
    diagramErrors: [],
    evaluatedRevision: null,
    conflict: null,              // {server_revision, command}
    error: null,                 // error object job-level gan nhat
    notice: null,                // thong bao ngan ("Đã cập nhật Stage")
    suggestions: [],             // intake results cho review
    intakeErrors: [],
    intakePartial: false,
    intakeBusy: false,
    wordOptions: null,
    wordResult: null,
    wordBusy: false,
    busy: null,                  // command dang chay (commit/evaluate/save)
  };

  function emit() {
    for (const cb of subs) {
      try { cb(state); } catch (e) { /* subscriber loi khong lam sap model */ }
    }
  }

  function subscribe(cb) {
    subs.add(cb);
    return () => subs.delete(cb);
  }

  function findNode(nodeId, fromCommitted) {
    const nodes = (fromCommitted ? state.committedDiagram : state.diagram)
      .nodes || [];
    return nodes.find((n) => n && n.id === nodeId && !n.deleted) || null;
  }

  function committedPersonIds() {
    return new Set(state.committed.people.map((p) => p.row_id));
  }

  function diagramPersonIds() {
    const ids = new Set();
    for (const n of state.diagram.nodes || []) {
      if (n && !n.deleted && n.personId) ids.add(n.personId);
    }
    return ids;
  }

  // Pool = Stage da commit − phan tu dang duoc gan tren draft Diagram
  // (drafting-tab §2). Assets: wire v1 khong co co che gan tai san len
  // diagram → moi tai san committed luon con trong Pool.
  function pool() {
    const assigned = diagramPersonIds();
    return {
      people: state.committed.people.filter((p) => !assigned.has(p.row_id)),
      assets: state.committed.assets.slice(),
    };
  }

  function applyWorkspace(data) {
    const c = data.case || {};
    state.caseId = c.id;
    state.caseInfo = clone(c);
    state.backendMode = data.backend_mode || 'real';
    state.revision = c.revision || 0;
    state.locked = !!c.locked;
    state.unsupported = c.case_type !== SUPPORTED_CASE_TYPE;
    state.capabilities = data.capabilities ||
      { intake: [], diagram: false, word_export: false };
    state.committed = clone(data.stage || { people: [], assets: [] });
    state.stage = clone(state.committed);
    const dg = data.diagram || {};
    state.diagram = clone(dg.state || { version: DIAGRAM_VERSION, nodes: [] });
    state.committedDiagram = clone(state.diagram);
    state.renderModel = dg.render_model || null;
    state.diagramWarnings = dg.warnings || [];
    state.stageDirty = false;
    state.diagramDirty = false;
    state.fieldErrors = [];
    state.diagramErrors = [];
    state.conflict = null;
    state.stale = false;
    state.error = null;
    state.status = state.locked ? 'locked' : 'ready';
  }

  function setLoadError(err) {
    state.error = err;
    state.status = isInfraError(err.code) ? 'unavailable' : 'error';
  }

  async function openCase(caseId) {
    state.status = 'loading';
    state.caseId = caseId;
    state.error = null;
    state.notice = null;
    emit();
    const r = await client.run('notary.workspace_get',
                               { case_id: caseId });
    if (!r.ok) {
      setLoadError(r.error || errObj('unknown'));
      emit();
      return r;
    }
    applyWorkspace(r.data || {});
    emit();
    return r;
  }

  function canWrite() {
    return (state.status === 'ready' || state.status === 'conflict') &&
      !state.locked && !state.unsupported;
  }

  // ---------- Stage draft ----------

  function touchStage() {
    state.stageDirty = true;
    emit();
  }

  function addPerson(fields) {
    const row = newPersonRow(uuid, fields);
    state.stage.people.push(row);
    touchStage();
    return row;
  }

  function addAsset(fields) {
    const row = newAssetRow(uuid, fields);
    // Tai san dau tien mac dinh la primary (contract: dung 1 primary).
    if (!state.stage.assets.length) row.is_primary = true;
    state.stage.assets.push(row);
    touchStage();
    return row;
  }

  function clearRowFieldError(rowId, field) {
    if (!state.fieldErrors.length) return;
    state.fieldErrors = state.fieldErrors.filter(
      (e) => !(e.row_id === rowId && (!field || e.field === field)));
  }

  function updatePersonField(rowId, field, value) {
    const row = state.stage.people.find((p) => p.row_id === rowId);
    if (!row || !PERSON_FIELDS.includes(field)) return;
    row[field] = value === '' ? null : value;
    clearRowFieldError(rowId, field);
    touchStage();
  }

  function updateAssetField(rowId, field, value) {
    const row = state.stage.assets.find((a) => a.row_id === rowId);
    if (!row) return;
    if (field === 'is_primary' && value === true) {
      // Dung 1 primary: bat cai nay thi tat cac dong khac (client-side
      // mirror cua rule primary_count — backend van la nguoi quyet).
      for (const a of state.stage.assets) a.is_primary = false;
      row.is_primary = true;
    } else if (ASSET_FIELDS.includes(field)) {
      row[field] = value === '' ? null : value;
    } else {
      return;
    }
    clearRowFieldError(rowId, field);
    touchStage();
  }

  function removeStageRow(rowId) {
    const before = state.stage.people.length + state.stage.assets.length;
    state.stage.people = state.stage.people.filter((p) => p.row_id !== rowId);
    state.stage.assets = state.stage.assets.filter((a) => a.row_id !== rowId);
    if (state.stage.people.length + state.stage.assets.length === before) {
      return;
    }
    // Mirror _prune_diagram phia backend: draft diagram bo tham chieu
    // toi dong vua xoa de save sau khong bi reference_outside_stage.
    for (const n of state.diagram.nodes || []) {
      if (n.personId === rowId) {
        n.personId = null;
        state.diagramDirty = true;
      }
    }
    state.fieldErrors = state.fieldErrors.filter((e) => e.row_id !== rowId);
    touchStage();
  }

  function fieldErrorsFor(rowId) {
    return state.fieldErrors.filter((e) => e.row_id === rowId);
  }

  function isStageEmpty() {
    return !state.stage.people.length && !state.stage.assets.length;
  }

  function applyWriteResult(r, command) {
    // Map loi ghi vao state; tra false neu la loi nghiep vu da xu ly.
    const err = r.error || errObj('unknown');
    if (err.code === 'workspace_conflict') {
      state.conflict = {
        server_revision: err.details && err.details.server_revision,
        command,
      };
      state.status = 'conflict';
      return false;
    }
    if (err.code === 'workspace_locked') {
      state.locked = true;
      if (state.caseInfo) state.caseInfo.locked = true;
      state.status = 'locked';
      state.error = err;
      return false;
    }
    state.error = err;
    return false;
  }

  async function commitStage() {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        state.locked ? 'Hồ sơ đã khóa — chỉ đọc'
                     : 'Loại việc chưa hỗ trợ') };
    }
    if (!state.stageDirty) return { ok: true, noop: true };
    state.busy = 'notary.workspace_commit_stage';
    emit();
    const r = await client.run('notary.workspace_commit_stage', {
      case_id: state.caseId,
      base_revision: state.revision,
      stage: clone(state.stage),
    });
    state.busy = null;
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'stage_validation_error') {
        state.fieldErrors =
          (err.details && err.details.field_errors) || [];
        emit();
        return r;
      }
      applyWriteResult(r, 'workspace_commit_stage');
      emit();
      return r;
    }
    const d = r.data || {};
    state.revision = d.revision;
    state.committed = clone(d.stage || state.stage);
    state.stage = clone(state.committed);
    if (d.diagram) {
      // Commit prune + re-evaluate trong transaction (§6.1): draft
      // diagram nap lai theo state server da prune, khong con dirty.
      state.diagram = clone(d.diagram.state || state.diagram);
      state.committedDiagram = clone(state.diagram);
      state.renderModel = d.diagram.render_model || state.renderModel;
      state.diagramDirty = false;
    }
    state.stageDirty = false;
    state.fieldErrors = [];
    state.stale = false;
    state.notice = 'Đã cập nhật Stage';
    emit();
    return r;
  }

  // ---------- Diagram draft ----------

  function touchDiagram() {
    state.diagramDirty = true;
    emit();
  }

  function addSlot(id) {
    const nodes = state.diagram.nodes || (state.diagram.nodes = []);
    let nid = id;
    if (!nid) {
      let i = nodes.length + 1;
      while (findNode(`slot_${i}`)) i += 1;
      nid = `slot_${i}`;
    }
    const node = newNode(nid);
    nodes.push(node);
    touchDiagram();
    return node;
  }

  // Gan nguoi (row_id trong Stage DA COMMIT) vao slot; rowId=null → bo gan,
  // nguoi quay ve Pool. Mot nguoi chi nam tren mot node — gan moi se clear
  // node cu (tranh engine duplicate_person).
  function assignPerson(nodeId, rowId) {
    const node = findNode(nodeId);
    if (!node) return false;
    if (rowId !== null && !committedPersonIds().has(rowId)) return false;
    if (rowId) {
      for (const n of state.diagram.nodes) {
        if (n !== node && !n.deleted && n.personId === rowId) {
          n.personId = null;
        }
      }
    }
    node.personId = rowId;
    touchDiagram();
    return true;
  }

  function setNodeFlag(nodeId, flag, value) {
    if (!NODE_BOOL_FIELDS.includes(flag) || flag === 'deleted') return false;
    const node = findNode(nodeId);
    if (!node) return false;
    node[flag] = !!value;
    touchDiagram();
    return true;
  }

  function setNodeRelation(nodeId, rel) {
    const node = findNode(nodeId);
    if (!node) return false;
    if (rel.parentSlotIds !== undefined) {
      node.parentSlotIds = Array.isArray(rel.parentSlotIds)
        ? rel.parentSlotIds.filter((x) => typeof x === 'string' && x)
          .slice(0, 2) : [];
    }
    if (rel.spouseSlotId !== undefined) {
      node.spouseSlotId = rel.spouseSlotId || null;
    }
    touchDiagram();
    return true;
  }

  function removeNode(nodeId) {
    const node = findNode(nodeId);
    if (!node) return false;
    node.deleted = true;             // engine bo qua node deleted (§7.1)
    // Xoa tham chieu slot cua node nay khoi cac node khac de tranh
    // dangling_parent/dangling_spouse khi save.
    for (const n of state.diagram.nodes) {
      if (!n || n.deleted) continue;
      if (Array.isArray(n.parentSlotIds)) {
        n.parentSlotIds = n.parentSlotIds.filter((p) => p !== nodeId);
      }
      if (n.spouseSlotId === nodeId) n.spouseSlotId = null;
    }
    touchDiagram();
    return true;
  }

  async function evaluateDiagram() {
    // Read-only theo DB — duoc phep tren case locked (contract §7.4).
    if (state.unsupported) {
      return { ok: false, error: errObj('case_type_unsupported',
                                        'Loại việc chưa hỗ trợ') };
    }
    state.busy = 'notary.diagram_evaluate';
    emit();
    const r = await client.run('notary.diagram_evaluate', {
      case_id: state.caseId,
      diagram: { state: clone(state.diagram) },
    });
    state.busy = null;
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'diagram_invalid_state') {
        state.diagramErrors =
          (err.details && err.details.errors) || [err];
      } else {
        state.error = err;
      }
      emit();
      return r;
    }
    state.renderModel = r.data.render_model || null;
    state.evaluatedRevision = r.data.evaluated_revision;
    state.diagramErrors = [];
    emit();
    return r;
  }

  async function saveDiagram() {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        state.locked ? 'Hồ sơ đã khóa — chỉ đọc'
                     : 'Loại việc chưa hỗ trợ') };
    }
    if (!state.diagramDirty) return { ok: true, noop: true };
    state.busy = 'notary.diagram_save';
    emit();
    const r = await client.run('notary.diagram_save', {
      case_id: state.caseId,
      base_revision: state.revision,
      diagram: { state: clone(state.diagram) },
    });
    state.busy = null;
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'diagram_invalid_state') {
        state.diagramErrors =
          (err.details && err.details.errors) || [err];
        emit();
        return r;
      }
      applyWriteResult(r, 'diagram_save');
      emit();
      return r;
    }
    const d = r.data || {};
    state.revision = d.revision;
    if (d.diagram) {
      state.diagram = clone(d.diagram.state || state.diagram);
      state.committedDiagram = clone(state.diagram);
      state.renderModel = d.diagram.render_model || state.renderModel;
    }
    state.diagramDirty = false;
    state.diagramErrors = [];
    state.stale = false;
    state.notice = 'Đã lưu sơ đồ';
    emit();
    return r;
  }

  // ---------- conflict ----------

  // mode: 'reload' = tai ban moi tu server (mat nhap);
  //       'keep'   = giu nhap de sao chep — KHONG co ghi de cuong buc.
  async function resolveConflict(mode) {
    if (mode === 'reload') {
      return openCase(state.caseId);
    }
    state.conflict = null;
    state.status = state.locked ? 'locked' : 'ready';
    state.stale = true;
    emit();
    return { ok: true };
  }

  // ---------- intake (thin — UI review o MIN-112) ----------

  async function intakeAnalyze(sources) {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        'Không thể nhập dữ liệu ở trạng thái hiện tại') };
    }
    state.intakeBusy = true;
    emit();
    const r = await client.run('notary.intake_analyze', {
      case_id: state.caseId,
      sources: clone(sources),
    });
    state.intakeBusy = false;
    if (!r.ok) {
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    const d = r.data || {};
    // Ket qua moi them len tren, khong xoa ngam suggestion cu (plan §13).
    state.suggestions = state.suggestions.concat(d.suggestions || []);
    state.intakeErrors = d.errors || [];
    state.intakePartial = !!r.partial;
    emit();
    return r;
  }

  // Dua suggestion vao Stage nhu draft — khong phai commit (§5).
  function acceptSuggestion(suggestionId) {
    const i = state.suggestions.findIndex(
      (s) => s.suggestion_id === suggestionId);
    if (i < 0) return null;
    const sug = state.suggestions[i];
    const fields = {};
    for (const [k, f] of Object.entries(sug.fields || {})) {
      fields[k] = f && f.normalized_value != null
        ? f.normalized_value : (f && f.raw_value != null ? f.raw_value : null);
    }
    const row = sug.target === 'asset'
      ? addAsset(fields) : addPerson(fields);
    state.suggestions.splice(i, 1);
    emit();
    return row;
  }

  function discardSuggestion(suggestionId) {
    const i = state.suggestions.findIndex(
      (s) => s.suggestion_id === suggestionId);
    if (i < 0) return;
    state.suggestions.splice(i, 1);
    emit();
  }

  // ---------- word export (thin — dialog day du o MIN-112) ----------

  async function loadWordOptions() {
    const r = await client.run('notary.word_export_options',
                               { case_id: state.caseId });
    if (!r.ok) {
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    state.wordOptions = (r.data && r.data.documents) || [];
    emit();
    return r;
  }

  async function exportWord(documentKeys, destination) {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        'Không thể xuất ở trạng thái hiện tại') };
    }
    state.wordBusy = true;
    state.wordResult = null;
    emit();
    const r = await client.run('notary.word_export_batch', {
      case_id: state.caseId,
      document_keys: documentKeys,
      destination,
    });
    state.wordBusy = false;
    if (!r.ok) {
      // failed job van co the mang result (breakdown) tren wire.
      state.wordResult = (r.job && r.job.result && r.job.result.data) ||
        (r.error && r.error.details && r.error.details.documents
          ? { documents: r.error.details.documents } : null);
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    state.wordResult = r.data || null;
    emit();
    return r;
  }

  // ---------- derived helpers ----------

  function mockBanner() {
    return state.backendMode === 'mock' ? MOCK_BANNER : null;
  }

  function hasUnsaved() {
    return state.stageDirty || state.diagramDirty;
  }

  function dismissNotice() {
    state.notice = null;
    state.error = null;
    emit();
  }

  return {
    state, subscribe,
    openCase, canWrite, mockBanner, hasUnsaved, isStageEmpty,
    addPerson, addAsset, updatePersonField, updateAssetField,
    removeStageRow, fieldErrorsFor, commitStage,
    pool,
    addSlot, assignPerson, setNodeFlag, setNodeRelation, removeNode,
    evaluateDiagram, saveDiagram,
    resolveConflict,
    intakeAnalyze, acceptSuggestion, discardSuggestion,
    loadWordOptions, exportWord,
    dismissNotice,
  };
}

const G1_NOTARY_MODEL = {
  createModel,
  SUPPORTED_CASE_TYPE,
  MOCK_BANNER,
  PERSON_FIELDS,
  ASSET_FIELDS,
};

if (typeof window !== 'undefined') window.G1_NOTARY_MODEL = G1_NOTARY_MODEL;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_MODEL;
}
