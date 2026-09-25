"""G1 shell sidecar — desktopcommand.v1 producer (FastAPI, loopback only).

Contract: systemdocs contracts/desktop-command.md (desktopcommand.v1).
Token: env SIDECAR_TOKEN (bat buoc — thieu thi khong khoi dong).
Port:  env SIDECAR_PORT (Electron main chon port dong truoc khi spawn).
"""
import hmac
import os
import re
import sys
import threading
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from command_registry import COMMANDS
from errors import CommandError, error_object
from fileref import validate_file_ref
from job_repository import JobRepository
from jobstore import JobStore

CONTRACT_VERSION = "desktopcommand.v1"
# desktopcommand.v1 = envelope transport; upload.workflow.v1 = workflow
# Upload Lab da implement (MIN-69) — client kiem capability qua /health.
SUPPORTED_VERSIONS = ["desktopcommand.v1", "upload.workflow.v1"]
ENGINE_VERSION = "g1-shell-sidecar/0.1.0"
ENGINE_INSTANCE_ID = uuid.uuid4().hex  # doi moi moi lan process start — §5 restart

TOKEN = os.environ.get("SIDECAR_TOKEN")
if not TOKEN:
    print("FATAL: thieu SIDECAR_TOKEN", file=sys.stderr)
    sys.exit(2)
PORT = int(os.environ.get("SIDECAR_PORT", "0"))
if not PORT:
    print("FATAL: thieu SIDECAR_PORT", file=sys.stderr)
    sys.exit(2)

SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|token|credential|cookie|auth|session|"
    r"storage_state|api_key|bearer", re.I)

app = FastAPI(title="g1-shell-sidecar", docs_url=None, redoc_url=None)


def _build_store():
    """JobStore + journal ben trong workspace.sqlite3 (MIN-69 T5).

    Repository mo cung file SQLite cua upload workspace — reconnect theo
    job_id/command_id song xuyen restart, job non-terminal cua process
    truoc thanh failed{engine_restarted} va handler khong chay lai.
    Khong mo duoc db → chay degraded (in-memory nhu cu), khong che boot.
    """
    try:
        import upload_workspace
        return JobStore(
            repository=JobRepository(upload_workspace.workspace_db_path()))
    except Exception as exc:  # noqa: BLE001 — boot khong duoc chet vi journal
        print(f"WARN: job repository khong mo duoc ({exc}) — "
              "chay in-memory", file=sys.stderr)
        return JobStore()


def _install_e2e_fixtures():
    """MIN-69 T9 — chi TEST BUILD. Ba lop guard:

    1. `G1_BUILD_LABEL=test` — main.js force-set `production|test` qua env
       sidecar (config.js); production packaged luon la `production` nen
       `G1_E2E_FIXTURE` con sot tren may user la no-op ngay ca khi
       `e2e_fixture_hook.py` giai duoc tu PYTHONPATH (F3 — spawn packaged
       da strip PYTHON*, lop nay la defense-in-depth).
    2. `G1_E2E_FIXTURE=1` — trusted harness channel qua env sidecar;
       renderer khong bao gio dat duoc env nay.
    3. Module `e2e_fixture_hook` chi ship trong dist:test — production
       khong bundle → import fail cung la no-op.
    """
    if os.environ.get("G1_BUILD_LABEL") != "test":
        return
    if os.environ.get("G1_E2E_FIXTURE") != "1":
        return
    try:
        import e2e_fixture_hook
    except ImportError:
        print("G1_E2E_FIXTURE=1 nhung e2e_fixture_hook khong co trong goi "
              "(production build) — bo qua", file=sys.stderr)
        return
    e2e_fixture_hook.install()


store = _build_store()
_install_e2e_fixtures()
_server = None  # uvicorn.Server, set in main()


def _err(status, code, message, retryable=False, next_action=None):
    return JSONResponse(
        {"error": error_object(code, message, retryable, next_action)},
        status_code=status)


