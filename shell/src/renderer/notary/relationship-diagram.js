'use strict';

/* Relationship diagram + Pool pane (MIN-112) — tier quan he trong
 * workspace Soạn hồ sơ.
 *
 * SOT hanh vi: spec UX §4 + contracts/notary-case-drafting.md §7.
 * - Pool = Stage DA COMMIT tru nguoi da gan tren draft Diagram (model
 *   tinh, khong phai view). Search chi loc hien thi — khong doi draft.
 * - Diagram render draft state (nodes) + ket qua engine render_model
 *   (allocations/warnings/breakdown) — JS KHONG tinh ty le/phan tram.
 * - Keo tha VA menu "Gán vị trí" (ban phim) cung tao draft assignment —
 *   khong ghi cho den "Lưu sơ đồ" (base_revision).
 * - Moi thay doi draft schedule evaluateDiagram debounce ~500ms (preview
 *   engine); "Đánh giá thử" chay ngay; "Xem cách tính" render breakdown
 *   engine verbatim.
 * - Xoa node chi la draft Diagram — khong xoa dong Stage.
 *
 * Export UMD: window.G1_NOTARY_DIAGRAM + module.exports. DOM chi trong
 * buildRelationTier (file load duoc trong node --test de static test).
 */

const REL_EVALUATE_DEBOUNCE_MS = 500;   // spec: 400–600ms sau draft doi

