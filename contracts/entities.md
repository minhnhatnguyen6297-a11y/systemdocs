# Định danh hồ sơ — định nghĩa dùng chung

**Phạm vi:** file này định nghĩa *ý nghĩa và cách chuẩn hóa* định danh người,
giấy chứng nhận/tài sản và tham chiếu hồ sơ. Chúng cung cấp bằng chứng tìm hồ
sơ liên quan, không mặc nhiên chứng minh "cùng một hồ sơ". Không áp đặt regex,
tên biến, schema DB hay dùng định danh người/tài sản làm khóa chính Case.

**Bắt buộc:** khi một repo trích xuất hoặc so khớp một trong các khóa dưới đây,
nó phải chuẩn hóa về **dạng canonical** ghi ở đây trước khi so sánh hoặc trước
khi ghi vào trường "khóa định danh". Giữ raw và provenance theo
`SYSTEM_ARCHITECTURE.md` §6.2; chuẩn hóa không được ghi đè bằng chứng gốc.

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
| `notaryoffice` (dự kiến) | `\b\d{12}\b` (`notaryoffice/docs/SPEC.md` v1.0 §7.2, ~dòng 413) | Đã bỏ ràng buộc số 0 đầu; chưa có implementation |

**Quy tắc thống nhất:** dù regex nào, giá trị đem đi so khớp phải là đúng 12 chữ
số. Không so khớp một phần, không so khớp 9 số cuối.

---

## 2. Số serial GCN (sổ đỏ)

- **Canonical:** 2 chữ cái in hoa + **6–8 chữ số**, không dấu cách: `DD123456`.
- Khi hiển thị cho người dùng có thể chèn dấu cách (`DD 123456`); khi so khớp thì
  không.
- Dải được hệ thống chấp nhận là `[A-Z]{2}` + 6–8 số; chuẩn hóa bằng cách bỏ
  khoảng trắng và viết hoa. Nguồn hiện hành:
  `notary_v2/routers/ocr_ai.py:919-922,968`; thiết kế đã đồng bộ:
  `notaryoffice/docs/SPEC.md` v1.0 §7.2 (~dòng 414, `[A-Z]{2}\s*\d{6,8}`).

---

## 3. Số vào sổ cấp GCN

- **Canonical:** tiền tố in hoa + khoảng trắng đơn + số: `CS 12345`, `CH 04321`.
- Đây là khóa **phụ**, dùng để tăng độ tin cậy, không đủ để tự ghép hồ sơ một
  mình vì tiền tố trùng nhiều giữa các xã/huyện.
- `notary_v2` gọi trường này `so_vao_so` (xem
  `docs/platform/document-intake/property-rules.md`).

---

## 4. Thửa đất + Tờ bản đồ

- **Canonical:** một **cặp** hai số nguyên `(thửa, tờ)`. Không bao giờ dùng số
  thửa một mình làm khóa — số thửa trùng lặp giữa các xã.
- **Chỉ có giá trị định danh khi kèm địa phương** (xã/phường + huyện). Cặp
  `(thửa, tờ, địa phương)` mới đủ mạnh để xếp hạng cao.
- `notary_v2`: `so_thua_dat`, `so_to_ban_do`, `dia_chi`.
- `notaryoffice` dự kiến dùng tên `so_thua_dat`, `so_to_ban_do`
  (`notaryoffice/docs/SPEC.md` §7.2, ~:415-416), không quy định regex thửa/tờ
  tại mục đó.
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

Điểm bám thiết kế: `notaryoffice/docs/SPEC.md` §7.3 (~:418-472) phân biệt
`entities`, `cases` và `case_entities` M:N; §8.1–8.2 (~:475-508) mô tả xếp
hạng rồi xác nhận.
Không suy ra cardinality giữa Case của hai module từ quan hệ nội bộ này; xem
`SYSTEM_ARCHITECTURE.md` §7. Không định nghĩa thêm shared ID/schema trong lần sửa này.
