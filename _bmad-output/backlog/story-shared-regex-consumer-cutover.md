---
id: 22
type: story
title: "Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi"
parent: none
covers: []
after: [7]
assignee: ""
refined: true
hitl: false
risk: high
status: built
completed: '2026-10-16'
---

# Dùng lõi regex chung cho các consumer sau khi giữ đủ hành vi

## Description

Hoàn tất hướng core chung đã duyệt cho consumer Notary, Upload và tool nhân viên thực tế. Chứng minh parity phạm vi hỗ trợ trước cutover, bỏ bản extraction/copy cũ sau chuyển, không giữ dual engine lâu dài.

## Acceptance Criteria

1. **Parity consumer**
   **Given** đáp án gán nhãn độc lập cho từng consumer/loại văn bản hỗ trợ
   **When** chạy qua entry point thực
   **Then** field/nhóm/cảnh báo/unsupported/Pending đúng đáp án, gồm serial nguyên văn/năm riêng và không tạo người Lời chứng
2. **Một core có hiệu lực**
   **Given** consumer đã chuyển cùng ranh rule writable/package
   **When** chuyên viên nhập Word/text hoặc dùng tool
   **Then** cùng core/rule identity có hiệu lực, mapping adapter rõ, không chép engine tay hoặc giữ fallback lâu dài
3. **Không giảm coverage âm thầm**
   **Given** nguồn hỗ trợ, file lỗi và ca ngoài phạm vi/Pending
   **When** batch/intake/tool xử lý
   **Then** giữ kết quả nguồn hợp lệ, báo lỗi từng nguồn, Pending không thành Approved chỉ vì có output

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Thực thi dưới uỷ quyền liên tục của owner; không thêm gate duyệt rule cho người dùng.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C21
- source — _bmad-output/specs/shared/extraction-rules.md, §1, §5–§8
- source — _bmad-output/specs/notary_v2/word-templates.md, §2.2
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §2

## Notes

- Tracking: C21; **built 16/10/2026**. #1 chỉ tracking, không chạy cùng leaf.
- Một đường luật `tools/regex_workbench/engine/contract_extract.py` cho Notary/Upload/tool; adapter giữ IO/mapping và source refs. Bản extraction/copy cũ và pipeline JSON profile đã gỡ sau parity; dev Workbench UI giữ và gọi lõi thật (chỉ editor profile lỗi thời bị bỏ).
- #7 đã hoàn tất trước cutover để tuần tự sửa core. Rule regex văn bản/rule upload theo website do developer quản lý, có version identity; không UI thử/công bố/chọn phiên bản/rollback cho người dùng. #23 giữ **superseded** theo [quyết định owner](../decisions/decision-owner-regex-rule-developer-only-20261016.md).
- Review độc lập: retained Quick t1 phát hiện Q1–Q7 → các vòng vá và adjudication MB1–MB9 → **retained Quick final multiline recheck clean 16Oct**; parent chấp nhận, mọi finding/residual đã đóng. Review cuối là read-only scoped recheck, không phải lượt reviewer chạy test.
- Bằng chứng cuối: workbench **53 passed, 6 subtests**; intake + Word-first **130 passed, 2 subtests**, thêm guard chuyển nhóm **1 passed**; Upload bounded **11 passed, 9 subtests**. Full Notary **1139 passed, 2 skipped** là lượt trước round 5–7, không phải full suite trên source cuối.
- So API theo nhãn đóng băng + 16 đính chính: **828 trường khớp / 0 lệch**, **44 null + 256 shape chưa kiểm**; F10/F11 unreviewed, Pending không duyệt. Không suy tỷ lệ chính xác toàn corpus.
- Sidecar thật dùng bundle đã stage: exact DOCX multiline trả 2 dòng typed, đủ raw spans, giữ serial/thửa/tờ, không ô phẳng/ambiguity giả; scan Upload **1/1/1**. Native GUI DOCX chưa thực thi do seam raw path/file_token; các giới hạn native picker/kiểm trang Word/máy khác của #9 không đổi.
- Bằng chứng, triage, diff và snapshot: [EXECUTION-SUMMARY](../tmp/issue-22-regex-consumer-cutover/evidence/EXECUTION-SUMMARY.md), [plan built](../tmp/issue-22-regex-consumer-cutover/plan.md). Không thêm luật parsing/nhánh OCR; text QR/OCR vẫn ở biên; không đổi schema hay dữ liệu người dùng.
