"""Dev server cho Regex Workbench — chi dung thu vien chuan Python.

    python tools/regex_workbench/serve.py [--port 8765]

Endpoints:
    GET  /              -> giao dien 3 cot (ui/index.html)
    GET  /ui/<file>     -> static assets
    GET  /api/profile   -> profile mac dinh (engine/profiles/transfer.json)
    POST /api/run       -> body {text, profile} -> ket qua engine JSON
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
sys.path.insert(0, str(ROOT))

from engine import (  # noqa: E402
    DEFAULT_PROFILE,
    lint_profile,
    load_profile,
    run,
    validate_profile,
)

CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8"}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT):
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/" or self.path == "/index.html":
            self._send_file(UI_DIR / "index.html")
        elif self.path == "/api/profile":
            profile = load_profile(DEFAULT_PROFILE)
            self._send_json({"profile": profile})
        elif self.path.startswith("/ui/"):
            self._send_file(UI_DIR / self.path[len("/ui/"):].split("?")[0])
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": f"body JSON khong hop le: {exc}"}, 400)
            return

        text = str(payload.get("text", ""))
        profile = payload.get("profile")
        if profile is None:
            profile = load_profile(DEFAULT_PROFILE)
        elif not isinstance(profile, dict):
            try:
                profile = load_profile(str(profile))
            except (OSError, json.JSONDecodeError) as exc:
                self._send_json({"error": f"khong nap duoc profile: {exc}"}, 400)
                return

        shape_problems = validate_profile(profile)
        if shape_problems:
            self._send_json(
                {"error": "profile sai cau truc", "problems": shape_problems}, 400
            )
            return

        lint_problems = lint_profile(profile)
        try:
            result = run(text, profile)
        except Exception as exc:  # engine khong duoc lam roi request
            self._send_json({"error": f"engine loi: {type(exc).__name__}: {exc}"}, 500)
            return
        result["profile_warnings"] = lint_problems
        self._send_json({"result": result})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[workbench] " + fmt % args + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regex Workbench dev server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Regex Workbench dang chay tai {url} (Ctrl+C de dung)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
