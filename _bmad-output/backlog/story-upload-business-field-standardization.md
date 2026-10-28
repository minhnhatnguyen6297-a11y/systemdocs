---
id: 41
type: story
title: "Thống nhất toàn bộ trường nghiệp vụ Upload theo chuẩn Người–Tài sản–Hồ sơ trước quét mẫu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Thống nhất toàn bộ trường nghiệp vụ Upload theo chuẩn Người–Tài sản–Hồ sơ trước quét mẫu

## Description

Owner báo Upload đang bóc văn bản thành trường để điền website nhưng hệ thống còn trường nghiệp vụ mồ côi và thiếu trường Hồ sơ. Thống nhất đầy đủ trường bóc tách/biểu mẫu Upload với chuẩn DB/contract ba đối tượng, chốt các gap có căn cứ rồi triển khai cutover mọi consumer bị ảnh hưởng. Người có thẩm quyền duyệt catalog/phần mở rộng canonical còn thiếu trước code; nghiệm thu issue là prerequisite của mọi lượt khảo sát/quét mẫu thực mới, corpus và vòng E2E theo mẫu, không chỉ của Upload.

## Acceptance Criteria

1. **Inventory đầy đủ xuyên module, không chỉ workspace Notary**
   **Given** các trường nghiệp vụ hiện có ở Upload, từ lõi bóc tách, adapter, kết quả lưu/đọc đến biểu mẫu website và consumer liên quan
   **When** lập catalog có nguồn và đối chiếu với chuẩn Người–Tài sản–Hồ sơ
   **Then** từng trường có nghĩa nghiệp vụ, đối tượng sở hữu, canonical key, kiểu, format/độ đầy đủ ngày, nhóm/thứ tự/cardinality, đích DB, wire và output/consumer maps; có nguồn thẩm quyền và trạng thái defined/Draft/ambiguous/unmapped.
   **And** ghi đầy đủ gap thực sự, xung đột và trường bị loại có lý do; không gọi bảng cột workspace Notary hoặc catalog local Draft là inventory đầy đủ hay implementation xong. Raw, provenance, file, cookie, cấu hình tab và timeout kỹ thuật được tách khỏi nghiệp vụ, không tự coi là orphan.
2. **Chốt đúng các lựa chọn của owner và phần chưa chọn**
   **Given** catalog đầy đủ, bao gồm chủ đất, số/ngày công chứng, công chứng viên, thư ký và các trường Upload khác
   **When** refine bộ trường canonical với người có thẩm quyền
   **Then** chủ đất thuộc **Hồ sơ**, không thành thuộc tính chủ sở hữu cố định của Tài sản và không mặc định bằng node `owner`/`owner_row_id` Thừa kế; thông tin công chứng thuộc **Hồ sơ**, độc lập với ngày tạo hồ sơ.
   **And** key/kiểu/cardinality/quan hệ/FK hoặc cấu trúc danh sách chưa chọn phải được chốt có căn cứ; chuẩn Hồ sơ được mở rộng khi thực sự cần và được duyệt, không xóa trường Upload cần thiết chỉ để vừa schema hiện tại, không suy mọi trường đã là cột DB được duyệt.
3. **Loại đúng thông tin owner bỏ qua**
   **Given** nguồn có thông tin giao dịch hoặc thời hạn nghiệp vụ
   **When** bóc tách và tạo dữ liệu nghiệp vụ chuẩn hóa theo chuẩn đã chốt
   **Then** không lấy giá giao dịch, đặt cọc, tiền thuê, khoản vay, lãi suất, điều khoản thanh toán hoặc thời hạn nghiệp vụ thành trường bóc tách/normalized.
   **And** vẫn giữ thời hạn sử dụng đất đúng cụm `land_rows[].thoihan` và timeout kỹ thuật đúng vai trò. Nếu portal yêu cầu trường bị loại, catalog ghi xung đột consumer/câu hỏi refinement để xử lý trước cutover; không âm thầm giữ extraction, bịa/default hoặc tự quyết bước nhập tay mới. Không xóa/viết lại raw hoặc bằng chứng lịch sử để đạt tiêu chí.
4. **Chuẩn được duyệt đi hết DB/contract và mọi consumer**
   **Given** catalog, mapping và phần mở rộng cần thiết đã được duyệt trước implementation
   **When** triển khai phạm vi chuẩn hóa được giao
   **Then** schema/contract, adapter, writer, reader, payload chuẩn hóa, output điền web và mọi consumer bị ảnh hưởng đều dùng cùng nghĩa/kiểu/format/nhóm/cardinality đã chốt; lưu/đọc lại không mất hoặc đổi nghĩa dữ liệu cần thiết.
   **And** không còn đường nghiệp vụ mồ côi trong phạm vi inventory; cụm trường phụ website đáp ứng điều kiện owner nêu là trường đã chốt, không tính orphan; không dùng `ghiChu` chung thay trường; raw capture chỉ provenance, không thay trường nghiệp vụ, không shim/alias mới chưa duyệt hoặc chỉ đổi tên để báo xanh. Consumer cũ bị thay được cutover đầy đủ, không để hai chuẩn song song; dữ liệu cũ và tham chiếu được bảo toàn theo thiết kế chuyển đổi đã duyệt.
5. **Chứng minh luồng thật, độc lập corpus owner đang bị gate**
   **Given** implementation được giao, input tổng hợp/kiểm soát và DB/profile cô lập có đáp án độc lập
   **When** chạy đường consumer thật từ extraction/chuẩn hóa qua ghi–đọc–mở lại đến output website theo khả năng được hỗ trợ
   **Then** bằng chứng thể hiện đúng đối tượng/trường/nhóm, không mất trường cần thiết, không orphan, không lấy trường bị loại; thiếu/mơ hồ/xung đột không bị đoán hoặc nhét ghi chú. Có hồi quy và bằng chứng bảo toàn dữ liệu cũ/tham chiếu cho thay đổi schema cần thiết.
   **And** proof không chỉ validator cục bộ, mock hoặc key rename; nêu rõ phạm vi thực chạy và giới hạn portal. Không tự bấm Lưu hoặc suy kết quả Lưu; không cần đọc/quét corpus `D:\testcase` để đóng issue này, tránh vòng phụ thuộc gate.
6. **Gate trước khảo sát mẫu được nghiệm thu đầy đủ**
   **Given** future owner-sample batch/mass survey, corpus hoặc vòng E2E theo mẫu ở bất kỳ module nào
   **When** quyết định có thể bắt đầu lượt đó
   **Then** phải có nghiệm thu #41 gồm catalog được duyệt, cutover và proof thực của các tiêu chí trên; bảng mapping hoặc local Draft không mở gate, ghi issue không phải quyền bắt đầu implementation.
   **And** chỉ sau gate và khi được giao thực thi mới tiếp tục vòng LLM đọc mẫu trước → nhận diện cấu trúc → so spec/code → sửa có căn cứ → test/lặp. Khi đó phần chưa rõ từng file vẫn pending qua #39, không chặn file đã rõ; không biến gate thành feature flag/tắt Scan/Upload production.

