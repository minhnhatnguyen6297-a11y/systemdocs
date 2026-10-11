'use strict';
// Control → source ownership registry for the visual-bug spike (schema v2).
// Anchors are exact definition needles; lines are located by bounded scan at
// save time so renames surface as stale:true instead of wrong line numbers.
//
// Privacy contract: only registry-KNOWN, normalized identities are serialized
// into source.control. Unknown fids/ids/classes are used for matching at save
// time but never persisted.
//
// SOT (read-only): shell/src/renderer/notary/case-drafting-view.js,
// shell/src/renderer/upload/index.js, shell/src/renderer/index.html,
// shell/src/renderer/notary/case-drafting.css, shell/src/renderer/upload/upload.css,
// shell/src/renderer/styles.css.

const NOTARY_VIEW = 'shell/src/renderer/notary/case-drafting-view.js';
const UPLOAD_INDEX = 'shell/src/renderer/upload/index.js';
const INDEX_HTML = 'shell/src/renderer/index.html';
const RENDERER = 'shell/src/renderer/renderer.js';
const NOTARY_CSS = 'shell/src/renderer/notary/case-drafting.css';
const UPLOAD_CSS = 'shell/src/renderer/upload/upload.css';
const SHELL_CSS = 'shell/src/renderer/styles.css';

// Base rule only per role — variant rules (.cd-cell:focus etc.) excluded.
const CSS_ANCHORS = {
  cdRoot: { file: NOTARY_CSS, selector: '.cd-root {', role: 'module base' },
  cdStageTbl: { file: NOTARY_CSS, selector: '.cd-root table.cd-stage-tbl {', role: 'stage table layout (shared asset/people)' },
  cdCell: { file: NOTARY_CSS, selector: '.cd-root .cd-stage-tbl .cd-cell {', role: 'stage table cell/input base' },
  cdAddressSuggestion: { file: NOTARY_CSS, selector: '.cd-root .cd-address-suggestion {', role: 'address suggestion dropdown base' },
  cdLookupRow: { file: NOTARY_CSS, selector: '.cd-root .cd-lookup-row {', role: 'lookup input wrapper' },
  uploadLab: { file: UPLOAD_CSS, selector: '.upload-lab {', role: 'module base' },
  ulTablist: { file: UPLOAD_CSS, selector: '.ul-tablist {', role: 'tab strip' },
  ulTab: { file: UPLOAD_CSS, selector: '.ul-tab {', role: 'tab button base' },
  ulTabSelected: { file: UPLOAD_CSS, selector: '.ul-tab[aria-selected="true"] {', role: 'selected tab state' },
  railLogo: { file: SHELL_CSS, selector: '.rail-logo {', role: 'rail logo' },
};

// Component anchor: exact needle to locate the definition/declaration line.
// kind 'js' (default): `function <symbol>(` declaration.
// kind 'assign': `<symbol>` assignment (e.g. upload's `NS.buildView =`).
// kind 'markup': literal needle in static HTML.
function jsComp(file, symbol, role) {
  return { file, symbol, role, needle: `function ${symbol}(`, mode: 'prefix' };
}
function assignComp(file, symbol, role) {
  return { file, symbol, role, needle: `${symbol} =`, mode: 'prefix' };
}
function markupComp(file, symbol, role, needle) {
  return { file, symbol, role, needle, mode: 'contains' };
}

