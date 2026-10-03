from datetime import date
from tests import test_case_metadata as t
from tests.test_case_metadata import db


def test_canonical_person_token_preserves_confirmed_death_evidence(db):
    data = t._create(db, with_state=True, people_overrides=({
        'loai_giay_to': 'Giấy chứng tử', 'noi_cap': 'UBND X'},))
    case = db.get(t.InheritanceCase, data['case']['id'])
    mapping = t.word_engine.build_template_mapping(case)
    assert mapping['[loaigiayto1]'] == 'Giấy chứng tử'
    assert mapping['[noicap1]'] == 'UBND X'


def test_derived_fields_ignore_other_case_master_edits(db):
    data = t._create(db, people_overrides=({}, {'ngay_cap': '2024-09-30'}))
    stage = data['stage']
    # Another consumer updates the shared master after this case committed.
    person = db.get(t.Customer, stage['people'][1]['entity_id'])
    person.ngay_cap = date(2024, 10, 1)
    db.commit()
    stage['people'][1]['ngay_cap'] = '2024-10-02'
    result = t._commit(db, data['case']['id'], data['case']['revision'], stage)
    assert result['stage']['people'][1]['loai_giay_to'] == 'Căn cước'