function createDiagramPane(ctx) {
  const model = ctx.model;
  const L = ctx.lib;
  const notify = ctx.notify || (() => {});
  const h = ctx.h;
  const btn = ctx.btn;
  const face = ctx.face;
  const openModal = ctx.openModal;
  const openWordDialog = ctx.openWordDialog || (() => {});
  const rerender = ctx.rerender || (() => {});

  let evalTimer = null;
  let calcOpen = false;
  let poolQuery = '';

  // Debounce evaluate sau moi draft-mutating action (§7.4: evaluate la
  // read-only — chay duoc ca khi locked; unsupported thi bo qua).
  function scheduleEvaluate() {
    if (!model.state.capabilities.diagram || model.state.unsupported) {
      return;
    }
    if (evalTimer) clearTimeout(evalTimer);
    evalTimer = setTimeout(async () => {
      evalTimer = null;
      const r = await model.evaluateDiagram();
      if (!r.ok && r.error &&
          r.error.code !== 'diagram_invalid_state') {
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    }, REL_EVALUATE_DEBOUNCE_MS);
  }

  function personName(rowId) {
    const p = model.state.committed.people
      .find((x) => x.row_id === rowId);
    return p ? (p.ho_ten || '(không tên)') : '—';
  }

  // ---------- Pool ----------

  function poolCardEl(row, kind) {
    const card = h('div', 'cd-pool-card');
    card.draggable = model.canWrite();
    const label = kind === 'person'
      ? (row.ho_ten || '(chưa đặt tên)')
      : (row.so_serial || '(chưa có serial)');
    card.append(h('span', 'cd-pool-label', label));
    card.append(h('span', 'cd-badge', kind === 'person' ? 'Người' : 'Tài sản'));
    // Keo tha (tien ich) — cung ket qua voi menu "Gán vị trí".
    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain',
        JSON.stringify({ kind, row_id: row.row_id }));
    });
    const assign = btn('Gán vị trí…', '', () =>
      openAssignMenu(row, kind));
    assign.disabled = !model.canWrite() || !model.state.capabilities.diagram;
    card.append(assign);
    return card;
  }

  function poolMatch(row, kind, q) {
    if (!q) return true;
    const label = (kind === 'person'
      ? [row.ho_ten, row.so_giay_to, row.ngay_sinh]
      : [row.so_serial, row.dia_chi, row.so_thua_dat])
      .filter(Boolean).join(' ').toLowerCase();
    return label.includes(q);
  }

  // ---------- Menu "Gán vị trí" (ban phim thay cho keo-tha) ----------

  function openAssignMenu(row, kind) {
    const s = model.state;
    openModal((box, close) => {
      box.append(h('div', 'cd-modal-title', 'Gán vị trí trên sơ đồ'));
      if (kind === 'asset') {
        // Wire v1: tai san khong gan vao node — chi xem (§7.1).
        box.append(h('div', 'muted',
          'Tài sản chưa gán trực tiếp lên sơ đồ trong phiên bản này — ' +
          'sơ đồ gán quan hệ giữa các người.'));
        box.append(btn('Đóng', 'primary', close));
        return;
      }
      const nodes = (s.diagram.nodes || []).filter((n) => !n.deleted);
      const empty = nodes.filter((n) => !n.personId);
      if (empty.length) {
        box.append(h('div', 'muted', 'Slot đang trống:'));
        for (const n of empty) {
          box.append(btn(`Gán vào “${n.id}”`, 'cd-menu-item', () => {
            if (model.assignPerson(n.id, row.row_id)) scheduleEvaluate();
            close();
          }));
        }
      }
      box.append(h('div', 'muted', 'Hoặc tạo slot mới:'));
      for (const n of nodes.filter((x) => x.personId)) {
        const who = personName(n.personId);
        box.append(
          btn(`Con của ${who}`, 'cd-menu-item', () => {
            const node = model.addSlot();
            if (node) {
              model.setNodeRelation(node.id, { parentSlotIds: [n.id] });
              model.assignPerson(node.id, row.row_id);
              scheduleEvaluate();
            }
            close();
          }),
          btn(`Vợ/chồng của ${who}`, 'cd-menu-item', () => {
            const node = model.addSlot();
            if (node) {
              model.setNodeRelation(node.id, { spouseSlotId: n.id });
              model.assignPerson(node.id, row.row_id);
              scheduleEvaluate();
            }
            close();
          }));
      }
      if (!nodes.length) {
        box.append(btn('Tạo slot đầu tiên và gán', 'cd-menu-item', () => {
          const node = model.addSlot('owner');
          if (node) {
            model.assignPerson(node.id, row.row_id);
            scheduleEvaluate();
          }
          close();
        }));
      }
      box.append(btn('Đóng', '', close));
    });
  }

  // ---------- Diagram ----------

  // Mui ten SVG nho cho strip quan he — plain SVG, khong framework.
  function arrowSvg(cls) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 44 12');
    svg.setAttribute('class', `cd-edge-svg ${cls || ''}`.trim());
    svg.setAttribute('aria-hidden', 'true');
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', '2'); line.setAttribute('y1', '6');
    line.setAttribute('x2', '34'); line.setAttribute('y2', '6');
    const tip = document.createElementNS(ns, 'path');
    tip.setAttribute('d', 'M34 2 L42 6 L34 10 Z');
    svg.append(line, tip);
    return svg;
  }

  // Allocation badge: chi DOC render_model cua engine — displayPercent la
  // chuoi engine da tinh, JS khong tu tinh phan tram (contract §10).
  function allocBadgeEl(personId) {
    const rm = model.state.renderModel;
    const a = rm && rm.allocations && rm.allocations[personId];
    if (!a) return null;
    const b = h('span', 'cd-badge cd-badge-alloc',
      `${a.displayPercent ?? '—'}%`);
    b.title = `phần cuối ${a.finalShare ?? '—'} (engine)`;
    return b;
  }

  function diagramNodeEl(n) {
    const card = h('div', 'cd-node');
    if (n.deleted) card.classList.add('cd-node-deleted');
    const head = h('div', 'cd-node-head');
    head.append(h('span', 'cd-node-id muted', n.id));
    head.append(h('span', 'cd-node-name',
      n.personId ? personName(n.personId) : '(trống)'));
    if (n.personId) {
      const alloc = allocBadgeEl(n.personId);
      if (alloc) head.append(alloc);
    }
    card.append(head);
    // Quan he draft render bang chu (slot id → nhan doc duoc).
    const rel = [];
    for (const pid of n.parentSlotIds || []) {
      rel.push(`con của ${pid}`);
    }
    if (n.spouseSlotId) rel.push(`vợ/chồng của ${n.spouseSlotId}`);
    if (rel.length) card.append(h('div', 'muted cd-node-rel', rel.join(' · ')));
    // Drop target: nhan pool card keo vao (cung ket qua menu Gan vi tri)
    card.addEventListener('dragover', (e) => e.preventDefault());
    card.addEventListener('drop', (e) => {
      e.preventDefault();
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person' &&
            model.assignPerson(n.id, d.row_id)) scheduleEvaluate();
      } catch (err) { /* payload rac — bo qua */ }
    });
    if (n.deleted) return card;
    const flags = h('div', 'cd-node-flags');
    const ro = !model.canWrite();
    const land = btn(n.isLandOwner ? '★ Chủ đất' : 'Chủ đất',
      n.isLandOwner ? 'primary' : '', () => {
        if (model.setNodeFlag(n.id, 'isLandOwner', !n.isLandOwner)) {
          scheduleEvaluate();
        }
      });
    land.disabled = ro;
    land.setAttribute('aria-pressed', String(!!n.isLandOwner));
    const recv = btn(n.willReceive ? '✓ Nhận' : 'Nhận',
      n.willReceive ? 'primary' : '', () => {
        if (model.setNodeFlag(n.id, 'willReceive', !n.willReceive)) {
          scheduleEvaluate();
        }
      });
    recv.disabled = ro;
    recv.setAttribute('aria-pressed', String(!!n.willReceive));
    flags.append(land, recv);
    if (n.personId) {
      const un = btn('Bỏ gán', '', () => {
        if (model.assignPerson(n.id, null)) scheduleEvaluate();
      });
      un.disabled = ro;
      flags.append(un);
    }
    const del = btn('✕', 'cd-del', () => {
      // Xoa slot = draft Diagram — dong Stage giu nguyen (§7.1).
      if (model.removeNode(n.id)) scheduleEvaluate();
    });
    del.disabled = ro;
    del.setAttribute('aria-label', `Xóa slot ${n.id}`);
    flags.append(del);
    card.append(flags);
    return card;
  }

  // Strip quan he: danh sach edge (con cua / vo-chong) bang SVG arrow —
  // doc tu draft state, khong suy luan nghiep vu.
  function edgesEl(nodes) {
    const box = h('div', 'cd-edges');
    // Nhan edge: ten nguoi khi slot da gan, fallback slot id.
    const label = (nid) => {
      const nn = nodes.find((x) => x.id === nid);
      return nn && nn.personId ? personName(nn.personId) : nid;
    };
    for (const n of nodes) {
      for (const pid of n.parentSlotIds || []) {
        const row = h('div', 'cd-edge-row');
        row.append(arrowSvg('cd-edge-parent'));
        row.append(h('span', '',
          `${label(n.id)} — con của ${label(pid)}`));
        box.append(row);
      }
      if (n.spouseSlotId) {
        const row = h('div', 'cd-edge-row');
        row.append(arrowSvg('cd-edge-spouse'));
        row.append(h('span', '',
          `${label(n.id)} — vợ/chồng của ${label(n.spouseSlotId)}`));
        box.append(row);
      }
    }
    return box;
  }

  // "Xem cách tính" — chi DOC output engine, render dang doc duoc,
  // khong render JSON tho, khong tu tinh ty le (contract §10 consumer).
  function calcPanelEl() {
    const rm = model.state.renderModel;
    const box = h('div', 'cd-calc');
    if (!rm) {
      box.append(face(L.faceEmpty(
        'Chưa có kết quả tính — bấm “Đánh giá thử” hoặc lưu sơ đồ.')));
      return box;
    }
    const statusLabel = {
      complete: 'Hoàn chỉnh', incomplete: 'Chưa đủ điều kiện',
      invalid: 'Không hợp lệ', unsupported: 'Chưa hỗ trợ',
    }[rm.status] || rm.status;
    box.append(h('div', 'cd-calc-status',
      `Trạng thái tính: ${statusLabel}`));
    if (rm.status === 'unsupported') {
      box.append(h('div', 'cd-badge cd-badge-warn',
        'Chưa hỗ trợ — đây không phải kết quả đã tính'));
    }
    const allocs = rm.allocations || {};
    const ids = Object.keys(allocs);
    if (ids.length) {
      const list = h('div', 'cd-alloc-list');
      for (const pid of ids) {
        const a = allocs[pid];
        const row = h('div', 'cd-alloc-row');
        row.append(h('span', 'cd-alloc-name', personName(pid)));
        row.append(h('span', 'cd-badge',
          `${a.displayPercent || '0.00'}%`));
        row.append(h('span', 'muted',
          `phần cuối ${a.finalShare ?? '—'}`));
        list.append(row);
      }
      box.append(list);
    }
    // Breakdown engine verbatim (explanation) — render dung text engine
    // gui, khong format lai so.
    for (const ex of rm.explanations || rm.explanation || []) {
      const t = typeof ex === 'string' ? ex : (ex && (ex.message || ex.text));
      if (t) box.append(h('div', 'cd-explain muted', t));
    }
    for (const w of rm.warnings || []) {
      box.append(h('div', 'muted warn-text', w.message || w.code));
    }
    for (const e of rm.errors || []) {
      box.append(h('div', 'error', e.message || e.code));
    }
    for (const u of rm.unresolvedEstates || []) {
      box.append(h('div', 'muted',
        `Phần chưa phân (${personName(u.sourcePersonId)}): ` +
        `${u.fraction} — ${u.reason === 'no_valid_heir'
          ? 'không có người thừa kế hợp lệ' : u.reason}`));
    }
    return box;
  }

  // ---------- tier ----------

  function build() {
    const s = model.state;
    const tier = h('div', 'cd-rel');

    // Pool (~22%) — committed Stage tru nguoi da gan (model.pool()).
    const pc = h('div', 'cd-card cd-pool');
    const pHead = h('div', 'cd-card-head');
    pHead.append(h('h3', 'cd-card-title', 'Pool'));
    pc.append(pHead);
    const search = h('input', 'cd-input cd-pool-search');
    search.type = 'search';
    search.placeholder = 'Lọc pool…';
    search.value = poolQuery;
    search.setAttribute('aria-label', 'Lọc pool theo tên/serial');
    search.oninput = () => {
      poolQuery = search.value.trim().toLowerCase();
      renderPool();
    };
    pc.append(search);
    const pBody = h('div', 'cd-card-body');
    pc.append(pBody);
    function renderPool() {
      pBody.innerHTML = '';
      const pool = model.pool();
      const pp = pool.people.filter((r) => poolMatch(r, 'person', poolQuery));
      const pa = pool.assets.filter((r) => poolMatch(r, 'asset', poolQuery));
      if (!pool.people.length && !pool.assets.length) {
        pBody.append(face(L.faceEmpty(
          'Pool trống — mọi người đã được gán hoặc Stage chưa có dữ liệu.')));
      } else if (!pp.length && !pa.length) {
        pBody.append(face(L.faceEmpty(
          'Không khớp bộ lọc — chỉ lọc hiển thị, draft không đổi.')));
      } else {
        for (const p of pp) pBody.append(poolCardEl(p, 'person'));
        for (const a of pa) pBody.append(poolCardEl(a, 'asset'));
      }
    }
    renderPool();
    tier.append(pc);

    // Diagram (~78%)
    const dc = h('div', 'cd-card cd-diagram');
    const dHead = h('div', 'cd-card-head');
    dHead.append(h('h3', 'cd-card-title', 'Sơ đồ quan hệ'));
    const tools = h('div', 'cd-toolbar cd-card-tools');
    const save = btn('Lưu sơ đồ', 'primary', async () => {
      const r = await model.saveDiagram();
      if (!r.ok && r.error && r.error.code !== 'workspace_conflict' &&
          r.error.code !== 'diagram_invalid_state') {
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    });
    if (s.diagramDirty) save.append(h('span', 'cd-dirty-dot', ''));
    save.disabled = !model.canWrite() || !s.diagramDirty ||
      !s.capabilities.diagram;
    const calc = btn('Xem cách tính', '', async () => {
      calcOpen = !calcOpen;
      if (calcOpen) await model.evaluateDiagram();
      rerender();
    });
    const evalBtn = btn('Đánh giá thử', '', async () => {
      const r = await model.evaluateDiagram();
      if (!r.ok && r.error) notify(
        `${r.error.code}: ${r.error.message}`, true);
      calcOpen = true;
    });
    evalBtn.disabled = !s.capabilities.diagram ||
      s.busy === 'notary.diagram_evaluate';
    const word = btn('Xuất Word', '', openWordDialog);
    word.disabled = !s.capabilities.word_export || s.wordBusy;
    const addSlotBtn = btn('+ Slot', '', () => {
      if (model.addSlot()) scheduleEvaluate();
    });
    addSlotBtn.disabled = !model.canWrite() || !s.capabilities.diagram;
    tools.append(save, calc, evalBtn, word, addSlotBtn);
    dHead.append(tools);
    dc.append(dHead);
    const dBody = h('div', 'cd-diagram-body');
    const nodes = (s.diagram.nodes || []).filter((n) => !n.deleted);
    if (!nodes.length) {
      dBody.append(face(L.faceEmpty(
        'Sơ đồ chưa có slot — thêm slot hoặc gán người từ Pool.')));
    } else {
      const e = edgesEl(nodes);
      if (e.childElementCount) dBody.append(e);
      const grid = h('div', 'cd-nodes');
      for (const n of s.diagram.nodes || []) {
        grid.append(diagramNodeEl(n));
      }
      dBody.append(grid);
    }
    for (const w of s.diagramWarnings || []) {
      dBody.append(h('div', 'muted warn-text', w.message || w.code));
    }
    for (const er of s.diagramErrors || []) {
      dBody.append(h('div', 'error', er.message || er.code));
    }
    if (calcOpen) dBody.append(calcPanelEl());
    dc.append(dBody);
    tier.append(dc);
    return tier;
  }

  return { build };
}

const G1_NOTARY_DIAGRAM = { createDiagramPane };

if (typeof window !== 'undefined') window.G1_NOTARY_DIAGRAM = G1_NOTARY_DIAGRAM;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_DIAGRAM;
}
