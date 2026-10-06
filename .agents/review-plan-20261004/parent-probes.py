from pathlib import Path
import sys,io,json
from zipfile import ZipFile
sys.path.insert(0,str(Path.cwd()/'notary_v2'))
sys.path.insert(0,str(Path.cwd()/'tools'))
from services.document_intake.docx_source import read_docx
from regex_workbench.engine.runner import run,load_profile

ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
mc='http://schemas.openxmlformats.org/markup-compatibility/2006'
person='Ông: Nguyễn Văn An, sinh ngày 01/01/1980; CCCD số: 012345678901; thường trú: xã Yên Bình, tỉnh Ninh Bình.'
p=lambda s:f'<w:p><w:r><w:t>{s}</w:t></w:r></w:p>'
body=p('HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT')+p('BÊN A:')+f'<mc:AlternateContent><mc:Choice Requires="w">{p(person)}</mc:Choice><mc:Fallback>{p(person)}</mc:Fallback></mc:AlternateContent>'+p('Điều 1. TÀI SẢN CHUYỂN NHƯỢNG')
xml=f'<w:document xmlns:w="{ns}" xmlns:mc="{mc}"><w:body>{body}</w:body></w:document>'
stream=io.BytesIO()
with ZipFile(stream,'w') as z:z.writestr('word/document.xml',xml)
source=read_docx(stream.getvalue())
result=run(source.text,load_profile('transfer'))
people=[p for b in result['parties'].get('blocks',[]) for p in b.get('persons',[])]
out={'alternate_content':{'physical_variants':2,'displayed_variants':1,'reader_text':source.text,'reader_warnings':source.warnings,'extracted_people':len(people),'names':[p['fields']['ho_ten']['value'] for p in people]}}
schema=json.loads(Path('contracts/notary-case-drafting/common.schema.json').read_text(encoding='utf-8'))
out['original_reason_schema']={'block_reason_definition':schema['definitions']['document_option']['properties']['block_reason'],'emitted_code':'word.original_mapping_invalid'}
print(json.dumps(out,ensure_ascii=False,indent=2))
Path('.agents/review-plan-20261004/parent-probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
