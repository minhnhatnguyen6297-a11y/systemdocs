/* ==========================================================================
   notary.js — màn Soạn hồ sơ: action bar, Stage (Tài sản bảng chuyển vị +
   Người bảng dòng), tầng quan hệ (Pool + sơ đồ thừa kế / hai bên), dialog
   loại đất, intake, conflict, stub Xuất Word. Dữ liệu giả — xem data.js.

   Đề xuất ban đầu ghi ở README.md + .agent/tasks/MIN-126/decisions.md —
   ĐÃ ĐƯỢC owner chốt 27/09/2026 (docs/spec/ui + contract §13 v2): semantics
   chip số, drop lên chỗ có người = swap, `Hủy thay đổi` = revert Stage
   draft, `Mở rộng` = canvas toàn màn.
   ========================================================================== */
'use strict';

(() => {
const { h, btn } = P;
const D = P_DATA;

/* ------------------------------ state ------------------------------ */
let S = null;

function newSession(scenario) {
  const d = D.NOTARY_SCENARIOS[scenario]();
  S = {
    scenario,
    diagramKind: S ? S.diagramKind : 'thua-ke',
    caseType: S && S.diagramKind === 'hai-ben' ? 'Hai bên' : 'Thừa kế',
    assets: d.assets,
    people: d.people,
    committed: null,                       // snapshot sau "Cập nhật"
    nodes: d.nodes.map(n => ({ ...n })),
    slots: { ...d.slots },
    committedDiagram: null,
    stageDirty: false,
    diagramDirty: false,
    evalStale: false,
    zoom: 1,
    calcOpen: false,
    fieldErrors: [],                       // [{rowId, field, msg}]
    tray: null,                            // suggestion tray intake
    saveLabel: 'Chưa lưu — hồ sơ nháp',
    caseId: null,                          // nháp mới → nút "Lưu hồ sơ"
    poolQuery: '',
  };
  // Kịch bản "đã commit sẵn": coi dữ liệu nạp ban đầu là đã commit trừ
  // kịch bản trống (để minh họa draft → commit → Pool tính lại).
  if (scenario !== 'empty') {
    S.committed = { assets: clone(S.assets), people: clone(S.people) };
    S.committedDiagram = { nodes: clone(S.nodes), slots: clone(S.slots) };
    S.saveLabel = 'Đã lưu lúc 09:41';
    S.caseId = 'HS-2024-0187';
  }
}
const clone = (o) => JSON.parse(JSON.stringify(o));

P.setNotaryScenario = (name) => { newSession(name); P.rerenderModule(); };
P.setNotaryDiagram = (kind) => {
  S.diagramKind = kind;
  S.caseType = kind === 'hai-ben' ? 'Hai bên' : 'Thừa kế';
  P.rerenderModule();
};
P.initNotary = () => newSession('std');

/* --------------------------- derived ------------------------------- */
const flags = () => P.state.flags;
const ro = () => flags().has('locked');    // read-only khi locked

function committedPeople() { return (S.committed && S.committed.people) || []; }
function committedAssets() { return (S.committed && S.committed.assets) || []; }
function personById(id) {
  return committedPeople().find(p => p.id === id) ||
         S.people.find(p => p.id === id);
}
function assignedIds() {
  // Pool trừ theo sơ đồ ĐANG hiển thị (thừa kế dùng nodes, hai bên dùng slots)
  const set = new Set();
  if (S.diagramKind === 'hai-ben') {
    for (const k of Object.keys(S.slots)) if (S.slots[k]) set.add(S.slots[k]);
  } else {
    for (const n of S.nodes) if (n.personId) set.add(n.personId);
  }
  return set;
}
function poolPeople() {
  const a = assignedIds();
  return committedPeople().filter(p => !a.has(p.id));
}

/* --------------------------- stage ops ----------------------------- */
function markStageDirty() {
  S.stageDirty = true;
  updateDirtyUI();
}
function updateDirtyUI() {
  const el = document.getElementById('screen-notary');
  const upd = el.querySelector('.js-update-btn');
  if (upd) {
    upd.querySelector('.dirty-dot')?.remove();
    if (S.stageDirty) upd.append(h('span', 'dirty-dot'));
  }
  const save = el.querySelector('.js-save-diagram');
  if (save) {
    save.querySelector('.dirty-dot')?.remove();
    if (S.diagramDirty) save.append(h('span', 'dirty-dot'));
  }
  const lbl = el.querySelector('.save-state');
  if (lbl) lbl.textContent = S.stageDirty
    ? 'Có thay đổi chưa cập nhật' : S.saveLabel;
}

function validateStage() {
  const errs = [];
  S.people.forEach((p) => {
    if (!p.ho_ten || !p.ho_ten.trim()) {
      errs.push({ rowId: p.id, field: 'ho_ten', msg: 'Thiếu họ tên' });
    }
    for (const f of ['ngay_sinh', 'ngay_mat']) {
      const v = p[f];
      if (v && !/^\d{2}\/\d{2}\/\d{4}$/.test(v.trim())) {
        errs.push({ rowId: p.id, field: f, msg: 'Ngày dạng DD/MM/YYYY' });
      }
    }
  });
  S.assets.forEach((a) => {
    if (!a.so_serial || !a.so_serial.trim()) {
      errs.push({ rowId: a.id, field: 'so_serial', msg: 'Thiếu số serial' });
    }
  });
  return errs;
}

function commitStage() {
  const errs = validateStage();
  if (errs.length) {
    S.fieldErrors = errs;
    P.rerenderModule();
    P.toast(`Cập nhật không thành công — ${errs.length} trường cần sửa (lỗi gắn đúng dòng).`, 'err');
    return;
  }
  S.fieldErrors = [];
  S.committed = { assets: clone(S.assets), people: clone(S.people) };
  S.stageDirty = false;
  S.evalStale = S.diagramDirty;   // Stage đổi → kết quả đánh giá cũ
  if (S.caseId == null) {         // nháp mới → Lưu hồ sơ
    S.caseId = 'HS-2024-0193';
    S.committedDiagram = { nodes: clone(S.nodes), slots: clone(S.slots) };
    S.diagramDirty = false;
  }
  S.saveLabel = `Đã lưu lúc ${new Date().toTimeString().slice(0, 5)}`;
  P.rerenderModule();
  P.toast(S.caseId ? 'Đã cập nhật Stage — Pool tính lại.' : 'Đã lưu hồ sơ.', 'ok');
}

function discardStage() {
  // ĐỀ XUẤT (chờ P2): "Hủy thay đổi" = revert Stage draft về snapshot
  // commit gần nhất; KHÔNG đụng Diagram draft.
  P.openModal((box, close) => {
    box.append(h('div', 'modal-head'));
    box.querySelector('.modal-head').append(
      h('h2', 'modal-title', 'Hủy thay đổi Stage?'), modalClose(close));
    const body = h('div', 'modal-body');
    body.append(h('p', '',
      'Bỏ toàn bộ thay đổi chưa cập nhật trong Stage (Người + Tài sản) ' +
      'và quay về bản đã lưu gần nhất. Sơ đồ đang gán giữ nguyên.'));
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Giữ thay đổi', '', close));
    const ok = btn('Hủy thay đổi', 'primary', () => {
      if (S.committed) { S.assets = clone(S.committed.assets); S.people = clone(S.committed.people); }
      else { const d = D.NOTARY_SCENARIOS['empty'](); S.assets = d.assets; S.people = d.people; }
      S.stageDirty = false; S.fieldErrors = [];
      close(); P.rerenderModule();
    });
    foot.append(ok);
    box.append(foot);
    ok.focus();
  });
}

/* ----------------------- drag payload helpers ----------------------- */
const DT = 'application/x-person';
function setDragPayload(e, personId, fromNodeId) {
  e.dataTransfer.setData(DT, JSON.stringify({ personId, from: fromNodeId || null }));
  e.dataTransfer.effectAllowed = 'move';
}
function getDragPayload(e) {
  try { return JSON.parse(e.dataTransfer.getData(DT)); } catch { return null; }
}

// Gán/di chuyển người giữa node (thừa kế), slot (hai bên) và Pool.
// ĐỀ XUẤT chờ P2: thả lên vị trí ĐÃ CÓ NGƯỜI = đổi chỗ (swap); thả lên
// slot trống = move; kéo về Pool = bỏ gán.
function movePerson(personId, target) {
  // target: {node:id} | {slot:n} | null (pool)
  const curNode = S.nodes.find(n => n.personId === personId);
  const curSlot = Object.keys(S.slots).find(k => S.slots[k] === personId);
  const clearCurrent = () => {
    if (curNode) curNode.personId = null;
    if (curSlot != null) S.slots[curSlot] = null;
  };
  let swapTo = null;
  if (target && target.node) {
    const n = S.nodes.find(x => x.id === target.node);
    if (!n) return;
    swapTo = n.personId; n.personId = personId;
    if (swapTo && curNode) curNode.personId = swapTo;
    else if (swapTo && curSlot != null) S.slots[curSlot] = swapTo;
    else clearCurrent();
  } else if (target && target.slot != null) {
    const k = String(target.slot);
    swapTo = S.slots[k]; S.slots[k] = personId;
    if (swapTo && curNode) curNode.personId = swapTo;
    else if (swapTo && curSlot != null) S.slots[curSlot] = swapTo;
    else clearCurrent();
  } else {
    clearCurrent(); // về Pool
  }
  S.diagramDirty = true;
  P.rerenderModule();
}

/* ============================ RENDER ================================= */
P.renderers.notary = (el) => {
  const snap = P.state; // module-level render full
  el.innerHTML = '';

  const content = h('div', 'module-content');
  if (flags().has('mock')) {
    const b = h('div', 'banner warn');
    b.append(h('span', 'grow', 'MOCK — đang xem dữ liệu giả của bản mẫu, không phải backend thật.'));
    content.append(b);
  }
  content.append(actionBar());

  if (flags().has('loading')) {
    // Mặt Loading toàn vùng (demo) — không giả progress
    const c = h('div', 'card'); const cb = h('div', 'card-body');
    cb.append(P.faceLoading('Đang tải workspace…'));
    c.append(cb); content.append(c);
    const c2 = h('div', 'card rel-card'); const cb2 = h('div', 'card-body');
    cb2.append(P.faceLoading('Đang tải sơ đồ…'));
    c2.append(cb2); content.append(c2);
    el.append(content);
    return;
  }

  content.append(stageTier());
  content.append(splitterH());
  content.append(relationTier());
  el.append(content);
};

/* -------------------------- action bar ------------------------------ */
function actionBar() {
  const bar = h('div', 'actionbar');
  const back = h('button', 'ab-back', '‹'); back.type = 'button';
  back.title = 'Quay lại Tổng quan hồ sơ';
  back.setAttribute('aria-label', 'Quay lại Tổng quan hồ sơ');
  back.addEventListener('click', () =>
    S.stageDirty || S.diagramDirty
      ? openLeaveConfirm() : P.toast('Quay lại Tổng quan (demo — không điều hướng).'));
  bar.append(back);
  bar.append(h('h1', 'ab-title', 'Soạn văn bản'));

  const ct = h('select', 'case-type');
  ct.setAttribute('aria-label', 'Loại việc');
  ['Thừa kế', 'Hai bên'].forEach(t => {
    const o = h('option', '', t); o.value = t; ct.append(o);
  });
  ct.value = S.caseType;
  ct.addEventListener('change', () => P.setNotaryDiagram(ct.value === 'Hai bên' ? 'hai-ben' : 'thua-ke'));
  bar.append(ct);
  if (S.caseId) bar.append(h('span', 'pill accent', S.caseId));
  else bar.append(h('span', 'pill warn', 'Hồ sơ nháp'));

  bar.append(h('span', 'spacer'));
  bar.append(h('span', 'save-state', S.stageDirty ? 'Có thay đổi chưa cập nhật' : S.saveLabel));
  if (flags().has('stale')) bar.append(h('span', 'pill warn', 'đã cũ'));

  const intakeBtn = btn('', '', openIntake);
  const upIc = P.svgIcon('M12 16V4M7 9l5-5 5 5');
  upIc.style.width = '15px'; upIc.style.height = '15px';
  intakeBtn.append(upIc, h('span', '', 'Nhập file'));
  bar.append(intakeBtn);
  const zalo = btn('Zalo', '', null);
  zalo.disabled = true;           // ràng buộc MIN-123: Zalo disable
  zalo.title = 'Zalo — chưa bật trong phiên bản này';
  bar.append(zalo);
  // ĐỀ XUẤT (chờ P2): nút Hủy thay đổi được vẽ theo ảnh approved; semantics
  // discard vẫn chờ chốt — mẫu này demo "revert Stage draft về bản đã lưu".
  const undo = btn('Hủy thay đổi', '', discardStage);
  undo.disabled = !S.stageDirty || ro();
  bar.append(undo);
  const upd = btn(S.caseId == null ? 'Lưu hồ sơ' : 'Cập nhật', 'primary js-update-btn', commitStage);
  upd.disabled = ro() || (!S.stageDirty && S.caseId != null);
  if (S.stageDirty) upd.append(h('span', 'dirty-dot'));
  bar.append(upd);
  return bar;
}

function openLeaveConfirm() {
  P.openModal((box, close) => {
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', 'Rời màn khi còn thay đổi chưa lưu?'), modalClose(close));
    box.append(head);
    box.append(h('div', 'modal-body',
      'Có thay đổi chưa được Cập nhật / Lưu sơ đồ. Rời đi sẽ mất phần nháp trong phiên.'));
    const foot = h('div', 'modal-foot');
    foot.append(btn('Ở lại', '', close));
    foot.append(btn('Rời màn', 'danger-ghost', () => { close(); P.toast('Quay lại Tổng quan (demo).'); }));
    box.append(foot);
  });
}
function modalClose(close) {
  const x = h('button', 'modal-close', '×');
  x.type = 'button'; x.setAttribute('aria-label', 'Đóng');
  x.addEventListener('click', close);
  return x;
}

/* --------------------------- Stage tier ------------------------------ */
const ASSET_ROWS = [
  ['is_primary',  'Tài sản chính'],
  ['so_serial',   'Số serial'],
  ['so_vao_so',   'Số vào sổ'],
  ['so_thua_dat', 'Thửa đất'],
  ['so_to_ban_do','Tờ bản đồ'],
  ['land',        'Loại đất'],
  ['dia_chi',     'Địa chỉ'],
];
const PERSON_COLS = [
  ['ho_ten',     'Họ tên'],
  ['ngay_sinh',  'Ngày sinh'],
  ['ngay_mat',   'Ngày mất'],
  ['so_giay_to', 'Số giấy tờ'],
  ['dia_chi',    'Địa chỉ'],
];

function stageTier() {
  const tier = h('div', 'stage');
  tier.append(assetCard(), peopleCard());
  return tier;
}

function errFor(rowId, field) {
  return S.fieldErrors.find(e => e.rowId === rowId && e.field === field) ||
         (flags().has('error') ? demoError(rowId, field) : null);
}
// Lỗi giả cố định khi bật cờ "Lỗi trường" — để duyệt trạng thái mà không
// cần nhập liệu tay.
function demoError(rowId, field) {
  const p0 = S.people[1];
  const a0 = S.assets[0];
  if (p0 && rowId === p0.id && field === 'ho_ten') return { msg: 'Tên trùng 2 hồ sơ khác — kiểm tra lại' };
  if (a0 && rowId === a0.id && field === 'so_thua_dat') return { msg: 'Số thửa không hợp lệ' };
  return null;
}

/* Card Tài sản — bảng chuyển vị, cột kéo đổi thứ tự */
function assetCard() {
  const card = h('div', 'card card-assets');
  const head = h('div', 'card-head');
  head.append(h('h2', 'card-title', `Tài sản (${S.assets.length})`));
  const tools = h('div', 'card-tools');
  const add = btn('+ Tài sản', 'secondary sm', () => {
    S.assets.push(D.asset());
    markStageDirty(); P.rerenderModule();
  });
  add.disabled = ro();
  tools.append(add);
  head.append(tools);
  card.append(head);

  const body = h('div', 'stage-body');
  if (!S.assets.length) {
    body.append(P.faceEmpty('Chưa có tài sản', 'Thêm tài sản đầu tiên để bắt đầu soạn.', '+ Tài sản', () => {
      S.assets.push(D.asset()); markStageDirty(); P.rerenderModule();
    }));
    card.append(body); return card;
  }
  const scroll = h('div', '', null); scroll.style.overflow = 'auto';
  const t = h('table', 'grid transposed');

  // header: nhãn + các cột tài sản (kéo reorder)
  const tr = h('tr');
  const th0 = h('th', 'rowlabel', 'Thuộc tính'); tr.append(th0);
  S.assets.forEach((a, ci) => {
    const th = h('th', 'asset-col');
    th.dataset.col = ci;
    if (errFor(a.id)) th.classList.add('col-err');
    const wrap = h('div', 'col-head');
    const colHandle = dragHandle(`kéo đổi thứ tự Tài sản ${ci + 1}`, (e) => {
      e.dataTransfer.setData('application/x-assetcol', String(ci));
    });
    colHandle.addEventListener('keydown', (e) => {
      if (!e.ctrlKey) return;
      const to = e.key === 'ArrowLeft' ? ci - 1 : e.key === 'ArrowRight' ? ci + 1 : null;
      if (to == null || to < 0 || to >= S.assets.length) return;
      e.preventDefault();
      const [m] = S.assets.splice(ci, 1); S.assets.splice(to, 0, m);
      markStageDirty(); P.rerenderModule();
    });
    wrap.append(colHandle);
    wrap.append(h('span', 'grow', `Tài sản ${ci + 1}${a.is_primary ? ' ★' : ''}`));
    const del = h('button', 'icon-x', '×');
    del.type = 'button'; del.title = `Xóa Tài sản ${ci + 1}`;
    del.setAttribute('aria-label', `Xóa Tài sản ${ci + 1} (draft)`);
    del.disabled = ro();
    del.addEventListener('click', () => {
      S.assets.splice(ci, 1); markStageDirty(); P.rerenderModule();
    });
    wrap.append(del);
    th.append(wrap);
    th.addEventListener('dragover', (e) => {
      if (e.dataTransfer.types.includes('application/x-assetcol')) { e.preventDefault(); th.classList.add('col-drop-before'); }
    });
    th.addEventListener('dragleave', () => th.classList.remove('col-drop-before'));
    th.addEventListener('drop', (e) => {
      e.preventDefault(); th.classList.remove('col-drop-before');
      const from = Number(e.dataTransfer.getData('application/x-assetcol'));
      if (Number.isInteger(from) && from !== ci) {
        const [m] = S.assets.splice(from, 1);
        S.assets.splice(ci, 0, m);
        markStageDirty(); P.rerenderModule();
      }
    });
    tr.append(th);
  });
  const thead = h('thead'); thead.append(tr); t.append(thead);

  const tb = h('tbody');
  for (const [field, label] of ASSET_ROWS) {
    const r = h('tr');
    r.append(h('td', 'rowlabel', label));
    S.assets.forEach((a) => {
      const td = h('td');
      const err = errFor(a.id, field);
      if (field === 'is_primary') {
        const rd = h('input'); rd.type = 'radio'; rd.name = 'primary-asset';
        rd.checked = !!a.is_primary; rd.disabled = ro();
        rd.setAttribute('aria-label', `Đặt ${a.so_serial || 'cột này'} là tài sản chính`);
        rd.addEventListener('change', () => {
          S.assets.forEach(x => x.is_primary = (x === a));
          markStageDirty(); P.rerenderModule();
        });
        td.append(rd);
      } else if (field === 'land') {
        const c = h('button', 'chip-link',
          a.parcels.length ? `${a.parcels.length} loại ↗` : '+ Loại đất ↗');
        c.type = 'button';
        c.disabled = ro();
        c.addEventListener('click', () => openLandTypes(a));
        td.append(c);
      } else {
        const inp = h('input', `input ${err ? 'err' : ''}`);
        inp.value = a[field] || ''; inp.disabled = ro();
        inp.setAttribute('aria-label', `${label} — ${a.so_serial || 'tài sản'}`);
        inp.addEventListener('input', () => { a[field] = inp.value; markStageDirty(); });
        td.append(inp);
        if (err) {
          td.classList.add('cell-err');
          td.append(h('div', 'field-err-msg', err.msg));
        }
      }
      r.append(td);
    });
    tb.append(r);
  }
  t.append(tb);
  scroll.append(t);
  body.append(scroll);
  card.append(body);
  return card;
}

function dragHandle(label, onDragStart) {
  const d = h('button', 'drag-handle', '⋮⋮');
  d.type = 'button';
  d.title = `${label} — kéo hoặc Ctrl+phím mũi tên`;
  d.setAttribute('aria-label', label);
  d.draggable = !ro();
  if (onDragStart) d.addEventListener('dragstart', onDragStart);
  return d;
}

/* Card Người — bảng dòng, kéo đổi thứ tự */
function peopleCard() {
  const card = h('div', 'card card-people');
  const head = h('div', 'card-head');
  head.append(h('h2', 'card-title', `Người (${S.people.length})`));
  const tools = h('div', 'card-tools');
  const add = btn('+ Người', 'secondary sm', () => {
    S.people.push(D.person('')); markStageDirty(); P.rerenderModule();
  });
  add.disabled = ro();
  tools.append(add);
  head.append(tools);
  card.append(head);

  const body = h('div', 'stage-body');
  body.style.maxHeight = '290px';
  if (!S.people.length) {
    body.append(P.faceEmpty('Chưa có người', 'Nhập file gợi ý hoặc thêm người đầu tiên.',
      '+ Người', () => { S.people.push(D.person('')); markStageDirty(); P.rerenderModule(); }));
    card.append(body); return card;
  }
  const t = h('table', 'grid');
  const thead = h('thead');
  const trh = h('tr');
  trh.append(h('th', '', ''));
  for (const [, label] of PERSON_COLS) trh.append(h('th', '', label));
  trh.append(h('th', '', ''));
  thead.append(trh); t.append(thead);

  const tb = h('tbody');
  S.people.forEach((p, ri) => {
    const tr = h('tr');
    tr.dataset.row = ri;
    // drag handle + keyboard reorder (Ctrl+↑/↓)
    const tdh = h('td'); tdh.style.width = '30px';
    const dh = dragHandle(`kéo đổi thứ tự dòng ${ri + 1} (${p.ho_ten || 'chưa tên'})`, (e) => {
      e.dataTransfer.setData('application/x-personrow', String(ri));
      tr.classList.add('dragging');
    });
    dh.addEventListener('dragend', () => tr.classList.remove('dragging'));
    dh.addEventListener('keydown', (e) => {
      if (!e.ctrlKey) return;
      const to = e.key === 'ArrowUp' ? ri - 1 : e.key === 'ArrowDown' ? ri + 1 : null;
      if (to == null || to < 0 || to >= S.people.length) return;
      e.preventDefault();
      const [m] = S.people.splice(ri, 1); S.people.splice(to, 0, m);
      markStageDirty(); P.rerenderModule();
    });
    tdh.append(dh); tr.append(tdh);
    for (const [field] of PERSON_COLS) {
      const td = h('td');
      const err = errFor(p.id, field);
      const inp = h('input', `input ${err ? 'err' : ''}`);
      inp.value = p[field] || ''; inp.disabled = ro();
      if (field === 'dia_chi') inp.title = p[field] || '';
      inp.setAttribute('aria-label', `${field} — ${p.ho_ten || `dòng ${ri + 1}`}`);
      inp.addEventListener('input', () => { p[field] = inp.value; markStageDirty(); });
      td.append(inp);
      if (err) td.append(h('div', 'field-err-msg', err.msg));
      tr.append(td);
    }
    const tdx = h('td'); tdx.style.width = '30px';
    const del = h('button', 'icon-x', '×');
    del.type = 'button'; del.title = 'Xóa dòng (draft — hiệu lực sau Cập nhật)';
    del.setAttribute('aria-label', `Xóa ${p.ho_ten || `dòng ${ri + 1}`}`);
    del.disabled = ro();
    del.addEventListener('click', () => {
      S.people.splice(ri, 1); markStageDirty(); P.rerenderModule();
    });
    tdx.append(del); tr.append(tdx);

    tr.addEventListener('dragover', (e) => {
      if (e.dataTransfer.types.includes('application/x-personrow')) {
        e.preventDefault();
        const r = tr.getBoundingClientRect();
        tr.classList.toggle('row-drop-above', e.clientY < r.top + r.height / 2);
        tr.classList.toggle('row-drop-below', e.clientY >= r.top + r.height / 2);
      }
    });
    tr.addEventListener('dragleave', () => tr.classList.remove('row-drop-above', 'row-drop-below'));
    tr.addEventListener('drop', (e) => {
      e.preventDefault();
      tr.classList.remove('row-drop-above', 'row-drop-below');
      const from = Number(e.dataTransfer.getData('application/x-personrow'));
      if (!Number.isInteger(from) || from === ri) return;
      const r = tr.getBoundingClientRect();
      const to = e.clientY < r.top + r.height / 2 ? ri : ri + 1;
      const [m] = S.people.splice(from, 1);
      S.people.splice(to > from ? to - 1 : to, 0, m);
      markStageDirty(); P.rerenderModule();
    });
    tb.append(tr);
  });
  t.append(tb);
  body.append(t);

  // Suggestion tray (kết quả intake) — nằm dưới bảng trong card Người
  if (S.tray) body.append(trayEl());
  card.append(body);
  return card;
}

/* ----------------------- tầng quan hệ (Pool + diagram) --------------- */
function relationTier() {
  const card = h('div', 'card rel-card');
  const head = h('div', 'card-head');
  head.append(h('h2', 'card-title',
    S.diagramKind === 'hai-ben' ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế'));
  const tools = h('div', 'card-tools');

  if (S.diagramKind === 'thua-ke') {
    const addSlot = btn('+ Slot', 'sm', () => {
      S.nodes.push({ id: D.uid('n'), gen: maxGen() + 0, order: 999, personId: null,
                     parents: [], spouse: null, chu: [], nhan: [] });
      S.diagramDirty = true; P.rerenderModule();
    });
    addSlot.disabled = ro();
    tools.append(addSlot);
    const calc = btn('Xem cách tính', 'sm', () => { S.calcOpen = !S.calcOpen; P.rerenderModule(); });
    tools.append(calc);
    if (flags().has('stale')) tools.append(h('span', 'pill warn', 'Stage đã đổi kể từ lần đánh giá'));
  }
  tools.append(zoomCluster());
  head.append(tools);
  card.append(head);

  const body = h('div', 'rel-body');
  body.append(poolPane());
  body.append(splitterV());
  const dg = h('div', 'rel-diagram');
  dg.append(diagramCanvas());
  body.append(dg);
  card.append(body);

  const foot = h('div', 'rel-foot');
  const save = btn('Lưu sơ đồ', 'secondary js-save-diagram', () => {
    S.committedDiagram = { nodes: clone(S.nodes), slots: clone(S.slots) };
    S.diagramDirty = false;
    P.rerenderModule();
    P.toast('Đã lưu sơ đồ (demo — không ghi backend).', 'ok');
  });
  save.disabled = ro() || !S.diagramDirty || S.caseId == null;
  if (S.diagramDirty) save.append(h('span', 'dirty-dot'));
  const word = btn('Xuất Word', 'primary', openWordStub);
  foot.append(save, word);
  card.append(foot);
  return card;
}

function maxGen() { return S.nodes.reduce((m, n) => Math.max(m, n.gen || 0), 0); }

function zoomCluster() {
  const z = h('div', 'zoom-cluster');
  const minus = btn('−', 'sm', () => setZoom(S.zoom - 0.1));
  const plus = btn('+', 'sm', () => setZoom(S.zoom + 0.1));
  minus.setAttribute('aria-label', 'Thu nhỏ sơ đồ');
  plus.setAttribute('aria-label', 'Phóng to sơ đồ');
  const lbl = h('span', 'zoom-label', `${Math.round(S.zoom * 100)}%`);
  const wide = btn('⛶ Mở rộng', 'sm', openExpanded);
  // Đã chốt qua prototype: "Mở rộng" = canvas toàn màn hình (overlay), không phải modal
  z.append(minus, lbl, plus, wide);
  return z;
}
function setZoom(z) {
  S.zoom = Math.min(1.6, Math.max(0.5, Math.round(z * 10) / 10));
  P.rerenderModule();
}

/* ------------------------------ Pool -------------------------------- */
function poolPane() {
  const pane = h('div', 'rel-pool');
  const head = h('div', 'card-head');
  head.style.padding = '6px 4px 2px';
  head.append(h('h3', 'card-title', `Pool (${poolPeople().length})`));
  pane.append(head);
  const search = h('input', 'input pool-search');
  search.type = 'search'; search.placeholder = 'Lọc pool…';
  search.value = S.poolQuery;
  search.setAttribute('aria-label', 'Lọc pool theo tên');
  search.addEventListener('input', () => { S.poolQuery = search.value; renderPoolList(box); });
  pane.append(search);
  const box = h('div', 'pool-box');
  box.dataset.scrollkey = 'pool';
  // thả thẻ người vào Pool = bỏ gán (draft Diagram)
  box.addEventListener('dragover', (e) => {
    if (e.dataTransfer.types.includes(DT)) { e.preventDefault(); box.classList.add('drop-hint'); }
  });
  box.addEventListener('dragleave', () => box.classList.remove('drop-hint'));
  box.addEventListener('drop', (e) => {
    e.preventDefault(); box.classList.remove('drop-hint');
    const d = getDragPayload(e);
    if (d && d.personId && (d.from || assignedIds().has(d.personId))) {
      movePerson(d.personId, null);
    }
  });
  pane.append(box);
  requestAnimationFrame(() => renderPoolList(box));
  return pane;

  function renderPoolList(boxEl) {
    boxEl.innerHTML = '';
    const q = S.poolQuery.trim().toLowerCase();
    const list = poolPeople().filter(p =>
      !q || (p.ho_ten || '').toLowerCase().includes(q) || (p.so_giay_to || '').includes(q));
    if (!committedPeople().length) {
      boxEl.append(h('div', 'face', 'Stage chưa có người đã xác nhận — Cập nhật Stage trước.'));
      return;
    }
    if (!list.length) {
      boxEl.append(h('div', 'face',
        q ? 'Không khớp bộ lọc — chỉ lọc hiển thị.' : 'Pool trống — mọi người đã được gán.'));
      return;
    }
    for (const p of list) boxEl.append(poolCard(p));
  }

  function poolCard(p) {
    const c = h('div', 'pool-card');
    c.draggable = !ro();
    c.append(dragHandle(`kéo ${p.ho_ten || 'người'} lên sơ đồ`, (e) => setDragPayload(e, p.id, null)));
    c.append(h('span', 'nm', p.ho_ten || '(chưa đặt tên)'));
    const assign = h('button', 'btn sm', '→');
    assign.type = 'button';
    assign.title = 'Gán vị trí (bàn phím — thay cho kéo thả)';
    assign.setAttribute('aria-label', `Gán vị trí cho ${p.ho_ten || 'người này'}`);
    assign.disabled = ro();
    assign.addEventListener('click', () => openAssignMenu(p));
    c.append(assign);
    c.addEventListener('dragstart', (e) => setDragPayload(e, p.id, null));
    c.addEventListener('dragend', () => c.classList.remove('dragging'));
    return c;
  }
}

/* Menu "Gán vị trí" — đường bàn phím thay kéo-thả */
function openAssignMenu(p) {
  P.openModal((box, close) => {
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', `Gán vị trí — ${p.ho_ten || '(chưa tên)'}`), modalClose(close));
    box.append(head);
    const body = h('div', 'modal-body');
    if (S.diagramKind === 'hai-ben') {
      const empty = Object.keys(S.slots).filter(k => !S.slots[k]);
      if (!empty.length) body.append(h('p', 'muted', 'Không còn chỗ trống (30/30 đã có người).'));
      const grid = h('div'); grid.style.display = 'flex'; grid.style.flexWrap = 'wrap'; grid.style.gap = '6px';
      for (const k of empty) {
        grid.append(btn(`Chỗ ${k}`, 'secondary sm', () => {
          movePerson(p.id, { slot: Number(k) }); close();
        }));
      }
      body.append(grid);
    } else {
      const empty = S.nodes.filter(n => !n.personId);
      if (empty.length) {
        body.append(h('p', 'muted', 'Slot đang trống:'));
        for (const n of empty) {
          body.append(btn(`Gán vào slot ${n.id}`, 'secondary sm', () => {
            movePerson(p.id, { node: n.id }); close();
          }));
        }
      }
      const filled = S.nodes.filter(n => n.personId);
      if (filled.length) {
        body.append(h('p', 'muted', 'Hoặc tạo slot mới quan hệ với:'));
        for (const n of filled) {
          const who = (personById(n.personId) || {}).ho_ten || n.id;
          body.append(btn(`Con của ${who}`, 'sm', () => {
            const node = { id: D.uid('n'), gen: (n.gen || 0) + 1, order: 999,
                           personId: p.id, parents: [n.id], spouse: null, chu: [], nhan: [] };
            S.nodes.push(node); S.diagramDirty = true; P.rerenderModule(); close();
          }));
          body.append(' ');
          body.append(btn(`Vợ/chồng của ${who}`, 'sm', () => {
            const node = { id: D.uid('n'), gen: n.gen || 0, order: (n.order || 0) + 0.5,
                           personId: p.id, parents: [], spouse: n.id, chu: [], nhan: [] };
            S.nodes.push(node); S.diagramDirty = true; P.rerenderModule(); close();
          }));
        }
      }
      if (!S.nodes.length) {
        body.append(btn('Tạo slot đầu tiên và gán', 'secondary', () => {
          S.nodes.push({ id: D.uid('n'), gen: 0, order: 0, personId: p.id,
                         parents: [], spouse: null, chu: [], nhan: [] });
          S.diagramDirty = true; P.rerenderModule(); close();
        }));
      }
    }
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Đóng', '', close));
    box.append(foot);
  });
}

/* --------------------------- canvas thừa kế -------------------------- */
const NODE_W = 208, NODE_H = 150, GAP_X = 40, ROW_H = 200, PAD = 28;

function layoutNodes() {
  // xếp theo thế hệ; trong thế hệ theo order; vợ/chồng được order liền nhau
  const byGen = {};
  for (const n of S.nodes) (byGen[n.gen || 0] = byGen[n.gen || 0] || []).push(n);
  const pos = {};
  let maxX = 0, maxY = 0;
  for (const g of Object.keys(byGen)) {
    const arr = byGen[g].sort((a, b) => (a.order - b.order));
    arr.forEach((n, i) => {
      pos[n.id] = { x: PAD + i * (NODE_W + GAP_X), y: PAD + Number(g) * ROW_H };
      maxX = Math.max(maxX, pos[n.id].x + NODE_W);
      maxY = Math.max(maxY, pos[n.id].y + NODE_H);
    });
  }
  return { pos, w: maxX + PAD, h: maxY + PAD };
}

function diagramCanvas() {
  const wrap = h('div', 'canvas-wrap');
  wrap.dataset.scrollkey = 'canvas';
  if (S.diagramKind === 'hai-ben') return sidesCanvas(wrap);

  if (!S.nodes.length) {
    wrap.append(P.faceEmpty('Sơ đồ chưa có slot',
      'Kéo thẻ từ Pool vào đây, hoặc dùng + Slot / Gán vị trí…',
      '+ Slot', () => {
        S.nodes.push({ id: D.uid('n'), gen: 0, order: 0, personId: null,
                       parents: [], spouse: null, chu: [], nhan: [] });
        S.diagramDirty = true; P.rerenderModule();
      }));
    return wrap;
  }

  const { pos, w, hgt } = (() => { const l = layoutNodes(); return { pos: l.pos, w: l.w, hgt: l.h }; })();
  const world = h('div', 'canvas-world');
  world.style.width = `${w * S.zoom}px`;
  world.style.height = `${hgt * S.zoom}px`;
  const scale = h('div', 'canvas-scale');
  scale.style.transform = `scale(${S.zoom})`;
  scale.style.width = `${w}px`; scale.style.height = `${hgt}px`;

  scale.append(edgesSvg(pos));
  for (const n of S.nodes) scale.append(nodeEl(n, pos[n.id]));
  world.append(scale);
  wrap.append(world);

  // kéo nền để pan (scroll)
  let panStart = null;
  wrap.addEventListener('mousedown', (e) => {
    if (e.target !== wrap && e.target !== world) return;
    panStart = { x: e.clientX, y: e.clientY, t: wrap.scrollTop, l: wrap.scrollLeft };
    wrap.classList.add('panning');
  });
  wrap.addEventListener('mousemove', (e) => {
    if (!panStart) return;
    wrap.scrollLeft = panStart.l - (e.clientX - panStart.x);
    wrap.scrollTop = panStart.t - (e.clientY - panStart.y);
  });
  ['mouseup', 'mouseleave'].forEach(ev => wrap.addEventListener(ev, () => {
    panStart = null; wrap.classList.remove('panning');
  }));

  if (S.calcOpen) wrap.append(calcPanel());
  return wrap;
}

function edgesSvg(pos) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('class', 'canvas-edges');
  const l = layoutNodes();
  svg.setAttribute('width', l.w); svg.setAttribute('height', l.h);
  const defs = document.createElementNS(ns, 'defs');
  const mk = document.createElementNS(ns, 'marker');
  mk.setAttribute('id', 'arr'); mk.setAttribute('viewBox', '0 0 10 10');
  mk.setAttribute('refX', '9'); mk.setAttribute('refY', '5');
  mk.setAttribute('markerWidth', '7'); mk.setAttribute('markerHeight', '7');
  mk.setAttribute('orient', 'auto-start-reverse');
  const tip = document.createElementNS(ns, 'path');
  tip.setAttribute('d', 'M0 0L10 5L0 10z');
  mk.append(tip); defs.append(mk); svg.append(defs);
  const path = (d, cls) => {
    const p = document.createElementNS(ns, 'path');
    p.setAttribute('d', d);
    if (cls) p.setAttribute('class', cls);
    p.setAttribute('marker-end', 'url(#arr)');
    svg.append(p);
  };
  const done = new Set();
  for (const n of S.nodes) {
    const c = pos[n.id];
    if (n.spouse && !done.has(n.id) && pos[n.spouse]) {
      const s = pos[n.spouse];
      const y = Math.min(c.y, s.y) + 34;
      const x1 = Math.min(c.x, s.x) + NODE_W;
      const x2 = Math.max(c.x, s.x);
      path(`M${x1} ${y} H${x2}`, 'spouse');
      done.add(n.spouse);
    }
    for (const pid of n.parents || []) {
      if (!pos[pid]) continue;
      const pp = pos[pid];
      const x1 = pp.x + NODE_W / 2, y1 = pp.y + NODE_H - 8;
      const x2 = c.x + NODE_W / 2, y2 = c.y;
      const mid = y1 + (y2 - y1) / 2;
      path(`M${x1} ${y1} V${mid} H${x2} V${y2 - 6}`);
    }
  }
  return svg;
}

function nodeEl(n, at) {
  const p = n.personId ? personById(n.personId) : null;
  if (!n.personId) {
    const e = h('div', 'node empty');
    e.style.left = `${at.x}px`; e.style.top = `${at.y}px`;
    e.textContent = 'Trống — thả thẻ Pool vào đây';
    wireDrop(e, { node: n.id });
    return e;
  }
  const el = h('div', 'node');
  el.style.left = `${at.x}px`; el.style.top = `${at.y}px`;
  el.draggable = !ro();
  el.addEventListener('dragstart', (e) => setDragPayload(e, n.personId, n.id));
  wireDrop(el, { node: n.id });

  const head = h('div', 'node-head');
  head.append(dragHandle(`kéo ${p ? p.ho_ten : 'node'}`, (e) => setDragPayload(e, n.personId, n.id)));
  head.append(h('span', 'node-name', p ? (p.ho_ten || '(chưa đặt tên)') : '—'));
  const del = h('button', 'icon-x', '×');
  del.type = 'button'; del.title = 'Xóa slot khỏi sơ đồ (draft — không xóa Stage)';
  del.setAttribute('aria-label', `Xóa slot ${p ? p.ho_ten : ''}`);
  del.disabled = ro();
  del.addEventListener('click', () => {
    S.nodes = S.nodes.filter(x => x !== n); S.diagramDirty = true; P.rerenderModule();
  });
  head.append(del);
  el.append(head);

  const meta = [p && p.ngay_sinh ? p.ngay_sinh.slice(-4) : '…', p && p.ngay_mat ? p.ngay_mat.slice(-4) : '…'];
  el.append(h('div', 'node-meta', `${meta[0]} – ${meta[1]}`));

  const nAssets = Math.max(committedAssets().length, 1);
  for (const [key, label] of [['chu', 'Chủ đất'], ['nhan', 'Nhận đất']]) {
    const row = h('div', 'node-flags');
    row.append(h('span', 'lbl', label));
    for (let i = 1; i <= nAssets; i++) {
      const on = (n[key] || []).includes(i);
      const c = h('button', `poschip ${on ? 'on' : ''}`, on ? `✓${i}` : `${i}`);
      c.type = 'button';
      c.title = `${label} — tài sản ${i} (đề xuất: số = cột tài sản)`;
      c.setAttribute('aria-pressed', String(on));
      c.disabled = ro();
      c.addEventListener('click', () => {
        const arr = new Set(n[key] || []);
        if (arr.has(i)) arr.delete(i); else arr.add(i);
        n[key] = [...arr].sort();
        S.diagramDirty = true; P.rerenderModule();
      });
      row.append(c);
    }
    el.append(row);
  }
  return el;
}

function wireDrop(el, target) {
  el.addEventListener('dragover', (e) => {
    if (e.dataTransfer.types.includes(DT)) { e.preventDefault(); el.classList.add('drop-ok'); }
  });
  el.addEventListener('dragleave', () => el.classList.remove('drop-ok'));
  el.addEventListener('drop', (e) => {
    e.preventDefault(); el.classList.remove('drop-ok');
    const d = getDragPayload(e);
    if (d && d.personId) movePerson(d.personId, target);
  });
}

/* panel "Xem cách tính" — đọc output giả, JS không tự tính */
function calcPanel() {
  const box = h('div', 'card');
  box.style.cssText = 'position:absolute;right:12px;top:12px;width:300px;max-height:70%;overflow:auto;z-index:5;';
  const b = h('div', 'card-body');
  b.append(h('div', 'pill info', 'Trạng thái tính: Hoàn chỉnh (dữ liệu giả)'));
  const list = h('div', 'small');
  list.style.marginTop = '8px';
  for (const n of S.nodes.filter(x => x.personId).slice(0, 6)) {
    const p = personById(n.personId);
    const row = h('div', 'ul-row');
    row.style.justifyContent = 'space-between';
    row.append(h('span', '', p ? p.ho_ten : '—'));
    row.append(h('span', 'pill accent', '—'));
    list.append(row);
  }
  b.append(list);
  b.append(h('p', 'muted small',
    'Bản mẫu: panel chỉ minh họa vị trí — số liệu % do engine Python tính ở bản thật, UI không tự tính.'));
  box.append(b);
  return box;
}

/* --------------------- canvas hai bên (30 chỗ) ------------------------ */
// ĐỀ XUẤT chờ P2: bên A = chỗ 1–15, bên B = chỗ 16–30 (gợi ý "vị trí 16"
// là đầu bên B trong checklist MIN-123). Card = tên + số chỗ.
function sidesCanvas(wrap) {
  const world = h('div', 'canvas-world');
  const innerW = 700;
  // 15 chỗ/cột × (56 + margin 8) + tiêu đề + padding — đủ cao để wrap cuộn
  const rows = 15;
  const innerH = 24 + 36 + rows * 64 + 24;
  world.style.width = `${innerW * S.zoom}px`;
  world.style.height = `${innerH * S.zoom}px`;
  world.style.minHeight = '100%';
  const scale = h('div', 'canvas-scale');
  scale.style.transform = `scale(${S.zoom})`;
  scale.style.width = `${innerW}px`;
  scale.style.height = `${innerH}px`;
  const sides = h('div', 'sides');
  sides.style.padding = '16px';
  sides.append(sideCol('Bên A — chuyển', 1, 15), sideCol('Bên B — nhận', 16, 30));
  scale.append(sides);
  world.append(scale);
  wrap.append(world);
  return wrap;
}

function sideCol(title, from, to) {
  const col = h('div', 'side-col');
  const ttl = h('h3', 'side-title', title);
  const filled = Array.from({length: to - from + 1}, (_, i) => S.slots[from + i]).filter(Boolean).length;
  ttl.append(h('span', 'pill accent', `${filled}/${to - from + 1} chỗ`));
  col.append(ttl);
  for (let i = from; i <= to; i++) {
    col.append(slotEl(i));
  }
  return col;
}

function slotEl(pos) {
  const pid = S.slots[pos];
  const p = pid ? personById(pid) : null;
  const s = h('div', `slot ${pid ? 'filled' : ''}`);
  s.append(h('span', 'slot-badge', `Chỗ ${pos}`));
  if (pid) {
    s.append(h('span', 'nm', p ? (p.ho_ten || '(chưa đặt tên)') : '—'));
    s.append(h('span', 'sub', p && p.ngay_sinh ? p.ngay_sinh.slice(-4) : ''));
    const del = h('button', 'icon-x', '×');
    del.type = 'button'; del.title = `Bỏ ${p ? p.ho_ten : ''} khỏi chỗ ${pos} (về Pool)`;
    del.setAttribute('aria-label', `Bỏ khỏi chỗ ${pos}`);
    del.disabled = ro();
    del.addEventListener('click', () => { S.slots[pos] = null; S.diagramDirty = true; P.rerenderModule(); });
    s.append(del);
    s.draggable = !ro();
    s.addEventListener('dragstart', (e) => setDragPayload(e, pid, `slot:${pos}`));
  } else {
    s.append(h('span', 'muted', 'Trống — thả thẻ Pool vào đây'));
  }
  wireDrop(s, { slot: pos });
  return s;
}

/* ---------------------- Mở rộng (fullscreen) ------------------------- */
// Đã chốt qua prototype: canvas phủ toàn khung app, Esc/nút Đóng để thoát.
// (Không đi qua P.openModal vì overlay này là "xem lớn", không phải dialog
// quyết định — nhưng vẫn giữ: Esc đóng + trả focus về nút Mở rộng.)
function openExpanded() {
  const opener = document.activeElement;
  const overlay = h('div', 'modal-overlay');
  overlay.style.background = 'rgba(15,23,42,.55)';
  const box = h('div', 'modal wide');
  box.style.maxWidth = 'none'; box.style.width = '96vw'; box.style.height = '92vh';
  const close = () => {
    overlay.remove();
    if (opener && opener.isConnected) opener.focus();
  };
  const head = h('div', 'modal-head');
  head.append(h('h2', 'modal-title',
    S.diagramKind === 'hai-ben' ? 'Sơ đồ hai bên — toàn màn' : 'Sơ đồ thừa kế — toàn màn'));
  const z = h('div', 'zoom-cluster');
  const lbl = h('span', 'zoom-label', `${Math.round(S.zoom * 100)}%`);
  const applyZoom = (v) => {
    S.zoom = Math.min(1.6, Math.max(0.5, Math.round(v * 10) / 10));
    lbl.textContent = `${Math.round(S.zoom * 100)}%`;
    rebuild();
    P.rerenderModule();          // giữ canvas phía sau đồng bộ zoom
  };
  const minus = btn('−', 'sm', () => applyZoom(S.zoom - 0.1));
  const plus = btn('+', 'sm', () => applyZoom(S.zoom + 0.1));
  minus.setAttribute('aria-label', 'Thu nhỏ sơ đồ');
  plus.setAttribute('aria-label', 'Phóng to sơ đồ');
  z.append(minus, lbl, plus);
  head.append(z);
  head.append(modalClose(close));
  box.append(head);
  const body = h('div', 'modal-body');
  body.style.flex = '1'; body.style.display = 'flex'; body.style.overflow = 'hidden';
  box.append(body);
  function rebuild() {
    body.innerHTML = '';
    const wrap = diagramCanvas();
    wrap.style.flex = '1';
    body.append(wrap);
  }
  rebuild();
  overlay.append(box);
  overlay.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.preventDefault(); close(); } });
  box.tabIndex = -1;
  document.getElementById('modalRoot').append(overlay);
  box.focus();
}

