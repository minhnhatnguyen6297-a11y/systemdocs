# Kế hoạch nối UI Electron với nghiệp vụ thật (prototype tham khảo)

**Trạng thái:** bản kế hoạch để review, chưa phải phê duyệt production

**Ngày:** 23/09/2026

**Goal:** MIN-56 · **Nguồn UX:** MIN-88 · **Nhánh khảo sát:** `consolidate/monorepo`

## 1. Đích và ranh giới

Xây từng lát cắt nghiệp vụ trên renderer Electron hiện có, dùng prototype chỉ
làm tham khảo UX có thể thay đổi, rồi nối với engine Python thật. Đây là bản
phân rã hành vi/action để owner sửa workflow trước khi chốt contract; không
phải kế hoạch chuyển nguyên HTML hoặc bố cục prototype vào production. Bản này
bổ trợ `docs/architecture/ELECTRON_G1_PLAN.md`, không thay thế các gate G1. Giai đoạn
đầu dùng contract `desktopcommand.v1` trên
loopback **một máy**; kiểm chứng hai máy/LAN thuộc MIN-76. MIN-66 là review
merge-readiness, **không** phải cutover (`docs/product/MIN66_MERGE_READINESS_DRAFT.md:12-29`).
Không đổi engine nghiệp vụ sang Node, không đọc SQLite qua renderer,
không biến dữ liệu OCR/Zalo chưa xác nhận thành sự thật nghiệp vụ.

Prototype là tham chiếu UX có thể chỉnh, không phải source code production:
file HTML hiện dùng dữ liệu hư cấu và `localStorage`, không có API/file I/O thật
(xem `he-thong-cong-chung-prototype-demo1.html`:7,267-300,603-647). Kiểm tra
trạng thái MIN-88 trên Linear khi bắt đầu việc; owner có thể đổi màn hình/bố cục.
Từng lát cắt cần chốt workflow và hành động nghiệp vụ trước khi sửa spec/module.

Mốc khảo sát prototype: thư mục Open Design
`C:/Users/Toan Phat/AppData/Roaming/Open Design/namespaces/release-stable-win/data/projects/5efb3fcd-c093-4334-ba32-d5764ab9e97c/`.
Không khóa phiên bản HTML, màn hình hay bố cục; bản thiết kế có thể tiếp tục đổi
trong khi từng hành động nghiệp vụ được đặc tả và triển khai.

Quy trình cho **mỗi hành động**: owner sửa/chốt workflow UX → kiểm kê chính xác
backend đã có, có một phần hay chưa có → duyệt contract trong issue riêng → UI
Electron dùng Mock theo contract → tái sử dụng hoặc xây backend còn thiếu → thay
Mock bằng Real và kiểm chứng side effect thật. Mock và Real phải cùng request,
response, trạng thái và lỗi; không coi một nút hiển thị được là đã nối xong.

## 2. Kiến trúc nối UI

```text
Prototype (tham khảo trải nghiệm, không dùng code)
            ↓ owner chốt từng hành động nghiệp vụ
Electron renderer → preload `window.desktop.v1` → main IPC/command client
                                                → FastAPI sidecar loopback
                                                → adapter Python → engine/DB owner
```

Đường này đã tồn tại ở `shell/src/preload/preload.js:8`,
`shell/src/main/ipc.js:89`, `shell/src/main/command-client.js:74`,
`shell/sidecar/app.py:115`. Renderer hiện nằm chủ yếu trong
`shell/src/renderer/renderer.js`; upload view ở `:494`, notary view ở `:712`,
điều hướng ở `:1180`. Adapters tách sẵn ở
`shell/sidecar/upload_adapter.py` và `shell/sidecar/notary_adapter.py`.

Giữ dữ liệu hồ sơ, kết quả và job trong owner Python/sidecar theo contract;
renderer chỉ giữ state trình bày và bản nháp chưa gửi. Mọi action nghiệp vụ có
I/O phải đi qua command được allowlist, dùng `command_id` để chống lặp, hiển thị đúng
`waiting_user`/`partial`/`failed`, và không tự thực hiện Save/Finalize
(`contracts/desktop-command.md:22-29,47-85,136-144`). FileRef phải đúng máy sở
hữu file (`contracts/desktop-command.md:87-100`). `g1.module.v1` đã chốt nghĩa
provenance, unknown/null và quyền ghi (`contracts/g1-module-data.md:3,62-87`).

