import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode('utf-8')

paths = set(filter(None, (git('ls-files', '-m', '-o', '--exclude-standard', '-z')
                         + git('diff', '--name-only', '-z', '8a7d8bf')).split('\0')))
errors = []
checked = 0
links = 0
historical = []
for name in sorted(paths):
    p = ROOT / name
    if p.suffix != '.md' or not p.is_file():
        continue
    if '/withdrawn-20261004/' in name:
        historical.append(name)
        continue
    checked += 1
    content = p.read_text(encoding='utf-8', errors='replace')
    for match in re.finditer(r'\[[^\]]*\]\((<[^>]*>|[^\n)]*)\)', content):
        target = match.group(1).strip().strip('<>')
        if target.startswith(('http:', 'https:', 'codex:', 'mailto:', '#', 'app:', 'plugin:')):
            continue
        target = target.split('#')[0].split(' "')[0]
        if not target or ':' in target[:10]:
            continue
        path = p.parent / unquote(target)
        links += 1
        if not path.exists():
            errors.append({'file': name, 'line': content[:match.start()].count('\n') + 1,
                           'target': target})

result = {'markdown_files_checked': checked, 'local_links_checked': links,
          'historical_snapshots_skipped': len(historical), 'missing_links': errors,
          'scope': 'new/modified markdown; historical withdrawn snapshots preserve original source links'}
(ROOT / '.agents/handoff/worktree-consolidation-20261005/link-check.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
