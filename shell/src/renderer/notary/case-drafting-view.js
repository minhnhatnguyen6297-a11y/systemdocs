'use strict';

/* Case-drafting view — khung UI tab Soạn hồ sơ (MIN-111 → MIN-129 P6 →
 * MIN-133 W2 mật độ cao).
 *
 * SOT bo cuc: mockup MIN-133 đã duyệt (.agent/tasks/MIN-133/mockup/
 * mockup-1440x775.png) trên nền bản mẫu P6 (docs/spec/ui/prototypes):
 *   - Thanh trên DUY NHẤT (.cd-topbar, ~42px): tab cục bộ (Tổng quan /
 *     Soạn / Word) | loại việc, Nhập file, Zalo (disabled placeholder)
 *     ……… Hủy thay đổi, Lưu hồ sơ/Cập nhật (chấm dirty = tín hiệu chưa
 *     lưu duy nhất). Không nút back, không tiêu đề, không pill Nháp,
 *     không nhãn trạng thái lưu (MIN-133 D4/D5).
 *   - Không card Thông tin hồ sơ (D2): document_type theo mặc định model,
 *     ngay_lap_ho_so backend tự điền, noi_niem_yet/ghi_chu null.
 *   - Stage: Tài sản bảng chuyển vị (mỗi tài sản MỘT CỘT, tối đa 3) /
 *     Người bảng dòng (mỗi người MỘT HÀNG, 7 cột theo DB Customer — D1).
 *     table-layout fixed + colgroup, KHÔNG thanh cuộn trong Stage (D8).
 *   - Kéo-thả đổi vị trí cột tài sản / hàng người + đường bàn phím
 *     (Ctrl+←/→ cho cột, Ctrl+↑/↓ cho hàng). Reorder/re-render KHÔNG
 *     mất giá trị đang gõ hay focus (defer + data-fid restore).
 *   - Popup Loại đất: mỗi loại MỘT CỘT; "Áp dụng" chỉ ghi draft Stage
 *     + dirty; "Hủy" không đụng draft.
 *   - Reorder tài sản = đổi nghĩa vị trí (contract §13.3): dấu chọn
 *     ownPositions/receivePositions giữ SỐ vị trí, không bám row_id.
 *   - Hủy thay đổi = client-only restore cả Stage + Diagram draft về
 *     committed snapshots (§13.2 Q2) — không gọi command ra ngoài.
 *   - Chỉ render từ model.state — không tự suy luận nghiệp vụ, không
 *     render JSON kỹ thuật, không input ID bằng tay trong production view.
 *
 * Export UMD: window.G1_NOTARY_VIEW + module.exports. DOM chỉ được chạm
 * bên trong hàm build (file load được trong node --test để static test).
 */

const DOC_TYPE_LABEL = {
  khai_nhan: 'Khai nhận di sản',
  thoa_thuan: 'Thỏa thuận phân chia',
  // two_party document_type enum (contract §13.6).
  chuyen_nhuong: 'Chuyển nhượng',
  tang_cho: 'Tặng cho',
  cho_thue: 'Cho thuê',
  dat_coc: 'Đặt cọc',
};

const CASE_TYPE_LABEL = {
  inheritance: 'Thừa kế',
  two_party: 'Hai bên',
};

// Person stage columns — 7 cột đúng DB Customer (MIN-133 D1, owner chốt
// 28/09/2026). `noi_cap` (backend suy từ ngày cấp) và `place_of_origin`
// KHÔNG có ô nhập nhưng vẫn nằm trên row của model và đi nguyên vẹn lên
// wire (view không xóa key nào khỏi row) — không mất dữ liệu cũ.
const PERSON_COLS = [
  ['ho_ten', 'Họ tên'],
  ['gioi_tinh', 'Giới tính'],
  ['ngay_sinh', 'Ngày sinh'],
  ['ngay_chet', 'Ngày mất'],
  ['so_giay_to', 'Số giấy tờ'],
  ['ngay_cap', 'Ngày cấp'],
  ['dia_chi', 'Địa chỉ'],
];

// Asset stage rows — 4 hàng đầu khớp bản mẫu + 'land' chip + phần còn
// lại của ASSET_FIELDS contract §13.3 (không bỏ trường).
const ASSET_FIELD_ROWS = [
  ['so_serial', 'Số serial'],
  ['so_vao_so', 'Số vào sổ'],
  ['so_thua_dat', 'Thửa đất'],
  ['so_to_ban_do', 'Tờ bản đồ'],
  ['land', 'Loại đất'],            // chip mở dialog — không phải input
  ['dia_chi', 'Địa chỉ'],
  ['loai_so', 'Loại sổ'],
  ['hinh_thuc_su_dung', 'Hình thức SD'],     // MIN-136: viet tat giam rong
  ['thoi_han', 'Thời hạn'],
  ['nguon_goc', 'Nguồn gốc'],
  ['ngay_cap', 'Ngày cấp'],
  ['co_quan_cap', 'Cơ quan cấp'],
];

const GIOI_TINH_OPTS = [['', '—'], ['Nam', 'Nam'], ['Nữ', 'Nữ']];

// Mã loại đất canonical backend
// (docs/spec/notary_v2/input/property-rules.md §loai_dat).
// Giá trị ngoài danh sách được giữ làm option riêng — không mất dữ liệu.
const LAND_TYPE_CODES = ['ONT', 'ODT', 'CLN', 'NTS', 'LUC', 'BHK',
                         'SKC', 'TMD', 'DV', 'DGT', 'DKV', 'DHT'];

// Drag payload nội bộ Stage (index) — KHÁC với payload Pool/diagram
// ('text/plain' JSON {kind:'person', row_id} — giữ nguyên cho P7).
const DT_ASSET_COL = 'application/x-assetcol';
const DT_PERSON_ROW = 'application/x-personrow';

// INTAKE_KIND_LABEL/OBS_STATE_LABEL khai báo trong intake-dialog.js
// (load trước file này trong index.html) — script <script> thường share
// global scope nên không được redeclare const trùng tên. Tên riêng +
// typeof fallback giữ file require được độc lập trong node --test.
const _OBS_STATE_LABEL =
  (typeof OBS_STATE_LABEL !== 'undefined')
    ? OBS_STATE_LABEL
    : { observed: 'đọc được', normalized: 'đã chuẩn hóa', inferred: 'suy luận' };

// Dev flag: đặt window.G1_DEV = true trong DevTools để hiện mục debug
// (mở fixture mock nhanh). Production không có input ID bằng tay.
function isDevMode() {
  return typeof window !== 'undefined' && window.G1_DEV === true;
}

// ---------- pure helpers export được để node --test dùng ----------

// Splice helper reorder dùng chung cho cả asset col/person row
// (asset đi qua model.moveAsset; people đi qua movePersonRow bên dưới).
function spliceMove(list, from, to) {
  const i = from | 0, j = to | 0;
  if (i < 0 || i >= list.length || j < 0 || j >= list.length || i === j) {
    return false;
  }
  const [m] = list.splice(i, 1);
  list.splice(j, 0, m);
  return true;
}

// Client-only restore §13.2 Q2: Stage + Diagram draft về committed
// snapshot — KHÔNG gọi command nào ra ngoài. Model hiện chưa export
// cancelDraft() (ghi vào handoff); hàm này thực hiện đúng semantics bằng
// field public state + emit gián tiếp qua dismissNotice().
function cancelDraftState(state) {
  state.stage = structuredClone(state.committed);
  // Inheritance draft mới: committed rỗng thiếu key owner_row_id —
  // thêm lại để cột "Để lại" render được (§13.1 stage shape).
  if (state.caseId == null && state.caseInfo &&
      state.caseInfo.case_type !== 'two_party' &&
      !('owner_row_id' in state.stage)) {
    state.stage.owner_row_id = null;
  }
  state.diagram = structuredClone(state.committedDiagram);
  state.stageDirty = false;
  state.diagramDirty = false;
  state.fieldErrors = [];
  state.diagramErrors = [];
}

