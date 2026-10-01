"""Validator cho contracts/notary-case-drafting/examples — stdlib-only.

Chạy:  python contracts/notary-case-drafting/validate_examples.py
Quy tắc: mọi *.valid.json phải pass hết rule; mọi *.invalid.json phải vi phạm
ít nhất một rule VÀ khai báo expected_error khớp error code trong contract
(`contracts/notary-case-drafting.md` §9).

Fixture được phép mang top-level `fixture_context` (không nằm trên wire) mô tả
trạng thái server giả định để validator kiểm rule ngữ cảnh:
    {"server_revision": <int>, "stage_row_ids": [<row_id>, ...]}
"""
import json
import ntpath
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EX = HERE / "examples"

ENVELOPE_VERSION = "desktopcommand.v1"
SCHEMA_VERSION = "notary.case-drafting.v1"
DRAFT_SCHEMA_VERSION = "notary.case-drafting.v2"   # §13 DRAFT (MIN-125)
DRAFT_CASE_TYPES = {"inheritance", "two_party"}
DRAFT_TWO_PARTY_DOC_TYPES = {
    "chuyen_nhuong", "tang_cho", "cho_thue", "dat_coc",
}
DRAFT_MAX_ASSETS = 3
DRAFT_MAX_PEOPLE_TWO_PARTY = 30
DRAFT_POSITIONS = {1, 2, 3}
DRAFT_TWO_PARTY_IDS = [f"p{i}" for i in range(1, 31)]
DRAFT_NODE_FIELDS = {
    "id", "personId", "parentSlotIds", "spouseSlotId",
    "ownPositions", "receivePositions", "hidden", "deleted",
}
DRAFT_NODE_FIELDS_TWO_PARTY = {"id", "personId", "hidden", "deleted"}
# asset_row_v2 = asset_row trừ is_primary (§13.3)
DRAFT_ASSET_FIELDS = {
    "row_id", "entity_id", "so_serial", "so_vao_so", "so_thua_dat",
    "so_to_ban_do", "dia_chi", "loai_so", "hinh_thuc_su_dung",
    "thoi_han", "nguon_goc", "ngay_cap", "co_quan_cap", "land_rows",
}
DRAFT_STAGE_FIELDS = {"owner_row_id", "people", "assets"}
DRAFT_DATA_CODES = {
    "stage.legacy_asset_overflow", "stage.legacy_primary_ambiguous",
    "stage.legacy_land_rows_invalid", "stage.legacy_land_rows_overflow",
    "stage.orphan_thoi_han",
    "diagram.two_party_unsupported", "diagram.selection_pruned",
}

COMMANDS = {
    "notary.workspace_create": "workspace_create",
    "notary.workspace_get": "workspace_get",
    "notary.intake_analyze": "intake_analyze",
    "notary.workspace_commit_stage": "workspace_commit_stage",
    "notary.diagram_evaluate": "diagram_evaluate",
    "notary.diagram_save": "diagram_save",
    "notary.word_export_options": "word_export_options",
    "notary.word_export_batch": "word_export_batch",
}
KINDS = set(COMMANDS.values())

# §2.1a — case_id: bắt buộc / nháp được (absent ok, null lỗi) / cấm
CASE_ID_REQUIRED = {
    "notary.workspace_get", "notary.workspace_commit_stage",
    "notary.diagram_save", "notary.word_export_options",
    "notary.word_export_batch",
}
CASE_ID_DRAFTABLE = {"notary.intake_analyze", "notary.diagram_evaluate"}
CASE_ID_FORBIDDEN = {"notary.workspace_create"}
CASE_FIELDS = {
    "id", "case_type", "document_type", "status", "locked", "revision",
    "ngay_lap_ho_so", "noi_niem_yet", "ghi_chu",
    # đợt 3 (MIN-141): emit luôn có; legacy key trên wire
    "nguoi_nhan_uy_quyen", "nguoi_nhan_uy_quyen_id", "noi_dung_viec",
}
CASE_META_FIELDS = {
    "document_type", "ngay_lap_ho_so", "noi_niem_yet", "ghi_chu",
    # đợt 3: meta mới trong payload.case create/commit
    "nguoi_nhan_uy_quyen", "nguoi_nhan_uy_quyen_id", "noi_dung_viec",
}
# đợt 3: commit payload.case — meta + cặp immutable gửi kèm kiểm tra
COMMIT_CASE_FIELDS = CASE_META_FIELDS | {"case_type"}
# canonical key server chấp nhận ở payload (contract §4.1/§6)
CASE_META_CANON = {
    "casetype": "case_type", "documenttype": "document_type",
    "ngaylaphoso": "ngay_lap_ho_so", "noiniemyet": "noi_niem_yet",
    "nguoinhanuyquyen": "nguoi_nhan_uy_quyen",
    "nguoinhanuyquyenid": "nguoi_nhan_uy_quyen_id",
    "noidungviec": "noi_dung_viec", "ghichu": "ghi_chu",
}
PERSON_CANON = {
    "ten": "ho_ten", "gioitinh": "gioi_tinh", "ngaysinh": "ngay_sinh",
    "ngaychet": "ngay_chet", "sogiayto": "so_giay_to",
    "ngaycap": "ngay_cap", "noicap": "noi_cap", "diachi": "dia_chi",
    "loaigiayto": "loai_giay_to", "loaidiachi": "loai_dia_chi",
}
DOCUMENT_TYPES = {"khai_nhan", "thoa_thuan"}

STATUSES = {"accepted", "running", "waiting_user", "partial",
            "succeeded", "failed", "canceled"}
WAITING_ON = {"login", "review", "finalize", "confirm", None}
SOURCE_KINDS = {"image", "pdf", "docx", "xlsx", "text"}
GENDERS = {"Nam", "Nữ", None}
# registry mở — khi backend thêm document_key phải cập nhật set này
DOC_CATALOG = {"khai_nhan_di_san", "thoa_thuan_phan_chia", "niem_yet"}
BLOCK_REASONS = {
    "word.no_assets", "word.no_landowner", "word.no_deceased_landowner",
    "word.no_receiver", "word.too_many_assets", "word.too_many_people",
    "word.too_many_signers", "word.template_missing",
}
RENDER_STATUSES = {"invalid", "unsupported", "incomplete", "complete"}
DOC_STATUSES = {"saved", "failed", "skipped"}
OBSERVATION_STATES = {"observed", "normalized", "inferred"}

MAX_SOURCES = 8
MAX_FILE_BYTES = 20 * 1024 * 1024   # 20 MB
MAX_TEXT_CHARS = 100_000

UUID4_RX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}"
    r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
DATE_OR_YEAR_RX = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")
DATE_FULL_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SERIAL_RX = re.compile(r"^[A-Z]{2}\d{6,8}$")
DOC_KEY_RX = re.compile(r"^[a-z][a-z0-9_]*$")
FILENAME_RX = re.compile(r"^[A-Za-z0-9_-]+_HS-\d+(_\d+)?\.docx$")

SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|credential|cookie|auth|session|"
    r"storage_state|api_key|bearer", re.I)

