'use strict';
const path = require('node:path');
const { ipcRenderer } = require('electron');
const req = name => require(path.join(window.auditRoot, 'shell/src/renderer', name));
const L = req('lib.js');
const M = req('notary/case-drafting-model.js');
const VIEW = req('notary/case-drafting-view.js');
window.G1_NOTARY_ERRORS = req('notary/error-catalog.js');
window.G1_NOTARY_INTAKE = req('notary/intake-dialog.js');
window.G1_NOTARY_DIAGRAM = req('notary/relationship-diagram.js');
window.G1_NOTARY_WORD = req('notary/word-export-dialog.js');
const settle = () => new Promise(resolve => setTimeout(resolve, 40));
const sel = fid => `[data-fid="${fid}"]`;
function build(confirmation = true) {
  const calls = [], pending = [];
  const client = { run(cmd, payload) {
    if (cmd !== 'notary.address_lookup') return Promise.resolve({ok:true,data:{}});
    calls.push({cmd, payload});
    return new Promise(resolve => pending.push(resolve));
  } };
  const model = M.createModel({client});
  const view = VIEW.createNotaryModuleView({model, lib:L, notify:() => {},
    confirm:async () => confirmation, runCommand:client.run});
  document.activeElement?.blur();
  document.getElementById('fixture').replaceChildren(view.el);
  model.newDraft('inheritance');
  const person = model.addPerson({ho_ten:'Demo', dia_chi:'Xa A, Tinh P'});
  const fid = `p:${person.row_id}:dia_chi`;
  const traFid = `lookup-tra:person:${person.row_id}`;
  const source = () => view.el.querySelector(sel(fid));
  const box = () => view.el.querySelector(`#address-person-${person.row_id}`);
  return {model, view, person, calls, pending, fid, traFid, source, box};
}
async function click(fid) {
  await ipcRenderer.invoke('audit-click', sel(fid));
  await settle();
}
function response(presentation, status = 'found') {
  return {ok:true, data: {schema_version:'notary.address-lookup.v2',
    presentation, status, total:status === 'too_many' ? 12 : 1,
    results:status === 'too_many' ? [] : [{unit_id:'audit-a', level:'commune',
      name:'Xã Demo A', province:{unit_id:'audit-p',name:'Tỉnh Demo P'},
      source_text:'Xã Gốc A', display:'Kết quả riêng cho A',
      observation_id:'audit-obs', evidence:[]}], dataset_version:'synthetic',revision:1}};
}
exports.run = async () => {
  const a = build();
  a.source().focus();
  a.source().setSelectionRange(1,4,'backward');
  await click(a.traFid);
  if (!a.pending.length) throw Error('Native Tra click did not start lookup');
  const before = a.box().textContent;
  a.view.el.querySelector(sel(`p:${a.person.row_id}:ho_ten`)).focus();
  a.pending.shift()(response('drafting'));
  await settle();
  const readyWhileEditing = {
    scenario:'lookup returns while another input has focus (source unchanged)',
    status_before_response:before,
    model_phase:a.model.state.addressSlots['person:' + a.person.row_id].phase,
    rendered_text:a.box().textContent,
    copy_buttons:a.box().querySelectorAll('button').length,
    focus_after_response:document.activeElement?.dataset.fid || null,
  };

  const b = build(false);
  b.source().focus();
  b.source().setSelectionRange(1,4,'backward');
  await click(b.traFid);
  if (!b.pending.length) throw Error('Cancel scenario did not start lookup');
  b.pending.shift()(response('drafting','too_many'));
  await settle();
  const cancelFocus = {
    scenario:'cancel too_many after editing address selection',
    expected_focus:b.fid,
    actual_focus:document.activeElement?.dataset.fid || null,
    actual_selection:[b.source().selectionStart,b.source().selectionEnd],
    full_calls:b.calls.filter(c => c.payload.presentation === 'full').length,
  };

  async function checkClose(previousField) {
    const d = build(true);
    const previousFid = previousField === 'dia_chi' ? d.fid
      : `p:${d.person.row_id}:ho_ten`;
    const previous = d.view.el.querySelector(sel(previousFid));
    previous.focus();
    previous.value += ' chưa lưu';
    previous.dispatchEvent(new Event('input',{bubbles:true}));
    previous.setSelectionRange(1,4,'backward');
    if (!previous.isConnected || document.activeElement !== previous)
      throw Error('Audit setup lost the input before native click');
    const beforeStage = JSON.stringify(d.model.state.stage);
    await click(d.traFid);
    d.pending.shift()(response('drafting','too_many'));
    await settle();
    if (!d.model.state.addressFull || !d.pending.length) throw Error('Close scenario did not open');
    await click('lookup-full-close');
    d.pending.shift()(response('full'));
    await settle();
    const after = d.view.el.querySelector(sel(previousFid));
    return { scenario:`close full while request pending; previously editing ${previousField}`,
      expected_focus:previousFid,actual_focus:document.activeElement?.dataset.fid || null,
      expected_selection:[1,4,'backward'],
      actual_selection:[after.selectionStart,after.selectionEnd,after.selectionDirection],
      draft_preserved:beforeStage === JSON.stringify(d.model.state.stage),
      full_cleared:d.model.state.addressFull === null,
      modal_count_after_late_response:document.querySelectorAll('[role="dialog"]').length,
    };
  }
  const normalClose = await checkClose('dia_chi');
  const otherFieldClose = await checkClose('ho_ten');

  const c = build(true);
  c.source().focus();
  c.source().setSelectionRange(1,4,'backward');
  await click(c.traFid);
  if (!c.pending.length) throw Error('Overlay scenario did not start lookup');
  c.pending.shift()(response('drafting','too_many'));
  await settle();
  const query = document.querySelector(sel('lookup-full-query'));
  if (!query || !c.pending.length) return {
    ready_while_editing:readyWhileEditing,cancel_focus:cancelFocus,
    normal_close:normalClose,other_field_close:otherFieldClose,
    overlay_error:{calls:c.calls,slots:c.model.state.addressSlots,
      full:c.model.state.addressFull,html:c.view.el.textContent.slice(-1800)} };
  query.value = 'Xa B, Tinh P';
  query.dispatchEvent(new Event('input',{bubbles:true}));
  c.pending.shift()(response('full'));
  await settle();
  const overlayEdited = {
    scenario:'edit overlay query A -> B while response for A pending',
    visible_query:query.value,
    model_query:c.model.state.addressFull.query,
    model_phase:c.model.state.addressFull.phase,
    rendered_results:document.querySelector(sel('lookup-full-list')).textContent,
    auto_lookup_on_edit:c.calls.length > 2,
    modal_count:document.querySelectorAll('[role="dialog"]').length,
    viewport:{width:innerWidth,height:innerHeight},
  };

  const e = build(true);
  const dead = e.model.addPerson({ho_ten:'Chet', ngay_chet:'2020-01-01',
    dia_chi:'Xa Chet, Tinh P', noi_cap:'UBND Xa Cu'});
  await settle();
  await click(`lookup-tra:issuer:${dead.row_id}`);
  const issuerCalls = e.calls.filter(x => x.payload.presentation === 'drafting');
  e.model.updateCaseMeta('noi_niem_yet', 'Niem yet that');
  await settle();
  await click('lookup-tra:posting:posting');
  const postingCalls = e.calls.filter(x => x.payload.presentation === 'drafting');
  const flows = {
    scenario:'issuer query from deceased address; posting query from posting box',
    issuer_query:issuerCalls.length ? issuerCalls[issuerCalls.length-1].payload.query : null,
    posting_query:postingCalls.length ? postingCalls[postingCalls.length-1].payload.query : null,
  };

  const f = build(true);
  await click(f.traFid);
  f.pending.shift()(response('drafting','too_many'));
  await settle();
  f.pending.shift()(response('full'));
  await settle();
  const copyBtn = document.querySelector(sel('lookup-full-copy:0'));
  const docFocused = document.hasFocus();
  let clipboardApi = 'unknown';
  try {
    clipboardApi = (typeof navigator !== 'undefined' &&
      !!(navigator.clipboard && navigator.clipboard.writeText)) ?
      'available' : 'missing';
  } catch (err) {
    clipboardApi = 'check-failed';
  }
  await click('lookup-full-copy:0');
  await new Promise(resolve => setTimeout(resolve, 800));
  await settle();
  let clipboardText = null;
  try {
    clipboardText = require('electron').clipboard.readText();
  } catch (err) {
    clipboardText = 'CLIPBOARD_UNREADABLE:' + String(err);
  }
  const copyCheck = {
    scenario:'click Copy in full overlay, read OS clipboard',
    clipboard_text:clipboardText,
    expected_display:'Kết quả riêng cho A',
    copy_button_text:document.querySelector(sel('lookup-full-copy:0')) ?
      document.querySelector(sel('lookup-full-copy:0')).textContent : null,
    copy_button_before_click:copyBtn ? copyBtn.textContent : null,
    document_focused:docFocused,
    clipboard_api:clipboardApi,
    overlay_note:document.querySelector(sel('lookup-full-note')) ?
      document.querySelector(sel('lookup-full-note')).textContent : null,
  };
  return {ready_while_editing:readyWhileEditing,cancel_focus:cancelFocus,
    normal_close:normalClose,other_field_close:otherFieldClose,
    overlay_edited:overlayEdited,flows:flows,copy_check:copyCheck};
};