/* -------------------------- dialog Loại đất -------------------------- */
function openLandTypes(asset) {
  const idx = S.assets.indexOf(asset);
  // draft riêng của dialog — Hủy không đụng Stage (đề xuất: Apply mới ghi)
  const draft = clone(asset.parcels);
  P.openModal((box, close) => {
    box.classList.add('wide');
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', `Loại đất · Tài sản ${idx + 1}`));
    head.append(modalClose(close));
    box.append(head);
    const body = h('div', 'modal-body');
    const tools = h('div'); tools.style.display = 'flex'; tools.style.justifyContent = 'flex-end'; tools.style.marginBottom = '8px';
    tools.append(btn('+ Loại đất', 'secondary', () => {
      draft.push({ loai_dat: 'ONT', dien_tich: '', thoi_han: 'Lâu dài' });
      rebuild();
    }));
    body.append(tools);
    const tblWrap = h('div'); tblWrap.style.overflow = 'auto'; tblWrap.style.maxHeight = '52vh';
    body.append(tblWrap);
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Hủy', '', close));
    const apply = btn('Áp dụng', 'primary', () => {
      asset.parcels = clone(draft);
      markStageDirty();          // đề xuất: Apply → draft Stage, chưa commit
      close(); P.rerenderModule();
    });
    foot.append(apply);
    box.append(foot);

    rebuild();
    function rebuild() {
      tblWrap.innerHTML = '';
      if (!draft.length) {
        tblWrap.append(P.faceEmpty('Chưa có loại đất', '', '+ Loại đất', () => {
          draft.push({ loai_dat: 'ONT', dien_tich: '', thoi_han: 'Lâu dài' }); rebuild();
        }));
        return;
      }
      const t = h('table', 'grid transposed');
      const trh = h('tr');
      trh.append(h('th', 'rowlabel', ''));
      draft.forEach((row, ci) => {
        const th = h('th', 'asset-col');
        const w = h('div', 'col-head');
        w.style.justifyContent = 'flex-end';
        const del = h('button', 'icon-x', '×');
        del.type = 'button'; del.setAttribute('aria-label', `Xóa thửa ${ci + 1}`);
        del.addEventListener('click', () => { draft.splice(ci, 1); rebuild(); });
        w.append(del); th.append(w); trh.append(th);
      });
      const thead = h('thead'); thead.append(trh); t.append(thead);
      const tb = h('tbody');
      const rows = [
        ['loai_dat', 'Loại đất', 'select', D.LAND_TYPES],
        ['dien_tich', 'Diện tích (m²)', 'input', null],
        ['thoi_han', 'Thời hạn', 'select', D.LAND_TERMS],
      ];
      for (const [f, label, kind, opts] of rows) {
        const r = h('tr');
        r.append(h('td', 'rowlabel', label));
        draft.forEach((row) => {
          const td = h('td');
          let ctl;
          if (kind === 'select') {
            ctl = h('select', 'input');
            for (const o of opts) { const op = h('option', '', o); op.value = o; ctl.append(op); }
            ctl.value = row[f] || opts[0];
            ctl.addEventListener('change', () => { row[f] = ctl.value; });
          } else {
            ctl = h('input', 'input'); ctl.value = row[f] || '';
            ctl.inputMode = 'numeric';
            ctl.addEventListener('input', () => { row[f] = ctl.value; });
          }
          ctl.style.width = '100%';
          ctl.setAttribute('aria-label', `${label} — thửa ${draft.indexOf(row) + 1}`);
          td.append(ctl); r.append(td);
        });
        tb.append(r);
      }
      t.append(tb);
      tblWrap.append(t);
    }
  }, { wide: true });
}