# Field nullable — "" cấm thay null (g1-module-data §6 + contract §2.2/2.3)
NEVER_EMPTY = {
    "normalized_value", "raw_value", "ho_ten", "so_serial", "dia_chi",
    "display_name", "actual_filename", "path", "row_id", "personId",
    "source_id", "suggestion_id", "document_key", "id", "case_type",
    "filename_stem", "text",
    # person_row nullable strings (+ đợt 3 derived/evidence)
    "so_giay_to", "noi_cap", "place_of_origin",
    "loai_giay_to", "loai_dia_chi",
    # case meta nullable (rev 1.1 + đợt 3)
    "noi_niem_yet", "ghi_chu", "ngay_lap_ho_so",
    "nguoi_nhan_uy_quyen", "noi_dung_viec",
    # canonical spellings cùng cấm ""
    "ten", "gioitinh", "sogiayto", "ngaycap", "noicap", "diachi",
    "loaigiayto", "loaidiachi", "noiniemyet", "nguoinhanuyquyen",
    "noidungviec", "ghichu", "ngaylaphoso",
    # asset_row + land_rows nullable strings
    "so_vao_so", "so_thua_dat", "so_to_ban_do", "loai_so",
    "hinh_thuc_su_dung", "thoi_han", "nguon_goc", "co_quan_cap",
    "loai_dat",
}

PERSON_FIELDS = {
    "row_id", "entity_id", "ho_ten", "gioi_tinh", "ngay_sinh", "ngay_chet",
    "so_giay_to", "ngay_cap", "noi_cap", "dia_chi", "place_of_origin",
    # đợt 3: emit luôn có; payload chấp nhận cả canonical (PERSON_CANON)
    "loai_giay_to", "loai_dia_chi",
} | set(PERSON_CANON)
PERSON_DATE_FIELDS = {"ngay_sinh", "ngay_chet", "ngay_cap"}
ASSET_FIELDS = {
    "row_id", "entity_id", "is_primary", "so_serial", "so_vao_so",
    "so_thua_dat", "so_to_ban_do", "dia_chi", "loai_so",
    "hinh_thuc_su_dung", "thoi_han", "nguon_goc", "ngay_cap",
    "co_quan_cap", "land_rows",
}
NODE_FIELDS = {
    "id", "personId", "parentSlotIds", "spouseSlotId", "isLandOwner",
    "willReceive", "hidden", "deleted",
}
NODE_BOOL_FIELDS = {"isLandOwner", "willReceive", "hidden", "deleted"}

ERRORS = {
    # mã riêng của contract này
    "case_not_found", "case_type_unsupported", "workspace_locked",
    "workspace_conflict", "stage_validation_error",
    "intake_unsupported_source", "intake_source_too_large",
    "intake_too_many_sources", "intake_text_too_long",
    "diagram_reference_outside_stage", "diagram_invalid_state",
    "word_no_documents_selected", "word_duplicate_document_key",
    "word_unknown_document_key", "word_template_missing",
    "word_unresolved_placeholders", "word_batch_failed",
    "word_path_traversal", "workspace_owner_required",
    "validation_error",
    # §13.9 DRAFT v2 (MIN-125) — chỉ nhận khi fixture_context.draft_v2
    "diagram_domain_mismatch", "diagram_owner_mismatch",
    # reuse từ envelope / g1-module-data
    "file_scope_not_supported", "file_not_found", "file_locked",
    "payload_rejected_sensitive_key", "unsupported_contract_version",
    "engine_not_installed", "engine_restarted", "engine_unavailable",
    "engine_version_mismatch", "user_canceled", "job_already_terminal",
    "engine_shutdown",
}


def walk_keys(obj, path="", key=None):
    """Yield (path, key, value) cho MỌI node — kể cả dict bên trong list
    (key của phần tử list = "<parent_key>[i]")."""
    if key is not None:
        yield path, key, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_keys(v, path + "/" + str(k), str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]",
                                 (key or "") + f"[{i}]")


def is_abs_local(p):
    """Absolute drive path hoặc \\\\?\\ prefix; KHÔNG UNC \\\\server\\..."""
    if not isinstance(p, str) or not p:
        return False
    if p.startswith("\\\\?\\"):
        return True
    if p.startswith("\\\\"):
        return False                      # UNC
    return bool(re.match(r"^[A-Za-z]:[\\/]", p))


def _canon_conflicts(row, canon, where, v):
    """canonical + legacy cùng mang mà giá trị lệch → validation_error."""
    for ck, lk in canon.items():
        if ck in row and lk in row and row[ck] != row[lk]:
            v.append(("validation_error",
                      f"{where} {ck}!={lk} conflict"))


def check_person_row(row, where, v):
    if not isinstance(row, dict):
        v.append(("stage_validation_error", f"{where} not object"))
        return
    extra = set(row) - PERSON_FIELDS
    if extra:
        v.append(("validation_error", f"{where} extra keys {sorted(extra)}"))
    _canon_conflicts(row, PERSON_CANON, where, v)
    rid = row.get("row_id")
    if not (isinstance(rid, str) and UUID4_RX.match(rid)):
        v.append(("stage_validation_error", f"{where} row_id={rid!r}"))
    eid = row.get("entity_id")
    if eid is not None and not isinstance(eid, int):
        v.append(("stage_validation_error", f"{where} entity_id={eid!r}"))
    if not (isinstance(row.get("ho_ten"), str) and row["ho_ten"].strip()):
        v.append(("stage_validation_error", f"{where} ho_ten required"))
    if row.get("gioi_tinh") not in GENDERS:
        v.append(("stage_validation_error",
                  f"{where} gioi_tinh={row.get('gioi_tinh')!r}"))
    for f in PERSON_DATE_FIELDS:
        val = row.get(f)
        if val is not None and not (isinstance(val, str)
                                    and DATE_OR_YEAR_RX.match(val)):
            v.append(("stage_validation_error",
                      f"{where} {f}={val!r} bad date"))


def check_asset_row(row, where, v, draft_v2=False):
    if not isinstance(row, dict):
        v.append(("stage_validation_error", f"{where} not object"))
        return
    extra = set(row) - (DRAFT_ASSET_FIELDS if draft_v2 else ASSET_FIELDS)
    if extra:
        v.append(("validation_error", f"{where} extra keys {sorted(extra)}"))
    rid = row.get("row_id")
    if not (isinstance(rid, str) and UUID4_RX.match(rid)):
        v.append(("stage_validation_error", f"{where} row_id={rid!r}"))
    if not draft_v2 and not isinstance(row.get("is_primary"), bool):
        v.append(("validation_error", f"{where} is_primary not bool"))
    serial = row.get("so_serial")
    if not (isinstance(serial, str) and serial.strip()):
        v.append(("stage_validation_error", f"{where} so_serial required"))
    elif not SERIAL_RX.match(serial):
        v.append(("stage_validation_error",
                  f"{where} so_serial={serial!r} not canonical"))
    if not (isinstance(row.get("dia_chi"), str) and row["dia_chi"].strip()):
        v.append(("stage_validation_error", f"{where} dia_chi required"))
    nc = row.get("ngay_cap")
    if nc is not None and not (isinstance(nc, str) and DATE_FULL_RX.match(nc)):
        v.append(("stage_validation_error", f"{where} ngay_cap={nc!r}"))
    lr = row.get("land_rows")
    if lr is not None:
        if not isinstance(lr, list):
            v.append(("validation_error", f"{where} land_rows not list"))
        else:
            for i, r in enumerate(lr):
                if not isinstance(r, dict):
                    v.append(("validation_error",
                              f"{where} land_rows[{i}] not object"))


