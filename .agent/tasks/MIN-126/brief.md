# Brief — MIN-126

**Linear:** https://linear.app/minhnotary/issue/MIN-126/ui-p3-lam-ban-mau-tuong-tac-dje-duyet-bo-cuc-notary-va-upload · **Ngày bắt đầu:** 2026-09-28 · **Nhánh:** `consolidate/monorepo` tại `D:\systemdocs` (không worktree — chủ dự án chốt commit trực tiếp; worker P2 chạy song song ở `contracts/` + docs Notary → kỷ luật `git add` theo đường dẫn sở hữu)

## Mục tiêu

Làm bản mẫu tương tác (HTML/CSS/JS độc lập, dữ liệu giả, không backend) để owner duyệt bố cục Notary + Upload trước P4 — chi tiết yêu cầu/điều kiện hoàn thành ở Linear MIN-126 và `.agent/tasks/MIN-123/plan.md` mục 4 (P3).

## Phạm vi

- Repo/module ảnh hưởng: chỉ `docs/product/ui/prototypes/` + `.agent/tasks/MIN-126/`.
- File/thư mục dự kiến sửa: `index.html`, `prototype.css`, `app.js`, `data.js`, `notary.js`, `upload.js`, `README.md` trong `docs/product/ui/prototypes/`; task files trong `.agent/tasks/MIN-126/` (+ `screenshots/` nếu chụp được).
- Ranh giới dùng chung cần giữ: **không** sửa runtime `shell/`, không sửa `contracts/`, không sửa `DESIGN.md`/`EXPERIENCE.md`/`tokens.json` (token đổi → ghi đề xuất trong handoff). Lựa chọn nghiệp vụ chưa chốt chỉ ghi trong README/decisions — không rải chú thích lên UI, không tự chốt.

## Bằng chứng nghiệm thu

- `index.html` mở bằng `file://` hoặc static server — tương tác kéo/thả, dialog, focus, resize, chuyển tab giữ trạng thái hoạt động.
- Ảnh chụp playwright (venv `notary_v2/venv` có sẵn) các màn ở 1280×800 / 1366×768 / 1920×1080 vào `.agent/tasks/MIN-126/screenshots/`.
- `git status` trước commit: chỉ stage đường dẫn thuộc phạm vi; không `git add -A`.
