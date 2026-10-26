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
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt; phần "ý nghĩa mã" đã chốt ở D-028 · **Loại:** kỹ thuật
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
- **Trạng thái:** Đã chốt; owner xác nhận lại ở D-020 (Q-001) · **Loại:** lệch nghiệp vụ (quy ước sản phẩm)
- **Quyết định:** `Fraction(1, len(owners))`. Không nhập tỷ lệ riêng (D-020).
- **Lý do:** đa số hồ sơ đất là hai vợ chồng, chia đôi trùng HNGĐ 66.
- **Nguồn:** BR §3.1; engine :276.

### D-014 — `nhường phần` không phải từ chối nhận di sản
- **Trạng thái:** Đã chốt; **sửa một phần bởi D-024** (nhóm "người còn lại" mang nhãn nghiệp vụ "từ chối" — vẫn không phải văn bản từ chối 620) · **Loại:** luật (620)
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

### D-020 — Đồng sở hữu: chia đều giữa các chủ đất hiện tại (Q-001)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ
- **Bối cảnh:** luật: di sản là phần của người chết theo giấy tờ/thoả thuận (BLDS 612); tài sản chung vợ chồng chia đôi (HNGĐ 66).
- **Quyết định:** mặc định chia đều tài sản cho những người đang là chủ đất. Không thêm ô nhập tỷ lệ.
- **Lý do:** owner: thực tế hồ sơ; khi chỉ có hai vợ chồng thì trùng luật (chia đôi).
- **Hệ quả:** giữ `1/len(owners)` (D-013). Lệch luật khi giấy tờ ghi tỷ lệ không đều — công chứng viên tự xử lý ngoài app.
- **Nguồn:** owner 26/10/2026, trả lời Q-001.

### D-021 — Không có logic theo phiên bản luật; áp quy tắc hiện hành (Q-002, tạm)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt tạm (owner); Q-002 vẫn mở, ưu tiên thấp, cần giải thích lại · **Loại:** lệch nghiệp vụ (giới hạn)
- **Bối cảnh:** luật áp dụng là luật tại thời điểm mở thừa kế; người chết trước 01/01/2017 có thể thuộc BLDS 2005/1995.
- **Quyết định:** engine không phân nhánh theo phiên bản luật; luôn áp quy tắc BLDS 2015.
- **Lý do:** owner: thực tế chưa từng vướng; quy định hàng thừa kế/thế vị ổn định giữa luật cũ và mới.
- **Hệ quả:** không thêm cảnh báo theo ngày. Cần giải thích lại cho owner: câu hỏi chỉ là "nếu người chết trước 2017 thì có điểm nào luật cũ khác không" (ví dụ quy định chuyển tiếp) — hiện không biết điểm khác nào ảnh hưởng hồ sơ đất.
- **Nguồn:** owner 26/10/2026, trả lời Q-002.

### D-022 — Chỉ lưu vợ/chồng hợp pháp cuối cùng; vợ/chồng cũ chỉ để phân biệt con (Q-003)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ
- **Bối cảnh:** luật: người đang ly hôn chưa có hiệu lực, hoặc tái hôn sau khi người kia chết, vẫn thừa kế (655).
- **Quyết định:** một `spouseSlotId` = vợ/chồng hợp pháp cuối cùng. Không lưu lịch sử hôn nhân. Vợ/chồng cũ (nếu nhập) **không** có suất; chỉ dùng để biết con là con chung hay con riêng (gắn cha/mẹ của con, D-023).
- **Lý do:** owner: về pháp lý vợ/chồng cũ không còn liên quan.
- **Hệ quả:** không làm phương án lịch sử hôn nhân. Trường hợp 655 (đang ly hôn, tái hôn sau) user tự xác định ai là "vợ/chồng cuối cùng hợp pháp" khi nhập.
- **Nguồn:** owner 26/10/2026, trả lời Q-003.

