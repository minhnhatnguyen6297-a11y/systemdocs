# Nền pháp lý thừa kế — đối chiếu điều luật

> **Vai trò:** file duy nhất trong spec ghi **số điều luật**. `business-rules.md`
> giữ nguyên quy ước "không ghi số điều" và trỏ về đây. Quyết định đã chốt nằm ở
> [`decision-80`](../../../../decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md);
> câu hỏi mở nằm ở [`business-rules.md` §16](./business-rules.md#16-câu-hỏi-mở-q-xxx).
> **Trạng thái:** tóm tắt do agent đọc văn bản gốc ngày 26/10/2026. Chưa có người
> có chuyên môn pháp lý xác nhận. Tóm tắt **không** thay văn bản luật.
> **Mặc định:** app làm theo luật, trừ khi owner chốt lệch và ghi lý do (D-019).

## 1. Văn bản nguồn

| Văn bản | Hiệu lực | Link tra cứu |
|---|---|---|
| Bộ luật Dân sự 2015 (91/2015/QH13) — BLDS | 01/01/2017 | [thuvienphapluat](https://thuvienphapluat.vn/van-ban/Quyen-dan-su/Bo-luat-dan-su-2015-296215.aspx) · [vbpl.moj.gov.vn](https://vbpl.moj.gov.vn/toaannhandantoicao/Pages/vbpq-toanvan.aspx?ItemID=95942&Keyword=91%2F2015%2FQH13) · bản đã đọc: [luatvietnam](https://luatvietnam.vn/dan-su/bo-luat-dan-su-2015-101333-d1.html) |
| Luật Hôn nhân và gia đình 2014 (52/2014/QH13) — HNGĐ | 01/01/2015 | [thuvienphapluat](https://thuvienphapluat.vn/van-ban/Quyen-dan-su/Luat-Hon-nhan-va-gia-dinh-2014-238640.aspx) |

## 2. BLDS 2015 — Phần thừa kế

| Điều | Nội dung (tóm tắt) | Áp vào app |
|---|---|---|
| 611 | Thời điểm mở thừa kế là lúc người có tài sản chết; tuyên bố chết thì là ngày Toà xác định (khoản 2 Điều 71). Địa điểm: nơi cư trú cuối cùng. | Mỗi vòng di sản mở tại ngày chết (`business-rules` §5). |
| 612 | Di sản gồm tài sản riêng và phần tài sản của người chết trong tài sản chung. | Chủ đất / tỷ lệ sở hữu gốc (§3); Q-001. |
| 613 | Người thừa kế phải còn sống lúc mở thừa kế, hoặc đã thành thai trước khi người đó chết và sinh ra còn sống. | Comparator ngày (§4). Thai nhi: `fetus_not_supported`. |
| 614 | Quyền, nghĩa vụ tài sản của người thừa kế phát sinh từ thời điểm mở thừa kế. | Phần đã nhận thuộc người nhận ngay, kể cả khi họ chết sau (chuyển tiếp). |
| 615 | Nghĩa vụ tài sản của người chết được trả trong phạm vi di sản. | Ngoài phạm vi engine. |
| 619 | Người chết cùng thời điểm, hoặc được coi là cùng thời điểm vì không xác định được ai chết trước, **không thừa kế của nhau**; di sản mỗi người do người thừa kế của người đó hưởng, trừ thế vị theo Điều 652. | D-006, D-007. |
| 620 | Được từ chối nhận di sản, trừ khi để trốn nghĩa vụ. Phải lập **văn bản**, gửi người quản lý di sản và những người thừa kế khác, trước thời điểm phân chia. | `nhường phần` ≠ từ chối (D-014). `legal_refusal_not_supported`. |
| 621 | Người không được quyền hưởng di sản (khoản 1 a–d: xâm phạm tính mạng/sức khoẻ, vi phạm nghĩa vụ nuôi dưỡng, xâm phạm tính mạng người thừa kế khác, lừa dối/cưỡng ép về di chúc). Khoản 2: vẫn hưởng nếu người để lại di sản biết mà vẫn cho hưởng theo di chúc. | `disinheritance_not_supported`; Q-005. |
| 644 | Người thừa kế không phụ thuộc nội dung di chúc: con chưa thành niên, cha, mẹ, vợ/chồng, con thành niên mất khả năng lao động — hưởng ít nhất 2/3 suất theo pháp luật. Không áp dụng cho người từ chối hoặc không được quyền hưởng. | Chỉ có nghĩa khi có di chúc → `wills_not_supported`. |
| 649 | Thừa kế theo pháp luật: theo hàng, điều kiện, trình tự luật định. | Phạm vi engine. |
| 650 | Áp dụng khi: không có di chúc; di chúc không hợp pháp; người thừa kế theo di chúc chết trước/cùng lúc; người được chỉ định không có quyền hưởng hoặc từ chối; phần không định đoạt. | Engine giả định không có di chúc. |
| 651 | Hàng 1: vợ, chồng, cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi, con đẻ, con nuôi. Hàng 2: ông bà nội/ngoại, anh chị em ruột, cháu ruột (người chết là ông/bà). Hàng 3: cụ nội/ngoại, bác/chú/cậu/cô/dì ruột, cháu ruột (người chết là bác/chú/cậu/cô/dì), chắt ruột (người chết là cụ). Cùng hàng hưởng **bằng nhau**. Hàng sau chỉ hưởng khi hàng trước không còn ai do đã chết, không có quyền hưởng, bị truất quyền hoặc từ chối. | Engine chỉ tính hàng 1 (`second_order_required`). |
| 652 | **Thế vị:** con chết **trước hoặc cùng thời điểm** người để lại di sản → cháu hưởng phần cha/mẹ cháu lẽ ra được hưởng nếu còn sống; cháu cũng chết trước/cùng lúc → chắt hưởng. | §6; dừng ở chắt (D-012). |
| 653 | Con nuôi và cha/mẹ nuôi thừa kế của nhau, đồng thời áp dụng Điều 651, 652. | Cần loại quan hệ đẻ/nuôi; Q-004. |
| 654 | Con riêng và bố dượng/mẹ kế chăm sóc, nuôi dưỡng nhau như cha con, mẹ con thì thừa kế của nhau, áp dụng Điều 652, 653. | Chưa biểu diễn; Q-004. |
| 655 | Vợ/chồng đã chia tài sản chung khi hôn nhân còn tồn tại, đang xin ly hôn hoặc đã được ly hôn nhưng bản án/quyết định chưa có hiệu lực, hoặc đã kết hôn với người khác sau khi người kia chết — **vẫn được thừa kế**. | Q-003. |
| 656 | Họp mặt người thừa kế; thoả thuận phải lập **thành văn bản**. | Cơ sở của `giữ phần`/`nhường phần` (D-008); Q-008. |
| 658 | Thứ tự ưu tiên thanh toán (chi phí mai táng, cấp dưỡng, …, tiền phạt, chi phí khác). | Ngoài phạm vi engine. |

## 3. Chuyển tiếp và thế vị — hai việc khác nhau

Xét X chết, con là C.

| Tình huống | Tên | Hệ quả |
|---|---|---|
| C chết **sau** X (kể cả chết sau một ngày) | **Chuyển tiếp** (thừa kế nối tiếp) | C đã hưởng phần của mình tại lúc X chết (613, 614). Phần đó vào **di sản của C**; khi C chết mở **vòng di sản mới** của C; vợ/chồng, cha mẹ, con của C là hàng 1 của vòng đó (651). |
| C chết **trước** hoặc **cùng thời điểm** X, hoặc không xác định được thứ tự | **Thế vị** (652, 619) | C không hưởng. Con của C (cháu X) hưởng phần C lẽ ra được hưởng. Vợ/chồng của C **không** nhận phần thế vị. |

Ví dụ Q01 của brainstorm: C chết sau X → chuyển tiếp, mở di sản của C, không phải
thế vị. Đã đưa vào D-010.

## 4. HNGĐ 2014 — tài sản chung vợ chồng

| Điều | Nội dung (tóm tắt) | Áp vào app |
|---|---|---|
| 33 | Tài sản chung: tài sản tạo ra, thu nhập trong thời kỳ hôn nhân (kể cả hoa lợi, lợi tức từ tài sản riêng), được thừa kế/tặng cho chung, tài sản thoả thuận là chung. QSDĐ có sau khi kết hôn là tài sản chung, trừ được thừa kế riêng, tặng cho riêng hoặc có từ giao dịch bằng tài sản riêng. Là sở hữu chung **hợp nhất** (k2). Không chứng minh được là riêng thì **coi là chung** (k3). | Mặc định đất trong hôn nhân là chung → hai vợ chồng cùng là Chủ. Q-001. |
| 34 | Giấy chứng nhận tài sản chung ghi tên cả hai vợ chồng (trừ thoả thuận khác). | Căn cứ đọc chủ sở hữu từ sổ. |
| 43 | Tài sản riêng: có trước hôn nhân, được thừa kế/tặng cho riêng, chia riêng theo Điều 38–40, đồ dùng cá nhân thiết yếu, tài sản hình thành từ tài sản riêng. | Một Chủ duy nhất. |
| 59 | Ly hôn: tài sản chung chia đôi, có tính các yếu tố luật định. | Ngoài phạm vi. |
| 65 | Hôn nhân chấm dứt từ thời điểm vợ/chồng chết. | Vòng di sản sau đó không còn quan hệ hôn nhân với người chết. |
| 66 | Một bên chết: bên còn sống quản lý tài sản chung. Khi chia di sản, tài sản chung **chia đôi** (trừ thoả thuận chế độ tài sản); **nửa của người chết** chia theo pháp luật thừa kế. Bên còn sống có thể yêu cầu hạn chế phân chia (k3). | Quy ước chia đều giữa các Chủ trùng với chia đôi khi chỉ có hai vợ chồng (D-017). |

## 5. Điểm chưa xác minh

- Điều khoản chuyển tiếp áp dụng luật cũ (BLDS 2005/1995) cho thừa kế mở trước
  01/01/2017 — chưa đọc (Q-002).
- Hôn nhân không đăng ký (sống chung trước 03/01/1987 vẫn công nhận theo Nghị
  quyết 35/2000/QH10) — chưa đọc văn bản, chỉ là hiểu biết chung (Q-003).
- Toàn văn 619–658 đọc từ bản sao luatvietnam vì thuvienphapluat/vbpl chặn tải
  toàn văn; cần đối chiếu lại với vbpl.
