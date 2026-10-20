---
title: "Làm rõ quan hệ nhiều Người–nhiều Tài sản trong Hồ sơ"
ticket: 43
status: done
---

# #43 — Đề xuất nghiệp vụ quan hệ Người–Tài sản trong Hồ sơ

**Artifact bền vững:** nội dung thiết kế PROPOSED nằm đầy đủ ngay trong plan này. Bản tmp chỉ là bằng chứng làm việc tùy chọn, không là nguồn bắt buộc hoặc spec đã áp dụng.

**Trạng thái:** phân tích đủ16ca, Q1/Q2/BANKMODE đã trả lời và bàn giao #41.
Không ownerblock; BANKMODE “app tự lấy”. Phân tích **done/refined:true** theo
quyền parent sau fresh bank-auto review CLEAN/mandatory Ticket PASS AC1–5.
Hitl:true giữ lịch sử đáp án owner; không duyệt schema hoặc hoàn tất #41.

Đây là kết quả điều tra/refinement D06+D07, không contract/schema quan hệ.
Lượt docs chỉ dùng tình huống tổng hợp (`Người 1`, `Tài sản 1`, `GCN X`),
không PII/mẫu thật/parser/app/browser/test/DB. Lệnh owner mới cho phép triển
khai riêng slice requester/ngân hàng #41 theo §6.1; không docs-only freeze,
không hoàn thành #41 hoặc mở gate mẫu.

## 1. Phần đã chốt — không hỏi lại

- Lệnh owner mới nhất: **chỉ placeholder và trường tĩnh**. Không thiết kế tầng 2 đoạn động, formula engine hoặc điều kiện cho người dùng cấu hình. Đoạn trình bày có thể điền từ các trường/tham chiếu đã được duyệt; việc đó không tự duyệt trường văn bản canonical mới. Không xóa hoặc đổi nghĩa các block token Word legacy đang hoạt động.
- Mọi luồng dựa trên Người–Tài sản–Hồ sơ; quan hệ là nghĩa thuộc Hồ sơ, độc lập bố cục Word/editor. Cùng xuất hiện không chứng minh có liên kết. Không suy tích mọi Người × mọi Tài sản; không gộp theo tên hoặc serial.
- **Bảo toàn nghĩa scope là yêu cầu đã có** ở ticket AC2/SOT D07, không hỏi duyệt lại: cả nhóm–cả tập (C04), từng cặp riêng (C05), tập con chồng nhau (C06) và chưa rõ (C07) phải phân biệt. Không bung nhóm–tập thành quyền cá nhân, không biến chưa rõ thành tất cả/không có. Không đặt gate output toàn cục vì scope chưa rõ.
- **Q1 đã trả lời — requester Nam Định/Upload:** cá nhân sống A/B/đại diện
  theo ủy quyền vào output; người chết/CCV/nhân viên không vào output đó.
  Không xóa Person chết/Stage/Hồ sơ thừa kế/raw/history/metadata nhân sự.
  Cá nhân chuẩn, không prose/lookup/firstperson; không thêm thân nhân chỉ nhắc.
  Ngân hàng **chỉ thế chấp** hiện cả cụm, không Person; BANKMODE **app tự lấy**
  theo §6.1, không legal field mới. Alias/D04/D08 cá nhân khác giữ policy cũ.
- **Q2 đã trả lời:** ủy quyền A=ủy quyền/B=được ủy quyền; một bên không gán;
  nguồn trái nhau giữ conflict/xác nhận phần nhóm, không winner/thu hẹp
  requester. “Nhận” không universal regex. Pháp nhân vẫn không thuộc Person;
  policy nhập tay chung đã có ngoại lệ ngân hàng thế chấp app tự lấy; cá nhân khác vẫn chuẩn.
