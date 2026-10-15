# Upload — đối chiếu kho Word và điền website

**Cập nhật:** 15/10/2026. Spec hành vi module; giữ phân biệt hướng được duyệt, đề xuất thị giác và giới hạn code đã quan sát.

## 1. Mục đích và luồng

Đọc Word cũ vì phần mềm văn phòng chưa có API lấy dữ liệu. Không tự đổi sang API/DB nguồn khác khi chưa chốt. Luồng: chọn website/đăng nhập → lấy sổ Excel → quét Word → đối chiếu/chọn hồ sơ → bóc trường → điền form → người dùng tự Lưu → xác minh hoặc đối chiếu lại.

DOC qua IFilter; DOCX giữ thứ tự đoạn/bảng để không trộn bên. Bóc người, người yêu cầu, tài sản, số/ngày công chứng, công chứng viên và loại văn bản. Kết quả giữ JSON, registry SQLite và manifest theo lượt quét; theo bộ trường DB/contract, không tự gộp hoặc suy dữ liệu thiếu. Chuẩn số công chứng hiện hành là xxx/yyyy; phân biệt năm và website, không suy số thứ tự là mã hồ sơ chung.

<a id="ui"></a>
## 2. Màn hình và thao tác

### 2.1. Điều hướng và không gian bảng

Shell có một module chính tên **Upload Lab** (module id nội bộ `upload`). Bên
trong có đúng hai tab:

1. **Audit Sổ Công Chứng**
2. **Quét & Upload Hồ Sơ**

- Mỗi tab chiếm **toàn bộ chiều rộng** phần nội dung còn lại của shell.
- Không có sidebar thứ hai trong Upload Lab; không xếp Audit và Upload cạnh
  nhau; không gộp thành một trang dài nhiều khối đóng/mở.
- **Không có tab Cấu hình và không có tab/trang Nhật ký riêng.** Chức năng
  cấu hình/kiểm tra môi trường nằm đầu tab Audit (mục 2); log chẩn đoán chỉ
  tồn tại ở backend đã lọc, không hiển thị thành trang.
- Bỏ trang Nhật ký **không có nghĩa** mất thông báo kết quả hay dữ liệu phục
  hồi: kết quả/lỗi hiển thị inline tại vùng liên quan và trạng thái khôi phục
  vẫn được backend lưu trữ.

#### Giữ trạng thái khi chuyển đổi

Đổi tab hoặc sang module khác rồi quay lại phải giữ nguyên:

- website đang chọn, khoảng ngày, đường dẫn file Excel/thư mục đã chọn;
- kết quả audit, kết quả quét và phân loại đang hiển thị;
- ô chọn hồ sơ, lựa chọn đã lọc, vị trí cuộn;
- tác vụ đang chạy (scan, tải Excel, prepare) và tiến độ của nó.

Bảng có vùng cuộn riêng và tiêu đề cột cố định. Đường dẫn file dài được cắt
gọn trong ô nhưng **không kéo vỡ bố cục**; xem đủ đường dẫn bằng tooltip và
mở file gốc trực tiếp từ dòng đó (mở bằng ứng dụng mặc định của Windows, qua
Electron main).

### 2.2. Tab Audit Sổ Công Chứng

Thứ tự các vùng từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Chọn website | Dropdown tên website; trạng thái kết nối/đăng nhập; nút kiểm tra môi trường và mở đăng nhập. Địa chỉ website có thể hiển thị chỉ-đọc để nhận biết. Không có ô nhập URL tự do. |
| Nguồn sổ | `Từ ngày`, `Đến ngày` (hiển thị `DD/MM/YYYY`), nút `Tải Excel từ Web`; ô đường dẫn + `Chọn tệp Excel...` và `Nạp dữ liệu`. |
| Số liệu | Bốn thẻ KPI: **Tổng số đã nạp**, **Hợp lệ trong sổ**, **Số còn thiếu**, **Lỗi / Trùng lặp**. |
| Bảng | Hai vùng **Số còn thiếu** và **Số lỗi, trùng** xếp trên/dưới, cùng toàn chiều rộng, kéo chia chiều cao được. |

