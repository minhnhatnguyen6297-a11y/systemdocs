# docs/g1 — Tài liệu lộ trình G1/Electron (lịch sử & tham chiếu)

Thư mục này chứa các tài liệu quá trình (process/spec/plan/handoff) của lộ
trình G1 Electron **trước khi gộp monorepo**. Chúng là hồ sơ quyết định và
tham chiếu kỹ thuật — **không phải** đặc tả nghiệp vụ đang áp dụng. Nghiệp vụ
đang áp dụng nằm ở `<module>/docs/SPEC.md`; contract đang áp dụng ở
`contracts/`; kiến trúc hiện tại ở `SYSTEM_ARCHITECTURE.md`.

Các đường dẫn `D:\...`, `upload_lab_repo`, nhánh `electron-system-shell` trong
các file này là **bối cảnh trước khi gộp** — không sửa lại từng file; đọc với
ý thức đó là tài liệu lịch sử. Code hiện tại nằm trong các module của monorepo.

## Trạng thái theo Linear (team MIN)

| File | Linear | Trạng thái issue | Vai trò file |
|---|---|---|---|
| `ELECTRON_G1_PLAN.md` | MIN-56 | In Progress | Kế hoạch + gate tổng của G1; vẫn là lộ trình đang chạy |
| `MIN50_IMPLEMENTATION_SPEC.md` | MIN-50 | In Progress | Spec triển khai MIN-50 (W0–W6) |
| `MIN61_CONVERSION_OCR_DECISION.md` | MIN-61 | Canceled | Hồ sơ quyết định (đã hủy) |
| `MIN62_DATA_CONTRACT_DRAFT.md` | MIN-62 | Done | Draft contract; normative ref của `g1.module.v1` |
| `MIN63_DATABASE_SPEC_DRAFT.md` | MIN-63 | Backlog | Draft DB chung — chưa duyệt, chưa implement |
| `MIN64_UI_SPEC_DRAFT.md` | MIN-64 | Done | Draft UI spec |
| `MIN66_MERGE_READINESS_DRAFT.md` | MIN-66 | Backlog | Checklist merge readiness |
| `COMPONENT_MAP.md` | MIN-57 | Canceled | Bản đồ ownership/reuse trước gộp (snapshot lúc đó) |
| `G1_SINGLE_MACHINE_INVENTORY.md` | MIN-74 | Done | Inventory trước G1 single-machine |
| `G1_SINGLE_MACHINE_COMPATIBILITY_MATRIX.md` | MIN-75 | Done | Compat matrix trước G1 |
| `HANDOFF_2026-09-14.md` | — | — | Handoff lịch sử |
| `DEVIN_HANDOFF_G1_SINGLE_MACHINE.md` | — | — | Handoff lịch sử |
| `specs/` (4 file 2026-09-14) | MIN-50 nhánh con | — | Spec con của lộ trình G1 |

**Quy tắc:** trạng thái công việc tra Linear (team MIN) — không tạo file
task/plan mới trong repo gốc để theo dõi việc. Khi một issue đổi trạng thái,
cập nhật lại cột ở bảng trên.
