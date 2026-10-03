// Pure-state tests cho case-drafting-model.js (MIN-111 → MIN-128 v2).
// Model la state machine thuan — khong DOM, khong Node API ngoai crypto/uuid
// inject duoc. Test inject command client gia co semantics notary.case-
// drafting.v2 §13 (giong mock adapter): revision guard, owner_row_id mirror,
// ownPositions/receivePositions, domain two_party 30 slot canonical.
// Fixtures: shell/test/fixtures/notary-case-drafting/*.json.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIX_DIR = path.join(HERE, 'fixtures', 'notary-case-drafting');

const M = require('../src/renderer/notary/case-drafting-model.js');

const uuid = () => crypto.randomUUID();
const SCHEMA = 'notary.case-drafting.v2';
const TP_IDS = Array.from({ length: 30 }, (_, i) => `p${i + 1}`);

function loadFixture(name) {
  return JSON.parse(
    fs.readFileSync(path.join(FIX_DIR, `${name}.json`), 'utf8'));
}

function fakeRenderModel(state) {
  // Render_model toi thieu dung shape contract §7.2 — inheritance: 'complete'
  // khi co node owner da gan nguoi (v2 khong con isLandOwner).
  const nodes = (state && state.nodes || []).filter(
    (n) => n && !n.deleted && n.personId);
  const owner = nodes.find((n) => n.id === 'owner');
  return {
    engineVersion: 2,
    status: owner ? 'complete' : 'invalid',
    allocations: {},
    breakdowns: [],
    requiredSlots: [],
    warnings: [],
    errors: owner ? []
      : [{ code: 'missing_land_owner', message: 'no owner' }],
    unresolvedEstates: [],
    conservation: { allocated: '0', unresolved: '0', total: '0' },
  };
}

function unsupportedRender() {
  // §13.5: domain two_party khong chay engine thua ke — unsupported model.
  return {
    engineVersion: 2,
    status: 'unsupported',
    allocations: {},
    breakdowns: [],
    requiredSlots: [],
    warnings: [{ code: 'diagram.two_party_unsupported',
                 message: 'khong ho tro tinh thua ke' }],
    errors: [],
    unresolvedEstates: [],
    conservation: { allocated: '0', unresolved: '0', total: '0' },
  };
}

function canonicalTwoParty(nodes) {
  // canonical 30 slot — giu personId/hidden cua slot hop le, bo phan thua.
  const byId = {};
  for (const n of nodes || []) {
    if (n && typeof n.id === 'string' && !(n.id in byId)) byId[n.id] = n;
  }
  return TP_IDS.map((id) => ({
    id,
    personId: byId[id] && !byId[id].deleted ? byId[id].personId ?? null
                                           : null,
    hidden: !!(byId[id] && byId[id].hidden),
    deleted: false,
  }));
}

