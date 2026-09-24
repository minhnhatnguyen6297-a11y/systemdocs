# Upload Lab — Kế hoạch chuyển sang shell Electron

## Tóm tắt dễ đọc

Giữ cách làm việc đang tốt, chuyển sang khung ứng dụng mới với **hai tab rộng**: `Audit Sổ Công Chứng` và `Quét & Upload Hồ Sơ`. Chọn website ở đầu Audit; cả hai tab dùng chung lựa chọn này. Bỏ trang Nhật ký. Website thứ hai sẽ bổ sung sau khi có thông tin, không dựng một lựa chọn chưa dùng được.

Thứ tự làm: chốt cách trao đổi dữ liệu → nối bộ xử lý website và giữ an toàn dữ liệu cũ → nối đủ Audit/Upload → kiểm tra trên bản đóng gói → mới chuyển sang dùng mặc định. Chưa bỏ bản cũ cho đến khi bản mới đã được kiểm chứng.

Một số từ dùng trong phần kỹ thuật bên dưới:

- **Shell** là khung ứng dụng mới; **backend/engine** là phần Python thực sự đọc hồ sơ, đối chiếu và điều khiển trình duyệt. **Sidecar** là tiến trình Python chạy cùng ứng dụng.
- **Contract** là quy ước hai phần phải cùng hiểu, ví dụ nút Upload gửi những trường nào và nhận kết quả gì.
- **Run/manifest** là một lượt quét và tệp ghi danh sách hồ sơ của lượt đó; **job** là một tác vụ đang chạy; **queue** là danh sách hồ sơ chờ xử lý.
- **Provider** là bộ xử lý riêng của một website. **Revision** là số phiên bản dữ liệu để phát hiện khi màn hình đang dùng kết quả cũ.
- **Dry-run** ở đây là điền sẵn để người dùng tự kiểm tra và bấm Lưu. **Fixture** là dữ liệu/website giả dành riêng cho kiểm thử, không phải hồ sơ thật.
- **Pilot** là chạy thử có người kiểm tra; **rollback** là quay lại bản cũ an toàn; **hash** là dấu kiểm tra giúp biết tệp có bị thay đổi khi sao chép không.

Phần dưới là hướng dẫn chi tiết cho người triển khai. Đây là tài liệu kế hoạch, **chưa sửa code hoặc chuyển dữ liệu thật**.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đưa trải nghiệm Upload Lab hiện tại vào module `Upload Lab` của shell Electron, gồm hai tab rộng `Audit Sổ Công Chứng` và `Quét & Upload Hồ Sơ`, dùng chung website được chọn và tiếp tục chạy nghiệp vụ Python hiện có.

**Architecture:** Electron hiển thị giao diện và nhận thao tác; Python sở hữu quét hồ sơ, đối chiếu sổ, dữ liệu và trình duyệt upload. Website được chọn bằng một mã ổn định; backend dùng mã đó để chọn bộ xử lý và vùng dữ liệu riêng. Cầu nối Electron–Python được hoàn thiện theo từng luồng có thể kiểm chứng trước khi đổi ứng dụng mặc định.

**Tech Stack:** Dùng các công nghệ hiện có, theo `docs/architecture/TECH_STACK.md`: Electron, JavaScript/CSS thuần, Python/FastAPI, SQLite, Playwright, python-docx, Windows IFilter và openpyxl. Không thêm framework giao diện hoặc cơ sở dữ liệu mới.

**Spec:** Quyết định của người dùng trong §1; hành vi hiện tại ở `upload_lab/README.md`, `upload_lab/ui_qt/main_window.py`, `upload_lab/ui/services/`; chuẩn bảng đã chốt trong MIN-77; ranh giới tại `contracts/desktop-command.md`, `contracts/g1-module-data.md` và `docs/architecture/ELECTRON_G1_PLAN.md`.

Ngày lập: **24/09/2026**. Đây là kế hoạch chuyển đổi để review và chia việc, chưa phải xác nhận runtime đã hoàn thành hay contract mới đã được duyệt.

