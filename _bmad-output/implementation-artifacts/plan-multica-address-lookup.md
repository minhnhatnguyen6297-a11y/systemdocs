---
title: 'NAIA-9/14-21: Bando administrative-address lookup'
type: feature
ticket: 'NAIA-9'
created: '2026-10-04'
status: in-review
route: full
route_source: auto
review: thorough
review_source: auto
lenses_ran: []
review_loop_iteration: 0
baseline_revision: 4665e65c56f96a4fc00d2a51c4707b6c588da7ef
context: ['AGENTS.md', 'docs/spec/notary_v2/README.md', 'docs/spec/notary_v2/administrative-timeline.md', '_bmad-output/archive/linear-tasks/NAIA-9-decisions.md']
---

<frozen-after-approval reason="Owner requests all Multica tasks and confirms Bando SOT/date rule">

## Intent

Finish NAIA-9 and children14-21: versioned local administrative-unit data,
old/new address parser and lookup, human-applied suggestions for person/land
addresses, posting place and death-certificate issuer. Bando website is the
owner-selected source of truth for current commune/province names and their
immediate predecessors. Owner specifically asks to inspect its API/bulk downloads.
Older historical relations may come from cited official resolutions; current
destination names must agree with Bando. No new district or village is invented.

## Boundaries & Constraints

Owner source comments NAIA-9 `01a0fd70-3664-7a6a-a564-9f198c3b62d3` and
`01a0fd8d-1bb9-7173-8454-17b0cf816919`,02/10/2026; chat answers03/10 and04/10.
Posting target date is case creation date; source-document date selects source
address format. Person identity date, death-certificate date and land-certificate
date are independent. Missing/split/uncertain lookup requires review, never first
match. Suggestions run after input but apply only by button, always remain editable.
Person/land original address is retained with `(nay là ...)`; posting place is
replaced only on acceptance. No guessed new village/district. Death issuer remains
independent from posting or residence; confirmed manual value never auto-overwritten.
No customer address sent to external website: runtime lookup is local. No push/PR,
external task messages, original DB/source-worktree changes. Preserve MIN-141,
Word8/12 and DOCX intake integration. Do not fabricate effective dates/history.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected | Error |
|---|---|---|---|
| Old address | before01/07/2025, commas/hyphens/prefix/no prefix | parse right-to-left province/district/commune, preserve hamlet | no guessing if ambiguous |
| New address | since01/07/2025 | province/commune, no required district | missing/syntax date invalid_input |
| Unique | exact evidenced commune, source province | final matching destination + source/version | unsupported historical interval explicit |
| Split | Gia Tân or A→B/C→Y/T | every eligible destination, user chooses | never auto-select |
| Multi-step | A→C→E with dated official relations | traverse eligible edges, trace intermediate provenance | reject cycles/conflicts/orphan evidence |
| Duplicate names | >1 old unit, district unavailable Bando | only use corroborated discriminator; otherwise ambiguity | district not guessed |
| Source refresh | HTTP error/malformed/count loss | keep prior valid local snapshot, report failure | atomic refresh, no partial overwrite |
| Posting | land address+its date, case creation date | chosen commune stored through update_meta | missing case date, stale guard |
| Issuer | explicit death-issuer address+death-doc issue date | suggested historical/current UBND, manual apply | do not use residence/posting as issuer |
| Apply address | user approves result | original exact text + new commune/province | no duplicate nay-là suffix |
| Input race | address/date/row/case changes before response | discard stale suggestion | no previous case leak |

</frozen-after-approval>

## Code Map

Read full `.agent/scratch/multica-address-research/bando-api-research.md` once
research finishes; `research.md`, raw Bando and NSO checks are corroborating input.
Confirmed root request POST `https://sapnhap.bando.com.vn/p.co_dvhc`, body `ma=0`,
HTTP200,3355 rows including34 provinces/3321 communes; fields ma,ten,magoc,malk,
truocsapnhap. The predecessor field is prose, not a normalized legal-history table.
Preserve the full phrase and evidence; only conservative parsed names become edges.