Mỗi khoảng trống cần contract mới hoặc thay đổi nghĩa contract hiện có phải
được đặc tả/duyệt trong issue riêng trước issue implement. Chỉ mở command mới
khi action thật sự cần nó; ưu tiên dùng engine/API và command đã có.

Hai ranh giới nghiệp vụ dễ bị nhầm khi nhìn UI: backend Notary hiện lưu
`InheritanceCase` với người chết, tài sản và loại văn bản `khai_nhan`/`thoa_thuan`
(`notary_v2/models.py:83-103`, `shell/sidecar/notary_adapter.py:278-302`). Nó
**không** lưu loại hồ sơ hai bên A/B của `NV2-02` (chuyển nhượng, tặng cho, cho
thuê, đặt cọc trong `he-thong-cong-chung-prototype-demo1.html:404`). Tương tự,
`upload.prepare` gọi
`prepare_manifest` để mở các tab Chromium điền thử và chờ người dùng review
(`shell/sidecar/upload_adapter.py:281-325`), **không** tạo/chỉnh PDF cho `UL-04`.
Những UI này phải được đánh dấu chưa có backend phù hợp, không ánh xạ giả vào
case thừa kế hay command portal.

## 3. Thứ tự lát cắt

| Lát cắt | Tham chiếu UX hiện tại (có thể đổi) | Nối vào hiện trạng | Hoàn tất khi |
|---|---|---|---|
| P0 — Chốt workflow từng hành động | Các màn hình prototype chỉ để gợi ý, không khóa 21 ID hay layout | Owner sửa luồng text theo nghiệp vụ thật; lập bảng action → backend đã có/có phần/chưa có → contract/fixture/issue. So với inventory G1 để không bỏ luồng cũ. | Mỗi action được phân loại theo **engine**, **bridge Electron** và **UI** riêng; owner duyệt workflow trước contract. |
| S0 — Shell và job thật | `SH-01`, `SH-02` | Shell đã có navigation, command/job thật; ánh xạ lại UX badge/tác vụ của prototype lên nguồn này. Chốt API trình bày chung cho hai view trước khi tách file, và xác minh từng control retry/cancel thực sự được backend hỗ trợ. | Đổi module không mất form/job/scroll; waiting user, retry/cancel nếu hỗ trợ, mất sidecar và version mismatch hiện đúng; không có fallback dữ liệu giả. |
| U1 — Nguồn và đối soát | `UL-01`–`UL-03` tham khảo | Dùng `upload.scan`, `upload.audit_excel` nhưng tách rõ: scan Word và audit Excel là hai luồng độc lập, audit chưa phải đối soát với portal. Bước review/edit kết quả trích xuất và chọn queue của G1 phải được kiểm kê/đặc tả riêng, chưa mặc định đã nối Electron (`docs/architecture/ELECTRON_G1_PLAN.md:70-75`). `upload.scan` qua shell chưa gọi `finalize_manifest` (`shell/sidecar/upload_adapter.py:87-120`, `upload_lab/batch_scan.py:517-526,827-833`); sửa điểm đứt này theo contract trước khi dùng kết quả scan cho U3. | Scan/audit trả kết quả đúng fixture; người dùng review/edit/chọn queue theo workflow đã duyệt; scan lưu manifest **file** của chính lượt quét để U3 dùng, không chọn nhầm run cũ. |
| U2 — Kiểm tra nguồn đính kèm | `UL-04` phần chọn/xem file | `upload.env_check` chỉ kiểm môi trường (`shell/sidecar/upload_adapter.py:178-190`); đọc metadata/preview file nguồn cần read-only adapter + contract được duyệt trước. File portal nhận hiện là đường dẫn `file_goc` của source (`upload_lab/playwright_uploader.py:807,2020-2023`). UI đổi thứ tự trang/xoay/xóa/tạo PDF chưa có pipeline production trong snapshot; tách spec/engine riêng, không gọi `upload.prepare` ở bước này. | Người dùng xem đúng file nguồn, nhận cảnh báo file thiếu/sai/không đọc được trước phiên portal; phần chỉnh PDF chưa có không xuất hiện như thao tác đã lưu; dry-run vẫn là mặc định. |
| U3 — Portal và kết quả | `UL-05`, `UL-06` tham khảo | Chỉ bắt đầu sau khi U1 tạo đúng manifest; `upload.prepare` hiện cần manifest file hoặc tự chọn run cũ (`shell/sidecar/upload_adapter.py:290-300`). Dùng các lệnh session/prepare/finish hiện có; thêm UI cho `upload.download_export` nếu workflow được owner duyệt. | Manifest đúng lượt quét → đăng nhập tay → điền thử trong Chromium → người dùng tự Save/Finalize tại cổng → kiểm tra kết quả từng mục; không nhầm dry-run là đã lưu. |
| N1 — Hồ sơ thừa kế và dữ liệu nền | `NV2-01`, phần người/tài sản của `NV2-04` | Dùng `notary.case_list`, `notary.case_get`, `notary.case_create`, `notary.customer_list`, `notary.customer_create`, `notary.property_list`, `notary.property_create`, `notary.participant_add` cho **hồ sơ thừa kế**. `case_create` đòi `nguoi_chet_id` và `tai_san_id` (`shell/sidecar/notary_adapter.py:278-302`): UI thu thập/lưu hai nguồn này trước rồi mới tạo case; nếu cần tạo hồ sơ rỗng, phải đặc tả năng lực mới. Thao tác sửa/xóa/xác nhận mà bridge chưa có cũng cần spec/contract trước. | Tạo/mở hồ sơ thừa kế với dữ liệu nền hợp lệ; tải lại vẫn đúng owner DB, dữ liệu chưa xác nhận còn trạng thái rõ; không thể tạo A/B dưới nhãn thừa kế. |
| N2 — Bàn soạn thừa kế | `NV2-03`, phần gán/diagram của `NV2-04` | Tái sử dụng parser/validation Case Workspace (`notary_v2/routers/cases.py:133-274,518-567`). `notary.case_get` mới trả cờ `has_engine_state`/`has_case_state`, chưa trả sơ đồ (`shell/sidecar/notary_adapter.py:151-178`); cần đặc tả và duyệt command đọc/lưu state, revision, quyền ghi trước khi nối UI. | Gán người/tài sản, lưu và mở lại sơ đồ thừa kế đúng; thay dữ liệu nền làm output liên quan stale; không âm thầm ghi đè khi revision đổi. |
| N3a — Intake/OCR | `NV2-04` phần OCR tham khảo | Backend OCR có nhưng bridge Electron đang gọi `_get_api_key(model)` sai chữ ký hàm `_get_api_key()` (`shell/sidecar/notary_adapter.py:478`, `notary_v2/routers/ocr_ai.py:68`); lệnh hiện chưa chạy được. Bridge cũng chưa có command xác nhận giá trị OCR vào hồ sơ. | Sửa lỗi bridge và kiểm chứng OCR thật → người dùng review/confirm theo contract được duyệt; trường chưa confirm không thành dữ liệu nghiệp vụ. |
| N3b — Nguồn Zalo | `NV2-05`, `NV2-06` | `zalo.status` chỉ cho biết trạng thái; QR, danh sách tin/media và chọn/chuyển file chưa có bridge tương ứng. Chốt policy tài khoản văn phòng và nguồn dữ liệu server trước khi mở command. | QR/source/media chỉ bật khi có command và policy thật; file chọn được gắn nguồn và quyền truy cập, không tạo dữ liệu giả. |
| N4 — Word thừa kế hiện có | `NV2-07` phần văn bản chính tham khảo | Dùng `notary.export_word` xuất **một** `ho_so_thua_ke_<id>.docx` (`shell/sidecar/notary_adapter.py:407-459`); `notary.word_templates` đã đăng ký nhưng chưa có control UI. Word engine cần sơ đồ đủ chủ đất/người chết/người nhận (`notary_v2/services/word_engine.py:808-825`), điều mà luồng tạo đơn giản trên Electron chưa bảo đảm. Bộ nhiều văn bản/tờ khai thuế/đơn đề nghị là feature khác. | Hồ sơ fixture đi từ Electron tới một Word thừa kế đúng, file mở được; thiếu field/lỗi xuất hiện đúng, không coi bản cũ là bản mới; UI không báo đã xuất cả bộ. |
| V — Parity và phát hành | Cả hai module G1 | Đối chiếu inventory MIN-74, chạy packaged smoke, lỗi mạng/process/file và hai máy theo MIN-76; MIN-66 chỉ review merge-readiness, không tự quyết cutover. | Theo scope G1 đã duyệt, chứng minh Upload gồm review/edit và queue, Notary gồm intake/OCR→review→confirm, Case→Word và Zalo Inbox (`docs/architecture/ELECTRON_G1_PLAN.md:70-84`); mọi phần chưa có phải ghi gap hoặc được owner đổi scope, không tính là parity. |

