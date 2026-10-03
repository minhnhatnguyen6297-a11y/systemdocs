"""Synthetic labels for DOCX → review → saved Stage → original template."""
import asyncio
import hashlib
import io
import json
import unicodedata
import uuid
import base64
from zipfile import ZipFile
from pathlib import Path

import pytest
from docx import Document
from docx.oxml import OxmlElement

from services.document_intake.adapters.docx import extract
from services.document_intake.docx_source import read_docx, replace_spans
from services.document_intake.docx_store import DocxStore
from services.document_intake.models import AdapterContext, SourceSpec
from services.case_workspace import CaseWorkspaceService, WorkspaceError
from services.word_original import binding_proposals, reviewed_template, export_original, slot_for
from tests.test_case_workspace import db, session_factory, _person_row, _asset_row
from models import InheritanceCase


def fixture_bytes():
    doc = Document()
    doc.add_paragraph('HỢP ĐỒNG CHUYỂN NHƯỢNG')
    doc.add_paragraph('Bên A:')
    p = doc.add_paragraph('Ông: ')
    p.add_run('Nguyễn Văn ').bold = True
    p.add_run('Mẫu').italic = True
    p.add_run(', sinh ngày 01/02/1980; CCCD: 001234567890; thường trú: Nhà A')
    doc.add_paragraph('Bên B:')
    doc.add_paragraph('Bà: Trần Thị Mẫu, sinh ngày 03/04/1985; CCCD: 001234567891; thường trú: Nhà B')
    doc.add_paragraph('Tài sản 1:')
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = 'Số serial: ZZ123456; có địa chỉ tại: Nhà đất A\nThửa đất số: 12; tờ bản đồ số: 5'
    doc.add_paragraph('Loại đất: ONT; Diện tích: 50; Thời hạn: Lâu dài')
    doc.add_paragraph('Loại đất: CLN; Diện tích: 20; Thời hạn: 2050')
    doc.add_paragraph('Tài sản 2:')
    doc.add_paragraph('Số serial: YY123456; có địa chỉ tại: Nhà đất B\nThửa đất số: 22; tờ bản đồ số: 7')
    doc.add_paragraph('Loại đất: ONT; Diện tích: 90; Thời hạn: Lâu dài')
    doc.add_paragraph('Điều 2: Nội dung giữ nguyên 😀')
    doc.add_paragraph('Lời chứng: Nguyễn Văn Mẫu — tên nhắc lại giữ nguyên')
    doc.sections[0].header.paragraphs[0].text = 'ĐẦU TRANG GIỮ NGUYÊN'
    doc.add_picture(io.BytesIO(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=')))
    stream = io.BytesIO(); doc.save(stream)
    return stream.getvalue()


def extraction(content, store=None):
    spec = SourceSpec(str(uuid.uuid4()), 'docx', filename='synthetic.docx')
    ctx = AdapterContext('', '', None, None, read_file=lambda _: content,
                         store_docx=store.save if store else None)
    return asyncio.run(extract(spec, ctx))


def test_labeled_group_ownership_and_raw_refs():
    content = fixture_bytes()
    source = read_docx(content)
    suggestions = extraction(content)
    people = [s for s in suggestions if s['target'] == 'person']
    assets = [s for s in suggestions if s['target'] == 'asset']
    assert len(people) == len(assets) == 2
    assert [p['fields']['ho_ten']['normalized_value'] for p in people] == ['Nguyễn Văn Mẫu', 'Trần Thị Mẫu']
    assert [p['fields']['so_giay_to']['normalized_value'] for p in people] == ['001234567890', '001234567891']
    assert [a['fields']['so_serial']['normalized_value'] for a in assets] == ['ZZ123456', 'YY123456']
    assert [len(json.loads(a['fields']['land_rows']['normalized_value'])) for a in assets] == [2, 1]
    for s in suggestions:
        for field in s['fields'].values():
            for ref in field['source_refs']:
                lo, hi = ref['span']
                assert source.text[lo:hi] == ref['raw_snippet']
                assert ref['docx_refs']


def test_ambiguity_retains_all_evidence_and_duplicates_never_merge():
    doc = Document()
    for line in ['Bên A:', 'Ông: Nguyễn Văn Mẫu, CCCD: 001234567890; CCCD: 001234567899',
                 'Bên B:', 'Bà: Trần Thị Mẫu, CCCD: 001234567890',
                 'Tài sản 1:', 'Serial: Z123456; có địa chỉ tại: Nhà A',
                 'Tài sản 2:', 'Serial: YY123456; có địa chỉ tại: Nhà B',
                 'Tài sản 3:', 'Serial: YY123456; có địa chỉ tại: Nhà C', 'Điều 2: Giữ nguyên']:
        doc.add_paragraph(line)
    stream = io.BytesIO(); doc.save(stream)
    suggestions = extraction(stream.getvalue())
    assert len(suggestions) == 5
    field = suggestions[0]['fields']['so_giay_to']
    assert field['normalized_value'] is None and len(field['source_refs']) == 2
    assert suggestions[2]['fields']['so_serial']['normalized_value'] is None
    assert all(any(w['code'] == 'intake.suspected_duplicate' for w in s['warnings']) for s in suggestions[3:])


def test_two_party_mapping_uses_saved_seat_not_source_or_stage_order():
    snapshot = {'case_type': 'two_party', 'stage': [{'row_id': 'first'}, {'row_id': 'second'}],
                'diagram': {'state': {'nodes': [{'id': 'p17', 'personId': 'first'}, {'id': 'p2', 'personId': 'second'}]}}}
    assert slot_for(snapshot, 'person', 'first', 'ho_ten') == '[Bên B 2 - Họ tên]'
    assert slot_for(snapshot, 'person', 'second', 'ho_ten') == '[Bên A 2 - Họ tên]'


def test_physical_merged_nested_tables_unicode_and_repeated_occurrences():
    doc = Document()
    doc.add_paragraph('TRƯỚC 😀')
    table = doc.add_table(rows=1, cols=2)
    cell = table.cell(0, 0).merge(table.cell(0, 1))
    cell.text = 'GỘP'
    nested = cell.add_table(rows=1, cols=1)
    nested.cell(0, 0).text = 'LỒNG'
    text = unicodedata.normalize('NFD', 'Tên Đặng')
    p = doc.add_paragraph(); p.add_run(text[:4]).bold = True; p.add_run(text[4:])
    doc.add_paragraph(text)
    stream = io.BytesIO(); doc.save(stream); content = stream.getvalue()
    source = read_docx(content)
    assert source.text.count('GỘP') == 1
    assert source.text.index('TRƯỚC') < source.text.index('GỘP') < source.text.index('LỒNG') < source.text.index(text)
    start = source.text.index(text)
    rendered = replace_spans(content, source, [([start, start + len(text)], 'Đã sửa')])
    assert read_docx(rendered).text.count(text) == 1
    assert 'Đã sửa' in read_docx(rendered).text
    with ZipFile(io.BytesIO(content)) as a, ZipFile(io.BytesIO(rendered)) as b:
        for name in a.namelist():
            if name != 'word/document.xml':
                assert a.read(name) == b.read(name)
        assert b'<w:b' in b.read('word/document.xml')


def test_unsupported_hyperlink_and_overlap_rejected():
    doc = Document(); p = doc.add_paragraph('A ')
    hyperlink = OxmlElement('w:hyperlink'); run = OxmlElement('w:r'); text = OxmlElement('w:t')
    text.text = 'Không sửa'; run.append(text); hyperlink.append(run); p._p.append(hyperlink)
    stream = io.BytesIO(); doc.save(stream); content = stream.getvalue(); source = read_docx(content)
    start = source.text.index('Không sửa')
    assert source.warnings
    with pytest.raises(ValueError, match='chưa hỗ trợ'):
        replace_spans(content, source, [([start, start + 3], 'X')])
    with pytest.raises(ValueError, match='chồng'):
        replace_spans(content, source, [([0, 1], 'X'), ([0, 2], 'Y')])


def reviewed_case(db, tmp_path):
    store = DocxStore(tmp_path / 'sources')
    content = fixture_bytes(); suggestions = extraction(content, store)
    people, assets, records = [], [], []
    source_ref = next(iter(suggestions[0]['fields'].values()))['source_refs'][0]
    for suggestion in suggestions:
        values = {key: field['normalized_value'] for key, field in suggestion['fields'].items()}
        if 'land_rows' in values:
            values['land_rows'] = json.loads(values['land_rows'])
        row = _person_row(**values) if suggestion['target'] == 'person' else _asset_row(**values)
        (people if suggestion['target'] == 'person' else assets).append(row)
        records.append({'candidate_id': suggestion['suggestion_id'], 'row_id': row['row_id']})
    context = {'version': 1, 'sources': [{'source_id': source_ref['source_id'], 'sha256': source_ref['source_sha256'], 'records': records, 'bindings': []}]}
    service = CaseWorkspaceService(db, store)
    data = service.create(str(uuid.uuid4()), {'case_type': 'inheritance', 'document_type': 'khai_nhan'},
        {'owner_row_id': people[0]['row_id'], 'people': people, 'assets': assets}, None, context)
    return content, store, service, data


def test_end_to_end_review_commit_reload_original_preservation_and_edit(db, tmp_path):
    original, store, service, data = reviewed_case(db, tmp_path)
    cid = data['case']['id']; revision = data['case']['revision']
    source_id = data['docx_import']['sources'][0]['source_id']
    data['stage']['people'][0]['ho_ten'] = 'Tên đã kiểm tra'
    service.commit_stage(cid, revision, data['stage'])
    db.expire_all(); reloaded = service.get(cid)
    assert reloaded['docx_import']['sources'][0]['records'] == data['docx_import']['sources'][0]['records']
    case = db.get(InheritanceCase, cid)
    proposals = binding_proposals(case, source_id, store)
    bindings = [{key: p[key] for key in ('candidate_id', 'occurrence_id', 'field_key', 'slot')}
                for p in proposals if p['supported']]
    context = reloaded['docx_import']; context['sources'][0]['bindings'] = bindings
    committed = service.commit_stage(cid, reloaded['case']['revision'], reloaded['stage'], docx_import=context)
    with pytest.raises(WorkspaceError, match='Revision'):
        service.commit_stage(cid, reloaded['case']['revision'], reloaded['stage'], docx_import=context)
    db.expire_all(); case = db.get(InheritanceCase, cid)
    rendered, template_hash = reviewed_template(case, source_id, store)
    assert len(template_hash) == 64
    text = read_docx(rendered).text
    assert 'Tên đã kiểm tra' in text
    assert 'Lời chứng: Nguyễn Văn Mẫu — tên nhắc lại giữ nguyên' in text
    assert 'Điều 2: Nội dung giữ nguyên 😀' in text
    with ZipFile(io.BytesIO(original)) as a, ZipFile(io.BytesIO(rendered)) as b:
        assert a.namelist() == b.namelist()
        for name in a.namelist():
            if name != 'word/document.xml':
                assert a.read(name) == b.read(name)
        assert any(name.startswith('word/media/') for name in a.namelist())
    assert hashlib.sha256(original).hexdigest() == context['sources'][0]['sha256']
    result = export_original(case, source_id, store, tmp_path)
    assert result['documents'][0]['status'] == 'saved'
    reordered = committed['stage']; reordered['people'].reverse()
    service.commit_stage(cid, committed['revision'], reordered)
    db.expire_all()
    with pytest.raises(ValueError, match='Thứ tự'):
        reviewed_template(db.get(InheritanceCase, cid), source_id, store)
    path = store.root / source_id / 'original.docx'; path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='đã đổi'):
        reviewed_template(db.get(InheritanceCase, cid), source_id, store)


def test_context_new_session_invalid_binding_rollback_and_row_removal(db, session_factory, tmp_path):
    _, store, _, data = reviewed_case(db, tmp_path)
    cid = data['case']['id']; source_id = data['docx_import']['sources'][0]['source_id']
    with session_factory() as fresh:
        service = CaseWorkspaceService(fresh, DocxStore(store.root))
        loaded = service.get(cid)
        assert loaded['docx_import'] == data['docx_import']
        bad = json.loads(json.dumps(loaded['docx_import']))
        bad['sources'][0]['bindings'] = [{'candidate_id': bad['sources'][0]['records'][0]['candidate_id'],
            'occurrence_id': str(uuid.uuid4()), 'field_key': 'ho_ten', 'slot': '[Người 1 - Họ tên]'}]
        loaded['stage']['people'][0]['ho_ten'] = 'Không được lưu'
        with pytest.raises(WorkspaceError, match='Vị trí'):
            service.commit_stage(cid, loaded['case']['revision'], loaded['stage'], docx_import=bad)
        unchanged = service.get(cid)
        assert unchanged['stage']['people'][0]['ho_ten'] != 'Không được lưu'
        assert unchanged['case']['revision'] == loaded['case']['revision']
        removed = unchanged['stage']['people'].pop(0)['row_id']
        unchanged['stage']['owner_row_id'] = unchanged['stage']['people'][0]['row_id']
        result = service.commit_stage(cid, unchanged['case']['revision'], unchanged['stage'])
        assert all(r['row_id'] != removed for r in result['docx_import']['sources'][0]['records'])
        with pytest.raises(ValueError, match='không thuộc'):
            binding_proposals(fresh.get(InheritanceCase, cid), str(uuid.uuid4()), store)


def test_actual_context_and_proposals_match_contract_schema(db, tmp_path):
    from jsonschema import Draft7Validator, FormatChecker
    from referencing import Registry, Resource
    _, store, service, data = reviewed_case(db, tmp_path)
    root = Path(__file__).resolve().parents[2] / 'contracts/notary-case-drafting'
    schemas = {p.name: json.loads(p.read_text(encoding='utf-8')) for p in root.glob('*.schema.json')}
    registry = Registry().with_resources(
        [((root / name).as_uri(), Resource.from_contents(schema)) for name, schema in schemas.items()]
        + [(schema['$id'], Resource.from_contents(schema)) for schema in schemas.values()])
    def validate(name, definition, value):
        Draft7Validator({'$ref': (root / name).as_uri()+'#/definitions/'+definition}, registry=registry,
                        format_checker=FormatChecker()).validate(value)
    validate('common.schema.json', 'docx_import', data['docx_import'])
    cid = data['case']['id']; case = db.get(InheritanceCase, cid)
    proposals = binding_proposals(case, data['docx_import']['sources'][0]['source_id'], store)
    validate('draft-v2.schema.json', 'word_options_result_v2', {'schema_version': data['schema_version'],
        'documents': [], 'binding_proposals': proposals})
    context = data['docx_import']; context['sources'][0]['bindings'] = [
        {k:p[k] for k in ('candidate_id','occurrence_id','field_key','slot')} for p in proposals if p['supported']]
    committed = service.commit_stage(cid, data['case']['revision'], data['stage'], docx_import=context)
    validate('common.schema.json', 'docx_import', committed['docx_import'])
    validate('draft-v2.schema.json', 'payload_commit_stage_v2', {'case_id': cid,
        'base_revision': committed['revision'], 'stage': committed['stage'], 'docx_import': committed['docx_import']})