// Client gia mo phong contract v2 §13: revision counter, workspace_conflict
// khi base_revision khac, stage_validation_error khi ho_ten rong,
// workspace_locked khi locked, workspace_owner_required khi inheritance
// thieu owner_row_id, diagram_owner_mismatch khi node owner lech pointer,
// diagram_domain_mismatch khi state.domain != case_type, prune personId +
// position > len(assets), canonical 30 slot cho two_party.
function fakeClient(seed) {
  const cases = {};
  const catalog = JSON.parse(
    JSON.stringify((seed && seed.__customers) || []));
  for (const [cid, c] of Object.entries(seed)) {
    if (cid === '__customers') continue;
    cases[Number(cid)] = JSON.parse(JSON.stringify(c));
    cases[Number(cid)].id = Number(cid);
  }
  let nextEid = 900;
  let nextCid = 1000;
  const idem = {};                        // idempotency_key → case_id
  const calls = [];

  const ok = (data, extra = {}) => ({ ok: true, data, ...extra });
  const fail = (code, message, details) => ({
    ok: false,
    error: { code, message: message || code, retryable: false,
             next_action: null, details: details || null },
  });
  const isTp = (c) => c.case_type === 'two_party';
  const supported = (c) =>
    c.case_type === 'inheritance' || isTp(c);

  function getCase(payload) {
    const c = cases[payload && payload.case_id];
    if (!c) return { err: fail('case_not_found', 'khong tim thay ho so') };
    return { c };
  }

  function diagramOut(c) {
    const dg = c.diagram;
    return {
      domain: dg.domain || (supported(c) ? c.case_type : 'inheritance'),
      state: JSON.parse(JSON.stringify(dg.state)),
      render_model: dg.render_model === 'auto'
        ? (isTp(c) ? unsupportedRender()
                   : fakeRenderModel(dg.state))
        : dg.render_model,
      warnings: dg.warnings || [],
    };
  }

  function workspaceData(c) {
    const sup = supported(c);
    return {
      schema_version: SCHEMA,
      backend_mode: 'mock',
      case: {
        id: c.id, case_type: c.case_type,
        document_type: c.document_type, status: c.status,
        locked: !!c.locked, revision: c.revision,
        ngay_lap_ho_so: c.ngay_lap_ho_so ?? null,
        noi_niem_yet: c.noi_niem_yet ?? null,
        nguoi_nhan_uy_quyen: c.nguoi_nhan_uy_quyen ?? null,
        nguoi_nhan_uy_quyen_id: c.nguoi_nhan_uy_quyen_id ?? null,
        noi_dung_viec: c.noi_dung_viec ?? null,
        ghi_chu: c.ghi_chu ?? null,
      },
      stage: JSON.parse(JSON.stringify(c.stage)),
      diagram: diagramOut(c),
      capabilities: {
        intake: sup ? ['image', 'pdf', 'docx', 'xlsx', 'text'] : [],
        diagram: sup,
        word_export: c.case_type === 'inheritance',
      },
    };
  }

  // prune personId ngoai stage + position > len(assets) + sync mirror
  // owner + canonical two_party — mirror notary_mock_adapter._prune_diagram
  // /_sync_owner_node (§13.4/§13.6).
  function pruneDiagram(c) {
    const st = c.diagram.state;
    const ids = new Set(c.stage.people.map((p) => p.row_id));
    const warnings = [];
    for (const n of st.nodes || []) {
      if (n.personId && !ids.has(n.personId)) n.personId = null;
    }
    if (isTp(c)) {
      st.nodes = canonicalTwoParty(st.nodes);
    } else {
      const count = (c.stage.assets || []).length;
      for (const n of st.nodes || []) {
        for (const k of ['ownPositions', 'receivePositions']) {
          if (!Array.isArray(n[k])) continue;
          const next = n[k].filter((p) => p >= 1 && p <= count);
          if (next.length !== n[k].length) {
            n[k] = next;
            warnings.push({ code: 'diagram.selection_pruned',
                            node: n.id,
                            message: `vi tri > ${count} bi bo` });
          }
        }
      }
      // §13.6: commit sync node 'owner' := stage.owner_row_id.
      const oid = c.stage.owner_row_id;
      const owner = (st.nodes || []).find(
        (n) => n.id === 'owner' && !n.deleted);
      if (owner && oid) owner.personId = oid;
    }
    return warnings;
  }

  // §13.1/§13.6: owner_row_id bat buoc + tro row co that (inheritance);
  // cam field voi two_party.
  function checkOwnerPointer(c, stage) {
    if (isTp(c)) {
      if ('owner_row_id' in stage) {
        return fail('validation_error',
                    'owner_row_id cam voi two_party');
      }
      return null;
    }
    const ids = new Set((stage.people || []).map((p) => p.row_id));
    const oid = stage.owner_row_id;
    const UUID4 =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!(typeof oid === 'string' && UUID4.test(oid) && ids.has(oid))) {
      return fail('workspace_owner_required',
                  'thieu owner_row_id hop le',
                  { owner_row_id: oid ?? null });
    }
    return null;
  }

  function stageFieldErrors(c, stage) {
    const fe = [];
    const people = stage.people || [];
    const assets = stage.assets || [];
    for (const p of people) {
      if (!p.ho_ten || !String(p.ho_ten).trim()) {
        fe.push({ row_id: p.row_id, field: 'ho_ten',
                  code: 'required', message: 'bat buoc' });
      }
    }
    if (assets.length > 3) {
      fe.push({ row_id: assets[3].row_id, field: 'assets',
                code: 'asset_limit', message: 'toi da 3' });
    }
    const pLimit = isTp(c) ? 30 : 20;
    if (people.length > pLimit) {
      fe.push({ row_id: people[pLimit].row_id, field: 'people',
                code: 'people_limit', message: `toi da ${pLimit}` });
    }
    return fe;
  }

  async function run(command, payload) {
    calls.push({ command, payload: JSON.parse(JSON.stringify(payload)) });
    switch (command) {
      case 'notary.workspace_get': {
        const { c, err } = getCase(payload);
        if (err) return err;
        return ok(workspaceData(c));
      }
      case 'notary.workspace_commit_stage': {
        const { c, err } = getCase(payload);
        if (err) return err;
        if (c.locked) return fail('workspace_locked', 'da khoa');
        if (!supported(c)) {
          return fail('case_type_unsupported', 'chua ho tro');
        }
        if (payload.base_revision !== c.revision) {
          return fail('workspace_conflict', 'revision khac',
                      { server_revision: c.revision });
        }
        const stage = payload.stage;
        if (!stage || typeof stage !== 'object' ||
            !Array.isArray(stage.people) || !Array.isArray(stage.assets)) {
          return fail('validation_error', 'stage khong dung shape');
        }
        const ownerErr = checkOwnerPointer(c, stage);
        if (ownerErr) return ownerErr;
        const fieldErrors = stageFieldErrors(c, stage);
        if (fieldErrors.length) {
          return fail('stage_validation_error', 'loi field',
                      { field_errors: fieldErrors });
        }
        // MIN-141 đợt 3: payload.case (neu co) ap cung transaction —
        // validate immutable type + uq id/name nhu mock adapter.
        const cm = payload.case;
        if (cm != null) {
          if (typeof cm !== 'object' || Array.isArray(cm)) {
            return fail('validation_error', 'payload.case phai la object');
          }
          if (cm.case_type !== undefined && cm.case_type !== c.case_type) {
            return fail('validation_error',
                        'case_type immutable', { expected: c.case_type });
          }
          if (cm.document_type !== undefined &&
              cm.document_type !== c.document_type) {
            return fail('validation_error',
                        'document_type immutable',
                        { expected: c.document_type });
          }
          const uid = cm.nguoi_nhan_uy_quyen_id;
          if (uid !== undefined && uid !== null &&
              (!Number.isInteger(uid) || uid < 1)) {
            return fail('validation_error',
                        'nguoi_nhan_uy_quyen_id phai la int >= 1/null');
          }
          if (uid != null) {
            const cust = catalog.find((x) => x.id === uid);
            if (!cust) {
              return fail('validation_error',
                          `nguoi_nhan_uy_quyen_id ${uid} khong ton tai`);
            }
            if (cm.nguoi_nhan_uy_quyen !== undefined &&
                cm.nguoi_nhan_uy_quyen !== null &&
                cm.nguoi_nhan_uy_quyen !== cust.ho_ten) {
              return fail('validation_error',
                          'nguoi_nhan_uy_quyen vs id mau thuan');
            }
            c.nguoi_nhan_uy_quyen = cust.ho_ten;
            c.nguoi_nhan_uy_quyen_id = cust.id;
          } else if ('nguoi_nhan_uy_quyen' in cm) {
            c.nguoi_nhan_uy_quyen = cm.nguoi_nhan_uy_quyen;
            c.nguoi_nhan_uy_quyen_id = null;
          }
          for (const f of ['noi_niem_yet', 'noi_dung_viec', 'ghi_chu']) {
            if (f in cm) c[f] = cm[f];
          }
          if (cm.ngay_lap_ho_so !== undefined &&
              cm.ngay_lap_ho_so !== null) {
            c.ngay_lap_ho_so = cm.ngay_lap_ho_so;
          }
        }
        c.stage = JSON.parse(JSON.stringify(stage));
        for (const row of [...c.stage.people, ...c.stage.assets]) {
          if (row.entity_id == null) row.entity_id = nextEid++;
        }
        const pruneWarn = pruneDiagram(c);
        c.diagram.render_model =
          isTp(c) ? unsupportedRender() : fakeRenderModel(c.diagram.state);
        c.revision += 1;
        return ok({
          schema_version: SCHEMA,
          revision: c.revision,
          stage: JSON.parse(JSON.stringify(c.stage)),
          diagram: {
            state: JSON.parse(JSON.stringify(c.diagram.state)),
            render_model: c.diagram.render_model,
            warnings: pruneWarn,
          },
        });
      }
      case 'notary.workspace_create': {
        const key = payload.idempotency_key;
        if (idem[key] != null) {
          return ok({ ...workspaceData(cases[idem[key]]),
                      created: false });
        }
        const ct = (payload.case && payload.case.case_type) || 'inheritance';
        if (!['inheritance', 'two_party'].includes(ct)) {
          return fail('validation_error', `case_type la: ${ct}`);
        }
        const stage = payload.stage || {};
        if (!Array.isArray(stage.people) || !Array.isArray(stage.assets)) {
          return fail('validation_error', 'stage khong dung shape');
        }
        const ownerErr = checkOwnerPointer({ case_type: ct }, stage);
        if (ownerErr) return ownerErr;
        const fieldErrors = [];
        for (const p of stage.people) {
          if (!p.ho_ten || !String(p.ho_ten).trim()) {
            fieldErrors.push({ row_id: p.row_id, field: 'ho_ten',
                               code: 'required', message: 'bat buoc' });
          }
          if (p.entity_id != null) {
            fieldErrors.push({ row_id: p.row_id, field: 'entity_id',
                               code: 'invalid_format',
                               message: 'phai null' });
          }
        }
        if (!stage.people.length) {
          fieldErrors.push({ row_id: null, field: 'people',
                             code: 'required', message: 'can it nhat 1' });
        }
        if (!stage.assets.length) {
          fieldErrors.push({ row_id: null, field: 'assets',
                             code: 'required', message: 'can it nhat 1' });
        }
        fieldErrors.push(
          ...stageFieldErrors({ case_type: ct }, stage));
        if (fieldErrors.length) {
          return fail('stage_validation_error', 'loi field',
                      { field_errors: fieldErrors });
        }
        const stored = JSON.parse(JSON.stringify(stage));
        for (const row of [...stored.people, ...stored.assets]) {
          if (row.entity_id == null) row.entity_id = nextEid++;
        }
        const rowIds = new Set(stored.people.map((p) => p.row_id));
        // §13.6: diagram absent → server seed (owner node / 30 slot);
        // diagram co mat → validate domain + refs + owner mirror.
        let state;
        let renderAuto = false;
        if (payload.diagram && payload.diagram.state) {
          state = payload.diagram.state;
          if (state.domain !== ct) {
            return fail('diagram_domain_mismatch',
                        `domain ${state.domain} != ${ct}`,
                        { expected: ct, got: state.domain });
          }
          for (const n of state.nodes || []) {
            if (n.personId && !rowIds.has(n.personId)) {
              return fail('diagram_reference_outside_stage',
                          'personId ngoai stage', { personId: n.personId });
            }
          }
          const oid = stored.owner_row_id;
          const ownerNode = (state.nodes || []).find(
            (n) => n.id === 'owner' && !n.deleted && n.personId != null);
          if (ct === 'inheritance' && ownerNode &&
              ownerNode.personId !== oid) {
            return fail('diagram_owner_mismatch',
                        'owner node != owner_row_id',
                        { owner_row_id: oid,
                          node_person_id: ownerNode.personId });
          }
          if (ct === 'two_party') state.nodes = canonicalTwoParty(state.nodes);
          renderAuto = true;
        } else if (ct === 'two_party') {
          state = { version: 3, domain: 'two_party',
                    nodes: canonicalTwoParty([]) };
        } else {
          const pos = stored.assets.map((_, i) => i + 1);
          state = { version: 3, domain: 'inheritance', nodes: [
            { id: 'owner', personId: stored.owner_row_id,
              parentSlotIds: [], spouseSlotId: null,
              ownPositions: pos, receivePositions: [],
              hidden: false, deleted: false } ] };
        }
        const c = {
          id: nextCid++, case_type: ct,
          document_type: payload.case.document_type,
          status: 'draft', locked: false, revision: 1,
          ngay_lap_ho_so: payload.case.ngay_lap_ho_so ?? null,
          noi_niem_yet: payload.case.noi_niem_yet ?? null,
          nguoi_nhan_uy_quyen:
            payload.case.nguoi_nhan_uy_quyen ?? null,
          nguoi_nhan_uy_quyen_id:
            payload.case.nguoi_nhan_uy_quyen_id ?? null,
          noi_dung_viec: payload.case.noi_dung_viec ?? null,
          ghi_chu: payload.case.ghi_chu ?? null,
          stage: stored,
          diagram: {
            domain: ct,
            state: JSON.parse(JSON.stringify(state)),
            render_model: renderAuto ? 'auto' : null, warnings: [],
          },
        };
        cases[c.id] = c;
        idem[key] = c.id;
        return ok({ ...workspaceData(c), created: true });
      }
      case 'notary.customer_list': {
        // MIN-141 đợt 3: danh ba gia — loc theo ten/so giay to/dia chi.
        const q = String((payload && payload.query) || '').toLowerCase();
        let rows = catalog.slice();
        if (q) {
          rows = rows.filter((x) =>
            String(x.ho_ten || '').toLowerCase().includes(q) ||
            String(x.so_giay_to || '').toLowerCase().includes(q) ||
            String(x.dia_chi || '').toLowerCase().includes(q));
        }
        return ok({ customers: rows, total: rows.length },
                  { type: 'customer_list' });
      }
      case 'notary.customer_create': {
        const name = String((payload && payload.ho_ten) || '').trim();
        if (!name) {
          return fail('validation_error', 'ho_ten bat buoc');
        }
        const sgt = String((payload && payload.so_giay_to) || '')
          .trim() || null;
        let cust = sgt &&
          catalog.find((x) => x.so_giay_to === sgt);
        if (cust) {
          cust.ho_ten = name;
          return ok({ customer: cust, updated: true },
                    { type: 'customer_upsert' });
        }
        cust = {
          id: nextEid++, ho_ten: name,
          gioi_tinh: payload.gioi_tinh ?? null,
          ngay_sinh: payload.ngay_sinh ?? null,
          ngay_chet: payload.ngay_chet ?? null,
          so_giay_to: sgt,
          ngay_cap: payload.ngay_cap ?? null,
          dia_chi: payload.dia_chi ?? null,
        };
        catalog.push(cust);
        return ok({ customer: cust, updated: false },
                  { type: 'customer_upsert' });
      }
      case 'notary.diagram_evaluate': {
        if (payload.case_id == null) {
          // Draft mode (§2.1a): stage + hint case.case_type trong payload,
          // evaluated_revision null.
          if (payload.case_id === null) {
            return fail('validation_error', 'case_id null');
          }
          if (!payload.stage || !Array.isArray(payload.stage.people)) {
            return fail('validation_error', 'stage bat buoc');
          }
          const ct = (payload.case && payload.case.case_type) ||
            'inheritance';
          const state = payload.diagram && payload.diagram.state;
          if (state && state.domain && state.domain !== ct) {
            return fail('diagram_domain_mismatch',
                        `domain ${state.domain} != ${ct}`,
                        { expected: ct, got: state.domain });
          }
          if (ct === 'inheritance') {
            const oidErr = checkOwnerPointer(
              { case_type: ct }, payload.stage);
            if (oidErr) return oidErr;
          }
          const rowIds = new Set(
            payload.stage.people.map((p) => p.row_id));
          for (const n of (state && state.nodes) || []) {
            if (n.personId && !rowIds.has(n.personId)) {
              return fail('diagram_reference_outside_stage',
                          'personId ngoai stage',
                          { personId: n.personId });
            }
          }
          return ok({
            schema_version: SCHEMA,
            evaluated_revision: null,
            render_model: ct === 'two_party'
              ? unsupportedRender() : fakeRenderModel(state),
          });
        }
        const { c, err } = getCase(payload);
        if (err) return err;
        if (!supported(c)) {
          return fail('case_type_unsupported', 'chua ho tro');
        }
        const state = payload.diagram && payload.diagram.state;
        if (state && state.domain && state.domain !== c.case_type) {
          return fail('diagram_domain_mismatch',
                      `domain ${state.domain} != ${c.case_type}`,
                      { expected: c.case_type, got: state.domain });
        }
        const ids = new Set(c.stage.people.map((p) => p.row_id));
        for (const n of (state && state.nodes) || []) {
          if (n.personId && !ids.has(n.personId)) {
            return fail('diagram_reference_outside_stage',
                        'personId ngoai stage',
                        { personId: n.personId });
          }
        }
        return ok({
          schema_version: SCHEMA,
          evaluated_revision: c.revision,
          render_model: isTp(c)
            ? unsupportedRender() : fakeRenderModel(state),
        });
      }
      case 'notary.diagram_save': {
        const { c, err } = getCase(payload);
        if (err) return err;
        if (c.locked) return fail('workspace_locked', 'da khoa');
        if (!supported(c)) {
          return fail('case_type_unsupported', 'chua ho tro');
        }
        if (payload.base_revision !== c.revision) {
          return fail('workspace_conflict', 'revision khac',
                      { server_revision: c.revision });
        }
        const state = payload.diagram && payload.diagram.state;
        if (state && state.domain && state.domain !== c.case_type) {
          return fail('diagram_domain_mismatch',
                      `domain ${state.domain} != ${c.case_type}`,
                      { expected: c.case_type, got: state.domain });
        }
        const ids = new Set(c.stage.people.map((p) => p.row_id));
        for (const n of (state && state.nodes) || []) {
          if (n.personId && !ids.has(n.personId)) {
            return fail('diagram_reference_outside_stage',
                        'personId ngoai stage',
                        { personId: n.personId });
          }
        }
        // §13.4: node 'owner' (co personId) phai = owner_row_id da commit.
        const oid = c.stage.owner_row_id;
        const ownerNode = (state.nodes || []).find(
          (n) => n.id === 'owner' && !n.deleted && n.personId != null);
        if (!isTp(c) && ownerNode && ownerNode.personId !== oid) {
          return fail('diagram_owner_mismatch',
                      'owner node != owner_row_id',
                      { owner_row_id: oid ?? null,
                        node_person_id: ownerNode.personId });
        }
        c.diagram.state = JSON.parse(JSON.stringify(state));
        const pruneWarn = pruneDiagram(c);
        c.diagram.render_model =
          isTp(c) ? unsupportedRender() : fakeRenderModel(c.diagram.state);
        c.revision += 1;
        return ok({
          schema_version: SCHEMA,
          revision: c.revision,
          diagram: {
            state: JSON.parse(JSON.stringify(c.diagram.state)),
            render_model: c.diagram.render_model,
            warnings: pruneWarn,
          },
        });
      }
      case 'notary.intake_analyze': {
        if (payload.case_id !== undefined) {
          if (payload.case_id === null) {
            return fail('validation_error', 'case_id null');
          }
          const { err } = getCase(payload);
          if (err) return err;
        }
        const sid = payload.sources[0].source_id;
        return ok({
          schema_version: SCHEMA,
          suggestions: [{
            suggestion_id: crypto.randomUUID(),   // moi lan mot id (backend sinh)
            source_id: sid,
            target: 'person',
            fields: {
              ho_ten: { raw_value: 'NGUOI MOI', normalized_value: 'Người Mới',
                        observation_state: 'normalized', confidence: null,
                        source_refs: [] },
              ngay_sinh: { raw_value: '1970', normalized_value: '1970',
                           observation_state: 'normalized', confidence: null,
                           source_refs: [] },
            },
            warnings: [],
          }],
          errors: [],
        });
      }
      case 'notary.word_export_options': {
        const { c, err } = getCase(payload);
        if (err) return err;
        if (isTp(c)) {
          return fail('case_type_unsupported', 'two_party khong word');
        }
        return ok({
          schema_version: SCHEMA,
          documents: [
            { document_key: 'khai_nhan_di_san',
              display_name: 'Văn bản khai nhận di sản',
              ready: true, block_reason: null },
            { document_key: 'niem_yet', display_name: 'Thông báo niêm yết',
              ready: false, block_reason: 'word.template_missing' },
          ],
        });
      }
      case 'notary.word_export_batch': {
        const { c, err } = getCase(payload);
        if (err) return err;
        if (isTp(c)) {
          return fail('case_type_unsupported', 'two_party khong word');
        }
        const docs = payload.document_keys.map((k) => ({
          document_key: k, display_name: k,
          status: k === 'niem_yet' ? 'failed' : 'saved',
          actual_filename: k === 'niem_yet' ? null : `${k}_HS-42.docx`,
          output_file: null,
          error: k === 'niem_yet'
            ? { code: 'word.template_missing', message: 'no template' }
            : null,
        }));
        const failed = docs.filter((d) => d.status === 'failed')
          .map((d) => d.document_key);
        return ok({
          schema_version: SCHEMA,
          destination: payload.destination,
          documents: docs,
          breakdown: { succeeded: docs.filter((d) => d.status === 'saved')
                                       .map((d) => d.document_key),
                       failed, skipped: [] },
        }, { partial: failed.length > 0 });
      }
      default:
        return fail('command_unknown', `khong biet ${command}`);
    }
  }
  return { run, calls, cases };
}

