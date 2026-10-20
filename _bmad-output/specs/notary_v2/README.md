# Soạn thảo hồ sơ

**Cập nhật:** 17/10/2026. Gỡ cả nhánh Thừa kế **#21B BUILT 17/10/2026**; retained Quick CODE t3 **No actionable findings**, parent chấp nhận AC1–4. Node full 198 passed trước patch bỏ assertion chữ; file bị ảnh hưởng chạy lại 25 passed; service 106 passed (24 warnings hiện có); Source Electron + real IPC/SQLite riêng đạt. Không claim packaged/Word; giữ giới hạn startup toast đã ghi.

## 1. Mục đích và luồng

Giảm đánh máy lại: nhận giấy tờ/chữ, kiểm tra Người/Tài sản, gán quan hệ khi văn bản cần rồi xuất Word. Luồng Input → Stage → Pool/Diagram → Word cho phép làm dở; không bắt hoàn thiện quan hệ không phục vụ văn bản đang soạn.

Stage giữ thông tin Người/Tài sản; Diagram giữ vai trò/quan hệ; Word dùng dữ liệu đã lưu. Một phần chưa đủ thông tin phải được chỉ rõ, không tự điền cho đủ.

<a id="context-ho-so-thu"></a>
### Context theo loại hồ sơ — owner 19/10/2026

Đây là phân loại **nghiệp vụ do owner định hướng**, không phải danh sách loại
đã được runtime triển khai. Mọi loại dùng dữ liệu chuẩn **Người, Tài sản,
Hồ sơ**; không tạo bộ trường riêng hoặc tự điền dữ liệu thiếu.

