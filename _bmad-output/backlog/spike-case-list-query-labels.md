---
id: 20
type: spike
title: "Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Chốt tìm kiếm, bộ lọc và nhãn Danh sách hồ sơ

## Description

Chốt nhãn, nguồn tìm kiếm, bộ lọc và trình bày trạng thái của Danh sách hồ sơ. Danh sách/tạo/mở hiện có không bị coi là chưa tồn tại.

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
- tracking — _bmad-output/backlog/README.md, C19
- source — _bmad-output/specs/notary_v2/README.md, §2, §9
- evidence — _bmad-output/tmp/issue-20-case-list/evidence.md, ledger + run smoke 17/10/2026

## Notes

- Tracking: C19; **owner trả lời 17/10/2026 — chức năng làm lại DEFERRED**, owner sẽ tự triển khai spec sau; `refined: false`, không built, không đổi runtime/contract/code. Phương hướng owner ghi nguyên văn bên dưới là **Draft chưa duyệt**, không phải business design đã chốt. Đề xuất phạm vi của trợ lý trước đó **chưa được duyệt; không còn là câu hỏi đang hoạt động**, chỉ giữ làm bằng chứng lịch sử. #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Nhãn/lọc chưa rõ làm khó tìm đúng hồ sơ; lượt này **không** đổi query/runtime.
- Lượt này: worker `case-list-scope-evidence` (đối chiếu nguồn, chạy smoke cô lập và ghi Notes; không đổi hành vi), 17/10/2026.
- Evidence: [evidence](../tmp/issue-20-case-list/evidence.md) + `static-ledger.json` + smoke throwaway có giới hạn, 17/10/2026.

### Ledger nguồn — 17/10/2026 (hiện trạng vs đề xuất, có ngày)

| Nội dung | Nguồn/thẩm quyền | Kết luận |
|---|---|---|
| Danh sách/tạo/mở đã có | [Notary §2](../specs/notary_v2/README.md), dòng 11–13; `shell/src/renderer/notary/case-drafting-view.js` `buildCaseListPanel` | Đã tồn tại thật; **không** phải feature built mới. |
| Tên mong muốn | [nền sản phẩm](../specs/README.md), dòng 17; sổ tay dòng 79 | "Danh sách hồ sơ" thay "Tổng quan" đã nêu rõ — **không hỏi lại**; code vẫn "Tổng quan hồ sơ". |
| Nguồn tìm hiện tại | `shell/sidecar/notary_adapter.py` `case_list`/`_case_row` | Row đã serialize = **một khách hàng neo** (cột legacy `nguoi_chet_id`) + **một tài sản vị trí 1** + metadata; không bỏ dấu. Người khác/tài sản khác **không** được tìm **như trường Stage có cấu trúc**. |
| Lọc trước/sau limit | `case_list` (trên); smoke runtime 17/10 | **Lỗi hiện hành:** lọc **sau** `limit`; hồ sơ cũ hơn 50 bản mới nhất không khớp. Đã quan sát runtime; sửa là **việc developer**, không cần owner cho phép. |
| Ngày | `notary_v2/frontend/templates/cases/list.html`; `word_engine.py` | Code hiện dùng `ngay_lap_ho_so` — chỉ là **hiện trạng**; chọn business `created_at` vs ngày lập hồ sơ **vẫn là đề xuất**, không phải đã chốt. |
| Nhãn trạng thái | `notary_v2/models.py` (comment `# draft / locked`); `list.html` | Hai trạng thái hiện có; chữ thân thiện chỉ là **tiền lệ code web cũ** — việc developer, không hỏi micro-choice. |
| Rỗng/lỗi | `case-drafting-view.js` | Đã có face loading/rỗng/lỗi — **không phải feature thiếu**. |
| "Người tạo" | `notary_v2/models.py` (`InheritanceCase`, phạm vi Notary đã đọc) | **Không** có cột tác giả / hệ tài khoản trong phạm vi đã đọc ⇒ không suy được; cần nguồn định danh thật **bên ngoài**. |
| Wire `case_list` | `contracts/notary-case-drafting.md` | `case_list` **không được định nghĩa** trong contract (shape chỉ cố định bằng code + test parity). Không đếm tổng command. |

### Đề xuất phạm vi — CHƯA ĐƯỢC DUYỆT

**Đã bị thay thế làm câu hỏi đang hoạt động — 17/10/2026.** Đề xuất này **chưa được duyệt; không còn là câu hỏi đang hoạt động**; hướng làm lại được ghi nguyên văn ở §"Định hướng owner" bên dưới và cũng **chưa chốt**. Giữ nguyên phần này làm bằng chứng lịch sử, không phải đã được chọn.

- **Q1 (chính) — nguồn tìm + bộ lọc:** tìm theo họ tên **+ số giấy tờ** của **mọi Người đã lưu trong Stage** và **serial + số thửa + số tờ** của **mọi Tài sản đã lưu**, bỏ dấu/hoa-thường; bộ lọc **Loại văn bản / Trạng thái / Ngày lập hồ sơ**. Phương án hẹp để so: **giữ nguyên phạm vi tìm hiện có** (khách hàng neo + tài sản vị trí 1 + metadata). Owner **có thể đổi từng trường**. [INFERENCE] khuyến nghị đề xuất mở rộng; **không** phải đã chọn.
- **Q2 (kèm) — "người tạo":** **hoãn** tới khi có nguồn định danh thật; nếu owner chọn rõ thì cho **gõ tay** tên người tạo. **Không** thay bằng "Công chứng viên/Người phụ trách" (vai trò khác) và **không** thêm auth/gán việc.
- **Không** hỏi cú pháp/ngôn ngữ truy vấn/schema; **không** dựng UI giả hay đổi runtime trong spike.

