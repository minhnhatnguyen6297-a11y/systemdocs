'use strict';

/* Case-drafting model — state machine thuan cho tab Soạn hồ sơ (MIN-111).
 *
 * SOT hanh vi: _bmad-output/specs/notary_v2/README.md (chi tiet: workspace-detail.md)
 * Wire shape: contracts/notary-case-drafting.md §13 (notary.case-drafting.v2).
 *
 * - Khong DOM, khong Node API bat buoc: chay trong renderer (<script>) va
 *   node --test. Export UMD: window.G1_NOTARY_MODEL + module.exports.
 * - Command client inject qua deps.client.run(command, payload):
 *     Promise<{ok:true, data, partial?} | {ok:false, error}>
 *   o renderer runCommand adapter boc submitCommand+getJob toi terminal.
 * - Draft chi song trong phien (drafting-tab §4): khong localStorage,
 *   khong log — state giu trong object nay.
 * - Mot ban dang sua: Stage, Pool va Diagram cung doc `state.stage`/
 *   `state.diagram`. Baseline `committed*` chi la ban da luu gan nhat de
 *   tinh dirty/diff/conflict. Chi `saveCase` (Luu ho so) ghi DB.
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
  'so_giay_to', 'ngay_cap', 'noi_cap', 'dia_chi', 'place_of_origin',
  // MIN-141 đợt 3: gia trị xac nhan/suy ra — OCR/intake dien, commit
  // giu lai trong snapshot (contract §4.1).
  'loai_giay_to', 'loai_dia_chi'];
// MIN-141 review: 'thoi_han' LE cap tai san da rut khoi whitelist —
// thoi han moi chi thuoc land_rows[].thoi_han (popup Loại đất). Row
// load tu server van co key (master giu lich su) → stageForWire()
// strip truoc khi gui; backend giu nguyen master khi key vang.
const ASSET_FIELDS = ['so_serial', 'so_vao_so',
  'so_thua_dat', 'so_to_ban_do', 'dia_chi', 'loai_so',
  'hinh_thuc_su_dung', 'nguon_goc', 'ngay_cap', 'co_quan_cap'];
const NODE_BOOL_FIELDS = ['hidden', 'deleted'];
const NODE_POSITION_FIELDS = ['ownPositions', 'receivePositions'];

// Meta cho phep sua — khop payload.case §13.6 + đợt 3 (MIN-141).
// case_type/document_type đổi ở nháp hoặc dedicated convertCaseType;
// 5 truong con lai sua duoc ca tren case that — ghi qua commit Stage
// cung transaction (contract §6).
const CASE_META_FIELDS = ['case_type', 'document_type', 'ngay_lap_ho_so',
                          'noi_niem_yet', 'ghi_chu',
                          'nguoi_nhan_uy_quyen', 'nguoi_nhan_uy_quyen_id',
                          'noi_dung_viec'];
// Meta sua duoc tren case da tao (commit payload.case).
const CASE_META_EDITABLE = ['ngay_lap_ho_so', 'noi_niem_yet', 'ghi_chu',
                            'nguoi_nhan_uy_quyen',
                            'nguoi_nhan_uy_quyen_id', 'noi_dung_viec'];
// Meta cap nhat duoc tren case da luu qua notary.workspace_update (§6.2) —
// case_type/document_type chỉ đổi trên case đã lưu qua convertCaseType.
const CASE_META_UPDATE_FIELDS = ['ngay_lap_ho_so', 'noi_niem_yet',
                                 'ghi_chu'];

const CASE_DOCUMENT_TYPES = ['khai_nhan', 'thoa_thuan'];
const CASE_DOCUMENT_TYPES_TWO_PARTY =
  ['chuyen_nhuong', 'tang_cho', 'cho_thue', 'dat_coc'];

// 5 loai nguon intake — khop INTAKE_KINDS o sidecar (notary_adapter.py
// §intake_analyze; missing case_id = che do nhap duoc ho tro §2.1a).
const INTAKE_KINDS = ['image', 'pdf', 'docx', 'xlsx', 'text'];

function documentTypesFor(caseType) {
  return caseType === CASE_TYPE_TWO_PARTY
    ? CASE_DOCUMENT_TYPES_TWO_PARTY : CASE_DOCUMENT_TYPES;
}

function clone(v) {
  return v === undefined ? undefined : JSON.parse(JSON.stringify(v));
}

// Stage payload gui len wire: asset `thoi_han` LE cua DONG MOI duoc giu
// khi co gia tri (nguon Done co the mang field nay; bo di se lam mat du
// kien khi tao row moi — §13.20). Row da co trong `committed` van strip
// nhu truoc (backend giu gia tri lich su). Khong mo o nhap moi.
function normalizeStageAssets(stage) {
  const s = clone(stage) || { people: [], assets: [] };
  for (const a of s.assets || []) {
    if (a && typeof a === 'object') {
      a.so_serial = a.so_serial == null ? '' : String(a.so_serial);
    }
  }
  return s;
}

function stageForWire(stage, committed) {
  const s = normalizeStageAssets(stage);
  const existing = new Set(
    ((committed && committed.assets) || []).map((a) => a && a.row_id));
  for (const a of s.assets || []) {
    if (!a || typeof a !== 'object') continue;
    if (a.thoi_han == null || existing.has(a.row_id)) delete a.thoi_han;
    for (const row of a.land_rows || []) delete row._source_land_row;
  }
  return s;
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
  row.so_serial = row.so_serial == null ? '' : String(row.so_serial);
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

function findInNodes(nodes, id) {
  return (nodes || []).find((n) => n && n.id === id && !n.deleted) || null;
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
    committedCaseInfo: null,     // baseline case de huy nhap meta (đợt 3)
    uqCatalog: null,             // danh bạ người nhận ủy quyền [{id,ho_ten}]
    uqCatalogBusy: false,
    unsupported: false,          // case_type ngoai 'inheritance'
    locked: false,
    stale: false,                // giu nhap sau conflict — server da doi
    revision: 0,
    capabilities: { intake: [], diagram: false, word_export: false },
    committed: { people: [], assets: [] },   // baseline da luu (diff/dirty)
    stage: { people: [], assets: [] },       // ban dang sua — nguon hien thi
    stageDirty: false,
    diagramDirty: false,
    metaDirty: false,            // meta nhap chua luu (chi co tren nhap)
    positionTouched: new Set(),  // session-only "<nodeId>:<own|receive>"
    draftId: null,               // idempotency_key cua phien nhap (uuid4)
    fieldErrors: [],             // [{row_id, field, code, message}]
    diagram: { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
               nodes: [] },                     // ban dang sua
    committedDiagram: { version: DIAGRAM_VERSION,
                        domain: CASE_TYPE_INHERITANCE, nodes: [] },
    renderModel: null,           // output engine gan nhat (evaluate/save)
    diagramWarnings: [],
    diagramErrors: [],
    evaluatedRevision: null,
    conflict: null,              // {server_revision, command}
    error: null,                 // error object job-level gan nhat
    notice: null,                // thong bao ngan
    suggestions: [],             // intake results cho review
    intakeErrors: [],
    intakePartial: false,
    intakeBusy: false,
    wordOptions: null,
    wordBindingProposals: [],
    // Snapshot Stage/Diagram/case/revision tai luc tai proposals — chi
    // de xac nhan binding lap lai khi chi docx context doi. Ngoai wire.
    wordProposalSnapshot: null,
    wordResult: null,
    wordBusy: false,
    busy: null,                  // command dang chay (commit/evaluate/save)
    savingCase: false,           // request workspace_save_case dang chay
    duplicatePending: null,      // {sourceId, key} — giu key qua retry
    duplicating: null,           // sourceCaseId dang cho nhân bản
  };

  let lastUnsaved = false;
  // Session guard: openCase/newDraft tang counter; response tro ve sau
  // khi session da doi (user chuyen case/nhap khac) bi BO — khong ap
  // vao state nua (MIN-122: "bo job response ve tre cua case cu").
  let session = 0;
  // Scan guard rieng cho word options (NAIA-8 review): hai lan quet
  // folder lien tiep trong cung session van phai "response moi nhat
  // thang" — session chi bat duoc chuyen case, khong bat duoc doi folder.
  let wordScanSeq = 0;
  // Tra cuu dia chi thu cong (TASK-4): chi nut Tra moi gui lenh, khong
  // tu tra khi render/go, khong ghi Stage/o. lookupSeq don dieu tang moi
  // khi du lieu nguon doi hoac co lan Tra moi — response chi hien khi seq
  // van nguyen (bat ca A->B->A). lookupCallId phan biet cac lan Tra.
  let lookupSeq = 0;
  let lookupCallId = 0;
  // So lan so do draft bi sua/thay (touchDiagram, gan/go owner, xoa dong,
  // thay wholesale khi mo/luu/doi loai). evaluate ghi lai luc gui de bo
  // response ve sau khi so do da doi (§7.1 D2).
  let diagramMutation = 0;
  // Lan evaluate moi nhat + error object do evaluate dat — de response cu
  // chi don busy cua chinh no, va evaluate thanh cong chi don loi do
  // chinh evaluate dat (khong dung loi cua duong ghi).
  let evaluateSeq = 0;
  let evaluateError = null;
  state.addressSlots = {};
  state.addressFull = null;
  state.addressSuggestions = {};
  state.postingAssetId = null;

  // dateCellInput luu raw dd/mm/yyyy vao model trong luc go (MIN-136,
  // chu y thiet ke) — payload IPC phai gui ISO, nen chuan hoa o day
  // thay vi doi blur/change chuan hoa truoc.
  function isoDate(value) {
    const t = String(value || '').trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t;
    const m = /^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$/.exec(t) ||
              /^(\d{2})(\d{2})(\d{4})$/.exec(t);
    if (!m) return '';
    const d = +m[1], mo = +m[2], y = +m[3];
    const dt = new Date(Date.UTC(y, mo - 1, d));
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 ||
        dt.getUTCDate() !== d) return '';
    const pad = (n) => String(n).padStart(2, '0');
    return `${m[3]}-${pad(mo)}-${pad(d)}`;
  }

  // Nguon chuoi tra cuu theo spec: dia chi Nguoi/Tai san lay o dia chi
  // cua chinh dong do; Noi niem yet lay noi dung chinh o niem yet; Noi cap
  // giay khai tu lay dia chi cua chinh nguoi da chet (o dich van la noi_cap
  // cua nguoi do — hai o co the khac nhau). Doc tu state model (input nao
  // cung dong bo vao model ngay khi go) nen la chu chua luu moi nhat.
  function lookupSlotKey(kind, rowId) {
    return kind + ':' + rowId;
  }

  function addressContext(kind, rowId) {
    if (kind === 'posting') {
      const query = (state.caseInfo || {}).noi_niem_yet;
      if (typeof query !== 'string' || !query.trim()) return null;
      return { query, presentation: 'drafting' };
    }
    const person = kind === 'person' || kind === 'issuer';
    const row = (person ? state.stage.people : state.stage.assets)
      .find(r => r.row_id === rowId);
    if (!row) return null;
    // issuer tra dia chi nguoi chet, khong tra chu trong o noi_cap.
    const query = row.dia_chi;
    if (typeof query !== 'string' || !query.trim()) return null;
    return { query, presentation: 'drafting' };
  }

  // Chuyen case/nhap moi: xoa ket qua tra cuu cu — session guard loai
  // response tre cua case cu.
  function clearAddressLookups() {
    lookupSeq += 1;
    state.addressSlots = {};
    state.addressFull = null;
    state.addressSuggestions = {};
    state.postingAssetId = null;
  }

  function lookupShapeValid(data, presentation) {
    const text = (v) => typeof v === 'string';
    const ref = (v) => v && text(v.unit_id) && text(v.name);
    if (!data || data.schema_version !== 'notary.address-lookup.v2' ||
        !['found', 'not_found', 'too_many', 'invalid_input', 'reload_failed'].includes(data.status) ||
        !(data.presentation === presentation ||
          (data.status === 'invalid_input' && data.presentation === null)) ||
        !Number.isInteger(data.total) || data.total < 0 || !Array.isArray(data.results) ||
        !(data.dataset_version === null || text(data.dataset_version)) ||
        !(data.revision === null || (Number.isInteger(data.revision) && data.revision >= 0))) return false;
    if (data.status !== 'found') return data.results.length === 0 &&
      (data.status === 'too_many' ? presentation === 'drafting' && data.total > 10 : data.total === 0);
    return data.total === data.results.length && data.total > 0 &&
      (presentation !== 'drafting' || data.total <= 10) && data.results.every((row) =>
        row && ref(row) && ['commune', 'province'].includes(row.level) &&
        (row.level === 'commune' ? ref(row.province) : row.province === null) &&
        (row.source_text === null || text(row.source_text)) &&
        text(row.display) && row.display.length > 0 &&
        (row.observation_id === undefined || text(row.observation_id)) &&
        Array.isArray(row.evidence) && row.evidence.every((e) =>
          e && text(e.source_id) && text(e.row_key)));
  }

  function lookupFailure(response) {
    return { ok: false,
      error: { message: 'Không đọc được bảng địa chỉ cục bộ.' } };
  }

  // Nut Tra cua o drafting: gui {query, presentation:'drafting'} voi
  // chu dang thay trong o nguon. Bam lai cung chuoi van gui (khong chan).
  // Moi lan bam la mot callId moi; response cu (sai callId, doi seq, doi
  // session, query hien tai khac luc bam) deu bi bo.
  async function requestLookup(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    const payload = addressContext(kind, rowId);
    lookupSeq += 1;
    const callId = ++lookupCallId;
    if (!payload) {
      state.addressSlots[key] = { phase: 'error', query: '', callId,
        message: 'Nhập địa chỉ cần tra rồi bấm Tra.' };
      emit();
      return;
    }
    state.addressSlots[key] = { phase: 'loading', query: payload.query,
      callId, gen: lookupSeq };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    let response;
    try { response = await client.run('notary.address_lookup', payload); }
    catch (error) { response = lookupFailure(error); }
    if (capturedSession !== session) return;
    const slot = state.addressSlots[key];
    if (!slot || slot.callId !== callId) return;
    if (lookupSeq !== capturedSeq ||
        JSON.stringify(addressContext(kind, rowId)) !== JSON.stringify(payload)) {
      // Nguon doi khi request dang bay ma chua co lan Tra moi hon: don
      // loading treo, bao nguoi dung bam Tra lai thay vi treo mai.
      state.addressSlots[key] = { phase: 'error', query: payload.query,
        callId, gen: capturedSeq,
        message: 'Nội dung đã đổi sau khi bấm Tra. Bấm Tra lại.' };
      emit();
      return;
    }
    const data = response.ok ? response.data : null;
    state.addressSlots[key] = lookupShapeValid(data, 'drafting')
      ? { phase: 'ready', query: payload.query, callId, gen: capturedSeq,
        result: data }
      : { phase: 'error', query: payload.query, callId, gen: capturedSeq,
        message: (response.error || {}).message || 'Tra cứu thất bại.' };
    emit();
  }

  // Xoa ghi chu/ket qua cua mot o (sau khi huy xac nhan too_many).
  function dismissLookupSlot(kind, rowId) {
    delete state.addressSlots[lookupSlotKey(kind, rowId)];
    emit();
  }

  // Bao ket qua cua o da cu (nguoi dung doi du lieu sau khi xac nhan).
  function markLookupStale(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    state.addressSlots[key] = { phase: 'error',
      query: (state.addressSlots[key] || {}).query || '',
      callId: (state.addressSlots[key] || {}).callId || 0,
      message: 'Nội dung đã đổi sau lần Tra trước. Bấm Tra lại.' };
    emit();
  }

  // Mo overlay full sau khi nguoi dung dong y cau hoi too_many: gui ngay
  // yeu cau full DAU TIEN bang dung query da chup tu lan Tra do. Tra ve
  // {ok:false, stale:true} khi slot hoac chu nguon da doi — view bao
  // nguoi dung bam Tra lai, khong mo overlay.
  function openFullFromSlot(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    const slot = state.addressSlots[key];
    const current = addressContext(kind, rowId);
    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many' ||
        slot.result.presentation !== 'drafting' ||
        !current || current.query !== slot.query ||
        slot.gen !== lookupSeq) {
      return { ok: false, stale: true };
    }
    lookupSeq += 1;
    const callId = ++lookupCallId;
    state.addressFull = { slotKey: key, query: slot.query, callId,
      phase: 'loading', result: null, message: null };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    const payload = { query: slot.query, presentation: 'full' };
    (async () => {
      let response;
      try { response = await client.run('notary.address_lookup', payload); }
      catch (error) { response = lookupFailure(error); }
      if (capturedSession !== session) return;
      const full = state.addressFull;
      if (!full || full.callId !== callId) return;
      if (lookupSeq !== capturedSeq) return;
      const data = response.ok ? response.data : null;
      state.addressFull = lookupShapeValid(data, 'full')
        ? { slotKey: key, query: full.query, callId, phase: 'ready',
          result: data, message: null }
        : { slotKey: key, query: full.query, callId, phase: 'error',
          result: null,
          message: (response.error || {}).message || 'Tra cứu thất bại.' };
      emit();
    })();
    return { ok: true };
  }

  // Nut Tra trong overlay: gui query dang thay voi presentation full.
  // Sua chu khong tu gui — chi nut nay gui.
  function requestFull(queryText) {
    const full = state.addressFull;
    if (!full) return;
    lookupSeq += 1;
    const callId = ++lookupCallId;
    state.addressFull = { slotKey: full.slotKey, query: queryText, callId,
      phase: 'loading', result: null, message: null };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    const payload = { query: queryText, presentation: 'full' };
    (async () => {
      let response;
      try { response = await client.run('notary.address_lookup', payload); }
      catch (error) { response = lookupFailure(error); }
      if (capturedSession !== session) return;
      const current = state.addressFull;
      if (!current || current.callId !== callId) return;
      if (lookupSeq !== capturedSeq) return;
      const data = response.ok ? response.data : null;
      state.addressFull = lookupShapeValid(data, 'full')
        ? { slotKey: current.slotKey, query: queryText, callId,
          phase: 'ready', result: data, message: null }
        : { slotKey: current.slotKey, query: queryText, callId,
          phase: 'error', result: null,
          message: (response.error || {}).message || 'Tra cứu thất bại.' };
      emit();
    })();
  }

  // Dong overlay: huy phien full; response ve muon bi bo (khong mo lai
  // cua so, khong doi focus, khong hien ket qua).
  function closeFull() {
    if (!state.addressFull) return;
    state.addressFull = null;
    lookupSeq += 1;
    emit();
  }

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

  function findNode(nodeId) {
    const nodes = state.diagram.nodes || [];
    return nodes.find((n) => n && n.id === nodeId && !n.deleted) || null;
  }

  // Moi case (nhap hay da luu) gan personId theo row_id cua Stage dang
  // sua — cung nguon voi bang Nguoi va Pool, khong doi theo committed.
  function assignablePersonIds() {
    return new Set(state.stage.people.map((p) => p.row_id));
  }

  function diagramPersonIds() {
    const ids = new Set();
    for (const n of state.diagram.nodes || []) {
      if (n && !n.deleted && n.personId) ids.add(n.personId);
    }
    return ids;
  }

  // Pool = nguoi cua Stage dang sua chua gan tren Diagram dang sua.
  // Nguoi vua them/sua xuat hien ngay, khong doi commit. Tai san khong
  // xuong Pool — khong co flow gan tai san len node; diagram chi tham
  // chieu qua ownPositions/receivePositions (vi tri 1..3).
  function pool() {
    const assigned = diagramPersonIds();
    return {
      people: state.stage.people.filter((p) => !assigned.has(p.row_id)),
    };
  }

  function applyWorkspace(data) {
    const c = data.case || {};
    state.caseId = c.id;
    state.caseInfo = clone(c);
    state.committedCaseInfo = clone(c);
    state.backendMode = data.backend_mode || 'real';
    state.revision = c.revision || 0;
    state.locked = !!c.locked;
    state.unsupported = !CASE_TYPES.includes(c.case_type);
    state.capabilities = data.capabilities ||
      { intake: [], diagram: false, word_export: false };
    state.committed = normalizeStageAssets(data.stage || { people: [], assets: [] });
    state.docxImport = clone(data.docx_import || { version: 1, sources: [] });
    state.committedDocxImport = clone(state.docxImport);
    state.stage = clone(state.committed);
    restoreLandIdentity();
    const dg = data.diagram || {};
    state.diagram = clone(dg.state ||
      (c.case_type === CASE_TYPE_TWO_PARTY
        ? newTwoPartyState()
        : { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
            nodes: [] }));
    state.committedDiagram = clone(state.diagram);
    diagramMutation += 1;             // thay wholesale — response evaluate cu bo
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
    state.wordBindingProposals = [];
    state.wordProposalSnapshot = null;
    state.wordResult = null;
    state.wordBusy = false;
    state.evaluatedRevision = null;
    state.busy = null;
    state.savingCase = false;
    state.duplicatePending = null;
    state.duplicating = null;
    state.status = state.locked ? 'locked' : 'ready';
  }

  function setLoadError(err) {
    state.error = err;
    state.status = isInfraError(err.code) ? 'unavailable' : 'error';
  }

  async function openCase(caseId) {
    const s = ++session;
    clearAddressLookups();
    state.positionTouched.clear();
    state.status = 'loading';
    state.caseId = caseId;
    state.draftId = null;
    state.error = null;
    state.notice = null;
    state.busy = null;
    state.savingCase = false;
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

  // Nhãn nghiệp vụ từ trạng thái ĐÃ LƯU của hồ sơ (`caseInfo.status`),
  // không suy từ việc có ID hay không. draft = Nháp, done = Đã lưu;
  // giá trị lạ trả nguyên trạng. Nhãn này độc lập với chấm dirty.
  function statusLabel() {
    const status = state.caseInfo && state.caseInfo.status;
    if (status === 'draft') return 'Nháp';
    if (status === 'done') return 'Đã lưu';
    return status || null;
  }

  // Stage/diagram draft theo loai ho so (§13.1): inheritance mang
  // owner_row_id (BẮT BUỘC) + seed 7 slot; two_party khong co owner_row_id,
  // diagram la 30 slot canonical p1..p30.
  function newStageDraft(caseType) {
    return caseType === CASE_TYPE_TWO_PARTY
      ? { people: [], assets: [] }
      : { owner_row_id: null, people: [], assets: [] };
  }

  // MIN-136: so do thua ke khoi tao DUNG 1 o 'owner' trong. Nguoi dau
  // tien duoc tha vao mac dinh la chu dat (owner_row_id sync trong
  // assignPerson). Moi o sau CHI sinh tu engine requiredSlots —
  // khong co duong them thu cong (xem relationship-diagram.js).
  function newDiagramDraft(caseType) {
    return caseType === CASE_TYPE_TWO_PARTY
      ? newTwoPartyState()
      : { version: DIAGRAM_VERSION, domain: CASE_TYPE_INHERITANCE,
          nodes: [newNode('owner')] };
  }

  // Mo nhap trong — stage rong + diagram seed theo caseType. draftId =
  // idempotency_key cua phien: retry saveCase dung lai → khong tao
  // trung (contract §13.6). newDraft lai → key moi = nhap khac.
  async function newDraft(caseType) {
    const ct = CASE_TYPES.includes(caseType)
      ? caseType : CASE_TYPE_INHERITANCE;
    const s = ++session;              // vo hieu response dang cho cua case cu
    clearAddressLookups();
    state.positionTouched.clear();
    state.status = 'loading';         // khoa sua/luu den khi doc nguon xong
    state.caseId = null;
    state.draftId = uuid();
    state.caseInfo = {
      id: null, case_type: ct,
      document_type: documentTypesFor(ct)[0],
      status: 'draft', locked: false, revision: 0,
      ngay_lap_ho_so: null, noi_niem_yet: null, ghi_chu: null,
      nguoi_nhan_uy_quyen: null, nguoi_nhan_uy_quyen_id: null,
      noi_dung_viec: null,
    };
    state.backendMode = null;
    state.revision = 0;
    state.locked = false;
    state.unsupported = false;
    // MIN-136: adapter ho tro intake nhap khong case_id (contract §2.1a)
    // — nhap moi cong bo du 5 loai nguon, khong khoa nut Nhap file nua.
    state.capabilities =
      { intake: INTAKE_KINDS.slice(), diagram: true, word_export: false };
    state.committed = { people: [], assets: [] };
    state.committedCaseInfo = null;   // nhap moi: khong co baseline case
    state.stage = newStageDraft(ct);
    state.docxImport = { version: 1, sources: [] };
    state.committedDocxImport = clone(state.docxImport);
    state.wordBindingProposals = [];
    state.wordProposalSnapshot = null;
    state.stageDirty = false;
    state.diagramDirty = true;        // seed la draft chua persist
    state.metaDirty = false;
    state.diagram = newDiagramDraft(ct);
    state.committedDiagram = clone(state.diagram);
    diagramMutation += 1;             // nhap moi — response evaluate cu bo
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
    state.busy = 'notary.workspace_source_latest';
    state.savingCase = false;
    state.duplicatePending = null;
    state.duplicating = null;
    emit();

    // Nguon Done moi nhat: dung MOT lan cho phien nhap nay. Loi hien
    // ro (status error/unavailable) — khong nuot thanh nguon rong.
    let r;
    try {
      r = await client.run('notary.workspace_source_latest', {});
    } catch (e) {
      r = { ok: false, error: errObj(
        'unknown', (e && e.message) || 'Không đọc được nguồn') };
    }
    if (s !== session) return r;      // phien khac da thay the
    state.busy = null;
    if (!r || !r.ok) {
      setLoadError((r && r.error) || errObj('unknown'));
      emit();
      return r || { ok: false, error: errObj('unknown') };
    }
    const data = r.data || {};
    const source = data.stage || {};
    const people = Array.isArray(source.people) ? clone(source.people) : [];
    const assets = Array.isArray(source.assets) ? clone(source.assets) : [];
    // Chi chep Stage nguon: committed van rong (chua co DB), meta/diagram
    // moi rieng, loai do nguoi dung chon — khong chep case/meta/diagram.
    const stage = newStageDraft(ct);
    stage.people = people;
    stage.assets = assets;
    if (ct === CASE_TYPE_INHERITANCE) {
      stage.owner_row_id = typeof source.owner_row_id === 'string'
        ? source.owner_row_id : null;
    }
    state.stage = stage;
    state.stageDirty = people.length > 0 || assets.length > 0;
    state.status = 'ready';
    emit();
    return r;
  }

  // Sua meta ho so. Tren nhap moi: du 8 truong (ghi qua
  // workspace_create.payload.case). Tren case da tao: chi
  // CASE_META_EDITABLE — ghi cung commit Stage trong mot transaction
  // (đợt 3, contract §6); chuyển loại saved dùng convertCaseType riêng.
  function updateCaseMeta(field, value) {
    if (!CASE_META_FIELDS.includes(field) || !canWrite()) return false;
    const draftOnly = field === 'case_type' || field === 'document_type';
    if (draftOnly && !isDraft()) return false;
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
      state.positionTouched.clear();
      state.committedDiagram = clone(state.diagram);
      diagramMutation += 1;           // doi loai reset so do
      state.diagramDirty = true;
      state.diagramErrors = [];
      state.metaDirty = true;
      state.stageDirty = true;
      noteLookupSourceChanged();
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
    if (field === 'noi_niem_yet') noteLookupSourceChanged();
    emit();
    return true;
  }

  // Luu meta cho case DA TAO qua notary.workspace_update (§6.2) — mot
  // nguon du lieu duy nhat la DB backend; khong localStorage. Nhap chua
  // nguoi dung (caseId null) → cap nhat nhap local, ghi DB o lan Luu
  // ho so (workspace_save_case). Caller tu hien thi r.error.
  async function saveCaseMeta(patch) {
    if (state.savingCase) {
      return { ok: false, error: errObj('validation_error',
                                        'Đang lưu hồ sơ') };
    }
    const meta = (patch && typeof patch === 'object') ? patch : {};
    const keys = Object.keys(meta);
    if (!keys.length ||
        keys.some((k) => !CASE_META_UPDATE_FIELDS.includes(k))) {
      return { ok: false, error: errObj(
        'validation_error', 'Meta khong hop le') };
    }
    if (isDraft()) {
      for (const k of keys) updateCaseMeta(k, meta[k]);
      return { ok: true };
    }
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        state.locked ? 'Hồ sơ đã khóa — chỉ đọc'
                     : 'Loại việc chưa hỗ trợ') };
    }
    state.busy = 'notary.workspace_update';
    emit();
    const s = session;
    const before = clone(state.caseInfo);
    const committedBefore = clone(state.committedCaseInfo);
    const r = await client.run('notary.workspace_update', {
      case_id: state.caseId,
      base_revision: state.revision,
      case: meta,
    });
    state.busy = null;
    if (s !== session) return r;
    if (!r.ok) {
      // Conflict/locked map vao state nhu moi write khac — caller van
      // nhan r de hien thi loi luu ro rang tai cho (dialog).
      applyWriteResult(r, 'workspace_update');
      emit();
      return r;
    }
    const d = r.data || {};
    if (d.case) {
      const saved = clone(d.case);
      state.committedCaseInfo = { ...state.committedCaseInfo, ...saved };
      // A metadata-only save must preserve other edits in the Stage card,
      // including values typed while the command was still pending.
      for (const [key, value] of Object.entries(saved)) {
        const unchanged = (state.caseInfo[key] ?? null) === (before[key] ?? null);
        const locallyClean = (before[key] ?? null) === (committedBefore[key] ?? null);
        if (unchanged && (keys.includes(key) ||
            !CASE_META_EDITABLE.includes(key) || locallyClean)) {
          state.caseInfo[key] = value;
        }
      }
      state.metaDirty = CASE_META_EDITABLE.some((key) =>
        (state.caseInfo[key] ?? null) !==
        (state.committedCaseInfo[key] ?? null));
    }
    if (typeof d.revision === 'number') state.revision = d.revision;
    state.notice = 'Đã lưu thông tin hồ sơ';
    emit();
    return r;
  }

  async function convertCaseType(conversion) {
    if (!canWrite() || state.caseId == null || state.busy ||
        state.stageDirty || state.metaDirty || state.conflict || state.stale) {
      return { ok: false, error: errObj('validation_error',
        'Hãy Lưu hồ sơ và xử lý xung đột trước khi đổi loại.') };
    }
    const s = session;
    state.busy = 'notary.workspace_convert_type';
    emit();
    let r;
    try {
      r = await client.run('notary.workspace_convert_type', {
        case_id: state.caseId, base_revision: state.revision, ...conversion,
      });
    } catch (e) {
      r = { ok: false, error: errObj('unknown', e.message || 'Không đổi được loại hồ sơ') };
    }
    if (s !== session) return r;
    state.busy = null;
    if (r.ok) {
      applyWorkspace(r.data || {});
      state.positionTouched.clear();
      state.notice = 'Đã đổi loại hồ sơ';
    } else {
      applyWriteResult(r, 'workspace_convert_type');
    }
    emit();
    return r;
  }

  // "Lưu hồ sơ" — một snapshot nhất quán Stage + meta + docx_import +
  // Diagram + revision, gửi notary.workspace_save_case (§13.19). Case
  // mới dùng idempotency_key của phiên nháp (retry giữ nguyên key);
  // case cũ cấm key và dùng base_revision. Trong lúc chờ: savingCase
  // khóa mọi mutator (canWrite=false), không cho snapshot thứ hai.
  // Chỉ response thành công của cùng session mới thay model + clear
  // dirty; lỗi/conflict giữ nguyên draft để người dùng xử lý.
  async function saveCase() {
    if (state.savingCase) {
      return { ok: false, error: errObj('validation_error',
                                        'Đang lưu hồ sơ') };
    }
    if (!canWrite()) {
      return { ok: false, error: errObj(
        state.locked ? 'workspace_locked' : 'case_type_unsupported',
        state.locked ? 'Hồ sơ đã khóa — chỉ đọc'
                     : 'Loại việc chưa hỗ trợ') };
    }
    syncPositionDefaults();
    const caseId = state.caseId;
    const s = session;
    const meta = {};
    for (const f of CASE_META_FIELDS) meta[f] = state.caseInfo[f] ?? null;
    const payload = caseId == null
      ? { idempotency_key: state.draftId || (state.draftId = uuid()) }
      : { case_id: caseId, base_revision: state.revision };
    payload.case = meta;
    payload.stage = stageForWire(state.stage, state.committed);
    payload.diagram = { state: clone(state.diagram) };
    // Case cũ: chỉ gửi docx_import khi draft khác bản đã lưu — absent
    // nghĩa "giữ provenance" theo §13.19, tránh xóa ngoài ý muốn.
    const docx = clone(state.docxImport || { version: 1, sources: [] });
    if (caseId == null ||
        JSON.stringify(docx) !==
          JSON.stringify(state.committedDocxImport || null)) {
      payload.docx_import = docx;
    }
    state.savingCase = true;
    state.busy = 'notary.workspace_save_case';
    emit();
    let r;
    try {
      r = await client.run('notary.workspace_save_case', payload);
    } catch (e) {
      r = { ok: false, error: errObj(
        'unknown', (e && e.message) || 'Không lưu được hồ sơ') };
    }
    if (s !== session) return r;   // session da doi — bo response tre
    state.savingCase = false;
    state.busy = null;
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (!applyStageWriteError(err)) {
        applyWriteResult(r, 'workspace_save_case');
      }
      emit();
      return r;
    }
    applyWorkspace(r.data || {});
    state.notice = caseId == null && r.data && r.data.created === false
      ? 'Hồ sơ đã tồn tại (đã mở lại)' : 'Đã lưu hồ sơ';
    emit();
    return r;
  }

  // Nhân bản toàn bộ Hồ sơ từ danh sách (§13.21): key sinh MỘT lần cho một
  // ý định, giữ qua timeout/lỗi hạ tầng để retry đúng payload; success →
  // key mới. Không đọc buffer nguồn, không gọi newDraft/source_latest.
  async function duplicateCase(sourceCaseId) {
    const sid = Number(sourceCaseId);
    if (!Number.isInteger(sid) || sid < 1) {
      return { ok: false, error: errObj(
        'validation_error', 'Hồ sơ nguồn không hợp lệ') };
    }
    if (state.duplicating != null) {
      return { ok: false, error: errObj(
        'validation_error', 'Đang nhân bản hồ sơ') };
    }
    let intent = state.duplicatePending;
    if (!intent || intent.sourceId !== sid) {
      intent = { sourceId: sid, key: uuid() };
      state.duplicatePending = intent;
    }
    const s = session;
    state.duplicating = sid;
    state.error = null;
    state.notice = null;
    emit();
    let r;
    let transport = false;
    try {
      r = await client.run('notary.workspace_duplicate', {
        source_case_id: sid,
        idempotency_key: intent.key,
      });
    } catch (e) {
      transport = true;
      r = { ok: false, error: errObj(
        'unknown', (e && e.message) || 'Không nhân bản được hồ sơ') };
    }
    if (s !== session) return r;      // phien da doi — bo response tre
    state.duplicating = null;
    if (!r || !r.ok) {
      const err = (r && r.error) || errObj('unknown');
      // Giữ key khi lỗi hạ tầng/timeout; lỗi nghiệp vụ là ý định mới.
      if (!transport && !err.retryable && !isInfraError(err.code)) {
        state.duplicatePending = null;
      }
      state.error = err;
      emit();
      return r || { ok: false, error: err };
    }
    // Success → key mới cho ý định Nhân bản sau (applyWorkspace cũng clear).
    state.duplicatePending = null;
    applyWorkspace(r.data || {});
    state.positionTouched.clear();
    state.notice = r.data && r.data.created === false
      ? 'Đã mở bản sao đã tạo' : 'Đã nhân bản hồ sơ';
    emit();
    return r;
  }

  function canWrite() {
    return (state.status === 'ready' || state.status === 'conflict') &&
      !state.savingCase &&
      !state.duplicating &&
      state.busy !== 'notary.workspace_convert_type' &&
      !state.locked && !state.unsupported;
  }

  // Chi lenh GHI moi khoa nut "Luu ho so". Lenh doc (diagram_evaluate,
  // workspace_source_latest, case_list...) co the dang cho ma nut van
  // phai bam duoc — neu khong, click trong luc evaluate debounce bi nuot
  // (§7.1 D1). Giu tap nay dung bang cac duong ghi cua man soan.
  const WRITE_COMMANDS = [
    'notary.workspace_save_case',
    'notary.workspace_update',
    'notary.workspace_convert_type',
    'notary.workspace_duplicate',
  ];

  function isWriteBusy() {
    return state.savingCase || state.duplicating != null ||
      WRITE_COMMANDS.includes(state.busy);
  }

  // ---------- Stage draft ----------

  // Defense-in-depth: case locked/unsupported khong bao gio mutate draft,
  // ke ca khi view lo de nut write chay (rule drafting-tab §4).
  function touchStage() {
    state.stageDirty = true;
    emit();
  }

  // Dau thay doi cho tra cuu: chi dia chi/noi cap/noi niem yet, them/xoa
  // dong Nguoi/Tai san, doi case. Sua ho ten/ngay thang/sap xep khong lam
  // request dang bay het hieu luc.
  function noteLookupSourceChanged() {
    lookupSeq += 1;
    for (const [key, slot] of Object.entries(state.addressSlots)) {
      const separator = key.indexOf(':');
      const context = addressContext(key.slice(0, separator), key.slice(separator + 1));
      if (!context || context.query !== slot.query) {
        state.addressSlots[key] = { ...slot, phase: 'error', result: null,
          message: 'Nội dung đã đổi sau khi bấm Tra. Bấm Tra lại.' };
      }
    }
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
    // Da co nguoi → loi cap danh sach 'people' (row_id=null) cua lan
    // truoc khong con la ket qua hien tai. Giu nguyen loi khac.
    state.fieldErrors = state.fieldErrors.filter(
      (e) => !(e.row_id == null && e.field === 'people'));
    noteLookupSourceChanged();
    touchStage();
    return row;
  }

  function addAsset(fields) {
    if (!canWrite()) return null;
    // Toi da 3 asset; vi tri = index+1 trong mang (contract §13.3).
    if (state.stage.assets.length >= MAX_ASSETS) return null;
    const row = newAssetRow(uuid, fields);
    state.stage.assets.push(row);
    // Da co tai san → loi cap danh sach 'assets' (row_id=null) khong con
    // la ket qua hien tai. Giu nguyen loi khac.
    state.fieldErrors = state.fieldErrors.filter(
      (e) => !(e.row_id == null && e.field === 'assets'));
    noteLookupSourceChanged();
    touchStage();
    syncPositionDefaults();
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
    if (field === 'dia_chi' || field === 'noi_cap') noteLookupSourceChanged();
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
            _source_land_row: x && x._source_land_row || null,
          })) : [];
      for (const source of state.docxImport?.sources || []) {
        const record = source.records.find((r) => r.row_id === rowId);
        if (record) {
          record.land_rows = row.land_rows.map((r) => r._source_land_row);
          source.bindings = source.bindings.filter((b) => b.candidate_id !== record.candidate_id || b.field_key !== 'land_rows');
          delete source.template_sha256;
        }
      }
    } else if (field === 'so_serial') {
      // Serial là chuỗi nguyên văn: rỗng giữ '', không đổi thành null.
      row[field] = value == null ? '' : String(value);
    } else if (ASSET_FIELDS.includes(field)) {
      row[field] = value === '' ? null : value;
    } else {
      return;
    }
    clearRowFieldError(rowId, field);
    if (field === 'dia_chi') noteLookupSourceChanged();
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
  // luu; client cap nhat mirror de render dung ngay.
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
      diagramMutation += 1;           // mirror owner doi
    }
    // Chon duoc nguoi de lai → banner workspace_owner_required da het
    // nguyen nhan. Go owner (null) thi nguyen nhan con do: giu banner.
    if (rowId !== null && state.error &&
        state.error.code === 'workspace_owner_required') {
      state.error = null;
    }
    // Gan/go owner la sua so do — diagramErrors cua lan Luu truoc da cu.
    // movePerson ve Pool goi thang setOwnerRow(null), khong qua touchDiagram,
    // nen phai don tai day.
    state.diagramErrors = [];
    touchStage();
    return true;
  }

  function removeStageRow(rowId) {
    if (!canWrite()) return;
    const before = state.stage.people.length + state.stage.assets.length;
    const assetCount = state.stage.assets.length;
    state.stage.people = state.stage.people.filter((p) => p.row_id !== rowId);
    state.stage.assets = state.stage.assets.filter((a) => a.row_id !== rowId);
    if (state.stage.people.length + state.stage.assets.length === before) {
      return;
    }
    noteLookupSourceChanged();
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
        diagramMutation += 1;         // tham chieu node bi go
      }
    }
    state.fieldErrors = state.fieldErrors.filter((e) => e.row_id !== rowId);
    touchStage();
    if (state.stage.assets.length !== assetCount) syncPositionDefaults();
  }

  function fieldErrorsFor(rowId) {
    return state.fieldErrors.filter((e) => e.row_id === rowId);
  }

  function isStageEmpty() {
    return !state.stage.people.length && !state.stage.assets.length;
  }

  // Loi hien thi phai la ket qua cua lan ghi GAN NHAT: chi mot kenh loi
  // duoc bat moi lan, khong treo banner/o do cua lan thao tac truoc.
  // Tra true khi loi da thuoc kenh field/diagram (khong dat state.error).
  function applyStageWriteError(err) {
    if (err.code === 'stage_validation_error') {
      state.fieldErrors = (err.details && err.details.field_errors) || [];
      state.diagramErrors = [];
      state.error = null;
      return true;
    }
    if (err.code === 'diagram_invalid_state') {
      state.diagramErrors = (err.details && err.details.errors) || [err];
      state.fieldErrors = [];
      state.error = null;
      return true;
    }
    // Loi khac (owner_required/conflict/locked/unknown...) — fieldErrors/
    // diagramErrors thuoc lan truoc, khong con la ket qua hien tai.
    state.fieldErrors = [];
    state.diagramErrors = [];
    return false;
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

  // ---------- Diagram draft ----------

  function touchDiagram() {
    state.diagramDirty = true;
    diagramMutation += 1;
    // Sua so do → diagramErrors cua lan Luu truoc khong con la ket qua
    // hien tai. Khong dung fieldErrors/error: chung thuoc du lieu stage.
    state.diagramErrors = [];
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

  function syncPositionDefaults() {
    if (diagramDomain() !== CASE_TYPE_INHERITANCE) return;
    const nodes = state.diagram.nodes || [];
    const count = state.stage.assets.length;
    const otherOwner = nodes.some((n) => n && !n.deleted &&
      n.id !== 'owner' && n.ownPositions && n.ownPositions.length);
    let changed = false;
    for (const node of nodes) {
      if (!node || node.deleted || !node.personId) continue;
      const kind = node.id === 'owner' ? 'own' : 'receive';
      if (state.positionTouched.has(`${node.id}:${kind}`)) continue;
      const field = kind === 'own' ? 'ownPositions' : 'receivePositions';
      const positions = node[field] || [];
      if (kind === 'own' && !positions.length && otherOwner) continue;
      if (positions.length === count &&
          positions.every((pos, i) => pos === i + 1)) continue;
      node[field] = Array.from({ length: count }, (_, i) => i + 1);
      changed = true;
    }
    if (changed) touchDiagram();
  }

  // Gan nguoi (row_id trong Stage dang sua) vao slot; rowId=null → bo gan,
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
    state.positionTouched.add(`${nodeId}:${kind}`);
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

  function nodeRemovalImpact(nodeId) {
    if (diagramDomain() !== CASE_TYPE_INHERITANCE || !findNode(nodeId)) {
      return null;
    }
    const nodes = state.diagram.nodes;
    const children = new Map();
    for (const n of nodes) {
      if (!n || n.deleted) continue;
      for (const parent of n.parentSlotIds || []) {
        if (!children.has(parent)) children.set(parent, []);
        children.get(parent).push(n.id);
      }
    }
    const removed = new Set([nodeId]);
    const queue = [nodeId];
    for (let i = 0; i < queue.length; i += 1) {
      for (const child of children.get(queue[i]) || []) {
        if (removed.has(child)) continue;
        removed.add(child);
        queue.push(child);
      }
    }
    const relations = [];
    const spouses = new Set();
    for (const n of nodes) {
      if (!n) continue;
      for (const parent of n.parentSlotIds || []) {
        if (removed.has(n.id) || removed.has(parent)) {
          relations.push({ kind: 'parent', from: parent, to: n.id });
        }
      }
      if (n.spouseSlotId &&
          (removed.has(n.id) || removed.has(n.spouseSlotId))) {
        const pair = [n.id, n.spouseSlotId].sort();
        const key = JSON.stringify(pair);
        if (!spouses.has(key)) {
          spouses.add(key);
          relations.push({ kind: 'spouse', from: pair[0], to: pair[1] });
        }
      }
    }
    return { nodeIds: queue, relations };
  }

  function removeNode(nodeId) {
    if (!canWrite()) return false;
    const impact = nodeRemovalImpact(nodeId);
    if (!impact) return false;
    const removed = new Set(impact.nodeIds);
    for (const n of state.diagram.nodes) {
      if (!n) continue;
      if (removed.has(n.id)) {
        n.deleted = true;
        n.parentSlotIds = [];
        n.spouseSlotId = null;
      } else {
        if ((n.parentSlotIds || []).some((p) => removed.has(p))) {
          n.parentSlotIds = n.parentSlotIds.filter((p) => !removed.has(p));
        }
        if (removed.has(n.spouseSlotId)) n.spouseSlotId = null;
      }
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
    const call = ++evaluateSeq;
    const diagramAtIssue = diagramMutation;
    state.busy = 'notary.diagram_evaluate';
    emit();
    const s = session;
    // Mọi workspace đang sửa (kể cả case đã lưu) evaluate trên buffer:
    // nhánh draft của adapter — case hint + Stage + Diagram, KHÔNG
    // case_id/base_revision, không ghi DB (§2.1a, §13.2).
    const payload = { case: { case_type: caseType() },
      stage: stageForWire(state.stage, state.committed),
      diagram: { state: clone(state.diagram) } };
    const r = await client.run('notary.diagram_evaluate', payload);
    const isLatest = call === evaluateSeq;
    if (isLatest) state.busy = null;
    if (s !== session) return r;      // response tre — bo
    if (!isLatest || diagramMutation !== diagramAtIssue) {
      // Response tre: so do da sua/thay hoac da co lan evaluate moi hon.
      // Chi don busy cua chinh no; khong dung error/diagramErrors/
      // renderModel/warnings cua trang thai hien tai (§7.1 D2).
      if (isLatest) emit();
      return r;
    }
    // Ket qua moi nhat cho dung so do hien tai — loi do evaluate dat
    // truoc do khong con la ket qua hien tai; loi cua duong ghi thi
    // KHONG duoc don o day.
    if (state.error && state.error === evaluateError) state.error = null;
    evaluateError = null;
    if (!r.ok) {
      const err = r.error || errObj('unknown');
      if (err.code === 'diagram_invalid_state') {
        state.diagramErrors =
          (err.details && err.details.errors) || [err];
      } else {
        state.error = err;
        evaluateError = err;
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
    if (s !== session) return { ok: true, stale: true };
    state.intakeBusy = false;
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
    const intakeSnapshot = clone(d);
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
    return { ...r, intakeSnapshot };
  }

  // Dua suggestion vao Stage nhu draft — khong phai commit (§5).
  function acceptSuggestion(suggestionId) {
    if (!canWrite()) return null;
    const i = state.suggestions.findIndex(
      (s) => s.suggestion_id === suggestionId);
    if (i < 0) return null;
    const sug = state.suggestions[i];
    const ref = Object.values(sug.fields || {}).flatMap((f) => f.source_refs || []).find((r) => r.kind === 'docx');
    if (ref && !state.docxImport.sources.some((s) => s.source_id === ref.source_id) && state.docxImport.sources.length >= 8) {
      state.notice = 'Hồ sơ đã có 8 nguồn Word; hãy gỡ một nguồn trước khi thêm nguồn mới'; emit(); return null;
    }
    const fields = {};
    for (const [k, f] of Object.entries(sug.fields || {})) {
      if (f?.review_error) { state.notice = f.review_error; emit(); return null; }
      if (k === 'land_rows' && !f.land_identity) {
        try { f.land_identity = JSON.parse(f.normalized_value || '[]').map((_, n) => n + 1); } catch (_) { f.land_identity = []; }
      }
      if (k === 'land_rows' && (f.source_refs || []).some((r) =>
        ['ambiguous', 'error', 'warning_nonstandard'].includes(r.core_state) &&
        (f.land_identity || []).includes(r.land_row) && !f.reviewed_cells?.includes(`${r.land_row}:${r.land_field}`))) {
        state.notice = 'Cụm đất: hãy kiểm tra từng ô còn mơ hồ'; emit(); return null;
      }
      if (k !== 'land_rows' && f && f.normalized_value == null && (f.source_refs || []).some((ref) =>
          ['ambiguous', 'error', 'warning_nonstandard'].includes(ref.core_state)) && !f.reviewed) {
        state.notice = `${k}: hãy chọn hoặc sửa giá trị trước khi đưa vào Stage`;
        emit();
        return null;
      }
      fields[k] = f && f.reviewed ? f.normalized_value : f && f.normalized_value != null
        ? f.normalized_value : (f && f.raw_value != null ? f.raw_value : null);
    }
    if (fields.land_rows) {
      try {
        fields.land_rows = JSON.parse(fields.land_rows);
        if (Array.isArray(fields.land_rows) && fields.land_rows.length > 20) {
          state.notice = 'Stage giữ tối đa 20 cụm đất; hãy bỏ bớt dòng trước khi đưa vào Stage'; emit(); return null;
        }
        if (!Array.isArray(fields.land_rows) ||
            fields.land_rows.some((r) => !r || typeof r !== 'object' || Array.isArray(r))) throw new Error();
        const identity = sug.fields.land_rows.land_identity || fields.land_rows.map((_, n) => n + 1);
        fields.land_rows.forEach((r, n) => { r._source_land_row = identity[n] || null; });
      } catch (_) { state.notice = 'Cụm đất cần là danh sách JSON hợp lệ'; emit(); return null; }
    }
    const row = sug.target === 'asset'
      ? addAsset(fields) : addPerson(fields);
    if (!row) { state.notice = 'Stage đã đủ chỗ; gợi ý vẫn được giữ để xử lý sau'; emit(); return null; }
    if (ref) {
      state.docxImport = state.docxImport || { version: 1, sources: [] };
      let source = state.docxImport.sources.find((s) => s.source_id === ref.source_id);
      if (!source) {
        source = { source_id: ref.source_id, sha256: ref.source_sha256, label: ref.source_label || 'Hợp đồng Word', records: [], bindings: [] };
        state.docxImport.sources.push(source);
      }
      source.records.push({ candidate_id: sug.suggestion_id, row_id: row.row_id,
        ...(sug.target === 'asset' && fields.land_rows ? { land_rows: fields.land_rows.map((r) => r._source_land_row) } : {}) });
    }
    state.suggestions.splice(i, 1);
    emit();
    return row;
  }

  function reviewSuggestion(suggestionId, fieldKey, value, landReview) {
    const sug = state.suggestions.find((s) => s.suggestion_id === suggestionId);
    if (!canWrite() || !sug || !sug.fields[fieldKey]) return false;
    const field = sug.fields[fieldKey];
    const invalid = (message) => {
      field.reviewed = false;
      field.review_error = message;
      field.review_input = value;
      field.normalized_value = null;
      state.notice = message; emit(); return false;
    };
    if (fieldKey.startsWith('ngay_') && value) {
      const t = String(value).trim();
      let y, m, d;
      let match = t.match(/^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$/);
      if (match) [, d, m, y] = match;
      else if ((match = t.match(/^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$/))) [, y, m, d] = match;
      else if (/^(19|20)\d{2}$/.test(t)) value = t;
      else return invalid('Ngày cần là năm hoặc ngày/tháng/năm hợp lệ');
      if (y) {
        const date = new Date(Date.UTC(Number(y), Number(m) - 1, Number(d)));
        if (date.getUTCFullYear() !== Number(y) || date.getUTCMonth() + 1 !== Number(m) || date.getUTCDate() !== Number(d)) {
          return invalid('Ngày không hợp lệ');
        }
        value = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      }
    }
    if (fieldKey === 'dien_tich' && value !== '' && value != null) {
      let text = String(value).trim();
      if (text.includes(',') && text.includes('.')) text = text.replace(/\./g, '').replace(/,/g, '.');
      else if (text.includes(',')) text = text.replace(/,/g, '.');
      if (!/^\+?\d+(\.\d+)?$/.test(text) || !Number.isFinite(Number(text))) return invalid('Diện tích cần là số hữu hạn từ 0 trở lên');
      value = Number(text);
    }
    if (fieldKey === 'land_rows') {
      let rows;
      try { rows = JSON.parse(value); } catch (_) { return invalid('Cụm đất cần là danh sách JSON hợp lệ'); }
      if (!Array.isArray(rows) || rows.some((r) => !r || (r.dien_tich != null &&
          (typeof r.dien_tich !== 'number' || !Number.isFinite(r.dien_tich) || r.dien_tich < 0)))) {
        return invalid('Diện tích cần là số hữu hạn từ 0 trở lên');
      }
    }
    field.normalized_value = value === '' ? null : value;
    delete field.review_error;
    delete field.review_input;
    field.reviewed = true;
    if (fieldKey === 'land_rows' && landReview) {
      field.land_identity = clone(landReview.identity);
      field.reviewed_cells = [...new Set([...(field.reviewed_cells || []), ...(landReview.cell ? [landReview.cell] : [])])];
    }
    emit();
    return true;
  }

  function restoreLandIdentity() {
    for (const source of state.docxImport?.sources || []) for (const record of source.records) {
      for (const stage of [state.stage, state.committed]) {
        const asset = stage.assets.find((a) => a.row_id === record.row_id);
        if (asset) (asset.land_rows || []).forEach((r, n) => { r._source_land_row = record.land_rows ? record.land_rows[n] : n + 1; });
      }
    }
  }

  function detachOriginalSource(sourceId) {
    if (!canWrite()) return false;
    state.docxImport.sources = state.docxImport.sources.filter((s) => s.source_id !== sourceId);
    touchStage(); return true;
  }

  function confirmOriginalBindings(sourceId, bindings) {
    if (!canWrite()) return false;
    const source = state.docxImport.sources.find((s) => s.source_id === sourceId);
    if (!source) return false;
    // Proposals chi con dung khi Stage/Diagram/case/revision khong doi
    // ke tu luc tai. Docx context (nguon/bindings) duoc doi — cho phep
    // lap confirm tren cung snapshot. Doi buffer thi phai Luu/tai lai.
    const snap = state.wordProposalSnapshot;
    if (!snap || snap.caseId !== state.caseId ||
        snap.revision !== state.revision ||
        JSON.stringify(snap.stage) !== JSON.stringify(state.stage) ||
        JSON.stringify(snap.diagram) !== JSON.stringify(state.diagram)) {
      state.wordProposalSnapshot = null;
      return false;
    }
    source.bindings = bindings.map((b) => ({ candidate_id: b.candidate_id,
      occurrence_id: b.occurrence_id, field_key: b.field_key, slot: b.slot }));
    touchStage();
    return true;
  }

  function discardSuggestion(suggestionId) {
    const i = state.suggestions.findIndex(
      (s) => s.suggestion_id === suggestionId);
    if (i < 0) return;
    state.suggestions.splice(i, 1);
    emit();
  }

  // ---------- Danh ba nguoi nhan uy quyen (đợt 3, MIN-141) ----------
  // Catalog = bang customers qua notary.customer_list (danh ba chung cua
  // backend — AC "uu tien tai dung danh ba hien co"). Mock khong co danh
  // ba that: tra danh sach rong, UI roi ve nhap tu do.

  async function loadUqCatalog(query) {
    if (state.uqCatalogBusy) return { ok: true, noop: true };
    state.uqCatalogBusy = true;
    emit();
    const s = session;
    const r = await client.run('notary.customer_list', {
      query: query || '', limit: 200,
    });
    state.uqCatalogBusy = false;
    if (s !== session) return r;
    if (!r.ok) {
      // Catalog khong bat buoc — nhap tu do van duoc; loi chi noi
      // qua error state (khong chan Stage).
      state.uqCatalog = [];
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    state.uqCatalog = (r.data && r.data.customers) || [];
    emit();
    return r;
  }

  // "+ Them vao danh ba": tao customer moi toi thieu (ho_ten) roi gan
  // lam nguoi nhan uy quyen — tham chieu on dinh customers.id di vao
  // commit tiep theo (AC: khong chi mot chuoi ten).
  async function createUqCustomer(hoTen) {
    const name = (hoTen == null ? '' : String(hoTen)).trim();
    if (!name) {
      return { ok: false, error: errObj('validation_error',
                                        'Tên người nhận ủy quyền trống') };
    }
    state.uqCatalogBusy = true;
    emit();
    const s = session;
    const r = await client.run('notary.customer_create',
                               { ho_ten: name });
    state.uqCatalogBusy = false;
    if (s !== session) return r;
    if (!r.ok) {
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    const cust = (r.data && r.data.customer) || {};
    if (cust.id != null) {
      if (Array.isArray(state.uqCatalog) &&
          !state.uqCatalog.some((x) => x && x.id === cust.id)) {
        state.uqCatalog.push(cust);
      }
      updateCaseMeta('nguoi_nhan_uy_quyen', cust.ho_ten || name);
      updateCaseMeta('nguoi_nhan_uy_quyen_id', cust.id);
    } else {
      updateCaseMeta('nguoi_nhan_uy_quyen', cust.ho_ten || name);
      updateCaseMeta('nguoi_nhan_uy_quyen_id', null);
    }
    emit();
    return r;
  }

  // Giai name -> catalog id: go ten trung het mot entry → gan id (tham
  // chieu on dinh); khong trung → free text (id null). Dung cho input
  // nguoi nhan uy quyen ket hop datalist.
  function resolveUqName(name) {
    const t = (name == null ? '' : String(name)).trim();
    const list = Array.isArray(state.uqCatalog) ? state.uqCatalog : [];
    const hit = list.find((c) => c && c.ho_ten === t);
    updateCaseMeta('nguoi_nhan_uy_quyen', t || null);
    updateCaseMeta('nguoi_nhan_uy_quyen_id',
                   hit && hit.id != null ? hit.id : null);
  }

  // ---------- word export (thin — dialog day du o MIN-112) ----------

  // NAIA-8: `templateDir` = {file_token} cua thu muc mau do nguoi dung
  // chon — main resolve thanh FileRef is_dir:true; backend quet .docx
  // trong thu muc do. Khong truyen → catalog/builtin cu.
  async function loadWordOptions(templateDir, originalSourceId) {
    const s = session;
    const seq = ++wordScanSeq;
    // Quet folder moi = nguon mau moi — xoa options ngay de khong ai
    // doc danh sach cua folder truoc khi dang cho scan.
    state.wordOptions = null;
    state.wordBindingProposals = [];
    state.wordProposalSnapshot = null;
    emit();
    const payload = { case_id: state.caseId };
    if (templateDir) payload.template_dir = templateDir;
    if (originalSourceId) payload.original_source_id = originalSourceId;
    const r = await client.run('notary.word_export_options', payload);
    if (s !== session || seq !== wordScanSeq) {
      // Response tre (case doi hoac folder moi hon dang scan) — BO ca
      // success lan error; scan moi nhat tu render/error state cua no.
      return { ok: true, stale: true };
    }
    if (!r.ok) {
      state.error = r.error || errObj('unknown');
      emit();
      return r;
    }
    state.wordOptions = (r.data && r.data.documents) || [];
    state.wordBindingProposals = (r.data && r.data.binding_proposals) || [];
    // Proposals duoc server chung minh tren Stage/Diagram/case/revision
    // tai thoi diem nay. Chi docx context (nguon/bindings) duoc doi ma
    // khong vo hieu snapshot; Stage/Diagram/case/revision doi thi phai
    // Luu ho so roi tai lai.
    state.wordProposalSnapshot = {
      caseId: state.caseId,
      revision: state.revision,
      stage: clone(state.stage),
      diagram: clone(state.diagram),
    };
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

  // opts: {onJob, templateDir, createCaseSubdir} — dialog hien thi
  // progress + cancel theo job_id. `templateDir` = {file_token} thu muc
  // mau; `createCaseSubdir` = tao thu muc con HS-<case_id> trong dich.
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
    const o = (opts && typeof opts === 'object') ? opts : {};
    const payload = {
      case_id: state.caseId,
      document_keys: documentKeys,
      destination,
    };
    if (o.templateDir) payload.template_dir = o.templateDir;
    if (o.originalSourceId) {
      if (hasUnsaved()) {
        state.wordBusy = false;
        return { ok: false, error: errObj('word.original_mapping_invalid', 'Hãy Lưu hồ sơ trước khi xuất.') };
      }
      payload.original_source_id = o.originalSourceId;
      payload.base_revision = state.revision;
    }
    if (o.createCaseSubdir) payload.create_case_subdir = true;
    const r = await client.run('notary.word_export_batch', payload, opts);
    if (s !== session) return { ok: true, stale: true };
    state.wordBusy = false;
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
    return state.stageDirty || state.diagramDirty || state.metaDirty;
  }

  function dismissNotice() {
    state.notice = null;
    state.error = null;
    emit();
  }

  return {
    state, subscribe,
    addressContext, requestLookup, dismissLookupSlot, markLookupStale,
    openFullFromSlot, requestFull, closeFull,
    openCase, newDraft, isDraft, statusLabel, saveCase, updateCaseMeta, saveCaseMeta, convertCaseType,
    duplicateCase,
    loadUqCatalog, createUqCustomer, resolveUqName,

    canWrite, isWriteBusy, mockBanner, hasUnsaved, isStageEmpty,
    caseType, diagramDomain, documentTypesFor,
    addPerson, addAsset, updatePersonField, updateAssetField,
    moveAsset, setOwnerRow,
    removeStageRow, fieldErrorsFor,
    pool,
    addSlot, assignPerson, movePerson,
    setNodeFlag, toggleNodePosition, setNodeRelation, nodeRemovalImpact, removeNode,
    evaluateDiagram,
    resolveConflict,
    intakeAnalyze, acceptSuggestion, discardSuggestion, reviewSuggestion, confirmOriginalBindings, detachOriginalSource,
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
  CASE_META_EDITABLE,
  CASE_DOCUMENT_TYPES,
  CASE_DOCUMENT_TYPES_TWO_PARTY,
  documentTypesFor,
  DIAGRAM_VERSION,
  MAX_ASSETS,
  MAX_PEOPLE_TWO_PARTY,
  POSITIONS,
  TWO_PARTY_IDS,
  INTAKE_KINDS,
  newTwoPartyState,
};

if (typeof window !== 'undefined') window.G1_NOTARY_MODEL = G1_NOTARY_MODEL;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_MODEL;
}
