import json
import logging
import math
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Dùng SQLite — file notary.db tự tạo trong thư mục dự án
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "notary.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def enable_sqlite_foreign_keys(sqlalchemy_engine):
    event.listen(sqlalchemy_engine, "connect", _enable_sqlite_foreign_keys)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
enable_sqlite_foreign_keys(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def assert_foreign_key_check():
    con = sqlite3.connect(DB_PATH)
    try:
        violation = con.execute("PRAGMA foreign_key_check").fetchone()
    finally:
        con.close()
    if violation:
        raise RuntimeError("SQLite foreign key check failed")


def migrate_customers_nullable():
    """Chuyển các cột customers (trừ ho_ten) sang nullable nếu chưa có."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='customers'")
    row = cur.fetchone()
    if row and "NOT NULL" in row[0]:
        cur.executescript("""
            PRAGMA foreign_keys=off;
            BEGIN;
            CREATE TABLE customers_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ho_ten      VARCHAR(200) NOT NULL,
                gioi_tinh   VARCHAR(10),
                ngay_sinh   DATE,
                ngay_chet   DATE,
                so_giay_to  VARCHAR(50) UNIQUE,
                ngay_cap    DATE,
                dia_chi     TEXT,
                created_at  DATETIME DEFAULT (CURRENT_TIMESTAMP)
            );
            INSERT INTO customers_new SELECT id,ho_ten,gioi_tinh,ngay_sinh,ngay_chet,so_giay_to,ngay_cap,dia_chi,created_at FROM customers;
            DROP TABLE customers;
            ALTER TABLE customers_new RENAME TO customers;
            COMMIT;
            PRAGMA foreign_keys=on;
        """)
    con.close()


def _ensure_table_columns(cur, table_name: str, expected_columns: dict[str, str]):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    if cur.fetchone() is None:
        return

    cur.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cur.fetchall()}
    for column_name, column_sql in expected_columns.items():
        if column_name not in existing_columns:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def migrate_inheritance_cases_schema():
    """Them cac cot moi cho cac bang thua ke tren DB cu."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    _ensure_table_columns(cur, "inheritance_cases", {
        "noi_niem_yet": "VARCHAR(200)",
        "nguoi_nhan_uy_quyen": "VARCHAR(200)",
        "noi_dung_viec": "TEXT",
        "engine_state_json": "TEXT",
        "case_state_json": "TEXT",
        "workspace_revision": "INTEGER NOT NULL DEFAULT 1",
        "workspace_idempotency_key": "VARCHAR(64)",
        "updated_at": "DATETIME",
    })
    _ensure_table_columns(cur, "inheritance_participants", {
        "parent_customer_id": "INTEGER",
    })
    con.commit()
    con.close()


def migrate_properties_schema():
    """Them cac cot moi cho bang properties tren DB cu."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    _ensure_table_columns(cur, "properties", {
        "dien_tich": "FLOAT",
        "loai_so": "VARCHAR(200)",
        "land_rows_json": "TEXT",
    })
    con.commit()
    con.close()


# Bí danh key cụm đất: tên nghiệp vụ mới (canonical, MIN-141) → key JSON/wire
# legacy. Giữ nguyên cả hai khi đọc; cả hai cùng có giá trị mâu thuẫn → lỗi.
_LAND_FIELD_ALIASES = (
    ("loaidat", "loai_dat"),
    ("dientich", "dien_tich"),
    ("thoihan", "thoi_han"),
)
# Giới hạn cụm đất/tài sản trên Stage (entities.md §9.2).
MAX_LAND_ROWS = 20


def _land_value_present(value) -> bool:
    """Giá trị 'có' khi non-None và (chuỗi → khác rỗng sau strip)."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _land_row_field(row: dict, new_key: str, old_key: str):
    """Đọc một trường cụm đất theo bí danh cũ/mới.

    → (value, conflict). Mâu thuẫn = cả hai key đều có giá trị và giá trị
    khác nhau (chuỗi so sau strip, số so theo giá trị) — caller báo lỗi,
    không âm thầm chọn một (AC MIN-141 đợt 2)."""
    new_v, old_v = row.get(new_key), row.get(old_key)
    if not (_land_value_present(new_v) and _land_value_present(old_v)):
        return (new_v if _land_value_present(new_v) else old_v), False

    def _norm(v):
        return v.strip() if isinstance(v, str) else v

    return new_v, _norm(new_v) != _norm(old_v)