### Bên chờ, giới hạn và đúng ba AC

- **Ai chờ:** việc làm lại Danh sách hồ sơ chờ owner triển khai spec sau (nay DEFERRED); Q1/Q2 không còn chờ trả lời. **Nơi ghi:** hướng owner nguyên văn ở Notes (DRAFT chưa duyệt) + [decision hoãn](../decisions/decision-owner-case-list-redesign-deferred-20261017.md); spec/design Notary (§2/§9) ghi trạng thái hoãn; wire `case_list` chỉ khi có spec được chốt. **Không chờ:** danh sách/tạo/mở hiện có, Xuất Word, #21/#27; Office DEFERRED 17/10.
- **Bằng chứng chạy (17/10/2026):** smoke throwaway gọi **adapter thật** `notary_adapter.case_list` trên SQLite TEMP (51 hồ sơ): token cũ nhất / limit mặc định → **0**, token mới nhất → **1**, token cũ nhất / limit=200 → **1**. Lệnh + kết quả + giới hạn ở [evidence](../tmp/issue-20-case-list/evidence.md) §9. **Không** sửa hành vi; việc sửa lọc-trước-limit thuộc developer.
- **AC1:** ledger trên đối chiếu có ngày; phần không lấy được (nguồn định danh; nhu cầu tra cứu thật) ghi rõ.
- **AC2:** chỉ UX/query tương lai chờ; nơi ghi và việc độc lập không chờ đã nêu.
- **AC3:** owner đã trả lời (hoãn làm lại; hướng Draft chưa duyệt); operator/reviewer nhận bằng chứng đo sau. Giữ Draft/`refined: false`; **không** đánh dấu accepted/built/đóng #20.
- **Trạng thái trang:** **owner trả lời 17/10/2026 — chức năng làm lại DEFERRED**; không còn câu hỏi đang chờ. Hướng owner là Draft chưa duyệt (§"Định hướng owner" bên dưới); lượt này chỉ đồng bộ trạng thái hoãn trong spec Notary, không triển khai spec chi tiết hay đổi contract/code/runtime.

### Định hướng owner — 17/10/2026 (nguyên văn; Draft, chưa chốt)

Owner gửi nguyên văn đoạn dưới (giữ nguyên chữ/câu, kể cả "NGười"; owner yêu cầu "ghi lại đoạn này vào issue, nguyên văn"):

```
chức năng này cần làm lại, note lại phương hướng (chưa chốt chắc chắn):
- tuân theo rule mọi input, output phải theo chuẩn database.
- Mỗi hồ sơ (hiển thị dạng thẻ) trong danh sách hồ sơ sẽ hiển thị những trường gì? được quyền search trường gì?
- Khi filter thì filter trường gì?
- Search và filter tôi chưa chốt những trường gì mà chức năng này được phép gửi request đến database? 
- Dự kiến: Mỗi thẻ chia làm 3 vùng: 
+ NGười: Tên, số giấy tờ
+ Tài sản: Số serial, địa chỉ, tên chủ đất (trường này chưa tồn tại hoặc chưa được chốt rõ ở bảng dữ liệu nào, chỉ có quan hệ chủ đất trong hồ sơ thừa kế)
+ Hồ sơ: ngày tạo, loại hồ sơ, tình trạng xử lý (đang làm, xuất xong)
### ghi lại đoạn này vào issue, nguyên văn, tôi sẽ triển khai spec sau. Chuyển issue tiếp
```

Diễn giải phạm vi — **không** phải quyết định nghiệp vụ:

- Chức năng Danh sách hồ sơ **làm lại** và nay **DEFERRED**: owner tự triển khai spec sau. Không giao viết spec, đổi runtime, contract hay code ở lượt này.
- Đoạn trên là **phương hướng Draft** ("chưa chốt chắc chắn"): các câu hỏi trường hiển thị/search/filter, whitelist/mapping cụ thể, bố cục thẻ 3 vùng Người/Tài sản/Hồ sơ, và ý niệm "tên chủ đất" đều **chưa được duyệt**. Riêng ràng buộc "mọi input/output tuân theo chuẩn database" là **yêu cầu trực tiếp của owner**, không phải phần tentative.
- **Owner yêu cầu mọi input/output tuân theo chuẩn database** — ràng buộc trực tiếp của owner, không phải đề xuất bị bỏ. Whitelist trường hiển thị/search/filter, mapping input/output cụ thể và phạm vi `case_list` gửi tới database **chưa chốt**. Bố cục thẻ, enum trạng thái (đang làm/xuất xong), nghĩa "ngày tạo" và vị trí DB của chủ đất vẫn **tentative/chưa duyệt**.
- Không hỏi lại #20. Lỗi lọc-sau-`limit` đã tái hiện 17/10/2026 vẫn **chưa sửa** và không thuộc lượt này; evidence cũ giữ nguyên.

### Làm rõ mới — owner 19/10/2026

**Chủ đất là trường Hồ sơ**, không là thuộc tính sở hữu cố định của Tài sản
hoặc mặc định node `owner`/`owner_row_id` Thừa kế. Lựa chọn này thay phần
“vị trí chủ đất chưa chốt” trong diễn giải lịch sử 17/10 bên trên; **không sửa
đoạn owner nguyên văn**. Key/kiểu/cardinality/schema cụ thể còn phải chốt trong
[#41](story-upload-business-field-standardization.md). #20 vẫn **DEFERRED**;
whitelist hiển thị/search/filter, phạm vi request và bố cục thẻ chưa được duyệt.
Không phải quyền triển khai UI, contract hoặc runtime.
[Quyết định mới](../decisions/decision-owner-upload-field-standardization-20261019.md).