**Bổ sung owner 19/10/2026:** **chủ đất thuộc Hồ sơ**, không là thuộc tính cố
định của Tài sản hoặc mặc định node `owner`/`owner_row_id` Thừa kế. Thông tin
công chứng thuộc Hồ sơ, độc lập ngày tạo hồ sơ; inventory phải đủ số/ngày công
chứng, công chứng viên, thư ký và mọi trường Upload, không chỉ workspace Notary.
Key/kiểu/cardinality và DB-wire-output còn thiếu được chốt trong
[#41](../../backlog/story-upload-business-field-standardization.md), không tự
duyệt cột mới hoặc xóa trường cần thiết cho vừa schema hiện tại.
Không bóc/chuẩn hóa giá/cọc/thuê/vay/lãi/điều khoản thanh toán hoặc thời hạn
nghiệp vụ; **giữ thời hạn sử dụng đất** đúng cụm và timeout kỹ thuật. Portal
cần trường bị loại thì ghi xung đột để refine, không bịa/default hoặc tự quyết
bước nhập tay mới. Không sửa raw/lịch sử/runtime ở lượt tài liệu.
Một Người nhiều giấy tờ và địa chỉ là
[#42 riêng](../../backlog/story-person-multiple-identities-addresses.md);
model hiện hành ô đơn không được tự ép đa trị, model tương lai chưa chọn.

| Nhóm | Context nghiệp vụ cần giữ |
|---|---|
| 1. Chuyển nhượng | Hai bên. |
| 2. Đặt cọc | Hai bên. |
| 3. Di chúc | Pháp lý là đơn phương; trong bố trí nghiệp vụ của hệ thống có hai bên vì có người nhận. Owner: **“Người nhận tài sản theo di chúc có vị trí khác so với các văn bản khác”**. Đây là context **cấu trúc văn bản**: LLM đọc mẫu thực để tìm vùng/người nhận và mapping vào dữ liệu chuẩn; vị trí cụ thể chưa được cung cấp. Không diễn giải thành quyết định về ghế Diagram. |
| 4. Thuê đất, vay tiền, ủy quyền, tặng cho, văn bản cam kết | Theo nhóm hai bên thông thường. Đây không phải phê duyệt thêm enum hoặc khẳng định regex chuyên biệt cho tất cả văn bản này. |
| 5. Mua bán ô tô/xe máy | Hai bên; trường Tài sản và các biến thể xe chưa được chọn. **Chỉ ghi issue DEFERRED [#29](../../backlog/spike-vehicle-sale-case-scope.md); hiện không làm ca này**, không tự tạo field hoặc hồ sơ thử. |
| 6. Thế chấp | Ngân hàng cung cấp nội dung; văn phòng **chỉ soạn lời chứng**. Đầu vào **luôn thiếu thông tin tài sản** trong hướng dẫn này; không tưởng tượng tài sản bảo đảm, không tự dựng hợp đồng thế chấp đầy đủ thay ngân hàng. |
| 7. Thừa kế | Văn bản phụ có thể gồm từ chối nhận di sản, cử đại diện, thông báo niêm yết và tài liệu khác theo hồ sơ; không coi đây là checklist pháp lý bắt buộc/đã khép kín. |

Văn bản phụ điển hình của hồ sơ: **ủy quyền cho người của văn phòng đi làm
thay khách** (khác việc mặc định bên nhận ủy quyền là khách/bên giao dịch);
**đơn đăng ký, thường dùng Mẫu 18**, ghi công việc đề nghị cơ quan nhà nước
giải quyết; **bộ khai thuế gồm ba loại khi đổi chủ sử dụng**. Owner chưa cung
cấp tên/mẫu của ba loại thuế, không tự đoán hoặc sinh biểu mẫu. Đây là context,
không quyết định rằng mọi hồ sơ phải có đủ bộ phụ hoặc mọi văn bản phụ đều được
regex/OCR hỗ trợ.

Runtime hiện chỉ có `inheritance/{khai_nhan, thoa_thuan}` và
`two_party/{chuyen_nhuong, tang_cho, cho_thue, dat_coc}` theo contract hiện hành.
Nhận diện regex, phân loại nghiệp vụ và khả năng tạo/sửa/xuất hồ sơ là ba trục
khác nhau; không đổi enum, schema hoặc bỏ gate xuất để làm chúng có vẻ trùng nhau.
Di chúc, vay tiền, ủy quyền, cam kết, thế chấp và xe không được ghi là runtime
mới đã hỗ trợ chỉ vì có context trên.

Folder owner chuẩn bị là `D:\testcase`; đọc
[README chung](file:///D:/testcase/README.md) trước khi làm việc với bộ hồ sơ.
Hiện chỉ ghi context/README theo định hướng, **chưa tạo Word/corpus hoặc chạy
test/E2E**, chờ owner chỉ dẫn tiếp. Đề xuất mười bundle và bản nháp trong
`testdata/notary-e2e/v1/` trước lệnh dừng không phải nguồn triển khai được duyệt.
[Quyết định và phần chưa chốt](../../decisions/decision-owner-case-context-standard-data-20261019.md).

**Gate trước mọi lượt quét/đọc mẫu thực mới, corpus và E2E theo mẫu:** chờ #41
được nghiệm thu đầy đủ chuẩn DB/contract đã duyệt, cutover consumer và proof
luồng thật, không chỉ lập bảng mapping. Proof riêng #41 có thể dùng input
tổng hợp/kiểm soát và DB/profile cô lập khi được giao, không cần quét corpus
owner để đóng issue. #42 không tự là prerequisite; Scan/Upload production
không bị tắt. Sau gate vẫn chờ được giao thực thi.

Sau gate #41 và khi được giao chạy, theo vòng **LLM đọc hàng loạt mẫu thực → nhận diện cấu trúc
trước → so code → điều chỉnh code → test lại → sai thì lặp**; mục tiêu xuất đủ,
đúng thông tin hợp đồng trong ba đối tượng chuẩn. Các cấu trúc/mapping chưa chốt
có issue riêng theo loại ở [catalog #30–#38](../../backlog/README.md).
Văn bản lạ hoặc phần không tự quyết được vào
[#39 — tổng hợp xem sau](../../backlog/spike-unfamiliar-document-review-queue.md),
giữ nguồn và pending, tiếp tục các file đã rõ; không dừng cả lô hoặc tự thêm
field/nghiệp vụ. Đây mới là quy trình được ghi lại, chưa bắt đầu đọc mẫu/sửa
code/test. Chi tiết [vòng theo mẫu thực](../shared/extraction-rules.md#sample-iteration).
Trước mỗi lô đọc [báo cáo ổn định](file:///D:/testcase/BAO_CAO_KHAO_SAT.md),
sau mỗi lô cập nhật và giữ kết quả cũ. Chỉ claim chuẩn trường/mapping đủ sau
audit có tên/kiểu/format/nhóm/thứ tự/đích DB-wire/ràng buộc/nguồn canonical;
tách defined/Draft/unmapped, không suy mọi biến thể đã rõ từ key có sẵn.
Audit catalog nền đã ghi trong báo cáo; bộ trường Hồ sơ/Upload xuyên module
và mapping từng biến thể **chưa khép kín**; #41 đóng thiếu định nghĩa/mapping,
không coi catalog local Draft là implementation xong.
Riêng serial GCN có chuẩn nguyên văn/rỗng/trùng đã chốt nhưng có
[gap validation/persistence source tĩnh #40](../../backlog/bug-stage-raw-gcn-serial-contract.md).
Chưa có runtime reproduction, không phải yêu cầu owner chọn lại serial và
không phải record văn bản lạ trong #39.

## 2. Danh sách hồ sơ

Tên mong muốn là Danh sách hồ sơ. Người dùng xem danh sách, tìm/lọc, tạo nháp và mở hồ sơ. Nhãn trạng thái, người tạo, tên/ngày tạo là hướng mô tả; danh sách nhãn, nguồn tìm kiếm và trường lọc chưa chốt đầy đủ. Chức năng sẽ **làm lại** — **DEFERRED 17/10/2026** (owner tự triển khai spec sau); hướng trường hiển thị/tìm/lọc owner ghi là **Draft chưa duyệt**, chưa phải quy tắc. [Decision](../../decisions/decision-owner-case-list-redesign-deferred-20261017.md).

Chọn Thừa kế hoặc Hai bên khi tạo nháp. Loại không hỗ trợ hiện lý do và khóa thao tác không có khả năng, không tự chuyển sang Thừa kế. Tạo hồ sơ lần đầu chưa cần Diagram; intake/evaluate nháp không ghi database. Đổi loại của hồ sơ **đã lưu** chỉ qua đường chuyển loại đã duyệt (`inheritance` ↔ `two_party`): giữ ID + giá trị Người/Tài sản của Stage, reset Diagram theo domain mới (Thừa kế: seed **chỉ** node `owner` mới chọn — không seed khung 7 slot mặc định, không giữ quan hệ/dấu cũ, nhưng vẫn **đủ key bắt buộc** với `parentSlotIds`/`ownPositions`/`receivePositions` rỗng, `spouseSlotId:null`; Hai bên: 30 slot trống), buộc chọn `document_type` hợp lệ của loại mới và xác nhận phần Diagram mất trước khi ghi; chuyển vào Thừa kế cần `owner_row_id` từ Stage, vào Hai bên cấm trường đó. Không suy việc chọn loại lúc tạo nháp thành quyền tự đổi domain; `case_type`/`document_type` vẫn bất biến ngoài đường này ([decision](../../decisions/decision-owner-saved-case-type-conversion-20261016.md), contract §13.18).

Trong Soạn hồ sơ đã lưu, bấm **Đổi loại** cạnh loại hiện tại để mở dialog.
Văn bản mới và người để lại (khi vào Thừa kế) ban đầu chưa chọn; phải chọn rõ
và đánh dấu xác nhận xóa Diagram trước **Áp dụng**. Stage/thông tin hồ sơ còn
nháp thì dialog yêu cầu đóng và **Cập nhật** bằng luồng hiện có, không tự lưu
hay bỏ nháp. Nháp Diagram chỉ bị reset khi ghi thành công. Hủy/Escape/nền
trước Áp dụng không ghi; lỗi/xung đột giữ nháp và các lựa chọn. Sau Áp dụng
chờ kết quả nguyên tử, không đóng dialog giữa ghi. Command riêng
`notary.workspace_convert_type` giữ commit/update thường bất biến loại.

Chỉ hồ sơ `draft` được xóa. Xóa trong một lần ghi trọn vẹn: dọn dữ liệu thuộc hồ sơ nếu không còn được hồ sơ khác, participant, liên kết tài sản hoặc snapshot tham chiếu. Danh bạ người nhận ủy quyền tái dùng không bị xóa theo hồ sơ; không quét danh bạ mồ côi ngoài phạm vi. Lỗi phải khôi phục toàn bộ.

Thống kê Người/Tài sản đếm mỗi bản ghi thực sự gắn hồ sơ một lần, không đếm danh bạ rời; tài sản vừa chính vừa liên kết không đếm hai lần.

<a id="input"></a>
## 3. Input — đọc và kiểm tra nguồn

Nhận ảnh/PDF, DOCX, XLSX và chữ dán; tạo gợi ý có nguồn, không tự ghi hồ sơ, gán quan hệ hoặc chọn người nhận. Zalo đang tách riêng, không phải đầu vào đã tích hợp.

Giới hạn intake: tối đa 8 nguồn/lượt, 20 MB/file, PDF 50 trang, chữ 100.000 ký tự. Backend có thể siết chặt hơn, không tự nới. DOCX giữ vị trí đoạn/bảng theo XML; XLSX đọc bảng; ảnh qua OCR Qwen đã duyệt, không tự dùng QR/local OCR cứu lỗi.

Người dùng thấy nguồn, giá trị đọc được/chuẩn hóa, cảnh báo và lỗi từng nguồn. Sửa gợi ý rồi Đưa vào Stage chỉ tạo bản nháp. Phân tích thêm không làm mất gợi ý đang sửa; lỗi một nguồn vẫn giữ kết quả nguồn khác và báo kết quả một phần. Phản hồi đến muộn của hồ sơ cũ bị bỏ.

Không chắc ranh người/tài sản thì giữ nguồn và báo mơ hồ; nhiều giá trị phải chọn/sửa trước khi nhận. Trùng giấy tờ/serial chỉ cảnh báo, không tự gộp. Không suy giới tính từ tên, vai trò/quan hệ/sở hữu từ lời văn. Một file nhiều người/tài sản không mặc định là một hồ sơ.

Nhập Word giữ chữ lấy được ở đúng ô để sửa, kể cả lỗi gõ/dính chữ; không thêm ô nguyên văn hoặc tự sửa tên cơ quan. Ngày sai lịch, diện tích âm/không hữu hạn phải sửa; không lấy riêng năm để che ngày sai. Diện tích `1.234,5` đọc được; chỉ `1.234` thì giữ nguyên + báo mơ hồ. Thiếu trường vẫn cho kiểm tra/bổ sung; không vượt giới hạn khi nhận vào Stage.

Ảnh nhập tay được xem lại đúng nguồn. Không lưu bản nháp giấy tờ vào localStorage/log. Chỉ Cập nhật thành công mới ghi dữ liệu nghiệp vụ.

<a id="stage"></a>
## 4. Stage — sửa thông tin và Cập nhật

Người sửa theo dòng; tài sản theo cột. Thêm/sửa/xóa/sắp xếp chỉ đổi bản nháp. Mỗi dòng có `row_id` ổn định; ID database có thể chưa có trước lần lưu đầu. Sửa Người/Tài sản tại Stage, không sửa từ Pool hoặc Diagram.

| Nhóm | Quy tắc |
|---|---|
| Người | Sáu trường nghiệp vụ chính: tên, sinh, chết, số giấy tờ, ngày cấp, địa chỉ; có giới tính và trường kỹ thuật. Chỉ họ tên bắt buộc. Giới tính Nam/Nữ/trống; ngày đúng lịch hoặc năm riêng. Độ đầy đủ ngày giữ theo bằng chứng đã lưu của hồ sơ: `2010` vẫn là năm riêng, phân biệt với `01/01/2010`; đọc lại và xuất dùng giá trị đã commit, master danh bạ không đệm lại. Giấy tờ/địa chỉ có thể trống. |
| Giấy tờ | Người sống suy loại/nơi cấp/nhãn cư trú theo ngày cấp và mốc 01/10/2024; thiếu ngày để trống. Người chết dùng bằng chứng giấy tờ đã xác nhận, không mặc định nơi cấp. Nhãn nơi cấp phải phân biệt CCCD và giấy khai tử; địa chỉ người chết mang nhãn Nơi chết theo quy tắc đã có. Nhãn hiển thị theo bằng chứng: chỉ khi `loai_giay_to` là giấy chứng tử/khai tử mới mang nhãn `Nơi cấp giấy khai tử`, còn lại (kể cả người đã mất chưa có bằng chứng) là `Nơi cấp giấy tờ`; ô địa chỉ mang nhãn `Nơi chết` khi `loai_dia_chi` là Nơi chết; giữ nguyên giá trị `dia_chi`/`noi_cap` đã lưu và binding. |
| Tài sản | Tối đa 3; thứ tự 1..3 có ý nghĩa với dấu Chủ/Nhận. Serial nguyên văn, có thể trống/trùng, không ép mẫu hoặc thay mã XX. Địa chỉ không rỗng khi commit; thửa/tờ tùy chọn. |
| Loại đất | Mỗi tài sản tối đa 20 cụm loại đất–diện tích–thời hạn. Có thể để danh sách trống. Giữ vị trí trống; bỏ thời hạn lẻ cấp tài sản, không tự đắp vào cụm. |
| Hồ sơ | Nơi niêm yết nhập tay; người nhận ủy quyền từ danh mục/tạo mới; nội dung việc nhập tay. Ba dòng đặt dưới tài sản. |

**Người chết — owner 21/10/2026 đã chốt và giao runtime hẹp:** `Nơi chết` và nơi thường
trú/cư trú cuối cùng dùng cùng `dia_chi` hiện có, không thêm field/đổi câu Word
hoặc tự chọn giá trị mâu thuẫn. Ba loại là `Trích lục khai tử`,
`Trích lục khai tử (bản sao)`, `Giấy chứng tử`; nguồn `Giấy chứng tử (bản sao)`
quy về `Giấy chứng tử`. Số giữ nguyên giá trị, kể cả dấu phẩy/quyển; ngày cấp
là ngày của chính giấy, giữ độ đầy đủ. Cơ quan giữ xã/phường/thị trấn đúng
nguồn tại ngày cấp, không ép xã hoặc suy lịch sử chưa xác nhận.

Mỗi văn bản độc lập: **không đề xuất bổ sung hoặc tự ghép giữa văn bản**, kể
cả cùng bộ hồ sơ; không lấy bản đầy nhất/mới nhất. **Không gợi ý** trường
sinh/chết/giấy tờ Người từ `Đơn xin xác nhận`. Thiếu ngày chết chỉ là không
có thông tin: giữ `null`/rỗng, các trường có căn cứ được phép vẫn điền độc lập,
không chặn Người vì thiếu ngày/giấy, không tự coi còn sống hoặc tạo ngày giả/
Boolean/status. Địa chỉ chung rõ phạm vi và nhắc lại cùng người trong một
văn bản vẫn theo nguồn khi không mâu thuẫn; không suy chung giấy.
Raw/history/liên kết đã có giữ nguyên. Số giấy lưu nguyên giá trị, không
UNIQUE/tự ghép theo số; cập nhật chỉ theo ID chọn rõ hoặc row_id của chính
hồ sơ. Snapshot giữ bằng chứng loại/nơi cấp/nhãn, kể cả chết thiếu ngày.
Migration/consumer đã được actual proof synthetic (fresh+migrated DB, exact
Word; UI legacy giới hạn); **BUILT bounded**, chưa nghiệm thu toàn #41.

Tên và định dạng trường giữ chuẩn DB; alias cũ cần ánh xạ. Hai alias của cùng trường trái nhau phải báo lỗi, không chọn ngầm. Cụm đất lưu `property_land_rows`, duy nhất theo tài sản và vị trí; JSON cũ chỉ tương thích. Tên token cụm viết đủ `loaidat<M><N>`, `dientich<M><N>`, `thoihan<M><N>`: M là cụm, N là tài sản; không thêm dạng rút gọn gây lẫn cụm 12 với tài sản 2.

Thừa kế cần `owner_row_id` theo contract lưu hiện hành; Hai bên không nhận trường đó, tối đa 30 người. Hồ sơ cũ hơn 3 tài sản vẫn đọc đủ và cảnh báo; commit hiện chặn đến khi còn tối đa 3. Đây là giới hạn hiện hành cần xem xét riêng nếu thay đổi, không tự bỏ vì triết lý điền dần.

**Cập nhật:** kiểm toàn bộ Stage → ghi Người/Tài sản → dọn tham chiếu Diagram của đối tượng đã xóa → tính lại → tăng phiên bản → lưu trọn vẹn. Một dòng lỗi thì không lưu nửa chừng; báo đúng ô và giữ bản nháp. Lần đầu tạo hồ sơ dùng cùng `idempotency_key` khi thử lại sau timeout để tránh tạo trùng.

Mọi ghi gửi phiên bản đã đọc (`base_revision`); nếu server có bản khác, báo xung đột và cho tải bản mới hoặc giữ nháp để sao chép, không ghi đè cưỡng bức. Hồ sơ khóa chỉ đọc, vẫn xem/sao chép và dùng thao tác đọc được cho phép.

Không chặn chuyển tab chỉ vì đang nhập. Chuyển module phải giữ nháp; rời/đóng khi có thay đổi chưa lưu phải cảnh báo. Cập nhật nền không ghi đè ô đang sửa. Nút `Hủy thay đổi` của Stage đã bỏ cùng cơ chế khôi phục riêng; dirty, cảnh báo rời/đóng và nhánh bỏ nháp khi mở hồ sơ khác vẫn giữ.

<a id="pool"></a>
## 5. Pool và Diagram — gán quan hệ

Pool = người trong Stage đã cập nhật − người đã gán trên Diagram đang xem. Khi kéo thả, Pool phản ánh bản nháp Diagram; tải lại dùng bản đã lưu. Pool không có bảng dữ liệu hoặc nút lưu riêng.

Kéo người vào vị trí để gán; gỡ thẻ trả người về Pool nhưng không xóa Stage. Một người không xuất hiện ở nhiều vị trí xung đột. Xóa ở Stage chỉ ảnh hưởng sơ đồ khi Cập nhật thành công.

Hai bên có 30 vị trí cố định: p1..p15 Bên A, p16..p30 Bên B. Giữ ghế trống; thả lên ghế có người thì hoán đổi, không dồn danh sách. Thừa kế biểu diễn cha/mẹ, vợ/chồng, con và nhánh thế vị; dấu Chủ/Nhận (sở hữu/nhận tài sản) chỉ thuộc Thừa kế, chọn theo vị trí tài sản 1..3; đổi thứ tự/xóa tài sản phải cảnh báo đổi nghĩa.

Diagram có nháp riêng và nút Lưu sơ đồ. Xem cách tính chỉ đọc kết quả Python, không lưu và không tính lại bằng JavaScript. Quan hệ sai/vòng lặp/người ngoài Stage bị chặn; cấu trúc hợp lệ nhưng thiếu dữ liệu vẫn cho lưu, hiện rõ phần còn thiếu. Lỗi không xóa sơ đồ cũ.

**Gỡ cả nhánh Thừa kế — owner 17/10/2026: “B - gỡ cả nhánh”.** Xóa node gỡ cả node đó và mọi hậu duệ active theo cạnh cha/mẹ → con ở mọi độ sâu, kể cả slot trống/ẩn hoặc con còn cha/mẹ khác. Không gỡ spouse chỉ vì quan hệ vợ/chồng, không giữ ô trung gian rỗng và không tự nối lại cha/mẹ. Trước khi đổi draft, liệt kê đúng node sẽ gỡ và quan hệ sẽ ngắt, báo phần hưởng có thể đổi. Hủy/Escape/đóng không đổi draft/dirty/revision và không phát evaluate/save do thao tác này. Xác nhận áp một mutation draft rồi evaluate theo luồng có sẵn, chưa tự lưu.

Người vẫn ở Stage, về Pool theo gán trên node active. Giữ tombstone `deleted:true` trong Node v3 canonical; xóa quan hệ đi ra và tham chiếu đi vào phần bị gỡ, kể cả trên tombstone, để không còn parent sai hoặc spouse lệch hai chiều. Giữ ID/giá trị/thứ tự Người/Tài sản và mọi node, dấu Chủ/Nhận, quan hệ không bị tác động. Save tiếp tục nguyên tử/revision hiện có; lỗi giữ draft/bản lưu cũ; mở lại đọc đúng canonical đã lưu. [Quy tắc chi tiết](diagram-rules.md#branch-removal) · [Decision](../../decisions/decision-owner-inheritance-remove-entire-branch-20261017.md). Đây là spec đã chốt, chưa phải bằng chứng #21B built.

<a id="word"></a>
## 6. Xuất Word và quản lý mẫu

Chọn thư mục mẫu, các văn bản và thư mục đích; mỗi văn bản tạo một DOCX riêng. Không chọn lại Người/Tài sản ở màn xuất. Dữ liệu Người/Tài sản lấy Stage đã lưu; vai trò/quan hệ từ Diagram, kết quả tính từ Python.

Định hướng owner: trường có dữ liệu thì điền; trường hợp lệ chưa có dữ liệu để trống, không bắt hoàn thành sơ đồ nếu mẫu không cần. Lỗi mẫu, token không hỗ trợ, nguồn hỏng hoặc nguy cơ dùng dữ liệu khác với phần đang sửa phải báo rõ.

**Khoảng lệch cần xử lý:** luồng thư mục mẫu hiện đã cho xuất thông tin tĩnh khi thiếu Chủ/Nhận trong thừa kế; catalog cũ còn chặn theo nghiệp vụ, một số kiểm tra về Stage/tài sản/slot đại diện còn tồn tại. Định hướng mới không chứng minh các kiểm tra này đã được bỏ. Chi tiết các giới hạn hiện hành được ghi trong file mẫu Word để triển khai đúng phạm vi.

Ô Nơi niêm yết phải lưu trước khi xuất nếu đang khác bản đã lưu; không hiển thị chữ mới rồi xuất chữ cũ. Một file lỗi không làm mất file khác; báo Đã lưu/Lỗi/Bỏ qua theo từng file. Không ghi đè file có sẵn, tên trùng thêm số. Hủy giữ file đã tạo, dọn file đang ghi dở khi có thể.

Nhập DOCX có thể xuất theo bản gốc: người dùng chọn đúng từng vị trí cần thay, gắn với dòng và trường đã lưu, xác nhận rồi xuất. Không thay mọi chuỗi giống nhau; không sửa file nguồn. Tab Word tự tạo/quản lý mẫu lâu dài còn là hướng chưa đặc tả.

**Tab Word tạo/lưu mẫu DEFERRED — owner 17/10/2026:** owner tự làm sau, cần spec chi tiết trước implementation tương lai; không giao đặc tả/triển khai trong lượt này. Nguồn/bố cục, catalog/lưu và nghiệm thu chưa được chọn. Xuất Word và intake bản gốc hiện có không bị hoãn. [Decision](../../decisions/decision-owner-word-authoring-deferred-20261017.md).

<a id="address"></a>
## 7. Tra địa chỉ ngay khi nhập

Tra địa chỉ Người/Tài sản hoặc chính ô Nơi niêm yết bằng chữ đang nhập. Lookup
v2 hiện chỉ trả tên **hiện hành**, không nhận ngày giấy và không tra được tên
lịch sử tại ngày cấp; tra kho cục bộ, không gửi địa chỉ khách hàng lên website.
**Nơi cấp giấy chết** phải theo cơ quan tại ngày cấp chính giấy, không suy từ
địa chỉ người chết hoặc copy tên hiện hành làm tên lịch sử. Lịch sử chưa đủ
xác nhận thì không tự điền; đây là yêu cầu nghiệp vụ, không claim lookup v2
đã có chức năng theo ngày hoặc thêm quy trình nhập tay mới.

Máy chỉ trả kết quả để Copy; không tự sửa, nối “nay là” hoặc lưu Stage. Hơn 10 kết quả thì hỏi mở danh sách đầy đủ. Cửa sổ đầy đủ cho sửa câu tìm, bấm Tra và Copy từng dòng; đóng về đúng ô/con trỏ/vùng chọn/cuộn, không mất nháp. Đổi hồ sơ/ô/chuỗi tìm thì bỏ phản hồi cũ. Copy lỗi phải báo lỗi.

<a id="layout"></a>
## 8. Bố cục và thao tác

Tài sản bên trái, Người bên phải; phía dưới là Pool và Diagram. Tài sản dùng bảng cột, Người dùng bảng dòng; danh sách dài cuộn trang. Dialog Loại đất sửa cụm, Áp dụng chỉ về nháp, Cập nhật mới lưu. Có đường bàn phím thay kéo thả; lỗi đặt ngay ô/thẻ liên quan.

Mốc bố cục: Stage 35:65 (38:62 ở màn ≥1920), Pool nội dung 224 px (khung ngoài 240), node có người 144 px, node trống 88×24. Ô Hai bên: rộng −30%, cao +100% so với số đo thật trước thay đổi (288×26 → 202×52), JS/CSS đồng bộ; giữ đủ `p1..p30` và đường bàn phím. Màn ≤900 px xếp các vùng dọc; không thu chữ/node đến khó đọc. Canvas pan/zoom; Mở rộng là lớp phủ trong ứng dụng. Dấu chưa lưu của Stage và Diagram tách riêng. Thông báo tạm (`notice`) nằm trong khoảng trống sẵn có của thanh trên (cạnh các pill trạng thái): không đổi vị trí vùng Sơ đồ và không che drop target/điều khiển; thanh trên bám trên cùng khi vùng nội dung cuộn nên thông báo vẫn trong tầm nhìn; banner lỗi/khoá vẫn trong luồng. Thông báo dài quá một dòng được cắt bằng ellipsis nhưng luôn đọc được đầy đủ bằng bàn phím: nút nội dung (Tab tới được) mở dialog `Thông báo` của module (Esc/×/click-outside, focus trả về nút).

Yêu cầu tăng vùng sơ đồ +50% (report 802) đã chốt theo quyết định owner (`decision-owner-802-diagram-height-20261016`): tăng CHIỀU CAO vùng Sơ đồ + Pool, mục tiêu 726px tại viewport report (1920×983) từ baseline đo 484px (×1.5), không đổi chiều rộng; viewport thấp thì trang cuộn/pan, không thu chữ. Vùng Sơ đồ + Pool vì vậy có sàn chiều cao 726px; nội dung lớn hơn (ô Hai bên) vẫn cao theo quy tắc hiện có và không bị thu nhỏ — phần tăng do nội dung không tính là fix 802. Canvas vẫn là khung cuộn/pan; giữ đủ `p1..p30` và xếp dọc ≤900px.

## 9. Tiêu chí kiểm và phần chưa chốt

- Lưu/mở lại giữ đúng Người/Tài sản/quan hệ; lỗi hoặc xung đột không mất nháp, không lưu nửa chừng.
- Gỡ thẻ không xóa người; xóa Stage dọn tham chiếu đúng; reorder giữ ID và báo đổi nghĩa vị trí.
- Nhập nhiều nguồn giữ phần đã sửa, lỗi từng nguồn rõ ràng; dữ liệu mơ hồ không tự được xác nhận.
- Xuất dùng đúng bản đã lưu, không sửa nguồn hoặc ghi đè đầu ra; kiểm văn bản có trường trống và văn bản chỉ cần Stage khi triển khai định hướng mới.
- Chuyển loại hồ sơ đã lưu: Người/Tài sản giữ ID + giá trị; Diagram reset rỗng theo domain mới; buộc chọn `document_type` mới kèm xác nhận; lỗi/xung đột/khóa không đổi state/revision.
- Danh sách hồ sơ: **làm lại — DEFERRED 17/10/2026**; owner tự triển khai spec sau. Hướng trường hiển thị/search/filter là Draft chưa duyệt, chưa phải quy tắc hiện hành. [Decision](../../decisions/decision-owner-case-list-redesign-deferred-20261017.md).
- Gỡ cả nhánh Thừa kế: cảnh báo liệt kê đúng node/quan hệ trước mutation; con có parent khác vẫn gỡ, spouse không tự gỡ; Hủy/Escape/đóng không mutate/evaluate/save; xác nhận một mutation draft, lưu/mở lại giữ đúng tombstone và graph còn lại, Stage/ID/vị trí tài sản không đổi.
- Chưa chốt: tab Word tạo mẫu; phạm vi thay các điều kiện chặn hiện hành. Quy tắc tính thừa kế Draft không tự được duyệt.
- Tab Word tạo/lưu mẫu: giữ Draft, **DEFERRED 17/10/2026**, cần spec kỹ khi làm sau; không phải câu hỏi phạm vi đang chờ owner và không phải feature built.

## 10. Tra cứu chuyên sâu

[Quy tắc sơ đồ](diagram-rules.md), [Word và nguồn DOCX](word-templates.md), [bóc tách dùng chung](../shared/extraction-rules.md), [tra địa chỉ](../shared/administrative-lookup.md#lookup). Các file này bổ sung chi tiết; luồng thường dùng đã được mô tả đầy đủ ở trên.

Hai bên không chạy engine chia di sản; evaluate trả unsupported, còn xuất Word có đường hỗ trợ riêng. Không thêm nghiệp vụ mới vào web cũ; nếu cần tương thích thì gọi dịch vụ chung.

Code bắt đầu tại `shell/src/renderer/notary/` và `notary_v2/routers/cases.py`; contract giao tiếp tại `contracts/notary-case-drafting.md`. Spec quyết định hành vi, code/test chứng minh hiện trạng, không tự đổi quy tắc theo code.
