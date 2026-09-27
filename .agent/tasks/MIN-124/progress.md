# MIN-124 — Tiến độ

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| Khảo sát nguồn (MIN-123, spec, renderer) | done | |
| Task record `.agent/tasks/MIN-124/` | done | brief + progress + decisions + handoff |
| `docs/product/ui/` (README, DESIGN, EXPERIENCE, tokens) | done | JSON parse OK |
| Chép 2 ảnh approved + metadata | done | byte-identical (md5 trùng), `references/README.md` |
| `notary_v2/.../visual-design.md` | done | |
| `upload_lab/docs/visual-design.md` | done | phụ lục token, không spec song song |
| Đánh dấu `drafting-tab.md` + `spec_UI.md` | done | sửa luôn marker "contract chưa tồn tại" |
| Cập nhật index/spec cũ trỏ nguồn mới | done | README root + shell, spec UX 24/09 (superseded token), spec shell 14/09, contracts/README, case-workspace README, upload_lab README |
| Bản đồ màn hình/trạng thái → file | done | `docs/product/ui/README.md` §4 |
| Danh sách quyết định cần owner | done | `decisions.md` + DESIGN §9 + EXPERIENCE §10 |
| Kiểm link/JSON/scope + commit | done | 0 broken link, diff sạch |

## Nhật ký

- 28/09/2026 — Khảo sát toàn bộ nguồn; ghi nhận `drafting-tab.md` còn
  marker "contract chưa tồn tại" (đã có `contracts/notary-case-drafting.md`)
  và spec UX §3 dẫn token lime/rail-đen hướng cũ → đã sửa.
- 28/09/2026 — Tạo `docs/product/ui/` (README/DESIGN/EXPERIENCE/tokens +
  references), hai `visual-design.md` module, cập nhật 8 file index/spec
  trỏ nguồn mới. Verify: JSON OK, link checker 0 broken, ảnh md5 trùng,
  `git diff --check` sạch, không runtime nào đổi.
- 28/09/2026 — Commit `docs(MIN-124)` trên `consolidate/monorepo`, không push.
