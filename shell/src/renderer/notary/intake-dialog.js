'use strict';

/* Intake dialog (MIN-112) — "Nhập dữ liệu → gợi ý".
 *
 * SOT hanh vi: spec UX §4 + contracts/notary-case-drafting.md §5.
 * - Nguon: native picker (filters ảnh/PDF/DOCX/XLSX), drop-zone qua
 *   desktop.v1.registerDroppedFile (webUtils — khong lo path vao renderer),
 *   dan van ban (kind:'text').
 * - File gui len wire chi la {file_token} — main resolve thanh FileRef.
 * - Ket qua la SUGGESTION cho review ("Đưa vào Stage" chi tao draft row);
 *   dong dialog giu nguyen tray trong workspace (state.suggestions).
 * - Cung mot component cho mock va real — khac nhau chi o client seam.
 *
 * Export UMD: window.G1_NOTARY_INTAKE + module.exports. DOM chi trong
 * createIntakeDialog(...).open() (file load duoc trong node --test).
 */

const INTAKE_EXT_KIND = {
  jpg: 'image', jpeg: 'image', png: 'image',
  pdf: 'pdf', docx: 'docx', xlsx: 'xlsx',
};
const INTAKE_KIND_LABEL = {
  image: 'ảnh', pdf: 'PDF', docx: 'Word', xlsx: 'Excel', text: 'văn bản',
};
const OBS_STATE_LABEL = {
  observed: 'đọc được', normalized: 'đã chuẩn hóa', inferred: 'suy luận',
};
const INTAKE_FILTERS = [
  { name: 'Tài liệu/Giấy tờ',
    extensions: ['jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx'] },
];
const INTAKE_FIELD_LABEL = {
  ho_ten: 'Họ tên', so_giay_to: 'Số giấy tờ', ngay_sinh: 'Ngày sinh', ngay_chet: 'Ngày chết',
  ngay_cap: 'Ngày cấp', noi_cap: 'Nơi cấp', dia_chi: 'Địa chỉ', so_serial: 'Serial giấy chứng nhận',
  so_vao_so: 'Số vào sổ', so_thua_dat: 'Số thửa đất', so_to_ban_do: 'Số tờ bản đồ',
  dien_tich: 'Diện tích', co_quan_cap: 'Cơ quan cấp', land_rows: 'Cụm đất',
};

// Same numeric rule as Intake normalization: 1.234,5 → 1234.5.
function reviewedArea(raw) {
  let text = String(raw || '').trim();
  if (text.includes(',') && text.includes('.')) text = text.replace(/\./g, '').replace(/,/g, '.');
  else if (text.includes(',')) text = text.replace(/,/g, '.');
  return /^\d+(\.\d+)?$/.test(text) && Number.isFinite(Number(text)) ? Number(text) : null;
}