function seedCases(...names) {
  const cases = {};
  for (const n of names) {
    const doc = loadFixture(n);
    Object.assign(cases, doc.cases);
  }
  return cases;
}

function makeModel(seed) {
  const client = fakeClient(seed);
  const model = M.createModel({ client, uuid });
  return { model, client };
}

// ---------- load workspace ----------

test('openCase: tai workspace ready — stage/diagram/revision/mock banner', async () => {
  const { model } = makeModel(seedCases('ready'));
  const r = await model.openCase(42);
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.caseId, 42);
  assert.equal(s.revision, 7);
  assert.equal(s.stage.people.length, 4);
  assert.equal(s.stage.assets.length, 2);
  // v2: stage inheritance mang owner_row_id; diagram state v3 + domain.
  assert.equal(s.stage.owner_row_id,
               '11111111-1111-4111-8111-111111111111');
  assert.equal(s.diagram.version, 3);
  assert.equal(s.diagram.domain, 'inheritance');
  assert.equal(s.diagram.nodes.length, 4);
  assert.equal(s.backendMode, 'mock');
  assert.equal(model.mockBanner(), 'Dữ liệu mô phỏng');
  assert.equal(s.locked, false);
  assert.equal(s.unsupported, false);
  // khong co field `confirmed` hay v1 flag nao tren wire/state
  const raw = JSON.stringify(s);
  assert.equal(raw.includes('"confirmed"'), false);
  assert.equal(raw.includes('isLandOwner'), false);
  assert.equal(raw.includes('willReceive'), false);
  assert.equal(raw.includes('is_primary'), false);
});

test('openCase: two_party — domain/state 30 slot canonical, word_export off', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  const r = await model.openCase(48);
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(model.caseType(), 'two_party');
  assert.equal(model.diagramDomain(), 'two_party');
  assert.equal('owner_row_id' in s.stage, false);
  assert.equal(s.diagram.version, 3);
  assert.deepEqual(s.diagram.nodes.map((n) => n.id), TP_IDS);
  assert.equal(s.renderModel.status, 'unsupported');
  assert.equal(s.capabilities.diagram, true);
  assert.equal(s.capabilities.word_export, false);
});

test('openCase: backend_mode real thi khong co banner mo phong', async () => {
  const client = { run: async (cmd) => {
    if (cmd === 'notary.workspace_get') {
      const base = fakeClient(seedCases('empty'));
      const r = await base.run(cmd, { case_id: 43 });
      r.data.backend_mode = 'real';
      return r;
    }
    return { ok: false, error: { code: 'command_unknown' } };
  } };
  const model = M.createModel({ client, uuid });
  await model.openCase(43);
  assert.equal(model.state.backendMode, 'real');
  assert.equal(model.mockBanner(), null);
});

test('openCase: case_not_found → status error co code', async () => {
  const { model } = makeModel(seedCases('ready'));
  const r = await model.openCase(999);
  assert.equal(r.ok, false);
  assert.equal(model.state.status, 'error');
  assert.equal(model.state.error.code, 'case_not_found');
});

test('openCase: engine_unavailable → status unavailable', async () => {
  const client = { run: async () => ({ ok: false, error: {
    code: 'engine_unavailable', message: 'sidecar chet',
    retryable: true } }) };
  const model = M.createModel({ client, uuid });
  await model.openCase(42);
  assert.equal(model.state.status, 'unavailable');
});

test('openCase: empty fixture → stage rong nhung van ready', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.stage.people.length, 0);
  assert.equal(s.stage.assets.length, 0);
  assert.equal(s.stage.owner_row_id, null);       // key co mat, gia tri null
  assert.equal(model.isStageEmpty(), true);
  assert.equal(s.renderModel, null);              // chua tung evaluate
});

test('openCase: locked → status locked, write bi tu choi o model', async () => {
  const { model, client } = makeModel(seedCases('locked'));
  await model.openCase(44);
  const s = model.state;
  assert.equal(s.status, 'locked');
  assert.equal(s.locked, true);
  assert.equal(model.canWrite(), false);
  // commit tren case locked: model khong gui command, tra loi locked
  const before = client.calls.length;
  const r = await model.commitStage();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_locked');
  assert.equal(client.calls.length, before);   // khong goi wire
});

test('openCase: case_type ngoai CASE_TYPES → unsupported', async () => {
  const { model } = makeModel(seedCases('unsupported'));
  await model.openCase(45);
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.unsupported, true);
  assert.equal(model.canWrite(), false);
  assert.equal(s.capabilities.diagram, false);
  assert.equal(s.capabilities.word_export, false);
});

// ---------- dirty Stage + commit ----------

test('addPerson/setOwnerRow/update/remove → stageDirty; commit reset', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.equal(model.state.stageDirty, false);

  const row = model.addPerson({ ho_ten: 'Người Mẫu Z' });
  assert.ok(row.row_id);
  assert.match(row.row_id, /^[0-9a-f-]{36}$/);   // uuid4 shape
  assert.equal(row.entity_id, null);
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.stage.people.length, 1);

  // v2: commit inheritance bat buoc owner_row_id — chon owner.
  assert.equal(model.setOwnerRow(row.row_id), true);
  assert.equal(model.state.stage.owner_row_id, row.row_id);

  model.updatePersonField(row.row_id, 'ngay_sinh', '1999');
  assert.equal(model.state.stage.people[0].ngay_sinh, '1999');

  const r = await model.commitStage();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.stageDirty, false);
  assert.equal(s.revision, 2);                   // 1 → 2
  assert.equal(s.stage.people[0].entity_id, 900); // backend gan entity_id
  // payload gui di co base_revision + toan bo stage snapshot + owner_row_id
  const sent = client.calls.at(-1).payload;
  assert.equal(sent.base_revision, 1);
  assert.equal(sent.stage.people.length, 1);
  assert.equal(sent.stage.owner_row_id, row.row_id);

  // xoa dong owner → pointer ve null + node owner mirror giai phong
  model.removeStageRow(row.row_id);
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.stage.people.length, 0);
  assert.equal(model.state.stage.owner_row_id, null);
});

test('commitStage: thieu owner_row_id → workspace_owner_required, draft giu nguyen', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  model.addPerson({ ho_ten: 'Chưa chọn owner' });
  const r = await model.commitStage();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_owner_required');
  assert.equal(model.state.stageDirty, true);    // van dirty — chua commit
  assert.equal(model.state.revision, 1);
});

test('commitStage: stage_validation_error → fieldErrors theo row_id, stage giu draft', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const row = model.addPerson({ ho_ten: '' });   // rong → required
  model.setOwnerRow(row.row_id);                  // pointer hop le → den
                                                // duoc field check
  const r = await model.commitStage();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'stage_validation_error');
  const s = model.state;
  assert.equal(s.stageDirty, true);              // van dirty — chua commit
  assert.equal(s.revision, 1);                   // revision khong doi
  assert.equal(s.stage.people.length, 1);        // draft con nguyen
  const errs = model.fieldErrorsFor(row.row_id);
  assert.equal(errs.length, 1);
  assert.equal(errs[0].field, 'ho_ten');
  // sua field → loi cua field do duoc gỡ
  model.updatePersonField(row.row_id, 'ho_ten', 'Đã sửa');
  assert.equal(model.fieldErrorsFor(row.row_id).length, 0);
});