- A/B trong scope requester là tư cách nguồn, không tag filter: cá nhân sống
  tham gia văn bản một bên/đại diện ủy quyền vẫn vào requester khi nhóm không
  gán hoặc conflict. Giữ requester độc lập nhãn nhóm, không hỏi lại owner.
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
2. **Membership khác requester:** giữ mọi đối tượng/nguồn hợp lệ của Hồ sơ; output requester Nam Định chỉ scope §1 đã trả lời, không xóa Người chết khỏi Stage/Hồ sơ thừa kế/snapshot.
3. **Tham gia như thế nào:** mỗi lần/vai trò/nhóm có căn cứ, thứ tự trong nhóm và nguồn riêng; nhiều lần tham gia không nhân bản dữ kiện Người. Nhãn nguồn giữ lại để đối chiếu, không biến thành chức vụ prose trong R06.
4. **Tài sản có thuộc Hồ sơ không:** danh sách tài sản có thứ tự, giữ identity từng tài sản và snapshot. Mỗi tài sản giữ cụm đất có thứ tự riêng. Người đứng tên GCN là dữ kiện nguồn, không tự là Chủ Diagram.
5. **Ai liên quan phần nào:** ghi đúng ý nguồn/xác nhận: cả nhóm với cả tập tài sản; riêng cá nhân với tài sản cụ thể; hoặc những tập con khác nhau. Ghi rõ quan hệ đang nói đến (chuyển, nhận, được ủy quyền… khi có căn cứ), không nâng “liên quan” thành sở hữu hợp pháp. Không tính tỷ lệ, chia di sản hay dựng đồ thị pháp lý.
6. **Nguồn chưa nói gì:** giữ thiếu/chưa rõ/xung đột cùng nguồn; không biến thành “không liên quan”, cũng không thành “tất cả”. Giữ dữ kiện chắc chắn độc lập phần scope còn thiếu. Áp chính sách điền dần/partial đã có ở nơi nguồn đã trả lời; không đoán quan hệ hoặc tạo gate toàn Hồ sơ. Chỉ ghi câu hỏi nghiệp vụ riêng cho consumer nếu lúc triển khai thực sự có output bắt buộc chưa được policy hiện hành trả lời; không invent gate ở spike này.

Các cách tổ chức ở mục 2–5 là đề xuất, **không duyệt entity schema, cardinality hoặc cách lưu**; riêng việc bảo toàn đúng nghĩa scope nguồn ở mục 5 là bất biến đã yêu cầu, không chờ owner đồng ý lại. Thứ tự thành viên, thứ tự lần tham gia/nhóm, thứ tự tài sản và thứ tự cụm đất là các thứ tự khác nhau; renderer chỉ đọc đúng thứ tự được duyệt, không làm nguồn xác định quan hệ ngược lại.

### Kết luận bảo toàn có căn cứ — không chờ owner duyệt lại

- **Một Người, nhiều lần tham gia:** trong tập cá nhân thuộc scope requester đã trả lời, mỗi identity xác nhận một lần theo nguồn/danh sách; giữ đủ các lần tham gia riêng, không dedup tên/ưu tiên B/container raw. Căn cứ R06/AC1/contract §13.10; Notary Stage không đổi, ngân hàng cả cụm không Person giả.
- **Quan hệ Upload mới bám đúng tài sản nguồn:** reorder chỉ đổi trình bày, không tự chuyển liên kết; thêm tài sản không tự sinh liên kết vào scope đã xác nhận. Căn cứ: AC2/D07 bảo toàn scope, identity khác vị trí và cấm suy Cartesian. Đây là kết luận bảo toàn dữ liệu/engineering cho luồng mới, không đòi owner chọn lại. **Không sửa** Diagram Notary legacy: `ownPositions` vẫn bám vị trí theo contract §13.3.
- **Thiếu scope:** giữ nguyên chưa rõ, dùng được dữ kiện độc lập theo chính sách điền dần hiện hành; không đoán liên kết, không mở fallback tay hoặc chặn toàn Hồ sơ mới. Căn cứ: spec nền §2 điền dần, AC2/AC5 và data-rules §4.2. Không mở consumer feature, schema hoặc contract mới từ các kết luận này.

