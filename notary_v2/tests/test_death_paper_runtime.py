"""Synthetic owner rules: real DOCX evidence, workspace persistence and Word."""
import asyncio
import io
import uuid

import pytest
from docx import Document

from models import Customer
from services.case_workspace import CaseWorkspaceService
from services.document_intake.adapters.docx import extract
from services.document_intake.models import AdapterContext, SourceSpec
from services.document_intake.ocr_pipeline import _pair_persons
from services.word_engine import WordPerson
from tests.test_case_workspace import db, session_factory, _person_row, _asset_row


def read_people(*clauses, heading='VĂN BẢN KHAI NHẬN DI SẢN'):
    doc = Document()
    for text in (heading, 'Người để lại di sản:', *clauses):
        doc.add_paragraph(text)
    stream = io.BytesIO()
    doc.save(stream)
    spec = SourceSpec(str(uuid.uuid4()), 'docx', filename='controlled-death.docx')
    ctx = AdapterContext('', '', None, None, read_file=lambda _: stream.getvalue())
    suggestions = asyncio.run(extract(spec, ctx))
    return [item for item in suggestions if item['target'] == 'person']


def values(item):
    return {key: field['normalized_value'] for key, field in item['fields'].items()}


@pytest.mark.parametrize('source_type,canonical,number', [
    ('Trích lục khai tử', 'Trích lục khai tử', '1234/TLKT'),
    ('trích lục khai tử (Bản sao)', 'Trích lục khai tử (bản sao)', '1234/2024/TLKT-BS'),
    ('Giấy chứng tử', 'Giấy chứng tử', '12, quyển 1'),
    ('Giấy chứng tử (bản sao)', 'Giấy chứng tử', '12/2024, quyển số 1/2024'),
])
def test_real_docx_paper_fields_preserve_exact_number_type_issuer(source_type, canonical, number):
    person, = read_people(
        'Ông Lê Văn Mẫu, sinh năm 1940, chết năm 2000 theo '
        f'{source_type} số: {number} do Ủy ban nhân dân thị trấn Mẫu cấp ngày 02/03/2024; '
        'Nơi thường trú cuối cùng trước khi chết: Xóm Mẫu, thị trấn Mẫu.')
    result = values(person)
    assert result == {
        'ho_ten': 'Lê Văn Mẫu', 'gioi_tinh': 'Nam', 'ngay_sinh': '1940',
        'ngay_chet': '2000', 'so_giay_to': number, 'loai_giay_to': canonical,
        'ngay_cap': '2024-03-02', 'noi_cap': 'Ủy ban nhân dân thị trấn Mẫu',
        'dia_chi': 'Xóm Mẫu, thị trấn Mẫu', 'loai_dia_chi': 'Nơi chết',
    }
    assert person['fields']['so_giay_to']['source_refs'][0]['raw_snippet'] == number
    assert person['fields']['loai_giay_to']['source_refs'][0]['raw_snippet'] == source_type


def test_unknown_death_date_keeps_other_fields_and_does_not_derive_card(db, session_factory):
    suggestion, = read_people('Bà Trần Thị Mẫu, sinh năm 1945, đã chết; '
                             'Nơi chết tại: Xã Mẫu.')
    fields = values(suggestion)
    assert fields == {'ho_ten': 'Trần Thị Mẫu', 'gioi_tinh': 'Nữ', 'ngay_sinh': '1945',
                      'dia_chi': 'Xã Mẫu', 'loai_dia_chi': 'Nơi chết'}
    row = _person_row(**fields, ngay_chet=None, ngay_cap='2024')
    service = CaseWorkspaceService(db, None)
    created = service.create(str(uuid.uuid4()),
                             {'case_type': 'two_party', 'document_type': 'chuyen_nhuong'},
                             {'people': [row], 'assets': [_asset_row()]}, None)
    cid = created['case']['id']
    with session_factory() as fresh:
        saved, = CaseWorkspaceService(fresh, None).get(cid)['stage']['people']
        assert saved['ngay_chet'] is None
        assert saved['ngay_sinh'] == '1945'
        assert saved['ngay_cap'] == '2024'
        assert saved['loai_giay_to'] is None and saved['noi_cap'] is None
        assert saved['loai_dia_chi'] == 'Nơi chết'
        assert WordPerson(**{key: saved[key] for key in ('ngay_chet', 'loai_dia_chi')}).is_deceased


