'use strict';

// Upload Lab — module view (MIN-69, task 6).
// Khung hai tab full-width + state dung chung; renderer.js chi goi
// G1_UPLOAD.buildView(deps) va truyen api/jobs/notify/helper qua tham so.
// Hai tabpanel la DOM persistent — doi tab chi toggle `hidden`, khong huy
// form/selection/scroll; vi tri cuon #view luu trong state.tabs[*].

(function () {
  const NS = (typeof window !== 'undefined')
    ? (window.G1_UPLOAD = window.G1_UPLOAD || {}) : null;
  if (!NS) return;

  function scrollBoxFor(sectionEl) {
    return (sectionEl && sectionEl.parentElement) ||
      document.getElementById('view');
  }

  // Cap nhat tbody theo khoa — KHONG dung lai toan bo bang moi nhip poll:
  // giu DOM node/scroll/focus cua cac dong khong doi.
  function syncTbody(h, tbody, rows, keyOf, renderRow, emptyText) {
    if (!rows.length) {
      const tr = h.el('tr');
      // Khoa sentinel: lan goi non-empty sau do placeholder vao byKey va bi
      // xoa nhu moi dong cu — khong de "(trong)" nam lai tren du lieu that.
      tr.dataset.k = '__empty__';
      const td = h.el('td', 'muted', emptyText || '—');
      td.colSpan = 20;
      tr.append(td);
      tbody.replaceChildren(tr);
      return;
    }
    const byKey = new Map();
    for (const tr of Array.from(tbody.children)) {
      if (tr.dataset && tr.dataset.k != null) byKey.set(tr.dataset.k, tr);
      else tr.remove(); // node khong khoa (placeholder cu) khong duoc nam lai
    }
    const order = [];
    rows.forEach((row, idx) => {
      const k = String(keyOf(row, idx));
      let tr = byKey.get(k);
      if (tr) {
        byKey.delete(k);
        renderRow(row, tr, idx);
      } else {
        tr = renderRow(row, null, idx);
        tr.dataset.k = k;
      }
      order.push(tr);
    });
    for (const tr of byKey.values()) tr.remove();
    for (const tr of order) tbody.appendChild(tr);
  }

  NS.buildView = function (deps) {
    const {
      api, L, jobs, notify, h, entry, module: mod, submit,
      engineInstanceId,
    } = deps;
    const S = NS.state;
    const C = NS.client;
    const state = S.createUploadState();
    const inflight = {};
    let booted = false;
    let lastSessPoll = 0;
    let sessPollTimer = null;

    const s = h.el('section', 'upload-lab');
    const head = h.el('div', 'ul-head');
    head.append(h.el('h2', 'ul-title', 'Upload Lab'));
    head.append(h.el('span', 'ul-sub muted',
      'Số hóa hồ sơ Word, audit sổ công chứng, chuẩn bị biểu mẫu ' +
      '(dry-run — người dùng tự Lưu trong Chromium).'));
    s.append(head);
    const engSlot = h.el('div', 'ul-eng');
    s.append(engSlot);
    const noticeBox = h.el('div', 'ul-notice');
    s.append(noticeBox);

    // ---------- tablist (ARIA) ----------
    const tablist = h.el('div', 'ul-tablist');
    tablist.setAttribute('role', 'tablist');
    tablist.setAttribute('aria-label', 'Upload Lab');
    const tabEls = {};
    for (const t of S.TABS) {
      const b = h.el('button', 'ul-tab', t.label);
      b.type = 'button';
      b.id = `ul-tab-${t.id}`;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', 'false');
      b.setAttribute('aria-controls', `ul-panel-${t.id}`);
      b.tabIndex = -1;
      b.addEventListener('click', () => switchTab(t.id));
      tabEls[t.id] = b;
      tablist.append(b);
    }
    s.append(tablist);

    // ---------- command helpers ----------
    async function quiet(command, payload) {
      // Query/doc: loi chi hien qua empty state, khong toast.
      const r = await api.submitCommand(
        command, C.withVersion(payload), crypto.randomUUID());
      if (!r.ok) return { ok: false, error: r.error };
      jobs.set(r.data.job_id, r.data);
      return { ok: true, job: r.data };
    }

    async function loud(command, payload) {
      // Thao tac nguoi dung: submit cua renderer (toast loi + retry payload).
      const job = await submit(
        command, C.withVersion(payload), crypto.randomUUID());
      return job || null;
    }

    // Co job cung command con song (non-terminal: accepted/running/checking/
    // waiting_user) trong jobs map → derive KHONG submit trung; cho ket qua
    // hoac cho job chet han roi retry paced moi duoc tao job moi.
    function liveJob(command) {
      for (const j of jobs.values()) {
        if (j && j.command === command && !C.isTerminal(j)) return true;
      }
      return false;
    }

    // Submit upload.prepare cho mot tap ids — dung chung cho ca ba nguon:
    // nut "Upload file da chon", "Tiep tuc" va auto-retry stale_revision.
    // Ghi nhan lastPrepareIds de loi stale_revision con biet tap can gui lai.
    async function submitPrepareIds(ids) {
      const job = await loud('upload.prepare', {
        website_id: state.websiteId, browser_id: state.browserId,
        run_id: state.runId, audit_id: state.auditId,
        queue_revision: state.queueRevision,
        record_ids: ids,
        chunk_size: state.chunkSize,
        cong_chung_vien: state.staff.congChungVien || null,
        thu_ky: state.staff.thuKy || null,
      });
      if (job) {
        state.prepareJobId = job.job_id;
        state.lastPrepareIds = [...ids];
        state.prepareError = null;
      }
      return job;
    }

    async function bootstrap() {
      try {
        const cap = C.hasWorkflowCapability(mod);
        if (cap === false) {
          state.workflowReady = false;
          return;
        }
      } catch (e) {
        // Bootstrap im lang — UI hien empty state, khong vo module.
      }
    }

    // Fetch dan xuat khi ngu canh doi — moi submit duoc guard bang
    // inflight flag + moc queueFor/prefsTried/staffTried de khong lap vo han.
    function derive() {
      if (state.workflowReady === false) return;
      // Sidecar restart = engine_instance_id moi: catalog co the da thay
      // doi luc engine chet → refetch mot lan. Chi reset khi da tung thay
      // instance (boot lan dau chi ghi nhan), va bo qua giai doan engine
      // down (instance null) de khong flap.
      const inst = typeof engineInstanceId === 'function'
        ? engineInstanceId() : null;
      if (inst && inst !== state.engineInstanceId) {
        if (state.engineInstanceId) state.catalogLoaded = false;
        state.engineInstanceId = inst;
      }
      // Catalog bootstrap — chay trong derive (moi refresh) de tu thu lai
      // khi submit fail luc sidecar chua ready; VERSION_ERRORS (backend
      // qua cu, khong co workflow) la tat dinh → dung han. Gate tren
      // catalogLoaded (job upload.websites da succeeded), KHONG tren
      // websites.length — catalog rong hay job failed deu khong duoc
      // resubmit nong; job non-terminal con song cung khong bi chong.
      if (!state.catalogLoaded && !inflight.catalog &&
          !liveJob('upload.websites')) {
        inflight.catalog = true;
        // Submit fail tam thoi (sidecar chua ready khi module mo): hen
        // refresh lai bang timer vi refreshAll chi chay khi status doi —
        // khong co poll dinh ky nao goi lai derive. Giu inflight trong
        // thoi gian cho de tranh vong submit lap tuc. awaitJob chi tinh
        // SUCCEEDED la xong — failed/timeout/waiting_user di qua retry
        // paced 4s (khong resubmit nong tao vong lap job).
        const release = () => { inflight.catalog = false; view.refresh(); };
        const retry = () => {
          // unref khi co (node --test): timer retry khong duoc giu process
          // song — trong browser setTimeout tra number, khong co unref.
          const t = setTimeout(release, 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.websites', {})
          .then((r) => {
            if (r.ok) {
              return h.awaitJob(r.job.job_id, 30000)
                .then((j) => !!(j && j.status === 'succeeded'));
            }
            if (r.error && C.VERSION_ERRORS.has(r.error.code)) {
              state.workflowReady = false;
              return true;
            }
            return false;
          })
          .then((done) => { if (done) release(); else retry(); })
          .catch(retry);
        return;
      }
      // Workspace ban dau (khoi phuc website/run/browser da luu) — cung
      // pattern retry: submit fail khi sidecar chua ready phai duoc thu lai.
      // wsTried chi len khi job SUCCEEDED — failed/timeout khong duoc
      // khoa co che phuc hoi cho den lan doi website sau.
      if (!inflight.ws && !state.wsTried && state.websiteId &&
          !liveJob('upload.workspace_get')) {
        inflight.ws = true;
        const release = (ok) => {
          if (ok) state.wsTried = true;
          inflight.ws = false;
          view.refresh();
        };
        const retry = () => {
          const t = setTimeout(() => release(false), 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.workspace_get', { website_id: state.websiteId })
          .then((r) => (r.ok ? h.awaitJob(r.job.job_id, 30000)
            .then((j) => !!(j && j.status === 'succeeded')) : false))
          .then((done) => { if (done) release(true); else retry(); })
          .catch(retry);
        return;
      }
      if (state.websiteId && state.runId &&
          (!state.queueFor || state.queueFor.runId !== state.runId ||
           state.queueFor.auditId !== state.auditId) &&
          !inflight.queue && !liveJob('upload.queue_get') &&
          Date.now() > (inflight.queueRetryAt || 0)) {
        inflight.queue = true;
        // Job terminal FAILED cung phai retry paced (4s) — khong release
        // inflight ngay de derive nhip sau resubmit nong (cung pattern
        // catalog/ws/prefs/staff). Thanh cong → release + refresh ngay.
        const release = () => { inflight.queue = false; view.refresh(); };
        const retry = () => {
          inflight.queueRetryAt = Date.now() + 4000;
          inflight.queue = false;
          const t = setTimeout(() => view.refresh(), 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.queue_get', {
          website_id: state.websiteId, run_id: state.runId,
          audit_id: state.auditId,
        }).then((r) => {
          if (r.ok) {
            state.queueJobId = r.job.job_id;
            return h.awaitJob(r.job.job_id, 30000)
              .then((j) => !!(j && j.status === 'succeeded'));
          }
          return false;
        }).then((done) => { if (done) release(); else retry(); })
          .catch(retry);
      }
      // Auto-retry DUNG MOT LAN sau stale_revision (armed trong adoptJobs):
      // queue vua duoc doc lai → gui lai dung tap ids user da submit voi
      // revision tuoi. Day la hoan tat mot hanh dong nguoi dung bi tu choi
      // vi race, KHONG phai tu chay dot moi — prepareRetryOf nganh retry
      // chong retry, scope/queue khong con tuoi thi marker bi huy im lang.
      if (state.prepareRetryIds) {
        const deadScope = !state.websiteId || !state.runId ||
          !state.browserId ||
          !(state.login && state.login.status === 'authenticated') ||
          !state.uploadSessionActive;
        const queueReady = !!(state.queueFor &&
          state.queueFor.runId === state.runId &&
          state.queueFor.auditId === state.auditId);
        if (deadScope) {
          state.prepareRetryIds = null;
        } else if (queueReady && !inflight.queue &&
                   !liveJob('upload.prepare')) {
          const ids = state.prepareRetryIds;
          state.prepareRetryIds = null;
          submitPrepareIds(ids).then((job) => {
            if (job) state.prepareRetryOf = job.job_id;
          }).catch(() => {});
        }
      }
      // Lay browser_id trong luc session_start con waiting_user — nut
      // "Xac nhan da dang nhap" can scope website+browser (contract §7.2).
      if (state.websiteId && !state.browserId &&
          state.waitingBanner && state.waitingBanner.on === 'login' &&
          !inflight.wsLogin && !liveJob('upload.workspace_get')) {
        inflight.wsLogin = true;
        // Paced retry — failed/timeout khong release ngay (vong submit
        // nong); cung pattern catalog/ws/prefs/staff.
        const release = () => { inflight.wsLogin = false; view.refresh(); };
        const retry = () => {
          const t = setTimeout(release, 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.workspace_get', { website_id: state.websiteId })
          .then((r) => (r && r.ok)
            ? h.awaitJob(r.job.job_id, 15000)
              .then((j) => !!(j && j.status === 'succeeded'))
            : false)
          .then((done) => { if (done) release(); else retry(); })
          .catch(retry);
      }
      // prefsTried/staffTried chi len khi job SUCCEEDED — submit fail tam
      // thoi hoac job failed di qua retry paced 4s, khong khoa vinh vien
      // (cung lop bug voi co catalogLoaded/wsTried da sua o tren).
      if (state.websiteId && !state.prefsTried && !inflight.prefs &&
          !liveJob('upload.preferences')) {
        inflight.prefs = true;
        const release = (ok) => {
          if (ok) state.prefsTried = true;
          inflight.prefs = false;
          view.refresh();
        };
        const retry = () => {
          const t = setTimeout(() => release(false), 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.preferences', { website_id: state.websiteId })
          .then((r) => {
            if (r.ok) {
              state.prefsJobId = r.job.job_id;
              return h.awaitJob(r.job.job_id, 30000)
                .then((j) => !!(j && j.status === 'succeeded'));
            }
            return false;
          }).then((done) => { if (done) release(true); else retry(); })
          .catch(retry);
      }
      if (state.websiteId && !state.staffTried && !inflight.staff &&
          !liveJob('upload.staff_options')) {
        inflight.staff = true;
        const release = (ok) => {
          if (ok) state.staffTried = true;
          inflight.staff = false;
          view.refresh();
        };
        const retry = () => {
          const t = setTimeout(() => release(false), 4000);
          if (t && typeof t.unref === 'function') t.unref();
        };
        quiet('upload.staff_options', {
          website_id: state.websiteId, browser_id: null, refresh: false,
        }).then((r) => {
          if (r.ok) {
            state.staffJobId = r.job.job_id;
            return h.awaitJob(r.job.job_id, 30000)
              .then((j) => !!(j && j.status === 'succeeded'));
          }
          return false;
        }).then((done) => { if (done) release(true); else retry(); })
          .catch(retry);
      }
    }

    // Poll session_status gop khi co job waiting_user (contract §7.2) —
    // throttle 4s, khong chong request. Poll phai TU DUY TRI: refresh chi
    // chay khi co push job/status — trong luc cho login/review khong con
    // push nao khac, nen nhip throttle-skip ma khong hen lai se dung poll
    // vinh vien (Save-awareness chet: hang da Luu khong bao gio roi bang).
    // Mot timer cho duy nhat; tu chain lai qua refresh cho toi khi het
    // job waiting (nhip sau waiting=false → return som, khong hen tiep).
    function scheduleSessionTick() {
      if (sessPollTimer) return;
      const t = setTimeout(() => {
        sessPollTimer = null;
        view.refresh();
      }, 1000);
      sessPollTimer = t;
      if (t && typeof t.unref === 'function') t.unref();
    }

    function maybePollSession() {
      if (!state.browserId) return;
      const waiting = C.runningJobs(state, jobs).some(
        (j) => j.status === 'waiting_user' &&
               String(j.command || '').startsWith('upload.'));
      if (!waiting) return;
      scheduleSessionTick();
      if (Date.now() - lastSessPoll < 4000) return;
      lastSessPoll = Date.now();
      quiet('upload.session_status', {
        website_id: state.websiteId, browser_id: state.browserId,
      }).then((r) => {
        if (r.ok) return h.awaitJob(r.job.job_id, 30000);
        return null;
      }).then(() => view.refresh()).catch(() => {});
    }

    // ---------- actions (handler chia cho 2 tab) ----------
    const actions = {
      requestRender: () => view.refresh(),
      switchTab: (id) => switchTab(id, true),
      gotoAudit: () => {
        switchTab('audit');
        if (panels.audit.focusWebsite) panels.audit.focusWebsite();
      },
      changeWebsite: async (id) => {
        if (!id || id === state.websiteId || state.pendingWebsiteId) return;
        state.siteError = null;
        state.pendingWebsiteId = id;
        view.refresh();
        const job = await loud('upload.website_select', {
          website_id: id, expected_revision: state.revision,
        });
        if (job) state.websiteJobId = job.job_id;
        else {
          state.pendingWebsiteId = null;
          view.refresh();
        }
      },
      envCheck: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        const job = await loud('upload.env_check',
          { website_id: state.websiteId });
        if (job) state.envJobId = job.job_id;
      },
      sessionStart: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        state.siteError = null;
        const job = await loud('upload.session_start', {
          website_id: state.websiteId, expected_revision: state.revision,
        });
        if (job) state.sessionJobId = job.job_id;
      },
      confirmLogin: async () => {
        // Xac nhan "toi da dang nhap" cho job session_start dang
        // waiting_user — can scope website+browser+job dich (contract §7.2).
        const target = (state.waitingBanner &&
          state.waitingBanner.on === 'login')
          ? state.waitingBanner.jobId : state.sessionJobId;
        if (!state.websiteId || !state.browserId || !target) {
          notify('Chưa có phiên đăng nhập đang chờ.', true);
          return;
        }
        state.siteError = null;
        const job = await loud('upload.confirm_login', {
          website_id: state.websiteId, browser_id: state.browserId,
          target_job_id: target,
        });
        if (job) state.confirmJobId = job.job_id;
      },
      finishReview: async () => {
        const target = (state.waitingBanner &&
          state.waitingBanner.on === 'review')
          ? state.waitingBanner.jobId : state.prepareJobId;
        if (!state.websiteId || !state.browserId || !target) {
          notify('Chưa có đợt kiểm tra đang chờ.', true);
          return;
        }
        const job = await loud('upload.finish_review', {
          website_id: state.websiteId, browser_id: state.browserId,
          target_job_id: target,
        });
        if (job) state.reviewJobId = job.job_id;
      },
      pickExcel: async () => {
        // Backend chi nhan .xlsx/.xlsm (contract §6.9) — .xls bi tu choi
        // nen khong hien trong filter dialog.
        const r = await api.pickFiles({
          multi: false,
          filters: [{ name: 'Excel (.xlsx, .xlsm)',
                      extensions: ['xlsx', 'xlsm'] }],
        });
        if (!r.ok) {
          notify(`${r.error.code}: ${r.error.message}`, true);
          return;
        }
        if (!r.data.files.length) return;
        const f = r.data.files[0];
        if (f.is_dir) {
          notify('Mục đã chọn là thư mục — chọn tệp Excel.', true);
          return;
        }
        // Giu nguyen metadata cua FileRef da chon (size_bytes/sha256 neu
        // picker cung cap) — audit_excel nhan file_ref day du, khong cat bot.
        state.excelFile = {
          path: f.path, scope: f.scope || 'machine_local',
          size_bytes: f.size_bytes ?? null,
          sha256: f.sha256 ?? null,
        };
        state.auditError = null;
        state.downloadError = null;
        S.markAuditStale(state);
        view.refresh();
        // Chon file tren may → tu nap va audit theo khoang ngay (spec §2).
        await actions.loadExcel();
      },
      downloadExcel: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        if (!state.browserId ||
            !(state.login && state.login.status === 'authenticated')) {
          notify('Chưa đăng nhập — mở đăng nhập trước.', true);
          return;
        }
        state.downloadError = null;
        const job = await loud('upload.download_export', {
          website_id: state.websiteId, browser_id: state.browserId,
          from_date: state.fromDate, to_date: state.toDate,
        });
        if (!job) return;
        state.downloadJobId = job.job_id;
        const done = await h.awaitJob(job.job_id, 120000);
        if (done) C.adoptJobResult(state, done);
        // Tai xong → tu nap audit theo khoang ngay dang chon (spec §2).
        if (done && done.status === 'succeeded' && state.excelFile) {
          await actions.loadExcel();
        }
      },
      loadExcel: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        if (!state.excelFile) {
          notify('Chọn tệp Excel trước.', true);
          return;
        }
        state.auditError = null;
        const job = await loud('upload.audit_excel', {
          website_id: state.websiteId, file_ref: state.excelFile,
          from_date: state.fromDate, to_date: state.toDate,
        });
        if (job) state.auditJobId = job.job_id;
      },
      pickFolder: async () => {
        const r = await api.pickFiles({ directory: true });
        if (!r.ok) {
          notify(`${r.error.code}: ${r.error.message}`, true);
          return;
        }
        if (!r.data.files.length) return;
        const f = r.data.files[0];
        state.folder = { path: f.path, scope: f.scope || 'machine_local' };
        view.refresh();
      },
      scan: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        if (!state.folder) {
          notify('Chọn thư mục hồ sơ trước.', true);
          return;
        }
        const job = await loud('upload.scan', {
          website_id: state.websiteId, folder: state.folder,
          expected_revision: state.revision,
        });
        if (job) state.scanJobId = job.job_id;
      },
      prepare: async () => {
        if (!state.websiteId || !state.runId) {
          notify('Chưa có lượt quét — quét thư mục trước.', true);
          return;
        }
        if (!state.browserId ||
            !(state.login && state.login.status === 'authenticated')) {
          notify('Chưa đăng nhập — mở đăng nhập và xác nhận trước.', true);
          return;
        }
        if (!state.selectedIds.size) {
          notify('Chưa chọn hồ sơ nào trong bảng.', true);
          return;
        }
        // Dot moi: gui dung tap dang chon va GHI NHAN lam tap goc cho
        // cac lan Tiep tuc (Qt: activeUploadSelectedRecordIds = selected).
        const ids = [...state.selectedIds];
        state.activeUploadIds = new Set(ids);
        await submitPrepareIds(ids);
      },
      continuePrepare: async () => {
        // Tiep tuc gui lai DUNG tap goc cua dot upload (khong them record
        // ngoai tap, khong doc lai checkbox hien tai) — engine tu loai muc
        // da mo/da Luu/needs_reconcile. Khong bao gio tu chay dot tiep sau
        // cancel/failed: nguoi dung bam la moi submit.
        if (!state.websiteId || !state.runId) {
          notify('Chưa có lượt quét — quét thư mục trước.', true);
          return;
        }
        if (!state.browserId ||
            !(state.login && state.login.status === 'authenticated')) {
          notify('Chưa đăng nhập — mở đăng nhập và xác nhận trước.', true);
          return;
        }
        const ids = [...state.activeUploadIds];
        if (!ids.length) {
          notify('Chưa có đợt upload nào để tiếp tục.', true);
          return;
        }
        await submitPrepareIds(ids);
      },
      reconcile: async () => {
        if (!state.websiteId || !state.runId) {
          notify('Chưa có lượt quét để đối chiếu.', true);
          return;
        }
        if (!state.needsReconcileIds.size) {
          notify('Không có hồ sơ nào cần đối chiếu.', true);
          return;
        }
        if (!state.excelFile) {
          notify(
            'Nạp sổ Excel mới ở tab Audit trước khi đối chiếu.', true);
          return;
        }
        // Contract §6.15: doi chieu BAT BUOC audit_id moi (so tai lai sau
        // khi nguoi dung kiem tra tren web) — audit lai file hien tai roi
        // moi goi upload.reconcile, tuyet doi khong dung lai audit_id cu.
        state.auditError = null;
        const aj = await loud('upload.audit_excel', {
          website_id: state.websiteId, file_ref: state.excelFile,
          from_date: state.fromDate, to_date: state.toDate,
        });
        if (!aj) return;
        state.auditJobId = aj.job_id;
        const done = await h.awaitJob(aj.job_id, 120000);
        const ad = done && C.jobData(done);
        if (!done || done.status !== 'succeeded' || !ad || !ad.audit_id) {
          if (done && done.status !== 'succeeded' && !state.auditError) {
            state.auditError = {
              code: `job_${done.status}`,
              message: 'Audit mới cho đối chiếu không hoàn tất.',
              retryable: true, next_action: 'retry',
            };
            view.refresh();
          }
          return;
        }
        const job = await loud('upload.reconcile', {
          website_id: state.websiteId, run_id: state.runId,
          audit_id: ad.audit_id,
        });
        if (job) state.reconcileJobId = job.job_id;
      },
      closeSession: async () => {
        if (!state.browserId) return;
        await loud('upload.session_close', {
          website_id: state.websiteId, browser_id: state.browserId,
        });
      },
      refreshStaff: async () => {
        if (!state.websiteId) {
          notify('Chọn website trước.', true);
          return;
        }
        const job = await loud('upload.staff_options', {
          website_id: state.websiteId, browser_id: state.browserId,
          refresh: true,
        });
        if (job) state.staffJobId = job.job_id;
      },
      savePrefs: async () => {
        if (!state.websiteId) return;
        const r = await quiet('upload.preferences', {
          website_id: state.websiteId,
          values: {
            chunk_size: state.chunkSize,
            cong_chung_vien: state.staff.congChungVien || null,
            thu_ky: state.staff.thuKy || null,
          },
        });
        if (r.ok) state.prefsJobId = r.job.job_id;
      },
      stopRunning: async () => {
        const running = C.runningJobs(state, jobs).filter(
          (j) => ['upload.scan', 'upload.prepare',
                  'upload.session_start',
                  'upload.download_export'].includes(j.command));
        if (!running.length) return;
        for (const j of running) {
          const r = await api.cancelJob(j.job_id);
          if (!r.ok) {
            notify(`${r.error.code}: ${r.error.message}`, true);
          }
        }
      },
      openFile: async (ref) => {
        // Nhan FileRef {path, scope:'machine_local'} hoac path thuan —
        // preload/main kiem scope truoc khi mo bang OS.
        const p = ref && typeof ref === 'object' ? ref.path : ref;
        if (!p) return;
        const r = await api.openPath(ref);
        if (!r.ok) notify(`${r.error.code}: ${r.error.message}`, true);
      },
      setFromDate: (v) => {
        state.fromDate = v || state.fromDate;
        S.markAuditStale(state);
        view.refresh(); // badge "chua cap nhat" hien ngay, khong cho poll
      },
      setToDate: (v) => {
        state.toDate = v || state.toDate;
        S.markAuditStale(state);
        view.refresh();
      },
    };

    const dom = {
      syncTbody: (tbody, rows, keyOf, render, empty) =>
        syncTbody(h, tbody, rows, keyOf, render, empty),
    };

    const ctx = {
      api, L, jobs, notify, h, state, actions, dom, mod,
    };

    // ---------- panels ----------
    const panels = {
      audit: NS.buildAuditTab(ctx),
      'scan-upload': NS.buildScanUploadTab(ctx),
    };
    for (const t of S.TABS) {
      const p = panels[t.id].el;
      p.id = `ul-panel-${t.id}`;
      p.setAttribute('role', 'tabpanel');
      p.setAttribute('aria-labelledby', `ul-tab-${t.id}`);
      p.tabIndex = 0;
      s.append(p);
    }

    s.append(h.el('h3', '', 'Job'));
    const jobsBox = h.el('div', 'slot');
    s.append(jobsBox);

    // ---------- tab switching ----------
    function syncTabDom() {
      for (const t of S.TABS) {
        const on = t.id === state.activeTab;
        tabEls[t.id].setAttribute('aria-selected', on ? 'true' : 'false');
        tabEls[t.id].tabIndex = on ? 0 : -1;
        panels[t.id].el.hidden = !on;
      }
    }

    function switchTab(id, focus) {
      if (!S.TAB_IDS.has(id)) return;
      if (id !== state.activeTab) {
        const box = scrollBoxFor(s);
        if (box && state.tabs[state.activeTab]) {
          state.tabs[state.activeTab].scrollTop = box.scrollTop;
        }
        S.selectTab(state, id);
        syncTabDom();
        if (box) box.scrollTop = state.tabs[id].scrollTop || 0;
      } else {
        syncTabDom();
      }
      if (focus) tabEls[id].focus();
    }

    // ARIA tablist keyboard: Left/Right/Home/End doi tab + chuyen focus.
    tablist.addEventListener('keydown', (e) => {
      const ids = S.TABS.map((t) => t.id);
      const cur = ids.indexOf(state.activeTab);
      let next = -1;
      if (e.key === 'ArrowRight') next = (cur + 1) % ids.length;
      else if (e.key === 'ArrowLeft') {
        next = (cur - 1 + ids.length) % ids.length;
      } else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = ids.length - 1;
      if (next >= 0) {
        e.preventDefault();
        switchTab(ids[next], true);
      }
    });

    function renderNotice() {
      noticeBox.innerHTML = '';
      let msg = null;
      let tone = 'muted';
      if (state.waitingBanner) {
        const on = state.waitingBanner.on;
        msg = on === 'login'
          ? 'Chờ đăng nhập trên cửa sổ Chromium — đăng nhập xong quay lại xác nhận.'
          : on === 'review'
            ? 'Các tab đã điền sẵn đang chờ kiểm tra trên Chromium — ' +
              'người dùng tự bấm Lưu.'
            : 'Chờ thao tác của người dùng.';
        tone = 'warn';
        const item = h.el('div', `ul-notice-item ul-badge-${tone}`, msg);
        // CTA xac nhan nam ngay tren banner — backend van tu kiem trang
        // thai portal that sau khi nguoi dung xac nhan (contract §7.2).
        if (on === 'login') {
          const b = h.el('button', 'primary ul-login-confirm',
            'Xác nhận đã đăng nhập');
          b.disabled = !state.browserId;
          b.addEventListener('click', () => actions.confirmLogin());
          item.append(b);
        } else if (on === 'review') {
          const b = h.el('button', 'primary', 'Xong kiểm tra');
          b.disabled = !state.browserId;
          b.addEventListener('click', () => actions.finishReview());
          item.append(b);
        }
        noticeBox.append(item);
        return;
      } else if (state.workflowReady === false) {
        msg = 'Backend chưa hỗ trợ upload.workflow.v1 — ' +
          'khung UI sẵn sàng, chờ sidecar cập nhật contract.';
        tone = 'warn';
      } else if (state.pendingWebsiteId) {
        msg = 'Đang đổi website…';
      } else if (!state.websites.length && state.catalogLoaded) {
        msg = 'Chưa có danh sách website từ backend.';
      } else if (!state.websiteId) {
        msg = 'Chọn website ở tab Audit để bắt đầu.';
      }
      if (msg) {
        noticeBox.append(h.el('div', `ul-notice-item ul-badge-${tone}`, msg));
      }
    }

    const view = {
      el: s,
      refresh() {
        engSlot.innerHTML = '';
        const slot = h.engineSlotEl ? h.engineSlotEl() : null;
        if (slot) engSlot.append(slot);
        if (!booted) {
          booted = true;
          void bootstrap();
        }
        C.adoptJobs(state, jobs);
        derive();
        maybePollSession();
        renderNotice();
        panels.audit.refresh();
        panels['scan-upload'].refresh();
        syncTabDom();
        if (h.renderJobs) h.renderJobs(jobsBox, mod);
      },
    };

    syncTabDom();
    return view;
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = NS;
  }
})();
