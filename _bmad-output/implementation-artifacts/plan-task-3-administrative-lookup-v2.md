---
title: 'TASK-3: Lõi tra cứu hành chính theo spec + contract v2'
type: 'feature'
ticket: ''
created: '2026-10-05'
status: 'superseded'
superseded_by: '.agents/plans/task-3-administrative-lookup-v2.md'
route: 'full'
route_source: 'auto'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: ['docs/spec/shared/administrative-lookup.md', 'contracts/notary-case-drafting.md']
---

<frozen-after-approval reason="Owner duyệt spec + contract v2 05/10/2026">

> **Lịch sử, không dùng để giao worker.** Owner yêu cầu hoàn thiện lại spec
> và plan TASK-3/TASK-4 ngày 05/10/2026. Plan tiếp nối tại
> [`.agents/plans/task-3-administrative-lookup-v2.md`](../../.agents/plans/task-3-administrative-lookup-v2.md).
> Spec hiện hành ưu tiên: nhận diện dấu trước mở rộng viết tắt; cách xử lý
> nhiều observation cùng đơn vị/bản kho đã chốt: trả riêng các dòng khớp để
> người dùng chọn. Các đề xuất nối
> `raw_phrase` hoặc chọn nguồn trong nội dung lịch sử bên dưới chưa là luật
> đã duyệt. Không triển khai trực tiếp từ trạng thái `ready-for-dev` cũ.

## Intent

**Problem:** Runtime `notary.address_lookup` còn v1: bắt `source_date`/`target_date`, tách xã+tỉnh, bỏ tiền tố khi so, đoán cấp theo mốc ngày, tách `raw_phrase` bằng regex, nối `(nay là …)`, trả `match|ambiguous` + `coverage` — toàn bộ trái spec + contract v2 Owner đã duyệt (TASK-2). Đường lịch sử (events confirmed) là dead code: kho thật không có event confirmed nào.

**Approach:** Viết lại `notary_v2/services/administrative_address.py` thành lõi theo spec: tách cụm `,`/`-`, mở rộng viết tắt bằng danh mục cố định, giữ tiền tố, khớp liền cụm trên `tên + raw_phrase`. **Mọi cụm tra độc lập** vào cả xã lẫn tỉnh (Owner đổi mục 7 sau khi quan sát Bando: không phải→trái, không scope tỉnh, không bỏ qua cụm huyện, tỉnh luôn in dòng riêng). Trả v2 `found|not_found|too_many|invalid_input|reload_failed` với `display` theo `presentation`. Renderer **ngủ đông**: nối dây v2 nhưng tắt đường gọi tự động và bỏ `(nay là …)` — tính năng tra trong màn soạn tạm tắt tới TASK-4 (nút Tra/popup/overlay). Viết lại test; xóa schema v1.

## Boundaries & Constraints

**Always:**
- Spec `docs/spec/shared/administrative-lookup.md` là SOT; không suy diễn luật ngoài spec (không strip `ubnd`/`(nay là…)`, không thêm dấu ngăn ngoài `,` `-`, không quy đổi số).
- Chỉ đọc ledger cục bộ, read-only, không ghi DB, không gọi mạng.
- Mọi kết quả cùng một `dataset_version`/`revision` của bản đã nạp; reload lỗi → `reload_failed`, không trả kết quả cũ dưới nhãn mới.
- Giữ pattern cache `AddressLookup` (chữ ký path+mtime+size, lock, TOCTOU) và `read_ledger`/`validate` của `administrative_timeline.py`.

