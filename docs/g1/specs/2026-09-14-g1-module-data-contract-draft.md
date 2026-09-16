# SPEC — Contract dữ liệu shell↔engine cho G1 một máy (MIN-62 binding)

> **Trạng thái: DRAFT — chờ owner duyệt (gate D2). Draft chưa duyệt không đặt
> vào `contracts/`; publish thuộc MIN-72 (P3).**
>
> Phạm vi G1-SM: contract giữa **Electron shell** và **Python sidecar** trên
> một máy. Nó tái sử dụng vocabulary của `MIN62_DATA_CONTRACT_DRAFT.md`
> (branch `min-62-data-contract-draft`) bằng tham chiếu — không nhân bản.
> Contract xuyên-sản-phẩm (ConversionEnvelope publish cho consumer repo khác)
> vẫn theo Gate A/B/C/D của draft đó; tài liệu này chỉ chốt phần shell↔engine.

## 1. Tên và version

- Contract: **`g1.module.v1`** — kênh lệnh `desktopcommand.v1` (MIN-64 spec)
  mang payload/result theo shape dưới đây.
- `contract_version` xuất hiện ở mọi request/response. Version mismatch →
  `unsupported_contract_version`, không parse tiếp.
- Compatibility window: sidecar quảng bá `supported_versions: ["v1"]` trong
  `/healthz`; shell từ chối chạy khi ngoài window (ghi `engine_version_mismatch`).

## 2. Shape dữ liệu chung

### 2.1 FileRef (machine scope — quyết định D0-7 đề xuất)

```yaml
file_ref:
  path: "D:/.../file.docx"        # absolute; cho phép \\?\ extended prefix
  scope: machine_local            # G1-SM chỉ chấp nhận giá trị này
  sha256: <optional>
  media_type: <optional>
  size_bytes: <optional>
```

- UNC/`scope: lan_share` → sidecar trả `file_scope_not_supported` trong G1-SM.
- Không dùng path làm identity; khi cần dedup dùng `sha256` (MIN-62 §2.3).
- Path do Electron main chuyển sau file dialog; renderer không tự gửi path.

### 2.2 JobResult payload (result của command)

```yaml
result:
  kind: extraction|scan_report|audit_report|ocr_result|word_export|...
  data: <theo kind — domain của repo owner, không ép vocabulary>
  evidence: [<IdentityEvidence>]     # khi có so khớp — xem §3
  warnings: [{code, message, source_ref?}]
  errors:   []                      # lỗi nặng đã nằm ở job.error
```

`data` giữ nguyên shape domain (upload_lab `web_form`, notary_v2 case JSON) —
contract **không** ép enum nội bộ thành vocabulary chung (MIN-62 §1 nguyên
tắc; MIN-64 job status chỉ là display vocabulary).

### 2.3 ErrorObject (dùng chung mọi kênh)

```yaml
code: <namespace.snake_case>   # engine.*, upload.*, ocr.*, file.*, auth.*
message: <cho người đọc, tiếng Việt>
retryable: true|false
job_id: <id nếu có>
next_action: login_required|pick_files|retry|contact_admin|null
details: <object optional — KHÔNG chứa credential/cookie/token/raw doc>
```

## 3. Identity & provenance trong G1

- Dùng `IdentityEvidence` của MIN-62 draft §2.1 nguyên trạng (evidence_id,
  subject_type, kind, raw_value, normalized_value, source_ref,
  observation_state, confidence, observed_at). CCCD/thửa-tờ/serial GCN =
  matching evidence, không phải Case PK.
- Trạng thái quan sát theo `SOURCE → RAW → NORMALIZED → INFERRED → CONFIRMED`
  (MIN-62 §1). OCR/AI không tự thành `confirmed`; `waiting_user` của command
  là điểm người xác nhận.
- `source_ref` tối thiểu `{page|sheet|cell|paragraph|evidence_excerpt}` — null
  hợp lệ khi producer không chứng minh được vị trí, kèm warning.
- Mọi `normalized_value` tuân `contracts/entities.md` (CCCD 12 số, serial GCN
  `[A-Z]{2}\d{6,8}`, số công chứng `xxx/yyyy`…). Chuẩn hóa không ghi đè raw.

## 4. Null / unknown / partial

Tuân MIN-62 §4 nguyên văn; nhắc lại ràng buộc cho consumer G1:

- `null` + warning = không quan sát được; chuỗi rỗng `""` **không** hợp lệ làm
  "không có dữ liệu" — renderer hiển thị "—"/"Chưa có" chứ không render "".
