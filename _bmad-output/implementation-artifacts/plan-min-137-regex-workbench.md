---
title: 'MIN-137 Regex Workbench — hardening round 2 (real timeout, provenance fidelity, baseline check)'
type: 'feature'
ticket: 'MIN-137'
created: '2026-10-01'
status: 'in-review'
route: 'full'
route_source: 'auto'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Vòng 1 (commit f48a762) dùng ThreadPoolExecutor làm "timeout" — nhưng
`Future.cancel()`/`shutdown(cancel_futures=True)` không ngắt được match `re` đang
chạy; lint `_NESTED_QUANTIFIER` cũng không bao phủ mọi pattern backtracking. Lỗi
timeout trong `extract_parties` bị nuốt (trả về như không có dữ liệu). Span chưa
kiểm chứng trên input NFD/ký tự ngoài BMP; UI JS dùng UTF-16 index nên lệch với
span code-point của Python. Chưa đối chiếu đúng 20 thư mục baseline.

**Approach:** Chuyển toàn bộ regex do profile điều khiển sang engine `regex`
(có `timeout=` ngắt thật, raise `TimeoutError`), truyền lỗi timeout đúng nghĩa,
sửa pipeline span để trỏ về đúng văn bản nguồn gốc, UI highlight theo code point,
và chạy đối chiếu trên đúng 20 thư mục baseline (báo cáo chỉ tổng hợp, không PII).

## Boundaries & Constraints

**Always:**
- Chỉ sửa trong `tools/regex_workbench/` + record `.agent/tasks/MIN-137/` + plan file này.
- Mọi regex từ profile (zones, kind_rules, fields, parties, validators) đều qua
  cơ chế timeout thật; lỗi kèm `rule_id` và state `error`, không nuốt.
- Span `[start,end]` cắt đúng `raw_snippet` trên văn bản nguồn người dùng nhập
  (kể cả input NFD, ký tự ngoài BMP); JS highlight dùng code-point index.
- Test timeout chạy trong tiến trình con có giới hạn cứng — suite không thể treo.
- Báo cáo baseline: chỉ số tổng hợp (đọc được/bỏ qua, phân bố state/kind),
  không raw text/tên người thật; nêu rõ giới hạn ground truth.
- Giữ nguyên AC1–AC6 đã công bố trong comment điều phối của Leader.

**Never:**
- Không tạo bản triển khai mới, không đổi nhánh/scope ngoài `tools/regex_workbench/`.
- Không dùng ThreadPoolExecutor "timeout" giả; không giải quyết bằng lint tĩnh.
- Không commit dữ liệu khách thật (manifest đường dẫn, snippet, tên, số liệu cá nhân).
- Không coi bộ mẫu giả lập là đã kiểm chứng đủ 20 thư mục; không coi 227 thư mục
  cùng tập mẫu baseline.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| ReDoS field rule | `(a|a)*b` qua lint, chạy trên scope tốn thời gian | field `state=error`, `errors[]` chứa `rule_id` | `TimeoutError` → error state |
| ReDoS trong parties | side_marker/person_delimiter/person_field quá hạn | `parties.state=error` hoặc field con `error`, có rule_id | Không trả `missing` giả |
| Hồi phục sau timeout | run() lại với profile sạch | kết quả bình thường, không kẹt state | — |
| Input NFD | văn bản combining marks | span cắt đúng đoạn trong input gốc | — |
| Ký tự ngoài BMP | emoji/char >U+FFFF trước field | JSON span đúng code point; JS highlight đúng | — |
| Regex hỏng cú pháp | pattern invalid | `error` state + lint report | compile error |

</frozen-after-approval>

## Code Map

- `tools/regex_workbench/engine/extractor.py` — `_guarded_finditer` hiện dùng
  ThreadPoolExecutor (dòng ~45-64): thay bằng `regex` module `timeout=`;
  `extract_parties` dòng ~257 nuốt lỗi timeout; validators/person_delimiter/
  person_fields cũng phải guard.
- `tools/regex_workbench/engine/zoner.py` — `detect_title`/`find_zones` dùng
  `re.search` trần cho kind_rules + start/end_markers: phải qua guard timeout.
- `tools/regex_workbench/engine/textnorm.py` — thêm `normalize_with_index_map`
  (replacements có map, không NFC tổng thể) + `map_span` nâng cấp: fold→s1→raw,
  mở rộng end qua combining mark để span phủ đủ cluster NFD.
