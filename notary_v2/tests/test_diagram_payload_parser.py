"""Biên web của workspace B: form tạo/sửa/stage-update ghi dòng case-owned.

Các helper parser/JSON Stage legacy đã bị xóa cùng cutover; test ở đây chỉ
kiểm hành vi biên còn sống: payload form được decode thành stage wire
row-keyed rồi đi qua `CaseWorkspaceService`, GET trả view từ rows, và hai
route lock/unlock chỉ còn tombstone 410.
"""
import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

import database
from fastapi import FastAPI
from fastapi.testclient import TestClient
from models import (
    CaseAssetRow,
    CasePersonRow,
    Customer,
    InheritanceCase,
    InheritanceParticipant,
    Property,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from routers import cases as cases_router


def _customer(cid: int, name: str) -> Customer:
    return Customer(id=cid, ho_ten=name)


def _property(pid: int) -> Property:
    return Property(id=pid, so_serial=f"SER-{pid}", dia_chi=f"Dia chi {pid}")


def _stage_row(row_id, name, *, doc="", dead=None):
    return {
        "row_id": row_id,
        "ho_ten": name,
        "gioi_tinh": "Nam",
        "ngay_sinh": "1950",
        "ngay_chet": dead.isoformat() if dead else None,
        "so_giay_to": doc,
        "ngay_cap": None,
        "noi_cap": "",
        "dia_chi": "",
        "place_of_origin": "",
    }


class CaseStateSchemaTests(unittest.TestCase):
    def test_inheritance_case_model_declares_case_state_json_column(self):
        self.assertIn("case_state_json", InheritanceCase.__table__.columns)
        column = InheritanceCase.__table__.columns["case_state_json"]
        self.assertEqual(str(column.type).upper(), "TEXT")

    def test_inheritance_cases_schema_migration_adds_case_state_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "legacy.db"
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE inheritance_cases (
                    id INTEGER PRIMARY KEY,
                    nguoi_chet_id INTEGER NOT NULL,
                    tai_san_id INTEGER NOT NULL,
                    ngay_lap_ho_so DATE NOT NULL
                )
                """
            )
            con.commit()
            con.close()

            original_db_path = database.DB_PATH
            try:
                database.DB_PATH = db_path
                database.migrate_inheritance_cases_schema()
            finally:
                database.DB_PATH = original_db_path

            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("PRAGMA table_info(inheritance_cases)")
            columns = {row[1] for row in cur.fetchall()}
            con.close()

        self.assertIn("case_state_json", columns)


class WebBoundaryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self._tmp.name) / 'web.db'}")
        database.Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        app = FastAPI()
        app.include_router(cases_router.router, prefix="/cases")

        def get_test_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[cases_router.get_db] = get_test_db
        self.client = TestClient(app)
        self.client.__enter__()
        with self.session_factory() as db:
            owner = Customer(ho_ten="Owner", so_giay_to="001",
                             name_anchor="owner", document_anchor="001",
                             ngay_chet=date(2024, 2, 3))
            child = Customer(ho_ten="Child", so_giay_to="002",
                             name_anchor="child", document_anchor="002")
            prop = Property(so_serial="WEB-1", dia_chi="Dia chi dat",
                            so_thua_dat="12")
            db.add_all([owner, child, prop])
            db.commit()
            self.owner_id, self.child_id = owner.id, child.id
            self.property_id = prop.id

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.engine.dispose()
        self._tmp.cleanup()

    def _form(self, stage_rows):
        return {
            "nguoi_chet_id": str(self.owner_id),
            "tai_san_id": str(self.property_id),
            "case_state_json": json.dumps(
                {"schemaVersion": 1, "stage": stage_rows, "diagram": {}},
                ensure_ascii=False),
        }

    def test_create_writes_case_rows_and_v4_payload(self):
        response = self.client.post("/cases/create", data=self._form([
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a11", "Owner",
                       doc="001", dead=date(2024, 2, 3)),
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a12", "Child",
                       doc="002"),
        ]), follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        with self.session_factory() as db:
            case = db.query(InheritanceCase).one()
            people = sorted(case.person_rows, key=lambda row: row.vitri)
            self.assertEqual([row.ho_ten for row in people], ["Owner", "Child"])
            self.assertEqual([row.customer_id for row in people],
                             [self.owner_id, self.child_id])
            self.assertEqual(len(case.asset_rows), 1)
            self.assertEqual(case.asset_rows[0].property_id, self.property_id)
            payload = json.loads(case.case_state_json)
            self.assertEqual(payload["schemaVersion"], 4)
            self.assertNotIn("stage", payload)
            self.assertEqual(payload["owner_row_id"], people[0].row_id)
            self.assertIsNone(case.engine_state_json)

    def test_edit_merges_rows_by_row_id_and_removes_dropped_row(self):
        self.client.post("/cases/create", data=self._form([
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a11", "Owner",
                       doc="001", dead=date(2024, 2, 3)),
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a12", "Child",
                       doc="002"),
        ]), follow_redirects=False)
        with self.session_factory() as db:
            case = db.query(InheritanceCase).one()
            case_id = case.id
            owner_row_id = case.person_rows[0].row_id

        response = self.client.post(f"/cases/{case_id}/edit", data={
            "nguoi_chet_id": str(self.owner_id),
            "tai_san_id": str(self.property_id),
            "case_state_json": json.dumps({"stage": [
                _stage_row(owner_row_id, "Owner đã sửa", doc="001",
                           dead=date(2024, 2, 3)),
                _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a13",
                           "Người mới", doc="003"),
            ]}, ensure_ascii=False),
            "ghi_chu": "ghi chú mới",
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        with self.session_factory() as db:
            case = db.get(InheritanceCase, case_id)
            self.assertEqual([row.ho_ten for row in case.person_rows],
                             ["Owner đã sửa", "Người mới"])
            self.assertEqual(case.ghi_chu, "ghi chú mới")
            self.assertEqual(case.workspace_revision, 2)
            self.assertEqual(db.query(Customer).filter_by(
                ho_ten="Child").count(), 1)  # danh bạ không bị xóa

    def test_stage_update_writes_rows_and_keeps_projection(self):
        self.client.post("/cases/create", data=self._form([
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a11", "Owner",
                       doc="001", dead=date(2024, 2, 3)),
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a12", "Child",
                       doc="002"),
        ]), follow_redirects=False)
        with self.session_factory() as db:
            case = db.query(InheritanceCase).one()
            case_id = case.id
            owner_row_id = case.person_rows[0].row_id

        response = self.client.post(f"/cases/{case_id}/stage-update", data={
            "case_state_json": json.dumps({"stage": [
                _stage_row(owner_row_id, "Owner", doc="001",
                           dead=date(2024, 2, 3))]}, ensure_ascii=False),
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        view = json.loads(body["case_state_json"])
        self.assertEqual([row["row_id"] for row in view["stage"]],
                         [owner_row_id])
        self.assertEqual(body["revision"], 2)

        with self.session_factory() as db:
            case = db.get(InheritanceCase, case_id)
            self.assertEqual([row.ho_ten for row in case.person_rows],
                             ["Owner"])
            payload = json.loads(case.case_state_json)
            self.assertNotIn("stage", payload)
            self.assertEqual(case.workspace_revision, 2)

    def test_lock_unlock_are_gone_and_do_not_touch_status(self):
        self.client.post("/cases/create", data=self._form([
            _stage_row("7f1e2b70-0f8a-4d3d-8f43-0d8a4f9c2a11", "Owner",
                       doc="001", dead=date(2024, 2, 3)),
        ]), follow_redirects=False)
        with self.session_factory() as db:
            case_id = db.query(InheritanceCase).one().id
            db.query(InheritanceCase).one().trang_thai = "done"
            db.commit()

        for action in ("lock", "unlock"):
            response = self.client.post(f"/cases/{case_id}/{action}")
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()["code"], "endpoint_deprecated")

        with self.session_factory() as db:
            self.assertEqual(
                db.get(InheritanceCase, case_id).trang_thai, "done")


if __name__ == "__main__":
    unittest.main()
