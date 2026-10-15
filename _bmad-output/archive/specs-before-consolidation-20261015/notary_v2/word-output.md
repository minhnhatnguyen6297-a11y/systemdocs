> **Lịch sử trước đợt gom 15/10/2026. Không phải nguồn hành vi hiện hành; không nạp mặc định đầu phiên. Trạng thái Draft/đã duyệt trong bản gốc được giữ nguyên.**

# Word output — Xuất văn bản

**Trạng thái:** Active cho hồ sơ thừa kế và hai bên (NAIA-8/12).
Owner yêu cầu tích hợp 03/10/2026; kiểm chứng bản tích hợp 04/10/2026.

## 1. Công dụng

Dựng một hoặc nhiều file DOCX từ snapshot Stage, Diagram, tài sản và lựa chọn
văn bản đã lưu. Word chỉ trình bày; không tự quyết quan hệ hoặc kết quả pháp lý.

## 2. Flow

```text
Chọn thư mục mẫu + chọn văn bản + thư mục đích
→ kiểm workspace và loại hồ sơ
→ đọc Stage và Diagram đã lưu
→ backend dựng placeholder
→ tạo từng DOCX
→ trả kết quả saved/failed/skipped theo file
```

Đổi thư mục mẫu xoá ngay lựa chọn cũ và khoá Xuất/Chọn trong lúc quét; chỉ
kết quả của lần quét mới nhất được hiển thị — không để response của thư mục
trước đè danh sách thư mục sau.

Dialog có ô **Nơi niêm yết**: nạp giá trị đã lưu của hồ sơ, cho sửa và lưu
qua `notary.workspace_update`. Lệnh cập nhật cả cột hồ sơ và đúng key của
snapshot đã lưu trong một lần ghi; không đổi Stage, tài sản hoặc sơ đồ.
Lưu lỗi giữ nội dung đang nhập; revision cũ phải báo xung đột. Bản nháp metadata
khác trong card Tài sản không bị mất khi lưu riêng Nơi niêm yết.
Nếu ô Nơi niêm yết khác bản đã lưu, dialog yêu cầu lưu trước khi xuất, kể cả
bản nháp đã có từ card Tài sản. Không hiển thị nơi mới rồi xuất theo nơi cũ.

Tra nơi niêm yết theo [tra cứu địa chỉ](administrative-address.md): bấm Tra
trên chính nội dung ô, không chọn tài sản nguồn, không cần ngày. Kết quả chỉ để
copy; không tự lưu hoặc thay giá trị đang nhập (Owner 05/10/2026, TASK-2).

## 3. Input và output

Input: `case_id`, danh sách `document_keys` và thư mục đích local đã tồn tại;
optional `template_dir` (thư mục chứa mẫu `.docx` người dùng chọn) và
`create_case_subdir` (ghi vào `<đích>/HS-<case_id>/`). Nhánh mẫu thư mục/catalog
không nhận `base_revision`; nhánh hợp đồng gốc cần revision đã lưu. Output liệt kê từng document, tên file thực, path, trạng thái
và lỗi; breakdown luôn có `succeeded`, `failed`, `skipped`.

### Nguồn mẫu

Luồng nhập hợp đồng DOCX có thêm **Dùng hợp đồng Word đã nhập** trong dialog
này. Chọn riêng từng lần xuất hiện → dòng đã lưu → slot catalog rồi lưu đối
chiếu trước khi xuất. `original_source_id` chỉ resolve nguồn backend thuộc
hồ sơ, không nhận đường dẫn mẫu tùy ý; batch này cần `base_revision`. Mẫu gốc
và mẫu dẫn xuất đều kiểm hash; đổi thứ tự/ô phải xác nhận lại. Không thay mọi
chuỗi giống nhau. Quy tắc và giới hạn tại
[`input/docx-import.md`](input/docx-import.md).

Nguồn mẫu thông thường chọn từ thư mục. Catalog cố định còn được backend
giữ để tương thích với các lệnh cũ, không phải lựa chọn trong dialog.
Không `template_dir` → catalog backend cố định (hành vi cũ). Có `template_dir`
→ backend quét file `.docx` ngay trong thư mục (bỏ `~$*` lock file, bỏ
non-DOCX, không vào thư mục con, thứ tự theo tên). `document_key` = basename
gốc; `document_keys` được đối chiếu lại với đúng tập file của thư mục đã cấp
quyền — renderer không gửi được path tùy ý hay thoát thư mục qua traversal.

## 4. Quy tắc dữ liệu

