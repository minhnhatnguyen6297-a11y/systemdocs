# Core regex trích xuất Người + Tài sản

**Trạng thái:** Active · **Cập nhật:** 06/10/2026 · **Phạm vi:** `upload_lab`
(engine, test, validator, tool test) + repo test cho nhân viên
(`regex-test-tool/`)

Trang này là bản đồ duy nhất của core regex: tool là gì, làm việc
thế nào, sửa lỗi ra sao, tinh thần nào giữ xuyên suốt, owner đã
chốt gì. Chi tiết pattern từng loại văn bản nằm ở file riêng
(`regex-thua-ke.md`, ...). [Quy tắc trường](regex-fields.md) sở hữu giá trị từng trường;
[đáp án mẫu](regex-expected-results.md) sở hữu kết quả phải kiểm;
[catalog](regex-rules.md) dẫn tới cấu trúc/loại. TASK-10.1: không chép lại luật trường.

## 1. Core là gì, không là gì

Core regex chỉ làm đúng 1 việc: **đọc văn bản Word, xuất dữ liệu
người + tài sản** (regex, tất định, không AI).

Core **không** làm: so sánh, đối chiếu, gộp hồ sơ, phán quyết pháp
lý. Việc đối chiếu đúng sai là của tầng khác (người kiểm tra +
validator). Người trong **Lời chứng không được trích** (regex-decision-46)
vì không đối chiếu được với đầu văn bản.

Core chịu trách nhiệm đúng 2 nhóm: **người** (sống, đã chết — người
chết là person_row có `ngay_chet`) và **tài sản** (đất từng thửa;
sổ tiết kiệm/bảo hiểm **tạm dừng**, chỉ gắn cờ `tai_san_chua_ho_tro`
+ R12). Số công chứng vẫn được đọc để phục vụ upload/audit nhưng
không còn là tiêu chí đủ/thiếu của core.

## 2. Hai flow (không lẫn nhau)

| | Flow người dùng | Flow phát triển (việc đang làm) |
|---|---|---|
| Ai | Nhân viên văn phòng | Agent + owner |
| Làm gì | Mở tool → import file/thư mục → xem bảng → gửi log | Đọc mẫu → viết/sửa regex → test → báo cáo |
| Ra gì | Log `.jsonl` gửi về | Code + test xanh + báo cáo vòng |
| Chuẩn đúng sai | Người đối chiếu nguồn và đề xuất trong tool | Đáp án theo spec, so từng trường; R00..R13 hỗ trợ cảnh báo (R11 đã xóa) |

## 3. Cách làm việc (vòng lặp bắt buộc)

```text
mẫu thật → agent đọc MÙ source → viết đáp án expected.json (chưa nhìn output máy)
→ chạy engine → compare diff từng trường → sửa code → test giữ hành vi
→ quét hàng loạt → báo cáo vòng
```

1. Mỗi vòng làm **1 loại văn bản** (thừa kế trước, thế chấp tiếp).
2. Đáp án viết **trước khi nhìn output máy** — hai lượt tách rõ,
   vì nhìn trước sẽ làm agent chép lỗi của máy. Không dùng số ô
   được điền hay số cảnh báo làm thước đo đúng.
3. Không commit khi test đỏ. Không đoán số liệu trôi nổi: pattern
   nào cũng phải có nhãn neo (`Sinh năm`, `Số thửa`, ...).
4. Số liệu giữ nguyên chữ trong văn bản (diện tích tuyệt đối chính
   xác, không làm tròn). Thiếu căn cứ thì để trống + gắn cờ, không
   tự bịa, không tự suy mã.
5. Trong `expected.json`: `null`/thiếu = **chưa trả lời** (compare bỏ
   qua, nhưng file toàn null = lỗi); `[]` = **đã xác nhận không có**
   — máy bóc thừa sẽ bị bắt. JSON hỏng, thiếu thư mục đáp án hoặc
   cache từ engine/luật cũ (fingerprint lệch) đều khiến compare báo
   lỗi thay vì trả "đạt".
6. Golden đổi kết quả ≠ tự động tách phiên bản rule: trước hết xác
   định đáp án cũ sai, code cũ sai, hay biểu mẫu thật sự khác.

### Lệnh của vòng (engine hiện hành `upload_lab`)

```bash
# quet hang loat + tong hop theo luat
python tools/quet_kiem_tra.py "D:\thu-muc-mau" --full --ra ket-qua.json

# tao goi doc mu: *.source.txt + *.expected.json (khong lo output)
python tools/regex_lab.py ingest --input "D:\thu-muc-mau" --cache .cache/rl
python tools/regex_lab.py review --blind --input "D:\thu-muc-mau" --cache .cache/rl --packets .cache/pk

# agent doc .source.txt, dien .expected.json, roi so
python tools/regex_lab.py compare --answers .cache/pk/<run> --cache .cache/rl

# sau khi sua code: golden hoi quy
python tools/regex_lab.py verify --input "D:\thu-muc-mau" --cache .cache/rl --golden regex_review_samples/golden
python tools/regex_lab.py approve --cluster <id>   # chi khi owner da duyet ket qua moi
```

