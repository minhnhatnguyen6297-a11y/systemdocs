# Quick review lens prompt — visual bug comment capture

Run this prompt in a fresh session (this worker may not spawn subagents). Copy the block below verbatim.

Note for the reviewer: the spike code lives under `_bmad-output/tmp/` (git-ignored), so it appears in the diff as whole-file `new file` sections rather than deltas; the intended delta is described in the plan's `## Implementation Notes`. Tracked shell hooks appear as normal diffs.

---

Read `D:/systemdocs-spike-visual-bug/_bmad-output/implementation-artifacts/plan-visual-bug-comment-capture.md` — the plan holding the acceptance criteria and intent — and the files its frontmatter `context:` lists. Read the agent instruction files (`AGENTS.md`, `CLAUDE.md`, or equivalents) at the repository root and in the directories the diff touches; those are the rules. Then read the unified diff at `C:/Users/MINH/AppData/Local/Temp/visual-bug-comment-capture-latest.diff` — it is the change under review (refreshed to include the harness sink `G1_VISUAL_SPIKE_SINK`, the `smoke-reports/` isolation and the `check_image.py` sink-path fix).

Report unmet acceptance criteria, broken rules, and bugs. Each finding: the location, what goes wrong, and evidence checked against the surrounding code. Output a Markdown list of findings only — no severity, priority, or ranking.

Do not invoke any skill, and do not spawn subagents of your own — you are the reviewer. Return your findings as text in your final message; do not route them through any findings-reporting tool the host may offer.
