# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`AGENTS.md`** at the repo root — primary authority and review gates.
- **`../../docs/spec/notary_v2/`** — read the module/flow/feature spec that
  owns the area you are about to work in.
- **Domain & Platform specs**:
  - `docs/domains/inheritance/README.md`
  - `docs/platform/document-intake/README.md`
  - `docs/platform/case-workspace/README.md`
  - `docs/platform/document-generation/README.md`
  - `docs/platform/fast-text-audit/README.md`
- **`CONTEXT.md`** at the repo root (if present).

If any optional file does not exist, proceed silently. The `/domain-modeling` skill creates or updates domain context and ADRs when terms or decisions are resolved.

## File structure

Single-context repo with modular domain specs:

```text
/
├── AGENTS.md
├── docs/
│   ├── domains/                ← Domain specifications
│   ├── platform/               ← Platform capabilities
│   └── superpowers/            ← Implementation plans and specs
```

## Use the glossary's vocabulary

When naming domain concepts (in issue titles, refactor proposals, test names,
or specs), use established terms from the routed domain specs and the nearest
owning spec under `../../docs/spec/notary_v2/`.

## Flag spec conflicts

If an analysis or proposal contradicts an approved spec, surface it explicitly
rather than silently overriding.
