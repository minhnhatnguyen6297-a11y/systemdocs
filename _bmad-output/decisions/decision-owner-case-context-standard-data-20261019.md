---
id: decision-owner-case-context-standard-data-20261019
title: "Owner chốt trục Người–Tài sản–Hồ sơ và context hồ sơ tại D:\\testcase"
date: '2026-10-19'
status: accepted
---

## Nguồn và quyền thực hiện

Owner dừng triển khai corpus trong hội thoại, nguyên văn:

> D:\testcase đây là folder tôi đã chuẩn bị, chưa làm vội, tôi cần thiết lập 1 số định hướng trước khi bạn tự chạy triển khai

Sau đó owner cho ghi **tài liệu/context/README**, yêu cầu quy tắc toàn hệ thống vào AGENTS. Các mục bên dưới là ghi lại nội dung chỉ dẫn trong hội thoại, không trình bày phần diễn giải là nguyên văn. Ngày ghi theo đồng hồ máy đã đọc: 19/10/2026.

## Quyết định toàn hệ thống

- Mọi luồng nghiệp vụ xoay quanh **Người, Tài sản, Hồ sơ**. Mỗi đối tượng có bộ trường canonical đã duyệt; chức năng dùng dữ liệu chuẩn hóa đó. Mọi input nghiệp vụ sau chuẩn hóa phải ánh xạ vào đúng trường chuẩn, mọi output nghiệp vụ dùng đúng trường, kiểu, định dạng và cách nhóm. Không để dữ liệu nghiệp vụ mồ côi, không nhét khác nghĩa vào ghi chú, không tự thêm trường/alias hoặc dựng schema theo từng văn bản.
- Bộ trường cố định đối với lần triển khai không cấm mở rộng được duyệt sau này. Nếu chưa có mapping hoặc cần trường mới thì giữ phần phụ thuộc pending, ghi issue để owner chốt nghiệp vụ/schema sau và tiếp tục file đã rõ; không đoán thay, không dừng cả lô.
- File/chữ raw, bằng chứng và `source_refs` vẫn là provenance kỹ thuật phải giữ nguyên; không buộc raw mang schema DB và không biến chúng thành entity nghiệp vụ mới. Không tạo Case chung hoặc quyền tích hợp liên module từ quy tắc này.
- Chuẩn trường/ánh xạ hiện có theo [entities](../../contracts/entities.md), [contract theo module](../../contracts/README.md) và [quy tắc dữ liệu](../specs/shared/data-rules.md). Không sửa contract hoặc code trong lượt ghi định hướng.

## Context từng nhóm owner nêu

| Nhóm | Quy tắc đã ghi nhận |
|---|---|
| 1. Chuyển nhượng | Hai bên. |
| 2. Đặt cọc | Hai bên. |
| 3. Di chúc | Pháp lý đơn phương; nghiệp vụ hệ thống bố trí hai bên vì có người nhận. Nguyên văn owner: **“Người nhận tài sản theo di chúc có vị trí khác so với các văn bản khác”**. Context là cấu trúc văn bản: tìm vùng/người nhận và mapping từ mẫu thực trước. Chưa có vị trí cụ thể; không suy đây là quyết định về ghế Diagram hoặc tự biến thành câu hỏi chọn slot. |
| 4. Thuê đất, vay tiền, ủy quyền, tặng cho, văn bản cam kết | Nhóm hai bên thông thường. |
| 5. Mua bán ô tô/xe máy | Hai bên; bộ trường Tài sản và biến thể xe chưa chọn. **Tạo issue để sau, hiện không làm ca này.** Không sinh field hoặc dữ liệu xe. |
| 6. Thế chấp | Nội dung ngân hàng cung cấp; văn phòng **chỉ soạn lời chứng**. Input **luôn thiếu thông tin tài sản** theo hướng dẫn này, không chỉ đôi khi; không tự bịa tài sản bảo đảm hoặc soạn thay cả hợp đồng. |
| 7. Thừa kế | Bộ phụ có thể gồm từ chối nhận di sản, cử đại diện, thông báo niêm yết và tài liệu khác theo hồ sơ. Đây không phải checklist pháp lý khép kín hoặc xác nhận tất cả tài liệu là bắt buộc. |

