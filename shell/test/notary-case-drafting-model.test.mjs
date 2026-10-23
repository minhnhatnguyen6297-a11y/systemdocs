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
    if (cid.startsWith('__')) continue;
    cases[Number(cid)] = JSON.parse(JSON.stringify(c));
    cases[Number(cid)].id = Number(cid);
  }
  let nextEid = 900;
  let nextCid = 1000;
  const idem = {};                        // idempotency_key → case_id
  const saveIdem = {};                    // save_case key → {digest, caseId}
  const calls = [];
  let latestSource = null;
  const duplicateIdem = {};            // key → {digest, caseId}
  const setSourceLatest = (value) => { latestSource = value; };
  const emptySource = () => ({
    schema_version: SCHEMA,
    backend_mode: 'mock',
    source_case_id: null,
    source_status: null,
    stage: { people: [], assets: [] },
  });

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
      docx_import: JSON.parse(JSON.stringify(
        c.docx_import || { version: 1, sources: [] })),
      capabilities: {
        intake: sup ? ['image', 'pdf', 'docx', 'xlsx', 'text'] : [],
        diagram: sup,
        word_export: sup,
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

  const UUID4 =
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  function checkSaveStage(ct, stage, requireRows) {
    if (!stage || typeof stage !== 'object' ||
        !Array.isArray(stage.people) || !Array.isArray(stage.assets)) {
      return fail('validation_error', 'stage khong dung shape');
    }
    const ownerErr = checkOwnerPointer({ case_type: ct }, stage);
    if (ownerErr) return ownerErr;
    const fe = stageFieldErrors({ case_type: ct }, stage);
    if (requireRows) {
      if (!stage.people.length) {
        fe.push({ row_id: null, field: 'people', code: 'required',
                  message: 'can it nhat 1' });
      }
      if (!stage.assets.length) {
        fe.push({ row_id: null, field: 'assets', code: 'required',
                  message: 'can it nhat 1' });
      }
    }
    if (fe.length) {
      return fail('stage_validation_error', 'loi field',
                  { field_errors: fe });
    }
    return null;
  }

  // Kiểm Diagram theo Stage cùng payload. Ref của row đã lưu nhưng bị
  // xóa trong payload được prune (giống server); UUID chưa từng thuộc
  // bản cũ/payload là outside_stage.
  function checkSaveDiagram(ct, state, stage, oldPeople) {
    if (!state || typeof state !== 'object' || !Array.isArray(state.nodes)) {
      return fail('validation_error', 'diagram.state khong dung shape');
    }
    if (state.domain !== ct) {
      return fail('diagram_domain_mismatch',
                  `domain ${state.domain} != ${ct}`,
                  { expected: ct, got: state.domain });
    }
    const valid = new Set(stage.people.map((p) => p.row_id));
    const previous = new Set(oldPeople || []);
    for (const n of state.nodes) {
      if (n.personId && !valid.has(n.personId)) {
        if (!previous.has(n.personId)) {
          return fail('diagram_reference_outside_stage',
                      'personId ngoai stage', { personId: n.personId });
        }
        n.personId = null;                 // prune ref tới row đã xóa
      }
    }
    if (ct !== 'two_party') {
      const oid = stage.owner_row_id;
      const ownerNode = state.nodes.find(
        (n) => n.id === 'owner' && !n.deleted && n.personId != null);
      if (ownerNode && ownerNode.personId !== oid) {
        return fail('diagram_owner_mismatch',
                    'owner node != owner_row_id',
                    { owner_row_id: oid ?? null,
                      node_person_id: ownerNode.personId });
      }
    } else {
      state.nodes = canonicalTwoParty(state.nodes);
    }
    return null;
  }

  function applyCaseMeta(c, cm) {
    if (cm == null) return null;
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
    return null;
  }

  function applySavedStage(c, stage, state) {
    c.stage = JSON.parse(JSON.stringify(stage));
    for (const row of [...c.stage.people, ...c.stage.assets]) {
      if (row.entity_id == null) row.entity_id = nextEid++;
    }
    c.diagram = c.diagram || { domain: c.case_type, warnings: [] };
    c.diagram.domain = c.case_type;
    c.diagram.state = JSON.parse(JSON.stringify(state));
    const pruneWarn = pruneDiagram(c);
    c.diagram.render_model =
      isTp(c) ? unsupportedRender() : fakeRenderModel(c.diagram.state);
    return pruneWarn;
  }

  function checkDocxImport(value) {
    if (value === undefined) return null;
    if (!value || typeof value !== 'object' ||
        !Array.isArray(value.sources)) {
      return fail('validation_error', 'docx_import khong dung shape');
    }
    return null;
  }


  async function run(command, payload) {
    calls.push({ command, payload: JSON.parse(JSON.stringify(payload)) });
    switch (command) {
      case 'notary.workspace_save_case': {
        const hasId = Object.prototype.hasOwnProperty.call(payload, 'case_id');
        const key = payload.idempotency_key;
        if (!hasId) {
          if (typeof key !== 'string' || !UUID4.test(key)) {
            return fail('validation_error', 'idempotency_key khong hop le');
          }
          if ('base_revision' in payload) {
            return fail('validation_error', 'base_revision cam khi tao moi');
          }
          const digest = JSON.stringify({
            command: 'workspace_save_case', case: payload.case,
            stage: payload.stage, diagram: payload.diagram,
            docx_import: payload.docx_import ?? null,
          });
          if (saveIdem[key]) {
            if (saveIdem[key].digest !== digest) {
              return fail('idempotency_conflict', 'key da dung');
            }
            const replay = cases[saveIdem[key].caseId];
            return ok({ ...workspaceData(replay), created: false });
          }
          const cm = payload.case;
          if (!cm || typeof cm !== 'object' || Array.isArray(cm)) {
            return fail('validation_error', 'payload.case phai la object');
          }
          const ct = cm.case_type;
          if (!['inheritance', 'two_party'].includes(ct)) {
            return fail('validation_error', `case_type la: ${ct}`);
          }
          if (!cm.document_type ||
              !(isTp({ case_type: ct })
                ? ['chuyen_nhuong', 'tang_cho', 'cho_thue', 'dat_coc']
                : ['khai_nhan', 'thoa_thuan']).includes(cm.document_type)) {
            return fail('validation_error', 'document_type khong hop le');
          }
          const dxErr = checkDocxImport(payload.docx_import);
          if (dxErr) return dxErr;
          const stageErr = checkSaveStage(ct, payload.stage, true);
          if (stageErr) return stageErr;
          const state = payload.diagram && payload.diagram.state;
          const dgErr = checkSaveDiagram(ct, state, payload.stage, []);
          if (dgErr) return dgErr;
          const c = {
            id: nextCid++, case_type: ct,
            document_type: cm.document_type,
            status: 'done', locked: false, revision: 1,
            ngay_lap_ho_so: cm.ngay_lap_ho_so ?? null,
            noi_niem_yet: cm.noi_niem_yet ?? null,
            nguoi_nhan_uy_quyen: cm.nguoi_nhan_uy_quyen ?? null,
            nguoi_nhan_uy_quyen_id: cm.nguoi_nhan_uy_quyen_id ?? null,
            noi_dung_viec: cm.noi_dung_viec ?? null,
            ghi_chu: cm.ghi_chu ?? null,
            stage: { people: [], assets: [] },
            diagram: { domain: ct, warnings: [] },
            docx_import: JSON.parse(JSON.stringify(
              payload.docx_import || { version: 1, sources: [] })),
          };
          const metaErr = applyCaseMeta(c, cm);
          if (metaErr) return metaErr;
          applySavedStage(c, payload.stage, state);
          cases[c.id] = c;
          saveIdem[key] = { digest, caseId: c.id };
          return ok({ ...workspaceData(c), created: true });
        }
        if ('idempotency_key' in payload) {
          return fail('validation_error', 'idempotency_key cam voi case cu');
        }
        if (!Number.isInteger(payload.case_id) || payload.case_id < 1) {
          return fail('validation_error', 'case_id khong hop le');
        }
        if (!Number.isInteger(payload.base_revision) ||
            payload.base_revision < 1) {
          return fail('validation_error', 'base_revision bat buoc');
        }
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
        const cm = payload.case;
        if (!cm || typeof cm !== 'object' || Array.isArray(cm)) {
          return fail('validation_error', 'payload.case phai la object');
        }
        const dxErr = checkDocxImport(payload.docx_import);
        if (dxErr) return dxErr;
        const stageErr = checkSaveStage(c.case_type, payload.stage, false);
        if (stageErr) return stageErr;
        const state = payload.diagram && payload.diagram.state;
        const oldPeople = (c.stage.people || []).map((p) => p.row_id);
        const dgErr = checkSaveDiagram(
          c.case_type, state, payload.stage, oldPeople);
        if (dgErr) return dgErr;
        const metaErr = applyCaseMeta(c, cm);
        if (metaErr) return metaErr;
        applySavedStage(c, payload.stage, state);
        if (payload.docx_import !== undefined) {
          c.docx_import = JSON.parse(JSON.stringify(payload.docx_import));
        }
        c.status = 'done';
        c.revision += 1;
        return ok({ ...workspaceData(c), created: false });
      }
      case 'notary.workspace_source_latest': {
        if (!payload || Object.keys(payload).length) {
          return fail('validation_error', 'payload phai la object rong');
        }
        return ok(latestSource
          ? { ...JSON.parse(JSON.stringify(latestSource)),
              schema_version: SCHEMA, backend_mode: 'mock' }
          : emptySource());
      }
      case 'notary.workspace_get': {
        const { c, err } = getCase(payload);
        if (err) return err;
        return ok(workspaceData(c));
      }
      case 'notary.workspace_duplicate': {
        const extra = Object.keys(payload || {})
          .filter((k) => !['source_case_id', 'idempotency_key'].includes(k));
        if (extra.length) return fail('validation_error', 'key ngoai schema');
        const sid = payload.source_case_id;
        if (!Number.isInteger(sid) || sid < 1) {
          return fail('validation_error', 'source_case_id khong hop le');
        }
        const key = payload.idempotency_key;
        if (typeof key !== 'string' || !new RegExp(
          '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
          'i').test(key)) {
          return fail('validation_error', 'idempotency_key khong hop le');
        }
        const digest = JSON.stringify({
          command: 'workspace_duplicate', source_case_id: sid });
        if (duplicateIdem[key]) {
          if (duplicateIdem[key].digest !== digest) {
            return fail('idempotency_conflict', 'key da dung');
          }
          const replay = cases[duplicateIdem[key].caseId];
          return ok({ ...workspaceData(replay), source_case_id: sid,
                      created: false });
        }
        const source = cases[sid];
        if (!source) {
          return fail('case_not_found', 'khong tim thay',
                      { source_case_id: sid });
        }
        if (!supported(source)) {
          return fail('case_type_unsupported', 'khong ho tro',
                      { case_type: source.case_type });
        }
        const fresh = JSON.parse(JSON.stringify(source));
        const personMap = {};
        fresh.stage.people = (fresh.stage.people || []).map((row) => {
          const rid = crypto.randomUUID();
          personMap[row.row_id] = rid;
          return { ...row, row_id: rid };
        });
        fresh.stage.assets = (fresh.stage.assets || []).map((row) => ({
          ...row, row_id: crypto.randomUUID() }));
        if (fresh.case_type === 'inheritance') {
          fresh.stage.owner_row_id = personMap[
            source.stage.owner_row_id] ?? null;
        } else {
          delete fresh.stage.owner_row_id;
        }
        fresh.diagram.state.nodes = (fresh.diagram.state.nodes || []).map(
          (node) => (node.personId
            ? { ...node, personId: personMap[node.personId] ?? null }
            : node));
        fresh.id = nextCid++;
        fresh.status = 'draft';
        fresh.revision = 1;
        cases[fresh.id] = fresh;
        duplicateIdem[key] = { digest, caseId: fresh.id };
        return ok({ ...workspaceData(fresh), source_case_id: sid,
                    created: true });
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
      case 'notary.workspace_update': {
        // §6.2: cap nhat meta case da luu (khong cham stage/diagram),
        // revision+1; workspace_conflict/locked nhu moi write.
        const { c, err } = getCase(payload);
        if (err) return err;
        if (c.locked) return fail('workspace_locked', 'da khoa');
        if (payload.base_revision !== c.revision) {
          return fail('workspace_conflict', 'revision khac',
                      { server_revision: c.revision });
        }
        const cm = payload.case;
        if (!cm || typeof cm !== 'object' || Array.isArray(cm) ||
            !Object.keys(cm).length) {
          return fail('validation_error', 'case meta rong');
        }
        for (const k of Object.keys(cm)) {
          if (!['ngay_lap_ho_so', 'noi_niem_yet', 'ghi_chu'].includes(k)) {
            return fail('validation_error', `key la: ${k}`);
          }
          c[k] = cm[k];
        }
        c.revision += 1;
        return ok({
          schema_version: SCHEMA,
          revision: c.revision,
          case: workspaceData(c).case,
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
        if (!supported(c)) {
          return fail('case_type_unsupported', 'case type khong ho tro');
        }
        // NAIA-8 folder mode: template_dir co mat → nguon mau la cac
        // .docx trong thu muc (fake tra tap co dinh, key = basename).
        if (payload.template_dir) {
          return ok({
            schema_version: SCHEMA,
            documents: [
              { document_key: 'Mau thue nha.docx',
                display_name: 'Mau thue nha',
                ready: true, block_reason: null },
              { document_key: 'To cam ket.docx',
                display_name: 'To cam ket',
                ready: true, block_reason: null },
            ],
          });
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
        if (!supported(c)) {
          return fail('case_type_unsupported', 'case type khong ho tro');
        }
        const docs = payload.document_keys.map((k) => ({
          document_key: k, display_name: k,
          status: k === 'niem_yet' ? 'failed' : 'saved',
          actual_filename: k === 'niem_yet' ? null
            : `${k.replace(/\.docx$/i, '')}_HS-42.docx`,
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
  return { run, calls, cases, setSourceLatest };
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

// Nhu makeModel, nhung notary.diagram_evaluate tra promise do test
// resolve thu cong — de dieu khien thu tu response ve (T1/T2 §7.1).
function makeDeferredModel(seed) {
  const base = fakeClient(seed);
  const pending = [];
  const client = {
    calls: base.calls,
    run(command, payload) {
      if (command === 'notary.diagram_evaluate') {
        return new Promise((resolve) => pending.push({ payload, resolve }));
      }
      return base.run(command, payload);
    },
  };
  const model = M.createModel({ client, uuid });
  return { model, pending };
}

function evaluateOk(entry) {
  return { ok: true,
    data: { schema_version: SCHEMA,
      evaluated_revision: null,
      render_model: fakeRenderModel(entry.payload.diagram.state) } };
}

function evaluateFail(code) {
  return { ok: false,
    error: { code, message: code, retryable: false,
      next_action: null, details: null } };
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

test('openCase: two_party — domain/state 30 slot canonical, word_export on (NAIA-8)', async () => {
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
  assert.equal(s.capabilities.word_export, true);
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
  // saveCase tren case locked: model khong gui command, tra loi locked
  const before = client.calls.length;
  const r = await model.saveCase();
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

test('addPerson/setOwnerRow/update/remove → stageDirty; saveCase reset', async () => {
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

  const r = await model.saveCase();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.stageDirty, false);
  assert.equal(s.revision, 2);                   // 1 → 2
  assert.equal(s.caseInfo.status, 'done');
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

test('saveCase: thieu owner_row_id → workspace_owner_required, draft giu nguyen', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  model.addPerson({ ho_ten: 'Chưa chọn owner' });
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_owner_required');
  assert.equal(model.state.stageDirty, true);    // van dirty — chua luu
  assert.equal(model.state.revision, 1);
});

test('saveCase: stage_validation_error → fieldErrors theo row_id, stage giu draft', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const row = model.addPerson({ ho_ten: '' });   // rong → required
  model.setOwnerRow(row.row_id);                  // pointer hop le → den
                                                // duoc field check
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'stage_validation_error');
  const s = model.state;
  assert.equal(s.stageDirty, true);              // van dirty — chua luu
  assert.equal(s.revision, 1);                   // revision khong doi
  assert.equal(s.stage.people.length, 1);        // draft con nguyen
  const errs = model.fieldErrorsFor(row.row_id);
  assert.equal(errs.length, 1);
  assert.equal(errs[0].field, 'ho_ten');
  // sua field → loi cua field do duoc gỡ
  model.updatePersonField(row.row_id, 'ho_ten', 'Đã sửa');
  assert.equal(model.fieldErrorsFor(row.row_id).length, 0);
});

test('asset_limit — dong thu 4 bi tu choi o client', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.ok(model.addAsset({ so_serial: 'MM000001' }));
  assert.ok(model.addAsset({ so_serial: 'MM000002' }));
  assert.ok(model.addAsset({ so_serial: 'MM000003' }));
  assert.equal(model.addAsset({ so_serial: 'MM000004' }), null);  // MAX_ASSETS=3
  assert.equal(model.state.stage.assets.length, 3);
});

test('asset serial: new/cleared rỗng giữ "" và wire gửi chuỗi rỗng', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const person = model.addPerson({ ho_ten: 'Chủ đất' });
  model.setOwnerRow(person.row_id);

  const asset = model.addAsset();
  assert.equal(asset.so_serial, '');

  model.updateAssetField(asset.row_id, 'so_serial', '  RAW  ');
  assert.equal(model.state.stage.assets[0].so_serial, '  RAW  ');

  model.updateAssetField(asset.row_id, 'so_serial', '');
  assert.equal(model.state.stage.assets[0].so_serial, '');

  const r = await model.saveCase();
  assert.equal(r.ok, true);
  const sent = client.calls.at(-1).payload;
  assert.equal(sent.stage.assets[0].so_serial, '');
  assert.notEqual(sent.stage.assets[0].so_serial, null);
});

test('openCase: serial null từ server được map thành chuỗi rỗng', async () => {
  const seed = seedCases('ready');
  seed[42].stage.assets[0].so_serial = null;
  const { model } = makeModel(seed);
  await model.openCase(42);
  assert.equal(model.state.stage.assets[0].so_serial, '');
  assert.equal(model.state.committed.assets[0].so_serial, '');
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

test('saveCase stage+diagram cung dirty: baseline giu truoc Luu, payload du assignment, hydrate ca hai', async () => {
  const { model, client } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  assert.equal(s.diagram.nodes.length, 2);      // owner, spouse
  const baselineNodes = JSON.stringify(s.committedDiagram);

  // Draft dirty ca hai: gan E (dang o Pool) vao slot moi + sua ten.
  const node = model.addSlot();
  const e = s.stage.people.find((p) => p.ho_ten === 'Người Mẫu E');
  assert.ok(model.assignPerson(node.id, e.row_id));
  model.updatePersonField(s.stage.people[0].row_id, 'ho_ten',
                          'Người Mẫu A đổi');
  assert.equal(s.stageDirty, true);
  assert.equal(s.diagramDirty, true);
  // Truoc Luu: baseline va revision khong doi.
  assert.equal(JSON.stringify(s.committedDiagram), baselineNodes);
  assert.equal(s.revision, 5);

  const r = await model.saveCase();
  assert.equal(r.ok, true);
  assert.equal(s.revision, 6);                    // 5 → 6
  assert.equal(s.stageDirty, false);
  assert.equal(s.diagramDirty, false);
  assert.equal(s.caseInfo.status, 'done');
  // Payload chứa tất cả gán hợp lệ trong một snapshot.
  const sent = client.calls.filter(
    (c) => c.command === 'notary.workspace_save_case').at(-1).payload;
  assert.equal(sent.base_revision, 5);
  const sentNode = sent.diagram.state.nodes.find((n) => n.id === node.id);
  assert.equal(sentNode.personId, e.row_id);
  assert.equal(sent.stage.people[0].ho_ten, 'Người Mẫu A đổi');
  // Hydrate cả hai từ workspace server.
  assert.equal(s.diagram.nodes.find((n) => n.id === node.id).personId,
               e.row_id);
  assert.equal(s.committedDiagram.nodes.length, s.diagram.nodes.length);

  // UUID chưa từng thuộc Stage bị validation từ chối, không fake-prune.
  const staleNode = model.addSlot();
  staleNode.personId = '99999999-9999-4999-8999-999999999999';
  model.state.diagramDirty = true;
  const bad = await model.saveCase();
  assert.equal(bad.ok, false);
  assert.equal(bad.error.code, 'diagram_reference_outside_stage');
  assert.equal(model.state.diagramDirty, true);
  assert.equal(s.diagram.nodes.find((n) => n.id === staleNode.id).personId,
               '99999999-9999-4999-8999-999999999999');
});

test('saveCase khi diagram sach: hydrate workspace server, khong gia revision evaluate', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  assert.equal(s.diagramDirty, false);
  model.updatePersonField(s.stage.people[0].row_id, 'ho_ten', 'Đổi tên');
  const r = await model.saveCase();
  assert.equal(r.ok, true);
  assert.equal(s.diagramDirty, false);
  assert.equal(s.revision, 6);
  // evaluate draft tra evaluated_revision null; save khong gia revision DB.
  assert.equal(s.evaluatedRevision, null);
  assert.ok(s.renderModel);
});

test('saveCase voi stage dirty: xoa person → persist node da prune + flag khac', async () => {
  const { model } = makeModel(seedCases('diagram-warning'));
  await model.openCase(46);
  const s = model.state;
  const b = s.stage.people.find((p) => p.ho_ten === 'Người Mẫu B');
  // draft dirty bang flag hidden tren node spouse
  assert.ok(model.setNodeFlag('spouse', 'hidden', true));
  // xoa B khoi stage draft → mirror prune spouse.personId ngay
  model.removeStageRow(b.row_id);
  const r = await model.saveCase();
  assert.equal(r.ok, true);
  assert.equal(s.stageDirty, false);
  assert.equal(s.diagramDirty, false);
  assert.equal(
    s.diagram.nodes.find((n) => n.id === 'spouse').personId, null);
  // flag hidden=true (thay doi draft) da duoc persist cung snapshot
  assert.equal(
    s.diagram.nodes.find((n) => n.id === 'spouse').hidden, true);
  // B khong con trong stage da luu
  assert.equal(
    s.committed.people.some((p) => p.row_id === b.row_id), false);
});

test('saveCase: workspace_conflict → status conflict + server_revision', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'X' });
  // gia lap server revision doi (tab khac da ghi)
  client.cases[42].revision = 9;
  const r = await model.saveCase();
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
  await model.saveCase();
  assert.equal(model.state.status, 'conflict');

  // keep → tro lai ready, draft nguyen, stale flag
  model.resolveConflict('keep');
  assert.equal(model.state.status, 'ready');
  assert.equal(model.state.stale, true);
  assert.equal(model.state.stage.people.length, 5);

  // conflict lai → reload → draft bi thay bang ban server moi
  const r2 = await model.saveCase();
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

test('pool: person vua them tren case da luu xuat hien ngay va gan duoc truoc Luu', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const row = model.addPerson({ ho_ten: 'Draft chưa lưu' });
  assert.equal(model.pool().people.length, 1);
  assert.equal(model.pool().people[0].row_id, row.row_id);
  assert.equal(model.isStageEmpty(), false);
  // Case đã lưu vẫn gán được người mới trước khi Lưu hồ sơ.
  const node = model.addSlot('owner');
  assert.equal(model.assignPerson(node.id, row.row_id), true);
  assert.equal(model.pool().people.length, 0);
  assert.equal(model.state.stage.owner_row_id, row.row_id);
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

test('diagram draft: addSlot/togglePosition/removeNode → diagramDirty; saveCase reset', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
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

  const r = await model.saveCase();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.diagramDirty, false);
  assert.equal(s.revision, 8);                    // 7 → 8
  const sent = client.calls.filter(
    (c) => c.command === 'notary.workspace_save_case').at(-1).payload;
  assert.equal(sent.base_revision, 7);
  assert.equal(sent.diagram.state.version, 3);    // v3 tren wire
  assert.equal(sent.diagram.state.domain, 'inheritance');

  model.removeNode(node.id);                      // → deleted:true
  const gone = model.state.diagram.nodes
    .find((n) => n.id === node.id);
  assert.equal(gone.deleted, true);
  assert.equal(model.state.diagramDirty, true);
});

test('branch removal: active parent closure, reciprocal tombstones, one draft mutation', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const node = (id, parents = [], spouse = null, extra = {}) => ({
    id, personId: `person-${id}`, parentSlotIds: parents, spouseSlotId: spouse,
    ownPositions: [1], receivePositions: [2], hidden: false, deleted: false,
    ...extra,
  });
  const nodes = [
    node('owner'), node('B', ['owner'], 'S'), node('S', [], 'B'),
    node('C', ['B', 'S']), node('D', ['C']),
    node('empty', ['B'], null, { personId: null }),
    node('hidden', ['empty'], null, { hidden: true }),
    node('U', ['owner'], 'V'), node('V', [], 'U'),
    node('old', ['B'], 'B', { deleted: true }),
    node('behind-old', ['old']),
  ];
  const s = model.state;
  s.diagram.nodes = nodes;
  s.stage.people = nodes.filter(n => n.personId).map(n => ({
    row_id: n.personId, ho_ten: n.id,
  }));
  s.committed = structuredClone(s.stage);
  const stage = structuredClone(s.stage);
  const before = structuredClone(s.diagram);
  let notifications = 0;
  const unsubscribe = model.subscribe(() => { notifications += 1; });
  const impact = model.nodeRemovalImpact('B');
  assert.deepEqual(impact.nodeIds, ['B', 'C', 'empty', 'D', 'hidden']);
  assert.equal(impact.relations.filter(r => r.kind === 'spouse').length, 2);
  assert.ok(impact.relations.some(r => r.from === 'S' && r.to === 'C'));
  assert.ok(impact.relations.some(r => r.from === 'B' && r.to === 'old'));
  assert.deepEqual(s.diagram, before, 'preview is read-only');
  assert.equal(notifications, 0);
  assert.equal(model.removeNode('B'), true);
  assert.equal(notifications, 1, 'subscribers see only the completed cutover');
  unsubscribe();
  assert.deepEqual(s.stage, stage);
  assert.deepEqual(s.committed, stage);
  assert.deepEqual(nodes.map(n => n.id), before.nodes.map(n => n.id));
  for (const id of impact.nodeIds) {
    const n = nodes.find(n => n.id === id);
    const original = before.nodes.find(n => n.id === id);
    assert.deepEqual(n, {
      ...original, deleted: true, parentSlotIds: [], spouseSlotId: null,
    });
  }
  assert.equal(nodes.find(n => n.id === 'S').spouseSlotId, null);
  assert.deepEqual(nodes.find(n => n.id === 'old').parentSlotIds, []);
  assert.equal(nodes.find(n => n.id === 'old').spouseSlotId, null);
  for (const id of ['owner', 'U', 'V', 'behind-old']) {
    assert.deepEqual(nodes.find(n => n.id === id), before.nodes.find(n => n.id === id));
  }
  const pool = new Set(model.pool().people.map(p => p.row_id));
  for (const id of ['B', 'C', 'D', 'hidden', 'old']) {
    assert.ok(pool.has(`person-${id}`), `${id} must not be assigned by a tombstone`);
  }
  assert.equal(pool.has('person-S'), false);
  assert.equal(s.diagramDirty, true);
  assert.equal(model.removeNode('B'), false);
  assert.equal(model.nodeRemovalImpact('missing'), null);
});

test('branch removal does not remove canonical two-party slots', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft('two_party');
  const before = structuredClone(model.state.diagram);
  const dirty = model.state.diagramDirty;
  assert.equal(model.nodeRemovalImpact('p1'), null);
  assert.equal(model.removeNode('p1'), false);
  assert.deepEqual(model.state.diagram, before);
  assert.equal(model.state.diagramDirty, dirty);
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
  await model.newDraft();                          // MIN-136: 1 node owner
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

test('position defaults: owner assigned without assets expands with every added asset', async () => {
  const { model } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Owner' });
  model.assignPerson('owner', person.row_id);
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(owner.ownPositions, []);
  model.addAsset({ so_serial: 'G1-1' });
  assert.deepEqual(owner.ownPositions, [1]);
  model.addAsset({ so_serial: 'G1-2' });
  assert.deepEqual(owner.ownPositions, [1, 2]);
});

test('position defaults: removing an asset shrinks untouched ownership', async () => {
  const { model } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Owner' });
  model.addAsset({ so_serial: 'G1-1' });
  const removed = model.addAsset({ so_serial: 'G1-2' });
  model.assignPerson('owner', person.row_id);
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  assert.deepEqual(owner.ownPositions, [1, 2]);
  model.removeStageRow(removed.row_id);
  assert.deepEqual(owner.ownPositions, [1]);
});

for (const empty of [false, true]) {
  test(`position defaults: manual ownership ${empty ? 'empty' : 'subset'} survives add and repeated saves`, async () => {
    const { model, client } = makeModel({});
    await model.newDraft();
    const person = model.addPerson({ ho_ten: 'Owner' });
    model.addAsset({ so_serial: 'G1-1' });
    if (!empty) model.addAsset({ so_serial: 'G1-2' });
    model.assignPerson('owner', person.row_id);
    model.toggleNodePosition('owner', 'own', 1);
    const expected = empty ? [] : [2];
    model.addAsset({ so_serial: 'G1-3' });
    assert.deepEqual(model.state.diagram.nodes[0].ownPositions, expected);
    assert.equal((await model.saveCase()).ok, true);
    model.addAsset({ so_serial: 'G1-4' });
    assert.equal((await model.saveCase()).ok, true);
    const sent = client.calls.filter((c) =>
      c.command === 'notary.workspace_save_case');
    for (const call of sent) {
      assert.deepEqual(call.payload.diagram.state.nodes[0].ownPositions, expected);
    }
    assert.deepEqual(model.state.diagram.nodes[0].ownPositions, expected);
  });
}

test('position defaults: saveCase sends ownership after adding first asset without diagram edits', async () => {
  const { model, client } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Owner' });
  model.assignPerson('owner', person.row_id);
  model.addAsset({ so_serial: 'G1-1' });
  assert.equal((await model.saveCase()).ok, true);
  const call = client.calls.find((c) => c.command === 'notary.workspace_save_case');
  assert.deepEqual(call.payload.diagram.state.nodes[0].ownPositions, [1]);
  assert.equal('positionTouched' in call.payload.diagram.state, false);
});

test('position defaults: empty owner stays empty when another node owns assets', async () => {
  const { model } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Owner' });
  const other = model.addPerson({ ho_ten: 'Other owner' });
  model.assignPerson('owner', person.row_id);
  const slot = model.addSlot();
  model.assignPerson(slot.id, other.row_id);
  model.toggleNodePosition(slot.id, 'own', 1);
  model.addAsset({ so_serial: 'G1-1' });
  assert.deepEqual(model.state.diagram.nodes[0].ownPositions, []);
  assert.deepEqual(slot.ownPositions, [1]);
});

test('position defaults: assigned heir receives all assets until receive chips are touched', async () => {
  const { model } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Heir' });
  const slot = model.addSlot();
  model.assignPerson(slot.id, person.row_id);
  model.addAsset({ so_serial: 'G1-1' });
  assert.deepEqual(slot.receivePositions, [1]);
  model.toggleNodePosition(slot.id, 'own', 1);
  model.addAsset({ so_serial: 'G1-2' });
  assert.deepEqual(slot.receivePositions, [1, 2]);
  model.toggleNodePosition(slot.id, 'receive', 1);
  model.toggleNodePosition(slot.id, 'receive', 2);
  model.addAsset({ so_serial: 'G1-3' });
  assert.deepEqual(slot.receivePositions, []);
  model.removeStageRow(model.state.stage.assets[0].row_id);
  assert.deepEqual(slot.receivePositions, []);
});

test('position defaults: saveCase synchronizes defaults before capturing payload', async () => {
  const { model, client } = makeModel({});
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'Owner' });
  model.addAsset({ so_serial: 'G1-1' });
  model.addAsset({ so_serial: 'G1-2' });
  model.assignPerson('owner', person.row_id);
  // Represent an untouched partial default loaded into the draft buffer.
  model.state.diagram.nodes[0].ownPositions = [1];
  assert.equal((await model.saveCase()).ok, true);
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
  assert.deepEqual(call.payload.diagram.state.nodes[0].ownPositions, [1, 2]);
});

test('position defaults: newDraft and openCase reset manual selection tracking', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.toggleNodePosition('owner', 'own', 1);
  await model.openCase(42);
  model.addAsset({ so_serial: 'G1-3' });
  assert.deepEqual(model.state.diagram.nodes.find((n) =>
    n.id === 'owner').ownPositions, [1, 2, 3]);
  model.toggleNodePosition('owner', 'own', 1);
  await model.newDraft();
  const person = model.addPerson({ ho_ten: 'New owner' });
  model.assignPerson('owner', person.row_id);
  model.addAsset({ so_serial: 'G1-1' });
  assert.deepEqual(model.state.diagram.nodes[0].ownPositions, [1]);
});

test('saveCase diagram-only: workspace_conflict → status conflict', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.setNodeFlag('owner', 'hidden', true);    // dirty diagram
  client.cases[42].revision = 12;
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_conflict');
  assert.equal(model.state.status, 'conflict');
  assert.equal(model.state.conflict.server_revision, 12);
});

test('saveCase: owner mirror lech → diagram_owner_mismatch passthrough', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  // Gia lap draft lech mirror (khong qua setter — UI khong bao gio tao
  // trang thai nay, nhung server van la chot cuoi).
  const owner = model.state.diagram.nodes.find((n) => n.id === 'owner');
  const other = model.state.stage.people[1].row_id;
  model.state.diagram.nodes.find((n) => n.id === 'spouse').personId = null;
  owner.personId = other;
  model.state.diagramDirty = true;
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'diagram_owner_mismatch');
});

test('saveCase: domain mismatch → diagram_domain_mismatch', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.diagram = { version: 3, domain: 'two_party',
    nodes: TP_IDS.map((id) => ({ id, personId: null,
                                hidden: false, deleted: false })) };
  model.state.diagramDirty = true;
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'diagram_domain_mismatch');
});

test('saveCase two_party: persist + revision bump', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  model.assignPerson('p3', model.state.stage.people[0].row_id);
  const r = await model.saveCase();
  assert.equal(r.ok, true);
  assert.equal(model.state.revision, 3);          // 2 → 3
  assert.equal(model.state.renderModel.status, 'unsupported');
  assert.deepEqual(model.state.diagram.nodes.map((n) => n.id), TP_IDS);
});

