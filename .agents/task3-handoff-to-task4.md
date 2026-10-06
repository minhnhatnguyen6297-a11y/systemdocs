# TASK-3 handoff → TASK-4 (runtime v2, renderer ngủ đông)

Ngày: 05/10/2026. TASK-3 code xong, test liên quan xanh (xem chứng cứ dưới).

## Lõi v2
- `notary_v2/services/administrative_address.py` viết lại: payload đúng
  `{query, presentation}`; `presentation` null chỉ khi `invalid_input`;
  mọi cụm tách ở `,`/`-` tra độc lập vào xã + tỉnh toàn quốc; giữ tiền tố;
  viết tắt X./P./TT./TP./TP/H./Q./TX.; NFC + casefold; có dấu so có dấu,
  không dấu so bỏ dấu cả hai phía (đ→d); khớp liền cụm đúng thứ tự, riêng
  từng trường (không nối name+raw_phrase); tên khớp → trả mọi observation
  đang hoạt động của đơn vị (mỗi dòng giữ source_text/evidence/
  observation_id riêng); raw khớp → chỉ dòng đó; đơn vị không observation →
  một dòng name-only (source_text null, không observation_id); bỏ trùng duy
  nhất cùng cặp `(unit_id, observation_id)`; xã trước tỉnh sau, thứ tự kho;
  `total` đếm dòng; `too_many` chỉ drafting khi total>10 (results rỗng,
  total giữ số thật); full không giới hạn; cache/khóa/chữ ký/reload_failed
  giữ như cũ.
- Hàm v1 đã xóa: `normalize`, `parse_address`, `predecessor_names`,
  `apply_address`, `_covers`, `name_at`, `province_at`, `descendants`.
  Giữ API công khai `lookup_address(payload)`, `AddressLookup`, `AddressIndex`
  (+ helper `split_query`, `expand_abbreviation`).
- `notary_v2/tests/test_administrative_address.py` viết lại 54 test:
  fixture synthetic (đa observation cùng unit, name-only, 11 unit trùng token
  với 12 dòng) + kho thật; pytest 53 passed 1 skipped (thiếu jsonschema,
  validator examples vẫn chạy).
- Adapter `shell/sidecar/notary_adapter.py` KHÔNG đổi (pass-through đã đủ;
  mock delegate theo).

## Renderer ngủ đông (entrypoint cho TASK-4)
- `case-drafting-model.js`: `addressContext(kind,rowId)` → `{query,
  presentation:'drafting'}` hoặc null (nguồn tạm như cũ: issuer←noi_cap,
  còn lại←dia_chi; TASK-4 đổi issuer→dia_chi người chết, posting→ô niêm yết).
  `ensureAddressSuggestion(kind,rowId)` async gọi trực tiếp
  `client.run('notary.address_lookup', payload)`, kiểm shape v2
  (`schema_version/total/results`), session guard + so sánh query hiện tại
  để bỏ phản hồi cũ; KHÔNG debounce, KHÔNG gate ngày/UBND, KHÔNG ghi
  Stage/ô, KHÔNG nối chuỗi. Đã XÓA `applyAddressSuggestion`,
  `ignoreAddressSuggestion`, `addressTimers/addressRequests`.
  Export: `addressContext, ensureAddressSuggestion` (bỏ apply/ignore).
- `case-drafting-view.js`: `addressSuggestionEl` chỉ dựng khung rỗng giữ id
  (không gọi lookup); `postingSuggestionEl` dựng khung rỗng (không chọn tài
  sản); `refreshAddressBoxes` no-op. Không nút Tra/Áp dụng/Bỏ qua (TASK-4).
- Test: `shell/test/notary-address-lookup.test.mjs` 6 test (v2 payload,
  không tự tra, không sửa dữ liệu, bỏ phản hồi cũ, lỗi shape); view test TASK-3
  1 test + giữ test issuer input. `test_notary_mock_adapter.py` chuyển v2.

## Schema/docs
- XÓA `contracts/notary-case-drafting/address-lookup.schema.json` (v1).
  Tham chiếu v1 còn lại duy nhất là dòng changelog lịch sử NAIA-9 trong
  `contracts/notary-case-drafting.md:1028` (giữ làm lịch sử).
- `docs/spec/shared/administrative-lookup.md` §12 → đã đáp ứng (TASK-3);
  contract §14 + changelog đồng bộ.

## Chứng cứ chạy
- `pytest notary_v2/tests/test_administrative_address.py
  shell/test/test_notary_mock_adapter.py`: 207 passed, 3 skipped.
- `node --test test/notary-address-lookup.test.mjs
  test/notary-case-drafting-view.test.mjs` (từ shell/): 62 pass.
- `python contracts/notary-case-drafting/validate_examples.py`: 82 files,
  0 unexpected outcomes.
- `npm test` đầy đủ: RỚT tại `notary-docx-intake.test.mjs` (file không thuộc
  phạm vi, không sửa; lỗi exec python xử lý docx — tồn tại trước TASK-3).
- `git diff --check`: không lỗi whitespace (chỉ cảnh báo CRLF có sẵn).

## Chưa kiểm (cho TASK-4 / review)
- GUI thật trong Electron (không có môi trường hiển thị ở đây).
- Test `test_schema_v2_shapes` và staging-powershell bị skip nếu thiếu
  jsonschema/pwsh (ở máy này jsonschema thiếu → skip; validate_examples bù).
