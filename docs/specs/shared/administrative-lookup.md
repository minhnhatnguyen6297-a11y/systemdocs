# Lõi tra cứu tên đơn vị hành chính — TASK-2

**Trạng thái:** Owner duyệt 05/10/2026; runtime v2 đã nghiệm thu TASK-3/TASK-4 ngày 06/10/2026 · **Phạm vi:** dùng chung toàn hệ thống ·
**Nguồn quyết định:** Owner, brainstorm 05/10/2026 —
[TASK-2](../../archive/backlog/tasks/task-2%20-%20Brainstorm-Muc-5-Loi-tra-cuu-thay-doi-ten-don-vi-hanh-chinh-dung-chung.md),
[memlog](../../../docs/brainstorming/brainstorm-tra-cuu-don-vi-hanh-chinh-2026-10-05/.memlog.md).

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
| Huyện | Không có đơn vị cấp huyện trong kết quả | Kho không có danh mục huyện; Bando chỉ ghi huyện trong ngoặc — nhưng cụm `quận Hà Đông` vẫn khớp đoạn gốc của xã/tỉnh và in ra các xã đó (mục 7) |
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

Tỉnh cũ nằm trong đoạn chữ của tỉnh mới, nên `tỉnh Nam Định` có thể khớp dòng
tỉnh Ninh Bình. Đây là một dòng kết quả độc lập, không giới hạn phạm vi tra
các cụm khác vào tỉnh đó (mục 7). Không cần bảng tỉnh cũ riêng.

Kết quả phải cùng một phiên bản kho: tên trả về lấy từ đúng bản đang hoạt động
(DC-08 là lỗi hiện có, ngoài luật tra). Kho mới lỗi → báo lỗi kho, không trả
kết quả cũ dưới nhãn mới. Bổ sung/sửa lịch sử theo spec timeline.

**Nhiều dòng nguồn:** trong bản dữ liệu đang hoạt động, một đơn vị có nhiều
dòng nguồn thì tra và trả từng dòng khớp, giữ nguyên đoạn chữ và bằng chứng
của dòng đó. Không chọn hộ, nối các đoạn nguồn hay báo lỗi chỉ vì có nhiều
dòng. *Tại sao:* đây là công cụ truy vấn kho; người dùng xem dữ liệu và tự
chọn (Owner chốt 05/10/2026).

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
- **Unicode:** chuẩn hóa NFC trước khi so để hai cách mã hóa cùng một chữ có
  dấu cho cùng kết quả (ví dụ chữ `ế` dựng sẵn và chữ ghép dấu).
- **Dấu:** cụm có dấu → so có dấu. Cụm hoàn toàn không dấu → bỏ dấu phía DB rồi
  so (`yen binh` ra cả `Yên Bình`, `Yến Bình`); ở phép so không dấu, đổi `đ`/`Đ`
  phía DB thành `d`/`D`. Phép so có dấu giữ phân biệt `d` và `đ`.
  Xác định có dấu từ cụm người dùng nhập sau NFC, trước khi mở rộng viết tắt;
  chữ có dấu do máy thêm (`P.` → `Phường`) không đổi cách so của đầu vào.
  Ví dụ `P. yen binh`: mở rộng tiền tố rồi so hai phía ở dạng không dấu.
- **Số:** không quy đổi `1`/`01`/`I`. DB ghi ký tự nào thì tìm ký tự đó; sai thì
  người dùng gõ lại.

## 6. Luật khớp

Cụm sau chuẩn hóa phải **nằm nguyên vẹn, liên tiếp, đúng thứ tự** trong tên hoặc
đoạn chữ gốc. Không chèn, không cắt ký tự.
So riêng từng trường: không nối tên với đoạn chữ gốc để tạo một chuỗi khớp
vắt qua ranh giới hai trường. *Tại sao:* một cụm như vậy không nằm trong tên
hay đoạn nguồn nào như luật đã chốt.

