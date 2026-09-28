// MIN-133 mockup — dữ liệu giả + dựng bảng/sơ đồ + đo tràn.
// Chỉ phục vụ ảnh duyệt; không phải runtime.

const ASSET_ROWS = [
  ['so_serial', 'Số serial'],
  ['so_vao_so', 'Số vào sổ'],
  ['so_thua_dat', 'Thửa đất'],
  ['so_to_ban_do', 'Tờ bản đồ'],
  ['land', 'Loại đất'],
  ['dia_chi', 'Địa chỉ'],
  ['loai_so', 'Loại sổ'],
  ['hinh_thuc_su_dung', 'Hình thức sử dụng'],
  ['thoi_han', 'Thời hạn'],
  ['nguon_goc', 'Nguồn gốc'],
  ['ngay_cap', 'Ngày cấp'],
  ['co_quan_cap', 'Cơ quan cấp'],
];
const ASSETS = [
  { so_serial: 'CS 123456', so_vao_so: 'CS01234', so_thua_dat: '125', so_to_ban_do: '12', land: 2,
    dia_chi: 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An', loai_so: 'Sổ hồng',
    hinh_thuc_su_dung: 'Sử dụng riêng', thoi_han: 'Lâu dài',
    nguon_goc: 'Nhà nước giao đất có thu tiền', ngay_cap: '15/10/2013', co_quan_cap: 'UBND huyện Đức Hòa' },
  { so_serial: 'CS 067890', so_vao_so: 'CS05678', so_thua_dat: '208', so_to_ban_do: '15', land: 1,
    dia_chi: 'Ấp Bình Tả, xã Đức Hòa Hạ, huyện Đức Hòa, tỉnh Long An', loai_so: 'Sổ đỏ',
    hinh_thuc_su_dung: 'Sử dụng riêng', thoi_han: '15/10/2043',
    nguon_goc: 'Công nhận QSDĐ', ngay_cap: '22/03/2004', co_quan_cap: 'UBND huyện Đức Hòa' },
  { so_serial: 'CS 024681', so_vao_so: 'CS09876', so_thua_dat: '316', so_to_ban_do: '22', land: 3,
    dia_chi: 'Khu phố 4, thị trấn Hậu Nghĩa, huyện Đức Hòa, tỉnh Long An', loai_so: 'Sổ hồng',
    hinh_thuc_su_dung: 'Sử dụng chung', thoi_han: 'Lâu dài',
    nguon_goc: 'Nhận chuyển nhượng', ngay_cap: '08/07/2018', co_quan_cap: 'Sở TN&MT tỉnh Long An' },
];

