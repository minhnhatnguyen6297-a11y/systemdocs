# Bàn giao Word NAIA-8/12

Root review và sửa bổ sung 04/10/2026: năm ISO, xuống dòng/khoảng trắng Word,
đủ tên A/B, Nơi niêm yết chưa lưu, XML note hỏng, mock parity, DOCM exclusion,
pending-save edit và oracle độc lập đọc control Word. Root kiểm 409 backend,
102 oracle, 240 adapter, 190 renderer/schema/wire và 78 ví dụ contract đều qua.
Report mới thay bằng chứng trước: `artifacts/word-integration-review-fixes-final-20261004/e2e_report.json`
với 22/22 saved, 0 failed, negative passed, originals unchanged; 17 DOCX
structural passed và 5 DOC structural not_verified. Native UI/visual pages
vẫn chưa thực hiện, ghi trong deferred-work; không tự đổi trạng thái issue.

Đã ghép tip Word 6889c7b vào source MIN-141 của branch tích hợp. Giữ nguyên
database/model MIN-141, thêm Word engine/batch/UI/schema/migration và sửa các
lỗi ghép snapshot metadata, giữ draft, ngày đầy đủ và ghế trống hai bên.
Owner bỏ slot ủy quyền2: test metadata cũ đổi từ duplicate slot1 sang assert
không đăng ký token, theo quyết định 02/10/2026; không bỏ coverage snapshot.

Word COM đã chuyển mới cả 5 DOC. SaveAs2 không thể thay inode đang pin;
fallback WordOpenXML đóng gói ZIP đủ XML/binary và ghi qua writer handle được
so danh tính với pin read handle. Không dùng conversion reference cũ.

Kiểm chứng: focused MIN-141/Word/workspace 327 pass; Word engine/batch cuối
142 pass; migration/E2E 172 pass; adapters 238 pass; renderer/schema/wire
187 pass; 78 ví dụ contract đúng. Report cuối ở
artifacts/word-integration-20261004-final/e2e_report.json: ok=true,
22 migration, 22 saved, 0 failed, negative passed, sources_unchanged=true.
Nguồn owner gốc cũng được hash lại: 22/22 không đổi.

Giới hạn: chưa thao tác Electron/native picker thật, chưa xem trực quan các
trang. 17 DOCX so cấu trúc XML đạt; 5 DOC chỉ có bằng chứng Word COM mở được
và số trang nguồn/mẫu chuyển khớp, vẫn not_verified ở tầng XML. Không coi
batch saved là nghiệm thu pháp lý hoặc xác nhận thị giác. Root review diff
và report trên commit tích hợp trước khi kết luận chung.

Artifacts chứa bản mẫu chuyển và output test: để local, không commit hoặc
upload. Không thay trạng thái task bên ngoài. Spec Word/catalog/2-party/
contract cập nhật cùng phạm vi.