- `normalized_value: null` + `observation_state: observed` = chưa chuẩn hóa.
- `partial` job phải kèm breakdown `{succeeded:[], failed:[]}` ở `result.data`.

## 5. Write ownership (G1-SM)

| Dữ liệu | Ghi bởi | Shell được phép |
|---|---|---|
| Job/command registry | sidecar | đọc qua `/v1/jobs`, không ghi trực tiếp |
| Business tables (notary.db, registry.sqlite3) | sidecar/engine | **không đọc DB trực tiếp** — qua command |
| OCR calls/audit | sidecar | đọc qua result/audit endpoint |
| Evidence/IdentityEvidence | sidecar | hiển thị, không sửa |
| file nghiệp vụ (output/, runs/, word_templates/) | sidecar | chọn file qua dialog; không ghi thẳng |
| Config UI-only (theme, window bounds) | shell | tự quản, không qua contract |

## 6. Examples

### Valid — command + job

```json
// POST /v1/commands
{"contract_version":"desktopcommand.v1","command_id":"8f3d2c10-…-uuid",
 "command":"upload.prepare",
 "payload":{"files":[{"path":"D:/hs/GD-03.docx","scope":"machine_local",
   "sha256":"ab12…","media_type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}]},
 "client_meta":{"shell_version":"0.1.0","module":"upload"}}

// GET /v1/jobs/{id}
{"contract_version":"desktopcommand.v1","job_id":"j_01H…",
 "command_id":"8f3d2c10-…-uuid","status":"waiting_user","waiting_on":"finalize",
 "progress":{"done":3,"total":3,"current_label":"dry-run xong"},
 "result":{"kind":"upload_prepare","data":{"prepared":3,"failed":0},
   "evidence":[{"evidence_id":"ev_1","subject_type":"case","kind":"notary_number",
     "raw_value":"428/2026/CCGD","normalized_value":"428/2026",
     "source_ref":{"page":1},"observation_state":"inferred","confidence":0.9,
     "observed_at":"2026-09-14T10:00:00Z"}],"warnings":[]},
 "error":null,"updated_at":"2026-09-14T10:01:00Z"}
```

### Invalid — vi phạm

```json
// ✗ UNC path trong G1-SM  → expect file_scope_not_supported
{"path":"\\\\maychu\\D\\Minh\\mau.docx","scope":"lan_share"}
// ✗ credential trong payload → expect payload_rejected_sensitive_key
{"payload":{"nd_password":"…"}}
// ✗ thiếu contract_version → expect unsupported_contract_version/400
{"command":"upload.prepare"}
// ✗ normalized sai canonical (không phải 12 số) → expect evidence_invalid
{"kind":"cccd","raw_value":"0123","normalized_value":"0123",
 "observation_state":"normalized"}
// ✗ "" thay cho null  → expect validation_error
{"normalized_value":""}
```

## 7. Migration/compatibility policy (G1)

1. Thêm field optional = backward-compatible (consumer bỏ qua được).
2. Đổi nghĩa/kiểu field, đổi tên command, đổi status enum → tăng `v2`.
3. Field deprecated giữ ≥1 chu kỳ review + migration note.
4. Sidecar có thể hỗ trợ nhiều version qua `supported_versions`; shell chọn
   version cao nhất giao nhau.
5. POC `v0.experimental` **không** tương thích ngầm — consumer phải nâng
   explicit sang `v1` (đổi status `completed`→`succeeded`, thêm progress/
   waiting_on/file_ref).

## 8. Conformance checklist (MIN-62 nghiệm thu)

- [ ] Mọi request/response có `contract_version`; mismatch bị từ chối.
- [ ] FileRef chặn UNC/lan_share trong G1-SM; path tuyệt đối qua dialog.
- [ ] Payload reject đệ quy key nhạy cảm (credential/cookie/token/…).
- [ ] IdentityEvidence đủ trường; raw không bị normalized ghi đè;
      unconfirmed không thành business truth.
- [ ] null/unknown/partial/warning/error theo §4 + ErrorObject §2.3.
- [ ] Job statuses khớp MIN-64 §2.2; `waiting_on` chỉ {login,review,
      finalize,confirm}.
- [ ] Examples §6 parse/validate được bằng script (P3 dựng validator).
- [ ] Write ownership §5 không bị phá — shell không đọc/ghi DB trực tiếp.
- [ ] Owner duyệt → MIN-72 mới publish vào `contracts/` (P3).
