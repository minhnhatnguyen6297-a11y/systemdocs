---
id: 1
type: bug
title: "Flow Soạn hồ sơ khó thao tác, khó kiểm tra regex và khó tìm mẫu Word"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: high
severity: P2
---

# Flow Soạn hồ sơ khó thao tác, khó kiểm tra regex và khó tìm mẫu Word

> **Tracking-only — 15/10/2026:** yêu cầu mới của owner là gom thành nhiều issue và đề xuất thứ tự. [Catalog hiện hành](README.md) ánh xạ C01–C27 / #2–#28; #11 và #26 được giữ lịch sử ở trạng thái dropped, #28 là draft cutover; các ghi nhận phía dưới không là một lượt implementation song song. Không coi việc tách issue là đã sửa hoặc nghiệm thu hành vi. Quyết định: `_bmad-output/decisions/decision-issues-reconciliation-20261015.md` và `_bmad-output/decisions/decision-upload-web-sot-without-save-tracking.md`. 16/10/2026: rule regex văn bản và rule upload theo website do developer quản lý — AC10 dưới đây chỉ còn lịch sử; xem catalog C07/C22 và [decision](../decisions/decision-owner-regex-rule-developer-only-20261016.md). Các cách diễn đạt lịch sử về quy tắc — "sửa quy tắc dần khi test" (Description), "chỉnh quy tắc rồi chạy lại" (AC6) và "chỉnh được khi test" (Notes 13/10) — được hiểu là developer chỉnh/thử rule, không phải tính năng người dùng có UI; luồng người dùng thật vẫn dùng regex core chung và xem/sửa kết quả bóc tách trước khi nhận vào Stage.

## Description

Người dùng gặp ô Địa chỉ chứa hai trường khác nghĩa, không đổi được loại hồ sơ đã lưu, vùng Pool/Sơ đồ chật và ô thả người dẹt. Người dùng không cần nút Hủy thay đổi, cần dùng regex core chung ngay trong flow nhập thực tế và sửa quy tắc dần khi test, đồng thời biết mẫu Word có placeholder ở đâu. Tổng hợp thành một ticket để đánh giá thiết kế toàn flow, đối chiếu specs/docs và sửa đồng bộ thay vì vá từng report.

## Reproduction

### Sáu report giao diện

Môi trường báo cáo: Electron qua `run-dev.bat`, Notary mock, engine ready, viewport 1920×983. Report là JSON và ảnh wireframe, không phải screenshot chứa chữ/dữ liệu thật.

1. `18ae1083`: tạo hồ sơ Thừa kế, thêm Người, nhập địa chỉ và ngày mất. Ô Địa chỉ xuất hiện thêm dòng nơi cấp giấy khai tử. Mong đợi: hai ý nghĩa có nhãn/vị trí riêng, không trông như hai địa chỉ trong một ô.
2. `d9da640e`: mở hồ sơ đã lưu. Loại việc Thừa kế/Hai bên chỉ là nhãn, không sửa được. Mong đợi owner: cho phép đổi loại; quy tắc chuyển dữ liệu và sơ đồ cần chốt trước implementation.
3. `e86a02bb`: mở sơ đồ Hai bên và kéo người từ Pool tới ô trống. Người báo ô nhỏ, dẹt, khó thả; yêu cầu ngắn hơn 30%, cao hơn 100%. Vùng chọn là danh sách một bên 288×446, không phải rect của một ô; chưa có bằng chứng một lần drop bị xử lý sai.
4. `802bd69e`: vùng canvas được chọn 1603×484. Owner yêu cầu tăng chiều dài vùng Sơ đồ + Pool thêm 50%; cần làm rõ mục tiêu chiều cao và cách cuộn trên màn thấp.
5. `2c232a28`: nội dung Pool được chọn rộng 160px. Owner yêu cầu tăng độ rộng 40%; cần phân biệt nội dung với khung ngoài.
6. `b54184b3`: toolbar có nút Hủy thay đổi. Owner yêu cầu bỏ nút và code chỉ phục vụ chức năng này.

### Regex và Word

