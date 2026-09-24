'use strict';

// Upload Lab — tab "Audit Sổ Công Chứng" (MIN-69, task 6).
// Thu tu vung theo spec_UI §2: Chon website → Nguon so → 4 the KPI →
// hai bang 4 cot (STT | Ngay | So cong chung | Ghi chu) xep tren/duoi,
// vung cuon rieng, chia chieu cao bang resize CSS.
// Khong DOM tai require-time — moi viec dung qua ctx {h, state, actions}.

(function () {
  const NS = (typeof window !== 'undefined')
    ? (window.G1_UPLOAD = window.G1_UPLOAD || {}) : null;
  if (!NS) return;

  function loginBadge(h, state) {
    const st = state.login && state.login.status;
    if (st === 'authenticated') {
      return h.el('span', 'ul-badge ul-badge-ok', 'Đã đăng nhập');
    }
    if (st === 'awaiting_login') {
      return h.el('span', 'ul-badge ul-badge-warn', 'Chờ đăng nhập…');
    }
    if (st === 'closed') {
      return h.el('span', 'ul-badge ul-badge-muted', 'Phiên đã đóng');
    }
    return h.el('span', 'ul-badge ul-badge-muted', 'Chưa đăng nhập');
  }

  NS.buildAuditTab = function (ctx) {
    const { h, state, actions, dom } = ctx;
    const S = NS.state;
    const panel = h.el('div', 'ul-panel');

    // ---------- Chon website ----------
    const siteCard = h.el('div', 'ul-card');
    siteCard.append(h.el('div', 'ul-card-title', 'Chọn website'));
    const row1 = h.el('div', 'ul-row');
    row1.append(h.el('span', 'ul-label', 'Website:'));
    const siteSel = h.el('select', 'ul-site');
    siteSel.setAttribute('aria-label', 'Website');
    siteSel.addEventListener('change',
      () => actions.changeWebsite(siteSel.value));
    const envBtn = h.el('button', '', 'Kiểm tra môi trường');
    envBtn.addEventListener('click', () => actions.envCheck());
    const loginBtn = h.el('button', '', 'Mở đăng nhập');
    loginBtn.addEventListener('click', () => actions.sessionStart());
    const badgeSlot = h.el('span', 'ul-badge-slot');
    row1.append(siteSel, badgeSlot, envBtn, loginBtn);
    siteCard.append(row1);
    const siteUrl = h.el('div', 'ul-site-url muted', '');
    siteCard.append(siteUrl);
    const envBox = h.el('div', 'ul-env');
    siteCard.append(envBox);
    panel.append(siteCard);

    // ---------- Nguon so ----------
    const srcCard = h.el('div', 'ul-card');
    srcCard.append(h.el('div', 'ul-card-title', 'Nguồn sổ'));
    const dRow = h.el('div', 'ul-row');
    dRow.append(h.el('span', 'ul-label', 'Từ ngày:'));
    const fromIn = h.el('input');
    fromIn.type = 'date';
    fromIn.setAttribute('aria-label', 'Từ ngày');
    fromIn.addEventListener('change',
      () => actions.setFromDate(fromIn.value));
    dRow.append(fromIn);
    dRow.append(h.el('span', 'ul-label', 'Đến ngày:'));
    const toIn = h.el('input');
    toIn.type = 'date';
    toIn.setAttribute('aria-label', 'Đến ngày');
    toIn.addEventListener('change', () => actions.setToDate(toIn.value));
    dRow.append(toIn);
    const dlBtn = h.el('button', 'primary', 'Tải Excel từ Web');
    dlBtn.addEventListener('click', () => actions.downloadExcel());
    dRow.append(dlBtn);
    srcCard.append(dRow);

    const fRow = h.el('div', 'ul-row');
    const pathIn = h.el('input', 'ul-input-grow');
    pathIn.type = 'text';
    pathIn.readOnly = true;
    pathIn.placeholder = 'Đường dẫn tệp Excel sổ công chứng đã tải về...';
    pathIn.setAttribute('aria-label', 'Đường dẫn tệp Excel');
    const pickBtn = h.el('button', '', 'Chọn tệp Excel...');
    pickBtn.addEventListener('click', () => actions.pickExcel());
    const loadBtn = h.el('button', '', 'Nạp dữ liệu');
    loadBtn.addEventListener('click', () => actions.loadExcel());
    fRow.append(pathIn, pickBtn, loadBtn);
    srcCard.append(fRow);
    const srcMsg = h.el('div', 'ul-src-msg');
    srcCard.append(srcMsg);
    panel.append(srcCard);

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
        siteSel.append(o);
      }
    }

    function renderEnv() {
      envBox.innerHTML = '';
      const e = state.envCheck;
      if (!e) return;
      if (e.error) {
        envBox.append(h.errorFaceEl
          ? h.errorFaceEl(e.error, null)
          : h.el('div', 'ul-error', `${e.error.code}: ${e.error.message}`));
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
      siteSel.disabled = !state.websites.length ||
        !!state.pendingWebsiteId;
      badgeSlot.innerHTML = '';
      badgeSlot.append(loginBadge(h, state));
      const ws = state.websites
        .find((w) => w.website_id === state.websiteId);
      siteUrl.textContent = ws && ws.display_url ? ws.display_url : '';
      renderEnv();

      // Nguon so — khong ghi de o dang go.
      const doc = panel.ownerDocument || document;
      if (doc.activeElement !== fromIn && fromIn.value !== state.fromDate) {
        fromIn.value = state.fromDate;
      }
      if (doc.activeElement !== toIn && toIn.value !== state.toDate) {
        toIn.value = state.toDate;
      }
      pathIn.value = state.excelFile ? state.excelFile.path : '';
      pathIn.title = pathIn.value;
      dlBtn.disabled = !state.websiteId || !state.browserId;
      loadBtn.disabled = !state.excelFile || !state.websiteId;

      // KPI.
      const sm = (state.audit && state.audit.summary) || {};
      kpiVals.total.textContent = String(sm.excel_total ?? 0);
      kpiVals.valid.textContent = String(sm.valid_count ?? 0);
      kpiVals.missing.textContent = String(sm.missing_count ?? 0);
      kpiVals.issue.textContent = String(sm.issue_count ?? 0);
      staleBadge.hidden = !state.auditStale;

      // Loi nap: bao ro tai cho, khong giu so lieu cu.
      srcMsg.innerHTML = '';
      if (state.auditError) {
        const err = state.auditError;
        const box = h.el('div', 'ul-error');
        box.append(h.el('div', '',
          `${err.code || 'error'}: ${err.message || ''}`));
        const meta = [];
        if (err.retryable) meta.push('có thể thử lại');
        if (err.next_action) meta.push(`gợi ý: ${err.next_action}`);
        if (meta.length) {
          box.append(h.el('div', 'muted', meta.join(' · ')));
        }
        if (err.retryable) {
          const re = h.el('button', '', 'Thử lại');
          re.addEventListener('click', () => actions.loadExcel());
          box.append(re);
        }
        srcMsg.append(box);
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