## 4. Ma trận 16 tình huống tổng hợp

Các ca tổng hợp không proof runtime. Q1/Q2/BANKMODE ở §6 đã đủ đáp án; giữ nguyên đủ C01–C16. Bảo toàn §3 không là câu hỏi mở.

| Ca | Input: dữ kiện / nhóm nguồn | Câu hỏi quan hệ đích | Bất biến phải giữ | Khuyến nghị và phần chưa chọn |
|---|---|---|---|---|
| C01 · 1 Người–1 Tài sản | Hồ sơ có Người 1, Tài sản 1 và quan hệ nguồn, không nhãn bên | Một bên có gán A/B? | Không tạo Người/Bên B giả hoặc Chủ Diagram | **Q2 đã trả lời:** không gán A/B, giữ quan hệ nguồn |
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
| C12 · một bên | Cam kết chỉ nêu Người 1 và tài sản | Có gán A/B? | Không tạo bên đối ứng; requester độc lập nhóm | **Đã trả lời:** không gán gì, không default A/fake B |
| C13 · thừa kế/người chết | Người 1 chết; Người 2 nhận; Người 3 chỉ nhắc là thân nhân; Người 4 thư ký; Diagram chọn Chủ Người 2 | Ai vào requester? | Không xóa Person chết/estate snapshot; Chủ vẫn theo Diagram | **Q1 đã trả lời:** không Người 1/4 vào requester; tên thân nhân không tự tạo đối tượng output. Cá nhân sống A/B/ủy quyền dùng chuẩn |
| C14 · đại diện + ngân hàng | Ngân hàng, Người 1 đại diện theo ủy quyền và Người 2 khách sống; Tài sản 1 | Person/requester/cụm tổ chức có cùng nghĩa? | Không Person giả/quyền đại diện/field/default cụm | **BANKMODE app tự lấy** toàn cụm ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/ủy quyền có nguồn chỉ thế chấp; tại vị trí nguồn trong requester đầy đủ có Người 2 chuẩn, không lặp Người 1 đã trong cụm; JSON projection hợp lệ, không canonical field mới |
| C15 · ủy quyền/nguồn trái nhau | Người 1 ủy quyền, Người 2 được ủy quyền; hai nguồn đảo A/B | Gán nhóm/phân xử nguồn? | Không regex “nhận”, không winner/đổi requester | **Q2 đã trả lời:** A=ủy quyền/B=được ủy quyền; conflict/xác nhận phần nhóm bị ảnh hưởng |
| C16 · đổi thứ tự, không đổi tài sản | Nguồn xác nhận Người 1 liên quan Tài sản 1; danh sách từ [Tài sản 1, Tài sản 2] đổi thành [Tài sản 2, Tài sản 1] | Đổi chỗ trình bày có được tự đổi liên kết nguồn không? | Không áp ngầm nghĩa mới lên Diagram legacy: ở đó dấu chọn bám vị trí đã được duyệt | Upload mới giữ liên kết với Tài sản 1 theo kết luận bảo toàn §3; không owner gate, không sửa `ownPositions` Notary |

C04 khác C05 dù có cùng tập Người/Tài sản; C07 khác cả hai dù payload phẳng có thể giống nhau. C08 khác C09: nhiều lần của một cá nhân khác hai cá nhân trùng tên. C10 tách đúng ba nghĩa GCN/thửa/cụm đất; C13 tách người để lại/chủ Diagram/thành viên. Các khác biệt này phải còn đọc được sau khi trình bày thành chuỗi.

## 5. Phương án tối thiểu và đánh đổi

