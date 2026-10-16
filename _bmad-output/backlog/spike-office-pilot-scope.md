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

- Tracking: C13; **BLOCKED — chờ lựa chọn phạm vi của owner, 16/10/2026**. Điều tra repo đã ghi nhận; không phải pilot complete/built, vẫn `refined: false`. #1 chỉ tracking. Lệnh làm liên tục bỏ duyệt plan riêng, không chọn thay quyết định nghiệp vụ ([decision](../decisions/decision-bmad-all-active-loose-issues-no-autoresearch.md), §Cập nhật 16/10).
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
- **Ai chờ:** delivery Office chờ owner chọn scope; operator/reviewer chỉ nhận nhiệm vụ đo sau khi có môi trường/dữ liệu được phép. Owner nhận lựa chọn sản phẩm; người giữ môi trường/chuyên viên cung cấp điều kiện thật và nhãn nghiệp vụ, reviewer nhận proof đúng điều kiện.
- **Không hard-after DB vật lý #13:** đo cô lập không cần DB chung; chuyển liên module thật vẫn cần contract/quyền riêng. Notary/Upload và tài liệu độc lập không bị #14 chặn kỹ thuật; coordinator vẫn dừng tại business gate theo thứ tự backlog, không tự chạy issue kế tiếp.
- **Một câu hỏi để coordinator gửi owner:** Giữ Office Draft và tiếp tục các issue khác (**khuyến nghị, chưa chọn**), hay cho phép đo tạm/cô lập A1/A3/A4 trước (không phải pilot sản phẩm), hay giao pilot ngay (cần chốt scope tiếp)?
- **Nơi ghi đáp án:** Notes leaf này; khi owner thực sự chọn, cập nhật decision/spec Office cùng phiên. Không tạo decision thay owner. AC1/2 đã có ledger/bên chờ; AC3 mới chuẩn bị câu hỏi và phân vai, **chưa ghi owner đã nhận/trả lời hoặc reviewer đã nhận phép đo**.
- Loại trừ giữ nguyên: theo dõi bản in, tài khoản/tin riêng, ghi phím, quay màn hình và chấm công; không tự bật Sentinel/Hub/popup/Zalo hoặc tạo schema/runtime Office.
- **Review tài liệu — 16/10/2026:** Quick độc lập `office-pilot-gate-review` không có finding actionable; coordinator đã đọc diff và research. CLEAN chỉ áp dụng bản ghi business gate, không nghiệm thu pilot hoặc chứng minh A1/A3/A4. #14 vẫn BLOCKED; chưa có đáp án owner/ghi nhận nhận đáp án AC3.
