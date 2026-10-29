# STACK — agent đọc trước tiên

Mục đích: agent tự chạy vòng làm việc mà không hỏi lại. Không ghi secret vào file này.
Ký hiệu: ✅ đã mở file/cấu hình để kiểm chứng (2026-10-29) · ⚠️ chưa kiểm chứng / kiểm chứng một phần.

## 1. Stack

| Thành phần | Thực tế | Kiểm chứng |
|---|---|---|
| App | Electron shell (`shell/`, `shell/src/main/main.js`) + sidecar Python (`notary_v2/`, `upload_lab/`) | ✅ |
| Coder | omp (`~/.bun/bin/omp`), cấu hình `~/.omp/agent/config.yml` trên cloud box: `default: openai-codex/gpt-6.1-sol:medium`, `smol: xompet/deepseek-v4.1-flash`, fallback chain có `xompet/glm-5.3-flash`. Chạy không tương tác: `omp -p "<việc>" </dev/null` | ✅ config · ⚠️ lệnh chạy theo quy ước, không có trong repo |
| Commit | Vai trò commit có sẵn của omp: `omp commit` (v18.12.5; pipeline conventional/agentic, model role `default`, bước nhẹ role `smol`; không tạo agent riêng). Gọi qua `tools/dev/omp-commit.sh "<vì sao, #issue/D-xxx>"`: stage trước, script nạp chuẩn [`COMMIT.md`](COMMIT.md) qua `-c`, `--no-changelog`, rồi chạy `tools/ci/commitlint.py` trên commit vừa tạo. Điều phối: Mika giao việc → `omp -p` sửa code (không commit) → Mika/Reviewer soát diff → `omp-commit.sh` commit → push/PR | ✅ `omp commit --help` |
| Điều phối / review | Mika (coordinator) giao việc, Reviewer bot review diff trước khi báo xong (AGENTS.md "Luật cho coder agent") | ⚠️ chỉ quy ước, không có cấu hình trong repo |
| Proxy model | CLIProxyAPI nghe `127.0.0.1:8317` trên cloud box | ✅ (process `cli-proxy-api` đang listen) |
| CI | `.github/workflows/ci.yml`: `js-unit`, `pytest-linux`, `pytest-windows` (bắt buộc), `e2e-smoke` (`continue-on-error`, chưa bắt buộc). `security.yml`: `gitleaks`, `actionlint`. Lỗi đã biết: `tools/ci/known-failures-js.txt`, `known-failures-py-linux.txt`, `known-failures-py-windows.txt` (đọc bởi `tools/ci/known_failures.py`) | ✅ |
| Branch protection | Nhánh mặc định `consolidate/monorepo`: chỉ qua PR, 5 check bắt buộc pytest-linux, pytest-windows, js-unit, actionlint, gitleaks | ✅ |
| Python local | Mỗi worktree: `tools/dev/setup-worktree.sh` (venv Python 3.12 dùng chung `~/.cache/systemdocs/venv-py312` + `npm ci`), rồi `tools/dev/run-tests.sh` (pytest + node --test + known-failures như CI, `--basetemp ~/workspace/tmp-pytest`). Windows: [`SETUP.md`](SETUP.md) | ✅ |
| E2E | `tools/ci/e2e-smoke.sh` (Electron + Xvfb + CDP, profile rỗng); selector trong `docs/screen-map.yaml` (sinh bởi `tools/screen-map/`); harness `/workspace/usability/launch-app-cdp.sh` trên box; skill `.omp/skills/reproduce-and-fix/SKILL.md` | ✅ |
| Báo lỗi | `tools/file-bug.sh` in markdown issue + chép ảnh vào `docs/evidence/<mã>/`; ảnh push lên nhánh `evidence/<mã>` (không merge). Che PII/đường dẫn/token cho log Python: PR #30 | ✅ script · ⚠️ `file-bug.sh` không tự che PII — chỉ dùng dữ liệu giả lập |

## Agent luôn nạp

Chỉ nạp cố định 4 nguồn sau ở đầu phiên:

1. [`AGENTS.md`](../AGENTS.md)
2. `docs/STACK.md` (file này)
3. [`docs/README.md`](README.md)
4. Bảng issue: GitHub Issues đang mở của repo (`gh issue list` / cursor-github)

Mọi file khác (spec, decision, contract, code, `graphify-out/`) **đọc khi cần** cho
việc đang làm, theo con trỏ trong các nguồn trên — không nạp sẵn.

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
| Cài đặt / chạy / test local | [`SETUP.md`](SETUP.md), `tools/dev/` |
| Chuẩn commit | [`COMMIT.md`](COMMIT.md), `.gitmessage` |
| Tiến độ | §4 dưới đây — tracker tiến độ **duy nhất** |
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

Đây là tracker tiến độ duy nhất (không ghi tiến độ ở file khác). Mỗi PR merge phải cập nhật mục này trong chính PR đó (checklist PR template).


- **Xong:** CI + known-failures + gitleaks/actionlint + branch protection; fix Linux/Windows CI (#15–#19, PR #25, #27); form lỗi + log xoay vòng + che PII (PR #30); sổ D-001…D-050 (PR #29); mục lục nguồn chuẩn + glossary (PR #35); tách tên "luật chặn chủ đất còn sống" khỏi Luật A + legal-baseline chưa luật sư rà soát (PR #36); luật sơ đồ v2 (PR #32); D-051 thiếu Chủ đất vẫn Lưu/Evaluate kèm cảnh báo, đóng #31 (PR #37); known-failures py linux/windows rỗng.
- **Xong (tiếp):** D-030 sơ đồ Thừa kế lỗi cấu trúc lưu với `status: invalid` (PR #39); môi trường test local giống CI, SETUP.md, chuẩn commit + job `commitlint` chưa bắt buộc, mục "Agent luôn nạp" (PR này).
- **Đang làm:** #33 Zalo hai mặt CCCD thành 2 người (chờ quyết định).
- **Tiếp theo:** `commitlint` thành bắt buộc khi các PR mới đều đạt; #7 tier frontier/worker qua CLIProxyAPI; #11 chuyển key omp sang biến môi trường; `e2e-smoke` thành bắt buộc sau ~10 lần xanh liên tiếp; bot theo từng area (⚠️ chưa có issue).
