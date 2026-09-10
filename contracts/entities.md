# Định danh hồ sơ — định nghĩa dùng chung

**Phạm vi:** file này định nghĩa *ý nghĩa và cách chuẩn hóa* các khóa dùng để
nhận ra "hai dữ liệu này nói về cùng một hồ sơ". Nó **không** áp đặt regex,
không áp đặt tên biến, không áp đặt schema DB.

**Bắt buộc:** khi một repo trích xuất hoặc so khớp một trong các khóa dưới đây,
nó phải chuẩn hóa về **dạng canonical** ghi ở đây trước khi so sánh hoặc trước
khi ghi vào trường "khóa định danh". Muốn lưu thêm dạng raw thì tùy repo.

Cập nhật: 09/09/2026

---

## 1. CCCD — Số căn cước công dân

- **Canonical:** 12 chữ số liền nhau, không dấu cách, không dấu chấm.
- **Không dùng làm khóa:** CMND 9 số. Nếu chỉ có CMND 9 số, coi là dữ liệu phụ,
  không dùng để tự động ghép hồ sơ.
- **Nguồn đọc được cả hai:** mã MRZ hộ chiếu/CCCD dạng `IDVNM(\d{9})(\d)(\d{12})`
  chứa cả CMND cũ và CCCD mới — lấy nhóm 12 số làm CCCD.

**Ba repo hiện làm khác nhau — chưa cần sửa, nhưng phải biết:**

| Repo | Cách nhận | Ghi chú |
|---|---|---|
| `notary_v2` | `(?<!\d)(\d{12})(?!\d)` — mọi cụm 12 số (`routers/ocr_ai.py`) | Rộng nhất, vì OCR ảnh hay mất chữ đầu |
| `upload_lab` | Neo theo nhãn: `(?:Căn cước\|CCCD\|CMND)\s*(?:số)?\s*:?\s*(\d+)` (`extract_contract.py`) | Chặt theo ngữ cảnh vì text Word có sẵn nhãn |
| `notaryoffice` (dự kiến) | `\b0\d{11}\b` — bắt buộc bắt đầu bằng `0` (`intent.md` §5.2) | **Hẹp hơn thực tế**: có CCCD không bắt đầu bằng 0. Phải xem lại trước khi code |

**Quy tắc thống nhất:** dù regex nào, giá trị đem đi so khớp phải là đúng 12 chữ
số. Không so khớp một phần, không so khớp 9 số cuối.

---

## 2. Số serial GCN (sổ đỏ)

- **Canonical:** 2 chữ cái in hoa + 6 chữ số, **không dấu cách**: `DD123456`.
- Khi hiển thị cho người dùng có thể chèn dấu cách (`DD 123456`); khi so khớp thì
  không.
- **Thực tế có phôi 7–8 số.** `notary_v2` nhận `[A-Z]{2}\s*\d{6,8}`. Vì vậy:
  **không được reject serial dài hơn 6 số** — chấp nhận `[A-Z]{2}` + 6–8 số, chỉ
  chuẩn hóa bằng cách bỏ hết khoảng trắng và viết hoa.
- `notaryoffice/intent.md` ghi cứng 6 số — cần nới ra khi implement.

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
- `notaryoffice` dự kiến: `thửa\s*(\d+)[\s,]+tờ\s*(\d+)`.
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
- Số công chứng **chỉ tồn tại sau khi hồ sơ hoàn tất**. Hồ sơ đang soạn không có
  khóa này → không dùng nó làm khóa chính trong `notary_v2` hay `notaryoffice`.
- Đây là khóa duy nhất **hệ thống nhà nước** cũng dùng, nên nó là khóa mạnh nhất
  cho hồ sơ lưu trữ.

---

## 6. Tên người — KHÔNG phải khóa

Trùng họ tên **không bao giờ** đủ để tự động ghép hai dữ liệu thành một hồ sơ.
Được dùng để: xếp hạng ứng viên, tìm kiếm, hiển thị. Không được dùng để: tự động
gán, tự động gộp record.

Lý do: tên Việt trùng lặp rất cao trong cùng một địa phương, và một lần gán sai
trong nghề công chứng đắt hơn hai mươi lần gán đúng.

---

## 7. Độ mạnh của khóa — thứ tự thống nhất

Từ mạnh đến yếu:

1. CCCD (12 số) — đủ mạnh để tự ghép
2. Số serial GCN — đủ mạnh để tự ghép
3. Số công chứng `xxx/yyyy` — đủ mạnh cho hồ sơ đã xong
4. `(thửa, tờ, địa phương)` — mạnh, nhưng nên có bước xác nhận
5. Số vào sổ GCN — chỉ để tăng điểm
6. Đường dẫn thư mục hồ sơ — chỉ để tăng điểm
7. Họ tên — chỉ để xếp hạng, không để ghép

Thứ tự này là nền của bảng tính điểm trong `notaryoffice`
(`intent.md` §5.2, đã được `session_summary.md` chỉnh: điểm dùng để **xếp hạng**
ứng viên, không dùng để **loại bỏ** ứng viên).
