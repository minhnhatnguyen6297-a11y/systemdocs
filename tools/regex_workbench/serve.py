"""Dev server cho Regex Workbench — chỉ dùng thư viện chuẩn Python.

    python tools/regex_workbench/serve.py [--port 8765] [--no-browser]

Endpoints:
    GET  /              -> giao diện 3 cột (ui/index.html)
    GET  /ui/<file>     -> static assets
    GET  /api/meta      -> identity lõi + tên trường payload (suy từ lõi)
    POST /api/run       -> body {text, plain_text?} -> kết quả lõi + nhóm tài sản

Công cụ dev cho MỘT lõi luật (`engine/contract_extract.py`). Editor profile cũ
đã bỏ vì hết tác dụng kỹ thuật: định dạng profile JSON không còn tồn tại, luật
nay là mã Python trong lõi — dev sửa mã chuẩn rồi thử bằng chính lõi này.
Không phụ thuộc `upload_lab`, `shell`, `notary_v2`.
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

from engine import contract_extract as core  # noqa: E402

CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8"}


def meta() -> dict:
    """Identity + tên trường lấy từ chính lõi (không chép danh sách tay)."""
    empty = core.extract_text("")
    return {
        "engine": {"id": core.ENGINE_ID, "version": core.ENGINE_VERSION},
        "web_form_fields": list(empty["web_form"]),
        "case_fields": list(empty["case"]),
        "raw_keys": list(empty["raw"]),
    }


def run(text: str, *, plain_text: bool = False) -> dict:
    """Chạy lõi trên text dán vào, kèm khối nhóm tài sản để soi thửa/đất."""
    payload = core.extract_text(text, use_ifilter_for_doc=plain_text)
    tai_san = payload["web_form"].get("tai_san") or ""
    return {
        "payload": payload,
        "groups": core.tach_nhom_tai_san(tai_san),
        "asset_context": core.document_asset_context(tai_san),
    }


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

    def _not_found(self) -> None:
        if self.path.startswith("/api/"):
            self._send_json({"error": f"không có endpoint {self.path}"}, 404)
        else:
            self.send_error(404)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send_file(UI_DIR / "index.html")
        elif self.path == "/api/meta":
            self._send_json(meta())
        elif self.path.startswith("/ui/"):
            self._send_file(UI_DIR / self.path[len("/ui/"):].split("?")[0])
        else:
            self._not_found()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self._not_found()
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": f"body JSON không hợp lệ: {exc}"}, 400)
            return
        if not isinstance(body, dict):
            self._send_json({"error": "body phải là JSON object {text, plain_text?}"}, 400)
            return
        text = body.get("text", "")
        if not isinstance(text, str):
            self._send_json({"error": "trường text phải là chuỗi văn bản nguồn"}, 400)
            return
        plain_text = body.get("plain_text", False)
        if not isinstance(plain_text, bool):
            self._send_json({"error": "plain_text phải là true/false"}, 400)
            return
        try:
            result = run(text, plain_text=plain_text)
        except Exception as exc:  # lõi không được làm rơi request
            self._send_json({"error": f"lỗi lõi: {type(exc).__name__}: {exc}"}, 500)
            return
        self._send_json(result)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[workbench] " + fmt % args + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regex Workbench dev server (một lõi luật)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Regex Workbench đang chạy tại {url} (Ctrl+C để dừng)")
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