def test_separate_papers_same_issuer_date_stay_with_correct_person():
    items = read_people(
        'Ông Lê Văn Mẫu, sinh năm 1940, chết ngày 01/02/2000 theo Trích lục khai tử số 1/TLKT do UBND xã Mẫu cấp ngày 02/03/2024.',
        'Bà Trần Thị Mẫu, sinh năm 1945, chết ngày 03/04/2001 theo Trích lục khai tử số 2/TLKT do UBND xã Mẫu cấp ngày 02/03/2024.')
    by_name = {values(item)['ho_ten']: values(item) for item in items}
    assert by_name['Lê Văn Mẫu']['so_giay_to'] == '1/TLKT'
    assert by_name['Lê Văn Mẫu']['ngay_chet'] == '2000-02-01'
    assert by_name['Trần Thị Mẫu']['so_giay_to'] == '2/TLKT'
    assert by_name['Trần Thị Mẫu']['ngay_chet'] == '2001-04-03'


def test_shared_address_is_not_shared_paper():
    items = read_people(
        'Ông Lê Văn Mẫu và bà Trần Thị Mẫu; đã chết năm 2000 theo Trích lục khai tử số 1/TLKT do UBND xã Mẫu cấp ngày 02/03/2024; '
        'Cả hai có cùng nơi chết tại: Xã Mẫu.')
    by_name = {values(item)['ho_ten']: values(item) for item in items}
    assert set(by_name) == {'Lê Văn Mẫu', 'Trần Thị Mẫu'}
    for person in by_name.values():
        assert person['dia_chi'] == 'Xã Mẫu'
        assert 'so_giay_to' not in person and 'loai_giay_to' not in person


def test_cited_confirmation_does_not_suppress_another_valid_paper():
    items = read_people(
        'Ông Lê Văn Chờ, sinh năm 1930, chết năm 1990 theo Đơn xin xác nhận của UBND xã Mẫu.',
        'Bà Trần Thị Đủ, sinh năm 1945, chết năm 2001 theo Giấy chứng tử số 12, quyển 1 do UBND xã Mẫu cấp năm 2024.')
    person, = items
    assert values(person)['ho_ten'] == 'Trần Thị Đủ'
    assert values(person)['so_giay_to'] == '12, quyển 1'
    assert values(person)['ngay_cap'] == '2024'


def test_sources_never_enrich_each_other_and_ocr_numbers_do_not_match_across_files():
    first, = read_people('Ông Lê Văn Mẫu, sinh năm 1940, đã chết.')
    second, = read_people('Ông Lê Văn Mẫu, đã chết theo Trích lục khai tử số 1/TLKT do UBND xã Mẫu cấp năm 2024.')
    assert 'so_giay_to' not in values(first)
    assert 'ngay_sinh' not in values(second)
    people = _pair_persons([
        {'ho_ten': 'Lê Văn Mẫu', 'so_giay_to': '001234567890', 'ngay_sinh': '1940', '_files': ['first.png'], 'side': 'front'},
        {'ho_ten': 'Lê Văn Mẫu', 'so_giay_to': '001234567890', 'ngay_cap': '2024', '_files': ['second.png'], 'side': 'back'},
    ])
    assert [(person.get('ngay_sinh'), person.get('ngay_cap')) for person in people] == [('1940', ''), ('', '2024')]


