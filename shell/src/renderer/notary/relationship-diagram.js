'use strict';

/* Relationship diagram + Pool pane (MIN-112 → MIN-130 P7).
 *
 * SOT hanh vi: spec UX §4 + contracts/notary-case-drafting.md §7 + §13;
 * bo cuc/thao tac: docs/product/ui/prototypes/notary.js (canvas pan/zoom/
 * "Mở rộng", card thua ke + 2 hang chip, hai ben 30 cho).
 *
 * - Pool = Stage DA COMMIT tru nguoi da gan tren draft Diagram — ke ca
 *   nhap moi (caseId=null): draft Stage dang so KHONG lo vao Pool
 *   (MIN-129). Search chi loc hien thi — khong doi draft.
 * - Keo tha payload 'text/plain' JSON {kind:'person', row_id} — contract
 *   P6 giu nguyen: drop len node/slot = movePerson (move/swap), drop vao
 *   Pool = movePerson(row_id, null). Menu "Gán vị trí" = duong ban phim.
 * - Domain inheritance: canvas = world×zoom + SVG edges tu
 *   parentSlotIds/spouseSlotId cua DRAFT state (khong suy luan nghiep vu)
 *   + card gon (ten, nam sinh–mat, vai tro, 2 hang chip "Chủ đất"/
 *   "Nhận đất" = ownPositions/receivePositions doc lap §13.4).
 * - Domain two_party: 30 cho canonical p1..p30 — Ben A = p1..p15, Ben B
 *   = p16..p30 (p16 luon dau B, khong lay thu tu hang Stage lam so);
 *   khong mui ten/quan he thua ke, khong chip tai san, khong tu don lo
 *   trong. Card = "Chỗ N" + ten nguoi (khong ngay thang/vai tro).
 * - Slot tu sinh: base seed (nut "Tạo sơ đồ mẫu" khi canvas trong, qua
 *   model-level seedDiagramSlots) + requiredSlots cua engine sau
 *   evaluate — engine la SOT cho cho con thieu, view chi tao slot trong
 *   tuong ung, KHONG tu quyet dinh luat thua ke.
 * - Zoom (−/%/+ trong 0.5–1.6) + pan (keo nen) + "Mở rộng" overlay
 *   ~toan man (Esc/x + tra focus — openModal xu ly). Khong auto-fit/ep
 *   nho chu — 60+ node van thao tac bang cuon/pan/zoom.
 * - Moi draft-mutation schedule evaluateDiagram debounce ~500ms — chi
 *   domain inheritance (two_party engine khong ho tro — §13.5).
 * - Xoa slot (x) chi o inheritance va chi la draft Diagram — khong xoa
 *   dong Stage; two_party 30 slot canonical khong xoa duoc.
 *
 * Export UMD: window.G1_NOTARY_DIAGRAM + module.exports. DOM chi trong
 * build() (file load duoc trong node --test de static test).
 */

const REL_EVALUATE_DEBOUNCE_MS = 500;   // spec: 400–600ms sau draft doi
const TWO_PARTY = 'two_party';

// Kich thuoc layout canvas (px logic — scale boi zoom, khong co chu).
// MIN-133 D7 (mockup duyet 28/09/2026): node DA THA 144×87 (ten 14px,
// nam 13px, 2 hang chip 22×19); node TRONG 88×24 vien dut, khong chu.
// Le 6px, giua the he 14px (plan 12–16), giua node 14px, cap vo/chong
// 28px. CSS .cd-node/.cd-node-empty phai khop cac hang nay.
const NODE_W = 144, NODE_H = 87;
const EMPTY_W = 88, EMPTY_H = 24;
const PAD = 6, GAP_X = 14, SPOUSE_GAP = 28, GAP_Y = 14;
const ROW_H = NODE_H + GAP_Y;          // buoc toi da giua 2 hang the he
// Hai ben: 2 cot × 15 cho, cho cao 26px (CSS .cd-tp-slot khop).
const TP_COL_W = 288, TP_SLOT_H = 26, TP_SLOT_GAP = 4, TP_TITLE_H = 26;
const TP_W = PAD * 2 + TP_COL_W * 2 + 12;
const TP_H = PAD * 2 + TP_TITLE_H + 15 * TP_SLOT_H + 14 * TP_SLOT_GAP;
const ZOOM_MIN = 0.5, ZOOM_MAX = 1.6;

// Nhan hien thi cho slot id canonical seed (chi label — khong luat).
const SLOT_LABEL = {
  owner: 'Người để lại', father: 'Cha', mother: 'Mẹ',
  spouse: 'Vợ/chồng', spouse_father: 'Cha vợ/chồng',
  spouse_mother: 'Mẹ vợ/chồng',
};

// So cho canonical cua node two_party (p16 = dau Ben B); null neu khong
// phai id canonical.
function slotNum(id) {
  const m = /^p(\d+)$/.exec(id || '');
  return m ? Number(m[1]) : null;
}

// Layout the he tu parentSlotIds cua DRAFT state — pure function, khong
// suy luan nghiep vu: gen(n) = 0 neu khong co cha/me song, nguoc lai =
// max(gen cha/me) + 1. Chu ky draft (engine se bao loi) → gen 0.
// Trong mot gen: giu thu tu mang nodes, nhung cap vo/chong (spouseSlotId
// 2 chieu hop le 1 chieu) duoc don sat nhau de edge ngang ngan gon.
// MIN-133: kich thuoc theo trang thai node (da tha 144×87 / trong 88×24);
// hang rong nhat can giua, hang tren/duoi can theo tam con/cha-me da dat
// (cap vo/chong la mot khoi 28px). Chi la vi tri hien thi.
// Tra {pos: {id:{x,y,w,h,gen}}, w, h} — vi tri TOP-LEFT tren world logic.
function nodeSize(n) {
  return n && n.personId ? { w: NODE_W, h: NODE_H }
                         : { w: EMPTY_W, h: EMPTY_H };
}

