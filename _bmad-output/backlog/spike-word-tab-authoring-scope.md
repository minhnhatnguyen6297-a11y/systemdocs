---
id: 19
type: spike
title: "Đặc tả tab Word tạo và lưu mẫu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Đặc tả tab Word tạo và lưu mẫu

## Description

Đặc tả flow tab Word riêng: nhập văn bản, đề xuất placeholder, tải về sửa, nhập lại và xác nhận lưu mẫu lâu dài. Owner chọn nguồn vào và cam kết giữ bố cục trước implementation; “nhập văn bản” chưa xác định chỉ chữ dán hay file DOCX. Khác nút Xuất Word hiện có.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C18
- source — _bmad-output/specs/notary_v2/word-templates.md, §6
- source — _bmad-output/specs/notary_v2/README.md, §6, §9
- source — _bmad-output/decisions/regex-decision-46.md, Decision 4
- source — _bmad-output/decisions/decision-regex-core-consumer-cutover-20261016.md, Quyết định
- source — _bmad-output/decisions/decision-owner-regex-rule-developer-only-20261016.md, Quyết định
- source — _bmad-output/backlog/spike-word-naming-authority.md, Notes
- evidence — _bmad-output/tmp/issue-19-word-authoring/evidence.md, ledger 17/10/2026

## Notes

- Tracking: C18; **owner answered 17/10/2026 — spike scope closed; tab authoring DEFERRED**, owner tự làm sau và cần spec kỹ trước implementation tương lai. Giữ Draft/`refined: false`, không built, không xóa leaf. [Decision](../decisions/decision-owner-word-authoring-deferred-20261017.md). Chuyển #20, không hỏi tiếp #19.
- Risk: medium — Tự chọn chỉ chữ dán có thể bỏ mất nhu cầu tái dùng mẫu DOCX; tự chọn giữ định dạng có thể hứa vượt phạm vi. Đây là spike đặc tả, không triển khai A hoặc B.
- Lịch sử câu hỏi nguồn/bố cục: coordinator **đã gửi** câu hỏi A/B sau công bố `169e4faf9dfa6f4f6373009cfb25640b66af4c10`; owner đáp: “chức năng này tôi sẽ tự làm sau, cần spec kỹ. Chuyển issue khác”. Đây là trả lời hoãn, **không chọn A/B**. Nguồn/bố cục, storage/catalog và nghiệm thu vẫn cần đặc tả sau, không còn gate hỏi owner lúc này. Ledger và đề xuất bên dưới giữ làm lịch sử, không phải scope được duyệt.

### Ledger nguồn — 17/10/2026

