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
- **Ghi đè đường dẫn Superpowers:** skill brainstorming/writing-plans mặc định ghi
  `docs/superpowers/...`. Trong repo này: spec/design → `docs/specs/<module>/`,
  plan → `docs/plans/YYYY-MM-DD-<slug>.md`. Không tạo `docs/superpowers/`.
- Thuật ngữ: `docs/glossary.md`. Danh mục quyết định: `docs/decisions/README.md`.

## Thứ tự đọc trước việc nghiệp vụ

`docs/specs/product-overview.md` → `docs/decisions/README.md` → sổ D-xxx
(`docs/decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md`) →
`docs/specs/notary_v2/diagram/inheritance/legal-baseline.md` →
`business-rules.md` → `docs/specs/notary_v2/diagram-rules.md` → `graphify-out/` → code.

## Giao thức hỏi owner (D/Q)

- Trước khi hỏi: tra D-xxx → luật → code. Đã có câu trả lời thì dùng, không hỏi lại.
  Mặc định theo luật trừ khi D-xxx chốt lệch.
- Chỉ hỏi lựa chọn nghiệp vụ thật; gom một lượt; mỗi câu có bối cảnh, mặc định luật
  (số điều), khuyến nghị, lý do, ảnh hưởng code. Ghi câu hỏi vào Q-xxx
  (`business-rules.md` §10).
- Owner trả lời xong: thêm D-xxx vào cuối decision-80 ngay trong phiên (không đánh
  số lại, không xoá; bị thay thì sửa dòng Trạng thái) và đánh dấu Q-xxx đã chốt.
- Trích dẫn luôn kèm file: `decision-80 §D-041` (khác `decision-41`).
- Bộ nhớ của agent không phải nơi lưu quyết định; chỉ giữ con trỏ.

## Commit

- Khi xong, tạo commit nhỏ, rõ ràng. Trước khi xóa hoặc move hàng loạt, tạo commit
  bảo lưu; hỏi owner nếu phạm vi chưa rõ.

## Tra cứu trước / không xu nịnh

- Nếu gặp vấn đề mới hoặc không chắc chắn có bằng chứng, hãy tra cứu GitHub để tìm kiếm lời giải/repo/skill tương tự trước khi tự xây từ đầu.
- Dùng skill `search-first` (repo, package, GitHub, web) và `find-skills` (skills.sh / `npx skills find`) để tìm có hệ thống, không tìm mò.
- Không mặc định đồng ý với người dùng. Nếu thấy giả định sai hoặc đã có lời giải sẵn, nói rõ bất đồng kèm bằng chứng.
- Thứ tự trả lời: (1) phát hiện/bất đồng có bằng chứng, (2) nguồn đã tìm, mỗi nguồn BẮT BUỘC kèm URL đầy đủ và đã kiểm tra tồn tại, (3) rồi mới đề xuất: dùng lại / mở rộng / tự xây. Nói rõ kênh tìm nào không dùng được.
