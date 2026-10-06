# Tra cứu địa chỉ trong hồ sơ — NAIA-9, TASK-2, TASK-3, TASK-4

**Trạng thái:** luật tra và bố cục được Owner chốt 05/10/2026;
**TASK-3/TASK-4 đã nghiệm thu ngày 06/10/2026**.
Đã sửa P1–P12 và lỗi Word tìm thêm trong review; kiểm Electron thật
1280×800 + 1366×768: một dialog, đúng Tra/Copy/nguồn, giữ nháp/focus/vùng chọn/cuộn,
không mở lại Word đã đóng. Word nối producer frozen với kho public,
full 3.001 dòng và clipboard hệ điều hành đạt.
Python 294 đạt/2 bỏ qua symlink; renderer 90 đạt; npm 403 đạt; examples 82/0.
Các test đã thử bỏ sửa trong bộ nhớ và bắt đúng lỗi cũ.
[Kết quả nghiệm thu và giới hạn](../../../_bmad-output/archive/removed-agents-files.md);
[review trước sửa](../../../_bmad-output/archive/removed-agents-files.md) giữ làm lịch sử.
[Báo cáo worker](../../../_bmad-output/archive/removed-agents-files.md)
và [audit gốc](../../../_bmad-output/archive/removed-agents-files.md) giữ làm lịch sử.
**Nguồn quyết định:** Owner
03–04/10/2026 tại [NAIA-9](../../../_bmad-output/archive/linear-tasks/NAIA-9-decisions.md); thay một
phần bởi Owner 05/10/2026 tại TASK-2.

Luật tra (đầu vào, khớp, kết quả, đúng/sai) nằm tại
[lõi tra cứu dùng chung](../shared/administrative-lookup.md). Trang này chỉ ghi
**cách `notary_v2` gọi lõi**; không lặp lại luật.

## Công dụng và Tại sao?

Giúp chuyên viên đổi địa chỉ trên giấy tờ cũ sang tên xã/tỉnh hiện hành khi lập
hồ sơ. Máy chỉ trả kết quả để copy; người dùng tự quyết ghi gì vào ô.

## Nơi gọi

| Ô | Chuỗi được tra |
|---|---|
| Địa chỉ Người | Nội dung ô địa chỉ của người đó |
| Địa chỉ Tài sản | Nội dung ô địa chỉ của tài sản đó |
| Nơi niêm yết | Nội dung chính ô Nơi niêm yết; không bắt chọn tài sản nguồn |
| Nơi cấp giấy khai tử | Địa chỉ của chính người đã chết; kết quả là xã mới để người dùng ghi nơi cấp |

Mọi ô dùng kiểu trình bày `drafting` (`xã Ý Yên, tỉnh Ninh Bình`), nút Tra bên
phải ô, kết quả bên dưới ô và copy được. Quá 10 kết quả → popup "Nhiều kết quả khớp. Xem đầy
đủ?", bấm đồng ý mới mở tool tra cứu dạng popup đè lên hồ sơ; đóng popup về
đúng chỗ cũ, không mất nháp đang nhập. Không cần ngày cấp giấy hay
`ngay_lap_ho_so`. *Tại sao:* lõi chỉ trả bước cuối (Owner 05/10).

## Quy tắc riêng của hồ sơ

- Máy không ghi, đè hay nối `(nay là …)` vào ô hoặc Stage. Người dùng dán/sửa
  tay rồi lưu như mọi chỉnh sửa khác; lưu metadata dùng revision hiện hành,
  xung đột không ghi đè cưỡng bức.
- Không tự sửa thôn, số nhà hoặc chi tiết ranh giới.
- Nơi cấp giấy khai tử: tra xã mới từ địa chỉ của người đó, không phụ thuộc
  ngày (Owner 05/10/2026). Máy vẫn không tự ghi; người dùng copy và sửa nếu
  giấy ghi khác. Quy tắc nơi cấp giấy tờ người sống theo MIN-141 vẫn độc lập.
