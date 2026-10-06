# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("D:/systemdocs/.agents/rework-electron/electron-audit.cjs")
t = p.read_text(encoding="utf-8")
old = "const ROOT = path.resolve(__dirname, '../..');"
new = "const ROOT = 'D:\\\\systemdocs';"
assert old in t
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

h = Path("D:/systemdocs/.agents/rework-electron/harness.html")
h.write_text(
    '<!doctype html>\n<html lang="vi"><head><meta charset="utf-8">\n'
    '<link rel="stylesheet" href="file:///D:/systemdocs/shell/src/renderer/styles.css">\n'
    '<link rel="stylesheet" href="file:///D:/systemdocs/shell/src/renderer/notary/case-drafting.css">\n'
    '<style>html,body{height:100%;margin:0}#app{height:100%;padding:12px;box-sizing:border-box}</style>\n'
    '</head><body><div id="app"><main id="content"><section id="view">'
    '<section id="fixture" class="cd-root-outer"></section>'
    '</section></main></div></body></html>\n',
    encoding="utf-8",
)
print("harness copy ready")
