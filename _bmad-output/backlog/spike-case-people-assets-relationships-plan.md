---
title: "Làm rõ quan hệ nhiều Người–nhiều Tài sản trong Hồ sơ"
ticket: 43
status: draft
blocked_at: "2026-10-20"
blocked_reason: "Refinement/design awaiting owner: 16 synthetic cases completed; Q1 membership definition and Q2 A/B exceptions unresolved. Identity, source order and scope preservation are requirements, not owner gates. No runtime start; refined false; #41 gate unchanged."
---

# #43 — Đề xuất nghiệp vụ quan hệ Người–Tài sản trong Hồ sơ

**Artifact bền vững:** nội dung thiết kế PROPOSED nằm đầy đủ ngay trong plan này. Bản tmp chỉ là bằng chứng làm việc tùy chọn, không là nguồn bắt buộc hoặc spec đã áp dụng.

**Trạng thái refinement:** awaiting owner Q1–Q2; `status: draft`/blocked giữ nguyên, không runtime start, `hitl: true`, `refined: false`.

**Ngày:** 20/10/2026 · **Trạng thái: PROPOSED — chờ owner trả lời Q1–Q2.**

Đây là kết quả điều tra/refinement D06+D07, không phải contract, schema hoặc lệnh build. Chỉ dùng tình huống tổng hợp. `Người 1`, `Tài sản 1`, `GCN X` là nhãn minh họa, không phải dữ liệu khách hoặc giấy tờ giả. Không đọc mẫu thật, chạy parser, app, browser, test hoặc ghi DB. #43 vẫn `hitl: true`, `refined: false`; #41 chưa xong, gate mẫu ĐÓNG.

## 1. Phần đã chốt — không hỏi lại

- Lệnh owner mới nhất: **chỉ placeholder và trường tĩnh**. Không thiết kế tầng 2 đoạn động, formula engine hoặc điều kiện cho người dùng cấu hình. Đoạn trình bày có thể điền từ các trường/tham chiếu đã được duyệt; việc đó không tự duyệt trường văn bản canonical mới. Không xóa hoặc đổi nghĩa các block token Word legacy đang hoạt động.
- Mọi luồng dựa trên Người–Tài sản–Hồ sơ; quan hệ là nghĩa thuộc Hồ sơ, độc lập bố cục Word/editor. Cùng xuất hiện không chứng minh có liên kết. Không suy tích mọi Người × mọi Tài sản; không gộp theo tên hoặc serial.
- **Bảo toàn nghĩa scope là yêu cầu đã có** ở ticket AC2/SOT D07, không hỏi duyệt lại: cả nhóm–cả tập (C04), từng cặp riêng (C05), tập con chồng nhau (C06) và chưa rõ (C07) phải phân biệt. Không bung nhóm–tập thành quyền cá nhân, không biến chưa rõ thành tất cả/không có. Không đặt gate output toàn cục vì scope chưa rõ.
- R06/D08: requester = **tất cả Người thuộc Hồ sơ**, chỉ dữ kiện Người chuẩn. Không chọn B, người đầu, lookup, chỉ người ký hoặc chỉ người sống; không kèm lời quan hệ/chức vụ/tư cách. Phạm vi “thuộc Hồ sơ” chưa được owner xác định hết (Q1).
- D05 chọn nhóm output chung **Bên A/Bên B**. “Gần như 100% B có chữ nhận” là quan sát, không universal regex; không có chữ nhận không suy thành A. Ngoại lệ một bên/ủy quyền/xung đột nhãn vẫn mở (Q2).
- Pháp nhân không là Người; người dùng nhập tay. Bảng pháp nhân riêng là hướng tương lai, chưa duyệt/build. Có dữ kiện cá nhân đại diện thì giữ đúng Người đó; không suy quyền đại diện hay tự dựng lời ủy quyền. Alias nếu cần nhập tay, lời tư cách/căn cứ phức tạp D04 sửa tay; không mở fallback tay cho mọi gap.
- `chudat` là metadata Hồ sơ lấy lựa chọn Chủ `ownPositions` trên Diagram đã lưu, tài sản hiện có, loại hidden/deleted; tên snapshot Stage theo `personId`. Không lấy GCN/Bên A/slot `owner`/`owner_row_id` làm mặc định; Upload không Diagram thì null. Không biến tên `chudat` thành toàn bộ quan hệ pháp lý hoặc scope chi tiết.
- Snapshot của chính Hồ sơ là dữ kiện lịch sử; thay master hoặc Hồ sơ/module khác không tự ghi đè. Không ghi chéo DB, ghép Case hoặc tạo shared Case ID. #42 nhiều giấy tờ/địa chỉ độc lập, không là prerequisite.

