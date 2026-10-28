import os
from pathlib import Path

import pytest

from errors import CommandError
from fileref import validate_file_ref


def _ref(path):
    return {"path": path, "scope": "machine_local"}


@pytest.mark.skipif(os.name == "nt", reason="POSIX absolute paths are non-Windows only")
def test_posix_absolute_path_accepted():
    assert validate_file_ref(_ref("/tmp/x")) == Path("/tmp/x")


def test_relative_path_rejected():
    with pytest.raises(CommandError) as exc:
        validate_file_ref(_ref("tmp/x"))
    assert exc.value.code == "file_scope_not_supported"


def test_unc_path_rejected():
    with pytest.raises(CommandError) as exc:
        validate_file_ref(_ref("\\\\server\\share\\x"))
    assert exc.value.code == "file_scope_not_supported"


def test_drive_path_accepted():
    assert validate_file_ref(_ref("C:\\temp\\x")) == Path("C:\\temp\\x")
