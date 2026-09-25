'use strict';

/* Word export dialog (MIN-112) — "Xuất Word — nhiều văn bản".
 *
 * SOT hanh vi: spec UX §5 + contracts/notary-case-drafting.md §8.
 * - Options qua notary.word_export_options; checkbox theo document ready.
 * - Destination qua pickFiles({directory:true}) → {file_token,is_dir:true}
 *   — renderer khong thay path; main resolve token truoc khi forward.
 * - Mot lan notary.word_export_batch; progress + cancel theo job seam.
 * - Ket qua per-document: Đã lưu (+Mở file qua openPath) / Lỗi (+ly do) /
 *   Bỏ qua (breakdown.skipped — canceled giua batch, MIN-115).
 * - partial/all-failed/canceled deu render; KHONG tu dong khi con loi.
 *
 * Export UMD: window.G1_NOTARY_WORD + module.exports. DOM chi trong open().
 */

const WORD_BLOCK_LABEL = {
  'word.no_assets': 'Hồ sơ chưa có tài sản',
  'word.no_landowner': 'Chưa có chủ đất trên sơ đồ',
  'word.no_deceased_landowner': 'Chưa có chủ đất đã mất',
  'word.no_receiver': 'Chưa có người nhận',
  'word.too_many_assets': 'Quá nhiều tài sản (tối đa 5)',
  'word.too_many_people': 'Quá nhiều người trên sơ đồ (tối đa 20)',
  'word.too_many_signers': 'Quá nhiều người ký (tối đa 20)',
  'word.template_missing': 'Văn bản chưa có mẫu',
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

  function open() {
    let jobId = null;
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
        cb.checked = !!d.ready;
        cb.setAttribute('aria-label', d.display_name || d.document_key);
        lab.append(cb, h('span', '', d.display_name || d.document_key));
        if (!d.ready) {
          lab.append(h('span', 'muted',
            ` — ${WORD_BLOCK_LABEL[d.block_reason] || d.block_reason ||
              'chưa sẵn sàng'}`));
        }
        body.append(lab);
        checks.push({ key: d.document_key, cb });
      }

      // Destination: directory picker → opaque token is_dir:true (§8.3).
      const destLabel = h('span', 'muted', 'Chưa chọn thư mục');
      let destToken = null;
      const pickDir = btn('Chọn thư mục…', '', async () => {
        const r2 = await pickFiles({ directory: true });
        if (!r2.ok) {
          notify(`${r2.error.code}: ${r2.error.message}`, true);
          return;
        }
        const f = (r2.data.files || [])[0];
        if (!f || f.is_dir !== true) {
          notify('Mục đã chọn không phải thư mục.', true);
          return;
        }
        destToken = f.file_token;
        destLabel.textContent = `Thư mục: ${f.name || '(đã chọn)'}`;
      });

      const prog = h('div', 'cd-slot muted');
      const out = h('div', 'cd-slot');
      const cancelBtn = btn('Hủy xuất', '', async () => {
        if (jobId) await cancelJob(jobId);
      });
      cancelBtn.hidden = true;

      const go = btn('Xuất', 'primary', async () => {
        const keys = checks.filter((c) => c.cb.checked).map((c) => c.key);
        if (!keys.length) {
          notify('Chưa chọn văn bản nào.', true);
          return;
        }
        if (!destToken) {
          notify('Chưa chọn thư mục đích.', true);
          return;
        }
        go.disabled = true;
        pickDir.disabled = true;
        cancelBtn.hidden = false;
        out.innerHTML = '';
        prog.textContent = 'Đang gửi…';
        const rr = await model.exportWord(
          keys, { file_token: destToken }, {
            onJob: (job) => {
              if (job && job.job_id) jobId = job.job_id;
              const p = job && job.progress;
              prog.textContent = p
                ? `Đang xuất ${p.done ?? 0}/${p.total ?? '?'} — ` +
                  (p.current_label || '')
                : 'Đang xuất…';
            },
          });
        jobId = null;
        go.disabled = false;
        pickDir.disabled = false;
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

      const row = h('div', 'cd-toolbar');
      row.append(pickDir, go, cancelBtn, btn('Đóng', '', close));
      box.append(row, destLabel, prog, out);
    });
  }

  return { open };
}

const G1_NOTARY_WORD = { createWordDialog };

if (typeof window !== 'undefined') window.G1_NOTARY_WORD = G1_NOTARY_WORD;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_WORD;
}
