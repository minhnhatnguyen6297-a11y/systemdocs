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
  3. engine bundle ship trong goi packaged: `G1_ENGINE_DIR/<key>` (Electron
     main dat env nay toi <resourcesPath>/engine khi packaged); khi chay
     frozen ma khong co env thi fallback `<resources>/engine` tinh tu
     vi tri exe (resources/sidecar/g1-shell-sidecar/)
  4. thu muc cung ten trong repo gop: <repo>/notary_v2, <repo>/upload_lab
Thieu ca bon → engine_not_installed (khong retry, next_action ro rang).

G1_OUTPUT_DIR: thu muc output do sidecar so huu (word export, file tai ve).
Default <shell>/output (gitignored). Electron main co the dat env nay toi
userData cho ban packaged. Khi frozen ma env thieu → fallback ve
%LOCALAPPDATA%/g1-shell/output thay vi ghi vao thu muc cai dat.

G1_ENGINE_DATA_DIR (tu buoc 3): data root cho engine root read-only
(bundle nam trong resources — khong duoc ghi). Hien chi can cho
notary_v2 (database.py neo notary.db canh __file__); adapter redirect DB
ve <data_dir>/notary.db khi root la bundled. Dev khong doi: data dir
chinh la engine root (repo) nhu cu; co the override bang
G1_NOTARY_DATA_DIR (test khong ghi DB that).
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

# Env override cho engine_data_dir — test/packaged redirect noi ghi cua
# engine root read-only. upload_lab co data root rieng (G1_UPLOAD_DATA_DIR,
# upload_workspace.upload_data_root) — khong di qua helper nay.
_DATA_ENV_BY_KEY = {
    "notary_v2": "G1_NOTARY_DATA_DIR",
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


def bundled_engine_base():
    """Thu muc `resources/engine` cua goi packaged — None khi dev.

    Env `G1_ENGINE_DIR` (Electron main truyen) uu tien; frozen fallback:
    exe nam tai resources/sidecar/g1-shell-sidecar/ → parents[2] = resources.
    """
    raw = os.environ.get("G1_ENGINE_DIR")
    if raw:
        return Path(raw).expanduser()
    if getattr(sys, "frozen", False):
        try:
            return Path(sys.executable).resolve().parents[2] / "engine"
        except (IndexError, OSError):
            return None
    return None


def bundled_engine_dir(key):
    base = bundled_engine_base()
    if base is None:
        return None
    return base / key


def engine_root(key):
    """Tra Path root cua engine hoac CommandError(engine_not_installed)."""
    env_name = _ENV_BY_KEY.get(key)
    if env_name is None:
        raise CommandError("validation_error", f"engine key la: {key!r}")
    raw = os.environ.get(env_name) or _load_roots_file().get(key)
    if not raw:
        bundled = bundled_engine_dir(key)
        if bundled is not None and bundled.is_dir():
            return bundled
        sibling = SHELL_ROOT.parent / key
        if sibling.is_dir():
            return sibling
        raise CommandError(
            "engine_not_installed",
            f"chua cau hinh engine root cho {key} "
            f"(env {env_name}, engine-roots.json hoac engine bundle)",
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


def is_bundled_root(key):
    """True khi engine root resolve tu bundle packaged (read-only)."""
    bundled = bundled_engine_dir(key)
    if bundled is None or not bundled.is_dir():
        return False
    try:
        return engine_root(key).resolve() == bundled.resolve()
    except CommandError:
        return False


def engine_data_dir(key):
    """Noi engine duoc phep ghi khi engine root read-only/bundled.

    - env `_DATA_ENV_BY_KEY[key]` (vd G1_NOTARY_DATA_DIR) thang luon —
      test tro ve tempdir de khong ghi DB that.
    - bundled root → <G1_OUTPUT_DIR>/engine-data/<key> (userData — song
      qua app update; install dir khong bao gio bi ghi).
    - root thuong (dev) → chinh engine root: DB/file engine van nam canh
      code nhu truoc, khong doi hanh vi dev.
    """
    env_name = _DATA_ENV_BY_KEY.get(key)
    raw = os.environ.get(env_name) if env_name else None
    if raw:
        base = Path(raw).expanduser()
    elif is_bundled_root(key):
        base = Path(output_dir()) / "engine-data" / key
    else:
        return engine_root(key)
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


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


def _default_output_base():
    """Base cho output_dir khi G1_OUTPUT_DIR khong co.

    Frozen (packaged) ma thieu env → %LOCALAPPDATA%/g1-shell/output —
    khong bao gio default vao _MEIPASS/install dir (read-only)."""
    if getattr(sys, "frozen", False):
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "g1-shell" / "output"
        return Path.home() / "AppData" / "Local" / "g1-shell" / "output"
    return SHELL_ROOT / "output"


def output_dir(*parts):
    """Thu muc output do sidecar so huu (contract g1-module-data §5)."""
    base = Path(os.environ.get("G1_OUTPUT_DIR") or _default_output_base())
    target = base.joinpath(*parts) if parts else base
    target.mkdir(parents=True, exist_ok=True)
    return target


def engine_info():
    """Thong tin cau hinh engine cho diagnostics — khong lo secret."""
    info = {}
    for key in _ENV_BY_KEY:
        try:
            root = engine_root(key)
            info[key] = {"root": str(root), "ok": True,
                         "bundled": is_bundled_root(key)}
        except CommandError as exc:
            info[key] = {"root": None, "ok": False, "error": exc.code}
    return info