def check_stage(stage, where, v, draft_v2=False, case_type="inheritance",
                in_payload=False, allow_overflow=False):
    """people/assets rows + primary count + duplicate row_id.
    draft_v2 (§13): stage = {owner_row_id?, people, assets}; assets ≤3;
    two_party people ≤30; owner_row_id rules theo case_type/payload."""
    if not isinstance(stage, dict):
        v.append(("validation_error", f"{where} not object"))
        return
    if draft_v2:
        extra = set(stage) - DRAFT_STAGE_FIELDS
        if extra:
            v.append(("validation_error",
                      f"{where} extra keys {sorted(extra)}"))
        oid = stage.get("owner_row_id")
        if case_type == "two_party":
            if "owner_row_id" in stage:
                v.append(("validation_error",
                          f"{where}.owner_row_id forbidden for two_party"))
        elif in_payload:
            # commit/create/evaluate-nháp inheritance: phải trỏ row people
            people_ids = {
                r.get("row_id") for r in stage.get("people") or []
                if isinstance(r, dict)}
            if not (isinstance(oid, str) and UUID4_RX.match(oid)) \
                    or oid not in people_ids:
                v.append(("workspace_owner_required",
                          f"{where}.owner_row_id={oid!r}"))
        else:
            # result stage: luôn emit owner_row_id (uuid4 hoặc null legacy)
            if "owner_row_id" not in stage or (
                    oid is not None and not (
                        isinstance(oid, str) and UUID4_RX.match(oid))):
                v.append(("validation_error",
                          f"{where}.owner_row_id={oid!r}"))
    people = stage.get("people")
    assets = stage.get("assets")
    if not isinstance(people, list):
        v.append(("validation_error", f"{where}.people missing/not list"))
        people = []
    if not isinstance(assets, list):
        v.append(("validation_error", f"{where}.assets missing/not list"))
        assets = []
    seen = set()
    for i, r in enumerate(people):
        check_person_row(r, f"{where}.people[{i}]", v)
        rid = r.get("row_id") if isinstance(r, dict) else None
        if rid in seen:
            v.append(("stage_validation_error",
                      f"{where} duplicate row_id {rid!r}"))
        seen.add(rid)
    for i, r in enumerate(assets):
        check_asset_row(r, f"{where}.assets[{i}]", v, draft_v2=draft_v2)
        rid = r.get("row_id") if isinstance(r, dict) else None
        if rid in seen:
            v.append(("stage_validation_error",
                      f"{where} duplicate row_id {rid!r}"))
        seen.add(rid)
    if draft_v2:
        if len(assets) > DRAFT_MAX_ASSETS and not allow_overflow:
            v.append(("stage_validation_error",
                      f"{where} asset_limit assets={len(assets)} > "
                      f"{DRAFT_MAX_ASSETS}"))
        if case_type == "two_party" \
                and len(people) > DRAFT_MAX_PEOPLE_TWO_PARTY:
            v.append(("stage_validation_error",
                      f"{where} people_limit people={len(people)} > "
                      f"{DRAFT_MAX_PEOPLE_TWO_PARTY}"))
    elif assets:
        primaries = sum(1 for r in assets
                        if isinstance(r, dict) and r.get("is_primary") is True)
        if primaries != 1:
            v.append(("stage_validation_error",
                      f"{where} primary_count={primaries}"))


def check_positions(n, w, v):
    """§13.4 — ownPositions/receivePositions ⊆ {1,2,3}, unique, non-null."""
    for f in ("ownPositions", "receivePositions"):
        arr = n.get(f)
        if not isinstance(arr, list):
            v.append(("diagram_invalid_state", f"{w} {f}={arr!r} not list"))
            continue
        seen = set()
        for x in arr:
            if not isinstance(x, int) or isinstance(x, bool) \
                    or x not in DRAFT_POSITIONS:
                v.append(("diagram_invalid_state",
                          f"{w} {f} invalid_position {x!r}"))
            elif x in seen:
                v.append(("diagram_invalid_state",
                          f"{w} {f} duplicate position {x}"))
            seen.add(x)


def check_person_id(n, w, stage_ids, v):
    pid = n.get("personId")
    if pid is None:
        return
    if not (isinstance(pid, str) and UUID4_RX.match(pid)):
        v.append(("diagram_reference_outside_stage",
                  f"{w} personId={pid!r} not row_id"))
    elif stage_ids is not None and pid not in stage_ids:
        v.append(("diagram_reference_outside_stage",
                  f"{w} personId={pid!r} outside stage"))


def check_diagram_state_v2(state, where, stage_ids, v, case_type):
    """§13.4/13.5 — version:3 + domain bắt buộc; node shape theo domain."""
    if state.get("version") != 3:
        v.append(("diagram_invalid_state",
                  f"{where}.version={state.get('version')!r}"))
    dom = state.get("domain")
    if dom not in DRAFT_CASE_TYPES:
        v.append(("diagram_invalid_state", f"{where}.domain={dom!r}"))
        dom = None
    elif dom != case_type:
        v.append(("diagram_domain_mismatch",
                  f"{where}.domain={dom!r} != case_type={case_type!r}"))
    nodes = state.get("nodes")
    if not isinstance(nodes, list):
        v.append(("diagram_invalid_state", f"{where}.nodes not list"))
        return
    eff = dom or case_type
    ids = set()
    persons = set()          # duplicate_person — §13.5 giữ rule A3
    for i, n in enumerate(nodes):
        w = f"{where}.nodes[{i}]"
        if not isinstance(n, dict):
            v.append(("diagram_invalid_state", f"{w} not object"))
            continue
        if eff == "two_party":
            extra = set(n) - DRAFT_NODE_FIELDS_TWO_PARTY
            if extra:
                v.append(("diagram_invalid_state",
                          f"{w} invalid_node extra {sorted(extra)}"))
            nid = n.get("id")
            if nid not in DRAFT_TWO_PARTY_IDS:
                v.append(("diagram_invalid_state",
                          f"{w} invalid_position id={nid!r}"))
            elif nid in ids:
                v.append(("diagram_invalid_state",
                          f"{w} duplicate_node_id {nid!r}"))
            else:
                ids.add(nid)
        else:
            extra = set(n) - DRAFT_NODE_FIELDS
            if extra:
                v.append(("diagram_invalid_state",
                          f"{w} invalid_node extra {sorted(extra)}"))
            nid = n.get("id")
            if not (isinstance(nid, str) and nid.strip()):
                v.append(("diagram_invalid_state", f"{w} id={nid!r}"))
            elif nid in ids:
                v.append(("diagram_invalid_state",
                          f"{w} duplicate_node_id {nid!r}"))
            else:
                ids.add(nid)
            check_positions(n, w, v)
            ps = n.get("parentSlotIds")
            if not (isinstance(ps, list) and len(ps) <= 2
                    and all(isinstance(x, str) for x in ps)):
                v.append(("diagram_invalid_state",
                          f"{w} parentSlotIds={ps!r}"))
            ss = n.get("spouseSlotId")
            if ss is not None and not isinstance(ss, str):
                v.append(("diagram_invalid_state",
                          f"{w} spouseSlotId={ss!r}"))
            if isinstance(nid, str):
                if isinstance(ps, list) and nid in ps:
                    v.append(("diagram_invalid_state",
                              f"{w} self_parent"))
                if ss == nid:
                    v.append(("diagram_invalid_state",
                              f"{w} self_spouse"))
        check_person_id(n, w, stage_ids, v)
        pid = n.get("personId")
        if pid is not None and n.get("deleted") is not True:
            if pid in persons:
                v.append(("diagram_invalid_state",
                          f"{w} duplicate_person {pid!r}"))
            persons.add(pid)
        for f in ("hidden", "deleted"):
            if not isinstance(n.get(f), bool):
                v.append(("diagram_invalid_state",
                          f"{w} {f}={n.get(f)!r} not strict bool"))
    if eff == "two_party" and ids != set(DRAFT_TWO_PARTY_IDS):
        missing = sorted(set(DRAFT_TWO_PARTY_IDS) - ids,
                         key=lambda s: int(s[1:]))
        v.append(("diagram_invalid_state",
                  f"{where} missing_position {missing}"))
    if eff != "two_party":
        for i, n in enumerate(nodes):
            if not isinstance(n, dict):
                continue
            w = f"{where}.nodes[{i}]"
            for p in n.get("parentSlotIds") or []:
                if isinstance(p, str) and p not in ids:
                    v.append(("diagram_invalid_state",
                              f"{w} dangling_parent {p!r}"))
            ss = n.get("spouseSlotId")
            if isinstance(ss, str) and ss not in ids:
                v.append(("diagram_invalid_state",
                          f"{w} dangling_spouse {ss!r}"))


