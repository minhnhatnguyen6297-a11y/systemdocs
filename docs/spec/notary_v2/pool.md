# Pool — Người chưa được gán lên Diagram

**Trạng thái:** Active · **Không phải nguồn dữ liệu riêng**

## 1. Công dụng

Pool cho người dùng biết người nào trong Stage committed chưa được đặt vào
Diagram. Pool hỗ trợ kéo-thả; nó không sở hữu dữ liệu Người.

```text
Pool = Stage.people committed − personId đang gán trên Diagram committed
```

## 2. Thao tác và trạng thái

- Sau commit Stage thành công, Pool được tính lại.
- Kéo thẻ từ Pool vào slot Diagram tạo gán trong Diagram draft.
- Gỡ node khỏi Diagram đưa người đó trở lại Pool draft tương ứng.
- `Lưu sơ đồ` commit Diagram; `Hủy` khôi phục Pool/Diagram từ bản committed.
- Hồ sơ mới chưa commit Stage có Pool rỗng.

## 3. Input và output

Input: `stage.people` committed và `diagram.state`. Output: danh sách thẻ Người
chưa được gán. Pool không có table, JSON column hoặc endpoint save riêng.

## 4. Quy tắc

- Không đọc Stage draft để tránh hiển thị người chưa commit.
- Không sửa tên, CCCD hoặc field Người từ Pool.
- Một `personId` chỉ xuất hiện một lần trên Diagram, trừ khi contract domain
  sau này cho phép rõ ràng.
- Thứ tự Pool chỉ là trình bày, không mang nghĩa pháp lý.

## 5. Lỗi và ngoại lệ

- `personId` ngoài Stage committed: reject `diagram_reference_outside_stage`.
- Stage commit prune người đã xóa; Pool tính lại từ snapshot server trả về.
- Không dùng flag `inPool`, `isHidden` hoặc bản sao local làm SOT.

## 6. Kiến trúc và lịch sử

Pool từng được điều khiển bằng nhiều flag UI, gây mất thẻ sau save/reload. Mô
hình hiện tại dùng projection từ Stage và Diagram để không có hai nguồn sự thật.

## 7. Nguồn

- `notary_v2/docs/platform/case-workspace/contract.md`.
- `notary_v2/docs/domains/inheritance/workflow.md`.
