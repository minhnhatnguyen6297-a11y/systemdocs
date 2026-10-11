'use strict';
// Reuse installed dependencies read-only, without modifying global PATH/config.
const { spawnSync } = require('child_process');
const fs = require('fs'), path = require('path');
const { repo, shared, python, testRoot } = require('./test-runtime.cjs');
const shell = path.join(repo, 'shell');
const env = { ...process.env, NODE_PATH: path.join(shared, 'shell/node_modules'),
  PATH: path.dirname(python) + path.delimiter + process.env.PATH };
const tests = fs.readdirSync(path.join(shell, 'test')).filter(n => n.endsWith('.test.mjs')).map(n => 'test/' + n);
const result = spawnSync(process.execPath, ['--test', ...tests], { cwd: shell, env, encoding: 'utf8' });
const out = result.stdout + result.stderr;
fs.mkdirSync(path.join(testRoot, 'evidence'), { recursive: true });
fs.writeFileSync(path.join(testRoot, 'evidence/regression.txt'), out);
console.log(out.slice(-5500)); process.exitCode = result.status;