test('commitStage: asset_limit — dong thu 4 bi tu choi o client', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.ok(model.addAsset({ so_serial: 'MM000001' }));
  assert.ok(model.addAsset({ so_serial: 'MM000002' }));
  assert.ok(model.addAsset({ so_serial: 'MM000003' }));
  assert.equal(model.addAsset({ so_serial: 'MM000004' }), null);  // MAX_ASSETS=3
  assert.equal(model.state.stage.assets.length, 3);
});

test('moveAsset: doi thu tu = doi nghia vi tri, clamp index', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const [a1, a2] = model.state.stage.assets.map((a) => a.row_id);
  assert.equal(model.moveAsset(a2, 0), true);
  assert.deepEqual(model.state.stage.assets.map((a) => a.row_id),
                   [a2, a1]);
  // clamp: index am → 0; qua dai → cuoi
  assert.equal(model.moveAsset(a2, -5), true);   // da o 0 — no-op
  assert.equal(model.moveAsset(a1, 99), true);   // → cuoi
  assert.deepEqual(model.state.stage.assets.map((a) => a.row_id),
                   [a2, a1]);
  // moveAsset KHONG cham diagram — dau chon giu so vi tri nguyen.
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(owner.ownPositions, [1, 2]);
});

test('setOwnerRow: set/unset pointer + mirror node owner; reject row la', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const s = model.state;
  const other = s.stage.people[1].row_id;
  assert.equal(model.setOwnerRow(other), true);
  assert.equal(s.stage.owner_row_id, other);
  const owner = s.diagram.nodes.find((n) => n.id === 'owner');
  assert.equal(owner.personId, other);           // mirror theo pointer
  assert.equal(s.stageDirty, true);
  assert.equal(s.diagramDirty, true);
  // unset → pointer null + mirror null
  assert.equal(model.setOwnerRow(null), true);
  assert.equal(s.stage.owner_row_id, null);
  assert.equal(owner.personId, null);
  // row khong thuoc stage → reject, pointer khong doi
  assert.equal(model.setOwnerRow('99999999-9999-4999-8999-999999999999'),
               false);
  assert.equal(s.stage.owner_row_id, null);
});

test('setOwnerRow: no-op tren two_party', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  assert.equal(model.setOwnerRow('x'), false);
  assert.equal('owner_row_id' in model.state.stage, false);
});

test('commitStage giu draft diagram dirty: khong mat assignment, prune personId ngoai stage moi', async () => {
  // Review MIN-112: commit stage khong duoc xoa ngam draft diagram —
  // assignment chua luu phai con, diagramDirty giu true.
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  assert.equal(s.diagram.nodes.length, 2);      // owner, spouse

  // Draft dirty: gan E (dang o Pool) vao slot moi.
  const node = model.addSlot();
  const e = s.committed.people.find((p) => p.ho_ten === 'Người Mẫu E');
  assert.ok(model.assignPerson(node.id, e.row_id));
  assert.equal(s.diagramDirty, true);
  // Gia lap tham chieu stale trong draft (personId khong con trong stage
  // committed sau commit) — server _prune_diagram se bo no.
  const staleNode = model.addSlot();
  staleNode.personId = '99999999-9999-4999-8999-999999999999';
  const beforeCount = s.diagram.nodes.length;

  // Stage dirty bang edit field (khong xoa dong) → commit.
  model.updatePersonField(s.stage.people[0].row_id, 'ho_ten',
                          'Người Mẫu A đổi');
  const r = await model.commitStage();
  assert.equal(r.ok, true);
  assert.equal(s.revision, 6);                    // 5 → 6
  assert.equal(s.stageDirty, false);
  assert.equal(s.diagramDirty, true);             // draft KHONG bi xoa
  assert.equal(s.diagram.nodes.length, beforeCount); // node giu nguyen
  // assignment hop le con nguyen
  const kept = s.diagram.nodes.find((n) => n.id === node.id);
  assert.equal(kept.personId, e.row_id);
  // assignment cu tren owner/spouse con nguyen (khong bi reset bang
  // server state — server state giong vi khong prune gi them)
  assert.equal(
    s.diagram.nodes.find((n) => n.id === 'owner').personId,
    '11111111-1111-4111-8111-111111111111');
  // tham chieu stale bi prune (mirror _prune_diagram client-side)
  assert.equal(
    s.diagram.nodes.find((n) => n.id === staleNode.id).personId, null);
  // baseline committed nap theo server (2 node, khong co slot draft)
  assert.equal(s.committedDiagram.nodes.length, 2);
  // renderModel/ref moi tu commit van cap nhat
  assert.ok(s.renderModel);
  // evaluatedRevision giu nguyen (null — chua evaluate) de badge stale
  // co the bao: rm hien thi mo ta committed, chua mo ta draft.
  assert.equal(s.evaluatedRevision, null);
});

test('commitStage khi diagram sach: nap state server + evaluatedRevision = revision moi', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  assert.equal(s.diagramDirty, false);
  model.updatePersonField(s.stage.people[0].row_id, 'ho_ten', 'Đổi tên');
  const r = await model.commitStage();
  assert.equal(r.ok, true);
  assert.equal(s.diagramDirty, false);
  assert.equal(s.revision, 6);
  // rm tu commit evaluate tren stage@6 → khong con "stale"
  assert.equal(s.evaluatedRevision, 6);
});

test('commitStage voi draft dirty: xoa person khoi stage → draft prune personId do', async () => {
  // removeStageRow da mirror prune ngay luc xoa; commit-time prune la
  // lop thu hai khi server tra committed stage khac draft (dedupe/merge).
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  const b = s.committed.people.find((p) => p.ho_ten === 'Người Mẫu B');
  // draft dirty bang flag hidden tren node spouse
  assert.ok(model.setNodeFlag('spouse', 'hidden', true));
  // xoa B khoi stage draft → mirror prune spouse.personId ngay
  model.removeStageRow(b.row_id);
  const r = await model.commitStage();
  assert.equal(r.ok, true);
  assert.equal(s.diagramDirty, true);             // draft van chua luu
  assert.equal(
    s.diagram.nodes.find((n) => n.id === 'spouse').personId, null);
  // flag hidden=true (thay doi draft) van giu — draft khong bi thay
  // bang ban server
  assert.equal(
    s.diagram.nodes.find((n) => n.id === 'spouse').hidden, true);
  // B khong con trong committed stage moi
  assert.equal(
    s.committed.people.some((p) => p.row_id === b.row_id), false);
});

test('commitStage: workspace_conflict → status conflict + server_revision', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'X' });
  // gia lap server revision doi (tab khac da ghi)
  client.cases[42].revision = 9;
  const r = await model.commitStage();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_conflict');
  assert.equal(model.state.status, 'conflict');
  assert.equal(model.state.conflict.server_revision, 9);
  // draft van con — nguoi dung chon "giu ban nhap"
  assert.equal(model.state.stage.people.length, 5);
});

test('resolveConflict: reload tai ban moi, keep giu draft de sao chep', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'Nháp giữ' });
  client.cases[42].revision = 9;
  await model.commitStage();
  assert.equal(model.state.status, 'conflict');

  // keep → tro lai ready, draft nguyen, stale flag
  model.resolveConflict('keep');
  assert.equal(model.state.status, 'ready');
  assert.equal(model.state.stale, true);
  assert.equal(model.state.stage.people.length, 5);

  // conflict lai → reload → draft bi thay bang ban server moi
  const r2 = await model.commitStage();
  assert.equal(r2.ok, false);
  await model.resolveConflict('reload');
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.revision, 9);
  assert.equal(s.stage.people.length, 4);        // nhap mat
  assert.equal(s.stageDirty, false);
  assert.equal(s.stale, false);
});

// ---------- derived Pool ----------

test('pool = committed Stage − personId dang gan tren draft Diagram', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  // fixture: 3 nguoi commit, 2 nguoi gan (owner+spouse) → pool 1 nguoi (E)
  const pool = model.pool();
  assert.equal(pool.people.length, 1);
  assert.equal(pool.people[0].ho_ten, 'Người Mẫu E');
  // MIN-136: tai san KHONG xuong pool (khong co flow gan tai san len
  // node — diagram chi tham chieu vi tri own/receivePositions).

  // bo gan spouse → nguoi do quay ve pool
  model.assignPerson('spouse', null);
  assert.equal(model.pool().people.length, 2);
});

test('pool: person draft chua commit KHONG xuat hien trong pool', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  model.addPerson({ ho_ten: 'Draft chưa commit' });
  assert.equal(model.pool().people.length, 0);
  assert.equal(model.isStageEmpty(), false);
});

test('assignPerson: gan vao node → ra khoi pool; node khac bi clear de tranh duplicate', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const e = model.state.committed.people
    .find((p) => p.ho_ten === 'Người Mẫu E');
  model.assignPerson('owner', e.row_id);   // owner dang la A → move
  const nodes = model.state.diagram.nodes;
  const owners = nodes.filter((n) => n.personId === e.row_id);
  assert.equal(owners.length, 1);               // chi 1 node giu E
  assert.equal(owners[0].id, 'owner');
  // stage.owner_row_id theo mirror — pointer = E
  assert.equal(model.state.stage.owner_row_id, e.row_id);
  // A tro lai pool
  assert.ok(model.pool().people.some((p) => p.ho_ten === 'Người Mẫu A'));
});

test('assignPerson owner: rowId dang o node khac → clear node cu', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const e = model.state.committed.people
    .find((p) => p.ho_ten === 'Người Mẫu E');
  // E len child truoc, sau do lam owner → child phai duoc giai phong.
  const child = model.addSlot();
  model.assignPerson(child.id, e.row_id);
  assert.equal(model.assignPerson('owner', e.row_id), true);
  const nodes = model.state.diagram.nodes;
  assert.equal(nodes.filter((n) => n.personId === e.row_id).length, 1);
  assert.equal(nodes.find((n) => n.id === child.id).personId, null);
  assert.equal(model.state.stage.owner_row_id, e.row_id);
});

// ---------- draft Diagram (v3) ----------

