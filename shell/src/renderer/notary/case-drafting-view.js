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
    const close = () => wrap.remove();
    wrap.onclick = (e) => { if (e.target === wrap) close(); };
    build(box, close);
    wrap.append(box);
    document.body.append(wrap);
    const first = box.querySelector('button, input, textarea, select');
    if (first) first.focus();
    return close;
  }

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
    const s = model.state;
    const wrap = h('div', 'cd-row');
    const head = btn('', 'cd-row-head', () => {
      wrap.classList.toggle('open');
    });
    head.setAttribute('aria-expanded', 'false');
    head.onclick = () => {
      const open = wrap.classList.toggle('open');
      head.setAttribute('aria-expanded', String(open));
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
    // Detail: cac truong chinh edit duoc (field-level, draft only)
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
    const s = model.state;
    const wrap = h('div', 'cd-row');
    const head = btn('', 'cd-row-head', () => {});
    head.setAttribute('aria-expanded', 'false');
    head.onclick = () => {
      const open = wrap.classList.toggle('open');
      head.setAttribute('aria-expanded', String(open));
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

  // ---------- Relation tier: Pool + Diagram ----------

  function poolCardEl(row, kind) {
    const card = h('div', 'cd-pool-card');
    card.draggable = model.canWrite();
    const label = kind === 'person'
      ? (row.ho_ten || '(chưa đặt tên)')
      : (row.so_serial || '(chưa có serial)');
    card.append(h('span', 'cd-pool-label', label));
    card.append(h('span', 'cd-badge', kind === 'person' ? 'Người' : 'Tài sản'));
    // Keo tha (tien ich) — cung ket qua voi menu "Gán vị trí".
    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain',
        JSON.stringify({ kind, row_id: row.row_id }));
    });
    const assign = btn('Gán vị trí…', '', () =>
      openAssignMenu(row, kind));
    assign.disabled = !model.canWrite() || !model.state.capabilities.diagram;
    card.append(assign);
    return card;
  }

  // Menu "Gán vị trí" — cach thay the ban phim cho keo tha (spec §4).
  function openAssignMenu(row, kind) {
    const s = model.state;
    openModal((box, close) => {
      box.append(h('div', 'cd-modal-title', 'Gán vị trí trên sơ đồ'));
      if (kind === 'asset') {
        // Wire v1: tai san khong gan vao node — chi xem (§7.1).
        box.append(h('div', 'muted',
          'Tài sản chưa gán trực tiếp lên sơ đồ trong phiên bản này — ' +
          'sơ đồ gán quan hệ giữa các người.'));
        const ok = btn('Đóng', 'primary', close);
        box.append(ok);
        return;
      }
      const nodes = (s.diagram.nodes || []).filter(
        (n) => !n.deleted);
      const empty = nodes.filter((n) => !n.personId);
      if (empty.length) {
        box.append(h('div', 'muted', 'Slot đang trống:'));
        for (const n of empty) {
          const b = btn(`Gán vào “${n.id}”`, 'cd-menu-item', () => {
            model.assignPerson(n.id, row.row_id);
            close();
          });
          box.append(b);
        }
      }
      box.append(h('div', 'muted', 'Hoặc tạo slot mới:'));
      const occupied = nodes.filter((n) => n.personId);
      for (const n of occupied) {
        const who = personName(n.personId);
        const child = btn(`Con của ${who}`, 'cd-menu-item', () => {
          const node = model.addSlot();
          model.setNodeRelation(node.id, { parentSlotIds: [n.id] });
          model.assignPerson(node.id, row.row_id);
          close();
        });
        const spouse = btn(`Vợ/chồng của ${who}`, 'cd-menu-item', () => {
          const node = model.addSlot();
          model.setNodeRelation(node.id, { spouseSlotId: n.id });
          model.assignPerson(node.id, row.row_id);
          close();
        });
        box.append(child, spouse);
      }
      if (!nodes.length) {
        const b = btn('Tạo slot đầu tiên và gán', 'cd-menu-item', () => {
          const node = model.addSlot('owner');
          model.assignPerson(node.id, row.row_id);
          close();
        });
        box.append(b);
      }
      const cancel = btn('Đóng', '', close);
      box.append(cancel);
    });
  }

  function personName(rowId) {
    const p = model.state.committed.people
      .find((x) => x.row_id === rowId);
    return p ? (p.ho_ten || '(không tên)') : '—';
  }

  function diagramNodeEl(n) {
    const s = model.state;
    const card = h('div', 'cd-node');
    if (n.deleted) card.classList.add('cd-node-deleted');
    const head = h('div', 'cd-node-head');
    head.append(h('span', 'cd-node-id muted', n.id));
    head.append(h('span', 'cd-node-name',
      n.personId ? personName(n.personId) : '(trống)'));
    card.append(head);
    // Drop target: nhan pool card keo vao (cung ket qua menu Gan vi tri)
    card.addEventListener('dragover', (e) => e.preventDefault());
    card.addEventListener('drop', (e) => {
      e.preventDefault();
      try {
        const d = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (d.kind === 'person') model.assignPerson(n.id, d.row_id);
      } catch (err) { /* payload rac — bo qua */ }
    });
    if (n.deleted) return card;
    const flags = h('div', 'cd-node-flags');
    const ro = !model.canWrite();
    const land = btn(n.isLandOwner ? '★ Chủ đất' : 'Chủ đất',
      n.isLandOwner ? 'primary' : '', () =>
        model.setNodeFlag(n.id, 'isLandOwner', !n.isLandOwner));
    land.disabled = ro;
    land.setAttribute('aria-pressed', String(!!n.isLandOwner));
    const recv = btn(n.willReceive ? '✓ Nhận' : 'Nhận',
      n.willReceive ? 'primary' : '', () =>
        model.setNodeFlag(n.id, 'willReceive', !n.willReceive));
    recv.disabled = ro;
    recv.setAttribute('aria-pressed', String(!!n.willReceive));
    flags.append(land, recv);
    if (n.personId) {
      const un = btn('Bỏ gán', '', () => model.assignPerson(n.id, null));
      un.disabled = ro;
      flags.append(un);
    }
    const del = btn('✕', 'cd-del', () => model.removeNode(n.id));
    del.disabled = ro;
    del.setAttribute('aria-label', `Xóa slot ${n.id}`);
    flags.append(del);
    card.append(flags);
    return card;
  }

  // "Xem cách tính" — chi DOC output engine, render dang doc duoc,
  // khong render JSON tho, khong tu tinh ty le (contract §10 consumer).
  function calcPanelEl() {
    const rm = model.state.renderModel;
    const box = h('div', 'cd-calc');
    if (!rm) {
      box.append(face(L.faceEmpty(
        'Chưa có kết quả tính — bấm “Đánh giá thử” hoặc lưu sơ đồ.')));
      return box;
    }
    const statusLabel = {
      complete: 'Hoàn chỉnh', incomplete: 'Chưa đủ điều kiện',
      invalid: 'Không hợp lệ', unsupported: 'Chưa hỗ trợ',
    }[rm.status] || rm.status;
    box.append(h('div', 'cd-calc-status',
      `Trạng thái tính: ${statusLabel}`));
    if (rm.status === 'unsupported') {
      box.append(h('div', 'cd-badge cd-badge-warn',
        'Chưa hỗ trợ — đây không phải kết quả đã tính'));
    }
    const allocs = rm.allocations || {};
    const ids = Object.keys(allocs);
    if (ids.length) {
      const list = h('div', 'cd-alloc-list');
      for (const pid of ids) {
        const a = allocs[pid];
        const row = h('div', 'cd-alloc-row');
        row.append(h('span', 'cd-alloc-name', personName(pid)));
        row.append(h('span', 'cd-badge',
          `${a.displayPercent || '0.00'}%`));
        row.append(h('span', 'muted',
          `phần cuối ${a.finalShare ?? '—'}`));
        list.append(row);
      }
      box.append(list);
    }
    for (const w of rm.warnings || []) {
      box.append(h('div', 'muted warn-text', w.message || w.code));
    }
    for (const e of rm.errors || []) {
      box.append(h('div', 'error', e.message || e.code));
    }
    for (const u of rm.unresolvedEstates || []) {
      box.append(h('div', 'muted',
        `Phần chưa phân (${personName(u.sourcePersonId)}): ` +
        `${u.fraction} — ${u.reason === 'no_valid_heir'
          ? 'không có người thừa kế hợp lệ' : u.reason}`));
    }
    return box;
  }

  function relationTierEl() {
    const s = model.state;
    const tier = h('div', 'cd-rel');

    // Pool (~22%)
    const pc = h('div', 'cd-card cd-pool');
    const pHead = h('div', 'cd-card-head');
    pHead.append(h('h3', 'cd-card-title', 'Pool'));
    pc.append(pHead);
    const pBody = h('div', 'cd-card-body');
    const pool = model.pool();
    if (!pool.people.length && !pool.assets.length) {
      pBody.append(face(L.faceEmpty(
        'Pool trống — mọi người đã được gán hoặc Stage chưa có dữ liệu.')));
    } else {
      for (const p of pool.people) pBody.append(poolCardEl(p, 'person'));
      for (const a of pool.assets) pBody.append(poolCardEl(a, 'asset'));
    }
    pc.append(pBody);
    tier.append(pc);

    // Diagram (~78%)
    const dc = h('div', 'cd-card cd-diagram');
    const dHead = h('div', 'cd-card-head');
    dHead.append(h('h3', 'cd-card-title', 'Sơ đồ quan hệ'));
    const tools = h('div', 'cd-toolbar cd-card-tools');
    const save = btn('Lưu sơ đồ', 'primary', async () => {
      const r = await model.saveDiagram();
      if (!r.ok && r.error && r.error.code !== 'workspace_conflict' &&
          r.error.code !== 'diagram_invalid_state') {
        notify(`${r.error.code}: ${r.error.message}`, true);
      }
    });
    if (s.diagramDirty) save.append(h('span', 'cd-dirty-dot', ''));
    save.disabled = !model.canWrite() || !s.diagramDirty ||
      !s.capabilities.diagram;
    const calc = btn('Xem cách tính', '', async () => {
      calcOpen = !calcOpen;
      if (calcOpen) await model.evaluateDiagram();
      rerender();
    });
    const evalBtn = btn('Đánh giá thử', '', async () => {
      const r = await model.evaluateDiagram();
      if (!r.ok && r.error) notify(
        `${r.error.code}: ${r.error.message}`, true);
      calcOpen = true;
    });
    evalBtn.disabled = !s.capabilities.diagram ||
      s.busy === 'notary.diagram_evaluate';
    const word = btn('Xuất Word', '', openWordDialog);
    word.disabled = !s.capabilities.word_export || s.wordBusy;
    const addSlotBtn = btn('+ Slot', '', () => model.addSlot());
    addSlotBtn.disabled = !model.canWrite() || !s.capabilities.diagram;
    tools.append(save, calc, evalBtn, word, addSlotBtn);
    dHead.append(tools);
    dc.append(dHead);
    const dBody = h('div', 'cd-diagram-body');
    const nodes = (s.diagram.nodes || []).filter((n) => !n.deleted);
    if (!nodes.length) {
      dBody.append(face(L.faceEmpty(
        'Sơ đồ chưa có slot — thêm slot hoặc gán người từ Pool.')));
    } else {
      const grid = h('div', 'cd-nodes');
      for (const n of s.diagram.nodes || []) {
        grid.append(diagramNodeEl(n));
      }
      dBody.append(grid);
    }
    for (const w of s.diagramWarnings || []) {
      dBody.append(h('div', 'muted warn-text', w.message || w.code));
    }
    for (const e of s.diagramErrors || []) {
      dBody.append(h('div', 'error', e.message || e.code));
    }
    if (calcOpen) dBody.append(calcPanelEl());
    dc.append(dBody);
    tier.append(dc);
    return tier;
  }

  // ---------- intake dialog (khung toi thieu — MIN-112 lam sau) ----------

  function openIntakeDialog(presetKind) {
    const picked = [];
    openModal((box, close) => {
      box.append(h('div', 'cd-modal-title', 'Nhập dữ liệu → gợi ý'));
      box.append(h('div', 'muted',
        'Mọi kết quả là gợi ý chờ kiểm tra — không tự ghi vào hồ sơ.'));
      const pick = btn('Chọn file…', '', async () => {
        const filters = presetKind === 'xlsx'
          ? [{ name: 'Excel', extensions: ['xlsx'] }]
          : presetKind === 'image'
            ? [{ name: 'Giấy tờ', extensions: ['jpg', 'jpeg', 'png', 'pdf'] }]
            : [{ name: 'Tài liệu',
                 extensions: ['jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx'] }];
        const r = await pickFiles({ multi: true, filters });
        if (!r.ok) { notify(`${r.error.code}: ${r.error.message}`, true); return; }
        for (const f of r.data.files || []) picked.push(f);
        list.innerHTML = '';
        for (const f of picked) list.append(h('div', 'file-row', f.path));
      });
      const ta = h('textarea', 'cd-input cd-textarea');
      ta.setAttribute('aria-label', 'Dán văn bản để phân tích');
      ta.placeholder = 'Hoặc dán văn bản…';
      const list = h('div', 'files');
      const go = btn('Phân tích', 'primary', async () => {
        const sources = [];
        for (const f of picked) {
          const ext = (f.path.split('.').pop() || '').toLowerCase();
          const kind = { jpg: 'image', jpeg: 'image', png: 'image',
                         pdf: 'pdf', docx: 'docx', xlsx: 'xlsx' }[ext];
          if (!kind) continue;
          sources.push({ source_id: crypto.randomUUID(), kind,
                         file_ref: { path: f.path, scope: 'machine_local',
                                     size_bytes: f.size_bytes ?? 0 } });
        }
        const text = ta.value.trim();
        if (text) {
          sources.push({ source_id: crypto.randomUUID(), kind: 'text',
                         text });
        }
        if (!sources.length) {
          notify('Chưa có nguồn nào — chọn file hoặc dán văn bản.', true);
          return;
        }
        const r = await model.intakeAnalyze(sources);
        if (!r.ok) notify(`${r.error.code}: ${r.error.message}`, true);
        close();
      });
      go.disabled = !model.canWrite();
      const cancel = btn('Đóng', '', close);
      const row = h('div', 'cd-toolbar');
      row.append(pick, go, cancel);
      box.append(row, ta, list);
    });
  }

  // ---------- word export dialog ----------

  function openWordDialog() {
    openModal(async (box, close) => {
      box.append(h('div', 'cd-modal-title', 'Xuất Word — nhiều văn bản'));
      const body = h('div', 'cd-slot');
      box.append(body);
      body.append(face(L.faceLoading('Đang tải danh sách văn bản…')));
      const r = await model.loadWordOptions();
      body.innerHTML = '';
      if (!r.ok) {
        body.append(face(L.faceError(r.error)));
        box.append(btn('Đóng', '', close));
        return;
      }
      const checks = [];
      for (const d of model.state.wordOptions || []) {
        const lab = h('label', 'cd-check-row');
        const cb = h('input');
        cb.type = 'checkbox';
        cb.disabled = !d.ready;
        cb.setAttribute('aria-label', d.display_name);
        lab.append(cb, h('span', '', d.display_name));
        if (!d.ready) {
          lab.append(h('span', 'muted',
            ` — ${BLOCK_REASON_LABEL[d.block_reason] ||
              'chưa sẵn sàng'}`));
        }
        box.append(lab);
        checks.push({ key: d.document_key, cb });
      }
      const destLabel = h('span', 'muted', 'Chưa chọn thư mục');
      let dest = null;
      const pickDir = btn('Chọn thư mục…', '', async () => {
        const r2 = await pickFiles({ directory: true });
        if (!r2.ok) { notify(`${r2.error.code}: ${r2.error.message}`, true); return; }
        if (!r2.data.files.length) return;
        dest = r2.data.files[0];
        destLabel.textContent = dest.path;
      });
      const out = h('div', 'cd-slot');
      const go = btn('Xuất', 'primary', async () => {
        const keys = checks.filter((c) => c.cb.checked).map((c) => c.key);
        if (!keys.length) {
          notify('Chưa chọn văn bản nào.', true);
          return;
        }
        if (!dest) {
          notify('Chưa chọn thư mục đích.', true);
          return;
        }
        go.disabled = true;
        const rr = await model.exportWord(keys, {
          path: dest.path, scope: 'machine_local', is_dir: true });
        go.disabled = false;
        out.innerHTML = '';
        const res = model.state.wordResult;
        if (res && res.documents) {
          for (const d of res.documents) {
            const row = h('div', 'cd-word-row');
            if (d.status === 'saved') {
              row.append(h('span', 'cd-badge cd-badge-ok', 'Đã lưu'));
              row.append(h('span', '', d.actual_filename || ''));
              const op = btn('Mở', '', () =>
                openPath(d.output_file && d.output_file.path));
              row.append(op);
            } else if (d.status === 'skipped') {
              row.append(h('span', 'cd-badge', 'Bỏ qua'));
              row.append(h('span', 'muted', d.display_name));
            } else {
              row.append(h('span', 'cd-badge cd-badge-err', 'Lỗi'));
              row.append(h('span', '', d.display_name));
              row.append(h('span', 'error',
                (d.error && (BLOCK_REASON_LABEL[d.error.code] ||
                             d.error.message)) || ''));
            }
            out.append(row);
          }
        } else if (!rr.ok) {
          out.append(face(L.faceError(rr.error)));
        }
        // Khong tu dong popup khi con loi (spec §7) — nguoi dung dong.
      });
      const row = h('div', 'cd-toolbar');
      row.append(pickDir, go, btn('Đóng', '', close));
      box.append(row, destLabel, out);
    });
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

  let calcOpen = false;

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

  const openCaseInDrafting = (id) => {
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
      const retry = btn('Thử lại', '', () => model.openCase(s.caseId));
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
