# -*- coding: utf-8 -*-
import json

s = json.load(open("contracts/administrative-timeline/ledger.schema.json", encoding="utf-8"))
defs = s["$defs"]
with open("C:/Users/MINH/AppData/Local/Temp/opencode/defs.txt", "w", encoding="utf-8") as fh:
    for key in ("observations", "names", "parents", "units", "sources"):
        fh.write("=== " + key + " ===\n")
        fh.write(json.dumps(defs[key], ensure_ascii=False)[:2500] + "\n")
print("ok")
