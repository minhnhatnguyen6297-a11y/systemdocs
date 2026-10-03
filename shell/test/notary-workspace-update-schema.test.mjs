// Kiểm JSON Schema draft-07 THẬT (ajv) cho
// contracts/notary-case-drafting/workspace-update.schema.json — §6.2 (+ §13
// v2/two_party). Đây là kiểm chứng machine-readable của schema chuẩn mà
// contract §0 chỉ định; rule ngữ cảnh base_revision vs server_revision
// (workspace_conflict) KHÔNG nằm trong schema — giữ ở validate_examples.py.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const Ajv = require('ajv'); // draft-07 engine — đã có trong node_modules (lock)

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CONTRACT_DIR = path.resolve(HERE, '..', '..', 'contracts',
  'notary-case-drafting');
const SCHEMA_ID = 'https://systemdocs/contracts/notary-case-drafting/' +
  'workspace-update.schema.json';

const readJson = (rel) =>
  JSON.parse(fs.readFileSync(path.join(CONTRACT_DIR, rel), 'utf8'));

const ajv = new Ajv({ allErrors: true });
for (const f of ['common.schema.json', 'workspace.schema.json',
                 'draft-v2.schema.json', 'workspace-update.schema.json']) {
  ajv.addSchema(readJson(f));
}
const check = (frag) => ajv.compile({ $ref: `${SCHEMA_ID}#/definitions/${frag}` });
const validatePayload = check('payload');
const validateResultV1 = check('result_data_v1');
const validateResultV2 = check('result_data_v2');
const validateResult = check('result_data');

const CMD_V1 = 'examples/valid/command.workspace-update.valid.json';
const CMD_V2 = 'examples/draft-v2/command.workspace-update.valid.json';
const JOB_V1 = 'examples/valid/job.workspace-update.valid.json';
const JOB_V2_2P = 'examples/draft-v2/job.workspace-update-two-party.valid.json';

const del = (obj, key) => {
  const copy = { ...obj };
  delete copy[key];
  return copy;
};

test('schema: payload examples hợp lệ qua draft-07 (v1 + v2)', () => {
  for (const rel of [CMD_V1, CMD_V2]) {
    const doc = readJson(rel);
    assert.equal(validatePayload(doc.payload), true,
      `${rel}: ${JSON.stringify(validatePayload.errors)}`);
  }
});

test('schema: invalid payload examples bị reject (key/value sai, patch rỗng, thiếu case_id)', () => {
  for (const rel of [
    'examples/invalid/command.workspace-update-bad-key.invalid.json',
    'examples/invalid/command.workspace-update-bad-value.invalid.json',
    'examples/invalid/command.workspace-update-empty-case.invalid.json',
    'examples/invalid/command.workspace-update-missing-case-id.invalid.json',
  ]) {
    const doc = readJson(rel);
    assert.equal(validatePayload(doc.payload), false,
      `${rel} phải bị schema reject`);
  }
});

test('schema: stale-revision vẫn SCHEMA-VALID — conflict theo server_revision giữ ở validator', () => {
  const doc = readJson(
    'examples/invalid/command.workspace-update-stale-revision.invalid.json');
  assert.equal(validatePayload(doc.payload), true,
    'base_revision int hợp lệ về mặt schema; conflict là rule ngữ cảnh');
});

test('schema: result v1 example khớp result_data_v1 + entry anyOf', () => {
  const data = readJson(JOB_V1).result.data;
  assert.equal(validateResultV1(data), true,
    JSON.stringify(validateResultV1.errors));
  assert.equal(validateResultV2(data), false,
    'v1 result không được khớp nhánh v2 (phân biệt schema_version)');
  assert.equal(validateResult(data), true);
});

test('schema: result v2 two_party example khớp result_data_v2 + entry anyOf', () => {
  const data = readJson(JOB_V2_2P).result.data;
  assert.equal(validateResultV2(data), true,
    JSON.stringify(validateResultV2.errors));
  assert.equal(validateResultV1(data), false,
    'v2 two_party result không được khớp nhánh v1');
  assert.equal(validateResult(data), true);
});