/* --------------------------- dialog Nhập file ------------------------- */
function openIntake() {
  P.openModal((box, close) => {
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', 'Nhập file — phân tích thành gợi ý'), modalClose(close));
    box.append(head);
    const body = h('div', 'modal-body');
    body.append(h('p', 'muted',
      'Dialog intake hiện hữu (ảnh/PDF/Word/Excel/text) — mẫu chỉ demo luồng suggestion.'));
    const list = h('div');
    [['giay_to_nhan_than_A.jpg', 'image'], ['so_ho_khau_scan.pdf', 'pdf'],
     ['danh_sach_nguoi.xlsx', 'xlsx'], ['doan_van_dan.txt', 'text']].forEach(([f, k]) => {
      const r = h('div', 'tray-row');
      r.append(h('span', 'pill accent', k));
      r.append(h('span', 'grow', f));
      r.append(h('span', 'muted small', 'sẵn sàng'));
      list.append(r);
    });
    body.append(list);
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Đóng', '', close));
    const run = btn('Phân tích (demo)', 'primary', () => {
      run.disabled = true; run.textContent = 'Đang phân tích…';
      setTimeout(() => {
        close();
        S.tray = {
          items: [
            { kind: 'observed',    text: 'Phạm Văn Quân — 04/04/1957 (ảnh CCCD)', ok: true },
            { kind: 'normalized',  text: 'Hồ Thị Bích Vân — chuẩn hóa từ "Ho Thi Bich Van"', ok: true },
            { kind: 'inferred',    text: 'Tài sản: thửa 77, tờ 9 — suy từ sổ đỏ scan', ok: true },
            { kind: 'error',       text: 'danh_sach_nguoi.xlsx — sheet 2 đọc lỗi (partial)', ok: false },
          ],
        };
        P.rerenderModule();
      }, 800);
    });
    foot.append(run);
    box.append(foot);
  });
}

