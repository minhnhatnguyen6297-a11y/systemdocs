'use strict';
const assert = require('assert/strict');
const { enabled, validate } = require('./policy.cjs');
const wc = { mainFrame: { url: 'file:///test' } }, win = { webContents: wc };
const event = { sender: wc, senderFrame: wc.mainFrame };
const good = { selector: 'html > body:nth-child(2) > button:nth-child(1)', note: 'Nut luu bi cat o 1024px', sourceIds: [] };
assert.equal(enabled(false, '1'), true);
assert.equal(enabled(true, '1'), false);
assert.equal(enabled(false, undefined), false);
assert.equal(validate(event, win, 'file:///test', good).note, 'Nut luu bi cat o 1024px');
assert.equal(validate(event, win, 'file:///test', { ...good, note: 'x'.repeat(240) }).note.length, 240);
for (const ev of [{ ...event, sender: {} }, { ...event, senderFrame: { url: 'file:///test' } }]) {
  assert.throws(() => validate(ev, win, 'file:///test', good), /sender_denied/);
}
assert.throws(() => validate(event, win, 'file:///wrong', good), /sender_denied/);
for (const bad of [{ ...good, selector: '#secret' }, { ...good, note: '' }, { ...good, note: 'x'.repeat(241) },
  { ...good, note: 'x'.repeat(9000) }, { ...good, sourceIds: ['x'.repeat(101)] }, { ...good, sourceIds: null }]) {
  assert.throws(() => validate(event, win, 'file:///test', bad), /invalid_payload/);
}
console.log('PASS: enabled/packaged gates, sender/frame/URL, size/schema, note kept verbatim');
// Schema v2 identity fields: valid payloads pass, structural abuse rejected.
assert.equal(validate(event, win, 'file:///test', { ...good,
  fid: 'a:3:dia_chi', ownId: 'ul-tab-2', classes: ['cd-cell'], moduleRoot: 'cd-root' }).fid, 'a:3:dia_chi');
