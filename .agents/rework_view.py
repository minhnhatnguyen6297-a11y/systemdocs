# -*- coding: utf-8 -*-
"""Rework view R3/R5: in-place result refresh, true edit focus, no focus steal."""
from pathlib import Path

path = Path("shell/src/renderer/notary/case-drafting-view.js")
text = path.read_text(encoding="utf-8")

# 1. Track the actually-edited input: focusin (keyboard path) + Tra-button
#    mousedown (mouse path, fires before the button takes focus).
old = """  // ---------- Tra cuu dia chi thu cong (TASK-4) ----------
  // Nut Tra nam ben phai o nhap; ket qua hien ngay duoi o tuong ung.
  // May khong bao gio tu ghi vao o/Stage — nguoi dung Copy roi tu dan.
"""
new = """  // ---------- Tra cuu dia chi thu cong (TASK-4) ----------
  // Nut Tra nam ben phai o nhap; ket qua hien ngay duoi o tuong ung.
  // May khong bao gio tu ghi vao o/Stage — nguoi dung Copy roi tu dan.
  // O "dang sua" la o that su co focus truoc khi nut Tra lay focus (co the
  // khac o dich, vd dang sua Ho ten roi bam Tra dia chi): theo doi qua
  // focusin (ban phim) + mousedown tren nut Tra (chuot, chay truoc khi
  // focus doi). Huy cau hoi/dong full phuc hoi dung o nay.

  let lastEditFid = null;
  let pendingMouseCtx = null;

  function noteEditInput(el) {
    if (!el || !/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName || '')) return null;
    if (!el.dataset || !el.dataset.fid) return null;
    if (!panels.drafting.contains(el)) return null;
    let sel = null;
    if (typeof el.selectionStart === 'number') {
      sel = [el.selectionStart, el.selectionEnd,
        (typeof el.selectionDirection === 'string' && el.selectionDirection) || null];
    }
    return { fid: el.dataset.fid, sel };
  }

  function trackEditFocus() {
    if (typeof root.addEventListener === 'function') {
      root.addEventListener('focusin', (e) => {
        const noted = noteEditInput(e && e.target);
        if (noted) lastEditFid = noted.fid;
      });
    }
  }

  function restoreLookupFocus(focusCtx) {
    if (!focusCtx || !focusCtx.fid) return;
    const dp = panels.drafting;
    const el = dp.querySelector(`[data-fid="${focusCtx.fid}"]`);
    if (!el || !el.focus) return;
    el.focus();
    if (focusCtx.sel && typeof el.setSelectionRange === 'function') {
      try {
        const sel = focusCtx.sel;
        if (sel[2]) el.setSelectionRange(sel[0], sel[1], sel[2]);
        else el.setSelectionRange(sel[0], sel[1]);
      } catch (e) { /* giu focus, bo caret */ }
    }
  }
"""
assert old in text, "lookup header not found"
text = text.replace(old, new, 1)

# 2. captureLookupFocus prefers mouse/focusin-tracked element over target box.
old = """  function captureLookupFocus(targetFid) {
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
"""
new = """  function captureLookupFocus(targetFid) {
    const dp = panels.drafting;
    const noted = pendingMouseCtx;
    pendingMouseCtx = null;
    let fid = targetFid;
    if (noted && noted.fid) {
      fid = noted.fid;
    } else if (lastEditFid &&
        dp.querySelector(`[data-fid="${lastEditFid}"]`)) {
      fid = lastEditFid;
    }
    const el = fid ? dp.querySelector(`[data-fid="${fid}"]`) : null;
    let sel = null;
    if (el && typeof el.selectionStart === 'number') {
      sel = [el.selectionStart, el.selectionEnd,
        (typeof el.selectionDirection === 'string' && el.selectionDirection) || null];
    }
    return { fid, sel,
      top: dp ? dp.scrollTop || 0 : 0, left: dp ? dp.scrollLeft || 0 : 0 };
  }

  async function onTraLookup(kind, rowId, targetFid) {
    const slotKey = kind + ':' + rowId;
    const focusCtx = captureLookupFocus(targetFid);
    await model.requestLookup(kind, rowId);
    // Ket qua tu cap nhat qua emit/rerender; KHONG keo focus ve nut Tra —
    // nguoi dung co the dang sua o khac.
    const slot = model.state.addressSlots[slotKey];
    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many') {
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
      restoreLookupFocus(focusCtx);
      return;
    }
    const opened = model.openFullFromSlot(kind, rowId);
    if (!opened.ok) {
      model.markLookupStale(kind, rowId);
      restoreLookupFocus(focusCtx);
      return;
    }
    openLookupOverlay(focusCtx);
  }

  function lookupTraButton(kind, rowId, targetFid) {
    const tra = btn('Tra', 'secondary sm',
      () => { onTraLookup(kind, rowId, targetFid); });
    tra.dataset.fid = `lookup-tra:${kind}:${rowId}`;
    tra.setAttribute('aria-label', 'Tra cứu địa chỉ');
    if (typeof tra.addEventListener === 'function') {
      tra.addEventListener('mousedown', () => {
        pendingMouseCtx = noteEditInput(document.activeElement);
      });
    }
    return tra;
  }
"""
assert old in text, "onTraLookup block not found"
text = text.replace(old, new, 1)

# 3. refreshAddressBoxes: rebuild only the result boxes (no inputs inside).
old = """  // Rebuild trong luc render: khong goi lookup (chi nut Tra moi goi).
  function refreshAddressBoxes(scope) {
    void scope;
  }
"""
new = """  // Lam moi rieng cac o ket qua (khong chua input nen an toan ngay ca
  // khi nguoi dung dang go): render lai tai cho, khong goi lookup, khong
  // doi focus.
  function refreshAddressBoxes(scope) {
    if (!scope || typeof scope.querySelectorAll !== 'function') return;
    let boxes = [];
    try {
      boxes = [...scope.querySelectorAll('[id^="address-"]')];
    } catch (e) {
      return;
    }
    for (const box of boxes) {
      const m = /^address-(person|asset|issuer|posting)-(.+)$/
        .exec(box.id || '');
      if (m) box.replaceWith(addressSuggestionEl(m[1], m[2], box._afterApply));
    }
  }
"""
assert old in text, "refreshAddressBoxes not found"
text = text.replace(old, new, 1)

# 4. overlay close reuses the shared restore routine.
old = """      if (!restore) return;
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
"""
new = """      if (!restore) return;
      const dp = panels.drafting;
      try {
        dp.scrollTop = focusCtx.top;
        dp.scrollLeft = focusCtx.left;
      } catch (e) { /* giu nguyen neu khong cuon duoc */ }
      restoreLookupFocus(focusCtx);
    }
"""
assert old in text, "overlay close restore not found"
text = text.replace(old, new, 1)

# 5. start edit tracking once the view is built.
old = """  model.subscribe(rerender);
  rerender();
"""
new = """  model.subscribe(rerender);
  trackEditFocus();
  rerender();
"""
assert old in text, "view init not found"
text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("view rework done")