def check_diagram_state(state, where, stage_ids, v, draft_v2=False,
                        case_type="inheritance"):
    if not isinstance(state, dict):
        v.append(("diagram_invalid_state", f"{where} not object"))
        return
    if draft_v2:
        check_diagram_state_v2(state, where, stage_ids, v, case_type)
        return
    if state.get("version") != 2:
        v.append(("diagram_invalid_state",
                  f"{where}.version={state.get('version')!r}"))
    nodes = state.get("nodes")
    if not isinstance(nodes, list):
        v.append(("diagram_invalid_state", f"{where}.nodes not list"))
        return
    ids = set()
    for i, n in enumerate(nodes):
        w = f"{where}.nodes[{i}]"
        if not isinstance(n, dict):
            v.append(("diagram_invalid_state", f"{w} not object"))
            continue
        extra = set(n) - NODE_FIELDS
        if extra:
            v.append(("validation_error", f"{w} extra keys {sorted(extra)}"))
        nid = n.get("id")
        if not (isinstance(nid, str) and nid.strip()):
            v.append(("diagram_invalid_state", f"{w} id={nid!r}"))
        elif nid in ids:
            v.append(("diagram_invalid_state",
                      f"{w} duplicate_node_id {nid!r}"))
        else:
            ids.add(nid)
        pid = n.get("personId")
        if pid is not None:
            if not (isinstance(pid, str) and UUID4_RX.match(pid)):
                v.append(("diagram_reference_outside_stage",
                          f"{w} personId={pid!r} not row_id"))
            elif stage_ids is not None and pid not in stage_ids:
                v.append(("diagram_reference_outside_stage",
                          f"{w} personId={pid!r} outside stage"))
        ps = n.get("parentSlotIds")
        if not (isinstance(ps, list) and len(ps) <= 2
                and all(isinstance(x, str) for x in ps)):
            v.append(("diagram_invalid_state",
                      f"{w} parentSlotIds={ps!r}"))
        ss = n.get("spouseSlotId")
        if ss is not None and not isinstance(ss, str):
            v.append(("diagram_invalid_state",
                      f"{w} spouseSlotId={ss!r}"))
        for f in NODE_BOOL_FIELDS:
            if not isinstance(n.get(f), bool):
                v.append(("diagram_invalid_state",
                          f"{w} {f}={n.get(f)!r} not strict bool"))
        if isinstance(nid, str):
            if isinstance(ps, list) and nid in ps:
                v.append(("diagram_invalid_state", f"{w} self_parent"))
            if ss == nid:
                v.append(("diagram_invalid_state", f"{w} self_spouse"))
    # dangling refs
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            continue
        w = f"{where}.nodes[{i}]"
        for p in n.get("parentSlotIds") or []:
            if isinstance(p, str) and p not in ids:
                v.append(("diagram_invalid_state",
                          f"{w} dangling_parent {p!r}"))
        ss = n.get("spouseSlotId")
        if isinstance(ss, str) and ss not in ids:
            v.append(("diagram_invalid_state",
                      f"{w} dangling_spouse {ss!r}"))


def check_render_model(rm, where, v):
    if not isinstance(rm, dict):
        v.append(("validation_error", f"{where} not object"))
        return
    if rm.get("engineVersion") != 2:
        v.append(("validation_error",
                  f"{where}.engineVersion={rm.get('engineVersion')!r}"))
    if rm.get("status") not in RENDER_STATUSES:
        v.append(("validation_error",
                  f"{where}.status={rm.get('status')!r}"))
    allo = rm.get("allocations")
    if not isinstance(allo, dict):
        v.append(("validation_error", f"{where}.allocations not object"))
    else:
        need = {"baseShare", "inheritedShare", "distributedShare",
                "finalShare", "displayPercent"}
        for pid, a in allo.items():
            if not isinstance(a, dict) or not need <= set(a):
                v.append(("validation_error",
                          f"{where}.allocations[{pid!r}] missing keys"))
    cons = rm.get("conservation")
    if not (isinstance(cons, dict)
            and {"allocated", "unresolved", "total"} <= set(cons)):
        v.append(("validation_error", f"{where}.conservation missing keys"))
    for i, r in enumerate(rm.get("requiredSlots") or []):
        if isinstance(r, dict) and r.get("reason") not in (
                "active_estate", "representation_branch"):
            v.append(("validation_error",
                      f"{where}.requiredSlots[{i}].reason="
                      f"{r.get('reason')!r}"))
    for i, u in enumerate(rm.get("unresolvedEstates") or []):
        if isinstance(u, dict) and u.get("reason") != "no_valid_heir":
            v.append(("validation_error",
                      f"{where}.unresolvedEstates[{i}].reason="
                      f"{u.get('reason')!r}"))


def check_intake_payload(payload, v):
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        v.append(("validation_error", "payload.sources missing/empty"))
        return
    if len(sources) > MAX_SOURCES:
        v.append(("intake_too_many_sources",
                  f"sources={len(sources)} > {MAX_SOURCES}"))
    seen = set()
    for i, s in enumerate(sources):
        w = f"payload.sources[{i}]"
        if not isinstance(s, dict):
            v.append(("validation_error", f"{w} not object"))
            continue
        sid = s.get("source_id")
        if not (isinstance(sid, str) and UUID4_RX.match(sid)):
            v.append(("validation_error", f"{w} source_id={sid!r}"))
        elif sid in seen:
            v.append(("validation_error", f"{w} duplicate source_id"))
        seen.add(sid)
        kind = s.get("kind")
        if kind not in SOURCE_KINDS:
            v.append(("intake_unsupported_source",
                      f"{w} kind={kind!r}"))
            continue
        if kind == "text":
            if "file_ref" in s:
                v.append(("validation_error",
                          f"{w} file_ref forbidden for text"))
            t = s.get("text")
            if not isinstance(t, str):
                v.append(("validation_error", f"{w} text required"))
            elif len(t) > MAX_TEXT_CHARS:
                v.append(("intake_text_too_long",
                          f"{w} text {len(t)} > {MAX_TEXT_CHARS}"))
        else:
            if "text" in s:
                v.append(("validation_error",
                          f"{w} text forbidden for kind={kind}"))
            fr = s.get("file_ref")
            if not isinstance(fr, dict):
                v.append(("validation_error", f"{w} file_ref required"))
            else:
                if fr.get("is_dir") is True:
                    v.append(("validation_error",
                              f"{w} file_ref is_dir=true"))
                sb = fr.get("size_bytes")
                if not isinstance(sb, int):
                    v.append(("validation_error",
                              f"{w} file_ref.size_bytes required"))
                elif sb > MAX_FILE_BYTES:
                    v.append(("intake_source_too_large",
                              f"{w} size_bytes={sb} > {MAX_FILE_BYTES}"))


