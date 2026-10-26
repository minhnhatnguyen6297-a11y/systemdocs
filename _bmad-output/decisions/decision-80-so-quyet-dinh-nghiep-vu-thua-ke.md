# Quyết định: sổ quyết định nghiệp vụ thừa kế (D-xxx)

Ngày lập: 2026-10-26. Owner yêu cầu có "project memory" để agent không hỏi lại
những gì đã chốt; câu hỏi phải có lý do; nghiệp vụ được phép lệch luật nếu ghi rõ.

## Cách dùng

- Một file, nhiều mục `D-xxx`. Thêm mục mới ở cuối, **không** đánh số lại, không
  xoá: quyết định bị thay thì đổi `Trạng thái` thành `Bị thay bởi D-yyy`.
- **Loại:** `luật` (làm theo điều luật) · `lệch nghiệp vụ` (owner chủ động khác
  hoặc thêm ngoài luật) · `kỹ thuật` (cách app lưu/hiển thị, không đổi quyền hưởng).
- Điều luật: [`legal-baseline.md`](../specs/notary_v2/diagram/inheritance/legal-baseline.md).
  Câu hỏi chưa chốt: [`business-rules.md` §16](../specs/notary_v2/diagram/inheritance/business-rules.md#16-câu-hỏi-mở-q-xxx).
- Khi owner trả lời một Q-xxx: thêm D-xxx ngay trong phiên, đánh dấu Q đó `Đã chốt → D-xxx`.

Nguồn viết tắt: **HT1/HT2** = hai file review hội thoại (vòng 2 adversarial +
review BLDS 2015) tổng hợp trong brainstorm "Kiến trúc Diagram trong Soạn hồ sơ"
26/10/2026; **BR** = `business-rules.md`.

---

### D-001 — Chỉ hai trạng thái sống/chết; ngày trống hoặc sai coi là còn sống
- **Ngày:** trước 26/10/2026 (HT1) · **Trạng thái:** Đã chốt · **Loại:** lệch nghiệp vụ
- **Bối cảnh:** dữ liệu khách thường thiếu ngày chết; luật cần chứng cứ chết (611).
- **Quyết định:** không có trạng thái "không rõ". Ngày chết trống/không parse được → còn sống.
- **Lý do:** đơn giản cho người nhập; người chết luôn có giấy chứng tử để điền ngày.
- **Hệ quả:** engine không cảnh báo "thiếu ngày chết"; nhập sai ngày làm đổi kết quả âm thầm → UI nên hiển thị rõ ai đang được coi là sống.
- **Nguồn:** HT1; brainstorm (a).

### D-002 — Không bao giờ chặn lưu và xuất Word (QĐ-A)
- **Ngày:** trước 26/10/2026 · **Trạng thái:** Đã chốt · **Loại:** kỹ thuật
- **Bối cảnh:** chặn lưu khi engine chưa `complete` làm mất công nhập; hàng 2/3 luôn `unsupported`.
- **Quyết định:** lưu và xuất Word được ở mọi trạng thái; trạng thái (`invalid`/`unsupported`/`incomplete`/`complete`) ghi vào `engineResult` và hiện nhãn trên UI/Word.
- **Lý do:** công chứng viên mới là người kết luận; app chỉ cảnh báo (BR INV-11).
- **Hệ quả:** **lệch code/contract hiện tại**: `diagram_invalid_state` vẫn chặn lỗi cấu trúc; README §8 ghi "invalid: save bị chặn". Phải sửa contract + code (BR §13 mục 5). Lỗi cấu trúc làm hỏng dữ liệu (vd. vòng tổ tiên thật) cần quyết định riêng cách lưu — xem Q-012.
- **Nguồn:** HT1/HT2; BR §13 mục 5.

### D-003 — Một nguồn sự thật; mọi màn hình là view của nó
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (hướng kiến trúc) · **Loại:** kỹ thuật
- **Bối cảnh:** preview dùng draft, Word dùng bản đã lưu; web cũ tự tính lại phân số.
- **Quyết định:** fact đã lưu theo revision → engine Python → projection. Diagram, bảng `Xem cách tính`, danh sách người ký, Word đều đọc **cùng một** projection của **một** revision.
- **Lý do:** tránh Word âm thầm khác màn hình.
- **Hệ quả:** Word phải ghi revision và cảnh báo khi còn thay đổi chưa lưu; gỡ dần `engine_state_json`, `inheritance_participants.ty_le`, `diagram_edges.js`.
- **Nguồn:** brainstorm (d) phương án B.

### D-004 — ID ổn định; mã 1.1.x chỉ là nhãn hiển thị
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt · **Loại:** kỹ thuật
- **Quyết định:** quan hệ, phân bổ, lịch sử bám `personId`/`nodes[].id` (và `estateId`/`allocationId` khi có — chưa có trong code). Không bao giờ suy quan hệ hay quyền hưởng từ mã 1.1.x.
- **Lý do:** mã đổi khi sắp lại cây; ID không đổi.
- **Hệ quả:** ý nghĩa mã cần chốt riêng (Q-009).
- **Nguồn:** HT2; brainstorm (d).

### D-005 — Một người có thể mang nhiều mã; không có field "pair anchor"
- **Ngày:** trước 26/10/2026 · **Trạng thái:** Đã chốt · **Loại:** kỹ thuật
- **Quyết định:** một người xuất hiện ở nhiều vai/nhánh thì hiển thị nhiều mã, vẫn là một `personId`. Không thêm field neo cặp vợ chồng.
- **Hệ quả:** cộng dồn phần từ nhiều nguồn (BR INV-7).
- **Nguồn:** HT1.

### D-006 — Chết cùng thời điểm hoặc không rõ thứ tự: không thừa kế của nhau
- **Trạng thái:** Đã chốt · **Loại:** luật (619)
- **Quyết định:** hai người cùng ngày chết đầy đủ, hoặc comparator trả "không xác định thứ tự", không nhận di sản của nhau; phần của con chết cùng lúc đi xuống theo thế vị (652).
- **Nguồn:** HT1; BR §4.3.

### D-007 — Ngày chỉ có năm = "không phân biệt được thứ tự"
- **Trạng thái:** Đã chốt (user) · **Loại:** lệch nghiệp vụ (quy ước nhập liệu)
- **Quyết định:** `yyyy` không phải dữ liệu thiếu; `01/01/yyyy` chỉ là khoá sắp xếp nội bộ, không in, không dùng để nói ai chết trước.
- **Hệ quả:** code hiện ép `2010` → `2010-01-01` và mất cờ độ phân giải (BR §11.1) — phải sửa.
- **Nguồn:** BR §4.2.

### D-008 — Nhận/nhường theo từng người × từng vòng di sản × từng tài sản
- **Trạng thái:** Đã chốt · **Loại:** luật (656, thoả thuận phân chia) + kỹ thuật
- **Quyết định:** mặc định `giữ phần`; user chọn `nhường phần` trên từng tài sản.
- **Hệ quả:** adapter `_v3_to_v2_nodes` hiện ép `receivePositions` thành một boolean `willReceive` → mất thông tin theo tài sản trước khi tính. Phải sửa.
- **Nguồn:** HT1; BR §7.

### D-009 — Người bị gỡ khỏi Diagram trả về Pool
- **Trạng thái:** Đã chốt · **Loại:** kỹ thuật
- **Quyết định:** gỡ node không xoá người khỏi Stage; người đó lại xuất hiện trong Pool (Pool = Stage − Diagram, tính ra, không lưu).
- **Nguồn:** HT1; `notary_v2/README.md` §2.

### D-010 — Con chết sau người để lại di sản: chuyển tiếp, không phải thế vị (Q01 brainstorm)
- **Trạng thái:** Đã chốt (theo luật, không cần hỏi) · **Loại:** luật (613, 614, 652)
- **Quyết định:** C chết sau X → C hưởng phần tại lúc X chết, phần đó vào di sản của C và mở vòng di sản mới khi C chết. Thế vị chỉ khi C chết trước/cùng thời điểm X.
- **Hệ quả:** engine đã làm đúng (holdings dương được chuyển tiếp); UI/mã phải tách hai đường này (Q-009).
- **Nguồn:** brainstorm Q01; `legal-baseline.md` §3; BR §5–6.

### D-011 — Nhánh không còn ai nhận: chia lại cho các đơn vị còn lại cùng vòng
- **Trạng thái:** Đã chốt (user) · **Loại:** lệch nghiệp vụ
- **Quyết định:** như BR §6.2 (ví dụ bà V nhận toàn bộ khi các cháu thế vị đều nhường).
- **Lý do:** đây là ý chí thoả thuận của người có suất, không phải từ chối pháp lý.
- **Nguồn:** BR §6.2.

### D-012 — Thế vị dừng ở chắt
- **Trạng thái:** Đã chốt · **Loại:** luật (652)
- **Quyết định:** sâu hơn chắt → `unsupported: representation_depth_exceeded`.
- **Nguồn:** BR §6.1.

### D-013 — Đồng chủ sở hữu mặc định chia đều
- **Trạng thái:** Đã chốt cho code hiện tại · **Loại:** lệch nghiệp vụ (quy ước sản phẩm)
- **Quyết định:** `Fraction(1, len(owners))` khi chưa có tỷ lệ. Nhập tỷ lệ riêng: Q-001.
- **Lý do:** đa số hồ sơ đất là hai vợ chồng, chia đôi trùng HNGĐ 66.
- **Nguồn:** BR §3.1; engine :276.

### D-014 — `nhường phần` không phải từ chối nhận di sản
- **Trạng thái:** Đã chốt · **Loại:** luật (620)
- **Quyết định:** không suy "người từ chối" từ việc bỏ tick Nhận; cấm nhãn "từ chối/khước từ/waive". Word để `legal_refusal_people=[]`.
- **Hệ quả:** `/export-word-legacy` vẫn ghi "từ chối" — phải gỡ.
- **Nguồn:** HT2; BR §2.

### D-015 — Engine không bịa người, quan hệ, hay kết luận ngoài sơ đồ
- **Trạng thái:** Đã chốt · **Loại:** kỹ thuật
- **Quyết định:** BR INV-9, INV-13. Thiếu thì trả `requiredSlots`/cảnh báo.

### D-016 — Vợ/chồng của người chết trước không nhận phần thế vị
- **Trạng thái:** Đã chốt · **Loại:** luật (652)
- **Quyết định:** ô vợ/chồng chỉ sinh để biểu diễn cặp cha mẹ; tài sản riêng của người chết trước vẫn mở vòng riêng, nơi vợ/chồng là hàng 1.
- **Nguồn:** BR §6.

### D-017 — Tài sản chung vợ chồng: nửa của người chết mới là di sản
- **Trạng thái:** Đã chốt · **Loại:** luật (HNGĐ 33, 66; BLDS 612)
- **Quyết định:** hai vợ chồng cùng là Chủ trên tài sản chung; vòng di sản của người chết chỉ chia phần của người đó; người còn sống giữ phần sở hữu gốc.
- **Nguồn:** `legal-baseline.md` §4; BR §2, §3.

### D-018 — Giao thức hỏi owner
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** kỹ thuật (quy trình)
- **Quyết định:** trước khi hỏi: tra decisions → `legal-baseline.md` → code/spec. Chỉ hỏi lựa chọn nghiệp vụ thật, gom thành một lượt, mỗi câu có bối cảnh, mặc định theo luật, khuyến nghị, lý do. Trả lời xong ghi D-xxx ngay.
- **Nguồn:** owner 26/10/2026 ("không bị hỏi mãi", "hỏi phải có lý do").

### D-019 — Mặc định theo luật; lệch luật phải ghi
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ (nguyên tắc)
- **Quyết định:** khi chưa có quyết định, app làm theo luật. Owner được chọn lệch; mục lệch phải là D-xxx loại `lệch nghiệp vụ` có lý do.
- **Nguồn:** owner 26/10/2026.
