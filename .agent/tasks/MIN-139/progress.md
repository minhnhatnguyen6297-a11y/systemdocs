# Progress — MIN-139

## Trạng thái: triển khai cục bộ, chờ root review — 2026-10-04

Owner đã duyệt Word-first theo các comment NAIA-4 ghi trong brief/decisions.
Lịch sử ngày 29/09 phía dưới là đề xuất cũ, không còn trạng thái triển khai hiện tại.

## Đã triển khai

- Đọc Word theo thứ tự đoạn/bảng, dùng chung lõi regex và giữ bằng chứng từng vị trí.
- Review người/tài sản, sửa trường và dòng loại đất, chọn bằng chứng; tải JSON cục bộ.
- Lưu file gốc, mã nguồn, dòng đã nhận và vị trí xác nhận cùng Stage; mở lại vẫn còn.
- Tạo bản mẫu riêng và xuất theo giá trị đã lưu, giữ phần Word không được chọn.
- Đối chiếu mã băm (dấu nhận dạng file), thứ tự người/tài sản, revision; từ chối nguồn/vị trí sai.
- Đồng bộ spec và schema tại feature hiện có; Upload vẫn hai tab.

## Kiểm chứng đã chạy

### Re-derivation iteration 2 — 04/10/2026

- Giữ đủ diện tích `1.234,5` trong bằng chứng và khi xuất; dùng profile 1.1.1.
- Ngày sửa sai chặn nhận vào Stage và hiện lỗi cho tới khi sửa đúng; không lấy ngày cũ.
- Gỡ nguồn khóa trong lúc lưu; bảng chọn vị trí vẫn còn sau khi lưu.
- Số dòng nguồn có thể lớn hơn 20; lưu/mở lại vẫn giữ đúng dòng 21 trong
  danh sách tối đa 20 dòng Stage. Schema cho proposal không hỗ trợ có slot rỗng,
  nhưng proposal hỗ trợ và binding đã lưu vẫn cần slot thật.
- Kiểm cấu trúc mỗi rule đất trước lint; giữ trạng thái trường Word lồng nhau
  qua nhiều đoạn và chặn mọi chữ kết quả trong trường. Kiểm byte bằng chứng
  bằng `extraction.sha256`, từ chối dấu kiểm thiếu/hỏng hoặc nội dung bị đổi.
- Bằng chứng từng ô đất có profile/version/candidate state. Nguồn/mẫu chưa
  dùng giữ local; chưa duyệt dọn tự động hoặc thời hạn giữ.
- 19/19 Python DOCX, 280/280 regression Intake/Workspace/Word ở đúng cwd
  `notary_v2`; 86/86 sidecar adapter/Intake; 221/221 Node; 38/38 shared-core;
  78 ví dụ contract với 0 kết quả ngoài dự kiến. DOCX đã chạy lại sau khi sửa
  test đọc output_file.path; các regression khác đã qua trong cùng bộ kiểm.
- Root chạy lại Electron thật trên code iteration 2: nhập/sửa/lưu Stage/sơ đồ/
  tải lại/25 vị trí/xuất thành công. Báo cáo và giới hạn native picker ở dưới.
- Lần gọi regression đầu từ root cwd không tìm được mẫu Word tương đối;
  gọi lại trong `notary_v2` đã giải quyết. Cảnh báo datetime adapter Python là cũ.

### Re-derivation sau root review — 04/10/2026

- Giữ danh tính dòng đất từ review đến Stage/reload; xóa dòng đầu không gắn
  nhầm bằng chứng/vị trí sang dòng kế. Mỗi ô đất mơ hồ phải được duyệt riêng.
- Ngày chọn từ evidence đổi về dạng ngày chuẩn; slot trống/không hỗ trợ và
  span nhiều kiểu chữ bị chặn, có lý do. Run gốc và phần chưa chọn giữ nguyên.
- Checkbox mở lại đúng vị trí đã lưu; bỏ chọn hết và lưu được. Lựa chọn chưa
  lưu khóa xuất. Tên nguồn do backend tạo; nguồn thứ 9 bị chặn trước Stage;
  gỡ nguồn hỏng được mà không đọc file ấy, dữ liệu Stage vẫn còn.
- Binding mới được kiểm slot/giá trị trên snapshot vừa dựng trong transaction;
  sai slot hủy cả dữ liệu/revision. Kết quả xuất thư mục con trả đích cha đã chọn.
