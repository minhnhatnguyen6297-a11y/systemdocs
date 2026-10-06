# Tham khảo cách tổ chức rule: invoice2data và Dedoc

Ngày: 05/10/2026. Theo yêu cầu Owner, hai Luna đọc code riêng từng repo; parent đọc lại các phần quyết định và tổng hợp. Đây là báo cáo tham khảo trước khi duyệt bảng dấu hiệu, không phải spec hoặc plan triển khai.

## Trả lời câu hỏi chính

**Liệt kê dấu hiệu là bước đúng hướng của một bộ trích theo quy tắc.** Hai repo được nhắc trước đây đều có cách khai báo mẫu nhận diện. Tuy nhiên, danh sách “tên bắt đầu bằng Ông/Bà, ngày sinh bắt đầu bằng Sinh ngày” mới mô tả một phần của rule: còn phải xác định phạm vi tìm, phần giá trị cần lấy và cách giữ các bản ghi riêng.

Bảng 56 mục phù hợp để Owner duyệt từ ngữ và ý nghĩa trường. Không cần Owner viết regex. Agent phải chuyển các dấu hiệu đã duyệt thành quy tắc có giới hạn rõ, rồi kiểm bằng văn bản và đáp án mong đợi. Nhận xét này là kết luận của parent từ code đã đọc; không phải tuyên bố có một tiêu chuẩn duy nhất cho mọi engine trích xuất.

## Code của họ làm gì?

| Việc | invoice2data | Dedoc | Điều phù hợp để tham khảo |
|---|---|---|---|
| Chọn quy tắc | Mẫu khai báo từ khóa cần có, từ khóa loại trừ và mức ưu tiên. | Bộ pattern phân loại dòng; có thể dựa trên heading/list của Word hoặc chữ. | Phân biệt dấu hiệu nhận loại/vùng với dấu hiệu nhận trường. |
| Nhận dấu hiệu | Một trường có thể có nhiều regex; gom các giá trị khớp. | Có `StartWordPattern` kiểm tra cụm mở đầu dòng và `RegexpPattern` kiểm tra mẫu chữ. | Một danh sách biến thể như Ông/Bà/Tôi là có cơ sở. |
| Lấy giá trị | Regex có phần bắt giá trị; có chuyển kiểu và xử lý kết quả. | Pattern cấu trúc chỉ trả nhãn/cấp của dòng, chưa bóc tên/ngày thành trường. | “Nhận ra dòng có tên” và “lấy đúng tên” là hai công việc khác nhau. |
| Giữ phạm vi | Bộ đọc dòng có mốc bắt đầu/kết thúc; có cấu hình dòng mở đầu, dòng tiếp và dòng cuối. | Dựng cây từ cấp dòng; có điều kiện ghép nhiều dòng. | Phải biết thông tin thuộc Người/thửa/giấy tờ nào trước khi gán trường. |
| Quy tắc chồng nhau | Chọn mẫu theo ưu tiên; bộ regex trường có thể gom từ nhiều pattern. | Dùng pattern khớp đầu tiên; pattern cụ thể cần đứng trước pattern rộng. | Chốt cách ưu tiên để Ông không lấy mất tiền tố Ông/bà. Đây là trách nhiệm kỹ thuật cần kiểm thử. |

Nguồn code đối chiếu:

