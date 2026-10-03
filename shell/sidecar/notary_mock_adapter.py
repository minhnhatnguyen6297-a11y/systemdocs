"""Mock backend cho 8 command notary.* — notary.case-drafting.v2 (MIN-128).

Chi duoc goi qua notary_gateway khi G1_DEV_NOTARY_MOCK=1 + khong packaged.
SOT wire: contracts/notary-case-drafting.md §13 — mock tra dung shape/error
code cua contract; khong chinh contract, khong phat minh code moi.

Nguon du lieu: scenario fixtures JSON o
`shell/test/fixtures/notary-case-drafting/*.json` (merge tat ca case, key =
case_id). Fixture la database gia cua mock — "mock tra fixture bat bien".
Thieu thu muc fixture (packaged build, khong bao gio vi gateway chan) ->
fallback seed toi thieu trong code.

Scenario mac dinh: 42 ready | 43 empty | 44 locked | 45 gift (unsupported)
| 46 ready + pool chua gan. Khac -> case_not_found.

Marker deterministic (khong PII, khong parse that):
  - text/file name chua "mock_fail"       -> errors[] intake.parse_failed
  - chua "mock_unsupported"               -> errors[] intake.unsupported_target
  - diagram.render_model="auto" trong seed -> tinh render_model luc load

word_export_batch tao DOCX that bang python-docx (dep co san) theo naming
`<stem>_HS-<case_id>[_n].docx`, reservation trong batch, KHONG BAO GIO ghi
de — ghi vao destination file_ref, khong viet ra folder nguoi dung khac.

Gioi han platform da biet (khong sua trong task nay — jobstore):
  - job failed/canceled -> result=null (jobstore huy result); mock van tra
    error code + details dung contract; thong tin per-file nam trong
    error.details.documents / tren dia.
  - status "partial": handler tra result kem key "partial" lam marker —
    JobStore doc roi POP khoi result truoc khi len wire (jobstore.py).
"""
import copy
import hashlib
import json
import re
import threading
import time
import uuid
from pathlib import Path

from errors import CommandError
from fileref import validate_file_ref

SCHEMA_VERSION = "notary.case-drafting.v2"
DIAGRAM_STATE_VERSION = 3
CASE_TYPE_INHERITANCE = "inheritance"
CASE_TYPE_TWO_PARTY = "two_party"
CASE_TYPES = (CASE_TYPE_INHERITANCE, CASE_TYPE_TWO_PARTY)
DOCUMENT_TYPES = ("khai_nhan", "thoa_thuan")
DOCUMENT_TYPES_TWO_PARTY = ("chuyen_nhuong", "tang_cho",
                            "cho_thue", "dat_coc")
MAX_ASSETS = 3
MAX_PEOPLE_TWO_PARTY = 30
POSITIONS = (1, 2, 3)
TWO_PARTY_IDS = tuple(f"p{i}" for i in range(1, 31))
TWO_PARTY_ID_SET = set(TWO_PARTY_IDS)

# Gioi han contract §5.2 — mock giu nguyen, khong noi.
MAX_SOURCES = 8
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARS = 100_000

# Delay mo phong moi file word — cho cancel co cua so; test monkeypatch.
WORD_DOC_DELAY = 0.05

UUID4_RX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}"
    r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
DATE_OR_YEAR_RX = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")
DATE_FULL_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SERIAL_RX = re.compile(r"^[A-Z]{2}\d{6,8}$")
DOC_KEY_RX = re.compile(r"^[a-z][a-z0-9_]*$")
GENDERS = ("Nam", "Nữ", None)
INTAKE_KINDS = ("image", "pdf", "docx", "xlsx", "text")
NODE_BOOL_FIELDS = ("hidden", "deleted")
NODE_FIELDS = {"id", "personId", "parentSlotIds", "spouseSlotId",
               "ownPositions", "receivePositions", "hidden", "deleted"}
NODE_FIELDS_TWO_PARTY = {"id", "personId", "hidden", "deleted"}
PERSON_FIELDS = ("row_id", "entity_id", "ho_ten", "gioi_tinh", "ngay_sinh",
                 "ngay_chet", "so_giay_to", "ngay_cap", "noi_cap",
                 "dia_chi", "place_of_origin",
                 # đợt 3 (MIN-141): emit thêm; payload nhận cả canonical
                 "loai_giay_to", "loai_dia_chi")
# Canonical key → legacy (contract §4.1; parity case_workspace._PERSON_KEY_ALIASES)
PERSON_CANON = {
    "ten": "ho_ten", "gioitinh": "gioi_tinh", "ngaysinh": "ngay_sinh",
    "ngaychet": "ngay_chet", "sogiayto": "so_giay_to",
    "ngaycap": "ngay_cap", "noicap": "noi_cap", "diachi": "dia_chi",
    "loaigiayto": "loai_giay_to", "loaidiachi": "loai_dia_chi",
}
# Canonical key → legacy cho payload.case (contract §6; parity
# case_workspace._CASE_META_KEY_ALIASES)
CASE_META_CANON = {
    "casetype": "case_type", "documenttype": "document_type",
    "ngaylaphoso": "ngay_lap_ho_so", "noiniemyet": "noi_niem_yet",
    "nguoinhanuyquyen": "nguoi_nhan_uy_quyen",
    "nguoinhanuyquyenid": "nguoi_nhan_uy_quyen_id",
    "noidungviec": "noi_dung_viec", "ghichu": "ghi_chu",
}
ASSET_FIELDS = ("row_id", "entity_id", "so_serial",
                "so_vao_so", "so_thua_dat", "so_to_ban_do", "dia_chi",
                "loai_so", "hinh_thuc_su_dung", "thoi_han", "nguon_goc",
                "ngay_cap", "co_quan_cap", "land_rows")
STAGE_FIELDS = {"owner_row_id", "people", "assets"}

# Catalog van ban v1 (contract §8.1) + filename_stem ASCII do backend so huu.
DOC_CATALOG = {
    "khai_nhan_di_san": {
        "display_name": "Văn bản khai nhận di sản",
        "filename_stem": "Van_ban_khai_nhan_di_san",
    },
    "thoa_thuan_phan_chia": {
        "display_name": "Thỏa thuận phân chia di sản",
        "filename_stem": "Thoa_thuan_phan_chia_di_san",
    },
    "niem_yet": {
        "display_name": "Thông báo niêm yết",
        "filename_stem": "Thong_bao_niem_yet",
    },
}
# niem_yet chua co template -> luon bi block (contract §8.1 catalog note).
NO_TEMPLATE_KEYS = {"niem_yet"}

_FIXTURE_DIR = (Path(__file__).resolve().parent.parent
                / "test" / "fixtures" / "notary-case-drafting")

_FAIL_MARK = "mock_fail"
_UNSUPPORTED_MARK = "mock_unsupported"


# ---------- seed / state ----------

def _resolve_case_ref(case, fixture_dir, cid):
    """Case seed co the la {'$ref_scenario': '<name>'} — nap tu file khac."""
    if isinstance(case, dict) and "$ref_scenario" in case:
        ref = fixture_dir / (case["$ref_scenario"] + ".json")
        try:
            doc = json.loads(ref.read_text(encoding="utf-8"))
        except OSError:
            return None
        cases = doc.get("cases") or {}
        return copy.deepcopy(cases.get(cid) or
                             cases.get(next(iter(cases), None)))
    return case


def _builtin_cases():
    """Fallback toi thieu khi fixture dir khong ton tai (chi defensive —
    mock khong chay packaged)."""
    return {
        "43": {
            "case_type": "inheritance", "document_type": "khai_nhan",
            "status": "draft", "locked": False, "revision": 1,
            "stage": {"owner_row_id": None, "people": [], "assets": []},
            "diagram": {"domain": "inheritance",
                        "state": {"version": 3, "domain": "inheritance",
                                  "nodes": []},
                        "render_model": None, "warnings": []},
        },
    }


# Thu tu merge fixture — case 42 duoc khai o nhieu file (ready goc,
# conflict/intake-partial la ban giam); seed mac dinh lay phien ban
# "primary" truoc. Seed rieng trong test dung reset_backend(seed).
_FIXTURE_PRIORITY = (
    "ready", "ready-two-party", "empty", "locked", "unsupported",
    "diagram-warning", "intake-partial", "conflict", "word-collision",
    "word-partial", "word-all-failed", "word-canceled",
)


def _load_default_cases():
    """Merge moi fixture *.json thanh case map; fallback builtin."""
    cases = {}
    if _FIXTURE_DIR.is_dir():
        files = sorted(
            _FIXTURE_DIR.glob("*.json"),
            key=lambda f: (
                _FIXTURE_PRIORITY.index(f.stem)
                if f.stem in _FIXTURE_PRIORITY else 99, f.stem))
        for f in files:
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for cid, c in (doc.get("cases") or {}).items():
                c = _resolve_case_ref(c, _FIXTURE_DIR, cid)
                if isinstance(c, dict) and cid not in cases:
                    cases[cid] = c
    return cases or _builtin_cases()


class _MockState:
    """Server gia trong bo nho — case map + counter entity_id."""

    def __init__(self, seed=None):
        self._lock = threading.Lock()
        self._next_entity_id = 500
        # đợt 3 (MIN-141): danh ba gia cho dropdown uy quyen — seed tu
        # fixture key "customers" (list) neu co, mac dinh rong.
        self._next_customer_id = 900
        self.customers = {}
        for c in (seed or {}).get("customers") or []:
            if isinstance(c, dict) and c.get("id") is not None:
                self.customers[int(c["id"])] = dict(c)
        # idempotency_key -> case_id (workspace_create replay, §4.3)
        self._idempotency = {}
        raw = (seed or {}).get("cases") or _load_default_cases()
        self.cases = {}
        for cid, c in raw.items():
            prepared = self._prepare(c)
            prepared["id"] = int(cid)
            self.cases[int(cid)] = prepared

    def _prepare(self, c):
        case = copy.deepcopy(c)
        case.setdefault("case_type", "inheritance")
        case.setdefault("document_type", "khai_nhan")
        case.setdefault("status", "draft")
        case.setdefault("locked", False)
        case.setdefault("revision", 1)
        case.setdefault("ngay_lap_ho_so", None)
        case.setdefault("noi_niem_yet", None)
        case.setdefault("nguoi_nhan_uy_quyen", None)
        case.setdefault("nguoi_nhan_uy_quyen_id", None)
        case.setdefault("noi_dung_viec", None)
        case.setdefault("ghi_chu", None)
        stage = case.setdefault("stage", {"people": [], "assets": []})
        stage.setdefault("people", [])
        stage.setdefault("assets", [])
        if case["case_type"] == CASE_TYPE_INHERITANCE:
            stage.setdefault("owner_row_id", None)
        else:
            stage.pop("owner_row_id", None)
        dg = case.setdefault("diagram", {})
        dom = (case["case_type"] if case["case_type"] in CASE_TYPES
               else CASE_TYPE_INHERITANCE)
        dg["domain"] = dom
        state = dg.setdefault("state", {})
        state["version"] = DIAGRAM_STATE_VERSION
        state["domain"] = dom
        if dom == CASE_TYPE_TWO_PARTY:
            state["nodes"] = _canonical_two_party(
                state.get("nodes") or [])
        else:
            state.setdefault("nodes", [])
        dg.setdefault("warnings", [])
        if dg.get("render_model") == "auto":
            # render_model luon khop state hien tai (contract §4);
            # two_party khong qua engine -> unsupported (§13.5)
            dg["render_model"] = (
                _unsupported_render() if dom == CASE_TYPE_TWO_PARTY
                else _render(state, stage))
        elif "render_model" not in dg:
            dg["render_model"] = None
        return case

    def assign_entity_id(self):
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid


