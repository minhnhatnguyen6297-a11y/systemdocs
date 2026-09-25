"""F2 (MIN-69 T9 review) — preflight dep check cho goi sidecar.

Doc `requirements-package.txt` (pin cung version voi spec) va kiem:
  1. Moi package da cai trong interpreter hien tai DUNG version pin
     (importlib.metadata — offline, khong pip/network).
  2. Module name tuong ung import duoc — phat hien thieu module ma spec
     cho la co (vd python-multipart → FastAPI raise luc import routers).

Su dung: `python check_package_deps.py` (build_sidecar.ps1 va
test/build-upload-test.ps1 goi truoc PyInstaller). Exit 2 khi mismatch.
"""
import importlib
import importlib.metadata
import sys
from pathlib import Path

REQ = Path(__file__).resolve().parent / "requirements-package.txt"

# Ten distribution -> module de import-check (khac ten dist thi khai bao).
_MODULE_BY_DIST = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "python-multipart": "multipart",
    "sqlalchemy": "sqlalchemy",
    "openpyxl": "openpyxl",
    "python-docx": "docx",
    "pymupdf": "pymupdf",
    "playwright": "playwright.sync_api",
    "httpx": "httpx",
    "certifi": "certifi",
    "pillow": "PIL",
    "jinja2": "jinja2",
    "python-dotenv": "dotenv",
    "tzdata": "tzdata",
    # PyMuPDFb la wheel binary (mupdf*.dll) — khong co module rieng.
}


def _pinned():
    for line in REQ.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line and "==" in line:
            dist, ver = line.split("==", 1)
            yield dist.strip(), ver.strip()


def main() -> int:
    failures = []
    for dist, want in _pinned():
        try:
            got = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            failures.append(f"{dist}: THIEU (can {want})")
            continue
        if got != want:
            failures.append(f"{dist}: {got} != pin {want}")
        mod = _MODULE_BY_DIST.get(dist.lower())
        if mod:
            try:
                importlib.import_module(mod)
            except Exception as exc:  # noqa: BLE001 — bao ten module ro
                failures.append(f"{dist}: import {mod} loi: {exc}")
    if failures:
        print("check_package_deps FAIL — cai dung pin:\n"
              f"  {sys.executable} -m pip install -r {REQ}\n"
              + "\n".join(f"  - {f}" for f in failures),
              file=sys.stderr)
        return 2
    print(f"check_package_deps OK ({REQ.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
