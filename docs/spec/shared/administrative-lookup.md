# Lõi tra cứu tên đơn vị hành chính — TASK-2

**Trạng thái:** Owner duyệt 05/10/2026, runtime chưa đáp ứng · **Phạm vi:** dùng chung toàn hệ thống ·
**Nguồn quyết định:** Owner, brainstorm 05/10/2026 —
[TASK-2](../../../backlog/tasks/task-2%20-%20Brainstorm-Muc-5-Loi-tra-cuu-thay-doi-ten-don-vi-hanh-chinh-dung-chung.md),
[memlog](../../../_bmad-output/brainstorming/brainstorm-tra-cuu-don-vi-hanh-chinh-2026-10-05/.memlog.md).

## 1. Công dụng và Tại sao?

Trả lời một câu: **tên xã/tỉnh người dùng gõ (cũ hoặc mới) nay là đơn vị nào,
gồm những đơn vị cũ nào.**

| Việc | Người dùng có | Cần nhận | Tần suất |
|---|---|---|---|
| A | Địa chỉ cũ đủ xã/huyện/tỉnh | Tên hiện hành | ~85% |
| B | Chỉ tên xã cũ (đã biết tỉnh mới) | Tên xã hiện hành, một lần tra | ít |
| C | Tên xã mới | Các xã cũ đã gộp/tách thành nó | ít |

Không làm: suy đoán, sửa ô nhập, tra thôn, tra huyện, dựng lịch sử.

**Tại sao dùng chung:** ô địa chỉ khi soạn hồ sơ, tool tra cứu riêng và module
khác về sau cần cùng một câu trả lời. Một luật + một kho → không lệch giữa các
nơi. Đây là ngoại lệ có chủ ý của luật "chưa tạo shared core khi chưa đủ hai
consumer" tại [spec hệ thống](../README.md#đã-chốt).

## 2. Nguyên lý

1. **Chỉ phản ánh DB.** Có dữ liệu → xuất; không có → không có. Engine không
   suy cấp, không đoán đơn vị, không ghép lịch sử. *Tại sao:* gợi ý sai mất
   lòng tin hơn nhiều gợi ý đúng; quan hệ tách/gộp/tách-gộp liên tục là việc
   của kho, không của engine.
2. **Chỉ đúng hoặc sai.** Đúng = ít nhất một kết quả. Sai = không trả gì; không
   trả nửa kết quả kiểu "đã hiểu tỉnh X, chưa hiểu cụm Y". *Tại sao:* nửa kết
   quả dễ bị chép như kết quả thật.
3. **Không cần ngày.** Không có `source_date`/`target_date`. *Tại sao:* lõi chỉ
   trả bước cuối; bắt ngày đang chặn ca chỉ gõ tên xã (DC-01) và khiến máy đoán
   cấp theo ngày (DC-04).
4. **Tiêu chí hoàn thành = đúng bước cuối:** đơn vị hiện hành và các đơn vị liền
   trước nó. Phủ ~90% ca. Không cố truy lịch sử nhiều đời.

## 3. Cấp được tra

| Cấp | Tra? | Tại sao |
|---|---|---|
| Xã/phường/thị trấn, cũ và mới | Có | Trục chính, khó tra nhất |
| Tỉnh, cũ và mới | Có | Cùng dạng kết quả với xã |
| Huyện | Không, luôn "không có" | Kho không có danh mục huyện; Bando chỉ ghi huyện trong ngoặc |
| Thôn/xóm | Không | Chưa có dữ liệu tổng hợp |

## 4. Dữ liệu dùng

Nguồn duy nhất: [kho timeline](../notary_v2/administrative-timeline.md) (owner
dữ liệu hiện là `notary_v2`). Mỗi đơn vị hiện hành dùng: tên chính thức có tiền
tố, tỉnh cha (với xã), **đoạn chữ gốc "sáp nhập từ" của Bando nguyên văn**, ID
dòng nguồn, `dataset_version`, `revision`.

