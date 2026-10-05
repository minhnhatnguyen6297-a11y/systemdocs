from pathlib import Path
import sys,json,tempfile,shutil
sys.path.insert(0,str(Path.cwd()))
from notary_v2.tests.test_administrative_timeline import bando_fixture
from notary_v2.administrative_timeline import import_bando,read_ledger
from notary_v2.services.administrative_address import AddressIndex
root=Path.cwd()/'.agents/review-plan-20261004'
folder=Path(tempfile.mkdtemp(prefix='ledger-',dir=root))
try:
 raw,tables=bando_fixture()
 first=import_bando(folder,raw,'2026-10-04T00:00:00+07:00',tables,strict=False)
 old_version=read_ledger(folder)['dataset_version']
 rows=json.loads(raw);rows[1]['ten']='Xã New C'
 newer=json.dumps(rows,ensure_ascii=False).encode()
 nt={'01':(json.dumps(rows[0],ensure_ascii=False)+'.synt.'+json.dumps(rows[1:],ensure_ascii=False)).encode()}
 import_bando(folder,newer,'2026-10-05T00:00:00+07:00',nt,strict=False)
 import_bando(folder,raw,'2026-10-06T00:00:00+07:00',tables,strict=False)
 ledger=read_ledger(folder)
 result=AddressIndex(ledger).lookup({'address':'Xã C, Tỉnh Test','source_date':'2026-01-01','target_date':'2026-10-04'})
 result={'reactivated_version_is_A':ledger['dataset_version']==old_version,'requested_current_name':'Xã C','returned':result}
 public=json.loads(Path('notary_v2/data/administrative_units/ledger.json').read_text(encoding='utf-8'))
 result['dated_public_events']=sum(e['effective_on'] is not None for e in public['events'])
 (root/'address-refresh-probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'reactivated_version_is_A':result['reactivated_version_is_A'],'request':'Xã C, Tỉnh Test','returned':[c['address'] for c in result['returned']['candidates']],'dated_public_events':result['dated_public_events']},ensure_ascii=False,indent=2))
finally:
 shutil.rmtree(folder)
