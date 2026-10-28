import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const script = `import json, sys
sys.path.insert(0, 'sidecar')
from notary_mock_adapter import _render
state = {"nodes": [{"id": "owner", "personId": "p1", "ownPositions": [1], "receivePositions": [], "deleted": False}]}
stage = {"people": [{"row_id": "p1", "ho_ten": "A", "ngay_chet": "2020-01-01"}], "assets": [{"row_id": "a1"}]}
print(json.dumps(_render(state, stage)["requiredSlots"]))`;

test('mock adapter requests slots for an assigned deceased owner', () => {
  const result = spawnSync('python3', ['-c', script], {
    cwd: new URL('..', import.meta.url),
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr);
  const [requirement] = JSON.parse(result.stdout);
  assert.equal(requirement.anchorSlotId, 'owner');
  assert.equal(requirement.reason, 'active_estate');
  assert.deepEqual(requirement.slotTypes, ['father', 'mother', 'spouse', 'child']);
  assert.equal(requirement.minimumEmptyChildSlots, 1);
  assert.equal(requirement.minimumEmptySpouseSlots, 1);
  assert.deepEqual(requirement.slots.map(({ role }) => role),
    ['father', 'mother', 'spouse', 'spouse', 'child', 'child']);
});