_STATE = None
_STATE_LOCK = threading.Lock()


def _state():
    global _STATE
    with _STATE_LOCK:
        if _STATE is None:
            _STATE = _MockState()
        return _STATE


def reset_backend(seed=None):
    """Test hook: reset state; seed={'cases': {...}} hoac None = default."""
    global _STATE
    with _STATE_LOCK:
        _STATE = _MockState(seed)


# ---------- helpers ----------

def _result(kind, data, warnings=None, source_files=None,
            evidence=None, partial=False):
    r = {"kind": kind, "data": data,
         "evidence": evidence or [], "warnings": warnings or [],
         "source_files": source_files or []}
    if partial:
        r["partial"] = True        # marker jobstore -> status 'partial'
    return r


def _case(payload):
    cid = (payload or {}).get("case_id")
    if not isinstance(cid, int) or isinstance(cid, bool) or cid < 1:
        raise CommandError("validation_error",
                           f"case_id={cid!r} phai la int >= 1")
    case = _state().cases.get(cid)
    if case is None:
        raise CommandError("case_not_found",
                           f"Không tìm thấy hồ sơ #{cid}",
                           details={"case_id": cid})
    return case


def _check_supported(case):
    ct = case.get("case_type")
    if ct not in CASE_TYPES:
        raise CommandError("case_type_unsupported",
                           f"loại việc {ct!r} chưa hỗ trợ trong v2",
                           details={"case_type": ct})


def _check_writable(case):
    # Real parity (commit_stage/save_diagram): locked TRUOC case_type —
    # gift+locked -> workspace_locked, khong phai case_type_unsupported.
    if case.get("locked"):
        raise CommandError("workspace_locked",
                           f"hồ sơ #{case['id']} đã khóa")
    _check_supported(case)


def _check_base_revision(case, payload):
    br = (payload or {}).get("base_revision")
    if not isinstance(br, int) or isinstance(br, bool) or br < 1:
        raise CommandError("validation_error",
                           f"base_revision={br!r} phai la int >= 1")
    srv = case["revision"]
    if br != srv:
        raise CommandError("workspace_conflict",
                           f"base_revision={br} khác server_revision={srv}",
                           details={"server_revision": srv})


def _det_uuid4(seed):
    """UUID4-shaped deterministic id cho suggestion (suggestion_id do
    backend sinh — fixture bat bien giua hai lan goi)."""
    h = hashlib.md5(seed.encode("utf-8")).hexdigest()
    return (f"{h[0:8]}-{h[8:12]}-4{h[13:16]}-"
            f"{('8', '9', 'a', 'b')[int(h[16], 16) % 4]}{h[17:20]}-{h[20:32]}")


def _person_map(case):
    return {p["row_id"]: p for p in case["stage"]["people"]
            if isinstance(p, dict)}


# ---------- diagram validation + render (mock engine, contract v2 §13.4) ----------

def _canonical_two_party(nodes):
    """state two_party canonical — đủ đúng 30 slot p1..p30 theo thứ tự."""
    by_id = {n.get("id"): n for n in nodes if isinstance(n, dict)}
    return [{
        "id": pid,
        "personId": (by_id.get(pid) or {}).get("personId"),
        "hidden": bool((by_id.get(pid) or {}).get("hidden")),
        "deleted": bool((by_id.get(pid) or {}).get("deleted")),
    } for pid in TWO_PARTY_IDS]


def _unsupported_render():
    """render_model unsupported — sơ đồ hai bên KHÔNG qua engine (§13.5)."""
    return {"engineVersion": 2, "status": "unsupported", "allocations": {},
            "breakdowns": [], "requiredSlots": [],
            "warnings": [{
                "code": "diagram.two_party_unsupported",
                "message": "Sơ đồ hai bên không chạy engine thừa kế"}],
            "errors": [], "unresolvedEstates": [],
            "conservation": {"allocated": "0", "unresolved": "0",
                             "total": "0"}}


def _validate_diagram_state(state):
    """diagram_state_v3 → [errors] (engine codes §13.4/§13.9). Nhánh
    theo state.domain (real parity: wire check doc domain tu state;
    mismatch voi case_type do _check_domain bat truoc).

    personId không phải uuid4 / ngoài stage KHÔNG nằm trong nhóm này —
    caller map sang diagram_reference_outside_stage (nhất quán real)."""
    errors = []
    if not isinstance(state, dict):
        return [{"code": "invalid_input",
                 "message": "state không phải object"}]
    if state.get("version") != DIAGRAM_STATE_VERSION:
        errors.append({"code": "invalid_version",
                       "message": f"version={state.get('version')!r}, cần "
                                  f"{DIAGRAM_STATE_VERSION}"})
    dom = state.get("domain")
    if dom not in CASE_TYPES:
        errors.append({"code": "invalid_domain",
                       "message": f"domain={dom!r} ∉ {list(CASE_TYPES)}"})
    nodes = state.get("nodes")
    if not isinstance(nodes, list):
        errors.append({"code": "invalid_nodes",
                       "message": "nodes không phải list"})
        return errors
    two_party = dom == CASE_TYPE_TWO_PARTY
    ids = set()
    node_by_id = {}
    persons = set()
    for i, n in enumerate(nodes):
        w = f"nodes[{i}]"
        if not isinstance(n, dict):
            errors.append({"code": "invalid_node", "node": w,
                           "message": f"{w} không phải object"})
            continue
        nid = n.get("id")
        extra = set(n) - (NODE_FIELDS_TWO_PARTY if two_party
                          else NODE_FIELDS)
        for k in extra:
            errors.append({"code": "invalid_node", "node": nid or w,
                           "message": f"{w} field lạ {k!r}"})
        if two_party:
            if not isinstance(nid, str):
                errors.append({"code": "invalid_node_id", "node": w,
                               "message": f"{w}.id phải là chuỗi"})
            elif nid not in TWO_PARTY_ID_SET or i >= 30 \
                    or nid != f"p{i + 1}":
                errors.append({"code": "invalid_position", "node": nid or w,
                               "message": f"{w}.id={nid!r} — kỳ vọng "
                                          f"'p{i + 1}' theo canonical"})
            elif nid in ids:
                errors.append({"code": "duplicate_node", "node": nid,
                               "message": f"trùng node id {nid!r}"})
            else:
                ids.add(nid)
                node_by_id[nid] = n
        else:
            if not (isinstance(nid, str) and nid.strip()):
                errors.append({"code": "invalid_node_id", "node": w,
                               "message": f"{w} thiếu id"})
                continue
            if nid in ids:
                errors.append({"code": "duplicate_node", "node": nid,
                               "message": f"trùng node id {nid!r}"})
                continue
            ids.add(nid)
            node_by_id[nid] = n
        for f in NODE_BOOL_FIELDS:
            if not isinstance(n.get(f), bool):
                errors.append({"code": "invalid_boolean", "node": nid or w,
                               "message": f"{w}.{f} phải là boolean"})
        pid = n.get("personId")
        if pid is not None and n.get("deleted") is not True:
            if pid in persons:
                errors.append({"code": "duplicate_person", "node": nid or w,
                               "message": f"personId {pid} gán trên "
                                          "nhiều node"})
            persons.add(pid)
        if two_party or dom != CASE_TYPE_INHERITANCE:
            continue
        ps = n.get("parentSlotIds")
        if not (isinstance(ps, list) and len(ps) <= 2
                and all(isinstance(x, str) and x.strip() for x in ps)):
            errors.append({"code": "invalid_parent", "node": nid,
                           "message": f"{w}.parentSlotIds phải là "
                                      "list ≤2 string non-empty"})
            ps = []
        elif len(set(ps)) != len(ps):
            errors.append({"code": "duplicate_parent", "node": nid,
                           "message": f"{w}.parentSlotIds trùng"})
        elif nid in ps:
            errors.append({"code": "self_parent", "node": nid,
                           "message": f"{nid} tự làm cha"})
        ss = n.get("spouseSlotId")
        if ss is not None and not (isinstance(ss, str) and ss.strip()):
            errors.append({"code": "invalid_spouse", "node": nid,
                           "message": f"{w}.spouseSlotId phải là "
                                      "string non-empty/null"})
        elif ss == nid:
            errors.append({"code": "self_spouse", "node": nid,
                           "message": f"{nid} tự làm vợ/chồng"})
        for pf in ("ownPositions", "receivePositions"):
            arr = n.get(pf)
            if not isinstance(arr, list):
                errors.append({"code": "invalid_position", "node": nid,
                               "message": f"{w}.{pf} phải là list ⊆ "
                                          "{1,2,3}"})
            elif (any(isinstance(x, bool) or not isinstance(x, int)
                      or x not in POSITIONS for x in arr)
                    or len(set(arr)) != len(arr)):
                errors.append({"code": "invalid_position", "node": nid,
                               "message": f"{w}.{pf} phải ⊆ {{1,2,3}} "
                                          "không trùng"})
    if two_party and ids != TWO_PARTY_ID_SET:
        missing = sorted(TWO_PARTY_ID_SET - ids, key=lambda s: int(s[1:]))
        errors.append({"code": "missing_position",
                       "message": f"state two_party thiếu slot {missing}"})
    if dom == CASE_TYPE_INHERITANCE:
        # dangling refs + spouse conflict + ancestry cycle (giữ §7.1).
        for i, n in enumerate(nodes):
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            for p in n.get("parentSlotIds") or []:
                if isinstance(p, str) and p not in ids:
                    errors.append({"code": "dangling_parent", "node": nid,
                                   "message": f"{nid} tham chiếu parent "
                                              f"{p!r} không tồn tại"})
            ss = n.get("spouseSlotId")
            if isinstance(ss, str):
                if ss not in ids:
                    errors.append({"code": "dangling_spouse", "node": nid,
                                   "message": f"{nid} tham chiếu spouse "
                                              f"{ss!r} không tồn tại"})
                else:
                    other = node_by_id.get(ss) or {}
                    if other.get("spouseSlotId") != nid:
                        errors.append({"code": "spouse_conflict",
                                       "node": nid,
                                       "message": f"{nid}↔{ss} spouse "
                                                  "không đối xứng"})
        for nid in ids:
            seen = set()
            frontier = list(
                (node_by_id.get(nid) or {}).get("parentSlotIds") or [])
            while frontier:
                cur = frontier.pop()
                if cur == nid:
                    errors.append({"code": "ancestry_cycle", "node": nid,
                                   "message": f"chu kỳ tổ tiên qua {nid}"})
                    frontier = []
                    break
                if cur in seen:
                    continue
                seen.add(cur)
                frontier.extend(
                    (node_by_id.get(cur) or {}).get("parentSlotIds") or [])
    return errors


