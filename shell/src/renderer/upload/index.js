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
    } = deps;
    const S = NS.state;
    const C = NS.client;
    const state = S.createUploadState();
    const inflight = {};
    let booted = false;
    let lastSessPoll = 0;

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

    async function bootstrap() {
      try {
        const cap = C.hasWorkflowCapability(mod);
        if (cap === false) {
          state.workflowReady = false;
          return;
        }
        if (!inflight.catalog && !state.catalogTried) {
          inflight.catalog = true;
          state.catalogTried = true;
          try {
            const r = await quiet('upload.websites', {});
            if (r.ok) {
              await h.awaitJob(r.job.job_id, 30000);
            } else if (r.error && C.VERSION_ERRORS.has(r.error.code)) {
              state.workflowReady = false;
            }
          } catch (e) {
            // Loi bat ngo: khong khoa co — lan bootstrap sau duoc thu lai.
            state.catalogTried = false;
          } finally {
            inflight.catalog = false;
          }
          view.refresh();
        }
        if (!inflight.ws) {
          inflight.ws = true;
          try {
            const r = await quiet('upload.workspace_get',
              { website_id: state.websiteId });
            if (r.ok) await h.awaitJob(r.job.job_id, 30000);
          } finally {
            inflight.ws = false;
          }
          view.refresh();
        }
      } catch (e) {
        // Bootstrap im lang — UI hien empty state, khong vo module.
      }
    }

    // Fetch dan xuat khi ngu canh doi — moi submit duoc guard bang
    // inflight flag + moc queueFor/prefsTried/staffTried de khong lap vo han.
    function derive() {
      if (state.workflowReady === false) return;
      if (state.websiteId && state.runId &&
          (!state.queueFor || state.queueFor.runId !== state.runId ||
           state.queueFor.auditId !== state.auditId) &&
          !inflight.queue &&
          Date.now() > (inflight.queueRetryAt || 0)) {
        inflight.queue = true;
        quiet('upload.queue_get', {
          website_id: state.websiteId, run_id: state.runId,
          audit_id: state.auditId,
        }).then((r) => {
          if (r.ok) {
            state.queueJobId = r.job.job_id;
            return h.awaitJob(r.job.job_id, 30000);
          }
          inflight.queueRetryAt = Date.now() + 15000;
          return null;
        }).then(() => {
          inflight.queue = false;
          view.refresh();
        }).catch(() => { inflight.queue = false; });
      }
      if (state.websiteId && !state.prefsTried && !inflight.prefs) {
        inflight.prefs = true;
        state.prefsTried = true;
        quiet('upload.preferences', { website_id: state.websiteId })
          .then((r) => {
            if (r.ok) {
              state.prefsJobId = r.job.job_id;
              return h.awaitJob(r.job.job_id, 30000);
            }
            return null;
          }).then(() => {
            inflight.prefs = false;
            view.refresh();
          }).catch(() => { inflight.prefs = false; });
      }
      if (state.websiteId && !state.staffTried && !inflight.staff) {
        inflight.staff = true;
        state.staffTried = true;
        quiet('upload.staff_options', {
          website_id: state.websiteId, browser_id: null, refresh: false,
        }).then((r) => {
          if (r.ok) {
            state.staffJobId = r.job.job_id;
            return h.awaitJob(r.job.job_id, 30000);
          }
          return null;
        }).then(() => {
          inflight.staff = false;
          view.refresh();
        }).catch(() => { inflight.staff = false; });
      }
    }

    // Poll session_status gop khi co job waiting_user (contract §7.2) —
    // throttle 4s, khong chong request.
    function maybePollSession() {
      if (!state.browserId) return;
      const waiting = C.runningJobs(state, jobs).some(
        (j) => j.status === 'waiting_user' &&
               String(j.command || '').startsWith('upload.'));
      if (!waiting) return;
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
        const job = await loud('upload.session_start', {
          website_id: state.websiteId, expected_revision: state.revision,
        });
        if (job) state.sessionJobId = job.job_id;
      },
      pickExcel: async () => {
        const r = await api.pickFiles({
          multi: false,
          filters: [{ name: 'Excel', extensions: ['xlsx', 'xls', 'xlsm'] }],
        });
        if (!r.ok) {
          notify(`${r.error.code}: ${r.error.message}`, true);
          return;
        }
        if (!r.data.files.length) return;
        const f = r.data.files[0];
        state.excelFile = { path: f.path, scope: f.scope || 'machine_local' };
        state.auditError = null;
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
        if (!state.browserId) {
          notify('Chưa đăng nhập — mở đăng nhập trước.', true);
          return;
        }
        const job = await loud('upload.download_export', {
          website_id: state.websiteId, browser_id: state.browserId,
          from_date: state.fromDate, to_date: state.toDate,
        });
        if (!job) return;
        state.downloadJobId = job.job_id;
        const done = await h.awaitJob(job.job_id, 120000);
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
        if (!state.selectedIds.size) {
          notify('Chưa chọn hồ sơ nào trong bảng.', true);
          return;
        }
        const job = await loud('upload.prepare', {
          website_id: state.websiteId, browser_id: state.browserId,
          run_id: state.runId, audit_id: state.auditId,
          queue_revision: state.queueRevision,
          record_ids: [...state.selectedIds],
          chunk_size: state.chunkSize,
          cong_chung_vien: state.staff.congChungVien || null,
          thu_ky: state.staff.thuKy || null,
        });
        if (job) state.prepareJobId = job.job_id;
      },
      continuePrepare: async () => {
        await actions.prepare();
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
                  'upload.session_start'].includes(j.command));
        if (!running.length) return;
        for (const j of running) {
          const r = await api.cancelJob(j.job_id);
          if (!r.ok) {
            notify(`${r.error.code}: ${r.error.message}`, true);
          }
        }
      },
      openFile: async (p) => {
        if (!p) return;
        const r = await api.openPath(p);
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
      } else if (state.workflowReady === false) {
        msg = 'Backend chưa hỗ trợ upload.workflow.v1 — ' +
          'khung UI sẵn sàng, chờ sidecar cập nhật contract.';
        tone = 'warn';
      } else if (state.pendingWebsiteId) {
        msg = 'Đang đổi website…';
      } else if (!state.websites.length && state.catalogTried) {
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
