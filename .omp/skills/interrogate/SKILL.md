---
name: interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Adversaries try to break a change or design, and only findings proven by a run survive."
disable-model-invocation: true
---

# Interrogate

> Nguồn: pstack `skills/interrogate/SKILL.md` (https://github.com/backnotprop/pstack, mirror của cursor/plugins/pstack v0.15.36+), © 2026 Lauren Tan, MIT — xem `LICENSE-pstack`. Chuyển thể tối thiểu cho omp: bỏ phụ thuộc skill `arena`/`in-your-own-words`/`poteto-mode` (viết gộp các bước cần dùng vào đây) và thay model/subagent kiểu Cursor bằng tool `task` + model role của omp.

Adversaries try to break a change or a design. A finding survives only when a run proves it. Report the findings. Do not apply fixes.

## Frame

The scope is what the user names. Otherwise it is the branch diff from its merge base with the base branch, through the working tree. Restate the intent in your own words (what the user wants and what problem it solves), from the user's message, the commits, and the PR description. Ask the user when the intent is unclear.

## Fan out

1. Pick the adversaries: by default two, one on omp's `default` model role and one on the `smol` role (`~/.omp/agent/config.yml` modelRoles; do not edit it). If a role cannot be spawned, run that seat on the parent model and say so. Add more adversaries when the scope covers several independent areas.
2. Give each adversary its own git worktree (or `/tmp/interrogate-<slug>/adversary-<n>/` when a worktree is impossible) and copy the scope's uncommitted changes into it, so adversaries never share state.
3. Spawn all adversaries at once, in parallel, as general-purpose subagents (omp `task` tool, agent `task`). If one produces no output, continue with the rest and note the dropout. Give each adversary the scope, the intent, its worktree path, and this brief:

> Break this change. Prove each finding with a run against the real code, such as a failing test, a repro script, or command output that shows the wrong behavior. For a design or plan, run a prototype or probe the current tree. Keep repros in your own worktree. Report each finding with a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter. No findings is a valid result.

## Verify

Verify each finding yourself by rerunning its command. Keep a finding when the output shows the failure and the failure breaks the intent. Drop the rest. Merge findings that share a root cause.

Do not pick one adversary's list or judge between them. Adversaries find different failures, so the verdict keeps every verified finding, not one adversary's list.

## Output

- **Intent**: the restatement.
- **Findings**: for each verified finding, the command, its output, how it breaks the intent, and the adversaries that found it. Say "no verified findings" when none survive.
- **Dropped**: for each adversary, the count of dropped findings and why.
