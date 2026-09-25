"""MIN-69 task 7 — E2E Upload Lab tren app dev qua Electron + CDP.

Chay app Electron that (dev mode: python sidecar + file:// renderer), sidecar
con duoc gan test hook (`test/e2e_hook/sitecustomize.py` qua PYTHONPATH) dang
ky hai portal gia lap `fake_portal`/`fake_portal_b` — khong cham sidecar,
engine hay contract. File picker duoc stub boi `G1_E2E_PICK_FILES`
(main.js) — doc JSON {"files": [...]} thay dialog that, van qua cung
filter/validate.

    python test/test_upload_e2e.py --case audit

Ca `audit`: chon website gia lap -> kiem tra moi truong -> mo dang nhap ->
user dang nhap tren portal gia -> xac nhan -> tai Excel -> audit tu dong ->
4 KPI + 2 bang dung du lieu -> doi ngay danh dau chua cap nhat -> nap lai
sach -> chon .xlsm tu nạp -> loi nap xoa ket qua -> doi website xoa scope.

Fail RA (khong skip) khi thieu: Electron binary, fixture, python deps
(fastapi/uvicorn/openpyxl cho sidecar; playwright cho driver CDP).
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


def check_deps(python):
    """Fail ro rang khi thieu Electron/fixture/python deps."""
    require(ELECTRON_EXE.is_file(),
            f"Thieu Electron dev binary: {ELECTRON_EXE} — chay "
            f"'npm install' trong shell/")
    require((FIXTURES / "upload_portal.py").is_file(),
            f"Thieu fixture upload_portal.py trong {FIXTURES}")
    require((HOOK_DIR / "sitecustomize.py").is_file(),
            f"Thieu e2e hook {HOOK_DIR / 'sitecustomize.py'}")
    require((SIDECAR / "app.py").is_file(),
            f"Thieu sidecar {SIDECAR / 'app.py'}")
    for mod in ("openpyxl",):
        try:
            __import__(mod)
        except ImportError:
            raise E2EFail(
                f"Thieu python dep '{mod}' cho runner — pip install {mod}")
    # Sidecar con chay bang G1_PYTHON (mac dinh = interpreter nay) — can
    # fastapi/uvicorn/openpyxl. Kiem bang mot process con cho dung.
    probe = subprocess.run(
        [python, "-c", "import fastapi, uvicorn, openpyxl"],
        capture_output=True, text=True)
    require(probe.returncode == 0,
            f"Sidecar python '{python}' thieu fastapi/uvicorn/openpyxl: "
            f"{probe.stderr.strip()[-400:]}")
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


def launch_app(tmp: Path, port: int, python: str):
    env = dict(os.environ)
    env["G1_PYTHON"] = python
    env["G1_UPLOAD_LAB_ROOT"] = str(REPO / "upload_lab")
    env["G1_UPLOAD_DATA_DIR"] = str(tmp / "upload_lab")
    env["G1_OUTPUT_DIR"] = str(tmp / "output")
    env["G1_E2E_STATE"] = str(tmp / "e2e-state.json")
    env["G1_E2E_PICK_FILES"] = str(tmp / "pick.json")
    # openPath seam: moi file duoc mo ghi mot dong vao log thay vi dep
    # app that (Word) — cung pattern G1_E2E_PICK_FILES.
    env["G1_E2E_OPEN_LOG"] = str(tmp / "opened.log")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(HOOK_DIR), str(FIXTURES), str(SIDECAR),
         env.get("PYTHONPATH", "")])
    env["ELECTRON_ENABLE_LOGGING"] = "1"
    stderr = open(tmp / "electron.stderr.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(ELECTRON_EXE), str(SHELL),
         f"--remote-debugging-port={port}",
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

    def __init__(self, tmp: Path, port: int, python: str):
        self.tmp = tmp
        self.port = port
        self.python = python
        self.proc = None
        self.stderr_fh = None
        self.portals = {}

    def start(self):
        self.proc, self.stderr_fh = launch_app(self.tmp, self.port,
                                               self.python)
        wait_cdp(self.port, self.proc)
        state = wait_state_file(self.tmp)
        self.portals = state.get("portals") or {}
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
    wsdb = tmp / "upload_lab" / "workspace.sqlite3"
    regdb = (tmp / "upload_lab" / "websites" / "fake_portal_c"
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="audit",
                    choices=["audit", "upload", "all"])
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter cho sidecar con (G1_PYTHON)")
    ap.add_argument("--port", type=int, default=9333,
                    help="cong CDP remote-debugging")
    ap.add_argument("--keep", action="store_true",
                    help="giu thu muc tmp khi xong")
    args = ap.parse_args()

    check_deps(args.python)
    tmp = Path(tempfile.mkdtemp(prefix="g1-upload-e2e-"))
    app = AppInstance(tmp, args.port, args.python)
    try:
        portals = app.start()
        require("fake_portal" in portals and "fake_portal_b" in portals,
                f"e2e-state thieu portal gia lap: {portals}")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            if args.case in ("audit", "all"):
                browser, page = connect_page(pw, args.port)
                try:
                    case_audit(page, app.portals, tmp)
                except BaseException:
                    dump_debug(page)
                    raise
                finally:
                    browser.close()
            if args.case in ("upload", "all"):
                require("fake_portal_c" in app.portals,
                        f"e2e-state thieu fake_portal_c: {app.portals}")
                case_upload(app, pw, tmp)
        print(f"PASS --case {args.case}")
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
        if not args.keep:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