| Phương án nghiệp vụ | Giữ được gì / mất gì | Đánh giá |
|---|---|---|
| Chỉ danh sách Người + Tài sản của Hồ sơ và nhãn A/B | Đơn giản nhưng không phân biệt C04/C05/C06/C07 hoặc các lần tham gia C08 | **Không đạt AC2/D07 hiện hành**, không là phương án bình thường để owner chọn trong refinement này. Chỉ xem xét nếu có thay đổi phạm vi tương lai được owner yêu cầu rõ; không tự thu nhỏ #43 |
| **Danh sách thành viên trực tiếp + lần tham gia/nhóm + phạm vi liên quan tường minh** | Giữ các danh sách có thứ tự, cùng một Người nhiều vai trò, nhóm–tập khác cặp riêng; không rõ vẫn không rõ. Cần người dùng/nguồn xác định phạm vi thực sự, không tự suy | **Khuyến nghị PROPOSED.** Chỉ giữ những nghĩa có nguồn ở ma trận, không tạo hệ đồ thị, công thức, tính quyền/tỷ lệ hoặc loại quan hệ tùy biến. Chưa quyết định bảng/entity/FK |
| Chỉ lưu block raw/editor phẳng, dùng nó làm nghiệp vụ | Giữ nguyên văn nhưng không bảo đảm identity/quan hệ/cutover; dễ thay dữ kiện bằng prose | **Loại khỏi model canonical đích**, không loại persistence projection output hiện có: cụm ngân hàng thế chấp §6.1 là ngoại lệ text tĩnh có nguồn được duyệt. Raw/history/source_refs giữ nguyên |

Chọn phương án khuyến nghị không đồng nghĩa mọi liên kết cần tách từng cặp. Cả nhóm–cả tập giữ đúng cấp nhóm–tập; liên kết riêng chỉ có khi nguồn nói riêng. Placeholder chỉ là nơi điền dữ liệu, không định nghĩa quan hệ; không có template vẫn cần hiểu được Người/Tài sản/Hồ sơ. Đích hiện tại không có trường động/công thức/điều kiện cấu hình.

## 6. Đáp án đầy đủ — Q1/Q2/BANKMODE FINAL

**Q1 đã trả lời:** requester Nam Định/Upload gồm cá nhân sống A/B/đại diện
theo ủy quyền; không người chết/CCV/nhân viên trong output đó. Giữ Person
chết/Stage/Hồ sơ thừa kế/raw/snapshot/history. Ngân hàng thế chấp hiện cả
cụm, không Person. Nguyên văn đầy đủ tại decision “Đáp án #43”.

**Q2 đã trả lời:** ủy quyền A=ủy quyền/B=được ủy quyền; một bên không gán;
nguồn trái nhau giữ conflict/xác nhận phần nhóm, không winner/thu hẹp requester.
Không hỏi lại Q1/Q2, identity/thứ tự/reorder/add hoặc chi tiết kỹ thuật.

**BANKMODE đã trả lời — nguyên văn “app tự lấy”.** App tự lấy toàn cụm ngân
hàng có nguồn **chỉ thế chấp** và điền requester, không user-paste-only.
Đáp án cuối decision là authority; quote requester/A-B trước đó giữ nguyên.
Đây là output text tĩnh có nguồn qua đường hiện có, không pháp nhân Person/
canonical field/bảng mới. Cá nhân khác chuẩn; không blanket raw ba editor,
manual fallback mọi gap hoặc D04/D08/alias auto cho cá nhân. Không còn bank
clarification. W05 và A09-A đã chốt; các pending ngoài #43 giữ nguyên.

### 6.1 Kế hoạch triển khai có giới hạn — ghi trước sửa code

Owner đã chốt BANKMODE **“app tự lấy”** và giao tiếp tục slice runtime #41.
Mapping dùng đường có sẵn: nguồn văn bản → `web_form.nguoi_yeu_cau` →
payload JSON hiện có → queue reader/builder → editor requester Nam Định.
Persist projection text này là hợp lệ; không phải canonical Person/Asset/parties
hoặc hoàn tất normalized cutover #41, không thêm key/bảng/entity nghiệp vụ.