// 7 cột = cột DB Customer (bỏ Nơi cấp, Nguyên quán)
const PERSON_COLS = [
  ['ho_ten', 'Họ tên'],
  ['gioi_tinh', 'Giới tính'],
  ['ngay_sinh', 'Ngày sinh'],
  ['ngay_chet', 'Ngày mất'],
  ['so_giay_to', 'Số giấy tờ'],
  ['ngay_cap', 'Ngày cấp'],
  ['dia_chi', 'Địa chỉ'],
];
const PEOPLE = [
  { id: 1, ho_ten: 'Nguyễn Văn An', gioi_tinh: 'Nam', ngay_sinh: '12/03/1955', ngay_chet: '08/06/2021',
    so_giay_to: '080055000123', ngay_cap: '20/05/2016', dia_chi: 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An' },
  { id: 2, ho_ten: 'Trần Thị Lan', gioi_tinh: 'Nữ', ngay_sinh: '20/10/1960', ngay_chet: '',
    so_giay_to: '080160000456', ngay_cap: '11/08/2021', dia_chi: 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An' },
  { id: 3, ho_ten: 'Nguyễn Minh Đức', gioi_tinh: 'Nam', ngay_sinh: '25/07/1982', ngay_chet: '',
    so_giay_to: '080082001234', ngay_cap: '03/01/2022', dia_chi: '123 Lê Lợi, P. Bến Thành, Quận 1, TP. Hồ Chí Minh' },
  { id: 4, ho_ten: 'Nguyễn Thị Hoàng Phương Thảo', gioi_tinh: 'Nữ', ngay_sinh: '14/11/1985', ngay_chet: '',
    so_giay_to: '080185002345', ngay_cap: '15/09/2021', dia_chi: 'Khu phố 4, TT. Hậu Nghĩa, huyện Đức Hòa, tỉnh Long An' },
  { id: 5, ho_ten: 'Nguyễn Hoàng Nam', gioi_tinh: 'Nam', ngay_sinh: '03/02/1990', ngay_chet: '',
    so_giay_to: '080090003456', ngay_cap: '27/12/2021', dia_chi: 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An' },
  { id: 6, ho_ten: 'Nguyễn Gia Bảo', gioi_tinh: 'Nam', ngay_sinh: '19/06/1993', ngay_chet: '',
    so_giay_to: '080093004567', ngay_cap: '02/04/2022', dia_chi: '45 Trần Phú, P.4, Quận 5, TP. Hồ Chí Minh' },
  { id: 7, ho_ten: 'Nguyễn Thị Mai', gioi_tinh: 'Nữ', ngay_sinh: '30/09/1996', ngay_chet: '',
    so_giay_to: '080196005678', ngay_cap: '18/10/2022', dia_chi: 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An' },
];
const OWNER_ID = 1;
const POOL = [6, 7];

function h(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
function cellInput(val, placeholder) {
  const i = h('input', 'cell-in');
  i.value = val || '';
  i.placeholder = placeholder || '';
  if (val) i.title = val;
  return i;
}

// ---------- Tài sản: bảng chuyển vị (hàng = trường, cột = tài sản) ----------
function buildAssets() {
  const t = h('table', 'grid cd-tbl');
  const cg = h('colgroup');
  const c0 = h('col'); c0.style.width = 'var(--asset-label-w, 122px)'; cg.append(c0);
  ASSETS.forEach(() => cg.append(h('col')));
  t.append(cg);
  const thead = h('thead');
  const trh = h('tr');
  trh.append(h('th', 'cd-rowlabel', 'Thuộc tính'));
  ASSETS.forEach((a, i) => {
    const th = h('th', 'cd-asset-col');
    const head = h('div', 'cd-col-head');
    head.append(h('span', 'drag-handle', '⠿'), h('span', 'grow', `Tài sản ${i + 1}`), h('span', 'icon-x', '×'));
    th.append(head);
    trh.append(th);
  });
  thead.append(trh); t.append(thead);
  const tb = h('tbody');
  for (const [k, label] of ASSET_ROWS) {
    const r = h('tr');
    r.append(h('td', 'cd-rowlabel', label));
    ASSETS.forEach((a) => {
      const td = h('td');
      if (k === 'land') {
        td.append(h('span', 'cd-chip-link', `${a.land} loại ↗`));
      } else {
        td.append(cellInput(a[k]));
      }
      r.append(td);
    });
    tb.append(r);
  }
  t.append(tb);
  document.getElementById('asset-table').append(t);
}

// ---------- Người: hàng = người, cột = 7 trường Customer ----------
function buildPeople() {
  const t = h('table', 'grid cd-ptbl');
  const widths = ['20px', '44px', 'var(--col-name, 214px)', '64px', 'var(--col-date, 86px)', 'var(--col-date, 86px)',
    'var(--col-id, 106px)', 'var(--col-date, 86px)', '', '24px'];
  const cg = h('colgroup');
  widths.forEach((w) => { const c = h('col'); if (w) c.style.width = w; cg.append(c); });
  t.append(cg);
  const thead = h('thead');
  const trh = h('tr');
  trh.append(h('th', 'cd-drag-col', ''));
  trh.append(h('th', 'cd-owner-col', 'Để lại'));
  for (const [, label] of PERSON_COLS) trh.append(h('th', '', label));
  trh.append(h('th', 'cd-drag-col', ''));
  thead.append(trh); t.append(thead);
  const tb = h('tbody');
  for (const p of PEOPLE) {
    const r = h('tr', p.id === OWNER_ID ? 'row-owner' : '');
    const tdh = h('td', 'cd-drag-col'); tdh.append(h('span', 'drag-handle', '⠿')); r.append(tdh);
    const tdo = h('td', 'cd-owner-cell' + (p.id === OWNER_ID ? ' cd-owner-on' : ''));
    const rb = h('input'); rb.type = 'radio'; rb.name = 'cd-owner-row'; rb.checked = p.id === OWNER_ID;
    tdo.append(rb); r.append(tdo);
    for (const [k] of PERSON_COLS) {
      const td = h('td');
      if (k === 'gioi_tinh') {
        const s = h('select', 'cell-in');
        for (const o of ['—', 'Nam', 'Nữ']) { const op = h('option', '', o); op.selected = o === p[k]; s.append(op); }
        td.append(s);
      } else {
        const inp = cellInput(p[k], k === 'ngay_chet' ? '—' : '');
        td.append(inp);
      }
      r.append(td);
    }
    const tdx = h('td', 'cd-drag-col'); tdx.append(h('span', 'icon-x', '×')); r.append(tdx);
    tb.append(r);
  }
  t.append(tb);
  document.getElementById('people-table').append(t);
}

// ---------- Pool ----------
function buildPool() {
  const box = document.getElementById('pool');
  for (const id of POOL) {
    const p = PEOPLE.find((x) => x.id === id);
    const c = h('div', 'cd-pool-card');
    c.draggable = true;
    c.append(h('span', 'drag-handle', '⠿'), h('span', 'cd-pool-nm', p.ho_ten));
    c.title = p.ho_ten;
    box.append(c);
  }
}

// ---------- Sơ đồ thừa kế ----------
// own/recv = vị trí tài sản 1..3 được bật chip
const NODES = {
  f:    { empty: true },                       // cha của người để lại (chưa thả)
  m:    { empty: true },                       // mẹ của người để lại (chưa thả)
  an:   { pid: 1, years: '1955 – 2021', own: [1, 2, 3], recv: [], owner: true },
  lan:  { pid: 2, years: '1960 – …', own: [1], recv: [2] },
  duc:  { pid: 3, years: '1982 – …', own: [], recv: [1] },
  thao: { pid: 4, years: '1985 – …', own: [], recv: [2] },
  nam:  { pid: 5, years: '1990 – …', own: [], recv: [3] },
  c4:   { empty: true },                       // slot con còn trống
};

function nodeEl(n) {
  if (n.empty) {
    const e = h('div', 'cd-node cd-node-empty');
    e.title = 'Ô trống — thả người từ Pool';
    return e;
  }
  const p = PEOPLE.find((x) => x.id === n.pid);
  const e = h('div', 'cd-node' + (n.owner ? ' cd-node-owner' : ''));
  e.draggable = true;
  const nm = h('span', 'cd-node-name', p.ho_ten); nm.title = p.ho_ten;
  e.append(nm, h('div', 'cd-node-meta', n.years));
  e.append(h('span', 'icon-x hover', '×'));
  for (const [label, arr] of [['Chủ', n.own], ['Nhận', n.recv]]) {
    const row = h('div', 'cd-posrow');
    row.append(h('span', 'cd-posrow-label', label));
    for (const k of [1, 2, 3]) row.append(h('span', 'cd-poschip' + (arr.includes(k) ? ' on' : ''), String(k)));
    e.append(row);
  }
  return e;
}

function buildDiagram() {
  const cv = document.getElementById('canvas');
  const svg = document.getElementById('edges');
  const els = {};
  for (const [id, n] of Object.entries(NODES)) { els[id] = nodeEl(n); cv.append(els[id]); }
  const W = cv.clientWidth;
  const nw = els.an.offsetWidth, nh = els.an.offsetHeight;
  const ew = els.f.offsetWidth, eh = els.f.offsetHeight;
  const PAD = 6, VG0 = 12, VG1 = 16, HG = 14, SP = 28;
  const cx = Math.round(W / 2);
  const place = (id, x, y) => { els[id].style.left = x + 'px'; els[id].style.top = y + 'px'; return { x, y, w: els[id].offsetWidth, h: els[id].offsetHeight }; };
  const P = {};
  // gen1: cặp người để lại + vợ/chồng, căn giữa
  const y1 = PAD + eh + VG0;
  P.an = place('an', cx - SP / 2 - nw, y1);
  P.lan = place('lan', cx + SP / 2, y1);
  // gen0: 2 ô trống cha/mẹ trên người để lại
  const anC = P.an.x + nw / 2;
  P.f = place('f', anC - ew - 6, PAD);
  P.m = place('m', anC + 6, PAD);
  // gen2: con
  const y2 = y1 + nh + VG1;
  const kids = ['duc', 'thao', 'nam', 'c4'];
  const kw = kids.reduce((s, k) => s + els[k].offsetWidth, 0) + HG * (kids.length - 1);
  let x = cx - kw / 2;
  for (const k of kids) { P[k] = place(k, Math.round(x), y2); x += els[k].offsetWidth + HG; }

  const paths = [];
  // cha/mẹ → người để lại
  const jy = PAD + eh + VG0 / 2;
  paths.push(`M${P.f.x + ew / 2} ${PAD + eh} V${jy} H${P.m.x + ew / 2} V${PAD + eh}`);
  paths.push(`M${anC} ${jy} V${y1}`);
  // vợ/chồng
  const sy = y1 + nh / 2;
  paths.push({ d: `M${P.an.x + nw} ${sy} H${P.lan.x}`, cls: 'spouse' });
  // cặp → con
  const by = y2 - VG1 / 2;
  paths.push(`M${cx} ${sy} V${by}`);
  paths.push(`M${P.duc.x + P.duc.w / 2} ${by} H${P.c4.x + P.c4.w / 2}`);
  for (const k of kids) paths.push(`M${P[k].x + P[k].w / 2} ${by} V${y2}`);
  svg.setAttribute('width', W); svg.setAttribute('height', y2 + nh + PAD);
  svg.innerHTML = paths.map((p) => typeof p === 'string'
    ? `<path d="${p}"/>` : `<path class="${p.cls}" d="${p.d}"/>`).join('');
  return { treeBottom: y2 + nh + PAD, canvasH: cv.clientHeight, nodeW: nw, nodeH: nh, emptyW: ew, emptyH: eh };
}

// ---------- đo tràn ----------
function measure(diag) {
  const over = (el) => ({ h: el.scrollHeight - el.clientHeight, w: el.scrollWidth - el.clientWidth });
  const m = { viewport: `${innerWidth}x${innerHeight}` };
  m.page = over(document.getElementById('view'));
  m.body = over(document.documentElement);
  m.assetsBody = over(document.querySelector('.cd-assets .cd-stage-body'));
  m.peopleBody = over(document.querySelector('.cd-people .cd-stage-body'));
  m.canvas = over(document.getElementById('canvas'));
  m.diagram = diag;
  m.stageH = document.querySelector('.cd-stage').offsetHeight;
  m.relH = document.querySelector('.cd-rel-card').offsetHeight;
  m.assetsW = document.querySelector('.cd-assets').offsetWidth;
  m.peopleW = document.querySelector('.cd-people').offsetWidth;
  m.truncated = [];
  const nn = document.querySelectorAll('.cd-node-name'); m.nodeNameBox = [...nn].map((s) => [s.clientWidth, s.scrollWidth]);
  document.querySelectorAll('.cell-in').forEach((i) => {
    if (i.tagName === 'INPUT' && i.scrollWidth > i.clientWidth + 1) m.truncated.push(i.value);
  });
  document.querySelectorAll('.cd-node-name,.cd-pool-nm').forEach((s) => {
    if (s.scrollWidth > s.clientWidth + 1) m.truncated.push('node/pool: ' + s.textContent);
  });
  m.peopleCols = [...document.querySelectorAll('.cd-ptbl thead th')].map((th) => th.offsetWidth);
  m.assetCols = [...document.querySelectorAll('.cd-tbl thead th')].map((th) => th.offsetWidth);
  const cx = document.createElement('canvas').getContext('2d');
  const tw = (font, t) => { cx.font = font; return Math.ceil(cx.measureText(t).width); };
  m.textW = {
    thao14: tw('14px "Segoe UI"', 'Nguyễn Thị Hoàng Phương Thảo'),
    nam600: tw('600 14px "Segoe UI"', 'Nguyễn Hoàng Nam'),
    nam400: tw('14px "Segoe UI"', 'Nguyễn Hoàng Nam'),
    duc600: tw('600 14px "Segoe UI"', 'Nguyễn Minh Đức'),
    addr14: tw('14px "Segoe UI"', 'Ấp 3, xã Tân Phú, huyện Đức Hòa, tỉnh Long An'),
    date14: tw('14px "Segoe UI"', '12/03/1955'),
    id14: tw('14px "Segoe UI"', '080055000123'),
  };
  const out = JSON.stringify(m);
  document.getElementById('metrics').textContent = out;
  document.title = 'M:' + out;
  console.log(out);
}

// Tỷ lệ theo bề rộng: màn lớn nới cột, màn nhỏ siết (không thu chữ).
function tune() {
  const r = document.documentElement.style;
  const w = innerWidth;
  if (w <= 1400) {
    r.setProperty('--assets-w', '35%');
    r.setProperty('--asset-label-w', '122px');
    r.setProperty('--col-name', '200px');
    r.setProperty('--col-date', '84px');
    r.setProperty('--col-id', '102px');
  } else if (w >= 1800) {
    r.setProperty('--assets-w', '38%');
    r.setProperty('--asset-label-w', '140px');
    r.setProperty('--col-name', '230px');
    r.setProperty('--col-date', '100px');
    r.setProperty('--col-id', '120px');
  }
}

tune();
buildAssets();
buildPeople();
buildPool();
document.fonts.ready.then(() => {
  const d = buildDiagram();
  // mô phỏng trạng thái focus 1 ô cho thấy ô nhập tại chỗ
  measure(d);
});