test('diagram draft: addSlot/togglePosition/removeNode → diagramDirty; save reset', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.equal(model.state.diagramDirty, false);

  const node = model.addSlot();
  assert.ok(node.id);
  assert.equal(node.personId, null);
  // v3 node shape — khong con isLandOwner/willReceive
  assert.equal('isLandOwner' in node, false);
  assert.equal('willReceive' in node, false);
  assert.deepEqual(node.ownPositions, []);
  assert.deepEqual(node.receivePositions, []);
  assert.equal(model.state.diagramDirty, true);

  model.setNodeFlag(node.id, 'hidden', true);
  assert.equal(node.hidden, true);
  // NODE_BOOL_FIELDS chi con hidden/deleted — flag v1 bi tu choi
  assert.equal(model.setNodeFlag(node.id, 'isLandOwner', true), false);
  assert.equal(model.setNodeFlag(node.id, 'willReceive', true), false);

  const r = await model.saveDiagram();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.diagramDirty, false);
  assert.equal(s.revision, 2);                    // save tang revision
  const sent = client.calls.at(-1).payload;
  assert.equal(sent.base_revision, 1);
  assert.equal(sent.diagram.state.version, 3);    // v3 tren wire
  assert.equal(sent.diagram.state.domain, 'inheritance');

  model.removeNode(node.id);                      // → deleted:true
  const gone = model.state.diagram.nodes
    .find((n) => n.id === node.id);
  assert.equal(gone.deleted, true);
  assert.equal(model.state.diagramDirty, true);
});

test('toggleNodePosition: own/receive doc lap, dedupe, chan ngoai {1..3}', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const spouse = model.state.diagram.nodes.find((n) => n.id === 'spouse');
  assert.deepEqual(spouse.receivePositions, [1, 2]);
  // tat pos 2
  assert.equal(model.toggleNodePosition('spouse', 'receive', 2), true);
  assert.deepEqual([...spouse.receivePositions].sort(), [1]);
  // bat pos 3 — duoc phep ca khi chua co asset 3 (server prune sau)
  assert.equal(model.toggleNodePosition('spouse', 'receive', 3), true);
  assert.deepEqual([...spouse.receivePositions].sort(), [1, 3]);
  // own doc lap — khong bi anh huong
  assert.deepEqual(spouse.ownPositions, []);
  assert.equal(model.toggleNodePosition('spouse', 'own', 3), true);
  assert.deepEqual(spouse.ownPositions, [3]);
  // dedupe: bat lai pos da co → tat (khong nhan doi)
  assert.equal(model.toggleNodePosition('spouse', 'own', 3), true);
  assert.deepEqual(spouse.ownPositions, []);
  // chan tham so la
  assert.equal(model.toggleNodePosition('spouse', 'own', 4), false);
  assert.equal(model.toggleNodePosition('spouse', 'bogus', 1), false);
  assert.equal(model.toggleNodePosition('khong-co', 'own', 1), false);
});

test('toggleNodePosition/setNodeRelation/addSlot: no-op tren two_party', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  assert.equal(model.addSlot(), null);          // 30 slot canonical co dinh
  assert.equal(model.toggleNodePosition('p1', 'own', 1), false);
  assert.equal(model.setNodeRelation('p1', { spouseSlotId: 'p2' }), false);
  assert.equal(model.state.diagramDirty, false);
});

test('applyAssignDefaults: owner → ownPositions het; node khac → receivePositions het', async () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();                          // MIN-136: 1 node owner
  const a = model.addPerson({ ho_ten: 'Owner' });
  const b = model.addPerson({ ho_ten: 'Heir' });
  model.addAsset({ so_serial: 'MM000001' });
  model.addAsset({ so_serial: 'MM000002' });
  // Gan owner → ownPositions default [1,2], receive giu rong
  model.assignPerson('owner', a.row_id);
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(owner.ownPositions, [1, 2]);
  assert.deepEqual(owner.receivePositions, []);
  // Slot thua ke khac → receivePositions default [1,2]
  const sp = model.addSlot();
  model.assignPerson(sp.id, b.row_id);
  const spouse = model.state.diagram.nodes.find((n) => n.id === sp.id);
  assert.deepEqual(spouse.receivePositions, [1, 2]);
  // Mang explicit khong bi ghi de: tat 1 chip roi gan lai → giu explicit
  model.toggleNodePosition(sp.id, 'receive', 2);
  const c = model.addPerson({ ho_ten: 'C' });
  const kid = model.addSlot();
  model.assignPerson(kid.id, c.row_id);
  assert.deepEqual(model.state.diagram.nodes
    .find((n) => n.id === sp.id).receivePositions, [1]);
});

test('saveDiagram: workspace_conflict → status conflict', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.setNodeFlag('owner', 'hidden', true);    // dirty diagram
  client.cases[42].revision = 12;
  const r = await model.saveDiagram();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_conflict');
  assert.equal(model.state.status, 'conflict');
  assert.equal(model.state.conflict.server_revision, 12);
});

test('saveDiagram: owner mirror lech → diagram_owner_mismatch passthrough', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  // Gia lap draft lech mirror (khong qua setter — UI khong bao gio tao
  // trang thai nay, nhung server van la chot cuoi).
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  const other = model.state.stage.people[1].row_id;
  model.state.diagram.nodes.find((n) => n.id === 'spouse').personId = null;
  owner.personId = other;
  model.state.diagramDirty = true;
  const r = await model.saveDiagram();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'diagram_owner_mismatch');
});

test('saveDiagram: domain mismatch → diagram_domain_mismatch', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.diagram = { version: 3, domain: 'two_party',
    nodes: TP_IDS.map((id) => ({ id, personId: null,
                                hidden: false, deleted: false })) };
  model.state.diagramDirty = true;
  const r = await model.saveDiagram();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'diagram_domain_mismatch');
});

test('saveDiagram two_party: persist + revision bump', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  model.assignPerson('p3', model.state.stage.people[0].row_id);
  const r = await model.saveDiagram();
  assert.equal(r.ok, true);
  assert.equal(model.state.revision, 3);          // 2 → 3
  assert.equal(model.state.renderModel.status, 'unsupported');
  assert.deepEqual(model.state.diagram.nodes.map((n) => n.id), TP_IDS);
});

test('evaluateDiagram: cap nhat renderModel, KHONG doi revision/persist', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const node = model.addSlot();
  model.setNodeFlag(node.id, 'hidden', true);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.revision, 1);                    // read-only — khong tang
  assert.equal(s.evaluatedRevision, 1);
  assert.ok(s.renderModel);
  assert.equal(s.renderModel.engineVersion, 2);
  assert.equal(s.diagramDirty, true);             // draft van chua luu
});

test('diagram tren case locked: evaluate duoc phep (read-only), save bi chan', async () => {
  const { model } = makeModel(seedCases('locked'));
  await model.openCase(44);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);                       // read-only qua duoc
  const r2 = await model.saveDiagram();
  assert.equal(r2.ok, false);
  assert.equal(r2.error.code, 'workspace_locked');
});

// ---------- intake / word (thin, cho MIN-112 wire UI) ----------

test('intakeAnalyze → suggestions; acceptSuggestion tao draft row, khong auto-commit', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const r = await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text',
      text: 'Ong Nguyen Van Mau, sinh 1970' }]);
  assert.equal(r.ok, true);
  assert.equal(model.state.suggestions.length, 1);
  // suggestion KHONG tu vao stage
  assert.equal(model.state.stage.people.length, 0);

  const sug = model.state.suggestions[0];
  assert.equal(sug.fields.ho_ten.normalized_value, 'Người Mới');
  const row = model.acceptSuggestion(sug.suggestion_id);
  assert.equal(row.ho_ten, 'Người Mới');
  assert.equal(model.state.stage.people.length, 1);
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.suggestions.length, 0);
});

test('wordExportOptions + exportWord: options/result theo tung van ban', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const o = await model.loadWordOptions();
  assert.equal(o.ok, true);
  assert.equal(model.state.wordOptions.length, 2);
  const blocked = model.state.wordOptions
    .find((d) => d.document_key === 'niem_yet');
  assert.equal(blocked.ready, false);
  assert.equal(blocked.block_reason, 'word.template_missing');

  const r = await model.exportWord(
    ['khai_nhan_di_san', 'niem_yet'],
    { path: 'D:/out', scope: 'machine_local', is_dir: true });
  assert.equal(r.ok, true);
  assert.equal(r.partial, true);
  const res = model.state.wordResult;
  assert.equal(res.breakdown.succeeded.length, 1);
  assert.equal(res.breakdown.failed.length, 1);
});

test('word tren two_party: server tu choi case_type_unsupported', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  const o = await model.loadWordOptions();
  assert.equal(o.ok, false);
  assert.equal(o.error.code, 'case_type_unsupported');
});

// ---------- locked: draft mutations bi chan (defense-in-depth) ----------

test('locked case: moi mutation draft la no-op — addPerson/addAsset/update/remove/diagram', async () => {
  const { model } = makeModel(seedCases('locked'));
  await model.openCase(44);
  const s = model.state;
  assert.equal(s.status, 'locked');
  assert.equal(model.canWrite(), false);

  // Stage mutations — tra null, khong doi draft, khong dirty
  assert.equal(model.addPerson({ ho_ten: 'X' }), null);
  assert.equal(model.addAsset({ so_serial: 'S1' }), null);
  assert.equal(s.stage.people.length, 2);
  assert.equal(s.stage.assets.length, 1);
  const pid = s.stage.people[0].row_id;
  model.updatePersonField(pid, 'ho_ten', 'TEN MOI');
  assert.equal(s.stage.people[0].ho_ten, 'Người Mẫu A');
  model.updateAssetField(s.stage.assets[0].row_id, 'dia_chi', 'DC MOI');
  assert.notEqual(s.stage.assets[0].dia_chi, 'DC MOI');
  model.removeStageRow(pid);
  assert.equal(s.stage.people.length, 2);
  assert.equal(model.setOwnerRow(s.stage.people[1].row_id), false);
  assert.equal(model.moveAsset(s.stage.assets[0].row_id, 0), false);
  assert.equal(s.stageDirty, false);

  // Diagram mutations — tra false/null, khong dirty
  assert.equal(model.addSlot(), null);
  assert.equal(model.assignPerson('owner', null), false);
  assert.equal(model.setNodeFlag('owner', 'hidden', true), false);
  assert.equal(model.toggleNodePosition('owner', 'own', 1), false);
  assert.equal(model.setNodeRelation('owner', { spouseSlotId: null }),
    false);
  assert.equal(model.removeNode('owner'), false);
  const owner = s.diagram.nodes.find((n) => n.id === 'owner');
  assert.equal(owner.deleted, false);
  assert.equal(owner.personId, '11111111-1111-4111-8111-111111111111');
  assert.equal(s.diagramDirty, false);
});

test('unsupported case: mutation draft cung la no-op', async () => {
  const { model } = makeModel(seedCases('unsupported'));
  await model.openCase(45);
  assert.equal(model.state.unsupported, true);
  assert.equal(model.addPerson({ ho_ten: 'X' }), null);
  assert.equal(model.addAsset(), null);
  assert.equal(model.addSlot(), null);
  assert.equal(model.state.stageDirty, false);
  assert.equal(model.state.diagramDirty, false);
});

// ---------- applyWorkspace reset aux state (khong leak giua case) ----------

