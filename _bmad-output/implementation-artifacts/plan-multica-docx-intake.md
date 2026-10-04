---
title: 'NAIA-4: Word to reviewed records to original template'
type: feature
ticket: 'MIN-139'
created: '2026-10-03'
status: built
route: full
route_source: auto
review: thorough
review_source: auto
lenses_ran: ['blind-hunter', 'verification-gap', 'intent-alignment', 'edge-case-hunter']
review_loop_iteration: 5
baseline_revision: d2668572d823cbfe49a79be4befd3bc7fd33efea
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

Existing verification runtime (no install):
`C:/Users/MINH/.codex/worktrees/1aae/systemdocs/.agent/scratch/multica-intake/schema-venv/Scripts/python.exe`
includes jsonschema and system-site packages. Run notary tests with cwd
`notary_v2` to keep relative Word-template paths valid. Node uses
`NODE_PATH=D:/systemdocs/shell/node_modules`. Optional pytest basetemp belongs
under `.agent/scratch/` with a fresh uniquely named directory, not shared
pytest-current or another agent's test directory. Actual Electron harness
uses `D:/systemdocs/notary_v2/venv/Scripts/python.exe` for Playwright and sets
backend Python to schema-venv; both are already installed.

Exactly one coding executor. Root handles overall review. Read the integrated
Word code first; do not recover stale engine. Source store belongs to existing
engine-data arrangement; no new DB technology. Claims of accuracy are limited
to labeled fixtures tested here; missing office corpus does not block building
the authorized reviewable flow. When ambiguity cannot be resolved, keep it visible.

## Plan Change Log

04/10/2026 iteration 3: all four lenses collected. Amend retry/selection lock,
asset-zone bounds, numeric land review, empty land evidence, source-store atomic
publication, original-export destination errors and late-response handling.
Preserve all 19 DOCX tests and successful current Electron result. Root reverses
only code/contracts to the preserved baseline, then executor reapplies KEEP.
No new business decision: reject unsupported boundaries, keep editable uncertainty,
preserve original sources and session isolation. Add cancellation coverage.

04/10/2026 iteration 2: all four review lenses collected. Complete numeric
spans, invalid-date rejection, detach/save locking, mapping refresh, source
ordinal schemas, custom-profile validation, cross-paragraph Word field safety,
extraction integrity, land provenance and genuine roundtrip/schema tests amended
outside frozen intent. Root reversed code/contracts only from d266857 to the
current attempt; 8e5a994 remains recoverable. Reapply the KEEP patch before fixes.
Keep all iteration-1 invariants and successful isolated Electron flow; do not
retain the old test assertion that invalid input may silently accept an old date.
Unused source files remain preserved; document limits without automatic deletion.

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

### Review iteration6 — final re-derived code, all four lenses collected

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind6 1 one-digit ISO prefix | medium | Profile ISO demands2digits while normalizer accepts1; year alternative silently takes1980 from1980-2-31. Direct pattern quantifier correction, patch. |
| Blind6 2 exponent numeric prefix | medium | Pattern recognizes leading1 in1e309, leaving suffix outside evidence. Direct numeric-token regex alternative captures whole unsupported notation for existing null/error path; patch. |
| Blind6 3 reanalyze finished sources | medium | Pre-existing MIN112 loop already sends every listed nonerror source including xong at d266857. No new automatic acceptance: every duplicate remains reviewable, explicit detach available. Pre-existing batch-selection behavior, defer rather than redesign this DOCX change. |
| Blind6 4 source label in cards | medium | source_label exists in refs/store but card/evidence renders only value/span. Direct display of existing label, patch. |
| Blind6 5 stale export dialog result | medium | Model returns stale and correctly protects current case, but dialog reads current wordResult after await without rr.stale. Direct stale return check before display mutation, patch. |
| Blind6 6 reader preallocation limits | low | Expanded ZIP guard100MB and file20MB already bound input; pathological many-node/source text near bound can still use more memory before text rejection. Uncommon adversarial layout; reject further reader guard complexity. |
| Blind6 7 duplicate ZIP entries | low | Duplicate member names require irregular package; ordinary Office creates unique parts. Reader filename duplication can affect preservation. Reject new duplicate validation/branches for uncommon malformed package; no supplied office case. |
| Blind6 8 valid checksum malformed package | low | Store alone writes exact package shape, checksum catches changes; matching checksum plus invalidshape requires manual change of source+checksum or unknown future version. Reject new schema surface/guards without reachable ordinary writer. |
| Blind6 9 Strict format | low | Strict namespace unsupported and parse fails, no silent import. Low interoperability corner, direct spec-supported-format notice patch; no new parser. |
| Blind6 10 backup steps | low | Spec says copy DB+sources but lacks sequence. Direct operational explanation patch, actual joint restore remains unverified/deferred. |
| Edge6 1 Unicode minus | medium | Unicode− remains separator and50captured positive. Direct regex sign class+normalize sign, existingnegative/error path; patch. |
| Edge6 2 exponent | medium | Same whole token defect as Blind6 2; patch grouping. |
| Gap6 | false | No verification gaps found; no missing-test claim filed. |
| Intent6 1 corpus | maybe-false | carried previous corpus evidence limitation/defer unchanged. |
| Intent6 2 UI | maybe-false | carried native-picker/clean-install limits; real Electron HS-8 proves specified local IPC flow. Existing defer unchanged. |
| Intent6 3 JSON | maybe-false | carried original suggestion download vs reviewed Stage documented reading; no new consumer requiring alternate wire. Previous verdict/route preserved. |
| Intent6 4 cross-case reuse | false | carried one-contract/case scope, unrelated-template library not required. |
| Intent6 5 page layout | maybe-false | carried actual Word pages unverified; preserve prior defer. |
| Intent6 6 office readiness | maybe-false | carried corpus/install/joint recovery not claimed as complete. Existing defer unchanged. |

