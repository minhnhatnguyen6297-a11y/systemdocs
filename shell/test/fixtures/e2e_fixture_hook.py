"""MIN-69 T9 — E2E fixture hook cho TEST BUILD.

File nay CHI duoc PyInstaller dong goi khi `G1_SIDECAR_TEST_BUILD=1`
(xem g1-shell-sidecar.spec + test/build-upload-test.ps1). Ban production
khong ship module → env `G1_E2E_FIXTURE` la no-op ben production.

Dieu kien kich hoat (trusted harness channel): Electron main truyen
`G1_E2E_FIXTURE=1` qua env sidecar — renderer KHONG bao gio dat duoc env
nay, payload/IPC khong the bat fixture provider.

`install()` dang ky website portal gia lap (fake_portal*, loopback-only)
vao provider registry cua engine upload_lab trong bo nho process va ghi
loopback URL ra file `G1_E2E_STATE` cho harness doc. Khong sua engine.

Them lenh `diag.fixture_browser_launch`: mo that headless chromium
(playwright.sync_api) toi trang portal fixture localhost — chung minh goi
packaged tu launch duoc browser ma khong tai gi luc runtime.
"""

import json
import os
from urllib.parse import urlparse

PORTALS = {}  # website_id -> FakePortal


def _install_portals():
    import upload_portal as fixture

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
        # Website cho case upload: 31 ho so quet, mot so da co trong so
        # (601/2026 → khong chon mac dinh) va mot so sai nam (631/1999).
        "fake_portal_c": [
            ("Số công chứng", "Ngày công chứng"),
            ("601/2026", "15/04/2026"),
        ],
    }
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
        PORTALS[wid] = portal
    out = os.environ.get("G1_E2E_STATE")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(
                {"portals": {w: p.base_url for w, p in PORTALS.items()}},
                fh)


def _fixture_browser_launch(job, payload):
    """Chung minh playwright+chromium packaged hoat dong khong download.

    KHONG nhan URL tu payload — chi duyet trang portal fixture da dang ky
    (trusted channel), va assert them loopback.
    """
    from errors import CommandError
    from playwright.sync_api import sync_playwright

    portal = PORTALS.get("fake_portal") or next(iter(PORTALS.values()), None)
    if portal is None:
        raise CommandError("internal_error",
                           "fixture portal chua duoc dang ky")
    host = urlparse(portal.base_url).hostname
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise CommandError("internal_error",
                           f"fixture portal khong loopback: {host}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(portal.base_url, timeout=15_000)
            title = page.title()
        finally:
            browser.close()
    return {
        "kind": "diag_result",
        "data": {"title": title, "url": portal.base_url,
                 "headless": True},
        "evidence": [],
        "warnings": [],
    }


def install():
    _install_portals()
    # Lenh diag chi co o test build — production registry khong bao gio co.
    from command_registry import COMMANDS
    COMMANDS["diag.fixture_browser_launch"] = _fixture_browser_launch