test('openCase(B) sau openCase(A) co aux state → moi aux state sach', async () => {
  const { model, client } = makeModel(seedCases('empty', 'ready'));
  await model.openCase(43);
  // tao aux state tren case A: suggestion + wordOptions + renderModel
  // (evaluatedRevision) + notice (commit ok) + error (commit bi locked).
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'abc' }]);
  assert.equal(model.state.suggestions.length, 1);
  await model.loadWordOptions();
  assert.ok(model.state.wordOptions.length > 0);
  await model.evaluateDiagram();
  assert.equal(model.state.evaluatedRevision, 1);
  const p = model.addPerson({ ho_ten: 'Nháp A' });
  model.setOwnerRow(p.row_id);
  const rc = await model.commitStage();
  assert.equal(rc.ok, true);
  assert.equal(model.state.notice, 'Đã cập nhật Stage');
  // server khoa case → commit tiep nhan workspace_locked → state.error
  client.cases[43].locked = true;
  model.updatePersonField(
    model.state.stage.people[0].row_id, 'ho_ten', 'Sửa lại');
  const rl = await model.commitStage();
  assert.equal(rl.ok, false);
  assert.equal(model.state.error.code, 'workspace_locked');
  assert.equal(model.state.status, 'locked');

  // mo case khac → toan bo aux state phai sach
  const r = await model.openCase(42);
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.locked, false);
  assert.equal(s.caseId, 42);
  assert.deepEqual(s.suggestions, []);
  assert.deepEqual(s.intakeErrors, []);
  assert.equal(s.intakePartial, false);
  assert.equal(s.intakeBusy, false);
  assert.equal(s.wordOptions, null);
  assert.equal(s.wordResult, null);
  assert.equal(s.wordBusy, false);
  assert.equal(s.evaluatedRevision, null);
  assert.equal(s.conflict, null);
  assert.equal(s.notice, null);
  assert.equal(s.error, null);
  assert.equal(s.busy, null);
  assert.equal(s.stageDirty, false);
  assert.equal(s.diagramDirty, false);
  assert.equal(s.stage.people.length, 4);   // stage cua case 42
});

test('acceptSuggestion tren case locked → null, suggestion van con cho review', async () => {
  const { model, client } = makeModel(seedCases('empty', 'locked'));
  await model.openCase(43);
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'abc' }]);
  assert.equal(model.state.suggestions.length, 1);
  client.cases[43].locked = true;
  // day case sang locked qua mot write that bai
  model.updatePersonField('x', 'ho_ten', 'y');   // no-op nhung khong loi
  model.addPerson({ ho_ten: 'tmp' });
  const r = await model.commitStage();
  assert.equal(r.error.code, 'workspace_locked');
  assert.equal(model.canWrite(), false);
  const sugId = model.state.suggestions[0].suggestion_id;
  assert.equal(model.acceptSuggestion(sugId), null);
  assert.equal(model.state.suggestions.length, 1);
});

// ---------- misc ----------

test('hasUnsaved = stageDirty || diagramDirty', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  assert.equal(model.hasUnsaved(), false);
  model.addPerson({ ho_ten: 'x' });
  assert.equal(model.hasUnsaved(), true);
});

test('onChange: subscriber duoc goi sau mutation/load', async () => {
  const { model } = makeModel(seedCases('empty'));
  let n = 0;
  model.subscribe(() => { n += 1; });
  await model.openCase(43);
  const afterLoad = n;
  assert.ok(afterLoad >= 2);          // loading + ready
  model.addPerson({ ho_ten: 'x' });
  assert.ok(n > afterLoad);
});

test('model khong depend DOM: module load duoc trong node (khong window)', () => {
  assert.ok(M.createModel);
  assert.equal(typeof M.createModel, 'function');
});

// ---------- MIN-112: intake/word wiring day du ----------

test('intakeAnalyze: lan chay sau them suggestion LEN DAU, khong xoa ngam cu', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'lan 1' }]);
  const firstId = model.state.suggestions[0].suggestion_id;
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'lan 2' }]);
  assert.equal(model.state.suggestions.length, 2);
  // ket qua moi nhat dung dau danh sach (plan §13 — them len tren)
  assert.notEqual(model.state.suggestions[0].suggestion_id, firstId);
  assert.equal(model.state.suggestions[1].suggestion_id, firstId);
});

test('intakeAnalyze: opts passthrough (onJob cho progress/cancel); user_canceled → notice khong phai error', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  let gotJob = null;
  const orig = client.run.bind(client);
  client.run = async (cmd, payload, opts) => {
    if (opts && opts.onJob) opts.onJob({ job_id: 'j_intake_9' });
    return orig(cmd, payload);
  };
  await model.intakeAnalyze(
    [{ source_id: crypto.randomUUID(), kind: 'text', text: 'x' }],
    { onJob: (j) => { gotJob = j.job_id; } });
  assert.equal(gotJob, 'j_intake_9');   // dialog can job_id de cancel
  // user_canceled: khong phai loi — giu suggestion cu, hien notice
  client.run = async () => ({ ok: false, error: {
    code: 'user_canceled', message: 'nguoi dung huy', retryable: false } });
  const before = model.state.suggestions.length;
  const r = await model.intakeAnalyze(
    [{ source_id: crypto.randomUUID(), kind: 'text', text: 'y' }]);
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'user_canceled');
  assert.equal(model.state.error, null);
  assert.equal(model.state.notice, 'Đã hủy phân tích');
  assert.equal(model.state.suggestions.length, before);
  assert.equal(model.state.intakeBusy, false);
});

test('intakeAnalyze: loi that → state.error; intakeErrors tich luy tu data.errors', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  client.run = async () => ({ ok: false, error: {
    code: 'engine_not_installed', message: 'thieu OCR', retryable: false } });
  const r = await model.intakeAnalyze(
    [{ source_id: crypto.randomUUID(), kind: 'image',
       file_ref: { file_token: 't' } }]);
  assert.equal(r.ok, false);
  assert.equal(model.state.error.code, 'engine_not_installed');
  assert.equal(model.state.intakeBusy, false);
});

test('exportWord: opts passthrough; word_batch_failed → wordResult normalized per-doc', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  let gotJob = null;
  const orig = client.run.bind(client);
  client.run = async (cmd, payload, opts) => {
    if (opts && opts.onJob) opts.onJob({ job_id: 'j_word_1' });
    return orig(cmd, payload);
  };
  await model.exportWord(['khai_nhan_di_san'],
    { file_token: 't-dir' }, { onJob: (j) => { gotJob = j.job_id; } });
  assert.equal(gotJob, 'j_word_1');

  // all-failed: error.details.documents (dang compact) → normalize thanh
  // document rows day du de UI render thong nhat.
  client.run = async () => ({ ok: false,
    job: { status: 'failed' },
    error: { code: 'word_batch_failed', message: 'tat ca loi',
             retryable: true, next_action: 'retry',
             details: { documents: [
               { document_key: 'niem_yet', code: 'word.template_missing',
                 message: 'chua co template' } ] } } });
  const r = await model.exportWord(['niem_yet'], { file_token: 't' });
  assert.equal(r.ok, false);
  const res = model.state.wordResult;
  assert.ok(res && res.documents, 'wordResult.documents phai co');
  assert.equal(res.documents[0].document_key, 'niem_yet');
  assert.equal(res.documents[0].status, 'failed');
  assert.equal(res.documents[0].error.code, 'word.template_missing');
});

// ---------- MIN-112 review: unsaved transition + dedupe suggestion ----------

test('onUnsavedChange: emit dung transition dirty→clean, promise rejection khong sap emit', async () => {
  const seen = [];
  const client = fakeClient(seedCases('empty'));
  const model = M.createModel({ client, uuid,
    onUnsavedChange: (d) => { seen.push(d); } });
  await model.openCase(43);
  assert.deepEqual(seen, []);                     // load sach — khong phat
  const p = model.addPerson({ ho_ten: 'X' });
  model.setOwnerRow(p.row_id);
  assert.deepEqual(seen, [true]);                 // idle → dirty
  model.updatePersonField(
    model.state.stage.people[0].row_id, 'ngay_sinh', '1990');
  assert.deepEqual(seen, [true]);                 // van dirty — khong lap
  const r = await model.commitStage();
  assert.equal(r.ok, true);
  assert.deepEqual(seen, [true, false]);          // dirty → clean

  // Callback tra promise reject (bridge IPC chet) — emit khong sap,
  // khong unhandled rejection.
  const m2 = M.createModel({ client: fakeClient(seedCases('empty')),
    uuid, onUnsavedChange: () => Promise.reject(new Error('bridge dead')) });
  await m2.openCase(43);
  m2.addPerson({ ho_ten: 'Z' });                  // khong throw
  assert.equal(m2.state.stageDirty, true);
});

test('intakeAnalyze: suggestion_id trung → dedupe, ban moi thay ban cu o dau', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'lan 1' }]);
  const first = model.state.suggestions[0];
  // Lan analyze sau emit lai suggestion_id da co (re-analyze cung nguon)
  // → ban moi thay ban cu, khong nhan doi entry trong tray.
  const orig = client.run.bind(client);
  client.run = async (cmd, payload) => {
    const r = await orig(cmd, payload);
    if (cmd === 'notary.intake_analyze' && r.ok) {
      r.data.suggestions[0].suggestion_id = first.suggestion_id;
      r.data.suggestions[0].fields.ho_ten.normalized_value = 'Bản Mới';
    }
    return r;
  };
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'lan 2' }]);
  assert.equal(model.state.suggestions.length, 1);
  assert.equal(model.state.suggestions[0].suggestion_id,
               first.suggestion_id);
  assert.equal(
    model.state.suggestions[0].fields.ho_ten.normalized_value, 'Bản Mới');
  // id khac van xep chong binh thuong
  client.run = orig;
  await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'lan 3' }]);
  assert.equal(model.state.suggestions.length, 2);
});

test('exportWord: canceled job giu result (breakdown.skipped len wire — MIN-115)', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  client.run = async () => ({ ok: false,
    job: { status: 'canceled',
      result: { data: {
        schema_version: SCHEMA,
        documents: [
          { document_key: 'khai_nhan_di_san', display_name: 'KN',
            status: 'saved', actual_filename: 'a.docx',
            output_file: { path: 'D:/o/a.docx', scope: 'machine_local' },
            error: null },
          { document_key: 'thoa_thuan_phan_chia', display_name: 'TT',
            status: 'skipped', actual_filename: null,
            output_file: null, error: null },
        ],
        breakdown: { succeeded: ['khai_nhan_di_san'], failed: [],
                     skipped: ['thoa_thuan_phan_chia'] } } } },
    error: { code: 'user_canceled', message: 'da huy', retryable: false } });
  const r = await model.exportWord(
    ['khai_nhan_di_san', 'thoa_thuan_phan_chia'], { file_token: 't' });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'user_canceled');
  const res = model.state.wordResult;
  assert.equal(res.breakdown.skipped.length, 1);
  assert.equal(res.documents[1].status, 'skipped');
  assert.equal(model.state.wordBusy, false);
});

