---
id: decision-owner-entity-anchors-case-snapshots-20261021
title: "Owner chốt: điểm neo Người/Tài sản, lấy mới nhất vào Hồ sơ mới"
date: '2026-10-21'
status: accepted
---

## Quyết định đang áp dụng

Người dùng chủ yếu làm Hồ sơ và tìm lại các Hồ sơ đã làm. Hệ thống phải có
quy tắc gom ID mặc định, không đòi người dùng quản lý nhóm hay chọn phiên bản.

1. **Người:** tự dùng cùng ID khi **đồng thời tên và số giấy tờ giống nhau**.
   Ngày cấp, địa chỉ và các trường khác có thể khác mà vẫn cùng ID.
   Chỉ cùng tên hoặc chỉ cùng số không đủ. Đổi tên hoặc đổi số giấy tờ thì
   chấp nhận thành ID khác. Không tự thêm loại giấy, ngày sinh, ngày cấp hay
   địa chỉ vào điều kiện gom ID.
2. **Tài sản:** số **serial** là điểm neo để gom các bộ thông tin vào cùng ID.
   Serial tiếp tục giữ nguyên văn, không ép mẫu hoặc thay bằng mã giả.
3. **Lấy lại dữ liệu:** khi tạo Hồ sơ mới, tìm Người/Tài sản đã làm trước đây
   thì mặc định lấy bộ thông tin mới nhất của ID đó; không có bước chọn phiên bản.
4. **Hồ sơ đã lưu:** giữ snapshot riêng. Thông tin mới ở Hồ sơ khác hoặc
   danh mục dùng chung **không tự cập nhật ngược**. Người dùng vẫn có thể mở
   Hồ sơ và sửa thủ công theo quyền ghi hiện hành.
5. **Lịch sử:** các bộ thông tin khác nhau của cùng ID vẫn được giữ qua
   snapshot của những Hồ sơ liên quan. Mỗi Hồ sơ chỉ một snapshot hiện hành;
   sửa/lưu lại cùng Hồ sơ không tạo lịch sử từng ô hay snapshot từng lần lưu.
   Không bắt buộc thêm bảng phiên bản Người/Tài sản độc lập.
6. **Tra cứu:** tìm Người nhằm xem Người đó đã làm những Hồ sơ gì. Không trải
   phẳng mọi thay đổi giấy tờ/địa chỉ thành danh sách phiên bản bắt người dùng đọc.
7. Người sống và Người chết cùng một bảng Người. Logic dùng ngày chết và
   thông tin phụ có nguồn; thiếu ngày chết không tự chứng minh còn sống.
8. Liên kết địa chỉ cũ–mới do sáp nhập **tạm thời giữ nguyên cách hiện tại**,
   owner chưa chốt mô hình mới. Đề xuất danh mục/quan hệ chuyển đổi và mã
   tham chiếu từ các trường địa chỉ chưa được duyệt, không triển khai theo
   đề xuất đó. Dữ liệu nền và quy tắc đối chiếu hiện có không được coi là mô
   hình lịch sử địa chỉ đã chuẩn hóa.

## Lý do và rủi ro owner chấp nhận

Giảm thao tác cho người dùng phổ thông, giữ Hồ sơ là đơn vị công việc/lịch sử.
Owner chấp nhận khả năng hiếm hai người chết cùng tên và số giấy khai tử,
và chấp nhận một người đổi tên/số giấy tờ thành hai ID. Đây là quy ước gom
dữ liệu của sản phẩm, không khẳng định dữ liệu nhập/OCR không bao giờ sai.

Quy tắc gom ID không cho phép tự bổ sung dữ kiện giữa các văn bản, sửa nguồn,
gộp hai Hồ sơ thành một hoặc nâng dữ kiện chưa xác nhận thành đã xác nhận.

## Thay thế và giữ lại

- Thay policy ở `8b4e85f` và #44: CCCD chỉ gợi ý, user chọn mới liên kết,
  bỏ qua tạo ID mới. Luồng bắt user quản lý gợi ý/sai khác không còn là yêu
  cầu mặc định để thực hiện thiết kế này. Không tự mang kho “thông tin liên
  kết” và lifecycle gợi ý cũ vào mô hình mới; phần dữ liệu/nguồn đã có vẫn giữ.
- Thay yêu cầu chọn bộ thông tin theo Hồ sơ/phiên bản khi lấy vào Hồ sơ mới
  trong quyết định snapshot trước đó. Giữ nguyên quy tắc mỗi Hồ sơ một snapshot
  và không cập nhật ngược Hồ sơ cũ.
- Không khôi phục phương án CCCD UNIQUE/chặn luồng của `6eaf42b`.
  Quy tắc gom dùng cặp tên + số, không phải số giấy tờ duy nhất toàn cục.
- Giữ Nháp lưu database, cho lưu tiến độ thiếu trường và nhãn Nháp rõ.
  Không tự định nghĩa Hồ sơ hoàn thiện hoặc cách tính báo cáo.

## Phần thiết kế còn mở

Mục này ghi trạng thái tại 21/10. Owner đã trả lời mốc mới nhất, loại draft,
đối chiếu tên, ID trùng cũ, serial và phạm vi Nhân bản trong
[quyết định 22/10](decision-owner-data-entry-save-rules-20261022.md); hai bước
ghi và lifecycle ID khi nhập dở đang được rà soát trước code.

- “Mới nhất” được xếp theo mốc nào; Nháp thiếu trường có được làm nguồn mặc
  định hay không. Chưa chọn lấy theo lần lưu, ngày giấy tờ hoặc ngày nghiệp vụ;
  không tự ghép từng trường của nhiều Hồ sơ để tạo một bộ “đầy đủ nhất”.
- Chi tiết so sánh tên/số: khoảng trắng, chữ hoa/thường và ký tự tương đương.
  Không suy đã duyệt tìm gần đúng, bỏ dấu hoặc bỏ dấu câu trong số giấy tờ.
- Thiếu tên/số hoặc serial thì chưa đủ điểm neo để kết luận cùng ID;
  không gom theo giá trị rỗng và không biến điều đó thành chặn lưu Nháp.
  Thời điểm cấp ID cho dòng Nháp thiếu dữ liệu còn thiết kế.
- Nhiều ID cũ đã cùng điểm neo: cách chuyển liên kết còn thiết kế;
  quyết định không cấp quyền hợp nhất/xóa/chuyển dữ liệu hiện có.
- Serial chung nhiều thửa/nhóm đất: giữ đủ hàng và vai trò/thứ tự theo Hồ sơ;
  chưa chốt cấu trúc bảng/cardinality, không tự gộp mất các dòng tài sản.
- Schema, cách giữ/truy vấn bộ mới nhất, liên kết Người–Tài sản–Hồ sơ,
  #42 nhiều giấy tờ/địa chỉ và phạm vi #41 tiếp tục thiết kế.

## Hiệu lực và phạm vi phiên

Đồng bộ quy tắc trong contracts, shared data-rules, spec Notary và sổ tay.
Đây là quyết định thiết kế, chưa phải hành vi đã triển khai. Không sửa code,
schema hoặc DB production; không migration/test/đọc mẫu mới. #41 vẫn mở,
gate mẫu vẫn đóng; không lấy thiết kế lưu trữ chưa xong làm gate mới cho
mọi phần regex/placeholder đã rõ nghĩa.