7. Fixture: `_bmad-output/tmp/notary-flow-remediation/runtime-synthetic/synthetic-transfer.docx`. Cách tái hiện qua UI, chưa thực hiện trong phiên này: mở Soạn hồ sơ → Nhập file → chọn fixture → xem gợi ý Tài sản trước khi duyệt vào Stage; đối chiếu serial `TEST-001` và dòng `Địa chỉ thửa đất: xã Mẫu, tỉnh Mẫu;` trong nguồn. Bằng chứng đã chạy là intake service và core trực tiếp: hai Người/một Tài sản được trích, serial/địa chỉ trả `missing`, không có lỗi runtime. Setup/lời gọi tương đương được ghi tại assessment-plan §8. Editor độc lập cho chạy rule sửa trong ô soạn, nhưng chưa công bố rule đó để flow nhập dùng.
8. Đi tới Xuất Word. Dialog yêu cầu tự chọn thư mục mẫu, không dẫn tới mẫu đi kèm hoặc catalog placeholder. Thư viện ngoài có 17 DOCX và 5 DOC; folder mode hiện chỉ quét DOCX trực tiếp. File nguồn đã tìm thấy, chưa có bằng chứng bị di chuyển.

## Cause Hypothesis

Bố cục ưu tiên mật độ dữ liệu nhưng ghép trường khác nghĩa và làm vùng thao tác hẹp. Loại hồ sơ bất biến (đã có ngoại lệ chuyển loại đã lưu, owner 16/10/2026 — [decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)) và Hủy thay đổi là contract cũ trái yêu cầu mới. Notary nhập DOCX đã dùng core chung, nhưng matcher vẫn giới hạn serial/nhãn địa chỉ; Upload Lab và tool test còn dùng engine cũ; editor chưa publish vào nguồn rule của app. Word có nhiều nguồn mẫu nhưng dialog không dẫn tới vị trí/catalog và catalog thiếu nhóm Hai bên.

## Acceptance Criteria

1. **Một flow và một nguồn hành vi rõ ràng**
   **Given** sáu report cùng yêu cầu regex và Word
   **When** đối chiếu hiện trạng, thiết kế và các spec/contract liên quan
   **Then** từng vấn đề có kết luận, thiết kế đích, nguồn cần cập nhật và bằng chứng nghiệm thu; không bỏ mục vì đang đúng contract cũ.
2. **Trường địa chỉ không lẫn nơi cấp**
   **Given** người sống, người có ngày mất hoặc có dữ liệu nơi cấp cũ
   **When** mở và sửa hồ sơ
   **Then** người dùng phân biệt và sửa được đúng trường; lưu/mở lại không mất địa chỉ hoặc nơi cấp.
3. **Chuyển loại hồ sơ theo quy tắc đã duyệt**
   **Given** hồ sơ đã lưu, có hoặc chưa có sơ đồ và có dữ liệu chưa lưu
   **When** đổi giữa Thừa kế và Hai bên theo phương án owner chốt
   **Then** kết quả đúng quy tắc chuyển đổi; không mất Người/Tài sản, không giữ tham chiếu sơ đồ sai domain và không ghi nửa chừng khi xung đột hoặc thất bại.
4. **Vùng thao tác đủ dùng**
   **Given** layout đích được duyệt ở viewport/DPI quy định và danh sách người dài
   **When** dùng Pool, kéo/thả người và gán bằng bàn phím
   **Then** kích thước, cuộn và nhãn đúng thiết kế; target không bị che; thả vào ô trống và hoán đổi ô đã có người đúng kết quả.
5. **Bỏ Hủy thay đổi đúng phạm vi**
   **Given** hồ sơ có thay đổi chưa lưu
   **When** thao tác toolbar, đổi tab hoặc đóng cửa sổ
   **Then** không còn hành động Hủy thay đổi trên toolbar; tín hiệu dirty và cảnh báo rời/đóng vẫn bảo vệ dữ liệu.
