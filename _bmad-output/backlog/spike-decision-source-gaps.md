---
id: 15
type: spike
title: "Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: low
---

# Đối chiếu các lỗ hổng bằng chứng quyết định còn thực sự tồn tại

## Description

Đối chiếu lỗ hổng provenance còn thật sự tồn tại với spec tự đủ nghĩa và decision đã bổ sung. Số 56 accepted và 6 proposed thân trống là baseline audit lịch sử, không phải số hiện tại.

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
- tracking — _bmad-output/backlog/README.md, C14
- source — _bmad-output/decisions/decision-owner-doc-clarifications-20261015.md, items 7–8
- source — _bmad-output/tmp/owner-doc-decisions-20261015/56-quyet-dinh.md, historical pre-update list
- source — _bmad-output/tmp/docs-consistency-20261014/decisions-audit.md, baseline and limitations

## Notes

- Tracking: C14; **answered 17/10/2026 ở DOC closeout** (đọc nguồn leaf dẫn + bằng chứng sẵn có; không có lựa chọn sản phẩm mới; phần Draft/Pending giữ nguyên). #1 chỉ tracking, không chạy cùng leaf.
- Risk: low — Khôi phục sai lịch sử có thể làm người đọc tưởng một lựa chọn đã được duyệt. Tiêu đề/thân decision rỗng **không** là thẩm quyền; không dựng lý do từ tiêu đề.
- Open question (đã trả lời 17/10/2026): Sau khi đọc nguồn hiện hành, quy tắc quan trọng nào vẫn thiếu bằng chứng? Original task-3/decision48 còn ở đâu ngoài tombstone, và đúng việc nào thật sự bị thiếu nguồn đó chặn?
- Ai chờ: chỉ quy tắc thật sự cần nguồn còn thiếu; không blanket gate. Nơi ghi: ledger theo nguồn và tham chiếu sửa. Không dựng lý do từ tiêu đề hoặc duyệt lại toàn bộ 56; giữ ghi nhận nguồn mất nếu không tìm thấy.

### Trả lời (17/10/2026) — bounded: nguồn leaf dẫn + bằng chứng đã đọc, không phải audit toàn bộ

- **AC1 — quy tắc vật chất còn thiếu bằng chứng:** trong các nguồn được leaf dẫn, quy tắc còn **chưa được owner duyệt** là *bảng đơn dòng nhiều thửa* (đề xuất `decision-72`); spec hiện hành tự ghi rõ "chưa được owner duyệt" (`_bmad-output/specs/shared/extraction-rules.md` §4.4) và owner 15/10 xác nhận mục 4 chưa duyệt (`_bmad-output/decisions/decision-owner-doc-clarifications-20261015.md`). Trong phạm vi đã đọc, **không tìm thấy bảng gốc** cho các quy tắc từng chỉ nằm trong decision thân-trống; hành vi hiện hành **tự đủ trong spec** nên **không thiếu contract hành vi / không mở blanket gate**, nhưng **phê duyệt/lý do gốc vẫn thiếu** (provenance gap — xem AC1b). **Không** phát biểu quét toàn bộ decision/spec.
- **AC1b — lệch provenance (không phải luật sai, không phải quyền sửa code/duyệt):** tiểu quy tắc *ngoặc người chết đứng trước ngoặc sinh/chết* (cùng tiêu đề `decision-72`) xuất hiện trong spec như hành vi hiện hành có mốc 11–12/10, trong khi `decision-72` vẫn `proposed` + thân rỗng nên **không chứng minh được phê duyệt/lý do độc lập**; spec **viết** hành vi này là hiện hành, **không** tự tuyên bố chưa duyệt. Ghi là **provenance gap** — không kết luận luật sai, không cấp phép sửa code, không mở quyền phê duyệt.
- **AC2 — task-3/decision-48 ngoài tombstone:** file gốc `.agents/plans/task-3-administrative-lookup-v2.md` **chưa từng được commit** nên **không tìm thấy bảng gốc/nguyên văn** (chỉ tên trong `_bmad-output/archive/removed-agents-files.md`; `_bmad-output/decisions/decision-48 - Chap-nhan-mat-file-tam-agents-va-BMAD-doc-spec-tu-noi-moi.md` chỉ liệt kê tên, không lưu nội dung/tóm tắt). Phần **nội dung tương ứng vẫn còn** ở nơi khác: spec tự đủ `_bmad-output/specs/shared/administrative-lookup.md` (**thẩm quyền hành vi hiện hành duy nhất** — `:344–346` giữ kết quả nghiệm thu như ghi chép trong spec), và thẻ task lưu trữ `_bmad-output/archive/backlog/tasks/task-3 - Triển-khai-lõi-tra-cứu-hành-chính-theo-spec-contract-v2.md` (chỉ **bằng chứng hoàn thành/tóm tắt lịch sử** — AC + mục PLAN/NOTES). **Decisions 40–47 kiểm giới hạn 17/10: accepted nhưng thân RỖNG (chỉ tiêu đề)** → **không** phải thẩm quyền độc lập. **Không** phải plan đã mất, thẻ task, hay tiêu đề/thân rỗng làm thẩm quyền.
- **AC3 — trong phạm vi các nguồn leaf dẫn đã đối chiếu: nguồn task-3 đã mất KHÔNG chặn việc nào.** Lõi tra cứu v2 đã built/nghiệm thu; không thấy việc TASK-3 hiện tại nào phụ thuộc plan gốc (**không** suy rộng ra mọi nguồn đã mất). Hai bên chờ thật sự đều **ngoài** #15: **#12** thiếu **nguồn + nhãn độc lập** cho F04/F05 (bằng chứng **đo**; nguyên tắc/tương thích đã ghi — **không** phải lựa chọn thuật toán được duyệt); **#13** DB vật lý/migration **UNSELECTED** là **việc kỹ thuật chưa chọn**, không phải câu hỏi owner chọn SQLite, và chỉ phát sinh per-ca khi có ca chuyển được duyệt/chọn. **Office DEFERRED** 17/10 — không có việc Office ở đây.

