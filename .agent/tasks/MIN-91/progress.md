# Progress — MIN-91

## Trạng thái: bổ sung task migration module thứ tư; goal triển khai vẫn Todo — 2026-09-24

## Đã làm

- Tạo goal MIN-91 và 11 issue con MIN-92, MIN-102, MIN-93..101 theo chuỗi phụ thuộc contract liên repo → repo local/contract kết quả nội bộ → collector/OCR/transport/parser → dữ liệu thật → consumer → UI → cutover.
- Viết plan có quyền sở hữu, bản đồ source, file dự kiến, giao diện kỹ thuật, test lỗi, dữ liệu thật và gate nghiệm thu.
- Review source xác nhận Stage có thể được Word dùng ngay và `Property.land_rows_json` khác dữ liệu nhiều thửa; bổ sung DraftInput riêng/contract mapping.
- Owner chọn giữ gói file raw trên máy chính để soát lỗi và cho OCR bổ sung có giới hạn; plan thêm request/status theo `logical_id`, mã lỗi, quota cần duyệt, raw revision và parser chạy lại không ghi đè giá trị đã duyệt.
- Phân MIN-92 cho contract liên repo, MIN-102 cho result/DraftInput/fingerprint/nhiều thửa nội bộ. Thêm listener gap, sự kiện nguồn nếu adapter hỗ trợ và hạn giữ raw sau ACK làm gate trước dữ liệu thật.

## Chưa triển khai

- Chưa có code hoặc repo Zalo mới; các task implementation chờ MIN-92. Số quota OCR và TTL raw sau ACK là đề xuất trong draft, MIN-92 phải duyệt trước ảnh thật. Fallback khi bot không bắt được sự kiện thuộc MIN-90.

## Bổ sung 24/09 — module thứ tư

- Tạo đúng một issue con mới [MIN-103](https://linear.app/minhnotary/issue/MIN-103) để chuyển Zalo-owned connector/session/listener/media/Qwen primitives/tests và tài liệu producer vào repo Zalo riêng cùng snapshot `zalo/` trong monorepo. Repo và folder đều là đích dự kiến, chưa tạo; repo nguồn chính và manifest phải được chốt khi thực thi. Parser Document Intake vẫn tại notary.
- Thu hẹp MIN-93 còn scaffold/entrypoints/config; chuyển dependency MIN-94/95/97 từ MIN-93 sang MIN-103. MIN-92→93→103→94/95/97; MIN-92→102→96; cả bốn task 94/95/96/97→98→99→100→101. Chỉ MIN-101 cutover/gỡ code legacy.
- Phân retention: MIN-92 chốt raw bot sau ACK; MIN-102 chốt folder imported/raw máy chính đủ để tra lỗi, MIN-99 thực hiện. Bảng chuyển trạng thái/fixture/validator thuần thuộc contract; test runtime crash/ACK/cleanup thuộc MIN-97/99. Chưa nhận các đề xuất Claude về transcript/quota/auto/manual/gộp variant là quyết định đã duyệt.
- Plan bỏ yêu cầu skill/model cứng và nói rõ checkbox chỉ để review; trạng thái thật ở Linear, tiến độ ở `.agent/tasks`. MIN-98 thêm thí nghiệm `enable_rotate=true` lượt mặc định, không đổi production.
- Kiểm mới trên file plan: 26 liên kết Markdown, 0 đường nội bộ thiếu; 0 dòng thừa khoảng trắng; đúng một heading MIN-103; không còn `REQUIRED SUB-SKILL`. Đọc lại graph Linear của cả 12 issue con: parent đều MIN-91, blockers khớp chuỗi trên. Đây là check tài liệu, không phải test runtime.

## Bổ sung 24/09 — raw OCR có vị trí dòng

- Đọc code hiện hành: `notary_v2/routers/ocr_ai.py:405` gọi `text_recognition`; `:346–374` chỉ rút chữ thành `list[str]`, `:440–451` trả danh sách dòng. Ảnh được EXIF transpose/resize ở `:322–343`; crop chân GCN ở `:1624–1647`; retry rotate/footer ở `:2497–2565` nhưng không giữ tọa độ/khung/pass. Chưa có bằng chứng runtime hiện giữ geometry.
- Tài liệu Alibaba chính thức xác nhận `advanced_recognition` trả `ocr_result.words_info[]` gồm text, `location` 8 tọa độ và `rotate_rect`; chưa nói rõ mapping sau min/max_pixels, enable_rotate và các phép biến đổi ảnh phía client. Đã nâng đây thành khả năng raw mục tiêu trong plan; MIN-92 chốt schema/frame/status, MIN-95 adapter có cấu trúc, MIN-96 dùng bố cục trong notary, MIN-98 so chất lượng/độ đúng tọa độ trước quyết định bật mặc định. Text-only vẫn được hỗ trợ và geometry thiếu có trạng thái rõ.
- Cập nhật mô tả Linear MIN-89/91/92/95/96/98/99/102, không tạo task mới, không đổi graph. Không gọi Qwen live, không đổi code hoặc default production. Các câu hỏi trước về transcript/quota/auto/manual/gộp variant vẫn mở.

## Bước tiếp theo của goal triển khai

- MIN-92 chốt và publish contract liên repo; MIN-93 tạo scaffold repo local, MIN-103 chuyển baseline và tài liệu producer. MIN-102 chốt contract kết quả/retention máy chính trước MIN-96/99. Các task còn lại tuân dependency trên Linear.

## Check đã chạy

- Đã kiểm chứng source bằng đọc file/rg; review độc lập phát hiện hai lỗi mapping đã được sửa.
- Sau khi dọn SOT, kiểm 28 Markdown đang đổi, 132 link nội bộ, 6 JSON ví dụ, CAP-01..16/T01..24: 0 lỗi; `git diff --check` exit 0. Linear xác nhận 11 issue con thuộc MIN-91 và quan hệ blockedBy đúng plan.

## Kiểm cuối sau bổ sung geometry

- Sửa lời khẳng định quá mạnh về khung tọa độ: giữ nguyên số provider và metadata ảnh gửi, nhưng đánh dấu phép ánh xạ chưa xác minh cho tới khi MIN-95/98 kiểm overlay với ảnh có mốc. Cập nhật cùng nội dung ở Linear MIN-92/MIN-95.
- Giữ việc chọn khóa quota OCR bổ sung `attachment` hay từng trang là quyết định mở của MIN-92; plan, draft và task không còn ngầm chọn attachment. Sửa chỉ mục `contracts/README.md` từng ghi sai rằng thư mục chỉ có một file.
- Kiểm lại 31 Markdown thay đổi/chưa theo dõi, 162 liên kết local, 8 khối JSON và 42 khối code: 0 lỗi; CAP-01..16, T01..24 và 12 task đúng thứ tự; `git diff --check` exit 0, chỉ có cảnh báo LF/CRLF của Windows.
