# Catalog issue — 15/10/2026

**Catalog status (2026-10-16):** #4, #5, #6, #7, #22, #25, and #28 are built within their approved scopes; this does not approve or complete the rest of the backlog or publish the catalog. Other issue statuses remain as listed; #1 is history/tracking-only and #11/#26 remain dropped. No active initiative change. [Quyết định cách theo dõi](../decisions/decision-issues-reconciliation-20261015.md). The separate pre-existing #28 UI `file_token` blocker remains deferred and is not claimed fixed. C22/#23 is superseded by the 2026-10-16 owner decision (rule management is developer-only); C07/#8's business question is answered with remaining choices technical. C02/#3 is answered by the 2026-10-16 owner decision (saved-case type conversion); C24/#25 is built (independent Quick clean).

## Ưu tiên, thứ tự và điều kiện bắt đầu

P1/P2 là ưu tiên đề xuất, không phải severity hay thứ tự ID. Cần refinement/approval trước implementation; spike chỉ nhận quyết định/bằng chứng. **Hard after: #22 ← #7; #23 ← #8 và #22; #25 ← #3.** Cạnh #7→#22 chỉ tuần tự hóa sửa cùng core, không thêm gate nghiệp vụ; #7 không chờ full parity. Không chặn pilot Office bởi DB vật lý chung hoặc nghiệm thu Word thật bởi naming. #27 về nguồn hành chính vẫn độc lập với #12. #11/#26 dropped theo quyết định owner; #28 không có hard after. #23 superseded 16/10/2026 (rule do developer quản lý) nên cạnh #23 ← #8/#22 chỉ còn lịch sử.

