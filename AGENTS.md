# AGENTS.md — luật làm việc trong systemdocs

## Workflow: Superpowers (thử nghiệm, nhánh `agent/omp/superpowers-trial`)

- Dùng skill Superpowers cài ở mức project: `.omp/extensions/superpowers/`
  (bootstrap `using-superpowers` tự nạp). Luồng: brainstorming → writing-plans →
  test-driven-development (red/green thật) → requesting-code-review →
  verification-before-completion. Việc ngắn, rõ: không cần ceremony dài nhưng
  vẫn test trước rồi mới code.
- BMAD đã gỡ khỏi repo này. Không dùng skill `bmad-*` (đã ẩn trong
  `.omp/config.yml`). Không nâng cấp BMAD lên v7. Bản BMAD cũ: tag
  `bmad-archive-20261028`.
- Không dùng Orca, không cài 1DevTool. Không chạy script khôi phục lạ từ archive.
- Code tối giản; trao đổi với user tự nhiên, dễ hiểu.

## Nhánh và worktree

- Không bao giờ code trên `main`/nhánh mặc định (`consolidate/monorepo`).
- Mỗi việc một nhánh `agent/<agent>/<slug>` trong worktree riêng ở
  `~/workspace/worktrees/<agent>-<slug>`; ghi vào worktree registry
  (`~/workspace/goals/*/hidden_files/worktree-registry.md`).
- Không đụng worktree của agent khác. Không push khi chưa được owner duyệt.

## Test và dữ liệu

- Chạy pytest với `--basetemp ~/workspace/tmp-pytest/<tên-việc>` (không dùng /tmp
  mặc định), chạy từ root repo, ví dụ:
  `python -m pytest notary_v2/tests -q --basetemp ~/workspace/tmp-pytest/<tên-việc>`.
- Chỉ dùng dữ liệu giả lập (synthetic). Không đưa hồ sơ, CCCD, tên thật hay dữ
  liệu công chứng thật vào test, fixture, log hay commit.
- Không in hoặc ghi token/secret.

## Nguồn chuẩn

| Nội dung | Nơi lưu |
|---|---|
| Hành vi (spec) | `docs/specs/` |
| Quyết định đã chốt (LÀ GÌ + TẠI SAO) | `docs/decisions/` |
| Plan triển khai | `docs/plans/` |
| Nghiên cứu, brief | `docs/planning/` |
| Brainstorm | `docs/brainstorming/` |
| Lịch sử | `docs/archive/` |
| Quan hệ code | `graphify-out/` |

- Spec quyết định hành vi; code chứng minh hiện trạng. Đổi hành vi thì cập nhật
  spec liên quan trước khi sửa code.
- Ghi quyết định của owner vào `docs/decisions/` trong phiên hiện tại.
  File tạm nằm trong `docs/tmp/` (ignored).
- Đọc `graphify-out/` trước khi dò code thủ công.
- Plan/spec viết bằng Markdown; không còn export HTML plan.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

## Tra cứu trước / không xu nịnh

- Nếu gặp vấn đề mới hoặc không chắc chắn có bằng chứng, hãy tra cứu GitHub để tìm kiếm lời giải/repo/skill tương tự trước khi tự xây từ đầu.
- Dùng skill `search-first` (repo, package, GitHub, web) và `find-skills` (skills.sh / `npx skills find`) để tìm có hệ thống, không tìm mò.
- Không mặc định đồng ý với người dùng. Nếu thấy giả định sai hoặc đã có lời giải sẵn, nói rõ bất đồng kèm bằng chứng.
- Thứ tự trả lời: (1) phát hiện/bất đồng có bằng chứng, (2) nguồn đã tìm (link), (3) rồi mới đề xuất: dùng lại / mở rộng / tự xây. Nói rõ kênh tìm nào không dùng được.
