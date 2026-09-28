'use strict';

/* Case-drafting model — state machine thuan cho tab Soạn hồ sơ (MIN-111).
 *
 * SOT hanh vi: notary_v2/docs/platform/case-workspace/drafting-tab.md
 * Wire shape: contracts/notary-case-drafting.md §13 (notary.case-drafting.v2).
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

const CASE_TYPE_INHERITANCE = 'inheritance';
const CASE_TYPE_TWO_PARTY = 'two_party';
const CASE_TYPES = [CASE_TYPE_INHERITANCE, CASE_TYPE_TWO_PARTY];
const MOCK_BANNER = 'Dữ liệu mô phỏng';
const DIAGRAM_VERSION = 3;
const MAX_ASSETS = 3;
const MAX_PEOPLE_TWO_PARTY = 30;
const POSITIONS = [1, 2, 3];
const TWO_PARTY_IDS = Array.from({ length: 30 }, (_, i) => `p${i + 1}`);

// Field whitelist theo contract §13.3/§13.4 — strip field la truoc khi
// gui. is_primary/isLandOwner/willReceive BI CAM tren wire v2.
const PERSON_FIELDS = ['ho_ten', 'gioi_tinh', 'ngay_sinh', 'ngay_chet',
  'so_giay_to', 'ngay_cap', 'noi_cap', 'dia_chi', 'place_of_origin'];
const ASSET_FIELDS = ['so_serial', 'so_vao_so',
  'so_thua_dat', 'so_to_ban_do', 'dia_chi', 'loai_so',
  'hinh_thuc_su_dung', 'thoi_han', 'nguon_goc', 'ngay_cap', 'co_quan_cap'];
const NODE_BOOL_FIELDS = ['hidden', 'deleted'];
const NODE_POSITION_FIELDS = ['ownPositions', 'receivePositions'];

// Meta cho phep sua tren nhap moi — khop payload.case §13.6.
const CASE_META_FIELDS = ['case_type', 'document_type', 'ngay_lap_ho_so',
                          'noi_niem_yet', 'ghi_chu'];
const CASE_DOCUMENT_TYPES = ['khai_nhan', 'thoa_thuan'];
const CASE_DOCUMENT_TYPES_TWO_PARTY =
  ['chuyen_nhuong', 'tang_cho', 'cho_thue', 'dat_coc'];

function documentTypesFor(caseType) {
  return caseType === CASE_TYPE_TWO_PARTY
    ? CASE_DOCUMENT_TYPES_TWO_PARTY : CASE_DOCUMENT_TYPES;
}

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
           ownPositions: [], receivePositions: [],
           hidden: false, deleted: false };
}

function newTwoPartyNode(id) {
  return { id, personId: null, hidden: false, deleted: false };
}

// State two_party canonical — dung 30 slot p1..p30, khong compact.
function newTwoPartyState() {
  return { version: DIAGRAM_VERSION, domain: CASE_TYPE_TWO_PARTY,
           nodes: TWO_PARTY_IDS.map((id) => newTwoPartyNode(id)) };
}

// Seed V2 toi thieu port tu ReactFlowApp.jsx (drafting-tab/MIN-122):
// bay slot co dinh — cha/me nguoi de lai, cha/me vo-chong, owner, spouse,
// child_1. KHONG port resolveSubRelations/engine JS/heuristic ngay chet.
// Idempotent: chi them slot chua co (ke ca deleted = khong them lai).
function seedDiagramSlots(nodes) {
  const have = new Set((nodes || []).map((n) => n && n.id));
  const add = (id, rel) => {
    if (have.has(id)) return null;
    const n = newNode(id);
    if (rel) {
      n.parentSlotIds = rel.parents || [];
      n.spouseSlotId = rel.spouse || null;
    }
    nodes.push(n);
    have.add(id);
    return n;
  };
  add('father'); add('mother');
  add('spouse_father'); add('spouse_mother');
  const owner = findInNodes(nodes, 'owner') || add('owner');
  const spouse = findInNodes(nodes, 'spouse') || add('spouse');
  add('child_1', { parents: ['owner', 'spouse'] });
  if (owner) {
    owner.spouseSlotId = 'spouse';
    owner.parentSlotIds = ['father', 'mother'].filter(
      (x) => have.has(x));
  }
  if (spouse) {
    spouse.spouseSlotId = 'owner';
    spouse.parentSlotIds = ['spouse_father', 'spouse_mother'].filter(
      (x) => have.has(x));
  }
  return nodes;
}

function findInNodes(nodes, id) {
  return (nodes || []).find((n) => n && n.id === id && !n.deleted) || null;
}

// Them mot slot child_N trong ke tiep khi moi child_* da gan nguoi —
// giu "luon co mot o con trống" (MIN-122). Tra node moi hoac null.
function ensureEmptyChildSlot(nodes) {
  const kids = (nodes || []).filter(
    (n) => n && !n.deleted && /^child_\d+$/.test(n.id));
  if (kids.some((n) => !n.personId)) return null;
  let i = 1;
  const ids = new Set((nodes || []).map((n) => n && n.id));
  while (ids.has(`child_${i}`)) i += 1;
  const node = newNode(`child_${i}`);
  node.parentSlotIds = ['owner', 'spouse'].filter(
    (x) => findInNodes(nodes, x));
  nodes.push(node);
  return node;
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
    diagramDirty: false,
    metaDirty: false,            // meta nhap chua luu (chi co tren nhap)
    draftId: null,               // idempotency_key cua phien nhap (uuid4)
    fieldErrors: [],             // [{row_id, field, code, message}]
    diagram: { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
               nodes: [] },                     // draft
    committedDiagram: { version: DIAGRAM_VERSION,
                        domain: CASE_TYPE_INHERITANCE, nodes: [] },
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

  let lastUnsaved = false;
  // Session guard: openCase/newDraft tang counter; response tro ve sau
  // khi session da doi (user chuyen case/nhap khac) bi BO — khong ap
  // vao state nua (MIN-122: "bo job response ve tre cua case cu").
  let session = 0;

  function emit() {
    // Bao main biet hasUnsaved doi → window-close guard (MIN-112). Tinh o
    // day vi moi thay doi draft deu di qua emit (touchStage/touchDiagram/
    // commit/save/applyWorkspace).
    const u = state.stageDirty || state.diagramDirty || state.metaDirty;
    if (u !== lastUnsaved) {
      lastUnsaved = u;
      if (typeof deps.onUnsavedChange === 'function') {
        try {
          const p = deps.onUnsavedChange(u);
          // Bridge co the tra promise (IPC invoke) — nuot rejection de
          // khong lam sap emit/unhandled rejection.
          if (p && typeof p.catch === 'function') p.catch(() => {});
        } catch (e) { /* bridge loi */ }
      }
    }
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

  // Che do nhap (caseId=null): diagram gan personId theo row_id cua
  // stage NHAP — chua co gi committed. Case da tao: van theo committed
  // (§2.1a — personId trong persisted state la row_id cua Stage).
  function assignablePersonIds() {
    return state.caseId == null
      ? new Set(state.stage.people.map((p) => p.row_id))
      : committedPersonIds();
  }

  function diagramPersonIds() {
    const ids = new Set();
    for (const n of state.diagram.nodes || []) {
      if (n && !n.deleted && n.personId) ids.add(n.personId);
    }
    return ids;
  }

  // Pool = Stage da commit − phan tu dang duoc gan tren draft Diagram
  // (drafting-tab §2). Assets khong gan vao node — diagram chi tham
  // chieu tai san qua ownPositions/receivePositions (vi tri 1..3) →
  // moi tai san committed luon con trong Pool.
  function pool() {
    const assigned = diagramPersonIds();
    const src = state.caseId == null ? state.stage : state.committed;
    return {
      people: src.people.filter((p) => !assigned.has(p.row_id)),
      assets: src.assets.slice(),
    };
  }

  function applyWorkspace(data) {
    const c = data.case || {};
    state.caseId = c.id;
    state.caseInfo = clone(c);
    state.backendMode = data.backend_mode || 'real';
    state.revision = c.revision || 0;
    state.locked = !!c.locked;
    state.unsupported = !CASE_TYPES.includes(c.case_type);
    state.capabilities = data.capabilities ||
      { intake: [], diagram: false, word_export: false };
    state.committed = clone(data.stage || { people: [], assets: [] });
    state.stage = clone(state.committed);
    const dg = data.diagram || {};
    state.diagram = clone(dg.state ||
      (c.case_type === CASE_TYPE_TWO_PARTY
        ? newTwoPartyState()
        : { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
            nodes: [] }));
    state.committedDiagram = clone(state.diagram);
    state.renderModel = dg.render_model || null;
    // dg.warnings = warning compose stage (list[string], real backend);
    // render_model.warnings = warning engine [{code,message}] — gop ca
    // hai de canh bao pool/serial hien ngay khi mo, khong doi evaluate.
    state.diagramWarnings = (dg.warnings || [])
      .concat((dg.render_model && dg.render_model.warnings) || []);
    state.stageDirty = false;
    state.diagramDirty = false;
    state.metaDirty = false;
    state.draftId = null;
    state.fieldErrors = [];
    state.diagramErrors = [];
    state.conflict = null;
    state.stale = false;
    state.error = null;
    // Aux state la per-case — reset het khi mo case khac, tranh leak
    // suggestion/word result/notice cua case truoc sang case moi.
    state.notice = null;
    state.suggestions = [];
    state.intakeErrors = [];
    state.intakePartial = false;
    state.intakeBusy = false;
    state.wordOptions = null;
    state.wordResult = null;
    state.wordBusy = false;
    state.evaluatedRevision = null;
    state.busy = null;
    state.status = state.locked ? 'locked' : 'ready';
  }

  function setLoadError(err) {
    state.error = err;
    state.status = isInfraError(err.code) ? 'unavailable' : 'error';
  }

  async function openCase(caseId) {
    const s = ++session;
    state.status = 'loading';
    state.caseId = caseId;
    state.draftId = null;
    state.error = null;
    state.notice = null;
    emit();
    const r = await client.run('notary.workspace_get',
                               { case_id: caseId });
    if (s !== session) return r;      // user da chuyen case/nhap — bo
    if (!r.ok) {
      setLoadError(r.error || errObj('unknown'));
      emit();
      return r;
    }
    applyWorkspace(r.data || {});
    emit();
    return r;
  }

  // ---------- nhap moi (case chua ton tai) ----------

  function isDraft() {
    return state.caseId == null &&
      (state.status === 'ready' || state.status === 'conflict');
  }

  // Stage/diagram draft theo loai ho so (§13.1): inheritance mang
  // owner_row_id (BẮT BUỘC) + seed 7 slot; two_party khong co owner_row_id,
  // diagram la 30 slot canonical p1..p30.
  function newStageDraft(caseType) {
    return caseType === CASE_TYPE_TWO_PARTY
      ? { people: [], assets: [] }
      : { owner_row_id: null, people: [], assets: [] };
  }

  function newDiagramDraft(caseType) {
    return caseType === CASE_TYPE_TWO_PARTY
      ? newTwoPartyState()
      : { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
          nodes: seedDiagramSlots([]) };
  }

  // Mo nhap trong — stage rong + diagram seed theo caseType. draftId =
  // idempotency_key cua phien: retry saveDraft dung lai → khong tao
  // trung (contract §13.6). newDraft lai → key moi = nhap khac.
  function newDraft(caseType) {
    const ct = CASE_TYPES.includes(caseType)
      ? caseType : CASE_TYPE_INHERITANCE;
    ++session;                        // vo hieu response dang cho cua case cu
    state.status = 'ready';
    state.caseId = null;
    state.draftId = uuid();
    state.caseInfo = {
      id: null, case_type: ct,
      document_type: documentTypesFor(ct)[0],
      status: 'draft', locked: false, revision: 0,
      ngay_lap_ho_so: null, noi_niem_yet: null, ghi_chu: null,
    };
    state.backendMode = null;
    state.revision = 0;
    state.locked = false;
    state.unsupported = false;
    state.capabilities =
      { intake: [], diagram: true, word_export: false };
    state.committed = { people: [], assets: [] };
    state.stage = newStageDraft(ct);
    state.stageDirty = false;
    state.diagramDirty = true;        // seed la draft chua persist
    state.metaDirty = false;
    state.diagram = newDiagramDraft(ct);
    state.committedDiagram = clone(state.diagram);
    state.renderModel = null;
    state.diagramWarnings = [];
    state.diagramErrors = [];
    state.evaluatedRevision = null;
    state.conflict = null;
    state.stale = false;
    state.fieldErrors = [];
    state.error = null;
    state.notice = null;
    state.suggestions = [];
    state.intakeErrors = [];
    state.intakePartial = false;
    state.intakeBusy = false;
    state.wordOptions = null;
    state.wordResult = null;
    state.wordBusy = false;
    state.busy = null;
    emit();
  }

  // Sua meta nhap (document_type/ngay_lap_ho_so/noi_niem_yet/ghi_chu).
  // Chi co nghia tren nhap chua luu — case da tao sua qua commit Stage
  // khong doi meta (contract khong co command update meta).
  function updateCaseMeta(field, value) {
    if (!isDraft() || !CASE_META_FIELDS.includes(field)) return false;
    if (field === 'case_type') {
      // Doi loai ho so o nhap = reset diagram buffer theo domain moi
      // (contract §13.5); stage moc owner_row_id doi theo loai.
      if (!CASE_TYPES.includes(value)) return false;
      if (state.caseInfo.case_type === value) return true;
      state.caseInfo.case_type = value;
      const docs = documentTypesFor(value);
      if (!docs.includes(state.caseInfo.document_type)) {
        state.caseInfo.document_type = docs[0];
      }
      if (value === CASE_TYPE_TWO_PARTY) {
        delete state.stage.owner_row_id;
      } else if (!('owner_row_id' in state.stage)) {
        state.stage.owner_row_id = null;
      }
      state.diagram = newDiagramDraft(value);
      state.committedDiagram = clone(state.diagram);
      state.diagramDirty = true;
      state.diagramErrors = [];
      state.metaDirty = true;
      state.stageDirty = true;
      emit();
      return true;
    }
    if (field === 'document_type' &&
        !documentTypesFor(state.caseInfo.case_type).includes(value)) {
      return false;
    }
    const v = value === '' ? null : value;
    if ((state.caseInfo[field] ?? null) === v) return true;
    state.caseInfo[field] = v;
    state.metaDirty = true;
    emit();
    return true;
  }

  async function saveDraft() {
    if (!isDraft()) {
      return { ok: false, error: errObj('validation_error',
                                        'Khong phai nhap moi') };
    }
    state.busy = 'notary.workspace_create';
    emit();
    const s = session;
    const meta = {};
    for (const f of CASE_META_FIELDS) meta[f] = state.caseInfo[f] ?? null;
    const r = await client.run('notary.workspace_create', {
      idempotency_key: state.draftId,
      case: meta,
      stage: clone(state.stage),
      diagram: { state: clone(state.diagram) },
    });
    state.busy = null;
    if (s !== session) return r;      // nhap da bi thay — bo response
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'stage_validation_error') {
        state.fieldErrors =
          (err.details && err.details.field_errors) || [];
      } else if (err.code === 'diagram_invalid_state') {
        state.diagramErrors =
          (err.details && err.details.errors) || [err];
      }
      state.error = err;
      emit();
      return r;
    }
    // thanh cong → nhap tro thanh case that (revision=1); draftId giai
    // phong qua applyWorkspace — retry tiep theo dung luong revision.
    applyWorkspace(r.data || {});
    state.notice = r.data && r.data.created === false
      ? 'Hồ sơ đã tồn tại (đã mở lại)' : 'Đã lưu hồ sơ';
    emit();
    return r;
  }

  function canWrite() {
    return (state.status === 'ready' || state.status === 'conflict') &&
      !state.locked && !state.unsupported;
  }

  // ---------- Stage draft ----------

  // Defense-in-depth: case locked/unsupported khong bao gio mutate draft,
  // ke ca khi view lo de nut write chay (rule drafting-tab §4).
  function touchStage() {
    state.stageDirty = true;
    emit();
  }

  // Loai ho so hien tai cua nhap/case (stage draft hay caseInfo).
  function caseType() {
    return (state.caseInfo && state.caseInfo.case_type) ||
      CASE_TYPE_INHERITANCE;
  }

  function diagramDomain() {
    return (state.diagram && state.diagram.domain) || caseType();
  }

  function addPerson(fields) {
    if (!canWrite()) return null;
    // two_party: toi da 30 nguoi (stage.people → slot p1..p30).
    if (caseType() === CASE_TYPE_TWO_PARTY &&
        state.stage.people.length >= MAX_PEOPLE_TWO_PARTY) {
      return null;
    }
    const row = newPersonRow(uuid, fields);
    state.stage.people.push(row);
    touchStage();
    return row;
  }

  function addAsset(fields) {
    if (!canWrite()) return null;
    // Toi da 3 asset; vi tri = index+1 trong mang (contract §13.3).
    if (state.stage.assets.length >= MAX_ASSETS) return null;
    const row = newAssetRow(uuid, fields);
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
    if (!canWrite()) return;
    const row = state.stage.people.find((p) => p.row_id === rowId);
    if (!row || !PERSON_FIELDS.includes(field)) return;
    row[field] = value === '' ? null : value;
    clearRowFieldError(rowId, field);
    touchStage();
  }

  function updateAssetField(rowId, field, value) {
    if (!canWrite()) return;
    const row = state.stage.assets.find((a) => a.row_id === rowId);
    if (!row) return;
    if (field === 'land_rows') {
      // Form dọc: land_rows la list {loai_dat, dien_tich, thoi_han}.
      row.land_rows = Array.isArray(value)
        ? value.map((x) => ({
            loai_dat: x && x.loai_dat != null ? String(x.loai_dat) : null,
            dien_tich: x && x.dien_tich != null ? x.dien_tich : null,
            thoi_han: x && x.thoi_han != null ? String(x.thoi_han) : null,
          })) : [];
    } else if (ASSET_FIELDS.includes(field)) {
      row[field] = value === '' ? null : value;
    } else {
      return;
    }
    clearRowFieldError(rowId, field);
    touchStage();
  }

  // Doi thu tu asset = doi nghia vi tri (contract §13.3): row_id di
  // theo dong; dau chon ownPositions/receivePositions KHONG tu chuyen
  // theo — server giu so vi tri nguyen, prune vi tri > len(assets).
  function moveAsset(rowId, toIndex) {
    if (!canWrite()) return false;
    const i = state.stage.assets.findIndex((a) => a.row_id === rowId);
    if (i < 0) return false;
    const j = Math.max(0, Math.min(toIndex | 0, state.stage.assets.length - 1));
    if (i === j) return true;
    const [row] = state.stage.assets.splice(i, 1);
    state.stage.assets.splice(j, 0, row);
    clearRowFieldError(rowId);
    touchStage();
    return true;
  }

  // Owner cua case inheritance = stage.owner_row_id (contract §13.1).
  // Node 'owner' tren draft diagram chi mirror — server sync luc
  // commit/save; client cap nhat mirror de render dung ngay.
  function setOwnerRow(rowId) {
    if (!canWrite()) return false;
    if (caseType() !== CASE_TYPE_INHERITANCE) return false;
    if (rowId !== null &&
        !state.stage.people.some((p) => p.row_id === rowId)) {
      return false;
    }
    if (state.stage.owner_row_id === rowId) return true;
    state.stage.owner_row_id = rowId;
    const owner = findInNodes(state.diagram.nodes, 'owner');
    if (owner) {
      owner.personId = rowId;
      state.diagramDirty = true;
    }
    touchStage();
    return true;
  }

  function removeStageRow(rowId) {
    if (!canWrite()) return;
    const before = state.stage.people.length + state.stage.assets.length;
    state.stage.people = state.stage.people.filter((p) => p.row_id !== rowId);
    state.stage.assets = state.stage.assets.filter((a) => a.row_id !== rowId);
    if (state.stage.people.length + state.stage.assets.length === before) {
      return;
    }
    // Xoa dong owner → pointer ve null (draft cho phep; commit se bat
    // workspace_owner_required neu chua chon lai truoc khi Cap nhat).
    if (state.stage.owner_row_id === rowId) {
      state.stage.owner_row_id = null;
      const owner = findInNodes(state.diagram.nodes, 'owner');
      if (owner) owner.personId = null;
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
    const s = session;
    const r = await client.run('notary.workspace_commit_stage', {
      case_id: state.caseId,
      base_revision: state.revision,
      stage: clone(state.stage),
    });
    state.busy = null;
    if (s !== session) return r;
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
      // Commit prune + re-evaluate trong transaction (§6.1). Baseline
      // committed luon nap theo state server da prune.
      state.committedDiagram = clone(d.diagram.state ||
                                     state.committedDiagram);
      if (state.diagramDirty) {
        // Draft diagram co thay doi chua luu — KHONG thay bang ban
        // server (mat assignment chua persist). Mirror _prune_diagram
        // phia client: bo gan personId khong con trong stage committed
        // moi (giong removeStageRow), giu nguyen cac assignment khac.
        const ids = new Set(state.committed.people.map((p) => p.row_id));
        for (const n of state.diagram.nodes || []) {
          if (n && n.personId && !ids.has(n.personId)) {
            n.personId = null;
          }
        }
        // diagramDirty giu true — user van phai "Lưu sơ đồ" de persist;
        // evaluatedRevision giu nguyen de badge "Stage đã đổi kể từ lần
        // đánh giá" bao khi rm hien thi chua mo ta draft hien tai.
      } else {
        state.diagram = clone(d.diagram.state || state.diagram);
        // rm tu commit duoc evaluate tren stage@revision moi — danh dau
        // de badge khong bao "stale" sai.
        state.evaluatedRevision = d.revision;
      }
      state.renderModel = d.diagram.render_model || state.renderModel;
      state.diagramWarnings =
        (d.diagram.render_model && d.diagram.render_model.warnings) || [];
    }
    state.stageDirty = false;
    state.fieldErrors = [];
    state.stale = false;
    state.error = null;            // ghi thanh cong → loi cu khong con dung
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
    if (!canWrite()) return null;
    // two_party: 30 slot canonical co dinh — khong them slot tuy y.
    if (diagramDomain() === CASE_TYPE_TWO_PARTY) return null;
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

  // Mac dinh khi gan (contract §13.4 Q5 — tien ich client): node owner
  // → ownPositions = moi vi tri dang co; slot thua ke khac →
  // receivePositions = moi vi tri dang co. Chi ap khi mang dang rong
  // (khong ghi de lua chon user); wire luon mang mang explicit.
  function applyAssignDefaults(node) {
    if (!node || diagramDomain() !== CASE_TYPE_INHERITANCE) return;
    if (!node.personId) return;
    const all = state.stage.assets.map((_, i) => i + 1);
    if (node.id === 'owner') {
      if (!node.ownPositions || !node.ownPositions.length) {
        node.ownPositions = all.slice();
      }
    } else if (!node.receivePositions || !node.receivePositions.length) {
      node.receivePositions = all.slice();
    }
  }

  // Gan nguoi (row_id trong Stage DA COMMIT) vao slot; rowId=null → bo gan,
  // nguoi quay ve Pool. Mot nguoi chi nam tren mot node — gan moi se clear
  // node cu (tranh engine duplicate_person).
  function assignPerson(nodeId, rowId) {
    if (!canWrite()) return false;
    const node = findNode(nodeId);
    if (!node) return false;
    // Node 'owner' la mirror cua stage.owner_row_id — gan qua setter de
    // pointer stage cap nhat cung (contract §13.4).
    if (diagramDomain() === CASE_TYPE_INHERITANCE &&
        nodeId === 'owner') {
      if (!setOwnerRow(rowId)) return false;
      // Mot nguoi chi nam tren mot node — rowId dang o node khac thi
      // clear truoc (tranh duplicate_person nhu nhanh generic).
      if (rowId) {
        for (const n of state.diagram.nodes) {
          if (n.id !== 'owner' && !n.deleted && n.personId === rowId) {
            n.personId = null;
          }
        }
      }
      applyAssignDefaults(findInNodes(state.diagram.nodes, 'owner'));
      touchDiagram();
      return true;
    }
    if (rowId !== null && !assignablePersonIds().has(rowId)) return false;
    if (rowId) {
      for (const n of state.diagram.nodes) {
        if (n !== node && !n.deleted && n.personId === rowId) {
          n.personId = null;
        }
      }
    }
    node.personId = rowId;
    applyAssignDefaults(node);
    if (diagramDomain() !== CASE_TYPE_TWO_PARTY) {
      ensureEmptyChildSlot(state.diagram.nodes);
    }
    touchDiagram();
    return true;
  }

  // movePerson(rowId, targetNodeId|null) — nen MIN-119 drag/drop:
  //   target node trong  → move (nguon ve Pool)
  //   target co nguoi    → swap personId hai node
  //   target = null      → bo gan, nguoi quay ve Pool
  // rowId tu Pool (chua gan node nao) cung move duoc — tuong duong
  // assignPerson nhung swap nguoi cu cua target ve Pool.
  function movePerson(rowId, targetNodeId) {
    if (!canWrite()) return false;
    if (rowId == null) return false;
    const sourceNode = (state.diagram.nodes || []).find(
      (n) => n && !n.deleted && n.personId === rowId) || null;
    if (targetNodeId == null) {
      if (!sourceNode) return false;      // da o Pool roi
      if (diagramDomain() === CASE_TYPE_INHERITANCE &&
          sourceNode.id === 'owner') {
        return setOwnerRow(null);
      }
      sourceNode.personId = null;
      if (diagramDomain() !== CASE_TYPE_TWO_PARTY) {
        ensureEmptyChildSlot(state.diagram.nodes);
      }
      touchDiagram();
      return true;
    }
    const target = findNode(targetNodeId);
    if (!target || target === sourceNode) return false;
    // Tha len slot 'owner' = chon owner moi — qua setOwnerRow de
    // pointer stage theo cung; owner cu ve Pool (Q9 swap).
    if (diagramDomain() === CASE_TYPE_INHERITANCE &&
        target.id === 'owner') {
      if (!setOwnerRow(rowId)) return false;
      if (sourceNode) sourceNode.personId = null;
      applyAssignDefaults(findInNodes(state.diagram.nodes, 'owner'));
      ensureEmptyChildSlot(state.diagram.nodes);
      touchDiagram();
      return true;
    }
    if (!assignablePersonIds().has(rowId)) return false;
    const displaced = target.personId;
    target.personId = rowId;
    if (sourceNode) {
      if (diagramDomain() === CASE_TYPE_INHERITANCE &&
          sourceNode.id === 'owner') {
        // Swap owner ra khoi slot owner = doi owner_row_id sang nguoi
        // bi choan cho (hoac null) — mirror luon theo pointer stage.
        setOwnerRow(displaced || null);
      } else {
        sourceNode.personId = displaced || null;   // swap (null = move)
      }
    }                                   // displaced khong co sourceNode
                                        // → tu nhien ve Pool
    applyAssignDefaults(target);
    if (diagramDomain() !== CASE_TYPE_TWO_PARTY) {
      ensureEmptyChildSlot(state.diagram.nodes);
    }
    touchDiagram();
    return true;
  }

  function setNodeFlag(nodeId, flag, value) {
    if (!canWrite()) return false;
    if (!NODE_BOOL_FIELDS.includes(flag) || flag === 'deleted') return false;
    const node = findNode(nodeId);
    if (!node) return false;
    node[flag] = !!value;
    touchDiagram();
    return true;
  }

  // Bat/tat dau chon tai san tren node inheritance (contract §13.4):
  // kind = 'own'|'receive'; pos ∈ {1,2,3}; mang khong trung phan tu.
  // View disable chip vi tri chua co asset (P6) — model van cho phep
  // chon (server prune > len(assets) tai commit/save, khong reject).
  function toggleNodePosition(nodeId, kind, pos) {
    if (!canWrite()) return false;
    if (diagramDomain() !== CASE_TYPE_INHERITANCE) return false;
    const field = kind === 'own' ? 'ownPositions'
      : kind === 'receive' ? 'receivePositions' : null;
    if (!field || !POSITIONS.includes(pos)) return false;
    const node = findNode(nodeId);
    if (!node) return false;
    const arr = Array.isArray(node[field]) ? node[field].slice() : [];
    const i = arr.indexOf(pos);
    if (i >= 0) arr.splice(i, 1); else arr.push(pos);
    node[field] = arr;
    touchDiagram();
    return true;
  }

  function setNodeRelation(nodeId, rel) {
    if (!canWrite()) return false;
    // two_party: node khong co quan he cha/me/vo-chong (contract §13.5).
    if (diagramDomain() === CASE_TYPE_TWO_PARTY) return false;
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
    if (!canWrite()) return false;
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
    const s = session;
    // §2.1a: nhap moi (caseId=null) → khong gui case_id, kem stage nhap
    // + hint case.case_type de server evaluate dung domain (§13.7).
    const payload = state.caseId == null
      ? { case: { case_type: caseType() },
          stage: clone(state.stage),
          diagram: { state: clone(state.diagram) } }
      : { case_id: state.caseId,
          diagram: { state: clone(state.diagram) } };
    const r = await client.run('notary.diagram_evaluate', payload);
    state.busy = null;
    if (s !== session) return r;      // response tre — bo
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
    // Warnings engine gan nhat — diagram.warnings chi co tren
    // workspace_get; evaluate/save tra warnings trong render_model (§7.2).
    state.diagramWarnings =
      (r.data.render_model && r.data.render_model.warnings) || [];
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
    const s = session;
    const r = await client.run('notary.diagram_save', {
      case_id: state.caseId,
      base_revision: state.revision,
      diagram: { state: clone(state.diagram) },
    });
    state.busy = null;
    if (s !== session) return r;
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
      state.diagramWarnings =
        (d.diagram.render_model && d.diagram.render_model.warnings) || [];
      // rm evaluate tren state vua persist o revision moi.
      state.evaluatedRevision = d.revision;
    }
    state.diagramDirty = false;
    state.diagramErrors = [];
    state.stale = false;
    state.error = null;
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

  // ---------- intake ----------

  // opts: {onJob} — dialog can job_id/progress de hien thi + cancel.
  async function intakeAnalyze(sources, opts) {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        'Không thể nhập dữ liệu ở trạng thái hiện tại') };
    }
    state.intakeBusy = true;
    emit();
    const s = session;
    // §2.1a: nhap moi → khong gui case_id (case_id:null la loi client).
    const payload = state.caseId == null
      ? { sources: clone(sources) }
      : { case_id: state.caseId, sources: clone(sources) };
    const r = await client.run('notary.intake_analyze', payload, opts);
    state.intakeBusy = false;
    if (s !== session) return r;      // response tre — bo
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'user_canceled') {
        // Huy khong phai loi: giu nguyen suggestion tray, chi notice.
        state.notice = 'Đã hủy phân tích';
      } else {
        state.error = err;
        // Loi job-level co the kem errors per-source — tach rieng de
        // dialog/toa do hien thi dung nguon.
        const per = err.details && err.details.errors;
        if (Array.isArray(per) && per.length) {
          state.intakeErrors = per.concat(state.intakeErrors);
        }
      }
      emit();
      return r;
    }
    const d = r.data || {};
    // Ket qua moi them LEN TREN, khong xoa ngam suggestion cu (plan §13);
    // loi per-source tich luy theo source_id, khong lan sang nguon khac.
    // Dedupe theo suggestion_id: backend co the emit lai id da co (re-
    // analyze cung source) — ban moi thay ban cu, van nam dau danh sach.
    const incoming = d.suggestions || [];
    const newIds = new Set(
      incoming.map((s) => s && s.suggestion_id).filter(Boolean));
    state.suggestions = incoming.concat(
      state.suggestions.filter(
        (s) => !(s && newIds.has(s.suggestion_id))));
    state.intakeErrors = (d.errors || []).concat(state.intakeErrors);
    state.intakePartial = !!r.partial;
    emit();
    return r;
  }

  // Dua suggestion vao Stage nhu draft — khong phai commit (§5).
  function acceptSuggestion(suggestionId) {
    if (!canWrite()) return null;
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
    const s = session;
    const r = await client.run('notary.word_export_options',
                               { case_id: state.caseId });
    if (s !== session) return r;
    if (!r.ok) {
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    state.wordOptions = (r.data && r.data.documents) || [];
    emit();
    return r;
  }

  // Chuan hoa 1 document row ve shape contract §8.4 du nguon la result
  // day du (success/partial/canceled) hay error.details.documents dang
  // compact {document_key, code, message} (all-failed word_batch_failed).
  function normalizeWordDoc(d, key) {
    if (d && typeof d === 'object' &&
        typeof d.status === 'string') {
      return {
        document_key: d.document_key || key || null,
        display_name: d.display_name ?? null,
        status: d.status,
        actual_filename: d.actual_filename ?? null,
        output_file: d.output_file ?? null,
        error: d.error ?? null,
      };
    }
    return {
      document_key: (d && d.document_key) || key || null,
      display_name: (d && d.display_name) ?? null,
      status: 'failed',
      actual_filename: null,
      output_file: null,
      error: { code: (d && d.code) || 'unknown',
               message: (d && d.message) || 'lỗi xuất' },
    };
  }

  function normalizeWordResult(raw, keys) {
    if (!raw || typeof raw !== 'object') return null;
    const docs = (raw.documents || []).map(
      (d) => normalizeWordDoc(d, null));
    return {
      schema_version: raw.schema_version || null,
      destination: raw.destination || null,
      // breakdown.skipped giu nguyen tu wire (MIN-115). Key trong skipped
      // ma khong co row trong documents[] → tong hop row 'skipped' de
      // dialog hien thi tung van ban bi bo qua (cancel giua batch).
      documents: docs.concat(
        ((raw.breakdown && raw.breakdown.skipped) || [])
          .filter((k) => !docs.some((d) => d.document_key === k))
          .map((k) => ({
            document_key: k, display_name: null, status: 'skipped',
            actual_filename: null, output_file: null, error: null,
          }))),
      breakdown: raw.breakdown || {
        succeeded: docs.filter((d) => d.status === 'saved')
          .map((d) => d.document_key),
        failed: docs.filter((d) => d.status === 'failed')
          .map((d) => d.document_key),
        skipped: docs.filter((d) => d.status === 'skipped')
          .map((d) => d.document_key)
          .concat((keys || []).filter(
            (k) => !docs.some((d) => d.document_key === k))),
      },
    };
  }

  // opts: {onJob} — dialog hien thi progress + cancel theo job_id.
  async function exportWord(documentKeys, destination, opts) {
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        'Không thể xuất ở trạng thái hiện tại') };
    }
    state.wordBusy = true;
    state.wordResult = null;
    emit();
    const s = session;
    const r = await client.run('notary.word_export_batch', {
      case_id: state.caseId,
      document_keys: documentKeys,
      destination,
    }, opts);
    state.wordBusy = false;
    if (s !== session) return r;
    if (!r.ok) {
      // Failed/canceled/partial job van co the mang result (breakdown)
      // tren wire: job.result.data (MIN-115) hoac error.details.documents.
      const raw = (r.job && r.job.result && r.job.result.data) ||
        (r.error && r.error.details &&
         (r.error.details.documents ? r.error.details : null)) || null;
      state.wordResult = normalizeWordResult(raw, documentKeys);
      const err = r.error || errObj('unknown');
      if (err.code === 'user_canceled') {
        state.notice = 'Đã hủy xuất Word';
      } else {
        state.error = err;
      }
      emit();
      return r;
    }
    state.wordResult = normalizeWordResult(r.data, documentKeys);
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
    openCase, newDraft, isDraft, saveDraft, updateCaseMeta,
    canWrite, mockBanner, hasUnsaved, isStageEmpty,
    caseType, diagramDomain, documentTypesFor,
    addPerson, addAsset, updatePersonField, updateAssetField,
    moveAsset, setOwnerRow,
    removeStageRow, fieldErrorsFor, commitStage,
    pool,
    addSlot, assignPerson, movePerson,
    setNodeFlag, toggleNodePosition, setNodeRelation, removeNode,
    evaluateDiagram, saveDiagram,
    resolveConflict,
    intakeAnalyze, acceptSuggestion, discardSuggestion,
    loadWordOptions, exportWord,
    dismissNotice,
  };
}

const G1_NOTARY_MODEL = {
  createModel,
  CASE_TYPE_INHERITANCE,
  CASE_TYPE_TWO_PARTY,
  CASE_TYPES,
  SUPPORTED_CASE_TYPE: CASE_TYPE_INHERITANCE,   // back-compat alias
  MOCK_BANNER,
  PERSON_FIELDS,
  ASSET_FIELDS,
  NODE_BOOL_FIELDS,
  NODE_POSITION_FIELDS,
  CASE_META_FIELDS,
  CASE_DOCUMENT_TYPES,
  CASE_DOCUMENT_TYPES_TWO_PARTY,
  documentTypesFor,
  DIAGRAM_VERSION,
  MAX_ASSETS,
  MAX_PEOPLE_TWO_PARTY,
  POSITIONS,
  TWO_PARTY_IDS,
  seedDiagramSlots,
  newTwoPartyState,
};

if (typeof window !== 'undefined') window.G1_NOTARY_MODEL = G1_NOTARY_MODEL;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_MODEL;
}
