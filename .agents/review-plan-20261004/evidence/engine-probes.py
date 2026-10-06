import sys, json, time, hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
sys.path.insert(0,str(Path.cwd()/'notary_v2'))
from regex_workbench.engine.runner import run, load_profile
from services.administrative_address import AddressLookup, AddressIndex, predecessor_names, normalize

out = Path('artifacts/investigation-20261004')
out.mkdir(exist_ok=True)
profile=load_profile('transfer')
persons = '\n'.join(f'{title}: {name}, sinh ngày: 0{i}/01/1980; CCCD số: 01234567890{i} do Bộ Công an cấp ngày 01/12/2024; thường trú: xã Yên Bình, tỉnh Ninh Bình.' for i,(title,name) in enumerate([('Ông','Nguyễn Văn An'),('Bà','Trần Thị Bình'),('Ông','Lê Văn Cường')],1))
asset='Điều 1. TÀI SẢN CHUYỂN NHƯỢNG\nTài sản 1:\nGiấy chứng nhận số: AB123456; số vào sổ: CS12345; cấp ngày 01/01/2020.\nThửa đất số: 206; tờ bản đồ số: 119; diện tích: 300,0 m2; có địa chỉ tại: xã Yên Bình, tỉnh Ninh Bình.\nLoại đất: Đất ở tại nông thôn; Diện tích: 100,0; Thời hạn: Lâu dài\nLoại đất: Đất trồng cây lâu năm; Diện tích: 200,0; Thời hạn: 2050\nĐiều 2. Giá chuyển nhượng'
base='HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT\nBÊN A:\n'+persons+'\n'+asset
cases={
 'baseline_3_people_1_asset':base,
 'numbered_people':base.replace('Ông: Nguyễn','1. Ông: Nguyễn').replace('Bà: Trần','2. Bà: Trần').replace('Ông: Lê','3. Ông: Lê'),
 'no_transfer_side_inheritance':base.replace('HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT','VĂN BẢN KHAI NHẬN DI SẢN').replace('BÊN A:','NHỮNG NGƯỜI KHAI NHẬN DI SẢN:'),
 'asset_address_at_label':base.replace('có địa chỉ tại:','Địa chỉ thửa đất:'),
 'land_use_purpose':base.replace('Loại đất:','Mục đích sử dụng:'),
 'death_date':base.replace('sinh ngày: 01/01/1980;','sinh ngày: 01/01/1980; chết ngày 02/03/2020;'),
 'person_address_period_abbreviation':base.replace('thường trú: xã Yên Bình, tỉnh Ninh Bình.','thường trú: số 12, P. Yên Bình, TP. Ninh Bình.'),
 'address_followed_by_birth':base.replace('CCCD số: 012345678902 do Bộ Công an cấp ngày 01/12/2024; thường trú: xã Yên Bình, tỉnh Ninh Bình.','CCCD số: 012345678902 do Bộ Công an cấp ngày 01/12/2024;\ntrụ tại xã Vụ Bản, sinh ngày 01/01/1991; CCCD số: 123456789001;'),
 'serial_arbitrary':base.replace('AB123456','1234/X-2020'),
 'two_unlabelled_parcels':base.replace('Tài sản 1:\n','') .replace('Điều 2. Giá chuyển nhượng','Thửa đất số: 207; tờ bản đồ số: 120; diện tích: 400 m2; có địa chỉ tại: xã Yên Bình, tỉnh Ninh Bình.\nGiấy chứng nhận số: CD123456.\nĐiều 2. Giá chuyển nhượng'),
}
results={}
for name,text in cases.items():
 r=run(text,profile)
 ps=[{k:v.get('value') for k,v in p['fields'].items() if v.get('span')} for b in r['parties'].get('blocks',[]) for p in b.get('persons',[])]
 assets=[{'state':g['state'],'fields':{f['name']:{'state':f['state'],'value':f.get('value')} for f in g['fields'] if f.get('span')},'land_rows':len(g['land_rows'])} for g in r['asset_groups']]
 results[name]={'people':ps,'assets':assets,'errors':r['errors'],'zones':[(z['name'],z['state']) for z in r['zones']]}
 print(name, json.dumps(results[name],ensure_ascii=False))
lookup=AddressLookup()
queries=[
 {'address':'xã Yên Bình'},
 {'address':'xã Yên Bình','source_date':'2024-01-01','target_date':'2026-10-04'},
 {'address':'xã Yên Bình, tỉnh Ninh Bình','source_date':'2024-01-01','target_date':'2026-10-04'},
 {'address':'xã Yên Bình, tỉnh Vĩnh Phúc','source_date':'2024-01-01','target_date':'2026-10-04'},
 {'address':'xã Yên, tỉnh Ninh Bình','source_date':'2024-01-01','target_date':'2026-10-04'},
 {'address':'xã Yên Bình, tỉnh Ninh Bình','source_date':'2027-01-01','target_date':'2026-10-04'},
]
addresses=[]
for q in queries:
 start=time.perf_counter(); r=lookup.lookup(q)
 compact={'query':q,'seconds':round(time.perf_counter()-start,3),'status':r['status'],'coverage':r['coverage'],'candidates':[{k:c.get(k) for k in ['address','raw_phrase','partial','historical']} for c in r['candidates']]}
 addresses.append(compact); print('ADDRESS',json.dumps(compact,ensure_ascii=False))
ledger=json.loads(Path('notary_v2/data/administrative_units/ledger.json').read_text(encoding='utf-8'))
index=AddressIndex(ledger)
aliases={term:len(index.aliases[normalize(term)]) for term in ['xã Yên Bình','tỉnh Nam Định','tỉnh Hà Nam','tỉnh Ninh Bình','tỉnh Bắc Kạn','tỉnh Vĩnh Phúc']}
print('ALIASES',json.dumps(aliases,ensure_ascii=False))
hashes=[{'id':s['id'],'ok':hashlib.sha256((Path('notary_v2/data/administrative_units')/s['snapshot']).read_bytes()).hexdigest()==s['sha256']} for s in ledger['sources']]
stats={'snapshot_count':len(hashes),'hash_mismatch':[h for h in hashes if not h['ok']], 'aliases':aliases}
(out/'probes.json').write_text(json.dumps({'extraction':results,'addresses':addresses,'ledger':stats},ensure_ascii=False,indent=2),encoding='utf-8')
