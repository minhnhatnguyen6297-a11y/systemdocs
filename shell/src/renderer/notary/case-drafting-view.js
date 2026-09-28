'use strict';

/* Case-drafting view — khung UI tab Soạn hồ sơ (MIN-111 → MIN-129 P6).
 *
 * SOT bo cuc: bản mẫu đã duyệt (docs/product/ui/prototypes +
 * references/approved-{drafting,land-types}.png):
 *   - Action bar gọn một hàng: back, loại việc, trạng thái lưu,
 *     Nhập file, Zalo (disabled placeholder), Hủy thay đổi, Cập nhật.
 *   - Stage: Tài sản bảng chuyển vị (mỗi tài sản MỘT CỘT, tối đa 3) /
 *     Người bảng dòng (mỗi người MỘT HÀNG, trường trong ô).
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

// Person stage columns — toàn bộ PERSON_FIELDS contract §13.3 (không bỏ
// trường nghiệp vụ). 4 cột đầu khớp bản mẫu; phần còn lại cuộn ngang.
const PERSON_COLS = [
  ['ho_ten', 'Họ tên'],
  ['ngay_sinh', 'Ngày sinh'],
  ['ngay_chet', 'Ngày mất'],
  ['so_giay_to', 'Số giấy tờ'],
  ['dia_chi', 'Địa chỉ'],
  ['gioi_tinh', 'Giới tính'],
  ['ngay_cap', 'Ngày cấp'],
  ['noi_cap', 'Nơi cấp'],
  ['place_of_origin', 'Nguyên quán'],
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
  ['hinh_thuc_su_dung', 'Hình thức sử dụng'],
  ['thoi_han', 'Thời hạn'],
  ['nguon_goc', 'Nguồn gốc'],
  ['ngay_cap', 'Ngày cấp'],
  ['co_quan_cap', 'Cơ quan cấp'],
];

const GIOI_TINH_OPTS = [['', '—'], ['Nam', 'Nam'], ['Nữ', 'Nữ']];

// Mã loại đất canonical backend
// (notary_v2/docs/platform/document-intake/property-rules.md §loai_dat).
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

  // ---------- modal canonical (DESIGN §6 / styles.css .modal-*) ----------
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
    async function loadList() {
      out.innerHTML = '';
      out.append(face(L.faceLoading('Đang tải danh sách hồ sơ…')));
      const r = await runCommand('notary.case_list',
                                 { query: q.value.trim() });
      out.innerHTML = '';
      if (!r.ok) {
        out.append(face(L.faceError(r.error)));
        if (isDevMode()) out.append(devQuickOpen(onOpen));
        return;
      }
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
    const create = btn('+ Hồ sơ mới', '', async () => {
      // Nháp mới thay toàn bộ draft hiện tại — hỏi khi có thay đổi
      // chưa lưu (case khác đang so / nháp khác đang dở).
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
      onNewDraft();
    });
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

  // ---------- action bar (approved: một hàng gọn) ----------

  function saveStateText() {
    const s = model.state;
    if (s.caseId == null) return 'Chưa lưu hồ sơ';
    if (s.stageDirty || s.diagramDirty) {
      const n = [];
      if (s.stageDirty) n.push('Stage');
      if (s.diagramDirty) n.push('Sơ đồ');
      return `Chưa lưu: ${n.join(' + ')}`;
    }
    return `Đã lưu · phiên bản ${s.revision}`;
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
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    } else {
      const r = await model.commitStage();
      if (!r.ok && r.error &&
          r.error.code !== 'stage_validation_error' &&
          r.error.code !== 'workspace_conflict') {
        notify(`${r.error.code}: ${r.error.message}`, true);
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

  function actionBarEl(onBack) {
    const s = model.state;
    const c = s.caseInfo || {};
    const draft = s.caseId == null;
    const bar = h('div', 'actionbar');
    const back = h('button', 'ab-back', '‹');
    back.type = 'button';
    back.setAttribute('aria-label', 'Quay lại Tổng quan hồ sơ');
    back.title = 'Quay lại Tổng quan hồ sơ';
    back.onclick = onBack;
    bar.append(back);
    bar.append(h('h1', 'ab-title', 'Soạn văn bản'));
    // Loại việc: nháp → select (ghi updateCaseMeta, đổi loại reset
    // diagram buffer §13.5); case thật → pill immutable.
    if (draft) {
      const sel = h('select', 'cd-case-type');
      for (const [v, lbl] of Object.entries(CASE_TYPE_LABEL)) {
        const o = h('option', '', lbl);
        o.value = v;
        if ((c.case_type || 'inheritance') === v) o.selected = true;
        sel.append(o);
      }
      sel.setAttribute('aria-label', 'Loại việc');
      sel.onchange = () => model.updateCaseMeta('case_type', sel.value);
      bar.append(sel);
    } else {
      bar.append(h('span', 'pill accent',
        CASE_TYPE_LABEL[c.case_type] || c.case_type || '—'));
    }
    if (draft) {
      bar.append(h('span', 'pill warn', 'Nháp — chưa lưu'));
    } else {
      bar.append(h('span', 'pill accent', `HS-${s.caseId}`));
      if (c.document_type) {
        bar.append(h('span', 'muted small',
          DOC_TYPE_LABEL[c.document_type] || c.document_type));
      }
    }
    if (s.locked) bar.append(h('span', 'pill warn', 'Đã khóa'));
    if (s.unsupported) {
      bar.append(h('span', 'pill err', 'Loại việc chưa hỗ trợ'));
    }
    if (s.stale) {
      bar.append(h('span', 'pill warn', 'Bản nháp cũ — server đã thay đổi'));
    }
    bar.append(h('span', 'spacer', ''));
    bar.append(h('span', 'save-state js-cd-save-state', saveStateText()));
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
    const undo = btn('Hủy thay đổi', 'js-cd-undo', cancelDraft);
    undo.disabled = !model.canWrite() || !model.hasUnsaved();
    undo.title = 'Bỏ thay đổi Stage + Sơ đồ chưa cập nhật (về bản đã lưu)';
    bar.append(undo);
    const primary = btn(draft ? 'Lưu hồ sơ' : 'Cập nhật',
      'primary js-cd-update', runCommit);
    if (draft ? (s.stageDirty || s.diagramDirty || s.metaDirty)
              : s.stageDirty) {
      primary.append(h('span', 'dirty-dot', ''));
      primary.setAttribute('aria-label',
        `${primary.textContent} — có thay đổi chưa lưu`);
    }
    primary.disabled = commitDisabled();
    bar.append(primary);
    return bar;
  }

  // Cập nhật gọn nút commit/undo/nhãn save khi rebuild bị defer (đang
  // gõ trong panel) — dirty state phải hiện ngay, không chờ blur.
  function syncChromeUI() {
    const s = model.state;
    const upd = root.querySelector('.js-cd-update');
    if (upd) {
      upd.disabled = commitDisabled();
      const dirty = s.caseId == null
        ? (s.stageDirty || s.diagramDirty || s.metaDirty)
        : s.stageDirty;
      let dot = upd.querySelector('.dirty-dot');
      if (dirty && !dot) upd.append(h('span', 'dirty-dot', ''));
      if (!dirty && dot) dot.remove();
    }
    const undo = root.querySelector('.js-cd-undo');
    if (undo) undo.disabled = !model.canWrite() || !model.hasUnsaved();
    const lbl = root.querySelector('.js-cd-save-state');
    if (lbl) lbl.textContent = saveStateText();
  }

  // Form meta của nháp mới (document_type + 3 field optional §4.3) —
  // chỉ render khi caseId=null; case_type nằm trên action bar.
  function draftMetaEl() {
    const s = model.state;
    if (s.caseId != null) return null;
    const c = s.caseInfo || {};
    const box = h('div', 'card');
    const head = h('div', 'card-head');
    head.append(h('h3', 'card-title', 'Thông tin hồ sơ'));
    box.append(head);
    const body = h('div', 'card-body cd-field-stack');
    const dt = h('label', 'cd-field');
    dt.append(h('span', 'muted', 'Loại văn bản'));
    const sel = h('select');
    // Enum document_type phụ thuộc case_type (contract §13.6).
    const docTypes = model.documentTypesFor
      ? model.documentTypesFor(c.case_type) : Object.keys(DOC_TYPE_LABEL);
    for (const v of docTypes) {
      const o = h('option', '', DOC_TYPE_LABEL[v] || v);
      o.value = v;
      if (c.document_type === v) o.selected = true;
      sel.append(o);
    }
    sel.setAttribute('aria-label', 'Loại văn bản');
    sel.onchange = () => model.updateCaseMeta('document_type', sel.value);
    dt.append(sel);
    body.append(dt);
    const f = (label, key) => {
      const lab = h('label', 'cd-field');
      lab.append(h('span', 'muted', label));
      const inp = h('input');
      inp.value = c[key] || '';
      inp.setAttribute('aria-label', label);
      inp.onchange = () => model.updateCaseMeta(key, inp.value);
      lab.append(inp);
      return lab;
    };
    body.append(f('Ngày lập hồ sơ', 'ngay_lap_ho_so'));
    body.append(f('Nơi niêm yết', 'noi_niem_yet'));
    body.append(f('Ghi chú', 'ghi_chu'));
    box.append(body);
    return box;
  }

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
      box.append(h('div', 'error small', er.message || er.code));
    }
    return box;
  }

  function cellErrs(rowId, field, td) {
    const errs = model.fieldErrorsFor(rowId)
      .filter((e) => e.field === field);
    for (const fe of errs) {
      td.classList.add('cd-cell-err');
      td.append(h('div', 'cd-err-msg', fe.message || fe.code));
    }
    return errs.length;
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
    const t = h('table', 'grid cd-tbl');
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
        } else {
          const inp = h('input');
          inp.value = a[key] || '';
          inp.disabled = ro;
          inp.setAttribute('aria-label', `${label} — Tài sản ${i + 1}`);
          inp.dataset.fid = `a:${a.row_id}:${key}`;
          inp.oninput = () => model.updateAssetField(
            a.row_id, key, inp.value);
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
    const t = h('table', 'grid cd-ptbl');
    const thead = h('thead');
    const trh = h('tr');
    trh.append(h('th', 'cd-drag-col', ''));
    if (inheritance) trh.append(h('th', 'cd-owner-col', 'Để lại'));
    for (const [, label] of PERSON_COLS) trh.append(h('th', '', label));
    trh.append(h('th', 'cd-drag-col', ''));
    thead.append(trh);
    t.append(thead);
    const tb = h('tbody');
    people.forEach((p, ri) => {
      const tr = h('tr');
      tr.dataset.rowIdx = String(ri);
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
      if (inheritance) {
        const tdo = h('td', 'cd-owner-cell');
        const ob = h('input');
        ob.type = 'radio';
        ob.name = 'cd-owner-row';
        ob.checked = s.stage.owner_row_id === p.row_id;
        ob.disabled = ro;
        ob.dataset.fid = `p:${p.row_id}:owner`;
        ob.setAttribute('aria-label',
          `Người để lại tài sản — ${p.ho_ten || `dòng ${ri + 1}`}`);
        ob.title = 'Người để lại tài sản (bắt buộc khi Cập nhật)';
        ob.onchange = () => model.setOwnerRow(p.row_id);
        tdo.append(ob);
        if (s.stage.owner_row_id === p.row_id) {
          tdo.classList.add('cd-owner-on');
        }
        tr.append(tdo);
      }
      for (const [key, label] of PERSON_COLS) {
        const td = h('td');
        let ctl;
        if (key === 'gioi_tinh') {
          ctl = h('select');
          for (const [v, lbl] of GIOI_TINH_OPTS) {
            const o = h('option', '', lbl);
            o.value = v;
            if ((p.gioi_tinh || '') === v) o.selected = true;
            ctl.append(o);
          }
          ctl.onchange = () => model.updatePersonField(
            p.row_id, key, ctl.value);
        } else {
          ctl = h('input');
          ctl.value = p[key] || '';
          if (key === 'dia_chi' && p[key]) ctl.title = p[key];
          ctl.oninput = () => model.updatePersonField(
            p.row_id, key, ctl.value);
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

  function stageTierEl() {
    const s = model.state;
    const wrap = h('div', 'cd-stage-wrap');
    const tier = h('div', 'cd-stage');

    // Card Tài sản (~36%)
    const ac = h('div', 'card cd-assets');
    const aHead = h('div', 'card-head');
    aHead.append(h('h3', 'card-title', `Tài sản (${s.stage.assets.length})`));
    const aTools = h('div', 'card-tools');
    const addA = btn('+ Tài sản', 'secondary sm', () => model.addAsset());
    // Tối đa 3 asset (§13.3) — hết slot thì disable nút thêm.
    const assetFull = s.stage.assets.length >= 3;
    addA.disabled = !model.canWrite() || assetFull;
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
      if (assetFull) {
        aBody.append(h('div', 'muted small', 'Tối đa 3 tài sản.'));
      }
    }
    ac.append(aBody);
    tier.append(ac);

    // Card Người (~64%)
    const pc = h('div', 'card cd-people');
    const pHead = h('div', 'card-head');
    pHead.append(h('h3', 'card-title', `Người (${s.stage.people.length})`));
    const pTools = h('div', 'card-tools');
    const addP = btn('+ Người', 'secondary sm', () => model.addPerson());
    // two_party: tối đa 30 người (§13.5) — hết slot thì disable.
    const peopleFull =
      (s.caseInfo && s.caseInfo.case_type === 'two_party') &&
      s.stage.people.length >= 30;
    addP.disabled = !model.canWrite() || peopleFull;
    pTools.append(addP);
    pHead.append(pTools);
    pc.append(pHead);
    const pBody = h('div', 'card-body cd-stage-body');
    for (const f of ['people', 'owner_row_id']) {
      const e = cardLevelErrors(f);
      if (e) pBody.append(e);
    }
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
      tray.append(h('div', 'error small', er.message || er.code));
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

  function workspaceEl(onBack) {
    const s = model.state;
    const ws = h('div', 'cd-workspace');
    if (s.backendMode === 'mock') {
      ws.append(h('div', 'banner ok', model.mockBanner()));
    }
    ws.append(actionBarEl(onBack));
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
      const eb = h('div', 'banner err',
        `${s.error.code}: ${s.error.message}`);
      const x = btn('×', 'ghost sm', () => model.dismissNotice());
      eb.append(h('span', 'grow', ''));
      eb.append(x);
      ws.append(eb);
    }
    const meta = draftMetaEl();
    if (meta) ws.append(meta);         // form meta nháp mới (§4.3)
    ws.append(stageTierEl());
    ws.append(relationTierEl());
    return ws;
  }

  // ---------- assembly: local nav + panels ----------

  const root = h('section', 'cd-root');
  const tabBar = h('div', 'cd-localnav');
  tabBar.setAttribute('role', 'tablist');
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
      notify(`openCase lỗi: ${e && e.message || e}`, true);
    }
  };

  panels.overview.append(buildCaseListPanel(openCaseInDrafting,
    () => { model.newDraft(); activeTab = 'drafting'; rerender(); }));
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
  root.append(tabBar);
  for (const k of Object.keys(panels)) root.append(panels[k]);

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
      return;
    }
    const cap = captureFocus(dp);
    dp.innerHTML = '';
    if (s.status === 'idle') {
      dp.append(face(L.faceEmpty(
        'Chưa mở hồ sơ — chọn hồ sơ ở tab Tổng quan hồ sơ.')));
      const go = btn('Đi tới Tổng quan hồ sơ', '', () => {
        activeTab = 'overview';
        rerender();
      });
      dp.append(go);
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
      dp.append(workspaceEl(() => {
        activeTab = 'overview';
        rerender();
      }));
      restoreFocus(dp, cap);
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
                DT_ASSET_COL, DT_PERSON_ROW },
};

if (typeof window !== 'undefined') window.G1_NOTARY_VIEW = G1_NOTARY_VIEW;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_VIEW;
}
