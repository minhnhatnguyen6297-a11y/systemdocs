# Decisions — MIN-109

Chỉ ghi quyết định trong phạm vi task. Contract
`notary.case-drafting.v1` là immutable — mọi lựa chọn bám theo §7 và
hành vi mock adapter đã duyệt.

## 2026-09-21 — Service mới `inheritance_workspace.py`, tái dùng seam `case_workspace`

- **Chọn:** Tạo `InheritanceWorkspaceService` giữ một
  `CaseWorkspaceService` trên cùng session để tái dùng `_compose_stage`,
  `_revision`, `_build_payload`, `_sync_participants_and_owner`,
  `_v2_to_legacy_nodes`, `_people_map`.
- **Lý do:** Stage composition, revision guard, legacy projection và
  participant/owner sync đã được MIN-107 implement + test; viết lại sẽ
  tạo hai nguồn sự thật cho cùng một payload format.
- **Loại bỏ:** Thêm method vào `CaseWorkspaceService` — brief yêu cầu
  service riêng (`notary_v2/services/inheritance_workspace.py`) để
  Diagram business rule tách khỏi Stage business rule.
- **Nguồn:** `.agent/tasks/MIN-109/brief.md`.

## 2026-09-21 — Phần lớp validate wire state nằm ở service, không phải engine

- **Chọn:** `_validate_diagram_wire` kiểm version literal 2, shape node,
  strict Python boolean, slot refs, dangling/self/spouse-conflict/cycle
  **trước** khi gọi engine; mọi lỗi → `diagram_invalid_state` kèm
  `details.errors[]` mang engine code §7.3.
- **Lý do:** Engine `run_inheritance_case` heal một số input (spouse link
  một chiều, boolean coerce). Contract yêu cầu strict wire: string
  boolean, legacy field (`parentSlotId`, `familyGroupId`, `role`,
  `relationType`, `person`...) phải bị reject, không heal.
- **Loại bỏ:** Sửa engine để strict mode — brief cấm đổi engine trừ khi
  bắt buộc; engine là authority cho tính toán, không phải wire validation.
- **Nguồn:** contract §7.1/§7.3 + mock adapter `notary_mock_adapter.py`.

## 2026-09-21 — Engine error phân hai lớp: outcome vs structural

- **Chọn:** Engine trả `errors[]` thì outcome codes
  (`missing_land_owner`, `invalid_death_date`, `conservation_failed` và
  reserved `second_order_required`, `representation_depth_exceeded`) giữ
  trong `render_model` (status `invalid`/`unsupported`); mọi code khác →
  job error `diagram_invalid_state`.
- **Lý do:** Contract §7.2 định render_model chứa cả lỗi nghiệp vụ
  (ví dụ thiếu Chủ đất) — đó là evaluate thành công trả model, không
  phải command error. Lỗi cấu trúc phải là `diagram_invalid_state` theo
  §7.3 — đã được service bắt trước, lớp kiểm engine là defense-in-depth.
- **Nguồn:** contract §7.2/§7.3.

## 2026-09-21 — Pool warning `diagram.unassigned_pool_person`

- **Chọn:** Sau khi engine chạy, nếu `status != invalid` và còn người
  Stage chưa được gán (`personId` trên node không `deleted`), append
  warning `diagram.unassigned_pool_person` và downgrade
  `complete` → `incomplete`.
- **Lý do:** Pool là projection (Stage committed − assigned), không
  persist; contract drafting-tab §2 yêu cầu biểu lộ người chưa gán.
  `hidden` vẫn tính assigned, `deleted` không — khớp semantics đã test.
- **Nguồn:** contract drafting-tab §2/§6; semantics hidden/deleted kiểm
  chứng bằng test.

## 2026-09-21 — `case_type_unsupported` guard nhưng hiện unreachable

- **Chọn:** Check `case_type != inheritance` ở cả evaluate và save
  (evaluate trước Stage compose, save sau locked check).
- **Lý do:** `InheritanceCase` chưa có cột case_type — `_case_meta` luôn
  trả `inheritance` theo precedent MIN-108; guard sẵn cho khi case_type
  thành explicit column. Comment trong code ghi rõ branch unreachable.
- **Nguồn:** brief §unsupported case types; precedent MIN-108.

## 2026-09-21 — Atomic revision bump bằng guarded UPDATE

- **Chọn:** `UPDATE inheritance_cases SET workspace_revision=:rev WHERE
  id=:cid AND workspace_revision=:base`; `rowcount != 1` → rollback +
  `workspace_conflict` kèm `server_revision` mới nhất.
- **Lý do:** Giống hệt pattern `commit_stage` — hai save cùng
  `base_revision` chỉ một cái thắng; đảm bảo revision tăng đúng một lần
  trong transaction atomic.
- **Nguồn:** `services/case_workspace.py` (MIN-107 precedent).