## 4. Cách sửa lỗi

1. Công nhận lỗi khi nguồn và đáp án theo spec cho thấy máy trích sai,
   bỏ mất hoặc trích thừa trường/bản ghi. Không yêu cầu lỗi phải có cờ R.
   `upload_lab/kiem_tra_trich_xuat.py` vẫn sở hữu mã R00..R13 (R11 đã xóa)
   để cảnh báo/kiểm điều kiện; không thay việc đọc nguồn và so đáp án.
   File chưa đọc được chữ hoặc không thuộc loại phải ghi trạng thái tương ứng,
   không tính như mẫu “đã xác nhận không có người/tài sản”.
2. Sửa ở engine (`upload_lab/extract_contract.py`), thêm test giữ
   hành vi, chạy toàn bộ suite.
3. Quét lại hàng loạt bằng `upload_lab/tools/quet_kiem_tra.py`
   (cùng bộ luật, không chấm tay).
4. Ghi quyết định qua Backlog, cập nhật đúng nguồn sở hữu: luật trường ở
   [regex-fields.md](regex-fields.md), loại/vùng ở spec loại. F01/F04/F05
   giữ trạng thái chờ, không gọi approve/Golden hoặc đổi luật thay owner.

## 5. Tinh thần giữ xuyên suốt

- **Bất đối xứng lỗi (owner, 13/10/2026):** trích thiếu (sót) an toàn hơn cắt
  nhầm (mất dữ liệu im lặng) — thiếu thì validator/mã R báo được, mất im lặng
  thì không ai phát hiện. Khi lưỡng lự giữa giữ và cắt: **giữ + gắn cờ R**,
  không cắt im lặng, không gộp rồi bỏ bản giàu hơn. Rule chặt để sót được cảnh
  báo vẫn tốt hơn rule rộng để cắt mất — quyết định này nhắm trực tiếp các lỗi gộp
  im lặng F03/F05/F06 của vòng review 13/10/2026.
- R có thể không chỉ ra một người/thửa bị sót hoặc một trường bị dịch;
  phép so đáp án phải kiểm số bản ghi và dữ liệu từng trường.
- Máy đề xuất, người quyết định cuối; thiếu bằng chứng thì để
  trống, không tự điền.
- Có người nào xuất người đó; trùng/khác thì gắn cờ cho người kiểm,
  core không tự gộp, không tự loại.
- Tương thích ngược: thêm field mới không xóa field cũ; đổi hành vi
  phải có test mới + cập nhật catalog cùng thay đổi.
- PII (tên, CCCD) chỉ ở máy nội bộ và file log gửi tay; không ghi
  log rộng, không đăng mạng.

## 6. File và vị trí (để agent sau tìm đúng)

| Thứ | File |
|---|---|
| Lõi regex dùng chung (SOT, Owner 06/10/2026) | `tools/regex_workbench/engine/` + profile JSON — trích xuất + đề xuất placeholder |
| Engine thừa kế đang chạy (nguồn kiến thức trường để port) | `upload_lab/extract_contract.py` (`ENGINE_VERSION`) |
| Luật kiểm tra R00..R10, R12, R13 | `upload_lab/kiem_tra_trich_xuat.py` |
| Quét hàng loạt chuẩn | `upload_lab/tools/quet_kiem_tra.py` (có summary theo luật/loại) |
| Gói đọc mù + so đáp án + golden | `upload_lab/tools/regex_lab.py` (`ingest`/`review --blind`/`compare`/`verify`/`approve`) |
| Test giữ hành vi | `upload_lab/tests/test_upload_lab_extract_contract.py` + `test_kiem_tra_trich_xuat.py` |
| Catalog cấu trúc/loại | `_bmad-output/specs/upload_lab/regex-rules.md` |
| Quy tắc từng trường (SOT giá trị) | `_bmad-output/specs/upload_lab/regex-fields.md` |
| Đáp án mẫu theo spec; Pending hiện riêng | `_bmad-output/specs/upload_lab/regex-expected-results.md` |
| Chi tiết từng loại (SOT vùng/cấu trúc) | `_bmad-output/specs/upload_lab/regex-<loai>.md` |
| Báo cáo từng vòng (tạm, không commit) | `_bmad-output/tmp/task-<id>/` |
| Repo test cho nhân viên | `regex-test-tool/tool/` tất cả trong 1 folder (engine snapshot + `ENGINE_VERSION`, log đóng dấu bản) |

