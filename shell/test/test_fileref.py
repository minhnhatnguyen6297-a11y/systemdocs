"""Unit test cho shell/sidecar/fileref.py — kiem tra absolute/UNC helpers.

Khong phu thuoc OS: Windows drive (X:\\), long path (\\\\?\\D:\\) va UNC
(\\\\server\\share, //server/share, \\\\?\\UNC\\...) duoc kiem ca tren Linux.
"""
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "sidecar"))

from errors import CommandError  # noqa: E402
import fileref  # noqa: E402


class TestIsAbsolute(unittest.TestCase):
    def test_windows_drive_accepted(self):
        for p in ("D:\\intake\\file.docx", "X:/tmp/a.jpg", "z:\\x"):
            self.assertTrue(fileref.is_absolute(p), p)

    def test_long_prefix_local_drive_accepted(self):
        self.assertTrue(fileref.is_absolute("\\\\?\\D:\\duong\\dan.docx"))

    def test_posix_absolute_accepted(self):
        self.assertTrue(fileref.is_absolute("/home/user/a.docx"))

    def test_relative_rejected(self):
        for p in ("relative/path.docx", "a.docx", "./x", "..\\y"):
            self.assertFalse(fileref.is_absolute(p), p)


class TestIsUnc(unittest.TestCase):
    def test_backslash_unc(self):
        self.assertTrue(fileref.is_unc("\\\\server\\share\\f.docx"))

    def test_forward_slash_unc(self):
        self.assertTrue(fileref.is_unc("//server/share/f.docx"))

    def test_extended_unc(self):
        self.assertTrue(fileref.is_unc("\\\\?\\UNC\\server\\share\\f.docx"))

    def test_long_prefix_local_drive_not_unc(self):
        self.assertFalse(fileref.is_unc("\\\\?\\D:\\duong\\dan.docx"))

    def test_local_paths_not_unc(self):
        for p in ("D:\\a.docx", "/home/u/a.docx", "a.docx"):
            self.assertFalse(fileref.is_unc(p), p)


class TestValidateFileRef(unittest.TestCase):
    def test_windows_drive_accepted(self):
        out = fileref.validate_file_ref(
            {"path": "D:\\intake\\file.docx", "scope": "machine_local"})
        self.assertEqual(out, Path("D:\\intake\\file.docx"))

    def test_unc_rejected(self):
        for p in ("\\\\server\\share\\f.docx", "//server/share/f.docx",
                  "\\\\?\\UNC\\server\\share\\f.docx"):
            with self.assertRaises(CommandError) as ctx:
                fileref.validate_file_ref({"path": p, "scope": "machine_local"})
            self.assertEqual(ctx.exception.code, "file_scope_not_supported")

    def test_relative_rejected(self):
        with self.assertRaises(CommandError) as ctx:
            fileref.validate_file_ref(
                {"path": "relative/a.docx", "scope": "machine_local"})
        self.assertEqual(ctx.exception.code, "file_scope_not_supported")


if __name__ == "__main__":
    unittest.main()
