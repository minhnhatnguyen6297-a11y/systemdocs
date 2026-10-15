# Sổ tay sản phẩm theo màn hình

**Cập nhật:** 15/10/2026 · **Dùng để:** giúp owner và coordinator cùng nhìn
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
2. **Số hóa hồ sơ cũ:** đọc Word, đối chiếu sổ Excel và chuẩn bị nhập portal để
   chuyên viên tự kiểm tra, tự lưu.
3. **Theo dõi vận hành:** dự kiến cho biết hồ sơ đang ở đâu và chờ việc gì;
   hiện mới có thiết kế, chưa có chương trình chạy.

Việc đang mở được tổng hợp tại [catalog issue](../backlog/README.md)
(15/10, draft/chưa duyệt triển khai). [Ticket tổng cũ](../backlog/bug-notary-flow-ui-regex-word.md)
giữ làm lịch sử và bị chặn tracking-only để không chạy trùng các leaf. Các điểm chính:

- Tách rõ địa chỉ của người và nơi cấp giấy khai tử; chốt quy tắc đổi loại hồ
  sơ đã lưu trước khi làm.
- Làm rõ kích thước Pool/Sơ đồ và thao tác thả người; gỡ nút `Hủy thay đổi`
  theo yêu cầu owner nhưng vẫn giữ bảo vệ dữ liệu chưa lưu.
- Nối việc sửa/thử rule regex với rule dùng trong flow; kiểm tra serial và địa
  chỉ thửa đang thiếu trong fixture.
- Giúp tìm mẫu Word và biết chỗ điền dữ liệu nào được hỗ trợ.

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
| Stage: Hủy thay đổi | Hủy phần sửa chưa cập nhật; ticket mới yêu cầu bỏ nút này | [Stage](notary_v2/README.md#stage) | [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js) · `cancelDraft` |
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

**Chuyển loại hồ sơ sau khi lưu** còn chờ quy tắc owner trong ticket; không xem
lựa chọn loại lúc tạo nháp là bằng chứng đã hỗ trợ đổi loại.

## upload_lab — Số hóa và chuẩn bị upload hồ sơ cũ

Hai tab đang có trong UI là `Audit Sổ Công Chứng` và `Quét & Upload Hồ Sơ`.
Flow dừng trước thao tác lưu trên portal để người dùng tự kiểm tra.

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
| Quét & Upload: tiếp tục đợt/đối chiếu lại | Làm đợt tiếp theo hoặc nạp sổ mới | [Upload Lab](upload_lab/README.md) §5 | [index.js](../../shell/src/renderer/upload/index.js) |
| Quét & Upload: dừng/đóng browser | Dừng tiến trình hoặc đóng phiên portal | [Phiên portal](upload_lab/README.md#portal) | [index.js](../../shell/src/renderer/upload/index.js) · `upload.session_close` |

## notaryoffice — Theo dõi hồ sơ

Đây là module thứ ba trong tầm nhìn nhưng hiện mới là **bản thiết kế nháp**,
chưa có màn chạy.
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
