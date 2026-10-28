---
title: Gộp TASK-10 regex sweep vào nhánh chính
status: built
date: '2026-10-08'
source_branch: minhnhatnguyen6297-a11y/task5-regex-hop-dong-word
source_commit: 585f918
main_before: 76bb9a8
---

Owner đã yêu cầu commit/gộp/xử lý xung đột. [Quyết định và lý do](../decisions/decision-75-regex-integration.md).

Giữ `_bmad-output` của main, nhập sửa lỗi regex và Stage đã kiểm. Task cũ lưu ở archive, không quay lại Backlog live. Corpus/bằng chứng gốc giữ ngoài commit tại worktree `C:/Users/MINH/orca/workspaces/systemdocs/task5-regex-hop-dong-word/.agents/`.

Xử lý 41 xung đột đường dẫn theo nơi lưu mới; gộp cả hai nội dung của `deferred-work.md`. Giữ các thay đổi khác đã có trên main. Tách mã quyết định trùng 46/47/48; giữ đúng ý nghĩa tham chiếu regex. Git dùng `core.longpaths=true` theo từng lệnh, không đổi cấu hình máy.

Kiểm trước khi đưa vào main: không còn conflict; spec/link/namespace đúng; engines/validators/fixtures mirror; Upload/Tool/DOCX/renderer đạt; chạy mới 50 file và kiểm UI đã lưu/mở lại. So ancestry/HEAD và main sạch trước/sau gộp. Không push, không làm mất bằng chứng cũ.

Mốc sweep tiếp 3980; gap 3910–3929 và gap 20 file vị trí10–29 giữ riêng. F01/F04/F05 còn chờ quyết định.

## Kiểm sau xử lý xung đột
Upload424passed/2skip;Tool207passed/1skip;DOCX+docs67passed/1skip;renderer102passed, không loại3testWord cũ. Các thay đổi Word có sẵn trên main giải quyết3test đó. Có241link hợp lệ,0conflict/legacytrackedpath,4cặp snapshot mirror. Native fresh50 vẫn48khớp trường đã kiểm+2source_review,76người/13mô tả đất;nguồn50 và110bằng chứng cũ không đổi. Chromium+realDB nhận/sửa/lưu/mở lại/chặn ngày sai/giữnguồn đạt.

Log tại docs/tmp/regex-integration/ trong worktree kiểm; corpus gốc tại worktree đã ghi. Lần DOCX đầu dùng basetemp quá dài làm os.link gặp giới hạn Windows; giữ log lỗi và chạy lại cùng tests với basetemp ngắn, không sửa test hoặc production để né lỗi. Đây vẫn là giới hạn đường dẫn của dịch vụ hiện có, không tính là lỗi merge.

## Gộp trên nhánh chính
Nhánh chính kiểm sạch tại76bb9a8 trước khi gộp; commit sửa585f918 và commit xử lý xung đột dda5355 đã có trong ancestry. Tạo merge commit trên consolidate/monorepo, giữ nhánh chính làm parent thứ nhất. User đã cho phép gộp; chưa push. Báo cáo kiểm cuối tại docs/tmp/regex-integration/ trong D:/systemdocs.
