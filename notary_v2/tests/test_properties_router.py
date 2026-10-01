"""MIN-141 — route /properties trực tiếp qua TestClient.

- create/edit không còn nhận/ghi `thoi_han` lẻ — kể cả khi client cũ
  gửi kèm; edit giữ nguyên giá trị lịch sử `properties.thoi_han`.
- Form dict của create/edit không còn mang `thoi_han`; template không
  render ô nhập, chỉ block read-only cho giá trị cũ.
- inline-create ghi thời hạn theo cụm `property_land_rows[].thoihan`,
  không mirror sang cột lẻ.

Dùng SQLite in-memory (StaticPool) + dependency_overrides[get_db] —
không chạm notary.db thật.

Ghi chú env dev: starlette cài đặt mới hơn pin requirements.txt
(fastapi==0.111.0) nên `TemplateResponse(name, context)` kiểu cũ không
render được — các test GET form stub `properties_router.templates` để
bắt context (vẫn đi qua route function thật), cộng assert tĩnh trên
file template. POST create/edit/inline-create trả Redirect/JSON nên
không bị ảnh hưởng.
"""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
from database import get_db
from models import Property, PropertyLandRow
from routers import properties as properties_router

TEMPLATE = (Path(__file__).resolve().parent.parent
            / "frontend" / "templates" / "properties" / "form.html")


@pytest.fixture()
def client_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False,
                           autoflush=False)

    app = FastAPI()
    app.include_router(properties_router.router, prefix="/properties")

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, factory
    engine.dispose()


class _CaptureTemplates:
    """Bắt context TemplateResponse thay vì render (xem docstring module
    về lệch phiên bản starlette trong env dev)."""

    def __init__(self):
        self.calls = []

    def TemplateResponse(self, name, context, *args, **kwargs):
        self.calls.append({"name": name, "context": context})
        return JSONResponse({
            "template": name,
            "form": context.get("form"),
            "obj_thoi_han": getattr(context.get("obj"), "thoi_han", None),
        })


def _create_form(serial="RT100001", **over):
    data = {"so_serial": serial, "dia_chi": "Thửa 1, xã A",
            "dien_tich": "100", "loai_dat": "ODT"}
    data.update(over)
    return data


# --------------------------------------------------------------- template


def test_form_template_has_no_thoi_han_input():
    src = TEMPLATE.read_text(encoding="utf-8")
    assert 'name="thoi_han"' not in src
    # giá trị lịch sử chỉ hiển thị read-only khi đang sửa
    assert "{% if obj and obj.thoi_han %}" in src
    assert "{{ obj.thoi_han }}" in src


def test_create_form_context_has_no_thoi_han(client_factory, monkeypatch):
    client, _ = client_factory
    stub = _CaptureTemplates()
    monkeypatch.setattr(properties_router, "templates", stub)
    resp = client.get("/properties/create")
    assert resp.status_code == 200
    assert resp.json()["form"] is not None
    assert "thoi_han" not in resp.json()["form"]


def test_edit_form_context_no_thoi_han_but_obj_keeps_history(
        client_factory, monkeypatch):
    """Edit form: form dict không có thoi_han; obj vẫn được truyền để
    template hiển thị giá trị lịch sử read-only."""
    client, factory = client_factory
    db = factory()
    prop = Property(so_serial="RT200001", dia_chi="Thửa 2",
                    thoi_han="Lâu dài")
    db.add(prop); db.commit()
    pid = prop.id
    db.close()

    stub = _CaptureTemplates()
    monkeypatch.setattr(properties_router, "templates", stub)
    resp = client.get(f"/properties/{pid}/edit")
    assert resp.status_code == 200
    assert "thoi_han" not in resp.json()["form"]
    assert resp.json()["obj_thoi_han"] == "Lâu dài"


# ---------------------------------------------------------------- create


