---
id: 9
type: spike
title: "Kiểm chứng đường xuất Word thật và nguồn mẫu"
parent: none
covers: []
after: []
assignee: ""
refined: false
hitl: true
risk: medium
---

# Kiểm chứng đường xuất Word thật và nguồn mẫu

## Description

Lập đường nhập thử an toàn qua backend thật, picker native và đúng byte mẫu; kiểm nội dung Word thực. Một người thao tác UI native và kiểm trang mẫu đại diện; mock không thay nghiệm thu engine.

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
- tracking — _bmad-output/backlog/README.md, C08
- source — _bmad-output/specs/notary_v2/word-templates.md, §2.3–2.4, §3, §5
- source — _bmad-output/tmp/notary-word-recheck/template-evidence.md, §Evidence, §Synthetic smoke
- source — _bmad-output/implementation-artifacts/deferred-work.md, Word/picker, clean-install/restore and filesystem records

## Notes

- Tracking: C08; **answered 2026-10-16** (evidence complete with native/visual/clean-install/non-NTFS gaps identified; retained independent Quick t2 clean). No product implementation. #1 remains tracking only and is not run with this leaf.
- Risk: medium — Missing route-scope evidence could cause a false close of the Word export issue; this spike does not alter product data.
- Acceptance gap (2026-10-16): native packaged-route and Word visual evidence remain missing. This is an automation/host-capability gap, not a pending owner business decision. Đã kiểm bằng các ca tổng hợp cô lập; bằng chứng sau khi dừng app là ca 3 (xem nhãn ở mục Measured evidence). Clean install on another machine and non-NTFS remain unverified.
- Who is waiting (2026-10-16): operator/reviewer receives measured proof (native automation + Word-rendering capability) to finish the full route; the owner receives ONLY unresolved product choices — none currently. #24 không phải chờ các thiếu bằng chứng native/Word/cài sạch. This run makes no product decision. Record canonical decisions here if needed; no cleanup/retention policy is approved. Generic run-dev DOCX neither proves this route correct nor proves a defect.

### Measured evidence — 2026-10-16

- **Native picker (operator, isolated G1 PID `9196`):** reached G1-owned `Select Folder` HWND `4459518` (`#32770`). The folder-edit control exposed no UIA patterns and `SetFocus` failed; the foreground guard saw Orca PID `9604` and sent no keys. After `SetWindowText` + `BM_CLICK`, the actual app result remained `Downloads`, not the copied template folder. The helper’s [lines 28–35](../../.tmp/shortpaths/issue-9-word-route/select-native-template-folder.ps1) print `selected=$dest` (the requested path), without checking the returned directory. Automation did not navigate/commit the target; the exact control failure is unresolved. No export followed and no native retry is planned. This is not proof of a Word-opening product bug. See [stall diagnosis](../tmp/issue-9-word-route/stall-diagnosis.md) and [owned G1 DOM capture](../tmp/issue-9-word-route/evidence/owned-g1-dom-state.json).
- **Direct service batch (operator):** `notary_v2.services.word_batch_export` on isolated synthetic case 1 exported both copied templates; both ready, 2 saved, 0 failed/skipped, no unresolved square-bracket tokens. This bypassed packaged renderer command transport and the native picker. PCDS source/copy SHA-256 `675F46D00BF795B5AB54801FF090B734856CD7770F5CF8E801F5FD397F19E0A5`; custom source/copy SHA-256 `60B057347FFE4B5EB4FE47EA17C73E49F897464F342AD0517AE63171442E56C4`; both unchanged. Outputs: `1_PCDS_HS-1.docx` SHA-256 `97e0b81ed833f9158f5cf8e7c7debc7208fe3e0e50de4cccf88917149481bb51`; `20260320_111543_e39fbc7d_HS-1.docx` SHA-256 `862ca885b0aafd29cfc30ac21f0f6f483fe639371192ed756ac3ffcff9cb54d8`. See [service batch JSON](../tmp/issue-9-word-route/evidence/service-batch.json).
- **Word render (operator, owned synthetic instance only):** PID `16344` was closed gracefully after guarded COM `Documents.Open` exceeded 120 s; `ExportAsFixedFormat` was not reached. No PDF/page images or visual inspection; no user Word touched. See [render JSON](../tmp/issue-9-word-route/evidence/word-com-render.json).
- **Paired restore — case 2 (operator, synthetic fixture; INITIAL/HISTORICAL record, not the authoritative after-stop proof):** reused `notary_v2/tests/test_docx_word_first.py`’s `fixture_bytes`/`extraction`/`reviewed_case` pattern and row helpers; created case 2 with one supported saved binding. Owned G1 instance closed gracefully and no direct child process remained; then the isolated SQLite DB + complete `docx_sources` tree were backed up/restored together. Backup and restored DB SHA-256 both `2c146d2af256f4aeb07dcfb1a767164c9bfefe0c71ade6a5ba54fb55b1ac4eb8`; both integrity checks `ok`; every source-store file hash matched. Restored service reopened revision 2 with the saved binding and exported `hop_dong_goc_HS-2.docx` (37,972 bytes, SHA-256 `08c09bea33a3593f45e3adfa24fd6dadf969cd543f88e192ddd7813d26f70b69`); the one bound synthetic occurrence changed from `ISSUE9 SOURCE HOLDER` to `ISSUE9 SAVED VALUE`, leaving one unbound source occurrence intact. See [paired-restore JSON](../tmp/issue-9-word-route/evidence/paired-restore.json).
- **Post-stop service create/bind/export — case 3 (operator; AUTHORITATIVE after-stop proof):** after that instance exited, created and bound synthetic case 3 using `CaseWorkspaceService.create`/`commit_stage` with the same proven fixture pattern, then backed up/restored DB + `docx_sources` and reopened/exported through the service. Backup/restored DB SHA-256 `8bc2be6142a4259acfd529cf601c76c3a6aedd951966241a60b52a4590319f75`; both integrity checks `ok`, all 8 source-store files matched. `hop_dong_goc_HS-3.docx` saved (37,978 bytes, SHA-256 `9610ca8213f6a00885753367864e01c0de98b9ce89c76b39140ea5f2943fdf98`) with the single bound synthetic value visible once. See [after-stop evidence](../tmp/issue-9-word-route/evidence/after-stop-service-restore.json).
- **Host/reviewer limits:** all mounted volumes observed on this host were NTFS; no non-NTFS test volume was available. No clean install on another machine, native route, or Word page-render check is established. The #9 plan is `in-review`, with native acceptance incomplete; parent/independent Quick review is required before any commit.
