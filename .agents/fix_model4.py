# -*- coding: utf-8 -*-
"""TASK-4 model: manual Tra with callId+generation guards, correct query sources."""
from pathlib import Path

path = Path("shell/src/renderer/notary/case-drafting-model.js")
text = path.read_text(encoding="utf-8")

# --- 1. addressContext: correct per-field query sources ---------------------
old_ctx = """  // Nguon chuoi tra cuu (TASK-3 giu tam nhu cu; TASK-4 sua theo spec:
  // noi cap khai tu lay dia chi nguoi chet, noi niem yet lay o chinh).
  function addressContext(kind, rowId) {
    const person = kind === 'person' || kind === 'issuer';
    const row = (person ? state.stage.people : state.stage.assets).find(r => r.row_id === rowId);
    if (!row) return null;
    const query = kind === 'issuer' ? row.noi_cap : row.dia_chi;
    if (typeof query !== 'string' || !query.trim()) return null;
    return { query, presentation: 'drafting' };
  }
"""
new_ctx = """  // Nguon chuoi tra cuu theo spec: dia chi Nguoi/Tai san lay o dia chi
  // cua chinh dong do; Noi niem yet lay noi dung chinh o niem yet; Noi cap
  // giay khai tu lay dia chi cua chinh nguoi da chet (o dich van la noi_cap
  // cua nguoi do — hai o co the khac nhau). Doc tu state model (input nao
  // cung dong bo vao model ngay khi go) nen la chu chua luu moi nhat.
  function lookupSlotKey(kind, rowId) {
    return kind + ':' + rowId;
  }

  function addressContext(kind, rowId) {
    if (kind === 'posting') {
      const query = (state.caseInfo || {}).noi_niem_yet;
      if (typeof query !== 'string' || !query.trim()) return null;
      return { query, presentation: 'drafting' };
    }
    const person = kind === 'person' || kind === 'issuer';
    const row = (person ? state.stage.people : state.stage.assets)
      .find(r => r.row_id === rowId);
    if (!row) return null;
    // issuer tra dia chi nguoi chet, khong tra chu trong o noi_cap.
    const query = row.dia_chi;
    if (typeof query !== 'string' || !query.trim()) return null;
    return { query, presentation: 'drafting' };
  }
"""
assert old_ctx in text, "addressContext block not found"
text = text.replace(old_ctx, new_ctx, 1)

# --- 2. seq/callId state + slot/full stores ----------------------------------
old_state = """  // Tra cuu dia chi ngu dong (TASK-3): khong tu tra khi render/go,
  // khong debounce/timer, khong ghi Stage/o. Chi ham goi truc tiep
  // ensureAddressSuggestion (nut Tra cua TASK-4 se dung) moi gui lenh.
  state.addressSuggestions = {};
  state.postingAssetId = null;
"""
new_state = """  // Tra cuu dia chi thu cong (TASK-4): chi nut Tra moi gui lenh, khong
  // tu tra khi render/go, khong ghi Stage/o. lookupSeq don dieu tang moi
  // khi du lieu nguon doi hoac co lan Tra moi — response chi hien khi seq
  // van nguyen (bat ca A->B->A). lookupCallId phan biet cac lan Tra.
  let lookupSeq = 0;
  let lookupCallId = 0;
  state.addressSlots = {};
  state.addressFull = null;
  state.addressSuggestions = {};
  state.postingAssetId = null;
"""
assert old_state in text, "lookup state block not found"
text = text.replace(old_state, new_state, 1)

old_clear = """  function clearAddressLookups() {
    state.addressSuggestions = {};
    state.postingAssetId = null;
  }
"""
new_clear = """  function clearAddressLookups() {
    lookupSeq += 1;
    state.addressSlots = {};
    state.addressFull = null;
    state.addressSuggestions = {};
    state.postingAssetId = null;
  }

  function lookupShapeValid(data) {
    return !!data && data.schema_version === 'notary.address-lookup.v2' &&
      typeof data.status === 'string' && Array.isArray(data.results) &&
      typeof data.total === 'number';
  }

  function lookupFailure(response) {
    return { ok: false,
      error: { message: 'Không đọc được bảng địa chỉ cục bộ.' } };
  }
"""
assert old_clear in text, "clearAddressLookups not found"
text = text.replace(old_clear, new_clear, 1)