Nguồn: ticket #43; decision owner §“Trả lời ma trận Nam Định”; SOT Nam Định §6–7; entities §8–9.4; lệnh tiếp tục mới nhất ở phiên hiện tại. Mục hai tầng “đang cân nhắc” trong tài liệu cũ là lịch sử trước lệnh chỉ trường tĩnh, không phải phương án tiếp tục.

## 2. Audit có giới hạn: đã có gì, chưa được chọn gì

| Nguồn đã đọc | Điều có căn cứ | Không được suy thành |
|---|---|---|
| `contracts/entities.md` §8.1–8.2; contract Notary §4.1 | Người có tên, sinh/chết, giấy tờ/ngày cấp, địa chỉ; snapshot/bằng chứng giấy tờ giữ nghĩa và độ đầy đủ ngày. Tên không là khóa | Mỗi lần xuất hiện/vai trò là một Người mới; Person hiện có đã hỗ trợ nhiều giấy/địa chỉ |
| Contract Notary §2.1, §13.2; `case_workspace.py:2768–2784` | Stage có dòng Người/Tài sản, identity riêng với vị trí; payload lưu snapshot từng Hồ sơ. Diagram `personId` trỏ dòng Người đã commit | Row/slot Diagram là model membership xuyên module đã duyệt; thiếu trên Diagram nghĩa là không thuộc Hồ sơ |
| Contract Notary §13.4–13.5; `inheritance_workspace.py:146–154,184–196` | Diagram hiện chặn một Người trên hai node active. Thừa kế có hai lựa chọn Chủ/Nhận độc lập theo vị trí tài sản; Hai bên không mang lựa chọn đó | Cấm nghiệp vụ một Người nhiều vai trò; cả nhóm A/B mặc nhiên liên quan toàn bộ tài sản; công thức thừa kế đã tính riêng mỗi tài sản |
| Contract Notary §13.3–13.4 | Tối đa 3 tài sản Stage, 20 cụm đất/tài sản; đổi thứ tự tài sản giữ dấu chọn theo số vị trí, có thể đổi tài sản được chọn; engine hiện coi di sản là một khối | Giới hạn nghiệp vụ toàn Upload, hoặc phép âm thầm chuyển dấu Diagram cũ sang bám identity |
| Contract Notary §8.1, §13.10; Word spec §2.3 | Word có giới hạn riêng 5 tài sản, 20 Người/ký thừa kế, 30 Người Hai bên; Người N theo Stage, Bên A/B theo ghế, không dồn ghế trống | Chọn giới hạn toàn hệ thống, dùng thứ tự ghế làm thứ tự requester mọi module, hoặc cắt raw vượt giới hạn |
| SOT Nam Định §6.1–6.2; `contract_extract.py:4950–4973` | Upload giữ `raw.ben_a`, `raw.ben_b`, `raw.nguoi_chet`, hàng `danh_sach_thua_dat`; nguồn hai bên có thứ tự và `entity_lines`. Các editor vẫn là output trình bày, chưa cutover Người/Asset/parties | Hai danh sách Người và thửa đã là các cặp; `entity_lines` là Person; đã có persistence quan hệ canonical |
| `contract_extract.py:4855–4880,4924–4946` | Legacy tách Người chết và lọc khỏi hai bên bằng tên/ngày sinh; requester ưu tiên B/fallback A, cam kết A | Quy tắc membership hay hợp nhất danh tính đã được owner duyệt. Đây là **xung đột consumer với R06**, không lấy union/dedup theo tên từ output cũ làm đáp án |
| Entities §9.2; contract §4.2, §13.3 | Một Tài sản giữ từng cụm loại đất–diện tích–thời hạn có thứ tự, kể cả vị trí trống. Serial có thể trùng ở nhiều thửa; snapshot tài sản thuộc Hồ sơ | Cụm loại đất là một thửa hoặc một Tài sản độc lập; cùng GCN thì gộp thửa; thời hạn lẻ được rải vào mọi cụm |
| Entities §9.4; `case_workspace.py:2785–2793` | Tám trường Case: `tenvanban`, `nhomhopdong`, `loaivanbannhandien`, `socongchung`, `ngaycongchung`, `congchungvien`, `thuky`, `chudat`; metadata được snapshot cùng Hồ sơ | Tám scalar đủ lưu membership/vai trò/scope, hoặc metadata BUILT là toàn #41 đã xong |
| SOT Nam Định §5.2, §7.2 | Catalog portal có nhóm có A/B và nhóm role metadata null; có văn bản một bên, ủy quyền không cần chữ nhận | Null nghĩa không có Người; nhãn nhóm portal là authority quan hệ của app; mọi loại đều đủ hai bên |

