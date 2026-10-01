// MIN-141 — payload THẬT do renderer phát ra phải khớp contract schema.
//
// Driver: case-drafting-model.js chạy thật (newDraft/openCase/addPerson/
// addAsset/setOwnerRow/saveDraft/commitStage/evaluateDiagram) với client
// inject chỉ để GHI payload trên wire — không mock hành vi model.
//
// Điểm kiểm tra chính: `thoi_han` lẻ cấp tài sản đã rút khỏi input
// (asset_row_input / asset_row_v2 không còn bắt buộc, stageForWire strip
// trước khi gửi) nhưng vẫn bắt buộc phía emit (asset_row) cho đối chiếu
// lịch sử / warning stage.orphan_thoi_han.
//
// Validator: JSON Schema draft-07 subset (stdlib-free) đủ cho các def của
// contracts/notary-case-drafting — resolve $ref cùng file lẫn
// "ten-file#/definitions/x".
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const CONTRACT_DIR = path.join(HERE, '..', '..', 'contracts',
                               'notary-case-drafting');
const M = require('../src/renderer/notary/case-drafting-model.js');

const uuid = () => crypto.randomUUID();

// ---------- JSON Schema draft-07 subset ----------

const schemaCache = {};
function loadSchema(file) {
  if (!schemaCache[file]) {
    schemaCache[file] = JSON.parse(
      fs.readFileSync(path.join(CONTRACT_DIR, file), 'utf8'));
  }
  return schemaCache[file];
}

function deref(ref, fromFile) {
  const i = ref.indexOf('#');
  const file = i === 0 ? fromFile : ref.slice(0, i);
  const frag = ref.slice(i + 1);
  if (!frag.startsWith('/')) throw new Error(`unsupported ref ${ref}`);
  let node = loadSchema(file);
  for (const key of frag.slice(1).split('/')) {
    node = node && node[key];
    if (node === undefined) throw new Error(`unresolved ref ${ref}`);
  }
  return { schema: node, file };
}

function typeOk(v, t) {
  switch (t) {
    case 'string': return typeof v === 'string';
    case 'integer': return Number.isInteger(v);
    case 'number': return typeof v === 'number';
    case 'boolean': return typeof v === 'boolean';
    case 'null': return v === null;
    case 'array': return Array.isArray(v);
    case 'object': {
      return v !== null && typeof v === 'object' && !Array.isArray(v);
    }
    default: throw new Error(`unknown type ${t}`);
  }
}

