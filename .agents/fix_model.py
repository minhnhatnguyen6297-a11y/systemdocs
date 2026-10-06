# -*- coding: utf-8 -*-
"""One-off: replace v1 auto-lookup block in case-drafting-model.js with v2 dormant helper."""
from pathlib import Path

path = Path("shell/src/renderer/notary/case-drafting-model.js")
text = path.read_text(encoding="utf-8")

old_gate = (
    "    // Gate UBND phai bo dau giong normalize() phia service \u2014 \"uy ban\n"
    "    // nhan dan\" khong dau van la dia chi co quan hop le.\n"
    "    const addrAscii = (payload.address || '').normalize('NFD')\n"
    "      .replace(/[\\u0300-\\u036f]/g, '').replace(/\u0111/g, 'd').replace(/\u0110/g, 'D');\n"
    "    if (kind === 'issuer' && !/^(?:ubnd|uy ban nhan dan)\\s/i.test(addrAscii)) {\n"
    "      state.addressSuggestions[key] = { message: 'Nh\u1eadp \u0111\u00fang \u0111\u1ecba ch\u1ec9 UBND tr\u00ean gi\u1ea5y khai t\u1eed; kh\u00f4ng l\u1ea5y \u0111\u1ecba ch\u1ec9 c\u01b0 tr\u00fa.' };\n"
    "      return;\n"
    "    }\n"
    "    if (!payload.address || !/^\\d{4}-\\d{2}-\\d{2}$/.test(payload.source_date) || !/^\\d{4}-\\d{2}-\\d{2}$/.test(payload.target_date)) {\n"
    "      state.addressSuggestions[key] = { message: 'C\u1ea7n \u0111\u1ecba ch\u1ec9, ng\u00e0y c\u1ea5p \u0111\u1ea7y \u0111\u1ee7 v\u00e0 ng\u00e0y l\u1eadp h\u1ed3 s\u01a1 (ng\u00e0y c\u1ea5p cho khai t\u1eed).' };\n"
    "      return;\n"
    "    }\n"
)
assert old_gate in text, "gate block not found"

old_tail = (
    "    state.addressSuggestions[key] = { loading: true };\n"
    "    const capturedSession = session;\n"
    "    addressTimers.set(key, setTimeout(async () => {\n"
    "      let response;\n"
    "      try { response = await client.run('notary.address_lookup', payload); }\n"
    "      catch (error) { response = { ok: false, error: { message: 'Kh\u00f4ng \u0111\u1ecdc \u0111\u01b0\u1ee3c b\u1ea3ng \u0111\u1ecba ch\u1ec9 c\u1ee5c b\u1ed9.' } }; }\n"
    "      if (capturedSession !== session || addressRequests.get(key) !== identity ||\n"
    "          JSON.stringify(addressContext(kind, rowId)) !== JSON.stringify(payload)) return;\n"
    "      // User da bam \"Bo qua\" trong luc response dang bay \u2014 ignored thang.\n"
    "      if (state.addressSuggestions[key] && state.addressSuggestions[key].ignored) return;\n"
    "      // Kiem shape truoc khi tin \u2014 du lieu thieu schema_version/fields ma ap\n"
    "      // vao dia chi se ghi \"undefined, undefined\" vao ho so.\n"
    "      const data = response.ok ? response.data : null;\n"
    "      const valid = !!data && data.schema_version === 'notary.address-lookup.v1' &&\n"
    "        typeof data.status === 'string' && Array.isArray(data.candidates);\n"
    "      state.addressSuggestions[key] = valid ? { result: data, identity }\n"
    "        : { message: (response.error || {}).message || 'Tra c\u1ee9u th\u1ea5t b\u1ea1i.' };\n"
    "      emit();\n"
    "    }, deps.addressDebounceMs ?? 350));\n"
    "  }\n"
)
assert old_tail in text, "timer tail not found"

new_body = (
    "    state.addressSuggestions[key] = { loading: true };\n"
    "    const capturedSession = session;\n"
    "    let response;\n"
    "    try { response = await client.run('notary.address_lookup', payload); }\n"
    "    catch (error) { response = { ok: false, error: { message: 'Kh\u00f4ng \u0111\u1ecdc \u0111\u01b0\u1ee3c b\u1ea3ng \u0111\u1ecba ch\u1ec9 c\u1ee5c b\u1ed9.' } }; }\n"
    "    if (capturedSession !== session) return;\n"
    "    if (JSON.stringify(addressContext(kind, rowId)) !== JSON.stringify(payload)) return;\n"
    "    const data = response.ok ? response.data : null;\n"
    "    const valid = !!data && data.schema_version === 'notary.address-lookup.v2' &&\n"
    "      typeof data.status === 'string' && Array.isArray(data.results) &&\n"
    "      typeof data.total === 'number';\n"
    "    state.addressSuggestions[key] = valid ? { result: data }\n"
    "      : { message: (response.error || {}).message || 'Tra c\u1ee9u th\u1ea5t b\u1ea1i.' };\n"
    "    emit();\n"
    "  }\n"
)

text = text.replace(old_gate, "", 1)
text = text.replace(old_tail, new_body, 1)

old_head = "  function ensureAddressSuggestion(kind, rowId) {\n"
assert old_head in text
text = text.replace(
    old_head,
    "  // Chi goi truc tiep (nut Tra o TASK-4). Khong debounce, khong gate\n"
    "  // ngay/UBND, khong tu ghi Stage/o, khong noi \"(nay la ...)\".\n"
    "  async function ensureAddressSuggestion(kind, rowId) {\n",
    1,
)

path.write_text(text, encoding="utf-8")
print("model helper replaced")