Đây là audit contract/spec và một số đoạn code tĩnh, không proof runtime hay khảo sát corpus. Không chọn cap Upload mới. Không cần owner trả lời ID, JSON, bảng nối, migration hoặc chi tiết renderer trong spike này.

## 3. Cách hiểu nghiệp vụ tối thiểu — đề xuất, chưa duyệt

1. **Người là ai:** dữ kiện nhận dạng của một cá nhân. Trùng tên không đủ gộp; cùng Người chỉ được tái dùng khi có căn cứ đã xác nhận, không nối Case tự động.
2. **Người có thuộc Hồ sơ không:** danh sách thành viên của chính Hồ sơ, có thứ tự và nguồn. Không đồng nhất với danh sách chữ được nhắc đến, ghế Diagram, người ký hay người yêu cầu theo heuristic cũ. R06 lấy toàn bộ danh sách này sau khi owner chốt nghĩa.
3. **Tham gia như thế nào:** mỗi lần/vai trò/nhóm có căn cứ, thứ tự trong nhóm và nguồn riêng; nhiều lần tham gia không nhân bản dữ kiện Người. Nhãn nguồn giữ lại để đối chiếu, không biến thành chức vụ prose trong R06.
4. **Tài sản có thuộc Hồ sơ không:** danh sách tài sản có thứ tự, giữ identity từng tài sản và snapshot. Mỗi tài sản giữ cụm đất có thứ tự riêng. Người đứng tên GCN là dữ kiện nguồn, không tự là Chủ Diagram.
5. **Ai liên quan phần nào:** ghi đúng ý nguồn/xác nhận: cả nhóm với cả tập tài sản; riêng cá nhân với tài sản cụ thể; hoặc những tập con khác nhau. Ghi rõ quan hệ đang nói đến (chuyển, nhận, được ủy quyền… khi có căn cứ), không nâng “liên quan” thành sở hữu hợp pháp. Không tính tỷ lệ, chia di sản hay dựng đồ thị pháp lý.
6. **Nguồn chưa nói gì:** giữ thiếu/chưa rõ/xung đột cùng nguồn; không biến thành “không liên quan”, cũng không thành “tất cả”. Giữ dữ kiện chắc chắn độc lập phần scope còn thiếu. Áp chính sách điền dần/partial đã có ở nơi nguồn đã trả lời; không đoán quan hệ hoặc tạo gate toàn Hồ sơ. Chỉ ghi câu hỏi nghiệp vụ riêng cho consumer nếu lúc triển khai thực sự có output bắt buộc chưa được policy hiện hành trả lời; không invent gate ở spike này.

Các cách tổ chức ở mục 2–5 là đề xuất, **không duyệt entity schema, cardinality hoặc cách lưu**; riêng việc bảo toàn đúng nghĩa scope nguồn ở mục 5 là bất biến đã yêu cầu, không chờ owner đồng ý lại. Thứ tự thành viên, thứ tự lần tham gia/nhóm, thứ tự tài sản và thứ tự cụm đất là các thứ tự khác nhau; renderer chỉ đọc đúng thứ tự được duyệt, không làm nguồn xác định quan hệ ngược lại.

### Kết luận bảo toàn có căn cứ — không chờ owner duyệt lại

