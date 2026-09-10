# Kiến trúc hệ thống

## 0. Đọc mục này trước

Đích đến của hệ thống: **một hệ thống thống nhất, dùng chung một database.** Ba
repo là ba công cụ xử lý dữ liệu cho ba mục đích khác nhau trong hệ thống đó.

**Giai đoạn hiện tại: ba công cụ vẫn chạy độc lập, và đó là đúng.** Việc bây giờ
là làm tốt từng phần, đồng thời **không để chúng phân kỳ** ở ba chỗ: khóa định
danh ([`contracts/entities.md`](./contracts/entities.md)), lựa chọn công nghệ
([`TECH_STACK.md`](./TECH_STACK.md)), và schema/tên trường (`TECH_STACK.md` mục 3).

Vì vậy đọc mục 1–3 dưới đây là **hiện trạng**, không phải trạng thái cuối cùng.

## 1. Hiện trạng: ba công cụ chạy độc lập

Đây là sơ đồ **thực tế hôm nay**, không phải mong muốn. Chưa có API, chưa có DB
dùng chung, chưa có luồng dữ liệu tự động nào giữa ba công cụ.

```mermaid
flowchart TB
    subgraph NV2["notary_v2 — Soạn thảo hồ sơ mới"]
        direction TB
        NV2IN["Ảnh giấy tờ / Zalo cá nhân"]
        NV2OCR["Cloud AI OCR + parser regex<br/>(CCCD, sổ đỏ, giấy khai tử)"]
        NV2CASE["Case Workspace<br/>Stage / Pool / Diagram<br/>engine thừa kế"]
        NV2OUT["Word hợp đồng / văn bản<br/>(word_engine + template)"]
        NV2IN --> NV2OCR --> NV2CASE --> NV2OUT
    end

    subgraph UL["upload_lab — Số hóa hồ sơ giấy"]
        direction TB
        ULIN["Kho Word cũ .doc/.docx<br/>trên ổ đĩa"]
        ULEX["python-docx + Windows IFilter<br/>→ trích trường web form"]
        ULDB["output/*.json<br/>registry.sqlite3"]
        ULAUD["Đối chiếu sổ Excel<br/>phát hiện số công chứng bị hở"]
        ULUP["Playwright → web CSDL<br/>công chứng tỉnh Nam Định"]
        ULIN --> ULEX --> ULDB --> ULAUD --> ULUP
    end

    subgraph NO["notaryoffice — Theo dõi hồ sơ đang chạy (chưa code)"]
        direction TB
        NOSEN["Activity Sentinel trên 6 máy con<br/>file save · print spooler · scan"]
        NOEV["Evidence Record<br/>(dữ kiện quan sát được)"]
        NODC["Draft Case Builder<br/>+ confidence ranking"]
        NOCF["Popup xác nhận tại máy trạm"]
        NOSE["Search: hồ sơ bà Gái ở đâu?"]
        NOSEN --> NOEV --> NODC --> NOCF --> NOSE
    end

    SD["systemdocs<br/>vocabulary · ranh giới · quyết định mở"]
    SD -.->|tham chiếu, không ràng buộc runtime| NV2
    SD -.->|tham chiếu, không ràng buộc runtime| UL
    SD -.->|tham chiếu, không ràng buộc runtime| NO

    NV2OUT -. "hôm nay: người copy file thủ công" .-> ULIN
```

Mũi tên nét rời duy nhất giữa hai sản phẩm là **thao tác tay của con người**:
Word do `notary_v2` sinh ra được lưu vào ổ đĩa, và sau đó `upload_lab` quét ổ
đĩa đó như quét bất kỳ Word nào khác. Không có tích hợp code.

## 2. Ai sở hữu dữ liệu gì

Quy tắc chống chồng chéo: mỗi loại dữ liệu có **đúng một** công cụ chủ sở hữu.
Quy tắc này vẫn giữ sau khi gộp DB — dùng chung database **không** có nghĩa là ai
cũng được ghi vào bảng của người khác.

