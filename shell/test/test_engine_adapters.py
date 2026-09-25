"""Integration test: cac command P6 goi engine that (notary_v2/upload_lab).

Chay: python test/test_engine_adapters.py
Can shell/engine-roots.json tro toi engine roots tren may nay; thieu thi skip.
Khong dung OCR/browser session trong unit test nay (can API key/Chromium) —
2 luong do duoc kiem chung qua smoke tay trong app Electron.

MIN-69 T9 — test KHONG duoc ghi vao data that:
  - Notary: G1_NOTARY_DATA_DIR → tempdir (notary_adapter._ensure_db rebind
    notary.db sang data dir) + G1_OUTPUT_DIR → tempdir; test khong bao gio
    tao record trong notary.db that hay xuat docx vao output that.
  - Upload: G1_UPLOAD_DATA_DIR → tempdir (workspace.sqlite3 +
    websites/<id>/registry.sqlite3 deu duoi do); DOCX/Excel fixture do test
    tu tao — khong phu thuoc upload_lab/downloads/.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SHELL = _HERE.parent
sys.path.insert(0, str(_SHELL / "sidecar"))

from jobstore import Job  # noqa: E402
import command_registry as reg  # noqa: E402
from errors import CommandError  # noqa: E402
import engine_roots  # noqa: E402

_WF = "upload.workflow.v1"


def _write_docx(path: Path, lines):
    """Tao file .docx that (python-docx) cho scan fixture."""
    import docx
    d = docx.Document()
    for line in lines:
        d.add_paragraph(line)
    d.save(str(path))


def _write_xlsx(path: Path, rows):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(list(r))
    wb.save(str(path))


def _run(command, payload=None):
    job = Job("cmd_test_" + command.replace(".", "_"), command)
    job.status = "running"
    return reg.COMMANDS[command](job, payload or {})


def _engines_available():
    try:
        engine_roots.engine_root("notary_v2")
        engine_roots.engine_root("upload_lab")
        return True
    except CommandError:
        return False


@unittest.skipUnless(_engines_available(),
                     "chua cau hinh engine-roots.json")
class TestNotaryAdapter(unittest.TestCase):
    """MIN-68: case/customer/property/participant/Word/Zalo qua engine that.

    DB that tuyet doi khong bi ghi: setUpClass tro G1_NOTARY_DATA_DIR ve
    tempdir → notary_adapter rebind notary.db sang do (khong sua engine)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="g1-notary-test-")
        import os
        os.environ["G1_NOTARY_DATA_DIR"] = cls._tmp.name
        # Word export/output cung khong duoc roi vao output that.
        cls._out = tempfile.TemporaryDirectory(prefix="g1-output-test-")
        os.environ["G1_OUTPUT_DIR"] = cls._out.name

    @classmethod
    def tearDownClass(cls):
        # Nha handle sqlite (Windows khong cho xoa file dang mo).
        try:
            database = engine_roots.import_engine_module(
                "notary_v2", "database")
            database.engine.dispose()
        except Exception:
            pass

    def test_case_list_empty_or_rows(self):
        res = _run("notary.case_list")
        self.assertEqual(res["kind"], "case_list")
        self.assertIn("cases", res["data"])

    def test_case_flow_to_word(self):
        """Fixture: customer + property + case + participant → export .docx."""
        import uuid
        tag = uuid.uuid4().hex[:6].upper()
        cust = _run("notary.customer_create", {
            "ho_ten": "Nguyen Van Test G1",
            "so_giay_to": "00109" + tag.replace("0", "7")[:7],
            "ngay_sinh": "1950-01-01", "ngay_chet": "2024-05-01",
            "dia_chi": "xa test, Nam Dinh"})
        cid_cust = cust["data"]["customer"]["id"]

        prop = _run("notary.property_create", {
            "so_serial": f"TEST-G1-{tag}", "dia_chi": "thon test, xa test",
            "so_thua_dat": "999", "so_to_ban_do": "88"})
        cid_prop = prop["data"]["property"]["id"]

        case = _run("notary.case_create", {
            "nguoi_chet_id": cid_cust, "tai_san_id": cid_prop,
            "loai_van_ban": "khai_nhan", "noi_niem_yet": "xa test"})
        case_id = case["data"]["case"]["id"]

        heir = _run("notary.customer_create", {
            "ho_ten": "Nguyen Thi Test Heir",
            "so_giay_to": "00108" + tag.replace("0", "7")[:7],
            "ngay_sinh": "1980-03-03", "dia_chi": "xa test"})
        _run("notary.participant_add", {
            "case_id": case_id, "customer_id": heir["data"]["customer"]["id"],
            "vai_tro": "Con", "hang_thua_ke": 1, "ty_le": 100,
            "co_nhan_tai_san": True})

        detail = _run("notary.case_get", {"case_id": case_id})
        self.assertEqual(detail["data"]["id"], case_id)
        self.assertEqual(len(detail["data"]["participants"]), 1)
        self.assertEqual(detail["data"]["tong_ty_le"], 100)

        out = _run("notary.export_word", {"case_id": case_id})
        self.assertEqual(out["kind"], "word_export")
        out_path = Path(out["data"]["output_file"]["path"])
        self.assertTrue(out_path.is_file())
        self.assertTrue(str(out_path).endswith(".docx"))
        # Mapping that — file docx mo duoc va khong con placeholder.
        import docx
        doc = docx.Document(str(out_path))
        text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("Nguyen Van Test G1".upper().replace(" ", " "),
                      text.upper())

    def test_word_templates_and_zalo(self):
        tpl = _run("notary.word_templates")
        self.assertGreaterEqual(len(tpl["data"]["templates"]), 1)
        zalo = _run("zalo.status")
        self.assertEqual(zalo["kind"], "zalo_status")
        self.assertIn("accounts", zalo["data"])
        self.assertIn("totals", zalo["data"])

    def test_validation_errors_structured(self):
        with self.assertRaises(CommandError) as ctx:
            _run("notary.case_get", {"case_id": "abc"})
        self.assertEqual(ctx.exception.code, "validation_error")
        with self.assertRaises(CommandError) as ctx2:
            _run("notary.case_create", {})
        self.assertEqual(ctx2.exception.code, "validation_error")


