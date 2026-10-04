# Bàn giao toàn bộ lượt tiếp nhận Multica

**Ngày:** 04/10/2026, giờ Việt Nam · **Trạng thái:** bàn giao theo yêu cầu Owner.
Đây là record thực thi tổng hợp, không thay spec, Linear hay trạng thái Multica.
Đọc file này trước để tiếp tục; không cần khởi động lại các phần đã hoàn thành.

## 1. Bắt đầu ở đúng chỗ

- Checkout cần dùng: `C:/Users/MINH/.codex/worktrees/1aae/systemdocs`.
- Nhánh: `codex/multica-takeover`; HEAD khi chuẩn bị bàn giao:
  `4665e65c56f96a4fc00d2a51c4707b6c588da7ef`.
- **Có code địa chỉ và docs chưa commit. Không reset/clean hoặc checkout sang
  nhánh khác làm mất phần này.** Chạy `rtk git status --short` trước khi sửa.
- Default/main của repo là `consolidate/monorepo`, không phải `main`.
  14 commit worker đã vào nhánh này ở `6c07d89a65d4a62cdddee8ba40d25903c6139f18`.
  Các phần Word/timeline/DOCX sau đó nằm trên nhánh takeover; chưa gộp phần
  takeover hoàn chỉnh vào default, chưa push/PR.
- Nói tiếng Việt dễ hiểu. Đọc `C:/Users/MINH/.codex/RTK.md`, mọi lệnh shell
  đi qua `rtk`; lệnh cần output nguyên dạng dùng `rtk proxy`.
- Đọc `README.md` → `docs/spec/README.md` → README module/flow → spec feature.
  Không tạo một bộ spec/kiến trúc/nguồn dữ liệu song song.

Các worktree kiểm tại thời điểm bàn giao:

| Worktree | Nhánh/HEAD | Chỉ dẫn |
|---|---|---|
| `D:/systemdocs` | worker `agent/worker-nh-n-vi-c/1127ad7579d2`, `3fec5cba` | Giữ nguyên, có dữ liệu văn phòng |
| `.../.codex/worktrees/1aae/systemdocs` | takeover, `4665e65` | Tiếp tục ở đây |
| `.../.codex/worktrees/5d44/systemdocs` | detached `f6c62584` | Không tự xóa |
| `C:/Users/MINH/orca/workspaces/systemdocs/sterlet` | sterlet, `6c07d89a` | Không sửa thay checkout hiện tại |

## 2. Những quyết định Owner đã chốt — không hỏi lại

1. 14 commit worker là đúng, đưa vào nhánh chính và sửa docs khớp code.
2. Tiếp nhận toàn bộ task Multica; coding/kiểm định cục bộ. Không tự gửi
   message, đổi trạng thái issue hoặc kích hoạt run Multica trùng công việc.
3. **Nơi niêm yết theo `ngay_lap_ho_so`.** Ngày cấp giấy nguồn chỉ giúp đọc
   địa chỉ cũ/mới. Không thay ngày lập hồ sơ bằng ngày máy hoặc `created_at`.
4. Nơi cấp giấy khai tử tách riêng, đọc cơ quan ghi trên chính giấy ấy, theo
   ngày cấp giấy ấy. Không suy từ cư trú, nơi chết hoặc nơi niêm yết.
5. `https://sapnhap.bando.com.vn/` là nguồn chính tên xã/tỉnh hiện hành và bước
   tiền thân gần nhất. Không dựng huyện mới vì Bando không có danh mục huyện.
6. Chuẩn bị lịch sử nhiều bước A→B→C→D cho xã/huyện/tỉnh. Owner sẽ bổ sung
   các mốc cũ sau; **không đi thu thập lịch sử Nghị quyết/GitHub thay Owner lúc này**.
7. Ghi rõ cách mở rộng về sau vào docs. Giữ nguyên văn địa chỉ gốc, người dùng
   chọn gợi ý; không tự ghi đè giá trị đã nhập/xác nhận.

