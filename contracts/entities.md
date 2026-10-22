# Định danh hồ sơ — định nghĩa dùng chung

**Phạm vi:** file này định nghĩa *ý nghĩa và cách chuẩn hóa* định danh người,
giấy chứng nhận/tài sản và tham chiếu hồ sơ. Chúng cung cấp bằng chứng tìm hồ
sơ liên quan, không mặc nhiên chứng minh "cùng một hồ sơ". Không áp đặt regex,
tên biến, schema DB hay dùng định danh người/tài sản làm khóa chính Case.

**Bắt buộc:** khi một repo trích xuất hoặc so khớp một trong các khóa dưới đây,
nó phải chuẩn hóa về **dạng canonical** ghi ở đây trước khi so sánh hoặc trước
khi ghi vào trường "khóa định danh". Giữ raw và nguồn gốc theo
[`../_bmad-output/specs/README.md`](../_bmad-output/specs/README.md) mục 4; chuẩn hóa không được
ghi đè bằng chứng gốc.

Cập nhật: 21/10/2026 — bổ sung điểm neo gom ID; quy tắc chuẩn hóa giữ theo nguồn.

---

## 1. CCCD — Số căn cước công dân

- **Canonical:** 12 chữ số liền nhau, không dấu cách, không dấu chấm.
- **Không dùng làm khóa:** CMND 9 số. Nếu chỉ có CMND 9 số, coi là dữ liệu phụ,
  không dùng để tự động ghép hồ sơ.
- **Nguồn đọc được cả hai:** mã MRZ hộ chiếu/CCCD dạng `IDVNM(\d{9})(\d)(\d{12})`
  chứa cả CMND cũ và CCCD mới — lấy nhóm 12 số làm CCCD.

**Cách nhận hiện hành và thiết kế dự kiến — không đồng nhất với canonical:**

| Repo | Cách nhận | Ghi chú |
|---|---|---|
| `notary_v2` | `(?<!\d)(\d{12})(?!\d)` — mọi cụm 12 số (`routers/ocr_ai.py`) | Rộng nhất, vì OCR ảnh hay mất chữ đầu |
| `upload_lab` | Neo theo nhãn: `(?:Căn cước\|CCCD\|CMND)\s*(?:số)?\s*:?\s*(\d+)` (lõi chung `tools/regex_workbench/engine/contract_extract.py`, gọi qua adapter Upload) | Chặt theo ngữ cảnh vì text Word có sẵn nhãn |
| `notaryoffice` (dự kiến) | `\b\d{12}\b` (`_bmad-output/specs/notaryoffice/intent-source.md` v1.0 §7.2) | Đã bỏ ràng buộc số 0 đầu; chưa có implementation |

**Quy tắc thống nhất:** dù regex nào, giá trị đem đi so khớp phải là đúng 12 chữ
số. Không so khớp một phần, không so khớp 9 số cuối.
Đây là chuẩn của trường CCCD, không ép mọi số giấy tờ thành CCCD. Điểm neo
Người ở §8.3 dùng tên + số giấy tờ đang có theo đúng loại dữ liệu nguồn.

---

## 2. Số serial GCN (sổ đỏ)

- **Hiện hành (Owner 06/10/2026, mở rộng decision-2 ngày 04/10/2026):** serial
  là **chuỗi nguyên văn tùy nguồn**, không bắt buộc định dạng nào, có thể
  trống, có thể trùng giữa các thửa (cùng sổ cùng serial). Quy tắc này áp ở
  mọi tầng: trích xuất, Stage, DB — **không chuẩn hóa, không thay thế**.
- Tại sao: serial trên giấy tờ thật không có định dạng chung; ép
  `[A-Z]{2}\d{6,8}` biến serial ngoài chuẩn thành số giả.
- Lịch sử: MIN-140 (29/09/2026) nguyên văn/tùy chọn → MIN-141 (03/10/2026)
  bắt buộc canonical → Owner 04–06/10/2026 quay lại nguyên văn/tùy chọn ở
  mọi nơi. Đọc hồ sơ cũ giữ serial nguyên văn, không thay bằng mã `XX`.
- Nguồn nhận dạng OCR hiện hành: `notary_v2/routers/ocr_ai.py:924-925,972`;
  thiết kế đã đồng bộ: `_bmad-output/specs/notaryoffice/intent-source.md` v1.0 §7.2
  (`[A-Z]{2}\s*\d{6,8}` — gợi ý trích xuất, không phải rule chặn nhập).