| Nội dung | Nguồn/thẩm quyền | Kết luận |
|---|---|---|
| Flow tab riêng | [Word §6](../specs/notary_v2/word-templates.md#6-tab-word-dự-kiến), dòng 454–456; [Notary §6](../specs/notary_v2/README.md#word), dòng 79–90 | Đã có ý định nhập văn bản → đề xuất → tải về chỉnh trong Word → nhập lại → xác nhận lưu mẫu lâu dài. Không phải original-DOCX intake hoặc nút Xuất Word. |
| Rule đề xuất | Word §6; [owner 06/10, Decision 4](../decisions/regex-decision-46.md), dòng 28–31; [cutover hiện hành](../decisions/decision-regex-core-consumer-cutover-20261016.md), dòng 10–14 | Dùng lõi regex chung. Lõi nhận Word/text không có nghĩa UI authoring đã chọn nhận cả hai; không có lựa chọn AI/cloud ở đây. |
| Token và số thứ tự | [Word §3.3](../specs/notary_v2/word-templates.md#33-quy-tắc-dữ-liệu), dòng 301–318; [§4.1](../specs/notary_v2/word-templates.md#41-quy-tắc-placeholder), dòng 374–406; [#10 Notes](spike-word-naming-authority.md#notes) | Mẫu mới `[Người N - Trường]` theo thứ tự Stage; Bên A/B theo ghế. Compact/alias cũ giữ slot legacy, không đổi số ngầm. Không hỏi lại cú pháp. |
| Sửa kết quả khác sửa rule | [owner 16/10](../decisions/decision-owner-regex-rule-developer-only-20261016.md), dòng 8–16 | Người dùng có thể kiểm tra/sửa kết quả và mẫu; không có UI thử/công bố/chọn phiên bản/rollback rule. Chi tiết kỹ thuật rule thuộc developer, không dựng role/version UI cho user. |
| Duyệt/tải/nhập lại | Word §6, dòng 456 | Sửa ngoài Word và xác nhận sau nhập lại đã có trong flow. Chưa chọn màn duyệt bắt buộc trước tải; không tự thêm gate này. |
| Nguồn và bố cục | Word §6, dòng 456; [Notary §9](../specs/notary_v2/README.md#9-tiêu-chí-kiểm-và-phần-chưa-chốt), dòng 108–115 | “Nhập văn bản” còn mơ hồ. Không tìm thấy lựa chọn authoring về chỉ chữ dán hay DOCX giữ bố cục trong tập spec/decision liên quan đã khảo sát; cần đúng một fork ở trên. |
| Catalog/lưu và tiêu chí phát hành | Word §6, dòng 456; [xuất hiện hành §3.2](../specs/notary_v2/word-templates.md#32-input-và-output), dòng 248–271 | Chưa được owner chốt cho tab authoring. Xuất hiện có dùng thư mục local, catalog backend cũ chỉ tương thích; không lấy đó làm quyết định kho mẫu authoring. Storage path, kiểm token/ghi file là kỹ thuật, không tự thêm câu hỏi nghiệp vụ hoặc framework quản lý mẫu. |

### Hai phương án và đề xuất — chưa được chấp thuận

- **A — Chỉ chữ dán/nhập:** sinh DOCX có placeholder rồi người dùng tự định dạng trong Word. Không mang theo bố cục bảng/ảnh/header/footer của file đang có. Lời “nhập văn bản” không chứng minh A đã được chọn; tự chọn A có thể cắt mất công việc thực tế.
- **B — Nhận DOCX hiện có và giữ bố cục:** tái dùng văn bản/mẫu Word văn phòng khi thay placeholder. Cần đặc tả phạm vi giữ định dạng và kiểm bằng Word thật sau khi owner chọn; không tự nhập các giới hạn của intake sang tab này. Phạm vi định dạng không hỗ trợ chỉ hỏi tiếp khi thực sự cần, không mở thêm checklist gate lúc này.
- **[INFERENCE] Khuyến nghị B** vì phù hợp nhu cầu biến mẫu Word đang có thành mẫu placeholder dùng được, nhưng **không phải lựa chọn cũ hoặc đáp án mới của owner**. Không tự chọn A/B, dựng UI giả hoặc triển khai feature trong spike.
- **Đề xuất kỹ thuật, chưa accepted:** mẫu lưu trong thư mục local người dùng chọn, nối đường export-folder hiện có; không thêm catalog quản trị, version/role/permission UI. Đây chưa phải phê duyệt storage/catalog. Không nâng câu hỏi đường dẫn/quyền OS/kiểm file thành business gate.
- **Tiêu chí đề xuất, chưa accepted:** hoàn thành vòng nhập → gợi ý → tải/sửa → nhập lại/xác nhận; mở lại vẫn dùng được mẫu đã lưu cho hồ sơ khác, đúng token/số thứ tự, không ghi đè nguồn. Nếu B được chọn, nghiệm thu giữ bố cục trong phạm vi được đặc tả bằng Word thật; không thay bằng kiểm token hay hứa giữ từng pixel. Không gọi vòng này là nghiệm thu đã có.

### Bên chờ, giới hạn và đúng ba AC

- **Ai chờ:** chỉ implementation authoring tương lai chờ lựa chọn nguồn/bố cục. Token, xuất Word hiện có và developer bảo trì core không chờ. [#9](spike-word-real-route-acceptance.md#notes) là bằng chứng xuất/restore và giới hạn native/visual; [#24](story-gradual-fill-word-readiness.md) là readiness xuất điền dần, không chứng minh authoring đã hoàn thành. Office vẫn DEFERRED, không giao thêm việc.
- **Nơi ghi đáp án hoãn:** [decision accepted](../decisions/decision-owner-word-authoring-deferred-20261017.md), Notes này và Word §6. Quyết định nguồn/bố cục chưa có; khi làm sau cần spec chi tiết, không tự viết/chọn trong lượt này.
- **AC1:** ledger trên đã phân biệt điều chọn sẵn, bằng chứng thiếu và hệ quả A/B có ngày. Đối chiếu nguồn chi tiết ở [evidence](../tmp/issue-19-word-authoring/evidence.md); không có phép đo hoặc nghiệm thu runtime mới.
- **AC2:** chỉ implementation authoring tương lai cần spec chi tiết và các lựa chọn chưa chốt; xuất/token hiện có không chờ. Owner đã hoãn nên không có việc authoring đang chờ thực hiện trong lượt này.
- **AC3 — nhận đáp án phạm vi 17/10/2026:** parent đã gửi câu hỏi; owner đã trả lời hoãn và tự làm sau, cần spec kỹ. Spike scope closed theo deferral, không phải nguồn/bố cục đã được trả lời hoặc tính năng được nghiệm thu. Giữ Draft/Pending và `refined: false`.
- **Independent DOC review — 17/10/2026:** retained `word-authoring-scope-review` Quick **t2 CLEAN — no actionable findings**, parent đã đọc toàn bộ scoped deferral diff. Review này áp cho quyết định hoãn và đồng bộ tài liệu, khác lượt CLEAN của gate cũ tại `169e4faf9dfa6f4f6373009cfb25640b66af4c10`. Phạm vi spike đã được owner trả lời bằng DEFERRED; không chứng minh nguồn/bố cục đã chọn hoặc feature built.
