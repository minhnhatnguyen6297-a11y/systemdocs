/* Regex Workbench UI — vanilla JS, server Python chạy MỘT lõi luật.
   Luật nằm trong engine/contract_extract.py; UI này chỉ để dev soi kết quả
   trích xuất + chẩn đoán + vị trí giá trị trong nguồn. */
"use strict";

const $ = (id) => document.getElementById(id);
// Escape đầy đủ cho cả text node lẫn attribute (title="..."): giá trị/ nhãn
// chứa dấu ngoặc kép phải không phá được markup.
const esc = (s) => String(s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

let meta = null;
let runToken = 0;

/* ---- Meta (identity lõi) ---- */

async function loadMeta() {
  try {
    const res = await fetch("/api/meta");
    meta = await res.json();
  } catch (err) {
    meta = null;
  }
  renderEngine();
  return meta;
}

function renderEngine() {
  const el = $("engine");
  if (!el) return;
  if (!meta) {
    el.innerHTML = '<span class="badge err">không đọc được /api/meta</span>';
    return;
  }
  el.innerHTML =
    `<div><b>Lõi luật:</b> <span class="badge ok">${esc(meta.engine.id)}</span>` +
    ` <span class="mono">${esc(meta.engine.version)}</span></div>` +
    `<div class="muted small">Luật sửa trực tiếp trong <code>engine/contract_extract.py</code>; ` +
    `không có profile thứ hai, không có chọn/công bố rule trên UI.</div>`;
}

/* ---- Run ---- */

function plainText() {
  const el = $("plain");
  return !!(el && el.checked);
}

async function runEngine() {
  const source = $("source");
  // Snapshot lúc gửi: response thuộc về văn bản CŨ nếu user sửa trong lúc chờ.
  const sentText = source ? source.value : "";
  const token = ++runToken;
  const btn = $("btn-run");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: sentText, plain_text: plainText() }),
    });
    const data = await res.json();
    if (token !== runToken) return; // response cũ — bỏ
    if (!res.ok) {
      $("errors").textContent = data.error || "server error";
      return;
    }
    if (source && source.value !== sentText) {
      $("errors").textContent =
        "Văn bản nguồn đã thay đổi trong lúc chạy — bỏ qua kết quả cũ, nhấn Run lại.";
      return;
    }
    render(sentText, data);
  } catch (err) {
    if (token === runToken) $("errors").textContent = "lỗi gọi server: " + err.message;
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* ---- Vị trí giá trị trong nguồn (tìm chuỗi chính xác) ---- */

function cpIndex(text, utf16Index) {
  return Array.from(text.slice(0, utf16Index)).length;
}

function collectValues(data) {
  const out = new Map();
  const add = (value, label) => {
    const text = String(value == null ? "" : value).trim();
    if (text.length >= 2 && !out.has(text)) out.set(text, label);
  };
  const payload = (data && data.payload) || {};
  const webForm = payload.web_form || {};
  for (const [key, value] of Object.entries(webForm)) {
    if (typeof value === "string") add(value, "web_form." + key);
  }
  const raw = payload.raw || {};
  for (const side of ["ben_a", "ben_b"]) {
    for (const person of (raw[side] && raw[side].nguoi) || []) {
      for (const [key, value] of Object.entries(person)) {
        if (typeof value === "string") add(value, side + "." + key);
      }
    }
  }
  for (const parcel of raw.danh_sach_thua_dat || []) {
    for (const [key, value] of Object.entries(parcel)) {
      if (typeof value === "string") add(value, "thua_dat." + key);
    }
  }
  for (const group of (data && data.groups) || []) {
    for (const [key, value] of Object.entries(group)) {
      if (typeof value === "string") add(value, "nhom." + key);
    }
  }
  return [...out.entries()].map(([value, label]) => ({ value, label }));
}

function highlightIntervals(text, values) {
  const intervals = [];
  for (const { value, label } of values) {
    const at = text.indexOf(value);
    if (at < 0) continue; // giá trị đã chuẩn hóa/không còn nguyên văn — không tô
    intervals.push({
      s: cpIndex(text, at),
      e: cpIndex(text, at + value.length),
      label,
      warn: label.indexOf("chua_ho_tro") >= 0,
    });
  }
  return intervals.sort((a, b) => (a.s - b.s) || (b.e - a.e));
}

function renderHighlight(text, values) {
  const cps = Array.from(text);
  const intervals = highlightIntervals(text, values);
  const bounds = new Set([0, cps.length]);
  for (const iv of intervals) { bounds.add(iv.s); bounds.add(iv.e); }
  const points = [...bounds].sort((a, b) => a - b);

  let html = "";
  for (let i = 0; i < points.length - 1; i++) {
    const s = points[i], e = points[i + 1];
    const segment = cps.slice(s, e).join("");
    const hit = intervals.find((iv) => iv.s <= s && iv.e >= e);
    html += hit
      ? `<span class="${hit.warn ? "mk mk-warn" : "mk"}" title="${esc(hit.label)}">${esc(segment)}</span>`
      : esc(segment);
  }
  const el = $("highlight");
  if (el) el.innerHTML = html || '<span class="muted">(chưa có văn bản)</span>';
}

/* ---- Bảng & chẩn đoán ---- */

const RAW_LABELS = {
  ben_a: "Bên A", ben_b: "Bên B", nguoi_chet: "Người chết",
  tai_san_chua_ho_tro: "Tài sản chưa hỗ trợ",
};

function badge(text, kind) {
  return `<span class="badge ${kind}">${esc(text)}</span>`;
}

function renderSummary(data) {
  const payload = data.payload || {};
  const raw = payload.raw || {};
  const webForm = payload.web_form || {};
  const missing = raw.missing_web_form_fields || [];
  const unsupported = raw.tai_san_chua_ho_tro || [];
  const chips = missing.length
    ? missing.map((name) => badge(name, "miss")).join(" ")
    : badge("đủ trường bắt buộc", "ok");
  $("summary").innerHTML =
    `<div><b>Loại văn bản:</b> <code>${esc(raw.document_kind || "")}</code>` +
    ` · <b>chế độ:</b> <code>${esc(raw.extract_mode || "")}</code>` +
    ` · <b>số công chứng:</b> <code>${esc(raw.scan_contract_no || "—")}</code></div>` +
    `<div><b>File gốc:</b> <span class="mono">${esc(raw.file_goc || "(text dán)")}</span></div>` +
    `<div><b>Trường còn thiếu:</b> ${chips}</div>` +
    `<div><b>Tài sản chưa hỗ trợ:</b> ${unsupported.length ? unsupported.map((s) => badge(s, "warn")).join(" ") : '<span class="muted">không</span>'}</div>` +
    `<div><b>Người chết (di sản):</b> ${((raw.nguoi_chet) || []).length}</div>`;
}

function renderErrors(data) {
  const payload = data.payload || {};
  const items = [...(payload.raw && payload.raw.errors ? payload.raw.errors : [])];
  const el = $("errors");
  if (el) el.innerHTML = items.length ? items.map((e) => `<div class="err-item">⚠ ${esc(e)}</div>`).join("") : "";
}

function renderFields(data) {
  const webForm = (data.payload && data.payload.web_form) || {};
  const raw = (data.payload && data.payload.raw) || {};
  const missing = new Set(raw.missing_web_form_fields || []);
  const rows = Object.entries(webForm).map(([key, value]) =>
    `<tr><td class="mono">${esc(key)}</td>` +
    `<td class="val">${esc(value == null ? "" : value)}</td>` +
    `<td>${missing.has(key) ? badge("thiếu", "miss") : ""}</td></tr>`).join("");
  $("fields").innerHTML = "<tr><th>Trường</th><th>Giá trị</th><th></th></tr>" + rows;
}

function renderPersons(data) {
  const raw = (data.payload && data.payload.raw) || {};
  const rows = [];
  for (const side of ["ben_a", "ben_b", "nguoi_chet"]) {
    const block = raw[side];
    for (const person of (block && block.nguoi) || (Array.isArray(block) ? block : [])) {
      // ben_a/ben_b (person_row) dùng `cccd` + `cccd_khac`; người chết
      // (_extract_nguoi_chet) dùng `so_giay_to` cho trích lục khai tử.
      const giayTo = [person.cccd, ...(Array.isArray(person.cccd_khac) ? person.cccd_khac : [])]
        .filter(Boolean).join(", ") || person.so_giay_to || "";
      rows.push(`<tr><td>${esc(RAW_LABELS[side] || side)}</td>` +
        `<td class="val">${esc(person.ho_ten || "")}</td>` +
        `<td class="val">${esc(person.ngay_sinh || "")}</td>` +
        `<td class="val">${esc(giayTo)}</td>` +
        `<td class="val">${esc(person.dia_chi || "")}</td></tr>`);
    }
  }
  $("persons").innerHTML =
    "<tr><th>Khối</th><th>Họ tên</th><th>Ngày/năm sinh</th><th>Giấy tờ</th><th>Địa chỉ</th></tr>" + rows.join("");
}

function renderParcels(data) {
  const parcels = ((data.payload && data.payload.raw) || {}).danh_sach_thua_dat || [];
  const rows = parcels.map((parcel) =>
    `<tr><td class="mono">${esc(parcel.so_thua_dat || "")}</td>` +
    `<td class="mono">${esc(parcel.so_to_ban_do || "")}</td>` +
    `<td class="val">${esc(parcel.dia_chi || "")}</td>` +
    `<td class="val">${esc(parcel.dien_tich || "")}</td>` +
    `<td class="val">${esc(parcel.loai_dat || "")}</td></tr>`).join("");
  $("parcels").innerHTML =
    "<tr><th>Thửa</th><th>Tờ</th><th>Địa chỉ</th><th>Diện tích</th><th>Loại đất</th></tr>" + rows;
}

function renderGroups(data) {
  const groups = data.groups || [];
  const rows = [];
  for (const [index, group] of groups.entries()) {
    const landRows = group.land_rows || [];
    rows.push(`<tr><td class="mono">${index + 1}</td>` +
      `<td class="val">${esc(group.so_serial || "")}</td>` +
      `<td class="val">${esc(group.dia_chi || "")}</td>` +
      `<td class="val">${esc(group.so_thua_dat || "")}</td>` +
      `<td class="val">${esc(group.so_to_ban_do || "")}</td></tr>`);
    for (const [rowIndex, row] of landRows.entries()) {
      rows.push(`<tr><td class="mono">${index + 1}.${rowIndex + 1}</td>` +
        `<td class="val" colspan="2">${esc(row.loai_dat || "")}</td>` +
        `<td class="val">${esc(row.dien_tich || "")}</td>` +
        `<td class="val">${esc(row.thoi_han || "")}</td></tr>`);
    }
  }
  $("groups").innerHTML =
    "<tr><th>#</th><th>Serial</th><th>Địa chỉ</th><th>Thửa</th><th>Tờ</th></tr>" + rows.join("");
}

function renderContext(data) {
  const context = data.asset_context || {};
  const rows = Object.entries(context).map(([key, value]) =>
    `<tr><td class="mono">${esc(key)}</td><td class="val">${esc(Array.isArray(value) ? value.join(" | ") : value == null ? "" : value)}</td></tr>`).join("");
  $("context").innerHTML = "<tr><th>Khóa</th><th>Giá trị</th></tr>" + rows;
}

function render(text, data) {
  renderHighlight(text, collectValues(data));
  renderSummary(data);
  renderErrors(data);
  renderFields(data);
  renderPersons(data);
  renderParcels(data);
  renderGroups(data);
  renderContext(data);
  $("json").textContent = JSON.stringify(data, null, 2);
}

/* ---- Toolbar ---- */

const runButton = $("btn-run");
if (runButton && runButton.addEventListener) runButton.addEventListener("click", runEngine);
const sourceBox = $("source");
if (sourceBox && sourceBox.addEventListener) {
  sourceBox.addEventListener("input", () => renderHighlight(sourceBox.value, []));
}

loadMeta();