- **Một Người, nhiều lần tham gia:** R06 lấy tập tất cả Người đã xác nhận, không tập lần xuất hiện. Mỗi identity cá nhân đã xác nhận xuất một lần trong requester; giữ đủ vai trò/lần tham gia và thứ tự nhóm riêng. Thứ tự theo danh sách/nguồn đã xác nhận (Notary theo Stage; Upload theo lần xuất hiện đầu tiên trong nguồn, không ưu tiên B hoặc container raw). Căn cứ: R06, AC1 không gộp/mất Người, contract §13.10 thứ tự Stage. Không dedup theo tên; chưa đủ căn cứ cùng Người thì giữ phân biệt/mơ hồ.
- **Quan hệ Upload mới bám đúng tài sản nguồn:** reorder chỉ đổi trình bày, không tự chuyển liên kết; thêm tài sản không tự sinh liên kết vào scope đã xác nhận. Căn cứ: AC2/D07 bảo toàn scope, identity khác vị trí và cấm suy Cartesian. Đây là kết luận bảo toàn dữ liệu/engineering cho luồng mới, không đòi owner chọn lại. **Không sửa** Diagram Notary legacy: `ownPositions` vẫn bám vị trí theo contract §13.3.
- **Thiếu scope:** giữ nguyên chưa rõ, dùng được dữ kiện độc lập theo chính sách điền dần hiện hành; không đoán liên kết, không mở fallback tay hoặc chặn toàn Hồ sơ mới. Căn cứ: spec nền §2 điền dần, AC2/AC5 và data-rules §4.2. Không mở consumer feature, schema hoặc contract mới từ các kết luận này.

## 4. Ma trận 16 tình huống tổng hợp

“Có căn cứ” dưới đây nghĩa là dữ kiện được đặt rõ trong tình huống, không phải code đã đọc được hoặc owner đã duyệt mô hình. Q1–Q2 trỏ hai câu hỏi ở §6; các kết luận bảo toàn ở §3 không là câu hỏi còn mở.