- `tools/regex_workbench/engine/runner.py` — `run()` đọc `regex_timeout_ms` một
  lần, truyền xuống mọi tầng; gom `errors` từ zoning+fields+parties.
- `tools/regex_workbench/serve.py` — API giữ nguyên; result JSON không đổi shape.
- `tools/regex_workbench/ui/app.js` — `renderHighlight` slice theo code point
  (`Array.from`), spans từ engine vẫn là code-point index của input người dùng.
- `tools/regex_workbench/tests/` — thêm `_timeout_probe.py` (subprocess probe)
  + case mới trong `test_workbench.py`.
- `tools/regex_workbench/baseline_eval.py` — script đối chiếu baseline: đọc
  `results.json` của artifacts g1-transfer-20, chạy engine, xuất CHỈ tổng hợp.
- `tools/regex_workbench/requirements.txt` — thêm `regex`.

## Tasks & Acceptance

**Execution:**
- [ ] `engine/textnorm.py` -- normalize map 2 tầng + span→raw -- provenance đúng nguồn
- [ ] `engine/extractor.py` -- regex engine timeout + truyền lỗi parties -- yêu cầu Leader
- [ ] `engine/zoner.py` -- guard timeout cho kind_rules/zone markers + errors
- [ ] `engine/runner.py` -- plumbing timeout_ms + errors hợp nhất
- [ ] `ui/app.js` -- code-point slicing -- non-BMP alignment
- [ ] `tests/` + `tests/_timeout_probe.py` -- timeout/subprocess + NFD/BMP tests
- [ ] `baseline_eval.py` + `requirements.txt` + `README.md` -- baseline 20 folder + dep
- [ ] `.agent/tasks/MIN-137/handoff.md` -- cập nhật record

**Acceptance Criteria:**
- Given pattern backtracking nặng (lint không bắt được), when run, then bị ngắt
  thật, field/parties báo `error` kèm `rule_id`, và run hợp lệ kế tiếp thành công.
- Given input NFD hoặc chứa ký tự ngoài BMP, when extract, then mọi `span` cắt
  đúng `raw_snippet` trên text gốc và highlight UI tô đúng vùng.
- Given timeout trong zone/kind rule, when run, then `errors[]` ghi lỗi kèm
  rule_id thay vì im lặng.
- Given 20 thư mục baseline, when chạy đối chiếu, then báo số đọc được/bỏ qua,
  phân bố kết quả, ghi rõ giới hạn ground truth — không PII.

## Implementation Notes

- `regex` module hóa ra chống shortcut rất mạnh (required-literal analysis) —
  pattern test phải là `(a|a)*b` trên `a*60+'cb'` mới thật sự TimeoutError;
  các pattern `(x+x+)+y`/`(a+)+$` bị engine tối ưu, không treo → không dùng
  được làm bằng chứng timeout.
- Bỏ NFC tổng thể trong normalize: span giờ map thẳng về raw input qua
  char_ranges; folded text đồng nhất nhờ per-char NFD ở bước fold.
- `detect_title` nhận folded_lines đã remap sang raw offsets từ runner.
- `baseline_eval.py` đọc `results.json` (text đã trích sẵn) — không đọc lại
  file Word, không in đường dẫn/tên/giá trị.
- `regex.error` KHÔNG kế thừa `re.error` — compile guard bắt riêng.

## Plan Change Log

## Review Triage Log

## Design Notes

- `regex` module: `Pattern.search/finditer(..., timeout=sec)` raise `TimeoutError`
  ngay trong engine — đây là interrupt thật, khác hẳn thread-pool wait.
  `regex.error` KHÔNG phải subclass `re.error` — catch riêng.
- Folded text đồng nhất cho input NFC lẫn NFD (fold làm NFD per-char), nên bỏ
  NFC tổng thể: span map thẳng về text gốc qua char_ranges của bước replacement.
- `(a|a)*b` né được `_NESTED_QUANTIFIER` (`(a|a)` không chứa quantifier bên trong)
  nhưng vẫn catastrophic — pattern dùng cho test timeout.
- JS `string.length`/`slice` theo UTF-16 unit; Python theo code point → UI phải
  slice qua `Array.from(text)`.

## Verification

**Commands:**
- `python -m pytest tools/regex_workbench/tests -q` -- expected: all passed, không treo
- `python tools/regex_workbench/baseline_eval.py --results <baseline results.json> --source-root <dir>` -- aggregate JSON only
- `python tools/regex_workbench/serve.py --port <p> --no-browser` + `POST /api/run` smoke
