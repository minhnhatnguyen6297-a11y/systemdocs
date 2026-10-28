import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const { makeRotatingStream } = createRequire(import.meta.url)('../src/main/rotating-log.js');

test('xoay vong khi vuot maxBytes, giu toi da keep ban', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rlog-'));
  const f = path.join(dir, 'main.log');
  const s = makeRotatingStream(f, { maxBytes: 100, keep: 2 });
  for (let i = 0; i < 20; i++) s.write(`dong ${i} ${'x'.repeat(30)}\n`);
  assert.ok(fs.statSync(f).size <= 100);
  assert.ok(fs.existsSync(f + '.1') && fs.existsSync(f + '.2'));
  assert.ok(!fs.existsSync(f + '.3'));
  assert.match(fs.readFileSync(f, 'utf8'), /dong 19/);
});

test('tiep tuc kich thuoc file co san', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rlog-'));
  const f = path.join(dir, 'a.log');
  fs.writeFileSync(f, 'y'.repeat(90));
  makeRotatingStream(f, { maxBytes: 100, keep: 1 }).write('z'.repeat(20));
  assert.equal(fs.readFileSync(f + '.1', 'utf8').length, 90);
});