test('evaluateDiagram: gui payload draft cho case da luu, KHONG doi revision/persist', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.setNodeFlag('owner', 'hidden', true);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const s = model.state;
  assert.equal(s.revision, 7);                    // read-only — khong tang
  assert.equal(s.evaluatedRevision, null);        // draft evaluate
  assert.ok(s.renderModel);
  assert.equal(s.renderModel.engineVersion, 2);
  assert.equal(s.diagramDirty, true);             // draft van chua luu
  const call = client.calls.filter(
    (c) => c.command === 'notary.diagram_evaluate').at(-1).payload;
  assert.equal('case_id' in call, false);
  assert.equal('base_revision' in call, false);
  assert.equal(call.case.case_type, 'inheritance');
  assert.equal(call.stage.people.length, 4);
  assert.equal(s.status, 'ready');
});

test('diagram tren case locked: evaluate duoc phep (read-only), save bi chan', async () => {
  const { model } = makeModel(seedCases('locked'));
  await model.openCase(44);
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);                       // read-only qua duoc
  const r2 = await model.saveCase();
  assert.equal(r2.ok, false);
  assert.equal(r2.error.code, 'workspace_locked');
});

// §7.1 D2: response evaluate gui tu so do CU khong duoc dat lai error/
// renderModel sau khi so do da sua (gan owner) va da co evaluate moi hon.
test('evaluateDiagram: response cu ve sau khi gan owner bi bo — khong dat lai error/renderModel', async () => {
  const { model, pending } = makeDeferredModel(seedCases('ready'));
  await model.openCase(42);
  const ownerRow = model.state.stage.owner_row_id;
  model.setOwnerRow(null);                 // so do chua owner — A gui luc nay
  const pA = model.evaluateDiagram();
  assert.equal(pending.length, 1);
  assert.equal(
    pending[0].payload.diagram.state.nodes.find((n) => n.id === 'owner')
      .personId, null);
  model.setOwnerRow(ownerRow);             // nguoi dung gan owner
  const pB = model.evaluateDiagram();
  assert.equal(pending.length, 2);
  pending[1].resolve(evaluateOk(pending[1]));
  await pB;
  const renderB = model.state.renderModel;
  assert.equal(renderB.status, 'complete');
  // A (gui luc chua owner) ve SAU B va fail — phai bi bo hoan toan.
  pending[0].resolve(evaluateFail('workspace_owner_required'));
  const a = await pA;
  assert.equal(a.ok, false);
  assert.equal(model.state.error, null,
    'banner owner_required cu bi dat lai sau khi da gan owner');
  assert.equal(model.state.renderModel, renderB);
  assert.deepEqual(model.state.diagramErrors, []);
  assert.equal(model.state.busy, null);
});

