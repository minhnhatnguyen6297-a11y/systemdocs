# Tool test trích xuất văn bản (cho nhân viên)

Tool này để mở file Word hợp đồng / thừa kế rồi xem máy bóc được
đúng người và tài sản không. **Không cần chọn loại văn bản** —
máy tự nhận diện (phân chia, từ chối, khai nhận di sản,
chuyển nhượng, tặng cho, thế chấp...).

## Nhân viên dùng (3 bước)

1. Nhấn đúp file **`run.bat`**.
   Lần đầu nó tự cài thêm phần mềm (cần mạng, chờ vài phút).
   Các lần sau mở lên ngay.
2. Test:
   - **Test 1 file**: bấm `Chọn file Word...`, xem các bảng
     Người / Người đã chết / Thửa đất / Sổ tiết kiệm / Bảo hiểm.
     Ô nào **nền vàng** là máy chưa bóc được, nhớ để ý.
     Cần copy giá trị nào thì **bấm chuột phải đúng ô đó**
     rồi chọn `Copy ô`.
   - **Test cả thư mục**: bấm `Chọn thư mục...` rồi `Chạy tất cả`
     để test hàng loạt. **Không cần phân loại trước** — thư mục
     lẫn nhiều loại văn bản vẫn được: máy tự nhận diện loại từng
     file, file lỗi không làm dừng cả đợt, có thanh tiến trình và
     nút `Dừng`. Xong sẽ báo số lượng từng loại
     (phân chia/từ chối/chuyển nhượng...) + số file lỗi/cảnh báo;
     mỗi dòng ghi mã kiểm tra (R00..R13, bỏ qua R11 đã xóa) để tra cứu.
   - Mỗi lần chạy máy **tự ghi vào file log**, không cần làm gì thêm.
3. Gửi log: mở tab **Xem log** → bấm **Mở thư mục chứa log** →
   copy file `ket-qua-test.jsonl` gửi cho chủ.
   (File log nằm ở `Documents\KetQuaTestRegex`, xóa folder tool
   cũng không mất.)

## Nhận bản cập nhật

Mỗi bản mới là **nguyên cả folder** (tên có ngày + phiên bản).
Xóa folder cũ đi, giải nén folder mới, nhấn đúp `run.bat` như cũ.
Không phải cài lại gì thêm (trừ khi được dặn riêng).

## Cho chủ / người sửa code

- File `mo-phong-may-trang.bat`: giả lập máy chưa cài Python
  (chạy `run.bat` như trên máy trắng) để kiểm tra nhanh đường
  cài đặt. Chỉ dùng để test, nhân viên không cần.
- Engine: `extract_contract.py` ngay trong `tool/` (bản chụp từ
  `upload_lab`, có `ENGINE_VERSION`). Mỗi dòng log đóng dấu phiên bản engine.
- Đổi engine: copy file mới ghi đè `extract_contract.py` +
  `kiem_tra_trich_xuat.py`, tăng `ENGINE_VERSION` (ví dụ ngày + tên vòng).
- Đọc log: tab **Xem log** trong tool (lọc theo loại văn bản,
  ô thiếu tô vàng) hoặc đọc trực tiếp file `.jsonl`
  (1 dòng = 1 file đã test).
- Test tự động: `python -B -X utf8 -m pytest tests/ -q -p no:cacheprovider`
  trong folder này; đây là lệnh chuẩn, thu cả hàm test và lớp unittest.
  `tests/fixtures/word_field_cases.json` giữ đáp án Closed và đầu vào Pending;
  Pending chưa có đáp án được duyệt nên không tính đạt.
- Log chứa họ tên + CCCD thật: chỉ lưu máy nội bộ, gửi trực
  tiếp cho nhau, không đăng lên mạng.