def _outside_person(state, stage_ids):
    """personId sai định dạng uuid4 hoặc ngoài stage → trả pid đó."""
    for n in (state.get("nodes") or []):
        if not isinstance(n, dict):
            continue
        pid = n.get("personId")
        if pid is None:
            continue
        if not (isinstance(pid, str) and UUID4_RX.match(pid)) \
                or pid not in stage_ids:
            return pid
    return None


def _persisted_diagram_state(state):
    """Normalize state đã validate về canonical persist shape."""
    if state["domain"] == CASE_TYPE_TWO_PARTY:
        return {"version": DIAGRAM_STATE_VERSION,
                "domain": CASE_TYPE_TWO_PARTY,
                "nodes": _canonical_two_party(state["nodes"])}
    return {"version": DIAGRAM_STATE_VERSION,
            "domain": CASE_TYPE_INHERITANCE,
            "nodes": [{
                "id": n["id"], "personId": n.get("personId"),
                "parentSlotIds": list(n.get("parentSlotIds") or []),
                "spouseSlotId": n.get("spouseSlotId"),
                "ownPositions": list(n.get("ownPositions") or []),
                "receivePositions": list(n.get("receivePositions") or []),
                "hidden": n["hidden"], "deleted": n["deleted"]}
                for n in state["nodes"]]}


def _render(state, stage):
    """Render_model deterministic cua mock engine (shape §7.2, §13.4 A4:
    isLandOwner := ownPositions≠[]; willReceive := receivePositions≠[]).

    Domain two_party khong bao gio vao day (caller tra _unsupported_render).
    Rule don gian mot estate: landowner da chet -> chia deu cho cac node
    receivePositions non-empty co personId. Khong co landowner -> invalid
    missing_land_owner. Pool person chua gan -> incomplete + warning.
    """
    stage_people = _person_map({"stage": stage})
    nodes = [n for n in (state.get("nodes") or [])
             if isinstance(n, dict) and not n.get("deleted")]
    empty = {"engineVersion": 2, "status": "invalid", "allocations": {},
             "breakdowns": [], "requiredSlots": [], "warnings": [],
             "errors": [{"code": "missing_land_owner",
                         "message": "Sơ đồ chưa có chủ đất"}],
             "unresolvedEstates": [],
             "conservation": {"allocated": "0", "unresolved": "0",
                              "total": "0"}}
    landowners = [n for n in nodes
                  if n.get("ownPositions") and n.get("personId")]
    if not landowners:
        if not nodes:
            return empty
        rm = copy.deepcopy(empty)
        rm["requiredSlots"] = _required_slots(nodes)
        return rm
    deceased = [n for n in landowners
                if (stage_people.get(n["personId"]) or {}).get("ngay_chet")]
    assigned = {n["personId"] for n in nodes if n.get("personId")}
    unassigned_pool = [rid for rid in stage_people if rid not in assigned]
    warnings = []
    if unassigned_pool:
        warnings.append({
            "code": "diagram.unassigned_pool_person",
            "message": "Còn người trong Pool chưa được gán trên sơ đồ"})
    receivers = [n for n in nodes
                 if n.get("receivePositions") and n.get("personId")]
    rm = {"engineVersion": 2, "status": "complete", "allocations": {},
          "breakdowns": [], "requiredSlots": _required_slots(nodes),
          "warnings": warnings, "errors": [], "unresolvedEstates": [],
          "conservation": {"allocated": "0", "unresolved": "0",
                           "total": "0"}}
    if not deceased:
        rm["status"] = "incomplete"
        rm["warnings"] = warnings + [{
            "code": "diagram.no_active_estate",
            "message": "Chưa có chủ đất đã chết — chưa phát sinh di sản"}]
        for n in nodes:
            if n.get("personId"):
                rm["allocations"][n["personId"]] = _alloc("0", "0", "0", "0")
        return rm
    if not receivers:
        src = deceased[0]["personId"]
        ev = (stage_people.get(src) or {}).get("ngay_chet")
        # unresolved_estate.eventDate la date_full; ngay_chet nam-le -> null
        if not (isinstance(ev, str) and DATE_FULL_RX.match(ev)):
            ev = None
        rm["status"] = "incomplete"
        rm["unresolvedEstates"] = [{
            "sourcePersonId": src, "eventDate": ev,
            "fraction": "1", "reason": "no_valid_heir"}]
        rm["conservation"] = {"allocated": "0", "unresolved": "1",
                              "total": "1"}
        for n in nodes:
            if n.get("personId"):
                rm["allocations"][n["personId"]] = _alloc("0", "0", "0", "0")
        return rm
    n_recv = len(receivers)
    share = f"1/{n_recv}" if n_recv > 1 else "1"
    pct = f"{100.0 / n_recv:.2f}"
    src_id = deceased[0]["personId"]
    for n in nodes:
        pid = n.get("personId")
        if not pid:
            continue
        if n in landowners and pid == src_id:
            rm["allocations"][pid] = _alloc("1", "0", "1", "0")
        elif n.get("receivePositions"):
            rm["allocations"][pid] = _alloc("0", share, "0", share)
            rm["allocations"][pid]["displayPercent"] = pct
            rm["breakdowns"].append({
                "personId": pid, "total": share,
                "terms": [{"kind": "inheritance", "fraction": share,
                           "sourcePersonId": src_id,
                           "viaBranchPersonIds": []}]})
        else:
            rm["allocations"][pid] = _alloc("0", "0", "0", "0")
    rm["conservation"] = {"allocated": "1", "unresolved": "0", "total": "1"}
    if unassigned_pool:
        rm["status"] = "incomplete"
    return rm


def _alloc(base, inherited, distributed, final):
    return {"baseShare": base, "inheritedShare": inherited,
            "distributedShare": distributed, "finalShare": final,
            "displayPercent": "0.00"}


def _required_slots(nodes):
    return [{"anchorSlotId": n["id"], "reason": "active_estate",
             "slotTypes": ["father", "mother", "spouse", "child"],
             "minimumEmptyChildSlots": 0}
            for n in nodes
            if isinstance(n, dict) and n.get("id") and not n.get("personId")
            and not n.get("deleted")]


def _payload_diagram_state(payload):
    """Lay diagram.state tu payload — thieu field -> validation_error
    (missing required field); state co mat nhung sai shape -> de
    _evaluate_state_or_raise lo (diagram_invalid_state)."""
    dg = (payload or {}).get("diagram")
    if not isinstance(dg, dict) or "state" not in dg:
        raise CommandError("validation_error",
                           "payload.diagram.state bắt buộc")
    return dg["state"]


def _check_domain(state, case_type):
    """state.domain hợp lệ nhưng khác case_type → diagram_domain_mismatch
    — kiem TRUOC wire validation (real parity); domain khong thuoc enum
    -> invalid_domain trong _validate_diagram_state."""
    if isinstance(state, dict):
        dom = state.get("domain")
        if dom in CASE_TYPES and dom != case_type:
            raise CommandError(
                "diagram_domain_mismatch",
                f"state.domain={dom!r} không khớp case_type={case_type!r}",
                details={"expected": case_type, "got": dom})


def _validate_case_state(case, state):
    """domain + wire validation tren case da commit."""
    _check_domain(state, case["case_type"])
    errors = _validate_diagram_state(state)
    if errors:
        raise CommandError("diagram_invalid_state",
                           "diagram state không hợp lệ",
                           details={"errors": errors})


def _check_owner_node(case, state):
    """diagram_save owner mirror (§13.4): node 'owner' co personId phai
    = owner_row_id da commit -> sai = diagram_owner_mismatch."""
    if case["case_type"] != CASE_TYPE_INHERITANCE:
        return
    oid = (case.get("stage") or {}).get("owner_row_id")
    owner_pid = next(
        (n.get("personId") for n in state.get("nodes") or []
         if isinstance(n, dict) and n.get("id") == "owner"
         and n.get("deleted") is not True
         and n.get("personId") is not None), None)
    if owner_pid is not None and owner_pid != oid:
        raise CommandError(
            "diagram_owner_mismatch",
            "node owner.personId phải khớp stage.owner_row_id đã commit",
            details={"owner_row_id": oid, "node_personId": owner_pid})


def _check_person_refs(state, stage_ids):
    outside_pid = _outside_person(state, stage_ids)
    if outside_pid is not None:
        raise CommandError("diagram_reference_outside_stage",
                           f"personId {outside_pid} không thuộc Stage "
                           "đã commit", details={"personId": outside_pid})


def _evaluate_state_or_raise(case, state):
    """diagram_evaluate tren case committed: domain -> wire -> refs ->
    render (real parity; KHONG kem owner-mismatch)."""
    _validate_case_state(case, state)
    _check_person_refs(state, set(_person_map(case)))
    if case["case_type"] == CASE_TYPE_TWO_PARTY:
        return _unsupported_render()
    return _render(state, case["stage"])


def _sync_owner_node(case):
    """Server seed/refresh node 'owner' := stage.owner_row_id khi commit.

    Được gọi sau _prune_diagram; owner_row_id đã được validate thuộc
    stage.people. Node owner mới được append đuôi — client drag lại."""
    if case.get("case_type") != CASE_TYPE_INHERITANCE:
        return
    oid = (case.get("stage") or {}).get("owner_row_id")
    nodes = (case.get("diagram") or {}).get("state", {}).get("nodes") or []
    for n in nodes:
        if isinstance(n, dict) and n.get("id") == "owner":
            n["personId"] = oid
            return
    nodes.append({
        "id": "owner", "personId": oid, "parentSlotIds": [],
        "spouseSlotId": None, "ownPositions": [], "receivePositions": [],
        "hidden": False, "deleted": False})


def _prune_diagram(case):
    """Sau commit stage: prune refs + vị trí (§13.4 R6 + MAX_ASSETS).

    - personId ngoài Stage: inheritance drop node (đã có link thì scrub);
      two_party chỉ clear personId (canonical giữ đủ 30 slot).
    - inheritance: node 'owner' sync := owner_row_id (server SOT).
    - own/receivePositions: bỏ vị trí > len(assets) → pruned=True."""
    ct = case.get("case_type")
    stage_ids = set(_person_map(case))
    two_party = ct == CASE_TYPE_TWO_PARTY
    state = case["diagram"].get("state") or {}
    nodes = state.get("nodes") or []
    node_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
    dropped = set()
    if two_party:
        for n in nodes:
            if isinstance(n, dict) and n.get("personId") \
                    and n["personId"] not in stage_ids:
                n["personId"] = None
        # Real _canonical_two_party_nodes: giu dung 30 slot p1..p30
        # theo thu tu, khong compact.
        state["nodes"] = nodes = _canonical_two_party(nodes)
    else:
        kept = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            pid = n.get("personId")
            if pid is not None and pid not in stage_ids:
                dropped.add(n.get("id"))
                continue
            kept.append(n)
        nodes = kept
        state["nodes"] = nodes
    pruned = False
    for n in nodes:
        if isinstance(n.get("parentSlotIds"), list):
            n["parentSlotIds"] = [p for p in n["parentSlotIds"]
                                  if p in node_ids and p not in dropped]
        ss = n.get("spouseSlotId")
        if ss is not None and (ss not in node_ids or ss in dropped):
            n["spouseSlotId"] = None
        if two_party:
            continue
        for k in ("ownPositions", "receivePositions"):
            arr = n.get(k)
            if isinstance(arr, list):
                allowed = list(range(1, len(case["stage"]["assets"]) + 1))
                pruned = pruned or any(x not in allowed for x in arr)
                n[k] = [x for x in arr if x in allowed]
    _sync_owner_node(case)
    return pruned