- invoice2data: [chọn mẫu](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/invoice_template.py#L157-L194), [bộ regex trường](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/parsers/regex.py#L25-L104), [vùng dòng](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/parsers/lines.py#L255-L309).
- Dedoc: [nhận cụm đầu dòng](https://github.com/ispras/dedoc/blob/a02300423e2ef2eb1c90890b77c839735ce1c488/dedoc/structure_extractors/patterns/start_word_pattern.py#L63-L82), [thứ tự pattern](https://github.com/ispras/dedoc/blob/a02300423e2ef2eb1c90890b77c839735ce1c488/dedoc/structure_extractors/patterns/pattern_composition.py#L30-L56), [dựng cây và ghép dòng](https://github.com/ispras/dedoc/blob/a02300423e2ef2eb1c90890b77c839735ce1c488/dedoc/structure_constructors/concrete_structure_constructors/tree_constructor.py#L31-L63).

### Một ví dụ thật trong repo

Template QualityHosting của invoice2data có hai cách tìm ngày. Phần dịch vụ được giới hạn từ nhãn “Contract No.” đến “Total EUR”, có rule riêng cho dòng đầu, dòng mô tả tiếp và dòng cuối. File đáp án đi kèm chứa 7 dịch vụ, mỗi dịch vụ giữ mô tả nhiều dòng trong một bản ghi. Điều đáng học là họ khai báo cả **dấu hiệu lẫn cách gom dữ liệu**, và có đáp án cụ thể để so sánh. [Template](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/templates/de/de.qualityhosting.yml), [đáp án JSON](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/tests/compare/QualityHosting.json).

Dedoc có test phân biệt dòng chương và điều bằng pattern, rồi kiểm loại/cấp dòng. Kết quả này kiểm chứng việc nhận cấu trúc; chưa kiểm chứng trích Người/Tài sản. [Test cấu trúc](https://github.com/ispras/dedoc/blob/a02300423e2ef2eb1c90890b77c839735ce1c488/tests/unit_tests/test_doctype_default_structure_extractor.py#L60-L84).

## Áp vào bảng dấu hiệu của mình

Minh họa dưới đây là đề xuất của parent, chưa sửa bảng đang chờ duyệt. Không yêu cầu bổ sung câu hỏi nghiệp vụ ở lượt này.

| Trường | Vùng được đọc | Dấu hiệu | Cách lấy và dừng | Ví dụ → kết quả mong đợi |
|---|---|---|---|---|
| Tên người | Khối thông tin của một Người trong vùng chính | Ông; Bà; Ông/bà; Tôi là; Họ và tên… theo danh sách được duyệt | Bỏ đúng toàn bộ tiền tố; lấy tên đến nhãn trường kế tiếp hoặc ranh giới đã nhận ra; không coi mọi xuống dòng đều kết thúc tên. | `Ông/bà: Nguyễn Văn A; Sinh năm: 1980` → tên `Nguyễn Văn A` |
| Ngày/năm sinh | Cùng khối Người | Sinh ngày; Ngày sinh; Năm sinh; Sinh năm… | Lấy ngày đầy đủ hoặc chỉ năm tùy chữ nguồn; không kéo sang ngày cấp. | `Sinh năm: 1980; CCCD số: …` → năm `1980` |
| Ngày cấp giấy tờ | Cụm của từng giấy tờ thuộc Người | Cấp ngày; Ngày cấp… | Mỗi số giấy giữ ngày/nơi cấp của chính giấy đó; không chọn ngày đầu tiên của toàn văn bản. | Hai phiên bản cùng số nhưng ngày cấp khác → hai bộ giấy tờ theo quyết định đã có |

Đây là các thông tin cần có trong rule hoàn chỉnh. Phần triển khai có thể dùng cấu hình dùng chung thay vì sao chép regex cho mỗi loại văn bản. Dấu hai chấm, khoảng trắng và chữ hoa/thường thường có thể xử lý bằng thành phần chung; biến thể mang ý nghĩa khác như ngày sinh/ngày cấp vẫn phải gắn với đúng trường.

## Những mặc định không nên bê nguyên vào sản phẩm

- **Khử trùng giá trị:** bộ regex của invoice2data bỏ giá trị lặp. Một số giấy giống nhau có thể thuộc hai phiên bản khác ngày cấp; hai thửa có thể dùng chung serial. Cần giữ ngữ cảnh bản ghi theo quyết định của Owner. [Code khử trùng](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/parsers/regex.py#L197-L201).
- **Loại kết quả thiếu:** invoice2data có thể không trả kết quả của mẫu khi thiếu trường bắt buộc, rồi thử bộ đọc khác. Luồng của mình đã chốt trả phần engine lấy được, kể cả dòng thiếu; lớp đánh giá cuối chỉ báo kết quả. [Kiểm trường bắt buộc](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/extract/invoice_template.py#L651-L677), [đường xử lý](https://github.com/invoice-x/invoice2data/blob/31e6a4c362509baf25445dfa84c82b8090d14fb3/src/invoice2data/api.py#L159-L195).
- **Bắt buộc mốc kết thúc:** bộ `lines` cần cả `start` và `end` để đọc khối; không lấy nguyên giả định đó thành điều kiện phải có phần ký/lời chứng. Vùng chính của từng loại phải có cách xác định phù hợp, theo quyết định đã chốt.
- **Ghép dòng tự động:** Dedoc có thể nối các dòng cùng loại/cấp. Cần xác định rõ khối Người/thửa/giấy trước khi dùng ý tưởng này để tránh nối hai bản ghi riêng.

## Kết luận và giới hạn bằng chứng

Giữ bảng dấu hiệu làm tài liệu để Owner duyệt là phù hợp. Phần cần học từ hai repo là tổ chức dấu hiệu thành quy tắc có phạm vi, cách lấy giá trị và ví dụ kiểm chứng. Việc liệt kê 56 mục tự nó chưa chứng minh engine sẽ trích đúng; code và bộ mẫu có đáp án mới chứng minh điều đó.

Đã đọc code, template, test và JSON kỳ vọng; không cài/chạy hai thư viện, không thử chúng trên hồ sơ khách hàng. Chưa có căn cứ chọn một repo làm thư viện sản phẩm. Bảng dấu hiệu, code và spec/plan của sản phẩm chưa được sửa trong lượt này.

Hai báo cáo Luna: [invoice2data](invoice2data-report.md), [Dedoc](dedoc-report.md). Source được chốt theo commit `31e6a4c362509baf25445dfa84c82b8090d14fb3` và `a02300423e2ef2eb1c90890b77c839735ce1c488`. Các liên kết GitHub trong báo cáo trỏ đúng hai commit này. Bản source tải để đọc chỉ nằm cục bộ, không đóng gói vào commit bàn giao.
