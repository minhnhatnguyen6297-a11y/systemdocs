# Chỉ mục quyết định: tìm kết luận, tìm “tại sao”

**Kiểm kê bước đầu:** 28/09/2026, MIN-135. Đây là **bản đồ đường dẫn**, không phải
nguồn quy tắc mới. Trước khi sửa sản phẩm, mở nguồn được dẫn và kiểm tra trạng thái
hiện tại của chính nguồn đó. “Đã chốt” trong bảng là trạng thái **nguồn ghi**, không
chứng minh code đã làm xong hoặc điều kiện ngoài đời vẫn y nguyên.

Hai cột cuối cố ý tách riêng:

- **Lý do đã viết**: tài liệu hiện có giải thích vì sao chọn cách đó.
- **Lời gốc của owner**: có đường dẫn tới câu nói, comment hoặc bản duyệt gốc,
  giữ ví dụ và ngoại lệ. `Chưa dẫn` nghĩa là **trong nguồn được kiểm ở đây** chưa
  có đường dẫn đó; không khẳng định lời giải thích chưa từng tồn tại.

| # | Cần biết điều gì? | Trạng thái nguồn ghi | Mở nguồn có thẩm quyền | Lý do đã viết | Lời gốc của owner |
|---|---|---|---|---|---|
| K01 | Khi máy suy ra dữ liệu hồ sơ, ai xác nhận? | Nguyên tắc đã chốt | [VISION.md](VISION.md) §2 | Có: một suy đoán sai có thể làm lệch hồ sơ; máy chỉ tạo ứng viên | Chưa dẫn trong mục này |
| K02 | Vì sao Upload Lab đọc file Word thay vì lấy từ phần mềm quản lý cũ? | B1 đã chốt | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) §B1 | Có: phần mềm đang dùng không có API lấy dữ liệu; Word là nguồn công việc thật | Chưa dẫn trong mục B1 |
| K03 | Zalo được đọc đến đâu? | B2 đã chốt về **ranh giới quyền riêng tư** | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) §B2 | Có: chỉ tài khoản chung của văn phòng, trong phạm vi đã nêu; không mở sang tài khoản nhân viên | Chưa dẫn trong mục B2 |
| K04 | Có thể dùng số bản in để xác định hồ sơ đã in bản cuối? | A2 ghi **không** | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) §A2 | Có hệ quả thiết kế: số bản chỉ là suy đoán, không được làm điều kiện cứng | Chưa dẫn phép đo gốc hoặc lời owner trong mục A2 |
| K05 | Có đọc được file khi Word giữ file, ổ Z: báo đổi file đầy đủ, 6 máy dùng tài khoản riêng? | A1/A3/A4 còn mở trong nguồn | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) §A | Nguồn ghi tác động của từng đáp án; chưa có kết quả đo | Chưa có kết luận để gắn lời gốc |
| K06 | CCCD trùng thì có tự gộp hồ sơ không? Tên người có làm khóa không? | Contract hiện hành: **không** | [entities.md](../../contracts/entities.md) §1, §6–7 | Có: CCCD xác định người, không xác định Case; tên trùng dễ gây gán sai | Chưa dẫn trong contract |
| K07 | Vì sao tài liệu nghiệp vụ của Notary chia theo domain và platform? | ADR Accepted | [ADR-0001](../../notary_v2/docs/architecture/decisions/0001-domain-module-documentation-architecture.md) | Có: bối cảnh, động lực, phương án loại và hệ quả | ADR là bản giải thích; chưa dẫn lời owner gốc |
| K08 | UI chung đọc file nào, ảnh mẫu có là quy tắc nghiệp vụ không? | UI ACTIVE/Approved | [UI README](../product/ui/README.md) §1–3; [MIN-124 decisions](../../.agent/tasks/MIN-124/decisions.md) | Có cho cách chia SOT; ảnh chỉ là tham chiếu thị giác | Có ngày duyệt, nhưng chưa dẫn lời giải thích gốc cho từng lựa chọn |
| K09 | Electron là shell, Python giữ nghiệp vụ? | Hướng đích đã chốt trong tài liệu hệ thống | [TECH_STACK.md](TECH_STACK.md) §1; [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) §5.1 | Có ranh giới và hệ quả kỹ thuật; **lý do owner chọn Electron** chưa được ghi đủ ở các mục này | Chưa dẫn ở các mục này |
| K10 | Người nhận và người từ chối trong Word suy ra từ đâu? | Tài liệu flow có; **spec tính thừa kế chưa được duyệt** | [word-export.md](../../notary_v2/docs/domains/inheritance/word-export.md) §2, §6; [Inheritance README](../../notary_v2/docs/domains/inheritance/README.md) | Có ranh giới: từ chối cần đầu vào pháp lý riêng, không suy từ nút “Nhận” | Chưa dẫn quyết định nghiệp vụ gốc trong flow |
| K11 | Placeholder Word đang hỗ trợ trường nào? | Danh mục hiện có, phạm vi thừa kế | [placeholder_mapping.md](../../notary_v2/word_templates/placeholder_mapping.md) | Có mô tả nguồn và cách dựng một số trường; **không phải từ điển toàn bộ dữ liệu Người** | Chưa dẫn lời gốc cho từng quy tắc |
| K12 | Có chọn MarkItDown/adapter OCR làm production chưa? | Decision record **DRAFT** | [MIN61_CONVERSION_OCR_DECISION.md](../product/MIN61_CONVERSION_OCR_DECISION.md) | Có bằng chứng POC, giới hạn và gate; chưa được dùng làm quyết định đã duyệt | Chờ xác nhận owner theo §7 |

