// Upload Lab — state thuan (MIN-69, task 6):
// - doi tab khong mat website/ngay/scroll/selection/job
// - acceptScopedResult: ket qua sai website/run/job bi bo qua
// - chuyen website khong mang queue/selection cu theo
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const S = require('../src/renderer/upload/state.js');

test('createUploadState: mot websiteId dung chung, hai tab, selection rong', () => {
  const st = S.createUploadState();
  assert.equal(st.websiteId, null);
  assert.equal(st.activeTab, 'audit');
  assert.ok(st.tabs.audit, 'tab audit phai ton tai');
  assert.ok(st.tabs['scan-upload'], 'tab scan-upload phai ton tai');
  assert.ok(st.selectedIds instanceof Set);
  assert.equal(st.selectedIds.size, 0);
  assert.equal(st.queue, null);
});

// Vi du bat buoc trong brief Task 6.
test('brief example: doi tab giu selection; scope cu bi tu choi', () => {
  const state = S.createUploadState();
  state.websiteId = 'nam_dinh';
  state.runId = 'run_b';
  state.scanJobId = 'job_b';
  state.selectedIds = new Set([12]);
  S.selectTab(state, 'audit');
  S.selectTab(state, 'scan-upload');
  assert.deepEqual([...state.selectedIds], [12]);
  assert.equal(S.acceptScopedResult(state, {
    websiteId: 'nam_dinh', runId: 'run_a', jobId: 'job_a'
  }), false);
});

test('selectTab giu ngay/scroll/selection/job qua cac lan doi', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.fromDate = '2026-01-01';
  st.toDate = '2026-09-24';
  st.selectedIds = new Set([3, 5]);
  st.scanJobId = 'job_1';
  st.tabs.audit.scrollTop = 120;
  S.selectTab(st, 'scan-upload');
  st.tabs['scan-upload'].scrollTop = 240;
  S.selectTab(st, 'audit');
  assert.equal(st.activeTab, 'audit');
  assert.equal(st.tabs.audit.scrollTop, 120);
  assert.equal(st.tabs['scan-upload'].scrollTop, 240);
  assert.equal(st.fromDate, '2026-01-01');
  assert.equal(st.toDate, '2026-09-24');
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [3, 5]);
  assert.equal(st.scanJobId, 'job_1');
});

test('selectTab tu choi tab khong ton tai (khong co tab nhay/config)', () => {
  const st = S.createUploadState();
  assert.equal(S.selectTab(st, 'logs'), false);
  assert.equal(S.selectTab(st, 'config'), false);
  assert.equal(S.selectTab(st, 'audit'), true);
  assert.equal(S.selectTab(st, 'scan-upload'), true);
  assert.equal(st.activeTab, 'scan-upload');
});

test('acceptScopedResult: khop thi nhan, sai website/run/job thi bo', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_1';
  st.scanJobId = 'job_1';
  assert.equal(S.acceptScopedResult(st, { websiteId: 'nam_dinh' }), true);
  assert.equal(S.acceptScopedResult(st, {
    websiteId: 'nam_dinh', runId: 'run_1', jobId: 'job_1'
  }), true);
  assert.equal(S.acceptScopedResult(st, { websiteId: 'khac' }), false);
  assert.equal(S.acceptScopedResult(st, {
    websiteId: 'nam_dinh', runId: 'run_2'
  }), false);
  assert.equal(S.acceptScopedResult(st, {
    websiteId: 'nam_dinh', jobId: 'job_x'
  }), false);
  assert.equal(S.acceptScopedResult(st, null), false);
  assert.equal(S.acceptScopedResult(st, {}), true);
});

test('setWebsite: queue/selection/run cua website cu khong theo sang', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_1';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'run_1', queue_revision: 1,
    has_excel: true,
    folder_rows: [
      { record_id: 1, contract_no: '1/2026', selected: true },
      { record_id: 2, contract_no: '2/2026', selected: true },
    ],
    missing_in_excel_record_ids: [1],
  });
  assert.equal(st.selectedIds.size, 2);
  assert.ok(st.queue);

  S.setWebsite(st, 'khac', {
    website_id: 'khac', revision: 2, run_id: null, audit_id: null,
    browser_id: null, active_job_ids: [], needs_reconcile_record_ids: [],
    has_excel: false, queue_revision: null,
  });
  assert.equal(st.websiteId, 'khac');
  assert.equal(st.runId, null);
  assert.equal(st.queue, null);
  assert.equal(st.selectedIds.size, 0);
  assert.equal(st.hasExcel, false);
  assert.equal(st.revision, 2);
  // ket qua thuoc website cu bi tu choi
  assert.equal(S.acceptScopedResult(st, { websiteId: 'nam_dinh' }), false);
  assert.equal(S.acceptScopedResult(st, { websiteId: 'khac' }), true);
});

