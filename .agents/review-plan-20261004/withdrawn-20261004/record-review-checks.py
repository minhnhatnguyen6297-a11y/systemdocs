from pathlib import Path
import json
import subprocess

folder = Path(__file__).resolve().parent
root = folder.parents[1]
validation = json.loads((folder / "handoff-validation.json").read_text(encoding="utf-8"))
if validation["errors"]:
    raise SystemExit("Handoff checks failed")
note = f"""Kiểm bàn giao cuối lượt review: validate-handoff.py kiểm {validation['checked_files']} file, {validation['local_links_checked']} local links, backticks/fences, references/dependencies và xác nhận {len(validation['repair_tasks_to_do_unchecked'])} task sửa đều To Do/AC chưa tick; 0 lỗi. git diff --check qua. File theo dõi trong Git chỉ có spec được review sửa và NAIA-15/progress.md vốn đã bẩn; không sửa runtime/contract/schema/mẫu. Bằng chứng: .agents/review-plan-20261004/handoff-validation.json.

AC review 1–4 đã có report/spec/plan/checklist và bằng chứng kiểm tài liệu; không phải AC triển khai tính năng. TASK-2 giữ In Progress để chốt bản plan cuối sau Q1/Q2/Q3; task sửa chưa bắt đầu. TASK-11 chờ danh mục/mẫu để chốt nhóm cấu trúc. CLI decision chỉ hỗ trợ title/status; quyết định gì/tại sao nằm trong title decision, notes TASK-2 và spec tương ứng. Các mục Context/Decision/Consequences do CLI tạo chưa có nội dung riêng; không sửa tay Backlog.
"""
args = ["rtk", "proxy", "node", "C:/Users/MINH/AppData/Roaming/npm/node_modules/backlog.md/cli.js",
        "task", "edit", "TASK-2", "--check-ac", "1", "--check-ac", "2", "--check-ac", "3", "--check-ac", "4",
        "--check-dod", "1", "--check-dod", "2", "--append-notes", note, "--plain"]
run = subprocess.run(args, cwd=root, capture_output=True, encoding="utf-8", errors="replace")
(folder / "review-checks-cli.log").write_text(run.stdout + "\n" + run.stderr, encoding="utf-8")
if run.returncode:
    raise SystemExit(run.stdout + run.stderr)
print("Recorded review AC evidence; repair tasks remain To Do; owner questions remain open.")