## Khoảng trống cần giải trước khi spec chi tiết

1. **Từ điển dữ liệu Người chưa có một bản đầy đủ được duyệt.** [Mapping
   placeholder](../../notary_v2/word_templates/placeholder_mapping.md) chỉ cho
   biết đầu ra Word trong phạm vi thừa kế; [word-export](../../notary_v2/docs/domains/inheritance/word-export.md)
   mô tả luồng. Hai file này chưa trả lời cho *mỗi trường*: ai nhập, ai nhìn thấy,
   tính theo công thức nào, được lưu hay chỉ tính khi xuất, lấy từ nguồn nào,
   áp dụng cho loại hồ sơ nào, và tại sao. Đây là đầu vào của nhóm D (dữ liệu)
   và W (Word), không được tự suy ngược từ placeholder.
2. **Một số kết luận chỉ còn bản diễn giải.** B1, B2, A2 và contract định danh
   có lý do hữu ích, nhưng chỉ mục chưa tìm thấy link tới lời giải thích nguyên
   gốc của owner trong chính các nguồn trên. Khi owner nhắc lại, lưu nguyên ý
   cùng ví dụ, ngoại lệ và nguồn theo [KNOWLEDGE.md](KNOWLEDGE.md); không thay
   lời gốc bằng câu ngắn trong bảng này.
3. **Có dấu hiệu tài liệu lệch hiện trạng.** [OPEN_DECISIONS.md](OPEN_DECISIONS.md)
   §B2 và [TECH_STACK.md](TECH_STACK.md) §1.1 còn ghi repo/folder Zalo “chưa có”,
   trong khi `AGENTS.md` hiện ghi Zalo đã tách sang `D:\zalo-intake`. Phải đối
   chiếu repo và issue [MIN-103](https://linear.app/minhnotary/issue/MIN-103/migrate-engine-zalo-thanh-module-thu-tu-trong-repo-rieng-va-zalo)
   trước khi dùng các câu về **vị trí engine**. Ranh giới quyền riêng tư B2 là
   quyết định khác, không bị câu vị trí này tự động thay thế.

## Cách dùng chỉ mục

Tìm câu hỏi → mở nguồn → đọc trạng thái, phạm vi, ngày/nguồn duyệt → mở lời gốc
nếu có → mới viết spec hoặc story. Nếu nguồn chỉ có kết luận mà thiếu lời gốc,
ghi `Tại sao: Chưa truy được lời giải thích gốc` trong task hiện tại và hỏi owner
khi quyết định đó ảnh hưởng hành vi. Khi có lời giải thích mới, cập nhật **nguồn
thuộc đúng module** rồi sửa đường dẫn hoặc trạng thái trong bảng này; không chép
nguyên một quy tắc nghiệp vụ mới vào chỉ mục cấp hệ thống.
