---
id: 13
type: spike
title: "Chốt DB vật lý và contract chuyển dữ liệu liên module"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: high
---

# Chốt DB vật lý và contract chuyển dữ liệu liên module

## Description

Chốt DB vật lý/migration và chuyển dữ liệu xuyên ownership trước công việc thực sự ghi/chuyển liên module. Các phép đo Office cô lập không cần đợi DB vật lý chung.

## Approach

Đọc nguồn hiện hành và bằng chứng sẵn có trước. Chỉ so phương án trong ranh issue; không đoán phần nguồn thiếu. Người có vai trò ghi trong Notes cung cấp bằng chứng không thể lấy từ repo hoặc nhận đáp án cần lựa chọn. Không triển khai sản phẩm trong spike.

## Acceptance Criteria

1. **Trả lời đúng câu hỏi hoặc xác định bằng chứng thiếu**
   Verify: Notes ghi đối chiếu có ngày theo từng câu hỏi, nguồn/phương án/hệ quả và phần thông tin còn thật sự không lấy được.
2. **Đáp án dùng được cho đúng bên chờ**
   Verify: Notes chỉ rõ ai chờ, cần quyết định/capability gì, nơi ghi đáp án canonical và việc độc lập không phải chờ.
3. **Người chịu trách nhiệm nhận đáp án đúng phạm vi**
   Verify: owner nhận lựa chọn sản phẩm; người thao tác/reviewer nhận bằng chứng đo. Notes ghi vai trò/ngày; phần Draft/Pending chưa chọn vẫn giữ trạng thái.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C12
