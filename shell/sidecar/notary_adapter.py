"""Adapter notary_v2 — goi engine that tu codex/zalo-document-inbox-v2.

Khong viet lai nghiep vu: moi thao tac deu qua models/services/router
handlers cua repo con. Write path (customer/property/case/participant) goi
dung inline-create/participant handlers → giu nguyen validation, upsert va
business rule (locked case, dedup, unique serial).

DB: notary.db cua engine root (database.py neo theo __file__). Sidecar la
owner ghi duy nhat — renderer khong bao gio cham DB (g1-module-data §5).
"""
import asyncio
import io
import json
from datetime import date, datetime
from pathlib import Path

from errors import CommandError
from engine_roots import engine_root, import_engine_module, output_dir


_db_ready = False


def _ensure_db():
    """Khoi tao schema notary.db lan dau — cung loat migrate nhu main.py."""
    global _db_ready
    if _db_ready:
        return
    database = import_engine_module("notary_v2", "database")
    database.migrate_customers_nullable()
    database.migrate_inheritance_cases_schema()
    database.migrate_properties_schema()
    database.migrate_inheritance_case_properties_schema()
    database.migrate_zalo_schema()
    database.Base.metadata.create_all(bind=database.engine)
    _db_ready = True


def _db_session():
    _ensure_db()
    database = import_engine_module("notary_v2", "database")
    return database.SessionLocal()


def _models():
    return import_engine_module("notary_v2", "models")


def _svc(name):
    return import_engine_module("notary_v2", f"services.{name}")


def _router(name):
    return import_engine_module("notary_v2", f"routers.{name}")