| Gõ `yên bình` | Khớp? |
|---|---|
| `Xã Yên Bình`, `Phường Yên Bình`, `Xã Yên Bình Đông` | Có |
| `Xã Bình Yên`, `Xã Yên Thịnh Bình` | Không |

Tên thật có `-` (`Bà Rịa - Vũng Tàu`) bị tách thành hai cụm; `Vũng Tàu` vẫn khớp
tên đầy đủ. Mảnh còn lại nếu khớp đơn vị khác thì thêm dòng, người dùng tự chọn.

## 7. Flow — mọi cụm tra độc lập

Engine không phân biệt vị trí hay vai trò của cụm. Dán một đoạn địa chỉ cũ
(thôn, xã, huyện, tỉnh) hay gõ một tên lẻ đều chạy cùng một luật:

1. **Mỗi cụm** so với các dòng **xã** (tên + đoạn chữ gốc) trên **toàn quốc**
   bằng đúng luật khớp mục 6; gom mọi dòng khớp. Một dòng khớp nhiều cụm chỉ
   xuất hiện một lần; các dòng nguồn khác nhau của cùng đơn vị vẫn giữ riêng.
2. **Mỗi cụm** cũng so với các dòng **tỉnh** (tên + đoạn chữ gốc); mọi tỉnh
   khớp in một dòng riêng, **kể cả** khi tỉnh đó đã là tỉnh cha của một xã
   trong kết quả.
3. **Không có luật bỏ qua theo tiền tố, không có phạm vi tỉnh.** Cụm
   `huyện Ý Yên` được tra như mọi cụm — khớp đoạn gốc chứa `(huyện Ý Yên)`
   thì in các xã từng thuộc huyện đó. `quận Hà Đông` → các phường Hà Đông,
   Kiến Hưng… *Tại sao:* engine chỉ phản ánh kho; một luật nhất quán ít lỗi
   hơn ngoại lệ; nhiễu đã có luật >10 của mục 8 lo (Owner 05/10, thay luật
   "đọc phải→trái, cụm cuối khoanh phạm vi tỉnh, bỏ qua cụm huyện").
4. 0 kết quả → **sai**.

Thứ tự hiển thị: các dòng xã trước, các dòng tỉnh sau; trong mỗi nhóm theo
thứ tự kho. Gõ `Yên Bình, Ý Yên, Nam Định` → xã Ý Yên + dòng chứa Xã Yên
Bình + `tỉnh Ninh Bình`; người dùng chọn.

## 8. Kết quả

**Lõi luôn trả đủ dữ liệu có cấu trúc** (mục 4). Nơi gọi chỉ chọn **kiểu trình
bày**; lõi không biết feature nào gọi. *Tại sao:* thêm nơi gọi không sửa lõi.

| Kiểu | Nơi dùng | Dạng mỗi dòng |
|---|---|---|
| `full` | Tool tra cứu riêng | `Xã Ý Yên = <đoạn chữ gốc>, Tỉnh Ninh Bình` |
| `drafting` | Trình soạn thảo | `xã Ý Yên, tỉnh Ninh Bình` |

- Mỗi dòng kết quả gắn với một đơn vị **hiện hành** và một dòng nguồn. Cùng
  `unit_id` có thể xuất hiện nhiều lần khi có nhiều dòng nguồn khớp; mỗi dòng
  giữ `observation_id`, `source_text`, `evidence` riêng. Đơn vị không có đoạn
  nguồn vẫn có thể khớp tên và trả một dòng với `source_text: null`.
- Bỏ lặp theo cùng dòng `(unit_id, observation_id)` khi nhiều cụm cùng khớp;
  không bỏ dòng chỉ vì tên, `unit_id` hoặc `display` giống nhau. Không có
  observation thì dùng một dòng tên của đơn vị. Thứ tự các dòng nguồn cùng
  đơn vị theo thứ tự trong kho. `total` đếm **dòng kết quả**, không đếm số
  `unit_id` khác nhau; ngưỡng 10 áp dụng theo số dòng này.
