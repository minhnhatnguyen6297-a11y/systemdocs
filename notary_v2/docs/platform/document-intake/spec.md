# Cloud AI OCR — luồng upload hiện hành và nguồn Zalo

Status: active
Owner: platform/document-intake
Source of truth: OCR Qwen, endpoint hiện hành và ranh giới với Zalo Intake
**Cập nhật:** quyết định owner mới nhất 2026-09-24 (MIN-89); phần Zalo là thiết kế DRAFT, chưa đổi runtime hoặc triển khai server.
**Files lien quan:** `routers/ocr_ai.py`, `frontend/templates/cases/form.html`
**API endpoint:** `POST /api/ocr/analyze`, `GET /api/ocr/config`

Có hai ngữ cảnh khác nhau:

1. **Upload OCR thủ công hiện hành:** UI gửi file ảnh đến POST /api/ocr/analyze; backend gọi Qwen, parse và trả JSON như trước. Luồng này vẫn nhận file và có thể cho xem ảnh nguồn trong giao diện hồ sơ.
2. **Zalo Intake mới:** module độc lập được phát triển trong thư mục/repo local riêng trước (đề xuất `D:\zalo-intake`), chạy Windows server sau. Module nhận/giữ ảnh, chuẩn bị ảnh khi cần byte ảnh và gọi Qwen API OCR. Gói bàn giao cho máy công chứng gồm **chữ OCR thô, trạng thái, thời gian và provenance** (dấu vết nguồn), tuyệt đối không kèm ảnh, thumbnail, base64, đường dẫn hoặc link tải ảnh. Soạn hồ sơ/Document Intake trên máy chính chạy regex, phân loại, bóc trường, ghép mặt giấy/người/tài sản và gợi ý nhóm từ raw đã Sync. Người dùng kiểm tra/xác nhận thẻ rồi đưa vào đầu vào soạn thảo; mở Zalo thật để đối chiếu ảnh. Xem [spec Zalo chính](../zalo-document-inbox/spec.md).

Vị trí thực thi đã chốt: Qwen OCR ảnh Zalo ở module độc lập; xử lý chữ OCR thành dữ liệu nghiệp vụ ở Document Intake trên máy chính. Quy tắc parser thuộc năng lực Soạn hồ sơ cho các nguồn đầu vào; không nhân bản thành parser riêng trong bot. Giai đoạn này chưa triển khai server; schema và transport của giao diện trao đổi còn là DRAFT. Lấy bù sự kiện bot chưa nhận thuộc MIN-90, giai đoạn sau. Endpoint upload hiện hành không bị đổi bởi đề xuất này.

Đích mới của nguồn Zalo giữ cả **vị trí từng dòng chữ OCR khi đường Qwen được duyệt cung cấp**, kèm kích thước khung tọa độ và dấu vết ánh xạ xoay/cắt/đổi kích thước của từng lượt; code hiện tại mới lấy chuỗi chữ. Document Intake có thể dùng vị trí đã kiểm chứng để phân biệt hai cột CCCD, nhãn cạnh giá trị ở các dòng kề nhau và các hàng/dòng GCN; đây là bằng chứng bổ sung cho regex, không là mẫu ô pixel cố định trên ảnh điện thoại hoặc tọa độ riêng từng từ. Thiếu hoặc sai vị trí thì dùng chữ và hiện phần cần người kiểm tra. Parser dùng chung vẫn nhận nguồn chỉ có chữ; luồng OCR upload thủ công hiện tại và adapter MarkItDown chưa bị buộc cung cấp tọa độ. Bot chỉ giao raw OCR/bố cục kỹ thuật, không chọn trường hay ghép hồ sơ; máy chính vẫn không nhận ảnh Zalo. [Spec Zalo](../zalo-document-inbox/spec.md) CAP-05/CAP-11/T17 và contract MIN-92 quyết định shape; MIN-102/96 quyết định cách parser dùng bằng chứng này.

---

## Muc tieu

Cloud AI OCR hiện hành đọc ảnh giấy tờ qua Qwen; parser backend đang xử lý CCCD, sổ đỏ và giấy khai tử. Zalo Intake dùng Qwen lấy chữ thô trên module, sau đó Document Intake bóc trường và ghép/nhóm từ raw đã nhập. Kết quả đã xử lý vẫn là dữ liệu chờ kiểm tra, không tự trở thành dữ liệu nghiệp vụ đã xác nhận.

