# -*- coding: utf-8 -*-
"""TASK-4 view: Tra buttons, inline results, full overlay, focus/scroll keep."""
from pathlib import Path

path = Path("shell/src/renderer/notary/case-drafting-view.js")
text = path.read_text(encoding="utf-8")

# --- A. replace dormant suggestion block with TASK-4 lookup UI ---------------
start = text.index("  // Ngu dong (TASK-3): khong tu tra khi render.")
end = text.index("  function assetTableEl() {", start)

ui = """  // ---------- Tra cuu dia chi thu cong (TASK-4) ----------
  // Nut Tra nam ben phai o nhap; ket qua hien ngay duoi o tuong ung.
  // May khong bao gio tu ghi vao o/Stage — nguoi dung Copy roi tu dan.

  function lookupStatusMessage(status) {
    if (status === 'not_found') {
      return 'Không tìm thấy địa chỉ phù hợp. Kiểm tra lại chữ đã nhập rồi bấm Tra.';
    }
    if (status === 'invalid_input') {
      return 'Chuỗi tra chưa hợp lệ. Sửa lại rồi bấm Tra.';
    }
    if (status === 'reload_failed') {
      return 'Không đọc được bảng địa chỉ cục bộ. Kiểm tra nguồn dữ liệu rồi bấm Tra lại.';
    }
    return 'Tra cứu thất bại. Bấm Tra lại.';
  }

  async function copyLookupText(display) {
    try {
      const clip = (typeof navigator !== 'undefined' && navigator.clipboard) || null;
      if (!clip || typeof clip.writeText !== 'function') return { ok: false };
      await clip.writeText(display);
      return { ok: true };
    } catch (e) {
      return { ok: false };
    }
  }

  function captureLookupFocus(targetFid) {
    const dp = panels.drafting;
    const el = targetFid ? dp.querySelector(`[data-fid="${targetFid}"]`) : null;
    let sel = null;
    if (el && typeof el.selectionStart === 'number') {
      sel = [el.selectionStart, el.selectionEnd,
        (typeof el.selectionDirection === 'string' && el.selectionDirection) || null];
    }
    return { fid: targetFid, sel,
      top: dp ? dp.scrollTop || 0 : 0, left: dp ? dp.scrollLeft || 0 : 0 };
  }

  function focusTraButton(kind, rowId) {
    const el = panels.drafting.querySelector(
      `[data-fid="lookup-tra:${kind}:${rowId}"]`);
    if (el && el.focus) el.focus();
  }

  async function onTraLookup(kind, rowId, targetFid) {
    const slotKey = kind + ':' + rowId;
    const focusCtx = captureLookupFocus(targetFid);
    await model.requestLookup(kind, rowId);
    const slot = model.state.addressSlots[slotKey];
    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many') {
      focusTraButton(kind, rowId);
      return;
    }
    const ok = await confirm({
      title: 'Nhiều kết quả khớp. Xem đầy đủ?',
      body: 'Danh sách quá dài để hiện dưới ô. Mở công cụ tra cứu đầy đủ?',
      confirmLabel: 'Xem đầy đủ',
      cancelLabel: 'Hủy',
    });
    if (!ok) {
      model.dismissLookupSlot(kind, rowId);
      focusTraButton(kind, rowId);
      return;
    }
    const opened = model.openFullFromSlot(kind, rowId);
    if (!opened.ok) {
      model.markLookupStale(kind, rowId);
      focusTraButton(kind, rowId);
      return;
    }
    openLookupOverlay(focusCtx);
  }

  function lookupTraButton(kind, rowId, targetFid) {
    const tra = btn('Tra', 'secondary sm',
      () => { onTraLookup(kind, rowId, targetFid); });
    tra.dataset.fid = `lookup-tra:${kind}:${rowId}`;
    tra.setAttribute('aria-label', 'Tra cứu địa chỉ');
    return tra;
  }

  function lookupCopyButton(row, fid) {
    const copy = btn('Copy', 'ghost sm', async () => {
      const r = await copyLookupText(row.display);
      if (r.ok) {
        copy.textContent = 'Đã copy';
      } else {
        copy.textContent = 'Copy';
        const warn = copy.parentElement &&
          copy.parentElement.parentElement;
        if (warn) {
          warn.append(h('div', 'muted small',
            'Copy thất bại — hãy copy thủ công.'));
        }
      }
    });
    copy.dataset.fid = fid;
    return copy;
  }

  function lookupResultRows(box, kind, rowId, results) {
    (results || []).forEach((row, i) => {
      const line = h('div', 'cd-lookup-item');
      line.append(h('span', 'small', row.display));
      line.append(lookupCopyButton(row, `lookup-copy:${kind}:${rowId}:${i}`));
      box.append(line);
    });
  }

  function addressSuggestionEl(kind, rowId, afterApply, idPrefix) {
    const box = h('div', 'cd-address-suggestion');
    box.id = `${idPrefix || 'address'}-${kind}-${rowId}`;
    box._afterApply = afterApply;
    box.setAttribute('aria-live', 'polite');
    const slot = model.state.addressSlots[kind + ':' + rowId];
    if (!slot) return box;
    if (slot.phase === 'loading') {
      box.append(h('span', 'muted small', 'Đang tra cứu địa chỉ…'));
      return box;
    }
    if (slot.phase === 'error') {
      box.append(h('span', 'muted small',
        slot.message || 'Tra cứu thất bại.'));
      return box;
    }
    const res = slot.result;
    if (!res) return box;
    if (res.status === 'found') {
      box.append(h('div', 'muted small',
        `Tìm thấy ${res.total} dòng — Copy dòng phù hợp rồi dán vào ô.`));
      lookupResultRows(box, kind, rowId, res.results);
      return box;
    }
    if (res.status === 'too_many') {
      box.append(h('span', 'muted small',
        'Nhiều kết quả khớp. Bấm Tra rồi chọn Xem đầy đủ.'));
      return box;
    }
    box.append(h('span', 'muted small', lookupStatusMessage(res.status)));
    return box;
  }

  function postingSuggestionEl(afterApply, idPrefix) {
    void afterApply;
    void idPrefix;
    return addressSuggestionEl('posting', 'posting');
  }

  // Rebuild trong luc render: khong goi lookup (chi nut Tra moi goi).
  function refreshAddressBoxes(scope) {
    void scope;
  }

  // ---------- Cua so full (overlay) ----------
  let lookupOverlay = null;

  function openLookupOverlay(focusCtx) {
    if (lookupOverlay) lookupOverlay.destroy();
    const full0 = model.state.addressFull;
    const wrap = h('div', 'modal-overlay');
    const box = h('div', 'modal wide');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Tra cứu địa chỉ đầy đủ');
    const head = h('div', 'modal-head');
    head.append(h('div', 'modal-title', 'Tra cứu địa chỉ'));
    const queryInput = h('input', 'cd-cell');
    queryInput.value = (full0 && full0.query) || '';
    queryInput.setAttribute('aria-label', 'Chuỗi tra cứu đầy đủ');
    queryInput.dataset.fid = 'lookup-full-query';
    const traBtn = btn('Tra', 'secondary sm', () => {
      model.requestFull(queryInput.value);
    });
    traBtn.dataset.fid = 'lookup-full-tra';
    const queryRow = h('div', 'cd-lookup-row');
    queryRow.append(queryInput, traBtn);
    const listEl = h('div', 'cd-lookup-list');
    listEl.dataset.fid = 'lookup-full-list';
    const noteEl = h('div', 'muted small');
    noteEl.dataset.fid = 'lookup-full-note';

    function refresh() {
      const full = model.state.addressFull;
      if (!full) return;
      listEl.innerHTML = '';
      noteEl.textContent = '';
      if (full.phase === 'loading') {
        listEl.append(h('div', 'muted small', 'Đang tra cứu…'));
        return;
      }
      if (full.phase === 'error' || !full.result) {
        noteEl.textContent = (full && full.message) || 'Tra cứu thất bại.';
        return;
      }
      const res = full.result;
      if (res.status === 'found') {
        listEl.append(h('div', 'muted small',
          `Tìm thấy ${res.total} dòng — mỗi dòng là một nguồn riêng, Copy dòng phù hợp rồi dán vào hồ sơ.`));
        (res.results || []).forEach((row, i) => {
          const line = h('div', 'cd-lookup-item');
          line.append(h('span', 'small', row.display));
          line.append(lookupCopyButton(row, `lookup-full-copy:${i}`));
          listEl.append(line);
        });
        return;
      }
      noteEl.textContent = lookupStatusMessage(res.status);
    }

    function close(restore) {
      document.removeEventListener('keydown', onKey);
      if (lookupOverlay && lookupOverlay.wrap === wrap) lookupOverlay = null;
      model.closeFull();
      wrap.remove();
      if (!restore) return;
      const dp = panels.drafting;
      try {
        dp.scrollTop = focusCtx.top;
        dp.scrollLeft = focusCtx.left;
      } catch (e) { /* giu nguyen neu khong cuon duoc */ }
      if (focusCtx.fid) {
        const el = dp.querySelector(`[data-fid="${focusCtx.fid}"]`);
        if (el && el.focus) {
          el.focus();
          if (focusCtx.sel &&
              typeof el.setSelectionRange === 'function') {
            try {
              const sel = focusCtx.sel;
              if (sel[2]) el.setSelectionRange(sel[0], sel[1], sel[2]);
              else el.setSelectionRange(sel[0], sel[1]);
            } catch (e) { /* giu focus, bo caret */ }
          }
        }
      }
    }

    function destroy() {
      document.removeEventListener('keydown', onKey);
      if (lookupOverlay && lookupOverlay.wrap === wrap) lookupOverlay = null;
      wrap.remove();
    }

    function onKey(e) {
      if (e.key === 'Escape') { close(true); return; }
      if (e.key !== 'Tab') return;
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

    const xBtn = h('button', 'modal-close', '\\u00d7');
    xBtn.type = 'button';
    xBtn.setAttribute('aria-label', 'Đóng');
    xBtn.onclick = () => close(true);
    head.append(xBtn);
    const closeBtn = btn('Đóng', 'secondary sm', () => close(true));
    closeBtn.dataset.fid = 'lookup-full-close';
    const foot = h('div', 'modal-foot');
    foot.append(closeBtn);
    box.append(head, queryRow, listEl, noteEl, foot);
    wrap.onclick = (e) => { if (e.target === wrap) close(true); };
    wrap.append(box);
    root.append(wrap);
    document.addEventListener('keydown', onKey);
    if (queryInput.focus) queryInput.focus();
    lookupOverlay = { wrap, refresh, close, destroy,
      savedScroll: focusCtx };
    refresh();
  }

"""
text = text[:start] + ui + text[end:]