| Candidate / ID | Issue | Nhóm | Ưu tiên | Hard after | Sẵn sàng |
|---|---|---|---|---|---|
| C01 / #2 | [Không gian Stage, Pool và Diagram liền mạch, dễ thao tác](story-notary-workspace-continuity.md) | bug/report đã báo | P2 | không | 6/6 report đã built (18ae/b541/2c232/e86/ac5 + 802 sàn chiều cao 726px, geometry thật chứng minh; Node 193 pass/0 fail, adapter 83 pass, GUI gói default 0 fail + đóng sạch; independent Quick t1 patch thông báo dài + t2 clean) |
| C02 / #3 | [Chốt quy tắc đổi loại hồ sơ đã lưu](spike-saved-case-conversion-semantics.md) | quyết định | P1 | không | answered 2026-10-16 (owner chốt nguyên đề xuất: giữ Stage + reset Diagram, buộc chọn `document_type` mới; [decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)) |
| C03 / #4 | [Sơ đồ không hiển thị đúng thông báo khi gặp lỗi](bug-diagram-error-messages.md) | bug/report đã báo | P1 | không | built (2026-10-16; independent Quick review clean, no findings) |
| C04 / #5 | [Lưu và mở lại sơ đồ hợp lệ còn thiếu dữ liệu](story-save-valid-incomplete-diagram.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; full Notary 1115 passed, 2 skipped; scoped checks 41 + 239 passed, 2 skipped; diagram Node 30 passed; Electron 21/21; independent Quick t3 clean) |
| C05 / #6 | [Giữ nguyên độ đầy đủ của ngày qua lưu và xuất](story-preserve-year-only-precision.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; Q1 medium-risk fallback patch fixed and clean on recheck; no outstanding business decision) |
| C06 / #7 | [Regex bỏ sót serial nguyên văn và địa chỉ thửa có nhãn](bug-regex-raw-serial-parcel-address.md) | bug/report đã báo | P1 | không | built (2026-10-16; transfer profile 1.1.3; Notary full suite 1113 passed, 2 skipped, 115 warnings, 2 subtests on short basetemp; workbench 45 passed, 18 subtests; independent Quick review clean) |
| C07 / #8 | [Chốt vòng đời thử, công bố và chạy lại rule regex](spike-regex-rule-lifecycle.md) | quyết định | P1 | không | answered 2026-10-16 (owner: rule developer-only, có phân biệt phiên bản; người dùng không dùng tính năng); phần còn lại là lựa chọn kỹ thuật |
| C08 / #9 | [Kiểm chứng đường xuất Word thật và nguồn mẫu](spike-word-real-route-acceptance.md) | bằng chứng | P1 | không | spike answered 2026-10-16 (retained Quick t2 clean; native/Word visual not accepted; direct batch 2 + paired restore case 3 proof) |
| C09 / #10 | [Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word](spike-word-naming-authority.md) | bằng chứng | P2 | không | answered 2026-10-16 (entities §9.1 nguyên văn áp cả placeholder và rộng hơn Word §4.1; đã căn chỉnh phạm vi tên trường/khóa canonical + họ token compact giữ slot legacy, mặt chữ mẫu mới theo Word §4.1; không cần quyết định owner mới, không đổi parser/mapping; `tmp/issue-10-word-naming-authority/evidence.md`) |
| C10 / #11 | [Kết quả Lưu portal bị lệch khi đóng tab hoặc mất phản hồi](bug-upload-save-reconciliation.md) | bug/report đã báo — dropped | P1 lịch sử | không | DROPPED theo quyết định owner; giữ leaf/plan lịch sử, thay phạm vi bằng C27/#28 |
| C11 / #12 | [Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở](spike-extraction-source-policy-evidence.md) | bằng chứng | P2 | không | investigation/evidence recorded 16/10/2026; source/ground-truth gap còn lại, F04/F05 Pending; chỉ thay luật phụ thuộc nguồn thật mới bị chặn, không có gate chọn thuật toán cho owner |
| C12 / #13 | [Chốt DB vật lý và contract chuyển dữ liệu liên module](spike-shared-data-transfer-boundary.md) | quyết định | P2 | không | investigation/evidence recorded 16/10/2026; **chưa có ca chuyển liên module nào được duyệt/chọn để triển khai** (ca Draft đã có: `zalo-intake` MIN-92) nên chưa có ownership/payload-ACK per-ca; ownership policy đã chọn, “DB chung là đích” không phải quyền gộp Case; engine/migration **UNSELECTED** (việc kỹ thuật tương lai, không phải gate nghiệp vụ hiện tại) — `tmp/issue-13-shared-data-boundary/evidence.md` |
| C13 / #14 | [Chốt phạm vi và tiêu chí pilot NotaryOffice](spike-office-pilot-scope.md) | quyết định | P2 | không | **owner answered — 17/10/2026; spike scope closed, Office DEFERRED/Draft, không built**. Owner để lại làm sau; không giao pilot/đo A1/A3/A4/code/schema/runtime. Không còn gate #14 và **không tạo phụ thuộc Office cho spike còn lại**. |
| C14 / #15 | [Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại](spike-decision-source-gaps.md) | bằng chứng | P2 | không | answered 2026-10-17 (bounded theo nguồn leaf dẫn; không có lựa chọn sản phẩm mới; Draft/Pending giữ nguyên — [Notes](spike-decision-source-gaps.md#notes); ledger `_bmad-output/tmp/issue-15-decision-source-gaps/evidence.md`) |
| C15 / #16 | [Sửa tham chiếu không còn đúng trong spec đang dùng](story-canonical-spec-references.md) | khoảng lệch đã chọn | P2 | không | **built 17/10/2026 — independent Quick CLEAN, parent accepted**; hai tham chiếu canonical đã sửa, nguồn lịch sử có nhãn; structural DOC resolver **5 PASS / 0 FAIL** (đúng năm link), không tuyên bố nghiệm thu runtime — [Notes](story-canonical-spec-references.md#notes) |
| C16 / #17 | [Chuyển desktop sang bản Electron còn được hỗ trợ](story-supported-electron-release.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; independent Quick t2 clean; Electron 44.7.2/builder 24.13.3; 2,975-file snapshot proves startup/IPC `G1_SMOKE` only; public picker→`file.inspect` matched size/hash. Upload UI `upload.audit_excel` still fails on blank `file_ref.path`; production `--case offline` failed at `upload.scan` before its own snapshot; test `--case all` timed out after `upload.download_export`. Full Upload E2E is not green (xem plan/spec) |

