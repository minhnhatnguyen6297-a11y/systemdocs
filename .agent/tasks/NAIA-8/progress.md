# NAIA-8/12 — tích hợp Word

Trạng thái: đã triển khai local, chờ root review; không đổi issue bên ngoài.
Nguồn: plan-multica-word-integration.md, owner takeover 03/10/2026.
Kiểm chứng: 04/10/2026.

Sau root review 04/10: sửa năm ISO snapshot, xuống dòng Word thật/khoảng trắng,
đủ tên A/B, chặn xuất Nơi niêm yết chưa lưu, báo XML note hỏng, mock readiness
và loại DOCM chưa hỗ trợ. Thêm test sửa metadata trong lúc save đang chờ;
oracle đọc đúng xuống dòng/tab nhưng vẫn bắt sai người/năm sinh.
Root chạy: 409 backend Word/workspace/MIN-141, 102 migration-export oracle,
240 adapter, 190 renderer/schema/wire và 78 ví dụ contract đều qua.
Chạy mới 22 mẫu: 22 saved, 0 failed, negative passed, source unchanged;
17 DOCX structural passed, 5 DOC structural not_verified; Word COM available.
Report: `artifacts/word-integration-review-fixes-final-20261004/e2e_report.json`.
Native picker và nhìn từng trang chưa chạy; không nâng thành nghiệm thu desktop.

- Áp dụng đúng diff fbd3c9f → 6889c7b; giữ MIN-141 thay vì lấy source cũ.
- Ghép snapshot/null của người, tài sản/cụm đất 1..20 và metadata hồ sơ.
- Thư mục mẫu, 2-party, renderer XML parts, metadata update, schema/UI và
  migration/oracle khôi phục. Ngày đầy đủ hiển thị dd/mm/yyyy; Bên A/B giữ
  ghế trống; phase thư mục chỉ chặn kỹ thuật theo owner.
- Metadata-only save cập nhật đúng key snapshot; hồ sơ legacy không sinh
  snapshot thiếu Stage. UI giữ các draft khác và baseline sau save.
- Word SaveAs2 bị pin chống đổi file chặn: fallback WordOpenXML trong bộ nhớ,
  ZIP XML/binary ghi qua handle kiểm danh tính, pin giữ đến receipt/Close.
  Test 4 điểm lifecycle cũ + fallback/foreign/binary đạt.
- Kiểm tra focused MIN-141/Word/workspace 327 pass; sau thay đổi cuối,
  Word engine/batch 142 pass (gồm test mới static không người nhận).
  Migration/E2E 172 pass; adapters 238 pass; renderer/schema/wire 187 pass.
  Validator contract 78/78 đạt. Không chạy lại toàn suite không liên quan.
- Fresh owner source: 17 DOCX + 5 DOC, migration 22/22, batch 22/22, phép
  thử thiếu đại diện đạt, hash bản sao và nguồn gốc 22/22 giữ nguyên.
- Report: artifacts/word-integration-20261004-final/e2e_report.json.
  Word COM số trang nguồn/mẫu chuyển khớp 22/22; structural XML 17 pass,
  5 DOC not_verified do không có XML gốc. UI Electron/native dialog và
  kiểm trực quan từng trang chưa chạy.

Mẫu/report không commit; không chạm DB thật, worktree Multica, code địa chỉ/
import của root; không push, PR hay gửi thông báo ngoài.