test('evaluateDiagram: evaluate moi thanh cong don loi do evaluate dat truoc', async () => {
  const { model, pending } = makeDeferredModel(seedCases('ready'));
  await model.openCase(42);
  const pA = model.evaluateDiagram();
  pending[0].resolve(evaluateFail('workspace_owner_required'));
  await pA;
  assert.equal(model.state.error.code, 'workspace_owner_required');
  // Sua so do qua touchDiagram — duong nay KHONG tu don state.error.
  model.setNodeFlag('owner', 'hidden', true);
  assert.equal(model.state.error.code, 'workspace_owner_required');
  const pB = model.evaluateDiagram();
  pending[1].resolve(evaluateOk(pending[1]));
  await pB;
  assert.equal(model.state.error, null,
    'loi do evaluate dat van treo sau lan evaluate thanh cong');
  assert.equal(model.state.renderModel.status, 'complete');
});

test('evaluateDiagram: evaluate thanh cong KHONG don loi cua duong ghi', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const w = await model.duplicateCase(999);      // lenh ghi fail → state.error
  assert.equal(w.ok, false);
  const writeError = model.state.error;
  assert.equal(writeError.code, 'case_not_found');
  const r = await model.evaluateDiagram();
  assert.equal(r.ok, true);
  assert.equal(model.state.error, writeError,
    'evaluate khong duoc don loi cua duong ghi');
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

test('word tren two_party: duoc phep (NAIA-8) — options + batch', async () => {
  const { model } = makeModel(seedCases('ready-two-party'));
  await model.openCase(48);
  const o = await model.loadWordOptions();
  assert.equal(o.ok, true);
  assert.equal(model.state.wordOptions.length, 2);

  const r = await model.exportWord(
    ['khai_nhan_di_san'],
    { path: 'D:/out', scope: 'machine_local', is_dir: true });
  assert.equal(r.ok, true);
  assert.deepEqual(
    model.state.wordResult.breakdown.succeeded, ['khai_nhan_di_san']);
});

test('word folder mode (NAIA-8): template_dir + create_case_subdir len wire', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const dirToken = { file_token: 'tok-tpl-dir' };

  const o = await model.loadWordOptions(dirToken);
  assert.equal(o.ok, true);
  // Folder mode: documents la file .docx quet duoc (key = basename).
  assert.deepEqual(
    model.state.wordOptions.map((d) => d.document_key),
    ['Mau thue nha.docx', 'To cam ket.docx']);
  const optCall = client.calls.find(
    (c) => c.command === 'notary.word_export_options');
  assert.deepEqual(optCall.payload.template_dir, dirToken);

  const r = await model.exportWord(
    ['Mau thue nha.docx'],
    { path: 'D:/out', scope: 'machine_local', is_dir: true },
    { templateDir: dirToken, createCaseSubdir: true });
  assert.equal(r.ok, true);
  const call = client.calls.find(
    (c) => c.command === 'notary.word_export_batch');
  assert.deepEqual(call.payload.template_dir, dirToken);
  assert.equal(call.payload.create_case_subdir, true);
  assert.equal(call.payload.destination.is_dir, true);
  assert.deepEqual(
    model.state.wordResult.breakdown.succeeded, ['Mau thue nha.docx']);
});

