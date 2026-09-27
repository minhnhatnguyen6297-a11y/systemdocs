# Brief — MIN-125

**Linear:** [MIN-125](https://linear.app/minhnotary/issue/MIN-125/ui-p2-chot-hop-djong-du-lieu-stage-3-tai-san-va-30-vi-tri-hai-ben) · **Ngày bắt đầu:** 2026-09-28 · **Nhánh:** `consolidate/monorepo` (commit trực tiếp, không worktree — chủ dự án chốt)

## Mục tiêu
P2 của MIN-123: chốt **contract dữ liệu** cho Stage (vòng đời draft/commit/Hủy, hồ sơ mới qua Cập nhật), 3 tài sản theo vị trí 1..3, sơ đồ thừa kế per-position và sơ đồ hai bên 30 vị trí — **chỉ thiết kế contract + ví dụ** (runtime ở P5/MIN-128). Điều kiện hoàn thành đầy đủ ở Linear.

## Phạm vi
- Repo/module ảnh hưởng: `systemdocs` (contracts), spec Notary đánh dấu.
- File/thư mục được sửa:
  - `contracts/notary-case-drafting.md` — thêm phần **DRAFT rev 2.0** (không sửa phần v1 đã publish).
  - `contracts/notary-case-drafting/` — schema draft + examples draft + `validate_examples.py` (mở rộng additive).
  - `notary_v2/docs/platform/case-workspace/drafting-tab.md` — chỉ mục §10 điểm mở (trỏ sang DRAFT, giữ trạng thái chờ duyệt).
  - `notary_v2/docs/platform/case-workspace/visual-design.md` — chỉ các marker PENDING trỏ sang P2.
  - `.agent/tasks/MIN-125/`.
- **Không sửa:** runtime JS/Python/CSS; `docs/product/ui/prototypes/` (vùng của P3/MIN-126 đang chạy song song); `contracts/README.md`.
- Kỷ luật stage: chỉ `git add` đường dẫn sở hữu; trước commit `git status` — file lạ của P3 thì bỏ qua.

## Ranh giới dữ liệu đã kiểm chứng (file:dòng)
- `case-drafting-model.js`: `pool()`/`assignablePersonIds()` đọc Stage draft khi `caseId==null` (233-258); `addAsset()` không chặn 3 (466); `removeStageRow()` xóa tham chiếu diagram ngay trong draft (517-541); `saveDraft()` (404) / `commitStage()` (573).
- `case_workspace.py:817-825`: `workspace_create` đòi đúng một node `owner` có personId ∈ stage + đúng một `is_primary` (đòi chủ/primary trước khi gán sơ đồ — vòng phụ thuộc).
- `models.py:88-89`: `InheritanceCase.nguoi_chet_id`/`tai_san_id` NOT NULL — owner/primary phải suy ra được lúc tạo.
- `inheritance_workspace.py:53`: node chỉ có `isLandOwner`/`willReceive` boolean.
- `word_engine.py:31` `MAX_WORD_ASSETS=5`; `:825/:852/:937` giới hạn 20 người/người ký; `:966-1010` placeholder `[Tài sản N - field]` theo thứ tự 1..5; `word_batch_export.py:110` block messages.

## Bằng chứng nghiệm thu
- `rtk proxy python contracts/notary-case-drafting/validate_examples.py` → 0 unexpected (v1 giữ nguyên + draft fixtures mới pass).
- Mọi phần đề xuất mới ghi rõ **DRAFT — chờ owner duyệt**; không tuyên bố publish.
- Commit message dạng `docs(MIN-125): ...`/`contract(MIN-125): ...` + footer Devin.
