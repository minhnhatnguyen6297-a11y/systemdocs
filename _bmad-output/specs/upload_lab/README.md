# Upload — đối chiếu kho Word và điền website

**Cập nhật:** 15/10/2026. Spec hành vi module; giữ phân biệt hướng được owner chốt, đề xuất thị giác và giới hạn code đã quan sát.

## 1. Mục đích và luồng

Đọc Word cũ vì phần mềm văn phòng chưa có API lấy dữ liệu. Không tự đổi sang API/DB nguồn khác khi chưa chốt. Luồng: chọn website/đăng nhập → nạp hoặc tải sổ Excel làm ảnh chụp theo website/khoảng ngày → quét Word → đối chiếu/chọn hồ sơ → bóc trường → điền form → người dùng tự kiểm tra và Lưu. Dữ liệu đã được website ghi nhận chính thức là nguồn sự thật (SOT); app không kết luận kết quả Lưu từ tín hiệu browser.

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
- Bỏ trang Nhật ký không làm mất kết quả/lỗi của scan, audit và job: hiển thị
  inline tại vùng liên quan. Tiến độ job/workspace có thể được giữ để tiếp
  tục công việc; không dùng làm bằng chứng hay phục hồi kết quả Lưu.

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

#### Quy tắc chọn và phân lô

- **Chưa có Excel**: vẫn cho quét và xem hồ sơ; không tự chọn là "thiếu trên
  web".
- **Có Excel cùng website**: chọn mặc định các số hợp lệ chưa có trong ảnh
  chụp sổ đang nạp; giữ ghi chú cho số sai format, sai năm, thiếu trường,
  trùng trong folder. Ảnh chụp là dữ liệu chính thức từ website theo website,
  năm/khoảng ngày và thời điểm tải/nạp; không dùng phản hồi của lần điền form
  làm dữ liệu đã upload.
- Người dùng bỏ chọn thủ công → poll/cập nhật nền **không tự chọn lại**.
- Trong một lượt quét, app chỉ nhớ tiến độ hồ sơ đã chuẩn bị và quyền sở hữu
  tài nguyên để phân lô; trạng thái này không chứng minh website đã Lưu và
  không tạo danh sách chặn vĩnh viễn.
- Người dùng bấm `Tiếp tục N số tiếp theo` để chuyển qua các hồ sơ đã chọn
  nhưng chưa chuẩn bị trong lượt hiện tại. Hồ sơ đã chuẩn bị không tự đi vào
  lô sau chỉ vì chưa được Lưu; app không tự mở lô, retry hoặc đưa hồ sơ chưa
  Lưu vào queue.
- Quét lại/chọn lại thủ công dùng phép đối chiếu bình thường với ảnh chụp
  chính thức đang nạp. Tải/nạp Excel vẫn là thao tác hiện có; không thêm fetch
  tự động hay bước đối chiếu bắt buộc sau khi điền.
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
- Dòng và job thể hiện tiến độ chuẩn bị/chờ người/lỗi; app không gán trạng
  thái Lưu suy từ browser hoặc cộng dồn số đếm Lưu suy từ browser. Phân loại
  hiện diện trong sổ chính thức vẫn được giữ.
- Người dùng có thể chủ ý không Lưu vì form lỗi, trùng hoặc lý do nghiệp vụ.
  Tình trạng không rõ Lưu không tự sinh cảnh báo, khóa UI, thao tác giải
  phóng, retry hoặc lô chuẩn bị lại. Người dùng tự quyết định thao tác tiếp
  theo theo dữ liệu chính thức của website.

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
- Bộ xử lý/rule upload theo từng website thuộc phạm vi developer, có phân biệt
  phiên bản để nhận biết (owner 16/10/2026 —
  [decision](../../decisions/decision-owner-regex-rule-developer-only-20261016.md));
  người dùng sản phẩm không có chức năng thử, công bố, chọn phiên bản hoặc
  quay lui rule.

### 2.5. Quy tắc hiển thị chung

- **Ngôn ngữ**: toàn bộ nhãn/nút/thông báo là tiếng Việt **có dấu** (chuẩn
  Việt hóa trước đây vẫn giữ: `Từ ngày`, `Đến ngày`, `Số còn thiếu`,
  `Số lỗi, trùng`, `hợp lệ`, `thiếu`, `lỗi`, `trùng`...).
- **Ngày**: trên dây truyền/backend dùng ISO `YYYY-MM-DD`; UI hiển thị
  `DD/MM/YYYY`; bộ xử lý website chuyển sang định dạng portal. Giá trị không
  có là `null` → hiển thị trống/"—", không hiển thị `null` hay `""`.
- **Trạng thái chờ người** (`waiting_user`): banner nêu rõ việc cần làm
  ("Đăng nhập trên cửa sổ Chromium", "Kiểm tra các tab đã điền"); đây là bước
  thao tác của người, không phải trạng thái Lưu. Chromium do Python quản lý
  chỉ được đưa lên trước **một lần có chủ đích**, không giật focus lặp lại.
- **Tài nguyên browser**: trạng thái mở/đóng tab và phiên chỉ mô tả tài nguyên
  đang được app quản lý; không suy ra trạng thái đã Lưu trên website.
- **Lỗi**: hiển thị inline tại vùng liên quan theo shape lỗi của contract
  (code + message + retryable + next_action); nút Thử lại chỉ khi
  `retryable: true`. Đây là xử lý lỗi job thông thường, không tự retry hay
  xếp lại hồ sơ chỉ vì người dùng chưa Lưu. **Không in JSON, tên command, hay
  stack trace** cho người dùng.
