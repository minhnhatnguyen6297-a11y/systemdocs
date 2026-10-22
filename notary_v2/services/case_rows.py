"""Reader/serializer cho dòng dữ kiện case-owned Storage B.

Nguồn duy nhất của dữ kiện Stage là `case_person_rows`, `case_asset_rows`,
`case_asset_land_rows`. Module này KHÔNG mở transaction, KHÔNG ghi và
KHÔNG fallback Customer/Property: identity (`customer_id`/`property_id`)
chỉ là con trỏ kỹ thuật, dữ kiện đọc từ dòng của chính Hồ sơ.

- `read_stage(case)`: stage wire đầy đủ (`people`/`assets`/`owner_row_id`).
- `materialize_case_state(case)`: view RAM ghép rows + meta + Diagram +
  docx_import cho consumer Word/binding; không persist Stage vào JSON.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Optional

from models import InheritanceCase

CASE_TYPE_INHERITANCE = "inheritance"
CASE_TYPE_TWO_PARTY = "two_party"

DOCUMENT_TYPES = ("khai_nhan", "thoa_thuan")
DOCUMENT_TYPES_TWO_PARTY = ("chuyen_nhuong", "tang_cho",
                            "cho_thue", "dat_coc")

# Khớp `_person_contract_keys`/`_asset_contract_keys` của case_workspace và
# contract §4.1/§4.3. Khai báo độc lập để reader không import service ghi
# (tránh vòng import case_workspace → case_rows).
PERSON_CONTRACT_KEYS = (
    "row_id", "entity_id", "ho_ten", "gioi_tinh", "ngay_sinh", "ngay_chet",
    "so_giay_to", "ngay_cap", "noi_cap", "dia_chi", "place_of_origin",
    "loai_giay_to", "loai_dia_chi",
)
ASSET_CONTRACT_KEYS = (
    "row_id", "entity_id", "so_serial", "so_vao_so", "so_thua_dat",
    "so_to_ban_do", "dia_chi", "loai_so", "hinh_thuc_su_dung", "thoi_han",
    "nguon_goc", "ngay_cap", "co_quan_cap", "land_rows",
)
CASE_SCALAR_FIELDS = (
    "tenvanban", "nhomhopdong", "loaivanbannhandien", "socongchung",
    "ngaycongchung", "congchungvien", "thuky",
)
PAYLOAD_SCHEMA_VERSION = 4


def case_types(case: InheritanceCase) -> tuple[str, str]:
    """(case_type, document_type) từ cột `loai_van_ban` — không thêm cột."""
    loai = (case.loai_van_ban or "").strip()
    if loai in DOCUMENT_TYPES:
        return CASE_TYPE_INHERITANCE, loai
    if loai in DOCUMENT_TYPES_TWO_PARTY:
        return CASE_TYPE_TWO_PARTY, loai
    return (loai or "unknown"), "khai_nhan"


def load_json(case: InheritanceCase) -> dict:
    raw = (case.case_state_json or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _date_wire(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _person_wire(row) -> dict:
    return {
        "row_id": row.row_id,
        "entity_id": row.customer_id,
        "ho_ten": row.ho_ten,
        "gioi_tinh": row.gioi_tinh,
        "ngay_sinh": row.ngay_sinh,
        "ngay_chet": row.ngay_chet,
        "so_giay_to": row.so_giay_to,
        "ngay_cap": row.ngay_cap,
        "noi_cap": row.noi_cap,
        "dia_chi": row.dia_chi,
        "place_of_origin": row.place_of_origin,
        "loai_giay_to": row.loai_giay_to,
        "loai_dia_chi": row.loai_dia_chi,
    }


def _asset_wire(row) -> dict:
    land_rows = None
    if row.land_rows_present:
        land_rows = [
            {"loai_dat": land.loaidat,
             "dien_tich": land.dientich,
             "thoi_han": land.thoihan}
            for land in sorted(row.land_rows, key=lambda x: x.vitri)
        ]
    return {
        "row_id": row.row_id,
        "entity_id": row.property_id,
        "so_serial": row.so_serial if row.so_serial is not None else "",
        "so_vao_so": row.so_vao_so,
        "so_thua_dat": row.so_thua_dat,
        "so_to_ban_do": row.so_to_ban_do,
        "dia_chi": row.dia_chi,
        "loai_so": row.loai_so,
        "hinh_thuc_su_dung": row.hinh_thuc_su_dung,
        "thoi_han": row.thoi_han,
        "nguon_goc": row.nguon_goc,
        "ngay_cap": _date_wire(row.ngay_cap),
        "co_quan_cap": row.co_quan_cap,
        "land_rows": land_rows,
    }


def _owner_row_id(case: InheritanceCase, domain: str) -> Optional[str]:
    if domain != CASE_TYPE_INHERITANCE:
        return None
    value = load_json(case).get("owner_row_id")
    return value if isinstance(value, str) and value else None


def read_stage(case: InheritanceCase) -> dict:
    """`{owner_row_id?, people[], assets[]}` từ rows, ordered `vitri`."""
    domain, _doc = case_types(case)
    people = [_person_wire(r) for r in sorted(case.person_rows,
                                             key=lambda x: x.vitri)]
    assets = [_asset_wire(r) for r in sorted(case.asset_rows,
                                             key=lambda x: x.vitri)]
    stage: dict = {"people": people, "assets": assets}
    if domain == CASE_TYPE_INHERITANCE:
        stage = {"owner_row_id": _owner_row_id(case, domain), **stage}
    return stage


def _case_view(case: InheritanceCase, payload: Mapping[str, Any]) -> dict:
    domain, document_type = case_types(case)
    scalars = payload.get("case") if isinstance(payload.get("case"), Mapping) else {}
    return {
        "id": case.id,
        "case_type": domain,
        "document_type": document_type,
        "status": case.trang_thai,
        "revision": case.workspace_revision,
        "ngay_lap_ho_so": _date_wire(case.ngay_lap_ho_so),
        "noi_niem_yet": case.noi_niem_yet,
        "nguoi_nhan_uy_quyen": case.nguoi_nhan_uy_quyen,
        "nguoi_nhan_uy_quyen_id": case.nguoi_nhan_uy_quyen_id,
        "noi_dung_viec": case.noi_dung_viec,
        "ghi_chu": case.ghi_chu,
        # Metadata cột là SOT (§2.5): consumer Word đọc cùng key canonical
        # với wire nhưng không lấy bản sao Stage/JSON. Null tường minh.
        "ngaylaphoso": _date_wire(case.ngay_lap_ho_so),
        "noiniemyet": case.noi_niem_yet,
        "nguoinhanuyquyen": case.nguoi_nhan_uy_quyen,
        "noidungviec": case.noi_dung_viec,
        "ghichu": case.ghi_chu,
        **{key: scalars.get(key) for key in CASE_SCALAR_FIELDS},
    }


def materialize_case_state(case: InheritanceCase) -> dict:
    """View RAM cho consumer: rows thành `stage[]`/`assets[]` phẳng.

    `id` legacy (entity id dạng chuỗi) chỉ là thông tin phụ nullable cho
    consumer còn đọc key cũ; quan hệ luôn `row_id`. Không persist lại
    Stage vào `case_state_json`.
    """
    payload = load_json(case)
    stage = read_stage(case)
    people = [{**row, "id": (str(row["entity_id"])
                             if row["entity_id"] is not None else None)}
              for row in stage["people"]]
    assets = [{**row, "id": (str(row["entity_id"])
                             if row["entity_id"] is not None else None)}
              for row in stage["assets"]]
    domain = case_types(case)[0]
    diagram = payload.get("diagram")
    view: dict = {
        "schemaVersion": PAYLOAD_SCHEMA_VERSION,
        "case_type": domain,
        "case": _case_view(case, payload),
        "stage": people,
        "assets": assets,
        "diagram": dict(diagram) if isinstance(diagram, Mapping) else {},
    }
    if domain == CASE_TYPE_INHERITANCE:
        view["owner_row_id"] = stage.get("owner_row_id")
    if "docx_import" in payload:
        view["docx_import"] = payload["docx_import"]
    return view
