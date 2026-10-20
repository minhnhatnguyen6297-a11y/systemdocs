# Nam Định — SOT cấu trúc website và mapping Upload

**Cập nhật/quan sát:** 20/10/2026 · **website_id:** `nam_dinh` · **Website:** <https://congchungnamdinh.ninhbinh.gov.vn/>.

Đây là **nguồn chuẩn lâu dài của tri thức cấu trúc website thứ nhất**, dùng để bảo trì adapter và refine mapping #41; không phải nguồn duyệt schema nghiệp vụ. Website chính thức vẫn quyết định dữ liệu đã được ghi nhận; app điền sẵn, người dùng kiểm tra/tự Lưu, không suy kết quả Lưu từ browser. Owner đã giao triển khai adapter theo policy chốt dưới đây; không thêm cột/key canonical hoặc tự điền dữ liệu thiếu.

## 1. Phạm vi, thẩm quyền và mức bằng chứng

Owner 20/10 chọn **Nam Định trước; duy trì SOT cấu trúc website lâu dài; có thể cần trường phụ theo website nhưng chưa duyệt schema mới**. Xem [quyết định](../../decisions/decision-owner-upload-field-standardization-20261019.md#bổ-sung-owner-20102026--sot-cấu-trúc-website). Website thứ hai chưa định danh/khảo sát trong lượt này; không dùng catalog Nam Định làm catalog chung hoặc tự bật provider thứ hai.

**Policy owner chốt 20/10/2026 — phạm vi Upload Nam Định hiện tại:** bỏ qua/không điền cả bốn ô `chiphi.phicongchung`, `chiphi.thulaoCongchung`, `chiphi.phiDvNgoaicongchung`, `chiphi.phikhac` và Ghi chú `ghichu`. Không ghi 0, không xóa default portal, không thêm extraction/cột phí hoặc quy trình nhập tay. Tổng chi phí là hiển thị suy ra, không ô thứ năm và không có persistence riêng. Tất cả hợp đồng upload mặc định **`DACONGCHUNG` / “Đã công chứng”** — policy portal, không extracted fact hoặc trạng thái Notary draft/locked. Owner đã giao triển khai liên tục phần đã chốt; không có technical approval gate mới. Gap mapping phí nằm ngoài scope hiện tại, không còn là câu hỏi chờ owner. Mở rộng tương lai phải được giao và duyệt riêng; toàn #41 còn mở, gate mẫu **ĐÓNG**.

**Hợp đồng consumer preSave của slice này:** builder và fill order không chứa phí/ghi chú; caller mang giá trị cũ cũng không được điền. Title/Thư ký freeSolo nhập qua input và blur không submit; các remote autocomplete chọn option thật, không chọn option đầu bất kỳ hoặc gán object/ID trực tiếp; status dạng combobox mở/chọn “Đã công chứng”, native select vẫn được hỗ trợ. Không bấm Lưu, không dùng Enter/prime validation hoặc chặn submit toàn form để che bug. Attachment nguồn `raw.file_goc` là provenance kỹ thuật: chuẩn bị qua input file đã quan sát, kiểm filename/file selection và phản ánh thiếu/lỗi thành partial, không coi text tên file trên trang là upload thành công. Không đoán metadata attachment, POST hoặc backend persistence. Proof dùng browser/profile/SQLite/form kiểm soát, không real portal upload.

- **Website/public bundle** chứng minh tên field, widget, rule, route và conversion được frontend định nghĩa; không chứng minh DOM sau đăng nhập, quyền của tài khoản, option hiện hành hoặc backend đã lưu đúng.
- **Authenticated empty quick-create, 20/10/2026 sau khi user tự đăng nhập:** DOM và option đang render chứng minh trạng thái của form/list trong phiên khảo sát; không chứng minh toàn bộ catalog của mọi đơn vị, form state sau chọn, request submit hoặc DB website. Chỉ đọc/thử chọn rồi trả form về rỗng; không bấm Lưu, prime validation, upload hoặc mở record.
- **Source repo** chứng minh adapter, storage, projection hiện có; không thay bằng chứng live. **Canonical/contract được duyệt** quyết định nghĩa/key/kiểu/nhóm: [entities §8–9.4](../../../contracts/entities.md#8-từ-điển-dữ-liệu-người-customers-và-các-trường-suy-ra), [Notary contract](../../../contracts/notary-case-drafting.md). Upload workflow vẫn **DRAFT** (`contracts/README.md:11-18,33-44`; `contracts/upload-workflow.md:1-14`); tài liệu website không nâng nó thành approved.
- 8 key Case đã implement, nhưng Person/Asset/parties chưa canonical cutover đầy đủ. **Toàn #41 chưa hoàn thành; gate khảo sát mẫu ĐÓNG**, không phải tuyên bố issue đã CLOSED. Không đọc testcase/corpus để hoàn thiện catalog này.
- Không lưu PII, tên/ID nhân sự thật, cookie/token/credential, record hợp đồng hoặc raw khách hàng. Các option công khai phi cá nhân có thể chép; catalog nhân sự chỉ giữ shape/scope/trạng thái coverage.

### Ma trận kiểm chứng hiện tại — 20/10/2026, sau đăng nhập thủ công

| Bề mặt | Quan sát thực tế | Kết luận được phép |
|---|---|---|
| Empty quick-create authenticated | 1 form, 2 section; **17 trường ngữ nghĩa** quan sát DOM | Không đếm raw `<input>` để suy số trường; có editor, hidden input và textarea nội bộ |
| Required/default/state | **7 label có dấu required**; 17 control nghiệp vụ không disabled/readOnly; status `DACONGCHUNG`, ngày `20/10/2026`, trường khác rỗng | Không có HTML `required`/`aria-required`; chưa thử enforcement client/server |
| Sáu widget catalog | Status **3**, nhóm **13**, loại tài sản **12**, title **5**, CCV **3**, thư ký **5** option | Đủ option hiện render trong phiên, không phải tổng DB/toàn đơn vị; §5 giữ list phi cá nhân và proof |
| Scope/pagination | Mỗi remote catalog một GET lúc mount; không quan sát query paging/`donviId`; số `props.options` khớp DOM | Chưa biết server chọn scope theo quyền/đơn vị thế nào hoặc có tổng ngoài response |
| Public static assets + repo | Inventory **17 fields, 7 required tĩnh, 6 catalog widgets**; mapping source-level | Không chạy app/parser/build/test hoặc thay schema/runtime |
| Form API / lưu | Không submit/upload/prime; không gọi ghi DB | Không capture request submit, không chứng minh backend persistence hoặc Lưu thành công |

**Lịch sử trước đăng nhập, cũng ngày 20/10/2026:** root/direct quick-create chuyển `/dang-nhap`; browser/relay lúc đầu chưa đọc được form (**0 field DOM authenticated, 0 catalog authenticated đầy đủ tại thời điểm đó**). Public GET nhóm/loại tài sản trả **403**; title GET không scope trả **200 `items=[]`**; nhân sự chưa được gọi. Đây là mốc static audit, **không còn là coverage hiện tại** và không chứng minh catalog rỗng. Public module 926 đã cho 3 status static; bằng chứng live sau đó xác nhận list đang render.

**Coverage còn thiếu:** enforcement required; form state/submission conversion object↔ID; scope server/unit/global và tổng DB ngoài response; catalog refresh sau mount/save; nhập tiền/rounding; giới hạn file/editor. Chưa biết portal DB/schema hoặc persistence. Các list §5 chỉ đầy đủ cho option được cung cấp/render trong phiên authenticated này.

## 2. Nguồn website bền vững và cấu trúc đọc

Các URL W1–W5 là nguồn public được lấy 20/10/2026; **A1** là audit authenticated read-only sau đăng nhập thủ công cùng ngày. Số module là locator trong bundle minified, không bịa line code chưa có. Khi hash URL đổi, đọc lại route/module thay vì mặc định module ID còn giữ.

| Mã | URL / locator | Nội dung dùng làm bằng chứng |
|---|---|---|
| W1 | <https://congchungnamdinh.ninhbinh.gov.vn/static/js/11.df7d9ede.chunk.js> · module **1517** | Schema quick-create, label/required/default/editor `D`; **977** chi phí; **926** status; **930** service submit; **772/773/779/803/910/911/927** hỗ trợ form |
| W2 | <https://congchungnamdinh.ninhbinh.gov.vn/static/js/app.e07578fa.chunk.js> · route `QUICK_CREATE → 1517` | Quyền `CREATE_HOSO`; modules **638/642/650/654/655/656/678/700/757/972** wrapper/widgets; **647** prefix API |
| W3 | <https://congchungnamdinh.ninhbinh.gov.vn/api/dm/nhomhopdong> | GET 403; không có list |
| W4 | <https://congchungnamdinh.ninhbinh.gov.vn/api/dm/loaitaisan> | GET 403; không có list |
| W5 | <https://congchungnamdinh.ninhbinh.gov.vn/api/danh-muc/TEN_HOP_DONG> | GET không scope: 200, `items=[]`; không là list của đơn vị |
| A1 | <https://congchungnamdinh.ninhbinh.gov.vn/ho-so-cong-chung/tao-moi-nhanh> · authenticated empty form, 20/10/2026 | DOM 17 trường; state/default/required markers; 6 widget catalogs; props↔DOM counts, query/pagination và thử dependency có hoàn tác |

SHA-256 của **text asset đã fetch, encode UTF-8** (không claim raw transfer bytes):

- W1: `0c24bfb433769d9bb6ad70c5c8920ffd04a94ebc572ff8b77e3371641a8fc1ba`.
- W2: `97553b476fa4120979a3c9c6b2e4e60043f74bbf0faae06bc703ef01595dd637`.

Phần thiết yếu được chép an toàn trong tài liệu này, không phụ thuộc file tmp hoặc bundle còn truy cập được. Evidence chi tiết cục bộ tùy chọn: `_bmad-output/tmp/namdinh-website-sot/live-authenticated-audit-20261020.json` và `.md` (**A1, bản hiệu chỉnh t3**: tách semantic/raw DOM, widget/form/POST, request context/scope, thêm title item IDs); `website-evidence.json`, `website-handoff.txt`, `public-static-schema-excerpt.txt`, `public-widget-submit-excerpts.txt` (public/static). Không dùng chúng thay catalog bền vững; account/đơn vị/nhân sự/secret đã loại khỏi bản ghi an toàn.

### Cấu trúc bề mặt được khảo sát

1. Root → `/dang-nhap`: username/password + Đăng nhập (selector repo `uploader_selectors.py:8-21:LOGIN_SELECTORS`). User tự đăng nhập; không thu thập credential hoặc điều khiển bước đăng nhập.
2. Sau đăng nhập, quick-create `/ho-so-cong-chung/tao-moi-nhanh` đã quan sát empty form (**A1**); adapter dùng cùng path (`playwright_uploader.py:87-88:LOGIN_PATH,CREATE_PATH`; W2). Không inventory menu authenticated hoặc toàn bộ trang khác của portal.
3. Quick-create gồm **Thông tin hồ sơ** (13 trường (kể cả attachment/ghi chú)) và **Chi phí** (4 input tiền). Wrapper Chi phí dùng lại `name:"ghichu"` với `isFieldBuildIn:true`: **không phải input ghi chú thứ hai**. Tổng chi phí chỉ hiển thị.
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

## 4. Inventory đầy đủ 17 trường quick-create

**R** là required trong W1 module 1517; A1 xác nhận đúng 7 **label marker**, không phải HTML attr/enforcement. Bảng giữ default/mapping **static** và selector repo; đối chiếu DOM/default live tại §4.2. CSS ID có dấu chấm phải escape `\.`. Các editor repo dùng XPath `Field-container` có label → `[contenteditable='true'][1]` (`uploader_selectors.py:103-132`). W1 không định nghĩa dependency title→group/group→asset rõ ràng; các phép chọn giới hạn ở §5 không chứng minh mọi runtime path độc lập.

| # / field website / nhãn | Widget · R · default tĩnh | Extraction → canonical/đối tượng → DB/wire thực | App form key / selector / source |
|---|---|---|---|
| 1 `hopdong.tenhopdong` · Tên hợp đồng | freeSolo autocomplete · R · không ghi default | detect title `build_payload:4856,4932` → **C tenvanban** → Case JSON; text nguồn, không enum Notary | `ten_hop_dong` / `#hopdong\.tenhopdong` · selectors:41-48 |
| 2 `hopdong.tinhtrang` · Tình trạng | MUI select · R · `DACONGCHUNG` | Không extraction/canonical; **P** app label “Đã công chứng”; không map `inheritance_cases.trang_thai` draft/locked | `tinh_trang` / `#hopdong\.tinhtrang` · 64-70; defaults:3 |
| 3 `hopdong.ngaycongchung` · Ngày công chứng | date picker · không R · ngày hiện tại `yyyy-MM-dd`, display `dd/MM/yyyy` | `find_ngay_cong_chung` → **C ngaycongchung**, ISO/null `build_payload:4930-4936`; boundary `case_portal_projection:4845-4852` → DD/MM/YYYY. Ngày website mặc định không là ngày nguồn | `ngay_cong_chung` / `input[placeholder='dd/mm/yyyy']` · 49-55 |
| 4 `nhomhopdongId` · Nhóm hợp đồng | remote autocomplete · R | `guess_nhom_hd(title):1119-1129` → **C nhomhopdong** label → Case JSON; static dự kiến ID nhưng A1 chỉ xác nhận widget object, form/POST chưa reconcile; app chưa lưu catalog ID | `nhom_hop_dong` / `#nhomhopdongId` · 71-78 |
| 5 `loaiTaisan` · Loại tài sản | remote autocomplete, object · R | `guess_loai_tai_san:1176-1202` → **J web_form.loai_tai_san** label; discriminator portal chưa canonical Asset cutover, không cột DB Upload/approved shared enum | `loai_tai_san` / `#loaiTaisan` · 79-86 |
| 6 `hopdong.sohopdong` · Số công chứng | text · không R tĩnh | `find_so_cong_chung`/scan + normalize `build_payload:4923,4935` → **C socongchung**; registry.contract_no vẫn scan/reference | `so_cong_chung` / `#hopdong\.sohopdong` · 56-63 |
| 7 `hopdong.congchungvien.id` · Công chứng viên | remote autocomplete · R | regex nguồn `build_payload:4929,4937` hoặc lựa chọn prepare rõ ràng → **C congchungvien** tên/null → Case JSON; ID website không là FK Notary | `cong_chung_vien` / `#hopdong\.congchungvien\.id` · 87-94; builder:781-792 |
| 8 `hopdong.thuky` · Thư ký | freeSolo autocomplete · không R | extraction `thuky=null` `build_payload:4938`; input prepare → **C thuky** tên/null → Case JSON; widget string, form/POST chưa quan sát | `thu_ky` / `#hopdong\.thuky` · 95-102 |
| 9 `hopdong.nguoiYeucauCongchung` · Thông tin người yêu cầu công chứng (ghi sổ công chứng) | CKEditor HTML · không R | `build_payload` → `_requester_projection` personfacts + mortgage-only sourced bankblock → existing **J `web_form.nguoi_yeu_cau`**, JSON save/fresh queue/builder preserves exact projection; không lookup override. Không toàn canonical Person/parties cutover (§6) | `nguoi_yeu_cau` / label XPath · uploader_selectors103–112; `playwright_uploader.build_upload_form_data` |
| 10 `hopdong.duongsu` · Đương sự | CKEditor HTML · R | `raw.ben_a/b` → `_fmt_duong_su_by_kind:4749-4765` → **J web_form.duong_su**, raw_text/entity_lines ghép; Person/parties chưa cutover | `duong_su` / label XPath · 113-122 |
| 11 `hopdong.taisan` · Tài sản | CKEditor HTML · R | `_find_tai_san_by_kind:1007-1116` → **J web_form.tai_san** text; song song `raw.danh_sach_thua_dat` `build_payload:4962-4973`. Asset chưa cutover; text không thay các field chuẩn | `tai_san` / label XPath · 123-132 |
| 12 `hopdong.fileHopdong` · Văn bản hợp đồng | upload + preview · không R · accept `.doc,.docx,.pdf` | **F** `raw.file_goc` → JSON + registry.file_path; không canonical business column | `file_hop_dong` / `#hopdong\.fileHopdong`; `FORM_FIELD_ORDER` → `_upload_file`; preSave selection, không proof backend (§8) |
| 13 `ghichu` · Ghi chú | textarea rows=3 · không R | **Policy bỏ qua**; không extraction/canonical storage. Không dùng Notary `ghichu` làm bucket cho trường khác nghĩa | Không builder key/selector/fill order; giữ default portal |
| 14 `chiphi.phicongchung` · Phí công chứng | money autocomplete · không R | **Policy bỏ qua**; chưa canonical/DB-wire cho phí trong tuyến Upload | Không builder key/selector/fill order; không ghi 0/clear |
| 15 `chiphi.thulaoCongchung` · Thù lao công chứng | money autocomplete · không R | **Policy bỏ qua**; chưa canonical/DB-wire cho thù lao trong tuyến Upload | Không builder key/selector/fill order; không ghi 0/clear |
| 16 `chiphi.phiDvNgoaicongchung` · Phí dịch vụ ngoài công chứng | money autocomplete · không R | **Policy bỏ qua**; không extraction/canonical/DB-wire; W1 module 977 | Không builder key/selector/fill order; không thêm schema |
| 17 `chiphi.phikhac` · Phụ phí khác | money autocomplete · không R | **Policy bỏ qua**; không extraction/canonical/DB-wire; W1 module 977 | Không builder key/selector/fill order; không thêm schema |

Chi phí dùng currency `đ`, phân nhóm chữ số bằng khoảng trắng; thiếu thành 0 **chỉ trong công thức tổng website**, không là policy phí app đã duyệt. `fileLimit:10` truyền cho editor Đương sự/Tài sản không chứng minh editor enforce 10 file. Preview attachment `viewOnly:true` không đồng nghĩa input upload readonly; inherited maxFileSize default 10 chưa kiểm độc lập đơn vị. Không upload để suy giới hạn.

**Derived/hidden không tính thêm input:** module 977 cộng bốn khoản vào `chiphi.tongphi`; wrapper hiển thị `chiphi.total` / “Tổng chi phí” readonly; hidden Field lại viết **`phicongchung.tongphi`** và wrapper hidden trả null. Giữ nguyên discrepancy tên này; không “sửa đúng” bằng doc/schema. Không extraction/Case key/DB column cho tổng; không tự duyệt persist dữ liệu suy ra.

Required tĩnh đúng **7**: Tên hợp đồng, Tình trạng, Nhóm hợp đồng, Loại tài sản, Công chứng viên, Đương sự, Tài sản. A1 thấy đúng 7 label `Mui-required` + dấu sao, **không HTML `required` hoặc `aria-required`**, chưa submit/prime để thử enforcement. **Ngày/Số công chứng không đánh dấu required**; app critical list khác (`identify_missing_fields:810-812` gồm title, number, group, asset type, asset text). Rule date static cho trống, có giá trị thì parse `yyyy-MM-dd`, lỗi “Định dạng ngày không hợp lệ”. CKEditor emits HTML; chưa xác minh semantic-empty HTML. Global viewOnly có thể disable; A1 chỉ xác nhận 17 control nghiệp vụ của empty quick-create hiện không disabled/readOnly.

### 4.1 State trước Lưu → request API (public source, chưa submit)

Đường client W1 **module 1517 `onSubmit(t)` → module 930 export `b`/symbol `u(t)` → W2 module 647 → `POST /api/hoso/nhap-nhanh`, `data:t`**. Generic Form W2 **655** gọi callback bằng form state, không có bước map lại các tên field được thấy. Trích đúng phần quyết định:

```javascript
// W1 1517 — callback quick-create
onSubmit:function(t){return Object(l.b)(t).then(/* thông báo + điều hướng */)}
// l = n(930); W1 930 export b -> u
u=function(t){return Object(a.a)("hoso/nhap-nhanh",{method:"post",data:t})}
```

Đường nối source của từng hàng §4 sang API dùng **name path của form**, không phải tên canonical app. Danh sách sau là **diễn giải static**, chưa capture form state/body; A1 chỉ thấy widget props, nên giả thuyết ID cho nhóm/CCV **chưa được reconcile** với whole-object widget value:

- `hopdong` khai báo `tenhopdong` (label/free text), `tinhtrang` (enum), `ngaycongchung` (ISO/null/invalid-date marker trước validation), `sohopdong` (text), `congchungvien.id` (static dự kiến ID), `thuky` (label/free text), `nguoiYeucauCongchung/duongsu/taisan` (HTML), `fileHopdong` (giá trị attachment do upload control quản lý; **shape file metadata/persistence backend chưa xác minh**, không gửi local path như cột business).
- Root `nhomhopdongId` static dự kiến ID; root `loaiTaisan` static object từ autocomplete. Root `ghichu` là textarea text. **Giá trị form state/POST của mọi autocomplete vẫn UNKNOWN**, không dùng path `.id` hoặc object prop để tự kết luận conversion.
- `chiphi` chứa bốn field tiền đúng tên ở §4, và `tongphi` do module 977 tính. Money widget W1 **927** emits string input; numeric coercion unary `+` trong tổng không chứng minh backend currency type/rounding hoặc schema monetary amount approved.
- `chiphi.total` là wrapper hiển thị, không chứng minh có field value trong request. Hidden `phicongchung.tongphi` khác spelling: không chứng minh backend lưu path đó. JSON request thực tế chưa được capture.

**Không có bằng chứng client** chuyển `nhomhopdongId` thành `hopdong.nhomhopdong.id` hoặc `loaiTaisan` thành `hopdong.loaitaisan.id`; tuyệt đối không dùng các biến đổi giả định đó làm mapping. Initial edit values có đoạn `nhomhopdong: f.nhomhopdong?.id` (W1 1517), khác input `nhomhopdongId`; ghi nhận chênh lệch, không tự sửa/diễn giải là preSave conversion.

W1 callback sau promise thành công hiện thông báo “Đã lưu thành công” rồi điều hướng list; đó là hành vi **frontend source**, không evidence đã chạy thành công hoặc quyền app suy Save. Backend portal DB/schema và accepted body/attachment vẫn **chưa biết**, không đồng nhất với DB registry hoặc Notary. W1 module 930 còn khai báo GET `hoso`, GET/PUT/DELETE `hoso/:id`, POST `hoso`, GET `hoso/export`, GET `hoso/export-so-cong-chung`; chỉ catalog quick-create POST ở trên thuộc luồng form này, không thực thi endpoint ghi.

### 4.2 Đối chiếu DOM/default live — A1, 20/10/2026

- **17 trường ngữ nghĩa = 13 input-backed + 1 textarea Ghi chú + 3 CKEditor**, không phải tổng raw DOM. Raw có **16 `<input>`** (13 nghiệp vụ, gồm hidden native input của status, + 3 CKEditor hidden image inputs) và **2 `<textarea>`** (1 nghiệp vụ + 1 MUI artifact); không cộng các tầng đếm với nhau. 1 form, section “Thông tin hồ sơ”/“Chi phí”. Ngoài status/ngày, các control nghiệp vụ rỗng; cả 17 không disabled/readOnly trong phiên này.
- Tên hợp đồng/Thư ký: autocomplete **freeSolo**; Nhóm/Loại tài sản/CCV: autocomplete remote; status là **`div[role=combobox]`** tại `#hopdong\.tinhtrang` cùng hidden `.MuiSelect-nativeInput`, không native select hiển thị. Default status `DACONGCHUNG`.
- Ngày: input `type=tel`, placeholder `dd/mm/yyyy`, **không id**; hiển thị `20/10/2026`, nút calendar. Đây là default website ngày khảo sát, không dữ kiện trích từ Word.
- 3 CKEditor HTML (người yêu cầu/Đương sự/Tài sản) đều rỗng; file input single, accept `.doc,.docx,.pdf`, chưa thử upload. Ghi chú là textarea `rows=3`; textarea hidden readonly `aria-hidden=true`, cao 0 bên trong là artifact MUI, không input nghiệp vụ thứ 18.
- Cả **4 ô tiền** là autocomplete freeSolo, mỗi ô **0 option**, adornment `đ`, default rỗng. “**Tổng chi phí: 0 đ**” là text **`h5`**, không input; không suy 0 là policy phí được duyệt.
- Nút `Lưu hợp đồng` có `type=submit`, `Hủy bỏ` có `type=button`; không click. A1 chỉ thấy **widget props**: nhóm/asset/CCV là object option, title/thư ký là string label/free text. **Underlying form state và POST của cả 5 autocomplete đều UNKNOWN**. Static ID interpretation cho `nhomhopdongId`/`hopdong.congchungvien.id` chưa reconcile; không tự khẳng định widget object là submitted object hoặc đã chuyển ID.

## 5. Sáu catalog: nội dung, scope và ID/label

**Phạm vi chung A1:** website `nam_dinh`, empty quick-create authenticated ngày **20/10/2026**, danh sách được cung cấp/render trong **phiên hiện tại**. Không giữ định danh account/đơn vị. “Đầy đủ” dưới đây nghĩa là đủ option của widget đã quan sát, **không phải từ điển bất biến, tổng DB hoặc coverage mọi đơn vị/quyền**. IDs là technical website scope, không approved canonical business fields/FK.

| Catalog website | Nguồn / shape / lớp giá trị | Live state và count A1 | Mapping app và gap |
|---|---|---|---|
| Tình trạng | W1 module 926, enum string→label; A1 `div[role=combobox]` | **3**, chọn `DACONGCHUNG`; label required; enabled | app chọn label, không lưu enum vào Case; không map Notary status |
| Tên hợp đồng | `/api/danh-muc/TEN_HOP_DONG`; item có `id,value,label,danhmucId,donviId`; freeSolo label/free text | **5**, rỗng, label required, enabled; `value==label` | **C `tenvanban`** title nguồn, app `ten_hop_dong`; không ép enum Notary hoặc lưu catalog ID như canonical |
| Nhóm hợp đồng | `/api/dm/nhomhopdong`; `id` numeric, `tennhom`, `vaitroDuongsu`; static dự kiến ID, chưa reconcile | **13**, rỗng, label required, enabled; widget `props.value` whole option object, form state/POST unknown | **C `nhomhopdong`** label theo site; root form name `nhomhopdongId`; không approved local ID business column |
| Loại tài sản | `/api/dm/loaitaisan`; `id` numeric, `ten`, `nhomTaisanId`, `thuoctinh`; source `isValueObject:true` | **12**, rỗng, label required, enabled; object widget | **J `web_form.loai_tai_san`** label; root `loaiTaisan` object source, không canonical Asset record/enum |
| Công chứng viên | `/api/user/congchungvien`; option `id/hoten`, không freeSolo | **3**, rỗng, label required, enabled; chỉ shape/count, không tên/ID nhân sự | **C `congchungvien`** tên/null. Static path `hopdong.congchungvien.id` dự kiến ID; live widget prop whole object; form state/POST **UNKNOWN**, hai lớp chưa reconcile |
| Thư ký | `/api/danh-muc/THU_KY`; shape option label, freeSolo label/free text | **5**, rỗng, không label required, enabled; chỉ shape/count | **C `thuky`** tên/text; không tự thêm staff FK hoặc lưu danh tính vào SOT |

### 5.1 Tình trạng — 3 option

| Value string | Label |
|---|---|
| `DANGXULY` | Đang xử lý |
| `DACONGCHUNG` | Đã công chứng |
| `HS_HUY` | Hủy bỏ |

Default `DACONGCHUNG` được xác nhận live, không là dữ kiện trích xuất hoặc trạng thái Notary.

### 5.2 Nhóm hợp đồng — 13 option, theo thứ tự A1

| ID number | `tennhom` / label chính xác | `vaitroDuongsu` |
|---|---|---|
| 1 | Thuê - Mượn tài sản | Chuẩn A/B |
| 2 | Di chúc | `null` |
| 3 | Cầm cố - Thế chấp - Vay | Chuẩn A/B |
| 5 | Ủy quyền | `null` |
| 8 | Đặt cọc | `null` |
| 9 | Thoả thuận - Cam kết | Chuẩn A/B |
| 10 | Góp vốn - Hợp tác | Chuẩn A/B |
| 11 | Chuyển nhượng - Mua bán | Chuyển nhượng A/B |
| 12 | Tặng, cho tài sản | `null` |
| 14 | Khác | `null` |
| 17 | Thừa kế (khai nhận - phân chia di sản thừa kế ) | `null` |
| 16 | Từ chối nhận di sản thừa kế | Chuẩn A/B |
| 18 | Phụ lục hợp đồng - văn bản sửa đổi | `null` |

`vaitroDuongsu` là metadata website **array hoặc null**, không canonical parties/Diagram role. Giữ nguyên khoảng trắng trước `)` ở label ID 17. Mỗi array gồm hai object theo thứ tự:

- **Chuẩn A/B** (IDs **1,3,9,10,16**): `{label:"Bên A",vaitroValue:"Bên A",vaitroCode:null,required:false}`, `{label:"Bên B",vaitroValue:"Bên B",vaitroCode:null,required:false}`.
- **Chuyển nhượng A/B** (ID **11**): `{label:"Bên A",vaitroValue:"Bên Chuyển nhượng",vaitroCode:null,required:false}`, `{label:"Bên B",vaitroValue:"Bên Nhận chuyển nhượng",vaitroCode:null,required:false}`.
- **Null** ở IDs **2,5,8,12,14,17,18**; không đổi null thành array rỗng hoặc tự gán vai trò.

### 5.3 Loại tài sản — 12 option, theo thứ tự A1

| ID number | `ten` / label chính xác |
|---|---|
| 1 | Đất đai có tài sản |
| 2 | Đất đai không có tài sản |
| 3 | Ô tô |
| 4 | Xe máy |
| 5 | Tàu, thuyền |
| 7 | Sổ tiết kiệm |
| 11 | Tài sản khác |
| 9 | Thẻ ATM |
| 10 | Chứng khoán |
| 12 | Cổ phần |
| 13 | Cổ phiếu |
| 14 | Công việc |

Mọi option A1 có `nhomTaisanId:null`, `thuoctinh` kiểu object; nội dung đầy đủ của object chưa được catalog ở đây. “Công việc” là label website, không đối tượng nghiệp vụ thứ tư. **`loaiTaisan`** là discriminator/catalog object portal; **`hopdong.taisan`/app `tai_san`** là HTML mô tả tài sản; **canonical Asset/land_rows** là dữ liệu có cấu trúc khác. Không đồng nhất với `loai_gcn/loai_so`, loại đất hoặc suy đã hỗ trợ DB/extraction mọi option.

**Owner W05, 20/10/2026:** giữ loại **ID 1 — Đất đai có tài sản** (thông thường
là nhà ở trên đất). Chưa có hợp đồng mẫu để rút rule regex không có nghĩa loại
này không tồn tại hoặc bị loại khỏi nghiệp vụ. Hiện thiếu nguồn/rule chi tiết
nhà/công trình; không tự dựng schema/regex hoặc đọc mẫu khi gate còn đóng.

### 5.4 Tên hợp đồng — 5 option, freeSolo

| Item ID number | `value` = `label` (string, đúng chính tả A1) |
|---|---|
| 497 | Hợp đồng chuyển nhượng quyền sử dụng đất |
| 498 | Văn bản cam kết tài sản riêng |
| 499 | Hợp đồng tặng cho quyền sử dụng đất |
| 500 | Hợp đồng thế chấp |
| 501 | Hợp đồng uỷ quyền |

Năm item có cùng **`danhmucId:5`** và mỗi item có `donviId` (định danh đơn vị không lưu). `danhmucId` là ID danh mục chung, **không phải ID riêng từng option 497–501**. FreeSolo cho phép text ngoài 5 gợi ý; không dùng list này làm enum `tenvanban` hoặc synonym của `nhomhopdong/loaivanbannhandien`. ID danh mục/option không thay canonical title text; form state/POST chưa được quan sát.

### 5.5 Scope, completeness/pagination và dependency — A1

- Mỗi remote catalog có **1 GET lúc mount**; các request app đã capture **không có query params**, gồm cả `page/pageSize/limit/donviId`. Static wrapper có đường truyền `donviId` cho title/thư ký, nhưng không dùng source đó để bịa query live; thiếu query cũng **không chứng minh** server scope global hay đơn vị.
- Response được quan sát là arrays, không paging metadata; không `hasMore/onLoadMore` hoặc UI “xem thêm”. Listbox MUI không virtualize; **props.options.length = DOM `[role=option]`** lần lượt nhóm **13/13**, asset **12/12**, title **5/5**, CCV **3/3**, thư ký **5/5**. Nhóm scrollHeight **550** > clientHeight **367** nhưng đủ 13 option nằm trong DOM. Status có đủ **3** option live. Đây là proof đầy đủ **rendered list của phiên**, không proof server-total.
- Cookie-only page-context probes (không app headers) là lớp riêng với request của app: nhóm/asset **403**; title **200 `items=[]`**; thư ký **21** item so với UI **5**; CCV không trả JSON. Không gộp probe với list UI hoặc suy 21 là tổng staff có thẩm quyền. Khác request context đã quan sát, nhưng **auth mechanism và scope rule UNKNOWN** (không inspect header/token); không suy server-scoping hoặc nguyên nhân/filter từ khác biệt đó.
- Thử chọn rồi hoàn tác: nhóm **Di chúc** → asset vẫn 12, không field khác đổi; asset **Ô tô** → nhóm vẫn 13; title **Hợp đồng thế chấp** → không auto-fill nhóm/asset/CCV, ngày/status giữ; nhóm **Thuê - Mượn tài sản** → chưa xuất hiện role UI, số control không đổi. Không suy mọi tổ hợp/luồng đều không dependency hoặc `vaitroDuongsu` không bao giờ được dùng.
- Sau thử, form về rỗng với status `DACONGCHUNG`, ngày `20/10/2026`; không Lưu/submit/prime/upload. Scope unit/global/quyền, tổng DB ngoài arrays, refresh và body submit vẫn **UNKNOWN**.

### 5.6 Boundary của adapter hiện tại

**Adapter label boundary:** `playwright_uploader.py:get_field_value_candidates,field_value_matches,_fill_dropdown,_select_dropdown_option` chọn native select bằng label; custom status mở combobox rồi click role option có label chính xác; title/thư ký freeSolo nhập + blur nếu không có option; remote phải chọn option, không fallback option đầu/Enter/page text hoặc direct API ID assignment. Staff verify folded equality; field khác folded substring, nhưng filler failure vẫn thành partial kể cả visible text khớp. Không là bằng chứng ID đúng/backend chấp nhận. `FIELD_VALUE_ALIASES` giữ các biến thể nhóm có sẵn, không thêm alias/catalog mới.

**Nguồn event freeSolo (W1 module 772, đọc lại public 20/10/2026):** quick-create dùng cùng `F.a=n(772)` cho title/thư ký. Wrapper khai báo `freeSolo:!0`, `onInputChange:function(t,e){return r(e)}`; chọn option gọi `onChange:function(t,e){return r(e?e[g]:void 0)}` (`g` mặc định `"label"`, `r` là prop `onChange` của field). Do đó typing đã đi qua callback được source định nghĩa, blur/Tab không cần Enter hoặc Lưu để commit free text. Đây là evidence static cho cơ chế adapter; **không** capture live form state/POST hoặc chứng minh backend accepted.

`_read_dropdown_options:1384-1412` đọc label, bỏ placeholder/dedup; `fetch_staff_options:1414-1427` cache **labels** Công chứng viên/Thư ký. Không có local authoritative IDs; cache không thay list live hoặc approve nhân sự. Default CCV trong code chỉ prefill legacy, không dữ kiện extracted: `build_upload_form_data:790-792`; historical JSON bằng default không được nâng thành fact (`case_from_payload:4838-4841`). Không chép tên default cá nhân vào SOT.

`guess_loai_tai_san:1176-1202` có labels đất có/không tài sản, xe, tàu/thuyền, sổ tiết kiệm, cổ phần/cổ phiếu/chứng khoán/thẻ ATM/khác; `guess_nhom_hd:1119-1129` trả nhóm từ title hoặc Khác. Đây là **candidate output của engine**, **không phải danh sách dropdown Nam Định đã xác minh**. Fixture `shell/test/fixtures/upload_portal.py` là portal giả; native select/options mẫu không được dùng làm bằng chứng website.

## 6. Người / Tài sản / vai trò Hồ sơ trong ba editor

### 6.1 Người và parties

Nguồn `raw.ben_a/b.nguoi[]` giữ thứ tự, `entity_lines` là provenance tổ chức/đầu mục. Requester hiện đi qua `contract_extract._requester_projection` (3040), `_requester_person_facts` (2984), `_mortgage_bank_spans` (3002), `build_payload` (4969); source refs kỹ thuật giữ text/spans. `batch_scan.save_output_json` lưu payload, `playwright_uploader.load_upload_queue` (470) đọc và `build_upload_form_data` (540) giữ nguyên projection cho editor. Lookup/firstperson formatter/override cũ đã bỏ khỏi đường requester. `_format_person_block`/`_fmt_duong_su_by_kind` còn là hiện trạng trình bày Đương sự riêng, không bằng chứng canonical parties đã cutover.

**Policy đích R06 — đáp án #43, owner 20/10/2026:** trong requester Nam Định/
Upload, lấy mọi **cá nhân sống thuộc Bên A, Bên B, người đại diện theo ủy quyền**;
không đưa người chết, công chứng viên hoặc nhân viên vào output này. Không suy
thêm thân nhân chỉ được nhắc. Mỗi identity xác nhận một lần, giữ thứ tự nguồn;
không lookup/ưu tiên B/người đầu hoặc lời quan hệ/chức vụ/tư cách. Đây là phạm
vi output, không xóa Person chết, Stage, raw, lịch sử hoặc metadata nhân sự.
Ngân hàng ở hợp đồng thế chấp được hiện **cả cụm** nhưng không là Person;
**BANKMODE đã trả lời: “app tự lấy”.** App lấy/điền cả cụm ngân hàng thế chấp
từ nguồn vào `web_form.nguoi_yeu_cau` hiện có, persist payload JSON → queue →
editor requester. Không Person/key canonical/bảng pháp nhân mới. Cụm chỉ
ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/căn cứ ủy quyền có nguồn,
tại vị trí nguồn trong requester đầy đủ; không lặp đại diện đã ở trong cụm.
Không tài sản/giá/cọc/vay/lãi/thanh toán/thời hạn nghiệp vụ. Giữ raw/person arrays/
provenance/history; cá nhân khác chuẩn, không alias auto/job/kinship/role prose.
Persistence projection text này hợp lệ, không normalized cutover #41. Kế hoạch
trước code ở #43 plan §6.1; bounded proof/fresh review CLEAN, #43 phân tích done; #41/gate mẫu không mở.
Lookup/firstperson/raw formatter ở trên là baseline cũ, không policy đích.
Requester không lọc bằng tag A/B đã gán. Cá nhân sống tham gia văn bản một bên/
đại diện theo ủy quyền vẫn vào requester khi không gán hoặc đang conflict A/B;
chỉ phần nhãn nhóm bị ảnh hưởng chờ xác nhận, không phát sinh owner gate mới.

**Changelog/proof bank-auto 20/10/2026:** engine
`2026-10-20-requester-bank-projection` lấy sourcebank spans chỉ mortgage,
normal personfacts source-order; JSON save → fresh queue → builder → actual
local contenteditable `_fill_editor` đạt, representative một lần, Save=0/
Submit=0/about:blank. Không portal/network hoặc chạm Chrome đã đăng nhập.
Final isolated five-suite sau bỏ hai test fixture ngoài repo và forwarding echo:
**250 passed,0 skipped,28 subtests passed**, gồm cả5 browser cases với
process-only CASE_FIELDS_CHROMIUM trỏ Chromium headless riêng; không Chrome user.
Privacy caveat: lượt full suite trước còn hai test hardcoded fixture owner-local;
khả năng đã truy cập fixture là **[INFERENCE] từ skip count**, không được gọi
lượt đó wholly synthetic. Không kiểm tra lại file, không biết/claim nội dung
hoặc corpus coverage; chỉ xóa hai method test, giữ nguyên mọi file/fixture.
Baseline/result/expectations JSON tmp là bằng chứng phụ; quy tắc/kết quả này
lưu bền tại SOT/#41. Throwaway script và workdir tổng hợp đã gỡ.
Fresh bank-auto review CLEAN/Ticket PASS; final semantic smoke parser8b503e7f/uploader930f1fa5; projection không toàn canonical #41.

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
| `ten_goi_khac`, `entity_lines`, vai trò requester/Bên A/Bên B | R05 không tự điền/không mở rộng chuẩn alias; entity/quan hệ chưa canonical cutover | Giữ raw/lịch sử; alias nếu cần user điền tay, không nối vào `ten`; pháp nhân khác nhập tay, ngân hàng thế chấp app tự lấy cụm nguồn theo §6.1; nhóm/quan hệ xem D05–D07 |
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

### 6.3 Pháp nhân và cụm trường phụ theo website — chưa chọn cấu trúc

**Hiện trạng:** ba editor `nguoi_yeu_cau`, `duong_su`, `taisan` vẫn nhận chuỗi
trình bày dựng từ nguồn; Person/Asset/parties chưa canonical cutover. Chưa có
bảng pháp nhân, chưa có trường canonical lưu cụm. `entity_lines` có thể chứa
tên tổ chức nhưng không tự là Người và không được gán loại pháp nhân cho Person.

**Owner 20/10/2026 chốt:** pháp nhân **không đưa vào Người**; policy nhập tay
chung có ngoại lệ ngân hàng thế chấp bên dưới. Bảng riêng tương lai **chưa duyệt schema/
build**. Hồ sơ thế chấp là trường hợp mặc định có pháp nhân; nguồn thường nêu
ngân hàng/chi nhánh/đại diện; loại khác ít xảy ra. Sự có mặt đó không cho phép
tự bịa tên, người đại diện hoặc default party; chỉ dùng dữ kiện nguồn nêu rõ;
pháp nhân khác giữ nguồn và không bị âm thầm bỏ mất hoặc tự xếp loại.

**Ngoại lệ output #43 — BANKMODE “app tự lấy”:** chỉ thế chấp, app lấy toàn
cụm nguồn ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/ủy quyền vào requester
đầy đủ theo §6.1, không Person/canonical legal field/bảng hoặc default.
Policy nhập tay chung không còn áp cho cụm được duyệt này; pháp nhân khác giữ nguyên.

**Owner 20/10/2026 cho phép có điều kiện** thêm một trường giữ cả cụm khi cụm
phức tạp, không lặp lại và thuộc một ô nhập của một website cụ thể. Đây không
phải quyết định biến cả ba editor hoặc mọi ô web thành block/trường phụ. Khi
chọn cụm phải xác định website/phạm vi ô, nghĩa nghiệp vụ, lý do không tái dùng
trường canonical đã biết, kiểu lưu và provenance; giữ nguồn. Chỉ hỏi owner khi
có quyết định nghiệp vụ thực sự chưa rõ; chi tiết kỹ thuật do implementation sở
hữu theo contract/rule đã duyệt. Không dùng `ghichu` chung hoặc JSON bag chung
thay trường; raw capture chỉ là provenance, không thay trường nghiệp vụ; không
tự đặt key/tên/kiểu/nhóm/storage; chỉ tự lấy cụm ngân hàng theo §6.1. Cụm có thể
là trường riêng theo ô; phần tái dùng được vẫn map canonical, không mặc định
coi cụm là orphan. Ngoại lệ requester dùng projection có sẵn, không duyệt thêm
canonical field/DB column hoặc A09.

**Quan hệ Người–Tài sản–Hồ sơ:** nhiều người/nhiều tài sản chưa chọn model,
cardinality, quan hệ/FK hay bảng nối. D06 và D07 chuyển **một issue riêng
[#43](../../backlog/spike-case-people-assets-relationships.md)**, xử lý ngay sau
làm rõ các ô §7; không chờ toàn #41 hoàn thành, không phụ thuộc #42. #41 dùng
kết quả cho cutover quan hệ; 16ca/Q1/Q2/BANKMODE đã bàn giao. Runtime slice đã giao không đổi gate mẫu.

<a id="owner-review"></a>
## 7. Ma trận owner rà soát — quyết định 20/10/2026 và phần còn làm rõ

**Phạm vi “mọi cụm của web” ở lượt này:** toàn bộ **17 trường quick-create Nam Định mà uploader dùng**, cộng Tổng chi phí derived; không phải toàn website. Các màn tạo đầy đủ, sửa standard/simple/online và website thứ hai **chưa được audit form**, dù §2 có route static. Không đọc mẫu/corpus mới. A1 là empty form nên chỉ chứng minh **ô nhập**, không chứng minh mọi văn bản có mọi thông tin con dưới đây. Các đơn vị con là phân rã từ extraction/contract/source hiện có, **không phải label con đã thấy trên portal**.

**Cách đọc và trả lời:** `W01…W17` giữ đúng số **#1…#17 ở §4**, không đổi theo thứ tự nhóm; `WΣ` chỉ display derived. `R`, `D`, `A` là mã dòng review dưới W09/W10/W11, **không phải key dữ liệu/schema mới**. Owner có thể trả lời bằng ID và phương án; dòng **ĐÃ CHỐT** không cần duyệt lại. **CHỜ CHỌN** chỉ hỏi nghĩa/phạm vi nghiệp vụ thật sự; không hỏi owner đặt ID, JSON layout, FK hoặc duyệt từng chi tiết kỹ thuật. Khuyến nghị chưa được chọn không là consent/default, không cấp quyền code/schema.

Các cách xử lý dùng trong bảng:

- **Tái dùng chuẩn:** lấy đúng trường canonical đã có, không sao chép thành trường web trùng nghĩa.
- **Dựng hiển thị:** ghép từ dữ liệu chuẩn và tham chiếu/nhóm đã được chốt; renderer của từng website chỉ quyết định trình bày. Khi quan hệ chưa chốt, đây là hướng đề xuất, không giả định đã có model.
- **Cụm riêng theo ô:** dữ kiện tĩnh có nghĩa/nguồn/ranh giới theo một ô Nam Định, không generic bag/ghi chú/blanket raw. Ngoại lệ ngân hàng thế chấp đã chốt dùng projection hiện có §6.1, không thay canonical hoặc suy quan hệ.
- **Nhập tay/sửa tay:** pháp nhân khác ngoài ngoại lệ ngân hàng §6.1, alias nếu cần, lời phức tạp D04 của cá nhân khác; không fallback mọi gap.
- **Bỏ qua:** chỉ scope đã chốt bỏ qua; không âm thầm bỏ các gap khác để báo đủ.

**Hai lớp không được gộp:** **C** đã qua Case JSON/`file_registry.case_json`; **J** là payload JSON lưu file (`output_json_path`), gồm `raw`/`web_form`. **J là persistence projection hợp lệ**, chưa là canonical Người/Tài sản/quan hệ Upload; DB/contract Notary có trường không chứng minh Upload đã ghi nó. Ngân hàng thế chấp app tự lấy qua J → queue → requester editor; pháp nhân khác nhập tay. Phí/Ghi chú bỏ qua, status `DACONGCHUNG`, thời hạn đất giữ, không bóc tài chính/thời hạn nghiệp vụ; #42 độc lập, #41 mở/gate mẫu **ĐÓNG**.

### 7.1 Bao phủ 17 trường và phần derived, theo nhóm công việc

| ID · trường website (số §4) | Nội dung / đường hiện có | Chuẩn sẵn có + Upload thực lưu | Phương án phù hợp | Khuyến nghị và đánh đổi | Owner cần chọn? |
|---|---|---|---|---|---|
| **W01** · Tên hợp đồng (#1) | Tiêu đề nguồn → `build_payload` → `case_portal_projection`; catalog §5.4 | **C `tenvanban`**; không enum Notary/catalog ID | Tái dùng chuẩn → free text/gợi ý website | Dùng title chuẩn trực tiếp; tránh khóa 5 gợi ý thành mọi loại văn bản | **ĐÃ CHỐT** nghĩa scalar; ID/label là adapter |
| **W02** · Tình trạng (#2) | Không extraction; policy portal; catalog §5.1 | **P**, không Case status | Policy cố định | Mọi upload `DACONGCHUNG`; không dùng draft/locked Notary | **ĐÃ CHỐT**, không hỏi lại |
| **W04** · Nhóm hợp đồng (#4) | `guess_nhom_hd(title)` → projection; catalog/role metadata §5.2 | **C `nhomhopdong`** label có scope website | Tái dùng chuẩn + catalog adapter | Giữ label Case, chọn option thật; không biến website ID thành canonical FK, không dùng metadata A/B để duyệt quan hệ | **ĐÃ CHỐT** scalar; conversion form/POST vẫn unknown |
| **W05** · Loại tài sản (#5) | `guess_loai_tai_san(tai_san,title)`; §5.3, §5.6 | **J `web_form.loai_tai_san`**; chưa Asset chuẩn cutover | Dựng lựa chọn portal từ tập tài sản có căn cứ, mapping site riêng | Owner đồng ý hướng này; giữ **ID 1 Đất đai có tài sản**, thường nhà trên đất; thiếu mẫu/rule không là loại không tồn tại. Không tự tạo trường nhà/regex, chọn loại đầu/“Khác” để che tổ hợp | **ĐỒNG Ý CÓ ĐIỀU KIỆN**; quy tắc một ô khi tổ hợp nhiều loại thực sự chưa chốt, không universal fallback |
| **W07** · Công chứng viên (#7) | Regex nguồn hoặc lựa chọn prepare rõ ràng; §4/§5.6 | **C `congchungvien`** tên/null; default legacy không thành fact | Tái dùng chuẩn + catalog nhân sự | Chọn đúng option theo tên, không tự thêm staff FK; thiếu option không chọn đầu | **ĐÃ CHỐT** nghĩa/nguồn; không cần owner duyệt technical ID |
| **W08** · Thư ký (#8) | Extraction hiện `null`; input prepare → projection; §4/§5.6 | **C `thuky`** tên/null | Tái dùng chuẩn → freeSolo | Giữ lựa chọn rõ ràng trong Case được prepare; không đoán từ list/default | **ĐÃ CHỐT** |
| **W03** · Ngày công chứng (#3) | `find_ngay_cong_chung` → ISO → display DD/MM/YYYY | **C `ngaycongchung`**; không ngày tạo/ngày default website | Tái dùng chuẩn + đổi format tại biên | Không tạo ngày giả từ ngày mở form; gap clear/default hiện có ở §3 không tự thành policy mới | **ĐÃ CHỐT** scalar; không hỏi lại |
| **W06** · Số công chứng (#6) | `find_so_cong_chung`/scan → normalize | **C `socongchung`**; `registry.contract_no` chỉ scan/reference | Tái dùng chuẩn | Giữ `xxx/yyyy` và scope sổ/năm/site; không dùng làm shared Case ID | **ĐÃ CHỐT** |
| **W09** · Thông tin người yêu cầu… (#9) | Baseline first-person/raw/lookup; target §6.1 | **J `web_form.nguoi_yeu_cau`**, projection hợp lệ, chưa canonical cutover | Mọi cá nhân sống tham gia/đại diện chuẩn + chỉ thế chấp toàn cụm ngân hàng app tự lấy | Thứ tự nguồn, không lặp đại diện trong cụm; không người chết/CCV/nhân viên, không prose cá nhân khác; giữ history | **Q1/BANKMODE đã chốt**, proof runtime cuối còn chờ |
| **W10** · Đương sự (#10) | `raw.ben_a/b` → formatter theo loại | **J**, chưa parties cutover | Nhóm A/B theo nghĩa đã chốt | Ủy quyền A=ủy quyền/B=được ủy quyền; một bên không gán; nguồn trái nhau xác nhận phần nhóm, không winner tự động | **D05/#43 Q2 đã trả lời**; model/cutover chưa implement |
| **W11** · Tài sản (#11) | Text `_find_tai_san_by_kind` + `raw.danh_sach_thua_dat[]`; §6.2 | **J `web_form.tai_san`** và các hàng raw; chưa Upload Asset chuẩn | Dựng từ trường Asset/land rows đã biết | Phân biệt đoạn ghép toàn tài sản với lời dư thật chưa map; ví dụ §7.5.1; chưa duyệt block A09 | **A09 chờ làm rõ phạm vi; A10 đã duyệt nhận diện/pending** |
| **W12** · Văn bản hợp đồng (#12) | `raw.file_goc` → builder → input file; §8 | **F** JSON + `registry.file_path`; không cột nghiệp vụ | Tái dùng file/provenance kỹ thuật | Giữ nguồn; file selection trước Lưu không chứng minh portal upload/persistence | **ĐÃ PHÂN LOẠI**, không quyết định nghiệp vụ mới |
| **W13** · Ghi chú (#13) | Không builder/selector/fill | Không storage nghiệp vụ mới | Bỏ qua | Không điền/clear default; không dùng làm kho chứa gap | **ĐÃ CHỐT**, không hỏi lại |
| **W14** · Phí công chứng (#14) | Ngoài đường fill | Không extraction/cột phí mới | Bỏ qua | Không ghi 0/clear default hoặc thêm bước nhập tay | **ĐÃ CHỐT**, không hỏi lại |
| **W15** · Thù lao công chứng (#15) | Ngoài đường fill | Không extraction/cột phí mới | Bỏ qua | Như W14; không mở lại phạm vi phí | **ĐÃ CHỐT**, không hỏi lại |
| **W16** · Phí dịch vụ ngoài công chứng (#16) | Ngoài đường fill | Không extraction/cột phí mới | Bỏ qua | Như W14; mapping cũ thiếu không là việc cần triển khai hiện tại | **ĐÃ CHỐT**, không hỏi lại |
| **W17** · Phụ phí khác (#17) | Ngoài đường fill | Không extraction/cột phí mới | Bỏ qua | Như W14; không thêm canonical key | **ĐÃ CHỐT**, không hỏi lại |
| **WΣ** · Tổng chi phí (derived §4) | Website cộng bốn phí; live chỉ text h5 | Không input thứ 18, không persistence riêng | Để website hiển thị; app không điền/lưu | Giữ discrepancy hidden path đã ghi §4, không suy tổng 0 là lệnh ghi phí 0 | **ĐÃ CHỐT** |

### 7.2 Nguồn đọc bảng con và khác biệt loại văn bản

Các locator dưới đây là **source tĩnh đã đọc**, không kết quả parser mới; viết tắt `E` = `tools/regex_workbench/engine/contract_extract.py`, `U` = `upload_lab/playwright_uploader.py`, `N` = `notary_v2/services/document_intake/adapters/docx.py`.

| Mã nguồn | Locator chính xác / điều chứng minh |
|---|---|
| **S-P** | E `3200–3235:_extract_plain_text_person_entries`, `3688–3804` tên/danh xưng/ngày/giấy tờ+nơi cấp; `4154–4183:_extract_party_data` người có thứ tự + entity lines; `4608–4620:_extract_nguoi_chet` alias/ngày chết/TLKT/địa chỉ cuối |
| **S-R** | E `_requester_person_facts:2984`, `_mortgage_bank_spans:3002`, `_requester_projection:3040`, `build_payload:4969`; `batch_scan.save_output_json` persist payload; U `load_upload_queue:470`, `build_upload_form_data:540` giữ requester projection, không lookup/firstperson override; `_fill_editor:1462` là actual consumer |
| **S-D** | E `4637–4739:_extract_parties_generic` nhánh loại và headings; `4749–4765:_fmt_duong_su_by_kind`; `4855–4880,4953–4959:build_payload` người chết riêng/lọc khỏi bên; metadata vai trò website **khác** quan hệ app tại §5.2 |
| **S-A** | E `1772–1802:_new_thua_dat`; `2163–2183:thua_dat_sang_land_rows`; `2249–2259` hình thức sử dụng và Ghi chú chung đổ vào `phan_ghi_them`; `2503–2522` detail/bộ ba/`o_tho`; `4962–4973` output parcel |
| **S-T** | E `1007–1116:_find_tai_san_by_kind` khác vùng tài sản theo loại; `4768–4780:_phat_hien_tai_san_chua_ho_tro`; không chứng minh bóc đủ xe/sổ tiết kiệm/bảo hiểm |
| **S-C** | `contracts/entities.md:150–185,205–231,240–267`; `contracts/notary-case-drafting.md:246–285,314–362`: Người/Asset/land_rows/Case hiện có; không schema quan hệ Upload mới |
| **S-N** | N `49–69:PERSON_FIELD_SOURCES,ASSET_FIELD_SOURCES`, `316–350` chỉ mapper người hai bên, `552–568` parcel → land rows. Alias/giới tính/người chết không được suy là mapper đã đi đủ; `nguon_goc/hinh_thuc_su_dung` không có trong bảng ASSET_FIELD_SOURCES |
| **S-J** | `upload_lab/batch_scan.py:32–36,180–203,366–370,726–738`: chỉ Case JSON nhỏ ở registry; payload lớn ở file JSON. Mọi dòng **J** bên dưới mang đúng giới hạn này, không ghi Notary DB |

| Loại nguồn đã có nhánh code | Khác biệt thực cần giữ khi review, không là claim accuracy trên corpus |
|---|---|
| Chuyển nhượng / tặng cho | S-T ưu tiên vùng QSDĐ; S-D formatter chuyển nhượng ghép hai bên, tặng cho đi nhánh formatter chung. Không lấy một nhãn nhóm portal làm vai trò cho mọi loại |
| Thế chấp | Baseline S-D nhận Bên thế chấp/Bên nhận, fallback phần mở đầu; S-T có thể chỉ có title khi thiếu QSDĐ. Target app tự lấy toàn cụm ngân hàng có nguồn theo §6.1; không bịa tài sản hoặc quyền đại diện. Pháp nhân khác vẫn nhập tay |
| Phân chia / khai nhận / từ chối di sản | S-D có nhánh lấy bên riêng, formatter hiện chỉ dùng bên A cho W10; `raw.nguoi_chet` tách riêng, không tự gán thành requester/đương sự sống. S-T có vùng tài sản riêng và fallback mô tả savings/insurance/vehicle, chưa structured support |
| Cam kết tài sản | S-R chọn bên A cho requester khi có người, khác heuristic bên B thường dùng; S-T cắt vùng tài sản trước cam kết/lời chứng |
| Ủy quyền / di chúc / loại khác | S-D có pattern người ủy quyền/người được ủy quyền/người di chúc và fallback chung; không chứng minh nhận diện đủ người nhận di chúc, quyền đại diện hoặc quan hệ. S-T có fallback vùng đất/generic, không hứa mọi loại đều đủ trường; gate mẫu vẫn đóng |
| Hủy chuyển nhượng | S-T có vùng mô tả tài sản riêng; nhóm không được kéo theo chữ “chuyển nhượng” trong title hủy (E `1119–1129`). Không đồng nhất số hợp đồng được nhắc với số công chứng hiện tại |

### 7.3 W09 — người yêu cầu: 7 đơn vị thông tin

| ID / nội dung | Extraction hiện tại / nguồn | Chuẩn có sẵn + Upload thực lưu | Phương án phù hợp | Khuyến nghị + lý do/đánh đổi | Owner cần chọn? |
|---|---|---|---|---|---|
| **W09-R01** · Họ tên, danh xưng | `nguoi[].ho_ten/gioi_tinh`, raw formatter; S-P/S-R | `ten`; `gioitinh` wire Nam/Nữ/null khác Ông/Bà; **J**, mapper N chưa map giới tính | Tái dùng chuẩn rồi dựng hiển thị | Không gộp Ông/Bà/quan hệ vào tên; chỉ dùng giới tính/danh xưng có căn cứ, không đoán từ tên. Không cần field web trùng Person | **ĐÃ CÓ chuẩn scalar**; phần mapper/cutover chưa làm |
| **W09-R02** · Ngày/năm sinh; ngày chết trong dữ liệu nguồn | `ngay_sinh/chi_co_nam_sinh`; người chết nguồn riêng | `ngaysinh/ngaychet` giữ YYYY/full date; **J** | Giữ trường Person/raw/snapshot đúng nghĩa | Người chết không vào requester theo đáp án #43, nhưng không xóa giấy khai tử/ngày chết khỏi dữ liệu Hồ sơ thừa kế | **Scalar giữ nguyên; requester membership đã trả lời** |
| **W09-R03** · Giấy tờ, loại, ngày cấp, cơ quan cấp | `cccd/ngay_cap_cccd/noi_cap`; chết: `so_giay_to/ngay_cap/loai_giay_to`; S-P | `sogiayto/ngaycap/noicap/loaigiayto`; snapshot/master theo §6.1; **J** | Tái dùng chuẩn + hiển thị theo loại giấy tờ | Không ép mọi giấy thành CCCD; issuer snapshot có nghĩa riêng, không tự đồng nhất cơ quan công chứng. Nhiều giấy giữ ambiguous/#42, không nhét list vào ô đơn | **ĐÃ CHỐT scalar**; #42 độc lập, không hỏi lại |
| **W09-R04** · Địa chỉ và nhãn địa chỉ | `dia_chi/dia_chi_line`, người chết địa chỉ cuối; S-P/S-R | `diachi/loaidiachi`, line chỉ presentation; **J** | Tái dùng chuẩn + dựng nhãn theo nguồn/quy tắc đã chốt | Không nhân đôi địa chỉ vì ô web dài; không tự đổi nơi chết thành thường trú. Đa địa chỉ thuộc #42 | **ĐÃ CHỐT scalar** |
| **W09-R05** · Tên gọi khác | `raw.nguoi_chet[].ten_goi_khac`; S-P | **J raw/lịch sử**, chưa field alias approved | Không tự điền alias vào output chuẩn/không mở rộng chuẩn hóa; nếu cần user điền tay | Owner “bỏ tên gọi khác – nếu có user điền tay”; không nối vào `ten`, thêm field alias hoặc mở rộng normalization/#42; giữ raw/lịch sử, runtime chưa đổi | **ĐÃ CHỐT**, không hỏi lại |
| **W09-R06** · Ai là requester | Baseline first B/fallback A/lookup | **J**, chưa membership canonical cutover | Mọi cá nhân sống tham gia/đại diện, không cần tag A/B; không người chết/CCV/nhân viên | Một lần mỗi identity xác nhận theo nguồn; không prose/lookup/ưu tiên bên, giữ history | **Q1/BANKMODE đủ đáp án**, handoff #41 |
| **W09-R07** · Tổ chức và cá nhân đại diện | `entity_lines`/cá nhân đại diện/nguồn §6.1 | Không Person/legal table mới; **J** projection | **App tự lấy** toàn cụm ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/ủy quyền, chỉ thế chấp | Đúng vị trí nguồn, không lặp đại diện đã trong cụm; cá nhân khác chuẩn, không bịa quyền | **BANKMODE đã chốt**, proof runtime còn chờ |

### 7.4 W10 — đương sự: 8 đơn vị thông tin

| ID / nội dung | Extraction hiện tại / nguồn | Chuẩn có sẵn + Upload thực lưu | Phương án phù hợp | Khuyến nghị + lý do/đánh đổi | Owner cần chọn? |
|---|---|---|---|---|---|
| **W10-D01** · Dữ liệu từng thể nhân | `ben_a/b.nguoi[]` với tên/danh xưng/ngày/ID+cấp/địa chỉ; S-P | Cùng scalar R01–R04, không bộ Person thứ hai; **J** raw + web text | Tái dùng chuẩn + dựng từng người | Dùng một chuẩn Người, không sao chép các scalar vào block Đương sự; renderer giữ nguồn/độ đầy đủ, không chỉ ghép tên | **ĐÃ CÓ chuẩn scalar**, chưa Upload cutover |
| **W10-D02** · Người để lại di sản, ngày chết/TLKT | `raw.nguoi_chet[]` riêng | Scalar Người có sẵn, **J** | Giữ Person và snapshot Hồ sơ đúng nghĩa | Owner loại người chết khỏi requester Nam Định, không loại khỏi mọi Hồ sơ/Stage hoặc phá dữ kiện thừa kế; không suy chủ đất | **Đã trả lời phạm vi requester; scalar/history giữ** |
| **W10-D03** · Pháp nhân/tổ chức/chi nhánh | `entity_lines`/nguồn, chưa object chuẩn | Không Person/legal table; **J** text | Ngân hàng thế chấp app tự lấy toàn cụm ở requester §6.1; pháp nhân khác nhập tay | Giữ nguồn, không default/canonical legal field/blanket raw editor | **BANKMODE đã chốt**, không schema mới |
| **W10-D04** · Cá nhân đại diện và lời tư cách/căn cứ | Scalar cá nhân + raw/entity lines | Scalar có sẵn; authority chưa canonical model; **J** | Cá nhân khác chuẩn, lời phức tạp user sửa; chỉ cụm ngân hàng thế chấp giữ đủ đại diện/ủy quyền nguồn §6.1 | Không suy quyền/hiệu lực, không block D04 mới/manual fallback mọi gap | **ĐÃ CHỐT**, proof cuối slice còn chờ |
| **W10-D05** · Nhóm Bên A/Bên B | Nhánh nguồn chuyển/nhận, ủy quyền, một bên | **J**, participation chưa cutover | Nhóm A/B chung; ủy quyền A=người ủy quyền/B=người được ủy quyền | Một bên không gán; hai nguồn trái nhau giữ conflict/xác nhận phần nhóm; không tự winner hoặc dùng “nhận” phổ quát | **#43 Q2 đã trả lời**, không hỏi lại |
| **W10-D06** · Nhiều người/thứ tự/lần tham gia | Array nguồn có thứ tự | **J**, chưa model chuẩn | #43 đủ16ca/Q1/Q2/BANKMODE, handoff #41 | Giữ identity/nguồn/lần tham gia, không gộp tên/cắt người đầu; requester độc lập tag nhóm | **Phân tích đủ đáp án**, chưa canonical schema/cutover |
| **W10-D07** · Người liên quan tài sản nào | Cùng payload không chứng minh cặp; `chudat` Diagram khác nghĩa | **J**, chưa model/cardinality/FK; Upload `chudat=null` | #43 giữ scope người/nhóm–tài sản có nguồn | Cả nhóm/cả tập khác từng cặp/chưa rõ, không Cartesian/chủ đất từ A/GCN | **Đã bàn giao #41**, không chờ toàn #41/#42 |
| **W10-D08** · Lời quan hệ/tư cách phụ | `raw_text/entity_lines` giữ lời nguồn; S-P | Không field residual prose approved, **J** | Owner trả lời **theo R06**: dữ liệu chuẩn Người, không lời mô tả phụ | Không duyệt cụm dư D08; không đưa con đẻ/quan hệ/chức vụ/role prose vào requester. Nhóm W10 theo D05, quan hệ #43; nguồn vẫn giữ | **ĐÃ TRẢ LỜI**, không hỏi lại D08 |

### 7.5 W11 — tài sản: 10 đơn vị thông tin

| ID / nội dung | Extraction hiện tại / nguồn | Chuẩn/đích sẵn có + Upload thực lưu | Phương án phù hợp | Khuyến nghị + lý do/đánh đổi | Owner cần chọn? |
|---|---|---|---|---|---|
| **W11-A01** · GCN: serial nguyên văn, số vào sổ, loại giấy | `so_gcn_raw/so_vao_so/loai_gcn` theo parcel/context; S-A | Wire `so_serial/so_vao_so/loai_so`, properties tương ứng; **J** | Tái dùng chuẩn rồi dựng khối GCN | Không lấy normalized serial thay nguyên văn, không ép unique/format; nhiều thửa có thể cùng GCN. Loại giấy khác W05 loại tài sản; #40 không tự fixed | **ĐÃ CÓ chuẩn**, chưa Upload cutover |
| **W11-A02** · Thửa, tờ bản đồ, địa chỉ; thứ tự các tài sản | `danh_sach_thua_dat[]` và context, `*_values` báo nhiều giá trị; S-A | Wire/properties `so_thua_dat/so_to_ban_do/dia_chi`; **J** | Tái dùng chuẩn + nhóm tài sản có nguồn | Giữ từng thửa/thứ tự và context GCN đúng phạm vi; không lấy thửa đầu hoặc gộp mọi địa chỉ vì một editor. Không suy serial/thửa là shared Case ID; liên kết người xem D07 | **ĐÃ CÓ scalar**; phạm vi liên kết chờ D07, không chốt cardinality mới |
| **W11-A03** · Ngày cấp GCN, cơ quan cấp | `ngay_cap_gcn/co_quan_cap`, context và alternatives; S-A | Wire/properties `ngay_cap/co_quan_cap`; **J** | Tái dùng chuẩn + format | Khác ngày/cơ quan công chứng và cấp giấy tờ Người. Thiếu/mâu thuẫn giữ nguồn, không lấy ngày hiện tại | **ĐÃ CÓ chuẩn**, không hỏi lại scalar |
| **W11-A04** · Tổng diện tích thửa và diện tích chi tiết | `dien_tich` cấp thửa + `chi_tiet_dien_tich[].dien_tich`; S-A | properties có `dien_tich` tổng, child có `dientich`; contract/mapper chi tiết §6.2, **J**; có cột tổng không chứng minh Upload writer/đủ wire | Tái dùng đúng đích đã có; dựng hiển thị tổng/chi tiết tách nghĩa | Không ghi tổng vào mọi cụm, không tự cộng chi tiết thay tổng nguồn khi chưa chứng minh phủ hết. Wire gap của tổng phải đối chiếu contract trước cutover, không tự thêm key canonical | **Không mở lại nghĩa scalar**; mapping/wire còn phải hoàn tất, không gọi đã implemented |
| **W11-A05** · Các hàng mục đích/loại đất–diện tích–thời hạn, có thứ tự | `chi_tiet_dien_tich[]` → `thua_dat_sang_land_rows`; S-A/S-N | Canonical `land_rows[].loaidat/dientich/thoihan`; child DB Notary có vị trí; **J** trong Upload | Tái dùng chuẩn + dựng bảng/đoạn HTML từ từng hàng | Không flatten ba danh sách rời, không tráo dòng/rút chỉ một loại đất; giữ vị trí kể cả dòng trống theo contract. Loại đất khác W05/loại GCN | **ĐÃ CHỐT**, không hỏi lại cấu trúc bộ ba |
| **W11-A06** · Thời hạn đất cấp thửa chưa rõ cụm | `thoi_han_su_dung` riêng và từng detail; S-A | Chỉ thời hạn đúng `land_rows[].thoihan` là đường mới; cấp Asset chỉ legacy/history; **J** | Map vào đúng cụm khi có bằng chứng; phần chưa gắn giữ unresolved/nguồn | **Giữ thời hạn sử dụng đất**, không áp policy loại thời hạn nghiệp vụ để bỏ nó; không tự rải thời hạn lẻ cho mọi hàng hoặc dùng block che gap | **ĐÃ CHỐT**, không xin lại; unresolved không tính đã map |
| **W11-A07** · Nguồn gốc sử dụng đất | `nguon_goc`; S-A | Wire/properties `nguon_goc` có thật; **S-N chưa map field này**, Upload **J** | Tái dùng đích nghĩa đã có | Ưu tiên hoàn thiện mapping đúng nghĩa, không tạo cụm riêng trùng trường; không nói chung engine đã ghi DB vì có cột | **ĐÃ CÓ đích**, phần mapper/cutover kỹ thuật chưa làm |
| **W11-A08** · Hình thức sử dụng riêng/chung khi nguồn nêu rõ | Label “Hình thức sử dụng” và “Ghi chú” cùng vào `phan_ghi_them`; S-A `2249–2259` | Wire/properties `hinh_thuc_su_dung` có thật, **chưa mapping cả blob**, Upload **J** | Tách đoạn có nghĩa rõ → tái dùng chuẩn; phần dư xem A09 | **Đề xuất map chỉ phần được nguồn xác định là hình thức sử dụng**, không coi cả `phan_ghi_them` là field này; không cần owner mở lại scalar đã có | **Không quyết định scalar mới**; mapping phải giữ bằng chứng/ambiguous khi chưa tách được |
| **W11-A09** · Đoạn tài sản ghép và lời dư thật chưa map | `phan_ghi_them`, detail extras/`o_tho`, W11; S-A/S-T | A01–A08 có các đích nghĩa thật; phần dư **chưa field cụm approved**, **J** | Làm rõ đoạn này dùng trường nào, lưu ví dụ tổng hợp §7.5.1 | Toàn đoạn mô tả GCN/thửa/cụm đất có thể dựng từ chuẩn, không vì là đoạn dài mà thành block dư. Chỉ lời còn lại sau mapping mới là ứng viên residual; `phan_ghi_them` hỗn hợp không tự là field hình thức hay field mới; nhà/công trình thiếu catalog/rule | **CHỜ LÀM RÕ A09**, chưa duyệt block/storage/engine |
| **W11-A10** · Xe / sổ tiết kiệm / bảo hiểm | Flags `tai_san_chua_ho_tro` + text; S-T | Chưa structured Asset/Upload persistence đầy đủ, **J** | Giữ nhận diện + nguồn, **pending structured support**, chưa mở rộng hiện tại | Owner duyệt khuyến nghị này; #29 xe vẫn DEFERRED. Không dùng A10 để loại **đất có tài sản/nhà W05**, không mất nguồn hoặc coi đã chuẩn hóa | **ĐÃ DUYỆT phạm vi**, không permission implementation |

### 7.5.1 A09 — những trường tạo nên đoạn tài sản và ví dụ lưu lại

**Hai nghĩa khác nhau:** (1) toàn đoạn trình bày tài sản ghép từ các dữ kiện chuẩn;
(2) lời dư thật chưa có mapping sau khi tách dữ kiện. Ví dụ dưới chỉ minh họa (1),
**không chứng minh cần field lưu cả đoạn hoặc duyệt cụm A09**.

Nguồn thẩm quyền: [contract Notary](../../../contracts/notary-case-drafting.md)
**§4.2 asset_row, §13.3 snapshot tài sản** và
[entities §9.2](../../../contracts/entities.md).
§6.2/S-A/S-N ghi đường extraction/mapper và gap; có đích Notary không chứng minh
Upload đã cutover. Đây là bảng giải nghĩa trường có thật, **không wire payload mới**.

| Dữ kiện hiển thị | Trường nguồn/đích đã có | Giá trị minh họa hoàn toàn giả lập |
|---|---|---|
| Serial GCN nguyên văn | extraction `so_gcn_raw` → wire/model `so_serial` | `MINH-HOA AB 000000` (giữ nguyên văn) |
| Số vào sổ | `so_vao_so` | `CS-MINH-HOA-001` |
| Loại giấy | `loai_gcn` → `loai_so` | Giấy chứng nhận quyền sử dụng đất |
| Ngày cấp; cơ quan cấp | `ngay_cap_gcn` → `ngay_cap`; `co_quan_cap` | 15/06/2020; Cơ quan cấp minh họa |
| Thửa; tờ; địa chỉ | `so_thua_dat`; `so_to_ban_do`; `dia_chi` | 101; 09; Thôn Minh Họa, xã Giả Lập, tỉnh Minh Họa |
| Diện tích **tổng thửa** từ nguồn | extraction/model/snapshot `dien_tich`; wire §4.2 không liệt kê scalar tổng, §13.3 có snapshot tổng hợp | 240 m²; không tự tính tổng chi tiết làm fact hoặc ghi vào mọi cụm |
| Cụm đất vị trí 1 | canonical/model `land_rows[].loaidat/dientich/thoihan`; wire emit `loai_dat/dien_tich/thoi_han` | Đất ở tại nông thôn; 100 m²; Lâu dài |
| Cụm đất vị trí 2 | cùng bộ ba, giữ vị trí 2 | Đất trồng cây lâu năm; 140 m²; đến 31/12/2063 |
| Nguồn gốc | `nguon_goc` có wire/model; S-N chưa map | Công nhận QSDĐ như giao đất không thu tiền sử dụng đất (giả lập) |
| Hình thức sử dụng, **nếu có nguồn rõ** | `hinh_thuc_su_dung` có wire/model; không map toàn blob `phan_ghi_them` | Sử dụng riêng (giả lập) |

**Đoạn minh họa, không phải output runtime hoặc mẫu Word:**

> Tài sản minh họa: quyền sử dụng thửa đất số 101, tờ bản đồ số 09, tại Thôn
> Minh Họa, xã Giả Lập, tỉnh Minh Họa. Diện tích toàn thửa: 240 m². Theo thứ tự
> nguồn: (1) Đất ở tại nông thôn, 100 m², thời hạn Lâu dài; (2) Đất trồng cây
> lâu năm, 140 m², thời hạn đến 31/12/2063. Hình thức sử dụng: Sử dụng riêng.
> Nguồn gốc: Công nhận QSDĐ như giao đất không thu tiền sử dụng đất.
> Giấy chứng nhận quyền sử dụng đất số nguyên văn “MINH-HOA AB 000000”,
> số vào sổ “CS-MINH-HOA-001”, cấp ngày 15/06/2020 bởi Cơ quan cấp minh họa.

Mọi giá trị/địa danh/cơ quan trên đều bịa để minh họa, không PII, không fixture,
corpus hoặc hợp đồng thật; không giá/cọc/vay/điều khoản giao dịch. Ví dụ không
mô tả nhà vì **chưa có catalog/rule chi tiết nhà**, không phủ nhận loại W05 ID 1.
Trường vắng không được bịa; việc bỏ nhãn/dấu câu tương ứng chỉ là cách minh họa,
chưa chọn renderer/template engine. Ví dụ không có residual narrative thực;
chưa đủ căn cứ duyệt field “mô tả bổ sung tài sản”.

### 7.6 Đã chốt và phần còn cần làm rõ

- **Đã trả lời:** R05 alias nhập tay; R06 requester Nam Định là cá nhân sống
  A/B/đại diện ủy quyền, không người chết/CCV/nhân viên trong output; dữ kiện/
  Person/Stage/history giữ nguyên. D04/D08 cá nhân không prose; A10 pending,
  #29 deferred. Ngân hàng thế chấp cả cụm không Person; **BANKMODE “app tự lấy”**.
- **W05 đồng ý có điều kiện:** dựng lựa chọn portal từ tập tài sản; giữ ID 1
  đất có tài sản/nhà. Còn thiếu rule khi một hồ sơ thực sự có nhiều loại khác nhau;
  không tự chọn một loại bao quát/đầu/Khác, không đọc mẫu mới để lấp gap.
- **D05 đã trả lời #43:** ủy quyền A=ủy quyền/B=được ủy quyền; một bên không
  gán; hai nguồn trái nhau giữ conflict/xác nhận nhóm bị ảnh hưởng, không
  winner/thu hẹp requester. “Nhận” không universal regex/“không nhận=A”.
- **A09 còn làm rõ phạm vi:** bảng/ví dụ §7.5.1 cho biết trường thật tạo đoạn
  tài sản; chưa xác định lời dư cụ thể đủ điều kiện để duyệt cụm riêng. Giữ
  chưa map/source cho nội dung chưa rõ, không dựng thêm field nhà/`o_tho`.
- **D06+D07/#43:** đủ16ca/kết luận bảo toàn/Q1/Q2/BANKMODE, không owner bank
  gate; bàn giao #41. App tự lấy cụm ngân hàng thế chấp qua projection hiện có,
  không legal field/blanket raw editor; model/FK/schema quan hệ chưa chốt, #41 mở.

### 7.7 Hai tầng dữ kiện / đoạn suy ra — lịch sử phương án; owner chốt chỉ placeholder và trường tĩnh

**Cập nhật 20/10/2026 — đã chốt:** owner chốt **“chỉ dùng placeholder và trường
tĩnh, tiếp tục”**. **Đối với trường nghiệp vụ mới**, spec đích chỉ dùng **trường
tĩnh ghi nhận từ nguồn** và **placeholder/formatting output hiện có**; không mở
trường tầng 2 động/tính toán, text canonical persisted từ suy ra, engine công
thức hoặc framework điều kiện/cấu hình. **Block token/alias/formatter/mẫu Word
và logic derived cố định đang có giữ nguyên**, không bị quyết định này gỡ hay
duyệt engine mới. Phần dưới đây giữ làm **lịch sử/phương án đã cân nhắc, chưa
từng triển khai**, không phải định hướng hay approval hiện hành.

**Giới hạn cần đọc cùng quyết định:** quyền **có điều kiện** cho một trường giữ
cả cụm **text tĩnh** phức tạp, không lặp lại, của một ô website cụ thể (§6.3/§7)
**vẫn giữ**, vì đó là dữ kiện tĩnh có nguồn, không phải tầng động; vẫn phải chỉ
rõ ô/mapping/provenance và chốt theo quy trình hiện có. **A09 vẫn chưa duyệt
field.** Placeholder/formatting Word hiện có là lớp output, không tự thành
trường nghiệp vụ mới; block token do code Word định nghĩa, alias cũ, formatter
và mẫu đang hỗ trợ không bị xóa/sửa bởi quyết định này.

Owner nêu Người và Tài sản thường trình bày tự nhiên trong một đoạn, cân nhắc
tầng 1 dữ kiện tĩnh và tầng 2 đoạn dựng từ dữ kiện, có thể có điều kiện. Đây là
**khám phá phương án lịch sử**, không còn là định hướng hiện hành. Ví dụ tổng
hợp A09 không phải quyết định field hay kiến trúc; không đưa ví dụ Người có
tên/ID của user vào Git.

**Tiền lệ hiện có, không phải engine mới đã duyệt:** Word tính mapping token →
chuỗi và có khối tên cố định với điều kiện trong code; không phải engine công
thức/điều kiện tổng quát do user cấu hình. Nguồn tĩnh:
[`build_template_mapping`, `word_engine.py:1877–1917`](../../../notary_v2/services/word_engine.py),
[`_add_block_placeholders`, `word_engine.py:1607–1642`](../../../notary_v2/services/word_engine.py).

| Phương án đã so sánh (lịch sử) | Lợi ích | Đánh đổi |
|---|---|---|
| Formatter cố định theo output | Gọn, ít cơ chế mới, dễ kiểm soát câu xuất | Mỗi biến thể cần developer; Word/web có trình bày riêng, dễ lặp logic nếu dùng lại nhiều |
| Khối suy ra có tên, phạm vi hữu hạn; điều kiện do code định nghĩa | Tái dùng đoạn/điều kiện có tên rõ, phù hợp tiền lệ khối Word | Cần chốt nghĩa/phạm vi từng khối; thêm/sửa vẫn cần code, kiểm tương thích các consumer |
| Engine công thức/điều kiện cấu hình sâu bởi user | User tự đổi quy tắc/biến thể không cần mỗi lần phát hành code | Thêm gánh kiểm lỗi cấu hình, bảo mật, vòng phụ thuộc và version; **không được chọn** theo quyết định 20/10/2026 |

**Rủi ro chung, kể cả formatter/khối cố định:** phải rõ đoạn đọc snapshot đã
commit hay nháp/master; sửa tay kết quả có bị tính lại/ghi đè khi dữ kiện đổi
hoặc xuất lại; thiếu trường, ngày chỉ có năm, dấu câu/nhãn thừa; Word là text
còn editor web là HTML nên không mặc định dùng chung chuỗi/escaping. Ngay logic
suy ra cố định đã có phân biệt giá trị user sửa với giá trị tự suy
([`_resolve_derived_field`, `case_workspace.py:341–361`](../../../notary_v2/services/case_workspace.py));
đó chưa là policy override cho mọi đoạn. Khả năng tái tạo văn bản cũ cũng phụ
thuộc phiên bản formatter, dữ kiện/ngày xuất, không chỉ engine cấu hình.
Tùy biến sâu **thêm** rủi ro vòng/cycle, thực thi nội dung không an toàn,
version cấu hình và lỗi user; không làm biến mất các rủi ro chung trên.

**Khuyến nghị lịch sử — đã bị thay bởi quyết định 20/10/2026:** ưu tiên dữ kiện
chuẩn tĩnh làm nguồn sự thật, dựng đoạn theo nhu cầu tại lúc xuất. Phương án
engine cấu hình sâu **không được chọn**; không xây framework/engine, không duyệt
lưu text canonical hoặc policy tính lại/override/version mới. Định dạng output
bằng placeholder/formatter hiện có vẫn tách khỏi dữ kiện nghiệp vụ tĩnh.

Spec đích không tự là proof runtime. Owner đã giao runtime slice Nam Định đã
chốt, gồm ngân hàng; docs-only mốc trước không freeze slice này. Proof cuối chờ
main, không BUILT/toàn normalized cutover; #41 mở/gate mẫu **ĐÓNG**.

## 8. Implementation preSave — đã kiểm chứng cô lập và review độc lập sạch

1. **17 trường website, 12 trường adapter được chuẩn bị:** năm ô phí/ghi chú chủ động ngoài builder/selector/fill order. Không thêm key cho hai phí chưa có mapping, không tạo persistence cho tổng.
2. `uploader_selectors.py:FORM_FIELD_ORDER` đã có `file_hop_dong`; `build_upload_form_data` giữ nguồn `raw.file_goc`; `_prepare_record` đi tới `_upload_file` dùng `set_input_files`. Verify file đọc chính file input, so filename; source không tồn tại/selection lỗi là partial, không fallback text tên file trên trang. Chỉ chứng minh preSave selection/file-change của form kiểm soát, không metadata/upload API/backend portal.
3. Status policy Đã công chứng vốn đã có trong builder, nay cũng enforced ở consumer và verify. Điều khiển `div[role=combobox]` được mở/chọn option; không thử type/fill như input. Native select vẫn được hỗ trợ cho consumer hiện có.
4. Đã gỡ `_prime_contract_name_validation`, retype-after-prime, flag và mọi caller/test legacy. `_select_dropdown_option` không Enter/ArrowDown/fallback page text. Title/thư ký freeSolo input+blur; remote chọn role option đúng. Không cài generic preventDefault/submit blocker trong runtime.
5. `_prepare_record` vẫn persist Case nhân sự chỉ khi record thực prepare; queue read không ghi override. Preview/default không là fact. Historical Case invalid vẫn báo lỗi, không silently rơi về legacy. JSON nguồn/provenance giữ nguyên; không sửa schema/canonical metadata hoặc queue không chọn/trùng/chờ đợt sau.

**Proof 20/10/2026:** regression bền vững `upload_lab/tests/test_namdinh_preparation.py` chạy actual `prepare_manifest → _prepare_record` trên Chromium mới, form có submit/Save-click/Enter counters và MUI-like observed shapes (không coi fixture là portal catalog). Trước sửa: một ca freeSolo có **3 submit / 3 Save-click / 2 Enter / 9 skipped-field events**, attachment rỗng. Sau sửa: title ngoài gợi ý và có gợi ý, remote thiếu option, source file thiếu đều **0 submit / 0 Save-click / 0 Enter / 0 skipped-field events**; năm default portal giữ nguyên; status `DACONGCHUNG`; file có thật đúng filename/51 bytes/file-change state; thiếu file/option thành partial. Chỉ một GET route local mỗi ca, không request ghi/upload mạng. Case suite còn chứng minh selection/duplicate/chunk và JSON nguồn không đổi.

Verification implementer: **42 passed** (Upload scoped, gồm 5 ca Chromium) và **60 passed** (sidecar workflow); warnings openpyxl hiện có. **Review độc lập CLEAN**, reviewer chạy lại **42 pass, không skip + 60 pass**, xác nhận counters/file/persistence. Sau review bổ sung permanent smoke: source file thiếu nhưng có text filename không liên quan đang hiển thị; actual consumer vẫn file DOM rỗng, filler/verify false, `prepared_partial`; affected suite chạy lại **5 passed, không skip, 32.49s**, không đổi runtime. Evidence local tùy chọn: `_bmad-output/tmp/namdinh-preparation/{before,after,final,case-evidence}/`. Không nghiệm thu portal thật, metadata/ID conversion/POST, packaging, corpus hoặc toàn #41; gate mẫu **ĐÓNG**. Bản source được sửa; build/dist chưa tái sinh, không claim đã phát hành.

## 9. Bảo trì và cập nhật

- **Một site một catalog chuyên sâu tại file này**; README module là entrypoint, không dựng workflow/source SOT song song. Khi website đổi route/bundle/widget/options/API hoặc adapter/schema đổi, cập nhật cùng file: ngày, scope nguồn, field count, option count/completeness, dependency, mapping và gap #41.
- Đầu lượt đọc AGENTS → specs README/product-overview → module README → graphify-out → source hiện hành. Dùng source `file:symbol:line`; line có thể trôi nên kiểm symbol trước khi cập nhật. Không dùng file tmp/cache như nguồn chuẩn bắt buộc.
- Thu thập an toàn theo quyền có thật: public GET/static trước; authenticated **empty form read-only** khi có phiên được phép, không tự tìm/import credential. Không Lưu/upload/ghi DB/đọc record cá nhân để kiểm widget. Ghi riêng static vs authenticated; nếu không vào được thì giữ gap, không sửa nhãn thành verified.
- Mỗi catalog phải có site/đơn vị/date/source, item value/label/type hoặc shape-only với lý do PII; ghi query/dependency/pagination trước khi claim đầy đủ. Không ghi tên nhân sự thật trong Git. Không suy 200+items=[] là list đầy đủ nếu thiếu scope; không suy 403 là catalog rỗng.
- Nếu chỉ đổi selector/catalog/policy, phân loại technical adapter config; nếu đổi nghĩa nghiệp vụ/DB-wire, refine #41 và xin schema approval theo contract trước code. Không tự rename canonical, thêm alias, dùng ghichu/raw capture thay trường hoặc đóng gate. Ngoại lệ hẹp đã được owner chấp thuận là cụm trường phụ website rõ nghĩa (§6.3, §7); không phải quyền mở rộng schema hoặc biến editor thành block.
- Main agent/reviewer kiểm liên kết/citation/counter consistency và đối chiếu source độc lập trước commit. Audit website A1 không chạy app/test hoặc submit/upload; implementation sau đó chỉ chạy kiểm chứng cô lập theo §8. Không tạo HTML vì đây là catalog tra cứu, không thay app UI.