Đây là phân loại nghiệp vụ được owner định hướng, **không phải nghiệm thu runtime hoặc phê duyệt enum/schema mới**. Runtime hiện vẫn chỉ có sáu `document_type`: `khai_nhan`, `thoa_thuan`, `chuyen_nhuong`, `tang_cho`, `cho_thue`, `dat_coc`, thuộc hai domain hiện có. Nhận diện regex không đồng nghĩa tạo/sửa/xuất được hồ sơ. Không đổi catalog, bỏ gate thiếu tài sản, hoặc dùng enum không đúng nghĩa để giả lập hỗ trợ Di chúc/thế chấp/xe.

## Văn bản phụ điển hình

- **Ủy quyền cho người của văn phòng đi làm cho khách**; không mặc định người nhận ủy quyền là khách hoặc bên giao dịch.
- **Đơn đăng ký thường dùng Mẫu 18**, ghi công việc đề nghị cơ quan nhà nước giải quyết. Không tự suy tên pháp lý đầy đủ, phiên bản hoặc bộ trường mẫu chưa được cung cấp.
- **Bộ khai thuế gồm ba loại khi đổi chủ sử dụng**. Tên và mẫu cụ thể của ba loại **chưa được owner cung cấp**; không tự đoán, không sinh biểu mẫu.
- Danh sách điển hình không biến thành yêu cầu pháp lý bắt buộc cho mọi hồ sơ, không chứng minh regex/OCR hỗ trợ tất cả giấy tờ phụ. Vai trò văn bản chính, văn bản phụ và cách sử dụng dữ liệu phải được ghi trong context khi owner cho làm tiếp.

## Folder, giới hạn và bản nháp cũ

- Folder owner chọn là **`D:\testcase`**, có README chung để agents đọc trước; context từng nhóm được ghi trực tiếp trong [README Notary](../specs/notary_v2/README.md#context-ho-so-thu). AGENTS dẫn tới hai điểm đọc này.
- Lượt này **chỉ tài liệu**: chưa sinh Word/corpus, không chạy parser/app/test/E2E hoặc bắt đầu đọc mẫu/sửa code; chờ chỉ dẫn tiếp của owner, không coi README mới là quyền tự triển khai. Tài liệu repo đã review được commit/push theo chỉ dẫn hiện hành; không đưa nguồn khách hàng hoặc tài liệu ngoài repo lên Git.
- Đề xuất mười bundle tại `_bmad-output/tmp/e2e-canonical-corpus/research-design.md`, kế hoạch authoring cũ và `testdata/notary-e2e/v1/authoring.json` được viết trước lệnh dừng **không còn là chỉ dẫn triển khai được duyệt**. Đặc biệt: đề xuất hợp đồng thế chấp đầy đủ kèm tài sản và địa điểm corpus trong repo đã bị định hướng mới thay thế. Chúng không phải corpus chuẩn, không có DOCX đã tạo trong lượt đó; giữ nguyên, không tự sửa/xóa/move sang D:\testcase.
- Chưa cung cấp vị trí cụ thể của người nhận trong **cấu trúc Di chúc**, bộ trường/biến thể xe, tên/mẫu ba loại thuế, phiên bản/nội dung chi tiết Mẫu 18 hoặc tiêu chuẩn so sánh Word. LLM cần đọc mẫu thực trước để nhận diện cấu trúc/mapping; phần không tự quyết được ghi issue và tiếp tục file đã rõ, không tự chọn ghế Diagram, nghiệp vụ hoặc tuyên bố giống từng trang/byte.
- Việc xe được ghi riêng ở [#29](../backlog/spike-vehicle-sale-case-scope.md), **DEFERRED / refined:false**. Không mở lại #14 Office, #19 tab Word, #20 Danh sách hồ sơ, #27 nguồn thời gian; #18 vẫn REMOVED, không dùng lại ID.
- Chỉ dẫn tiếp cùng ngày xác lập **LLM đọc hàng loạt mẫu → nhận diện cấu trúc → so code → điều chỉnh code → test lại, sai thì lặp** và mục tiêu xuất đủ, đúng thông tin hợp đồng. Cấu trúc chưa chốt có issue riêng; văn bản lạ vào issue tổng hợp để owner xem sau, không dừng vòng trên các file đã rõ. [Quyết định quy trình](decision-owner-sample-first-iteration-20261019.md). Đây chưa phải lệnh bắt đầu đọc mẫu/sửa code/test trong lượt tài liệu này.

## Đồng bộ tài liệu

AGENTS; nền sản phẩm; shared/data-rules; README Notary; Word spec; sổ tay và một hàng backlog xe. Việc ghi tài liệu không tạo mới capability, field, hồ sơ thử, fixture hay bằng chứng E2E.
