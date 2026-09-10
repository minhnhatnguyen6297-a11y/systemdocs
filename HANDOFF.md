# Handoff — giao việc cho agent sửa từng repo

File này để chủ dự án copy đưa cho agent làm việc ở **một repo cụ thể**. Mỗi mục
là một gói việc độc lập, không phụ thuộc mục khác.

Cập nhật: 10/09/2026 · Trạng thái systemdocs: đã sửa xong theo các câu trả lời
A2 / B1 / B2 / B3 / B4 và định hướng gộp hệ thống.

**Bối cảnh một câu để agent nào cũng hiểu:** ba repo là ba công cụ riêng, nhưng
đích đến là **một hệ thống thống nhất dùng chung database**. Giai đoạn hiện tại
là làm tốt từng phần — kèm đúng một nghĩa vụ: **không chọn công nghệ lệch nhau**,
vì lúc gộp sẽ phải viết lại.

---

## 0. Việc chung: nối repo con về folder cha

**Mục tiêu:** agent ở repo con biết folder này tồn tại, nhưng **không đọc nó
theo mặc định** — chỉ đọc khi task chạm ranh giới giữa các sản phẩm, hoặc khi
sắp chọn một công nghệ mới. Tránh phình context.

### 0.1. `notary_v2` — đã có `AGENTS.md`, chỉ thêm vào

Thêm **đúng khối này** vào `D:\notary_v2\AGENTS.md`, đặt ở cuối mục
`## Sources of truth` (sau bảng routing, trước mục kế tiếp):

```markdown
## Cross-product context (read only when needed)

`D:\systemdocs\systemdocs` — parent docs for the notary product family
(`notary_v2`, `upload_lab`, `notaryoffice`). Not needed for normal tasks.

Read it only when the task touches: product boundaries, shared entity keys
(CCCD / GCN serial / parcel / notarization number), or a cross-product
integration. Then read only the file you need:
`PROJECTS.md` (what the other repos are), `contracts/entities.md` (key
normalization), `OPEN_DECISIONS.md` (do not decide these alone).

MUST read before choosing a new technology (a different OCR provider, ORM,
queue, or UI framework) or making an architecture decision: `TECH_STACK.md`.
The three repos will merge onto one shared database; diverging now means
rewriting later.

It does not override this file. On conflict, this repo wins for internal
behavior; report the conflict instead of silently following either side.
```

Lưu ý cho agent: `notary_v2/AGENTS.md` có scope-lock chặt. Việc thêm khối này là
sửa tài liệu, không sửa hành vi — nhưng vẫn nên xin xác nhận trước khi commit.

### 0.2. `upload_lab_repo` — chưa có `AGENTS.md`, cần tạo

Tạo `D:\upload_lab_repo\AGENTS.md`. **Tối giản**, không copy phong cách nặng của
`notary_v2`:

```markdown
# AGENTS.md — upload_lab

## Sources of truth
- `README.md` — pipeline 3 giai đoạn, sơ đồ codebase, lệnh chạy/test
- `docs/regex-rules.md` — quy chuẩn trích xuất theo từng loại văn bản
- `docs/spec_UI.md` — UI

## Rules
- Không tự chuyển chế độ Finalize thành mặc định. Dry-run là mặc định.
- Đổi selector web tỉnh: sửa ở `uploader_selectors.py`, không rải trong code.
- Thêm loại văn bản mới: cập nhật `docs/regex-rules.md` cùng lúc với code.
- Chạy test trước khi báo xong.

## Cross-product context (read only when needed)
`D:\systemdocs\systemdocs` — tài liệu cấp cha cho họ sản phẩm công chứng.
Task thường ngày **không cần** đọc. Chỉ đọc khi task chạm ranh giới sản phẩm,
khóa định danh dùng chung, hoặc tích hợp: `PROJECTS.md`,
`contracts/entities.md`, `OPEN_DECISIONS.md`. Repo này thắng về hành vi nội bộ.

**Bắt buộc đọc `TECH_STACK.md` trước khi** thêm/đổi công nghệ (thư viện đọc
file, OCR, DB, queue, framework UI) hoặc ra quyết định kiến trúc. Ba repo sẽ
gộp về một database dùng chung, chọn lệch nhau là viết lại sau.
```

