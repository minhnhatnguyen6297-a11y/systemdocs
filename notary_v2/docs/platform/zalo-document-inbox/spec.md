# Zalo Intake v2 — module Zalo bàn giao raw OCR cho Document Intake

**Spec chính hiện hành — ranh giới xử lý, gói file và quyền OCR lại có giới hạn đã chốt; API/chi tiết kỹ thuật còn DRAFT, chưa triển khai runtime.**
Ngày: 24/09/2026 · Owner: platform/document-intake · Spec: MIN-89 · Goal triển khai: MIN-91

**Nguồn chuẩn cho hành vi và nghiệm thu v2.** Đọc [trang chỉ đường](README.md) để biết thứ tự ưu tiên. [Thiết kế tổng thể](../../../../docs/product/specs/2026-09-24-zalo-independent-intake.md) giải thích ranh giới; [quy cách trao đổi nháp](../../../../docs/product/specs/zalo-file-exchange-v1-draft.md) là đầu vào của MIN-92, chưa được dùng như contract đã duyệt. [Kiểm kê hiện trạng](v2-current-state-audit.md) và spec v1 chỉ đối chiếu code cũ.

## 1. Phạm vi giai đoạn đầu

Module Zalo được tách thành **repo local độc lập trước** (đề xuất `D:/zalo-intake`), chưa deploy Windows server. Module nhận sự kiện, giữ ảnh tạm, gọi Qwen OCR và làm các bước xử lý cần byte ảnh như xoay/cắt để OCR lại. Nó bàn giao **raw OCR, trạng thái và dấu vết nguồn trong gói file/folder** có version, không bàn giao person/property/group đã bóc. **Document Intake của hệ thống công chứng chạy sau Sync** để phân loại, regex, bóc trường, ghép mặt giấy tờ/người/tài sản và gợi ý nhóm. Khi parser chỉ ra vùng chữ thiếu/chưa rõ, máy chính được yêu cầu bot thử một biến thể OCR **có loại định sẵn** cho ảnh còn hạn bằng ID ổn định, không chuyển ảnh. Người dùng duyệt trước khi đưa dữ liệu vào input soạn hồ sơ. Sau nghiệm thu local/dữ liệu thật mới tính chuyển bot sang server. [Plan giao agents MIN-91](../../../../docs/product/plans/2026-09-24-zalo-independent-implementation-plan.md).

Bộ thu thập Zalo có vòng đời riêng, kể cả khi app công chứng tắt; giai đoạn triển khai server sau phải chạy khi máy công chứng tắt. “Server” trong spec chỉ vai trò module thu/OCR độc lập, ở bước đầu vẫn chạy thử trong repo local riêng. Giai đoạn đầu giả định bot bắt đúng toàn bộ tin/ảnh trong phạm vi nguồn đã bật, để tập trung vào luồng chuẩn: nhận tin và ảnh, gọi Qwen API đọc chữ, bàn giao raw/status/nguồn, sau đó Document Intake xử lý và người dùng duyệt. Đây là giả định thiết kế; chưa tuyên bố đã kiểm chứng toàn bộ tin đã gửi trên Zalo.

Máy công chứng tự lấy gói raw đã sẵn có từ module, lưu chữ OCR/trạng thái/thông tin nguồn bền vững, rồi chạy Document Intake tạo thẻ ứng viên và áp dụng dữ liệu đã được người dùng duyệt vào hồ sơ. **Không chuyển ảnh, thumbnail, base64, URL tải ảnh hay đường dẫn ảnh trong gói.** Máy công chứng không tải, lưu hoặc cho xem trước ảnh. Khi cần so với bản gốc, người dùng tự mở Zalo thật. Ứng dụng Zalo desktop riêng không thuộc phạm vi thiết kế.

