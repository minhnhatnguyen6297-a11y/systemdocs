---
title: 'NAIA-8/12: recover and finish Word export'
type: feature
ticket: 'NAIA-8'
created: '2026-10-03'
status: built
route: full
route_source: auto
review: thorough
review_source: auto
lenses_ran: [blind-hunter, edge-case-hunter, verification-gap, intent-alignment]
review_loop_iteration: 0
baseline_revision: 6c07d89a65d4a62cdddee8ba40d25903c6139f18
context: ['AGENTS.md', 'docs/spec/notary_v2/README.md', 'docs/spec/notary_v2/word-output.md']
---

<frozen-after-approval reason="User explicitly requests implement all remaining Multica tasks on 2026-10-03">

## Intent

Recover completed Word code from Multica and finish NAIA-8/12 on the current
integration branch. Owner requests all tasks, retaining the existing work.
The current main contains the newly approved MIN-141 implementation; recovered
Word work must extend it without losing its snapshot/data/migration behavior.

## Boundaries & Constraints

Always preserve customer evidence, committed snapshot semantics, revision guards,
atomic writes, draft edits and original template files. No cloud/customer upload.
Keep Word-first scope, 2-party support and owner-approved template catalogue rules
from NAIA-8/12 owner comments in `.agent/scratch/multica-intake/`.
User says posting authority follows case creation date; document issue date only
selects source address format. Keep death-certificate issuer independent.
Never change the real DB, edit original Multica worktrees, push, create PRs or send
messages to external tasks. Keep generated templates and reports in artifacts.
Do not alter root's address/import code or scratch work. Commit only this scope.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected | Error |
|---|---|---|---|
| Export | saved Stage, chosen supported template | correct Stage person slots, per-template file, preserve formatting | per-file failures |
| Shared masters | another case changes master | saved case fields stay stable | none |
| User edits metadata | stale revision/pending save | preserve input, reject stale revision, no misleading success | conflict shown |
| Migration | original docx/doc templates | new folder, source unchanged, complete per-file manifest | report unknown/ambiguous token |
| Removed fields | signed owner removal of notary number/price | remove token; report without fabricating values | numeric oracle still detects changed amounts |
| Aliases | chained rename/multiple occurrences | final token and exact occurrence accounting | fail unresolved mismatches |
| Word parts | split runs/header/footer/textbox/table | replace supported tokens preserving other parts | no silent leftovers |

</frozen-after-approval>

## Code Map

- Recoverable Word tip `6889c7b0c0ebe4ad90ee701f3f48aa031d7cc6ad`, already fetched
  from local Multica Git cache; includes NAIA-8 tip a980f87. Inspect ancestry/diff
  before integrating. It derives from fbd3c9f and lacks newer MIN-141 source.
- Original worktree:
  `C:/Users/MINH/multica_workspaces_desktop-api.multica.ai/naiad-rvfm-87364c0e4423/naia-12-e96216dde233/workdir/systemdocs`.
- `notary_v2/services/word_engine.py`: extend latest MIN-141 snapshot fields with
  recovered Stage indexing/2-party/XML part renderer; preserve confirmed death
  issuer and per-key null semantics. `word_batch_export.py`: template discovery,
  actual chosen template, cancellation/write-scope safety.
- `word_template_migration.py`, `scripts/naia12_e2e_migrate_export.py`: recovered
  migration and independent numeric/token validation, including final 6889c7b fixes.
- `case_workspace.py`, sidecar adapters, `case-drafting-model.js`: integrate
  metadata update without dropping MIN-141 commit_stage case fields/land rows.
- `word-export-dialog.js`, schemas/examples/validator: recovered UI/command wiring.
- Original templates `C:/Users/MINH/OneDrive/Desktop/2. Mẫu thừa kế` exist; count
  unlocked .docx and .doc fresh. Never commit documents containing real customer data.
- Recovered NAIA10 catalogue under original workdir `attachments/naia10-newest/` is
  stale Draft; update existing spec/catalog by current approved owner decisions.

## Tasks & Acceptance

- [x] Integrate recovered Word tip locally and reconcile conflicts deliberately;
  keep MIN-141 schema/metadata/snapshot functionality. Do not regress its tests.
- [x] Run focused current MIN-141 tests plus all Word engine/batch/migration/E2E,
  schemas, sidecar and renderer tests. Repair integration errors, never weaken tests.
- [x] Re-run migration/export on fresh copies of unlocked owner templates, use Word
  COM if available to validate .doc conversion and source/output formatting. Retain
  artifacts and report exact tested scope; do not claim unrun visual/UI acceptance.
- [x] Sync `docs/spec/notary_v2/word-output.md`, its detail, 2-party spec, contract,
  placeholder catalogue and `.agent/tasks/NAIA-8/{progress,handoff}.md` with results.
- [x] Verify local Markdown links/diff whitespace; commit scope locally and report SHA.