**MVP tra thẳng trên tên + đoạn chữ gốc; không tách đoạn chữ thành từng xã cũ.**
*Tại sao:* Bando chỉ lưu xã mới thành trường; xã cũ là một đoạn văn kèm ghi chú
như `(quận Hà Đông)`, `(phần còn lại sau khi sáp nhập vào phường Đại Mỗ)`. Tách
dễ sai; đoạn gốc đã tự nói gộp toàn bộ hay một phần.
Owner chấp nhận: cụm có thể khớp vào ghi chú trong ngoặc, ví dụ `phường Đại Mỗ`
ra cả dòng phường Hà Đông.

Tỉnh cũ chỉ nằm trong đoạn chữ của tỉnh mới, nên khớp `tỉnh Nam Định` = phạm vi
tỉnh Ninh Bình. Không cần bảng tỉnh cũ riêng.

Kết quả phải cùng một phiên bản kho: tên trả về lấy từ đúng bản đang hoạt động
(DC-08 là lỗi hiện có, ngoài luật tra). Kho mới lỗi → báo lỗi kho, không trả
kết quả cũ dưới nhãn mới. Bổ sung/sửa lịch sử theo spec timeline.

## 5. Chuẩn hóa đầu vào

- **Tách cụm** theo `,` và `-`. Bỏ cụm rỗng.
- **Viết tắt:** danh mục cố định chỉ đổi viết tắt → tiền tố đầy đủ: `X.`→Xã,
  `P.`→Phường, `TT.`→Thị trấn, `TP.`/`TP`→Thành phố, `H.`→Huyện, `Q.`→Quận,
  `TX.`→Thị xã. Danh mục thêm mục = sửa spec.
- **Giữ tiền tố đầy đủ** (`xã`, `phường`, `thị trấn`, `tỉnh`…). *Tại sao:* tiền tố
  là một phần tên chính thức trong DB. Giữ nó thì `xã Yên Bình` không lẫn
  `Phường Yên Bình` (DC-02), `thôn Yên Bình` không khớp `Xã Yên Bình`.
  `Thị trấn Lâm` → ít kết quả; `Lâm` → hàng trăm.
- **Hoa/thường:** không phân biệt.
- **Dấu:** cụm có dấu → so có dấu. Cụm hoàn toàn không dấu → bỏ dấu phía DB rồi
  so (`yen binh` ra cả `Yên Bình`, `Yến Bình`).
- **Số:** không quy đổi `1`/`01`/`I`. DB ghi ký tự nào thì tìm ký tự đó; sai thì
  người dùng gõ lại.

## 6. Luật khớp

Cụm sau chuẩn hóa phải **nằm nguyên vẹn, liên tiếp, đúng thứ tự** trong tên hoặc
đoạn chữ gốc. Không chèn, không cắt ký tự.

| Gõ `yên bình` | Khớp? |
|---|---|
| `Xã Yên Bình`, `Phường Yên Bình`, `Xã Yên Bình Đông` | Có |
| `Xã Bình Yên`, `Xã Yên Thịnh Bình` | Không |

Tên thật có `-` (`Bà Rịa - Vũng Tàu`) bị tách thành hai cụm; `Vũng Tàu` vẫn khớp
tên đầy đủ. Mảnh còn lại nếu khớp đơn vị khác thì thêm dòng, người dùng tự chọn.

## 7. Flow — đọc từ phải sang trái

1. **Cụm cuối** so với các dòng **tỉnh** bằng đúng luật khớp mục 6. Khớp →
   phạm vi = mọi tỉnh khớp (một hay nhiều, không luật riêng). Không khớp →
   phạm vi = toàn quốc, cụm cuối được xét như cụm còn lại ở bước 2. Cụm ngắn
   như `Hà` khớp nhiều tỉnh → nhiều kết quả → luật >10 của mục 8 (popup hỏi
   chuyển sang tool). *Tại sao:* một luật nhất quán, không thêm ngoại lệ (Owner 05/10).
2. **Mỗi cụm còn lại** so với các dòng **xã trong phạm vi**; gom mọi dòng khớp,
   bỏ trùng.
   - Cụm có tiền tố cấp huyện (`Huyện`, `Quận`, `Thị xã`; `Thành phố` khi không
     là cụm cuối) → bỏ qua có chủ đích, không là lỗi. *Tại sao:* giấy cũ (ca A)
     gần như luôn có huyện; huyện không tra được nhưng không được làm hỏng ca.
   - Cụm không khớp (thôn, số nhà, rác) → không góp kết quả; **không dừng**.