@unittest.skipUnless(_engines_available(),
                     "chua cau hinh engine-roots.json")
class TestUploadAdapter(unittest.TestCase):
    """MIN-69: scan/audit/env_check qua engine that (khong can browser).

    Versioned commands (upload.workflow.v1) + G1_UPLOAD_DATA_DIR → tempdir:
    registry/workspace/ghi deu nam trong temp, khong cham data that.
    Fixture DOCX/Excel do test tu tao."""

    @classmethod
    def setUpClass(cls):
        import os
        cls._tmp = tempfile.TemporaryDirectory(prefix="g1-upload-test-")
        os.environ["G1_UPLOAD_DATA_DIR"] = cls._tmp.name
        cls._fixtures = Path(cls._tmp.name) / "fixtures"

    @classmethod
    def tearDownClass(cls):
        # Nha handle workspace.sqlite3 truoc khi tempdir cleanup.
        try:
            import upload_workspace
            upload_workspace.reset_store_for_tests()
        except Exception:
            pass

    def _workspace_revision(self):
        ws = _run("upload.workspace_get", {
            "workflow_version": _WF, "website_id": "nam_dinh"})
        return ws["data"]["revision"]

    def test_websites_and_workspace(self):
        cat = _run("upload.websites", {"workflow_version": _WF})
        ids = [w["website_id"] for w in cat["data"]["websites"]]
        self.assertIn("nam_dinh", ids)

    def test_env_check_real(self):
        res = _run("upload.env_check", {
            "workflow_version": _WF, "website_id": "nam_dinh"})
        self.assertEqual(res["kind"], "env_check")
        self.assertIn("steps", res["data"])

    def test_scan_and_audit_fixture(self):
        folder = self._fixtures / "hs-scan"
        folder.mkdir(parents=True, exist_ok=True)
        _write_docx(folder / "HD-001.docx", [
            "HỢP ĐỒNG CHUYỂN NHƯỢNG",
            "Số công chứng: 77/2026 ngày 10/05/2026",
        ])
        res = _run("upload.scan", {
            "workflow_version": _WF, "website_id": "nam_dinh",
            "folder": {"path": str(folder), "scope": "machine_local"},
            "expected_revision": self._workspace_revision(),
            "full_rescan": True})
        self.assertEqual(res["kind"], "scan_report")
        self.assertTrue(res["data"]["run_id"])
        self.assertIn("records", res["data"])
        # Data root la temp — registry nam duoi G1_UPLOAD_DATA_DIR.
        regdb = (Path(self._tmp.name) / "websites" / "nam_dinh"
                 / "registry.sqlite3")
        self.assertTrue(regdb.is_file(),
                        f"registry khong trong data root temp: {regdb}")

        xlsx = self._fixtures / "so_cong_chung.xlsx"
        _write_xlsx(xlsx, [
            ("Số công chứng", "Ngày công chứng"),
            ("77/2026", "10/05/2026"),
            ("79/2026", "12/05/2026"),
            ("79/2026", "12/05/2026"),
        ])
        audit = _run("upload.audit_excel", {
            "workflow_version": _WF, "website_id": "nam_dinh",
            "file_ref": {"path": str(xlsx), "scope": "machine_local"},
            "from_date": "2026-05-01", "to_date": "2026-05-31"})
        self.assertEqual(audit["kind"], "audit_report")
        self.assertIn("missing", audit["data"])
        self.assertIn("issues", audit["data"])
        self.assertTrue(audit["data"]["audit_id"])
        # Engine that chay: 3 dong, 79/2026 trung → 2 issue trung_so.
        self.assertEqual(
            audit["data"]["summary"]["excel_total"], 3)
        dupes = [i["so_cong_chung"]
                 for i in audit["data"]["issues"] or []
                 if "trung" in (i.get("ghi_chu") or "")]
        self.assertEqual(dupes.count("79/2026"), 2)
        for row in (audit["data"]["issues"] or [])[:3]:
            self.assertIn("so_cong_chung", row)
            self.assertIn("ghi_chu", row)

    def test_unc_rejected(self):
        with self.assertRaises(CommandError) as ctx:
            _run("upload.scan",
                 {"folder": {"path": "\\\\server\\share",
                             "scope": "machine_local"}})
        self.assertEqual(ctx.exception.code, "file_scope_not_supported")