// NAIA-8 review: doi folder giua chung — chi response MOI NHAT duoc ap
// vao state; thanh cong/loi cua scan cu deu phai bi bo.
function scanClient(seed, handlers) {
  const base = fakeClient(seed);
  return {
    calls: base.calls, cases: base.cases,
    run: async (cmd, payload) => {
      if (cmd === 'notary.word_export_options' && payload.template_dir) {
        const h = handlers[payload.template_dir.file_token];
        return h ? h() : { ok: false, error: {
          code: 'file_not_found', message: 'khong thay thu muc',
          retryable: false, next_action: null, details: null } };
      }
      return base.run(cmd, payload);
    },
  };
}
const docsOf = (keys) => ({ ok: true, data: {
  schema_version: SCHEMA,
  documents: keys.map((k) => ({
    document_key: k, display_name: k.replace(/\.docx$/i, ''),
    ready: true, block_reason: null })) } });
const deferred = () => {
  let resolve;
  const promise = new Promise((res) => { resolve = res; });
  return { promise, resolve };
};

test('loadWordOptions: doi folder — xoa options ngay + chi response moi nhat thang (response dao)', async () => {
  // Hai folder TRUNG basename "mau" nhung token khac nhau — dinh danh
  // scan la file_token, khong phai ten hien thi (NAIA-8 review).
  const dA = deferred();
  const dB = deferred();
  const client = scanClient(seedCases('ready'), {
    'tok-A-mau': () => dA.promise,
    'tok-B-mau': () => dB.promise,
  });
  const model = M.createModel({ client, uuid });
  await model.openCase(42);
  const pA = model.loadWordOptions({ file_token: 'tok-A-mau' });
  // Cho A quet xong de co options roi doi folder.
  dA.resolve(docsOf(['a1.docx', 'a2.docx']));
  assert.equal((await pA).ok, true);
  assert.deepEqual(
    model.state.wordOptions.map((d) => d.document_key),
    ['a1.docx', 'a2.docx']);

  const dA2 = deferred();
  // Scan lai folder A (re-scan) roi ngay lap tuc doi sang B.
  const pA2 = model.loadWordOptions({ file_token: 'tok-A-mau' });
  // Lai nay van cho — nhung phai xoa options cu NGAY.
  assert.equal(model.state.wordOptions, null);
  const pB = model.loadWordOptions({ file_token: 'tok-B-mau' });
  // B ve truoc → state la danh sach cua B.
  dB.resolve(docsOf(['b.docx']));
  assert.equal((await pB).ok, true);
  assert.deepEqual(
    model.state.wordOptions.map((d) => d.document_key), ['b.docx']);
  // A tre ve sau — KHONG duoc de len options cua B.
  dA2.resolve(docsOf(['a-late.docx']));
  const rA2 = await pA2;
  assert.equal(rA2.stale, true);
  assert.deepEqual(
    model.state.wordOptions.map((d) => d.document_key), ['b.docx']);
});

test('loadWordOptions: loi cua scan cu ve muon → khong set state.error', async () => {
  const dA = deferred();
  const client = scanClient(seedCases('ready'), {
    'tok-A': () => dA.promise,
    'tok-B': async () => docsOf(['b.docx']),
  });
  const model = M.createModel({ client, uuid });
  await model.openCase(42);
  const pA = model.loadWordOptions({ file_token: 'tok-A' });
  const pB = model.loadWordOptions({ file_token: 'tok-B' });
  assert.equal((await pB).ok, true);
  // A fail tre — bi bo, state.error khong bi set boi scan cu.
  dA.resolve({ ok: false, error: {
    code: 'file_not_found', message: 'A khong doc duoc',
    retryable: false, next_action: null, details: null } });
  const rA = await pA;
  assert.equal(rA.stale, true);
  assert.equal(model.state.error, null);
  assert.deepEqual(
    model.state.wordOptions.map((d) => d.document_key), ['b.docx']);
});

