# INTENT — Hệ thống Nhận biết và Quản lý Hoạt động Hồ sơ Công chứng (Notary Work Intelligence)

**Dự án:** `notaryoffice` / Notary Work Intelligence  
**Vai trò tài liệu:** Nguồn Chân lý Duy nhất (Single Source of Truth) — Hợp nhất toàn diện Tầm nhìn, Phân tích nghiệp vụ, Kiến trúc kỹ thuật, Mô hình dữ liệu 14 bảng, Ràng buộc đã chốt & Lộ trình thực hiện.  
**Phiên bản:** 1.0 (Consolidated Unified Intent)  
**Ngày cập nhật:** 10/09/2026  
**Môi trường triển khai:** Mạng cục bộ (LAN) văn phòng công chứng (~6 máy trạm Windows của chuyên viên, 1 máy chủ trung tâm / NAS nội bộ).  
**Trạng thái dự án:** Tài liệu đặc tả kiến trúc — Chưa có code (phải tuân thủ các điều kiện tiên quyết trước khi viết code).  

---

## Mục lục
1. [Tóm tắt Điều hành & Tầm nhìn Cốt lõi](#1-tóm-tắt-điều-hành--tầm-nhìn-cốt-lõi)
2. [Ranh giới Đạo đức, Quyền riêng tư & Ràng buộc Pháp lý](#2-ranh-giới-đạo-đức-quyền-riêng-tư--ràng-buộc-pháp-lý)
3. [Kịch bản Hoạt động Nghiệp vụ Thực tế](#3-kịch-bản-hoạt-động-nghiệp-vụ-thực-tế)
4. [Các Nguồn Dấu vết & Bản ghi Dữ kiện (Evidence Records)](#4-các-nguồn-dấu-vết--bản-ghi-dữ-kiện-evidence-records)
5. [Đột phá Kỹ thuật: Windows IFilter & Khắc phục File Lock](#5-đột-phá-kỹ-thuật-windows-ifilter--khắc-phục-file-lock)
6. [Kiến trúc Kỹ thuật & Phân tích Đánh đổi](#6-kiến-trúc-kỹ-thuật--phân-tích-đánh-đổi)
7. [Mô hình Dữ liệu & 14 Bảng Database Chuẩn](#7-mô-hình-dữ-liệu--14-bảng-database-chuẩn)
8. [Cơ chế Dựng Hồ sơ Ứng viên (Draft Case) & Duyệt Trạm](#8-cơ-chế-dựng-hồ-sơ-ứng-viên-draft-case--duyệt-trạm)
9. [Giao diện Tra cứu & Thẻ Hồ sơ Cấu trúc](#9-giao-diện-tra-cứu--thẻ-hồ-sơ-cấu-trúc)
10. [Bảng Quyết định & Quản trị Rủi ro](#10-bảng-quyết-định--quản-trị-rủi-ro)
11. [Lộ trình Triển khai, Chi phí & Tiêu chí Nghiệm thu](#11-lộ-trình-triển-khai-chi-phí--tiêu-chí-nghiệm-thu)

---

## 1. Tóm tắt Điều hành & Tầm nhìn Cốt lõi

### 1.1. Vấn đề thực tế tại Văn phòng Công chứng
Văn phòng công chứng hoạt động trong môi trường phi tuyến tính, nhịp độ dồn dập và áp lực pháp lý cao:
- Mỗi chuyên viên phụ trách đồng thời **30–70 hồ sơ** ở các giai đoạn khác nhau.
- Tài liệu và tiến độ bị phân mảnh trầm trọng: file Word nằm trên máy trạm hoặc ổ chia sẻ, ảnh CCCD/sổ đỏ khách gửi rải rác trong Zalo, bản scan phiếu hẹn, hồ sơ giấy luân chuyển qua nhiều bàn làm việc và các cơ quan bên ngoài (Văn phòng ĐKĐĐ, Chi cục Thuế, đơn vị trích đo).
- Ba tình huống lặp lại hằng ngày gây tắc nghẽn:
  1. Khách hàng hoặc lãnh đạo hỏi *"Hồ sơ của tôi tới đâu rồi?"* $\rightarrow$ Phải đi hỏi vòng quanh, gián đoạn công việc của nhiều người mới chắp vá được câu trả lời.
  2. Hồ sơ bị treo hoặc chờ phản hồi từ cơ quan bên ngoài rồi bị lãng quên 2–3 tuần không ai nhận ra.
  3. Chuyên viên nghỉ phép hoặc luân chuyển công tác, công việc đang dở dang không ai nắm được ngữ cảnh bàn giao.

Đây không phải là vấn đề về kỷ luật nhân sự, mà là do **văn phòng hoàn toàn thiếu một Bộ nhớ Hoạt động Chung (Collaborative Office Memory)**.

### 1.2. Vì sao các phần mềm quản lý truyền thống luôn thất bại
Các phần mềm quản lý hồ sơ theo quy trình mẫu (Workflow/BPM) truyền thống đòi hỏi nhân viên phải chủ động đăng nhập, mở hồ sơ, chọn bước và bấm cập nhật trạng thái. Cách tiếp cận này chắc chắn thất bại trong thực tế: chuyên viên đang xử lý hàng chục việc trong ngày cao điểm sẽ không dừng lại để khai báo hành chính. Sau 1–2 tuần, dữ liệu trong phần mềm hoàn toàn lệch khỏi thực tế và hệ thống trở thành gánh nặng bị bỏ rơi.

### 1.3. Ý tưởng cốt lõi & Tầm nhìn sản phẩm
Hệ thống **Notary Work Intelligence** chọn con đường hoàn toàn ngược lại: **Không ép buộc bất kỳ ai phải nhập liệu thủ công**.

> **"Đặt một 'thư ký thầm lặng' trên mỗi máy tính. Hệ thống không can thiệp vào công việc, chỉ ghi lại những dấu vết mà công việc tự nhiên để lại — rồi tự dựng thành hồ sơ ứng viên tốt nhất và nhờ chuyên viên xác nhận một lần duy nhất."**  
> *(Triết lý: Capture facts broadly, build the best Draft Case, then ask once).*

Chuyên viên vẫn giữ nguyên thói quen làm việc: vẫn mở Word soạn thảo, in ấn, lưu vào thư mục mạng chung hoặc máy con. Hệ thống tự động quan sát các dấu vết kỹ thuật số, suy luận liên kết và phục vụ tìm kiếm tức thì.

### 1.4. Bộ nguyên tắc định hướng (Guiding Principles)
1. **Capture Reality First – Structure Second – Automate Third:** Ghi nhận sự thật khách quan trước, chuẩn hóa cấu trúc sau, tự động hóa ở bước cuối cùng.
2. **Event-First, Deterministic-First (85–90%), AI-Second (10–15%), Human-Last:**
   - 85–90% khối lượng xử lý (bóc tách text, diff, regex thực thể, hash, ghép nối phiên) được thực hiện bằng mã tất định cục bộ trong mạng LAN.
   - AI (LLM / OpenClaw) chỉ can thiệp ở 10–15% trường hợp bất định (semantic diff dị biệt, suy luận bàn giao tạm thời, cảnh báo hồ sơ treo).
   - Con người đóng vai trò chốt chặn cuối cùng (Human-in-the-loop) với chi phí thao tác tối thiểu (1 click).
3. **Bộ nhớ Tập trung là Nguồn Chân lý Duy nhất (Single Source of Truth):** Toàn bộ dữ liệu Case, Work Item, Activity Session và Timeline nằm tập trung tại máy chủ văn phòng; lớp AI không nắm giữ trạng thái nghiệp vụ độc quyền trong bộ nhớ riêng.
4. **Mục tiêu tối thượng:** Trả lời chính xác câu hỏi *"Hồ sơ bà Gái ở đâu / đang ở giai đoạn nào?"* với đầy đủ trạng thái, người chịu trách nhiệm, người đang cầm, vị trí vật lý và tài liệu mới nhất trong thời gian $< 1$ giây.

---

## 2. Ranh giới Đạo đức, Quyền riêng tư & Ràng buộc Pháp lý

Để dự án được nhân viên đồng thuận và tuân thủ tuyệt đối quy định pháp luật, các ranh giới sau là **bất khả xâm phạm**:

### 2.1. Hệ thống TUYỆT ĐỐI KHÔNG làm
- **Không quay video màn hình** (Screen Recording) dưới bất kỳ hình thức nào.
- **Không cài keylogger**, không ghi nhận phím gõ, không đọc mật khẩu hay biểu mẫu cá nhân.
- **Không theo dõi trình duyệt web cá nhân**, mạng xã hội, tin tức, mua sắm.
- **Không đọc bất kỳ file nào nằm ngoài các thư mục hồ sơ nghiệp vụ** đã được văn phòng thống nhất bằng văn bản.
- **Không dùng dữ liệu cho mục đích chấm công**, giám sát giờ làm việc hay đánh giá năng suất chuyên viên. Hệ thống chỉ quản lý **hồ sơ**, không quản lý **con người**.

### 2.2. Tuân thủ Pháp lý Bảo vệ Dữ liệu Cá nhân (Nghị định 13/2023/NĐ-CP)
- Thông tin hợp đồng chứa căn cước công dân (CCCD), tài sản, địa chỉ của khách hàng.
- **Quyết định B3 (ĐÃ CHỐT):** Hoàn thành văn bản thông báo cho toàn thể nhân viên và bổ sung nội dung giám sát hoạt động nghiệp vụ vào **Nội quy lao động của Văn phòng trước ngày triển khai thử nghiệm**, không để đến sau khi hệ thống đã vận hành.

### 2.3. Ranh giới Kết nối Zalo (Quyết định B2 đã chốt)
Zalo là kênh nhận ảnh giấy tờ phổ biến nhưng nhạy cảm về quyền riêng tư. Ranh giới kỹ thuật được xác lập cứng:
- **Chỉ sử dụng DUY NHẤT một tài khoản Zalo chung của Văn phòng** đặt listener trên máy chủ trung tâm để tiếp nhận giấy tờ khách gửi vào nhóm nghiệp vụ hoặc gửi trực tiếp tới văn phòng.
- **Tuyệt đối KHÔNG đọc tài khoản Zalo cá nhân của nhân viên.** Không cài bất kỳ listener hay extension can thiệp Zalo trên máy trạm của chuyên viên.
- Ranh giới này bảo vệ sự riêng tư của nhân viên, tuân thủ pháp luật và loại bỏ hoàn toàn nguy cơ bị Zalo khóa tài khoản cá nhân.

### 2.4. Tính Cục bộ Mạng LAN (Local-First Data Residency)
- 100% dữ liệu hồ sơ, văn bản, nhật ký hoạt động được lưu trữ và xử lý trên máy chủ LAN nội bộ của văn phòng.
- Dữ liệu nghiệp vụ **không gửi ra Internet**, ngoại trừ dịch vụ Cloud OCR (Qwen-VL-OCR qua DashScope theo danh mục kiểm soát tại `TECH_STACK.md` phục vụ đọc ảnh giấy tờ phức tạp).

---

## 3. Kịch bản Hoạt động Nghiệp vụ Thực tế

Hệ thống vận hành trơn tru xoay quanh một ngày làm việc thực tế của chuyên viên:

```
Máy chuyên viên (6 máy trạm)             Máy chủ trung tâm văn phòng (LAN)
─────────────────────────────            ──────────────────────────────────
[Chuyên viên soạn Word/in ấn]
          │
          ▼
[Sentinel đọc IFilter <15ms] ──(JSON text)──► [Lưu Snapshot, tính Diff]
                                             [Chạy Regex bóc tách Thực thể]
                                             [Ghép nối vào Draft Case]
                                                        │
[Toast Popup xác nhận trạm]  ◄──(Gợi ý ghép)────────────┘
     (1 click: [Đúng])
          │
          └─────────────────────(Xác nhận)───► [Case Verified / Sẵn sàng tra cứu]
                                                        ▲
                                                        │ (Tra cứu tức thì < 1s)
                                              [Lãnh đạo / Spotlight Search]
```

### 3.1. Một buổi sáng thực tế
- **8:40 — Chuyên viên Bình mở file Word soạn hợp đồng chuyển nhượng cho bà Nguyễn Thị Gái:**
  - Chương trình Sentinel chạy ngầm trên máy PC-02 nhận biết sự kiện lưu file.
  - Sử dụng Windows IFilter bóc tách text thuần trong 10ms, trích xuất: CCCD `036...`, Thửa 125, Tờ bản đồ 09, Số seri GCN `DD 123456`.
  - Sentinel đóng gói bản ghi JSON nhỏ (30KB) gửi về Hub máy chủ qua mạng LAN, không gửi file Word nhị phân nặng.
- **9:15 — Bình in hợp đồng ra máy in Canon LBP 2900:**
  - Sentinel bắt sự kiện Print Spooler (Event ID 307): ghi nhận file vừa in, người in, máy in, số trang và dấu mốc thời gian.
  - Tín hiệu in là bằng chứng cho thấy hợp đồng đã chuyển sang giai đoạn soát lỗi hoặc chuẩn bị ký.
- **9:20 — Máy chủ tổng hợp và dựng Hồ sơ Ứng viên (Draft Case):**
  - Hub liên kết phiên sửa file Word và lệnh in cùng chuyên viên Bình thành một `Draft Case`:
    * Khách hàng: Nguyễn Thị Gái — Chuyển nhượng Thửa 125, Tờ 09.
    * Người phụ trách: Bình.
    * Giai đoạn dự kiến: Soạn thảo xong, chờ soát lỗi / ký.
- **9:21 — Một Toast Notification nhẹ xuất hiện góc màn hình máy Bình:**
  - *"📋 Hồ sơ vừa xử lý: HDCN_NguyenThiGai.docx (Thửa 125, GCN DD123456). [✔ Đúng] [✖ Bỏ qua] [✏ Sửa]"*
  - Bình bấm **Đúng** — mất đúng 1 giây. Hồ sơ ứng viên lập tức chuyển thành Hồ sơ chính thức đã xác nhận.
- **14:30 — Khách hàng gọi điện hỏi tiến độ:**
  - Chị chủ văn phòng gõ *"Gái"* vào ô tìm kiếm Spotlight.
  - Trong $< 1$ giây, Thẻ Hồ sơ hiện ra đầy đủ: hồ sơ đang ở đâu, ai đang giữ, tài liệu mới nhất, lần in gần nhất, không cần gọi hỏi bất kỳ ai.

### 3.2. Xử lý ảnh giấy tờ Zalo và tài liệu rời rạc
- Khi khách hàng gửi ảnh chụp sổ đỏ vào Zalo chung của văn phòng mà không kèm lời nhắn:
  - Zalo Connector trên máy chủ tải ảnh, băm SHA-256 lưu trữ.
  - OCR nhận diện ra số GCN `DD 123456`.
  - Hệ thống tự động so khớp với Case đang mở của bà Gái (trùng GCN) và gắn ảnh vào danh sách tài liệu (`artifacts`) của Case, cập nhật dòng thời gian mà không cần con người can thiệp.
- Nếu OCR không tìm thấy Case trùng khớp, hệ thống vẫn lưu trữ Evidence Record và tạo một Draft Case ở trạng thái `UNCLASSIFIED` chờ chuyên viên gộp sau. **Không bao giờ loại bỏ dữ kiện chỉ vì chưa hiểu ý nghĩa.**

---

## 4. Các Nguồn Dấu vết & Bản ghi Dữ kiện (Evidence Records)

### 4.1. Khái niệm Bản ghi Dữ kiện (Evidence Record)
Evidence Record là dữ kiện khách quan ghi nhận điều máy tính thực sự quan sát được tại một thời điểm, có nguồn gốc và dấu thời gian rõ ràng, độc lập với việc nó thuộc về hồ sơ nào.

```yaml
record_type: WORD_DOCUMENT_SAVED
record_id: "rec_550e8400-e29b-41d4-a716-446655440000"
source: "SENTINEL_PC02"
timestamp: "2026-09-10T08:40:15+07:00"
workstation_id: "PC-02"
windows_user: "binh_nv"
file_path: "Z:\\HOSO\\2026\\HDCN_NguyenThiGai.docx"
content_hash: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
extracted_entities:
  cccd: ["036089012345"]
  gcn_serial: ["DD 123456"]
  land_parcel: { "thua": 125, "to": 9 }
```

### 4.2. Năm Nguồn Dấu vết Trọng tâm cho MVP
Hệ thống chuẩn hóa 5 Source Connectors chính:

1. **Word Activity Connector (Tín hiệu Nghiệp vụ Cốt lõi):**
   - Theo dõi sự kiện mở, lưu, Save As file `.docx` và `.doc`.
   - Áp dụng sliding-window debounce (3–5 phút im lặng sau chuỗi lưu liên tục) để gom thành một phiên làm việc (`activity_sessions`).
   - Tạo text snapshot và tính Text Delta (Word Diff) để phát hiện biến động thực thể (thay đổi giá trị hợp đồng, thêm người ủy quyền, sửa số thửa, phát sinh chênh lệch diện tích).
2. **File System & Storage Watcher:**
   - Hỗ trợ đồng thời **80% khối lượng nằm trên ổ mạng chia sẻ (NAS / Server LAN / ổ Z:)** và **20% khối lượng trên ổ máy con cá nhân (`D:\HoSo`, Desktop)**.
   - Bắt sự kiện tạo, sửa, đổi tên, chuyển thư mục hoặc xóa file.
   - Băm SHA-256 nội dung để nhận diện file gốc ngay cả khi nhân viên đổi tên file hoặc lưu sang thư mục khác.
3. **Print Spooler Connector (Xác thực Giai đoạn Hoàn thiện):**
   - Lắng nghe sự kiện Windows Print Spooler (Event ID 307 / Win32 API).
   - Khi phát sinh lệnh in: Kích hoạt IFilter đọc snapshot tài liệu tức thì (không cần chờ hết thời gian debounce).
   - **Ràng buộc kỹ thuật (Quyết định A2 đã chốt):** Print Spooler **KHÔNG cung cấp số bản in (copies)**. Do đó, **tuyệt đối không dùng số bản in làm điều kiện cứng** phân biệt bản nháp (`DRAFT_PRINTED`) và bản ký (`FINAL_PRINTED`).
   - **Tiêu chí thay thế để phân định mức độ hoàn thiện:**
     * *Thời điểm in so với lần sửa cuối:* In sau một chuỗi chỉnh sửa và không phát sinh chỉnh sửa mới trong khoảng thời gian nhất định $\rightarrow$ Hướng tới bản chuẩn ký.
     * *Có sửa file sau khi in hay không:* Nếu sau lệnh in tiếp tục có các phiên sửa file Word $\rightarrow$ Lệnh in trước đó là in nháp soát lỗi.
     * *Số lần in lặp lại:* Ghi nhận lịch sử in kết hợp phản hồi xác nhận nhẹ từ chuyên viên (tối đa 3 popup/ngày).
4. **Scanner & Downloads Watcher:**
   - Giám sát thư mục lưu file scan từ máy quét hoặc thư mục Downloads trình duyệt.
   - Khi có file mới: Gửi yêu cầu OCR bóc tách thông tin phiếu hẹn, văn bản trả lời thuế, trích đo địa chính.
5. **Shared Office Zalo Connector (Server-only theo B2):**
   - Connector chạy trên máy chủ lắng nghe tin nhắn văn bản, ảnh giấy tờ, file đính kèm gửi tới tài khoản Zalo chung của văn phòng.
   - Tải file về vùng lưu trữ trung tâm, băm SHA-256 và kích hoạt pipeline OCR trích xuất thực thể.

### 4.3. Các Nguồn Mở rộng Sau MVP
- Trình xem PDF (Adobe Acrobat / Foxit Reader).
- Lịch sử tải xuống của Chrome/Edge.
- File đính kèm từ Email văn phòng.
- Thao tác sao chép hồ sơ qua cổng USB.
- Tiêu đề cửa sổ ứng dụng đang kích hoạt (Foreground Window Title).

### 4.4. DRAFT MIN-54 — Ánh xạ Evidence/Draft Case vào pipeline chung

**Trạng thái: chờ chủ dự án duyệt; không phải runtime, database schema hay
contract tích hợp đã được chấp thuận.** Mục này chỉ thống nhất nghĩa dữ liệu để
khi `notaryoffice`, `notary_v2` và `upload_lab` dùng chung database sau này thì
không nhầm **bằng chứng**, **suy luận** và **xác nhận**.

Pipeline áp dụng cho mọi nguồn dấu vết:

```text
SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED
```

| Bước | Đầu vào/đầu ra dự định của notaryoffice | Trường và provenance bắt buộc | Owner ghi dự định | Không được suy ra |
| :--- | :--- | :--- | :--- | :--- |
| **SOURCE** | Sự kiện từ Word, file system, Spooler, scanner/download hoặc Zalo chung | connector/source, loại event, thời điểm nhận, file/media type và locator khả dụng | Source Connector tạo observation | Không suy ra Case, người phụ trách hay “bản ký” chỉ từ một event. |
| **RAW** | `Evidence Record` độc lập với Case | record/source id, timestamp, source hash nếu có file, raw path/message reference theo chính sách, workstation/user **chỉ khi source thực sự có**, converter/OCR call, location/ref, warning/error | Evidence ingestion của notaryoffice | Hash/OCR text/đường dẫn không tự là entity canonical hoặc Case. |
| **NORMALIZED** | Facts được chuẩn hóa, vẫn liên kết Evidence gốc | raw value + canonical value + extractor/converter version + source refs; CCCD/GCN/thửa-tờ/số công chứng theo `systemdocs/contracts/entities.md` | Enrichment/extraction của notaryoffice | Chuẩn hóa thành công không chứng minh hai Evidence cùng Case. |
| **INFERRED** | Candidate link, activity session, Draft Case và ranking | evidence ids, rule/model version, score/reasons, candidate Case/Draft Case refs, missing/ambiguous signals | Draft Case Builder của notaryoffice | Score dùng để xếp hạng, không auto-link/auto-discard hay ghi Case truth. |
| **CONFIRMED** | Xác nhận/từ chối/sửa-gộp của người có thẩm quyền; Case projection theo owner | actor, timestamp, action, candidate/evidence refs, reason nếu có và state trước/sau | Workflow/Case owner của notaryoffice | Không xóa Evidence bị từ chối hoặc Evidence `UNCLASSIFIED`; xác nhận không sửa raw evidence. |

#### RAW: Evidence là nguồn gốc, không phải kết luận

Mỗi Evidence Record phải giữ tối thiểu source/type, thời gian quan sát, định danh
record, hash/type/size của file khi có, và warning/error khi không lấy được một
trường. `file_path`, `windows_user`, workstation và location chỉ được ghi khi
connector thực sự quan sát được; không điền suy đoán để làm dữ liệu “đẹp”.

Nếu nhận OCR hay conversion, audit phải gắn với Evidence: converter name/version,
OCR provider/model, policy/version cho phép, input hash, duration, trạng thái,
lỗi và source location thực sự biết được. Payload gốc, secret/cookie và dữ liệu
nhạy cảm không được đưa vào log audit. Việc này khớp shape thử nghiệm
`ConversionEnvelope v0.experimental` ở `systemdocs/SYSTEM_ARCHITECTURE.md`
§6.5, nhưng Envelope chỉ là **input kỹ thuật tùy chọn** cho RAW; nó không sở hữu
Evidence, không tự sinh Case và không cho plugin/converter quyết định gửi cloud.

`ConversionEnvelope` có thể góp `source.sha256`, media type, content/segments,
source_ref, `ocr_calls`, warnings và errors. Evidence phải giữ reference tới
nguồn Envelope/revision đã nhận thay vì chép thành “fact đã xác nhận”. Nếu
`source_ref` là `null` hoặc không đáng tin, giữ warning; không bịa số trang Word.

#### NORMALIZED và INFERRED: giữ cả bằng chứng lẫn lý do

Facts tại NORMALIZED phải giữ `raw_value`, `normalized_value`, extractor/rule
version và `evidence_record_id`/source ref. Các định danh chuẩn chỉ để tìm và
xếp hạng ứng viên: CCCD là định danh người, serial GCN là giấy tờ/tài sản,
thửa+tờ cần địa phương, và số công chứng cần phạm vi sổ/đơn vị. Không định danh
nào trong số đó là khóa chính chung của Case hoặc cho phép tự gộp hồ sơ.

Draft Case Builder được phép tạo một hoặc nhiều candidate và ghi lý do điểm
xếp hạng; nó không được loại Evidence vì chưa tìm được candidate. Evidence chưa
ghép phải tồn tại trong Draft Case/Work Item `UNCLASSIFIED` để người dùng review
sau. Điều này giữ nguyên nguyên tắc ở §3.2 và §8.1: xếp hạng để ưu tiên review,
không phải quyết định thay người.

#### CONFIRMED, idempotency và ownership

Xác nhận của người dùng tạo một fact mới có actor/time/action; không overwrite
Evidence RAW hay normalized fact. Nếu một candidate bị từ chối, Evidence vẫn
được bảo toàn cùng lý do/timestamp từ chối để có thể review hoặc dựng candidate
khác sau này. Popup confirmation vẫn tuân thủ giới hạn cứng ba popup/người/ngày
ở §8.2.

Khi có runtime, một receipt id/event id từ connector phải được giữ cùng source
id và revision/hash để ingestion có thể idempotent: cùng receipt không sinh
Evidence lặp; nội dung/file revision mới tạo Evidence/snapshot mới, không ghi đè
bằng chứng cũ. Cách tạo receipt id cụ thể, retention và schema vật lý là thiết
kế implementation sau, chưa chốt ở đặc tả này.

`notaryoffice` là owner nghiệp vụ **dự định** của Evidence Record, Draft Case
và confirmation workflow. `notary_v2` vẫn sở hữu Case Workspace hiện hành;
`upload_lab` vẫn sở hữu upload registry/lifecycle. Consumer khác chỉ đọc qua
contract đã được duyệt; dùng chung database không cấp quyền ghi chéo. Không có
runtime owner, API, shared package hay contract production nào được tạo bởi mục
này.

#### Hiện chưa tồn tại

- Chưa có Sentinel, Hub, Evidence database/table, Draft Case Builder, connector
  runtime, API hay contract trao đổi giữa ba repo.
- A1 (đọc file khi Word giữ lock), A3 (event ổ mạng) và A4 (tài khoản Windows)
  vẫn chưa đo trên sáu máy thật. Vì vậy workflow không được giả định luôn có
  text, event đầy đủ hoặc người thao tác đáng tin; khi thiếu phải ghi warning và
  đưa review, không bù bằng suy luận.
- Chưa có `ConversionEnvelope` production, MarkItDown production, OCR plugin
  integration hay quyết định Qwen compatible; chúng không phải điều kiện để
  Evidence tồn tại.

---

## 5. Đột phá Kỹ thuật: Windows IFilter & Khắc phục File Lock

Trong kiến trúc máy trạm, giải pháp công nghệ then chốt giải quyết toàn bộ bài toán hiệu năng và đọc tài liệu là **Windows IFilter** (`query.dll` / COM Interface):

```
                        ┌─────────────────────────────────────────────────────────┐
                        │              Workstation (Sentinel C# .NET 8)           │
                        │                                                         │
[WINWORD.EXE] ────────► │ [File Word đang mở] ◄─── (FILE_SHARE_READ|WRITE)        │
(Đang khóa file)        │                                │                        │
                        │                       [Windows IFilter]                 │
                        │                       (query.dll native)                │
                        │                                │ (<15ms)                │
                        │                       [Plain Text Snapshot]             │
                        │                       (Chỉ 20 - 50 KB)                  │
                        │                                │                        │
                        │                       [Local SQLite Buffer]             │
                        │                                │                        │
                        └────────────────────────────────┼────────────────────────┘
                                                         │ (JSON Payload qua LAN)
                                                         ▼
                                       [Central Activity Hub (FastAPI)]
```

### 5.1. Bốn Lợi thế Vượt trội của IFilter
1. **Tốc độ Native C++ siêu tốc (5 – 15 mili-giây):** Bóc tách toàn bộ text thuần của hợp đồng dài 20 trang gần như tức thì mà không tiêu tốn CPU hay RAM máy trạm.
2. **Khắc phục triệt để lỗi Khóa file (File Lock Resilience):** Khi Word (`WINWORD.EXE`) đang mở file, Windows khóa chặt không cho các thư viện thông thường mở đọc. IFilter truy cập ở tầng `FILE_SHARE_READ | FILE_SHARE_WRITE`, đọc snapshot text trực tiếp ngay cả khi chuyên viên đang gõ văn bản.
3. **Hỗ trợ đồng thời `.doc` cũ, `.docx` mới và `.pdf`:** Văn phòng công chứng tồn tại rất nhiều biểu mẫu `.doc` (Word 97–2003 nhị phân) lưu trữ từ nhiều năm trước. IFilter xử lý mượt mà cả `.doc`, `.docx` (OpenXML) lẫn `.pdf` mà không cần cài Word Automation hay bộ chuyển đổi cồng kềnh.
4. **Siêu tiết kiệm băng thông mạng LAN:** Sentinel chỉ trích xuất text thuần (20–50 KB) gửi về Server dưới dạng JSON. Không cần truyền tải các file Word nhị phân nặng hàng chục MB (vốn chứa nhiều ảnh chụp phôi bằng cấp, sổ đỏ chèn bên trong).

---

## 6. Kiến trúc Kỹ thuật & Phân tích Đánh đổi

### 6.1. Pipeline Xử lý Dữ liệu Tổng thể
Luồng dữ liệu được thiết kế một chiều, đảm bảo tính phân tách trách nhiệm rõ ràng:

```
[Nguồn: Word / File / Print / Scan / Zalo]
                   │
                   ▼
         [Source Connectors]
                   │
                   ▼
          [Evidence Records]
                   │
                   ▼
      [Enrichment & Extraction]
(IFilter Text + Word Diff + Deterministic Regex + OCR)
                   │
                   ▼
        [Work Session Grouper]
(Gom sự kiện theo User, Thời gian, Thư mục, File Hash)
                   │
                   ▼
         [Draft Case Builder]
   (Tự động dựng hồ sơ ứng viên & xếp hạng)
                   │
                   ▼
         [Confirmation Layer]
 (Popup máy trạm <= 3 lần/ngày + Review cuối ngày)
                   │
                   ▼
        [Case Search Projection]
(Chỉ mục tìm kiếm đa tiêu chí: Spotlight < 1s)
```

### 6.2. Phương án Được Chọn: Hybrid Pipeline
Hệ thống áp dụng mô hình phân tán thông minh:
- **Tại máy trạm (Activity Sentinel C# .NET 8 siêu mỏng):**
  - Chạy dưới dạng Windows Service hoặc Background Tray App.
  - Mức độ chiếm dụng tài nguyên cực thấp: **< 30MB RAM, < 0.5% CPU**.
  - Bắt file event (debounce 3–5 phút) trên cả ổ mạng dùng chung (80%) và ổ local máy con (20%).
  - Bắt sự kiện in (Event ID 307) $\rightarrow$ Kích hoạt IFilter đọc text tức thì.
  - Tích hợp hàng đợi **SQLite local (FIFO buffer)**: Khi mạng LAN chập chờn hoặc mất kết nối máy chủ, toàn bộ event được lưu cục bộ và tự động flush đồng bộ về Hub khi có mạng trở lại.
- **Tại máy chủ văn phòng (Central Activity Hub - Python FastAPI + SQLite WAL):**
  - Đóng vai trò Single Source of Truth của toàn văn phòng.
  - Tiếp nhận JSON text, lưu snapshot phiên bản (`document_snapshots`).
  - Tính Text Delta so với phiên trước (`document_deltas`).
  - Chạy bộ lọc Regex tất định bóc tách CCCD, GCN, Thửa, Tờ, diện tích, giá trị.
  - Nhận diện sự kiện in ấn để cập nhật giai đoạn hồ sơ.
  - Dựng Draft Case và điều phối thông báo xác nhận tới đúng máy trạm của chuyên viên vừa thao tác.

### 6.3. Các Lựa chọn Kiến trúc ĐÃ LOẠI BỎ (Discarded Alternatives)

| Phương án bị loại | Mô tả | Lý do loại bỏ (Đã chốt — Không đề xuất lại) |
| :--- | :--- | :--- |
| **❌ Server-Centric FileWatcher** | Đặt FileWatcher tại máy chủ tự động quét ổ NAS/SMB chung. | Trễ giao thức SMB, phát sinh sự kiện ảo, không định danh được Windows User nào vừa lưu file, và bỏ sót hoàn toàn 20% công việc trên máy con. |
| **❌ Full Edge-Processing** | Máy trạm tự diff, tự chạy toàn bộ Regex, tự tính điểm. | Biến máy trạm thành client dày gây lag giật máy chuyên viên; khó bảo trì khi phải cập nhật rule/regex trên toàn bộ 6 máy trạm thay vì 1 nơi trên server. |
| **❌ Auto-link Cứng Ma trận Điểm** | Điểm $\ge 90$ tự động ghép cứng vào Case, không cần hỏi. | Rủi ro pháp lý công chứng rất cao (trùng họ tên, ủy quyền nhiều việc, cùng thửa đất khác xã). Bị loại để chuyển sang **xếp hạng ứng viên + hỏi người 1 lần**. |
| **❌ Đọc API/DB phần mềm cũ** | Kết nối trực tiếp vào phần mềm quản lý công chứng đang dùng. | **Quyết định B1 đã chốt:** Phần mềm cũ không có API/DB mở để kết nối. Nguồn thật là file Word và dấu vết máy trạm. |
| **❌ Đọc Zalo cá nhân nhân viên** | Cài extension/tool đọc Zalo trên máy trạm của nhân viên. | **Quyết định B2 đã chốt:** Vi phạm quyền riêng tư và tiềm ẩn rủi ro khóa tài khoản nhân viên. Chỉ dùng tài khoản chung trên server. |
| **❌ Dùng số bản in từ Spooler** | Đọc số bản copies từ Print Spooler để kết luận bản ký. | **Quyết định A2 đã chốt:** Windows Spooler không báo số bản in. Không thiết kế bất kỳ tính năng nào phụ thuộc vào số này. |

### 6.4. Vai trò của Lớp OpenClaw / AI Engine (10 – 15% Bất định)
OpenClaw hoạt động như một Trực ban Ngữ nghĩa (Semantic Observer):
- **Tuyệt đối KHÔNG làm:** Không lưu trạng thái nghiệp vụ trong bộ nhớ riêng của model; không can thiệp vào các event đã match tất định; không làm chậm luồng xử lý chính.
- **Nhiệm vụ chính:**
  * **Semantic Diff:** Phân tích các thay đổi dị biệt mà Regex không bắt được (ví dụ: hợp đồng phát sinh điều khoản *"diện tích thực tế tăng 15m2 do khai hoang thêm"* $\rightarrow$ Đề xuất sinh Work Item *"Đo đạc chỉnh lý"*).
  * **Handoff Inference:** Suy luận bàn giao tạm thời giữa các chuyên viên (A ngừng sửa file, B mở file và in $\rightarrow$ Gợi ý bàn giao A $\rightarrow$ B để người dùng xác nhận).
  * **Ambient Heartbeat:** Quét định kỳ 30–60 phút phát hiện các hồ sơ chết lâm sàng (**Stale Cases > 7 ngày** không có hoạt động) để gửi thông báo nhắc nhở lãnh đạo.
  * **Natural Language Query:** Chuyển đổi câu hỏi khẩu ngữ tự nhiên của lãnh đạo (*"Hồ sơ chuyển nhượng nhà bà Gái hôm qua đã in chưa?"*) thành truy vấn dữ liệu chính xác.

---

## 7. Mô hình Dữ liệu & 14 Bảng Database Chuẩn

### 7.1. Mô hình Khái niệm 5 Lớp (Core Data Model)
Mọi hoạt động trong văn phòng công chứng được quy chiếu về mô hình quan hệ 5 tầng:

```
[ENTITY] (CCCD, Số GCN, Thửa/Tờ, Khách hàng)
   │
   ▼
 [CASE] (Hồ sơ tổng thể: #3812 - Nguyễn Thị Gái)
   │
   ├─► [CASE OWNER] (Chuyên viên chịu trách nhiệm chính)
   ├─► [CURRENT HANDLER] (Người đang thực thi thao tác hiện tại)
   ├─► [PHYSICAL LOCATION] (Bàn A, Bàn ký CCV, Đơn vị đo đạc, Thuế...)
   │
   └─► [WORK ITEM] (Đầu việc logic: Chuyển nhượng, Đo đạc, UNCLASSIFIED)
         │
         └─► [ACTIVITY SESSION] (Chuỗi phiên làm việc, in ấn, nhận tài liệu)
               │
               └─► [ARTIFACT] (File .docx, .doc, scan, ảnh Zalo, phiếu nộp)
```

### 7.2. Quy chuẩn Định danh Thực thể Công chứng Việt Nam (`contracts/entities.md`)
Để đảm bảo tính tương thích khi tích hợp toàn hệ thống (theo `systemdocs`), các trường dữ liệu bắt buộc tuân thủ:
- **Căn cước công dân (CCCD):** Chuỗi 12 chữ số (`\b\d{12}\b`). Nhận diện cả trường hợp số đầu khác 0 do lỗi OCR/nhập liệu.
- **Số Seri Giấy chứng nhận (Sổ đỏ/Sổ hồng):** 2 chữ cái in hoa + 6–8 chữ số (`[A-Z]{2}\s*\d{6,8}`) (ví dụ: `DD 123456`, `DA 998812`).
- **Thửa đất & Tờ bản đồ:** Cụm từ chuẩn hóa `so_thua_dat` và `so_to_ban_do`.
- **Tên trường chuẩn hóa:** Toàn bộ bảng cơ sở dữ liệu phải dùng chung định dạng: `so_serial`, `so_vao_so`, `so_thua_dat`, `so_to_ban_do`, `dia_chi`, `ngay_cap`, `co_quan_cap`, `dien_tich`. Ngày tháng lưu trữ theo chuẩn **ISO-8601** (`YYYY-MM-DDTHH:MM:SSZ`).

### 7.3. Cấu trúc 14 Bảng Cơ sở Dữ liệu Chi tiết

```
 ┌──────────────┐       ┌──────────────┐       ┌────────────────────┐
 │   offices    │◄──────┤    users     │◄──────┤  sentinel_clients  │
 └──────────────┘       └──────┬───────┘       └────────────────────┘
                               │
                               ▼
 ┌──────────────┐       ┌──────────────┐       ┌────────────────────┐
 │   entities   │◄─────►│    cases     │──────►│     work_items     │
 └──────────────┘       └──────┬───────┘       └────────────────────┘
                               │
                               ▼
                        ┌──────────────┐       ┌────────────────────┐
                        │  artifacts   │◄──────┤ activity_sessions  │
                        └──────┬───────┘       └────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
 ┌────────────────────┐ ┌──────────────┐ ┌────────────────────┐
 │ document_snapshots │ │  print_jobs  │ │case_timeline_events│
 └─────────┬──────────┘ └──────────────┘ └────────────────────┘
           ▼                   ▲
 ┌────────────────────┐        │
 │  document_deltas   │        │
 └────────────────────┘        │
                               ▼
                    ┌─────────────────────┐
                    │  calibration_logs   │
                    └─────────────────────┘
```

1. **`offices`**: Danh bạ văn phòng công chứng / chi nhánh.
2. **`users`**: Danh sách chuyên viên, công chứng viên, quản trị viên.
3. **`sentinel_clients`**: Danh bạ máy trạm kết nối trong mạng LAN (`machine_name`, `ip_address`, `mac_address`, `installed_version`, `status`).
4. **`entities`**: Sổ cái thực thể chuẩn hóa (`entity_type`: CCCD, GCN_SERIAL, LAND_PARCEL, PHONE; `normalized_value`, `raw_value`).
5. **`cases`**: Thực thể Hồ sơ cốt lõi:
   - `case_number`, `title`, `status` (`DRAFT`, `IN_PROGRESS`, `READY_FOR_SIGNING`, `SIGNED`, `WAITING_EXTERNAL`, `COMPLETED`, `ARCHIVED`).
   - `owner_user_id` (Chuyên viên phụ trách chính).
   - `current_handler_id` (Người đang thao tác gần nhất).
   - `physical_location` (Vị trí vật lý của hồ sơ giấy).
   - `blocker` (Vướng mắc pháp lý/hành chính nếu có).
   - `next_action` (Hành động dự kiến tiếp theo).
6. **`case_entities`**: Bảng liên kết M:N giữa Hồ sơ và Thực thể kèm theo vai trò (`role`: BÊN_CHUYỂN_NHƯỢNG, BÊN_NHẬN, TÀI_SẢN_CHÍNH...).
7. **`work_items`**: Các đầu việc cụ thể trong hồ sơ (`work_type`: CHUYEN_NHUONG, THE_CHAP, THUA_KE, DO_DAC, THUE, `UNCLASSIFIED`; `status`).
8. **`artifacts`**: Quản lý tài liệu kỹ thuật số (`file_path`, `storage_type`: SHARED_NAS / LOCAL_DISK, `file_hash_sha256`, `mime_type`, `file_size`).
9. **`activity_sessions`**: Phiên làm việc gom nhóm do Sentinel ghi nhận (`user_id`, `workstation_id`, `start_time`, `end_time`, `save_count`).
10. **`document_snapshots`**: Toàn bộ bản text thuần bóc tách từ IFilter qua từng phiên làm việc (v1, v2, v3...) phục vụ đối soát.
11. **`document_deltas`**: Chi tiết diff các đoạn thêm / sửa / xóa văn bản giữa các snapshot liên tiếp.
12. **`print_jobs`**: Nhật ký in ấn (`workstation_id`, `user_id`, `printer_name`, `doc_name`, `total_pages`, `printed_at`; không có số copies từ spooler).
13. **`calibration_logs`**: Sổ cái hiệu chuẩn xác suất ghi nhận phản hồi popup của chuyên viên (`calculated_score`, `detected_signals_json`, `user_action`: CONFIRMED / REJECTED / TIMEOUT, `response_time_ms`).
14. **`case_timeline_events`**: Dòng thời gian sự kiện bất biến (Audit Trail / Event Sourcing) lưu vết toàn bộ lịch sử biến động của hồ sơ.

---

## 8. Cơ chế Dựng Hồ sơ Ứng viên (Draft Case) & Duyệt Trạm

### 8.1. Chuyển đổi Tư duy: Từ Lọc Cứng sang Xếp hạng Ứng viên (Draft Case Ranking)
Kinh nghiệm thực tế cho thấy việc áp dụng ma trận điểm cứng để tự động ghép hoặc loại bỏ hồ sơ sẽ gây thất thoát dữ liệu nghiêm trọng. Hệ thống áp dụng quy trình 2 bước:
1. **Dựng Draft Case:** Mọi Evidence Record hợp lệ đều được gom thành phiên và dựng thành một hoặc nhiều `Draft Case` tốt nhất có thể.
2. **Xếp hạng Tin cậy (Ranking):** Điểm số chỉ dùng để **sắp xếp thứ tự ưu tiên** hiển thị cho con người lựa chọn, không dùng để loại bỏ.

**Tiêu chí tính điểm xếp hạng ứng viên:**
- Trùng CCCD hoặc Số Seri GCN: **+100 điểm** (Ưu tiên số 1).
- Trùng Thửa đất + Tờ bản đồ: **+80 điểm**.
- Cùng cuộc trò chuyện Zalo / Thư mục hồ sơ: **+30 điểm**.
- Cùng chuyên viên thao tác: **+20 điểm**.
- Hoạt động gần nhau về mặt thời gian: **+15 điểm**.
- Case đang chạy (`IN_PROGRESS`) được ưu tiên hơn Case đã lưu trữ (`COMPLETED`).

### 8.2. Popup Duyệt Trạm (Workstation Confirmation Toast)
Khi một Draft Case được dựng sau phiên soạn thảo Word hoặc lệnh in:
- Một Toast Notification nhỏ gọn xuất hiện ở góc dưới màn hình của **chính chuyên viên vừa thao tác**:

```text
┌─────────────────────────────────────────────────────────────┐
│ 📋 PHÁT HIỆN HỒ SƠ VỪA SOẠN THẢO                           │
│ File: HDCN_NguyenThiGai.docx                                │
│ Khách: Nguyễn Thị Gái | Thửa 125, Tờ 09 | GCN: DD 123456    │
│ Giai đoạn dự kiến: Đã in bản chuẩn / Sẵn sàng ký            │
│                                                             │
│  [ ✔ Đúng là hồ sơ tôi làm ]   [ ✖ Bỏ qua ]   [ ✏ Sửa/Gộp ] │
└─────────────────────────────────────────────────────────────┘
```

- **Giới hạn cứng chống phản xạ bấm vô thức:**
  * **Rủi ro lớn nhất:** Nếu chuyên viên nhận 20 popup/ngày, họ sẽ bấm "Đúng" theo phản xạ mà không đọc nội dung, làm sai lệch toàn bộ dữ liệu.
  * **Quy tắc cứng:** Giới hạn tối đa **3 popup xác nhận / người / ngày**.
  * Các hồ sơ còn lại trong ngày được tự động gom vào **Màn hình Tổng kết Cuối ngày (End-of-day Review)** để chuyên viên duyệt một lần trong 2 phút trước khi ra về.
  * **Đo thời gian phản hồi (`response_time_ms`):** Hệ thống tự động phát hiện nếu chuyên viên bấm nút dưới **1.5 giây** liên tục để cảnh báo dấu hiệu bấm không đọc và hạ trọng số tin cậy.

### 8.3. Sổ cái Hiệu chuẩn Xác suất (`calibration_logs`) & Tính năng Export CSV
Mọi tương tác với popup được lưu trữ đầy đủ trong bảng `calibration_logs`. Quản trị viên có thể xuất file CSV bất kỳ lúc nào để:
- Quan sát phân bố xác suất thực tế tại văn phòng (ví dụ: hồ sơ có điểm xếp hạng 90–100 đạt tỷ lệ xác nhận đúng 99.2%, dải 70–89 đạt 86%).
- Tinh chỉnh các tham số trọng số toán học dựa trên dữ liệu thực chứng thay vì giả định cảm tính.

---

## 9. Giao diện Tra cứu & Thẻ Hồ sơ Cấu trúc

### 9.1. Giao diện Tra cứu Trọng tâm (Search-First Omnibox)
Giao diện chính của hệ thống là thanh tìm kiếm thông minh dạng Spotlight/Omnibox. Người dùng có thể tìm kiếm bằng bất kỳ từ khóa nào: Tên khách hàng, Số CCCD, Số sổ đỏ, Số thửa đất hoặc tên chuyên viên.

Kết quả trả về trong **$< 1$ giây**, hiển thị danh sách các Case ứng viên phù hợp nhất kèm nhãn phân định rõ ràng giữa **Dữ liệu đã xác nhận** và **Dữ liệu suy đoán (Draft)**:

```text
1. Nguyễn Thị Gái – Chuyển nhượng Thửa 125, Tờ 09
   Giai đoạn: Sẵn sàng ký (Đã in bản chuẩn)
   Hoạt động cuối: In tài liệu lúc 09:15 bởi Bình
   Trạng thái dữ liệu: [ĐÃ XÁC NHẬN BỞI CHUYÊN VIÊN]

2. Nguyễn Thị Gái – Ủy quyền
   Giai đoạn: Đang soạn thảo
   Hoạt động cuối: Sửa file Word 3 ngày trước
   Trạng thái dữ liệu: [DỰ ĐOÁN TỪ HỆ THỐNG]
```

### 9.2. Thẻ Hồ sơ Cấu trúc Chi tiết (Structured Answer Card)
Khi bấm chọn một hồ sơ, hệ thống hiển thị Thẻ Hồ sơ duy nhất giải quyết triệt để câu hỏi *"Hồ sơ đang ở đâu?"*:

```yaml
HỒ SƠ: CASE #3812 - NGUYỄN THỊ GÁI
Tài sản: Thửa đất 125, Tờ bản đồ 09 | GCN số: DD 123456
----------------------------------------------------------------------
Trạng thái:            READY_FOR_SIGNING (Đã in bản chuẩn - Sẵn sàng ký)
Độ tin cậy liên kết:    100/100 (Bình đã xác nhận lúc 09:21)
Chủ hồ sơ (Owner):     Nguyễn Văn Bình (Chuyên viên phụ trách chính)
Người đang xử lý:      Nguyễn Văn Bình (Vừa hoàn thành lệnh in)
Vị trí thực tế:        Bàn ký / Chờ Công chứng viên kiểm tra và ký
Lần in gần nhất:       09:15:20 - Máy in Canon LBP 2900 (Đã in 4 trang)
Biến động gần nhất:    Bổ sung diện tích chênh lệch + bên mua (Diff v3)
Vấn đề chặn (Blocker): Không có
Việc tiếp theo:        Ký công chứng -> Bàn giao khách nộp thuế & ĐKĐĐ
Tài liệu liên kết:
  - HDCN_NguyenThiGai.docx (Z:\HOSO\2026\)
  - zalo-attachment-gcn-DD123456.jpg (Zalo Văn phòng)
```

---

## 10. Bảng Quyết định & Quản trị Rủi ro

### 10.1. Danh mục Quyết định Tiên quyết (Đã chốt & Cần kiểm chứng)

| Mã | Nội dung câu hỏi | Trạng thái | Hướng xử lý / Hệ quả kỹ thuật |
| :--- | :--- | :--- | :--- |
| **A1** | Đọc được tài liệu khi Word đang mở không? | 🔴 Cần đo máy thật | Đã có giải pháp đột phá Windows IFilter (`query.dll`); cần kiểm chứng thực tế tại văn phòng. |
| **A2** | Print Spooler có báo số bản in (copies) không? | 🟢 **ĐÃ CHỐT: KHÔNG** | Spooler không báo số bản in. Cấm dùng số bản in làm điều kiện phân loại; dùng thời điểm in, việc sửa sau in và lịch sử in. |
| **A3** | Ổ mạng chung (Z:) có báo sự kiện đầy đủ không? | 🔴 Cần đo máy thật | Kiểm tra xem giao thức SMB có bỏ sót event; nếu có sẽ bổ sung job quét đối chiếu định kỳ. |
| **A4** | 6 máy trạm dùng tài khoản Windows riêng hay chung? | 🔴 Cần khảo sát | Nếu dùng tài khoản riêng: theo dõi bàn giao mượt mà. Nếu dùng chung: phải loại bỏ tính năng theo dõi người làm cụ thể. |
| **B1** | Phần mềm cũ có API/DB để trích xuất không? | 🟢 **ĐÃ CHỐT: KHÔNG** | Không có API. Đóng vĩnh viễn hướng đọc API cũ. Nguồn thật là file Word và dấu vết máy con. |
| **B2** | Phạm vi kết nối Zalo | 🟢 **ĐÃ CHỐT** | Chỉ dùng 1 tài khoản Zalo chung văn phòng trên server. Cấm đọc Zalo cá nhân nhân viên. |
| **B3** | Thông báo nhân viên & Nội quy lao động | 🟢 **ĐÃ CHỐT** | Bắt buộc hoàn thành văn bản thông báo và bổ sung nội quy trước khi triển khai thử nghiệm. |
| **B4** | Chọn chuyên viên tham gia thử nghiệm | 🟢 **ĐÃ CHỐT** | Chủ dự án chọn 2 chuyên viên có tinh thần hợp tác tốt nhất. |

### 10.2. Ma trận Quản trị Rủi ro Kỹ thuật & Vận hành

| Rủi ro tiềm ẩn | Mức độ | Biện pháp giảm thiểu đã thiết kế |
| :--- | :---: | :--- |
| **Nhân viên bấm "Đúng" theo phản xạ** | **Cao** | Giới hạn cứng tối đa 3 popup/ngày; phần còn lại xem xét cuối ngày; đo thời gian phản hồi (<1.5s là dấu hiệu bấm vô thức). |
| **Mất kết nối mạng LAN cục bộ** | Trung bình | Sentinel tích hợp SQLite FIFO local cache, tự động lưu trữ và flush về máy chủ khi có mạng trở lại. |
| **Nhân viên lưu file ngoài thư mục quy chuẩn** | Trung bình | Cấu hình Sentinel giám sát thêm thư mục Desktop và Downloads của user; phát hiện văn bản công chứng nằm sai chỗ để cảnh báo nhẹ. |
| **Suy luận bàn giao sai (False Handoff)** | Thấp | Luôn gán nhãn trạng thái dự đoán (`Provisional State: B đang xử lý [Xác nhận]`), không tự ý đổi cứng quyền sở hữu hồ sơ. |
| **Chi phí gọi AI tăng cao** | Thấp | Nguyên tắc Deterministic-First chặn 85–90% khối lượng; gom cụm Heartbeat 30 phút; ước tính chi phí LLM < 1 triệu VNĐ/tháng. |

---

## 11. Lộ trình Triển khai, Chi phí & Tiêu chí Nghiệm thu

### 11.1. Lộ trình Triển khai 4 Giai đoạn

```
[Giai đoạn 0: Kiểm chứng Thực địa] (1 - 2 tuần)
- Đo A1, A3, A4 trên 6 máy thật
- Đo độ chính xác bóc tách thực thể trên 50 hợp đồng thật
                │
                ▼
[Giai đoạn 1: Bản dùng thử MVP] (6 - 10 tuần)
- 2 máy trạm chuyên viên + 1 Hub trung tâm LAN
- 15 - 20 hồ sơ đang chạy thực tế
- Word Diff + IFilter + Print Spooler + Zalo Server + Popup duyệt trạm + Spotlight Search
                │
                ▼
[Giai đoạn 2: Mở rộng Toàn diện] (4 - 6 tuần tiếp theo)
- Mở rộng toàn bộ 6 máy trạm
- Bổ sung Scanner/Downloads watcher, cảnh báo Stale Cases > 7 ngày
                │
                ▼
[Giai đoạn 3: AI Nâng cao (Tùy chọn)]
- Phân tích Semantic Diff phức tạp, hỏi đáp ngôn ngữ tự nhiên, suy luận bàn giao tự động
```

### 11.2. Dự toán Hạ tầng & Chi phí
- **Hạ tầng phần cứng:** Tận dụng 1 máy tính hiện có hoặc thiết bị NAS trong văn phòng làm máy chủ LAN. Không cần đầu tư máy chủ chuyên dụng, không phát sinh chi phí thuê Cloud Server.
- **Chi phí phát triển:** Chi phí chính là công sức phát triển kỹ thuật trong 2–3 tháng đầu.
- **Chi phí vận hành AI:** Nếu kích hoạt tầng AI ở Giai đoạn 3, chi phí API token (OpenClaw / LLM) ước tính dưới **1.000.000 VNĐ / tháng** cho toàn bộ văn phòng.

### 11.3. Bốn Tiêu chí Nghiệm thu Thành công Thực tế
Hệ thống không đánh giá bằng sự phức tạp của công nghệ, mà bằng 4 con số đo lường hiệu quả thực tế:

1. **Tốc độ trả lời câu hỏi "Hồ sơ đang ở đâu":** Trả lời chính xác trong **$< 1$ giây** (hoặc $< 10$ giây cho truy vấn tìm kiếm sâu) mà không cần gọi điện hay hỏi chuyên viên, đạt tỷ lệ ít nhất **8/10 lần hỏi**.
2. **Độ chính xác bóc tách thực thể:** Tỷ lệ đọc đúng CCCD, Số GCN, Thửa/Tờ đất từ tài liệu hợp đồng đạt **$\ge 80\%$**.
3. **Tỷ lệ ghép sai hồ sơ gần bằng 0:** Hệ thống luôn duy trì trạng thái hồ sơ ứng viên (Draft Case) cho tới khi có xác nhận của con người, triệt tiêu rủi ro nhầm lẫn pháp lý.
4. **Không làm phiền nhân viên:** Chuyên viên chỉ tốn tối đa **1 cái bấm chuột, dưới 1 phút mỗi ngày** (tối đa 3 popup/ngày), không cảm thấy bị giao thêm việc hành chính.
