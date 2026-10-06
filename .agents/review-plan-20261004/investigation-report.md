# Ghi nhận điều tra Word, trích xuất hợp đồng và địa chỉ — 04/10/2026

**Báo cáo lịch sử tại các mốc code ghi ở mục 1, không phải spec/plan có hiệu lực hiện tại.** Báo cáo phục vụ task review cũ [TASK-2 đã lưu trữ](../../backlog/archive/tasks/task-2%20-%20Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md). Owner sau đó yêu cầu hoàn tác spec/plan: xem [WITHDRAWN](WITHDRAWN.md). Các mục 3–11 giữ bằng chứng và diễn giải lúc review; câu nói “đã ghi vào spec” ở dưới là lịch sử, không khẳng định spec hiện tại đã chứa yêu cầu đó. Trạng thái và các task/spec/plan hiện dùng tại [bàn giao 05/10](../handoff/notary-20261005/README.md).

**Đính chính của người dùng, 04/10/2026:** “lỗi nhầm trường tôi report trước đó là chưa đúng, tôi nhìn nhầm”. Rút nghi vấn nhầm dữ liệu địa chỉ/nơi cấp khỏi danh sách lỗi. Nội dung NG-01 bên dưới chỉ giữ lịch sử đính chính, không là đầu việc sửa.

Bước đầu chỉ đọc và ghi bằng chứng. Sau yêu cầu tiếp theo của Owner, đã review, ghi các yêu cầu đã rõ vào spec và lập plan giao agent khác. Chưa sửa code sản phẩm, schema, contract hay mẫu Word; không ghi vào database hồ sơ thật. Các phép thử dùng dữ liệu tự dựng, thư mục tạm và database trong bộ nhớ.

## 1. Bản được kiểm tra và yêu cầu đối chiếu

- Worktree: `C:\Users\MINH\.codex\worktrees\1aae\systemdocs`.
- Code đích review: 19 commit đến `53c7804cf8d9d50843340772366bf7e7e3b7cdb8`. HEAD worktree lúc lập plan: `fe71917820665f17bb3e2209b9dcfb51ab28dd05`; phần mới sau đích review là luật làm việc và khởi tạo Backlog, không thay runtime.
- So với `consolidate/monorepo`, mốc chung `6c07d89a65d4a62cdddee8ba40d25903c6139f18`: 19 commit, 151 file, 539.277 dòng thêm, 804 dòng xóa. `ledger.json` chiếm 516.486 dòng thêm; còn 35 snapshot thô.
- Có sẵn chỉnh sửa chưa commit tại `.agent/tasks/NAIA-15/progress.md`; điều tra này giữ nguyên.
- Danh sách file, kích thước và mã băm của bản kiểm tra: [change-inventory.json](evidence/change-inventory.json). Mã băm giúp nhận ra file đã đổi sau ngày báo cáo, không chứng minh nội dung đúng nghiệp vụ.

Yêu cầu trực tiếp của Owner đã được ghi là **đích sửa chưa được runtime đáp ứng** trong spec tương ứng; các lựa chọn chưa trả lời vẫn để mở:

| Luồng | Yêu cầu hiện tại |
|---|---|
| Word | Logic xuất mới; chuyển mẫu cũ sang placeholder mới; xuất đầy đủ thông tin Người. Placeholder là dấu giữ chỗ trong mẫu, ví dụ `[Người 1 - Họ tên]`. |
| Địa chỉ | Gõ địa chỉ hoặc cụm tên, kể cả chỉ `xã Yên Bình`, phải tra được danh sách cũ/mới phù hợp; nhận biết chữ xã/phường/tỉnh; người dùng chọn nhập địa chỉ mới. |
| Trích xuất | Một hợp đồng có 3 người, 1 tài sản phải tách đủ các bản ghi và trường chuẩn để đưa vào Stage. Stage là vùng người dùng kiểm tra dữ liệu trước khi lưu. |
| Tài sản | Bắt buộc: địa chỉ, số thửa, số tờ, diện tích tổng, loại đất. Serial không có mẫu định dạng chuẩn. |

## 2. Cách đọc các ghi nhận

**Tái hiện**: đã gọi code hiện tại với đầu vào cụ thể và lưu kết quả. **Đọc code**: thấy đường xử lý trong source, chưa chạy trọn thao tác trên ứng dụng thật. **Chưa xác định**: còn thiếu file gốc, thao tác hoặc nguồn phê duyệt. Ưu tiên và phân loại ở mục 10 dùng để lập plan, không phải kết luận nghiệm thu.

## 3. Người, trường địa chỉ và tài sản

### NG-01 — Đã rút: nghi vấn nhầm dữ liệu địa chỉ và nơi cấp

**Tái hiện bằng bộ dựng màn hình dùng trong test.** Người mẫu sống có `dia_chi=null`, `noi_cap="Bộ Công an"`, `ngay_chet=null`. Ô địa chỉ vẫn rỗng; ngay dưới nó xuất hiện ô `Bộ Công an` mang nhãn truy cập `Nơi cấp giấy khai tử — Người sống mẫu`.

