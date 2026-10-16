# Catalog issue — 15/10/2026

**Catalog status (2026-10-16):** #4, #5, #6, #7, and #28 are built within their approved scopes; this does not approve or complete the rest of the backlog or publish the catalog. Other issue statuses remain as listed; #1 is history/tracking-only and #11/#26 remain dropped. No active initiative change. [Quyết định cách theo dõi](../decisions/decision-issues-reconciliation-20261015.md). The separate pre-existing #28 UI `file_token` blocker remains deferred and is not claimed fixed. C22/#23 is superseded by the 2026-10-16 owner decision (rule management is developer-only); C07/#8's business question is answered with remaining choices technical.

## Ưu tiên, thứ tự và điều kiện bắt đầu

P1/P2 là ưu tiên đề xuất, không phải severity hay thứ tự ID. Cần refinement/approval trước implementation; spike chỉ nhận quyết định/bằng chứng. **Hard after: #22 ← #7; #23 ← #8 và #22; #25 ← #3.** Cạnh #7→#22 chỉ tuần tự hóa sửa cùng core, không thêm gate nghiệp vụ; #7 không chờ full parity. Không chặn pilot Office bởi DB vật lý chung hoặc nghiệm thu Word thật bởi naming. #27 về nguồn hành chính vẫn độc lập với #12. #11/#26 dropped theo quyết định owner; #28 không có hard after. #23 superseded 16/10/2026 (rule do developer quản lý) nên cạnh #23 ← #8/#22 chỉ còn lịch sử.

| Candidate / ID | Issue | Nhóm | Ưu tiên | Hard after | Sẵn sàng |
|---|---|---|---|---|---|
| C01 / #2 | [Không gian Stage, Pool và Diagram liền mạch, dễ thao tác](story-notary-workspace-continuity.md) | bug/report đã báo | P2 | không | 6/6 report đã built (18ae/b541/2c232/e86/ac5 + 802 sàn chiều cao 726px, geometry thật chứng minh; Node 193 pass/0 fail, adapter 83 pass, GUI gói default 0 fail + đóng sạch; independent Quick t1 patch thông báo dài + t2 clean) |
| C02 / #3 | [Chốt quy tắc đổi loại hồ sơ đã lưu](spike-saved-case-conversion-semantics.md) | quyết định | P1 | không | lập kế hoạch/bằng chứng |
| C03 / #4 | [Sơ đồ không hiển thị đúng thông báo khi gặp lỗi](bug-diagram-error-messages.md) | bug/report đã báo | P1 | không | built (2026-10-16; independent Quick review clean, no findings) |
| C04 / #5 | [Lưu và mở lại sơ đồ hợp lệ còn thiếu dữ liệu](story-save-valid-incomplete-diagram.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; full Notary 1115 passed, 2 skipped; scoped checks 41 + 239 passed, 2 skipped; diagram Node 30 passed; Electron 21/21; independent Quick t3 clean) |
| C05 / #6 | [Giữ nguyên độ đầy đủ của ngày qua lưu và xuất](story-preserve-year-only-precision.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; Q1 medium-risk fallback patch fixed and clean on recheck; no outstanding business decision) |
| C06 / #7 | [Regex bỏ sót serial nguyên văn và địa chỉ thửa có nhãn](bug-regex-raw-serial-parcel-address.md) | bug/report đã báo | P1 | không | built (2026-10-16; transfer profile 1.1.3; Notary full suite 1113 passed, 2 skipped, 115 warnings, 2 subtests on short basetemp; workbench 45 passed, 18 subtests; independent Quick review clean) |
| C07 / #8 | [Chốt vòng đời thử, công bố và chạy lại rule regex](spike-regex-rule-lifecycle.md) | quyết định | P1 | không | answered 2026-10-16 (owner: rule developer-only, có phân biệt phiên bản; người dùng không dùng tính năng); phần còn lại là lựa chọn kỹ thuật |
| C08 / #9 | [Kiểm chứng đường xuất Word thật và nguồn mẫu](spike-word-real-route-acceptance.md) | bằng chứng | P1 | không | spike answered 2026-10-16 (retained Quick t2 clean; native/Word visual not accepted; direct batch 2 + paired restore case 3 proof) |
| C09 / #10 | [Đối chiếu phạm vi quy tắc tên entities với hướng dẫn mẫu Word](spike-word-naming-authority.md) | bằng chứng | P2 | không | lập kế hoạch/bằng chứng |
| C10 / #11 | [Kết quả Lưu portal bị lệch khi đóng tab hoặc mất phản hồi](bug-upload-save-reconciliation.md) | bug/report đã báo — dropped | P1 lịch sử | không | DROPPED theo quyết định owner; giữ leaf/plan lịch sử, thay phạm vi bằng C27/#28 |
| C11 / #12 | [Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở](spike-extraction-source-policy-evidence.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C12 / #13 | [Chốt DB vật lý và contract chuyển dữ liệu liên module](spike-shared-data-transfer-boundary.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C13 / #14 | [Chốt phạm vi và tiêu chí pilot NotaryOffice](spike-office-pilot-scope.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C14 / #15 | [Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại](spike-decision-source-gaps.md) | bằng chứng | P2 | không | lập kế hoạch/bằng chứng |
| C15 / #16 | [Sửa tham chiếu không còn đúng trong spec đang dùng](story-canonical-spec-references.md) | khoảng lệch đã chọn | P2 | không | có thể refinement, không cần chọn lại hướng nghiệp vụ |
| C16 / #17 | [Chuyển desktop sang bản Electron còn được hỗ trợ](story-supported-electron-release.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; independent Quick t2 clean; Electron 44.7.2/builder 24.13.3; 2,975-file snapshot proves startup/IPC `G1_SMOKE` only; public picker→`file.inspect` matched size/hash. Upload UI `upload.audit_excel` still fails on blank `file_ref.path`; production `--case offline` failed at `upload.scan` before its own snapshot; test `--case all` timed out after `upload.download_export`. Full Upload E2E is not green (xem plan/spec) |