## Boundaries

- Owner đã giao triển khai liên tục phần runtime Nam Định đã chốt; không cần technical approval pause. Không đọc mẫu/corpus, portal thật upload/Save, production DB hoặc credentials; verification riêng #41 dùng nguồn tổng hợp và browser/SQLite/form cô lập. Chỉ dừng phần phụ thuộc quyết định nghiệp vụ/schema thật sự chưa chốt.
- Website chính thức vẫn là SOT; app chỉ điền sẵn, người dùng tự kiểm tra và bấm Lưu. Rule regex/website có version do developer quản lý; không thêm UI quản lý rule cho người dùng.
- Không chọn engine DB vật lý chung, shared Case ID, DB merge hay quyền liên kết/ghi chéo module. Contract Upload còn Draft không tự thành approved.
- #40 serial GCN Stage/persistence là issue riêng, không nhân bản phạm vi hoặc tuyên bố fixed bởi #41. #20 Danh sách hồ sơ vẫn DEFERRED, whitelist UI/search/filter chưa duyệt.
- #42 nhiều giấy tờ và địa chỉ của một Người là một issue riêng, không tự là prerequisite; không ép model một giấy hiện tại thành đa trị để hoàn thành #41.
- D06+D07 về nhiều Người–nhiều Tài sản chuyển một [#43 riêng](spike-case-people-assets-relationships.md), xử lý ngay sau làm rõ các ô Nam Định §7. Không chờ toàn #41 xong, không #42 prerequisite; #41 tiếp nhận đáp án trước cutover quan hệ, không chọn model/FK/cardinality ở lượt docs.

## References

- parent — none
- decision — _bmad-output/decisions/decision-owner-upload-field-standardization-20261019.md, Quyết định hiện hành
- behavior — _bmad-output/specs/shared/data-rules.md, §4.2
- behavior — _bmad-output/specs/shared/extraction-rules.md, Vòng làm việc theo mẫu thực; Giá trị từng trường
- behavior — _bmad-output/specs/upload_lab/README.md, §1, §2.3 và §3
- authority — contracts/entities.md, §8–9 và chuẩn định danh
- contract status — contracts/README.md, Trạng thái và contract trước code sau
- bounded static evidence — upload_lab/extraction_adapter.py, dòng 244–260: đường gọi extraction
- bounded static evidence — tools/regex_workbench/engine/contract_extract.py, dòng 4855–4908: payload form/structured output; dòng 3751 và 4540–4560: giấy tờ phụ và Người chết
- bounded static evidence — upload_lab/playwright_uploader.py, dòng 755–796: dựng dữ liệu form và điều kiện chuẩn bị
- bounded static evidence — upload_lab/uploader_selectors.py, dòng 23–38: thứ tự trường portal
- bounded schema evidence — notary_v2/models.py, dòng 36–48 và 99–150: model Notary hiện có, không phải bằng chứng toàn hệ thống không có đích trường
- implemented Case catalog — contracts/entities.md, §9.4; contracts/notary-case-drafting.md, metadata Case
- permanent Case regressions — upload_lab/tests/test_case_fields.py; notary_v2/tests/test_case_assigned_landowners.py; notary_v2/tests/test_inheritance_workspace.py, save/reopen ownership transitions

## Notes

- Decision 19/10/2026: owner yêu cầu ghi issue chuẩn hóa trước triển khai quét file mẫu; report orphan là ground truth, không chạy Upload để xác nhận lại trong lượt tài liệu.
- Evidence 19/10/2026: inventory source tĩnh có giới hạn đã thấy các key form `ten_hop_dong`, `ngay_cong_chung`, `so_cong_chung`, `nhom_hop_dong`, `loai_tai_san`, `cong_chung_vien`, `thu_ky`, `nguoi_yeu_cau`, `duong_su`, `tai_san`; các vùng Người/hàng đất có cấu trúc và output trình bày cùng tham gia luồng. Đây là ví dụ có căn cứ, không phải tuyên bố inventory toàn bộ đã xong.
- Evidence 19/10/2026: các điểm cần catalog/refinement gồm thông tin công chứng, tiêu đề/nhóm/loại văn bản, chủ đất, discriminator loại tài sản, `phan_ghi_them` và `chi_tiet_dien_tich`. Không tự đồng nhất nhóm/loại Upload với enum Notary hiện tại hoặc ghi tất cả thành cột mới. Nội dung nghiệp vụ trong container tên `raw` vẫn cần mapping; chỉ raw/bằng chứng kỹ thuật thực sự mới là provenance.
- Evidence 19/10/2026: `nguoi_yeu_cau`/`duong_su`/`tai_san` là output trình bày cần truy về dữ liệu Người/Tài sản/vai trò Hồ sơ đã chuẩn hóa, không thay canonical bằng chuỗi ghép. Các giá trị portal mặc định `tinh_trang`, `ghi_chu`, `phi_cong_chung`, `thu_lao_cong_chung` phải được phân loại theo nghĩa/consumer, không coi hằng/rỗng là dữ kiện đã bóc hoặc tự suy owner đã chọn chính sách phí công chứng. Raw/file/ambiguity evidence không là orphan nghiệp vụ.
- Evidence 20/10/2026: [SOT Nam Định bền vững](../specs/upload_lab/nam-dinh-website-sot.md)
  inventory toàn bộ **17 trường public-static quick-create**, 6 catalog, 7 required
  tĩnh; mapping source→canonical/raw/policy→DB-wire→selector/API. Tại mốc audit,
  repo có 15 mapping (14 fill-order entries, thiếu iterate attachment),
  hai phí thiếu mapping và nhánh prime có click Lưu. Slice runtime bên dưới
  đã xử lý preparation theo policy; không thêm key/cột. Catalog IDs/config/
  provenance khác nghiệp vụ; tổng vẫn không persistence riêng.
- Owner 20/10/2026 chốt **policy đích Nam Định**: bốn ô `chiphi.phicongchung`,
  `chiphi.thulaoCongchung`, `chiphi.phiDvNgoaicongchung`, `chiphi.phikhac`
  và Ghi chú `ghichu` bỏ qua/không điền; không ghi 0 hoặc xóa default portal,
  không thêm extraction/cột phí/quy trình nhập tay. Tổng không ô thứ năm,
  không persistence riêng. Mọi hợp đồng upload mặc định `DACONGCHUNG` /
  “Đã công chứng” — portal policy, không extracted fact/Notary draft/locked.
  Gap phí giữ làm hiện trạng ngoài scope, không pending owner choice.
  Runtime preparation đã được giao và kiểm chứng cô lập như mục dưới;
  mở rộng tương lai cần duyệt/giao riêng. Toàn #41 còn mở, gate mẫu **ĐÓNG**.
- Coverage hiện tại 20/10/2026 **sau user đăng nhập thủ công**: empty form live
  có **17 trường ngữ nghĩa**, **7 label required** (không HTML attr/enforcement).
  Sáu widget/list hiện render: status **3**, nhóm **13**, asset **12**, title **5**,
  CCV **3**, thư ký **5**. SOT giữ đầy đủ list phi cá nhân/ID-label và
  `vaitroDuongsu` của nhóm; nhân sự chỉ shape/count. Props↔DOM, không paging
  metadata/UI load-more là proof đầy đủ option **của phiên**, không tổng DB
  hoặc mọi đơn vị. Scope server/unit/global và form/submission conversion
  object↔ID vẫn unknown; required enforcement chưa thử. Không Lưu/submit,
  prime validation, upload hoặc mở record; portal DB chưa biết.
- Lịch sử trước đăng nhập 20/10/2026: **0 DOM authenticated, 0 catalog
  authenticated đầy đủ**; status 3 static, nhóm/asset public GET 403, title
  unscoped items=[] không chứng minh list đơn vị rỗng. Mốc này không còn là
  coverage hiện tại. Request source quick-create vẫn POST `/api/hoso/nhap-nhanh`
  với form state; audit live chưa capture submit body. Bổ sung evidence
  không đóng #41, mở gate mẫu, duyệt auxiliary business schema hoặc nghiệm thu
  cutover/consumer/backend.
- Decision 20/10/2026 R05: bỏ tự điền/chuẩn hóa mở rộng `ten_goi_khac`; nếu cần user điền tay. Giữ raw/history, không nối `ten` hoặc tạo field alias. Không mở rộng #42; `cccd_khac` trong extraction không chứng minh hỗ trợ đa giấy tờ end-to-end.
- Open question: catalog đầy đủ sẽ chốt key/kiểu/format/nhóm/cardinality/DB-wire-output còn thiếu và xung đột portal với trường đã loại. Đây là công việc refinement của issue, không yêu cầu owner chọn schema ngay lúc ghi nhận.
- Risk: high — mapping sai có thể gắn thông tin sai Người/Tài sản/Hồ sơ hoặc mất dữ liệu lưu/điền web. Ngoài AC, reviewer độc lập cần đối chiếu catalog với các consumer và thiết kế bảo toàn dữ liệu trước cutover.
- Identity: `next_id: 41` từ `tickets.py status _bmad-output/backlog` ngày 19/10/2026. Loose backlog theo waiver hiện có; active initiative để unset, không setup/install/config. Slice Case đã BUILT và review sạch; slice Nam Định preparation implement/verify cô lập và **review độc lập CLEAN**, owner đã giao commit. Toàn #41 giữ `refined:false`; không push.

### Metadata Case BUILT — chưa hoàn thành toàn #41; gate mẫu ĐÓNG

- Owner làm rõ: **“người được gán chủ đất trong diagram”**; nguồn là lựa chọn
  Chủ `ownPositions` đã lưu, tên snapshot Stage theo ID, không tự suy từ
  GCN/Bên A/người chết hoặc slot owner. Không Diagram là null.
- Phạm vi hiện tại: bảy scalar công chứng/văn bản và `chudat` theo entities
  §9.4. Person/Asset/parties chưa canonical cutover trong slice này; không
  set `refined:true`, built toàn #41 hoặc mở gate mẫu từ kết quả Case.
- Verification Case đã chạy: DOCX tổng hợp → registry/DB tạm → fresh reopen →
  form builder → Playwright preSave trang local; save Diagram/fresh session
  kiểm tên chủ đất theo assignment. Không nghiệm thu portal thật/corpus owner.
- Quick code sạch sau sửa queue read không persist override; chỉ record thực
  sự prepare sau selection/duplicate/chunk filters mới lưu nhân sự; fix được
  Quick độc lập chấp nhận. Tài liệu cuối hoàn tất 19/10/2026; chưa
  commit/push trước khi parent duyệt và cho phép.
- Catalog, contract và regression bền vững ở References đủ dùng trong clone
  mới. Plan/proof tạm `_bmad-output/tmp/issue-41-case-fields/` chỉ là evidence
  local **tùy chọn**, không là dependency hay nguồn chuẩn bắt buộc.

### Nam Định preparation — implement/verify 20/10/2026, review độc lập CLEAN

- Bỏ phí/ghi chú khỏi builder, selector và fill order; caller mang giá trị cũ vẫn không điền hoặc clear default. Status policy Đã công chứng được enforce ở consumer và verify, không canonical fact.
- Gỡ prime-Lưu/retype/flag và mọi caller/test obsolete. FreeSolo input+blur, remote/status chọn role option đúng label; không Enter/native submit, không generic website-submit suppression.
- File nguồn kỹ thuật vào actual preSave qua input attachment; verify selection filename; lỗi/thiếu source hoặc remote option là partial, không đoán metadata/POST/backend.
- Verification actual `prepare_manifest → _prepare_record` trên Chromium mới/form MUI-like kiểm soát và SQLite tạm: 0 submit/Save-click/Enter/skipped-field events; file DOM và file-change state đúng; status DACONGCHUNG; nguồn/Case/queue ngoài selection giữ nguyên. Upload scoped **42 passed**, sidecar workflow **60 passed**; warnings openpyxl hiện có.
- Permanent regression: `upload_lab/tests/test_namdinh_preparation.py`; Case selection/source proof `upload_lab/tests/test_case_fields.py`. Plan/evidence tùy chọn `_bmad-output/tmp/namdinh-preparation/`; giới hạn và behavior bền vững tại SOT §8. Không portal thật writes/credentials/corpus/production DB; không đóng #41 hoặc mở gate mẫu.
- Reviewer chạy lại **42 pass, không skip + 60 pass**, xác nhận controlled counters/files/persistence và scope 13 paths. Sau review harden permanent consumer smoke với filename decoy hiển thị khi thiếu source: file DOM rỗng, filler/verify false, status partial; affected suite **5 passed, không skip, 32.49s**. Không đổi runtime sau review; không nghiệm thu portal thật/packaged, build/dist chưa tái sinh.

### Owner 20/10/2026 — pháp nhân, cụm trường phụ và quan hệ

- **Đề xuất cũ bị bác (hẹp):** việc đưa pháp nhân vào Người bị owner bác,
  **không phải quyết định đã chấp nhận**; lý do pháp nhân không phải thể nhân,
  trường chưa đồng nhất, ép vào Person sẽ phân loại sai/trộn nghĩa. Mô hình
  parties rộng hoặc quan hệ đơn giản trước đây **chưa được chấp nhận**, không
  dùng làm tiền đề, nhưng owner **không bác mọi khái niệm parties/ordered
  participation**; quan hệ nhiều người/nhiều tài sản là bài toán riêng, cần làm
  kỹ, chưa chọn model/cardinality/schema.
- **Pháp nhân:** owner chốt trước đó **“pháp nhân để user nhập tay”**; giữ
  nguyên quote như lịch sử, policy chung có ngoại lệ ngân hàng thế chấp **app
  tự lấy** ở đáp án cuối. Không Person; bảng riêng tương lai **chưa duyệt schema/build**.
  Phạm vi ba đối tượng hiện tại không đổi; bảng pháp nhân tương lai là hướng
  owner cho phép. Hồ sơ thế chấp là mặc định có pháp nhân, loại khác ít xảy ra;
  sự có mặt đó không đồng nghĩa đã biết hoặc được tự điền ngân hàng/chi nhánh/
  người đại diện/default party; chỉ dùng dữ kiện nguồn nêu rõ. R05 alias và D04
  lời phức tạp có lựa chọn nhập/sửa tay riêng bên dưới; không fallback mọi gap.
- **Cụm trường phụ website:** owner cho phép **có điều kiện** thêm một trường
  giữ cả cụm khi cụm phức tạp, không lặp lại và thuộc một ô nhập của một website
  cụ thể. Không phải quyết định biến ba editor `nguoi_yeu_cau`/`duong_su`/
  `taisan` hoặc mọi ô web thành block/trường phụ. Khi chọn cụm phải xác định
  website/phạm vi ô/nghĩa/lý do/kiểu/provenance; chỉ hỏi owner khi có quyết định
  nghiệp vụ thực sự chưa rõ, chi tiết kỹ thuật do implementation sở hữu theo
  contract/rule đã duyệt. Ưu tiên tái dùng trường canonical Người/Tài sản/Hồ sơ
  đã biết; không dùng `ghiChu` chung hoặc JSON bag chung thay trường; raw capture
  chỉ là provenance, không thay trường nghiệp vụ; không tự đặt key/tên/kiểu/
  nhóm/storage; chỉ tự lấy ngân hàng theo ngoại lệ chốt bên dưới. Cụm có thể là
  trường riêng theo ô; phần tái dùng được vẫn map canonical, không mặc định coi
  là orphan. Không thêm canonical field cho projection requester hiện có.
- **Quan hệ Người–Tài sản–Hồ sơ:** chưa chọn model/cardinality/quan hệ/FK hoặc
  bảng nối. Owner mới chuyển D06+D07 sang **một #43 riêng**, làm ngay sau rõ
  các ô §7; thay chỉ đạo trước “refinement #41, không tạo ticket mới”. #41 nhận
  đáp án trước cutover phần quan hệ, không đòi #41 hoàn thành để #43 bắt đầu;
  #42 vẫn chỉ là nhiều giấy tờ/địa chỉ của một Người, không prerequisite.
- **Hiện trạng:** chưa có bảng/key canonical pháp nhân; Person/Asset/parties
  chưa canonical cutover. Ba editor vẫn là output trình bày, text projection
  persist qua JSON hiện có hợp lệ; không tự là normalized cutover #41.
  Raw/provenance giữ nguyên; #41 mở/`refined:false`, gate mẫu **ĐÓNG**.
- **Ma trận Nam Định — owner đã trả lời 20/10/2026:** [SOT §7](../specs/upload_lab/nam-dinh-website-sot.md#owner-review)
  giữ **W01–W17 + Tổng derived**, **25 đơn vị** (R7/D8/A10), source và giới hạn
  storage thực. Không còn 10 dòng đồng loạt chờ chọn:
  - **W05 đồng ý có điều kiện:** dựng loại portal từ tập tài sản, giữ ID1 Đất
    đai có tài sản/nhà; thiếu mẫu/rule không là loại không tồn tại. Tổ hợp nhiều
    loại vẫn thiếu quy tắc chọn một ô, không tự default/loại đầu/Khác.
  - **R05 đã chốt:** alias nếu cần user điền tay, không auto-fill/mở rộng chuẩn.
  - **R06/#43 Q1 đã trả lời:** requester Nam Định/Upload gồm cá nhân sống
    A/B/đại diện theo ủy quyền; loại người chết/CCV/nhân viên **chỉ khỏi output
    requester**, không xóa Person chết/Stage/Hồ sơ thừa kế/raw/snapshot/history.
    Cá nhân chuẩn, không prose/lookup/firstperson; ngân hàng **chỉ thế chấp** hiện
    cả cụm không Person, **BANKMODE đã chốt “app tự lấy”**, không user-paste-only.
  - **D04 đã chốt:** bỏ lời phức tạp khỏi tự động điền, user tự sửa; không block
    được duyệt hoặc manual fallback cho mọi unknown; nguồn giữ.
  - **D05/#43 Q2 đã trả lời:** ủy quyền A=người ủy quyền/B=người được ủy quyền;
    một bên không gán; hai nguồn trái nhau giữ conflict/xác nhận nhóm bị ảnh
    hưởng, không tự winner/thu hẹp requester. Chữ “nhận” không universal regex.
  - **D06+D07 → #43:** 16ca/membership/roles/thứ tự/scope đủ đáp án Q1/Q2/
    BANKMODE, bàn giao #41; model/cardinality/schema quan hệ vẫn chưa chọn.
  - **D08 đã trả lời theo R06**, không residual prose block, không hỏi lại.
  - **A09 đã chốt A**, không residual field; [SOT §7.5.1](../specs/upload_lab/nam-dinh-website-sot.md)
    lưu bảng trường thực/ví dụ; raw/history retained, output chỉ canonical/
    placeholder, không auto-fill notes.
  - **A10 đã duyệt** nhận diện + nguồn, pending structured xe/sổ tiết kiệm/
    bảo hiểm; #29 deferred, không áp để loại đất có tài sản W05.
- **Đã chốt 20/10/2026 — chỉ placeholder và trường tĩnh:** owner chốt
  “chỉ dùng placeholder và trường tĩnh, tiếp tục”. Không mở trường tầng 2
  động/tính toán, text canonical persisted từ suy ra, engine công thức hoặc
  framework điều kiện/cấu hình; không có scope trường động mới và không tạo
  technical approval gate mới. Đề xuất hai tầng trước đây chỉ là **lịch sử
  chưa triển khai**, không phải định hướng hiện hành. Quyền có điều kiện trước
  đó cho cụm **text tĩnh** đã duyệt khác **vẫn giữ** (dữ kiện tĩnh có nguồn,
  không phải tầng động); **A09 đã chốt A** không residual field. Dữ kiện nguồn tĩnh tách khỏi
  định dạng output/placeholder; block token do code Word định nghĩa, alias cũ,
  formatter và mẫu đang hỗ trợ giữ nguyên, không bị xóa/sửa bởi quyết định này.
- **Lịch sử docs/ticket trước FINAL:** independent review CLEAN/Ticket draft
  PASS thuộc delta cũ BANKMODE còn mở, không là bằng chứng cho delta tự lấy này.
  Docs-only ở mốc trước không freeze runtime slice owner giao liên tục; #41
  `refined:false`/mở, gate mẫu **ĐÓNG**, #42 độc lập.
- **Đáp án #43 FINAL 20/10/2026:** [decision “Đáp án #43”](../decisions/decision-owner-upload-field-standardization-20261019.md)
  giữ nguyên văn owner cũ và bổ sung **“app tự lấy”**. Q1/Q2/BANKMODE đủ đáp án,
  không còn bank owner gate; đủ16ca/kết luận bảo toàn, AC4 bàn giao decision/
  spec/#41 đã có. #43 phân tích done/refined:true/hitl:true sau fresh CLEAN/Ticket PASS.
  Không fake Person/persisted legal field/bảng/blanket raw editor; toàn model
  quan hệ/normalized cutover #41 chưa hoàn tất, không #42/JSON/FK gate mới.
  Latest-auto independent review CLEAN; bounded proof đã có, không claim toàn #41 BUILT.
  Requester không cần tag A/B đã gán: cá nhân sống tham gia văn bản một bên/
  đại diện theo ủy quyền vẫn vào khi nhóm không gán hoặc conflict.

### Kế hoạch slice requester/ngân hàng — FINAL, ghi trước sửa code

Kế hoạch có giới hạn ở [#43 plan §6.1](spike-case-people-assets-relationships-plan.md):
nguồn → `web_form.nguoi_yeu_cau` có sẵn → payload JSON → queue reader/builder →
editor requester Nam Định; không key canonical/entity/bảng mới. Full requester
giữ mọi cá nhân sống thực sự tham gia/đại diện theo nguồn bằng block dữ kiện
chuẩn, không chỉ ngân hàng/ưu tiên B hoặc A/B-tag prerequisite. Chỉ thế chấp,
app lấy toàn cụm ngân hàng/chi nhánh/định danh/địa chỉ/đại diện/căn cứ ủy quyền
có nguồn tại vị trí nguồn; không lặp đại diện đã trong cụm. Cá nhân khác không
alias auto/job/kinship/role prose; giữ raw/person arrays/provenance/history.
Không nuốt tài sản/giao dịch/thời hạn nghiệp vụ. Queue không ghi đè requester
đầy đủ bằng projection stale ngân hàng-only/firstperson.

Proof tổng hợp/cô lập đã chạy source parser → payload JSON save → fresh registry/
queue/form builder → actual local contenteditable `_fill_editor`, không portal/
network/Save/upload/production DB. Giữ logged-in Chrome không chạm.
W05/A09 và unrelated pending/deferred vẫn nguyên; fresh independent review CLEAN.

### Evidence bounded bank-auto implementation

- Source version `2026-10-20-requester-bank-projection`; existing
  `web_form.nguoi_yeu_cau` đi hết JSON persistence/queue/reader/editor, không
  new businesskey/entity/schema. Whole bank nguồn chỉ mortgage; natural facts
  độc lập tag A/B, staff/dead không requester, rep trong bank không lặp.
- Before: controlled baseline bỏ A1/A2 và tên/địa chỉ ngân hàng, chỉ representative.
  After: tất cả A1/A2 chuẩn rồi nguyên bankblock theo nguồn, Save=0/Submit=0,
  URL about:blank. Raw/person arrays/history và eight Case keys giữ nghĩa.
  Local evidence `_bmad-output/tmp/issue-43-bank-smoke-result.json`; baseline
  và expectations cạnh file đó, không nguồn khách hoặc claim portal thật.
- Các hồi quy biên ngân hàng/identity được ghi ở plan #43; projection này
  không phải canonical Person/Asset/parties cutover toàn #41; gate mẫu ĐÓNG.
- Final isolated five-suite sau xóa đúng hai test hardcoded fixture owner-local:
  **250 passed,0 skipped,28 subtests passed** gồm cả5 browsercases, process-only
  CASE_FIELDS_CHROMIUM trỏ browser headless riêng; không Chrome đã đăng nhập.
- Lượt full trước không gọi wholly synthetic: khả năng fixture access là
  **[INFERENCE] từ skip count**; không probe/read lại, không claim nội dung
  hoặc broader corpus coverage. Mọi fixture giữ nguyên; chỉ hai test method
  đã bỏ theo parent. Chi tiết privacy-safe/proof lưu bền SOT §6.1.
- Namesake chết thiếu DOB không loại living knownDOB; raw staff giữ nhưng
  requester loại. Không claim skipped pass/portal thật/sample accuracy.

### Slice A07 — mapping `nguon_goc` (kế hoạch giữ lịch sử + landed/verified)

Authority đã có ở contract asset_row/wire và `Property.nguon_goc`; source
parcel lõi đã phát `nguon_goc`, normalization/writer/snapshot/readback/Word
đã có đích. DOCX adapter bỏ sót mapping nên hoàn thiện
`ASSET_FIELD_SOURCES["nguon_goc"] = "nguon_goc"` là cutover kỹ thuật được
giao, không key/schema/nghiệp vụ mới hoặc owner gate. Audit nhánh group thực
tế chưa phát origin: source group phải giữ các `nguon_goc` đã có của parcel
và technical `nguon_goc_values`, rồi GROUP mapper mới được đọc. Nhiều origin
khác nhau dùng cơ chế ambiguous hiện có (normalized null+refs), không lấy
first/broadcast; thiếu giữ thiếu. Không lấy nguồn gốc từ note/title.

Phạm vi code chỉ DOCX adapter và regression trong `test_docx_word_first.py`:
synthetic DOCX hai tài sản có nguồn gốc khác nhau → intake suggestion với
source refs → workspace asset → save/fresh reopen → Word/property output.
Giữ từng nguồn gốc đúng tài sản, không broadcast chung/nhét ghi chú; không
thay bank parser/uploader. Main sở hữu SOT/#41docs/design/review; fast worker
sở hữu adapter+focused test. Chỉ kiểm cô lập sau land; không hồ sơ thật/
corpus/production DB/browser portal, #41/gate mẫu không đổi.

**A07 landed/verified 20/10/2026:** parser group chỉ lộ `nguon_goc`/
`nguon_goc_values` từ parcel observation thật (multi-value path cùng thửa giữ
mọi lần thấy); adapter map cả asset/group, multi-value dùng ambiguous hiện có;
label nguồn gốc có sẵn. Hai real-DOCX regression phủ đủ hai mode: cùng thửa
A/C → `normalized null`+2refs+`intake.ambiguous`, thửa B giữ, thửa thiếu giữ
thiếu; group C/D → `normalized null`+refs C,D+warning, không broadcast. Cả hai
đi suggestion→workspace→fresh DB reopen→Property→Word. Focused suite **5
passed,61 deselected**; isolated smoke `a07-origin-smoke-result.json` PASS.
Parser hash `583b27e488d46b076bb8c59f00dd0b16acf545fc0bcc141586d9f45487fe602a`,
adapter `6126ae5c242ef4cc36c759c7ef8deba409b1e805f2bd517a9c71cd99ebcaa32e`.
Không new key/schema; đây chỉ slice A07, không đóng toàn #41; gate mẫu ĐÓNG.
Independent review 20/10/2026 đọc diff/consumer và chấp nhận evidence báo cáo
(không rerun test/browser); finalizer chạy focused **5 passed,61 deselected**,
full `test_docx_word_first.py` **66 passed** và isolated smoke trước commit;
không phát hiện silent loss/broadcast. Commit cùng ngày trong slice A07, không
push.

### Slice W09-R01 — giới tính Người từ danh xưng trong DOCX intake

Authority: canonical `Nam`/`Nữ`/null ở Customer/person_row/Word đã có; chỉ
thiếu đường DOCX intake. Mapping mới dùng **duy nhất** danh xưng rõ trong
nguồn: lõi phát `Ông`/`Bà` (bảng in `Anh`/`Chị` cũng đã chuẩn hoá về hai giá
trị này), `norm_gender` nhận thêm `ong`→Nam, `ba`→Nữ; adapter emit riêng
`person.gioi_tinh` với span đúng token danh xưng đứng trước họ tên (hỗ trợ
NFC/NFD, `Anh`/`Chị` trong bảng không `raw_text`), không qua `map_fields`.
Danh xưng trung tính (`Ông/bà`) hoặc thiếu → **không emit**, giữ null; không
suy từ tên/`Thị`/năm sinh/ID. `raw.nguoi_chet` không do adapter này phát —
ngoài phạm vi slice, không claim đã map người chết.

Regression real-DOCX: hai bên Ông/Bà → Nam/Nữ + refs đúng token, họ tên không
đổi; `Ông/bà` → riêng người đó null, người Bà còn lại Nữ; `Đại diện: Ông` →
Nam; dòng bảng `Ông`/`Chị` → Nam/Nữ với source ref `Ông`/`Chị`. Cả chuỗi
suggestion→workspace→fresh DB reopen→Customer→WordPerson.gender_normalized
được assert; test giữ gender vắng = null thay vì default `_person_row`.
Focused 4 test mới **4 passed,66 deselected**; full
`test_docx_word_first.py` **70 passed**; isolated synthetic smoke
`_bmad-output/tmp/w09-gender-smoke-result.json` PASS (4 case, `failures: []`).
Không new key/schema/alias; đây chỉ slice W09-R01 DOCX intake, không claim toàn
bộ người/Excel/OCR hoặc đóng #41; gate mẫu ĐÓNG.

### Slice W11-A08 — hình thức sử dụng từ nhãn nguồn DOCX

Authority đã có ở `asset_row.hinh_thuc_su_dung`/`Property.hinh_thuc_su_dung`,
writer/readback/Word. Adapter map **chỉ** giá trị sau label `Hình thức sử dụng:`
trong đúng cửa sổ tài sản; không map blob `phan_ghi_them`, `Ghi chú`, title
hoặc cửa sổ tài sản khác. Parcel dùng cửa sổ bắt đầu tại thửa hiện tại để
không mượn label của thửa trước; group giữ cửa sổ nhóm, context không có thửa
dùng đúng span nguồn của khối `tai_san_block` đã bóc (định vị duy nhất; không
định vị được thì bỏ, không đoán). Label thiếu
hoặc ô chỉ có header → absent; lặp cùng giá trị → một value giữ đủ refs; nhiều
label rõ với giá trị khác → `normalized null`+all refs+`intake.ambiguous`.
Một label có giá trị ghép `;` được giữ nguyên đến nhãn kế/endline, không tự
tách thành hai form; hai label `Hình thức sử dụng:` rõ trên cùng dòng vẫn là
hai quan sát và đi vào ambiguous. Prose kiểu "theo Giấy chứng nhận …" chỉ bị
cắt khi có nhãn kế thật kèm `:`. Label NFC/NFD, bullet/comma prefix trong tài
sản được nhận; raw/`phan_ghi_them`/history giữ nguyên; phần dư A09 không đổi,
không claim scalar mới.

Real-DOCX regression phủ: hai thửa khác form (không broadcast, Ghi chú không
bị lấy), thửa thiếu form vẫn absent và label ngoài tài sản không bị mượn,
label lặp trùng vs xung đột, NFD + bullet/comma prefix, header rồi prose dòng
sau không bị lấy, prose tail không bị cắt, semicolon compound giữ một value,
hai label cùng dòng → ambiguous. Context không có thửa dùng đúng span khối
`tai_san_block` nên form trước serial trong khối vẫn đọc được, form sau
`Điều 2` không bị mượn; parcel/group cũng giao cửa sổ form với span khối thật
nên thửa/nhóm cuối không đọc label sau `Điều 2`; parcel không có nhãn thửa
cũng giao cửa sổ mặc định với span khối nên label ngoài block vẫn absent.
Roundtrip
suggestion→workspace→fresh reopen (session mới) assert Stage+Property+Word
cho cả value, absent và conflict. Focused 10 test mới **10 passed,70
deselected**; full `test_docx_word_first.py` **80 passed**; isolated synthetic
smoke `_bmad-output/tmp/a08-form-smoke-result.json` sha
`51b8095f319dea3bc3b30fe87c9afe0fe177a3dab12056f69093cece515976da`,
PASS (`failures: []`, 11 case explicit/absent/conflict/duplicate/NFD/compound/
same_line/context/last_parcel/last_group/no_thua). Không new key/schema; đây chỉ slice
W11-A08 DOCX intake, #41 vẫn mở/gate mẫu ĐÓNG.

### Slice W05 — hỗn hợp thửa có nhà + thửa trống, owner chốt 20/10/2026

Owner trả lời **1** cho câu hỏi cùng Hồ sơ có một thửa đất có nhà + một thửa
đất trống: chọn **Đất đai có tài sản** khi có ít nhất một tài sản gắn liền đất
có bằng chứng, thay vì bắt người dùng tự chọn. Phạm vi chỉ tổ hợp đất-nhà/đất-
trống; không thành ưu tiên phổ quát trên xe/sổ tiết kiệm/cổ phần/… và không
tạo field/catalog nhà mới. Bằng chứng dùng rule chi tiết hiện có (`Nhà ở:`,
`Diện tích xây dựng`, `Kết cấu`, ...); heading GCN “quyền sử dụng đất, quyền
sở hữu nhà ở và tài sản khác gắn liền…” một mình không tính; cụm phủ định
`Không có nhà ở:`/`Nhà ở: không có`/`Không có tài sản gắn liền với đất` không
thành positive.

Thay đổi code tối thiểu: `guess_loai_tai_san` hiện đã trả ID 1 cho mọi blob đất
có chi tiết gắn liền, nên mixed hai thứ tự đã đúng; chỉ bổ sung strip cụm phủ
định **trong cùng clause** trước khi khớp detail pattern, dừng ở dấu phẩy/chấm
phẩy/xuống dòng để không xóa positive của thửa khác. Negative của một thửa
không được ăn positive `Nhà ở:`/`Công trình xây dựng:`/`Diện tích xây dựng:`
của thửa kế bên. Không đổi canonical key/schema/UI/catalog, raw/history/
source_refs và W11-A10 giữ nguyên.

Real-DOCX regression: mixed house-first, house-last, negated-other-then-house,
negated-value-then-construction và house-then-negated-other → payload `loai_tai_san = Đất đai có tài sản` →
`save_output_json` → JSON reread → `build_upload_form_data` cùng value;
heading-only và các dạng phủ định (gồm `Nhà ở: không có; Diện tích xây dựng:
không có; Kết cấu: không có`) → Đất đai không có tài sản. Selector ID1 được
fast namdinh-login-session xác nhận bằng actual Chromium controlled DOM; không
giữ mock echo test riêng. `upload_lab/tests/test_upload_lab_extract_contract.py`:
**200 passed,19 subtests**; `test_playwright_uploader.py`: **26 passed**
(không đổi file uploader). Isolated smoke
`_bmad-output/tmp/a07-w05-mixed-kind-smoke.json` sha
`35cf26dadbd26c1700f8bc8b7399f6ba733439d8143600cd57480b8aaaba3816`,
PASS (`failures: []`, 9 case house_first/house_last/heading_only/
negated_house_value/negated_all_details/negated_then_house/
negated_value_then_construction/house_then_negated/negated_house_only). Fast
namdinh controlled Chromium artifact `_bmad-output/tmp/w05-asset-kind-browser-after.json`
(run `2bfcf3df`, parser `067cfe61…`) prepared **9/9**, `errors=[]`, actual
selected optionId **1** for mixed/positive both orders and **2** for
heading/bare/negated; Save0/Submit0/Enter0, local `w05.invalid/create` only.
#41 vẫn mở/gate mẫu ĐÓNG; không đọc mẫu/corpus.

### Slice A09-A — không trường residual; render canonical asset

Owner trả lời **1a/A**: không tạo field residual business/catch-all. Asset editor
render các trường canonical/placeholder đã duyệt; `phan_ghi_them`/`o_tho`/raw
stay as source/provenance and are not auto-filled. Current upload chain confirmed
`web_form.tai_san` raw block was copied to editor; `web_form.tai_san` remains the
raw/source block for DOCX intake/bench compatibility, while
`build_upload_form_data` now renders canonical parcel/group projections: approved
asset fields, source total `dien_tich` only when unambiguous (no sum/first-wins),
ordered land rows including blank positions, explicit `Hình thức sử dụng` from
parser technical field, no flat term when observations conflict, no notes/residual.
Unsupported/no structured asset → empty editor text (raw flags/`tai_san_chua_ho_tro`
retained), no raw fallback. A09 conditional static-field permission is retired;
bank/W05/static policies unaffected. Raw/history/aliases/Word tokens preserved.

Real-DOCX tests: canonical fields + Ghi chú/residual → editor has serial/thửa/total/
form/land type, no note; unsupported savings → empty editor + recognition flag;
ambiguous total/flat term omitted; equal total/detail retained; group-only asset
with blank/mixed row retained; notes blob cannot become form;
`upload_lab/tests/test_upload_lab_extract_contract.py`: **207 passed,19 subtests**;
`test_playwright_uploader.py`: **26 passed**.
Actual controlled Chromium source→save_output_json→fresh isolated SQLite→builder→
`_fill_editor` run on current parser `27d117ba…`, renderer `d9a8d8c6…`, uploader
`f1aa3ea4…`: 8/8 cases PASS (canonical/note excluded, conflicting, detail, grouped,
equal total/detail, multiline, same-line, mixed blank row), Save/Submit/Enter 0;
artifact `_bmad-output/tmp/final-a09-verify/final-a09-verification.json` sha
`5cb2a0ee39a2c0c38d0e558c72eab1b7c5de07c60968c550247993f26a637ef8`, prewritten expectations sha `adae671f79ab1a74038dd532414b61d7832b5ec0a1546cb8f712a0b78e8773dd`. One limitation recorded: one
mixed-group browser `innerText` repeated a blank line; semantic normalized match
true, exact raw string false. Not byte-exact layout proof.

### Slice deceased Person intake

DOCX adapter now emits deceased Person suggestions from `raw.nguoi_chet`:
`ho_ten/gioi_tinh/ngay_sinh/ngay_chet/dia_chi` plus document fields
`loai_giay_to/ngay_cap/noi_cap` only when source doctype explicitly says Trích lục
khai tử. Số TLKT is **not** copied into `so_giay_to`/Customer unique because
writer find-or-create by number can merge unrelated deceased; raw retains it.
No requester/owner/Diagram assignment; same-name living deceased filter now
requires positive deceased birth evidence, so living namesake with unknown
deceased birth is retained; no name-only merge, no #42.

Real-DOCX tests: TLKT full fields + source refs; living namesake/death unknown
birth; missing doctype leaves document fields absent while date/gender/name/address
still map; Stage/fresh DB session/Customer/Word. `test_docx_word_first.py`:
**82 passed**. The Word regression now builds an actual synthetic DOCX from
**explicit fixed tokens written before mapping/output** (`[Người 3 - ...]`,
source-confirmed Stage slot 3), replaces them with real `replace_in_doc`, and
asserts every expected source field/name/date/type/place and no leftover tokens;
it does not select tokens from mapping values. Focused deceased+full notary pass;
smoke `_bmad-output/tmp/deceased-person-smoke.json` sha
`eea7e5eb6aedfe5d2fbd84a85fa9ffe8f0fba77bfded0a5817781341f23e13c9` PASS
(mapped death/type/issuer, no TLKT identity, raw retained, not requester).

### Người chết — owner 21/10/2026 chốt sáu câu (trước runtime)

1. Nơi chết/cư trú cuối dùng một `dia_chi` Người hiện có; không thêm trường
   hoặc tự chọn giá trị mâu thuẫn.
2. `Giấy chứng tử (bản sao)` quy về `Giấy chứng tử`; chỉ ba loại cùng
   `Trích lục khai tử` và `Trích lục khai tử (bản sao)`.
3. Giữ cơ quan xã/phường/thị trấn theo nguồn tại ngày cấp chính giấy,
   không ép xã, thay bằng hiện hành hoặc bù lịch sử chưa xác nhận.
4. **Không đề xuất bổ sung, không tự ghép giữa văn bản**, kể cả cùng bộ;
   không mượn trường thiếu, matching người hoặc lấy bản đầy nhất/mới nhất.
5. **Không gợi ý** trường sinh/chết/giấy tờ Người từ `Đơn xin xác nhận`,
   kể cả qua normalized/inferred.
6. Thiếu ngày chết là không có thông tin (`null`/rỗng), có trường hợp lệ nào
   điền trường đó; không chặn Người vì thiếu ngày/giấy, không tự coi còn sống,
   tạo ngày giả/01/01, Boolean hoặc status mới.

Số giấy giữ nguyên giá trị và nhãn ngoài số; không đổi raw/history/liên kết
Case/ID, logic câu Word/trường tĩnh. Trong cùng văn bản, địa chỉ chung và lần
nhắc rõ cùng người giữ đúng phạm vi khi không mâu thuẫn, không suy chung giấy.
Không duyệt model #42, khóa số toàn cục, migration hoặc ghép liên module.

**Trạng thái trước khi owner “trien khai” — lịch sử, đã thay bởi mục dưới:**
**BUSINESS CHỐT, runtime TẠM DỪNG:** lượt này chỉ docs, không code/test/mẫu mới.
Slice deceased intake và proof cũ bên trên giữ đúng phạm vi lịch sử, không
nghiệm thu sáu quy tắc mới. Grammar ba loại/số freeform, derive thiếu ngày
và đường số TLKT raw-only do UNIQUE/lookup khi đó vẫn là khoảng trống triển khai.
#41 vẫn OPEN/`refined:false`, chưa cutover Person/Asset/parties hoặc nghiệm
thu toàn bộ; gate chung ĐÓNG ngoài ngoại lệ đọc hẹp đã ghi, không mở lô mới.

### Runtime Người chết — owner “trien khai”, 21/10/2026

**Owner đã mở runtime hẹp:** sáu quy tắc và giấy tờ
Người dùng chung với khai tử/chứng tử, thay tạm dừng chỉ trong workstream này.
Thực hiện parser/normalization/intake, lưu số thật với identity `Customer.id`
không auto ghép theo số, migration SQLite giữ IDs/FKs/snapshot/history và
consumer/Word. Hồi quy và DOCX → intake → Stage → SQLite riêng mở lại → Word
bằng dữ kiện tổng hợp được phép. Tại thời điểm mở runtime, chưa claim
built/cutover hoặc proof mới; kết quả proof ở đoạn dưới.
Không mẫu thật/corpus/prodDB/portal/Chrome owner; không mở #42/A04/quan hệ,
field/model mới hoặc gate chung. #41 vẫn OPEN/`refined:false`.

**BUILT bounded, actual proof PASS (21/10):** số giấy freeform qua
lõi → intake → writer, không còn raw-only; Customer.id/same-case row_id
giữ identity, số index không UNIQUE. Bootstrap thay migration nullable cũ
bằng migration số giấy idempotent/atomic giữ schema objects/FKs/history.
Snapshot giữ loại/issuer/nhãn/ngày chính hồ sơ kể cả null, không borrow master.
Không cross-file OCR enrichment/fuzzy-number merge; legacy form bỏ dedupe
theo số và cờ guard đã hết dùng. Word dùng ngữ cảnh loại/nhãn khi thiếu ngày.

Hồi quy đã chạy bằng `notary_v2/venv/Scripts/python.exe`: bảy file Notary
**297 passed, 2 subtests**; shared core **41 passed, 6 subtests**. Sau sửa hai
ranh parser (câu kể gián tiếp/tên rút gọn chính xác) và assertion cũ bắt giấy
cho năm chết: Upload generated class **158 passed, 2 subtests**, tập death
runtime mới **20 passed**. Cảnh báo còn lại là deprecation SQLite/openpyxl/
Starlette, không claim đã sửa. Lượt global-env trước thiếu jsonschema/lệch
Starlette được ghi giới hạn rồi dùng venv hiện có, không sửa môi trường chung.

Evidence số liệu/attempts: `../tmp/death-runtime-regressions.json`; actual proof
implementer-run `../tmp/death-runtime-inventory/final_summary.json` (chi tiết
`final_result.json`; 164 checks, fresh+migrated DB, exact Word; UI legacy giới
hạn programmatic DOM, không nút Add/search-picker đầy đủ). Không claim
independent review, Electron packaged,
national coverage hoặc toàn #41; mẫu owner/corpus/prodDB/provider/portal không chạy.

### Lịch sử owner “chốt” identity — 21/10/2026, ĐÃ BỊ THAY THẾ

**Superseded:** policy gợi ý/liên kết không chặn bên dưới thay toàn bộ yêu
cầu UNIQUE, prerequisite index/migration và nhận định “gap bảo vệ trùng CCCD”
trong mục lịch sử này; không dùng nó làm AC hiện hành.

Quyết định bổ sung trong phạm vi #41, không tạo issue mới hoặc mở #42:
một bảng Người, `Customer.id` ổn định; chết vẫn là chính Người. CCCD theo
loại giấy tờ xác nhận đáng tin cậy phải UNIQUE, số khai tử/chứng tử không
UNIQUE toàn cục. Không phân loại bằng ngày chết null/ngày cấp/độ dài số.
CCCD xác nhận đã tồn tại thì không tạo ID mới, không tự ghi đè/merge;
user chọn rõ Người hiện có không cho phép cross-document SUGGEST/JOIN.

**Gap OPEN:** `f6d53b5` bỏ global UNIQUE/merge theo số nhưng chưa bảo vệ
trùng CCCD. Proof/tests ở trên giữ giá trị historical bounded, không chứng
minh hoàn tất identity/#41. Runtime một Người/death subset giữ nguyên.
Quy tắc mới thay ý định “mọi số giấy không UNIQUE”, không thay current fact.

**Điều kiện thiết kế/triển khai tương lai, chưa được giao trong lượt “chốt”:**
duyệt lưu bền loại giấy tờ canonical trước chọn index/migration; loại chỉ ở
snapshot/derived master chưa đủ DB enforce. Chưa chọn tên field/key, kiểu,
model vật lý; chưa triển khai conditional index. Audit trùng/migration tương
lai không tự merge/xóa IDs, giữ Case links, raw/history local và snapshot
có key null. Không audit production DB, đọc mẫu/corpus hoặc chạy test mới.
Ba loại canonical và sáu quy tắc owner giữ nguyên. #41 OPEN/`refined:false`,
gate mẫu ĐÓNG; #42 độc lập/chưa chọn model, không mở entity/broad flow mới.

### Policy mới của owner — 21/10/2026, docs + issue, không triển khai

CCCD có trong DB chỉ gợi ý ID cũ. User chọn → dòng input liên kết ID cũ,
gợi ý biến mất. Sai khác không chặn, ghi “thông tin liên kết” để user
xem/xóa/sửa bất cứ lúc nào. Không chọn/bỏ qua → ID mới; không auto merge.
Đề xuất UNIQUE/chặn CCCD, chặn khác tên hoặc xác nhận thêm vì trùng tên
đã bị bác bỏ/thay thế; không còn prerequisite lưu loại để làm unique index.

[#44](story-person-cccd-suggestion-link.md) là issue riêng cho interaction
và lifecycle gợi ý bị bỏ qua chưa chốt, không nhét vào #42. Shape/key/nơi
lưu/cardinality thông tin liên kết chưa chọn, không bịa field/model hoặc
field thắng/ghi đè master. Runtime `f6d53b5` cho số trùng/cập nhật master qua
ID explicit chưa phải đầy đủ UX mới; proof lịch sử giữ đúng phạm vi.
Một bảng Người/ID ổn định, death subset, raw/history/Case links/snapshot null
giữ nguyên. #41 OPEN/`refined:false`, gate mẫu ĐÓNG; #42 độc lập.
Policy mọi task: không tự thêm gate/đổi hành vi chưa báo và owner duyệt;
ưu tiên tối thiểu 80% hơn 90% cộng 10 thao tác, không đánh đổi tính đúng/nguồn.
Blocker hiện có chưa kiểm kê/xác minh; không tự audit/gỡ safeguard hoặc mở
thêm issue audit. Lượt này không code/schema/tests/DB/mẫu/production.