| C17 / #18 | ~~Khôi phục bằng chứng và phân loại 12 report mất ghi chú~~ **REMOVED theo owner 17/10/2026** | bằng chứng (đã bỏ) | P2 | không | Bỏ issue đang hoạt động theo quyết định owner 17/10/2026 ([decision](../decisions/decision-owner-remove-historical-report-issue-20261017.md)); leaf đã gỡ khỏi backlog, không còn câu hỏi hay bảng record đang hoạt động; owner tự tạo issue riêng, **không dùng lại ID #18**; toàn bộ nội dung cũ giữ ở Git `8e8d0c1b298a13ab752166b5c6fdef1c06bcb826`. Đây không phải kết luận bug/đóng triệu chứng. |
| C18 / #19 | [Đặc tả tab Word tạo và lưu mẫu](spike-word-tab-authoring-scope.md) | quyết định | P2 | không | **owner answered 17/10/2026 — spike scope closed; authoring DEFERRED**, owner tự làm sau, cần spec kỹ trước implementation tương lai; Draft/`refined: false`, không built. Không còn gate A/B lúc này; chuyển #20. [Decision](../decisions/decision-owner-word-authoring-deferred-20261017.md). |
| C19 / #20 | [Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ](spike-case-list-query-labels.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C20 / #21 | [Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế](spike-inheritance-middle-node-deletion.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C21 / #22 | [Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi](story-shared-regex-consumer-cutover.md) | khoảng lệch đã chọn | P2 | #7 | built 2026-10-16; retained Quick t1 findings → patches → retained Quick final multiline recheck clean 16Oct, parent accepted; one core/identity, real staged DOCX proof; compare 828/0 (44 null + 256 shape, F10/F11 unreviewed); native GUI DOCX seam not exercised; #23 superseded |
| C22 / #23 | [Thử và công bố rule regex rồi duyệt kết quả chạy lại trong flow](story-in-flow-regex-publication-review.md) | khoảng lệch đã chọn | P2 | #8, #22 | SUPERSEDED 2026-10-16 theo quyết định owner (rule do developer quản lý; người dùng không dùng tính năng); giữ lịch sử, không triển khai |
| C23 / #24 | [Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần](story-gradual-fill-word-readiness.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; gate nhóm theo token mẫu thực dùng cho folder+legacy; before/after engine 523608a + UI packaged non-native picker; adapter cutover sidecar-only; Quick t1 finding fixed + recheck clean) |
| C24 / #25 | [Đổi loại hồ sơ đã lưu theo quy tắc đã chốt](story-saved-case-type-conversion.md) | khoảng lệch đã chọn | P2 | #3 | built (16/10/2026; command + dialog nguyên tử; service/DOCX 252, adapter/job/mock 263, Node 177, contract 83 files; Electron source IPC hai chiều + real DOCX export; independent Quick clean) |
| C25 / #26 | [Kiểm chứng ý nghĩa tín hiệu Lưu trên portal thật](spike-upload-real-save-signal-validation.md) | bằng chứng — dropped | P1 lịch sử | không | DROPPED; không còn là gate ngữ nghĩa portal cho cutover |
| C26 / #27 | [Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày](spike-administrative-same-day-evidence.md) | bằng chứng | P2 | không | chỉ nghiên cứu văn bản, không đổi thuật toán |
| C27 / #28 | [Bỏ theo dõi kết quả Lưu và giữ tiến độ chuẩn bị theo lượt](story-upload-web-official-sot-cutover.md) | khoảng lệch theo quyết định owner | P1 | không | built (2026-10-16; UI E2E remains blocked by the deferred pre-existing `file_token` mismatch) |

Khuyến nghị hiện hành, không phải lệnh triển khai: (1) #28 cutover đã được owner chốt và #4 formatter, #6 độ đầy đủ ngày, #7 field extraction, #5 lưu incomplete, #17 nền desktop đã built; #11 cũ đã dropped; vị trí đầu của #28 là đề xuất điều phối, không phải phần của lựa chọn A ban đầu; (2) #2 workspace đã built (trục 802 owner đã chốt: chiều cao, sàn 726px; Quick t2 clean); #9 nghiệm thu Word thật đã answered; #24 readiness điền dần đã built (Quick t1 clean sau vá nhãn readiness); (3) #22 cutover đã built (retained Quick final multiline recheck clean 16Oct); #23 đã superseded theo quyết định owner 16/10/2026 (rule developer-only); (4) #25 đã refined từ decision #3 (16/10/2026) — semantics chốt, chưa built. Các việc nguồn/docs/quyết định độc lập có thể được đánh giá cùng lúc. Cần refinement/approval trước implementation cho việc chưa được uỷ quyền.

## Câu hỏi còn mở và phần đã rõ

