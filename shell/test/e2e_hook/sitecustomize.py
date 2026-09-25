"""MIN-69 task 7 — E2E hook, chi chay ben trong sidecar con cua Electron.

`sitecustomize` duoc Python tu import luc khoi dong khi folder nay nam tren
PYTHONPATH. Moi truong that khong dat PYTHONPATH nay → file la no-op o moi
tien trinh khac. Dieu kien kich hoat: SIDECAR_TOKEN co mat (chi sidecar con
cua Electron main moi co) — khong cham vao shell/test runner thuong.

Hook dang ky website portal gia lap (`fake_portal`, `fake_portal_b`,
`fake_portal_c`) vao provider registry cua engine upload_lab va ghi loopback
URL ra file G1_E2E_STATE de test doc duoc. KHONG sua sidecar/engine — chi
them provider fixture vao registry trong bo nho cua process test.

`fake_portal_c` phuc vu case `upload` cua test_upload_e2e.py: 31 ho so quet
(chunk 10), mot so da co trong Excel (601/2026 — khong duoc chon mac dinh),
mot so sai nam (631/1999 — issue).
"""

import json
import os
import sys

_HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
_SHELL = os.path.dirname(os.path.dirname(_HOOK_DIR))
for _p in (os.path.join(_SHELL, "sidecar"),
           os.path.join(_SHELL, "test", "fixtures")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _install():
    import upload_portal as fixture

    portals = {}
    datasets = {
        # So sach xuat ve cho tab Audit: thieu 103/2026, trung 104/2026.
        "fake_portal": [
            ("Số công chứng", "Ngày công chứng"),
            ("101/2026", "15/04/2026"),
            ("102/2026", "16/04/2026"),
            ("104/2026", "18/04/2026"),
            ("104/2026", "18/04/2026"),
            ("105/2026", "20/04/2026"),
        ],
        # Website thu hai — kiem doi website dung scope.
        "fake_portal_b": [
            ("Số công chứng", "Ngày công chứng"),
            ("301/2026", "05/05/2026"),
            ("302/2026", "06/05/2026"),
        ],
        # Website cho case --case upload: 31 ho so, mot so da co trong so
        # (601/2026 → khong chon mac dinh, prepare phai loai) va mot so sai
        # nam (631/1999 → issue, khong chon mac dinh).
        "fake_portal_c": [
            ("Số công chứng", "Ngày công chứng"),
            ("601/2026", "15/04/2026"),
        ],
    }
    # 31 hop dong quet duoc cho fake_portal_c — record i ung hop dong
    # "60{i}/2026/CCGD" (i=1..30) va "631/1999/CCGD" (i=31, sai nam).
    scan_contracts = {
        "fake_portal_c": [
            f"{600 + i}/2026/CCGD" for i in range(1, 31)
        ] + ["631/1999/CCGD"],
    }
    for wid, rows in datasets.items():
        portal = fixture.FakePortal()
        portal.export_rows = rows
        provider = fixture.register_fake_portal_website(
            portal, website_id=wid)
        provider.scan_contract_nos = scan_contracts.get(wid, [])
        portals[wid] = portal.base_url
    out = os.environ.get("G1_E2E_STATE")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"portals": portals}, fh)


if os.environ.get("SIDECAR_TOKEN"):
    try:
        _install()
    except Exception as exc:  # noqa: BLE001 — loi phai lo trong stderr log
        print(f"G1_E2E hook failed: {exc!r}", file=sys.stderr)