def _walk_sensitive(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SENSITIVE_KEY.search(str(k)):
                return str(k)
            found = _walk_sensitive(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _walk_sensitive(v)
            if found:
                return found
    return None


def _walk_file_refs(obj):
    """Tim dict dang file_ref (co key 'path' kieu str) de validate scope/path
    ngay luc submit — contract §6 yeu cau 400 file_scope_not_supported."""
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str):
            yield obj
        for v in obj.values():
            yield from _walk_file_refs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_file_refs(v)


@app.middleware("http")
async def auth_boundary(request: Request, call_next):
    # Loopback API khong phuc vu browser: bat ky Origin nao cung bi tu choi
    # (khong CORS — contract §1,§4).
    if "origin" in request.headers:
        return _err(403, "auth_forbidden", "Origin header khong duoc phep")
    if request.url.path == "/healthz":
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    try:
        ok = hmac.compare_digest(auth.encode(), f"Bearer {TOKEN}".encode())
    except (TypeError, UnicodeError):
        ok = False
    if not ok:
        return _err(401, "auth_unauthorized", "thieu/sai bearer token")
    return await call_next(request)


@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "engine_instance_id": ENGINE_INSTANCE_ID,
        "supported_versions": SUPPORTED_VERSIONS,
        "accepting": store.accepting,
        # Nhan build cho harness — dev khong dat = "dev"; packaged main
        # truyen production|test (config.js G1_BUILD_LABEL).
        "build_label": os.environ.get("G1_BUILD_LABEL", "dev"),
    }


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.I)


@app.post("/v1/commands")
async def submit_command(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _err(400, "validation_error", "body khong phai JSON hop le")
    if not isinstance(body, dict):
        return _err(400, "validation_error", "body phai la object")
    if body.get("contract_version") != CONTRACT_VERSION:
        return _err(400, "unsupported_contract_version",
                    f"can {CONTRACT_VERSION}")
    command_id = body.get("command_id")
    if not isinstance(command_id, str) or not _UUID_RE.match(command_id):
        return _err(400, "validation_error", "command_id phai la uuid")
    meta = body.get("client_meta") or {}
    if not isinstance(meta, dict) or not isinstance(meta.get("shell_version"), str) \
            or not isinstance(meta.get("module"), str):
        return _err(400, "validation_error",
                    "client_meta can {shell_version, module}")
    command = body.get("command")
    if not isinstance(command, str) or "." not in command:
        return _err(400, "validation_error", "command phai namespaced")
    handler = COMMANDS.get(command)
    if handler is None:
        return _err(400, "command_unknown", f"khong biet command {command!r}")
    payload = body.get("payload")
    if payload is not None and not isinstance(payload, dict):
        return _err(400, "validation_error", "payload phai la object/null")
    bad_key = _walk_sensitive(payload)
    if bad_key:
        return _err(400, "payload_rejected_sensitive_key",
                    f"key cam trong payload: {bad_key}")
    if payload:
        for ref in _walk_file_refs(payload):
            try:
                validate_file_ref(ref)
            except CommandError as exc:
                return _err(400, exc.code, exc.message)
    try:
        job = store.submit(command_id, command, handler, payload)
    except CommandError as exc:
        if exc.code == "command_id_conflict":
            # Cung command_id nhung noi dung request khac — xung dot
            # identity, KHONG duoc ghi de job cu (contract §8).
            return _err(409, exc.code, exc.message, exc.retryable)
        return _err(503, exc.code, exc.message, exc.retryable)
    return job.snapshot()


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str):
    job = store.get(job_id)
    if job is None:
        return _err(404, "job_not_found", f"khong co job {job_id!r}")
    return job.snapshot()


@app.post("/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    outcome = store.cancel(job_id)
    if outcome == "missing":
        return _err(404, "job_not_found", f"khong co job {job_id!r}")
    if outcome == "terminal":
        return _err(409, "job_already_terminal", "job da ket thuc")
    job = store.get(job_id)
    return job.snapshot()


@app.post("/shutdown")
def shutdown():
    def _stop():
        # Drain job truoc (cancel engine_shutdown + persist terminal),
        # roi cho browser worker reconcile/dong an toan — tab chua xac
        # minh Luu duoc giu dau needs_reconcile, khong coi la saved.
        # Worst-case ≈ 0.2 (timer) + 2 (drain) + ~2 (worker shutdown —
        # reconcile+join chia budget) + ~0.3 (uvicorn exit) ≈ 4.5s; phai
        # nam trong SHUTDOWN_GRACE_MS (shell/src/main/config.js).
        store.drain(timeout=2)
        try:
            import upload_session
            upload_session.worker().shutdown(timeout=2)
        except Exception:
            pass
        if _server is not None:
            _server.should_exit = True
    threading.Timer(0.2, _stop).start()
    return {"stopping": True}


def main():
    global _server
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT,
                            log_level="warning", access_log=False)
    _server = uvicorn.Server(config)
    _server.run()
    # worker threads co the chua daemon — thoat han process
    os._exit(0)


if __name__ == "__main__":
    main()
