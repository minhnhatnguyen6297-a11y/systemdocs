# NAIA-15 — Ngày giấy tờ/ngày hồ sơ và điểm nối

**Tiếp nhận 04/10/2026:** đang triển khai/kiểm phần tích hợp.

Owner đã chốt ngày nơi niêm yết là ngay_lap_ho_so; giấy nguồn chỉ giúp đọc dạng địa chỉ. Nơi cấp giấy khai tử dùng bằng chứng/ngày cấp của chính giấy ấy, độc lập nơi cư trú.

Quyết định Owner ở [NAIA-9](../NAIA-9/decisions.md); sản phẩm ở
[spec địa chỉ](../../../docs/spec/notary_v2/administrative-address.md)
và [spec timeline](../../../docs/spec/notary_v2/administrative-timeline.md).
Record này giữ thực thi cục bộ, không là spec/SOT task mới, không đóng issue.

## 04/10/2026 — Bổ sung (Multica)

- Hai câu hỏi nghiệp vụ đã được Owner chốt 03/10 (ghi trong
  [NAIA-9/decisions.md](../NAIA-9/decisions.md)): ngày đích niêm yết =
  `ngay_lap_ho_so`; nơi cấp giấy khai tử tách riêng, không lấy địa chỉ cư
  trú suy ra.
- Consumer đã cài đúng quyết định trong commit `a83f993`: posting suggestion
  dùng ngày hồ sơ + ngày cấp giấy của tài sản được chọn; issuer gate kiểm
  UBND riêng. Đã commit `53c7804` vá staging đóng gói.

## 05/10/2026 — Trạng thái khi gom nhánh

Phần bổ sung 04/10 ở trên ghi nhận runtime cũ. Owner đã thay yêu cầu phụ thuộc ngày/tự gợi ý bằng tra độc lập và chỉ tra khi bấm nút; xem [spec hiện dùng](../../../docs/spec/shared/administrative-lookup.md) và TASK-3/TASK-4. Không triển khai lại gate ngày từ log này.
