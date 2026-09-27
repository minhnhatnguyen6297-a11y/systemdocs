/* ==========================================================================
   upload.js — module Upload Lab: tab "Audit Sổ Công Chứng" + tab
   "Quét & Upload Hồ Sơ". Bố cục/hành vi theo upload_lab/docs/spec_UI.md;
   thị giác theo upload_lab/docs/visual-design.md + tokens chung.
   Dữ liệu giả — không gọi backend, không mở website thật.
   ========================================================================== */
'use strict';

(() => {
const { h, btn } = P;
const D = P_DATA;

let U = null;
P.initUpload = () => { U = newSession('std'); };
P.setUploadScenario = (name) => { U = newSession(name); P.rerenderModule(); };

function newSession(scenario) {
  const d = D.uploadData(scenario);
  return {
    scenario,
    tab: 'audit',                 // audit | scan — giữ khi re-render
    ...d,
    filterErr: false,
    staleResult: false,           // đổi ngày/file → kết quả "chưa cập nhật"
    envCheck: null,               // null | 'ok' | 'warn' | 'err'
    auditing: false,
    scanning: false,
  };
}
const flags = () => P.state.flags;

/* ============================ RENDER ================================== */
P.renderers.upload = (el) => {
  el.innerHTML = '';
  const content = h('div', 'module-content');
  if (flags().has('mock')) {
    const b = h('div', 'banner warn');
    b.append(h('span', 'grow', 'MOCK — đang xem dữ liệu giả của bản mẫu, không phải backend thật.'));
    content.append(b);
  }
  content.append(tabsEl());
  const pa = h('div', 'ul-panel'); pa.dataset.tab = 'audit';
  const ps = h('div', 'ul-panel'); ps.dataset.tab = 'scan';
  buildAudit(pa); buildScan(ps);
  pa.hidden = U.tab !== 'audit';
  ps.hidden = U.tab !== 'scan';
  // hai panel luôn mounted → chuyển tab giữ trạng thái + vị trí cuộn
  pa.style.display = pa.hidden ? 'none' : 'flex';
  ps.style.display = ps.hidden ? 'none' : 'flex';
  pa.style.flexDirection = ps.style.flexDirection = 'column';
  pa.style.gap = ps.style.gap = '12px';
  content.append(pa, ps);
  el.append(content);
};

function tabsEl() {
  const bar = h('div', 'ul-tabs'); bar.setAttribute('role', 'tablist');
  const mk = (id, label) => {
    const t = h('button', 'ul-tab', label);
    t.type = 'button'; t.setAttribute('role', 'tab');
    t.setAttribute('aria-selected', String(U.tab === id));
    t.addEventListener('click', () => {
      U.tab = id;
      // giữ DOM hai panel — chỉ lật hiển thị, không mất state/scroll
      const pa = document.querySelector('.ul-panel[data-tab="audit"]');
      const ps = document.querySelector('.ul-panel[data-tab="scan"]');
      pa.hidden = ps.hidden = true;
      pa.style.display = ps.style.display = 'none';
      const cur = id === 'audit' ? pa : ps;
      cur.hidden = false; cur.style.display = 'flex';
      document.querySelectorAll('.ul-tab').forEach(x =>
        x.setAttribute('aria-selected', String(x === t)));
    });
    return t;
  };
  bar.append(mk('audit', 'Audit Sổ Công Chứng'), mk('scan', 'Quét & Upload Hồ Sơ'));
  return bar;
}

/* ============================ TAB AUDIT =============================== */
function buildAudit(el) {
  /* vùng chọn website + env */
  const c1 = h('div', 'card');
  const b1 = h('div', 'card-body');
  const r1 = h('div', 'ul-row');
  r1.append(h('span', 'lbl', 'Website'));
  const sel = h('select', 'input');
  const o = h('option', '', `Nam Định — ${U.websiteUrl}`); sel.append(o);
  sel.setAttribute('aria-label', 'Chọn website');
  sel.disabled = U.scanning;      // chỉ đổi website khi không có job chạy
  r1.append(sel);
  r1.append(h('span', `pill ${U.loggedIn ? 'ok' : 'warn'}`,
    U.loggedIn ? 'Đã đăng nhập' : 'Cần đăng nhập'));
  r1.append(h('span', 'grow'));
  r1.append(btn('Kiểm tra môi trường', '', () => {
    U.envCheck = flags().has('enverr') ? 'err' : 'ok';
    P.rerenderModule();
  }));
  r1.append(btn('Mở đăng nhập', 'secondary', () => {
    flags().add('waiting'); P.rerenderModule();
    P.toast('Cửa sổ Chromium đăng nhập mở (demo — không mở thật).');
  }));
  b1.append(r1);

  if (flags().has('enverr')) {
    const err = h('div', 'banner err');
    err.style.marginTop = '8px';
    err.append(h('span', 'grow',
      'env_check_failed — chưa tìm thấy Chromium/Playwright. Cài gói runtime rồi thử lại.'));
    err.append(btn('Thử lại', 'sm', () => { flags().delete('enverr'); U.envCheck = 'ok'; P.rerenderModule(); }));
    b1.append(err);
  } else if (U.envCheck === 'ok') {
    const ok = h('div', 'banner ok');
    ok.style.marginTop = '8px';
    ok.append(h('span', 'grow', 'Môi trường sẵn sàng: Python ✓ · Chromium ✓ · Excel reader ✓'));
    b1.append(ok);
  }
  c1.append(b1);
  el.append(c1);

  /* vùng nguồn sổ */
  const c2 = h('div', 'card');
  const b2 = h('div', 'card-body');
  const r2 = h('div', 'ul-row');
  r2.append(h('span', 'lbl', 'Từ ngày'));
  const d1 = h('input', 'input'); d1.value = U.fromDate; d1.style.width = '118px';
  d1.placeholder = 'DD/MM/YYYY'; d1.setAttribute('aria-label', 'Từ ngày');
  d1.addEventListener('input', () => { U.fromDate = d1.value; U.staleResult = true; updStale(b2); });
  const d2 = h('input', 'input'); d2.value = U.toDate; d2.style.width = '118px';
  d2.placeholder = 'DD/MM/YYYY'; d2.setAttribute('aria-label', 'Đến ngày');
  d2.addEventListener('input', () => { U.toDate = d2.value; U.staleResult = true; updStale(b2); });
  r2.append(d1, h('span', 'lbl', 'Đến ngày'), d2);
  r2.append(btn('Tải Excel từ Web', 'secondary', () => {
    if (!U.loggedIn) { P.toast('Cần đăng nhập website trước.', 'warn'); return; }
    U.excelPath = 'D:\\Download\\so_cong_chung_nam_dinh_2024_ban_tai_ve_ngay_28_09_2026.xlsx';
    doAudit();
  }));
  r2.append(h('span', 'muted', '|'));
  const path = h('input', 'input'); path.readOnly = true;
  path.value = U.excelPath; path.title = U.excelPath || 'Chưa chọn tệp Excel';
  path.style.width = '280px';
  path.setAttribute('aria-label', 'Đường dẫn file Excel');
  r2.append(path, btn('Chọn tệp Excel…', '', () => {
    U.excelPath = 'D:\\Tai_lieu\\bo_so_cong_chung\\so_cong_chung_nam_dinh_2024_loc_tu_phong_mot_cua.xlsx';
    U.staleResult = true; P.rerenderModule();
  }));
  r2.append(btn('Nạp dữ liệu', 'primary sm', doAudit));
  b2.append(r2);
  const stale = h('div', 'js-stale');
  if (U.staleResult && U.kpi) {
    stale.append(h('span', 'pill warn', 'Kết quả chưa cập nhật — đã đổi ngày/file'));
    stale.style.marginTop = '6px';
  }
  b2.append(stale);
  c2.append(b2);
  el.append(c2);

  /* KPI */
  const kpis = h('div', 'ul-kpis');
  const kv = U.kpi || { loaded: '—', valid: '—', missing: '—', err: '—' };
  [['Tổng số đã nạp', kv.loaded], ['Hợp lệ trong sổ', kv.valid],
   ['Số còn thiếu', kv.missing], ['Lỗi / Trùng lặp', kv.err]].forEach(([l, v]) => {
    const k = h('div', 'card ul-kpi');
    k.append(h('div', 'v', String(v)), h('div', 'l', l));
    kpis.append(k);
  });
  el.append(kpis);

  /* hai bảng + splitter chiều cao */
  const box = h('div', 'audit-tables');
  box.style.minHeight = '0'; box.style.flex = '1';
  const p1 = auditPane('Số còn thiếu', U.missing);
  const sp = auditSplitter();
  const p2 = auditPane('Số lỗi, trùng', U.errs);
  box.append(p1, sp, p2);
  el.append(box);
}

function updStale(body) {
  const s = body.querySelector('.js-stale');
  if (s && !s.childElementCount) {
    s.append(h('span', 'pill warn', 'Kết quả chưa cập nhật — đã đổi ngày/file'));
    s.style.marginTop = '6px';
  }
}

function doAudit() {
  if (U.auditing) return;
  U.auditing = true;
  const t = setTimeout(() => {
    clearTimeout(t);
    const d = D.uploadData('std');
    U.kpi = d.kpi; U.missing = d.missing; U.errs = d.errs;
    U.staleResult = false; U.auditing = false;
    P.rerenderModule();
    P.toast('Đã nạp và audit xong (demo).', 'ok');
  }, 800);
  P.rerenderModule();
}

function auditPane(title, rows) {
  const pane = h('div', 'audit-pane');
  pane.style.flex = '1';
  const head = h('div', 'ul-row');
  head.style.padding = '2px 2px 6px';
  head.append(h('strong', '', title));
  head.append(h('span', 'pill muted', `${rows.length} dòng`));
  pane.append(head);
  const wrap = h('div', 'ul-table-wrap');
  wrap.dataset.scrollkey = `audit-${title}`;
  wrap.style.flex = '1'; wrap.style.minHeight = '0';
  if (flags().has('loading')) {
    wrap.append(P.faceLoading(`Đang tải ${title.toLowerCase()}…`));
  } else if (!rows.length) {
    wrap.append(P.faceEmpty(
      U.kpi ? 'Không có dòng nào.' : 'Chưa nạp sổ',
      U.kpi ? '' : 'Chọn tệp Excel hoặc tải từ web rồi Nạp dữ liệu.'));
  } else {
    const t = h('table', 'ul-grid');
    const th = h('thead'); const tr = h('tr');
    ['STT', 'Ngày', 'Số công chứng', 'Ghi chú'].forEach(c =>
      tr.append(h('th', c === 'STT' ? 'num' : '', c)));
    th.append(tr); t.append(th);
    const tb = h('tbody');
    for (const r of rows) {
      const tr = h('tr');
      tr.append(h('td', 'num', String(r.stt)));
      tr.append(h('td', 'num', r.ngay || '—'));
      tr.append(h('td', 'num', r.so));
      tr.append(h('td', '', r.note || ''));
      tb.append(tr);
    }
    t.append(tb);
    wrap.append(t);
  }
  pane.append(wrap);
  return pane;
}

function auditSplitter() {
  const s = h('div', 'splitter-h');
  s.style.margin = '0';
  s.tabIndex = 0; s.setAttribute('role', 'separator');
  s.setAttribute('aria-label', 'Kéo đổi chiều cao hai bảng audit');
  s.title = 'Kéo để đổi chiều cao hai bảng (bàn phím: ↑/↓)';
  let drag = null;
  s.addEventListener('mousedown', (e) => { drag = { y: e.clientY }; s.classList.add('active'); e.preventDefault(); });
  window.addEventListener('mousemove', (e) => {
    if (!drag) return;
    const p1 = s.previousElementSibling;
    if (p1) {
      const cur = p1.getBoundingClientRect().height;
      const nx = Math.max(80, cur + (e.clientY - drag.y));
      p1.style.flex = `0 0 ${nx}px`;
      drag.y = e.clientY;
    }
  });
  window.addEventListener('mouseup', () => { drag = null; s.classList.remove('active'); });
  s.addEventListener('keydown', (e) => {
    const p1 = s.previousElementSibling;
    if (!p1) return;
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault();
      const cur = p1.getBoundingClientRect().height;
      p1.style.flex = `0 0 ${Math.max(80, cur + (e.key === 'ArrowDown' ? 24 : -24))}px`;
    }
  });
  return s;
}

/* ========================= TAB QUÉT & UPLOAD ========================== */
function buildScan(el) {
  /* ngữ cảnh */
  const c0 = h('div', 'card');
  const b0 = h('div', 'card-body');
  const r0 = h('div', 'ul-row');
  r0.append(h('span', 'lbl', 'Website'));
  r0.append(h('strong', '', U.website));
  r0.append(h('span', `pill ${U.loggedIn ? 'ok' : 'warn'}`,
    U.loggedIn ? 'Phiên đăng nhập hợp lệ' : 'Chưa đăng nhập'));
  if (U.excelPath) {
    r0.append(h('span', 'muted small', `Nguồn: ${U.excelPath.split('\\').pop()} · ${U.fromDate}–${U.toDate}`));
  } else {
    r0.append(h('span', 'pill warn', 'Chưa có sổ Excel — vẫn quét được nhưng không tự chọn "thiếu"'));
  }
  r0.append(h('span', 'grow'));
  const back = h('button', 'btn sm', 'Sang tab Audit để đổi website');
  back.type = 'button';
  back.addEventListener('click', () => {
    U.tab = 'audit';
    document.querySelector('.ul-panel[data-tab="scan"]').style.display = 'none';
    const pa = document.querySelector('.ul-panel[data-tab="audit"]');
    pa.hidden = false; pa.style.display = 'flex';
    document.querySelectorAll('.ul-tab').forEach((x, i) =>
      x.setAttribute('aria-selected', String(i === 0)));
  });
  r0.append(back);
  b0.append(r0);
  c0.append(b0);
  el.append(c0);

  /* nguồn + nhân sự */
  const c1 = h('div', 'card');
  const b1 = h('div', 'card-body');
  const r1 = h('div', 'ul-row');
  r1.append(btn('Chọn thư mục', '', () => {
    U.folder = 'D:\\HoSo\\2024\\Scan\\bo_sung_dot_2';
    P.rerenderModule();
  }));
  const fp = h('input', 'input'); fp.readOnly = true; fp.value = U.folder;
  fp.title = U.folder || 'Chưa chọn thư mục'; fp.style.width = '300px';
  fp.setAttribute('aria-label', 'Thư mục hồ sơ');
  r1.append(fp);
  const scan = btn('Bắt đầu Quét', 'primary sm', () => {
    U.scanning = true;
    const t = setTimeout(() => {
      clearTimeout(t);
      U.scanning = false; U.scanPct = 100;
      if (!U.queue.length) U.queue = D.uploadData('std').queue;
      P.rerenderModule();
      P.toast('Quét xong — lượt quét mới, lựa chọn cũ đã reset (demo).');
    }, 900);
    P.rerenderModule();
  });
  scan.disabled = U.scanning || !U.folder;
  r1.append(scan);
  r1.append(h('span', 'muted', '|'));
  r1.append(h('span', 'lbl', 'Công chứng viên'));
  const ccv = h('select', 'input'); ccv.style.width = '190px';
  ['Nguyễn Thị Hoa', 'Phạm Văn Ký', 'Lê Đức Thành'].forEach(n => {
    const o = h('option', '', n); ccv.append(o);
  });
  ccv.value = U.ccv;
  ccv.addEventListener('change', () => { U.ccv = ccv.value; });
  r1.append(ccv);
  r1.append(h('span', 'lbl', 'Thư ký'));
  const tk = h('input', 'input'); tk.value = U.thuky; tk.style.width = '160px';
  tk.addEventListener('input', () => { U.thuky = tk.value; });
  r1.append(tk);
  r1.append(btn('Cập nhật danh sách', '', () => P.toast('Đã làm mới danh sách nhân sự (demo).')));
  r1.append(h('span', 'lbl', 'Số tab mỗi đợt'));
  const nt = h('input', 'input'); nt.type = 'number'; nt.min = 1; nt.max = 30;
  nt.value = U.tabsPerBatch; nt.style.width = '64px';
  nt.setAttribute('aria-label', 'Số tab mỗi đợt (1–30)');
  nt.addEventListener('change', () => {
    let v = Math.round(Number(nt.value) || 10);
    v = Math.min(30, Math.max(1, v)); nt.value = v; U.tabsPerBatch = v;
  });
  r1.append(nt);
  b1.append(r1);

  /* tiến độ */
  const pr = h('div', 'ul-row'); pr.style.marginTop = '10px';
  pr.append(h('span', 'lbl', 'Quét'));
  const p1 = h('div', 'progress'); p1.append(h('i')); p1.firstChild.style.width = `${U.scanPct}%`;
  pr.append(p1, h('span', 'progress-lbl', `${U.scanPct}%`));
  pr.append(h('span', 'lbl', 'Chuẩn bị biểu mẫu'));
  const p2 = h('div', 'progress'); p2.append(h('i')); p2.firstChild.style.width = `${U.prepPct}%`;
  pr.append(p2, h('span', 'progress-lbl', `${U.prepPct}%`));
  const stop = btn('Dừng', '', () => {
    P.openModal((box, close) => {
      const hd = h('div', 'modal-head');
      hd.append(h('h2', 'modal-title', 'Dừng tác vụ đang chạy?'), modalX(close));
      box.append(hd);
      box.append(h('div', 'modal-body',
        'Dừng sau đơn vị đang xử lý; các tab người đang kiểm tra không tự đóng. ' +
        'Hủy không hoàn tác một lần Lưu đã xảy ra.'));
      const f = h('div', 'modal-foot');
      f.append(btn('Tiếp tục chạy', '', close));
      f.append(btn('Dừng', 'danger-ghost', () => {
        close(); U.scanning = false; P.rerenderModule();
        P.toast('Đã yêu cầu dừng (demo).', 'warn');
      }));
      box.append(f);
    });
  });
  stop.disabled = !U.scanning && !flags().has('waiting');
  pr.append(stop);
  b1.append(pr);
  c1.append(b1);
  el.append(c1);

  /* banner chờ người / cần đối chiếu */
  if (flags().has('waiting')) {
    const w = h('div', 'banner warn');
    w.append(h('span', 'grow',
      'Đang chờ kiểm tra — đợt biểu mẫu đã điền sẵn trong Chromium. Kiểm tra và bấm Lưu từng tab, rồi xác nhận tại đây.'));
    w.append(btn('Mở lại trình duyệt', 'sm', () => P.toast('Đưa cửa sổ Chromium lên trước (demo).')));
    w.append(btn('Xác nhận xong kiểm tra', 'secondary sm', () => {
      flags().delete('waiting'); P.rerenderModule();
      P.toast('Đã ghi nhận xong kiểm tra (demo — không phải bằng chứng Lưu).');
    }));
    el.append(w);
  }
  if (flags().has('reconcile')) {
    const w = h('div', 'banner warn');
    w.append(h('span', 'grow',
      '3 hồ sơ có thể đã Lưu nhưng chưa xác minh được — cần đối chiếu sổ mới hoặc xác nhận tay trước khi gửi lại.'));
    w.append(btn('Đối chiếu ngay', 'secondary sm', () => P.toast('Chạy đối chiếu sổ mới (demo).')));
    el.append(w);
  }

  /* thanh thao tác */
  const c2 = h('div', 'card');
  const b2 = h('div', 'card-body');
  const act = h('div', 'ul-row');
  const selCount = () => U.queue.filter(r => r.sel).length;
  act.append(btn('Chọn tất cả', 'sm', () => { U.queue.forEach(r => r.sel = true); resortQueue(); }));
  act.append(btn('Bỏ chọn tất cả', 'sm', () => { U.queue.forEach(r => r.sel = false); resortQueue(); }));
  const filt = btn(U.filterErr ? 'Hoàn tác lọc' : 'Lọc số lỗi', 'sm', () => {
    U.filterErr = !U.filterErr; P.rerenderModule();
  });
  act.append(filt);
  act.append(btn('Số thiếu trong Excel', 'sm', () => {
    let n = 0;
    U.queue.forEach(r => { const on = r.state === 'ok'; if (on) n++; r.sel = on; });
    resortQueue();
    P.toast(`Đã chọn ${n} số chưa có trong sổ (demo).`);
  }));
  act.append(h('span', 'grow'));
  const up = btn(`Upload file đã chọn (${selCount()})`, 'primary sm', () => {
    flags().add('waiting'); P.rerenderModule();
    P.toast(`Bắt đầu đợt ${Math.min(U.tabsPerBatch, selCount())} tab đầu (demo).`);
  });
  up.disabled = !selCount() || U.scanning;
  act.append(up);
  const next = btn(`Tiếp tục ${U.tabsPerBatch} số tiếp theo`, 'secondary sm', () => {
    P.toast(`Mở đợt ${U.tabsPerBatch} tab kế tiếp — chỉ khi người bấm (demo).`);
  });
  next.disabled = !flags().has('waiting');
  act.append(next);
  act.append(btn('Đóng browser upload', 'danger-ghost sm', () => {
    P.toast('Đóng trình duyệt upload (demo) — tab đang kiểm tra không tự đóng.', 'warn');
  }));
  b2.append(act);
  c2.append(b2);
  el.append(c2);

  /* bảng queue 6 cột */
  const c3 = h('div', 'card');
  c3.style.flex = '1'; c3.style.display = 'flex'; c3.style.flexDirection = 'column'; c3.style.minHeight = '0';
  const head3 = h('div', 'card-head');
  head3.append(h('h3', 'card-title', `Hàng chờ (${U.queue.length} hồ sơ · đã chọn ${selCount()})`));
  c3.append(head3);
  const wrap = h('div', 'ul-table-wrap');
  wrap.dataset.scrollkey = 'queue';
  wrap.style.flex = '1';
  if (flags().has('loading')) {
    wrap.append(P.faceLoading('Đang tải hàng chờ…'));
  } else if (!U.queue.length) {
    wrap.append(P.faceEmpty('Chưa có hồ sơ',
      'Chọn thư mục rồi Bắt đầu Quét — vẫn quét được khi chưa có Excel.',
      'Bắt đầu Quét', () => {
        U.folder = 'D:\\HoSo\\2024\\Scan';
        U.scanning = true; P.rerenderModule();
        setTimeout(() => {
          U.scanning = false; U.scanPct = 100;
          U.queue = D.uploadData('std').queue; P.rerenderModule();
        }, 800);
      }));
  } else {
    wrap.append(queueTable());
  }
  c3.append(wrap);
  el.append(c3);
}

function resortQueue() {
  // quy tắc spec_UI §3: dòng đã chọn xếp lên đầu (dùng record_id, không STT)
  U.queue.sort((a, b) => (b.sel - a.sel) || (a.stt - b.stt));
  P.rerenderModule();
}

const STATE_PILL = {
  filled: ['accent', 'Đã điền sẵn'],
  review: ['warn', 'Đang chờ kiểm tra'],
  saved: ['ok', 'Đã lưu trên web'],
  reconcile: ['warn', 'Cần đối chiếu'],
  err: ['err', 'Lỗi'],
};

function queueTable() {
  const t = h('table', 'ul-grid');
  const th = h('thead'); const tr = h('tr');
  const cbAll = h('input'); cbAll.type = 'checkbox'; cbAll.className = 'cb';
  const rows = U.queue.filter(r => !U.filterErr || r.state === 'err' || r.state === 'reconcile');
  cbAll.checked = rows.length > 0 && rows.every(r => r.sel);
  cbAll.setAttribute('aria-label', 'Chọn tất cả hồ sơ');
  cbAll.addEventListener('change', () => {
    rows.forEach(r => r.sel = cbAll.checked); resortQueue();
  });
  const thc = h('th'); thc.style.width = '30px'; thc.append(cbAll); tr.append(thc);
  ['STT', 'Ngày', 'Số công chứng', 'Ghi chú', 'Địa chỉ file'].forEach((c, i) =>
    tr.append(h('th', i === 0 || i === 1 || i === 2 ? 'num' : '', c)));
  th.append(tr); t.append(th);
  const tb = h('tbody');
  for (const r of rows) {
    const tr = h('tr');
    if (r.sel) tr.classList.add('selected');
    const c0 = h('td');
    const cb = h('input'); cb.type = 'checkbox'; cb.className = 'cb';
    cb.checked = r.sel;
    cb.setAttribute('aria-label', `Chọn hồ sơ ${r.so}`);
    cb.addEventListener('change', () => { r.sel = cb.checked; resortQueue(); });
    c0.append(cb); tr.append(c0);
    tr.append(h('td', 'num', String(r.stt)));
    tr.append(h('td', 'num', r.ngay));
    tr.append(h('td', 'num', r.so));
    const cg = h('td');
    const sp = STATE_PILL[r.state];
    if (sp) cg.append(h('span', `pill ${sp[0]}`, sp[1]));
    if (r.note && r.note !== sp?.[1]) cg.append(h('span', 'muted', ` ${r.note}`));
    tr.append(cg);
    const cp = h('td', 'pathcell');
    const p = h('span', 'p', r.path);
    p.title = r.path;         // tooltip xem đủ đường dẫn
    cp.append(p);
    tr.append(cp);
    tb.append(tr);
  }
  t.append(tb);
  return t;
}

function modalX(close) {
  const x = h('button', 'modal-close', '×');
  x.type = 'button'; x.setAttribute('aria-label', 'Đóng');
  x.addEventListener('click', close);
  return x;
}

})();
