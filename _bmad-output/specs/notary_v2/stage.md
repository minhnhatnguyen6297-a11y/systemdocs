# Stage — Dữ liệu đã commit của hồ sơ

**Trạng thái:** Active · **Owner:** `notary_v2`

## 1. Công dụng

Stage là nguồn dữ liệu Người và Tài sản đã được người dùng xác nhận cho workspace.
Mọi Input chỉ trở thành Stage sau thao tác `Cập nhật` thành công.

## 2. Draft và committed

- **Draft:** bản người dùng đang thêm, sửa, xóa hoặc sắp xếp; chỉ sống trong
  phiên UI.
- **Committed:** snapshot server trả sau `workspace_create` hoặc
  `workspace_commit_stage`; Pool và Diagram dùng bản này.
- `Hủy` là thao tác client: khôi phục cả Stage và Diagram draft về snapshot
  committed gần nhất, không tăng revision.

## 3. Thao tác

- Người và Tài sản sửa trực tiếp trên Stage.
- Chỉ nút xóa của dòng được xóa dòng đó.
- Xóa/sửa draft chưa đổi server và chưa prune Diagram.
- `Cập nhật` gửi toàn bộ Stage cùng `base_revision`.
- Hồ sơ mới: lần `Cập nhật` đầu gọi `workspace_create`, tạo case và revision 1.
  Client sinh một `idempotency_key` UUID v4 cho nháp và dùng lại đúng key khi
  retry sau timeout; đổi key có thể tạo hồ sơ trùng.

## 4. Input và output

Input gồm Stage snapshot `{people, assets}`, case metadata và `base_revision`
khi cập nhật. Output gồm revision mới, Stage đã gán `entity_id`, Diagram sau
prune và render model do backend tính lại.

`row_id` do client sinh UUID v4 và giữ ổn định qua commit/reload. `entity_id`
là ID database, có thể null trước commit.

## 5. Quy tắc dữ liệu

- Người: 6 trường nghiệp vụ chính (`ten`, `ngaysinh`, `ngaychet`, `sogiayto`,
  `ngaycap`, `diachi`); DB còn giữ giới tính và ID/thời gian tạo. Chỉ họ tên
  bắt buộc; giới tính nhận Nam/Nữ/null, ngày nhận `YYYY-MM-DD`, `YYYY` hoặc
  null; số giấy tờ/địa chỉ có thể null. Người sống có ngày cấp được suy loại
  giấy tờ/nơi cấp/nhãn cư trú theo mốc 01/10/2024; thiếu ngày để trống.
  Người chết giữ loại giấy tờ/nơi cấp theo bằng chứng đã xác nhận trong
  snapshot, không gán mặc định; nhãn địa chỉ là `Nơi chết`.
- Tài sản: serial bắt buộc `[A-Z]{2}\d{6,8}` và địa chỉ không rỗng;
  số thửa/số tờ tùy chọn. Cụm đất có thể null/rỗng; nếu có, kiểm kiểu và
  alias mâu thuẫn, tối đa 20 cụm. Quy tắc hiện hành thay bộ bắt buộc và
  serial tự do của MIN-140 theo Owner xác nhận 03/10/2026.
- Không chặn chuyển tab khi nhập; chỉ `Cập nhật` mới kiểm dữ liệu.
- CCCD/giấy tờ là free text, không dùng làm Case key.
- Nhập Word giữ phần regex lấy được trong ô tương ứng để người dùng sửa,
  kể cả chữ nguồn bị dính/sai chính tả; không tự sửa tên cơ quan hoặc bỏ
  giá trị chữ chỉ vì khác mẫu (Owner TASK-10.3, 08/10/2026). Không thêm ô
  nguyên văn. Ngày/diện tích và nhiều giá trị chưa chọn vẫn theo quy tắc
  kiểm hiện hành của [nhập DOCX](./input/docx-import.md).
  Ô nơi cấp đang có phải ghi đúng nghĩa: người sống là nơi cấp giấy tờ,
  người chết là nơi cấp giấy khai tử; không gắn nhãn giấy khai tử cho CCCD.
- Tài sản v2 tối đa 3; vị trí là thứ tự mảng, vị trí 1 là primary theo nghĩa
  engine. Không dùng `is_primary` trong wire v2.
  * Bỏ trường lẻ `thoi_han` ở cấp tài sản vì là trường mồ côi: không tự đắp
    vào cụm khi xuất; giữ nguyên bản gốc và báo cần đối chiếu.
  * Thông tin loại đất lưu cụm 3 trường: `loaidat` - `dientich` - `thoihan`
    (tối đa 20 cụm một tài sản). Mỗi cụm là một bản ghi trong bảng con
    `property_land_rows` (UNIQUE `(property_id, vitri)`, `vitri` = vị trí
    cụm 1..20, giữ nguyên vị trí trống); `properties.land_rows_json` chỉ
    còn vai trò tương thích/chuyển đổi, không còn là nguồn lưu chính.
  * Wire/snapshot chấp nhận cả key canonical (`loaidat`/`dientich`/`thoihan`)
    lẫn key legacy (`loai_dat`/`dien_tich`/`thoi_han`); cùng trường mà hai
    key mang giá trị mâu thuẫn → `stage_validation_error` code `conflict`,
    không chọn ngầm.
  * Định danh phân biệt Loại đất thứ mấy trong Tài sản thứ mấy:
    Cú pháp `[trường][loại đất M][tài sản N]` viết liền không dấu, **không có dấu gạch dưới `_`**.
    Ví dụ: `loaidat12` = loại đất 1 của tài sản 2; `dientich12` = diện tích loại đất 1 của tài sản 2; `thoihan12` = thời hạn loại đất 1 của tài sản 2.
    Review MIN-141 (29/09/2026) chốt: chỉ dùng dạng đầy đủ `loaidat<M><N>`,
    không thêm alias rút gọn `loaidatM` vì `loaidat12` trùng nghĩa giữa
    "cụm 1 tài sản 2" và "cụm 12 tài sản 1".
