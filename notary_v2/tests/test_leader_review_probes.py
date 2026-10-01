"""Leader review probes — MIN-141 đợt 2 (comment review 01a0f6c8).

Ba probe Leader đính kèm trong review `7c43bef`; giữ nguyên nội dung để
regression. Fixture/helper dùng lại của test_property_land_rows.
"""
import json
from tests import test_property_land_rows as t
from tests.test_property_land_rows import db, session_factory, legacy_db


def test_reopen_keeps_same_asset_as_word(db):
    t.test_two_cases_sharing_property_word_uses_own_snapshot(db)
    case = db.query(t.InheritanceCase).order_by(t.InheritanceCase.id).first()
    word = t.word_engine.build_template_mapping(case)
    reopened = t.CaseWorkspaceService(db).get(case.id)
    assert reopened['stage']['assets'][0]['land_rows'][0]['loai_dat'] == word['[loaidat11]']


def test_migration_reports_object_field_instead_of_crashing(legacy_db):
    _, con = legacy_db
    t._insert_property(con, json.dumps([{'loai_dat': {'bad': 'type'}, 'dien_tich': 5}]))
    report = t.database.migrate_property_land_rows(con)
    assert report['anomalies']


def test_overflow_warning_survives_successful_backfill(db):
    people, assets, state = t._create_args()
    created = t._create(db, people, assets, state)
    prop = db.get(t.Property, created['stage']['assets'][0]['entity_id'])
    prop.land_rows = []
    db.flush()
    prop.land_rows = [t.PropertyLandRow(vitri=i+1, loaidat='X', dientich=1) for i in range(25)]
    prop.land_rows_json = json.dumps([{'loai_dat': 'X', 'dien_tich': 1}] * 25)
    db.commit()
    result = t.CaseWorkspaceService(db).get(created['case']['id'])
    assert 'stage.legacy_land_rows_overflow' in t._land_warning_codes(result)
