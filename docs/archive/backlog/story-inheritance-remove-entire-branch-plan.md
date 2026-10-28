---
title: 'Remove the entire inheritance branch after impact warning'
type: feature
ticket: 21B
created: '2026-10-17'
status: built
baseline_revision: 'a37a591ec86230a037e5ac5a226e28f6bde94164'
route: full
route_source: auto
risk: high
review: quick
review_source: pinned
lenses_ran: []
review_loop_iteration: 0
context:
  - D:/systemdocs/AGENTS.md
  - D:/systemdocs/_bmad-output/specs/notary_v2/diagram-rules.md
  - D:/systemdocs/_bmad-output/decisions/decision-owner-inheritance-remove-entire-branch-20261017.md
---

<frozen-after-approval reason="owner-selected intent; standing waiver removes individual owner plan approval">

## Intent

Owner, **17/10/2026**, exactly: **“B - gỡ cả nhánh”**. For A→B→C, B↔S, C parents `[B,S]`, ×B removes B, C and all active recursive parent-edge descendants, despite C having another parent. S stays unless independently a parent-edge descendant. This is not option C (preserve an empty B slot).

Warn with actual affected nodes/relations before changing anything. Confirm one draft mutation, then existing evaluate; explicit Save persists through existing atomic/revision guards.

## Boundaries & Constraints

**Always:** Stage people/assets, IDs, order and values unchanged; Pool derives from active assignments. Keep deleted nodes in canonical Node v3 with IDs/personId/position marks/hidden intact. Clear removed nodes' outgoing parent/spouse links and every incoming reference, including on old tombstones. Preserve unrelated graph/roles/asset positions. Include empty/hidden active descendants. No spouse traversal, reparenting, renumbering or automatic save.

**Never:** new persistence/API/schema; inheritance formula fixes; redesign requiredSlots/default-slot behavior; change ordinary unassign or two-party slots; touch #19/#20/Office/#18, foreign changes, `.agent/`, docs outside this scope or dist-app. No Autoresearch, agent spawning, commit or push without parent authorization.

## I/O & Edge-Case Matrix

| Scenario | Expected behavior |
|---|---|
| Multi-level/shared-parent graph | Remove root + every active descendant; spouses/unrelated branches remain. |
| Empty/hidden slots, old tombstone references | Include active empty descendants; clear affected links on all nodes; no resurrection/ID reuse. |
| Hủy/Escape/close/backdrop | No draft/dirty/revision change, evaluate or save caused by removal. |
| Confirm | Exactly one draft notification/mutation, then normal evaluate; warning lists all affected nodes/relations. |
| Graph/session changes during warning | Do not apply stale impact; refresh warning or close without mutation. |
| Save success/failure | Fresh reopen equals saved canonical; invalid/conflict/locked/error retains old DB snapshot and draft under existing guards. |

</frozen-after-approval>

## Code Map

Graphify report communities 82/247 located the flow before source inspection.

- `shell/src/renderer/notary/case-drafting-model.js`: `removeNode` currently tombstones one node and clears only live incoming links. Add one read-only impact calculation reused by confirmation and mutation; `findNode`, `touchDiagram`, `pool`, `saveDiagram`, `openCase` provide existing guards/canonical flow. Prefer an active parent→children index and visited set, not recursive mutation. Relationship cleanup includes deleted nodes. One `touchDiagram` after the complete cutover; two-party no-op.
- `shell/src/renderer/notary/relationship-diagram.js`: `inheritanceCardEl` × currently calls removeNode directly; add canonical impact modal through injected `openModal`. `personRow`/slot labels identify real nodes, including empty slots; list deduplicated spouse pairs and parent edges actually cleared, including affected tombstone metadata. Render labels with DOM text, not HTML. `renderPool` currently counts tombstone personId: reuse `model.pool()` rather than a second assignment convention. Reuse scheduleEvaluate/applyRequiredSlots unchanged.
- `shell/src/renderer/notary/case-drafting-view.js:234-292`: existing modal handles Escape/backdrop, focus trap/restoration; reuse bare modal-head/body/foot + close button, no second modal system. Normally no edit needed.
- `notary_v2/services/inheritance_workspace.py`: reciprocal validator includes tombstones; `_persisted_state` retains Node v3 metadata. `save_diagram` validates/evaluates/atomically writes; `case_workspace.py` reopens canonical. Reuse these paths, no new backend deletion command.
- Existing tests: `shell/test/notary-case-drafting-model.test.mjs`, `notary-diagram.test.mjs`, `notary-case-drafting-view.test.mjs`; real SQLite fixture `_seed_case`/`_draft_state` in `notary_v2/tests/test_inheritance_workspace.py`.