# ---------- stage validation ----------

def _err(row_id, field, code, message):
    return {"row_id": row_id, "field": field, "code": code,
            "message": message}


def _err_row(rid, label):
    """field_error.row_id schema bat uuid4 — row_id loi thi dung uuid4
    deterministic tu label (van truy vet duoc qua message)."""
    if isinstance(rid, str) and UUID4_RX.match(rid):
        return rid
    return _det_uuid4(f"field_error:{label}:{rid!r}")


def _validate_stage(stage, case_type):
    """Tra (field_errors, people_norm, assets_norm). Norm = strip field la
    + dien null cho nullable thieu (producer strip — contract §4.1).

    Code parity voi validator oracle + case_workspace._validate_stage:
    - loi CONTAINER/shape (stage khong dict / people|assets thieu hoac
      khong list) + key la -> validation_error;
    - owner_row_id: bat buoc + tro row co that voi inheritance ->
      workspace_owner_required; CÂM voi two_party -> validation_error;
    - field_errors chi cho loi ROW-level + limit (asset_limit/
      people_limit — §13.9 field-error codes)."""
    if not isinstance(stage, dict):
        raise CommandError("validation_error",
                           "stage phải là object")
    extra = set(stage) - STAGE_FIELDS
    if extra:
        raise CommandError("validation_error",
                           f"stage key lạ: {sorted(extra)}")
    missing = [k for k in ("people", "assets")
               if not isinstance(stage.get(k), list)]
    if missing:
        raise CommandError(
            "validation_error",
            f"stage.{', stage.'.join(missing)} phải là list")
    people = stage["people"]
    assets = stage["assets"]
    if case_type == CASE_TYPE_TWO_PARTY:
        if "owner_row_id" in stage:
            raise CommandError(
                "validation_error",
                "stage.owner_row_id cấm với case_type two_party")
    else:
        oid = stage.get("owner_row_id")
        people_ids = {r.get("row_id") for r in people
                      if isinstance(r, dict)}
        if not (isinstance(oid, str) and UUID4_RX.match(oid)
                and oid in people_ids):
            raise CommandError(
                "workspace_owner_required",
                "stage.owner_row_id phải là row_id của một dòng Người "
                "trong stage (inheritance)")
    errs = []
    seen = set()
    seen_pkeys = set()
    seen_pentities = set()
    seen_serials = set()
    seen_aentities = set()

    def _nullable(r, field, w):
        """Parity _check_nullable_str: non-string → invalid_type;
        chuỗi rỗng → invalid_format."""
        v = r.get(field)
        if v is not None and not isinstance(v, str):
            errs.append(_err(w, field, "invalid_type",
                             f"{field} phải là chuỗi/null"))
        elif isinstance(v, str) and not v.strip():
            errs.append(_err(w, field, "invalid_format",
                             f"{field} rỗng — dùng null"))

    people_norm = []
    for i, r in enumerate(people):
        if isinstance(r, dict):
            # đợt 3: fold key canonical -> legacy trước validate
            # (parity case_workspace.commit_stage).
            r = _fold_canon(r, PERSON_CANON, f"people[{i}]")
        rid = r.get("row_id") if isinstance(r, dict) else None
        w = _err_row(rid, f"people[{i}]")
        if not isinstance(r, dict):
            errs.append(_err(w, "row", "invalid_type",
                             f"people[{i}] không phải object"))
            continue
        extra = set(r) - set(PERSON_FIELDS)
        if extra:
            raise CommandError(
                "validation_error",
                f"people[{i}] key lạ: {sorted(extra)}")
        if not (isinstance(rid, str) and UUID4_RX.match(rid)):
            errs.append(_err(w, "row_id", "invalid_format",
                             f"row_id phải là uuid4 (nhận {rid!r})"))
        elif rid in seen:
            errs.append(_err(rid, "row_id", "duplicate_row_id",
                             "row_id trùng trong payload"))
        else:
            seen.add(rid)
        eid = r.get("entity_id")
        if eid is not None and (not isinstance(eid, int)
                                or isinstance(eid, bool) or eid < 1):
            errs.append(_err(w, "entity_id", "invalid_type",
                             "entity_id phải là int >= 1/null"))
        elif eid is not None:
            if eid in seen_pentities:
                errs.append(_err(w, "entity_id", "invalid_format",
                                 "entity_id trùng với dòng khác"))
            else:
                seen_pentities.add(eid)
        ht = r.get("ho_ten")
        if not (isinstance(ht, str) and ht.strip()):
            errs.append(_err(w, "ho_ten", "required", "ho_ten bắt buộc"))
        if r.get("gioi_tinh") not in GENDERS:
            errs.append(_err(w, "gioi_tinh", "invalid_enum",
                             "gioi_tinh ∈ {Nam, Nữ, null}"))
        for f in ("ngay_sinh", "ngay_chet", "ngay_cap"):
            v = r.get(f)
            if v is not None and not (isinstance(v, str)
                                      and DATE_OR_YEAR_RX.match(v)):
                errs.append(_err(w, f, "invalid_date",
                                 f"{f} phải YYYY-MM-DD/YYYY/null"))
        for f in ("so_giay_to", "noi_cap", "dia_chi",
                  "place_of_origin", "loai_giay_to", "loai_dia_chi"):
            _nullable(r, f, w)
        sgt = r.get("so_giay_to")
        if isinstance(sgt, str) and sgt.strip():
            s = sgt.strip()
            if s in seen_pkeys:
                errs.append(_err(w, "so_giay_to", "invalid_format",
                                 "so_giay_to trùng với dòng khác"))
            else:
                seen_pkeys.add(s)
        people_norm.append({f: r.get(f) for f in PERSON_FIELDS})
    assets_norm = []
    for i, r in enumerate(assets):
        rid = r.get("row_id") if isinstance(r, dict) else None
        w = _err_row(rid, f"assets[{i}]")
        if not isinstance(r, dict):
            errs.append(_err(w, "row", "invalid_type",
                             f"assets[{i}] không phải object"))
            continue
        extra = set(r) - set(ASSET_FIELDS)
        if extra:
            raise CommandError(
                "validation_error",
                f"assets[{i}] key lạ: {sorted(extra)}")
        if not (isinstance(rid, str) and UUID4_RX.match(rid)):
            errs.append(_err(w, "row_id", "invalid_format",
                             f"row_id phải là uuid4 (nhận {rid!r})"))
        elif rid in seen:
            errs.append(_err(rid, "row_id", "duplicate_row_id",
                             "row_id trùng trong payload"))
        else:
            seen.add(rid)
        eid = r.get("entity_id")
        if eid is not None and (not isinstance(eid, int)
                                or isinstance(eid, bool) or eid < 1):
            errs.append(_err(w, "entity_id", "invalid_type",
                             "entity_id phải là int >= 1/null"))
        elif eid is not None:
            if eid in seen_aentities:
                errs.append(_err(w, "entity_id", "invalid_format",
                                 "entity_id trùng với dòng khác"))
            else:
                seen_aentities.add(eid)
        serial = r.get("so_serial")
        canon = serial.strip() if isinstance(serial, str) else serial
        if not canon:
            errs.append(_err(w, "so_serial", "required",
                             "so_serial bắt buộc"))
        elif not SERIAL_RX.match(canon):
            errs.append(_err(w, "so_serial", "invalid_format",
                             "so_serial phải canonical [A-Z]{2}\\d{6,8}"))
        elif canon in seen_serials:
            errs.append(_err(w, "so_serial", "invalid_format",
                             "so_serial trùng với dòng khác"))
        else:
            seen_serials.add(canon)
        dc = r.get("dia_chi")
        if not (isinstance(dc, str) and dc.strip()):
            errs.append(_err(w, "dia_chi", "required", "dia_chi bắt buộc"))
        nc = r.get("ngay_cap")
        if nc is not None and not (isinstance(nc, str)
                                   and DATE_FULL_RX.match(nc)):
            errs.append(_err(w, "ngay_cap", "invalid_date",
                             "ngay_cap tài sản chỉ nhận YYYY-MM-DD"))
        for f in ("so_vao_so", "so_thua_dat", "so_to_ban_do",
                  "loai_so", "hinh_thuc_su_dung", "thoi_han",
                  "nguon_goc", "co_quan_cap"):
            _nullable(r, f, w)
        lr = r.get("land_rows")
        if lr is not None and not isinstance(lr, list):
            errs.append(_err(w, "land_rows", "invalid_type",
                             "land_rows phải là list/null"))
        elif isinstance(lr, list):
            for j, x in enumerate(lr):
                if not isinstance(x, dict):
                    errs.append(_err(w, "land_rows", "invalid_type",
                                     "land_row phải là object"))
                    continue
                dt = x.get("dien_tich")
                if dt is not None and (not isinstance(dt, (int, float))
                                       or isinstance(dt, bool)):
                    errs.append(_err(w, "land_rows", "invalid_type",
                                     "dien_tich phải là number/null"))
                for lf in ("loai_dat", "thoi_han"):
                    if x.get(lf) is not None and not isinstance(
                            x.get(lf), str):
                        errs.append(_err(w, "land_rows", "invalid_type",
                                         f"{lf} phải là chuỗi/null"))
        row = {f: r.get(f) for f in ASSET_FIELDS}
        row["so_serial"] = canon or row["so_serial"]
        row["land_rows"] = [
            {"loai_dat": x.get("loai_dat"),
             "dien_tich": x.get("dien_tich"),
             "thoi_han": x.get("thoi_han")}
            for x in lr if isinstance(x, dict)] \
            if isinstance(lr, list) else None
        assets_norm.append(row)
    # Gioi han §13.3/§13.5 — field_errors, gan row_id dong thua (real
    # parity: loi limit nam sau loi row-level trong field_errors[]).
    for i, r in enumerate(assets[MAX_ASSETS:], start=MAX_ASSETS):
        errs.append(_err(
            _err_row(r.get("row_id") if isinstance(r, dict) else None,
                     f"assets[{i}]"),
            "assets", "asset_limit",
            f"stage.assets tối đa {MAX_ASSETS} (v2)"))
    if case_type == CASE_TYPE_TWO_PARTY:
        for i, r in enumerate(people[MAX_PEOPLE_TWO_PARTY:],
                              start=MAX_PEOPLE_TWO_PARTY):
            errs.append(_err(
                _err_row(r.get("row_id") if isinstance(r, dict) else None,
                         f"people[{i}]"),
                "people", "people_limit",
                f"stage.people tối đa {MAX_PEOPLE_TWO_PARTY} "
                "với two_party"))
    return errs, people_norm, assets_norm