3. Không còn cụm nào ngoài cụm tỉnh → kết quả cấp tỉnh.
4. 0 kết quả → **sai**.

Engine không có chế độ "đảo thứ tự" riêng; chỉ chạy các bước trên.
Không có tiền tố, máy có thể ra cả xã mới lẫn xã cũ cùng chữ: `Yên Bình, Ý Yên,
Nam Định` → dòng xã Ý Yên và dòng chứa Xã Yên Bình; người dùng chọn.

## 8. Kết quả

**Lõi luôn trả đủ dữ liệu có cấu trúc** (mục 4). Nơi gọi chỉ chọn **kiểu trình
bày**; lõi không biết feature nào gọi. *Tại sao:* thêm nơi gọi không sửa lõi.

| Kiểu | Nơi dùng | Dạng mỗi dòng |
|---|---|---|
| `full` | Tool tra cứu riêng | `Xã Ý Yên = <đoạn chữ gốc>, Tỉnh Ninh Bình` |
| `drafting` | Trình soạn thảo | `xã Ý Yên, tỉnh Ninh Bình` |

- Mỗi dòng một đơn vị **hiện hành**; trùng tên → nhiều dòng (khác tỉnh).
- Tra tên mới hay tên cũ đều cùng dạng; không gắn nhãn chiều cũ→mới.
- `drafting`: danh từ chung (`xã`, `phường`, `tỉnh`…) viết thường, tên riêng viết
  hoa, theo thể thức NĐ 30/2020. Owner bỏ bước xác minh văn bản gốc (05/10).
- `drafting` quá **10** kết quả → không hiện dòng nào; hiện popup
  **"Nhiều kết quả khớp. Xem đầy đủ?"**. Người dùng bấm đồng ý mới mở tool tra
  cứu (`full`) với cùng chuỗi; bấm hủy thì ở lại ô soạn thảo.
- Tool tra cứu mở dạng **popup đè lên màn hình đang làm**, không chuyển màn
  hình. Đóng popup → về đúng chỗ cũ; nội dung đang nhập, nháp chưa lưu, vị trí
  con trỏ giữ nguyên. Copy từ popup rồi dán vào ô như bình thường.
- *Tại sao:* danh sách dài không đọc được ở ô soạn thảo; hiện 10 dòng đầu là
  nửa kết quả; chuyển màn hình làm mất việc người dùng đang làm dở (Owner 05/10,
  thay quyết định "chuyển thẳng").

## 9. Thao tác — mọi nơi gọi

- **Chỉ tra khi người dùng bấm nút Tra.** Không tự tra khi gõ, dán, rời ô, trỏ
  chuột hay mở hồ sơ. *Tại sao:* tra tự động trả kết quả liên tục, lệch với
  thao tác, mỗi lần nhìn một khác; bấm nút thì không có truy vấn thừa.
- **Kết quả copy được; máy không tự ghi, đè hay nối `(nay là …)` vào ô.**
  Người dùng tự quyết. Đây là câu trả lời Q3 của báo cáo điều tra cho phần tra
  cứu.
- Phản hồi về khi chuỗi/ô đã đổi → bỏ.
- Chỉ đọc kho cục bộ; không gửi địa chỉ khách hàng ra website.

## 10. Ví dụ đầu vào → cách hiểu

Ví dụ minh họa luật; kết quả thật phụ thuộc dữ liệu kho.

