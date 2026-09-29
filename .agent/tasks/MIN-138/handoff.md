# Handoff — MIN-138

## Tiếp nối 29/09 — gom tài liệu `notary_v2/docs`

Baseline trước đợt này: `5c5897005e059507aae840c85d314696de3eb21c`.
38 file cũ được đối chiếu theo nhóm dưới đây; Git tại baseline vẫn giữ nguyên
toàn văn để tra lịch sử. Bảng này là đường truy nguồn, không phải spec thứ hai.

| Nguồn cũ | Đích/giá trị giữ lại |
|---|---|
| `platform/document-intake/{spec,property-rules}.md` | `docs/spec/notary_v2/input/{ocr-detail,property-rules}.md` và README Input |
| `platform/zalo-document-inbox/spec.md` | `docs/spec/notary_v2/input/zalo/acceptance.md`; v1/audit giữ trong Git và record MIN-89 |
| `platform/case-workspace/{drafting-tab,visual-design}.md` | `docs/spec/notary_v2/{workspace-detail,visual-reference}.md`; README module giải thích vai trò |
| `domains/inheritance/{workflow,word-export}.md` | `docs/spec/notary_v2/diagram/inheritance/web-workflow.md` và `word-output-detail.md` |
| `domains/inheritance/spec.md` và `superpowers/specs/2026-08-24-*` | Draft mới nhất ở `docs/spec/notary_v2/diagram/inheritance/business-rules.md`; bản trước trong Git, chưa duyệt |
| `domains/inheritance/technical/inheritance-engine.md`, research catalog/provenance | `docs/spec/notary_v2/diagram/inheritance/{engine,examples,provenance}.md` |
| `platform/fast-text-audit/technical.md` | `docs/spec/notary_v2/fast-text-audit.md` |
| `platform/document-generation/technical.md` | Quy tắc renderer và context chính ở `docs/spec/notary_v2/word-output.md`; mapping cụ thể vẫn cạnh template |
| Stage-sync Draft, case-state parked | `docs/spec/notary_v2/diagram/stage-sync-draft.md` và `diagram/inheritance/case-state-parked.md`, gắn nhãn chưa duyệt |
| Validation snapshot, plans, v1 legacy, agent/template cũ | Kết luận và điểm mở nhập vào spec/record liên quan; văn bản gốc ở Git baseline, không còn là tài liệu vận hành |

Không coi Draft thừa kế, Zalo hay POC MarkItDown là Approved. Các nhắc tới
đường cũ trong task record đã kết thúc là bằng chứng của thời điểm đó.

## Trạng thái khi bàn giao — 2026-09-29

Đã hoàn tất cấu trúc lại và review diff. Linear MIN-138 có thể chuyển `Done`
sau khi local commit được tạo.

## Kết quả

- `README.md`: bản đồ duy nhất của cây spec.
- `AGENTS.md`: luật đọc gốc → cha → lá và chọn nơi ghi theo phạm vi.
- `docs/spec/`: SOT dài hạn mới theo hệ thống/module/flow/feature.
- `docs/spec/ui/`: giữ token, prototype và ảnh duyệt như phụ lục.
- `docs/architecture`, `docs/product`, `docs/maintenance` và ADR rời trong
  `notary_v2/docs/architecture`: đã xóa sau khi chuyển nội dung còn hiệu lực.
- Link liên quan trong module, contract, shell và template đã đổi sang cây mới.

## Cách verify

- `rtk git diff --check`
- Tìm các đường cũ bằng `rtk rg`.
- Kiểm link local của toàn bộ Markdown thay đổi/mới.
- Xem cây trong `README.md`, rồi đi tới từng spec lá.

## Việc còn lại / rủi ro

- Bản rút gọn đã qua 4 review lens; các gap cụ thể về lý do, trạng thái Draft,
  UI, DB, Internet và contract đã được bổ sung. Lịch sử đầy đủ vẫn có trong Git.
- Không đổi runtime behavior hoặc schema contract. File runtime chỉ đổi comment
  dẫn tài liệu; contract chỉ sửa mô tả/link để giữ đúng trạng thái hiện có.

## File tạm đã dọn

- Script kiểm link tạm trong `.agent/scratch/` đã xóa.
