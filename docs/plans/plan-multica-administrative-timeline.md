---
title: 'NAIA-9: Bando source and extendable administrative timeline'
type: feature
ticket: 'NAIA-9'
created: '2026-10-04'
status: built
route: full
route_source: auto
review: thorough
review_source: auto
lenses_ran: [blind-hunter, edge-case-hunter, verification-gap, intent-alignment]
review_loop_iteration: 2
baseline_revision: a32c1fe6f69259097a32115ca60acc30374be2f3
context: ['AGENTS.md', 'docs/spec/notary_v2/README.md', 'docs/archive/linear-tasks/NAIA-9-decisions.md']
---

<frozen-after-approval reason="Owner explicitly requests timeline storage and Bando data">

## Intent

Take the public Bando website data and create the project's source of truth for
administrative-unit name timelines. Bando supplies the latest predecessor→current
transition only. Owner will supply earlier transitions later; do not research or
invent them now. Design storage that can add A→B→C→D for commune, district and
province, and accommodate merges/splits rather than incorrectly assuming1→1.
Owner selects Bando as canonical latest commune/province names in chat04/10/2026.
This is the next implementation phase, before broader address UI and DOCX intake.

## Boundaries & Constraints

No fabricated dates, old codes, old province/district parents, or historical
identity. Preserve exact source names/prose and retrieval time, independent from
effective date. Unknown date remains null/pending; do not date every current unit
01/07/2025 because Bando also contains2026 changes. No customer data or lookup
requests to public service; fetch only public full catalog/table. Existing office
DB unchanged. No automatic historical NQ expansion; Owner will curate older events.
Do not merge same-name units without identity evidence. Support district records
and events in schema even though Bando supplies no district catalog. Preserve all
Word/MIN-141 behavior; do not change address UI or DOCX implementation yet.
No push/PR/external task messages/Multica worktree writes.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected | Error |
|---|---|---|---|
| Bando catalog |3355 rows,34 province3321 commune | exact current names/codes/parents+source snapshot | reject malformed/corrupt response |
| Latest old names | free prose/partial territory/district parentheses | lossless evidence plus conservative pending references | unparsed text visible, never discarded |
| Unknown identity | same old name, no old code/parent | separate unresolved mentions/candidates | never conflate solely by name |
| Old timeline later | Owner addsA→B→C→D, dated source | add units/name periods/events without rewriting latest evidence | reject invalid refs/date contradiction |
| Merge/split | A+B→C, A→B+C | event has several input/output references and partial notes | no forced one-to-one |
| Rename | same stable unit changes name | name versions associated with event/valid period | not a fresh unrelated unit by default |
| Missing date | source has no effective date | pending/undated; no confident date lookup | retrieved date never event date |
| District | manual county add/abolition/reparent | same structure level=district | source Bando coverage remains0 district |
| Refresh | unchanged/new/failed snapshot | idempotent, preserve manually curated history, atomic update | never truncate existing source/history |
| Validation | cycle/dangling/overlap/code reuse | meaningful report; reject impossible confirmed timeline | ambiguity stays pending |

</frozen-after-approval>

## Code Map

Read `.agent/scratch/multica-address-research/bando-api-research.md` fully when
present; raw Bando catalog and NinhBinh tables in same scratch folder. Root
independently POSTed `/p.co_dvhc` body `ma=0`, HTTP200,3355 rows. This is the
site's public read endpoint; no public integration/version contract established.
Table endpoint `/p.co_bangbieu` accepts province layer ID and generates client
Excel; keep its raw evidence/citation when used. No need to install Excel/UI tools.

Choose a cohesive runtime-owned folder, e.g. `notary_v2/data/administrative_units/`
for local curated ledger and source snapshots. Define machine-readable schema
under `contracts/administrative-timeline/` and a feature spec at
`docs/spec/notary_v2/administrative-timeline.md`; link from module README. No
parallel architecture/design files. Ledger is the data SOT; spec explains meaning.

- Unit identity: stable internal ID independent of name; level commune/district/
  province; optional official code assertions with source/validity; name and parent
  versions. Current Bando units can receive deterministic initial IDs, but future
  official-code reuse must not force identity. Support rename on same ID.
- Events: stable ID, type(rename/merge/split/reparent/abolish/reported_transition),
  multiple from/to references, effective_on nullable, optional valid interval,
  verification state and source evidence; partial territorial notes preserved.
- Old mentions lacking identity are unresolved references, separate from verified
  units. Store raw phrase and source-row key. Conservative extraction may offer
  candidate names; it must not promote them to verified code/province identity.