def _land_area_to_float(value):
    """dientich/dien_tich → float|None. bool, chuỗi không parse được,
    số/chuỗi không hữu hạn (inf/nan) và kiểu không hỗ trợ → raise
    ValueError (caller ghi anomaly, giữ nguyên bản gốc — không âm thầm
    ép giá trị sai về NULL)."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("dien_tich bool không hợp lệ")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        result = float(text)  # ValueError → anomaly
    else:
        raise ValueError(f"unsupported dien_tich type {type(value).__name__}")
    if not math.isfinite(result):
        raise ValueError("dien_tich không hữu hạn")
    return result


def migrate_property_land_rows(con=None):
    """Tạo bảng con ``property_land_rows`` và backfill từ
    ``properties.land_rows_json`` (MIN-141 đợt 2).

    - Idempotent: tài sản đã có dòng trong bảng con → bỏ qua, không nhân đôi.
    - Bảo toàn giá trị, thứ tự và vị trí trống: mọi phần tử mảng JSON thành
      một dòng ``vitri`` = chỉ số mảng + 1; dòng rỗng → NULL cả ba cột.
    - JSON lỗi / không phải mảng / dòng không phải object / key cũ-mới mâu
      thuẫn / dien_tich không parse được → bỏ qua tài sản đó, giữ nguyên
      land_rows_json, ghi anomaly trong report — không bỏ qua/cắt cụt rồi
      báo thành công.
    - Mảng vượt ``MAX_LAND_ROWS``: vẫn ghi đủ tất cả dòng để không mất dữ
      liệu, đồng thời ghi anomaly ``over_limit`` cần đối chiếu.
    - ``properties.thoi_han`` lẻ không trùng ``thoihan`` cụm nào → ghi
      anomaly ``orphan_thoi_han``, giữ nguyên bản gốc, không tự đoán cụm.
    - Không DROP/UPDATE ``land_rows_json`` trong bước chuyển đổi này.

    ``con`` có thể truyền sqlite3.Connection tới DB khác (test/sidecar);
    trả về report dict {table_created, scanned, backfilled, rows_inserted,
    skipped_existing, empty, anomalies}.
    """
    own_con = con is None
    if own_con:
        con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    report = {
        "table_created": False,
        "scanned": 0,
        "backfilled": 0,
        "rows_inserted": 0,
        "skipped_existing": 0,
        "empty": 0,
        "anomalies": [],
    }

    def anomaly(property_id, code, detail):
        report["anomalies"].append(
            {"property_id": property_id, "code": code, "detail": detail})
        logger.warning(
            "property_land_rows migration: property=%s %s — %s",
            property_id, code, detail)

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='property_land_rows'")
    if cur.fetchone() is None:
        report["table_created"] = True
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS property_land_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            vitri INTEGER NOT NULL,
            loaidat VARCHAR(200),
            dientich FLOAT,
            thoihan VARCHAR(200),
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(property_id) REFERENCES properties(id),
            CONSTRAINT uq_property_land_row_vitri
                UNIQUE (property_id, vitri)
        );
        CREATE INDEX IF NOT EXISTS ix_property_land_rows_property_id
        ON property_land_rows(property_id);
    """)

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='properties'")
    if cur.fetchone() is None:
        # DB mới tinh — properties sẽ do create_all tạo sau; không có gì
        # để backfill.
        con.commit()
        if own_con:
            con.close()
        return report

    cur.execute("PRAGMA table_info(properties)")
    prop_columns = {r[1] for r in cur.fetchall()}
    if "land_rows_json" not in prop_columns:
        # DB rất cũ chưa có cột JSON — gọi migrate_properties_schema
        # trước; không có gì để backfill.
        con.commit()
        if own_con:
            con.close()
        return report

    try:
        _migrate_property_land_rows_scan(cur, prop_columns, report, anomaly)
        con.commit()
    except Exception:
        # Lỗi bất ngờ (DB, FK, …): rollback sạch, đóng connection nếu
        # hàm tự mở, rồi raise — không để transaction treo nửa chừng.
        con.rollback()
        raise
    finally:
        if own_con:
            con.close()
    if own_con:
        assert_foreign_key_check()
    return report


