"""file_ref validation theo desktopcommand.v1 §6 — machine_local only (O1).

G1-SM chi chap nhan path tuyet doi tren may nay; UNC bi tu choi o moi dang:
\\\\server\\share, \\\\?\\UNC\\server\\share (dang extended cua UNC).
Prefix \\\\?\\ cho local drive duoc phep (long path, finding F2 cua P1).
"""
import re
from pathlib import Path

from errors import CommandError

_ABS_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_LONG_PREFIX = "\\\\?\\"


def _is_unc(path):
    if path.startswith(_LONG_PREFIX):
        rest = path[len(_LONG_PREFIX):]
        # \\?\UNC\server\share la UNC dang extended; \\?\D:\... la local
        low = rest.lower()
        return (low.startswith("unc\\") or low.startswith("unc/")
                or rest.startswith("\\\\") or rest.startswith("//"))
    return path.startswith("\\\\")


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
    if _is_unc(path):
        raise CommandError(
            "file_scope_not_supported",
            "UNC path bi tu choi trong G1-SM (mot may)")
    if not (path.startswith(_LONG_PREFIX) or _ABS_DRIVE.match(path)):
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
