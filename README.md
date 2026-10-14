# Notary System

Kho này chứa runtime tích hợp và nguồn tài liệu chung cho hệ thống công chứng.
Tài liệu được tổ chức theo **phạm vi và flow**, không theo loại “nghiệp vụ”,
“kiến trúc”, “UI” hay “quyết định”.

## Bắt đầu đọc

1. Đọc [nền sản phẩm và khái niệm chung](./_bmad-output/specs/README.md).
2. Đọc [sổ tay sản phẩm theo màn hình](./_bmad-output/specs/product-overview.md)
   để tìm UI và việc đang mở.
3. Chọn module trong cây dưới.
4. Đọc README của module và từng thư mục cha, rồi tới spec feature để biết hành vi chi tiết.
5. Đọc contract và source được spec lá dẫn tới.

## Cây tài liệu

```text
_bmad-output/specs/
├── README.md                       # Nền sản phẩm, khái niệm chung và spec toàn hệ thống
├── shared/
│   └── administrative-lookup.md    # Lõi tra cứu tên xã/tỉnh dùng chung
├── notary_v2/
│   ├── README.md                   # Input → Stage → Pool → Diagram → Word
│   ├── input/
│   │   ├── README.md               # Nhập ảnh, PDF, Word, Excel, text
│   │   └── zalo/                  # Gói raw OCR và điều kiện nghiệm thu consumer Zalo
│   ├── stage.md                    # Dữ liệu Người/Tài sản đã commit
│   ├── pool.md                     # Người chưa được gán Diagram
│   ├── diagram/
│   │   ├── README.md               # Thao tác, state, lưu và contract Diagram
│   │   ├── inheritance/            # Nghiệp vụ, engine và ví dụ thừa kế
│   │   └── two-party.md            # Hai bên A/B, 30 vị trí ổn định
│   ├── word-output.md              # Xuất nhiều văn bản Word
│   └── fast-text-audit.md          # CLI soát nhanh Word với scan
├── upload_lab/
│   ├── README.md                   # Word → audit Excel → chuẩn bị upload
│   ├── regex-core.md               # Phạm vi và vòng kiểm tra trích Word
│   ├── regex-fields.md             # Một nguồn quy tắc từng trường
│   ├── regex-expected-results.md   # Đáp án mẫu, Closed/Pending
│   ├── regex-thua-ke.md            # Loại/vùng thừa kế
│   ├── regex-rules.md              # Catalog cấu trúc/loại Word
│   ├── portal-session.md           # Đăng nhập, nhận diện Lưu
│   ├── ui.md                       # Hai tab Electron và lớp thị giác
│   └── references/                # Ảnh mockup/UI cũ, không là spec
├── notaryoffice/
│   ├── README.md                   # Evidence → Draft Case → xác nhận → tìm kiếm
│   └── intent-source.md            # Phụ lục Draft lớn, lập luận gốc
└── ui/
    ├── README.md                   # UI dùng chung của Electron shell
    ├── tokens.json
    ├── prototypes/                 # Bản mẫu, không có backend thật
    └── references/                 # Ảnh owner đã duyệt
```

Tên thư mục là bản đồ. README của một thư mục giữ điều dùng chung cho mọi file
con. Một feature nhỏ dùng một file; chỉ tách thư mục khi chính feature có các
chức năng con độc lập.

## Cấu trúc một feature nhỏ

Ví dụ feature **Nhập liệu**:

| Mục | Câu hỏi cần trả lời |
|---|---|
| Công dụng | Giải quyết việc gì, không làm gì? |
| Người dùng và thao tác | Ai dùng, bấm/kéo/nhập thế nào? |
| Input | Nhận file, text hoặc dữ liệu nào; giới hạn gì? |
| Output | Trả gì; trạng thái nào chỉ là gợi ý? |
| Flow | Từng bước từ đầu vào tới kết quả |
| Quy tắc và Tại sao | Điều kiện, công thức, lý do ngành, ngoại lệ |
| Dữ liệu | Lưu ở đâu, shape gì, revision/owner nào? |
| Contract | Feature/module khác gửi và nhận gì? |
| Kiến trúc/công nghệ | Thành phần nào làm; công nghệ và lý do |
| Giao diện | Trạng thái, nút, lỗi, accessibility |
| Câu hỏi/lịch sử | Điều chưa chốt, quyết định cũ và nguồn |

