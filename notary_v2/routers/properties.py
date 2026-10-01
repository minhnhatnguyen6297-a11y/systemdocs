from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import date, datetime

from database import (get_db, MAX_LAND_ROWS, _land_area_to_float,
                      _land_row_field)
from models import Property, PropertyLandRow

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")


def parse_date(s):
    if s and str(s).strip():
        try:
            return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


@router.get("/")
def list_properties(request: Request, db: Session = Depends(get_db), q: str = ""):
    query = db.query(Property)
    if q:
        query = query.filter(
            or_(Property.so_serial.contains(q), Property.dia_chi.contains(q),
                Property.so_thua_dat.contains(q))
        )
    props = query.order_by(Property.id.desc()).all()
    return templates.TemplateResponse("properties/list.html", {"request": request, "properties": props, "q": q})


@router.get("/create")
def create_form(request: Request):
    form = {
        "so_serial": "", "so_vao_so": "", "so_thua_dat": "", "so_to_ban_do": "",
        "dia_chi": "", "dien_tich": "", "loai_so": "", "loai_dat": "", "hinh_thuc_su_dung": "",
        "thoi_han": "", "nguon_goc": "", "ngay_cap": "", "co_quan_cap": ""
    }
    return templates.TemplateResponse("properties/form.html", {
        "request": request, "obj": None, "errors": [], "field_errors": {}, "form": form
    })


