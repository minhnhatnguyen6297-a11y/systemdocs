"""Test UI qua DOM stub + Node — chạy ui/app.js thật, không cần trình duyệt.

_ui_dom_probe.mjs stub document/fetch/URL tối thiểu rồi eval app.js và thao
tác như người dùng: Run (kể cả sửa source giữa chừng), import file lỗi/đúng,
export, highlight sau emoji. Kết quả in JSON; test này assert từng check.

Bỏ qua khi máy không có Node — tool là dev-tool nên môi trường dev có node
là đủ; CI thiếu node thì test skip, không fail giả.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

PROBE = Path(__file__).resolve().parent / "_ui_dom_probe.mjs"


@unittest.skipUnless(shutil.which("node"), "cần Node để chạy DOM stub probe")
class UiDomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(
            ["node", str(PROBE)],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            raise AssertionError(f"ui dom probe crash:\n{proc.stderr[-2000:]}")
        cls.out = json.loads(proc.stdout)

    def test_all_ui_checks_pass(self):
        failures = [
            f"{name}: {info.get('detail', '')[:120]}"
            for name, info in self.out["checks"].items()
            if not info["pass"]
        ]
        self.assertEqual(self.out["fails"], [])
        self.assertEqual(failures, [], "\n".join(failures))

    def test_expected_checks_present(self):
        expected = {
            "esc_attribute_quotes",
            "highlight_codepoint_after_emoji",
            "stale_response_discarded",
            "request_sent_snapshot",
            "normal_run_renders",
            "shape_problems_displayed",
            "import_bad_json_shows_error",
            "import_ok_loads_profile",
            "export_profile_downloads",
            "invalid_profile_blocks_run",
        }
        self.assertEqual(expected, set(self.out["checks"]))


if __name__ == "__main__":
    unittest.main()