After individual verdicts: no intent_gap/bad_plan. Numeric token/date pattern
and label/stale-display direct patches add no public surface or unobserved
state guards; same executor re-engaged. README/spec operational corrections
are direct text edits. Pre-existing batch reanalysis deferred, not a new source
lifecycle redesign. Re-run plan checks after patches; no further loopback.


### Review iteration 5 — all four lenses collected, 2026-10-04

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind5 1 several candidates same row | low | carried same manually composed mapping as Blind4 6/7: normal accept always creates a new unique row. Reject added merge-state complexity; no new merge UI. |
| Blind5 2 corrupt removed source | false | carried source-detach recovery explicitly implemented and tested, available without reading the corrupt package; removing Stage rows alone does not detach retained original source. |
| Blind5 3 tracked/textbox content | low | Reader explicitly marks unsupported nodes and emits warning, with body extraction documented; no supplied case establishes deleted w:delText emitted (reader only w:t). Unusual tracked/textbox layout needs broader active-view parsing; reject complexity, manual review remains. |
| Blind5 4 footnotes | low | carried Blind4 5 unchanged body-only scope and uncommon scalar footnote; reject additional guards/parser. |
| Blind5 5 localized numeric input | medium | Browser number inputs sanitize non-number string before onchange; raw localized value may become empty despite reviewedArea support. Direct input text/inputmode correction and test; patch included rederive. |
| Blind5 6 empty land after deletion | medium | acceptSuggestion rejects array.length0, though Stage permits empty land rows. User can delete all inaccurate rows but cannot retain correct other fields. Direct length guard deletion with identity0 tested; patch included rederive. |
| Blind5 7 ambiguous_group confirmation | false | candidate displays explicit ambiguous_group warning and all fields; user explicitly presses accept. That is the documented human group review, not automatic mutation; intent does not mandate another checkbox. |
| Blind5 8 stale mapping when selecting source | medium | originalSourceId/checks changed but listBox retains old proposals until successful request. Failed new source leaves misleading old rows visible. Direct clear/loading state at existing transition; patch included rederive. |
| Blind5 9 options reload after save error | medium | saved binding success followed failed load leaves mappingDirty and no failure message; retry path needs visible saved/reload state rather than silent return. bad_plan. |
| Blind5 10 README profile version | low | Exact README transfer1.1.0 vs profile1.1.2; direct version correction patch included rederive. |
| Gap5 text-limit fixture false protection | medium | preverified: all-X fixture produces no candidates and parse_failed even without limit. Replace with recognizable fixture plus padding and under-limit control, patch included rederive. |
| Edge5 invalid source date | medium | norm_date raw31/02 returnsnull but ref.core_state matched, so accept copies raw without requiring correction, save later fails. ISO normalization also returned impossible dates unvalidated. bad_plan: common date normalization and DOCX evidence error/correction. |
| Intent5 1 corpus | maybe-false | carried previous corpus limitation, existing defer unchanged. |
| Intent5 2 UI/clean machine | maybe-false | carried native-picker/clean-install limit; actual Electron HS-7 proves real IPC/save/export within stated isolation. No repeat defer. |
| Intent5 3 independent JSON | maybe-false | carried documented original-suggestion download vs reviewed Stage reading, no demonstrated required alternate consumer; earlier verdict/route preserved. |
| Intent5 4 cross-case templates | false | carried one imported contract and its case scope, unrelated-case reuse not required by frozen intent. |
| Intent5 5 Word page layout | maybe-false | carried unverified actual Word page appearance, existing defer unchanged. |
| Intent5 6 office completion | maybe-false | carried corpus/install/recovery boundaries; source implementation does not claim these checks passed. No repeat defer. |

Grouping after verdicts: invalid source date/correction and successful binding
save followed reload error are bad_plan; iteration5. Small direct guard/display,
README and test-fixture corrections incorporated. Keep frozen intent unchanged.

### Re-derivation iteration 5

KEEP .agent/scratch/docx-code-review5-keep.diff reapplied exactly once. Preserve
all iteration4 source/template atomic integrity, numeric exact spans/export,
immutable downloaded schema-valid original JSON, identifier-missing assets,
retry/locks, 35 DOCX and UI regression tests, MIN141/Word/timeline baseline.

- Date source evidence must not silently fall back to raw invalid calendar date.
  Validate all recognized complete date formats, including ISO, with calendar;
  null normalization for a present invalid date marks DOCX refs error and visible
  warning. Human correction required before accept; legitimate year-only stays
  allowed. Preserve exact raw source spans. Test raw31/02 and invalidISO then
  corrected accept/commit; no invented date or relaxed backend validation.