# --- B. asset dia_chi cell: input + Tra row, result below --------------------
old_asset = """          td.append(inp);
          cellErrs(a.row_id, key, td);
          if (key === 'dia_chi') {
            inp.setAttribute('aria-describedby', `address-asset-${a.row_id}`);
            td.append(addressSuggestionEl('asset', a.row_id));
          }
"""
new_asset = """          if (key === 'dia_chi') {
            inp.setAttribute('aria-describedby', `address-asset-${a.row_id}`);
            const trow = h('div', 'cd-lookup-row');
            trow.append(inp,
              lookupTraButton('asset', a.row_id, `a:${a.row_id}:dia_chi`));
            td.append(trow);
          } else {
            td.append(inp);
          }
          cellErrs(a.row_id, key, td);
          if (key === 'dia_chi') {
            td.append(addressSuggestionEl('asset', a.row_id));
          }
"""
assert old_asset in text, "asset cell not found"
text = text.replace(old_asset, new_asset, 1)

# --- C. person dia_chi + issuer noi_cap --------------------------------------
old_person = """        td.append(ctl);
        if (key === 'dia_chi') {
          ctl.setAttribute('aria-describedby', `address-person-${p.row_id}`);
          td.append(addressSuggestionEl('person', p.row_id));
          // Hien ca khi ngay_chet rong ma noi_cap con du lieu"""
