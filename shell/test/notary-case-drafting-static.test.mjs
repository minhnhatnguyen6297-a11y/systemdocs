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

const modelSrc = R(MODEL);
const viewSrc = R(VIEW);
const cssSrc = R(CSS);
const htmlSrc = R('src/renderer/index.html');
const rendererSrc = R('src/renderer/renderer.js');
const stylesSrc = R('src/renderer/styles.css');

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

test('view khong co Zalo / React / ReactFlow / Bootstrap', () => {
  for (const bad of ['zalo', 'Zalo', 'ZALO', 'React', 'react',
                     'ReactFlow', 'reactflow', 'Bootstrap', 'bootstrap',
                     'jsx', 'createElementNS']) {
    assert.ok(!viewCode.includes(bad), `view chua "${bad}"`);
  }
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
  assert.match(viewCode, /Gán vị trí/);         // nut menu thay the keo-tha
  assert.match(viewCode, /openAssignMenu/);
});

test('view co banner mock "Dữ liệu mô phỏng" + a11y attributes', () => {
  // Text banner o model (MOCK_BANNER), view render qua model.mockBanner()
  assert.match(modelSrc, /Dữ liệu mô phỏng/);
  assert.match(viewCode, /mockBanner\(\)/);
  assert.match(viewCode, /aria-label|setAttribute\('aria/);
  assert.match(viewCode, /role=|setAttribute\('role'/);
});

test('css: control >=44px va co focus-visible', () => {
  assert.match(cssSrc, /--cd-tap:\s*44px/);
  assert.match(cssSrc, /:focus-visible/);
  // khong con control nao nho hon 44px (tru checkbox/radio 20px mac dinh)
  assert.ok(!/min-(height|width):\s*(1[0-9]|2[0-9]|3[0-9])px/.test(cssSrc),
    'con control < 40px');
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