- **Owner 21/10/2026, thiết kế chưa triển khai:** serial là điểm neo gom
  các bộ thông tin Tài sản vào cùng ID. Thiếu serial không gom theo rỗng,
  không chặn lưu Nháp. Serial chung nhiều thửa không cho phép mất các hàng
  thửa/cụm đất; cấu trúc liên kết còn thiết kế. Khi lấy vào Hồ sơ mới dùng
  bộ mới nhất; Hồ sơ đã lưu giữ snapshot riêng, không tự cập nhật ngược.

---

## 3. Số vào sổ cấp GCN

- **Canonical:** tiền tố in hoa + khoảng trắng đơn + số: `CS 12345`, `CH 04321`.
- Đây là khóa **phụ**, dùng để tăng độ tin cậy, không đủ để tự ghép hồ sơ một
  mình vì tiền tố trùng nhiều giữa các xã/huyện.
- `notary_v2` gọi trường này `so_vao_so` (xem
  `_bmad-output/specs/notary_v2/input/property-rules.md`).

---

## 4. Thửa đất + Tờ bản đồ

- **Canonical:** một **cặp** hai số nguyên `(thửa, tờ)`. Không bao giờ dùng số
  thửa một mình làm khóa — số thửa trùng lặp giữa các xã.
- **Chỉ có giá trị định danh khi kèm địa phương** (xã/phường + huyện). Cặp
  `(thửa, tờ, địa phương)` mới đủ mạnh để xếp hạng cao.
- `notary_v2`: `so_thua_dat`, `so_to_ban_do`, `dia_chi`.
- `notaryoffice` dự kiến dùng tên `so_thua_dat`, `so_to_ban_do`
  (`_bmad-output/specs/notaryoffice/intent-source.md` §7.2), không quy định regex thửa/tờ tại mục đó.
