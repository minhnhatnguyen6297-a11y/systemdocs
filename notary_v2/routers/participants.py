from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import InheritanceParticipant, InheritanceCase, case_saved_at

router = APIRouter()


def _stamp_case(db: Session, case_id: int) -> None:
    """Đóng mốc lưu của Hồ sơ cha trong CÙNG transaction với thay đổi
    participant (contract §13.20). Sửa con không làm ORM parent dirty nên
    phải UPDATE tường minh, không trông chờ onupdate."""
    db.execute(sa_text(
        "UPDATE inheritance_cases SET updated_at = :now WHERE id = :cid"),
        {"now": case_saved_at(), "cid": case_id})


@router.post("/add")
def add(
    ho_so_id: int = Form(...),
    customer_id: int = Form(...),
    vai_tro: str = Form(...),
    hang_thua_ke: int = Form(1),
    co_nhan_tai_san: Optional[str] = Form(None),
    ty_le: float = Form(0.0),
    ghi_chu: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    case = db.query(InheritanceCase).filter(InheritanceCase.id == ho_so_id).first()
    if not case:
        raise HTTPException(404, "Không tìm thấy hồ sơ")

    # Tránh thêm trùng
    exists = db.query(InheritanceParticipant).filter(
        InheritanceParticipant.ho_so_id == ho_so_id,
        InheritanceParticipant.customer_id == customer_id
    ).first()
    if not exists:
        p = InheritanceParticipant(
            ho_so_id=ho_so_id, customer_id=customer_id,
            vai_tro=vai_tro, hang_thua_ke=hang_thua_ke,
            co_nhan_tai_san=(co_nhan_tai_san == "on"),
            ty_le=ty_le, ghi_chu=ghi_chu or None
        )
        db.add(p)
        _stamp_case(db, ho_so_id)
        db.commit()
    return RedirectResponse(f"/cases/{ho_so_id}", status_code=302)


@router.post("/{pid}/edit")
def edit(
    pid: int,
    vai_tro: str = Form(...),
    hang_thua_ke: int = Form(1),
    co_nhan_tai_san: Optional[str] = Form(None),
    ty_le: float = Form(0.0),
    ghi_chu: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    p = db.query(InheritanceParticipant).filter(InheritanceParticipant.id == pid).first()
    if not p: raise HTTPException(404)

    p.vai_tro = vai_tro; p.hang_thua_ke = hang_thua_ke
    p.co_nhan_tai_san = (co_nhan_tai_san == "on")
    p.ty_le = ty_le; p.ghi_chu = ghi_chu or None
    _stamp_case(db, p.ho_so_id)
    db.commit()
    return RedirectResponse(f"/cases/{p.ho_so_id}", status_code=302)


@router.post("/{pid}/delete")
def delete(pid: int, db: Session = Depends(get_db)):
    p = db.query(InheritanceParticipant).filter(InheritanceParticipant.id == pid).first()
    if not p: raise HTTPException(404)
    case_id = p.ho_so_id
    db.delete(p)
    _stamp_case(db, case_id)
    db.commit()
    return RedirectResponse(f"/cases/{case_id}", status_code=302)