Mốc 01/07/2025 chỉ giúp đọc cấu trúc địa chỉ, không là ngày hiệu lực giả định
cho toàn bộ Bando. Một tên hiện tại tìm được chưa chứng minh đúng tại ngày
hồ sơ. Phải phân biệt danh mục hiện tại với lịch sử đã có nguồn/ngày xác nhận.

## 3. Trạng thái các issue

Trạng thái cột Multica bên dưới lấy từ bản xuất 03/10/2026 22:25, **không phải
trạng thái đã đọc lại trực tiếp lúc bàn giao**. Lượt này chưa đóng issue ngoài hệ thống.

| Issue | Trạng thái bản xuất | Kết quả/lỗ hổng của lượt tiếp nhận |
|---|---|---|
| NAIA-1,2,3,5,7,10,13,23 | Done | Kế thừa kết quả cũ; không tuyên bố đã kiểm lại toàn bộ |
| NAIA-6 / MIN-141 | In review | 14 commit đã gộp default; docs và regression tích hợp cập nhật; Owner nghiệm thu ngoài hệ thống còn riêng |
| NAIA-8,12 | In progress | Word engine/UI/migration đã hoàn thành và kiểm bản tích hợp; xem §4 |
| NAIA-11 | Canceled | Trùng scope NAIA-8; không mở lại |
| NAIA-4 / MIN-139 | Blocked | DOCX→JSON→Stage→Word gốc đã hoàn thành tại takeover; không còn chặn bởi uv ở phiên này |
| NAIA-9 | In progress | Kho timeline hoàn thành; consumer địa chỉ đang dở |
| NAIA-14 | In progress | Bando API và dữ liệu đầy đủ đã nghiên cứu/tải; acceptance lịch sử cũ đổi theo chỉ dẫn Owner |
| NAIA-15 | Blocked | Câu hỏi ngày đã được Owner giải đáp; code tích hợp ngày/nguồn chưa nghiệm thu |
| NAIA-16 | Backlog | Ledger/schema/history tooling hoàn thành; packaging consumer đang kiểm |
| NAIA-17 | Backlog | Parser/lookup local đã có code chưa commit, chưa root review |
| NAIA-18 | Backlog | Gợi ý niêm yết theo tài sản chọn rõ đang có code; chưa kiểm toàn luồng |
| NAIA-19 | Backlog | Gợi ý cơ quan cấp khai tử riêng đang có code; dữ liệu lịch sử thực tế còn thiếu |
| NAIA-20 | Backlog | Person/asset suggestions, chọn/áp dụng/bỏ qua đang có code; chưa nghiệm thu UI/race |
| NAIA-21 | Backlog | **Chưa hoàn thành:** review, kiểm toàn luồng và bàn giao địa chỉ cuối |
| NAIA-22 | Blocked | Online/offline sandbox mới chạy được; nguồn credential sai ngày03/10 và ổn định dài hạn chưa xác định |
| NAIA-24 | Blocked | uv dùng chung đã chạy trong cả hai sandbox; agent Multica mới nhận PATH/render BMAD chưa chứng minh |

## 4. Những phần đã làm xong và bằng chứng

### 4.1 Gộp worker và đồng bộ quy tắc

Đã kiểm 14 commit worker, gộp vào default ở `6c07d89a`. Giữ hành vi MIN-141:
dữ liệu người sống/chết, đất 1..20, xóa nháp có kiểm tham chiếu, thống kê,
metadata và revision. Spec hiện hành ở `docs/spec/notary_v2/stage.md`, README
module và contracts. Không sửa database văn phòng hoặc worker worktree.

### 4.2 Word — NAIA-8/12

- Hồ sơ hai bên 30 vị trí A/B; engine tĩnh, không tự đoán quy tắc pháp lý.
- Chọn thư mục mẫu, xuất nhiều văn bản, không ghi đè, giữ nháp nơi niêm yết.
- Migration bản sao DOC/DOCX, giữ package parts, xử lý Word COM/FlatOPC,
  token/alias/year/linebreak/xml-space và ba token Owner bỏ.
