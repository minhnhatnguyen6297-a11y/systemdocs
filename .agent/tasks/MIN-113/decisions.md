# MIN-113 decisions

1. **Verifier agent `e33d87e3` bị treo** (~8h, hoàn thành install + sidecar build
   + packaged build + fixture rồi stall, không process active) → parent tiếp quản
   phần verify còn lại trực tiếp. Bài học: packaged GUI launch cần `timeout`
   wrapper — parent đã dùng `timeout 25` và lấy được log evidence đầy đủ.

2. **E2E scripted qua `command_registry.COMMANDS` + `JobStore` thật** thay vì
   cần Electron UI cho phần logic — UI packaged smoke verify riêng bằng exe.
   Real-mode E2E chạy trên `notary.db` worktree-local (`D:\systemdocs-min-113\`),
   KHÔNG đụng DB user ở checkout chính — đúng ranh giới "fixture/output ở DB tạm".

3. **`word.template_missing` cho `niem_yet` trong fixture** — cố ý để batch
   3 văn bản luôn ra `partial` (2 saved + 1 failed) → test đúng kịch bản
   nghiệm thu "ép 1 lỗi trong batch ba file, 2 file còn nguyên".

4. **Cutover KHÔNG tự thực hiện** — nghiệm thu Linear ghi "chỉ sau owner duyệt
   mới chuyển entry mặc định". Task này dừng ở bằng chứng + checklist.
