// Static invariants cho workspace Soạn hồ sơ (MIN-111):
// - model pure (khong DOM), UMD
// - view khong co Zalo / React / ReactFlow / Bootstrap / raw JSON render /
//   input ID ky thuat trong production path
// - css co vung bam >=44px + focus-visible
// - index.html nap dung scripts/css; renderer co dirty-leave guard
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const R = (p) => fs.readFileSync(path.join(HERE, '..', p), 'utf8');

const MODEL = 'src/renderer/notary/case-drafting-model.js';
const VIEW = 'src/renderer/notary/case-drafting-view.js';
const CSS = 'src/renderer/notary/case-drafting.css';
const INTAKE = 'src/renderer/notary/intake-dialog.js';
const DIAGRAM = 'src/renderer/notary/relationship-diagram.js';
const WORD = 'src/renderer/notary/word-export-dialog.js';

const modelSrc = R(MODEL);
const viewSrc = R(VIEW);
const cssSrc = R(CSS);
const htmlSrc = R('src/renderer/index.html');
const rendererSrc = R('src/renderer/renderer.js');
const stylesSrc = R('src/renderer/styles.css');
const ipcSrc = R('src/main/ipc.js');
const mainSrc = R('src/main/main.js');
const preloadSrc = R('src/preload/preload.js');

// Bo comment khoi source truoc khi check chuoi cam (comment duoc nhac den
// tu khoa nhu "Khong Zalo" ma khong vi pham).
function stripComments(src) {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/[^\n]*/g, '$1');
}

const viewCode = stripComments(viewSrc);
const rendererCode = stripComments(rendererSrc);
const modelCode = stripComments(modelSrc);

test('model pure: khong DOM API, UMD export ca window + module', () => {
  assert.ok(!/document\.(createElement|querySelector|getElementById|body)/
    .test(modelCode), 'model dung DOM');
  assert.match(modelSrc, /window\.G1_NOTARY_MODEL/);
  assert.match(modelSrc, /module\.exports/);
});

test('model nhan client inject, khong goi desktop api truc tiep', () => {
  assert.match(modelSrc, /deps\.client\.run|client\.run\(/);
  assert.ok(!/window\.desktop|desktop\.v1/.test(modelCode));
});

test('view khong co Zalo engine / React / ReactFlow / Bootstrap', () => {
  // MIN-129: nut "Zalo" placeholder duoc phep (visible + disabled) —
  // cam la ENGINE/flow Zalo, khong phai label nut.
  for (const bad of ['zaloEngine', 'ZALO', 'zalo-intake', 'zaloIntake',
                     'zalo.status', 'zaloSec', 'openZalo', 'zaloDialog',
                     'zalo_document', 'React', 'react', 'ReactFlow',
                     'reactflow', 'Bootstrap', 'bootstrap',
                     'jsx', 'createElementNS']) {
    assert.ok(!viewCode.includes(bad), `view chua "${bad}"`);
  }
  // Zalo placeholder phai ton tai + disabled (khong duoc an nut).
  assert.match(viewCode, /zalo\.disabled\s*=\s*true/);
  // css cung khong import framework ngoai
  assert.ok(!/@import|bootstrap|tailwind/i.test(cssSrc));
});

test('view khong render raw JSON cho user', () => {
  // JSON.stringify chi duoc dung cho payload keo-tha (dataTransfer),
  // khong duoc di vao textContent/innerHTML/append.
  const uses = [...viewCode.matchAll(/JSON\.stringify/g)].map((m) => m.index);
  for (const i of uses) {
    const ctx = viewCode.slice(Math.max(0, i - 120), i + 80);
    assert.match(ctx, /dataTransfer|setData/,
      'JSON.stringify ngoai ngu canh drag payload');
  }
});

test('production view khong co input ID ky thuat — chi o devQuickOpen', () => {
  // Moi input nhap id ho so phai nam trong block dev (G1_DEV guard).
  const devBlock = viewCode.match(
    /function devQuickOpen[\s\S]*?return box;\s*\}/);
  assert.ok(devBlock, 'thieu devQuickOpen block');
  const outside = viewCode.replace(devBlock[0], '');
  assert.ok(!/id hồ sơ|id_ho_so|case_id.*input|input.*case_id/i.test(outside),
    'input ID ky thuat nam ngoai dev block');
  // dev block phai bi gate boi isDevMode
  assert.match(viewCode, /isDevMode\(\)\)/);
});