- Reorder đổi nghĩa vị trí nhưng không đổi `row_id`.
- Hồ sơ thừa kế bắt buộc `owner_row_id`; hồ sơ `two_party` cấm trường này.
- Hồ sơ có 3 trường quản lý: `noiniemyet` (nhập tay; gợi ý địa chỉ đang triển khai
  theo [quy tắc tra cứu](./administrative-address.md)),
  `nguoinhanuyquyen` (danh mục quen/tạo mới), `noidungviec` (nhập tay).
  Tất cả tuân thủ quy tắc viết liền không dấu, không có ký tự `_`.

## 6. Commit và lưu

Backend thực hiện trong một transaction:

```text
validate
→ upsert/link Người và Tài sản
→ prune tham chiếu Diagram không còn hợp lệ
→ chạy lại engine
→ tăng revision
→ commit
```

Một dòng sai làm toàn bộ commit thất bại. `base_revision` khác server revision
phải báo `workspace_conflict`; không ghi đè cưỡng bức.

## 7. Quan hệ với feature khác

Tra tên xã/tỉnh dùng kho cục bộ, không gửi địa chỉ khách hàng lên website,
không cần ngày giấy. Nơi cấp giấy khai tử tra xã mới từ địa chỉ của chính người
đã chết. Máy không tự ghi kết quả vào Stage: người
dùng copy rồi lưu như sửa tay. Cách gọi nằm tại
[tra cứu địa chỉ](./administrative-address.md).

Nhập hợp đồng DOCX giữ optional `docx_import` bên cạnh Stage, không nhét
nguồn vào field Người/Tài sản. Context ghi cùng transaction/revision khi
create/commit, tải lại qua workspace_get; xóa dòng prune binding, đổi thứ tự
không đổi row_id và buộc kiểm slot trước xuất. Chi tiết tại
[`input/docx-import.md`](./input/docx-import.md).
Danh tính cụm đất nguồn được giữ riêng với vị trí cụm trong danh sách đã lưu;
xóa cụm không chuyển đối chiếu sang cụm kế tiếp. Gỡ nguồn Word chỉ bỏ đối
chiếu, giữ dòng Stage và không đọc lại file đã hỏng. Binding mới sai ô/slot
hoặc chưa có giá trị khiến cả transaction bị hủy.

- Input thêm/sửa Stage draft, không commit thay người dùng.
- Pool = người trong Stage committed chưa được gán Diagram.
- Diagram chỉ tham chiếu `row_id` của Stage committed.
- Word đọc snapshot Stage và Diagram đã lưu.

## 8. Lỗi và ngoại lệ

- Lỗi field gắn đúng `row_id`, field và code.
- Xóa phần tử Stage khi commit phải prune mọi tham chiếu Diagram trong cùng
  transaction.
- Hồ sơ legacy có hơn 3 tài sản vẫn được đọc đủ kèm warning; commit bị chặn
  đến khi còn tối đa 3.
- Commit lỗi không được xóa draft hoặc local UI state.

## 9. Giao diện

- Tài sản dùng bảng chuyển vị: mỗi cột là Tài sản 1..3; mỗi dòng là một
  thuộc tính. Cụm loại đất sửa các dòng `(Loại đất, Diện tích, Thời hạn)`.
- Bảng hồ sơ: Bố trí thêm 3 dòng ngay dưới các dòng tài sản (`Nơi niêm yết`,
  `Người nhận ủy quyền`, `Nội dung việc`), giảm 10% độ cao các ô để không
  chiếm nhiều diện tích màn hình.
- Người dùng bảng dòng có kéo sắp xếp, radio `Để lại`, các field chính và nút
  xóa. Danh sách dài cuộn cả trang, không tạo vùng cuộn riêng trong card.
- Lỗi field tô đúng ô/dòng theo `row_id`. `+ Người`, `+ Tài sản` và xóa chỉ
  thay draft cho tới khi commit.
- Toolbar dùng `Nhập file`, `Hủy thay đổi`, `Cập nhật`; chấm dirty cho biết
  Stage chưa commit. Quy tắc màu/kích thước chung thuộc `_bmad-output/specs/ui/`.

## 10. Kiến trúc, câu hỏi và lịch sử

Stage v2 thay mô hình flag phân tán bằng snapshot có revision. Owner chốt
27/09/2026: vòng đời draft/committed, `owner_row_id`, tài sản theo vị trí và
commit nguyên khối thuộc `notary.case-drafting.v2`.
Owner chốt 01/10/2026 (MIN-141): Từ điển dữ liệu Người đầy đủ, chuẩn hóa cụm
loại đất (1..20) bỏ `thoi_han` lẻ mồ côi, bổ sung 3 dòng hồ sơ dưới tài sản,
và quy tắc đặt tên trường tiếng Việt không dấu viết liền số.

Ngày 03/10/2026, Owner xác nhận 14 commit MIN-141 là cập nhật đúng và yêu cầu
gộp vào nhánh chính. Quy tắc hiện hành ở §5 thay phần MIN-140 mâu thuẫn;
không thay các quy tắc revision, owner và giữ nháp.

## 11. Nguồn

- Contract: `contracts/notary-case-drafting.md` §13.
- Ảnh bố cục đã duyệt: `_bmad-output/specs/ui/references/approved-drafting-v2.png`.
- Source chính: `shell/src/renderer/notary/case-drafting-view.js` và
  `notary_v2/routers/cases.py`.
