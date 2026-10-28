---
title: Visual HTML plans and specs in BMAD
created: 2026-10-10
status: in-progress
route: full
context:
  - D:/systemdocs/docs/decisions/decision-html-plan-exhibits-not-markdown-wrapper.md
---

# Intent approved in this conversation

User asked to implement through Orca with role task workers, then review before delivery. The rejected developer-review app proposal remains rejected. Implement the corrected exhibit-first direction: users see what the actual app will look like and how visible states change. HTML is a human view, not the source of implementation truth.

# Contract

- Reuse the real Thariq `anthropics/claude-plugins-community/html-plan` runtime/packer, pinned and attributed. No second renderer, JSON component DSL, daemon, hook dependency or tracker.
- Hand-author a behavior claim tree: original WHY quote, WHAT as app mock/state screen, HOW and WHERE as optional technical depth. One exhibit per claim; concise Vietnamese.
- Existing app design/labels/tokens guide mockups. Proposed mock is not a screenshot of implemented behavior. No unrelated product change.
- BMAD build/spec load a portable project authoring contract through supported customization. Preserve native Markdown/spec workflows and human gates; do not add fake decisions or a decision quota.
- Browser interaction helps understand the change. Original optional response controls remain secondary; unseen is not approval.
- Do not touch existing dirty deferred-work.md, decision-76…md, or plan-visual-bug-reporting-spike.md; do not modify application runtime or installed/global skills.

# Implementation ownership

1. Runtime worker: `_bmad/custom/html-plan/runtime/htmlplan.css`, `htmlplan.js`, `pack.mjs`, plus parent `LICENSE` and `UPSTREAM.md`.
2. Authoring worker: `docs/specs/shared/visual-html-plans.md`, `_bmad/custom/html-plan/authoring.md`, `_bmad/custom/bmad-build.toml`, `_bmad/custom/bmad-spec.toml`, `README.md`. Write contract before overrides.
3. Exhibit worker: `_bmad/custom/html-plan/examples/notary-diagram-errors.html`; scratch source-map in `docs/tmp/visual-html-plan/`. Ground in the existing diagram-error plan, actual UI source and evidence; do not implement that app change.

Workers share one checkout with disjoint edit ownership. No nested agents, worker gates, formatters or commits. Coordinator owns verification and commits.

# Acceptance and verification

- Given the authored Notary example, when packed with the vendored Node packer, then one offline HTML opens with app-shaped mockups and no unresolved resource dependencies.
- Given the visible lifecycle, when the reader selects states, then the app mock and message/action presentation change meaningfully, not just the explanatory prose.
- Given closed/open claims, when the reader drills into HOW/WHERE, then actual code citations/evidence are discoverable without replacing WHAT with a wall of text.
- Given build/spec customization, when resolved, then both contain the authoring contract and executable portable pack command; build loads it before its planning checkpoint.
- Given desktop/mobile browser views, then mocks remain legible without clipping or page overflow, and any actual upstream limitations are reported.
- Independent read-only reviewers cover provenance/runtime risks and workflow/visual intent. Route real findings back to task workers; rerun affected checks before delivery.

# Verification commands

- `node _bmad/custom/html-plan/runtime/pack.mjs _bmad/custom/html-plan/examples/notary-diagram-errors.html --root D:/systemdocs -o docs/tmp/visual-html-plan/notary-diagram-errors.html`
- Resolve `_bmad/custom/bmad-build.toml` and `bmad-spec.toml` with the existing `resolve_customization.py` and inspect merged persistent facts.
- Browser open the packed example, view closed and expanded claims, switch states, inspect referenced mocks/code, screenshot desktop/mobile, capture errors and external resource requests.
- Check vendored source hashes against recorded pinned upstream source; Node syntax checks on runtime scripts.

# Review and delivery

Review evidence and final user-facing HTML handoff live in `docs/tmp/visual-html-plan/`. Commit only this task's persistent files after green verification; release every settled Orca dispatch. Never claim the Notary application itself was changed.
