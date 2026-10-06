# Task 5 — regex hợp đồng Word (task5-regex-hop-dong-word)

## brief.md
Xây core regex dùng chung trích xuất Người + Tài sản từ Word công
chứng, làm từng loại văn bản, mỗi vòng có báo cáo. Bắt đầu từ thừa kế.

## progress.md (06/10/2026)
- Xong loại thừa kế (v1): phân chia / từ chối / khai nhận di sản;
  tài sản đất (từng thửa + `land_rows` shape DB), sổ tiết kiệm /
  tài khoản / thẻ, bảo hiểm; người sống / chết / lời chứng.
- Engine `upload_lab/extract_contract.py` (`ENGINE_VERSION
  2026-10-06-thuake5`); luật kiểm tra `kiem_tra_trich_xuat.py`
  (R00–R11); quét chuẩn `tools/quet_kiem_tra.py`.
- Quét 50 bản đầu ở `D`: 31 sạch, 11 loại đúng (không phải văn bản),
  8 gắn cờ người kiểm (3 vênh diện tích trong văn bản, 5 lời chứng
  thiếu người ký).
- Repo test cho nhân viên: `regex-test-tool/` (Test 1 file + Test cả
  thư mục + Xem log, log cố định ngoài folder, copy snapshot engine).
- Test: 84 (upload_lab) + 7 (regex-test-tool) xanh.
- Spec: `docs/spec/upload_lab/regex-core.md` (SOT cách làm),
  `regex-thua-ke.md` (SOT chi tiết thừa kế v1),
  `regex-rules.md` (catalog tra nhanh).

## decisions.md
- 05/10: tách thửa; số công chứng ra khỏi core; core không so sánh.
- 06/10: năm sinh giữ `YYYY` + cờ; copy chuột phải/ngay + nút dòng;
  quét không cần phân loại trước; diện tích tuyệt đối chính xác;
  `loai_dat` giữ chữ gốc; luật trong code là chuẩn duy nhất.
- Xem đầy đủ ở `docs/spec/upload_lab/regex-core.md` §7.

## Code Review

### 2026-10-06 17:30
Code review: 7 decision-needed, 13 patch, 6 defer, 13 rejected
(4 lens: blind-hunter, edge-case-hunter, verification-gap, intent-alignment;
đối chiếu regex-core.md + regex-thua-ke.md + regex-rules.md).

- [ ] [Review][Decision] Định dạng số diện tích — `_so_thuc`/`_so_thuc_dien_tich` coi "1.234" là 1,234 (VN thường là 1234 m²) và "1.234,5" trả None → R10 bỏ qua, land_rows sai giá trị
- [ ] [Review][Decision] Tài sản hỗn hợp — `_find_tai_san_by_kind` chỉ lấy 1 khối; sổ tiết kiệm/bảo hiểm nằm TRƯỚC khối đất bị mất im lặng (R09 không bắn vì đã có thửa)
- [ ] [Review][Decision] Giới tính mặc định "Ông" khi tên không có "Thị" (`Ông/bà:`, tên trần) — trái nguyên tắc "thiếu căn cứ để trống + gắn cờ"
- [ ] [Review][Decision] R11 không gắn cờ khi lời chứng parse ra 0 người (`n_chung and ...`)
- [ ] [Review][Decision] Validator chỉ phủ thừa kế; văn bản chuyển nhượng/tặng cho... hiện "đủ" trong tool nhân viên dù không luật nào kiểm
- [ ] [Review][Decision] Bản copy engine + luật (+ 2 GUI) giữa upload_lab và regex-test-tool không có cơ chế giữ đồng bộ (script copy hay test so hash)
- [ ] [Review][Decision] Tên người thật (Xương, Bùi Văn Tài, bà Luyến, ông Kính bà Tới) nằm trong đường dẫn test; repo có remote GitHub