test('loadWordOptions: scan moi nhat fail → state.error co code loi quet', async () => {
  const client = scanClient(seedCases('ready'), {
    'tok-x': async () => docsOf(['x.docx']),
    'tok-missing': async () => ({ ok: false, error: {
      code: 'file_not_found', message: 'khong thay thu muc',
      retryable: false, next_action: null, details: null } }),
  });
  const model = M.createModel({ client, uuid });
  await model.openCase(42);
  await model.loadWordOptions({ file_token: 'tok-x' });
  const r = await model.loadWordOptions({ file_token: 'tok-missing' });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'file_not_found');
  assert.equal(model.state.error.code, 'file_not_found');
  assert.equal(model.state.wordOptions, null);
});

test('saveCaseMeta: case da luu → wire workspace_update, revision+1, caseInfo cap nhat', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const rev = model.state.revision;
  const r = await model.saveCaseMeta({ noi_niem_yet: 'xã Yên Sở' });
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_update');
  assert.ok(call);
  assert.equal(call.payload.case_id, 42);
  assert.equal(call.payload.base_revision, rev);
  assert.deepEqual(call.payload.case, { noi_niem_yet: 'xã Yên Sở' });
  assert.equal(model.state.revision, rev + 1);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Yên Sở');
  assert.equal(model.state.notice, null, 'R14: không toast chữ thành công');
  // Reload qua workspace_get thay gia tri da luu (mot nguon du lieu).
  await model.openCase(42);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Yên Sở');
});

test('saveCaseMeta preserves other metadata drafts and refreshes cancel baseline', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.updateCaseMeta('noi_dung_viec', 'Nội dung đang sửa');
  const result = await model.saveCaseMeta({ noi_niem_yet: 'xã Đã Lưu' });
  assert.equal(result.ok, true);
  assert.equal(model.state.caseInfo.noi_dung_viec, 'Nội dung đang sửa');
  assert.equal(model.state.metaDirty, true);
  assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Đã Lưu');
});

test('saveCaseMeta keeps edits made to a clean field while response is pending', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const revision = model.state.revision;
  const committedContent = model.state.committedCaseInfo.noi_dung_viec;
  assert.equal(model.state.caseInfo.noi_dung_viec, committedContent);
  const run = client.run;
  let finish;
  client.run = (command, payload) => command === 'notary.workspace_update'
    ? new Promise((resolve) => { finish = async () => resolve(await run(command, payload)); })
    : run(command, payload);
  const pending = model.saveCaseMeta({ noi_niem_yet: 'xã Đã Lưu' });
  assert.equal(typeof finish, 'function');
  model.updateCaseMeta('noi_dung_viec', 'Sửa khi đang chờ');
  await finish();
  const result = await pending;
  assert.equal(result.ok, true);
  assert.equal(model.state.caseInfo.noi_dung_viec, 'Sửa khi đang chờ');
  assert.equal(model.state.committedCaseInfo.noi_dung_viec, committedContent);
  assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Đã Lưu');
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Đã Lưu');
  assert.equal(model.state.revision, revision + 1);
  assert.equal(model.state.metaDirty, true);
});

test('saveCaseMeta: conflict → ok:false, error ro rang, khong ghi de state', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  client.cases[42].revision += 5;   // ben thu ba da ghi truoc
  const r = await model.saveCaseMeta({ noi_niem_yet: 'xã X' });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_conflict');
  assert.equal(model.state.conflict != null, true);
  assert.equal(model.state.caseInfo.noi_niem_yet ?? null, null);
});

test('saveCaseMeta: case locked → khong goi wire, tra workspace_locked', async () => {
  const { model, client } = makeModel(seedCases('locked'));
  await model.openCase(44);
  const r = await model.saveCaseMeta({ noi_niem_yet: 'xã Y' });
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_locked');
  assert.equal(client.calls.filter(
    (c) => c.command === 'notary.workspace_update').length, 0);
});

test('saveCaseMeta: draft → cap nhat nhap local, khong goi wire; key la → validation_error', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.newDraft();
  const r = await model.saveCaseMeta({ noi_niem_yet: 'phường A' });
  assert.equal(r.ok, true);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'phường A');
  assert.equal(client.calls.filter(
    (c) => c.command === 'notary.workspace_update').length, 0);
  const bad = await model.saveCaseMeta({ case_type: 'gift' });
  assert.equal(bad.ok, false);
  assert.equal(bad.error.code, 'validation_error');
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
  assert.equal(model.state.evaluatedRevision, null);
  const p = model.addPerson({ ho_ten: 'Nháp A' });
  model.setOwnerRow(p.row_id);
  const rc = await model.saveCase();
  assert.equal(rc.ok, true);
  assert.equal(model.state.notice, null, 'R14: không toast chữ thành công');
  // server khoa case → saveCase tiep nhan workspace_locked → state.error
  client.cases[43].locked = true;
  model.updatePersonField(
    model.state.stage.people[0].row_id, 'ho_ten', 'Sửa lại');
  const rl = await model.saveCase();
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
  const r = await model.saveCase();
  assert.equal(r.error.code, 'workspace_locked');
  assert.equal(model.canWrite(), false);
  const sugId = model.state.suggestions[0].suggestion_id;
  assert.equal(model.acceptSuggestion(sugId), null);
  assert.equal(model.state.suggestions.length, 1);
});

// ---------- misc ----------

