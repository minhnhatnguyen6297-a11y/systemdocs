# Tra cứu địa chỉ theo lịch sử địa giới — NAIA-9/14–21

**Trạng thái:** Draft, đang nối vào ứng dụng · **Nguồn quyết định:** Owner
03–04/10/2026 tại [NAIA-9](../../../.agent/tasks/NAIA-9/decisions.md).

## Công dụng và Tại sao?

Giúp chuyên viên đối chiếu địa chỉ trên giấy tờ với tên xã/tỉnh cần dùng khi
lập hồ sơ, chọn nơi niêm yết hoặc đọc nơi cấp giấy khai tử. Máy chỉ gợi ý;
người dùng chọn, sửa hoặc bỏ qua. Không tự đổi một địa chỉ đã xác nhận.

[Kho timeline](./administrative-timeline.md) là nguồn dữ liệu duy nhất. Kho
giữ tên, mã, nơi quản lý và các lần thay đổi của xã, huyện, tỉnh. Trang này
giải thích **cách ứng dụng dùng kho**, không tạo danh mục hoặc lịch sử thứ hai.

Owner chọn [Bando](https://sapnhap.bando.com.vn/) cho tên xã/tỉnh hiện hành và
mô tả tiền thân gần nhất. Snapshot 04/10/2026 có 34 tỉnh, 3.321 xã và không có
danh mục huyện. Không dựng huyện mới, thôn mới hoặc mốc đổi tên chưa có nguồn.

## Ngày nào dùng cho việc gì?

| Việc | Ngày đọc giấy nguồn | Ngày cần đối chiếu tên |
|---|---|---|
| Địa chỉ Người | Ngày cấp giấy của chính người đó | `ngay_lap_ho_so` |
| Địa chỉ Tài sản | Ngày cấp giấy chứng nhận của chính tài sản đó | `ngay_lap_ho_so` |
| Nơi niêm yết | Ngày cấp giấy chứng nhận của tài sản được chọn | `ngay_lap_ho_so` |
| Nơi cấp giấy khai tử | Ngày cấp giấy khai tử | Cũng ngày cấp giấy khai tử |

Ngày lập hồ sơ là trường nghiệp vụ của hồ sơ, không thay bằng ngày chạy máy,
thời điểm tạo record hoặc ngày giấy tờ. Năm không có tháng/ngày chưa đủ để
tra một mốc cụ thể. Thiếu ngày vẫn được sửa trực tiếp, nhưng phải báo thiếu
dữ liệu cho tra cứu. Không lấy ngày CCCD thay cho ngày sổ đất.

Mốc 01/07/2025 giúp đọc cấu trúc địa chỉ: trước mốc thường có tỉnh/huyện/xã;
sau mốc tỉnh/xã không đòi huyện. Mốc này **không là ngày hiệu lực chung** cho
mọi dòng Bando, vốn có cả cập nhật năm 2026.

Nơi cấp giấy khai tử là cơ quan được ghi trên giấy ấy. Địa chỉ cư trú, nơi chết
và nơi niêm yết không tự chứng minh nơi cấp. Quy tắc suy nơi cấp giấy tờ của
người sống theo MIN-141 vẫn độc lập.

## Dữ liệu đủ và dữ liệu còn thiếu

Kho hiện giữ các mô tả Bando nguyên văn, chưa có ngày hiệu lực cho những quan
hệ ấy. Một kết quả duy nhất trong danh mục hiện tại chưa chứng minh tên đó
đúng tại một ngày trong quá khứ. Gợi ý phải phân biệt:

- **Danh mục hiện tại:** tìm được tên đích từ bằng chứng Bando; thiếu lịch sử
  có ngày để khẳng định đúng ngày hồ sơ.
- **Lịch sử đã xác nhận:** tên và quan hệ có nguồn/ngày được người phụ trách
  xác nhận, đủ bao phủ ngày hỏi.
- **Nhiều đích/chưa rõ:** chia tách, tên trùng, thiếu tỉnh hoặc thiếu bằng chứng;
  hiện các ứng viên, không tự chọn dòng đầu.

Các tên cũ tách từ văn xuôi Bando chỉ là dữ liệu tìm kiếm có thể tạo lại từ
nguồn. Chúng giữ ID dòng quan sát/nguồn, không tự thành ID đơn vị lịch sử,
quan hệ confirmed hoặc bằng chứng huyện/tỉnh cũ. Không ghi ngược kết quả
phân tích vào ledger trong lúc khách hàng tra địa chỉ.

## Thao tác và dữ liệu lưu

Người dùng nhập/sửa địa chỉ cùng ngày giấy tờ. Gợi ý đặt cạnh trường liên quan,
hiện khi dùng bàn phím hoặc chuột; nút chọn/áp dụng có nhãn rõ. Phản hồi cũ
phải bị bỏ nếu địa chỉ, ngày, dòng hoặc hồ sơ đã đổi trong lúc chờ.

Địa chỉ Người/Tài sản giữ **nguyên văn gốc** và thêm `(nay là …)` khi được chọn.
Không nối thêm lần nữa nếu đã có phần này. Không tự sửa thôn, số nhà hoặc
chi tiết ranh giới từ tên xã. Người dùng vẫn sửa tay được và lưu qua Stage.

Nơi niêm yết dùng địa chỉ của tài sản được chọn rõ. Hồ sơ có nhiều tài sản
không âm thầm lấy tài sản đầu. Kết quả chỉ đi vào ô nhập sau khi chấp nhận;
lưu metadata dùng revision hiện hành, xung đột không ghi đè cưỡng bức.

Nơi cấp giấy khai tử nhận địa chỉ/cơ quan nhập rõ của giấy ấy; chỉ gợi ý UBND
khi bằng chứng địa chỉ và lịch sử đủ. Giá trị nhập tay không bị thay bởi tra
cứu nền. Không gửi địa chỉ khách hàng ra website; tra cứu lúc làm hồ sơ chỉ
đọc dữ liệu cục bộ.

## Cách bổ sung và mở rộng về sau

Owner bổ sung lịch sử tại kho timeline bằng nguồn và ngày thật; xem hướng dẫn
[thêm A→B→C→D, gộp/tách và sửa dữ liệu](./administrative-timeline.md).
Ứng dụng phải đi qua các quan hệ đã xác nhận còn hiệu lực ở ngày hỏi, giữ
dấu vết qua các bước và mọi nhánh chia tách. Không đi qua quan hệ đang chờ
xác nhận để đưa ra kết luận lịch sử chắc chắn.

Bộ chỉ mục tìm tên chỉ giúp tìm nhanh, không sở hữu dữ liệu. Khi Owner sửa
lịch sử, phải nhận cả `revision` mới; không chỉ nhìn `dataset_version` của
lần tải Bando. Kiểm kho mới hợp lệ trước khi thay bản nhớ; lỗi tải/kiểm tra
phải hiện rõ phiên bản cũ hoặc lỗi, không gắn nhãn mới cho kết quả cũ.

Bản cài cần helper, schema và đúng ledger/snapshots công khai. Không đóng gói
database văn phòng, cấu hình riêng, khóa ghi hoặc archive lịch sử của người
quản lý. Nâng cấp định dạng kho phải theo hướng migration của spec timeline,
không tạo một danh mục riêng cho mỗi ô nhập hoặc sao chép tên vào code.

## Đường gọi và nơi xử lý

[`administrative_address.py`](../../../notary_v2/services/administrative_address.py)
đọc kho qua helper timeline, kiểm dữ liệu trước khi dựng bộ chỉ mục tìm tên.
`notary.address_lookup` đi qua registry và adapter của sidecar (phần Python
chạy cùng ứng dụng), không gọi website và không ghi dữ liệu hồ sơ.

Đầu vào gồm địa chỉ nguyên văn hoặc tỉnh/xã đã tách, huyện tùy chọn,
`source_date` và `target_date` đủ ngày/tháng/năm theo `YYYY-MM-DD`. Kết quả
gồm trạng thái tìm được một/nhiều/không có ứng viên hoặc đầu vào không hợp
lệ; mỗi ứng viên giữ tên đích, ID đơn vị và bằng chứng. `dataset_version`
và `revision` cho biết chính xác bản kho đã dùng. Phần `coverage` giải thích
kho đủ lịch sử có ngày hay chỉ có ứng viên từ danh mục hiện tại.

Tên cũ tách từ Bando giữ nguyên mô tả, ID quan sát và dấu chia tách/chưa xác
nhận tỉnh cũ. Không gọi một kết quả `match` là kết luận lịch sử nếu
`coverage` vẫn báo `current_catalog_candidates`. Kho mới lỗi thì trả
`reload_failed`, không tiếp tục đưa ứng viên cũ dưới nhãn phiên bản mới.

## Đầu vào, lỗi và ngoại lệ

- Khi cả `address` và cặp `province`+`commune` cùng có, `address` được ưu
  tiên: service chỉ phân tích `address`; `province`/`commune`/`district`
  gửi kèm bị bỏ qua (vẫn bị kiểm kiểu/độ dài). `district` chỉ còn nghĩa
  làm đối chứng phân biệt alias cũ, không bắt buộc.
- `status` nói **hình dáng kết quả**: `match` một ứng viên duy nhất,
  `ambiguous` nhiều ứng viên hợp lệ (không tự chọn), `not_found` không
  tìm được, `invalid_input` đầu vào không hợp lệ (thiếu ngày đầy đủ,
  địa chỉ không tách được xã+tỉnh, `target_date` trước `source_date`).
- `coverage.kind` nói **bản chất bằng chứng** — hai lớp độc lập với
  `status`: `confirmed_history` đủ chuỗi confirmed có ngày;
  `current_catalog_candidates` chỉ có danh mục Bando hiện tại;
  `insufficient_confirmed_history` không đủ chuỗi — kể cả khi một số
  nhánh chia tách đã confirmed (các nhánh đó vẫn được trả, không bị bỏ
  vì nhánh bên thiếu); `invalid_input`; `reload_failed` kho cục bộ lỗi.
- Lỗi đầu vào luôn nằm trong `result.data.status` (job thành công),
  không phải `error.code` của envelope; lỗi dữ liệu kho (khóa treo, thiếu
  trường, snapshot hỏng) trả `reload_failed`, không nhầm thành
  `invalid_input`.
- Ví dụ: `{"address": "junk"}` → `invalid_input`; xã thật nhưng chỉ có
  danh mục hiện tại → `ambiguous`/`match` + `current_catalog_candidates`.

## Trạng thái kiểm chứng

Đã nối service → registry → adapter → renderer và ghi nhận chạy thật qua
probe Electron cách ly (04/10/2026): lookup person hiện ứng viên, áp dụng
giữ nguyên văn + `(nay là …)`, tài sản chia tách trả đủ ứng viên, nơi
niêm yết theo tài sản đã chọn, lưu/mở lại giữ giá trị, database gốc và
DOCX gốc không đổi. Các ví dụ nhiều bước có ngày trong phép thử ghi rõ là
giả lập; không biến ngày thử thành lịch sử Bando. Nghiệm thu tên/ngày
thực tế vẫn phụ thuộc nguồn lịch sử Owner bổ sung.
