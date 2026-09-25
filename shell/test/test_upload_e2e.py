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
              return {
                has_lab: !!lab,
                site_val: sel ? sel.value : null,
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="audit", choices=["audit"])
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter cho sidecar con (G1_PYTHON)")
    ap.add_argument("--port", type=int, default=9333,
                    help="cong CDP remote-debugging")
    ap.add_argument("--keep", action="store_true",
                    help="giu thu muc tmp khi xong")
    args = ap.parse_args()

    check_deps(args.python)
    tmp = Path(tempfile.mkdtemp(prefix="g1-upload-e2e-"))
    proc = None
    stderr_fh = None
    try:
        proc, stderr_fh = launch_app(tmp, args.port, args.python)
        wait_cdp(args.port, proc)
        state = wait_state_file(tmp)
        portals = state.get("portals") or {}
        require("fake_portal" in portals and "fake_portal_b" in portals,
                f"e2e-state thieu portal gia lap: {state}")

        from playwright.sync_api import sync_playwright

        page = None
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(
                f"http://127.0.0.1:{args.port}")
            try:
                ctx = browser.contexts[0]
                deadline = time.time() + 60
                while time.time() < deadline and page is None:
                    for p in ctx.pages:
                        if "index.html" in (p.url or ""):
                            page = p
                            break
                    if page is None:
                        time.sleep(0.5)
                require(page is not None,
                        "khong tim thay cua so index.html qua CDP")
                page.wait_for_selector(
                    '#module-list li[data-id="upload"]', timeout=60000)
                page.click('#module-list li[data-id="upload"]')
                page.wait_for_selector(".upload-lab", timeout=30000)
                if args.case == "audit":
                    try:
                        case_audit(page, portals, tmp)
                    except BaseException:
                        dump_debug(page)
                        raise
            finally:
                browser.close()
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
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        errlog = tmp / "electron.stderr.log"
        if errlog.is_file():
            tail = errlog.read_text(
                encoding="utf-8", errors="replace")[-4000:]
            print(f"--- electron.stderr tail ---\n{tail}", file=sys.stderr)
        return 1
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        if stderr_fh is not None:
            stderr_fh.close()
        if not args.keep:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