[case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js), dòng 1149–1164, ghép cả hai ô vào cùng ô bảng Địa chỉ; điều kiện `p.ngay_chet || p.noi_cap` khiến người sống có nơi cấp cũng vào nhánh này. [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 237–277, lại áp quy tắc UBND/khai tử cho ô nơi cấp đó.

Phép thử chỉ chứng minh cách vẽ hai ô, không chứng minh nhầm dữ liệu. Người dùng đã xác nhận nhận định nhầm trường trước đó là nhìn nhầm. **Không sửa ánh xạ `dia_chi`/`noi_cap` hoặc chuyển vị trí trường chỉ vì ghi nhận này.** Bằng chứng giao diện cũ được giữ tại [ui-probes.json](evidence/ui-probes.json); các điều kiện tra cứu địa chỉ vẫn được xem riêng ở nhóm DC.

### TS-01 — Bộ bắt buộc hiện tại khác yêu cầu tài sản người dùng vừa nêu

**Tái hiện ở validator lưu Stage.** Serial `AB123456` và địa chỉ có chữ, nhưng số thửa/số tờ để null, các dòng loại đất rỗng → không có lỗi. Serial `1234/X-2020` → `invalid_format` với yêu cầu `[A-Z]{2}` và 6–8 chữ số.

[case_workspace.py](../../notary_v2/services/case_workspace.py), dòng 2276–2305, bắt serial/địa chỉ, cho số thửa/số tờ và cụm đất trống. Quy tắc này **đã có ở nhánh nền**, không phải toàn bộ do 19 commit mới tạo ra. Bản spec trước review ghi quy tắc tương ứng và dẫn “Owner xác nhận 03/10/2026”; [stage.md](../../docs/spec/notary_v2/stage.md) hiện đã ghi yêu cầu mới 04/10 và sự khác biệt với runtime.

Record [MIN-141/progress.md](../../.agent/tasks/MIN-141/progress.md), dòng 7–15, nói đã duyệt gộp 14 commit để xử lý các điểm khác MIN-140; chưa có bằng chứng trong phiên này cho việc người dùng duyệt riêng từng ràng buộc serial. Không diễn giải việc duyệt gộp thành câu trả lời thay người dùng. Yêu cầu mới trong phiên này được ghi ở mục 1. Bằng chứng chạy: [domain-probes.json](evidence/domain-probes.json), `asset_required`.

### TS-02 — Serial không theo mẫu có thể bị thay bằng giá trị giả rồi ghi đè dữ liệu gốc

**Tái hiện với database trong bộ nhớ.** Tài sản đã có serial `1234/X-2020`; `_asset_wire` trả ra `XX000001` kèm cảnh báo. Gửi chính dòng đó vào `_upsert_assets` làm serial bản ghi thành `XX000001`.

[case_workspace.py](../../notary_v2/services/case_workspace.py), dòng 1801–1811 và 2476, nối hai bước này. Đọc hồ sơ riêng lẻ chưa ghi đè; đường **đọc → Stage → lưu lại** mới tạo thay đổi. Quy tắc thay serial cũng đã có ở nhánh nền. [entities.md](../../contracts/entities.md), dòng 39–49, mô tả dữ liệu legacy giữ nguyên trong DB khi đọc; mô tả đó chưa thể hiện hậu quả khi lưu lại. Bằng chứng: `legacy_serial` trong [domain-probes.json](evidence/domain-probes.json).

### TS-03 — Diện tích tổng có trong DB nhưng chưa đi xuyên suốt Nhập → Stage → Lưu → Word

**Đọc code và tái hiện phần Word.** [models.py](../../notary_v2/models.py), dòng 110, đã có `Property.dien_tich`; không phải thiếu cột DB. Nhưng danh sách trường tài sản trong model màn hình, `_asset_contract_keys`, schema Stage và đường `_upsert_assets` chưa có trường diện tích tổng độc lập cho người dùng nhập/lưu.

[adapters/docx.py](../../notary_v2/services/document_intake/adapters/docx.py), dòng 128–130, bỏ `dien_tich` đã trích khi có `land_rows`. [word_engine.py](../../notary_v2/services/word_engine.py), dòng 1620–1627 và 1794–1804, lấy tổng các dòng loại đất khi tổng đó khác 0.

Phép thử có diện tích tổng nguồn **300**, chỉ một dòng loại đất **100**: `[Diện tích]`, `[Tài sản 1 - Diện tích]` và chữ diện tích đều xuất **100**. Chưa có cách giữ riêng hai số rồi báo chênh lệch trong luồng này. Bằng chứng: `total_area` trong [domain-probes.json](evidence/domain-probes.json).

## 4. Trích xuất hợp đồng

### RE-01 — Nhận diện người phụ thuộc mạnh vào tiêu đề và cách đánh số

**Tái hiện qua đúng lõi dùng bởi adapter DOCX:** profile `transfer` 1.1.2. Hợp đồng mẫu có 3 người và 1 tài sản; bản gốc tự dựng lấy được 3 người. Chỉ thay cách trình bày đã cho các kết quả sau:

| Biến thể đầu vào | Kết quả |
|---|---|
| `Ông: Nguyễn…` → `1. Ông: Nguyễn…`, tương tự người 2 và 3 | 0 người, danh sách lỗi engine rỗng. |
| Đổi tiêu đề thành khai nhận di sản và `BÊN A:` thành `NHỮNG NGƯỜI KHAI NHẬN DI SẢN:` | 0 người. |
| Thêm `chết ngày 02/03/2020` vào dòng người thứ nhất | 4 bản ghi người; có tên giả `chết ngày 02/03/2020`; không trích đúng ngày chết. |
| Địa chỉ nối với `trụ tại xã Vụ Bản, sinh ngày…; CCCD số…` | Có bản ghi người mang tên `trụ tại xã Vụ Bản`. |

Nguồn: [transfer.json](../../tools/regex_workbench/engine/profiles/transfer.json), các quy tắc vùng đương sự và tách người khoảng dòng 168–215; [adapters/docx.py](../../notary_v2/services/document_intake/adapters/docx.py), dòng 30, luôn nạp profile `transfer`. Các câu mẫu dùng để thử, không phải hợp đồng gốc trong ảnh 1. Có hiện tượng tên giả giống ảnh; chưa khẳng định cùng nguyên nhân trên chính file của người dùng.

### RE-02 — Địa chỉ, serial và loại đất có các cách viết thông thường chưa được nhận đúng

**Tái hiện trên các biến thể của cùng mẫu:**

| Biến thể | Kết quả |
|---|---|
| `thường trú: số 12, P. Yên Bình, TP. Ninh Bình.` | Địa chỉ chỉ còn `số 12, P`; bị cắt ở dấu chấm viết tắt. |
| `có địa chỉ tại:` → `Địa chỉ thửa đất:` | Mất trường địa chỉ tài sản. |
| `Loại đất:` → `Mục đích sử dụng:` | Không có dòng loại đất. |
| Serial `AB123456` → `1234/X-2020` | Không lấy được serial nguồn. |

Nguồn: [transfer.json](../../tools/regex_workbench/engine/profiles/transfer.json), khoảng dòng 213, 249, 281, 310–315. Các mẫu tìm chữ đang dựa vào nhãn hẹp; mẫu địa chỉ người dừng ở dấu chấm.

### RE-03 — Hai thửa/hai GCN không có nhãn “Tài sản N” bị gom thành một nhóm

**Tái hiện.** Đầu vào tự dựng có hai số thửa 206/207 và hai serial AB/CD, bỏ dòng `Tài sản 1:` → engine trả **một nhóm tài sản mơ hồ**, không trả hai bản ghi tài sản đã tách.

[runner.py](../../tools/regex_workbench/engine/runner.py), dòng 242–266, mở nhóm chủ yếu theo nhãn `Tài sản [thứ] N:`. Ghi nhận này không đồng nhất “hai dòng loại đất” với “hai tài sản”; phép thử có hai GCN để chỉ rõ trường hợp đang khảo sát.

### RE-04 — Danh sách trường trích còn hẹp hơn dữ liệu chuẩn hệ thống

**Đọc code.** Profile hiện tại chưa có quy tắc riêng cho ngày chết; các trường tài sản như cơ quan cấp, loại sổ, hình thức sử dụng, nguồn gốc chưa được bao phủ như các trường Stage đang có. Số giấy tờ được adapter coi là trường cần cảnh báo thiếu, trong khi Stage chỉ bắt buộc họ tên. Nhận được nhiều gợi ý chưa chứng minh đã đủ trường và đúng đối tượng.

Đầu vào và kết quả của 10 phép thử RE-01/02/03: [engine-probes.py](evidence/engine-probes.py), [probes.json](evidence/probes.json). Chưa có bộ hợp đồng thật với đáp án do người dùng xác nhận để tính tỷ lệ chính xác. Bộ test hiện có kiểm các dạng mẫu cụ thể; không suy tỷ lệ chính xác từ số test qua.

## 5. Tra cứu địa chỉ hành chính

### DC-01 — Truy vấn đơn giản bị chặn cả ở màn hình lẫn backend

**Tái hiện và đọc code.** `{address:"xã Yên Bình"}` trả `invalid_input`. Thêm đủ hai ngày nhưng vẫn chỉ có cụm này cũng trả `invalid_input`: bộ tách yêu cầu xã/phường **và tỉnh**. Nhập `xã Yên, tỉnh Ninh Bình` không tìm thấy, vì không có tìm kiếm theo một phần tên.

[case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 237–277, chỉ gửi khi có địa chỉ, ngày cấp đầy đủ và ngày lập hồ sơ đầy đủ. [address-lookup.schema.json](../../contracts/notary-case-drafting/address-lookup.schema.json), dòng 10 trở đi, bắt hai ngày. [administrative_address.py](../../notary_v2/services/administrative_address.py), dòng 36–58, 200–236 và 280–297, tách địa chỉ và tìm bằng khóa tên đầy đủ.

Thông báo “Cần địa chỉ, ngày cấp đầy đủ…” trong ảnh xuất phát từ chính điều kiện này. Đây là hành vi cũng được ghi trong spec Draft, khác yêu cầu tìm cụm tên người dùng nêu trong phiên này.

### DC-02 — Chữ “xã” và “phường” bị bỏ trước khi đối chiếu

**Tái hiện với kho đang có.** `xã Yên Bình, tỉnh Ninh Bình`, ngày nguồn 2024-01-01, ngày đích 2026-10-04 → hai ứng viên:

- Xã Vũ Dương, từ câu nguồn nhắc **Xã Yên Bình**.
- Phường Yên Thắng, từ câu nguồn nhắc **Phường Yên Bình**.

[administrative_address.py](../../notary_v2/services/administrative_address.py), dòng 28–33, xóa tiền tố cấp khi tạo khóa so tên; cả hai vào cùng nhóm `commune`. Việc người dùng đã gõ rõ `xã` chưa được giữ làm điều kiện lọc ứng viên. Bằng chứng câu nguồn và kết quả: `addresses` trong [probes.json](evidence/probes.json).

### DC-03 — Địa chỉ hiện tại vẫn được ghép “nay là” chính nó

**Tái hiện.** `xã Vũ Dương, tỉnh Ninh Bình`, hai ngày trong 2026, trả ứng viên cùng địa chỉ. Áp dụng tạo:

`xã Vũ Dương, tỉnh Ninh Bình (nay là Xã Vũ Dương, Tỉnh Ninh Bình)`.

[administrative_address.py](../../notary_v2/services/administrative_address.py), dòng 93–95, và [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 316–319, luôn nối hậu tố khi áp dụng; chưa so xem có thực sự đổi địa chỉ không. Bằng chứng: [address-extra.json](evidence/address-extra.json).

### DC-04 — Cùng một chuỗi địa chỉ bị tách khác nhau chỉ vì ngày giấy tờ

**Tái hiện.** `Thôn A, Yên Bình, Ninh Bình`:

- Ngày nguồn 2024: coi Yên Bình là huyện, Thôn A là xã → `not_found`.
- Ngày nguồn 2026: coi Yên Bình là xã, Thôn A là thôn → có ứng viên.

[administrative_address.py](../../notary_v2/services/administrative_address.py), dòng 56–72, dùng mốc 2025-07-01 để đoán cấp với các cụm không có tiền tố. Ngày giấy tờ chưa chứng minh chuỗi trên có hay không có huyện. Kết quả và cấu trúc đã tách lưu tại [address-extra.json](evidence/address-extra.json).

### DC-05 — Ô nơi niêm yết chưa tra chính nội dung người dùng gõ

**Đọc code.** `addressContext('posting', rowId)` lấy `row.dia_chi` của tài sản và ngày cấp của tài sản, không lấy `caseInfo.noi_niem_yet` làm chuỗi tìm kiếm. Màn hình yêu cầu chọn tài sản nguồn, kể cả khi người dùng chỉ muốn tìm xã trong ô nơi niêm yết.

Nguồn: [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 237–243, 257–261, 311; [case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js), dòng 769–783. Đây cũng là flow được ghi trong `word-output.md`, dòng 34–38; chưa phải flow tìm cụm tên tự do.

### DC-06 — Kho có danh mục và câu gốc, chưa có lịch sử có ngày được xác nhận

**Đếm và kiểm nội dung kho hiện tại.** Có 3.355 đơn vị: 34 tỉnh, 3.321 đơn vị cấp xã; 3.219 sự kiện, **tất cả `pending`**, **0 sự kiện có ngày hiệu lực**. Kiểm mã băm của 35 snapshot đều khớp với ledger.

Vì vậy các truy vấn thật đã thử đi vào nhánh ứng viên theo danh mục/câu gốc (`current_catalog_candidates`), không chứng minh quan hệ đổi tên theo ngày (`confirmed_history`). Kho vẫn có ích để tìm tên cũ được nhắc trong câu nguồn; không ghi nhận là “không có dữ liệu cũ/mới”. Mã băm khớp cũng chưa chứng minh nguồn có thẩm quyền pháp lý hay lịch sử đã đầy đủ.

Nguồn: [ledger.json](../../notary_v2/data/administrative_units/ledger.json), [administrative_timeline.py](../../notary_v2/administrative_timeline.py), đường nhập Bando; [probes.json](evidence/probes.json) và [address-extra.json](evidence/address-extra.json). Chưa đối chiếu trực tiếp nghị quyết/văn bản nhà nước hoặc cập nhật nguồn ngoài mạng trong phiên này.

### DC-07 — Hai giới hạn khác nhìn thấy trong code, chưa có phép thử dữ liệu thật

**Đọc code, chưa kết luận ảnh hưởng trên kho thật.** Nhánh lịch sử xác nhận chọn xã theo xã+tỉnh, chưa dùng huyện nguồn để phân biệt các xã trùng tên; lọc huyện chỉ có trong nhánh ứng viên câu gốc (dòng 206 và 245–247). Bộ nhập Bando còn kiểm đúng số lượng 34/3.321 của đợt dữ liệu này; thay đổi số lượng ở đợt sau không tự được nhận. Giới hạn số lượng đã được spec timeline ghi nhận.

## 6. Danh bạ và xuất Word

### DB-01 — Nút “+ Danh bạ” vẫn bị khóa sau khi người dùng gõ tên

**Tái hiện bằng bộ dựng màn hình.** Ban đầu ô ủy quyền rỗng, nút bị khóa. Gõ tên → sự kiện input → change → mất focus: nút vẫn khóa. Chỉ sau một thao tác khác phát tín hiệu vẽ lại màn hình, nút mới mở.

[case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js), dòng 1287–1295 và 1673–1700: để giữ con trỏ, code hoãn dựng lại khi input còn focus; phần cập nhật nhanh không cập nhật nút này. Nút đang gọi tạo khách hàng mới từ tên, không mở màn hình chọn danh bạ. Cần phân biệt hành vi hiện có với ý nghĩa người dùng mong đợi của nút. Lỗi giữ nút khóa đã có ở nhánh nền. Bằng chứng: `catalog` trong [ui-probes.json](evidence/ui-probes.json).

**Đọc code thêm:** chọn người trong danh sách tên dùng `.find` theo họ tên; hai người trùng tên có thể cùng dẫn về người đầu tiên. Danh sách tải ban đầu giới hạn 200 người, chưa thấy truy vấn theo nội dung đang gõ ở đường này. Chưa thử với danh bạ thật.

### W-01 — Người nhận ủy quyền trong thông tin hồ sơ khác nguồn người được ủy quyền của mẫu Word

**Tái hiện ở engine.** Hồ sơ đã có `nguoinhanuyquyen={id:3,ten:"Đại diện được chọn ở hồ sơ"}`. Placeholder metadata `[nguoinhanuyquyen]` có tên, nhưng `authorized_people` rỗng và `[Người được ủy quyền 1 - Họ tên]` rỗng.

[word_engine.py](../../notary_v2/services/word_engine.py), dòng 803 trở đi, lấy nhóm người được ủy quyền từ vai trò `participants`, không từ trường người dùng chọn trong card hồ sơ. Mẫu đã chuyển `3. UQ.docx` đòi `[Dòng người được ủy quyền1]`; [word_batch_export.py](../../notary_v2/services/word_batch_export.py), dòng 496–504, có thể chặn bằng `word.missing_authorized_person` ở trạng thái trên.

Spec `word-output.md`, dòng 107–114, cũng đang ghi hai nguồn như vậy. Đây là một đường chặn đã tìm thấy; **chưa khẳng định đó là lỗi xuất Word cụ thể người dùng đang gặp**. Bằng chứng: `authorization` trong [domain-probes.json](evidence/domain-probes.json); mẫu đã đọc bằng OfficeCLI 1.0.153 tại [3. UQ.docx](evidence/word-artifacts.md).

### W-02 — Mẫu “đã chuyển” vẫn chứa nhiều placeholder cũ, hai hệ đánh số có nghĩa khác nhau

**Kiểm manifest và gọi engine.** Bộ mẫu đã chuyển có 22 file; manifest đếm 2.128 lần xuất hiện token, `applied=47`, thêm 14 lần thay chữ tĩnh. Có nhiều token được giữ nguyên do engine tiếp tục hỗ trợ alias cũ. Không diễn giải `applied=47` thành chỉ 47 ô được điền khi xuất; đây là số thay token trong bước chuyển mẫu.

Ví dụ Stage có người nhận ở dòng 1, chủ ở dòng 2:

| Placeholder | Người được lấy |
|---|---|
| `[Người 1 - Họ tên]` | Người nhận, đúng dòng 1 Stage. |
| `[Tên 1]` và `[ten1]` | Chủ ở dòng 2 Stage. |
| `[Người 2 - Họ tên]` | Chủ ở dòng 2 Stage. |
| `[Tên 3]` | Người nhận ở dòng 1 Stage. |

Nguồn: [word_template_migration.py](../../notary_v2/services/word_template_migration.py), `old_to_new_map` khoảng dòng 509–527; [word_engine.py](../../notary_v2/services/word_engine.py), `_pick_core_people`, mapping legacy và mapping danh sách Stage; [migration_manifest.json](evidence/word-artifacts.md), [domain-probes.json](evidence/domain-probes.json).

Spec công khai việc giữ thứ tự legacy, nên không coi bảng trên tự nó là lỗi so với spec hiện tại. Nó cho thấy “mẫu đã chuyển và xuất được” chưa đồng nghĩa “toàn bộ placeholder đã chuyển sang cùng hệ mới” theo mục tiêu người dùng. Engine mới vẫn dùng nhiều hàm/chế độ cũ, không phải thay toàn bộ engine cũ.

### W-03 — Xuất trường Người vẫn bị chặn bởi điều kiện có tài sản; hai bên còn cần sơ đồ

**Đọc code.** `word_block_reason(..., static=True)` yêu cầu có người, có tài sản; hồ sơ hai bên cần sơ đồ đã lưu, kể cả khi mẫu chỉ chứa thông tin Người. Nguồn: [word_engine.py](../../notary_v2/services/word_engine.py), dòng 1353–1363; spec Word trước review ghi tương ứng. Owner đã trả lời Q5 ở mục 11: chỉ kiểm dữ liệu mẫu cần. Runtime vẫn chưa sửa theo quyết định đó.

Nhánh dùng hợp đồng gốc còn chặn khi Stage hoặc sơ đồ chưa lưu. Khi Stage bị chặn bởi TS-01, đường xuất dùng dữ liệu đã lưu có thể chưa đi tiếp được. Chưa có mã lỗi/thao tác xuất của người dùng để chọn đúng một nguyên nhân.

### W-04 — Bằng chứng xuất trước đây chưa bao gồm chạy màn hình chọn thư mục trên ứng dụng thật

**Đọc artifact có sẵn, không chạy lại xuất 22 mẫu.** [e2e_report.json](evidence/word-artifacts.md) ghi xuất 22 file, 0 lỗi; 17 mẫu có kiểm so cấu trúc XML, 5 mẫu `.doc` chuyển qua Word COM ghi hạn chế tương ứng. Kiểm số trang bằng Word COM được ghi cho 22 file; phần UI ghi `not_run` vì chưa chạy luồng chọn thư mục thật.

Các bản mẫu chuyển nằm trong `artifacts/…/migrated`, là file không được theo dõi trong Git; không phải 22 mẫu đã tự thay vào thư mục runtime. Luồng thư mục cần người dùng chọn đúng thư mục mẫu. Chưa kiểm trên bản cài đóng gói hoặc xem từng trang Word trong phiên điều tra này; chưa xác nhận toàn bộ chữ điền đúng người/đúng tài sản bằng đáp án người dùng duyệt.

## 7. Rà soát tài liệu đã đổi

Đã đối chiếu các thay đổi ở 12 file `docs/spec/`, contract liên quan, catalog placeholder và task record. Bảng dưới ghi hiện trạng trước lượt sửa tài liệu của review này. Phần yêu cầu mới đã được thêm riêng vào 5 spec; không dùng việc thêm yêu cầu để tuyên bố runtime đã hoàn thành.

| File | Ghi nhận |
|---|---|
| [docs/spec/README.md](../../docs/spec/README.md) | Có thêm Bando làm nguồn cập nhật kho; link nguồn không tự chứng minh lịch sử đã xác nhận. |
| [notary_v2/README.md](../../docs/spec/notary_v2/README.md) | Dẫn các luồng mới, phân biệt trạng thái; vẫn phải đọc giới hạn tại spec lá. |
| [administrative-address.md](../../docs/spec/notary_v2/administrative-address.md) | Draft; quy tắc bắt ngày/xã+tỉnh, nối `nay là`, chọn tài sản niêm yết đều khác thao tác tìm cụm tên người dùng vừa yêu cầu. |
| [administrative-timeline.md](../../docs/spec/notary_v2/administrative-timeline.md) | Active cho kho/CLI; tự ghi thiếu ngày và khác biệt observed/confirmed. Active không có nghĩa toàn bộ sự kiện trong kho đã confirmed. |
| [input/README.md](../../docs/spec/notary_v2/input/README.md) | Link Word local và quy tắc giữ nguyên địa chỉ; chưa phải bằng chứng engine trích đúng mọi hợp đồng. |
| [input/docx-import.md](../../docs/spec/notary_v2/input/docx-import.md) | Active cho flow, **tự ghi độ chính xác chưa nghiệm thu**; phạm vi mẫu `transfer`, tài sản có nhãn và dòng `Loại đất:`. |
| [stage.md](../../docs/spec/notary_v2/stage.md) | Bộ bắt buộc serial/địa chỉ là quy tắc nền, trái yêu cầu hiện tại; ghi nguồn “duyệt gộp” chưa đủ để kiểm xác nhận riêng từng ràng buộc. |
| [word-output.md](../../docs/spec/notary_v2/word-output.md) | Active hai loại hồ sơ; vẫn giữ alias legacy, yêu cầu tài sản/sơ đồ, lấy nhóm ủy quyền từ participants. Có ghi giới hạn kiểm chứng; không thể dùng chữ Active làm nghiệm thu đầu ra đầy đủ. |
| [word-output-detail.md](../../docs/spec/notary_v2/word-output-detail.md) | Đã đổi nguồn Người sang thứ tự Stage cho catalog mới; khi đọc phải phân biệt alias legacy giữ số khác. |
| [diagram/two-party.md](../../docs/spec/notary_v2/diagram/two-party.md) | Đã mở Word hai bên; số Người theo Stage, số Bên A/B theo vị trí sơ đồ. Đây là hai cách đánh số khác nhau có chủ ý trong docs. |
| [workspace-detail.md](../../docs/spec/notary_v2/workspace-detail.md) | Đã ghi capability Word hai bên; capability chỉ báo có chức năng, không chứng minh mẫu sẽ đủ dữ liệu. |
| [upload_lab/README.md](../../docs/spec/upload_lab/README.md) | Ghi dùng dialog hiện có, không tab thứ ba; không thấy bằng chứng lỗi ở thay đổi điều hướng này. |

[contracts/notary-case-drafting.md](../../contracts/notary-case-drafting.md) và schema đã thêm lookup địa chỉ, update metadata, xuất theo thư mục và DOCX context. Phần mô tả Approved v1/v2 ở cấp contract không tự phân biệt trạng thái Draft của tra cứu địa chỉ hay việc nghiệm thu regex. Cần giữ tách bạch **hình dạng dữ liệu/lệnh được mô tả** và **hành vi, nguồn dữ liệu đã được duyệt**; chưa xác minh phê duyệt trên Linear trong phiên này.

[placeholder_mapping.md](../../notary_v2/word_templates/placeholder_mapping.md) giữ cả tên mới và alias cũ; token đất `[ONT]` đang được giải thích theo vị trí cụm, không mặc định là tìm đúng mã loại đất ONT. Tài liệu có ghi quyết định owner cho cách này; chưa dùng tên token để tự đổi nghiệp vụ.

Các handoff/task log có nguồn lịch sử và số test, nhưng không làm spec Draft hay độ chính xác chưa nghiệm thu tự trở thành Approved. Các lỗi TS-01/02 và DB-01 được phân biệt là có từ nhánh nền để tránh quy toàn bộ cho hai commit cuối.

## 8. Kiểm tra đã chạy và giới hạn

| Kiểm tra | Kết quả hiện tại | Bằng chứng |
|---|---|---|
| 8 bộ Python: address, timeline, DOCX, workspace, Word engine/batch/migration, E2E script | Lần đầu 514 qua, 27 lỗi môi trường, 4 bỏ qua; chạy lại đúng 27 trường hợp: 25 qua, 2 bỏ qua. Tổng 539 qua, 6 bỏ qua. | [python-checks.log](evidence/python-checks.log), [python-recheck-checks.log](evidence/python-recheck-checks.log) |
| Python adapter thật/giả, regex workbench, metadata | 293 qua, 2 bỏ qua. | [additional-python-checks.log](evidence/additional-python-checks.log) |
| 5 bộ Node cho địa chỉ, intake, model/view, schema | Lần đầu 190 qua, 1 lỗi môi trường; chạy lại trường hợp đó qua. Tổng 191 qua. | [node-checks.log](evidence/node-checks.log), [node-recheck-checks.log](evidence/node-recheck-checks.log) |
| Node kiểm quy tắc source tĩnh | 36 qua. | [additional-node-checks.log](evidence/additional-node-checks.log) |
| Ví dụ contract | 81 file, 0 kết quả ngoài dự kiến. | [contract-checks.log](evidence/contract-checks.log) |
| Phép thử theo triệu chứng/yêu cầu | Có các sai lệch được ghi tại NG/TS/RE/DC/DB/W; không dùng chúng để tính tỷ lệ chính xác corpus. | Các JSON và script trong [artifacts điều tra](evidence/) |

Lỗi môi trường ban đầu: thiếu `jsonschema`, chạy một số test từ root trong khi fixture dùng đường dẫn tương đối dưới `notary_v2`, và trùng tên package `tests` khi gom nhiều cây test. Chạy lại đã dùng `jsonschema` cài riêng trong thư mục tạm, đúng thư mục và chế độ import phù hợp; không sửa code để làm test qua. Tổng kết gộp các lượt: **832 test Python qua, 8 bỏ qua; 227 test Node qua**. Đây không phải một lượt full suite của toàn repo.

Phạm vi đã làm: kiểm danh sách toàn bộ diff; đọc docs/spec đổi, các nhánh xử lý code chính và phần thay đổi liên quan; đọc test/record/artifact để đối chiếu; kiểm cấu trúc/số lượng/mã băm kho; thử engine và màn hình giả lập. Không tuyên bố đã đọc thủ công từng dòng của 151 file hoặc 516 nghìn dòng dữ liệu. Những thứ chưa có bằng chứng trực tiếp:

- File hợp đồng gây đúng ảnh 1, snapshot sau import và thao tác/mã lỗi xuất Word của người dùng.
- Bộ hợp đồng/mẫu với đáp án người dùng duyệt để chấm đầy đủ người, tài sản, trường và giá trị Word.
- Nghị quyết và nguồn nhà nước cho từng quan hệ đổi tên/gộp/tách, ngày hiệu lực; trạng thái Linear và chat phê duyệt nguyên bản.
- Màn hình Electron chạy thật, danh bạ thật, hộp chọn thư mục của Windows, bản cài đóng gói và việc xem từng trang Word.

Các đường bảo vệ đã thấy và test qua cũng được giữ trong bằng chứng: file DOCX gốc có mã băm; thay chữ theo vị trí đã chọn; kiểm revision và không tự ghi gợi ý địa chỉ. Chúng không thay thế việc kiểm đúng nội dung trích/xuất.

## 9. Năm lỗi bổ sung và tách lại sau review

### RE-05 — Reader đọc cả hai bản thay thế của cùng nội dung Word

**Tái hiện bằng DOCX tự dựng.** XML có `AlternateContent` với `Choice` và `Fallback`: đây là hai cách biểu diễn để Word chọn một cách hiển thị. Mỗi nhánh chứa cùng một người. Reader đọc cả hai → engine trả **2 người**, dù nội dung có một người hiển thị.

[docx_source.py](../../notary_v2/services/document_intake/docx_source.py), dòng 88–95, đi vào mọi nhánh con. Cảnh báo “chưa hỗ trợ sửa” không ngăn adapter dùng chữ đó để trích. Không sửa bằng cách bỏ mọi đoạn giống nhau: hai người thật trùng tên vẫn có thể là hai người khác nhau. Bằng chứng: [parent-probes.py](./parent-probes.py), [parent-probes.json](./parent-probes.json), khóa `alternate_content`.

### DC-08 — Chọn lại bộ địa chỉ cũ nhưng trả tên từ bộ mới hơn

**Tái hiện qua đường nhập kho thật, trong thư mục tạm.** Nhập bộ A có `Xã C`, bộ B đổi thành `Xã New C`, rồi nhập lại A. `dataset_version` đang là A, nhưng tìm `Xã C, Tỉnh Test` trả **Xã New C, Tỉnh Test**.

[administrative_address.py](../../notary_v2/services/administrative_address.py), dòng 248–249, lấy tên observed cuối cùng trong toàn lịch sử thay vì tên của phiên bản đang hoạt động. Quan sát dùng để tìm tên đầu vào lại đã lọc theo phiên bản, nên đầu vào và kết quả không cùng bộ dữ liệu. Kho giữ A/B là đúng; chọn tên để trả về đang sai. Bằng chứng: [verify-address-refresh.py](./verify-address-refresh.py), [address-refresh-probe.json](./address-refresh-probe.json). Phép thử dùng catalog nhỏ với `strict=False`, không thay kho 34/3.321 của ứng dụng.

### DB-02 — Gõ tên trùng nhau tự gắn ID của người đầu tiên

**Tái hiện bằng model màn hình thật.** Danh bạ có ID 11 và 22, cùng `Nguyễn Văn An`, số giấy tờ lần lượt 111 và 222. Gõ tên đó → `nguoi_nhan_uy_quyen_id=11`; chưa có thao tác chọn đúng người.

[case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 1573–1579, dùng `.find` theo họ tên. Đây là lỗi chọn danh tính riêng với lỗi nút khóa DB-01. Cần lựa chọn bằng ID và hiển thị thông tin phân biệt; khi chỉ gõ tên mơ hồ không tự gán người đầu tiên. Bằng chứng: [contact-name-probe.mjs](./contact-name-probe.mjs), [contact-name-probe.json](./contact-name-probe.json).

### W-05 — Mã chặn xuất mẫu gốc có trong code nhưng không có trong schema

**Đối chiếu code/schema.** [notary_adapter.py](../../shell/sidecar/notary_adapter.py), dòng 1023–1029, có thể trả `documents[].block_reason="word.original_mapping_invalid"`. Danh sách cho phép trong [common.schema.json](../../contracts/notary-case-drafting/common.schema.json), dòng 497–503, và `BLOCK_REASONS` của [validate_examples.py](../../contracts/notary-case-drafting/validate_examples.py), dòng 114–119, thiếu giá trị này.

Response đó không phù hợp contract của chính hệ thống. UI đã có nhãn cho mã lỗi nên **chưa kết luận đây là nguyên nhân màn hình xuất Word bị hỏng**. Cần fixture response thật cho mapping thiếu/sai, không chỉ ví dụ happy path. Bằng chứng enum và mã phát ra: [parent-probes.json](./parent-probes.json), khóa `original_reason_schema`.

### NG-02 — Người sống vẫn được gắn nhãn và lời nhắc giấy khai tử

**Tái hiện UI từ phép thử ở NG-01, phân loại riêng.** Người mẫu `ngay_chet=null`, `noi_cap="Bộ Công an"` vẫn có ô mang nhãn “Nơi cấp giấy khai tử” và lời nhắc “Nhập đúng địa chỉ UBND trên giấy khai tử”. Đây là lỗi nhãn/ngữ cảnh trợ giúp, không là nghi vấn hoán đổi hai trường đã rút.

[case-drafting-view.js](../../shell/src/renderer/notary/case-drafting-view.js), dòng 1155–1164, mở nhánh giấy khai tử chỉ vì `noi_cap` có dữ liệu. [case-drafting-model.js](../../shell/src/renderer/notary/case-drafting-model.js), dòng 271–273, áp trợ giúp UBND cho nhánh đó. Spec Stage đã phân biệt nơi cấp giấy tờ người sống và người chết; cần sửa nhãn và việc bật gợi ý theo đúng ngữ cảnh, giữ giá trị nơi cấp hiện có. Bằng chứng: [ui-probes.json](evidence/ui-probes.json). Chưa chạy UI Electron thật.

## 10. Phân loại để giao sửa

| Nhóm | Cách xử lý | Tại sao / điều kiện |
|---|---|---|
| TS-02, TS-03 | Ưu tiên trước luồng nhập/xuất | Có nguy cơ đổi serial nguồn hoặc xuất sai diện tích tổng. DB đã có diện tích; không tạo cột mới trùng nghĩa. |
| TS-01 | Cập nhật theo yêu cầu mới | Quy tắc bắt buộc cũ có từ nền; Owner đã thay bằng 5 trường ở mục 1. Serial DB hiện còn `NOT NULL, UNIQUE`; phải cho để trống và trùng giữa các thửa cùng sổ theo Q4 đã chốt. |
| RE-01/02/04/05 | Sửa khả năng trích và kiểm đủ trường | Dữ liệu tự dựng đã chứng minh thiếu/thừa/sai. Mục tiêu toàn bộ hợp đồng rộng hơn profile transfer đang được ghi trong spec cũ. |
| RE-03 | Sửa nhận diện theo từng thửa, giữ serial chung nếu cùng sổ | Q4 đã chốt. DB hiện serial unique, upsert tìm theo serial; phải sửa để hai thửa không bị gom vào cùng entity. Không tự quy hai loại đất thành hai tài sản. |
| DC-01/05 | Thay luồng theo yêu cầu mới | Gõ cụm tên không cần ngày/tỉnh; nơi niêm yết tìm chính nội dung ô. |
| DC-02/03/04/08 | Sửa logic tìm và trình bày ứng viên | Giữ cấp xã/phường, không đoán cấp chỉ bằng ngày, không nối “nay là” vào địa chỉ không đổi, không trộn phiên bản. |
| DC-06 | Hoàn thiện nguồn và chứng cứ | Kho có tên/câu nguồn nhưng chưa có sự kiện confirmed có ngày. Không gọi toàn kho là lịch sử pháp lý đã chuẩn hóa. |
| DC-07 | Giới hạn đã biết; chưa nhận là lỗi | Spec chủ ý dùng huyện để phân biệt alias cũ và khóa số lượng một đợt nguồn. Không bỏ kiểm đầy đủ để nhận catalog thiếu. |
| DB-01/02 | Sửa nút và cách chọn ID | Lỗi đã tái hiện; không cần chờ Q2 để sửa lựa chọn danh bạ. Ý nghĩa nhóm UQ trong Word vẫn chờ Q2. |
| W-01/02 | Quyết định trước phần phụ thuộc | Nguồn UQ và nghĩa placeholder cũ cần Q1/Q2. W-02 là khoảng cách với mục tiêu chuyển hết mẫu, không tự nó là bug so với spec cũ. |
| W-03 | Sửa điều kiện xuất và đường lưu theo Q5 đã chốt | Mẫu chỉ kiểm dữ liệu cần, mẫu chỉ có Người không đòi tài sản/sơ đồ. DB hồ sơ hiện cũng đòi tài sản, không chỉ UI Word. |
| W-05 | Sửa contract và kiểm response thật | Thiếu mã lỗi đã đối chiếu được; không đổi luật nghiệp vụ. |
| W-04 | Bổ sung kiểm ứng dụng/Word/bản cài | Test xanh và kiểm XML chưa chứng minh dùng được qua thao tác thật hoặc điền đúng từng chỗ. |
| NG-01 | Rút khỏi đầu việc sửa | Owner đã đính chính; không tiếp tục dùng ảnh để kết luận nhầm trường. |
| NG-02 | Sửa nhãn/ngữ cảnh gợi ý | Chỉ ngữ cảnh giấy khai tử mới dùng nhãn/trợ giúp UBND; không bỏ dữ liệu nơi cấp của người sống. |

**Không nhận thêm lỗi hủy xuất:** đã đọc đường mẫu gốc và batch; có kiểm hủy trước công bố file, dọn file tạm và dọn file chép dở khi lỗi. Chưa tìm được bằng chứng để báo lỗi ở các đường này. Bộ test tương ứng vẫn phải được giữ khi viết lại.

## 11. Phần chờ và bàn giao

**Đã chốt bằng câu trả lời trực tiếp:** Q4 — mỗi thửa một tài sản riêng, cùng sổ thì dùng cùng serial; Q5 — chỉ kiểm dữ liệu mà mẫu thực sự cần, mẫu chỉ có Người được xuất khi chưa có tài sản/sơ đồ. Đã ghi vào Stage, DOCX import và Word spec.

Còn **Q1** nghĩa vai trò/thứ tự của placeholder cũ; **Q2** người nhận UQ trong hồ sơ và mẫu UQ có cùng vai trò; **Q3** thay phần hành chính hay nối `nay là`. Các nhánh phụ thuộc phải chờ xác nhận và ghi quyết định vào spec trước code.

Plan chi tiết, thứ tự phụ thuộc, task sửa và checklist parent review nằm trong **Implementation Plan của [TASK-2](../../backlog/archive/tasks/task-2%20-%20Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md)**. Báo cáo là bằng chứng hiện trạng; plan/spec là đích cần sửa. Agent implement phải bổ sung ca hồi quy vào tests được theo dõi trong Git, không chỉ dựa vào các script/artifact tạm này.

**Bổ sung chiến lược trích xuất của Owner:** engine được tách sang
[TASK-11](../../backlog/archive/tasks/task-11%20-%20Xay-lai-engine-trich-van-ban-theo-cau-truc-va-rule-dung-chung.md),
theo [spec nhận cấu trúc/chia vùng/quy tắc dùng chung](withdrawn-20261004/docs/spec/notary_v2/input/document-extraction.md).
Khoảng 30 loại và khoảng 10 nhóm là đầu vào dự kiến, chưa là danh mục đã kiểm.
TASK-6 giữ đọc DOCX/bằng chứng/adapter/Stage và phụ thuộc TASK-3/TASK-11;
các lỗi rules RE-01…04 thuộc task engine, RE-05 thuộc reader. Đây là quyết
định phân việc và tiêu chí nghiệm thu mới, không thay bằng chứng lỗi hiện tại.

Lượt bổ sung dùng hai reader **gpt-6-luna** theo yêu cầu Owner; parent kiểm chứng và phân loại. Các reviewer Astra đã dừng. Không ghi đây là một lượt hoàn tất đủ mọi reviewer của workflow BMAD. Đã đọc code map nhưng không dựng lại được vì Graphify không có trong môi trường; giới hạn này không được dùng làm bằng chứng code không có lỗi.

**Kết quả review:** có bằng chứng đủ để lập các phần sửa đã rõ; chưa nghiệm thu các chức năng và chưa triển khai sửa runtime. Test tổng ở mục 8 là các lượt điều tra trước, không phải một lượt full suite mới. Bốn phép kiểm bổ sung ở mục 9 không làm tăng tỷ lệ chính xác trích xuất hợp đồng thật.
