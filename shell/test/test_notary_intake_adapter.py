"""Integration test: notary.intake_analyze qua engine that (MIN-108).

Chay: python test/test_notary_intake_adapter.py
Can shell/engine-roots.json tro toi engine roots tren may nay; thieu thi skip.
Text/xlsx/pdf path khong can OCR API key — image OCR path van duoc kiem chung
bang per-source ocr.engine_unavailable khi thieu key.

Kiem tra bo sung: result.data chay qua contract validator
(contracts/notary-case-drafting/validate_examples.py) khi repo root co san.
"""
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
_REPO = _SHELL.parent
sys.path.insert(0, str(_SHELL / "sidecar"))

from jobstore import Job  # noqa: E402
import command_registry as reg  # noqa: E402
from errors import CommandError  # noqa: E402
import engine_roots  # noqa: E402

_VALIDATOR = _REPO / "contracts" / "notary-case-drafting" / "validate_examples.py"


def _run(command, payload=None):
    job = Job("cmd_test_" + command.replace(".", "_"), command)
    job.status = "running"
    return reg.COMMANDS[command](job, payload or {})


def _engines_available():
    try:
        engine_roots.engine_root("notary_v2")
        return True
    except CommandError:
        return False


def _sid(n):
    return f"00000000-0000-4000-8000-{n:012d}"


def _text_source(n, text):
    return {"source_id": _sid(n), "kind": "text", "text": text}


def _file_source(n, kind, path, size=None):
    return {
        "source_id": _sid(n),
        "kind": kind,
        "file_ref": {
            "path": str(path),
            "scope": "machine_local",
            "size_bytes": Path(path).stat().st_size if size is None else size,
        },
    }


PROPERTY_LINES = [
    "GIẤY CHỨNG NHẬN",
    "QUYỀN SỬ DỤNG ĐẤT",
    "Số phát hành (serial): DD 123456",
    "Số vào sổ: VP00166",
    "Thửa đất số: 10",
    "Tờ bản đồ số: 5",
    "Diện tích: 447,0 m2",
    "Địa chỉ: Thôn A, Xã B, Huyện C, Tỉnh D",
    "Ngày cấp: 20/05/2010",
]


def _walk_strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def _make_case():
    """Fixture case that: customer + property + case → case_id."""
    tag = uuid.uuid4().hex[:6].upper()
    cust = _run("notary.customer_create", {
        "ho_ten": "Nguyen Van Intake " + tag,
        "so_giay_to": "00999" + tag.replace("0", "7")[:7],
        "ngay_sinh": "1955-02-02", "ngay_chet": "2024-01-15",
        "dia_chi": "xa intake test"})
    prop = _run("notary.property_create", {
        "so_serial": f"INT-{tag}", "dia_chi": "thon intake, xa test",
        "so_thua_dat": "100", "so_to_ban_do": "20"})
    case = _run("notary.case_create", {
        "nguoi_chet_id": cust["data"]["customer"]["id"],
        "tai_san_id": prop["data"]["property"]["id"],
        "loai_van_ban": "khai_nhan", "noi_niem_yet": "xa test"})
    return case["data"]["case"]["id"]


def _contract_violations(result, status):
    """Chay result qua contract validator khi repo root co contracts/."""
    if not _VALIDATOR.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_examples", str(_VALIDATOR))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    doc = {
        "contract_version": "desktopcommand.v1",
        "job_id": "j_test",
        "command_id": str(uuid.uuid4()),
        "command": "notary.intake_analyze",
        "status": status,
        "waiting_on": None,
        "payload": {"case_id": 1, "sources": [
            _text_source(9, "placeholder"),
        ]},
        "result": result,
        "error": None,
        "updated_at": "2026-09-24T09:45:00Z",
    }
    return mod.violations(doc)