Lưu ý (Owner 06/10/2026): flow "sửa ở `upload_lab` rồi chép snapshot" chỉ áp
cho engine thừa kế hiện hành. Khi port sang `tools/regex_workbench/engine`,
cả `upload_lab` và `regex-test-tool` gọi lõi chung — không chép tay.

## 7. Quyết định của owner (nguồn sự thật cho code)

| Ngày | Quyết định |
|---|---|
| 05/10/2026 | Tài sản nhiều thửa thì tách, mỗi thửa 1 dòng |
| 05/10/2026 | Số công chứng ra khỏi tiêu chí đủ/thiếu của core (vẫn đọc cho upload/audit) |
| 05/10/2026 | Core chỉ trích xuất, không so sánh/gộp |
| 05/10/2026 | Core vẫn nằm trong `upload_lab`, ghi rõ vị trí cho agent sau |
| 06/10/2026 | Người chỉ có năm sinh thì xuất đúng `YYYY` + cờ `chi_co_nam_sinh`, không tự thêm `01/01` |
| 06/10/2026 | Chuột phải copy ngay ô đang bấm (không menu); nút riêng cuối dòng copy cả dòng |
| 06/10/2026 | Quét thư mục không cần phân loại trước; lỗi 1 file không dừng đợt; log là bản giao |
| 06/10/2026 | Diện tích tuyệt đối chính xác, không làm tròn (epsilon 1e-9 chỉ trừ sai số máy) |
| 06/10/2026 | `loai_dat` giữ chữ gốc trong văn bản, không tự suy mã khi thiếu căn cứ |
| 06/10/2026 | Lõi regex dùng chung = `tools/regex_workbench/engine`; `upload_lab/extract_contract.py` là nguồn kiến thức để port profile; lõi cũng phục vụ đề xuất placeholder và nhận text thô |
| 06/10/2026 | Serial là chuỗi nguyên văn tùy nguồn ở mọi tầng (trích xuất, Stage, DB) — bỏ bắt buộc `[A-Z]{2}\d{6,8}`; có thể trống/trùng |
| 06/10/2026 | `place_of_origin` (quê quán) giữ trong contract để đọc snapshot cũ; engine không điền |
| 06/10/2026 | Sổ tiết kiệm + bảo hiểm tạm dừng: chỉ nhận diện và gắn cờ "chưa hỗ trợ", không bóc dòng |
| TASK-10.1 | Một nguồn luật mỗi trường + đáp án theo nguồn; mã R không thay đáp án; F01/F04/F05 chờ quyết định (decision-73) |
| 06/10/2026 | Người chết = một person_row có `ngay_chet`; trích lục khai tử điền vào trường giấy tờ người, không entity riêng |
| 06/10/2026 | Không suy giới tính; thiếu căn cứ → để trống + cờ; không đếm/ngang hàng đương sự qua vùng lời chứng (theo TASK-5) |

## 8. Câu hỏi mở và cảnh báo

- [CONFIRM] `loai_tai_san` của bảo hiểm để `Tài sản khác` vì portal
  chưa có enum bảo hiểm — có cần thêm enum trên portal?
- [CONFIRM] Người đã từ chối nhưng vẫn đứng tên ở mở đầu văn bản
  (Uy/Thúy...) hiện vẫn xuất ở đương sự + cờ R11 — có cần mục
  riêng "người liên quan đã từ chối"?
- Cảnh báo: văn bản thật có lỗi đánh máy của chuyên viên (sai tên
  bố mẹ, Lời chứng khác đầu văn bản, tổng diện tích thiếu) —
  engine bóc đúng như văn bản viết và gắn cờ, người kiểm tra văn
  bản gốc, không đổ lỗi cho tool.
- Cảnh báo: file `.doc` đọc chậm (IFilter) và hay dồn bảng; code đã
  giữ TAB thành `|` nhưng văn bản quá nát vẫn cần người đọc lại.
- Chưa xong: các loại văn bản ngoài thừa kế (chuyển nhượng, tặng
  cho, thế chấp, cam kết, ủy quyền...) — làm tiếp từng loại.

## 9. Nguồn

- Spec hệ thống: [`README.md`](./README.md) (flow),
  [`../README.md`](../README.md) (nguyên tắc chung).
- Contract DB: [`../../../contracts/notary-case-drafting.md`](../../../contracts/notary-case-drafting.md)
  (shape `asset_row.land_rows`, `person_row` chấp nhận `YYYY`).
- Định danh: [`../../../contracts/entities.md`](../../../contracts/entities.md).
- Code là bằng chứng hiện trạng; spec quyết định hành vi phải có.
