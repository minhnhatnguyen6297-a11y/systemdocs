/* ==========================================================================
   app.js — lõi bản mẫu: DOM helper, modal có focus trap, toast, thanh demo,
   khung nhìn (viewport) và điều hướng module. Dữ liệu giả, không backend.
   ========================================================================== */
'use strict';

window.P = (() => {

  /* ---------- DOM helper ---------- */
  const h = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  };
  const btn = (label, cls, onClick) => {
    const b = h('button', `btn ${cls || ''}`.trim(), label);
    b.type = 'button';
    if (onClick) b.addEventListener('click', onClick);
    return b;
  };
  const svgIcon = (d) => {
    // icon 22px, stroke đơn giản — chỉ cho rail demo
    const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('fill', 'none');
    s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '1.8');
    s.setAttribute('stroke-linecap', 'round');
    s.setAttribute('stroke-linejoin', 'round');
    s.setAttribute('aria-hidden', 'true');
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', d);
    s.append(p);
    return s;
  };
  const ICONS = {
    notary: 'M6 2h9l5 5v15H6z M14 2v6h6 M9 13h8M9 17h8M9 9h2',
    upload: 'M12 16V4M7 9l5-5 5 5 M4 20h16',
    office: 'M3 21h18 M5 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16 M15 9h4a2 2 0 0 1 2 2v10 M9 7h2M9 11h2M9 15h2',
    search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M21 21l-4.3-4.3',
    gear: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
    doc: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6',
  };

  /* ---------- faces (Loading/Empty/Error/Unavailable) ---------- */
  function face(kind, title, detail, actionLabel, onAction) {
    const box = h('div', 'face');
    if (title) box.append(h('div', 'face-title', title));
    if (detail) box.append(h('div', '', detail));
    if (actionLabel) box.append(btn(actionLabel, 'secondary sm', onAction));
    return box;
  }
  const faceEmpty = (t, d, l, f) => face('empty', t, d, l, f);
  const faceLoading = (t) => {
    const b = face('loading', '', t || 'Đang tải…');
    const bar = h('div', 'skeleton'); bar.style.width = '60%'; bar.style.height = '14px';
    const bar2 = h('div', 'skeleton'); bar2.style.width = '40%'; bar2.style.height = '14px';
    b.prepend(bar, bar2);
    return b;
  };
  const faceError = (code, msg, retryable, onRetry) => {
    const b = face('error', 'Không tải được', `${code} — ${msg}`);
    if (retryable) b.append(btn('Thử lại', 'secondary sm', onRetry));
    return b;
  };
  const faceUnavail = (cap, why) =>
    face('unavailable', `${cap} — chưa khả dụng`, why);

  /* ---------- toast ---------- */
  function toast(msg, tone) {
    const t = h('div', `toast ${tone || ''}`.trim(), msg);
    t.setAttribute('role', 'status');
    document.getElementById('toastRoot').append(t);
    setTimeout(() => t.remove(), 4200);
  }

  /* ---------- modal (focus trap + trả focus) ---------- */
  let modalStack = [];
  function openModal(build, opts) {
    const root = document.getElementById('modalRoot');
    const overlay = h('div', 'modal-overlay');
    const box = h('div', `modal ${opts && opts.wide ? 'wide' : ''}`.trim());
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    overlay.append(box);
    const opener = document.activeElement;
    const close = () => {
      overlay.remove();
      modalStack = modalStack.filter(x => x !== ctx);
      if (opener && opener.isConnected) opener.focus();
    };
    const ctx = { overlay, box, close };
    modalStack.push(ctx);
    build(box, close);
    root.append(overlay);
    // focus trap
    overlay.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key !== 'Tab') return;
      const els = box.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      const list = [...els].filter(el => !el.disabled && el.offsetParent !== null);
      if (!list.length) return;
      const first = list[0], last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    // click nền ngoài không đóng (giữ hành vi app); Esc đóng.
    const focusables = box.querySelectorAll(
      'button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const target = box.querySelector('[autofocus]') ||
      box.querySelector('.modal-body input, .modal-body select') || focusables[0];
    if (target) target.focus();
    return close;
  }

  /* ---------- state toàn cục demo ---------- */
  const state = {
    module: 'notary',
    flags: new Set(),           // error/loading/stale/conflict/locked/mock/waiting/reconcile/enverr
    notary: null,               // do notary.js build
    upload: null,               // do upload.js build
  };

  const RAIL = [
    { id: 'notary', title: 'notary_v2 — Soạn hồ sơ', icon: 'notary' },
    { id: 'upload', title: 'upload_lab — Audit / Quét-upload', icon: 'upload' },
    { id: 'office', title: 'notaryoffice (placeholder)', icon: 'office' },
    { id: 'search', title: 'Tra cứu (tiện ích shell)', icon: 'search' },
  ];

  function buildRail() {
    const rail = document.getElementById('rail');
    rail.innerHTML = '';
    rail.append(h('div', 'rail-logo', 'N'));
    for (const item of RAIL) {
      const b = h('button', `rail-btn ${state.module === item.id ? 'active' : ''}`);
      b.type = 'button';
      b.title = item.title;
      b.setAttribute('aria-label', item.title);
      b.append(svgIcon(ICONS[item.icon]));
      if (item.id === 'notary' || item.id === 'upload') {
        b.addEventListener('click', () => setModule(item.id));
      } else {
        b.addEventListener('click', () =>
          toast(`${item.title}: mục demo, không có nội dung trong bản mẫu.`, 'warn'));
      }
      rail.append(b);
    }
    rail.append(h('div', 'rail-spacer'));
    const gear = h('button', 'rail-btn');
    gear.type = 'button';
    gear.title = 'Trạng thái/Cài đặt (tiện ích shell)';
    gear.setAttribute('aria-label', 'Trạng thái/Cài đặt');
    gear.append(svgIcon(ICONS.gear));
    gear.addEventListener('click', () =>
      toast('Trạng thái/Cài đặt: tiện ích shell — ngoài phạm vi bản mẫu.', 'warn'));
    rail.append(gear);
  }

  /* ---------- render dispatch ---------- */
  const renderers = {};  // module → fn(el)
  function render() {
    buildRail();
    const elNotary = document.getElementById('screen-notary');
    const elUpload = document.getElementById('screen-upload');
    elNotary.hidden = state.module !== 'notary';
    elUpload.hidden = state.module !== 'upload';
    const el = state.module === 'notary' ? elNotary : elUpload;
    if (renderers[state.module]) renderers[state.module](el);
    syncDemoBar();
  }

  // Giữ vị trí cuộn của các vùng cuộn chính qua re-render (draft/reorder…)
  const SCROLL_SEL = ['.module-content', '.stage-body', '.canvas-wrap',
                      '.pool-box', '.audit-pane', '.ul-table-wrap'];
  function snapshotScroll(el) {
    const m = {};
    el.querySelectorAll(SCROLL_SEL.join(',')).forEach((n, i) => {
      m[n.dataset.scrollkey || i] = { t: n.scrollTop, l: n.scrollLeft };
    });
    return m;
  }
  function restoreScroll(el, snap) {
    el.querySelectorAll(SCROLL_SEL.join(',')).forEach((n, i) => {
      const s = snap[n.dataset.scrollkey || i];
      if (s) { n.scrollTop = s.t; n.scrollLeft = s.l; }
    });
  }
  function rerenderModule() {
    const el = state.module === 'notary'
      ? document.getElementById('screen-notary')
      : document.getElementById('screen-upload');
    const snap = snapshotScroll(el);
    if (renderers[state.module]) renderers[state.module](el);
    restoreScroll(el, snap);
  }

  function setModule(id) {
    if (state.module === id) return;
    state.module = id;
    render();
  }

  /* ---------- thanh demo ---------- */
  function syncDemoBar() {
    document.querySelectorAll('[data-for]').forEach(el => {
      el.hidden = el.dataset.for !== state.module;
    });
    document.getElementById('demoModule').value = state.module;
    document.querySelectorAll('.demo-flag').forEach(b => {
      b.setAttribute('aria-pressed', String(state.flags.has(b.dataset.flag)));
    });
  }

  function initDemoBar() {
    document.getElementById('demoModule').addEventListener('change', (e) =>
      setModule(e.target.value));
    document.getElementById('demoDiagram').addEventListener('change', (e) => {
      if (P.setNotaryDiagram) P.setNotaryDiagram(e.target.value);
    });
    document.getElementById('demoScenarioNotary').addEventListener('change', (e) => {
      if (P.setNotaryScenario) P.setNotaryScenario(e.target.value);
    });
    document.getElementById('demoScenarioUpload').addEventListener('change', (e) => {
      if (P.setUploadScenario) P.setUploadScenario(e.target.value);
    });
    document.querySelectorAll('.demo-flag').forEach(b => {
      b.addEventListener('click', () => {
        const f = b.dataset.flag;
        if (f === 'conflict') {
          // conflict là dialog một lần, không phải cờ
          if (P.openConflictDemo) P.openConflictDemo();
          return;
        }
        if (state.flags.has(f)) state.flags.delete(f); else state.flags.add(f);
        rerenderModule(); syncDemoBar();
      });
    });
    document.getElementById('demoViewport').addEventListener('change', (e) => {
      const vp = document.getElementById('vp');
      const v = e.target.value;
      if (v === 'full') {
        vp.classList.remove('vp-fixed');
        vp.style.width = ''; vp.style.height = '';
      } else {
        const [w, hgt] = v.split('x').map(Number);
        vp.classList.add('vp-fixed');
        vp.style.width = `${w}px`; vp.style.height = `${hgt}px`;
      }
    });
  }

  function init() {
    initDemoBar();
    if (P.initNotary) P.initNotary();
    if (P.initUpload) P.initUpload();
    render();
  }

  return { h, btn, svgIcon, ICONS, face, faceEmpty, faceLoading, faceError,
           faceUnavail, toast, openModal, state, render, rerenderModule,
           renderers, init };
})();