- **C01 / #2:** 802 đã làm theo quyết định owner (trả lời '1'): tăng CHIỀU CAO vùng Sơ đồ + Pool — sàn 726px từ baseline 484px của report, không đổi chiều rộng; geometry thật trên gói default xác nhận (thừa kế diagram 236→726px, khối gộp `.cd-rel-body` 244→734px; Hai bên giữ nguyên theo nội dung). 6/6 report đã built; independent Quick t1 (patch thông báo dài) + t2 clean.
- **C02 / #3 (answered 16/10/2026):** owner chốt nguyên đề xuất — giữ ID + giá trị Người/Tài sản của Stage; reset Diagram rỗng theo domain mới; buộc chọn `document_type` mới + xác nhận phần Diagram mất trước khi ghi; chuyển vào Thừa kế cần `owner_row_id` từ Stage, vào Hai bên cấm; giữ guard revision/khóa/atomic; binding Word không remap ngầm, không thêm chặn hồ sơ đã xuất/bound. Ngoại lệ `case_type`/`document_type` immutable (contract §13.18). [Decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md).
- **C07 / #8 (answered 16/10/2026):** owner chốt rule regex văn bản và rule upload theo website do developer quản lý, có phân biệt phiên bản để nhận biết; người dùng sản phẩm không dùng tính năng này. Người dùng vẫn xem/sửa kết quả bóc tách trước khi nhận vào Stage. Phần cơ chế (nơi lưu, format, version/hash, kích hoạt/quay lui nội bộ, phạm vi chạy lại) là lựa chọn kỹ thuật của developer, không còn câu hỏi nghiệp vụ. [Decision](../decisions/decision-owner-regex-rule-developer-only-20261016.md).
- **C08 / #9 (answered 16/10/2026):** evidence đã trả lời — direct `word_batch_export` batch 2 mẫu + paired DB/`docx_sources` restore với ca 3 là bằng chứng sau khi dừng app; retained Quick t2 clean. Còn là **giới hạn capability**: native picker/renderer transport, kiểm trang Word thật và cài sạch/máy khác/non-NTFS chưa nghiệm thu; không thử phá dữ liệu production.
- **C09 / #10 (answered 16/10/2026):** câu blanket `entities.md` §9.1 nguyên văn bắt buộc viết liền và **nêu cả placeholder**, rộng hơn Word §4.1 — đã căn chỉnh về phạm vi tên trường/khóa canonical + họ token compact, mặt chữ placeholder mẫu mới theo Word §4.1. Hành vi hiện hành theo spec Word §4.1 + C09 đã rõ; **không** cần owner chọn lựa chọn sản phẩm mới, **không** đổi parser/mapping/cú pháp. Bằng chứng: `tmp/issue-10-word-naming-authority/evidence.md`.
- **C11 / #12 (evidence recorded 16/10/2026):** ledger nguồn có ngày đã ghi bền vững trong [Notes của leaf](spike-extraction-source-policy-evidence.md#notes); điều tra hoàn tất phần reachable, **không phải đáp án trường đã duyệt**. P04 là `210 m2`/`210,0 m2`, chưa phải hai tổng thực sự khác; P05 là `40/CLN/12/2043` và `40/CLN/12/2063` + ghi chú, chưa biết hai cụm hay hai phiên bản. Người giữ nguồn cần đúng Word/ảnh gốc + filename/hash/trang/đoạn và nhãn độc lập trước output. F04/F05 vẫn Pending; nguyên tắc thửa/tờ + DB/giữ raw/không tự gộp đã chọn; không hỏi owner chọn thuật toán khi thiếu ground truth, không mở lại lỗi #22 built. Không bao gồm #27.
- **C12 / #13 (evidence recorded 16/10/2026 — điều tra hoàn tất phần lấy được, không phải “DB/kênh chuyển đã duyệt”):** **Chưa có ca chuyển liên module nào được duyệt/chọn để triển khai** (ca Draft đã có: `zalo-intake` MIN-92, chưa được duyệt); `contracts/README.md` (đọc 16/10/2026, dòng 20–23, 57–62, 69–78) ghi ba công cụ độc lập và **chưa có contract trao đổi dữ liệu xuyên sản phẩm**, luật nối = contract → owner duyệt → code. Ownership đã chọn ở mức chính sách (module giữ quyền ghi; dùng chung DB/app không cho ghi bảng module khác, không tự nối/gộp); “DB nghiệp vụ chung là đích” **không** phải giấy phép gộp Case. Payload/xác nhận per-ca: chưa có bản nào được duyệt (bản Draft đã thấy: `zalo-intake` MIN-92). DB vật lý/migration **vẫn UNSELECTED** — việc kỹ thuật sau khi có ca chuyển được duyệt/chọn + contract + model ổn định, không tự chọn và không phải lựa chọn owner hiện tại. Giữ Draft `zalo-intake`/`IdentityEvidence`/`ConversionEnvelope`/Office; #14 A1/A3/A4 không bị chặn. Chi tiết: [Notes leaf](spike-shared-data-transfer-boundary.md#notes) + `tmp/issue-13-shared-data-boundary/evidence.md`.
- **C13 / #14 (owner answered — 17/10/2026):** “notaryoffice để lại, tôi sẽ làm sau” — [decision accepted](../decisions/decision-owner-notaryoffice-deferred-20261017.md). Toàn bộ Office **DEFERRED**, giữ Draft/công việc/spec; không giao pilot, phép đo A1/A3/A4, code/schema/runtime lúc này, không đặt hạn mở lại. Câu hỏi phạm vi spike đã khép lại, không còn business gate #14; các spike còn lại đi theo nguồn/bằng chứng riêng của nó; không Autoresearch/duyệt lại từng plan. Đây không phải Office built hay pilot nghiệm thu. [Notes + ledger lịch sử](spike-office-pilot-scope.md#notes) giữ hướng owner 25/09 và bằng chứng chưa đo; proof Notary/Upload không thay A1/A3/A4.
- **C14 / #15 (answered 17/10/2026, bounded theo nguồn leaf dẫn):** quy tắc còn chưa được owner duyệt là *bảng đơn dòng* (decision-72; spec tự ghi chưa duyệt — không mở lại ở đây); tiểu quy tắc *ngoặc người chết* là **provenance gap** (thiếu nguồn duyệt độc lập, không kết luận luật sai). Task-3/decision-48 **không tìm thấy bảng gốc** (không có trong repo/chưa từng commit) — nội dung còn ở **spec tự đủ** (thẩm quyền hành vi hiện hành) + thẻ task Done (chỉ bằng chứng hoàn thành/tóm tắt), **không** nguyên văn/rationale gốc; `decision-40..47` accepted nhưng **thân rỗng (không thẩm quyền)**. **Không việc nào của TASK-3 đã đối chiếu bị nguồn đã mất chặn** (không suy rộng cho mọi nguồn đã mất). Bên chờ ngoài #15: #12 (nguồn/nhãn F04/F05) và #13 (DB/kênh chuyển — việc kỹ thuật UNSELECTED). Draft/Pending giữ nguyên.
- **C18 / #19 (owner answered 17/10/2026 — DEFERRED):** “chức năng này tôi sẽ tự làm sau, cần spec kỹ. Chuyển issue khác”. [Decision](../decisions/decision-owner-word-authoring-deferred-20261017.md). Câu hỏi nguồn/bố cục đã được gửi; đáp án là hoãn, không chọn A/B/storage/catalog/nghiệm thu. Cần spec chi tiết khi làm sau, chưa giao viết lúc này. Giữ leaf/Draft/`refined: false`, không built; không hỏi tiếp, chuyển #20. Xuất Word/intake/token hiện có không bị hoãn.
- **C19 / #20:** Chọn nhãn/trạng thái, trường nguồn và luật tìm/lọc nào, gồm người tạo/tên/ngày và trạng thái rỗng/lỗi?
- **C20 / #21:** Sau khi báo các con/quan hệ bị ảnh hưởng, nhánh nào giữ, tách hay xóa; xác nhận/hủy ra sao và lưu/mở lại state canonical thế nào?
- **C23 / #24 (built 16/10/2026; Quick t1 finding vá nhãn readiness + recheck clean):** phạm vi nới đã chốt bằng code + spec/contract: gate nhóm (`no_landowner`/`no_deceased_landowner`/`no_receiver` và `no_diagram` hai bên) chỉ áp theo token mẫu thực dùng — nhận diện theo registry key engine sinh, catalog legacy theo mẫu từng `document_key`, folder mode giữ semantics nhóm thiếu để trống; giới hạn kỹ thuật, unresolved-slot và người được ủy quyền mẫu cần giữ nguyên. Bằng chứng before/after (engine 523608a cô lập) + UI packaged trong `_bmad-output/tmp/issue-24-word-readiness/evidence/`; independent Quick chạy sau.
- **C09 đã rõ:** ngoặc vuông, tên nhóm dễ đọc cho mẫu mới, tên viết liền hỗ trợ và alias cũ theo Word §4.1. #10 chỉ đối chiếu phạm vi câu bắt buộc tên viết liền trong entities §9.1; không hỏi lại cú pháp, không thêm hỗ trợ/migration/phát hiện ngoặc nhọn.
- **C16 / #17 — BUILT:** Runtime/IPC/picker evidence and limitations are recorded in [runtime record](../specs/shell/electron-runtime-support.md); full Upload paths remain failed/incomplete, not a blocker to the scoped runtime-support result.
- **C22 / #23 — SUPERSEDED 16/10/2026:** owner chốt rule do developer quản lý; không có UI người dùng thử/công bố/chọn phiên bản/rollback. Leaf giữ lịch sử; luồng duyệt kết quả bóc tách trước Stage giữ nguyên.
- **C24 / #25 (built 16/10/2026; independent Quick clean):** dedicated `notary.workspace_convert_type` + dialog `Đổi loại`; giữ Stage ID/giá trị, reset Diagram theo domain mới, buộc chọn `document_type` + owner (vào Thừa kế) + xác nhận mất Diagram. Binding cũ giữ guard `word.original_mapping_invalid`. Bằng chứng trong `tmp/issue-25-saved-case-conversion/evidence/`.
- **C25 / #26 — DROPPED:** quyết định owner bỏ theo dõi/diễn giải kết quả Lưu; không cần kiểm chứng host/body/từng trường làm gate cho contract hoặc runtime cutover. Nội dung spike và bằng chứng cũ được giữ làm lịch sử, không phải yêu cầu hiện hành.
- **C26 / #27:** văn bản nào chứng minh chuyển một phần và bãi bỏ phối hợp cùng ngày? Thiếu nguồn giữ chưa xác minh; không chọn thứ tự nội ngày hoặc cấm toàn bộ cùng ngày.
- **C27 / #28:** built within its approved scope (2026-10-16); the pre-existing picker/reference `file_token` mismatch still blocks UI E2E and remains deferred. No unresolved business decision.

