# Sổ tay sản phẩm theo màn hình

**Cập nhật:** 20/10/2026 · **Dùng để:** giúp owner và coordinator cùng nhìn
vào sản phẩm, giao diện và việc còn dở khi bắt đầu phiên làm việc.

Đọc [nền sản phẩm và khái niệm chung](README.md) trước để hiểu người dùng,
ba kết quả và nghĩa các từ dùng chung. Trang này là bản đồ ngắn để tìm đúng
màn hình, tài liệu và điểm vào mã, đồng thời ghi việc đang mở. Spec trong
`_bmad-output/specs/` quyết định hành vi; code cho biết hiện trạng. Có mã nguồn
không đồng nghĩa đã nghiệm thu trên ứng dụng. Hãy kiểm tra lại nguồn mới nhất
trước khi bắt tay vào việc.

## Đường đọc sau khi gom spec

Soạn thảo có một spec luồng và hai phần chuyên sâu Sơ đồ/Word. Upload và NotaryOffice mỗi module một spec chính. Quy tắc dữ liệu, bóc tách, OCR và địa chỉ nằm trong shared; chỉ mở đúng phần cần làm. Spec viết đủ hành vi; decision giữ lý do và phương án bỏ. Issue/task bền vững ở backlog; bản ghi tạm ở tmp. Bản cũ trong archive không nạp mặc định.

## Mục tiêu và việc đang mở

Sản phẩm hỗ trợ văn phòng công chứng giảm nhập liệu lặp lại qua ba hướng:

1. **Soạn hồ sơ mới:** đọc giấy tờ, cho chuyên viên kiểm tra dữ liệu, lập quan
   hệ và xuất Word.
2. **Số hóa hồ sơ cũ:** đọc Word, so với dữ liệu chính thức của website và
   chuẩn bị biểu mẫu để chuyên viên tự kiểm tra, tự quyết định Lưu. Dữ liệu đã
   được website ghi nhận chính thức là SOT; app không suy kết quả Lưu từ browser.
3. **Theo dõi vận hành:** dự kiến cho biết hồ sơ đang ở đâu và chờ việc gì;
   hiện mới có thiết kế, chưa có chương trình chạy.

