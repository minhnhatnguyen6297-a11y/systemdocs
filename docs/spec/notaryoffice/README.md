# notaryoffice — Theo dõi hồ sơ trong văn phòng

**Trạng thái:** Draft `[CONFIRM]`; chưa có runtime · **Nguồn:**
`notaryoffice/intent.md` v1.0, 10/09/2026 · **Owner duyệt:** chưa thấy bằng
chứng duyệt toàn bộ thiết kế

## 1. Mục tiêu

Trả lời nhanh: hồ sơ nào đang được xử lý, ai đang giữ, đang ở đâu, bị chặn bởi
việc gì và bước tiếp theo là gì. Hệ thống thu dấu vết công việc để dựng ứng viên;
không biến suy đoán thành hồ sơ đã xác nhận.

## 2. Flow dự kiến

```text
Dấu vết Word/in/nguồn được phép
→ Evidence Record
→ nhóm phiên làm việc
→ Draft Case và xếp hạng ứng viên
→ chuyên viên xác nhận/sửa/gộp/bỏ qua
→ Case vận hành đã xác nhận
→ tìm kiếm và timeline
```

Điểm số chỉ xếp thứ tự ứng viên, không loại Evidence và không tự ghép cứng.

## 3. Nguồn và ranh giới

- Word text diff: nhận biết thay đổi CCCD, GCN, thửa/tờ, tiền, diện tích.
- Print event: tín hiệu tiến trình; không cung cấp số copies đáng tin cậy.
- Zalo: chỉ tài khoản chung văn phòng theo ranh giới hệ thống.
- Không quay màn hình, ghi phím hoặc dùng dữ liệu để chấm công.
- Trước thử nghiệm phải thông báo nhân viên và bổ sung nội quy phù hợp.

## 4. Dữ liệu chính dự kiến

- `evidence_records`: dấu vết có nguồn.
- `draft_cases`: ứng viên chưa xác nhận.
- `cases`, `case_entities`, `work_items`: hồ sơ vận hành đã xác nhận.
- `artifacts`, `document_snapshots`, `document_deltas`, `print_jobs`.
- `calibration_logs`: phản hồi xác nhận để đo chất lượng.
- `case_timeline_events`: lịch sử bất biến.

Đây là thiết kế logic, chưa cho phép tạo schema production. Aggregate theo dõi
công việc không mặc định 1:1 với case soạn thảo của `notary_v2`.

## 5. Xác nhận và chống làm phiền

- Tối đa 3 popup/người/ngày chỉ áp dụng khi A4 xác nhận mỗi người có định danh
  Windows riêng; nếu dùng chung tài khoản, cách tính quota vẫn là câu hỏi mở.
- Bấm dưới 1,5 giây liên tục là tín hiệu cần kiểm tra, không tự kết tội.
- Popup hiển thị bằng chứng và cho `Đúng`, `Bỏ qua`, `Sửa/Gộp`.
- Trạng thái dự đoán luôn có nhãn; chỉ người dùng mới xác nhận.

**Tại sao:** nhiều popup làm người dùng bấm theo phản xạ. Dữ liệu nhìn có vẻ
đầy đủ nhưng sai, rồi hệ thống học từ sai lệch đó.

## 6. Kiến trúc dự kiến

- Agent mỏng trên máy trạm ghi dấu vết được phép và cache FIFO khi mất LAN.
- Hub trong LAN chuẩn hóa, diff, dựng ứng viên và phục vụ tìm kiếm.
- Rule tất định xử lý phần lớn; AI chỉ hỗ trợ ca mơ hồ và không giữ state riêng.
- Tìm kiếm ưu tiên tên, CCCD, GCN, thửa/tờ và chuyên viên; kết quả phân biệt
  `ĐÃ XÁC NHẬN` với `DỰ ĐOÁN`.

Các phương án đã loại:

- FileWatcher tập trung: không thấy đầy đủ hành vi trên máy trạm.
- Xử lý toàn bộ trên máy con: khó quản trị phiên bản và hợp nhất dữ liệu.
- Tự ghép bằng điểm: rủi ro mất hoặc gán sai hồ sơ; điểm chỉ được xếp hạng.

## 7. Câu hỏi phải đo

| Mã | Câu hỏi | Trạng thái |
|---|---|---|
| A1 | IFilter đọc ổn định khi Word đang mở? | Cần đo máy thật |
| A2 | Print Spooler báo chính xác số bản in? | Đã chốt: không |
| A3 | Ổ mạng chung báo sự kiện đầy đủ? | Cần đo máy thật |
| A4 | Sáu máy dùng tài khoản Windows riêng? | Cần khảo sát |

A2 cấm dùng số copies làm điều kiện phân loại. Nếu A4 dùng chung tài khoản,
phải bỏ tính năng theo dõi người làm cụ thể.

## 8. Nghiệm thu dự kiến

- Trả lời “hồ sơ đang ở đâu” đúng ít nhất 8/10 lần hỏi.
- Bóc đúng định danh chính trên tập đo đã duyệt.
- Tỷ lệ ghép sai gần 0 nhờ giữ Draft Case tới khi xác nhận.
- Người dùng tốn tối đa một thao tác ngắn mỗi ngày theo thiết kế thông báo.

## 9. Nguồn

- Thiết kế chi tiết và ví dụ ngành: `notaryoffice/intent.md`.
- Định danh chung: `contracts/entities.md`.