@router.post("/inline-create")
def inline_create(
    so_serial: Optional[str] = Form(None),
    so_vao_so: Optional[str] = Form(None),
    so_thua_dat: Optional[str] = Form(None),
    so_to_ban_do: Optional[str] = Form(None),
    dia_chi: Optional[str] = Form(None),
    loai_so: Optional[str] = Form(None),
    hinh_thuc_su_dung: Optional[str] = Form(None),
    nguon_goc: Optional[str] = Form(None),
    ngay_cap: Optional[str] = Form(None),
    co_quan_cap: Optional[str] = Form(None),
    land_rows: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    import json as _json
    form = {
        "so_serial": (so_serial or "").strip(),
        "so_vao_so": (so_vao_so or "").strip(),
        "so_thua_dat": (so_thua_dat or "").strip(),
        "so_to_ban_do": (so_to_ban_do or "").strip(),
        "dia_chi": (dia_chi or "").strip(),
        "loai_so": (loai_so or "").strip(),
        "hinh_thuc_su_dung": (hinh_thuc_su_dung or "").strip(),
        "nguon_goc": (nguon_goc or "").strip(),
        "ngay_cap": (ngay_cap or "").strip(),
        "co_quan_cap": (co_quan_cap or "").strip(),
        "land_rows": (land_rows or "").strip(),
    }
    errors = {}
    if not form["so_serial"]:
        errors["so_serial"] = "Bat buoc"
    if not form["dia_chi"]:
        errors["dia_chi"] = "Bat buoc"
    if form["ngay_cap"] and parse_date(form["ngay_cap"]) is None:
        errors["ngay_cap"] = "Ngay khong hop le"
    if form["so_serial"] and db.query(Property).filter(Property.so_serial == form["so_serial"]).first():
        errors["so_serial"] = "So serial da ton tai"

    # Cụm đất: parse + validate theo cùng luật Stage (dual key cũ/mới,
    # chuỗi|số đúng kiểu, tối đa MAX_LAND_ROWS) — canonical hóa ngay để
    # bảng con property_land_rows và mirror land_rows_json ghi cùng một
    # transaction, không lệch nhau (MIN-141 đợt 2 fix).
    normalized_rows = []
    if form["land_rows"]:
        try:
            rows = _json.loads(form["land_rows"])
        except Exception:
            rows = None
        if not isinstance(rows, list):
            errors["land_rows"] = "Land_rows phai la mang JSON"
        elif len(rows) > MAX_LAND_ROWS:
            errors["land_rows"] = (
                f"Land_rows toi da {MAX_LAND_ROWS} cum moi tai san")
        else:
            for index, r in enumerate(rows):
                if not isinstance(r, dict):
                    errors["land_rows"] = (
                        f"land_rows[{index}] phai la object")
                    break
                vals, conflict_key = {}, None
                for new_key, old_key in (("loaidat", "loai_dat"),
                                         ("dientich", "dien_tich"),
                                         ("thoihan", "thoi_han")):
                    vals[new_key], c = _land_row_field(r, new_key, old_key)
                    if c:
                        conflict_key = (new_key, old_key)
                if conflict_key:
                    errors["land_rows"] = (
                        f"land_rows[{index}] '{conflict_key[0]}' va "
                        f"'{conflict_key[1]}' mau thuan")
                    break
                if (vals["loaidat"] is not None
                        and not isinstance(vals["loaidat"], str)):
                    errors["land_rows"] = (
                        f"land_rows[{index}].loaidat phai la chuoi "
                        "hoac null")
                    break
                if (vals["thoihan"] is not None
                        and not isinstance(vals["thoihan"], str)):
                    errors["land_rows"] = (
                        f"land_rows[{index}].thoihan phai la chuoi "
                        "hoac null")
                    break
                try:
                    dien = _land_area_to_float(vals["dientich"])
                except (ValueError, TypeError):
                    errors["land_rows"] = (
                        f"land_rows[{index}].dientich khong phai so")
                    break
                normalized_rows.append({
                    "loaidat": (vals["loaidat"].strip() or None
                                if isinstance(vals["loaidat"], str)
                                else None),
                    "dientich": dien,
                    "thoihan": (vals["thoihan"].strip() or None
                                if isinstance(vals["thoihan"], str)
                                else None),
                })

    if errors:
        return JSONResponse({"ok": False, "errors": errors},
                            status_code=400)

    loai_dat_val = ""
    thoi_han_val = ""
    dien_tich_total = None
    land_rows_json_val = None
    if normalized_rows:
        parts = []
        total = 0.0
        for r in normalized_rows:
            dien_s = ("" if r["dientich"] is None else
                      ("%g" % r["dientich"]))
            if r["loaidat"] or r["dientich"] is not None or r["thoihan"]:
                parts.append(
                    f"{r['loaidat'] or ''} | {dien_s}m2 | "
                    f"{r['thoihan'] or ''}")
            if r["dientich"]:
                total += r["dientich"]
        loai_dat_val = "; ".join(parts)
        thoi_han_val = normalized_rows[0]["thoihan"] or ""
        if total > 0:
            dien_tich_total = total
        # Mirror legacy keys — đúng shape migrate_property_land_rows ghi.
        land_rows_json_val = _json.dumps([
            {"loai_dat": r["loaidat"],
             "dien_tich": (int(r["dientich"])
                           if isinstance(r["dientich"], float)
                           and r["dientich"].is_integer()
                           else r["dientich"]),
             "thoi_han": r["thoihan"]}
            for r in normalized_rows], ensure_ascii=False)

    p = Property(
        so_serial=form["so_serial"], so_vao_so=form["so_vao_so"] or None,
        so_thua_dat=form["so_thua_dat"] or None, so_to_ban_do=form["so_to_ban_do"] or None,
        dia_chi=form["dia_chi"], loai_dat=loai_dat_val or None,
        dien_tich=dien_tich_total, loai_so=form["loai_so"] or None,
        land_rows_json=land_rows_json_val,
        hinh_thuc_su_dung=form["hinh_thuc_su_dung"] or None,
        thoi_han=thoi_han_val or None,
        nguon_goc=form["nguon_goc"] or None, ngay_cap=parse_date(form["ngay_cap"]),
        co_quan_cap=form["co_quan_cap"] or None
    )
    p.land_rows = [
        PropertyLandRow(vitri=i + 1, loaidat=r["loaidat"],
                        dientich=r["dientich"], thoihan=r["thoihan"])
        for i, r in enumerate(normalized_rows)]
    db.add(p); db.commit(); db.refresh(p)
    return JSONResponse({
        "ok": True,
        "property": {
            "id": p.id,
            "so_serial": p.so_serial,
            "so_thua_dat": p.so_thua_dat or "",
            "dia_chi": p.dia_chi or "",
            "ngay_cap": p.ngay_cap.isoformat() if p.ngay_cap else "",
            "dien_tich": p.dien_tich,
        }
    })


@router.post("/create")
def create(
    request: Request,
    so_serial: Optional[str] = Form(None),
    so_vao_so: Optional[str] = Form(None),
    so_thua_dat: Optional[str] = Form(None),
    so_to_ban_do: Optional[str] = Form(None),
    dia_chi: Optional[str] = Form(None),
    dien_tich: Optional[str] = Form(None),
    loai_so: Optional[str] = Form(None),
    loai_dat: Optional[str] = Form(None),
    hinh_thuc_su_dung: Optional[str] = Form(None),
    thoi_han: Optional[str] = Form(None),
    nguon_goc: Optional[str] = Form(None),
    ngay_cap: Optional[str] = Form(None),
    co_quan_cap: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    form = {
        "so_serial": (so_serial or "").strip(),
        "so_vao_so": (so_vao_so or "").strip(),
        "so_thua_dat": (so_thua_dat or "").strip(),
        "so_to_ban_do": (so_to_ban_do or "").strip(),
        "dia_chi": (dia_chi or "").strip(),
        "dien_tich": (dien_tich or "").strip(),
        "loai_so": (loai_so or "").strip(),
        "loai_dat": (loai_dat or "").strip(),
        "hinh_thuc_su_dung": (hinh_thuc_su_dung or "").strip(),
        "thoi_han": (thoi_han or "").strip(),
        "nguon_goc": (nguon_goc or "").strip(),
        "ngay_cap": (ngay_cap or "").strip(),
        "co_quan_cap": (co_quan_cap or "").strip(),
    }
    errors = []
    field_errors = {}
    if not form["so_serial"]:
        field_errors["so_serial"] = "Bat buoc"
    if not form["dia_chi"]:
        field_errors["dia_chi"] = "Bat buoc"
    if form["ngay_cap"] and parse_date(form["ngay_cap"]) is None:
        field_errors["ngay_cap"] = "Ngay khong hop le"

    if form["so_serial"] and db.query(Property).filter(Property.so_serial == form["so_serial"]).first():
        field_errors["so_serial"] = "So serial da ton tai"
        errors.append(f"Số serial '{form['so_serial']}' đã tồn tại!")

    if field_errors:
        return templates.TemplateResponse("properties/form.html", {
            "request": request, "obj": None, "errors": errors,
            "field_errors": field_errors, "form": form
        })

    dien_tich_val = None
    try:
        dien_tich_val = float(form["dien_tich"]) if form["dien_tich"] else None
    except (ValueError, TypeError):
        pass

    p = Property(
        so_serial=form["so_serial"], so_vao_so=form["so_vao_so"] or None,
        so_thua_dat=form["so_thua_dat"] or None, so_to_ban_do=form["so_to_ban_do"] or None,
        dia_chi=form["dia_chi"], dien_tich=dien_tich_val,
        loai_so=form["loai_so"] or None, loai_dat=form["loai_dat"] or None,
        hinh_thuc_su_dung=form["hinh_thuc_su_dung"] or None, thoi_han=form["thoi_han"] or None,
        nguon_goc=form["nguon_goc"] or None, ngay_cap=parse_date(form["ngay_cap"]),
        co_quan_cap=form["co_quan_cap"] or None
    )
    db.add(p); db.commit()
    return RedirectResponse("/properties", status_code=302)


@router.get("/{pid}")
def detail(pid: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == pid).first()
    if not p: raise HTTPException(404)
    return templates.TemplateResponse("properties/detail.html", {"request": request, "obj": p})


@router.get("/{pid}/edit")
def edit_form(pid: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == pid).first()
    if not p: raise HTTPException(404)
    form = {
        "so_serial": p.so_serial or "",
        "so_vao_so": p.so_vao_so or "",
        "so_thua_dat": p.so_thua_dat or "",
        "so_to_ban_do": p.so_to_ban_do or "",
        "dia_chi": p.dia_chi or "",
        "dien_tich": str(p.dien_tich) if p.dien_tich is not None else "",
        "loai_so": p.loai_so or "",
        "loai_dat": p.loai_dat or "",
        "hinh_thuc_su_dung": p.hinh_thuc_su_dung or "",
        "thoi_han": p.thoi_han or "",
        "nguon_goc": p.nguon_goc or "",
        "ngay_cap": p.ngay_cap.isoformat() if p.ngay_cap else "",
        "co_quan_cap": p.co_quan_cap or "",
    }
    return templates.TemplateResponse("properties/form.html", {
        "request": request, "obj": p, "errors": [], "field_errors": {}, "form": form
    })


@router.post("/{pid}/edit")
def edit(
    pid: int, request: Request,
    so_serial: Optional[str] = Form(None), so_vao_so: Optional[str] = Form(None),
    so_thua_dat: Optional[str] = Form(None), so_to_ban_do: Optional[str] = Form(None),
    dia_chi: Optional[str] = Form(None), dien_tich: Optional[str] = Form(None),
    loai_so: Optional[str] = Form(None), loai_dat: Optional[str] = Form(None),
    hinh_thuc_su_dung: Optional[str] = Form(None), thoi_han: Optional[str] = Form(None),
    nguon_goc: Optional[str] = Form(None), ngay_cap: Optional[str] = Form(None),
    co_quan_cap: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    p = db.query(Property).filter(Property.id == pid).first()
    if not p: raise HTTPException(404)
    form = {
        "so_serial": (so_serial or "").strip(),
        "so_vao_so": (so_vao_so or "").strip(),
        "so_thua_dat": (so_thua_dat or "").strip(),
        "so_to_ban_do": (so_to_ban_do or "").strip(),
        "dia_chi": (dia_chi or "").strip(),
        "dien_tich": (dien_tich or "").strip(),
        "loai_so": (loai_so or "").strip(),
        "loai_dat": (loai_dat or "").strip(),
        "hinh_thuc_su_dung": (hinh_thuc_su_dung or "").strip(),
        "thoi_han": (thoi_han or "").strip(),
        "nguon_goc": (nguon_goc or "").strip(),
        "ngay_cap": (ngay_cap or "").strip(),
        "co_quan_cap": (co_quan_cap or "").strip(),
    }
    errors = []
    field_errors = {}
    if not form["so_serial"]:
        field_errors["so_serial"] = "Bat buoc"
    if not form["dia_chi"]:
        field_errors["dia_chi"] = "Bat buoc"
    if form["ngay_cap"] and parse_date(form["ngay_cap"]) is None:
        field_errors["ngay_cap"] = "Ngay khong hop le"

    if form["so_serial"]:
        dup = db.query(Property).filter(Property.so_serial == form["so_serial"], Property.id != pid).first()
        if dup:
            field_errors["so_serial"] = "So serial da ton tai"
            errors.append(f"Số serial '{form['so_serial']}' đã tồn tại!")

    if field_errors:
        return templates.TemplateResponse("properties/form.html", {
            "request": request, "obj": p, "errors": errors,
            "field_errors": field_errors, "form": form
        })

    dien_tich_val = None
    try:
        dien_tich_val = float(form["dien_tich"]) if form["dien_tich"] else None
    except (ValueError, TypeError):
        pass

    p.so_serial = form["so_serial"]; p.so_vao_so = form["so_vao_so"] or None
    p.so_thua_dat = form["so_thua_dat"] or None; p.so_to_ban_do = form["so_to_ban_do"] or None
    p.dia_chi = form["dia_chi"]; p.dien_tich = dien_tich_val
    p.loai_so = form["loai_so"] or None; p.loai_dat = form["loai_dat"] or None
    p.hinh_thuc_su_dung = form["hinh_thuc_su_dung"] or None; p.thoi_han = form["thoi_han"] or None
    p.nguon_goc = form["nguon_goc"] or None; p.ngay_cap = parse_date(form["ngay_cap"])
    p.co_quan_cap = form["co_quan_cap"] or None
    db.commit()
    return RedirectResponse(f"/properties/{pid}", status_code=302)


@router.post("/{pid}/delete")
def delete(pid: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == pid).first()
    if p: db.delete(p); db.commit()
    return RedirectResponse("/properties", status_code=302)