def _migrate_property_land_rows_scan(cur, prop_columns, report, anomaly):
    """Quét properties và backfill property_land_rows — phần thân của
    migrate_property_land_rows, tách ra để caller bọc try/rollback."""
    cur.execute(
        "SELECT id, land_rows_json, thoi_han FROM properties ORDER BY id"
        if "thoi_han" in prop_columns else
        "SELECT id, land_rows_json, NULL FROM properties ORDER BY id")
    for property_id, json_text, thoi_han in cur.fetchall():
        report["scanned"] += 1
        cur.execute(
            "SELECT COUNT(*) FROM property_land_rows WHERE property_id=?",
            (property_id,))
        existing = cur.fetchone()[0]
        cluster_terms = []
        if existing:
            report["skipped_existing"] += 1
            cur.execute(
                "SELECT thoihan FROM property_land_rows WHERE property_id=?",
                (property_id,))
            cluster_terms = [r[0] for r in cur.fetchall()]
        else:
            raw = (json_text or "").strip()
            if not raw:
                report["empty"] += 1
            else:
                try:
                    data = json.loads(raw)
                except (ValueError, TypeError):
                    anomaly(property_id, "invalid_json",
                            "land_rows_json không parse được")
                    data = None
                if data is not None:
                    if not isinstance(data, list):
                        anomaly(property_id, "invalid_shape",
                                "land_rows_json không phải mảng")
                    else:
                        rows = []
                        bad = False
                        for index, item in enumerate(data):
                            if not isinstance(item, dict):
                                anomaly(property_id, "invalid_row",
                                        f"land_rows[{index}] "
                                        "không phải object")
                                bad = True
                                break
                            values = {}
                            for new_key, old_key in _LAND_FIELD_ALIASES:
                                value, conflict = _land_row_field(
                                    item, new_key, old_key)
                                if conflict:
                                    anomaly(
                                        property_id, "conflict",
                                        f"land_rows[{index}] '{new_key}' "
                                        f"và '{old_key}' mâu thuẫn")
                                    bad = True
                                    break
                                values[new_key] = value
                            if bad:
                                break
                            # Kiểu sai (object/list/bool/…) → anomaly,
                            # không để giá trị lạ chạy vào câu INSERT
                            # (SQLite crash) và không ép về NULL.
                            for tkey in ("loaidat", "thoihan"):
                                tv = values[tkey]
                                if (tv is not None
                                        and not isinstance(tv, str)):
                                    anomaly(
                                        property_id, "invalid_field",
                                        f"land_rows[{index}].{tkey} "
                                        f"sai kiểu "
                                        f"{type(tv).__name__}")
                                    bad = True
                                    break
                            if bad:
                                break
                            try:
                                values["dientich"] = _land_area_to_float(
                                    values["dientich"])
                            except ValueError:
                                anomaly(
                                    property_id, "invalid_dientich",
                                    f"land_rows[{index}].dien_tich "
                                    "không parse được / không hợp lệ")
                                bad = True
                                break
                            values["loaidat"] = (
                                values["loaidat"].strip()
                                if isinstance(values["loaidat"], str)
                                else values["loaidat"])
                            values["thoihan"] = (
                                values["thoihan"].strip()
                                if isinstance(values["thoihan"], str)
                                else values["thoihan"])
                            rows.append(values)
                        if not bad:
                            for vitri, r in enumerate(rows, start=1):
                                cur.execute(
                                    "INSERT INTO property_land_rows "
                                    "(property_id, vitri, loaidat, "
                                    "dientich, thoihan) "
                                    "VALUES (?,?,?,?,?)",
                                    (property_id, vitri, r["loaidat"],
                                     r["dientich"], r["thoihan"]))
                            report["backfilled"] += 1
                            report["rows_inserted"] += len(rows)
                            if len(rows) > MAX_LAND_ROWS:
                                anomaly(
                                    property_id, "over_limit",
                                    f"{len(rows)} cụm > {MAX_LAND_ROWS} "
                                    "— đã ghi đủ, cần đối chiếu")
                            cluster_terms = [r["thoihan"] for r in rows]
        # Thời hạn lẻ không gắn được cụm → báo đối chiếu, giữ nguyên.
        if isinstance(thoi_han, str) and thoi_han.strip():
            term = thoi_han.strip()
            matched = any(
                isinstance(t, str) and t.strip() == term
                for t in cluster_terms)
            if not matched:
                anomaly(property_id, "orphan_thoi_han",
                        f"thoi_han lẻ '{term}' không trùng thoihan "
                        "cụm nào — giữ nguyên, cần đối chiếu")