# ---------- commands ----------

def _mock_case_row(cid, case):
    """Row shape parity voi notary_adapter._case_row — nguoi_chet = person
    co ngay_chet (chu the da mat), tai_san = asset position 1 (index 0)."""
    stage = case.get("stage") or {}
    deceased = next(
        (p for p in stage.get("people", []) if p.get("ngay_chet")), None)
    assets = stage.get("assets", [])
    primary = assets[0] if assets else None
    return {
        "id": cid,
        "nguoi_chet": {
            "id": deceased.get("entity_id"), "ho_ten": deceased.get("ho_ten"),
            "gioi_tinh": deceased.get("gioi_tinh"),
            "ngay_sinh": deceased.get("ngay_sinh"),
            "ngay_chet": deceased.get("ngay_chet"),
            "so_giay_to": deceased.get("so_giay_to"),
            "ngay_cap": deceased.get("ngay_cap"),
            "dia_chi": deceased.get("dia_chi"), "con_song": False,
        } if deceased else None,
        "tai_san": {
            "id": primary.get("entity_id"),
            "so_serial": primary.get("so_serial"),
            "so_vao_so": primary.get("so_vao_so"),
            "so_thua_dat": primary.get("so_thua_dat"),
            "so_to_ban_do": primary.get("so_to_ban_do"),
            "dia_chi": primary.get("dia_chi"),
            "loai_dat": primary.get("loai_dat"),
            "dien_tich": primary.get("dien_tich"),
            "loai_so": primary.get("loai_so"),
            "hinh_thuc_su_dung": primary.get("hinh_thuc_su_dung"),
            "thoi_han": primary.get("thoi_han"),
            "nguon_goc": primary.get("nguon_goc"),
            "ngay_cap": primary.get("ngay_cap"),
            "co_quan_cap": primary.get("co_quan_cap"),
        } if primary else None,
        "ngay_lap_ho_so": case.get("ngay_lap_ho_so"),
        "loai_van_ban": case.get("document_type"),
        "trang_thai": case.get("status"),
        "noi_niem_yet": case.get("noi_niem_yet"),
        "ghi_chu": case.get("ghi_chu"),
        "is_locked": bool(case.get("locked")),
        "tong_ty_le": case.get("tong_ty_le"),
    }


def case_list(job, payload):
    """notary.case_list mock (MIN-112): danh sach fixture case cho tab
    Tong quan ho so — cung query/limit semantic voi real adapter."""
    q = str((payload or {}).get("query") or "").strip()
    limit = max(1, min(int((payload or {}).get("limit") or 50), 200))
    st = _state()
    items = [_mock_case_row(cid, st.cases[cid])
             for cid in sorted(st.cases, reverse=True)][:limit]
    if q:
        ql = q.lower()
        items = [i for i in items
                 if ql in json.dumps(i, ensure_ascii=False).lower()]
    job.check_cancel()
    return _result("case_list", {"cases": items, "total": len(items)})


def customer_list(job, payload):
    """notary.customer_list mock (MIN-141 đợt 3): danh bạ người nhận ủy
    quyền — lọc theo tên/số giấy tờ/địa chỉ như search_customers."""
    st = _state()
    q = str((payload or {}).get("query") or "").strip().lower()
    limit = max(1, min(int((payload or {}).get("limit") or 50), 200))
    rows = sorted(st.customers.values(), key=lambda c: c["ho_ten"])
    if q:
        rows = [c for c in rows if q in str(c.get("ho_ten") or "").lower()
                or q in str(c.get("so_giay_to") or "").lower()
                or q in str(c.get("dia_chi") or "").lower()]
    rows = [copy.deepcopy(c) for c in rows[:limit]]
    job.check_cancel()
    return _result("customer_list", {"customers": rows,
                                     "total": len(rows)})


def customer_create(job, payload):
    """notary.customer_create mock (MIN-141 đợt 3): upsert theo
    so_giay_to; thieu → tao moi trong danh ba gia."""
    p = payload or {}
    name = str(p.get("ho_ten") or "").strip()
    if not name:
        raise CommandError("validation_error", "ho_ten bắt buộc")
    st = _state()
    with st._lock:
        sgt = str(p.get("so_giay_to") or "").strip() or None
        existing = None
        if sgt:
            existing = next(
                (c for c in st.customers.values()
                 if c.get("so_giay_to") == sgt), None)
        if existing is not None:
            existing["ho_ten"] = name
            job.check_cancel()
            return _result("customer_upsert",
                           {"customer": copy.deepcopy(existing),
                            "updated": True})
        cid = st._next_customer_id
        st._next_customer_id += 1
        cust = {
            "id": cid, "ho_ten": name,
            "gioi_tinh": p.get("gioi_tinh") or None,
            "ngay_sinh": p.get("ngay_sinh") or None,
            "ngay_chet": p.get("ngay_chet") or None,
            "so_giay_to": sgt,
            "ngay_cap": p.get("ngay_cap") or None,
            "dia_chi": str(p.get("dia_chi") or "").strip() or None,
        }
        st.customers[cid] = cust
        job.check_cancel()
        return _result("customer_upsert",
                       {"customer": copy.deepcopy(cust),
                        "updated": False})


def _workspace_data(cid, case):
    """result.data cua workspace_get/workspace_create — §4 + §4.3 + §13."""
    ct = case.get("case_type")
    caps = ct in CASE_TYPES
    stage = case.get("stage") or {}
    stage_out = {"people": copy.deepcopy(stage.get("people") or []),
                 "assets": copy.deepcopy(stage.get("assets") or [])}
    # Real get(): domain fallback inheritance cho case_type ngoai CASE_TYPES
    # (gift) — owner_row_id emit khi DOMAIN la inheritance, khong phai
    # chi khi case_type == inheritance.
    dom = (case.get("diagram") or {}).get("domain") or (
        ct if ct in CASE_TYPES else CASE_TYPE_INHERITANCE)
    if dom == CASE_TYPE_INHERITANCE:
        stage_out["owner_row_id"] = stage.get("owner_row_id")
    dg = case.get("diagram") or {}
    data = {
        "schema_version": SCHEMA_VERSION,
        "backend_mode": "mock",          # contract §4 — nhan 'Dữ liệu mô phỏng'
        "case": {
            "id": cid,
            "case_type": ct,
            "document_type": case.get("document_type"),
            "status": case.get("status"),
            "locked": bool(case.get("locked")),
            "revision": case.get("revision"),
            "ngay_lap_ho_so": case.get("ngay_lap_ho_so"),
            "noi_niem_yet": case.get("noi_niem_yet"),
            "nguoi_nhan_uy_quyen": case.get("nguoi_nhan_uy_quyen"),
            "nguoi_nhan_uy_quyen_id": case.get("nguoi_nhan_uy_quyen_id"),
            "noi_dung_viec": case.get("noi_dung_viec"),
            "ghi_chu": case.get("ghi_chu"),
        },
        "stage": stage_out,
        "diagram": {
            "domain": dg.get("domain", ct),
            "state": copy.deepcopy(dg.get("state")),
            "render_model": copy.deepcopy(dg.get("render_model")),
            "warnings": copy.deepcopy(dg.get("warnings") or []),
        },
        "capabilities": {
            "intake": list(INTAKE_KINDS) if caps else [],
            "diagram": caps,
            "word_export": ct == CASE_TYPE_INHERITANCE,
        },
    }
    if case.get("warnings"):
        data["warnings"] = copy.deepcopy(case["warnings"])
    return data


def workspace_get(job, payload):
    case = _case(payload)
    data = _workspace_data(int(payload["case_id"]), case)
    job.check_cancel()
    return _result("workspace_get", data)


_CASE_META_FIELDS = ("document_type", "ngay_lap_ho_so",
                     "noi_niem_yet", "ghi_chu", "case_type",
                     # đợt 3: meta moi trong payload.case create/commit
                     "nguoi_nhan_uy_quyen", "nguoi_nhan_uy_quyen_id",
                     "noi_dung_viec")


def _fold_canon(obj, canon, where):
    """Fold key canonical -> legacy; cùng mang mà giá trị lệch →
    validation_error (parity _fold_key_aliases)."""
    if not isinstance(obj, dict):
        return obj
    obj = dict(obj)
    for ck, lk in canon.items():
        if ck in obj:
            cv = obj.pop(ck)
            if lk in obj and obj[lk] != cv:
                raise CommandError(
                    "validation_error",
                    f"{where}: {ck} và {lk} mang giá trị mâu thuẫn")
            obj[lk] = cv
    return obj


def _apply_case_meta(case, cm, where="payload.case"):
    """Validate + ghi meta đợt 3 (parity _validate_case_meta commit path):
    case_type/document_type gửi kèm phải khớp giá trị đã lưu."""
    cm = _fold_canon(cm, CASE_META_CANON, where)
    extra = set(cm) - set(_CASE_META_FIELDS)
    if extra:
        raise CommandError("validation_error",
                           f"{where} key lạ: {sorted(extra)}")
    for f in ("case_type", "document_type"):
        v = cm.get(f)
        if v is not None and v != case.get(f):
            raise CommandError(
                "validation_error",
                f"{where}.{f}={v!r} khác giá trị đã lưu "
                f"{case.get(f)!r} (immutable)")
    nl = cm.get("ngay_lap_ho_so")
    if nl is not None and not (
            isinstance(nl, str) and DATE_FULL_RX.match(nl)):
        raise CommandError("validation_error",
                           "ngay_lap_ho_so phải YYYY-MM-DD/null")
    uq_id = cm.get("nguoi_nhan_uy_quyen_id")
    uq_name = cm.get("nguoi_nhan_uy_quyen")
    cust = None
    if uq_id is not None:
        if not (isinstance(uq_id, int) and not isinstance(uq_id, bool)
                and uq_id >= 1):
            raise CommandError(
                "validation_error",
                "nguoi_nhan_uy_quyen_id phải là int >= 1/null")
        # Parity _resolve_auth_recipient: id phai ton tai trong danh ba
        # gia; kem ten ma lech master → loi; id co → ten = master.
        cust = _state().customers.get(uq_id)
        if cust is None:
            raise CommandError(
                "validation_error",
                f"nguoi_nhan_uy_quyen_id {uq_id} không tồn tại "
                "trong danh bạ")
        if uq_name is not None and uq_name != cust.get("ho_ten"):
            raise CommandError(
                "validation_error",
                "nguoi_nhan_uy_quyen và nguoi_nhan_uy_quyen_id "
                "mâu thuẫn nhau")
        uq_name = cust.get("ho_ten")
    for f in ("noi_niem_yet", "ghi_chu", "nguoi_nhan_uy_quyen",
              "noi_dung_viec"):
        v = cm.get(f)
        if v is not None and (
                not isinstance(v, str) or not v.strip()):
            raise CommandError("validation_error",
                               f"{f} phải là chuỗi non-empty/null")
    # Real parity: payload.case là block meta đầy đủ — field vắng mặt
    # ghi None; ngay_lap_ho_so null = giữ nguyên (cột NOT NULL).
    if nl is not None:
        case["ngay_lap_ho_so"] = nl
    case["noi_niem_yet"] = cm.get("noi_niem_yet")
    case["nguoi_nhan_uy_quyen"] = uq_name
    case["nguoi_nhan_uy_quyen_id"] = cust["id"] if cust else uq_id
    case["noi_dung_viec"] = cm.get("noi_dung_viec")
    case["ghi_chu"] = cm.get("ghi_chu")