- When binding commit succeeds but options reload fails, preserve committed mapping
  and saved revision, show that save succeeded but reload failed, discard stale
  displayed options/choices and provide a working retry through existing source
  selection. Never restore precommit context or export stale unsaved selection.
  Case-switch must not update new case UI. Test save success/reload failure/retry.
- Direct patch corrections: land area input text + decimal inputmode so1.234,5
  reaches parser; finite/nonnegative validation remains. Allow intentionally empty
  land_rows after deleting every row, identity[]; receive/save/export remaining
  valid asset fields, no rebind removed source occurrences. Clear mappingChoices
  and listBox immediately on original-source selection; display loading/error,
  new source failure cannot show old proposals. README profile1.1.2 alignment.
- Limit text fixture must be recognized fixture_bytes plus padding; under-limit
  same fixture is accepted, above-limit rejected before store, valid batch source
  survives. Prove removal of text-limit check makes test fail (temporary mutation
  restored immediately, scoped test only); do not keep any disabled guard.

Known-bad states: wrong raw date silently accepted; saved binding reported
neither saved nor reload error; stale source choices; lost localized area;
empty-land correction blocked; false-positive limit test. No new public surface.


### Review iteration 4 — all four lenses collected, 2026-10-04

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind4 1 signed area lost | high | Profile asset.dien_tich skips minus before captured digits; Edge4 executed -50 becomes 50. Wrong source value and replacement span. bad_plan. |
| Blind4 2 detach rollback | medium | Word dialog removes context before commit; failed result leaves removed draft/source still visible. Normal retry can persist unconfirmed removal. bad_plan. |
| Blind4 3 over20 land message | low | acceptSuggestion handles length>20 with malformed JSON notice although schema allows extraction of more rows. Direct correction, patch grouped into rederive. |
| Blind4 4 JSON UI metadata | medium | Download closes over mutable news; review adds private keys but replacer strips only reviewed. Standard wire output can violate field schema or include invalid pending edit metadata. bad_plan. |
| Blind4 5 footnote coverage warning | low | Only body is documented and read; footnote/endnote bodies preserved but not specifically warned. Uncommon scalar data in notes; reject additional per-part guard complexity. Reader is not advertised as full document coverage. |
| Blind4 6 several candidates same row | low | Backend allows manually composed many-to-one records; normal acceptSuggestion always adds a fresh unique row. No merge UI/caller creating this state. Reject new validation complexity for nonordinary manually fabricated mapping. |
| Blind4 7 several sources overwrite land identity | low | Same manually composed row across sources can overwrite UI-only identity; ordinary accept creates new row for every candidate, including other files. Reject source-indexed identity redesign for unreachable ordinary UI. |
| Blind4 8 os.link filesystem support | maybe-false | NTFS default app data supports hard links; no evidence of supported non-hardlink data location. Medium unverified: filesystem installation test would settle. defer. |
| Blind4 9 land evidence location display | low | Per-cell source refs contain span, but label displays only row/field/raw. Direct display correction, patch grouped into rederive. |
| Blind4 10 native picker/package | maybe-false | carried package/picker limits already recorded; isolated Electron HS-6 proves actual IPC path, native dialog/clean machine remain unverified. Keep existing defer, no new entry. |
| Edge4 1 negative area | high | Same executed claim as Blind4 1; complete signed span must survive review/replacement. bad_plan, numeric group. |
| Edge4 2 nonfinite area | medium | 400-digit source normalizes to float infinity; strict JSON cannot carry it, so normalizer must reject and keep raw evidence. bad_plan, numeric group. |
| Edge4 3 missing identifier drops asset | medium | Adapter skips every asset group lacking serial/parcel/register even when explicit heading/address/land evidence exists. Normal incomplete documents lose reviewable record. bad_plan. |
| Gap4 DOCX limit verification | medium | preverified: text over-limit test exercises different adapter; searches/read tests found no DOCX100MB/100000-character rejection through analyze or mixed-batch continuation. patch tests in rederive. |
| Intent4 1 corpus grouping | maybe-false | carried representative office corpus still absent; previous defer unchanged, no repeat. |
| Intent4 2 real UI | false | Root isolated real Electron HS-6 completed review/edit, save/reload, confirmed original mapping and export; test-double native picker explicitly bounded. |
| Intent4 3 JSON reading | maybe-false | carried interpretation: suggestions JSON and reviewed Stage are distinct documented structures, no new consumer proving need for third output. Prior rejected/deferred interpretation unchanged; specific wire metadata defect handled Blind4 4. |
| Intent4 4 cross-case template reuse | false | carried intent imports one contract into its case and exports edited case; it does not require unrelated case template library. |
| Intent4 5 Word layout | maybe-false | carried actual Word page inspection remains unverified; preserve prior defer, no repeat. |
| Intent4 6 complete office adoption | maybe-false | carried source/dev implementation does not prove clean installation/corpus/office acceptance. Existing defer unchanged. |

Grouping after individual verdicts: complete finite numeric evidence (Blind4 1,
Edge4 1/2); failed detach restoration; immutable standard JSON download;
identifier-missing recognized asset retention. All four bad_plan groups trigger
iteration4. Small message/evidence-display corrections and DOCX limit tests
are included in this rederivation. No frozen intent change. No new merging UI,
per-source land redesign, note parser or nontext image editing.