def test_create_route_does_not_write_standalone_thoi_han(client_factory):
    """POST create không gửi thoi_han → property mới thoi_han IS NULL."""
    client, factory = client_factory
    resp = client.post("/properties/create", data=_create_form(),
                             follow_redirects=False)
    assert resp.status_code == 302
    db = factory()
    prop = db.query(Property).filter_by(so_serial="RT100001").one()
    assert prop.thoi_han is None
    db.close()


def test_create_ignores_legacy_client_thoi_han(client_factory):
    """Client cũ vẫn gửi kèm field lẻ → bị bỏ qua, không ghi cột lẻ."""
    client, factory = client_factory
    resp = client.post("/properties/create",
                       data=_create_form(serial="RT100002",
                                         thoi_han="50 năm"),
                       follow_redirects=False)
    assert resp.status_code == 302
    db = factory()
    prop = db.query(Property).filter_by(so_serial="RT100002").one()
    assert prop.thoi_han is None
    db.close()


# ------------------------------------------------------------------ edit


def test_edit_omitted_thoi_han_preserves_history(client_factory):
    """POST edit không gửi thoi_han → giá trị lịch sử giữ nguyên, các
    field khác vẫn cập nhật."""
    client, factory = client_factory
    db = factory()
    prop = Property(so_serial="RT200002", dia_chi="Địa chỉ cũ",
                    thoi_han="Đến 2043")
    db.add(prop); db.commit()
    pid = prop.id
    db.close()

    resp = client.post(f"/properties/{pid}/edit",
                       data=_create_form(serial="RT200002",
                                         dia_chi="Địa chỉ mới"),
                       follow_redirects=False)
    assert resp.status_code == 302
    db = factory()
    prop = db.get(Property, pid)
    assert prop.thoi_han == "Đến 2043"       # lịch sử không mất
    assert prop.dia_chi == "Địa chỉ mới"
    db.close()


def test_edit_ignores_legacy_client_thoi_han(client_factory):
    """Client cũ gửi thoi_han trong POST edit → bị bỏ qua, không ghi đè
    giá trị lịch sử."""
    client, factory = client_factory
    db = factory()
    prop = Property(so_serial="RT200003", dia_chi="a",
                    thoi_han="Lâu dài")
    db.add(prop); db.commit()
    pid = prop.id
    db.close()

    resp = client.post(f"/properties/{pid}/edit",
                       data=_create_form(serial="RT200003",
                                         thoi_han="Đến 2099"),
                       follow_redirects=False)
    assert resp.status_code == 302
    db = factory()
    assert db.get(Property, pid).thoi_han == "Lâu dài"
    db.close()


# ---------------------------------------------------------- inline-create


def test_inline_create_stores_term_only_in_land_rows(client_factory):
    """inline-create: thời hạn mới chỉ nằm trong cụm đất — bảng con +
    mirror land_rows_json đúng, cột lẻ NULL."""
    client, factory = client_factory
    rows = [{"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
            {"loai_dat": "CLN", "dien_tich": 50.5, "thoi_han": "50 năm"}]
    resp = client.post("/properties/inline-create",
                       data={"so_serial": "RT300001",
                             "dia_chi": "Thửa 3, xã B",
                             "land_rows": json.dumps(rows,
                                                     ensure_ascii=False)})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    db = factory()
    prop = db.query(Property).filter_by(so_serial="RT300001").one()
    assert prop.thoi_han is None             # không ghi giá trị lẻ
    assert [(r.vitri, r.loaidat, r.dientich, r.thoihan)
            for r in db.query(PropertyLandRow)
            .filter_by(property_id=prop.id)
            .order_by(PropertyLandRow.vitri)] == [
        (1, "ODT", 80.0, "Lâu dài"),
        (2, "CLN", 50.5, "50 năm"),
    ]
    assert json.loads(prop.land_rows_json) == [
        {"loai_dat": "ODT", "dien_tich": 80, "thoi_han": "Lâu dài"},
        {"loai_dat": "CLN", "dien_tich": 50.5, "thoi_han": "50 năm"}]
    assert prop.dien_tich == 130.5           # tổng diện tích các cụm
    db.close()
