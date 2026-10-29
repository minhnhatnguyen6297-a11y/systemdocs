# Mục lục nguồn chuẩn (docs)

Agent đọc [`STACK.md`](STACK.md) trước. Trang này chỉ trỏ tới nơi lưu; không chép lại nội dung.

| Cần gì | Nguồn chuẩn | Ghi chú |
|---|---|---|
| Thuật ngữ nghiệp vụ | [`glossary.md`](glossary.md) | Tra nhanh. Khi lệch, `business-rules.md` §1 và D-xxx thắng. Chỉ dùng thuật ngữ có ở đây. |
| Luật vs nghiệp vụ | [`business-rules.md`](../_bmad-output/specs/notary_v2/diagram/inheritance/business-rules.md) (cột "Lệch luật?"), [`legal-baseline.md`](../_bmad-output/specs/notary_v2/diagram/inheritance/legal-baseline.md) | Mỗi mục D-xxx ghi `Loại: luật · lệch nghiệp vụ · kỹ thuật`. `legal-baseline.md` là file duy nhất dẫn số điều luật; bản tóm tắt của agent, **chưa luật sư soát**. |
| Quyết định nghiệp vụ thừa kế | [`decisions/decision-80-…`](decisions/decision-80-so-quyet-dinh-nghiep-vu-thua-ke.md) (D-001…D-051) | Append-only. `D-041` ≠ `decision-41`. |
| Quyết định khác (hệ thống, quy trình, task) | [`../_bmad-output/decisions/`](../_bmad-output/decisions/), danh mục: [`decisions/README.md`](decisions/README.md) | Có ghi chú trùng số 76/77, regex-46/47/48. |
| Spec từng module | [`../_bmad-output/specs/`](../_bmad-output/specs/) (`notary_v2`, `notaryoffice`, `upload_lab`, `shared`, `ui`) | Luật sơ đồ: [`diagram-rules.md`](../_bmad-output/specs/notary_v2/diagram-rules.md). |
| Luật làm việc của agent | [`../AGENTS.md`](../AGENTS.md) | |
| Trạng thái task | GitHub Issues của repo | Không dùng Notion/file riêng cho task. |
| Thế nào là xong | [`definition-of-done.md`](definition-of-done.md), [PR template](../.github/pull_request_template.md) | |
| Màn hình / selector e2e | [`screen-map.yaml`](screen-map.yaml) | Sinh tự động. |
