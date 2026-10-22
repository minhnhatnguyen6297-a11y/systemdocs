from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List, Union, Any
from datetime import date, datetime
import io
import json
from pathlib import Path
import re
from uuid import uuid4

from database import get_db
from models import (
    CaseAssetRow,
    CasePersonRow,
    Customer,
    InheritanceCase,
    InheritanceCaseProperty,
    InheritanceParticipant,
    Property,
    WordTemplate,
)
from services import word_engine
from services.case_workspace import CaseWorkspaceService, WorkspaceError
from services.case_rows import materialize_case_state, read_stage

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")
WORD_TEMPLATE_UPLOAD_DIR = Path("word_templates/custom")
def _to_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _normalize_property_ids(primary_property_id: str, raw_property_ids: Optional[Union[List[str], str]]) -> list[int]:
    values: list[str] = []
    for item in _to_list(raw_property_ids):
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                for v in parsed if isinstance(parsed, list) else []:
                    values.append(str(v).strip())
                continue
            except Exception:
                pass
        values.extend([x.strip() for x in text.split(",") if x and x.strip()])

    if primary_property_id:
        values.append(primary_property_id)
    out: list[int] = []
    seen: set[int] = set()
    for v in values:
        if not str(v).isdigit():
            continue
        pid = int(v)
        if pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
    if primary_property_id and primary_property_id.isdigit():
        primary = int(primary_property_id)
        if primary in out:
            out = [primary] + [x for x in out if x != primary]
    return out


class DiagramPayloadValidationError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_nullable_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _render_case_form(
    request: Request,
    *,
    obj: Optional[InheritanceCase],
    deceased: list[Customer],
    properties: list[Property],
    errors: list[str],
    field_errors: dict[str, str],
    form: dict[str, Any],
    all_customers: list[Customer],
    participants: list[Any],
    participant_ids: set[int],
    case_property_ids: list[int],
):
    return templates.TemplateResponse("cases/form.html", {
        "request": request,
        "obj": obj,
        "deceased": deceased,
        "properties": properties,
        "errors": errors,
        "field_errors": field_errors,
        "form": form,
        "all_customers": all_customers,
        "participants": participants,
        "participant_ids": participant_ids,
        "case_property_ids": case_property_ids,
    })


# ------------------------------------------------ biên nhận payload web → B
_STAGE_PERSON_FIELDS = (
    "ho_ten", "gioi_tinh", "ngay_sinh", "ngay_chet", "so_giay_to",
    "ngay_cap", "noi_cap", "dia_chi", "place_of_origin",
    "loai_giay_to", "loai_dia_chi",
)
_STAGE_DATE_FIELDS = {"ngay_sinh", "ngay_chet", "ngay_cap"}


def _is_uuid4_text(value: Any) -> bool:
    return bool(re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}", _clean_text(value)))


def _stage_date(value: Any) -> Optional[str]:
    """Ngày Stage wire `YYYY` | `YYYY-MM-DD` | null.

    Form web cũ post ngày hiển thị `dd/mm/yyyy`; chuẩn hóa ở biên. Chuỗi
    không nhận diện được giữ nguyên để service báo `invalid_date` thay vì
    tự đoán.
    """
    text = _clean_text(value)
    if not text or text in {"0", "00/00/0000"}:
        return None
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        return (f"{int(match.group(3)):04d}-{int(match.group(2)):02d}-"
                f"{int(match.group(1)):02d}")
    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if match:
        return (f"{match.group(1)}-{int(match.group(2)):02d}-"
                f"{int(match.group(3)):02d}")
    return text


def _master_date(value: Optional[date]) -> Optional[str]:
    """Date master → wire Người: năm trần khi đúng quy ước 01/01."""
    if value is None:
        return None
    if value.day == 1 and value.month == 1:
        return str(value.year)
    return value.isoformat()


def _parse_posted_payload(raw_payload: Any) -> Optional[dict]:
    text = _clean_text(raw_payload)
    if not text:
        return None
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise DiagramPayloadValidationError(
            [f"case_state_json không phải JSON hợp lệ: {exc}"])
    if not isinstance(payload, dict):
        raise DiagramPayloadValidationError(
            ["case_state_json phải là object JSON."])
    return payload


def _person_row_from_item(item: dict, existing: Optional[dict] = None) -> dict:
    """Một dòng Người stage wire từ item form; giữ row_id nếu là dòng đã lưu.

    Dòng mới nhận row_id client hoặc UUID v4 mới; `entity_id` để null —
    resolver của service tự tìm danh tính theo neo, form không có quyền
    ép liên kết master.
    """
    if existing is not None:
        row = dict(existing)
    else:
        row_id = _clean_text(item.get("row_id"))
        row = {
            "row_id": row_id if _is_uuid4_text(row_id) else str(uuid4()),
            "entity_id": None,
            **{key: None for key in _STAGE_PERSON_FIELDS},
        }
    for key in _STAGE_PERSON_FIELDS:
        if key not in item:
            continue
        if key in _STAGE_DATE_FIELDS:
            row[key] = _stage_date(item.get(key))
        else:
            row[key] = _clean_nullable_text(item.get(key))
    return row


def _people_from_customer(customer: Customer) -> dict:
    return {
        "row_id": str(uuid4()),
        "entity_id": None,
        "ho_ten": _clean_text(customer.ho_ten),
        "gioi_tinh": _clean_nullable_text(customer.gioi_tinh),
        "ngay_sinh": _master_date(customer.ngay_sinh),
        "ngay_chet": _master_date(customer.ngay_chet),
        "so_giay_to": _clean_nullable_text(customer.so_giay_to),
        "ngay_cap": _master_date(customer.ngay_cap),
        "noi_cap": _clean_nullable_text(customer.noi_cap),
        "dia_chi": _clean_nullable_text(customer.dia_chi),
        "place_of_origin": _clean_nullable_text(
            getattr(customer, "place_of_origin", None)),
        "loai_giay_to": _clean_nullable_text(customer.loai_giay_to),
        "loai_dia_chi": _clean_nullable_text(customer.loai_dia_chi),
    }


def _master_land_rows(prop: Property) -> list[dict]:
    rows = sorted(getattr(prop, "land_rows", None) or [],
                  key=lambda row: row.vitri)
    if rows:
        return [{"loai_dat": row.loaidat, "dien_tich": row.dientich,
                 "thoi_han": row.thoihan} for row in rows]
    raw = getattr(prop, "land_rows_json", None)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    out = []
    for row in parsed:
        if not isinstance(row, dict):
            continue
        out.append({
            "loai_dat": row.get("loai_dat", row.get("loaidat")),
            "dien_tich": row.get("dien_tich", row.get("dientich")),
            "thoi_han": row.get("thoi_han", row.get("thoihan")),
        })
    return out


