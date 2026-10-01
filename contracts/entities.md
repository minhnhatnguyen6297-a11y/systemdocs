# Định danh hồ sơ — định nghĩa dùng chung

**Phạm vi:** file này định nghĩa *ý nghĩa và cách chuẩn hóa* định danh người,
giấy chứng nhận/tài sản và tham chiếu hồ sơ. Chúng cung cấp bằng chứng tìm hồ
sơ liên quan, không mặc nhiên chứng minh "cùng một hồ sơ". Không áp đặt regex,
tên biến, schema DB hay dùng định danh người/tài sản làm khóa chính Case.

**Bắt buộc:** khi một repo trích xuất hoặc so khớp một trong các khóa dưới đây,
nó phải chuẩn hóa về **dạng canonical** ghi ở đây trước khi so sánh hoặc trước
khi ghi vào trường "khóa định danh". Giữ raw và nguồn gốc theo
[`../docs/spec/README.md`](../docs/spec/README.md) mục 4; chuẩn hóa không được
ghi đè bằng chứng gốc.

Cập nhật: 10/09/2026

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
| `upload_lab` | Neo theo nhãn: `(?:Căn cước\|CCCD\|CMND)\s*(?:số)?\s*:?\s*(\d+)` (`extract_contract.py`) | Chặt theo ngữ cảnh vì text Word có sẵn nhãn |
| `notaryoffice` (dự kiến) | `\b\d{12}\b` (`docs/spec/notaryoffice/intent-source.md` v1.0 §7.2) | Đã bỏ ràng buộc số 0 đầu; chưa có implementation |

**Quy tắc thống nhất:** dù regex nào, giá trị đem đi so khớp phải là đúng 12 chữ
số. Không so khớp một phần, không so khớp 9 số cuối.

---

## 2. Số serial GCN (sổ đỏ)

- **Canonical:** 2 chữ cái in hoa + **6–8 chữ số**, không dấu cách: `DD123456`.
- Khi hiển thị cho người dùng có thể chèn dấu cách (`DD 123456`); khi so khớp thì
  không.
- Dải được hệ thống chấp nhận là `[A-Z]{2}` + 6–8 số; chuẩn hóa bằng cách bỏ
  khoảng trắng và viết hoa. Nguồn hiện hành:
  `notary_v2/routers/ocr_ai.py:924-925,972`; thiết kế đã đồng bộ:
  `docs/spec/notaryoffice/intent-source.md` v1.0 §7.2 (`[A-Z]{2}\s*\d{6,8}`).

---

## 3. Số vào sổ cấp GCN

- **Canonical:** tiền tố in hoa + khoảng trắng đơn + số: `CS 12345`, `CH 04321`.
- Đây là khóa **phụ**, dùng để tăng độ tin cậy, không đủ để tự ghép hồ sơ một
  mình vì tiền tố trùng nhiều giữa các xã/huyện.
- `notary_v2` gọi trường này `so_vao_so` (xem
  `docs/spec/notary_v2/input/property-rules.md`).

---

## 4. Thửa đất + Tờ bản đồ

- **Canonical:** một **cặp** hai số nguyên `(thửa, tờ)`. Không bao giờ dùng số
  thửa một mình làm khóa — số thửa trùng lặp giữa các xã.
- **Chỉ có giá trị định danh khi kèm địa phương** (xã/phường + huyện). Cặp
  `(thửa, tờ, địa phương)` mới đủ mạnh để xếp hạng cao.
- `notary_v2`: `so_thua_dat`, `so_to_ban_do`, `dia_chi`.
- `notaryoffice` dự kiến dùng tên `so_thua_dat`, `so_to_ban_do`
  (`docs/spec/notaryoffice/intent-source.md` §7.2), không quy định regex thửa/tờ tại mục đó.
- `upload_lab` hiện **không tách thửa/tờ thành trường riêng** — nó trích cả khối
  mô tả tài sản dưới dạng text để điền web. Nếu sau này cần khớp hồ sơ giữa
  `upload_lab` và `notaryoffice`, đây là việc phải làm thêm ở `upload_lab`.