test('setWebsite cung website (idempotent) khong xoa state', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.selectedIds = new Set([7]);
  S.setWebsite(st, 'nam_dinh', {
    website_id: 'nam_dinh', revision: 5,
  });
  assert.equal(st.websiteId, 'nam_dinh');
  assert.equal(st.revision, 5);
  assert.deepEqual([...st.selectedIds], [7]);
});

test('applyWorkspace: snapshot cu hon revision khong keo scope lui', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.revision = 8;
  st.runId = 'run_moi';
  st.browserId = 'br_moi';
  // workspace_get submit TRUOC khi audit/scan bump revision → snapshot
  // revision 3 den muon: khong duoc ghi de run/audit/browser/queue hien tai.
  S.applyWorkspace(st, {
    website_id: 'nam_dinh', revision: 3,
    run_id: 'run_cu', audit_id: 'aud_cu', browser_id: 'br_cu',
    has_excel: true, queue_revision: 9,
    needs_reconcile_record_ids: [1], active_job_ids: ['j_x'],
  });
  assert.equal(st.revision, 8, 'revision khong duoc lui');
  assert.equal(st.runId, 'run_moi');
  assert.equal(st.browserId, 'br_moi');
  assert.equal(st.auditId, null);
  assert.equal(st.hasExcel, false);
  assert.equal(st.queueRevision, null);
  assert.equal(st.needsReconcileIds.size, 0);
  assert.equal(st.knownJobIds.size, 0);
  // Snapshot CUNG revision van ap — wsLogin doc browser_id o revision
  // hien tai trong luc session_start con waiting_user.
  S.applyWorkspace(st, {
    website_id: 'nam_dinh', revision: 8, browser_id: 'br_live',
  });
  assert.equal(st.browserId, 'br_live');
  // Snapshot moi hon ap day du.
  S.applyWorkspace(st, {
    website_id: 'nam_dinh', revision: 9, run_id: 'run_9',
    needs_reconcile_record_ids: [4],
  });
  assert.equal(st.revision, 9);
  assert.equal(st.runId, 'run_9');
  assert.deepEqual([...st.needsReconcileIds], [4]);
});

test('applyQueue: chon mac dinh tu backend; refresh giu chon tay', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1, has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: false },
      { record_id: 3, selected: true },
    ],
    missing_in_excel_record_ids: [1],
  });
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [1, 3]);
  assert.deepEqual([...st.missingInExcelIds], [1]);

  // Nguoi dung bo chon 3; queue refresh them record 4 (default selected)
  // → 3 khong tu chon lai (ghi nhan lua chon nguoi dung), 4 chon mac dinh.
  st.selectedIds.delete(3);
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 2, has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: false },
      { record_id: 3, selected: true },
      { record_id: 4, selected: true },
    ],
    missing_in_excel_record_ids: [1],
  });
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [1, 4]);
});

test('applyQueue: ho so da xac minh Luu roi khoi bang', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1, has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: false },
    ],
    missing_in_excel_record_ids: [],
  });
  st.savedIds.add(1);
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 2, has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: false },
    ],
    missing_in_excel_record_ids: [],
  });
  assert.equal(st.rowIds.has(1), false);
  assert.equal(st.rowIds.has(2), true);
  assert.deepEqual(st.queue.folder_rows.map((r) => r.record_id), [2]);
  assert.equal(st.selectedIds.has(1), false);
});

test('sortedQueueRows: dong da chon len dau, giu thu tu goc', () => {
  const st = S.createUploadState();
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1,
    folder_rows: [{ record_id: 1 }, { record_id: 2 }, { record_id: 3 }],
  });
  st.selectedIds = new Set([3]);
  assert.deepEqual(S.sortedQueueRows(st).map((r) => r.record_id), [3, 1, 2]);
});

test('toggleIssueFilter: bo chon so loi, hoan tac khoi phuc (theo Qt)', () => {
  const st = S.createUploadState();
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1,
    folder_rows: [
      { record_id: 1, has_issue: true },
      { record_id: 2 },
      { record_id: 3 },
    ],
  });
  st.selectedIds = new Set([1, 2, 3]);
  assert.equal(S.toggleIssueFilter(st), 'filtered');
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [2, 3]);
  assert.equal(S.toggleIssueFilter(st), 'restored');
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [1, 2, 3]);
});

test('selectMissingExcel: chon dung cac record thieu trong Excel', () => {
  const st = S.createUploadState();
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1, has_excel: true,
    folder_rows: [{ record_id: 1 }, { record_id: 2 }, { record_id: 3 }],
    missing_in_excel_record_ids: [2, 3],
  });
  st.selectedIds = new Set([1]);
  assert.equal(S.selectMissingExcel(st), true);
  assert.deepEqual([...st.selectedIds].sort((a, b) => a - b), [2, 3]);
});

