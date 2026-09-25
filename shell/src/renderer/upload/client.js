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
  // updated_at chi co do phan giai giay — hai job xong trong cung mot giay
  // hoa nhau; khi do job SUBMIT SAU (di vao map muon hon = y dinh moi hon)
  // thang, nen dung >= thay vi >.
  function latestJob(jobs, command) {
    let best = null;
    for (const j of jobs.values()) {
      if (!j || j.command !== command) continue;
      if (!best ||
          String(j.updated_at || '') >= String(best.updated_at || '')) {
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

  // Danh dau queue cu sau mot job lam doi queue backend (saved/prepared/
  // reconcile/close) → derive fetch lai DUNG MOT LAN cho moi job. adoptJobs
  // chay lai tren MOI refresh — reset queueFor vo dieu kien o day se tao
  // vong: queue_get ap queueFor roi chinh job cu xoa lai ngay trong cung
  // nhip → queueReady khong bao gio len + queue_get bi resubmit vo han.
  function staleQueueOnce(state, job) {
    if (!job || state.queueStaleFor === job.job_id) return;
    state.queueStaleFor = job.job_id;
    state.queueFor = null;
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
      // Snapshot {done,total,current_label} (jobstore) — cap nhat "con lai"
      // ngay trong luc prepare chay/cho review de nut Tiep tuc phan anh dung
      // so dot sau truoc khi job terminal.
      if (!isTerminal(job) && job.progress &&
          typeof job.progress.total === 'number') {
        state.remaining = Math.max(
          0, job.progress.total - (job.progress.done || 0));
      }
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
          // Catalog tai xong KE CA KHI rong — derive() gate tren co nay,
          // khong tren websites.length (catalog rong la ket qua hop le,
          // khong phai ly do submit lai).
          state.catalogLoaded = true;
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
        // Ap DUNG MOT LAN cho moi job: snapshot ws la trang thai TAI THOI
        // DIEM chay — re-adopt tren moi refresh se keo lui browser_id/run_id
        // /audit_id ve gia tri luc snapshot, de mat binding vua tao.
        if (state.wsAppliedFor === job.job_id) return false;
        // Marker phai ghi SAU setWebsite: clearWebsiteScope (khi doi
        // website) xoa wsAppliedFor — ghi truoc thi marker bi xoa ngay,
        // nhip refresh sau ap lai snapshot mot lan nua.
        if (!state.websiteId) S.setWebsite(state, d.website_id, d);
        else S.applyWorkspace(state, d);
        state.wsAppliedFor = job.job_id;
        state.wsTried = true;  // co snapshot workspace — khoi restore job
        return true;
      }

      case 'upload.website_select': {
        // Result la workspace cua website MOI — chi rang buoc job, website
        // dich kiem qua pendingWebsiteId.
        if (!S.acceptScopedResult(state, { jobId: job.job_id })) return false;
        if (isSuccess(job) && d && d.website_id) {
          if (state.pendingWebsiteId &&
              d.website_id !== state.pendingWebsiteId) {
            // Job terminal nhung backend tra website KHAC website dich:
            // phai mo khoa pending + bao loi — neu khong pendingWebsiteId
            // ket mai, dropdown khoa va banner "Dang doi website" treo.
            const retryTarget = state.pendingWebsiteId;
            state.pendingWebsiteId = null;
            state.siteError = {
              code: 'website_mismatch',
              message: `Backend trả website ${d.website_id}, không phải ` +
                `${retryTarget} đã chọn.`,
              retryable: true,
              next_action: 'retry',
              _retry: { kind: 'website', websiteId: retryTarget },
            };
            return true;
          }
          // Snapshot workspace cua website moi — ap mot lan/job, re-adopt
          // tren moi refresh se keo lui browser/run/audit ve thoi diem select.
          if (state.siteAppliedFor === job.job_id) return false;
          // Marker SAU setWebsite (clearWebsiteScope xoa siteAppliedFor —
          // ghi truoc thi nhip sau ap lai). pendingWebsiteId/siteError cung
          // phai xoa SAU vi setWebsite->clearWebsiteScope da reset chung.
          S.setWebsite(state, d.website_id, d);
          state.siteAppliedFor = job.job_id;
          state.pendingWebsiteId = null;
          state.siteError = null;
          state.wsTried = true;  // snapshot moi nhat da ap — khoi wsGet restore
          return true;
        }
        if (isTerminal(job)) {
          // Bi tu choi (workflow_busy/stale_revision/unknown_website):
          // giu nguyen website cu, bo cho; loi hien canh nut chon (spec §4
          // — khong giu so lieu cu duoi ten moi, cung khong im lang).
          const retryTarget = state.pendingWebsiteId;
          state.pendingWebsiteId = null;
          if (job.error) {
            state.siteError = Object.assign({}, job.error, {
              _retry: retryTarget
                ? { kind: 'website', websiteId: retryTarget } : null,
            });
          }
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

      case 'upload.session_start': {
        if (!d) {
          // Job terminal khong result (failed/canceled) → bao loi ngay
          // canh nut Mo dang nhap, khong chi o the Job duoi cung.
          if (isTerminal(job) && job.error &&
              S.acceptScopedResult(state, { jobId: job.job_id })) {
            state.siteError = Object.assign({}, job.error, {
              _retry: { kind: 'session' },
            });
            return true;
          }
          if (isTerminal(job) && !job.error &&
              S.acceptScopedResult(state, { jobId: job.job_id })) {
            state.siteError = {
              code: `job_${job.status}`,
              message: job.status === 'canceled'
                ? 'Đã hủy mở đăng nhập.'
                : 'Mở đăng nhập không hoàn tất.',
              retryable: true, next_action: 'retry',
              _retry: { kind: 'session' },
            };
            return true;
          }
          return false;
        }
        // session_start la nguon uy tin cua browser_id — scope theo job
        // (job phai la job da track / workspace bao dang song) + website,
        // KHONG theo browserId: ket qua nay la cho tao ra binding do, neu
        // doi browserId da co thi phien dau tien khong bao gio ap duoc.
        if (!S.acceptScopedResult(state, {
          websiteId: d.website_id, jobId: job.job_id,
        })) return false;
        // Result terminal la snapshot tai thoi diem phien tao — ap mot lan
        // duy nhat, re-adopt tren moi refresh se keo lui revision/login ve
        // thoi diem do sau khi audit/scan da bump revision xa hon.
        if (isTerminal(job)) {
          if (state.sessionAppliedFor === job.job_id) return false;
          state.sessionAppliedFor = job.job_id;
        }
        if (d.browser_id) state.browserId = d.browser_id;
        if (d.login) state.login = d.login;
        if (d.tabs) state.sessionTabs = d.tabs;
        if (d.staff_options &&
            Array.isArray(d.staff_options.cong_chung_vien)) {
          state.staff.options = d.staff_options.cong_chung_vien;
        }
        // session_start bump revision (binding browser moi) — revision la
        // bo dem global don dieu: chi ap khi moi hon, khong bao gio lui.
        if (d.revision != null && Number(d.revision) > state.revision) {
          state.revision = Number(d.revision);
        }
        // Session vua tao → active tru khi result chinh no bao da dong.
        state.uploadSessionActive =
          !(d.login && d.login.status === 'closed');
        state.siteError = null;
        return true;
      }

      case 'upload.session_status': {
        if (!d) return false;
        if (!S.acceptScopedResult(state, {
          websiteId: d.website_id, browserId: d.browser_id,
        })) return false;
        if (d.browser_id) state.browserId = d.browser_id;
        if (d.login) {
          // Poll doc snapshot lien tuc — mot nhip ve TRE hon xac nhan
          // session_start co the mang trang thai pre-auth. Snapshot co
          // checked_at KHONG moi hon hien tai khong duoc ha
          // 'authenticated' xuong; snapshot moi hon (vd. het han phien,
          // dong browser) van ap binh thuong.
          const cur = state.login;
          const inAt = d.login.checked_at || '';
          const curAt = (cur && cur.checked_at) || '';
          const regresses = cur && cur.status === 'authenticated' &&
            d.login.status !== 'authenticated' &&
            (!inAt || !curAt || inAt <= curAt);
          if (!regresses) state.login = d.login;
        }
        if (d.tabs) {
          state.sessionTabs = d.tabs;
          state.openTabIds = new Set(d.tabs.open_record_ids || []);
          // Save-awareness trong luc cho review: tab nguoi dung da bam Luu
          // (POST da xac minh) roi bang ngay; tab dong/mat dau → can doi
          // chieu — mirror store phia backend (_update_snapshot).
          markSaved(state, d.tabs.saved_record_ids);
          addReconcile(state, [
            ...(d.tabs.closed_record_ids || []),
            ...(d.tabs.unknown_record_ids || []),
          ]);
        }
        if (d.staff_options &&
            Array.isArray(d.staff_options.cong_chung_vien)) {
          state.staff.options = d.staff_options.cong_chung_vien;
        }
        // Active theo login hieu luc SAU merge (regresses guard o tren):
        // snapshot 'closed' cu khong duoc ha phien dang authenticated.
        state.uploadSessionActive =
          !(state.login && state.login.status === 'closed');
        return true;
      }

      case 'upload.session_close': {
        if (!d || !S.acceptScopedResult(state, {
          websiteId: d.website_id, browserId: d.browser_id,
        })) return false;
        state.uploadSessionActive = false;
        state.sessionTabs = null;
        state.openTabIds = new Set();
        if (Array.isArray(d.verified_record_ids)) {
          markSaved(state, d.verified_record_ids);
        }
        if (Array.isArray(d.needs_reconcile_record_ids)) {
          addReconcile(state, d.needs_reconcile_record_ids);
        }
        // Qt _handle_upload_closed: het phien → het dot tiep theo; tab con
        // mo da chuyen needs_reconcile → queue doi → fetch lai MOT LAN de
        // queue_revision gui dot sau luon tuoi (chong stale_revision).
        state.remaining = 0;
        state.prepareRetryIds = null;  // phien dong — retry dang cho chet theo
        staleQueueOnce(state, job);
        return true;
      }

      case 'upload.download_export': {
        if (!S.acceptScopedResult(state, {
          websiteId: d && d.website_id, jobId: job.job_id,
        })) return false;
        if (isSuccess(job) && d && d.file_ref) {
          // Ap file_ref DUNG MOT LAN cho moi job: re-adopt tren cac nhip
          // refresh sau khong duoc ghi de file nguoi dung da chon lai.
          if (state.downloadAppliedFor === job.job_id) return false;
          state.downloadAppliedFor = job.job_id;
          state.excelFile = d.file_ref;
          state.downloadedExport = d;
          state.downloadError = null;
          // File tai ve ung voi khoang ngay luc tai — neu nguoi dung doi
          // ngay trong luc tai thi ket qua/file nay khong con "moi nhat".
          if ((d.from_date && d.from_date !== state.fromDate) ||
              (d.to_date && d.to_date !== state.toDate)) {
            S.markAuditStale(state);
          }
          return true;
        }
        if (isTerminal(job) && job.error) {
          // Tai loi: bao tai vung Nguon so (spec §4 — huong dan hanh dong).
          state.downloadError = job.error;
          return true;
        }
        if (isTerminal(job)) {
          state.downloadError = {
            code: `job_${job.status}`,
            message: job.status === 'canceled'
              ? 'Đã hủy tải sổ từ website.'
              : 'Tải sổ từ website không hoàn tất.',
            retryable: true,
            next_action: 'retry',
          };
          return true;
        }
        return false;
      }

      case 'upload.audit_excel': {
        if (!S.acceptScopedResult(state, {
          websiteId: d && d.website_id, jobId: job.job_id,
        })) return false;
        if (isSuccess(job) && d) {
          // Ap DUNG MOT LAN cho moi job: audit result dung im sau do —
          // re-adopt khong duoc reset queueFor (se tao vong queue_get vo
          // han) hay xoa nhan "chua cap nhat" nguoi dung vua tao bang cach
          // doi ngay/file.
          if (state.auditAppliedFor === job.job_id) return false;
          const prevAuditId = state.auditId;
          state.auditAppliedFor = job.job_id;
          state.audit = d;
          if (d.audit_id) state.auditId = d.audit_id;
          // audit_excel bump revision phia backend — revision global don
          // dieu: chi ap khi moi hon, khong bao gio lui.
          if (d.revision != null && Number(d.revision) > state.revision) {
            state.revision = Number(d.revision);
          }
          state.hasExcel = true;
          state.auditError = null;
          // Result mo ta bo loc/file LUC CHAY — neu nguoi dung doi ngay
          // hoac chon file khac giua luc audit dang chay, ket qua nay khong
          // con la "ket qua cua bo loc moi": danh dau chua cap nhat (spec
          // §2 — khong dung ket qua cu nhu ket qua cua bo loc moi).
          const sameRange =
            (!d.from_date || d.from_date === state.fromDate) &&
            (!d.to_date || d.to_date === state.toDate);
          const srcFiles = (job.result && job.result.source_files) || [];
          const srcPath = srcFiles[0] && srcFiles[0].path;
          const curPath = state.excelFile && state.excelFile.path;
          const sameFile = !srcPath || !curPath ||
            String(srcPath).toLowerCase() === String(curPath).toLowerCase();
          state.auditStale = !(sameRange && sameFile);
          // So hop le thay doi → queue phai fetch lai theo audit moi (chi
          // khi audit_id that su doi — trah vong refetch vo han).
          if (d.audit_id && d.audit_id !== prevAuditId) state.queueFor = null;
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
        if (d.revision != null && Number(d.revision) > state.revision) {
          state.revision = Number(d.revision);
        }
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
        if (!d) {
          // Terminal khong result (scope_violation/stale_revision/login...)
          // → hien loi tai cho, KHONG nuot vao the Job duoi cung. Job
          // canceled LUON mang error user_canceled → phai bat truoc nhanh
          // error de "Dung" cua nguoi dung khong bi hien nhu dot that bai.
          if (isTerminal(job) &&
              S.acceptScopedResult(state, { jobId: job.job_id })) {
            if (job.status === 'canceled') {
              state.prepareError = null;
            } else if (job.error) {
              state.prepareError = job.error;
              if (job.error.code === 'stale_revision') {
                // Queue backend da doi — fetch lai MOT LAN/job de retry
                // mang revision moi.
                staleQueueOnce(state, job);
                // Hanh dong nguoi dung bi tu choi chi vi race revision —
                // khong phai loi du lieu. Backend chi dan "doc lai
                // queue_get": khi queue moi ap xong, derive() gui lai
                // DUNG TAP ids da submit. prepareRetryOf chan re-arm tren
                // chinh job retry — toi da mot lan tu dong cho moi click.
                if (state.prepareRetryOf !== job.job_id &&
                    Array.isArray(state.lastPrepareIds)) {
                  state.prepareRetryIds = [...state.lastPrepareIds];
                }
              }
            }
            return true;
          }
          return false;
        }
        if (!S.acceptScopedResult(state, {
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
        if (isSuccess(job)) {
          state.uploadSessionActive = true;
          // Partial = co muc loi trong dot — hien breakdown, khong nuot.
          state.prepareError =
            (job.error && job.error.code === 'upload.partial_failure')
              ? job.error : null;
        } else if (job.status === 'canceled') {
          // Nguoi dung tu Dung — khong phai loi; KHONG tu chay dot tiep.
          state.prepareError = null;
        } else if (job.error) {
          state.prepareError = job.error;
          if (job.error.code === 'stale_revision' &&
              state.prepareRetryOf !== job.job_id &&
              Array.isArray(state.lastPrepareIds)) {
            state.prepareRetryIds = [...state.lastPrepareIds];
          }
        }
        // Queue revision da doi (saved/prepared/needs_reconcile) → fetch lai
        // queue MOT LAN/job de queue_revision gui dot tiep theo luon tuoi.
        staleQueueOnce(state, job);
        return true;
      }

      case 'upload.confirm_login':
      case 'upload.finish_review': {
        if (!d) {
          // Xac nhan sai job/scope (wrong_job) hoac that bai khac → hien
          // loi canh nut dang nhap/kiem tra, khong nuot vao the Job.
          if (isTerminal(job) && job.error &&
              S.acceptScopedResult(state, { jobId: job.job_id })) {
            state.siteError = Object.assign({}, job.error, {
              _retry: { kind: job.command === 'upload.confirm_login'
                        ? 'confirm' : 'review' },
            });
            return true;
          }
          return false;
        }
        if (!S.acceptScopedResult(state, {
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
        // Da xac minh them muc → queue doi → fetch lai MOT LAN/job.
        staleQueueOnce(state, job);
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
