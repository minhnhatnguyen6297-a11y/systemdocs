import json,sys
from pathlib import Path
from collections import Counter
from types import SimpleNamespace
from datetime import date
sys.path.insert(0,str(Path.cwd()/'notary_v2'))
from tests.test_word_engine import _person,_participant,_prop,_make_case,_case_state
from services.word_engine import build_template_mapping,build_word_context
from services.case_workspace import CaseWorkspaceService
from models import Property
from tests.test_case_workspace import _person_row,_asset_row
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import database

owner=_person(1,'Chủ đứng dòng 2',born=date(1960,1,1),dead=date(2020,1,1))
receiver=_person(2,'Người nhận đứng dòng 1',born=date(1980,1,1))
case=_make_case(owner,[_participant(receiver,'Con')],case_state=_case_state(receiver,owner))
mapping=build_template_mapping(case,static=True)
keys=['[Người 1 - Họ tên]','[Tên 1]','[ten1]','[Người 2 - Họ tên]','[Tên 2]','[Tên 3]']
result={'word_order':{key:mapping.get(key) for key in keys}}
case.nguoi_nhan_uy_quyen='Đại diện được chọn ở hồ sơ'
case.nguoi_nhan_uy_quyen_id=3
state=json.loads(case.case_state_json)
state['case']={'nguoinhanuyquyen':{'id':3,'ten':case.nguoi_nhan_uy_quyen}}
case.case_state_json=json.dumps(state)
context=build_word_context(case)
mapping=build_template_mapping(case,static=True)
result['authorization']={'metadata_name':mapping['[nguoinhanuyquyen]'],'authorized_people':[p.ho_ten for p in context.authorized_people], 'group_slot':mapping.get('[Người được ủy quyền 1 - Họ tên]')}
prop=_prop(dien_tich=300,land_rows_json='[{"loai_dat":"ONT","dien_tich":100,"thoi_han":"Lâu dài"}]')
case=_make_case(owner,[_participant(receiver,'Con')],properties=[prop],case_state=_case_state(receiver,owner))
mapping=build_template_mapping(case,static=True)
result['total_area']={'source_property_total':prop.dien_tich,'land_rows_sum':100,'exports':{k:mapping.get(k) for k in ['[Diện tích]','[Tài sản 1 - Diện tích]','[Diện tích chữ]']}}
dbengine=create_engine('sqlite:///:memory:')
database.Base.metadata.create_all(dbengine)
with Session(dbengine) as session:
 svc=CaseWorkspaceService(session)
 p=_person_row()
 a=_asset_row(so_serial='AB123456',dia_chi='Địa chỉ mẫu',so_thua_dat=None,so_to_ban_do=None,land_rows=[])
 result['asset_required']={'empty_required_fields':svc._validate_stage([p],[a],'two_party')}
 a['so_serial']='1234/X-2020'
 result['asset_required']['arbitrary_serial']=svc._validate_stage([p],[a],'two_party')
 legacy=Property(so_serial='1234/X-2020',dia_chi='Địa chỉ cũ')
 session.add(legacy);session.flush()
 warnings=[]
 wire=svc._asset_wire(a['row_id'],legacy.id,legacy,warnings=warnings)
 result['legacy_serial']={'original':legacy.so_serial,'wire':wire['so_serial'],'warnings':warnings}
 svc._upsert_assets([wire])
 result['legacy_serial']['after_save']=legacy.so_serial
dbengine.dispose()
manifest=json.loads(Path('artifacts/word-integration-review-fixes-final-20261004/migrated/migration_manifest.json').read_text(encoding='utf-8'))
result['migration_totals']=manifest['totals']
result['legacy_name_occurrences']={f['output_name']:sum(t['count']-t['applied'] for t in f['tokens'] if t['old'].startswith('[Tên ')) for f in manifest['files']}
print(json.dumps(result,ensure_ascii=False,indent=2))
Path('artifacts/investigation-20261004/domain-probes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
