# Chuẩn commit

Theo [Conventional Commits](https://www.conventionalcommits.org/vi/v1.0.0/), rút gọn.
CI kiểm bằng `tools/ci/commitlint.py` (job `commitlint`, **chưa bắt buộc**).

## Dạng

```text
<type>(<scope>): <tóm tắt ngắn, ≤72 ký tự, không chấm cuối>

Cái gì: thay đổi gì.
Vì sao: lý do / lỗi / quyết định owner.
Tính năng: màn hình hoặc luồng bị ảnh hưởng.

Refs: #123, D-030
```

- **type**: `feat` (tính năng), `fix` (sửa lỗi), `docs`, `test`, `refactor`,
  `perf`, `build`, `ci`, `chore`, `revert`. Thay đổi phá tương thích: thêm `!`
  (`feat(contracts)!: …`).
- **scope** = module, chữ thường: `notary`, `diagram`, `shell`, `sidecar`,
  `upload`, `zalo`, `contracts`, `docs`, `ci`, `tools`. Bắt buộc có.
- **body** bắt buộc: cái gì / vì sao / tính năng nào.
- **tham chiếu** bắt buộc: issue `#123`, quyết định `D-xxx`, hoặc dòng `Refs:`
  (không có issue thì ghi `Refs: không có — <lý do>`).
- Merge commit được bỏ qua.

Ví dụ:

```text
fix(diagram): lưu sơ đồ lỗi cấu trúc với status invalid

Cái gì: diagram_save ghi state + errors thay vì từ chối diagram_invalid_state.
Vì sao: owner chốt theo D-030 (29/10/2026).
Tính năng: Lưu hồ sơ ở màn Sơ đồ thừa kế.

Refs: D-030, D-048
```

## Agent commit

Agent không tự viết message: stage file rồi chạy
`tools/dev/omp-commit.sh "<vì sao, #issue/D-xxx>"` (vai trò `omp commit`, xem `docs/STACK.md` §1).

## Dùng mẫu có sẵn

```bash
git config commit.template .gitmessage
```

Kiểm tra trước khi push: `python tools/ci/commitlint.py origin/consolidate/monorepo HEAD`.

## Tiêu đề PR và cách merge

- Repo merge bằng **merge commit, không squash** (`docs/STACK.md` §3), nên từng
  commit trong PR phải đúng chuẩn.
- Tiêu đề PR cũng theo dạng `<type>(<scope>): <tóm tắt>` (job `commitlint` kiểm).
  Nếu sau này đổi sang squash-merge, tiêu đề PR thành commit message trên nhánh
  chính — khi đó tiêu đề PR là bắt buộc đúng chuẩn.
