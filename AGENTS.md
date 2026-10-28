# AGENTS.md — luật làm việc trong systemdocs

## Dùng BMAD

- Dùng workflow BMAD và customization của repo trong `_bmad/custom/`; đọc skill
  tương ứng trước khi dùng. Không dựng flow song song.
- Code tối giản; artifact và handoff ngắn gọn; trao đổi với user tự nhiên, dễ hiểu.

## Nguồn chuẩn

| Nội dung | Nơi lưu |
|---|---|
| Hành vi | `_bmad-output/specs/` |
| Quyết định đã chốt (LÀ GÌ + TẠI SAO) | `_bmad-output/decisions/` |
| Artifact workflow | `_bmad-output/` |
| Lịch sử | `_bmad-output/archive/` |
| Quan hệ code | `graphify-out/` |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `_bmad-output/decisions/` trong phiên hiện tại.
  Task, handoff và file tạm nằm trong `_bmad-output/tmp/`.
- Đọc `graphify-out/` trước khi dò code thủ công.

## Trình bày

- Chỉ tạo file HTML trong `_bmad-output/tmp/` cho plan, spec, brainstorming hoặc
  minh họa cấu trúc; chat, trạng thái, phân tích, review và báo cáo thường trả lời
  trong hội thoại.
- HTML plan/spec là lớp trình bày; Markdown và artifact BMAD vẫn là nguồn chuẩn.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

## Luật cho coder agent

- **Review bắt buộc trước khi báo xong**: chạy Superpowers `requesting-code-review`
  hoặc agent Reviewer trên diff; xử lý góp ý hoặc ghi lý do.
- Không dùng `git stash` (dùng commit WIP hoặc worktree riêng). Không code trên `main`.
- **Tìm trên GitHub trước** khi tự viết công cụ/pattern; ghi URL đã tham khảo.
- Quyết định nhỏ: tự quyết và ghi lại. Thay đổi kiến trúc, schema/contract hoặc
  dependency: dừng, báo các phương án + đánh đổi, chờ owner.
- Báo cáo phải có lệnh đã chạy + output (kể cả lỗi, bước bị bỏ qua), tách đã kiểm
  chứng / chưa kiểm chứng, và nêu giả định.
- Không skip test để cho xanh: lỗi đã biết ghi vào `tools/ci/known-failures-*.txt`
  kèm issue ref. Chuẩn "xong": `docs/definition-of-done.md`.

## Báo lỗi phải có bằng chứng

Mọi issue lỗi (người hay agent tạo) dùng form `.github/ISSUE_TEMPLATE/bug_report.yml`. Issue trống đã bị tắt.

Agent khi báo lỗi phải đính kèm đủ:

1. **Nhánh + commit SHA** đang chạy khi thấy lỗi.
2. **Lệnh tái hiện chính xác** (hoặc tên test đang fail), chạy được từ gốc repo.
3. **Đoạn log** liên quan của app và sidecar (vài chục dòng quanh lỗi, không dán cả file).
4. **Ảnh chụp/video** (ví dụ ảnh từ harness CDP trong `/workspace/usability`, `/workspace/e2e-run`).
5. Kết quả mong đợi vs thực tế, môi trường.

Log cố định: app ghi `<userData>/logs/main.log` và `sidecar.log` (xoay vòng 5 MB × 3 bản; userData = `%APPDATA%\g1-shell` trên Windows, `~/.config/g1-shell` trên Linux; bản test là `g1-shell-test`). Script đọc mặc định từ đây.

Sinh nội dung nhanh: `tools/file-bug.sh --title "..." --repro "lệnh" [--log file]... [--shot file.png]` → in markdown ra stdout và chép ảnh vào `docs/evidence/<mã>/`. Script không tạo issue.

**Đính kèm ảnh khi không có trình duyệt:** API GitHub không upload được file đính kèm issue. Cách dùng: commit ảnh/log vào `docs/evidence/<mã>/` trên nhánh riêng `evidence/<mã>` (không merge vào nhánh chính), push nhánh đó, rồi dẫn link `https://github.com/<owner>/<repo>/blob/evidence/<mã>/docs/evidence/<mã>/<file>?raw=true` trong issue. **Repo này PUBLIC**: mọi ảnh/log push lên nhánh `evidence/*` ai cũng xem được — chỉ dùng dữ liệu giả lập, đã che đường dẫn/token. Mã là ngày-giờ + slug, sau khi có số issue thì ghi số issue vào README trong thư mục.

**Chỉ dữ liệu giả lập.** Không chụp/ghi log có dữ liệu công dân thật.

Issue lỗi thiếu một trong các mục trên → gắn nhãn `needs-evidence` và **không được xử lý** cho đến khi bổ sung. Agent nhận việc từ issue như vậy: hỏi bổ sung, không tự đoán.