// Each entry: how control identity matches, plus the JS components that render
// the control and the CSS anchors relevant to it. cd-lookup-row wrappers are
// built by four different functions (addressSuggestionEl :1010, assetTableEl
// :1220, peopleTableEl :1466/:1482, caseMetaEl :1566) — without a fid we
// cannot tell which, so all builders are listed.
const CONTROLS = [
  {
    id: 'notary.asset.address',
    match: { fid: /^a:\{row\}:dia_chi$/ },
    module: 'notary_v2',
    components: [
      jsComp(NOTARY_VIEW, 'assetTableEl', 'renders asset table incl. dia_chi input'),
      jsComp(NOTARY_VIEW, 'addressSuggestionEl', 'builds address input + suggestion dropdown'),
    ],
    css: ['cdStageTbl', 'cdCell', 'cdLookupRow', 'cdAddressSuggestion'],
  },
  {
    id: 'notary.person.address',
    match: { fid: /^p:\{row\}:dia_chi$/ },
    module: 'notary_v2',
    components: [
      jsComp(NOTARY_VIEW, 'peopleTableEl', 'renders people table incl. dia_chi input'),
      jsComp(NOTARY_VIEW, 'addressSuggestionEl', 'builds address input + suggestion dropdown'),
    ],
    css: ['cdStageTbl', 'cdCell', 'cdLookupRow', 'cdAddressSuggestion'],
  },
  {
    id: 'notary.person.issuer',
    match: { fid: /^p:\{row\}:issuer_no$/ },
    module: 'notary_v2',
    components: [jsComp(NOTARY_VIEW, 'peopleTableEl', 'renders people table incl. issuer field')],
    css: ['cdStageTbl', 'cdCell'],
  },
  {
    id: 'notary.case_meta.field',
    match: { fid: /^meta:[a-z_]+$/ },
    module: 'notary_v2',
    components: [jsComp(NOTARY_VIEW, 'caseMetaEl', 'renders case meta fields (meta:*)')],
    css: ['cdRoot'],
  },
  {
    id: 'notary.top.case_type',
    match: { fid: 'top:case_type' },
    module: 'notary_v2',
    components: [jsComp(NOTARY_VIEW, 'fillTopActions', 'renders top bar incl. case type select')],
    css: ['cdRoot'],
  },
  {
    id: 'notary.stage_table',
    match: { classToken: 'cd-stage-tbl' },
    module: 'notary_v2',
    components: [
      jsComp(NOTARY_VIEW, 'assetTableEl', 'asset table (grid cd-tbl cd-stage-tbl)'),
      jsComp(NOTARY_VIEW, 'peopleTableEl', 'people table (grid cd-ptbl cd-stage-tbl)'),
    ],
    css: ['cdStageTbl', 'cdCell'],
  },
  {
    id: 'notary.address_suggestion',
    match: { classToken: 'cd-address-suggestion' },
    module: 'notary_v2',
    components: [jsComp(NOTARY_VIEW, 'addressSuggestionEl', 'builds address suggestion dropdown')],
    css: ['cdAddressSuggestion'],
  },
  {
    id: 'notary.lookup_row',
    match: { classToken: 'cd-lookup-row' },
    module: 'notary_v2',
    components: [
      jsComp(NOTARY_VIEW, 'addressSuggestionEl', 'lookup wrapper inside suggestion control (:1010)'),
      jsComp(NOTARY_VIEW, 'assetTableEl', 'lookup wrapper inside asset table (:1220)'),
      jsComp(NOTARY_VIEW, 'peopleTableEl', 'lookup wrappers inside people table (:1466/:1482)'),
      jsComp(NOTARY_VIEW, 'caseMetaEl', 'lookup wrapper inside case meta (:1566)'),
    ],
    css: ['cdLookupRow', 'cdCell'],
  },
  {
    id: 'upload.tab',
    match: { idPattern: /^ul-tab-\{tabId\}$/ },
    module: 'upload',
    components: [assignComp(UPLOAD_INDEX, 'NS.buildView', 'renders upload module incl. tab buttons (ul-tab-*)')],
    css: ['ulTab', 'ulTablist', 'ulTabSelected', 'uploadLab'],
  },
  {
    id: 'upload.module_root',
    match: { classToken: 'upload-lab' },
    module: 'upload',
    components: [assignComp(UPLOAD_INDEX, 'NS.buildView', 'renders upload module root')],
    css: ['uploadLab'],
  },
  {
    id: 'shell.rail_logo',
    match: { classToken: 'rail-logo' },
    module: 'shell',
    components: [
      markupComp(INDEX_HTML, 'rail-logo', 'static rail logo markup', '<div id="rail-logo"'),
      jsComp(RENDERER, 'setStatus', 'updates engine-state status/tooltip on rail logo'),
    ],
    css: ['railLogo'],
  },
];

function normalizeId(v) {
  if (typeof v !== 'string') return '';
  return v.replace(/(a|p):[^:]+:/i, '$1:{row}:')
    .replace(/^ul-tab-.+$/, 'ul-tab-{tabId}')
    .replace(/^cd-[a-z]+-\d+-\d+$/, 'cd-{grid}-{x}-{y}');
}

// Anchored scan: 'prefix' (default) requires the trimmed line to START with
// the needle — matches actual declarations/selectors, never commented code or
// same-suffix lines ('#view section.upload-lab {' cannot match '.upload-lab {').
// 'contains' matches a mid-line literal (static markup like id="rail-logo").
function findLine(lines, needle, mode) {
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (mode === 'contains' ? t.includes(needle) : t.startsWith(needle)) return i + 1;
  }
  return null;
}

function controlIdentity(pick) {
  const fid = normalizeId(pick.fid || '');
  const ownId = normalizeId(pick.ownId || '');
  const classes = Array.isArray(pick.classes) ? pick.classes : [];
  // Nearest ancestor table tokens: with border-collapse the table itself is
  // never a hit target, so a real pick on a stage table lands on th/td.
  const table = Array.isArray(pick.tableTokens) ? pick.tableTokens : [];
  const cellLike = pick.cellLike === true;
  const moduleRoot = pick.moduleRoot || '';
  return { fid, ownId, classes, table, cellLike, moduleRoot };
}