| C17 / #18 | [Khôi phục bằng chứng và phân loại 12 report mất ghi chú](spike-historical-report-note-triage.md) | bằng chứng | P2 | không | lập kế hoạch/bằng chứng |
| C18 / #19 | [Đặc tả tab Word tạo và lưu mẫu](spike-word-tab-authoring-scope.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C19 / #20 | [Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ](spike-case-list-query-labels.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C20 / #21 | [Chốt xử lý nhánh khi xóa nút giữa sơ đồ thừa kế](spike-inheritance-middle-node-deletion.md) | quyết định | P2 | không | lập kế hoạch/bằng chứng |
| C21 / #22 | [Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi](story-shared-regex-consumer-cutover.md) | khoảng lệch đã chọn | P2 | #7 | chờ tuần tự sửa core, không chọn lại nghiệp vụ; #23 superseded 16/10/2026, parity không đổi |
| C22 / #23 | [Thử và công bố rule regex rồi duyệt kết quả chạy lại trong flow](story-in-flow-regex-publication-review.md) | khoảng lệch đã chọn | P2 | #8, #22 | SUPERSEDED 2026-10-16 theo quyết định owner (rule do developer quản lý; người dùng không dùng tính năng); giữ lịch sử, không triển khai |
| C23 / #24 | [Xuất Word theo dữ liệu mẫu thực sự cần, cho phép điền dần](story-gradual-fill-word-readiness.md) | khoảng lệch đã chọn | P1 | không | built (2026-10-16; gate nhóm theo token mẫu thực dùng cho folder+legacy; before/after engine 523608a + UI packaged non-native picker; adapter cutover sidecar-only; Quick t1 finding fixed + recheck clean) |
| C24 / #25 | [Đổi loại hồ sơ đã lưu theo quy tắc đã chốt](story-saved-case-type-conversion.md) | khoảng lệch đã chọn | P2 | #3 | draft có gate; xem dưới |
| C25 / #26 | [Kiểm chứng ý nghĩa tín hiệu Lưu trên portal thật](spike-upload-real-save-signal-validation.md) | bằng chứng — dropped | P1 lịch sử | không | DROPPED; không còn là gate ngữ nghĩa portal cho cutover |
| C26 / #27 | [Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày](spike-administrative-same-day-evidence.md) | bằng chứng | P2 | không | chỉ nghiên cứu văn bản, không đổi thuật toán |
| C27 / #28 | [Bỏ theo dõi kết quả Lưu và giữ tiến độ chuẩn bị theo lượt](story-upload-web-official-sot-cutover.md) | khoảng lệch theo quyết định owner | P1 | không | built (2026-10-16; UI E2E remains blocked by the deferred pre-existing `file_token` mismatch) |