| Gõ | Máy hiểu | Trả |
|---|---|---|
| `xã YÊn Bình` | 1 cụm, không phải tỉnh → toàn quốc | Mọi đơn vị hiện hành có tên/đoạn gốc chứa `xã yên bình`; mỗi tỉnh một dòng |
| `Yên Bình` | Không tiền tố → cả xã, phường, `Yên Bình Đông`… | Nhiều dòng; `drafting` >10 → popup "Nhiều kết quả khớp. Xem đầy đủ?" |
| `yen binh` | Không dấu → so bỏ dấu | Thêm `Yến Bình`… |
| `P. Yên Bình` | `P.` → `Phường` | Chỉ dòng chứa `phường yên bình` |
| `tỉnh Nam Định` | Khớp đoạn gốc tỉnh Ninh Bình; không còn cụm | `tỉnh Ninh Bình` |
| `huyện Ý Yên` | Cấp huyện, bỏ qua; 0 kết quả | Sai |
| `xã Yên Bình, tỉnh Nam Định` | Phạm vi Ninh Bình | Dòng xã hiện hành chứa Xã Yên Bình trong Ninh Bình |
| `Thôn A, xã Yên Bình, huyện Ý Yên, tỉnh Nam Định` | Tỉnh → Ninh Bình; huyện bỏ qua; `Thôn A` không khớp | Như dòng trên |
| `Yên Bình, Ý Yên, Nam Định` | Ninh Bình; cả hai cụm đều khớp | Xã Ý Yên + dòng chứa Xã Yên Bình |
| `Phường 01` | Không quy đổi | Chỉ khớp nếu DB ghi `01` |
| `abc, xyz` | Không cụm nào khớp | Sai |

## 11. Phạm vi MVP (MoSCoW, Owner chốt 05/10)

- **Must:** mục 2–9, gồm tool tra cứu riêng dạng `full` (Owner chuyển từ
  Should 05/10 vì luật >10 của `drafting` cần nơi để chuyển tới).
- **Could:** nút "Chi tiết" hiện JSON/timeline lịch sử nhiều đời khi kho có;
  thêm ký tự ngăn cách dự phòng ngoài `,` `-`.
- **Won't (lần này):** tra huyện → tỉnh; dữ liệu thôn; tách đoạn gốc thành
  trường riêng; tự tra khi gõ/bong bóng gợi ý; chặn tra lại chuỗi không đổi.

## 12. Hiện trạng runtime/contract — đích chưa đáp ứng

Code là hiện trạng, không là hành vi đích. Khi triển khai phải sửa:

- Contract đích: `notary.address-lookup.v2` tại
  [§14 contract](../../../contracts/notary-case-drafting.md) +
  [schema v2](../../../contracts/notary-case-drafting/address-lookup.v2.schema.json)
  (Owner duyệt 05/10). Runtime còn trả v1
  ([schema v1](../../../contracts/notary-case-drafting/address-lookup.schema.json):
  bắt hai ngày, tách xã+tỉnh, `coverage`) → trái mục 2, 7, 8.
- [`administrative_address.py`](../../../notary_v2/services/administrative_address.py):
  bỏ tiền tố khi so (DC-02), đoán cấp theo mốc 01/07/2025 (DC-04), tách tên cũ
  bằng regex `predecessor_names`, `apply_address` nối `(nay là …)` (DC-03),
  chọn tên theo bản observed cuối (DC-08).
- [`administrative_timeline.py`](../../../notary_v2/administrative_timeline.py):
  cờ "một phần" gắn cho cả dòng — MVP không dùng, đoạn gốc tự hiện ghi chú.
- Renderer chỉ gửi khi đủ địa chỉ + hai ngày; nơi niêm yết lấy địa chỉ tài sản
  (DC-01, DC-05).

## 13. Còn mở

- Danh mục viết tắt đầy đủ và ký tự ngăn cách dự phòng.
- Vị trí nút Tra và bố cục bên trong popup tool tra cứu.
- Contract cho module ngoài `notary_v2` gọi lõi.
- Nguồn dữ liệu huyện (Won't hiện tại).

## 14. Lịch sử

Owner 05/10/2026 thay các quy tắc Draft cũ tại
[`notary_v2/administrative-address.md`](../notary_v2/administrative-address.md):
bắt ngày giấy/ngày lập hồ sơ, bắt xã+tỉnh, nối `(nay là …)` khi áp dụng, gợi ý
nơi niêm yết theo tài sản nguồn. Bằng chứng lỗi: mục 5 của
[báo cáo điều tra 04/10](../../../.agents/review-plan-20261004/investigation-report.md).
