/* Regex Workbench UI — vanilla JS, server Python chay engine that. */
"use strict";

const $ = (id) => document.getElementById(id);
// Escape đầy đủ cho cả text node lẫn attribute (title="..."): rule_id hay
// raw_snippet chứa dấu ngoặc kép phải không phá được markup.
const esc = (s) => String(s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

let defaultProfile = null;

async function loadDefaultProfile() {
  const res = await fetch("/api/profile");
  const data = await res.json();
  defaultProfile = data.profile;
  $("profile").value = JSON.stringify(defaultProfile, null, 2);
}

function readProfile() {
  try {
    const profile = JSON.parse($("profile").value);
    $("profile-status").textContent = "profile JSON hợp lệ";
    $("profile-status").className = "status ok";
    return profile;
  } catch (err) {
    $("profile-status").textContent = "profile JSON lỗi: " + err.message;
    $("profile-status").className = "status bad";
    return null;
  }
}

async function runEngine() {
  const profile = readProfile();
  if (!profile) return;
  // Snapshot input lúc gửi request: nếu user sửa source trong lúc chờ,
  // response thuộc về văn bản CŨ — không được render lên văn bản mới.
  const sentText = $("source").value;
  $("btn-run").disabled = true;
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: sentText, profile }),
    });
    const data = await res.json();
    if (!res.ok) {
      const detail = (data.problems || []).length ? " — " + data.problems.join("; ") : "";
      $("errors").textContent = (data.error || "server error") + detail;
      return;
    }
    if ($("source").value !== sentText) {
      $("errors").textContent =
        "Văn bản nguồn đã thay đổi trong lúc chạy — bỏ qua kết quả cũ, nhấn Run lại.";
      return;
    }
    render(sentText, data.result);
  } finally {
    $("btn-run").disabled = false;
  }
}

/* ---- Highlight: sweep boundaries, zone tint + field/person state ---- */

function collectIntervals(result) {
  const intervals = [];
  for (const z of result.zones || []) {
    if (z.state === "matched" && z.span) {
      intervals.push({ s: z.span[0], e: z.span[1], cls: "z-" + z.name, kind: "zone", title: "zone " + z.name });
    }
  }
  for (const f of result.fields || []) {
    if (f.span && ["matched", "warning_nonstandard", "ambiguous"].includes(f.state)) {
      intervals.push({ s: f.span[0], e: f.span[1], cls: "fld st-" + f.state, kind: "field", title: f.rule_id + " → " + f.name });
    }
  }
  for (const b of (result.parties && result.parties.blocks) || []) {
    for (const p of b.persons || []) {
      if (p.span) {
        intervals.push({ s: p.span[0], e: p.span[1], cls: "person", kind: "person", title: "người — bên " + p.side });
      }
      for (const [fname, fd] of Object.entries(p.fields || {})) {
        if (fd.span && ["matched", "warning_nonstandard", "ambiguous"].includes(fd.state)) {
          intervals.push({ s: fd.span[0], e: fd.span[1], cls: "fld st-" + fd.state, kind: "field", title: fd.rule_id + " → " + fname });
        }
      }
    }
  }
  if (result.title && result.title.span) {
    intervals.push({ s: result.title.span[0], e: result.title.span[1], cls: "fld st-matched", kind: "field", title: "title → " + result.title.rule_id });
  }
  return intervals;
}

function renderHighlight(text, result) {
  // Spans từ engine là index theo CODE POINT trên text người dùng nhập.
  // JS slice() đếm theo UTF-16 unit nên ký tự ngoài BMP (emoji...) làm lệch
  // offset — phải slice qua Array.from (mỗi phần tử = 1 code point).
  const cps = Array.from(text);
  const intervals = collectIntervals(result);
  const bounds = new Set([0, cps.length]);
  for (const iv of intervals) { bounds.add(iv.s); bounds.add(iv.e); }
  const pts = [...bounds].sort((a, b) => a - b);

  let html = "";
  for (let i = 0; i < pts.length - 1; i++) {
    const s = pts[i], e = pts[i + 1];
    const seg = cps.slice(s, e).join("");
    const containing = intervals.filter((iv) => iv.s <= s && iv.e >= e);
    const innermost = (kind) =>
      containing.filter((iv) => iv.kind === kind).sort((a, b) => (a.e - a.s) - (b.e - b.s))[0];
    const zone = innermost("zone");
    const fld = innermost("field");
    const person = innermost("person");
    const classes = [zone && zone.cls, person && "person", fld && fld.cls].filter(Boolean).join(" ");
    const title = (fld || person || zone || {}).title || "";
    html += classes
      ? `<span class="${classes}" title="${esc(title)}">${esc(seg)}</span>`
      : esc(seg);
  }
  $("highlight").innerHTML = html || '<span class="muted">(chưa có văn bản)</span>';
}