Lấy bù và đối chiếu các sự kiện bot chưa từng nhận là **OPEN [MIN-90](https://linear.app/minhnotary/issue/MIN-90/research-zalo-fallback-khi-bot-bat-thieu-va-ocr-het-han-anh) của giai đoạn sau**. Nút “Sync” ở máy công chứng chỉ lấy gói raw đã có trên module; nó không yêu cầu Zalo trả lịch sử. Việc thử lại tải/OCR cho một sự kiện đã ghi nhận là xử lý lỗi trong luồng chuẩn, khác với tìm lại sự kiện chưa được bot ghi nhận.

Thời gian chính của mỗi dòng là captured_at: lúc bot bắt được tin/sự kiện lần đầu. Mốc này không đổi khi nhận lặp, OCR lại hoặc truyền lại. source_sent_at do Zalo cung cấp và imported_at lúc máy chính nhập là thông tin phụ. Danh sách, lọc và gợi ý nhóm dùng captured_at; nếu thiếu hoặc sai giờ nguồn, không tự thay captured_at bằng giờ nhập.

## 2. Module xử lý độc lập — local trước, server sau

> **Producer SOT đã chuyển tại MIN-103.** Phần chuẩn tắc phía producer
> (CAP-01..16: listener/single-account, phiên QR & session, source policy,
> journal + captured_at, media tải tạm và vòng đời 168h, sở hữu Qwen OCR,
> raw provenance, sản xuất gói bất biến, yêu cầu OCR lại có giới hạn) nay
> nằm ở repo module `D:\zalo-intake` → `docs/spec-producer.md` (snapshot một
> chiều: `zalo/docs/spec-producer.md` trong monorepo). Wire contract giữa
> module và máy chính do `contracts/zalo-intake/` quy định — bản vendored
> read-only ở `schemas/` của repo module. File này chỉ giữ phần consumer và
> luồng đồng bộ phía máy chính.

## 3. Đồng bộ gói dữ liệu từ máy chính

> Nội dung mục này nay do **`contracts/zalo-intake/`** chi phối ở mức wire
> (schema gói, feed pending, biên nhận, OCR request, mã lỗi — vendored tại
> `schemas/` của repo module). Phần dưới giữ vai trò mô tả ý định thiết kế;
> nếu lệch contract đã duyệt, contract thắng.

Máy công chứng chủ động lấy gói khi backend khởi động, khi kết nối trở lại, theo chu kỳ trong lúc chạy và khi người dùng bấm **Sync**. Bốn trigger dùng cùng một đường nhận; nút Sync chỉ tải gói đã công bố, không quét history Zalo, không tự phát lệnh OCR lại và không tải ảnh. Yêu cầu OCR lại là thao tác riêng do Document Intake phát sau khi phân tích raw.

Đã chọn **gói file/folder bất biến** (`manifest.json`, `records.jsonl`, `READY.json`) và máy chính chủ động tải. Chi tiết API/contract đề xuất dùng HTTPS có xác thực; thử local trên cùng máy cho phép HTTP có xác thực chỉ tại loopback (`127.0.0.1`); dùng mạng LAN hoặc server ngoài phải dùng HTTPS:

1. GET /intake/v1/packages?delivery=pending&after=<sequence>&limit=<n> liệt kê gói chưa ACK theo sequence tăng riêng. Mỗi lượt quét pending từ after=0, chốt until_sequence và phân trang theo quy cách trao đổi. Sequence chỉ đánh số gói đã công bố; không suy ra thứ tự hoặc tính liên tục của message ID Zalo.
2. Máy chính tải `manifest.json`, `records.jsonl` và `READY.json` của từng package vào thư mục staging cục bộ. Gói đề xuất mang schema `intake.raw-package.v1`; danh mục file và cách tải do quy cách trao đổi định nghĩa. Không có `results.json` hoặc endpoint tải ảnh.
3. Kiểm version, READY, hash, số bản ghi và identity nguồn. Chỉ công bố vào ready cục bộ sau khi đủ file; sau đó nhập **raw/status/nguồn và sổ nhập** bền vững.
4. POST /intake/v1/receipts gửi ACK kèm package ID và manifest hash **ngay sau commit raw**, không chờ parser hoặc người dùng duyệt. Mất ACK thì module đưa lại gói, máy chính trả cùng biên nhận đã nhập, không nhân đôi.

Cursor là vị trí phân trang trong lượt, **không phải ACK**. Chỉ chuyển trang sau khi danh sách ID/hash gói đã được ghi bền vững vào sổ nhập hoặc hàng chờ cục bộ. Gói chưa ACK trong sổ được thử lại theo ID sau crash, và lượt mới quét pending từ đầu để không bỏ gói cũ tải lỗi. Gói hỏng hoặc version chưa hỗ trợ được đánh dấu lỗi/giữ riêng, không biến thành đã nhập thành công và không chặn các gói độc lập khác. Module không xóa gói raw chờ ACK. Kênh truyền có xác thực kiểm tra danh tính hai bên; hash chỉ kiểm file hỏng, không chứng minh người gửi.

Thư mục cục bộ có staging, ready, `imported/` và khu gói lỗi theo [quy cách trao đổi nháp](../../../../docs/product/specs/zalo-file-exchange-v1-draft.md). Bản gói trong `imported/` dùng để đối chiếu file, hash và trạng thái khi có lỗi; thời hạn cụ thể và cách dọn thuộc chính sách máy chính do MIN-102 chốt, MIN-99 thực hiện. Máy chính không tạo thư mục ảnh nhập, không mở ảnh từ module và không dùng link ảnh làm bằng chứng lâu dài. Gói dữ liệu có thể chứa trạng thái ảnh/OCR chưa đủ; ACK kỹ thuật chỉ xác nhận raw/status/nguồn và sổ nhập đã được giữ, không có nghĩa parser đã xong hoặc người dùng đã duyệt nghiệp vụ.

### Yêu cầu OCR lại có giới hạn

Sau khi đã nhập và ACK gói raw, Document Intake có thể thấy một trường giấy chứng nhận đọc chưa rõ, ví dụ ngày cấp ở cuối trang. Nó chỉ gửi `logical_id` ổn định của ảnh/trang đã biết, raw revision đang xét, `request_id` chống lặp, loại biến thể trong danh sách cho phép (chẳng hạn xoay ảnh hoặc đọc lại vùng chân) và lý do. Không gửi file, bytes/base64, URL/path ảnh, tọa độ cắt tự do hoặc prompt Qwen tùy ý. Endpoint/tên trường và mức ngân sách cụ thể phải được MIN-92 duyệt; **quyền gửi yêu cầu có giới hạn là phạm vi đã chốt**.

Bot chỉ nhận yêu cầu từ consumer được xác thực, đối chiếu `logical_id` với ảnh/source thuộc quyền, kiểm revision consumer đã xem còn mới, ảnh vẫn tồn tại trước `image_expires_at=captured_at+168 giờ` và kiểm số lượt/chi phí cho ảnh và consumer. Cùng `request_id` với cùng nội dung trả cùng trạng thái/kết quả, không tạo thêm lượt Qwen; cùng ID nhưng nội dung khác là xung đột. Lượt đã xử lý cùng ảnh, loại biến thể, tham số và cấu hình Qwen cũng được dùng lại khi phù hợp, dù consumer gửi ID yêu cầu khác. Bot ghi trạng thái yêu cầu bền vững để không quên khi restart. Không có cơ chế kéo dài hạn ảnh hoặc tải ảnh về máy chính.

Bot thực hiện Qwen tại nơi giữ ảnh, giữ `ocr_pass_id`, biến thể chữ/vùng/lần thử và công bố **gói raw revision mới** sau job đã nhận có kết quả hoặc lỗi trong lúc chạy; `captured_at` luôn là giờ bot bắt tin ban đầu. Yêu cầu bị từ chối ngay do ảnh hết hạn, revision cũ, quyền hoặc ngân sách chỉ trả status bền vững theo `request_id`, không tạo gói raw giả. Máy chính lấy và ACK gói mới qua Sync như mọi gói file, rồi Document Intake phân tích lại và tạo result/revision **nội bộ** khi có chữ mới. Giá trị đã duyệt chỉ hiện thành thay đổi đề xuất để người dùng so, không tự ghi đè. Nếu ảnh hết hạn, mất file, Qwen lỗi hoặc hết ngân sách, người dùng thấy trạng thái cụ thể; không ngầm nói ảnh đã được đọc đủ. Yêu cầu này áp dụng cho **ảnh đã được bot ghi nhận**; tìm lại sự kiện bot chưa từng nhận vẫn thuộc MIN-90.

## 4. Phân tích, thẻ và xác nhận

**Đã chốt: regex/phân loại/bóc trường/ghép mặt giấy tờ, người, tài sản và nhóm hồ sơ chạy trong Document Intake của máy công chứng sau Sync.** Bot chỉ gọi Qwen và làm công việc cần byte ảnh như thử xoay/cắt/đọc lại vùng ảnh; máy chính không gọi Qwen trực tiếp cho ảnh Zalo. Khi cần thêm chữ, Document Intake gửi yêu cầu OCR lại theo §3 cho bot. Document Intake tạo thẻ ứng viên người/tài sản, nhóm tạm, bằng chứng, xung đột và phiên bản kết quả **nội bộ** từ raw đã nhập. Parser cần dùng cùng quy tắc cho nguồn Zalo và upload thủ công; hướng MarkItDown đi vào cùng lớp văn bản/nguồn khi được tích hợp. MarkItDown hiện là POC riêng, chưa phải runtime chung.

Khi có vị trí OCR đáng tin, Document Intake được dùng **quan hệ tương đối giữa các dòng chữ** — nhãn và giá trị ở hai dòng kề nhau, hai cột trên CCCD, hàng/cột và nhiều dòng trên GCN — làm bằng chứng bổ sung cho chữ và regex. Với nhãn và giá trị trong cùng một dòng, parser dùng vị trí dòng cùng nội dung chữ; không suy ra hộp tọa độ riêng cho từng từ. Ảnh chụp điện thoại có góc, độ nghiêng và khoảng cách khác nhau nên không gán trường bằng một ô pixel cố định cho mọi ảnh. Nếu vị trí thiếu/sai khung, quay về phân tích chữ và đánh dấu trường mơ hồ để người dùng xem; bot không được tự suy ra người, tài sản hoặc giá trị pháp lý từ tọa độ. Parser dùng chung vẫn chấp nhận nguồn chỉ có chữ, gồm upload thủ công hiện tại và adapter MarkItDown khi được tích hợp; phần này không đổi đường OCR upload đang chạy.

Ghép tài sản phải phân biệt giấy chứng nhận và thửa đất: serial GCN xác định giấy, một giấy có thể có nhiều thửa; thửa+tờ phải có địa phương. Trang chủ sở hữu, trang thửa đất và trang biến động có thể ở các ảnh khác nhau, cần ghép bằng chứng theo khóa đủ mạnh và giữ lịch sử/giá trị mâu thuẫn. Trùng tên chủ hoặc chỉ trùng thửa không đủ để gộp; dữ liệu thiếu khóa là ứng viên cần xem lại. Không biến việc cùng người/tài sản thành cùng hồ sơ. `land_rows` trong **kết quả nội bộ Document Intake** biểu diễn các thửa; `Property.land_rows_json` hiện tại của máy công chứng là các dòng loại đất/diện tích/thời hạn, không được coi là cùng cấu trúc khi ánh xạ.

Trước khi đưa vào input soạn hồ sơ, người dùng chọn nhóm/thẻ, xem xung đột, sửa giá trị, chọn hồ sơ mới hoặc có sẵn và bấm xác nhận. Lựa chọn đó được lưu trong vùng nháp Zalo riêng; chỉ thao tác **Cập nhật** rõ ràng mới được ghi vào Customer/Property/case_state_json sau kiểm tra từng trường. `case_state_json.stage` hiện đã có thể được Word sử dụng nên không được dùng nó làm vùng nháp chưa xác nhận. Bridge nghiệp vụ kiểm revision kết quả và dấu kiểm trạng thái hồ sơ/Customer/Property đã xem trước ngay trong một transaction; case hiện không có cột version. Retry/click lặp không tạo đương sự/tài sản trùng. Không tự gán vai trò bên mua/bên bán/thừa kế từ OCR; giữ các bước xác nhận hiện có của Case Workspace.

Các thẻ dùng trường person/property đang có trong [document-intake](../document-intake/spec.md) và [kiểm kê hiện trạng](v2-current-state-audit.md). Dữ liệu thiếu để trống; kết quả OCR/regex là gợi ý, không được ghi thành dữ liệu đã xác nhận. Mỗi thẻ/field giữ tham chiếu tới raw event, raw OCR và dòng chữ nếu có. Tham chiếu ảnh ở máy chính chỉ là ID nguồn để người dùng tìm trên Zalo; không là path, link hay thumbnail. Hệ thống biết hạn ảnh module từ metadata, không tự biết ảnh còn trên ứng dụng Zalo thật hay không; nếu người dùng không tìm được ảnh thì ghi nhận “Chưa đối chiếu được” theo thông tin người dùng.

`result_id`, `revision` và `processing_scope_id` của **Document Intake** xác định kết quả/phạm vi xử lý nội bộ sau khi raw đã nhập; chúng không do bot cấp hoặc nằm trong base package. `source_refs` nối từng trường về raw record/trang/dòng đã nhập. Máy chính lưu các revision riêng và chỉ áp dụng bản người dùng đã chọn. Không suy ID người hoặc hồ sơ từ số thứ tự mảng.

Khi đếm người, phân biệt số ảnh, số giấy tờ, số người ứng viên và số người đã được duyệt. Hai ảnh cùng mặt trước không thành đủ hai mặt; ID lệch một số hoặc tên giống chỉ là đề xuất ghép cần người duyệt. Một trang OCR có thể nhắc nhiều người; không mặc định mọi tên là một đương sự. Không dùng cờ paired hoặc summary.persons cũ làm số người đã xác thực.

Nhóm hồ sơ là gợi ý có thể tách/gộp/sửa. Khoảng thời gian nhóm dùng captured_at, không dùng source_sent_at hoặc imported_at để quyết định cụm. Cùng hội thoại, cùng người gửi, album/reply và text có thể là dấu hiệu; không tự gộp các hồ sơ chỉ vì gần giờ. Nhóm đã duyệt không bị dữ liệu mới âm thầm sửa.

Màn hình buổi sáng hiển thị chữ OCR, thẻ, lỗi, nguồn hội thoại, người gửi, captured_at chính, giờ Zalo gửi nếu có và giờ nhập phụ. Không hiển thị ảnh hoặc thumbnail. Có hướng dẫn mở tin trong Zalo thật bằng thông tin nguồn/giờ để user tự so; người dùng có thể không tìm lại được ảnh. Hạn 7 ngày của module không khẳng định thời hạn ảnh trên ứng dụng Zalo thật. Người dùng có thể sửa field, đánh dấu cần bổ sung, tách/gộp nhóm hoặc xác nhận phần đủ kèm ghi chú phần còn thiếu. Hai người sửa cùng bản phải phát hiện version cũ, không ghi đè nhau. Dữ liệu do user xác nhận không bị lần OCR/parser đến muộn thay ngầm.

## 5. Lỗi và giới hạn được công khai

- Tin bot đã nhận nhưng ảnh tải lỗi: giữ metadata/trạng thái, retry trong thời hạn ảnh còn khả dụng; quá 7 ngày tính từ captured_at thì đánh dấu hết hạn và không giữ ảnh.
- Qwen lỗi, thiếu key hoặc bị giới hạn: giữ trạng thái OCR lỗi, retry theo chính sách trước hạn ảnh; không build local OCR để cứu ngầm và không chặn gói dữ liệu.
- Máy chính tắt hoặc mất mạng: module vẫn nhận/OCR; gói raw chờ ACK giữ lại. Ảnh module vẫn tự xóa sau 7 ngày, không đợi máy chính. Document Intake phân tích khi máy chính mở và nhập raw.
- Gói truyền dở, hash sai hoặc ACK thất lạc: staging/verify/retry từ gói đã công bố; import chống trùng.
- Yêu cầu OCR lại bị từ chối do hết hạn ảnh, nguồn không hợp lệ hoặc hết ngân sách; Qwen thất bại: giữ trạng thái riêng theo `request_id`, không xóa raw cũ và không tự xác nhận trường đang thiếu. Gửi lặp cùng yêu cầu không tiêu thêm lượt Qwen.
- Bot không hề nhận một sự kiện: giai đoạn đầu chưa có cơ chế tự phát hiện và lấy bù đáng tin cậy. Ghi đây là OPEN issue cho giai đoạn sau; không hiển thị “đã đối chiếu đủ” nếu chưa có bằng chứng độc lập.
- Nguồn không cung cấp lại ảnh hoặc người dùng không tìm được ảnh trong Zalo: ghi rõ không đối chiếu được ảnh; không tạo link hoặc preview giả trên máy chính.

## 6. Tiêu chí nghiệm thu giai đoạn đầu

Các bài thử dùng tài khoản/nhóm thử được phép và danh sách tin gửi độc lập. Chỉ khẳng định kết quả trong tập thử; không suy rộng thành bảo đảm bắt đủ mọi event Zalo. Đo trạng thái, thời gian và version adapter/Qwen khi thử.

Khi thử hai repo trên cùng một máy local, mô phỏng “máy công chứng tắt” bằng cách dừng toàn bộ app/backend công chứng trong khi module vẫn chạy. Bài thử tắt máy vật lý dành cho bước triển khai hai máy sau; không tắt máy đang chứa cả hai repo rồi kỳ vọng module vẫn chạy.

| ID | Bài thử | Điều kiện đạt |
|---|---|---|
| T01 | Tắt app/backend công chứng, gửi 10 ảnh qua nguồn thử rồi bật lại | Module đã tải và gọi Qwen cho ảnh hỗ trợ; máy chính tự lấy raw, hiển thị 10 dấu ảnh/trạng thái và chữ OCR có được, rồi Document Intake tạo thẻ ứng viên, không có byte/link ảnh. |
| T02 | Một tin nhiều ảnh, album, hai tin cùng ảnh | Giữ đúng thứ tự và nguồn; tin khác ID không bị gộp vì hash ảnh giống; số ảnh không bị gọi là số người. |
| T03 | Kill collector trước/sau ghi journal, trong lúc tải hoặc gọi Qwen | Việc đã ghi tiếp tục sau restart; file tải dở không bị coi hoàn chỉnh; trường hợp chết trước journal được ghi là giới hạn chưa có fallback. |
| T04 | Server mất mạng tới Zalo hoặc Qwen lỗi | Có trạng thái lỗi và retry riêng; không xóa phiên Zalo do lỗi máy chính, listener không bị chặn vì OCR. |
| T05 | Máy chính crash trước raw commit, sau raw commit trước ACK hoặc mất ACK | Gói raw được nhập lại an toàn, không nhân đôi; ACK chỉ sau raw commit, module giữ gói chưa ACK. Bản gói file đã nhập còn mở được trong `imported/` để kiểm raw/status/hash đến hạn giữ theo chính sách MIN-102; parser lỗi sau ACK vẫn retry từ raw ở máy chính, kể cả khi MIN-99 đã dọn bản file đúng hạn. |
| T06 | Gói dữ liệu thiếu file, sai hash/version hoặc truyền dở | Máy chính không nhận như gói hợp lệ, báo lỗi rõ và xử lý các gói độc lập khác. |
| T07 | Tại mốc 168 giờ và sau mốc đó kể từ captured_at, máy chính vẫn tắt | Ảnh module tự xóa dù chưa ACK; gói raw/status và sổ chờ ACK còn; sau khi bật, máy chính nhập chữ/trạng thái rồi Document Intake phân tích mà không tải ảnh. |
| T08 | Sync lúc máy chính đang chạy | Chỉ kéo gói dữ liệu đã công bố qua kênh đã cấu hình; không gọi history Zalo, không gọi Qwen lại và không lấy ảnh. |
| T09 | Lặp gói, lặp trang feed, mất mạng giữa trang | Feed sequence không dùng message ID; cursor và sổ chờ giữ gói chưa ACK, nhập lại không nhân đôi. |
| T10 | Ba người, thiếu mặt sau, hai mặt trước, ID lệch một số | Thẻ/người là ứng viên cần xem; không báo đủ hai mặt hoặc số người xác thực từ cờ ghép cũ; user sửa/xác nhận được mà không xem ảnh trong app. |
| T11 | Hai hồ sơ gửi gần nhau, một hồ sơ nhiều đợt | Nhóm theo captured_at là gợi ý sửa được; không tự ghi hồ sơ hoặc ghi đè nhóm đã duyệt. |
| T12 | Raw OCR đến muộn hoặc parser chạy lại sau người dùng xác nhận | Document Intake tạo run/revision nội bộ riêng để so sánh, không thay giá trị đã xác nhận; raw OCR lỗi vẫn có gói metadata/trạng thái. |
| T13 | Bỏ collector, vẫn mở dữ liệu đã nhập trên máy chính | Raw/thẻ/hồ sơ đã nhập đọc được và parser có thể chạy lại từ raw, không cần cookie hoặc đường ảnh module; khi cần kiểm ảnh thì user mở Zalo thật. |
| T14 | Ghép thông tin một tài sản rải trên nhiều ảnh | Cùng serial có nhiều thửa vẫn giữ đủ số thửa/tờ riêng trong kết quả và DraftInput; không nhét danh sách thửa vào `Property.land_rows_json`. Khác serial/địa phương không gộp sai; trang biến động giữ xung đột/lịch sử và refs. |
| T15 | Duyệt kết quả đưa vào input soạn hồ sơ, bấm lại hoặc nhận revision muộn | Ghi người/tài sản đúng trường một lần, version conflict được báo, không overwrite dữ liệu đã duyệt; chọn loại hợp đồng dùng dữ liệu đã đưa vào. |
| T16 | Cùng một transcript giấy tờ đi qua Zalo và upload thủ công | Document Intake dùng cùng bộ quy tắc bóc/ghép và giữ source_refs theo từng nguồn; không có bản parser riêng trong bot. MarkItDown hiện là POC và chỉ áp dụng chung khi adapter văn bản được tích hợp. |
| T17 | Ảnh sổ cần xoay hoặc đọc lại vùng cuối để rõ ngày cấp; CCCD hai cột/GCN nhiều dòng có chữ dễ bị ghép nhầm | Module ghi các lần gọi Qwen/biến thể chữ và transcript mặc định theo tiêu chí kỹ thuật. Nếu đường đã duyệt có vị trí OCR, gói giữ vị trí dòng chữ theo từng lượt, khung tọa độ và dấu vết xoay/cắt/đổi kích thước; fixture kiểm vị trí cùng khung mới được so, mất/sai khung phải về text-only có trạng thái rõ. Document Intake dùng quan hệ nhãn–giá trị, cột/hàng để so chứng cứ và chọn ngày cấp, không khóa theo pixel tuyệt đối, không bịa vị trí từng từ hoặc tự xác nhận trường. Nếu đường v1 chưa xử lý được, có trạng thái/giới hạn chất lượng rõ. Yêu cầu OCR lại theo §3 chỉ đi bằng ID/loại biến thể, không đi bằng ảnh. |
| T18 | Listener mất kết nối từ 01:10 đến 04:30 rồi kết nối lại | Nhật ký kết nối vẫn còn sau restart; máy chính nhận và hiển thị đúng khoảng có thể không nghe được, không khẳng định Zalo không có tin trong khoảng đó. |
| T19 | Nguồn chưa bật, ảnh do chính bot gửi, My Documents | Không thu nội dung ngoài nguồn cho phép. Ảnh bot tự gửi trong nhóm đã bật và My Documents được thử theo quy tắc riêng; loại chưa hỗ trợ có trạng thái rõ. |
| T20 | Hàng OCR/gói chờ tăng, gần đầy đĩa; adapter phát sửa/thu hồi/reaction | Cảnh báo tuổi hàng/dung lượng có thời gian quan sát; loại sự kiện adapter hỗ trợ được lưu riêng và nối tin gốc, không âm thầm sửa dữ liệu đã duyệt. Loại không hỗ trợ được báo rõ. |
| T21 | Parser thấy ngày cấp GCN thiếu khi ảnh còn hạn và gửi yêu cầu OCR lại hợp lệ | Bot xác thực/kiểm nguồn và dùng ảnh nội bộ gọi Qwen theo loại biến thể; công bố gói file raw revision mới giữ `captured_at` gốc, `ocr_pass_id`/vùng/lần thử. Máy chính Sync/ACK sau raw commit rồi tạo revision kết quả nội bộ; giá trị đã duyệt không bị thay ngầm. Không có byte/link/path ảnh ở request, response, gói hoặc cache máy chính. |
| T22 | Yêu cầu OCR lại khi ảnh vừa hết 168 giờ hoặc file nguồn không còn | Bot không gọi Qwen; API trả `source_image_expired` khi quá hạn và `source_image_unavailable` khi file mất trước hạn. Yêu cầu bị từ chối trước khi tạo job chỉ cần trạng thái bền vững theo `request_id`; job đã nhận rồi thất bại mới công bố raw revision có mã lỗi. Không kéo dài hạn ảnh hoặc xóa raw cũ. |
| T23 | Gửi lặp cùng `request_id`, rồi gửi cùng ID nhưng loại biến thể khác | Lặp đúng trả cùng trạng thái/gói, chỉ một lượt Qwen; cùng ID khác nội dung bị báo xung đột, không tiêu thêm ngân sách. Cùng ảnh/biến thể/tham số/cấu hình đã có kết quả cũng dùng lại khi phù hợp. Restart giữa các bước vẫn giữ idempotency. |
| T24 | Yêu cầu hợp lệ nhưng Qwen lỗi/hết ngân sách hoặc consumer không có quyền | Mỗi trường hợp có mã/trạng thái riêng, không công bố chữ giả; giữ raw cũ và dữ liệu đã duyệt, cảnh báo người dùng; không lộ ảnh hoặc secret trong lỗi/log/gói. |

## 7. Chuyển từ v1 và điểm còn mở

Giữ [spec v1 lịch sử](spec-v1-legacy.md) và [phụ lục hiện trạng](v2-current-state-audit.md) làm bằng chứng về hệ thống cũ. V2 thay việc backend cùng tiến trình, shared media path, OCR sau người dùng chọn batch và giả định máy công chứng giữ ảnh. Không mang thời hạn 72 giờ của batch cũ sang gói raw; ảnh tại module có hạn riêng 7 ngày từ captured_at. **Tại MIN-103, producer SOT (CAP-01..16 và ghi chú §2 cũ) đã chuyển sang `docs/spec-producer.md` của repo module `D:\zalo-intake`** — spec này giữ phần consumer; baseline rủi ro/open issues theo module ở `docs/baseline-open-issues.md` của repo đó, còn `open-issues-v1-legacy.md` ở đây chỉ là bằng chứng v1.

Điểm còn mở trước khi triển khai: duyệt contract gói **raw OCR/status/nguồn**, API/biên nhận và **lệnh OCR lại có giới hạn** cùng quyền truy cập; chốt danh mục biến thể, quota và version quy tắc/schema kết quả **nội bộ Document Intake**; quyết định cách user tìm tin Zalo khi chỉ có metadata; đo tốc độ Qwen và dung lượng 7 ngày; xác minh hành vi nguồn đối với ảnh nhiều đính kèm. **Thời hạn hữu hạn giữ raw trên bot sau ACK phải được MIN-92 chốt trước thử dữ liệu thật**; gói bot chưa ACK vẫn phải giữ. Chính sách giữ bản `imported/` trên máy chính thuộc MIN-102. Cấu hình server thật chốt sau thử local. **Lấy bù/đối chiếu tin bot chưa nhận là OPEN issue giai đoạn sau**, không nằm trong nghiệm thu giai đoạn đầu. Tài liệu này chưa nói runtime đã thay đổi hoặc lỗi cũ đã được sửa.