`U1` và `N1` có thể bắt đầu song song sau `P0/S0`. Phụ thuộc trong Upload là
`U1 (manifest đúng) → U3`; `U2` là lát cắt riêng nếu workflow cần preview/PDF.
Trong Notary, `N2` cần `N1`; `N4` có thể bắt đầu sau `N2` với
fixture đã xác nhận. `N3a` và `N3b` có thể làm song song sau `N1` khi contract
tương ứng được duyệt; sau đó kiểm chứng OCR/Zalo ảnh hưởng đúng tới precheck và
Word. `N3a`/`N3b` không được bỏ khỏi gate parity G1 nếu owner chưa đổi scope.
Ưu tiên đầu tiên cho nghiệm thu chạy thật là `U1` vì shell đã có lệnh
scan/audit và G1 đặt Upload/Audit trước Notary; `N1` vẫn triển khai song song.
`NV2-02`, bộ nhiều Word và xử lý PDF của `UL-04` không nằm trên đường găng
G1 này cho đến khi owner duyệt phạm vi nghiệp vụ mới.

## 4. Phần UX tham khảo chưa có backend phù hợp

| Màn hình | Quyết định trong kế hoạch này | Gate mở implementation |
|---|---|---|
| `NV2-02` bàn soạn A/B | Hiện `Chưa hỗ trợ` hoặc loại khỏi luồng tạo hồ sơ G1; không lưu thành `InheritanceCase`. | AB0: duyệt spec chuyển nhượng/tặng cho/cho thuê/đặt cọc, model/engine owner và contract riêng; AB1 sau đó mới xây backend và nối UI A/B. |
| `UL-04` chỉnh trang/tạo PDF | Chỉ cho xem/chọn file nguồn trong U2; xoay, xóa, đổi thứ tự trang và xuất PDF chưa được coi là đã lưu. | U4a: duyệt spec output, nguồn file, an toàn tài liệu và contract; U4b sau đó mới làm engine PDF/UI và test. Không dùng `upload.prepare` làm PDF. |
| `NV2-07` bộ nhiều văn bản | N4 chỉ xuất Word thừa kế hiện có; tax/request, retry từng file và bộ output không giả lập trạng thái thành công. | W0: duyệt template, dữ liệu đầu vào, precheck, version/stale và contract bundle; W1 sau đó mới làm engine xuất từng văn bản và nối UI. |
| `NO-01`–`NO-05` Office/Evidence, proposal, record, phí, thống kê | Chỉ hiện navigation `Chưa triển khai`, không để các nút mô phỏng ghi nhận case/record/phí như thật. `notaryoffice` hiện chỉ có `intent.md`, không có runtime (`notaryoffice/intent.md:263-274`). | MIN-54/spec owner duyệt; A1/A3/A4 trong `docs/architecture/OPEN_DECISIONS.md:20-23` có kết quả đo; contract và backend được làm ở task tách biệt. |
| `DB-01` database chung | Giữ thông tin trạng thái/placeholder; không cho renderer truy cập DB trực tiếp. | MIN-63 và ADR engine/schema/migration/backup riêng; G1 chưa gộp DB vật lý. |
| Excel → Word và Search trong registry shell | Giữ empty/unavailable rõ ràng; không lấy UI mock làm bằng chứng capability. | Feature spec + engine/command được duyệt và triển khai riêng. |