### Re-derivation iteration 4

KEEP .agent/scratch/docx-code-review4-keep.diff: reapply exactly once to the
reverted product tree. Preserve all previous iterations and successful tests,
checksum/atomic-store, per-cell review and source identities, reopen/pending cards,
case race guards, Word/MIN141/timeline baseline. Docs/tasks remain in place.

- Numeric evidence: shared profile captures complete signed area, including minus;
  shared normalization never emits nonfinite numbers. Invalid negative/nonfinite
  source scalar or land cell remains raw/null with explicit uncertain/error state
  requiring human correction before acceptance; do not silently turn it positive
  or omit its sign from source replacement. Keep localized 1.234,5 normalization.
  Test source scalar and land cells, strict JSON and corrected exact-span export.
- Detach: save failure/exception restores original context and stageDirty for the
  same case, retaining visible source and allowing retry. Never restore an old
  case after switching. Keep existing save lock and successful detach behavior.
- JSON download is an immutable snapshot of original standard Intake suggestions
  and errors at analysis completion, before review mutates model objects. Explain
  in UI/spec that edits are saved into Stage. Snapshot must validate against Intake
  schema after review/invalid pending edits and not include private review keys.
- Keep explicitly recognized asset groups with supported address or land evidence
  even when all identifiers are missing; fragment warning makes missing fields
  visible. Do not create empty/unlabeled noise assets or guess identifiers.
- Direct corrections: distinguish land capacity>20 from malformed JSON; display
  existing per-cell raw span position; test both relevant UI outcomes.
- Add actual DOCX analyze limits/mixed batch tests, protecting both100MBexpanded
  and100000text checks, rejected source not stored and valid source survives.

Known-bad state avoided: negative evidence rewritten as positive; Infinity on
wire; missing asset disappears; failed detach silently pending; download includes
private/invalid review state. Current implementation commit0f09d506 remains
recoverable in Git; reverse only DOCX product delta against d266857.


### Review iteration 3 — verdicts before grouping

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind3 1, replacement crosses inline drawing | low | Reader emits no separator for nontext drawing; spans can move text across image. Exact bad arrangement possible, but inline image interrupting a detected scalar is uncommon. Reject: dedicated new nontext-boundary guard complexity for this uncommon layout; existing source/part preservation remains. |
| Blind3 2, binding-save failure cannot retry | medium | confirmOriginalBindings marks stageDirty; commit failure retains it; next confirmation refuses dirty state. bad_plan: restore pre-confirm local context/dirty state on failure while retaining human checkbox choices, permit retry and test fail→success. |
| Blind3 3, checkboxes editable during save | medium | Only export/doc toolbar locks; mapping checkboxes onchange remains enabled and later load overwrites newer choice. bad_plan: lock mapping selection through in-flight save and preserve eligibility on unlock. |
| Blind3 4, subdirectory/error created before validation | low | Mapping error may leave an empty HS directory, no output data. Error mapping subclaim separately verified as Edge3 2 below. Reject cosmetic empty-directory cleanup complexity; do not delete preexisting folders. |
| Blind3 5, grouping begins before asset zone | high | Zoner searches asset marker after parties cursor; runner matches labels on full folded text and filters only end. Earlier title/body label can create group containing party fields. bad_plan: restrict starts and end to asset zone, correct fallback/uncertainty and verify labeled heading before parties. |
| Blind3 6, negative/nonfinite land review accepted | medium | Number(input.value) ignores min; review marks cell reviewed and accept produces invalid Stage that backend later refuses. bad_plan: show cell error and block acceptance until fixed; preserve pending typed value and other reviewed cells. |
| Blind3 7, earlier suggestion review hidden after next analyze | medium | Callback review.innerHTML='' and loops news only; model retains old suggestions. Clear/latest-only behavior predates DOCX review, but new field editing is only reachable in dialog. bad_plan: render all pending cards after another analysis (including error/cancel) and preserve typed reviews, test two analyses. |
| Blind3 8, source/template final files written directly | medium | save_template uses xb on digest destination; interruption leaves wrong bytes under same digest and retries fail. Source save can leave incomplete folder. bad_plan: write temp then publish without overwrite, preserve original immutability and retry interrupted publication safely; test failure/no partial final/template retry. |
| Blind3 9, real corpus | maybe-false | carried: same previously logged office-corpus requirement; no new source proving required grouping error. Prior defer retained, no repeat. |
| Blind3 10, clean package/restore not exercised | maybe-false | Word/baseline packaging deferred already; no evidence of actual install defect. Medium unverified, defer packaged DOCX flow plus joint source/database backup/restore acceptance. |
| Gap3 1, original cancellation cleanup not tested | medium | Pre-verified: old batch cancellation bypasses export_original; add cancellation after temp exists, no output/temp, original unchanged. bad_plan verification combined with atomic-store group. |
| Edge3 1, empty land evidence drops whole source | high | field_value rejects empty refs; adapter creates land_rows even when all matches have no spans. One blank Loại đất row can lose valid people/assets. bad_plan: keep valid records and explicit missing-data warning, do not invent evidence. |
| Edge3 2, original child mkdir escapes Word errors | medium | child.mkdir outside WordBatchError mapping raises raw permission/file-exists failure. bad_plan: map OS destination errors consistently and test locked/file-as-folder. |
| Edge3 3, late original export clears current state | medium | exportWord clears wordBusy before session test, returns old r without stale; dialog receives old success. bad_plan: reject late response before mutating state, return stale flag already used by dialogs, test case switch and concurrent new-case export. |
| Intent3 1, office grouping | maybe-false | carried: same corpus finding, no repeat defer. |
| Intent3 2, arbitrary split/merge | maybe-false | carried: same absent required example, prior defer retained. |
| Intent3 3, only confirmed Word occurrences | false | carried: explicit original-preservation constraint. |
| Intent3 4, Intake JSON versus committed rows | false | carried: existing Intake JSON contract, no second export required. |
| Intent3 5, backend lifecycle covered | false | Positive observation, not a defect. |
| Intent3 6, Electron unverified in diff | false | Root current real Electron flow artifact ok=true; tests use a native-picker double, and actual picker/pages/install remain openly unverified. |
| Intent3 7, regex shared | false | carried: positive invariant, no duplicated engine. |

