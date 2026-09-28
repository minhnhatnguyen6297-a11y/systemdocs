// Shell chrome — MIN-133 (W1 nen chung):
// - #statusbar da bo khoi index.html/styles.css (D3); engine/version/contract
//   chuyen vao tooltip logo G1 tren rail.
// - setStatus() an toan khi khong con element statusbar; polling sidecar giu.
// - :root cua styles.css khop tokens.json v1.1.0 cho cac gia tri MIN-133.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RENDERER = path.join(HERE, '..', 'src', 'renderer');
const read = (rel) => fs.readFileSync(path.join(RENDERER, rel), 'utf8');
const TOKENS = JSON.parse(fs.readFileSync(
  path.join(HERE, '..', '..', 'docs', 'product', 'ui', 'tokens.json'), 'utf8'));

const htmlSrc = read('index.html');
const stylesSrc = read('styles.css');
const rendererSrc = read('renderer.js');

function extractSetStatus() {
  const start = rendererSrc.indexOf('function setStatus(s) {');
  assert.ok(start > -1, 'renderer.js thieu setStatus');
  const end = rendererSrc.indexOf('\n}\n', start);
  return rendererSrc.slice(start, end + 2);
}

function makeSetStatus(doc) {
  const L = { engineStateLabel: (s) => `lbl:${s || '—'}` };
  // eslint-disable-next-line no-new-func
  return new Function('L', 'document', `${extractSetStatus()}\nreturn setStatus;`)(L, doc);
}

test('index.html: khong con #statusbar + 3 pill engine; logo G1 co id + title', () => {
  assert.doesNotMatch(htmlSrc, /id="statusbar"/);
  assert.doesNotMatch(htmlSrc, /id="engine-state"|id="engine-version"|id="contract"/);
  assert.match(htmlSrc, /id="rail-logo"[^>]*class="rail-logo"|class="rail-logo"[^>]*id="rail-logo"/);
  assert.match(htmlSrc, /<div id="rail-logo"[^>]*title=/);
  assert.match(htmlSrc, /<section id="view"><\/section>/);
});

test('styles.css: khong con style #statusbar', () => {
  assert.doesNotMatch(stylesSrc, /#statusbar\s*\{/);
});

test('setStatus: khong crash khi khong co element nao (statusbar da bo)', () => {
  const setStatus = makeSetStatus({ getElementById: () => null });
  assert.doesNotThrow(() => setStatus({ state: 'ready' }));
  assert.doesNotThrow(() => setStatus(undefined));
});

test('setStatus: tooltip logo mang engine + version + contract', () => {
  const attrs = {};
  const logo = {
    title: '', dataset: {},
    setAttribute(k, v) { attrs[k] = v; },
  };
  const setStatus = makeSetStatus({
    getElementById: (id) => (id === 'rail-logo' ? logo : null),
  });
  setStatus({ state: 'ready', engine_version: '1.2.3', contract_version: 'desktopcommand.v1' });
  assert.match(logo.title, /engine: lbl:ready/);
  assert.match(logo.title, /1\.2\.3/);
  assert.match(logo.title, /desktopcommand\.v1/);
  assert.match(attrs['aria-label'], /^G1 — engine: lbl:ready/);
  assert.equal(logo.dataset.engineState, 'ready');
  // thieu version/contract → tooltip chi con dong engine
  setStatus({ state: 'starting' });
  assert.equal(logo.title, 'engine: lbl:starting');
});

test('renderer giu polling sidecarStatus + engineSlotEl + engineInstanceId', () => {
  assert.match(rendererSrc, /setInterval\(async \(\) => \{\s*const r = await api\.getStatus\(\)/);
  assert.match(rendererSrc, /setStatus\(r\.data\)/);
  assert.match(rendererSrc, /function engineSlotEl\(\)/);
  assert.match(rendererSrc, /engineInstanceId: \(\) => sidecarStatus\.engine_instance_id/);
  assert.match(rendererSrc, /function buildStatus\(entry\)/);
});

test(':root styles.css khop tokens.json v1.1.0 (gia tri MIN-133)', () => {
  const rootBlock = stylesSrc.slice(stylesSrc.indexOf(':root {'),
    stylesSrc.indexOf('}', stylesSrc.indexOf(':root {')));
  const cssVar = (name) => {
    const m = rootBlock.match(new RegExp(`--${name}:\\s*([^;]+);`));
    assert.ok(m, `:root thieu --${name}`);
    return m[1].trim();
  };
  const pairs = [
    ['bg-app', TOKENS.color.bg.app.value],
    ['bg-canvas', TOKENS.color.bg.canvas.value],
    ['border-card', TOKENS.color.border.card.value],
    ['fs-data', TOKENS.font.size.data.value],
    ['fs-small', TOKENS.font.size.small.value],
    ['fs-chip', TOKENS.font.size.chip.value],
    ['fs-card', TOKENS.font.size.cardTitle.value],
    ['btn-h', TOKENS.size.buttonHeight.value],
    ['btn-h-sm', TOKENS.size.buttonHeightSm.value],
    ['row-h', TOKENS.size.tableRow.value],
    ['card-head-h', TOKENS.size.cardHeadHeight.value],
    ['gap', TOKENS.space.cardGap.value],
    ['view-pad', TOKENS.space.viewPadding.value],
    ['card-pad-x', TOKENS.space.cardPadding.x],
  ];
  for (const [name, want] of pairs) {
    assert.equal(cssVar(name).toLowerCase(), String(want).toLowerCase(), `--${name}`);
  }
  assert.equal(TOKENS.layout.contentMaxWidth.value, null);
});

test('styles.css: card vien 1px, #view padding token, nut sm dung token', () => {
  assert.match(stylesSrc, /\.card \{[^}]*border:\s*1px solid var\(--border-card\)/);
  assert.match(stylesSrc, /#view \{[^}]*padding:\s*var\(--view-pad\)/);
  assert.match(stylesSrc, /button\.sm, \.btn\.sm \{[^}]*min-height:\s*var\(--btn-h-sm\)/);
  assert.match(stylesSrc, /\.card-head \{[^}]*min-height:\s*var\(--card-head-h\)/);
  // rail van giu vung bam 44px (tapMin)
  assert.match(stylesSrc, /\.rail-btn \{[^}]*min-height:\s*44px/);
});