// Reorder 1 hàng people trên draft Stage — contract không cấm; thứ tự
// là thứ tự phụ lục/người ([Người N]). Model chưa export movePersonRow
// (ghi vào handoff) → view splice + đánh dấu dirty giống moveAsset.
// ---------- MIN-136: nhap/hien thi ngay dd/mm/yyyy ----------
// <input type=date> hien thi theo locale OS — may mm/dd/yyyy se sai
// yeu cau. Dung text input: nhap dd/mm/yyyy (chap nhan d/m/yyyy,
// ddmmyyyy 8 so, hoac yyyy cho truong nguoi — contract cho phep
// year-only); wire van gui ISO YYYY-MM-DD.
const PERSON_DATE_FIELDS = new Set(['ngay_sinh', 'ngay_chet', 'ngay_cap']);
const ASSET_DATE_FIELDS = new Set(['ngay_cap']);

// ISO 'YYYY-MM-DD'|'YYYY' → 'dd/mm/yyyy'|'yyyy'; dang khac (legacy)
// hien nguyen van.
function fmtDisplayDate(v) {
  const t = (v == null ? '' : String(v)).trim();
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(t);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  return t;
}

// 'dd/mm/yyyy' | 'd/m/yyyy' | 'ddmmyyyy' | 'yyyy'(allowYear) →
// { iso } | { error:'invalid' }. Ngay that khong ton tai (31/02,
// 29/02 khong nhuan) → invalid. '05/06/1990' LUON doc la dd/mm —
// quy uoc VN, khong mo ho mm/dd.
function parseDisplayDate(text, allowYear) {
  const t = (text == null ? '' : String(text)).trim();
  if (!t) return { iso: null };
  if (allowYear && /^\d{4}$/.test(t)) return { iso: t };
  const m = /^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$/.exec(t) ||
            /^(\d{2})(\d{2})(\d{4})$/.exec(t);
  if (!m) return { error: 'invalid' };
  const d = +m[1], mo = +m[2], y = +m[3];
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return { error: 'invalid' };
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 ||
      dt.getUTCDate() !== d) {
    return { error: 'invalid' };
  }
  const pad = (n, w) => String(n).padStart(w, '0');
  return { iso: `${pad(y, 4)}-${pad(mo, 2)}-${pad(d, 2)}` };
}

function movePersonRowState(state, rowId, toIndex) {
  const people = state.stage.people;
  const i = people.findIndex((p) => p.row_id === rowId);
  if (i < 0) return false;
  const j = Math.max(0, Math.min(toIndex | 0, people.length - 1));
  if (i === j) return true;
  spliceMove(people, i, j);
  // Mirror moveAsset: lỗi field của dòng vừa reorder được clear (lỗi
  // gắn row_id — reorder không đổi dữ liệu, lỗi từ lần commit trước
  // không còn nghĩa).
  state.fieldErrors = (state.fieldErrors || [])
    .filter((e) => e.row_id !== rowId);
  state.stageDirty = true;
  return true;
}

