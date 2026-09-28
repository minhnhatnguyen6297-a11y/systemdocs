'use strict';

// Upload Lab — tab "Quét & Upload Hồ Sơ" (MIN-69, task 6).
// Thu tu vung theo spec_UI §3: Ngu canh → Nguon va nhan su → Tien do (2
// thanh rieng) → Thanh thao tac → Bang 6 cot
// (✓ | STT | Ngay | So cong chung | Ghi chu | Dia chi file).
// Quy tac chon/loc giu theo Qt: dong da chon len dau, Loc so loi = bo chon
// so loi co hoan tac, So thieu trong Excel = select_only, ID that.

(function () {
  const NS = (typeof window !== 'undefined')
    ? (window.G1_UPLOAD = window.G1_UPLOAD || {}) : null;
  if (!NS) return;

  NS.buildScanUploadTab = function (ctx) {
    const { h, state, actions, dom } = ctx;
    const S = NS.state;
    const C = NS.client;
    const panel = h.el('div', 'ul-panel');

    function capOf(name) {
      // Capability tu catalog backend (cung helper audit.js) — website
      // thieu cap → nut tuong ung khoa, khong an, khong nhan.
      const w = state.websites
        .find((x) => x.website_id === state.websiteId);
      return !!(w && Array.isArray(w.capabilities) &&
        w.capabilities.includes(name));
    }

    function jobActive(id) {
      const j = id && ctx.jobs && ctx.jobs.get(id);
      return !!(j && !C.isTerminal(j));
    }

    function authed() {
      return !!(state.login && state.login.status === 'authenticated');
    }

    // ---------- Ngu canh — mot hang gon (ban mau P8) ----------
    const ctxCard = h.el('div', 'card');
    const ctxBody = h.el('div', 'card-body');
    const ctxRow = h.el('div', 'ul-row');
    ctxRow.append(h.el('span', 'ul-label', 'Website'));
    const ctxSite = h.el('strong', '', '—');
    const ctxBadge = h.el('span', 'ul-badge ul-badge-muted', 'Chưa đăng nhập');
    const ctxExcel = h.el('span', 'muted small ul-context-excel',
      'Chưa nạp sổ Excel');
    const spacer = h.el('span', 'ul-spacer');
    const gotoAudit = h.el('button', 'sm', 'Sang tab Audit để đổi website');
    gotoAudit.addEventListener('click', () => actions.gotoAudit());
    ctxRow.append(ctxSite, ctxBadge, ctxExcel, spacer, gotoAudit);
    ctxBody.append(ctxRow);
    ctxCard.append(ctxBody);
    panel.append(ctxCard);

    // ---------- Nguon + nhan su + tien do — mot card, hai hang ----------
    const cfg = h.el('div', 'card');
    const cfgBody = h.el('div', 'card-body');
    const r1 = h.el('div', 'ul-row');
    const browseBtn = h.el('button', '', 'Chọn thư mục');
    browseBtn.addEventListener('click', () => actions.pickFolder());
    const folderIn = h.el('input', 'ul-input-grow');
    folderIn.type = 'text';
    folderIn.readOnly = true;
    folderIn.placeholder = 'Đường dẫn thư mục chứa hồ sơ Word công chứng...';
    folderIn.setAttribute('aria-label', 'Đường dẫn thư mục');
    const scanBtn = h.el('button', 'primary sm', 'Bắt đầu Quét');
    scanBtn.addEventListener('click', () => actions.scan());
    r1.append(browseBtn, folderIn, scanBtn);
    r1.append(h.el('span', 'muted', '|'));
    r1.append(h.el('span', 'ul-label', 'Công chứng viên'));
    const staffSel = h.el('select', 'ul-staff');
    staffSel.setAttribute('aria-label', 'Công chứng viên');
    staffSel.addEventListener('change', () => {
      state.staff.congChungVien = staffSel.value || null;
      actions.savePrefs();
    });
    r1.append(staffSel);
    r1.append(h.el('span', 'ul-label', 'Thư ký'));
    const secIn = h.el('input', 'ul-sec');
    secIn.type = 'text';
    secIn.placeholder = 'Nhập tên thư ký...';
    secIn.setAttribute('aria-label', 'Thư ký');
    secIn.addEventListener('change', () => {
      state.staff.thuKy = secIn.value.trim();
      actions.savePrefs();
    });
    r1.append(secIn);
    const refStaff = h.el('button', '', 'Cập nhật danh sách');
    refStaff.addEventListener('click', () => actions.refreshStaff());
    r1.append(refStaff);
    r1.append(h.el('span', 'ul-label', 'Số tab mỗi đợt'));
    const chunkIn = h.el('input', 'ul-chunk');
    chunkIn.type = 'number';
    chunkIn.min = String(S.MIN_CHUNK);
    chunkIn.max = String(S.MAX_CHUNK);
    chunkIn.setAttribute('aria-label', 'Số tab mỗi đợt');
    chunkIn.addEventListener('change', () => {
      state.chunkSize = S.clampChunk(chunkIn.value);
      chunkIn.value = String(state.chunkSize);
      actions.savePrefs();
      syncButtons();
    });
    r1.append(chunkIn);
    cfgBody.append(r1);

    // Tien do: quet va chuan bi/upload la HAI thanh rieng biet (spec §3),
    // nam trong cung card nguon — khong tach card rieng.
    const pRow = h.el('div', 'ul-row ul-progress-row');
    pRow.append(h.el('span', 'ul-label', 'Quét'));
    const scanBar = h.el('progress', 'ul-progress');
    scanBar.max = 1;
    const scanLabel = h.el('span', 'ul-progress-label muted', 'Chưa quét.');
    pRow.append(scanBar, scanLabel);
    pRow.append(h.el('span', 'ul-label', 'Chuẩn bị'));
    const prepBar = h.el('progress', 'ul-progress');
    prepBar.max = 1;
    const prepLabel = h.el('span', 'ul-progress-label muted',
      'Chưa chuẩn bị.');
    const stopBtn = h.el('button', 'danger sm', 'Dừng');
    stopBtn.disabled = true;
    stopBtn.addEventListener('click', () => actions.stopRunning());
    pRow.append(prepBar, prepLabel, stopBtn);
    cfgBody.append(pRow);
    const sessLine = h.el('div', 'muted small ul-note', '');
    sessLine.hidden = true;
    cfgBody.append(sessLine);
    const scanSummary = h.el('div', 'muted small ul-note', 'Chưa quét thư mục.');
    cfgBody.append(scanSummary);
    cfg.append(cfgBody);
    panel.append(cfg);

    // ---------- Thanh thao tac — card rieng tren bang (spec §3) ----------
    const actCard = h.el('div', 'card');
    const actBody = h.el('div', 'card-body');
    const bar = h.el('div', 'ul-actions');
    const selAll = h.el('button', 'sm', 'Chọn tất cả');
    selAll.addEventListener('click', () => {
      S.selectAll(state);
      refresh();
    });
    const selNone = h.el('button', 'sm', 'Bỏ chọn tất cả');
    selNone.addEventListener('click', () => {
      S.clearSelection(state);
      refresh();
    });
    const filterBtn = h.el('button', 'sm', 'Lọc số lỗi');
    filterBtn.addEventListener('click', () => {
      S.toggleIssueFilter(state);
      refresh();
    });
    const missBtn = h.el('button', 'sm', 'Số thiếu trong Excel');
    missBtn.addEventListener('click', () => {
      if (!S.selectMissingExcel(state)) {
        ctx.notify('Chưa có số thiếu trong Excel để chọn.', true);
      }
      refresh();
    });
    const barSpacer = h.el('span', 'ul-spacer');
    const upBtn = h.el('button', 'primary sm', 'Upload file đã chọn (0)');
    upBtn.addEventListener('click', () => actions.prepare());
    const contBtn = h.el('button', 'secondary sm',
      'Tiếp tục 10 số tiếp theo');
    contBtn.addEventListener('click', () => actions.continuePrepare());
    const closeBtn = h.el('button', 'danger sm', 'Đóng browser upload');
    closeBtn.addEventListener('click', () => actions.closeSession());
    bar.append(selAll, selNone, filterBtn, missBtn, barSpacer,
      upBtn, contBtn, closeBtn);
    actBody.append(bar);
    actCard.append(actBody);
    panel.append(actCard);

    // ---------- Hang cho (queue) — card co tieu de dem so + bang ----------
    const qCard = h.el('div', 'card ul-queue-card');
    const qHead = h.el('div', 'card-head');
    const queueTitle = h.el('h3', 'card-title',
      'Hàng chờ (0 hồ sơ · đã chọn 0)');
    qHead.append(queueTitle);
    qCard.append(qHead);
    const qBody = h.el('div', 'card-body ul-queue-body');

    // Canh bao can doi chieu + nut hanh dong (upload.reconcile — contract
    // §6.15). Banner luon dem so ho so chua ro da Luu; hanh dong doi chieu
    // nam ngay day, KHONG huong dan di qua trang log da bo.
    const reconBanner = h.el('div', 'ul-reconcile');
    reconBanner.hidden = true;
    const reconText = h.el('span', 'ul-reconcile-text');
    const reconBtn = h.el('button', 'ul-reconcile-btn secondary sm',
      'Đối chiếu với sổ mới');
    reconBtn.type = 'button';
    reconBtn.addEventListener('click', () => actions.reconcile());
    const reconHint = h.el('span', 'ul-reconcile-hint');
    reconBanner.append(reconText, reconBtn, reconHint);
    qBody.append(reconBanner);

    // Loi/partial cua dot prepare — hien ngay tren bang, khong nuot vao
    // the Job (spec §4).
    const prepErr = h.el('div', 'ul-error ul-prepare-error');
    prepErr.hidden = true;
    qBody.append(prepErr);

    // ---------- Bang 6 cot ----------
    const wrap = h.el('div', 'ul-table-wrap');
    const t = h.el('table', 'ul-grid ul-queue-grid');
    const thead = h.el('thead');
    const htr = h.el('tr');
    for (const c of S.QUEUE_COLUMNS) {
      htr.append(h.el('th', c === 'STT' ? 'num' : '', c));
    }
    thead.append(htr);
    t.append(thead);
    const tbody = h.el('tbody');
    t.append(tbody);
    wrap.append(t);
    qBody.append(wrap);
    qCard.append(qBody);
    panel.append(qCard);

    function queueRow(row, tr, idx) {
      const id = Number(row.record_id);
      if (!tr) {
        tr = h.el('tr');
        tr._c = {};
        const cbTd = h.el('td', 'ul-cb');
        const cb = h.el('input', 'cb');
        cb.type = 'checkbox';
        cb.setAttribute('aria-label', `Chọn hồ sơ ${id}`);
        cb.addEventListener('change', () => {
          S.setSelected(state, id, cb.checked);
          refresh();
        });
        cbTd.append(cb);
        tr._c.cb = cb;
        tr.append(cbTd);
        // Qt: double-click dong mo file nguon bang OS (openPath qua
        // preload — main kiem scope/extension). Bo qua khi dblclick trung
        // checkbox/nut Mo (handler rieng da xu ly).
        tr.addEventListener('dblclick', (e) => {
          if (e.target && e.target.closest &&
              e.target.closest('button,input')) return;
          if (tr._c.path && tr._c.path._p) actions.openFile(tr._c.path._p);
        });
        for (const k of ['stt', 'ngay', 'so', 'chu', 'path']) {
          const td = h.el('td',
            (k === 'chu' || k === 'path') ? '' : 'num');
          tr._c[k] = td;
          tr.append(td);
        }
        tr._c.path.classList.add('ul-path');
        const inner = h.el('div', 'ul-path-inner');
        // truncate-path (shared): cat dau duong dan, giu ten file; title
        // hien duong dan day du khi hover.
        const txt = h.el('span', 'ul-path-text truncate-path');
        const open = h.el('button', 'ul-open', 'Mở');
        open.type = 'button';
        open.addEventListener('click', () => {
          if (tr._c.path._p) actions.openFile(tr._c.path._p);
        });
        inner.append(txt, open);
        tr._c.pathTxt = txt;
        tr._c.path.append(inner);
      }
      const c = tr._c;
      c.cb.checked = state.selectedIds.has(id);
      c.stt.textContent = idx + 1;
      c.ngay.textContent = S.isoToDisplay(row.ngay);
      c.so.textContent =
        row.contract_no || row.normalized_contract_no || '';
      let note = row.ghi_chu || '';
      if (state.needsReconcileIds.has(id)) {
        note = note ? `${note} — cần đối chiếu` : 'cần đối chiếu';
      } else if (state.openTabIds.has(id)) {
        note = note ? `${note} — đang mở trên web` : 'đang mở trên web';
      }
      c.chu.textContent = note;
      c.path._p = row.file_path || '';
      c.pathTxt.textContent = row.file_path || '';
      c.pathTxt.title = row.file_path || '';
      tr.classList.toggle('ul-row-selected', c.cb.checked);
      tr.classList.toggle('ul-row-reconcile',
        state.needsReconcileIds.has(id));
      tr.classList.toggle('ul-row-open', state.openTabIds.has(id));
      tr.classList.toggle('ul-row-issue', !!row.has_issue);
      return tr;
    }

    function siteLabel() {
      const ws = state.websites
        .find((w) => w.website_id === state.websiteId);
      return ws ? (ws.label || ws.website_id)
        : (state.websiteId || '—');
    }

    // Gating theo backend state + capability (spec §4): moi nut chi bat
    // khi hanh dong do thuc su goi duoc ngay luc nay — Upload/Tiep tuc can
    // dang nhap + queue cua DUNG run/audit dang hien thi; Tiep tuc can mot
    // dot da submit (activeUploadIds) va con ho so dot sau; Dong can phien
    // song va khong co prepare dang cho review.
    function syncButtons(hasRows) {
      const selCount = state.selectedIds.size;
      const prepJob = state.prepareJobId && ctx.jobs.get(state.prepareJobId);
      const prepLive = !!(prepJob && !C.isTerminal(prepJob));
      const prepRunning = !!(prepLive &&
        prepJob.status !== 'waiting_user');
      const scanLive = jobActive(state.scanJobId) || !!state.scanProgress;
      const loginWait = jobActive(state.sessionJobId) &&
        state.waitingBanner && state.waitingBanner.on === 'login';
      const queueReady = !!(state.runId && state.queueFor &&
        state.queueFor.runId === state.runId &&
        state.queueFor.auditId === state.auditId);
      const canPrep = capOf('prepare') && !!state.browserId && authed() &&
        queueReady;
      selAll.disabled = !hasRows;
      selNone.disabled = !hasRows;
      const issues = S.issueRecordIds(state);
      filterBtn.disabled = !hasRows || !issues.size;
      filterBtn.textContent = state.issueFilterBackup != null
        ? 'Hoàn tác lọc số lỗi' : 'Lọc số lỗi';
      missBtn.disabled = !hasRows;
      upBtn.disabled = !hasRows || !selCount || !canPrep ||
        prepLive || scanLive || !!loginWait;
      upBtn.textContent = `Upload file đã chọn (${selCount})`;
      upBtn.title = canPrep ? '' :
        'Cần đăng nhập và queue của lượt quét hiện tại sẵn sàng';
      contBtn.disabled = !canPrep || prepLive || scanLive ||
        !!loginWait || !state.uploadSessionActive ||
        !(state.remaining > 0) || !state.activeUploadIds.size;
      // Gate breakdown cho debug/E2E — doc duoc ly do disable ma khong can
      // moc state noi bo (mot dong, khong lo du lieu nhay).
      const gate = [
        ['cap', !canPrep], ['capOf', !capOf('prepare')],
        ['bid', !state.browserId], ['auth', !authed()],
        ['q', !queueReady], ['prep', prepLive], ['scan', scanLive],
        ['loginWait', !!loginWait], ['sess', !state.uploadSessionActive],
        ['rem', !(state.remaining > 0)], ['origin', !state.activeUploadIds.size],
      ].filter(([, v]) => v).map(([k]) => k).join(',') || 'ok';
      contBtn.dataset.gate = gate +
        `|q=${state.queueFor ? state.queueFor.auditId : 'null'}` +
        `/a=${state.auditId}` +
        `/r=${state.queueFor ? state.queueFor.runId : 'null'}` +
        `/${state.runId}`;
      contBtn.textContent = state.remaining > 0
        ? `Tiếp tục đợt sau — còn ${state.remaining}`
        : 'Tiếp tục đợt sau';
      closeBtn.disabled = !state.browserId || !state.uploadSessionActive ||
        prepLive;
      // Nhan su/chunk doc khi prepare tiep theo gui — khoa trong luc
      // engine dang mo tab (accepted/running); luc cho review van sua duoc
      // cho dot sau.
      staffSel.disabled = prepRunning;
      secIn.disabled = prepRunning;
      refStaff.disabled = prepRunning || !authed() || !state.browserId;
      chunkIn.disabled = prepRunning;
      browseBtn.disabled = scanLive;
      scanBtn.disabled = !state.websiteId || !capOf('scan') || scanLive;
      // Doi chieu can audit MOI tu file hien tai (§6.15) — khoa khi chua
      // nap so, dang audit/reconcile, hoac dang cho review.
      reconBtn.disabled = !capOf('reconcile') || !state.runId ||
        !state.excelFile || prepLive ||
        jobActive(state.reconcileJobId) || jobActive(state.auditJobId);
    }

    let lastStaffKey = null;

    function syncStaff() {
      const opts = state.staff.options || [];
      const cur = state.staff.congChungVien;
      const key = JSON.stringify([opts, cur]);
      if (key === lastStaffKey) return;
      lastStaffKey = key;
      staffSel.innerHTML = '';
      const empty = h.el('option', '', '(chọn công chứng viên)');
      empty.value = '';
      staffSel.append(empty);
      const names = opts.slice();
      if (cur && !names.includes(cur)) names.unshift(cur);
      for (const n of names) {
        const o = h.el('option', '', n);
        o.value = n;
        staffSel.append(o);
      }
      staffSel.value = cur || '';
    }

    function syncProgress() {
      const sp = state.scanProgress;
      if (sp) {
        scanBar.max = sp.total || 1;
        if (sp.total) scanBar.value = sp.done || 0;
        else scanBar.removeAttribute('value');
        scanLabel.textContent = `${sp.done ?? 0}/${sp.total ?? '?'}`
          + (sp.current_label ? ` — ${sp.current_label}` : '');
      } else {
        scanBar.value = 0;
        scanBar.max = 1;
        scanLabel.textContent = state.runId
          ? `Đã quét xong (run ${state.runId}).` : 'Chưa quét.';
      }
      const pp = state.prepareProgress;
      if (pp) {
        prepBar.max = pp.total || 1;
        if (pp.total) prepBar.value = pp.done || 0;
        else prepBar.removeAttribute('value');
        prepLabel.textContent = `${pp.done ?? 0}/${pp.total ?? '?'}`
          + (pp.current_label ? ` — ${pp.current_label}` : '');
      } else {
        prepBar.value = 0;
        prepBar.max = 1;
        prepLabel.textContent = state.remaining > 0
          ? `Còn ${state.remaining} hồ sơ đợt sau.`
          : 'Chưa chuẩn bị.';
      }
      // Dong tab portal theo snapshot phien (open/saved/closed/unknown) —
      // hien ngay trong luc cho review de nguoi dung thay so da Lưu.
      const tb = state.sessionTabs;
      if (state.uploadSessionActive || tb) {
        const n = (k) => (tb && Array.isArray(tb[k]) ? tb[k].length : 0);
        sessLine.hidden = false;
        sessLine.textContent =
          `Tab portal: ${n('open_record_ids')} đang mở · ` +
          `${n('saved_record_ids')} đã Lưu · ` +
          `${n('closed_record_ids')} đã đóng · ` +
          `${state.needsReconcileIds.size} chưa rõ`;
      } else {
        sessLine.hidden = true;
        sessLine.textContent = '';
      }
      const running = C.runningJobs(state, ctx.jobs)
        .filter((j) => ['upload.scan', 'upload.prepare',
                        'upload.session_start'].includes(j.command));
      stopBtn.disabled = !running.length;
      return running.length > 0;
    }

    function refresh() {
      // Ngu canh.
      ctxSite.textContent = siteLabel();
      const st = state.login && state.login.status;
      ctxBadge.className = 'ul-badge ' + (
        st === 'authenticated' ? 'ul-badge-ok'
        : st === 'awaiting_login' ? 'ul-badge-warn'
        : 'ul-badge-muted');
      ctxBadge.textContent = st === 'authenticated' ? 'Đã đăng nhập'
        : st === 'awaiting_login' ? 'Chờ đăng nhập…'
        : st === 'closed' ? 'Phiên đã đóng' : 'Chưa đăng nhập';
      const fileName = state.excelFile && state.excelFile.path
        ? state.excelFile.path.split(/[\\/]/).pop() : null;
      ctxExcel.textContent = state.audit
        ? `Sổ: ${fileName || 'đã nạp'} · ` +
          `${S.isoToDisplay(state.fromDate)}–${S.isoToDisplay(state.toDate)}`
        : (fileName
          ? `Sổ: ${fileName} · chưa nạp`
          : 'Chưa nạp sổ Excel — vẫn quét/xem được');

      // Nguon + nhan su.
      folderIn.value = state.folder ? state.folder.path : '';
      folderIn.title = folderIn.value;
      syncStaff();
      const doc = panel.ownerDocument || document;
      if (doc.activeElement !== secIn &&
          secIn.value !== (state.staff.thuKy || '')) {
        secIn.value = state.staff.thuKy || '';
      }
      if (doc.activeElement !== chunkIn &&
          Number(chunkIn.value) !== state.chunkSize) {
        chunkIn.value = String(state.chunkSize);
      }

      syncProgress();
      const rows = S.sortedQueueRows(state);
      syncButtons(state.rowIds.size > 0);
      queueTitle.textContent =
        `Hàng chờ (${state.rowIds.size} hồ sơ · ` +
        `đã chọn ${state.selectedIds.size})`;

      // Tom tat luot quet.
      const parts = [`folder=${state.rowIds.size}`];
      parts.push(`thieu=${state.missingInExcelIds.size}`);
      parts.push(`da_chon=${state.selectedIds.size}`);
      parts.push(state.hasExcel ? 'có Excel' : 'chưa nạp Excel');
      if (state.scanStats && state.scanStats.processed_files != null) {
        parts.push(`xử lý=${state.scanStats.processed_files}`);
      }
      scanSummary.textContent = state.runId || state.rowIds.size
        ? parts.join(' | ') : 'Chưa quét thư mục.';

      // Can doi chieu — dem so ho so chua ro da Lưu ngay tren bang, kem
      // hanh dong upload.reconcile (audit moi → doi chieu → khong gui lai).
      const rec = state.needsReconcileIds.size;
      reconBanner.hidden = !rec;
      if (rec) {
        reconText.textContent =
          `${rec} hồ sơ có thể đã Lưu nhưng chưa xác minh — ` +
          'cần đối chiếu với sổ mới trước khi gửi lại.';
        reconHint.textContent = !state.excelFile
          ? ' Nạp sổ Excel mới ở tab Audit trước.' : '';
      }
      // Loi/partial cua dot prepare ngay tren bang (khong chi o the Job).
      const pe = state.prepareError;
      prepErr.hidden = !pe;
      if (pe) {
        const parts = [pe.message || 'Chuẩn bị hồ sơ không hoàn tất.'];
        if (pe.code) parts.push(`[${pe.code}]`);
        if (pe.retryable && !state.needsReconcileIds.size) {
          parts.push('— có thể thử lại.');
        } else if (state.needsReconcileIds.size) {
          parts.push('— đối chiếu trước khi gửi lại.');
        }
        prepErr.textContent = parts.join(' ');
      }

      dom.syncTbody(tbody, rows,
        (r) => r.record_id,
        queueRow,
        'Chưa có hồ sơ — chọn thư mục và Bắt đầu Quét.');
    }

    return { el: panel, refresh };
  };
})();
