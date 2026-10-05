# Trích văn bản theo cấu trúc và bộ quy tắc

**Trạng thái:** Chiến lược Owner chốt 04/10/2026; chưa triển khai.
Danh sách loại văn bản, nhóm cấu trúc và bộ mẫu nghiệm thu đang chờ đầu vào.
**Owner:** `notary_v2`; lõi quy tắc dùng chung tại `tools/regex_workbench/engine`.
Nguồn: Owner trong phiên review. Triển khai riêng tại
[TASK-11](../../../../backlog/tasks/task-11%20-%20Xay-lai-engine-trich-van-ban-theo-cau-truc-va-rule-dung-chung.md);
plan tổng tại [TASK-2](../../../../backlog/tasks/task-2%20-%20Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md).

## Quyết định và Tại sao?

Owner sẽ liệt kê khoảng 30 loại văn bản thường gặp, dự kiến khoảng 10 nhóm
có cấu trúc khác rõ ràng. Đây là ước lượng để khảo sát, không là số nhóm đã
được kiểm chứng. Nhận diện cấu trúc trước, chia vùng rồi chọn quy tắc trích
cho từng vùng. Vùng có cùng cấu trúc được dùng chung giữa các loại văn bản.

Tại sao: vá regex cho một mẫu không chứng minh nhận đúng những mẫu khác.
Không có mẫu cụ thể, đáp án và điều kiện thành công thì agent không biết
đang sửa đúng hay đang làm mất dữ liệu ở văn bản khác.

## 1. Ba cấp cấu hình, một lõi chạy

| Cấp | Nội dung | Ví dụ minh họa, chưa là danh mục Owner |
|---|---|---|
| Loại văn bản | Tên nghiệp vụ và dấu hiệu nhận diện | Những loại khác nhau có thể dùng cùng bố cục hai bên |
| Nhóm cấu trúc | Vùng nào, thứ tự/ranh giới nào, dùng bộ quy tắc nào | Tiêu đề → đương sự → tài sản → điều khoản → lời chứng |
| Bộ quy tắc vùng/trường | Nhận người, thửa, dòng loại đất và từng trường | Họ tên/ngày sinh/giấy tờ dùng chung trong vùng người |

Loại văn bản và nhóm cấu trúc là hai thông tin riêng. Không tạo 30 engine
hoặc chép 30 bản đầy đủ của cùng regex. Hai vùng giống nhau chỉ dùng chung
khi đã kiểm cả ranh giới, nghĩa trường và kết quả trên mẫu của hai loại.

```text
Đọc chữ và cấu trúc đoạn/bảng, giữ vị trí nguồn
→ nhận loại văn bản + nhóm cấu trúc bằng dấu hiệu
→ chia vùng, kiểm ranh giới
→ chọn bộ quy tắc trong từng vùng
→ tách Người/Tài sản, trích trường
→ kiểm giá trị và độ đầy đủ, giữ bằng chứng
→ trả gợi ý hoặc báo thiếu/mơ hồ để người dùng kiểm
```

MVP dùng cấu hình dữ liệu và hàm Python hiện có nếu phù hợp. Chưa quyết định
cài thư viện mới, xây ngôn ngữ cấu hình riêng hoặc bộ máy plugin.
`runner.py` đã có chia vùng; adapter DOCX hiện luôn nạp `transfer`. Hành vi
mới cần được kiểm trọn đường chọn cấu hình → adapter, không chỉ dev workbench.

## 2. Chọn bộ quy tắc và đường dự phòng

- Mỗi loại/nhóm ghi dấu hiệu nhận diện, dấu hiệu loại trừ, phạm vi được xét
  và mẫu chứng minh. Không chọn loại chỉ vì một từ xuất hiện ở điều khoản.
  Kết hợp tiêu đề, nhãn và bố cục thật của đoạn/bảng.
- Khi nhiều cấu hình phù hợp, giải quyết bằng điều kiện phân biệt đã ghi rõ
  và có test. Chưa phân biệt được thì trả mơ hồ; không chọn cấu hình đầu tiên
  vì tên file hay thứ tự danh sách.
- Trong vùng chắc chắn, thử quy tắc riêng của cấu trúc rồi biến thể dùng
  chung được phép. Ghi quy tắc nào đã chạy, vì sao chạy và có dùng dự phòng.
  Quy tắc lỗi/timeout báo lỗi; không biến lỗi thành “không có dữ liệu”.
  Danh sách dự phòng hữu hạn, không lặp lại vô hạn; có giới hạn thời gian
  mỗi rule và toàn lượt xử lý, được kiểm bằng mẫu trong giới hạn đầu vào.
- Không nhận diện được toàn văn bản: chỉ giữ gợi ý từ vùng/nhóm có bằng
  chứng rõ, báo phạm vi chưa xác định. Không chạy mọi regex trên toàn file
  rồi chọn kết quả trông giống nhất. Dữ liệu này không được tính là trích
  đầy đủ thành công.
- Khi thiếu vùng hoặc gặp một file có nhiều văn bản, không giả định toàn
  file thuộc một loại duy nhất hay bỏ phần sau mà không báo. Cách xử lý cụ
  thể phải được xác định từ bộ mẫu trước khi thêm vào phạm vi hỗ trợ.

