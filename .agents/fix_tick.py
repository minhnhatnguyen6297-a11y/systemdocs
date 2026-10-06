# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("D:/systemdocs/shell/test/notary-case-drafting-view.test.mjs")
lines = p.read_text(encoding="utf-8").split("\n")
for i in range(1510, len(lines)):
    lines[i] = lines[i].replace("tick(", "ltick(")
p.write_text("\n".join(lines), encoding="utf-8")
print("renamed")
