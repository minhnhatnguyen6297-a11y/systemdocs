'use strict';
// Test dependencies follow run.bat: current worktree first, shared Git root second.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const repo = path.resolve(__dirname, '../..');
let shared = repo;
try {
  const common = execFileSync('git', ['-C', repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'], { encoding: 'utf8' }).trim();
  shared = path.dirname(common);
} catch { /* A standalone checkout may supply its own installed dependencies. */ }
function installed(relative) {
  const local = path.join(repo, relative);
  return fs.existsSync(local) ? local : path.join(shared, relative);
}
const python = process.env.G1_PYTHON || installed('notary_v2/venv/Scripts/python.exe');
const playwright = path.resolve(path.dirname(python), '../Lib/site-packages/playwright/driver/package');
const electron = installed('shell/node_modules/electron/dist/electron.exe');
const testRoot = path.resolve(process.env.G1_VISUAL_SPIKE_TEST_DIR || path.join(repo, 'docs/tmp/visual-bug-reporting/checks'));
module.exports = { repo, shared, python, playwright, electron, testRoot };
