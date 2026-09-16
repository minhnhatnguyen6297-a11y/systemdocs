# Contract: G1 Module Data `v1`

**Version:** `g1.module.v1` · **Status:** APPROVED (owner duyệt 14/09/2026) ·
**Owner:** module `shell/` — trước đây branch `electron-system-shell` ·
**Published:** P3 / MIN-72 · **Kênh mang:** `desktopcommand.v1`
(`contracts/desktop-command.md`)

Shape dữ liệu chung trong `payload`/`result`/`error` giữa Electron shell và
Python sidecar trên một máy. **Đây không phải** contract xuyên-sản-phẩm
(ConversionEnvelope giữa các repo vẫn theo Gate A–D của
`docs/g1/MIN62_DATA_CONTRACT_DRAFT.md` — file đó là normative reference, không
bị tài liệu này thay thế).

## 1. Vocabulary dùng lại (không nhân bản)

- `IdentityEvidence` — định nghĩa trường ở `MIN62_DATA_CONTRACT_DRAFT.md` §2.1.
- Tiến trình trạng thái `SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED` —
  MIN-62 draft §1. Unconfirmed không bao giờ thành business truth.
- Chuẩn hóa định danh — `contracts/entities.md` (CCCD 12 số; serial GCN
  `[A-Z]{2}\d{6,8}`; số công chứng `xxx/yyyy`; thửa+tờ là cặp).
- Nguyên tắc null/unknown — MIN-62 draft §4.

## 2. JobResult (`result` của job)

```yaml
result:
  kind: <snake_case>             # extraction | scan_report | audit_report |
                                 #   ocr_result | word_export | zalo_batch | ...
  data: <object>                 # domain shape của repo owner — KHÔNG ép
                                 #   vocabulary chung lên enum nội bộ
  evidence: [<IdentityEvidence>] # optional — chỉ khi có so khớp/trích định danh
  warnings: [{ code, message, source_ref? }]
  source_files: [<file_ref>]     # file đầu vào đã dùng — provenance đầu chuỗi
```

`file_ref` theo `desktop-command.md` §6 (`machine_local` only trong G1-SM).

## 3. IdentityEvidence — ràng buộc dùng trong G1

Ngoài shape ở MIN-62 §2.1, trong kênh này:

- `observation_state ∈ {observed, normalized, inferred, confirmed}`.
- `normalized_value` phải khớp canonical của `contracts/entities.md` nếu
  `observation_state` ≥ normalized; không khớp → `evidence_invalid`.
- `normalized_value: null` hợp lệ chỉ khi `observation_state = observed`.
- `confidence` chỉ ý nghĩa khi state là `inferred`; `confirmed` đến từ hành
  động người (command `waiting_on=review/confirm`), không phải field.
- `kind` mở rộng được nhưng phải đăng ký trong §5 namespace; không đổi nghĩa
  kind đã phát hành.

## 4. ErrorObject

Dùng nguyên shape ở `desktop-command.md` §4 `error`. Namespace code mở:

`engine.*` (engine_restarted, engine_not_installed, engine_unavailable,
engine_version_mismatch), `upload.*`, `ocr.*`, `zalo.*`, `file.*`
(file_scope_not_supported, file_not_found, file_locked), `auth.*`,
`payload.*`, `contract.*` (unsupported_contract_version), `matching.*`.

Producer thêm code mới được; đổi nghĩa code đã phát hành → tăng major version.

## 5. Write ownership (G1-SM — một máy)

| Dữ liệu | Owner ghi | Shell/renderer được phép |
|---|---|---|
| Job/command registry | sidecar | đọc `GET /v1/jobs`, không ghi trực tiếp |
| `notary.db`, `registry.sqlite3` | sidecar/engine | **không đọc/ghi trực tiếp** — qua command |
| OCR call audit, Evidence | sidecar | hiển thị; không sửa/xóa |
| `output/`, `runs/`, `downloads/`, `word_templates/custom/` | sidecar | chọn file qua dialog; không ghi thẳng |
| Session portal (`nd_storage_state.json`), credential | sidecar | **không bao giờ qua contract** |
| UI-only state (theme, window bounds, last module) | shell | tự quản, không qua contract |

## 6. Null/unknown/warning — binding cho renderer

- `null` = không quan sát được / không áp dụng. `""` **không hợp lệ** thay
  null — validator reject. Renderer hiển thị "—"/"Chưa có".
- `warnings` không làm job `confirmed`; warning có `code` + `message`,
  `source_ref` optional.
- `partial` bắt buộc `data.breakdown` — xem desktop-command §5.

## 7. Examples & conformance

- Examples: `contracts/g1/examples/` (valid + invalid kèm `expected_error`).
- Validator: `contracts/g1/validate_examples.py` (stdlib-only, không dep).
- Producer PHẢI: emit đủ trường shape; giữ raw không ghi đè; unconfirmed
  không ghi business table; reject `""`-as-null và FileRef sai scope.
- Consumer PHẢI: check `contract_version`; không parse `error.message` để
  quyết nghiệp vụ; render null an toàn; hiển thị evidence theo
  observation_state.

## 8. Changelog

| Version | Ngày | Thay đổi |
|---|---|---|
| v1 | 14/09/2026 | Publish đầu tiên sau owner duyệt spec P2; binding MIN-62 draft vocabulary vào kênh desktopcommand.v1 |
