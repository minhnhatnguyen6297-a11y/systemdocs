# HTML presentation at the existing BMAD phase

Cloud-package wiring repair; the project repository and upstream skills are unchanged. Load this reference through the supported `workflow.activation_steps_append` and `workflow.persistent_facts` customizations. Paths are relative to the active project root (the folder containing `_bmad/`), not the installed skill directory. Keep these phase instructions active when reading just-in-time step files.

The complete, approved authoring contract is `_bmad/custom/html-plan/authoring.md`; its policy source is `_bmad-output/specs/shared/visual-html-plans.md`. Read both fully. The contract's claim/exhibit HTML skeleton, text/plain block data shape, runtime URLs and pack command are the actual authoring interface; there is no `sections[]`/JSON plan schema or Markdown-to-HTML wrapper. Runtime dependencies are the three local files in `_bmad/custom/html-plan/runtime/`; Node uses built-ins only. Do not fetch a runtime or run BMAD setup.

## Build — step-02-plan.md / CHECKPOINT 1

After investigation, the canonical Markdown plan, self-review and resolution of the workflow's existing open questions, but BEFORE presenting CHECKPOINT 1 or requesting its existing approval, re-read the authoring contract and generate the task's HTML presentation. Inspect relevant real source/UI as that contract requires. Author `_bmad-output/tmp/<task-slug>/plan.html` using real task claims and one useful exhibit per claim; resolve its relative CSS/JS URLs to this project's runtime. Pack from the project root:

```sh
node _bmad/custom/html-plan/runtime/pack.mjs _bmad-output/tmp/<task-slug>/plan.html --root .
```

Replace `<task-slug>` with this task's actual slug. Fix pack errors and handle or disclose warnings. Open `plan.packed.html` in the available browser, inspect closed/open claims and every relevant state at desktop and narrow viewport. Present its clickable packed path together with `{plan_file}` at the SAME existing checkpoint. Preserve the Markdown template, source of truth, choices and approval semantics. If the plan changes, regenerate its presentation before presenting again; never treat a stale HTML as the updated plan.

## Build — step-oneshot.md / before Implement

On either automatic or pinned oneshot, and on resumed oneshot before further implementation, apply the same authoring/pack/browser/presentation steps for changes requiring visual explanation BEFORE implementation. Do not add an approval checkpoint to oneshot. Apply the approved trivial-task exception; an explicit request for visuals still requires HTML. Do not defer HTML to `on_complete`.

## Spec — after Self-Validate / before Output

For create/update, after the two existing self-validation passes and BEFORE Output, re-read the contract and author `_bmad-output/tmp/<task-slug>/spec.html` from the current spec; pack with the same command using `spec.html`. Inspect in the browser, then deliver the clickable `spec.packed.html` path alongside the canonical spec folder in interactive output. In headless mode produce the HTML beside the artifacts and let the caller deliver its path WITHOUT adding keys to `assets/headless-schemas.md`. Spec activation remains `resolve_customization.py`, not `render_skill.py`. Preserve `.memlog.md`, SPEC.md, companions, CAP IDs and the existing output schema.

## Shared limits

HTML is presentation, not a new planning authority or approval gate. Respond/comments and unseen defaults are not approval. If no browser is available, disclose exactly what was packed and what was not visually inspected; do not claim visual proof. Follow the contract's trivial-task exception. The packaged `BMAD-FLOW.html` and `html-plan-example.html` are offline workflow guidance and a synthetic runtime example, NOT an executed or approved application plan; never substitute either for task-specific authoring.
