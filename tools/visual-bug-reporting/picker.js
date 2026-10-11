(() => {
  if (!window.visualBugSpike || window.__visualPickerLoaded) return;
  window.__visualPickerLoaded = true;
  let picking = false, selected = null, highlight = null, panel = null;
  function reset() {
    picking = false; selected = null;
    highlight?.remove(); panel?.remove(); highlight = panel = null;
  }
  function pathFor(e) {
    const parts = [];
    while (e && e !== document.documentElement) {
      parts.unshift(e.localName + ':nth-child(' + (Array.from(e.parentElement.children).indexOf(e) + 1) + ')');
      e = e.parentElement;
    }
    return 'html > ' + parts.join(' > ');
  }
  function arm() {
    reset(); document.getElementById('vb-toast')?.remove(); picking = true;
    highlight = document.createElement('div'); highlight.id = 'vb-highlight';
    Object.assign(highlight.style, { position: 'fixed', pointerEvents: 'none',
      border: '3px solid red', zIndex: '2147483646', boxSizing: 'border-box' });
    document.body.append(highlight);
  }
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { reset(); return; }
    if (!(e.ctrlKey && e.shiftKey && e.code === 'KeyB')) return;
    e.preventDefault(); arm();
  }, true);
  document.addEventListener('pointermove', e => {
    if (!picking) return;
    const r = e.target.getBoundingClientRect();
    Object.assign(highlight.style, { left: r.x + 'px', top: r.y + 'px', width: r.width + 'px', height: r.height + 'px' });
  }, true);
  document.addEventListener('click', e => {
    if (!picking) return;
    e.preventDefault(); e.stopImmediatePropagation();
    selected = e.target; picking = false;
    panel = document.createElement('div'); panel.id = 'vb-panel'; panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Visual bug report');
    Object.assign(panel.style, { position: 'fixed', right: '20px', bottom: '20px', width: '450px',
      padding: '18px', background: 'white', color: 'black', border: '2px solid red', zIndex: '2147483646' });
    const label = document.createElement('label');
    label.textContent = 'Bug note (your own words, saved to the local report; not anonymized). Image exports layout only.';
    const note = document.createElement('textarea'); note.id = 'vb-note'; note.maxLength = 240;
    Object.assign(note.style, { display: 'block', width: '100%', height: '80px', marginTop: '8px' });
    note.placeholder = 'What looks wrong? (up to 240 characters)';
    note.setAttribute('aria-label', 'Bug note');
    label.append(note);
    const save = document.createElement('button'); save.id = 'vb-save'; save.textContent = 'Save report';
    const cancel = document.createElement('button'); cancel.id = 'vb-cancel'; cancel.textContent = 'Cancel';
    const status = document.createElement('p'); status.id = 'vb-status'; status.setAttribute('role', 'status');
    cancel.onclick = reset;
    save.onclick = async () => {
      if (!note.value.trim()) { status.textContent = 'Enter a short note first.'; note.focus(); return; }
      save.disabled = true; cancel.disabled = true;
      const sourceIds = []; let cur = selected;
      while (cur && sourceIds.length < 40) { if (cur.id && cur.id.length <= 100) sourceIds.push(cur.id); cur = cur.parentElement; }
      // Control identity (schema v2): nearest data-fid, exact classList tokens
      // of the picked element, and module root class. Values (input content,
      // aria-label) are never read — structure only.
      let fidEl = selected, fid = null;
      while (fidEl && fidEl !== document.documentElement) {
        if (fidEl.dataset && typeof fidEl.dataset.fid === 'string' && fidEl.dataset.fid.length >= 1 && fidEl.dataset.fid.length <= 100) { fid = fidEl.dataset.fid; break; }
        fidEl = fidEl.parentElement;
      }
      const classes = Array.from(selected.classList || []).slice(0, 20)
        .filter((t) => t.length <= 40);
      const ownId = typeof selected.id === 'string' && selected.id.length >= 1 && selected.id.length <= 100 ? selected.id : null;
      // Nearest ancestor table's exact classList tokens (same ancestor-walk
      // pattern as the data-fid lookup): with border-collapse the table itself
      // is never a hit target, so a real pick always lands on th/td.
      const tbl = selected.closest ? selected.closest('table') : null;
      const tableTokens = tbl ? Array.from(tbl.classList || []).filter((t) => t.length <= 40).slice(0, 12) : [];
      // Structural cell flag: a th/td pick IS part of the table structure;
      // any other node inside the table is merely contained by it.
      const cellLike = !!(selected.matches && selected.matches('th,td'));
      let modRoot = null;
      if (selected.closest && typeof selected.closest === 'function') {
        if (selected.closest('.cd-root')) modRoot = 'cd-root';
        else if (selected.closest('.upload-lab')) modRoot = 'upload-lab';
      }
      try {
        const result = await window.visualBugSpike.save({ selector: pathFor(selected), note: note.value, sourceIds, fid, ownId, classes, tableTokens, cellLike, moduleRoot: modRoot });
        if (!result.ok) {
          status.textContent = `Save failed: ${result.error}`;
          save.disabled = false; cancel.disabled = false;
          return;
        }
        arm();
        const toast = document.createElement('div'); toast.id = 'vb-toast'; toast.setAttribute('role', 'status');
        toast.textContent = `Saved ${result.id}; screenshot ${result.screenshot}. Tro tiep muc khac…`;
        Object.assign(toast.style, { position: 'fixed', left: '50%', bottom: '20px', transform: 'translateX(-50%)',
          padding: '10px 16px', background: '#111', color: '#fff', zIndex: '2147483646' });
        document.body.append(toast);
        setTimeout(() => toast.remove(), 5000);
      } catch {
        status.textContent = 'Save failed: bridge_error';
        save.disabled = false; cancel.disabled = false;
      }
    };
    panel.append(label, save, cancel, status); document.body.append(panel); note.focus();
  }, true);
})();
