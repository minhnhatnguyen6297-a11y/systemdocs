# Zalo — nguồn tiếp nhận tài liệu

Chương của [SPEC notary_v2](../../SPEC.md); cập nhật 17/09/2026.
Chủ dự án chốt **Zalo là nguồn input, chỉ sửa dữ liệu ở Stage**.
Luồng nguồn/lô đã có implementation; luồng đưa về Stage là yêu cầu đích
**chưa triển khai/nghiệm thu trong task tài liệu này**.

## 1. Phạm vi và nơi sửa quy tắc

Zalo giúp nhận và chọn tài liệu; không có bản dữ liệu nghiệp vụ để sửa/duyệt riêng.
Quy tắc OCR nằm tại [Tiếp nhận](../document-intake/spec.md); sửa, xác nhận và
lưu nằm tại [Stage](../case-workspace/contract.md). File này chỉ sở hữu kết nối,
nguồn, lô tài liệu và cách sử dụng đầu ra.

Dùng **tài khoản Zalo chung văn phòng**, connector chạy trên máy chủ theo
[OPEN_DECISIONS B2](../../../../OPEN_DECISIONS.md#b2--ranh-giới-đọc-zalo-đã-chốt).
Không đọc Zalo cá nhân nhân viên. “Zalo cá nhân” trong tài liệu cũ mô tả loại
API tài khoản thường, không phải quyền lấy tài khoản của nhân viên.
QR đăng nhập khác QR đọc giấy tờ. Không gửi tin, làm CRM hoặc tự xử lý nghiệp vụ từ chat.

## 2. Luồng sử dụng mới

1. Kết nối tài khoản được phép; đồng ý nhận dữ liệu và chọn nguồn.
2. Chọn tài liệu từ một hoặc nhiều hội thoại, chuẩn bị ảnh/PDF theo §4.
3. Với dữ liệu cần OCR, xem ảnh/kết quả ở cửa sổ chỉ xem.
4. Chủ động đưa kết quả về Stage đúng loại; sửa mọi dữ liệu tại Stage.
5. Cập nhật toàn cục theo chương Stage; Zalo không có nút Xác nhận riêng bỏ qua bước này.
6. Các đầu ra có dữ liệu đã soát chỉ lấy bản đã được Stage cập nhật thành công.

Luồng cũ “sửa trong modal → Xác nhận → JSON/Excel, không đi qua Stage” không còn
là hành vi đích. Mở/đóng OCR không tự xác nhận hay xóa kết quả tạm.
Không tự gán Người/Tài sản vào hồ sơ hoặc Diagram vì đã nhận tài liệu từ Zalo.

Giữ nhu cầu xuất JSON/Excel/PDF; không xóa chức năng chỉ vì đổi nơi sửa dữ liệu:
- JSON/Excel chứa dữ liệu đã duyệt: phải lấy từ Stage sau cập nhật toàn cục.
- PDF gộp ảnh chỉ là đầu ra tài liệu, không cần OCR/duyệt dữ liệu, không tạo
  dữ liệu nghiệp vụ và không phải đường vượt qua Stage.
- Stage cho xuất độc lập nằm trong ngữ cảnh nào, có cần chọn Hồ sơ hay không,
  cách nối snapshot với lô và thời điểm xuất còn mở. Không tự ép tạo hồ sơ.
- Gộp cửa sổ OCR tuân gate phân loại ở chương tiếp nhận. Khi chưa đủ engine,
  không mở giấy tờ khác hoặc ghép loại sai để giả lập luồng chung.

## 3. Kết nối, nguồn và đồng bộ — giữ phạm vi đã có

- Chỉ nhận nội dung sau khi người dùng đồng ý intake. Trước đó có thể lập danh
  mục nguồn nhưng không lưu chat hoặc tải tài liệu.
- Trên tài khoản văn phòng được phép: friends/groups và My Documents mặc định
  bật; strangers mặc định tắt. Lựa chọn bật/tắt chủ động phải được giữ qua đăng
  nhập lại, làm mới và thay đổi loại nguồn; không bị default ghi đè.
- Khi chuyển policy cũ mà chưa có dấu lựa chọn rõ ràng, yêu cầu đồng ý lại trước
  intake. Khi thay đổi đang chờ áp dụng, nguồn đó chưa được nhận content cho
  tới khi connector xác nhận; UI không báo sẵn sàng sớm.
- Làm mới nguồn chỉ đọc metadata. Giữ trigger đăng nhập/khôi phục phiên,
  sự kiện bạn/nhóm, kết nối lại, tra nguồn chưa biết, nút làm mới và đối chiếu
  định kỳ 60 phút. Không kéo lịch sử tin nhắn qua thao tác này.
- Khi tab Inbox đang hiển thị, giao diện đọc trạng thái/dữ liệu đã nhận từ
  backend mỗi 2 giây theo mặc định; khi tab hiện lại hoặc được focus thì làm
  mới ngay. Nhịp này không gọi Zalo hoặc tự kích Source Sync/Data Sync, và
  không thay listener realtime của connector.
- Danh sách có hoạt động xếp mới nhất trước, chưa hoạt động xếp theo tên;
  strangers tách rõ. Không hứa biết đầy đủ mọi stranger.
- Realtime nhận event khi connected; chỉ nguồn bật được lưu text/tải
  JPG/JPEG/PNG/PDF. Không nhận video, voice, sticker hoặc file khác.
- Nguồn chưa biết phải được xác định loại: friend/group theo default hoặc
  lựa chọn đã có; stranger chỉ có metadata tắt, không tải nội dung.
- My Documents chỉ nhận self-event đúng send2me_id, không phải mọi tin mình
  gửi đi. Realtime cần kiểm chứng tài khoản thật; history chưa được hứa hỗ trợ.
- Ba trạng thái chính: Cần đăng nhập lại, Mất kết nối, Đã kết nối. Đăng nhập lại
  ưu tiên cao nhất; “đang tự kết nối lại/connector dừng” là lý do mất kết nối.
- Chỉ mở QR khi user bấm đăng nhập; QR cũ/hết hạn không được tiếp tục hiển thị.
  Giữ thời hạn QR 100 giây, heartbeat mặc định 15 giây, ngưỡng mất heartbeat 45
  giây; phân biệt heartbeat/policy polling với đối chiếu nguồn 60 phút.
- Không tự đổi tài khoản; đổi tài khoản cần reset/onboard có phạm vi riêng.

Đồng bộ dữ liệu:
- Chỉ chạy khi user bấm, đã consent, connected, policy đã áp dụng và chưa có run
  active của tài khoản. Không tự chạy khi login/reconnect, không lấy history ngầm.
- Chốt danh sách nguồn bật và thời điểm bắt đầu; chỉ nhận dữ liệu thuộc phạm
  vi đó trong tối đa 7 ngày. Toggle sau đó không âm thầm đổi phạm vi của run.
- Giữ hai yêu cầu history User/Group; không mở My Documents history trước gate.
- Realtime được ưu tiên; run báo Đang đồng bộ / Hoàn tất best-effort / Lỗi.
  Có timeout, giữ item đã nhận thành công và cho chạy lại an toàn.
- Báo số event nhận, trùng, text mới, tài liệu mới và tài liệu tải lỗi.
  Link media hết hạn chỉ báo lỗi, không tạo tài liệu giả.
- Không hứa đầy đủ lịch sử; chỉ báo khoảng có thể thiếu. Đồng bộ xong không
  tự xóa cảnh báo khoảng thiếu hoặc khẳng định đã thu đủ.
- Nhận lại cùng event/payload không tạo bản thứ hai; payload khác cùng khóa
  bị từ chối. Không loại ảnh khác nhau chỉ vì cùng hash nội dung.

## 4. Lô ảnh/PDF và chuẩn bị tài liệu

- Người dùng chủ động tạo lô, chọn qua nhiều hội thoại, giữ lựa chọn khi chuyển
  hội thoại và đổi thứ tự. Một media/trang không chọn hai lần trong cùng lô;
  không tự chia lô theo người/loại giấy tờ.
- Trong lúc chọn, media mới nhận chỉ nối cuối danh sách: không đổi thứ tự
  cũ, cuộn trang tự động hoặc xóa các mục đã chọn.
- Trước Xử lý, lựa chọn là tạm trong trang; chưa hứa khôi phục qua reload.
- Xử lý phải kiểm toàn lô trước khi tạo: mặc định tối đa 20 MB/file, 100
  ảnh/trang và tổng byte/pixel theo cấu hình deployment. Sai loại, PDF hỏng/có
  mật khẩu, nguồn mất hoặc quá giới hạn: báo đúng item, giữ lựa chọn, không
  âm thầm bỏ item và xử lý phần còn lại.
- Tạo working copy riêng; không sửa file gốc. PDF được thay tại vị trí cũ bằng
  các trang đúng thứ tự: A, PDF, B → A, P1, P2, B.
- Chỉ crop/làm rõ/resize khi user yêu cầu xử lý. Cho chọn crop/không crop từng
  ảnh; không crop vẫn dùng toàn khung đã resize/làm rõ. Không thêm editor bốn góc.
- Sau khi đã tạo lô, preparation/preview nằm phía backend và khôi phục theo URL.
  Còn item đang chuẩn bị/lỗi thì chưa chốt preview; có thể thử lại hoặc bỏ item.
- User chọn một lần một hoặc nhiều đầu ra JSON, Excel, PDF sau khi duyệt
  preview. Chỉ khi backend xác nhận lựa chọn thì mới khóa nội dung/thứ tự/crop
  thành snapshot cho các đầu ra; lựa chọn trùng hoặc đồng thời phải được xử
  lý để chỉ một lần được chấp nhận. Không sửa ngầm snapshot hay thêm loại
  đầu ra sau đó; muốn thay đổi phải tạo lô mới.
- Sau khi backend nhận lựa chọn, job tiếp tục dù đóng tab. Chỉ chọn PDF không
  yêu cầu OCR hoặc Stage; chọn JSON/Excel dùng một kết quả OCR chung và chờ
  dữ liệu đã cập nhật từ Stage theo §2, không khôi phục nút Xác nhận OCR cũ.
- Có link Lô gần nhất. Nếu tạo lô mới khi lô trước chưa xong, cảnh báo kèm link
  để mở/lưu lô trước; không tự xóa lô cũ. Không hứa màn quản lý nhiều lô hoặc hard cancel.

## 5. Kết quả, lỗi, truy nguyên và thời hạn

- Raw OCR giữ gắn với ảnh/trang nguồn; retry OCR chỉ chạy item lỗi rồi ghép/parse
  lại với cache hợp lệ. Parse lỗi thì thử parse lại, không tự gọi OCR lại.
- JSON/Excel không xuất một phần khi còn lỗi dữ liệu/OCR; Stage phải cập nhật
  toàn cục thành công. Retry export dùng bản đã duyệt, không sửa/xác nhận lại ở OCR.
- Đầu ra hiển thị Đang tạo / Sẵn sàng / Lỗi / Hết hạn. Lỗi tất định như không
  có dữ liệu Excel không được gắn nút retry vô ích.
- Khu kết quả chỉ hiển thị một dòng xử lý OCR khi đã chọn JSON hoặc Excel;
  lô chỉ có PDF không có dòng OCR. Mỗi loại đầu ra đã chọn có một dòng
  trạng thái/file riêng. Khi cần duyệt dữ liệu, dòng OCR hướng về Stage,
  không mang trạng thái/nút sửa và Xác nhận riêng của modal cũ.
- Giữ đầu ra JSON/Excel/PDF và nguồn/thời điểm/trang để đối chiếu; JSON giữ
  source_refs, Excel giữ các cột Nguồn, Thời điểm, Trang. Không đổi wire format
  hoặc sheet hiện có trong task docs; thay liên kết Stage cần review riêng.
- Chỉ tạo sheet Excel có dữ liệu; không tạo workbook rỗng. PDF không cần OCR.
- Lô đã tạo giữ mốc hết hạn 72 giờ từ lúc validation thành công; quá hạn không
  retry/download/publish kết quả muộn. Chỉ giữ thông tin tối thiểu để URL báo Hết hạn.
- Đóng OCR không phải hết hạn lô. Cập nhật Stage dọn cache OCR tạm tương ứng,
  không xóa media nguồn hoặc lô/đầu ra còn hiệu lực. Dữ liệu đã chuyển sang
  luồng chính và file đã tải không bị xóa theo lô.
- Cần chốt ranh giới cache đủ cho retry/provenance sau cập nhật khi triển khai
  Stage-backed export; không lấy yêu cầu dọn modal làm quyền xóa mọi raw source.
- Giờ hiển thị/tên file theo Asia/Ho_Chi_Minh; không theo timezone ngẫu nhiên của server.

## 6. Bảo vệ dữ liệu

- Giữ media nguồn tới khi có working copy; quota không được xóa media đang được
  lô chưa hết hạn sử dụng. Hết chỗ thì báo và tạm dừng intake thay vì xóa dữ liệu được bảo vệ.
- Text và media có quota/retention độc lập; text đầy không chặn media nếu còn chỗ.
  Text chưa có chức năng tự phân loại, LLM, hành động, thông báo nội dung hoặc export.
- Session/cookie chỉ ở connector; webhook phải xác thực/bind đúng account.
  Opaque ID không thay thế phân quyền, không đưa đường dẫn máy chủ vào browser.
- Outbox retry tới ACK, QR đăng nhập lại không làm mất delivery đã nhận;
  ACK chỉ khi object đúng nguồn, đọc được và khớp loại/kích thước.
- Không đưa chat, giấy tờ, tên nguồn, giá trị raw/đã sửa hoặc secret vào production log.
- Chỉ chạy local/LAN tin cậy khi chưa có access control; không public Internet.
  Khi có cơ chế phân quyền chung, mọi trang/API/download phải đi qua nó.

## 7. Kiểm chứng và các điểm chưa hoàn tất

- Gap code: [zalo_inbox.py:280](../../../routers/zalo_inbox.py#L280) vẫn phân biệt
  raw/confirmed, [zalo_inbox.py:800](../../../routers/zalo_inbox.py#L800) có endpoint
  confirm riêng. Không tuyên bố đã đi qua Stage sau khi chỉ sửa SPEC.
- [open-issues.md](open-issues.md) giữ bằng chứng live cũ; phải xác minh lại,
  không lấy số test/nhánh cũ làm nghiệm thu hiện tại.
- Còn mở: vị trí Stage cho xuất độc lập, snapshot cập nhật/lô, cache sau commit,
  quota deployment, live My Documents/history và mức đủ tốt của classifier.
- Giấy tờ khác hoàn thiện giao diện/Stage sau theo chương intake. Nhánh parse
  khai tử và mapping đã chốt cũ được giữ để triển khai tiếp, nhưng không
  lấy sự hiện diện parser làm cam kết luồng duyệt hoàn thiện.
- Tiêu chí mới: chỉ sửa Stage; đóng OCR không mất tạm; lỗi một vùng chặn cập
  nhật toàn cục; JSON/Excel lấy đúng bản Stage đã duyệt; PDF không tạo dữ liệu
  nghiệp vụ; không thay đổi source consent/privacy hoặc tự thu thêm dữ liệu.

## 8. Truy nguyên tài liệu cũ

[Bản 08/2026](reference-2026-08.md) giữ nguyên để tra các mã R/FR/SC và chi tiết
kỹ thuật trước đây; **không phải SOT hoặc giấy phép triển khai**.
Đặc biệt R-028, US-003, FR-009/010 và các ca sửa/xác nhận modal đã bị thay thế.
Khi cần chi tiết kỹ thuật cũ chưa mô tả ở đây, đối chiếu với code và quy tắc
hiện hành trước khi dùng; không khôi phục cả luồng cũ chỉ để test cũ chạy.