Group verified survivors only after individual verdicts: binding retry/lock;
asset zone bounds; invalid land review; pending-review retention; atomic source/
template publication + cancellation tests; empty land evidence; destination OS
mapping; session isolation. All route to bad_plan. Unverified packaging is appended
to deferred-work; rare inline-image crossing and empty-directory cosmetic cleanup
are rejected without new guards or deletion behavior.

### Re-derivation iteration 3

KEEP patch: `.agent/scratch/docx-code-review3-keep.diff`. Root reverses only
code/contracts; docs/task records remain. Reapply KEEP once, then fix the eight
verified groups above with focused tests and current plan Verification. Do not
redo previous review findings or erase their tests, and do not add speculative
image-boundary or directory-cleanup behavior rejected above. Keep 19 DOCX tests,
all iteration-2 safety/schema/provenance rules, snapshot/null/revision behavior,
shared core, local-only sources and successful isolated Electron integration.
Source/template publication must not overwrite already valid immutable files;
interrupted files must not leave an unrecoverable digest destination. Missing
stored checksums still require reimport/review, no silent trust.
No children or root-owned plan/global spec/word-output/deferred edits. Commit only
owned phase files and report actual tests and remaining native/package limits.
Pending-review retention also covers closing/reopening Intake with suggestions
already in the model: populate their review cards before another successful
analysis, including an empty/error/canceled analysis. Do not require re-import
to edit a retained ambiguous record. Preserve typed review metadata on reopen
and test this ordinary continuation of the same retention group.

Root verification 04/10/2026: isolated real Electron, main/preload/sidecar,
two-party DOCX import of 2 people and 2 assets, name edit, Stage and diagram save,
reload, 25 binding proposals, original-template export passed. Artifact:
`artifacts/docx-electron-20261004/startup-report.json`, `ok: true`.
Original source hash, untouched ZIP parts and workspace database hash unchanged.
Tracked engine code copied to isolated artifact directory before startup.
Native picker is a test double returning paths; main token handling remains real.
Native-picker interaction, office corpus, Word page rendering and packaged build
remain unverified. Review iteration 2 is collecting lenses, not yet triaged.

### Review iteration 2 — all four lenses collected 04/10/2026