- Không gửi địa chỉ khách hàng ra website; chỉ đọc kho cục bộ.

## Bản cài

Bản cài cần helper, schema và đúng ledger/snapshots công khai. Không đóng gói
database văn phòng, cấu hình riêng, khóa ghi hoặc archive lịch sử của người
quản lý. Nâng cấp định dạng kho theo migration của
[spec timeline](./administrative-timeline.md).

## Luồng giao diện của TASK-4

### Chuỗi tra và nội dung đang nhập

- Khi bấm Tra, lấy đúng chữ đang hiện trong ô nguồn, kể cả phần chưa lưu;
  không lấy lại giá trị cũ từ Stage. Nơi cấp giấy khai tử dùng ô địa chỉ của
  chính người chết như bảng Nơi gọi; không dùng chữ đang nhập trong ô nơi cấp.
- Gửi `{query, presentation: "drafting"}`. Không gửi ngày, tỉnh/xã tách sẵn,
  `case_id` hay `base_revision`. Tra cứu không phải thao tác lưu hồ sơ.
- Gắn mỗi lần tra với hồ sơ, người/tài sản, ô đích và chuỗi nguồn lúc bấm.
  Đổi một trong các giá trị đó khi đang chờ thì bỏ phản hồi cũ. Lần tra sau
  không được bị kết quả của lần tra trước ghi đè. Đặc biệt, đổi địa chỉ người
  chết làm kết quả nơi cấp khai tử đang chờ hết hiệu lực.
  Đổi từ A sang B rồi quay lại A cũng không làm phản hồi cũ của A hợp lệ lại.
- Người dùng được tra lại cùng chuỗi bằng nút Tra; không giữ luật chặn chuỗi
  không đổi của giao diện cũ (spec lõi mục 11).

### Phản hồi và cửa sổ tra cứu

| Phản hồi | Hành vi |
|---|---|
| Đang tra | Báo đang tra tại vùng thao tác; không tự ghi vào ô |
| `found` | Hiện đủ `results[].display`; người dùng copy rồi tự dán/sửa |
| `not_found` | Báo không tìm thấy; không suy đoán hoặc hiện kết quả cũ |
| `invalid_input` | Báo đầu vào không hợp lệ; cho người dùng sửa rồi bấm Tra |
| `reload_failed` | Báo không đọc được kho cục bộ; không thay bằng kết quả từ bản kho cũ |
| `too_many` | Không hiện dòng nào; hỏi đúng câu “Nhiều kết quả khớp. Xem đầy đủ?” |
| Lỗi gửi lệnh/nhận phản hồi | Báo lỗi tại vùng tra; giữ nguyên nháp, cho bấm Tra lại |

Đồng ý câu hỏi `too_many` mới gửi lại **đúng chuỗi đã tra** với
`presentation: "full"`; không lấy một chuỗi khác vừa sửa trong ô. Nếu hồ sơ,
ô hoặc chuỗi nguồn đã đổi, bỏ yêu cầu cũ, người dùng bấm Tra lại. Hủy câu hỏi
không gọi `full` và trở lại chỗ soạn thảo.

Cửa sổ full hiện toàn bộ kết quả, gồm cả xã và tỉnh theo đúng thứ tự lõi trả;
không cắt còn 10 dòng, không tự lọc tỉnh khỏi kết quả nơi cấp khai tử. Người
dùng chọn dòng phù hợp để copy. Giữ riêng các dòng nguồn khớp, kể cả cùng
`unit_id` hoặc `display`; không chọn/gộp hay báo lỗi vì có nhiều dòng.

**Bố cục đã chốt:** ô tìm kiếm sửa được và nút Tra ở trên; danh sách cuộn ở
dưới, mỗi dòng có Copy; có nút Đóng. Mở lần đầu sau xác nhận dùng đúng query
vừa tra. Sửa query trong cửa sổ không sửa ô hồ sơ và không tự tra; bấm Tra
mới gửi query mới với `presentation: "full"`. Mỗi dòng full hiện nguyên đoạn
nguồn tương ứng để người dùng phân biệt và chọn. *Tại sao:* thao tác ngay
bên ô đang sửa; tra thêm trong cửa sổ mà vẫn giữ nguyên nháp hồ sơ (Owner 05/10).