| Ca | Input: dữ kiện / nhóm nguồn | Câu hỏi quan hệ đích | Bất biến phải giữ | Khuyến nghị và phần chưa chọn |
|---|---|---|---|---|
| C01 · 1 Người–1 Tài sản | Hồ sơ 1 có Người 1 và Tài sản 1; nguồn nói rõ Người 1 có quan hệ với Tài sản 1, không nêu bên | Có đúng một thành viên và liên kết đã nêu, hay chỉ là hai đối tượng cùng xuất hiện? | Không tự tạo Người/Bên B thứ hai hoặc gán Chủ Diagram | Giữ liên kết có nguồn; không cần đồ thị. Nhóm chưa rõ theo Q2; một đối tượng mỗi loại tự nó chưa chứng minh quan hệ |
| C02 · 1 Người–nhiều Tài sản | Người 1; tài sản theo nguồn [Tài sản 2, Tài sản 1]; nguồn nói Người 1 chuyển cả hai | Phạm vi là tập hai tài sản, có thứ tự nào? | Không chỉ lấy tài sản đầu; không chuyển thứ tự thành identity | Giữ cả tập/thứ tự nguồn; reorder không đổi liên kết, thêm tài sản không tự mở scope theo kết luận §3, không owner gate |
| C03 · nhiều Người–1 Tài sản | Nhóm A theo nguồn [Người 2, Người 1] cùng chuyển Tài sản 1 | Hai Người cùng tham gia một việc, hay mỗi người có quyền/tỷ lệ riêng? | Giữ hai Người và thứ tự; không tự chia đôi hoặc suy vợ chồng | Giữ quan hệ chung có căn cứ, không thêm tỷ lệ; giữ thứ tự nguồn/danh sách đã xác nhận theo §3 |
| C04 · chung cả nhóm/cả tập | Nguồn nêu nhóm A [Người 1, Người 2] cùng chuyển tập [Tài sản 1, Tài sản 2] cho nhóm B [Người 3, Người 4], nhưng không phân quyền cá nhân | Cả nhóm tham gia với cả tập hay đã có bốn cặp cá nhân? | Không nhân thành quyền sở hữu riêng mỗi Người với mọi tài sản | Phải giữ phát biểu cấp nhóm–tập, không bung cặp; bất biến AC2/D07, không chờ duyệt lại |
| C05 · các cặp tách rời | Nguồn xác định Người 1→Tài sản 1; Người 2→Tài sản 2; hai Người cùng nhãn A | Có được gộp nhãn A thành A↔cả hai tài sản? | Không sinh Người 1→Tài sản 2 hoặc Người 2→Tài sản 1 | Phải giữ đúng hai cặp; cùng nhãn không làm mất scope, không chờ duyệt lại |
| C06 · tập con chồng nhau | Người 1 liên quan [Tài sản 1, Tài sản 2]; Người 2 chỉ Tài sản 2; Người 3 chỉ Tài sản 3; nguồn nói rõ | Phân biệt một phạm vi nhiều tài sản với các phạm vi hẹp thế nào? | Giữ giao nhau tại Tài sản 2, không gộp tất cả hoặc loại liên kết trùng đích | Phải giữ đúng các phạm vi nguồn; cách tổ chức tối thiểu còn PROPOSED, không graph engine/cap mới |
| C07 · không biết scope | Nguồn có A [Người 1, Người 2] và [Tài sản 1, Tài sản 2], không nói cặp hay phạm vi chung | Biết ai có mặt nhưng đã biết ai liên quan tài sản nào chưa? | Cùng xuất hiện không là tích Descartes; chưa rõ không là không có | Giữ hai danh sách/nguồn và scope chưa xác định; áp điền dần/partial có sẵn, không đoán và không thêm global gate |
| C08 · một Người nhiều vai trò | Có căn cứ xác nhận cùng Người 1 xuất hiện hai lần: tự mình với Tài sản 1, rồi đại diện Người 2 với Tài sản 2 | Một Người hay hai; giữ hai lần tham gia/nhóm ra sao; requester lặp mấy lần? | Không nhân bản Person hoặc mất lần tham gia; không suy quyền đại diện từ tên lặp | Một Người đã xác nhận xuất một lần ở R06; giữ đủ các lần tham gia/nguồn theo §3. Diagram một node active không cho phép mất vai trò hoặc nhân bản Người |
| C09 · trùng tên, khác Người | Người 1 và Người 2 có cùng giá trị tên minh họa, nguồn phân biệt rõ bằng dữ kiện riêng; cả hai cùng nhóm A | Hai cá nhân có bị dedup khi dựng requester/nhóm không? | Không gộp tên; giữ hai nguồn và hai dòng dù output tên giống nhau | Hai Người riêng, mỗi Người một dòng theo thứ tự nguồn/danh sách đã xác nhận. Không cần số CCCD giả để chứng minh |
| C10 · một GCN, nhiều thửa | GCN X được nêu cho hai hàng thửa khác nhau: Tài sản 1 và Tài sản 2; Tài sản 1 có hai cụm loại đất, Tài sản 2 có một cụm | Giấy chứng nhận, hàng thửa và cụm loại đất có phải cùng đơn vị không? | Không gộp vì serial; không tách hai cụm thành hai thửa; giữ đúng bộ ba và thứ tự từng tài sản | Giữ hai tài sản khi nguồn đã xác định hai hàng riêng, giữ GCN X trên từng nguồn; không tạo entity GCN mới. Scope chủ thể nếu nguồn chưa nêu vẫn chưa rõ |
| C11 · thay nguồn qua Hồ sơ | Hồ sơ 1 đã xác nhận Người 1 địa chỉ “Địa chỉ cũ”, Tài sản 1 hai cụm đất; Hồ sơ 2 có địa chỉ “Địa chỉ mới” và mô tả tài sản khác | Được sửa ngược Hồ sơ 1, chuyển vai trò/scope hoặc tự nối hai Case không? | Snapshot Hồ sơ 1 không đổi theo master/Hồ sơ 2/module khác; không tự đồng nhất hai Người chỉ vì cùng tên | Giữ từng snapshot và nguồn; sửa một Hồ sơ chỉ theo thao tác thuộc quyền của nó. Không đợi #42 để bảo toàn lịch sử |
| C12 · một bên | Văn bản cam kết chỉ nêu Người 1 và tài sản, không có bên đối ứng trong nguồn | Đưa Người 1 vào A, B hay giữ chưa gán? | Không tạo bên rỗng giả thành dữ kiện; R06 không phụ thuộc nhãn A/B | Đề xuất chỉ gán khi có căn cứ, không tạo B; nhóm một bên cần Q2, không áp universal “không nhận=A” |
| C13 · thừa kế/người chết | Nguồn có Người 1 đã chết, Người 2 là người nhận; nhắc Người 3 là thân nhân và Người 4 là thư ký; Diagram đã lưu chọn Chủ cho Người 2 trên Tài sản 1 | Ai thuộc Hồ sơ cho R06; người chết/thân nhân/nhân sự có tự vào membership không? | Không chỉ người sống/người ký; không suy `chudat` là Người 1 vì slot owner; không đưa thư ký vào Person tự động từ metadata | Chủ theo lựa chọn Diagram là nghĩa đã chốt; membership bốn trường hợp chờ Q1. Không dùng việc legacy lọc người chết khỏi hai bên để tự loại R06 |
| C14 · cá nhân đại diện + pháp nhân nhập tay | Nguồn nêu tổ chức “Tổ chức X” và dữ kiện Người 1 đại diện, Người 2 là khách; có Tài sản 1 | Cá nhân đại diện có thuộc Hồ sơ/R06, thuộc nhóm nào; thông tin tổ chức ở đâu? | Không biến Tổ chức X thành Person, không tự dựng chức vụ/quyền hoặc mặc định ngân hàng | Pháp nhân nhập tay đã chốt; dữ kiện cá nhân giữ chuẩn, membership Q1 và nhóm Q2. Authority prose D04 sửa tay, không tạo bảng pháp nhân |
| C15 · ủy quyền/nhãn xung đột | Nguồn 1 ghi “người ủy quyền” Người 1, “người được ủy quyền” Người 2 (không chữ nhận); nguồn 2 của cùng Hồ sơ đảo nhãn A/B | Dùng nguồn nào để xếp bên, có tự coi người được ủy quyền=B không? | Không dùng thiếu chữ nhận để gán A, không âm thầm chọn một nguồn thắng | Giữ nhãn/vị trí nguồn mâu thuẫn; đề xuất xác nhận nhóm trước output phụ thuộc nhóm. Q2, không dựng rule phân xử chưa duyệt |
| C16 · đổi thứ tự, không đổi tài sản | Nguồn xác nhận Người 1 liên quan Tài sản 1; danh sách từ [Tài sản 1, Tài sản 2] đổi thành [Tài sản 2, Tài sản 1] | Đổi chỗ trình bày có được tự đổi liên kết nguồn không? | Không áp ngầm nghĩa mới lên Diagram legacy: ở đó dấu chọn bám vị trí đã được duyệt | Upload mới giữ liên kết với Tài sản 1 theo kết luận bảo toàn §3; không owner gate, không sửa `ownPositions` Notary |