- Commit chính `a32c1fe`; bản sửa tích hợp `a94e3dc`.
- 22 mẫu Owner được kiểm trên **bản sao**: 22/22 saved; hash 22 nguồn không
  đổi. Word COM đọc nguồn/đầu ra, số trang khớp. So XML trực tiếp đạt17 DOCX;
  5 DOC là `not_verified` ở tầng XML. Chưa kiểm trực quan mọi trang hoặc
  native picker. Không gọi đây là nghiệm thu toàn bộ bản cài.
- Bằng chứng: `artifacts/word-integration-review-fixes-final-20261004/e2e_report.json`.
- Spec: `docs/spec/notary_v2/word-output.md`; records `.agent/tasks/NAIA-8/`.

### 4.3 Kho lịch sử xã/huyện/tỉnh — NAIA-9/14/16

- SOT dữ liệu: `notary_v2/data/administrative_units/ledger.json`.
- 3.355 đơn vị =34 tỉnh+3.321 xã+0 huyện; 35 snapshot bất biến có SHA-256.
  136 quan sát giữ nguyên,3.219 quan hệ đang chờ,161 dòng liên quan một phần.
  Ngày hiệu lực Bando vẫn null; không dựng danh tính cũ từ văn xuôi.
- Schema: `contracts/administrative-timeline/ledger.schema.json`;
  helper `notary_v2/administrative_timeline.py`.
- ID tách tên/mã/parent theo thời kỳ; nhiều đầu vào/đầu ra cho gộp/tách;
  rename/reparent/abolish; pending/confirmed và whole/partial/unknown.
- CLI validate/query/refresh/import/update; revision, khóa ghi, atomic write,
  raw hash và archive ledger trước sửa; refresh giữ lịch sử Owner bổ sung.
- API site dùng POST `/p.co_dvhc` body `ma=0`, POST `/p.co_bangbieu`
  body `ma=<malk tỉnh>`. Đã lấy34 bảng tỉnh. Excel do trình duyệt dựng bằng
  Tabulator/SheetJS; không tìm thấy file quốc gia tĩnh. API dùng bởi site,
  chưa có cam kết hỗ trợ API bên thứ ba.
- Commit cuối `a3b33dc4456aa1a694277ca283e4e00c7ea936dc`; root79 timeline+
  5 docs passed,1 docs skip vốn có;35hash/3355IDs và ledger gốc giữ nguyên.
- Spec `docs/spec/notary_v2/administrative-timeline.md` có hướng Owner thêm
  A→B→C→D, chia tách, xác nhận ngày/nguồn, nâng schema/database khi cần.
- Research scratch: `.agent/scratch/multica-address-research/bando-api-research.md`.

### 4.4 Nhập DOCX và xuất theo bản gốc — NAIA-4/MIN-139

- Đọc physical XML body/table/merged/nested theo thứ tự thật; giữ source spans.
  Không tự gán giới tính/vai trò hoặc thay mọi chuỗi giống nhau.
- Review nhiều người/tài sản/cụm đất, lỗi/null có bằng chứng; sửa xong mới
  đưa Stage; nguồn và bindings theo revision lưu cùng hồ sơ.
- UUID/hash nguồn, bản gốc bất biến, ghi atomically; slot dựa Stage/sơ đồ đã
  lưu. Giữ định danh cụm đất nguồn khi xóa/reorder; gỡ nguồn không xóa Stage.
- Snapshot JSON download đúng contract gốc; export thay đúng vị trí chọn,
  giữ phần XML/binary không đổi. Guard case/revision/late response/save failure.
- Sửa ngày ISO1/2chữ số, ngày không hợp lệ, dấu âm Unicode, số mũ không hỗ
  trợ, localized decimal và nguồn không đủ identifier. DOCX thường được hỗ
  trợ; Strict/field/hyperlink/tracked/textbox phức tạp có giới hạn rõ.
- Root review sáu lượt; plan đã built:
  `_bmad-output/implementation-artifacts/plan-multica-docx-intake.md`.
- Source cuối `17b5672c7f517d418aae06b42c1e723c148da1e1`; docs cuối `4665e65`.
- Root kiểm cuối: **413 backend passed,2 file-symlink skipped** vì quyền Windows
  (không phải Word COM);115 adapter/Intake/core passed;235 Node passed;
  78 contract examples đúng kỳ vọng. Trong backend60 DOCX tests đều chạy.