## Ánh xạ đủ bảy report hiện tại

Chỉ ghi tóm tắt che dữ liệu; UUID dẫn tới bằng chứng private. Spec mới không chứng minh đã sửa.

- `18ae1083-4110-4c2e-bb35-6b815d8d14ac` — Địa chỉ/Nơi chết và nơi cấp giấy tờ lẫn nghĩa → C01/#2; đã xử lý (nhãn theo bằng chứng).
- `2c232a28-38aa-49e0-b591-ad0f6de1d807` — Cần tăng chiều rộng Pool → C01/#2; đã xử lý (nội dung 224/khung 240).
- `802bd69e-0b20-44df-8f83-7c83431fcd75` — Cần thêm chiều cao Pool/Sơ đồ → C01/#2; đã xử lý (sàn 726px chiều cao, geometry trong plan phase).
- `ac5e3ae3-bb4b-40f1-8cab-97591a182c61` — Thông báo đẩy Sơ đồ xuống, gãy flow → C01/#2; đã xử lý (thông báo trong thanh trên).
- `b54184b3-3606-4f7b-afec-1a7cf9d0a8e3` — Bỏ riêng Hủy thay đổi Stage, giữ bảo vệ nháp → C01/#2; đã xử lý (nút + cơ chế khôi phục riêng đã gỡ, guard giữ).
- `d9da640e-43fd-435e-b892-f05b517eff1f` — Không sửa được loại hồ sơ đã lưu → C02/#3 rồi C24/#25; #3 trả lời 16/10/2026 ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)), #25 built 16/10/2026 (independent Quick clean).
- `e86a02bb-9e67-48ba-a14a-46b787553231` — Ô Hai bên dẹt, khó thả → C01/#2; đã xử lý (ô 202×52, giữ p1..p30).