test('schema: result v2 inheritance cũng khớp nhánh v2 (else của document_type)', () => {
  const data = readJson(JOB_V2_2P).result.data;
  const inh = {
    ...data,
    case: {
      ...data.case,
      case_type: 'inheritance',
      document_type: 'khai_nhan',
    },
  };
  assert.equal(validateResultV2(inh), true,
    JSON.stringify(validateResultV2.errors));
});

test('schema: payload mutation — thiếu trường / bool thay integer / key-value sai đều reject', () => {
  const base = readJson(CMD_V1).payload;
  const cases = {
    'missing case_id': del(base, 'case_id'),
    'missing base_revision': del(base, 'base_revision'),
    'missing case': del(base, 'case'),
    'case_id bool thay integer': { ...base, case_id: true },
    'case_id string': { ...base, case_id: '42' },
    'case_id zero': { ...base, case_id: 0 },
    'base_revision bool thay integer': { ...base, base_revision: true },
    'base_revision float': { ...base, base_revision: 7.5 },
    'base_revision zero': { ...base, base_revision: 0 },
    'case không phải object': { ...base, case: 'x' },
    'case patch rỗng': { ...base, case: {} },
    'payload key lạ (stage)': { ...base, stage: {} },
    'patch key lạ (document_type)':
      { ...base, case: { document_type: 'thoa_thuan' } },
    'patch key lạ (case_type)':
      { ...base, case: { case_type: 'two_party' } },
    'ghi_chu number thay string/null': { ...base, case: { ghi_chu: 123 } },
    'noi_niem_yet empty-string thay null':
      { ...base, case: { noi_niem_yet: '' } },
    'ngay_lap_ho_so sai format': { ...base, case: { ngay_lap_ho_so: '03-10-2026' } },
    'ngay_lap_ho_so number thay date/null':
      { ...base, case: { ngay_lap_ho_so: 20261003 } },
  };
  for (const [name, inst] of Object.entries(cases)) {
    assert.equal(validatePayload(inst), false, `${name} phải bị reject`);
  }
});

test('schema: result.data mutation — thiếu trường / sai type / case xấu đều reject', () => {
  const data = readJson(JOB_V1).result.data;
  const cases = {
    'missing schema_version': del(data, 'schema_version'),
    'missing revision': del(data, 'revision'),
    'missing case': del(data, 'case'),
    'schema_version const sai': { ...data, schema_version: 'notary.case-drafting.v3' },
    'revision bool thay integer': { ...data, revision: true },
    'revision string': { ...data, revision: '8' },
    'revision zero': { ...data, revision: 0 },
    'result.data key lạ': { ...data, backend_mode: 'real' },
    'case thiếu revision': { ...data, case: del(data.case, 'revision') },
    'case thiếu case_type': { ...data, case: del(data.case, 'case_type') },
    'case key lạ (people)': { ...data, case: { ...data.case, people: [] } },
    'case revision bool thay integer':
      { ...data, case: { ...data.case, revision: true } },
    'case status sai enum': { ...data, case: { ...data.case, status: 'archived' } },
    'case document_type hai bên trên v1':
      { ...data, case: { ...data.case, document_type: 'chuyen_nhuong' } },
    'case ngay_lap_ho_so sai format':
      { ...data, case: { ...data.case, ngay_lap_ho_so: '28/09/2026' } },
  };
  for (const [name, inst] of Object.entries(cases)) {
    assert.equal(validateResult(inst), false, `${name} phải bị reject`);
  }
});

test('schema: result v2 mutation — case_type/document_type lệch nhánh đều reject', () => {
  const data = readJson(JOB_V2_2P).result.data;
  const cases = {
    'two_party với document_type thừa kế':
      { ...data, case: { ...data.case, document_type: 'khai_nhan' } },
    'inheritance với document_type hai bên': {
      ...data,
      case: {
        ...data.case,
        case_type: 'inheritance',
        document_type: 'chuyen_nhuong',
      },
    },
    'case_type ngoài enum': { ...data, case: { ...data.case, case_type: 'legacy' } },
    'schema_version v1 trên case v2 (anyOf không nhánh nào khớp)':
      { ...data, schema_version: 'notary.case-drafting.v1' },
    'v2 result thiếu document_type': { ...data, case: del(data.case, 'document_type') },
  };
  for (const [name, inst] of Object.entries(cases)) {
    assert.equal(validateResult(inst), false, `${name} phải bị reject`);
  }
});
