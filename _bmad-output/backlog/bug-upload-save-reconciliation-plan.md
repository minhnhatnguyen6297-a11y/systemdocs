---
title: 'Kết quả Lưu portal bị lệch khi đóng tab hoặc mất phản hồi'
type: 'bugfix'
ticket: '11'
created: '2026-10-15'
status: dropped
baseline_revision: '023148099fc7e093b80abedb0965d978d00ea3e6'
route: 'full'
route_source: 'auto'
risk: 'high'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/upload_lab/README.md'
  - '{project-root}/contracts/upload-workflow.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Vấn đề:** Tín hiệu Lưu v1 đã được ghi nhận qua `POST /api/hoso` HTTP 2xx có thể bị hạ thành `closed` nếu tab đóng trước lần thăm dò kế tiếp. Khi mất phản hồi, kết quả có thể không rõ; không được báo là đã Lưu hoặc đề nghị gửi lại nếu chưa đối chiếu.

**Cách tiếp cận:** Bảo toàn bằng chứng Lưu dương tính đã nhận trước khi xử lý sự kiện đóng tab. Tái sử dụng các điều khiển hiện có để kết thúc kiểm tra, đóng trình duyệt, audit mới và đối chiếu; tiếp tục chặn chuẩn bị hồ sơ khi còn kết quả chưa rõ. Để ngỏ cho quyết định bên dưới cách giải phóng hồ sơ không có số trong audit.

## Boundaries & Constraints

**Luôn:** Chỉ coi tín hiệu `POST /api/hoso` 2xx hiện có của v1 là bằng chứng Lưu đã biết. Giữ hồ sơ chưa rõ trong `needs_reconcile` và chặn chuẩn bị cho đến khi có kết quả đối chiếu được chủ sở hữu phê duyệt. Tách biệt workflow legacy.

**Không bao giờ:** Mở rộng tiêu chí thành công sang thay đổi route, suy đoán từ host/nội dung phản hồi, thời gian trôi qua hoặc thao tác người dùng; tự lưu hoặc tự gửi lại; thay đổi trạng thái duyệt trong hợp đồng Draft; gộp ngữ nghĩa portal thật thuộc phạm vi #26. Không thêm timeout mới; chỉ thêm hành động nếu kết quả được chủ sở hữu phê duyệt yêu cầu.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Lưu đã biết rồi đóng tab | Tab v1 đã nhận POST 2xx được công nhận trước khi bộ theo dõi thấy tab đóng | Giữ trạng thái `saved`; không hạ thành `needs_reconcile` hoặc đề nghị chuẩn bị lại | Hiển thị lỗi engine thông thường mà không xóa bằng chứng đã ghi nhận |
| Chưa rõ khi phiên kết thúc | Không có tín hiệu Lưu được công nhận; người dùng kết thúc kiểm tra và đóng trình duyệt upload | Giữ hồ sơ ở trạng thái chưa xác minh, lưu bền dưới `needs_reconcile`; cung cấp đường dẫn audit mới hiện có và chặn chuẩn bị lại cho đến khi có kết quả đối chiếu được duyệt | Không giả định thành công hoặc gửi lại |

</frozen-after-approval>

## Code Map

- `upload_lab/playwright_uploader.py` — `_register_prepared_page` (1930–1952) ghi nhận tín hiệu thành công nghiêm ngặt; `poll_prepared_pages` (1968–2025) hiện kiểm tra tab đóng trước cờ đã Lưu. Giữ nguyên tín hiệu nghiêm ngặt và bảo toàn kết quả dương tính khi tab đóng.
- `shell/sidecar/upload_session.py` — `_update_snapshot` (466–532) chuyển tab đóng/chưa rõ sang trạng thái đối chiếu bền vững và tăng phiên bản queue của lượt khởi tạo. `upload_session_close_v1` trong `shell/sidecar/upload_adapter.py` (1609–1659) thăm dò lần cuối rồi đánh dấu các tab còn mở là chưa rõ.
- `shell/sidecar/upload_workspace_store.py` — các dòng `needs_reconcile` bền vững và snapshot toàn website (`102–108`, `464–514`, `560–580`). Tái sử dụng trạng thái này; không thêm schema.
- `shell/sidecar/upload_adapter.py` — `upload_prepare_v1` (1787–2018) loại ID chưa được giải quyết; `upload_reconcile_v1` (2137–2250) dùng audit mới và chỉ xóa hồ sơ đã xác minh. Điều kiện chặn chuẩn bị do backend sở hữu.
- `shell/src/renderer/upload/index.js` — `finishReview` và `closeSession` (454–466, 650–655); hành động đối chiếu hiện có audit lại Excel trước khi gọi `upload.reconcile` (607–649). `scan-upload.js` (182–194, 487–497) hiển thị số lượng chưa rõ và hành động “Đối chiếu với sổ mới”. Tái sử dụng các điều khiển này.
- Vị trí hồi quy: `shell/test/test_upload_browser_workflow.py`, `shell/test/test_upload_recovery.py` và `upload_lab/tests/test_playwright_uploader.py`; các ca hiện có bao phủ tín hiệu Lưu nghiêm ngặt, đóng tab, khôi phục và đối chiếu bằng audit mới, nhưng chưa bao phủ tình huống được báo cáo là phản hồi đến trước khi đóng tab.