6. **Regex chung được dùng và test trong flow thật**
   **Given** bộ tài liệu thử có đáp án độc lập và quy tắc chung
   **When** nhập tài liệu qua các flow nằm trong phạm vi và chỉnh quy tắc rồi chạy lại
   **Then** kết quả phản ánh cùng core/rule đã chọn, có bằng chứng nguồn đúng; gợi ý chưa được duyệt không tự ghi vào Stage hoặc DB; kết quả cũ không bị áp vào sai nội dung.
7. **Người dùng tìm và dùng đúng mẫu Word**
   **Given** mẫu sẵn có, mẫu tùy chỉnh hoặc thư mục mẫu và hồ sơ đủ dữ liệu
   **When** chọn mẫu, mở vị trí/catalog rồi xuất Word
   **Then** biết nguồn/file mẫu thực sự dùng, tìm được placeholder hỗ trợ, mở được kết quả đúng dữ liệu; không ghi đè mẫu gốc. Thiếu mẫu hoặc placeholder không hỗ trợ có thông báo đúng nguyên nhân.
8. **Kiểm chứng và đồng bộ trước đóng ticket**
   **Given** thay đổi cuối đã hoàn tất
   **When** chạy flow nhập → duyệt → lưu → gán sơ đồ → xuất Word cùng các regression hành vi liên quan
   **Then** đạt các tiêu chí trên, specs/contracts/docs không còn chỉ dẫn trái hành vi mới và reviewer độc lập không còn finding cản nghiệm thu. Kết luận không cần sửa chỉ hợp lệ cho mục đã chứng minh hành vi mong đợi thực sự đạt, không dùng để bỏ yêu cầu mới của owner.

9. **Trích đúng raw và không mất coverage khi dùng core chung**
   **Given** tài liệu thử có serial không theo mẫu hai chữ-sáu số, nhãn địa chỉ khác nhau, người chỉ có năm sinh, Lời chứng và loại văn bản từng được hỗ trợ
   **When** chạy qua Notary, Upload Lab và tool kiểm tra sau cutover
   **Then** đáp án đúng nguồn/spec, serial giữ nguyên, năm sinh không bị thêm ngày, Lời chứng không thành đương sự; loại chưa hỗ trợ báo đúng trạng thái và Pending không bị đổi thành Approved theo kết quả máy.
10. **Rule công bố và chạy lại có hiệu lực, có bảo vệ dữ liệu**
    **Given** rule draft đã thử và nguồn đã có gợi ý hoặc Stage được duyệt
    **When** công bố version mới rồi chạy lại trong flow
    **Then** các consumer dùng cùng version/hash, cache không trả kết quả cũ; người dùng thấy khác biệt trước áp dụng; evidence/binding cũ không bị âm thầm chuyển sang kết quả mới và Stage không tự đổi.

## Boundaries

- Giữ flow Input → gợi ý chờ duyệt → Stage → Pool → Diagram → Word.
- Giữ revision, write nguyên tử, raw nguồn, slot ổn định và cảnh báo dữ liệu chưa lưu.
- Không tự suy giới tính, vai trò, quan hệ pháp lý hoặc sửa đáp án theo máy.
- Không đổi thư viện Word nguồn của owner hoặc coi file bên ngoài repo là tài nguyên đã đóng gói.
- Bỏ Hủy thay đổi trên toolbar không đồng nghĩa bỏ Hủy xuất, hủy dialog hoặc bảo vệ khi đóng app.

## References

- parent — none
- decision — `_bmad-output/decisions/decision-notary-flow-consolidated-remediation.md`
- product — `_bmad-output/specs/notary_v2/README.md`, §1–§5
- UI — `_bmad-output/specs/ui/README.md`, §2–§5
- layout — `_bmad-output/specs/notary_v2/visual-reference.md`, §1, §3, §6, §9
- wire — `contracts/notary-case-drafting.md`, §13.5
- reports — `_bmad-output/tmp/visual-bug-reporting/reports/`, sáu UUID nêu tại Reproduction
- design proposal — `_bmad-output/tmp/notary-flow-remediation/assessment-plan.md`, §1 và §5
- visual proposal — `_bmad-output/tmp/notary-flow-remediation/plan.packed.html`
- regex source — `_bmad-output/specs/upload_lab/regex-core.md`, §6–§7
- DOCX source — `_bmad-output/specs/notary_v2/input/docx-import.md`, quy tắc nguồn và core
- Word source — `_bmad-output/specs/notary_v2/word-output.md`, §3–§4
- placeholder reference — `notary_v2/word_templates/placeholder_mapping.md`
- runtime evidence — `_bmad-output/tmp/notary-flow-remediation/runtime-synthetic/intake-result.json`, `core-result.json`, `word/word-result.json`