- Sources: URL/protocol/retrieved_at/hash/provider/raw immutable snapshot and row
  evidence. Keep current-source names exactly, record updates instead of deleting
  older curated names. Include dataset version and coverage/report.
- Small standard-library import/validate/update/query CLI script(s) and reusable
  ledger helpers. Offline input option for reproducibility; public refresh optional.
  Manual update consumes structured JSON with explicit source/status, validates
  before atomic write, preserves unrelated history. No new DB technology.

## Tasks & Acceptance

- [x] Fetch and retain public full Bando dataset and provenance, conservative latest
  relationships/pending references, unparsed/partial report. Counts34/3321 verified.
- [x] Machine-readable schema and cohesive ledger model supports all3 levels,
  repeated changes, stable identities, rename/merge/split/abolition and unknown dates.
- [x] Reproducible idempotent importer and safe manual update/validation/query path;
  never overwrite existing Owner history on source refresh.
- [x] Synthetic labeled tests A→B→C→D, merge/split, district/province, pending date,
  same-name unrelated units, code reuse, malformed/dangling/conflicting history,
  failed refresh and manual changes retained; no tests that merely mirror trivial code.
- [x] Feature spec in concise Vietnamese: why, exact Owner authority, storage
  explanation/example, how Owner later adds dates/history, Bando API and coverage,
  unresolved data limitations. Parent links and task progress/handoff aligned.
- [x] Focused relevant tests/schema + full-data validation, Markdown links/diffcheck,
  local commit only this scope. Report actual counts and sample timelines pending.

## Implementation Notes

Exactly one coding executor, after Word executor finishes; root supplies baseline.
Do not ask generic plan approval: latest human explicitly asks to create storage.
Start with a local versioned JSON ledger and atomic files, no unnecessary service
or product UI. Retrieval date is04/10/2026; source events with unknown dates must
remain unknown. Data source may omit meaningful history: preserving uncertainty
is part of successful implementation. Human can later resolve pending old IDs.

## Plan Change Log

- 04/10/2026 — Owner requests explicit documentation for future growth. The feature
  spec must explain stable identity versus changing names/codes, multi-input/output
  events, unresolved dates and old mentions, adding earlier history with the actual
  CLI, refresh preservation, and later district coverage. Include examples matching
  the schema. Describe larger-data indexing/storage migration as a future option,
  distinct from the implemented JSON ledger; consumers read the local dataset and
  do not fetch Bando on each lookup. This expands documentation, not infrastructure.

- 04/10/2026 — Review loop 1: re-derive the affected validator/query/snapshot paths
  with the constraints below. KEEP all 35 raw snapshots, original dataset hashes,
  current 3355 unit IDs/observations, manual update semantics, conservative pending
  imports, and the Owner-requested scale documentation. Preserve completed work as
  requested by Owner; amend the existing implementation rather than discard data
  or other takeover work. Pending relationships cannot carry confirmed history
  across identities; resolved mentions can expose pending evidence without turning
  it into confirmed history. Confirmed parent periods must respect the parent's end
  date; reject conflicting whole consumption or rename/abolition on the same day.
  A merge output is not automatically a new unit: formation must have explicit
  source evidence, since an existing unit may receive territory. Validate exact
  ISO dates, province headers, snapshot paths and schema patterns. Write raw
  snapshots atomically. Cover locks/current-observation filtering with tests.

- 04/10/2026 — Review loop 2: distinguish confirmed partial territorial movements
  from whole-unit succession for cycle/date validation. Partial movements may run
  in both directions at different dates without destroying either identity.
  Reject a confirmed name period spanning a sourced confirmed rename date, even
  if its event_id is null. A confirmed whole reported_transition must apply the
  same lifecycle/end rules when an input identity is absent from outputs; pending
  raw Bando evidence stays pending. Reject source-key reuse across levels. Guard
  non-object patch input and missing stored ledgers (initial import may explicitly
  initialize a new folder). Add immutable compressed previous-ledger revisions
  before manual curation changes so corrections retain the prior records; archive
  failure aborts the update, and archives are recovery evidence, not a second SOT.
  Document CLI name-only query coverage, fixed source-count baseline revalidation,
  lock recovery process identification, independent assertion/event confidence,
  and long-graph future limits. Keep all existing raw/current dataset bytes and IDs.
  Add default-strict full import/rejection, exact-date boundary and actual CLI
  subprocess tests. Do not expand into UI, historical research or a new database.

## Review Triage Log