| Dữ liệu | Chủ sở hữu | Ghi chú |
|---|---|---|
| Hồ sơ đang soạn, các bên, tài sản, quan hệ thừa kế | `notary_v2` | `notary.db` |
| Kết quả Cloud OCR giấy tờ + media Zalo | `notary_v2` | `ocr_jobs.db`, storage backend |
| Word/hợp đồng sinh ra từ template | `notary_v2` | |
| Trường dữ liệu bóc từ kho Word cũ | `upload_lab` | `output/*.json`, `registry.sqlite3` |
| Trạng thái đã/chưa upload lên web tỉnh | `upload_lab` | `registry.sqlite3` (`SCANNED`/`UPLOADED`) |
| Session đăng nhập web tỉnh | `upload_lab` | `nd_storage_state.json` |
| Dấu vết thao tác trên máy con | `notaryoffice` | chưa tồn tại |
| Trạng thái/giai đoạn/người đang giữ hồ sơ đang chạy | `notaryoffice` | chưa tồn tại |

**Hôm nay: không công cụ nào đọc DB của công cụ khác.** Đây là trạng thái của
giai đoạn hiện tại, không phải nguyên tắc vĩnh viễn — đích đến là DB dùng chung.

Nhưng cho tới khi việc gộp được thiết kế và duyệt, mọi dữ liệu chéo phải đi qua
một contract thống nhất trước (`contracts/README.md`). **Agent không được tự mở
kết nối đọc DB của repo khác** vì "dù sao sau này cũng gộp".

Khi gộp thật: quyền **ghi** vẫn thuộc đúng một chủ sở hữu như bảng trên; các công
cụ khác chỉ **đọc**.

## 3. Chồng chéo đã biết — không phải bug, nhưng phải theo dõi

Ba sản phẩm cùng bóc tách thực thể công chứng và đang có **ba cách làm riêng**:

| Việc | `notary_v2` | `upload_lab` | `notaryoffice` (dự kiến) |
|---|---|---|---|
| Nguồn đầu vào | ảnh giấy tờ | file Word | file Word đang sửa |
| Cách lấy text | Cloud AI OCR | `python-docx` + IFilter | IFilter |
| Bóc trường | regex trong `routers/ocr_ai.py` | regex trong `extract_contract.py` | regex phía Central Hub |

Đây là trùng lặp **có chủ ý ở giai đoạn này** — ba nguồn đầu vào khác nhau về
bản chất, hợp nhất sớm sẽ tạo abstraction sai. Nhưng ba nơi cùng định nghĩa "số
GCN hợp lệ là gì" là rủi ro thật: sửa một nơi, hai nơi kia lệch.

**Cách xử lý đã chốt:** giai đoạn này chưa gộp code, nhưng **bắt buộc thống nhất
định nghĩa thực thể** ở `contracts/entities.md`. Ba repo tự implement, cùng tham
chiếu một định nghĩa.

Đây chính là việc quan trọng nhất phải làm đúng từ bây giờ: nếu ba nơi lưu CCCD
theo ba định dạng khác nhau, lúc gộp DB sẽ không join được và phải làm lại toàn
bộ dữ liệu cũ.

## 4. Kiến trúc dự kiến của notaryoffice

Sản phẩm này chưa có code nên toàn bộ mục này là **thiết kế**, không phải hiện
trạng. Nguồn: `notaryoffice/intent_v2.md` (quyết định kỹ thuật) và
`notaryoffice/session_summary.md` (mở rộng sang Evidence Record).

Mô hình đã chọn: **Hybrid Pipeline — Edge IFilter + Central Processing Hub**

- **Máy trạm (~6 máy):** Sentinel C# .NET 8 siêu mỏng. Bắt file save
  (`ReadDirectoryChangesW`, debounce 3–5 phút), bắt print job (Event ID 307),
  gọi Windows IFilter (`query.dll`) lấy plain text trong ~5–15ms — đọc được cả
  khi Word đang mở file, xử lý được cả `.doc` cũ và `.docx`. Gửi JSON text
  (20–50KB) về Hub, **không gửi file nhị phân**. Có SQLite FIFO buffer local,
  tự flush khi LAN trở lại.
- **Máy chủ (1 máy/NAS trong văn phòng):** Central Hub — Python FastAPI + DB.
  Lưu `document_snapshots`, tính text diff, chạy regex tất định trên delta, ghép
  print job để phân biệt bản nháp và bản chuẩn ký, dựng Draft Case, phục vụ
  search.