test('view co keyboard/menu alternative cho gan vi tri tren so do', () => {
  // MIN-112: relation tier tach sang relationship-diagram.js — keyboard
  // alternative "Gán vị trí" nam trong pane do.
  const comb = viewCode + '\n' + stripComments(R(DIAGRAM));
  assert.match(comb, /Gán vị trí/);            // nut menu thay the keo-tha
  assert.match(comb, /openAssignMenu/);
});

test('view co banner mock "Dữ liệu mô phỏng" + a11y attributes', () => {
  // Text banner o model (MOCK_BANNER), view render qua model.mockBanner()
  assert.match(modelSrc, /Dữ liệu mô phỏng/);
  assert.match(viewCode, /mockBanner\(\)/);
  assert.match(viewCode, /aria-label|setAttribute\('aria/);
  assert.match(viewCode, /role=|setAttribute\('role'/);
});

test('css: token P4 + scope .cd-root/cd-*, khong re-khai shared', () => {
  // MIN-129: module css dung tokens styles.css (P4) — khong tu :root moi.
  assert.ok(!/(^|\n)\s*:root/.test(cssSrc), 'module redefine :root');
  assert.match(cssSrc, /var\(--(accent|fs-base|border-hairline|surface-card|btn-h|row-h|text-muted)\)/);
  assert.match(cssSrc, /\.cd-root/);
  // focus ring van duoc override chu dong o local nav.
  assert.match(cssSrc, /:focus-visible/);
  // Khong re-khai class shared khong prefix o top-level selector
  // (.card/.btn/.input/.modal/.pill/.face/.drop-hint/.drag-handle...) —
  // override phai nam duoi .cd-root hoac dung ten cd-*.
  const bad = cssSrc.split('\n')
    .map((l) => l.trim())
    .filter((l) => /^\.(card|card-head|card-title|card-tools|card-body|btn|input|modal|modal-overlay|modal-head|modal-body|modal-foot|modal-title|modal-close|toolbar|actionbar|face|pill|banner|grid|drag-handle|dragging|drop-hint|row-drop-above|row-drop-below|col-drop-before|icon-x|dirty-dot|warn-text|muted|small|error|grow|spacer|save-state|pool-card|pool-box)\b/.test(l));
  assert.deepEqual(bad, [],
    `re-khai shared class khong prefix: ${bad.join(' | ')}`);
});

test('styles.css: focus-visible + control 44px toan cuc', () => {
  assert.match(stylesSrc, /:focus-visible/);
  assert.match(stylesSrc, /min-height:\s*44px/);
});

test('index.html nap model + view + css cua case drafting', () => {
  assert.match(htmlSrc, /notary\/case-drafting\.css/);
  assert.match(htmlSrc, /notary\/case-drafting-model\.js/);
  assert.match(htmlSrc, /notary\/case-drafting-view\.js/);
  // load truoc renderer.js (model/view la global cho renderer dung)
  const iModel = htmlSrc.indexOf('case-drafting-model.js');
  const iRend = htmlSrc.indexOf('renderer.js');
  assert.ok(iModel > -1 && iModel < iRend,
    'case-drafting-model.js phai load truoc renderer.js');
});

test('renderer co dirty-leave guard cho module notary', () => {
  assert.match(rendererCode, /canLeave/);
  assert.match(rendererCode, /hasUnsaved/);
  assert.match(rendererCode, /G1_NOTARY_MODEL\.createModel/);
  assert.match(rendererCode, /G1_NOTARY_VIEW\.createNotaryModuleView/);
});

test('renderer khong con view Zalo / id input cu', () => {
  for (const bad of ['zalo.status', 'zaloSec', 'buildDocReviewView']) {
    assert.ok(!rendererCode.includes(bad), `renderer con "${bad}"`);
  }
});

// ---------- MIN-112: opaque file token + dialog files ----------

test('MIN-112: intake/diagram/word dialog files ton tai + load truoc renderer.js', () => {
  for (const f of [INTAKE, DIAGRAM, WORD]) {
    assert.ok(fs.existsSync(path.join(HERE, '..', f)), `thieu ${f}`);
  }
  const iRend = htmlSrc.indexOf('renderer.js');
  for (const s of ['notary/intake-dialog.js', 'notary/relationship-diagram.js',
                   'notary/word-export-dialog.js']) {
    const i = htmlSrc.indexOf(s);
    assert.ok(i > -1 && i < iRend, `${s} phai load truoc renderer.js`);
  }
});

test('MIN-112: renderer khong gui path trong command payload — chi file_token', () => {
  // Opaque token: moi file_ref/destination/folder/file trong payload di qua
  // {file_token}; main resolve. Renderer code khong duoc con "{ path: ... }".
  const files = [
    ['renderer', rendererCode], ['view', viewCode],
    ['intake-dialog', R(INTAKE)], ['word-dialog', R(WORD)],
    ['relationship-diagram', R(DIAGRAM)],
  ];
  for (const [name, src0] of files) {
    const src = stripComments(src0);
    assert.ok(!/\bpath\s*:/.test(src),
      `${name} con literal "path:" — renderer khong duoc gui path`);
  }
  // intake + word dung file_token
  assert.match(stripComments(R(INTAKE)), /file_token/);
  assert.match(stripComments(R(WORD)), /file_token/);
});

test('MIN-112: main.js pickFiles cap opaque token, khong tra path cho renderer', () => {
  // pickFiles map qua store issue — body ham khong tra "path" literal.
  assert.match(mainSrc, /fileTokens/);
  const pf = stripComments(mainSrc)
    .match(/function pickFiles[\s\S]*?\n\}/);
  assert.ok(pf, 'thieu pickFiles trong main.js');
  assert.ok(!/\bpath\s*:/.test(pf[0]),
    'pickFiles tra path cho renderer — phai chi tra file_token');
});

test('MIN-112: preload expose registerDroppedFile + setDirtyState; drop qua webUtils', () => {
  assert.match(preloadSrc, /registerDroppedFile/);
  assert.match(preloadSrc, /setDirtyState/);
  assert.match(preloadSrc, /webUtils|getPathForFile/);
  // khong fallback doc file.path trong preload (forge duoc)
  assert.ok(!/file\.path\b/.test(preloadSrc),
    'preload khong duoc doc file.path (forge path)');
});

test('MIN-112: ipc co token resolution + handler moi', () => {
  assert.match(ipcSrc, /resolveFileTokens/);
  assert.match(ipcSrc, /desktop\.v1\.registerDroppedFile/);
  assert.match(ipcSrc, /desktop\.v1\.setDirtyState/);
  assert.match(ipcSrc, /file_token/);
});

test('MIN-112: window close guard doc dirty flag renderer (main.js)', () => {
  assert.match(mainSrc, /rendererDirty|setDirty/);
  assert.match(mainSrc, /fileTokens\.clear\(\)/);
});

test('MIN-112: debounce evaluate sau khi draft diagram doi', () => {
  const comb = viewCode + '\n' + stripComments(R(DIAGRAM));
  assert.match(comb, /evaluateDiagram/);
  assert.match(comb, /setTimeout\(|debounce/i);
});

// ---------- MIN-112 review fixes ----------

test('MIN-112r: Xem cach tinh render breakdowns[] (khong con explanations dead code)', () => {
  const diag = stripComments(R(DIAGRAM));
  assert.match(diag, /rm\.breakdowns/);           // field that §7.2
  assert.match(diag, /bd\.terms|\.terms\b/);      // terms[] verbatim
  assert.ok(!/rm\.explanations|rm\.explanation\b/.test(diag),
    'con dead code doc rm.explanations — field khong ton tai');
});

test('MIN-112r: openPath co whitelist extension trong main.js', () => {
  assert.match(mainSrc, /openPathBlockReason|OPEN_PATH_EXTS/);
  assert.ok(
    fs.existsSync(path.join(HERE, '..', 'src/main/open-path.js')),
    'thieu open-path.js (whitelist ext dung chung main+ipc)');
});

test('MIN-112r: confirmModal co role dialog + aria-modal + Escape', () => {
  const mm = rendererCode.match(
    /function confirmModal[\s\S]*?\n\}/);
  assert.ok(mm, 'thieu confirmModal');
  assert.match(mm[0], /role', 'dialog'/);
  assert.match(mm[0], /aria-modal/);
  assert.match(mm[0], /Escape/);
});

// ---------- MIN-128: v2 wire invariants ----------

test('MIN-128: renderer KHONG emit field v1 bi cam (is_primary/isLandOwner/willReceive)', () => {
  // §13.14: producer v2 khong emit cac field nay o bat ky level nao.
  // Check sau khi strip comment — keyword trong comment thi khong sao.
  for (const [name, code] of [
      ['model', modelCode], ['view', viewCode],
      ['diagram', stripComments(R(DIAGRAM))],
      ['word-dialog', stripComments(R(WORD))],
      ['intake-dialog', stripComments(R(INTAKE))]]) {
    for (const bad of ['is_primary', 'isLandOwner', 'willReceive']) {
      assert.ok(!code.includes(bad), `${name} con field v1 "${bad}"`);
    }
  }
});

test('MIN-128: model co v2 contracts — version 3, owner_row_id, positions, two_party', () => {
  assert.match(modelSrc, /DIAGRAM_VERSION\s*=\s*3\b/);
  assert.match(modelSrc, /owner_row_id/);
  assert.match(modelSrc, /ownPositions/);
  assert.match(modelSrc, /receivePositions/);
  assert.match(modelSrc, /two_party/);
  assert.match(modelSrc, /MAX_ASSETS\s*=\s*3\b/);
  assert.match(modelSrc, /MAX_PEOPLE_TWO_PARTY\s*=\s*30\b/);
  assert.match(modelSrc, /case_type/);
});

test('MIN-128: diagram co position chips + two_party groups; khong co +Slot arbitrary tren two_party', () => {
  const diag = R(DIAGRAM);
  assert.match(diag, /ownPositions|toggleNodePosition/);
  assert.match(diag, /receivePositions/);
  assert.match(diag, /two_party/);
  assert.match(diag, /Bên A|Bên B|p1|p16/);
});

test('MIN-128: view co owner selector + case type badge + position display', () => {
  const v = R(VIEW);
  assert.match(v, /owner_row_id/);
  assert.match(v, /case_type/);
  assert.match(v, /two_party/);
});

// ---------- MIN-133 W2: thanh trên + Stage (mockup đã duyệt 28/09) ----------

// Lấy khối rule theo selector đầu dòng (chỉ top-level, đủ cho CSS phẳng).
function cssRule(src, selector) {
  const esc = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const m = src.match(new RegExp(`(^|\\n)${esc}\\s*\\{([^}]*)\\}`));
  return m ? m[2] : null;
}

test('MIN-133 D8: Stage không thanh cuộn — bỏ max-height/overflow cuộn/min-width cột', () => {
  const body = cssRule(cssSrc, '.cd-stage-body');
  assert.ok(body !== null, 'thiếu rule .cd-stage-body');
  assert.ok(!/max-height/.test(body), '.cd-stage-body còn max-height');
  assert.ok(!/overflow\s*:\s*(auto|scroll)/.test(body),
    '.cd-stage-body còn overflow cuộn');
  const wrap = cssRule(cssSrc, '.cd-table-wrap');
  assert.ok(wrap !== null, 'thiếu rule .cd-table-wrap');
  assert.ok(!/overflow\s*:\s*(auto|scroll)/.test(wrap),
    '.cd-table-wrap còn cuộn');
  // Phần Stage (layout tổng → hết Stage) không còn overflow cuộn, không
  // min-width cho ô/cột, không sticky cột nhãn.
  const start = cssSrc.indexOf('layout tổng (MIN-133 D8)');
  const end = cssSrc.indexOf('land-types dialog');
  assert.ok(start > -1 && end > start, 'không tìm thấy vùng CSS Stage');
  const stage = cssSrc.slice(start, end)
    .replace(/\.cd-caselist\s*\{[^}]*\}/, '');   // danh sách Tổng quan
  assert.ok(!/overflow\s*:\s*(auto|scroll)/.test(stage),
    'vùng Stage/thanh trên còn overflow cuộn');
  assert.ok(!/min-width\s*:\s*(1[01]\d|17\d)px/.test(stage),
    'còn min-width cột/ô cũ (110/118/176px)');
  assert.ok(!/position\s*:\s*sticky/.test(stage), 'còn sticky cột nhãn');
});

test('MIN-133: bảng Stage table-layout fixed + colgroup theo mockup', () => {
  assert.match(cssSrc, /table\.cd-stage-tbl\s*\{[^}]*table-layout\s*:\s*fixed/);
  assert.match(cssSrc, /col\.cd-acol-label\s*\{\s*width:\s*var\(--cd-asset-label-w\)/);
  assert.match(cssSrc, /--cd-asset-label-w:\s*122px/);
  assert.match(cssSrc, /col\.cd-pcol-drag\s*\{\s*width:\s*20px/);
  assert.match(cssSrc, /col\.cd-pcol-owner\s*\{\s*width:\s*44px/);
  assert.match(cssSrc, /--cd-col-name:\s*214px/);
  assert.match(cssSrc, /col\.cd-pcol-gioi_tinh\s*\{\s*width:\s*64px/);
  assert.match(cssSrc, /--cd-col-date:\s*86px/);
  assert.match(cssSrc, /--cd-col-id:\s*106px/);
  assert.match(cssSrc, /col\.cd-pcol-del\s*\{\s*width:\s*24px/);
  // Địa chỉ = phần còn lại: không có width cố định.
  assert.ok(!/col\.cd-pcol-dia_chi\s*\{/.test(cssSrc));
  // Tài sản : Người = 35 : 65 (38 : 62 ở màn ≥1800).
  assert.match(cssSrc, /--cd-assets-w:\s*35%/);
  assert.match(cssSrc, /min-width:\s*1800px\)[\s\S]*?--cd-assets-w:\s*38%/);
  assert.match(cssSrc, /\.cd-assets\s*\{[^}]*flex:\s*0 0 var\(--cd-assets-w\)/);
  // Hàng 25px, dữ liệu 14px, nhãn 13px; ô nhập không nền, cắt "…".
  assert.match(cssSrc, /--cd-row-h:\s*25px/);
  assert.match(cssSrc, /--cd-fs-data:\s*var\(--fs-data,\s*14px\)/);
  const cell = cssSrc.match(/\.cd-stage-tbl \.cd-cell\s*\{([^}]*)\}/);
  assert.ok(cell, 'thiếu rule .cd-cell');
  assert.match(cell[1], /background:\s*transparent/);
  assert.match(cell[1], /border:\s*1px solid transparent/);
  assert.match(cell[1], /text-overflow:\s*ellipsis/);
  assert.match(cssSrc, /\.cd-cell:focus\s*\{[^}]*border-color:\s*var\(--accent\)/);
});

test('MIN-133 D5: thanh trên 42px; select Loại việc rộng ≥128px', () => {
  const bar = cssRule(cssSrc, '.cd-topbar');
  assert.ok(bar, 'thiếu rule .cd-topbar');
  assert.match(bar, /height:\s*42px/);
  const sel = cssSrc.match(/\.cd-root \.cd-case-type\s*\{([^}]*)\}/);
  assert.ok(sel, 'thiếu rule .cd-root .cd-case-type');
  const mw = sel[1].match(/min-width:\s*(\d+)px/);
  assert.ok(mw && Number(mw[1]) >= 128, 'select loại việc < 128px');
  assert.ok(!/actionbar|ab-back|ab-title|save-state/.test(cssSrc),
    'CSS còn rule actionbar/back/title/save-state cũ');
});

test('MIN-133 D8: layout flex dọc — vùng sơ đồ lấp phần còn lại, có min-height', () => {
  assert.match(cssSrc, /\.cd-root-outer\s*\{[^}]*flex-direction:\s*column[^}]*min-height:\s*100%/);
  const rel = cssSrc.match(/\.cd-workspace > \.cd-rel-card\s*\{([^}]*)\}/);
  assert.ok(rel, 'thiếu rule lớp ngoài .cd-rel-card');
  assert.match(rel[1], /flex:\s*1 0 auto/);
  assert.match(rel[1], /min-height:\s*\d+px/);
  // min-height (không height) để Stage cao thì cả trang cuộn.
  assert.ok(!/\.cd-root\s*\{[^}]*[\s;]height:\s*100%/.test(cssSrc));
});

test('MIN-133 D1/D2/D4: view không còn cột noi_cap/place_of_origin, card meta, back/title', () => {
  const cols = viewCode.match(/const PERSON_COLS = \[([\s\S]*?)\];/);
  assert.ok(cols);
  const keys = [...cols[1].matchAll(/\['(\w+)'/g)].map((m) => m[1]);
  assert.deepEqual(keys, ['ho_ten', 'gioi_tinh', 'ngay_sinh', 'ngay_chet',
    'so_giay_to', 'ngay_cap', 'dia_chi']);
  for (const bad of ['draftMetaEl', 'Thông tin hồ sơ', 'ab-back', 'ab-title',
                     'Soạn văn bản', 'Nháp — chưa lưu', 'saveStateText',
                     'js-cd-save-state']) {
    assert.ok(!viewCode.includes(bad), `view còn "${bad}"`);
  }
  // Model vẫn giữ trường wire (không đổi model/contract).
  assert.match(modelSrc, /'noi_cap'/);
  assert.match(modelSrc, /'place_of_origin'/);
  assert.match(modelSrc, /'ngay_lap_ho_so'/);
});