def _asset_row_from_property(prop: Property) -> dict:
    """Dòng Tài sản stage wire từ master chỉ tại biên tạo/cập nhật web."""
    land_rows = _master_land_rows(prop)
    return {
        "row_id": str(uuid4()),
        "entity_id": None,
        "so_serial": _clean_text(prop.so_serial),
        "so_vao_so": _clean_nullable_text(prop.so_vao_so),
        "so_thua_dat": _clean_nullable_text(prop.so_thua_dat),
        "so_to_ban_do": _clean_nullable_text(prop.so_to_ban_do),
        "dia_chi": _clean_text(prop.dia_chi),
        "loai_so": _clean_nullable_text(prop.loai_so),
        "hinh_thuc_su_dung": _clean_nullable_text(prop.hinh_thuc_su_dung),
        "thoi_han": _clean_nullable_text(prop.thoi_han),
        "nguon_goc": _clean_nullable_text(prop.nguon_goc),
        "ngay_cap": prop.ngay_cap.isoformat() if prop.ngay_cap else None,
        "co_quan_cap": _clean_nullable_text(prop.co_quan_cap),
        "land_rows": land_rows or None,
    }


def _posted_people(case: Optional[InheritanceCase], payload: Optional[dict]) -> list[dict]:
    """Dòng Người stage wire: merge item form lên dòng đã lưu theo row_id.

    Payload không có `stage` (POST cũ/không hydrate) → giữ nguyên dòng đã
    lưu, không xóa dữ kiện ngoài ý định.
    """
    base = read_stage(case) if case is not None else {"people": []}
    existing = {row["row_id"]: row for row in base["people"]}
    posted = payload.get("stage") if isinstance(payload, dict) else None
    if not isinstance(posted, list):
        return [dict(row) for row in base["people"]]
    people = []
    for index, item in enumerate(posted):
        if not isinstance(item, dict):
            raise DiagramPayloadValidationError(
                [f"case_state_json.stage[{index}] phải là object JSON."])
        row_id = _clean_text(item.get("row_id"))
        prior = existing.get(row_id) if row_id else None
        if prior is None:
            # Form legacy chỉ có `id` (customer id): ghép lại đúng dòng đã
            # lưu theo identity để không tạo dòng trùng mỗi lần cập nhật.
            legacy_id = _clean_text(item.get("id"))
            if legacy_id.isdigit():
                prior = next((row for row in base["people"]
                              if row.get("entity_id") == int(legacy_id)), None)
        people.append(_person_row_from_item(item, prior))
    return people


def _owner_row_for_customer(people: list[dict],
                            customer_id: Optional[int]) -> Optional[str]:
    if customer_id is None:
        return None
    return next((row["row_id"] for row in people
                 if row.get("entity_id") == customer_id), None)


def _case_meta_from_form(case: Optional[InheritanceCase], form: dict) -> dict:
    meta: dict[str, Any] = {}
    if case is None:
        meta.update({"case_type": "inheritance",
                     "document_type": "khai_nhan"})
    raw_date = _clean_text(form.get("ngay_lap_ho_so"))
    if not raw_date and case is not None and case.ngay_lap_ho_so is not None:
        raw_date = case.ngay_lap_ho_so.isoformat()
    if not raw_date:
        raw_date = date.today().isoformat()
    meta["ngay_lap_ho_so"] = _stage_date(raw_date)
    for field in ("noi_niem_yet", "ghi_chu", "nguoi_nhan_uy_quyen",
                  "noi_dung_viec"):
        if field in form:
            meta[field] = _clean_nullable_text(form.get(field))
    return meta


def _workspace_error(exc: WorkspaceError) -> DiagramPayloadValidationError:
    messages = [exc.message]
    field_errors = (exc.details or {}).get("field_errors")
    if isinstance(field_errors, list):
        for item in field_errors:
            if isinstance(item, dict) and item.get("message"):
                messages.append(str(item["message"]))
    return DiagramPayloadValidationError(messages)


def _case_facts(case: InheritanceCase) -> dict:
    """Dữ kiện hiển thị danh sách/chi tiết, đọc từ dòng của hồ sơ."""
    view = materialize_case_state(case)
    people = view.get("stage") or []
    owner = next((row for row in people
                  if row.get("row_id") == view.get("owner_row_id")), None)
    owner = owner or (people[0] if people else None)
    assets = view.get("assets") or []
    asset = assets[0] if assets else None

    def display_date(value: Any) -> str:
        text = _clean_text(value)
        if not text:
            return ""
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match:
            return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"
        return text

    return {
        "owner": {
            "name": _clean_text(owner.get("ho_ten")) if owner else "",
            "birth": display_date(owner.get("ngay_sinh")) if owner else "",
            "death": display_date(owner.get("ngay_chet")) if owner else "",
            "doc": _clean_text(owner.get("so_giay_to")) if owner else "",
            "address": _clean_text(owner.get("dia_chi")) if owner else "",
        } if owner else None,
        "asset": {
            "serial": _clean_text(asset.get("so_serial")) if asset else "",
            "thua": _clean_text(asset.get("so_thua_dat")) if asset else "",
            "to_ban_do": _clean_text(asset.get("so_to_ban_do")) if asset else "",
            "address": _clean_text(asset.get("dia_chi")) if asset else "",
        } if asset else None,
        "status": case.trang_thai,
        "status_label": "Đã lưu" if case.trang_thai == "done" else "Nháp",
    }


def _form_from_case(case: InheritanceCase) -> dict:
    view = materialize_case_state(case)
    return {
        "nguoi_chet_id": str(case.nguoi_chet_id) if case.nguoi_chet_id else "",
        "tai_san_id": str(case.tai_san_id) if case.tai_san_id else "",
        "ngay_lap_ho_so": case.ngay_lap_ho_so.isoformat() if case.ngay_lap_ho_so else "",
        "loai_van_ban": case.loai_van_ban or "khai_nhan",
        "noi_niem_yet": case.noi_niem_yet or "",
        "ghi_chu": case.ghi_chu or "",
        "engine_state_json": "",
        "diagram_payload": "",
        "case_state_json": json.dumps(view, ensure_ascii=False),
    }


