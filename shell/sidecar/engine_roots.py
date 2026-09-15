"""Engine roots — resolve duong dan repo con va import module engine that.

P6 (MIN-68/69): sidecar khong port lai nghiep vu sang day — no import code
that tu repo con (`services.*`, `batch_scan`, `ui.services.*`) qua sys.path
theo engine root. Nguon migrate duoc owner khoa:
  - notary_v2: codex/zalo-document-inbox-v2 @ d350048 (D0-1, MIN-74)
  - upload_lab: main (da gom MIN-77/39-42 fixes)

Thu tu resolve (uutien cao → thap):
  1. env G1_NOTARY_V2_ROOT / G1_UPLOAD_LAB_ROOT
  2. shell/engine-roots.json (gitignored — path tuyet doi cua tung may)
     {"notary_v2": "D:/notary_v2", "upload_lab": "D:/upload_lab_repo"}
Thieu ca hai → engine_not_installed (khong retry, next_action ro rang).

G1_OUTPUT_DIR: thu muc output do sidecar so huu (word export, file tai ve).
Default <shell>/output (gitignored). Electron main co the dat env nay toi
userData cho ban packaged.
"""
import importlib
import json
import os
import sys
from pathlib import Path

from errors import CommandError

_SIDE_DIR = Path(__file__).resolve().parent
SHELL_ROOT = _SIDE_DIR.parent
_CONFIG_PATH = SHELL_ROOT / "engine-roots.json"

_ENV_BY_KEY = {
    "notary_v2": "G1_NOTARY_V2_ROOT",
    "upload_lab": "G1_UPLOAD_LAB_ROOT",
}

_loaded_roots = None


def _load_roots_file():
    global _loaded_roots
    if _loaded_roots is None:
        try:
            _loaded_roots = json.loads(
                _CONFIG_PATH.read_text(encoding="utf-8"))
        except OSError:
            _loaded_roots = {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            _loaded_roots = {}
    return _loaded_roots


def engine_root(key):
    """Tra Path root cua engine hoac CommandError(engine_not_installed)."""
    env_name = _ENV_BY_KEY.get(key)
    if env_name is None:
        raise CommandError("validation_error", f"engine key la: {key!r}")
    raw = os.environ.get(env_name) or _load_roots_file().get(key)
    if not raw:
        raise CommandError(
            "engine_not_installed",
            f"chua cau hinh engine root cho {key} "
            f"(env {env_name} hoac engine-roots.json)",
            retryable=False,
            next_action="tao shell/engine-roots.json tu "
                        "engine-roots.example.json")
    root = Path(raw)
    if not root.is_dir():
        raise CommandError(
            "engine_not_installed",
            f"engine root khong ton tai: {root}",
            retryable=False,
            next_action="kiem tra lai engine-roots.json")
    return root


def import_engine_module(key, module):
    """Import module trong engine root. Engine code that, khong copy."""
    root = engine_root(key)
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise CommandError(
            "engine_unavailable",
            f"khong import duoc {module} tu {root}: {exc}",
            retryable=True) from exc


def output_dir(*parts):
    """Thu muc output do sidecar so huu (contract g1-module-data §5)."""
    base = Path(os.environ.get("G1_OUTPUT_DIR") or (SHELL_ROOT / "output"))
    target = base.joinpath(*parts) if parts else base
    target.mkdir(parents=True, exist_ok=True)
    return target


def engine_info():
    """Thong tin cau hinh engine cho diagnostics — khong lo secret."""
    info = {}
    for key in _ENV_BY_KEY:
        try:
            info[key] = {"root": str(engine_root(key)), "ok": True}
        except CommandError as exc:
            info[key] = {"root": None, "ok": False, "error": exc.code}
    return info