## Notes

- Decision: 2026-10-13 — owner yêu cầu một ticket tổng, đánh giá thiết kế và đối chiếu tài liệu trước sửa đồng bộ; regex phải dùng trong flow thật và chỉnh được khi test; cần tìm mẫu Word có placeholder.
- Risk: high vì chuyển loại hồ sơ và thay nguồn trích xuất có thể làm sai snapshot/sơ đồ/Word. Kiểm tra ngoài tiêu chí ticket: người kiểm tra độc lập đối chiếu Word xuất với tài liệu thử và dữ liệu hồ sơ sau khi mở lại.
- Unknown (đã đóng 16/10/2026): quy tắc chuyển loại hồ sơ đã lưu đã chốt ở #3 ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md)); #25 chưa built.
- Open question: tỷ lệ kích thước report áp vào target thực hay toàn vùng khoanh; thiết kế cần minh họa và xác nhận trước implementation.
- Decision: 2026-10-13 — giữ một ticket theo yêu cầu owner; các chặng khảo sát, thiết kế, sửa và nghiệm thu nằm trong ticket này, không tự tách thành các ticket khác.
- Source conflict (đã giải 16/10/2026): loại hồ sơ immutable theo Q8 nhưng report yêu cầu sửa sau lưu — đã có ngoại lệ chuyển loại đã duyệt ([decision](../decisions/decision-owner-saved-case-type-conversion-20261016.md), contract §13.18).
- Source conflict: bố cục ghi bỏ ô nơi cấp, tính năng tra cứu/code lại cho sửa trong ô Địa chỉ; cần vị trí có nghĩa riêng.
- Source conflict: spec core cho serial nguyên văn nhưng matcher hiện chỉ nhận format hẹp; smoke đã cho thấy mất serial.
- Evidence: intake service thật succeeded, 2 Người/1 Tài sản, profile transfer1.1.2; trace core xác nhận serial/địa chỉ missing; Word service thật saved Synthetic_HS-99.docx với dữ liệu đúng, hash mẫu không đổi. Không coi các smoke này là full flow Electron hoặc installer đã đạt.
- Notes: core hiện hữu được owner định vị tại `tools/regex_workbench/engine/`; proposal không tạo core thứ hai. Đường thư viện mẫu đã tìm thấy: `C:/Users/MINH/OneDrive/Desktop/2. Mẫu thừa kế/`; catalog hiện hành trong `notary_v2/word_templates/placeholder_mapping.md`. Không hard-code đường máy này vào app.
- Review: single-ticket check độc lập đã bao phủ toàn scope; finding P2 về fixture và sự khác nhau giữa tái hiện UI/bằng chứng service được chấp nhận và sửa trong Reproduction #7. Không coi review draft là approval hoặc nghiệm thu implementation.

- Decision: 2026-10-15 — yêu cầu nhiều issue thay riêng lựa chọn giữ một ticket ngày 13/10. Giữ ID/filename/nội dung lịch sử #1; dùng catalog hiện hành và các leaf để theo dõi thực thi, không chạy #1 cùng leaf. #1 giữ trạng thái chưa hoàn tất và bị chặn tracking-only.
- Current sources: `_bmad-output/specs/notary_v2/README.md`, `diagram-rules.md`, `word-templates.md`; `_bmad-output/specs/shared/extraction-rules.md`; `_bmad-output/backlog/README.md`. Các đường cũ phía trên là nguồn lịch sử, không khôi phục spec archive thành hiện hành.
