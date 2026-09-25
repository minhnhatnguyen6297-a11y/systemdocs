'use strict';

// Upload Lab — tab "Audit Sổ Công Chứng" (MIN-69, task 6/7).
// Thu tu vung theo spec_UI §2: Chon website → Nguon so → header audit →
// 4 the KPI → hai bang 4 cot (STT | Ngay | So cong chung | Ghi chu) xep
// tren/duoi, vung cuon rieng, chia chieu cao bang resize CSS.
// Nut theo capability catalog + trang thai dang nhap/busy; loi hien ngay
// canh nut voi huong dan hanh dong (code + message + next_action), khong
// raw JSON. Khong DOM tai require-time — moi viec dung qua ctx
// {h, state, actions, jobs}.

(function () {
  const NS = (typeof window !== 'undefined')
    ? (window.G1_UPLOAD = window.G1_UPLOAD || {}) : null;
  if (!NS) return;

  // Huong dan hanh dong theo next_action cua contract (khong in raw code
  // cho nguoi dung — code chi la nhan phu nho).
  const NEXT_ACTION_TEXT = {
    login_required: 'Mở đăng nhập và đăng nhập lại trên cửa sổ trình duyệt.',
    pick_files: 'Chọn lại tệp/thư mục hợp lệ.',
    retry: 'Có thể thử lại ngay.',
    contact_admin: 'Liên hệ quản trị để kiểm tra cấu hình/engine.',
  };

  function loginBadge(h, state) {
    const st = state.login && state.login.status;
    if (st === 'authenticated') {
      return h.el('span', 'ul-badge ul-badge-ok', 'Đã đăng nhập');
    }
    if (st === 'awaiting_login' || st === 'waiting') {
      return h.el('span', 'ul-badge ul-badge-warn', 'Chờ đăng nhập…');
    }
    if (st === 'closed') {
      return h.el('span', 'ul-badge ul-badge-muted', 'Phiên đã đóng');
    }
    return h.el('span', 'ul-badge ul-badge-muted', 'Chưa đăng nhập');
  }

  NS.buildAuditTab = function (ctx) {
    const { h, state, actions, dom, jobs } = ctx;
    const S = NS.state;
    const C = NS.client;
    const panel = h.el('div', 'ul-panel');

    function capOf(name) {
      // Capability tu catalog backend — website thieu field capabilities
      // hoac thieu cap → nut tuong ung khoa (khong an, khong nhan).
      const w = state.websites
        .find((x) => x.website_id === state.websiteId);
      return !!(w && Array.isArray(w.capabilities) &&
        w.capabilities.includes(name));
    }

    function jobActive(id) {
      const j = id && jobs && jobs.get(id);
      return !!(j && !C.isTerminal(j));
    }

    function authed() {
      return !!(state.login && state.login.status === 'authenticated');
    }

    function errBox(err, onRetry) {
      const box = h.el('div', 'ul-error');
      box.append(h.el('div', '', (err && err.message) || 'Có lỗi xảy ra.'));
      const meta = [];
      if (err && err.code) meta.push(String(err.code));
      if (err && err.retryable) meta.push('có thể thử lại');
      const guide = err && NEXT_ACTION_TEXT[err.next_action];
      if (guide) meta.push(guide);
      if (meta.length) box.append(h.el('div', 'muted', meta.join(' · ')));
      if (err && err.retryable && onRetry) {
        const re = h.el('button', '', 'Thử lại');
        re.addEventListener('click', onRetry);
        box.append(re);
      }
      return box;
    }

    // ---------- Chon website ----------
    const siteCard = h.el('div', 'ul-card');
    siteCard.append(h.el('div', 'ul-card-title', 'Chọn website'));
    const row1 = h.el('div', 'ul-row');
    row1.append(h.el('span', 'ul-label', 'Website:'));
    const siteSel = h.el('select', 'ul-site');
    siteSel.setAttribute('aria-label', 'Website');
    siteSel.addEventListener('change',
      () => actions.changeWebsite(siteSel.value));
    const badgeSlot = h.el('span', 'ul-badge-slot');
    const envBtn = h.el('button', '', 'Kiểm tra môi trường');
    envBtn.addEventListener('click', () => actions.envCheck());
    const loginBtn = h.el('button', '', 'Mở đăng nhập');
    loginBtn.addEventListener('click', () => actions.sessionStart());
    // Nut xac nhan chi hien trong luc job session_start waiting_user(login)
    // — backend van tu kiem trang thai portal that sau khi xac nhan.
    const confirmBtn = h.el('button', 'primary ul-login-confirm',
      'Xác nhận đã đăng nhập');
    confirmBtn.hidden = true;
    confirmBtn.addEventListener('click', () => actions.confirmLogin());
    row1.append(siteSel, badgeSlot, envBtn, loginBtn, confirmBtn);
    siteCard.append(row1);
    const siteUrl = h.el('div', 'ul-site-url muted', '');
    siteCard.append(siteUrl);
    // Loi website/session — ngay canh cac nut thao tac.
    const siteErr = h.el('div', 'ul-site-err');
    siteErr.hidden = true;
    siteCard.append(siteErr);
    const envBox = h.el('div', 'ul-env');
    siteCard.append(envBox);
    panel.append(siteCard);

    // ---------- Nguon so ----------
    const srcCard = h.el('div', 'ul-card');
    srcCard.append(h.el('div', 'ul-card-title', 'Nguồn sổ'));
    const dRow = h.el('div', 'ul-row');
    dRow.append(h.el('span', 'ul-label', 'Từ ngày:'));

    // Ngay hien thi/nhap DD/MM/YYYY (spec §2); wire backend la ISO.
    function dateInput(which) {
      const inp = h.el('input', 'ul-date');
      inp.type = 'text';
      inp.placeholder = 'dd/mm/yyyy';
      inp.setAttribute('aria-label',
        which === 'from' ? 'Từ ngày' : 'Đến ngày');
      inp.setAttribute('inputmode', 'numeric');
      inp.addEventListener('change', () => commitDate(inp, which));
      return inp;
    }
    const fromIn = dateInput('from');
    const toIn = dateInput('to');
    dRow.append(fromIn);
    dRow.append(h.el('span', 'ul-label', 'Đến ngày:'));
    dRow.append(toIn);
    const dlBtn = h.el('button', 'primary', 'Tải Excel từ Web');
    dlBtn.addEventListener('click', () => actions.downloadExcel());
    dRow.append(dlBtn);
    srcCard.append(dRow);

    function validIso(iso) {
      const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
      if (!m) return false;
      const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
      return d.getFullYear() === Number(m[1]) &&
        d.getMonth() === Number(m[2]) - 1 && d.getDate() === Number(m[3]);
    }

    function commitDate(inp, which) {
      const iso = S.displayToIso(inp.value);
      if (!iso || !validIso(iso)) {
        // Sai dinh dang/ngay khong that: danh dau + tra ve gia tri dang
        // dung — khong cap nhat state, khong lam ket qua cu "che".
        inp.classList.add('ul-invalid');
        inp.title = 'Nhập ngày dạng dd/mm/yyyy';
        inp.value = S.isoToDisplay(
          which === 'from' ? state.fromDate : state.toDate);
        return;
      }
      inp.classList.remove('ul-invalid');
      inp.title = '';
      inp.value = S.isoToDisplay(iso);
      if (which === 'from') actions.setFromDate(iso);
      else actions.setToDate(iso);
    }

    const fRow = h.el('div', 'ul-row');
    const pathIn = h.el('input', 'ul-input-grow');
    pathIn.type = 'text';
    pathIn.readOnly = true;
    pathIn.placeholder = 'Đường dẫn tệp Excel sổ công chứng đã tải về...';
    pathIn.setAttribute('aria-label', 'Đường dẫn tệp Excel');
    const pickBtn = h.el('button', '', 'Chọn tệp Excel...');
    pickBtn.addEventListener('click', () => actions.pickExcel());
    const openBtn = h.el('button', 'ul-open', 'Mở');
    openBtn.addEventListener('click',
      () => actions.openFile(state.excelFile));
    const loadBtn = h.el('button', '', 'Nạp dữ liệu');
    loadBtn.addEventListener('click', () => actions.loadExcel());
    fRow.append(pathIn, pickBtn, openBtn, loadBtn);
    srcCard.append(fRow);
    // Loi tai/nap so — trong cung card Nguon so, kem huong dan hanh dong.
    const srcMsg = h.el('div', 'ul-src-msg');
    srcCard.append(srcMsg);
    panel.append(srcCard);

    // ---------- Header ket qua audit: ten web khop audit_id dang hien ----------
    const auditHead = h.el('div', 'ul-audit-head muted');
    auditHead.hidden = true;
    panel.append(auditHead);

    // ---------- KPI ----------
    const kpis = h.el('div', 'ul-kpis');
    const kpiVals = {};
    for (const [key, title, tone] of [
      ['total', 'TỔNG SỐ ĐÃ NẠP', 'total'],
      ['valid', 'HỢP LỆ TRONG SỔ', 'valid'],
      ['missing', 'SỐ CÒN THIẾU', 'missing'],
      ['issue', 'LỖI / TRÙNG LẶP', 'issue'],
    ]) {
      const c = h.el('div', 'ul-kpi');
      c.dataset.tone = tone;
      c.dataset.kpi = key;
      c.append(h.el('div', 'ul-kpi-t', title));
      const v = h.el('div', 'ul-kpi-v', '0');
      c.append(v);
      kpiVals[key] = v;
      kpis.append(c);
    }
    panel.append(kpis);

    const staleBadge = h.el('div', 'ul-stale',
      'Kết quả chưa cập nhật — bấm "Nạp dữ liệu" để audit lại theo bộ lọc mới.');
    staleBadge.hidden = true;
    panel.append(staleBadge);

    // ---------- Hai bang 4 cot ----------
    function mkTable(title) {
      const wrap = h.el('div', 'ul-table-wrap');
      const ttl = h.el('div', 'ul-table-title', `${title} (0)`);
      const scroll = h.el('div', 'ul-scroll ul-scroll-resize');
      const t = h.el('table', 'ul-table');
      const thead = h.el('thead');
      const tr = h.el('tr');
      for (const c of S.AUDIT_COLUMNS) tr.append(h.el('th', '', c));
      thead.append(tr);
      t.append(thead);
      const tbody = h.el('tbody');
      t.append(tbody);
      scroll.append(t);
      wrap.append(ttl, scroll);
      return { wrap, ttl, tbody };
    }
    const missT = mkTable('Số còn thiếu');
    const issT = mkTable('Số lỗi, trùng');
    panel.append(missT.wrap, issT.wrap);

    function auditRow(row, tr, idx) {
      if (!tr) {
        tr = h.el('tr');
        tr._td = {};
        for (const k of ['stt', 'ngay', 'so', 'chu']) {
          const td = h.el('td');
          tr._td[k] = td;
          tr.append(td);
        }
      }
      tr._td.stt.textContent = row.stt ?? idx + 1;
      tr._td.ngay.textContent = S.isoToDisplay(row.ngay);
      tr._td.so.textContent = row.so_cong_chung || '';
      tr._td.chu.textContent = row.ghi_chu || '';
      return tr;
    }

    function syncAuditTable(tbl, rows) {
      dom.syncTbody(tbl.tbody, rows,
        (r, i) => r.stt ?? i,
        auditRow,
        '(trống)');
      return rows.length;
    }

    let lastCatKey = null;

    function rebuildSites() {
      siteSel.innerHTML = '';
      if (!state.websites.length) {
        const o = h.el('option', '', '(chưa có website)');
        o.value = '';
        siteSel.append(o);
        return;
      }
      for (const w of state.websites) {
        const o = h.el('option', '', w.label || w.website_id);
        o.value = w.website_id;
        // Website backend bao khong kha dung → giu trong list nhung khoa
        // chon (khong an, khong tu quay ve lua chon khac).
        if (w.status && w.status !== 'available') o.disabled = true;
        siteSel.append(o);
      }
    }

    function renderEnv() {
      envBox.innerHTML = '';
      const e = state.envCheck;
      if (!e) return;
      if (e.error) {
        envBox.append(errBox(e.error, () => actions.envCheck()));
        return;
      }
      const steps = e.steps || [];
      if (e.status === 'passed' && !steps.some(
        (x) => x.status !== 'passed')) {
        envBox.append(
          h.el('div', 'ul-env-line', 'Môi trường: đạt.'));
        return;
      }
      for (const x of steps) {
        const line = h.el('div', 'ul-env-line');
        const tone = x.status === 'passed' ? 'ok'
          : x.status === 'blocked' ? 'err' : 'warn';
        line.append(h.el('span',
          `ul-badge ul-badge-${tone}`, x.status || '?'));
        line.append(h.el('span', '',
          ` ${x.label || x.key || ''} — ${x.message || ''}`));
        if (x.guidance) {
          line.append(h.el('div', 'muted', x.guidance));
        }
        envBox.append(line);
      }
    }

    function siteRetry() {
      const r = state.siteError && state.siteError._retry;
      if (!r) return null;
      if (r.kind === 'website' && r.websiteId) {
        return () => actions.changeWebsite(r.websiteId);
      }
      if (r.kind === 'session') return () => actions.sessionStart();
      if (r.kind === 'confirm') return () => actions.confirmLogin();
      return null;
    }

    function renderSiteError() {
      siteErr.innerHTML = '';
      siteErr.hidden = !state.siteError;
      if (state.siteError) {
        siteErr.append(errBox(state.siteError, siteRetry()));
      }
    }

    function refresh() {
      // Website dropdown — rebuild chi khi catalog doi.
      const catKey = JSON.stringify(
        state.websites.map((w) => w.website_id));
      if (catKey !== lastCatKey) {
        lastCatKey = catKey;
        rebuildSites();
      }
      if (siteSel.value !== (state.websiteId || '')) {
        siteSel.value = state.websiteId || '';
      }
      const waitLogin = !!(state.waitingBanner &&
        state.waitingBanner.on === 'login');
      const anyBusy = jobs ? C.runningJobs(state, jobs).length > 0 : false;
      // Doi website chi khi khong co tac vu dang hoat dong — backend
      // kiem lai (workflow_busy); UI khoa truoc de khoi click chet.
      siteSel.disabled = !state.websites.length ||
        !!state.pendingWebsiteId || anyBusy;
      badgeSlot.innerHTML = '';
      badgeSlot.append(loginBadge(h, state));
      const ws = state.websites
        .find((w) => w.website_id === state.websiteId);
      siteUrl.textContent = ws && ws.display_url ? ws.display_url : '';
      renderSiteError();
      renderEnv();

      // Gating nut theo capability + dang nhap + busy (spec §4).
      envBtn.disabled = !state.websiteId || jobActive(state.envJobId) ||
        !!state.pendingWebsiteId;
      loginBtn.disabled = !state.websiteId || !capOf('login') ||
        authed() || jobActive(state.sessionJobId) || waitLogin;
      confirmBtn.hidden = !waitLogin;
      confirmBtn.disabled = !state.browserId;
      const dlBusy = jobActive(state.downloadJobId);
      const auditBusy = jobActive(state.auditJobId);
      dlBtn.disabled = !state.websiteId || !capOf('download_export') ||
        !authed() || !state.browserId || dlBusy;
      pickBtn.disabled = !state.websiteId || !capOf('audit_excel');
      openBtn.disabled = !state.excelFile;
      loadBtn.disabled = !state.websiteId || !capOf('audit_excel') ||
        !state.excelFile || auditBusy;

      // Nguon so — khong ghi de o dang go.
      const doc = panel.ownerDocument || document;
      if (doc.activeElement !== fromIn &&
          fromIn.value !== S.isoToDisplay(state.fromDate)) {
        fromIn.value = S.isoToDisplay(state.fromDate);
      }
      if (doc.activeElement !== toIn &&
          toIn.value !== S.isoToDisplay(state.toDate)) {
        toIn.value = S.isoToDisplay(state.toDate);
      }
      pathIn.value = state.excelFile ? state.excelFile.path : '';
      pathIn.title = pathIn.value;

      // Header ket qua audit: website + khoang ngay + audit_id cua CHINH
      // result dang hien — khong the hien nham website khac (spec §4).
      auditHead.innerHTML = '';
      auditHead.hidden = !state.audit;
      if (state.audit) {
        const aw = state.websites.find(
          (w) => w.website_id === state.audit.website_id);
        const label = (aw && aw.label) || state.audit.website_id || '—';
        const rng =
          `${S.isoToDisplay(state.audit.from_date)}–` +
          `${S.isoToDisplay(state.audit.to_date)}`;
        auditHead.append(h.el('span', '',
          `Kết quả audit — ${label} `));
        auditHead.append(h.el('span', 'muted',
          `[${state.audit.website_id || '—'}] · ${rng} · ` +
          `${state.audit.audit_id || state.auditId || '—'}`));
      }

      // KPI.
      const sm = (state.audit && state.audit.summary) || {};
      kpiVals.total.textContent = String(sm.excel_total ?? 0);
      kpiVals.valid.textContent = String(sm.valid_count ?? 0);
      kpiVals.missing.textContent = String(sm.missing_count ?? 0);
      kpiVals.issue.textContent = String(sm.issue_count ?? 0);
      staleBadge.hidden = !state.auditStale;

      // Loi tai/nap: bao ro tai cho, khong giu so lieu cu.
      srcMsg.innerHTML = '';
      if (state.downloadError) {
        srcMsg.append(errBox(state.downloadError,
          () => actions.downloadExcel()));
      }
      if (state.auditError) {
        srcMsg.append(errBox(state.auditError, () => actions.loadExcel()));
      }

      const missRows = (state.audit && state.audit.missing) || [];
      const issRows = (state.audit && state.audit.issues) || [];
      missT.ttl.textContent =
        `Số còn thiếu (${syncAuditTable(missT, missRows)})`;
      issT.ttl.textContent =
        `Số lỗi, trùng (${syncAuditTable(issT, issRows)})`;
    }

    return {
      el: panel,
      refresh,
      focusWebsite() { siteSel.focus(); },
    };
  };
})();
