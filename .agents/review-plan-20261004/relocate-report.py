from pathlib import Path
root=Path.cwd()
source=root/'.agent/tasks/MIN-139/investigation-report-2026-10-04.md'
target=root/'.agents/review-plan-20261004/investigation-report.md'
assert source.resolve().is_relative_to(root.resolve()) and target.resolve().is_relative_to(root.resolve())
assert not target.exists()
text=source.read_text(encoding='utf-8')
text=text.replace('](../../../','](../../').replace('](../MIN-141/progress.md)','](../../.agent/tasks/MIN-141/progress.md)')
target.write_text(text,encoding='utf-8')
source.unlink()
print(str(target))