// ---------- MIN-122/128: nhap moi / draft / case_type ----------

test('newDraft: inheritance — stage co owner_row_id null + seed DUNG 1 node owner (MIN-136)', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  const s = model.state;
  assert.equal(s.status, 'ready');
  assert.equal(s.caseId, null);
  assert.ok(model.isDraft());
  assert.ok(model.canWrite());
  // stage v3: owner_row_id co mat (bat buoc cho inheritance)
  assert.equal('owner_row_id' in s.stage, true);
  assert.equal(s.stage.owner_row_id, null);
  // diagram v3 domain inheritance + DUNG 1 o owner — node sau chi sinh
  // tu engine requiredSlots, khong con seed 7 slot (MIN-136).
  assert.equal(s.diagram.version, 3);
  assert.equal(s.diagram.domain, 'inheritance');
  assert.equal(s.diagram.nodes.length, 1);
  const owner = s.diagram.nodes[0];
  assert.equal(owner.id, 'owner');
  assert.equal(owner.personId, null);            // chua chon owner
  assert.deepEqual(owner.ownPositions, []);
  assert.deepEqual(owner.receivePositions, []);
  assert.equal('isLandOwner' in owner, false);   // v1 flag bi cam
  assert.equal('willReceive' in owner, false);
  // MIN-136: nhap moi cong bo du 5 loai intake → nut Nhap file mo duoc
  // (sidecar ho tro intake_analyze khong case_id — contract §2.1a).
  assert.deepEqual(s.capabilities.intake,
    ['image', 'pdf', 'docx', 'xlsx', 'text']);
  assert.equal(s.capabilities.diagram, true);
  assert.equal(s.capabilities.word_export, false);
  assert.match(s.draftId,
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
});

test('newDraft(two_party): stage khong owner_row_id + 30 slot canonical', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft('two_party');
  const s = model.state;
  assert.equal(model.caseType(), 'two_party');
  assert.equal(model.diagramDomain(), 'two_party');
  assert.equal('owner_row_id' in s.stage, false);
  assert.equal(s.diagram.version, 3);
  assert.deepEqual(s.diagram.nodes.map((n) => n.id), TP_IDS);
  for (const n of s.diagram.nodes) {
    assert.deepEqual(Object.keys(n).sort(),
      ['deleted', 'hidden', 'id', 'personId']);
    assert.equal(n.personId, null);
  }
  // document_type default theo enum two_party
  assert.equal(s.caseInfo.document_type, 'chuyen_nhuong');
  assert.deepEqual(model.documentTypesFor('two_party'),
    ['chuyen_nhuong', 'tang_cho', 'cho_thue', 'dat_coc']);
});

test('updateCaseMeta case_type: doi loai → reset diagram buffer + stage key owner_row_id', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  const s = model.state;
  // thiet lap draft inheritance
  const p = model.addPerson({ ho_ten: 'X' });
  model.setOwnerRow(p.row_id);
  assert.equal(s.diagram.nodes.length, 1);       // MIN-136: 1 node owner
  // doi sang two_party → owner_row_id bi go, diagram ve 30 slot
  assert.equal(model.updateCaseMeta('case_type', 'two_party'), true);
  assert.equal(model.caseType(), 'two_party');
  assert.equal('owner_row_id' in s.stage, false);
  assert.deepEqual(s.diagram.nodes.map((n) => n.id), TP_IDS);
  assert.equal(s.caseInfo.document_type, 'chuyen_nhuong'); // enum doi
  assert.equal(s.diagramDirty, true);
  assert.equal(s.metaDirty, true);
  // stage people/assets giu nguyen
  assert.equal(s.stage.people.length, 1);
  // doi lai ve inheritance → owner_row_id quay lai (null)
  assert.equal(model.updateCaseMeta('case_type', 'inheritance'), true);
  assert.equal(s.stage.owner_row_id, null);
  assert.equal(s.diagram.nodes.length, 1);       // MIN-136: 1 node owner
  // gia tri la → reject
  assert.equal(model.updateCaseMeta('case_type', 'gift'), false);
});

test('two_party draft: addSlot chan; addPerson toi da 30; assign unique', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft('two_party');
  const s = model.state;
  assert.equal(model.addSlot(), null);          // canonical co dinh
  // gan nguoi vao p1..p30
  const people = [];
  for (let i = 0; i < 31; i += 1) {
    people.push(model.addPerson({ ho_ten: `P${i + 1}` }));
  }
  assert.equal(people[30], null);               // nguoi thu 31 bi chan
  assert.equal(s.stage.people.length, 30);
  assert.equal(model.assignPerson('p1', people[0].row_id), true);
  assert.equal(model.assignPerson('p16', people[1].row_id), true);
  // unique person: gan people[0] vao p2 → p1 giai phong
  assert.equal(model.assignPerson('p2', people[0].row_id), true);
  const nodes = s.diagram.nodes;
  assert.equal(nodes.find((n) => n.id === 'p1').personId, null);
  assert.equal(nodes.find((n) => n.id === 'p2').personId,
               people[0].row_id);
  // hidden/deleted flag van hoat dong tren node two_party
  assert.equal(model.setNodeFlag('p3', 'hidden', true), true);
});

test('MIN-136: seedDiagramSlots/ensureEmptyChildSlot khong con export', () => {
  // Sinh node chi qua engine requiredSlots — helper client-side seed
  // 7 slot va auto-child da bi go khoi API cong khai.
  assert.equal(typeof M.seedDiagramSlots, 'undefined');
  assert.equal(typeof M.ensureEmptyChildSlot, 'undefined');
});

test('newTwoPartyState: canonical p1..p30 — export dung cho test/view', () => {
  const st = M.newTwoPartyState();
  assert.equal(st.version, 3);
  assert.equal(st.domain, 'two_party');
  assert.deepEqual(st.nodes.map((n) => n.id), TP_IDS);
});

test('newDraft: draft diagram dung stage nhap — assign tu stage, pool tu stage', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  const row = model.addPerson({ ho_ten: 'Người Nháp' });
  assert.ok(row);
  assert.equal(model.pool().people.length, 1);
  assert.equal(model.assignPerson('owner', row.row_id), true);
  assert.equal(model.pool().people.length, 0);
  // pointer stage theo mirror — saveDraft gui owner_row_id hop le
  assert.equal(model.state.stage.owner_row_id, row.row_id);
});

test('movePerson: move vao node trong / swap / unassign ve Pool — owner mirror theo pointer', () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  const a = model.addPerson({ ho_ten: 'A' });
  const b = model.addPerson({ ho_ten: 'B' });
  const sp = model.addSlot();                    // slot thu cong (API noi bo)
  model.assignPerson('owner', a.row_id);
  model.assignPerson(sp.id, b.row_id);
  assert.equal(model.state.stage.owner_row_id, a.row_id);
  // swap owner <-> slot phu: a len slot, b xuong owner → pointer = b
  assert.equal(model.movePerson(a.row_id, sp.id), true);
  const nodes = model.state.diagram.nodes;
  assert.equal(nodes.find((n) => n.id === sp.id).personId, a.row_id);
  assert.equal(nodes.find((n) => n.id === 'owner').personId, b.row_id);
  assert.equal(model.state.stage.owner_row_id, b.row_id);
  // unassign owner → ve Pool, pointer ve null
  assert.equal(model.movePerson(b.row_id, null), true);
  assert.equal(nodes.find((n) => n.id === 'owner').personId, null);
  assert.equal(model.state.stage.owner_row_id, null);
  assert.equal(model.pool().people.length, 1);
  // tu Pool → node co nguoi (swap: nguoi cu ve Pool)
  assert.equal(model.movePerson(b.row_id, sp.id), true);
  assert.equal(nodes.find((n) => n.id === sp.id).personId, b.row_id);
  assert.equal(model.pool().people.length, 1);   // a ve Pool
  // tha len owner → pointer doi sang nguoi tha
  assert.equal(model.movePerson(b.row_id, 'owner'), true);
  assert.equal(model.state.stage.owner_row_id, b.row_id);
});

