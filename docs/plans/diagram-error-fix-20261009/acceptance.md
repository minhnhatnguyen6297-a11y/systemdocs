# Checklist để worker chứng minh bản sửa chạy đúng

**Dùng với:** `../plan-diagram-error-fix-20261009.md`. Tất cả dữ liệu thử là dữ liệu giả.

Stage là bảng Người/Tài sản đang nhập. Toast là thông báo nổi. Banner là dải thông báo trong màn hình. Alias là tên biến riêng trỏ tới một hàm đã có.

Harness là script mở app và thao tác tự động để kiểm tra. DOM là cây phần tử đang hiển thị. IPC là đường gửi lệnh từ màn hình qua phần xử lý của Electron.

## 1. Chuẩn bị và bảo vệ công việc đang có

1. Làm trong checkout được giao; đọc AGENTS.md tại đó và `C:/Users/MINH/.codex/RTK.md`.
2. Ghi HEAD đầy đủ, branch, `git status --short`. Không reset/stash/dọn file.
3. Source chính cần sửa là `shell/src/renderer/notary/relationship-diagram.js`. Nếu đang có chỉnh sửa của người khác tại source này hoặc file test mới, không ghi đè. Chọn worktree Orca nếu cần tách; chỉ đọc evidence từ D:/systemdocs.
4. Ở lúc lập plan, ba tài liệu có thay đổi sẵn: `deferred-work.md`, `decision-76-visual-bug-spike-mot-app-duy-nhat-dev-gate-khong-tach-app-dev-rieng.md`, `plan-visual-bug-reporting-spike.md`. Kiểm lại trạng thái hiện tại; không stage chúng vào commit của task này.
5. Đọc `docs/specs/notary_v2/README.md` §2/§5, `diagram/README.md`, contract §7.4/§7.5 và §13. Không dùng tài liệu Draft về đồng bộ sơ đồ để đổi behavior.

## 2. Viết test mới trước khi sửa

File dự kiến: `shell/test/notary-diagram-errors.test.mjs`.

- Dùng `node:test`, `node:assert`, `node:vm`, source thật từ filesystem và `shell/test/dom-stub.mjs` đã có. Không thêm framework/dependency.
- Mỗi test tạo môi trường mới. `window` phải tồn tại khi nạp catalog và sơ đồ; nạp đúng thứ tự trong index.html.
- Catalog phải là source thật. Kiểm tra `typeof window.G1_NOTARY_ERRORS.errText === 'function'`; không tự tạo export `.relErrText` vì sẽ che lỗi.
- Chỉ thay client trả kết quả giả; không sửa lời trả lời kỳ vọng để hợp với source lỗi.
- Dựng pane/view thật; dùng nút từ cây DOM. Kiểm tra nút đủ điều kiện bật trước khi gọi callback trong DOM giả.
- Ca đánh giá/lưu: ghi nhận `notify` và so nội dung với `G1_NOTARY_ERRORS.errText(error)`, tham số đánh dấu lỗi là `true`.
- Ca render: kiểm tra chữ lỗi xuất hiện cùng card sơ đồ trong cây DOM, không chỉ gọi `model.evaluateDiagram()` thành công.
- Có ít nhất một ca đi qua model thật và cập nhật view thật; `model.emit()` hiện nuốt exception của subscriber nên state đúng chưa đủ.
- Giữ ca Node không có window/catalog để chứng minh đường fallback không bị mất. Đây là ca phụ, không thay ca browser catalog.

Chạy test mới trên source chưa sửa. Lưu log thất bại đúng TypeError ở ba nơi. Sau đó sửa một thuộc tính và chạy lại **cùng test, cùng kỳ vọng**. Nếu ca trước sửa không bắt được lỗi, sửa cách nạp test trước, chưa được coi là đã có test chống tái phát.

Node VM không mô phỏng hoàn toàn quy tắc trùng khai báo giữa nhiều script của Chrome. Dùng test static đã có và Electron native để chặn trường hợp đổi tên alias sai.

## 3. Các ca cần kiểm tra

