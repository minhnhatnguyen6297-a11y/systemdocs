# Kế hoạch giao worker — MIN-123

Ngày: 2026-09-27. Nhánh tích hợp: `consolidate/monorepo`, checkout `D:\systemdocs`.
Bản nền đã gộp: `e3ef8ad`. Trạng thái: **xong gộp code và lập kế hoạch; chưa thực thi UI mới**.

**Nguồn yêu cầu và điều kiện hoàn thành:** [MIN-123](https://linear.app/minhnotary/issue/MIN-123/plan-djong-nhat-ui-electron-notary-va-upload-lab-theo-mau-dja-duyet) và các issue con.
File này là hướng dẫn thực thi: ai sửa file nào, thứ tự, bằng chứng, điểm dừng. Không thay mô tả yêu cầu ở Linear.

## 1. Bắt đầu từ đâu

1. Giao **P1 / MIN-124** trước.
2. P1 xong và được duyệt: giao P2 và P3 cho hai worker riêng.
3. P3 được duyệt: P4 làm giao diện chung. P2 được duyệt: P5 làm dữ liệu. Hai nhánh này có thể chạy song song.
4. P4 xong: giao P8 Upload. P4 + P5 xong: giao P6 Notary.
5. P6 xong: giao P7 sơ đồ.
6. P7 + P8 xong: giao P9 gộp và nghiệm thu.

“Được duyệt” là có quyết định thật của chủ dự án ghi trong issue/handoff. Ảnh đã duyệt trong phiên chỉ chốt hướng nhìn của Notary; chưa thay cho contract dữ liệu hoặc bản mẫu Upload.

| Phase | Task | Đầu ra chính | Chờ |
|---|---|---|---|
| P0 | MIN-123 | Gộp nhánh, giữ AGENTS monorepo — **đã xong** | — |
| P1 | [MIN-124](https://linear.app/minhnotary/issue/MIN-124/ui-p1-chot-bo-file-thiet-ke-va-cach-thao-tac-chung) | Bộ file thiết kế và bảng màn hình | — |
| P2 | [MIN-125](https://linear.app/minhnotary/issue/MIN-125/ui-p2-chot-hop-djong-du-lieu-stage-3-tai-san-va-30-vi-tri-hai-ben) | Contract dữ liệu + ví dụ + cách đọc hồ sơ cũ | P1 |
| P3 | [MIN-126](https://linear.app/minhnotary/issue/MIN-126/ui-p3-lam-ban-mau-tuong-tac-dje-duyet-bo-cuc-notary-va-upload) | Bản mẫu thao tác và ảnh thật cả hai module | P1 |
| P4 | [MIN-127](https://linear.app/minhnotary/issue/MIN-127/ui-p4-ap-dung-nen-giao-dien-va-thanh-phan-dung-chung-cua-electron) | CSS/thành phần chung Electron | P1, P3 |
| P5 | [MIN-128](https://linear.app/minhnotary/issue/MIN-128/ui-p5-thuc-thi-model-va-luu-du-lieu-notary-theo-contract-dja-duyet) | Model, adapter, lưu dữ liệu Notary | P2 |
| P6 | [MIN-129](https://linear.app/minhnotary/issue/MIN-129/ui-p6-dung-vung-nhap-tai-sannguoi-bang-loai-djat-va-pool) | Stage, bảng loại đất, nhập file, Pool | P4, P5 |
| P7 | [MIN-130](https://linear.app/minhnotary/issue/MIN-130/ui-p7-dung-so-djo-thua-ke-va-hai-ben-theo-bo-thiet-ke-moi) | Hai kiểu sơ đồ | P6 |
| P8 | [MIN-131](https://linear.app/minhnotary/issue/MIN-131/ui-p8-lam-nhe-hai-man-hinh-upload-lab-theo-bo-giao-dien-chung) | Hai tab Upload Lab | P4 |
| P9 | [MIN-132](https://linear.app/minhnotary/issue/MIN-132/ui-p9-gop-cac-phase-kiem-tra-toan-luong-va-ban-giao-ui) | Bản gộp, bằng chứng và bàn giao cuối | P7, P8 |

Không ước lượng giờ trước khi P1/P2 chốt số màn hình và mức đổi dữ liệu.

## 2. Hồ sơ nguồn cần đọc

Đọc `AGENTS.md` trên **monorepo hiện tại**, không dùng bản từ worktree cũ.
Các số dòng dưới đây được đối chiếu ở `e3ef8ad`; dùng tên hàm khi code đã thay đổi.

| Nguồn đã có | Ý nghĩa khi giao việc |
|---|---|
| `shell/src/renderer/notary/case-drafting-model.js:233` | Hồ sơ mới dùng Stage chưa xác nhận cho assignablePersonIds; `pool()` ở dòng 253 cũng đọc Stage đang gõ. P2/P5 phải giải quyết. |
| Cùng file, `addAsset()` dòng 466 | Chưa chặn 3 tài sản tại hàm này; tài sản đầu tự thành primary. Đừng chỉ chặn nút giao diện. |
| Cùng file, `removeStageRow()` dòng 517 | Xóa row đang sửa đã xóa tham chiếu diagram. Phải thiết kế Hủy để không mất sơ đồ. |
| Cùng file, `saveDraft()` dòng 404 và `commitStage()` dòng 573 | Luồng tạo mới và luồng cập nhật hiện khác nhau; cần kiểm tra cả hai. |
| `notary_v2/services/case_workspace.py:817` | Tạo hồ sơ kiểm tra node owner; không thể chỉ đổi CSS rồi bắt mọi hồ sơ mới Cập nhật trước khi có Pool. |
| `notary_v2/services/inheritance_workspace.py:53` | Cờ node hiện gồm isLandOwner/willReceive dạng đúng/sai, chưa là ba lựa chọn độc lập. |
| `shell/src/renderer/notary/relationship-diagram.js:381` | Cả Pool và diagram hiện trong cùng renderer. P6 phải bàn giao file này trước P7. |
| `notary_v2/frontend/static/ReactFlowApp.jsx`, `diagram_edges.js` | Tham chiếu thao tác/rule sinh chỗ và đường nối cũ; không đưa luật thừa kế JS cũ vào runtime mới. |
| `upload_lab/docs/spec_UI.md:14` | Chuẩn hai tab toàn chiều ngang, giữ trạng thái khi chuyển màn hình. |
| Cùng file, dòng 110 | Dry-run, chờ người dùng Lưu, không tự chạy đợt tiếp, đối soát chưa thành công. |
| `notary_v2/services/word_engine.py:31`, `word_batch_export.py:110` | Word hiện có giới hạn riêng 5 tài sản/20 người. Khả năng mới của UI không đồng nghĩa Word đã hỗ trợ. |
| `shell/package.json:7` | Runtime Electron hiện có; renderer JS/CSS. Bắt đầu bằng công nghệ này. |
| `upload_lab/upload_services/` | Đường dẫn service sau dọn monorepo. Không khôi phục đường dẫn `ui/services` cũ. |

Đọc thêm:
- `notary_v2/docs/platform/case-workspace/drafting-tab.md`.
- `docs/product/specs/2026-09-24-notary-v2-case-drafting-electron-ux.md`.
- `contracts/README.md`, `contracts/notary-case-drafting.md`, schema/ví dụ tương ứng.
- `upload_lab/README.md`, `upload_lab/docs/spec_UI.md`.
- `docs/architecture/TECH_STACK.md` trước khi đề xuất công nghệ khác.
- [Ảnh màn soạn thảo đã duyệt](references/approved-drafting.png), [ảnh bảng loại đất](references/approved-land-types.png).

Ảnh là tham chiếu thị giác. Các dấu chọn trong ảnh là dữ liệu ví dụ; không được lấy ảnh làm mặc định nghiệp vụ. Nút Zalo trong bản thật phải disable dù ảnh vẽ chưa rõ. Không quay lại nền kem hoặc phối màu riêng cho từng vùng từ các thử nghiệm trước.

## 3. Danh sách file thiết kế cần tạo ở P1/P3

Các đường dẫn dưới đây là **dự kiến**, chưa được tạo bởi task lập kế hoạch.

| File | Người tạo | Nội dung/ranh giới |
|---|---|---|
| `docs/product/ui/README.md` | P1 | Mục lục, trạng thái duyệt, liên kết nguồn từng module. |
| `docs/product/ui/DESIGN.md` | P1 | Màu, font, cỡ chữ, khoảng cách, bo góc, bóng, trạng thái, thành phần chung. |
| `docs/product/ui/EXPERIENCE.md` | P1 | Cách thao tác chung: focus, bàn phím, cuộn, dialog, lỗi và trạng thái tải. |
| `docs/product/ui/tokens.json` | P1 | Giá trị thiết kế có tên; P4 ánh xạ vào CSS. Không cần xây máy sinh code mới. |
| `docs/product/ui/references/` | P1 | Chuyển ảnh đã duyệt vào nơi tra cứu dài hạn, ghi nguồn/phiên bản. |
| `notary_v2/docs/platform/case-workspace/visual-design.md` | P1 | Bố cục màn Notary, kích thước bảng/card/dialog, liên kết luật ở drafting-tab. |
| `notary_v2/docs/platform/case-workspace/drafting-tab.md` | P1, sau đó P2 | Sửa các mô tả cũ trái với quyết định mới; đánh dấu hiện trạng/mục tiêu/chờ duyệt. |
| `upload_lab/docs/visual-design.md` | P1 | Bố cục và kích thước 2 tab Upload; liên kết spec_UI cho hành vi. |
| `upload_lab/docs/spec_UI.md` | P1 | Cập nhật cấu trúc hiển thị đã duyệt; không tự đổi nghiệp vụ. |
| `docs/product/ui/prototypes/index.html` và CSS/JS cạnh đó | P3 | Mẫu thao tác có dữ liệu giả, dùng lâu dài để so giao diện. |
| `docs/product/ui/prototypes/README.md` | P3 | Cách mở, trạng thái minh họa, kích thước cửa sổ, giới hạn mẫu. |

P1 cập nhật chỉ mục/tài liệu Electron cũ để dẫn sang nguồn mới, không duy trì hai bản quy định tương đương.
Màu số cụ thể, ngưỡng đổi bố cục và kích thước card do P1/P3 đưa ra để duyệt; không suy trực tiếp từ số pixel trong ảnh AI.

## 4. Gói giao việc từng phase

### P1 — Thiết kế chung · MIN-124

**Nhận:** hai ảnh trong references, mô tả MIN-123, code/spec hiện tại.
**Được sửa:** các file tài liệu trong mục 3; file chỉ mục liên quan.
**Thực hiện:**
1. Lập danh sách màn hình và trạng thái từ source; mỗi màn có file renderer sở hữu.
2. Viết bộ kích thước/chữ/màu và bảng thành phần có tên dùng chung.
3. Vẽ bố cục ở các cửa sổ thường, xác định vùng cuộn và vùng được kéo tăng/giảm chiều cao.
4. Đối chiếu tài liệu cũ, ghi những gì phải thay thế và những gì cần P2 chốt.
5. Bàn giao phiên bản thiết kế có ngày duyệt.

**Bằng chứng:** bảng file–màn hình, thiết kế đủ trạng thái, ảnh nguồn có thể mở.
**Điểm dừng:** trình bộ file cụ thể để duyệt; không sửa runtime hoặc tự chốt nghiệp vụ còn mở.

### P2 — Contract dữ liệu · MIN-125

**Nhận:** P1 đã duyệt, bảng khoảng cách với source ở mục 2.
**Được sửa:** `contracts/notary-case-drafting.md`, thư mục schema/ví dụ cùng tên, tài liệu Notary liên quan. Đề xuất chưa duyệt phải ghi rõ DRAFT; không ghi là contract đã publish.
**Thực hiện:**
1. Vẽ vòng đời dữ liệu: đang sửa → xác nhận → Pool/diagram → lưu/mở; gồm hồ sơ chưa có case_id.
2. Lập bảng trường cũ → trường mới → quy tắc chuyển; tách ID đối tượng khỏi số chỗ.
3. Liệt kê lệnh/tham số/trả lỗi, cách bảo vệ revision, retry và phản hồi đến muộn.
4. Đưa ví dụ trước/sau cho reorder, xóa rồi Hủy, node trống, vị trí 16, tài sản được nhiều người chọn.
5. Đề xuất cụ thể cho các câu hỏi trong issue, gom để chủ dự án chốt một lượt.
6. Chỉ sau duyệt mới khóa schema để P5 dùng.

**Bằng chứng:** ví dụ valid/invalid, bảng tương thích hồ sơ cũ, quyết định có người duyệt.
**Điểm dừng:** chưa có duyệt contract thì chưa giao runtime P5. Đây là quy tắc của `contracts/README.md`, không phải một vòng xin phép merge mới.

### P3 — Bản mẫu thao tác · MIN-126

**Nhận:** P1. Có thể chạy song song P2; dùng dữ liệu giả, không tự chốt schema của P2.
**Được sửa:** `docs/product/ui/prototypes/`; ghi bằng chứng duyệt trong task.
**Thực hiện:** dựng từng màn, kiểm tra kích thước thật, bổ sung rỗng/lỗi/sửa dở, chụp màn hình, ghi các khác biệt với ảnh được duyệt.
**Bằng chứng:** file mở được, thao tác kéo/thả/chọn/dialog có phản hồi; ảnh 2 màn Notary và 2 tab Upload, bảng loại đất.
**Điểm dừng:** chủ dự án duyệt trước P4. Nếu P2 thay đổi hành vi ảnh hưởng mẫu, sửa mẫu và xác nhận phần thay đổi trước worker liên quan triển khai.

### P4 — CSS và thành phần chung · MIN-127

**Nhận:** P1/P3 đã duyệt.
**Sở hữu:** `shell/src/renderer/styles.css`, `lib.js`, phần shell trong `renderer.js`, `index.html`; file UI chung mới chỉ khi thật cần.
**Thực hiện:** ánh xạ tokens → CSS; làm từng thành phần nhỏ; đổi nền/khối/toolbar; kiểm tra các màn chưa chuyển; bàn giao tên lớp và cách dùng.
**Bằng chứng:** trang mẫu thành phần, danh sách vùng đã chuyển, kiểm tra navigation/state.
**Điểm dừng:** khóa giao diện dùng chung trước P6/P8. Worker module muốn đổi file chung gửi yêu cầu cho người sở hữu; không tự rải CSS toàn cục.

### P5 — Model/lưu dữ liệu Notary · MIN-128

**Nhận:** contract P2 đã duyệt; chạy độc lập với P4 nếu không sửa giao diện.
**Sở hữu:**
- `shell/src/renderer/notary/case-drafting-model.js`.
- `shell/sidecar/notary_adapter.py`, `notary_mock_adapter.py`, phần đăng ký lệnh nếu contract cần.
- `notary_v2/services/case_workspace.py`, `inheritance_workspace.py`.
- `notary_v2/models.py`, `database.py` chỉ phần dữ liệu đã duyệt.
- Các test/fixture đúng các tầng trên.

**Thực hiện:** lưu/load phiên bản mới → bảo vệ Stage draft/confirmed → model thao tác → adapter → tương thích dữ liệu cũ → bàn giao API cho view.
**Lưu ý:** thay đổi DB phải có đường nâng cấp không phá dữ liệu, dùng bản sao khi kiểm tra; không reset DB thật. Không lùi thay đổi Zalo đã có trong monorepo.
**Bằng chứng:** bảng lệnh/model API, ví dụ round-trip, cập nhật thất bại/retry/hủy, mở hồ sơ cũ.
**Điểm dừng:** luật pháp lý chưa rõ phải tìm source Python/spec và hỏi đúng phần thiếu; không suy từ ảnh hay từ JS web cũ.

### P6 — Stage, popup loại đất, intake, Pool · MIN-129

**Nhận:** P4 + P5.
**Sở hữu:** `case-drafting-view.js`, `case-drafting.css`, `intake-dialog.js`; phần Pool trong `relationship-diagram.js`.
**Thực hiện:** Stage tài sản → bảng người → đổi thứ tự → popup loại đất → toolbar/intake → Pool → các trạng thái sửa dở/lỗi.
**Bàn giao đặc biệt:** ghi dạng dữ liệu kéo/thả và DOM/class của Pool; commit xong `relationship-diagram.js` trước P7. Nếu cần thêm hàm model, yêu cầu P5 bổ sung/bàn giao quyền trước.
**Bằng chứng:** nhập thực, giữ focus/giá trị khi render, thêm/xóa/đổi chỗ/Hủy, popup Apply chưa truyền dữ liệu.
**Điểm dừng:** không tự làm sơ đồ hai bên hoặc thay module Upload trong phase này.

### P7 — Sơ đồ · MIN-130

**Nhận:** P6 đã gộp; contract và model P5.
**Sở hữu:** `relationship-diagram.js`, phần diagram trong `case-drafting.css`, điểm nối diagram trong `case-drafting-view.js`.
**Thực hiện:** giao diện thừa kế → card và nút số → sinh chỗ/đường nối → pan/zoom/mở rộng → sơ đồ hai bên → lưu/mở và đổi loại theo P2.
**Bằng chứng:** video ngắn hoặc chuỗi ảnh thao tác, cấu trúc node trước/sau, tình huống đủ 30 hai bên và hơn 30 thừa kế.
**Điểm dừng:** không sửa engine Word hoặc giảm số người thừa kế xuống 30 để vừa màn hình. Bỏ viền trang trí không có nghĩa bỏ đường biểu diễn quan hệ.

### P8 — Upload Lab · MIN-131

**Nhận:** P4. Chạy song song P5/P6/P7 vì sở hữu file khác.
**Sở hữu:** `shell/src/renderer/upload/audit.js`, `scan-upload.js`, `index.js`, `upload.css`.
**Chỉ sửa khi thật cần:** `state.js`, `client.js` để giữ trạng thái giao diện, không đổi API backend.
**Thực hiện:** Audit trước → Quét-upload → dialog/lỗi/loading → giữ dữ liệu khi chuyển màn hình → đối chiếu hành vi với spec.
**Bằng chứng:** ảnh hai tab, bảng so từng nút cũ/mới, chuyển tab/module và polling không mất lựa chọn.
**Điểm dừng:** backend `upload_lab/upload_services/`, parser, selector và Qt là nguồn đối chiếu; không thuộc quyền sửa thiết kế của phase này.

### P9 — Gộp và bàn giao · MIN-132

**Nhận:** tất cả phase hoàn tất, quyết định duyệt và commit đủ.
**Sở hữu:** tích hợp và sửa lỗi phát sinh trong phạm vi; tôn trọng người sở hữu file đang làm dở.
**Thực hiện:** gộp theo dependency → đi toàn luồng → chạy checklist cửa sổ thật → sửa lỗi → đối chiếu docs → bàn giao.
**Bằng chứng:** kết quả ở mục 6, ảnh thật, commit cuối, danh sách giới hạn còn lại.
**Điểm dừng:** nghiệm thu UI mới riêng với phần Word để lại. Không báo “xong toàn bộ flow xuất văn bản” khi chưa có task Word.

## 5. Cách chia worker để không sửa chồng

| Đợt | Worker A | Worker B |
|---|---|---|
| 1 | P1 | — |
| 2 | P2: contract | P3: bản mẫu |
| 3 | P5: dữ liệu | P4: giao diện chung |
| 4 | P6: Stage/Pool | P8: Upload |
| 5 | P7: diagram | Hoàn tất P8 nếu còn |
| 6 | P9: gộp và nghiệm thu | — |

- Mỗi worker có worktree/nhánh riêng từ commit phụ thuộc đã gộp; không sửa trực tiếp cùng checkout.
- Không bắt đầu từ `772aa80` vì chưa có các thay đổi monorepo. Bắt đầu từ `consolidate/monorepo` sau commit kế hoạch này.
- P2 và P3 chỉ cùng đọc DESIGN; thay đổi thiết kế gốc do P1/người điều phối quản lý.
- P5 giữ model/adapter. P6 rồi P7 lần lượt giữ view/CSS Notary, không chạy song song.
- P8 giữ CSS trong module Upload; P4 giữ styles.css toàn cục.
- Chỉ người điều phối merge vào monorepo. Quyền “ưu tiên worktree” trong lần gộp P0 không là quyền bỏ thay đổi của worker khác về sau.
- Mỗi worker ghi `.agent/tasks/<ID>/brief.md`, `progress.md`, `decisions.md` nếu có, `handoff.md`; issue vẫn là nguồn mô tả và điều kiện hoàn thành.
- Nếu cần thay ngoài vùng sở hữu: nêu file, lý do, phương án trong issue/handoff trước khi người điều phối phân lại quyền.

## 6. Kế hoạch bằng chứng

Đây là các kiểm tra **đề xuất cho worker tương lai**. Kết quả đã chạy cho merge P0 nằm riêng trong [progress.md](progress.md).

| Nhóm | Kiểm tra | Phase |
|---|---|---|
| Tài liệu | Link/file tồn tại; mục nào đã duyệt, mục nào còn draft; không trùng nguồn quyết định | P1–P3, P9 |
| Contract | Từ root: `rtk proxy python contracts/notary-case-drafting/validate_examples.py`; cập nhật fixture theo contract đã duyệt | P2, P5 |
| Renderer/model | Tại shell: `rtk proxy node --test test/*.test.mjs` | P4–P9 khi được giao kiểm chứng |
| Adapter Notary | Tại shell: `rtk proxy python -m pytest test/test_notary_adapter_contract.py test/test_notary_intake_adapter.py test/test_notary_mock_adapter.py -q` | P5, P9 |
| Dịch vụ Notary | Tại notary_v2: `rtk proxy python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q`; `verify.ps1` theo môi trường repo | P5, P9 |
| Upload UI | `shell/test/upload-state.test.mjs`, `upload-routing.test.mjs`; mô phỏng phản hồi cũ đến muộn | P8, P9 |
| Upload adapter | Chọn các test liên quan trong `shell/test/test_upload_workspace.py`, `test_upload_workflow.py`, `test_upload_recovery.py`; kiểm tra điều kiện chạy trước | P8 nếu chạm state/client, P9 |
| Mắt và chuột thật | Chụp/click/kéo/thả/gõ ở Electron, có tên dài, dữ liệu lớn, lỗi, rỗng, focus | P3, P6–P9 |

Không chỉ dựa vào test đọc chuỗi CSS để kết luận giao diện dùng được. Test cũ gắn với kích thước cũ phải đối chiếu mục đích trước khi sửa, không xóa để làm xanh kết quả.
Không chạy kiểm tra upload dùng dịch vụ thật hoặc tự bấm Lưu trên cổng tỉnh.

Checklist đi tay khi nghiệm thu:
- Cửa sổ 1280×800, 1366×768, 1920×1080; Windows scale 125% và 150%. Ghi cả kích thước vùng nội dung và scale.
- Bàn phím Tab/Shift+Tab, focus thấy rõ, mở/đóng dialog, trả focus, kéo thả có phương án thao tác đã duyệt.
- Stage mới chưa Cập nhật; sửa rồi Hủy; xóa người đã ở diagram rồi Hủy; popup loại đất Apply rồi Hủy Stage.
- Đổi tài sản 1↔3; số nhận vẫn là số vị trí; reorder hàng người không đổi số chỗ A/B.
- Node 1,15,16,30; chỗ trống ở giữa; thả vào chỗ có người theo quyết định P2.
- 30 người hai bên; >30 thừa kế; tên trùng/tên dài; sơ đồ không tự ép nhỏ chữ.
- Upload đổi nguồn/run khi job cũ còn về; chọn/bỏ chọn khi polling; đổi tab/module; chờ Lưu và cần đối soát.
- Word chỉ xác nhận chức năng cũ không hỏng và ranh giới hỗ trợ rõ. Không kiểm nhận khả năng Word mới chưa thực hiện.

## 7. Mẫu giao việc để sao chép

Thay <ID> và <P> bằng hàng trong mục 1:

> Thực hiện <ID> / phase <P> thuộc MIN-123.
> Đọc AGENTS.md trên consolidate/monorepo, issue Linear và .agent/tasks/MIN-123/plan.md.
> Kiểm tra phase phụ thuộc đã bàn giao và phần cần chủ dự án duyệt có quyết định thật.
> Tạo worktree riêng từ commit tích hợp mới nhất; tạo task record theo template.
> Chỉ sửa các file phase này sở hữu; nếu phát hiện cần đổi dữ liệu/hành vi ngoài phạm vi, ghi rõ và báo người điều phối.
> Làm đủ đầu ra của issue; chưa làm Word.
> Ghi commit, file đổi, cách kiểm chứng, kết quả và điểm còn thiếu vào handoff.md.
> Không tự merge/push nhánh tích hợp; trả commit để người điều phối gộp.

Khi giao P9, thêm yêu cầu kiểm chứng đầy đủ theo mục 6 và gộp các commit đã được duyệt.

## 8. Tiêu chuẩn nhận bàn giao một phase

1. Có commit chứa đúng phần việc; không cuốn file người khác hoặc dữ liệu local.
2. Có link issue, bản thiết kế/contract đang theo và quyết định duyệt cần thiết.
3. Có danh sách file đổi, file chung đã bàn giao quyền.
4. Có bằng chứng đạt điều kiện hoàn thành; phần chưa kiểm chứng được nói rõ.
5. Có ghi thay đổi nào ảnh hưởng phase sau và cách mở/chạy.
6. Tài liệu dài hạn cập nhật đúng nguồn; task log nằm trong .agent/tasks.
7. Không có thư viện mới, DB reset hoặc thay đổi Word nằm lẫn mà không được giao.

## 9. Việc tách ra sau

Phần chọn mẫu Word, popup xuất, nội dung biến, giới hạn và engine xuất là đợt sau do chủ dự án giao. Các issue hiện tại chỉ chuẩn bị dữ liệu và ranh giới tương thích; không được tự mở rộng sang triển khai xuất Word.