- Requester đầy đủ gồm mọi cá nhân sống thực sự tham gia/đại diện ủy quyền:
  block dữ kiện chuẩn theo **thứ tự nguồn**, không chỉ ngân hàng hoặc chỉ B.
  Văn bản một bên/nhóm chưa gán/conflict vẫn giữ tập requester; người chết,
  CCV/nhân viên và thân nhân chỉ được nhắc không vào output.
- **Chỉ hợp đồng thế chấp:** lấy nguyên cụm ngân hàng có nguồn, gồm ngân hàng/
  chi nhánh, định danh, địa chỉ, đại diện và căn cứ ủy quyền được nêu; giữ vị trí
  cụm trong thứ tự nguồn. Không xuất trùng đại diện đã nằm trong cụm ngân hàng.
  Ngoại lệ này không mở job/kinship/role prose, alias auto hoặc D04/D08 cho cá
  nhân khác; không kéo phần tài sản, giá/cọc/vay/lãi/thanh toán/thời hạn nghiệp vụ.
- Giữ nguyên raw, person arrays, provenance và payload lịch sử. Source refs kỹ
  thuật theo convention có sẵn được phép, không thành trường canonical mới.
  Queue không được lấy requester stale ngân hàng-only/firstperson ghi đè output
  đầy đủ mới; editor nhận chính projection đã chọn qua consumer hiện có.
- Runtime tổng hợp/cô lập đã chạy: nguồn → parser → JSON save → fresh queue/
  form builder → actual `_fill_editor` trên contenteditable local `about:blank`.
  Cụm ngân hàng đủ, A/B sống giữ thứ tự nguồn, đại diện một lần; loại staff/dead/
  prose, không tài sản/loan/payment, Save=0/Submit=0. Evidence tại
  `_bmad-output/tmp/issue-43-bank-smoke-result.json`; không portal/network/
  customer/corpus/production DB hoặc chạm phiên browser đã đăng nhập.
  #41 mở/gate mẫu ĐÓNG; W05 và A09-A đã chốt; phần quan hệ canonical chưa chốt giữ nguyên.

## 7. Handoff và điều kiện khép spike

- Phân tích đủ16ca và kết luận bảo toàn hoàn tất; Q1/Q2/BANKMODE đủ đáp án,
  decision/spec/#41 cùng dẫn đáp án cuối 20/10/2026. **AC4 owner-answer/handoff
  đã có**, không chờ bank owner hoặc model kỹ thuật; normalized #41 chưa xong.
- Fresh bank-auto review CLEAN, mandatory Ticket PASS AC1–5; parent cho
  transition completed-analysis done/refined:true. Không dùng review cũ cho
  latest-auto; proof hiện tại250pass0skip28subtests/local smoke0fail đã đọc.
  #41 normalized cutover vẫn mở/gate mẫu ĐÓNG. Delta bank đã parent đọc và
  commit `cb303f6`; A07 là slice #41 tiếp theo, đã land/verified/commit cùng slice.

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

## 9. BMAD state và acceptance của phân tích

AC1–2: đủ16ca C01–C16/§3 giữ identity/membership/thứ tự/vai trò/scope/history.
AC3: §1/§6 đủ Q1/Q2/BANKMODE và ranh giới projection ngân hàng chỉ thế chấp.
AC4: owner đã trả lời đủ; decision/spec/#41 dẫn cùng đáp án ngày 20/10/2026,
handoff đã ghi, không còn ownerblock. Đây không duyệt schema quan hệ hoặc đóng #41.
AC5: lượt spike/docs không implementation/runtime; §6.1 chỉ lập kế hoạch trước
code cho slice #41 đã được giao riêng, không mở gate mẫu.
Proof bounded #41 có, fresh latest-auto review CLEAN/Ticket PASS; #43 phân tích
done theo quyền parent, refined:true/hitl:true. Không ownerblock hoặc technicalgate.

