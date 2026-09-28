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