## Tasks & Acceptance

1. After parent reads this plan and fresh retained Quick plan review, mark ready/in-progress; keep one mutation author. #21 spike remains research-only with its three AC; #21B story owns implementation. No additional owner gate.
2. Edit model: pure impact + shared removeNode traversal/cleanup; no-op for missing/deleted target, unsupported/locked/two-party. Snapshot/case identity must prevent stale modal application. Keep mutation synchronous and atomic from subscribers' perspective.
3. Edit diagram: × opens scrollable actual impact warning with node labels/slots and relation list, consequence/Stage/Pool/not-yet-saved text; Hủy/close and explicit **Gỡ cả nhánh**. No model action or new timer until confirm. Confirm recomputes/checks current impact/context before one mutation and existing debounce. Reuse model Pool derivation.
4. Extend behavioral regressions in existing model/diagram tests and real-service inheritance tests: matrix rows, all-depth/coparent, spouse/outgoing tombstones, unrelated roles/marks, empty slots, reassignment/default-position toggles, required-slot evaluation, one mutation, no-cancel effects, canonical save/reopen and rejection preservation. No permanent wiring/source-wording tests.
5. Run bounded tests and actual source Electron against isolated DB; retain full commands, result JSON, graph snapshots, revision/Stage comparisons and UI screenshots in [evidence folder](../tmp/issue-21b-branch-removal/). Parent reads complete scoped diff/proof then fresh Quick code review. Fix accepted findings and rerun only affected checks; no implementation acceptance inferred from old probes.
6. After review, remove only owned executable probes (preserve evidence), update existing spec/handbook/catalog/story + existing changelog, then wait for scoped commit authorization; never mutate foreign processes/packages.

**Acceptance:** Given each matrix fixture, when exercised through model/UI/service as applicable, then every expected observable result holds. Given real Electron × on B, when cancel and confirm/Save/reopen are driven, then dialog, graph, Pool, Stage and revision match story #21B AC1–4. Given final diff/proof, independent Quick has no unresolved acceptance-blocking finding.

## Implementation Notes

- 17/10/2026 — Parent read full phase-1 canonical diff, plan and warning prototype. Retained independent Quick PLAN t2: **No actionable findings**; Ticket validation **clean**. Parent released tasks 2–5 to the same sole author; intent ready, implementation now in progress, no additional owner gate or commit authorization.
- 17/10/2026 — Implemented tasks 2–5 in two renderer files; behavioral tests in existing model/diagram/inheritance workspace suites. Final Node: **198 passed**; real SQLite workspace suites: **106 passed**, 24 existing Python datetime deprecation warnings. No schema/API/store/backend formula change.
- Actual source Electron + real IPC/isolated SQLite completed (`ui-runtime-output-16.txt`, `ui-ipc-proof.json` under evidence). All four dismissals and keyboard focus/trap passed without workspace/command change; synchronous actual confirm-button handler produced **one complete graph transition / one callback**, no partial cut or command before debounce. Real evaluate seeded new `child_owner_2` without reviving deleted IDs. Invalid Save retained draft/old DB; successful Save revision **1→2** and fresh renderer/model reopen were canonical/Stage exact; actual Pool-menu reassignment and receive-position toggle passed.
- Earlier smoke attempts were harness-boundary failures (obsolete nav role, startup readiness, guarded fixture deleted flag, ephemeral catalog refresh/focus, Playwright CSP wait, timing across debounce, ambiguous drag/assign buttons). Kept attempt JSON/logs; final proof did not relax behavior criteria. Bounded service fixture used full committed asset fields instead of legacy pointer-only data; Stage equality remains asserted. Startup `engine_unavailable` toasts remain a disclosed existing observation; screenshot pixels alone do not prove offscreen graph absence, canonical/DOM assertions do.
- Owned executable probe remains for parent/reviewer inspection; delete only after review. All product checks ran before fresh Quick CODE. Plan stays in progress; no built/commit/push claim or authorization.

