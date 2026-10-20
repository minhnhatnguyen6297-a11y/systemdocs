# Nam Định — SOT cấu trúc website và mapping Upload

**Cập nhật/quan sát:** 20/10/2026 · **website_id:** `nam_dinh` · **Website:** <https://congchungnamdinh.ninhbinh.gov.vn/>.

Đây là **nguồn chuẩn lâu dài của tri thức cấu trúc website thứ nhất**, dùng để bảo trì adapter và refine mapping #41; không phải nguồn duyệt schema nghiệp vụ. Website chính thức vẫn quyết định dữ liệu đã được ghi nhận; app điền sẵn, người dùng kiểm tra/tự Lưu, không suy kết quả Lưu từ browser. Tài liệu này ghi hiện trạng và gap, không cho phép sửa runtime, thêm cột/key canonical hoặc tự điền dữ liệu thiếu.

## 1. Phạm vi, thẩm quyền và mức bằng chứng

Owner 20/10 chọn **Nam Định trước; duy trì SOT cấu trúc website lâu dài; có thể cần trường phụ theo website nhưng chưa duyệt schema mới**. Xem [quyết định](../../decisions/decision-owner-upload-field-standardization-20261019.md#bổ-sung-owner-20102026--sot-cấu-trúc-website). Website thứ hai chưa định danh/khảo sát trong lượt này; không dùng catalog Nam Định làm catalog chung hoặc tự bật provider thứ hai.

- **Website/public bundle** chứng minh tên field, widget, rule, route và conversion được frontend định nghĩa; không chứng minh DOM sau đăng nhập, quyền của tài khoản, option hiện hành hoặc backend đã lưu đúng.
- **Source repo** chứng minh adapter, storage, projection hiện có; không thay bằng chứng live. **Canonical/contract được duyệt** quyết định nghĩa/key/kiểu/nhóm: [entities §8–9.4](../../../contracts/entities.md#8-từ-điển-dữ-liệu-người-customers-và-các-trường-suy-ra), [Notary contract](../../../contracts/notary-case-drafting.md). Upload workflow vẫn **DRAFT** (`contracts/README.md:11-18,33-44`; `contracts/upload-workflow.md:1-14`); tài liệu website không nâng nó thành approved.
- 8 key Case đã implement, nhưng Person/Asset/parties chưa canonical cutover đầy đủ. **Toàn #41 chưa hoàn thành; gate khảo sát mẫu ĐÓNG**, không phải tuyên bố issue đã CLOSED. Không đọc testcase/corpus để hoàn thiện catalog này.
- Không lưu PII, tên/ID nhân sự thật, cookie/token/credential, record hợp đồng hoặc raw khách hàng. Các option công khai phi cá nhân có thể chép; catalog nhân sự chỉ giữ shape/scope/trạng thái coverage.

### Ma trận kiểm chứng 20/10/2026

| Bề mặt | Quan sát thực tế | Kết luận được phép |
|---|---|---|
| Root, `/dang-nhap`, direct quick-create | Public shell tới được; browser chuyển `/dang-nhap`; phiên browser ban đầu không có tab; relay discovery timeout 8000 ms | Có shell/trang đăng nhập; **0 field DOM authenticated** |
| Public static assets | GET không credential thành công; route quick-create trỏ module 1517, permission `CREATE_HOSO` | Inventory **17 editable fields, 7 required tĩnh, 6 catalog widgets**, 1 tổng hiển thị + 2 hidden/derived state paths |
| Trạng thái | Module 926 định nghĩa đủ 3 option tĩnh | Đủ danh sách **static**, không claim đã mở dropdown DOM |
| Nhóm / Loại tài sản | Public GET trả 403 | Shape có source; **danh sách option chưa có** |
| Tên hợp đồng | Public GET không scope trả 200, `items=[]` | Không chứng minh catalog đơn vị rỗng/đủ; cần `donvi.id` |
| Công chứng viên / Thư ký | Không gọi person endpoints, không lưu nhân sự | Shape/scope có source; **count và option chưa xác minh** |
| Form API / lưu | Không submit/upload, không gọi ghi DB | Không chứng minh backend persistence hoặc Lưu thành công |
| Repo | Chỉ đọc source tĩnh, không chạy app/parser/build/test | Mapping source-level, không thêm proof runtime |

**Coverage còn thiếu:** authenticated empty quick-create DOM (required/readOnly/disabled/default thực), danh sách Nhóm hợp đồng, Loại tài sản, Tên hợp đồng đúng đơn vị, Công chứng viên và Thư ký đúng scope; xác nhận widget/selector thực. **Yêu cầu danh sách dropdown của user chưa được xác minh đầy đủ.** Không coi mảng rỗng public, fixture giả hay labels engine là câu trả lời thay thế.

## 2. Nguồn website bền vững và cấu trúc đọc

Các URL là nguồn public được lấy 20/10/2026; số module là locator trong bundle minified, không bịa line code chưa có. Khi hash URL đổi, đọc lại route/module thay vì mặc định module ID còn giữ.

| Mã | URL / locator | Nội dung dùng làm bằng chứng |
|---|---|---|
| W1 | <https://congchungnamdinh.ninhbinh.gov.vn/static/js/11.df7d9ede.chunk.js> · module **1517** | Schema quick-create, label/required/default/editor `D`; **977** chi phí; **926** status; **930** service submit; **772/773/779/803/910/911/927** hỗ trợ form |
| W2 | <https://congchungnamdinh.ninhbinh.gov.vn/static/js/app.e07578fa.chunk.js> · route `QUICK_CREATE → 1517` | Quyền `CREATE_HOSO`; modules **638/642/650/654/655/656/678/700/757/972** wrapper/widgets; **647** prefix API |
| W3 | <https://congchungnamdinh.ninhbinh.gov.vn/api/dm/nhomhopdong> | GET 403; không có list |
| W4 | <https://congchungnamdinh.ninhbinh.gov.vn/api/dm/loaitaisan> | GET 403; không có list |
| W5 | <https://congchungnamdinh.ninhbinh.gov.vn/api/danh-muc/TEN_HOP_DONG> | GET không scope: 200, `items=[]`; không là list của đơn vị |

SHA-256 của **text asset đã fetch, encode UTF-8** (không claim raw transfer bytes):

- W1: `0c24bfb433769d9bb6ad70c5c8920ffd04a94ebc572ff8b77e3371641a8fc1ba`.
- W2: `97553b476fa4120979a3c9c6b2e4e60043f74bbf0faae06bc703ef01595dd637`.

Phần thiết yếu được chép an toàn trong tài liệu này, không phụ thuộc file tmp hoặc bundle còn truy cập được. Evidence chi tiết cục bộ tùy chọn: `_bmad-output/tmp/namdinh-website-sot/website-evidence.json`, `website-handoff.txt`, `public-static-schema-excerpt.txt`, `public-widget-submit-excerpts.txt`; không dùng chúng thay catalog bền vững.

### Cấu trúc bề mặt được khảo sát

1. Root → `/dang-nhap`: username/password + Đăng nhập (selector repo `uploader_selectors.py:8-21:LOGIN_SELECTORS`); không lưu credential, không thử login.
2. Sau đăng nhập, adapter đi `/ho-so-cong-chung/tao-moi-nhanh` (`playwright_uploader.py:87-88:LOGIN_PATH,CREATE_PATH`; W2). Không xác minh menu authenticated hoặc toàn bộ trang khác của portal.
3. Quick-create gồm **Thông tin hồ sơ** (13 input kể cả attachment/ghi chú) và **Chi phí** (4 input tiền). Wrapper Chi phí dùng lại `name:"ghichu"` với `isFieldBuildIn:true`: **không phải input ghi chú thứ hai**. Tổng chi phí chỉ hiển thị.
4. Nút `Lưu hợp đồng` là đích thao tác người dùng; không click trong khảo sát. Upload Excel audit là bề mặt khác trong module, không lấy schema quick-create áp cho mọi form website.

Route declarations W2 sau đây là cấu trúc static liên quan Hồ sơ công chứng, **không phải menu đã quan sát với quyền thật**; không inventory toàn bộ form khác:

| Route | Tên / permission / module |
|---|---|
| `/ho-so-cong-chung` | Hồ sơ công chứng · `LIST_HOSO` · 1074 |
| `/ho-so-cong-chung/tao-moi` | Thêm mới hồ sơ công chứng · `CREATE_HOSO` · 1485 |
| `/ho-so-cong-chung/tao-moi-nhanh` | Thêm nhanh hồ sơ công chứng · `CREATE_HOSO` · **1517**, uploader dùng |
| `/ho-so-cong-chung/:id/standard` | Cập nhật hồ sơ công chứng · `UPDATE_HOSO` · 1484 |
| `/ho-so-cong-chung/:id/simple` | Cập nhật hồ sơ công chứng · `UPDATE_HOSO` · **1517** tái dùng form |
| `/ho-so-cong-chung/:id/online` | Route constant `UPDATE_ONLINE`; chưa xác minh component/form/permission của route này |

## 3. Tuyến dữ liệu và ký hiệu mapping

**Đường hiện có:** Word → `upload_lab/extraction_adapter.py:249-263:extract` → lõi `tools/regex_workbench/engine/contract_extract.py:4855-4983:build_payload` → `{case,web_form,raw}` → JSON extraction + registry → `playwright_uploader.py:698-741:load_upload_queue` → `770-807:build_upload_form_data` → `1944-1984:_prepare_record` → control website.

- **C (Case implemented):** canonical string/null; `ngaycongchung` full ISO date/null, `socongchung` `xxx/yyyy` scoped sổ/năm/website. DB Upload: `file_registry.case_json` TEXT JSON 8 key cố định; JSON extraction cũng có `case`. `batch_scan.py:32-36:REGISTRY_EXTRA_COLUMNS`, `180-271:upsert_registry_record`, `726-739:run_batch_scan`; reader ưu tiên registry Case `load_upload_queue:726-734`. Không nhân đôi Person/Asset thành cột registry. `contract_no` là scan/reference riêng, không PK Case chung.
- **J (JSON/raw/presentation):** `batch_scan.py:366-370:save_output_json` giữ payload; DB chỉ giữ `output_json_path` (`ensure_registry_schema:107-140`). Có trong JSON không đồng nghĩa approved canonical/storage nghiệp vụ hoàn chỉnh. Nội dung nghiệp vụ trong container tên `raw` vẫn cần mapping, không tự thành provenance.
- **P (policy/config):** default/giá trị portal, không phải dữ kiện từ Word. Rỗng khác số 0 hoặc quyết định bỏ phí. `_prepare_record:1975-1977` **bỏ qua giá trị rỗng**, không chủ động xóa default website.
- **U (unmapped):** không có key canonical/đích DB/wire approved cho nghĩa đó trong tuyến Upload; không tự đề xuất tên canonical. **F** là file/provenance kỹ thuật.
- Notary có DB độc lập: `inheritance_cases.case_state_json` (`notary_v2/models.py:130-150`) snapshot block **`case`** chứa 8 key; contract gọi là `case_state_json.payload.case` khi mô tả payload. `case_workspace.py:287-290:CASE_SCALAR_FIELDS`, `1016-1019:get`, `1197-1201:commit_stage`, `2788-2793:_build_payload`. Có đích Notary không có nghĩa Upload ghi nó. Provider tách data dir (`providers/registry.py:50-56`, `nam_dinh.py:58-105`); không shared Case ID/ghi chéo DB.

Canonical names giữ nguyên owner: `tenvanban,nhomhopdong,loaivanbannhandien,socongchung,ngaycongchung,congchungvien,thuky,chudat`. Nguồn chuẩn `contracts/entities.md:240-267`; source mapping `contract_extract.py:4783-4852:CASE_FIELDS,CASE_PORTAL_FIELDS,validate_case_fields,case_from_payload,case_portal_projection`. `loaivanbannhandien/chudat` không có input tương ứng trên quick-create. Upload không Diagram nên `chudat=null`; không suy từ Bên A/GCN/người chết.

## 4. Inventory đầy đủ 17 input quick-create

**R** là required trong W1 module 1517, không phải đã kiểm server/DOM. Control website lấy từ W1/W2; selector là **repo khai báo** hoặc name source, chưa DOM verified. CSS ID có dấu chấm phải escape `\.`. Các editor repo dùng XPath `Field-container` có label → `[contenteditable='true'][1]` (`uploader_selectors.py:103-132`). W1 defines no explicit title→group/group→asset dependency; không suy ra runtime không có dependency.

| # / field website / nhãn | Widget · R · default tĩnh | Extraction → canonical/đối tượng → DB/wire thực | App form key / selector / source |
|---|---|---|---|
| 1 `hopdong.tenhopdong` · Tên hợp đồng | freeSolo autocomplete · R · không ghi default | detect title `build_payload:4856,4932` → **C tenvanban** → Case JSON; text nguồn, không enum Notary | `ten_hop_dong` / `#hopdong\.tenhopdong` · selectors:41-48 |
| 2 `hopdong.tinhtrang` · Tình trạng | MUI select · R · `DACONGCHUNG` | Không extraction/canonical; **P** app label “Đã công chứng”; không map `inheritance_cases.trang_thai` draft/locked | `tinh_trang` / `#hopdong\.tinhtrang` · 64-70; defaults:3 |
| 3 `hopdong.ngaycongchung` · Ngày công chứng | date picker · không R · ngày hiện tại `yyyy-MM-dd`, display `dd/MM/yyyy` | `find_ngay_cong_chung` → **C ngaycongchung**, ISO/null `build_payload:4930-4936`; boundary `case_portal_projection:4845-4852` → DD/MM/YYYY. Ngày website mặc định không là ngày nguồn | `ngay_cong_chung` / `input[placeholder='dd/mm/yyyy']` · 49-55 |
| 4 `nhomhopdongId` · Nhóm hợp đồng | remote autocomplete · R | `guess_nhom_hd(title):1119-1129` → **C nhomhopdong** label → Case JSON; website chọn ID, app chưa lưu catalog ID | `nhom_hop_dong` / `#nhomhopdongId` · 71-78 |
| 5 `loaiTaisan` · Loại tài sản | remote autocomplete, object · R | `guess_loai_tai_san:1176-1202` → **J web_form.loai_tai_san** label; discriminator portal chưa canonical Asset cutover, không cột DB Upload/approved shared enum | `loai_tai_san` / `#loaiTaisan` · 79-86 |
| 6 `hopdong.sohopdong` · Số công chứng | text · không R tĩnh | `find_so_cong_chung`/scan + normalize `build_payload:4923,4935` → **C socongchung**; registry.contract_no vẫn scan/reference | `so_cong_chung` / `#hopdong\.sohopdong` · 56-63 |
| 7 `hopdong.congchungvien.id` · Công chứng viên | remote autocomplete · R | regex nguồn `build_payload:4929,4937` hoặc lựa chọn prepare rõ ràng → **C congchungvien** tên/null → Case JSON; ID website không là FK Notary | `cong_chung_vien` / `#hopdong\.congchungvien\.id` · 87-94; builder:781-792 |
| 8 `hopdong.thuky` · Thư ký | freeSolo autocomplete · không R | extraction `thuky=null` `build_payload:4938`; input prepare → **C thuky** tên/null → Case JSON; không ID conversion cần thêm | `thu_ky` / `#hopdong\.thuky` · 95-102 |
| 9 `hopdong.nguoiYeucauCongchung` · Thông tin người yêu cầu công chứng (ghi sổ công chứng) | CKEditor HTML · không R | `build_payload:4924-4927,4944` chọn B nếu có người, fallback A; cam kết tài sản A → first person raw_text; optional requester lookup → **J** presentation. Người + vai trò Hồ sơ **chưa cutover** (§6) | `nguoi_yeu_cau` / label XPath · 103-112; `resolve_requester_override:561-588` |
| 10 `hopdong.duongsu` · Đương sự | CKEditor HTML · R | `raw.ben_a/b` → `_fmt_duong_su_by_kind:4749-4765` → **J web_form.duong_su**, raw_text/entity_lines ghép; Person/parties chưa cutover | `duong_su` / label XPath · 113-122 |
| 11 `hopdong.taisan` · Tài sản | CKEditor HTML · R | `_find_tai_san_by_kind:1007-1116` → **J web_form.tai_san** text; song song `raw.danh_sach_thua_dat` `build_payload:4962-4973`. Asset chưa cutover; text không thay các field chuẩn | `tai_san` / label XPath · 123-132 |
| 12 `hopdong.fileHopdong` · Văn bản hợp đồng | upload + preview · không R · accept `.doc,.docx,.pdf` | **F** `raw.file_goc` (`build_payload:4974`) → JSON + registry.file_path; không canonical business column | `file_hop_dong` / `#hopdong\.fileHopdong` · 133-140; **không nằm fill order** (§8) |
| 13 `ghichu` · Ghi chú | textarea rows=3 · không R | **P/U** `DEFAULT_GHI_CHU=""`; không extraction/canonical storage. Không dùng Notary `ghichu` làm bucket cho trường khác nghĩa | `ghi_chu` / `#ghichu` · 141-147; builder:803 |
| 14 `chiphi.phicongchung` · Phí công chứng | money autocomplete · không R | **P/U** `DEFAULT_PHI_CONG_CHUNG=""`; chưa semantics/canonical/DB-wire cho phí trong tuyến Upload | `phi_cong_chung` / `#chiphi\.phicongchung` · 148-154; builder:804 |
| 15 `chiphi.thulaoCongchung` · Thù lao công chứng | money autocomplete · không R | **P/U** `DEFAULT_THU_LAO=""`; chưa semantics/canonical/DB-wire cho thù lao trong tuyến Upload | `thu_lao_cong_chung` / `#chiphi\.thulaoCongchung` · 155-161; builder:805 |
| 16 `chiphi.phiDvNgoaicongchung` · Phí dịch vụ ngoài công chứng | money autocomplete · không R | **U** không extraction, canonical key, registry field, builder key/selector hiện có; nguồn W1 module 977 | App **missing**, name website không là key schema mới được duyệt |
| 17 `chiphi.phikhac` · Phụ phí khác | money autocomplete · không R | **U** không extraction, canonical key, registry field, builder key/selector hiện có; nguồn W1 module 977 | App **missing**, không tự thêm cột/key |

Chi phí dùng currency `đ`, phân nhóm chữ số bằng khoảng trắng; thiếu thành 0 **chỉ trong công thức tổng website**, không là policy phí app đã duyệt. `fileLimit:10` truyền cho editor Đương sự/Tài sản không chứng minh editor enforce 10 file. Preview attachment `viewOnly:true` không đồng nghĩa input upload readonly; inherited maxFileSize default 10 chưa kiểm độc lập đơn vị. Không upload để suy giới hạn.

**Derived/hidden không tính thêm input:** module 977 cộng bốn khoản vào `chiphi.tongphi`; wrapper hiển thị `chiphi.total` / “Tổng chi phí” readonly; hidden Field lại viết **`phicongchung.tongphi`** và wrapper hidden trả null. Giữ nguyên discrepancy tên này; không “sửa đúng” bằng doc/schema. Không extraction/Case key/DB column cho tổng; không tự duyệt persist dữ liệu suy ra.

Required tĩnh đúng **7**: Tên hợp đồng, Tình trạng, Nhóm hợp đồng, Loại tài sản, Công chứng viên, Đương sự, Tài sản. **Ngày/Số công chứng không đánh dấu required tĩnh**; app critical list khác (`identify_missing_fields:810-812` gồm title, number, group, asset type, asset text). Rule date cho trống, có giá trị thì parse `yyyy-MM-dd`, lỗi “Định dạng ngày không hợp lệ”. CKEditor emits HTML; chưa xác minh rule semantic-empty HTML. Các control không khai báo disabled riêng, nhưng global viewOnly có thể disable; actual DOM chưa quan sát.

### 4.1 State trước Lưu → request API (public source, chưa submit)

Đường client W1 **module 1517 `onSubmit(t)` → module 930 export `b`/symbol `u(t)` → W2 module 647 → `POST /api/hoso/nhap-nhanh`, `data:t`**. Generic Form W2 **655** gọi callback bằng form state, không có bước map lại các tên field được thấy. Trích đúng phần quyết định:

```javascript
// W1 1517 — callback quick-create
onSubmit:function(t){return Object(l.b)(t).then(/* thông báo + điều hướng */)}
// l = n(930); W1 930 export b -> u
u=function(t){return Object(a.a)("hoso/nhap-nhanh",{method:"post",data:t})}
```

Do đó, đường nối từng hàng §4 sang API là **name path của form**, không phải tên canonical app:

- `hopdong` chứa `tenhopdong` (label/free text), `tinhtrang` (enum), `ngaycongchung` (ISO/null/invalid-date marker trước validation), `sohopdong` (text), `congchungvien.id` (ID), `thuky` (label/free text), `nguoiYeucauCongchung/duongsu/taisan` (HTML), `fileHopdong` (giá trị attachment do upload control quản lý; **shape file metadata/persistence backend chưa xác minh**, không gửi local path như cột business).
- Root `nhomhopdongId` là ID; root `loaiTaisan` là object từ autocomplete. Root `ghichu` là textarea text.
- `chiphi` chứa bốn field tiền đúng tên ở §4, và `tongphi` do module 977 tính. Money widget W1 **927** emits string input; numeric coercion unary `+` trong tổng không chứng minh backend currency type/rounding hoặc schema monetary amount approved.
- `chiphi.total` là wrapper hiển thị, không chứng minh có field value trong request. Hidden `phicongchung.tongphi` khác spelling: không chứng minh backend lưu path đó. JSON request thực tế chưa được capture.

**Không có bằng chứng client** chuyển `nhomhopdongId` thành `hopdong.nhomhopdong.id` hoặc `loaiTaisan` thành `hopdong.loaitaisan.id`; tuyệt đối không dùng các biến đổi giả định đó làm mapping. Initial edit values có đoạn `nhomhopdong: f.nhomhopdong?.id` (W1 1517), khác input `nhomhopdongId`; ghi nhận chênh lệch, không tự sửa/diễn giải là preSave conversion.

W1 callback sau promise thành công hiện thông báo “Đã lưu thành công” rồi điều hướng list; đó là hành vi **frontend source**, không evidence đã chạy thành công hoặc quyền app suy Save. Backend portal DB/schema và accepted body/attachment vẫn **chưa biết**, không đồng nhất với DB registry hoặc Notary. W1 module 930 còn khai báo GET `hoso`, GET/PUT/DELETE `hoso/:id`, POST `hoso`, GET `hoso/export`, GET `hoso/export-so-cong-chung`; chỉ catalog quick-create POST ở trên thuộc luồng form này, không thực thi endpoint ghi.

## 5. Sáu catalog: nội dung, scope và ID/label

| Catalog website | Nguồn / shape / conversion website | Nội dung biết chắc 20/10 | Mapping app và gap |
|---|---|---|---|
| Tình trạng | W1 module 926; value enum → label; default `DACONGCHUNG` | **3 option static đầy đủ:** `DANGXULY` → Đang xử lý; `DACONGCHUNG` → Đã công chứng; `HS_HUY` → Hủy bỏ | app chọn label default, không lưu enum vào Case; không map Notary status |
| Tên hợp đồng | `/api/danh-muc/TEN_HOP_DONG?donviId=<đơn vị hiện tại>`; `response.items`, accessor mặc định `label`; freeSolo emits label/free text, **không ID** | **List đơn vị chưa biết**. Unscoped items=[] không chứng minh rỗng. `donvi.id` lấy từ `/api/user/me` (không gọi trong khảo sát) | `tenvanban` giữ title nguồn, `ten_hop_dong` label/text; không ép vào enum Notary |
| Nhóm hợp đồng | `/api/dm/nhomhopdong`; item `id/tennhom`, emits **ID** | **List chưa biết — 403** | `nhomhopdong` Case đang là label; UI resolves label→option→ID, chưa local catalog mapping ID có scope |
| Loại tài sản | `/api/dm/loaitaisan`; item `id/ten`, `isValueObject:true` emits **object** | **List chưa biết — 403** | app chỉ label `web_form.loai_tai_san`; object website không phải canonical Asset record |
| Công chứng viên | `/api/user/congchungvien`; item `id/hoten`, emits **ID** | **Count/list chưa biết**, person endpoint không gọi, không giữ tên/ID thật | `congchungvien` Case là tên; UI resolves option ID; không approved new staff FK |
| Thư ký | `/api/danh-muc/THU_KY?donviId=<đơn vị hiện tại>`; items label, freeSolo emits label/free text, **không ID** | **Count/list chưa biết**, person endpoint không gọi | `thuky` Case là tên/text; scope đơn vị; không tự thêm FK |

**Adapter label boundary:** `playwright_uploader.py:161-186:get_field_value_candidates,field_value_matches`; `1637-1739:_fill_dropdown` chọn native select bằng `label` hoặc custom gõ text/chọn role option, không direct API ID assignment. Staff match folded equality; field khác folded substring; không là bằng chứng ID đúng/backend chấp nhận. `FIELD_VALUE_ALIASES:113-118` chỉ các biến thể “Thoả/Thỏa thuận - Cam kết”/“Cam kết - Thỏa thuận”, không catalog web.

`_read_dropdown_options:1384-1412` đọc label, bỏ placeholder/dedup; `fetch_staff_options:1414-1427` cache **labels** Công chứng viên/Thư ký. Không có local authoritative IDs; cache không thay list live hoặc approve nhân sự. Default CCV trong code chỉ prefill legacy, không dữ kiện extracted: `build_upload_form_data:790-792`; historical JSON bằng default không được nâng thành fact (`case_from_payload:4838-4841`). Không chép tên default cá nhân vào SOT.

`guess_loai_tai_san:1176-1202` có labels đất có/không tài sản, xe, tàu/thuyền, sổ tiết kiệm, cổ phần/cổ phiếu/chứng khoán/thẻ ATM/khác; `guess_nhom_hd:1119-1129` trả nhóm từ title hoặc Khác. Đây là **candidate output của engine**, **không phải danh sách dropdown Nam Định đã xác minh**. Fixture `shell/test/fixtures/upload_portal.py` là portal giả; native select/options mẫu không được dùng làm bằng chứng website.

## 6. Người / Tài sản / vai trò Hồ sơ trong ba editor

### 6.1 Người và parties

Nguồn `raw.ben_a/b.nguoi[]` giữ thứ tự, `entity_lines` là text tổ chức/đầu mục; `_extract_party_data:4154-4183`. `_format_person_block:2970-2979` hiện **dùng raw_text**, không rebuild từ canonical; `fmt_nguoi_yeu_cau:2982-2987` lấy người đầu hoặc tối đa ba entity_lines; `_append_party_display:2998-3009` ghép tất cả. `_fmt_duong_su_by_kind:4749-4765` chọn nhóm theo loại văn bản, không là quan hệ DB parties approved. Lookup requester tùy chọn theo số/năm/ngày có thể format người match từ hai bên hoặc trả tên lookup nguyên văn (`resolve_requester_override:561-588`, `_format_requester_person:527-558`); không chứng minh một quan hệ requester canonical được lưu.

| Nguồn extraction | Canonical / wire Notary đã có | Đích thực và ranh giới |
|---|---|---|
| `ho_ten` | `ten` / `ho_ten` | `customers.ho_ten` + case snapshot Stage |
| `ngay_sinh`, `chi_co_nam_sinh` | `ngaysinh` / `ngay_sinh` full date hoặc year/null | master Date + snapshot giữ độ đầy đủ; bool extraction không cột nghiệp vụ mới |
| `cccd` (người sống); `so_giay_to` (người chết) | `sogiayto` / `so_giay_to` | `customers.so_giay_to`; không ép mọi giấy thành CCCD hoặc auto link Case |
| `ngay_cap_cccd`; `ngay_cap` người chết | `ngaycap` / `ngay_cap` | `customers.ngay_cap`, snapshot; không tự padding năm |
| `dia_chi`, `dia_chi_line` | `diachi` / `dia_chi` | `customers.dia_chi`, snapshot; line là presentation; người chết địa chỉ theo nghĩa nguồn |
| `ngay_chet` | `ngaychet` / `ngay_chet` | `customers.ngay_chet`, snapshot |
| `noi_cap`, `loai_giay_to` | `noicap`,`loaigiayto` / legacy wire tương ứng | snapshot/derived evidence, **không cột customers** |
| `gioi_tinh` Ông/Bà | `gioitinh` / wire `gioi_tinh` Nam/Nữ/null | Cột customers.gioi_tinh có thật; danh xưng không tự là giá trị wire đúng; mapper DOCX hiện không map field này |
| `cccd_khac` | chưa approved multi-ID model | raw/evidence; Notary DOCX mapper tạo ambiguous normalized null, không persist list giấy tờ; #42 riêng |
| `ten_goi_khac`, `entity_lines`, vai trò requester/Bên A/Bên B | **U** mapping/catalog chưa chốt | không thêm schema, không ghi ghichu; entity_lines có thể chứa tổ chức, không tự xem là Người |
| `raw_text`, line/span/source_refs | provenance | giữ nguồn, không dùng chuỗi raw để claim canonical cutover |

Proof: `contract_extract.py:3688-3754:_extract_plain_text_person_entries`, `4608-4620:_extract_nguoi_chet`; `contracts/entities.md:150-185`; `contracts/notary-case-drafting.md:246-283:person_row`; `notary_v2/models.py:36-48:Customer`; `case_workspace.py:306-310:_PERSON_KEY_ALIASES`, `2495-2569:_upsert_people`, `2768-2779:_build_payload`. Notary DOCX mapper **thực** là `services/document_intake/adapters/docx.py:49-57:PERSON_FIELD_SOURCES`, loop **chỉ hai bên** `316-350`; không claim đã map đủ `raw.nguoi_chet`, alias/giới tính. `329-343` giữ multi-ID refs + `intake.ambiguous`. Cùng dùng lõi không phải luồng Upload→Notary DB.

### 6.2 Tài sản và cụm đất

`_new_thua_dat:1772-1802` giữ hàng thửa và nhiều giá trị/raw để báo mơ hồ; `build_payload:4962-4973` lưu `raw.danh_sach_thua_dat[]`. Map đối chiếu sau chỉ dùng tên canonical đã có, không tự đặt tên mới cho Asset.

| Nguồn hàng thửa | Wire/cột Notary có thật | Trạng thái mapping |
|---|---|---|
| `so_gcn_raw` | `so_serial` / properties.so_serial | Notary DOCX mapper dùng **raw**, giữ nguyên văn; không lấy normalized `so_gcn` thay |
| `so_vao_so`,`so_thua_dat`,`so_to_ban_do`,`dia_chi`,`co_quan_cap` | wire và properties cùng key | có đích; Upload vẫn J, không ghi Notary |
| `loai_gcn` | `loai_so` / properties.loai_so | mapper có; không cùng nghĩa `loaiTaisan` portal |
| `ngay_cap_gcn` | `ngay_cap` / properties.ngay_cap | ngày full, không ngày công chứng |
| `dien_tich` tổng | `dien_tich` tổng hợp/snapshot; properties.dien_tich có cột | không thay diện tích từng cụm; cần giữ tổng/chi tiết đúng nguồn |
| `muc_dich_su_dung`, `chi_tiet_dien_tich[].muc_dich_su_dung/dien_tich/thoi_han_su_dung` | `land_rows[].loai_dat/dien_tich/thoi_han` wire; canonical `loaidat/dientich/thoihan` | child DB `property_land_rows(property_id,vitri,loaidat,dientich,thoihan)`; vị trí=index+1, không trộn cụm |
| `thoi_han_su_dung` cấp thửa | `thoi_han` legacy emit/history | không tự đắp vào cụm không rõ; thời hạn mới chỉ thuộc cụm đất |
| `nguon_goc` | properties.nguon_goc / wire nguon_goc | có cột/writer, **không trong ASSET_FIELD_SOURCES** DOCX; không claim mapper đã đi hết |
| `phan_ghi_them` (hình thức sử dụng/ghi thêm/narrative lẫn nhau) | properties.hinh_thuc_su_dung có cột nhưng **không mapping toàn blob** | **U** cần tách nghĩa có căn cứ; không nhét Notary ghichu |
| `chi_tiet_dien_tich` phần không phải bộ ba; `*_raw`,`*_values`,`o_tho` | raw/alternatives/provenance hoặc nghiệp vụ chưa map | giữ nguồn/mơ hồ; không coi mọi nội dung trong container là kỹ thuật hay đủ DB |

Proof: `contract_extract.py:2163-2183:thua_dat_sang_land_rows`; `notary_v2/services/document_intake/adapters/docx.py:58-105:ASSET_FIELD_SOURCES,GROUP_FIELD_SOURCES`, `552-568` map parcel/land_rows; `contracts/notary-case-drafting.md:314-362,1177-1236`; `models.py:99-118:Property`, `182-208:PropertyLandRow`; `case_workspace.py:2572-2636:_upsert_assets` ghi master/child/mirror, `2781-2783` snapshot. Có schema đích **không chứng minh Upload cutover**.

`raw.tai_san_chua_ho_tro` nhận diện sổ tiết kiệm/bảo hiểm/xe, chưa bóc đầy đủ row nghiệp vụ (`_phat_hien_tai_san_chua_ho_tro:4768-4780`); mô tả text có thể còn nguyên. Không suy có dropdown loại xe là đã supported Asset DB/extraction hoặc mở phạm vi mua bán xe.

## 7. Phân loại trường phụ website — chưa duyệt schema

| Nhóm | Ví dụ | Hướng refinement, không phải implementation approval |
|---|---|---|
| Catalog mapping có scope | group ID↔label; asset object ID/ten; CCV ID↔tên; đơn vị của title/thư ký | Có thể là cấu hình/catalog adapter theo website + đơn vị + ngày/version. Không tự tạo Person/Asset/Case business column hoặc staff FK |
| Policy/config portal | default status, label aliases, selectors, route, default CCV legacy | Quản lý developer theo site; không nâng thành extraction fact. Không đồng nhất trạng thái portal với Notary draft/locked |
| Provenance/file/technical | file path, source_refs, asset hash/module, run/record IDs, timeout | Giữ evidence/scope an toàn; không buộc thành cột nghiệp vụ mới, không nhét PII vào doc |
| Nghiệp vụ cần quyết định nghĩa/owner/mapping | bốn khoản phí/thù lao, ghi chú thật của hồ sơ, trạng thái portal nếu cần lưu trong app, phần asset/parties chưa map | Refine trong **#41**: thật sự cần app lưu không, thuộc đối tượng nào, tên/kiểu/cardinality/DB-wire-output nào được owner duyệt. **Chưa chọn key/cột/default hoặc manual step mới** |
| Derived website | tổng chi phí và hidden path khác spelling | Phân biệt display/calculation với dữ kiện nguồn; chưa duyệt persist tổng hoặc sửa spelling |
| Owner đã loại | giá giao dịch/cọc/thuê/vay/lãi/điều khoản thanh toán/thời hạn nghiệp vụ | Không extraction/normalized; portal đòi thì ghi conflict #41, không bịa/default/âm thầm giữ hoặc tự quyết nhập tay. **Phí công chứng/thù lao không tự đồng nhất giá giao dịch**; vẫn cần quyết định riêng |

Thời hạn sử dụng đất đúng `land_rows[].thoihan` và timeout kỹ thuật vẫn giữ. Không xóa raw/lịch sử để đạt catalog. #42 model đa giấy tờ/đa địa chỉ chưa chọn; không tự là gate mới. Không tạo ticket trùng #41 chỉ vì mới thấy hai khoản phí.

## 8. Chênh lệch implementation cần giữ rõ

1. **17 input website vs 15 mapping repo:** hai khoản `chiphi.phiDvNgoaicongchung`/`chiphi.phikhac` chưa builder/selector/canonical/DB-wire. Tổng cũng chưa mapping; không báo inventory repo là toàn form.
2. `FORM_FIELD_ORDER` chỉ **14 entries** (`uploader_selectors.py:23-38`), không có `file_hop_dong`. Builder/selector/_upload_file có key/nhánh nhưng `_prepare_record:1969-1974` không đi tới attachment khi iterate order hiện tại. Không gọi file upload implemented end-to-end chỉ vì selector tồn tại.
3. Repo `kind:"text"` cho phí/ghi chú là cách fill của adapter, không widget site: site là money autocomplete/textarea; `kind:"dropdown"` gồm cả freeSolo. `_fill_text:1502-1515`, `_fill_editor:1742-1769` không chứng minh form state/API chấp nhận.
4. `_prime_contract_name_validation:1602-1618` có thể **click Lưu hợp đồng** khi số/nhóm còn trống; `_fill_dropdown:1707-1713` gọi nó để prime validation. Đây là discrepancy với nguyên tắc người dùng tự Lưu, **không** proof đã lưu/permission chạy hay lý do sửa runtime trong lượt tài liệu. Cần review/refine theo #41 và quy tắc SOT hiện có, không âm thầm mô tả runtime tuyệt đối không click.
5. `_prepare_record:1944-1951` persist Case nhân sự chỉ khi record thực prepare; queue read không ghi override. Preview/default không là fact. Historical Case invalid không được silently rơi về legacy; `validate_case_fields:4794-4810`/`case_from_payload:4813-4842` giữ lỗi.

## 9. Bảo trì và cập nhật

- **Một site một catalog chuyên sâu tại file này**; README module là entrypoint, không dựng workflow/source SOT song song. Khi website đổi route/bundle/widget/options/API hoặc adapter/schema đổi, cập nhật cùng file: ngày, scope nguồn, field count, option count/completeness, dependency, mapping và gap #41.
- Đầu lượt đọc AGENTS → specs README/product-overview → module README → graphify-out → source hiện hành. Dùng source `file:symbol:line`; line có thể trôi nên kiểm symbol trước khi cập nhật. Không dùng file tmp/cache như nguồn chuẩn bắt buộc.
- Thu thập an toàn theo quyền có thật: public GET/static trước; authenticated **empty form read-only** khi có phiên được phép, không tự tìm/import credential. Không Lưu/upload/ghi DB/đọc record cá nhân để kiểm widget. Ghi riêng static vs authenticated; nếu không vào được thì giữ gap, không sửa nhãn thành verified.
- Mỗi catalog phải có site/đơn vị/date/source, item value/label/type hoặc shape-only với lý do PII; ghi query/dependency/pagination trước khi claim đầy đủ. Không ghi tên nhân sự thật trong Git. Không suy 200+items=[] là list đầy đủ nếu thiếu scope; không suy 403 là catalog rỗng.
- Nếu chỉ đổi selector/catalog/policy, phân loại technical adapter config; nếu đổi nghĩa nghiệp vụ/DB-wire, refine #41 và xin schema approval theo contract trước code. Không tự rename canonical, thêm alias, dùng ghichu/raw capture thay trường hoặc đóng gate.
- Main agent/reviewer kiểm liên kết/citation/counter consistency và đối chiếu source độc lập trước commit. Lượt này không chạy build/test/runtime; docs không nghiệm thu portal hay corpus. Không tạo HTML vì đây là catalog tra cứu, không thay UI/luồng cần minh họa.