@router.get("/")
def list_cases(request: Request, db: Session = Depends(get_db), q: str = ""):
    cases = db.query(InheritanceCase).order_by(InheritanceCase.id.desc()).all()
    facts = {case.id: _case_facts(case) for case in cases}
    if q:
        needle = q.lower()
        cases = [c for c in cases
                 if needle in (facts[c.id]["owner"] or {}).get("name", "").lower()]
    return templates.TemplateResponse("cases/list.html", {
        "request": request, "cases": cases, "case_facts": facts, "q": q})


@router.get("/create")
def create_form(request: Request, db: Session = Depends(get_db)):
    all_customers = db.query(Customer).order_by(Customer.ho_ten).all()
    deceased = [c for c in all_customers if c.ngay_chet is not None]
    properties = db.query(Property).order_by(Property.id.desc()).all()
    form = {
        "nguoi_chet_id": "", "tai_san_id": "", "ngay_lap_ho_so": date.today().isoformat(),
        "loai_van_ban": "khai_nhan", "ghi_chu": "", "engine_state_json": "",
        "diagram_payload": "", "case_state_json": ""
    }
    return _render_case_form(
        request, obj=None, deceased=deceased, properties=properties,
        errors=[], field_errors={}, form=form, all_customers=all_customers,
        participants=[], participant_ids=set(), case_property_ids=[])


