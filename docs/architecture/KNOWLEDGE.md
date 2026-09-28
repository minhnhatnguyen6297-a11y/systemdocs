# Tri thức dự án: tìm quyết định và giữ lại “tại sao”

**Tra cứu quyết định đã kiểm kê:** [DECISION_INDEX.md](DECISION_INDEX.md) — phân biệt
kết luận, lý do đã viết và lời giải thích gốc của owner.

**Trạng thái:** quy tắc tra cứu và ghi nhận đang áp dụng từ MIN-134 (28/09/2026).
Trang này chỉ đường đến nguồn có thẩm quyền; nó không thay thế spec nghiệp vụ,
contract hoặc issue Linear.

> Giữ lại phần "Tại sao?" cho các quyết định, mỗi lần tôi giải thích - là 1 chi
> tiết tinh tế, kiến thức ngách của ngành mà không hệ thống hoặc tài liệu chung
> chung nào nhắc tới, không nên để những kinh nghiệm, đúc kết đó mất đi.
>
> — Owner, yêu cầu MIN-134 ngày 28/09/2026.

## Tìm ở đâu?

| Câu hỏi | Nguồn cần mở trước | Giữ “tại sao” ở đâu? |
|---|---|---|
| Việc nào đang làm, đã nghiệm thu chưa? | Issue Linear; `.agent/tasks/<ID>/` chỉ là nhật ký thực thi | Issue/comment gốc; `decisions.md` của task dẫn lại nguồn |
| Quy tắc nghiệp vụ của một loại hồ sơ? | `notary_v2/docs/domains/<nghiệp-vụ>/` hoặc tài liệu module sở hữu | Mục `decisions/` của domain nếu quyết định có đánh đổi; spec dẫn tới bản ghi đó |
| Cơ chế dùng chung trong một module? | `notary_v2/docs/platform/`, `upload_lab/docs/`, hoặc docs của module sở hữu | Bản ghi quyết định trong docs của module đó |
| Định danh và dữ liệu trao đổi giữa module? | `contracts/`; xem thêm `docs/architecture/SYSTEM_ARCHITECTURE.md` về owner dữ liệu | Quyết định kiến trúc/contract liên quan, có link hai chiều |
| Giao diện chung? | `docs/product/ui/README.md` → `DESIGN.md`, `EXPERIENCE.md`, `tokens.json` | Quyết định và nguồn duyệt mà các file này dẫn tới |
| Ranh giới hệ thống hoặc công nghệ? | `docs/architecture/` và `OPEN_DECISIONS.md` | Bản ghi quyết định cấp hệ thống hoặc mục đã chốt trong `OPEN_DECISIONS.md` |
| Chương trình hiện chạy thế nào? | Source code và test ở đúng revision | Code chứng minh hiện trạng; lý do chọn hành vi phải tra spec/quyết định, không đoán từ code |

`README.md` và README trong từng module là cửa vào. Bản nháp, mockup, task log,
issue đã hủy và ADR `Superseded` vẫn là bằng chứng lịch sử; trạng thái của chúng
phải được đọc trước khi dùng làm quy tắc hiện hành. Khi hai nguồn mâu thuẫn,
đối chiếu owner, phạm vi, trạng thái và nguồn duyệt; không chọn tự động bản có
ngày mới nhất. Với hành vi nội bộ, tài liệu của module sở hữu thắng tài liệu
cấp cha theo `AGENTS.md`, rồi sửa chỗ cấp cha bị lệch.

## Ghi một quyết định để không mất kinh nghiệm ngành

1. **Ghi kết luận và lời giải thích gốc tách nhau.** Nếu owner nói rõ lý do,
   chép nguyên ý, giữ ví dụ, trường hợp ngoại lệ và giới hạn. Có thể viết thêm
   bản diễn giải cho agent, nhưng không thay thế lời gốc bằng bản tóm tắt.