- source — _bmad-output/specs/shared/data-rules.md, §5–§7, Còn mở
- source — _bmad-output/decisions/decision-extraction-output-data-contract.md, §Decision
- source — contracts/README.md, dòng 20–23, 57–62, 69–78 (đọc 16/10/2026): ba công cụ độc lập; **chưa có contract trao đổi dữ liệu xuyên sản phẩm**; luật contract → owner duyệt → code
- source — _bmad-output/specs/README.md, §5, dòng 46,48 (engine chung/cách chuyển chưa chốt; module giữ quyền ghi)
- source — _bmad-output/specs/shared/data-rules.md, §4.1–§4.2 và §5–§7 (dòng 28–29,44–46,54–55,71–72,96–108,119–129,163–167)
- source — contracts/g1-module-data.md, §5 (APPROVED 14/09/2026) — ownership một máy
- source — contracts/zalo-intake/zalo-intake.md, §2 (DRAFT MIN-92) — producer/consumer + ranh giới trao đổi
- source — _bmad-output/specs/notaryoffice/README.md, §3,§5; _bmad-output/backlog/spike-office-pilot-scope.md, dòng 44–45 (“Không hard-after DB chung #13”)
- evidence tạm — _bmad-output/tmp/issue-13-shared-data-boundary/evidence.md (16/10/2026)

## Notes

- Tracking: C12; **investigation/evidence recorded 16/10/2026 — điều tra hoàn tất phần lấy được, KHÔNG phải “DB/kênh chuyển liên module đã được duyệt”**. Ownership policy đã có sẵn; **chưa có ca chuyển liên module nào được duyệt/chọn để triển khai** — ca Draft thì đã có (`zalo-intake` MIN-92, §2), nhưng Draft không phải quyền triển khai; DB vật lý/migration vẫn **UNSELECTED**. #1 chỉ tracking, không chạy cùng leaf.
- Risk: high — Ownership hoặc migration sai có thể nối nhầm hồ sơ, mất dữ liệu và ghi ngoài quyền module.
- Open question (đã điều tra 16/10/2026 — xem ledger dưới): Với lần chuyển liên module cụ thể, ai sở hữu từng lần ghi, payload/xác nhận nào được duyệt, chọn DB vật lý/migration nào trước schema production?
- Người thực hiện/ngày: worker `shared-data-boundary-evidence`, nghiên cứu chỉ đọc và ghi tài liệu 16/10/2026; không phải owner, người thao tác hoặc reviewer độc lập. Không có quyết định sản phẩm mới, không tự chọn engine/migration, không tạo decision, không đổi spec.
- Ai chờ: **implementation chuyển liên module thật** — cần **một ca chuyển được duyệt/chọn để triển khai** (ca Draft đã có: `zalo-intake` MIN-92) + contract của ca đó được duyệt + model ổn định trước khi chọn DB vật lý/migration. Nơi ghi: contract dữ liệu/chuyển được duyệt và Notes này. Không gộp Case từ CCCD/GCN/thửa-tờ; không chặn #14 đo A1/A3/A4.
- Independent check: reviewer không phải người thực hiện đối chiếu riêng quyết định/kết quả với nguồn và dữ liệu/đầu ra liên quan, ghi nhận ngoài bằng chứng tự kiểm của issue.
- Review closeout (16/10/2026): Quick review độc lập ngoài worker (reviewer `shared-data-boundary-review`) — **t1**: câu “chưa có ca chuyển cụ thể” nói quá vì `contracts/zalo-intake/zalo-intake.md` §2 đã mô tả một ca producer↔consumer + payload/ACK; phần thiếu là **duyệt/chọn để triển khai**, không phải sự tồn tại của ca/bản nháp — đã sửa toàn bộ câu chữ; **t2**: CLEAN, chỉ tài liệu (docs-only), không đo runtime, không chạy app/test. Bản ghi đóng băng từ đây, không đổi câu chữ thêm ngoài ghi chú closeout này. Không có phê duyệt sản phẩm nào được tạo.

### Ledger nguồn canonical — 16/10/2026

Các đường dẫn tính từ root repo; số dòng là vị trí đọc, không phải phiên bản hay bằng chứng chạy ứng dụng.

| Câu hỏi | Điều đã rõ (nguồn, đọc 16/10/2026) | Phần còn thiếu và hệ quả |
|---|---|---|
| Ai sở hữu từng lần ghi? | Chính sách đã chọn: module giữ quyền ghi của mình; dùng chung DB không cho ghi bảng do module khác sở hữu; dùng chung ứng dụng không cho tự nối/gộp — `_bmad-output/specs/README.md:46,48`, `_bmad-output/specs/shared/data-rules.md:96–101`. Trong một máy: `contracts/g1-module-data.md` §5 (APPROVED 14/09/2026) — sidecar/engine ghi, shell chỉ qua command. | Chưa có ca liên module nào **được duyệt/chọn để triển khai** để gán chủ từng lần ghi; câu trả lời per-ca thuộc contract của chính ca đó (ca Draft `zalo-intake` MIN-92 đã mô tả producer/consumer nhưng chưa được duyệt). |
| Payload/xác nhận nào được duyệt? | `contracts/README.md` (đọc 16/10/2026) dòng 20–23, 57–62, 69–78: ba công cụ **chưa có API giữa chúng, chưa đọc DB của nhau, chưa có file trao đổi tự động**; **hiện chưa có contract trao đổi dữ liệu xuyên sản phẩm**; luật nối = contract (ai gọi ai, dữ liệu gì, ai sở hữu, xử lý lỗi, ai chịu trách nhiệm khi schema đổi) → owner duyệt → mới viết code. | Chưa có payload/ACK nào được duyệt. Bản Draft đã thấy trong repo mô tả chuyển liên sản phẩm là `contracts/zalo-intake/zalo-intake.md` §2 — **DRAFT** MIN-92 (producer Zalo ↔ consumer Document Intake; ACK = raw đã lưu bền vững, không phải duyệt nghiệp vụ). Không suy đây là ca tương lai duy nhất. |
| Chọn DB vật lý/migration nào trước schema production? | Hiện trạng đã chốt là **SQLite theo module** (decision-34 “stack chung … SQLite/module”, accepted 05/10/2026; `specs/README.md:46`); ràng buộc gộp đã có: UUID/tiền tố nguồn cho record đi qua nhiều module, ISO-8601, tên field tài sản chung, không `rowid` ẩn/kiểu lỏng SQLite trong logic nghiệp vụ — `data-rules.md:102–129`. | **UNSELECTED**: “Engine DB vật lý cuối chưa chốt”; “DB chung và engine đích chưa duyệt”; mục **Còn mở** gồm “Engine DB chung và migration vật lý” — `data-rules.md:96–108,163–167`. Đây là việc kỹ thuật tương lai gắn với model ổn định + ca chuyển được duyệt/chọn để triển khai, **không** phải lựa chọn nghiệp vụ hiện tại; không tự chọn. |
| “DB nghiệp vụ chung là đích” có cho gộp Case hoặc nối module? | Không: “sau này sẽ gộp” **không phải giấy phép** (`contracts/README.md:57–59`); CCCD/GCN/thửa-tờ/số công chứng là bằng chứng đối chiếu, không tự tạo Case hoặc quan hệ sở hữu và không tạo Case liên module (`data-rules.md:44–46,54–55`; [decision-extraction-output-data-contract](../decisions/decision-extraction-output-data-contract.md), §Decision). | Giữ nguyên: không gộp Case, không dùng khóa định danh chung làm mã hồ sơ. Đích DB chung sau khi model ổn định không đổi phần này. |
| Hiện trạng code | **Quan sát đọc tĩnh có giới hạn, ngày 16/10/2026:** `notary_v2/database.py:11–14` neo `notary.db`; `upload_lab/batch_scan.py:26–27` + `upload_lab/registry.py:17–25` dùng `registry.sqlite3` theo website; `shell/sidecar/notary_adapter.py:8–9`, `upload_adapter.py:7–11`, `engine_roots.py:26–31` ghi DB qua command và tách engine root theo module. Grep tên DB trong `notary_v2/` + `upload_lab/` không thấy truy cập DB của module kia. | **Đây KHÔNG phải chứng minh runtime độc lập toàn cục** — chỉ là đọc tĩnh giới hạn tại thời điểm ghi; không chạy app/test, không thay bằng chứng runtime. Không dùng quan sát này thay cho luật contract ở các dòng trên. |

### Bên chờ và giao bằng chứng — 16/10/2026

- **Implementation chuyển liên module thật:** chờ **một ca chuyển được duyệt/chọn để triển khai (ca Draft đã có: `zalo-intake` MIN-92) + contract của ca đó được duyệt + model ổn định**; khi đó mới chốt ownership từng lần ghi, payload/ACK, và chọn DB vật lý/migration (việc kỹ thuật, ghi ở cấp spec/contract theo `data-rules.md` §6). Không dựng kênh trước contract.
- **Owner:** hiện **không có lựa chọn sản phẩm mới đủ bằng chứng**. Khi có ca được chọn để triển khai, việc của owner là duyệt contract của chính ca đó (`contracts/README.md:75`); **không** hỏi owner chọn SQLite/Postgres, revision hay cơ chế chuẩn hóa.
- **Giữ nguyên Draft/Pending (retain):** `contracts/zalo-intake/` (DRAFT MIN-92), `IdentityEvidence`/`ConversionEnvelope` xuyên sản phẩm (Draft MIN-62/MIN-61), thiết kế NotaryOffice (Draft, chưa có runtime). Không nâng thành đã duyệt.
- **Việc độc lập không phải chờ:** #14 đo Office cô lập A1/A3/A4 **không bị chặn** bởi DB vật lý chung hay bởi #13; phần evidence của #12 đã đóng; không phát sinh hard-after mới.
- **Nơi ghi đáp án:** Notes này là bản giữ bền vững; bằng chứng chi tiết tạm ở [`tmp/issue-13-shared-data-boundary/evidence.md`](../tmp/issue-13-shared-data-boundary/evidence.md). Không tạo decision mới cho lượt điều tra này; nếu sau này có quyết định hệ thống thật thì ghi `decisions/` + spec cùng phiên.
- **Giới hạn kết luận:** AC của spike cho phép xác định bằng chứng thiếu. Kết quả là **điều tra hoàn tất phần lấy được**: không phải “DB/kênh chuyển liên module đã được duyệt”, không phải mọi phần đã trả lời, và không có phê duyệt nào được tạo.

## Bổ sung 22/10/2026 — ba phương án ghi Hồ sơ để owner cân nhắc

**Trạng thái: OWNER ĐÃ CHỌN PHƯƠNG ÁN B (22/10/2026) — xem `decision-owner-case-storage-b-20261022.md`. CHƯA DUYỆT SCHEMA VẬT LÝ HOẶC TRIỂN KHAI.**

- Decision: owner yêu cầu ghi chi tiết cả ba phương án vào issue, sau đó commit và push tài liệu. Đây không phải phê duyệt phương án B được đề nghị trong hội thoại.
- Phạm vi bổ sung: nơi lưu tiến độ Nháp, bộ thông tin Người/Tài sản theo Hồ sơ, ID dùng chung và trách nhiệm của hai nút **Cập nhật / Lưu hồ sơ**. Giữ nguyên phần điều tra ngày 16/10 ở trên; không cấp quyền chuyển dữ liệu liên module.
- Ai chờ: owner cân nhắc trước khi chọn; người thiết kế/triển khai cách ghi mới chờ phương án và hành vi được duyệt. Không đặt thêm điều kiện chờ #13 cho việc regex/placeholder đã rõ.
- Ưu tiên owner: cấu trúc ghi đủ rõ và ổn định. Không dùng câu hỏi về tải tương lai, số máy hoặc chức năng “lưu tức thì” làm điều kiện tiếp tục thiết kế.
- Nơi ghi lựa chọn sau này: decision trong `_bmad-output/decisions/`, quy tắc đang áp dụng trong spec/contract liên quan và Notes issue này. Chưa có lựa chọn mới trong lượt ghi này.
- Cập nhật 22/10/2026: owner đã chọn **phương án B**, sửa Done là thay luôn (không lấy phần C), và **Lưu hồ sơ lưu luôn cả ô đang sửa chưa Cập nhật** — ghi tại `_bmad-output/decisions/decision-owner-case-storage-b-20261022.md`.

### 1. Nguyên tắc cả ba phương án phải giữ

1. Record nghiệp vụ là **Hồ sơ: ai, tài sản gì, làm gì**. Mỗi Hồ sơ có một snapshot nghiệp vụ hiện hành; lưu lại cập nhật snapshot đó, không sinh lịch sử từng ô/lần lưu hoặc bảng phiên bản Người/Tài sản chỉ vì một trường đổi.
2. Nháp lưu bền trong DB dù mới nhập một phần, có nhãn rõ và không làm nguồn lấy dữ liệu mới nhất. Done là mốc user Lưu hồ sơ đã chốt, không tự hiểu là đủ sáu trường hoặc đã công chứng.
3. Hồ sơ đã lưu không tự đổi theo Hồ sơ khác; user có thể sửa thủ công chính Hồ sơ đó.
4. Nguồn điền lại cho Hồ sơ mới là bộ thông tin của **Hồ sơ Done được lưu gần nhất**, không theo ngày giấy tờ, độ đầy đủ hoặc mốc Cập nhật Nháp. Không tự trộn trường của nhiều bộ thông tin.
5. Người gom theo **tên + số giấy tờ đồng thời**. So tên chấp nhận khác dấu/hoa-thường; giữ tên gốc khi hiển thị/xuất. Chưa duyệt so gần đúng mọi lỗi gõ hoặc bỏ dấu câu trong số giấy tờ. Đổi tên/số chấp nhận ID khác; sống/chết cùng bảng.
6. Thiếu điểm neo thì không gom với đối tượng khác. ID trùng đã tồn tại giữ nguyên, không tự hợp nhất; không khôi phục CCCD UNIQUE hoặc chặn nhập vì trùng.
7. Tài sản cùng serial dùng cùng ID dù khác thửa. Giữ từng dòng thửa/tờ, nhóm và lần xuất hiện trong Hồ sơ; không gộp mất chúng vì chung ID.
8. Nhân bản toàn bộ nội dung Hồ sơ. Sửa bản sao không tự thay Hồ sơ nguồn; chi tiết mã dòng/liên kết khi nhân bản còn cần chọn.
9. Dùng bộ trường Người–Tài sản–Hồ sơ đã duyệt. Không thêm đối tượng nghiệp vụ thứ tư, trường tùy ý, công thức/đoạn văn động hoặc túi ghi chú. Giữ raw/bằng chứng/`source_refs` và lịch sử kỹ thuật đã có.
10. Chủ đất thuộc Hồ sơ, lấy assignment Chủ của Diagram đã lưu; không thành thuộc tính cố định của Tài sản. Địa chỉ cũ–mới tạm giữ hiện trạng.

Nguồn: [quyết định 22/10](../decisions/decision-owner-data-entry-save-rules-20261022.md), [điểm neo](../decisions/decision-owner-entity-anchors-case-snapshots-20261021.md), [snapshot](../decisions/decision-owner-case-snapshot-as-history-20261021.md), [Nháp lưu bền](../decisions/decision-owner-persistent-case-drafts-20261021.md), [dữ liệu chung](../specs/shared/data-rules.md).

### 2. Mã Hồ sơ, mã dòng và ID dùng chung

**Đề xuất đang cân nhắc:** mỗi dòng nhập có mã ổn định riêng, kể cả khi chưa có ID Người/Tài sản dùng chung.

| Mã minh họa | Ý nghĩa | Khi nhập thiếu |
|---|---|---|
| H01 | Hồ sơ đang làm | Có thể cấp ngay |
| R01 | Dòng thông tin Người trong H01 | Có thể cấp ngay |
| P09 | ID nhóm Người qua nhiều Hồ sơ | Liên kết có thể để trống |
| A01 / T07 | Dòng Tài sản trong H01 / ID Tài sản dùng chung | Tương tự Người |

Các mã/tên bảng chỉ minh họa quan hệ, chưa phải tên cột/schema được duyệt. `NULL` nghĩa là chưa có giá trị; khóa ngoại là ô trỏ đến ID ở bảng khác.

| Thời điểm giả định | Hồ sơ / dòng | Thông tin trên dòng | ID Người dùng chung |
|---|---|---|---|
| Nhập tên rồi Cập nhật | H01 / R01 | Nguyễn Văn A, số giấy tờ trống | Trống |
| Ba tháng sau mở H01, bổ sung số | H01 / **R01** | Nguyễn Văn A, số giấy tờ đã có | Có thể vẫn trống nếu chọn chốt ID lúc Lưu hồ sơ |
| Chốt liên kết khi Lưu hồ sơ | H01 / **R01** | Giữ bộ thông tin user nhập | P09 nếu phù hợp; hoặc ID mới khi đủ neo và chưa có đối tượng phù hợp |

- R01 lưu bền cùng H01; không cần ID danh mục mới lưu được. Theo đề xuất này, thiếu neo không làm dòng tự hết hạn hoặc chỉ được giữ trong bộ nhớ tạm.
- Mở lại đọc dữ liệu H01, không tự lấy bản mới nhất ở Hồ sơ khác đè Nháp. Bổ sung số sửa đúng R01, không mặc nhiên tạo R02 hoặc chuyển dữ liệu sang bảng khác.
- Liên kết **dòng thuộc H01** phải lưu ngay để mở lại. Nó khác liên kết **dòng thuộc P09** hoặc vai trò trong Diagram. “Lưu quan hệ khi bấm Lưu hồ sơ” không có nghĩa mọi quan hệ DB đều trống trước đó.
- Chưa cấp ID dùng chung chỉ là một phương án. Cấp ID ngay khi Cập nhật vẫn chưa bị owner loại bỏ; nếu cấp sớm phải xử lý rõ bổ sung/đổi neo và ID tạm không còn được dùng.

### 3. Phương án A — lưu cả Hồ sơ thành một khối có cấu trúc

**Tổ chức đề xuất**

- Bảng Hồ sơ giữ ID, trạng thái và một khối có cấu trúc cố định, ví dụ JSON. JSON là cách ghi các trường/danh sách có tên, không phải ghi chú tự do.
- Khối chứa bộ thông tin Người/Tài sản theo Hồ sơ, mã dòng, thứ tự/nhóm và Diagram. Tham chiếu ID dùng chung có thể trống.
- Danh mục Người/Tài sản hoặc bảng tra phụ vẫn có thể cần cho tìm kiếm xuyên Hồ sơ. Khối Hồ sơ giữ bộ thông tin đã dùng; không đọc master để tự thay snapshot cũ.

**Luồng đề xuất**

1. Cập nhật lưu phần nhập dở vào khối H01; mở lại H01 khôi phục các dòng cùng mã.
2. Lưu hồ sơ ghi nội dung chốt, Diagram, liên kết đã giải quyết và trạng thái trong cùng một lượt ghi trọn vẹn.
3. Mở/xuất H01 đọc khối H01. Tìm Người/Tài sản xuyên Hồ sơ cần tra bên trong khối hoặc bảng/chỉ mục phụ.

**Thuận lợi:** ít nơi giữ dữ liệu; dễ lưu, mở và nhân bản toàn bộ Hồ sơ; gần cách đóng gói một file công việc.

**Đánh đổi:** sửa một ô có thể phải ghi lại cả khối; tra cứu xuyên Hồ sơ cần thiết kế thêm. Nếu có bảng tra phụ phải giữ nó khớp khối nguồn. Ít bảng không tự bảo đảm nhanh hơn. Sửa phần đang hiện không được làm mất trường chưa hiện, raw hoặc source_refs.

**Chưa tự giải quyết:** thời điểm gắn ID, Lưu trước Cập nhật và cách sửa Done. Dùng JSON không tự quyết định các hành vi đó.

### 4. Phương án B — lưu từng dòng thuộc Hồ sơ

**Tổ chức đề xuất**

| Nhóm bảng minh họa | Chịu trách nhiệm |
|---|---|
| Hồ sơ | ID, trạng thái, dữ kiện Hồ sơ và mốc Lưu hồ sơ |
| Dòng Người của Hồ sơ | Mã dòng, Hồ sơ cha, bộ trường Người theo Hồ sơ, thứ tự, liên kết Người dùng chung có thể trống |
| Người | ID nhóm qua nhiều Hồ sơ; cấu trúc điểm neo/tra cứu cụ thể còn phải chọn |
| Dòng Tài sản của Hồ sơ | Mã dòng, Hồ sơ cha, bộ trường Tài sản theo Hồ sơ, nhóm/thứ tự, liên kết Tài sản dùng chung có thể trống |
| Tài sản | ID nhóm theo serial; không làm mất nhiều thửa/lần xuất hiện theo Hồ sơ |

Quan hệ minh họa: **P09 ← R01 → H01**, **P09 ← R08 → H02**. R01 và R08 có thể khác địa chỉ/ngày cấp; xuất H01 vẫn dùng R01. Dòng Người của Hồ sơ có thể đồng thời là dòng liên kết có dữ liệu, không bắt buộc thêm bảng chỉ để nối lại cùng quan hệ. Quan hệ Diagram/người–tài sản vẫn phải thiết kế theo Hồ sơ; không suy từ ID danh mục.

**Luồng đề xuất**

1. Cập nhật ghi các dòng thay đổi theo mã dòng. Nháp và Done có thể dùng cùng bảng, không chuyển DB/bảng tạm chỉ vì đổi trạng thái.
2. Với biến thể trì hoãn ID, Nháp lưu bộ thông tin và Hồ sơ cha, còn liên kết danh mục có thể trống.
3. Lưu hồ sơ đối chiếu neo, gắn/tạo ID theo quy tắc được duyệt, lưu Diagram/quan hệ và chuyển Done trong một lượt ghi trọn vẹn.
4. Mở/xuất H01 đọc các dòng thuộc H01. Điền Hồ sơ mới dùng bộ của Hồ sơ Done lưu gần nhất liên quan ID cần lấy.

**Thuận lợi:** dữ liệu thiếu có nơi lưu rõ; bổ sung sửa cùng dòng; tra cứu qua cột/chỉ mục thuận tiện; không cần di chuyển dữ liệu khi cấp ID dùng chung. Thông tin riêng và quan hệ Hồ sơ cha nhìn thấy trực tiếp.

**Đánh đổi:** nhiều dòng/bảng hơn A; phải giữ nhóm/thứ tự và đọc đủ các quan hệ. Không xóa rồi tạo lại toàn bộ dòng mỗi lần lưu làm đổi mã/gãy Diagram. Không được ghi master dùng chung từ Nháp rồi lấy master làm nguồn, dù truy vấn ngoài đã lọc Hồ sơ Nháp.

**Chưa tự giải quyết:** sửa dòng của Hồ sơ vẫn mang Done có thể khiến nội dung chưa Lưu hồ sơ trở thành nguồn. B vẫn phải chọn quy tắc sửa Done; hoãn cấp ID chưa đủ giải quyết vấn đề.

### 5. Phương án C — các dòng đang làm + một bản Hồ sơ đã lưu

**Tổ chức đề xuất**

- Lưu dữ liệu đang làm theo dòng như B.
- Có thêm **đúng một snapshot nghiệp vụ đã Lưu hồ sơ** để xuất/làm nguồn Done. Lưu tiếp thì thay snapshot này, không nối thêm chuỗi lịch sử.
- Bản đang làm là tiến độ sửa; snapshot Done là nội dung user đã chốt. Tách hai trạng thái là đề xuất chưa duyệt, phải xác nhận tương thích nguyên tắc một snapshot hiện hành.
- Snapshot có thể đóng gói sẵn để đọc thuận tiện; không mặc định cần dịch vụ cache, hệ thống sự kiện hoặc DB khác.

**Luồng đề xuất**

1. Cập nhật lưu các dòng đang làm, kể cả thiếu thông tin. Hồ sơ chưa từng Done chỉ là Nháp, chưa có snapshot Done làm nguồn.
2. Với Hồ sơ đã Done, Cập nhật chỉ đổi bản đang làm, chưa đổi bản Done trước đó.
3. Lưu hồ sơ ghi nốt nội dung cần lưu, giải quyết liên kết, thay snapshot Done cùng Diagram/quan hệ và mốc lưu trong một lượt ghi trọn vẹn.
4. Lấy nguồn cho Hồ sơ khác hoặc xuất bản đã lưu thì đọc snapshot Done. Xuất bản đang sửa cần hành vi được duyệt riêng, không tự đoán.

**Thuận lợi:** giữ được Done đã chốt khi sửa tiếp; tách tiến độ khỏi dữ liệu được phép làm nguồn; có nơi rõ ràng để lấy bộ dữ liệu xuất của Hồ sơ.

**Đánh đổi:** trùng một phần dữ liệu; phải chỉ rõ mỗi thao tác đọc bản nào. Snapshot sinh từ dữ liệu đang làm khi Lưu hồ sơ, không cho hai bản tự sửa qua lại. Phải cùng thành công/cùng hủy để tránh lệch dữ liệu. Không khẳng định đây là phương án nhanh nhất.

**Điều cần cân nhắc:** có cần giữ Done trước đó trong khi sửa không? Nếu không, phần tách hai trạng thái có thể chưa cần. C không tự duyệt thêm thao tác/hộp thoại cho user.

### 6. So sánh và khuyến nghị chưa được chọn

| Tiêu chí | A — khối Hồ sơ | B — dòng thuộc Hồ sơ | C — dòng đang làm + một bản đã lưu |
|---|---|---|---|
| Nháp thiếu thông tin lưu lâu dài | Có | Có | Có |
| Chưa có ID dùng chung vẫn lưu được | Có thể thiết kế | Có thể thiết kế | Có thể thiết kế |
| Mở/nhân bản toàn bộ | Trực tiếp từ khối | Đọc/sao chép các dòng và quan hệ | Phải chọn bản đang làm hay đã lưu; không bớt nội dung |
| Tra cứu theo trường xuyên Hồ sơ | Tra JSON/chỉ mục hoặc bảng phụ | Qua cột/chỉ mục | Như B, nhưng nguồn phải từ phần Done |
| Ghi một dòng thay đổi | Có thể phải ghi lại khối | Ghi đúng dòng | Ghi đúng dòng; Lưu hồ sơ còn thay snapshot |
| Giữ Done cũ khi đang sửa | Không tự có | Không tự có | Có nếu chọn tách hai trạng thái |
| Nơi phải giữ đồng bộ | Khối + bảng tra phụ nếu có | Các dòng + quan hệ | Dòng làm việc + snapshot/quan hệ đã lưu |

**Recommendation, chưa duyệt:** B làm nền vì trách nhiệm lưu từng dòng/liên kết dễ kiểm tra. Bổ sung C nếu owner muốn giữ Done trước đó khi sửa tiếp. A vẫn hợp lệ nếu ưu tiên đóng gói/lưu/mở toàn bộ và chấp nhận cách tra phụ. Không tự chọn B/C, engine DB hoặc migration từ khuyến nghị này.

### 7. Thứ tự nhập/bấm nút phải được trả lời trước triển khai

Các hướng xử lý dưới đây để cân nhắc, không phải toàn bộ hành vi đã được duyệt.

| Tình huống | Cấu trúc phải hỗ trợ / phần cần chọn |
|---|---|
| Chỉ tên → Cập nhật nhiều lần | Lưu trên cùng dòng; không tạo dòng/ID mới chỉ vì bấm lại. Cấp ID sớm hay để trống chưa chọn. |
| Nhập số trước, tên sau hoặc qua input khác | Không phụ thuộc thứ tự ô; đủ tên + số mới có neo Người hoàn chỉnh. |
| Bổ sung neo, không có ID phù hợp | Nếu hoãn ID thì cấp tại bước đã chọn. Nếu cấp sớm phải quy định giữ/đổi liên kết; không sinh ID mỗi lần lưu. |
| Bổ sung neo, có ID phù hợp | Có thể gắn dòng hiện tại vào ID đó; không tự hợp nhất/xóa ID cũ hoặc sửa Hồ sơ khác. Nhiều ID cũ trùng cần cách xử lý rõ, không tự đặt luật. |
| Đã Done khi thiếu neo, sau đó điền tiếp | Giải quyết liên kết của dòng hiện có. “Hoãn ID lúc Nháp” không tự giải quyết nhánh này. |
| Xóa/đổi tên hoặc số của dòng đã liên kết | Mã dòng ổn định không buộc giữ cùng Người mãi; đổi A thành B cần xét lại ID. Không đổi các Hồ sơ khác. |
| Gõ thêm → Lưu hồ sơ trước Cập nhật | Đề xuất ghi cả ô đang sửa trong cùng lượt Lưu hồ sơ, chưa được owner chọn. Không âm thầm báo xong khi nội dung mới gõ chưa lưu. |
| Cập nhật rồi dựng/lưu Diagram | Dòng đã thuộc Hồ sơ; tham chiếu Diagram theo mã dòng không đổi chỉ vì bổ sung ID dùng chung. |
| Sửa Done → Cập nhật, chưa Lưu hồ sơ | Chọn chuyển Nháp, hay giữ Done và bản làm việc như C, hay thay Done ngay. Không tự chọn; nguồn phải khớp hành vi được duyệt. |
| Cùng serial, nhiều thửa/dòng | Cùng ID Tài sản, giữ đủ từng dòng/nhóm/thứ tự; không chặn vì ID lặp hoặc thêm điều kiện cùng thửa. |
| Nhân bản H01, thay B bằng C | Bản sao là Hồ sơ khác, đầy đủ nội dung. Thay dòng B ở bản sao không xóa Người B hoặc quan hệ Hồ sơ nguồn. Cách cấp/nối mã dòng cần chọn. |
| Lỗi giữa lúc Lưu hồ sơ | Không để nội dung mới, liên kết cũ và Done dở dang; mọi phần thuộc một lần Lưu hồ sơ phải cùng thành công/cùng hủy. |

### 8. Nguyên tắc ghi/đọc gọn khi chọn thiết kế

- Transaction là một lượt ghi trọn vẹn: các thay đổi liên quan cùng thành công/cùng hủy. Gom thay đổi của một lần bấm nút, không hoàn tất riêng từng ô; không kéo OCR/Word/gọi mạng vào giữa lượt ghi DB.
- Giữ mã dòng qua sửa/mở lại; ghi dòng thay đổi, không xóa rồi tạo lại toàn bộ Người/Tài sản mỗi lần Cập nhật.
- Chỉ mục giống mục lục sách: cân nhắc cho Hồ sơ cha, điểm neo Người, serial và thứ tự nguồn Done. Chỉ mục phục vụ truy vấn cụ thể, không bảo đảm một mức tốc độ.
- Chuẩn hóa khóa tra theo quy tắc được duyệt khi ghi, giữ giá trị gốc để hiển thị/xuất. Không tự suy so hoa/thường SQLite mặc định đủ cho tên tiếng Việt.
- Tách mốc lưu tiến độ khỏi Lưu hồ sơ Done. Cập nhật Nháp không đẩy nguồn “mới nhất” hoặc làm bẩn master mà engine lấy lại.
- Đọc bộ thông tin Hồ sơ bằng một số ít truy vấn theo nhóm; tránh đọc riêng từng ô/người khi có thể đọc chung. Output vẫn dùng canonical fields và snapshot đúng Hồ sơ.
- Không thêm bảng phiên bản mỗi lần sửa, tự gom ID cũ, đổi engine hoặc cơ chế phục hồi phức tạp để dự phòng tải tương lai. Không hứa độ trễ “tức thì” từ việc chọn A/B/C.

### 9. Còn mở và giới hạn bằng chứng

- ĐÃ CHỐT 22/10/2026: chọn **B** (không A, không cộng C) — `decision-owner-case-storage-b-20261022.md`.
- Open question: cấp/đối chiếu ID tại Cập nhật, Lưu hồ sơ hay mốc khác; xử lý Done thiếu neo, đổi/xóa neo và nhiều ID cũ trùng ra sao?
- ĐÃ CHỐT 22/10/2026: Lưu hồ sơ nhận cả ô chưa Cập nhật (lưu tất cả trong cùng lượt); sửa Done là thay luôn nội dung hiện hành, bản đang sửa là nguồn/xuất — cùng decision ở trên.
- Open question: chi tiết chuẩn hóa tên/số, nguồn mới nhất khi có nhiều ứng viên, và cách lấy dữ liệu khi một ID Tài sản có nhiều dòng/thửa trong Hồ sơ nguồn. Không tự gộp mất dòng hoặc chọn một thửa thay user.
- Open question: nhân bản lấy bản đang làm hay đã lưu nếu chọn C; mã dòng/quan hệ ở bản sao cấp và nối thế nào để không ảnh hưởng nguồn?
- Open question: Nháp/Done trong từng báo cáo và UX lưu khi đóng. Không biến phần chưa chọn thành chốt chặn nhập mới.
- Evidence: lượt đọc source 22/10 đã ghi nhận có snapshot JSON, nhưng model Hồ sơ còn bắt buộc liên kết Người/Tài sản và đường Cập nhật có thể sửa master. Vì vậy liên kết dùng chung để trống là **đề xuất thay đổi**, không phải tính năng đã chứng minh chạy được.
- Boundary: chỉ tài liệu; chưa chạy app/test/benchmark/migration, đọc DB production hoặc mẫu khách hàng; chưa sửa code, chọn engine đích hoặc tạo quyền chuyển liên module. Owner cân nhắc tiếp; giữ backlog, `refined: false`.
- Independent check: trước triển khai, reviewer đối chiếu phương án được chọn với §7 và nguồn quyết định. Review tài liệu hiện tại không thay nghiệm thu sản phẩm.
- Review tài liệu 22/10/2026: check Ticket độc lập của BMAD đối chiếu addendum, catalog và sổ tay với nguồn 21–22/10, kết quả PASS trong phạm vi tài liệu; không có lỗi cần sửa. Đường dẫn local/anchor mới hợp lệ, phần điều tra 16/10 và `refined: false` giữ nguyên. Không chạy app/test/DB hoặc kiểm URL web; không coi review này là duyệt A/B/C.

### 10. Tham khảo cho phần bổ sung

- source — `_bmad-output/decisions/decision-owner-data-entry-save-rules-20261022.md`, toàn văn.
- source — `_bmad-output/specs/shared/data-rules.md`, snapshot, điểm neo và ranh giới ghi.
- source — `contracts/entities.md`; `contracts/notary-case-drafting.md`, trường chuẩn, mã dòng và quan hệ Hồ sơ.
- source — `_bmad-output/backlog/story-person-multiple-identities-addresses.md` (#42); `_bmad-output/backlog/spike-case-people-assets-relationships.md` (#43), phạm vi riêng giữ nguyên.
- technical reference — [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html): tham chiếu có thể trống; khi có giá trị phải tuân ràng buộc liên kết.
- technical reference — [SQLite FAQ](https://www.sqlite.org/faq.html#q19): gom thao tác bằng transaction; không lấy số tốc độ phần cứng cũ cam kết hiệu năng sản phẩm.
- technical reference — [SQLite Query Planning](https://www.sqlite.org/queryplanner.html): chỉ mục/tìm dữ liệu, không phải benchmark sản phẩm.
