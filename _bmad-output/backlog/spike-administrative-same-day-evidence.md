---
id: 27
type: spike
title: "Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Đối chiếu văn bản chuyển một phần và bãi bỏ hành chính cùng ngày

## Description

Tìm và đọc văn bản lịch sử chứng minh quan hệ giữa chuyển một phần lãnh thổ và bãi bỏ đơn vị cùng ngày. Người có nguồn/chuyên môn xác nhận cách đọc sự kiện. Đây là nghiên cứu độc lập với extraction/OCR #12; không triển khai thuật toán thời gian.

## Approach

Đọc giới hạn ledger và deferred trước, tận dụng văn bản đã có. Theo từng ca, ghi đơn vị nguồn/đích, toàn bộ hay một phần, ngày hiệu lực và phần văn bản cho biết các việc có phối hợp trong cùng văn bản hay không. Không suy thứ tự nội ngày hoặc nhóm văn bản khi nguồn không có. Nếu không lấy được văn bản đủ căn cứ, giữ câu hỏi unresolved.

## Acceptance Criteria

1. **Nguồn gắn đúng từng nhận định**
   Verify: Notes/ledger có danh mục văn bản, trích vị trí liên quan, ngày và ID đơn vị có căn cứ; phần không xác định hoặc pending được ghi riêng.
2. **Phân biệt lịch sử whole/partial và giới hạn ledger**
   Verify: bảng đối chiếu giải thích nguồn nào chứng minh phối hợp chuyển một phần/bãi bỏ cùng ngày, nguồn nào chưa đủ; không lấy vòng partial ở ngày khác làm bằng chứng tự động cho cùng ngày.
3. **Kết luận nghiên cứu có người nhận**
   Verify: owner/người có chuyên môn nhận cách đọc nguồn với ngày xác nhận, hoặc ghi rõ thiếu nguồn chưa giải quyết. Chỉ thay luật thời gian dùng kết luận này chờ đáp án; extraction/OCR #12 không chờ.

## Boundaries

- Không thêm temporal algorithm, thứ tự nội ngày, nhóm văn bản, migration/schema hoặc luật cấm toàn bộ cùng ngày.
- Không đổi pending thành confirmed, không dùng ngày tải làm ngày hiệu lực, không suy whole từ partial/unknown.
- Không mở lại hướng DB/dịch vụ mới hoặc tối ưu recursion khi chưa có nhu cầu thực.

## References

