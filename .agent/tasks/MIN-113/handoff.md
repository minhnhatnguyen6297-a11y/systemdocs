# MIN-113 handoff

## Đã xong
- Toàn bộ verification tự động + scripted E2E mock+real + fault injection +
  packaged smoke thật — evidence ở `progress.md`.
- Fixture nghiệm thu `shell/test/fixtures/notary-case-drafting/full-flow.json`
  (case 47: 6 người/2 tài sản/diagram/3 Word với 1 blocked cố ý).
- Branch `minhnhatnguyen6297/min-113-...` sẵn merge (chỉ fixture + task records).

## Chờ owner — checklist review UI thật (packaged `dist-app\win-unpacked\g1-shell.exe`)
1. Mở app → nav chính 3 module + tiện ích; vào notary_v2 → `Soạn hồ sơ`.
2. Mở case 47 (mock: `G1_DEV_NOTARY_MOCK=1 npm start` ở shell dev; packaged: case real).
3. 1440×1024 + 1280×820: Stage 36/64 trên, Pool/Diagram 22/78 dưới.
4. Intake: chọn file qua dialog / paste text → review cards → `Đưa vào Stage` (draft).
5. Sửa inline + drawer → `Cập nhật` (commit + revision).
6. Pool kéo/menu `Gán vị trí` → sơ đồ → `Đánh giá thử` → `Lưu sơ đồ`.
7. `Xuất Word` → chọn 3 văn bản → chọn folder → theo dõi job → 2 Đã lưu + Mở file,
   1 Lỗi có lý do (niem_yet thiếu template).
8. Rời tab/đóng app khi đang draft → confirm.
9. Không thấy Zalo, JSON kỹ thuật, ô nhập ID.

## Cutover (SAU khi owner duyệt)
- Đổi default entry/renderer sang tab Soạn hồ sơ mới.
- Web cũ giữ 1 chu kỳ release rollback.
- `zalo.status` handler trong `command_registry.py:205` dọn khi MIN-103 hoàn tất.

## Lưu ý vận hành
- Packaged build: `npm run build:sidecar` rồi `npm run dist` → `dist-app/win-unpacked/`.
- Mock dev: `G1_DEV_NOTARY_MOCK=1` (packaged luôn strip).
- OCR ảnh/PDF-scan thật cần `QWEN_API_KEY`; thiếu → `ocr.engine_unavailable` per-source.