## Phủ 22 ghi nhận deferred

Nguồn: [deferred-work](../implementation-artifacts/deferred-work.md). Key là dòng bắt đầu ở nguồn, không là số issue mới.

| Record | Phạm vi đã che | Ánh xạ | Kết luận |
|---|---|---|---|
| deferred-1 | Kiểm dynamic import trong package | C16 | Bằng chứng release; smoke thủ công cũ không thay regression đóng gói. |
| deferred-5 | CLI standalone và regex sau copy | C21,C16 | Giữ hành vi khi cutover/package; không tạo dự án tool kiểm thử mới. |
| deferred-9 | Bỏ Qt/web cũ sau cutover | PARKED | PARKED: chỉ retire sau nghiệm thu package và chọn phạm vi; chưa xác minh. |
| deferred-13 | Đọc lại 38 file nghiệp vụ cũ | C14; PARKED inheritance Draft | Dùng spec hiện hành; không tự duyệt Draft thừa kế archive. |
| deferred-19 | Corpus tổng hợp nhiều Người | C11,C21 | Bằng chứng parity/corpus, chưa là lỗi parser đã xác nhận. |
| deferred-20 | TAB trong DOC lẫn địa chỉ/mô tả | C11,C21 | Giả thuyết chưa xác minh; cần mẫu gán nhãn trước sửa. |
| deferred-21 | Bảng đơn dòng nhiều thửa | C11 | Decision72 chưa duyệt; chỉ đối chiếu bằng chứng. |
| deferred-22 | Bóc dòng sổ tiết kiệm/bảo hiểm | C11 | Yêu cầu bóc dòng đã bỏ: hiện chỉ nhận diện chưa hỗ trợ, không thêm parser. |
| deferred-23 | Bảng docs regex cũ trùng | C15 | Bố cục cũ được thay bằng spec gộp; chỉ sửa tham chiếu hiện hành. |
| deferred-24 | Bố cục progress/brief cũ | HISTORY | HISTORY: quy ước tác giả lịch sử, không là implementation sản phẩm. |
| deferred-26 | Picker native và nhìn từng trang Word | C08 | Chưa có nghiệm thu native/nội dung đầy đủ. |
| deferred-30 | Chuyển một phần/bãi bỏ cùng ngày | C26/#27 | Research độc lập: cần văn bản lịch sử trước luật thời gian; không tự cấm toàn bộ cùng ngày. |
| deferred-34 | Corpus nhóm/ownership đại diện | C11,C08,C21 | Chưa xác minh bằng corpus văn phòng; synthetic không đủ. |
| deferred-38 | Có cần editor tách/gộp ứng viên | C11 | Chưa chọn; cần ca gán nhãn ranh nhóm sai trước. |
| deferred-42 | Picker tới xuất Word bản gốc | C08 | Chưa nghiệm thu toàn native; backend/component không đủ. |
| deferred-45 | Cài sạch, khôi phục DB và nguồn | C08 | Chưa xác minh; phải giữ hash nguồn/binding cùng bản sao lưu. |
| deferred-49 | Công bố trên FS không hard-link | C08 | Xác định FS được hỗ trợ trước; chưa chứng minh là lỗi. |
| deferred-53 | Analyze chạy lại tất cả hay chỉ nguồn mới | C07,C22 | Chọn lifecycle rồi duyệt rerun; không tự đổi Stage đã nhận. |
| deferred-59 | Đếm decision thân trống cũ | C14 | 47 rồi 56 accepted/6 proposed là baseline lịch sử; không số hiện tại/blanket gate. |
| deferred-61 | Ký tự carriage-return trong title cũ | C14 | Hygiene lịch sử cần xác minh còn áp dụng; không duyệt lại nghiệp vụ. |
| deferred-63 | Mô hình process spec cũ | HISTORY | HISTORY: index/cách backlog hiện hành thay thế; không là sửa runtime. |
| deferred-66 | Electron hết hỗ trợ | C16 | Chọn target triển khai kỹ thuật; không tự khẳng định CVE. |