def check_word_batch_payload(payload, v):
    keys = payload.get("document_keys")
    if not isinstance(keys, list):
        v.append(("validation_error", "document_keys missing/not list"))
    elif not keys:
        v.append(("word_no_documents_selected", "document_keys empty"))
    else:
        if len(keys) != len(set(keys)):
            v.append(("word_duplicate_document_key",
                      "duplicate document_key"))
        for k in keys:
            if not (isinstance(k, str) and DOC_KEY_RX.match(k)) \
                    or k not in DOC_CATALOG:
                v.append(("word_unknown_document_key", f"key={k!r}"))
    dest = payload.get("destination")
    if not isinstance(dest, dict):
        v.append(("validation_error", "destination missing/not object"))
    elif dest.get("is_dir") is not True:
        v.append(("validation_error",
                  "destination is_dir must be true"))


def check_case_object(case, where, v, draft_v2=False):
    """case object trong result (workspace_get/commit/create) — §4."""
    if not isinstance(case, dict):
        v.append(("validation_error", f"{where} missing/not object"))
        return
    extra = set(case) - CASE_FIELDS
    if extra:
        v.append(("validation_error", f"{where} extra keys {sorted(extra)}"))
    for rk in CASE_FIELDS:
        if rk not in case:
            v.append(("validation_error", f"{where} missing {rk}"))
    ct = case.get("case_type")
    if draft_v2:
        if ct not in DRAFT_CASE_TYPES:
            v.append(("validation_error",
                      f"{where} case_type={ct!r} not in {DRAFT_CASE_TYPES}"))
        d = case.get("document_type")
        if ct == "two_party":
            if d not in DRAFT_TWO_PARTY_DOC_TYPES:
                v.append(("validation_error",
                          f"{where} document_type={d!r} not two_party"))
        elif d is not None and d not in DOCUMENT_TYPES:
            v.append(("validation_error",
                      f"{where} document_type={d!r}"))
    else:
        d = case.get("document_type")
        if d is not None and d not in DOCUMENT_TYPES:
            v.append(("validation_error", f"{where} document_type={d!r}"))
    nl = case.get("ngay_lap_ho_so")
    if nl is not None and not (isinstance(nl, str)
                               and DATE_FULL_RX.match(nl)):
        v.append(("validation_error", f"{where} ngay_lap_ho_so={nl!r}"))


def check_create_payload(payload, v, draft_v2=False):
    """notary.workspace_create — §4.3 (v1) / §13.6 (v2 draft)."""
    ik = payload.get("idempotency_key")
    if not (isinstance(ik, str) and UUID4_RX.match(ik)):
        v.append(("validation_error", f"idempotency_key={ik!r}"))
    cm = payload.get("case")
    case_type = "inheritance"
    meta_fields = CASE_META_FIELDS | ({"case_type"} if draft_v2 else set()) \
        | set(CASE_META_CANON)
    if not isinstance(cm, dict):
        v.append(("validation_error", "payload.case missing/not object"))
    else:
        extra = set(cm) - meta_fields
        if extra:
            v.append(("validation_error",
                      f"payload.case extra keys {sorted(extra)}"))
        _canon_conflicts(cm, CASE_META_CANON, "payload.case", v)
        if draft_v2:
            ct = cm.get("case_type", cm.get("casetype", "inheritance"))
            if ct not in DRAFT_CASE_TYPES:
                v.append(("validation_error",
                          f"payload.case.case_type={ct!r}"))
            else:
                case_type = ct
            d = cm.get("document_type", cm.get("documenttype"))
            ok = d in DRAFT_TWO_PARTY_DOC_TYPES if ct == "two_party" \
                else d in DOCUMENT_TYPES
            if not ok:
                v.append(("validation_error",
                          f"payload.case.document_type={d!r}"))
        elif cm.get("document_type", cm.get("documenttype")) \
                not in DOCUMENT_TYPES:
            v.append(("validation_error",
                      f"payload.case.document_type="
                      f"{cm.get('document_type', cm.get('documenttype'))!r}"))
        nl = cm.get("ngay_lap_ho_so", cm.get("ngaylaphoso"))
        if nl is not None and not (isinstance(nl, str)
                                   and DATE_FULL_RX.match(nl)):
            v.append(("validation_error",
                      f"payload.case.ngay_lap_ho_so={nl!r}"))
    st = payload.get("stage")
    check_stage(st, "payload.stage", v, draft_v2=draft_v2,
                case_type=case_type, in_payload=True)
    people = st.get("people") if isinstance(st, dict) else None
    assets = st.get("assets") if isinstance(st, dict) else None
    row_ids = set()
    if isinstance(people, list):
        if not people:
            v.append(("stage_validation_error", "payload.stage.people empty"))
        for r in people:
            if isinstance(r, dict):
                if r.get("entity_id") is not None:
                    v.append(("stage_validation_error",
                              f"person row {r.get('row_id')!r} "
                              "entity_id must be null"))
                if isinstance(r.get("row_id"), str):
                    row_ids.add(r["row_id"])
    if isinstance(assets, list):
        if not assets:
            v.append(("stage_validation_error", "payload.stage.assets empty"))
        for r in assets:
            if isinstance(r, dict) and r.get("entity_id") is not None:
                v.append(("stage_validation_error",
                          f"asset row {r.get('row_id')!r} "
                          "entity_id must be null"))
    dg = payload.get("diagram")
    state = dg.get("state") if isinstance(dg, dict) else None
    if draft_v2:
        # §13.6: diagram optional; owner chỉ định bằng stage.owner_row_id;
        # node owner (nếu có personId) phải khớp owner_row_id.
        if isinstance(state, dict) and case_type == "inheritance" \
                and isinstance(state.get("nodes"), list):
            oid = st.get("owner_row_id") if isinstance(st, dict) else None
            for n in state["nodes"]:
                if isinstance(n, dict) and n.get("id") == "owner" \
                        and n.get("deleted") is not True:
                    npid = n.get("personId")
                    if npid is not None and npid != oid:
                        v.append(("diagram_owner_mismatch",
                                  f"owner node personId={npid!r} "
                                  f"!= owner_row_id={oid!r}"))
        return
    # v1: đúng một node id=owner không deleted, personId ∈ stage people
    if isinstance(state, dict) and isinstance(state.get("nodes"), list):
        owners = [n for n in state["nodes"]
                  if isinstance(n, dict) and n.get("id") == "owner"
                  and n.get("deleted") is not True]
        if len(owners) != 1 or owners[0].get("personId") not in row_ids:
            v.append(("workspace_owner_required",
                      "node 'owner' must reference one stage person"))


