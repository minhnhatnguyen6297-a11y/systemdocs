# STACK — agent đọc trước tiên

Mục đích: agent tự chạy vòng làm việc mà không hỏi lại. Không ghi secret vào file này.
Ký hiệu: ✅ đã mở file/cấu hình để kiểm chứng (2026-10-29) · ⚠️ chưa kiểm chứng / kiểm chứng một phần.

## 1. Stack

| Thành phần | Thực tế | Kiểm chứng |
|---|---|---|
| App | Electron shell (`shell/`, `shell/src/main/main.js`) + sidecar Python (`notary_v2/`, `upload_lab/`) | ✅ |
| Coder | omp (`~/.bun/bin/omp`), cấu hình `~/.omp/agent/config.yml` trên cloud box: `default: openai-codex/gpt-6.1-sol:medium`, `smol: xompet/deepseek-v4.1-flash`, fallback chain có `xompet/glm-5.3-flash`. Chạy không tương tác: `omp -p "<việc>" </dev/null` | ✅ config · ⚠️ lệnh chạy theo quy ước, không có trong repo |
| Điều phối / review | Mika (coordinator) giao việc, Reviewer bot review diff trước khi báo xong (AGENTS.md "Luật cho coder agent") | ⚠️ chỉ quy ước, không có cấu hình trong repo |
| Proxy model | CLIProxyAPI nghe `127.0.0.1:8317` trên cloud box | ✅ (process `cli-proxy-api` đang listen) |
| CI | `.github/workflows/ci.yml`: `js-unit`, `pytest-linux`, `pytest-windows` (bắt buộc), `e2e-smoke` (`continue-on-error`, chưa bắt buộc). `security.yml`: `gitleaks`, `actionlint`. Lỗi đã biết: `tools/ci/known-failures-js.txt`, `known-failures-py-linux.txt` (đọc bởi `tools/ci/known_failures.py`) | ✅ |
| Branch protection | Nhánh mặc định `consolidate/monorepo`: chỉ qua PR, 5 check bắt buộc pytest-linux, pytest-windows, js-unit, actionlint, gitleaks | ✅ |
| Python local | venv `/workspace/venv2` (Python 3.13.5); chạy `pytest --basetemp ~/workspace/tmp-pytest` | ✅ venv · ⚠️ basetemp theo quy ước |
| E2E | `tools/ci/e2e-smoke.sh` (Electron + Xvfb + CDP, profile rỗng); selector trong `docs/screen-map.yaml` (sinh bởi `tools/screen-map/`); harness `/workspace/usability/launch-app-cdp.sh` trên box; skill `.omp/skills/reproduce-and-fix/SKILL.md` | ✅ |
| Báo lỗi | `tools/file-bug.sh` in markdown issue + chép ảnh vào `docs/evidence/<mã>/`; ảnh push lên nhánh `evidence/<mã>` (không merge). Che PII/đường dẫn/token cho log Python: PR #30 | ✅ script · ⚠️ `file-bug.sh` không tự che PII — chỉ dùng dữ liệu giả lập |

## 2. Cái gì ghi ở đâu

| Nội dung | Nơi |
|---|---|
| Thuật ngữ | `docs/glossary.md` |
| Luật vs nghiệp vụ | `business-rules.md` (cột "Lệch luật?"), `legal-baseline.md`, trường `Loại` trong D-xxx |
| Quyết định nghiệp vụ | `docs/decisions/decision-80-…` (D-xxx); quyết định khác `_bmad-output/decisions/` |
| Spec module | `_bmad-output/specs/` |
| Luật agent | `AGENTS.md` |
| Trạng thái task | GitHub Issues (nhãn `area:*`, `needs-approval`, `needs-evidence`) |
| PR template | `.github/pull_request_template.md` |
| Định nghĩa xong | `docs/definition-of-done.md` |
| Registry worktree | `~/workspace/goals/h-th-ng-c-ng-ch-ng-systemdocs/hidden_files/worktree-registry.md` (cloud box, ngoài repo) |

Mục lục đầy đủ: [`docs/README.md`](README.md).

## 3. Vòng chuẩn

1. Issue có bằng chứng (form `bug_report.yml`). Thiếu mục ⇒ nhãn `needs-evidence`, không xử lý, hỏi bổ sung.
2. Nhánh `agent/<agent>/<slug>` từ `origin/consolidate/monorepo`, worktree riêng, ghi một dòng vào registry.
3. Tái hiện (test fail hoặc CDP theo `screen-map.yaml`). Chưa tái hiện được ⇒ không sửa.
4. Sửa trong phạm vi issue; đổi hành vi ⇒ sửa spec/decision trước.
5. Test kèm lệnh + output thật; lỗi đã biết chỉ vào `known-failures-*` kèm issue.
6. PR theo template, review (Reviewer bot), 5 check bắt buộc xanh.
7. Merge commit (không squash). Đóng issue hoặc để comment handoff; cập nhật registry.

## 4. Lộ trình

- **Xong:** CI + known-failures + gitleaks/actionlint + branch protection; fix Linux/Windows CI (#15–#19, PR #25, #27); form lỗi + log xoay vòng + che PII (PR #30); sổ D-001…D-050 (PR #29); mục lục nguồn chuẩn + glossary (PR này).
- **Đang làm:** PR #32 diagram-rules-v2; #31 câu hỏi nghiệp vụ (ô Chủ đất trống); #33 Zalo hai mặt CCCD thành 2 người.
- **Tiếp theo:** #7 tier frontier/worker qua CLIProxyAPI; #11 chuyển key omp sang biến môi trường; `e2e-smoke` thành bắt buộc sau ~10 lần xanh liên tiếp; bot theo từng area (⚠️ chưa có issue).