C04 khác C05 dù có cùng tập Người/Tài sản; C07 khác cả hai dù payload phẳng có thể giống nhau. C08 khác C09: nhiều lần của một cá nhân khác hai cá nhân trùng tên. C10 tách đúng ba nghĩa GCN/thửa/cụm đất; C13 tách người để lại/chủ Diagram/thành viên. Các khác biệt này phải còn đọc được sau khi trình bày thành chuỗi.

## 5. Phương án tối thiểu và đánh đổi

| Phương án nghiệp vụ | Giữ được gì / mất gì | Đánh giá |
|---|---|---|
| Chỉ danh sách Người + Tài sản của Hồ sơ và nhãn A/B | Đơn giản nhưng không phân biệt C04/C05/C06/C07 hoặc các lần tham gia C08 | **Không đạt AC2/D07 hiện hành**, không là phương án bình thường để owner chọn trong refinement này. Chỉ xem xét nếu có thay đổi phạm vi tương lai được owner yêu cầu rõ; không tự thu nhỏ #43 |
| **Danh sách thành viên trực tiếp + lần tham gia/nhóm + phạm vi liên quan tường minh** | Giữ các danh sách có thứ tự, cùng một Người nhiều vai trò, nhóm–tập khác cặp riêng; không rõ vẫn không rõ. Cần người dùng/nguồn xác định phạm vi thực sự, không tự suy | **Khuyến nghị PROPOSED.** Chỉ giữ những nghĩa có nguồn ở ma trận, không tạo hệ đồ thị, công thức, tính quyền/tỷ lệ hoặc loại quan hệ tùy biến. Chưa quyết định bảng/entity/FK |
| Chỉ lưu block raw/editor phẳng, dùng nó làm nghiệp vụ | Giữ nguyên văn được nhưng không bảo đảm identity, danh sách R06, thứ tự/nhóm/cặp hoặc cutover; dễ lấy lời prose thay dữ kiện | **Loại khỏi phương án đích** vì trái chuẩn hóa đã chốt, không phải vì bỏ raw. Raw/history/source_refs vẫn giữ nguyên để kiểm chứng |

