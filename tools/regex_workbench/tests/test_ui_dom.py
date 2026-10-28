"""Test UI qua DOM stub + Node — chạy ui/app.js thật, không cần trình duyệt.

`_ui_dom_probe.mjs` stub document/fetch tối thiểu rồi nạp app.js và thao tác
như người dùng: Run, sửa nguồn giữa chừng, response về sai thứ tự, lỗi 400,
escape markup, tô vị trí giá trị sau emoji. Kết quả in JSON; test này assert
từng check.

Bỏ qua khi máy không có Node — tool là dev-tool nên môi trường dev có node
là đủ; máy thiếu node thì skip, không fail giả.
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
            timeout=60,
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


if __name__ == "__main__":
    unittest.main()
