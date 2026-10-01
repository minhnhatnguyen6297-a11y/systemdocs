# MIN-140 — FIX — Soạn hồ sơ: gỡ rule ẩn chặn Cập nhật Stage

Linear: https://linear.app/minhnotary/issue/MIN-140/fix-soan-ho-so-go-rule-an-chan-cap-nhat-stage-serial-bat-buoc-primary
Branch: `minhnhatnguyen6297/min-140-fix-soan-ho-so-go-rule-an-chan-stage-serial-bat`

## Nguồn (lời owner, 29/09/2026)

> "tab Soạn hồ sơ có rule ẩn chặn Stage Tài sản/Người, vd số serial phải dạng
> `XX123456` dù owner không đặt rule này. Nguyên tắc owner: gần như không chặn
> gì, mọi thao tác do user chịu trách nhiệm; chỉ chặn (1) draft Stage chưa lưu,
> (2) đang thao tác mà chuyển tab."

## Đã chốt với owner trong phiên

- **Người**: mọi trường có ô nhập đều bắt buộc — `ho_ten`, `gioi_tinh`,
  `ngay_sinh`, `so_giay_to`, `ngay_cap`, `dia_chi`. Ngoại lệ `ngay_chet`:
  trống = còn sống. Không ép format `so_giay_to`.
- **Tài sản**: bắt buộc `so_to_ban_do` + `so_thua_dat` + `dia_chi` + ≥1
  `land_rows` mỗi dòng có `loai_dat` + `dien_tich` (số). Mọi trường khác —
  kể cả `so_serial` — để trống được.
- **Serial**: không còn canonical `^[A-Z]{2}\d{6,8}$`; lưu `null` khi trống,
  lưu nguyên văn (trim 2 đầu ở boundary `_nn`) khi có; KHÔNG surrogate
  `XX%06d`; so khớp/merge property cũ qua match key = bỏ non-alphanumeric +
  uppercase (`'XX 123456' ≡ 'xx123456'`).
- **Chuyển tab**: KHÔNG chặn — draft nằm trong client model, không mất gì.
  (Owner liệt kê "đang thao tác mà chuyển tab" trong 2 case chặn ban đầu,
  nhưng chốt lại là không cần chặn vì buffer giữ nguyên.)
- `is_primary` vẫn cấm trên wire v2 — primary = `stage.assets[0]`
  (giữ nguyên từ MIN-125, không phải rule ẩn mới).

## Phạm vi sửa

- `notary_v2/services/case_workspace.py` — `_validate_stage`, `_asset_wire`,
  `_upsert_assets`, `_find_property_by_serial`, `_serial_match_key`.
- `notary_v2/models.py` — `Property.so_serial` → nullable.
- `notary_v2/database.py` + `main.py` — migration rebuild bảng
  `properties` cho DB SQLite cũ có `so_serial NOT NULL`.
- `shell/sidecar/notary_mock_adapter.py` — parity cùng rule.
- `shell/src/renderer/notary/case-drafting-view.js` — hiện lỗi
  `land_rows` ngay ô chip "Loại đất".
- `contracts/notary-case-drafting.md` §13.3/§13.16 + changelog;
  `draft-v2.schema.json`; `validate_examples.py`; `entities.md` §2;
  `docs/spec/notary_v2/stage.md`.
- Tests: `notary_v2/tests/test_case_workspace.py`,
  `test_inheritance_workspace.py`, `shell/test/test_notary_mock_adapter.py`,
  `test_notary_adapter_contract.py`, fixture `ready.json`, 4 example
  `command.*.valid.json` trong `contracts/.../examples/draft-v2/`.