**Never:**
- Không nút Tra, popup xác nhận, tool overlay — TASK-4. Renderer chỉ ngủ đông: tắt tự tra (debounce), bỏ tự nối `(nay là …)`; không giữ auto-lookup nào chạy sai spec.
- Không tra huyện/thôn; không tách `raw_phrase` thành trường xã cũ; không sửa `administrative_timeline.py` hay ledger data.
- Không sửa mock adapter (`address_lookup` delegate sang real, tự theo v2).
- Không push, không commit ngoài phạm vi task.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error |
|---|---|---|---|
| Ca chuẩn | `xã Yên Bình, huyện Ý Yên, tỉnh Nam Định`, drafting | cụm độc lập: mọi Xã Yên Bình toàn quốc + xã khớp `(huyện Ý Yên)` + xã khớp `nam định` (nếu có) + dòng `tỉnh Ninh Bình`; `display: xã …, tỉnh …` | — |
| Chỉ tỉnh | `tỉnh Nam Định` | found kết quả level=province (`tỉnh Ninh Bình`) | — |
| Nhiều tỉnh | cụm khớp ≥2 tỉnh (vd `Hà`) | mỗi tỉnh một dòng riêng | — |
| Không tiền tố | `Yên Bình` | mọi commune chứa `yên bình` (xã+phường+`Yên Bình Đông`…); >10 → too_many | — |
| Không dấu/hoa | `yen binh`, `xã YÊn Bình` | khớp bỏ dấu (cả `Yến Bình`)/không phân biệt hoa | — |
| NFD input | input encode NFD | chuẩn hóa NFC trước khi so — khớp như NFC | — |
| `d`/`đ` | `dien bien` (không dấu) vs `Điện Biên` | khớp (đ→d phía DB chỉ khi input hoàn toàn không dấu) | — |
| Không liền cụm | `yên bình` vs `Bình Yên`, `Yên Thịnh Bình` | không khớp | — |
| Viết tắt | `P. Yên Bình` | `P.`→`Phường`, chỉ khớp dòng phường | — |
| Huyện trực tiếp | `huyện Ý Yên` | found: mọi xã có `(huyện Ý Yên)` trong raw_phrase | — |
| Quận trực tiếp | `quận Hà Đông` | found: Phường Hà Đông, Kiến Hưng… (giống Bando) | — |
| Cụm rác | `Thôn A, xã Yên Bình, tỉnh Nam Định` | `Thôn A` không khớp → vẫn found nhờ cụm xã + tỉnh | — |
| Ghi chú ngoặc | `phường Đại Mỗ` | khớp cả raw_phrase chứa `(…sáp nhập vào phường Đại Mỗ)` — rủi ro đã chấp nhận | — |
| Tên có `-` | `Bà Rịa - Vũng Tàu` | 2 cụm đều khớp cùng tỉnh → dedupe một dòng tỉnh (+ commune nếu `bà rịa` khớp) | — |
| Trùng tên | hai xã cùng tên khác tỉnh | hai dòng, không auto-chọn | — |
| Quá 10 | drafting total>10 | `too_many`, `results:[]`, `total`=số thật (gồm cả dòng tỉnh); cùng query `full` → `found` đủ dòng | — |
| Độ dài | `query` length 1 ok; 4000 ok; 4001 | 4001 → `invalid_input` | — |
| Sai input | key lạ (`source_date`), `presentation` lạ, `query` rỗng/không phải chuỗi | `invalid_input`, `total:0`, `results:[]`, `presentation:null` | job vẫn succeeded |
| Kho lỗi | ledger hỏng/snapshot thiếu | `reload_failed`, `total:0`, `results:[]`, giữ version/revision bản tốt cuối | — |

</frozen-after-approval>

## Code Map