2. **Ghi nguồn có thể tìm lại.** Dẫn issue/comment Linear, file và mục, hoặc
   trích lời owner kèm ngày và ngữ cảnh. Chỉ ghi “owner đã nói” là chưa đủ.
3. **Ghi phạm vi và trạng thái.** `Đề xuất`, `Đã chốt`, `Đã thay thế` là ba trạng
   thái khác nhau. Ghi quyết định nào bị thay thế và điều kiện nào khiến cần
   hỏi lại. Không lấy một quyết định cho hồ sơ thừa kế áp sang loại hồ sơ khác.
4. **Đặt ở đúng chủ sở hữu.** Quy tắc nghiệp vụ vào docs của domain; cách trao
   đổi giữa module vào contract; lý do kiến trúc xuyên sản phẩm vào
   `docs/architecture/`. `decisions.md` của task ghi diễn biến rồi dẫn tới nơi
   lưu lâu dài. Không tạo thêm một “sổ quyết định” thứ hai có quyền khác.
5. **Thiếu lý do thì nói là thiếu.** Ghi `Tại sao: Chưa có lời giải thích được
   xác nhận` và dẫn điều đã biết. Khi thay đổi có thể làm sai nghiệp vụ, hỏi
   owner trước; không suy ra lý do từ tên cột, giao diện, code hoặc AI.

Nếu owner giải thích một kinh nghiệm **chưa dẫn tới quyết định**, giữ nguyên lời
giải thích trong issue/comment Linear liên quan và dẫn lại trong task đang làm.
Đánh dấu `Chưa chốt`; khi đã xác nhận phạm vi áp dụng, chuyển nó vào tài liệu
nghiệp vụ của module sở hữu. Không ép kinh nghiệm đó thành một quy tắc đã duyệt.

Khung ngắn để ghi trong `decisions/` của đúng nơi sở hữu:

```markdown
# <ID> — <câu hỏi/quyết định>

- Trạng thái: Đề xuất | Đã chốt | Đã thay thế
- Phạm vi: <loại hồ sơ, module, phiên bản>
- Người chốt / ngày: <ai, khi nào>
- Nguồn gốc: <link issue/comment hoặc tài liệu + mục>
- Thay thế / bị thay thế bởi: <link nếu có>

## Quyết định
<Điều được chọn và ranh giới áp dụng.>

## Tại sao? — lời giải thích gốc
> <Giữ cách diễn đạt, ví dụ và ngoại lệ của owner; nếu chưa có, ghi rõ là chưa có.>

## Cách áp dụng
<Hệ quả cho dữ liệu, giao diện, Word, kiểm thử; dẫn spec/contract tương ứng.>

## Phương án khác và khi nào xem lại
<Chỉ ghi phương án và lý do loại nếu thật sự có nguồn; điều kiện làm quyết định đổi.>
```

**Ví dụ đã có nguồn:** Quyết định B1 trong
[`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) ghi rằng văn phòng có phần mềm quản lý
hồ sơ nhưng không có API lấy dữ liệu. Mục “B1 — vì sao `upload_lab` tồn tại”
giữ lý do ngành cụ thể: phải trích dữ liệu từ file Word chuyên viên đã soạn.
Khi viết story liên quan đến nguồn dữ liệu của Upload Lab, dẫn tới mục B1 này;
không rút gọn thành “đọc Word vì tiện” hoặc đề xuất lại việc đọc API của phần
mềm cũ khi chưa có bằng chứng tình hình đã thay đổi.

## Tra cứu trước khi sửa

Từ câu hỏi nghiệp vụ, mở README của module rồi tìm đúng khái niệm bằng `rg -n`.
Đọc mục tìm được cùng trạng thái tài liệu, lần theo link nguồn và issue Linear.
Nếu chưa tìm thấy lời giải thích, ghi khoảng trống trong task đang làm; khi owner
giải thích, lưu lại theo khung trên ngay trong lượt làm việc đó. Chỉ lập chỉ mục
tìm kiếm hoặc RAG từ các nguồn đã phân quyền và phân trạng thái rõ ràng.