- **Lớp AI:** chỉ vào 10–15% ca mơ hồ (semantic diff, suy luận bàn giao, quét
  hồ sơ chết lâm sàng, dịch câu hỏi tự nhiên thành truy vấn). Phải thay thế
  được, không được giữ trạng thái nghiệp vụ riêng.

Hai tín hiệu xương sống đã chốt:

1. **Word text diff** → biến động thực thể (thêm/sửa CCCD, GCN, thửa/tờ, số
   tiền, diện tích) → cập nhật Case, phát hiện việc phát sinh.
2. **Print spooler** → mức độ hoàn thiện tài liệu. Ý tưởng ban đầu là phân biệt
   `DRAFT_PRINTED` / `FINAL_PRINTED` theo **số bản in** (in 1 bản = soát lỗi; in
   ≥2 bản = bản chuẩn sẵn sàng ký, vì hợp đồng công chứng phải in 3–4 bản).

   ⚠️ **Cách này không dùng được.** Print Spooler **không cung cấp số bản in**
   (`OPEN_DECISIONS.md` A2 — đã chốt = Không). Số bản chỉ suy ra được từ tổng số
   trang, tức là **suy đoán**. Vì vậy phải phân biệt bằng tín hiệu khác: thời
   điểm in so với lần sửa cuối, có sửa file sau khi in hay không, số lần in. Đừng
   thiết kế tính năng nào cần biết chính xác số bản in.

Ba phương án đã **loại bỏ** (đừng đề xuất lại):

- ❌ FileWatcher tập trung trên máy chủ — SMB/NAS trễ, sinh event ảo, không
  định danh được user nào trên máy nào, và bỏ sót 20% file nằm trên ổ máy con.
- ❌ Full edge processing (máy trạm tự diff + tự chạy regex) — biến máy nhân
  viên thành heavy client, và mỗi lần sửa regex phải đi cài lại 6 máy.
- ❌ Tự động ghép cứng 100% theo điểm ≥90 không cần người xác nhận — trùng tên,
  trùng số thửa giữa các xã dẫn tới ghép nhầm hồ sơ.

## 5. Lộ trình đi tới hệ thống thống nhất

**Giai đoạn 1 — hiện tại: làm tốt từng phần.** Ba công cụ phát triển riêng. Việc
duy nhất làm ở tầng hệ thống: **không để phân kỳ** — khóa định danh giống nhau
(`contracts/entities.md`), công nghệ giống nhau cho cùng một việc
(`TECH_STACK.md`), tên trường và kiểu dữ liệu giống nhau khi tạo bảng mới.

**Giai đoạn 2 — hội tụ có chọn lọc.** Nối những chỗ rẻ và rõ ràng, từng cái một,
mỗi cái một contract. Ứng viên đầu tiên đã được nêu ở
`notaryoffice/gioi-thieu-du-an.md` mục 8: `notaryoffice` đọc số công chứng từ
`registry.sqlite3` của `upload_lab` ở chế độ **chỉ đọc**, để có bộ khung hồ sơ
chính xác 100% thay vì suy đoán. Chưa cam kết thời điểm.

**Giai đoạn 3 — một hệ thống, một database dùng chung.** Ba công cụ trở thành ba
đường xử lý dữ liệu trên cùng một kho. Điều kiện để giai đoạn này không thành một
lần viết lại toàn bộ:

- Khóa định danh đã thống nhất từ giai đoạn 1 (điều kiện bắt buộc).
- Không có hai công nghệ khác nhau cho cùng một việc.
- Không dùng tính năng riêng của SQLite ở tầng nghiệp vụ — DB chung có thể là
  PostgreSQL. Chi tiết: `TECH_STACK.md` mục 3.
- ID không trùng giữa các nguồn.
- Mỗi loại dữ liệu vẫn có đúng một chủ sở hữu quyền ghi (mục 2).

**Chưa tới lúc thiết kế giai đoạn 3.** Ghi ra đây để không ai vô tình đóng cửa nó
bằng một quyết định kiến trúc nhỏ ở giai đoạn 1.

Điều kiện chặn mọi bước hội tụ: cả hai bên phải đồng ý một contract ghi ở
`contracts/` **trước khi** viết code tích hợp. Không agent nào được tự tạo
contract rồi tự implement trong cùng một task.
