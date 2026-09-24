'use strict';

// Upload Lab — lop command/scope phia renderer (MIN-69, task 6).
// Boc payload bang `workflow_version: upload.workflow.v1` (contract §2) va
// anh xa result cua job ve state module qua acceptScopedResult: ket qua sai
// website/run/job den muon khong ghi de ngu canh dang xem.
// Khong DOM — test duoc bang node --test.

(function () {
  const S = (typeof window !== 'undefined' &&
             window.G1_UPLOAD && window.G1_UPLOAD.state)
    ? window.G1_UPLOAD.state
    : require('./state.js');

  const WORKFLOW_VERSION = 'upload.workflow.v1';

  // Command luong versioned — gui kem workflow_version trong payload.
  const TRACKED_COMMANDS = [
    'upload.websites', 'upload.workspace_get', 'upload.website_select',
    'upload.env_check', 'upload.session_start', 'upload.session_status',
    'upload.session_close', 'upload.download_export', 'upload.audit_excel',
    'upload.scan', 'upload.queue_get', 'upload.staff_options',
    'upload.preferences', 'upload.prepare', 'upload.finish_review',
    'upload.confirm_login', 'upload.reconcile',
  ];

  const VERSION_ERRORS = new Set([
    'command_unknown', 'unsupported_workflow_version',
    'unsupported_contract_version',
  ]);

  function withVersion(payload) {
    return Object.assign({ workflow_version: WORKFLOW_VERSION }, payload || {});
  }

  // Capability theo contract §9: module registry phai cong bo
  // 'upload.workflow.v1'. Tra null khi registry chua co truong capabilities
  // (backend qua doi) — consumer van thu goi va degrade qua websites job.
  function hasWorkflowCapability(mod) {
    if (!mod) return false;
    if (!Array.isArray(mod.capabilities)) return null;
    return mod.capabilities.includes(WORKFLOW_VERSION);
  }

  function isTerminal(job) {
    return !!job && ['succeeded', 'failed', 'canceled', 'partial']
      .includes(job.status);
  }

  function isSuccess(job) {
    return !!job &&
      (job.status === 'succeeded' || job.status === 'partial') &&
      !!job.result;
  }

  function jobData(job) {
    return (job && job.result && job.result.data) || null;
  }

  // Job moi nhat theo updated_at cua mot command — ket qua cu hon khong bao
  // gio len mat na ket qua moi (nhanh poll nhieu lan chi doc job moi nhat).
  function latestJob(jobs, command) {
    let best = null;
    for (const j of jobs.values()) {
      if (!j || j.command !== command) continue;
      if (!best ||
          String(j.updated_at || '') > String(best.updated_at || '')) {
        best = j;
      }
    }
    return best;
  }

  function markSaved(state, ids) {
    for (const id of (ids || []).map(Number)) {
      state.savedIds.add(id);
      state.selectedIds.delete(id);
      state.needsReconcileIds.delete(id);
    }
    // Ho so da xac minh Luu roi khoi bang hien thi (spec §3).
    if (state.queue && Array.isArray(state.queue.folder_rows)) {
      const rows = state.queue.folder_rows
        .filter((r) => !state.savedIds.has(Number(r.record_id)));
      state.queue = Object.assign({}, state.queue, { folder_rows: rows });
      state.rowIds = new Set(rows.map((r) => Number(r.record_id)));
    }
  }

  function addReconcile(state, ids) {
    for (const id of (ids || []).map(Number)) {
      state.needsReconcileIds.add(id);
    }
  }

  function trackProgress(state, job) {
    // Hai thanh tien do rieng: quet va chuan bi bieu mau (spec §3).
    if (job.job_id === state.scanJobId) {
      state.scanProgress = isTerminal(job)
        ? null
        : (job.progress || { done: 0, total: null });
    }
    if (job.job_id === state.prepareJobId) {
      state.prepareProgress = isTerminal(job)
        ? null
        : (job.progress || { done: 0, total: null });
    }
    if (!isTerminal(job) && job.status === 'waiting_user' && job.waiting_on) {
      // Banner chi pin khi job thuoc scope hien tai — job waiting cua
      // website/run cu (du lieu bi tu choi) khong duoc hien banner.
      const d = jobData(job);
      const inScope = S.activeJobIds(state).has(job.job_id) ||
        (d && S.acceptScopedResult(state, {
          websiteId: d.website_id, runId: d.run_id,
          browserId: d.browser_id,
        }));
      if (inScope) {
        state.waitingBanner = { on: job.waiting_on, jobId: job.job_id };
      }
    } else if (state.waitingBanner &&
               state.waitingBanner.jobId === job.job_id) {
      state.waitingBanner = null;
    }
  }

  // Ap mot job snapshot vao state. Tra true khi state thay doi.
  // Ham nay la cong duy nhat ket qua di vao — moi scope check tap trung o day.
  function adoptJobResult(state, job) {
    if (!state || !job || typeof job.command !== 'string') return false;
    const cmd = job.command;
    const d = jobData(job);
    trackProgress(state, job);

    switch (cmd) {
      case 'upload.websites': {
        if (isSuccess(job) && d) {
          state.websites = Array.isArray(d.websites) ? d.websites : [];
          if (!state.websiteId && d.selected_website_id) {
            state.websiteId = d.selected_website_id;
          }
          state.workflowReady = true;
          return true;
        }
        if (isTerminal(job) && job.error &&
            VERSION_ERRORS.has(job.error.code)) {
          state.workflowReady = false;
          return true;
        }
        return false;
      }

      case 'upload.workspace_get': {
        if (!isSuccess(job) || !d || !d.website_id) return false;
        // Workspace cua website khac (result cu den muon) → bo qua.
        if (state.websiteId && d.website_id !== state.websiteId) return false;
        if (!state.websiteId) S.setWebsite(state, d.website_id, d);
        else S.applyWorkspace(state, d);
        return true;
      }

      case 'upload.website_select': {
        // Result la workspace cua website MOI — chi rang buoc job, website
        // dich kiem qua pendingWebsiteId.
        if (!S.acceptScopedResult(state, { jobId: job.job_id })) return false;
        if (isSuccess(job) && d && d.website_id) {
          if (state.pendingWebsiteId &&
              d.website_id !== state.pendingWebsiteId) return false;
          S.setWebsite(state, d.website_id, d);
          state.pendingWebsiteId = null;
          return true;
        }
        if (isTerminal(job)) {
          // Bi tu choi (workflow_busy/stale_revision/unknown_website):
          // giu nguyen website cu, bo cho.
          state.pendingWebsiteId = null;
          return true;
        }
        return false;
      }

      case 'upload.env_check': {
        if (!S.acceptScopedResult(state, {
          websiteId: d && d.website_id, jobId: job.job_id,
        })) return false;
        if (isSuccess(job) && d) {
          state.envCheck = d;
          return true;
        }
        if (isTerminal(job) && job.error) {
          state.envCheck = { status: 'blocked', steps: [], error: job.error };
          return true;
        }
        return false;
      }

      case 'upload.session_start':
      case 'upload.session_status': {
        if (!d) return false;
        if (!S.acceptScopedResult(state, {
          websiteId: d.website_id, browserId: d.browser_id,
        })) return false;
        if (d.browser_id) state.browserId = d.browser_id;
        if (d.login) state.login = d.login;
        if (d.tabs) state.sessionTabs = d.tabs;
        if (d.staff_options &&
            Array.isArray(d.staff_options.cong_chung_vien)) {
          state.staff.options = d.staff_options.cong_chung_vien;
        }
        state.uploadSessionActive = true;
        return true;
      }

      case 'upload.session_close': {
        if (!d || !S.acceptScopedResult(state, {
          websiteId: d.website_id, browserId: d.browser_id,
        })) return false;
        state.uploadSessionActive = false;
        if (Array.isArray(d.verified_record_ids)) {
          markSaved(state, d.verified_record_ids);
        }
        if (Array.isArray(d.needs_reconcile_record_ids)) {
          addReconcile(state, d.needs_reconcile_record_ids);
        }
        return true;
      }

      case 'upload.download_export': {
        if (!S.acceptScopedResult(state, {
          websiteId: d && d.website_id, jobId: job.job_id,
        })) return false;
        if (isSuccess(job) && d && d.file_ref) {
          state.excelFile = d.file_ref;
          state.downloadedExport = d;
          return true;
        }
        return false;
      }

      case 'upload.audit_excel': {
        if (!S.acceptScopedResult(state, {
          websiteId: d && d.website_id, jobId: job.job_id,
        })) return false;
        if (isSuccess(job) && d) {
          state.audit = d;
          if (d.audit_id) state.auditId = d.audit_id;
          state.hasExcel = true;
          state.auditStale = false;
          state.auditError = null;
          // So hop le thay doi → queue phai fetch lai theo audit moi.
          state.queueFor = null;
          return true;
        }
        if (isTerminal(job) && job.error) {
          // Nap loi: bao ro tai cho, KHONG giu so lieu cu (spec §2).
          state.audit = null;
          state.auditStale = false;
          state.auditError = job.error;
          return true;
        }
        if (isTerminal(job)) {
          // Terminal khong error (vd. canceled/khong result): so lieu cu
          // khong con mo ta bo loc hien tai — xoa de khong hien bao cao cu.
          state.audit = null;
          state.auditStale = false;
          state.auditError = {
            code: `job_${job.status}`,
            message: job.status === 'canceled'
              ? 'Đã hủy nạp dữ liệu Excel.'
              : 'Nạp dữ liệu Excel không hoàn tất.',
            retryable: true,
            next_action: 'retry',
          };
          return true;
        }
        return false;
      }

      case 'upload.scan': {
        if (!isSuccess(job) || !d) return false;
        if (!S.acceptScopedResult(state, {
          websiteId: d.website_id, jobId: job.job_id,
        })) return false;
        const newRun = d.run_id;
        if (newRun !== state.runId) {
          // Luot quet moi: bo ID da chon cua luot cu (spec §3).
          S.resetScanContext(state, newRun);
        }
        state.runId = newRun;
        state.manifestRef = d.manifest_ref || null;
        state.scanStats = d.stats || null;
        if (d.revision != null) state.revision = d.revision;
        state.scanProgress = null;
        return true;
      }

      case 'upload.queue_get': {
        if (!isSuccess(job) || !d) return false;
        if (!S.acceptScopedResult(state, {
          websiteId: d.website_id, runId: d.run_id, jobId: job.job_id,
        })) return false;
        S.applyQueue(state, d, { preserveSelection: true });
        return true;
      }

      case 'upload.staff_options': {
        if (!isSuccess(job) || !d ||
            !S.acceptScopedResult(state, { websiteId: d.website_id })) {
          return false;
        }
        state.staff.options = d.cong_chung_vien || [];
        state.staffSource = d.source || null;
        return true;
      }

      case 'upload.preferences': {
        if (!isSuccess(job) || !d ||
            !S.acceptScopedResult(state, { websiteId: d.website_id })) {
          return false;
        }
        if (d.chunk_size != null) state.chunkSize = S.clampChunk(d.chunk_size);
        if (d.cong_chung_vien !== undefined) {
          state.staff.congChungVien = d.cong_chung_vien;
        }
        if (d.thu_ky !== undefined) state.staff.thuKy = d.thu_ky;
        return true;
      }

      case 'upload.prepare': {
        if (!d || !S.acceptScopedResult(state, {
          websiteId: d.website_id, runId: d.run_id, jobId: job.job_id,
        })) return false;
        const sum = d.summary || {};
        if (sum.remaining != null) state.remaining = sum.remaining;
        if (Array.isArray(d.saved_record_ids)) {
          markSaved(state, d.saved_record_ids);
        }
        if (Array.isArray(d.needs_reconcile_record_ids)) {
          addReconcile(state, d.needs_reconcile_record_ids);
        }
        state.uploadSessionActive = true;
        return true;
      }

      case 'upload.confirm_login':
      case 'upload.finish_review': {
        if (!d || !S.acceptScopedResult(state, {
          websiteId: d.website_id, browserId: d.browser_id,
        })) return false;
        return true;
      }

      case 'upload.reconcile': {
        if (!isSuccess(job) || !d || !S.acceptScopedResult(state, {
          websiteId: d.website_id, runId: d.run_id,
        })) return false;
        if (Array.isArray(d.verified_record_ids)) {
          markSaved(state, d.verified_record_ids);
        }
        if (Array.isArray(d.needs_reconcile_record_ids)) {
          addReconcile(state, d.needs_reconcile_record_ids);
        }
        return true;
      }

      default:
        return false;
    }
  }

  // Quet moi nhat cua tung command trong jobs map vao state.
  function adoptJobs(state, jobs) {
    let changed = false;
    for (const cmd of TRACKED_COMMANDS) {
      const j = latestJob(jobs, cmd);
      if (j && adoptJobResult(state, j)) changed = true;
    }
    return changed;
  }

  // Job upload dang con chay (accepted/running/waiting_user/checking) trong
  // pham vi job tracker — dung cho nut Dung va trang thai busy.
  function runningJobs(state, jobs) {
    const ids = S.activeJobIds(state);
    const out = [];
    for (const j of jobs.values()) {
      if (j && ids.has(j.job_id) && !isTerminal(j)) out.push(j);
    }
    return out;
  }

  const API = {
    WORKFLOW_VERSION, TRACKED_COMMANDS, VERSION_ERRORS,
    withVersion, hasWorkflowCapability, isTerminal, isSuccess, jobData,
    latestJob, adoptJobResult, adoptJobs, runningJobs, markSaved, addReconcile,
  };

  if (typeof window !== 'undefined') {
    window.G1_UPLOAD = window.G1_UPLOAD || {};
    window.G1_UPLOAD.client = API;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
  }
})();