## Tasks & Acceptance

**Execution:**
- [ ] `upload_lab/playwright_uploader.py` — bảo đảm tín hiệu Lưu v1 được công nhận hoàn tất trước khi phân loại tab đã đóng; giữ nguyên xử lý legacy và tiêu chí thành công.
- [ ] `shell/sidecar/upload_session.py` và `shell/sidecar/upload_adapter.py` — bảo toàn kết quả Lưu đã biết qua lưu trạng thái phiên; xác nhận tình trạng đóng chưa rõ/khởi động lại vẫn tới UI hiện có và điều kiện chặn chuẩn bị. Tái sử dụng các điều khiển hiện có; chỉ ghi nhận hành động giải phóng sau khi chủ sở hữu trả lời câu hỏi mở.
- [ ] `shell/test/test_upload_browser_workflow.py`, `shell/test/test_upload_recovery.py`, `upload_lab/tests/test_playwright_uploader.py` — bổ sung bằng chứng hồi quy cho phản hồi-rồi-đóng, đóng khi chưa rõ/đối chiếu và chặn chuẩn bị lại; dùng portal tổng hợp cục bộ, không thông tin đăng nhập thật hay ghi dữ liệu môi trường sản xuất.

**Acceptance Criteria:**
- Với tab v1 đã nhận POST 2xx được công nhận, khi tab đóng trước lần thăm dò tiếp theo của bộ theo dõi, thì kết quả Lưu đã xác minh vẫn được ghi nhận và không bị hạ thành chưa rõ.
- Với kết quả vẫn chưa rõ khi người dùng đóng trình duyệt upload, khi lượt thăm dò cuối hoàn tất, thì dòng hồ sơ vẫn hiển thị `needs_reconcile` và đường dẫn đối chiếu bằng audit mới hiện có; hồ sơ không bị đánh dấu đã Lưu hoặc gửi lại.
- Với hồ sơ còn chưa được giải quyết, khi lô chuẩn bị mới có chứa hồ sơ đó, thì backend chặn/loại hồ sơ cho đến khi kết quả đối chiếu được chủ sở hữu phê duyệt giải quyết.

## Open Questions

1. **Khi audit mới không có số hồ sơ, xác nhận tường minh cho từng hồ sơ của người vận hành sau khi kiểm tra portal có đủ để xóa `needs_reconcile` và cho phép một lần chuẩn bị chủ động sau đó (A), hay hồ sơ phải tiếp tục bị chặn cho đến khi audit mới xác minh có hồ sơ (B)?** (A) Xác nhận sau khi kiểm tra portal có thể cho phép gửi trùng nếu xác nhận nhầm. (B) Tiếp tục chặn đến khi audit mới xác minh có hồ sơ có thể khiến hồ sơ thực sự chưa được lưu vẫn bị chặn. Đặc tả đã cho phép chung “xác nhận của người dùng” nhưng chưa định nghĩa hành động giải phóng hoặc bằng chứng khi audit không có số; code hiện chỉ xóa khi audit mới có hồ sơ.

**Retired 15/10/2026:** [owner decision](../decisions/decision-upload-web-sot-without-save-tracking.md) supersedes this Save-tracking scope. #11 is dropped; this historical A/B question no longer gates work, and no answer was selected. Runtime cutover is tracked by draft #28, not approved implementation.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- Trong thư mục `shell`: `rtk pytest -q test/test_upload_browser_workflow.py test/test_upload_recovery.py test/test_upload_workspace.py` — kỳ vọng: các kiểm thử hồi quy race, khôi phục và chặn gửi trùng đạt.
- Trong thư mục `upload_lab`: `rtk proxy python -X utf8 -c "import sys; sys.path.insert(0, '.'); import pytest; raise SystemExit(pytest.main(['-q', 'tests/test_playwright_uploader.py']))"` — kỳ vọng: bộ kiểm thử đơn vị uploader đạt.

**Manual checks (if no CLI):**
- Sau khi triển khai, chạy thử luồng app/backend/engine thật với portal tổng hợp cô lập tại máy, dữ liệu tổng hợp, không dùng thông tin đăng nhập thật hoặc ghi dữ liệu sản xuất. Thực hiện các tình huống POST 2xx được công nhận rồi đóng tab ngay, đóng khi không có phản hồi, đối chiếu bằng audit mới và điều kiện chặn chuẩn bị. Việc này không xác minh ngữ nghĩa host/nội dung/mức đầy đủ nghiệp vụ của portal; chúng vẫn thuộc phạm vi riêng #26.
