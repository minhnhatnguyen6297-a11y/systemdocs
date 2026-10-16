---
id: 2
type: story
title: "Không gian Stage, Pool và Diagram liền mạch, dễ thao tác"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: false
risk: medium
---

# Không gian Stage, Pool và Diagram liền mạch, dễ thao tác

## Description

Thực hiện sáu cải thiện workspace đã báo: phân biệt địa chỉ với nơi cấp giấy tờ, mở rộng vùng thao tác Pool/Sơ đồ và ô Hai bên, bỏ riêng Hủy thay đổi của Stage, không để thông báo đẩy Sơ đồ khỏi vị trí đang làm.

## Acceptance Criteria

1. **Đúng nghĩa trường**
   **Given** người sống/người chết có địa chỉ và nơi cấp
   **When** chuyên viên sửa, lưu rồi mở lại
   **Then** địa chỉ/Nơi chết và nơi cấp giấy tờ có nhãn riêng, giữ đủ hai giá trị
2. **Vùng thao tác dùng được**
   **Given** layout được duyệt ở viewport report/màn nhỏ và danh sách dài
   **When** gán/hoán đổi bằng kéo thả hoặc bàn phím và có thông báo
   **Then** target còn tiếp cận được, thông báo không đẩy Sơ đồ khỏi vị trí thao tác, kích thước/cuộn đúng thiết kế đã nhận
3. **Giữ nháp**
   **Given** Stage hoặc Diagram chưa lưu
   **When** chuyên viên chuyển màn hoặc đóng app
   **Then** không còn Hủy thay đổi của Stage nhưng dirty, giữ nháp và cảnh báo rời/đóng vẫn hoạt động

## Boundaries

- Giữ nguồn gốc, dữ liệu đã lưu, ID field/slot và bảo vệ revision/ghi nguyên tử áp dụng cho phạm vi này.
- Không thêm tính năng không liên quan, suy pháp lý, schema, OCR fallback hoặc tự gộp liên module.
- Draft không phải duyệt triển khai.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C01
- source — _bmad-output/specs/notary_v2/README.md, §4, §5, §8
- source — _bmad-output/tmp/notary-flow-remediation/assessment-plan.md, §1 proposal, not approved design

## Notes

- Tracking: C01; phase 5 report đã làm và built một phần dưới uỷ quyền liên tục (standing continuous authorization) — không chờ phê duyệt plan; #2 nói chung vẫn một phần. #1 chỉ tracking, không chạy cùng leaf.
- Risk: medium — Bố cục hoặc nhãn sai làm khó thao tác và có thể khiến người dùng sửa nhầm trường; phải giữ bảo vệ nháp.
- Unknown: Chỉ còn trục tăng 50% vùng sơ đồ (802: chiều cao hay chiều rộng) chờ owner chốt. Kích thước Pool (nội dung 224/khung 240), ô Hai bên (202×52) và vị trí thông báo (khoảng trống sẵn có của thanh trên) đã chốt theo số đo thật + report; không còn câu hỏi kích thước nào chặn phần nhãn/nút (đã làm).
- Report: 18ae1083, e86a02bb, 802bd69e, 2c232a28, b54184b3, ac5e3ae3. Thiết kế ở assessment §1 mới là đề xuất, chưa duyệt tỷ lệ.
- Trạng thái 2026-10-16 (execution phase; plan + `final-verification.md` trong `_bmad-output/tmp/issue-2-unblocked-work/`): 5/6 report đã làm trong source — 18ae (nhãn `Nơi chết`/`Nơi cấp giấy khai tử` theo bằng chứng; người đã mất thiếu bằng chứng vẫn `Nơi cấp giấy tờ`), b541 (gỡ riêng nút `Hủy thay đổi` của Stage + code revert; giữ dirty/cảnh báo rời-đóng/nhánh bỏ nháp), 2c232 (Pool nội dung 224/khung 240), e86 (ô Hai bên 202×52), ac5 (thông báo tạm trong khoảng trống thanh trên, bám trên cùng khi `#view` cuộn). Bằng chứng hiện hành: Node 369 pass/0 fail (sau khi sửa env PATH/UTF-8; lần đầu 368 pass + 1 lỗi env jsonschema được giữ), adapter contract 83 pass, GUI trên chính gói default `shell/dist-app` 21 check/0 fail + đóng sạch (ASAR khôi phục từ i6, SHA khớp), independent Quick `workspace-clear-quick-review t1` — "No actionable findings.". Lần `npm run dist` gốc thất bại và lần smoke đầu lỗi prelaunch CP1252 (chi tiết + khóa DELETE của Orca PID 9604 giữ ở `final-verification.md`).
- 802 CHƯA làm: owner chưa chốt trục (chiều cao hay chiều rộng) cho yêu cầu +50% vùng sơ đồ; không tự áp tỷ lệ. #2 giữ trạng thái một phần, chưa built.
