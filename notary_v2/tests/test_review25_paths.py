"""Review PR #25: path driveless tren Windows + builtin template traversal."""
import pytest

from routers.cases import _is_safe_builtin_name
from services.document_intake.service import _is_abs


@pytest.mark.parametrize("p", ["\\foo\\a.pdf", "/foo/a.pdf", "C:foo", "rel\\a.pdf"])
def test_intake_rejects_driveless_on_windows(p):
    assert _is_abs(p, windows=True) is False


def test_intake_accepts_drive_and_long_prefix():
    assert _is_abs("C:\\in\\a.pdf", windows=True)
    assert _is_abs("\\\\?\\D:\\in\\a.pdf", windows=True)
    assert _is_abs("/tmp/a.pdf", windows=False)


@pytest.mark.parametrize("name", ["xa_PCDS_template.docx", "Mau 1.DOCX"])
def test_builtin_name_ok(name):
    assert _is_safe_builtin_name(name)


@pytest.mark.parametrize("name", ["", "..", "../x.docx", "..\\x.docx", "C:\\x.docx",
                                  "/etc/x.docx", "sub/x.docx", "x.txt"])
def test_builtin_name_rejects_traversal(name):
    assert not _is_safe_builtin_name(name)
