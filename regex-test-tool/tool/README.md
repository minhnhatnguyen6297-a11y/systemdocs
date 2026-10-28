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
- Lõi luật (engine): một đường luật duy nhất trong repo —
  `tools/regex_workbench/engine/contract_extract.py` (danh tính
  `contract_word` + `ENGINE_VERSION` của lõi). Tool **không giữ bản luật
  riêng**: nó gọi lõi chung qua consumer `upload_lab/extraction_adapter.py`
  (đọc file Word + gọi lõi + giữ shape payload), rồi kiểm tra payload bằng
  `upload_lab/kiem_tra_trich_xuat.py`. Mỗi dòng log đóng dấu
  `ENGINE_VERSION` của lõi — cả repo dùng đúng một danh tính engine.
- Đóng gói bản cho nhân viên: chạy `build_release.ps1` (trong
  `regex-test-tool/`). Script gom đúng 3 nguồn vào `tool/vendor/`:
  `vendor/tools/regex_workbench/engine/**`,
  `vendor/upload_lab/extraction_adapter.py`,
  `vendor/upload_lab/kiem_tra_trich_xuat.py`; thiếu nguồn là báo lỗi ngay.
  Khi có `tool/vendor/`, tool tự ưu tiên bản này.
  `tool/vendor/` là artifact build (đã gitignore), **không commit**.
- Chạy trong repo (dev/test): không có `tool/vendor/` thì tool tự trỏ về
  `tools/` + `upload_lab/` của repo (đường đi từ `regex-test-tool/tool/`).
- Sửa luật: sửa ở lõi `tools/regex_workbench/engine/contract_extract.py`,
  tăng `ENGINE_VERSION` trong lõi, rồi chạy lại `build_release.ps1`
  trước khi phát hành. Không copy file luật vào tool.
- Đọc log: tab **Xem log** trong tool (lọc theo loại văn bản,
  ô thiếu tô vàng) hoặc đọc trực tiếp file `.jsonl`
  (1 dòng = 1 file đã test).
- Test tự động: `python -B -X utf8 -m pytest tests/ -q -p no:cacheprovider`
  trong folder `tool/` này (chạy từ đây để `ket_qua_log` import được).
  Test ở đây kiểm tra phần tool (log/kết quả); test giữ hành vi lõi luật
  và bộ đáp án Word (`tests/fixtures/word_field_cases.json`) nằm ở bộ
  chuẩn `upload_lab/tests/` — tool không giữ bản chép.
- Log chứa họ tên + CCCD thật: chỉ lưu máy nội bộ, gửi trực
  tiếp cho nhau, không đăng lên mạng.