def workspace_create(job, payload):
    """notary.workspace_create mock — §4.3/§13.4: validate → tao case mot
    transaction ao (assign entity_id + seed) → revision=1. Idempotent
    theo `idempotency_key` da persist (replay tra created:false).

    diagram la TUY CHON: payload co state thi validate + render; khong
    co thi server seed (inheritance: node 'owner' = owner_row_id;
    two_party: canonical 30 slot) va render_model=null."""
    p = payload if isinstance(payload, dict) else {}
    ik = p.get("idempotency_key")
    if not (isinstance(ik, str) and UUID4_RX.match(ik)):
        raise CommandError("validation_error",
                           "idempotency_key phải là uuid4")
    st = _state()
    with st._lock:
        replay_id = st._idempotency.get(ik)
        if replay_id is not None:
            data = _workspace_data(replay_id, st.cases[replay_id])
            data["created"] = False
            return _result("workspace_create", data)

        cm = p.get("case")
        if not isinstance(cm, dict):
            raise CommandError("validation_error",
                               "payload.case phải là object")
        cm = _fold_canon(cm, CASE_META_CANON, "payload.case")
        extra = set(cm) - set(_CASE_META_FIELDS)
        if extra:
            raise CommandError(
                "validation_error",
                f"payload.case key lạ: {sorted(extra)}")
        ct = cm.get("case_type", CASE_TYPE_INHERITANCE)
        if ct not in CASE_TYPES:
            raise CommandError("validation_error",
                               f"case_type={ct!r} ngoài enum")
        dt = cm.get("document_type")
        doc_types = (DOCUMENT_TYPES if ct == CASE_TYPE_INHERITANCE
                     else DOCUMENT_TYPES_TWO_PARTY)
        if dt not in doc_types:
            raise CommandError("validation_error",
                               f"document_type={dt!r} ngoài enum "
                               f"cho {ct}")
        nl = cm.get("ngay_lap_ho_so")
        if nl is not None and not (
                isinstance(nl, str) and DATE_FULL_RX.match(nl)):
            raise CommandError("validation_error",
                               "ngay_lap_ho_so phải YYYY-MM-DD/null")
        for f in ("noi_niem_yet", "ghi_chu", "nguoi_nhan_uy_quyen",
                  "noi_dung_viec"):
            v = cm.get(f)
            if v is not None and (
                    not isinstance(v, str) or not v.strip()):
                raise CommandError(
                    "validation_error",
                    f"{f} phải là chuỗi non-empty/null")
        uq_id = cm.get("nguoi_nhan_uy_quyen_id")
        uq_name = cm.get("nguoi_nhan_uy_quyen")
        uq_cust = None
        if uq_id is not None:
            if not (isinstance(uq_id, int) and not isinstance(uq_id, bool)
                    and uq_id >= 1):
                raise CommandError(
                    "validation_error",
                    "nguoi_nhan_uy_quyen_id phải là int >= 1/null")
            # Parity _resolve_auth_recipient: id ton tai trong danh ba
            # gia; kem ten lech master → loi; id co → ten = master.
            uq_cust = st.customers.get(uq_id)
            if uq_cust is None:
                raise CommandError(
                    "validation_error",
                    f"nguoi_nhan_uy_quyen_id {uq_id} không tồn tại "
                    "trong danh bạ")
            if uq_name is not None and \
                    uq_name != uq_cust.get("ho_ten"):
                raise CommandError(
                    "validation_error",
                    "nguoi_nhan_uy_quyen và nguoi_nhan_uy_quyen_id "
                    "mâu thuẫn nhau")
            uq_name = uq_cust.get("ho_ten")

        stage = p.get("stage")
        errs, people_norm, assets_norm = _validate_stage(stage, ct)
        raw_people = stage.get("people") if isinstance(stage, dict) else []
        raw_assets = stage.get("assets") if isinstance(stage, dict) else []
        if not raw_people:
            errs.append(_err(
                _det_uuid4("field_error:people_empty"), "people",
                "required", "stage.people phải có ít nhất một dòng"))
        if not raw_assets:
            errs.append(_err(
                _det_uuid4("field_error:assets_empty"), "assets",
                "required", "stage.assets phải có ít nhất một dòng"))
        for i, r in enumerate(raw_people):
            if isinstance(r, dict) and r.get("entity_id") is not None:
                errs.append(_err(
                    _err_row(r.get("row_id"), f"people[{i}]"),
                    "entity_id", "invalid_format",
                    "entity_id phải null — workspace_create tạo entity mới"))
        for i, r in enumerate(raw_assets):
            if isinstance(r, dict) and r.get("entity_id") is not None:
                errs.append(_err(
                    _err_row(r.get("row_id"), f"assets[{i}]"),
                    "entity_id", "invalid_format",
                    "entity_id phải null — workspace_create tạo entity mới"))
        if errs:
            raise CommandError("stage_validation_error",
                               f"{len(errs)} lỗi field trong Stage",
                               details={"field_errors": errs})

        dg = p.get("diagram")
        provided_state = None
        if dg is not None:
            if not isinstance(dg, dict) or set(dg) != {"state"}:
                raise CommandError(
                    "validation_error",
                    "payload.diagram chỉ chứa 'state'")
            provided_state = dg.get("state")
        stage_ids = {r["row_id"] for r in people_norm}
        if provided_state is not None:
            errors = _validate_diagram_state(provided_state)
            if errors:
                raise CommandError("diagram_invalid_state",
                                   "diagram state không hợp lệ",
                                   details={"errors": errors})
            if provided_state["domain"] != ct:
                raise CommandError(
                    "diagram_domain_mismatch",
                    "state.domain không khớp case.case_type",
                    details={"expected": ct,
                             "got": provided_state["domain"]})
            outside_pid = _outside_person(provided_state, stage_ids)
            if outside_pid is not None:
                raise CommandError(
                    "diagram_reference_outside_stage",
                    f"personId {outside_pid} không thuộc Stage của "
                    "payload", details={"personId": outside_pid})
            if ct == CASE_TYPE_INHERITANCE:
                oid = stage.get("owner_row_id")
                owner_pid = next(
                    (n.get("personId") for n in provided_state["nodes"]
                     if isinstance(n, dict) and n.get("id") == "owner"
                     and n.get("deleted") is not True
                     and n.get("personId") is not None), None)
                if owner_pid is not None and owner_pid != oid:
                    raise CommandError(
                        "diagram_owner_mismatch",
                        "node owner.personId phải khớp "
                        "stage.owner_row_id",
                        details={"owner_row_id": oid,
                                 "node_personId": owner_pid})

        for row in people_norm + assets_norm:
            row["entity_id"] = st.assign_entity_id()
        if provided_state is not None:
            state = _persisted_diagram_state(provided_state)
            render_model = (_unsupported_render()
                            if ct == CASE_TYPE_TWO_PARTY
                            else _render(
                                state, {"people": people_norm,
                                        "assets": assets_norm}))
        elif ct == CASE_TYPE_TWO_PARTY:
            state = {"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_TWO_PARTY,
                     "nodes": _canonical_two_party([])}
            render_model = None
        else:
            state = {"version": DIAGRAM_STATE_VERSION,
                     "domain": CASE_TYPE_INHERITANCE,
                     "nodes": [{
                         "id": "owner",
                         "personId": stage.get("owner_row_id"),
                         "parentSlotIds": [], "spouseSlotId": None,
                         "ownPositions": [], "receivePositions": [],
                         "hidden": False, "deleted": False}]}
            render_model = None
        new_id = (max(st.cases) + 1) if st.cases else 1
        stage_store = {"people": people_norm, "assets": assets_norm}
        if ct == CASE_TYPE_INHERITANCE:
            stage_store["owner_row_id"] = stage.get("owner_row_id")
        case = {
            "id": new_id,
            "case_type": ct,
            "document_type": dt,
            "status": "draft",
            "locked": False,
            "revision": 1,
            "ngay_lap_ho_so": nl,
            "noi_niem_yet": cm.get("noi_niem_yet"),
            "nguoi_nhan_uy_quyen": uq_name,
            "nguoi_nhan_uy_quyen_id": uq_cust["id"] if uq_cust else uq_id,
            "noi_dung_viec": cm.get("noi_dung_viec"),
            "ghi_chu": cm.get("ghi_chu"),
            "stage": stage_store,
            "diagram": {
                "domain": ct,
                "state": state,
                "render_model": render_model,
                "warnings": [],
            },
        }
        st.cases[new_id] = case
        st._idempotency[ik] = new_id
        data = _workspace_data(new_id, case)
        data["created"] = True
        job.check_cancel()
        return _result("workspace_create", data)


