# Bản đồ tri thức dự án

**Một cửa vào để biết đọc gì và ghi vào đâu.** Trang này chỉ định chủ sở hữu
tài liệu; không chép lại quy tắc nghiệp vụ, công thức hay danh sách quyết định
thành một SOT thứ hai. Trạng thái trong file được dẫn quyết định file đó có được
dùng làm quy tắc hiện hành hay chỉ là bản nháp/lịch sử. Linear quản lý task;
`.agent/tasks/` là dấu vết thực hiện, không phải spec sản phẩm.

> Giữ lại phần "Tại sao?" cho các quyết định, mỗi lần tôi giải thích - là 1 chi
> tiết tinh tế, kiến thức ngách của ngành mà không hệ thống hoặc tài liệu chung
> chung nào nhắc tới, không nên để những kinh nghiệm, đúc kết đó mất đi.
>
> — Owner, yêu cầu MIN-134 ngày 28/09/2026.

## 1. Tầm nhìn chung và định hướng sản phẩm

**Câu hỏi của phần này:** Hệ thống giải bài toán gì, bốn phần phối hợp ra sao,
dữ liệu nào được trao đổi, và điều gì phải do con người quyết định?

| Hạng mục | Mở file để đọc và sửa | Phạm vi của file |
|---|---|---|
| Mục tiêu, nguyên tắc và điều cố tình không làm | [VISION.md](VISION.md) | Định hướng toàn hệ thống; không mô tả chi tiết màn hình hoặc công thức nghiệp vụ |
| Ranh giới sản phẩm, ai sở hữu dữ liệu nào, flow trao đổi giữa các phần | [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Kiến trúc xuyên module; hành vi bên trong do module sở hữu |
| Vai trò và hiện trạng từng sản phẩm | [PROJECTS.md](PROJECTS.md) | Tổng quan để định tuyến; không chép spec sản phẩm vào đây |
| Công nghệ, ranh giới Electron/Python và điều kiện chọn thêm công nghệ | [TECH_STACK.md](TECH_STACK.md) | Quyết định kỹ thuật dùng chung; cần đối chiếu code khi hỏi hiện trạng chạy thật |
| Định danh và giao tiếp giữa module | [contracts/README.md](../../contracts/README.md), [entities.md](../../contracts/entities.md) | Contract chung; không tự suy CCCD trùng là cùng hồ sơ |
| Giao diện chung của shell Electron | [UI README](../product/ui/README.md) → `DESIGN.md`, `EXPERIENCE.md`, `tokens.json` | Thị giác và thao tác chung; không chốt nghiệp vụ của Notary hoặc Upload Lab |
| Câu hỏi còn mở hoặc quyết định xuyên sản phẩm đã có từ trước | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Đọc trạng thái trước khi dùng; quyết định mới chỉ thuộc một module phải ghi ở module đó |

**Flow cấp hệ thống:** nguồn tài liệu/tin nhắn/dấu vết → phần sở hữu tiếp nhận →
dữ liệu có nguồn gốc và trạng thái → con người kiểm tra/xác nhận → phần khác
chỉ nhận qua contract đã chốt. Đây là định hướng; flow cụ thể ở ba phần dưới.

**Quyết định cần mở trước:** [VISION.md §2](VISION.md) giữ nguyên tắc “máy đề
xuất, người xác nhận”; [SYSTEM_ARCHITECTURE.md §2](SYSTEM_ARCHITECTURE.md)
phân quyền sở hữu dữ liệu; [TECH_STACK.md §2](TECH_STACK.md) đặt điều kiện khi
chọn công nghệ mới. Khi quyết định chỉ ảnh hưởng một module, chuyển tới phần
module dưới đây thay vì viết kết luận nghiệp vụ vào tài liệu cấp hệ thống.

## 2. Soạn thảo tự động — `notary_v2`

**Mục tiêu:** hướng tới soạn thảo hồ sơ và sinh văn bản tự động, với dữ liệu và
quy tắc nghiệp vụ có thể kiểm tra trước khi người dùng xác nhận. [Cửa vào của
module](../../notary_v2/docs/README.md) phân biệt domain nghiệp vụ với năng
lực dùng chung. Không coi flow đích là bằng chứng mọi bước đã nối và chạy xong.

**Flow chính cần đặc tả:** nhận giấy tờ/chữ OCR → bóc tách và đối chiếu → người
dùng sửa/xác nhận → dựng hồ sơ/quan hệ → tính quy tắc của loại hồ sơ → dựng
placeholder và xuất Word. Mỗi mũi tên phải có nguồn dữ liệu, bước xác nhận và
trạng thái rõ ràng trong file sở hữu bên dưới.

| Hạng mục | File sở hữu | Trạng thái/ràng buộc cần đọc |
|---|---|---|
| Nhận giấy tờ, OCR, phân loại và bóc trường | [Document Intake](../../notary_v2/docs/platform/document-intake/README.md) → `spec.md`, `property-rules.md` | Đọc README để phân biệt hiện hành với thiết kế đích |
| Chữ OCR thô từ Zalo đưa vào Soạn hồ sơ | [Zalo snapshot README](../../zalo/README.md), [Zalo Inbox README](../../notary_v2/docs/platform/zalo-document-inbox/README.md) | `D:\zalo-intake` là repo gốc của engine; `zalo/` chỉ là snapshot, Notary sở hữu phần nhận và dùng dữ liệu đã Sync |
| Không gian soạn hồ sơ, Stage/Pool và thao tác người dùng | [Case Workspace](../../notary_v2/docs/platform/case-workspace/README.md) → `drafting-tab.md` | SOT hành vi tab Soạn hồ sơ nằm trong module; UI chung chỉ quyết định kiểu trình bày |
| Quy tắc của từng loại hồ sơ; hiện có thừa kế | [Inheritance](../../notary_v2/docs/domains/inheritance/README.md) → `workflow.md`, `spec.md` | `workflow.md` ghi hành vi quan sát được; `spec.md` tính thừa kế còn là **draft**, chưa thành quy tắc duyệt |
| Sinh văn bản và mẫu Word | [Document Generation](../../notary_v2/docs/platform/document-generation/README.md), [Word export thừa kế](../../notary_v2/docs/domains/inheritance/word-export.md), [placeholder mapping](../../notary_v2/word_templates/placeholder_mapping.md) | Mapping chỉ là danh mục đầu ra Word của phạm vi đang mô tả, không phải từ điển dữ liệu Người hoàn chỉnh |
| Giao diện riêng của tab Soạn hồ sơ | [visual-design.md](../../notary_v2/docs/platform/case-workspace/visual-design.md) | Phần nhìn riêng của module; thao tác chung ở UI README mục 1 |

**Quyết định và “tại sao”:** quy tắc thừa kế ghi trong tài liệu domain; cơ chế
tiếp nhận/soạn thảo/Word dùng chung ghi trong platform tương ứng. Quyết định
kiến trúc có đánh đổi lớn dùng [ADR của Notary](../../notary_v2/docs/architecture/README.md).
Trước khi đổi phân loại người nhận/người từ chối hoặc cách dựng Word, mở
[word-export.md §2 và §6](../../notary_v2/docs/domains/inheritance/word-export.md)
và trạng thái của [Inheritance README](../../notary_v2/docs/domains/inheritance/README.md).
Không tạo thêm `decision_index.md`, `flow.md` hay `ux.md` để lặp lại cùng một
quy tắc; nếu cần tách file, README của đúng module phải nói rõ file mới sở hữu
điều gì và file cũ không còn sở hữu điều gì.

**Khoảng trống phải giải cùng owner:** chưa có từ điển dữ liệu **Người** được
duyệt đủ để trả lời cho từng trường: ai nhập/nhìn/sửa, lấy từ giấy tờ hay tính
ra, công thức và điều kiện áp dụng, lưu hay chỉ dựng lúc xuất, placeholder nào
dùng, ngoại lệ và **tại sao**. Không suy ngược các câu trả lời này từ code hay
placeholder. Chọn nơi ghi trong domain/platform sau khi xác định phạm vi dùng
chung của trường; chưa tự tạo một spec song song.

## 3. Số hóa tài liệu sẵn có — `upload_lab`

**Mục tiêu:** đọc các hồ sơ Word đã được chuyên viên soạn để số hóa và chuẩn
bị nhập lên CSDL công chứng. [Upload Lab README](../../upload_lab/README.md)
lưu lý do xuất phát B1: phần mềm quản lý hiện có không có API lấy dữ liệu,
nên phải trích từ file Word công việc thật. Nếu điều kiện này thay đổi, hỏi lại
owner.

**Flow chính:** Word `.doc`/`.docx` → trích trường có nguồn → đối chiếu sổ Excel
trên web → phân loại hàng đợi → mở form và điền sẵn → người dùng kiểm tra, tự
bấm Lưu → ghi nhận kết quả. [README của Upload Lab](../../upload_lab/README.md)
§1–2 sở hữu flow nghiệp vụ và trường web form; không lấy flow soạn thảo hồ sơ
mới của `notary_v2` áp cho tài liệu cũ.

| Hạng mục | File sở hữu | Ranh giới |
|---|---|---|
| Đọc Word, nhận diện loại văn bản, bóc trường, đối chiếu và hàng đợi | [Upload Lab README](../../upload_lab/README.md) §1–2; [regex-rules.md](../../upload_lab/docs/regex-rules.md) | README giữ flow/ý nghĩa; catalog regex giữ quy tắc nhận diện chi tiết |
| Đăng nhập web, chuẩn bị form và nhận biết lần Lưu do người dùng thực hiện | [handoff-login-handshake.md](../../upload_lab/docs/handoff-login-handshake.md) | Không biến tự điền thành tự bấm Lưu |
| Hành vi hai tab Electron | [spec_UI.md](../../upload_lab/docs/spec_UI.md) | Hành vi/bố cục của Upload Lab; [visual-design.md](../../upload_lab/docs/visual-design.md) chỉ là lớp nhìn riêng |

**Quyết định và “tại sao”:** bổ sung vào mục sở hữu trong README hoặc file
chi tiết tương ứng; chỉ dẫn tới [contract Upload](../../contracts/upload-workflow.md)
nếu thay đổi giao tiếp với shell. Không mở thêm spec UI hoặc quyết định song
song với các file trên. Hai điểm cần đọc trước khi đổi flow: lý do nguồn Word
B1 và điểm dừng để người dùng tự Lưu trong
[Upload Lab README §1](../../upload_lab/README.md).

## 4. Quản lý vận hành — `notaryoffice`

**Mục tiêu:** nhận biết hồ sơ đang được xử lý trong văn phòng từ dấu vết công
việc, hỗ trợ tra cứu và theo dõi, không tự coi suy đoán của máy là hồ sơ đã xác
nhận. Hiện module có [intent.md](../../notaryoffice/intent.md) và **chưa có
runtime**; các flow dưới đây là thiết kế, không phải tính năng đã chạy.

**Flow chính dự kiến:** dấu vết từ Word/in ấn/nguồn được phép → bản ghi bằng
chứng → ứng viên hồ sơ → chuyên viên xác nhận → trạng thái vận hành và tra cứu.
[intent.md §3–4](../../notaryoffice/intent.md) mô tả tình huống thật và nguồn
bằng chứng; §6–9 mô tả pipeline, mô hình dữ liệu, bước duyệt và giao diện.

| Hạng mục | File sở hữu | Trạng thái/ràng buộc |
|---|---|---|
| Bài toán vận hành, ví dụ thực tế và ranh giới quyền riêng tư | [intent.md](../../notaryoffice/intent.md) §1–3 | Kinh nghiệm ngành và lý do chọn phương án phải ở đây cùng lời gốc của owner |
| Nguồn dấu vết, bằng chứng, ghép ứng viên và duyệt | [intent.md](../../notaryoffice/intent.md) §4, §6–8 | Không nâng ứng viên thành sự thật khi chưa có bước xác nhận |
| Tra cứu, trạng thái và các quyết định tiên quyết | [intent.md](../../notaryoffice/intent.md) §9–10 | §10.1 sở hữu A1–A4; A1/A3/A4 còn cần đo thực tế, không tự chốt từ tài liệu thiết kế |

**Quyết định cần mở trước:** [intent.md §2](../../notaryoffice/intent.md) về
quyền riêng tư (dẫn tới chính sách B2 liên sản phẩm);
[intent.md §10.1](../../notaryoffice/intent.md) về điều phải đo trên máy thật,
gồm kết luận A2 rằng không dùng số bản in như một dữ kiện chắc chắn. Mục A
trong `OPEN_DECISIONS.md` chỉ còn là đường dẫn cũ. Phương án kiến trúc và lý do loại nằm ở
[intent.md §6](../../notaryoffice/intent.md).

Khi module có spec được duyệt và code riêng, cập nhật `intent.md` để nó chỉ
tới spec mới, nêu phần nào đã chuyển quyền sở hữu. Không để hai file cùng ghi
hai đáp án khác nhau cho một hành vi.

## Quy tắc dùng bản đồ và giữ lời gốc

1. Tìm một trong bốn phần → mở **file sở hữu** → kiểm tra trạng thái và phạm vi
   → đọc source/test để biết hiện trạng code. Bản nháp, prototype, task log và
   code không tự biến thành quyết định nghiệp vụ đã duyệt.
2. Khi owner quyết định, ghi **ngay trong mục sở hữu**: kết luận; trạng thái;
   phạm vi; người/ngày/nguồn; **“Tại sao?” bằng nguyên ý**, gồm ví dụ, ngoại lệ
   và điều kiện phải hỏi lại. Bản diễn giải cho agent đặt sau lời gốc, không
   thay lời gốc. Nếu chưa có lời giải thích, ghi rõ `Chưa có lời giải thích được
   xác nhận`.
3. Nếu lời giải thích chưa dẫn tới quyết định, giữ nguyên ở issue/comment gốc
   và dẫn từ task; chưa đưa thành quy tắc trong spec. Nếu hai file mâu thuẫn,
   xác định owner và trạng thái, sửa chỗ sai; không chọn file mới hơn theo ngày.
4. Chỉ tạo file dài hạn mới khi file hiện có không thể chứa nội dung mà vẫn rõ
   quyền sở hữu. File mới phải có mục đích, trạng thái, phạm vi, nguồn quyết
   định và đường dẫn từ bản đồ này **trong cùng thay đổi**. Quy tắc kiểm tra
   bắt buộc cho agent nằm ở [`AGENTS.md`](../../AGENTS.md).

Chưa đưa RAG (tìm kiếm bằng AI) thành nguồn sự thật. Nếu làm, nó chỉ lập chỉ
mục từ các file trên, trả kèm file/mục/trạng thái và không tự lấp chỗ thiếu
“tại sao”.
