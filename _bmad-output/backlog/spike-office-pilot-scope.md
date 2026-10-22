---
id: 14
type: spike
title: "Chốt phạm vi và tiêu chí pilot NotaryOffice"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Chốt phạm vi và tiêu chí pilot NotaryOffice

## Description

Chốt có giao pilot Office và đo A1/A3/A4 trong môi trường cô lập được phép hay chưa. Owner/người tham gia chọn scope và nghiệm thu; issue này không cấp quyền schema/runtime production.

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
- tracking — _bmad-output/backlog/README.md, C13
- source — _bmad-output/specs/notaryoffice/README.md, §1–6
- source — _bmad-output/specs/shared/data-rules.md, §5–§7, Còn mở

## Notes

- Tracking: C13; **owner answered — 17/10/2026; đóng spike ở mức quyết định phạm vi, Office DEFERRED/Draft, không built**. Owner: “notaryoffice để lại, tôi sẽ làm sau” ([decision](../decisions/decision-owner-notaryoffice-deferred-20261017.md)). Không còn business gate #14; không giao pilot, đo A1/A3/A4, code/schema/runtime Office lúc này. Giữ `refined: false` cho phần thiết kế chưa refined; #1 chỉ tracking.
- Risk: medium — nhận diện sai người/việc hoặc thu nhận ngoài quyền. Không triển khai schema/runtime production trong spike.

### Đối chiếu nguồn — 16/10/2026

| Câu hỏi | Bằng chứng hiện có và phần còn thiếu |
|---|---|
| Đã giao pilot hiện hành? | [Spec Office](../specs/notaryoffice/README.md) §1–6 giữ Draft/chưa runtime nghiệm thu; [decision-39](../decisions/decision-39-notaryoffice-workstation-hub-draft.md) vẫn `proposed`. [Brainstorm 25/09](../brainstorming/brainstorm-notaryoffice-mvp-path-2026-09-25/.memlog.md), dòng 20,29–36, **có** owner chọn văn phòng mình làm nơi pilot và hướng offline trước/G0–G6; không nói owner chưa từng chọn pilot. Chưa có phạm vi/ủy quyền hiện hành đủ để thực thi, người tham gia, quyền dữ liệu/retention và tập mẫu/người/tiêu chí nghiệm thu đã chốt. |
| A1 — IFilter khi Word giữ file | **UNMEASURED** theo spec Office §5 và [data-rules](../specs/shared/data-rules.md) §6/Còn mở; cần Word/IFilter, bản sao mẫu và trạng thái mở/khóa thực trong môi trường được phép. Đường đọc DOC/đọc-xuất DOCX Notary/Upload không chứng minh A1. |
| A3 — sự kiện SMB/ổ mạng | **UNMEASURED**; cần share/cấu hình/quyền thực và đối chiếu thao tác với event. Scan file/local NTFS không chứng minh nhận đủ sự kiện SMB. |
| A4 — tài khoản sáu máy | **UNMEASURED/chưa khảo sát**; cần thực tế tài khoản/máy được phép, không suy máy = người. Dùng chung Windows không tự nhận diện người; khảo sát giả định không phải feature theo dõi tài khoản. |
| Nhóm việc, quyền và nghiệm thu | Loại việc/flow là định hướng; chưa có corpus Office có nguồn/hash/nhãn độc lập, người phân xử, quyền xác nhận, thông báo/phạm vi dữ liệu và retention hiện hành. Mốc 8/10, gần 0 ghép sai, một thao tác ngắn/ngày còn Draft, không thành AC Approved. Chỉ làm rõ phần cần thiết sau khi owner chọn scope. |

- Bằng chứng chi tiết và giới hạn capability: [ledger research](../tmp/issue-14-office-pilot/evidence.md), §1–4. Chỉ đọc artifact có sẵn; không chạy app/phép đo/test mới. A1/A3/A4 là giả thuyết cần kiểm, không phải tính năng đã giao.
- **Bên nhận và đáp án — 17/10/2026:** owner đã trả lời câu hỏi scope bằng “notaryoffice để lại, tôi sẽ làm sau”; coordinator ghi nhận **toàn bộ Office DEFERRED, giữ Draft**. Delivery/operator/reviewer không được giao pilot hoặc phép đo lúc này; không có proof A1/A3/A4 mới hay nghiệm thu kỹ thuật để chuyển giao.
- **Không hard-after DB vật lý #13:** đo cô lập không cần DB chung về kỹ thuật, nhưng hiện cũng không được giao do owner hoãn toàn bộ Office. Chuyển liên module thật vẫn cần contract/quyền riêng. Tiếp tục các issue độc lập theo thứ tự backlog, kế tiếp #15 sau khi xuất bản bản ghi; không còn gate #14.
- **Câu hỏi phạm vi đã khép lại:** không hỏi lại fork giữ Draft/đo cô lập/pilot trong lượt này. Quyết định là ưu tiên của owner, không đặt deadline mở lại, không xóa hướng pilot/offline/G0–G6 lịch sử 25/09 và không coi hướng đó là quyền thực thi hiện tại.
- **Nơi ghi đáp án và AC:** [decision owner 17/10](../decisions/decision-owner-notaryoffice-deferred-20261017.md) + spec Office/Notes/catalog/sổ tay cập nhật cùng phiên. AC1/2 có ledger/bên chờ; AC3 có câu trả lời scope trực tiếp của owner và ranh giao việc nêu trên, không giả có người nhận kết quả đo. Spike trả lời phạm vi, không xác nhận pilot hoàn tất; ledger 16/10 và review dưới đây giữ làm lịch sử trước đáp án.
- Loại trừ giữ nguyên: theo dõi bản in, tài khoản/tin riêng, ghi phím, quay màn hình và chấm công; không tự bật Sentinel/Hub/popup/Zalo hoặc tạo schema/runtime Office.
- **Review tài liệu — 16/10/2026 (lịch sử trước đáp án owner):** Quick độc lập `office-pilot-gate-review` không có finding actionable; coordinator đã đọc diff và research. CLEAN chỉ áp dụng bản ghi business gate, không nghiệm thu pilot hoặc chứng minh A1/A3/A4. Tại thời điểm review, #14 còn BLOCKED và chưa có đáp án owner/ghi nhận nhận đáp án AC3; trạng thái hiện hành đã đổi theo đáp án 17/10 ở trên.
- **Review tài liệu — 17/10/2026:** reviewer độc lập giữ phiên `office-pilot-gate-review`, lượt t2, không có finding actionable; coordinator đã đọc diff. CLEAN áp dụng bản ghi quyết định owner hoãn Office và tài liệu đồng bộ, không phải nghiệm thu Office/pilot hoặc phép đo A1/A3/A4.
