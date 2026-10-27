'use strict';

/* Relationship diagram + Pool pane (MIN-112 → MIN-130 P7).
 *
 * SOT hanh vi: spec UX §4 + contracts/notary-case-drafting.md §7 + §13;
 * bo cuc/thao tac: _bmad-output/specs/ui/prototypes/notary.js (canvas pan/zoom/
 * "Mở rộng", card thua ke + 2 hang chip, hai ben 30 cho).
 *
 * - Pool = nguoi CHUA GAN tren draft Diagram, luon doc Stage dang sua
 *   (cung nguon voi bang Nguoi/nhan node). Chi nguoi — tai san khong
 *   xuong Pool (khong co flow gan len node).
 *   Search chi loc hien thi — khong doi draft.
 * - Keo tha payload 'text/plain' JSON {kind:'person', row_id} — contract
 *   P6 giu nguyen: drop len node/slot = movePerson, drop vao Pool =
 *   movePerson(row_id, null). Menu "Gán vị trí" = duong ban phim.
 * - Domain inheritance: canvas = world×zoom + SVG edges tu
 *   parentSlotIds/spouseSlotIds cua DRAFT state (khong suy luan nghiep vu)
 *   + card gon (ten, nam sinh–mat, vai tro, 2 hang chip "Chủ đất"/
 *   "Nhận đất" = ownPositions/receivePositions doc lap §13.4).
 * - Domain two_party: 30 cho canonical p1..p30 — Ben A = p1..p15, Ben B
 *   = p16..p30 (p16 luon dau B, khong lay thu tu hang Stage lam so);
 *   khong mui ten/quan he thua ke, khong chip tai san, khong tu don lo
 *   trong. Card = "Chỗ N" + ten nguoi (khong ngay thang/vai tro).
 * - Draft moi bat dau DUNG 1 o 'owner' trong. O them tu engine
 *   requiredSlots hoac menu Quan he cua tung nguoi: chi tao o TRONG,
 *   gan nguoi da co tu Stage/Pool. Cha/me cua con do user chon tuong
 *   minh, khong suy tu vo/chong.
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

// N3: MỘT nhãn duy nhất cho người chưa có tên ở mọi vị trí sơ đồ.
const EMPTY_PERSON_NAME = '(chưa có tên)';
const CASE_TYPE_LABELS = { inheritance: 'Thừa kế', two_party: 'Hai bên' };

// Thong diep loi than thien tu error-catalog (MIN-136) — fallback raw
// khi module chua nap (node --test nap tung file doc lap).
const relErrText = (typeof window !== 'undefined' && window.G1_NOTARY_ERRORS)
  ? window.G1_NOTARY_ERRORS.errText
  : (e) => (e && (e.message || e.code)) || 'Lỗi';
const relIsDiagramError =
  (typeof window !== 'undefined' && window.G1_NOTARY_ERRORS &&
   typeof window.G1_NOTARY_ERRORS.isDiagramError === 'function')
    ? window.G1_NOTARY_ERRORS.isDiagramError
    : () => true;

// Kich thuoc layout canvas (px logic — scale boi zoom, khong co chu).
// MIN-133 D7 / WP6: node DA THA 144×87 (ten 14px, nam 13px, 2 hang chip 22×19);
// node TRONG 88×24 vien dut, hien nhan vai tro (Chu dat, Cha, Me, Vo/chong, Con, Con cua <ten>).
// Le 6px, giua the he 14px (plan 12–16), giua node 14px, cap vo/chong
// 28px. CSS .cd-node/.cd-node-empty phai khop cac hang nay.
const NODE_W = 144, NODE_H = 87;
const EMPTY_W = 88, EMPTY_H = 24;
const PAD = 6, GAP_X = 14, SPOUSE_GAP = 28, GAP_Y = 14;
const ROW_H = NODE_H + GAP_Y;          // buoc toi da giua 2 hang the he
// Hai ben: 2 cot × 15 cho; do thuc te truoc thay doi 288×26 → ap
// rong−30% (202) / cao+100% (52); CSS .cd-tp-slot phai khop hang so.
const TP_COL_W = 202, TP_SLOT_H = 52, TP_SLOT_GAP = 4, TP_TITLE_H = 26;
const TP_W = PAD * 2 + TP_COL_W * 2 + 12;
const TP_H = PAD * 2 + TP_TITLE_H + 15 * TP_SLOT_H + 14 * TP_SLOT_GAP;
const ZOOM_MIN = 0.5, ZOOM_MAX = 1.6;

// Nhan hien thi cho slot id canonical seed (chi label — khong luat).
const SLOT_LABEL = {
  owner: 'Chủ đất', father: 'Cha', mother: 'Mẹ',
  spouse: 'Vợ/chồng', spouse_father: 'Cha vợ/chồng',
  spouse_mother: 'Mẹ vợ/chồng',
};

// Nhan trang thai tinh — dung chung cho panel "Xem cach tinh" va cue
// chi-doc khi panel dong (cung mot nguon render_model).
const CALC_STATUS_LABEL = {
  complete: 'Hoàn chỉnh', incomplete: 'Chưa đủ điều kiện',
  invalid: 'Không hợp lệ', unsupported: 'Chưa hỗ trợ',
};
const INCOMPLETE_ERROR_CODES = new Set([
  'missing_land_owner', 'invalid_death_date',
]);

function displayCalcStatus(renderModel) {
  if (renderModel.status === 'invalid' &&
      Array.isArray(renderModel.errors) && renderModel.errors.length &&
      renderModel.errors.every((error) =>
        INCOMPLETE_ERROR_CODES.has(error && error.code))) {
    return 'incomplete';
  }
  return renderModel.status;
}
const RELATIONSHIP_ROLE_LABEL = {
  grandparent: 'ông/bà nội/ngoại',
  sibling: 'anh/chị/em ruột',
  grandchild: 'cháu ruột (người để lại là ông/bà)',
  great_grandparent: 'cụ nội/ngoại',
  parent_sibling: 'bác/chú/cậu/cô/dì ruột',
  sibling_child: 'cháu ruột (người để lại là bác/chú/cậu/cô/dì)',
  great_grandchild: 'chắt ruột',
};

// So cho canonical cua node two_party (p16 = dau Ben B); null neu khong
// phai id canonical.
function slotNum(id) {
  const m = /^p(\d+)$/.exec(id || '');
  return m ? Number(m[1]) : null;
}

// Layout the he tu chu dat (owner) — WP6: moi the he mot hang tinh tu chu dat:
// cha me hang -1, chu dat + vo/chong hang 0, con hang +1, chau +2, chat +3.
// Trong mot gen: vo/chong cung hang ngay canh partner, o du phong vo/chong cuoi.
// Con sap xep theo ngay sinh (unknown cuoi, on dinh), o con du phong cuoi.
// Tra {pos: {id:{x,y,w,h,gen}}, w, h} — vi tri TOP-LEFT tren world logic.
function parseBirthKey(raw) {
  if (raw == null) return null;
  if (typeof raw === 'number') return `${raw}-00-00`;
  if (typeof raw !== 'string') return null;
  const s = raw.trim();
  if (!s) return null;
  const dmy = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);
  if (dmy) {
    return `${dmy[3]}-${dmy[2].padStart(2, '0')}-${dmy[1].padStart(2, '0')}`;
  }
  const ymd = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
  if (ymd) {
    return `${ymd[1]}-${ymd[2].padStart(2, '0')}-${ymd[3].padStart(2, '0')}`;
  }
  const y = /^(\d{4})$/.exec(s);
  if (y) return `${y[1]}-00-00`;
  const m = /(\d{4})/.exec(s);
  if (m) return `${m[1]}-00-00`;
  return null;
}

function nodeSize(n) {
  return n && n.personId ? { w: NODE_W, h: NODE_H }
                         : { w: EMPTY_W, h: EMPTY_H };
}

function layoutInheritance(nodes, people = []) {
  const live = (nodes || []).filter((n) => n && !n.deleted);
  if (!live.length) return { pos: {}, w: PAD * 2, h: PAD * 2 };
  const byId = new Map(live.map((n) => [n.id, n]));
  const personById = new Map(
    (Array.isArray(people) ? people : Object.values(people || {}))
      .filter(Boolean)
      .map((p) => [p.row_id || p.id, p])
  );

  // 1. Tinh the he theo chu dat (owner = 0, cha/me = -1, con = +1, chau = +2, chat = +3)
  const ownerNode = byId.get('owner') || live[0];
  const genMap = new Map();
  genMap.set(ownerNode.id, 0);

  const adj = new Map();
  for (const n of live) adj.set(n.id, []);

  for (const n of live) {
    const spouseIds = new Set([
      ...(n.spouseSlotIds || []),
      ...(n.spouseSlotId ? [n.spouseSlotId] : []),
    ]);
    for (const sid of spouseIds) {
      if (byId.has(sid)) {
        adj.get(n.id).push({ to: sid, diff: 0 });
        adj.get(sid).push({ to: n.id, diff: 0 });
      }
    }
    for (const pid of n.parentSlotIds || []) {
      if (byId.has(pid)) {
        adj.get(n.id).push({ to: pid, diff: -1 });
        adj.get(pid).push({ to: n.id, diff: +1 });
      }
    }
  }

  const queue = [ownerNode.id];
  const visited = new Set([ownerNode.id]);
  while (queue.length > 0) {
    const curr = queue.shift();
    const currGen = genMap.get(curr);
    for (const edge of adj.get(curr) || []) {
      if (!visited.has(edge.to)) {
        visited.add(edge.to);
        genMap.set(edge.to, currGen + edge.diff);
        queue.push(edge.to);
      }
    }
  }

  for (const n of live) {
    if (!visited.has(n.id)) {
      let baseGen = 0;
      for (const edge of adj.get(n.id) || []) {
        if (visited.has(edge.to)) {
          baseGen = genMap.get(edge.to) - edge.diff;
          break;
        }
      }
      genMap.set(n.id, baseGen);
      visited.add(n.id);
      const subQueue = [n.id];
      while (subQueue.length > 0) {
        const c = subQueue.shift();
        const cg = genMap.get(c);
        for (const edge of adj.get(c) || []) {
          if (!visited.has(edge.to)) {
            visited.add(edge.to);
            genMap.set(edge.to, cg + edge.diff);
            subQueue.push(edge.to);
          }
        }
      }
    }
  }

  const gens = new Map();
  for (const n of live) {
    const g = genMap.get(n.id) ?? 0;
    if (!gens.has(g)) gens.set(g, []);
    gens.get(g).push(n);
  }
  const size = new Map(live.map((n) => [n.id, nodeSize(n)]));
  // Khoi: partner va cac vo/chong ke nhau (sat 28px).
  const blocksOf = (row, gen) => {
    const rowIds = new Set(row.map((n) => n.id));
    const spouseOf = new Map();
    const spousesByPartner = new Map();

    for (const n of row) {
      const spIds = [
        ...(n.spouseSlotIds || []),
        ...(n.spouseSlotId ? [n.spouseSlotId] : []),
      ].filter((sid) => rowIds.has(sid) && sid !== n.id);

      if (spIds.length > 0) {
        if (!spousesByPartner.has(n.id)) spousesByPartner.set(n.id, []);
        for (const sid of spIds) {
          const spouse = byId.get(sid);
          if (spouse && !spouseOf.has(sid)) {
            spouseOf.set(sid, n.id);
            spousesByPartner.get(n.id).push(spouse);
          }
        }
      }
    }

    const units = [];
    const seen = new Set();
    for (const n of row) {
      if (seen.has(n.id) || spouseOf.has(n.id)) continue;
      seen.add(n.id);
      const group = [n];
      const partnerSpouses = spousesByPartner.get(n.id) || [];
      // WP6: vo/chong canh partner, o du phong vo/chong cuoi
      const occupied = partnerSpouses.filter((s) => s.personId);
      const spare = partnerSpouses.filter((s) => !s.personId);
      for (const s of [...occupied, ...spare]) {
        seen.add(s.id);
        group.push(s);
      }
      units.push(group);
    }
    for (const n of row) {
      if (!seen.has(n.id)) {
        seen.add(n.id);
        units.push([n]);
      }
    }

    // WP6: con theo ngay sinh (unknown cuoi, on dinh), o con du phong cuoi
    if (gen >= 1) {
      units.sort((a, b) => {
        const na = a[0], nb = b[0];
        const aParents = (na.parentSlotIds || []).slice().sort().join(',');
        const bParents = (nb.parentSlotIds || []).slice().sort().join(',');
        if (aParents !== bParents) {
          return aParents.localeCompare(bParents);
        }
        const aIsSpare = !na.personId;
        const bIsSpare = !nb.personId;
        if (aIsSpare && !bIsSpare) return 1;
        if (!aIsSpare && bIsSpare) return -1;
        if (aIsSpare && bIsSpare) return 0;

        const pa = personById.get(na.personId) || na.person;
        const pb = personById.get(nb.personId) || nb.person;
        const ka = parseBirthKey(pa?.ngay_sinh);
        const kb = parseBirthKey(pb?.ngay_sinh);
        if (ka && kb) {
          if (ka < kb) return -1;
          if (ka > kb) return 1;
          return 0;
        }
        if (ka && !kb) return -1;
        if (!ka && kb) return 1;
        return 0;
      });
    }

    return units.map((m) => ({
      m,
      w: m.reduce((s, n) => s + size.get(n.id).w, 0) + (m.length - 1) * SPOUSE_GAP,
    }));
  };
  const gkeys = [...gens.keys()].sort((a, b) => a - b);
  const rows = gkeys.map((g) => blocksOf(gens.get(g), g));
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

function spouseOwnerOf(nodeId, nodes) {
  return (nodes || []).find((n) => !n.deleted &&
    (n.spouseSlotIds || []).includes(nodeId)) || null;
}

// WP6: nhãn vai trò ô trống (Chủ đất, Cha, Mẹ, Vợ/chồng, Con, 'Con của <tên>' thế vị)
function emptySlotRole(n, live = [], people = []) {
  if (!n) return 'Ô trống';
  if (n.id === 'owner') return 'Chủ đất';
  const nodes = (live && live.length) ? live : [];
  const owner = nodes.find((k) => k && k.id === 'owner');

  // Vợ/chồng
  const spOwner = spouseOwnerOf(n.id, nodes);
  if (spOwner || nodes.some((k) => k && ((k.spouseSlotIds || []).includes(n.id) || k.spouseSlotId === n.id))) {
    return 'Vợ/chồng';
  }

  // Cha / Mẹ của chủ đất
  if (owner && (owner.parentSlotIds || []).includes(n.id)) {
    const idx = owner.parentSlotIds.indexOf(n.id);
    if (idx === 0 || n.id === 'father' || n.role === 'father') return 'Cha';
    if (idx === 1 || n.id === 'mother' || n.role === 'mother') return 'Mẹ';
  }
  if (n.id === 'father' || n.role === 'father') return 'Cha';
  if (n.id === 'mother' || n.role === 'mother') return 'Mẹ';

  // Con / Con của <tên> (thế vị)
  const parents = (n.parentSlotIds || []).map((id) => nodes.find((k) => k && k.id === id)).filter(Boolean);
  if (parents.length > 0) {
    if (parents.some((p) => p.id === 'owner')) {
      return 'Con';
    }
    const anchor = parents[0];
    let anchorName = '';
    const pList = Array.isArray(people) ? people : Object.values(people || {});
    if (anchor && anchor.personId) {
      const p = pList.find((x) => x && (x.row_id === anchor.personId || x.id === anchor.personId));
      if (p && p.ho_ten) anchorName = p.ho_ten;
    }
    if (!anchorName && anchor) {
      anchorName = anchor.ho_ten || anchor.id;
    }
    return anchorName ? `Con của ${anchorName}` : 'Con';
  }
  if (/^child(?:_|$)/.test(n.id || '') || n.role === 'child') return 'Con';
  return SLOT_LABEL[n.id] || n.id || 'Ô trống';
}
const REMOVAL_NOTIFY_KEY = 'notary.diagram.notify_on_remove';
const _memStorage = new Map();

function isRemovalNotifyEnabled() {
  try {
    const raw = (typeof window !== 'undefined' && window.localStorage)
      ? window.localStorage.getItem(REMOVAL_NOTIFY_KEY)
      : (typeof localStorage !== 'undefined'
        ? localStorage.getItem(REMOVAL_NOTIFY_KEY)
        : _memStorage.get(REMOVAL_NOTIFY_KEY));
    if (raw === '0' || raw === 'false') return false;
    return true;
  } catch (_) {
    return true;
  }
}

function setRemovalNotifyEnabled(enabled) {
  const val = enabled ? '1' : '0';
  _memStorage.set(REMOVAL_NOTIFY_KEY, val);
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(REMOVAL_NOTIFY_KEY, val);
    } else if (typeof localStorage !== 'undefined') {
      localStorage.setItem(REMOVAL_NOTIFY_KEY, val);
    }
  } catch (_) {}
}


function createDiagramPane(ctx) {
  const model = ctx.model;
  const L = ctx.lib;
  const notify = ctx.notify || (() => {});
  const h = ctx.h;
  const btn = ctx.btn;
  const face = ctx.face;
  const openModal = ctx.openModal;
  const actionStatus = ctx.actionStatus ||
    { run: (sel, root, task) => task(), sync: () => {}, isBusy: () => false };
  const errText = ctx.errText || relErrText;
  const uiRoot = () => (ctx.uiRoot ? ctx.uiRoot()
    : (typeof document !== 'undefined' ? document : null));
  const openWordDialog = ctx.openWordDialog || (() => {});
  const openConversionDialog = ctx.openConversionDialog || (() => {});
  // Luu ho so tat ca qua coordinator view (flush editor truoc snapshot);
  // fallback model.saveCase cho test thuan pane khong co view.
  const onSaveCase = ctx.onSaveCase ||
    (() => (typeof model.saveCase === 'function' ? model.saveCase() : null));
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
  // Refresh hẹp phần quan hệ khi view hoãn rebuild vì Stage input đang
  // focus — không dựng lại editor Stage/ô đang gõ.
  let currentCard = null;
  let currentDiagramRegion = null;
  let currentSaveBtn = null;
  let currentRenderPool = null;

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
    model.subscribe(() => {
      if (model.state.status === 'loading' && evalTimer) {
        clearTimeout(evalTimer);
        evalTimer = null;
      }
      if (expandBody) rebuildExpand();
    });
  }

  // Stage dirty (case da ton tai): evaluate chay tren buffer dang sua
  // (payload draft), nen khong con gate bat luu truoc.

  function isTp() {
    return model.diagramDomain && model.diagramDomain() === TWO_PARTY;
  }


  async function runEvaluate() {
    return model.evaluateDiagram();
  }

  function personRow(rowId) {
    // Mọi case: nhãn/năm/hint đọc Stage đang sửa — cùng nguồn với bảng
    // Người, không chờ lần ghi trung gian.
    return (model.state.stage.people || [])
      .find((x) => x.row_id === rowId) || null;
  }

  function personName(rowId) {
    const p = personRow(rowId);
    return p ? (p.ho_ten || EMPTY_PERSON_NAME) : '—';
  }

  // N5: còn sống chỉ hiện năm sinh; có năm mất hiện "sinh – mất".
  // Bỏ dấu "…" lửng của dạng cũ.
  function yearOf(v) {
    const m = /\d{4}/.exec(v || '');
    return m ? m[0] : null;
  }

  function personYears(rowId) {
    const p = personRow(rowId);
    if (!p) return null;
    const b = yearOf(p.ngay_sinh), d = yearOf(p.ngay_chet);
    if (d) return b ? `${b} – ${d}` : d;
    return b || null;
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
    if (/^child(?:_|$)/.test(n.id || '')) {
      const m = /^child_(\d+)$/.exec(n.id || '');
      return m ? `Con ${m[1]}` : 'Con';
    }
    if (/^[a-z]+_[a-z]+$/.test(n.id || '')) return 'Ô trống';
    return n.id || 'Ô trống';
  }
  // Ten ngan de tham chieu slot: ten nguoi neu da gan, nhan slot neu
  // trong.
  function refName(n) {
    if (!n) return '—';
    if (n.personId) return personName(n.personId);
    return SLOT_LABEL[n.id] || slotTag(n);
  }

  // Vai tro hien thi tu quan he draft da khai bao — presentation only,
  // KHONG suy luan nghiep vu (khong phan biet cha vs me — engine cung
  // khong: parentSlotIds la tap cha/me).
  function roleLabel(n) {
    if (n.id === 'owner') return 'Chủ đất';
    const sp = nodeById(n.spouseSlotId) ||
      liveNodes().find((k) => k.spouseSlotId === n.id);
    if (sp) return `vợ/chồng của ${refName(sp)}`;
    const kids = liveNodes().filter(
      (k) => (k.parentSlotIds || []).includes(n.id));
    if (kids.length) {
      const names = kids.slice(0, 2).map(refName).join(', ');
      return `cha/mẹ của ${names}${kids.length > 2 ? '…' : ''}`;
    }
    const owner = spouseOwnerOf(n.id, liveNodes());
    const ownerPerson = owner && owner.personId
      ? personRow(owner.personId) : null;
    if (owner && (!ownerPerson || ownerPerson.ngay_chet)) {
      return `vợ/chồng của ${refName(owner)}`;
    }
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

  // MIN-136: Pool chi con nguoi — tai san khong xuong (khong co flow
  // gan len node). Card = ten + grip keo + nut → menu gan vi tri.
  function poolCardEl(row, sub) {
    const card = h('div', 'cd-pool-card');
    const canDrag = model.canWrite();
    card.draggable = canDrag;
    const label = row.ho_ten || EMPTY_PERSON_NAME;
    const setPayload = (e) => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain',
        JSON.stringify({ kind: 'person', row_id: row.row_id }));
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
    // Pool rong chi con ten) — van trong tab order.
    const assign = btn('→', 'sm cd-pool-assign',
      () => openAssignMenu(row));
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

  function poolMatch(row, q) {
    if (!q) return true;
    const label = [row.ho_ten, row.so_giay_to, row.ngay_sinh]
      .filter(Boolean).join(' ').toLowerCase();
    return label.includes(q);
  }

  // ---------- Menu "Gán vị trí" (ban phim thay cho keo-tha) ----------

  // Menu chi gan/doi cho tren cac o hien co; tao quan he o menu rieng
  // cua tung nguoi, khong tao ho so Stage.
  function openAssignMenu(row) {
    openModal((box, close) => {
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title',
        `Gán vị trí — ${row.ho_ten || EMPTY_PERSON_NAME}`));
      const x = h('button', 'modal-close', '×');
      x.type = 'button';
      x.setAttribute('aria-label', 'Đóng');
      x.onclick = close;
      head.append(x);
      box.append(head);
      const body = h('div', 'modal-body cd-field-stack');
      const nodes = liveNodes();
      const assign = (nodeId) => () => {
        // movePerson bao trum ca move vao cho trong LAN swap khi cho
        // da co nguoi — cung semantics voi keo-tha (§13.5 Q9).
        model.movePerson(row.row_id, nodeId);
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
        if (!nodes.length) {
          body.append(h('div', 'muted',
            'Sơ đồ chưa có ô — khôi phục ô khởi tạo trên canvas trước.'));
        }
      }
      box.append(body);
      const foot = h('div', 'modal-foot');
      foot.append(btn('Đóng', '', close));
      box.append(foot);
    }, { bare: true });
  }


  // ---------- Diagram ----------

  // Drop target chung: nhan pool card hoac node co nguoi keo vao —
  // movePerson bao trum move/swap (§13.5 Q9) cho ca hai domain.
  function wirePersonDrop(el, nodeId) {
    el.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
      el.classList.add('drop-hint');
    });
    el.addEventListener('dragleave', () =>
      el.classList.remove('drop-hint'));
    el.addEventListener('drop', (e) => {
      e.preventDefault();
      el.classList.remove('drop-hint');
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person') model.movePerson(d.row_id, nodeId);
      } catch (err) { /* payload rac — bo qua */ }
    });
  }


  let activeUndoToast = null;

  function dismissActiveToast() {
    if (activeUndoToast) {
      activeUndoToast.dismiss();
      activeUndoToast = null;
    }
  }

  function showUndoToast(count, onUndo) {
    dismissActiveToast();
    let box = typeof document?.getElementById === 'function'
      ? document.getElementById('toast')
      : (typeof document?.querySelector === 'function' ? document.querySelector('#toast') : null);
    if (!box) {
      box = h('div', 'toast-root');
      box.id = 'toast';
      const target = document.body || (typeof uiRoot === 'function' ? uiRoot() : null);
      if (target) target.append(box);
    }
    const item = h('div', 'toast toast-undo');
    item.setAttribute('role', 'status');
    const msg = h('span', 'toast-text', `Đã đưa ${count} người về Pool`);
    const sep = h('span', 'toast-sep', ' · ');
    const undoBtn = btn('Hoàn tác', 'toast-action js-toast-undo', () => {
      dismissActiveToast();
      onUndo();
    });
    undoBtn.setAttribute('aria-label', 'Hoàn tác');
    item.append(msg, sep, undoBtn);
    box.append(item);
    const timer = setTimeout(() => {
      if (activeUndoToast && activeUndoToast.el === item) {
        item.remove();
        activeUndoToast = null;
      }
    }, 5000);
    activeUndoToast = {
      el: item,
      dismiss() {
        clearTimeout(timer);
        item.remove();
      },
    };
    return activeUndoToast;
  }

  async function handleCardRemoval(personId) {
    if (!model.canWrite() || !personId) return;
    const res = await model.removeCard(personId);
    if (!res || !res.ok) return;
    if (res.cascadeOthers.length > 0 && isRemovalNotifyEnabled()) {
      showUndoToast(res.cascadeOthers.length, () => {
        model.restoreDraftSnapshot(res.snapshot);
      });
    }
    return res;
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
    const spouseOwner = spouseOwnerOf(n.id, liveNodes());
    const spouseIndex = spouseOwner
      ? spouseOwner.spouseSlotIds.indexOf(n.id) : -1;
    const spouseLawful = !!(spouseOwner &&
      spouseIndex === spouseOwner.spouseSlotIds.length - 1);
    if (spouseOwner) {
      card.classList.add(spouseLawful
        ? 'cd-node-spouse-lawful' : 'cd-node-spouse-faded');
    }

    if (!n.personId) {
      // WP6: node TRONG 88×24 vien dut, hien nhan vai tro (Chu dat, Cha, Me, Vo/chong, Con, Con cua <ten>).
      card.classList.add('cd-node-empty');
      const what = emptySlotRole(n, liveNodes(), model.state.stage?.people);
      const label = `Ô trống: ${what}${role ? ` (${role})` : ''}`;
      card.setAttribute('aria-label', label);
      card.title = label;
      const nm = h('span', 'cd-empty-label', what);
      card.append(nm);
      wirePersonDrop(card, n.id);
      return card;
    }

    const name = (p && p.ho_ten) || EMPTY_PERSON_NAME;
    card.setAttribute('aria-label', role ? `${name} — ${role}` : name);
    if (role) card.title = role;
    const nm = h('span', 'cd-node-name', name);
    nm.title = role ? `${name} — ${role}` : name;
    card.append(nm);
    if ((model.state.renderModel?.warnings || []).some((warning) =>
      warning.code === 'missing_death_date' && warning.personId === n.personId)) {
      card.append(h('div', 'cd-badge cd-badge-warn', 'thiếu ngày mất'));
    }
    if (spouseOwner) {
      const text = spouseLawful ? 'Vợ/chồng hợp pháp'
        : 'Không phải vợ/chồng hợp pháp';
      card.append(h('div', 'cd-spouse-label', text));
    }
    if (!ro) {
      // Ban phim: gan lai/doi cho cho nguoi dang o node (menu du nang
      // luc nhu keo-tha — move/swap) + bo gan ve Pool.
      const acts = h('div', 'cd-node-acts');
      const mv = btn('→', 'cd-mini-btn', () => openAssignMenu(p, 'person'));
      mv.title = 'Gán lại/đổi chỗ (bàn phím — thay cho kéo thả)';
      mv.setAttribute('aria-label', `Gán lại ${name}`);
      mv.disabled = !model.state.capabilities.diagram;
      const un = btn('↩', 'cd-mini-btn js-node-unassign js-card-remove', () =>
        handleCardRemoval(n.personId)
      );
      un.title = 'Bỏ gán — trả người về Pool';
      un.setAttribute('aria-label', `Bỏ gán ${name} về Pool`);
      acts.append(mv, un);
      card.append(acts);
    }
    const meta = h('div', 'cd-node-meta');
    meta.append(h('span', '', personYears(n.personId) || '—'));
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
      for (const pos of window.G1_NOTARY_MODEL.POSITIONS) {
        const on = Array.isArray(arr) && arr.includes(pos);
        const chip = btn(`${pos}`,
          `cd-poschip${on ? ' on' : ''}`, () => {
            model.toggleNodePosition(n.id, kind, pos);
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
        e.dataTransfer.effectAllowed = 'move';
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
      const nm = h('span', 'cd-tp-nm', p.ho_ten || EMPTY_PERSON_NAME);
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
        model.movePerson(n.personId, null);
      });
      del.title = `Bỏ ${p.ho_ten || ''} khỏi chỗ ${num} (về Pool)`;
      del.setAttribute('aria-label', `Bỏ khỏi chỗ ${num}`);
      del.disabled = ro;
      acts.append(mv, del);
      slot.append(acts);
      if (!ro) {
        slot.draggable = true;
        slot.addEventListener('dragstart', (e) => {
          e.dataTransfer.effectAllowed = 'move';
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
      const label = `Chỗ ${num} trống`;
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
    const nodes = (model.state.diagram.nodes || []).filter((n) => !n.deleted);
    const lay = layoutInheritance(nodes, model.state.stage?.people);
    scale.append(edgesSvgEl(nodes, lay.pos, lay.w, lay.h));
    for (const n of nodes) {
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
      wrap.append(face(L.faceEmpty('Sơ đồ trống.')));
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
  // parentSlotIds/spouseSlotIds draft — khong suy luan. Kich thuoc lay
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
      ((a.spouseSlotIds || []).includes(b.id) ||
       (b.spouseSlotIds || []).includes(a.id)));
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
      // Draw each one-way spouse link exactly once.
      for (const spouseId of n.spouseSlotIds || []) {
        if (!pos[spouseId]) continue;
        const key = [n.id, spouseId].sort().join('|');
        if (drawn.has(key)) continue;
        drawn.add(key);
        const seg = spouseSeg(n.id, spouseId);
        if (seg) edgePath(`M${seg.x1} ${seg.y} H${seg.x2}`,
          'cd-edge-spouse');
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
      box.append(face(L.faceEmpty('Chưa có kết quả tính.')));
      return box;
    }
    const status = displayCalcStatus(rm);
    const statusLabel = CALC_STATUS_LABEL[status] || status;
    box.append(h('div', 'cd-calc-status',
      `Trạng thái tính: ${statusLabel}`));
    if (status === 'unsupported') {
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
    // viaBranchPersonIds?, heirRank?, relationshipRoles?}]}.
    // JS chi doc field engine emit, KHONG tinh/format lai so.
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
          if (t.heirRank === 2 || t.heirRank === 3) {
            bits.push(`hàng ${t.heirRank}`);
            const roles = (t.relationshipRoles || [])
              .map((code) => RELATIONSHIP_ROLE_LABEL[code] || code);
            if (roles.length) bits.push(roles.join(', '));
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

  // ---------- Pool pane (Stage đang sửa) + tier ----------

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
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
      box.classList.add('drop-hint');
    });
    box.addEventListener('dragleave', () =>
      box.classList.remove('drop-hint'));
    box.addEventListener('drop', (e) => {
      e.preventDefault();
      box.classList.remove('drop-hint');
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person' && d.row_id) {
          if (isTp()) model.movePerson(d.row_id, null);
          else handleCardRemoval(d.row_id);
        }
      } catch (err) { /* bo qua */ }
    });
    pane.append(box);

    function renderPool() {
      box.innerHTML = '';
      const poolPeople = model.pool().people;
      title.textContent = `Pool (${poolPeople.length})`;
      const pp = poolPeople.filter((r) => poolMatch(r, poolQuery));
      if (!(model.state.stage.people || []).length) {
        box.append(face(L.faceEmpty('Chưa có người.')));
        return;
      }
      if (!pp.length) {
        box.append(face(L.faceEmpty(
          poolQuery ? 'Không khớp bộ lọc.' : 'Pool trống.')));
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
        box.append(poolCardEl(p, sub));
      }
    }
    renderPool();
    currentRenderPool = renderPool;
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
    // R13: slot lỗi dành sẵn — lỗi sơ đồ hiện đúng một dòng tại đây,
    // không toast/banner trùng; slot luôn chiếm chỗ nên canvas và các
    // vùng khác không nhảy khi lỗi xuất hiện/biến mất.
    const errSlot = h('div', 'cd-diagram-errslot');
    extra.append(errSlot);
    // MIN-136: chu dat DA GAN nhung chua co ngay mat → engine khong
    // spawn nhanh (dung nghiep vu — thua ke chi phat sinh khi co nguoi
    // chet). Hint user dien Ngay mat o bang Nguoi; evaluate tu chay lai
    // va requiredSlots sinh cac o (cha/me, vo/chong, con).
    if (!isTp()) {
      const owner = nodeById('owner');
      const ownerPerson = owner && owner.personId
        ? personRow(owner.personId) : null;
      if (ownerPerson && !ownerPerson.ngay_chet) {
        extra.append(h('div', 'cd-hint',
          'Người để lại chưa có ngày mất — điền cột “Ngày mất” ở bảng ' +
          'Người để sơ đồ sinh các nhánh thừa kế.'));
      }
    }
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
    // Cue chi-doc khi panel "Xem cach tinh" dong: trang thai + cho engine
    // yeu cau (requiredSlots) + loi engine — hien ngay sau save/mo lai
    // tu render_model da luu. KHONG mutate draft, KHONG goi evaluate;
    // slot chi sinh khi user bam "Xem cach tinh" (MIN-136).
    if (!isTp() && !calcOpen && s.renderModel) {
      const rm = s.renderModel;
      // Trạng thái chỉ-đọc cho mọi kết quả engine đã lưu (kể cả complete)
      // — §9.6; không mutate draft, không gọi evaluate.
      const status = displayCalcStatus(rm);
      if (CALC_STATUS_LABEL[status]) {
        extra.append(h('div', 'muted warn-text',
          `Trạng thái tính: ${CALC_STATUS_LABEL[status]}`));
      }
      for (const req of rm.requiredSlots || []) {
        const anchor = nodeById(req.anchorSlotId);
        const kinds = (req.slotTypes || [])
          .map((t) => SLOT_LABEL[t] || (t === 'child' ? 'Con' : t))
          .join(', ');
        if (!kinds) continue;
        extra.append(h('div', 'muted warn-text',
          `Cần bổ sung ${kinds} cho ô “${anchor ? slotTag(anchor)
            : req.anchorSlotId}” — bấm “Xem cách tính” để sinh ô.`));
      }
      // Loi engine cua render_model da luu; save vua bi tu choi da co
      // diagramErrors rieng nen khong lap lai.
      if (status === 'invalid' && !(s.diagramErrors || []).length) {
        for (const e of rm.errors || []) {
          errSlot.append(h('div', 'error small', errText(e)));
        }
      }
    }
    for (const er of s.diagramErrors || []) {
      errSlot.append(h('div', 'error small', errText(er)));
    }
    // Lỗi do evaluate/gọi sơ đồ đặt vào state.error (model chỉ giữ MỘT
    // kênh lỗi mỗi lần) — hiện tại đây, không lặp ở card Stage.
    if (s.error && relIsDiagramError(s.error.code) &&
        !(s.diagramErrors || []).length) {
      errSlot.append(h('div', 'error small', errText(s.error)));
    }
    if (calcOpen) extra.append(calcPanelEl());
    dg.append(extra);
    return dg;
  }

  function syncSaveButton() {
    if (!currentSaveBtn) return;
    const s = model.state;
    const dirty = s.stageDirty || s.diagramDirty || s.metaDirty;
    const dot = currentSaveBtn.querySelector('.dirty-dot');
    if (dirty && !dot) currentSaveBtn.append(h('span', 'dirty-dot', ''));
    if (!dirty && dot) dot.remove();
    currentSaveBtn.disabled = model.isWriteBusy() ||
      !s.capabilities.diagram || !model.canWrite();
    if (dirty) {
      currentSaveBtn.setAttribute('aria-label',
        'Lưu hồ sơ — có thay đổi chưa lưu');
    } else {
      currentSaveBtn.removeAttribute('aria-label');
    }
  }

  // Refresh hẹp phần quan hệ (Pool + canvas/nhãn/hint/lỗi + nút Lưu hồ
  // sơ) trên card hiện có. Dùng khi view hoãn rebuild vì Stage input
  // đang focus: editor Stage/caret/value không bị dựng lại.
  function refresh() {
    if (!currentCard || currentCard.isConnected === false) return false;
    if (currentRenderPool) currentRenderPool();
    const oldWrap = currentDiagramRegion &&
      currentDiagramRegion.querySelector('.cd-canvas-wrap');
    const scroll = oldWrap
      ? { top: oldWrap.scrollTop, left: oldWrap.scrollLeft } : null;
    const next = diagramRegionEl();
    if (currentDiagramRegion && currentDiagramRegion.isConnected) {
      currentDiagramRegion.replaceWith(next);
    }
    currentDiagramRegion = next;
    if (scroll) {
      const wrap = next.querySelector('.cd-canvas-wrap');
      if (wrap) { wrap.scrollTop = scroll.top; wrap.scrollLeft = scroll.left; }
    }
    syncSaveButton();
    return true;
  }

  function build() {
    const s = model.state;
    const tp = isTp();
    const card = h('div', 'card cd-rel-card');

    // Head: title + chọn loại sơ đồ + tools nho (cach tinh, danh gia —
    // chi domain inheritance co engine; zoom + Mo rong cho ca hai).
    const head = h('div', 'card-head');
    head.append(h('h3', 'card-title',
      tp ? 'Sơ đồ hai bên' : 'Sơ đồ thừa kế'));
    // R7: MỘT vị trí + MỘT dạng UI cho cả hồ sơ mới và hồ sơ cũ.
    // Nháp → đổi loại trực tiếp trên buffer; hồ sơ đã lưu → mở luồng
    // convert hiện có (chọn văn bản mới/người để lại/xác nhận xóa sơ đồ).
    const typeSel = h('select', 'cd-case-type cd-diagram-type');
    for (const [v, lbl] of Object.entries(CASE_TYPE_LABELS)) {
      const o = h('option', '', lbl);
      o.value = v;
      typeSel.append(o);
    }
    const currentType =
      (s.caseInfo && s.caseInfo.case_type) || 'inheritance';
    typeSel.value = currentType;
    typeSel.setAttribute('aria-label', 'Loại sơ đồ');
    typeSel.dataset.fid = 'diagram:case_type';
    typeSel.disabled = !model.canWrite() || !!s.busy || !!s.conflict ||
      s.stale || s.unsupported;
    typeSel.onchange = () => {
      const cur = (model.state.caseInfo &&
        model.state.caseInfo.case_type) || 'inheritance';
      const next = typeSel.value;
      if (next === cur) return;
      if (model.state.caseId == null) {
        model.updateCaseMeta('case_type', next);
        return;
      }
      typeSel.value = cur;             // dialog quyết định thay đổi
      openConversionDialog(next);
    };
    head.append(typeSel);
    const tools = h('div', 'card-tools');
    if (!tp) {
      // MIN-136: chi giu "Xem cach tinh" — bo + Slot va Danh gia thu
      // (evaluate van tu chay qua scheduleEvaluate + khi mo panel).
      const calc = btn('Xem cách tính', 'sm js-calc-eval', async () => {
        calcOpen = !calcOpen;
        if (!calcOpen) { rerender(); return; }
        // rerender TRONG task: nút được dựng lại trước khi action-status
        // đóng dấu tích, nên tích xanh nằm trên node đang hiển thị.
        await actionStatus.run('.js-calc-eval', uiRoot(),
          () => runEvaluate().then((r) => { rerender(); return r; }),
          { ok: (r) => !!(r && r.ok) });
      });
      calc.disabled = !s.capabilities.diagram;
      tools.append(calc);
      // Badge stale: stage revision da vuot lan evaluate cuoi cua draft.
      const staleEval = s.evaluatedRevision != null &&
        s.evaluatedRevision !== s.revision;
      if (staleEval) {
        tools.append(h('span', 'pill warn',
          'Stage đã đổi kể từ lần đánh giá'));
      }
    }
    tools.append(zoomClusterEl());
    const expand = btn('⛶ Mở rộng', 'sm', () => openExpanded());
    expand.setAttribute('aria-label', 'Mở rộng sơ đồ toàn màn');
    expand.title = 'Xem sơ đồ ở cửa sổ lớn gần toàn màn hình';
    tools.append(expand);
    if (!tp) {
      const toggleWrap = h('label', 'cd-toggle-setting');
      toggleWrap.title = 'Thông báo và cho phép hoàn tác khi gỡ thẻ làm người khác bị đưa về Pool';
      const toggle = h('input', 'cd-toggle-checkbox js-toggle-notify-on-remove');
      toggle.type = 'checkbox';
      toggle.checked = isRemovalNotifyEnabled();
      toggle.setAttribute('aria-label', 'Thông báo khi gỡ');
      toggle.onchange = () => {
        setRemovalNotifyEnabled(toggle.checked);
      };
      toggleWrap.append(toggle, h('span', 'cd-toggle-label', 'Thông báo khi gỡ'));
      tools.append(toggleWrap);
    }
    // Nút "Lưu hồ sơ" gọi coordinator view → flush editor rồi
    // model.saveCase (workspace_save_case: Stage+meta+Diagram, done).
    // Không disable vì caseId=null, Diagram sạch hay stageDirty; chỉ
    // khóa khi đang có lệnh GHI (save/convert/duplicate/update), thiếu
    // capability hoặc không workspace. Lệnh đọc (evaluate) không khóa.
    tools.append(h('span', 'cd-vsep', ''));
    const save = btn('Lưu hồ sơ', 'sm secondary js-save-diagram', async () => {
      // View coordinator đã flush + báo lỗi qua kênh notify hiện có.
      await onSaveCase();
    });
    currentSaveBtn = save;
    save.dataset.label = 'Lưu hồ sơ';
    // Dot + aria/disabled theo đúng một nguồn (dirty live cả khi rebuild).
    syncSaveButton();
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
    const region = diagramRegionEl();
    currentDiagramRegion = region;
    body.append(region);
    card.append(body);
    currentCard = card;
    return card;
  }

  return {
    build,
    refresh,
    removeCard: handleCardRemoval,
    isRemovalNotifyEnabled,
    setRemovalNotifyEnabled,
  };
}

const G1_NOTARY_DIAGRAM = {
  createDiagramPane,
  isRemovalNotifyEnabled,
  setRemovalNotifyEnabled,
  REMOVAL_NOTIFY_KEY,
  // Export cho test thuan: layout thua ke + so cho canonical —
  // pure functions, khong can DOM/model.
  _internals: { layoutInheritance, emptySlotRole, slotNum, NODE_W, NODE_H, PAD,
                ROW_H, GAP_X, ZOOM_MIN, ZOOM_MAX },
};

if (typeof window !== 'undefined') window.G1_NOTARY_DIAGRAM = G1_NOTARY_DIAGRAM;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_DIAGRAM;
}