### Giữ nháp và vị trí đang sửa

- Cửa sổ full phủ lên màn hình hồ sơ đang mở; không điều hướng sang module
  khác, không nạp lại hồ sơ, không gọi lưu hoặc reset form khi mở/đóng/copy.
- Ghi nhớ ô đang sửa và vị trí con trỏ/vùng chữ được chọn trước khi nút Tra
  lấy focus. Giữ nguyên chữ đang nhập, nháp chưa lưu và vị trí cuộn.
- Chỉ một hộp thoại của luồng tra cứu tại một thời điểm: đóng câu hỏi trước
  khi mở cửa sổ full. Giữ thao tác bàn phím trong hộp thoại; Esc, nút × hoặc
  Đóng đều đóng và trả về vị trí đang sửa. Áp dụng
  [quy tắc dialog chung](../ui/README.md), với yêu cầu riêng của tính năng
  này là khôi phục con trỏ trong ô đang sửa trước khi bấm Tra, thay vì chỉ
  focus nút mở. Ô lấy chuỗi để tra và ô trả focus có thể khác nhau: Tra nơi
  cấp khai tử đọc địa chỉ người chết nhưng không ép focus sang ô địa chỉ đó.
- Copy không tự đóng cửa sổ, không sửa dữ liệu hồ sơ. Copy lỗi phải báo rõ;
  không báo đã copy khi thao tác clipboard thất bại.

## Phân chia TASK-3 và TASK-4

Owner 05/10/2026 yêu cầu hoàn thiện spec và lập plan hai task song song.
Phần triển khai giao diện vẫn phụ thuộc lõi v2, vì hai task dùng chung
`case-drafting-model.js` và `case-drafting-view.js`.

- TASK-3: chuyển lõi/contract sang v2, bỏ đường tự tra và hành vi nối
  `(nay là …)`; phần tra cứu trong renderer tạm ngủ đông theo quyết định đã
  ghi trong TASK-3. Chưa có nút Tra/popup không được mô tả là hoàn tất TASK-4.
- TASK-4: nhận lại model/view đã chuyển v2, thêm thao tác Tra, kết quả copy
  và cửa sổ full. Không viết lại luật khớp trong renderer.
- Backlog giữ kế hoạch thực hiện và trạng thái task; `docs/spec` giữ hành vi.
  Plan không được tự thêm quy tắc tìm kiếm hoặc chọn/gộp kết quả thay người dùng.

## Còn mở

Không còn mục sửa đã xác nhận hoặc lựa chọn bố cục chờ Owner trong TASK-4.
Helper/schema/kho và producer frozen đã chạy ở thư mục riêng; không tạo
bản cài Electron toàn bộ hoặc phát hành trong lần sửa này.
Giữ riêng các nhánh D1/D2 chỉ tái hiện khi gọi API model, chưa chứng minh
đường thao tác người dùng khi full chặn nền; không thêm luật vì các nhánh này.
Xem [ghi riêng](../../../_bmad-output/archive/removed-agents-files.md).
*Tại sao:* nghiệm thu theo hành vi người dùng đã chốt và bằng chứng chạy thật,
phân biệt lỗi đã xác nhận với tình huống chưa đạt được trên UI; không đổi luật Owner.

## Lịch sử

Owner 05/10/2026 bỏ: bắt ngày giấy/ngày lập hồ sơ, bắt xã+tỉnh, nút áp dụng nối
`(nay là …)`, nơi niêm yết lấy địa chỉ tài sản được chọn, nơi cấp giấy khai tử
tra theo ngày cấp giấy và "địa chỉ cư trú không chứng minh nơi cấp". Hiện trạng code còn
theo các quy tắc cũ; xem mục 12 của
[lõi tra cứu](../shared/administrative-lookup.md).