Khuyến nghị hiện hành, không phải lệnh triển khai: (1) #28 cutover đã được owner chốt và #4 formatter, #6 độ đầy đủ ngày, #7 field extraction, #5 lưu incomplete, #17 nền desktop đã built; #11 cũ đã dropped; vị trí đầu của #28 là đề xuất điều phối, không phải phần của lựa chọn A ban đầu; (2) #2 workspace đã built (trục 802 owner đã chốt: chiều cao, sàn 726px; Quick t2 clean); #9 nghiệm thu Word thật đã answered; #24 readiness điền dần đã built (Quick t1 clean sau vá nhãn readiness); (3) #22 parity tiếp tục (không đổi); #23 đã superseded theo quyết định owner 16/10/2026 (rule developer-only); (4) #25 khi #3 chốt semantics. Các việc nguồn/docs/quyết định độc lập có thể được đánh giá cùng lúc. Cần refinement/approval trước implementation.

## Câu hỏi còn mở và phần đã rõ

- **C01 / #2:** 802 đã làm theo quyết định owner (trả lời '1'): tăng CHIỀU CAO vùng Sơ đồ + Pool — sàn 726px từ baseline 484px của report, không đổi chiều rộng; geometry thật trên gói default xác nhận (thừa kế diagram 236→726px, khối gộp `.cd-rel-body` 244→734px; Hai bên giữ nguyên theo nội dung). 6/6 report đã built; independent Quick t1 (patch thông báo dài) + t2 clean.
- **C02 / #3:** Khi đổi loại hồ sơ đã lưu, gán người, quyền sở hữu, lựa chọn văn bản và binding được giữ hay chuyển thế nào? Chuyển nào bị cấm; cần xem trước/xác nhận gì?
- **C07 / #8 (answered 16/10/2026):** owner chốt rule regex văn bản và rule upload theo website do developer quản lý, có phân biệt phiên bản để nhận biết; người dùng sản phẩm không dùng tính năng này. Người dùng vẫn xem/sửa kết quả bóc tách trước khi nhận vào Stage. Phần cơ chế (nơi lưu, format, version/hash, kích hoạt/quay lui nội bộ, phạm vi chạy lại) là lựa chọn kỹ thuật của developer, không còn câu hỏi nghiệp vụ. [Decision](../decisions/decision-owner-regex-rule-developer-only-20261016.md).
- **C08 / #9 (answered 16/10/2026):** evidence đã trả lời — direct `word_batch_export` batch 2 mẫu + paired DB/`docx_sources` restore với ca 3 là bằng chứng sau khi dừng app; retained Quick t2 clean. Còn là **giới hạn capability**: native picker/renderer transport, kiểm trang Word thật và cài sạch/máy khác/non-NTFS chưa nghiệm thu; không thử phá dữ liệu production.
- **C09 / #10:** Quy định tên viết liền bắt buộc tại entities §9.1 chỉ áp cho tên trường nghiệp vụ hay cả placeholder và có lấn hướng dẫn Word §4.1 không? Đối chiếu nguồn đã có trước; chỉ hỏi owner nếu đúng điểm thẩm quyền này còn thiếu căn cứ.
- **C11 / #12:** Đáp án từng trường của các nguồn mâu thuẫn là gì? Có chọn quy tắc mới nào cho gộp nguồn/gộp ảnh, chuẩn hóa tiếng Việt hoặc classifier fallback sau khi đọc bằng chứng không? Không bao gồm nghiên cứu hành chính #27.
- **C12 / #13:** Với lần chuyển liên module cụ thể, ai sở hữu từng lần ghi, payload/xác nhận nào được duyệt, chọn DB vật lý/migration nào trước schema production?
- **C13 / #14:** Giao pilot lúc này hay giữ Draft? Những phép đo Word đang mở, sự kiện ổ mạng, tài khoản người dùng, ví dụ nhóm việc, quyền/retention và tiêu chí người dùng nào xác định pilot?
- **C14 / #15:** Sau khi đọc nguồn hiện hành, quy tắc quan trọng nào vẫn thiếu bằng chứng? Original task-3/decision48 còn ở đâu ngoài tombstone, và đúng việc nào thật sự bị thiếu nguồn đó chặn?
- **C17 / #18:** Với từng UUID vẫn không còn triệu chứng sau khi đọc nguồn sẵn có, người báo gốc có thể bổ sung triệu chứng/kết quả mong đợi không? Không phát lại để bác bỏ phản ánh.
- **C18 / #19:** Định dạng nguồn, đề xuất/duyệt, catalog/quyền lưu mẫu và tiêu chí phát hành nào xác định tab Word riêng?
- **C19 / #20:** Chọn nhãn/trạng thái, trường nguồn và luật tìm/lọc nào, gồm người tạo/tên/ngày và trạng thái rỗng/lỗi?
- **C20 / #21:** Sau khi báo các con/quan hệ bị ảnh hưởng, nhánh nào giữ, tách hay xóa; xác nhận/hủy ra sao và lưu/mở lại state canonical thế nào?
- **C23 / #24 (built 16/10/2026; Quick t1 finding vá nhãn readiness + recheck clean):** phạm vi nới đã chốt bằng code + spec/contract: gate nhóm (`no_landowner`/`no_deceased_landowner`/`no_receiver` và `no_diagram` hai bên) chỉ áp theo token mẫu thực dùng — nhận diện theo registry key engine sinh, catalog legacy theo mẫu từng `document_key`, folder mode giữ semantics nhóm thiếu để trống; giới hạn kỹ thuật, unresolved-slot và người được ủy quyền mẫu cần giữ nguyên. Bằng chứng before/after (engine 523608a cô lập) + UI packaged trong `_bmad-output/tmp/issue-24-word-readiness/evidence/`; independent Quick chạy sau.
- **C09 đã rõ:** ngoặc vuông, tên nhóm dễ đọc cho mẫu mới, tên viết liền hỗ trợ và alias cũ theo Word §4.1. #10 chỉ đối chiếu phạm vi câu bắt buộc tên viết liền trong entities §9.1; không hỏi lại cú pháp, không thêm hỗ trợ/migration/phát hiện ngoặc nhọn.
- **C16 / #17 — BUILT:** Runtime/IPC/picker evidence and limitations are recorded in [runtime record](../specs/shell/electron-runtime-support.md); full Upload paths remain failed/incomplete, not a blocker to the scoped runtime-support result.
- **C22 / #23 — SUPERSEDED 16/10/2026:** owner chốt rule do developer quản lý; không có UI người dùng thử/công bố/chọn phiên bản/rollback. Leaf giữ lịch sử; luồng duyệt kết quả bóc tách trước Stage giữ nguyên.
- **C24 / #25:** nhu cầu đổi loại đã được report yêu cầu; chỉ chờ semantics #3, nhất là giữ hay reset gán người. Giữ runtime bất biến tới khi contract chuyển đổi duyệt.
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
- `d9da640e-43fd-435e-b892-f05b517eff1f` — Không sửa được loại hồ sơ đã lưu → C02/#3 rồi C24/#25; còn mở.
- `e86a02bb-9e67-48ba-a14a-46b787553231` — Ô Hai bên dẹt, khó thả → C01/#2; đã xử lý (ô 202×52, giữ p1..p30).