| Mã | Given / chuẩn bị | When / hành động | Then / quan sát bắt buộc | Nơi chứng minh |
|---|---|---|---|---|
| C01 | Catalog thật đã nạp; evaluate trả `stage_validation_error` | Bấm `Xem cách tính` | Một toast đúng catalog; callback hoàn tất; không TypeError; model không còn busy | Test mới + Electron |
| C02 | Người mẫu đã gán; client evaluate trả lỗi C01 | Thao tác bỏ gán hoặc chọn chip làm lịch tự đánh giá chạy | Hết debounce có lời lỗi đúng; không `unhandledrejection`; không chỉ gọi thẳng hàm đánh giá | Electron |
| C03 | Model trả `diagram_invalid_state`, `details.errors` có mã/điệp lỗi | Bấm đánh giá; view dựng lại qua subscribe | Lỗi dưới sơ đồ; `.cd-rel-card` và bảng Stage còn hiện; không toast riêng | Test mới + Electron |
| C04 | Hồ sơ có caseId, writable, diagramDirty; nút save bật | Cho command save trả `workspace_locked` sau khi bấm | Toast đúng catalog; chưa lưu vẫn còn; Stage/Diagram và revision không bị sửa như save thành công | Test mới + Electron |
| C05 | Diagram draft chưa hợp lệ | Save trả `diagram_invalid_state` | Hiện lỗi dưới sơ đồ; không toast riêng; không mất draft; không tăng revision | Test mới |
| C06 | Diagram dirty, base revision cũ; response có `details.server_revision` | Save trả `workspace_conflict` | Luồng xung đột hiện có được giữ, không toast riêng, không ghi đè | Test mới; test model/view có sẵn |
| C07 | State hợp lệ, client trả render_model thành công | Đánh giá sơ đồ | Không toast lỗi; giữ render_model/requiredSlots hợp lệ; evaluate không ghi DB | Test mới hoặc test cũ đúng đường chạy + Electron |
| C08 | Fixture ready, sửa Diagram hợp lệ | Lưu sơ đồ, mở lại | Revision tăng một lần; dirty được xóa sau thành công; state mở lại đúng lựa chọn đã lưu | Test round-trip cũ + Electron/IPC thật |
| C09 | domain two_party | Thao tác gán/bỏ gán | Không gọi engine evaluate thừa kế; 30 vị trí còn nguyên | Test cũ + lượt nhìn kiểm tra Electron |
| C10 | Stage đã sửa nhưng chưa Cập nhật trên case đã lưu | Xem trạng thái evaluate/save | Giữ khóa hiện có; không vượt qua stageGate để ép test chạy | Test cũ; nếu thiếu thì bổ sung ca ngắn |
| C11 | Không có window/catalog khi require độc lập | Dựng lỗi bằng pane test | Fallback còn hoạt động; không ReferenceError | Test mới |
| C12 | Catalog và sơ đồ nạp như index.html | Mở module sau reload | Export sơ đồ tồn tại; không lỗi trùng tên errText/module_missing | Test static + Electron |

Các ca đã có test đủ tốt chỉ cần dẫn tên test/lệnh và kết quả; không viết lại để tăng số lượng. Khi lỗi thất bại, so Stage/Diagram trước và sau; bấm đóng thông báo vẫn phải tiếp tục thao tác được.

## 4. Harness Electron trong app thật

File tạm worker tạo: `docs/tmp/diagram-error-fix-20261009/electron-check.cjs`.

### Môi trường

- Khởi chạy `<checkout>/shell` bằng `<checkout>/shell/node_modules/electron/dist/electron.exe`; giữ entry `src/main/main.js` và `index.html` thật. Không tạo Electron product/main/index riêng.
- Dùng Playwright `_electron` đã có trong `D:/systemdocs/notary_v2/venv/Lib/site-packages/playwright/driver/package`, sau khi xác minh đường dẫn. Nếu đã có đường dẫn hợp lệ tương đương thì dùng nó; không cài mới chỉ để chạy một check.
- Chuyển `userData`, `G1_NOTARY_DATA_DIR`, `G1_UPLOAD_DATA_DIR`, `G1_OUTPUT_DIR` vào thư mục tạm riêng trong evidence. Đặt `G1_DEV_NOTARY_MOCK=1`, `G1_PYTHON` tới interpreter phù hợp, engine root tới checkout đang sửa. Gỡ `ELECTRON_RUN_AS_NODE` khỏi env khi launch.
- Không đụng profile/DB đang dùng của người dùng. Không dùng cửa sổ đang mở sẵn. Đóng instance thử và dọn timer/listener của harness khi kết thúc.
- Giữ sandbox, contextIsolation và webSecurity; không sửa CSP hoặc bật DevTools/CDP trong production.

### Cách gây lỗi có kiểm soát

Lỗi C01/C03/C04 có thể được trả qua `client.run` giả **chỉ trong harness**, trong khi pane/view/catalog vẫn lấy từ source thật đã nạp vào cửa sổ app. Không cần và không được tạo nút/test hook mới trong production.

