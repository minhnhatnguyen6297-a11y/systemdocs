# Progress — MIN-92

Ghi đến đâu khi làm đến đó. Agent/phiên khác đọc file này + `brief.md` là làm
tiếp được mà không cần hỏi lại.

## Trạng thái: HOÀN TẤT — owner duyệt + đã publish 2026-09-25

## Đã làm
- Đọc SOT: README chỉ đường, spec v2 (CAP-11/12/15/16, T05/T06/T09/T18/T21–T24), plan §1.2–1.3/§4 MIN-92, draft `zalo-file-exchange-v1-draft.md`, `contracts/README.md`, issue MIN-92.
- Dựng khu nháp `.agent/scratch/MIN-92/contracts/zalo-intake/` (chưa duyệt nên chưa vào `contracts/`).
- Wave 1 hoàn tất: A (transport schemas+fixtures), B (raw-record+geometry+fixtures), C (OCR request+quota+fixtures), D (`zalo-intake.md` 972 dòng).
- Integration + fix loop: gỡ `region` khỏi ocr-request (owner chưa duyệt tọa độ tự do); thêm rule `kind_body_mismatch`; sửa fixture rec-05/rec-11/gap-01 cho đúng ngữ nghĩa transcript/session; manifest `files` `maxItems:1`+`uniqueItems`; region conditional trong raw-record; `rules_status` smoke-load schema phụ.
- Reviewer độc lập chấm lần 1 NEEDS_FIX → fix loop → chấm lần 2 **PASS** (3 Important resolved, còn minor doc-nit + coverage ghi vào checklist publish).

## Đang làm dở
- Không còn. Owner duyệt publish (giữ `_build`, chưa commit) → đã publish
  `contracts/zalo-intake/` + `examples/.gitattributes` + cập nhật
  `contracts/README.md`. Validator chạy lại từ vị trí publish: 99 case xanh.

## Owner đã chốt (xem decisions.md)
quota theo logical_id (2/khóa/168h, 100 lượt/24h, 2 đồng thời); raw sau ACK 30d/1GiB/80%; transcript giữ lượt mặc định; auto+tay; 1 variant/request; source_event v1 (recall+reaction, edit unsupported).

## Wave 0 đã xong
- `source-facts.md`: zca-js chỉ phát undo/reaction (không edit); ≤1 attachment/tin; page_index 1-based; rotate=provider enable_rotate; words_info{location[8],rotate_rect[5]} — khung tọa độ UNVERIFIED.
- Framework validator stdlib: `_validator/` (io byte-exact, schema_subset, cases, run_slice) + `validate_examples.py` — 117 unit test xanh; report `MIN-92-framework-report.md`.

## Bước tiếp theo (khi owner duyệt)
1. Chuyển staging → `contracts/zalo-intake/` (giữ `_validator/`, `validate_examples.py`, `examples/`).
2. Thêm `contracts/zalo-intake/examples/.gitattributes` (`* -text`) — `core.autocrlf=true` có thể làm hỏng fixture byte-exact.
3. Quyết định `examples/_build/` (script sinh fixture — giữ làm tool tái tạo hay bỏ).
4. Cập nhật `contracts/README.md` mục lục nếu cần, progress/handoff, ledger.
5. Git: hỏi owner cách commit (chưa commit gì; scratch gitignored).

## Check đã chạy (sau mọi fix — 2026-09-25)
- `python validate_examples.py` trong staging: **27 valid + 72 invalid = 99 case, 0 unexpected, exit 0**.
- `python -m unittest discover -s _validator/tests -t .`: **117 test OK**.
- Byte sweep toàn bộ `.jsonl`: không BOM, không CR, kết thúc LF (pkg-13/pkg-14 vi phạm cố ý → reject đúng; pkg-02 rỗng hợp lệ record_count=0). JSON fixtures không BOM.
- Reviewer pass 2: **PASS** — drift mới 0; minor còn: vài nhánh fixture chưa phủ (dir-in-package, receipt.json trong gói, case-variant filename, full_image+fraction, gap-on-disconnected), `accepted_at`/`deduplicated` optional, `rules_receipt` skip `package/**`.