def check_base_revision(payload, ctx, v):
    br = payload.get("base_revision")
    if not (isinstance(br, int) and br >= 1):
        v.append(("validation_error", f"base_revision={br!r}"))
        return
    srv = ctx.get("server_revision")
    if isinstance(srv, int) and br != srv:
        v.append(("workspace_conflict",
                  f"base_revision={br} != server_revision={srv}"))


def norm(p):
    return ntpath.normcase(ntpath.normpath(p))


def check_word_batch_result(data, v):
    dest = data.get("destination")
    dest_norm = None
    if not isinstance(dest, dict):
        v.append(("validation_error", "data.destination missing"))
    else:
        if dest.get("is_dir") is not True:
            v.append(("validation_error",
                      "data.destination is_dir must be true"))
        if isinstance(dest.get("path"), str):
            dest_norm = norm(dest["path"])
    docs = data.get("documents")
    seen_by_status = {"saved": [], "failed": [], "skipped": []}
    if not isinstance(docs, list):
        v.append(("validation_error", "data.documents missing"))
    else:
        for i, d in enumerate(docs):
            w = f"data.documents[{i}]"
            if not isinstance(d, dict):
                v.append(("validation_error", f"{w} not object"))
                continue
            for rk in ("document_key", "display_name", "status",
                       "actual_filename", "output_file", "error"):
                if rk not in d:
                    v.append(("validation_error",
                              f"{w} missing {rk}"))
            if not (isinstance(d.get("display_name"), str)
                    and d["display_name"].strip()):
                v.append(("validation_error",
                          f"{w} display_name required"))
            if d.get("status") not in DOC_STATUSES:
                v.append(("validation_error",
                          f"{w} status={d.get('status')!r}"))
            else:
                seen_by_status[d["status"]].append(d.get("document_key"))
            fn = d.get("actual_filename")
            if fn is not None:
                if (not isinstance(fn, str) or ".." in fn
                        or "/" in fn or "\\" in fn or ":" in fn):
                    v.append(("word_path_traversal",
                              f"{w} actual_filename={fn!r}"))
                elif not FILENAME_RX.match(fn):
                    v.append(("validation_error",
                              f"{w} actual_filename={fn!r} bad pattern"))
            of = d.get("output_file")
            if of is not None:
                if not isinstance(of, dict):
                    v.append(("validation_error", f"{w} output_file"))
                else:
                    if of.get("is_dir") is True:
                        v.append(("validation_error",
                                  f"{w} output_file is_dir=true"))
                    op = of.get("path")
                    if dest_norm and isinstance(op, str) \
                            and is_abs_local(op):
                        op_n = norm(op)
                        if not op_n.startswith(dest_norm + "\\"):
                            v.append(("word_path_traversal",
                                      f"{w} output_file outside dest"))
            st = d.get("status")
            if st == "saved" and (fn is None or of is None):
                v.append(("validation_error",
                          f"{w} saved without filename/output_file"))
            if st == "failed" and not isinstance(d.get("error"), dict):
                v.append(("validation_error",
                          f"{w} failed without error"))
            if st == "skipped" and (
                    fn is not None or of is not None
                    or d.get("error") is not None):
                v.append(("validation_error",
                          f"{w} skipped must have nulls"))
    bd = data.get("breakdown")
    if not (isinstance(bd, dict) and isinstance(bd.get("succeeded"), list)
            and isinstance(bd.get("failed"), list)
            and isinstance(bd.get("skipped"), list)):
        v.append(("validation_error",
                  "data.breakdown missing (need succeeded+failed+skipped)"))
    elif isinstance(docs, list):
        if set(bd["succeeded"]) != set(seen_by_status["saved"]) \
                or set(bd["failed"]) != set(seen_by_status["failed"]) \
                or set(bd["skipped"]) != set(seen_by_status["skipped"]):
            v.append(("validation_error",
                      "breakdown sets != documents statuses"))


def check_suggestion(s, where, v):
    if not isinstance(s, dict):
        v.append(("validation_error", f"{where} not object"))
        return
    for f in ("suggestion_id", "source_id"):
        val = s.get(f)
        if not (isinstance(val, str) and UUID4_RX.match(val)):
            v.append(("validation_error", f"{where} {f}={val!r}"))
    if s.get("target") not in ("person", "asset"):
        v.append(("validation_error",
                  f"{where} target={s.get('target')!r}"))
    if not isinstance(s.get("warnings"), list):
        v.append(("validation_error", f"{where}.warnings missing"))
    fields = s.get("fields")
    if not isinstance(fields, dict):
        v.append(("validation_error", f"{where}.fields not object"))
    else:
        for name, fv in fields.items():
            w = f"{where}.fields.{name}"
            if not isinstance(fv, dict):
                v.append(("validation_error", f"{w} not object"))
                continue
            if fv.get("observation_state") not in OBSERVATION_STATES:
                v.append(("validation_error",
                          f"{w} observation_state="
                          f"{fv.get('observation_state')!r}"))
            c = fv.get("confidence")
            if c is not None and not (isinstance(c, (int, float))
                                      and not isinstance(c, bool)
                                      and 0 <= c <= 1):
                v.append(("validation_error",
                          f"{w} confidence={c!r}"))


def _data_case_type(data, ctx=None):
    c = data.get("case") if isinstance(data, dict) else None
    ct = c.get("case_type") if isinstance(c, dict) else None
    if isinstance(ct, str):
        return ct
    ct = (ctx or {}).get("case_type")
    return ct if isinstance(ct, str) else "inheritance"


def _has_data_warning(data, code):
    ws = data.get("warnings") if isinstance(data, dict) else None
    return isinstance(ws, list) and any(
        isinstance(w, dict) and w.get("code") == code for w in ws)