BMAD đã resolve output/config/store/customization, `find backlog 43` và `status
backlog` trước sửa: #43 đang backlog, không plan, `refined:false`, `hitl:true`,
không assignee. Loose-backlog waiver/active initiative unset được giữ. Resolver
báo thiếu record `bmod-method`; theo phạm vi giao không install/setup/config,
không dựng workflow thay thế. Đây là spike design, không gọi app build.

Proposal/model trước đáp án giữ làm lịch sử thiết kế, không schema áp dụng.
Fresh latest-auto review CLEAN/Ticket PASS hiện tại bao phủ delta16path và
final semantic smoke hash8b503e7f/930f1fa5; delta bank đã commit `cb303f6`.
A07 `nguon_goc` là slice #41 riêng, đã land/verified/commit; #41 vẫn mở/gate mẫu ĐÓNG.

### Kết quả implementation/proof của slice #41, không toàn #41

- Parser output version `2026-10-20-requester-bank-projection` dựng requester
  từ canonical personfacts và cụm ngân hàng mortgage-only với technical source
  spans. Queue giữ đúng projection đã persist; lookup override/dead helper đã bỏ.
- Biên ngân hàng có hồi quy direct CCV/staff không cần `LỜI CHỨNG` và loan terms
  cùng dòng tên ngân hàng; không nuốt EOF/transaction text. Requester lấy source
  participants trước legacy raw-display filter để không loại người sống trùng
  tên người chết thiếu ngày sinh; không đổi raw/Person/history cũ.
- Final isolated five-suite sau bỏ đúng hai test fixture ngoài repo theo parent:
  **250 passed,0 skipped,28 subtests passed**, gồm5 browsercases với process-only CASE_FIELDS_CHROMIUM riêng; echo test đã bỏ, contradictoryDOB consumer regression giữ.
  Actual controlled pipeline smoke0fail/Save0/Submit0/about:blank; source hashes
  ở result. Lượt trước không gọi wholly synthetic: fixture-access possibility
  **[INFERENCE] từ skip count**, không probe lại hoặc claim nội dung/coverage.
  Giữ mọi fixture, chỉ bỏ hai methods. Fresh auto review CLEAN/Ticket PASS.


### A04 + quan hệ Person–Asset–Case — PROPOSED, chưa duyệt

Nguồn: audit kỹ thuật độc lập HEAD `b383031`; artifact tạm
`_bmad-output/tmp/canonical-area-relationships-proposal.md` chỉ là đề xuất, không
phải contract publish.

- **A04 total area:** `properties.dien_tich` đã có; `asset_row`/v2 + allowlist
  backend/UI đang thiếu. Đề xuất thêm đúng key `dien_tich` top-level (number/null,
  source total), input optional/preserve, server emit always; `land_rows[].dien_tich`
  giữ riêng/order; không sum, không copy, không backfill; precision qua
  `dien_tich_thanh_so`. Đây là technical add của scalar đã có nghĩa, cần contract
  approval trước code; `upload.workflow.v1` DRAFT không authority.
- **Quan hệ:** đề xuất optional `participation` trong Case snapshot, dùng
  `person_row_id`/`asset_row_id`; một record = một occurrence/group statement,
  `asset_set|unknown`, `source_group`, `role`, `sequence`, `source_refs`; C04
  group-set một record, C05 pairs riêng, C06 overlap nhiều record, C07 unknown
  không edge, C08 repeated person nhiều occurrence, C09 same name/serial khác
  row_id, C16 reorder giữ link. Không Person thứ tư/FK/shared ID; không Cartesian/
  name-serial dedup/inverse. `source_group`/`role` là vocabulary đề xuất, chưa
  duyệt enum; nếu emit wire phải version contract mới, hiện chỉ snapshot/raw.
- **Không thay đổi** contract/schema/writer trong slice A09/deceased; không
  self-publish Draft. Đây là proposal cho #41, không phải owner business question
  mới.