### D-023 — "Con" gồm con đẻ và con nuôi; con hưởng từ cha/mẹ được gắn tên (Q-004)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ (đơn giản hoá)
- **Bối cảnh:** luật có 653 (con nuôi), 654 (con riêng – bố dượng/mẹ kế có nuôi dưỡng).
- **Quyết định:** không phân loại đẻ/nuôi. Mỗi con trong diagram gắn tên cha, tên mẹ (được để trống). Con đã gắn với cha/mẹ nào thì hưởng di sản của người đó. Không gắn = không hưởng từ người đó.
- **Lý do:** owner: đủ cho thực tế, giảm nhập liệu.
- **Hệ quả:** giữ tối đa 2 cha/mẹ, không thêm loại quan hệ. Con riêng hưởng từ bố dượng/mẹ kế (654) chỉ khi user tự gắn — lệch luật có chủ đích, user chịu trách nhiệm.
- **Nguồn:** owner 26/10/2026, trả lời Q-004.

### D-024 — Ba nhóm: chủ đất · người nhận · còn lại mặc định "từ chối" (Q-005)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ (cố ý)
- **Bối cảnh:** luật có từ chối bằng văn bản (620), không được quyền hưởng (621), truất quyền qua di chúc.
- **Quyết định:** mọi người chia thành **chủ đất / người nhận / những người còn lại**; nhóm còn lại mặc định là người từ chối. Khác biệt thì user sửa tay. App **không** mô hình hoá từ chối hợp pháp, không được quyền hưởng, truất quyền.
- **Lý do:** owner: làm rõ các trường hợp này quá phức tạp cho hệ thống.
- **Hệ quả:** sửa một phần D-014: được dùng nhãn "từ chối" cho nhóm còn lại như nhãn nghiệp vụ; app vẫn không tạo/kiểm văn bản từ chối 620. Việc nhóm còn lại có phải lập văn bản từ chối hay không do công chứng viên quyết. Phần của người "từ chối" chia lại theo D-025 (đề xuất).
- **Nguồn:** owner 26/10/2026, trả lời Q-005.

### D-025 — Người thế vị từ chối: chia lại trong nhánh trước, hết nhánh mới ra cả hàng (Q-006, ĐỀ XUẤT)
- **Ngày:** 26/10/2026 · **Trạng thái:** **Đề xuất — chờ owner xác nhận** · **Loại:** luật (cách hiểu) + khớp D-024
- **Bối cảnh:** owner nhờ Mika đề xuất. Luật: 620 cho phép từ chối (văn bản, trước khi chia); BLDS không có điều riêng về chia lại phần bị từ chối trong thừa kế theo pháp luật (650.1(c) nói về người thừa kế theo di chúc từ chối) → phần đó về những người thừa kế theo pháp luật còn lại theo 651–652; 651.2 người cùng hàng hưởng bằng nhau; 652 cháu/chắt hưởng **phần mà cha/mẹ lẽ ra được hưởng** — tức phần đó gắn với vị trí (nhánh) của người chết trước. 623 chỉ là thời hiệu, không ảnh hưởng.
- **Đề xuất:** người thế vị (cháu/chắt) từ chối/không nhận → phần đó ở lại nhánh, chia đều cho những người thế vị còn nhận **cùng nhánh** (theo từng cấp). Chỉ khi cả nhánh không còn ai nhận thì phần nhánh mới chia cho các suất còn lại của hàng 1 trong cùng vòng (trùng D-011).
- **Lý do:** đúng cấu trúc 652 (cả nhánh thay một suất), không làm thay đổi phần của nhánh khác; **engine hiện đã làm đúng như vậy** (`descendant_plan` bỏ người không nhận khỏi nhánh rồi chia đều người còn lại; nhánh rỗng thì không thành đơn vị, `first_line_units` chia cho đơn vị còn lại) → không phải sửa code; áp chung cho "từ chối" mặc định của D-024 và `nhường phần`.
- **Hệ quả nếu chọn "cả hàng":** phải đổi engine, và một cháu từ chối sẽ làm tăng phần của chú/bác — trái tinh thần 652.
- **Nguồn:** Mika 26/10/2026; `inheritance_engine.py` :308-342.