def check_result_data(kind, data, stage_ids, v, draft_v2=False, ctx=None):
    if not isinstance(data, dict):
        v.append(("validation_error", "result.data not object"))
        return
    want_sv = DRAFT_SCHEMA_VERSION if draft_v2 else SCHEMA_VERSION
    if data.get("schema_version") != want_sv:
        v.append(("validation_error",
                  f"schema_version={data.get('schema_version')!r}"))
    ct = _data_case_type(data, ctx) if draft_v2 else "inheritance"
    if kind == "workspace_get" or kind == "workspace_create":
        if kind == "workspace_create" \
                and not isinstance(data.get("created"), bool):
            v.append(("validation_error",
                      f"data.created={data.get('created')!r}"))
        check_case_object(data.get("case"), "data.case", v,
                          draft_v2=draft_v2)
        caps = data.get("capabilities")
        if not (isinstance(caps, dict)
                and {"intake", "diagram", "word_export"} <= set(caps)):
            v.append(("validation_error",
                      "data.capabilities missing keys"))
        elif draft_v2 and ct == "two_party" \
                and caps.get("word_export") is not False:
            v.append(("validation_error",
                      "data.capabilities.word_export must be false "
                      "for two_party"))
        allow_overflow = draft_v2 \
            and _has_data_warning(data, "stage.legacy_asset_overflow")
        check_stage(data.get("stage"), "data.stage", v, draft_v2=draft_v2,
                    case_type=ct, allow_overflow=allow_overflow)
        dg = data.get("diagram")
        if isinstance(dg, dict):
            if draft_v2:
                st_dom = (dg.get("state") or {}).get("domain") \
                    if isinstance(dg.get("state"), dict) else None
                if dg.get("domain") is not None \
                        and st_dom is not None \
                        and dg["domain"] != st_dom:
                    v.append(("validation_error",
                              "data.diagram.domain != state.domain"))
            check_diagram_state(dg.get("state"), "data.diagram.state",
                                stage_ids, v, draft_v2=draft_v2,
                                case_type=ct)
            rm = dg.get("render_model")
            if rm is not None:
                check_render_model(rm, "data.diagram.render_model", v)
        else:
            v.append(("validation_error", "data.diagram missing"))
    elif kind == "intake_analyze":
        for i, s in enumerate(data.get("suggestions") or []):
            check_suggestion(s, f"data.suggestions[{i}]", v)
        if not isinstance(data.get("suggestions"), list):
            v.append(("validation_error", "data.suggestions missing"))
        if not isinstance(data.get("errors"), list):
            v.append(("validation_error", "data.errors missing"))
    elif kind == "workspace_commit_stage":
        if not (isinstance(data.get("revision"), int)
                and data["revision"] >= 1):
            v.append(("validation_error",
                      f"revision={data.get('revision')!r}"))
        check_stage(data.get("stage"), "data.stage", v, draft_v2=draft_v2,
                    case_type=ct)
        dg = data.get("diagram")
        if isinstance(dg, dict):
            check_diagram_state(dg.get("state"), "data.diagram.state",
                                stage_ids, v, draft_v2=draft_v2,
                                case_type=ct)
            # I-8: commit result luôn kèm render_model non-null
            if dg.get("render_model") is None:
                v.append(("validation_error",
                          "data.diagram.render_model required after commit"))
            else:
                check_render_model(dg["render_model"],
                                   "data.diagram.render_model", v)
        else:
            v.append(("validation_error", "data.diagram missing"))
    elif kind == "diagram_evaluate":
        er = data.get("evaluated_revision")
        # rev 1.1: null = chế độ nháp; khi present phải int ≥ 1
        if er is not None and not (isinstance(er, int) and er >= 1):
            v.append(("validation_error",
                      f"evaluated_revision={er!r}"))
        check_render_model(data.get("render_model"),
                           "data.render_model", v)
    elif kind == "diagram_save":
        if not (isinstance(data.get("revision"), int)
                and data["revision"] >= 1):
            v.append(("validation_error",
                      f"revision={data.get('revision')!r}"))
        dg = data.get("diagram")
        if isinstance(dg, dict):
            check_diagram_state(dg.get("state"), "data.diagram.state",
                                stage_ids, v, draft_v2=draft_v2,
                                case_type=ct)
            # M-12: save thành công luôn kèm render_model non-null
            if dg.get("render_model") is None:
                v.append(("validation_error",
                          "data.diagram.render_model required after save"))
            else:
                check_render_model(dg["render_model"],
                                   "data.diagram.render_model", v)
        else:
            v.append(("validation_error", "data.diagram missing"))
    elif kind == "word_export_options":
        docs = data.get("documents")
        if not isinstance(docs, list):
            v.append(("validation_error", "data.documents missing"))
        else:
            for i, d in enumerate(docs):
                w = f"data.documents[{i}]"
                if not isinstance(d, dict):
                    v.append(("validation_error", f"{w} not object"))
                    continue
                for rk in ("document_key", "display_name", "ready",
                           "block_reason"):
                    if rk not in d:
                        v.append(("validation_error",
                                  f"{w} missing {rk}"))
                k = d.get("document_key")
                if not (isinstance(k, str) and DOC_KEY_RX.match(k)):
                    v.append(("validation_error",
                              f"{w} document_key={k!r}"))
                if not (isinstance(d.get("display_name"), str)
                        and d["display_name"].strip()):
                    v.append(("validation_error",
                              f"{w} display_name required"))
                if not isinstance(d.get("ready"), bool):
                    v.append(("validation_error", f"{w} ready not bool"))
                br = d.get("block_reason")
                if br is not None and br not in BLOCK_REASONS:
                    v.append(("validation_error",
                              f"{w} block_reason={br!r}"))
                if d.get("ready") is False and br is None:
                    v.append(("validation_error",
                              f"{w} ready=false without block_reason"))
                if d.get("ready") is True and br is not None:
                    v.append(("validation_error",
                              f"{w} ready=true with block_reason"))
    elif kind == "word_export_batch":
        check_word_batch_result(data, v)


def _payload_case_type(payload, ctx):
    """case_type hiệu lực cho payload/result: payload.case.case_type >
    fixture_context.case_type > inheritance (§13.5/13.6 draft)."""
    c = payload.get("case") if isinstance(payload, dict) else None
    ct = c.get("case_type") if isinstance(c, dict) else None
    if isinstance(ct, str):
        return ct
    ct = ctx.get("case_type")
    return ct if isinstance(ct, str) else "inheritance"