## Plan Change Log

## Review Triage Log

- 17/10/2026 — PLAN t2 (parent-owned retained Quick): no actionable findings; Ticket validation clean. This is plan readiness only, not a code review or runtime acceptance.
- 17/10/2026 — Fresh retained Quick **CODE t3: No actionable findings**; parent accepted verified AC1–4 after full scoped diff, test-only patch, actual UI and proof/logs read. **BUILT** per existing build workflow convention. Node full 198 preceded wording-assert deletion; affected diagram file 25 passed afterward; service 106/24 existing warnings and Source Electron proof unchanged. No new runs during finalization. Only owned `electron-proof.py` removed after reviewer read; probe diff/all evidence retained. Commit/push tách khỏi nghiệm thu hành vi; receipt lưu riêng.

## Design Notes

Full/high: recursive mass-unassignment changes inheritance reachability and can invalidate reciprocal tombstones; plan designs exact cut set, pre-mutation UI and proof boundaries, not a new architecture. No missing business choice. Phase 1 changes docs/plan only. Markdown is canonical; [packed HTML](../tmp/issue-21b-branch-removal/plan.packed.html) is **Đề xuất · chưa implement** using inspected app modal/tokens. Browser inspection of this artifact is not app smoke.

## Verification

**Proposed bounded commands after parent release (not run in phase 1):**

- `node --test shell/test/notary-case-drafting-model.test.mjs shell/test/notary-diagram.test.mjs shell/test/notary-case-drafting-view.test.mjs shell/test/notary-diagram-errors.test.mjs` — behavior regression, no source-wording pinning.
- From `D:/systemdocs/notary_v2`: `venv/Scripts/python.exe -m pytest tests/test_inheritance_workspace.py tests/test_case_workspace.py` — real engine, own temporary SQLite, success/rejection/reopen. Backend code need not change if existing guards pass.
- Source app: launch `shell/node_modules/electron/dist/electron.exe shell --user-data-dir=<owned evidence/profile> --remote-debugging-port=<free owned port>` using `G1_NOTARY_DATA_DIR`, `G1_UPLOAD_DATA_DIR`, `G1_OUTPUT_DIR` pointing solely at owned evidence subdirectories; `G1_NOTARY_V2_ROOT=D:/systemdocs/notary_v2`, real backend, no mock. Reuse existing main/preload command IPC + CDP/browser and real SQLite service fixtures, not a parallel renderer. Capture × warning, all dismissal routes, keyboard/focus, complete actual node/relation list, coparent/spouse cut, Pool, failed Save draft, successful Save and fresh reopen. Stop only this owned app/sidecar. Never PID9604/shared Orca or foreign Word. No build/dist rewrite unless a demonstrated runtime prerequisite requires it.
- Compare pre/post Stage IDs/values/order, unaffected graph/marks, DB revision/canonical JSON and real engine errors/warnings. Exercise existing empty-slot default and position toggle paths after cut without restoring deleted nodes.

Phase 1 only: pack HTML with `node _bmad/custom/html-plan/runtime/pack.mjs _bmad-output/tmp/issue-21b-branch-removal/plan.html --root .`; inspect closed/open/every-state desktop and narrow viewport. Parent owns separate Ticket/plan Quick validation (`skill://bmad-ticket/references/validate-checks.md`, Ticket section) and the code-review gate. Product tests/runtime proof remain unrun until release.
