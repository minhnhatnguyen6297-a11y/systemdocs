"""Controlled legacy SQLite: retain identities, FK graph, history and custom DDL."""
import sqlite3

import pytest
from sqlalchemy import create_engine

import database
from models import Customer


DDL = '''
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten VARCHAR(200) NOT NULL,
    gioi_tinh VARCHAR(10), ngay_sinh DATE, ngay_chet DATE,
    so_giay_to VARCHAR(50) NOT NULL UNIQUE,
    ngay_cap DATE, dia_chi TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    local_note TEXT DEFAULT 'keep, literal' CHECK(length(local_note)>0),
    UNIQUE(ho_ten, so_giay_to)
);
CREATE INDEX customer_name_custom ON customers(ho_ten);
CREATE UNIQUE INDEX customer_number_custom ON customers(so_giay_to);
CREATE TABLE cases(id INTEGER PRIMARY KEY, owner_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
                   case_state_json TEXT);
CREATE TABLE participants(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id));
CREATE TABLE history(customer_id INTEGER REFERENCES customers(id), description TEXT);
CREATE TRIGGER retain_customer_history AFTER UPDATE OF ho_ten ON customers BEGIN
  INSERT INTO history VALUES(new.id, old.ho_ten);
END;
INSERT INTO customers(id,ho_ten,so_giay_to,created_at) VALUES(41,'Người trước','12, quyển 1','2000-01-02 03:04:05');
INSERT INTO customers(id,ho_ten,so_giay_to) VALUES(90,'Đã xóa','90');
DELETE FROM customers WHERE id=90;
INSERT INTO cases VALUES(1,41,'{"stage":[{"id":"41","ngay_sinh":"1940"}],"diagram":{"owner":"41"}}');
INSERT INTO participants VALUES(7,41);
INSERT INTO history VALUES(41,'Giữ lịch sử');
'''


def legacy(path):
    with sqlite3.connect(path) as con:
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript(DDL)


def snapshot(path):
    with sqlite3.connect(path) as con:
        return {table: con.execute(f'SELECT * FROM {table}').fetchall()
                for table in ('customers', 'cases', 'participants', 'history')}


def test_atomic_migration_preserves_ids_fk_snapshots_defaults_indexes_triggers(tmp_path, monkeypatch):
    path = tmp_path / 'controlled-legacy.db'
    legacy(path)
    before = snapshot(path)
    monkeypatch.setattr(database, 'DB_PATH', path)
    database.migrate_customers_document_number()
    assert snapshot(path) == before
    database.migrate_customers_document_number()
    assert snapshot(path) == before
    with sqlite3.connect(path) as con:
        con.execute('PRAGMA foreign_keys=ON')
        assert con.execute('PRAGMA foreign_keys').fetchone() == (1,)
        assert con.execute('PRAGMA foreign_key_check').fetchall() == []
        con.execute("INSERT INTO customers(ho_ten,so_giay_to) VALUES('Người khác','12, quyển 1')")
        row = con.execute("SELECT id,local_note FROM customers WHERE ho_ten='Người khác'").fetchone()
        assert row[0] > 90 and row[1] == 'keep, literal'
        con.execute("INSERT INTO customers(ho_ten) VALUES('Chưa có giấy')")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO customers(ho_ten,so_giay_to) VALUES('Người khác','12, quyển 1')")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO customers(ho_ten,local_note) VALUES('Sai check','')")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute('INSERT INTO participants VALUES(8,9999)')
        con.execute("UPDATE customers SET ho_ten='Người sau' WHERE id=41")
        assert con.execute('SELECT description FROM history WHERE customer_id=41').fetchall() == [('Giữ lịch sử',), ('Người trước',)]
        indexes = {row[1]: row[2] for row in con.execute('PRAGMA index_list(customers)')}
        assert indexes['customer_name_custom'] == 0
        assert indexes['customer_number_custom'] == 0
        assert indexes['ix_customers_so_giay_to'] == 0
        assert con.execute('SELECT owner_id,case_state_json FROM cases').fetchone() == before['cases'][0][1:]


def test_failure_rolls_back_schema_rows_and_fk_graph(tmp_path, monkeypatch):
    path = tmp_path / 'controlled-failure.db'
    legacy(path)
    with sqlite3.connect(path) as con:
        con.execute('CREATE VIEW customers_document_new AS SELECT 1')
        ddl = con.execute("SELECT type,name,sql FROM sqlite_master ORDER BY name").fetchall()
    before = snapshot(path)
    monkeypatch.setattr(database, 'DB_PATH', path)
    with pytest.raises(sqlite3.Error):
        database.migrate_customers_document_number()
    assert snapshot(path) == before
    with sqlite3.connect(path) as con:
        assert con.execute("SELECT type,name,sql FROM sqlite_master ORDER BY name").fetchall() == ddl
        assert con.execute('PRAGMA foreign_key_check').fetchall() == []


def test_fresh_schema_and_repeat_bootstrap_allow_number_collisions(tmp_path, monkeypatch):
    path = tmp_path / 'controlled-fresh.db'
    engine = create_engine(f'sqlite:///{path.as_posix()}')
    database.enable_sqlite_foreign_keys(engine)
    database.Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setattr(database, 'DB_PATH', path)
    database.migrate_customers_document_number()
    database.migrate_customers_document_number()
    with sqlite3.connect(path) as con:
        con.executemany('INSERT INTO customers(ho_ten,so_giay_to) VALUES(?,?)',
                        [('Người một','1/TLKT'),('Người hai','1/TLKT')])
        assert con.execute('SELECT ho_ten,so_giay_to FROM customers ORDER BY id').fetchall() == [('Người một','1/TLKT'),('Người hai','1/TLKT')]
        assert con.execute('PRAGMA foreign_key_check').fetchall() == []