Cả hai bảng dùng đúng **bốn cột** (chuẩn MIN-77):

`STT | Ngày | Số công chứng | Ghi chú`

- Không đưa lại bảng "Danh sách Excel"/số hợp lệ; không có cột `Số dòng`,
  `Năm`, `Loại lỗi`, `Số chuẩn`, `Số gốc` — đã loại ở MIN-77.
- Ô không có ngày hoặc ghi chú hiển thị trống. Số thiếu do chính nó lỗi/trùng
  chỉ nằm ở bảng lỗi, không lặp lại ở bảng thiếu.

#### Quy tắc nạp và làm mới

- Chọn file trên máy hoặc tải Excel thành công → **tự nạp và audit** theo
  khoảng ngày đang chọn (giữ hành vi Qt); người dùng vẫn có `Nạp dữ liệu` để
  chạy lại sau khi đổi ngày.
- Đổi ngày hoặc đổi file → kết quả cũ được đánh dấu *chưa cập nhật*; không
  được trình bày kết quả cũ như kết quả của bộ lọc mới.
- Nạp lỗi → vùng hiện tại báo lỗi rõ ngay tại chỗ, **không giữ số liệu cũ**
  dưới nguồn mới.
- Thông báo kiểm tra môi trường hiển thị ở khối đầu trang khi cần (checklist
  đạt/cảnh báo/bị chặn + hướng dẫn đã lọc); trạng thái bình thường chỉ chiếm
  một hàng gọn. Ưu tiên chiều cao cho hai bảng.

### 2.3. Tab Quét & Upload Hồ Sơ

Thứ tự các vùng từ trên xuống:

| Vùng | Nội dung |
|---|---|
| Ngữ cảnh | Tên website đang dùng, trạng thái đăng nhập, nguồn Excel/khoảng ngày đang đối chiếu; nút quay sang tab Audit để đổi website. |
| Nguồn và nhân sự | `Chọn thư mục`/`Bắt đầu Quét`; Công chứng viên (dropdown), Thư ký (nhập tay), `Cập nhật danh sách`; `Số tab mỗi đợt` từ **1 đến 30**, mặc định **10** nếu chưa có giá trị đã lưu. |
| Tiến độ | Tiến độ quét và tiến độ chuẩn bị biểu mẫu là **hai thanh riêng**; nút `Dừng` bật theo trạng thái đang chạy. |
| Thanh thao tác | `Chọn tất cả`, `Bỏ chọn tất cả`, `Lọc số lỗi`/`Hoàn tác lọc`, `Số thiếu trong Excel`, `Upload file đã chọn (N)`, `Tiếp tục N số tiếp theo`, `Đóng browser upload`. |
| Bảng | Một bảng hồ sơ toàn chiều rộng, cột đúng thứ tự bên dưới. |

Bảng hồ sơ dùng đúng **sáu cột** (chuẩn MIN-77):

`✓ | STT | Ngày | Số công chứng | Ghi chú | Địa chỉ file`

#### Quy tắc chọn và phân loại (giữ nguyên từ hiện hành)

- **Chưa có Excel**: vẫn cho quét và xem hồ sơ; không tự chọn là "thiếu trên
  web".
- **Có Excel cùng website**: chọn mặc định các số hợp lệ chưa có trong sổ;
  giữ ghi chú cho số sai format, sai năm, thiếu trường, trùng trong folder.
- Người dùng bỏ chọn thủ công → poll/cập nhật nền **không tự chọn lại**; chỉ
  bỏ khỏi bảng các hồ sơ đã xác minh **Lưu thành công** trên portal.
- `Lọc số lỗi` giữ cơ chế chọn-tạm-thời và `Hoàn tác lọc` của Qt; không đổi
  thành tìm kiếm tự do, không xóa vĩnh viễn dòng khác.