**Định hướng hồ sơ thử — owner 19/10/2026:** folder `D:\testcase`, đọc
[README chung](file:///D:/testcase/README.md) và
[context từng loại](notary_v2/README.md#context-ho-so-thu).
Mọi luồng dùng dữ liệu chuẩn Người–Tài sản–Hồ sơ; hiện **chỉ ghi tài liệu**,
chưa tạo Word/corpus hoặc chạy E2E. Vị trí người nhận trong cấu trúc Di chúc
cần nhận diện từ mẫu, không phải quyết định ghế Diagram; thế chấp ngân hàng
cung cấp nội dung, văn phòng chỉ soạn lời chứng và input
luôn thiếu thông tin tài sản; mua bán xe chỉ ghi
[#29 DEFERRED](../backlog/spike-vehicle-sale-case-scope.md), hiện không làm.
[Decision](../decisions/decision-owner-case-context-standard-data-20261019.md).
**Gate mới — owner 19/10/2026:** mọi future sample batch/khảo sát mẫu thực,
corpus và E2E theo mẫu chờ
[#41 chuẩn hóa toàn bộ trường Upload](../backlog/story-upload-business-field-standardization.md)
được nghiệm thu chuẩn DB/contract, cutover và proof consumer thật, không chỉ
bảng mapping. Proof riêng #41 khi được giao dùng input tổng hợp/kiểm soát
cô lập, không cần quét corpus owner để đóng gate. Không tắt Scan/Upload
production. Chủ đất thuộc **Hồ sơ**, không Tài sản cố định/node `owner` Thừa kế;
thông tin công chứng thuộc Hồ sơ, khác ngày tạo. Key/kiểu/cardinality chưa
chọn; inventory gồm số/ngày công chứng, công chứng viên, thư ký và mọi trường.
Không bóc/chuẩn hóa thông tin giá/cọc/thuê/vay/lãi/thanh toán hoặc thời hạn
nghiệp vụ; vẫn giữ thời hạn đất và timeout kỹ thuật. Portal cần trường đã loại
thì ghi xung đột để refine, không bịa/default hay tự chọn bước nhập tay.
[#42 Người nhiều giấy tờ và địa chỉ](../backlog/story-person-multiple-identities-addresses.md)
là issue riêng, model tương lai chưa chọn, không tự là prerequisite #41.
**Pháp nhân (owner 20/10/2026):** không đưa vào Người; policy nhập tay chung
có ngoại lệ ngân hàng thế chấp **app tự lấy** bên dưới. Bảng riêng tương lai
chưa duyệt schema/build; không bịa/default. **Cụm trường phụ website** theo hướng owner cho phép có điều kiện cho một ô
cụ thể (phức tạp, không lặp lại); chưa chọn ô/cấu trúc nào và không tự biến editor
thành block. Quan hệ nhiều người/nhiều tài sản chưa chọn model/cardinality;
D06+D07 chuyển [#43 riêng](../backlog/spike-case-people-assets-relationships.md),
làm ngay sau làm rõ các ô Nam Định §7, không chờ toàn #41 xong/#42.
[Quyết định](../decisions/decision-owner-upload-field-standardization-20261019.md).
**Đáp án #43 — owner 20/10/2026:** requester Nam Định/Upload gồm cá nhân sống
A/B/đại diện theo ủy quyền; không người chết/CCV/nhân viên trong output đó,
không xóa Person chết/Stage/Hồ sơ thừa kế/raw/history. Cá nhân vẫn dữ kiện
chuẩn, alias manual, D04/D08 không prose/lookup/firstperson. Ngân hàng thế
chấp hiện cả cụm, không Person; **BANKMODE đã chốt “app tự lấy”**: toàn cụm có
nguồn ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/ủy quyền, chỉ thế chấp.
Requester giữ mọi cá nhân sống thực sự tham gia theo thứ tự nguồn, đặt cụm
ngân hàng đúng vị trí, không lặp đại diện đã nằm trong cụm. Cá nhân khác chuẩn.
`web_form.nguoi_yeu_cau` → payload JSON → queue → editor là persistence
projection hiện có hợp lệ, không thêm canonical field/schema. A/B đã chốt:
ủy quyền A=ủy quyền/B=được ủy quyền, một bên không gán, conflict nhóm không
winner/thu hẹp requester. #43 giữ đủ 16 ca, Q1/Q2/BANKMODE đủ đáp án và bàn
giao #41; không còn bank owner gate, không tuyên bố #41 cutover xong. Requester không
cần tag A/B đã gán: cá nhân sống một bên/đại diện ủy quyền vẫn vào khi nhóm
không gán/conflict. W05
đã chốt: giữ ID1 đất có tài sản/nhà; hồ sơ có thửa nhà + thửa trống chọn ID1
khi có bằng chứng gắn liền đất, chỉ phạm vi đất-nhà/đất-trống, không ưu tiên
phổ quát trên loại khác. D05 chọn nhóm A/B chung, chữ “nhận” gần như 100% không luật
tuyệt đối. A09 đã chốt A: không residual field/block, chỉ render canonical/
placeholder; raw/history retained không auto-fill. [SOT §7.5.1](upload_lab/nam-dinh-website-sot.md)
lưu trường thật/ví dụ tổng hợp GCN/thửa/cụm đất. A10 nhận diện/pending structured,
#29 deferred; không loại đất có nhà. **Owner 20/10/2026 chốt chỉ dùng
placeholder và trường tĩnh**; không mở trường tầng 2 động/tính toán, text
canonical persisted từ suy ra, engine công thức hoặc framework điều kiện.
Quyền có điều kiện cho cụm **text tĩnh** đã duyệt khác vẫn giữ; **A09 đã chốt A**
không residual field, chỉ render canonical/placeholder. Dữ kiện nguồn tĩnh khác
lớp định dạng output/placeholder.
Bounded local proof đã có, fresh bank-auto review CLEAN/Ticket PASS; #43 phân
tích done/bàn giao. Không toàn normalized cutover #41, #41 mở/gate mẫu ĐÓNG.
**BUILT — slice metadata Case, 19/10/2026; verification đạt, Quick code độc lập
sạch sau fix được chấp nhận, tài liệu hoàn tất:** tám
trường canonical đã đi qua extraction, lưu/đọc lại, builder và preSave consumer.
Chủ đất là **“người được gán chủ đất trong diagram”**: lựa chọn Chủ
`ownPositions` đã lưu, tên snapshot Stage theo ID, không mặc định slot
owner/người chết. Upload không có Diagram là null. Catalog ở entities §9.4.
Proof tổng hợp DOCX/SQLite/fresh reopen/local Chromium đã đạt; Quick code sạch
sau sửa ghi nhân sự chỉ cho record thực sự prepare (queue read không ghi).
Không claim portal thật có đăng nhập, packaging hoặc corpus accuracy.
Person/Asset/parties chưa cutover; **toàn #41 chưa hoàn thành, gate mẫu ĐÓNG**.
Sau gate và khi được giao, quy trình là **LLM đọc hàng loạt mẫu → nhận diện cấu trúc
→ so code → điều chỉnh code → test lại, sai thì lặp**, nhằm xuất đủ, đúng thông
tin hợp đồng. Issue riêng theo cấu trúc chưa chốt #30–#38;
[#39 tổng hợp văn bản lạ](../backlog/spike-unfamiliar-document-review-queue.md)
để owner xem sau, không chặn các file đã rõ. Không phải lệnh bắt đầu chạy lô.
Đọc/cập nhật [báo cáo khảo sát ổn định](file:///D:/testcase/BAO_CAO_KHAO_SAT.md)
trước/sau mỗi lô; audit trường chuẩn và mapping từng biến thể trước claim đủ
đúng. Catalog nền chưa đủ trường Hồ sơ/Upload và không chứng minh đã khảo sát
nội dung mẫu.

Việc đang mở được tổng hợp tại [catalog issue](../backlog/README.md)
(16/10/2026; #17 built after independent Quick t2 clean; Upload failures and proof limits remain in the catalog/runtime record).
[Ticket tổng cũ](../backlog/bug-notary-flow-ui-regex-word.md) giữ làm lịch sử và bị chặn tracking-only để không chạy trùng các leaf. Các điểm chính:

- Đổi loại hồ sơ đã lưu **built 16/10/2026** (giữ Stage, reset Diagram, chọn văn bản mới + xác nhận — [decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)). [#25](../backlog/story-saved-case-type-conversion.md): command + dialog nguyên tử, smoke Electron/source IPC hai chiều và xuất DOCX thật; **independent Quick clean** — built.
- Sơ đồ/Stage: nhãn `Nơi chết`/`Nơi cấp giấy khai tử` theo bằng chứng (người đã mất thiếu bằng chứng vẫn `Nơi cấp giấy tờ`), Pool nội dung 224 (khung 240), ô Hai bên 202×52, thông báo tạm trong khoảng trống thanh trên (bám trên cùng khi vùng nội dung cuộn) không đẩy Sơ đồ; nút `Hủy thay đổi` của Stage đã gỡ, bảo vệ nháp giữ. Vùng Sơ đồ + Pool +50% chiều cao (802, đã chốt: sàn 726px từ baseline 484px, không đổi chiều rộng).
- Regex gợi ý intake (#7) và cutover **#22 built 16/10/2026**: Notary/Upload/tool dùng **một đường luật chung** `tools/regex_workbench/engine/contract_extract.py` (identity `contract_word`), adapter giữ IO/mapping và `source_refs` span nguồn. Serial nguyên văn, địa chỉ có nhãn, nhóm/cụm đất nhiều dòng được giữ; ô phẳng mâu thuẫn vẫn báo mơ hồ. Retained Quick t1 findings → các vòng vá Q1–Q7/MB1–MB9 → **retained Quick final multiline recheck clean 16Oct**, parent chấp nhận. Bằng chứng cuối: workbench **53 passed, 6 subtests**; intake + Word-first **130 passed, 2 subtests** + guard chuyển nhóm **1 passed**; Upload bounded **11 passed, 9 subtests**. So API **828 trường khớp / 0 lệch**, **44 null + 256 shape chưa kiểm**, F10/F11 unreviewed — không phải all-accuracy. Sidecar thật trên bundle đã stage chứng minh exact DOCX multiline + provenance, Upload scan 1/1/1; **native GUI DOCX chưa thực thi** (seam raw path/file_token). Full Notary 1139 passed/2 skipped là trước round 5–7, không claim full suite hiện tại. Dev Workbench UI giữ, gọi lõi thật; bỏ editor JSON profile lỗi thời. [#22](../backlog/story-shared-regex-consumer-cutover.md) · [bằng chứng](../tmp/issue-22-regex-consumer-cutover/evidence/EXECUTION-SUMMARY.md).
- Rule regex văn bản và rule upload theo website do developer quản lý, có phân biệt phiên bản để nhận biết; owner chốt 16/10/2026 người dùng sản phẩm không có tính năng thử/công bố/chọn phiên bản/rollback — [#23](../backlog/story-in-flow-regex-publication-review.md) superseded, [#8](../backlog/spike-regex-rule-lifecycle.md) đã có đáp án nghiệp vụ ([decision](../decisions/decision-owner-regex-rule-developer-only-20261016.md)).
- Giúp tìm mẫu Word và biết chỗ điền dữ liệu nào được hỗ trợ.
- Word #9 (đường xuất thật): evidence đã trả lời 16/10/2026 (direct batch + paired restore, bằng chứng sau khi dừng app là ca 3; retained Quick t2 clean); native picker/kiểm trang Word/cài sạch còn là giới hạn capability. [#9](../backlog/spike-word-real-route-acceptance.md).
- Word #24 (readiness điền dần): built 16/10/2026 (Quick t1 clean sau vá nhãn readiness) — gate nhóm (Chủ/Nhận, sơ đồ hai bên) chỉ áp theo token mẫu thực dùng, nhận diện theo registry key engine sinh; folder mode giữ nhóm thiếu để trống; bằng chứng before/after engine 523608a + UI packaged (seam picker non-native) trong `_bmad-output/tmp/issue-24-word-readiness/evidence/`; independent Quick chạy sau. [#24](../backlog/story-gradual-fill-word-readiness.md).
- Upload: đã bỏ theo dõi kết quả Lưu, runtime cutover 15/10/2026. [#28](../backlog/story-upload-web-official-sot-cutover.md).
- Desktop runtime (#17): manifest/lock dùng Electron `44.7.2`, builder `24.13.3`; production/test packages build, core tests, Notary IPC và Chromium loopback diagnostic đạt. Snapshot startup/sidecar smoke giữ nguyên 2,975 files; public picker token qua `file.inspect` khớp size/hash. Upload UI `file_ref.path`, production offline `file_token` và test `--case all` vẫn lỗi; chưa khẳng định full Upload E2E hay offline-flow immutability. Xem [runtime record](shell/electron-runtime-support.md).

- Sơ đồ: binding thông báo lỗi đã được sửa; có test hồi quy và probe trên
  Electron thật (client stub; không xác minh command IPC/engine), review Quick
  độc lập sạch. [#4](../backlog/bug-diagram-error-messages.md).
- Sơ đồ: lưu bản hợp lệ còn thiếu giữ warning Pool/`requiredSlots` qua mở lại;
  state `invalid` bị từ chối và giữ nguyên bản cũ; cue chỉ-đọc (trạng thái +
  phần thiếu) hiện khi panel cách tính đóng. Bằng chứng service/adapter và
  Electron thật (service thật, SQLite tạm) đạt; independent Quick t3 CLEAN,
  review xong. Smoke còn ghi nhận toast khởi động thoáng qua
  `engine_unavailable` khi mở danh sách; danh sách tự retry. Đây là giới hạn
  đã quan sát, không thuộc scope #5 và không được tuyên bố đã khắc phục.
  [#5](../backlog/story-save-valid-incomplete-diagram.md).
- Sơ đồ Thừa kế **#21B BUILT 17/10/2026** theo owner **“B - gỡ cả nhánh”**; retained Quick CODE t3 **No actionable findings**, parent accepted AC1–4. Node full 198 trước patch bỏ assertion chữ; affected file 25 sau patch, service 106 (24 warnings hiện có). Source Electron + real IPC/SQLite riêng đạt cảnh báo/dismiss/focus/atomic cut/Pool/Save invalid và fresh reopen exact. Không claim packaged/Word; startup toast `engine_unavailable` còn quan sát. #21 vẫn là spike nhận đáp án, không chứa implementation. [Proof](../tmp/issue-21b-branch-removal/evidence/ui-ipc-proof.json) · [Quy tắc](notary_v2/diagram-rules.md#branch-removal).
- Ngày Người giữ độ đầy đủ qua lưu/đọc/sửa/xuất Word: `2010` (chỉ năm) không
  bị đệm thành `01/01/2010`; snapshot hồ sơ là bằng chứng, master chỉ fallback
  khi snapshot cũ thiếu key. Đã sửa, test hồi quy và export DOCX thật đạt;
  review độc lập Quick sạch. [#6](../backlog/story-preserve-year-only-precision.md).

Đây là các hướng cần đánh giá theo ticket, không phải lệnh triển khai tự động.
Danh sách [deferred-work](../implementation-artifacts/deferred-work.md) là
lịch sử cần xác minh từng mục, không phải danh sách việc hiện đang mở.

## Menu chung

Menu gốc được khai báo tại [`NAV_SPEC`](../../shell/src/renderer/lib.js), rồi
hiển thị bởi [`renderSidebar`](../../shell/src/renderer/renderer.js). Menu có ba
module nghiệp vụ và hai tiện ích:

| Mục trên menu | Việc làm được | Tài liệu | Điểm vào mã |
|---|---|---|---|
| `notary_v2` | Soạn hồ sơ mới | [Module](notary_v2/README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildNotaryView` |
| `upload_lab` | Đọc hồ sơ cũ, audit sổ và chuẩn bị upload | [Module](upload_lab/README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildUploadView` |
| `notaryoffice` | Theo dõi hồ sơ — **thiết kế nháp, chưa có màn chạy** | [Thiết kế](notaryoffice/README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildOffice` |
| `Tra cứu` | Tìm kiếm chung — chưa có nguồn dữ liệu để tìm | [Tầm nhìn hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildSearch` |
| `Trạng thái/Cài đặt` | Xem kết nối, phiên bản, module, job, môi trường và diagnostics; phần Cài đặt hiện chỉ có thông tin | [Spec hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildStatus` |

## notary_v2 — Soạn hồ sơ mới

Flow chính: **Tổng quan hồ sơ → Soạn hồ sơ → Nhập liệu/gợi ý → Stage → Pool →
Diagram → Xuất Word.** Tab `Word` hiện chỉ có thông báo, chưa có chức năng
riêng; nút xuất nằm trong `Soạn hồ sơ`. Nút Zalo đang tắt. Mỗi dòng dưới đây
trỏ tới phần nhỏ để bắt đầu tìm hiểu.

**Tab Word tạo/lưu mẫu tương lai DEFERRED — owner 17/10/2026:** “chức năng này tôi sẽ tự làm sau, cần spec kỹ. Chuyển issue khác”. Cần spec chi tiết trước implementation tương lai; chưa giao viết spec hoặc code lúc này, các lựa chọn nguồn/bố cục/catalog/nghiệm thu chưa chốt. #19 đã nhận đáp án hoãn phạm vi, không built; chuyển #20, không hỏi tiếp #19. Nút Xuất Word và intake hiện có không bị hoãn. [Decision](../decisions/decision-owner-word-authoring-deferred-20261017.md).

**Danh sách hồ sơ (Tổng quan hồ sơ) làm lại — owner 17/10/2026:** owner “note lại phương hướng (chưa chốt chắc chắn)” và **sẽ tự triển khai spec sau**; chức năng **DEFERRED**, không giao code hoặc spec lúc này. Owner yêu cầu mọi input/output tuân theo chuẩn database; whitelist trường, mapping cụ thể và phạm vi request chưa chốt. Phần tentative **chưa duyệt**: trường hiển thị/search/filter, thẻ chia 3 vùng Người/Tài sản/Hồ sơ. Danh sách/tạo/mở hiện có không bị dừng. [#20](../backlog/spike-case-list-query-labels.md) · [Decision](../decisions/decision-owner-case-list-redesign-deferred-20261017.md).

| Màn / thao tác | Dùng để | Tài liệu | Điểm vào mã |
|---|---|---|---|
| Tổng quan: lọc hồ sơ | Thu hẹp danh sách | [Workspace](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `buildCaseListPanel` |
| Tổng quan: làm mới | Tải lại danh sách | [Workspace](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `buildCaseListPanel` |
| Tổng quan: tạo nháp | Chọn loại việc và mở hồ sơ mới | [Workspace](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `newDraftFlow` |
| Tổng quan: mở hồ sơ | Vào workspace đã lưu | [Workspace](notary_v2/README.md#stage) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `openCase` |
| Input: chọn file | Nhận ảnh, PDF, Word, Excel | [Input](notary_v2/README.md#input) | [intake-dialog.js](../../shell/src/renderer/notary/intake-dialog.js) · `createIntakeDialog` |
| Input: dán văn bản | Nhận chữ do người dùng cung cấp | [Input](notary_v2/README.md#input) | [intake-dialog.js](../../shell/src/renderer/notary/intake-dialog.js) · `createIntakeDialog` |
| Input: phân tích | Tạo gợi ý từ nguồn nhập | [Input](notary_v2/README.md#input) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `intakeAnalyze` |
| Input: sửa gợi ý | Kiểm tra, sửa dòng trước khi nhận | [Nhập liệu](notary_v2/README.md#input) | [intake-dialog.js](../../shell/src/renderer/notary/intake-dialog.js) · `reviewCardEl`, `renderRows` |
| Input: đưa vào Stage | Chấp nhận gợi ý đã kiểm tra | [Workspace](notary_v2/README.md#stage) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `acceptSuggestion` |
| Input: bỏ qua gợi ý | Loại gợi ý chưa dùng | [Input](notary_v2/README.md#input) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `discardSuggestion` |
| Stage: thêm Người | Thêm dòng Người mới | [Stage](notary_v2/README.md#stage) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `addPerson` |
| Stage: sửa Người | Sửa dữ liệu trong bảng | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `peopleTableEl` |
| Stage: xóa Người | Bỏ dòng Người khỏi Stage | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `model.removeStageRow` |
| Stage: đổi thứ tự Người | Kéo hoặc dùng Ctrl + ↑/↓ để sắp xếp dòng | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `movePersonRow` |
| Stage: thêm Tài sản | Thêm cột Tài sản | [Stage](notary_v2/README.md#stage) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `addAsset` |
| Stage: sửa Tài sản | Sửa dữ liệu trong cột | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `assetTableEl` |
| Stage: xóa Tài sản | Bỏ cột Tài sản khỏi Stage | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `removeAssetAt` |
| Stage: đổi thứ tự Tài sản | Kéo cột hoặc dùng Ctrl + ←/→ để sắp xếp | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `assetTableEl`, `model.moveAsset` |
| Stage: sửa loại đất | Chọn, thêm hoặc sửa loại đất trong draft | [Quy tắc tài sản](shared/ocr-rules.md#property) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `openLandDialog` |
| Stage: áp dụng loại đất | Đưa lựa chọn loại đất vào draft hiện tại | [Quy tắc tài sản](shared/ocr-rules.md#property) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `openLandDialog` |
| Stage: tra địa chỉ | Tra xã/tỉnh, copy kết quả phù hợp rồi tự dán vào ô | [Tra cứu địa chỉ](shared/administrative-lookup.md#usage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `lookupTraButton`, `lookupCopyButton` |
| Stage: Cập nhật | Lưu dữ liệu Stage đã kiểm tra | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `runCommit` |
| Pool: gán người | Chọn người chưa gán và đưa vào sơ đồ | [Pool](notary_v2/README.md#pool) | [relationship-diagram.js](../../shell/src/renderer/notary/relationship-diagram.js) · `openAssignMenu` |
| Pool: bỏ gán người | Trả người từ vị trí sơ đồ về Pool | [Pool](notary_v2/README.md#pool) | [relationship-diagram.js](../../shell/src/renderer/notary/relationship-diagram.js) · `inheritanceCardEl` |
| Diagram: Hai bên | Xếp người theo hai bên hợp đồng | [Hai bên](notary_v2/diagram-rules.md#two-party) | [relationship-diagram.js](../../shell/src/renderer/notary/relationship-diagram.js) · `twoPartyInto` |
| Diagram: Thừa kế | Xếp quan hệ và vai trò thừa kế | [Sơ đồ](notary_v2/diagram-rules.md#common) · [Thừa kế](notary_v2/diagram-rules.md#inheritance) | [relationship-diagram.js](../../shell/src/renderer/notary/relationship-diagram.js) · `inheritanceInto` |
| Diagram: xem cách tính | Xem kết quả và giải thích từ engine | [Sơ đồ](notary_v2/diagram-rules.md#common) | [relationship-diagram.js](../../shell/src/renderer/notary/relationship-diagram.js) · `runEvaluate`, `calcPanelEl` |
| Diagram: lưu | Lưu sơ đồ đã kiểm tra | [Sơ đồ](notary_v2/diagram-rules.md#common) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `saveDiagram` |
| Word: chọn thư mục mẫu | Chọn thư mục chứa các mẫu Word | [Xuất Word](notary_v2/word-templates.md#export) | [word-export-dialog.js](../../shell/src/renderer/notary/word-export-dialog.js) · `createWordDialog` |
| Word: quét mẫu | Tải danh sách file và trạng thái sẵn sàng | [Xuất Word](notary_v2/word-templates.md#export) | [word-export-dialog.js](../../shell/src/renderer/notary/word-export-dialog.js) · `renderDocs` |
| Word: chọn thư mục đích | Chọn nơi lưu kết quả | [Xuất Word](notary_v2/word-templates.md#export) | [word-export-dialog.js](../../shell/src/renderer/notary/word-export-dialog.js) · `pickDirToken` |
| Word: xuất | Tạo văn bản từ hồ sơ | [Xuất Word](notary_v2/word-templates.md#export) | [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js) · `exportWord` |
| Word: mở file | Mở file kết quả | [Xuất Word](notary_v2/word-templates.md#export) | [word-export-dialog.js](../../shell/src/renderer/notary/word-export-dialog.js) · `resultRowEl` |

**Chuyển loại hồ sơ sau khi lưu** đã có quy tắc owner 16/10/2026 ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md),
contract §13.18): giữ Người/Tài sản của Stage, reset Diagram rỗng theo domain mới, buộc chọn
`document_type` mới kèm xác nhận. Nút **Đổi loại** ở Soạn hồ sơ đã triển khai với
`notary.workspace_convert_type`; Stage/meta nháp phải Cập nhật trước, lỗi giữ nháp
Diagram. [#25](../backlog/story-saved-case-type-conversion.md) **built 16/10/2026,
independent Quick clean**; không coi lựa chọn loại lúc tạo nháp là bằng chứng đổi loại.

## upload_lab — Số hóa và chuẩn bị upload hồ sơ cũ

Hai tab đang có trong UI là `Audit Sổ Công Chứng` và `Quét & Upload Hồ Sơ`.
App điền sẵn rồi dừng trước nút Lưu để người dùng tự kiểm tra; dữ liệu chính
thức trên website là nguồn sự thật, không phải tín hiệu browser cục bộ.

**SOT cấu trúc website — 20/10/2026, sau đăng nhập thủ công:**
[Nam Định](upload_lab/nam-dinh-website-sot.md) là website thứ nhất được catalog
lâu dài: **17 trường ngữ nghĩa** trên empty form live, **7 label required**
(không proof HTML attr/enforcement); 6 widget/list hiện render gồm status **3**,
nhóm **13**, asset **12**, title **5**, CCV **3**, thư ký **5**. List phi cá nhân
và ID/label/metadata vai trò nhóm được chép bền vững; nhân sự chỉ shape/count.
Có default/state và proof props↔DOM/pagination **trong phiên**, không tổng DB
hoặc mọi đơn vị. Zero authenticated coverage/403/unscoped=[] của audit static
trước đó giữ làm lịch sử; scope server và form/submission conversion còn unknown.
Không Lưu/prime/upload hoặc mở record trên portal thật. Policy owner đã chốt:
bốn phí/ghi chú bỏ qua, status Đã công chứng. Slice preSave adapter đã sửa và
kiểm chứng Chromium cô lập (không submit, có file selection), **review độc lập CLEAN**
không suy backend từ widget. Person/Asset/parties chưa cutover, **toàn #41 chưa
xong, gate mẫu ĐÓNG**; website thứ hai chưa khảo sát, không thêm canonical key.
Reviewer chạy lại Upload **42 pass, không skip** và sidecar **60 pass**; smoke
filename decoy bổ sung **5 pass, không skip**. Không nghiệm thu portal thật hoặc
packaged; build/dist chưa tái sinh.


| Màn / thao tác | Dùng để | Tài liệu | Điểm vào mã |
|---|---|---|---|
| Audit: chọn website | Chọn nguồn portal dùng chung cho hai tab | [UI](upload_lab/README.md#ui) | [audit.js](../../shell/src/renderer/upload/audit.js) · `buildAuditTab` |
| Audit: kiểm tra môi trường | Xem khả năng kết nối portal | [UI](upload_lab/README.md#ui) | [index.js](../../shell/src/renderer/upload/index.js) · `upload.env_check` |
| Audit: đăng nhập/xác nhận | Mở browser và xác nhận đã đăng nhập | [Phiên portal](upload_lab/README.md#portal) | [index.js](../../shell/src/renderer/upload/index.js) · `upload.session_start`, `upload.confirm_login` |
| Audit: chọn khoảng ngày | Giới hạn đợt cần so sánh | [UI](upload_lab/README.md#ui) | [audit.js](../../shell/src/renderer/upload/audit.js) · `commitDate` |
| Audit: tải Excel từ web | Tải sổ portal về | [UI](upload_lab/README.md#ui) | [index.js](../../shell/src/renderer/upload/index.js) · `upload.download_export` |
| Audit: chọn/nạp Excel | Nạp sổ để đối chiếu | [Upload Lab](upload_lab/README.md) · [UI](upload_lab/README.md#ui) | [audit.js](../../shell/src/renderer/upload/audit.js) |
| Audit: xem KPI và bảng kết quả | Xem tổng, hợp lệ, thiếu, lỗi và số trùng | [Upload Lab](upload_lab/README.md) §4 | [audit.js](../../shell/src/renderer/upload/audit.js) · `buildAuditTab` |
| Quét & Upload: chọn website | Dùng cùng website với tab Audit | [UI](upload_lab/README.md#ui) | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) · `buildScanUploadTab` |
| Quét & Upload: chọn thư mục/quét | Chạy quét kho Word | [Upload Lab](upload_lab/README.md) §3 | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) · `buildScanUploadTab` |
| Quét & Upload: cập nhật Công chứng viên/Thư ký | Quản lý thông tin dùng khi chuẩn bị form | [UI](upload_lab/README.md#ui) | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) |
| Quét & Upload: chọn số tab, xem tiến độ | Chia hồ sơ thành từng đợt | [UI](upload_lab/README.md#ui) | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) |
| Quét & Upload: chọn tất cả/bỏ chọn | Chọn hàng trong danh sách | [UI](upload_lab/README.md#ui) | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) · `selectAll`, `clearSelection` |
| Quét & Upload: lọc lỗi/hoàn tác | Thu hẹp danh sách và khôi phục lọc | [UI](upload_lab/README.md#ui) | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) · `toggleIssueFilter` |
| Quét & Upload: chọn số thiếu trong Excel | Đưa hàng thiếu vào đợt chuẩn bị | [Upload Lab](upload_lab/README.md) §5 | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) |
| Quét & Upload: điền form đã chọn | Điền sẵn, dừng để người dùng tự bấm Lưu | [Upload Lab](upload_lab/README.md) §5 | [scan-upload.js](../../shell/src/renderer/upload/scan-upload.js) · `actions.prepare` |
| Quét & Upload: tiếp tục đợt/đối chiếu đầu vào | Chuyển qua hồ sơ đã chọn nhưng chưa chuẩn bị, hoặc nạp sổ để so lại dữ liệu chính thức | [Upload Lab](upload_lab/README.md) §2.3, §3.2 | [index.js](../../shell/src/renderer/upload/index.js) |
| Quét & Upload: dừng/đóng browser | Dừng tiến trình hoặc đóng phiên portal | [Phiên portal](upload_lab/README.md#portal) | [index.js](../../shell/src/renderer/upload/index.js) · `upload.session_close` |

## notaryoffice — Theo dõi hồ sơ

Đây là module thứ ba trong tầm nhìn nhưng hiện mới là **bản thiết kế nháp**,
chưa có màn chạy. **DEFERRED — owner 17/10/2026:** “notaryoffice để lại, tôi sẽ làm sau”.
Giữ Draft và công việc để làm sau; không giao pilot, phép đo A1/A3/A4,
code/schema/runtime Office lúc này. [Quyết định](../decisions/decision-owner-notaryoffice-deferred-20261017.md);
[#14](../backlog/spike-office-pilot-scope.md) đã được trả lời về phạm vi, không phải Office built.
Thiết kế dự kiến nhận dấu vết được phép, gom gợi ý hồ sơ, rồi để chuyên viên
xác nhận. Đây chưa phải tích hợp hoàn chỉnh; nguồn Zalo riêng cũng chưa nối
xong contract với ứng dụng chính.

| Hướng màn hình dự kiến | Mục đích | Tài liệu | Mã hiện tại |
|---|---|---|---|
| Dấu vết / bằng chứng | Giữ nguồn và thời gian của hoạt động được phép | [Thiết kế](notaryoffice/README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildOffice` chỉ hiện thông báo chưa triển khai |
| Hồ sơ nháp đề xuất | Gom hoạt động thành ứng viên để người kiểm tra | [Nguồn ý tưởng](../archive/specs-before-consolidation-20261015/notaryoffice/intent-source.md) | Chưa có mã chạy |
| Hồ sơ đã xác nhận / lịch sử | Tìm hồ sơ và xem tiến trình | [Thiết kế](notaryoffice/README.md) | Chưa có mã chạy |

Zalo là nguồn thu nhận, không phải module nghiệp vụ thứ tư. Trong màn Soạn hồ
sơ, nút Zalo đang disabled. Nguồn inbox có ở phần riêng; kết nối consumer còn
đang ở dạng thiết kế nháp.

## Tiện ích và công cụ khác

| Màn / công cụ | Dùng để | Tài liệu | Điểm vào |
|---|---|---|---|
| Tra cứu chung | Tìm trên dữ liệu nhiều module khi nguồn dữ liệu sẵn sàng | [Tầm nhìn hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildSearch`, hiện báo chưa có nguồn để tìm |
| Trạng thái/Cài đặt: kết nối, phiên bản | Xem tình trạng kết nối và phiên bản | [Spec hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `buildStatus` |
| Trạng thái/Cài đặt: module, job | Xem sức khỏe module và công việc đang chạy | [Spec hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `healthTableEl`, `renderJobs` |
| Trạng thái/Cài đặt: engine, diagnostics | Kiểm tra môi trường và tải thông tin lỗi | [Spec hệ thống](README.md) | [renderer.js](../../shell/src/renderer/renderer.js) · `runEnvCheck`, `loadDiagnostics` |
| Soát Word với bản scan (công cụ dòng lệnh) | Đối chiếu chữ và trường, không ghi hồ sơ | [Soát văn bản](shared/document-audit.md) | [run_fast_audit.py](../../notary_v2/tools/run_fast_audit.py) |
| Regex Lab | So sánh quy tắc với đáp án kiểm tra độc lập | [Core và quy trình](shared/extraction-rules.md#core) | [regex_lab.py](../../upload_lab/tools/regex_lab.py) |
| Tool kiểm tra regex cho nhân viên | Thử một file hoặc cả thư mục Word | [Catalog regex](shared/extraction-rules.md#types) | [regex_test_tool.py](../../regex-test-tool/tool/regex_test_tool.py) |
| Tool xem kết quả một file | Xem Người/Thửa/JSON được trích | [Catalog regex](shared/extraction-rules.md#types) | [regex_test_tool.py](../../upload_lab/tools/regex_test_tool.py) |
| Nguồn inbox Zalo riêng | Nhận nội dung theo phạm vi cho phép; nút tích hợp trong app đang tắt | [Đầu vào Zalo](../archive/specs-before-consolidation-20261015/notary_v2/input/zalo/README.md) | [zalo_inbox.py](../../notary_v2/routers/zalo_inbox.py); phần nối với app còn là thiết kế nháp |
| Tra cứu địa chỉ trong Stage | Tra địa chỉ của Người hoặc Tài sản | [Tra cứu địa chỉ](shared/administrative-lookup.md#usage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `lookupTraButton`, `lookupCopyButton`; backend `lookup_address` |
| Lõi địa chỉ dùng chung | Tra tên xã/tỉnh từ kho cục bộ | [Lõi tra cứu](shared/administrative-lookup.md#lookup) | [administrative_address.py](../../notary_v2/services/administrative_address.py) · `lookup_address` |

## Cách dùng sổ tay

- Bắt đầu từ màn hình người dùng định làm việc; mở spec trước rồi lần tới code.
- Khi sửa hành vi, cập nhật spec liên quan trước code. Ghi quyết định owner vào
  `_bmad-output/decisions/`.
- Đọc `graphify-out/` khi cần tìm quan hệ code, rồi kiểm tra source hiện hành.
- Sau thay đổi UI, trạng thái module hoặc việc đang mở, cập nhật sổ tay này để
  góc nhìn đầu phiên còn đúng. Đây là bản đồ, không thay spec hành vi.