def test_paper_collisions_repeat_save_and_explicit_id_do_not_cross_enrich(db, session_factory):
    service = CaseWorkspaceService(db, None)
    number = '12, quyển 1'
    people = [
        _person_row(ho_ten='Người giấy một', so_giay_to=number,
                    loai_giay_to='Giấy chứng tử', loai_dia_chi='Nơi chết',
                    noi_cap='UBND xã Một', ngay_cap='2024', ngay_sinh='1940'),
        _person_row(ho_ten='Người giấy hai', so_giay_to=number,
                    loai_giay_to='Giấy chứng tử', loai_dia_chi='Nơi chết',
                    noi_cap='UBND thị trấn Hai', ngay_cap='2023', ngay_sinh='1945'),
        _person_row(ho_ten='Người thẻ', so_giay_to=number),
    ]
    created = service.create(str(uuid.uuid4()),
        {'case_type': 'two_party', 'document_type': 'chuyen_nhuong'},
        {'people': people, 'assets': [_asset_row()]}, None)
    cid = created['case']['id']
    first_ids = [person['entity_id'] for person in created['stage']['people']]
    assert len(set(first_ids)) == 3
    stage = created['stage']
    for person in stage['people']:
        person['entity_id'] = None
    saved = service.commit_stage(cid, created['case']['revision'], stage)
    assert [person['entity_id'] for person in saved['stage']['people']] == first_ids
    assert db.query(Customer).filter_by(so_giay_to=number).count() == 3
    other = service.create(str(uuid.uuid4()),
        {'case_type': 'two_party', 'document_type': 'chuyen_nhuong'},
        {'people': [_person_row(ho_ten='Nguồn khác', so_giay_to=number)],
         'assets': [_asset_row()]}, None)
    assert other['stage']['people'][0]['entity_id'] not in first_ids
    assert other['stage']['people'][0]['noi_cap'] is None
    other['stage']['people'][0]['entity_id'] = first_ids[0]
    other['stage']['people'][0]['ho_ten'] = 'Tên sửa rõ ràng'
    service.commit_stage(other['case']['id'], other['case']['revision'], other['stage'])
    with session_factory() as fresh:
        original = CaseWorkspaceService(fresh, None).get(cid)['stage']['people']
        assert [person['entity_id'] for person in original] == first_ids
        assert original[0]['ho_ten'] == 'Người giấy một'
        assert original[0]['noi_cap'] == 'UBND xã Một'
        assert original[0]['so_giay_to'] == number
        assert original[0]['ngay_sinh'] == '1940'
        assert original[1]['noi_cap'] == 'UBND thị trấn Hai'


def test_router_create_and_update_require_explicit_id_not_number(db):
    from routers.customers import inline_create, quick_update
    import json
    form = dict(ho_ten='Người một', gioi_tinh=None, ngay_sinh=None, ngay_chet=None,
                so_giay_to='1/TLKT', ngay_cap=None, dia_chi=None, db=db)
    first = json.loads(inline_create(**form).body)['customer']
    form['ho_ten'] = 'Người hai'
    second = json.loads(inline_create(**form).body)['customer']
    assert first['id'] != second['id']
    form['ho_ten'] = 'Sửa người hai'
    changed = json.loads(quick_update(cid=second['id'], **form).body)['customer']
    assert changed['id'] == second['id']
    assert db.get(Customer, first['id']).ho_ten == 'Người một'
    assert db.get(Customer, second['id']).ho_ten == 'Sửa người hai'


def test_native_death_paper_separates_paper_from_personal_id_without_guessing_date():
    from services.document_intake.ocr_pipeline import _normalize_native_ocr_doc
    paper = _normalize_native_ocr_doc([
        'Ủy ban nhân dân thị trấn Mẫu', 'GIẤY CHỨNG TỬ (bản sao)',
        'Số: 12/2024, quyển số 1/2024', 'Họ và tên người chết: Lê Văn Mẫu',
        'Ngày sinh: 1940', 'Giấy tờ tùy thân: CCCD 012000000090',
        'Nơi chết: Xã Mẫu', 'Ngày cấp: 2024',
    ], 'controlled-paper.png')
    assert paper['data']['so_giay_to'] == '012000000090'
    assert paper['data']['so_trich_luc_khai_tu'] == '12/2024, quyển số 1/2024'
    assert paper['data']['loai_giay_to'] == 'Giấy chứng tử'
    assert paper['data']['ngay_chet'] == ''
    assert paper['data']['ngay_sinh'] == '1940'
    assert paper['data']['ngay_cap'] == ''
    assert paper['data']['noi_cap'] == ''
    assert paper['data']['ngay_ky'] == '2024'
    assert paper['data']['noi_cap_khai_tu'] == 'Ủy ban nhân dân thị trấn Mẫu'
    assert paper['data']['loai_dia_chi'] == 'Nơi chết'