def _d(value):
    """date/datetime → ISO; giu None; khong suy luan."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _json_param(resp):
    """Route handler tra JSONResponse → dict; khong ok → CommandError."""
    body = json.loads(resp.body.decode("utf-8"))
    if not body.get("ok"):
        errs = body.get("errors") or {}
        msg = "; ".join(f"{k}: {v}" for k, v in errs.items()) or "that bai"
        raise CommandError("validation_error", msg, details=errs)
    return body


def _require(value, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise CommandError("validation_error", f"thieu {field}")
    return value


def _int_id(value, field):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CommandError("validation_error",
                           f"{field} phai la so nguyen") from exc


# ---------- doc ----------

def _customer_row(c):
    return {
        "id": c.id, "ho_ten": c.ho_ten, "gioi_tinh": c.gioi_tinh,
        "ngay_sinh": _d(c.ngay_sinh), "ngay_chet": _d(c.ngay_chet),
        "so_giay_to": c.so_giay_to, "ngay_cap": _d(c.ngay_cap),
        "dia_chi": c.dia_chi, "con_song": c.con_song,
    }


def _property_row(p):
    return {
        "id": p.id, "so_serial": p.so_serial, "so_vao_so": p.so_vao_so,
        "so_thua_dat": p.so_thua_dat, "so_to_ban_do": p.so_to_ban_do,
        "dia_chi": p.dia_chi, "loai_dat": p.loai_dat,
        "dien_tich": p.dien_tich, "loai_so": p.loai_so,
        "hinh_thuc_su_dung": p.hinh_thuc_su_dung, "thoi_han": p.thoi_han,
        "nguon_goc": p.nguon_goc, "ngay_cap": _d(p.ngay_cap),
        "co_quan_cap": p.co_quan_cap,
    }


def _case_row(c):
    return {
        "id": c.id,
        "nguoi_chet": _customer_row(c.nguoi_chet) if c.nguoi_chet else None,
        "tai_san": _property_row(c.tai_san) if c.tai_san else None,
        "ngay_lap_ho_so": _d(c.ngay_lap_ho_so),
        "loai_van_ban": c.loai_van_ban, "trang_thai": c.trang_thai,
        "noi_niem_yet": c.noi_niem_yet, "ghi_chu": c.ghi_chu,
        "is_locked": c.is_locked, "tong_ty_le": c.tong_ty_le,
    }


def _result(kind, data, warnings=None, source_files=None, evidence=None):
    return {
        "kind": kind, "data": data,
        "evidence": evidence or [],
        "warnings": warnings or [],
        "source_files": source_files or [],
    }


def case_list(job, payload):
    models = _models()
    q = str((payload or {}).get("query") or "").strip()
    limit = max(1, min(int((payload or {}).get("limit") or 50), 200))
    sess = _db_session()
    try:
        query = sess.query(models.InheritanceCase)
        rows = query.order_by(models.InheritanceCase.id.desc()).limit(limit).all()
        items = [_case_row(c) for c in rows]
        if q:
            ql = q.lower()
            items = [i for i in items
                     if ql in json.dumps(i, ensure_ascii=False).lower()]
        job.check_cancel()
        return _result("case_list", {"cases": items, "total": len(items)})
    finally:
        sess.close()


def case_get(job, payload):
    models = _models()
    cid = _int_id(_require((payload or {}).get("case_id"), "case_id"),
                  "case_id")
    sess = _db_session()
    try:
        case = sess.query(models.InheritanceCase).filter(
            models.InheritanceCase.id == cid).first()
        if case is None:
            raise CommandError("file_not_found",
                               f"khong co ho so #{cid}")
        participants = [{
            "id": p.id, "customer": _customer_row(p.customer),
            "vai_tro": p.vai_tro, "hang_thua_ke": p.hang_thua_ke,
            "co_nhan_tai_san": p.co_nhan_tai_san, "ty_le": p.ty_le,
            "ghi_chu": p.ghi_chu,
        } for p in case.participants]
        linked = [{
            "property": _property_row(link.property),
            "is_primary": link.is_primary,
        } for link in case.property_links]
        job.check_cancel()
        data = _case_row(case)
        data["participants"] = participants
        data["properties"] = linked
        data["has_engine_state"] = bool(case.engine_state_json)
        data["has_case_state"] = bool(case.case_state_json)
        return _result("case_detail", data)
    finally:
        sess.close()


def customer_list(job, payload):
    customers = _router("customers")
    q = str((payload or {}).get("query") or "")
    limit = max(1, min(int((payload or {}).get("limit") or 50), 200))
    sess = _db_session()
    try:
        # Route that tra JSONResponse {"ok": true, "data": [...]}.
        resp = customers.search_customers(sess, q=q, limit=limit)
        rows = _json_param(resp).get("data") or []
        job.check_cancel()
        return _result("customer_list", {"customers": rows,
                                         "total": len(rows)})
    finally:
        sess.close()


def customer_create(job, payload):
    customers = _router("customers")
    p = payload or {}
    sess = _db_session()
    try:
        resp = customers.inline_create(
            ho_ten=_require(p.get("ho_ten"), "ho_ten"),
            gioi_tinh=p.get("gioi_tinh"),
            ngay_sinh=p.get("ngay_sinh"),
            ngay_chet=p.get("ngay_chet"),
            so_giay_to=p.get("so_giay_to"),
            ngay_cap=p.get("ngay_cap"),
            dia_chi=p.get("dia_chi"),
            db=sess)
        body = _json_param(resp)
        ev = []
        cust = body.get("customer") or {}
        sgt = cust.get("so_giay_to")
        if sgt:
            ev.append({
                "kind": "cccd", "value": sgt,
                "normalized_value": sgt if len(str(sgt)) == 12 else None,
                "observation_state": "confirmed" if len(str(sgt)) == 12
                else "observed",
                "source_ref": f"customer:{cust.get('id')}",
            })
        return _result("customer_upsert",
                       {"customer": cust, "updated": body.get("updated", False)},
                       evidence=ev)
    finally:
        sess.close()


def property_list(job, payload):
    models = _models()
    q = str((payload or {}).get("query") or "").strip().lower()
    limit = max(1, min(int((payload or {}).get("limit") or 50), 200))
    sess = _db_session()
    try:
        rows = sess.query(models.Property).order_by(
            models.Property.id.desc()).limit(limit).all()
        items = [_property_row(p) for p in rows]
        if q:
            items = [i for i in items
                     if q in json.dumps(i, ensure_ascii=False).lower()]
        job.check_cancel()
        return _result("property_list", {"properties": items,
                                         "total": len(items)})
    finally:
        sess.close()


def property_create(job, payload):
    props = _router("properties")
    p = payload or {}
    sess = _db_session()
    try:
        resp = props.inline_create(
            so_serial=_require(p.get("so_serial"), "so_serial"),
            so_vao_so=p.get("so_vao_so"), so_thua_dat=p.get("so_thua_dat"),
            so_to_ban_do=p.get("so_to_ban_do"),
            dia_chi=_require(p.get("dia_chi"), "dia_chi"),
            loai_so=p.get("loai_so"),
            hinh_thuc_su_dung=p.get("hinh_thuc_su_dung"),
            nguon_goc=p.get("nguon_goc"), ngay_cap=p.get("ngay_cap"),
            co_quan_cap=p.get("co_quan_cap"),
            land_rows=json.dumps(p["land_rows"], ensure_ascii=False)
            if p.get("land_rows") else None,
            db=sess)
        body = _json_param(resp)
        return _result("property_upsert",
                       {"property": body.get("property")})
    finally:
        sess.close()


def case_create(job, payload):
    models = _models()
    p = payload or {}
    nguoi_id = _int_id(_require(p.get("nguoi_chet_id"), "nguoi_chet_id"),
                       "nguoi_chet_id")
    tai_san_id = _int_id(_require(p.get("tai_san_id"), "tai_san_id"),
                         "tai_san_id")
    ngay = p.get("ngay_lap_ho_so") or date.today().isoformat()
    try:
        ngay_lap = date.fromisoformat(str(ngay))
    except ValueError as exc:
        raise CommandError("validation_error",
                           "ngay_lap_ho_so phai dang yyyy-mm-dd") from exc
    loai = str(p.get("loai_van_ban") or "khai_nhan")
    if loai not in ("khai_nhan", "thoa_thuan"):
        raise CommandError("validation_error",
                           "loai_van_ban ∈ {khai_nhan, thoa_thuan}")
    sess = _db_session()
    try:
        if not sess.get(models.Customer, nguoi_id):
            raise CommandError("file_not_found",
                               f"khong co khach hang #{nguoi_id}")
        if not sess.get(models.Property, tai_san_id):
            raise CommandError("file_not_found",
                               f"khong co tai san #{tai_san_id}")
        case = models.InheritanceCase(
            nguoi_chet_id=nguoi_id, tai_san_id=tai_san_id,
            ngay_lap_ho_so=ngay_lap, loai_van_ban=loai,
            noi_niem_yet=p.get("noi_niem_yet") or None,
            ghi_chu=p.get("ghi_chu") or None,
            trang_thai="draft")
        sess.add(case)
        sess.commit()
        sess.refresh(case)
        return _result("case_created", {"case": _case_row(case)})
    finally:
        sess.close()


def participant_add(job, payload):
    participants = _router("participants")
    p = payload or {}
    sess = _db_session()
    try:
        # Handler that cua repo: kiem case locked + dedup ben trong, loi la
        # HTTPException(400); thanh cong tra RedirectResponse(302).
        from fastapi import HTTPException
        try:
            participants.add(
                ho_so_id=_int_id(_require(p.get("case_id"), "case_id"),
                                 "case_id"),
                customer_id=_int_id(
                    _require(p.get("customer_id"), "customer_id"),
                    "customer_id"),
                vai_tro=_require(p.get("vai_tro"), "vai_tro"),
                hang_thua_ke=int(p.get("hang_thua_ke") or 1),
                co_nhan_tai_san="on"
                if p.get("co_nhan_tai_san", True) else None,
                ty_le=float(p.get("ty_le") or 0.0),
                ghi_chu=p.get("ghi_chu"),
                db=sess)
        except HTTPException as exc:
            raise CommandError("validation_error",
                               str(exc.detail)) from exc
        return _result("participant_added",
                       {"case_id": _int_id(p.get("case_id"), "case_id")})
    finally:
        sess.close()


# ---------- word export ----------

def _resolve_template(sess, template_id):
    """Replicate routers/cases.py:_get_selected_word_template_path nhung
    resolve path tuyet doi theo engine root (cwd cua sidecar khong phai repo).
    Bo qua fallback UNC — contract §6 cam UNC trong G1-SM."""
    root = engine_root("notary_v2")
    models = _models()

    def _rel_or_abs(raw):
        p = Path(str(raw))
        return p if p.is_absolute() else (root / p)

    if template_id:
        tid = str(template_id)
        if tid.startswith("builtin:"):
            p = _rel_or_abs(Path("word_templates") / tid[len("builtin:"):])
            if p.exists():
                return p
        else:
            try:
                t = sess.get(models.WordTemplate, int(tid))
            except (TypeError, ValueError):
                t = None
            if t and t.duong_dan_file:
                p = _rel_or_abs(t.duong_dan_file)
                if p.exists():
                    return p
    active = (sess.query(models.WordTemplate)
              .filter(models.WordTemplate.is_active)
              .order_by(models.WordTemplate.id.desc()).first())
    if active and active.duong_dan_file:
        p = _rel_or_abs(active.duong_dan_file)
        if p.exists():
            return p
    for rel in ("word_templates/1. PCDS .docx",
                "word_templates/xa_PCDS_template.docx"):
        p = root / rel
        if p.exists():
            return p
    return None


def word_templates(job, payload):
    root = engine_root("notary_v2")
    models = _models()
    we = _svc("word_engine")
    sess = _db_session()
    try:
        custom = [{
            "id": t.id, "ten_mau": t.ten_mau,
            "is_active": bool(t.is_active),
            "builtin": False,
            "path": t.duong_dan_file,
        } for t in sess.query(models.WordTemplate).all()]
        builtin = we.list_public_builtin_templates(root / "word_templates")
        return _result("template_list",
                       {"templates": builtin + custom})
    finally:
        sess.close()


def export_word(job, payload):
    """Route that /{cid}/export-word qua services.word_engine — ket qua la
    file .docx trong G1_OUTPUT_DIR (sidecar so huu output)."""
    models = _models()
    we = _svc("word_engine")
    cid = _int_id(_require((payload or {}).get("case_id"), "case_id"),
                  "case_id")
    template_id = (payload or {}).get("template_id")
    job.report_progress(0, 3, "doc ho so")
    sess = _db_session()
    try:
        case = sess.query(models.InheritanceCase).filter(
            models.InheritanceCase.id == cid).first()
        if case is None:
            raise CommandError("file_not_found",
                               f"khong co ho so #{cid}")
        template_path = _resolve_template(sess, template_id)
        if not template_path:
            raise CommandError(
                "engine_unavailable",
                "khong tim thay template Word (chon word_templates/*.docx)",
                retryable=False)
        job.report_progress(1, 3, "build mapping")
        try:
            import docx
            doc = docx.Document(str(template_path))
        except Exception as exc:
            raise CommandError("engine_unavailable",
                               f"khong mo duoc template: {exc}") from exc
        try:
            mapping = we.build_template_mapping(case)
        except we.WordExportValidationError as exc:
            raise CommandError("validation_error", str(exc)) from exc
        we.replace_in_doc(doc, mapping)
        unresolved = we.find_unresolved_placeholders(doc)
        if unresolved:
            raise CommandError(
                "validation_error",
                "template con placeholder chua ho tro: "
                + ", ".join(unresolved),
                details={"unresolved": unresolved})
        job.report_progress(2, 3, "ghi docx")
        out_dir = output_dir("exports")
        out_path = out_dir / f"ho_so_thua_ke_{cid}.docx"
        doc.save(str(out_path))
        job.check_cancel()
        job.report_progress(3, 3, "xong")
        return _result(
            "word_export",
            {"case_id": cid, "template": str(template_path),
             "output_file": {"path": str(out_path), "scope": "machine_local"},
             "placeholders_filled": len(mapping)},
            source_files=[{"path": str(template_path),
                           "scope": "machine_local"}])
    finally:
        sess.close()


# ---------- OCR (cloud Qwen qua routers/ocr_ai that) ----------

def ocr_analyze(job, payload):
    """Intake OCR: goi ham analyze_images that (DashScope native + parse
    persons/properties/pairs). observation_state=observed — chua confirm
    khong bao gio thanh truth (g1-module-data §1)."""
    refs = (payload or {}).get("files")
    if not isinstance(refs, list) or not refs:
        raise CommandError("validation_error", "can files: [file_ref]")
    if len(refs) > 8:
        raise CommandError("validation_error", "toi da 8 anh/lan")
    ocr = _router("ocr_ai")
    model = ocr._get_model()
    if not ocr._get_api_key():
        raise CommandError(
            "ocr.engine_unavailable",
            "thieu API key OCR (QWEN_API_KEY/DASHSCOPE_API_KEY trong "
            "<notary_v2>/.env)", retryable=False,
            next_action="dat key vao .env engine roi thu lai")
    from fastapi import UploadFile
    from fileref import existing_file
    uploads = []
    paths = []
    for ref in refs:
        p = existing_file(ref)
        paths.append(p)
        uploads.append(UploadFile(
            filename=p.name, file=io.BytesIO(p.read_bytes())))
    job.report_progress(0, len(uploads), "ocr cloud")
    try:
        result = asyncio.run(ocr.analyze_images(files=uploads))
    except Exception as exc:
        raise CommandError("ocr.engine_unavailable",
                           f"{type(exc).__name__}: {exc}",
                           retryable=True) from exc
    job.check_cancel()
    evidence = []
    for person in result.get("persons") or []:
        id12 = person.get("so_giay_to") or person.get("id12") or ""
        ev = {
            "kind": "person_identity",
            "value": person.get("ho_ten") or "",
            "normalized_value": str(id12) if len(str(id12)) == 12 else None,
            "observation_state": "observed",
            "source_ref": "ocr.analyze",
        }
        evidence.append(ev)
    warnings = [{"code": "unconfirmed",
                 "message": "ket qua OCR la observed — can nguoi confirm "
                            "truoc khi thanh du lieu"}]
    return _result(
        "ocr_result",
        {"model": model, "persons": result.get("persons") or [],
         "properties": result.get("properties") or [],
         "marriages": result.get("marriages") or [],
         "errors": result.get("errors") or [],
         "summary": result.get("summary") or {}},
        warnings=warnings, evidence=evidence,
        source_files=[{"path": str(p), "scope": "machine_local"}
                      for p in paths])


# ---------- Zalo Inbox (doc trang thai that) ----------

def zalo_status(job, payload):
    models = _models()
    zalo = _svc("zalo_inbox")
    sess = _db_session()
    try:
        accounts = sess.query(models.ZaloConnectorAccount).all()
        account_rows = [{
            "id": a.id, "bound_zalo_id": a.bound_zalo_id,
            "session_state": a.session_state,
            "connector_state": zalo.connector_state(a),
            "last_seen_at": _d(a.last_seen_at),
            "intake_consented": a.intake_consented_at is not None,
            "policy_version": a.policy_version,
        } for a in accounts]
        sources = sess.query(models.ZaloSource).all()
        batches = sess.query(models.ZaloBatch).order_by(
            models.ZaloBatch.id.desc()).limit(10).all()
        job.check_cancel()
        return _result("zalo_status", {
            "accounts": account_rows,
            "sources": [{
                "id": s.id, "display_name": s.display_name,
                "conversation_type": s.conversation_type,
                "enabled": s.enabled, "ready": zalo.source_ready(s),
            } for s in sources],
            "recent_batches": [{
                "id": b.id,
                "status": getattr(b, "status", None),
                "created_at": _d(getattr(b, "created_at", None)),
            } for b in batches],
            "totals": {
                "accounts": len(accounts), "sources": len(sources),
                "media": sess.query(models.ZaloMedia).count(),
                "message_texts": sess.query(models.ZaloMessageText).count(),
            },
        })
    finally:
        sess.close()


# ---------- Case workspace (MIN-107 — contract notary.case-drafting.v1) ----------

# next_action phai nam trong envelope enum
# (login_required|pick_files|retry|contact_admin|null):
#   workspace_conflict      → retryable, client doc lai workspace roi retry
#   stage_validation_error  → khong retryable (payload sai retry mu se lai sai)
_WORKSPACE_RETRYABLE_CODES = {"workspace_conflict"}


def _workspace_command_error(err):
    """WorkspaceError cua service → CommandError theo contract §9.

    Giu nguyen `code`/`details` (server_revision, field_errors, ...).
    """
    code = getattr(err, "code", None) or "workspace_error"
    message = getattr(err, "message", None) or str(err) or code
    details = getattr(err, "details", None) or None
    retryable = code in _WORKSPACE_RETRYABLE_CODES
    return CommandError(
        code, message, retryable=retryable,
        next_action="retry" if retryable else None,
        details=details)


def _workspace_module():
    return _svc("case_workspace")


def workspace_get(job, payload):
    """notary.workspace_get — doc workspace + stage + diagram V2."""
    if not isinstance(payload, dict):
        payload = {}
    case_id = _int_id(_require(payload.get("case_id"), "case_id"),
                      "case_id")
    sess = _db_session()
    try:
        module = _workspace_module()
        try:
            data = module.CaseWorkspaceService(sess).get(case_id)
        except module.WorkspaceError as err:
            raise _workspace_command_error(err)
        job.check_cancel()
        return _result("workspace_get", data)
    finally:
        sess.close()


def workspace_commit_stage(job, payload):
    """notary.workspace_commit_stage — commit Stage nguyen tu + revision."""
    if not isinstance(payload, dict):
        payload = {}
    case_id = _int_id(_require(payload.get("case_id"), "case_id"), "case_id")
    base_revision = _int_id(
        _require(payload.get("base_revision"), "base_revision"),
        "base_revision")
    stage = payload.get("stage")
    if not isinstance(stage, dict):
        raise CommandError("validation_error", "stage phai la object")
    people = stage.get("people")
    assets = stage.get("assets")
    if not isinstance(people, list) or not isinstance(assets, list):
        raise CommandError(
            "validation_error",
            "stage.people/stage.assets phai la danh sach")
    sess = _db_session()
    try:
        module = _workspace_module()
        try:
            data = module.CaseWorkspaceService(sess).commit_stage(
                case_id, base_revision, people, assets)
        except module.WorkspaceError as err:
            raise _workspace_command_error(err)
        job.check_cancel()
        return _result("workspace_commit_stage", data)
    finally:
        sess.close()


# ---------- document intake da nguon (MIN-108, notary.case-drafting.v1) ----------

def intake_analyze(job, payload):
    """notary.intake_analyze: 5 source kinds → suggestions theo contract.

    Sidecar chi map envelope ↔ service; toan bo validate/parse/normalize nam
    trong notary_v2.services.document_intake (dung chung voi web OCR path).
    Mot source loi khong huy sources khac (partial + breakdown).
    """
    svc = _svc("document_intake.service")
    p = payload or {}
    extra = set(p) - {"case_id", "sources"}
    if extra:
        raise CommandError("validation_error",
                           f"payload co key ngoai schema: {sorted(extra)}")
    cid = _int_id(_require(p.get("case_id"), "case_id"), "case_id")
    if cid < 1:
        raise CommandError("validation_error", "case_id phai >= 1")
    sources = p.get("sources")
    if not isinstance(sources, list) or not sources:
        raise CommandError("validation_error", "can sources: [..]")

    models = _models()
    sess = _db_session()
    try:
        case = sess.get(models.InheritanceCase, cid)
        if case is None:
            raise CommandError("case_not_found",
                               f"khong co ho so #{cid}")
        # case_type: engine DB hien chi co InheritanceCase nen
        # case_type_unsupported unreachable — khi case_type thanh column
        # phai guard tai day (contract §5.3).
        if case.is_locked:
            raise CommandError("workspace_locked",
                               f"ho so #{cid} da khoa")
    finally:
        sess.close()

    def _progress(done, _total, label=""):
        job.report_progress(done, _total, label)

    try:
        outcome = svc.analyze(
            sources,
            check_cancel=job.check_cancel,
            report_progress=_progress)
    except svc.IntakeError as exc:
        raise CommandError(exc.code, exc.message,
                           details=exc.details) from exc
    job.check_cancel()

    source_files = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        ref = s.get("file_ref")
        if isinstance(ref, dict) and isinstance(ref.get("path"), str):
            source_files.append(
                {"path": ref["path"], "scope": "machine_local"})
    result = _result("intake_analyze", outcome.result_data,
                     source_files=source_files)
    # Contract §5.3: lifecycle succeeded | partial — partial bat buoc
    # breakdown={succeeded,failed} (da co trong result_data khi co loi).
    if outcome.status == "partial":
        result["partial"] = True
    return result


# ---------- word export nhieu van ban (MIN-110, contract §8) ----------

def _word_case_id(payload):
    """case_id int >= 1 (mock oracle: bool/non-int/<1 → validation_error)."""
    p = payload if isinstance(payload, dict) else {}
    raw = _require(p.get("case_id"), "case_id")
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
        raise CommandError("validation_error", "case_id phai la int >= 1")
    return raw


def _word_case(sess, models, cid, *, writable):
    """Load case cho word export. Session PHAI mo trong suot batch —
    build_word_context lazy-load participants/property_links/nguoi_chet."""
    case = sess.get(models.InheritanceCase, cid)
    if case is None:
        raise CommandError("case_not_found", f"khong co ho so #{cid}",
                           details={"case_id": cid})
    # case_type_unsupported unreachable: engine DB hien chi co
    # InheritanceCase (contract §5.3) — guard tai day khi case_type
    # thanh column.
    if writable and case.is_locked:
        raise CommandError("workspace_locked", f"ho so #{cid} da khoa")
    return case


def _word_batch_command_error(err):
    """WordBatchError cua service → CommandError. word_batch_failed kem
    result.data (breakdown + per-file errors len wire — §8.4 example)."""
    retryable = err.code in ("word_batch_failed", "engine_unavailable")
    result = (_result("word_export_batch", err.result_data)
              if err.result_data is not None else None)
    return CommandError(
        err.code, err.message, retryable=retryable,
        next_action="retry" if retryable else None,
        details=err.details, result=result)


def word_export_options(job, payload):
    """notary.word_export_options — catalog + readiness theo case that.

    Read-only: duoc phep tren locked/unsupported (§5.3 chi workspace_get
    quyet dinh capability) — mock oracle khong _check_writable."""
    p = payload if isinstance(payload, dict) else {}
    extra = set(p) - {"case_id"}
    if extra:
        raise CommandError("validation_error",
                           f"payload key la: {sorted(extra)}")
    cid = _word_case_id(payload)
    wbe = _svc("word_batch_export")
    models = _models()
    sess = _db_session()
    try:
        case = _word_case(sess, models, cid, writable=False)
        data = wbe.export_options(
            case,
            resolve_template=lambda _key: _resolve_template(sess, None))
        job.check_cancel()
        return _result("word_export_options", data)
    finally:
        sess.close()


def word_export_batch(job, payload):
    """notary.word_export_batch — nhieu DOCX doc lap vao destination
    nguoi dung chon: khong ZIP, khong output mac dinh, KHONG BAO GIO
    ghi de (open "xb" + reservation noi batch).

    Nghiep vu (catalog, readiness word.*, render, collision naming,
    per-document saved|failed|skipped) nam trong
    services.word_batch_export; sidecar chi map case/FileRef va noi
    job.check_cancel(result)/report_progress/partial vao jobstore.
    """
    from fileref import existing_dir

    p = payload if isinstance(payload, dict) else {}
    extra = set(p) - {"case_id", "document_keys", "destination"}
    if extra:
        raise CommandError("validation_error",
                           f"payload key la: {sorted(extra)}")
    cid = _word_case_id(payload)
    wbe = _svc("word_batch_export")
    models = _models()
    sess = _db_session()
    try:
        case = _word_case(sess, models, cid, writable=True)
        try:
            keys = wbe.validate_document_keys(p.get("document_keys"))
            dest_dir = existing_dir(p.get("destination"))
            data = wbe.export_batch(
                case, case_id=cid, document_keys=keys, dest_dir=dest_dir,
                resolve_template=lambda _key: _resolve_template(sess, None),
                # Cancel giua batch: pending docs -> skipped trong result
                # di len wire (contract §8.4 canceled example, MIN-115).
                check_cancel=lambda d: job.check_cancel(
                    _result("word_export_batch", d)),
                report_progress=job.report_progress)
        except wbe.WordBatchError as exc:
            raise _word_batch_command_error(exc) from exc
        # Checkpoint cuoi: cancel o day van mang full result len wire.
        job.check_cancel(_result("word_export_batch", data))
        result = _result("word_export_batch", data)
        if data["breakdown"]["failed"]:
            result["partial"] = True   # marker jobstore -> status 'partial'
        return result
    finally:
        sess.close()