### 0.3. `notaryoffice` — chưa có git, chưa có code

Tạo `D:\notaryoffice\AGENTS.md`:

```markdown
# AGENTS.md — notaryoffice

**Trạng thái: tài liệu, chưa có code.** Đừng mô tả nó như hệ thống đang chạy.

## Sources of truth (theo thứ tự)
1. `intent_v2.md` — quyết định kỹ thuật đã chốt, phương án đã loại, 14 bảng DB
2. `session_summary.md` — Evidence Record, Draft Case, confidence = xếp hạng
3. `gioi-thieu-du-an.md` — lộ trình, chi phí, câu hỏi cần quyết định
4. `intent.md` — v0.1, đã bị thay thế. Chỉ tra lịch sử

## Rules
- Trước khi viết code: A1 / A3 / A4 ở systemdocs `OPEN_DECISIONS.md` phải có câu
  trả lời thật (A2 đã chốt = Không).
- Print Spooler **không cho biết số bản in**. Không thiết kế feature nào cần con
  số đó.
- Không đề xuất lại các phương án đã loại trong `intent_v2.md`.
- Không quay màn hình, không keylogger, không dùng cho chấm công.
- Zalo: chỉ tài khoản chung của Văn phòng, chỉ trên máy chủ. Không đọc tài khoản
  Zalo của nhân viên.
- Giới hạn cứng 3 popup xác nhận/người/ngày — không nới.

## Cross-product context (read only when needed)
`D:\systemdocs\systemdocs` — tài liệu cấp cha. Chỉ đọc khi task chạm ranh giới
sản phẩm hoặc khóa định danh dùng chung: `PROJECTS.md`,
`contracts/entities.md`, `OPEN_DECISIONS.md`.

**Bắt buộc đọc `TECH_STACK.md` trước khi** chọn công nghệ cho bất kỳ tầng nào
(Sentinel, Hub, DB, OCR, queue, UI). Repo này chưa có code nên đây là nơi dễ
chọn lệch nhất — hệ thống sẽ gộp về một database dùng chung.
```

Có nên `git init` cho `notaryoffice` không: **nên**, nhưng đó là quyết định của
chủ dự án, agent hỏi trước.

### 0.4. `researchskill` — KHÔNG làm gì

Ngoài phạm vi hệ thống công chứng. Không thêm `AGENTS.md`, không nối vào
systemdocs, không đưa vào sơ đồ.

---

## 1. Gói việc: `notary_v2`

**Không có việc sửa nào phát sinh từ systemdocs**, ngoài mục 0.1.

Điều agent cần biết để không làm sai:

- `notary_v2` **không** phải core platform. Không repo nào gọi vào nó.
- **Không** có luồng nhận dữ liệu từ `upload_lab`. Nếu thấy tài liệu nào nói có,
  tài liệu đó sai.
- `notary_v2` **không** dùng Windows IFilter (`query.dll` chỉ có trong `venv/`
  như dependency gián tiếp). Đừng "thống nhất" cách đọc file với `upload_lab`:
  hai repo đọc hai loại đầu vào khác nhau (`.docx` mới vs `.doc` cũ).
- Local OCR đang parked. **OCR cloud dùng Qwen-VL-OCR trên DashScope là lựa chọn
  đã ghi cho toàn hệ thống** (`TECH_STACK.md` §1) — repo nào định dùng OCR
  provider khác thì phải xin duyệt, không phải quyết định nội bộ.
