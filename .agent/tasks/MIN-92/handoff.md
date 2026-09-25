# Handoff — MIN-92

Viết khi kết thúc phiên hoặc chuyển giao cho agent/người khác.

## Trạng thái khi bàn giao — 2026-09-25

**MIN-92 hoàn tất.** Contract `intake.*.v1` ranh giới Zalo↔Document Intake đã
được owner duyệt và publish tại `contracts/zalo-intake/` — contract
xuyên-sản-phẩm đầu tiên của repo. Reviewer độc lập chấm PASS sau hai vòng
(NEEDS_FIX → fix loop → PASS). Chưa commit (owner chọn "chưa commit").

Nội dung contract (9 schema + doc + validator + 99 fixtures):

- Gói raw: `manifest.json` (`intake.raw-package.v1`), `records.jsonl`
  (byte-exact UTF-8/LF), `READY.json`; sequence contiguous; replay cùng hash =
  idempotent, cùng `package_id` khác hash = conflict.
- Feed pending + receipt/ACK + service status + error envelope.
- Raw record 5 kind: `message_text`, `ocr_page`, `processing_status`,
  `source_event` (recall/reaction; **edit unsupported v1**), `listener_session`
  (mỗi lần kết nối = `session_id`+`logical_id` mới; `uncertain_gap` chỉ trên
  `connected`).
- OCR: attempt đầy đủ (task/op/region/frame/transform_chain/geometry_status/
  provider_lines verbatim); `text_recognition` ⇒ `geometry_status=not_applicable`;
  `present_mapping_verified` **reserved — enum loại hẳn** (chờ MIN-95/98 kiểm
  chứng khung tọa độ); transcript `text_lines`/`selected_pass_ids` giữ lượt
  pipeline capture-time — OCR bổ sung chỉ thêm attempt ở revision ≥ 2.
- Ảnh: `image_expires_at = captured_at + 168h` đúng tuyệt đối; `image_state`
  captured/retained/expired/missing; **không ảnh/base64/URL vào record**
  (quét đệ quy `image_payload_forbidden`/`provider_payload_forbidden`).
- OCR bổ sung: 1 variant/request (`crop_bottom`+preset bắt buộc | `rotate` |
  `full_res`), auto+tay, quota 2/khóa-168h + 100/ngày + 2 đồng thời, dedupe
  `(logical_id, variant, preset, config_version)`, retry ≤3, kết quả đi qua
  gói raw mới (không trả text trong response).
- Raw sau ACK: giữ 30 ngày, cap 1 GiB, cảnh báo 80%, chỉ xóa gói đã ACK.

## File đã đổi

- `contracts/zalo-intake/` — **mới, publish**: `zalo-intake.md` (SOT contract),
  `CONTRACT_REVISION`, 9 `*.schema.json`, `validate_examples.py`, `_validator/`,
  `examples/` (27 valid + 72 invalid + `_build/` tool tái tạo),
  `examples/.gitattributes` (`* -text` — chống autocrlf phá byte-exact).
- `contracts/README.md` — mục lục: trạng thái "hai kênh đã publish", thêm bảng
  zalo-intake.
- `.agent/tasks/MIN-92/` — brief/decisions/progress/handoff.
- `.agent/scratch/MIN-92/` — giữ `source-facts.md` + `decision-sheet.md` (input
  cho MIN-93/95); **đã xóa bản staging `contracts/`** để tránh hai bản contract.

## Cách verify

```powershell
cd D:\systemdocs\contracts\zalo-intake
python validate_examples.py          # kỳ vọng: 27 valid, 72 invalid, 0 unexpected, exit 0
python -m unittest discover -s _validator/tests -t .   # 117 test OK
```

`.gitattributes` đảm bảo checkout không đổi byte của fixtures.

## Việc còn lại / rủi ro

- **MIN-93 tiếp theo** theo dependency MIN-92→MIN-93→MIN-103→MIN-94/95/97→…
  Scaffold repo Zalo độc lập (`D:\zalo-intake` → `zalo/`) implement đúng contract
  này; contract là SOT, không sửa contract trong task implement.
- Minor mở (không chặn): vài nhánh fixture chưa phủ (dir-in-package, receipt.json
  trong gói, filename case-variant, `full_image`+fraction, gap-on-disconnected);
  `accepted_at`/`deduplicated` trong status là optional; `rules_receipt` chưa
  quét `package/**`. Thêm khi contract cần sửa lần tới.
- Geometry `location[8]`/`rotate_rect[5]` được bảo tồn verbatim nhưng khung tọa
  độ **chưa xác minh** — MIN-95/98 kiểm bằng dữ liệu thật trước khi dùng layout.
- Commit: chưa commit theo lựa chọn owner; khi commit, nhớ `.gitattributes`
  phải đi cùng lần commit đầu để fixtures không bị CRLF.

## File tạm đã dọn

- Xóa `.agent/scratch/MIN-92/contracts/` (bản staging — trùng với publish).
- Còn giữ: `.agent/scratch/MIN-92/source-facts.md`, `decision-sheet.md` (sẽ
  dọn sau khi MIN-93 xong); `.agent/scratch/sdd/zalo-v2/progress.md` (ledger
  xuyên MIN-91 → dọn cuối goal).