def intake_analyze(job, payload):
    # case_id absent = che do nhap (§2.1a) — bo qua kiem tra case.
    if "case_id" in (payload or {}):
        case = _case(payload)
        # Real intake_analyze: case_type TRUOC locked (adapter §13.5).
        _check_supported(case)
        if case.get("locked"):
            raise CommandError("workspace_locked",
                               f"hồ sơ #{case['id']} đã khóa")
    sources = (payload or {}).get("sources")
    if not isinstance(sources, list) or not sources:
        raise CommandError("validation_error", "sources phải là list 1..8")
    if len(sources) > MAX_SOURCES:
        raise CommandError("intake_too_many_sources",
                           f"{len(sources)} nguồn > {MAX_SOURCES}",
                           details={"count": len(sources),
                                    "limit": MAX_SOURCES})
    seen = set()
    for s in sources:
        if not isinstance(s, dict):
            raise CommandError("validation_error", "source không phải object")
        sid = s.get("source_id")
        if not (isinstance(sid, str) and UUID4_RX.match(sid)):
            raise CommandError("validation_error",
                               f"source_id={sid!r} phải là uuid4")
        if sid in seen:
            raise CommandError("validation_error",
                               f"source_id trùng: {sid}")
        seen.add(sid)
        kind = s.get("kind")
        if kind not in INTAKE_KINDS:
            raise CommandError("intake_unsupported_source",
                               f"kind={kind!r} ngoài enum",
                               details={"source_id": sid, "kind": kind})
        if kind == "text":
            if "file_ref" in s:
                raise CommandError("validation_error",
                                   "kind=text cấm file_ref")
            t = s.get("text")
            if not isinstance(t, str) or not t:
                raise CommandError("validation_error",
                                   "kind=text bắt buộc text non-empty")
            if len(t) > MAX_TEXT_CHARS:
                raise CommandError("intake_text_too_long",
                                   f"text {len(t)} > {MAX_TEXT_CHARS}",
                                   details={"source_id": sid,
                                            "length": len(t),
                                            "limit": MAX_TEXT_CHARS})
        else:
            if "text" in s:
                raise CommandError("validation_error",
                                   f"kind={kind} cấm text")
            ref = s.get("file_ref")
            if not isinstance(ref, dict):
                raise CommandError("validation_error",
                                   f"kind={kind} bắt buộc file_ref")
            if ref.get("is_dir") is True:
                raise CommandError("validation_error",
                                   "intake file_ref is_dir=true")
            sb = ref.get("size_bytes")
            if not isinstance(sb, int) or isinstance(sb, bool) or sb < 0:
                raise CommandError("validation_error",
                                   "intake file_ref bắt buộc size_bytes "
                                   "int >= 0")
            if sb > MAX_FILE_BYTES:
                raise CommandError("intake_source_too_large",
                                   f"size_bytes={sb} > {MAX_FILE_BYTES}",
                                   details={"source_id": sid,
                                            "limit": MAX_FILE_BYTES})
    suggestions = []
    errors = []
    ok_ids = []
    bad_ids = []
    for i, s in enumerate(sources):
        job.check_cancel()
        job.report_progress(i, len(sources),
                            f"nguồn {i + 1}/{len(sources)}")
        sid = s["source_id"]
        blob = s.get("text") if s["kind"] == "text" else (
            (s.get("file_ref") or {}).get("path") or "")
        low = str(blob).lower()
        if _FAIL_MARK in low:
            errors.append({"source_id": sid, "code": "intake.parse_failed",
                           "message": "Không trích được thực thể nào "
                                      "(mô phỏng)"})
            bad_ids.append(sid)
            continue
        if _UNSUPPORTED_MARK in low:
            errors.append({"source_id": sid,
                           "code": "intake.unsupported_target",
                           "message": "Loại nguồn không map được "
                                      "(mô phỏng)"})
            bad_ids.append(sid)
            continue
        suggestions.append(_canned_suggestion(s))
        ok_ids.append(sid)
    job.report_progress(len(sources), len(sources), "Hoàn tất")
    data = {"schema_version": SCHEMA_VERSION,
            "suggestions": suggestions, "errors": errors}
    partial = bool(errors)
    if partial:
        data["breakdown"] = {"succeeded": ok_ids, "failed": bad_ids}
    src_files = [{"path": s["file_ref"]["path"], "scope": "machine_local"}
                 for s in sources
                 if s["kind"] != "text" and isinstance(s.get("file_ref"), dict)
                 and isinstance(s["file_ref"].get("path"), str)]
    return _result("intake_analyze", data, source_files=src_files,
                   partial=partial)


def _canned_suggestion(src):
    """Suggestion fixture bat bien theo kind — observation_state hop le,
    khong bao gio 'confirmed'."""
    sid = src["source_id"]
    if src["kind"] in ("text", "image"):
        ref = {"span": [0, 10]} if src["kind"] == "text" else {"page": 1}
        fields = {
            "ho_ten": {"raw_value": "NGƯỜI MẪU I",
                       "normalized_value": "Người Mẫu I",
                       "observation_state": "normalized",
                       "confidence": None, "source_refs": [ref]},
            "ngay_sinh": {"raw_value": "1950",
                          "normalized_value": "1950",
                          "observation_state": "normalized",
                          "confidence": None, "source_refs": [ref]},
            "gioi_tinh": {"raw_value": "Nam",
                          "normalized_value": "Nam",
                          "observation_state": "observed",
                          "confidence": None, "source_refs": [ref]},
        }
        target = "person"
    else:
        ref = {"page": 1}
        fields = {
            "so_serial": {"raw_value": "MM 000010",
                          "normalized_value": "MM000010",
                          "observation_state": "inferred",
                          "confidence": 0.62, "source_refs": [ref]},
            "dia_chi": {"raw_value": "Địa chỉ mẫu intake",
                        "normalized_value": None,
                        "observation_state": "observed",
                        "confidence": None, "source_refs": [ref]},
            "so_thua_dat": {"raw_value": "123",
                            "normalized_value": "123",
                            "observation_state": "normalized",
                            "confidence": None,
                            "source_refs": [{"page": 2}]},
        }
        target = "asset"
    return {"suggestion_id": _det_uuid4(sid + ":" + src["kind"]),
            "source_id": sid, "target": target, "fields": fields,
            "warnings": []}


def workspace_commit_stage(job, payload):
    case = _case(payload)
    _check_writable(case)
    _check_base_revision(case, payload)
    ct = case["case_type"]
    # đợt 3: payload.case optional — meta ghi cùng transaction (validate
    # trước stage để fail kịch bản nào cũng không ghi — parity real).
    case_meta = (payload or {}).get("case")
    if case_meta is not None:
        if not isinstance(case_meta, dict):
            raise CommandError("validation_error",
                               "payload.case phải là object")
        _apply_case_meta(case, case_meta)
    stage = (payload or {}).get("stage")
    errs, people_norm, assets_norm = _validate_stage(stage, ct)
    if errs:
        raise CommandError("stage_validation_error",
                           f"{len(errs)} lỗi field trong Stage",
                           details={"field_errors": errs})
    # Atomic: assign entity_id + swap stage + prune + re-evaluate + rev+1
    for row in people_norm + assets_norm:
        if row.get("entity_id") is None:
            row["entity_id"] = _state().assign_entity_id()
    case["stage"] = {"people": people_norm, "assets": assets_norm}
    if ct == CASE_TYPE_INHERITANCE:
        case["stage"]["owner_row_id"] = stage.get("owner_row_id")
    pruned = _prune_diagram(case)
    case["diagram"]["render_model"] = (
        _unsupported_render() if ct == CASE_TYPE_TWO_PARTY
        else _render(case["diagram"]["state"], case["stage"]))
    case["revision"] += 1
    job.check_cancel()
    diagram_out = {
        "state": copy.deepcopy(case["diagram"]["state"]),
        "render_model": copy.deepcopy(
            case["diagram"]["render_model"]),
    }
    if pruned:
        diagram_out["warnings"] = [{
            "code": "diagram.selection_pruned",
            "message": "Các lựa chọn vị trí vượt số tài sản đã bị bỏ"}]
    return _result("workspace_commit_stage", {
        "schema_version": SCHEMA_VERSION,
        "revision": case["revision"],
        "stage": copy.deepcopy(case["stage"]),
        "diagram": diagram_out,
    })


def diagram_evaluate(job, payload):
    """Read-only — duoc phep tren case locked (§7.4); khong persist.

    case_id absent = che do nhap: stage payload thay Stage DB,
    evaluated_revision=null. case_id + stage cung luc -> validation_error
    (adapter parity). two_party -> render_model unsupported."""
    p = payload if isinstance(payload, dict) else {}
    if "case_id" in p and "stage" in p:
        raise CommandError("validation_error",
                           "payload.stage chỉ dùng khi không có case_id")
    state = _payload_diagram_state(p)
    if "case_id" not in p:
        case_hint = p.get("case")
        if case_hint is not None and not isinstance(case_hint, dict):
            raise CommandError("validation_error",
                               "payload.case phải là object/null")
        ct = (case_hint or {}).get("case_type", CASE_TYPE_INHERITANCE)
        if not isinstance(ct, str):
            ct = CASE_TYPE_INHERITANCE
        # ct tuy y: _check_domain bat domain-hop-le != ct truoc
        # (real evaluate_draft parity) — khong pre-check enum.
        stage = p.get("stage")
        # Thu tu real evaluate_draft: domain -> wire -> owner pointer +
        # stage field errors -> person refs -> render.
        _check_domain(state, ct)
        errors = _validate_diagram_state(state)
        if errors:
            raise CommandError("diagram_invalid_state",
                               "diagram state không hợp lệ",
                               details={"errors": errors})
        errs, people_norm, assets_norm = _validate_stage(stage, ct)
        if errs:
            raise CommandError("stage_validation_error",
                               f"{len(errs)} lỗi field trong Stage",
                               details={"field_errors": errs})
        _check_person_refs(state, {r["row_id"] for r in people_norm})
        rm = (_unsupported_render() if ct == CASE_TYPE_TWO_PARTY
              else _render(state, {"people": people_norm,
                                   "assets": assets_norm}))
        job.check_cancel()
        return _result("diagram_evaluate", {
            "schema_version": SCHEMA_VERSION,
            "evaluated_revision": None,
            "render_model": rm,
        })
    case = _case(p)
    _check_supported(case)
    rm = _evaluate_state_or_raise(case, state)
    job.check_cancel()
    return _result("diagram_evaluate", {
        "schema_version": SCHEMA_VERSION,
        "evaluated_revision": case["revision"],
        "render_model": rm,
    })


def diagram_save(job, payload):
    """Thu tu real save_diagram: domain -> wire -> owner mirror ->
    person refs -> prune positions -> persist + render -> revision+1."""
    case = _case(payload)
    _check_writable(case)
    _check_base_revision(case, payload)
    state = _payload_diagram_state(payload)
    _validate_case_state(case, state)
    _check_owner_node(case, state)
    _check_person_refs(state, set(_person_map(case)))
    ct = case["case_type"]
    clean_state = _persisted_diagram_state(state)
    warnings = []
    if ct == CASE_TYPE_INHERITANCE:
        pruned = False
        allowed = list(range(1, len(case["stage"]["assets"]) + 1))
        for n in clean_state["nodes"]:
            for k in ("ownPositions", "receivePositions"):
                arr = n.get(k) or []
                pruned = pruned or any(x not in allowed for x in arr)
                n[k] = [x for x in arr if x in allowed]
        if pruned:
            warnings.append({
                "code": "diagram.selection_pruned",
                "message": "Các lựa chọn vị trí vượt số tài sản đã bị bỏ"})
        rm = _render(clean_state, case["stage"])
    else:
        rm = _unsupported_render()
    case["diagram"]["state"] = clean_state
    case["diagram"]["render_model"] = rm
    case["revision"] += 1
    job.check_cancel()
    diagram_out = {
        "state": copy.deepcopy(clean_state),
        "render_model": copy.deepcopy(rm),
    }
    if warnings:
        diagram_out["warnings"] = warnings
    return _result("diagram_save", {
        "schema_version": SCHEMA_VERSION,
        "revision": case["revision"],
        "diagram": diagram_out,
    })


