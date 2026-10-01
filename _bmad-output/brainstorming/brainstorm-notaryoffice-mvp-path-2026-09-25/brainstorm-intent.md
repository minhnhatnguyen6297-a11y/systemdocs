# Brainstorm Intent — notaryoffice: đường an toàn từ tài liệu tới MVP chạy thật

**Nguồn:** phiên BMAD brainstorm ngày 2026-09-25, mode Creative Partner.
**Canonical record:** `.memlog.md` (cùng thư mục).
**Dùng cho:** input của `bmad-product-brief` / `bmad-prd` / phiên thiết kế G1 tiếp theo.

---

## 1. Sản phẩm là gì (reframe — khác spec)

`notaryoffice` **không phải hệ thống định vị hồ sơ** — là **bộ nhớ dấu vết của văn phòng**.
Ghi tối đa dấu vết số tự nhiên (60–70% bức tranh) thành **timeline theo hồ sơ**;
con người đọc timeline và tự suy luận phần còn lại. Không siết quy trình 100%.

- Người dùng trọng tâm: **cấp quản lý** (nontech). Đối thủ thật: hành vi "hỏi
  nhân viên" và sổ tay của quản lý — hệ thống thắng khi trả lời **nhanh hơn hỏi
  người** và **đúng đủ lâu để được tin**.
- Ngữ cảnh: sản phẩm **thương mại** cho nhiều VPCC quy mô nhỏ (~6 máy, nhân sự
  không được training). Văn phòng của owner là **pilot**. Owner là người legal,
  không phải dev — thực thi bằng agent.
- Triết lý xuyên suốt (đã chốt): **"đo trên thật, con người xác nhận"** —
  product và process đồng hình: capture rộng → draft → người xác nhận.

## 2. One Feature (đã chốt)

Từ dấu vết (máy tính, Zalo, hoặc nguồn bất kỳ) → **một record đủ đúng:**

> **Khách nào — Tài sản nào — Làm gì**

- Giấy tờ **thành phần** của một bộ hồ sơ (UQ, tờ khai, phụ lục…) tự bám vào
  một record — **không tràn lan thành nhiều việc**.
- Cần phân biệt văn bản-mức-hạng-mục (tạo record) vs văn bản-thành-phần
  (gắn vào record đang mở cùng khách+tài sản).
- Chế độ khó hơn `upload_lab`: đọc snapshot **dở dang**, record lớn dần theo
  phiên sửa file — không đợi tài liệu hoàn chỉnh.
- `upload_lab/extract_contract.py` + `docs/regex-rules.md` là baseline thật
  để đứng lên, không phát minh mới.

## 3. Luật gốc: thà thiếu còn hơn sai

Người quản lý suy luận **trên** dữ liệu đã ghi — một liên kết sai độc hơn
thiếu dữ liệu. Áp đồng loạt:

- **Split-bias:** không chắc cùng một việc → tách. Ngưỡng gộp cao.
- Metric bài đo: **tỷ lệ gộp nhầm ≈ 0**; tách thừa chỉ là chi phí đọc,
  chữa bằng công cụ "gộp mảnh" cho người.
- Popup ≤3/người/ngày; shadow mode trước khi hỏi ai — không đốt niềm tin sớm.

## 4. Lỗ hổng đã soi ra & cách xử lý

| Lỗ hổng | Xử lý trong phiên |
|---|---|
| Vị trí vật lý hồ sơ giấy không sensor nào thấy | **Ngoài phạm vi** — người suy luận từ dấu vết cuối (reframe ở §1) |
| "Im lặng" = hồ sơ đứng yên hay sensor mù? | Phải phân biệt hai trạng thái trong timeline, nếu không timeline nói dối |
| A4 hỏi sai biến | Biến thật = "máy nào là của ai"; văn phòng nhỏ bàn cố định → `workstation_id` là proxy người. Windows bẻ khóa = không baseline cài đặt (quyền admin, log PrintService mặc định tắt) |
| Local-first × remote-maintenance | **Đã giải (miệng, cần ghi spec):** vendor sở hữu phần mềm/logic, khách sở hữu DB, thuê server trong nước được. Cần: impact assessment ND13 + processor terms; sửa `intent.md` §2.4 và `TECH_STACK.md` §4. Vendor = chu vi bảo mật (breach đánh vào mọi khách) |
| UI phức tạp giết người dùng nontech | Reframe §1 + fork G5: trả lời trong kênh quản lý đang sống (Zalo văn phòng — tài khoản đã được phép theo B2; module Zalo MIN-89 là hạt giống sẵn) |
| "Nhét đại" vào folder khách | Là nhiễu thật của production; máy gom theo nội dung đôi khi đúng hơn cả con người xếp folder → chỗ máy ≠ folder cần người phân xử mẫu nhỏ |