## Mười hai report lịch sử mất ghi chú — C17 / #18

Một việc khôi phục bằng chứng; từng UUID là một triệu chứng chưa xác minh riêng. Console/selector chung không đủ suy root cause. Chỉ hỏi người báo phần thật sự đã mất sau khi đọc provenance còn lại.

- `0d1b1ff1-73ce-4e8b-a6bf-2c695f06dd3f` — chưa xác minh, giữ riêng.
- `2f352897-ab9b-4f11-84e4-a44c43145bf0` — chưa xác minh, giữ riêng.
- `377d8486-e885-4a21-8e84-497241546eaa` — chưa xác minh, giữ riêng.
- `534545cf-f020-4e22-8e03-362294f72508` — chưa xác minh, giữ riêng.
- `5db58074-cf8b-4a67-ab5a-09c0dd449a94` — chưa xác minh, giữ riêng.
- `60e02a79-727d-4de3-be7f-488b3f1a39ee` — chưa xác minh, giữ riêng.
- `643496a0-c4a4-4e5a-ab2f-bbbfa39d438a` — chưa xác minh, giữ riêng.
- `6714de6f-0049-4b4c-8d0d-2a2b179f15d9` — chưa xác minh, giữ riêng.
- `aaf29f16-68b4-4a92-b15c-b811043d9c80` — chưa xác minh, giữ riêng.
- `b5999b39-dce5-48dc-954a-66d231cce6ee` — chưa xác minh, giữ riêng.
- `bb496551-82b6-4f72-bd80-77df2e396e2f` — chưa xác minh, giữ riêng.
- `e3bba3ef-0f1f-4730-a505-cf0d282b75b1` — chưa xác minh, giữ riêng.

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
| R04 | Bỏ sót report toàn vùng | C17: Giữ riêng UUID 534545cf. |
| R05 | Đếm thêm năm ảnh thiếu | INVENTORY: Là tập con 18 record cũ, không cộng thêm report. |
| R06 | Gán console chung thành nguyên nhân | C17: Không suy root cause chung. |
| R07 | Thiếu message/payload gốc | C17: Ghi lỗ hổng bằng chứng, không bịa mã backend. |
| R08 | Gọi formatter lỗi là crash app | C03: Chỉ khẳng định nhánh trình bày bị ảnh hưởng. |
| R09 | Suy CSS không bao giờ chồng | INVENTORY: Loại fixture không chứng minh mọi bố cục đúng. |
| R10 | Có 12 chứ không 11 note mất | C17: Giữ đủ 12 UUID độc lập. |
| R11 | Múi giờ mtime không rõ | INVENTORY: Giữ UTC và giới hạn mtime sau copy. |
| R12 | Cụm cũ gồm control khác nhau | C17: Khôi phục từng triệu chứng, không đoán lỗi bảng chung. |
| R13 | Nhận xét alias trùng lặp | C03: Cùng safeguard R01, không thêm defect. |
| R14 | Nhận xét catalog trùng lặp | C03: Cùng safeguard R02. |
| R15 | Nhận xét nhánh lưu trùng lặp | C03: Cùng safeguard R03. |