| Nội dung | Nguồn |
|---|---|
| Thông tin cá nhân | Stage |
| Quan hệ | Diagram |
| Kết quả/phân số | Engine result Python |
| Tài sản | Stage assets + vị trí Diagram |
| Mẫu và placeholder | Thư mục người dùng chọn hoặc catalog backend |

Không lấy dữ liệu chưa commit hoặc kết quả frontend tự tính. Placeholder chưa
giải quyết phải làm file đó thất bại, không âm thầm để sót trong văn bản.

Phase thư mục mẫu chỉ chặn lỗi kỹ thuật: thiếu người/tài sản đã lưu, giới hạn
số lượng, mẫu/đường dẫn không hợp lệ và token không hỗ trợ. Thừa kế thiếu
người nhận hoặc dấu Chủ vẫn xuất được trường tĩnh; nhóm chưa có dữ liệu để
trống. Tại sao: owner NAIA-8 yêu cầu engine tĩnh trước; xuất được file không
phải xác nhận hồ sơ đã hoàn thiện pháp lý. Catalog backend cũ giữ điều kiện
chủ đất đã chết/người nhận để các consumer legacy không đổi hành vi.

### Placeholder và context

- Placeholder mới dùng `[Tên danh sách N - Trường]`; alias cũ chỉ để mở
  template cũ, không làm chuẩn đặt tên mới.
- **`[Người N - *]` lấy đúng thứ tự danh sách Stage** (NAIA-8), gồm cả người
  chưa có node — đảo/xóa node Diagram không đổi số Người. Vai trò lấy từ dữ
  liệu nghiệp vụ đã lưu, không suy từ vị trí node.
- Các alias viết liền MIN-141 (`[tenN]`, `[ngaysinhN]`, …) vẫn giữ slot legacy;
  field đọc snapshot, chỉ fallback master khi key thiếu. Null/rỗng đã lưu
  giữ nguyên; giấy chứng tử và nơi cấp đã xác nhận không bị suy lại từ địa chỉ.
  Metadata hồ sơ và cụm đất 1..20 cũng ưu tiên snapshot.
- Context thừa kế phân loại thành `Người`, `Chủ đất sống`, `Chủ đất chết`,
  `Người nhận`, `Người không nhận`; `Người từ chối` chỉ có khi có bằng chứng
  pháp lý xác nhận riêng.
- Context hai bên (`case_type:two_party`, NAIA-8): `[Bên A N - *]`/`[Bên B
  N - *]` theo slot `p1..p15`/`p16..p30` (ô trống render rỗng, không dồn);
  `[Bên A - Họ tên]`, `[Bên B - Họ tên]`, `[Tên bên A]`, `[Tên bên B]` =
  danh sách họ tên từng bên; placeholder riêng thừa kế render rỗng.
  Readiness hai bên chỉ kiểm tra kỹ thuật (`word.no_people`,
  `word.no_diagram`, `word.no_assets`, `word.too_many_*`) — không áp điều
  kiện chủ đất/người nhận của thừa kế, không thêm kiểm định pháp lý.
- **Người được ủy quyền** lấy từ vai trò đã lưu trong `participants.vai_tro`,
  không yêu cầu node Diagram (đại diện hợp lệ có thể không nằm trên sơ đồ;
  người bị ẩn/xóa trên Diagram không tính). Mẫu khai báo nhu cầu qua hậu tố
  số của token — `[Dòng người được ủy quyền N]`,
  `[Người được ủy quyền N - <trường>]`, `[<Trường> người được ủy quyền N]`,
  `[Người được ủy quyền inline N]` đều là slot `N`; token không số là slot 1.
  Hồ sơ thiếu đại diện cho slot mẫu đòi → file đó lỗi
  `word.missing_authorized_person`, không render rỗng rồi xuất.
- **Diện tích đất theo vị trí** (quyết định Owner 02/10/2026, NAIA-8 comment
  `01a0fd42-5cbe-7076-976e-ef907c8ca086`): `[ONT]`/`[CLN]`/`[NTS]`/`[LUC]`
  (và hậu tố ` N` theo tài sản) là diện tích của dòng loại đất ở VỊ TRÍ
  1/2/3/4 — không tra theo mã loại đất thật. Nhãn loại đất trong bản migrate
  mới dùng `[Loại đất tài sản N.M]` (loại đất thật của dòng) hoặc
  `[Tài sản N - Loại đất]`/`[Loại đất tài sản N]` (loại đất cấp tài sản);
  chữ ONT/CLN/NTS/LUC in cứng trong mẫu cũ được migration đổi thành
  placeholder đó thay vì giữ nhãn cứng sai dữ liệu (chi tiết §10 của catalog
  `placeholder_mapping.md`).