# --- 3. replace ensureAddressSuggestion with requestLookup + full session ----
start = text.index("  // Chi goi truc tiep (nut Tra o TASK-4).")
end = text.index("  function emit() {", start)
new_fns = """  // Nut Tra cua o drafting: gui {query, presentation:'drafting'} voi
  // chu dang thay trong o nguon. Bam lai cung chuoi van gui (khong chan).
  // Moi lan bam la mot callId moi; response cu (sai callId, doi seq, doi
  // session, query hien tai khac luc bam) deu bi bo.
  async function requestLookup(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    const payload = addressContext(kind, rowId);
    lookupSeq += 1;
    const callId = ++lookupCallId;
    if (!payload) {
      state.addressSlots[key] = { phase: 'error', query: '', callId,
        message: 'Nhập địa chỉ cần tra rồi bấm Tra.' };
      emit();
      return;
    }
    state.addressSlots[key] = { phase: 'loading', query: payload.query,
      callId };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    let response;
    try { response = await client.run('notary.address_lookup', payload); }
    catch (error) { response = lookupFailure(error); }
    if (capturedSession !== session) return;
    const slot = state.addressSlots[key];
    if (!slot || slot.callId !== callId) return;
    if (lookupSeq !== capturedSeq) return;
    if (JSON.stringify(addressContext(kind, rowId)) !== JSON.stringify(payload)) return;
    const data = response.ok ? response.data : null;
    state.addressSlots[key] = lookupShapeValid(data)
      ? { phase: 'ready', query: payload.query, callId, result: data }
      : { phase: 'error', query: payload.query, callId,
        message: (response.error || {}).message || 'Tra cứu thất bại.' };
    emit();
  }

  // Xoa ghi chu/ket qua cua mot o (sau khi huy xac nhan too_many).
  function dismissLookupSlot(kind, rowId) {
    delete state.addressSlots[lookupSlotKey(kind, rowId)];
    emit();
  }

  // Bao ket qua cua o da cu (nguoi dung doi du lieu sau khi xac nhan).
  function markLookupStale(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    state.addressSlots[key] = { phase: 'error',
      query: (state.addressSlots[key] || {}).query || '',
      callId: (state.addressSlots[key] || {}).callId || 0,
      message: 'Nội dung đã đổi sau lần Tra trước. Bấm Tra lại.' };
    emit();
  }

  // Mo overlay full sau khi nguoi dung dong y cau hoi too_many: gui ngay
  // yeu cau full DAU TIEN bang dung query da chup tu lan Tra do. Tra ve
  // {ok:false, stale:true} khi slot hoac chu nguon da doi — view bao
  // nguoi dung bam Tra lai, khong mo overlay.
  function openFullFromSlot(kind, rowId) {
    const key = lookupSlotKey(kind, rowId);
    const slot = state.addressSlots[key];
    const current = addressContext(kind, rowId);
    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many' ||
        slot.result.presentation !== 'drafting' ||
        !current || current.query !== slot.query) {
      return { ok: false, stale: true };
    }
    lookupSeq += 1;
    const callId = ++lookupCallId;
    state.addressFull = { slotKey: key, query: slot.query, callId,
      phase: 'loading', result: null, message: null };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    const payload = { query: slot.query, presentation: 'full' };
    (async () => {
      let response;
      try { response = await client.run('notary.address_lookup', payload); }
      catch (error) { response = lookupFailure(error); }
      if (capturedSession !== session) return;
      const full = state.addressFull;
      if (!full || full.callId !== callId) return;
      if (lookupSeq !== capturedSeq) return;
      const data = response.ok ? response.data : null;
      state.addressFull = lookupShapeValid(data)
        ? { slotKey: key, query: full.query, callId, phase: 'ready',
          result: data, message: null }
        : { slotKey: key, query: full.query, callId, phase: 'error',
          result: null,
          message: (response.error || {}).message || 'Tra cứu thất bại.' };
      emit();
    })();
    return { ok: true };
  }

  // Nut Tra trong overlay: gui query dang thay voi presentation full.
  // Sua chu khong tu gui — chi nut nay gui.
  function requestFull(queryText) {
    const full = state.addressFull;
    if (!full) return;
    lookupSeq += 1;
    const callId = ++lookupCallId;
    state.addressFull = { slotKey: full.slotKey, query: queryText, callId,
      phase: 'loading', result: null, message: null };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    const payload = { query: queryText, presentation: 'full' };
    (async () => {
      let response;
      try { response = await client.run('notary.address_lookup', payload); }
      catch (error) { response = lookupFailure(error); }
      if (capturedSession !== session) return;
      const current = state.addressFull;
      if (!current || current.callId !== callId) return;
      if (lookupSeq !== capturedSeq) return;
      const data = response.ok ? response.data : null;
      state.addressFull = lookupShapeValid(data)
        ? { slotKey: current.slotKey, query: queryText, callId,
          phase: 'ready', result: data, message: null }
        : { slotKey: current.slotKey, query: queryText, callId,
          phase: 'error', result: null,
          message: (response.error || {}).message || 'Tra cứu thất bại.' };
      emit();
    })();
  }

  // Dong overlay: huy phien full; response ve muon bi bo (khong mo lai
  // cua so, khong doi focus, khong hien ket qua).
  function closeFull() {
    if (!state.addressFull) return;
    state.addressFull = null;
    lookupSeq += 1;
    emit();
  }

"""
text = text[:start] + new_fns + text[end:]

# --- 4. generation bumps on source edits -------------------------------------
old_touch = """  function touchStage() {
    state.stageDirty = true;
    emit();
  }
"""
new_touch = """  function touchStage() {
    state.stageDirty = true;
    lookupSeq += 1;
    emit();
  }
"""
assert old_touch in text, "touchStage not found"
text = text.replace(old_touch, new_touch, 1)

old_meta_tail = """    const v = value === '' ? null : value;
    if ((state.caseInfo[field] ?? null) === v) return true;
    state.caseInfo[field] = v;
    state.metaDirty = true;
    emit();
    return true;
  }
"""
new_meta_tail = """    const v = value === '' ? null : value;
    if ((state.caseInfo[field] ?? null) === v) return true;
    state.caseInfo[field] = v;
    state.metaDirty = true;
    lookupSeq += 1;
    emit();
    return true;
  }
"""
assert old_meta_tail in text, "updateCaseMeta tail not found"
text = text.replace(old_meta_tail, new_meta_tail, 1)

# --- 5. exports ---------------------------------------------------------------
old_exports = """    state, subscribe,
    addressContext, ensureAddressSuggestion,
"""
new_exports = """    state, subscribe,
    addressContext, requestLookup, dismissLookupSlot, markLookupStale,
    openFullFromSlot, requestFull, closeFull,
"""
assert old_exports in text, "exports not found"
text = text.replace(old_exports, new_exports, 1)

path.write_text(text, encoding="utf-8")
print("model TASK-4 done")
