// Pure-state tests cho case-drafting-model.js (MIN-111).
// Model la state machine thuan — khong DOM, khong Node API ngoai crypto/uuid
// inject duoc. Test inject command client gia co semantics mock adapter
// (fixtures shell/test/fixtures/notary-case-drafting/*.json) va khong cham
// sidecar/IPC.
//
// Phu theo brief: load, dirty Stage, commit success/fail, derived Pool
// (Stage committed − Diagram assignment), draft Diagram, revision conflict,
// locked read-only, mock banner.
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

// Model chua ton tai → require fail cho den khi implement xong (TDD).
const M = require('../src/renderer/notary/case-drafting-model.js');

const uuid = () => crypto.randomUUID();

function loadFixture(name) {
  return JSON.parse(
    fs.readFileSync(path.join(FIX_DIR, `${name}.json`), 'utf8'));
}

function fakeRenderModel(state, stage) {
  // Render_model toi thieu dung shape contract §7.2 — test khong can gia
  // tri that, chi can presence/status de model luu + expose.
  const nodes = (state && state.nodes || []).filter(
    (n) => n && !n.deleted && n.personId);
  const landowner = nodes.find((n) => n.isLandOwner);
  return {
    engineVersion: 2,
    status: landowner ? 'complete' : 'invalid',
    allocations: {},
    breakdowns: [],
    requiredSlots: [],
    warnings: [],
    errors: landowner ? []
      : [{ code: 'missing_land_owner', message: 'no owner' }],
    unresolvedEstates: [],
    conservation: { allocated: '0', unresolved: '0', total: '0' },
  };
}