/* ---- Tables & summary ---- */

const STATE_LABEL = {
  matched: "matched",
  ambiguous: "ambiguous",
  warning_nonstandard: "warning",
  missing: "missing",
  error: "error",
};

function stateBadge(state) {
  return `<span class="badge st-${state}">${STATE_LABEL[state] || state}</span>`;
}

function renderSummary(result) {
  const counts = {};
  for (const f of result.fields || []) counts[f.state] = (counts[f.state] || 0) + 1;
  const chips = Object.entries(counts)
    .map(([st, n]) => `${stateBadge(st)} ×${n}`)
    .join(" ");
  $("summary").innerHTML = `
    <div><b>Loại văn bản:</b> <code>${esc(result.doc_kind)}</code>
      <span class="muted">(${esc(result.title.rule_id || "—")})</span></div>
    <div><b>Tiêu đề:</b> ${esc(result.title.value || "—")}</div>
    <div><b>Profile:</b> ${esc(result.profile_id || "?")} v${esc(result.profile_version || "?")}</div>
    <div class="chips">${chips}</div>`;
}

function renderFields(result) {
  const rows = (result.fields || [])
    .map((f) => `<tr>
      <td>${esc(f.name)}</td>
      <td class="val" title="${esc(f.raw_snippet || "")}">${esc(f.value == null ? "" : (Array.isArray(f.value) ? f.value.join(" | ") : f.value))}</td>
      <td>${stateBadge(f.state)}</td>
      <td class="mono">${esc(f.rule_id || "")}</td>
      <td class="mono">${f.span ? f.span[0] + "–" + f.span[1] : ""}</td>
    </tr>`)
    .join("");
  $("fields").innerHTML =
    `<tr><th>Field</th><th>Value</th><th>State</th><th>rule_id</th><th>span</th></tr>` + rows;
}

function renderPersons(result) {
  const rows = [];
  for (const b of (result.parties && result.parties.blocks) || []) {
    for (const p of b.persons || []) {
      const f = p.fields || {};
      const name = f.ho_ten ? f.ho_ten.value : "";
      rows.push(`<tr>
        <td>${esc(p.side)}</td><td>${esc(p.role)}</td>
        <td class="val">${esc(name || "")}</td>
        <td class="val">${esc((f.ngay_sinh && f.ngay_sinh.value) || "")}</td>
        <td class="val">${esc((f.cccd && f.cccd.value) || "")}</td>
        <td>${f.ho_ten ? stateBadge(f.ho_ten.state) : ""}</td>
        <td class="mono">${p.span ? p.span[0] + "–" + p.span[1] : ""}</td>
      </tr>`);
    }
  }
  $("persons").innerHTML =
    `<tr><th>Bên</th><th>Vai trò</th><th>Họ tên</th><th>Ngày/năm sinh</th><th>CCCD</th><th>State</th><th>span</th></tr>` +
    rows.join("");
}

function renderErrors(result) {
  const errs = [...(result.errors || []), ...(result.profile_warnings || [])];
  $("errors").innerHTML = errs.length
    ? errs.map((e) => `<div class="err-item">⚠ ${esc(e)}</div>`).join("")
    : "";
}

function render(text, result) {
  renderHighlight(text, result);
  renderSummary(result);
  renderFields(result);
  renderPersons(result);
  renderErrors(result);
  $("json").textContent = JSON.stringify(result, null, 2);
}

/* ---- Toolbar ---- */

$("btn-run").addEventListener("click", runEngine);
$("btn-reset").addEventListener("click", () => {
  if (defaultProfile) $("profile").value = JSON.stringify(defaultProfile, null, 2);
});
$("btn-export").addEventListener("click", () => {
  const blob = new Blob([$("profile").value], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "regex_workbench_profile.json";
  a.click();
  URL.revokeObjectURL(a.href);
});
$("btn-import").addEventListener("click", () => $("file-import").click());
$("file-import").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  ev.target.value = ""; // cho phép chọn lại đúng file vừa lỗi
  if (!file) return;
  try {
    const obj = JSON.parse(await file.text());
    $("profile").value = JSON.stringify(obj, null, 2);
    readProfile();
  } catch (err) {
    $("profile-status").textContent = "import thất bại: " + err.message;
    $("profile-status").className = "status bad";
  }
});
$("source").addEventListener("input", () => renderHighlight($("source").value, { zones: [], fields: [] }));

loadDefaultProfile();