Huong hien tai da chot:
- OCR AI khong con dung QR path.
- 100% request OCR duoc gui qua API cua Qwen.
- Muc tieu la lay raw OCR tu Qwen, sau do backend parse/shape ve JSON contract hien tai.
- QR neu can lam tiep se duoc phat trien thanh huong/chuc nang rieng; hien chua chot architecture va khong duoc ngam quay lai OCR AI path.
- Chuc nang OCR se tiep tuc phat trien rieng trong module AI path, khong troi sang local/research path.

Batch input co the gom:
- nhieu anh cung luc
- thu tu lon xon
- nhieu CCCD khac nhau
- anh khong phai CCCD

Kết quả của endpoint upload thủ công giữ contract JSON hiện tại. Gói Zalo không dùng response này làm định dạng bàn giao.

---

## Nguyên tắc theo luồng

### Upload OCR thủ công đang chạy

Những quy tắc dưới đây mô tả endpoint và UI hiện tại; chúng không giao quyền phân tích hoặc lưu ảnh Zalo cho máy chính:

- Route AI giu nguyen de khong vo UI:
  - `POST /api/ocr/analyze`
  - `GET /api/ocr/config`
- AI path khong dung QR server, khong client QR, khong QR rescue, khong QR-first routing.
- AI path goi Qwen OCR cho moi anh, sau do backend parse text, suy side, pair front/back, va shape response.
- Khong keo triage/fallback/heuristic nghien cuu tu local OCR vao day neu chua co scope ro.
- Muc tieu uu tien la dung nghiep vu cuoi cung, khong chi dep raw text.
- Neu gap ca sai ma khong ro rule nghiep vu, phai log ro case sai va hoi lai user truoc khi quyet dinh logic.

---

## Flow upload OCR hiện hành

```text
[AI button]
  -> frontend gui toan bo files len /api/ocr/analyze
  -> routers/ocr_ai.py doc tung file
  -> goi Qwen OCR theo tung anh
  -> backend nhan raw text / raw OCR payload
  -> backend parse text lines
  -> backend detect side
  -> backend pair front/back theo quy tac da chot
  -> backend normalize field text neu co rule an toan
  -> tra response JSON
```

---

## Flow Zalo Intake đích (MIN-89, chưa triển khai)

Module được phát triển và kiểm chứng trong repo local riêng trước; chuyển lên
Windows server là bước sau. Hai repo chỉ nối với nhau qua giao diện trao đổi
chữ OCR và metadata, không import trực tiếp code nội bộ của nhau.

```text
Zalo -> module độc lập ghi sự kiện và captured_at
     -> tải/chuẩn bị ảnh tạm trong module -> gọi Qwen API OCR
     -> công bố gói chữ OCR thô/trạng thái/nguồn, không ảnh/link ảnh
     -> máy chính tự kéo gói khi khởi động, nối lại mạng, định kỳ hoặc bấm Sync
     -> kiểm file/hash, nhập raw và ACK
     -> Document Intake regex/phân loại/bóc trường/ghép/nhóm thành thẻ ứng viên
     -> người dùng mở Zalo thật để đối chiếu, xác nhận rồi đưa vào đầu vào soạn thảo
```

Module tự xóa ảnh gốc và ảnh dẫn xuất đúng 7 ngày từ captured_at, kể cả khi máy chính chưa ACK. Gói raw chưa ACK tiếp tục được giữ để truyền lại. captured_at (lúc bot bắt tin) là thời gian chính cho từng dòng, hiển thị và gợi ý nhóm; source_sent_at và imported_at là thời gian phụ. Nút Sync chỉ lấy gói OCR raw đã có, không quét lịch sử Zalo. Lấy bù/đối chiếu tin bot chưa từng bắt là MIN-90, chưa là chức năng giai đoạn này.

Máy chính nhập gói raw OCR/trạng thái/nguồn an toàn rồi mới ACK. ACK chỉ xác nhận đã lưu raw, không có nghĩa parser chạy xong hoặc người dùng đã duyệt. Document Intake chạy regex, phân loại, ghép từ raw và có thể chạy lại khi nhận bản OCR mới; không dùng ảnh Zalo. Chi tiết endpoint, phân trang, xác thực và biên nhận thuộc contract liên repo MIN-92; [bản nháp giao tiếp](../../../../docs/product/specs/zalo-file-exchange-v1-draft.md) chỉ để soạn contract.

