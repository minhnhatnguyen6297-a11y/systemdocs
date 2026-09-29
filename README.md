# Notary System

Kho này chứa runtime tích hợp và nguồn tài liệu chung cho hệ thống công chứng.
Tài liệu được tổ chức theo **phạm vi và flow**, không theo loại “nghiệp vụ”,
“kiến trúc”, “UI” hay “quyết định”.

## Bắt đầu đọc

1. Đọc [spec toàn hệ thống](./docs/spec/README.md).
2. Chọn module trong cây dưới.
3. Đi qua README của từng thư mục cha tới feature cần sửa.
4. Đọc contract và source được spec lá dẫn tới.

## Cây tài liệu

```text
docs/spec/
├── README.md                       # Tầm nhìn, ranh giới, kiến trúc và câu hỏi toàn hệ thống
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
│   └── README.md                   # Word → audit Excel → chuẩn bị upload
├── notaryoffice/
│   └── README.md                   # Evidence → Draft Case → xác nhận → tìm kiếm
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
Nếu ảnh hưởng nhiều module, đặt ở `docs/spec/README.md`.

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

## Những nơi khác

| Chỗ | Dùng cho |
|---|---|
| [`contracts/`](./contracts/README.md) | Contract đã duyệt và schema máy đọc |
| `.agent/tasks/` | Tiến độ, quyết định trong task và handoff |
| `code-graphs/` | Snapshot để tìm quan hệ code; không phải spec |
| `_bmad-output/` | Artifact workflow BMAD |
| `.agent/scratch/`, `.tmp/`, `.cache/`, `logs/`, `artifacts/` | File tạm, không commit |

Linear là nguồn task. Trước khi sửa tài liệu, đọc [luật agent](./AGENTS.md).
