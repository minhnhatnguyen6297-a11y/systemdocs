// Probe UI: chạy ui/app.js THẬT trong DOM giả lập (không cần trình duyệt).
// pytest gọi file này qua subprocess và assert từng check trong JSON out.
//
//   node tests/_ui_dom_probe.mjs
//
// Các ca được kiểm chứng (map với findings review):
//   - esc() escape dấu ngoặc kép/nháy trong HTML attribute (app.js:5)
//   - renderHighlight slice theo CODE POINT (Array.from) — emoji không lệch (app.js:91)
//   - sửa source trong lúc request đang chờ -> kết quả cũ bị bỏ qua (app.js:44)
//   - import file JSON lỗi -> báo lỗi trong profile-status (app.js:204)
//   - import file hợp lệ -> nạp vào editor; export -> tải profile xuống
//   - response 400 kèm problems -> hiển thị chi tiết trong #errors

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const src = fs.readFileSync(path.join(here, "..", "ui", "app.js"), "utf8");

/* ---- DOM stub tối thiểu ---- */
const els = {};
const anchors = [];
function el(id) {
  if (!els[id]) {
    els[id] = {
      id,
      value: "",
      textContent: "",
      innerHTML: "",
      className: "",
      disabled: false,
      files: [],
      clicked: false,
      listeners: {},
      addEventListener(type, fn) {
        (this.listeners[type] ||= []).push(fn);
      },
      click() {
        this.clicked = true;
      },
    };
  }
  return els[id];
}

globalThis.document = {
  getElementById: el,
  createElement: () => {
    const a = { href: "", download: "", clicked: false, click() { a.clicked = true; } };
    anchors.push(a);
    return a;
  },
};
let fetchImpl = async () => ({
  ok: true,
  status: 200,
  json: async () => ({ profile: { profile_id: "transfer", version: "test" } }),
});
const fetchCalls = [];
globalThis.fetch = (...args) => {
  fetchCalls.push(args);
  return fetchImpl(...args);
};
globalThis.URL.createObjectURL = () => "blob:mock";
globalThis.URL.revokeObjectURL = () => {};
globalThis.Blob = class Blob { constructor(parts) { this.parts = parts; } };

const checks = {};
const fails = [];
function check(name, cond, detail = "") {
  checks[name] = { pass: !!cond, detail };
}

/* ---- Nạp app.js: strict-mode nên cần trailer export ra globalThis ---- */
(0, eval)(
  src +
    "\n;globalThis.__t = { esc, runEngine, renderHighlight, render, collectIntervals, readProfile, loadDefaultProfile };"
);
const t = globalThis.__t;
await new Promise((r) => setTimeout(r, 0)); // để loadDefaultProfile() settle

const FAKE_RESULT = {
  doc_kind: "transfer",
  title: { value: "HỢP ĐỒNG", state: "matched", span: [0, 8], rule_id: "kind.transfer" },
  zones: [{ name: "parties", state: "matched", span: [1, 4] }],
  fields: [],
  parties: { blocks: [] },
  errors: [],
};

try {
  // 1) esc() phải escape cả attribute quotes — finding app.js:5
  check(
    "esc_attribute_quotes",
    t.esc('a"b\'c<d>&') === "a&quot;b&#39;c&lt;d&gt;&amp;",
    t.esc('a"b\'c<d>&')
  );

  // 2) highlight theo code point — span [1,4] trên "📜ABC" phải tô đúng "ABC"
  //    (emoji = 1 code point Python nhưng 2 UTF-16 unit trong JS) — app.js:91
  el("highlight").innerHTML = "";
  t.renderHighlight("📜ABC", {
    zones: [{ name: "parties", state: "matched", span: [1, 4] }],
    fields: [],
    parties: { blocks: [] },
    title: {},
  });
  const hl = el("highlight").innerHTML;
  check(
    "highlight_codepoint_after_emoji",
    />ABC<\/span>/.test(hl) && hl.includes("📜"),
    hl
  );

  // 3) sửa source trong lúc request chờ -> bỏ qua response cũ — app.js:44
  el("profile").value = "{}";
  el("source").value = "VAN_BAN_V1";
  el("errors").textContent = "";
  el("json").textContent = "";
  let resolveFetch;
  fetchImpl = () => new Promise((r) => { resolveFetch = r; });
  const runPromise = t.runEngine();
  el("source").value = "VAN_BAN_V2_SUA_LUC_CHO";
  resolveFetch({ ok: true, status: 200, json: async () => ({ result: FAKE_RESULT }) });
  await runPromise;
  check(
    "stale_response_discarded",
    /đã thay đổi/.test(el("errors").textContent) && el("json").textContent === "",
    el("errors").textContent
  );

  // 4) request body phải chứa đúng snapshot text lúc gửi
  check(
    "request_sent_snapshot",
    JSON.parse(fetchCalls.at(-1)[1].body).text === "VAN_BAN_V1",
    fetchCalls.at(-1)[1].body
  );

  // 5) run bình thường (source không đổi) -> render đầy đủ
  el("errors").textContent = "";
  fetchImpl = async () => ({ ok: true, status: 200, json: async () => ({ result: FAKE_RESULT }) });
  await t.runEngine();
  check(
    "normal_run_renders",
    el("json").textContent.includes('"doc_kind"') && el("errors").textContent === "",
    el("json").textContent.slice(0, 60)
  );

  // 6) response 400 + problems -> #errors hiển thị chi tiết — serve.py contract
  fetchImpl = async () => ({
    ok: false,
    status: 400,
    json: async () => ({ error: "profile sai cau truc", problems: ["'fields' phai la list"] }),
  });
  await t.runEngine();
  check(
    "shape_problems_displayed",
    /sai cau truc/.test(el("errors").textContent) && /fields/.test(el("errors").textContent),
    el("errors").textContent
  );

  // 7) import file JSON lỗi -> profile-status báo lỗi — app.js:204
  el("file-import").files = [{ text: async () => "not json {" }];
  await els["file-import"].listeners.change[0]({ target: el("file-import") });
  check(
    "import_bad_json_shows_error",
    el("profile-status").className === "status bad" &&
      /import/.test(el("profile-status").textContent),
    el("profile-status").textContent
  );

  // 8) import file hợp lệ -> nạp vào editor + status ok
  el("file-import").files = [{ text: async () => '{"a":1}' }];
  await els["file-import"].listeners.change[0]({ target: el("file-import") });
  check(
    "import_ok_loads_profile",
    el("profile").value === '{\n  "a": 1\n}' && el("profile-status").className === "status ok",
    el("profile").value
  );

  // 9) export -> tạo blob + anchor download
  anchors.length = 0;
  els["btn-export"].listeners.click[0]();
  check(
    "export_profile_downloads",
    anchors.length === 1 &&
      anchors[0].clicked === true &&
      anchors[0].download === "regex_workbench_profile.json" &&
      anchors[0].href === "blob:mock",
    JSON.stringify(anchors[0] && { href: anchors[0].href, download: anchors[0].download })
  );

  // 10) profile JSON lỗi trong editor -> Run không gọi fetch, status bad
  const before = fetchCalls.length;
  el("profile").value = "{broken";
  await t.runEngine();
  check(
    "invalid_profile_blocks_run",
    fetchCalls.length === before && el("profile-status").className === "status bad",
    el("profile-status").textContent
  );
} catch (err) {
  fails.push(String(err && err.stack || err));
}

console.log(JSON.stringify({ checks, fails }, null, 2));