---

## Logging

`routers/ocr_ai.py` co logger rieng `ocr_ai`.

Log bat buoc:
- request-level:
  - `event=ocr_ai_done`
  - `model`
  - `images`
  - `total_ms`
  - `ocr_native_ms`
  - `backend_parse_ms`
  - `pair_ms`
  - `normalize_ms` (neu co layer normalize rieng)
- per AI call:
  - `event=qwen_call`
  - `filename`
  - `model`
  - `latency_ms`
  - `status=ok|error`

Neu co layer normalize text/field, log them:
- `event=ocr_normalize`
- `filename`
- `field`
- `before`
- `after`
- `rule_source=prompt|backend_rule|dictionary`

Khong log PII raw o muc qua rong trong production log; chi log mau/co che redact khi can. Với Zalo Intake, log không chứa nội dung tin nhắn, chữ OCR hoặc thông tin giấy tờ; dùng ID kỹ thuật đã che phù hợp. Quy tắc logging endpoint upload không cho phép chuyển ảnh Zalo sang máy chính.

---

## Frontend policy cho AI button (upload thủ công)

Trong `frontend/templates/cases/form.html`:
- AI button chi goi server route.
- Frontend khong duoc tu scan QR truoc khi goi server cho AI path.
- UI khong duoc gia dinh source `QR`; source cua AI path la OCR/Qwen.
- Preview `Xem anh` phai tiep tuc giu dung anh nguon tren tung person card **trong luồng upload thủ công hiện hành**. Với Zalo, Document Intake trên máy chính xử lý raw đã Sync thành thẻ/nhóm kèm provenance để kiểm tra/xác nhận; UI không có preview ảnh, thumbnail hoặc link tải ảnh. Người dùng tự mở Zalo thật khi cần đối chiếu.

---

## Response notes cho endpoint upload hiện hành

Response shape của POST /api/ocr/analyze giữ nguyên:
- `persons`
- `properties`
- `marriages`
- `raw_results`
- `errors`
- `summary`

Luu y:
- `paired_persons` duoc tinh sau khi backend pair front/back; đây là đếm record/cờ của parser cũ, không là số người hoặc số CCCD đủ hai mặt đã được xác nhận.
- Gói Zalo bàn giao raw text/OCR, trạng thái, thời gian và provenance; không có ảnh. Document Intake trên máy chính tạo dữ liệu người/tài sản đã bóc trường và ghép các mảnh liên quan, thẻ/nhóm gợi ý để người dùng kiểm tra/xác nhận rồi đưa vào đầu vào soạn thảo. Tên trường/schema cụ thể phải theo giao diện trao đổi được duyệt; không tự lấy response endpoint upload làm contract gói.
- `summary` co telemetry cho native OCR path: `ocr_native_ms`, `backend_parse_ms`, `pair_ms`.
- Neu them normalize layer, `summary` co the them `normalize_ms` va `normalized_fields`.

---

## Vietnamese normalization direction (đề xuất cho OCR thủ công)

OCR AI can xu ly 2 bai toan khac nhau:
1. **OCR raw extraction**: doc text tu anh
2. **Normalization / correction**: chuan hoa text tieng Viet thuong gap

Vi du mong muon:
- `nguyen thi A` -> rat co kha nang `Nguyễn Thị A`
- `y yen, nam dinh` -> co the chuan hoa thanh `Ý Yên, Nam Định`

### Nguyen tac cho normalize

- Khong duoc silently invent business data khi do tin cay thap.
- Phan normalize phai tach ro khoi phan OCR raw.
- Rule nao la **100% deterministic** moi duoc auto-apply khong can canh bao.
- Rule nao chi la **very likely / probabilistic** thi nen:
  - luu raw value
  - luu normalized value
  - danh dau confidence / warning
  - hoac cho user review

### Design options (non-normative)

This section records exploration, not the current runtime contract. The explicit current direction remains guidance until implemented and tested. Các phương án dưới đây bàn normalize cho luồng upload OCR thủ công; với nguồn Zalo, module chỉ gọi Qwen OCR, còn Document Intake chạy parser/ghép sau khi nhận raw theo quyết định mới nhất 24/09/2026. MarkItDown và plugin OCR mới là POC adapter trong TECH_STACK, chưa là đường production cho Zalo hoặc upload hiện hành.

