'use strict';
/*
 * error-catalog.js — Danh mục lỗi → thông điệp thân thiện + rule nghiệp
 * vụ ẩn sau mã lỗi (MIN-136). Đây cũng là bảng liệt kê "rule ẩn" của hệ
 * thống: mỗi entry ghi rõ hệ thống đang chặn/báo điều gì và người dùng
 * làm gì tiếp theo.
 *
 * Nguồn mã lỗi:
 *   - notary_v2/services/case_workspace.py  (WorkspaceError + field errors)
 *   - notary_v2/services/inheritance_engine.py (engine errors/warnings)
 *   - shell/sidecar/notary_adapter.py + notary_mock_adapter.py (CommandError)
 *   - shell/src/main/command-client.js + renderer.js (transport codes)
 *
 * Nguyên tắc hiển thị: user KHÔNG nhìn mã snake_case trần. describeError
 * trả { code, title, hint } — title là câu tiếng Việt; code giữ để tra
 * cứu/diagnostics (hiển thị mờ hoặc tooltip, không phải nội dung chính).
 */

// code → { title, hint } — title: chuyện gì; hint: người dùng làm gì /
// rule ẩn nào đang được bảo vệ. hint=null khi title đã tự đủ.
const ERROR_CATALOG = {
  // ---- Transport / vỏ ứng dụng ----
  submit_failed: {
    title: 'Không gửi được lệnh tới engine',
    hint: 'Engine có thể đang khởi động — đợi vài giây rồi thử lại.',
  },
  engine_unavailable: {
    title: 'Engine nghiệp vụ chưa sẵn sàng',
    hint: 'Đợi engine khởi động xong; nếu vẫn lỗi thì khởi động lại ứng dụng.',
  },
  engine_shutdown: {
    title: 'Engine nghiệp vụ đã dừng giữa chừng',
    hint: 'Khởi động lại ứng dụng để dựng lại engine.',
  },
  engine_version_mismatch: {
    title: 'Shell và engine không khớp phiên bản contract',
    hint: 'Cập nhật đồng bộ cả hai phía trước khi dùng.',
  },
  unsupported_contract: {
    title: 'Tính năng này chưa được engine phiên bản hiện tại hỗ trợ',
  },
  command_unknown: {
    title: 'Engine không nhận diện được lệnh',
    hint: 'Phiên bản shell/engine lệch — kiểm tra cập nhật.',
  },
  shell_internal_error: {
    title: 'Lỗi nội bộ của vỏ ứng dụng',
  },
  unknown: { title: 'Lỗi không xác định' },
  user_canceled: { title: 'Đã hủy thao tác' },

  // ---- File / scope ----
  file_not_found: { title: 'Không tìm thấy file' },
  file_locked: {
    title: 'File đang bị khóa bởi chương trình khác',
    hint: 'Đóng file đó ở chương trình đang mở rồi thử lại.',
  },
  file_scope_denied: {
    title: 'File nằm ngoài phạm vi được phép',
    hint: 'Chỉ file đi qua hộp thoại chọn / vùng thả của ứng dụng mới đọc được.',
  },
  file_scope: {
    title: 'File nằm ngoài phạm vi được phép',
    hint: 'Chỉ file đi qua hộp thoại chọn / vùng thả của ứng dụng mới đọc được.',
  },
  unconfirmed: {
    title: 'Nguồn nhập chưa được xác nhận',
    hint: 'Chọn file/loại nguồn rõ ràng rồi nhập lại.',
  },
  ocr: {
    title: 'Tài liệu cần OCR nhưng engine OCR chưa sẵn sàng',
  },
  unsupported: {
    title: 'Tính năng chưa được hỗ trợ',
  },

  // ---- Workspace (case_workspace.py) ----
  case_not_found: {
    title: 'Không tìm thấy hồ sơ',
    hint: 'Hồ sơ có thể đã bị xóa — tải lại danh sách ở tab Tổng quan.',
  },
  case_type_unsupported: {
    title: 'Loại việc này chưa được hỗ trợ',
    hint: 'Chỉ đọc được dữ liệu hiện có, không chỉnh sửa.',
  },
  workspace_locked: {
    title: 'Hồ sơ đã khóa',
    hint: 'Mọi thao tác chỉ đọc — mở khóa ở engine trước khi sửa.',
  },
  workspace_conflict: {
    title: 'Hồ sơ đã thay đổi ở phiên bản khác',
    hint: 'Tải lại bản mới hoặc giữ nháp để sao chép tay.',
  },
  workspace_owner_required: {
    title: 'Chưa chọn người để lại tài sản',
    hint: 'Kéo người để lại (đã mất) từ bảng Người vào ô khởi tạo ' +
      'trên sơ đồ thừa kế.',
  },
  stage: {
    title: 'Dữ liệu Stage chưa hợp lệ',
    hint: 'Sửa các ô/dòng đánh dấu đỏ rồi lưu lại.',
  },
  stage_validation_error: {
    title: 'Dữ liệu Stage chưa hợp lệ',
    hint: 'Sửa các ô/dòng đánh dấu đỏ rồi lưu lại.',
  },
  validation_error: { title: 'Dữ liệu không hợp lệ' },
  diagram_invalid_state: {
    title: 'Sơ đồ chưa hợp lệ',
    hint: 'Xem chi tiết trong phần cảnh báo dưới sơ đồ.',
  },
  diagram_owner_mismatch: {
    title: 'Ô chủ đất trên sơ đồ lệch với dữ liệu người để lại',
    hint: 'Gán lại người để lại vào ô khởi tạo trên sơ đồ.',
  },
  diagram_domain_mismatch: {
    title: 'Sơ đồ không đúng loại việc của hồ sơ',
  },
  diagram_reference_outside_stage: {
    title: 'Sơ đồ tham chiếu người không còn trong Stage',
    hint: 'Người đó có thể đã bị xóa khỏi Stage — gán lại trên sơ đồ.',
  },

  // ---- Field-level (trong details.fields của stage_validation_error) ----
  required: { title: 'Trường bắt buộc chưa có giá trị' },
  row: { title: 'Dòng dữ liệu không hợp lệ' },
  invalid_date: {
    title: 'Ngày không hợp lệ',
    hint: 'Nhập theo dd/mm/yyyy (trường người có thể chỉ nhập năm).',
  },
  invalid_enum: { title: 'Giá trị không nằm trong danh sách cho phép' },
  invalid_format: { title: 'Định dạng không hợp lệ' },
  invalid_type: { title: 'Kiểu dữ liệu không hợp lệ' },
  invalid_boolean: { title: 'Giá trị đúng/sai không hợp lệ' },

  // ---- Engine thừa kế (inheritance_engine.py) ----
  missing_land_owner: {
    title: 'Chưa có người để lại tài sản trên sơ đồ',
    hint: 'Kéo người để lại vào ô khởi tạo — engine chỉ tính được ' +
      'khi có người đã mất sở hữu tài sản.',
  },
  no_valid_heir: {
    title: 'Không có người thừa kế hợp lệ',
    hint: 'Phần tài sản của người này chưa phân được — kiểm tra lại ' +
      'các nhánh trên sơ đồ.',
  },
  unknown_person: {
    title: 'Sơ đồ tham chiếu người không có trong Stage',
  },
  duplicate_person: {
    title: 'Một người đang nằm trên nhiều ô sơ đồ',
    hint: 'Mỗi người chỉ được gán vào một ô.',
  },
  duplicate_node_id: { title: 'Trùng mã ô trên sơ đồ' },
  duplicate_node: { title: 'Trùng mã ô trên sơ đồ' },
  duplicate_parent: { title: 'Một ô khai báo trùng cha/mẹ' },
  missing_node_id: { title: 'Một ô trên sơ đồ thiếu mã định danh' },
  ancestry_cycle: {
    title: 'Quan hệ gia đình tạo vòng lặp',
    hint: 'Kiểm tra lại cha/mẹ — con trên các ô liên quan.',
  },
  spouse_conflict: {
    title: 'Quan hệ vợ/chồng mâu thuẫn',
    hint: 'Hai ô phải khai báo vợ/chồng qua lại đúng một cặp.',
  },
  self_parent: { title: 'Một ô tự nhận chính mình là cha/mẹ' },
  self_spouse: { title: 'Một ô tự nhận chính mình là vợ/chồng' },
  dangling_parent: { title: 'Quan hệ cha/mẹ trỏ tới ô không tồn tại' },
  dangling_spouse: { title: 'Quan hệ vợ/chồng trỏ tới ô không tồn tại' },
  too_many_parents: {
    title: 'Một ô có quá 2 cha/mẹ',
  },
  invalid_parent_slots: { title: 'Quan hệ cha/mẹ không hợp lệ' },
  invalid_parent: { title: 'Quan hệ cha/mẹ không hợp lệ' },
  invalid_spouse: { title: 'Quan hệ vợ/chồng không hợp lệ' },
  invalid_position: {
    title: 'Vị trí tài sản trên ô sơ đồ không hợp lệ',
    hint: 'Vị trí phải nằm trong số tài sản hiện có ở Stage.',
  },
  missing_position: { title: 'Một ô thiếu vị trí tài sản bắt buộc' },
  invalid_death_date: {
    title: 'Ngày mất không hợp lệ',
    hint: 'Điền ngày mất dạng dd/mm/yyyy ở bảng Người.',
  },
  invalid_domain: { title: 'Loại sơ đồ không hợp lệ' },
  invalid_node_id: { title: 'Mã ô trên sơ đồ không hợp lệ' },
  invalid_node: { title: 'Một ô trên sơ đồ có dữ liệu sai' },
  invalid_nodes: { title: 'Dữ liệu sơ đồ không hợp lệ' },
  invalid_version: { title: 'Phiên bản dữ liệu sơ đồ không được hỗ trợ' },
  invalid_input: { title: 'Đầu vào của engine không hợp lệ' },
  conservation_failed: {
    title: 'Tổng phần chia không bảo toàn (lỗi engine)',
    hint: 'Ghi nhận lỗi này để kiểm tra — không do thao tác của bạn.',
  },

  // ---- Intake ----
  intake_unsupported_source: {
    title: 'Loại nguồn nhập chưa được hỗ trợ',
  },
  intake_too_many_sources: {
    title: 'Quá nhiều nguồn trong một lần nhập',
  },
  intake_text_too_long: { title: 'Văn bản nhập quá dài' },
  intake_source_too_large: { title: 'File nhập quá lớn' },
  intake_parse_failed: {
    title: 'Không đọc được nội dung từ nguồn',
    hint: 'Thử file/ảnh rõ hơn hoặc nhập tay.',
  },
  extraction_failed: {
    title: 'Không trích xuất được dữ liệu từ tài liệu',
  },

  // ---- Word ----
  word_batch_failed: {
    title: 'Xuất Word không thành công',
    hint: 'Xem trạng thái từng văn bản trong hộp thoại Xuất Word.',
  },
  word_no_documents_selected: {
    title: 'Chưa chọn văn bản để xuất',
  },
  word_unknown_document_key: {
    title: 'Loại văn bản không tồn tại trong hệ thống',
  },
  word_duplicate_document_key: {
    title: 'Loại văn bản bị chọn trùng',
  },

  // ---- Khác ----
  unknown_website: { title: 'Không nhận diện được trang đích' },
};

// describeError(err) → { code, title, hint, raw } — title/hint thân
// thiện cho UI; raw giữ message gốc của backend để diagnostics.
function describeError(err) {
  const e = err || {};
  const code = e.code || 'unknown';
  const ent = ERROR_CATALOG[code];
  return {
    code,
    title: ent ? ent.title : (e.message || code),
    hint: (ent && ent.hint) || null,
    retryable: !!e.retryable,
    nextAction: e.next_action || null,
    raw: e.message || '',
  };
}

// Dòng thông báo ngắn cho toast/banner: "Title — hint". Mã lỗi kèm ở
// cuối trong ngoặc (mờ, để tra cứu) — không phải nội dung chính.
function errText(err) {
  const d = describeError(err);
  const base = d.hint ? `${d.title} — ${d.hint}` : d.title;
  return `${base} (${d.code})`;
}

const G1_NOTARY_ERRORS = { ERROR_CATALOG, describeError, errText };

if (typeof window !== 'undefined') window.G1_NOTARY_ERRORS = G1_NOTARY_ERRORS;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_ERRORS;
}