def violations(doc):
    """Return list of (error_code, detail) the contract rules."""
    v = []
    ctx = doc.get("fixture_context") or {}
    draft_v2 = ctx.get("draft_v2") is True   # §13 — flag ngoài wire

    # --- envelope version
    if doc.get("contract_version") != ENVELOPE_VERSION:
        v.append(("unsupported_contract_version",
                  f"contract_version={doc.get('contract_version')!r}"))

    # --- sensitive keys đệ quy trong payload (envelope §3)
    for path, k, val in walk_keys(doc.get("payload", {})):
        if SENSITIVE_KEY.search(str(k)):
            v.append(("payload_rejected_sensitive_key", f"key {path}"))

    # --- `confirmed` cấm ở mọi cấp (contract §2.3)
    # --- "" cấm thay null ở field nullable
    for path, k, val in walk_keys(doc):
        if str(k).lower() == "confirmed":
            v.append(("validation_error", f"forbidden key {path}"))
        if k in NEVER_EMPTY and val == "":
            v.append(("validation_error", f"{path} empty-string-as-null"))

    # --- file_ref rules (mọi nơi xuất hiện)
    for path, k, val in walk_keys(doc):
        if not (isinstance(val, dict) and "path" in val and "scope" in val):
            continue
        w = path
        if val.get("scope") != "machine_local":
            v.append(("file_scope_not_supported",
                      f"{w} scope={val.get('scope')!r}"))
        if not is_abs_local(val.get("path")):
            v.append(("file_scope_not_supported",
                      f"{w} path={val.get('path')!r}"))
        if "is_dir" in val and not isinstance(val["is_dir"], bool):
            v.append(("validation_error", f"{w} is_dir not bool"))
        if k != "destination" and val.get("is_dir") is True:
            v.append(("validation_error",
                      f"{w} is_dir=true on non-destination ref"))

    # --- command_id uuid (request + job echo)
    cid = doc.get("command_id")
    if cid is not None and not (isinstance(cid, str) and UUID4_RX.match(cid)):
        v.append(("validation_error", f"command_id={cid!r}"))

    # --- stage ids cho cross-check diagram
    stage_ids = set()
    res = doc.get("result") or {}
    data = res.get("data") if isinstance(res, dict) else {}
    payload = doc.get("payload") or {}
    for container in (data, payload):
        st = container.get("stage") if isinstance(container, dict) else None
        if isinstance(st, dict):
            for r in st.get("people") or []:
                if isinstance(r, dict) and isinstance(r.get("row_id"), str):
                    stage_ids.add(r["row_id"])
    for rid in ctx.get("stage_row_ids") or []:
        if isinstance(rid, str):
            stage_ids.add(rid)
    stage_ids = stage_ids or None

    # --- request payload rules
    ct = _payload_case_type(payload, ctx)
    cmd = doc.get("command")
    if cmd is not None:
        if cmd not in COMMANDS:
            v.append(("validation_error", f"command={cmd!r}"))
        elif not isinstance(payload, dict):
            v.append(("validation_error", "payload missing/not object"))
        elif cmd == "notary.intake_analyze":
            check_intake_payload(payload, v)
        elif cmd == "notary.workspace_commit_stage":
            check_base_revision(payload, ctx, v)
            # đợt 3: payload.case optional — meta hồ sơ cùng transaction
            cm = payload.get("case")
            if cm is not None:
                if not isinstance(cm, dict):
                    v.append(("validation_error",
                              "payload.case not object"))
                else:
                    extra = set(cm) - COMMIT_CASE_FIELDS \
                        - set(CASE_META_CANON)
                    if extra:
                        v.append(("validation_error",
                                  f"payload.case extra keys "
                                  f"{sorted(extra)}"))
                    _canon_conflicts(cm, CASE_META_CANON,
                                     "payload.case", v)
                    nl = cm.get("ngay_lap_ho_so", cm.get("ngaylaphoso"))
                    if nl is not None and not (
                            isinstance(nl, str) and DATE_FULL_RX.match(nl)):
                        v.append(("validation_error",
                                  f"payload.case.ngay_lap_ho_so={nl!r}"))
                    uq = cm.get("nguoi_nhan_uy_quyen_id",
                                cm.get("nguoinhanuyquyenid"))
                    if uq is not None and not (
                            isinstance(uq, int) and uq >= 1):
                        v.append(("validation_error",
                                  "payload.case.nguoi_nhan_uy_quyen_id="
                                  f"{uq!r}"))
            check_stage(payload.get("stage"), "payload.stage", v,
                        draft_v2=draft_v2, case_type=ct, in_payload=True)
        elif cmd == "notary.diagram_save":
            check_base_revision(payload, ctx, v)
            if draft_v2:
                st = payload.get("diagram") or {}
                state = st.get("state") if isinstance(st, dict) else None
                # §13.6: node owner personId phải khớp owner_row_id
                # (ctx.stage_owner_row_id — trạng thái server giả định)
                oid = ctx.get("stage_owner_row_id")
                if isinstance(state, dict) and ct == "inheritance" \
                        and isinstance(state.get("nodes"), list):
                    for n in state["nodes"]:
                        if isinstance(n, dict) and n.get("id") == "owner" \
                                and n.get("deleted") is not True \
                                and n.get("personId") is not None \
                                and n.get("personId") != oid:
                            v.append(("diagram_owner_mismatch",
                                      f"owner personId="
                                      f"{n.get('personId')!r} "
                                      f"!= owner_row_id={oid!r}"))
        elif cmd == "notary.word_export_batch":
            check_word_batch_payload(payload, v)
        elif cmd == "notary.workspace_create":
            check_create_payload(payload, v, draft_v2=draft_v2)
        # word_export_* trên two_party → case_type_unsupported (§13.5)
        if draft_v2 and ct == "two_party" and cmd in (
                "notary.word_export_options", "notary.word_export_batch"):
            v.append(("case_type_unsupported",
                      f"{cmd} on two_party"))
        # case_id: bắt buộc / nháp được / cấm — §2.1a
        if cmd in CASE_ID_REQUIRED and isinstance(payload, dict):
            if not (isinstance(payload.get("case_id"), int)
                    and payload["case_id"] >= 1):
                v.append(("validation_error",
                          f"payload.case_id={payload.get('case_id')!r}"))
        elif cmd in CASE_ID_DRAFTABLE and isinstance(payload, dict):
            if "case_id" in payload and not (
                    isinstance(payload["case_id"], int)
                    and payload["case_id"] >= 1):
                v.append(("validation_error",
                          f"payload.case_id={payload.get('case_id')!r}"))
            # chế độ nháp của diagram_evaluate cần stage payload (§7.4);
            # stage cấm khi case_id present
            if cmd == "notary.diagram_evaluate":
                if "case_id" not in payload \
                        and "stage" not in payload:
                    v.append(("validation_error",
                              "draft evaluate requires payload.stage"))
                if "case_id" in payload and "stage" in payload:
                    v.append(("validation_error",
                              "payload.stage forbidden when case_id present"))
        elif cmd in CASE_ID_FORBIDDEN and isinstance(payload, dict) \
                and "case_id" in payload:
            v.append(("validation_error",
                      f"payload.case_id forbidden for {cmd}"))
        # stage trong payload (draft evaluate / workspace_create)
        if cmd in CASE_ID_DRAFTABLE or cmd in CASE_ID_FORBIDDEN:
            st = payload.get("stage") if isinstance(payload, dict) else None
            if st is not None and cmd == "notary.diagram_evaluate":
                check_stage(st, "payload.stage", v, draft_v2=draft_v2,
                            case_type=ct, in_payload=True)
        # diagram state trong payload (evaluate/save/create)
        dg = payload.get("diagram") if isinstance(payload, dict) else None
        if isinstance(dg, dict) and "state" in dg:
            check_diagram_state(dg["state"], "payload.diagram.state",
                                stage_ids, v, draft_v2=draft_v2,
                                case_type=ct)

    # --- job rules
    if "status" in doc:
        if doc["status"] not in STATUSES:
            v.append(("validation_error", f"status={doc['status']!r}"))
        if doc.get("waiting_on") not in WAITING_ON:
            v.append(("validation_error",
                      f"waiting_on={doc.get('waiting_on')!r}"))
        if doc["status"] == "waiting_user" and not doc.get("waiting_on"):
            v.append(("validation_error", "waiting_user without waiting_on"))
        if doc["status"] in ("failed", "canceled") and not doc.get("error"):
            v.append(("validation_error", "failed/canceled without error"))
        if doc["status"] == "partial":
            bd = data.get("breakdown") if isinstance(data, dict) else None
            if not (isinstance(bd, dict) and "succeeded" in bd
                    and "failed" in bd):
                v.append(("validation_error", "partial without breakdown"))

    # --- result rules
    kind = res.get("kind") if isinstance(res, dict) else None
    if kind is not None:
        if kind not in KINDS:
            v.append(("validation_error", f"result.kind={kind!r}"))
        else:
            if kind == "intake_analyze" and doc.get("status") == "waiting_user":
                v.append(("validation_error",
                          "intake_analyze waiting_on forbidden"))
            if data is not None:
                check_result_data(kind, data, stage_ids, v,
                                  draft_v2=draft_v2, ctx=ctx)

    return v


def main():
    files = sorted(EX.glob("**/*.json"))
    if not files:
        print("no examples found")
        return 1
    bad = 0
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        viols = violations(doc)
        name = f.name
        if ".invalid." in name:
            exp = doc.get("expected_error")
            ok = bool(viols) and exp in ERRORS and any(
                c == exp for c, _ in viols)
            status = "REJECTED-CORRECTLY" if ok else \
                "!! NOT REJECTED AS EXPECTED"
            print(f"[invalid] {name}: expected={exp} "
                  f"got={[c for c, _ in viols]} -> {status}")
        else:
            ok = not viols
            print(f"[valid]   {name}: violations={viols} -> "
                  f"{'PASS' if ok else '!! FAIL'}")
        bad += 0 if ok else 1
    print(f"\n{len(files)} files, {bad} unexpected outcomes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
