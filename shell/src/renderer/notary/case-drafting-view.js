'use strict';

/* Case-drafting view — khung UI tab Soạn hồ sơ (MIN-111).
 *
 * SOT bo cuc: docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md
 * §1.2 — context bar; Stage Tài sản 36 / Người 64; Pool 22 / Diagram 78.
 * Chi render tu model.state — khong tu suy luan nghiep vu, khong render
 * JSON ky thuat, khong input ID bang tay trong production view.
 *
 * Export UMD: window.G1_NOTARY_VIEW + module.exports. DOM chi duoc cham
 * ben trong ham build (file load duoc trong node --test de static test).
 */

// Nhan hien thi cho cac truong hop spec §5 — khong hien data-code tho.
const BLOCK_REASON_LABEL = {
  'word.no_assets': 'Hồ sơ chưa có tài sản',
  'word.no_landowner': 'Chưa có chủ đất trên sơ đồ',
  'word.no_deceased_landowner': 'Chưa có chủ đất đã mất',
  'word.no_receiver': 'Chưa có người nhận',
  'word.too_many_assets': 'Quá nhiều tài sản (tối đa 5)',
  'word.too_many_people': 'Quá nhiều người trên sơ đồ (tối đa 20)',
  'word.too_many_signers': 'Quá nhiều người ký (tối đa 20)',
  'word.template_missing': 'Văn bản chưa có mẫu',
};

const DOC_TYPE_LABEL = {
  khai_nhan: 'Khai nhận di sản',
  thoa_thuan: 'Thỏa thuận phân chia',
};

const INTAKE_KIND_LABEL = {
  image: 'ảnh', pdf: 'PDF', docx: 'Word', xlsx: 'Excel', text: 'văn bản',
};

const OBS_STATE_LABEL = {
  observed: 'đọc được', normalized: 'đã chuẩn hóa', inferred: 'suy luận',
};

