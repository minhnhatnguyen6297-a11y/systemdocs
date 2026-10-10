import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';

const packer = fileURLToPath(new URL('../runtime/pack.mjs', import.meta.url));
const unchanged = ['#section', 'https://example.org/proof?q=1#section', '//example.org/proof', 'data:text/plain,evidence', 'mailto:owner@example.org', 'tel:+123456', '/root/proof.html', '?view=raw#section'];

for (const relocated of [true, false]) {
  test(`evidence hrefs retain their targets with ${relocated ? 'relocated' : 'same-directory'} output`, () => {
    const root = mkdtempSync(join(tmpdir(), 'html-plan-links-'));
    try {
      const input = join(root, 'source', 'examples', 'plan.html');
      const output = relocated ? join(root, 'artifacts', 'render', 'plan.html') : join(dirname(input), 'plan.packed.html');
      const evidence = join(root, 'evidence', 'report & notes.html');
      for (const path of [input, output, evidence]) mkdirSync(dirname(path), { recursive: true });
      writeFileSync(evidence, '<h1 id="section">Local evidence</h1>');
      const local = '../../evidence/report%20%26%20notes.html?view=raw&amp;mode=full#section';
      writeFileSync(join(dirname(input), 'extra.css'), '.evidence { color: green; }');
      writeFileSync(input, `<!doctype html><html><head><meta charset="utf-8"><title>Evidence links</title>
<link rel="stylesheet" href="htmlplan.css"><link rel="stylesheet" href="extra.css">
<script src="htmlplan.js" defer></script></head><body><h1 id="section">Evidence links</h1>
<a id="local" href="${local}">Evidence</a>
<doc-quote via="prompt" from="Owner" href='${local}'>Inspect evidence</doc-quote>
${unchanged.map((href, i) => `<a id="keep-${i}" href="${href}">Reference</a>`).join('\n')}
<script type="text/plain">Example: <a href="../../evidence/example.html">code</a></script>
</body></html>`);
      execFileSync(process.execPath, [packer, input, '--root', root, '-o', output, '--quiet'], { encoding: 'utf8' });
      const packed = readFileSync(output, 'utf8');
      const href = packed.match(/<a id="local" href="([^"]+)"/)[1];
      const resolved = new URL(href.replace(/&amp;/g, '&'), pathToFileURL(output));
      assert.equal(resolved.href, new URL(local.replace(/&amp;/g, '&'), pathToFileURL(input)).href);
      assert.equal(readFileSync(fileURLToPath(resolved), 'utf8'), '<h1 id="section">Local evidence</h1>');
      assert.equal(packed.match(/<doc-quote[^>]*href='([^']+)'/)[1], href);
      assert.equal(resolved.search, '?view=raw&mode=full');
      assert.equal(resolved.hash, '#section');
      if (!relocated) assert.equal(href, local);
      for (const [i, expected] of unchanged.entries()) {
        assert.equal(packed.match(new RegExp(`<a id="keep-${i}" href="([^"]+)"`))[1], expected);
      }
      assert.ok(packed.includes('.evidence { color: green; }'), 'local stylesheets are read relative to input before href rebasing');
      assert.ok(packed.includes('Example: <a href="../../evidence/example.html">code</a>'), 'source examples are not navigation');
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
}

test('reviewed packer boundaries: entities, base, secrets, css deps, source fidelity, oversized assets', () => {
  const root = mkdtempSync(join(tmpdir(), 'html-plan-boundaries-'));
  const run = (name, head, body) => {
    const input = join(root, 'source', `${name}.html`), output = join(root, 'out', `${name}.html`);
    mkdirSync(dirname(input), { recursive: true }); mkdirSync(dirname(output), { recursive: true });
    writeFileSync(input, `<!doctype html><html><head><meta charset="utf-8"><title>${name}</title><link rel="stylesheet" href="htmlplan.css"><script src="htmlplan.js" defer></script>${head}</head><body><h1>${name}</h1>${body}</body></html>`);
    const stdout = execFileSync(process.execPath, [packer, input, '--root', root, '-o', output, '--quiet'], { encoding: 'utf8' });
    return { output, packed: readFileSync(output, 'utf8'), stdout };
  };
  const runFails = (name, head, body) => {
    const input = join(root, 'source', `${name}.html`), output = join(root, 'out', `${name}.html`);
    mkdirSync(dirname(input), { recursive: true }); mkdirSync(dirname(output), { recursive: true });
    writeFileSync(input, `<!doctype html><html><head><meta charset="utf-8"><title>${name}</title>${head}</head><body>${body}</body></html>`);
    try { execFileSync(process.execPath, [packer, input, '--root', root, '-o', output], { encoding: 'utf8', stdio: 'pipe' }); return null; } catch (e) { return `${e.stdout || ''}${e.stderr || ''}`; }
  };
  try {
    mkdirSync(join(root, 'evidence'), { recursive: true });
    writeFileSync(join(root, 'evidence', "owner's.html"), '<p>Owner evidence</p>');
    writeFileSync(join(root, 'evidence', 'report notes.html'), '<p>Spaced evidence</p>');
    writeFileSync(join(root, 'evidence', 'current.js'), 'const current = 1;\n');
    writeFileSync(join(root, 'evidence', 'escaped.js'), "const tag = '</script>';\n");
    // Apostrophe and numeric-entity hrefs decode before path resolution.
    const links = run('links', '', `<a id="apostrophe" href='../evidence/owner%27s.html'>Owner</a><a id="entity" href="../evidence/report&#32;notes.html">Notes</a>`);
    assert.equal(decodeURIComponent(new URL(links.packed.match(/<a id="apostrophe" href='([^']*)'/)[1], pathToFileURL(links.output)).pathname), pathToFileURL(join(root, 'evidence', "owner's.html")).pathname);
    // <base> is rejected: pack resolves paths against the input file.
    assert.match(runFails('base', '<base href="../evidence/">', '<a href="proof.html">Proof</a>'), /<base>/);
    // Secret-shaped text in any embedded file is refused.
    writeFileSync(join(root, 'secret.css'), `/* ghp_${'A'.repeat(36)} */ .x{color:red}`);
    assert.match(runFails('secret', '<link rel="stylesheet" href="../secret.css">', '<p>No actual secret</p>'), /looks like a secrets file/);
    // Local stylesheet url()/@import dependencies are rebased before inlining.
    mkdirSync(join(root, 'source', 'css'), { recursive: true });
    writeFileSync(join(root, 'source', 'css', 'dot.png'), Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aip8AAAAASUVORK5CYII=', 'base64'));
    writeFileSync(join(root, 'source', 'css', 'dependent.css'), '.demo{background:url(dot.png)}');
    const css = run('css', '<link rel="stylesheet" href="css/dependent.css">', '<p class="demo">CSS dependency</p>');
    assert.match(css.packed, /url\(file:\/\/\/[^"')]*dot\.png\)/);
    // Embedded source keeps a literal </script and the fence survives packing.
    const escaped = run('escaped', '', '<doc-code src="../evidence/escaped.js" caption="Literal source"></doc-code>');
    assert.ok(escaped.packed.includes("const tag = '<\\/script>';"), 'fenced script content is escaped in the host page');
    // Oversized assets are not inlined but are copied beside relocated output.
    const big = Buffer.alloc(6_000_001); big.fill(0x42); writeFileSync(join(root, 'source', 'big.png'), big);
    const large = run('large', '', '<img src="big.png" alt="Large image">');
    assert.equal(large.packed.match(/<img src="([^"]+)"/)[1], 'big.png');
    assert.ok(existsSync(join(root, 'out', 'big.png')), 'oversized asset is copied beside relocated output');
    // Apache-2.0 attribution is embedded in the packed head.
    assert.ok(links.packed.includes('Thariq'), 'license attribution comment present');
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