- Electron thật, engine/DB riêng,4 review cards,25 lựa chọn binding,save/reload,
  original export HS-9; nguồn và package parts không đổi,DB checkout không đổi.
  Native file picker là double trả path; không giả vờ đã kiểm cửa sổ chọn file thật.
- Bằng chứng `artifacts/docx-electron-20261004/startup-report.json`,
  `export/hop_dong_goc_HS-9.docx` cùng thư mục.
- Spec `docs/spec/notary_v2/input/docx-import.md`; records MIN-139.

### 4.5 Môi trường NAIA-22/24

uv0.12.19 ở `C:/Program Files/Systemdocs Tools/uv/uv.exe`, PATH cấp máy giữ
mục cũ. SHA-256 đối chiếu binary WinGet:
`F94EDDB81F3ADDCA6EF8F2361A70C3EDDE31ADCBD1000A55FC6674306AE0B1E7`.
Phiên Online/Offline mới đều đúng tài khoản, tìm uv và `uv run` Python thành
công;8h Security4625 sau kiểm không có lỗi mới. Chưa biết caller giữ mật
khẩu cũ ngày03/10; không sửa password/policy. Multica managed daemon chưa
restart, không tạo agent/run mới để tránh trùng. Xem hai progress records.

## 5. Phần địa chỉ đang dở — ưu tiên tiếp tục

Plan: `_bmad-output/implementation-artifacts/plan-multica-address-lookup.md`,
`in-progress`, baseline `4665e65`, review_loop_iteration0, chưa root review.

### Source/contract chưa commit

- `notary_v2/services/administrative_address.py`: parser phải→trái, aliases từ
  quan sát Bando, confirmed dated graph, cache theo file/revision; local-only.
- `notary_v2/tests/test_administrative_address.py`: synthetic history tách
  real Bando; sáu nhóm Ninh Bình chia tách, Lâm→Ý Yên,Yên Dương→Vũ Dương,
  same-version history edit,reload fail,isolated staged loader.
- `shell/sidecar/command_registry.py`, `notary_adapter.py`, `notary_mock_adapter.py`:
  `notary.address_lookup`.
- `contracts/notary-case-drafting/address-lookup.schema.json`, examples valid/
  invalid và `validate_examples.py` đang nối. Kiểm contract prose chưa xong.
- `shell/sidecar/stage_package_assets.ps1` và mới
  `stage_administrative_reference.ps1`: helper/schema/ledger/snapshots công khai,
  không copy officeDB/config/revision archives. Cần kiểm đường staging thật.
- `shell/src/renderer/notary/case-drafting-model.js`, `case-drafting-view.js`,
  `case-drafting.css`, `word-export-dialog.js`: debounce350ms, lựa chọn/apply/
  ignore, source/date/case guards, ô ngày lập hồ sơ, explicit posting asset,
  death issuer chỉ từ UBND đã nhập và apply disabled khi thiếu lịch sử có ngày.
- `shell/test/notary-address-lookup.test.mjs` và view tests đang viết.

Payload địa chỉ nguyên văn OR province+commune (+district optional), source_date/
target_date full ISO. Result status match/ambiguous/not_found/invalid_input;
candidate names/unit_id/historical/evidence; Bando observation_id/raw_phrase/
partial/old_parent_unconfirmed; dataset_version/revision và coverage.
**`match` không đồng nghĩa đã chứng minh lịch sử theo ngày.**

### Docs/records root đã sửa, cũng chưa commit

- Mới `docs/spec/notary_v2/administrative-address.md`, **Draft**;
  links cập nhật README module,Stage,Word,Input,timeline.
- `.agent/tasks/NAIA-9/progress.md`; mới progress NAIA-14..21.
- Plan có ownership/cache/date/package/UX notes. Không nâng Draft/đánh built
  trước khi đối chiếu actual source và root kiểm cuối.
-53 local doc links đã kiểm tồn tại; `git diff --check` đạt ở thời điểm kiểm.

### Còn phải làm

1. Thu/đọc báo cáo cuối coder dưới §8, kiểm full diff và files mới từ baseline.
   Không coi source đang viết là đã hoàn thành vì tên file đã có.