## Phủ 15 nhận xét review37

Đây là nhận xét review/safeguard bằng chứng, không là 15 report người dùng. R01–R15 theo thứ tự `tmp/review-37-reports-20261009/findings.json`.

| Key | Nhận xét | Ánh xạ/kết luận |
|---|---|---|
| R01 | Trùng alias formatter | C03: Giữ alias không trùng, không export giả. |
| R02 | Test fallback che lỗi | C03: Nghiệm thu đúng catalog và thứ tự nạp thật. |
| R03 | Thiếu nhánh lỗi lưu | C03: Phủ lưu thông thường trả lỗi. |
| R04 | Bỏ sót report toàn vùng | C17 đã bỏ theo owner 17/10/2026: Giữ riêng UUID 534545cf. |
| R05 | Đếm thêm năm ảnh thiếu | INVENTORY: Là tập con 18 record cũ, không cộng thêm report. |
| R06 | Gán console chung thành nguyên nhân | C17 đã bỏ theo owner 17/10/2026: Không đủ căn cứ để quy nguyên nhân cho từng record hoặc suy nguyên nhân chung. |
| R07 | Thiếu message/payload gốc | C17 đã bỏ theo owner 17/10/2026: Ghi lỗ hổng bằng chứng, không bịa mã backend. |
| R08 | Gọi formatter lỗi là crash app | C03: Chỉ khẳng định nhánh trình bày bị ảnh hưởng. |
| R09 | Suy CSS không bao giờ chồng | INVENTORY: Loại fixture không chứng minh mọi bố cục đúng. |
| R10 | Có 12 chứ không 11 note mất | C17 đã bỏ theo owner 17/10/2026: Giữ đủ 12 UUID độc lập. |
| R11 | Múi giờ mtime không rõ | INVENTORY: Giữ UTC và giới hạn mtime sau copy. |
| R12 | Cụm cũ gồm control khác nhau | C17 đã bỏ theo owner 17/10/2026: Khôi phục từng triệu chứng, không đoán lỗi bảng chung. |
| R13 | Nhận xét alias trùng lặp | C03: Cùng safeguard R01, không thêm defect. |
| R14 | Nhận xét catalog trùng lặp | C03: Cùng safeguard R02. |
| R15 | Nhận xét nhánh lưu trùng lặp | C03: Cùng safeguard R03. |

