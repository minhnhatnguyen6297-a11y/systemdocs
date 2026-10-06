from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[3]
mode = sys.argv[1]
if mode == 'diff':
    text = (ROOT / '.agent/scratch/review-plan-20261004/branch.diff').read_text(encoding='utf-8-sig')
    for part in text.split('diff --git ')[1:]:
        if any(name in part.splitlines()[0] for name in sys.argv[2:]):
            print('diff --git ' + part)
elif mode == 'lines':
    lines = (ROOT / sys.argv[2]).read_text(encoding='utf-8-sig').splitlines()
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    end = int(sys.argv[4]) if len(sys.argv) > 4 else len(lines)
    print('\n'.join(f'{n}: {lines[n-1]}' for n in range(start, min(end, len(lines))+1)))
elif mode == 'outline':
    for name in sys.argv[2:]:
        path = ROOT / name
        print(name)
        src = path.read_text(encoding='utf-8-sig')
        if path.suffix == '.py':
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    print(f'  {node.lineno}-{node.end_lineno}: {node.name}')
        else:
            for n, line in enumerate(src.splitlines(), 1):
                if 'test(' in line or 'describe(' in line or 'function ' in line:
                    print(f'  {n}: {line}')
