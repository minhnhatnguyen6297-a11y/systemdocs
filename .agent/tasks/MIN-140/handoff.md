# Handoff — MIN-140

## Tóm tắt một câu

Stage v2 (Soạn hồ sơ) đã gỡ rule ẩn: serial tự do/null lưu nguyên văn,
không surrogate; Người/Tài sản chỉ chặn đúng các trường owner đã duyệt;
không chặn chuyển tab.

## Đọc trước khi sửa tiếp

- `brief.md` + `decisions.md` trong thư mục này — toàn bộ quyết định owner.
- Contract: `contracts/notary-case-drafting.md` §13.16 (MIN-140).
- Validator payload/result tách ở `validate_examples.py`
  (`strict_v2`/`in_payload`).

## Điểm dễ quên khi sửa lại

1. `_serial_match_key` CHỈ để so khớp (dedupe payload + tìm property cũ).
   Tuyệt đối không dùng để validate/ghi đè giá trị lưu — `prop.so_serial`
   giữ verbatim.
2. `land_rows=None` hoặc `[]` → `required`; dòng thiếu `loai_dat`/
   `dien_tich` → `required`; `dien_tich` không số → `invalid_type`.
   Field trên `field_errors` luôn là `"land_rows"` (không tách index).
3. Serial `""`/`"   "` vẫn bị chặn: convention nullable — gửi `null`.
   Đây không phải "rule ẩn" mà là kiểu contract.
4. Result side (`job.*`, `workspace_get`) vẫn emit serial null/verbatim —
   hồ sơ cũ không bị ép. Person result rows cũng vậy.
5. `is_primary` vẫn bị `_check_extra_keys` chặn trên wire v2 — đó là
   contract MIN-125, không thuộc phần gỡ.
6. Test helpers sinh `so_giay_to` unique bằng `uuid.uuid4().hex[:10]` —
   cần vì dedupe sgt trong payload.
7. Mock không có store property → không check "serial đã thuộc tài sản
   khác" (chỉ backend kiểm); dedupe trong payload vẫn parity.

## Verify nhanh

```bash
cd notary_v2 && python -m pytest tests/test_case_workspace.py tests/test_inheritance_workspace.py -q
cd shell/test && python -m pytest test_notary_mock_adapter.py test_notary_adapter_contract.py -q
cd contracts/notary-case-drafting && python validate_examples.py
cd shell && node --test test/notary-case-drafting-*.test.mjs
git diff --check
```

## Câu hỏi mở (nếu owner hỏi lại)

- `evaluate_draft` (preview render model) cũng chạy `_validate_stage` —
  nháp thiếu trường bắt buộc sẽ không evaluate được trước khi lưu. Đây là
  hành vi hiện hữu (validator dùng chung), giữ nguyên theo "validate khi
  commit/update"; nếu owner muốn preview lỏng hơn thì cần flag riêng.
- Migration chỉ cover schema `properties` biến thể đã biết (các cột lấy
  từ PRAGMA động — an toàn với DB thiếu cột mới; nếu DB cũ có cột thừa
  ngoài model thì INSERT sẽ lệch số cột → cần whitelist cột). Chưa gặp
  trên thực tế nhưng nên biết.
