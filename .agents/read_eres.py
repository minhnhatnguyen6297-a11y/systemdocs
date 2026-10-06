# -*- coding: utf-8 -*-
import json
r = json.load(open(".agents/rework-electron/electron-result.json", encoding="utf-8"))
out = []
for v in r:
    out.append({"viewport": v.get("viewport"), "flows": v.get("flows"),
                "copy_check": v.get("copy_check"),
                "ready": {k: v["ready_while_editing"][k] for k in
                          ("model_phase", "copy_buttons", "focus_after_response")},
                "cancel": {k: v["cancel_focus"][k] for k in
                           ("expected_focus", "actual_focus", "actual_selection", "full_calls")},
                "other_close": {k: v["other_field_close"][k] for k in
                                ("expected_focus", "actual_focus", "actual_selection")}})
with open("C:/Users/MINH/AppData/Local/Temp/opencode/erework.txt", "w", encoding="utf-8") as fh:
    fh.write(json.dumps(out, ensure_ascii=False, indent=1))
print("wrote")
