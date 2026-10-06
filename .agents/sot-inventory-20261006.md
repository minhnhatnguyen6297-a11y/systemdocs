# Kiểm kê SOT/quyết định — 2026-10-06

Bản làm việc sau khi gộp `consolidate/monorepo` vào nhánh
`minhnhatnguyen6297-a11y/task5-regex-hop-dong-word` (commit merge 97c2960).
Mục tiêu: liệt kê chỗ mâu thuẫn để Owner duyệt trước khi sửa spec/code.

## Trạng thái ký hiệu

- **[CHỐT]**: quyết định mới nhất của Owner, cần đồng bộ vào mọi SOT.
- **[MÂU THUẪN]**: hai nguồn ghi khác nhau, chờ Owner xác nhận phạm vi.
- **[MỞ]**: câu hỏi nghiệp vụ chưa có nguồn, không tự chốt.

## Bảng kiểm kê

| # | Chủ đề | Nguồn A | Nguồn B | Quyết định mới nhất | Trạng thái / việc cần làm |
|---|--------|---------|---------|---------------------|--------------------------|
| 1 | Lõi regex chung | `tools/regex_workbench/README.md` + `docx-import.md:45` — Owner NAIA-4 02/10 chọn `engine/` làm lõi (zoning-first, provenance, honest states) | `docs/spec/upload_lab/regex-core.md` §6 — `upload_lab/extract_contract.py` tự nhận bản gốc | Workbench (02/10, trước task5). Giờ thêm nhu cầu đề xuất placeholder → càng cần zoner | **[CHỐT]** sửa regex-core.md §6, regex-rules.md §0, README regex-test-tool |
| 2 | Serial GCN | `entities.md` §2 + contract §4.2/§1136/§1564: bắt buộc `[A-Z]{2}\d{6,8}` (MIN-141, Owner 03/10); ghi MIN-140 optional là "lịch sử" | decision-2 (04/10), TASK-5 (05/10), Owner 06/10: serial tự do/optional/trùng được | Owner 06/10: **bỏ ở tất cả các nơi** (decision-46) | **[ĐÃ ĐỒNG BỘ]** spec+contract+schema+validator; còn runtime `case_workspace.py` (so_n_format) và `form.html` (required) — việc triển khai |
| 3 | Quê quán `place_of_origin` | contract §4.1 person_row vẫn có trường | UI bỏ từ MIN-133; Owner 06/10: không dùng | **Giữ trường, engine không điền** (decision-46) | **[ĐÃ ĐỒNG BỘ]** contract §4.1 |
| 4 | Người làm chứng / lời chứng | TASK-5 + brainstorm 04/10: bỏ CCV/người làm chứng, không xác nhận qua vùng ký | task5 engine xuất `loi_chung`, validator có R11 | TASK-5 (05/10) | **[CHỐT]** engine bỏ trích lời chứng, xóa R11 khỏi validator |
| 5 | Giới tính | docx-import.md: không suy giới tính; Owner 06/10: thiếu → để trống + cờ | task5 engine suy "Ông" từ chữ "Thị" | Không suy đoán | **[CHỐT]** sửa engine |
| 6 | Diện tích | docx-import.md nhận `1.234,5` | Owner 06/10: neo `m2`; chỉ dấu chấm (`1.234`) → mơ hồ, giữ nguyên văn + cờ | Owner 06/10 | **[CHỐT]** bổ sung quy tắc dấu chấm trần vào docx-import.md |
| 7 | Trích lục người chết | contract có `loai_giay_to` cho giấy tờ người | task5 engine giữ `nguoi_chet` riêng với `so_trich_luc` | Owner 06/10: cùng format CCCD, điền thẳng trường Người | **[CHỐT]** người chết = person_row (`ngay_chet` + trường giấy tờ) |
| 8 | Sổ TK / bảo hiểm | task5 đã code trích | Owner 06/10: tạm dừng chưa làm | **Nhận diện + gắn cờ "chưa hỗ trợ", không bóc dòng** (decision-46) | **[ĐÃ ĐỒNG BỘ]** docx-import.md; engine sửa khi port profile |
| 9 | Thông tin chung (số CC, ngày, CCV) | contract chỉ có `ngay_lap_ho_so`, `noi_niem_yet`, `ghi_chu`; chưa có trường số/ngày/CCV | Owner 06/10: hướng an toàn = bảng thông tin hồ sơ, chưa chốt | Chưa chốt | **[MỞ]** cần bổ sung contract trước khi code |
| 10 | Input text thô | Owner 06/10: input có thể là đoạn text dán | engine hiện đọc file | Owner 06/10 | **[CHỐT]** API `extract(path \| text)` |
| 11 | Đề xuất placeholder | Owner 06/10: chức năng mới cho soạn hồ sơ (quét cấu trúc mẫu chưa gắn placeholder) | chưa có nơi nào ghi | Owner 06/10 | **[CHỐT]** bổ sung vào spec lõi; dùng chung zoner + từ điển trường |
| 12 | S01–S20 đáp án | `.agents/review/sample-rules-20261005/` + handoff — chờ Owner duyệt (TASK-5 AC#1–2) | task5 tự viết test synthetic | TASK-5 | **[CHỐT]** duyệt đáp án 20 mẫu là bước đầu |
| 13 | TASK-5 là spike | TASK-5 status To Do, "chưa giao triển khai engine"; engine mới thuộc TASK-11 (archive) | task5 đã viết engine mới | TASK-5/TASK-11 | **[CHỐT]** task5 code = nguồn kiến thức trường, port sang profile; không merge nguyên trạng |
| 14 | Nơi lưu record | AGENTS mới: Backlog.md + `.agents/` | task5 để ở `.agent/tasks/`, Linear | AGENTS (merged) | **[CHỐT]** chuyển record task5 sang `.agents/`, task status ở Backlog |
| 15 | decision-2, decision-7 | title đúng hướng, body Context/Decision/Consequences rỗng | — | — | **[CHỐT]** điền nội dung khi chốt xong bảng này |
| 16 | Bản sao engine ở regex-test-tool | code `import extract_contract` từ root `tool/` | README ghi `engine/` | Owner 06/10: phát triển trong tool trước rồi chép sang upload_lab | **[CHỐT]** sau khi chốt lõi: tool gọi lõi chung, không chép tay |

## Nguồn đã kiểm

- `backlog/tasks/task-5 - Duyệt...md` (To Do, spike, AC#1–4)
- `backlog/archive/tasks/task-11 - Xay lai engine...md` (engine cấu trúc, AC#1–8)
- `backlog/decisions/decision-2` (serial tự do; body rỗng), `decision-4`, `decision-7`
- `tools/regex_workbench/README.md`, `engine/` (zoner, extractor, profiles, runner)
- `contracts/entities.md` §2, `contracts/notary-case-drafting.md` §4.1/§4.2/§1564
- `docs/spec/notary_v2/input/docx-import.md`, `docs/spec/notary_v2/stage.md`
- `.agents/handoff/notary-20261005/`, `.agents/review/sample-rules-20261005/`
- Phát biểu Owner 06/10 trong phiên hiện tại