function violations(v, s, file, where, errs) {
  if (s == null || s === true) return errs;
  if (s === false) { errs.push(`${where}: schema false`); return errs; }
  if (s.$ref) {
    const r = deref(s.$ref, file);
    return violations(v, r.schema, r.file, where, errs);
  }
  for (const sub of s.allOf || []) violations(v, sub, file, where, errs);
  if (s.anyOf && !s.anyOf.some((x) => ok(v, x, file))) {
    errs.push(`${where}: anyOf fail`);
  }
  if (s.oneOf && s.oneOf.filter((x) => ok(v, x, file)).length !== 1) {
    errs.push(`${where}: oneOf fail`);
  }
  if (s.not && ok(v, s.not, file)) errs.push(`${where}: not violated`);
  if (s.if) {
    const branch = ok(v, s.if, file) ? s.then : s.else;
    if (branch) violations(v, branch, file, where, errs);
  }
  if (s.const !== undefined && v !== s.const) {
    errs.push(`${where}: const ${s.const} != ${JSON.stringify(v)}`);
  }
  if (s.enum && !s.enum.some((x) => x === v)) {
    errs.push(`${where}: enum fail ${JSON.stringify(v)}`);
  }
  if (s.type) {
    const ts = Array.isArray(s.type) ? s.type : [s.type];
    if (!ts.some((t) => typeOk(v, t))) {
      errs.push(`${where}: type ${ts} != ${JSON.stringify(v)}`);
      return errs;                       // sai kiểu → khỏi check sâu
    }
  }
  if (typeof v === 'string') {
    if (s.pattern && !(new RegExp(s.pattern).test(v))) {
      errs.push(`${where}: pattern fail ${JSON.stringify(v)}`);
    }
    if (s.minLength !== undefined && v.length < s.minLength) {
      errs.push(`${where}: minLength ${s.minLength}`);
    }
    if (s.maxLength !== undefined && v.length > s.maxLength) {
      errs.push(`${where}: maxLength ${s.maxLength}`);
    }
  }
  if (typeof v === 'number') {
    if (s.minimum !== undefined && v < s.minimum) {
      errs.push(`${where}: minimum ${s.minimum}`);
    }
    if (s.maximum !== undefined && v > s.maximum) {
      errs.push(`${where}: maximum ${s.maximum}`);
    }
  }
  if (Array.isArray(v)) {
    if (s.minItems !== undefined && v.length < s.minItems) {
      errs.push(`${where}: minItems ${s.minItems}`);
    }
    if (s.maxItems !== undefined && v.length > s.maxItems) {
      errs.push(`${where}: maxItems ${s.maxItems}`);
    }
    if (s.uniqueItems) {
      if (new Set(v.map((x) => JSON.stringify(x))).size !== v.length) {
        errs.push(`${where}: uniqueItems fail`);
      }
    }
    if (s.items) {
      v.forEach((x, i) => violations(x, s.items, file, `${where}[${i}]`,
                                     errs));
    }
  }
  if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
    for (const k of s.required || []) {
      if (!(k in v)) errs.push(`${where}: missing required '${k}'`);
    }
    const props = s.properties || {};
    if (s.additionalProperties === false) {
      for (const k of Object.keys(v)) {
        if (!(k in props)) errs.push(`${where}: extra key '${k}'`);
      }
    }
    for (const [k, sub] of Object.entries(props)) {
      if (k in v) violations(v[k], sub, file, `${where}.${k}`, errs);
    }
  }
  return errs;
}

function collect(v, ref, file) {
  return violations(v, { $ref: ref }, file, '', []);
}
function ok(v, s, file) {
  return violations(v, s, file, '', []).length === 0;
}

function assertValid(v, ref, file, label) {
  const errs = collect(v, ref, file);
  assert.deepEqual(errs, [],
    `${label} — vi phạm schema ${ref}:\n  ${errs.join('\n  ')}`);
}

// ---------- capture client (ghi payload, trả canned ok) ----------

function captureClient(getResponse) {
  const calls = [];
  return {
    calls,
    async run(command, payload) {
      calls.push({ command, payload: JSON.parse(JSON.stringify(payload)) });
      if (command === 'notary.workspace_get') return getResponse(payload);
      const okData = {
        schema_version: 'notary.case-drafting.v2',
        backend_mode: 'mock',
      };
      if (command === 'notary.workspace_commit_stage') {
        return { ok: true, data: { ...okData, revision: payload.base_revision + 1,
                                   stage: payload.stage,
                                   diagram: { state: { version: 3, nodes: [] },
                                              render_model: null } } };
      }
      if (command === 'notary.workspace_create') {
        const c = payload.case || {};
        return { ok: true, data: {
          ...okData, created: true,
          case: { id: 42, case_type: c.case_type || 'inheritance',
                  document_type: c.document_type, status: 'draft',
                  locked: false, revision: 1,
                  ngay_lap_ho_so: null, noi_niem_yet: null,
                  nguoi_nhan_uy_quyen: null, nguoi_nhan_uy_quyen_id: null,
                  noi_dung_viec: null, ghi_chu: null },
          stage: payload.stage,
          diagram: { domain: 'inheritance',
                     state: (payload.diagram || {}).state,
                     render_model: null },
          capabilities: { intake: [], diagram: true, word_export: true },
        } };
      }
      if (command === 'notary.diagram_evaluate') {
        return { ok: true, data: { ...okData, evaluated_revision: null,
                                   render_model: null } };
      }
      return { ok: false, error: { code: 'command_unknown',
                                   message: command, retryable: false,
                                   next_action: null, details: null } };
    },
  };
}