Review SOT lịch sử tách khỏi report: mất nguồn/thân decision/title → C14; tham chiếu hiện hành → C15 nếu còn áp dụng; claim build/config/exclude cũ giữ lịch sử/chưa xác minh tới kiểm deployment có mục tiêu C16. Sáu nhận xét đã bác bỏ giữ bác bỏ nếu không có bằng chứng mới.

## Parked và loại khỏi yêu cầu

- **PARKED, chưa duyệt implementation:** OCR local dài hạn; không QR/local rescue.
- **PARKED:** Zalo nghiên cứu/pháp lý riêng, không suy quyền sync/ACK/tự liên kết từ thiết kế cũ.
- **PARKED:** mở rộng Tra cứu chung/Cài đặt chưa chọn nguồn/phạm vi; không coi màn hiện có vắng mặt. C19 Danh sách hồ sơ là việc khác.
- **PARKED:** nghiệp vụ/công thức thừa kế Draft rộng hơn; chốt incomplete không duyệt toàn bộ. C13 pilot Office/C18 tab Word chỉ lập kế hoạch.
- **PARKED:** retire Qt/web cũ sau nghiệm thu package và chọn cutover; không xóa archive hàng loạt.
- **C11 có gate cụ thể:** từ điển/thuật toán chuẩn hóa tiếng Việt OCR, classifier fallback, gộp ảnh so với output contract, decision72 và đáp án nguồn mâu thuẫn. Chưa chọn thuật toán mới. Nguồn hành chính cùng ngày chuyển riêng sang C26/#27.
- **C08 chưa xác minh:** retention/dọn thủ công DOCX, khôi phục DB+docx_sources cùng bản sao, cài sạch, FS được hỗ trợ và nhìn từng trang Word. Không chính sách tự xóa hoặc nghiệm thu toàn bộ bằng API tổng hợp.
- **LOẠI:** toàn bộ thiết kế theo dõi bản in, connector/bảng/ví dụ.
- **LOẠI:** phục hồi tên người chết từ tên viết tắt/initial; không mở lại thành tính năng hay câu hỏi.

## Bằng chứng và kiểm độc lập

Inventory private ignored ở `_bmad-output/tmp/issues-reconciliation-20261015/report-inventory.json` và `.md`; matrix/priority-review cùng thư mục. Không chép raw note, PII, secret hoặc ảnh vào issue được theo dõi.
164 record khác nhau = 37 lịch sử + 7 mới + 120 kiểm chứng sinh ra. Phân loại: 145 fixture/check không là bằng chứng defect production, 12 triệu chứng lịch sử chưa xác minh, 7 report hiện tại còn mở. 37 bản export embedded là bản sao, không UUID mới. Cờ synthetic cũ từng gán mặc định, không đủ bác bỏ 12 thao tác có thể do người dùng.
Bằng chứng service/API tổng hợp cũ chỉ phủ phạm vi đã chạy. Kiểm đường Word thật khác mock generic run-dev. Chứng minh hành vi không đổi đã đúng chỉ giải quyết claim chưa xác minh; không bỏ yêu cầu hành vi mới.
Coverage-map/status/next và artifact checks ở tmp cùng phiên. Cần reviewer độc lập trước commit/publish; không chạy test/build ứng dụng trong authoring.