## 3. Thành phần của một quy tắc

Mỗi rule có mã ổn định, phiên bản, phạm vi áp dụng, dấu hiệu bắt đầu/dừng,
nhóm giá trị cần lấy, điều kiện loại trừ và ca đúng/sai. Kết quả giữ nguyên
chữ, vị trí nguồn, mã rule và trạng thái; chuẩn hóa không ghi đè chữ gốc.

Các thành phần dùng chung có thể gồm danh xưng, nhãn trường, dấu phân cách,
giá trị và điểm dừng. Ví dụ `ông A`, `ông: A`, `ông/bà A`, `ông/bà: A`,
đánh số trước tên, xuống dòng hoặc đặt trong bảng. Đây là biến thể cần kiểm,
không chỉ thêm dấu `:` vào một regex rồi coi đã bao phủ.

Phải có ca không được nhận: ngày chết hoặc địa chỉ không mở người mới;
người trong lời chứng/điều khoản không tự thành đương sự; dấu chấm `P.`/`TP.`
không tự kết thúc địa chỉ. Tách bản ghi trước khi ghép các trường; không lấy
ngày sinh của người B vào người A. Danh xưng là chữ nguồn, không tự xác nhận
giới tính hoặc vai trò pháp lý.

Đầu ra theo dữ liệu hệ thống: mỗi thửa một tài sản; cùng sổ giữ cùng serial;
diện tích tổng giữ riêng với dòng loại đất. Thiếu giấy tờ không được xóa một
người rõ tên. Nhiều giá trị mâu thuẫn giữ lựa chọn/bằng chứng, không lấy ngầm
giá trị đầu tiên. Xem [Stage](../stage.md) và [luồng DOCX](./docx-import.md).

## 4. Mẫu, đáp án và nghiệm thu

Trước khi viết rules, lập bảng loại → nhóm → mẫu → vùng → trường mong đợi.
Từng mẫu có đáp án về loại/cấu trúc, số Người/Tài sản, giá trị trường và
đoạn chữ làm bằng chứng. Thư mục/tên file không thay đáp án đã được kiểm.
Loại chưa có mẫu được ghi “chưa có mẫu”, không tự coi giống loại gần nhất.

Tách bộ dùng sửa và bộ giữ lại để review độc lập, tránh hai bản gần giống
của cùng mẫu bị chia sang hai bộ. Mỗi nhóm có mẫu chuẩn, biến thể trình bày
và trường hợp dễ nhận nhầm; kiểm cả việc dùng chung vùng giữa các nhóm.
File thực tế giữ ở kho cục bộ theo quy tắc dữ liệu; test Git dùng dữ liệu
tự dựng/đã ẩn danh và giữ cấu trúc cần kiểm.

Nghiệm thu trên bộ đáp án đã chốt: đúng loại/nhóm/vùng, đúng số bản ghi,
đúng trường và đúng người/thửa chứa trường; mọi trường nguồn trong phạm vi
phải được trích hoặc báo rõ chưa giải quyết. Thiếu/mơ hồ không được tính
thành công đầy đủ. Hợp đồng đáp án 3 người/1 tài sản phải trả đúng 3/1,
không có người/tài sản giả. Không tự hạ tiêu chí khi kết quả còn sai.

Báo cáo riêng theo loại, nhóm và trường: bao nhiêu mẫu đạt toàn bộ; giá trị
lấy đúng, lấy sai, bỏ sót, mơ hồ; nguyên nhân ở đọc nguồn, nhận loại, chia
vùng, tách bản ghi hay trích trường. Giữ thời gian chạy và lỗi/timeout.
Không công bố tỷ lệ chính xác từ số unit test xanh hoặc bộ mẫu chưa có đáp án.

## 5. Thứ tự triển khai và tham khảo

Lập danh mục/mẫu/đáp án → phân nhóm và catalog rules → thử một lát cắt có
ít nhất hai loại dùng chung vùng → kiểm bộ giữ lại → mở rộng các nhóm còn
lại → tích hợp DOCX/Stage. Danh mục chưa đủ thì chưa chốt số nhóm hoặc báo
đã hỗ trợ đủ 30 loại. Task engine và task tích hợp DOCX có trách nhiệm riêng.

Tham khảo cấu trúc, **chưa chọn làm thư viện của sản phẩm**:

- [invoice2data](https://invoice2data.readthedocs.io/latest/tutorial.html):
  mẫu có dấu hiệu chọn/loại trừ, regex cho trường và bộ xử lý vùng dòng có
  điểm bắt đầu/kết thúc. Học cách tách dữ liệu mẫu khỏi lõi; không mang luật
  mặc định của hóa đơn sang văn bản công chứng.
- [Dedoc](https://dedoc.readthedocs.io/en/latest/tutorials/using_patterns.html):
  nhận cấu trúc từ kiểu đoạn và các pattern cho tiêu đề/danh sách/đoạn.
  Học cách phối hợp bố cục với chữ. Việc chọn pattern đầu tiên của công cụ
  không thay quy tắc giải quyết mơ hồ của sản phẩm này.

Tham khảo được kiểm 04/10/2026 bằng tài liệu chính thức. Đây là căn cứ cho
đề xuất giữ engine gọn, chưa là bằng chứng regex cho tiếng Việt đã đạt.