- `upload_lab` chuẩn bị cả khối mô tả tài sản dưới dạng text để điền web; điều
  này không có nghĩa quy tắc bóc/kiểm không giữ được từng hàng thửa. Ví dụ
  [regex thừa kế](../_bmad-output/specs/shared/extraction-rules.md#inheritance) giữ hàng
  thửa để kiểm tra số thửa/tờ, gồm cả tình huống C03/C04 trong
  [bộ đáp án](../_bmad-output/specs/shared/extraction-rules.md#expected).
  Dạng hàng bóc tách không tự là khóa định danh canonical của tài sản hay
  contract liên kết module. Ánh xạ giữa các trường đã chốt thực hiện theo
  contract; việc ghi DB vẫn phải qua luồng kiểm tra/xác nhận của chức năng đích.
  Nếu sau này cần khớp hồ sơ giữa `upload_lab` và `notaryoffice`, phải chốt
  contract trước; không tự tạo phép ghép mới.

---

## 5. Số công chứng

- **Canonical:** `xxx/yyyy` — số thứ tự / năm 4 chữ số. Bỏ mọi hậu tố nghiệp vụ.
- Ví dụ chuẩn hóa (theo lõi chung `tools/regex_workbench/engine/contract_extract.py`
  `_normalize_web_contract_no`):

  | Raw | Canonical |
  |---|---|
  | `428/2026/CCGD` | `428/2026` |
  | `428.2026/CCGD` | `428/2026` |
  | `2433.2025/PCDS/CCGD` | `2433/2025` |
  | `2233.2025/TCDS/CCGD` | `2233/2025` |

- **Không zero-pad** số thứ tự. `07/2026` và `7/2026` là hai chuỗi khác nhau —
  nếu cần so khớp thì so bằng số nguyên, không so chuỗi.
- Không giả định hồ sơ đang soạn đã có số công chứng; không lấy trường này làm
  khóa chính bắt buộc cho mọi giai đoạn. Thời điểm cấp số thuộc nghiệp vụ owner.
- `xxx/yyyy` là tham chiếu hồ sơ trong **phạm vi sổ/đơn vị phát hành tương ứng**,
  không phải ID toàn cục. Giữ provenance/phạm vi khi đối chiếu xuyên nguồn;
  chưa đủ phạm vi thì chỉ tạo candidate link, không tự gộp.

---

## 6. Tên người — không đứng một mình để gom ID

Trùng họ tên **không bao giờ** đủ để tự động ghép hai dữ liệu thành một hồ sơ.
Được dùng để tìm kiếm, hiển thị. Owner 21/10/2026 chốt **tên + số giấy tờ
đồng thời giống nhau** là điểm neo tự dùng cùng ID Người (§8.3); tên riêng lẻ
không đủ. Quy tắc đó không tự gộp các Hồ sơ thành một record.

Lý do: tên Việt trùng lặp rất cao trong cùng một địa phương, và một lần gán sai
trong nghề công chứng đắt hơn hai mươi lần gán đúng.

---

## 7. Độ mạnh theo đối tượng — không phải thứ bậc khóa hồ sơ

| Tham chiếu | Đối tượng/phạm vi | Được dùng để |
|---|---|---|
| CCCD 12 số | Người được giấy tờ định danh | Đối chiếu người; tìm hồ sơ có người đó, không tự gộp Case |
| Tên + số giấy tờ đồng thời | Người | Owner 21/10: tự dùng cùng ID Người; không tự gộp Case |
| Serial GCN | Giấy chứng nhận, dẫn tới tài sản liên quan | Owner 21/10: điểm neo cùng ID Tài sản; không suy ra một hồ sơ duy nhất |
| Thửa + tờ + địa phương | Thửa đất trong phạm vi địa phương | Xếp hạng tài sản/hồ sơ liên quan; giữ nguồn và bước xác nhận |
| Số công chứng + năm + phạm vi sổ/đơn vị | Hồ sơ có tham chiếu công chứng | Liên kết khi đủ phạm vi và bằng chứng, không coi `xxx/yyyy` là ID toàn cục |
| Số vào sổ GCN | Tham chiếu phụ giấy chứng nhận | Bổ sung bằng chứng, không đứng một mình để ghép hồ sơ |
| Đường dẫn, họ tên | Ngữ cảnh yếu | Tìm kiếm/xếp hạng, không tự gán hoặc gộp record |

Không có thứ tự mạnh/yếu chung để thay thế định danh người bằng định danh hồ
sơ. Một người/tài sản có thể liên quan nhiều hồ sơ. Gom ID Người/Tài sản theo
điểm neo owner chọn không đồng nghĩa gộp hoặc liên kết các Case xuyên module.
Liên kết Case là inference
có provenance, được người có thẩm quyền xác nhận theo owner; chuẩn hóa thành
công không tự nâng dữ liệu thành `CONFIRMED`.

Điểm bám thiết kế: `_bmad-output/specs/notaryoffice/intent-source.md` §7 phân biệt `entities`,
`cases` và `case_entities` M:N; `:385-394` mô tả xếp hạng rồi xác nhận.
Không suy ra số lượng quan hệ Case giữa hai repo từ quan hệ nội bộ này; xem
[`../_bmad-output/specs/README.md`](../_bmad-output/specs/README.md) mục 5. Không định nghĩa thêm
shared ID/schema trong lần sửa này.

---

## 8. Từ điển dữ liệu Người (`customers`) và các trường suy ra

Cập nhật chốt từ Owner (01/10/2026): Từ điển người chuẩn hóa gồm 6 trường nghiệp vụ chính lưu cơ sở dữ liệu và 3 nhóm trường suy ra phục vụ hiển thị / soạn thảo văn bản.

### 8.1. Các trường lưu CSDL (bảng `customers`)

| Tên trường canonical | Tên thuộc tính DB | Kiểu dữ liệu | Mô tả |
|---|---|---|---|
| `ten` | `ho_ten` | String(200) | Họ và tên, người dùng nhập liệu hoặc OCR |
| `ngaysinh` | `ngay_sinh` | Date | Ngày tháng năm sinh (hoặc năm sinh) |
| `ngaychet` | `ngay_chet` | Date | Ngày/năm chết; `NULL` là không có thông tin ngày chết, không tự kết luận còn sống |
| `sogiayto` | `so_giay_to` | String(50) | Số giấy tờ (người chết: khai tử/chứng tử); giữ nguyên giá trị gồm dấu phẩy/phần quyển, không gồm nhãn, không ép CCCD |
| `ngaycap` | `ngay_cap` | Date | Ngày cấp chính giấy đang dùng, người chết là giấy khai tử/chứng tử, không phải ngày chết |
| `diachi` | `dia_chi` | Text | Một trường địa chỉ: người chết dùng chung cho Nơi chết và nơi thường trú/cư trú cuối cùng; không tạo thêm trường |

**Owner 15/10/2026 — độ đầy đủ của ngày:** bảng trên mô tả kiểu lưu hiện có,
không cho phép làm mất dữ liệu chỉ có năm. Lưu/đọc lại và hiển thị phải phân biệt
`2010` với ngày thật `01/01/2010`; ngày quy ước chỉ phục vụ tính toán nội bộ.
Cách giữ dữ liệu nhập/độ đầy đủ trong lưu trữ phải kiểm riêng khi triển khai,
không suy từ kiểu `Date` rằng đã đáp ứng hoặc tự tạo cột trong lần sửa docs này.

**Owner 21/10/2026:** thiếu ngày chết giữ `null`/rỗng theo contract; có trường
nào có căn cứ được phép thì điền trường đó độc lập, không chặn Người vì thiếu
ngày chết/bộ giấy. Không bịa ngày, đệm 01/01, tạo Boolean/status mới hoặc tự
phân loại còn sống. Một trường địa chỉ không cho phép tự chọn giữa các giá
trị mâu thuẫn hay tự điền từ người/văn bản khác.

Ngoài 6 trường nghiệp vụ chính, DB hiện vẫn giữ `gioi_tinh`, ID và thời gian tạo; không xóa các cột này.

*Ghi chú về quê quán (`place_of_origin`):* Chỉ lưu snapshot trong từng hồ sơ (`case_state_json` / contract `person_row`), không đưa vào danh bạ `customers` master.

### 8.2. Trường suy ra và bằng chứng được xác nhận

Hành vi cuối MIN-141, Owner xác nhận 03/10/2026:

- Người sống có ngày cấp: trước 01/10/2024 dùng `Căn cước công dân`,
  `Cục cảnh sát quản lý hành chính về trật tự xã hội`, `Thường trú` /
  `Thường trú tại`; từ mốc dùng `Căn cước`, `Bộ Công an`, `Cư trú` /
  `Cư trú tại`. Thiếu ngày cấp → để trống, không đoán cơ quan.
- Người đã chết: loại giấy tờ và nơi cấp theo bằng chứng được xác nhận trong
  snapshot hồ sơ; thiếu thì để trống, không default giấy hoặc UBND.
  Owner 21/10/2026 chốt ba loại: `Trích lục khai tử`,
  `Trích lục khai tử (bản sao)`, `Giấy chứng tử`; nguồn `Giấy chứng tử (bản sao)`
  quy về `Giấy chứng tử`. Giữ loại đơn vị cơ quan xã/phường/thị trấn, không ép
  thành xã; tên lịch sử theo **ngày cấp giấy**, không theo ngày chết/hiện tại,
  không suy lịch sử chưa xác nhận. `Nơi chết` và cư trú cuối dùng cùng `diachi`,
  nhãn Word/logic câu hiện có không đổi.
- Mỗi văn bản nguồn độc lập: không đề xuất bổ sung hoặc tự ghép giữa văn bản,
  kể cả cùng bộ hồ sơ; không mượn dữ kiện hoặc chọn bản đầy nhất/mới nhất.
  Không gợi ý sinh/chết/giấy tờ Người từ `Đơn xin xác nhận`, kể cả qua suy ra.
  Raw/history và liên kết Case/ID đã có giữ nguyên. Địa chỉ chung chỉ áp cho
  đúng người được chỉ rõ trong cùng văn bản, không chứng minh chung giấy.
  Đây là luật không tự bổ sung nội dung giấy tờ; gom ID theo tên + số giấy tờ
  ở §8.3 không bị cấm, không cho phép mượn trường thiếu giữa văn bản.
- Khi người dùng sửa ngày cấp/ngày chết, hệ thống tính lại giá trị từng tự
  suy ra; giá trị người dùng đã sửa khác giá trị suy ra được giữ lại.
- Word đọc giá trị đã commit trong snapshot của chính hồ sơ, kể cả null;
  chỉ dùng dữ liệu master nếu snapshot cũ thiếu key đó.

**Tại sao:** không để thay đổi danh bạ dùng chung làm đổi văn bản của hồ sơ
đã lưu, không biến dữ liệu thiếu thành bằng chứng pháp lý.

Ý định ban đầu suy UBND theo mốc 01/07/2025 được giữ làm lịch sử; bảng tra
xã/phường cũ–mới còn ở NAIA-9, chưa có đường suy tự động trong runtime.

**Runtime Người chết 21/10/2026 — BUILT bounded, actual proof synthetic:** số giấy
lưu nguyên giá trị vào `customers.so_giay_to`, index không UNIQUE; identity
là `Customer.id`, không tự lookup/ghép theo số hoặc tên. Cập nhật Người qua
ID đã chọn rõ hoặc `row_id` của chính hồ sơ đã lưu; hiện cùng số có thể tồn tại
ở nhiều Người, kể cả CCCD. Đây là hiện trạng, chưa thực hiện điểm neo mới ở §8.3.
Migration trước bootstrap giữ ID/FK/columns/defaults/checks/indexes/triggers
và snapshot/history, rollback nguyên tử khi lỗi.
Loại/nơi cấp và nhãn địa chỉ tiếp tục theo snapshot từng hồ sơ, không thêm
cột/model #42; không mượn master để lấp key snapshot đã có kể cả null.
Ngữ cảnh chết thiếu ngày dùng loại giấy/nhãn `Nơi chết` hiện có đã có nguồn,
không Boolean mới. Master riêng không có context snapshot không thể phục
hồi dữ kiện chết chưa lưu; không suy để lấp. #41 vẫn mở/chưa nghiệm thu toàn bộ.

<a id="83-owner-21102026--gợi-ý-cccd-người-dùng-quyết-định-liên-kết"></a>
### 8.3. Owner 21/10/2026 — tên + số giấy tờ là điểm neo gom Người

**Quyết định mới thay policy gợi ý/user chọn ở `8b4e85f`; chưa triển khai.**
Một bảng Người cho sống/chết; ID kỹ thuật vẫn là `Customer.id`.

- Đồng thời tên và số giấy tờ giống nhau → tự dùng cùng ID, không đòi user
  bấm liên kết. Ngày cấp/địa chỉ khác vẫn cùng ID. Chỉ trùng một trong hai
  không đủ; đổi tên hoặc số thì chấp nhận thành ID khác.
- Không thêm loại giấy/ngày sinh/ngày cấp/địa chỉ vào điều kiện gom. Không
  coi số giấy tờ riêng lẻ là UNIQUE toàn cục hoặc chặn vì số đã tồn tại.
- Tìm Người để xem các Hồ sơ liên quan; không bắt đọc danh sách thay đổi từng
  trường. Khi lấy Người vào Hồ sơ mới mặc định bộ mới nhất, không chọn phiên bản.
- Mỗi Hồ sơ đã lưu giữ snapshot riêng, kể cả null; dữ liệu mới ở nơi khác
  không tự đổi Hồ sơ cũ. User có thể sửa trực tiếp Hồ sơ theo quyền hiện hành.
  Các bộ thông tin khác nhau vẫn giữ qua các Hồ sơ, không thêm lịch sử từng ô.
- **Owner 22/10:** tên so không phân biệt dấu/hoa-thường, giữ tên gốc; không
  mở thành fuzzy tùy ý. Mới nhất theo Hồ sơ lưu gần nhất, chỉ nguồn `done`,
  không `draft`. Nhiều ID trùng cũ giữ nguyên, không tự hợp nhất; lấy bộ cuối.
  Thiếu tên/số không gom và không chặn lưu Nháp. Lifecycle ID của dòng đang
  nhập dở qua nhiều lần Cập nhật/Lưu hồ sơ đang rà soát, chưa chọn schema.
- Quy tắc gom ID không cho phép tự bổ sung dữ kiện giữa văn bản, xác nhận
  dữ kiện thay user hoặc xóa/hợp nhất dữ liệu lịch sử. Không suy còn sống
  từ ngày chết null. Không áp mô hình “thông tin liên kết” của policy cũ
  làm yêu cầu mặc định; nguồn/bằng chứng đã có vẫn giữ.

Runtime `f6d53b5` vẫn không tự tìm theo tên/số và có thể cập nhật master khi
ghi theo ID rõ; chưa thực hiện quy tắc mới. Không sửa schema/index trong
quyết định này. #41 OPEN/gate mẫu ĐÓNG, #42 độc lập; #44 cần điều chỉnh theo
[quyết định điểm neo/snapshot](../_bmad-output/decisions/decision-owner-entity-anchors-case-snapshots-20261021.md).

---

## 9. Chuẩn hóa Bảng Tài sản, Bảng Hồ sơ & Quy tắc đặt tên trường

### 9.1. Quy tắc chung đặt tên trường (Rule chung)

- **Định dạng bắt buộc:** Tiếng Việt không dấu, viết thường toàn bộ, **viết liền không dấu, tuyệt đối KHÔNG có dấu gạch dưới `_` hay dấu cách**.
- **Phạm vi quy ước:** áp cho **tên trường nghiệp vụ mới** và **tên canonical/họ token viết liền của placeholder** — gồm trường hồ sơ (`noiniemyet`, `nguoinhanuyquyen`, `noidungviec`, …), cụm đất `loaidat<M><N>`/`dientich<M><N>`/`thoihan<M><N>` (§9.2) và các alias viết liền được hỗ trợ. Quy ước này đặt tên **trường/khóa**, không đặt mặt chữ của mẫu: **placeholder trong mẫu mới** viết theo dạng nhóm dễ đọc `[Tên danh sách N - Trường]` (ví dụ `[Người 3 - Họ tên]`) tại [`word-templates.md` §4.1](../_bmad-output/specs/notary_v2/word-templates.md#placeholders); tên viết liền canonical vẫn được thay nhưng giữ slot legacy và tương ứng alias cũ — không đồng nhất thứ tự với nhóm dễ đọc của mẫu mới; alias cũ chỉ để mở template cũ.
- Tên cột DB và dữ liệu giao tiếp cũ như `loai_dat`, `so_giay_to` vẫn được giữ để tương thích; không đổi toàn bộ cột/schema. Các alias được hỗ trợ cụ thể ghi tại `notary-case-drafting.md`, không mặc định mọi tên chuẩn đều là key gửi được.
- **Ví dụ đúng:** `ten`, `ngaysinh`, `ngaychet`, `sogiayto`, `ngaycap`, `diachi`, `noicap`, `loaigiayto`, `loaicutru`, `noiniemyet`, `nguoinhanuyquyen`, `noidungviec`, `loaidat11`, `dientich11`, `thoihan11`, `loaidat12`, `dientich12`, `thoihan12`.

### 9.2. Bảng Tài sản (`properties`) — Phân biệt loại đất thứ mấy trong tài sản thứ mấy

- **Lưu trữ (MIN-141 đợt 2):** mỗi cụm đất là một bản ghi trong bảng con `property_land_rows(property_id, vitri, loaidat, dientich, thoihan)`, UNIQUE `(property_id, vitri)`; `vitri` = vị trí cụm trong tài sản (1–20, giữ nguyên vị trí trống). `properties.land_rows_json` chỉ còn làm nguồn tương thích/chuyển đổi — không còn là nguồn lưu chính. `N` (vị trí tài sản trong hồ sơ) **không** được ghi cứng vào master — N chỉ xuất hiện trong tên placeholder Word/snapshot của từng hồ sơ.
- **Loại bỏ trường lẻ:** Trường `thoi_han` ở cấp tài sản là trường mồ côi → loại bỏ khỏi đường xuất cụm; không tự đắp vào cụm khi không xác định được cụm tương ứng (báo cần đối chiếu, giữ nguyên bản gốc).
- **Cụm thông tin loại đất:** Thông tin đất luôn đi liền theo bộ 3 trường: `loaidat` - `dientich` - `thoihan`.
- **Cú pháp định danh phân biệt Loại đất thứ mấy trong Tài sản thứ mấy:**
  * Cấu trúc: `[tên_trường][chỉ_số_loại_đất][chỉ_số_tài_sản]` (viết liền, không có `_`).
  * Trong đó:
    - Ký tự chữ: `loaidat`, `dientich`, `thoihan`.
    - Chữ số đầu: **Loại đất thứ mấy** trong tài sản (từ 1 đến 20).
    - Chữ số sau: **Tài sản thứ mấy** trong hồ sơ (từ 1 đến 3).

| Tên trường (Không có `_`) | Ý nghĩa nghiệp vụ | Ví dụ minh họa |
|---|---|---|
| `loaidat11` | Loại đất **1** của Tài sản **1** | `ONT` / Đất ở |
| `dientich11` | Diện tích loại đất **1** của Tài sản **1** | `120.5` |
| `thoihan11` | Thời hạn loại đất **1** của Tài sản **1** | `Lâu dài` |
| `loaidat21` | Loại đất **2** của Tài sản **1** | `CLN` |
| `loaidat12` | Loại đất **1** của Tài sản **2** | `LUC` |
| `dientich12` | Diện tích loại đất **1** của Tài sản **2** | `500` |
| `thoihan12` | Thời hạn loại đất **1** của Tài sản **2** | `2063` |
| `loaidat22` | Loại đất **2** của Tài sản **2** | `BHK` |
| `loaidat13` | Loại đất **1** của Tài sản **3** | `HNK` |
| `loaidat23` | Loại đất **2** của Tài sản **3** | `RSX` |
| `loaidat102` | Loại đất **10** của Tài sản **2** | `NTS` |

*Ghi chú (quyết định MIN-141, review 29/09/2026):* chỉ dùng dạng đầy đủ `loaidat<M><N>` cho **mọi** hồ sơ, kể cả hồ sơ 1 tài sản — không cung cấp alias rút gọn `loaidatM`/`loaidat1`. Lý do: dạng rút gọn `loaidat12` đọc được thành "cụm 1 của tài sản 2" hoặc "cụm 12 của tài sản 1" → dễ trùng nghĩa khi template dùng lại giữa hồ sơ 1 và nhiều tài sản; một quy ước duy nhất loại trừ mập mờ.

### 9.3. Bảng Hồ sơ (`inheritance_cases`)

1. **`noiniemyet` (Nơi niêm yết):** hiện người dùng nhập và lưu theo hồ sơ; thiếu thì để trống khi xuất Word, không lấy địa chỉ đất thay thế. Tra cứu UBND từ địa chỉ đất + bảng xã cũ/mới là hướng còn mở tại NAIA-9.
2. **`nguoinhanuyquyen` (Người nhận ủy quyền):** Người nhận ủy quyền giải quyết công việc — chọn từ danh mục người quen hay ủy quyền hoặc cho phép tạo mới.
3. **`noidungviec` (Nội dung việc):** Cụm text nhập thủ công mô tả công việc (ví dụ: *"Đính chính hộ ông A thành ông A và bà B"*, *"Đính chính năm sinh ông A từ 1955 thành 1950"*...).
4. **Bố cục giao diện (UI):** Thêm 3 dòng trường hồ sơ ngay dưới các dòng tài sản; giảm 10% chiều cao các ô nhập liệu để giữ giao diện tổng thể gọn gàng, không phải cuộn nhiều.

### 9.4. Metadata Hồ sơ Upload — triển khai phạm vi Case

Owner giao triển khai chuẩn hóa Case và làm rõ chủ đất: **“người được gán chủ
đất trong diagram”**. Không mở model Người/Tài sản/vai trò mới hoặc khép toàn #41.

| Key canonical | Kiểu | Nguồn / nghĩa |
|---|---|---|
| `tenvanban` | string/null | Tiêu đề nguồn, không enum Notary |
| `nhomhopdong` | string/null | Nhóm portal, có scope website của lượt quét |
| `loaivanbannhandien` | string/null | Loại engine nhận diện, độc lập enum Notary |
| `socongchung` | string/null | `xxx/yyyy` theo §5, không Case ID toàn cục |
| `ngaycongchung` | ISO full date/null | Ngày công chứng, khác ngày lập hồ sơ |
| `congchungvien` | string/null | Tên từ nguồn hoặc lựa chọn prepare rõ ràng |
| `thuky` | string/null | Tên từ input prepare; không tự đoán |
| `chudat` | string/null | Tên snapshot Người được chọn Chủ trên Diagram đã lưu |

Thứ tự trường theo bảng. Thiếu là `null`, không chuỗi rỗng/default giả.
`chudat` lấy `personId` của node có `ownPositions` trỏ tài sản hiện có (1..3),
không hidden/deleted; đọc tên Stage committed theo ID, mỗi Người một dòng
theo thứ tự Stage, dedup theo row ID, không dedup theo tên.
Không đồng nhất với `owner_row_id`/slot `owner`; không suy từ Word/GCN/Bên A.
Hai bên không có lựa chọn Chủ và Upload không có Diagram: `chudat = null`.

Upload lưu record Case nhỏ có schema cố định trong DB registry cục bộ; không
nhân đôi payload lớn. JSON extraction/nguồn cũ giữ nguyên; form builder đọc Case rồi đổi ngày
sang `DD/MM/YYYY` tại biên portal. Notary giữ metadata trong snapshot
`case_state_json.payload.case`, derivation chủ đất trong transaction commit/save.
Không ghi chéo DB, không tạo shared Case ID. Raw/Person/Asset/parties giữ nguyên.