@unittest.skipUnless(_engines_available(), "chua cau hinh engine-roots.json")
class TestIntakeAnalyze(unittest.TestCase):
    """MIN-108: sidecar → document_intake service → contract suggestions."""

    @classmethod
    def setUpClass(cls):
        cls.case_id = _make_case()

    def _analyze(self, sources):
        return _run("notary.intake_analyze", {
            "case_id": self.case_id, "sources": sources})

    def test_text_source_succeeded_contract_shape(self):
        res = self._analyze([_text_source(1, "\n".join(PROPERTY_LINES))])
        self.assertEqual(res["kind"], "intake_analyze")
        data = res["data"]
        self.assertEqual(data["schema_version"], "notary.case-drafting.v1")
        self.assertFalse(res.get("partial"))
        sugs = data["suggestions"]
        self.assertEqual(len(sugs), 1)
        sug = sugs[0]
        self.assertEqual(sug["source_id"], _sid(1))
        self.assertEqual(sug["target"], "asset")
        uuid.UUID(sug["suggestion_id"])
        self.assertEqual(
            sug["fields"]["so_serial"]["normalized_value"], "DD123456")
        self.assertIn(
            sug["fields"]["so_serial"]["observation_state"],
            ("observed", "normalized", "inferred"))
        # Khong bao gio co `confirmed` o bat ky cap nao.
        self.assertNotIn("confirmed", list(_walk_strings(res)))

    def test_partial_breakdown_on_missing_file(self):
        res = self._analyze([
            _file_source(1, "pdf", "D:/nonexistent_xyz_108/a.pdf", size=5),
            _text_source(2, "\n".join(PROPERTY_LINES)),
        ])
        self.assertTrue(res.get("partial"))
        data = res["data"]
        self.assertEqual(data["breakdown"]["failed"], [_sid(1)])
        self.assertEqual(data["breakdown"]["succeeded"], [_sid(2)])
        self.assertEqual(data["errors"][0]["code"], "file_not_found")
        self.assertEqual(set(data["errors"][0]),
                         {"source_id", "code", "message"})

    def test_xlsx_file_source_person_rows(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl khong co trong interpreter sidecar")
        with tempfile.TemporaryDirectory() as td:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "DanhSach"
            ws.append(["Họ tên", "Giới tính", "Ngày sinh", "Số giấy tờ"])
            ws.append(["NGUYỄN VĂN A", "Nam", "1988", "111 222 333 444"])
            f = Path(td) / "people.xlsx"
            wb.save(str(f))
            res = self._analyze([_file_source(1, "xlsx", str(f))])
        self.assertFalse(res.get("partial"))
        sug = res["data"]["suggestions"][0]
        self.assertEqual(sug["target"], "person")
        ref = sug["fields"]["ho_ten"]["source_refs"][0]
        self.assertEqual(ref["sheet"], "DanhSach")
        self.assertEqual(ref["cell"], "A2")

    def test_validation_errors_structured(self):
        with self.assertRaises(CommandError) as ctx:
            _run("notary.intake_analyze",
                 {"case_id": self.case_id, "sources": [_text_source(1, "x")],
                  "bogus": 1})
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx:
            _run("notary.intake_analyze", {"sources": [_text_source(1, "x")]})
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx:
            _run("notary.intake_analyze",
                 {"case_id": 0, "sources": [_text_source(1, "x")]})
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx:
            self._analyze([{"source_id": "not-a-uuid", "kind": "text",
                            "text": "x"}])
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx:
            self._analyze([_text_source(1, "x"), _text_source(1, "y")])
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx:
            self._analyze([{"source_id": _sid(1), "kind": "zip",
                            "text": "x"}])
        self.assertEqual(ctx.exception.code, "intake_unsupported_source")
        with self.assertRaises(CommandError) as ctx:
            self._analyze([_text_source(i, "x") for i in range(1, 10)])
        self.assertEqual(ctx.exception.code, "intake_too_many_sources")
        with self.assertRaises(CommandError) as ctx:
            _run("notary.intake_analyze",
                 {"case_id": 999999999,
                  "sources": [_text_source(1, "x")]})
        self.assertEqual(ctx.exception.code, "case_not_found")

    def test_result_passes_contract_validator(self):
        viols = _contract_violations(
            self._analyze([
                _file_source(1, "pdf", "D:/nonexistent_xyz_108/a.pdf", size=5),
                _text_source(2, "\n".join(PROPERTY_LINES)),
            ]), "partial")
        if viols is None:
            self.skipTest("khong co contracts/ validator trong repo root")
        self.assertEqual(viols, [])


class TestRegistryWiring(unittest.TestCase):
    def test_intake_command_registered(self):
        self.assertIn("notary.intake_analyze", reg.COMMANDS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