Every row below is a verdict before grouping. Earlier triage remains historical.

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind2 1, area 1.234,5 truncated | high | transfer land.dien_tich permits only one separator; norm_number already supports both but receives only 1.234. Remaining ,5 is outside the replacement span. bad_plan. |
| Blind2 2, invalid edit accepts old date | high | reviewSuggestion returns false without invalidating the old reviewed value; onchange ignores return. Existing Node test even asserts acceptance of the old date after 31/02/1980. bad_plan. |
| Blind2 3, detach concurrent commits | medium | detach callback checks savingMeta but never sets it while awaiting commitStage. A second click changes local context and sends same revision. bad_plan. |
| Blind2 4, mapping disappears after save | low | renderDocs clears listBox, which owns mappingBox; confirm callback does not rebuild it. Common adjustment path requires reselecting source. bad_plan with cohesive mapping refresh. |
| Blind2 5, source row 21 violates schema | medium | extraction enumerates unrestricted source rows; deleting first leaves source identity 21 in at most 20 Stage rows. Python permits that source index, schema caps identity at 20. bad_plan: distinguish source ordinal from Stage capacity. |
| Blind2 6, malformed land rule crashes lint | medium | validate_profile checks list container only; lint_profile calls rule.get without element validation. Custom profile input can reach the shared workbench runner. bad_plan. |
| Blind2 7, cross-paragraph Word field unsafe | medium | reader only rejects paragraphs containing fldChar, so an intervening result paragraph is supported and replaceable. bad_plan: reject whole field range including nested fields across paragraphs. |
| Blind2 8, extraction JSON integrity missing | medium | DocxStore.load hashes original only; valid altered extraction.json can change occurrence/span metadata while original passes. bad_plan: pin package bytes and reject changed/missing integrity data before use. |
| Blind2 9, unused files retention undocumented | low | save persists source before acceptance; templates may exist after a rolled-back DB transaction. Original preservation is intentional; no owner authorizes automatic deletion. Document current keep behavior and cleanup limits, do not invent retention duration or delete originals. bad_plan docs clarification. |
| Blind2 10, land evidence lacks profile version | medium | ordinary refs include profile_id/version and candidate_state; land refs omit them despite §13.17 provenance contract. bad_plan. |
| Edge2 1, invalid date accepts old value | high | Same demonstrated date defect as Blind2 2; its guard snippet is a proposed correction, not actual source. bad_plan. |
| Gap2 1, restore source row after commit/get untested | medium | Pre-verified: tests only retain [2] before backend roundtrip; missing restore calls lose identity on next edit. bad_plan verification. |
| Gap2 other, unsupported proposal empty slot violates schema | medium | binding_proposals emits slot='' for removed/unmapped occurrence; word-export schema requires minLength 1 unconditionally. Existing schema test uses only unchanged rows. bad_plan: allow empty only for unsupported proposal, confirmed binding still requires real slot. |
| Intent2 1, real office grouping coverage | maybe-false | carried: same profile/labels/corpus claim as earlier Intent1; defer already recorded, no repeat defer. |
| Intent2 2, arbitrary split/merge editor | maybe-false | carried: same missing required real example as earlier Intent2; no repeat defer. |
| Intent2 3, original template changes only confirmed occurrences | false | carried: explicit preservation constraint excludes broad replacement of unrecognized clauses. |
| Intent2 4, downloaded JSON not committed rows | false | Existing Intake contract defines suggestions/errors JSON, and grouping creates correctly typed records on acceptance. No requirement for a second committed-row JSON export. |
| Intent2 5, two-party adapter lifecycle now covered | false | Positive observation confirmed by full adapter test; not a defect. |
| Intent2 6, actual Electron end-to-end missing | false | Root has now run isolated real Electron import/edit/accept/save/reload/mapping/export successfully; artifact above. Native picker, page rendering and packaging remain explicitly unverified. |
| Intent2 7, shared regex ownership | false | carried: positive observation; no duplicate engine. |

Grouping after verdicts: area; invalid-date review (Blind2 2/Edge2 1);
source-detach concurrency; mapping refresh; source-row/schema identity;
profile validation; whole Word field safety; extraction integrity; retention docs;
land provenance; roundtrip identity verification; unsupported proposal schema.
All verified groups route to bad_plan for cohesive re-derivation. No new frozen
business decision is required; keep originals and reject uncertain edits.

### Re-derivation iteration 2

Reapply `.agent/scratch/docx-code-review2-keep.diff` after root reverses only
the DOCX code/contract delta; keep prior DOCX docs/task records and root artifacts.
Preserve all working iteration-1 behavior and tests, except the test that asserts
old-date acceptance after an invalid edit: replace it with genuine blocked-accept
checks. Keep the successful Electron flow and its isolation unchanged.

Amend implementation and verification to fix every verified group above:
capture the complete localized numeric token and use consistent normalization
for extraction and evidence selection; invalid date edits invalidate acceptance
and display the error until corrected; lock detach through save and retain
mapping choices after refresh; source ordinals must be independent of the 20-row
Stage limit with correct schemas and >20-source-row roundtrip checks; validate
every custom land rule before linting; track nested Word field state across
physical paragraphs and reject result spans; verify saved extraction bytes,
fail clearly for missing/corrupt checksum instead of silently trusting old data;
include profile/candidate metadata on land refs. Clarify that currently unused
source/template files are retained locally, no automatic cleanup/retention period
has been approved, backup/cleanup must preserve every referenced source/template.
Do not create deletion behavior. Add real model commit/get identity restoration
checks and schema checks for removed/unsupported proposals. Unsupported proposals
may have no slot, but supported proposals and saved bindings must have one.

Exactly one executor, no children. Run focused meaningful checks covering these
edits and the plan's existing Verification. Commit only this phase's code/spec/
contract/test/task files; exclude root plan/deferred-work, global spec README,
NAIA-22/24 and future address plan. Report changed files, test counts and limits.

KEEP: immutable original Word, unrelated ZIP parts, supported mixed-style guard,
source labels/capacity/detach recovery, per-cell ambiguity, source row identities,
transactional new-binding validation, snapshot/null/revision checks, selected
parent destination, shared regex ownership and all previous Word/timeline work.