- [ ] [Review][Patch] R00/R01 không bỏ dấu tên file → danh sách bỏ qua chết với tên tiếng Việt có dấu; "pc" bắt nhầm [upload_lab/kiem_tra_trich_xuat.py:70-105 + bản copy]
- [ ] [Review][Patch] run.bat: tìm thấy `python` (không có `py`) vẫn chạy `py -3`; đường dẫn Python có dấu cách vỡ; dòng 38 lặp [regex-test-tool/tool/run.bat:18-23,38,43,68]
- [ ] [Review][Patch] Tab Xem log: dấu (!) không hiện cho bản ghi có cờ R (tom_tat trả "CỜ:" chứ không "THIẾU") [regex-test-tool/tool/regex_test_tool.py:545]
- [ ] [Review][Patch] `_extract_nguoi_chet` cửa sổ 400 ký tự lấn sang người chết kế tiếp → gán nhầm trích lục/địa chỉ cuối [upload_lab/extract_contract.py:2267]
- [ ] [Review][Patch] `quet_kiem_tra.json` mặc định ghi ra thư mục đang đứng, không bị gitignore, chứa tên/CCCD [upload_lab/tools/quet_kiem_tra.py:95]
- [ ] [Review][Patch] Thiếu test cho `_normalize_plain_text_for_extract` / nhánh `.doc` [upload_lab/extract_contract.py:311]
- [ ] [Review][Patch] Lọc người chết trong khối đương sự dùng `chet ngay` không cần ngày (trái comment + catalog) [upload_lab/extract_contract.py:2021]
- [ ] [Review][Patch] Bảo hiểm so khớp phân biệt hoa thường ("BẢO HIỂM" bị bỏ) [upload_lab/extract_contract.py:809]
- [ ] [Review][Patch] Sổ tiết kiệm "của Ngân hàng X" không lấy được ngân hàng (fallback chỉ có ở nhánh tài khoản) [upload_lab/extract_contract.py:974]
- [ ] [Review][Patch] Nút "Chạy tất cả" không khóa khi đang chạy → chạy lồng [regex-test-tool/tool/regex_test_tool.py:396]
- [ ] [Review][Patch] Tài liệu lỗi thời: README `engine/`, docstring chay-test.bat/cai-dat.bat/logs, ket_qua_log docstring, R10 "1m2" [regex-test-tool/tool/README.md, regex_test_tool.py:1-7, ket_qua_log.py:3, kiem_tra_trich_xuat.py:192]
- [ ] [Review][Patch] Log cắt `tai_san` 3000 ký tự [regex-test-tool/tool/ket_qua_log.py:70]
- [ ] [Review][Patch] `import os` thừa [upload_lab/tests/test_upload_lab_extract_contract.py:3]

- [x] [Review][Defer] Test file thật chỉ chạy trên máy owner (skip nơi khác) — deferred: suite tổng hợp đã phủ cùng nhánh code ở quy mô nhỏ
- [x] [Review][Defer] TAB→" | " có thể lọt vào dia_chi/mo_ta của .doc [extract_contract.py:317] — deferred: maybe-false; chạy 1 .doc mẫu xem dia_chi có "|"
- [x] [Review][Defer] `_tach_thua_bang_don_dong` chỉ bắt 1 thửa [extract_contract.py:1379] — deferred: maybe-false; cần .doc bảng dồn ≥2 thửa
- [x] [Review][Defer] Tách dòng bảo hiểm/sổ tiết kiệm có thể sai ("CCCD số" mở quyền lợi mới; tài khoản chưa có STK gộp vào sổ) — deferred: maybe-false; cần mẫu thật
- [x] [Review][Defer] regex-rules.md §0 trùng bảng file với regex-core.md §6 (2 chỉ mục song song) — deferred: sửa spec
- [x] [Review][Defer] progress.md gộp brief/decisions thay vì file riêng — deferred: file agent-context

Rejected: ban_ghi_thanh_payload thiếu document_kind (false — không nơi nào chạy lại luật trên log);
ImportError thiếu engine trong regex-test-tool (false — file có, trùng byte); os.startfile ngoài Windows
(low, tool chỉ Windows); installer không checksum (low, HTTPS python.org); read_word_comments range
không đóng (low, tool dev); pytest __import__ (low); fallback logs/ trong folder (low, hiếm, đã ghi
docstring); tom_tat thiếu đếm STK/BH (low, ô vàng vẫn hiện); bảng batch 6 giá trị/5 cột (low);
người chết "Cụ"/"chết vào ngày" (low, R06 đã gắn cờ); _doi_ngay_excel khoảng serial (low, chủ ý);
serial GCN <6 số / CMND 8 số (low, hiếm); R01 chấp nhận refusal cho tên "phân chia" (low).
