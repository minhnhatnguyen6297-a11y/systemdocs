"""Test tầng HTTP cho serve.py — server thật, request thật (urllib).

Công cụ dev chạy MỘT lõi luật: `/api/meta` trả identity lõi (suy từ lõi),
`/api/run` trả payload + nhóm tài sản/thửa đất. Body sai → JSON 400,
lõi ném exception → JSON 500, request không bị rơi.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import serve

FIXTURES = Path(__file__).resolve().parent / "fixtures"

GROUP_TEXT = "\n".join([
    "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
    "TÀI SẢN",
    "Tài sản thứ 1: Giấy chứng nhận số: B 011092; Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu",
    "Loại đất: Đất ở; Diện tích: 120 m2; Thời hạn: Lâu dài",
])


class ServeHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def _get(self, path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=10) as res:
                return res.status, res.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8")

    def _post(self, payload: bytes, path: str = "/api/run") -> tuple[int, dict]:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def _run(self, text: str, **extra) -> tuple[int, dict]:
        return self._post(json.dumps({"text": text, **extra}).encode("utf-8"))

    # ---- GET ----

    def test_get_static_asset_and_traversal_guard(self):
        # Thoát khỏi thư mục tool = 404.
        status, _ = self._get("/ui/../../../AGENTS.md")
        self.assertEqual(status, 404)
        status, _ = self._get("/ui/khong-co-file.js")
        self.assertEqual(status, 404)

    def test_get_meta_returns_documented_shape(self):
        status, body = self._get("/api/meta")
        self.assertEqual(status, 200)
        meta = json.loads(body)
        for key in ("engine", "web_form_fields", "raw_keys"):
            self.assertIn(key, meta)

    def test_unknown_paths_404(self):
        status, _ = self._get("/khong-ton-tai")
        self.assertEqual(status, 404)
        status, data = self._post(b"{}", path="/api/khong-ton-tai")
        self.assertEqual(status, 404)
        self.assertIn("endpoint", data["error"])

    # ---- POST /api/run ----

    def test_post_run_extracts_transfer_fixture(self):
        text = (FIXTURES / "transfer_chuan.txt").read_text(encoding="utf-8")
        status, data = self._run(text)
        self.assertEqual(status, 200)
        web_form = data["payload"]["web_form"]
        raw = data["payload"]["raw"]
        self.assertIn("CHUYỂN NHƯỢNG", web_form["ten_hop_dong"])
        self.assertEqual(data["payload"]["case"]["loaivanbannhandien"], "transfer_contract")
        self.assertEqual(raw["ben_a"]["nguoi"][0]["ho_ten"], "Nguyễn Văn An")
        self.assertEqual(raw["danh_sach_thua_dat"][0]["so_thua_dat"], "215")
        self.assertEqual(data["groups"], [])  # không có nhãn nhóm -> consumer dùng danh_sach_thua_dat

    def test_post_run_group_text_reports_land_rows(self):
        status, data = self._run(GROUP_TEXT)
        self.assertEqual(status, 200)
        self.assertEqual(len(data["groups"]), 1)
        group = data["groups"][0]
        self.assertIn("B 011092", group["so_serial"])
        self.assertEqual(len(group["land_rows"]), 1)
        row = group["land_rows"][0]
        self.assertEqual(row["loai_dat"], "Đất ở")
        self.assertIn("120", row["dien_tich"])
        self.assertEqual(row["thoi_han"], "Lâu dài")

    def test_post_run_plain_text_flag_switches_mode(self):
        status, data = self._run(GROUP_TEXT, plain_text=True)
        self.assertEqual(status, 200)
        self.assertEqual(data["payload"]["raw"]["extract_mode"], "plain_text_doc")

    def test_post_run_bad_body_json_returns_400(self):
        status, data = self._post(b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("body JSON", data["error"])

    def test_post_run_body_not_object_returns_400(self):
        status, data = self._post(b'["text"]')
        self.assertEqual(status, 400)
        self.assertIn("JSON object", data["error"])

    def test_post_run_text_not_string_returns_400(self):
        status, data = self._post(json.dumps({"text": 123}).encode("utf-8"))
        self.assertEqual(status, 400)
        self.assertIn("text", data["error"])

    def test_post_run_plain_text_not_bool_returns_400(self):
        status, data = self._post(json.dumps({"text": "x", "plain_text": "có"}).encode("utf-8"))
        self.assertEqual(status, 400)
        self.assertIn("plain_text", data["error"])

    def test_post_run_engine_error_is_json_500(self):
        with mock.patch.object(serve, "run", side_effect=RuntimeError("bum")):
            status, data = self._run("x")
        self.assertEqual(status, 500)
        self.assertIn("RuntimeError", data["error"])
        self.assertIn("bum", data["error"])


if __name__ == "__main__":
    unittest.main()