// Workspace mở lại từ server — asset đã commit CÒN key `thoi_han` lẻ
// (master giữ lịch sử — payload emit), để chứng minh renderer strip nó
// trước khi gửi ngược lên.
function legacyGetResponse() {
  const ownerId = '11111111-1111-4111-8111-111111111111';
  return { ok: true, data: {
    schema_version: 'notary.case-drafting.v2',
    backend_mode: 'real',
    case: { id: 42, case_type: 'inheritance', document_type: 'khai_nhan',
            status: 'draft', locked: false, revision: 7,
            ngay_lap_ho_so: null, noi_niem_yet: null,
            nguoi_nhan_uy_quyen: null, nguoi_nhan_uy_quyen_id: null,
            noi_dung_viec: null, ghi_chu: null },
    stage: {
      owner_row_id: ownerId,
      people: [{
        row_id: ownerId, entity_id: 11,
        ho_ten: 'Nguyễn Văn Chết', gioi_tinh: 'Nam',
        ngay_sinh: '1950-01-01', ngay_chet: '2011-05-15',
        so_giay_to: 'TLK 12/2011', ngay_cap: '2011-05-16',
        noi_cap: null, dia_chi: 'xã X', place_of_origin: null,
        loai_giay_to: 'Giấy chứng tử', loai_dia_chi: 'Nơi chết',
      }],
      assets: [{
        row_id: '55555555-5555-4555-8555-555555555555', entity_id: 201,
        so_serial: 'MM000001', so_vao_so: null, so_thua_dat: '123',
        so_to_ban_do: '45', dia_chi: 'Địa chỉ tài sản 1',
        loai_so: 'GCN QSDĐ', hinh_thuc_su_dung: null,
        thoi_han: 'Lâu dài',                    // lịch sử trên emit
        nguon_goc: null, ngay_cap: '2005-09-30', co_quan_cap: null,
        land_rows: [{ loai_dat: 'ODT', dien_tich: 85.5,
                      thoi_han: 'Lâu dài' }],
      }],
    },
    diagram: { domain: 'inheritance',
               state: { version: 3, domain: 'inheritance', nodes: [
                 { id: 'owner', personId: ownerId, parentSlotIds: [],
                   spouseSlotId: null, ownPositions: [1],
                   receivePositions: [], hidden: false, deleted: false },
               ] },
               render_model: null, warnings: [] },
    capabilities: { intake: ['image'], diagram: true, word_export: true },
  } };
}

// ---------- tests ----------

test('wire: saveDraft (workspace_create) — payload thật khớp '
     + 'payload_workspace_create_v2, không gửi thoi_han lẻ', async () => {
  const client = captureClient();
  const model = M.createModel({ client, uuid });
  model.newDraft();
  const p = model.addPerson({ ho_ten: 'Nguyễn Văn Chết',
                              ngay_chet: '2011-05-15' });
  const a = model.addAsset({ so_serial: 'MM000001',
                             dia_chi: 'Thửa 99, xã Y' });
  model.updateAssetField(a.row_id, 'land_rows',
                         [{ loai_dat: 'ODT', dien_tich: 85.5,
                            thoi_han: 'Lâu dài' }]);
  model.setOwnerRow(p.row_id);
  const r = await model.saveDraft();
  assert.equal(r.ok, true);

  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_create');
  assert.ok(call);
  // Validate FULL payload thật vs contract v2 — kể cả block case meta đợt 3.
  assertValid(call.payload, '#/definitions/payload_workspace_create_v2',
              'draft-v2.schema.json', 'workspace_create payload');
  for (const asset of call.payload.stage.assets) {
    assert.equal('thoi_han' in asset, false,
      'asset không được mang key thoi_han lẻ trên wire');
  }
  assert.equal(call.payload.stage.assets[0].land_rows[0].thoi_han,
               'Lâu dài', 'thời hạn mới chỉ thuộc cụm đất');
});