Given saved data, when chosen templates are exported, then each file contains correct
committed values and no unsupported token silently survives. Given MIN-141 tests,
when Word changes integrate, then all those tests still pass or a real approved
behavior change is documented with equivalent meaningful coverage. Given originals,
when migration runs, then their hashes stay identical and all outputs are traceable.

## Implementation Notes

User authorized full takeover explicitly; no generic plan approval is needed.
Work sequentially, use existing tests and local sources; report any real gap.

## Plan Change Log

## Review Triage Log

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind 1: ISO year | medium | Root ran _fmt_year('2024-02-03'); full ISO survived. Persisted snapshot dates reach this function. patch. |
| Blind 2: newline XML | medium | Root replaced a value containing newline; output w:t contained literal newline and no w:br, losing intended line layout. patch. |
| Blind 3: spaces XML | medium | Same probe showed leading/trailing whitespace without xml:space=preserve. This affects real connector tokens such as ' và '. patch. |
| Blind 4: A/B names | medium | Mapping uses party_a[0]/party_b[0], but approved Word spec requires all names for aliases. patch. |
| Blind 5: fixed-code registry keyed by filename | low | Filename-based verification is explicit existing registry behavior; accidental reuse can exempt labels. Existing known owner files work; content-pinning would add a new verification mechanism for a rare case. Reject complexity. |
| Blind 6: template path race | low | Reads use paths after containment check, so a concurrent local replacement can change the input. This requires local filesystem manipulation during export; reject additional handle-pinning complexity for this rare scenario. |
| Blind 7: output junction race | low | Destination containment precedes path writes. Concurrent replacement can redirect paths; ordinary chosen-folder workflow does not change junctions mid-export. Reject added directory-handle machinery. |
| Blind 8: draft posting value versus saved export | medium | Dialog shows caseInfo/input but export reads committed DB; no dirty-value warning or save-before-export check exists. patch: visibly require saving changed posting value before export. |
| Blind 9: no UI catalog choice | false | Current owner phase is folder-first. The spec explicitly describes catalog as backend compatibility when template_dir is absent, not an extra required UI option; clarify wording without adding another flow. |
| Blind 10: malformed Word XML skipped | medium | Root loaded a real DOCX with malformed footnote part; collector ignored that part and retained its broken bytes. Fail loudly instead of returning success for unchecked content. patch. |
| Edge 1: ISO year | medium | Same root reproduction as Blind 1. patch group. |
| Edge 2: output junction race | low | Same rare concurrent filesystem replacement as Blind 7. Reject complexity. |
| Edge 3: mock readiness | medium | Mock template-folder options use legacy inheritance readiness; real folder path uses static technical checks. Named consumer is mock UI/backend parity. patch. |
| Edge 4: orphan note paragraph | low | Root probe confirms stale parsed roots leave empty note paragraphs and removed_lines=0. Removing entire footnote paragraph can also require preserving Word note structure; rare removed-field-in-note case, reject expanded structural cleanup. |
| Edge 5: genuine DOCM | low | Migration candidate list admits DOCM but python-docx cannot read macro-enabled type. Owner corpus contains only DOCX/DOC; remove misleading support and explicitly exclude/report DOCM before writing. patch. |
| Gap: edit during metadata save | medium | Pre-verified deferred-response test is absent for the actual merge; current guard exists, but regression would silently lose edits. patch. |
| Intent: actual Electron/native picker and page appearance | maybe-false | Component/Word COM checks passed, but real native picker and visual page inspection are unrun. No completed acceptance claim; record limitation and verify in later desktop acceptance. defer, medium unverified. |
| Intent: broader backlog | false | This plan is Word recovery phase within the owner's broader takeover, not a claim of completing all Multica tasks. Other phases have separate plans. |
| Root after patches: Word oracle ignores real breaks | medium | Full 22-template rerun saved all files but flagged authorized block in 3. UQ.docx. Root independently extracted visible w:br/w:tab text: expected block is present; old _doc_paragraph_texts ignores these nodes and joins lines. Fix independent visible-text extraction and retain exact value/negative checks. patch. |

## Verification

Use isolated source copies/temporary DBs under `.agent/scratch/`; focused Python and
Node tests, contract examples, migration/export oracle, Word COM where available,
hash and link checks. Inspect every unexpected failure. Root coordinates overall
takeover and will independently review final diff and outcomes.

04/10/2026 root verification: 409 backend Word/workspace/MIN-141, 102 independent
oracle tests, 240 adapters, 190 renderer/schema/wire, 78 contract examples passed.
Actual rerun of all 22 copied owner templates: 22 saved/0 failed, negative passed,
sources unchanged. Structural checks passed for 17 DOCX; 5 DOC remain not_verified
at that layer. Word COM available; real Electron/native picker and visual pages
remain explicitly deferred. Commits a32c1fe recovery and a94e3dc review fixes.