Sau các gate của `notaryoffice`, phần UI này cần một lộ trình riêng ngoài G1:

| Lát cắt sau G1 | Màn hình | Đầu ra phải chứng minh |
|---|---|---|
| O0 — Đặc tả và nguồn Evidence | — | Đo A1/A3/A4 trên máy thật; owner duyệt MIN-54, nguồn sự kiện, write ownership và contract trước khi có consumer code. |
| O1 — Evidence tra cứu | `NO-01` | Ingest và tìm Evidence có source/timestamp thật; dữ liệu không ghép vẫn tra cứu được, không tự thành Case. |
| O2 — Đề xuất và xác nhận | `NO-02`, `NO-03` | Hiện candidate cùng lý do/source; người dùng confirm/edit/draft/cancel; Evidence bị từ chối vẫn còn, Case nhiều Record theo spec được duyệt. |
| O3 — Record, phí và tổng hợp | `NO-04`, `NO-05` | Record/status và thống kê lấy từ owner backend; quy tắc phí được duyệt riêng, không suy khoản thu từ file Word/output. |

`notaryoffice/intent.md:194-274` hiện mô tả pipeline và ownership **dự định**,
chưa có Sentinel, Hub, bảng Evidence hay Draft Case Builder. Các lát cắt O1–O3
chỉ là phân rã kế hoạch, không phải quyết định triển khai trước gate O0.

