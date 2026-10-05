# Tra cứu địa chỉ trong hồ sơ — NAIA-9, TASK-2

**Trạng thái:** Owner duyệt 05/10/2026, runtime chưa đáp ứng · **Nguồn quyết định:** Owner
03–04/10/2026 tại [NAIA-9](../../../.agent/tasks/NAIA-9/decisions.md); thay một
phần bởi Owner 05/10/2026 tại TASK-2.

Luật tra (đầu vào, khớp, kết quả, đúng/sai) nằm tại
[lõi tra cứu dùng chung](../shared/administrative-lookup.md). Trang này chỉ ghi
**cách `notary_v2` gọi lõi**; không lặp lại luật.

## Công dụng và Tại sao?

Giúp chuyên viên đổi địa chỉ trên giấy tờ cũ sang tên xã/tỉnh hiện hành khi lập
hồ sơ. Máy chỉ trả kết quả để copy; người dùng tự quyết ghi gì vào ô.

## Nơi gọi

| Ô | Chuỗi được tra |
|---|---|
| Địa chỉ Người | Nội dung ô địa chỉ của người đó |
| Địa chỉ Tài sản | Nội dung ô địa chỉ của tài sản đó |
| Nơi niêm yết | Nội dung chính ô Nơi niêm yết; không bắt chọn tài sản nguồn |
| Nơi cấp giấy khai tử | Địa chỉ của chính người đã chết; kết quả là xã mới để người dùng ghi nơi cấp |

Mọi ô dùng kiểu trình bày `drafting` (`xã Ý Yên, tỉnh Ninh Bình`), nút Tra cạnh
ô, kết quả copy được. Quá 10 kết quả → popup "Nhiều kết quả khớp. Xem đầy
đủ?", bấm đồng ý mới mở tool tra cứu dạng popup đè lên hồ sơ; đóng popup về
đúng chỗ cũ, không mất nháp đang nhập. Không cần ngày cấp giấy hay
`ngay_lap_ho_so`. *Tại sao:* lõi chỉ trả bước cuối (Owner 05/10).

## Quy tắc riêng của hồ sơ

- Máy không ghi, đè hay nối `(nay là …)` vào ô hoặc Stage. Người dùng dán/sửa
  tay rồi lưu như mọi chỉnh sửa khác; lưu metadata dùng revision hiện hành,
  xung đột không ghi đè cưỡng bức.
- Không tự sửa thôn, số nhà hoặc chi tiết ranh giới.
- Nơi cấp giấy khai tử: tra xã mới từ địa chỉ của người đó, không phụ thuộc
  ngày (Owner 05/10/2026). Máy vẫn không tự ghi; người dùng copy và sửa nếu
  giấy ghi khác. Quy tắc nơi cấp giấy tờ người sống theo MIN-141 vẫn độc lập.
- Không gửi địa chỉ khách hàng ra website; chỉ đọc kho cục bộ.

## Bản cài

Bản cài cần helper, schema và đúng ledger/snapshots công khai. Không đóng gói
database văn phòng, cấu hình riêng, khóa ghi hoặc archive lịch sử của người
quản lý. Nâng cấp định dạng kho theo migration của
[spec timeline](./administrative-timeline.md).

## Còn mở

- Vị trí nút Tra trong từng card.

## Lịch sử

Owner 05/10/2026 bỏ: bắt ngày giấy/ngày lập hồ sơ, bắt xã+tỉnh, nút áp dụng nối
`(nay là …)`, nơi niêm yết lấy địa chỉ tài sản được chọn, nơi cấp giấy khai tử
tra theo ngày cấp giấy và "địa chỉ cư trú không chứng minh nơi cấp". Hiện trạng code còn
theo các quy tắc cũ; xem mục 12 của
[lõi tra cứu](../shared/administrative-lookup.md).
