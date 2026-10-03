---
title: 'NAIA-4: Word to reviewed records to original template'
type: feature
ticket: 'MIN-139'
created: '2026-10-03'
status: in-progress
route: full
route_source: auto
review: thorough
review_source: auto
lenses_ran: []
review_loop_iteration: 0
baseline_revision: d266857
context: ['AGENTS.md', 'docs/spec/notary_v2/input/README.md', 'docs/spec/upload_lab/README.md', 'docs/spec/notary_v2/word-output.md', 'docs/spec/notary_v2/administrative-timeline.md']
---

<frozen-after-approval reason="Owner requests implement all remaining Multica tasks">

## Intent

Implement NAIA-4/MIN-139: import one Word contract, extract enough correctly
grouped people/assets into standard JSON, review/edit, put them into Case Drafting,
then export using the original document as the template. Preserve the previous
regex work as the single shared core. Owner comments NAIA-4
`01a0fd96-dc6d-77f5-a301-053b7eb6a651`, `01a0fd9b-ff2e-7e8c-be10-bbf2bfe91391`
02/10/2026 and `01a0ff5c-5cf6-7e55-a2e8-597143bfb0d3`03/10 authorize implementation.
The user repeats implement all in this chat. Word first; image/OCR/Excel later.

## Boundaries & Constraints

Do not guess person role, legal relationship, asset ownership or uncertain field.
Human review is required; no automatic case mutation. Keep the existing Intake
dialog and two Upload tabs. Preserve original file bytes and package parts outside
confirmed replacements. No real customer documents in Git. No external uploads,
Multica messages, push/PR/merge or source-worktree edits. Preserve MIN-141 and
integrated Word8/12 snapshot/null/revision/atomic-write behavior. Original document
identity and field evidence must survive Stage commit/reload, not only memory.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected | Error |
|---|---|---|---|
| Ordered DOCX | alternating paragraphs/tables, split runs | raw spans map to exact source nodes | explicit unsupported-part warning |
| Records | >=2 people/2 assets, one GCN with multiple land rows | enough records; fields belong to correct block | uncertain boundary stays reviewable |
| Uncertainty | duplicate/ambiguous/missing value | all evidence, no arbitrary first candidate | human correct/select before accept |
| Stage capacity | >3 assets | accepted ones only; remaining cards retained | capacity message |
| Persistence | accept/edit/commit/reload | exact source/row mapping retained transactionally | stale revision rejected |
| Template | confirmed occurrence→row+field | original-copy derivative; committed values replace exact spans | reject overlapping/unsupported span |
| Changed file/order | source hash or seat numbering changes | invalidate old mapping; re-review | never bind another person silently |
| Cancel/switch case | late intake/export response | ignore old response, original unchanged | user can retry |

</frozen-after-approval>

## Code Map

Detailed source map and implementation considerations:
`.agent/scratch/multica-intake/NAIA-4-implementation-research.md` (read completely).
Recovered specification:
`C:/Users/MINH/multica_workspaces_desktop-api.multica.ai/naiad-rvfm-87364c0e4423/naia-4-b998004dfaf7/workdir/systemdocs/docs/spec/upload_lab/document-field-studio.md`.
Read current module/feature READMEs first. Recover only relevant spec; old task
records are historical, broad multisource/tab3 scope is superseded.

- `tools/regex_workbench/engine/runner.py::run`, profiles and guarded extractor:
  shared detection; add declarative grouping there when necessary, no second regex engine.
- Document Intake DOCX adapter + new ordered reader: immutable bytes, hash,
  body/table text order, exact raw span/node map, field-specific source_refs.
- Normalization/suggestion wire: canonical field keys; uncertainty null plus
  alternatives/evidence; preserve one or multiple land rows, no bogus serial.
- Existing Intake review and case-drafting-model: review/edit/accept, keep cards
  when capacity rejects, preserve source→row context through actual backend save.
- `case_workspace.py`, schemas/adapters: optional documented durable import context
  with source IDs only; backend authorized data store, no arbitrary client read path.
  Save Stage/context with base_revision and transaction; restore on case switch/reload.
- Word services: confirmed row_id+field+occurrence bindings resolve current committed
  slot; source/template hash verification; derivative changes only supported w:t spans.
  Keep media/rPr/sections/unmodified XML parts, no paragraph.text assignments.

## Tasks & Acceptance

- [x] Ordered source reader and shared-core grouping; enough correctly owned fields.
- [x] Review cards with field evidence, JSON local export, override/ambiguity handling.
- [x] Durable source and binding context: accept, commit, reload, stale guard, switch.
- [x] Confirm original-template mapping and export through integrated Word services.
- [x] Synthetic labeled fixtures including multiple people/assets, land rows, repeated
  identical strings, merged/nested tables, split formatting, Unicode, unsupported spans.
- [x] End-to-end test DOCX→review→saved Stage→original template→Word validates record
  count, field ownership, edited values, static text/format/media preserved.
- [x] Sync feature/input/stage/Word specs and contract at the smallest applicable
  level; update MIN-139 execution records with owner source and actual coverage.
- [x] Focused meaningful Python/Node/schema checks, local links, diff whitespace,
  local commit of only this scope. Report artifacts, SHA and untested office corpus.

## Implementation Notes

Exactly one coding executor. Root handles overall review. Read the integrated
Word code first; do not recover stale engine. Source store belongs to existing
engine-data arrangement; no new DB technology. Claims of accuracy are limited
to labeled fixtures tested here; missing office corpus does not block building
the authorized reviewable flow. When ambiguity cannot be resolved, keep it visible.

## Plan Change Log

04/10/2026 Owner steers immediate priority to administrative timeline SOT. This
DOCX phase remains authorized and queued after that phase; no second coder writes
shared workspace/Word files while timeline coding is running.

04/10/2026 Timeline/Word phases are complete locally and reviewed at d266857.
Execute this DOCX phase next. Existing timeline ledger is the administrative SOT;
do not make another dataset or infer dated historical addresses from pending source.
Use the existing Intake UI and clear Vietnamese text, not a separate third tab.
Preserve commits a94e3dc Word fixes and a3b33dc timeline invariants. Root-only pending
NAIA-22/24 records and generated BMAD render artifacts are unrelated to this commit.

## Review Triage Log

## Verification

Isolated temporary DB/source corpus in scratch. Assert record identity and field
ownership, genuine Stage reload/transaction/stale conflicts, hash invalidation,
original-file hashes and untouched package XML, UI review/accept/mapping behavior.
Existing MIN-141/Word focused regression and contract examples must remain passing.

## Executor evidence — 2026-10-04

Implemented source reader/store, shared grouping, review/edit/JSON, durable Stage
context and immutable derivative, confirmed exact-span original export, additive
contracts and module specs. Backend and UI synthetic end-to-end checks pass.

Verification: 8 new Python/schema tests, 242 existing Intake/Workspace/Word tests,
37 shared-core tests, 145 Node model/view/Intake/Word tests; 78 contract examples
with zero unexpected outcomes; 28 local links and git diff whitespace pass.
Sidecar focused 79+6 regression tests were run. SQLAlchemy reports an existing
Python datetime-adapter deprecation warning.

Untested: office corpus, visual Electron/Word page rendering, packaged clean-machine
run. Arbitrary candidate split/merge UI remains outside this bounded implementation;
uncertain candidate boundaries stay visible for human correction. Desktop sidecar
provides the source store; other callers must supply it when committing imported cases.
Root review and local commit hash are recorded after executor handoff.
