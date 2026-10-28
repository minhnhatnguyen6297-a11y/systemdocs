---
name: reproduce-and-fix
description: Tái hiện một lỗi UI của systemdocs qua harness CDP (theo docs/screen-map.yaml), thu bằng chứng bằng tools/file-bug.sh, rồi sửa có giới hạn và dừng ở commit local + bản nháp PR. Dùng khi owner giao "tái hiện/sửa bug" có bước thao tác cụ thể. Không push.
---

# Reproduce and fix (systemdocs)

Chuyển thể từ pstack `reproduce-and-fix-issues`
(https://github.com/cursor/plugins/tree/main/pstack/automations/benny/skills/reproduce-and-fix-issues),
bỏ phần Slack/triage; giữ: fail-closed, tái hiện 2 lần bằng UI thật, bằng chứng trước/sau,
không sửa khi chưa tái hiện được.

## Luật cứng
- Chỉ dữ liệu giả lập; profile app tạm (launch-app-cdp.sh tự tạo). Không dùng dữ liệu khách hàng.
- Làm trong worktree riêng trên nhánh `agent/<tên>/<việc>`; không `git stash`, không code trên `main`.
- **Không push, không tạo PR thật.** Kết thúc ở commit local + văn bản PR nháp; push cần owner duyệt.
- Không ép triệu chứng bằng cách sửa state/DOM/DB. Đọc state chỉ để đối chiếu.
- Chưa tái hiện được ⇒ không viết fix. Đã có commit/PR sửa ⇒ chuyển sang chế độ xác minh, không viết đè.
- Thay đổi kiến trúc/schema/dependency ⇒ dừng, báo phương án cho owner.
- Ảnh/log bằng chứng chỉ commit qua `tools/file-bug.sh` (đã rút gọn); không commit profile, token.

## 1. Kiểm tra điều kiện (fail closed)
Cần đủ, thiếu thứ nào thì báo `Blocked: thiếu <X>` và dừng:
- `docs/screen-map.yaml` có màn khớp đường đi của lỗi (chạy `tools/screen-map/gen-screen-map.sh` nếu cũ).
- Harness `/workspace/usability/` (launch-app-cdp.sh, ux.cjs, stop-app-cdp.sh) và Playwright (`UX_PW`).
- `tools/file-bug.sh` (từ nhánh agent/mika/bug-evidence) có trong worktree.

Bảng năng lực adapter (theo control-adapter của pstack):

| Năng lực | Cách làm ở systemdocs |
|---|---|
| Bring up | `REPO=$PWD CDP=1 CDP_PORT=<p> /workspace/usability/launch-app-cdp.sh` |
| Điều hướng theo map | `reach_from_launch` của màn trong screen-map → `node ux.cjs click ...` |
| Drive UI | `ux.cjs click/fill/type/select/press/drag/pickfile/msgbox/upload` |
| Inspect (read-only) | `ux.cjs snapshot`, log `<profile>/app.log`, sidecar log |
| Screenshot | `ux.cjs shot <file.png>` |
| Recording | `UX_LOG` jsonl (replay bằng ux-record.cjs); chưa có video — ghi rõ khi báo cáo |
| Cleanup | `CDP_PORT=<p> /workspace/usability/stop-app-cdp.sh` |

## 2. Hiểu báo cáo
Ghi: đường thao tác, kỳ vọng, thực tế, điểm phân kỳ, tần suất, commit/nhánh, ảnh/log.
Tra màn tương ứng trong screen-map: selector, `related_tests`, `gotchas`.
Đọc `graphify-out/` và code liên quan; nêu ≥2 giả thuyết nguyên nhân cạnh tranh.

## 3. Tái hiện (2 lần độc lập)
1. Launch app trên commit lỗi; chờ status hết `engine_unavailable`.
2. Đi theo `reach_from_launch`, rồi các bước của báo cáo bằng ux.cjs (selector `role:Tên`).
3. Gọi tên trạng thái ĐÚNG và trạng thái LỖI; dừng ở điểm phân kỳ; `ux.cjs shot`.
4. Stop + launch lại (profile mới), lặp lại y hệt. Phải thấy lỗi giống lần 1.
5. Đối chiếu một giá trị thật (snapshot/log) nếu được.
Không tái hiện được trong ngân sách ⇒ báo `Could not reproduce` + các bước đã thử. Dừng.

## 4. Đóng gói bằng chứng
```bash
tools/file-bug.sh --title "<tiêu đề>" --repro "<chuỗi lệnh ux.cjs>" \
  --expected "<đúng>" --actual "<lỗi>" --shot <ảnh-lần-2.png>
```
Commit thư mục `docs/evidence/<id>/` vừa sinh: `git commit -m "evidence: <tiêu đề>"`.

## 5. Sửa có giới hạn
Chỉ khi: tái hiện xác nhận 2 lần, ảnh thể hiện rõ trạng thái lỗi, chưa có fix khác,
nguyên nhân gốc có bằng chứng runtime, thay đổi nhỏ trong phạm vi.
- Viết test hỏng trước (unit trong `related_tests` của màn) → sửa nhỏ nhất ở nguyên nhân gốc.
- Không dọn dẹp ngoài phạm vi. Phình to ⇒ dừng, báo owner.

## 6. Chứng minh
- Chạy lại đúng đường UI 2 lần trên bản sửa: lỗi biến mất, trạng thái đúng xuất hiện; chụp ảnh "sau".
- `cd shell && npm test`, pytest liên quan, so với `tools/ci/known_failures.py` (không thêm lỗi mới).
- Smoke các màn lân cận trong screen-map.
- Review bắt buộc (Superpowers `requesting-code-review` hoặc Reviewer).

## 7. Kết thúc: commit local + PR nháp
- Commit nhỏ theo thứ tự (test → fix → evidence). Quét `gitleaks git --redact -c .gitleaks.toml .`.
- Viết PR nháp theo `.github/pull_request_template.md` (trước/sau, lệnh + output, rủi ro) vào báo cáo.
- **Dừng.** Báo owner: nhánh, commit, PR nháp; push/PR thật chờ duyệt.
- Luôn chạy stop-app-cdp.sh.