Ưu tiên bắt model đang được view thật dùng bằng cách bọc factory `G1_NOTARY_MODEL.createModel` trong init script của phiên thử; giữ runner thật cho các command khác. Gây lỗi theo đúng command và đúng một lượt. Nếu dùng pane được dựng trực tiếp trong renderer để kiểm tra handler, ghi rõ đó là renderer với client giả; vẫn phải có lượt C08 đi qua màn hình app và IPC thật.

Trong mỗi ca: cài listener `pageerror`, `console.error` và `unhandledrejection` trước thao tác; chỉ kiểm lỗi thuộc ca đó. Không nối console còn giữ từ ca trước để suy nguyên nhân. Timeout có giới hạn; chờ điều kiện thật, không coi hết thời gian là thành công.

### Thứ tự lượt thử

1. Mở app, đợi engine ready, xác nhận module sơ đồ/catalog nạp được; ghi Electron/Chromium version.
2. Chạy C01–C04 với dữ liệu giả, lưu ảnh toàn màn hình có lời lỗi đọc được. Chờ lượt C02 chạy tự động thật.
3. Đóng lời lỗi, thực hiện một thao tác tiếp theo; xác nhận không đứng màn hình và dữ liệu nhập còn nguyên.
4. Mở fixture `ready` case 42 qua giao diện/command thật; sửa một lựa chọn Diagram hợp lệ, lưu, mở lại, đối chiếu C08. Snapshot dữ liệu fixture, không sửa file golden fixture.
5. Mở fixture `ready-two-party` case 48; kiểm tra 30 chỗ và C09. Không kiểm Word trong task này.
6. Tối thiểu lượt kiểm tra ở viewport 1280×800 và 1366×768: banner/toast đọc được, có thể đóng, nút còn bấm được. Đây là kiểm khả năng dùng sau lỗi, không đổi layout nếu chưa có triệu chứng và scope mới.
7. Reload và kiểm tra C12; kết thúc instance thử.

Mock fixture đi qua IPC thật là kiểm tích hợp Electron với mock sidecar, không phải chứng minh Python/database production. Bản sửa nằm ở renderer nên không yêu cầu sửa backend hoặc chạy toàn corpus Word.

## 5. Bằng chứng cần bàn giao

Lưu dưới evidence tạm:

- `before-fix.txt`: test mới thất bại đúng lỗi trước sửa.
- `after-fix.txt`: cùng test đạt sau sửa.
- `node-tests.txt`: test liên quan và bộ Node toàn shell, kèm exit code.
- `electron-check.cjs`: lệnh có thể chạy lại; tự tìm checkout từ vị trí file.
- `electron-results.json`: HEAD, runtime version, source/hash, từng mã Cxx, thao tác, backend thật/giả, pass/fail, lỗi console mới và file ảnh.
- Ảnh C01, C03, C04 và C08. Ghi rõ viewport và dữ liệu giả.
- `completion.html`: kết quả ngắn, file/commit, lệnh, hạn chế, link report còn mở.

Nếu native check không chạy được, ghi lý do và ca còn thiếu; giữ `in-progress` hoặc trạng thái chưa đủ nghiệm thu phù hợp. Không dùng 55 test xanh hoặc probe alias trong bộ nhớ thay cho kết quả source thật sau sửa.

## 6. Review, commit, phục hồi

1. Chạy test liên quan; khi đạt thì chạy `rtk npm test` một lần trong shell. Chỉ chạy lại khi có sửa mới hoặc kết quả còn nghi ngờ.
2. Review theo `bmad-code-review`, phạm vi diff của task; reviewer xem source và test, không đưa file bẩn của người khác vào diff. Nếu workflow cần agent, chỉ điều phối Orca.
3. `rtk git diff --check`; xem diff trước stage. Stage từng đường dẫn source, test và plan của task, không `git add .`.
4. Commit nhỏ, gợi ý `fix(notary): restore diagram error messages`. Không push/merge trong task này.
5. Nếu phải phục hồi bản sửa sau commit, dùng commit hoàn tác riêng chỉ cho thay đổi của task; không hard reset checkout có việc người khác.

**Đủ để báo sửa xong:** lỗi trước sửa bắt được, source thật sau sửa đạt, Electron đủ ca, draft không mất, ngoại lệ đúng, full Node suite/review đạt, evidence có thể chạy lại, 12 report vẫn mở.