@router.post("/create")
def create(
    request: Request,
    nguoi_chet_id: Optional[str] = Form(None),
    tai_san_id: Optional[str] = Form(None),
    property_ids: Optional[Union[List[str], str]] = Form(None),
    participant_id: Optional[Union[List[str], str]] = Form(None),
    noi_niem_yet: Optional[str] = Form(None),
    ghi_chu: Optional[str] = Form(None),
    ngay_lap_ho_so: Optional[str] = Form(None),
    case_state_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Tạo hồ sơ web qua `CaseWorkspaceService.create` (một transaction B)."""
    form = {
        "nguoi_chet_id": (nguoi_chet_id or "").strip(),
        "tai_san_id": (tai_san_id or "").strip(),
        "ngay_lap_ho_so": (ngay_lap_ho_so or "").strip(),
        "noi_niem_yet": (noi_niem_yet or "").strip(),
        "ghi_chu": (ghi_chu or "").strip(),
        "engine_state_json": "",
        "diagram_payload": "",
        "case_state_json": (case_state_json or "").strip(),
    }
    selected_property_ids = _normalize_property_ids(
        form["tai_san_id"], property_ids)
    all_customers = db.query(Customer).order_by(Customer.ho_ten).all()
    customers_by_id = {c.id: c for c in all_customers}
    properties = db.query(Property).order_by(Property.id.desc()).all()
    properties_by_id = {p.id: p for p in properties}
    deceased = [c for c in all_customers if c.ngay_chet is not None]
    errors: list[str] = []
    field_errors: dict[str, str] = {}

    owner_id = int(form["nguoi_chet_id"]) if form["nguoi_chet_id"].isdigit() else None
    if form["nguoi_chet_id"] and (
            owner_id is None or owner_id not in customers_by_id):
        field_errors["nguoi_chet_id"] = "Người chết không tồn tại"
    missing_props = [pid for pid in selected_property_ids
                     if pid not in properties_by_id]
    if missing_props:
        errors.append("Danh sách tài sản có id không tồn tại: "
                      + ", ".join(map(str, missing_props)))

    people: list[dict] = []
    assets: list[dict] = []
    owner_row_id = None
    posted_stage = None
    try:
        payload = _parse_posted_payload(form["case_state_json"])
        posted_stage = payload.get("stage") if payload else None
        if isinstance(posted_stage, list):
            # Stage gửi tường minh (kể cả []) là ý định của người dùng:
            # không thay bằng master fallback.
            people = _posted_people(None, payload)
        elif owner_id in customers_by_id:
            # Không có Stage gửi kèm → hydrate đúng master được chọn.
            owner_row = _people_from_customer(customers_by_id[owner_id])
            people = [owner_row]
            for cid in _to_list(participant_id):
                if not str(cid).strip().isdigit():
                    continue
                customer = customers_by_id.get(int(cid))
                if customer is not None and customer.id != owner_id:
                    people.append(_people_from_customer(customer))
        if owner_id in customers_by_id:
            # Owner chỉ theo lựa chọn; không tự lấy people[0].
            owner_row = next(
                (row for row in people
                 if row.get("ho_ten") == customers_by_id[owner_id].ho_ten),
                None)
            owner_row_id = owner_row["row_id"] if owner_row else None
    except DiagramPayloadValidationError as exc:
        errors.extend(exc.errors)

    if field_errors or errors:
        return _render_case_form(
            request, obj=None, deceased=deceased, properties=properties,
            errors=errors, field_errors=field_errors, form=form,
            all_customers=all_customers, participants=[],
            participant_ids=set(), case_property_ids=selected_property_ids)

    # Stage gửi kèm chỉ chở Người; Tài sản lấy đúng danh sách được chọn
    # (không tạo placeholder cho []).
    assets = [_asset_row_from_property(properties_by_id[pid])
              for pid in selected_property_ids]
    stage = {"people": people, "assets": assets,
             "owner_row_id": owner_row_id}
    try:
        data = CaseWorkspaceService(db).create(
            str(uuid4()), _case_meta_from_form(None, form), stage, None)
    except WorkspaceError as exc:
        errors.extend(_workspace_error(exc).errors)
        return _render_case_form(
            request, obj=None, deceased=deceased, properties=properties,
            errors=errors, field_errors=field_errors, form=form,
            all_customers=all_customers, participants=[],
            participant_ids=set(), case_property_ids=selected_property_ids)
    return RedirectResponse(f"/cases/{data['case']['id']}/edit", status_code=302)


@router.get("/{cid}")
def detail(cid: int, request: Request, db: Session = Depends(get_db)):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)
    all_customers = db.query(Customer).order_by(Customer.ho_ten).all()
    participant_ids = {p.customer_id for p in case.participants}
    available = [c for c in all_customers if c.id not in participant_ids and c.id != case.nguoi_chet_id]
    view = materialize_case_state(case)
    rows = {row.get("row_id"): row for row in view.get("stage") or []}
    return templates.TemplateResponse("cases/detail.html", {
        "request": request, "case": case, "available": available,
        "case_facts": _case_facts(case),
        "participant_rows": {p.id: rows.get(p.case_person_row_id)
                             for p in case.participants},
        "vai_tro_options": ["Vợ/Chồng", "Con", "Cha/Mẹ", "Anh/Chị/Em"]
    })


@router.get("/{cid}/edit")
def edit_form(cid: int, request: Request, db: Session = Depends(get_db)):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)
    all_customers = db.query(Customer).order_by(Customer.ho_ten).all()
    deceased = [c for c in all_customers if c.ngay_chet is not None]
    properties = db.query(Property).order_by(Property.id.desc()).all()
    participants = case.participants
    participant_ids = {p.customer_id for p in participants}
    case_property_ids = [row.property_id for row in sorted(
        case.property_links, key=lambda x: (not x.is_primary, x.id))
        if row.property_id is not None]
    if not case_property_ids and case.tai_san_id:
        case_property_ids = [int(case.tai_san_id)]
    return _render_case_form(
        request, obj=case, deceased=deceased, properties=properties,
        errors=[], field_errors={}, form=_form_from_case(case),
        all_customers=all_customers, participants=participants,
        participant_ids=participant_ids, case_property_ids=case_property_ids)


def _commit_case_form(case: InheritanceCase, db: Session,
                      form: dict, owner_id: Optional[int]) -> None:
    """Đẩy Stage form (row-keyed) qua `commit_stage`; giữ status/revision."""
    payload = _parse_posted_payload(form.get("case_state_json"))
    people = _posted_people(case, payload)
    read = read_stage(case)
    owner_row_id = _owner_row_for_customer(people, owner_id)
    if owner_row_id is None:
        stored = read.get("owner_row_id")
        if any(row["row_id"] == stored for row in people):
            owner_row_id = stored
    stage = {
        "people": people,
        "assets": read["assets"],
        "owner_row_id": owner_row_id,
    }
    CaseWorkspaceService(db).commit_stage(
        case.id, case.workspace_revision, stage,
        _case_meta_from_form(case, form))


def _form_from_posted(form: dict) -> dict:
    out = {
        "nguoi_chet_id": _clean_text(form.get("nguoi_chet_id")),
        "tai_san_id": _clean_text(form.get("tai_san_id")),
        "engine_state_json": "",
        "diagram_payload": "",
        "case_state_json": _clean_text(form.get("case_state_json")),
    }
    for key in ("noi_niem_yet", "ghi_chu", "ngay_lap_ho_so"):
        if key in form:
            out[key] = _clean_text(form[key])
    return out


@router.post("/{cid}/edit")
def edit(
    cid: int, request: Request,
    nguoi_chet_id: Optional[str] = Form(None), tai_san_id: Optional[str] = Form(None),
    noi_niem_yet: Optional[str] = Form(None),
    ghi_chu: Optional[str] = Form(None),
    ngay_lap_ho_so: Optional[str] = Form(None),
    case_state_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)
    posted = {"nguoi_chet_id": nguoi_chet_id, "tai_san_id": tai_san_id,
              "case_state_json": case_state_json}
    # Field vắng mặt nghĩa là form không quản lý → giữ giá trị đã lưu;
    # chỉ ghi null khi chính form gửi chuỗi rỗng.
    for key, value in (("noi_niem_yet", noi_niem_yet),
                       ("ghi_chu", ghi_chu),
                       ("ngay_lap_ho_so", ngay_lap_ho_so)):
        if value is not None:
            posted[key] = value
    form = _form_from_posted(posted)
    owner_id = int(form["nguoi_chet_id"]) if form["nguoi_chet_id"].isdigit() else None
    all_customers = db.query(Customer).order_by(Customer.ho_ten).all()
    deceased = [c for c in all_customers if c.ngay_chet is not None]
    properties = db.query(Property).order_by(Property.id.desc()).all()
    try:
        _commit_case_form(case, db, form, owner_id)
    except DiagramPayloadValidationError as exc:
        return _render_case_form(
            request, obj=case, deceased=deceased, properties=properties,
            errors=list(exc.errors), field_errors={}, form=form,
            all_customers=all_customers, participants=case.participants,
            participant_ids={p.customer_id for p in case.participants},
            case_property_ids=[], )
    except WorkspaceError as exc:
        mapped = _workspace_error(exc)
        return _render_case_form(
            request, obj=case, deceased=deceased, properties=properties,
            errors=list(mapped.errors), field_errors={}, form=form,
            all_customers=all_customers, participants=case.participants,
            participant_ids={p.customer_id for p in case.participants},
            case_property_ids=[], )
    return RedirectResponse(f"/cases/{cid}/edit", status_code=302)


@router.post("/{cid}/stage-update")
def update_stage(cid: int, case_state_json: str = Form(...),
                 nguoi_chet_id: Optional[str] = Form(None),
                 db: Session = Depends(get_db)):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        return JSONResponse({"ok": False, "error": "case_not_found"},
                            status_code=404)
    owner_id = (int(nguoi_chet_id)
                if (nguoi_chet_id or "").strip().isdigit() else None)
    try:
        read = read_stage(case)
        payload = _parse_posted_payload(case_state_json)
        people = _posted_people(case, payload)
        owner_row_id = _owner_row_for_customer(people, owner_id)
        if owner_row_id is None:
            stored = read.get("owner_row_id")
            if any(row["row_id"] == stored for row in people):
                owner_row_id = stored
        data = CaseWorkspaceService(db).commit_stage(
            case.id, case.workspace_revision,
            {"people": people, "assets": read["assets"],
             "owner_row_id": owner_row_id})
    except DiagramPayloadValidationError as exc:
        return JSONResponse({"ok": False, "error": "; ".join(exc.errors),
                             "errors": exc.errors}, status_code=400)
    except WorkspaceError as exc:
        status = 409 if exc.code == "workspace_conflict" else 400
        return JSONResponse({"ok": False, "error": exc.message,
                             "code": exc.code,
                             "details": exc.details}, status_code=status)
    view = materialize_case_state(case)
    return {"ok": True,
            "case_state_json": json.dumps(view, ensure_ascii=False),
            "revision": data["revision"]}


DEPRECATED_LOCK_MESSAGE = "Dùng Lưu hồ sơ; Hồ sơ không còn khóa"


@router.post("/{cid}/lock")
def lock(cid: int):
    return JSONResponse({"code": "endpoint_deprecated",
                         "message": DEPRECATED_LOCK_MESSAGE},
                        status_code=410)


@router.post("/{cid}/unlock")
def unlock(cid: int):
    return JSONResponse({"code": "endpoint_deprecated",
                         "message": DEPRECATED_LOCK_MESSAGE},
                        status_code=410)

def _live_master_refs(db: Session) -> tuple[set[int], set[int]]:
    """Tham chiếu sống tới master customers/properties từ dữ liệu còn lại.

    Nguồn là FK của dòng case-owned (`case_person_rows.customer_id`,
    `case_asset_rows.property_id`) + projection còn sống (người chết/tài
    sản chính/UQ, participant, link) — không quét JSON Stage đã bỏ.
    """
    customer_ids = {
        v for (v,) in db.query(InheritanceCase.nguoi_chet_id) if v is not None
    }
    customer_ids |= {
        v for (v,) in db.query(InheritanceCase.nguoi_nhan_uy_quyen_id)
        if v is not None
    }
    customer_ids |= {
        v for (v,) in db.query(CasePersonRow.customer_id) if v is not None
    }
    property_ids = {
        v for (v,) in db.query(InheritanceCase.tai_san_id) if v is not None
    }
    property_ids |= {
        v for (v,) in db.query(CaseAssetRow.property_id) if v is not None
    }
    for c_id, parent_id in db.query(
        InheritanceParticipant.customer_id,
        InheritanceParticipant.parent_customer_id,
    ):
        if c_id is not None:
            customer_ids.add(c_id)
        if parent_id is not None:
            customer_ids.add(parent_id)
    property_ids |= {
        v for (v,) in db.query(InheritanceCaseProperty.property_id)
        if v is not None
    }
    return customer_ids, property_ids


def _delete_case_and_unreferenced_masters(db: Session,
                                          case: InheritanceCase) -> None:
    """Xóa hồ sơ nháp + chỉ dọn master "thuộc hồ sơ" không còn tham chiếu.

    Master thuộc hồ sơ = người/tài sản trên dòng case-owned + projection
    (người chết, tài sản chính, participant kể cả parent, link phụ).
    Người nhận ủy quyền là danh bạ tái dùng → KHÔNG dọn theo hồ sơ.
    """
    customer_ids = {case.nguoi_chet_id}
    property_ids = {case.tai_san_id}
    customer_ids |= {row.customer_id for row in case.person_rows}
    property_ids |= {row.property_id for row in case.asset_rows}
    for p in case.participants:
        customer_ids.add(p.customer_id)
        customer_ids.add(p.parent_customer_id)
    for link in case.property_links:
        property_ids.add(link.property_id)
    customer_ids.discard(None)
    property_ids.discard(None)
    customer_ids.discard(case.nguoi_nhan_uy_quyen_id)

    db.delete(case)
    db.flush()  # rows/participants/links của hồ sơ đã đi

    live_customers, live_properties = _live_master_refs(db)
    for cid_ in customer_ids - live_customers:
        entity = db.get(Customer, cid_)
        if entity is not None:
            db.delete(entity)
    for pid_ in property_ids - live_properties:
        entity = db.get(Property, pid_)
        if entity is not None:
            db.delete(entity)


@router.post("/{cid}/delete")
def delete(cid: int, db: Session = Depends(get_db)):
    """Chỉ xóa hồ sơ nháp; hồ sơ Done sửa được nhưng không tự mở quyền xóa."""
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if case is None:
        raise HTTPException(404)
    if case.trang_thai != "draft":
        raise HTTPException(
            403, "Chỉ xóa được hồ sơ nháp; hồ sơ đã lưu không bị khóa sửa")
    try:
        _delete_case_and_unreferenced_masters(db, case)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return RedirectResponse("/cases", status_code=302)


def _get_selected_word_template_path(db: Session) -> Optional[Path]:
    active = (
        db.query(WordTemplate)
        .filter(WordTemplate.is_active)
        .order_by(WordTemplate.id.desc())
        .first()
    )
    if active and active.duong_dan_file:
        p = Path(active.duong_dan_file)
        if p.exists():
            return p

    template_candidates = [
        Path(r"\\maychu\D\Minh\HỒ SƠ UBND CÁC XÃ\2. Mẫu thừa kế\xã_PCDS -.docx"),
        Path("word_templates/xa_PCDS_template.docx"),
    ]
    existing_templates = [p for p in template_candidates if p.exists()]
    if not existing_templates:
        return None
    return max(existing_templates, key=lambda p: p.stat().st_mtime)


@router.get("/templates/list-json")
def list_templates_json(db: Session = Depends(get_db)):
    """API trả về danh sách template Word dạng JSON cho modal xuất văn bản."""
    items = db.query(WordTemplate).order_by(WordTemplate.id.desc()).all()
    # Also include built-in templates from word_templates/ dir
    builtin = []
    for p in Path("word_templates").glob("*.docx"):
        if p.exists():
            builtin.append({"id": f"builtin:{p.name}", "ten_mau": p.stem, "is_active": False, "builtin": True})
    return {
        "templates": [
            {"id": t.id, "ten_mau": t.ten_mau, "ten_file_goc": t.ten_file_goc, "is_active": t.is_active, "builtin": False}
            for t in items
        ] + builtin
    }


@router.get("/templates/manage")
def word_templates_page(request: Request, db: Session = Depends(get_db), ok: str = "", err: str = ""):
    items = db.query(WordTemplate).order_by(WordTemplate.id.desc()).all()
    return templates.TemplateResponse("cases/templates.html", {
        "request": request,
        "items": items,
        "ok": ok,
        "err": err,
    })


@router.post("/templates/manage/upload")
async def upload_word_template(
    ten_mau: str = Form(...),
    file_mau: UploadFile = File(...),
    dat_mac_dinh: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ten_mau = (ten_mau or "").strip()
    if not ten_mau:
        return RedirectResponse("/cases/templates/manage?err=Vui+long+nhap+ten+mau", status_code=302)
    if not file_mau or not file_mau.filename:
        return RedirectResponse("/cases/templates/manage?err=Vui+long+chon+file", status_code=302)
    if not file_mau.filename.lower().endswith(".docx"):
        return RedirectResponse("/cases/templates/manage?err=Chi+ho+tro+file+.docx", status_code=302)

    WORD_TEMPLATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.docx"
    saved_path = WORD_TEMPLATE_UPLOAD_DIR / saved_name
    content = await file_mau.read()
    saved_path.write_bytes(content)

    set_active = str(dat_mac_dinh).lower() in ("1", "true", "on", "yes")
    if set_active:
        db.query(WordTemplate).update({WordTemplate.is_active: False})

    item = WordTemplate(
        ten_mau=ten_mau,
        ten_file_goc=file_mau.filename,
        duong_dan_file=str(saved_path),
        is_active=set_active,
    )
    db.add(item)
    db.commit()
    return RedirectResponse("/cases/templates/manage?ok=Tai+mau+thanh+cong", status_code=302)


@router.post("/templates/manage/{tid}/activate")
def activate_word_template(tid: int, db: Session = Depends(get_db)):
    item = db.query(WordTemplate).filter(WordTemplate.id == tid).first()
    if not item:
        return RedirectResponse("/cases/templates/manage?err=Khong+tim+thay+mau", status_code=302)
    db.query(WordTemplate).update({WordTemplate.is_active: False})
    item.is_active = True
    db.commit()
    return RedirectResponse("/cases/templates/manage?ok=Da+chon+mau+mac+dinh", status_code=302)


@router.post("/templates/manage/{tid}/delete")
def delete_word_template(tid: int, db: Session = Depends(get_db)):
    item = db.query(WordTemplate).filter(WordTemplate.id == tid).first()
    if not item:
        return RedirectResponse("/cases/templates/manage?err=Khong+tim+thay+mau", status_code=302)

    was_active = bool(item.is_active)
    file_path = Path(item.duong_dan_file or "")
    db.delete(item)
    db.commit()

    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    if was_active:
        latest = db.query(WordTemplate).order_by(WordTemplate.id.desc()).first()
        if latest:
            latest.is_active = True
            db.commit()

    return RedirectResponse("/cases/templates/manage?ok=Da+xoa+mau", status_code=302)


# ── JSON API cho modal Quản lý mẫu (không rời trang) ──────────────────────────

@router.post("/templates/api/upload")
async def api_upload_template(
    ten_mau: str = Form(...),
    file_mau: UploadFile = File(...),
    dat_mac_dinh: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ten_mau = (ten_mau or "").strip()
    if not ten_mau:
        return JSONResponse({"ok": False, "err": "Vui lòng nhập tên mẫu"}, status_code=400)
    if not file_mau or not file_mau.filename:
        return JSONResponse({"ok": False, "err": "Vui lòng chọn file"}, status_code=400)
    if not file_mau.filename.lower().endswith(".docx"):
        return JSONResponse({"ok": False, "err": "Chỉ hỗ trợ file .docx"}, status_code=400)

    WORD_TEMPLATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.docx"
    saved_path = WORD_TEMPLATE_UPLOAD_DIR / saved_name
    content = await file_mau.read()
    saved_path.write_bytes(content)

    set_active = str(dat_mac_dinh).lower() in ("1", "true", "on", "yes")
    if set_active:
        db.query(WordTemplate).update({WordTemplate.is_active: False})

    item = WordTemplate(
        ten_mau=ten_mau,
        ten_file_goc=file_mau.filename,
        duong_dan_file=str(saved_path),
        is_active=set_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return JSONResponse({"ok": True, "id": item.id, "ten_mau": item.ten_mau, "is_active": item.is_active})


@router.post("/templates/api/{tid}/activate")
def api_activate_template(tid: int, db: Session = Depends(get_db)):
    item = db.query(WordTemplate).filter(WordTemplate.id == tid).first()
    if not item:
        return JSONResponse({"ok": False, "err": "Không tìm thấy mẫu"}, status_code=404)
    db.query(WordTemplate).update({WordTemplate.is_active: False})
    item.is_active = True
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/templates/api/{tid}/delete")
def api_delete_template(tid: int, db: Session = Depends(get_db)):
    item = db.query(WordTemplate).filter(WordTemplate.id == tid).first()
    if not item:
        return JSONResponse({"ok": False, "err": "Không tìm thấy mẫu"}, status_code=404)
    was_active = bool(item.is_active)
    file_path = Path(item.duong_dan_file or "")
    db.delete(item)
    db.commit()
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass
    if was_active:
        latest = db.query(WordTemplate).order_by(WordTemplate.id.desc()).first()
        if latest:
            latest.is_active = True
            db.commit()
    return JSONResponse({"ok": True})


def _fmt_date(d: Optional[date]) -> str:
    if not d:
        return ""
    return d.strftime("%d/%m/%Y")


def _fmt_birth_or_year(d: Optional[date]) -> str:
    if not d:
        return ""
    if d.day == 1 and d.month == 1:
        return str(d.year)
    return d.strftime("%d/%m/%Y")


def _safe_text(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if s == "0":
        return ""
    return s


def _so_thanh_chu(so: float) -> str:
    """Chuyển số thực (diện tích m²) thành chữ tiếng Việt."""
    if so is None:
        return ""
    don_vi = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def _doc_ba_chu_so(n: int) -> str:
        tram = n // 100
        chuc = (n % 100) // 10
        dv   = n % 10
        result = ""
        if tram:
            result += don_vi[tram] + " trăm"
            if chuc == 0 and dv:
                result += " linh " + don_vi[dv]
            elif chuc:
                result += " " + (don_vi[chuc] + " mươi" if chuc > 1 else "mười")
                if dv == 1 and chuc > 1:
                    result += " mốt"
                elif dv == 5 and chuc > 0:
                    result += " lăm"
                elif dv:
                    result += " " + don_vi[dv]
        elif chuc:
            result += (don_vi[chuc] + " mươi" if chuc > 1 else "mười")
            if dv == 1 and chuc > 1:
                result += " mốt"
            elif dv == 5 and chuc > 0:
                result += " lăm"
            elif dv:
                result += " " + don_vi[dv]
        elif dv:
            result += don_vi[dv]
        return result.strip()

    # Tách phần nguyên và thập phân
    phan_nguyen = int(so)
    phan_le_str = ""
    if so != phan_nguyen:
        le = round(so - phan_nguyen, 6)
        dec_s = f"{le:.6f}".split(".")[1].rstrip("0")
        if dec_s:
            phan_le_str = " phẩy " + " ".join(don_vi[int(d)] for d in dec_s)

    if phan_nguyen == 0:
        return ("không" + phan_le_str).strip()

    # Xử lý số nguyên
    parts = []
    n = phan_nguyen
    ty  = n // 1_000_000_000
    n %= 1_000_000_000
    tr  = n // 1_000_000
    n %= 1_000_000
    ng  = n // 1_000
    n %= 1_000
    dv3 = n

    if ty:
        parts.append(_doc_ba_chu_so(ty) + " tỷ")
    if tr:
        parts.append(_doc_ba_chu_so(tr) + " triệu")
    if ng:
        parts.append(_doc_ba_chu_so(ng) + " nghìn")
    if dv3:
        parts.append(_doc_ba_chu_so(dv3))

    return (" ".join(parts) + phan_le_str).strip()


@router.get("/{cid}/export-word-legacy")
def export_word(cid: int, db: Session = Depends(get_db)):
    """Xuat ho so thua ke ra file Word."""
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except Exception:
        raise HTTPException(status_code=500, detail="Thieu thu vien python-docx. Vui long cai requirements.")

    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)

    doc = Document()

    # Tiêu đề
    title = doc.add_heading("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("Độc lập - Tự do - Hạnh phúc")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    van_ban_name = "VĂN BẢN KHAI NHẬN DI SẢN THỪA KẾ" if case.loai_van_ban == "khai_nhan" else "VĂN BẢN THỎA THUẬN PHÂN CHIA DI SẢN THỪA KẾ"
    h = doc.add_heading(van_ban_name, level=2)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Thông tin người chết
    doc.add_heading("I. THÔNG TIN NGƯỜI ĐỂ LẠI DI SẢN", level=3)
    nd = case.nguoi_chet
    doc.add_paragraph(f"Họ và tên: {nd.ho_ten}")
    doc.add_paragraph(f"Ngày sinh: {nd.ngay_sinh.strftime('%d/%m/%Y') if nd.ngay_sinh else ''}")
    doc.add_paragraph(f"Ngày chết: {nd.ngay_chet.strftime('%d/%m/%Y') if nd.ngay_chet else ''}")
    doc.add_paragraph(f"Số CCCD/Giấy tờ: {nd.so_giay_to}")
    doc.add_paragraph(f"Địa chỉ thường trú: {nd.dia_chi}")

    doc.add_paragraph()

    # Thông tin tài sản
    doc.add_heading("II. TÀI SẢN", level=3)
    ts = case.tai_san
    doc.add_paragraph(f"Số serial GCN: {ts.so_serial}")
    doc.add_paragraph(f"Số vào sổ: {ts.so_vao_so or ''}")
    doc.add_paragraph(f"Số thửa: {ts.so_thua_dat or ''} - Tờ bản đồ số: {ts.so_to_ban_do or ''}")
    doc.add_paragraph(f"Địa chỉ: {ts.dia_chi}")
    doc.add_paragraph(f"Loại đất: {ts.loai_dat or ''}")
    doc.add_paragraph(f"Thời hạn sử dụng: {ts.thoi_han or ''}")
    doc.add_paragraph(f"Cơ quan cấp: {ts.co_quan_cap or ''}")

    doc.add_paragraph()

    # Người thừa kế
    doc.add_heading("III. NHỮNG NGƯỜI THỪA KẾ", level=3)
    nhan = [p for p in case.participants if p.co_nhan_tai_san]
    tuchoi = [p for p in case.participants if not p.co_nhan_tai_san]

    if nhan:
        doc.add_paragraph("Những người nhận thừa kế:")
        for i, p in enumerate(nhan, 1):
            c = p.customer
            ty_le = float(p.ty_le or 0)
            line = f"{i}. {c.ho_ten} - {p.vai_tro} - Ty le: {ty_le:.1f}%"
            doc.add_paragraph(line, style="List Number")

    if tuchoi:
        doc.add_paragraph()
        doc.add_paragraph("Những người từ chối nhận di sản:")
        for p in tuchoi:
            doc.add_paragraph(f"- {p.customer.ho_ten} ({p.vai_tro}): Từ chối nhận")

    doc.add_paragraph()
    doc.add_paragraph(f"Ngày lập văn bản: {case.ngay_lap_ho_so.strftime('%d tháng %m năm %Y')}")

    doc.add_paragraph()
    doc.add_paragraph("CÔNG CHỨNG VIÊN")
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph("(Ký và đóng dấu)")

    # Xuất ra stream
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = f"ho_so_thua_ke_{cid}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{cid}/export-word")
def export_word_from_template(cid: int, db: Session = Depends(get_db), template_id: Optional[str] = None):
    """Export inheritance case using the selected Word template."""
    try:
        from docx import Document
    except Exception:
        raise HTTPException(status_code=500, detail="Thieu thu vien python-docx. Vui long cai requirements.")

    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)

    # Resolve template path from template_id param
    template_path = None
    if template_id:
        if str(template_id).startswith("builtin:"):
            fname = str(template_id)[len("builtin:"):]
            p = Path("word_templates") / fname
            if p.exists():
                template_path = p
        else:
            try:
                tid = int(template_id)
                t = db.query(WordTemplate).filter(WordTemplate.id == tid).first()
                if t and t.duong_dan_file:
                    p = Path(t.duong_dan_file)
                    if p.exists():
                        template_path = p
            except (ValueError, TypeError):
                pass

    if not template_path:
        template_path = _get_selected_word_template_path(db)
    if not template_path:
        raise HTTPException(status_code=500, detail="Khong tim thay file template Word.")

    try:
        doc = Document(str(template_path))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Khong mo duoc template: {ex}")

    # Route web xuất bản đang có (không gate nhóm như batch); đọc dữ kiện B.
    mapping = word_engine.build_template_mapping(case, static=True)
    word_engine.replace_in_doc(doc, mapping)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = f"ho_so_thua_ke_{cid}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/live-preview")
def create_live_preview(
    request: Request,
    ngay_lap_ho_so: Optional[str] = Form(None),
    loai_van_ban: Optional[str] = Form("khai_nhan"),
    tai_san_id: Optional[str] = Form(None),
    ghi_chu: Optional[str] = Form(None),
    participant_id: Optional[Union[List[str], str]] = Form(None),
    participant_role: Optional[Union[List[str], str]] = Form(None),
    participant_share: Optional[Union[List[str], str]] = Form(None),
    participant_receive: Optional[Union[List[str], str]] = Form(None),
    participant_parent_id: Optional[Union[List[str], str]] = Form(None),
    db: Session = Depends(get_db)
):
    # Dummy case to use existing mapping logic
    class DummyCase:
        def __init__(self, ts, parts, loai, ngay):
            self.id = 9999
            self.tai_san = ts
            self.participants = parts
            self.loai_van_ban = loai
            self.ngay_lap_ho_so = ngay
            
            # Find owner
            self.nguoi_chet = None
            for p in parts:
                if p.vai_tro == "Owner" or p.customer_id == ts.id: # Just a fallback
                    pass # We will rely on the participants list in _pick_core_people
            
            # Actually, _pick_core_people expects nguoi_chet. 
            # Let's find the owner from the participants. Wait, in form, owner is NOT sent if we don't handle it.
            # In form: roleMap doesn't have Owner. Let's fix that.
            
    # We will build a custom HTML generator instead of relying on _build_template_mapping entirely because we want SMART documents.
    all_customers = db.query(Customer).all()
    customers_by_id = {str(c.id): c for c in all_customers}
    
    ts = db.query(Property).filter(Property.id == tai_san_id).first() if tai_san_id else None
    if not ts:
        ts = SimpleNamespace(so_serial="...", so_vao_so="...", so_thua_dat="...", so_to_ban_do="...", dia_chi="[...] Vui lòng chọn tài sản", loai_dat="", thoi_han="", nguon_goc="", ngay_cap=None, co_quan_cap="")
        
    id_list = _to_list(participant_id)
    role_list = _to_list(participant_role)
    _to_list(participant_share)
    receive_list = _to_list(participant_receive)
    parent_list = _to_list(participant_parent_id)
    
    participants = []
    owner = None
    spouses = []
    children = []
    grand = []
    parents = []
    
    for idx, cid in enumerate(id_list):
        c = customers_by_id.get(str(cid))
        if not c:
            continue
        role = role_list[idx] if idx < len(role_list) else ""
        recv = str(receive_list[idx]).lower() in ("1", "true") if idx < len(receive_list) else True
        parent_raw = parent_list[idx] if idx < len(parent_list) else ""
        parent_cid = int(parent_raw) if parent_raw and str(parent_raw).isdigit() else None
        
        # In fix_html.py we didn't map owner. The form hidden inputs do not include owner.
        # Wait, the owner IS in the form because owner card has data-role="Owner" (but roleMap in form didn't map it. Let me just use standard list)
        
        p = SimpleNamespace(customer=c, vai_tro=role, co_nhan_tai_san=recv, parent_customer_id=parent_cid)
        participants.append(p)
        
        if role in ("Cha", "Mẹ", "Cha_vc", "Me_vc"):
            parents.append(p)
        elif role == "Vợ/Chồng":
            spouses.append(p)
        elif role == "Con":
            children.append(p)
        elif role == "Cháu":
            grand.append(p)
        elif role == "Owner":
            owner = c
        
    # If owner missing (due to roleMap bug in JS we just wrote), let's guess from dead people
    if not owner:
        dead = [p.customer for p in participants if p.customer.ngay_chet]
        if dead:
            owner = dead[0]
        else:
            owner = SimpleNamespace(ho_ten="[Người để lại di sản]", so_giay_to="...", ngay_sinh=None, ngay_chet=None)

    nhan = [p for p in participants if p.co_nhan_tai_san and p.customer != owner]
    tuchoi = [p for p in participants if not p.co_nhan_tai_san and p.customer != owner]

    flags = {
        "co_nguoi_dai_dien": False,  # Later expanded using payload from frontend
    }

    ngay_lap = None
    if ngay_lap_ho_so:
        try:
            ngay_lap = datetime.strptime(ngay_lap_ho_so, "%Y-%m-%d").date()
        except Exception:
            pass

    template = templates.get_template("cases/_document_template.html")
    html = template.render({
        "loai_van_ban": loai_van_ban,
        "owner": owner,
        "spouses": spouses,
        "parents": parents,
        "children": children,
        "grand": grand,
        "nhan": nhan,
        "tuchoi": tuchoi,
        "has_tu_choi": len(tuchoi) > 0,
        "ts": ts,
        "flags": flags,
        "ngay_lap": ngay_lap
    })

    return JSONResponse({"html_content": html})

@router.post("/export-draft")
def export_draft_generic(html_content: str = Form("")):
    try:
        from docx import Document
        from htmldocx import HtmlToDocx
        doc = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html_content, doc)
    except ImportError:
        from docx import Document
        from bs4 import BeautifulSoup
        doc = Document()
        soup = BeautifulSoup(html_content, "html.parser")
        doc.add_paragraph(soup.get_text(separator='\n'))
        doc.add_paragraph("\n\n(Lỗi: Yêu cầu pip install htmldocx để kết xuất chính tả/định dạng HTML)")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    filename = f"ban_nhap_ho_so_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{cid}/preview")
def preview_word(cid: int, request: Request, db: Session = Depends(get_db)):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)
    mapping = word_engine.build_template_mapping(case, static=True)

    html_content = f"""
    <h1 style="text-align: center;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</h1>
    <h2 style="text-align: center;">Độc lập - Tự do - Hạnh phúc</h2>
    <p>&nbsp;</p>
    <h2 style="text-align: center;">{ 'VĂN BẢN KHAI NHẬN DI SẢN THỪA KẾ' if case.loai_van_ban == 'khai_nhan' else 'VĂN BẢN THỎA THUẬN PHÂN CHIA DI SẢN THỪA KẾ' }</h2>
    <p>&nbsp;</p>
    <p>Chúng tôi gồm có:</p>
    <p><b>1. {mapping.get('[Tên 1]', '')}</b> sinh năm {mapping.get('[Năm sinh 1]', '')}, CCCD số {mapping.get('[CCCD 1]', '')} cấp ngày {mapping.get('[Ngày cấp 1]', '')} tại {mapping.get('[Nơi cấp CC 1]', '')}</p>
    """
    if mapping.get('[Tên 2]', ''):
        html_content += f"""    <p><b>2. {mapping.get('[Tên 2]', '')}</b> sinh năm {mapping.get('[Năm sinh 2]', '')}, CCCD số {mapping.get('[CCCD 2]', '')} cấp ngày {mapping.get('[Ngày cấp 2]', '')}</p>"""
    
    html_content += f"""
    <p><i>(Cùng các đồng thừa kế khác...)</i></p>
    <p>&nbsp;</p>
    <h3>DI SẢN THỪA KẾ:</h3>
    <p>Giấy chứng nhận quyền sử dụng đất số <b>{mapping.get('[Serial]', '')}</b>, số vào sổ <b>{mapping.get('[Số vào sổ]', '')}</b> do {mapping.get('[Cơ quan cấp sổ]', '')} cấp ngày {mapping.get('[Ngày cấp sổ]', '')}</p>
    <p>Thửa đất số: {mapping.get('[Số thửa]', '')} - Tờ bản đồ số: {mapping.get('[Số tờ]', '')}</p>
    <p>Địa chỉ thửa đất: {mapping.get('[Địa chỉ đất]', '')}</p>
    <p>&nbsp;</p>
    """
    
    return templates.TemplateResponse("cases/preview.html", {
        "request": request, 
        "case": case,
        "html_content": html_content
    })

@router.post("/{cid}/export-preview")
def export_preview(cid: int, html_content: str = Form(""), db: Session = Depends(get_db)):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == cid).first()
    if not case:
        raise HTTPException(404)
    
    try:
        from docx import Document
        from htmldocx import HtmlToDocx
        doc = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html_content, doc)
    except ImportError:
        from docx import Document
        from bs4 import BeautifulSoup
        doc = Document()
        soup = BeautifulSoup(html_content, "html.parser")
        doc.add_paragraph(soup.get_text(separator='\n'))
        doc.add_paragraph("\n\n(Lỗi: Yêu cầu pip install htmldocx để kết xuất chính tả/định dạng HTML)")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    filename = f"ho_so_thua_ke_{cid}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
