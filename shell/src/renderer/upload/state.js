'use strict';

// Upload Lab — state thuan dung chung cho hai tab (MIN-69, task 6).
// Khong DOM, khong Electron: test duoc bang node --test. Mot `websiteId` duy
// nhat cho ca module — hai tab doc cung state nay. Scope {websiteId, runId,
// jobId} bao ve ket qua: ket qua cua website/run/job khac bi tu choi de
// khong ghi de ngu canh dang xem (contract upload-workflow §11 consumer).

(function () {
  const WORKFLOW_VERSION = 'upload.workflow.v1';

  // Dung hai tab — khong tab Nhat ky/Cau hinh (spec_UI §1).
  const TABS = [
    { id: 'audit', label: 'Audit Sổ Công Chứng' },
    { id: 'scan-upload', label: 'Quét & Upload Hồ Sơ' },
  ];
  const TAB_IDS = new Set(TABS.map((t) => t.id));

  // Cot bang chuan MIN-77.
  const AUDIT_COLUMNS = ['STT', 'Ngày', 'Số công chứng', 'Ghi chú'];
  const QUEUE_COLUMNS =
    ['✓', 'STT', 'Ngày', 'Số công chứng', 'Ghi chú', 'Địa chỉ file'];

  const MIN_CHUNK = 1;
  const MAX_CHUNK = 30;
  const DEFAULT_CHUNK_SIZE = 10;

  function isoToday() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function createUploadState() {
    const year = new Date().getFullYear();
    return {
      // Capability catalog: null = chua biet, true/false sau upload.websites.
      workflowReady: null,
      websites: [],               // catalog tu backend (KHONG hardcode)
      websiteId: null,
      pendingWebsiteId: null,     // website_select dang cho result
      revision: 0,

      // Scope hien tai — hai tab dung chung.
      runId: null,
      auditId: null,
      browserId: null,
      queueRevision: null,
      hasExcel: false,

      // Dieu huong — scroll giu theo tab khi doi.
      activeTab: 'audit',
      tabs: {
        audit: { scrollTop: 0 },
        'scan-upload': { scrollTop: 0 },
      },

      // Input cuc bo cua nguoi dung — giu nguyen ca khi doi website.
      fromDate: `${year}-01-01`,  // ISO; UI hien thi DD/MM/YYYY
      toDate: isoToday(),
      excelFile: null,            // FileRef {path, scope}
      folder: null,               // FileRef thu muc
      staff: { congChungVien: null, thuKy: '', options: [] },
      staffSource: null,
      chunkSize: DEFAULT_CHUNK_SIZE,

      // Audit (kind audit_report, contract §6.9).
      audit: null,                // {audit_id, summary, missing[], issues[]}
      auditStale: false,          // doi ngay/file sau lan nap cuoi
      auditError: null,
      envCheck: null,

      // Queue (kind upload_queue, contract §6.11).
      queue: null,                // {queue_revision, folder_rows[], ...}
      queueFor: null,             // {runId, auditId} queue dang hien thi
      rowIds: new Set(),
      selectedIds: new Set(),
      missingInExcelIds: new Set(),
      issueFilterBackup: null,    // Set — co gia tri = dang loc so loi
      savedIds: new Set(),        // da xac minh Luu tren portal → roi bang
      needsReconcileIds: new Set(),
      scanStats: null,
      manifestRef: null,
      remaining: 0,               // ho so con lai cho dot tiep theo
      uploadSessionActive: false,
      login: null,                // {status, checked_at}
      sessionTabs: null,          // {open, saved, closed, unknown}

      // Job tracking: moi truong *JobId tham gia vao accepted-job scope.
      scanJobId: null,
      auditJobId: null,
      downloadJobId: null,
      queueJobId: null,
      prepareJobId: null,
      sessionJobId: null,
      websiteJobId: null,
      envJobId: null,
      staffJobId: null,
      prefsJobId: null,
      reconcileJobId: null,
      catalogTried: false,
      prefsTried: false,
      staffTried: false,
      knownJobIds: new Set(),     // khoi phuc tu workspace.active_job_ids

      // Tien do tach rieng cho 2 thanh tien trinh.
      scanProgress: null,         // {done,total,current_label}
      prepareProgress: null,
      waitingBanner: null,        // {on, jobId} job waiting_user gan nhat
    };
  }

  // ---------- dieu huong ----------

  function selectTab(state, tabId) {
    if (!TAB_IDS.has(tabId)) return false;
    state.activeTab = tabId;
    return true;
  }

  // ---------- scope ----------

  function activeJobIds(state) {
    const ids = new Set(
      state.knownJobIds instanceof Set ? state.knownJobIds : []);
    for (const k of Object.keys(state)) {
      if (k.endsWith('JobId') && state[k]) ids.add(state[k]);
    }
    return ids;
  }

  // scope = {websiteId?, runId?, auditId?, browserId?, jobId?} — moi khoa co
  // gia tri phai khop state hien tai; thieu khoa = khong rang buoc khoa do.
  function acceptScopedResult(state, scope) {
    if (!state || !scope || typeof scope !== 'object') return false;
    if (scope.websiteId != null && scope.websiteId !== state.websiteId) {
      return false;
    }
    if (scope.runId != null && scope.runId !== state.runId) return false;
    if (scope.auditId != null && scope.auditId !== state.auditId) {
      return false;
    }
    if (scope.browserId != null && scope.browserId !== state.browserId) {
      return false;
    }
    if (scope.jobId != null && !activeJobIds(state).has(scope.jobId)) {
      return false;
    }
    return true;
  }

  // ---------- website / workspace ----------

  function clearWebsiteScope(state) {
    resetScanContext(state, null);
    state.audit = null;
    state.auditId = null;
    state.auditStale = false;
    state.auditError = null;
    state.envCheck = null;
    state.browserId = null;
    state.login = null;
    state.sessionTabs = null;
    state.hasExcel = false;
    state.uploadSessionActive = false;
    state.remaining = 0;
    state.savedIds = new Set();
    state.needsReconcileIds = new Set();
    state.staff = { congChungVien: null, thuKy: '', options: [] };
    state.staffSource = null;
    state.chunkSize = DEFAULT_CHUNK_SIZE;
    state.revision = 0;
    state.waitingBanner = null;
    state.scanProgress = null;
    state.prepareProgress = null;
    state.catalogTried = false;
    state.prefsTried = false;
    state.staffTried = false;
    for (const k of Object.keys(state)) {
      if (k.endsWith('JobId')) state[k] = null;
    }
    state.knownJobIds = new Set();
    state.pendingWebsiteId = null;
  }

  // Doi website: xoa moi state gan website cu (so/queue/selection/job) roi
  // ap workspace cua website moi — khong mang du lieu cu theo (spec §4).
  function setWebsite(state, websiteId, workspace) {
    if (state.websiteId !== websiteId) clearWebsiteScope(state);
    state.websiteId = websiteId;
    if (workspace) applyWorkspace(state, workspace);
    return state;
  }

  // Ap result kind upload_workspace (§6.2) vao state — khoa snake_case wire.
  function applyWorkspace(state, ws) {
    if (!ws || typeof ws !== 'object') return state;
    if (ws.website_id != null) state.websiteId = ws.website_id;
    if (ws.revision != null) state.revision = ws.revision;
    if (ws.run_id !== undefined) state.runId = ws.run_id;
    if (ws.audit_id !== undefined) state.auditId = ws.audit_id;
    if (ws.browser_id !== undefined) state.browserId = ws.browser_id;
    if (ws.has_excel !== undefined) state.hasExcel = Boolean(ws.has_excel);
    if (ws.queue_revision !== undefined) {
      state.queueRevision = ws.queue_revision;
    }
    if (Array.isArray(ws.needs_reconcile_record_ids)) {
      state.needsReconcileIds =
        new Set(ws.needs_reconcile_record_ids.map(Number));
    }
    if (Array.isArray(ws.active_job_ids)) {
      state.knownJobIds = new Set(ws.active_job_ids);
    }
    return state;
  }

  // ---------- run / queue ----------

  // Quet nguon moi = ngu canh luot quet moi: bo selection/queue cua luot cu;
  // ket qua job cu den muon khong ghi de (spec §3).
  function resetScanContext(state, runId) {
    state.runId = runId;
    state.queue = null;
    state.queueFor = null;
    state.queueRevision = null;
    state.rowIds = new Set();
    state.selectedIds = new Set();
    state.missingInExcelIds = new Set();
    state.issueFilterBackup = null;
    state.savedIds = new Set();
    state.needsReconcileIds = new Set();
    state.scanStats = null;
    state.manifestRef = null;
    state.remaining = 0;
    state.queueJobId = null;
    state.prepareJobId = null;
    state.reconcileJobId = null;
    return state;
  }

  // Ap result kind upload_queue. Giu co che Qt (render_scan_classification):
  // - hang moi xuat hien: chon theo `selected` mac dinh cua backend;
  // - hang da co: giu lua chon nguoi dung (khong tu chon/bo chon lai);
  // - hang da xac minh Luu (savedIds): bo khoi bang va khoi selection.
  function applyQueue(state, q, opts) {
    const o = opts || {};
    const rows = (q && Array.isArray(q.folder_rows)) ? q.folder_rows : [];
    const newIds = new Set(rows.map((r) => Number(r.record_id)));
    const prevIds = state.rowIds instanceof Set ? state.rowIds : new Set();
    const defaults = new Set(
      rows.filter((r) => r.selected).map((r) => Number(r.record_id)));

    let sel;
    const preserve = o.preserveSelection !== false && prevIds.size > 0;
    if (!preserve) {
      sel = new Set([...defaults].filter((id) => newIds.has(id)));
    } else {
      sel = new Set([...(state.selectedIds || [])]
        .filter((id) => prevIds.has(id) && newIds.has(id)));
      for (const id of newIds) {
        if (!prevIds.has(id) && defaults.has(id)) sel.add(id);
      }
    }

    // Ho so da xac minh Luu thanh cong roi khoi bang (spec §3).
    const removed = new Set(
      [...(state.savedIds || []), ...((o.removedIds) || [])].map(Number));
    const visibleRows = rows.filter((r) => !removed.has(Number(r.record_id)));
    const visibleIds = new Set(visibleRows.map((r) => Number(r.record_id)));
    for (const id of [...sel]) {
      if (!visibleIds.has(id)) sel.delete(id);
    }

    state.rowIds = visibleIds;
    state.selectedIds = sel;
    state.queue = Object.assign({}, q, { folder_rows: visibleRows });
    if (q.queue_revision != null) state.queueRevision = q.queue_revision;
    if (q.has_excel !== undefined) state.hasExcel = Boolean(q.has_excel);
    state.missingInExcelIds = new Set(
      (q.missing_in_excel_record_ids || []).map(Number));
    state.queueFor = {
      runId: q.run_id || state.runId,
      auditId: q.audit_id === undefined ? state.auditId : q.audit_id,
    };
    state.issueFilterBackup = null;
    return state;
  }

  // Dong da chon len dau, giu nguyen thu tu goc trong tung nhom (Qt:
  // _folder_rows_for_current_selection — sort ong dinh theo index).
  function sortedQueueRows(state) {
    const rows = (state.queue && state.queue.folder_rows) || [];
    const order = new Map(rows.map((r, i) => [Number(r.record_id), i]));
    const sel = state.selectedIds || new Set();
    return rows.slice().sort((a, b) => {
      const sa = sel.has(Number(a.record_id)) ? 0 : 1;
      const sb = sel.has(Number(b.record_id)) ? 0 : 1;
      return sa - sb ||
        order.get(Number(a.record_id)) - order.get(Number(b.record_id));
    });
  }

  // ---------- selection (theo UploadSelection Qt) ----------

  function setSelected(state, recordId, on) {
    const id = Number(recordId);
    if (!state.rowIds.has(id)) return false;
    if (on) state.selectedIds.add(id); else state.selectedIds.delete(id);
    return true;
  }

  function selectAll(state) {
    state.selectedIds = new Set(state.rowIds);
    state.issueFilterBackup = null;
  }

  function clearSelection(state) {
    state.selectedIds.clear();
    state.issueFilterBackup = null;
  }

  function selectOnly(state, ids) {
    const rows = state.rowIds;
    state.selectedIds = new Set(
      [...ids].map(Number).filter((id) => rows.has(id)));
  }

  function selectMissingExcel(state) {
    if (!state.missingInExcelIds || !state.missingInExcelIds.size) {
      return false;
    }
    selectOnly(state, state.missingInExcelIds);
    state.issueFilterBackup = null;
    return true;
  }

  function issueRecordIds(state) {
    const rows = (state.queue && state.queue.folder_rows) || [];
    return new Set(
      rows.filter((r) => r.has_issue).map((r) => Number(r.record_id)));
  }

  // "Loc so loi" cua Qt = BO CHON cac so loi (khong an dong), co hoan tac.
  function toggleIssueFilter(state) {
    const issues = issueRecordIds(state);
    if (state.issueFilterBackup == null) {
      if (!issues.size) return 'empty';
      state.issueFilterBackup = new Set(state.selectedIds);
      for (const id of issues) state.selectedIds.delete(id);
      return 'filtered';
    }
    const backup = state.issueFilterBackup;
    state.issueFilterBackup = null;
    selectOnly(state, backup);
    return 'restored';
  }

  // ---------- audit ----------

  // Doi ngay/file sau lan nap cuoi → ket qua cu "chua cap nhat", khong duoc
  // trinh bay nhu ket qua cua bo loc moi (spec §2).
  function markAuditStale(state) {
    if (state.audit) state.auditStale = true;
    return state;
  }

  // ---------- tien ich ----------

  function clampChunk(v) {
    const n = parseInt(v, 10);
    if (!Number.isFinite(n)) return DEFAULT_CHUNK_SIZE;
    return Math.min(MAX_CHUNK, Math.max(MIN_CHUNK, n));
  }

  function isoToDisplay(iso) {
    if (!iso) return '';
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
    return m ? `${m[3]}/${m[2]}/${m[1]}` : String(iso);
  }

  function displayToIso(s) {
    const m = /^(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{4})$/
      .exec(String(s || '').trim());
    if (!m) return null;
    return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`;
  }

  const API = {
    WORKFLOW_VERSION, TABS, TAB_IDS, AUDIT_COLUMNS, QUEUE_COLUMNS,
    MIN_CHUNK, MAX_CHUNK, DEFAULT_CHUNK_SIZE,
    createUploadState, selectTab, acceptScopedResult, activeJobIds,
    setWebsite, applyWorkspace, resetScanContext, applyQueue,
    sortedQueueRows, setSelected, selectAll, clearSelection, selectOnly,
    selectMissingExcel, issueRecordIds, toggleIssueFilter, markAuditStale,
    clampChunk, isoToDisplay, displayToIso, isoToday,
  };

  if (typeof window !== 'undefined') {
    window.G1_UPLOAD = window.G1_UPLOAD || {};
    window.G1_UPLOAD.state = API;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
  }
})();
