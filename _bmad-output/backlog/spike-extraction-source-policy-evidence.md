---
id: 12
type: spike
title: "Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Đối chiếu nguồn mâu thuẫn, nhóm dữ liệu và các quy tắc OCR còn mở

## Description

Đối chiếu xung đột trích xuất và ranh nhóm bằng nguồn cụ thể với owner. Bao gồm chuẩn hóa/classifier/gộp ảnh OCR so với contract đầu ra. Bằng chứng chuyển một phần/bãi bỏ hành chính cùng ngày được theo dõi độc lập ở C26/#27.

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
- tracking — _bmad-output/backlog/README.md, C11
- source — _bmad-output/specs/shared/extraction-rules.md, §2.8, §4.4, §5–6, §8
- source — _bmad-output/specs/shared/ocr-rules.md, lines 11,15,59–63
- source — _bmad-output/implementation-artifacts/deferred-work.md, dòng 20–22,34–41
- source — _bmad-output/decisions/decision-owner-doc-clarifications-20261015.md, mục 11–12 đã chốt; phần ghi rõ chưa duyệt vẫn chưa duyệt

## Notes

- Tracking: C11; **investigation/evidence recorded 16/10/2026 — SOURCE GAP còn lại, không phải đáp án trường đã được duyệt**. AC của spike cho phép xác định bằng chứng thiếu; lượt điều tra đã ghi đủ phần lấy được và phần không lấy được, không gọi ground truth đã trả lời hoặc engine built. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Chọn ngầm nguồn hoặc gộp sai người/thửa có thể tạo dữ liệu nghiệp vụ sai dù schema hợp lệ.
- Người thực hiện/ngày: worker `extraction-policy-evidence`, nghiên cứu và ghi tài liệu 16/10/2026; không phải owner hoặc reviewer độc lập. Không có quyết định sản phẩm mới; không cần owner chọn thuật toán để kết thúc việc ghi bằng chứng của #12.

### Ledger nguồn canonical — 16/10/2026

| Câu hỏi / nguồn đã đọc | Điều đã rõ | Phần còn thiếu và hệ quả |
|---|---|---|
| P04/F04 — `upload_lab/tests/fixtures/word_field_cases.json:309–312`; [spec §2.8, §6.3](../specs/shared/extraction-rules.md) | Đầu vào cùng thửa **211/tờ 9**, `210 m2` rồi `210,0 m2`: khác chữ raw nhưng cùng độ lớn, **chưa chứng minh hai tổng thực sự khác**. Owner đã chốt khối liên tục + cặp thửa/tờ; giữ nguồn, không tự bỏ lần nhắc. | Fixture vẫn `pending_decision`, không có filename/hash/vị trí hồ sơ thật hay expected độc lập. Cần đúng nguồn F04 có tổng trái nhau hoặc chứng minh chỉ khác cách viết; không tự duyệt số bản ghi/giá trị của fixture. |
| P05/F05 — cùng fixture, dòng 315–318; [spec §2.8, §6.3](../specs/shared/extraction-rules.md) | `Thửa đất số: 211`, hai dòng `40 / CLN / 12/2043` và `40 / CLN / 12/2063 / thuộc quyền sử dụng riêng`. Bộ loại–diện tích–thời hạn theo DB đã chọn; không tự lấy 2063 hoặc cộng thành 80. | Không có tờ/nhãn sửa đổi/nguồn thật để biết **hai cụm độc lập hay hai phiên bản cùng cụm**. Chọn hai cụm có thể đếm đôi; chọn một phiên bản có thể bỏ thời hạn đúng. Chưa chọn đáp án hoặc thuật toán gộp; giữ Pending. |
| Provenance F04/F05 — [decision-75](../decisions/decision-75-regex-integration.md), dòng 14–22; lịch sử được dẫn từ spec: `archive/specs-before-consolidation-20261015/upload_lab/regex-fields.md` §8–9 → `regex-expected-results.md` §3–4; TASK-10.1 tại `archive/backlog/tasks/` | Chuỗi nguồn lịch sử cũng giữ Pending. Decision-75 ghi corpus cá nhân ở máy/worktree gốc, không commit; TASK-10.1 Done không duyệt F04/F05. Decision-73 thân rỗng không phải ruling. | Các thư mục được dẫn `.agents/task-10.1/`, `.agents/review-sweep-20261007/`, `.agents/review-viewpoint-20261007/` không có trong checkout; tìm đúng tên trong archive và `chau.provenance.json` không có kết quả. R01-real/s283 chỉ kiểm Người, không trả lời Tài sản. Không dựng filename/hash hoặc đáp án thất lạc. |
| Ca Word đọc trực tiếp — `tmp/issue-22-regex-consumer-cutover/evidence/notary/after/inputs/gcn-multi-parcel.docx`, dòng trích 9–21; provenance nhãn độc lập #22 §8 | Fixture tổng hợp có thửa **10/tờ 5**: đất ở **200,0 m²/Lâu dài**, đất trồng cây lâu năm **247,0 m²/12/2043**, không tổng riêng. Hai loại đất khác nhau không phải xung đột P05; không suy tổng 447,0. | Corpus #22 không có hai tổng trái nhau hoặc chi tiết lặp mâu thuẫn. Family `F4-inheritance-partition.docx`/`F5-inheritance-refusal.docx` không phải P04/F04/P05/F05; không lấy tên family làm nguồn thật của Pending. |
| Nhóm nhiều nguồn/editor tách–gộp — [Word §2.2](../specs/notary_v2/word-templates.md); [deferred-work](../implementation-artifacts/deferred-work.md), dòng 34–41; [plan DOCX](../implementation-artifacts/plan-multica-docx-intake.md), phần giới hạn corpus | Hiện giữ nguồn và `ambiguous_group`, nhiều giá trị phải chọn/sửa trước nhận; trùng giấy tờ/serial chỉ cảnh báo, không tự gộp. Chưa có hợp đồng thật chứng minh cần editor; deferred là lịch sử thiếu phép đo, không tự mở scope. | Người thao tác/labeler cần ca ranh nhóm sai thật và nhóm đúng độc lập trước khi đề xuất luật/editor mới; không có lựa chọn sản phẩm mới đủ bằng chứng ở lượt này. |
| Gộp ảnh OCR — [OCR](../specs/shared/ocr-rules.md), dòng 15,171–207 | Chọn ngày mới hơn/recompute diện tích là mô tả parser cũ cần đối chiếu, không tự áp sang Word hoặc coi là phê duyệt quy tắc mới giữ nguồn. Qwen-only; `chu_su_dung` chưa có đích persist. | Chưa có cặp ảnh gốc có filename/hash/trang và đáp án field/group mâu thuẫn trong nguồn được dẫn; không tự duyệt gộp ảnh, thêm OCR local/QR rescue hoặc persist trường mới. |
| Chuẩn hóa tiếng Việt — cùng OCR, dòng 11 | Giữ raw; sửa có xác suất chỉ là gợi ý, không tự thêm dấu tên rồi coi là dữ kiện. Từ điển/thuật toán cuối chưa chốt. | Không có ca ảnh + đáp án độc lập để chọn quy tắc mới; phần chưa duyệt giữ nguyên, không hỏi owner chọn thuật toán thay bằng chứng đo. |
| Classifier fallback — cùng OCR, dòng 59–63; decision-72/[clarifications](../decisions/decision-owner-doc-clarifications-20261015.md) | Fallback ≥2/8 strong fields ghi rõ **non-normative**, không là contract đã duyệt; decision-72 bảng đơn dòng vẫn proposed/chưa duyệt. | Không có positive/negative source-ground-truth để giữ/đổi fallback; không nâng Draft/Pending từ mô tả hoặc output hiện có. |
| Hiện trạng #22 — [leaf built](story-shared-regex-consumer-cutover.md), Notes; [decision cutover](../decisions/decision-regex-core-consumer-cutover-20261016.md), dòng 17–31 | Record #22 đã đóng raw serial/NFD/spans, cụm nhiều dòng, detail so với scalar và ambiguity thật (MB1–MB9); vẫn không duyệt F04/F05. | Không mở lại lỗi đã built thành câu hỏi owner. Các số liệu/runtime #22 là bằng chứng có sẵn, **không phải lượt chạy mới của #12**. |

