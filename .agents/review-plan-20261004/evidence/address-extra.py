import sys,json,subprocess,hashlib
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path.cwd()/'notary_v2'))
from services.administrative_address import AddressLookup,parse_address,apply_address
out=Path('artifacts/investigation-20261004')
lookup=AddressLookup()
queries=[
 {'address':'xã Vũ Dương, tỉnh Ninh Bình','source_date':'2026-01-01','target_date':'2026-10-04'},
 {'address':'Thôn A, Yên Bình, Ninh Bình','source_date':'2024-01-01','target_date':'2026-10-04'},
 {'address':'Thôn A, Yên Bình, Ninh Bình','source_date':'2026-01-01','target_date':'2026-10-04'},
]
results=[]
for q in queries:
 r=lookup.lookup(q)
 results.append({'query':q,'parsed':parse_address(q['address'],q['source_date']),'result':r,'applied':[apply_address(q['address'],c['address']) for c in r['candidates']]})
ledger=json.loads(Path('notary_v2/data/administrative_units/ledger.json').read_text(encoding='utf-8'))
stats={key:{'count':len(ledger[key]),'status':dict(Counter(x.get('status') for x in ledger[key]))} for key in ('units','events')}
stats['unit_levels']=dict(Counter(x['level'] for x in ledger['units']))
stats['events_with_effective_date']=sum(x.get('effective_date') is not None for x in ledger['events'])
(out/'address-extra.json').write_text(json.dumps({'cases':results,'ledger':stats},ensure_ascii=False,indent=2),encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
names=git('diff','--name-only','--no-renames','consolidate/monorepo...HEAD').splitlines()
inventory={'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'base':git('merge-base','HEAD','consolidate/monorepo'),'commit_count':int(git('rev-list','--count','consolidate/monorepo..HEAD')),'files':[{'path':n,'bytes':Path(n).stat().st_size,'sha256':hashlib.sha256(Path(n).read_bytes()).hexdigest()} for n in names if Path(n).is_file()]}
(out/'change-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ledger':stats,'queries':[{'parsed':r['parsed'],'status':r['result']['status'],'applied':r['applied']} for r in results],'head':inventory['head'],'base':inventory['base'],'file_count':len(inventory['files'])},ensure_ascii=False,indent=2))
