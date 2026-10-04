'use strict';

/* Word export dialog (MIN-112 + NAIA-8) — "Xuất Word — nhiều văn bản".
 *
 * SOT hanh vi: spec UX §5 + contracts/notary-case-drafting.md §8.
 * - Nguon mau: folder nguoi dung chon qua pickFiles({directory:true}) →
 *   {file_token,is_dir:true}; backend quet .docx ngay trong thu muc.
 *   Doi folder → xoa NGAY selection cu + khoa Xuat/chon trong luc quet;
 *   chi response cua lan quet moi nhat duoc ap (model scan guard).
 * - Checkbox tung file + Chon tat ca / Bo chon; file blocked (ready:false)
 *   hien ly do, khong cho tich.
 * - Destination qua pickFiles({directory:true}) → token is_dir:true;
 *   renderer khong thay path; main resolve token truoc khi forward.
 * - Tuy chon "Tao thu muc con cho ho so" → create_case_subdir.
 * - Mot lan notary.word_export_batch; progress + cancel theo job seam.
 * - Ket qua per-document: Đã lưu (+Mở file qua openPath) / Lỗi (+ly do) /
 *   Bỏ qua (breakdown.skipped — canceled giua batch, MIN-115).
 * - "Nơi niêm yết" la meta hồ sơ: hien gia tri da luu, Luu qua
 *   model.saveCaseMeta → notary.workspace_update (§6.2); loi luu bao ro.
 * - partial/all-failed/canceled deu render; KHONG tu dong khi con loi.
 *
 * Export UMD: window.G1_NOTARY_WORD + module.exports. DOM chi trong open().
 */

const WORD_BLOCK_LABEL = {
  'word.no_people': 'Stage chưa có người nào',
  'word.no_diagram': 'Chưa có sơ đồ hai bên đã lưu',
  'word.no_assets': 'Hồ sơ chưa có tài sản',
  'word.no_landowner': 'Chưa có chủ đất trên sơ đồ',
  'word.no_deceased_landowner': 'Chưa có chủ đất đã mất',
  'word.no_receiver': 'Chưa có người nhận',
  'word.too_many_assets': 'Quá nhiều tài sản (tối đa 5)',
  'word.too_many_people': 'Quá nhiều người trong Stage',
  'word.too_many_signers': 'Quá nhiều người ký',
  'word.template_missing': 'Văn bản không còn mẫu trong thư mục',
  'word.original_mapping_invalid': 'Hãy kiểm tra và xác nhận lại các vị trí Word gốc',
};