// Returns the matched branch ('fid' | 'id' | 'class' | 'table') or null.
// 'class' = the picked node's OWN token; 'table' = an ANCESTOR table's token.
function matchControl(entry, ident) {
  const m = entry.match || {};
  if (m.fid) {
    if (typeof m.fid === 'string' ? ident.fid === m.fid : m.fid.test(ident.fid)) return 'fid';
    return null;
  }
  if (m.idPattern) return m.idPattern.test(ident.ownId) ? 'id' : null;
  if (m.classToken) {
    if (ident.classes.includes(m.classToken)) return 'class';
    if (ident.table.includes(m.classToken)) return 'table';
  }
  return null;
}
// Returns { control, confidence, owners } — never throws; unknown inputs
// degrade to module-ancestry or unmapped. Only registry-known identity fields
// are serialized; unknown identifiers are omitted, not echoed.
function resolveOwnership(pick, readSources) {
  const ident = controlIdentity(pick);
  const owners = { components: [], styles: [] };
  const moduleFromRoot = ident.moduleRoot === 'cd-root' ? 'notary_v2'
    : ident.moduleRoot === 'upload-lab' ? 'upload' : null;
  const control = { fid: null, id: null, classes: [], module: moduleFromRoot, scope: null };

  let entry = null; let branch = null;
  for (const c of CONTROLS) {
    const b = matchControl(c, ident);
    if (b) { entry = c; branch = b; break; }
  }

  // An ancestor-table token match is CONTEXT, not the picked node: only a
  // structural cell pick (th/td) is accepted as targeting the table itself
  // ('ancestor-table' scope); anything else inside the table degrades to the
  // component-ancestry tier so an unknown input can never claim exact-target
  // confidence through its container.
  const tableContext = branch === 'table' && !ident.cellLike;
  if (tableContext) { entry = null; branch = null; }

  let confidence;
  if (entry) {
    confidence = 'explicit-control-map';
    control.controlId = entry.id;
    control.module = entry.module;
    // Serialize ONLY the matched, normalized identity facet + scope.
    if (branch === 'fid') { control.fid = ident.fid; control.scope = 'exact'; }
    else if (branch === 'id') { control.id = ident.ownId; control.scope = 'exact'; }
    else if (branch === 'class') { control.classes = [entry.match.classToken]; control.scope = 'exact'; }
    else if (branch === 'table') { control.classes = [entry.match.classToken]; control.scope = 'ancestor-table'; }
  } else if (tableContext) {
    confidence = 'component-ancestry';
    control.container = { classToken: null, module: control.module };
    control.scope = 'ancestor-table';
  } else if (control.module) {
    confidence = 'module-ancestry';
  } else if (ident.fid || ident.ownId || ident.classes.length) {
    confidence = 'heuristic-static-id';
  } else {
    confidence = 'unmapped';
  }
  // Record the known ancestor-table token as container context (label only,
  // never as the picked control's identity).
  if (tableContext) {
    const known = ['cd-stage-tbl'].find((t) => ident.table.includes(t));
    control.container = { classToken: known || null, module: control.module };
  }

  const pushComponent = (c) => {
    const lines = readSources(c.file);
    const line = lines ? findLine(lines, c.needle, c.mode) : null;
    owners.components.push({
      file: c.file, symbol: c.symbol, role: c.role,
      line: line || null, stale: line === null,
    });
  };
  const pushCss = (key) => {
    const a = CSS_ANCHORS[key];
    const lines = readSources(a.file);
    const line = lines ? findLine(lines, a.selector) : null;
    owners.styles.push({
      file: a.file, selector: a.selector, role: a.role,
      line: line || null, stale: line === null,
    });
  };

  if (entry) {
    entry.components.forEach(pushComponent);
    entry.css.forEach(pushCss);
  } else if (confidence === 'component-ancestry' && control.container?.classToken === 'cd-stage-tbl') {
    // Container owners: the picked node is unknown, but the stage-table
    // container it lives in is known — list both builders as CONTEXT.
    pushComponent(jsComp(NOTARY_VIEW, 'assetTableEl', 'container: asset stage table builder (component-ancestry)'));
    pushComponent(jsComp(NOTARY_VIEW, 'peopleTableEl', 'container: people stage table builder (component-ancestry)'));
    pushCss('cdStageTbl');
  } else if (confidence === 'module-ancestry' && control.module === 'notary_v2') {
    pushComponent(jsComp(NOTARY_VIEW, 'createNotaryModuleView', 'notary module view (module-ancestry only)'));
    pushCss('cdRoot');
  } else if (confidence === 'module-ancestry' && control.module === 'upload') {
    pushComponent(assignComp(UPLOAD_INDEX, 'NS.buildView', 'upload module view (module-ancestry only)'));
    pushCss('uploadLab');
  }

  return { control, confidence, owners };
}

module.exports = { normalizeId, resolveOwnership, _CONTROLS: CONTROLS, _CSS_ANCHORS: CSS_ANCHORS };