test('updateCaseMeta: chi draft; saveDraft gui meta + idempotency_key', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft();
  assert.equal(model.updateCaseMeta('document_type', 'thoa_thuan'), true);
  assert.equal(model.updateCaseMeta('noi_niem_yet', 'xã Yên Sở'), true);
  assert.equal(model.updateCaseMeta('bogus', 'x'), false);
  const owner = model.addPerson({ ho_ten: 'Người Chết' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.assignPerson('owner', owner.row_id);
  const draftId = model.state.draftId;
  const r = await model.saveDraft();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_create');
  assert.ok(call);
  assert.equal(call.payload.idempotency_key, draftId);
  assert.equal(call.payload.case.document_type, 'thoa_thuan');
  assert.equal(call.payload.case.noi_niem_yet, 'xã Yên Sở');
  // stage gui di co owner_row_id + diagram state v3
  assert.equal(call.payload.stage.owner_row_id, owner.row_id);
  assert.equal(call.payload.diagram.state.version, 3);
  assert.equal(call.payload.diagram.state.domain, 'inheritance');
  const sent = JSON.stringify(call.payload);
  assert.equal(sent.includes('is_primary'), false);
  assert.equal(sent.includes('isLandOwner'), false);
  assert.equal(sent.includes('willReceive'), false);
  // sau save → khong con draft; caseId gan; revision=1
  assert.equal(model.isDraft(), false);
  assert.ok(model.state.caseId >= 1000);
  assert.equal(model.state.revision, 1);
});

test('saveDraft two_party: payload khong owner_row_id, case_type two_party', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft('two_party');
  model.addPerson({ ho_ten: 'Bên A 1' });
  model.addPerson({ ho_ten: 'Bên B 1' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  const ps = model.state.stage.people;
  model.assignPerson('p1', ps[0].row_id);
  model.assignPerson('p16', ps[1].row_id);
  const r = await model.saveDraft();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_create');
  assert.equal(call.payload.case.case_type, 'two_party');
  assert.equal(call.payload.case.document_type, 'chuyen_nhuong');
  assert.equal('owner_row_id' in call.payload.stage, false);
  assert.equal(call.payload.diagram.state.domain, 'two_party');
  assert.equal(call.payload.diagram.state.nodes.length, 30);
  const s = model.state;
  assert.equal(s.caseInfo.case_type, 'two_party');
  assert.equal(s.diagram.domain, 'two_party');
});

test('saveDraft khong gui diagram → server seed owner theo owner_row_id', async () => {
  // Mo phong backend seed khi payload thieu diagram (§13.6) — model luon
  // gui diagram, test xac nhan fake server dung seed path cho draft khac.
  const client = fakeClient(seedCases('empty'));
  const oid = crypto.randomUUID();
  const r = await client.run('notary.workspace_create', {
    idempotency_key: crypto.randomUUID(),
    case: { case_type: 'inheritance', document_type: 'khai_nhan' },
    stage: {
      owner_row_id: oid,
      people: [{ row_id: oid, entity_id: null, ho_ten: 'Owner',
                 gioi_tinh: 'Nam' }],
      assets: [{ row_id: crypto.randomUUID(), entity_id: null,
                 so_serial: 'MM000001' }],
    },
  });
  assert.equal(r.ok, true);
  const nodes = r.data.diagram.state.nodes;
  const owner = nodes.find((n) => n.id === 'owner');
  assert.equal(owner.personId, oid);
  assert.deepEqual(owner.ownPositions, [1]);     // mac dinh het vi tri
});

test('saveDraft: retry cung draftId → created:false, khong tao trung', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft();
  const owner = model.addPerson({ ho_ten: 'Người Chết' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.assignPerson('owner', owner.row_id);
  const r1 = await model.saveDraft();
  assert.equal(r1.ok && r1.data.created, true);
  const cid = model.state.caseId;
  // mo lai nhap khac roi quay lai goi workspace_create cung key qua client
  const r2 = await client.run('notary.workspace_create', {
    idempotency_key: client.calls.find(
      (c) => c.command === 'notary.workspace_create')
      .payload.idempotency_key,
    case: { document_type: 'khai_nhan' },
    stage: { owner_row_id: owner.row_id, people: [], assets: [] },
    diagram: { state: { version: 3, domain: 'inheritance', nodes: [] } },
  });
  assert.equal(r2.ok, true);
  assert.equal(r2.data.created, false);
  assert.equal(r2.data.case.id, cid);
});

test('saveDraft: stage_validation_error giu nhap + fieldErrors', async () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  const bad = model.addPerson({ ho_ten: '   ' });  // ho_ten trong → required
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.setOwnerRow(bad.row_id);                  // pointer hop le → toi
                                                  // duoc field check
  const r = await model.saveDraft();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'stage_validation_error');
  assert.ok(model.state.fieldErrors.length >= 1);
  assert.equal(model.isDraft(), true);          // nhap nguyen ven
});

test('saveDraft: thieu owner → workspace_owner_required, nhap giu nguyen', async () => {
  const { model } = makeModel(seedCases('empty'));
  model.newDraft();
  model.addPerson({ ho_ten: 'Ai Do' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  const r = await model.saveDraft();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_owner_required');
  assert.equal(model.isDraft(), true);
});

test('evaluateDiagram tren nhap: gui case.case_type + stage, khong gui case_id', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft();
  const owner = model.addPerson({ ho_ten: 'Người Chết' });
  model.assignPerson('owner', owner.row_id);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);
  const call = client.calls.find(
    (c) => c.command === 'notary.diagram_evaluate');
  assert.equal('case_id' in call.payload, false);
  assert.equal(call.payload.case.case_type, 'inheritance');
  assert.ok(call.payload.stage.people.length === 1);
  assert.equal(call.payload.stage.owner_row_id, owner.row_id);
  assert.equal(call.payload.diagram.state.version, 3);
  assert.equal(model.state.evaluatedRevision, null);
});

test('evaluateDiagram tren nhap two_party: case hint + unsupported render', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft('two_party');
  model.addPerson({ ho_ten: 'Bên A' });
  model.assignPerson('p1', model.state.stage.people[0].row_id);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);
  const call = client.calls.find(
    (c) => c.command === 'notary.diagram_evaluate');
  assert.equal('case_id' in call.payload, false);
  assert.equal(call.payload.case.case_type, 'two_party');
  assert.equal('owner_row_id' in call.payload.stage, false);
  assert.equal(model.state.renderModel.status, 'unsupported');
  assert.equal(model.state.evaluatedRevision, null);
});

test('intakeAnalyze tren nhap: khong gui case_id', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft();
  const r = await model.intakeAnalyze([
    { source_id: crypto.randomUUID(), kind: 'text', text: 'x' }]);
  assert.equal(r.ok, true);
  const call = client.calls.find(
    (c) => c.command === 'notary.intake_analyze');
  assert.equal('case_id' in call.payload, false);
});

test('session guard: openCase(A) rồi newDraft trước khi response về → bo apply', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  const origRun = client.run;
  let resolve;
  client.run = (cmd, p) => new Promise((res) => {
    resolve = () => origRun(cmd, p).then(res);
  });
  const p = model.openCase(42);
  model.newDraft();                       // session doi truoc khi response
  resolve();
  await p;
  // state van la nhap — response workspace_get cua case 42 bi bo
  assert.equal(model.isDraft(), true);
  assert.equal(model.state.caseId, null);
});

test('commitStage chi goi tren case that — draft khong co commitStage', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  model.newDraft();
  model.addPerson({ ho_ten: 'A' });
  assert.equal(model.state.stageDirty, true);
  // saveDraft la duong luu duy nhat cua nhap
  const callsBefore = client.calls.length;
  const owner = model.state.stage.people[0];
  model.assignPerson('owner', owner.row_id);
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  const r = await model.saveDraft();
  assert.equal(r.ok, true);
  assert.ok(client.calls.length > callsBefore);
});

// ---------- MIN-141 đợt 3: case metadata + danh bạ ủy quyền ----------

test('đợt3 openCase: meta mới vào caseInfo + baseline committedCaseInfo', async () => {
  const seed = seedCases('ready');
  seed[42].noi_niem_yet = 'xã Niêm Yết';
  seed[42].nguoi_nhan_uy_quyen = 'Người Nhận UQ';
  seed[42].nguoi_nhan_uy_quyen_id = 7;
  seed[42].noi_dung_viec = 'Khai nhận thừa kế';
  const { model } = makeModel(seed);
  await model.openCase(42);
  const ci = model.state.caseInfo;
  assert.equal(ci.noi_niem_yet, 'xã Niêm Yết');
  assert.equal(ci.nguoi_nhan_uy_quyen, 'Người Nhận UQ');
  assert.equal(ci.nguoi_nhan_uy_quyen_id, 7);
  assert.equal(ci.noi_dung_viec, 'Khai nhận thừa kế');
  assert.deepEqual(model.state.committedCaseInfo.noi_niem_yet,
    'xã Niêm Yết');
  assert.equal(model.state.metaDirty, false);
  assert.equal(model.hasUnsaved(), false);
});

test('đợt3 commitStage meta-only: payload.case đi kèm stage, metaDirty clear', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.updateCaseMeta('noi_niem_yet', 'xã Mới');
  model.updateCaseMeta('noi_dung_viec', 'Việc mới');
  assert.equal(model.state.metaDirty, true);
  assert.equal(model.hasUnsaved(), true);
  const rev = model.state.revision;
  const r = await model.commitStage();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_commit_stage');
  assert.ok(call.payload.case, 'commit meta-only phải gửi payload.case');
  assert.equal(call.payload.case.noi_niem_yet, 'xã Mới');
  assert.equal(call.payload.case.noi_dung_viec, 'Việc mới');
  assert.equal(call.payload.case.case_type, 'inheritance');
  assert.equal(call.payload.base_revision, rev);
  assert.equal(model.state.metaDirty, false);
  assert.equal(model.state.revision, rev + 1);
  assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Mới');
  // Reopen: meta da luu quay ve tu server.
  await model.openCase(42);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Mới');
  assert.equal(model.state.caseInfo.noi_dung_viec, 'Việc mới');
});

test('đợt3 commitStage: khong sua meta → payload khong kem case', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'Người Mới' });       // stageDirty only
  const r = await model.commitStage();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_commit_stage');
  assert.equal(call.payload.case, undefined,
    'stage-only commit khong duoc dinh kem payload.case');
});

test('đợt3 commit meta: uq_id danh ba hop le → server resolve ten master', async () => {
  const seed = seedCases('ready');
  seed.__customers = [{ id: 5, ho_ten: 'Người Danh Bạ' }];
  const { model, client } = makeModel(seed);
  await model.openCase(42);
  model.updateCaseMeta('nguoi_nhan_uy_quyen', 'Người Danh Bạ');
  model.updateCaseMeta('nguoi_nhan_uy_quyen_id', 5);
  const r = await model.commitStage();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen,
    'Người Danh Bạ');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen_id, 5);
  // Id khong ton tai → validation_error, meta giu nguyen de sua lai.
  model.updateCaseMeta('nguoi_nhan_uy_quyen_id', 999);
  const r2 = await model.commitStage();
  assert.equal(r2.ok, false);
  assert.equal(r2.error.code, 'validation_error');
  assert.equal(model.state.metaDirty, true,
    'commit loi phai giu metaDirty de khong mat noi dung');
});

test('đợt3 commit meta: immutable case_type mismatch → validation_error', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.updateCaseMeta('noi_niem_yet', 'x');
  // Gia lap client lo gui kem case_type khac — server phai tu choi.
  const orig = client.run;
  client.run = (cmd, p) => {
    if (cmd === 'notary.workspace_commit_stage' && p.case) {
      p = { ...p, case: { ...p.case, case_type: 'two_party' } };
    }
    return orig(cmd, p);
  };
  const r = await model.commitStage();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'validation_error');
  assert.equal(model.state.caseInfo.case_type, 'inheritance');
});

test('đợt3 loadUqCatalog: nap danh ba mot lan; resolveUqName gan/xoa id', async () => {
  const seed = seedCases('ready');
  seed.__customers = [
    { id: 5, ho_ten: 'Người Danh Bạ', so_giay_to: '001' },
    { id: 6, ho_ten: 'Người Khác', so_giay_to: '002' },
  ];
  const { model, client } = makeModel(seed);
  await model.openCase(42);
  const r = await model.loadUqCatalog();
  assert.equal(r.ok, true);
  assert.equal(model.state.uqCatalog.length, 2);
  // Trung danh ba → gan id on dinh; nhap tu do → id null.
  model.resolveUqName('Người Danh Bạ');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen_id, 5);
  model.resolveUqName('Tên Tự Do');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen, 'Tên Tự Do');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen_id, null);
});

test('đợt3 createUqCustomer: tao danh ba moi → chon lam nguoi nhan UQ', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const r = await model.createUqCustomer('Người Mới Thêm');
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.customer_create');
  assert.equal(call.payload.ho_ten, 'Người Mới Thêm');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen,
    'Người Mới Thêm');
  assert.ok(model.state.caseInfo.nguoi_nhan_uy_quyen_id >= 900,
    'id danh ba moi phai di vao meta de commit giu tham chieu');
  assert.equal(model.state.metaDirty, true);
  // Ten trong → tu choi cuc bo, khong goi command.
  const before = client.calls.length;
  const r2 = await model.createUqCustomer('   ');
  assert.equal(r2.ok, false);
  assert.equal(client.calls.length, before);
});