- 13 Python DOCX tests; 355 regression Intake/Workspace/Word; 80 sidecar adapter
  tests gồm full DOCX hai bên nhập→lưu→mở lại→xuất, stale export không tạo file;
  218 Node tests; 43 shared-regex/sidecar Intake tests; 78 contract examples
  không có kết quả ngoài dự kiến. Python datetime adapter vẫn có cảnh báo cũ.
- Lệnh/schema dùng môi trường schema-venv đã có; Node dùng NODE_PATH hiện có
  tại D:/systemdocs/shell/node_modules, không cài phụ thuộc mới.

### Lần triển khai trước review (giữ làm lịch sử)

- 8 tests Word-first: hai người/hai tài sản, 2+1 dòng đất, sửa rồi lưu/mở lại/xuất;
  nội dung tĩnh, kiểu chữ, ảnh, nguồn gốc và phần ZIP không sửa giữ nguyên.
- 242 tests Intake/Workspace/Word engine/batch; 37 shared-regex tests.
- 145 Node tests model/view/Intake/Word; 79 sidecar adapter tests và 6 Intake tests.
- 78 ví dụ contract: không có kết quả ngoài dự kiến; schema context/proposals thực tế pass.

## Giới hạn cần kiểm tra tiếp

Ngày 04/10/2026 root chạy Electron thật với dữ liệu tổng hợp: nhập hai người,
hai tài sản, sửa tên, lưu hồ sơ và sơ đồ, mở lại, xác nhận 25 vị trí rồi xuất
bằng hợp đồng gốc. Báo cáo `artifacts/docx-electron-20261004/startup-report.json`
ghi `ok: true`; Word gốc, các phần ZIP ngoài document.xml và database ban đầu
không đổi. Backend chạy trên bản sao code riêng, không dùng dữ liệu văn phòng.
Cửa sổ chọn file được thay bằng bộ trả đường dẫn giả lập; token, IPC và backend
vẫn đi qua code thật. Đây chưa phải phép thử cửa sổ chọn file native.

Chỉ dùng tài liệu mẫu tổng hợp, chưa đo độ chính xác trên hồ sơ văn phòng. Chưa chạy
bộ dựng trang Word hay bản đóng gói. Chưa có UI tách/gộp ứng viên
tùy ý; ranh giới không rõ giữ cảnh báo và cần người sửa. Không suy luận vai trò pháp lý.

## Lịch sử đề xuất 29/09/2026

# Progress — MIN-139

## Trạng thái: chờ owner review — 2026-09-29

## Đã làm
- Ghi `handoff.md` ngắn cho quyết định kiến trúc còn mở; gom lại tám đầu việc
  đã nêu trước khi so sánh các repo/công cụ regex.
- Tạo Linear MIN-139 và liên kết MIN-137, MIN-108, MIN-96, MIN-100, MIN-131.
- Viết product brief về lý do tồn tại, vấn đề, sản phẩm, phạm vi v1 và cách đo.
- Viết addendum về schema kết quả, chiến lược từng nguồn, noise/duplicate,
  Word assistant, ma trận test, quyết định mở và lộ trình.
- Đối chiếu Upload Lab SOT, kiến trúc parser, Document Intake adapters, contract
  Word và công cụ MIN-137 hiện có.

## Đang làm dở
- Chưa sửa SOT kiến trúc, `upload_lab/docs/spec_UI.md`, contract hoặc runtime.

## Bước tiếp theo
- Thử trên corpus nhiều nguồn và Word mẫu, rồi chốt quyền sở hữu engine/schema
  kết quả từ bằng chứng; bàn giao hiện tại đề xuất giữ lõi ở Document Intake.
- Sau khi chốt, tạo hoặc cập nhật contract trong task riêng trước khi implement.

## Check đã chạy
- `git diff --check`: pass sau lần soạn đầu.
- Kiểm tra trực tiếp 7 file Markdown mới/chưa được Git theo dõi: không có lỗi
  khoảng trắng cuối dòng, link nội bộ hoặc phạm vi 12 dẫn chứng source.
- Review cấu trúc và văn phong brief: đã chạy hai lượt độc lập và sửa câu chữ,
  bổ sung quyết định mở, phân biệt đề xuất triển khai với yêu cầu owner.
- Review cấu trúc addendum: đã chạy; bổ sung trạng thái đề xuất, giải thích từ,
  ranh giới schema, giữ mọi lần xuất hiện và liên kết tới file Word gốc.
- Review văn phong addendum: đã chạy; làm rõ quan hệ `duplicate_of` và các
  bước triển khai. Định nghĩa sản phẩm đã hoàn tất ở mức đề xuất; thuật toán
  nhóm dữ liệu và quyền sở hữu engine vẫn là câu hỏi mở.