Chọn phương án khuyến nghị không đồng nghĩa mọi liên kết cần tách từng cặp. Cả nhóm–cả tập giữ đúng cấp nhóm–tập; liên kết riêng chỉ có khi nguồn nói riêng. Placeholder chỉ là nơi điền dữ liệu, không định nghĩa quan hệ; không có template vẫn cần hiểu được Người/Tài sản/Hồ sơ. Đích hiện tại không có trường động/công thức/điều kiện cấu hình.

## 6. Hai câu hỏi thật sự cần owner trả lời

Mỗi khuyến nghị dưới đây vẫn **chưa được chọn**. Không hỏi lại policy R06/A-B/pháp nhân hoặc yêu cầu owner chọn cấu trúc kỹ thuật.

### Q1 — Ai thực sự được tính là “Người trong Hồ sơ”?

**Câu hỏi:** Trong ca C13–C14, xin chốt từng nhóm có thuộc danh sách R06 không: người chết có dữ kiện riêng; cá nhân đại diện; thân nhân chỉ được nhắc để giải thích; công chứng viên/thư ký chỉ xuất hiện với tư cách nhân sự xử lý? Có phải một người chỉ cần được nhắc tên trong văn bản là tự thuộc Hồ sơ không?

**Khuyến nghị:** Danh sách là những cá nhân được xác định là đối tượng của Hồ sơ; bao gồm người chết và đại diện khi họ là đối tượng, không tự biến mọi tên được nhắc hoặc metadata nhân sự thành thành viên. Trường hợp chỉ được nhắc giữ nguồn và cần xác định tư cách thành viên, không âm thầm loại hoặc thêm. R06 luôn lấy **toàn bộ** danh sách đã chốt, không thêm bộ lọc người sống/người ký.

**Đánh đổi:** Không lẫn nhân sự/nhắc tên vào requester, nhưng cần owner xác nhận ranh giới “đối tượng” bằng bốn nhóm trên. Không dùng cấu trúc parser để quyết định thay owner.

### Q2 — Ngoại lệ A/B: một bên, ủy quyền và nguồn trái nhau xử lý ra sao?

**Câu hỏi:** Với văn bản chỉ có Người 1 không nhãn bên (C12), có gán A không? Với người ủy quyền/được ủy quyền không chữ nhận (C15), có quy ước bên cố định không? Khi hai nguồn đảo A/B, xác nhận lại nhóm thay vì tự chọn có đúng không?

**Khuyến nghị:** Nguồn có A/B rõ thì dùng đúng; một bên không nhãn thì giữ chưa gán, không tự tạo B hay mặc định A; ủy quyền chỉ chuyển sang A/B theo quy ước nghiệp vụ owner chốt hoặc xác nhận cụ thể; xung đột giữ nguồn và chờ xác nhận **phần nhóm**, không thu hẹp requester. Output cần nhóm chưa rõ thì không điền lời gán nhóm chưa được xác nhận.

**Đánh đổi:** Không sai vai trò vì heuristic “nhận”, nhưng không hứa tự điền A/B cho mọi văn bản. Nếu owner muốn một bên luôn A hoặc ủy quyền cố định A/B thì cần trả lời rõ ngoại lệ này; không tự coi đó đã được D05 chọn.

## 7. Handoff và điều kiện khép spike