def migrate_zalo_schema():
    """Them cot va bang Zalo theo huong cong them, khong dien giai du lieu cu."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    _ensure_table_columns(cur, "zalo_connector_accounts", {
        "qr_generated_at": "DATETIME",
        "qr_expires_at": "DATETIME",
        "intake_consented_at": "DATETIME",
        "policy_version": "INTEGER NOT NULL DEFAULT 0",
        "policy_acked_version": "INTEGER NOT NULL DEFAULT 0",
        "source_sync_request_version": "INTEGER NOT NULL DEFAULT 0",
        "source_sync_acked_version": "INTEGER NOT NULL DEFAULT 0",
        "gap_started_at": "DATETIME",
        "text_storage_full": "BOOLEAN NOT NULL DEFAULT 0",
    })
    _ensure_table_columns(cur, "zalo_sources", {
        "source_type": "VARCHAR(20)",
        "enabled_explicit": "BOOLEAN",
        "acked_enabled": "BOOLEAN",
        "policy_version": "INTEGER NOT NULL DEFAULT 0",
        "policy_acked_version": "INTEGER NOT NULL DEFAULT 0",
        "last_activity_at": "DATETIME",
    })
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS zalo_message_texts (
            id VARCHAR(36) PRIMARY KEY,
            connector_account_id VARCHAR(36) NOT NULL,
            source_id VARCHAR(36) NOT NULL,
            conversation_id VARCHAR(200) NOT NULL,
            msg_id VARCHAR(200) NOT NULL,
            sender_id VARCHAR(200) NOT NULL,
            sent_at DATETIME NOT NULL,
            received_at DATETIME NOT NULL,
            raw_text TEXT NOT NULL,
            payload_digest VARCHAR(64) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(connector_account_id) REFERENCES zalo_connector_accounts(id),
            FOREIGN KEY(source_id) REFERENCES zalo_sources(id),
            CONSTRAINT uq_zalo_message_text UNIQUE (connector_account_id, conversation_id, msg_id)
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_message_texts_connector_account_id
        ON zalo_message_texts(connector_account_id);
        CREATE INDEX IF NOT EXISTS ix_zalo_message_texts_source_id
        ON zalo_message_texts(source_id);
        CREATE TABLE IF NOT EXISTS zalo_data_sync_runs (
            id VARCHAR(36) PRIMARY KEY,
            connector_account_id VARCHAR(36) NOT NULL,
            status VARCHAR(30) NOT NULL,
            cutoff_at DATETIME NOT NULL,
            deadline_at DATETIME NOT NULL,
            source_ids_json JSON NOT NULL DEFAULT '[]',
            counters_json JSON NOT NULL DEFAULT '{}',
            error_message TEXT,
            started_at DATETIME NOT NULL,
            completed_at DATETIME,
            FOREIGN KEY(connector_account_id) REFERENCES zalo_connector_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_data_sync_runs_connector_account_id
        ON zalo_data_sync_runs(connector_account_id);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_zalo_data_sync_running_account
        ON zalo_data_sync_runs(connector_account_id) WHERE status = 'running';
    """)
    con.commit()
    con.close()
    assert_foreign_key_check()


