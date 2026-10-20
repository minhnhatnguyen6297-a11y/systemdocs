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
| 9 `hopdong.nguoiYeucauCongchung` · Thông tin người yêu cầu công chứng (ghi sổ công chứng) | CKEditor HTML · không R | `build_payload:4924-4927,4944` chọn B nếu có người, fallback A; cam kết tài sản A → first person raw_text; optional requester lookup → **J** presentation. Người + vai trò Hồ sơ **chưa cutover** (§6) | `nguoi_yeu_cau` / label XPath · 103-112; `resolve_requester_override:561-588` |
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
| `ten_goi_khac`, `entity_lines`, vai trò requester/Bên A/Bên B | **U** mapping/catalog chưa chốt | không thêm schema, không ghi ghichu; entity_lines có thể chứa tổ chức, không tự xem là Người; pháp nhân do người dùng nhập tay (§6.3) |
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

**Owner 20/10/2026 chốt:** pháp nhân **không đưa vào Người**; theo policy, người
dùng **nhập tay**, code hiện tại chưa cutover. Bảng pháp nhân riêng sau này là định hướng **chưa duyệt schema/
build**. Hồ sơ thế chấp là trường hợp mặc định có pháp nhân; nguồn thường nêu
ngân hàng/chi nhánh/đại diện; loại khác ít xảy ra. Sự có mặt đó không cho phép
tự bịa tên, người đại diện hoặc default party; chỉ dùng dữ kiện nguồn nêu rõ;
pháp nhân khác giữ nguồn và không bị âm thầm bỏ mất hoặc tự xếp loại.

**Owner 20/10/2026 cho phép có điều kiện** thêm một trường giữ cả cụm khi cụm
phức tạp, không lặp lại và thuộc một ô nhập của một website cụ thể. Đây không
phải quyết định biến cả ba editor hoặc mọi ô web thành block/trường phụ. Khi
chọn cụm phải xác định website/phạm vi ô, nghĩa nghiệp vụ, lý do không tái dùng
trường canonical đã biết, kiểu lưu và provenance; giữ nguồn. Chỉ hỏi owner khi
có quyết định nghiệp vụ thực sự chưa rõ; chi tiết kỹ thuật do implementation sở
hữu theo contract/rule đã duyệt. Không dùng `ghichu` chung hoặc JSON bag chung
thay trường; raw capture chỉ là provenance, không thay trường nghiệp vụ; không
tự đặt key/tên/kiểu/nhóm/storage và không dùng cụm để tự bóc pháp nhân. Cụm có
thể là trường riêng theo ô; phần tái dùng được vẫn map canonical, không mặc định
coi cụm là dữ liệu chưa map/orphan. Chưa chọn cụm/ô nào; nhãn “trường phụ” không
đồng nghĩa canonical field hay DB column đã duyệt.

**Quan hệ Người–Tài sản–Hồ sơ** nhiều người/nhiều tài sản chưa chọn model,
cardinality, quan hệ/FK hay bảng nối; không coi mô hình quan hệ trước đó là đã
được owner chấp nhận. Phần này thuộc refinement #41 trước implementation, không
tạo ticket mới.

## 7. Phân loại trường phụ website — chưa duyệt schema

| Nhóm | Ví dụ | Hướng refinement, không phải implementation approval |
|---|---|---|
| Catalog mapping có scope | group ID↔label; asset object ID/ten; CCV ID↔tên; đơn vị của title/thư ký | Có thể là cấu hình/catalog adapter theo website + đơn vị + ngày/version. Không tự tạo Person/Asset/Case business column hoặc staff FK |
| Policy/config portal | default status, label aliases, selectors, route, default CCV legacy | Quản lý developer theo site; không nâng thành extraction fact. Không đồng nhất trạng thái portal với Notary draft/locked |
| Provenance/file/technical | file path, source_refs, asset hash/module, run/record IDs, timeout | Giữ evidence/scope an toàn; không buộc thành cột nghiệp vụ mới, không nhét PII vào doc |
| Scope owner đã chốt 20/10/2026 | bốn phí/thù lao, ghi chú, trạng thái portal | Bốn phí và ghi chú bỏ qua/không điền; không ghi 0/xóa default/thêm extraction, cột hoặc nhập tay. Status mọi hợp đồng upload mặc định `DACONGCHUNG`/Đã công chứng, không Notary status. Adapter đã sửa, proof consumer kiểm soát ở §8; chưa nghiệm thu portal thật |
| Pháp nhân — owner 20/10/2026 | hồ sơ thế chấp là mặc định có pháp nhân; nguồn thường nêu ngân hàng/chi nhánh/đại diện; loại khác ít xảy ra; trường chưa đồng nhất | Theo policy, người dùng **nhập tay**; không đưa vào Người, không thêm loại pháp nhân vào Person, không tự bịa tên/đại diện/default; chỉ dùng dữ kiện nguồn nêu rõ. Bảng riêng tương lai là định hướng, **chưa duyệt schema/build**; giữ nguồn, không âm thầm bỏ hoặc tự xếp loại |
| Cụm trường phụ website — owner 20/10/2026 | một số ô nhập web phức tạp, không lặp lại; website khác yêu cầu khác | Khi đáp ứng điều kiện owner nêu, xác định website/phạm vi ô/nghĩa/lý do/kiểu/provenance; ưu tiên canonical đã có; chỉ hỏi owner khi quyết định nghiệp vụ thực sự chưa rõ. Không generic bag/`ghichu` chung; raw capture chỉ provenance, không thay trường; không tự đặt key/type/group/storage, không tự coi ba editor là block; chưa chọn ô nào |
| Nghiệp vụ còn refine | Asset/parties chưa map; mở rộng thực sự cần trong tương lai | Refine **#41** theo nghĩa/owner/key/kiểu/cardinality/DB-wire-output trước implementation; quyết định bỏ phí/ghi chú hiện tại không duyệt schema tương lai |
| Derived website | tổng chi phí và hidden path khác spelling | Không phải ô phí thứ năm; không persistence riêng, không sửa spelling; quan sát tổng 0 không cho phép app ghi 0 |
| Owner đã loại | giá giao dịch/cọc/thuê/vay/lãi/điều khoản thanh toán/thời hạn nghiệp vụ | Không extraction/normalized; portal đòi thì ghi conflict #41, không bịa/default/âm thầm giữ hoặc tự quyết nhập tay. Phí công chứng/thù lao không đồng nghĩa giá giao dịch; đã có policy bỏ qua riêng ở trên |

Thời hạn sử dụng đất đúng `land_rows[].thoihan` và timeout kỹ thuật vẫn giữ. Không xóa raw/lịch sử để đạt catalog. #42 model đa giấy tờ/đa địa chỉ chưa chọn; không tự là gate mới. Quan hệ nhiều người/nhiều tài sản cũng chưa chọn model/cardinality/schema và không coi mô hình quan hệ trước đó là đã được owner chấp nhận; thuộc refinement #41, không tạo ticket mới. Các quy tắc pháp nhân/cụm trường là policy đích: hiện chưa có bảng pháp nhân hoặc trường lưu cụm, Person/Asset/parties chưa cutover, ba editor vẫn là output trình bày. Không tạo ticket trùng #41 chỉ vì mới thấy hai khoản phí.

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