function layoutInheritance(nodes) {
  const live = (nodes || []).filter((n) => n && !n.deleted);
  const byId = new Map(live.map((n) => [n.id, n]));
  const gens = new Map();                    // gen -> [nodes array order]
  const memo = new Map();
  const visiting = new Set();
  function genOf(n) {
    if (memo.has(n.id)) return memo.get(n.id);
    if (visiting.has(n.id)) return 0;        // chu ky — layout fallback
    visiting.add(n.id);
    const ps = (n.parentSlotIds || []).filter((p) => byId.has(p));
    let g = 0;
    if (ps.length) {
      g = Math.max(...ps.map((p) => genOf(byId.get(p)))) + 1;
    }
    visiting.delete(n.id);
    memo.set(n.id, g);
    return g;
  }
  for (const n of live) {
    const g = genOf(n);
    if (!gens.has(g)) gens.set(g, []);
    gens.get(g).push(n);
  }
  const spouseOf = (n) => (n.spouseSlotId && byId.get(n.spouseSlotId)) ||
    live.find((k) => k.spouseSlotId === n.id) || null;
  for (const arr of gens.values()) {
    const seen = new Set();
    const out = [];
    for (const n of arr) {
      if (seen.has(n.id)) continue;
      out.push(n); seen.add(n.id);
      const sp = spouseOf(n);
      if (sp && !seen.has(sp.id) &&
          memo.get(sp.id) === memo.get(n.id)) {
        out.push(sp); seen.add(sp.id);
      }
    }
    arr.splice(0, arr.length, ...out);
  }
  const size = new Map(live.map((n) => [n.id, nodeSize(n)]));
  const isPair = (a, b) =>
    a.spouseSlotId === b.id || b.spouseSlotId === a.id;
  // Khoi: node don hoac cap vo/chong ke nhau (giu sat 28px).
  const blocksOf = (row) => {
    const out = [];
    for (let i = 0; i < row.length; i += 1) {
      if (i + 1 < row.length && isPair(row[i], row[i + 1])) {
        out.push([row[i], row[i + 1]]); i += 1;
      } else {
        out.push([row[i]]);
      }
    }
    return out.map((m) => ({
      m, w: m.reduce((s, n) => s + size.get(n.id).w, 0) +
        (m.length > 1 ? SPOUSE_GAP : 0) }));
  };
  const gkeys = [...gens.keys()].sort((a, b) => a - b);
  const rows = gkeys.map((g) => blocksOf(gens.get(g)));
  const rowW = (bs) => bs.reduce((s, b) => s + b.w, 0) +
    Math.max(0, bs.length - 1) * GAP_X;
  const left = new Map();                    // id -> x trai (tuong doi)
  const center = (id) => left.get(id) + size.get(id).w / 2;
  // Dat mot hang: desired(block) = tam mong muon (hoac null). Quet trai
  // → phai giu thu tu + khoang cach toi thieu, roi dich ca hang ve phia
  // tam mong muon trung binh.
  function placeRow(bs, desired) {
    const xs = new Array(bs.length);
    const want = bs.map(desired);
    const k = want.findIndex((d) => d != null);
    if (k < 0) {
      let x = -rowW(bs) / 2;
      bs.forEach((b, i) => { xs[i] = x; x += b.w + GAP_X; });
    } else {
      xs[k] = want[k] - bs[k].w / 2;
      for (let i = k + 1; i < bs.length; i += 1) {
        const min = xs[i - 1] + bs[i - 1].w + GAP_X;
        xs[i] = want[i] != null ? Math.max(want[i] - bs[i].w / 2, min) : min;
      }
      for (let i = k - 1; i >= 0; i -= 1) {
        xs[i] = xs[i + 1] - GAP_X - bs[i].w;
      }
      let sum = 0, cnt = 0;
      bs.forEach((b, i) => {
        if (want[i] != null) { sum += want[i] - (xs[i] + b.w / 2); cnt += 1; }
      });
      const shift = cnt ? sum / cnt : 0;
      for (let i = 0; i < xs.length; i += 1) xs[i] += shift;
    }
    bs.forEach((b, i) => {
      let x = xs[i];
      for (const n of b.m) {
        left.set(n.id, x);
        x += size.get(n.id).w + SPOUSE_GAP;
      }
    });
  }
  const mean = (arr) => (arr.length
    ? arr.reduce((s, v) => s + v, 0) / arr.length : null);
  let anchor = 0;
  rows.forEach((bs, i) => { if (rowW(bs) > rowW(rows[anchor])) anchor = i; });
  if (rows.length) placeRow(rows[anchor], () => null);
  // Hang duoi hang rong nhat: theo tam cha/me da dat.
  for (let i = anchor + 1; i < rows.length; i += 1) {
    placeRow(rows[i], (b) => mean(b.m.flatMap((n) =>
      (n.parentSlotIds || []).filter((p) => left.has(p)).map(center))));
  }
  // Hang tren: theo tam con da dat.
  for (let i = anchor - 1; i >= 0; i -= 1) {
    placeRow(rows[i], (b) => mean(b.m.flatMap((n) => live
      .filter((k) => left.has(k.id) &&
        (k.parentSlotIds || []).includes(n.id))
      .map((k) => center(k.id)))));
  }
  const pos = {};
  let minX = Infinity;
  for (const x of left.values()) minX = Math.min(minX, x);
  const dx = Number.isFinite(minX) ? PAD - minX : PAD;
  let maxX = 0, y = PAD;
  for (const [gi, g] of gkeys.entries()) {
    let rowH = 0;
    for (const b of rows[gi]) {
      for (const n of b.m) {
        const s = size.get(n.id);
        const x = Math.round(left.get(n.id) + dx);
        pos[n.id] = { x, y, w: s.w, h: s.h, gen: g };
        maxX = Math.max(maxX, x + s.w);
        rowH = Math.max(rowH, s.h);
      }
    }
    y += rowH + GAP_Y;
  }
  const h = rows.length ? y - GAP_Y + PAD : PAD * 2;
  return { pos, w: Math.max(maxX, 0) + PAD, h };
}

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
  let zoom = 1;
  // Drag state cho pan canvas + splitter Pool — song qua cac lan build
  // (document listener dang ky 1 lan; build() chay lai khong nhan doi).
  let panDrag = null;    // {wrap, x, y, t, l}
  let poolDrag = null;   // {el, sp, x}
  // Canvas trong overlay "Mở rộng" — rebuild khi emit den de dong bo.
  let expandBody = null;

  if (typeof document !== 'undefined' && document.addEventListener) {
    document.addEventListener('mousemove', (e) => {
      if (panDrag) {
        panDrag.wrap.scrollLeft = panDrag.l - (e.clientX - panDrag.x);
        panDrag.wrap.scrollTop = panDrag.t - (e.clientY - panDrag.y);
      } else if (poolDrag) {
        const cur = poolDrag.el.getBoundingClientRect().width;
        const nx = Math.min(560, Math.max(150,
          cur + (e.clientX - poolDrag.x)));
        poolDrag.el.style.flex = `0 0 ${nx}px`;
        poolDrag.el.style.maxWidth = 'none';
        poolDrag.x = e.clientX;
      }
    });
    document.addEventListener('mouseup', () => {
      if (panDrag) {
        panDrag.wrap.classList.remove('panning');
        panDrag = null;
      }
      if (poolDrag) {
        poolDrag.sp.classList.remove('active');
        poolDrag = null;
      }
    });
  }

  // Canvas "Mở rộng" dang mo: emit moi → rebuild lai cho dong bo
  // (drag/drop/chip ben trong overlay mutate model → emit → ve lai).
  if (model.subscribe) {
    model.subscribe(() => { if (expandBody) rebuildExpand(); });
  }

  // Stage dirty (case da ton tai): evaluate/save diagram phai doi —
  // draft Stage chua cap nhat nen ket qua tinh se mo ta du lieu cu.
  // Nguoi dung Cap nhat hoac Huy Stage truoc (MIN-129 dirty-safety).
  function stageGate() {
    return model.state.caseId != null && model.state.stageDirty;
  }

  function isTp() {
    return model.diagramDomain && model.diagramDomain() === TWO_PARTY;
  }

  // Debounce evaluate sau moi draft-mutating action (§7.4: evaluate la
  // read-only — chay duoc ca khi locked; unsupported thi bo qua).
  // two_party: engine khong ho tro (§13.5) — khong goi evaluate.
  function scheduleEvaluate() {
    if (isTp() || !model.state.capabilities.diagram ||
        model.state.unsupported || stageGate()) {
      return;
    }
    if (evalTimer) clearTimeout(evalTimer);
    evalTimer = setTimeout(() => { void runEvaluate(); },
      REL_EVALUATE_DEBOUNCE_MS);
  }

  async function runEvaluate() {
    const r = await model.evaluateDiagram();
    if (!r.ok && r.error &&
        r.error.code !== 'diagram_invalid_state') {
      notify(`${r.error.code}: ${r.error.message}`, true);
    }
    if (r.ok) applyRequiredSlots();     // engine-required slots (SOT)
    return r;
  }

  function personRow(rowId) {
    // Draft (caseId=null): nguon la stage nhap; case that: committed.
    const src = model.state.caseId == null
      ? model.state.stage.people : model.state.committed.people;
    return src.find((x) => x.row_id === rowId) || null;
  }

  function personName(rowId) {
    const p = personRow(rowId);
    return p ? (p.ho_ten || '(không tên)') : '—';
  }

  // Nam sinh–mat tu truong Stage (YYYY-MM-DD | YYYY) — chi lay 4 so nam.
  function yearOf(v) {
    const m = /\d{4}/.exec(v || '');
    return m ? m[0] : null;
  }

  function personYears(rowId) {
    const p = personRow(rowId);
    if (!p) return null;
    const b = yearOf(p.ngay_sinh), d = yearOf(p.ngay_chet);
    if (!b && !d) return null;
    return `${b || '…'} – ${d || '…'}`;
  }

  function liveNodes() {
    return (model.state.diagram.nodes || [])
      .filter((n) => n && !n.deleted);
  }

  function nodeById(id) {
    return liveNodes().find((n) => n.id === id) || null;
  }

  // Nhan identity cua slot (label canonical hoac id tho) — khong phu
  // thuoc nguoi dang gan.
  function slotTag(n) {
    if (!n) return '—';
    if (SLOT_LABEL[n.id]) return SLOT_LABEL[n.id];
    const m = /^child_(\d+)$/.exec(n.id || '');
    if (m) return `Con ${m[1]}`;
    return n.id;
  }

  // Ten ngan de tham chieu slot: ten nguoi neu da gan, nhan slot neu
  // trong.
  function refName(n) {
    if (!n) return '—';
    if (n.personId) return personName(n.personId);
    return slotTag(n);
  }

  // Vai tro hien thi tu quan he draft da khai bao — presentation only,
  // KHONG suy luan nghiep vu (khong phan biet cha vs me — engine cung
  // khong: parentSlotIds la tap cha/me).
  function roleLabel(n) {
    if (n.id === 'owner') return 'Người để lại';
    const kids = liveNodes().filter(
      (k) => (k.parentSlotIds || []).includes(n.id));
    if (kids.length) {
      const names = kids.slice(0, 2).map(refName).join(', ');
      return `cha/mẹ của ${names}${kids.length > 2 ? '…' : ''}`;
    }
    const sp = nodeById(n.spouseSlotId) ||
      liveNodes().find((k) => k.spouseSlotId === n.id);
    if (sp) return `vợ/chồng của ${refName(sp)}`;
    const ps = (n.parentSlotIds || []).map(nodeById).filter(Boolean);
    if (ps.length) return `con của ${ps.map(refName).join(' + ')}`;
    return SLOT_LABEL[n.id] || '';
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
    nm.title = sub ? `${label} — ${sub}` : label;
    if (sub) nm.append(h('span', 'cd-pool-sub', sub));
    card.append(nm);
    // Duong ban phim thay keo-tha (a11y) — menu chon vi tri gan.
    // MIN-133: nut → noi tren mep phai, chi hien khi hover/focus (the
    // Pool 176px chi con ten) — van trong tab order.
    const assign = btn('→', 'sm cd-pool-assign',
      () => openAssignMenu(row, kind));
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
        const nodes = liveNodes();
        const assign = (nodeId) => () => {
          // movePerson bao trum ca move vao cho trong LAN swap khi cho
          // da co nguoi — cung semantics voi keo-tha (§13.5 Q9).
          if (model.movePerson(row.row_id, nodeId)) scheduleEvaluate();
          close();
        };
        if (isTp()) {
          // 30 cho canonical: trong = gan, co nguoi = doi cho — nhom
          // theo Ben A (p1..p15) / Ben B (p16..p30).
          for (const [label, lo, hi] of
              [['Bên A', 1, 15], ['Bên B', 16, 30]]) {
            const arr = nodes
              .filter((n) => {
                const k = slotNum(n.id);
                return k >= lo && k <= hi;
              })
              .sort((a, b) => slotNum(a.id) - slotNum(b.id));
            if (!arr.length) continue;
            body.append(h('div', 'muted', label));
            const grid = h('div', 'cd-assign-grid');
            for (const n of arr) {
              const num = slotNum(n.id);
              const b = n.personId
                ? btn(`${num} — ${personName(n.personId)}`, 'sm',
                    assign(n.id))
                : btn(`${num}`, 'secondary sm', assign(n.id));
              b.title = n.personId
                ? `Đổi chỗ ${num} với ${personName(n.personId)}`
                : `Gán vào chỗ ${num}`;
              grid.append(b);
            }
            body.append(grid);
          }
        } else {
          const empty = nodes.filter((n) => !n.personId);
          if (empty.length) {
            body.append(h('div', 'muted', 'Slot đang trống:'));
            const grid = h('div', 'cd-tight');
            for (const n of empty) {
              grid.append(btn(`Gán vào “${refName(n)}”`, 'secondary sm',
                assign(n.id)));
            }
            body.append(grid);
          }
          // Doi cho voi slot da co nguoi (swap) — duong ban phim cho
          // drop len node occupied.
          const others = nodes.filter(
            (n) => n.personId && n.personId !== row.row_id);
          if (others.length) {
            body.append(h('div', 'muted',
              'Đổi chỗ với slot đã có người:'));
            const grid = h('div', 'cd-tight');
            for (const n of others) {
              grid.append(btn(
                `${slotTag(n)} — ${personName(n.personId)}`, 'sm',
                assign(n.id)));
            }
            body.append(grid);
          }
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
          if (!nodes.length) {
            body.append(btn('Tạo sơ đồ mẫu và gán', 'secondary', () => {
              seedBase();
              if (model.assignPerson('owner', row.row_id)) {
                scheduleEvaluate();
              }
              close();
            }));
          }
        }
      }
      box.append(body);
      const foot = h('div', 'modal-foot');
      foot.append(btn('Đóng', '', close));
      box.append(foot);
    }, { bare: true });
  }

  // ---------- Seed + requiredSlots ----------

  // Seed 7 slot canonical (cha/me hai ben + owner + spouse + child_1)
  // khi canvas trong — qua helper model-level seedDiagramSlots. Helper
  // mutate state truc tiep (khong qua touchDiagram) → ep dirty+emit
  // bang mot setNodeRelation no-op (workaround: model khong expose
  // touch-only/seed API tren instance — ghi handoff).
  function seedBase() {
    const seed = (typeof window !== 'undefined' &&
                  window.G1_NOTARY_MODEL &&
                  window.G1_NOTARY_MODEL.seedDiagramSlots) || null;
    const nodes = model.state.diagram.nodes ||
      (model.state.diagram.nodes = []);
    if (seed) {
      seed(nodes);
      const any = nodes.find((n) => n && !n.deleted);
      if (any) model.setNodeRelation(any.id, {});
      else model.dismissNotice();
      return true;
    }
    // Fallback qua public API khi helper model-level khong duoc nap.
    const g = (id) => nodes.find((n) => n && n.id === id && !n.deleted);
    const mk = (id) => { if (!g(id)) model.addSlot(id); };
    mk('father'); mk('mother');
    mk('spouse_father'); mk('spouse_mother');
    mk('owner'); mk('spouse'); mk('child_1');
    const has = (id) => !!g(id);
    if (has('owner')) {
      model.setNodeRelation('owner', {
        parentSlotIds: ['father', 'mother'].filter(has),
        spouseSlotId: has('spouse') ? 'spouse' : null });
    }
    if (has('spouse')) {
      model.setNodeRelation('spouse', {
        parentSlotIds: ['spouse_father', 'spouse_mother'].filter(has),
        spouseSlotId: has('owner') ? 'owner' : null });
    }
    if (has('child_1')) {
      model.setNodeRelation('child_1', {
        parentSlotIds: ['owner', 'spouse'].filter(has) });
    }
    return true;
  }

  // Tu sinh slot thieu theo render_model.requiredSlots cua engine —
  // engine la SOT cho cho con thieu: view chi tao slot TRONG + noi quan
  // he tuong ung (father/mother → parentSlotIds cua anchor; spouse →
  // spouseSlotId; child → parentSlotIds tro ve anchor [+ spouse]).
  // Chi ap cho anchor DA GAN NGUOI (engine that: anchor = nguoi da mat;
  // mock dev emit ca cho slot trong → bo qua de khong no canvas).
  function applyRequiredSlots() {
    if (!model.canWrite() || isTp()) return false;
    const reqs = (model.state.renderModel &&
                  model.state.renderModel.requiredSlots) || [];
    if (!reqs.length) return false;
    const freeId = (bases) => {
      const used = new Set(
        (model.state.diagram.nodes || []).map((n) => n && n.id));
      for (const b of bases) if (!used.has(b)) return b;
      const last = bases[bases.length - 1];
      let i = 2;
      while (used.has(`${last}_${i}`)) i += 1;
      return `${last}_${i}`;
    };
    let touched = false;
    for (const req of reqs) {
      const anchor = nodeById(req.anchorSlotId);
      if (!anchor || !anchor.personId) continue;
      const types = new Set(req.slotTypes || []);
      // Cha/me: dam bao du slot cha/me (toi da 2 — contract cap).
      const wantKinds = ['father', 'mother'].filter((t) => types.has(t));
      const haveParents = (anchor.parentSlotIds || [])
        .filter((p) => nodeById(p)).length;
      const needParents = Math.min(
        Math.max(0, wantKinds.length - haveParents),
        2 - haveParents);
      for (let i = 0; i < needParents; i += 1) {
        const kind = wantKinds[i] || 'parent';
        const node = model.addSlot(
          freeId([kind, `${kind}_${anchor.id}`]));
        if (!node) break;
        model.setNodeRelation(anchor.id, {
          parentSlotIds: [...(anchor.parentSlotIds || []), node.id] });
        touched = true;
      }
      // Vo/chong: anchor chua co spouse (khai bao 1 chieu la du —
      // engine spouse_conflict chi khi lech cap).
      if (types.has('spouse')) {
        const hasSpouse = (anchor.spouseSlotId &&
          nodeById(anchor.spouseSlotId)) || liveNodes().some(
            (n) => n.spouseSlotId === anchor.id);
        if (!hasSpouse) {
          const node = model.addSlot(
            freeId(['spouse', `spouse_${anchor.id}`]));
          if (node) {
            model.setNodeRelation(node.id, { spouseSlotId: anchor.id });
            touched = true;
          }
        }
      }
      // Con: dam bao ≥ minimumEmptyChildSlots slot con TRONG; noi ve ca
      // spouse cua anchor (ke ca khi spouse khai bao 1 chieu tu phia
      // spouse — nhu seed child_1 → [owner, spouse]).
      if (types.has('child')) {
        const need = Math.max(0, req.minimumEmptyChildSlots || 0);
        const emptyKids = () => liveNodes().filter(
          (n) => !n.personId &&
            (n.parentSlotIds || []).includes(anchor.id)).length;
        const sp = (anchor.spouseSlotId &&
          nodeById(anchor.spouseSlotId)) || liveNodes().find(
            (n) => n.spouseSlotId === anchor.id);
        for (let i = emptyKids(); i < need; i += 1) {
          const node = model.addSlot(freeId([`child_${anchor.id}`]));
          if (!node) break;
          const parents = sp ? [anchor.id, sp.id] : [anchor.id];
          model.setNodeRelation(node.id, { parentSlotIds: parents });
          touched = true;
        }
      }
    }
    return touched;
  }

  // ---------- Diagram ----------

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

  // Drop target chung: nhan pool card hoac node co nguoi keo vao —
  // movePerson bao trum move/swap (§13.5 Q9) cho ca hai domain.
  function wirePersonDrop(el, nodeId) {
    el.addEventListener('dragover', (e) => {
      e.preventDefault();
      el.classList.add('drop-hint');
    });
    el.addEventListener('dragleave', () =>
      el.classList.remove('drop-hint'));
    el.addEventListener('drop', (e) => {
      e.preventDefault();
      el.classList.remove('drop-hint');
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person' &&
            model.movePerson(d.row_id, nodeId)) {
          scheduleEvaluate();
        }
      } catch (err) { /* payload rac — bo qua */ }
    });
  }

  // ---------- card thua ke ----------

  function inheritanceCardEl(n, at) {
    const ro = !model.canWrite();
    const p = n.personId ? personRow(n.personId) : null;
    const role = roleLabel(n);
    const card = h('div', 'cd-node');
    card.style.left = `${at.x}px`;
    card.style.top = `${at.y}px`;
    card.dataset.nodeId = n.id;
    card.setAttribute('role', 'group');
    if (n.hidden) card.classList.add('cd-node-hidden');
    if (n.id === 'owner') card.classList.add('cd-node-owner');

    // Nut hanh dong: chi hien khi hover/focus (CSS .cd-node-acts) —
    // van nam trong tab order cho ban phim.
    const acts = h('div', 'cd-node-acts');
    const del = btn('×', 'icon-x', () => {
      // Xoa slot = draft Diagram — dong Stage giu nguyen (§7.1).
      if (model.removeNode(n.id)) scheduleEvaluate();
    });
    del.title = `Xóa slot ${slotTag(n)} khỏi sơ đồ (draft — không xóa Stage)`;
    del.setAttribute('aria-label', `Xóa slot ${slotTag(n)}`);
    del.disabled = ro;

    if (!n.personId) {
      // MIN-133 D7: node TRONG 88×24 vien dut — khong nhan vai tro,
      // khong hint, khong chip. Van la drop target; vai tro doc qua
      // aria-label/tooltip (screen reader + ban phim qua menu Gán vị trí).
      card.classList.add('cd-node-empty');
      const what = role || slotTag(n);
      const label = `Ô trống: ${what} — thả người từ Pool vào đây`;
      card.setAttribute('aria-label', label);
      card.title = label;
      acts.append(del);
      card.append(acts);
      wirePersonDrop(card, n.id);
      return card;
    }

    const name = (p && p.ho_ten) || '(chưa đặt tên)';
    card.setAttribute('aria-label', role ? `${name} — ${role}` : name);
    if (role) card.title = role;
    const nm = h('span', 'cd-node-name', name);
    nm.title = role ? `${name} — ${role}` : name;
    card.append(nm);
    if (!ro) {
      // Ban phim: gan lai/doi cho cho nguoi dang o node (menu du nang
      // luc nhu keo-tha — move/swap) + bo gan ve Pool.
      const mv = btn('→', 'cd-mini-btn', () => openAssignMenu(p, 'person'));
      mv.title = 'Gán lại/đổi chỗ (bàn phím — thay cho kéo thả)';
      mv.setAttribute('aria-label', `Gán lại ${name}`);
      mv.disabled = !model.state.capabilities.diagram;
      const un = btn('↩', 'cd-mini-btn js-node-unassign', () => {
        if (model.movePerson(n.personId, null)) scheduleEvaluate();
      });
      un.title = 'Bỏ gán — trả người về Pool';
      un.setAttribute('aria-label', `Bỏ gán ${name} về Pool`);
      acts.append(mv, un);
    }
    acts.append(del);
    card.append(acts);

    const meta = h('div', 'cd-node-meta');
    meta.append(h('span', '', personYears(n.personId) || '—'));
    const alloc = allocBadgeEl(n.personId);
    if (alloc) meta.append(alloc);
    card.append(meta);

    // 2 hang chip so (§13.4): "Chủ" = ownPositions (chủ đất), "Nhận" =
    // receivePositions (nhận đất) — doc lap, multi-select; chip vi tri
    // chua co asset disable (server van prune > len(assets) tai commit).
    const assetCount = model.state.stage.assets.length;
    for (const [label, full, kind, arr] of [
        ['Chủ', 'Chủ đất', 'own', n.ownPositions],
        ['Nhận', 'Nhận đất', 'receive', n.receivePositions]]) {
      const wrap = h('div', 'cd-posrow');
      const lb = h('span', 'cd-posrow-label', label);
      lb.title = full;
      wrap.append(lb);
      for (const pos of [1, 2, 3]) {
        const on = Array.isArray(arr) && arr.includes(pos);
        const chip = btn(`${pos}`,
          `cd-poschip${on ? ' on' : ''}`, () => {
            if (model.toggleNodePosition(n.id, kind, pos)) {
              scheduleEvaluate();
            }
          });
        chip.disabled = ro || pos > assetCount;
        chip.setAttribute('aria-pressed', String(on));
        chip.setAttribute('aria-label',
          `${full} tài sản ${pos} — ${slotTag(n)}`);
        chip.title = `${full} — tài sản ${pos}`;
        wrap.append(chip);
      }
      card.append(wrap);
    }

    // Drag: nguoi tren node keo di — cung payload Pool card.
    if (n.personId && !ro) {
      card.draggable = true;
      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain',
          JSON.stringify({ kind: 'person', row_id: n.personId }));
        card.classList.add('dragging');
      });
      card.addEventListener('dragend', () =>
        card.classList.remove('dragging'));
    }
    wirePersonDrop(card, n.id);
    return card;
  }

  // ---------- card hai ben (30 cho canonical) ----------

  function tpSlotEl(n) {
    const ro = !model.canWrite();
    const num = slotNum(n.id);
    const p = n.personId ? personRow(n.personId) : null;
    const slot = h('div',
      `cd-tp-slot${p ? ' filled' : ''}${n.deleted ? ' cd-tp-off' : ''}`);
    slot.dataset.slotId = n.id;
    slot.append(h('span', 'cd-tp-idx', `Chỗ ${num ?? n.id}`));
    if (n.deleted) {
      // Degenerate (contract doi 30 slot song) — hien nhu cho mat hieu
      // luc, khong nhan drop.
      slot.append(h('span', 'cd-tp-empty muted', '—'));
      return slot;
    }
    if (p) {
      // Design P7: card hai ben chi TEN + so cho — khong ngay thang/
      // vai tro/chip thua ke (§13.5).
      const nm = h('span', 'cd-tp-nm', p.ho_ten || '(chưa đặt tên)');
      nm.title = p.ho_ten || '';
      slot.append(nm);
      // Nut hien khi hover/focus (MIN-133) — van trong tab order.
      const acts = h('div', 'cd-tp-acts');
      const mv = btn('→', 'cd-mini-btn',
        () => openAssignMenu(p, 'person'));
      mv.title = 'Đổi chỗ/gán lại (bàn phím — thay cho kéo thả)';
      mv.setAttribute('aria-label', `Đổi chỗ ${p.ho_ten || 'người này'}`);
      mv.disabled = ro || !model.state.capabilities.diagram;
      const del = btn('×', 'icon-x', () => {
        if (model.movePerson(n.personId, null)) scheduleEvaluate();
      });
      del.title = `Bỏ ${p.ho_ten || ''} khỏi chỗ ${num} (về Pool)`;
      del.setAttribute('aria-label', `Bỏ khỏi chỗ ${num}`);
      del.disabled = ro;
      acts.append(mv, del);
      slot.append(acts);
      if (!ro) {
        slot.draggable = true;
        slot.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain',
            JSON.stringify({ kind: 'person', row_id: n.personId }));
          slot.classList.add('dragging');
        });
        slot.addEventListener('dragend', () =>
          slot.classList.remove('dragging'));
      }
    } else {
      // MIN-133 D7: cho trong gon — o viền dut nho, khong hint chu;
      // mo ta cho screen reader/tooltip.
      const label = `Chỗ ${num} trống — thả người từ Pool vào đây`;
      slot.setAttribute('aria-label', label);
      slot.title = label;
      slot.append(h('span', 'cd-tp-empty', ''));
    }
    wirePersonDrop(slot, n.id);
    return slot;
  }

  function tpSideCol(title, list, total) {
    const col = h('div', 'cd-side-col');
    const ttl = h('h3', 'cd-side-title');
    ttl.append(h('span', '', title));
    const filled = list.filter((n) => n.personId && !n.deleted).length;
    ttl.append(h('span', 'pill accent', `${filled}/${total} chỗ`));
    col.append(ttl);
    const wrap = h('div', 'cd-tp-list');
    for (const n of list) wrap.append(tpSlotEl(n));
    col.append(wrap);
    return col;
  }

  // 30 cho canonical: lay DUNG node theo id p1..p30 — slot 16 luon dau
  // Ben B bat ke thu tu mang/hang Stage; cho trong giu nguyen vi tri,
  // khong compact (§13.5).
  function twoPartyInto(scale) {
    const byId = new Map(
      (model.state.diagram.nodes || []).map((n) => [n.id, n]));
    const pick = (from, to) => {
      const out = [];
      for (let i = from; i <= to; i += 1) {
        out.push(byId.get(`p${i}`) ||
          { id: `p${i}`, personId: null, deleted: true });
      }
      return out;
    };
    const sides = h('div', 'cd-sides');
    sides.append(
      tpSideCol('Bên A (p1–p15)', pick(1, 15), 15),
      tpSideCol('Bên B (p16–p30)', pick(16, 30), 15));
    scale.append(sides);
    return { w: TP_W, h: TP_H };
  }

  // ---------- canvas (pan + zoom, khong auto-fit) ----------

  function inheritanceInto(scale) {
    const nodes = model.state.diagram.nodes || [];
    const lay = layoutInheritance(nodes);
    scale.append(edgesSvgEl(nodes, lay.pos, lay.w, lay.h));
    for (const n of nodes) {
      if (n.deleted) continue;
      scale.append(inheritanceCardEl(n, lay.pos[n.id]));
    }
    return lay;
  }

  function canvasEl() {
    const tp = isTp();
    const wrap = h('div', 'cd-canvas-wrap');
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label',
      tp ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế');
    if (!liveNodes().length && !tp) {
      const e = face(L.faceEmpty(
        'Sơ đồ chưa có slot.',
        'Gán người từ Pool, dùng + Slot, hoặc tạo sơ đồ mẫu 7 slot cơ ' +
        'bản (cha/mẹ hai bên, người để lại, vợ/chồng, con).'));
      if (model.canWrite()) {
        e.append(btn('Tạo sơ đồ mẫu', 'secondary', () => {
          if (seedBase()) scheduleEvaluate();
        }));
      }
      wrap.append(e);
      return wrap;
    }
    const scale = h('div', 'cd-canvas-scale');
    const lay = tp ? twoPartyInto(scale) : inheritanceInto(scale);
    scale.style.transform = `scale(${zoom})`;
    scale.style.width = `${lay.w}px`;
    scale.style.height = `${lay.h}px`;
    const world = h('div', 'cd-canvas-world');
    world.style.width = `${lay.w * zoom}px`;
    world.style.height = `${lay.h * zoom}px`;
    world.append(scale);
    wrap.append(world);
    // Pan: keo tren NEN (wrap/world/scale — khong phai card) → cuon.
    // move/up xu ly o document listener (dang ky 1 lan tren pane).
    wrap.addEventListener('mousedown', (e) => {
      if (e.target !== wrap && e.target !== world &&
          e.target !== scale) return;
      panDrag = { wrap, x: e.clientX, y: e.clientY,
                  t: wrap.scrollTop, l: wrap.scrollLeft };
      wrap.classList.add('panning');
    });
    return wrap;
  }

  // Edges SVG (MIN-133, theo mockup — khong mui ten): vo/chong = doan
  // ngang net dut giua hai card cung hang; cha/me → con = elbow tu day
  // card cha/me (hoac tu giua doan vo/chong khi ca hai la cha/me cua con)
  // xuong thanh ngang o giua khe the he roi xuong dinh card con. Doc tu
  // parentSlotIds/spouseSlotId draft — khong suy luan. Kich thuoc lay
  // tu pos (w/h theo node da tha/trong) nen khop layout.
  function edgesSvgEl(nodes, pos, w, hgt) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'cd-canvas-edges');
    svg.setAttribute('width', String(w));
    svg.setAttribute('height', String(hgt));
    svg.setAttribute('aria-hidden', 'true');
    const edgePath = (d, cls) => {
      const pe = document.createElementNS(ns, 'path');
      pe.setAttribute('d', d);
      pe.setAttribute('class', cls ? `cd-edge ${cls}` : 'cd-edge');
      svg.append(pe);
    };
    const byId = new Map(nodes.filter((n) => n && !n.deleted)
      .map((n) => [n.id, n]));
    const paired = (a, b) => !!(a && b &&
      (a.spouseSlotId === b.id || b.spouseSlotId === a.id));
    // Doan vo/chong giua hai card cung hang: {x1, x2, y} hoac null.
    const spouseSeg = (a, b) => {
      const pa = pos[a], pb = pos[b];
      if (!pa || !pb || pa.y !== pb.y) return null;
      const [l, r] = pa.x <= pb.x ? [pa, pb] : [pb, pa];
      const x1 = l.x + l.w, x2 = r.x;
      if (x2 <= x1) return null;
      return { x1, x2, y: l.y + Math.min(l.h, r.h) / 2 };
    };
    const drawn = new Set();
    for (const n of nodes) {
      if (n.deleted || !pos[n.id]) continue;
      const c = pos[n.id];
      // Vo/chong: ve mot lan cho moi cap.
      if (n.spouseSlotId && pos[n.spouseSlotId]) {
        const key = [n.id, n.spouseSlotId].sort().join('|');
        if (!drawn.has(key)) {
          drawn.add(key);
          const seg = spouseSeg(n.id, n.spouseSlotId);
          if (seg) {
            edgePath(`M${seg.x1} ${seg.y} H${seg.x2}`, 'cd-edge-spouse');
          }
        }
      }
      // Cha/me → con. Khi cha me la mot cap vo/chong: ve MOT edge tu
      // giua doan vo/chong (khong ve 2 edge trung nhau).
      const ps = (n.parentSlotIds || []).filter((p) => pos[p]);
      const busY = c.y - GAP_Y / 2;
      const cx = c.x + c.w / 2;
      const seenOrigin = new Set();
      for (const pid of ps) {
        const pp = pos[pid];
        let ox = pp.x + pp.w / 2, oy = pp.y + pp.h;
        const mate = ps.find((q) => q !== pid &&
          paired(byId.get(pid), byId.get(q)));
        const seg = mate ? spouseSeg(pid, mate) : null;
        if (seg) { ox = (seg.x1 + seg.x2) / 2; oy = seg.y; }
        const key = `${ox},${oy}`;
        if (seenOrigin.has(key)) continue;
        seenOrigin.add(key);
        edgePath(`M${ox} ${oy} V${busY} H${cx} V${c.y}`, 'cd-edge-parent');
      }
    }
    return svg;
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
      const nm = personName(pid);
      return nm === '—' ? String(pid) : nm;
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

  // ---------- zoom + "Mở rộng" ----------

  const zoomLabels = new Set();
  function setZoom(v) {
    zoom = Math.min(ZOOM_MAX,
      Math.max(ZOOM_MIN, Math.round(v * 10) / 10));
    const pct = `${Math.round(zoom * 100)}%`;
    for (const l of zoomLabels) {
      // Label da detach khoi DOM (rebuild cu) → bo khoi set, khong cap
      // nhat (label moi tao da in % hien tai).
      if (l.isConnected === false) { zoomLabels.delete(l); continue; }
      l.textContent = pct;
    }
    if (expandBody) rebuildExpand();
    rerender();
  }

  function zoomClusterEl() {
    const z = h('div', 'cd-zoom');
    const minus = btn('−', 'sm', () => setZoom(zoom - 0.1));
    const plus = btn('+', 'sm', () => setZoom(zoom + 0.1));
    minus.setAttribute('aria-label', 'Thu nhỏ sơ đồ');
    plus.setAttribute('aria-label', 'Phóng to sơ đồ');
    const lbl = h('span', 'cd-zoom-label', `${Math.round(zoom * 100)}%`);
    zoomLabels.add(lbl);
    z.append(minus, lbl, plus);
    return z;
  }

  function rebuildExpand() {
    if (!expandBody) return;
    if (expandBody.isConnected === false) {
      // Overlay da dong — don tham chieu, khong rebuild DOM thua.
      expandBody = null;
      return;
    }
    expandBody.innerHTML = '';
    expandBody.append(canvasEl());
  }

  // "Mở rộng": overlay ~toan man qua openModal (Esc/x/click-outside +
  // tra focus ve nut da san). Canvas ben trong share zoom + tu dong bo
  // khi model emit (subscribe o tren).
  function openExpanded() {
    openModal((box, close) => {
      box.classList.add('cd-expand');
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title',
        `${isTp() ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế'} — toàn màn`));
      const zc = zoomClusterEl();
      head.append(zc);
      const x = h('button', 'modal-close', '×');
      x.type = 'button';
      x.setAttribute('aria-label', 'Đóng');
      x.onclick = close;
      head.append(x);
      box.append(head);
      expandBody = h('div', 'modal-body cd-expand-body');
      box.append(expandBody);
      // box CHUA attach (openModal build truoc append): isConnected=false
      // nen KHONG qua rebuildExpand() — no co check "da dong" cho loi
      // goi tu subscribe. Build truc tiep.
      expandBody.append(canvasEl());
    }, { bare: true, wide: true });
  }

  // ---------- Pool pane (committed-only) + tier ----------

  function poolPaneEl() {
    const s = model.state;
    const pane = h('div', 'cd-pool');
    const head = h('div', 'cd-pool-head');
    const title = h('h3', 'cd-pool-title', 'Pool');
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
    pane.append(head, search);
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

  // Splitter dung chung (styles.css .splitter-v): keo ngang doi ty le
  // Pool / so do; ban phim ←/→ ±24px — duong ban phim cho thao tac keo.
  function poolSplitterEl(poolEl) {
    const s = h('div', 'splitter-v');
    s.tabIndex = 0;
    s.setAttribute('role', 'separator');
    s.setAttribute('aria-label', 'Đổi chiều rộng Pool / sơ đồ');
    s.setAttribute('aria-orientation', 'vertical');
    s.title = 'Kéo hoặc ←/→ để đổi chiều rộng Pool / sơ đồ';
    s.addEventListener('mousedown', (e) => {
      poolDrag = { el: poolEl, sp: s, x: e.clientX };
      s.classList.add('active');
      e.preventDefault();
    });
    s.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault();
      const cur = poolEl.getBoundingClientRect().width;
      const nx = Math.min(560, Math.max(150,
        cur + (e.key === 'ArrowRight' ? 24 : -24)));
      poolEl.style.flex = `0 0 ${nx}px`;
      poolEl.style.maxWidth = 'none';
    });
    return s;
  }

  // Vung diagram (canvas + warnings/errors/calc panel) — P7 so huu.
  function diagramRegionEl() {
    const s = model.state;
    const dg = h('div', 'cd-diagram');
    dg.append(canvasEl());
    const extra = h('div', 'cd-diagram-extra');
    const deletedCount = (s.diagram.nodes || [])
      .filter((n) => n && n.deleted).length;
    if (deletedCount) {
      // Slot da xoa giu trong du lieu draft (engine bo qua) — bao so
      // dem de nguoi dung biet chung khong bien mat vo co.
      extra.append(h('div', 'muted small',
        `${deletedCount} slot đã xóa (vẫn giữ trong dữ liệu draft).`));
    }
    for (const w of s.diagramWarnings || []) {
      // Shape hon hop: compose warnings la string, engine warnings la
      // {code,message} — render ca hai.
      extra.append(h('div', 'muted warn-text',
        typeof w === 'string' ? w : (w.message || w.code)));
    }
    for (const er of s.diagramErrors || []) {
      extra.append(h('div', 'error', er.message || er.code));
    }
    if (calcOpen) extra.append(calcPanelEl());
    if (extra.childElementCount) dg.append(extra);
    return dg;
  }

  function build() {
    const s = model.state;
    const tp = isTp();
    const gate = stageGate();
    const card = h('div', 'card cd-rel-card');

    // Head: title + tools nho (slot, cach tinh, danh gia — chi domain
    // inheritance co engine; zoom + Mo rong cho ca hai) — ban mau.
    const head = h('div', 'card-head');
    head.append(h('h3', 'card-title',
      tp ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế'));
    const tools = h('div', 'card-tools');
    if (!tp) {
      const addSlotBtn = btn('+ Slot', 'sm', () => {
        if (model.addSlot()) scheduleEvaluate();
      });
      addSlotBtn.disabled = !model.canWrite() ||
        !s.capabilities.diagram;
      tools.append(addSlotBtn);
      const calc = btn('Xem cách tính', 'sm', async () => {
        calcOpen = !calcOpen;
        if (calcOpen) await runEvaluate();
        rerender();
      });
      calc.disabled = gate || !s.capabilities.diagram;
      tools.append(calc);
      const evalBtn = btn('Đánh giá thử', 'sm', async () => {
        await runEvaluate();
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
        if (!gate) {
          tools.append(h('span', 'pill warn',
            'Stage đã đổi kể từ lần đánh giá'));
        }
      }
      tools.append(evalBtn);
    }
    if (gate) {
      const pill = h('span', 'pill warn', 'Cập nhật Stage trước');
      pill.title = 'Đánh giá/lưu sơ đồ dùng Stage đã cập nhật — Cập ' +
        'nhật hoặc Hủy thay đổi Stage trước.';
      tools.append(pill);
    }
    tools.append(zoomClusterEl());
    const expand = btn('⛶ Mở rộng', 'sm', () => openExpanded());
    expand.setAttribute('aria-label', 'Mở rộng sơ đồ toàn màn');
    expand.title = 'Xem sơ đồ ở cửa sổ lớn gần toàn màn hình';
    tools.append(expand);
    // MIN-133 D6: Luu so do + Xuat Word len head (mockup — bo footer
    // .cd-rel-foot). Save giu dirty-dot + gate stageDirty nhu truoc.
    tools.append(h('span', 'cd-vsep', ''));
    const save = btn('Lưu sơ đồ', 'sm secondary js-save-diagram', async () => {
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
    const word = btn('Xuất Word', 'sm primary', openWordDialog);
    word.disabled = !s.capabilities.word_export || s.wordBusy;
    tools.append(save, word);
    head.append(tools);
    card.append(head);

    // Body: pool pane + splitter + vung diagram trong mot card
    // (ban mau rel-card: Pool trai ~22%, so do phai).
    const body = h('div', 'cd-rel-body');
    const poolEl = poolPaneEl();
    body.append(poolEl);
    body.append(poolSplitterEl(poolEl));
    body.append(diagramRegionEl());
    card.append(body);
    return card;
  }

  return { build };
}

const G1_NOTARY_DIAGRAM = {
  createDiagramPane,
  // Export cho test thuan: layout thua ke + so cho canonical —
  // pure functions, khong can DOM/model.
  _internals: { layoutInheritance, slotNum, NODE_W, NODE_H, PAD,
                ROW_H, GAP_X, ZOOM_MIN, ZOOM_MAX },
};

if (typeof window !== 'undefined') window.G1_NOTARY_DIAGRAM = G1_NOTARY_DIAGRAM;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_DIAGRAM;
}
