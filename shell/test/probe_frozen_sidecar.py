"""MIN-69 T9 — smoke frozen sidecar: healthz + engine-touching commands.

Chay exe da build (sidecar/dist/g1-shell-sidecar) voi G1_ENGINE_DIR tro vao
engine da stage — gia lap dung moi truong packaged ma khong can build app.

    python test/probe_frozen_sidecar.py [exe_path]

Exit 0 = PASS. Khong can portal, khong can mang.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = HERE.parent
EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    SHELL / "sidecar" / "dist" / "g1-shell-sidecar"
    / "g1-shell-sidecar.exe")
ENGINE = SHELL / "build" / "engine"
TOKEN = "probe-token-" + uuid.uuid4().hex[:12]
PORT = 8401


def http(url, method="GET", body=None, timeout=20):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


def submit(base, command, payload):
    cmd_id = str(uuid.uuid4())
    job = http(f"{base}/v1/commands", method="POST", body={
        "contract_version": "desktopcommand.v1",
        "command_id": cmd_id,
        "client_meta": {"shell_version": "probe", "module": "probe"},
        "command": command,
        "payload": payload})
    job_id = job["job_id"]
    deadline = time.time() + 120
    while time.time() < deadline:
        j = http(f"{base}/v1/jobs/{job_id}")
        if j["status"] in ("succeeded", "failed", "canceled", "partial"):
            return j
        time.sleep(0.4)
    raise RuntimeError(f"job {job_id} timeout")


# N4 (T9 review): sweep file tree cua goi PRODUCTION — fixture/test-only
# module va Qt khong bao gio duoc ship. Neu bat ky pattern nay xuat hien
# trong _internal (loose file) hay resources/engine thi goi production da
# chua test surface → fail ngay. (Module nam trong PYZ zip khong rglob
# duoc — lop do duoc chung minh bang diag.* = command_unknown + khong co
# pathex fixture ben duoi.)
_FORBIDDEN_NAME_PREFIXES = (
    "e2e_fixture_hook", "upload_portal", "sitecustomize",
    "pyside", "pyqt", "shiboken",
)
_FORBIDDEN_PATH_PARTS = (
    "fast_audit", "ui_qt",
    # sep cuoi: khong bat nham file ten 'custom*' ngay trong word_templates/.
    os.path.join("word_templates", "custom") + os.sep,
)


def assert_production_tree():
    """Tra danh sach file cam trong goi; [] = sach."""
    roots = [EXE.parent / "_internal"]
    for anc in EXE.parent.parents:
        if anc.name == "resources":
            roots.append(anc / "engine")
            break
    bad = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            name = p.name.lower()
            rel = str(p).lower()
            if name.startswith(_FORBIDDEN_NAME_PREFIXES) or any(
                    part in rel for part in _FORBIDDEN_PATH_PARTS):
                bad.append(str(p))
    return bad


def main():
    assert EXE.is_file(), f"thieu exe: {EXE}"
    assert ENGINE.is_dir(), f"chua stage engine: {ENGINE}"
    # N4: production file tree phai sach fixture/Qt/test surface.
    leaked = assert_production_tree()
    assert not leaked, (
        f"production tree chua {len(leaked)} file cam: {leaked[:10]}")
    print("tree sweep: sach (khong fixture/Qt/sitecustomize/fast_audit)")
    tmp = Path(tempfile.mkdtemp(prefix="g1-frozen-probe-"))
    env = dict(os.environ)
    env.update({
        "SIDECAR_TOKEN": TOKEN,
        "SIDECAR_PORT": str(PORT),
        "G1_ENGINE_DIR": str(ENGINE),
        "G1_UPLOAD_DATA_DIR": str(tmp / "upload_lab"),
        "G1_OUTPUT_DIR": str(tmp / "output"),
        "G1_BUILD_LABEL": "production",
    })
    err = open(tmp / "sidecar.err", "w", encoding="utf-8")
    proc = subprocess.Popen([str(EXE)], env=env, stderr=err,
                            stdout=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{PORT}"
    try:
        deadline = time.time() + 60
        health = None
        while time.time() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"exe exit {proc.returncode} — "
                                   f"xem {tmp}/sidecar.err")
            try:
                health = http(f"{base}/healthz")
                break
            except Exception:
                time.sleep(0.5)
        assert health and health.get("ok"), f"healthz fail: {health}"
        print("healthz:", health)
        assert health.get("build_label") == "production"

        cat = submit(base, "upload.websites",
                     {"workflow_version": "upload.workflow.v1"})
        ids = [w["website_id"]
               for w in (cat["result"]["data"]["websites"] or [])]
        assert "nam_dinh" in ids, f"catalog thieu nam_dinh: {ids}"
        assert not any(str(i).startswith("fake_portal") for i in ids)
        print("websites:", ids)

        # diag.fixture_browser_launch phai KHONG ton tai trong prod sidecar
        try:
            j = submit(base, "diag.fixture_browser_launch", {})
            raise AssertionError(f"diag ton tai trong production: {j}")
        except urllib.error.HTTPError as exc:
            assert exc.code == 400, exc
            print("diag.fixture_browser_launch: command_unknown (dung)")

        # Audit excel that — engine doc xlsx qua openpyxl.
        from openpyxl import Workbook
        excel = tmp / "so.xlsx"
        wb = Workbook()
        ws = wb.active
        for r in [("Số công chứng", "Ngày công chứng"),
                  ("77/2026", "10/05/2026"), ("79/2026", "12/05/2026"),
                  ("79/2026", "12/05/2026")]:
            ws.append(list(r))
        wb.save(str(excel))
        audit = submit(base, "upload.audit_excel", {
            "workflow_version": "upload.workflow.v1",
            "website_id": "nam_dinh",
            "file_ref": {"path": str(excel), "scope": "machine_local"},
            "from_date": "2026-05-01", "to_date": "2026-05-31"})
        assert audit["status"] == "succeeded", audit
        data = audit["result"]["data"]
        assert data["summary"]["excel_total"] == 3, data
        dupes = [i["so_cong_chung"] for i in data["issues"]
                 if "trung" in (i.get("ghi_chu") or "")]
        assert dupes.count("79/2026") == 2, data
        print("audit_excel:", data["summary"])

        # env_check that — playwright + chromium bundle duoc kiem.
        envj = submit(base, "upload.env_check", {
            "workflow_version": "upload.workflow.v1",
            "website_id": "nam_dinh"})
        print("env_check:", envj["status"],
              (envj.get("result") or {}).get("data", {}).get("status"))

        # khong Qt trong process — healthz xong khong cua so nao
        probe = subprocess.run(
            ["tasklist", "/FI", f"PID eq {proc.pid}"],
            capture_output=True, text=True)
        assert str(proc.pid) in probe.stdout
        print("PASS frozen sidecar probe")
        return 0
    finally:
        try:
            http(f"{base}/shutdown", method="POST", body={})
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        err.close()
        print("sidecar.err tail:")
        err_tail = Path(tmp / "sidecar.err")
        if err_tail.is_file():
            print(err_tail.read_text(
                encoding="utf-8", errors="replace")[-2000:])


if __name__ == "__main__":
    sys.exit(main())