Review SOT lịch sử tách khỏi report: mất nguồn/thân decision/title → C14; tham chiếu hiện hành → C15 nếu còn áp dụng; claim build/config/exclude cũ giữ lịch sử/chưa xác minh tới kiểm deployment có mục tiêu C16. Sáu nhận xét đã bác bỏ giữ bác bỏ nếu không có bằng chứng mới.

## Parked và loại khỏi yêu cầu

- **PARKED, chưa duyệt implementation:** OCR local dài hạn; không QR/local rescue.
- **PARKED:** Zalo nghiên cứu/pháp lý riêng, không suy quyền sync/ACK/tự liên kết từ thiết kế cũ.
- **PARKED:** mở rộng Tra cứu chung/Cài đặt chưa chọn nguồn/phạm vi; không coi màn hiện có vắng mặt. C19 Danh sách hồ sơ là việc khác.
- **PARKED:** nghiệp vụ/công thức thừa kế Draft rộng hơn; chốt incomplete không duyệt toàn bộ. **C13 Office DEFERRED theo owner 17/10/2026**, không giao pilot/phép đo; giữ Draft để làm sau. **C18 tab Word authoring DEFERRED 17/10/2026**, owner tự làm sau, cần spec kỹ trước implementation tương lai; không giao đặc tả/code hoặc hỏi lại lúc này.
- **PARKED:** retire Qt/web cũ sau nghiệm thu package và chọn cutover; không xóa archive hàng loạt.
- **C11 đã ghi bằng chứng, thay đổi còn chờ nguồn:** đáp án mẫu F04/F05 và phép đo OCR/nhóm còn thiếu nguồn thật/nhãn độc lập; chỉ công việc thay hành vi phụ thuộc chúng bị chặn. Từ điển/thuật toán chuẩn hóa tiếng Việt, classifier fallback, gộp ảnh mới và decision72/editor tách–gộp chưa được duyệt; không nâng Draft/Pending hoặc tạo gate owner cho lượt ghi bằng chứng #12. Nguồn hành chính cùng ngày vẫn riêng C26/#27.
- **C08 chưa xác minh:** retention/dọn thủ công DOCX, khôi phục DB+docx_sources cùng bản sao, cài sạch, FS được hỗ trợ và nhìn từng trang Word. Không chính sách tự xóa hoặc nghiệm thu toàn bộ bằng API tổng hợp.
- **LOẠI:** toàn bộ thiết kế theo dõi bản in, connector/bảng/ví dụ.
- **LOẠI:** phục hồi tên người chết từ tên viết tắt/initial; không mở lại thành tính năng hay câu hỏi.

## Bằng chứng và kiểm độc lập

Inventory private ignored ở `_bmad-output/tmp/issues-reconciliation-20261015/report-inventory.json` và `.md`; matrix/priority-review cùng thư mục. Không chép raw note, PII, secret hoặc ảnh vào issue được theo dõi.
164 record khác nhau = 37 lịch sử + 7 mới + 120 kiểm chứng sinh ra. Phân loại: 145 fixture/check không là bằng chứng defect production, 12 triệu chứng lịch sử chưa xác minh (**issue đã bỏ theo quyết định owner 17/10/2026** — [decision](../decisions/decision-owner-remove-historical-report-issue-20261017.md); không còn là việc đang mở và không chờ đầu vào), 7 report hiện tại còn mở. 37 bản export embedded là bản sao, không UUID mới. Cờ synthetic cũ từng gán mặc định, không đủ bác bỏ 12 thao tác có thể do người dùng.
Bằng chứng service/API tổng hợp cũ chỉ phủ phạm vi đã chạy. Kiểm đường Word thật khác mock generic run-dev. Chứng minh hành vi không đổi đã đúng chỉ giải quyết claim chưa xác minh; không bỏ yêu cầu hành vi mới.
Coverage-map/status/next và artifact checks ở tmp cùng phiên. Cần reviewer độc lập trước commit/publish; không chạy test/build ứng dụng trong authoring.
