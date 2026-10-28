/* Probe DOM cho ui/app.js — chạy app.js THẬT với document/fetch stub tối thiểu.
 *
 * Mục đích: kiểm hành vi UI mà không cần trình duyệt: render kết quả lõi,
 * đặt đúng cột giấy tờ (`cccd`), bỏ response cũ (stale), hiện lỗi 400,
 * escape markup, tô vị trí giá trị sau emoji (index code point). Cầu nối lấy
 * hàm từ app.js chỉ nằm trong file test này — app.js không có hook cho test.
 *
 * In JSON: {checks: {name: {pass, detail}}, fails: [...]}
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const appJs = readFileSync(join(here, "..", "ui", "app.js"), "utf8");

class El {
  constructor(id) {
    this.id = id;
    this.value = "";
    this.checked = false;
    this.textContent = "";
    this.innerHTML = "";
    this.disabled = false;
    this.listeners = {};
  }
  addEventListener(type, fn) {
    (this.listeners[type] ||= []).push(fn);
  }
}

const elements = new Map();
const el = (id) => {
  if (!elements.has(id)) elements.set(id, new El(id));
  return elements.get(id);
};

const document = { getElementById: (id) => el(id) };
const window = {};

let queue = [];
const fetch = async (url) => {
  const next = queue.shift();
  if (!next) throw new Error("probe: không có response dựng sẵn cho " + url);
  if (next.delay) await new Promise((resolve) => setTimeout(resolve, next.delay));
  return { ok: next.ok !== false, json: async () => next.json };
};

const META = {
  engine: { id: "probe-engine", version: "probe-version" },
  web_form_fields: ["ten_hop_dong", "tai_san", "so_cong_chung"],
  raw_keys: ["ben_a", "ben_b", "danh_sach_thua_dat"],
};

const SAMPLE = [
  "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
  "I. BÊN CHUYỂN NHƯỢNG (Bên A):",
  "Ông: Nguyễn Văn An, sinh ngày: 10/05/1975;",
  "Căn cước công dân số: 001075000001 do Bộ Công an cấp ngày 15/03/2021;",
  "Thường trú tại: số 12 đường Láng, quận Đống Đa, Hà Nội.",
  "TÀI SẢN",
  "Tài sản thứ 1: Giấy chứng nhận số: B 011092; Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu",
  "Loại đất: Đất ở; Diện tích: 120 m2; Thời hạn: Lâu dài",
  "Số công chứng 428/2026/CCGD",
].join("\n");

function runPayload(marker) {
  return {
    payload: {
      case: {
        tenvanban: "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
        nhomhopdong: null, loaivanbannhandien: "transfer_contract",
        socongchung: marker, ngaycongchung: null, congchungvien: null,
        thuky: null, chudat: null,
      },
      web_form: {
        ten_hop_dong: "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT",
        tai_san: "Tài sản thứ 1: Giấy chứng nhận số: B 011092; Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu",
        so_cong_chung: marker,
      },
      raw: {
        extract_mode: "structured_docx",
        scan_contract_no: marker,
        file_goc: "",
        missing_web_form_fields: ["ngay_cong_chung"],
        tai_san_chua_ho_tro: ["số tài khoản"],
        nguoi_chet: [],
        ben_a: { nguoi: [{ ho_ten: "Nguyễn Văn An", ngay_sinh: "1975-05-10", cccd: "001075000001", cccd_khac: ["001075000002"], dia_chi: "số 12 đường Láng, quận Đống Đa, Hà Nội" }] },
        ben_b: { nguoi: [] },
        danh_sach_thua_dat: [{ so_thua_dat: "215", so_to_ban_do: "34", dia_chi: "xã Mẫu", dien_tich: "120", loai_dat: "Đất ở" }],
      },
    },
    groups: [
      { so_serial: "B 011092", dia_chi: "xã Mẫu, tỉnh Mẫu", so_thua_dat: "", so_to_ban_do: "", land_rows: [{ loai_dat: "Đất ở", dien_tich: "120 m2", thoi_han: "Lâu dài" }] },
    ],
    asset_context: { so_serial: "B 011092", co_quan_cap: "" },
  };
}

const checks = {};
const record = (name, fn) => {
  try {
    const detail = fn();
    checks[name] = { pass: detail !== false, detail: typeof detail === "string" ? detail : "" };
  } catch (err) {
    checks[name] = { pass: false, detail: String(err && err.message ? err.message : err) };
  }
};
const includes = (haystack, needle, what) => {
  if (!String(haystack).includes(needle)) throw new Error(`${what}: thiếu ${JSON.stringify(needle)}`);
};

// Meta response phục vụ loadMeta() chạy ngay khi app.js được nạp.
queue.push({ json: META });
// Cầu nối TEST-ONLY: nối vào cuối script để lấy đúng các hàm probe cần —
// khai báo `function` cấp cao trong app.js không tự thành global khi script
// chạy qua Function; app.js production không có hook nào cho test.
const BRIDGE = "globalThis.__probe = { esc, highlightIntervals, renderHighlight, runEngine };";
new Function("document", "window", "fetch", appJs + "\n" + BRIDGE)(document, window, fetch);
const wb = globalThis.__probe;
await new Promise((resolve) => setTimeout(resolve, 0));

await (async () => {
  el("source").value = SAMPLE;
  el("plain").checked = false;
  queue.push({ json: runPayload("428/2026/CCGD") });
  await wb.runEngine();
})();

record("normal_run_renders", () => {
  includes(el("fields").innerHTML, "HỢP ĐỒNG CHUYỂN NHƯỢNG QUYỀN SỬ DỤNG ĐẤT", "web_form table");
  includes(el("parcels").innerHTML, "215", "parcels table");
  const row = el("persons").innerHTML.split("<tr>").find((r) => r.includes("Nguyễn Văn An"));
  if (!row) throw new Error("persons: thiếu hàng Bên A");
  const cells = row.split("<td").slice(1);
  if (!cells[3] || !cells[3].includes("001075000001, 001075000002")) {
    throw new Error("persons: cột Giấy tờ sai nội dung: " + row);
  }
});

record("groups_and_land_rows_rendered", () => {
  includes(el("groups").innerHTML, "B 011092", "group serial");
  includes(el("groups").innerHTML, "Lâu dài", "land row thời hạn");
});

record("missing_and_unsupported_shown", () => {
  includes(el("summary").innerHTML, "ngay_cong_chung", "missing field badge");
  includes(el("summary").innerHTML, "số tài khoản", "unsupported asset badge");
});

record("highlight_marks_extracted_value", () => {
  const html = el("highlight").innerHTML;
  includes(html, 'class="mk"', "highlight span");
  includes(html, "Nguyễn Văn An", "highlighted value");
});

await (async () => {
  el("source").value = SAMPLE;
  queue.push({ json: runPayload("111/2026/CCGD"), delay: 40 });
  const pending = wb.runEngine();
  el("source").value = SAMPLE + "\n(chỉnh giữa chừng)";
  await pending;
})();

record("stale_source_after_run_discarded", () => {
  includes(el("errors").textContent, "đã thay đổi", "stale notice");
});

await (async () => {
  el("source").value = SAMPLE;
  queue.push({ json: runPayload("111/2026/CCGD"), delay: 40 });
  const first = wb.runEngine();
  queue.push({ json: runPayload("222/2026/CCGD") });
  const second = wb.runEngine();
  await Promise.all([first, second]);
})();

record("out_of_order_response_discarded", () => {
  includes(el("json").textContent, "222/2026/CCGD", "newest result rendered");
  if (el("json").textContent.includes("111/2026/CCGD")) throw new Error("response cũ ghi đè kết quả mới");
});

await (async () => {
  el("source").value = SAMPLE;
  queue.push({ ok: false, json: { error: "trường text phải là chuỗi văn bản nguồn" } });
  await wb.runEngine();
})();

record("server_error_displayed", () => {
  includes(el("errors").textContent, "trường text phải là chuỗi", "error text");
});

record("esc_escapes_text_and_attribute", () => {
  const out = wb.esc('a"b<c>&d\'e');
  includes(out, "&quot;", "quote escaped");
  includes(out, "&lt;c&gt;", "angle escaped");
  includes(out, "&amp;", "amp escaped");
  if (out.includes("<") || out.includes('"')) throw new Error("escape còn ký tự thô: " + out);
});

record("highlight_codepoint_after_emoji", () => {
  const value = "Nguyễn Văn An";
  const text = "😀 mở đầu\n" + value + " kết thúc";
  const intervals = wb.highlightIntervals(text, [{ value, label: "ben_a.ho_ten" }]);
  if (intervals.length !== 1) throw new Error("không dựng được interval");
  const cps = Array.from(text);
  const sliced = cps.slice(intervals[0].s, intervals[0].e).join("");
  if (sliced !== value) throw new Error(`slice lệch: ${JSON.stringify(sliced)}`);
  wb.renderHighlight(text, [{ value, label: "ben_a.ho_ten" }]);
  includes(el("highlight").innerHTML, value, "highlighted after emoji");
  includes(el("highlight").innerHTML, "😀", "emoji giữ nguyên");
});

record("highlight_escapes_markup", () => {
  const value = "<b>giá trị</b>";
  const text = "trước " + value + " sau";
  wb.renderHighlight(text, [{ value, label: "web_form.tai_san" }]);
  includes(el("highlight").innerHTML, "&lt;b&gt;", "escaped markup");
  if (el("highlight").innerHTML.includes("<b>")) throw new Error("markup thô lọt vào highlight");
});

const fails = Object.entries(checks).filter(([, info]) => !info.pass).map(([name]) => name);
process.stdout.write(JSON.stringify({ checks, fails }, null, 2));