- Với `full`, mỗi dòng hiện đúng đoạn nguồn của nó để người dùng chọn.
  `drafting` giữ dạng ngắn đã chốt, kể cả khi hai dòng có cùng `display`.
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
| `xã YÊn Bình` | 1 cụm → toàn quốc | Mọi đơn vị hiện hành có tên/đoạn gốc chứa `xã yên bình`; chỉ thêm dòng tỉnh nếu chính dòng tỉnh khớp |
| `Yên Bình` | Không tiền tố → cả xã, phường, `Yên Bình Đông`… | Nhiều dòng; `drafting` >10 → popup "Nhiều kết quả khớp. Xem đầy đủ?" |
| `yen binh` | Không dấu → so bỏ dấu | Thêm `Yến Bình`… |
| `P. Yên Bình` | `P.` → `Phường` | Chỉ dòng chứa `phường yên bình` |
| `tỉnh Nam Định` | Khớp đoạn gốc tỉnh Ninh Bình | `tỉnh Ninh Bình` |
| `huyện Ý Yên` | Cụm thường → khớp `(huyện Ý Yên)` trong đoạn gốc | Các xã từng thuộc huyện Ý Yên |
| `quận Hà Đông` | Như trên | Các phường từng thuộc quận Hà Đông |
| `xã Yên Bình, tỉnh Nam Định` | Hai cụm tra độc lập | Mọi Xã Yên Bình toàn quốc + dòng `tỉnh Ninh Bình` |
| `Thôn A, xã Yên Bình, huyện Ý Yên, tỉnh Nam Định` | Bốn cụm tra độc lập; `Thôn A` không khớp | Như dòng trên + các xã thuộc huyện Ý Yên (có thể >10 → popup) |
| `Yên Bình, Ý Yên, Nam Định` | Ba cụm độc lập | Xã Ý Yên + dòng chứa Xã Yên Bình + `tỉnh Ninh Bình` |
| `Phường 01` | Không quy đổi | Chỉ khớp nếu DB ghi `01` |
| `abc, xyz` | Không cụm nào khớp | Sai |

## 11. Phạm vi MVP (MoSCoW, Owner chốt 05/10)

- **Must:** mục 2–9, gồm tool tra cứu riêng dạng `full` (Owner chuyển từ
  Should 05/10 vì luật >10 của `drafting` cần nơi để chuyển tới).
- **Could:** nút "Chi tiết" hiện JSON/timeline lịch sử nhiều đời khi kho có;
  thêm ký tự ngăn cách dự phòng ngoài `,` `-`.
- **Won't (lần này):** tra huyện → tỉnh; dữ liệu thôn; tách đoạn gốc thành
  trường riêng; tự tra khi gõ/bong bóng gợi ý; chặn tra lại chuỗi không đổi.

## 12. Hiện trạng runtime/contract — đã nghiệm thu TASK-3/TASK-4

Runtime đã chuyển sang `notary.address-lookup.v2`: payload `query` +
`presentation`, mọi cụm tra độc lập vào xã và tỉnh trên toàn quốc, mỗi
dòng nguồn khớp trả riêng để người dùng chọn, không tự tra/không tự
ghi/không nối `(nay là …)`. Schema v1
(`address-lookup.schema.json`) đã xóa; contract §14 và
[schema v2](../../../contracts/notary-case-drafting/address-lookup.v2.schema.json)
là SOT. Renderer đã có nút Tra và overlay full của TASK-4; không tự tra
hoặc áp dụng kết quả. Phần triển khai hiện có chưa đồng nghĩa nghiệm thu.

Lịch sử: runtime từng trả v1 (bắt hai ngày, tách xã+tỉnh, `coverage`,
bỏ tiền tố khi so, đoán cấp theo mốc 01/07/2025, tách tên cũ bằng regex,
nối `(nay là …)`, renderer chỉ gửi khi đủ địa chỉ + hai ngày) → trái mục
2, 7, 8; đã thay toàn bộ tại TASK-3.