- New cohesive address-lookup service under notary_v2/services; isolated parser
  and explicit local loader consume the existing administrative timeline ledger.
  Reuse notary_v2/administrative_timeline.py and its schema; do not create another
  data SOT or refresh script. Shared service is callable by Intake and Workspace.
  Load/validate once per ledger version and build rebuildable search/event indexes,
  not a full ledger scan per keystroke. Exact file names follow existing style.
  Cache identity includes dataset_version and revision/content signature: manual
  history updates can increase revision without changing Bando dataset_version.
  Detect changed ledger and validate before replacing cache; return actual loaded
  version/revision. Failed reload reports failure/old version explicitly, never
  presents an old result as from the new ledger. Test a manual-history update
  with the same dataset_version.
- Existing ledger refresh owns version/hash/URL/retrieval time and preserves raw
  observations/history. Runtime search can offer conservative predecessor names
  backed by row evidence, but parsing prose must not promote identity, parent or
  date into confirmed history. Keep partial/split uncertainty. Never hardcode all
  current units effective2025 when Bando includes2026 updates. Only confirmed
  sourced dates permit historical answers; Owner supplies older events later.
  Predecessor strings parsed from observations are rebuildable search indexes
  pointing back to observation/source row IDs, not new historical unit identities
  or confirmed transitions. Runtime never mutates ledger names/parents/events.
  Keep this distinction explicit in the consumer spec and returned coverage.
- IPC registry, real/mock adapter, command/result schema and validator examples:
  documented source_date/target_date, address or explicit province/commune, statuses
  match/ambiguous/not_found/invalid_input plus candidates/provenance/coverage.
- Package asset staging must include the existing `administrative_timeline.py`,
  its exact ledger/snapshots and `contracts/administrative-timeline` schema at
  the relative paths the loader validates. Current notary allowlist only stages
  database.py/models.py and services/routers/templates, so importing the helper
  from dev source is insufficient. Add narrow allowlist entries for public
  administrative reference data only; keep office databases/configuration,
  curator temp locks and revision archives out of the installed package. Verify
  lookup from an isolated staged tree without falling back to this checkout.
- case-drafting-model/view: reusable debounced suggestion helper for person and land
  address; source date from that row only, case date target; keep direct edits.
- word-export-dialog: posting suggestion from chosen land address and case date,
  use integrated update_meta save/revision guards. Multiple properties need explicit
  choice; no hidden first asset. Lookup does not itself save anything.
- Death issuer suggestion in people review/edit: use explicit issuer source or
  recognizable entered UBND address, never person's residence. Living-person card
  issuer derivation stays the MIN-141 date rule; do not apply commune logic to it.
- Feature spec `docs/spec/notary_v2/administrative-address.md` if absent, link parent
  README; smallest-level Word/input references and contracts explain shared behavior.

## Tasks & Acceptance

- [ ] Reproducible Bando snapshot and conservative source-backed relations; scope/
  version/history limits visible. Keep all partial split edges; validate datasets.
- [ ] Pure parser/lookup/dated graph with real-source and synthetic chain fixtures.
- [ ] Contract/IPC/adapter/mock wiring, local-only runtime (no customer HTTP).
- [ ] Automatic background suggestions, focus/hover accessible display, explicit
  apply/choose/ignore for person/land addresses and posting; preserve original/manual.
- [ ] Separate death-issuer date/source suggestion and living-person regression.
- [ ] Meaningful tests for before/at date boundary, Unicode/case/prefix variants,
  all6 NinhBinh splits, ownerLâm/ÝYên andYênDương/VũDương, no-suffix duplication,
  late responses, case-switch, missing/split/manual fields, stale atomic persistence.
- [ ] Align docs and NAIA9/14-21 execution record: why, owner contract, sources,
  Bando API protocol, actual dataset coverage, update and failure instructions.