function trayEl() {
  const box = h('div', 'tray');
  box.append(h('div', 'small', ''));
  const title = h('div', 'card-title'); title.style.fontSize = '13px';
  title.textContent = 'Gợi ý từ file vừa nhập (chưa vào Stage)';
  box.append(title);
  for (const it of S.tray.items) {
    const r = h('div', `tray-row ${it.ok ? '' : 'err'}`);
    const tone = { observed: 'info', normalized: 'accent', inferred: 'warn', error: 'err' }[it.kind];
    r.append(h('span', `pill ${tone}`, it.kind));
    r.append(h('span', 'grow', it.text));
    if (it.ok) {
      r.append(btn('Đưa vào Stage', 'secondary sm', () => {
        S.people.push(D.person(it.text.split(' — ')[0]));
        S.tray.items = S.tray.items.filter(x => x !== it);
        markStageDirty(); P.rerenderModule();
      }));
      r.append(btn('Bỏ qua', 'sm', () => {
        S.tray.items = S.tray.items.filter(x => x !== it);
        P.rerenderModule();
      }));
    }
    box.append(r);
  }
  return box;
}

/* ------------------------ conflict / word stub ------------------------ */
P.openConflictDemo = () => {
  P.openModal((box, close) => {
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', 'Hồ sơ đã thay đổi ở phiên khác'), modalClose(close));
    box.append(head);
    const body = h('div', 'modal-body');
    body.append(h('p', '', 'workspace_conflict — bản trên máy chủ mới hơn bản đang sửa. Chọn một:'));
    body.append(h('p', 'muted', 'Không có nút ghi đè cưỡng bức (theo spec đã khóa).'));
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Giữ bản nháp để sao chép', '', () => {
      close(); P.toast('Giữ nháp — dữ liệu trên màn không đổi (demo).');
    }));
    foot.append(btn('Tải bản mới', 'primary', () => {
      close(); P.toast('Tải bản mới — nháp hiện tại bị thay (demo).', 'warn');
    }));
    box.append(foot);
  });
};

