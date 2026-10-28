"""file_ref validation theo desktopcommand.v1 §6 — machine_local only (O1).

Path tuyet doi: chap nhan absolute path cua host OS qua pathlib
(Path(p).is_absolute()) VA Windows drive/long-path (ntpath) — de cung mot
logic chay dung tren Windows va tren Linux (test/CI). UNC bi tu choi o moi
dang: \\\\server\\share, //server/share, \\\\?\\UNC\\server\\share (dang extended
cua UNC). Prefix \\\\?\\ cho local drive duoc phep (long path, finding F2 cua P1).
"""
import os
import re
from pathlib import Path

from errors import CommandError

_LONG_PREFIX = "\\\\?\\"
_ABS_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")


def is_unc(path):
    r"""True neu `path` la UNC o bat ky dang nao (\\server\share,
    //server/share, \\?\UNC\server\share). \\?\D:\... la local, khong phai UNC."""
    if path.startswith(_LONG_PREFIX):
        rest = path[len(_LONG_PREFIX):]
        # \\?\UNC\server\share la UNC dang extended; \\?\D:\... la local
        low = rest.lower()
        return (low.startswith("unc\\") or low.startswith("unc/")
                or rest.startswith("\\\\") or rest.startswith("//"))
    return path.startswith("\\\\") or path.startswith("//")


def is_absolute(path, *, windows=None):
    r"""True neu `path` la absolute THAT SU (co o dia) theo Windows, hoac
    absolute POSIX khi host khong phai Windows.

    Path chi co goc ma khong co o dia (\foo, /foo) bi TU CHOI tren Windows:
    no resolve theo o dia hien hanh cua process (review PR #25 — ntpath.isabs
    tren Python 3.12 tra True cho \foo). UNC va \\?\ duoc xu ly rieng.
    """
    if path.startswith(_LONG_PREFIX) or _ABS_DRIVE.match(path):
        return True
    if windows is None:
        windows = os.name == "nt"
    return (not windows) and path.startswith("/") and not path.startswith("//")


def validate_file_ref(ref):
    """Tra Path da kiem hoac raise CommandError(file_scope_not_supported)."""
    if not isinstance(ref, dict):
        raise CommandError("validation_error", "file_ref phai la object")
    path = ref.get("path")
    scope = ref.get("scope")
    if scope != "machine_local":
        raise CommandError(
            "file_scope_not_supported",
            f"scope={scope!r}: G1-SM chi chap nhan machine_local")
    if not isinstance(path, str) or not path:
        raise CommandError("validation_error", "file_ref.path rong/khong phai chuoi")
    if is_unc(path):
        raise CommandError(
            "file_scope_not_supported",
            "UNC path bi tu choi trong G1-SM (mot may)")
    if not (path.startswith(_LONG_PREFIX) or is_absolute(path)):
        raise CommandError(
            "file_scope_not_supported",
            "path khong tuyet doi")
    return Path(path)


def existing_file(ref):
    """validate + ton tai + la file thuong. Tra Path."""
    p = validate_file_ref(ref)
    try:
        if not p.exists():
            raise CommandError("file_not_found", f"khong tim thay: {p.name}")
        if not p.is_file():
            raise CommandError("file_not_found", f"khong phai file: {p.name}")
    except PermissionError as exc:
        raise CommandError("file_locked", f"khong doc duoc: {p.name}") from exc
    return p


def existing_dir(ref):
    """Destination FileRef cua word_export_batch (contract §8.2):
    is_dir:true + validate_file_ref (scope/UNC/path tuyet doi) + ton tai
    + la thu muc. Tra Path; khong tao directory moi."""
    if not isinstance(ref, dict) or ref.get("is_dir") is not True:
        raise CommandError("validation_error",
                           "file_ref destination phai co is_dir:true")
    p = validate_file_ref(ref)
    try:
        if not p.exists():
            raise CommandError("file_not_found", f"khong tim thay: {p.name}")
        if not p.is_dir():
            raise CommandError("file_not_found",
                               f"khong phai thu muc: {p.name}")
    except PermissionError as exc:
        raise CommandError("file_locked", f"khong doc duoc: {p.name}") from exc
    return p