- Zalo Document Inbox đã APPROVED. `notaryoffice` cũng làm Zalo
  (`OPEN_DECISIONS.md` B2 — làm, không hoãn) nhưng phạm vi khác: tài khoản chung
  của Văn phòng, chạy trên máy chủ. Hai việc không xung đột, và **chưa** được nối
  vào nhau.

Việc tùy chọn, nếu chủ dự án muốn: đối chiếu regex CCCD ở `routers/ocr_ai.py`
với `contracts/entities.md` §1. Hiện `notary_v2` nhận mọi cụm 12 số — rộng nhất
trong ba repo. Đây là **lựa chọn hợp lý cho OCR ảnh**, không phải lỗi. Chỉ sửa
nếu có bug thật.

Bảo mật, áp dụng cho mọi agent: `D:\notary_v2\.env` chứa API key thật. File đã
`.gitignore` và không được track. **Không copy giá trị key vào tài liệu, không
commit `.env`.** Khi cần nói tới key thì nói tên biến, mẫu ở `.env.example`.

---

## 2. Gói việc: `upload_lab`

Ngoài mục 0.2:

- Tạo `AGENTS.md` (nội dung ở 0.2).
- **Xóa mọi mô tả cũ nói `upload_lab` là "lab OCR ảnh"** nếu còn sót trong repo.
  Đầu vào là **file Word**, không phải ảnh scan.
- Ghi đúng lý do repo này tồn tại (vào `README.md` nếu chưa có): văn phòng **đã
  có** phần mềm quản lý hồ sơ công chứng, nhưng phần mềm đó **không có API để lấy
  dữ liệu ra** (`OPEN_DECISIONS.md` B1). Vì vậy nguồn dữ liệu thật là file Word
  cũ, không phải DB của phần mềm đó. Đừng ai đi tìm "API của phần mềm cũ" nữa —
  đã kết luận là không có.
- Không có nghĩa vụ nào với `notary_v2`. Đừng thêm export "cho notary_v2".
- `registry.sqlite3` là dữ liệu do repo này **sở hữu và ghi**. Sau này
  `notaryoffice` có thể **đọc** nó, nhưng chỉ khi có contract được duyệt
  (`SYSTEM_ARCHITECTURE.md` mục 5, giai đoạn 2). Agent không tự mở kết nối.

Việc tùy chọn, chỉ làm khi được yêu cầu: tách `thửa`/`tờ` thành trường riêng
(hiện chỉ trích cả khối text tài sản). Chưa cần cho việc upload; sẽ cần khi gộp
DB. Nếu làm thì dùng đúng tên trường ở `TECH_STACK.md` §3 (`so_thua_dat`,
`so_to_ban_do`).

---

## 3. Gói việc: `notaryoffice`

Ngoài mục 0.3.

### 3.1. Sửa trong tài liệu (làm được ngay, không cần đo máy)

| Chỗ | Vấn đề | Sửa thành |
|---|---|---|
| `intent.md` §5.2 | Regex CCCD bắt buộc chữ số đầu là `0` — **hẹp hơn thực tế** | Nhận mọi cụm 12 chữ số; xem `contracts/entities.md` §1 |
| `intent.md` §5.2 | Serial GCN ghi cứng 2 chữ cái + **6** chữ số | Nới thành 6–8 chữ số; `notary_v2` gặp phôi 7–8 số thật |

`intent.md` là v0.1 đã bị thay thế, nhưng hai chỗ này sẽ được copy vào code nếu
không sửa — nên sửa, hoặc ghi rõ ở đầu file là đã lỗi thời.

### 3.2. Sửa theo các câu đã chốt (làm ngay)