- Dòng đã chọn xếp lên đầu; mọi thao tác dùng **`record_id` thật** — không
  dùng số thứ tự hiển thị (STT) làm định danh.
- Quét nguồn mới tạo ngữ cảnh lượt quét mới (`run_id` mới) và bỏ các ID đã
  chọn của lượt cũ; kết quả của job cũ đến muộn không ghi đè lượt đang xem.

#### Quy tắc đợt chuẩn bị (dry-run, người dùng tự Lưu)

- Mỗi đợt mở tối đa **N** tab (`Số tab mỗi đợt`). Đợt sau chỉ bắt đầu khi
  người dùng bấm `Tiếp tục N số tiếp theo`; app **không tự mở đợt kế tiếp**.
- App chỉ điền sẵn biểu mẫu rồi dừng trước nút Lưu; người dùng kiểm tra trực
  quan và tự bấm Lưu trong Chromium. Không có nút "Finalize" trong app.
- `Dừng` kết thúc sau đơn vị đang xử lý theo khả năng engine; trạng thái "đã
  yêu cầu dừng" không đồng nghĩa browser đã ngừng ngay.
- `Đã điền sẵn`, `Đang chờ kiểm tra`, `Đã lưu trên web`, `Lỗi` là các trạng
  thái **khác nhau** trên dòng/trạng thái job. Nút "Xong kiểm tra"
  (`finish_review`) chỉ kết thúc bước chờ — không phải bằng chứng đã Lưu.
- Hồ sơ có thể đã Lưu nhưng chưa xác minh được phải vào nhóm **Cần đối
  chiếu**, hiển thị ngay trong bảng/thanh trạng thái; không được gửi lại cho
  tới khi đối chiếu xong (sổ mới hoặc xác nhận người dùng).

### 2.4. Dropdown website dùng chung

- Hiện chỉ có một mục hoạt động: **`nam_dinh` — "Nam Định"**, địa chỉ
  `https://congchungnamdinh.ninhbinh.gov.vn` (lấy từ code hiện tại). Nhãn và
  tên miền có thể đổi sau; `website_id` không đổi.
- Danh sách website và thao tác đã hỗ trợ do **backend cung cấp**; frontend
  không chứa danh sách URL hay nhánh nghiệp vụ theo tỉnh, không ô nhập URL.
- Website được chọn quyết định bộ xử lý đăng nhập, tải file, đọc cấu trúc sổ
  và điền biểu mẫu; cùng một lựa chọn áp cho cả hai tab.
- Chỉ cho đổi website khi không có tác vụ/đợt chuẩn bị đang hoạt động hoặc
  tab đang chờ kiểm tra — backend kiểm lại điều kiện, không chỉ khóa
  dropdown ở UI. Đổi website hiển thị trạng thái của website mới; không giữ
  sổ/ô chọn của website cũ dưới tên mới.
- `website_id` không đăng ký bị từ chối (`unknown_website`); không quay về
  Nam Định ngầm. Website thứ hai chỉ được bật khi có bộ xử lý và mẫu file
  thật; không cần thay cấu trúc hai tab.

### 2.5. Quy tắc hiển thị chung

- **Ngôn ngữ**: toàn bộ nhãn/nút/thông báo là tiếng Việt **có dấu** (chuẩn
  Việt hóa trước đây vẫn giữ: `Từ ngày`, `Đến ngày`, `Số còn thiếu`,
  `Số lỗi, trùng`, `hợp lệ`, `thiếu`, `lỗi`, `trùng`...).
- **Ngày**: trên dây truyền/backend dùng ISO `YYYY-MM-DD`; UI hiển thị
  `DD/MM/YYYY`; bộ xử lý website chuyển sang định dạng portal. Giá trị không
  có là `null` → hiển thị trống/"—", không hiển thị `null` hay `""`.
- **Trạng thái chờ người** (`waiting_user`): banner trong module nêu rõ việc
  cần làm ("Đăng nhập trên cửa sổ Chromium", "Kiểm tra các tab đã điền");
  không phải lỗi. Chromium do Python quản lý chỉ được đưa lên trước **một
  lần có chủ đích**, không giật focus lặp lại.