def _word_block_reason(case, document_key):
    """Readiness theo validation that (contract §8.1 mapping) — chi duoc
    goi cho inheritance (caller reject two_party)."""
    if document_key in NO_TEMPLATE_KEYS:
        return "word.template_missing"
    assets = case["stage"]["assets"]
    nodes = [n for n in (case["diagram"].get("state") or {}).get("nodes")
             or [] if isinstance(n, dict) and not n.get("deleted")]
    if not assets:
        return "word.no_assets"
    if len(assets) > 5:
        return "word.too_many_assets"
    stage_people = _person_map(case)
    landowners = [n for n in nodes
                  if n.get("ownPositions") and n.get("personId")]
    if not landowners:
        return "word.no_landowner"
    deceased = [n for n in landowners
                if (stage_people.get(n["personId"]) or {}).get("ngay_chet")]
    if not deceased:
        return "word.no_deceased_landowner"
    receivers = [n for n in nodes
                 if n.get("receivePositions") and n.get("personId")]
    if not receivers:
        return "word.no_receiver"
    assigned = [n for n in nodes if n.get("personId")]
    if len(assigned) > 20:
        return "word.too_many_people"
    # signers = living landowners + receivers, dedupe personId — parity
    # voi word_engine.word_block_reason (real, MIN-110 review).
    living_landowners = [n for n in landowners if n not in deceased]
    signer_ids = {n["personId"]
                  for n in [*living_landowners, *receivers]
                  if n.get("personId")}
    if len(signer_ids) > 20:
        return "word.too_many_signers"
    return None


def word_export_options(job, payload):
    """Read-only — duoc phep tren locked (chi workspace_get quyet dinh
    capability); block_reason theo validation that. two_party ->
    case_type_unsupported (§13.8)."""
    case = _case(payload)
    if case.get("case_type") == CASE_TYPE_TWO_PARTY:
        raise CommandError("case_type_unsupported",
                           "Word export chưa hỗ trợ loại việc two_party",
                           details={"case_type": case.get("case_type")})
    docs = []
    for key, meta in DOC_CATALOG.items():
        reason = _word_block_reason(case, key)
        docs.append({"document_key": key,
                     "display_name": meta["display_name"],
                     "ready": reason is None,
                     "block_reason": reason})
    job.check_cancel()
    return _result("word_export_options",
                   {"schema_version": SCHEMA_VERSION, "documents": docs})


def _write_docx(out, title, case):
    """Tao DOCX that bang python-docx; fallback zip toi thieu hop le.
    `out` la file object mo san mode wb (exclusive create)."""
    try:
        import docx
        d = docx.Document()
        d.add_heading(title, level=1)
        d.add_paragraph(
            f"Dữ liệu mô phỏng — hồ sơ #{case['id']} "
            f"(notary.case-drafting.v2 mock).")
        d.add_paragraph("Nội dung mẫu, không phải văn bản pháp lý.")
        d.save(out)
        return
    except ImportError:
        pass
    # Fallback: docx toi thieu hop le (zip + 2 part bat buoc)
    import zipfile
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types"><Default Extension="rels" ContentType="application/'
        'vnd.openxmlformats-package.relationships+xml"/><Default '
        'Extension="xml" ContentType="application/xml"/><Override '
        'PartName="/word/document.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.document.main'
        '+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Dữ liệu mô '
        'phỏng — mock notary.case-drafting.v2</w:t></w:r></w:p></w:body>'
        '</w:document>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)


def _reserve_and_write(dest_dir, stem, case_id, taken, title, case):
    """Naming <stem>_HS-<id>[_n].docx (n>=2) + ghi file bang
    open('xb') exclusive-create: ten trong `taken` + ten da ton tai deu
    bo qua — KHONG BAO GIO ghi de (§8.3) va khong TOCTOU giua
    exists-check va write. Tra actual_filename."""
    base = f"{stem}_HS-{case_id}"
    n = 1
    while True:
        suffix = "" if n == 1 else f"_{n}"
        name = f"{base}{suffix}.docx"
        n += 1
        if name in taken:
            continue
        path = dest_dir / name
        try:
            fh = open(path, "xb")          # exclusive create — atomic
        except FileExistsError:
            continue
        taken.add(name)
        try:
            _write_docx(fh, title, case)
            fh.close()
        except Exception:
            try:
                fh.close()
            finally:
                try:
                    path.unlink()          # khong de file hong lai
                except OSError:
                    pass
            raise
        return name


def word_export_batch(job, payload):
    case = _case(payload)
    # real parity _word_case: two_party -> case_type_unsupported TRUOC
    # locked check.
    if case.get("case_type") == CASE_TYPE_TWO_PARTY:
        raise CommandError("case_type_unsupported",
                           "Word export chưa hỗ trợ loại việc two_party",
                           details={"case_type": case.get("case_type")})
    _check_writable(case)
    keys = (payload or {}).get("document_keys")
    # Oracle parity: thieu/null/khong list -> validation_error;
    # word_no_documents_selected CHI cho list rong [].
    if not isinstance(keys, list):
        raise CommandError("validation_error",
                           "document_keys phải là list")
    if not keys:
        raise CommandError("word_no_documents_selected",
                           "document_keys rỗng")
    if len(keys) != len(set(keys)):
        dup = next(k for k in keys if keys.count(k) > 1)
        raise CommandError("word_duplicate_document_key",
                           f"document_key lặp: {dup}",
                           details={"document_key": dup})
    for k in keys:
        if not (isinstance(k, str) and DOC_KEY_RX.match(k)) \
                or k not in DOC_CATALOG:
            raise CommandError("word_unknown_document_key",
                               f"document_key ngoài catalog: {k!r}",
                               details={"document_key": k})
    dest = (payload or {}).get("destination")
    if not isinstance(dest, dict) or dest.get("is_dir") is not True:
        raise CommandError("validation_error",
                           "destination phải là file_ref is_dir:true")
    dest_dir = validate_file_ref(dest)      # scope/UNC/abs — envelope §6
    if not dest_dir.is_dir():
        raise CommandError("file_not_found",
                           "destination không phải thư mục đang tồn tại")
    docs = []
    taken = set()
    failed = []
    saved = []

    def _pending_result():
        """Snapshot result: doc chua bat dau -> skipped — canceled job
        van mang breakdown.skipped len wire (MIN-115, §8.4 fixture)."""
        entries = list(docs)
        remaining = keys[len(entries):]
        for key in remaining:
            meta = DOC_CATALOG[key]
            entries.append({"document_key": key,
                            "display_name": meta["display_name"],
                            "status": "skipped", "actual_filename": None,
                            "output_file": None, "error": None})
        return _result(
            "word_export_batch",
            {"schema_version": SCHEMA_VERSION,
             "destination": {"path": str(dest_dir),
                             "scope": "machine_local", "is_dir": True},
             "documents": entries,
             "breakdown": {"succeeded": list(saved),
                           "failed": list(failed),
                           "skipped": list(remaining)}})

    # MIN-116 parity engine that: probe writability destination mot lan
    # dau batch bang file tao/xoa that (os.access tren Windows misreport
    # ACL deny-write) — deny thi MOI doc nhan cung per-file error, job
    # ket thuc ngay, khong hang. Thu tu: cancel -> probe -> loop.
    job.check_cancel(_pending_result())          # cancel truoc khi probe
    dest_error = None
    try:
        probe = dest_dir / f".word_export_probe_{uuid.uuid4().hex}.tmp"
        with open(probe, "xb"):
            pass
    except FileNotFoundError as exc:
        dest_error = ("file_not_found",
                      f"destination không còn tồn tại: {exc}")
    except PermissionError as exc:
        dest_error = ("file_locked",
                      f"destination không ghi được: {exc}")
    except OSError as exc:
        dest_error = ("word.render_failed",
                      f"destination không tạo được file: {exc}")
    else:
        try:
            probe.unlink()      # parity real: unlink OSError nuot, khong
        except OSError:         # lam fail batch (create-ok/delete-deny ACL)
            pass

    for i, key in enumerate(keys):
        job.check_cancel(_pending_result())  # cancel giua batch
        meta = DOC_CATALOG[key]
        if dest_error is not None:
            docs.append({"document_key": key,
                         "display_name": meta["display_name"],
                         "status": "failed", "actual_filename": None,
                         "output_file": None,
                         "error": {"code": dest_error[0],
                                   "message": dest_error[1]}})
            failed.append(key)
            job.report_progress(i + 1, len(keys),
                                f"văn bản {i + 1}/{len(keys)}")
            continue
        reason = _word_block_reason(case, key)
        if reason is not None:
            docs.append({"document_key": key,
                         "display_name": meta["display_name"],
                         "status": "failed", "actual_filename": None,
                         "output_file": None,
                         "error": {"code": reason,
                                   "message": _block_message(reason)}})
            failed.append(key)
        else:
            time.sleep(WORD_DOC_DELAY)       # mo phong render docx
            job.check_cancel(_pending_result())  # truoc khi ghi file
            try:
                name = _reserve_and_write(
                    dest_dir, meta["filename_stem"],
                    int(payload["case_id"]), taken,
                    meta["display_name"], {"id": payload["case_id"]})
            except OSError as exc:
                # Parity engine that (MIN-116): OSError o write path ->
                # per-doc error theo _doc_error_from (file_not_found /
                # file_locked / word.render_failed); all-failed ->
                # word_batch_failed kem result_data.
                if isinstance(exc, FileNotFoundError):
                    code = "file_not_found"
                elif isinstance(exc, PermissionError):
                    code = "file_locked"
                else:
                    code = "word.render_failed"
                docs.append({"document_key": key,
                             "display_name": meta["display_name"],
                             "status": "failed", "actual_filename": None,
                             "output_file": None,
                             "error": {"code": code,
                                       "message": f"không ghi được file: {exc}"}})
                failed.append(key)
            else:
                out_path = dest_dir / name
                docs.append({"document_key": key,
                             "display_name": meta["display_name"],
                             "status": "saved", "actual_filename": name,
                             "output_file": {"path": str(out_path),
                                             "scope": "machine_local"},
                             "error": None})
                saved.append(key)
        job.report_progress(i + 1, len(keys),
                            f"văn bản {i + 1}/{len(keys)}")
    breakdown = {"succeeded": saved, "failed": failed, "skipped": []}
    data = {"schema_version": SCHEMA_VERSION,
            "destination": {"path": str(dest_dir), "scope": "machine_local",
                            "is_dir": True},
            "documents": docs, "breakdown": breakdown}
    if len(failed) == len(keys):
        raise CommandError(                  # all failed -> job failed §8.4
            "word_batch_failed",
            "Toàn bộ văn bản trong lượt xuất đều lỗi",
            retryable=True, next_action="retry",
            details={"documents": [
                {"document_key": d["document_key"],
                 "code": d["error"]["code"],
                 "message": d["error"]["message"]} for d in docs]},
            # result van len wire: breakdown.failed per-file (fixture
            # job.word-export-batch-all-failed; MIN-115 mechanism).
            result=_result("word_export_batch", data))
    return _result("word_export_batch", data, partial=bool(failed))


def _block_message(code):
    return {
        "word.no_assets": "Hồ sơ chưa có tài sản",
        "word.no_landowner": "Chưa có chủ đất trên Diagram",
        "word.no_deceased_landowner": "Không có chủ đất đã chết",
        "word.no_receiver": "Chưa có người nhận",
        "word.too_many_assets": "Quá 5 tài sản",
        "word.too_many_people": "Quá 20 người trên Diagram",
        "word.too_many_signers": "Quá 20 người ký",
        "word.template_missing": "Văn bản chưa có template",
    }.get(code, code)