| Finding | Verdict | Evidence and route |
|---|---|---|
| Blind 1: ended parent | medium | Ending checks inspect unit_id but not parent_id; a confirmed child relationship can outlive its parent. bad_plan. |
| Blind 2: activity before merge output creation | false | A merge output is not asserted newly created; an existing identity can receive territory. The model has no sourced formation assertion, so deriving birth from output would invent a constraint. Clarify this limit in docs. |
| Blind 3: same-day whole consumption | medium | End validation only checks dates strictly greater than end, accepting two conflicting whole-consumption events on the same day. bad_plan. |
| Blind 4: pending edges transmit confirmed history | medium | query builds connected IDs from every event before status filtering; unrelated confirmed history crosses unverified edges. bad_plan. |
| Blind 5: resolved mention absent from query | medium | query uses only refs kind=unit and never resolves mention IDs. Confirmed mention identity is lost to the pending-evidence consumer. bad_plan. |
| Blind 6: compact query date | medium | _day uses date.fromisoformat which accepts YYYYMMDD, then query compares the original string. Wrong period can match. bad_plan. |
| Blind 7: inconsistent province header | medium | Import checks header.ma only, unlike all required commune fields; inconsistent province details enter the ledger. bad_plan. |
| Blind 8: interrupted raw write | medium | target.write_bytes writes final hash path directly; incomplete bytes cause collision on retry. bad_plan. |
| Blind 9: empty snapshot path | low | Path('').parts is empty; indexed access raises IndexError instead of LedgerError. Direct correction, patch. |
| Blind 10: schema patterns | medium | JSON Schema pattern is substring matching, while helper uses fullmatch; unanchored patterns give conflicting validation outcomes. bad_plan. |
| Edge 1: parent end | medium | Same verified missing parent_id end guard as Blind 1. bad_plan group. |
| Edge 2: same-day rename/abolition | medium | The strict > comparison permits a rename on the day the identity ends; distinct conflicting events need rejection. bad_plan group with Blind 3. |
| Edge 3: province header | medium | Same header-field gap as Blind 7. bad_plan group. |
| Edge 4: maximum open-ended date | low | The artificial upper sentinel 9999-12-31 excludes that legal date. Direct None-aware bound correction, patch. |
| Edge 5: empty path | low | Same IndexError as Blind 9. patch group. |
| Gap 1: lock test | medium | Pre-verified missing meaningful test for exclusive lock across both writers. patch. |
| Gap 2: current observation test | medium | Pre-verified refresh test lacks query assertion on dataset_version filtering. patch. |
| Intent: source evidence versus resolved histories | false | The approved matrix explicitly preserves unresolved names and dates; Owner supplies history later. No claim of current historical lookup or UI completion is made. No defect. |
| Loop 2 Blind 1: partial reciprocal movements | medium | Graph includes every confirmed event, so partial territory transfers create false successor cycles. bad_plan. |
| Loop 2 Blind 2: rename contradicts unlinked name period | medium | Date checks depend on event_id, leaving confirmed name periods spanning a confirmed rename unexamined. bad_plan. |
| Loop 2 Blind 3: whole reported transition does not end input | medium | Ending logic covers merge/split/abolish only, so generic confirmed whole transition leaves input identity active indefinitely. bad_plan. |
| Loop 2 Blind 4: old curator record overwritten | medium | Upsert replaces a same-ID curator record without retaining the previous version. Preserve previous revisions for corrections. bad_plan. |
| Loop 2 Blind 5: source-key level reuse | medium | Existing source_key keeps ID/level without checking new catalog level, permitting province evidence on a commune observation or vice versa. patch. |
| Loop 2 Blind 6: fixed full-source counts | low | Rejection is intentionally conservative rather than silent corruption; future baseline changes need documented complete-source verification. Direct documentation correction, patch. |
| Loop 2 Blind 7: missing ledger reports valid empty | medium | read_ledger silently initializes absent files for every caller, including validate/query. Separate explicit initial import from existing-store reads. patch. |
| Loop 2 Blind 8: patch null/type | low | set(patch) precedes object validation and raises TypeError for null. Direct input check, patch. |
| Loop 2 Blind 9: query omits codes/parents | low | This phase's query is name history, not complete dated-address resolution. Clarify its exact coverage in docs; no new API needed. patch. |
| Loop 2 Blind 10: empty lock recovery evidence | low | Docs needs concrete process-identification steps before removing a stale lock. Current runtime is CLI-only; improve recovery guidance without automatic deletion. patch. |
| Loop 2 Edge 1: confirmed assertion linked to pending event | false | Assertion has its own source/status/date and can be confirmed while predecessor identity remains unresolved. Query still does not promote the event or traverse pending history. Document independent confidence. |
| Loop 2 Edge 2: graph recursion over 1000 successors | low | Valid extreme-depth input could exceed Python recursion, but ordinary administrative history has far shorter succession depth; reject algorithm expansion now and document future iterative traversal/indexing. |
| Loop 2 Gap 1: strict full-import automated coverage | medium | Pre-verified all importer tests bypass strict default; actual root/coder full import exists but meaningful regression tests are missing. patch. |
| Loop 2 Gap 2: exact rename boundary | medium | Pre-verified no assertion distinguishes < from <= valid_to at the change date. patch. |
| Loop 2 Gap 3: actual CLI query | medium | Pre-verified named CLI test only calls helpers, so argument-forwarding errors survive. Add subprocess coverage. patch. |
| Loop 2 Intent: unresolved data/runtime scope | false | Same intentionally conservative evidence-only import as the approved matrix; actual UI integration remains a separate queued phase. |
| Loop 3 Blind 1: task link depth | false | Task lives at .agent/tasks/NAIA-9; ../../../ reaches repo root. Root resolved all three links successfully. Reviewer added an incorrect extra parent. |
| Loop 3 Blind 2: continuing identities in successor graph | medium | Graph adds edges from incoming IDs also present in outgoing, falsely treating continuing identities as consumed successors. Direct incoming-minus-outgoing correction, patch. |
| Loop 3 Blind 3: reparent spans old relationship | medium | Rename guard covers names only; equivalent parent period guard is missing at a confirmed reparent. Direct correction, patch. |
| Loop 3 Blind 4: partial abolition | medium | Abolish ends the whole identity regardless of territory=partial. Reject contradictory confirmed input directly, patch. |
| Loop 3 Blind 5: unknown territory treated as whole graph | medium | Graph uses !=partial whereas endings use ==whole. Keep unknown out of confirmed whole-succession checks, patch. |
| Loop 3 Blind 6: CLI query ignores source files | medium | CLI calls query without folder-backed snapshot validation although snapshots are required evidence. Direct validate(ledger,folder) before query, patch. |
| Loop 3 Blind 7: duplicate IDs inside patch | low | Sequential upsert last-wins hides duplicate entries in owner input. Direct reject repeated IDs before replacing, patch. |
| Loop 3 Blind 8: curator record citing Bando is immutable | medium | Protection currently keys off any Bando evidence, locking separate curator corrections. Distinguish importer-owned records from curated rows without altering existing schema, patch. |
| Loop 3 Blind 9: confirmed reported_transition without destination | medium | It acts like abolition despite its type; require both sides for confirmed reported_transition, patch. |
| Loop 3 Blind 10: manual counterfeit Bando observations | medium | Update can add observations claiming current Bando dataset with arbitrary row keys. Restrict importer-owned observations and reserved source-record namespace in manual upsert; curated conclusions use separate records. patch. |
| Loop 3 Edge 1: reparent | medium | Same verified parent-period guard gap as Blind 3. patch group. |
| Loop 3 Edge 2: same-day partial transfer and ending | maybe-false | A coordinated partial transfer followed by abolition in the same effective act can be valid; storage has no intra-day ordering or legal act grouping. Do not reject all same-day partial transitions; require future sourced curation of coordinated act semantics. defer, medium unverified. |
| Loop 3 Edge 3: CLI query snapshot | medium | Same source-file validation gap as Blind 6. patch group. |
| Loop 3 Gap: public refresh request path | medium | Pre-verified test gap covers actual POST arguments and failure-before-write. Add deterministic HTTP response fixture against main/fetch_public, preserving old ledger on failure. patch. |
| Loop 3 Intent: evidence versus resolved relations | false | Carried: conservative pending source mentions match the approved matrix and Owner-supplied later history; no historical/UI completion claim. |

## Verification

Real public HTTP sample+full response counts/hashes; schema and invariant validator
over entire ledger; labeled synthetic multi-step/split/rename/level fixtures;
idempotent refresh and manual preservation/atomic failure tests. Query output must
show pending evidence separately from verified chronological events. Original
office DB/source documents untouched. Link and whitespace check before commit.

Root final 04/10: 79 timeline tests + 5 docs checks passed, 1 pre-existing docs
skip. Full ledger validate: 3355 units/3219 pending events; all effective dates
unknown. Root resolved 28 module/feature links; implementer resolved 49 related
links. Public download wiring now tested against deterministic local HTTP,
including failed table request preserving the old store. JSON example and CLI
update/query date boundaries executed. Data snapshots/IDs unchanged across fixes.
Commits b82450d, a57408f, 14cae28, a3b33dc. Actual old history, resolved multi-name
predecessors and application consumers are deliberately not claimed complete.