class TestRegistryWiring(unittest.TestCase):
    """Khong can engine: registry phu dung namespace da duyet."""

    def test_new_commands_registered(self):
        for cmd in ("notary.case_list", "notary.case_get",
                    "notary.case_create", "notary.customer_list",
                    "notary.customer_create", "notary.property_list",
                    "notary.property_create", "notary.participant_add",
                    "notary.word_templates", "notary.export_word",
                    "ocr.analyze", "zalo.status",
                    "upload.scan", "upload.audit_excel", "upload.env_check",
                    "upload.session_start", "upload.session_status",
                    "upload.confirm_login", "upload.session_close",
                    "upload.download_export", "upload.prepare",
                    "upload.finish_review"):
            self.assertIn(cmd, reg.COMMANDS, f"thieu {cmd}")

    def test_missing_engine_is_structured(self):
        # Command van loi CommandError sach khi engine root khong hop le.
        import os
        old = os.environ.get("G1_NOTARY_V2_ROOT")
        os.environ["G1_NOTARY_V2_ROOT"] = "Z:/khong-ton-tai-g1"
        try:
            with self.assertRaises(CommandError) as ctx:
                _run("notary.case_list")
            self.assertEqual(ctx.exception.code, "engine_not_installed")
        finally:
            if old is None:
                os.environ.pop("G1_NOTARY_V2_ROOT", None)
            else:
                os.environ["G1_NOTARY_V2_ROOT"] = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
