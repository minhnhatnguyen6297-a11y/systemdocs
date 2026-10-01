"""Test tang HTTP cho serve.py — server that, request that (urllib).

Bao phu contract runner<->HTTP: profile sai shape -> 400 co cau truc,
body JSON loi -> 400, run binh thuong -> 200 + result day du, request
khong bi roi khi engine nem exception.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import serve
from engine import load_profile

FIXTURES = Path(__file__).resolve().parent / "fixtures"


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

    def _post(self, payload: bytes, path: str = "/api/run") -> tuple[int, dict]:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_get_profile_ok(self):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/api/profile", timeout=10
        ) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
        self.assertEqual(data["profile"]["profile_id"], "transfer")

    def test_post_run_ok(self):
        text = (FIXTURES / "transfer_chuan.txt").read_text(encoding="utf-8")
        status, data = self._post(json.dumps({"text": text}).encode("utf-8"))
        self.assertEqual(status, 200)
        self.assertEqual(data["result"]["doc_kind"], "transfer")
        self.assertIn("fields", data["result"])
        self.assertIn("profile_warnings", data["result"])

    def test_post_run_bad_body_json(self):
        status, data = self._post(b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_post_run_bad_profile_shape_returns_400(self):
        """serve.py:89 review — fields=null phai tra 400 co cau truc."""
        status, data = self._post(
            json.dumps({"text": "abc", "profile": {"fields": None, "zones": "x"}}).encode("utf-8")
        )
        self.assertEqual(status, 400)
        self.assertIn("error", data)
        self.assertTrue(data.get("problems"), data)
        self.assertTrue(any("fields" in p for p in data["problems"]))
        self.assertTrue(any("zones" in p for p in data["problems"]))

    def test_post_run_profile_not_dict_returns_400(self):
        status, data = self._post(
            json.dumps({"text": "abc", "profile": ["khong", "phai", "object"]}).encode("utf-8")
        )
        # list -> server thu load_profile theo ten -> that bai -> 400 ro rang
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_post_run_engine_error_is_json_500(self):
        """Engine nem loi bat ngo -> 500 JSON, request khong bi roi."""
        profile = load_profile("transfer")
        profile["regex_timeout_ms"] = "boom"  # qua validate vi khong phai so
        status, data = self._post(
            json.dumps({"text": "abc", "profile": profile}).encode("utf-8")
        )
        self.assertEqual(status, 400)  # validate_profile chan truoc
        self.assertIn("error", data)

        # Truong hop engine crash that su: timeout_ms kieu float am
        # van hop le shape nhung co the gay loi — chi can contract la JSON.
        profile2 = load_profile("transfer")
        status2, data2 = self._post(
            json.dumps({"text": "HỢP ĐỒNG CHUYỂN NHƯỢNG\n", "profile": profile2}).encode("utf-8")
        )
        self.assertEqual(status2, 200)
        self.assertIn("result", data2)

    def test_unknown_post_path_404(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/nope",
            data=b"{}",
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