function createIntakeDialog(ctx) {
  const model = ctx.model;
  const L = ctx.lib;
  const notify = ctx.notify || (() => {});
  const h = ctx.h;
  const btn = ctx.btn;
  const face = ctx.face;
  const openModal = ctx.openModal;
  const pickFiles = ctx.pickFiles || (async () => ({ ok: false }));
  // registerDroppedFile co the thieu tren shell cu — fallback picker.
  const registerDroppedFile = ctx.registerDroppedFile || null;
  const cancelJob = ctx.cancelJob || (async () => ({ ok: false }));

  function open(presetKind) {
    // item: {source_id, kind, label, token?, text?, status, error}
    // status: 'chờ' | 'đang phân tích' | 'xong' | 'lỗi' | 'bỏ qua'
    const items = [];
    let busy = false;
    let jobId = null;
    let lastResult = null;   // {suggestions, errors} cua lan chay gan nhat
    const list = h('div', 'cd-intake-list');

    function renderList() {
      list.innerHTML = '';
      for (const it of items) list.append(srcRowEl(it));
    }

    const filters = presetKind === 'xlsx'
      ? [{ name: 'Excel', extensions: ['xlsx'] }]
      : presetKind === 'image'
        ? [{ name: 'Giấy tờ',
            extensions: ['jpg', 'jpeg', 'png', 'pdf'] }]
        : INTAKE_FILTERS;

    function kindOfName(name) {
      const ext = String(name || '').split('.').pop().toLowerCase();
      return INTAKE_EXT_KIND[ext] || null;
    }

    function addEntry(entry) {
      // entry tu picker/registerDroppedFile: {file_token, name, ...}
      const kind = kindOfName(entry.name);
      if (!kind || entry.is_dir) {
        items.push({
          source_id: crypto.randomUUID(), kind: null,
          label: entry.name || '(file)', status: 'lỗi',
          error: entry.is_dir
            ? 'Thư mục không phải nguồn intake'
            : 'Định dạng chưa hỗ trợ (ảnh/PDF/DOCX/XLSX)',
        });
        return;
      }
      items.push({
        source_id: crypto.randomUUID(), kind,
        label: entry.name || '(file)', token: entry.file_token,
        sizeBytes: entry.size_bytes ?? null,
        status: 'chờ', error: null,
      });
    }

    function srcRowEl(it) {
      const row = h('div', 'cd-intake-row');
      row.append(h('span', 'cd-kind pill',
        INTAKE_KIND_LABEL[it.kind] || it.kind || '—'));
      row.append(h('span', 'grow', it.label));
      row.append(h('span', 'muted', it.status));
      if (it.error) row.append(h('span', 'error', it.error));
      if (!busy && it.status !== 'đang phân tích') {
        const x = btn('✕', 'cd-del', () => {
          items.splice(items.indexOf(it), 1);
          renderList();
        });
        x.setAttribute('aria-label', `Bỏ nguồn ${it.label}`);
        row.append(x);
      }
      return row;
    }

    // Review card cho suggestion moi — cung "Đưa vào Stage/Bỏ qua" nhu
    // tray ngoai workspace; tray giu lai khi dong dialog.
    function reviewCardEl(sug) {
      const card = h('div', 'cd-suggest-card');
      const head = h('div', 'cd-suggest-head');
      head.append(h('span', 'cd-badge',
        sug.target === 'asset' ? 'Tài sản' : 'Người'));
      const bits = [];
      for (const [k, f] of Object.entries(sug.fields || {})) {
        const v = f && (f.normalized_value != null
          ? f.normalized_value : f.raw_value);
        const st = f && f.observation_state;
        bits.push(`${INTAKE_FIELD_LABEL[k] || k}: ${k === 'land_rows' ? 'xem từng dòng bên dưới' : v == null ? '—' : v}` +
          (st ? ` (${OBS_STATE_LABEL[st] || st})` : ''));
      }
      head.append(h('span', 'cd-suggest-text', bits.join(' · ')));
      card.append(head);
      for (const [key, field] of Object.entries(sug.fields || {})) {
        if (key === 'land_rows') {
          const rowsBox = h('div', 'cd-slot');
          let rows = [];
          try { rows = JSON.parse(field.normalized_value || '[]'); } catch (_) { /* malformed stays editable */ }
          if (!Array.isArray(rows)) rows = [];
          let identity = field.land_identity || rows.map((_, n) => n + 1);
          const update = (cell) => model.reviewSuggestion(sug.suggestion_id, key, JSON.stringify(rows), { identity, cell });
          function renderRows() {
            rowsBox.innerHTML = '';
            rowsBox.append(h('div', 'muted', 'Cụm đất: mỗi dòng giữ riêng loại đất, diện tích và thời hạn.'));
            for (const row of rows) {
              const rowEl = h('div', 'cd-check-row');
              for (const [name, label] of [['loai_dat', 'Loại đất'], ['dien_tich', 'Diện tích'], ['thoi_han', 'Thời hạn']]) {
                const input = h('input'); input.type = name === 'dien_tich' ? 'number' : 'text';
                input.value = row[name] == null ? '' : String(row[name]);
                input.setAttribute('aria-label', label); input.placeholder = label;
                if (name === 'dien_tich') { input.min = '0'; input.step = 'any'; }
                input.onchange = () => { row[name] = input.value === '' ? null : name === 'dien_tich' ? Number(input.value) : input.value; update(`${identity[rows.indexOf(row)]}:${name}`); };
                rowEl.append(input);
              }
              rowEl.append(btn('Bỏ dòng', 'ghost sm', () => { const n = rows.indexOf(row); rows.splice(n, 1); identity.splice(n, 1); update(); renderRows(); }));
              rowsBox.append(rowEl);
            }
            rowsBox.append(btn('Thêm cụm đất', 'secondary sm', () => {
              if (rows.length >= 20) return;
              rows.push({ loai_dat: null, dien_tich: null, thoi_han: null }); identity.push(null); update(); renderRows();
            }));
          }
          renderRows(); card.append(rowsBox);
          const evidence = h('details'); evidence.append(h('summary', '', 'Xem chữ gốc của từng cụm đất'));
          for (const ref of field.source_refs || []) {
            evidence.append(h('div', 'muted', `Dòng ${ref.land_row || '?'} · ${ref.land_field || ''}: ${ref.raw_snippet || ''}`));
            if (ref.core_state === 'ambiguous') evidence.append(btn('Chọn giá trị này', 'ghost sm', () => {
              const row = rows[identity.indexOf(ref.land_row)];
              if (!row) return;
              row[ref.land_field] = ref.land_field === 'dien_tich' ? reviewedArea(ref.raw_snippet) : ref.raw_snippet;
              if (ref.land_field === 'dien_tich' && row[ref.land_field] == null) {
                notify('Diện tích không hợp lệ; hãy nhập số đã kiểm tra', true); return;
              }
              update(`${ref.land_row}:${ref.land_field}`); renderRows();
            }));
          }
          card.append(evidence);
          continue;
        }
        const label = h('label', 'cd-check-row');
        const input = h('input');
        input.type = 'text';
        input.value = field.review_input != null ? String(field.review_input) : field.normalized_value == null ? '' : String(field.normalized_value);
        input.setAttribute('aria-label', `Kiểm tra ${INTAKE_FIELD_LABEL[key] || key}`);
        input.placeholder = 'Thiếu hoặc chưa chắc — nhập giá trị đã kiểm tra';
        if (key.startsWith('ngay_')) input.placeholder = 'Năm hoặc ngày dạng 2026-10-04';
        const reviewError = h('span', 'error', field.review_error || '');
        const review = () => {
          const valid = model.reviewSuggestion(sug.suggestion_id, key, input.value);
          reviewError.textContent = field.review_error || '';
          input.setAttribute('aria-invalid', valid ? 'false' : 'true');
        };
        input.onchange = review;
        label.append(h('span', '', INTAKE_FIELD_LABEL[key] || key), input, reviewError);
        card.append(label);
        const evidence = h('details');
        evidence.append(h('summary', '', 'Xem chữ gốc và vị trí'));
        for (const ref of field.source_refs || []) {
          evidence.append(h('div', 'muted', `${ref.raw_snippet || field.raw_value || ''} · ` +
            (ref.span ? `chữ ${ref.span[0]}–${ref.span[1]} · ${ref.rule_id || ''}` : 'nguồn nhập')));
          if (ref.kind === 'docx' && key !== 'land_rows') {
            evidence.append(btn('Chọn giá trị này', 'ghost sm', () => {
              input.value = ref.raw_snippet;
              review();
              input.value = field.normalized_value == null ? '' : String(field.normalized_value);
            }));
          }
        }
        card.append(evidence);
      }
      for (const w of sug.warnings || []) {
        card.append(h('div', 'muted warn-text', w.message || w.code));
      }
      const actions = h('div', 'toolbar');
      const put = btn('Đưa vào Stage', 'primary sm', () => {
        const row = model.acceptSuggestion(sug.suggestion_id);
        if (row) card.remove();
        else notify(model.state.notice || 'Gợi ý chưa được đưa vào Stage', true);
      });
      put.disabled = !model.canWrite();
      const drop = btn('Bỏ qua', 'ghost sm', () => {
        model.discardSuggestion(sug.suggestion_id);
        card.remove();
      });
      actions.append(put, drop);
      card.append(actions);
      return card;
    }

    function markResults(data) {
      // Per-source status: ghep source_id → suggestion/error cua lan chay.
      // Loi o nguon nay khong lan sang nguon khac (contract §5.5).
      const suggIds = new Set(
        (data.suggestions || []).map((s) => s.source_id));
      const errBy = {};
      for (const e of data.errors || []) errBy[e.source_id] = e;
      for (const it of items) {
        if (it.status !== 'đang phân tích') continue;
        if (errBy[it.source_id]) {
          it.status = 'lỗi';
          it.error = errBy[it.source_id].message ||
            errBy[it.source_id].code;
        } else if (suggIds.has(it.source_id)) {
          it.status = 'xong';
        } else {
          it.status = 'bỏ qua';
        }
      }
    }

    openModal((box, close) => {
      const head = h('div', 'modal-head');
      head.append(h('h2', 'modal-title',
        'Nhập file — phân tích thành gợi ý'));
      const mx = h('button', 'modal-close', '×');
      mx.type = 'button';
      mx.setAttribute('aria-label', 'Đóng');
      mx.onclick = close;
      head.append(mx);
      box.append(head);
      const body = h('div', 'modal-body');
      body.append(h('div', 'muted',
        'Mọi kết quả là gợi ý chờ kiểm tra — không tự ghi vào hồ sơ.'));

      // Drop-zone: file tha vao di qua registerDroppedFile (main cap token)
      // — khong bao gio doc path trong renderer.
      const drop = h('div', 'cd-dropzone',
        'Kéo thả file vào đây (ảnh, PDF, Word, Excel)');
      drop.setAttribute('role', 'button');
      drop.setAttribute('tabindex', '0');
      const dropErr = h('div', 'cd-slot');
      const onDrop = async (e) => {
        e.preventDefault();
        drop.classList.remove('drop-hint');
        if (!registerDroppedFile) {
          dropErr.innerHTML = '';
          dropErr.append(face(L.faceError({
            code: 'unsupported', message:
              'Kéo thả chưa hỗ trợ trên bản này — dùng “Chọn file…”.' })));
          return;
        }
        for (const f of (e.dataTransfer && e.dataTransfer.files) || []) {
          const r = await registerDroppedFile(f);
          if (r.ok && r.data && r.data.file) addEntry(r.data.file);
          else {
            items.push({
              source_id: crypto.randomUUID(), kind: null,
              label: f && f.name || '(file)', status: 'lỗi',
              error: (r.error && r.error.message) || 'không đọc được file',
            });
          }
        }
        renderList();
      };
      drop.addEventListener('dragover', (e) => {
        e.preventDefault();
        drop.classList.add('drop-hint');
      });
      drop.addEventListener('dragleave', () =>
        drop.classList.remove('drop-hint'));
      drop.addEventListener('drop', onDrop);
      body.append(drop, dropErr);

      const ta = h('textarea', 'cd-textarea');
      ta.setAttribute('aria-label', 'Dán văn bản để phân tích');
      ta.placeholder = 'Hoặc dán văn bản…';
      body.append(ta);

      body.append(list);

      const prog = h('div', 'cd-slot muted');
      const review = h('div', 'cd-slot cd-ireview');
      for (const suggestion of model.state.suggestions || []) review.append(reviewCardEl(suggestion));
      body.append(prog, review);

      const pickBtn = btn('Chọn file…', 'secondary', async () => {
        const r = await pickFiles({ multi: true, filters });
        if (!r.ok) {
          notify(`${r.error.code}: ${r.error.message}`, true);
          return;
        }
        for (const f of r.data.files || []) addEntry(f);
        renderList();
      });
      // Keyboard parity cho drop-zone (moi drag/drop can cach ban phim):
      // Enter/Space tren drop-zone mo picker.
      drop.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          pickBtn.click();
        }
      });

      const cancelBtn = btn('Hủy phân tích', '', async () => {
        if (jobId) await cancelJob(jobId);
      });
      cancelBtn.hidden = true;

      const go = btn('Phân tích', 'primary', async () => {
        const sources = [];
        for (const it of items) {
          if (!it.kind || it.status === 'lỗi') continue;  // bo nguon loi
          it.status = 'đang phân tích';
          it.error = null;
          sources.push(it.kind === 'text'
            ? { source_id: it.source_id, kind: 'text', text: it.text }
            : { source_id: it.source_id, kind: it.kind,
                file_ref: { file_token: it.token } });
        }
        const text = ta.value.trim();
        if (text) {
          const it = {
            source_id: crypto.randomUUID(), kind: 'text',
            label: `Văn bản dán (${text.length} ký tự)`,
            text, status: 'đang phân tích', error: null,
          };
          items.push(it);
          sources.push({ source_id: it.source_id, kind: 'text', text });
          ta.value = '';
        }
        if (!sources.length) {
          notify('Chưa có nguồn nào — chọn file hoặc dán văn bản.', true);
          renderList();
          return;
        }
        busy = true;
        go.disabled = true;
        pickBtn.disabled = true;
        cancelBtn.hidden = false;
        review.innerHTML = '';
        renderList();
        prog.textContent = 'Đang gửi…';
        const r = await model.intakeAnalyze(sources, {
          onJob: (job) => {
            if (job && job.job_id) jobId = job.job_id;
            const p = job && job.progress;
            prog.textContent = p
              ? `Đang phân tích ${p.done ?? 0}/${p.total ?? '?'} — ` +
                (p.current_label || '')
              : 'Đang phân tích…';
          },
        });
        if (r.stale) return;
        busy = false;
        jobId = null;
        go.disabled = false;
        pickBtn.disabled = false;
        cancelBtn.hidden = true;
        prog.textContent = '';
        if (r.ok) {
          lastResult = r.data || {};
          markResults(lastResult);
          renderList();
          const news = lastResult.suggestions || [];
          for (const e of lastResult.errors || []) {
            review.append(h('div', 'error',
              `${e.code}: ${e.message || ''}`));
          }
          if (news.length) {
            review.append(btn('Tải JSON về máy', 'secondary sm', () => {
              const json = JSON.stringify({ schema_version: lastResult.schema_version,
                suggestions: news, errors: lastResult.errors || [] }, (key, value) => key === 'reviewed' ? undefined : value, 2);
              const url = URL.createObjectURL(new Blob([json], { type: 'application/json;charset=utf-8' }));
              const anchor = document.createElement('a');
              anchor.href = url;
              anchor.download = 'word-goi-y.json';
              anchor.click();
              URL.revokeObjectURL(url);
            }));
            review.append(h('div', 'cd-suggest-title',
              `${news.length} gợi ý mới — xử lý tại đây hoặc đóng ` +
              'và xử lý trong khay gợi ý dưới Stage.'));
            for (const s2 of news) review.append(reviewCardEl(s2));
          } else if (!(lastResult.errors || []).length) {
            review.append(face(L.faceEmpty(
              'Không trích được gợi ý nào từ các nguồn.')));
          }
        } else if (r.error && r.error.code === 'user_canceled') {
          for (const it of items) {
            if (it.status === 'đang phân tích') it.status = 'chờ';
          }
          renderList();
          review.append(h('div', 'muted', 'Đã hủy — nguồn giữ nguyên.'));
        } else {
          for (const it of items) {
            if (it.status === 'đang phân tích') {
              it.status = 'lỗi';
              it.error = (r.error && r.error.message) || 'lỗi phân tích';
            }
          }
          renderList();
          review.append(face(L.faceError(r.error || { code: 'unknown' })));
        }
      });
      go.disabled = !model.canWrite();

      box.append(body);
      const foot = h('div', 'modal-foot');
      foot.append(pickBtn, go, cancelBtn, btn('Đóng', 'ghost', close));
      box.append(foot);
    }, { bare: true });
  }

  return { open };
}

const G1_NOTARY_INTAKE = { createIntakeDialog };

if (typeof window !== 'undefined') window.G1_NOTARY_INTAKE = G1_NOTARY_INTAKE;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_INTAKE;
}
