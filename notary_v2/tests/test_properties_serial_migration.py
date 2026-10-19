"""Migration `properties.so_serial` → nullable, non-unique (issue #40)."""
import sqlite3
import pytest
from sqlalchemy import create_engine

import database
from models import Property


LEGACY_DDL = """
PRAGMA foreign_keys=off;
CREATE TABLE properties (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    so_serial         VARCHAR(100) NOT NULL UNIQUE,
    so_vao_so         VARCHAR(100),
    so_thua_dat       VARCHAR(100),
    so_to_ban_do      VARCHAR(100),
    dia_chi           TEXT NOT NULL,
    loai_dat          VARCHAR(100),
    dien_tich         FLOAT,
    loai_so           VARCHAR(200),
    land_rows_json    TEXT,
    hinh_thuc_su_dung VARCHAR(100),
    thoi_han          VARCHAR(100),
    nguon_goc         TEXT,
    ngay_cap          DATE,
    co_quan_cap       VARCHAR(200),
    created_at        DATETIME DEFAULT (CURRENT_TIMESTAMP)
);
CREATE TABLE inheritance_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);
CREATE TABLE inheritance_case_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(case_id) REFERENCES inheritance_cases(id),
    FOREIGN KEY(property_id) REFERENCES properties(id)
);
CREATE TABLE property_land_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    vitri INTEGER NOT NULL,
    loaidat VARCHAR(200),
    dientich FLOAT,
    thoihan VARCHAR(200),
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(property_id) REFERENCES properties(id)
);
PRAGMA foreign_keys=on;
"""


def _legacy_db(path):
    con = sqlite3.connect(path)
    con.executescript(LEGACY_DDL)
    con.execute("INSERT INTO inheritance_cases (id) VALUES (1)")
    con.execute("INSERT INTO inheritance_cases (id) VALUES (2)")
    for pid, serial, thua in ((7, "raw legacy 12/34", "123"),
                              (9, "DD123456", "456"),
                              (11, "", "789")):
        con.execute(
            "INSERT INTO properties (id, so_serial, so_thua_dat, dia_chi, "
            "ngay_cap, created_at) VALUES (?,?,?,?,?,?)",
            (pid, serial, thua, f"Thửa {thua}", "2020-01-02",
             "2026-01-01 00:00:00"))
    con.execute(
        "INSERT INTO inheritance_case_properties (case_id, property_id, is_primary) "
        "VALUES (1, 7, 1), (2, 9, 0)")
    con.execute(
        "INSERT INTO property_land_rows (property_id, vitri, loaidat, dientich) "
        "VALUES (7, 1, 'ODT', 80), (9, 1, 'CLN', 120)")
    con.commit()
    con.close()


def _snapshot(path):
    con = sqlite3.connect(path)
    try:
        props = con.execute(
            "SELECT id, so_serial, so_thua_dat, dia_chi, ngay_cap, created_at "
            "FROM properties ORDER BY id").fetchall()
        links = con.execute(
            "SELECT id, case_id, property_id, is_primary "
            "FROM inheritance_case_properties ORDER BY id").fetchall()
        land = con.execute(
            "SELECT id, property_id, vitri, loaidat, dientich "
            "FROM property_land_rows ORDER BY id").fetchall()
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        con.close()
    return props, links, land, fk


def _columns(path):
    con = sqlite3.connect(path)
    try:
        return {row[1]: row for row in
                con.execute("PRAGMA table_info(properties)")}
    finally:
        con.close()


def _all_indexes(path):
    con = sqlite3.connect(path)
    try:
        return {row[1] for row in con.execute("PRAGMA index_list(properties)")}
    finally:
        con.close()


def _unique_serial_indexes(path):
    con = sqlite3.connect(path)
    found = []
    try:
        for row in con.execute("PRAGMA index_list(properties)"):
            if not row[2]:
                continue
            cols = [r[2] for r in
                    con.execute(f'PRAGMA index_info("{row[1]}")')]
            if "so_serial" in cols:
                found.append((row[1], cols))
    finally:
        con.close()
    return found


def test_migration_preserves_ids_values_links_and_land_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    _legacy_db(db_path)
    before = _snapshot(db_path)

    database.migrate_properties_serial()

    assert "so_serial" in _columns(db_path)
    assert _columns(db_path)["so_serial"][3] == 0       # notnull = 0
    assert _unique_serial_indexes(db_path) == []
    assert "ix_properties_id" in _all_indexes(db_path)
    assert _snapshot(db_path) == before
    assert before[3] == []                              # FK check clean
    assert _columns(db_path)["dia_chi"][3] == 1         # NOT NULL giữ nguyên


def test_migration_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    _legacy_db(db_path)

    database.migrate_properties_serial()
    first = _snapshot(db_path)
    database.migrate_properties_serial()
    assert _snapshot(db_path) == first


def test_migration_allows_existing_duplicate_serials(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    con = sqlite3.connect(db_path)
    con.executescript(LEGACY_DDL.replace(" NOT NULL UNIQUE", " NOT NULL"))
    con.execute(
        "INSERT INTO properties (id, so_serial, dia_chi) VALUES "
        "(21, 'DD123456', 'Thửa 1'), (22, 'DD123456', 'Thửa 2')")
    con.commit()
    con.close()

    database.migrate_properties_serial()

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, so_serial FROM properties ORDER BY id").fetchall()
        assert rows == [(21, "DD123456"), (22, "DD123456")]
        assert _unique_serial_indexes(db_path) == []
    finally:
        con.close()


def test_migration_failure_leaves_legacy_db_untouched(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    _legacy_db(db_path)
    before = _snapshot(db_path)
    before_columns = _columns(db_path)
    con = sqlite3.connect(db_path)
    con.execute("CREATE VIEW properties_serial_new AS SELECT 1 AS x")
    con.commit()
    con.close()

    with pytest.raises(sqlite3.Error):
        database.migrate_properties_serial()

    assert _snapshot(db_path) == before
    assert _columns(db_path) == before_columns
    assert _unique_serial_indexes(db_path) != []


def test_fresh_schema_is_nullable_non_unique_and_migration_noops(tmp_path, monkeypatch):
    db_path = tmp_path / "fresh.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    database.Base.metadata.create_all(engine)
    engine.dispose()

    database.migrate_properties_serial()

    assert _columns(db_path)["so_serial"][3] == 0
    assert _unique_serial_indexes(db_path) == []
    with sqlite3.connect(db_path) as con:
        con.execute("INSERT INTO properties (so_serial, dia_chi) VALUES (?, ?)",
                    ("", "Thửa 0"))
        con.execute("INSERT INTO properties (so_serial, dia_chi) VALUES (?, ?)",
                    ("", "Thửa 0b"))
        assert con.execute(
            "SELECT COUNT(*) FROM properties WHERE so_serial=''").fetchone()[0] == 2
        assert con.execute(
            "SELECT COUNT(*) FROM properties WHERE so_serial IS NULL").fetchone()[0] == 0
        serial = Property.__table__.c.so_serial
        assert serial.nullable is True
        assert serial.unique in (None, False)