## 5. Con đường an toàn (cây quyết định — đã duyệt)

```
G0  Giấy tờ (owner tự làm, song song, không cần code):
    nội quy + thông báo nhân viên + văn bản chốt thư mục nghiệp vụ
G1  ĐO OFFLINE trên kho hồ sơ cũ — không cài gì:
    đọc file → bóc thực thể → gom record (split-biased)
    pass = gộp nhầm ~0 ; fail = sửa engine, loop rẻ
G2  Spike trên máy anh (giờ-ngày): A1 đọc file khi Word giữ lock
    (fallback: đọc khi đóng file) ; A3 theo dõi ổ Z: vài ngày
G3  Sentinel SHADOW MODE 1–2 máy: chỉ quan sát + ghi evidence,
    KHÔNG popup — A3 kiểm chứng thật + dữ liệu thật + rủi ro người = 0
G4  Record-builder trên evidence sống, đối chiếu thực tế nhân viên
G5  Bề mặt trả lời — FORK: Spotlight app hay Zalo office bot
G6  Vòng xác nhận (popup ≤3/ngày) — chỉ bật khi trust đã hình thành
→   Khách #2+: đóng gói thương mại (server thuê/khách host,
    bảo trì từ xa, môi trường nhiễu)
```

Điểm mạnh của cây: **G1–G4 không cần niềm tin của ai** — rủi ro kỹ thuật
chết trước khi một nhân viên nào phải đổi hành vi. G0 (legal, owner) và
G1 (agent) chạy song song, không chờ nhau.

## 6. MoSCoW (đã duyệt)

- **Must:** G0 giấy tờ · record-builder + đo offline · A1/A3 spike ·
  Sentinel shadow (file watcher + IFilter + buffer) · Hub + record-builder
  live · một bề mặt trả lời
- **Should:** print spooler (mốc "đã in") · end-of-day review + gộp mảnh
- **Could:** popup xác nhận + calibration · Zalo OCR intake ·
  scanner/downloads watcher
- **Won't (lần này):** lớp AI/OpenClaw · đa khách thương mại ·
  theo dõi vị trí vật lý hồ sơ giấy

## 7. Phương pháp đo & thực thi (đã chốt)

- Owner + agent: quét **10 folder xấu nhất** cùng loại (có nhét đại, nhiều
  vụ, .doc cũ, scan) → kiểm tay → rút quy tắc chung → sửa → loại tiếp theo.
- Ground truth 2 mức: folder = đáp án mức khách (miễn phí); hạng mục = gán
  nhãn nhẹ; mẫu lệch máy-folder → người phân xử.
- Đếm **riêng** lỗi gộp vs lỗi tách từ ngày đầu.
- Mỗi lần sửa quy tắc → **chạy lại toàn bộ loại đã pass** (regression set —
  quy tắc là toàn cục, sửa cho loại B có thể âm thầm hỏng loại A).

## 8. Việc thuộc owner (không phải code)

1. G0: soạn nội quy + thông báo + văn bản thư mục nghiệp vụ (người legal).
2. Kiểm tra thực địa: máy→người ổn định không; Z: phát event đủ không (A3).
3. Chọn 2 chuyên viên cho shadow mode (B4).
4. Gán nhãn hạng mục cho mẫu đo offline.
5. Quyết định fork G5 sau khi có dữ liệu shadow.

## 9. Còn mở / phải ghi lại vào spec (phiên sau)

- Sửa `intent.md` §2.4 + `TECH_STACK.md` §4: server thuê trong nước, khách
  sở hữu DB, remote-maintenance là điểm egress mới được phép.
- Viết lại câu A4 (biến máy-người) trong `OPEN_DECISIONS.md`.
- ND13: hồ sơ đánh giá tác động + điều khoản processor khi host dữ liệu khách.
- G5 fork: app vs Zalo bot — quyết khi có bằng chứng shadow.
- Bảo mật chu vi vendor: threat model cho nền tảng đa khách.