Kiểm tra độc lập 05/10/2026 (`docs/archive/removed-agents-files.md`)
tìm thêm 2 lỗi lõi đã sửa xong: raw khớp nhiều observation chỉ trả dòng
đầu (R1); tên/tỉnh cha lấy bản ghi cũ nhất thay vì đúng version (R2).
Sau sửa: kiểm importer thật hai snapshot (đổi tên + tỉnh cha), raw khớp
2/11 dòng, ngưỡng `too_many` đếm dòng — pytest 211 pass/3 skip.

Review tiếp tìm lỗi đơn vị đã mất khỏi catalog mới, thứ tự dòng nguồn và
xã thiếu tỉnh. Đã sửa/kiểm lại 06/10: ID phiên bản importer phân biệt lịch sử
với đơn vị tên-only hợp lệ; xuất nguồn theo thứ tự kho; không phát found sai schema.
*Tại sao:* đáp ứng mục 4, 7, 8 và contract hiện có; không thêm luật tra.
Python 294 đạt/2 bỏ qua symlink, npm 403 đạt, examples 82/0; kiểm bỏ sửa
trong bộ nhớ bắt lỗi cũ. Producer frozen với kho public và component Word
trên Electron thật đã kiểm, gồm full 3.001 dòng, clipboard và lỗi snapshot.
[Kết quả nghiệm thu](../../../docs/archive/removed-agents-files.md);
[review trước sửa](../../../docs/archive/removed-agents-files.md) giữ làm lịch sử.

## 13. Còn mở

- Mở rộng danh mục viết tắt hoặc ký tự ngăn cách ngoài danh mục cố định mục 5
  là việc sau MVP; không phải điều kiện chặn TASK-3.
- Bố cục TASK-4 đã chốt tại [spec nơi gọi](../notary_v2/administrative-address.md).
- Contract cho module ngoài `notary_v2` gọi lõi.
- Nguồn dữ liệu huyện (Won't hiện tại).
- `drafting` >10: vì kết quả giờ gồm cả các cụm huyện khớp, ca dán địa chỉ cũ
  đầy đủ dễ vượt 10 → popup/tool phải đọc được số lượng lớn.

## 14. Lịch sử

Owner 05/10/2026 chốt nhiều dòng nguồn: “in dữ liệu ra, chọn dòng nào là việc
của user”, vì đây là tool truy vấn database. Thay đề xuất báo lỗi kho và
quy tắc bỏ trùng theo đơn vị: giữ các dòng nguồn khớp riêng, chỉ bỏ cùng dòng
bị tìm thấy lặp lại qua nhiều cụm. Không thêm cơ chế xét đúng/sai giữa các nguồn.

Owner 05/10/2026, sau khi quan sát hành vi Bando (`quận hà đông` ra các xã
từng thuộc quận; `phường linh đàm, tỉnh nam định` trả xã và tỉnh độc lập),
thay mục 7: bỏ luật đọc phải→trái, bỏ phạm vi tỉnh và luật bỏ qua cụm huyện;
mọi cụm tra độc lập vào xã lẫn tỉnh, tỉnh khớp luôn in dòng riêng. Lý do:
luật nhất quán, ít lỗi hơn; tiền tố huyện chỉ là chữ trong đoạn gốc.

Owner 05/10/2026 thay các quy tắc Draft cũ tại
[`notary_v2/administrative-address.md`](../notary_v2/administrative-address.md):
bắt ngày giấy/ngày lập hồ sơ, bắt xã+tỉnh, nối `(nay là …)` khi áp dụng, gợi ý
nơi niêm yết theo tài sản nguồn. Bằng chứng lỗi: mục 5 của
[báo cáo điều tra 04/10](../../../docs/archive/removed-agents-files.md).