function createWordDialog(ctx) {
  const model = ctx.model;
  const L = ctx.lib;
  const notify = ctx.notify || (() => {});
  const h = ctx.h;
  const btn = ctx.btn;
  const face = ctx.face;
  const openModal = ctx.openModal;
  const pickFiles = ctx.pickFiles || (async () => ({ ok: false }));
  const openPath = ctx.openPath || (async () => ({ ok: false }));
  const cancelJob = ctx.cancelJob || (async () => ({ ok: false }));

  function reasonText(code, message) {
    return WORD_BLOCK_LABEL[code] || message || code || 'lỗi';
  }

  function resultRowEl(d) {
    const row = h('div', 'cd-word-row');
    if (d.status === 'saved') {
      row.append(h('span', 'cd-badge cd-badge-ok', 'Đã lưu'));
      row.append(h('span', 'cd-word-name',
        d.display_name || d.document_key || ''));
      // output_file.path la backend-produced output — openPath cho phep.
      const outPath = d.output_file && d.output_file.path;
      row.append(h('span', 'muted', d.actual_filename || ''));
      if (outPath) {
        row.append(btn('Mở file', '', () => openPath(outPath)));
      }
    } else if (d.status === 'skipped') {
      row.append(h('span', 'cd-badge', 'Bỏ qua'));
      row.append(h('span', 'muted', d.display_name || d.document_key || ''));
      row.append(h('span', 'muted', 'đã hủy trước khi xuất'));
    } else {
      row.append(h('span', 'cd-badge cd-badge-err', 'Lỗi'));
      row.append(h('span', 'cd-word-name',
        d.display_name || d.document_key || ''));
      const e = d.error || {};
      row.append(h('span', 'error', reasonText(e.code, e.message)));
    }
    return row;
  }

  // Chon folder qua picker; tra {file_token,is_dir} hoac null khi nguoi
  // dung huy picker / chon sai — KHONG bao loi cho cancel.
  async function pickDirToken() {
    const r = await pickFiles({ directory: true });
    if (!r.ok) {
      notify(`${r.error.code}: ${r.error.message}`, true);
      return null;
    }
    const f = (r.data.files || [])[0];
    if (!f) return null;                     // cancel picker — giu im
    if (f.is_dir !== true) {
      notify('Mục đã chọn không phải thư mục.', true);
      return null;
    }
    return f;
  }

  function open() {
    let jobId = null;
    openModal(async (box, close) => {
      // Scope rieng dialog Word — rule `.cd-word-modal [hidden]` trong
      // case-drafting.css restore an cho [hidden] (author `button`
      // display:inline-flex thang thuoc tinh hidden cua UA).
      box.classList.add('cd-word-modal');
      box.append(h('div', 'cd-modal-title', 'Xuất Word — nhiều văn bản'));

      // ---- state nội bộ dialog ----
      let tplToken = null;                   // {file_token} thu muc mau
      let originalSourceId = null;
      let destToken = null;                  // {file_token} thu muc dich
      let checks = [];                       // [{key, cb}]
      let exporting = false;
      let scanning = false;                  // dang quet thu muc mau
      let savingMeta = false;                // dang luu meta (workspace_update)
      let mappingDirty = false;
      let mappingChoices = [];

      const tplLabel = h('span', 'muted', 'Chưa chọn thư mục mẫu');
      const destLabel = h('span', 'muted', 'Chưa chọn thư mục đích');
      const listBox = h('div', 'cd-slot');
      listBox.append(h('div', 'muted',
        'Chọn thư mục chứa file mẫu .docx để xem danh sách văn bản.'));
      const prog = h('div', 'cd-slot muted');
      const out = h('div', 'cd-slot');

      const subdirLab = h('label', 'cd-check-row');
      const subdirCb = h('input');
      subdirCb.type = 'checkbox';
      subdirCb.setAttribute('aria-label',
        'Tạo thư mục con cho hồ sơ trong thư mục đích');
      subdirLab.append(subdirCb,
        h('span', '', 'Tạo thư mục con cho hồ sơ'));

      const selAll = btn('Chọn tất cả', 'sm', () => {
        for (const c of checks) if (!c.cb.disabled) c.cb.checked = true;
      });
      const selNone = btn('Bỏ chọn', 'sm', () => {
        for (const c of checks) c.cb.checked = false;
      });
      // Toolbar chon luon nam trong DOM (ke ca luc dang quet) — chi bi
      // khoa, khong bien mat, de nguoi dung thay ro trang thai.
      const selBar = h('div', 'cd-toolbar');
      selBar.append(selAll, selNone);

      // Khoa Xuat + nut chon khi dang quet folder mau, dang xuat hoac
      // dang luu meta — options/selection/noi_niem_yet dang doi, khong
      // cho nguoi dung xuat luc do.
      function refreshScanLock() {
        go.disabled = scanning || exporting || savingMeta || mappingDirty ||
          !model.canWrite();
        selAll.disabled = scanning || exporting || !checks.length;
        selNone.disabled = scanning || exporting || !checks.length;
        for (const choice of mappingChoices) choice.cb.disabled = scanning || exporting || savingMeta || !choice.proposal.supported;
      }

      function renderDocs() {
        // Doi folder → selection cu mat (checkbox rebuilt tu options moi).
        checks = [];
        listBox.innerHTML = '';
        const docs = model.state.wordOptions || [];
        if (!docs.length) {
          listBox.append(h('div', 'muted',
            'Thư mục không có file .docx nào.'));
          return;
        }
        for (const d of docs) {
          const lab = h('label', 'cd-check-row');
          const cb = h('input');
          cb.type = 'checkbox';
          cb.disabled = !d.ready;
          cb.checked = !!d.ready;
          cb.setAttribute('aria-label', d.display_name || d.document_key);
          lab.append(cb, h('span', '', d.display_name || d.document_key));
          if (!d.ready) {
            lab.append(h('span', 'muted',
              ` — ${WORD_BLOCK_LABEL[d.block_reason] || d.block_reason ||
                'chưa sẵn sàng'}`));
          }
          listBox.append(lab);
          checks.push({ key: d.document_key, cb });
        }
      }

      const pickTpl = btn('Chọn thư mục mẫu…', '', async () => {
        if (exporting || savingMeta) return;
        const f = await pickDirToken();
        if (!f) return;
        tplToken = { file_token: f.file_token };
        originalSourceId = null;
        mappingDirty = false;
        tplLabel.textContent = `Thư mục mẫu: ${f.name || '(đã chọn)'}`;
        // Doi folder → xoa NGAY selection cu; khoa Xuat/chon cho toi khi
        // scan xong de khong xuat nham mau cua folder truoc (review B1).
        checks = [];
        scanning = true;
        refreshScanLock();   // xoa selection → selAll/selNone cung khoa
        listBox.innerHTML = '';
        listBox.append(face(L.faceLoading('Đang quét thư mục mẫu…')));
        const r = await model.loadWordOptions(tplToken);
        if (r && r.stale) return;            // scan moi hon dang tu render
        scanning = false;
        refreshScanLock();
        if (!r.ok) {
          // Thu muc hong/mat doc duoc → giai phong token, xoa selection.
          tplToken = null;
          checks = [];
          listBox.innerHTML = '';
          listBox.append(face(L.faceError(r.error)));
          return;
        }
        renderDocs();
        refreshScanLock();   // checks da rebuild — mo lai nut chon
      });

      const pickDest = btn('Chọn thư mục đích…', '', async () => {
        if (exporting) return;
        const f = await pickDirToken();
        if (!f) return;
        destToken = { file_token: f.file_token };
        destLabel.textContent = `Thư mục đích: ${f.name || '(đã chọn)'}`;
      });

      const cancelBtn = btn('Hủy xuất', '', async () => {
        if (jobId) await cancelJob(jobId);
      });
      cancelBtn.hidden = true;

      const go = btn('Xuất', 'primary', async () => {
        if (exporting || scanning || savingMeta) return;
        if (mappingDirty) { notify('Hãy xác nhận và lưu lựa chọn vị trí trước khi xuất', true); return; }
        if (postingChanged()) {
          niemYetMsg.textContent = 'Nơi niêm yết đã thay đổi. Hãy bấm “Lưu nơi niêm yết” trước khi xuất.';
          niemYetMsg.className = 'error';
          niemYetInput.focus();
          return;
        }
        const keys = checks.filter((c) => c.cb.checked).map((c) => c.key);
        if (!tplToken && !originalSourceId) {
          notify('Chưa chọn thư mục chứa file mẫu.', true);
          return;
        }
        if (!keys.length) {
          notify('Chưa chọn văn bản nào.', true);
          return;
        }
        if (!destToken) {
          notify('Chưa chọn thư mục đích.', true);
          return;
        }
        exporting = true;
        refreshScanLock();
        pickTpl.disabled = true;
        pickDest.disabled = true;
        cancelBtn.hidden = false;
        out.innerHTML = '';
        prog.textContent = 'Đang gửi…';
        const rr = await model.exportWord(
          keys, destToken, {
            templateDir: tplToken,
            originalSourceId,
            createCaseSubdir: subdirCb.checked,
            onJob: (job) => {
              if (job && job.job_id) jobId = job.job_id;
              const p = job && job.progress;
              prog.textContent = p
                ? `Đang xuất ${p.done ?? 0}/${p.total ?? '?'} — ` +
                  (p.current_label || '')
                : 'Đang xuất…';
            },
          });
        if (rr.stale) return;
        jobId = null;
        exporting = false;
        refreshScanLock();
        pickTpl.disabled = false;
        pickDest.disabled = false;
        cancelBtn.hidden = true;
        prog.textContent = '';
        const res = model.state.wordResult;
        if (res && res.documents && res.documents.length) {
          if (res.destination && res.destination.path) {
            out.append(h('div', 'muted',
              `Thư mục đích: ${res.destination.path}`));
          }
          const bd = res.breakdown || {};
          out.append(h('div', 'muted',
            `Thành công ${(bd.succeeded || []).length} · ` +
            `lỗi ${(bd.failed || []).length} · ` +
            `bỏ qua ${(bd.skipped || []).length}`));
          for (const d of res.documents) out.append(resultRowEl(d));
          if (rr.ok && rr.partial) {
            out.append(h('div', 'muted warn-text',
              'Một phần văn bản lỗi — xem từng dòng.'));
          }
          if (!rr.ok && rr.error && rr.error.code === 'user_canceled') {
            out.append(h('div', 'muted',
              'Đã hủy — phần chưa xuất đánh dấu “Bỏ qua”.'));
          }
        } else if (!rr.ok) {
          out.append(face(L.faceError(rr.error || { code: 'unknown' })));
        }
        // Khong tu dong dialog khi con loi/cancel (spec §5) — nguoi
        // dung doc ket qua roi tu dong.
      });
      go.disabled = !model.canWrite();   // export_batch la write (§5.3)
      refreshScanLock();                 // checks rong → nut chon khoa

      // ---- Nơi niêm yết (meta hồ sơ — §6.2 workspace_update) ----
      // Gia tri khoi tao tu caseInfo da tai qua workspace_get; mo lai
      // dialog doc lai state moi nhat. Luu loi → hien ro tai cho + notify.
      const niemYetInput = h('input');
      niemYetInput.type = 'text';
      niemYetInput.setAttribute('aria-label', 'Nơi niêm yết');
      const metaCanEdit = model.canWrite() &&
        typeof model.saveCaseMeta === 'function';
      niemYetInput.disabled = !metaCanEdit;
      niemYetInput.value =
        (model.state.caseInfo && model.state.caseInfo.noi_niem_yet) || '';
      const niemYetMsg = h('span', 'muted', '');
      function postingChanged() {
        const committed = model.state.committedCaseInfo || {};
        return niemYetInput.value.trim() !== (committed.noi_niem_yet || '').trim();
      }
      function showPostingDraft() {
        niemYetMsg.textContent = postingChanged()
          ? 'Nơi niêm yết đã thay đổi. Hãy bấm “Lưu nơi niêm yết” trước khi xuất.' : '';
        niemYetMsg.className = postingChanged() ? 'error' : 'muted';
      }
      niemYetInput.oninput = showPostingDraft;
      showPostingDraft();
      const niemYetSave = btn('Lưu nơi niêm yết', 'sm', async () => {
        if (exporting || scanning || savingMeta || !metaCanEdit) return;
        // Khoa Xuat + input + Luu lap trong luc save pending — batch phai
        // chay voi gia tri da persist xong, khong phai ban cu (review:
        // bam Luu roi Xuat ngay truoc day van xuat voi noi cu).
        savingMeta = true;
        niemYetInput.disabled = true;
        niemYetSave.disabled = true;
        refreshScanLock();
        niemYetMsg.textContent = '';
        niemYetMsg.className = 'muted';
        const v = niemYetInput.value.trim();
        let r;
        try {
          r = await model.saveCaseMeta({ noi_niem_yet: v || null });
        } finally {
          savingMeta = false;
          // Mo lai theo quyen hien tai — save loi locked/conflict co
          // the doi canWrite (locked → giu khoa luon).
          const canEdit = metaCanEdit && model.canWrite();
          niemYetInput.disabled = !canEdit;
          niemYetSave.disabled = !canEdit;
          refreshScanLock();
        }
        if (!r || !r.ok) {
          const e = (r && r.error) || {};
          niemYetMsg.textContent =
            `Lưu thất bại: ${e.message || e.code || 'lỗi'}`;
          niemYetMsg.className = 'error';
          notify(
            `Lưu nơi niêm yết thất bại: ${e.code || 'lỗi'}`, true);
          return;
        }
        niemYetMsg.textContent = 'Đã lưu.';
      });
      niemYetSave.disabled = !metaCanEdit;
      const niemYetRow = h('div', 'cd-toolbar');
      niemYetRow.append(h('span', '', 'Nơi niêm yết:'),
                        niemYetInput, niemYetSave, niemYetMsg);

      const tplRow = h('div', 'cd-toolbar');
      tplRow.append(pickTpl, tplLabel);
      const originalBox = h('div', 'cd-slot');
      for (const source of (model.state.docxImport && model.state.docxImport.sources) || []) {
        const sourceRow = h('div', 'cd-toolbar'); originalBox.append(sourceRow);
        const sourceLabel = source.label || `Nguồn ${source.source_id.slice(0, 8)}`;
        sourceRow.append(btn('Gỡ nguồn Word: ' + sourceLabel, 'ghost sm', async () => {
          if (exporting || scanning || savingMeta) return;
          const previousContext = JSON.parse(JSON.stringify(model.state.docxImport));
          const previousDirty = model.state.stageDirty;
          const previousCase = model.state.caseId;
          if (!model.detachOriginalSource(source.source_id)) return;
          savingMeta = true;
          refreshScanLock();
          let committed = false;
          try {
            const saved = await model.commitStage();
            if (!saved.ok) { notify(saved.error.message || saved.error.code, true); return; }
            committed = true;
            if (model.state.caseId !== previousCase || saved.stale) return;
            if (originalSourceId === source.source_id) { originalSourceId = null; mappingDirty = false; checks = []; listBox.innerHTML = ''; }
            sourceRow.remove();
            notify('Đã gỡ nguồn Word; dữ liệu Stage vẫn được giữ');
          } catch (error) {
            notify(error.message || 'Không lưu được việc gỡ nguồn Word', true);
          } finally {
            if (!committed && model.state.caseId === previousCase) {
              model.state.docxImport = previousContext;
              model.state.stageDirty = previousDirty;
            }
            savingMeta = false; refreshScanLock();
          }
        }));
        sourceRow.append(btn('Dùng hợp đồng Word đã nhập: ' + sourceLabel, 'secondary', async () => {
          if (exporting || scanning || savingMeta) return;
          if (model.hasUnsaved()) { notify('Hãy Cập nhật Stage và Lưu sơ đồ trước khi gắn vị trí', true); return; }
          originalSourceId = source.source_id;
          mappingDirty = false;
          tplToken = null;
          scanning = true;
          checks = [];
          mappingChoices = [];
          listBox.innerHTML = '';
          listBox.append(h('div', 'muted', 'Đang tải các vị trí của nguồn Word…'));
          refreshScanLock();
          const selectionCase = model.state.caseId;
          let r;
          try { r = await model.loadWordOptions(null, originalSourceId); }
          catch (error) { r = { ok: false, error: { message: error.message || 'Không tải được vị trí Word' } }; }
          if (r.stale || model.state.caseId !== selectionCase) return;
          scanning = false;
          if (!r.ok) {
            listBox.innerHTML = '';
            listBox.append(h('div', 'error', 'Không tải được các vị trí Word; chọn lại nguồn để thử lại.'));
            notify(r.error.message || r.error.code, true); refreshScanLock(); return;
          }
          tplLabel.textContent = 'Mẫu: hợp đồng Word gốc đã lưu trong hồ sơ';
          renderDocs();
          const mappingBox = h('div', 'cd-slot');
          mappingBox.append(h('div', 'muted', 'Chọn từng vị trí sẽ thay. Chữ gốc → dòng đã lưu → giá trị xuất. Các chỗ không chọn giữ nguyên.'));
          const choices = [];
          mappingChoices = choices;
          for (const proposal of model.state.wordBindingProposals || []) {
            const lab = h('label', 'cd-check-row');
            const cb = h('input');
            cb.type = 'checkbox';
            cb.disabled = !proposal.supported;
            cb.checked = !!proposal.selected;
            cb.onchange = () => { if (savingMeta || exporting || scanning) return; mappingDirty = true; refreshScanLock(); };
            cb.setAttribute('aria-label', `${proposal.raw_snippet} thành ${proposal.slot}`);
            lab.append(cb, h('span', '', `${proposal.raw_snippet} → ${proposal.row_label} (${proposal.row_id}) · ${proposal.slot} → ${proposal.value}`));
            if (!proposal.supported) lab.append(h('span', 'error', proposal.reason || 'Vùng Word chưa hỗ trợ sửa'));
            mappingBox.append(lab);
            choices.push({ proposal, cb });
          }
          mappingBox.append(btn('Xác nhận và lưu các vị trí đã chọn', 'primary sm', async () => {
            if (exporting || scanning || savingMeta || originalSourceId !== source.source_id) return;
            const bindings = choices.filter((c) => c.cb.checked && !c.cb.disabled).map((c) => c.proposal);
            const previousContext = JSON.parse(JSON.stringify(model.state.docxImport));
            const previousDirty = model.state.stageDirty;
            const previousCase = model.state.caseId;
            if (!model.confirmOriginalBindings(originalSourceId, bindings)) { notify('Hồ sơ đã đổi; hãy tải lại', true); return; }
            savingMeta = true;
            for (const choice of choices) choice.cb.disabled = true;
            refreshScanLock();
            let committed = false;
            try {
              const saved = await model.commitStage();
              if (!saved.ok) {
                notify(saved.error.message || saved.error.code, true); return;
              }
              committed = true;
              if (saved.stale || model.state.caseId !== previousCase) return;
              mappingDirty = false;
              const loaded = await model.loadWordOptions(null, source.source_id);
              if (loaded.stale || model.state.caseId !== previousCase) return;
              if (!loaded.ok) {
                checks = []; mappingChoices = [];
                listBox.innerHTML = '';
                listBox.append(h('div', 'error', 'Đã lưu vị trí Word, nhưng chưa tải lại được danh sách. Chọn lại nguồn Word để thử lại.'));
                notify('Đã lưu vị trí Word, nhưng tải lại thất bại; chọn lại nguồn để thử lại', true);
                return;
              }
              renderDocs();
              for (const choice of choices) {
                const current = (model.state.wordBindingProposals || []).find((p) => p.occurrence_id === choice.proposal.occurrence_id);
                choice.proposal = current || { ...choice.proposal, supported: false };
                choice.cb.checked = !!current?.selected;
                choice.cb.disabled = !current?.supported;
              }
              listBox.append(mappingBox);
              notify('Đã lưu vị trí Word; có thể xuất vào thư mục đích');
            } catch (error) {
              if (model.state.caseId !== previousCase) return;
              if (committed) {
                checks = []; mappingChoices = []; mappingDirty = false;
                model.state.wordOptions = null;
                model.state.wordBindingProposals = [];
                listBox.innerHTML = '';
                listBox.append(h('div', 'error', 'Đã lưu vị trí Word, nhưng chưa tải lại được danh sách. Chọn lại nguồn Word để thử lại.'));
                notify('Đã lưu vị trí Word, nhưng tải lại thất bại; chọn lại nguồn để thử lại', true);
              } else notify(error.message || 'Không lưu được vị trí Word', true);
            } finally {
              if (!committed && model.state.caseId === previousCase) {
                model.state.docxImport = previousContext;
                model.state.stageDirty = previousDirty;
              }
              savingMeta = false;
              for (const choice of choices) choice.cb.disabled = !choice.proposal.supported;
              refreshScanLock();
            }
          }));
          listBox.append(mappingBox);
          refreshScanLock();
        }));
      }
      const destRow = h('div', 'cd-toolbar');
      destRow.append(pickDest, destLabel);
      const row = h('div', 'cd-toolbar');
      row.append(go, cancelBtn, btn('Đóng', '', close));
      box.append(tplRow, originalBox, selBar, listBox, destRow, subdirLab, niemYetRow,
                 row, prog, out);
    });
  }

  return { open };
}

const G1_NOTARY_WORD = { createWordDialog };

if (typeof window !== 'undefined') window.G1_NOTARY_WORD = G1_NOTARY_WORD;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_WORD;
}