- parent — none
- tracking — _bmad-output/backlog/README.md, C26
- source — _bmad-output/specs/shared/administrative-lookup.md, §3.5–§3.6, dòng 568–621
- source — _bmad-output/implementation-artifacts/deferred-work.md, dòng 30–33
- primary — [Nghị quyết 1286/NQ-UBTVQH15, UBTVQH](https://vanban.chinhphu.vn/?docid=211788&pageid=27160), [PDF ký/dấu](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/1286-qh.signed.pdf), Điều 1.14.a, 1.16.c–d; Điều 2, trang 8–9, 11
- primary — [Nghị quyết 1674/NQ-UBTVQH15, UBTVQH](https://vanban.chinhphu.vn/?pageid=27160&docid=213997), [PDF ký/dấu](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/6/1674-nq.signed.pdf), Điều 1.101/109; Điều 2.1–2.3, trang 7–10
- lead, chưa phải primary — [Báo Chính phủ, 16/10/2009: Thành lập thị trấn Thống nhất, tỉnh Thanh Hóa](https://baochinhphu.vn/thanh-lap-thi-tran-thong-nhat-tinh-thanh-hoa-10227967.htm), dẫn Nghị quyết 52/NQ-CP
- research — [ledger chi tiết và mapping nguồn](../tmp/issue-27-administrative-same-day/source-ledger.md), [handoff](../tmp/issue-27-administrative-same-day/handoff.md), [runtime proof](../tmp/issue-27-administrative-same-day/runtime-proof.json)

## Notes

- Tracking: C26; **17/10/2026 — hoàn tất phần nghiên cứu hữu hạn có thể thực hiện; nguồn/xác nhận còn UNRESOLVED**, không phải spike built hoặc đã xác nhận pháp lý. Giữ `refined: false`, HITL và risk medium; không đổi thuật toán, spec, validator hay dữ liệu.
- Risk: diễn giải sai phạm vi whole/partial, identity hoặc ngày có thể dẫn tới đề xuất quy tắc thời gian sai. Worker nghiên cứu không phải owner/chuyên gia pháp lý; acceptance của validator không phải pháp luật hoặc phê duyệt nghiệp vụ.

### Ledger kết luận có nguồn — 17/10/2026

**S1 — Cầu Dền, quận Hai Bà Trưng, Hà Nội: chứng minh phối hợp partial + nhập phần còn lại cùng ngày hiệu lực, không phải literal abolish riêng.** [Primary NQ1286](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/1286-qh.signed.pdf), Điều 1 khoản 16 điểm c–d, **trang 9**:

- Điểm c: “**Điều chỉnh một phần diện tích tự nhiên là 0,14 km², quy mô dân số là 9.502 người của phường Cầu Dền để nhập vào phường Bách Khoa.**”
- Điểm d: “**Nhập toàn bộ diện tích tự nhiên là 0,03 km², quy mô dân số là 2.036 người của phường Cầu Dền sau khi điều chỉnh theo quy định tại điểm c khoản này vào phường Thanh Nhàn.**”
- Cross-reference điểm d→c xác định chính Cầu Dền ấy, không nối theo tên trùng. Whole ở điểm d là **toàn bộ phần sau điều chỉnh**, không biến nhánh partial ở điểm c thành whole. Văn bản thông qua/ban hành **14/11/2024**; Điều 2, **trang 11**: “**Nghị quyết này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2025.**” Hai nhánh cùng hiệu lực **01/01/2025**; không suy giờ hoặc thứ tự nội ngày từ thứ tự điểm.
- **[INFERENCE]** Theo quy tắc validator hiện hành whole-consumes-input, phân bổ hết có thể được diễn giải là kết thúc identity trong mô hình. Hai điểm trên **không dùng câu “giải thể/bãi bỏ” riêng**; chưa chứng minh một sự kiện `abolish` độc lập được pháp lý/owner xác nhận. Không tự tạo abolish confirmed. Historical unit_id Cầu Dền/Bách Khoa/Thanh Nhàn chưa được nguồn/kho mapping; không bịa mã/ID.

**S2 — Hoàng Đông, phạm vi Ninh Bình mới: primary xác nhận phối hợp partial/remainder, chưa chọn ngày event lifecycle.** [Primary NQ1674](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/6/1674-nq.signed.pdf), Điều 1.101, **trang 7**, nêu “**một phần diện tích tự nhiên, quy mô dân số của phường Hoàng Đông**” cùng Duy Minh/Duy Hải thành phường mới **Duy Hà**; Điều 1.109, **trang 8**, nêu “**phần còn lại của phường Hoàng Đông sau khi sắp xếp theo quy định tại khoản 101 Điều này**” cùng các thành phần khác thành phường mới **Hà Nam**. Cross-reference nối cùng Hoàng Đông; không suy whole cho từng nhánh hoặc thêm mã/huyện cũ. Không gộp các phường Quang Trung khác nơi trong văn bản.

- Điều 2.1, **trang 9**: “**Nghị quyết này có hiệu lực thi hành từ ngày được thông qua.**” Cuối **trang 10** ghi thông qua **16/06/2025**, nên đó là ngày hiệu lực văn bản. Điều 2.2, **trang 10**, quy định chính quyền mới “**chính thức hoạt động từ ngày 01 tháng 7 năm 2025**”; Điều 2.3 giữ chính quyền cũ “**tiếp tục hoạt động cho đến khi chính quyền địa phương ở đơn vị hành chính cấp xã hình thành sau sắp xếp chính thức hoạt động**”. **Không chọn một `effective_on` giữa 16/06 và 01/07 cho partial + kết thúc identity khi chưa xác nhận phạm vi ngày**; không dùng ngày ký điện tử VGP 18/06 hoặc ngày tải Bando 04/10/2026 làm ngày sự kiện.
- Mapping local chỉ có **đích hiện hành**: Duy Hà `unit:bando:0e916e58168e7dc1ad6bef5e` (row `diaphanhanhchinhcapxa_2025.2769`), Hà Nam `unit:bando:2ea7f7d3c756c7955b4dcd0b` (row `diaphanhanhchinhcapxa_2025.2789`). Observations tương ứng `observation:24b1935cfd7712ca:unit:bando:0e916e58168e7dc1ad6bef5e` và `observation:24b1935cfd7712ca:unit:bando:2ea7f7d3c756c7955b4dcd0b` giữ câu Bando và link NQ1674. **Mentions/events tương ứng vẫn pending**; mention `resolved_unit_id=null`, event `effective_on=null`, `territory=partial`. Historical Hoàng Đông chưa mapped; không nâng observation hiện hành hoặc mention nhiều tên thành identity lịch sử đã xác nhận. Source IDs/snapshot/record details xem ledger bổ sung trong References.

**S3 — control whole-only, không là proof partial.** [Primary NQ1286](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/1286-qh.signed.pdf), Điều 1.14.a, **trang 8**, thuộc quận Đống Đa, Hà Nội: “**Nhập toàn bộ diện tích tự nhiên là 0,24 km², quy mô dân số là 13.283 người của phường Trung Phụng vào phường Khâm Thiên.**” Hiệu lực **01/01/2025** theo Điều 2/trang 11, ban hành 14/11/2024. Không dùng whole merger này chứng minh partial cùng ngày; không suy Khâm Thiên mới thành lập. Chưa mapping historical unit_id Trung Phụng/Khâm Thiên với NQ1286; mention Bando sau này chứa tên Khâm Thiên vẫn chưa resolved, không thay bằng mapping lịch sử.

**S4 — NQ52/NQ-CP: lead literal giải thể, primary/ngày hiệu lực UNRESOLVED.** [Bài Báo Chính phủ đăng 16/10/2009 15:49](https://baochinhphu.vn/thanh-lap-thi-tran-thong-nhat-tinh-thanh-hoa-10227967.htm), đoạn sau ảnh, viết “**giải thể thị trấn nông trường Thống Nhất trên cơ sở chuyển giao toàn bộ 2.775,06 ha diện tích tự nhiên và 6.619 nhân khẩu**” về 10 xã thuộc Yên Định, Ngọc Lặc, Cẩm Thủy, Thọ Xuân, Thanh Hóa; cuối bài dẫn NQ52/NQ-CP. Đây là bài báo, **không phải toàn văn nghị quyết**. Chưa có primary/điều hiệu lực, ngày ban hành hoặc mapping historical unit_id/event_id. **Không lấy 16/10/2009 ngày đăng báo làm ngày hiệu lực.** Đoạn lập thị trấn Thống Nhất từ phần của Yên Giang/Yên Lâm/Yên Tâm/Cao Thịnh/Quảng Phú là các **nguồn khác**; không suy chúng là partial của chính thị trấn nông trường bị giải thể, không gộp identity cũ/mới vì tên gần giống.

### Quan sát runtime và phần còn chờ

- Investigation mới đã thực chạy **17/10/2026**, command `python _bmad-output/tmp/issue-27-administrative-same-day/runtime_probe.py`, exit 0; [JSON retained](../tmp/issue-27-administrative-same-day/runtime-proof.json), captured `2026-10-17T04:01:46.230581+00:00`. Gọi **validator thật** trên `notary_v2/data/administrative_units/ledger.json` kèm folder snapshots: valid, **3355 units/3219 events, tất cả 3219 pending**, effective_dates_known=0. Đây là baseline của lần validator đã chạy, không là audit mới hoặc xác nhận lịch sử.
- Các nhãn **synthetic, không phải lịch sử/pháp luật**: partial A→B + whole abolish A cùng ngày **accept** cả khi đảo array; reciprocal partial A→B→A khác ngày **accept** nhưng **không chứng minh cùng ngày**; whole transfer + abolish cùng ngày, partial abolish và dùng A sau ngày kết thúc **reject**. Partial vào A cùng ngày abolish A cũng accept — chỉ ghi giới hạn acceptance hiện tại, không kết luận hợp pháp. Không sửa real data/permanent test/appcode; không suy array order thành thứ tự nội ngày.
- **Thiếu chính xác:** primary **NQ52/NQ-CP mà bài Chính phủ 16/10/2009 dẫn**, gồm điều giải thể/phân giao của chính thị trấn nông trường và điều hiệu lực; **và/hoặc** owner/curator/người có chuyên môn xác nhận có nguồn cách đọc S1 về identity-ending so với literal abolish, cùng phạm vi ngày lifecycle S2 nếu dùng để curation. **Ngày xác nhận: `null`**; chưa có owner/expert legal confirmation. Không tạo quyết định phê duyệt pháp lý mới.
- **Người nhận:** Main → owner/curator/người có chuyên môn. AC3 cho phép ghi thiếu nguồn chưa giải quyết; phần nghiên cứu hữu hạn đã hoàn tất, không cần hỏi owner “chọn thuật toán” lúc này. **Chỉ đề xuất đổi quy tắc thời gian cụ thể tương lai chờ nguồn/xác nhận**; #12 OCR độc lập, app hiện hành không đổi thuật toán. Không áp luật cấm toàn bộ cùng ngày, không thêm act grouping/thứ tự nội ngày/schema/migration.