test('wire: commitStage trên case mở lại — asset mang thoi_han lịch sử '
     + 'bị strip, payload khớp payload_commit_stage_v2', async () => {
  const client = captureClient(() => legacyGetResponse());
  const model = M.createModel({ client, uuid });
  await model.openCase(42);
  // Row load từ server VẪN mang thoi_han (emit giữ lịch sử).
  assert.equal(model.state.stage.assets[0].thoi_han, 'Lâu dài');
  // Sửa một field để stage dirty → commit gửi stage; sửa meta để
  // payload.case (đợt 3) cũng xuất hiện và được validate.
  model.updateAssetField(
    model.state.stage.assets[0].row_id, 'dia_chi', 'Địa chỉ mới');
  model.updateCaseMeta('ghi_chu', 'Ghi chú thử');
  const r = await model.commitStage();
  assert.equal(r.ok, true);

  const call = client.calls.find(
    (c) => c.command === 'notary.workspace_commit_stage');
  assert.ok(call);
  assertValid(call.payload, '#/definitions/payload_commit_stage_v2',
              'draft-v2.schema.json', 'commit_stage payload');
  assert.equal(call.payload.case.ghi_chu, 'Ghi chú thử');
  for (const asset of call.payload.stage.assets) {
    assert.equal('thoi_han' in asset, false);
    // land_rows cụm đất giữ nguyên thoi_han
    assert.ok(Array.isArray(asset.land_rows));
    assert.equal(asset.land_rows[0].thoi_han, 'Lâu dài');
  }
});

test('wire: evaluateDiagram nháp — stage kèm theo không có thoi_han lẻ, '
     + 'khớp stage_v2', async () => {
  const client = captureClient();
  const model = M.createModel({ client, uuid });
  model.newDraft();
  const p = model.addPerson({ ho_ten: 'Người Chết' });
  const a = model.addAsset({ so_serial: 'MM000001', dia_chi: 'Xã Y' });
  model.updateAssetField(a.row_id, 'land_rows',
                         [{ loai_dat: 'CLN', dien_tich: 50,
                            thoi_han: '50 năm' }]);
  model.setOwnerRow(p.row_id);
  await model.evaluateDiagram();

  const call = client.calls.find(
    (c) => c.command === 'notary.diagram_evaluate');
  assert.ok(call);
  // evaluate nháp (case_id absent) mang stage — validate subtree stage
  // vs stage_v2 (draft-v2 không có def payload evaluate riêng).
  assertValid(call.payload.stage, '#/definitions/stage_v2',
              'draft-v2.schema.json', 'diagram_evaluate draft stage');
  for (const asset of call.payload.stage.assets) {
    assert.equal('thoi_han' in asset, false);
  }
});

test('schema: tách input/emit — asset_row_input không bắt buộc thoi_han '
     + 'lẻ, asset_row (emit) vẫn bắt buộc', () => {
  // Row shape v1 (có is_primary) — cùng bộ field, KHÔNG thoi_han lẻ.
  const rowNoTerm = {
    row_id: uuid(), entity_id: null, is_primary: true,
    so_serial: 'MM000001', so_vao_so: null, so_thua_dat: '123',
    so_to_ban_do: '45', dia_chi: 'Địa chỉ tài sản',
    loai_so: 'GCN QSDĐ', hinh_thuc_su_dung: null,
    nguon_goc: null, ngay_cap: '2005-09-30', co_quan_cap: null,
    land_rows: [{ loai_dat: 'ODT', dien_tich: 85.5,
                  thoi_han: 'Lâu dài' }],
  };
  const file = 'common.schema.json';
  // INPUT: hợp lệ khi vắng thoi_han lẻ.
  assertValid(rowNoTerm, '#/definitions/asset_row_input', file,
              'asset_row_input không thoi_han');
  // INPUT: vẫn chấp nhận client legacy gửi key (ghi như cũ).
  assertValid({ ...rowNoTerm, thoi_han: 'Lâu dài' },
              '#/definitions/asset_row_input', file,
              'asset_row_input có thoi_han (legacy)');
  // EMIT: vắng thoi_han → invalid (server phải luôn emit key, kể cả null).
  const errs = collect(rowNoTerm, '#/definitions/asset_row', file);
  assert.ok(errs.some((e) => e.includes('thoi_han')),
    `asset_row emit phải bắt buộc thoi_han — got: ${errs}`);
  // EMIT: có key (kể cả null) → hợp lệ.
  assertValid({ ...rowNoTerm, thoi_han: 'Lâu dài' },
              '#/definitions/asset_row', file, 'asset_row emit đủ key');
  assertValid({ ...rowNoTerm, thoi_han: null },
              '#/definitions/asset_row', file, 'asset_row emit null');
});
