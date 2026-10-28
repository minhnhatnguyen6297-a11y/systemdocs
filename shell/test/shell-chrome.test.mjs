// Shell chrome — MIN-133 (W1 nen chung): setStatus() ghi tooltip/aria/state
// len logo G1 tren rail. #statusbar da bo khoi index.html/styles.css; test
// o day chi giu hanh vi that cua setStatus (khong doc lai HTML/CSS/source).
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RENDERER = path.join(HERE, '..', 'src', 'renderer');
const read = (rel) => fs.readFileSync(path.join(RENDERER, rel), 'utf8');
const TOKENS = JSON.parse(fs.readFileSync(
  path.join(HERE, '..', '..', '_bmad-output', 'specs', 'ui', 'tokens.json'), 'utf8'));

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