test('hasUnsaved = stageDirty || diagramDirty || metaDirty', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  assert.equal(model.hasUnsaved(), false);
  model.addPerson({ ho_ten: 'x' });
  assert.equal(model.hasUnsaved(), true);
  // Meta-only cũng là thay đổi chưa ghi.
  const { model: m2 } = makeModel(seedCases('ready'));
  await m2.openCase(42);
  m2.updateCaseMeta('noi_niem_yet', 'xã Meta');
  assert.equal(m2.state.stageDirty, false);
  assert.equal(m2.state.diagramDirty, false);
  assert.equal(m2.state.metaDirty, true);
  assert.equal(m2.hasUnsaved(), true);
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

test('model khong depend DOM: module load duoc trong node (khong window)', async () => {
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
  const r = await model.saveCase();
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

test('newDraft: inheritance — stage co owner_row_id null + seed DUNG 1 node owner (MIN-136)', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
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

test('newDraft(two_party): stage khong owner_row_id + 30 slot canonical', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft('two_party');
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

// ---------- vòng 2: nguồn Done cho nháp mới (§13.20) ----------

function sourceStage() {
  const owner = crypto.randomUUID();
  const heir = crypto.randomUUID();
  const asset = crypto.randomUUID();
  return {
    source_case_id: 77,
    source_status: 'done',
    stage: {
      owner_row_id: owner,
      people: [
        { row_id: owner, entity_id: 12, ho_ten: 'Người Chủ',
          gioi_tinh: null, ngay_sinh: '1950', ngay_chet: null,
          so_giay_to: '001', ngay_cap: null, noi_cap: null,
          dia_chi: null, place_of_origin: null,
          loai_giay_to: null, loai_dia_chi: null },
        { row_id: heir, entity_id: null, ho_ten: 'Người Thừa Kế',
          gioi_tinh: 'Nữ', ngay_sinh: null, ngay_chet: null,
          so_giay_to: null, ngay_cap: null, noi_cap: null,
          dia_chi: null, place_of_origin: null,
          loai_giay_to: null, loai_dia_chi: null },
      ],
      assets: [
        { row_id: asset, entity_id: 21, so_serial: 'SRC 001',
          so_vao_so: null, so_thua_dat: null, so_to_ban_do: null,
          dia_chi: null, loai_so: null, hinh_thuc_su_dung: null,
          thoi_han: '2063', nguon_goc: null, ngay_cap: null,
          co_quan_cap: null, land_rows: null },
        { row_id: crypto.randomUUID(), entity_id: null,
          so_serial: '', so_vao_so: null, so_thua_dat: null,
          so_to_ban_do: null, dia_chi: null, loai_so: null,
          hinh_thuc_su_dung: null, thoi_han: null, nguon_goc: null,
          ngay_cap: null, co_quan_cap: null, land_rows: [] },
      ],
    },
  };
}

test('newDraft: đọc nguồn đúng 1 lần, stage nguồn + owner, không leak case/meta/diagram', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  const src = sourceStage();
  client.setSourceLatest(src);
  const r = await model.newDraft('inheritance');
  assert.equal(r.ok, true);
  const s = model.state;
  const sourceCalls = client.calls.filter(
    (c) => c.command === 'notary.workspace_source_latest');
  assert.equal(sourceCalls.length, 1);
  assert.deepEqual(sourceCalls[0].payload, {});
  assert.equal(s.status, 'ready');
  assert.equal(s.caseId, null);
  // Stage nguồn: giữ thứ tự, entity_id/null/[]/thoi_han, owner đã remap
  assert.deepEqual(s.stage.people, src.stage.people);
  assert.deepEqual(s.stage.assets, src.stage.assets);
  assert.equal(s.stage.owner_row_id, src.stage.owner_row_id);
  assert.equal(s.stageDirty, true);
  // committed vẫn rỗng — chưa có DB cho nháp này
  assert.deepEqual(s.committed, { people: [], assets: [] });
  // meta/diagram mới của nháp, không chép nguồn
  assert.equal(s.caseInfo.id, null);
  assert.equal(s.caseInfo.ngay_lap_ho_so, null);
  assert.equal(s.diagram.domain, 'inheritance');
  assert.equal(s.diagram.nodes.length, 1);
  assert.equal(s.diagram.nodes[0].id, 'owner');
  assert.equal(s.diagram.nodes[0].personId, null);
  assert.equal('source_case_id' in s, false);
});

test('newDraft(two_party): nguồn inheritance → bỏ owner key, giữ Người/Tài sản', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  const src = sourceStage();
  client.setSourceLatest(src);
  await model.newDraft('two_party');
  const s = model.state;
  assert.equal('owner_row_id' in s.stage, false);
  assert.deepEqual(s.stage.people, src.stage.people);
  assert.deepEqual(s.stage.assets, src.stage.assets);
  assert.equal(s.diagram.domain, 'two_party');
  assert.deepEqual(s.diagram.nodes.map((n) => n.id), TP_IDS);
});

test('newDraft: không có Done → Stage rỗng thành công, không dirty', async () => {
  const { model } = makeModel(seedCases('empty'));
  const r = await model.newDraft();
  assert.equal(r.ok, true);
  assert.equal(model.state.status, 'ready');
  assert.deepEqual(model.state.stage.people, []);
  assert.deepEqual(model.state.stage.assets, []);
  assert.equal(model.state.stageDirty, false);
});

test('newDraft: lỗi đọc nguồn hiện rõ, không nuốt thành nguồn rỗng', async () => {
  const client = { run: async () => ({ ok: false, error: {
    code: 'engine_unavailable', message: 'db busy', retryable: true,
    next_action: 'retry', details: null } }) };
  const model = M.createModel({ client, uuid });
  const r = await model.newDraft();
  assert.equal(r.ok, false);
  assert.equal(model.state.status, 'unavailable');
  assert.equal(model.state.error.code, 'engine_unavailable');
  assert.equal(model.canWrite(), false);
  assert.deepEqual(model.state.stage.people, []);
  assert.equal(model.state.stageDirty, false);
});

test('newDraft: loading khóa sửa/lưu đến khi nguồn trả về', async () => {
  let resolveSource;
  const client = { run: () => new Promise((res) => {
    resolveSource = res;
  }) };
  const model = M.createModel({ client, uuid });
  const pending = model.newDraft();
  assert.equal(model.state.status, 'loading');
  assert.equal(model.canWrite(), false);
  const blocked = await model.saveCase();
  assert.equal(blocked.ok, false);
  resolveSource({ ok: true, data: { stage: { people: [], assets: [] } } });
  await pending;
  assert.equal(model.state.status, 'ready');
  assert.equal(model.canWrite(), true);
});

test('newDraft: response nguồn của phiên cũ không ghi đè nháp mới', async () => {
  const resolvers = [];
  const client = { run: () => new Promise((res) => resolvers.push(res)) };
  const model = M.createModel({ client, uuid });
  const first = model.newDraft('inheritance');
  const second = model.newDraft('two_party');
  const late = sourceStage();
  resolvers[1]({ ok: true, data: { stage: { people: [], assets: [] } } });
  await second;
  resolvers[0]({ ok: true, data: late });
  await first;
  assert.equal(model.caseType(), 'two_party');
  assert.deepEqual(model.state.stage.people, []);
  assert.equal(model.state.stageDirty, false);
});

test('newDraft: sửa tay sau khi lấy nguồn không bị đọc lại/ghi đè', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  client.setSourceLatest(sourceStage());
  await model.newDraft();
  const row = model.state.stage.people[0];
  model.updatePersonField(row.row_id, 'ho_ten', 'Sửa Tay');
  assert.equal(model.state.stage.people[0].ho_ten, 'Sửa Tay');
  assert.equal(client.calls.filter(
    (c) => c.command === 'notary.workspace_source_latest').length, 1);
});

test('saveCase tu nguon: giu entity_id goi y + thoi_han le cua dong moi', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  const src = sourceStage();
  client.setSourceLatest(src);
  await model.newDraft('inheritance');
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const sent = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case').payload;
  assert.equal(sent.stage.people[0].entity_id, src.stage.people[0].entity_id);
  assert.equal(sent.stage.people[1].entity_id, null);
  assert.equal(sent.stage.assets[0].thoi_han, '2063');
  assert.equal(sent.stage.assets[1].thoi_han, undefined);
  assert.deepEqual(sent.stage.assets[1].land_rows, []);
  assert.equal(sent.stage.owner_row_id, src.stage.owner_row_id);
  assert.equal(client.calls.some(
    (c) => c.command === 'notary.workspace_create'), false);
});

test('updateCaseMeta case_type: doi loai → reset diagram buffer + stage key owner_row_id', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
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

test('two_party draft: addSlot chan; addPerson toi da 30; assign unique', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft('two_party');
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

test('MIN-136: seedDiagramSlots/ensureEmptyChildSlot khong con export', async () => {
  // Sinh node chi qua engine requiredSlots — helper client-side seed
  // 7 slot va auto-child da bi go khoi API cong khai.
  assert.equal(typeof M.seedDiagramSlots, 'undefined');
  assert.equal(typeof M.ensureEmptyChildSlot, 'undefined');
});

test('newTwoPartyState: canonical p1..p30 — export dung cho test/view', async () => {
  const st = M.newTwoPartyState();
  assert.equal(st.version, 3);
  assert.equal(st.domain, 'two_party');
  assert.deepEqual(st.nodes.map((n) => n.id), TP_IDS);
});

test('newDraft: draft diagram dung stage nhap — assign tu stage, pool tu stage', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
  const row = model.addPerson({ ho_ten: 'Người Nháp' });
  assert.ok(row);
  assert.equal(model.pool().people.length, 1);
  assert.equal(model.assignPerson('owner', row.row_id), true);
  assert.equal(model.pool().people.length, 0);
  // pointer stage theo mirror — saveCase gui owner_row_id hop le
  assert.equal(model.state.stage.owner_row_id, row.row_id);
});

test('movePerson: move vao node trong / swap / unassign ve Pool — owner mirror theo pointer', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
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

test('updateCaseMeta: nhap local; saveCase gui meta day du + idempotency_key', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.newDraft();
  assert.equal(model.updateCaseMeta('document_type', 'thoa_thuan'), true);
  assert.equal(model.updateCaseMeta('noi_niem_yet', 'xã Yên Sở'), true);
  assert.equal(model.updateCaseMeta('bogus', 'x'), false);
  const owner = model.addPerson({ ho_ten: 'Người Chết' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.assignPerson('owner', owner.row_id);
  const draftId = model.state.draftId;
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
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

test('saveCase two_party: payload khong owner_row_id, case_type two_party', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.newDraft('two_party');
  model.addPerson({ ho_ten: 'Bên A 1' });
  model.addPerson({ ho_ten: 'Bên B 1' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  const ps = model.state.stage.people;
  model.assignPerson('p1', ps[0].row_id);
  model.assignPerson('p16', ps[1].row_id);
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
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

test('saveCase: retry sau loi mang giu draftId → created:true mot lan, khong tao trung', async () => {
  const client = fakeClient({});
  const model = M.createModel({ client, uuid });
  await model.newDraft();
  const owner = model.addPerson({ ho_ten: 'Người Chết' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.assignPerson('owner', owner.row_id);
  const draftId = model.state.draftId;
  const orig = client.run.bind(client);
  let dropped = null;
  client.run = async (command, payload) => {
    if (command === 'notary.workspace_save_case' && !dropped) {
      dropped = payload.idempotency_key;
      return { ok: false, error: {
        code: 'engine_unavailable', message: 'mat ket noi', retryable: true,
        next_action: 'retry', details: null } };
    }
    return orig(command, payload);
  };
  const r1 = await model.saveCase();
  assert.equal(r1.ok, false);
  assert.equal(model.state.caseId, null);
  assert.equal(model.state.draftId, draftId, 'giu key qua retry');
  assert.equal(dropped, draftId);

  const r2 = await model.saveCase();
  assert.equal(r2.ok, true, JSON.stringify(r2.error));
  assert.equal(r2.data.created, true);
  const cid = model.state.caseId;
  const keys = Object.keys(client.cases).filter((k) => Number(k) === cid);
  assert.equal(keys.length, 1, 'chi mot case duoc tao');
  assert.equal(client.cases[cid].status, 'done');
  assert.equal(model.state.revision, 1);
});

test('saveCase: stage_validation_error giu nhap + fieldErrors', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
  const bad = model.addPerson({ ho_ten: '   ' });  // ho_ten trong → required
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.setOwnerRow(bad.row_id);                  // pointer hop le → toi
                                                  // duoc field check
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'stage_validation_error');
  assert.ok(model.state.fieldErrors.length >= 1);
  assert.equal(model.isDraft(), true);          // nhap nguyen ven
});

test('saveCase new: thieu owner → workspace_owner_required, nhap giu nguyen', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.newDraft();
  model.addPerson({ ho_ten: 'Ai Do' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_owner_required');
  assert.equal(model.isDraft(), true);
});

test('evaluateDiagram tren nhap: gui case.case_type + stage, khong gui case_id', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.newDraft();
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
  await model.newDraft('two_party');
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
  await model.newDraft();
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
  const resolvers = [];
  client.run = (cmd, p) => new Promise((res) => {
    resolvers.push(() => origRun(cmd, p).then(res));
  });
  const p = model.openCase(42);
  const d = model.newDraft();          // session doi truoc khi response
  resolvers.forEach((fn) => fn());
  await Promise.all([p, d]);
  // state van la nhap — response workspace_get cua case 42 bi bo
  assert.equal(model.isDraft(), true);
  assert.equal(model.state.caseId, null);
});

test('ca nhap va case cu chi persist khi nguoi dung bam Luu ho so', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'A' });
  model.addAsset({ so_serial: 'AA000001', dia_chi: 'x' });
  model.assignPerson('spouse', model.state.stage.people.at(-1).row_id);
  // Sửa buffer không phát command ghi nào.
  assert.equal(client.calls.filter((c) => c.command.includes('save') ||
    c.command.includes('commit') ||
    c.command.includes('diagram_save')).length, 0);
  const r = await model.saveCase();
  assert.equal(r.ok, true);
  const writes = client.calls.filter((c) =>
    c.command === 'notary.workspace_save_case');
  assert.equal(writes.length, 1);
  assert.equal(client.calls.some(
    (c) => c.command === 'notary.workspace_create' ||
      c.command === 'notary.workspace_commit_stage' ||
      c.command === 'notary.diagram_save'), false);
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

test('đợt3 saveCase meta-only: payload case+stage+diagram, metaDirty clear', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.updateCaseMeta('noi_niem_yet', 'xã Mới');
  model.updateCaseMeta('noi_dung_viec', 'Việc mới');
  assert.equal(model.state.metaDirty, true);
  assert.equal(model.hasUnsaved(), true);
  const rev = model.state.revision;
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
  assert.ok(call.payload.case, 'saveCase luôn gửi snapshot case');
  assert.equal(call.payload.case.noi_niem_yet, 'xã Mới');
  assert.equal(call.payload.case.noi_dung_viec, 'Việc mới');
  assert.equal(call.payload.case.case_type, 'inheritance');
  assert.ok(call.payload.stage.people.length);
  assert.ok(call.payload.diagram.state);
  assert.equal(call.payload.base_revision, rev);
  assert.equal(model.state.metaDirty, false);
  assert.equal(model.state.revision, rev + 1);
  assert.equal(model.state.committedCaseInfo.noi_niem_yet, 'xã Mới');
  // Reopen: meta da luu quay ve tu server.
  await model.openCase(42);
  assert.equal(model.state.caseInfo.noi_niem_yet, 'xã Mới');
  assert.equal(model.state.caseInfo.noi_dung_viec, 'Việc mới');
});

test('đợt3 saveCase: khong sua meta van gui snapshot case+stage+diagram', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.addPerson({ ho_ten: 'Người Mới' });       // stageDirty only
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
  assert.ok(call.payload.case, 'saveCase luôn có block case');
  assert.equal(call.payload.case.case_type, 'inheritance');
  assert.equal(call.payload.case.ngay_lap_ho_so, null);
  assert.equal(call.payload.stage.people.length, 5);
  assert.ok(call.payload.diagram.state.nodes.length);
});

test('đợt3 commit meta: uq_id danh ba hop le → server resolve ten master', async () => {
  const seed = seedCases('ready');
  seed.__customers = [{ id: 5, ho_ten: 'Người Danh Bạ' }];
  const { model, client } = makeModel(seed);
  await model.openCase(42);
  model.updateCaseMeta('nguoi_nhan_uy_quyen', 'Người Danh Bạ');
  model.updateCaseMeta('nguoi_nhan_uy_quyen_id', 5);
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen,
    'Người Danh Bạ');
  assert.equal(model.state.caseInfo.nguoi_nhan_uy_quyen_id, 5);
  // Id khong ton tai → validation_error, meta giu nguyen de sua lai.
  model.updateCaseMeta('nguoi_nhan_uy_quyen_id', 999);
  const r2 = await model.saveCase();
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
    if (cmd === 'notary.workspace_save_case' && p.case) {
      p = { ...p, case: { ...p.case, case_type: 'two_party' } };
    }
    return orig(cmd, p);
  };
  const r = await model.saveCase();
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

test('saved conversion: dirty Stage được ghi cùng hành động, không bị chặn "Lưu trước"', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.diagram.nodes.find((n) => n.id === 'child_2').hidden = true;
  model.state.diagramDirty = true;
  const before = structuredClone(model.state.diagram);
  const original = client.run.bind(client);
  let writes = 0;
  client.run = async (command, payload) => {
    if (command !== 'notary.workspace_convert_type') return original(command, payload);
    writes++;
    return {ok:false,error:{code:'workspace_conflict',details:{server_revision:8}}};
  };
  model.updatePersonField(model.state.stage.people[0].row_id, 'ho_ten', 'Chữ đang sửa');
  const request = {case_type:'two_party',document_type:'dat_coc',confirm_diagram_reset:true};
  // R7: buffer Stage đang sửa không chặn convert — được ghi trước trong
  // cùng hành động rồi mới gọi convert (convert lỗi conflict thật).
  const conv = await model.convertCaseType(request);
  assert.equal(conv.ok, false);
  assert.equal(writes, 1, 'convert vẫn được gọi sau khi ghi buffer');
  const saveCall = client.calls.find(
    (c) => c.command === 'notary.workspace_save_case');
  assert.ok(saveCall, 'buffer Stage phải được ghi trước khi convert');
  assert.equal(model.state.stage.people[0].ho_ten, 'Chữ đang sửa',
    'chữ đang sửa không bị mất');
  assert.equal(model.state.stageDirty, false);
  assert.deepEqual(model.state.diagram, before);
  // Convert lỗi sau khi buffer đã được ghi: Diagram đang sửa đã nằm trong
  // bản lưu (không mất), nên dirty sạch; loại hồ sơ giữ nguyên.
  assert.equal(model.state.diagramDirty, false);
  assert.equal(model.hasUnsaved(), false);
  assert.equal(model.state.caseInfo.case_type, 'inheritance');
});

test('conversion pending blocks editing; success resets Diagram and invalidates Word result', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const before = structuredClone(model.state.stage);
  let finish;
  const original = client.run.bind(client);
  client.run = (command, payload) => command === 'notary.workspace_convert_type'
    ? new Promise(resolve => {finish=resolve;}) : original(command,payload);
  model.state.diagramDirty = true;
  model.state.wordOptions = {documents:[]};
  model.state.wordResult = {old:true};
  const pending = model.convertCaseType({case_type:'two_party',document_type:'dat_coc',confirm_diagram_reset:true});
  assert.equal(model.canWrite(), false);
  const name = model.state.stage.people[0].ho_ten;
  model.updatePersonField(model.state.stage.people[0].row_id, 'ho_ten', 'Must not apply');
  assert.equal(model.state.stage.people[0].ho_ten, name);
  const stage = structuredClone(before); delete stage.owner_row_id;
  finish({ok:true,data:{case:{...model.state.caseInfo,case_type:'two_party',document_type:'dat_coc',revision:8},
    stage,diagram:{state:M.newTwoPartyState(),render_model:null},
    capabilities:{intake:[],diagram:true,word_export:true}}});
  assert.equal((await pending).ok,true);
  assert.deepEqual(model.state.stage.people,before.people);
  assert.deepEqual(model.state.stage.assets,before.assets);
  assert.equal(model.state.diagramDirty,false);
  assert.equal(model.state.wordOptions,null);
  assert.equal(model.state.wordResult,null);
  assert.equal(model.state.diagram.domain,'two_party');
});

// ---------- issue 13: saveCase (workspace_save_case) ----------

function seedSaveCaseModel(client) {
  const model = M.createModel({ client, uuid });
  const s = model.state;
  s.status = 'ready';
  s.caseId = 42;
  s.caseInfo = { id: 42, case_type: 'inheritance',
                 document_type: 'khai_nhan', status: 'draft',
                 locked: false, revision: 3, ngay_lap_ho_so: '2024-05-01',
                 noi_niem_yet: null, ghi_chu: null,
                 nguoi_nhan_uy_quyen: null,
                 nguoi_nhan_uy_quyen_id: null, noi_dung_viec: null };
  s.committedCaseInfo = structuredClone(s.caseInfo);
  s.backendMode = 'real';
  s.revision = 3;
  s.locked = false;
  s.unsupported = false;
  s.capabilities = { intake: [], diagram: true, word_export: true };
  s.committed = { people: [{ row_id: 'c1', ho_ten: 'Người Đã Lưu' }],
                  assets: [{ row_id: 'a1', so_serial: 'S-001' }] };
  s.stage = structuredClone(s.committed);
  s.stage.owner_row_id = 'c1';
  s.committedDiagram = { version: 3, domain: 'inheritance', nodes: [
    { id: 'owner', personId: 'c1', parentSlotIds: [],
      spouseSlotId: null, ownPositions: [1], receivePositions: [],
      hidden: false, deleted: false }] };
  s.diagram = structuredClone(s.committedDiagram);
  s.diagramDirty = true;
  return model;
}

function savedWorkspace(payload, revision, status = 'done') {
  return {
    case: { id: 42, case_type: payload.case.case_type,
            document_type: payload.case.document_type, status,
            locked: false, revision },
    backend_mode: 'real',
    capabilities: { intake: [], diagram: true, word_export: true },
    stage: structuredClone(payload.stage),
    diagram: { state: structuredClone(payload.diagram.state),
               render_model: null },
    warnings: [],
  };
}

test('B5 saveCase conflict: giữ model + dirty, không tự merge/retry', async () => {
  const calls = [];
  const client = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    return { ok: false, error: { code: 'workspace_conflict',
      message: 'revision khac', details: { server_revision: 9 } } };
  } };
  const model = seedSaveCaseModel(client);
  model.updatePersonField('c1', 'ho_ten', 'Chữ Nháp');
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 'notary.workspace_save_case');
  assert.equal(calls[0][1].case_id, 42);
  assert.equal(calls[0][1].base_revision, 3);
  assert.equal('idempotency_key' in calls[0][1], false);
  assert.equal(model.state.status, 'conflict');
  assert.equal(model.state.revision, 3, 'revision client không đổi');
  assert.equal(model.state.stage.people[0].ho_ten, 'Chữ Nháp');
  assert.equal(model.state.stageDirty, true, 'dirty phải còn');
  assert.equal(model.state.diagramDirty, true, 'dirty diagram phải còn');
  assert.equal(model.state.savingCase, false);
  assert.equal(model.state.busy, null);
});

test('B5 saveCase lỗi mạng/validation: giữ dirty, không thay model', async () => {
  const client = { run: async () => ({ ok: false, error: {
    code: 'engine_unavailable', message: 'mat ket noi' } }) };
  const model = seedSaveCaseModel(client);
  model.updateAssetField('a1', 'so_serial', 'S-002');
  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(model.state.caseId, 42);
  assert.equal(model.state.revision, 3);
  assert.equal(model.state.stage.assets[0].so_serial, 'S-002');
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.error.code, 'engine_unavailable');
  assert.equal(model.state.notice, null, 'không báo thành công khi lỗi');

  const fieldClient = { run: async () => ({ ok: false, error: {
    code: 'stage_validation_error', message: 'loi field',
    details: { field_errors: [{ row_id: 'c1', field: 'ho_ten',
                                code: 'required', message: 'bat buoc' }] } } }) };
  const m2 = seedSaveCaseModel(fieldClient);
  const r2 = await m2.saveCase();
  assert.equal(r2.ok, false);
  assert.equal(m2.state.fieldErrors.length, 1);
  assert.equal(m2.state.stageDirty, false,
    'seed stage chưa dirty nhưng lỗi không được ghi đè model');
});