- **Lỗi**: hiển thị inline tại vùng liên quan theo shape lỗi của contract
  (code + message + retryable + next_action); nút Thử lại chỉ khi
  `retryable: true`. **Không in JSON, tên command, hay stack trace** cho
  người dùng.
- **Không tự hoàn thành bước của người**: không auto-Save, không tự xác nhận
  đăng nhập/review, không tự điền lựa chọn còn trống.
- **Hủy**: có ở trạng thái đang chạy/chờ; hủy không hoàn tác một lần Lưu đã
  xảy ra và không tự đóng các tab người dùng đang kiểm tra.

<a id="portal"></a>
## 3. Đăng nhập và tín hiệu Lưu

Một Chromium dùng chung để đăng nhập, tải sổ và điền form. Không lưu username/password; storage state cục bộ phải được bảo vệ vì có token. Với website hiện hành, nhận diện đăng nhập qua access_token và đã rời trang đăng nhập; nút xác nhận chỉ kiểm ngay trạng thái thực.

### 3.1. Kiểm tra môi trường khi đăng nhập lần đầu

- Trước lần mở đăng nhập đầu tiên, app cần có nút **Kiểm tra môi trường và mở đăng nhập**. Bộ kiểm tra chạy nền, không được làm app tự thoát khi lỗi.
- Phải kiểm tra: quyền ghi thư mục app, dung lượng đĩa, thư viện Playwright, Chromium đi kèm, mạng/DNS, HTTPS đến trang đăng nhập và việc Chromium thật mở được URL.
- Chrome cài sẵn không phải điều kiện bắt buộc vì app dùng Chromium của Playwright. Chỉ ghi nhận phiên bản Chrome/Edge để chẩn đoán hoặc khi người dùng chủ động chọn dùng chúng.
- Windows 10 cần được ghi là **tương thích có kiểm tra**: Playwright hiện hỗ trợ chính thức Windows 11+; không tự nâng cấp Playwright/Chromium trên máy Windows 10.
- Kết quả phải chỉ rõ bước nào lỗi, có nút Thử lại/Sao chép chẩn đoán, và chỉ lưu log đã bỏ token, cookie, mật khẩu và URL có query.

Các bước lỗi phải nêu nguyên nhân và cách thử lại; không bắt người dùng mở tài liệu lịch sử để hiểu thông báo.

### 3.2. Quy tắc kỹ thuật quan trọng

- URL mặc định là `https://congchungnamdinh.ninhbinh.gov.vn`.
- Route đăng nhập và tạo nhanh được tự suy ra từ địa chỉ web. Có thể đặt `ND_LOGIN_URL` hoặc `ND_CREATE_URL` trong `.env` nếu web đổi route.
- Token đăng nhập nằm trong local storage, không phải cookie. Playwright lưu lại storage state sau khi phát hiện đăng nhập thành công.
- Phải phân biệt hai luồng, đối chiếu source ngày 15/10/2026: workflow v1
  chỉ đánh dấu đã Lưu khi tab nhận `POST /api/hoso` trả HTTP 2xx; chỉ rời trang
  tạo mới thì chuyển sang cần đối chiếu (`needs_reconcile`). Luồng legacy
  không truyền `workflow_version` còn nhận cả dấu hiệu rời trang. Không áp
  fallback của legacy cho v1; [contract workflow](../../../contracts/upload-workflow.md)
  vẫn Draft, việc mô tả code ở đây không nâng trạng thái duyệt của contract.
- Mỗi tab gắn một `record_id`. Với v1, đóng tab/browser trước khi có kết quả
  đã xác minh phải đối chiếu lại; không tự mở lại hoặc gửi lại hồ sơ chưa rõ.
  Luồng legacy cũ có thể cho chuẩn bị lại khi tab đóng.