function openWordStub() {
  // "Word giữ vị trí vào chức năng hiện có, không thiết kế popup mới" (MIN-126)
  P.openModal((box, close) => {
    const head = h('div', 'modal-head');
    head.append(h('h2', 'modal-title', 'Xuất Word'), modalClose(close));
    box.append(head);
    const body = h('div', 'modal-body');
    body.append(h('p', '',
      'Vị trí nút được giữ đúng bố cục; popup chọn văn bản/folder dùng dialog ' +
      'xuất Word hiện hữu — không thiết kế lại trong bản mẫu này (MIN-123 mục 9).'));
    const ex = h('div', 'tray-row');
    ex.append(h('span', 'pill muted', 'ví dụ'));
    ex.append(h('span', 'grow', 'Văn bản thừa kế · Văn bản từ chối · Giấy ủy quyền…'));
    body.append(ex);
    box.append(body);
    const foot = h('div', 'modal-foot');
    foot.append(btn('Đóng', 'primary', close));
    box.append(foot);
  });
};

/* ------------------------- splitter helpers -------------------------- */
function splitterH() {
  const s = h('div', 'splitter-h');
  s.tabIndex = 0; s.setAttribute('role', 'separator');
  s.setAttribute('aria-label', 'Kéo đổi chiều cao Stage / sơ đồ');
  s.title = 'Kéo để đổi chiều cao vùng Stage / sơ đồ';
  let drag = null;
  s.addEventListener('mousedown', (e) => {
    drag = { y: e.clientY }; s.classList.add('active'); e.preventDefault();
  });
  window.addEventListener('mousemove', (e) => {
    if (!drag) return;
    const stage = s.previousElementSibling;
    if (stage && stage.classList.contains('stage')) {
      const cur = stage.getBoundingClientRect().height;
      const nx = Math.min(560, Math.max(160, cur + (e.clientY - drag.y)));
      stage.style.flex = `0 0 ${nx}px`; stage.style.overflow = 'auto';
      drag.y = e.clientY;
    }
  });
  window.addEventListener('mouseup', () => { drag = null; s.classList.remove('active'); });
  s.addEventListener('keydown', (e) => {
    const stage = s.previousElementSibling;
    if (!stage || !stage.classList.contains('stage')) return;
    const cur = stage.getBoundingClientRect().height;
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault();
      const nx = Math.min(560, Math.max(160, cur + (e.key === 'ArrowDown' ? 24 : -24)));
      stage.style.flex = `0 0 ${nx}px`; stage.style.overflow = 'auto';
    }
  });
  return s;
}