- `notary_v2/services/administrative_address.py` — viết lại lõi. Giữ: `AddressLookup` cache/lock/signature (L269-324), `lookup_address` entry (L327-331), helper NFC/casefold/bỏ dấu trong `normalize` (L28-33, bỏ phần strip tiền tố + `ubnd`). Bỏ: `parse_address`/`predecessor_names`/`apply_address`/`AddressIndex` lịch sử/SUFFIX/`_covers`.
- `notary_v2/administrative_timeline.py` — chỉ đọc: `DEFAULT_FOLDER`, `read_ledger`, `validate`, `empty_ledger`, `LedgerError`; collections `units/names/parents/observations` (names/parents `status:"observed"`, observation `raw_phrase` + `dataset_version`, `id` = `observation:<ver16>:<uid>`).
- `notary_v2/data/administrative_units/ledger.json` — 34 province + 3321 commune, `district:0`; raw_phrase nguyên văn Bando.
- `shell/sidecar/notary_adapter.py:93-96` — `address_lookup(job, payload)` → `lookup_address(payload)`; không đổi.
- `shell/src/renderer/notary/case-drafting-model.js:217-333` — ngủ đông: `addressContext` gửi `{query, presentation:'drafting'}`; check `schema_version==='notary.address-lookup.v2'` (L292); `applyAddressSuggestion` trả `result.display` để copy (bỏ gate `candidate.historical`, bỏ nối `(nay là …)`); **gỡ mọi điểm gọi tự động** (debounce/blur/change → `ensureAddressSuggestion`) — tính năng tạm tắt tới TASK-4. Mapping v1→v2 renderer đọc: `candidate.address`→`result.display`; `candidate.commune`/`candidate.province`→`result.name`/`result.province`; `candidate.historical`→bỏ; `result.coverage`/`candidate.partial`→bỏ.
- `shell/src/renderer/notary/case-drafting-view.js:733-795` — `addressSuggestionEl`/`postingSuggestionEl` đọc `results[].display`/`status` thay `candidates`/`coverage`.
- `contracts/notary-case-drafting/address-lookup.v2.schema.json` — schema đích (đã có). `address-lookup.schema.json` v1 — xóa.
- `contracts/notary-case-drafting.md` §14 (L1641-1644, changelog L1029) — cập nhật câu "runtime còn v1".
- `notary_v2/tests/test_administrative_address.py` — viết lại toàn bộ cho v2 (giữ pattern fixture synthetic + real-ledger + cache + staging).
- `shell/test/notary-address-lookup.test.mjs`, `shell/test/notary-case-drafting-view.test.mjs:1467-1512`, `shell/test/test_notary_mock_adapter.py:235-257` — stub/assert v2.

## Tasks & Acceptance

**Execution:**
- [ ] `notary_v2/services/administrative_address.py` -- viết lại engine v2 theo spec §5-8 -- lõi tra cứu
- [ ] `notary_v2/tests/test_administrative_address.py` -- viết lại test: mọi hàng I/O matrix + cache reload + staging isolation + validate theo schema v2 -- chứng minh đúng luật
- [ ] `shell/src/renderer/notary/case-drafting-model.js` + `case-drafting-view.js` -- ngủ đông: payload/result v2, gỡ trigger tự động, bỏ `(nay là …)` -- không vi phạm spec; UX mới = TASK-4
- [ ] `shell/test/notary-address-lookup.test.mjs`, `notary-case-drafting-view.test.mjs`, `test_notary_mock_adapter.py` -- stub/assert v2 -- test xanh
- [ ] `contracts/notary-case-drafting/address-lookup.schema.json` -- xóa; sửa tham chiếu (§14 L1642-44, test schema) -- AC#7
- [ ] `docs/spec/shared/administrative-lookup.md` §12 -- gỡ link schema v1 (ghi chú lịch sử trỏ v2); quét `docs/spec` còn tham chiếu v1 -- link không hỏng
- [ ] `contracts/notary-case-drafting.md` -- §14 + changelog: runtime nay trả v2 -- doc khớp hiện trạng

**Acceptance Criteria:**
- Given payload `{query, presentation}` hợp lệ, when `notary.address_lookup` chạy, then trả `notary.address-lookup.v2` đúng 5 status và shape §14.
- Given mọi hàng I/O matrix, when engine chạy trên synthetic + real ledger, then kết quả khớp cột Expected.
- Given ledger mtime đổi, when lookup kế, then index nạp lại đúng version mới; kho hỏng → `reload_failed` giữ version cuối.
- Given `pytest notary_v2`, `pytest shell/test`, `cd shell && npm test`, `python contracts/notary-case-drafting/validate_examples.py`, then tất cả xanh; không còn `notary.address-lookup.v1` trong code/test/schema.

## Implementation Notes

## Plan Change Log

## Review Triage Log

Codex review (orca run_a4b4870f70d1, `.agents/task3-plan-review-codex.md`) — verdict APPROVE_WITH_FIXES, 9 findings; xử lý 05/10:

- #1 [high] renderer giữ auto-lookup/`(nay là …)` tới TASK-4 → **Owner chọn A: ngủ đông** (tắt trigger, bỏ nối; đã sửa Boundaries/Code Map/Tasks).
- #2 [high] cụm cuối `quận Hà Đông` khớp raw_phrase tỉnh → **không còn là vấn đề**: Owner đổi luật — cụm huyện tra như cụm thường vào xã lẫn tỉnh, khớp gì in nấy (spec §7, decision-19). Đã kiểm ledger thật: 0 province raw_phrase chứa từ huyện.
- #3 test `Bà Rịa - Vũng Tàu` → đã thêm hàng matrix "Tên có `-`".
- #4 định nghĩa chuẩn hóa → Design Notes bước 2-3 (NFC; có dấu so có dấu; không dấu → bỏ dấu + đ→d); test NFD + d/đ đã thêm.
- #5 biên độ dài query 1/4000/4001 + shape `invalid_input` đầy đủ → đã thêm hàng "Độ dài" (schema: minLength 1, maxLength 4000).
- #6 mapping field renderer v1→v2 → đã liệt kê trong Code Map `case-drafting-model.js`.
- #7 dedupe `unit_id`, thứ tự ổn định theo kho, observation theo `dataset_version` đang nạp, nối nhiều raw_phrase bằng `, ` → Design Notes bước 3,5,6; fixture nhiều observation trong test.
- #8 xóa v1 schema làm hỏng link trong spec §12 → task mới: sửa §12 thành ghi chú lịch sử; quét tham chiếu mở rộng sang `docs/spec` (Verification).
- #9 test bổ sung: đủ danh mục viết tắt, cụm khớp nhiều tỉnh, `full` >10 không bị chặn, display cấp tỉnh cả 2 kiểu, khớp ghi chú trong ngoặc → hàng "Nhiều tỉnh", "Ghi chú ngoặc", "Quá 10" (full đủ dòng), "Chỉ tỉnh" (cả hai presentation trong test).

## Design Notes

Thuật toán khớp (spec §5-7, mọi cụm độc lập — Owner đổi 05/10 theo hành vi Bando):
1. Tách `query` theo `,` `-` → clauses (bỏ rỗng, collapse space).
2. Mỗi clause: mở rộng viết tắt đầu cụm (`X.|P.|TT.|TP.|TP|H.|Q.|TX.`→tiền tố đầy đủ); chuẩn hóa NFC+casefold; clause hoàn toàn không dấu → flag unaccented.
3. Text phía DB (tên unit + raw_phrase của các observation thuộc `dataset_version` đang nạp, nối bằng `, `) chuẩn hóa cùng cách; clause unaccented → so trên text đã bỏ dấu (đ→d). Input có dấu → so có dấu nguyên trạng.
4. Khớp = `clause_norm in text_norm` (liền cụm, đúng thứ tự).
5. Mọi clause so vào commune toàn quốc → union; và province → union. Không scope, không skip theo tiền tố.
6. Dedupe theo `unit_id`. Thứ tự hiển thị: commune trước, province sau; trong mỗi nhóm theo thứ tự dòng kho (ổn định).
7. Kết quả = commune ∪ province. 0 → `not_found`. `total` = commune + province.
8. `display`: drafting lowercase danh từ đầu (`Xã`→`xã`, `Tỉnh`→`tỉnh`…): `xã Ý Yên, tỉnh Ninh Bình`; province: `tỉnh Ninh Bình`. full: `Xã Ý Yên = <raw_phrase>, Tỉnh Ninh Bình`; không raw_phrase → bỏ ` = …`; province: `Tỉnh Ninh Bình = <raw_phrase>`. drafting total>10 → `too_many` + `results:[]`.

Ghi chú rủi ro đã chấp nhận (Codex #2, Owner trả lời): cụm tiền tố huyện không bị chắn — `quận Hà Đông` tra như cụm thường, khớp raw_phrase xã → in các xã (đúng ý Bando). Nếu raw_phrase cấp tỉnh sau này chứa tên huyện thì cũng in tỉnh đó — hành vi phản ánh kho, không phải lỗi.

## Verification

**Commands:**
- `uv run pytest notary_v2/tests/test_administrative_address.py -x -q` — expected: all pass
- `uv run pytest shell/test/test_notary_mock_adapter.py -x -q` — expected: all pass
- `cd shell && npm test` — expected: 0 fail
- `uv run python contracts/notary-case-drafting/validate_examples.py` — expected: 0 unexpected outcomes
- `grep -rn "address-lookup.v1\|address-lookup.schema.json" notary_v2 shell contracts tools docs/spec` — expected: chỉ còn trong lịch sử doc/handoff `.agents`, không trong code/test/schema/spec còn dùng
