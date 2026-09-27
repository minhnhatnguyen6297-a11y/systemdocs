# MIN-124 — Quyết định

## Đã chốt trong pha này (ranh giới tài liệu, không phải nghiệp vụ)

| # | Quyết định | Lý do / căn cứ |
|---|---|---|
| D1 | SOT thị giác chung đặt tại `docs/product/ui/DESIGN.md` + `tokens.json`; SOT thao tác chung tại `docs/product/ui/EXPERIENCE.md` | Theo plan MIN-123; giữ một nguồn cho cả hai module thay vì rải trong spec riêng |
| D2 | Ảnh approved lưu lâu dài ở `docs/product/ui/references/` kèm `README.md` ghi nguồn/phiên bản/ngày duyệt | Task file `.agent/` là record thực thi; tài nguyên thiết kế phải nằm trong `docs/` để P2–P9 dẫn ổn định |
| D3 | `upload_lab/docs/visual-design.md` chỉ là lớp thị giác — trỏ hành vi về `spec_UI.md`, không lặp quy tắc hai tab/bảng/scope | `upload_lab/README.md` §4 cấm tạo spec UI song song |
| D4 | `drafting-tab.md` giữ nguyên vai trò SOT hành vi/dữ liệu; chỉ thêm khối đánh dấu hiện trạng/đích/chờ duyệt và sửa marker "contract chưa tồn tại" (đã có `contracts/notary-case-drafting.md`) | File là SOT đã duyệt MIN-104; P1 không được viết lại ngữ nghĩa |
| D5 | Giá trị token trong `tokens.json` ghi `status: proposed` — số đo/tông màu cụ thể chờ owner duyệt trên prototype P3; P1 chỉ chốt tên token + ngữ nghĩa dùng | Plan MIN-123 yêu cầu "màu sắc, cỡ chữ, khoảng cách đề xuất"; không tự chốt số đo trong pha tài liệu |
| D6 | Spec UX 24/09 (`2026-09-24-notary-v2-case-drafting-electron-ux.md` §3 bảng token) đánh dấu superseded bởi `docs/product/ui/`; spec 14/09 (`module-transition-ux-spec`) giữ vai trò vocabulary trạng thái shell, EXPERIENCE.md dẫn lại thay vì nhân bản | Tránh hai bản quy định tương đương; spec cũ vẫn được dẫn đúng phần còn hiệu lực |
| D7 | Không chốt bất kỳ nghiệp vụ mở nào (vị trí 16, thả lên vị trí đã có người, giới hạn 3 tài sản trên ảnh, hai bên 30 vị trí, Apply loại đất, vòng đời Stage) — liệt kê trong danh sách chờ owner | Theo brief P1: không quyết định hành vi chưa chốt |

## Đang chờ owner (xem EXPERIENCE.md §10 + visual-design của từng module)

- Giá trị token cuối (tông xanh chính xác, cỡ chữ, chiều cao input 36–40,
  bo góc, shadow) — duyệt qua prototype P3.
- Chrome điều hướng shell: ảnh approved vẽ icon-rail sáng; sidebar hiện
  tại là rail tối có nhãn — cần chốt hình thức cuối.
- Ngữ nghĩa nút số `1/2/3` trên thẻ sơ đồ (Chủ đất/Nhận đất theo tài sản)
  và mô hình hai bên 30 vị trí — thuộc P2/P7.
- Nút `Hủy thay đổi` trên action bar ảnh approved — hiện chưa có API revert;
  ngữ nghĩa discard thuộc P2.
- `Mở rộng` trong cụm zoom sơ đồ — chưa rõ là toàn màn hình hay modal.
- Ngưỡng bố cục hẹp cho bảng tài sản chuyển vị + bảng Upload 6 cột.