### Bên chờ và giao bằng chứng — 16/10/2026

- **Người thao tác/người giữ nguồn:** cung cấp đúng Word/ảnh gốc F04/F05, filename + hash + trang/đoạn/node của mỗi giá trị; **labeler độc lập** ghi số bản ghi, tổng, từng cụm loại–diện tích–thời hạn và ghi chú/quan hệ phiên bản trước khi xem output. Với OCR/nhóm, chỉ bổ sung ca sai cụ thể và đáp án field/group có nguồn; không yêu cầu một corpus hoặc chính sách rộng chưa xác định.
- **Developer:** chỉ thay luật/đáp án phụ thuộc phần ground truth này mới chờ nguồn. Giữ raw/không tự gộp, bộ trường DB đã chọn, recognition-only sổ tiết kiệm/bảo hiểm và sửa #22 đã built không chờ. Hành chính cùng ngày #27 và việc độc lập không bị #12 chặn.
- **Owner:** hiện không có lựa chọn nghiệp vụ mới đủ bằng chứng; không yêu cầu chọn thuật toán, threshold hoặc đoán 2043/2063 từ fixture. Nếu tài liệu thật sau đọc độc lập vẫn có hai nghĩa nghiệp vụ, mới đưa đúng ví dụ và hệ quả hai cụm/hai phiên bản để chọn. Không nâng sửa xác suất thành dữ kiện, không OCR local/QR rescue, không thêm đích persist `chu_su_dung`.
- **Nơi ghi đáp án:** ledger bền vững tại Notes này. Chỉ khi có nguồn/đáp án đủ mới bổ sung spec bóc tách §6 và fixture; nếu thực sự phát sinh quyết định sản phẩm mới thì ghi decision/spec cùng phiên, **không tạo decision mới cho lượt điều tra này**. Bằng chứng chi tiết tạm: [evidence](../tmp/issue-12-extraction-policy/evidence.md), [static ledger](../tmp/issue-12-extraction-policy/static-ledger.json); Notes này đủ giữ kết luận khi tmp không được lưu.
- **Independent Quick — CLEAN 16/10/2026:** reviewer `extraction-policy-review` không có actionable findings; parent đã đọc diff leaf thực tế và evidence, chấp nhận kết quả. Phạm vi là ledger tài liệu, trạng thái Pending/Draft, bên chờ và giới hạn kết luận; ghi nhận thiếu nguồn dựa trên record điều tra, không chạy lại tìm kiếm hoặc nghiệm thu runtime. Chỉ điều tra/bằng chứng hoàn tất; **F04/F05 vẫn Pending, chưa duyệt đáp án hoặc thuật toán mới**. Lượt authoring chỉ đọc tài liệu/JSON và một DOCX tổng hợp; không chạy app/test/code, không có runtime proof mới.