new_person = """        if (key === 'dia_chi') {
          ctl.setAttribute('aria-describedby', `address-person-${p.row_id}`);
          const trow = h('div', 'cd-lookup-row');
          trow.append(ctl,
            lookupTraButton('person', p.row_id, `p:${p.row_id}:dia_chi`));
          td.append(trow);
          td.append(addressSuggestionEl('person', p.row_id));
          // Hien ca khi ngay_chet rong ma noi_cap con du lieu"""
assert old_person in text, "person cell not found"
text = text.replace(old_person, new_person, 1)

old_issuer = """            td.append(issuer, addressSuggestionEl('issuer', p.row_id));
"""
new_issuer = """            const irow = h('div', 'cd-lookup-row');
            irow.append(issuer,
              lookupTraButton('issuer', p.row_id, `p:${p.row_id}:noi_cap`));
            td.append(irow, addressSuggestionEl('issuer', p.row_id));
"""
assert old_issuer in text, "issuer cell not found"
text = text.replace(old_issuer, new_issuer, 1)

# --- C2. person cell: non-dia_chi keys still append the bare input ---------
old_person_else = """            td.append(irow, addressSuggestionEl('issuer', p.row_id));
          }
        }
        cellErrs(p.row_id, key, td);
"""
new_person_else = """            td.append(irow, addressSuggestionEl('issuer', p.row_id));
          }
        } else {
          td.append(ctl);
        }
        cellErrs(p.row_id, key, td);
"""
assert old_person_else in text, "person else anchor not found"
text = text.replace(old_person_else, new_person_else, 1)

# --- D. posting meta row ------------------------------------------------------
old_post = """    r1.append(ny);
    box.append(r1);
    box.append(postingSuggestionEl());
"""
new_post = """    const nyrow = h('div', 'cd-lookup-row');
    nyrow.append(ny, lookupTraButton('posting', 'posting', 'meta:noi_niem_yet'));
    r1.append(nyrow);
    box.append(r1);
    box.append(postingSuggestionEl());
"""
assert old_post in text, "posting meta not found"
text = text.replace(old_post, new_post, 1)

# --- E. rerender: keep dp scroll + refresh overlay ----------------------------
old_tail = """      } else if (s.status !== 'conflict') {
        lastConflict = null;
      }
    }
  }

  model.subscribe(rerender);
"""
new_tail = """      } else if (s.status !== 'conflict') {
        lastConflict = null;
      }
    }
    if (lookupOverlay) {
      const st = lookupOverlay.savedScroll;
      if (st) {
        try {
          dp.scrollTop = st.top;
          dp.scrollLeft = st.left;
        } catch (e) { /* giu nguyen neu khong cuon duoc */ }
      }
      lookupOverlay.refresh();
    }
  }

  model.subscribe(rerender);
"""
assert old_tail in text, "rerender tail not found"
text = text.replace(old_tail, new_tail, 1)

path.write_text(text, encoding="utf-8")
print("view TASK-4 done")