Issue bao trùm: [MIN-69 — MIGRATE — Upload/Audit vào Electron](https://linear.app/minhnotary/issue/MIN-69/migrate-uploadaudit-vao-electron). Đã đọc trực tiếp khi lập plan: issue đang **In Review**. Không suy trạng thái này thành đã nghiệm thu. Linear tiếp tục giữ mô tả, tiêu chí nghiệm thu và trạng thái task; các ô dưới đây dùng làm checklist kỹ thuật. Trước khi code, đối chiếu issue hiện có và tách công việc contract/runtime; không tạo issue trùng.

## Global Constraints

- Giữ UI/UX và nghiệp vụ đang dùng tốt của Upload Lab làm chuẩn đối chiếu; chỉ thay các điểm người dùng đã chốt trong §1.
- “mỗi phần là 1 tab nhỏ trong module upload lab”; “vùng xem bảng biểu cần rộng để user nhìn”.
- “Bỏ phần nhật ký”: bỏ trang/tab nhật ký khỏi Upload Lab. Thông báo lỗi cần xử lý vẫn xuất hiện tại thao tác tương ứng; không đưa bảng log kỹ thuật thay vào vùng nghiệp vụ.
- “đưa cấu hình vào đầu trang audit”: website và thao tác kết nối nằm ở đầu tab Audit.
- “sửa phần nhập web thành droplist chọn web”: không để người dùng gõ URL tùy ý trong luồng chính.
- Website chọn ở Audit dùng chung cho Quét & Upload; tab Upload hiển thị rõ website đích.
- Website mới sẽ được người dùng cung cấp sau. Đợt này có một lựa chọn hoạt động theo backend đã xác minh; không tạo lựa chọn thứ hai giả.
- Python tiếp tục sở hữu nghiệp vụ. Không chuyển parser, quy tắc audit hoặc Playwright sang JavaScript.
- Dry-run là mặc định: điền sẵn rồi người dùng tự kiểm tra và bấm Lưu trên Chromium. Không có thao tác tự Lưu/Finalize.
- Đồng bộ đủ hành vi trước khi đổi entrypoint mặc định; giữ ứng dụng Qt để quay lại cho đến khi nghiệm thu chuyển đổi.
- Contract mới/thay đổi nghĩa phải được duyệt và publish trong task riêng trước runtime phụ thuộc. Plan không tự publish contract.
- Phạm vi thực thi đầu tiên là **một máy Windows** theo `desktopcommand.v1`; LAN, database nghiệp vụ chung và các module khác có gate riêng.
- Không thêm UI chỉnh PDF, OCR, màn sửa từng trường trích xuất hoặc thay quy tắc regex trong đợt này. Kiểm tra/sửa giữ tại file nguồn và biểu mẫu portal như luồng hiện hành; phạm vi review/edit rộng hơn của MIN-69 phải được đối chiếu trước khi đóng issue.
- Bản production dùng engine thật. Bộ dữ liệu mô phỏng chỉ dùng phát triển/kiểm thử, không fallback âm thầm khi engine lỗi.
- Mật khẩu, token và cookie đăng nhập không đi qua payload gửi tới UI, log, ảnh kiểm thử hoặc localStorage. Không đưa dữ liệu hồ sơ thật vào log/ảnh kiểm thử. Quy tắc che thông tin dùng lại cơ chế hiện có.

---

## 1. Thiết kế sản phẩm đã chốt

### 1.1 Điều hướng và không gian bảng

Shell có một module chính tên **Upload Lab**. Bên trong có đúng hai tab nhỏ:

1. **Audit Sổ Công Chứng**.
2. **Quét & Upload Hồ Sơ**.

Mỗi tab sử dụng toàn bộ bề rộng phần nội dung còn lại của shell. Không có sidebar thứ hai trong Upload Lab; không xếp Audit và Upload cạnh nhau hay gộp thành trang dài nhiều khối đóng/mở. Không có tab Cấu hình và không có tab Nhật ký riêng.

Đổi tab hoặc sang module khác rồi quay lại phải giữ website, khoảng ngày, file đã chọn, kết quả, ô chọn hồ sơ, vị trí cuộn và tác vụ đang chạy. Bảng có vùng cuộn riêng, tiêu đề cột cố định; đường dẫn dài không kéo vỡ bố cục. Cho phép xem đủ đường dẫn bằng tooltip và mở file gốc từ dòng đó.

### 1.2 Tab Audit Sổ Công Chứng

Thứ tự từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Chọn website | Dropdown tên website; trạng thái kết nối/đăng nhập; nút kiểm tra và mở đăng nhập. Địa chỉ website có thể hiện chỉ đọc để nhận biết. |
| Nguồn sổ | Từ ngày, đến ngày, `Tải Excel từ Web`; chọn Excel trên máy và `Nạp dữ liệu`. |
| Số liệu | Bốn thẻ: Tổng số đã nạp, Hợp lệ trong sổ, Số còn thiếu, Lỗi / Trùng lặp. |
| Bảng | Hai vùng `Số còn thiếu` và `Số lỗi, trùng`, xếp trên/dưới, cùng toàn chiều rộng, có thể kéo chia chiều cao. |

Hai bảng dùng đúng bốn cột: `STT | Ngày | Số công chứng | Ghi chú`. Không đưa lại bảng số hợp lệ. Đây là chuẩn của [MIN-77](https://linear.app/minhnotary/issue/MIN-77/bug-chuan-hoa-cot-3-vung-audit-excel-va-rut-gon-cot-bang-upload), đã Done, và khớp source hiện tại. `upload_lab/docs/spec_UI.md` và một số ảnh tham chiếu cũ còn mô tả ba bảng/năm cột; cần sửa tài liệu đó trong chặng đặc tả, không lấy ảnh cũ làm chuẩn đích.

Chọn file trên máy hoặc tải file thành công sẽ tự nạp và audit theo khoảng ngày đang chọn, giữ hành vi Qt. Người dùng vẫn có nút Nạp dữ liệu để chạy lại sau khi đổi ngày. Đổi ngày/file làm kết quả cũ được đánh dấu chưa cập nhật; không dùng kết quả cũ như kết quả của bộ lọc mới. Khi nạp lỗi, vùng hiện tại báo lỗi rõ, không giữ số liệu cũ dưới nguồn mới.

Thông báo kiểm tra môi trường mở tại khối đầu trang khi cần; trạng thái bình thường chỉ chiếm một hàng gọn. Giữ phần lớn chiều cao cho bảng. Không in JSON, tên command hoặc stack trace cho người dùng.

### 1.3 Tab Quét & Upload Hồ Sơ

Thứ tự từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Ngữ cảnh | Tên website đang dùng, trạng thái đăng nhập, nguồn Excel/khoảng ngày đang đối chiếu; nút quay sang Audit để đổi website. |
| Nguồn và nhân sự | Chọn thư mục, `Bắt đầu Quét`; công chứng viên, thư ký, làm mới danh sách, số tab mỗi đợt từ 1 đến 30, mặc định 10 nếu chưa có giá trị đã lưu. |
| Tiến độ | Tiến độ quét và tiến độ chuẩn bị biểu mẫu tách riêng; nút `Dừng` theo trạng thái. |
| Thanh thao tác | Chọn tất cả, Bỏ chọn tất cả, Lọc số lỗi/Hoàn tác lọc, Số thiếu trong Excel, Upload file đã chọn, Tiếp tục N số tiếp theo, Đóng browser upload. |
| Bảng | `✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ file`. |

Quy tắc giữ từ backend/UI hiện tại:

- Chưa có Excel: vẫn cho quét và xem hồ sơ, không tự chọn là “thiếu trên web”.
- Có Excel cùng website: chọn mặc định các số hợp lệ chưa có trong sổ; giữ ghi chú số sai, sai năm, thiếu trường, trùng trong folder.
- Người dùng bỏ chọn thủ công thì cập nhật nền không tự chọn lại; chỉ bỏ khỏi bảng hồ sơ đã xác minh Lưu thành công.
- “Lọc số lỗi” giữ cơ chế chọn và hoàn tác của Qt; không tự đổi thành tìm kiếm tự do hoặc loại bỏ vĩnh viễn các dòng khác.
- Dòng đã chọn lên đầu; giữ ID thật cho mọi thao tác, không dùng số thứ tự hiển thị làm ID.
- Quét nguồn mới tạo ngữ cảnh lượt quét mới và bỏ các ID chọn từ lượt cũ; kết quả của job cũ đến muộn không ghi đè lượt đang xem.
- Mỗi đợt mở tối đa N tab. Đợt sau chỉ bắt đầu khi người dùng bấm Tiếp tục; không tự mở thêm.
- Dừng kết thúc sau đơn vị đang xử lý theo khả năng engine; không coi “đã yêu cầu dừng” là browser đã ngừng ngay.
- `Đã điền sẵn`, `Đang chờ kiểm tra`, `Đã lưu trên web`, `Lỗi` là các trạng thái khác nhau. Nút “Xong kiểm tra” không phải bằng chứng đã Lưu.

### 1.4 Dropdown website dùng chung

Chốt trước mắt một mục hoạt động **Nam Định**, dùng địa chỉ đã có trong source `https://congchungnamdinh.ninhbinh.gov.vn`. Mã nội bộ đề xuất: `nam_dinh`; nhãn và tên miền có thể thay đổi sau mà ID không đổi. Đây là địa chỉ từ code, không phải xác nhận đã truy cập portal trực tiếp trong lần lập plan.

Website được chọn quyết định bộ xử lý đăng nhập, tải file, đọc cấu trúc file và điền biểu mẫu. Các phần xử lý chung tiếp tục được tái sử dụng sau khi bộ xử lý website chuyển dữ liệu về cấu trúc chung.

Đề xuất kỹ thuật để hiện thực quyết định đã chốt:

- Backend cung cấp danh sách website cùng những thao tác đã hỗ trợ; frontend không chứa danh sách URL hoặc nhánh nghiệp vụ theo tỉnh.
- Mọi lệnh nghiệp vụ mang `website_id`. Lượt quét, sổ đã nạp, hàng đợi, browser và kết quả đều gắn cùng mã này.
- Chỉ cho đổi website khi không có tác vụ/đợt chuẩn bị đang hoạt động hoặc tab đang chờ kiểm tra. Backend kiểm lại điều kiện; không chỉ khóa dropdown ở UI.
- Đổi website sẽ hiển thị trạng thái của website mới, không giữ sổ/ô chọn của website cũ dưới tên website mới. Nếu chưa có dữ liệu thì hiện màn trống đúng nghĩa.
- Website chưa đăng ký bị từ chối; không quay về Nam Định ngầm.
- Lần sau thêm website phải có bộ xử lý và mẫu file thật của website đó trước khi bật các nút tương ứng. Không cần thay cấu trúc hai tab.

Việc bổ sung website thứ hai được tách sau khi người dùng cung cấp thông tin; không chặn chuyển website hiện có sang shell.

## 2. Hiện trạng và khoảng cách cần xử lý

Nguồn khảo sát: `D:/systemdocs`, nhánh `consolidate/monorepo`, commit `1abbb200c8f88126339ea9b7a599c46a1b6c546a`. `upload_lab/` và `shell/` không có sửa đổi local tại lúc đối chiếu. Một số tài liệu kiến trúc có sửa đổi chưa commit; không tự coi chúng là quyết định đã duyệt và không gom vào commit của công việc này.

| Hạng mục | Bằng chứng hiện tại | Công việc chuyển đổi |
|---|---|---|
| UI chuẩn | Bốn trang Qt; Audit và Upload ở `upload_lab/ui_qt/main_window.py:137`, `:162`, `:321`. | Giữ hai trang nghiệp vụ thành hai tab, chuyển cấu hình lên Audit, bỏ trang nhật ký. |
| UI Electron | `shell/src/renderer/renderer.js:494` gộp scan/audit/browser; `styles.css:18` giới hạn chiều rộng. | Tách module view và CSS theo Upload Lab; bỏ giới hạn 860px cho module này. |
| Đúng lượt quét | `shell/sidecar/upload_adapter.py:87` gọi scan nhưng không lưu manifest; `:120` trả thư mục runs; `:290` có fallback chọn run mới nhất. Legacy ghi manifest tại `upload_lab/ui/services/folder_workflow_service.py:26`. | Tạo file manifest của chính lượt scan; chuẩn bị upload buộc dùng đúng run, không tự chọn run khác. |
| Queue đối chiếu | `upload_lab/ui/services/scan_classification_service.py:79`; Qt dùng tại `main_window.py:1008`. Renderer mới chỉ hiển thị record scan thô ở `renderer.js:537`. | Gọi dịch vụ phân loại thật và trả đầy đủ dữ liệu cho bảng/chọn hồ sơ. |
| Tải sổ | Backend có `upload.download_export` ở `upload_adapter.py:262`; UI chưa có nút. Qt tự nạp sau tải ở `main_window.py:1311`. | Nối tải → nạp → audit → cập nhật phân loại cùng website. |
| Nhân sự và từng đợt | Qt gửi nhân sự, `chunk_size`, manifest và ID ở `main_window.py:1267`; shell chỉ gửi ID tại `renderer.js:664`. | Bổ sung đủ dữ liệu; truyền `chunk_size` xuống `prepare_manifest`. |
| Nhận biết đã Lưu | Qt poll liên tục ở `workers.py:128`; engine cập nhật registry ở `playwright_uploader.py:1959`. Shell chỉ poll sau `finish_review` tại `upload_adapter.py:333`. | Theo dõi liên tục trong browser thread và phản ánh kết quả từng hồ sơ trong lúc chờ người dùng. |
| Xác nhận đúng phiên | Các event dùng chung tại `upload_session.py:32`, các lệnh xác nhận không gắn job ở `upload_adapter.py:245`, `:340`. | Xác nhận phải gắn website, browser và job đích; từ chối tín hiệu cũ/khác đợt. |
| Kết quả một phần | Engine trả lỗi từng hồ sơ, adapter hiện gói summary mà chưa chuyển thành `partial`; `jobstore.py:161`. | Phân biệt thành công một phần và toàn bộ lỗi; giữ breakdown từng hồ sơ. |
| Restart/hủy | JobStore/tracker hiện giữ RAM: `jobstore.py:118`, `job-tracker.js:20`; terminal transition chưa khóa chặt tại `jobstore.py:106`. | Không phát lại upload mù sau crash; lưu thông tin khôi phục cần thiết; trạng thái đã kết thúc không bị ghi đè. |
| Đóng gói | `shell/package.json:19`, `shell/sidecar/g1-shell-sidecar.spec:4` chưa chứng minh đã mang đủ upload engine/dependency vào bản cài. | Chạy luồng Upload thật trên máy sạch, không dựa đường dẫn repo dev. |
| Kiểm thử | `shell/test/test_engine_adapters.py:123` chưa kiểm scan→manifest→prepare và có thể skip. | Dùng dữ liệu tự sinh, không skip khi thiếu thư mục downloads cá nhân; thêm kiểm thử UI và gói Windows. |

Đây là kết quả đọc source, chưa phải kết quả chạy test. Các con số pass trong inventory cũ chỉ là bằng chứng lịch sử.

## 3. Ranh giới code và dữ liệu

### 3.1 Đường đi của một thao tác

`Tab Electron → window.desktop.v1 → Electron main → Python sidecar → bộ xử lý website → engine Upload Lab`

Renderer chỉ giữ trạng thái trình bày và lựa chọn chưa gửi. Python kiểm tra website/run/ID, sở hữu registry và xác định hồ sơ đã Lưu. Main giữ hộp thoại chọn/mở file và vòng đời sidecar; token không vào renderer. Chromium vẫn là cửa sổ riêng do Python quản lý.

Bộ xử lý website hiện tại là lớp mỏng gọi `NamDinhUploaderSession`, `contract_book_audit` và các dịch vụ đã có. Không nhân đôi toàn bộ engine. Selector Nam Định vẫn chỉ sửa tại `upload_lab/uploader_selectors.py` theo rule repo. Website thứ hai sẽ có spec cho phần khác biệt trước khi thêm implementation.

### 3.2 Vùng dữ liệu và chuyển dữ liệu cũ

Tách **vị trí code** khỏi **vị trí dữ liệu**. Đề xuất cấu trúc dưới `app.getPath('userData')/upload_lab/`:

```text
upload_lab/
  workspace.sqlite3           # website đang chọn, run/audit binding, thông tin khôi phục
  websites/
    nam_dinh/
      registry.sqlite3       # giữ schema nghiệp vụ hiện tại
      output/                # kết quả trích xuất
      runs/                  # manifest từng lượt quét
      downloads/             # sổ Excel
      upload_runs/           # kết quả từng đợt
      nd_storage_state.json  # phiên đăng nhập, backend-only
      uploader_staff_options.json
      logs/                  # chẩn đoán đã lọc; không là trang UI
```

Đây là các tệp SQLite vận hành trong cùng công nghệ hiện có, không phải quyết định gộp database nghiệp vụ toàn hệ thống. Tách registry theo website để trạng thái `uploaded_success` của một web không làm web khác bỏ nhầm hồ sơ. Lượt scan thuộc website đang chọn; có thể tái sử dụng engine trích xuất nhưng không tái sử dụng trạng thái upload xuyên website.

Trước pilot thật: đóng phiên cũ, sao lưu nhất quán DB và các thư mục liên quan; chạy kiểm kê chuyển dữ liệu chỉ đọc trước. Chỉ ánh xạ dữ liệu cũ sang `nam_dinh` khi xác minh cấu hình nguồn đúng website này. Dữ liệu thiếu bằng chứng nguồn phải báo cần xác định, không tự gán.

Chuyển bằng **copy đã kiểm chứng**, giữ nguyên nguồn cũ. Giữ `record_id`, `run_id`, trạng thái thành công, quan hệ tới JSON; đổi các đường dẫn output nội bộ trong bản sao nếu cần, kiểm hash và số lượng. Đường dẫn tài liệu gốc của người dùng không đổi. Phiên đăng nhập có thể yêu cầu đăng nhập lại; không in nội dung tệp phiên. Tất cả việc đọc/ghi bên Python đều dùng data directory đã giải quyết, không mặc định ghi vào thư mục cài ứng dụng.

### 3.3 Khôi phục và chống gửi nhầm

- Đổi tab: giữ state trong module view, không dựng lại toàn bộ bảng mỗi nhịp poll.
- Renderer tải lại: đọc workspace và các job đang có từ backend/main; không tự chạy lại `prepare`.
- Sidecar/app restart: lệnh đang dở được báo gián đoạn; không coi là đang chạy. Run và thông tin đợt được khôi phục từ dữ liệu bền vững.
- Lưu tối thiểu `command_id`, hash yêu cầu, website, run, job, browser/đợt, ID hồ sơ và kết quả đã xác minh; không lưu cookie vào job store. Cùng `command_id` và nội dung trả cùng thao tác; cùng ID nhưng khác nội dung bị từ chối.
- Hồ sơ có thể đã Lưu trên portal nhưng chưa kịp ghi registry phải vào nhóm **Cần đối chiếu**. Dùng sổ mới/kiểm tra người dùng trước khi cho chuẩn bị lại; chỉ “không có trong file Excel cũ” không đủ chứng minh chưa Lưu.
- Hủy không hoàn tác một lần Lưu đã xảy ra. Trước khi đóng browser, poll/reconcile các tab còn đọc được; trường hợp không xác định phải giữ dấu cần kiểm tra.
- Bỏ trang Nhật ký không có nghĩa xóa dữ liệu phục hồi hoặc mất thông báo kết quả tại bảng.

## 4. Giao tiếp đích để publish trong task contract

Các tên/hình dạng dưới đây là đề xuất cụ thể cho task contract, không phải API đã tồn tại. Giữ outer envelope `desktopcommand.v1` và `g1.module.v1`. Dùng trường `workflow_version: "upload.workflow.v1"` trong payload/result để nhận diện luồng mới; công bố capability trong module registry. Consumer mới từ chối chạy nếu backend chưa công bố capability.

| Command | Request chính | Result chính |
|---|---|---|
| `upload.websites` — mới | workflow_version | danh sách website_id, label, display_url, capabilities |
| `upload.workspace_get` — mới | workflow_version, website_id hoặc null; null để đọc lựa chọn đã lưu | workspace hiện tại: website_id, revision, run_id, audit_id, browser_id, active_job_ids, trạng thái cần đối chiếu |
| `upload.website_select` — mới | workflow_version, website_id, expected_revision | workspace của website mới; từ chối khi còn hoạt động ở website cũ |
| `upload.env_check` — bổ sung | workflow_version, website_id | checklist đạt/cảnh báo/bị chặn, hướng dẫn đã lọc |
| `upload.session_start` — bổ sung | workflow_version, website_id, expected_revision | waiting_user(login); browser_id lấy qua workspace; trạng thái đăng nhập không chứa credential |
| `upload.confirm_login` — bổ sung | workflow_version, website_id, browser_id, target_job_id | xác nhận đúng job; backend vẫn kiểm trạng thái đăng nhập thật |
| `upload.session_status` — bổ sung | workflow_version, website_id, browser_id | đăng nhập, ID tab đang chuẩn bị/đã Lưu/đã đóng chưa rõ; không trả cookie |
| `upload.session_close` — bổ sung | workflow_version, website_id, browser_id | đã đóng, các ID đã xác minh và các ID cần đối chiếu |
| `upload.download_export` — bổ sung | workflow_version, website_id, browser_id, from_date, to_date | file_ref sổ tải xong kèm website và khoảng ngày |
| `upload.audit_excel` — bổ sung | workflow_version, website_id, file_ref, from_date, to_date | audit_id, summary, missing, issues; backend giữ tập số phục vụ đối chiếu |
| `upload.scan` — bổ sung | workflow_version, website_id, folder, expected_revision | run_id, manifest_ref trỏ tới **file**, stats, records và lỗi từng file |
| `upload.queue_get` — mới | workflow_version, website_id, run_id, audit_id hoặc null | queue_revision, folder_rows, missing_in_excel_record_ids, has_excel |
| `upload.staff_options` — mới | workflow_version, website_id, browser_id hoặc null, refresh | danh sách công chứng viên/cache đúng web; refresh thật cần browser |
| `upload.preferences` — mới | workflow_version, website_id; values khi lưu | chunk_size, cong_chung_vien, thu_ky; không nhận URL/token tự do |
| `upload.prepare` — bổ sung | workflow_version, website_id, browser_id, run_id, audit_id hoặc null, queue_revision, record_ids, chunk_size, cong_chung_vien, thu_ky | waiting_user(review), summary/breakdown cuối; cập nhật tab đang mở qua session_status |
| `upload.finish_review` — bổ sung | workflow_version, website_id, browser_id, target_job_id | kết thúc đúng bước kiểm tra; không tự đánh dấu uploaded_success |
| `upload.reconcile` — mới | workflow_version, website_id, run_id, audit_id mới | các ID đã xác minh có trên web và các ID còn cần kiểm tra; không tự gửi lại |

Các ràng buộc cần có trong contract và ví dụ kiểm chứng:

1. `website_id`, `browser_id`, `run_id`, `audit_id`, `record_ids` phải cùng phạm vi; tham chiếu sai bị từ chối trước khi mở tab. Backend tính danh sách loại trừ theo audit thật, không tin danh sách số do renderer tự dựng.
2. `manifest_ref` theo FileRef đã duyệt; backend giữ binding run→manifest và kiểm tồn tại/hash. Renderer không tự dựng path từ tên thư mục. Lỗi đọc registry/manifest phải là lỗi, không đổi thành thành công với danh sách rỗng.
3. `expected_revision` bảo vệ thay đổi nguồn/workspace; `queue_revision` bảo vệ queue đang gửi. Poll tiến độ không tự tăng revision nguồn, tránh làm thao tác hợp lệ bị từ chối liên tục.
4. Ngày qua boundary dùng ISO `YYYY-MM-DD`; UI hiển thị `DD/MM/YYYY`; bộ xử lý chuyển sang định dạng portal. Giá trị không có là null; ô không có ngày/ghi chú hiển thị trống theo MIN-77.
5. Không dùng khóa payload tên `session_id`: bộ lọc hiện tại chặn chuỗi `session`. `browser_id` là mã tham chiếu không bí mật, không mang quyền truy cập portal; mọi lệnh vẫn đi qua kiểm tra backend.
6. Lỗi dùng code và `next_action` đúng enum hiện hành. Chuẩn bị được một phần phải có `partial` và `data.breakdown={succeeded:[],failed:[]}`; mỗi mục nêu `record_id` và giai đoạn `prepared` hoặc `saved` để tránh hiểu nhầm.
7. Job vào waiting_user vẫn có thể theo dõi browser bằng lệnh trạng thái, không đưa result hoàn tất giả vào job đang chạy. Poll trạng thái được gộp, không chồng request; dọn kết quả truy vấn ngắn hạn khỏi bộ nhớ theo giới hạn xác định, giữ lịch sử thao tác có tác dụng thật cho recovery.
8. Một browser thread sở hữu mọi Playwright call, kể cả poll/close. Xác nhận cũ/khác website/khác job không giải phóng bước đang chờ.
9. Không thay nghĩa payload cũ âm thầm: `workflow_version` là lựa chọn tham gia luồng mới. Command cũ không có trường này giữ cách xử lý và data root legacy; không tự gán website rồi ghi vào kho mới. Consumer mới luôn gửi version và kiểm capability. Backend khóa không cho luồng cũ và mới đồng thời chiếm browser hoặc ghi dữ liệu Upload; lỗi xung đột phải rõ ràng. Việc bỏ hỗ trợ payload cũ là thay đổi phiên bản riêng sau này, không nằm trong đợt này. Task contract phải publish đầy đủ quy tắc tương thích trước runtime.
10. Hợp đồng dữ liệu website thứ hai chỉ được bổ sung khi có nguồn thật; các test chọn website khác dùng bộ xử lý giả nội bộ, không xuất hiện trong dropdown production.

## 5. Bản đồ file dự kiến

Tên file mới trong bảng là đích của các task, chưa được tạo trong lần lập plan này. Giữ module ID nội bộ `upload` để không ảnh hưởng registry hiện có; đổi nhãn hiển thị thành `Upload Lab`.

| Khu vực | File tạo/sửa | Trách nhiệm |
|---|---|---|
| Spec | Sửa `upload_lab/docs/spec_UI.md`, `upload_lab/README.md`; cập nhật phần Upload trong spec shell liên quan | Đồng bộ quyết định hai tab, bảng và website; dẫn một nguồn chính cho hành vi nội bộ. |
| Contract | Tạo `contracts/upload-workflow.md`, `contracts/upload-workflow/examples/`, `contracts/upload-workflow/validate_examples.py` sau review | Giao tiếp có version, ví dụ hợp lệ/không hợp lệ; cập nhật chỉ mục contracts. |
| Website | Tạo `upload_lab/providers/__init__.py`, `registry.py`, `nam_dinh.py` | Danh sách website và adapter mỏng tới engine hiện có. |
| Workspace | Tạo `shell/sidecar/upload_workspace.py`, `upload_workspace_store.py` | website/data root/revision, run–audit binding, thông tin đợt và recovery. |
| Chuyển dữ liệu | Tạo `upload_lab/tools/migrate_shell_data.py` | Kiểm kê và copy dữ liệu legacy có xác minh, không tự xóa nguồn. |
| Nối nghiệp vụ | Sửa `shell/sidecar/upload_adapter.py`, `upload_session.py`, `command_registry.py` | Gọi dịch vụ thật, scope dữ liệu và browser; thêm command sau contract. |
| Job | Sửa `shell/sidecar/jobstore.py`, `app.py`; tạo `shell/sidecar/job_repository.py` | Terminal không đổi ngược, lưu/khôi phục command/job cần thiết; hook đóng browser. |
| Shell dùng chung | Sửa `shell/src/main/{main,sidecar,config,registry,job-tracker,ipc}.js`, `shell/src/preload/preload.js` khi interface cần | Data path, capability, phục hồi job, quyền chọn/mở file; giữ API của module khác. |
| UI module | Tạo `shell/src/renderer/upload/{index,state,client,audit,scan-upload}.js`, `upload.css` | Điều hướng hai tab, state chung, command binding, từng trang và style giới hạn trong module. |
| Gắn UI | Sửa `shell/src/renderer/{renderer,lib}.js`, `index.html`, `styles.css` | Đưa Upload view ra file riêng, đăng ký script/style local và nhãn; không viết lại view Notary. |
| Package | Sửa `shell/sidecar/{requirements.txt,g1-shell-sidecar.spec}`, `shell/package.json`, `shell/README.md`; thêm cấu hình test build `shell/test/build-upload-test.ps1` | Bundle engine/dependency/Chromium cần thiết; code read-only, dữ liệu user-writable; bản kiểm thử tách biệt bản sử dụng thật. |
| Test engine | Thêm `upload_lab/tests/test_website_providers.py`, `test_shell_data_migration.py`; giữ tests hiện có | Provider hiện tại tương đương, dữ liệu chuyển an toàn. |
| Test bridge | Thêm `shell/test/test_upload_workflow.py`, `test_upload_browser_workflow.py`, `test_upload_recovery.py`; sửa tests job/contract | Scan→audit→queue→prepare, lifecycle, lỗi và recovery. |
| Test UI/package | Thêm `shell/test/upload-state.test.mjs`, `upload-routing.test.mjs`, `test_upload_e2e.py`, `fixtures/upload_portal.py` | State, cấu trúc hai tab, fake portal trên localhost và packaged flow bằng dữ liệu giả. |

Interface nội bộ đề xuất để các task dùng cùng tên:

| File | Hàm/phương thức | Kết quả và điều kiện |
|---|---|---|
| `upload_lab/providers/registry.py` | `list_websites()` | Danh sách cấu hình website công khai đã đăng ký. |
| `upload_lab/providers/registry.py` | `get_provider(website_id)` | Trả `NamDinhProvider` cho `nam_dinh`; ID không biết trả lỗi `unknown_website`. |
| `upload_lab/providers/nam_dinh.py` | `NamDinhProvider.create_browser(data_dir)` | Tạo phiên engine hiện có; chỉ gọi trong luồng thực thi sở hữu browser. |
| `upload_lab/providers/nam_dinh.py` | `NamDinhProvider.audit_excel(path, from_date, to_date)` | Đọc sổ theo cấu trúc Nam Định, trả kết quả chung đã quy định. |
| `shell/sidecar/upload_workspace.py` | `website_data_dir(website_id)` | Kiểm ID rồi trả đường dẫn nằm trong vùng dữ liệu đã cấp. |
| `shell/sidecar/upload_workspace.py` | `resolve_run(website_id, run_id)` | Trả đường dẫn manifest đã lưu và kiểm chứng thuộc đúng website/run. |
| `shell/sidecar/upload_workspace.py` | `require_same_website(website_id, actual_website_id)` | Không thay dữ liệu; từ chối nếu hai ID khác nhau. |

Đây là giao tiếp nội bộ dự kiến để chia việc. Task contract phải khóa cấu trúc dữ liệu trả về thành schema đầy đủ; không cho UI đọc SQLite trực tiếp.

## 6. Trình tự triển khai

`T1: đặc tả + contract → T2: website + vùng dữ liệu → T3: audit/scan/queue → T4: browser → T5: recovery → T6: UI hai tab → T7: nối Audit → T8: nối Upload → T9: package/pilot → T10: chuyển mặc định`

T6 có thể dựng layout bằng fixture sau T1; thao tác thật chỉ được nghiệm thu khi phần backend tương ứng đã qua kiểm tra. Các task là đơn vị chia issue/review, không phải cam kết làm trong một lần chạy. Trạng thái và bằng chứng nằm ở Linear và `.agent/tasks/<ID>/` theo AGENTS.md.

### Task 1: Khóa đặc tả và publish contract, chưa sửa runtime

**Files:** Sửa `upload_lab/docs/spec_UI.md`, `upload_lab/README.md`; review phần Upload của `docs/product/specs/2026-09-14-module-transition-ux-spec.md`; tạo contract/examples/validator tại các đường dẫn §5 sau owner review. Không ghi đè phần Zalo/Notary đang được sửa.

**Consumes:** §1–4, MIN-69, MIN-77, desktopcommand.v1 và g1.module.v1.

**Produces:** Spec UI duy nhất cho Upload Lab và upload.workflow.v1 đã duyệt, có bảng request/result/error/version/capability đầy đủ.

- [ ] Chốt nội dung §1 vào spec UI hiện có, thay phần ba bảng/năm cột đã cũ. Ghi rõ bỏ trang nhật ký, giữ thông báo inline và dữ liệu phục hồi.
- [ ] Lập schema chính xác cho toàn bộ command §4, bao gồm sửa khác biệt `file` hiện tại sang `file_ref` trong luồng có version và chính sách consumer cũ.
- [ ] Thêm ví dụ cho đúng website/run, sai website, ID ngoài run, revision cũ, manifest mất, xác nhận sai job, partial, browser busy, restart và website chưa hỗ trợ.
- [ ] Validator phải từ chối sai phạm với mã xác định; kiểm trường null, date, chunk_size 1–30, khóa nhạy cảm và đúng envelope.
- [ ] Review/publish contract trong issue riêng; chỉ sau đó mở task runtime phụ thuộc. Đối chiếu MIN-69 về review/edit: plan giữ cách sửa tại source/portal hiện có, không tự đánh dấu hoàn tất yêu cầu rộng hơn.

**Check:** `python contracts/upload-workflow/validate_examples.py` và `python contracts/g1/validate_examples.py`; tất cả ví dụ hợp lệ pass, ví dụ lỗi bị từ chối đúng mã. Kiểm diff tài liệu và link. Không cần chạy test runtime cho thay đổi chỉ Markdown/schema.

### Task 2: Website registry và vùng dữ liệu độc lập

**Files:** Tạo providers và workspace/store/migration tool trong §5; sửa `upload_adapter.py`, `upload_session.py` để tách engine root với data root; cấu hình main/sidecar truyền `G1_UPLOAD_DATA_DIR`. Thêm hai test engine đã liệt kê.

**Consumes:** Website ID/capability/revision và cơ chế phiên bản T1.

**Produces:** Danh mục có đúng Nam Định đang hoạt động; mọi đường ghi/upload data có website owner; tiện ích copy dữ liệu có kiểm chứng.

- [ ] Viết test registry: chỉ hiện backend thật, unknown ID báo lỗi, cùng record ID của hai website giả không trùng trạng thái. Hai website giả chỉ được inject từ test.
- [ ] Chạy `python -m unittest discover -s tests -p test_website_providers.py` trong `upload_lab`; xác nhận fail đúng vì chưa có provider.
- [ ] Adapter Nam Định gọi engine cũ; kiểm tra data_dir đã resolve thuộc data root. Không đọc `.env` tự do rồi trả toàn bộ cho UI; chỉ trả các giá trị công khai trong schema.
- [ ] Lưu cấu hình số tab/nhân sự theo website; session/cache/registry/runs không dùng lại của website khác. Khóa đổi website khi tác vụ hoặc tab cần kiểm tra còn tồn tại.
- [ ] Tool migration có `--inspect --source PATH --target PATH` để in số lượng/trạng thái đã lọc và `--apply` chỉ chạy khi target chưa có dữ liệu. Backup SQLite bằng API snapshot phù hợp; copy file, kiểm hash/count, đổi path nội bộ trong bản sao, kiểm liên kết; không overwrite nguồn/target có dữ liệu.
- [ ] Test trên thư mục tạm: source không đổi, target đúng ID/trạng thái/hash, chạy lại không nhân đôi, nguồn sai website bị từ chối, thiếu JSON/manifest báo rõ và không kích hoạt target chưa đủ.

**Check:** hai test provider/migration mới và test đọc/lưu cấu hình cũ trong `tests/test_playwright_uploader.py`.

### Task 3: Audit, scan và hàng đợi gắn đúng lượt

**Files:** Sửa `shell/sidecar/upload_adapter.py`, `command_registry.py`; tạo `test_upload_workflow.py`; dùng lại `folder_workflow_service.py`, `contract_book_audit.py`, `scan_classification_service.py`. Chỉ sửa engine khi có test chứng minh adapter hiện có không đủ.

**Consumes:** Provider/data root T2; schema scan/audit/queue T1.

**Produces:** run_id + file manifest thật, audit_id + nguồn sổ, queue_revision + dòng phân loại đúng website.

- [ ] Viết test lỗi scan→prepare: tự sinh DOCX và Excel trong TemporaryDirectory, không dựa thư mục downloads cá nhân. Kiểm manifest là file của chính run_id và mọi record thuộc run đó.
- [ ] Chạy `python test/test_upload_workflow.py` trong `shell`; test phải fail với cầu nối cũ.
- [ ] Dùng `run_folder_scan` với `folder_path`, `modified_since`, `full_rescan`, `progress_callback` và `working_dir` của website; dịch vụ này đã gọi `finalize_manifest` đúng một lần. Lưu mapping run→manifest trong workspace; bỏ fallback lấy file mới nhất cho workflow mới.
- [ ] Nạp Excel theo provider, lưu audit_id kèm website, khoảng ngày và dấu nhận diện file; trả summary cùng hai bảng. `.xls` chỉ bật nếu có đường đọc thật đã kiểm chứng; `.xlsx/.xlsm` theo khả năng engine và fixture, không dựa mỗi filter hộp thoại.
- [ ] Dùng `classify_scan_records` từ Python; trả đủ ngày/ghi chú/has_issue/selected/default IDs. Không viết lại quy tắc phân loại ở JS. Giữ tập số audit để loại trùng ở prepare.
- [ ] Test không có Excel, có số thiếu, số sai, năm sai, leading zero, trùng local, lỗi đọc registry, Excel đổi, hai lượt quét A/B, request B mang ID/manifest A. Trường hợp sai binding phải fail trước Playwright.

Ví dụ assertion bắt buộc sau khi helper fixture `run_scan_fixture()` được tạo trong cùng test:

```python
result = run_scan_fixture()
ref = result["data"]["manifest_ref"]
self.assertTrue(Path(ref["path"]).is_file())
manifest = json.loads(Path(ref["path"]).read_text(encoding="utf-8"))
self.assertEqual(manifest["run_id"], result["data"]["run_id"])
self.assertEqual(result["data"]["website_id"], "nam_dinh")
```

Helper này phải tạo tài liệu không có dữ liệu thật, gọi command registry qua Job thật với data root tạm; test truyền đủ payload T1. Không chỉ mock kết quả manifest rồi assert lại dữ liệu mock.

### Task 4: Phiên browser, tải sổ và từng đợt chuẩn bị

**Files:** Sửa `shell/sidecar/upload_session.py`, `upload_adapter.py`, `command_registry.py`; thêm `test_upload_browser_workflow.py` và `fixtures/upload_portal.py`; tham chiếu `upload_lab/ui_qt/workers.py`, `playwright_uploader.py`.

**Consumes:** run/audit/queue của T3; browser/job identity trong T1.

**Produces:** login, tải sổ, làm mới nhân sự, prepare tối đa N tab, poll Lưu, dừng/tiếp tục/đóng đúng hành vi hiện có.

- [ ] Test bằng fake session nhận biết thread ID: tất cả login/download/staff/prepare/poll/close phải cùng một browser thread; event xác nhận cho job A không đánh thức job B.
- [ ] Chạy `python test/test_upload_browser_workflow.py`, thấy fail với global events và thiếu poll hiện tại.
- [ ] Thay event global bằng trạng thái theo website/browser/job; cho phép tối đa một tác vụ browser có thay đổi tại một thời điểm. Status query đọc snapshot, không tạo browser ngầm.
- [ ] Phần idle của browser loop poll login và prepared pages; khi operation dài chạy, nhận progress/callback để cập nhật, không gọi Playwright từ timer/thread khác. Poll tiếp trong lúc chờ người review.
- [ ] Prepare lấy manifest qua run binding; truyền `selected_record_ids`, danh sách loại trừ backend tính, `chunk_size`, công chứng viên, thư ký. Giữ override/lookup hiện hành của provider nếu đang dùng; không mở thêm nguồn dữ liệu Internet.
- [ ] Tách count đã điền và đã Lưu. Callback Save đã xác minh mới ghi uploaded_success và bỏ dòng khỏi queue. Tab bị đóng mà thiếu bằng chứng Save giữ trạng thái cần kiểm tra/chưa lưu.
- [ ] Tải Excel sử dụng cùng browser của website, trả file đã hoàn tất; download gián đoạn không được audit như file đầy đủ. Chuẩn hóa ngày tại adapter.
- [ ] Dừng đặt stop event; chờ operation nhả browser trước khi cho đợt mới/đổi web. Đóng phiên kiểm tra kết quả còn đọc được rồi đóng; không tự bấm Lưu.

**Check:** fixture portal có login, trang tạo và Save giả trên localhost; các ca 0/1/N/N+1 hồ sơ, lỗi một mục, đóng tab tay, hết phiên, nút xác nhận bấm sớm/trễ, mất browser và không cướp focus. Test không gọi cổng thật.

### Task 5: Kết quả một phần, hủy và khôi phục sau gián đoạn

**Files:** Sửa `jobstore.py`, `app.py`, `job-tracker.js`, `upload_adapter.py`; tạo `job_repository.py`, `test_upload_recovery.py`; sửa `test_jobstore.py`, `test_sidecar_contract.py`.

**Consumes:** Lifecycle/breakdown T1 và browser state T4.

**Produces:** Không ghi đè terminal state, không báo “đã Lưu” nhờ prepare, không phát lại upload sau restart khi kết quả chưa rõ.

- [ ] Test cuộc đua hủy/hoàn tất: giữ handler tại một điểm bằng Event kiểm soát từ test, hủy trong waiting_user, cho handler tiếp tục; terminal cuối vẫn canceled. Không dùng sleep tùy ý để tạo lỗi timing.
- [ ] Chạy `python test/test_jobstore.py` và `python test/test_upload_recovery.py`; test hồi quy phải fail trước sửa.
- [ ] Mọi transition report/resume/finish kiểm terminal dưới lock. Kết quả chuẩn bị có lỗi chuyển partial với breakdown; toàn bộ mục lỗi chuyển failed. Error next_action theo enum, không trả câu tự do ở trường này.
- [ ] Repository lưu command identity và snapshot cần khôi phục; dùng SQLite hiện có, không tạo scheduler thứ hai. Test restart bằng instance store mới trên cùng tệp tạm: job dở thành engine_restarted, command cũ không chạy lại handler.
- [ ] Renderer/main reconnect theo ID; thử lại có chủ ý là thao tác mới sau khi kiểm tra scope/queue/reconciliation. Tắt retry tự động cho prepare khi còn hồ sơ chưa rõ đã Lưu.
- [ ] Reconcile cần audit mới bao phủ số/ngày liên quan. Hồ sơ đã thấy trên web được chặn chuẩn bị lại; vắng trong sổ chưa đủ phạm vi hoặc có lỗi vẫn Cần đối chiếu. Không suy idempotency key còn trong RAM là đủ chống trùng nghiệp vụ.
- [ ] Shutdown ngừng nhận lệnh, yêu cầu dừng, reconcile nếu còn kết nối, đóng browser trong thread owner; quá thời hạn thì giữ thông tin chưa rõ để lần sau kiểm tra. Test không để browser con sống vô chủ.

**Check:** engine/process crash trước prepare, trong prepare, sau Save nhưng trước ghi registry; mất browser; cancel/finish đồng thời; cùng command khác payload; partial đúng hồ sơ. Chạy lại tests shell chung vì JobStore phục vụ cả module khác, không chỉ Upload.

### Task 6: Khung UI hai tab và trạng thái dùng chung

**Files:** Tạo `shell/src/renderer/upload/{index,state,client,audit,scan-upload}.js`, `upload.css`; sửa renderer/lib/index/styles hiện có; thêm `upload-state.test.mjs`, `upload-routing.test.mjs`.

**Consumes:** Schema T1, màu/kích thước từ `upload_lab/ui_qt/theme.py`, chuẩn bảng MIN-77.

**Produces:** Hai tab riêng chiếm toàn chiều rộng, state dùng chung, không tab nhật ký/cấu hình, không ảnh hưởng các module khác.

- [ ] Viết test state cho đổi tab không mất ô chọn/ngày/scroll; nhận kết quả sai website/run/job bị bỏ qua; chuyển website không mang queue cũ theo.
- [ ] Chạy `node --test test/upload-state.test.mjs test/upload-routing.test.mjs` trong shell; thấy fail vì chưa có module.
- [ ] Tách `buildUploadView` khỏi renderer lớn, truyền dependency `api`, jobs và notify qua tham số; giữ helper chung ổn định. Các file UI expose một namespace local `window.G1_UPLOAD`, không thêm bundler/framework.
- [ ] Module state chỉ có một `websiteId`; hai tab đọc cùng state. Thêm các hàm thuần `createUploadState()`, `selectTab(state, tabId)`, `acceptScopedResult(state, scope)` để test bằng node; scope gồm websiteId/runId/jobId.
- [ ] CSS giới hạn dưới `.upload-lab`, `width:100%`, `max-width:none`, `min-width:0`; thay giới hạn cũ bằng class riêng khi module upload đang mở, không sửa rộng toàn bộ layout Notary.
- [ ] Theme sáng, thẻ/nút/bảng theo baseline; header compact. Bảng có scroll riêng, cột đường dẫn truncate, thanh nút wrap ở cửa sổ hẹp. Keyboard focus rõ và tab ARIA đúng.

Ví dụ test state sau khi định nghĩa ba hàm đúng chữ ký trên:

```javascript
const state = createUploadState();
state.websiteId = 'nam_dinh';
state.runId = 'run_b';
state.scanJobId = 'job_b';
state.selectedIds = new Set([12]);
selectTab(state, 'audit');
selectTab(state, 'scan-upload');
assert.deepEqual([...state.selectedIds], [12]);
assert.equal(acceptScopedResult(state, {
  websiteId: 'nam_dinh', runId: 'run_a', jobId: 'job_a'
}), false);
```

**Check:** UI thật ở 1440×900, 1280×820, 760×520 và Windows scale 125%/150%; không kiểm “rộng” chỉ bằng snapshot HTML. Không cần giống từng pixel Qt, nhưng không được mất dòng/cột/chức năng đã chốt.

### Task 7: Nối trọn tab Audit

**Files:** Sửa `upload/audit.js`, `upload/client.js`, `upload/state.js`; bổ sung UI assertions trong `test_upload_e2e.py`.

**Consumes:** Website/workspace T2, audit T3, login/download T4, khung T6.

**Produces:** Chọn web → kiểm tra/đăng nhập → tải/chọn Excel → audit → bốn KPI và hai bảng đúng nguồn.

- [ ] Viết E2E bắt buộc chỉ có hai tab, dropdown nằm trước bộ lọc ngày, không ô URL nhập tay và không trang nhật ký.
- [ ] Viết ca chọn Excel tự nạp, tải Excel tự nạp, đổi ngày làm kết quả cũ không còn được sử dụng, lỗi nạp xóa kết quả hiện hành; backend response trễ của website cũ bị bỏ qua.
- [ ] Dùng catalog backend để render lựa chọn; nút theo capability/đăng nhập/busy. Lỗi website hiện ngay cạnh nút và có hướng dẫn hành động, không raw JSON.
- [ ] Nối file picker qua main; bổ sung `.xlsm` khi đã xác minh parser. Mở file `.doc/.docx/.xlsx/.xlsm` từ UI phải qua allowlist main và FileRef có nguồn, không mở path tùy ý hay UNC của scope ngoài hợp đồng.
- [ ] Render bốn KPI và hai bảng, giữ cột MIN-77, vị trí chia bảng/scroll. Header tên web luôn khớp audit_id đang hiển thị.

**Check:** `python test/test_upload_e2e.py --case audit` chạy dữ liệu giả trên app dev qua test harness, có thất bại rõ nếu Electron/fixture thiếu; không skip để tạo kết quả xanh.

### Task 8: Nối trọn tab Quét & Upload

**Files:** Sửa `upload/scan-upload.js`, `upload/state.js`, `upload/client.js`; cập nhật quyền mở file trong main/preload nếu T1 yêu cầu; bổ sung `test_upload_e2e.py`.

**Consumes:** Queue T3, browser T4, recovery T5 và UI T6.

**Produces:** Luồng tương đương Qt về chọn hồ sơ, từng đợt, dừng/tiếp tục, nhận biết Lưu và cập nhật bảng.

- [ ] Viết E2E hai lượt scan A/B rồi cố gửi ID A trong run B; backend từ chối, không mở tab. Test đổi tab trong lúc scan/prepare vẫn giữ state và tiến độ.
- [ ] Viết ca selection: chọn mặc định số thiếu, bỏ chọn thủ công vẫn giữ khi poll; chọn tất cả/bỏ chọn/lọc lỗi/hoàn tác/chọn số thiếu; double-click mở đúng file nguồn.
- [ ] Nối nhân sự và số tab theo website; không tự chọn thay giá trị người dùng để trống. Nút Upload/Continue/Stop/Close bật/tắt theo state backend, đếm số chọn và khả năng thao tác.
- [ ] Gửi prepare với đúng browser/run/audit/revision và ID. Theo dõi session status trong lúc chờ review; chỉ remove các ID được xác minh đã Lưu. Không render lại toàn table làm mất focus/scroll/ô chọn mỗi lần nhận job.
- [ ] Nút Tiếp tục giữ tập hồ sơ ban đầu đã chọn trừ các mục xử lý xong/đang mở; không tự thêm hồ sơ ngoài tập đó. Hủy hoặc lỗi không kích hoạt đợt kế tiếp.
- [ ] UI recovery nêu số hồ sơ cần đối chiếu ngay trong bảng/thanh trạng thái; yêu cầu audit mới khi cần, không đưa người dùng tới trang log đã bỏ.

**Check:** `python test/test_upload_e2e.py --case upload`; fixture 31 hồ sơ, chunk 10, lỗi mục thứ 3, bỏ chọn mục thứ 5, Save hai mục rồi dừng/đóng/restart. Assert cả tab browser, DB tạm và UI; không chỉ kiểm nút hiện lên.

### Task 9: Package Windows và pilot có đối chiếu

**Files:** Sửa package/sidecar build config và README tại §5; hoàn thiện `test_upload_e2e.py`; kiểm tra các tests hiện có để tách fixture tạm khỏi dữ liệu cá nhân.

**Consumes:** Toàn bộ T2–T8 đã pass.

**Produces:** Gói Electron tự mở và chạy Upload/Audit bằng engine thật trên máy không có repo dev.

- [ ] Bundle đúng module Python/dependency dùng cho Upload Lab; bổ sung python-dotenv/openpyxl/Playwright và module engine cần import động. Kiểm version từ bộ đã chạy pass rồi khóa bản build; không tự nâng framework trong chặng này.
- [ ] Đóng gói engine theo namespace/root xác định và thử import từ bản frozen. Không kéo `ui_qt` vào đường chạy; kiểm không có cửa sổ Qt ẩn và không cần launcher Python cũ.
- [ ] Bundle/provision đúng Chromium tương ứng bản Playwright dùng trong build, nêu vị trí rõ. Build test bằng cache sạch; app chạy bình thường không tự cài dependencies qua mạng.
- [ ] App cấp đường dẫn data root writable cho Python; update thay code không xóa data/session. Test không có quyền ghi vào folder cài nhưng scan/audit/upload vẫn chạy ở userData.
- [ ] Chạy full suite trên fixture tạm. Sửa `test_engine_adapters.py` để Upload tests tự tạo fixture và chỉ chạy class Upload khi phù hợp; không chạy test Notary tạo dữ liệu trong DB thật.
- [ ] Thêm `shell/test/build-upload-test.ps1` và script `npm run dist:test`: đóng gói cùng source engine/UI nhưng có provider fixture chỉ trong bản kiểm thử, appId `dev.g1.shell.test`, productName `g1-shell-test`, output `dist-test` và userData riêng. Cấu hình fixture chỉ nhận từ test harness tin cậy, giới hạn localhost; không qua renderer. Bản production không chứa provider này hoặc nhận URL override cho nó. Không để build test ghi đè sidecar/gói production.
- [ ] Chạy gói production bằng `--case offline` để kiểm scan/audit/data root không cần portal; chạy gói kiểm thử bằng `--case all` để kiểm trọn luồng với portal localhost. Harness phải hỗ trợ rõ `--case audit`, `upload`, `offline`, `all`; kiểm nhãn build và từ chối ca dùng portal giả trên gói production.
- [ ] Trên máy sạch: `.doc` thật đã khử thông tin riêng, `.docx`, Excel, đường dẫn tiếng Việt/dài, file hỏng/đang bị khóa, cửa sổ chia màn hình nhỏ, tỉ lệ hiển thị Windows; ghi rõ pass/fail từng trường hợp.
- [ ] Pilot trên website thật có người thao tác: kiểm queue và biểu mẫu điền sẵn; người dùng quyết định Lưu. Không chạy Qt và Electron đồng thời ghi cùng portal/registry.

**Lệnh kiểm chứng sau khi các task đã tạo đủ test/script, thực hiện trong môi trường test:**

```powershell
# Từ upload_lab/, dùng Python của môi trường test
python -m unittest discover -s tests

# Từ shell/
npm test
python test/test_sidecar_contract.py
python test/test_jobstore.py
python test/test_upload_workflow.py
python test/test_upload_browser_workflow.py
python test/test_upload_recovery.py
npm run build:sidecar
npm run dist
python test/test_upload_e2e.py --app dist-app/win-unpacked/g1-shell.exe --case offline
npm run dist:test
python test/test_upload_e2e.py --app dist-test/win-unpacked/g1-shell-test.exe --case all

# Từ root repo
python contracts/g1/validate_examples.py
python contracts/upload-workflow/validate_examples.py
```

Các test/script mới chỉ chạy sau task tạo chúng. Harness E2E dùng công cụ Playwright đã chọn trong TECH_STACK; automation Electron là harness kiểm thử riêng, không thay cách production điều khiển portal. Bài smoke hiện có chỉ `file.inspect` không đủ để công nhận chuyển Upload Lab.

### Task 10: Đổi ứng dụng mặc định và kiểm chứng quay lại

**Files:** Cập nhật `shell/README.md`, `upload_lab/README.md`, spec UI đã thống nhất; ghi bằng chứng ở `.agent/tasks/<ID>/` của issue triển khai. Không xóa launcher/repo Qt trong task này.

**Consumes:** Gói Windows và báo cáo pilot T9; bản sao dữ liệu đã kiểm chứng T2.

**Produces:** Người dùng hoàn thành cả hai luồng trên shell mới; có thể quay lại bản cũ mà không gửi trùng hoặc mất kết quả đã Lưu.

- [ ] Chốt revision/build/engine/provider và bộ fixture được dùng làm mốc. Kiểm kê dữ liệu nguồn/đích, đợt đang dở và tài liệu trích xuất liên quan trước chuyển.
- [ ] Diễn tập rollback trên dữ liệu giả: đóng sidecar/browser, đối chiếu thành công trên portal fixture, mở Qt bằng **bản sao dữ liệu đã đối chiếu**; giữ bản legacy gốc và bản Electron để truy vết.
- [ ] Không chép đè registry cũ lên các hồ sơ đã Lưu trong pilot. Đưa các thành công mới đã xác minh vào bản dữ liệu dùng để quay lại; các mục chưa rõ tiếp tục bị chặn gửi lại.
- [ ] Sau nghiệm thu của người dùng, đổi shortcut/entrypoint mặc định sang Electron; kiểm mở lại, chọn web và chạy hai tab. Đây là bước triển khai riêng, không nằm trong lần viết plan.
- [ ] Cập nhật tài liệu hiện trạng: phần nào đã nối thật, phần nào chưa kiểm chứng; không đánh dấu LAN/toàn G1 hoặc toàn MIN-69 Done chỉ từ việc hoàn thành hai tab.

## 7. Ma trận nghiệm thu tối thiểu

| Nhóm | Phải chứng minh |
|---|---|
| Bố cục | Một module, hai tab rộng, đúng số/cột bảng, không tab Nhật ký, cấu hình nằm đầu Audit. |
| Website | Cùng lựa chọn ở cả hai tab; backend route đúng; không nhận unknown ID hoặc state của website khác. |
| Audit | Tải/chọn sổ thật, auto-load, đúng bốn KPI và hai bảng, file lỗi không hiện kết quả cũ như mới. |
| Scan/queue | Manifest là file của đúng run; phân loại giống Python/Qt; ID ngoài run bị từ chối. |
| Chọn hồ sơ | Giữ bỏ chọn thủ công, lọc/hoàn tác đúng, row order và mở file đúng, quét mới không giữ ID cũ. |
| Upload | Nhân sự/số tab đúng; prepare không Save; người dùng tự Lưu; tiếp tục có chủ ý. |
| Tiến độ/kết quả | Scan và prepare tách riêng; đã chuẩn bị khác đã Lưu; partial/lỗi đúng từng hồ sơ. |
| Browser | Một thread owner, cùng web/cùng phiên, xác nhận đúng job, poll saved liên tục, không giật focus. |
| Hủy/restart | Terminal không đổi ngược, không phát lại mù, kết quả chưa rõ cần đối chiếu, không gửi trùng sau crash. |
| Dữ liệu/package | Code và data riêng, copy có hash/count, app chạy trên máy sạch, update/rollback giữ thành công đã Lưu. |
| Hồi quy shell | Module khác vẫn hoạt động, đổi module giữ job, IPC/token/file policy còn đúng. |

Mỗi dòng phải có test hoặc thao tác kiểm chứng ghi lại được. Các trường hợp portal thật chưa được đo phải ghi chưa kiểm chứng; không lấy fixture giả làm bằng chứng portal thật.

## 8. Điểm kết thúc của kế hoạch này

Kết quả mong muốn là bản Upload Lab trong Electron giữ được công việc và trải nghiệm hiện tại, với hai tab rộng và lựa chọn website chung. Website thứ hai được thêm sau bằng backend riêng khi có thông tin; không cần đổi khung giao diện. Chuyển đổi không bao gồm tái thiết kế toàn shell, thay database chung, LAN hay chức năng mới ngoài các quyết định đã ghi.

Trong lần lập plan chỉ đọc source/Linear và tạo tài liệu này; chưa chạy test runtime, mở portal, di chuyển dữ liệu hoặc sửa code. Graphify/context-mode không được cung cấp trong phiên, nên bằng chứng dùng tìm kiếm và đọc source trực tiếp. Không có thay đổi trạng thái issue Linear hay commit tự động.
