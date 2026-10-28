---
id: decision-owner-inheritance-remove-entire-branch-20261017
title: "Owner chốt: gỡ cả nhánh khỏi sơ đồ thừa kế"
date: '2026-10-17'
status: superseded
---

**Bị thay thế ngày 27/10/2026** bởi
[luật sơ đồ v2 — gỡ thẻ + Hoàn tác](decision-owner-diagram-rules-v2-20261027.md).
Nội dung bên dưới giữ làm lịch sử, không còn là luật triển khai: không modal,
ô do engine sở hữu; gỡ chủ đất đưa cả vợ/chồng về Pool theo tập ô engine sinh.

## Quyết định của owner — 17/10/2026

Nguyên văn:

> B - gỡ cả nhánh

Lựa chọn trả lời ví dụ **ông/bà A → con B → cháu C**, B có vợ/chồng S, C có cha/mẹ `[B,S]`. **B** là phương án gỡ B và toàn bộ hậu duệ theo cạnh cha/mẹ khỏi Diagram, kể cả C còn cha/mẹ S. S không bị gỡ chỉ vì là vợ/chồng của B. Đây không phải phương án C giữ ô B trống.

## Quy tắc tại thời điểm 17/10/2026 — đã bị thay thế

- Khi xóa một node Thừa kế, tập bị gỡ gồm node đó và mọi node active đi tới được bằng cạnh cha/mẹ → con, ở mọi độ sâu; gồm cả slot chưa gán người và slot ẩn. Không đi theo cạnh vợ/chồng để tìm hậu duệ. Với C có hai cha/mẹ, chỉ một cha/mẹ nằm trong nhánh bị gỡ cũng đủ để gỡ C và hậu duệ của C.
- Người của tất cả node bị gỡ vẫn giữ nguyên trong Stage; Pool suy từ người không còn gán trên node active của Diagram đang xem. Không tạo kho Pool mới, không xóa dòng Stage, đổi ID, thứ tự hoặc giá trị Người/Tài sản.
- Giữ các node bị gỡ dưới dạng `deleted:true` trong state Node v3 canonical hiện có. Giữ ID, `personId`, dấu Chủ/Nhận và metadata không phải quan hệ; xóa toàn bộ `parentSlotIds`/`spouseSlotId` đi ra từ chúng. Dọn mọi tham chiếu đi vào tập bị gỡ trên tất cả node, kể cả tombstone cũ. Quan hệ vợ/chồng còn lại phải nhất quán; không để parent không hợp lệ. Các node/quan hệ/dấu Chủ/Nhận ngoài tác động này giữ nguyên. Không tự nối cháu lên ông/bà, đổi cha/mẹ hoặc tính lại phân số bằng JavaScript.
- Trước mutation, cảnh báo bằng **danh sách node thực tế** sẽ gỡ và **quan hệ thực tế** sẽ ngắt, phân biệt người và ô trống; giải thích người vẫn ở Stage, trở lại Pool, phần hưởng có thể đổi và chưa ghi cho tới khi Lưu sơ đồ. Không thay bằng lời báo chung hoặc chỉ số lượng.
- Hủy, Escape, nút đóng hoặc đóng nền trước xác nhận không đổi draft, dirty flag, revision, dữ liệu đã lưu và không phát evaluate/save do thao tác này. Xác nhận áp toàn bộ thay đổi trong **một** mutation draft rồi dùng đường evaluate hiện có; không tự save. Không áp âm thầm nếu graph đã khác phần tác động đang được cảnh báo.
- Lưu sơ đồ tiếp tục dùng command/state canonical, transaction và `base_revision` hiện có. Lỗi/invalid/conflict giữ draft và bản lưu cũ; lưu thành công rồi mở lại mới phải khớp state canonical đã lưu. Không tạo API/store/schema quan hệ mới; không đổi công thức thừa kế hoặc semantics sinh slot mặc định hiện hành.

## Phương án đã loại

- **A — chỉ gỡ B, giữ hậu duệ nhưng tách B:** không được chọn.
- **C — giữ ô B trống cùng quan hệ:** không được chọn.
- Tự đổi cha/mẹ lên thế hệ trước và tự gỡ spouse theo hôn nhân không thuộc lựa chọn B, không được triển khai.

## Phạm vi và trạng thái

- Spike #21 chỉ nhận đáp án/bằng chứng; giữ nguyên ba AC và `refined: false`, không triển khai hoặc tuyên bố built trong spike.
- Implementation riêng **#21B**, [story](../backlog/story-inheritance-remove-entire-branch.md) và [plan](../backlog/story-inheritance-remove-entire-branch-plan.md). Chỉ đạo tiếp tục không xin duyệt từng plan vẫn áp dụng; parent đọc plan và Quick độc lập trước code là kiểm soát nội bộ, không phải gate owner mới.
- Spec/contract được đồng bộ trước code trong phiên 17/10/2026. Ghi quyết định không chứng minh runtime đã sửa. Bằng chứng nghiên cứu trước quyết định ở `../tmp/issue-21-middle-node-deletion/` giữ nguyên, không chạy lại để xác nhận lỗi đã quan sát.
- #20 Danh sách hồ sơ, #19 Word authoring và Office/#14 vẫn DEFERRED; #18 REMOVED. Không mở lại, đổi config/initiative hoặc dùng Autoresearch.
