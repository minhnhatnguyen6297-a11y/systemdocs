# Stage, Cập nhật toàn cục, Pool và Diagram

Chương của [SPEC notary_v2](../../SPEC.md); cập nhật 17/09/2026.
Sửa hành vi Stage/Pool và lan truyền tại **file này**, không tại workflow thừa kế
hay bản Stage có ngày trong superpowers. Đây là đặc tả sản phẩm, không phải
contract API tích hợp mới.

Trạng thái: yêu cầu đích theo quyết định mới của chủ dự án và phần hành vi
Stage → Diagram đã bàn trước. **Code chưa được nghiệm thu toàn bộ**; xem
[SPEC §7](../../SPEC.md#7-yêu-cầu-đích-so-với-code-và-câu-hỏi-còn-mở).

## 1. Ba lớp dữ liệu

| Lớp | Mục đích | Ai được sửa |
|---|---|---|
| Ảnh/kết quả OCR gốc | Đối chiếu nguồn; không phải dữ liệu đã duyệt | Không sửa nội dung gốc qua UI OCR |
| Stage nháp | Dữ liệu cùng định dạng từ nhiều nguồn | Người dùng sửa tại Stage |
| Stage đã cập nhật | Dữ liệu đã được người dùng duyệt cho các phần phụ thuộc | Chỉ thay bằng Cập nhật toàn cục thành công |

Sửa Stage không ghi đè raw OCR. “Stage là SOT” là nói về dữ liệu nhập đã duyệt;
quan hệ, gán người và lựa chọn nghiệp vụ vẫn thuộc Diagram.

## 2. Bố trí và tiếp nhận

- Stage Người: mỗi người một hàng.
- Stage Tài sản: **mỗi tài sản một cột**, dù cùng sổ hay khác sổ.
- Stage các loại giấy tờ vẫn tách biệt dù sau này dùng một cửa sổ OCR chung.
- OCR, Excel, nhập tay, tìm/chọn dữ liệu đã có và Zalo đi về Stage phù hợp.
  Đưa vào Stage là tạo nháp, chưa phải duyệt hoặc ghi dữ liệu nghiệp vụ.
- Mọi nguồn dùng cùng quy tắc dữ liệu, không dành cho Zalo một đường sửa/duyệt riêng.
- Chuẩn hóa hình thức không có nghĩa tự đoán tên, tự sửa số giấy tờ, tự điền dữ
  liệu thiếu hoặc tự gộp người/tài sản. Dữ liệu trùng phải để người dùng kiểm tra.
- Một người liên kết bằng mã ổn định, không bằng số CCCD, tên hay thứ tự hàng.
  Giữ mã khi sửa thông tin để các gán trên sơ đồ không bị đứt.
- Với Stage Người, chỉ nút xóa cuối hàng được bỏ người khỏi bản nháp; chưa
  Cập nhật thì bản đã duyệt chưa đổi. Nút OCR, Pool và Diagram không được
  xóa hàng Stage thay người dùng.

## 3. Cập nhật là một hành động toàn cục

**Chủ dự án chốt ngày 17/09/2026:**
- Chỉ có Cập nhật toàn cục đối với dữ liệu Stage trong vùng làm việc hiện tại.
- Bao gồm **Người + Tài sản + giấy tờ khác** đang có, không chỉ CCCD.
- Không cập nhật từng hàng, từng người, từng tài sản hay từng loại giấy tờ riêng lẻ.
- Có dòng/cột lỗi: yêu cầu sửa đúng chỗ lỗi rồi mới được cập nhật.
- “Toàn cục” không có nghĩa sửa mọi hồ sơ trong DB hay mọi lô Zalo đang tồn tại.

Trình tự quan sát được:
1. Giữ bản nháp hiện tại, kiểm tra toàn bộ vùng Stage. Chưa ghi gì.
2. Nếu có lỗi: nêu dòng/cột/trường và lý do; giữ nguyên nháp, cache và bản đã
   duyệt. Không lưu phần đúng trước rồi bỏ qua phần lỗi.
3. Tính ảnh hưởng lên Diagram và các kết quả; hỏi xác nhận khi làm mất gán (§5).
4. Người dùng đồng ý: thực hiện một lần cập nhật toàn bộ.
5. Chỉ sau khi lưu thành công, công bố bản đã duyệt và cập nhật các phần phụ thuộc.
6. Dọn dữ liệu OCR tạm tương ứng đã được duyệt. Không xóa ảnh nguồn Zalo, lô
   không liên quan hoặc dữ liệu chưa nằm trong lần cập nhật.

Nếu bất kỳ phần lưu nào thất bại, không được để nghiệp vụ ở trạng thái lưu nửa
chừng. Giữ nháp để sửa/thử lại, không báo thành công và không dọn cache.
Rollback giao diện đơn thuần không chứng minh DB đã rollback.
Tài liệu này chốt kết quả tất-cả-hoặc-không; thiết kế giao dịch/API là task riêng.

Lưu hồ sơ, lưu Diagram, xuất Word/Excel/JSON không phải đường tắt cập nhật một
phần Stage. Việc giấy tờ khác chưa triển khai không được hiểu là phải có các
loại giấy tờ đó mới được cập nhật; chỉ kiểm các vùng đang có dữ liệu.

## 4. Đang sửa dở và thao tác ở vùng khác

Phần này tiếp nhận hành vi D8 trong thảo luận Stage ngày 18/08, không tự thêm
một lần lưu riêng cho từng hàng.

Khi Stage có nháp mà người dùng kéo thả, bỏ gán, đổi Chủ đất/Nhận, đổi tài sản
hoặc lưu hồ sơ, yêu cầu chọn:
- **Cập nhật**: chạy cập nhật toàn cục; chỉ tiếp tục thao tác khi thành công.
- **Hủy thay đổi**: bỏ nháp về bản đã duyệt, rồi tiếp tục thao tác.

Không tự chọn hộ; không dùng thao tác Diagram để dựng lại Stage từ bản cũ làm
mất nháp. Chưa chọn thì thao tác chờ, không được tiếp tục ngầm.
Việc hủy nháp không đồng nghĩa lệnh xóa ảnh nguồn hoặc toàn bộ cache OCR.

## 5. Ảnh hưởng Stage → Diagram đã được bàn trước

Nguồn truy nguyên: [thảo luận Stage 18/08 — D8, D9, D12](../../superpowers/specs/2026-08-18-stage-sot-sync-model.md).
Bản cũ là lịch sử, file này sở hữu hành vi hiện hành.

### 5.1 Sửa thông tin

Sau Cập nhật thành công:
- Tên, ngày sinh/chết, giấy tờ và dữ liệu hiển thị của cùng mã người đổi ở Pool
  và thẻ Diagram, không tạo người mới hoặc mất gán chỉ vì sửa CCCD.
- Sửa ngày sinh/chết có thể đổi vòng di sản, ô cần điền, phần nhận và cảnh báo.
  Tính lại kết quả, phần chưa phân chia và trạng thái xử lý; ô có thể xuất hiện
  hoặc không còn hợp lệ. Nếu gây bỏ gán phải cho biết người/nhánh bị ảnh hưởng
  trước khi chốt; node đã có dữ liệu không được âm thầm biến mất.
- Không được chỉ cập nhật chữ trên thẻ trong khi kết quả tính, danh sách người
  tham gia và lần xem trước/xuất tiếp theo vẫn đọc dữ liệu cũ.

Chuỗi phụ thuộc:
Stage đã duyệt → Pool/Diagram → đầu vào tính toán → kết quả/phần chưa phân chia/
cảnh báo/trạng thái → dữ liệu người tham gia → xem trước, danh sách hồ sơ và
lần xuất Word tiếp theo.

Đây là yêu cầu đồng bộ, không phê duyệt thuật toán thừa kế còn nháp.
Không tự sửa file Word đã tải hoặc mở bên ngoài; người dùng xuất lại.

### 5.2 Xóa người và ảnh hưởng hết nhánh

Phân biệt:
- Xóa hàng tại Stage: bỏ người khỏi hồ sơ sau Cập nhật, không ngầm xóa người khỏi kho.
- Bỏ gán tại Diagram: gỡ người khỏi vị trí trên sơ đồ, không xóa người ở Stage.

Ví dụ A → B → C, và C còn nhánh con:
1. Người dùng xóa B ở Stage rồi bấm Cập nhật.
2. Tính đầy đủ những gán của B, C và các nhánh phía dưới bị ảnh hưởng.
3. Hiện danh sách: ai bị bỏ khỏi Stage; ai chỉ bị bỏ gán và về Pool; ô cấu trúc
   nào bị dọn. Không chỉ báo chung “có ảnh hưởng”.
4. Người dùng hủy xác nhận: bản đã duyệt không đổi, nháp vừa sửa vẫn còn.
5. Đồng ý và lưu thành công: dọn gán/references không còn hợp lệ. C và những
   người vẫn thuộc Stage trở về Pool, không bị xóa theo B.
6. Ô cấu trúc không mang người có thể được dọn theo danh sách đã xác nhận;
   node có dữ liệu không được âm thầm biến mất, ô cần giữ thì bỏ gán thay vì xóa ô.
7. Tính lại toàn bộ phần phụ thuộc. Lưu thất bại thì giữ nguyên bản đã duyệt và nháp.

Không được giữ tham chiếu cũ rồi từ chối mọi lần cập nhật chỉ vì người dùng đã
xóa người ở Stage. Không được cascade theo chiều Diagram → xóa dữ liệu Stage.

### 5.3 Tài sản và giấy tờ khác

Cùng lần cập nhật toàn cục phải lan truyền thông tin đã đổi tới nơi sử dụng
tài sản/giấy tờ đó và lần xem trước/xuất tiếp theo.
Không tự gán người nhận riêng cho từng tài sản hoặc suy quan hệ gia đình từ giấy
khai sinh/kết hôn chỉ vì đã đọc OCR. Mô hình gán đa tài sản và giấy tờ khác còn
phải chi tiết hóa trước triển khai; không áp thuật toán cascade người một cách máy móc.

## 6. Pool và dữ liệu riêng của Diagram

Pool = người trong Stage đã duyệt chưa được gán trên Diagram.
Mỗi người hiển thị một thẻ; Pool là cách trình bày dữ liệu, không giữ bản để sửa riêng.

| Thao tác | Pool | Stage |
|---|---|---|
| Cập nhật thêm người | Có thẻ nếu chưa được gán | Có người đã duyệt |
| Kéo vào Diagram | Ẩn thẻ đang gán | Không đổi |
| Bỏ gán Diagram | Trở về nếu còn trong Stage | Không đổi |
| Xóa người ở Stage và Cập nhật | Không còn thẻ người đó | Bỏ khỏi hồ sơ |
| Bỏ gán cả nhánh | Người còn trong Stage trở về | Không xóa người theo nhánh |

Diagram giữ quan hệ, vị trí gán, dữ liệu cấu trúc và lựa chọn nghiệp vụ. Không
sửa tên/ngày/CCCD riêng trên Diagram. Sửa quan hệ hay lựa chọn thì tính lại phần
phụ thuộc gồm tỷ lệ, phần chưa phân chia, trạng thái, người tham gia, xem trước,
danh sách hồ sơ và lần xuất Word tiếp theo; không ghi ngược vào dữ liệu nhập ở Stage.

Ý nghĩa Chủ đất/Người nhận/Người không nhận phục vụ văn bản nằm ở
[Word §2](../../domains/inheritance/word-export.md#2-nguồn-dữ-liệu-và-thẩm-quyền).
Quy tắc chia và UX còn nháp tại chương thừa kế; không tự hợp thức hóa vì file này được cập nhật.

## 7. Kiểm tra đạt yêu cầu bằng thao tác

Các ca sau là tiêu chí đích, **chưa báo đã chạy/passing**:
1. Nhập từ OCR/Excel/tay/Zalo: sửa cùng loại dữ liệu ở đúng vùng Stage.
2. Một người sai hoặc một tài sản sai: không vùng nào được cập nhật.
3. Mọi vùng hợp lệ nhưng lưu một phần lỗi: không có dữ liệu nghiệp vụ ghi dở;
   nháp và cache còn nguyên.
4. Thành công: mọi vùng được duyệt, dữ liệu phụ thuộc đổi, chỉ cache liên quan được dọn.
5. Sửa CCCD/tên rồi cập nhật: giữ đúng người trên Diagram.
6. Sửa ngày chết gây đổi nhánh: thấy ảnh hưởng; hủy không mất nháp hoặc gán.
7. Xóa B trong A → B → C → D: xác nhận liệt kê hết; C/D còn Stage thì về Pool.
8. Bỏ gán C trên Diagram: không xóa C khỏi Stage.
9. Stage có nháp rồi kéo thẻ: buộc xử lý nháp trước; cập nhật lỗi không kéo tiếp.
10. Đóng/mở OCR: ảnh/kết quả tạm còn; không tự duyệt.
11. Hai tài sản cùng serial nhưng khác thửa: không bị từ chối chỉ vì trùng serial.
12. Sau cập nhật, xem trước/xuất lại dùng dữ liệu mới; file đã tải không tự đổi.
13. Chạy chuỗi thêm → sửa → gán → bỏ gán → xóa → cập nhật → lưu/mở lại nhiều lần:
    không mất người, không còn tham chiếu mồ côi, không tô lỗi toàn Stage vô cớ.

## 8. Còn mở và ranh giới triển khai

- Bản thảo cũ chứa các lựa chọn chưa được duyệt: một map React, đổi endpoint,
  số phiên bản chống ghi đè, bỏ cờ nội bộ. Không sao chép thành contract kỹ thuật đã duyệt.
- Bộ trường và validation chi tiết cho Tài sản/giấy tờ khác; ngày chỉ có năm
  và chính sách trùng người cần đối chiếu trước khi đổi code.
- Sửa người/tài sản dùng chung nhiều hồ sơ; phạm vi ảnh hưởng ngoài hồ sơ hiện tại.
- Khôi phục nháp qua reload/đóng app, thời hạn cache; không hứa bền vững chỉ vì modal đóng không mất.
- Chuỗi thao tác Diagram user báo gãy chưa có tái hiện mới; không dùng chẩn đoán
  từ nhánh cũ như bằng chứng nguyên nhân hiện tại.
