"""Case metadata derives assigned owners, not legacy deceased-owner force flags."""
import json
from copy import deepcopy

from sqlalchemy.orm import sessionmaker

from services.case_workspace import CaseWorkspaceService
from services.word_engine import committed_landowner_names
from tests.test_case_metadata import db, _create_args, _node


def test_assigned_owner_not_deceased_anchor_fresh_reopen(db):
    args = _create_args(with_state=True, case_meta={
        "case_type": "inheritance", "document_type": "khai_nhan",
        "ngay_lap_ho_so": "2026-10-19", "ngaycongchung": "2026-06-15",
        "socongchung": "007/2026", "tenvanban": "Văn bản nguồn",
        "nhomhopdong": "Nhóm portal", "loaivanbannhandien": "inheritance_declaration",
        "congchungvien": "CCV nguồn", "thuky": "Thư ký nguồn",
    })
    args["state"]["nodes"][0]["ownPositions"] = []
    args["state"]["nodes"][1]["ownPositions"] = [1]
    data = CaseWorkspaceService(db).create(**args)
    cid = data["case"]["id"]
    assert data["case"]["chudat"] == "Trần Thị Sống"
    fresh = sessionmaker(bind=db.bind)()
    try:
        reopened = CaseWorkspaceService(fresh).get(cid)
        assert reopened["case"]["chudat"] == "Trần Thị Sống"
        assert reopened["case"]["ngaycongchung"] == "2026-06-15"
        assert reopened["case"]["ngay_lap_ho_so"] == "2026-10-19"
        assert reopened["case"]["socongchung"] == "007/2026"
        assert reopened["case"]["tenvanban"] == "Văn bản nguồn"
        # A Stage commit preserves scalar metadata and updates names by row ID.
        stage = reopened["stage"]
        stage["people"][1]["ho_ten"] = "Tên được cập nhật"
        CaseWorkspaceService(fresh).commit_stage(cid, reopened["case"]["revision"], stage)
        assert CaseWorkspaceService(fresh).get(cid)["case"]["chudat"] == "Tên được cập nhật"
        assert CaseWorkspaceService(fresh).get(cid)["case"]["ngaycongchung"] == "2026-06-15"
    finally:
        fresh.close()


def test_deceased_without_assignment_is_null(db):
    args = _create_args(with_state=True)
    args["state"]["nodes"][0]["ownPositions"] = []
    data = CaseWorkspaceService(db).create(**args)
    assert data["case"]["chudat"] is None
    assert CaseWorkspaceService(db).get(data["case"]["id"])["case"]["chudat"] is None


def test_projection_stage_order_row_identity_hidden_deleted_and_real_positions():
    payload = {
        "stage": [{"row_id": "a", "id": "1", "ho_ten": "Trùng Tên"},
                  {"row_id": "b", "id": "2", "ho_ten": "Trùng Tên"},
                  {"row_id": "c", "id": "3", "ho_ten": "Ẩn"},
                  {"row_id": "d", "id": "4", "ho_ten": "Xóa"},
                  {"row_id": "e", "id": "5", "ho_ten": "Sai vị trí"}],
        "assets": [{}],
        "diagram": {"state": {"domain": "inheritance", "nodes": [
            _node("b", "b", own=[1]), _node("a", "a", own=[1]),
            {**_node("c", "c", own=[1]), "hidden": True},
            {**_node("d", "d", own=[1]), "deleted": True},
            _node("e", "e", own=[2, 0, True]),
        ]}},
    }
    assert committed_landowner_names(payload) == "Trùng Tên\nTrùng Tên"
    payload["assets"] = []
    assert committed_landowner_names(payload) is None
    payload["diagram"]["state"]["domain"] = "two_party"
    assert committed_landowner_names(payload) is None
    assert committed_landowner_names({"stage": payload["stage"], "assets": [{}]}) is None