// Client gia mo phong notary_mock_adapter tren seed cases: revision counter,
// workspace_conflict khi base_revision khac, stage_validation_error khi
// ho_ten rong, workspace_locked khi locked, prune personId ngoai stage.
function fakeClient(seed) {
  const cases = {};
  for (const [cid, c] of Object.entries(seed)) {
    cases[Number(cid)] = JSON.parse(JSON.stringify(c));
    cases[Number(cid)].id = Number(cid);
  }
  let nextEid = 900;
  const calls = [];

  const ok = (data, extra = {}) => ({ ok: true, data, ...extra });
  const fail = (code, message, details) => ({
    ok: false,
    error: { code, message: message || code, retryable: false,
             next_action: null, details: details || null },
  });

  function getCase(payload) {
    const c = cases[payload && payload.case_id];
    if (!c) return { err: fail('case_not_found', 'khong tim thay ho so') };
    return { c };
  }

  function workspaceData(c) {
    const supported = c.case_type === 'inheritance';
    const dg = c.diagram;
    return {
      schema_version: 'notary.case-drafting.v1',
      backend_mode: 'mock',
      case: {
        id: c.id, case_type: c.case_type,
        document_type: c.document_type, status: c.status,
        locked: !!c.locked, revision: c.revision,
      },
      stage: JSON.parse(JSON.stringify(c.stage)),
      diagram: {
        domain: 'inheritance',
        state: JSON.parse(JSON.stringify(dg.state)),
        render_model: dg.render_model === 'auto'
          ? fakeRenderModel(dg.state, c.stage)
          : dg.render_model,
        warnings: dg.warnings || [],
      },
      capabilities: {
        intake: supported ? ['image', 'pdf', 'docx', 'xlsx', 'text'] : [],
        diagram: supported,
        word_export: supported,
      },
    };
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
        if (c.case_type !== 'inheritance') {
          return fail('case_type_unsupported', 'chua ho tro');
        }
        if (payload.base_revision !== c.revision) {
          return fail('workspace_conflict', 'revision khac',
                      { server_revision: c.revision });
        }
        const fieldErrors = [];
        for (const p of payload.stage.people || []) {
          if (!p.ho_ten || !String(p.ho_ten).trim()) {
            fieldErrors.push({ row_id: p.row_id, field: 'ho_ten',
                               code: 'required', message: 'bat buoc' });
          }
        }
        if (fieldErrors.length) {
          return fail('stage_validation_error', 'loi field',
                      { field_errors: fieldErrors });
        }
        const stage = JSON.parse(JSON.stringify(payload.stage));
        for (const row of [...stage.people, ...stage.assets]) {
          if (row.entity_id == null) row.entity_id = nextEid++;
        }
        c.stage = stage;
        // prune personId khong con trong stage (mock _prune_diagram)
        const ids = new Set(stage.people.map((p) => p.row_id));
        for (const n of c.diagram.state.nodes || []) {
          if (n.personId && !ids.has(n.personId)) n.personId = null;
        }
        c.diagram.render_model =
          fakeRenderModel(c.diagram.state, c.stage);
        c.revision += 1;
        return ok({
          schema_version: 'notary.case-drafting.v1',
          revision: c.revision,
          stage: JSON.parse(JSON.stringify(c.stage)),
          diagram: {
            state: JSON.parse(JSON.stringify(c.diagram.state)),
            render_model: c.diagram.render_model,
          },
        });
      }
      case 'notary.diagram_evaluate': {
        const { c, err } = getCase(payload);
        if (err) return err;
        return ok({
          schema_version: 'notary.case-drafting.v1',
          evaluated_revision: c.revision,
          render_model:
            fakeRenderModel(payload.diagram.state, c.stage),
        });
      }
      case 'notary.diagram_save': {
        const { c, err } = getCase(payload);
        if (err) return err;
        if (c.locked) return fail('workspace_locked', 'da khoa');
        if (payload.base_revision !== c.revision) {
          return fail('workspace_conflict', 'revision khac',
                      { server_revision: c.revision });
        }
        const ids = new Set(c.stage.people.map((p) => p.row_id));
        for (const n of payload.diagram.state.nodes || []) {
          if (n.personId && !ids.has(n.personId)) {
            return fail('diagram_reference_outside_stage',
                        'personId ngoai stage',
                        { personId: n.personId });
          }
        }
        c.diagram.state = JSON.parse(JSON.stringify(payload.diagram.state));
        c.diagram.render_model =
          fakeRenderModel(c.diagram.state, c.stage);
        c.revision += 1;
        return ok({
          schema_version: 'notary.case-drafting.v1',
          revision: c.revision,
          diagram: {
            state: JSON.parse(JSON.stringify(c.diagram.state)),
            render_model: c.diagram.render_model,
          },
        });
      }
      case 'notary.intake_analyze': {
        const { c, err } = getCase(payload);
        if (err) return err;
        const sid = payload.sources[0].source_id;
        return ok({
          schema_version: 'notary.case-drafting.v1',
          suggestions: [{
            suggestion_id: '99999999-9999-4999-8999-999999999999',
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
        return ok({
          schema_version: 'notary.case-drafting.v1',
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
          schema_version: 'notary.case-drafting.v1',
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
  assert.equal(s.diagram.nodes.length, 4);
  assert.equal(s.backendMode, 'mock');
  assert.equal(model.mockBanner(), 'Dữ liệu mô phỏng');
  assert.equal(s.locked, false);
  assert.equal(s.unsupported, false);
  // khong co field `confirmed` o bat cu cho nao trong suggestion/stage
  assert.equal(JSON.stringify(s).includes('"confirmed"'), false);
});

test('openCase: backend_mode real thi khong co banner mo phong', async () => {
  const client = { run: async (cmd) => {
    if (cmd === 'notary.workspace_get') {
      const seed = loadFixture('empty').cases['43'];
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
  assert.equal(model.isStageEmpty(), true);
  assert.equal(s.renderModel, null);     // chua tung evaluate
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

test('openCase: case_type khac inheritance → unsupported + Chua ho tro', async () => {
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

test('addPerson/updatePerson/removeStageRow → stageDirty; commit reset', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.equal(model.state.stageDirty, false);

  const row = model.addPerson({ ho_ten: 'Người Mẫu Z' });
  assert.ok(row.row_id);
  assert.match(row.row_id, /^[0-9a-f-]{36}$/);   // uuid4 shape
  assert.equal(row.entity_id, null);
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.stage.people.length, 1);

  model.updatePersonField(row.row_id, 'ngay_sinh', '1999');
  assert.equal(model.state.stage.people[0].ngay_sinh, '1999');

  const r = await model.commitStage();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.stageDirty, false);
  assert.equal(s.revision, 2);                   // 1 → 2
  assert.equal(s.stage.people[0].entity_id, 900); // backend gan entity_id
  // payload gui di co base_revision + toan bo stage snapshot
  const sent = client.calls.at(-1).payload;
  assert.equal(sent.base_revision, 1);
  assert.equal(sent.stage.people.length, 1);

  // xoa dong → dirty lai
  model.removeStageRow(row.row_id);
  assert.equal(model.state.stageDirty, true);
  assert.equal(model.state.stage.people.length, 0);
});

test('commitStage: stage_validation_error → fieldErrors theo row_id, stage giu draft', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const row = model.addPerson({ ho_ten: '' });   // rong → required
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
  assert.equal(pool.assets.length, 1);           // asset luon o pool (v1)

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
  // A tro lai pool
  assert.ok(model.pool().people.some((p) => p.ho_ten === 'Người Mẫu A'));
});

// ---------- draft Diagram ----------

test('diagram draft: addSlot/setFlag/removeNode → diagramDirty; save reset', async () => {
  const { model, client } = makeModel(seedCases('empty'));
  await model.openCase(43);
  assert.equal(model.state.diagramDirty, false);

  const node = model.addSlot();
  assert.ok(node.id);
  assert.equal(node.personId, null);
  assert.equal(model.state.diagramDirty, true);

  model.setNodeFlag(node.id, 'isLandOwner', true);
  assert.equal(node.isLandOwner, true);
  model.setNodeFlag(node.id, 'willReceive', false);

  const r = await model.saveDiagram();
  assert.equal(r.ok, true);
  const s = model.state;
  assert.equal(s.diagramDirty, false);
  assert.equal(s.revision, 2);                    // save tang revision
  const sent = client.calls.at(-1).payload;
  assert.equal(sent.base_revision, 1);
  assert.equal(sent.diagram.state.version, 2);

  model.removeNode(node.id);                      // → deleted:true
  const gone = model.state.diagram.nodes
    .find((n) => n.id === node.id);
  assert.equal(gone.deleted, true);
  assert.equal(model.state.diagramDirty, true);
});

test('saveDiagram: workspace_conflict → status conflict', async () => {
  const { model, client } = makeModel(seedCases('ready'));
  await model.openCase(42);
  model.setNodeFlag('owner', 'willReceive', true);
  client.cases[42].revision = 12;
  const r = await model.saveDiagram();
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'workspace_conflict');
  assert.equal(model.state.status, 'conflict');
  assert.equal(model.state.conflict.server_revision, 12);
});

test('evaluateDiagram: cap nhat renderModel, KHONG doi revision/persist', async () => {
  const { model } = makeModel(seedCases('empty'));
  await model.openCase(43);
  const node = model.addSlot();
  model.setNodeFlag(node.id, 'isLandOwner', true);
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
