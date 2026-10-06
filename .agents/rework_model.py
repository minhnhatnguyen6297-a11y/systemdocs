# -*- coding: utf-8 -*-
"""Rework model: targeted gen bumps, slot gen capture, stale-slot cleanup."""
from pathlib import Path

path = Path("shell/src/renderer/notary/case-drafting-model.js")
text = path.read_text(encoding="utf-8")

# 1. touchStage no longer bumps: only address-source edits bump the gen.
old = """  function touchStage() {
    state.stageDirty = true;
    lookupSeq += 1;
    emit();
  }
"""
new = """  function touchStage() {
    state.stageDirty = true;
    emit();
  }

  // Dau thay doi cho tra cuu: chi dia chi/noi cap/noi niem yet, them/xoa
  // dong Nguoi/Tai san, doi case. Sua ho ten/ngay thang/sap xep khong lam
  // request dang bay het hieu luc.
  function noteLookupSourceChanged() {
    lookupSeq += 1;
  }
"""
assert old in text, "touchStage not found"
text = text.replace(old, new, 1)

# 2. add/remove rows bump.
for fn, anchor in (
    ("addPerson", "    const row = newPersonRow(uuid, fields);\n    state.stage.people.push(row);\n    touchStage();"),
    ("addAsset", "    const row = newAssetRow(uuid, fields);\n    state.stage.assets.push(row);\n    touchStage();"),
):
    assert anchor in text, fn + " anchor not found"
    text = text.replace(anchor, anchor.replace("    touchStage();", "    noteLookupSourceChanged();\n    touchStage();"), 1)

old_rm = """    if (state.stage.people.length + state.stage.assets.length === before) {
      return;
    }
"""
new_rm = """    if (state.stage.people.length + state.stage.assets.length === before) {
      return;
    }
    noteLookupSourceChanged();
"""
assert old_rm in text, "removeStageRow anchor not found"
text = text.replace(old_rm, new_rm, 1)

# 3. field edits bump only for address sources.
old_pf = """    row[field] = value === '' ? null : value;
    clearRowFieldError(rowId, field);
    touchStage();
  }

  function updateAssetField(rowId, field, value) {
"""
new_pf = """    row[field] = value === '' ? null : value;
    clearRowFieldError(rowId, field);
    if (field === 'dia_chi' || field === 'noi_cap') noteLookupSourceChanged();
    touchStage();
  }

  function updateAssetField(rowId, field, value) {
"""
assert old_pf in text, "updatePersonField anchor not found"
text = text.replace(old_pf, new_pf, 1)

old_af = """    clearRowFieldError(rowId, field);
    touchStage();
  }

  // Doi thu tu asset = doi nghia vi tri (contract"""
new_af = """    clearRowFieldError(rowId, field);
    if (field === 'dia_chi') noteLookupSourceChanged();
    touchStage();
  }

  // Doi thu tu asset = doi nghia vi tri (contract"""
assert old_af in text, "updateAssetField anchor not found"
text = text.replace(old_af, new_af, 1)

# 4. updateCaseMeta: only noi_niem_yet bumps (v2 has no dates).
old_mt = """    const v = value === '' ? null : value;
    if ((state.caseInfo[field] ?? null) === v) return true;
    state.caseInfo[field] = v;
    state.metaDirty = true;
    lookupSeq += 1;
    emit();
    return true;
  }
"""
new_mt = """    const v = value === '' ? null : value;
    if ((state.caseInfo[field] ?? null) === v) return true;
    state.caseInfo[field] = v;
    state.metaDirty = true;
    if (field === 'noi_niem_yet') noteLookupSourceChanged();
    emit();
    return true;
  }
"""
assert old_mt in text, "updateCaseMeta tail not found"
text = text.replace(old_mt, new_mt, 1)

old_ct = """      state.metaDirty = true;
      state.stageDirty = true;
      lookupSeq += 1;
      emit();
      return true;
    }
"""
new_ct = """      state.metaDirty = true;
      state.stageDirty = true;
      noteLookupSourceChanged();
      emit();
      return true;
    }
"""
assert old_ct in text, "case_type branch not found"
text = text.replace(old_ct, new_ct, 1)

# 5. requestLookup: capture gen in slot; stale cleanup when this call is
#    still the latest (no newer request owns the slot).
old_req = """    state.addressSlots[key] = { phase: 'loading', query: payload.query,
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
"""
new_req = """    state.addressSlots[key] = { phase: 'loading', query: payload.query,
      callId, gen: lookupSeq };
    emit();
    const capturedSession = session;
    const capturedSeq = lookupSeq;
    let response;
    try { response = await client.run('notary.address_lookup', payload); }
    catch (error) { response = lookupFailure(error); }
    if (capturedSession !== session) return;
    const slot = state.addressSlots[key];
    if (!slot || slot.callId !== callId) return;
    if (lookupSeq !== capturedSeq ||
        JSON.stringify(addressContext(kind, rowId)) !== JSON.stringify(payload)) {
      // Nguon doi khi request dang bay ma chua co lan Tra moi hon: don
      // loading treo, bao nguoi dung bam Tra lai thay vi treo mai.
      state.addressSlots[key] = { phase: 'error', query: payload.query,
        callId, gen: capturedSeq,
        message: 'Nội dung đã đổi sau khi bấm Tra. Bấm Tra lại.' };
      emit();
      return;
    }
    const data = response.ok ? response.data : null;
    state.addressSlots[key] = lookupShapeValid(data)
      ? { phase: 'ready', query: payload.query, callId, gen: capturedSeq,
        result: data }
      : { phase: 'error', query: payload.query, callId, gen: capturedSeq,
        message: (response.error || {}).message || 'Tra cứu thất bại.' };
    emit();
  }
"""
assert old_req in text, "requestLookup not found"
text = text.replace(old_req, new_req, 1)

# 6. openFullFromSlot: also require the captured gen to still be current
#    (catches A -> B -> A where the text is back but the gen moved).
old_open = """    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many' ||
        slot.result.presentation !== 'drafting' ||
        !current || current.query !== slot.query) {
      return { ok: false, stale: true };
    }
"""
new_open = """    if (!slot || slot.phase !== 'ready' || !slot.result ||
        slot.result.status !== 'too_many' ||
        slot.result.presentation !== 'drafting' ||
        !current || current.query !== slot.query ||
        slot.gen !== lookupSeq) {
      return { ok: false, stale: true };
    }
"""
assert old_open in text, "openFullFromSlot guard not found"
text = text.replace(old_open, new_open, 1)

path.write_text(text, encoding="utf-8")
print("model rework done")
