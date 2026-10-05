from pathlib import Path
import sys
for arg in sys.argv[1:]:
    name,_,span=arg.rpartition('@')
    if not span or ':' not in span:name,span=arg,'1:200'
    start,end=map(int,span.split(':'))
    lines=Path(name).read_text(encoding='utf-8-sig').splitlines()
    print(f'\n{name} ({len(lines)} lines)')
    for i in range(start-1,min(end,len(lines))):print(f'{i+1}: {lines[i]}')