- Tầng 1 lấy field trực tiếp. Tầng 2 dựng trọn câu/dòng và trả rỗng toàn bộ khi
  không áp dụng, tránh để lại dấu câu rác. Chưa có block `if/for` cho template.
- Resolver không được đoán nghiệp vụ từ tên placeholder. Catalog hiện hành nằm
  cạnh template tại `notary_v2/word_templates/placeholder_mapping.md`.

## 5. File và an toàn

- Tên: `<filename_stem>_HS-<case_id>[_n].docx`.
- Không ghi đè file có sẵn; trùng tên tăng `_2`, `_3`, ...
- Output phải nằm trong thư mục người dùng chọn; cấm UNC/path traversal theo
  contract hiện hành.
- Cancel giữ file đã lưu, đánh dấu file chưa bắt đầu là `skipped`.
- File đang ghi dở phải được dọn khi có thể.

## 6. Lỗi

- Không chọn văn bản, key lạ/lặp, thiếu template, placeholder còn sót, file bị
  khóa hoặc path sai đều có code riêng.
- `word.missing_authorized_person`: mẫu đòi slot đại diện N lớn hơn số vai
  trò `Người được ủy quyền` đã lưu — file đó thất bại, không tạo DOCX.
- Một file lỗi không bắt buộc làm mất file khác đã tạo.
- Tất cả file lỗi: job `word_batch_failed`; trộn kết quả: `partial`.

## 7. Kiến trúc, câu hỏi và lịch sử

Backend/Python sở hữu template catalog, mapping và tên file. Electron chỉ chọn
thư mục, gửi command, hiển thị kết quả và mở file khi người dùng yêu cầu.

Renderer phải xử lý placeholder trong paragraph, table, header/footer và khi
Word tách một placeholder thành nhiều run. Router chỉ điều phối; logic dựng
`WordExportContext` và thay placeholder thuộc service Word.

Migration đọc bản sao `.docx`/`.doc`, ghi thư mục mới và manifest theo từng file.
Không sửa mẫu nguồn. `.doc` dùng Word COM: nếu `SaveAs2` cần đổi tên file và bị
khóa an toàn chặn, lấy gói `WordOpenXML` trong bộ nhớ rồi ghi qua handle đã kiểm
danh tính; khóa chống đổi file vẫn giữ đến lúc đọc hash và đóng Word. Các part
XML và binary được giữ; token không rõ báo trong manifest, không tự tạo dữ liệu.

Owner 02/10/2026 bỏ `[Số công chứng]`, `[Giá chuyển nhượng]`,
`[Người ủy quyền2]`; migration ghi số lần bỏ và giữ nhãn biểu mẫu cần điền tay.
Mã cố định biểu mẫu thuế chỉ được miễn kiểm tra cho đúng mẫu đã xác minh.

Kiểm chứng 04/10/2026: 17 DOCX + 5 DOC chuyển mới và batch 22/22 saved;
22 nguồn giữ nguyên hash. Word COM đọc được nguồn/đầu ra, số trang nguồn và
mẫu chuyển khớp cả 22. So cấu trúc XML trực tiếp đạt 17 DOCX; 5 DOC vẫn
`not_verified` ở tầng này vì không có XML nguồn. Chưa kiểm trực quan từng trang
hoặc chọn thư mục mẫu bằng cửa sổ chọn file native. Bằng chứng sau sửa ở
`artifacts/word-integration-review-fixes-final-20261004/e2e_report.json`
(không commit); kiểm trên bản sao, không sửa file nguồn. DOCX nhập vào hồ sơ
có phép thử Electron thật riêng trong [spec nhập Word](input/docx-import.md),
cửa sổ chọn file của phép thử ấy vẫn là bộ giả lập trả đường dẫn.

Còn mở: bộ văn bản cho domain mới và mapping per-asset phải được duyệt; không
nhân bản logic từ template hiện có.

## 8. Nguồn

- `contracts/notary-case-drafting.md` §8.
- `notary_v2/word_templates/placeholder_mapping.md`.
- `notary_v2/services/word_engine.py` và tests Word.
- [`word-output-detail.md`](word-output-detail.md) giữ ví dụ placeholder,
  flow web cũ và các kiểm tra renderer chi tiết.
