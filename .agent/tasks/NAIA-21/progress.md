# NAIA-21 — Kiểm chứng và bàn giao

**Tiếp nhận 04/10/2026:** đang triển khai/kiểm phần tích hợp.

Chưa nghiệm thu consumer. Root sẽ đối chiếu source/tests, review và Electron cô lập; không thay trạng thái task ngoài repo.

Quyết định Owner ở [NAIA-9](../NAIA-9/decisions.md); sản phẩm ở
[spec địa chỉ](../../../docs/spec/notary_v2/administrative-address.md)
và [spec timeline](../../../docs/spec/notary_v2/administrative-timeline.md).
Record này giữ thực thi cục bộ, không là spec/SOT task mới, không đóng issue.

## 04/10/2026 — Bổ sung: test qua script cha

- Chạy `stage_package_assets.ps1` → `build_sidecar.ps1` →
  `electron-builder --dir` end-to-end; phát hiện và vá lỗi copy dir lồng
  (`services/services`); staged tree sau vá sạch, không file cấm.
- Smoke app packaged: `notary.address_lookup` succeeded qua sidecar exe.