- Phần nguồn trả lời được đã hoàn thành: từ điển/identity, snapshot, quan hệ Diagram, raw Upload, metadata Case 8 trường, giới hạn module, R06 và các kết luận bảo toàn §3. Chỉ còn hai câu hỏi ở §6: membership và ngoại lệ A/B; không biến thứ tự/dedup identity/reorder/thêm tài sản hoặc thiếu scope thành owner gate mới.
- Chờ owner trả lời Q1–Q2; chỉ khi owner chấp nhận nghĩa/tình huống hoặc giới hạn mới cập nhật decision/spec/#41 qua parent. Proposal không tự là đáp án đã duyệt. AC4 vẫn chưa đạt; không nâng refined/built/done hoặc mở gate #41.
- Sau đáp án, #41 nhận danh sách nghĩa đã chốt cùng các ca C01–C16, nguồn, cách giữ thứ tự/phạm vi/chưa rõ và ranh giới snapshot. Sau đó mới chọn contract kỹ thuật; không tự mở schema/triển khai trong #43. Xung đột Diagram một node/vị trí và quan hệ mới cần được nêu rõ trước cutover consumer, không dựng shim hoặc sửa legacy token.
- Independent narrow review cuối CLEAN; mandatory BMAD Ticket validation PASS cho bản draft, **không phải closure**. Parent đã đọc đủ 16 tình huống, kết luận và hai câu hỏi, cho commit đúng ba file. Các gate tránh được đã chuyển thành kết luận bảo toàn có căn cứ; Q1 membership/Q2 ngoại lệ A/B vẫn chờ owner, AC4 chưa đạt. Không chạy runtime verification.

## 8. Nguồn tra cứu đã mở

- `_bmad-output/backlog/spike-case-people-assets-relationships.md` — Description, AC1–5, Boundaries.
- `_bmad-output/backlog/story-upload-business-field-standardization.md` — AC1–2, Boundaries; nơi tiếp nhận đáp án.
- `_bmad-output/backlog/story-person-multiple-identities-addresses.md` — Boundaries; không nhận trùng #42.
- `_bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md` — Trả lời ma trận Nam Định §7 (R06, D04–D08), phần cân nhắc hai tầng trước lệnh mới.
- `_bmad-output/specs/upload_lab/nam-dinh-website-sot.md` — §5.2, §6.1–6.3, §7.1–7.4.
- `_bmad-output/specs/shared/data-rules.md` — §4.2, quyền ghi/nguồn/snapshot và gate.
- `contracts/entities.md` — §8.1–8.2, §9.2–9.4.
- `contracts/notary-case-drafting.md` — §2.1, §4.1–4.2, §13.2–13.5, §13.10.
- `_bmad-output/specs/notary_v2/README.md` — context loại hồ sơ, Stage; `diagram-rules.md` §5, §8–9; `word-templates.md` §2.3.
- `graphify-out/GRAPH_REPORT.md` — Community 0, 3, 15, 22, 26, 34: bản đồ tìm nguồn, không authority nghiệp vụ.
- `notary_v2/services/case_workspace.py:2768–2793` — snapshot Người/Tài sản/Case; `inheritance_workspace.py:146–154,184–196` — ràng buộc node hiện tại.
- `tools/regex_workbench/engine/contract_extract.py:4855–4880,4924–4973` — output raw/case/web_form và heuristic legacy cần phân biệt với policy đích.

## 9. BMAD state và acceptance chưa nghiệm thu

AC1–3 đã có bảng đối chiếu để owner xem, chưa có đáp án owner cho phần còn mở.
AC4 chưa đạt: chưa owner chấp nhận, chưa tích hợp đáp án vào decision/spec/#41.
AC5 được giữ trong phạm vi lượt này; không có implementation hoặc runtime proof.
Không đánh dấu spike built/done hoặc refined chỉ vì đã viết proposal.

BMAD đã resolve output/config/store/customization, `find backlog 43` và `status
backlog` trước sửa: #43 đang backlog, không plan, `refined:false`, `hitl:true`,
không assignee. Loose-backlog waiver/active initiative unset được giữ. Resolver
báo thiếu record `bmod-method`; theo phạm vi giao không install/setup/config,
không dựng workflow thay thế. Đây là spike design, không gọi app build.

Parent đã duyệt commit đúng ticket, matching plan và dòng #43 backlog index sau independent review CLEAN; không push. Thiết kế vẫn PROPOSED, blocked chờ owner, refined:false/hitl:true. Parent tích hợp đáp án decision/spec/#41 sau khi owner trả lời; không có dependency bắt buộc vào tmp.