test('resetScanContext: run moi bo het selection/queue cu', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_cu';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'run_cu', queue_revision: 4,
    folder_rows: [{ record_id: 1, selected: true }],
  });
  S.resetScanContext(st, 'run_moi');
  assert.equal(st.runId, 'run_moi');
  assert.equal(st.queue, null);
  assert.equal(st.selectedIds.size, 0);
  assert.equal(st.rowIds.size, 0);
  assert.equal(st.queueRevision, null);
});

test('markAuditStale + clampChunk + isoToDisplay', () => {
  const st = S.createUploadState();
  st.audit = { summary: {} };
  S.markAuditStale(st);
  assert.equal(st.auditStale, true);
  assert.equal(S.clampChunk(0), 1);
  assert.equal(S.clampChunk(31), 30);
  assert.equal(S.clampChunk('abc'), 10);
  assert.equal(S.clampChunk(12), 12);
  assert.equal(S.isoToDisplay('2026-03-14'), '14/03/2026');
  assert.equal(S.isoToDisplay(null), '');
  assert.equal(S.displayToIso('14/03/2026'), '2026-03-14');
  assert.equal(S.displayToIso('khong phai ngay'), null);
});

test('resetScanContext: run moi giu needsReconcileIds (website scope) '
     + 'nhung xoa selection/activeUploadIds/savedIds', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.runId = 'run_cu';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'run_cu', queue_revision: 4,
    folder_rows: [{ record_id: 1, selected: true }],
  });
  st.needsReconcileIds = new Set([6, 7]);
  st.activeUploadIds = new Set([1, 2, 3]);
  st.savedIds = new Set([9]);
  st.openTabIds = new Set([1]);
  S.resetScanContext(st, 'run_moi');
  assert.equal(st.runId, 'run_moi');
  assert.equal(st.selectedIds.size, 0);
  assert.equal(st.activeUploadIds.size, 0,
    'tap goc dot upload thuoc run cu — khong theo sang run moi');
  assert.equal(st.savedIds.size, 0);
  assert.equal(st.openTabIds.size, 0);
  // needs_reconcile la website-scoped (§6.15): run moi KHONG duoc lam
  // mat canh bao — ho so chua ro da Luu phai con hien cho toi khi
  // doi chieu xong.
  assert.deepEqual([...st.needsReconcileIds].sort((a, b) => a - b), [6, 7]);
});

test('clearWebsiteScope (qua setWebsite) xoa ca needsReconcileIds', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  st.needsReconcileIds = new Set([6, 7]);
  S.setWebsite(st, 'khac', {
    website_id: 'khac', revision: 2, run_id: null, audit_id: null,
    browser_id: null, active_job_ids: [],
    needs_reconcile_record_ids: [], has_excel: false,
    queue_revision: null,
  });
  assert.equal(st.needsReconcileIds.size, 0);
  // Snapshot moi co needs → ap lai dung.
  S.applyWorkspace(st, {
    website_id: 'khac', revision: 3,
    needs_reconcile_record_ids: [11],
  });
  assert.deepEqual([...st.needsReconcileIds], [11]);
});

test('applyQueue: dong can doi chieu VAN con trong bang (khong mat tich)', () => {
  const st = S.createUploadState();
  st.websiteId = 'nam_dinh';
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 1,
    has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: true },
    ],
    missing_in_excel_record_ids: [1, 2],
  });
  st.needsReconcileIds = new Set([1]);
  S.applyQueue(st, {
    website_id: 'nam_dinh', run_id: 'r', queue_revision: 2,
    has_excel: true,
    folder_rows: [
      { record_id: 1, selected: true },
      { record_id: 2, selected: true },
    ],
    missing_in_excel_record_ids: [1, 2],
  });
  assert.equal(st.rowIds.has(1), true,
    'dong can doi chieu khong duoc an khoi bang');
  assert.equal(st.needsReconcileIds.has(1), true);
});

test('TABS/AUDIT_COLUMNS/QUEUE_COLUMNS la hang so chuan MIN-77', () => {
  assert.deepEqual(S.TABS.map((t) => t.id), ['audit', 'scan-upload']);
  assert.deepEqual(S.TABS.map((t) => t.label),
    ['Audit Sổ Công Chứng', 'Quét & Upload Hồ Sơ']);
  assert.deepEqual(S.AUDIT_COLUMNS, ['STT', 'Ngày', 'Số công chứng', 'Ghi chú']);
  assert.deepEqual(S.QUEUE_COLUMNS,
    ['✓', 'STT', 'Ngày', 'Số công chứng', 'Ghi chú', 'Địa chỉ file']);
});
