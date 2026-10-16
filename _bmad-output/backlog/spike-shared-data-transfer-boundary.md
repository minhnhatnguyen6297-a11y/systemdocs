---
id: 13
type: spike
title: "Chốt DB vật lý và contract chuyển dữ liệu liên module"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt DB vật lý và contract chuyển dữ liệu liên module

## Description

Chốt DB vật lý/migration và chuyển dữ liệu xuyên ownership trước công việc thực sự ghi/chuyển liên module. Các phép đo Office cô lập không cần đợi DB vật lý chung.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C12
- source — _bmad-output/specs/shared/data-rules.md, §5–§7, Còn mở
- source — _bmad-output/decisions/decision-extraction-output-data-contract.md, §Decision
- source — contracts/README.md, dòng 20–23, 57–62, 69–78 (đọc 16/10/2026): ba công cụ độc lập; **chưa có contract trao đổi dữ liệu xuyên sản phẩm**; luật contract → owner duyệt → code
- source — _bmad-output/specs/README.md, §5, dòng 46,48 (engine chung/cách chuyển chưa chốt; module giữ quyền ghi)
- source — _bmad-output/specs/shared/data-rules.md, §4.1–§4.2 và §5–§7 (dòng 28–29,44–46,54–55,71–72,96–108,119–129,163–167)
- source — contracts/g1-module-data.md, §5 (APPROVED 14/09/2026) — ownership một máy
- source — contracts/zalo-intake/zalo-intake.md, §2 (DRAFT MIN-92) — producer/consumer + ranh giới trao đổi
- source — _bmad-output/specs/notaryoffice/README.md, §3,§5; _bmad-output/backlog/spike-office-pilot-scope.md, dòng 44–45 (“Không hard-after DB chung #13”)
- evidence tạm — _bmad-output/tmp/issue-13-shared-data-boundary/evidence.md (16/10/2026)

## Notes

- Tracking: C12; **investigation/evidence recorded 16/10/2026 — điều tra hoàn tất phần lấy được, KHÔNG phải “DB/kênh chuyển liên module đã được duyệt”**. Ownership policy đã có sẵn; **chưa có ca chuyển liên module nào được duyệt/chọn để triển khai** — ca Draft thì đã có (`zalo-intake` MIN-92, §2), nhưng Draft không phải quyền triển khai; DB vật lý/migration vẫn **UNSELECTED**. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Ownership hoặc migration sai có thể nối nhầm hồ sơ, mất dữ liệu và ghi ngoài quyền module.
- Open question (đã điều tra 16/10/2026 — xem ledger dưới): Với lần chuyển liên module cụ thể, ai sở hữu từng lần ghi, payload/xác nhận nào được duyệt, chọn DB vật lý/migration nào trước schema production?
- Người thực hiện/ngày: worker `shared-data-boundary-evidence`, nghiên cứu chỉ đọc và ghi tài liệu 16/10/2026; không phải owner, người thao tác hoặc reviewer độc lập. Không có quyết định sản phẩm mới, không tự chọn engine/migration, không tạo decision, không đổi spec.
- Ai chờ: **implementation chuyển liên module thật** — cần **một ca chuyển được duyệt/chọn để triển khai** (ca Draft đã có: `zalo-intake` MIN-92) + contract của ca đó được duyệt + model ổn định trước khi chọn DB vật lý/migration. Nơi ghi: contract dữ liệu/chuyển được duyệt và Notes này. Không gộp Case từ CCCD/GCN/thửa-tờ; không chặn #14 đo A1/A3/A4.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.
- Review closeout (16/10/2026): Quick review độc lập ngoài worker (reviewer `shared-data-boundary-review`) — **t1**: câu “chưa có ca chuyển cụ thể” nói quá vì `contracts/zalo-intake/zalo-intake.md` §2 đã mô tả một ca producer↔consumer + payload/ACK; phần thiếu là **duyệt/chọn để triển khai**, không phải sự tồn tại của ca/bản nháp — đã sửa toàn bộ câu chữ; **t2**: CLEAN, chỉ tài liệu (docs-only), không đo runtime, không chạy app/test. Bản ghi đóng băng từ đây, không đổi câu chữ thêm ngoài ghi chú closeout này. Không có phê duyệt sản phẩm nào được tạo.

### Ledger nguồn canonical — 16/10/2026

Các đường dẫn tính từ root repo; số dòng là vị trí đọc, không phải phiên bản hay bằng chứng chạy ứng dụng.

| Câu hỏi | Điều đã rõ (nguồn, đọc 16/10/2026) | Phần còn thiếu và hệ quả |
|---|---|---|
| Ai sở hữu từng lần ghi? | Chính sách đã chọn: module giữ quyền ghi của mình; dùng chung DB không cho ghi bảng do module khác sở hữu; dùng chung ứng dụng không cho tự nối/gộp — `_bmad-output/specs/README.md:46,48`, `_bmad-output/specs/shared/data-rules.md:96–101`. Trong một máy: `contracts/g1-module-data.md` §5 (APPROVED 14/09/2026) — sidecar/engine ghi, shell chỉ qua command. | Chưa có ca liên module nào **được duyệt/chọn để triển khai** để gán chủ từng lần ghi; câu trả lời per-ca thuộc contract của chính ca đó (ca Draft `zalo-intake` MIN-92 đã mô tả producer/consumer nhưng chưa được duyệt). |
| Payload/xác nhận nào được duyệt? | `contracts/README.md` (đọc 16/10/2026) dòng 20–23, 57–62, 69–78: ba công cụ **chưa có API giữa chúng, chưa đọc DB của nhau, chưa có file trao đổi tự động**; **hiện chưa có contract trao đổi dữ liệu xuyên sản phẩm**; luật nối = contract (ai gọi ai, dữ liệu gì, ai sở hữu, xử lý lỗi, ai chịu trách nhiệm khi schema đổi) → owner duyệt → mới viết code. | Chưa có payload/ACK nào được duyệt. Bản Draft đã thấy trong repo mô tả chuyển liên sản phẩm là `contracts/zalo-intake/zalo-intake.md` §2 — **DRAFT** MIN-92 (producer Zalo ↔ consumer Document Intake; ACK = raw đã lưu bền vững, không phải duyệt nghiệp vụ). Không suy đây là ca tương lai duy nhất. |
| Chọn DB vật lý/migration nào trước schema production? | Hiện trạng đã chốt là **SQLite theo module** (decision-34 “stack chung … SQLite/module”, accepted 05/10/2026; `specs/README.md:46`); ràng buộc gộp đã có: UUID/tiền tố nguồn cho record đi qua nhiều module, ISO-8601, tên field tài sản chung, không `rowid` ẩn/kiểu lỏng SQLite trong logic nghiệp vụ — `data-rules.md:102–129`. | **UNSELECTED**: “Engine DB vật lý cuối chưa chốt”; “DB chung và engine đích chưa duyệt”; mục **Còn mở** gồm “Engine DB chung và migration vật lý” — `data-rules.md:96–108,163–167`. Đây là việc kỹ thuật tương lai gắn với model ổn định + ca chuyển được duyệt/chọn để triển khai, **không** phải lựa chọn nghiệp vụ hiện tại; không tự chọn. |
| “DB nghiệp vụ chung là đích” có cho gộp Case hoặc nối module? | Không: “sau này sẽ gộp” **không phải giấy phép** (`contracts/README.md:57–59`); CCCD/GCN/thửa-tờ/số công chứng là bằng chứng đối chiếu, không tự tạo Case hoặc quan hệ sở hữu và không tạo Case liên module (`data-rules.md:44–46,54–55`; [decision-extraction-output-data-contract](../decisions/decision-extraction-output-data-contract.md), §Decision). | Giữ nguyên: không gộp Case, không dùng khóa định danh chung làm mã hồ sơ. Đích DB chung sau khi model ổn định không đổi phần này. |
| Hiện trạng code | **Quan sát đọc tĩnh có giới hạn, ngày 16/10/2026:** `notary_v2/database.py:11–14` neo `notary.db`; `upload_lab/batch_scan.py:26–27` + `upload_lab/registry.py:17–25` dùng `registry.sqlite3` theo website; `shell/sidecar/notary_adapter.py:8–9`, `upload_adapter.py:7–11`, `engine_roots.py:26–31` ghi DB qua command và tách engine root theo module. Grep tên DB trong `notary_v2/` + `upload_lab/` không thấy truy cập DB của module kia. | **Đây KHÔNG phải chứng minh runtime độc lập toàn cục** — chỉ là đọc tĩnh giới hạn tại thời điểm ghi; không chạy app/test, không thay bằng chứng runtime. Không dùng quan sát này thay cho luật contract ở các dòng trên. |

### Bên chờ và giao bằng chứng — 16/10/2026

- **Implementation chuyển liên module thật:** chờ **một ca chuyển được duyệt/chọn để triển khai (ca Draft đã có: `zalo-intake` MIN-92) + contract của ca đó được duyệt + model ổn định**; khi đó mới chốt ownership từng lần ghi, payload/ACK, và chọn DB vật lý/migration (việc kỹ thuật, ghi ở cấp spec/contract theo `data-rules.md` §6). Không dựng kênh trước contract.
- **Owner:** hiện **không có lựa chọn sản phẩm mới đủ bằng chứng**. Khi có ca được chọn để triển khai, việc của owner là duyệt contract của chính ca đó (`contracts/README.md:75`); **không** hỏi owner chọn SQLite/Postgres, revision hay cơ chế chuẩn hóa.
- **Giữ nguyên Draft/Pending (retain):** `contracts/zalo-intake/` (DRAFT MIN-92), `IdentityEvidence`/`ConversionEnvelope` xuyên sản phẩm (Draft MIN-62/MIN-61), thiết kế NotaryOffice (Draft, chưa có runtime). Không nâng thành đã duyệt.
- **Việc độc lập không phải chờ:** #14 đo Office cô lập A1/A3/A4 **không bị chặn** bởi DB vật lý chung hay bởi #13; phần evidence của #12 đã đóng; không phát sinh hard-after mới.
- **Nơi ghi đáp án:** Notes này là bản giữ bền vững; bằng chứng chi tiết tạm ở [`tmp/issue-13-shared-data-boundary/evidence.md`](../tmp/issue-13-shared-data-boundary/evidence.md). Không tạo decision mới cho lượt điều tra này; nếu sau này có quyết định hệ thống thật thì ghi `decisions/` + spec cùng phiên.
- **Giới hạn kết luận:** AC của spike cho phép xác định bằng chứng thiếu. Kết quả là **điều tra hoàn tất phần lấy được**: không phải “DB/kênh chuyển liên module đã được duyệt”, không phải mọi phần đã trả lời, và không có phê duyệt nào được tạo.