2. Chạy tests địa chỉ/IPC/schema/renderer và current Word/DOCX regressions.
   Kiểm staging thật chạy lookup trong cây riêng, không fallback về checkout.
3. Kiểm UI thật: sửa date/address lúc response chờ,switch case; manual issuer/
   posting được giữ; nhiều tài sản phải chọn rõ; split không tự chọn; apply
   giữ gốc và không lặp `(nay là ...)`;save/reload revision đúng.
4. Chạy đủ bốn review lenses BMAD, ghi mọi finding và triage; sửa lỗi có bằng
   chứng. Chưa có review findings địa chỉ được quyết định.
5. Khớp contract/spec actual behavior; ghi kết quả vào NAIA9/14–21; commit
   đúng owned files,không `git add .`; sau đó mới hoàn tất plan.
6. Gộp phần takeover đã kiểm vào default nếu tiếp tục chỉ thị Owner ban đầu;
   kiểm worktree sạch/xung đột trước thao tác. Không push hoặc PR tự động.

## 6. Cách chạy kiểm tra và chỗ tránh mất thời gian

Python có jsonschema:
`C:/Users/MINH/.codex/worktrees/1aae/systemdocs/.agent/scratch/multica-intake/schema-venv/Scripts/python.exe`.
Backend tests cũ dùng cwd `notary_v2`; address test mới import `notary_v2`
nên đọc cách coder chạy (thường từ root). `-p no:cacheprovider`, fresh basetemp
dưới `.agent/scratch/`; không dùng chung thư mục temp của process khác.

Node modules sẵn `D:/systemdocs/shell/node_modules`; đặt `NODE_PATH` bằng file
scratch `.ps1`, tránh `$env` bị outer PowerShell mở rộng. Scratch đã có
`.agent/scratch/verify-docx-final-node.ps1` (full notary suite) và
`.agent/scratch/check_address_doc_links.py`.
Examples: chạy Python môi trường trên với
`contracts/notary-case-drafting/validate_examples.py`.

Electron chuẩn bị **chưa chạy cho địa chỉ**:
`.agent/scratch/probe-address-electron.py --flow`, dùng
`D:/systemdocs/notary_v2/venv/Scripts/python.exe -X utf8`.
Harness reuse DOCX real IPC/main/preload/sidecar; copy Git-tracked engine vào
artifact riêng và dùng DB riêng. **Commit/track service mới trước khi chạy**,
hoặc sửa copy explicit source list an toàn; bản hiện tại không copy untracked.
Hướng kiểm: DOCX regression→Lâm apply→Gia Tân split→posting explicit asset→save/
reload. Có thể cần chỉnh locator theo actual UI; không mặc định harness đã đạt.
Output mới `artifacts/address-electron-20261004/`, không overwrite DOCX evidence.

Không chạy backend legacy imports trực tiếp vào officeDB/sourceworktreeDB.
Không xóa worktree/người dùng data. Trước recursive delete trong staging,
kiểm absolute target nằm đúng workspace/shell/build, dùng một PowerShell end-to-end.

`.pytest_cache` ở vài module và rendered BMAD
`_bmad/render/bmad-build/systemdocs-b0d75560fafa/4bb5da901e0435f85c16/`
bị AccessDenied. Không phải test failure; takeown không giải quyết. **Không
render lại BMAD** trong lượt này. Readable rendered full/thorough workflow:
`_bmad/render/bmad-build/systemdocs-b9299225dd5c/eaa2fc475dde637da078/`
(step-03/04/05 ngay thư mục, không có `steps/`). Các absolute path old checkout
trong đó cần resolve tương đương current checkout; review prompts cài ở
`C:/Users/MINH/.codex/skills/bmad-build/review-prompts/`.

BMAD một coder tại một thời điểm; bốn review trước triage; plan ghi baseline.
Reuse agent nếu available, nhưng sau bàn giao agent mới có thể đọc plan một
mình. Nếu pending_init kéo dài mà không có tiến triển, interrupt rồi followup
cùng agent từng giúp resume; không reset code đã có.

## 7. Giới hạn còn thật, không tự ghi “đã xong”