function createNotaryModuleView(deps) {
  const model = deps.model;
  const L = deps.lib;
  const notify = deps.notify || (() => {});
  // MIN-136: danh muc loi → thong diep than thien + rule an. Fallback
  // raw khi error-catalog chua nap (node --test tung file).
  const errCatalog = (typeof window !== 'undefined' &&
    window.G1_NOTARY_ERRORS) || null;
  const describeError = errCatalog ? errCatalog.describeError
    : (e) => ({ code: (e && e.code) || 'unknown',
                title: (e && e.message) || 'Lỗi', hint: null });
  const errText = errCatalog ? errCatalog.errText
    : (e) => `${e.code}: ${e.message}`;
  const pickFiles = deps.pickFiles || (async () => ({ ok: false }));
  const openPath = deps.openPath || (async () => ({ ok: false }));
  const confirm = deps.confirm ||
    (async () => true);
  const runCommand = deps.runCommand;
  // MIN-112 seams: drop-zone token + cancel job cho dialogs.
  const registerDroppedFile = deps.registerDroppedFile || null;
  const cancelJob = deps.cancelJob || (async () => ({ ok: false }));

  function h(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  // Button chuẩn token styles.css — class truyền thẳng (primary/
  // secondary/ghost/danger/sm map vào shared rules; cd-* cho nhu cầu
  // riêng của module).
  function btn(label, cls, onClick) {
    const b = h('button', (cls || '').trim(), label);
    b.type = 'button';
    if (onClick) b.onclick = onClick;
    return b;
  }

  function face(f) {
    // Dùng face descriptor của lib (vocabulary trạng thái chung).
    const box = h('div', `face face-${f.kind}`);
    box.append(h('div', 'face-title', f.title));
    if (f.detail) box.append(h('div', 'face-detail', f.detail));
    if (f.hint) box.append(h('div', 'face-hint muted', f.hint));
    return box;
  }

  // ---------- modal canonical (docs/spec/ui/README.md / styles.css .modal-*) ----------
  // wrap gắn vào .cd-root (không phải body) để cd-* trong dialog vẫn nằm
  // dưới scope module; position:fixed vẫn phủ viewport.
  // opts: {wide} → .modal.wide (≤1100px); {bare} → builder tự thêm
  //   modal-head/body/foot. Không bare → thêm .cd-modal (pad legacy cho
  //   dialog cũ như word-export — file đó ngoài sở hữu MIN-129).
  function openModal(build, opts) {
    const o = opts || {};
    const opener = document.activeElement;
    const wrap = h('div', 'modal-overlay');
    const box = h('div',
      'modal' + (o.wide ? ' wide' : '') + (o.bare ? '' : ' cd-modal'));
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    const close = () => {
      document.removeEventListener('keydown', onKey);
      wrap.remove();
      if (opener && opener.isConnected && opener.focus) opener.focus();
    };
    function onKey(e) {
      if (e.key === 'Escape') { close(); return; }
      if (e.key !== 'Tab') return;
      // Focus trap: Tab cycle trong dialog (MIN-112 a11y).
      const items = [...box.querySelectorAll(
        'button, input, textarea, select, [tabindex]')]
        .filter((x) => !x.disabled && !x.hidden);
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      const ae = document.activeElement;
      if (e.shiftKey && (ae === first || !box.contains(ae))) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && (ae === last || !box.contains(ae))) {
        e.preventDefault(); first.focus();
      }
    }
    wrap.onclick = (e) => { if (e.target === wrap) close(); };
    build(box, close);
    wrap.append(box);
    root.append(wrap);
    document.addEventListener('keydown', onKey);
    const first = box.querySelector('button, input, textarea, select');
    if (first) first.focus();
    return close;
  }

  // modal-close × dùng chung cho dialog canonical của module.
  function modalX(close) {
    const x = h('button', 'modal-close', '×');
    x.type = 'button';
    x.setAttribute('aria-label', 'Đóng');
    x.onclick = close;
    return x;
  }

  // ---------- MIN-112: dialogs + relation pane (file riêng, cùng helpers) ----------

  const intakeDlg = window.G1_NOTARY_INTAKE
    ? window.G1_NOTARY_INTAKE.createIntakeDialog({
        model, lib: L, notify, h, btn, face, openModal,
        pickFiles, registerDroppedFile, cancelJob })
    : null;
  const wordDlg = window.G1_NOTARY_WORD
    ? window.G1_NOTARY_WORD.createWordDialog({
        model, lib: L, notify, h, btn, face, openModal,
        pickFiles, openPath, cancelJob })
    : null;
  const diagramPane = window.G1_NOTARY_DIAGRAM
    ? window.G1_NOTARY_DIAGRAM.createDiagramPane({
        model, lib: L, notify, h, btn, face, openModal,
        openWordDialog: () => openWordDialog(),
        rerender: () => rerender() })
    : null;

  // ---------- Tổng quan hồ sơ (entry point: mở hồ sơ) ----------

  function buildCaseListPanel(onOpen, onNewDraft) {
    const s = h('section', 'cd-panel');
    s.append(h('p', 'muted',
      'Danh sách hồ sơ từ engine nghiệp vụ — bấm vào hồ sơ để mở ' +
      'workspace Soạn hồ sơ.'));
    const row = h('div', 'toolbar');
    const q = h('input');
    q.type = 'search';
    q.setAttribute('aria-label', 'Lọc hồ sơ theo từ khóa');
    q.placeholder = 'Lọc theo từ khóa…';
    q.oninput = () => loadList();           // lọc theo query trước limit
    const out = h('div', 'cd-slot');
    // MIN-136: race khoi dong — case_list chay ngay khi mo tab co the
    // gap luc sidecar chua ready → truoc day hien "submit_failed" tho
    // va khong tu retry. Retry toi da 5 lan cach 1.5s khi loi la infra;
    // loi khac hien danh muc than thien (khong con ma snake_case troi).
    const isInfraErr = (c) =>
      /^(engine_|file_scope|unsupported_contract|submit_failed)/.test(c || '');
    let infraFails = 0;
    let retryTimer = null;
    async function loadList() {
      out.innerHTML = '';
      out.append(face(L.faceLoading('Đang tải danh sách hồ sơ…')));
      const r = await runCommand('notary.case_list',
                                 { query: q.value.trim() });
      if (!r.ok) {
        out.innerHTML = '';
        const d = describeError(r.error);
        const f = face({
          kind: 'error',
          title: d.title,
          detail: d.raw && d.raw !== d.title ? d.raw : '',
          hint: (d.hint ? `${d.hint} ` : '') +
            (isInfraErr(d.code) && infraFails < 5
              ? `Tự thử lại… (${d.code})` : `[${d.code}]`),
        });
        out.append(f);
        if (isInfraErr(d.code) && infraFails < 5) {
          infraFails += 1;
          retryTimer = setTimeout(() => { void loadList(); }, 1500);
        } else {
          infraFails = 0;
        }
        if (isDevMode()) out.append(devQuickOpen(onOpen));
        return;
      }
      infraFails = 0;
      out.innerHTML = '';
      const cases = (r.data && r.data.cases) || [];
      const total = (r.data && r.data.total) ?? cases.length;
      out.append(h('div', 'muted cd-caselist-count',
        `${total} hồ sơ`));
      if (!cases.length) {
        out.append(face(L.faceEmpty('Chưa có hồ sơ nào.')));
      } else {
        const list = h('div', 'cd-caselist');
        for (const c of cases) {
          const name = c.nguoi_chet && c.nguoi_chet.ho_ten
            ? c.nguoi_chet.ho_ten : `Hồ sơ ${c.id}`;
          const sub = [c.tai_san && c.tai_san.so_serial,
                       c.ngay_lap_ho_so, c.trang_thai]
            .filter(Boolean).join(' · ');
          const item = btn('', 'cd-case-row', () => onOpen(c.id));
          item.append(h('span', 'cd-case-name', name));
          item.append(h('span', 'muted', sub || '—'));
          list.append(item);
        }
        out.append(list);
      }
      if (isDevMode()) out.append(devQuickOpen(onOpen));
    }
    const load = btn('Làm mới danh sách', 'primary', loadList);
    const create = btn('+ Hồ sơ mới', '', onNewDraft);
    row.append(create, q, load);
    s.append(row);
    s.append(out);
    // Auto-load khi vào tab (MIN-122) — không đợi người dùng bấm Tải.
    loadList();
    return s;
  }

  // Mục debug mở nhanh fixture mock — chỉ render khi G1_DEV bật.
  function devQuickOpen(onOpen) {
    const box = h('div', 'cd-dev');
    box.append(h('div', 'muted',
      'DEV (G1_DEV): mở nhanh fixture mock — nhập số hồ sơ:'));
    const row = h('div', 'toolbar');
    const inp = h('input');
    inp.type = 'number';
    inp.setAttribute('aria-label', 'DEV: id hồ sơ');
    inp.placeholder = 'id hồ sơ';
    const go = btn('Mở', '', () => {
      const id = parseInt(inp.value, 10);
      if (id > 0) onOpen(id);
    });
    row.append(inp, go);
    for (const id of [42, 43, 44, 45, 46]) {
      row.append(btn(`#${id}`, 'cd-chip', () => onOpen(id)));
    }
    box.append(row);
    return box;
  }

  // ---------- thanh trên: phần hành động (MIN-133 D4/D5) ----------
  // Tín hiệu chưa lưu duy nhất = chấm dirty trên nút Lưu/Cập nhật
  // (bỏ nhãn "Chưa lưu hồ sơ"/"Đã lưu · phiên bản N").

  function primaryDirty() {
    const s = model.state;
    return s.caseId == null
      ? (s.stageDirty || s.diagramDirty || s.metaDirty)
      : s.stageDirty;
  }

  // Commit/Cập nhật — điểm ghi duy nhất của Stage (§13.2). Nháp mới:
  // Lưu hồ sơ = workspace_create (ghi meta + stage + diagram cùng lúc).
  function commitDisabled() {
    const s = model.state;
    if (!model.canWrite()) return true;
    if (s.caseId == null) {
      return s.busy === 'notary.workspace_create';
    }
    return !s.stageDirty || s.busy === 'notary.workspace_commit_stage';
  }

  async function runCommit() {
    const s = model.state;
    if (s.caseId == null) {
      const r = await model.saveDraft();
      if (!r.ok && r.error &&
          r.error.code !== 'stage_validation_error' &&
          r.error.code !== 'diagram_invalid_state' &&
          r.error.code !== 'workspace_owner_required') {
        notify(errText(r.error), true);
      }
    } else {
      const r = await model.commitStage();
      if (!r.ok && r.error &&
          r.error.code !== 'stage_validation_error' &&
          r.error.code !== 'workspace_conflict') {
        notify(errText(r.error), true);
      }
    }
  }

  // Hủy thay đổi — client-only restore §13.2 Q2 (cả Stage lẫn Diagram
  // draft về committed); xác nhận trước vì hủy bỏ nháp đang sửa.
  async function cancelDraft() {
    const s = model.state;
    if (!model.canWrite() || !model.hasUnsaved()) return;
    const ok = await confirm({
      title: 'Hủy thay đổi chưa cập nhật?',
      body: 'Stage và sơ đồ quay về bản đã lưu gần nhất — thay đổi ' +
        'chưa cập nhật sẽ mất.',
      confirmLabel: 'Hủy thay đổi',
      cancelLabel: 'Ở lại',
    });
    if (!ok) return;
    if (s.caseId == null) {
      // Nháp chưa lưu: không có baseline committed — hủy = nháp mới
      // cùng loại việc. newDraft() reset toàn bộ + emit, không gọi
      // command nào ra ngoài.
      model.newDraft(s.caseInfo && s.caseInfo.case_type);
      return;
    }
    cancelDraftState(s);
    // model chưa export cancelDraft()/emit-only — dismissNotice() trigger
    // emit (xóa luôn notice/error cũ, hợp lý sau khi restore).
    model.dismissNotice();
  }

  // Điền phần hành động vào thanh trên (.cd-topbar-actions) — chỉ khi
  // tab Soạn hồ sơ đang mở một workspace. Thứ tự theo mockup MIN-133:
  // | loại việc · Nhập file · Zalo ……… [pill trạng thái] Hủy · Lưu •
  function fillTopActions(bar) {
    const s = model.state;
    const c = s.caseInfo || {};
    const draft = s.caseId == null;
    bar.append(h('span', 'cd-vsep', ''));
    // Loại việc: nháp → select (ghi updateCaseMeta, đổi loại reset
    // diagram buffer §13.5); case thật → pill immutable (loại · HS-id).
    if (draft) {
      const sel = h('select', 'cd-case-type');
      for (const [v, lbl] of Object.entries(CASE_TYPE_LABEL)) {
        const o = h('option', '', lbl);
        o.value = v;
        if ((c.case_type || 'inheritance') === v) o.selected = true;
        sel.append(o);
      }
      sel.value = c.case_type || 'inheritance';
      sel.setAttribute('aria-label', 'Loại việc');
      sel.dataset.fid = 'top:case_type';
      sel.onchange = () => model.updateCaseMeta('case_type', sel.value);
      bar.append(sel);
    } else {
      const pill = h('span', 'pill accent cd-case-pill',
        `${CASE_TYPE_LABEL[c.case_type] || c.case_type || '—'} · ` +
        `HS-${s.caseId}`);
      if (c.document_type) {
        pill.title = DOC_TYPE_LABEL[c.document_type] || c.document_type;
      }
      bar.append(pill);
    }
    // Intake duy nhất — mọi nguồn (file/ảnh/drop/text) qua dialog này.
    const intakeB = btn('Nhập file', '', () => openIntakeDialog(null));
    intakeB.disabled = !model.canWrite() ||
      !(s.capabilities.intake || []).length;
    intakeB.title = 'Nhập file/ảnh/tài liệu → gợi ý (chưa vào Stage)';
    bar.append(intakeB);
    // Zalo: giữ nút visible + disabled theo bản mẫu — module Zalo tách
    // repo (MIN-103), KHÔNG kéo engine vào lại.
    const zalo = btn('Zalo', '', null);
    zalo.disabled = true;
    zalo.title = 'Zalo — chưa bật trong phiên bản này';
    bar.append(zalo);
    bar.append(h('span', 'cd-spacer', ''));
    // Pill trạng thái chỉ khi thật sự có (locked/unsupported/stale) —
    // conflict đã có dialog riêng.
    if (s.locked) bar.append(h('span', 'pill warn', 'Đã khóa'));
    if (s.unsupported) {
      bar.append(h('span', 'pill err', 'Loại việc chưa hỗ trợ'));
    }
    if (s.stale) {
      const st = h('span', 'pill warn', 'Bản cũ');
      st.title = 'Bản nháp cũ — server đã thay đổi';
      bar.append(st);
    }
    const undo = btn('Hủy thay đổi', 'js-cd-undo', cancelDraft);
    undo.disabled = !model.canWrite() || !model.hasUnsaved();
    undo.title = 'Bỏ thay đổi Stage + Sơ đồ chưa cập nhật (về bản đã lưu)';
    bar.append(undo);
    const label = draft ? 'Lưu hồ sơ' : 'Cập nhật';
    const primary = btn(label, 'primary js-cd-update', runCommit);
    primary.dataset.label = label;
    setPrimaryDirty(primary, primaryDirty());
    primary.disabled = commitDisabled();
    bar.append(primary);
  }

  function setPrimaryDirty(upd, dirty) {
    const dot = upd.querySelector('.dirty-dot');
    if (dirty && !dot) upd.append(h('span', 'dirty-dot', ''));
    if (!dirty && dot) dot.remove();
    const label = upd.dataset.label || upd.textContent;
    if (dirty) {
      upd.setAttribute('aria-label', `${label} — có thay đổi chưa lưu`);
    } else {
      upd.removeAttribute('aria-label');
    }
  }

  // Cập nhật gọn nút commit/undo khi rebuild bị defer (đang gõ trong
  // panel) — dirty state phải hiện ngay, không chờ blur.
  function syncChromeUI() {
    const upd = root.querySelector('.js-cd-update');
    if (upd) {
      upd.disabled = commitDisabled();
      setPrimaryDirty(upd, primaryDirty());
    }
    const undo = root.querySelector('.js-cd-undo');
    if (undo) undo.disabled = !model.canWrite() || !model.hasUnsaved();
  }

  // MIN-133 D2: không còn card "Thông tin hồ sơ". Meta nháp mới đi lên
  // workspace_create theo mặc định của model — document_type =
  // documentTypesFor(case_type)[0], ngay_lap_ho_so null (backend tự điền
  // ngày hiện tại), noi_niem_yet/ghi_chu null. Chỗ nhập lại 4 trường này
  // do task Word quyết định; model.updateCaseMeta vẫn giữ nguyên.

  // ---------- Stage tier ----------

  // field_errors gắn row_id+field → cell err; lỗi cấp danh sách
  // (field 'assets'/'people'/'owner_row_id' hoặc không khớp cột) gom
  // hiển thị trên đầu card tương ứng.
  function cardLevelErrors(field) {
    const extra = (model.state.fieldErrors || [])
      .filter((e) => e.field === field);
    if (!extra.length) return null;
    const box = h('div', 'cd-row-errors');
    for (const er of extra) {
      box.append(h('div', 'error small', errLine(er)));
    }
    return box;
  }

  function cellErrs(rowId, field, td) {
    const errs = model.fieldErrorsFor(rowId)
      .filter((e) => e.field === field);
    for (const fe of errs) {
      td.classList.add('cd-cell-err');
      td.append(h('div', 'cd-err-msg', errLine(fe)));
    }
    return errs.length;
  }

  // Ô Stage cắt "…" khi dài (CSS) — tooltip = giá trị đầy đủ.
  function setCellTitle(inp) {
    inp.title = inp.value || '';
  }

  // Dong loi hien thi tu danh muc (MIN-136): catalog co entry →
  // title+hint than thien; khong co → message backend (thuong da la
  // tieng Viet, van tot hon snake_code troi).
  function errLine(er) {
    const d = describeError(er);
    return d.hint ? `${d.title} — ${d.hint}` : d.title;
  }

  // Ô ngay dd/mm/yyyy (MIN-136): hien fmtDisplayDate(row[key]); go raw
  // vao model de dirty live; blur/Enter parse → ISO len wire, repaint
  // display chuan. Sai format → danh dau do + giu raw (backend van
  // chan bang invalid_date khi luu — khong tham lang bo qua).
  function dateCellInput(getVal, onSet, allowYear, aria) {
    const inp = h('input', 'cd-cell cd-date');
    inp.value = fmtDisplayDate(getVal());
    inp.placeholder = allowYear ? 'dd/mm/yyyy hoặc năm' : 'dd/mm/yyyy';
    inp.setAttribute('inputmode', 'numeric');
    inp.maxLength = 10;
    setCellTitle(inp);
    inp.oninput = () => {
      setCellTitle(inp);
      inp.classList.remove('cd-input-bad');
      onSet(inp.value.trim() === '' ? null : inp.value);
    };
    inp.onchange = () => {
      const r = parseDisplayDate(inp.value, allowYear);
      if (r.error) {
        inp.classList.add('cd-input-bad');
        inp.title = 'Nhập ngày dạng dd/mm/yyyy';
        return;
      }
      inp.classList.remove('cd-input-bad');
      inp.value = fmtDisplayDate(r.iso);
      setCellTitle(inp);
      onSet(r.iso);
    };
    if (aria) inp.setAttribute('aria-label', aria);
    return inp;
  }

  // "+ Hồ sơ mới" — dung chung cho toolbar Tong quan va empty-state
  // tab Soạn hồ sơ (MIN-136): hoi truoc khi mat nhap dang so.
  async function newDraftFlow() {
    if (model.hasUnsaved()) {
      const okGo = await confirm({
        title: 'Thay đổi chưa lưu',
        body: 'Bản nháp hiện tại còn thay đổi chưa lưu — tạo hồ sơ ' +
          'mới sẽ mất bản nháp này.',
        confirmLabel: 'Bỏ nháp, tạo mới',
        cancelLabel: 'Ở lại',
      });
      if (!okGo) return;
    }
    model.newDraft();
    activeTab = 'drafting';
    rerender();
  }

  function dragHandle(label) {
    const grip = h('button', 'drag-handle', '⋮⋮');
    grip.type = 'button';
    grip.title = `${label} — kéo hoặc Ctrl+phím mũi tên`;
    grip.setAttribute('aria-label', label);
    return grip;
  }

  // --- Bảng chuyển vị Tài sản: mỗi tài sản MỘT CỘT (tối đa 3) ---

  function removeAssetAt(a, idx) {
    const total = model.state.stage.assets.length;
    const doRemove = async () => {
      // Xóa asset ở giữa dịch vị trí các cột sau — cảnh báo theo
      // contract §13.3 (dấu chọn giữ số vị trí, không bám row).
      if (idx < total - 1) {
        const ok = await confirm({
          title: 'Xóa tài sản',
          body: `Tài sản ở vị trí ${idx + 1} bị xóa sẽ đẩy các tài ` +
            'sản phía sau lên một vị trí — dấu chọn sở hữu/nhận trên ' +
            'sơ đồ giữ nguyên số vị trí (nghĩa thay đổi).',
          confirmLabel: 'Xóa tài sản',
          cancelLabel: 'Ở lại',
        });
        if (!ok) return;
      }
      model.removeStageRow(a.row_id);
    };
    return doRemove();
  }

  function assetTableEl() {
    const s = model.state;
    const ro = !model.canWrite();
    const assets = s.stage.assets;
    const t = h('table', 'grid cd-tbl cd-stage-tbl');
    // colgroup cố định (table-layout: fixed): nhãn 122px, các cột tài
    // sản chia đều phần còn lại — không min-width, không cuộn ngang.
    const cg = h('colgroup');
    cg.append(h('col', 'cd-acol-label'));
    for (let i = 0; i < assets.length; i++) cg.append(h('col', 'cd-acol'));
    t.append(cg);
    const thead = h('thead');
    const htr = h('tr');
    htr.append(h('th', 'cd-rowlabel', 'Thuộc tính'));
    assets.forEach((a, i) => {
      const th = h('th', 'cd-asset-col');
      th.dataset.colIdx = String(i);
      const head = h('div', 'cd-col-head');
      const grip = dragHandle(`kéo đổi vị trí Tài sản ${i + 1}`);
      grip.draggable = !ro;
      grip.dataset.fid = `adrag:${a.row_id}`;
      grip.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData(DT_ASSET_COL, String(i));
        e.dataTransfer.effectAllowed = 'move';
        th.classList.add('dragging');
      });
      grip.addEventListener('dragend', () => th.classList.remove('dragging'));
      // Đường bàn phím cho kéo-thả: Ctrl+←/→ = dời cột trái/phải —
      // đổi vị trí = đổi nghĩa (§13.3).
      grip.addEventListener('keydown', (e) => {
        if (!e.ctrlKey) return;
        const to = e.key === 'ArrowLeft' ? i - 1
          : e.key === 'ArrowRight' ? i + 1 : null;
        if (to == null || to < 0 || to >= assets.length) return;
        e.preventDefault();
        model.moveAsset(a.row_id, to);
      });
      const nm = h('span', 'grow', `Tài sản ${i + 1}`);
      nm.title = a.so_serial || `Tài sản ${i + 1}`;
      head.append(grip, nm);
      if (!ro) {
        const x = h('button', 'icon-x', '×');
        x.type = 'button';
        x.title = `Xóa Tài sản ${i + 1}`;
        x.setAttribute('aria-label', `Xóa Tài sản ${i + 1} (draft)`);
        x.dataset.fid = `adel:${a.row_id}`;
        x.onclick = () => removeAssetAt(a, i);
        head.append(x);
      }
      th.append(head);
      if (model.fieldErrorsFor(a.row_id).length) {
        th.classList.add('cd-col-err');
      }
      // Drop lên header cột j → chuyển asset kéo tới vị trí j (move-to
      // position semantics — các cột giữa dồn về phía khoảng trống).
      th.addEventListener('dragover', (e) => {
        if (e.dataTransfer.types.includes(DT_ASSET_COL)) {
          e.preventDefault();
          th.classList.add('col-drop-before');
        }
      });
      th.addEventListener('dragleave', () =>
        th.classList.remove('col-drop-before'));
      th.addEventListener('drop', (e) => {
        e.preventDefault();
        th.classList.remove('col-drop-before');
        const from = Number(e.dataTransfer.getData(DT_ASSET_COL));
        if (!Number.isInteger(from) || from === i || !assets[from]) return;
        model.moveAsset(assets[from].row_id, i);
      });
      htr.append(th);
    });
    thead.append(htr);
    t.append(thead);
    const tb = h('tbody');
    for (const [key, label] of ASSET_FIELD_ROWS) {
      const r = h('tr');
      r.append(h('td', 'cd-rowlabel', label));
      for (const a of assets) {
        const i = assets.indexOf(a);
        const td = h('td');
        if (key === 'land') {
          const rows = Array.isArray(a.land_rows) ? a.land_rows : [];
          const chip = btn(
            rows.length ? `${rows.length} loại ↗` : '+ Loại đất ↗',
            'cd-chip-link', () => openLandDialog(a, i));
          chip.disabled = ro;
          chip.dataset.fid = `a:${a.row_id}:land`;
          td.append(chip);
        } else if (ASSET_DATE_FIELDS.has(key)) {
          // Ngay cap tren GCN: backend chi nhan full ISO (valid_date_full)
          // — allowYear=false. Hien/nhap dd/mm/yyyy.
          const inp = dateCellInput(
            () => a[key],
            (v) => model.updateAssetField(a.row_id, key, v),
            false, `${label} — Tài sản ${i + 1}`);
          inp.disabled = ro;
          inp.dataset.fid = `a:${a.row_id}:${key}`;
          td.append(inp);
          cellErrs(a.row_id, key, td);
        } else {
          const inp = h('input', 'cd-cell');
          inp.value = a[key] || '';
          setCellTitle(inp);
          inp.disabled = ro;
          inp.setAttribute('aria-label', `${label} — Tài sản ${i + 1}`);
          inp.dataset.fid = `a:${a.row_id}:${key}`;
          inp.oninput = () => {
            setCellTitle(inp);
            model.updateAssetField(a.row_id, key, inp.value);
          };
          td.append(inp);
          cellErrs(a.row_id, key, td);
        }
        r.append(td);
      }
      tb.append(r);
    }
    t.append(tb);
    return t;
  }

  // --- Popup Loại đất: mỗi loại MỘT CỘT; Áp dụng → draft Stage ---

  function openLandDialog(asset, idx) {
    if (!model.canWrite()) return;
    // Draft riêng của dialog — Hủy/×/Esc/click nền không đụng Stage.
    const draft = structuredClone(
      Array.isArray(asset.land_rows) ? asset.land_rows : []);
    openModal((box, close) => {
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title', `Loại đất · Tài sản ${idx + 1}`));
      head.append(modalX(close));
      box.append(head);
      const body = h('div', 'modal-body');
      const tools = h('div', 'cd-land-tools');
      tools.append(btn('+ Loại đất', 'secondary', () => {
        draft.push({ loai_dat: 'ONT', dien_tich: null,
                     thoi_han: 'Lâu dài' });
        rebuild();
      }));
      body.append(tools);
      const tblWrap = h('div', 'cd-land-wrap');
      body.append(tblWrap);
      box.append(body);
      const foot = h('div', 'modal-foot');
      foot.append(btn('Hủy', 'ghost', close));
      const apply = btn('Áp dụng', 'primary', () => {
        // Chỉ ghi draft Stage (touchStage → dirty) — không gọi command
        // ra ngoài; Cập nhật ở action bar mới commit.
        const rows = draft.map((d) => ({
          loai_dat: d.loai_dat || null,
          dien_tich: d.dien_tich === '' || d.dien_tich == null ? null
            : (Number.isNaN(Number(d.dien_tich))
               ? d.dien_tich : Number(d.dien_tich)),
          thoi_han: d.thoi_han === '' ? null : (d.thoi_han || null),
        }));
        model.updateAssetField(asset.row_id, 'land_rows', rows);
        close();
      });
      foot.append(apply);
      box.append(foot);

      rebuild();
      function rebuild() {
        tblWrap.innerHTML = '';
        if (!draft.length) {
          const e = face(L.faceEmpty('Chưa có loại đất.'));
          const b = btn('+ Loại đất', '', () => {
            draft.push({ loai_dat: 'ONT', dien_tich: null,
                         thoi_han: 'Lâu dài' });
            rebuild();
          });
          e.append(b);
          tblWrap.append(e);
          return;
        }
        const t = h('table', 'grid cd-tbl');
        const trh = h('tr');
        trh.append(h('th', 'cd-rowlabel', ''));
        draft.forEach((row, ci) => {
          const th = h('th', 'cd-asset-col');
          const w = h('div', 'cd-col-head cd-land-head');
          const del = h('button', 'icon-x', '×');
          del.type = 'button';
          del.title = `Xóa thửa ${ci + 1}`;
          del.setAttribute('aria-label', `Xóa thửa ${ci + 1}`);
          del.addEventListener('click', () => {
            draft.splice(ci, 1);
            rebuild();
          });
          w.append(del);
          th.append(w);
          trh.append(th);
        });
        const thead = h('thead');
        thead.append(trh);
        t.append(thead);
        const tb = h('tbody');
        // Hàng Loại đất: select mã canonical + option giữ giá trị lạ.
        const lr = h('tr');
        lr.append(h('td', 'cd-rowlabel', 'Loại đất'));
        draft.forEach((row, ci) => {
          const td = h('td');
          const sel = h('select');
          const opts = LAND_TYPE_CODES.slice();
          if (row.loai_dat && !opts.includes(row.loai_dat)) {
            opts.push(row.loai_dat);
          }
          for (const o of opts) {
            const op = h('option', '', o);
            op.value = o;
            if ((row.loai_dat || 'ONT') === o) op.selected = true;
            sel.append(op);
          }
          sel.setAttribute('aria-label', `Loại đất — thửa ${ci + 1}`);
          sel.addEventListener('change', () => { row.loai_dat = sel.value; });
          td.append(sel);
          lr.append(td);
        });
        tb.append(lr);
        // Hàng Diện tích (m²) + Thời hạn — text input (wire string/number).
        const mkRow = (key, label, numeric) => {
          const r = h('tr');
          r.append(h('td', 'cd-rowlabel', label));
          draft.forEach((row, ci) => {
            const td = h('td');
            const inp = h('input');
            inp.value = row[key] == null ? '' : String(row[key]);
            if (numeric) inp.inputMode = 'numeric';
            inp.setAttribute('aria-label', `${label} — thửa ${ci + 1}`);
            inp.addEventListener('input', () => { row[key] = inp.value; });
            td.append(inp);
            r.append(td);
          });
          tb.append(r);
        };
        mkRow('dien_tich', 'Diện tích (m²)', true);
        mkRow('thoi_han', 'Thời hạn', false);
        t.append(tb);
        tblWrap.append(t);
      }
    }, { wide: true, bare: true });
  }

  // --- Bảng Người: mỗi người MỘT HÀNG, trường trong ô ---

  function movePersonRow(rowId, toIndex) {
    if (!model.canWrite()) return false;
    if (!movePersonRowState(model.state, rowId, toIndex)) return false;
    // Emit gián tiếp: model chưa export movePersonRow/emit-only — ghi
    // vào handoff. dismissNotice() trigger emit → rerender + hasUnsaved.
    model.dismissNotice();
    return true;
  }

  function peopleTableEl() {
    const s = model.state;
    const ro = !model.canWrite();
    const people = s.stage.people;
    const inheritance =
      (s.caseInfo && s.caseInfo.case_type) !== 'two_party' &&
      'owner_row_id' in s.stage;
    const t = h('table', 'grid cd-ptbl cd-stage-tbl');
    // colgroup cố định theo mockup MIN-133 + MIN-136 (bo cot "Để lại" —
    // chu dat chon qua so do): kéo 20 · Họ tên · Giới tính 64 · ngày ·
    // Số giấy tờ · Địa chỉ (phần còn lại) · xóa 24.
    const cg = h('colgroup');
    cg.append(h('col', 'cd-pcol-drag'));
    for (const [key] of PERSON_COLS) cg.append(h('col', `cd-pcol-${key}`));
    cg.append(h('col', 'cd-pcol-del'));
    t.append(cg);
    const thead = h('thead');
    const trh = h('tr');
    trh.append(h('th', 'cd-drag-col', ''));
    for (const [, label] of PERSON_COLS) trh.append(h('th', '', label));
    trh.append(h('th', 'cd-drag-col', ''));
    thead.append(trh);
    t.append(thead);
    const tb = h('tbody');
    people.forEach((p, ri) => {
      const tr = h('tr');
      tr.dataset.rowIdx = String(ri);
      if (inheritance && s.stage.owner_row_id === p.row_id) {
        tr.classList.add('cd-row-owner');
      }
      const tdh = h('td', 'cd-drag-col');
      const grip = dragHandle(
        `kéo đổi thứ tự dòng ${ri + 1} (${p.ho_ten || 'chưa tên'})`);
      grip.draggable = !ro;
      grip.dataset.fid = `pdrag:${p.row_id}`;
      grip.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData(DT_PERSON_ROW, String(ri));
        e.dataTransfer.effectAllowed = 'move';
        tr.classList.add('dragging');
      });
      grip.addEventListener('dragend', () =>
        tr.classList.remove('dragging'));
      // Ctrl+↑/↓ = đường bàn phím cho kéo-thả hàng.
      grip.addEventListener('keydown', (e) => {
        if (!e.ctrlKey) return;
        const to = e.key === 'ArrowUp' ? ri - 1
          : e.key === 'ArrowDown' ? ri + 1 : null;
        if (to == null || to < 0 || to >= people.length) return;
        e.preventDefault();
        movePersonRow(p.row_id, to);
      });
      tdh.append(grip);
      tr.append(tdh);
      // MIN-136: bo cot "Để lại" — chu dat chi chon qua o 'owner' tren
      // so do (owner_row_id sync san trong model). Hang cua chu dat
      // van sang nen de nhan biet (cd-row-owner).
      for (const [key, label] of PERSON_COLS) {
        const td = h('td');
        let ctl;
        if (key === 'gioi_tinh') {
          ctl = h('select', 'cd-cell');
          for (const [v, lbl] of GIOI_TINH_OPTS) {
            const o = h('option', '', lbl);
            o.value = v;
            if ((p.gioi_tinh || '') === v) o.selected = true;
            ctl.append(o);
          }
          ctl.onchange = () => model.updatePersonField(
            p.row_id, key, ctl.value);
        } else if (PERSON_DATE_FIELDS.has(key)) {
          // Ngay nguoi: allowYear — contract nhan year-only ("1950").
          ctl = dateCellInput(
            () => p[key],
            (v) => model.updatePersonField(p.row_id, key, v),
            true, `${label} — ${p.ho_ten || `dòng ${ri + 1}`}`);
        } else {
          ctl = h('input', 'cd-cell');
          ctl.value = p[key] || '';
          setCellTitle(ctl);
          const inp = ctl;
          inp.oninput = () => {
            setCellTitle(inp);
            model.updatePersonField(p.row_id, key, inp.value);
          };
        }
        ctl.disabled = ro;
        ctl.dataset.fid = `p:${p.row_id}:${key}`;
        ctl.setAttribute('aria-label',
          `${label} — ${p.ho_ten || `dòng ${ri + 1}`}`);
        td.append(ctl);
        cellErrs(p.row_id, key, td);
        tr.append(td);
      }
      const tdx = h('td', 'cd-drag-col');
      if (!ro) {
        const del = h('button', 'icon-x', '×');
        del.type = 'button';
        del.title = 'Xóa dòng (draft — hiệu lực sau Cập nhật)';
        del.dataset.fid = `pdel:${p.row_id}`;
        del.setAttribute('aria-label',
          `Xóa ${p.ho_ten || `dòng ${ri + 1}`}`);
        del.onclick = () => model.removeStageRow(p.row_id);
        tdx.append(del);
      }
      tr.append(tdx);
      // Drop: nửa trên/dưới hàng = chen trước/sau (shared
      // .row-drop-above/.row-drop-below).
      tr.addEventListener('dragover', (e) => {
        if (!e.dataTransfer.types.includes(DT_PERSON_ROW)) return;
        e.preventDefault();
        const r = tr.getBoundingClientRect();
        tr.classList.toggle('row-drop-above',
          e.clientY < r.top + r.height / 2);
        tr.classList.toggle('row-drop-below',
          e.clientY >= r.top + r.height / 2);
      });
      tr.addEventListener('dragleave', () =>
        tr.classList.remove('row-drop-above', 'row-drop-below'));
      tr.addEventListener('drop', (e) => {
        e.preventDefault();
        tr.classList.remove('row-drop-above', 'row-drop-below');
        const from = Number(e.dataTransfer.getData(DT_PERSON_ROW));
        if (!Number.isInteger(from) || from === ri || !people[from]) {
          return;
        }
        const r = tr.getBoundingClientRect();
        const to = e.clientY < r.top + r.height / 2 ? ri : ri + 1;
        movePersonRow(people[from].row_id, to > from ? to - 1 : to);
      });
      tb.append(tr);
    });
    t.append(tb);
    return t;
  }

  // "Tài sản (3)" — số đếm tông muted như mockup.
  function cardTitle(label, n) {
    const t = h('h3', 'card-title', `${label} `);
    t.append(h('span', 'cd-count', `(${n})`));
    return t;
  }

  // Lỗi trường người KHÔNG có ô trên Stage (noi_cap/place_of_origin sau
  // D1, hoặc field lạ) — gom lên đầu card để không bị nuốt mất.
  function hiddenPersonFieldErrors() {
    const shown = new Set(PERSON_COLS.map(([k]) => k));
    const rows = new Map(model.state.stage.people
      .map((p, i) => [p.row_id, p.ho_ten || `dòng ${i + 1}`]));
    const extra = (model.state.fieldErrors || []).filter((e) =>
      e.row_id != null && rows.has(e.row_id) && !shown.has(e.field));
    if (!extra.length) return null;
    const box = h('div', 'cd-row-errors');
    for (const er of extra) {
      box.append(h('div', 'error small',
        `${rows.get(er.row_id)} · ${er.field}: ${errLine(er)}`));
    }
    return box;
  }

  function stageTierEl() {
    const s = model.state;
    const wrap = h('div', 'cd-stage-wrap');
    const tier = h('div', 'cd-stage');

    // Card Tài sản (~36%)
    const ac = h('div', 'card cd-assets');
    const aHead = h('div', 'card-head');
    aHead.append(cardTitle('Tài sản', s.stage.assets.length));
    const aTools = h('div', 'card-tools');
    const addA = btn('+ Tài sản', 'secondary sm', () => model.addAsset());
    // Tối đa 3 asset (§13.3) — hết slot thì disable nút thêm.
    const assetFull = s.stage.assets.length >= 3;
    addA.disabled = !model.canWrite() || assetFull;
    if (assetFull) addA.title = 'Tối đa 3 tài sản';
    aTools.append(addA);
    aHead.append(aTools);
    ac.append(aHead);
    const aBody = h('div', 'card-body cd-stage-body');
    const aErr = cardLevelErrors('assets');
    if (aErr) aBody.append(aErr);
    if (!s.stage.assets.length) {
      const e = face(L.faceEmpty('Chưa có tài sản.'));
      const b = btn('+ Thêm tài sản đầu tiên', '', () => model.addAsset());
      b.disabled = !model.canWrite();
      e.append(b);
      aBody.append(e);
    } else {
      const twrap = h('div', 'cd-table-wrap');
      twrap.append(assetTableEl());
      aBody.append(twrap);
    }
    ac.append(aBody);
    tier.append(ac);

    // Card Người (~64%)
    const pc = h('div', 'card cd-people');
    const pHead = h('div', 'card-head');
    pHead.append(cardTitle('Người', s.stage.people.length));
    const pTools = h('div', 'card-tools');
    const addP = btn('+ Người', 'secondary sm', () => model.addPerson());
    // two_party: tối đa 30 người (§13.5) — hết slot thì disable.
    const peopleFull =
      (s.caseInfo && s.caseInfo.case_type === 'two_party') &&
      s.stage.people.length >= 30;
    addP.disabled = !model.canWrite() || peopleFull;
    if (peopleFull) addP.title = 'Tối đa 30 người';
    pTools.append(addP);
    pHead.append(pTools);
    pc.append(pHead);
    const pBody = h('div', 'card-body cd-stage-body');
    for (const f of ['people', 'owner_row_id']) {
      const e = cardLevelErrors(f);
      if (e) pBody.append(e);
    }
    const hidden = hiddenPersonFieldErrors();
    if (hidden) pBody.append(hidden);
    if (!s.stage.people.length) {
      const e = face(L.faceEmpty('Chưa có người nào trong Stage.'));
      const b = btn('+ Thêm người đầu tiên', '', () => model.addPerson());
      b.disabled = !model.canWrite();
      e.append(b);
      pBody.append(e);
    } else {
      const twrap = h('div', 'cd-table-wrap');
      twrap.append(peopleTableEl());
      pBody.append(twrap);
    }
    pc.append(pBody);
    tier.append(pc);
    wrap.append(tier);

    // Suggestion tray (intake results chờ review — không tự vào Stage)
    if (s.suggestions.length || s.intakeErrors.length) {
      wrap.append(suggestionTrayEl());
    }
    if (s.busy) {
      wrap.append(h('div', 'cd-busy muted small', 'Đang xử lý…'));
    }
    return wrap;
  }

  function suggestionTrayEl() {
    const s = model.state;
    const tray = h('div', 'card cd-suggest');
    tray.append(h('div', 'cd-suggest-title',
      'Gợi ý chờ kiểm tra — chưa ghi vào hồ sơ'));
    for (const er of s.intakeErrors || []) {
      tray.append(h('div', 'error small', errLine(er)));
    }
    for (const sug of s.suggestions) {
      const card = h('div', 'cd-suggest-card');
      const head = h('div', 'cd-suggest-head');
      head.append(h('span', 'pill',
        sug.target === 'asset' ? 'Tài sản' : 'Người'));
      const fieldBits = [];
      for (const [k, f] of Object.entries(sug.fields || {})) {
        const v = f && (f.normalized_value != null
          ? f.normalized_value : f.raw_value);
        const st = f && f.observation_state;
        fieldBits.push(`${k}: ${v == null ? '—' : v}` +
          (st ? ` (${_OBS_STATE_LABEL[st] || st})` : ''));
      }
      head.append(h('span', 'cd-suggest-text', fieldBits.join(' · ')));
      card.append(head);
      const actions = h('div', 'toolbar');
      const put = btn('Đưa vào Stage', 'primary sm', () => {
        model.acceptSuggestion(sug.suggestion_id);
      });
      put.disabled = !model.canWrite();
      const drop = btn('Bỏ qua', 'ghost sm', () =>
        model.discardSuggestion(sug.suggestion_id));
      actions.append(put, drop);
      card.append(actions);
      for (const w of sug.warnings || []) {
        card.append(h('div', 'muted small warn-text', w.message || w.code));
      }
      tray.append(card);
    }
    return tray;
  }

  // ---------- Relation tier: Pool + Diagram (MIN-112 — tách file) ----------
  // Pane duy nhất cho cả phiên: giữ debounce timer + trạng thái Xem cách
  // tính/lọc pool qua các lần rebuild (rerender tạo subtree mới nhưng pane
  // instance giữ nguyên state này).

  function relationTierEl() {
    return diagramPane ? diagramPane.build()
      : face(L.faceUnavailable('Sơ đồ', 'module_missing',
        'relationship-diagram.js chưa nạp.'));
  }

  // ---------- intake / word dialogs (MIN-112 — tách file) ----------

  function openIntakeDialog(presetKind) {
    if (intakeDlg) intakeDlg.open(presetKind);
    else notify('intake-dialog.js chưa nạp.', true);
  }

  function openWordDialog() {
    if (wordDlg) wordDlg.open();
    else notify('word-export-dialog.js chưa nạp.', true);
  }

  // ---------- conflict dialog ----------

  function conflictDialog() {
    const s = model.state;
    openModal((box, close) => {
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title',
        'Hồ sơ đã thay đổi trên máy chủ'));
      head.append(modalX(close));
      box.append(head);
      const body = h('div', 'modal-body');
      body.append(h('div', 'muted',
        `Phiên bản hiện tại: ${s.conflict.server_revision ?? '—'} — ` +
        'bản bạn đang sửa dựa trên phiên bản cũ hơn.'));
      body.append(h('div', 'muted',
        'Không có ghi đè cưỡng bức — bản nháp chỉ để bạn sao chép tay.'));
      box.append(body);
      const foot = h('div', 'modal-foot');
      const reload = btn('Tải bản mới', 'primary', async () => {
        await model.resolveConflict('reload');
        close();
      });
      const keep = btn('Giữ bản nháp để sao chép', '', () => {
        model.resolveConflict('keep');
        close();
      });
      foot.append(keep, reload);
      box.append(foot);
    }, { bare: true });
  }

  // ---------- workspace root ----------

  // Thanh trên (tab + hành động) nằm ngoài panel — xem .cd-topbar bên
  // dưới. Workspace = banner (nếu có) + Stage + vùng sơ đồ.
  function workspaceEl() {
    const s = model.state;
    const ws = h('div', 'cd-workspace');
    if (s.backendMode === 'mock') {
      ws.append(h('div', 'banner ok', model.mockBanner()));
    }
    if (s.unsupported) {
      ws.append(h('div', 'banner warn',
        `Loại việc “${s.caseInfo && s.caseInfo.case_type}” — Chưa hỗ trợ. ` +
        'Chỉ đọc dữ liệu hiện có.'));
    }
    if (s.locked) {
      ws.append(h('div', 'banner warn',
        'Hồ sơ đã khóa — toàn bộ chỉ đọc, vẫn xem/sao chép được.'));
    }
    if (s.notice) {
      const n = h('div', 'banner ok', s.notice);
      const x = btn('×', 'ghost sm', () => model.dismissNotice());
      n.append(h('span', 'grow', ''));
      n.append(x);
      ws.append(n);
    }
    if (s.error && s.status !== 'error' && s.status !== 'unavailable') {
      const ed = describeError(s.error);
      const eb = h('div', 'banner err',
        `${ed.title}${ed.hint ? ' — ' + ed.hint : ''} `);
      eb.append(h('span', 'muted small', `(${ed.code})`));
      const x = btn('×', 'ghost sm', () => model.dismissNotice());
      eb.append(h('span', 'grow', ''));
      eb.append(x);
      ws.append(eb);
    }
    ws.append(stageTierEl());
    ws.append(relationTierEl());
    return ws;
  }

  // ---------- assembly: local nav + panels ----------

  const root = h('section', 'cd-root');
  // MIN-133 D5: MỘT thanh cao ~42px = tab cục bộ + hành động workspace.
  // Tab bar sống suốt phiên; .cd-topbar-actions dựng lại theo state và
  // chỉ hiện khi tab Soạn hồ sơ đang có workspace.
  const topBar = h('div', 'card cd-topbar');
  const tabBar = h('div', 'cd-localnav');
  tabBar.setAttribute('role', 'tablist');
  const topActions = h('div', 'cd-topbar-actions');
  topBar.append(tabBar, topActions);
  const panels = {
    overview: h('div', 'cd-tabpage'),
    drafting: h('div', 'cd-tabpage'),
    word: h('div', 'cd-tabpage'),
  };
  let activeTab = 'drafting';
  let lastConflict = null;

  const TABS = [
    { id: 'overview', label: 'Tổng quan hồ sơ' },
    { id: 'drafting', label: 'Soạn hồ sơ' },
    { id: 'word', label: 'Word' },
  ];

  const openCaseInDrafting = async (id) => {
    // Mở case khác sẽ thay toàn bộ draft — hỏi trước khi mất nháp.
    if (model.hasUnsaved()) {
      const ok = await confirm({
        title: 'Thay đổi chưa lưu',
        body: 'Stage/Sơ đồ còn bản nháp chưa lưu — mở hồ sơ khác sẽ mất ' +
          'bản nháp hiện tại.',
        confirmLabel: 'Bỏ nháp và mở',
        cancelLabel: 'Ở lại',
      });
      if (!ok) return;
    }
    activeTab = 'drafting';
    try {
      await model.openCase(id);
    } catch (e) {
      // client.run reject (bridge/engine lỗi không bắt được) — model đã
      // set state lỗi riêng; đây chỉ chặn unhandled rejection.
      notify(errText(e && e.code ? e
        : { code: 'shell_internal_error',
            message: (e && e.message) || String(e) }), true);
    }
  };

  panels.overview.append(buildCaseListPanel(openCaseInDrafting,
    newDraftFlow));
  const wordPlaceholder = face(L.faceEmpty(
    'Tab Word — nội dung surface văn bản ở lát cắt sau (spec §1). ' +
    'Điểm vào xuất Word nằm trong Soạn hồ sơ → Xuất Word.'));
  panels.word.append(wordPlaceholder);

  for (const t of TABS) {
    const b = btn(t.label, 'cd-tab', () => {
      activeTab = t.id;
      rerender();
    });
    b.dataset.tab = t.id;
    b.setAttribute('role', 'tab');
    tabBar.append(b);
  }
  root.append(topBar);
  for (const k of Object.keys(panels)) root.append(panels[k]);

  const NO_WORKSPACE = ['idle', 'loading', 'unavailable', 'error'];

  function renderTopActions() {
    const s = model.state;
    const show = activeTab === 'drafting' && !NO_WORKSPACE.includes(s.status);
    topActions.hidden = !show;
    // Select loại việc đang focus (vừa đổi / đang mở bằng bàn phím):
    // không thay node để không đóng dropdown — chỉ đồng bộ nút.
    const ae = document.activeElement;
    if (show && s.caseId == null && ae && ae.tagName === 'SELECT' &&
        topActions.contains(ae)) {
      syncChromeUI();
      return;
    }
    topActions.innerHTML = '';
    if (show) fillTopActions(topActions);
  }

  // data-fid ổn định trên control → sau rebuild, focus quay về đúng
  // phần tử logic (row_id + field/handle), kể cả khi vị trí đã đổi.
  function captureFocus(dp) {
    const ae = document.activeElement;
    if (!ae || !dp.contains(ae)) return null;
    const fid = ae.dataset && ae.dataset.fid;
    if (!fid) return null;
    return {
      fid,
      sel: (typeof ae.selectionStart === 'number')
        ? [ae.selectionStart, ae.selectionEnd] : null,
    };
  }

  function restoreFocus(dp, cap) {
    if (!cap) return;
    const el = dp.querySelector(`[data-fid="${cap.fid}"]`);
    if (!el || !el.focus) return;
    el.focus();
    if (cap.sel && typeof el.setSelectionRange === 'function') {
      try { el.setSelectionRange(cap.sel[0], cap.sel[1]); } catch (e) { }
    }
  }

  function rerender() {
    const s = model.state;
    for (const b of tabBar.querySelectorAll('.cd-tab')) {
      const on = b.dataset.tab === activeTab;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', String(on));
    }
    for (const [k, el] of Object.entries(panels)) {
      el.hidden = k !== activeTab;
    }
    const dp = panels.drafting;
    // Emit nền (jobUpdate/status poll) trong lúc đang gõ trong drafting
    // panel: hoãn rebuild để input không mất focus/giá trị — render sau
    // lần emit kế tiếp (blur/change hoặc action tiếp theo của người
    // dùng). Chỉ nút commit/undo/nhãn save được cập nhật gọn ngay.
    const ae = document.activeElement;
    if (ae && dp.contains(ae) &&
        /^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName || '')) {
      syncChromeUI();
      // MIN-136 F-1: rebuild bi hoan khi dang go — nhung dialog
      // conflict phai hien NGAY (server tu choi commit thi user can
      // biet lieu ke, khong doi blur/emit sau).
      if (s.status === 'conflict' && s.conflict !== lastConflict) {
        lastConflict = s.conflict;
        conflictDialog();
      }
      return;
    }
    const cap = captureFocus(root);
    renderTopActions();
    dp.innerHTML = '';
    if (s.status === 'idle') {
      dp.append(face(L.faceEmpty(
        'Chưa mở hồ sơ — tạo hồ sơ mới hoặc chọn hồ sơ ở tab Tổng quan.')));
      const acts = h('div', 'toolbar');
      acts.append(
        btn('+ Hồ sơ mới', 'primary', newDraftFlow),
        btn('Đi tới Tổng quan hồ sơ', '', () => {
          activeTab = 'overview';
          rerender();
        }));
      dp.append(acts);
    } else if (s.status === 'loading') {
      dp.append(face(L.faceLoading('Đang tải workspace…')));
    } else if (s.status === 'unavailable') {
      const retry = btn('Thử lại', '', () => openCaseInDrafting(s.caseId));
      const f = face(L.faceUnavailable(
        'Engine', 'engine_unavailable',
        'Workspace không tải được khi engine chưa sẵn sàng.'));
      f.append(retry);
      dp.append(f);
    } else if (s.status === 'error') {
      const f = face(L.faceError(s.error || { code: 'unknown' }));
      const back = btn('← Quay lại Tổng quan', '', () => {
        activeTab = 'overview';
        rerender();
      });
      f.append(back);
      dp.append(f);
    } else {
      // ready / locked / conflict — conflict vẫn render workspace + dialog
      dp.append(workspaceEl());
      restoreFocus(root, cap);
      if (s.status === 'conflict' && s.conflict !== lastConflict) {
        lastConflict = s.conflict;
        conflictDialog();
      } else if (s.status !== 'conflict') {
        lastConflict = null;
      }
    }
  }

  model.subscribe(rerender);
  rerender();

  return {
    el: root,
    refresh() { rerender(); },
    model,
    hasUnsaved: () => model.hasUnsaved(),
    activeCaseId: () => model.state.caseId,
  };
}

const G1_NOTARY_VIEW = {
  createNotaryModuleView, isDevMode,
  // pure helpers export cho node --test (không cần DOM).
  _internals: { spliceMove, cancelDraftState, movePersonRowState,
                LAND_TYPE_CODES, PERSON_COLS, ASSET_FIELD_ROWS,
                DT_ASSET_COL, DT_PERSON_ROW,
                PERSON_DATE_FIELDS, ASSET_DATE_FIELDS,
                fmtDisplayDate, parseDisplayDate },
};

if (typeof window !== 'undefined') window.G1_NOTARY_VIEW = G1_NOTARY_VIEW;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_VIEW;
}
