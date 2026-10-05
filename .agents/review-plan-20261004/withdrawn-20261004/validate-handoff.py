from pathlib import Path
from urllib.parse import unquote
import json
import re
import subprocess

root = Path(__file__).resolve().parents[2]
folder = Path(__file__).resolve().parent
state = json.loads((folder / "backlog-publish-state.json").read_text(encoding="utf-8"))
specs = ["docs/spec/notary_v2/README.md", "docs/spec/notary_v2/stage.md",
         "docs/spec/notary_v2/administrative-address.md", "docs/spec/notary_v2/input/docx-import.md",
         "docs/spec/notary_v2/word-output.md", "docs/spec/notary_v2/input/README.md",
         "docs/spec/notary_v2/input/document-extraction.md"]
files = specs + [".agents/review-plan-20261004/investigation-report.md",
                 "backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md"]
files += [t["path"] for t in state["tasks"].values()]
files += [d["path"] for d in state["decisions"]]
errors = []
link_count = 0
for name in files:
    path = root / name
    body = path.read_text(encoding="utf-8-sig")
    for match in re.finditer(r"!?\[[^\]\n]+\]\(([^)\n]+)\)", body):
        target = match.group(1).strip().strip("<>")
        if re.match(r"^(?:https?://|mailto:|app://|#)", target):
            continue
        target = unquote(target.split("#", 1)[0])
        if not target:
            continue
        if not (path.parent / target).resolve().exists():
            errors.append(f"Missing link: {name}: {target}")
        link_count += 1
    if "{{" in body:
        errors.append("Unresolved placeholder in " + name)
    fence = False
    for number, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence and line.count("`") % 2:
            errors.append(f"Unpaired backtick: {name}:{number}")
    if fence:
        errors.append("Unclosed fence: " + name)

task_ids = {item["id"] for item in state["tasks"].values()}
task_checks = []
for key, item in state["tasks"].items():
    text = (root / item["path"]).read_text(encoding="utf-8-sig")
    if "status: To Do" not in text or re.search(r"^- \[x\]", text, re.M):
        errors.append("Repair prematurely checked/finished: " + item["id"])
    header = text.split("---", 2)[1]
    for ref in re.findall(r"^  - (.+)$", header, re.M):
        if ref.startswith("TASK-"):
            if ref not in task_ids:
                errors.append("Unknown dependency " + ref)
        elif ref.startswith(("docs/", "backlog/", ".agents/", "notary_v2/")):
            if not (root / ref).exists():
                errors.append("Missing task reference " + ref)
    task_checks.append(item["id"])

run = subprocess.run(["rtk", "proxy", "git", "diff", "--name-only"], cwd=root,
                     capture_output=True, encoding="utf-8", check=True)
tracked_changes = run.stdout.splitlines()
allowed = set(specs + [".agent/tasks/NAIA-15/progress.md"])
for name in tracked_changes:
    if name not in allowed:
        errors.append("Unexpected tracked modification " + name)

report = (folder / "investigation-report.md").read_text(encoding="utf-8")
for expected in ["NG-01 — Đã rút", "RE-05", "DC-08", "DB-02", "W-05", "Đã chốt bằng câu trả lời trực tiếp"]:
    if expected not in report:
        errors.append("Missing report requirement " + expected)
master = (root / "backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md").read_text(encoding="utf-8-sig")
for expected in ["Q1/Q2/Q3", "cùng serial", "chỉ kiểm dữ liệu", "Checklist parent", "test_notary_intake_adapter.py"]:
    if expected not in master:
        errors.append("Missing plan requirement " + expected)

engine = state["tasks"].get("engine")
if engine:
    engine_spec = (root / "docs/spec/notary_v2/input/document-extraction.md").read_text(encoding="utf-8-sig")
    for expected in [engine["id"], "ông/bà: A", "không là số nhóm đã", "bộ giữ lại", "dự phòng"]:
        if expected not in engine_spec:
            errors.append("Missing strategy requirement " + expected)
    if engine["id"] not in (root / state["tasks"]["intake"]["path"]).read_text(encoding="utf-8-sig"):
        errors.append("DOCX task missing engine dependency")

result = {"checked_files": len(files), "local_links_checked": link_count,
          "repair_tasks_to_do_unchecked": task_checks, "tracked_modifications": tracked_changes,
          "errors": errors}
(folder / "handoff-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
