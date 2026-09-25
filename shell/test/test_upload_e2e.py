"""MIN-69 task 7+9 — E2E Upload Lab qua Electron + CDP.

Hai che do app:

* Dev (khong --app): Electron binary dev + python sidecar, test hook
  `test/e2e_hook/sitecustomize.py` qua PYTHONPATH dang ky portal gia lap —
  khong cham sidecar, engine hay contract.
* Packaged (--app <exe>): goi electron-builder that — san pham tu spawn
  sidecar exe + engine/browsers trong resources/. Fixture chi duoc bat
  boi env `G1_E2E_FIXTURE=1` (trusted harness channel) va CHI hoat dong
  trong test package (marker `resources/test-pkg/test-build.json`);
  production khong ship hook → env la no-op.

Cases:

    python test/test_upload_e2e.py --case audit           # dev
    python test/test_upload_e2e.py --case upload          # dev
    python test/test_upload_e2e.py --app dist-app/win-unpacked/g1-shell.exe --case offline
    python test/test_upload_e2e.py --app dist-test/win-unpacked/g1-shell-test.exe --case all

`offline` (production package, khong portal): websites catalog khong co
fixture, diag.* khong ton tai, scan+audit_excel that qua engine trong
resources, moi ghi nam duoi userData (--user-data-dir), install dir khong
doi — ke ca khi bi chan ghi bang ACL deny.

`audit`/`upload`/`all` can portal gia lap → CHI chap nhan dev hoac test
package; production exe bi tu choi theo build label. `all` tren test
package them diag.fixture_browser_launch (chromium that, headless, toi
portal localhost) — chung minh playwright bundle khong can tai runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = HERE.parent
REPO = SHELL.parent
ELECTRON_EXE = SHELL / "node_modules" / "electron" / "dist" / "electron.exe"
HOOK_DIR = HERE / "e2e_hook"
FIXTURES = HERE / "fixtures"
SIDECAR = SHELL / "sidecar"

# Du lieu portal gia lap A — phai trung voi datasets trong e2e_hook.
PORTAL_A_ROWS = [
    ("Số công chứng", "Ngày công chứng"),
    ("101/2026", "15/04/2026"),
    ("102/2026", "16/04/2026"),
    ("104/2026", "18/04/2026"),
    ("104/2026", "18/04/2026"),
    ("105/2026", "20/04/2026"),
]
# Ky vong audit A (khoang 01/04/2026-31/05/2026, nam 2026):
#   excel_total=5, valid=3 (104x2 bi loai khoi clean vi trung),
#   missing={103/2026, 104/2026} → 2, issue=2 (hai dong trung_so).
A_KPIS = {"total": "5", "valid": "3", "missing": "2", "issue": "2"}


class E2EFail(RuntimeError):
    pass


def require(cond, msg):
    if not cond:
        raise E2EFail(msg)


def check_deps(python, app_exe=None):
    """Fail ro rang khi thieu Electron/fixture/python deps."""
    if app_exe is None:
        require(ELECTRON_EXE.is_file(),
                f"Thieu Electron dev binary: {ELECTRON_EXE} — chay "
                f"'npm install' trong shell/")
        require((HOOK_DIR / "sitecustomize.py").is_file(),
                f"Thieu e2e hook {HOOK_DIR / 'sitecustomize.py'}")
        require((SIDECAR / "app.py").is_file(),
                f"Thieu sidecar {SIDECAR / 'app.py'}")
        # Sidecar con chay bang G1_PYTHON (mac dinh = interpreter nay).
        probe = subprocess.run(
            [python, "-c", "import fastapi, uvicorn, openpyxl"],
            capture_output=True, text=True)
        require(probe.returncode == 0,
                f"Sidecar python '{python}' thieu fastapi/uvicorn/openpyxl: "
                f"{probe.stderr.strip()[-400:]}")
    require((FIXTURES / "upload_portal.py").is_file(),
            f"Thieu fixture upload_portal.py trong {FIXTURES}")
    for mod in ("openpyxl",):
        try:
            __import__(mod)
        except ImportError:
            raise E2EFail(
                f"Thieu python dep '{mod}' cho runner — pip install {mod}")
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        raise E2EFail(
            "Thieu 'playwright' cho driver CDP — pip install playwright "
            "(khong can 'playwright install': chi connect_over_cdp)")


def http_json(url, method="GET", body=None, timeout=15):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def build_label(app_exe: Path) -> str:
    """Nhan build cua goi — marker resources/test-pkg/test-build.json chi
    co trong dist:test. Khong co marker = production (production khong
    bao gio ship file nay)."""
    marker = (app_exe.parent / "resources" / "test-pkg"
              / "test-build.json")
    return "test" if marker.is_file() else "production"


def launch_app(tmp: Path, port: int, python: str, app_exe: Path = None):
    env = dict(os.environ)
    env["G1_E2E_STATE"] = str(tmp / "e2e-state.json")
    env["G1_E2E_PICK_FILES"] = str(tmp / "pick.json")
    # openPath seam: moi file duoc mo ghi mot dong vao log thay vi dep
    # app that (Word) — cung pattern G1_E2E_PICK_FILES. Chi dev/test
    # build ton trong seam; production bo qua hoan toan.
    env["G1_E2E_OPEN_LOG"] = str(tmp / "opened.log")
    env["ELECTRON_ENABLE_LOGGING"] = "1"
    # Trusted harness channel: chi env cua app spawn duoc truyen vao
    # sidecar. Production sidecar khong ship e2e_fixture_hook → no-op.
    env["G1_E2E_FIXTURE"] = "1"
    if app_exe is None:
        env["G1_PYTHON"] = python
        env["G1_UPLOAD_LAB_ROOT"] = str(REPO / "upload_lab")
        env["G1_UPLOAD_DATA_DIR"] = str(tmp / "upload_lab")
        env["G1_OUTPUT_DIR"] = str(tmp / "output")
        # F3 (T9 review): _install_e2e_fixtures can CA G1_BUILD_LABEL=test
        # LAN G1_E2E_FIXTURE=1 — dev harness la trusted channel nhu
        # packaged test build (marker). Production packaged van force
        # label qua config.js nen khong the bi env nay sua.
        env["G1_BUILD_LABEL"] = "test"
        env["PYTHONPATH"] = os.pathsep.join(
            [str(HOOK_DIR), str(FIXTURES), str(SIDECAR),
             env.get("PYTHONPATH", "")])
        cmd = [str(ELECTRON_EXE), str(SHELL)]
    else:
        # Packaged: KHONG dat G1_UPLOAD_DATA_DIR/G1_OUTPUT_DIR — sidecar
        # phai resolve vao <userData>/upload_lab + <userData>/output
        # (Writable data root check; task 9). Engine/browser trong
        # resources qua env do main.js truyen.
        cmd = [str(app_exe)]
    stderr = open(tmp / "electron.stderr.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd + [f"--remote-debugging-port={port}",
               f"--user-data-dir={tmp / 'user-data'}",
               "--no-first-run", "--no-default-browser-check"],
        env=env, stdout=subprocess.DEVNULL, stderr=stderr)
    return proc, stderr


def wait_cdp(port: int, proc, timeout_s=60):
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if proc.poll() is not None:
            raise E2EFail(f"Electron exit som (code {proc.returncode}) — "
                          f"xem electron.stderr.log trong thu muc tmp")
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(0.4)
    raise E2EFail(f"CDP {url} khong len sau {timeout_s}s")


def wait_state_file(tmp: Path, timeout_s=60):
    path = tmp / "e2e-state.json"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        time.sleep(0.4)
    raise E2EFail("Sidecar hook khong ghi e2e-state.json — sitecustomize "
                  "khong chay hoac import loi (xem sidecar.err trong log)")


def write_pick(tmp: Path, paths):
    (tmp / "pick.json").write_text(
        json.dumps({"files": [str(p) for p in paths]}, ensure_ascii=False),
        encoding="utf-8")


# ---------- fixture control channel (fake portal, khong phai API that) -------

def fctl(base: str, **kw):
    """POST /__fixture__/control — fail_record_ids, record_delay_s,
    fail_next_export, block=[scan|prepare|open], release=[...]"""
    return http_json(f"{base}/__fixture__/control", method="POST", body=kw)


def fuser(base: str, action: str, record_id=None):
    body = {"action": action}
    if record_id is not None:
        body["record_id"] = record_id
    return http_json(f"{base}/__fixture__/user", method="POST", body=body)


def fstate(base: str):
    return http_json(f"{base}/__fixture__/state")


def sql_rows(db_path: Path, query: str, params=()):
    conn = sqlite3.connect(str(db_path), timeout=15)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(query, params)]
    finally:
        conn.close()


def write_xlsx(path: Path, rows):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(list(r))
    wb.save(str(path))


def kpi(page, name):
    sel = f'#ul-panel-audit .ul-kpi[data-kpi="{name}"] .ul-kpi-v'
    return page.eval_on_selector(sel, "e => e.textContent")


def wait_kpi(page, name, value, timeout=30000):
    sel = f'#ul-panel-audit .ul-kpi[data-kpi="{name}"] .ul-kpi-v'
    page.wait_for_function(
        "(a) => { const e = document.querySelector(a.sel);"
        " return e && e.textContent === a.v; }",
        arg={"sel": sel, "v": str(value)}, timeout=timeout)


def audit_table_text(page, which):
    # which: 0 = So con thieu, 1 = So loi, trung
    return page.eval_on_selector_all(
        "#ul-panel-audit .ul-table-wrap tbody",
        f"els => els[{which}] ? els[{which}].innerText : ''")


def dump_debug(page):
    """In trang thai DOM/job khi mot buoc fail — goi trong except."""
    if page is None:
        return
    try:
        info = page.evaluate(
            """() => {
              const lab = document.querySelector('.upload-lab');
              const jobs = [...document.querySelectorAll(
                '.upload-lab .slot *')].map(e => e.textContent).join('|');
              const sel = document.querySelector(
                '#ul-panel-audit select.ul-site');
              const cont = [...document.querySelectorAll(
                '#ul-panel-scan-upload button')]
                .find(b => b.textContent.includes('Tiếp tục'));
              return {
                has_lab: !!lab,
                site_val: sel ? sel.value : null,
                cont_gate: cont ? cont.dataset.gate || null : null,
                notice: (document.querySelector('.ul-notice') || {})
                          .innerText || '',
                jobs: jobs.slice(0, 8000),
                lab_text: lab ? lab.innerText.slice(0, 2000) : null,
              };
            }""")
        print(f"--- page debug ---\n{json.dumps(info, ensure_ascii=False, indent=2)}",
              file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print(f"(debug dump failed: {exc})", file=sys.stderr)


def case_audit(page, portals, tmp):
    a_url = portals["fake_portal"]
    b_url = portals["fake_portal_b"]

    # -- Dung 2 tab, dropdown truoc bo loc ngay, khong o URL, khong Nhat ky
    tabs = page.eval_on_selector_all(
        '.ul-tablist [role="tab"]', "els => els.map(e => e.textContent)")
    require(tabs == ["Audit Sổ Công Chứng", "Quét & Upload Hồ Sơ"],
            f"tab list sai: {tabs}")
    ordered = page.evaluate(
        """() => {
          const sel = document.querySelector('#ul-panel-audit select.ul-site');
          const from = document.querySelector(
            '#ul-panel-audit input[aria-label="Từ ngày"]');
          return !!(sel && from &&
            (sel.compareDocumentPosition(from) &
             Node.DOCUMENT_POSITION_FOLLOWING));
        }""")
    require(ordered, "dropdown website phai nam TRUOC bo loc ngay")
    url_inputs = page.eval_on_selector_all(
        ".upload-lab input",
        "els => els.filter(e => e.type === 'url' || "
        "  /https?/i.test(e.placeholder || '')).length")
    require(url_inputs == 0, "co o nhap URL tu do trong Upload Lab")
    lab_text = page.eval_on_selector(".upload-lab", "e => e.innerText")
    require("Nhật ký" not in lab_text, "con trang/nhan Nhat ky")

    # -- Chon website gia lap A (catalog tu backend)
    page.wait_for_function(
        """() => [...document.querySelectorAll(
             '#ul-panel-audit select.ul-site option')]
             .some(o => o.value === 'fake_portal')""",
        timeout=60000)
    page.select_option("#ul-panel-audit select.ul-site", "fake_portal")
    page.wait_for_function(
        """() => {
          const s = document.querySelector('#ul-panel-audit select.ul-site');
          const u = document.querySelector('#ul-panel-audit .ul-site-url');
          return s && s.value === 'fake_portal' && u &&
                 u.textContent.includes('127.0.0.1');
        }""", timeout=30000)
    require(a_url in page.eval_on_selector(
        "#ul-panel-audit .ul-site-url", "e => e.textContent"),
        "display_url khong phai portal gia lap A")

    # -- Kiem tra moi truong
    page.click("#ul-panel-audit button:has-text('Kiểm tra môi trường')")
    page.wait_for_selector(
        "#ul-panel-audit .ul-env :text('đạt')", timeout=30000)

    # -- Mo dang nhap → banner cho → user login tren portal gia → xac nhan
    page.click("#ul-panel-audit button:has-text('Mở đăng nhập')")
    page.wait_for_selector(
        ".ul-notice .ul-login-confirm:not([disabled])", timeout=30000)
    http_json(f"{a_url}/api/login", method="POST", body={})
    page.click(".ul-notice .ul-login-confirm")
    page.wait_for_function(
        """() => {
          const b = document.querySelector(
            '#ul-panel-audit .ul-badge-slot .ul-badge');
          return b && b.textContent.includes('Đã đăng nhập');
        }""", timeout=30000)

    # -- Bo loc ngay DD/MM/YYYY (wire ISO o tang duoi)
    page.fill('#ul-panel-audit input[aria-label="Từ ngày"]', "01/04/2026")
    page.dispatch_event(
        '#ul-panel-audit input[aria-label="Từ ngày"]', "change")
    page.fill('#ul-panel-audit input[aria-label="Đến ngày"]', "30/04/2026")
    page.dispatch_event(
        '#ul-panel-audit input[aria-label="Đến ngày"]', "change")

    # -- Tai Excel tu web → tu nap audit
    page.click("#ul-panel-audit button:has-text('Tải Excel từ Web')")
    page.wait_for_selector("#ul-panel-audit .ul-audit-head", timeout=60000)
    head = page.eval_on_selector(
        "#ul-panel-audit .ul-audit-head", "e => e.textContent")
    require("fake_portal" in head and "01/04/2026" in head and
            "30/04/2026" in head,
            f"audit head sai scope: {head}")
    for k, v in A_KPIS.items():
        wait_kpi(page, k, v)
    miss = audit_table_text(page, 0)
    iss = audit_table_text(page, 1)
    require("103/2026" in miss and "104/2026" in miss,
            f"bang thieu sai: {miss!r}")
    require("trung_so" in iss and iss.count("104/2026") >= 2,
            f"bang loi/trung sai: {iss!r}")

    # -- Doi ngay → ket qua cu danh dau chua cap nhat, khong bi coi la moi
    page.fill('#ul-panel-audit input[aria-label="Đến ngày"]', "31/05/2026")
    page.dispatch_event(
        '#ul-panel-audit input[aria-label="Đến ngày"]', "change")
    page.wait_for_selector("#ul-panel-audit .ul-stale", timeout=10000)

    # -- Nap lai → sach
    page.click("#ul-panel-audit button:has-text('Nạp dữ liệu')")
    page.wait_for_function(
        """() => {
          const s = document.querySelector('#ul-panel-audit .ul-stale');
          const hd = document.querySelector('#ul-panel-audit .ul-audit-head');
          return (!s || s.hidden || s.offsetParent === null) &&
                 hd && hd.textContent.includes('31/05/2026');
        }""", timeout=60000)

    # -- Chon .xlsm qua picker stub → tu nap audit
    picked = tmp / "picked.xlsm"
    write_xlsx(picked, [
        ("Số công chứng", "Ngày công chứng"),
        ("201/2026", "05/05/2026"),
        ("202/2026", "06/05/2026"),
    ])
    write_pick(tmp, [picked])
    page.click("#ul-panel-audit button:has-text('Chọn tệp Excel')")
    wait_kpi(page, "total", "2")
    wait_kpi(page, "valid", "2")
    wait_kpi(page, "missing", "0")
    wait_kpi(page, "issue", "0")
    path_in = page.eval_on_selector(
        '#ul-panel-audit input[aria-label="Đường dẫn tệp Excel"]',
        "e => e.value")
    require("picked.xlsm" in path_in, f"path hien sai: {path_in}")

    # -- Loi nap xoa ket qua hien hanh + bao loi tai cho
    bad = tmp / "bad.xlsx"
    bad.write_bytes(b"day khong phai file excel")
    write_pick(tmp, [bad])
    page.click("#ul-panel-audit button:has-text('Chọn tệp Excel')")
    page.wait_for_selector("#ul-panel-audit .ul-src-msg .ul-error",
                           timeout=30000)
    require(kpi(page, "total") == "0", "KPI cu con sau loi nap")
    head_hidden = page.eval_on_selector(
        "#ul-panel-audit .ul-audit-head",
        "e => e.hidden || e.offsetParent === null")
    require(head_hidden, "audit head con hien sau loi nap")

    # -- Chon lai file tot → ket qua phuc hoi
    write_pick(tmp, [picked])
    page.click("#ul-panel-audit button:has-text('Chọn tệp Excel')")
    wait_kpi(page, "total", "2")

    # -- Doi website → scope A xoa sach; ket qua/loi tre cua A bi bo qua
    page.select_option("#ul-panel-audit select.ul-site", "fake_portal_b")
    page.wait_for_function(
        """() => {
          const s = document.querySelector('#ul-panel-audit select.ul-site');
          const u = document.querySelector('#ul-panel-audit .ul-site-url');
          return s && s.value === 'fake_portal_b' && u &&
                 u.textContent.includes('127.0.0.1');
        }""", timeout=30000)
    require(b_url in page.eval_on_selector(
        "#ul-panel-audit .ul-site-url", "e => e.textContent"),
        "display_url khong phai portal gia lap B")
    require(kpi(page, "total") == "0", "KPI cua website A con sot lai")
    require(page.eval_on_selector(
        "#ul-panel-audit .ul-audit-head",
        "e => e.hidden || e.offsetParent === null"),
        "audit head cua A con hien tren website B")
    badge = page.eval_on_selector(
        "#ul-panel-audit .ul-badge-slot .ul-badge", "e => e.textContent")
    require("Chưa đăng nhập" in badge,
            f"badge dang nhap cua A con sot: {badge}")
    # Job/env tre cua A den sau khi doi → van khong lam song lai so lieu A.
    page.click("#ul-panel-audit button:has-text('Kiểm tra môi trường')")
    page.wait_for_selector(
        "#ul-panel-audit .ul-env :text('đạt')", timeout=30000)
    time.sleep(1.0)  # cho cac update tre (neu co) den roi assert lai
    require(kpi(page, "total") == "0",
            "ket qua audit cua website A bi ap lai sau khi doi website")


# =================== --case upload (MIN-69 task 8) ===================
#
# Luong Qt-equivalent tren `fake_portal_c` (31 ho so, chunk 10):
#   login → audit → quet co gate (doi tab giua chung) → bo loc chon full
#   → double-click mo file → prepare dot 1 (loi record 3, bo chon record 5,
#   so 601 da co Excel) → cho review → Save 2 → finish → Tiep tuc co delay
#   → Dung giua chung → Dong browser → restart app → doi chieu → mo lai
#   phien → quet run B → submit record run A bi scope_violation, khong mo
#   tab nao.
# Moi assert deu qua ba lop: UI (CDP) + workspace/registry sqlite + trang
# thai tab tren fixture portal — khong chi kiem nut.

class AppInstance:
    """Vong doi app Electron cho case can restart giua chung."""

    def __init__(self, tmp: Path, port: int, python: str,
                 app_exe: Path = None, expect_portals: bool = True):
        self.tmp = tmp
        self.port = port
        self.python = python
        self.app_exe = app_exe
        self.expect_portals = expect_portals
        self.proc = None
        self.stderr_fh = None
        self.portals = {}

    @property
    def packaged(self) -> bool:
        return self.app_exe is not None

    @property
    def user_data_dir(self) -> Path:
        return self.tmp / "user-data"

    @property
    def data_dir(self) -> Path:
        """G1_UPLOAD_DATA_DIR thuc te cua sidecar."""
        if self.packaged:
            # Default packaged: <userData>/upload_lab (sidecar.js
            # _defaultUploadDataDir) — harness khong dat env override.
            return self.user_data_dir / "upload_lab"
        return self.tmp / "upload_lab"

    def start(self):
        self.proc, self.stderr_fh = launch_app(
            self.tmp, self.port, self.python, app_exe=self.app_exe)
        wait_cdp(self.port, self.proc)
        if self.expect_portals:
            state = wait_state_file(self.tmp)
            self.portals = state.get("portals") or {}
        else:
            self.portals = {}
        return self.portals

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.proc.pid), "/T", "/F"],
                    capture_output=True)
            else:
                self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.stderr_fh is not None:
            self.stderr_fh.close()
            self.stderr_fh = None

    def restart(self):
        """Giet app va mo lai cung data dir — mo phong user tat/mo shell."""
        self.stop()
        # e2e-state.json ghi lai khi sidecar con boot — xoa de cho file moi
        # (portal dang ky port ngau nhien moi moi lan).
        if self.expect_portals:
            (self.tmp / "e2e-state.json").unlink(missing_ok=True)
        return self.start()


def connect_page(pw, port: int):
    """Connect CDP + mo module Upload Lab; tra (browser, page)."""
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    ctx = browser.contexts[0]
    page = None
    deadline = time.time() + 60
    while time.time() < deadline and page is None:
        for p in ctx.pages:
            if "index.html" in (p.url or ""):
                page = p
                break
        if page is None:
            time.sleep(0.5)
    require(page is not None, "khong tim thay cua so index.html qua CDP")
    page.wait_for_selector('#module-list li[data-id="upload"]',
                           timeout=60000)
    page.click('#module-list li[data-id="upload"]')
    page.wait_for_selector(".upload-lab", timeout=30000)
    return browser, page


def scan_row_count(page):
    return page.eval_on_selector_all(
        '#ul-panel-scan-upload tbody tr[data-k]',
        "els => els.length")


def scan_checked_count(page):
    return page.eval_on_selector_all(
        '#ul-panel-scan-upload tbody tr[data-k] input[type=checkbox]',
        "els => els.filter(c => c.checked).length")


def wait_checked(page, n, timeout=20000):
    page.wait_for_function(
        "n => [...document.querySelectorAll("
        "'#ul-panel-scan-upload tbody tr[data-k] input[type=checkbox]')]"
        ".filter(c => c.checked).length === n",
        arg=n, timeout=timeout)


def wait_rows(page, n, timeout=30000):
    page.wait_for_function(
        "n => document.querySelectorAll("
        "'#ul-panel-scan-upload tbody tr[data-k]').length === n",
        arg=n, timeout=timeout)


def row_checked(page, record_id):
    return page.evaluate(
        "id => { const tr = document.querySelector("
        "'#ul-panel-scan-upload tbody tr[data-k=\"' + id + '\"]');"
        " const c = tr && tr.querySelector('input[type=checkbox]');"
        " return c ? c.checked : null; }",
        arg=str(record_id))


def prep_label(page):
    return page.eval_on_selector_all(
        "#ul-panel-scan-upload .ul-progress-label",
        "els => els[1] ? els[1].textContent : ''")


def submit_and_wait(page, command, payload, timeout_s=40):
    """submitCommand truc tiep qua preload (test seam cho scope-violation —
    UI khong bao gio tu tao payload nay)."""
    return page.evaluate(
        """async ({command, payload, timeout}) => {
          const api = window.desktop.v1;
          const r = await api.submitCommand(
            command, payload, crypto.randomUUID());
          if (!r.ok) return {submit_error: r.error};
          const id = r.data.job_id;
          const t0 = Date.now();
          while (Date.now() - t0 < timeout * 1000) {
            const jr = await api.getJob(id);
            const job = jr && jr.ok ? jr.data : null;
            if (job && ['succeeded','failed','canceled','partial']
                .includes(job.status)) return job;
            await new Promise(rs => setTimeout(rs, 300));
          }
          return {timeout: true, job_id: id};
        }""",
        {"command": command,
         "payload": {"workflow_version": "upload.workflow.v1", **payload},
         "timeout": timeout_s})


def ul_login(page, base):
    """Mo dang nhap → user login tren portal gia → xac nhan."""
    page.click("#ul-panel-audit button:has-text('Mở đăng nhập')")
    page.wait_for_selector(
        ".ul-notice .ul-login-confirm:not([disabled])", timeout=30000)
    http_json(f"{base}/api/login", method="POST", body={})
    page.click(".ul-notice .ul-login-confirm")
    page.wait_for_function(
        """() => {
          const b = document.querySelector(
            '#ul-panel-audit .ul-badge-slot .ul-badge');
          return b && b.textContent.includes('Đã đăng nhập');
        }""", timeout=30000)


def ul_wait_review_banner(page, timeout=60000):
    page.wait_for_selector(
        ".ul-notice button:has-text('Xong kiểm tra'):not([disabled])",
        timeout=timeout)


def wait_open_ids_gt(base, n, timeout=30000):
    # timeout theo ms (cung quy uoc playwright trong file nay).
    deadline = time.time() + timeout / 1000
    st = {}
    while time.time() < deadline:
        st = fstate(base)
        if len(st["session"]["open_record_ids"]) > n:
            return st["session"]["open_record_ids"]
        time.sleep(0.3)
    raise E2EFail(
        f"open_record_ids khong vuot {n}: {st.get('session')}")


def case_upload(app: AppInstance, pw, tmp: Path):
    wsdb = app.data_dir / "workspace.sqlite3"
    regdb = (app.data_dir / "websites" / "fake_portal_c"
             / "registry.sqlite3")
    folder = tmp / "hs-scan"
    folder.mkdir(parents=True, exist_ok=True)

    base = app.portals.get("fake_portal_c")
    require(base, f"e2e-state thieu fake_portal_c: {app.portals}")

    browser, page = connect_page(pw, app.port)
    try:
        # -- Website + env + login + download Excel → audit -------------
        page.wait_for_function(
            """() => [...document.querySelectorAll(
                 '#ul-panel-audit select.ul-site option')]
                 .some(o => o.value === 'fake_portal_c')""",
            timeout=60000)
        page.select_option("#ul-panel-audit select.ul-site",
                           "fake_portal_c")
        page.wait_for_function(
            """() => {
              const s = document.querySelector(
                '#ul-panel-audit select.ul-site');
              return s && s.value === 'fake_portal_c';
            }""", timeout=30000)
        page.click("#ul-panel-audit button:has-text('Kiểm tra môi trường')")
        page.wait_for_selector(
            "#ul-panel-audit .ul-env :text('đạt')", timeout=30000)
        ul_login(page, base)
        page.click("#ul-panel-audit button:has-text('Tải Excel từ Web')")
        page.wait_for_selector("#ul-panel-audit .ul-audit-head",
                               timeout=60000)
        wait_kpi(page, "total", "1")
        wait_kpi(page, "valid", "1")
        wait_kpi(page, "missing", "0")

        # -- Tab Quét: pick folder, chan scan, doi tab giua chung --------
        page.click("#ul-tab-scan-upload")
        write_pick(tmp, [folder])
        page.click("#ul-panel-scan-upload button:has-text('Chọn thư mục')")
        page.wait_for_function(
            """() => {
              const i = document.querySelector(
                '#ul-panel-scan-upload input[aria-label="Đường dẫn thư mục"]');
              return i && i.value.length > 0;
            }""", timeout=15000)
        fctl(base, block=["scan"])
        page.click("#ul-panel-scan-upload button:has-text('Bắt đầu Quét')")
        page.wait_for_function(
            """() => {
              const l = document.querySelectorAll(
                '#ul-panel-scan-upload .ul-progress-label')[0];
              return l && l.textContent !== 'Chưa quét.';
            }""", timeout=30000)
        # Doi tab giua scan: state/progress giu nguyen, KPI audit con nguyen.
        page.click("#ul-tab-audit")
        require(kpi(page, "total") == "1",
                "KPI audit mat sau khi doi tab giua scan")
        page.click("#ul-tab-scan-upload")
        fctl(base, release=["scan"])
        wait_rows(page, 31, timeout=60000)
        wait_checked(page, 29)
        # So da co trong Excel (601) va so sai nam (631/1999) khong chon.
        require(row_checked(page, 1) is False,
                "record da co trong Excel van duoc chon mac dinh")
        require(row_checked(page, 31) is False,
                "record issue (sai nam) duoc chon mac dinh")
        has_issue = page.eval_on_selector(
            '#ul-panel-scan-upload tbody tr[data-k="31"]',
            "e => e.className.includes('ul-row-issue')")
        require(has_issue, "record sai nam thieu class ul-row-issue")

        # -- Bo loc chon day du ----------------------------------------
        page.click("#ul-panel-scan-upload button:has-text('Chọn tất cả')")
        wait_checked(page, 31)
        page.click("#ul-panel-scan-upload button:has-text('Lọc số lỗi')")
        wait_checked(page, 30)
        page.wait_for_selector(
            "#ul-panel-scan-upload button:has-text('Hoàn tác lọc số lỗi')",
            timeout=10000)
        page.click(
            "#ul-panel-scan-upload button:has-text('Hoàn tác lọc số lỗi')")
        wait_checked(page, 31)
        page.click(
            "#ul-panel-scan-upload button:has-text('Bỏ chọn tất cả')")
        wait_checked(page, 0)
        page.click(
            "#ul-panel-scan-upload button:has-text('Số thiếu trong Excel')")
        wait_checked(page, 29)
        # Bo chon thu cong record 5 — phai song qua cac nhip poll sau.
        page.click(
            '#ul-panel-scan-upload tbody tr[data-k="5"] '
            'input[type=checkbox]')
        wait_checked(page, 28)

        # -- Double-click mo file nguon (G1_E2E_OPEN_LOG seam o main) --
        # openPath that qua preload → IPC → validate → log file. Page-side
        # stub khong the dung: contextBridge freeze desktop.v1.
        page.dblclick(
            '#ul-panel-scan-upload tbody tr[data-k="6"] td:nth-child(4)')
        opened_log = tmp / "opened.log"
        deadline = time.time() + 15
        while time.time() < deadline and not (
                opened_log.is_file()
                and opened_log.read_text(
                    encoding="utf-8", errors="replace").strip()):
            time.sleep(0.3)
        lines = opened_log.read_text(
            encoding="utf-8", errors="replace").splitlines()
        require(lines and lines[0].endswith("HD-006.docx"),
                f"dblclick mo sai file: {lines}")

        # -- Prepare dot 1: loi record 3, chunk 10 ------------------------
        fctl(base, fail_record_ids=[3])
        page.click(
            "#ul-panel-scan-upload button:has-text('Upload file đã chọn')")
        ul_wait_review_banner(page)
        st = fstate(base)["session"]
        require(st["prepare_calls"] == 1,
                f"prepare_calls={st['prepare_calls']}")
        require(st["last_prepare_kwargs"]["chunk_size"] == 10,
                f"chunk_size gui di: {st['last_prepare_kwargs']}")
        sent = sorted(st["last_prepare_kwargs"]["selected_record_ids"])
        require(len(sent) == 28 and 5 not in sent and 1 not in sent
                and 31 not in sent,
                f"record_ids gui di sai: {sent}")
        require(sorted(st["open_record_ids"]) ==
                [2, 4, 6, 7, 8, 9, 10, 11, 12],
                f"tab mo sau dot 1: {st['open_record_ids']}")
        run_a = sql_rows(
            wsdb, "SELECT run_id FROM runs ORDER BY created_at, rowid "
                  "LIMIT 1")[0]["run_id"]
        reg = sql_rows(
            regdb,
            "SELECT id, status FROM file_registry WHERE run_id = ? "
            "ORDER BY id", (run_a,))
        by_id = {r["id"]: r["status"] for r in reg}
        require(by_id.get(3) == "upload_failed",
                f"record 3 phai upload_failed: {by_id.get(3)}")
        require(sum(1 for s in by_id.values() if s == "prepared_dry_run")
                == 9, f"prepared_dry_run sai: {by_id}")

        # -- Doi tab trong luc cho review: selection + banner giu nguyen --
        page.click("#ul-tab-audit")
        require(kpi(page, "total") == "1",
                "KPI audit mat sau khi doi tab giua cho review")
        page.click("#ul-tab-scan-upload")
        page.wait_for_selector(
            ".ul-notice button:has-text('Xong kiểm tra')", timeout=10000)
        require(row_checked(page, 5) is False,
                "bo chon thu cong bi mat sau khi doi tab")

        # -- Save 2 tren portal → hang roi bang ngay (Save-awareness) -----
        fuser(base, "save", 2)
        fuser(base, "save", 4)
        page.wait_for_function(
            """() => !document.querySelector(
                 '#ul-panel-scan-upload tbody tr[data-k="2"]')""",
            timeout=30000)
        require(row_checked(page, 4) is None,
                "row 4 (da Lưu) van con trong bang")

        # -- Finish review → terminal partial + con lai -------------------
        page.click(".ul-notice button:has-text('Xong kiểm tra')")
        page.wait_for_function(
            """() => {
              const l = [...document.querySelectorAll(
                '#ul-panel-scan-upload .ul-progress-label')][1];
              return l && /Còn \\d+/.test(l.textContent);
            }""", timeout=60000)
        require("19" in prep_label(page),
                f"con lai sau dot 1 phai la 19: {prep_label(page)}")
        page.wait_for_selector(
            "#ul-panel-scan-upload .ul-prepare-error:not([hidden])",
            timeout=15000)
        reg = sql_rows(regdb,
                       "SELECT status FROM file_registry WHERE id IN (2,4)")
        require(all(r["status"] == "uploaded_success" for r in reg)
                and len(reg) == 2,
                f"saved records chua uploaded_success: {reg}")

        # -- Tiep tuc co delay → Dung giua chung → KHONG tu chay dot moi --
        fctl(base, fail_record_ids=[], record_delay_s=1.0)
        page.click("#ul-panel-scan-upload button:has-text('Tiếp tục')")
        wait_open_ids_gt(base, 7, timeout=30000)
        page.click("#ul-panel-scan-upload button:has-text('Dừng')")
        page.wait_for_function(
            """() => {
              const l = [...document.querySelectorAll(
                '#ul-panel-scan-upload .ul-progress-label')][1];
              return l && /Còn \\d+|Chưa chuẩn bị/.test(l.textContent);
            }""", timeout=30000)
        calls = fstate(base)["session"]["prepare_calls"]
        open_after = fstate(base)["session"]["open_record_ids"]
        time.sleep(2.5)  # ~2 record nua neu auto-continue — phai dung im
        st2 = fstate(base)["session"]
        require(st2["prepare_calls"] == calls,
                "tu chay them dot sau khi Dung (prepare_calls tang)")
        # Tiep tuc phai gui lai DUNG tap goc cua dot (activeUploadIds —
        # gom ca 2/4 da Luu, engine tu loai), KHONG doc lai checkbox hien
        # tai sau Save-awareness (26) — nhan nham se bo sot ho so dot.
        require(
            sorted(st2["last_prepare_kwargs"]["selected_record_ids"])
            == sent,
            f"record_ids dot Tiep tuc phai bang tap goc {sent}, "
            f"nhan {st2['last_prepare_kwargs']['selected_record_ids']}")
        require(sorted(st2["open_record_ids"]) == sorted(open_after),
                "tab mo thay doi sau khi Dung — co dot chay ngam")

        # -- Dong browser → tab con mo → needs_reconcile ------------------
        # needs_reconcile = cac tab dot 1 da giao cho user kiem tra va
        # store con track: {6..12} tru 2/4 da Luu. Tab mo trong dot 2 bi
        # Dung chua kip dang ky open_tabs (add_open_tabs dat SAU cho
        # review) → registry giu prepared_dry_run, khong phai "unknown".
        want_needs = [6, 7, 8, 9, 10, 11, 12]
        page.click(
            "#ul-panel-scan-upload button:has-text('Đóng browser upload')")
        page.wait_for_selector(
            "#ul-panel-scan-upload .ul-reconcile:not([hidden])",
            timeout=60000)
        banner = page.eval_on_selector(
            "#ul-panel-scan-upload .ul-reconcile", "e => e.textContent")
        require(str(len(want_needs)) in banner,
                f"banner doi chieu khong dem {len(want_needs)}: {banner}")
        needs = sql_rows(wsdb,
                         "SELECT record_id FROM needs_reconcile "
                         "WHERE website_id='fake_portal_c'")
        require(sorted(r["record_id"] for r in needs) == want_needs,
                f"needs_reconcile DB sai: {needs} vs {want_needs}")
        require(not sql_rows(wsdb, "SELECT record_id FROM open_tabs "
                             "WHERE website_id='fake_portal_c'"),
                "open_tabs con sot sau session_close")
        st = fstate(base)["session"]
        require(st["closed"], "session fixture chua dong")
        # Hang chua xac dinh KHONG bien mat khoi bang va duoc danh dau.
        wait_rows(page, 29, timeout=60000)
        marked = page.eval_on_selector_all(
            "#ul-panel-scan-upload tbody tr.ul-row-reconcile",
            "els => els.length")
        require(marked == len(want_needs),
                f"bang khong danh dau {len(want_needs)} dong doi chieu: "
                f"{marked}")
        # Trong luc can doi chieu, nut upload khong duoc mo retry mu:
        # prepare moi phai bi chan (guard o UI + backend).
    except BaseException:
        dump_debug(page)
        raise
    finally:
        browser.close()

    # ---------- restart: recovery phai song qua app restart ------------
    app.restart()
    base = app.portals["fake_portal_c"]
    browser, page = connect_page(pw, app.port)
    try:
        # Website + run khoi phuc; banner doi chieu hien lai (§6.15/§8).
        page.wait_for_function(
            """() => {
              const s = document.querySelector(
                '#ul-panel-audit select.ul-site');
              return s && s.value === 'fake_portal_c';
            }""", timeout=60000)
        page.click("#ul-tab-scan-upload")
        page.wait_for_selector(
            "#ul-panel-scan-upload .ul-reconcile:not([hidden])",
            timeout=90000)
        wait_rows(page, 29, timeout=60000)  # 31 - 2 da Lưu
        need_ids = [r["record_id"] for r in sql_rows(
            wsdb, "SELECT record_id, run_id FROM needs_reconcile "
                  "WHERE website_id='fake_portal_c'")]
        require(sorted(need_ids) == want_needs,
                f"needs_reconcile khong song qua restart: {need_ids}")
        marked = page.eval_on_selector_all(
            "#ul-panel-scan-upload tbody tr.ul-row-reconcile",
            "els => els.length")
        require(marked == len(want_needs),
                f"bang khong danh dau {len(want_needs)} dong can doi "
                f"chieu: {marked}")

        # -- Reconcile: audit MOI chua so do → verified → mo khoa ---------
        contracts = sql_rows(
            regdb,
            "SELECT contract_no FROM file_registry WHERE id IN (%s)"
            % ",".join("?" * len(need_ids)),
            tuple(need_ids))
        fresh = tmp / "so_doi_chieu.xlsx"
        write_xlsx(fresh, [("Số công chứng", "Ngày công chứng")] + [
            (r["contract_no"].replace("/CCGD", ""), "12/05/2026")
            for r in contracts])
        page.click("#ul-tab-audit")
        write_pick(tmp, [fresh])
        page.click("#ul-panel-audit button:has-text('Chọn tệp Excel')")
        page.wait_for_selector("#ul-panel-audit .ul-audit-head",
                               timeout=60000)
        page.click("#ul-tab-scan-upload")
        page.click("#ul-panel-scan-upload .ul-reconcile-btn")
        page.wait_for_function(
            """() => {
              const b = document.querySelector(
                '#ul-panel-scan-upload .ul-reconcile');
              return !b || b.hidden;
            }""", timeout=60000)
        require(not sql_rows(wsdb,
                             "SELECT record_id FROM needs_reconcile "
                             "WHERE website_id='fake_portal_c'"),
                "needs_reconcile con sot sau reconcile thanh cong")
        ok = sql_rows(regdb,
                      "SELECT status FROM file_registry WHERE id IN (%s)"
                      % ",".join("?" * len(need_ids)), tuple(need_ids))
        require(all(r["status"] == "uploaded_success" for r in ok),
                f"reconcile khong ghi uploaded_success: {ok}")

        # -- Mo lai phien + quet run B → scope_violation ------------------
        page.click("#ul-tab-audit")
        ul_login(page, base)
        page.click("#ul-tab-scan-upload")
        write_pick(tmp, [folder])
        page.click("#ul-panel-scan-upload button:has-text('Chọn thư mục')")
        page.click("#ul-panel-scan-upload button:has-text('Bắt đầu Quét')")
        wait_rows(page, 31, timeout=60000)
        run_b = sql_rows(wsdb,
                         "SELECT run_id FROM runs ORDER BY created_at DESC,"
                         " rowid DESC LIMIT 1")[0]["run_id"]
        bid = sql_rows(wsdb,
                       "SELECT browser_id FROM browsers WHERE status='open'"
                       " ORDER BY created_at DESC LIMIT 1")
        require(bid, "khong co browser mo sau khi dang nhap lai")
        qg = submit_and_wait(page, "upload.queue_get", {
            "website_id": "fake_portal_c", "run_id": run_b,
            "audit_id": None})
        require(qg and qg.get("status") == "succeeded",
                f"queue_get run B loi: {qg}")
        qd = (qg.get("result") or {}).get("data") or {}
        bogus = submit_and_wait(page, "upload.prepare", {
            "website_id": "fake_portal_c",
            "browser_id": bid[0]["browser_id"],
            "run_id": run_b,
            "audit_id": qd.get("audit_id"),
            "queue_revision": qd.get("queue_revision"),
            "record_ids": sorted(need_ids)[:3],  # record_ids cua run A
            "chunk_size": 10,
            "cong_chung_vien": None, "thu_ky": None})
        require(bogus.get("status") == "failed",
                f"prepare sai run khong bi tu choi: {bogus}")
        require((bogus.get("error") or {}).get("code") == "scope_violation",
                f"ma loi sai: {bogus.get('error')}")
        st = fstate(base)["session"]
        require(st["prepare_calls"] == 0 and
                st["open_record_ids"] == [],
                f"scope_violation van mo tab: {st}")
        # Khong cua so Chromium that nao duoc mo — chi mot page shell.
        require(len(page.context.pages) == 1,
                "co cua so/tab Chromium that ngoai shell")
    except BaseException:
        dump_debug(page)
        raise
    finally:
        browser.close()


# ============= --case offline (MIN-69 task 9, production package) =============
#
# Chung minh goi production chay that engine ma:
#   - KHONG co fixture provider/portal nao trong catalog;
#   - KHONG co lenh diag.* (test-build surface);
#   - scan + audit_excel ghi data HOAN TOAN duoi userData;
#   - install dir khong bi ghi de — ke ca khi deny write bang ACL.

def _tree_snapshot(root: Path) -> dict:
    """{relpath: (size, mtime_ns)} — diff truoc/sau cho install dir."""
    snap = {}
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try:
                st = p.stat()
                snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
            except OSError:
                pass
    return snap


def _acl_deny_writes(root: Path):
    """Chan ghi vao `root` cho user hien tai (Windows icacls).

    Mask hep (WD,AD,WA,WEA,DC): chan tao file moi/ghi/xoa con — nhu user
    thuong tren Program Files — nhung VAN cho execute (generic W cung
    deny SYNCHRONIZE → CreateProcess fail, khong phai dieu ta do).
    Tra mark de restore; None neu moi truong khong ho tro."""
    if os.name != "nt":
        return None
    domain = os.environ.get("USERDOMAIN") or ""
    user = os.environ.get("USERNAME")
    if not user:
        return None
    account = f"{domain}\\{user}" if domain else user
    r = subprocess.run(
        ["icacls", str(root), "/deny",
         f"{account}:(OI)(CI)(WD,AD,WA,WEA,DC)", "/T", "/Q"],
        capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return None
    return (root, account)


def _acl_restore(mark):
    if not mark:
        return
    root, account = mark
    subprocess.run(
        ["icacls", str(root), "/remove:d", account, "/T", "/Q"],
        capture_output=True, text=True, timeout=300)


def _submit_expect_error(page, command, payload, want_code):
    """submit va doi loi dung ma — cho assert command_unknown/production."""
    r = page.evaluate(
        """async ({command, payload}) => {
          const api = window.desktop.v1;
          const res = await api.submitCommand(
            command, payload, crypto.randomUUID());
          if (!res.ok) return {submit_error: res.error};
          const job = res.data;
          const t0 = Date.now();
          while (Date.now() - t0 < 30000) {
            const jr = await api.getJob(job.job_id);
            const j = jr && jr.ok ? jr.data : null;
            if (j && ['succeeded','failed','canceled','partial']
                .includes(j.status)) return j;
            await new Promise(rs => setTimeout(rs, 300));
          }
          return {timeout: true};
        }""",
        {"command": command, "payload": payload})
    err = (r.get("submit_error") or r.get("error") or {})
    code = err.get("code") if isinstance(err, dict) else None
    require(code == want_code,
            f"{command}: muon loi {want_code}, nhan {r}")
    return r


def case_offline(app: AppInstance, pw, tmp: Path):
    """Offline production package — khong portal, khong mang, khong Qt.

    Assert: catalog khong fixture; diag khong ton tai; scan/audit_excel
    that; du lieu chi duoi userData; install dir bat bien.
    """
    exe_dir = app.app_exe.parent
    require(app.packaged, "case offline can --app <exe>")
    require(app.data_dir == app.user_data_dir / "upload_lab",
            "case offline phai khong dat G1_UPLOAD_DATA_DIR")

    # -- Assert sidecar goi khong ship Qt + engine sach data ------------
    sidecar_dir = exe_dir / "resources" / "sidecar" / "g1-shell-sidecar"
    internal = sidecar_dir / "_internal"
    require(sidecar_dir.is_dir(),
            f"thieu sidecar packaged: {sidecar_dir}")
    require((internal / "playwright" / "driver" / "node.exe").is_file(),
            "thieu playwright driver trong _internal — spec chua bundle")
    qt_markers = [p for p in internal.rglob("*")
                  if p.name.lower().startswith(("pyside", "pyqt",
                                                "shiboken"))]
    require(not qt_markers,
            f"Qt bi ship trong sidecar: {qt_markers[:5]}")
    engine_dir = exe_dir / "resources" / "engine"
    require((engine_dir / "upload_lab").is_dir() and
            (engine_dir / "notary_v2").is_dir(),
            f"thieu engine bundled: {engine_dir}")
    forbidden = [p for p in engine_dir.rglob("*") if p.is_file() and (
        p.name in (".env", "registry.sqlite3", "nd_storage_state.json",
                   "notary.db") or "ui_qt" in str(p))]
    require(not forbidden,
            f"engine bundle chua file cam: {forbidden[:5]}")
    pw_dir = exe_dir / "resources" / "playwright-browsers"
    chromium = sorted(pw_dir.glob("chromium-*"))
    require(chromium, f"thieu chromium bundle: {pw_dir}")

    browser, page = connect_page(pw, app.port)
    try:
        # Frozen sidecar khoi dong cham hon dev — cho UI poll populate
        # catalog (cung la chung minh renderer↔main↔sidecar hoat dong).
        page.wait_for_function(
            """() => [...document.querySelectorAll(
                 '#ul-panel-audit select.ul-site option')]
                 .some(o => o.value === 'nam_dinh')""",
            timeout=120000)

        # -- Catalog production: chi provider that, KHONG fixture --------
        cat = submit_and_wait(page, "upload.websites", {})
        require(cat.get("status") == "succeeded",
                f"upload.websites loi: {cat}")
        sites = ((cat.get("result") or {}).get("data") or {}) \
            .get("websites") or []
        ids = [s.get("website_id") for s in sites]
        require("nam_dinh" in ids,
                f"catalog thieu nam_dinh: {ids}")
        fakes = [i for i in ids if str(i).startswith("fake_portal")]
        require(not fakes,
                f"PRODUCTION co fixture provider {fakes} — test hook bi "
                f"ro vao ban production")

        # -- diag.* khong ton tai trong production ----------------------
        _submit_expect_error(page, "diag.fixture_browser_launch", {},
                             "command_unknown")

        # -- Scan that tren fixture docx (ghi vao data root userData) ---
        ws = submit_and_wait(page, "upload.workspace_get", {
            "website_id": "nam_dinh",
        })
        require(ws.get("status") == "succeeded",
                f"upload.workspace_get loi: {ws}")
        revision = ((ws.get("result") or {}).get("data") or {}) \
            .get("revision")
        require(isinstance(revision, int),
                f"workspace revision thieu: {ws}")
        folder = tmp / "hs-offline"
        folder.mkdir(parents=True, exist_ok=True)
        docx_path = folder / "HD-001.docx"
        try:
            from docx import Document
        except ImportError:
            Document = None
        if Document is not None:
            d = Document()
            d.add_paragraph("Hop dong so 77/2026 ngay 10/05/2026")
            d.save(str(docx_path))
        else:
            docx_path.write_bytes(b"offline fixture docx")
        scan = submit_and_wait(page, "upload.scan", {
            "website_id": "nam_dinh",
            "folder": {"path": str(folder), "scope": "machine_local"},
            "expected_revision": revision,
            "full_rescan": True,
        }, timeout_s=120)
        require(scan.get("status") in ("succeeded", "partial"),
                f"upload.scan loi: {scan}")
        site_data = app.data_dir / "websites" / "nam_dinh"
        require((site_data / "registry.sqlite3").is_file(),
                f"registry khong nam duoi userData: {site_data}")

        # -- Audit Excel that (openpyxl/engine doc .xlsx) ---------------
        excel = tmp / "so-offline.xlsx"
        write_xlsx(excel, [
            ("Số công chứng", "Ngày công chứng"),
            ("77/2026", "10/05/2026"),
            ("78/2026", "11/05/2026"),
            ("78/2026", "11/05/2026"),
        ])
        audit = submit_and_wait(page, "upload.audit_excel", {
            "website_id": "nam_dinh",
            "file_ref": {"path": str(excel), "scope": "machine_local"},
            "from_date": "2026-05-01", "to_date": "2026-05-31",
        }, timeout_s=60)
        require(audit.get("status") == "succeeded",
                f"upload.audit_excel loi: {audit}")
        summary = ((audit.get("result") or {}).get("data") or {}) \
            .get("summary") or {}
        require(summary, f"audit thieu summary: {audit}")

        # -- env_check engine that (playwright/chromium bundle) ---------
        env = submit_and_wait(page, "upload.env_check", {
            "website_id": "nam_dinh",
        }, timeout_s=60)
        require(env.get("status") == "succeeded",
                f"upload.env_check loi: {env}")
    except BaseException:
        dump_debug(page)
        raise
    finally:
        browser.close()

    # -- Moi ghi phai nam duoi userData ---------------------------------
    require((app.user_data_dir / "output").exists() or
            (app.data_dir).exists(),
            "khong thay data nao duoi userData — sidecar ghi cho khac?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="audit",
                    choices=["audit", "upload", "all", "offline"])
    ap.add_argument("--app", default=None,
                    help="duong dan exe packaged (dist-app/dist-test); "
                         "khong dat = dev mode")
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter cho sidecar con (G1_PYTHON, dev)")
    ap.add_argument("--port", type=int, default=9333,
                    help="cong CDP remote-debugging")
    ap.add_argument("--keep", action="store_true",
                    help="giu thu muc tmp khi xong")
    ap.add_argument("--no-acl", action="store_true",
                    help="bo ACL deny-write check cua case offline")
    args = ap.parse_args()

    app_exe = Path(args.app).resolve() if args.app else None
    label = "dev"
    try:
        if app_exe is not None:
            require(app_exe.is_file(), f"khong tim thay --app: {app_exe}")
            label = build_label(app_exe)
            print(f"build label: {label} ({app_exe})")

        # Build-label enforcement: case portal can fixture → production
        # tu choi; offline chi tren production.
        if args.case in ("audit", "upload", "all") and label == "production":
            raise E2EFail(
                f"--case {args.case} can TEST package (fixture portal) — "
                f"production exe khong bao gio co fake_portal. Build bang "
                f"'npm run dist:test' roi tro --app sang dist-test/")
        if args.case == "offline" and app_exe is None:
            raise E2EFail("--case offline can --app <exe> (packaged)")
        if args.case == "offline" and label == "test":
            raise E2EFail(
                "--case offline chi chay tren production exe (dist-app) — "
                "test build luon co fixture provider trong catalog")
        check_deps(args.python, app_exe=app_exe)
    except E2EFail as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="g1-upload-e2e-"))
    expect_portals = args.case != "offline"
    app = AppInstance(tmp, args.port, args.python,
                      app_exe=app_exe, expect_portals=expect_portals)
    acl_mark = None
    install_snap = None
    if args.case == "offline":
        install_snap = _tree_snapshot(app_exe.parent)
        if not args.no_acl:
            acl_mark = _acl_deny_writes(app_exe.parent)
            if acl_mark:
                print("ACL deny-write da bat tren install dir "
                      "(install read-only check)")
            else:
                print("canh bao: khong deny-write duoc install dir "
                      "(icacls?) — chi snapshot-diff")
    try:
        portals = app.start()
        if expect_portals:
            require("fake_portal" in portals and "fake_portal_b" in portals,
                    f"e2e-state thieu portal gia lap: {portals}")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            if args.case == "offline":
                case_offline(app, pw, tmp)
                after = _tree_snapshot(app_exe.parent)
                diff = [k for k in set(install_snap) | set(after)
                        if install_snap.get(k) != after.get(k)]
                require(not diff,
                        f"install dir bi ghi de ({len(diff)} file): "
                        f"{diff[:5]}")
            if args.case in ("audit", "all"):
                browser, page = connect_page(pw, args.port)
                try:
                    case_audit(page, app.portals, tmp)
                except BaseException:
                    dump_debug(page)
                    raise
                finally:
                    browser.close()
            if args.case == "all":
                # Session con sot tu case audit (login fake_portal) phai
                # dong truoc case upload — sidecar chi cho mot browser/
                # website (website_mismatch neu con treo).
                browser, page = connect_page(pw, args.port)
                try:
                    for wid in app.portals:
                        ws = submit_and_wait(
                            page, "upload.workspace_get",
                            {"website_id": wid})
                        bid = ((ws.get("result") or {}).get("data")
                               or {}).get("browser_id")
                        if bid:
                            sc = submit_and_wait(
                                page, "upload.session_close",
                                {"website_id": wid, "browser_id": bid})
                            print(f"session_close {wid}: "
                                  f"{sc.get('status')}")
                    if app.packaged and label == "test":
                        # Real-browser probe: chromium bundle trong
                        # resources/playwright-browsers mo that toi portal
                        # localhost — packaged khong can tai gi runtime.
                        probe = submit_and_wait(
                            page, "diag.fixture_browser_launch", {},
                            timeout_s=90)
                        require(probe.get("status") == "succeeded",
                                f"fixture browser launch loi: {probe}")
                        data = ((probe.get("result") or {})
                                .get("data") or {})
                        require("127.0.0.1" in str(data.get("url")),
                                f"diag url khong loopback: {data}")
                        print(f"diag.fixture_browser_launch OK: {data}")
                finally:
                    browser.close()
            if args.case in ("upload", "all"):
                require("fake_portal_c" in app.portals,
                        f"e2e-state thieu fake_portal_c: {app.portals}")
                case_upload(app, pw, tmp)
        print(f"PASS --case {args.case} (label={label})")
        return 0
    except E2EFail as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        errlog = tmp / "electron.stderr.log"
        if errlog.is_file():
            tail = errlog.read_text(
                encoding="utf-8", errors="replace")[-4000:]
            print(f"--- electron.stderr tail ---\n{tail}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — bao loi kem log sidecar
        import traceback
        traceback.print_exc()
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        errlog = tmp / "electron.stderr.log"
        if errlog.is_file():
            tail = errlog.read_text(
                encoding="utf-8", errors="replace")[-4000:]
            print(f"--- electron.stderr tail ---\n{tail}", file=sys.stderr)
        return 1
    finally:
        app.stop()
        _acl_restore(acl_mark)
        if not args.keep:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