- **Không tự hoàn thành bước của người**: không auto-Save, không tự xác nhận
  đăng nhập/review, không tự điền lựa chọn còn trống.
- **Hủy**: có ở trạng thái đang chạy/chờ; hủy không tự đóng các tab người
  dùng đang kiểm tra. Hủy job không phải bằng chứng về kết quả lưu trên web.

<a id="portal"></a>
## 3. Đăng nhập và thao tác Lưu

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
- **Quy tắc owner:** app chỉ điền sẵn biểu mẫu rồi dừng trước nút Lưu; người
  dùng tự kiểm tra và quyết định có bấm Lưu hay không. Người dùng có thể chủ ý
  không Lưu do form lỗi, trùng hoặc lý do nghiệp vụ và chấp nhận rủi ro sự cố.
- Dữ liệu đã được website ghi nhận chính thức là SOT. Tải Excel từ website
  hoặc nạp Excel hiện có chỉ cung cấp ảnh chụp theo website, năm/khoảng ngày
  và thời điểm nạp. Không biến phản hồi POST, route/điều hướng, đóng tab,
  `finish_review` hoặc sự kiện cục bộ thành `uploaded_success` hay sự thật
  rằng hồ sơ đã Lưu.
- Không tích lũy trạng thái/số đếm Lưu suy từ browser, `needs_reconcile`,
  khóa UI vì chưa rõ kết quả Lưu hoặc thao tác giải phóng tương ứng. Phân loại
  có/thiếu trong sổ dựa trên dữ liệu website vẫn được dùng. Không tự retry/
  phục hồi Lưu hoặc đưa hồ sơ chưa Lưu vào đợt sau; không tự mở đợt tiếp theo.
- Trong lượt hiện tại, app chỉ nhớ tiến độ hồ sơ đã chuẩn bị và quyền sở hữu
  tài nguyên để chia đợt; điều đó không chứng minh website đã Lưu và không
  tạo blacklist vĩnh viễn. `Tiếp tục` do người dùng bấm, qua các hồ sơ đã
  chọn nhưng chưa chuẩn bị.
- Quét/chọn lại thủ công dùng đối chiếu thông thường với ảnh chụp sổ chính
  thức đang nạp. Tải/nạp Excel giữ nguyên là thao tác do người dùng khởi
  tạo; không có fetch tự động hoặc bước đối chiếu bắt buộc để phục hồi kết
  quả Lưu.
- **Hiện trạng runtime (đã cutover 15/10/2026):** engine/sidecar/store/UI
  không còn suy kết quả Lưu và không còn đọc/ghi/tạo mới trạng thái đối
  chiếu (`upload.reconcile` đã gỡ); dữ liệu di sản (bảng/cột cũ nếu có
  trong DB) giữ nguyên, không xóa. Tiến độ chuẩn bị theo lượt quét được
  giữ theo trạng thái registry trong `run_id`. Xem ticket
  [#28](../../backlog/story-upload-web-official-sot-cutover.md).
- Contract [workflow](../../../contracts/upload-workflow.md) vẫn Draft; spec
  này không nâng trạng thái duyệt của contract.

### 3.3. Không làm trong phạm vi này

- Không nhúng Chrome vào giao diện app.
- Không gửi hồ sơ bằng REST API thay cho Playwright.
- Không tự bấm nút Lưu thay người dùng.
- Không tự mở đợt kế tiếp.

## 4. Lỗi, dữ liệu và khôi phục

Engine Python sở hữu quét, audit, browser và registry; Electron không chứa parser/Playwright. Lỗi đọc một file ghi theo record, không làm mất record khác. File đang mở, đường dẫn dài/Unicode hoặc thiếu quyền phải có lỗi rõ. Không để luồng legacy và Electron cùng chiếm browser hoặc ghi registry; khi chuyển đổi phiên bản giữ dữ liệu mỗi bên để đối soát kho.

IFilter khi Word đang mở và sự kiện ổ mạng phải được đo trên máy thật khi ảnh hưởng luồng. Website mới chỉ bật khi có bộ xử lý/selectors và mẫu file thật. Bằng chứng POC giả lập không là nghiệm thu cổng thật. Trạng thái job/workspace có thể được lưu để tiếp tục công việc; dữ liệu này không phải bằng chứng Lưu hoặc cơ chế phục hồi kết quả POST.

## 5. Kiểm chứng và việc còn mở

- Đã điền, đang chờ người và lỗi là trạng thái của việc chuẩn bị/chờ thao tác;
  không có trạng thái Lưu suy từ browser hay đối chiếu kết quả Lưu. Phân loại
  hiện diện trong sổ chính thức vẫn được dùng.
- Dữ liệu chính thức từ website là SOT; ảnh chụp Excel cần đúng website,
  năm/khoảng ngày và thời điểm nạp. Đối chiếu đầu vào không suy từ phản hồi
  cục bộ.
- Owner đã chốt bỏ theo dõi kết quả Lưu suy từ browser và chấp nhận rủi ro
  người dùng có thể không Lưu. Runtime đã cutover theo quy tắc này
  (15/10/2026); không yêu cầu xác minh kết quả lưu trên portal.
- Chi tiết màu/kích thước riêng của Upload trong bản cũ còn Proposed; không nâng thành đã duyệt. Bộ token giao diện chung giữ hiệu lực.

## 6. Tra cứu

Quy tắc bóc trường và cách kiểm tập trung tại [bóc tách](../shared/extraction-rules.md). Code tại `upload_lab/`, giao diện `shell/src/renderer/upload/`; contract giao tiếp `contracts/upload-workflow.md` còn Draft theo trạng thái của nó, không được nâng duyệt bởi lần gom này.