function splitterV() {
  const s = h('div', 'splitter-v');
  s.tabIndex = 0; s.setAttribute('role', 'separator');
  s.setAttribute('aria-label', 'Kéo đổi chiều rộng Pool / sơ đồ');
  s.title = 'Kéo để đổi chiều rộng Pool / sơ đồ';
  let drag = null;
  s.addEventListener('mousedown', (e) => {
    drag = { x: e.clientX }; s.classList.add('active'); e.preventDefault();
  });
  window.addEventListener('mousemove', (e) => {
    if (!drag) return;
    const pool = s.previousElementSibling;
    if (pool && pool.classList.contains('rel-pool')) {
      const cur = pool.getBoundingClientRect().width;
      const nx = Math.min(520, Math.max(140, cur + (e.clientX - drag.x)));
      pool.style.flex = `0 0 ${nx}px`; pool.style.maxWidth = 'none';
      drag.x = e.clientX;
    }
  });
  window.addEventListener('mouseup', () => { drag = null; s.classList.remove('active'); });
  s.addEventListener('keydown', (e) => {
    const pool = s.previousElementSibling;
    if (!pool || !pool.classList.contains('rel-pool')) return;
    const cur = pool.getBoundingClientRect().width;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const nx = Math.min(520, Math.max(140, cur + (e.key === 'ArrowRight' ? 24 : -24)));
      pool.style.flex = `0 0 ${nx}px`; pool.style.maxWidth = 'none';
    }
  });
  return s;
}

})();