Không cần mục rỗng. Kiến trúc hay câu hỏi chỉ ảnh hưởng Nhập liệu nằm ngay trong
spec Nhập liệu. Nếu ảnh hưởng cả Stage và Diagram, đặt ở README `notary_v2`.
Nếu ảnh hưởng nhiều module, đặt ở `_bmad-output/specs/README.md`.

## Module và runtime

| Đường dẫn | Vai trò | Trạng thái |
|---|---|---|
| `shell/` | Electron shell + Python sidecar | Runtime tích hợp |
| `notary_v2/` | Soạn hồ sơ | Đang phát triển |
| `upload_lab/` | Số hóa và upload hồ sơ cũ | Đang phát triển |
| `notaryoffice/` | Theo dõi vận hành văn phòng | Chỉ có thiết kế |
| `zalo/` | Snapshot một chiều từ `D:\zalo-intake` | Repo nguồn sở hữu engine |

`shell` là hạ tầng, không phải module nghiệp vụ. Zalo là nguồn đầu vào kỹ thuật,
không tạo phần sản phẩm thứ tư.

### Báo lỗi giao diện trong chế độ dev

Chạy `run-dev.bat` ở gốc repo → Ctrl+Shift+B → chọn phần tử → viết ghi chú →
Save report. Launcher dùng lại `run.bat`, không cần đường dẫn máy cố định hoặc
`rtk`. Đây là cùng app nhưng **Notary mock, dữ liệu/profile thử tách riêng**,
không phải dữ liệu công chứng production. Báo cáo JSON/PNG nằm ở thư mục ignored
`_bmad-output/tmp/visual-bug-reporting/reports/`; ghi chú được giữ nguyên văn,
phải kiểm tra dữ liệu riêng tư trước khi chia sẻ. App đóng gói không bật tool này.
Xem [hướng dẫn và kiểm chứng](./tools/visual-bug-reporting/README.md).


## Những nơi khác

| Chỗ | Dùng cho |
|---|---|
| [`contracts/`](./contracts/README.md) | Contract đã duyệt và schema máy đọc |
| `_bmad-output/specs/` | SOT đặc tả hành vi (spec quyết định, code chứng minh) |
| `_bmad-output/decisions/` | Quyết định đã chốt: LÀ GÌ và TẠI SAO |
| `graphify-out/` | Snapshot để tìm quan hệ code; không phải spec |
| `_bmad-output/` | Artifact workflow BMAD (plans, review, archive) |
| `.tmp/`, `.cache/`, `logs/`, `artifacts/` | File tạm, không commit |

Trước khi sửa tài liệu, đọc [luật agent](./AGENTS.md).

## Plan/spec trực quan trong BMAD

`bmad-build` và `bmad-spec` tích hợp HTML qua các field BMAD hỗ trợ
(`persistent_facts`, `activation_steps_append`) trong `_bmad/custom/`. Cả hai nạp
[contract authoring](./_bmad/custom/html-plan/authoring.md) và
[spec hành vi](./_bmad-output/specs/shared/visual-html-plans.md); không gọi
skill HTML riêng.
Build trình bày HTML sau điều tra và tự kiểm tra, trước khi trình bày plan/xin
duyệt; với oneshot cần minh họa thì trước implementation. Spec trình bày sau
self-validation và trước khi trả kết quả. Agent viết theo cấu trúc
Thariq: cây hành vi và exhibit, mock app theo UI đã inspect; không bọc Markdown.
Markdown/memory BMAD vẫn là nguồn chuẩn.

Từ root repo, đóng gói ví dụ bằng Node:

```sh
node _bmad/custom/html-plan/runtime/pack.mjs _bmad/custom/html-plan/examples/notary-diagram-errors.html --root .
```

Mở `notary-diagram-errors.packed.html` cùng thư mục trong browser. Với task mới,
agent viết `_bmad-output/tmp/<slug>/plan.html` hoặc `spec.html`, thay input trong
command, xem cây đóng/mở và từng state rồi giao link `.packed.html` bấm được.
Không dùng dữ liệu ví dụ làm mặc định cho plan tương lai.

**Giới hạn:** customization là chỉ dẫn agent, không phải hook cưỡng chế, generator
hay runtime tự mở browser. Task nhỏ không bị ép lựa chọn hoặc gate mới; Respond là
phụ, chưa xem không phải đồng ý. Pack thành công không chứng minh mock đúng: vẫn
cần kiểm tra bằng mắt hoặc báo rõ chưa kiểm tra được.