- [ ] Focused backend/renderer/IPC/schema integration and appropriate current Word/
  DOCX regressions. Link/diff checks; local scope commit, no external status writes.

## Implementation Notes

Root owns docs/spec/notary_v2/administrative-address.md and related module/
Stage/Word/input/timeline spec links, plus NAIA9/14-21 execution records.
Coder owns product source, contract prose/schema and tests only, sending actual
service/command/result/UI details to root for documentation. Do not edit root
spec/task files concurrently. Root completes docs before matrix/review.

UI guidance: root used ui-ux-pro-max local UX queries for keyboard focus and
inline validation. Keep visible focus ring; never rely on hover alone, hide
focused controls, or move focus on every input change. Every suggestion action
is a real labeled button; loading/error/coverage messages stay beside its field,
aria-describedby/live feedback when relevant. Existing Electron vanilla JS/CSS
is the detected stack; preserve current visual tokens, no new page/design SOT.
Read current shared UI README before modifying CSS. Root handles final UI check.

Existing checks use
`C:/Users/MINH/.codex/worktrees/1aae/systemdocs/.agent/scratch/multica-intake/schema-venv/Scripts/python.exe`
(jsonschema available), notary regression cwd `notary_v2`, and
`NODE_PATH=D:/systemdocs/shell/node_modules`. No dependency install needed.
Scratch basetemp must be a fresh path under `.agent/scratch/`; do not reuse
another test process's temporary directory. Root Electron harness uses the
existing D:/systemdocs notary Python for Playwright and isolated copied engine.

Use the actual editable field `caseInfo.ngay_lap_ho_so` as the posting/address
target date; never substitute created_at, today or document issue date. A year
alone is insufficient for a dated lookup. Death-certificate issuer describes
the office named on that certificate at its issue date: its target date is the
person's `ngay_cap`, independently of the case date. An undated current-source
candidate cannot be presented as proof of that historical issuer. Keep the
explicit entered issuer and show missing historical coverage when necessary.
Person/land source date is that row's document date. Pending Bando rows may
support labeled current-catalog candidates, never a guaranteed historical result.
The 01/07/2025 rule controls expected address format, not effective dates for
every ledger transition. No confirmed manual value is changed by background lookup.

Sequential coding executor after Word and DOCX commits. Root supplies final
baseline then reviews. API endpoint is publicly used by the site, not necessarily
a documented supported third-party API; cache version locally and fail visibly.
NSO historical district metadata is auxiliary only when independently matched;
do not imply Bando provides it. If old province ownership cannot be proven from
Bando prose/official auxiliary source, return ambiguity rather than guessing.

## Plan Change Log

04/10/2026 Owner explicitly requests timeline SOT first and will supply earlier
events later. Execute after timeline ledger implementation, consume that ledger
rather than a second address dataset. Do not research/import older NQ history now.
Date lookup requires confirmed dated events; undated latest Bando suggestions must
be labeled current-source candidates, never asserted valid at an arbitrary past
case date. Preserve previous exact-address, manual application and issuer boundaries.

## Review Triage Log

## Verification

Use separate assertions for (a) real undated Bando candidates and (b) synthetic
confirmed dated history. The former must return insufficient dated coverage,
including case dates before catalog retrieval, even when the name match is unique.
The latter must prove 30/06 versus 01/07 boundary traversal and A→B→C/splits.
Never make a test fixture date become production effective_on for Bando rows.
Actual UI checks must edit each source/date after a response is pending, switch
cases, and preserve an already entered issuer/posting address until explicit apply.
Use synthetic documents and isolated DB/code copies for Electron runs; never
start legacy backend imports against office or current source-worktree databases.

Source-count/hash/duplicates/cycle/orphan/effective-date validation and live public
API sample; labeled real cases and synthetic chain/split boundary tests; actual
renderer interactions with IPC doubles and isolated backend temporary DB; saved
field/snapshot reload/stale checks. Preserve original address exact bytes and
explicitly distinguish current-catalog coverage from historical lookup coverage.