// Dev flag: dat window.G1_DEV = true trong DevTools de hien muc debug
// (mo fixture mock nhanh). Production khong co input ID bang tay.
function isDevMode() {
  return typeof window !== 'undefined' && window.G1_DEV === true;
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

  function btn(label, cls, onClick) {
    const b = h('button', `cd-btn ${cls || ''}`.trim(), label);
    b.type = 'button';
    if (onClick) b.onclick = onClick;
    return b;
  }

  function face(f) {
    // Dung face descriptor cua lib (vocabulary trang thai chung).
    const box = h('div', `face face-${f.kind}`);
    box.append(h('div', 'face-title', f.title));
    if (f.detail) box.append(h('div', 'face-detail', f.detail));
    if (f.hint) box.append(h('div', 'face-hint muted', f.hint));
    return box;
  }

  // ---------- modal nho gon (backdrop + dialog) ----------

  function openModal(build) {
    const wrap = h('div', 'cd-modal-backdrop');
    const box = h('div', 'cd-modal');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    const close = () => {
      document.removeEventListener('keydown', onKey);
      wrap.remove();
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
    document.body.append(wrap);
    document.addEventListener('keydown', onKey);
    const first = box.querySelector('button, input, textarea, select');
    if (first) first.focus();
    return close;
  }

  // ---------- MIN-112: dialogs + relation pane (file rieng, cung helpers) ----------

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

  // ---------- Tổng quan hồ sơ (entry point: mo ho so) ----------

  function buildCaseListPanel(onOpen) {
    const s = h('section', 'cd-panel');
    s.append(h('p', 'muted',
      'Danh sách hồ sơ từ engine nghiệp vụ — bấm vào hồ sơ để mở ' +
      'workspace Soạn hồ sơ.'));
    const row = h('div', 'cd-toolbar');
    const q = h('input', 'cd-input');
    q.type = 'search';
    q.setAttribute('aria-label', 'Lọc hồ sơ theo từ khóa');
    q.placeholder = 'Lọc theo từ khóa…';
    const load = btn('Tải danh sách', 'primary', async () => {
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
    });
    row.append(q, load);
    s.append(row);
    const out = h('div', 'cd-slot');
    s.append(out);
    return s;
  }

  // Muc debug mo nhanh fixture mock — chi render khi G1_DEV bat.
  function devQuickOpen(onOpen) {
    const box = h('div', 'cd-dev');
    box.append(h('div', 'muted',
      'DEV (G1_DEV): mở nhanh fixture mock — nhập số hồ sơ:'));
    const row = h('div', 'cd-toolbar');
    const inp = h('input', 'cd-input');
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

  // ---------- context bar ----------

  function contextBar(onBack) {
    const s = model.state;
    const bar = h('div', 'cd-context');
    const back = btn('← Tổng quan', 'cd-back', onBack);
    bar.append(back);
    const c = s.caseInfo || {};
    const title = h('span', 'cd-case-title',
      `Hồ sơ #${s.caseId} · ${DOC_TYPE_LABEL[c.document_type] ||
        c.document_type || '—'}`);
    bar.append(title);
    const typeBadge = h('span', 'cd-badge',
      c.case_type === 'inheritance' ? 'Thừa kế' : `Loại: ${c.case_type}`);
    bar.append(typeBadge);
    if (s.locked) bar.append(h('span', 'cd-badge cd-badge-lock', 'Đã khóa'));
    if (s.stale) {
      bar.append(h('span', 'cd-badge cd-badge-warn',
        'Bản nháp cũ — server đã thay đổi'));
    }
    const save = h('span', 'cd-save muted');
    if (s.stageDirty || s.diagramDirty) {
      const n = [];
      if (s.stageDirty) n.push('Stage');
      if (s.diagramDirty) n.push('Sơ đồ');
      save.textContent = `Chưa lưu: ${n.join(' + ')}`;
    } else {
      save.textContent = `Đã lưu · phiên bản ${s.revision}`;
    }
    bar.append(save);
    return bar;
  }

  // ---------- Stage tier ----------

  function personRowEl(p) {
    const wrap = h('div', 'cd-row');
    wrap.dataset.rowId = p.row_id;
    const head = btn('', 'cd-row-head');
    head.setAttribute('aria-expanded', 'false');
    head.onclick = () => {
      const open = wrap.classList.toggle('open');
      head.setAttribute('aria-expanded', String(open));
      if (open) openRowIds.add(p.row_id); else openRowIds.delete(p.row_id);
    };
    const main = h('span', 'cd-row-main', p.ho_ten || '(chưa đặt tên)');
    const meta = h('span', 'cd-row-meta muted',
      [p.ngay_sinh, p.ngay_chet ? `mất ${p.ngay_chet}` : 'còn sống',
       p.so_giay_to].filter(Boolean).join(' · '));
    head.append(main, meta);
    wrap.append(head);
    const errs = model.fieldErrorsFor(p.row_id);
    if (errs.length) {
      wrap.classList.add('cd-row-err');
      const e = h('div', 'cd-row-errors');
      for (const er of errs) e.append(h('div', 'error', er.message));
      wrap.append(e);
    }
    if (!model.canWrite()) {
      // locked/unsupported: chi doc — khong render control ghi
    } else {
      const del = btn('✕', 'cd-del', () => {
        model.removeStageRow(p.row_id);
      });
      del.setAttribute('aria-label', `Xóa dòng ${p.ho_ten || ''}`.trim());
      wrap.append(del);
    }
    // Detail: cac truong chinh edit duoc (field-level, draft only);
    // field_errors map theo row_id + field → hien thi duoi dung input
    // (contract §5.2).
    const det = h('div', 'cd-row-detail');
    const ro = !model.canWrite();
    const field = (label, key, val) => {
      const lab = h('label', 'cd-field');
      lab.append(h('span', 'muted', label));
      const inp = h('input', 'cd-input');
      inp.value = val || '';
      inp.disabled = ro;
      inp.setAttribute('aria-label', `${label} — ${p.ho_ten || 'người'}`);
      inp.onchange = () => model.updatePersonField(
        p.row_id, key, inp.value);
      lab.append(inp);
      for (const fe of errs.filter((e) => e.field === key)) {
        lab.append(h('span', 'cd-field-err error', fe.message));
      }
      return lab;
    };
    det.append(field('Họ tên', 'ho_ten', p.ho_ten));
    det.append(field('Ngày sinh', 'ngay_sinh', p.ngay_sinh));
    det.append(field('Ngày mất', 'ngay_chet', p.ngay_chet));
    det.append(field('Số giấy tờ', 'so_giay_to', p.so_giay_to));
    det.append(field('Địa chỉ', 'dia_chi', p.dia_chi));
    wrap.append(det);
    return wrap;
  }

  function assetRowEl(a) {
    const wrap = h('div', 'cd-row');
    wrap.dataset.rowId = a.row_id;
    const head = btn('', 'cd-row-head');
    head.setAttribute('aria-expanded', 'false');
    head.onclick = () => {
      const open = wrap.classList.toggle('open');
      head.setAttribute('aria-expanded', String(open));
      if (open) openRowIds.add(a.row_id); else openRowIds.delete(a.row_id);
    };
    const main = h('span', 'cd-row-main',
      (a.is_primary ? '★ ' : '') + (a.so_serial || '(chưa có serial)'));
    const meta = h('span', 'cd-row-meta muted',
      [a.dia_chi, a.so_thua_dat ? `thửa ${a.so_thua_dat}` : null]
        .filter(Boolean).join(' · '));
    head.append(main, meta);
    wrap.append(head);
    const errs = model.fieldErrorsFor(a.row_id);
    if (errs.length) {
      wrap.classList.add('cd-row-err');
      const e = h('div', 'cd-row-errors');
      for (const er of errs) e.append(h('div', 'error', er.message));
      wrap.append(e);
    }
    if (model.canWrite()) {
      const del = btn('✕', 'cd-del', () => {
        model.removeStageRow(a.row_id);
      });
      del.setAttribute('aria-label',
        `Xóa tài sản ${a.so_serial || ''}`.trim());
      wrap.append(del);
    }
    const det = h('div', 'cd-row-detail');
    const ro = !model.canWrite();
    const field = (label, key, val) => {
      const lab = h('label', 'cd-field');
      lab.append(h('span', 'muted', label));
      const inp = h('input', 'cd-input');
      inp.value = val || '';
      inp.disabled = ro;
      inp.setAttribute('aria-label',
        `${label} — ${a.so_serial || 'tài sản'}`);
      inp.onchange = () => model.updateAssetField(
        a.row_id, key, inp.value);
      lab.append(inp);
      for (const fe of errs.filter((e) => e.field === key)) {
        lab.append(h('span', 'cd-field-err error', fe.message));
      }
      return lab;
    };
    det.append(field('Số serial', 'so_serial', a.so_serial));
    det.append(field('Địa chỉ', 'dia_chi', a.dia_chi));
    det.append(field('Thửa đất', 'so_thua_dat', a.so_thua_dat));
    det.append(field('Tờ bản đồ', 'so_to_ban_do', a.so_to_ban_do));
    const prim = h('label', 'cd-field cd-field-check');
    const cb = h('input');
    cb.type = 'checkbox';
    cb.checked = !!a.is_primary;
    cb.disabled = ro;
    cb.setAttribute('aria-label', 'Tài sản chính');
    cb.onchange = () => model.updateAssetField(
      a.row_id, 'is_primary', cb.checked);
    prim.append(cb, h('span', '', 'Tài sản chính'));
    det.append(prim);
    wrap.append(det);
    return wrap;
  }

  function stageTierEl() {
    const s = model.state;
    const tier = h('div', 'cd-stage');

    // Card Tài sản (~36%)
    const ac = h('div', 'cd-card cd-assets');
    const aHead = h('div', 'cd-card-head');
    aHead.append(h('h3', 'cd-card-title', 'Tài sản'));
    const aTools = h('div', 'cd-card-tools');
    const intakeAsset = btn('Nhập dữ liệu', '', () => openIntakeDialog(null));
    const addA = btn('+ Tài sản', '', () => model.addAsset());
    intakeAsset.disabled = !model.canWrite();
    addA.disabled = !model.canWrite();
    aTools.append(intakeAsset, addA);
    aHead.append(aTools);
    ac.append(aHead);
    const aBody = h('div', 'cd-card-body');
    if (!s.stage.assets.length) {
      const e = face(L.faceEmpty('Chưa có tài sản.'));
      const b = btn('+ Thêm tài sản đầu tiên', '', () => model.addAsset());
      b.disabled = !model.canWrite();
      e.append(b);
      aBody.append(e);
    } else {
      for (const a of s.stage.assets) aBody.append(assetRowEl(a));
    }
    ac.append(aBody);
    tier.append(ac);

    // Card Người (~64%)
    const pc = h('div', 'cd-card cd-people');
    const pHead = h('div', 'cd-card-head');
    pHead.append(h('h3', 'cd-card-title', 'Người'));
    const pTools = h('div', 'cd-card-tools');
    const intakeExcel = btn('Nhập Excel', '', () => openIntakeDialog('xlsx'));
    const intakeOcr = btn('OCR giấy tờ', '', () => openIntakeDialog('image'));
    const addP = btn('+ Người', '', () => model.addPerson());
    intakeExcel.disabled = !model.canWrite();
    intakeOcr.disabled = !model.canWrite();
    addP.disabled = !model.canWrite();
    const commit = btn('Cập nhật', 'primary', async () => {
      const r = await model.commitStage();
      if (!r.ok && r.error && r.error.code !== 'stage_validation_error' &&
          r.error.code !== 'workspace_conflict') {
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    });
    if (s.stageDirty) {
      commit.append(h('span', 'cd-dirty-dot', ''));
      commit.setAttribute('aria-label', 'Cập nhật — có thay đổi chưa lưu');
    }
    commit.disabled = !model.canWrite() || !s.stageDirty ||
      s.busy === 'notary.workspace_commit_stage';
    pTools.append(intakeExcel, intakeOcr, addP, commit);
    pHead.append(pTools);
    pc.append(pHead);
    const pBody = h('div', 'cd-card-body');
    if (!s.stage.people.length) {
      const e = face(L.faceEmpty('Chưa có người nào trong Stage.'));
      const b = btn('+ Thêm người đầu tiên', '', () => model.addPerson());
      b.disabled = !model.canWrite();
      e.append(b);
      pBody.append(e);
    } else {
      for (const p of s.stage.people) pBody.append(personRowEl(p));
    }
    pc.append(pBody);
    tier.append(pc);

    // Suggestion tray (intake results cho review — khong tu vao Stage)
    if (s.suggestions.length || s.intakeErrors.length) {
      tier.append(suggestionTrayEl());
    }
    if (s.busy) {
      tier.append(h('div', 'cd-busy muted', 'Đang xử lý…'));
    }
    return tier;
  }

  function suggestionTrayEl() {
    const s = model.state;
    const tray = h('div', 'cd-suggest');
    tray.append(h('div', 'cd-suggest-title',
      'Gợi ý chờ kiểm tra — chưa ghi vào hồ sơ'));
    for (const er of s.intakeErrors || []) {
      tray.append(h('div', 'error', er.message || er.code));
    }
    for (const sug of s.suggestions) {
      const card = h('div', 'cd-suggest-card');
      const head = h('div', 'cd-suggest-head');
      head.append(h('span', 'cd-badge',
        sug.target === 'asset' ? 'Tài sản' : 'Người'));
      const fieldBits = [];
      for (const [k, f] of Object.entries(sug.fields || {})) {
        const v = f && (f.normalized_value != null
          ? f.normalized_value : f.raw_value);
        const st = f && f.observation_state;
        fieldBits.push(`${k}: ${v == null ? '—' : v}` +
          (st ? ` (${OBS_STATE_LABEL[st] || st})` : ''));
      }
      head.append(h('span', 'cd-suggest-text', fieldBits.join(' · ')));
      card.append(head);
      const actions = h('div', 'cd-toolbar');
      const put = btn('Đưa vào Stage', 'primary', () => {
        model.acceptSuggestion(sug.suggestion_id);
      });
      put.disabled = !model.canWrite();
      const drop = btn('Bỏ qua', '', () =>
        model.discardSuggestion(sug.suggestion_id));
      actions.append(put, drop);
      card.append(actions);
      for (const w of sug.warnings || []) {
        card.append(h('div', 'muted warn-text', w.message || w.code));
      }
      tray.append(card);
    }
    return tray;
  }

  // ---------- Relation tier: Pool + Diagram (MIN-112 — tach file) ----------
  // Pane duy nhat cho ca phien: giu debounce timer + trang thai Xem cach
  // tinh/loc pool qua cac lan rebuild (rerender tao subtree moi nhung pane
  // instance giu nguyen state nay).

  function relationTierEl() {
    return diagramPane ? diagramPane.build()
      : face(L.faceUnavailable('Sơ đồ', 'module_missing',
        'relationship-diagram.js chua nap.'));
  }

  // ---------- intake / word dialogs (MIN-112 — tach file) ----------

  function openIntakeDialog(presetKind) {
    if (intakeDlg) intakeDlg.open(presetKind);
    else notify('intake-dialog.js chua nap.', true);
  }

  function openWordDialog() {
    if (wordDlg) wordDlg.open();
    else notify('word-export-dialog.js chua nap.', true);
  }

  // ---------- conflict dialog ----------

  function conflictDialog() {
    const s = model.state;
    openModal((box, close) => {
      box.append(h('div', 'cd-modal-title', 'Hồ sơ đã thay đổi trên máy chủ'));
      box.append(h('div', 'muted',
        `Phiên bản hiện tại: ${s.conflict.server_revision ?? '—'} — ` +
        'bản bạn đang sửa dựa trên phiên bản cũ hơn.'));
      const row = h('div', 'cd-toolbar');
      const reload = btn('Tải bản mới', 'primary', async () => {
        await model.resolveConflict('reload');
        close();
      });
      const keep = btn('Giữ bản nháp để sao chép', '', () => {
        model.resolveConflict('keep');
        close();
      });
      row.append(reload, keep);
      box.append(row);
      box.append(h('div', 'muted',
        'Không có ghi đè cưỡng bức — bản nháp chỉ để bạn sao chép tay.'));
    });
  }

  // ---------- workspace root ----------

  const openRowIds = new Set();   // row_id cac dong Stage dang mo (detail)

  function workspaceEl(onBack) {
    const s = model.state;
    const root = h('div', 'cd-workspace');
    if (s.backendMode === 'mock') {
      root.append(h('div', 'cd-mock-banner', model.mockBanner()));
    }
    root.append(contextBar(onBack));
    if (s.unsupported) {
      root.append(h('div', 'cd-warn-banner',
        `Loại việc “${s.caseInfo && s.caseInfo.case_type}” — Chưa hỗ trợ. ` +
        'Chỉ đọc dữ liệu hiện có.'));
    }
    if (s.locked) {
      root.append(h('div', 'cd-warn-banner',
        'Hồ sơ đã khóa — toàn bộ chỉ đọc, vẫn xem/sao chép được.'));
    }
    if (s.notice) {
      const n = h('div', 'cd-notice', s.notice);
      const x = btn('×', '', () => model.dismissNotice());
      n.append(x);
      root.append(n);
    }
    if (s.error && s.status !== 'error' && s.status !== 'unavailable') {
      const eb = h('div', 'cd-error-banner error',
        `${s.error.code}: ${s.error.message}`);
      const x = btn('×', '', () => model.dismissNotice());
      eb.append(x);
      root.append(eb);
    }
    root.append(stageTierEl());
    root.append(relationTierEl());
    return root;
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
    // Mo case khac se thay toan bo draft — hoi truoc khi mat nhap.
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
    model.openCase(id);
  };

  panels.overview.append(buildCaseListPanel(openCaseInDrafting));
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
    // Emit nen (jobUpdate/status poll) trong luc dang go trong row detail:
    // hoan rebuild de input khong mat focus/gia tri — render sau lan emit
    // ke tiep (blur/change hoac action tiep theo cua nguoi dung).
    const ae = document.activeElement;
    if (ae && dp.contains(ae) && ae.closest('.cd-row-detail')) {
      return;
    }
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
      // ready / locked / conflict — conflict van render workspace + dialog
      dp.append(workspaceEl(() => {
        activeTab = 'overview';
        rerender();
      }));
      // Re-apply cac dong dang mo sau full rebuild (row_id on dinh trong
      // phien); prune id khong con trong draft (dong xoa / doi case).
      const present = new Set();
      for (const r of dp.querySelectorAll('.cd-row[data-row-id]')) {
        const rid = r.dataset.rowId;
        present.add(rid);
        if (openRowIds.has(rid)) {
          r.classList.add('open');
          const hd = r.querySelector('.cd-row-head');
          if (hd) hd.setAttribute('aria-expanded', 'true');
        }
      }
      for (const rid of [...openRowIds]) {
        if (!present.has(rid)) openRowIds.delete(rid);
      }
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

const G1_NOTARY_VIEW = { createNotaryModuleView, isDevMode };

if (typeof window !== 'undefined') window.G1_NOTARY_VIEW = G1_NOTARY_VIEW;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_VIEW;
}