Root review 2026-10-04, all four lenses collected before triage. Every finding
is recorded separately before grouping. Numbered references identify each lens's
ordered findings; the blind lens's arithmetic line is not a defect.

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind 1, deleted land row changes Word value | high | UI splices arrays; refs retain original land_row; slot_for uses that index. Original first-row text can receive second-row values. bad_plan: preserve per-source land-row identity. |
| Blind 2, one edited land cell approves all ambiguity | high | acceptSuggestion only checks field.reviewed; root executable probe confirms one of two ambiguous cells edited still accepts. bad_plan: review each ambiguous cell separately. |
| Blind 3, evidence dates become unnormalized | medium | Evidence button copies raw_snippet into normalized_value; reviewSuggestion has no date conversion and Stage requires ISO. bad_plan: normalize reviewed values by existing field rules. |
| Blind 4, empty catalog value selectable | medium | proposals supported checks XML only; reviewed_template refuses empty values after mapping save. bad_plan: disable unsupported/empty slots with visible reasons. |
| Blind 5, saved bindings shown unchecked | medium | dialog creates unchecked boxes but ready Word options can use existing bindings. The displayed selection can misdescribe what exports. bad_plan: display saved selection accurately. |
| Blind 6, cannot clear all saved bindings | medium | dialog rejects empty choices although context validator supports empty bindings. bad_plan: explicit clear/save path. |
| Blind 7, ninth DOCX source prevents saving | medium | each intake permits eight, acceptSuggestion appends unlimited sessions, validate_context caps total eight. bad_plan: check before adding a row and offer detach-source recovery. |
| Blind 8, corrupt source prevents removing all related rows | medium | validate_context loads original before pruning removed records; UI offers no source detach. bad_plan: explicit detach must not depend on reading corrupt source. |
| Blind 9, wrong slot saved successfully | medium | context validates occurrence/field but not slot_for using saved row/seat. reviewed_template discovers mismatch only at export. bad_plan: validate new binding against composed committed snapshot/catalog during same transaction. |
| Blind 10, evidence edits shifted land row | high | UI evidence action accesses rows[original land_row-1] after splice. bad_plan: same land-row identity defect as Blind 1. |
| Blind 11, indistinguishable source buttons | medium | all buttons identical text; context exposes only ID/hash. With two sources humans cannot identify original. bad_plan: safe backend-produced filename/display label. |
| Edge 1, deleted row export mismatch | high | Verified as Blind 1; same defect, independent finding retained. bad_plan. |
| Edge 2, land-row ambiguity bypass | high | Root probe verifies acceptance after unrelated cell edit; same defect as Blind 2. bad_plan. |
| Edge 3, selected raw date rejected | medium | Same evidence path as Blind 3; no downstream normalization before Stage validation. bad_plan. |
| Edge 4, mixed run styles disappear on replacement text | medium | replace_spans puts all new text in first run and clears later runs, so bold+italic field becomes only bold. bad_plan: reject mixed-format occurrences with an explicit reason; preserve every original run, do not invent a formatting policy. |
| Gap 1, original adapter revision guard untested | medium | Pre-verified: service tests bypass sidecar branch and no original_source_id adapter test existed. Add genuine stale-adapter export/no-write test. bad_plan verification. |
| Gap 2, dirty-original-export test never exports | medium | Pre-verified: test only calls intakeAnalyze. Add real model export dirty guards and source/revision payload assertions. bad_plan verification. |
| Gap other, subdirectory response contract mismatch | medium | Original branch passes child folder to _batch_data; existing contract test requires granted parent destination and child output_file. patch, retained in re-derivation. |
| Intent 1, real corpus coverage of grouping | maybe-false | transfer profile recognizes bounded labels; no office corpus establishes a reachable unsupported required contract. Medium unverified; defer representative corpus evaluation, not claim universal accuracy. |
| Intent 2, no arbitrary candidate split/merge UI | maybe-false | Existing review edits recognized fields; no example establishes a required wrong grouping recoverable only by a new grouping editor. Medium unverified; defer with actual mislabeled contract needed to decide. |
| Intent 3, unrecognized clauses/repeated text not updated | false | Intent asks correctly extracted person/asset records and original-template export, not rewriting arbitrary clauses. Exact explicitly confirmed occurrences preserve other text by frozen constraints. |
| Intent 4, real Electron end-to-end not exercised | maybe-false | Python services and DOM doubles pass, but picker-to-file runtime integration remains unexecuted. Medium unverified; defer isolated Electron flow verification, disclose limit. |
| Intent 5, two-party end-to-end absent | medium | Fixture saves transfer document into inheritance case; seat-only test does not exercise saved two-party import/export. bad_plan: add genuine two-party service/adapter lifecycle test. |
| Intent 6, shared regex ownership matches | false | Positive alignment observation; source imports the existing runner and changes profile there. No second engine or defect. |

Grouping after individual verdicts: land-row identity (Blind1/10, Edge1);
cell review (Blind2, Edge2); date normalization (Blind3, Edge3); proposal eligibility
(Blind4); persisted binding selection/clear (Blind5/6); source lifecycle/labels
(Blind7/8/11); transactional slot validation (Blind9); mixed formatting (Edge4);
missing original-path verification (Gap1/2, Intent5); destination response (Gap other).
All verified groups are this change's responsibility. Three unverified intent
observations are deferred separately; false observations rejected with evidence.

## Review re-derivation instructions — iteration 1

Root reverted only the DOCX delta in the working tree using the saved patch;
the previous committed attempt remains recoverable at 90331ab3abf410cc87a6b49406fdbca463b57bbc.
Re-apply `.agent/scratch/docx-integration-review.diff` as the KEEP starting material,
then implement the amended requirements below. Do not restart/render the workflow,
spawn children, or ask approval: root handles those steps. Exactly one coding executor.
Do not edit this plan's frozen content or existing triage rows; update execution
evidence and only your scoped source/spec/test/task files before local commit.