test('B5 saveCase: khóa snapshot thứ hai và bỏ response thành công của session cũ', async () => {
  let resolveSave;
  const calls = [];
  const saveCalls = [];
  const client = { run: (cmd, payload) => {
    calls.push([cmd, payload]);
    if (cmd === 'notary.workspace_source_latest') {
      return Promise.resolve({ ok: true, data: {
        schema_version: SCHEMA, backend_mode: 'mock',
        source_case_id: null, source_status: null,
        stage: { people: [], assets: [] } } });
    }
    saveCalls.push([cmd, payload]);
    return new Promise((resolve) => { resolveSave = resolve; });
  } };
  const model = seedSaveCaseModel(client);
  const pending = model.saveCase();
  assert.equal(model.state.savingCase, true);
  assert.equal(model.canWrite(), false, 'editor phải bị khóa khi đang lưu');
  const second = await model.saveCase();
  assert.equal(second.ok, false, 'không cho snapshot thứ hai chen vào');
  assert.equal(saveCalls.length, 1);
  assert.equal(model.updatePersonField('c1', 'ho_ten', 'Gõ chen'), undefined);
  assert.equal(model.state.stage.people[0].ho_ten, 'Người Đã Lưu',
    'mutator bị chặn trong lúc lưu');

  // Người dùng mở nháp khác trước khi response cũ về.
  await model.newDraft('inheritance');
  resolveSave({ ok: true, data: savedWorkspace(saveCalls[0][1], 4) });
  const r = await pending;
  assert.equal(r.ok, true);
  assert.equal(model.state.caseId, null, 'response cũ không được ghi đè');
  assert.equal(model.state.status, 'ready');
  assert.equal(model.state.diagramDirty, true, 'nháp mới giữ dirty seed');
  assert.equal(model.state.notice, null);
  assert.equal(model.state.savingCase, false);
});

// ---------- nhãn trạng thái nghiệp vụ (D2) ----------

test('statusLabel: draft→Nháp, done→Đã lưu, giữ nguyên dirty/unknown', async () => {
  const { model } = makeModel(seedCases('ready', 'done'));
  await model.openCase(42);
  assert.equal(model.state.stageDirty, false);
  assert.equal(model.statusLabel(), 'Nháp');

  await model.openCase(44);
  assert.equal(model.state.caseInfo.status, 'done');
  assert.equal(model.statusLabel(), 'Đã lưu');
  model.addPerson();
  assert.equal(model.state.stageDirty, true,
    'case Done phải dirty khi sửa');
  assert.equal(model.statusLabel(), 'Đã lưu',
    'Done + local dirty vẫn Đã lưu (nhãn độc lập chấm dirty)');

  model.state.caseInfo.status = 'archived';
  assert.equal(model.statusLabel(), 'archived');

  await model.newDraft('inheritance');
  assert.equal(model.statusLabel(), 'Nháp',
    'nháp mới đọc caseInfo.status=draft, không suy từ isDraft');
});

