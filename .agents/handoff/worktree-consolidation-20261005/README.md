# Gom worktree — TASK-6 — 05/10/2026

**Đích:** một nhánh `consolidate/monorepo`. **Tại sao:** Owner cần tiếp tục từ cùng
spec, task, plan và bằng chứng; tránh nhầm file chưa commit với việc đã bàn giao.
TASK-6 chỉ gom tài liệu. TASK-7 tiếp tục theo yêu cầu Owner: đưa nhánh chính về
thư mục gốc, sao lưu và kiểm tra trước khi dọn worktree phụ. Không force/reset
nhánh và không triển khai runtime.

## Nguồn tìm thấy

| Nguồn | Trạng thái đầu lượt | Đã xử lý |
|---|---|---|
| `codex/multica-takeover` | HEAD `8a7d8bf`, bằng HEAD nhánh chính | Toàn bộ commit đã có ở đích; không merge trùng |
| Worktree Codex `C:\Users\MINH\.codex\worktrees\1aae\systemdocs` | File còn, metadata `D:/systemdocs/.git/worktrees/systemdocs1` mất; một progress log đổi và bộ ghi chú/task chưa commit | Sao lưu, nhận gói regex/audit/brainstorm, TASK-5, review TASK-3 và progress NAIA-15; giữ raw và file tạm cục bộ |
| `D:\systemdocs` | HEAD worker MIN-141 `3fec5cb`, đã là tổ tiên nhánh chính; có tài liệu tổng quan/issue chưa commit | Nhận báo cáo tóm tắt, chỉ mục bản đầy đủ và product-overview; chỉ thêm liên kết README, không chép bản README cũ đè spec địa chỉ mới |
| Các nhánh local còn lại | Không có nhánh local nào chưa được merge vào `consolidate/monorepo` trước khi gom | Giữ nguyên refs; sao lưu lịch sử bằng bundle |
| Orca `C:\Users\MINH\orca\workspaces\systemdocs` | Bốn thư mục `fix-bug-notary_v2`, `notaryoffice-bmad-brainstorm`, `otter`, `xuất-word` không còn source/Git; hai file `nul` không phải công việc sản phẩm | Đã duyệt toàn bộ cây; không có thay đổi source để lấy. [Kiểm kê](orca-inventory.json) |
| Lưu phiên Orca (`.orca`, Roaming/Orca) | Đọc metadata đường dẫn, gồm 13 session record khớp systemdocs; đường dẫn workspace thực tìm được là `D:\systemdocs` | Không tìm thêm checkout trong metadata đã kiểm. Không sao chép token hoặc toàn bộ transcript |

Phạm vi tìm: các checkout Codex, toàn bộ cây `orca/workspaces`, đường dẫn phiên
Orca, repo gốc và refs local. Không khẳng định tìm hết mọi thư mục tùy ý trên các
ổ đĩa hoặc dữ liệu đã bị xóa từ trước.

## Phần giữ nguyên cục bộ

- Backup local tại `.agents/local-only/worktree-recovery-20261005/`: bundle đủ
  lịch sử 5 nhánh, zip 129 file hiện diện chưa commit từ Codex, zip 6 file hiện
  diện từ repo gốc, manifest/mã băm và refs ban đầu. Bundle đã được Git verify.
- Hai thư mục source tham khảo upstream chưa commit được giữ ở worktree gốc;
  báo cáo và commit nguồn đã có trong gói docs, không đóng gói repo tải về.
- Đáp án có dữ liệu cá nhân và inventory chi tiết giữ tại
  `.agents/local-only/notary-20261005/`; Word gốc vẫn ở thư mục mẫu bên ngoài.
- Bản ghi Multica đầy đủ 31.785 dòng có dữ liệu hồ sơ được giữ nguyên trong
  cùng thư mục local-only; Git nhận chỉ mục/mã băm và bản tóm tắt. 51 file Word/
  manifest/báo cáo xuất thử cũ cũng được copy nguyên vào local-only, không gọi
  việc copy là lượt chạy xuất mới.
- Repo gốc vẫn ở nhánh worker, các thay đổi làm dở giữ nguyên. Không nhận bản
  AGENTS cũ làm mất luật Backlog, không nhận việc thiếu 33 file `_bmad` làm yêu
  cầu xóa trên nhánh chính. Fixture Zalo chỉ khác xuống dòng CRLF/LF, không có
  khác biệt nội dung cần merge.
- Spec/plan từng bị rút được lưu dưới `withdrawn-20261004`; bản gốc và task
  archive là bằng chứng lịch sử, không phải đầu việc được giao lại.

## Chỗ tiếp tục

Checkout duy nhất để tiếp tục: `D:\systemdocs`, nhánh `consolidate/monorepo`.
Thư mục `consolidate-20261005` chỉ là điểm gom trung gian của TASK-6.
Đọc [bàn giao theo từng việc](../notary-20261005/README.md) trước khi giao agent.
TASK-3 In Progress, TASK-4/TASK-5 To Do; lượt gom không tự đánh dấu các chức năng
đã hoàn tất. Các quyết định đã duyệt và các bản nháp được giữ phân biệt.

Commit và kết quả kiểm cuối được ghi qua CLI trong TASK-6. Các ghi chép Multica
từ repo gốc được nhận như tài liệu trước đây; không xem chúng là xác nhận
nghiệm thu mới. Các file snapshot trong `withdrawn-20261004` giữ liên kết theo
vị trí nguồn lịch sử, không phải cây spec đang dùng.

## Đưa về root và dọn — TASK-7

Quyết định Owner: dùng một thư mục gốc; giữ mọi công việc và dữ liệu trước khi
xóa các checkout phụ. Các trạng thái ở bảng trên là kiểm kê **trước khi gom**.
Kết quả hiện tại xem [báo cáo root](root-verification.md).

Bản sao của worktree 1aae: 33.850 file đọc được, 4.241.032.743 byte nguồn;
file ZIP đã kiểm CRC, rồi đối chiếu SHA-256 từng file với nguồn. Nằm ở
`D:\systemdocs\.agents\local-only\root-consolidation-20261005\orphan-complete.zip`.
Bao gồm file bị Git bỏ qua, thư viện/build, repo tham khảo và các bản thử Word.
31 file ở các thư mục cache/workflow bị chặn quyền được giữ trong ZIP bổ sung
trước khi xóa. Chi tiết và vỏ thư mục còn bị khóa được ghi trong báo cáo root.
Các tài liệu/dữ liệu cần tiếp tục đã được đặt ở root; bản sao này giữ phần còn
lại để phục hồi khi cần. Các backup TASK-6 cũng đã copy sang root.

Các thay đổi cũ chưa commit ở root được giữ trong Git stash có nhãn
`TASK-7 root before consolidate 20261005`; không áp lại bản README/AGENTS cũ
đè tài liệu mới. Giữ nguyên các nhánh local và bundle lịch sử. Chưa push remote.

Windows từng chặn quyền đọc `_bmad` và một thư mục workflow bên dưới. Đã lưu
quyền cũ và sửa quyền đúng hai phạm vi đó; không xóa nội dung `_bmad`.
Log và kết quả sửa quyền nằm cùng thư mục backup root, không đưa vào Git.