#### Huong A - Prompt-based normalization trong Qwen call

Y tuong:
- Gui kem 1 file markdown/rulebook trong system prompt moi lan call AI.
- AI vua OCR vua co gang chuan hoa text theo cac rule thuong gap.

Uu diem:
- Don gian de thu nghiem nhanh.
- Co the sua rule ma khong can viet nhieu code parse backend.
- Co the xu ly nhieu pattern ngon ngu linh hoat hon dictionary cung.

Nhuoc diem:
- Kho kiem soat tinh xac dinh.
- Cung mot input co the normalize khac nhau giua cac lan/model version.
- Kho audit: khong ro AI sua theo rule nao neu prompt qua rong.
- Tang token/prompt size moi request.
- De lam mo ranh gioi giua OCR raw va field correction.

#### Huong B - Backend normalization sau khi AI tra raw text

Y tuong:
- Qwen chi OCR raw text.
- Backend parse xong moi chay mot layer normalize rieng.
- Layer nay co the la script/ruleset/dictionary/lookup.

Uu diem:
- Deterministic hon, de test hon, de audit hon.
- Co the tach `raw_value` va `normalized_value` ro rang.
- De viet regression test cho tung field.
- De gioi han auto-fix chi o cac rule an toan.

Nhuoc diem:
- Can them code va bo rule rieng.
- Nhung pattern mo ho/linh hoat se kho cover hon prompt AI.

### Huong de xuat hien tai

De xuat uu tien:
1. **Qwen chi OCR raw**
2. **Backend normalize sau**
3. Chia normalize thanh 2 lop:
   - **Deterministic rules**: auto-apply
   - **Probabilistic suggestions**: warning/review, khong silent overwrite

Vi du:
- Dia danh hanh chinh co dictionary chot ro (`Y Yen, Nam Dinh` -> `Ý Yên, Nam Định`) => co the dua vao deterministic mapping neu nguon mapping da duoc chot.
- Ho ten nguoi (`nguyen thi a`) => khong nen auto-khang-dinh 100% ngay chi bang heuristic dau cau; nen can nhac giu raw + normalized suggestion tru khi da co rule/lexicon du tin cay.

### Cau truc toi thieu de sau nay them normalize

Neu lam backend normalize, nen co 1 layer rieng, vi du:
- `services/ocr_ai_normalize.py`
- hoac `services/ocr_normalization/`

Output field co the can nhac:

```json
{
  "ho_ten_raw": "nguyen thi a",
  "ho_ten": "Nguyễn Thị A",
  "ho_ten_normalize_confidence": "suggested"
}
```

Hoac neu chua muon doi contract:
- giu `ho_ten`
- them warning/metadata noi bo trong `raw_results` / `summary`
- de UI quyet dinh co hien badge can review hay khong

---

## Decision notes 2026-07-10

- OCR AI duoc dinh huong lai thanh Qwen-only OCR path.
- Cac thong tin/chien luoc lien quan QR da khong con la huong target cua plan nay.
- Local OCR khong phai noi de tham chieu trong plan nay, tru khi can so sanh/ranh gioi pham vi o muc rat ngan.
- Bai toan normalize tieng Viet da duoc mo ra, nhung chua chot architecture cuoi cung.
- De xuat hien tai la: OCR raw bang Qwen, normalize hau xu ly o backend bang layer rieng de de test/audit.

## Decision confirmation 2026-08-11

- User confirmed the active Cloud AI OCR runtime must remove QR OCR completely.
- Do not restore server/client QR scan, QR rescue/fallback, QR-first routing, or QR/source priority to resolve shared OCR failures.
- Ghi chú OCR/Zalo cũ về QR hoặc shared runtime mismatch phải được đối chiếu với mã tại thời điểm triển khai; nó không thay thế [spec Zalo chính](../zalo-document-inbox/spec.md). Bản Zalo Intake mới chỉ đổi thiết kế dữ liệu bàn giao, chưa đổi endpoint OCR upload đang chạy.

---

## Khi debug

Route concrete OCR failures through the normal debugging and test workflow, without entering the parked local/research path unless explicitly scoped.
