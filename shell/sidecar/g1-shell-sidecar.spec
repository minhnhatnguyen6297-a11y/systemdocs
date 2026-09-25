# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — g1-shell-sidecar (MIN-69 T9).

Engine code (upload_lab/notary_v2) KHONG freeze vao exe — ship dang
extraResources `resources/engine/<key>` (engine_roots.bundled_engine_dir).
Spec nay dong goi sidecar app.py + python deps ma engine import luc chay
trong process sidecar (sys.path → resources/engine):

  - fastapi/uvicorn/pydantic/starlette  — contract server
  - openpyxl                            — Excel audit/export (contract_book_audit, batch download)
  - docx (python-docx)                  — scan/extract .docx + word export
  - pymupdf/fitz                        — PDF preview (file.inspect, zalo media)
  - dotenv                              — playwright_uploader .env, ocr_ai
  - playwright + driver (node.exe/package js) — NamDinhUploaderSession
  - sqlalchemy                          — notary_v2 database/models
  - httpx + certifi                     — ocr_ai cloud call
  - PIL                                 — ocr_ai/zalo_inbox image
  - jinja2                              — fastapi.templating o router import

Test build (G1_SIDECAR_TEST_BUILD=1, xem test/build-upload-test.ps1):
them `test/fixtures` vao pathex + hiddenimport `e2e_fixture_hook`/
`upload_portal` — ban production KHONG ship fixture provider nay.
"""
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

_TEST_BUILD = os.environ.get("G1_SIDECAR_TEST_BUILD") == "1"
_FIXTURES = os.path.normpath(
    os.path.join(SPECPATH, "..", "test", "fixtures"))

hiddenimports = []
datas = []
binaries = []

hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('docx')
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += [
    'dotenv',
    'httpx',
    'jinja2',
    'pydantic',
    'fitz',
    'pymupdf',
    'playwright.sync_api',
    # F2 (T9 review): FastAPI Form/File/UploadFile can python-multipart —
    # check_file_field raise RuntimeError LUC IMPORT router khi thieu →
    # engine_unavailable mo ho thay vi start sach. tzdata: ZoneInfo
    # ("Asia/Ho_Chi_Minh") trong services/zalo_inbox.py — Windows khong
    # co system tz database.
    'multipart',
    'tzdata',
]

# collect_all: datas + binaries + submodules cho package co file khong-.py.
for _pkg in ('playwright',   # driver/node.exe + package/*.js — bat buoc
             'pymupdf',      # mupdf*.dll
             'docx',         # docx/templates/default.docx
             'certifi'):     # cacert.pem — TLS cho httpx
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

if _TEST_BUILD:
    hiddenimports += ['e2e_fixture_hook', 'upload_portal']

# notary_mock_adapter (MIN-106) duoc bundle theo static import cua gateway,
# nhung BAT HOAT tren ban packaged: notary_gateway chi chon mock khi
# G1_DEV_NOTARY_MOCK=1 VA not sys.frozen — exe nay luon co sys.frozen.
# Electron main con strip flag khoi env con (config.js stripNotaryMockEnv).

# --- Third-party deps cua engine that (MIN-117) ---
# Engine source (notary_v2/, upload_lab/) duoc import tu filesystem qua
# engine_roots.sys.path — khong can bundle source. Nhung moi third-party
# package engine import PHAI nam trong bundle: packaged exe khong nhin thay
# site-packages cua venv dev. Thieu sqlalchemy tung lam moi notary.* real
# tra engine_not_installed/engine_unavailable (MIN-113 D3).
#
# collect_all lay ca datas + binaries + submodules vi cac package nay load
# tai nguyen dong: sqlalchemy.dialects.*, docx.oxml.*, PIL plugins,
# openpyxl sub-modules, playwright submodules, pydantic_core (.pyd),
# pymupdf C ext + mupdfcpp64.dll, rapidfuzz C ext, tzdata zoneinfo db
# (Windows khong co system tz db — services.zalo_inbox dung ZoneInfo),
# playwright driver (node.exe trong playwright/driver).
#
# multipart (python-multipart): bat buoc o IMPORT TIME — fastapi check
# "Form data requires python-multipart" khi routers.customers/properties/
# participants/ocr_ai dang ky route Form/File.
# fitz + pymupdf: PyMuPDF 1.24.x ca hai ten deu ton tai; engine dung
# "import fitz", sidecar command_registry dung "import pymupdf".
# rapidfuzz: hien chi fast_audit/tools CLI dung — khong reachable qua
# adapter; bundle san (~2MB) de phong command tuong lai, re hon them sau.
_ENGINE_DEP_PACKAGES = [
    'sqlalchemy',
    'docx',
    'lxml',
    'pymupdf',
    'fitz',
    'openpyxl',
    'PIL',
    'httpx',
    'rapidfuzz',
    'jinja2',
    'multipart',
    'pydantic',
    'pydantic_core',
    'dotenv',
    'tzdata',
    'playwright',
]
for _pkg in _ENGINE_DEP_PACKAGES:
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

# Word templates KHONG bundle: notary_adapter._resolve_template doc
# <engine_root>/word_templates/*.docx tu filesystem — datas=[] cho engine.
# sqlite3 la stdlib — PyInstaller tu bundle _sqlite3 + sqlite3.dll khi
# sqlalchemy.dialects.sqlite duoc phan tich.

a = Analysis(
    ['app.py'],
    pathex=[_FIXTURES] if _TEST_BUILD else [],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Qt/launcher khong bao gio vao runtime path (MIN-69 T9 req): PySide6
    # bi chan tuyet doi — ui_qt khong duoc di theo engine.
    excludes=[
        'PySide6', 'PyQt5', 'PyQt6', 'shiboken6',
        'tkinter',
        'matplotlib', 'numpy', 'pandas',
        'pytest', 'IPython',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='g1-shell-sidecar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='g1-shell-sidecar',
)