## 5. Chia việc cho subagents khi bắt đầu code

Sau khi contract action/result được duyệt ở issue riêng, integrator tách
`buildUploadView`/`buildDocReviewView` khỏi `renderer.js` thành hai file view
riêng, giữ `submit`/job/result/navigation là seam dùng chung. Đây là bước nhỏ
để hai người không cùng sửa một file hơn 1.200 dòng
(`renderer.js:235,474,494,712,1180`). Không thêm framework UI mới.

| Luồng | Quyền sửa chính | Không tự sửa |
|---|---|---|
| Integrator / shell | renderer core, preload/main IPC, command registry, contract conformance, review tích hợp | Quy tắc nghiệp vụ trong `notary_v2`/`upload_lab` |
| Subagent Upload | view Upload riêng, `shell/sidecar/upload_adapter.py`, `upload_lab/` và test module | view Notary, IPC chung |
| Subagent Notary | view Notary riêng, `shell/sidecar/notary_adapter.py`, `notary_v2/` và test module | view Upload, IPC chung |
| Subagent QA/UX | matrix action/screen và fixture/e2e riêng, kiểm thử keyboard/focus và parity | contract hoặc code nghiệp vụ khi chưa có owner |

Mỗi lát cắt là issue/sub-issue có scope, workflow được owner chốt, file owner,
acceptance, fixture, lệnh test và rollback. Kiểm tra trạng thái issue
MIN-68/MIN-69 trên Linear trước khi mở issue mới để không làm trùng phần đã có.
Contract và consumer implementation không nằm cùng một issue.

## 6. Cổng kiểm chứng cho từng lát cắt

1. Test command/adapter bằng fixture không nhạy cảm; chạy `npm test` và các
   Python sidecar checks trong `shell/README.md:72-78`, cộng check của repo
   con khi sửa engine. Chứng minh một action đi từ UI đến output/DB/file thật.
2. So kết quả với UI legacy/fixture MIN-74; kiểm tra empty/loading/error,
   partial/waiting user, cancel/retry, file hỏng, đường dẫn Unicode và quyền
   truy cập. Browser/renderer test ở 1280×820 và 760×520, keyboard/focus.
3. Xác minh đổi module, restart sidecar và ngắt kết nối không làm UI báo thành
   công sai. `shell/sidecar/jobstore.py:118` hiện giữ job trong bộ nhớ; trước
   khi hứa khôi phục job sau restart cần chốt cơ chế khôi phục và test ở gate
   tương ứng.
4. Packaged smoke Windows với engine thật; với Upload luôn mặc định dry-run và
   để người dùng tự quyết Save/Finalize. LAN/multi-client chỉ được công nhận
   sau MIN-76, vì contract hiện tại ghi rõ loopback một máy
   (`contracts/desktop-command.md:8-10`).

## 7. Điều cần chốt khi review plan

- Owner sửa/chốt workflow theo hành động; prototype có thể tiếp tục thay đổi và
  không cần đóng băng hay sửa lỗi render để mở công việc backend.
- Phân biệt `có code engine`, `đã nối bridge Electron` và `đã kiểm chứng end-to-end`;
  UI nào chưa có backend phù hợp phải ghi `chưa triển khai`.
- Chốt danh sách action cần command/contract mới theo từng module, rồi mới
  chia subagents implement. Không tự chốt A1/A3/A4 hoặc database chung.