def migrate_inheritance_case_properties_schema():
    """Tao bang lien ket nhieu tai san cho ho so neu chua co."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS inheritance_case_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            is_primary BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(case_id) REFERENCES inheritance_cases(id),
            FOREIGN KEY(property_id) REFERENCES properties(id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_case_property_unique
        ON inheritance_case_properties(case_id, property_id);
        CREATE INDEX IF NOT EXISTS ix_case_property_case
        ON inheritance_case_properties(case_id);
        CREATE INDEX IF NOT EXISTS ix_case_property_property
        ON inheritance_case_properties(property_id);
        """
    )
    con.commit()
    con.close()


def get_db():
    """Cung cấp kết nối DB cho mỗi request, tự đóng sau khi xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_zalo_exchange_schema():
    """Bang consumer goi raw Zalo (MIN-99) — cong them, khong cham legacy."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS zalo_raw_records (
            record_id VARCHAR(36) PRIMARY KEY,
            logical_id VARCHAR(36) NOT NULL,
            revision INTEGER NOT NULL,
            kind VARCHAR(40) NOT NULL,
            package_id VARCHAR(36) NOT NULL,
            package_sequence INTEGER NOT NULL,
            captured_at DATETIME NOT NULL,
            recorded_at DATETIME NOT NULL,
            canonical_sha256 VARCHAR(64) NOT NULL,
            payload_json TEXT NOT NULL,
            imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_zalo_raw_logical_rev UNIQUE (logical_id, revision)
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_raw_logical ON zalo_raw_records(logical_id);
        CREATE INDEX IF NOT EXISTS ix_zalo_raw_kind ON zalo_raw_records(kind);
        CREATE INDEX IF NOT EXISTS ix_zalo_raw_package ON zalo_raw_records(package_id);
        CREATE TABLE IF NOT EXISTS zalo_import_ledger (
            package_id VARCHAR(36) PRIMARY KEY,
            consumer_id VARCHAR(36) NOT NULL,
            sequence INTEGER NOT NULL,
            manifest_sha256 VARCHAR(64) NOT NULL,
            record_count INTEGER NOT NULL,
            sealed_at DATETIME,
            decision VARCHAR(20) NOT NULL,
            quarantine_reason TEXT,
            receipt_status VARCHAR(20),
            receipt_id VARCHAR(36),
            imported_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_import_sequence ON zalo_import_ledger(sequence);
        CREATE TABLE IF NOT EXISTS zalo_sync_state (
            key VARCHAR(60) PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS zalo_parse_jobs (
            job_id VARCHAR(36) PRIMARY KEY,
            package_id VARCHAR(36) NOT NULL,
            state VARCHAR(20) NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_parse_package ON zalo_parse_jobs(package_id);
        CREATE TABLE IF NOT EXISTS zalo_intake_results (
            result_id VARCHAR(36) PRIMARY KEY,
            package_id VARCHAR(36) NOT NULL,
            revision INTEGER NOT NULL,
            parser_version VARCHAR(40) NOT NULL,
            result_json TEXT NOT NULL,
            warnings_json TEXT NOT NULL DEFAULT '[]',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_zalo_results_package ON zalo_intake_results(package_id);
    """)
    con.commit()
    con.close()
    assert_foreign_key_check()