Amend non-frozen code map and acceptance to preserve land-row identity alongside
candidate/row binding (additive documented context if needed); track review per
ambiguous land cell; normalize selected dates using existing formats; prevent
unusable catalog bindings and validate new binding slots in the Stage transaction
against the composed saved rows/seats. Display saved bindings and allow clear.
Check source capacity before Stage mutation, expose explicit source detach, and
persist/display a safe backend-produced source label. Source detach must not read
corrupt files. Reject mixed-format exact occurrences visibly; no silent first-run
style collapse. Keep data.destination equal to the selected parent folder.

Tests must demonstrate deletion of earlier land rows, unresolved other cells,
raw selected dates, empty slots, save/reopen/clear, eight-plus-one sources,
corrupt-source detach, wrong-slot rollback, mixed-style rejection/preservation,
dirty model export, stale adapter export/no output, subfolder response, and a
complete saved two-party DOCX lifecycle. Do not write tests merely mirroring code.

KEEP: shared regex ownership; ordered physical XML/Unicode/evidence; original
bytes and unrelated ZIP parts; backend opaque source storage; transactional
Stage/revision and stable row IDs; exact occurrence-only export; existing two
Upload tabs and Intake UI; all prior MIN-141, Word and timeline commits. Keep
successful synthetic coverage and add genuine negative cases rather than relaxing
assertions. No office files, secrets, external actions or new DB technology.

Review change log 2026-10-04: defects above exposed array-index ownership and
field-level review shortcuts. Re-derive this DOCX delta against its baseline with
the explicit guards/tests above; retain all working behavior in KEEP. Existing
timeline/Word phases and unrelated root records stay untouched.

## Verification

Isolated temporary DB/source corpus in scratch. Assert record identity and field
ownership, genuine Stage reload/transaction/stale conflicts, hash invalidation,
original-file hashes and untouched package XML, UI review/accept/mapping behavior.
Existing MIN-141/Word focused regression and contract examples must remain passing.

## Initial executor evidence — 2026-10-04 (historical; superseded by final checks)

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

## Final iteration 3 verification — 2026-10-04

Commit 0f09d506: 24 DOCX Python tests, 353 backend regressions (2 file-symlink
skipped), 109 adapter/shared-core and 6 Intake tests, 226 Node tests, and
78 contract examples with zero unexpected outcomes. Root independently reran
all 24 DOCX Python tests: passed, with existing SQLite datetime and local cache
permission warnings. Root real Electron flow HS-6 passed: four editable review
records, 25 original binding choices, Stage save/reload and original-template
export. Original source, untouched ZIP parts and workspace DB hashes unchanged.
Native picker used a test double; native dialog, actual Word page layout, office
corpus, clean installation and joint DB/source recovery remain unverified.

### Frozen matrix audit

| Matrix row | Executed covering verification |
|---|---|
| Ordered DOCX | physical_merged_nested_tables_unicode_and_repeated_occurrences; nested_fields_across_paragraphs |
| Records | labeled_group_ownership_and_raw_refs; asset_heading_before_parties; Electron HS-6 four records |
| Uncertainty | ambiguity_retains_all_evidence; Node each ambiguous land cell and invalid date corrections |
| Stage capacity | Node capacity retains cards and visible review card rejection |
| Persistence | end_to_end_review_commit_reload; context_new_session_invalid_binding_rollback; Electron HS-6 |
| Template | original_preservation_and_edit; mixed_styles_rejected; unsupported_hyperlink; Electron ZIP comparison |
| Changed file/order | extraction_integrity tamper/missing checksum; two_party_mapping saved seats; land_deletion_does_not_rebind |
| Cancel/switch case | original_export_cancel_after_temp_write; Node case-switch and old-export stale tests |

All covering tests above ran and passed; no skipped DOCX matrix coverage.

## Iteration 4 executor and root verification — 2026-10-04

35 DOCX Python and 20 DOCX Node passed; broad checks 386 backend+2 file-symlink
skipped,229 Node,115 adapter/Intake/shared-core,78 contract examples no unexpected
outcomes. Signed scalar/land source corrected through saved Stage/bindings and
actual export, JSON download validated using real Intake schema. Root isolated
Electron HS-7 ok:true: four records,25 choices,save/reload/original export; source,
untouched ZIP parts and workspace database unchanged. Native picker double only;
previous corpus/page/clean-install/recovery limitations remain.

## Iteration5 final executor and root evidence — 2026-10-04

Commit3ef8d1f917fcdaffd3d8e1fdfd83479eedd0647e;44DOCX Python within397backend
pass/2file-symlink-skip,115adapter/Intake/core,233Node incl24DOCX,78contract examples
zero unexpected,7local links,whitespace pass. Text-limit mutation test failed
when guard was disabled and adapter restored exactly. Actual empty-land export
preserves removed source text without rebinding. Root real isolated Electron
HS-8 passed4records/25bindings/save/reload/export, original source/ZIP parts/DB
unchanged. Native picker double and prior corpus/page/install/recovery bounds stay.

## Root final post-patch verification — 2026-10-04

413 backend passed,2file-symlink skips (Windows privilege),115adapter/Intake/core,
235Node,78examples no unexpected,links/whitespace passed.60DOCX tests ran.
Electron HS-9 successful4records/25bindings/save/reload/original export with
source/untouchedZIP/DB unchanged. Review6 all4collected, patches resolved;
no surviving intent_gap/bad_plan. Deferred corpus/native picker/page/install/
recovery and pre-existing batch reanalysis remain explicitly bounded.