---

## 5. Số công chứng

- **Canonical:** `xxx/yyyy` — số thứ tự / năm 4 chữ số. Bỏ mọi hậu tố nghiệp vụ.
- Ví dụ chuẩn hóa (theo `upload_lab/extract_contract.py`
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

## 6. Tên người — KHÔNG phải khóa

Trùng họ tên **không bao giờ** đủ để tự động ghép hai dữ liệu thành một hồ sơ.
Được dùng để: xếp hạng ứng viên, tìm kiếm, hiển thị. Không được dùng để: tự động
gán, tự động gộp record.

Lý do: tên Việt trùng lặp rất cao trong cùng một địa phương, và một lần gán sai
trong nghề công chứng đắt hơn hai mươi lần gán đúng.

---

## 7. Độ mạnh theo đối tượng — không phải thứ bậc khóa hồ sơ

| Tham chiếu | Đối tượng/phạm vi | Được dùng để |
|---|---|---|
| CCCD 12 số | Người được giấy tờ định danh | Đối chiếu người; tìm hồ sơ có người đó, không tự gộp Case |
| Serial GCN | Giấy chứng nhận, dẫn tới tài sản liên quan | Đối chiếu giấy tờ/tài sản; không suy ra một hồ sơ duy nhất |
| Thửa + tờ + địa phương | Thửa đất trong phạm vi địa phương | Xếp hạng tài sản/hồ sơ liên quan; giữ nguồn và bước xác nhận |
| Số công chứng + năm + phạm vi sổ/đơn vị | Hồ sơ có tham chiếu công chứng | Liên kết khi đủ phạm vi và bằng chứng, không coi `xxx/yyyy` là ID toàn cục |
| Số vào sổ GCN | Tham chiếu phụ giấy chứng nhận | Bổ sung bằng chứng, không đứng một mình để ghép hồ sơ |
| Đường dẫn, họ tên | Ngữ cảnh yếu | Tìm kiếm/xếp hạng, không tự gán hoặc gộp record |

Không có thứ tự mạnh/yếu chung để thay thế định danh người bằng định danh hồ
sơ. Một người/tài sản có thể liên quan nhiều hồ sơ. Liên kết Case là inference
có provenance, được người có thẩm quyền xác nhận theo owner; chuẩn hóa thành
công không tự nâng dữ liệu thành `CONFIRMED`.

Điểm bám thiết kế: `docs/spec/notaryoffice/intent-source.md` §7 phân biệt `entities`,
`cases` và `case_entities` M:N; `:385-394` mô tả xếp hạng rồi xác nhận.
Không suy ra số lượng quan hệ Case giữa hai repo từ quan hệ nội bộ này; xem
[`../docs/spec/README.md`](../docs/spec/README.md) mục 5. Không định nghĩa thêm
shared ID/schema trong lần sửa này.

---

## 8. Từ điển dữ liệu Người (`customers`) và các trường suy ra

Cập nhật chốt từ Owner (01/10/2026): Bảng người chuẩn hóa gồm 6 trường lưu trữ cơ sở dữ liệu và 3 nhóm trường suy ra phục vụ hiển thị / soạn thảo văn bản.

### 8.1. Các trường lưu CSDL (bảng `customers`)

| Tên trường canonical | Tên thuộc tính DB | Kiểu dữ liệu | Mô tả |
|---|---|---|---|
| `ten` | `ho_ten` | String(200) | Họ và tên, người dùng nhập liệu hoặc OCR |
| `ngaysinh` | `ngay_sinh` | Date | Ngày tháng năm sinh (hoặc năm sinh) |
| `ngaychet` | `ngay_chet` | Date | Ngày chết (`NULL` nếu còn sống) |
| `sogiayto` | `so_giay_to` | String(50) | Số giấy tờ định danh (người sống: số CCCD/CC; người chết: số giấy khai tử / trích lục khai tử) |
| `ngaycap` | `ngay_cap` | Date | Ngày cấp giấy tờ định danh (ngày cấp CCCD hoặc ngày cấp trích lục khai tử) |
| `diachi` | `dia_chi` | Text | Địa chỉ người sống; nơi chết / nơi thường trú cuối cùng trước khi chết của người chết |

*Ghi chú về quê quán (`place_of_origin`):* Chỉ lưu snapshot trong từng hồ sơ (`case_state_json` / contract `person_row`), không đưa vào danh bạ `customers` master.

### 8.2. Các trường suy ra backend (@property, KHÔNG lưu DB)

Các trường này được tính toán động qua công thức backend và kết quả OCR, không tạo cột trong DB:

1. **`loaigiayto` (`loai_giay_to`) — Loại giấy tờ:**
   - **Người sống (`con_song == True`):** Lấy mốc **01/10/2024** làm chuẩn:
     * Trước 01/10/2024: `Căn cước công dân`.
     * Từ 01/10/2024 trở đi: `Căn cước`.
   - **Người chết (`con_song == False`):** Suy ra từ loại giấy tờ khai tử (OCR hoặc lựa chọn): `Trích lục khai tử`, `Trích lục khai tử (Bản sao)`, `Giấy chứng tử`... Mặc định: `Trích lục khai tử (Bản sao)`.

2. **`noicap` (`noi_cap`) — Nơi cấp giấy tờ định danh:**
   - **Người sống (`con_song == True`):** Lấy mốc **01/10/2024** làm chuẩn:
     * Trước 01/10/2024: `Cục cảnh sát quản lý hành chính về trật tự xã hội`.
     * Từ 01/10/2024 trở đi: `Bộ Công an`.
     * Trường hợp `ngaycap` trống: fallback cơ quan cấp theo quy định hoặc hiển thị theo OCR.
   - **Người chết (`con_song == False`):** Lấy mốc **01/07/2025** (sáp nhập đơn vị hành chính) làm chuẩn:
     * Trước 01/07/2025: `UBND xã/phường cũ cấp`.
     * Từ 01/07/2025 trở đi: `UBND xã/phường mới cấp` (tra cứu qua bảng chuẩn hóa xã cũ - mới sau sáp nhập).

3. **`loaicutru` (`loai_dia_chi`) — Loại cư trú / nhãn địa chỉ:**
   - Lấy mốc **01/10/2024** làm chuẩn:
     * Trước 01/10/2024: `Thường trú` (hoặc `Thường trú tại`).
     * Từ 01/10/2024 trở đi: `Cư trú` (hoặc `Cư trú tại`).

---

## 9. Chuẩn hóa Bảng Tài sản, Bảng Hồ sơ & Quy tắc đặt tên trường

### 9.1. Quy tắc chung đặt tên trường (Rule chung)

- **Định dạng bắt buộc:** Tiếng Việt không dấu, viết thường toàn bộ, **viết liền không dấu, tuyệt đối KHÔNG có dấu gạch dưới `_` hay dấu cách**.
- **Cấm:** Không dùng snake_case (`loai_dat`, `so_giay_to`), không dùng kebab-case (`loai-dat`), không dùng camelCase (`loaiDat`).
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

1. **`noiniemyet` (Nơi niêm yết):** UBND cấp xã nơi có đất → suy ra từ địa chỉ thửa đất và chuẩn hóa qua bảng tra cứu xã cũ - mới sau sáp nhập 01/07/2025.
2. **`nguoinhanuyquyen` (Người nhận ủy quyền):** Người nhận ủy quyền giải quyết công việc — chọn từ danh mục người quen hay ủy quyền hoặc cho phép tạo mới.
3. **`noidungviec` (Nội dung việc):** Cụm text nhập thủ công mô tả công việc (ví dụ: *"Đính chính hộ ông A thành ông A và bà B"*, *"Đính chính năm sinh ông A từ 1955 thành 1950"*...).
4. **Bố cục giao diện (UI):** Thêm 3 dòng trường hồ sơ ngay dưới các dòng tài sản; giảm 10% chiều cao các ô nhập liệu để giữ giao diện tổng thể gọn gàng, không phải cuộn nhiều.

