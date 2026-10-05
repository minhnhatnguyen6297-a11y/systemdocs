# Root duy nhất — TASK-7 — 05/10/2026

**Tiếp tục tại:** `D:\systemdocs`, nhánh `consolidate/monorepo`.
**Quyết định:** Owner yêu cầu gom các công việc về root, kiểm tra rồi dọn worktree.
**Tại sao:** tránh tiếp tục từ các bộ tài liệu/nhánh khác nhau.

## Kết quả

- Nhận các commit bàn giao TASK-6 và TASK-7 tại root. Không còn nhánh local nào
  có commit nằm ngoài nhánh chính. Không force/reset hoặc xóa nhánh.
- Git chỉ đăng ký một checkout: `D:\systemdocs`.
- Worktree trung gian `consolidate-20261005` đã xóa cả thư mục.
- Worktree mất metadata `1aae` đã dọn hết file. Còn **vỏ thư mục rỗng**
  `C:\Users\MINH\.codex\worktrees\1aae\systemdocs`: Windows báo đang được dùng
  (WinError 32), nên chưa xóa được thư mục này trong phiên đang mở. Nó không
  còn source hay `.git`; không còn là nơi làm việc.
- Đã xóa bốn thư mục Systemdocs cũ tại `C:\Users\MINH\orca\workspaces\systemdocs`.
  Hai file `nul` rỗng được sao lưu trước khi dọn. Không đụng dữ liệu phiên,
  cấu hình hoặc tài khoản Orca.
- Giữ Git stash `b9816eb9b95acb3999da941c5dfca3a23d106376` cho những thay đổi
  trước khi chuyển root. Không áp lại tài liệu cũ đè bản đã gom. Chưa push.

## Bảo toàn

Tất cả bản sao nằm trong `D:\systemdocs\.agents\local-only\`, được Git bỏ qua.

- `worktree-recovery-20261005/`: bundle đủ lịch sử 5 nhánh; ZIP thay đổi làm dở
  của hai nguồn trước TASK-6. Git xác nhận bundle hợp lệ.
- `root-consolidation-20261005/orphan-complete.zip`: 33.850 file đọc được,
  4.241.032.743 byte nguồn. ZIP kiểm CRC đạt; SHA-256 từng file khớp nguồn trước
  khi dọn. Một số thư mục cache/workflow bị chặn quyền không nằm trong lượt này.
- `root-consolidation-20261005/orphan-blocked-supplement.zip`: 31 file bổ sung
  sau khi mở quyền các thư mục bị chặn; ZIP kiểm CRC đạt. Đối chiếu mọi file còn
  lại với bản sao trước khi xóa. Các liên kết thư mục thử nghiệm được ghi riêng;
  khi xóa không đi theo liên kết sang nơi khác.
- `notary-20261005/`: đáp án đọc tay, inventory, lịch sử Multica đầy đủ và 51
  file Word/manifest/báo cáo thử cũ. Đã đối chiếu bản copy từ worktree trung gian.
- 20 mẫu S01–S20 tại `.agent/scratch/Dữ liệu mẫu word test` còn đủ, hash khớp.

File kiểm chi tiết/log nằm trong `root-consolidation-20261005/`, gồm
`preservation-verified.json`, `supplement-manifest.json`, `cleanup-result.json`,
`root-source-result.json`, `node-result.json`, `python-result.json`.

## Kiểm tra tại root

| Kiểm tra | Kết quả |
|---|---|
| Git: commit các nhánh local đã có trong main | Đạt |
| Backlog doctor: ID trùng, phụ thuộc vòng | Không có |
| Liên kết Markdown mới/sửa | Đạt; số lượng ở [kết quả](link-check.json) |
| Ví dụ contract Notary | 82 mẫu, 0 kết quả ngoài dự kiến |
| Bộ test shell hiện có | 382 đạt, 0 lỗi |
| Sáu bộ test Python: địa chỉ, timeline, Word, migration, batch, DOCX | 389 đạt, 2 bỏ qua, 26 cảnh báo thư viện |
| Runtime/contract/data so với mốc `8a7d8bf` | Không đổi trong lượt gom |

Lượt chạy đầu gặp thiếu `jsonschema`, quyền thư mục tạm và sai nơi chạy test
Word. Lượt đạt dùng thư viện kiểm riêng trong local-only, thư mục tạm riêng,
chạy Python từ `notary_v2` với root trong đường tìm module. Không sửa code sản
phẩm để làm test xanh. Hai test bỏ qua do không tạo được liên kết file trên máy;
chưa coi phần bỏ qua là được kiểm.

Test hiện có không chứng minh regex đúng trên hồ sơ thật, hay địa chỉ v2 đã
triển khai. Không chạy nghiệm thu UI/Electron hoặc đóng gói cài đặt mới.
TASK-3 vẫn In Progress; TASK-4/TASK-5 vẫn To Do. Xem
[bàn giao từng việc](../notary-20261005/README.md).

## Dọn vỏ thư mục sau phiên

Sau khi phiên đang giữ thư mục đóng, chỉ xóa vỏ rỗng bằng `Remove-Item -LiteralPath`
**không dùng `-Recurse`**, rồi xóa thư mục cha `1aae` nếu cũng rỗng. Nếu phát sinh
file mới thì dừng và kiểm tra; không xóa đệ quy. Dữ liệu phục hồi giữ ở root.
