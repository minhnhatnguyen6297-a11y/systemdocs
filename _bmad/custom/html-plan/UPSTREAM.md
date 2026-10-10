# html-plan upstream runtime

Original html-plan runtime by Thariq Shihipar, vendored from
[anthropics/claude-plugins-community](https://github.com/anthropics/claude-plugins-community)
at commit [`88003be1129c09381d27100b37a8fdc21b3214bf`](https://github.com/anthropics/claude-plugins-community/commit/88003be1129c09381d27100b37a8fdc21b3214bf)
(2026-10-05). This is the latest runtime-changing commit returned by the upstream
commit API when retrieved on 2026-10-10; the pin, not `main`, defines this copy.

Canonical source directory:
[`html-plan/skills/html-plan/runtime/`](https://github.com/anthropics/claude-plugins-community/tree/88003be1129c09381d27100b37a8fdc21b3214bf/html-plan/skills/html-plan/runtime).
`runtime/htmlplan.css` and LICENSE remain byte-for-byte upstream UTF-8; the CSS also
matches the downloaded research copy in `_bmad-output/tmp/thariq-html-plan-source/runtime/`.
`runtime/htmlplan.js` and `runtime/pack.mjs` start from the same pin but carry the
reviewed local patches described below.
The scoped `.gitattributes` keeps these four files LF on checkout, including
Windows clones with `core.autocrlf=true`; it does not reformat upstream content.

## Files and SHA-256

| Local file | Pinned raw source | Local SHA-256 |
|---|---|---|
| `runtime/htmlplan.css` | [htmlplan.css](https://raw.githubusercontent.com/anthropics/claude-plugins-community/88003be1129c09381d27100b37a8fdc21b3214bf/html-plan/skills/html-plan/runtime/htmlplan.css) | `f16d2c6aa08e5f275bceee96e38ec38f05dd0add91c4bb6636e8a0a8a4836a9e` |
| `runtime/htmlplan.js` (locally patched) | [htmlplan.js](https://raw.githubusercontent.com/anthropics/claude-plugins-community/88003be1129c09381d27100b37a8fdc21b3214bf/html-plan/skills/html-plan/runtime/htmlplan.js) | `228c0482486ad4ff0177217efccd125e9fd5c13fb0d34f58f4990b8b9e1bc8e3` |
| `runtime/pack.mjs` (locally patched) | [pack.mjs](https://raw.githubusercontent.com/anthropics/claude-plugins-community/88003be1129c09381d27100b37a8fdc21b3214bf/html-plan/skills/html-plan/runtime/pack.mjs) | `d2ba3a918e6cdb36f79e3ba75141b7deb515a3489788bb683bc326eca7d8be08` |
| `LICENSE` | [repository LICENSE](https://raw.githubusercontent.com/anthropics/claude-plugins-community/88003be1129c09381d27100b37a8fdc21b3214bf/LICENSE) | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

Downloaded bytes were authenticated against the pinned commit's Git tree blob
identifiers before copying. License: Apache-2.0, copied verbatim from the repository
root; the pinned tree has no html-plan-specific license or NOTICE file. Retain the
license and upstream attribution when distributing the runtime or packed artifacts.

## Local patches (reviewed)

Baseline SHA-256 before modification: `pack.mjs`
`88ca711cfc4a3c37c9155357487763f75aa8a9cf1ebc789dfefe1542a38944df`;
`htmlplan.js`
`4b5bcb3d7160c6170bc82c6f1809089d0faa890d2c7f7e8c9100ff6330478d42`.

1. **Href portability (`pack.mjs`).** After asset inlining, the packer rebases
   relative local `href` attributes from the authored file's directory to the
   output directory, so evidence links retain their target when `-o` relocates
   the HTML. HTML entities in hrefs (numeric and the common named ones, e.g.
   `&#32;`, `&amp;`) are decoded before path resolution, and percent-encoding
   is applied per path segment with apostrophes escaped. Query strings and
   fragments are retained; same-directory output, fragment-only/query-only
   links, root-relative paths and URL schemes (including external, data and
   mailto URLs) are unchanged. Comments and script/style bodies are not
   rewritten. No `<base>` element is inserted; a document that itself contains
   `<base>` is rejected with an error because pack resolves paths against the
   input file. Different-drive output uses a computed file URL when no relative
   filesystem path is possible; no checkout path is hardcoded.
2. **Secret fence everywhere (`pack.mjs`).** Every file the packer reads for
   embedding or inlining — code excerpts, call excerpts, local stylesheets and
   their inlined assets — is checked against the same secret-shaped-text rule
   as fenced blocks and refused (an error for code blocks and stylesheets, a
   skip with warning for call excerpts) if it matches. Evidence links are still not
   read. Local stylesheets have their own relative `url()`/`@import`
   dependencies rebased to absolute file URLs before inlining so relocated
   output keeps its images. Assets larger than 6 MB are not inlined; when the
   output is relocated, a copy is emitted beside the packed page instead of
   stranding the reference. A short Apache-2.0 attribution comment is embedded
   before `</head>` of packed documents.
3. **Fenced source fidelity (`htmlplan.js`).** The packer escapes a literal
   `</script` inside an embedded `<script type="text/plain">` fence as
   `<\/script` so the host page still parses. The runtime `srcOf` decode now
   reverses that exact escape, so displayed code matches the original source
   bytes. No other runtime behavior changed.

Focused regression command (isolated temporary fixtures):

```text
node --test _bmad/custom/html-plan/tests/pack-links.test.mjs
```

## Use

Node.js and its built-ins only; no install, dependencies, server or hooks. From the
project root, pass an authored HTML path to the CLI:

```text
node _bmad/custom/html-plan/runtime/pack.mjs <authored.html> --root . -o <packed.html>
```

The authored file links `htmlplan.css` and loads `htmlplan.js`; use relative paths
to this runtime directory. The packer validates the authored document, fills local
code excerpts, and inlines the runtime and supported local assets. Open the packed
HTML directly in a browser. For a standalone offline document, use local assets
within the allowed roots: remote URLs are not downloaded, missing assets remain
linked, and assets larger than 6 MB are not inlined. Inspect packer warnings rather
than assuming every packed document is self-contained.

## Exact update recipe

Run the following PowerShell from the project root to restore the upstream
baseline, not the locally patched files. It overwrites the local patches in both
`pack.mjs` and `htmlplan.js`: reapply and review the patches above before using
the restored runtime. For an update, first choose and review a full upstream
commit SHA, replace `$revision` with that SHA, and inspect its tree for changed
license/NOTICE obligations. Never fetch runtime files from an unpinned branch.

```powershell
$revision = '88003be1129c09381d27100b37a8fdc21b3214bf'
$base = "https://raw.githubusercontent.com/anthropics/claude-plugins-community/$revision"
$target = '_bmad/custom/html-plan'
New-Item -ItemType Directory -Force "$target/runtime" | Out-Null
foreach ($file in @('htmlplan.css', 'htmlplan.js', 'pack.mjs')) {
    curl.exe --fail --location "$base/html-plan/skills/html-plan/runtime/$file" --output "$target/runtime/$file"
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $file" }
}
curl.exe --fail --location "$base/LICENSE" --output "$target/LICENSE"
if ($LASTEXITCODE -ne 0) { throw 'Download failed: LICENSE' }
Get-FileHash -Algorithm SHA256 "$target/runtime/htmlplan.css", "$target/runtime/htmlplan.js", "$target/runtime/pack.mjs", "$target/LICENSE"
```

For this pin, compare the CSS, JS and LICENSE results with the table above and
the unpatched packer with its baseline hash in Local portability patch. After
reapplying the href patch, compare the packer with the local hash in the table.
For a new pin, authenticate downloaded files against that commit's Git tree,
update this file's revision, source URLs, baseline/local hashes and deviation
statement, and retain upstream source bytes without reformatting. Reapply only
the reviewed local deviation and run the focused regression. Then pack an
authored plan with relocated output and inspect its evidence links, exhibits
and important states offline; runtime and browser gates belong to the
integrating coordinator.
