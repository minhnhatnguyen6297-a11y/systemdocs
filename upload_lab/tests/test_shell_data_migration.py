"""Tests for tools/migrate_shell_data.py (MIN-69 task 2).

Copy da kiem chung du lieu legacy (working dir upload_lab cu) sang vung du
lieu theo website trong shell. Nguon khong bao gio bi ghi/doi; dich phai rong;
sai website bi tu choi; thieu JSON/manifest duoc bao ro va khong kich hoat
target chua day du.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from batch_scan import connect_registry, upsert_registry_record

from tools.migrate_shell_data import (
    MigrationError,
    apply_migration,
    inspect_source,
    main as migrate_main,
)

NAM_DINH_URL = "https://congchungnamdinh.ninhbinh.gov.vn"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(root))] = _sha256(path)
    return result


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class MigrationFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.source = self.root / "legacy_upload_lab"
        self.target = self.root / "data" / "websites" / "nam_dinh"

    # ---------- fixture builders ----------

    def _write_env(self, base_url: str = NAM_DINH_URL, extra: str = ""):
        _write(
            self.source / ".env",
            "ND_BASE_URL=" + base_url + "\n"
            "ND_LOGIN_URL=\n"
            "ND_CREATE_URL=\n"
            "ND_STORAGE_STATE_PATH=nd_storage_state.json\n"
            "ND_BROWSER_CHANNEL=chromium\n"
            "ND_MAX_PREPARED_TABS=10\n"
            "ND_POST_PREPARE_DELAY_MS=1500\n"
            "MAT_KHAU_RIENG=khong-duoc-copy\n" + extra)

    def _seed_row(self, conn, *, file_key, run_id, status,
                  output_json_path=None, artifact_dir=None, verify_json=None):
        docx = self.root / "user_docs" / f"{file_key}.docx"
        docx.parent.mkdir(parents=True, exist_ok=True)
        docx.write_text("dummy " + file_key, encoding="utf-8")
        upsert_registry_record(
            conn,
            file_key=file_key,
            file_path=docx,
            stat_result=docx.stat(),
            customer_folder="KhachA",
            contract_no="1/2026",
            status=status,
            run_id=run_id,
            output_json_path=(
                str(output_json_path) if output_json_path else None),
            artifact_dir=str(artifact_dir) if artifact_dir else None,
            verify_json=str(verify_json) if verify_json else None,
        )

    def _make_source(self, *, base_url: str = NAM_DINH_URL,
                     with_env: bool = True,
                     missing_output: bool = False,
                     missing_manifest: bool = False):
        self.source.mkdir(parents=True, exist_ok=True)
        if with_env:
            self._write_env(base_url)

        out1 = _write(self.source / "output" / "one.json",
                      json.dumps({"web_form": {"so": "1/2026"}}))
        out2 = _write(self.source / "output" / "two.json",
                      json.dumps({"web_form": {"so": "2/2026"}}))
        missing_path = self.source / "output" / "ghost.json"
        if not missing_output:
            _write(missing_path, json.dumps({"web_form": {"so": "3/2026"}}))

        art_dir = self.source / "upload_runs" / "batch_1"
        verify = _write(art_dir / "verify.json", "{}")

        conn = connect_registry(self.source / "registry.sqlite3")
        try:
            self._seed_row(conn, file_key="k1", run_id="run-1",
                           status="extracted", output_json_path=out1)
            self._seed_row(conn, file_key="k2", run_id="run-1",
                           status="uploaded_success", output_json_path=out2,
                           artifact_dir=art_dir, verify_json=verify)
            self._seed_row(conn, file_key="k3", run_id="run-1",
                           status="extract_failed",
                           output_json_path=missing_path)
            if missing_manifest:
                self._seed_row(conn, file_key="k4", run_id="run-khong-manifest",
                               status="extracted", output_json_path=out1)
        finally:
            conn.close()

        if not missing_manifest:
            _write(self.source / "runs" / "2026-01-02_030405.json",
                   json.dumps({"run_id": "run-1",
                               "folder_root": str(self.root / "user_docs"),
                               "stats": {"processed_files": 3}}))
        else:
            _write(self.source / "runs" / "2026-01-02_030405.json",
                   json.dumps({"run_id": "run-1",
                               "folder_root": str(self.root / "user_docs"),
                               "stats": {"processed_files": 3}}))

        _write(self.source / "downloads" / "so_cong_chung.xlsx", "fake-xlsx")
        _write(self.source / "nd_storage_state.json",
               json.dumps({"cookies": [{"name": "x", "value": "y"}]}))
        _write(self.source / "uploader_staff_options.json",
               json.dumps({"cong_chung_vien": ["CCV A"], "thu_ky": []},
                          ensure_ascii=False))
        _write(self.source / "logs" / "playwright_uploader.log", "log line\n")
        _write(self.source / "logs" / "login_network.jsonl",
               '{"url": "https://x", "headers": {"authorization": "t"}}\n')
        return self.source

    def _registry_rows(self, db_path: Path):
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(
                "SELECT * FROM file_registry ORDER BY id").fetchall()
        finally:
            conn.close()


class InspectTests(MigrationFixture):
    def test_inspect_reports_filtered_inventory(self):
        self._make_source()
        report = inspect_source(self.source)

        self.assertEqual(report["website"]["website_id"], "nam_dinh")
        self.assertTrue(report["website"]["verified"])
        counts = report["counts"]
        self.assertEqual(counts["registry_rows"], 3)
        self.assertEqual(counts["by_status"]["extracted"], 1)
        self.assertEqual(counts["by_status"]["uploaded_success"], 1)
        self.assertEqual(counts["by_status"]["extract_failed"], 1)
        self.assertEqual(counts["run_manifests"], 1)
        self.assertEqual(counts["output_json"], 3)
        self.assertEqual(counts["downloads"], 1)
        self.assertTrue(counts["storage_state"])
        self.assertTrue(counts["staff_options"])
        self.assertTrue(counts["env"])
        self.assertEqual(report["missing"]["output_json"], [])
        self.assertEqual(report["missing"]["run_manifests"], [])
        # khong in noi dung session/cookie/env secret vao bao cao
        blob = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("khong-duoc-copy", blob)
        self.assertNotIn('"cookies"', blob)

    def test_inspect_flags_missing_output_json(self):
        self._make_source(missing_output=True)
        report = inspect_source(self.source)
        self.assertTrue(
            any(p.replace("\\", "/").endswith("output/ghost.json")
                for p in report["missing"]["output_json"]),
            report["missing"]["output_json"])
        self.assertEqual(report["counts"]["output_json"], 2)

    def test_inspect_flags_missing_manifest(self):
        self._make_source(missing_manifest=True)
        report = inspect_source(self.source)
        self.assertIn("run-khong-manifest",
                      report["missing"]["run_manifests"])

    def test_inspect_unverified_source(self):
        self._make_source(with_env=False)
        report = inspect_source(self.source)
        self.assertFalse(report["website"]["verified"])
        self.assertIsNone(report["website"]["website_id"])
        self.assertTrue(report["website"]["problems"])


class ApplyTests(MigrationFixture):
    def test_apply_copies_and_verifies(self):
        self._make_source()
        report = apply_migration(self.source, self.target)

        self.assertEqual(report["status"], "complete")
        # cau truc dich
        for rel in ("registry.sqlite3", ".env", "nd_storage_state.json",
                    "uploader_staff_options.json", "output/one.json",
                    "output/two.json", "output/ghost.json",
                    "runs/2026-01-02_030405.json",
                    "downloads/so_cong_chung.xlsx",
                    "upload_runs/batch_1/verify.json",
                    "logs/playwright_uploader.log"):
            self.assertTrue((self.target / rel).is_file(), f"thieu {rel}")
        # network dump co the chua header nhay cam — khong copy
        self.assertFalse((self.target / "logs" / "login_network.jsonl").exists())
        self.assertIn("login_network.jsonl",
                      json.dumps(report["skipped"], ensure_ascii=False))

        # registry copy: so luong + trang thai khop, id giu nguyen
        src_rows = self._registry_rows(self.source / "registry.sqlite3")
        dst_rows = self._registry_rows(self.target / "registry.sqlite3")
        self.assertEqual(len(src_rows), len(dst_rows))
        self.assertEqual([r["id"] for r in src_rows],
                         [r["id"] for r in dst_rows])
        self.assertEqual([r["status"] for r in src_rows],
                         [r["status"] for r in dst_rows])
        self.assertEqual([r["run_id"] for r in src_rows],
                         [r["run_id"] for r in dst_rows])

        # duong dan noi bo duoc rewrite; file nguon cua user giu nguyen
        src_resolved = self.source.resolve()
        tgt_resolved = self.target.resolve()
        for srow, drow in zip(src_rows, dst_rows):
            self.assertEqual(srow["file_path"], drow["file_path"])
            for col in ("output_json_path", "artifact_dir", "verify_json"):
                sval, dval = srow[col], drow[col]
                if not sval:
                    continue
                self.assertTrue(
                    str(sval).startswith(str(src_resolved)),
                    f"{col} nguon khong nam trong source: {sval}")
                self.assertTrue(
                    str(dval).startswith(str(tgt_resolved)),
                    f"{col} chua rewrite sang target: {dval}")
        # file da rewrite ton tai that
        for drow in dst_rows:
            if drow["output_json_path"]:
                self.assertTrue(Path(drow["output_json_path"]).is_file())

        # hash file copy == hash nguon
        self.assertEqual(_sha256(self.source / "output" / "one.json"),
                         _sha256(self.target / "output" / "one.json"))
        self.assertEqual(_sha256(self.source / "downloads" / "so_cong_chung.xlsx"),
                         _sha256(self.target / "downloads" / "so_cong_chung.xlsx"))
        self.assertEqual(report["verified"]["files_copied"],
                         report["verified"]["files_hashed"])

        # .env chi giu key public — key la bi loc
        env_text = (self.target / ".env").read_text(encoding="utf-8")
        self.assertIn("ND_BASE_URL=" + NAM_DINH_URL, env_text)
        self.assertNotIn("MAT_KHAU_RIENG", env_text)
        self.assertIn("MAT_KHAU_RIENG", (self.source / ".env").read_text(
            encoding="utf-8"))  # nguon giu nguyen

    def test_source_untouched(self):
        self._make_source()
        before = _tree_hashes(self.source)
        apply_migration(self.source, self.target)
        after = _tree_hashes(self.source)
        self.assertEqual(before, after)

    def test_rerun_refused_target_not_empty(self):
        self._make_source()
        apply_migration(self.source, self.target)
        snapshot = _tree_hashes(self.target)
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertEqual(ctx.exception.code, "target_not_empty")
        self.assertEqual(_tree_hashes(self.target), snapshot)

    def test_wrong_website_rejected(self):
        self._make_source(base_url="https://tinh-khac.gov.vn")
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertIn(ctx.exception.code,
                      ("website_not_verified", "website_mismatch"))
        # khong kich hoat target
        self.assertFalse(self.target.exists()
                         and any(self.target.iterdir()))

    def test_missing_env_rejected(self):
        self._make_source(with_env=False)
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertEqual(ctx.exception.code, "website_not_verified")
        self.assertFalse(self.target.exists()
                         and any(self.target.iterdir()))

    def test_missing_output_json_blocks_apply(self):
        self._make_source(missing_output=True)
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertEqual(ctx.exception.code, "missing_source_files")
        self.assertIn("ghost.json", str(ctx.exception))
        self.assertFalse(self.target.exists()
                         and any(self.target.iterdir()))

    def test_missing_run_manifest_blocks_apply(self):
        self._make_source(missing_manifest=True)
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertEqual(ctx.exception.code, "missing_source_files")
        self.assertIn("run-khong-manifest", str(ctx.exception))
        self.assertFalse(self.target.exists()
                         and any(self.target.iterdir()))

    def test_nonempty_target_rejected(self):
        self._make_source()
        self.target.mkdir(parents=True)
        _write(self.target / "cu.txt", "data cu")
        with self.assertRaises(MigrationError) as ctx:
            apply_migration(self.source, self.target)
        self.assertEqual(ctx.exception.code, "target_not_empty")

    def test_target_inside_source_rejected(self):
        self._make_source()
        nested = self.source / "websites" / "nam_dinh"
        with self.assertRaises(MigrationError):
            apply_migration(self.source, nested)
        same = self.source
        with self.assertRaises(MigrationError):
            apply_migration(self.source, same)


class CliTests(MigrationFixture):
    def test_cli_inspect_and_apply(self):
        self._make_source()
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = migrate_main([
                "--inspect", "--source", str(self.source),
                "--target", str(self.target)])
        self.assertEqual(code, 0)
        self.assertIn("nam_dinh", buf.getvalue())

        code = migrate_main([
            "--apply", "--source", str(self.source),
            "--target", str(self.target)])
        self.assertEqual(code, 0)
        self.assertTrue((self.target / "registry.sqlite3").is_file())

    def test_cli_apply_refused_second_time(self):
        self._make_source()
        self.assertEqual(migrate_main([
            "--apply", "--source", str(self.source),
            "--target", str(self.target)]), 0)
        err = io.StringIO()
        with redirect_stderr(err):
            code = migrate_main([
                "--apply", "--source", str(self.source),
                "--target", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("target_not_empty", err.getvalue())

    def test_cli_bad_target_shape_is_clean_error(self):
        """Target khong phai .../websites/nam_dinh → exit 2, stderr, khong
        traceback ProviderDataDirError."""
        self._make_source()
        bad = self.root / "data" / "khong_dung_ten"
        err = io.StringIO()
        with redirect_stderr(err):
            code = migrate_main([
                "--apply", "--source", str(self.source),
                "--target", str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("invalid_target", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertFalse(bad.exists())

    def test_cli_unexpected_exception_is_clean_exit2(self):
        """Loi khong phai MigrationError (OSError/sqlite3.Error...) → exit 2
        tren stderr, khong phai traceback exit 1."""
        import tools.migrate_shell_data as mod
        original = mod.apply_migration
        mod.apply_migration = lambda *_a, **_k: 1 / 0
        try:
            err = io.StringIO()
            with redirect_stderr(err):
                code = migrate_main([
                    "--apply", "--source", str(self.source),
                    "--target", str(self.target)])
        finally:
            mod.apply_migration = original
        self.assertEqual(code, 2)
        self.assertIn("migration_failed", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_cli_inspect_without_target(self):
        """--inspect chi can --source (target la tuy chon tu fix)."""
        self._make_source()
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = migrate_main(["--inspect", "--source", str(self.source)])
        self.assertEqual(code, 0)
        self.assertIn("nam_dinh", buf.getvalue())
        self.assertNotIn("Target:", buf.getvalue())

    def test_cli_inspect_with_target_prints_check(self):
        """--inspect --target: in check san sang cua target thay vi bo qua."""
        self._make_source()
        self.target.mkdir(parents=True)  # thu muc rong → nhanh san sang
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = migrate_main([
                "--inspect", "--source", str(self.source),
                "--target", str(self.target)])
        self.assertEqual(code, 0)
        self.assertIn("shape: ok", buf.getvalue())
        self.assertIn("san sang --apply", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
