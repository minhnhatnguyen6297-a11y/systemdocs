# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_all

hiddenimports = []
datas = []
binaries = []
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('fastapi')

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
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