for (const bad of [{ ...good, fid: '' }, { ...good, ownId: '' }, { ...good, fid: 'x y' }, { ...good, ownId: 'a b' }, { ...good, classes: 'cd-cell' },
  { ...good, classes: ['ok', 'bad token'] }, { ...good, classes: new Array(21).fill('x') },
  { ...good, moduleRoot: 'evil' }]) {
  assert.throws(() => validate(event, win, 'file:///test', bad), /invalid_payload/);
}
console.log('PASS: schema v2 identity fields validated (ids with separators, class tokens, moduleRoot set)');
// Registry resolution: a: vs p: dia_chi must produce distinct owners; ids
// normalize to {row}/{tabId}; unknown fids degrade to module-ancestry.
const { normalizeId, resolveOwnership } = require('./linkage.cjs');
assert.equal(normalizeId('a:3:dia_chi'), 'a:{row}:dia_chi');
assert.equal(normalizeId('p:17:dia_chi'), 'p:{row}:dia_chi');
assert.equal(normalizeId('ul-tab-2'), 'ul-tab-{tabId}');
const noSrc = () => null;
const aRes = resolveOwnership({ fid: 'a:{row}:dia_chi', ownId: '', classes: [], moduleRoot: 'cd-root' }, noSrc);
const pRes = resolveOwnership({ fid: 'p:{row}:dia_chi', ownId: '', classes: [], moduleRoot: 'cd-root' }, noSrc);
assert.equal(aRes.confidence, 'explicit-control-map');
assert.equal(aRes.control.controlId, 'notary.asset.address');
assert.equal(pRes.control.controlId, 'notary.person.address');
assert.notEqual(aRes.owners.components[0].symbol, pRes.owners.components[0].symbol);
assert.ok(aRes.owners.components.every(c => c.stale === true)); // no sources → stale, never a guessed line
const tabRes = resolveOwnership({ fid: '', ownId: 'ul-tab-{tabId}', classes: [], moduleRoot: 'upload-lab' }, noSrc);
assert.equal(tabRes.control.controlId, 'upload.tab');
assert.equal(tabRes.control.module, 'upload');
assert.equal(tabRes.control.id, 'ul-tab-{tabId}');
assert.equal(tabRes.control.fid, null, 'id-branch must not echo a fid');
const unRes = resolveOwnership({ fid: 'zz:9:whatever', ownId: '', classes: [], moduleRoot: 'cd-root' }, noSrc);
assert.equal(unRes.confidence, 'module-ancestry');
assert.equal(unRes.control.module, 'notary_v2');
assert.equal(unRes.control.fid, null, 'unknown fid must NOT be serialized');
const bare = resolveOwnership({ fid: '', ownId: 'weird-7', classes: ['mystery-cls'], moduleRoot: null }, noSrc);
assert.equal(bare.confidence, 'heuristic-static-id');
assert.equal(bare.owners.components.length, 0);
assert.equal(bare.control.id, null, 'unknown own id must NOT be serialized');
assert.equal(bare.control.classes.length, 0, 'unknown classes must NOT be serialized');
const unCls = resolveOwnership({ fid: '', ownId: '', classes: ['cd-stage-tbl', 'secret-extra'], moduleRoot: 'cd-root' }, noSrc);
assert.deepEqual(unCls.control.classes, ['cd-stage-tbl'], 'only the matched registry token serializes');
console.log('PASS: linkage registry — a/p dia_chi distinct owners, upload tab id-pattern, ancestry fallbacks, unknown identities omitted, no guessed lines');
const fs = require('fs'), path = require('path');
// Live-source resolution against the real renderer tree (lines found, not stale).
const shellRoot = path.resolve(__dirname, '../..');
const readSrc = (rel) => {
  try { return fs.readFileSync(path.join(shellRoot, rel), 'utf8').split(/\r?\n/); } catch { return null; }
};
const live = resolveOwnership({ fid: 'a:{row}:dia_chi', ownId: '', classes: [], moduleRoot: 'cd-root' }, readSrc);
assert.ok(live.owners.components.length >= 2 && live.owners.components.every(c => c.line > 0 && c.stale === false));
assert.ok(live.owners.styles.every(s => s.line > 0 && s.stale === false));
assert.ok(live.owners.styles.some(s => s.selector === '.cd-root table.cd-stage-tbl {'));
const liveTab = resolveOwnership({ fid: '', ownId: 'ul-tab-{tabId}', classes: [], moduleRoot: 'upload-lab' }, readSrc);
assert.equal(liveTab.owners.components.length, 1);
assert.equal(liveTab.owners.components[0].symbol, 'NS.buildView');
assert.equal(liveTab.owners.components[0].file, 'shell/src/renderer/upload/index.js');
assert.ok(liveTab.owners.components[0].line > 0 && liveTab.owners.components[0].stale === false);
assert.ok(liveTab.owners.styles.every(s => s.line > 0 && s.stale === false));
assert.ok(liveTab.owners.styles.some(s => s.selector === '.ul-tab {'));
const liveLogo = resolveOwnership({ fid: '', ownId: '', classes: ['rail-logo'], moduleRoot: null }, readSrc);
assert.equal(liveLogo.owners.components.length, 2);
assert.ok(liveLogo.owners.components.some(c => c.symbol === 'rail-logo' && c.file.endsWith('index.html') && c.line > 0 && c.stale === false));
assert.ok(liveLogo.owners.components.some(c => c.symbol === 'setStatus' && c.file.endsWith('renderer.js') && c.line > 0 && c.stale === false));
const liveLookup = resolveOwnership({ fid: '', ownId: '', classes: ['cd-lookup-row'], moduleRoot: 'cd-root' }, readSrc);
assert.ok(liveLookup.owners.components.length >= 4, 'cd-lookup-row has four builder sites');
assert.deepEqual(liveLookup.control.classes, ['cd-lookup-row']);
const leakA = resolveOwnership({ fid: 'a:{row}:dia_chi', ownId: 'cd-row-77-3', classes: ['cd-cell', 'secret-custom'], moduleRoot: 'cd-root' }, readSrc);
const liveTbl = resolveOwnership({ fid: '', ownId: '', classes: ['cd-rowlabel'], tableTokens: ['grid', 'cd-tbl', 'cd-stage-tbl'], cellLike: true, moduleRoot: 'cd-root' }, readSrc);
assert.equal(liveTbl.control.controlId, 'notary.stage_table');
assert.equal(liveTbl.control.scope, 'ancestor-table');
assert.deepEqual(liveTbl.control.classes, ['cd-stage-tbl']);
// Unknown input INSIDE the table: container context only — never exact-target.
const contained = resolveOwnership({ fid: '', ownId: '', classes: ['mystery-cls'], tableTokens: ['grid', 'cd-tbl', 'cd-stage-tbl'], cellLike: false, moduleRoot: 'cd-root' }, readSrc);
assert.equal(contained.confidence, 'component-ancestry');
assert.equal(contained.control.scope, 'ancestor-table');
assert.equal(contained.control.container.classToken, 'cd-stage-tbl');
assert.equal(contained.control.container.module, 'notary_v2');
assert.equal(contained.owners.components.length, 2, 'container builders listed as context');
assert.equal(contained.owners.components[0].symbol, 'assetTableEl');
assert.equal(contained.owners.components[1].symbol, 'peopleTableEl');
assert.ok(!JSON.stringify(leakA.control).includes('secret-custom'), 'non-registry class must not leak');
const leakP = resolveOwnership({ fid: 'p:{row}:dia_chi', ownId: 'zz:3:whatever', classes: [], moduleRoot: 'cd-root' }, readSrc);
assert.ok(!JSON.stringify(leakP.control).includes('zz:3:whatever'), 'cross-facet id must not leak into p: match');
console.log('PASS: live renderer sources resolve anchor lines (asset dia_chi, upload tab NS.buildView, rail-logo markup, lookup-row builders); unknown ids/classes never leak');
// Execute the real main-entry gate with mocked packaging status; no installer claim.
const vm = require('vm');
const mainDir = path.join(shellRoot, 'shell/src/main');
const prefix = fs.readFileSync(path.join(mainDir, 'main.js'), 'utf8').split('// MIN-69 T9:')[0];
for (const [packaged, flag, expected] of [[true, '1', 0], [false, undefined, 0], [false, '1', 1]]) {
  let loaded = 0, isolated = 0;
  vm.runInNewContext(prefix, { __dirname: mainDir, process: { env: { G1_VISUAL_BUG_SPIKE: flag } },
    require(name) {
      if (name === 'path') return path;
      if (name === 'fs') return fs;
      if (name === 'electron') return { app: { isPackaged: packaged } };
      if (name.endsWith('main.cjs')) { loaded++; return { isolate() { isolated++; } }; }
      return {};
    } });
  assert.equal(loaded, expected); assert.equal(isolated, expected);
}
console.log('PASS: real main-entry gate, mocked app.isPackaged=true never loads spike');
// Missing/renamed declarations and commented CSS must never yield a guessed line.
const missingAnchors = resolveOwnership({ fid: 'a:12:dia_chi', classes: [], moduleRoot: 'cd-root' },
  () => ['// function assetTableEl(', 'function assetTableElRenamed(', '/* .cd-root table.cd-stage-tbl { */']);
assert(missingAnchors.owners.components.every(owner => owner.stale && owner.line === null));
assert(missingAnchors.owners.styles.every(owner => owner.stale && owner.line === null));
for (const fid of ['a:12:dia_chi:secret', 'prefix-a:12:dia_chi', 'p:12:unknown_field']) {
  const resolved = resolveOwnership({ fid, classes: [], moduleRoot: 'cd-root' }, noSrc);
  assert.equal(resolved.control.fid, null);
  assert.equal(resolved.confidence, 'module-ancestry');
}
for (const bad of [{ ...good, tableTokens: ['secret token'] }, { ...good, cellLike: 'true' }]) {
  assert.throws(() => validate(event, win, 'file:///test', bad), /invalid_payload/);
}
const pkg = JSON.parse(fs.readFileSync(path.join(shellRoot, 'shell/package.json'), 'utf8'));
assert.deepEqual(pkg.build.files, ['src/main/**', 'src/preload/**', 'src/renderer/**', 'package.json']);
console.log('PASS: stale anchors, malformed identities, structural validation, tools excluded from package globs');
