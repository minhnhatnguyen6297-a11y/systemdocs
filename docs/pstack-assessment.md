# Đánh giá pstack cho omp (2026-10-28)

Nguồn: https://github.com/cursor/plugins/tree/main/pstack (v0.15.36, MIT, tác giả Lauren Tan).
Đã đọc: `automations/benny/skills/reproduce-and-fix-issues/SKILL.md`,
`references/control-adapter.md`, `references/feature-map.example.md`, `plugin.json`.

## Cài được cho omp không?
- `pstack/plugin.json` khai `$schema` Agent Plugins 1.0.0 (agent-plugins.org). Mã nguồn omp đã cài
  (`@oh-my-pi/pi-coding-agent/src/discovery/agent-plugins.ts`) có provider "Agent Plugins" nạp
  `skills/*/SKILL.md` từ plugin root (marketplace install, `--plugin-dir`, extension package).
  ⇒ **Về định dạng: tương thích** (đọc code, CHƯA chạy thử).
- omp còn nạp skill dự án từ `.omp/skills/` (walk-up từ cwd, `discovery/builtin.ts`). Bản nháp
  `.omp/skills/reproduce-and-fix/` trong nhánh này chỉ có hiệu lực khi chạy omp trong worktree này,
  không đụng `~/.omp/agent/config.yml`.
- Rủi ro khi cài nguyên pstack: ~60 skill (principle-*, poteto-mode, unslop…) chồng chéo với
  Superpowers đang thử (agent/omp/superpowers-trial) ⇒ nhiễu context. Benny gắn chặt Slack +
  triage marker, không hợp quy trình một người.
- Khuyến nghị: **không cài cả gói**; chỉ mượn ý tưởng (feature map + control adapter + 2 lần
  tái hiện + bằng chứng trước/sau) qua skill chuyển thể `reproduce-and-fix`. Nếu muốn thử nguyên
  gói: dùng `--plugin-dir` cho một phiên, không ghi config chính.

## Ánh xạ khái niệm
| pstack | systemdocs |
|---|---|
| feature map (Markdown, viết tay) | `docs/screen-map.yaml` (sinh từ CDP, + overrides.json viết tay) |
| control adapter skill | harness `/workspace/usability` (launch-app-cdp.sh, ux.cjs, stop-app-cdp.sh) |
| bằng chứng ở thread Slack | `tools/file-bug.sh` → `docs/evidence/<id>/` |
| draft PR | commit local + văn bản PR nháp (push cần owner duyệt) |

## Khoảng trống
- Harness chưa quay video (pstack yêu cầu recording) — hiện chỉ có jsonl replay + ảnh.
- Harness nằm ngoài repo (`/workspace/usability`), CI không dùng được; nên đưa vào `tools/ux/`.
- `tools/file-bug.sh` chỉ có trên nhánh agent/mika/bug-evidence (chưa merge vào consolidate/monorepo).

## Cập nhật 2026-10-30: nhận `interrogate` và `tdd`
- Đã đưa vào skill dự án omp: `.omp/skills/interrogate/` và `.omp/skills/tdd/` (cạnh `reproduce-and-fix`).
  Vẫn **không cài cả gói**, không đụng `~/.omp/agent/config.yml`. Giữ ghi công MIT: dòng nguồn ở đầu
  mỗi SKILL.md + `LICENSE-pstack` trong từng thư mục.
- Vì sao: `tdd` ép có test hỏng-trước/qua-sau cho bug có đường test rẻ (khớp vòng chuẩn + CI pytest/js-unit);
  `interrogate` cho review đối kháng mà chỉ giữ phát hiện đã chạy ra lỗi — bù khoảng trống review một người.
- Chuyển thể: `tdd` giữ nguyên. `interrogate` gốc phụ thuộc skill `arena` (Phase A/B/F), `in-your-own-words`,
  `poteto-mode` và model/subagent kiểu Cursor (README nói độc lập nhưng thực tế không) ⇒ đã viết gộp các bước
  cần dùng vào skill, dùng tool `task` của omp và 2 đối thủ theo role `default`/`smol`.
- Cả hai có `disable-model-invocation: true` ⇒ omp không liệt kê trong system prompt; gọi tường minh
  (`/skill:<tên>` hoặc yêu cầu trực tiếp).
- Thử nghiệm: dùng trên việc Word MVP (bot Soạn thảo & Word); đánh giá lại sau đợt đó.