- Owner chưa cung cấp lịch sử cũ/ngày hiệu lực: không thể bảo đảm mọi địa chỉ
  đúng tại ngày quá khứ bằng chỉ Bando latest snapshot. Giữ coverage cảnh báo.
- NAIA-21 chưa nghiệm thu consumer; tests địa chỉ và UI đang hoàn thiện.
- NAIA-6 Owner acceptance và issue status bên ngoài chưa cập nhật.
- Word page-by-page/native picker, packaged clean-machine/upgrade/restore
  chưa được chứng minh (đã có smoke packaged trên máy dev — xem §8.1; còn
  thiếu máy sạch không dev-env và đường upgrade/restore); DOCX backup steps
  là hướng dẫn, không phải phép thử restore.
- DOCX deferred log có pre-existing reanalyse batch queue, filesystem hardlink
  compatibility chưa kiểm trên filesystem khác,corpus accuracy ngoài fixture.
  Xem `_bmad-output/implementation-artifacts/deferred-work.md`; không lặp lại
  việc defer hoặc sửa rare guards đã bị reject khi code/claim không đổi.
- NAIA-22/24: credential root cause/long-term stability/new Multica environment
  chưa xong. Không đổi password/policy để che lỗi,không restart daemon vô cớ.

Nguồn task gốc ở **checkout D:**:
`D:/systemdocs/.agent/tasks/Multica-tom-tat-issues.md` và
`Multica-toan-bo-issues.md` (24issues,227comments). Không có hai file này tại
checkout1aae. Digest scratch `.agent/scratch/multica-intake/NAIA-N-digest.md`.
Không commit nguyên bản export có thể chứa thông tin cá nhân/credentials.

## 8. Trạng thái coder lúc dừng bàn giao

Đã yêu cầu `/root/address_implementation` kết thúc thao tác đang chạy an toàn,
dừng mở rộng và báo files/tests/còn thiếu. Báo cáo cuối sẽ được chèn bên dưới
trước khi gửi Owner file này. Không có agent khác đang sửa sản phẩm.

### 8.1 Cập nhật lượt tiếp nhận (agent tiếp theo)

Lượt này hoàn tất kiểm chứng + vá sau review; chi tiết tại
`progress.md` (mục "tiếp nhận") và plan. Tóm tắt:

- **Đã verify end-to-end**: probe Electron thật pass (lookup → apply →
  save/reload → DB/DOCX gốc bất biến); 22+1 py address, 79 timeline,
  81 contract examples, 248 node, 5 scaffolding — tất cả xanh.
- **Bug thật đã vá**: ô gợi ý không refresh khi đang gõ (`refreshAddressBoxes`);
  ngày `dd/mm/yyyy` gõ lại y hệt giữ raw trong model → commit ở `blur`.
- **Review 4 lens chạy xong**: intent-alignment, test-gap, adversarial,
  completeness — findings đã triage; phần lớn vá ngay (contract §14, seam
  test, validator tighten, partial-history, issuer gate, ignore in-flight,
  prune state đổi case, idPrefix dialog, CSS token). Còn lại ghi deferred:
  DOM-level test phủ rộng (parent `stage_package_assets.ps1` flow test đã
  chạy ở lượt đóng gói 04/10 — xem dưới).
- **Contract/spec đồng bộ**: §14 + command thứ 10 + changelog; spec có mục
  lỗi/ngoại lệ và ghi kết quả probe thật.
- **04/10/2026 — kiểm đóng gói thật**: `stage_package_assets.ps1` có lỗi copy
  dir lồng (`services/services`) → đã vá; build full `electron-builder --dir`
  → `dist-app/win-unpacked`; smoke packaged qua CDP: sidecar `ready`,
  `notary.address_lookup` succeeded với coverage đúng (report:
  `artifacts/packaged-smoke-20261004/`). Chứng minh artifact chạy được trên
  máy dev — KHÔNG phải clean-machine.
- **Đã commit** `a83f993` + commit vá staging/records sau đó. **Chưa làm**:
  chưa push, chưa cập nhật Linear/NAIA-*; chưa gộp sang
  `consolidate/monorepo` — chờ Owner.