def test_same_sentence_proper_paper_survives_unrelated_confirmation_citation():
    person, = read_people(
        'Ông Lê Văn Mẫu, sinh năm 1940, chết năm 2000 theo Trích lục khai tử số 1/TLKT '
        'do UBND xã Mẫu cấp năm 2024; ngoài ra có Đơn xin xác nhận khác.')
    result = values(person)
    assert result['ngay_sinh'] == '1940' and result['ngay_chet'] == '2000'
    assert result['so_giay_to'] == '1/TLKT'
    assert result['noi_cap'] == 'UBND xã Mẫu'
    assert result['ngay_cap'] == '2024'


def test_confirmation_dates_are_not_hints_but_independent_paper_still_is():
    person, = read_people(
        'Ông Lê Văn Mẫu, sinh năm 1940, chết năm 2000 theo Đơn xin xác nhận; '
        'theo Giấy chứng tử số 12, quyển 1 do UBND thị trấn Mẫu cấp năm 2024.')
    result = values(person)
    assert 'ngay_sinh' not in result and 'ngay_chet' not in result
    assert result['so_giay_to'] == '12, quyển 1'
    assert result['ngay_cap'] == '2024'
    assert result['noi_cap'] == 'UBND thị trấn Mẫu'
    assert result['loai_dia_chi'] == 'Nơi chết'


def test_conflicting_addresses_are_not_first_wins():
    person, = read_people('Ông Lê Văn Mẫu, đã chết; Nơi chết: Xã Một; '
                         'Nơi cư trú cuối cùng: Xã Hai.')
    assert 'dia_chi' not in values(person)
    assert any(warning['code'] == 'intake.ambiguous' for warning in person['warnings'])


def test_requester_excludes_explicit_unknown_date_deceased_only():
    from regex_workbench.engine.contract_extract import extract_text
    result = extract_text(
        'HỢP ĐỒNG CHUYỂN NHƯỢNG\nBên A:\n'
        'Ông Lê Văn Cố, sinh năm 1940, đã chết; Nơi chết: Xã Mẫu.\n'
        'Bên B:\nBà Trần Thị Sống, sinh năm 1980; CCCD: 001234567890; thường trú: Xã Mẫu.\n'
        'Điều 1: Nội dung')
    requester = result['web_form']['nguoi_yeu_cau']
    assert 'Lê Văn Cố' not in requester
    assert 'Trần Thị Sống' in requester


def test_same_container_distinct_cards_with_same_number_are_not_merged():
    people = _pair_persons([
        {'ho_ten': 'Lê Văn Một', 'so_giay_to': '001234567890', 'ngay_sinh': '1940',
         '_files': ['container.pdf#p1'], 'side': 'front'},
        {'ho_ten': 'Trần Văn Hai', 'so_giay_to': '001234567890', 'ngay_cap': '2024',
         '_files': ['container.pdf#p2'], 'side': 'back'},
    ])
    assert [(person['ho_ten'], person['ngay_sinh'], person['ngay_cap']) for person in people] == [
        ('Lê Văn Một', '1940', ''), ('Trần Văn Hai', '', '2024')]


@pytest.mark.parametrize('heading', ['ĐƠN XIN XÁC NHẬN.', 'ĐƠN XIN XÁC NHẬN: Nội dung'])
def test_confirmation_heading_punctuation_never_produces_person_hints(heading):
    from services.document_intake.models import SourceFailed
    with pytest.raises(SourceFailed):
        read_people('Ông Lê Văn Mẫu, sinh năm 1940, chết năm 2000 '
                    'theo Giấy chứng tử số 1 do UBND xã Mẫu cấp năm 2024.',
                    heading=heading)


def test_shared_address_does_not_leak_to_unrelated_previous_paragraph():
    people = read_people(
        'Ông Lê Văn Ngoài, sinh năm 1930, đã chết.',
        'Ông Lê Văn Một và bà Trần Thị Một; đã chết năm 2000; Cả hai có cùng nơi chết tại: Xã Một.',
        'Ông Lê Văn Hai và bà Trần Thị Hai; đã chết năm 2001; Cả hai có cùng nơi chết tại: Xã Hai.')
    result = {values(person)['ho_ten']: values(person) for person in people}
    assert 'dia_chi' not in result['Lê Văn Ngoài']
    assert result['Lê Văn Một']['dia_chi'] == result['Trần Thị Một']['dia_chi'] == 'Xã Một'
    assert result['Lê Văn Hai']['dia_chi'] == result['Trần Thị Hai']['dia_chi'] == 'Xã Hai'
