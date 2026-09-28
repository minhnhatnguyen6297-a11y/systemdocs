'use strict';

/* Relationship diagram + Pool pane (MIN-112) — tier quan he trong
 * workspace Soạn hồ sơ.
 *
 * SOT hanh vi: spec UX §4 + contracts/notary-case-drafting.md §7 + §13.
 * - Pool = Stage DA COMMIT tru nguoi da gan tren draft Diagram — ke ca
 *   nhap moi (caseId=null): draft Stage dang so KHONG lo vao Pool
 *   (MIN-129). Search chi loc hien thi — khong doi draft.
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
const TWO_PARTY = 'two_party';

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

  // Stage dirty (case da ton tai): evaluate/save diagram phai doi —
  // draft Stage chua cap nhat nen ket qua tinh se mo ta du lieu cu.
  // Nguoi dung Cap nhat hoac Huy Stage truoc (MIN-129 dirty-safety).
  function stageGate() {
    return model.state.caseId != null && model.state.stageDirty;
  }

  // Debounce evaluate sau moi draft-mutating action (§7.4: evaluate la
  // read-only — chay duoc ca khi locked; unsupported thi bo qua).
  function scheduleEvaluate() {
    if (!model.state.capabilities.diagram || model.state.unsupported ||
        stageGate()) {
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
    // Draft (caseId=null): nguon la stage nhap; case that: committed.
    const src = model.state.caseId == null
      ? model.state.stage.people : model.state.committed.people;
    const p = src.find((x) => x.row_id === rowId);
    return p ? (p.ho_ten || '(không tên)') : '—';
  }

  // ---------- Pool ----------
  // Contract keo-tha GIU NGUYEN cho P7: dragstart set 'text/plain' =
  // JSON.stringify({kind:'person', row_id}); drop len node =
  // movePerson(row_id, nodeId), drop vao Pool = movePerson(row_id, null).
  // DOM P7 dung: .cd-pool, .cd-pool-box, .cd-pool-card, .cd-pool-nm,
  // .dragging, .drop-hint.

  function poolCardEl(row, kind, sub) {
    const card = h('div', 'cd-pool-card');
    // Tai san khong gan len node (chi tham chieu qua vi tri 1..3 tren
    // node inheritance) — chi person card keo duoc.
    const canDrag = kind === 'person' && model.canWrite();
    card.draggable = canDrag;
    const label = kind === 'person'
      ? (row.ho_ten || '(chưa đặt tên)')
      : (row.so_serial || '(chưa có serial)');
    const setPayload = (e) => {
      e.dataTransfer.setData('text/plain',
        JSON.stringify({ kind, row_id: row.row_id }));
      card.classList.add('dragging');
    };
    if (canDrag) {
      const grip = h('button', 'drag-handle', '⋮⋮');
      grip.type = 'button';
      grip.draggable = true;
      grip.title = `kéo ${label} lên sơ đồ`;
      grip.setAttribute('aria-label', `kéo ${label} lên sơ đồ`);
      grip.addEventListener('dragstart', setPayload);
      card.append(grip);
    }
    const nm = h('span', 'cd-pool-nm', label);
    if (sub) nm.append(h('span', 'cd-pool-sub', sub));
    card.append(nm);
    // Duong ban phim thay keo-tha (a11y) — menu chon vi tri gan.
    const assign = btn('→', 'sm', () => openAssignMenu(row, kind));
    assign.title = 'Gán vị trí (bàn phím — thay cho kéo thả)';
    assign.setAttribute('aria-label', `Gán vị trí cho ${label}`);
    assign.disabled = !model.canWrite() ||
      !model.state.capabilities.diagram;
    card.append(assign);
    card.addEventListener('dragstart', setPayload);
    card.addEventListener('dragend', () =>
      card.classList.remove('dragging'));
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
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title',
        `Gán vị trí — ${row.ho_ten || row.so_serial || '(chưa tên)'}`));
      const x = h('button', 'modal-close', '×');
      x.type = 'button';
      x.setAttribute('aria-label', 'Đóng');
      x.onclick = close;
      head.append(x);
      box.append(head);
      const body = h('div', 'modal-body cd-field-stack');
      if (kind === 'asset') {
        // Tai san khong gan vao node — so do chi ghi dau chon vi tri
        // own/receive tren node nguoi (§13.4); khong co node tai san.
        body.append(h('div', 'muted',
          'Tài sản chưa gán trực tiếp lên sơ đồ trong phiên bản này — ' +
          'sơ đồ gán quan hệ giữa các người.'));
      } else {
        const nodes = (s.diagram.nodes || []).filter((n) => !n.deleted);
        const tp = model.diagramDomain &&
          model.diagramDomain() === TWO_PARTY;
        const empty = nodes.filter((n) => !n.personId);
        if (empty.length) {
          body.append(h('div', 'muted', 'Slot đang trống:'));
          const grid = h('div', 'cd-tight');
          for (const n of empty) {
            const lbl = n.id === 'owner' ? `${n.id} (người để lại)` : n.id;
            grid.append(btn(`Gán vào “${lbl}”`, 'secondary sm', () => {
              if (model.assignPerson(n.id, row.row_id)) scheduleEvaluate();
              close();
            }));
          }
          body.append(grid);
        }
        // two_party: slot canonical co dinh — khong tao slot quan he moi.
        if (!tp) {
          const filled = nodes.filter((x) => x.personId);
          if (filled.length) {
            body.append(h('div', 'muted',
              'Hoặc tạo slot mới quan hệ với:'));
            for (const n of filled) {
              const who = personName(n.personId);
              const rowBtns = h('div', 'cd-tight');
              rowBtns.append(
                btn(`Con của ${who}`, 'sm', () => {
                  const node = model.addSlot();
                  if (node) {
                    model.setNodeRelation(node.id,
                      { parentSlotIds: [n.id] });
                    model.assignPerson(node.id, row.row_id);
                    scheduleEvaluate();
                  }
                  close();
                }),
                btn(`Vợ/chồng của ${who}`, 'sm', () => {
                  const node = model.addSlot();
                  if (node) {
                    model.setNodeRelation(node.id, { spouseSlotId: n.id });
                    model.assignPerson(node.id, row.row_id);
                    scheduleEvaluate();
                  }
                  close();
                }));
              body.append(rowBtns);
            }
          }
        }
        if (!nodes.length) {
          body.append(btn('Tạo slot đầu tiên và gán',
            'secondary', () => {
              const node = model.addSlot('owner');
              if (node) {
                model.assignPerson(node.id, row.row_id);
                scheduleEvaluate();
              }
              close();
            }));
        }
        if (!empty.length && tp && nodes.length) {
          body.append(h('div', 'muted',
            'Không còn chỗ trống (30/30 đã có người).'));
        }
      }
      box.append(body);
      const foot = h('div', 'modal-foot');
      foot.append(btn('Đóng', '', close));
      box.append(foot);
    }, { bare: true });
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
      // MIN-119: node da gan keo duoc — payload cung shape pool card;
      // drop len node khac = move/swap, drop vao Pool = bo gan.
      card.draggable = model.canWrite() && !n.deleted;
      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain',
          JSON.stringify({ kind: 'person', row_id: n.personId }));
      });
    }
    card.append(head);
    // Quan he draft render bang chu (slot id → nhan doc duoc).
    const rel = [];
    for (const pid of n.parentSlotIds || []) {
      rel.push(`con của ${pid}`);
    }
    if (n.spouseSlotId) rel.push(`vợ/chồng của ${n.spouseSlotId}`);
    if (rel.length) card.append(h('div', 'muted cd-node-rel', rel.join(' · ')));
    // Drop target: nhan pool card hoac node khac keo vao — movePerson
    // bao trum ca move/swap (MIN-122; node draggable o MIN-119).
    card.addEventListener('dragover', (e) => e.preventDefault());
    card.addEventListener('drop', (e) => {
      e.preventDefault();
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person' &&
            model.movePerson(d.row_id, n.id)) scheduleEvaluate();
      } catch (err) { /* payload rac — bo qua */ }
    });
    if (n.deleted) return card;
    const flags = h('div', 'cd-node-flags');
    const ro = !model.canWrite();
    const tp = model.diagramDomain &&
      model.diagramDomain() === TWO_PARTY;
    if (!tp) {
      // Dau chon tai san doc lap (§13.4): own = vi tri so huu, recv =
      // vi tri duoc nhan; chip vi tri chua co asset bi disable (server
      // van prune tai commit/save neu mang vuot len(assets)).
      const assetCount = model.state.stage.assets.length;
      const posRow = (label, kind, arr) => {
        const wrap = h('div', 'cd-posrow');
        wrap.append(h('span', 'muted cd-posrow-label', label));
        for (const pos of [1, 2, 3]) {
          const on = Array.isArray(arr) && arr.includes(pos);
          const chip = btn(on ? `✓ ${pos}` : `${pos}`,
            `cd-chip ${on ? 'primary' : ''}`.trim(), () => {
              if (model.toggleNodePosition(n.id, kind, pos)) {
                scheduleEvaluate();
              }
            });
          chip.disabled = ro || pos > assetCount;
          chip.setAttribute('aria-pressed', String(on));
          wrap.append(chip);
        }
        return wrap;
      };
      flags.append(
        posRow('Sở hữu', 'own', n.ownPositions),
        posRow('Nhận', 'receive', n.receivePositions));
    }
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
    // Breakdowns engine verbatim (contract §7.2): moi muc =
    // {personId, total, terms[{kind, fraction, sourcePersonId?,
    // viaBranchPersonIds?}]} — ai nhan fraction nao tu ai. JS chi doc
    // field engine emit, KHONG tinh/format lai so.
    const nameOf = (pid) => {
      const n = personName(pid);
      return n === '—' ? String(pid) : n;
    };
    const bds = rm.breakdowns || [];
    if (bds.length) {
      const bl = h('div', 'cd-breakdown-list');
      for (const bd of bds) {
        const item = h('div', 'cd-breakdown');
        item.append(h('div', 'cd-breakdown-head',
          `${nameOf(bd.personId)} — tổng ${bd.total ?? '—'}`));
        for (const t of bd.terms || []) {
          const bits = [`${t.kind ?? 'term'}: ${t.fraction ?? '—'}`];
          if (t.sourcePersonId) {
            bits.push(`từ ${nameOf(t.sourcePersonId)}`);
          }
          if (Array.isArray(t.viaBranchPersonIds) &&
              t.viaBranchPersonIds.length) {
            bits.push(
              `qua ${t.viaBranchPersonIds.map(nameOf).join(', ')}`);
          }
          item.append(h('div', 'cd-explain muted', bits.join(' · ')));
        }
        bl.append(item);
      }
      box.append(bl);
    }
    for (const w of rm.warnings || []) {
      box.append(h('div', 'muted warn-text',
        typeof w === 'string' ? w : (w.message || w.code)));
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

  // ---------- Pool pane (committed-only) + tier ----------

  function poolPaneEl() {
    const s = model.state;
    const pane = h('div', 'cd-pool');
    const head = h('div', 'cd-pool-head');
    const title = h('h3', 'card-title', 'Pool');
    head.append(title);
    const search = h('input', 'cd-pool-search');
    search.type = 'search';
    search.placeholder = 'Lọc pool…';
    search.value = poolQuery;
    search.setAttribute('aria-label', 'Lọc pool theo tên/serial');
    search.oninput = () => {
      poolQuery = search.value.trim().toLowerCase();
      renderPool();
    };
    head.append(search);
    pane.append(head);
    const box = h('div', 'cd-pool-box');
    // Drop target bo gan: keo node co nguoi vao Pool → ve Pool
    // (movePerson(rowId, null)) — payload cung shape {kind:'person',
    // row_id} (P7 contract).
    box.addEventListener('dragover', (e) => {
      e.preventDefault();
      box.classList.add('drop-hint');
    });
    box.addEventListener('dragleave', () => box.classList.remove('drop-hint'));
    box.addEventListener('drop', (e) => {
      e.preventDefault();
      box.classList.remove('drop-hint');
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person' && d.row_id &&
            model.movePerson(d.row_id, null)) scheduleEvaluate();
      } catch (err) { /* bo qua */ }
    });
    pane.append(box);

    function renderPool() {
      box.innerHTML = '';
      const st = model.state;
      // Committed-only KE CA nhap moi (caseId=null): draft Stage dang
      // so khong bao gio lo vao Pool (MIN-129). model.pool() dung stage
      // cho draft nen khong dung — P6 tinh tu state.committed; gap
      // (model nen export committedPool()) ghi vao handoff.
      const assigned = new Set((st.diagram.nodes || [])
        .map((n) => n.personId).filter(Boolean));
      const poolPeople = (st.committed.people || [])
        .filter((p) => !assigned.has(p.row_id));
      const poolAssets = (st.committed.assets || []).slice();
      title.textContent = `Pool (${poolPeople.length})`;
      const pp = poolPeople.filter((r) => poolMatch(r, 'person', poolQuery));
      const pa = poolAssets.filter((r) => poolMatch(r, 'asset', poolQuery));
      if (!(st.committed.people || []).length &&
          !(st.committed.assets || []).length) {
        box.append(face(L.faceEmpty(
          'Stage chưa có người đã xác nhận — Cập nhật Stage trước.')));
        return;
      }
      if (!pp.length && !pa.length) {
        box.append(face(L.faceEmpty(
          poolQuery ? 'Không khớp bộ lọc — chỉ lọc hiển thị.'
                    : 'Pool trống — mọi người đã được gán.')));
        return;
      }
      // Ten trung: dong phu phan biet (sinh/CCCD) theo ban mau — khong
      // lo row_id ky thuat len UI.
      const counts = {};
      for (const p of poolPeople) {
        const k = p.ho_ten || '';
        counts[k] = (counts[k] || 0) + 1;
      }
      for (const p of pp) {
        let sub = null;
        if ((counts[p.ho_ten || ''] || 0) > 1) {
          sub = p.ngay_sinh ? `sinh ${p.ngay_sinh}`
            : (p.so_giay_to ? `GT ${p.so_giay_to}` : '—');
        }
        box.append(poolCardEl(p, 'person', sub));
      }
      for (const a of pa) {
        box.append(poolCardEl(a, 'asset',
          ['Tài sản',
           a.so_thua_dat && `thửa ${a.so_thua_dat}`]
            .filter(Boolean).join(' · ')));
      }
    }
    renderPool();
    return pane;
  }

  // Vung canvas diagram (nodes/edges/calc) — P7 so huu ben trong; P6
  // chi dat khung card + head tools + foot theo ban mau duyet.
  function diagramBodyEl() {
    const s = model.state;
    const tp = model.diagramDomain &&
      model.diagramDomain() === TWO_PARTY;
    const dBody = h('div', 'cd-diagram-body');
    const nodes = (s.diagram.nodes || []).filter((n) => !n.deleted);
    if (!nodes.length) {
      dBody.append(face(L.faceEmpty(
        tp ? 'Sơ đồ hai bên chưa có slot — kiểm tra dữ liệu.'
           : 'Sơ đồ chưa có slot — thêm slot hoặc gán người từ Pool.')));
    } else if (tp) {
      // two_party: 30 slot canonical — p1..p15 ben A, p16..p30 ben B.
      const groups = [
        ['Bên A (p1–p15)', (n) => /^p([1-9]|1[0-5])$/.test(n.id)],
        ['Bên B (p16–p30)', (n) => /^p(1[6-9]|2[0-9]|30)$/.test(n.id)],
      ];
      for (const [label, match] of groups) {
        const groupNodes = (s.diagram.nodes || []).filter(
          (n) => !n.deleted && match(n));
        if (!groupNodes.length) continue;
        dBody.append(h('div', 'cd-group-label muted', label));
        const grid = h('div', 'cd-nodes');
        for (const n of groupNodes) grid.append(diagramNodeEl(n));
        dBody.append(grid);
      }
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
      // Shape hon hop: compose warnings la string, engine warnings la
      // {code,message} — render ca hai.
      dBody.append(h('div', 'muted warn-text',
        typeof w === 'string' ? w : (w.message || w.code)));
    }
    for (const er of s.diagramErrors || []) {
      dBody.append(h('div', 'error', er.message || er.code));
    }
    if (calcOpen) dBody.append(calcPanelEl());
    return dBody;
  }

  function build() {
    const s = model.state;
    const tp = model.diagramDomain &&
      model.diagramDomain() === TWO_PARTY;
    const gate = stageGate();
    const card = h('div', 'card cd-rel-card');

    // Head: title + tools nho (slot, cach tinh, danh gia) — ban mau.
    const head = h('div', 'card-head');
    head.append(h('h3', 'card-title',
      tp ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế'));
    const tools = h('div', 'card-tools');
    const addSlotBtn = btn('+ Slot', 'sm', () => {
      if (model.addSlot()) scheduleEvaluate();
    });
    addSlotBtn.disabled = !model.canWrite() ||
      !s.capabilities.diagram || tp;   // two_party: 30 slot co dinh
    tools.append(addSlotBtn);
    const calc = btn('Xem cách tính', 'sm', async () => {
      calcOpen = !calcOpen;
      if (calcOpen) await model.evaluateDiagram();
      rerender();
    });
    calc.disabled = gate || !s.capabilities.diagram;
    tools.append(calc);
    const evalBtn = btn('Đánh giá thử', 'sm', async () => {
      const r = await model.evaluateDiagram();
      if (!r.ok && r.error) notify(
        `${r.error.code}: ${r.error.message}`, true);
      calcOpen = true;
    });
    evalBtn.disabled = gate || !s.capabilities.diagram ||
      s.busy === 'notary.diagram_evaluate';
    // Badge stale: stage revision da vuot lan evaluate cuoi cua draft.
    const staleEval = s.evaluatedRevision != null &&
      s.evaluatedRevision !== s.revision;
    if (staleEval) {
      evalBtn.setAttribute('aria-label',
        'Đánh giá thử — Stage đã đổi kể từ lần đánh giá');
    }
    tools.append(evalBtn);
    if (gate) {
      const pill = h('span', 'pill warn', 'Cập nhật Stage trước');
      pill.title = 'Đánh giá/lưu sơ đồ dùng Stage đã cập nhật — Cập ' +
        'nhật hoặc Hủy thay đổi Stage trước.';
      tools.append(pill);
    } else if (staleEval) {
      tools.append(h('span', 'pill warn',
        'Stage đã đổi kể từ lần đánh giá'));
    }
    head.append(tools);
    card.append(head);

    // Body: pool pane + vung diagram trong mot card (ban mau rel-card).
    const body = h('div', 'cd-rel-body');
    body.append(poolPaneEl());
    const dg = h('div', 'cd-diagram');
    dg.append(diagramBodyEl());
    body.append(dg);
    card.append(body);

    // Foot: save + word — ghi that ro, tach biet Cap nhat Stage.
    const foot = h('div', 'cd-rel-foot');
    const save = btn('Lưu sơ đồ', 'secondary js-save-diagram', async () => {
      const r = await model.saveDiagram();
      if (!r.ok && r.error && r.error.code !== 'workspace_conflict' &&
          r.error.code !== 'diagram_invalid_state') {
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    });
    if (s.diagramDirty) save.append(h('span', 'dirty-dot', ''));
    // Nhap moi (caseId=null): chua co case de persist — so do duoc
    // ghi cung "Lưu hồ sơ" (workspace_create), khong phai nut nay.
    save.disabled = gate || s.caseId == null || !model.canWrite() ||
      !s.diagramDirty || !s.capabilities.diagram;
    const word = btn('Xuất Word', 'primary', openWordDialog);
    word.disabled = !s.capabilities.word_export || s.wordBusy;
    foot.append(save, word);
    card.append(foot);
    return card;
  }

  return { build };
}

const G1_NOTARY_DIAGRAM = { createDiagramPane };

if (typeof window !== 'undefined') window.G1_NOTARY_DIAGRAM = G1_NOTARY_DIAGRAM;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_DIAGRAM;
}