### D-026 — Chỉ thừa kế theo pháp luật; không di chúc, không phần bắt buộc; bỏ qua thai nhi (Q-007)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** giới hạn phạm vi (di chúc) + lệch nghiệp vụ (thai nhi)
- **Bối cảnh:** 644 (phần bắt buộc) thuộc thừa kế theo di chúc; 613 người thành thai trước khi người để lại di sản chết và sinh ra còn sống vẫn được thừa kế.
- **Quyết định:** hồ sơ chỉ làm thừa kế theo pháp luật. Không xử lý thai nhi: chỉ người có giấy tờ cá nhân mới được đưa vào; khách hàng chịu trách nhiệm về việc thành thai.
- **Hệ quả:** không làm template Word cho nhánh di chúc. Hàng 2–3 vẫn `unsupported` (chưa có quyết định đổi).
- **Nguồn:** owner 26/10/2026, trả lời Q-007.

### D-027 — Không xét ai ký; ai có tên trong Stage là người liên quan (Q-008)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** lệch nghiệp vụ (không can thiệp)
- **Quyết định:** app không tính danh sách người phải ký. Ai có tên trong Stage được coi là người liên quan; app không can thiệp thực tế ký.
- **Nguồn:** owner 26/10/2026, trả lời Q-008.

### D-028 — Bỏ bộ mã 1.x.x làm định danh; nhánh lấy từ engine (Q-009)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner, có điều kiện — điều kiện đã kiểm) · **Loại:** kỹ thuật
- **Quyết định owner:** mã 1.1.x chỉ là gợi ý ghi nhãn; nếu engine đã nhận diện hàng/tầng/nhánh chính xác thì không cần.
- **Kiểm engine (26/10/2026):** engine chỉ tính hàng 1 (cha mẹ, vợ/chồng, con; hàng 2/3 không có). Mỗi phần nhận có `kind` (`inheritance`/`representation`), `sourcePersonId` (vòng di sản nguồn) và `viaBranchPersonIds` (đường nhánh qua người chết trước) → **nhánh và người thuộc nhánh nào được xác định chính xác**, chuyển tiếp (vòng mới) và thế vị tách rõ. Không có field "hàng"/"tầng" riêng, nhưng suy ra được (độ dài `via` = tầng; hàng luôn 1).
- **Kết luận:** bỏ 1.x.x làm định danh/nguồn sự thật. Nếu cần nhãn hiển thị thì sinh từ `sourcePersonId` + `viaBranchPersonIds`.
- **Ghi chú:** engine không tự dừng ở chắt (D-012) — chưa thấy kiểm độ sâu trong `descendant_plan`; việc code sau.
- **Nguồn:** owner 26/10/2026; `inheritance_engine.py` :308-360.

### D-029 — Tối đa 3 tài sản mỗi hồ sơ (Q-010)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** kỹ thuật
- **Quyết định:** 3 tài sản.
- **Hệ quả (việc code sau, chưa sửa):** `word_engine.py` có `MAX_WORD_ASSETS = 5`, UI là 3 — phải thống nhất về 3.
- **Nguồn:** owner 26/10/2026, trả lời Q-010.

### D-030 — Lỗi cấu trúc vẫn được lưu (Q-012)
- **Ngày:** 26/10/2026 · **Trạng thái:** Đã chốt (owner) · **Loại:** kỹ thuật (khớp D-002)
- **Quyết định:** lưu nguyên trạng kể cả khi có lỗi cấu trúc, `status: invalid`, có nhãn.
- **Hệ quả (việc code sau):** code/contract vẫn chặn `diagram_invalid_state` và README §8 ghi "invalid: save bị chặn" — xung đột còn nguyên.
- **Nguồn:** owner 26/10/2026, trả lời Q-012.