- Engine dùng sự kiện phản hồi trên tab do app mở, rồi kiểm tra khoảng 0,5
  giây khi rảnh; thao tác đang chạy có thể làm chậm vòng kiểm tra. Không có
  thời hạn tự coi hồ sơ chưa bấm Lưu là đã Lưu. Máy ngủ không được kiểm tra;
  sau gián đoạn cần đối chiếu các hồ sơ chưa rõ, không bảo đảm giữ nội dung
  form chưa Lưu qua lần đóng browser hoặc khởi động lại app.
- Giới hạn hiện tại: code kiểm phương thức/path/mã HTTP, chưa kiểm nội dung
  phản hồi, hostname hoặc tính đầy đủ của từng trường. Chưa có bằng chứng cổng
  thật luôn dùng HTTP lỗi cho lỗi nghiệp vụ. Một lần POST 2xx được tính cho cả
  hồ sơ; engine không xác minh từng trường đã lưu đủ hay chỉ lưu một phần.
- Đã tái hiện bằng mô phỏng: nhận phản hồi Lưu rồi đóng tab trước vòng kiểm
  tra tiếp theo có thể vẫn bị ghi là `closed`/cần đối chiếu, vì code kiểm tab
  đóng trước cờ phản hồi. Nếu mất phản hồi mà vẫn ở trang tạo mới, tab có thể
  tiếp tục chờ vô thời hạn. Cần kiểm cổng thật và các tình huống gián đoạn
  trước khi kết luận tín hiệu này đủ tin cậy; chưa sửa engine trong phiên docs.
- Log mạng chỉ ghi phương thức, URL không có query string và mã trạng thái; không ghi token, cookie hay nội dung request.

### 3.3. Không làm trong phạm vi này

- Không nhúng Chrome vào giao diện app.
- Không gửi hồ sơ bằng REST API thay cho Playwright.
- Không tự bấm nút Lưu thay người dùng.
- Không tự mở ngay đợt kế tiếp sau khi phát hiện Lưu.

## 4. Lỗi, dữ liệu và khôi phục

Engine Python sở hữu quét, audit, browser và registry; Electron không chứa parser/Playwright. Lỗi đọc một file ghi theo record, không làm mất record khác. File đang mở, đường dẫn dài/Unicode hoặc thiếu quyền phải có lỗi rõ. Không để luồng legacy và Electron cùng chiếm browser hoặc ghi registry; quay lui phải giữ dữ liệu cả hai để đối chiếu.

IFilter khi Word đang mở và sự kiện ổ mạng phải được đo trên máy thật khi ảnh hưởng luồng. Website mới chỉ bật khi có bộ xử lý/selectors và mẫu file thật. Bằng chứng POC giả lập không là nghiệm thu cổng thật.

## 5. Kiểm chứng và việc còn mở

- Quét chưa có Excel vẫn xem được nhưng không tự gọi hồ sơ là thiếu trên web. Đổi nguồn/website phải bỏ kết quả không còn đúng ngữ cảnh.
- Đã điền, đang chờ người, đã lưu và cần đối chiếu là các trạng thái riêng. Không gửi lại hồ sơ chưa rõ kết quả; không tự mở đợt sau.
- Đối chiếu phải kiểm nguồn thật, dữ liệu từng trường và số bản ghi. Ít cảnh báo hoặc test xanh không chứng minh đọc đúng.
- Owner coi module tương đối hoàn thiện; chưa có bằng chứng trong đợt docs này để kết luận chỉ còn regex/website mới. Tín hiệu Lưu và gián đoạn vẫn cần kiểm cổng thật.
- Chi tiết màu/kích thước riêng của Upload trong bản cũ còn Proposed; không nâng thành đã duyệt. Bộ token giao diện chung giữ hiệu lực.

## 6. Tra cứu

Quy tắc bóc trường và cách kiểm tập trung tại [bóc tách](../shared/extraction-rules.md). Code tại `upload_lab/`, giao diện `shell/src/renderer/upload/`; contract giao tiếp `contracts/upload-workflow.md` còn Draft theo trạng thái của nó, không được nâng duyệt bởi lần gom này.
