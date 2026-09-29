# Input từ Zalo

**Trạng thái:** Producer đã có repo riêng; contract trao đổi MIN-92 vẫn
**Draft — chờ owner duyệt**, nên chưa cho phép code tích hợp production.

## 1. Công dụng và ranh giới

Module Zalo thu sự kiện, giữ ảnh tạm và gọi Qwen ở nơi có ảnh. Máy công chứng
nhận chữ OCR raw, trạng thái, thời gian và nguồn; không nhận ảnh, thumbnail,
base64, đường dẫn hoặc link tải ảnh.

Document Intake trên máy chính sở hữu regex, phân loại, bóc trường, ghép mặt
giấy tờ/người/tài sản và nhóm hồ sơ. Bot không xuất dữ liệu nghiệp vụ đã xử lý.

## 2. Flow

```text
Zalo văn phòng
→ collector ghi journal và captured_at
→ tải/chuẩn bị ảnh tạm
→ Qwen OCR
→ công bố gói raw có hash/version
→ máy chính Sync, kiểm và lưu raw
→ ACK kỹ thuật
→ Document Intake phân tích
→ người dùng đối chiếu Zalo thật và xác nhận
→ Stage draft
```

ACK chỉ nghĩa máy chính đã lưu raw; không nghĩa parser xong hoặc người dùng đã
duyệt. Nút Sync không quét lịch sử Zalo.

## 3. Dữ liệu và thời hạn

- `captured_at` là giờ bot bắt tin và là mốc chính để nhóm.
- `source_sent_at`, `imported_at` là mốc phụ.
- Ảnh gốc và ảnh dẫn xuất xóa sau 168 giờ từ `captured_at`, dù chưa ACK.
- Gói raw chưa ACK phải giữ để gửi lại.
- Máy chính giữ raw/revision đã nhập theo chính sách dữ liệu hồ sơ.
- OCR lại dùng ID nguồn và loại biến thể; không gửi bytes ảnh về máy chính.

## 4. Quyền riêng tư

- Chỉ tài khoản chung của văn phòng.
- Chỉ nhóm đã bật và tin riêng gửi tới chính tài khoản văn phòng.
- Không đọc tài khoản hoặc tin riêng của nhân viên.
- Không log nội dung tin, OCR, ảnh, cookie hoặc secret.

## 5. Lỗi

- Collector chết sau journal: job tiếp tục sau restart.
- Chết trước journal: chưa có bằng chứng lấy bù; phải báo giới hạn.
- Hash/version sai: không nhập như gói hợp lệ.
- Máy chính tắt: bot vẫn nhận/OCR; raw chờ ACK.
- Ảnh hết hạn/mất file/Qwen lỗi/hết quota: trả trạng thái cụ thể, không tạo chữ
  giả và không thay dữ liệu đã duyệt.
- Retry cùng ID phải idempotent; cùng ID khác nội dung là xung đột.

## 6. Kiến trúc và contract

- Repo nguồn: `D:\zalo-intake`; snapshot: `zalo/`.
- Producer SOT: `zalo/docs/spec-producer.md`.
- Contract Draft: `contracts/zalo-intake/`; schema/fixture hiện có chỉ dùng để
  review và kiểm thử bản nháp.
- Consumer hiện hành: `notary_v2/docs/platform/zalo-document-inbox/`.

## 7. Câu hỏi mở

- Cơ chế lấy bù sự kiện bot chưa từng nhận.
- Quota/enum OCR lại và chính sách raw sau ACK theo version contract tương ứng.
- Cách người dùng tìm lại tin khi chỉ có metadata và ảnh không còn trong Zalo.

## 8. Lịch sử

Thiết kế cũ đặt listener, ảnh và Inbox trong `notary_v2`. Owner chốt 24/09/2026:
tách producer ra repo local trước, server sau; máy chính chỉ nhận raw và giữ
parser nghiệp vụ. MIN-103 đã tạo repo nguồn và snapshot một chiều.
