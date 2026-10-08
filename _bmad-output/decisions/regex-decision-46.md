---
id: regex-decision-46
title: >-
  Owner 06/10: serial nguyen van o moi tang, que quan giu khong dien, so TK bao
  hiem gan co chua ho tro, loi regex = regex_workbench (trich + de xuat
  placeholder) - TASK-5
date: '2026-10-06 16:14'
status: accepted
---
## Context

Sau gộp `consolidate/monorepo` vào nhánh task5, phát hiện các SOT mâu thuẫn
nhau (xem `.agents/sot-inventory-20261006.md`): entities.md §2/contract ép
serial `[A-Z]{2}\d{6,8}` trong khi decision-2 và TASK-5 ghi tự do; contract
còn `place_of_origin` dù UI đã bỏ; task5 tự xây lõi regex mới song song với
`tools/regex_workbench/engine` Owner đã chọn 02/10; Owner bổ sung chức năng
lõi: quét cấu trúc mẫu Word để đề xuất placeholder cho soạn hồ sơ.

## Decision

1. Serial GCN là chuỗi nguyên văn tùy nguồn ở MỌI tầng (trích xuất, Stage,
   DB): không bắt buộc format, có thể trống, có thể trùng giữa thửa; không
   chuẩn hóa, không thay mã `XX` khi đọc hồ sơ cũ.
2. `place_of_origin` (quê quán) giữ trong contract để đọc snapshot cũ;
   intake/UI hiện hành không dùng — engine không điền.
3. Sổ tiết kiệm và bảo hiểm tạm dừng: engine chỉ nhận diện sự hiện diện và
   gắn cờ "loại tài sản chưa hỗ trợ", không bóc dòng.
4. Lõi regex dùng chung là `tools/regex_workbench/engine` (zoning-first).
   `upload_lab/extract_contract.py` là engine thừa kế đang chạy, dùng làm
   nguồn kiến thức trường để port sang profile. Lõi nhận input file Word
   hoặc text thô, và phục vụ đề xuất placeholder cho mẫu chưa gắn template.
5. Người chết = person_row có `ngay_chet`; trích lục khai tử điền vào trường
   giấy tờ người (`so_giay_to`/`ngay_cap`/`noi_cap`/`loai_giay_to`).
6. Thông tin chung (số CC, ngày, CCV) chưa chốt đích lưu; hướng an toàn là
   bảng thông tin hồ sơ — cần bổ sung contract trước khi code.

## Consequences

Đã đồng bộ: entities.md §2; contract §4.1/§4.2/§13.3/§13.16;
common.schema.json + draft-v2.schema.json (bỏ pattern serial);
validate_examples.py (serial chỉ kiểm kiểu chuỗi);
docx-import.md (serial, diện tích neo m2, người chết, cờ chưa hỗ trợ);
regex-rules.md §0 + regex-core.md §6-7 (lõi = regex_workbench).
Việc còn lại: `case_workspace.py` (so_n_format) và `form.html` (required)
còn ép serial ở runtime — thuộc task triển khai, không sửa trong đợt SOT.

## Integration 08/10/2026
Mã cũ decision-46 thuộc nhánh regex. Mã riêng giữ nguyên nội dung và tránh trùng quyết định khác của nhánh chính.
