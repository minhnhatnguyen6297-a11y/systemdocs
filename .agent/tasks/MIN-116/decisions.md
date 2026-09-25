# Decisions — MIN-116

Chỉ ghi quyết định **trong phạm vi task** đã được chốt (bởi user/owner hoặc
theo spec đã duyệt). Quyết định xuyên sản phẩm hoặc câu hỏi mở: **không** tự
chốt ở đây — đưa lên `docs/architecture/OPEN_DECISIONS.md`.

## 2026-09-25 — Root cause: `tempfile.TMP_MAX = 2**31-1` trên nt

- **Phát hiện:** `_mkstemp_inner` retry `PermissionError` khi
  `os.path.isdir(dir) and os.access(dir, W_OK)` — `os.access` trên Windows
  chỉ đọc read-only attribute, không eval ACL → misreport writable khi ACL
  deny-write. TMP_MAX trên nt = `sys.maxsize` (~2.1 tỷ, đo được >1.18M
  denied calls vẫn chưa dừng) → hang thực sự vô hạn, không phải 10.000
  lần rồi thoát.
- **Nguồn:** repro tay trên venv Python 3.12.10 (xem progress.md).

## 2026-09-25 — Chọn D2-phương-án 1+2: probe + bỏ mkstemp (không đổi same-volume)

- **Chọn:** probe writability một lần đầu batch bằng `open('xb')` tạo/xóa
  file thật trong dest; thay `tempfile.mkstemp` bằng `_temp_file_in`
  (uuid name + `open('xb')`, chỉ retry FileExistsError ×8); PermissionError
  ở bất kỳ đâu (probe/render/publish TOCTOU) → per-doc `file_locked`.
- **Lý do:** giữ nguyên giả định temp-in-dest same-volume (publish chỉ là
  copy nội bộ, không đổi atomicity semantics §8.3); `open('xb')` đã là
  pattern sẵn có của `_publish` — một cơ chế exclusive-create duy nhất,
  PermissionError raise ngay lần đầu, không retry loop.
- **Loại bỏ:** render temp ra `%TEMP%` rồi copy publish (D2-3 của
  MIN-113) — phá giả định same-volume, đổi failure mode của publish;
  giữ `mkstemp` + chỉ probe — vẫn còn retry loop ở TOCTOU path.
- **Nguồn:** MIN-113 decisions.md D2 (đề xuất), brief MIN-116.

## 2026-09-25 — Error code mapping: `file_locked` per-doc cho deny-write

- **Chọn:** probe PermissionError → `dest_error = ("file_locked", ...)`
  áp cho MỌI doc đồng nhất (kể cả doc sẽ fail `word.template_missing`) →
  all-failed → job `failed{word_batch_failed}` kèm result_data như §8.4.
  FileNotFoundError (dest mất giữa chừng) → `file_not_found`; OSError khác
  → `word.render_failed`.
- **Lý do:** §8.4 registry per-file data-code đã có sẵn `file_locked` /
  `file_not_found` (envelope reuse) — không tạo code mới, không sửa
  contract. Uniform `file_locked` đúng nghĩa: không doc nào có thể ghi
  được, lỗi destination không phải lỗi từng văn bản.
- **Loại bỏ:** job-level `file_locked` không kèm breakdown — mất
  result.data §8.4 trên wire, lệch shape cancel/failed đã chuẩn hóa
  MIN-115; per-doc theo block_reason từng doc — sai nghĩa (doc có template
  vẫn không ghi được).
- **Nguồn:** contract `notary-case-drafting.md` §8.4 + §9.

## 2026-09-25 — Vá mock adapter cho parity thật

- **Chọn:** `notary_mock_adapter.word_export_batch` thêm probe
  `.word_export_probe_<uuid>.tmp` một lần đầu batch (sau check_cancel đầu)
  + `dest_error` → per-doc error đồng nhất; thêm catch PermissionError
  quanh `_reserve_and_write` → `file_locked`.
- **Lý do:** divergence thật — trước vá, deny-write làm `_reserve_and_write`
  raise PermissionError trần → job chết không theo contract (không
  `word_batch_failed`, không breakdown), còn engine thật trả per-doc
  `file_locked`. Mock là oracle wire-shape cho UI dev nên phải khớp.
- **Nguồn:** brief MIN-116 §5 (chỉ sửa nếu divergence thật).
