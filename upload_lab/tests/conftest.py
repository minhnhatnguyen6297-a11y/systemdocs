"""Nạp đường dẫn cho test của Upload Lab.

Test trong `upload_lab/tests` import adapter consumer (`extraction_adapter`)
và lõi luật chung (`regex_workbench.engine.contract_extract`). pytest thêm
`upload_lab/` vào sys.path theo package `tests`; ở đây thêm `tools/` của
repo để lõi import được (dev = package dùng cùng đường dẫn này).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