### Ledger nguồn canonical — 17/10/2026

| Hạng mục | Kết luận có căn cứ | Nguồn (đọc 17/10/2026) |
|---|---|---|
| Nguồn mất | `decision-48` (lịch sử) ghi 11 file `.agents/` tạm (gồm plan task-3) **mất vĩnh viễn**; kiểm giới hạn 17/10: **không có trong repo/chưa từng commit**, tombstone chỉ có **tên** — **không** phải chứng minh phục hồi toàn cục cho mọi nguồn đã mất | `archive/removed-agents-files.md`; `decisions/decision-48 …` |
| Tự đủ nghĩa (thay nguồn mất) | Luồng tra cứu → `specs/shared/administrative-lookup.md`; quy tắc trường/luật hiện hành → `specs/shared/extraction-rules.md` | spec hiện hành |
| Thẩm quyền hành vi hiện hành | **chỉ** spec tự đủ (`specs/shared/administrative-lookup.md:344–346` giữ kết quả nghiệm thu như ghi chép trong spec); thẻ task Done (archive) chỉ là **bằng chứng hoàn thành/tóm tắt**; **không** dùng tiêu đề/thân rỗng (`decision-40..47` accepted nhưng **thân rỗng**) | spec hiện hành |
| Việc bị chặn bởi nguồn đã mất | **Trong phạm vi TASK-3 đã đối chiếu:** không có việc hiện tại nào bị chặn (không suy rộng cho mọi nguồn đã mất) | thẻ task-3 Done; spec tự đủ |
| Provenance gap còn ghi nhận | *bảng đơn dòng* chưa duyệt (`decision-72`); *ngoặc người chết* thiếu ghi nhận duyệt | `specs/shared/extraction-rules.md` §4.4/§4.3; `…clarifications-20261015` |
| Không lấy được | lý do/ngoại lệ `decision-72` & 51–54 (thân rỗng); bản Git plan task-3; đáp án F04/F05; DB/kênh chuyển | tombstone; `decision-48`; #12; #13 |

### Bên chờ và giao bằng chứng — 17/10/2026

- **Owner (lựa chọn sản phẩm):** không có câu hỏi **mới** từ #15. Quy tắc *bảng đơn dòng* chỉ cần owner duyệt **nếu/khi** định triển khai rule đó; hiện đã theo dõi ở C11/#12. Không mở lại ở đây.
- **Người thao tác/labeler (bằng chứng đo):** nguồn Word thật + nhãn độc lập cho F04/F05 — giao cho #12, không phải #15.
- **Developer/kỹ thuật (không phải owner):** chọn engine/migration DB vật lý + kênh chuyển — việc **kỹ thuật chưa chọn**, **không** phải owner chọn SQLite — thuộc #13.
- **Owner (chỉ khi có ca chuyển):** duyệt **payload/xác nhận per-ca** — thuộc #13.
- **Nơi ghi đáp án:** Notes này (ledger bền vững); bằng chứng chi tiết tạm ở `_bmad-output/tmp/issue-15-decision-source-gaps/evidence.md` + `static-ledger.json`.
- **Việc độc lập không chờ:** các issue nguồn/docs/quyết định khác theo catalog — không có mục nào ở đây bị #15 chặn (không gồm Office — deferred).

### Phần còn Draft/Pending (giữ nguyên)

- `decision-39`, `decision-51`–`decision-54`, `decision-72`: **giữ `proposed`** (thân rỗng — không phải thẩm quyền).
- Quy tắc *bảng đơn dòng*: **giữ "chưa được owner duyệt"**; không nâng Active.
- F04/F05: **giữ Pending**; Office: **giữ Draft** (deferred 17/10); DB/kênh chuyển: **giữ UNSELECTED**.

### Review độc lập — 17/10/2026

- Reviewer: `decision-source-gap-review` (phiên độc lập). **t1:** bốn phát hiện gốc — phạm vi phủ định AC3; không gộp "spec tự đủ" với provenance phê duyệt; quy nguồn mất/bất khả hồi đúng nguồn lịch sử; thẩm quyền hành vi = spec, **không** phải thẻ task — **đã sửa**. **t2:** **CLEAN**.
- Giới hạn: thuần **docs**; **không** runtime/code/test/bằng chứng đo; không duyệt lại 56 mục; không nâng Draft/Pending; không mở gate owner; không đổi status.
- Điều tra #15 **đã xong** — **không** có nghĩa provenance nguồn đã mất được khôi phục; **chuyển quyền ghi canonical sang #16**.
