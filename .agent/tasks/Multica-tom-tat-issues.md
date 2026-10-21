# Tóm tắt các issue Multica

Dựa trên bản xuất **24 issue, 227 comment**, chụp lúc **22:25 ngày 03/10/2026 (giờ Việt Nam)**. Đây là tóm tắt của bản xuất, không phải lần cập nhật trạng thái mới.

## Tổng quan

| Trạng thái | Số lượng | Issue |
|---|---:|---|
| Hoàn tất | 8 | NAIA-1, 2, 3, 5, 7, 10, 13, 23 |
| Chờ nghiệm thu | 1 | NAIA-6 |
| Đang triển khai / điều phối | 4 | NAIA-8, 9, 12, 14 |
| Bị chặn | 4 | NAIA-4, 15, 22, 24 |
| Chờ đầu vào | 6 | NAIA-16–21 |
| Đã hủy do gộp scope | 1 | NAIA-11 → NAIA-8 |

## Ba luồng công việc

| Luồng | Tiến độ | Bước tiếp theo |
|---|---|---|
| **Xuất Word — NAIA-8 + 12** | UI/engine/migration đã có nhiều bản sửa và test; **chưa nghiệm thu chung**. Review gần nhất còn lỗi xử lý token/alias và kiểm nội dung số. | Worker sửa phần còn thiếu ở NAIA-12; Leader review, rồi kiểm UI, Word COM và định dạng trên cùng bản tích hợp. |
| **Xã/phường — NAIA-9, 14–21** | Đã chia stage. NAIA-14 nghiên cứu chưa bàn giao đầy đủ, run gần nhất thất bại vì hạn mức. NAIA-15 đã khảo sát code nhưng chờ chốt nghiệp vụ ngày. | Chốt hai câu hỏi bên dưới, hoàn tất nguồn dữ liệu và khảo sát trước khi mở NAIA-16. |
| **Import Word → JSON → Soạn hồ sơ → Word — NAIA-4** | Spec đã có; được phép triển khai, nhưng thiếu `uv` trong môi trường agent. Tái sử dụng regex core NAIA-3. | Sửa NAIA-24 trước; triển khai NAIA-4, dùng nền dữ liệu NAIA-6 và bản Word tích hợp NAIA-8/12 khi kiểm toàn luồng. |

**NAIA-6:** code đã được Leader nghiệm thu; đang chờ Owner nghiệm thu. Việc tạo PR không là điều kiện của chế độ Local-Only.

## Thứ tự và khả năng song song

- **NAIA-8 ∥ NAIA-12 → nghiệm thu xuất Word chung.** Nhập Nơi niêm yết thủ công nên không chờ luồng xã/phường.
- **NAIA-14 ∥ NAIA-15 → NAIA-16 → NAIA-17 → NAIA-18 ∥ NAIA-19 ∥ NAIA-20 → NAIA-21.** Stage sau chỉ mở khi đầu vào đạt; việc ghi song song cần tách worktree/phạm vi file.
- **NAIA-24 → NAIA-4.** Đã có điều kiện tự đánh thức NAIA-4 khi NAIA-24 hoàn tất.

## Các điểm cần tháo gỡ

1. **NAIA-15 — Owner chốt nghiệp vụ:** ngày tham chiếu cho Niêm yết là ngày cấp giấy tờ nào hay ngày lập hồ sơ? Có tách nơi cấp khai tử khỏi Nơi niêm yết trong Word không? Các phương án trong comment hiện là đề xuất, chưa phải quyết định đã duyệt.
2. **NAIA-24 — Môi trường máy:** cài/cấu hình `uv` ổn định và kiểm chứng trong lượt agent mới; bản portable trong task khác chưa đạt yêu cầu.
3. **NAIA-22 — Sandbox:** lỗi Windows `1326/1909` chưa được xác định nguyên nhân tận gốc; cần kiểm nhật ký máy chủ. Phân biệt với lỗi hạn mức provider.
4. **NAIA-8/12 — Nghiệm thu:** test đạt không đồng nghĩa luồng UI/Word COM/định dạng thực tế đã đạt; vẫn cần bằng chứng ở đúng bản tích hợp.

**NAIA-23 đã hoàn tất:** Codex CLI và runtime Multica cùng nhận bản `0.160.0` tại thời điểm xác minh.

Mọi coding, commit và kiểm định tiếp tục cục bộ; push/PR/merge cần chỉ thị rõ của Owner. Nội dung chi tiết và bằng chứng giữ trong bản xuất đầy đủ `Multica-toan-bo-issues.md`.