test('saveCase thành công: thay model bằng workspace, xóa ba dirty flag', async () => {
  const calls = [];
  const client = { run: async (cmd, payload) => {
    calls.push([cmd, payload]);
    return { ok: true, data: savedWorkspace(payload, 8) };
  } };
  const model = seedSaveCaseModel(client);
  model.updatePersonField('c1', 'ho_ten', 'Người Lưu');
  model.updateCaseMeta('noi_niem_yet', 'Xã A');
  const r = await model.saveCase();
  assert.equal(r.ok, true, JSON.stringify(r.error));
  assert.equal(calls.length, 1);
  const p = calls[0][1];
  assert.equal(p.case.noi_niem_yet, 'Xã A');
  assert.equal(p.stage.people[0].ho_ten, 'Người Lưu');
  assert.deepEqual(p.docx_import, { version: 1, sources: [] });
  const s = model.state;
  assert.equal(s.caseId, 42);
  assert.equal(s.revision, 8);
  assert.equal(s.status, 'ready');
  assert.equal(s.caseInfo.status, 'done');
  assert.equal(s.stage.people[0].ho_ten, 'Người Lưu');
  assert.equal(s.stageDirty, false);
  assert.equal(s.diagramDirty, false);
  assert.equal(s.metaDirty, false);
  assert.equal(s.notice, null, 'R14: không toast chữ thành công');
  assert.equal(s.savingCase, false);
});

// ---------- đợt 5 / E2: duplicateCase — key theo ý định + session guard ----------

test('duplicateCase: timeout giữ key để retry, success đổi key + hydrate bản sao', async () => {
  const { model, client } = makeModel(seedCases('ready', 'done'));
  await model.openCase(42);
  const sourceBefore = JSON.parse(JSON.stringify(client.cases[44]));
  const realRun = client.run.bind(client);
  const dupCalls = [];
  let failOnce = true;
  client.run = async (cmd, payload) => {
    if (cmd === 'notary.workspace_duplicate') {
      dupCalls.push(JSON.parse(JSON.stringify(payload)));
      if (failOnce) {
        failOnce = false;
        throw new Error('timeout');
      }
    }
    return realRun(cmd, payload);
  };

  const first = await model.duplicateCase(44);
  assert.equal(first.ok, false);
  const kept = model.state.duplicatePending;
  assert.ok(kept, 'timeout phải giữ pending key');
  assert.equal(kept.sourceId, 44);
  assert.equal(model.state.duplicating, null);
  assert.equal(model.state.caseId, 42, 'lỗi giữ workspace cũ');

  const second = await model.duplicateCase(44);
  assert.equal(second.ok, true);
  assert.equal(second.data.created, true);
  assert.equal(dupCalls[1].idempotency_key, kept.key,
    'retry cùng ý định phải dùng lại key');
  assert.equal(dupCalls[1].source_case_id, 44);
  assert.equal(model.state.caseId, second.data.case.id);
  assert.equal(model.state.caseInfo.status, 'draft');
  assert.equal(model.state.revision, 1);
  assert.equal(model.state.stageDirty, false);
  assert.equal(model.state.diagramDirty, false);
  assert.equal(model.state.metaDirty, false);
  assert.equal(model.state.duplicatePending, null);
  assert.equal(model.state.notice, null, 'R14: không toast chữ thành công');
  assert.deepEqual(client.cases[44], sourceBefore, 'không sửa nguồn');

  const third = await model.duplicateCase(44);
  assert.equal(third.ok, true);
  assert.notEqual(dupCalls[2].idempotency_key, dupCalls[1].idempotency_key,
    'ý định sau success phải có key mới');
  assert.notEqual(third.data.case.id, second.data.case.id);
});

test('duplicateCase: lỗi nghiệp vụ không giữ key; stale response không áp', async () => {
  const { model, client } = makeModel(seedCases('ready', 'done'));
  await model.openCase(42);
  const missing = await model.duplicateCase(999);
  assert.equal(missing.ok, false);
  assert.equal(missing.error.code, 'case_not_found');
  assert.equal(model.state.duplicatePending, null);
  assert.equal(model.state.caseId, 42);

  const realRun = client.run.bind(client);
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  let dupPayload = null;
  client.run = (cmd, payload) => {
    if (cmd === 'notary.workspace_duplicate') {
      dupPayload = JSON.parse(JSON.stringify(payload));
      return gate.then(() => realRun(cmd, payload));
    }
    return realRun(cmd, payload);
  };
  const pending = model.duplicateCase(44);
  await Promise.resolve();
  assert.equal(model.state.duplicating, 44);
  assert.equal(model.canWrite(), false, 'đang nhân bản khóa sửa');
  await model.openCase(42);          // phiên đổi trước khi response về
  release();
  const late = await pending;
  assert.equal(late.ok, true);
  assert.equal(dupPayload.source_case_id, 44);
  assert.equal(model.state.caseId, 42, 'response bản sao của phiên cũ bị bỏ');
  assert.equal(model.state.duplicating, null);
});

// G3: trang thai loi hien thi phai thay the theo lan ghi gan nhat —
// banner cu (state.error) khong duoc treo qua lan bam sau.
function scriptedFailClient(responses) {
  let i = 0;
  return { run: async () => responses[Math.min(i++, responses.length - 1)] };
}

test('G3 saveCase: moi lan loi chi bat dung kenh cua lan do', async () => {
  const owner = { ok: false, error: {
    code: 'workspace_owner_required', message: 'chua chon owner' } };
  const field = { ok: false, error: {
    code: 'stage_validation_error', message: 'loi field',
    details: { field_errors: [{ row_id: 'c1', field: 'ho_ten',
                                code: 'required', message: 'bat buoc' }] } } };
  const diagram = { ok: false, error: {
    code: 'diagram_invalid_state', message: 'so do sai',
    details: { errors: [{ code: 'missing_land_owner',
                          message: 'thieu chu dat' }] } } };
  const model = seedSaveCaseModel(
    scriptedFailClient([owner, field, diagram, owner]));

  // (a) loi thuong → banner bat, khong co loi field/diagram
  const r1 = await model.saveCase();
  assert.equal(r1.ok, false);
  assert.equal(model.state.error.code, 'workspace_owner_required');
  assert.deepEqual(model.state.fieldErrors, []);
  assert.deepEqual(model.state.diagramErrors, []);

  // (b) stage_validation_error → fieldErrors moi, banner tat
  const r2 = await model.saveCase();
  assert.equal(r2.error.code, 'stage_validation_error');
  assert.equal(model.state.error, null, 'banner cua lan truoc phai tat');
  assert.equal(model.state.fieldErrors.length, 1);
  assert.equal(model.state.fieldErrors[0].field, 'ho_ten');
  assert.deepEqual(model.state.diagramErrors, []);

  // (c) diagram_invalid_state → diagramErrors moi, fieldErrors + banner sach
  const r3 = await model.saveCase();
  assert.equal(r3.error.code, 'diagram_invalid_state');
  assert.equal(model.state.error, null);
  assert.deepEqual(model.state.fieldErrors, []);
  assert.equal(model.state.diagramErrors.length, 1);
  assert.equal(model.state.diagramErrors[0].code, 'missing_land_owner');

  // (d) loi thuong lai → ca hai kenh field/diagram sach, banner moi
  const r4 = await model.saveCase();
  assert.equal(r4.error.code, 'workspace_owner_required');
  assert.equal(model.state.error.code, 'workspace_owner_required');
  assert.deepEqual(model.state.fieldErrors, []);
  assert.deepEqual(model.state.diagramErrors, []);
});

test('G3 saveCase case cu: stage_validation_error tat banner cu', async () => {
  const field = { ok: false, error: {
    code: 'stage_validation_error', message: 'loi field',
    details: { field_errors: [{ row_id: 'a1', field: 'so_serial',
                                code: 'required', message: 'bat buoc' }] } } };
  const model = seedSaveCaseModel(scriptedFailClient([field]));
  model.state.stageDirty = true;
  model.state.error = { code: 'workspace_owner_required', message: 'cu' };
  model.state.diagramErrors = [{ code: 'missing_land_owner' }];

  const r = await model.saveCase();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'stage_validation_error');
  assert.equal(model.state.error, null, 'banner cu phai tat');
  assert.equal(model.state.fieldErrors.length, 1);
  assert.equal(model.state.fieldErrors[0].field, 'so_serial');
  assert.deepEqual(model.state.diagramErrors, []);
});

// G3: sua du lieu lien quan phai don loi cua lan Luu truoc.
test('G3 setOwnerRow: chon duoc owner → tat banner workspace_owner_required', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  const people = model.state.stage.people;
  const other = people.find(
    (p) => p.row_id !== model.state.stage.owner_row_id);
  model.state.error = { code: 'workspace_owner_required', message: 'cu' };

  assert.equal(model.setOwnerRow(other.row_id), true);
  assert.equal(model.state.error, null,
               'da co owner thi banner chua-owner phai tat');
});

test('G3 setOwnerRow: go owner (null) → banner workspace_owner_required con', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  assert.ok(model.state.stage.owner_row_id);
  model.state.error = { code: 'workspace_owner_required', message: 'cu' };
  model.state.diagramErrors = [{ code: 'missing_land_owner' }];

  assert.equal(model.setOwnerRow(null), true);
  assert.equal(model.state.error.code, 'workspace_owner_required',
               'chua co owner thi nguyen nhan con — giu banner');
  assert.deepEqual(model.state.diagramErrors, [],
                   'go owner van la sua so do');
});

test('G3 toggleNodePosition: sua so do → diagramErrors sach', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.diagramErrors = [{ code: 'missing_land_owner' }];

  assert.equal(model.toggleNodePosition('spouse', 'receive', 2), true);
  assert.deepEqual(model.state.diagramErrors, []);
});

test('G3 addAsset: chi don loi danh sach assets, giu loi khac', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.fieldErrors = [
    { row_id: null, field: 'assets', code: 'required', message: 'chua co' },
    { row_id: 'a1', field: 'so_serial', code: 'required', message: 'bat buoc' },
  ];

  assert.ok(model.addAsset({ so_serial: 'G1-9' }));
  assert.deepEqual(model.state.fieldErrors,
                   [{ row_id: 'a1', field: 'so_serial', code: 'required',
                      message: 'bat buoc' }]);
});

test('G3 addPerson: chi don loi danh sach people, giu loi khac', async () => {
  const { model } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.state.fieldErrors = [
    { row_id: null, field: 'people', code: 'required', message: 'chua co' },
    { row_id: 'a1', field: 'so_serial', code: 'required', message: 'bat buoc' },
  ];

  assert.ok(model.addPerson({ ho_ten: 'Nguoi Moi' }));
  assert.deepEqual(model.state.fieldErrors,
                   [{ row_id: 'a1', field: 'so_serial', code: 'required',
                      message: 'bat buoc' }]);
});