| Chỗ | Phải sửa vì |
|---|---|
| Mọi đoạn suy ra **số bản in** từ Print Spooler | **A2 đã chốt: Không.** Spooler không cung cấp số bản copy. Số bản chỉ suy được từ số trang, và đó là **suy đoán, không phải sự thật**. Không được dùng làm điều kiện cứng để phân biệt `DRAFT_PRINTED` / `FINAL_PRINTED` — thay bằng: thời điểm in so với lần sửa cuối, có sửa sau khi in hay không, số lần in. Feature nào cần con số chính xác thì bỏ. |
| `gioi-thieu-du-an.md` §8 — phương án "đọc DB/API phần mềm cũ trước" | **B1 đã chốt: có phần mềm nhưng không có API.** Phương án này **đóng**. Không còn đường tắt "lấy dữ liệu chính xác 100%". Nguồn thật: file Word, ảnh giấy tờ, dấu vết trên máy con. |
| Mọi đoạn khuyến nghị **hoãn Zalo** | **B2 đã chốt: làm, không hoãn.** Phạm vi: tài khoản Zalo **chung của Văn phòng**, đọc tin nhắn nhóm + tin nhắn riêng gửi tới tài khoản đó, **chỉ chạy trên máy chủ**. **Không** đọc tài khoản Zalo của nhân viên, không chạy trên máy con. Agent không được nới phạm vi này để "tăng độ phủ dữ liệu". |
| Phần pháp lý / triển khai | **B3 đã chốt: có.** Thông báo cho nhân viên và đưa vào nội quy lao động **trước** khi triển khai (Nghị định 13/2023). |

### 3.3. Phải làm trước khi viết dòng code đầu tiên

1. Trả lời **A1, A3, A4** ở `OPEN_DECISIONS.md` (A2 đã chốt). **A4 — máy dùng
   tài khoản Windows riêng hay chung — quan trọng nhất**, chỉ cần đi xem 6 máy.
2. Xong nội quy lao động (B3) trước khi triển khai, không phải sau.
3. Đọc `TECH_STACK.md` và chọn đúng công nghệ đã có trong hệ thống cho tầng Hub
   (Python FastAPI, SQLAlchemy 2.x, SQLite hôm nay nhưng viết code **không khóa
   vào SQLite**). Sentinel C# .NET 8 là lựa chọn đã ghi.

Agent **không được** bắt đầu implement Sentinel khi A1 / A3 / A4 còn 🔴.

---

## 4. Cách agent báo lại khi phát hiện systemdocs sai

Folder cha có thể lạc hậu so với code. Khi agent ở repo con thấy systemdocs mô tả
sai repo mình:

1. **Không tự sửa systemdocs** trong cùng task đang làm ở repo con.
2. Ghi lại: file nào, dòng nào sai, sự thật là gì, bằng chứng ở đâu (đường dẫn
   file + số dòng trong repo con).
3. Báo cho chủ dự án. Việc sửa systemdocs là một task riêng.

Lý do: một agent vừa sửa code vừa sửa tài liệu mô tả code của mình thì không còn
ai kiểm tra chéo.

Ngoại lệ ngược lại: nếu agent thấy repo mình **đang dùng một công nghệ khác** với
`TECH_STACK.md` cho cùng một việc, đó không phải lỗi tài liệu mà là **xung đột
thật** — báo ngay, vì đây chính là thứ sẽ vỡ lúc gộp DB.

---

## 5. Checklist cho chủ dự án

- [ ] 0.1 — thêm khối cross-product vào `notary_v2/AGENTS.md`
- [ ] 0.2 — tạo `upload_lab_repo/AGENTS.md`
- [ ] 0.3 — tạo `notaryoffice/AGENTS.md` (+ quyết định có `git init` không)
- [ ] 3.1 — sửa 2 chỗ regex trong `notaryoffice/intent.md`
- [ ] 3.2 — sửa 4 chỗ trong tài liệu `notaryoffice` theo A2 / B1 / B2 / B3
- [ ] A1, A3, A4 — đi đo trên 6 máy thật (A2 và B1 đã chốt)
- [ ] B3 — nội quy lao động, làm trước khi triển khai
- [ ] `researchskill` — không làm gì, đúng như thiết kế
