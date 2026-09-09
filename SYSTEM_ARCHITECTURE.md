# Sơ Đồ Kiến Trúc Hệ Thống (System Architecture)

Tài liệu mô tả luồng vận hành tổng thể giữa 4 phân hệ chức năng.

```mermaid
flowchart TD
    subgraph Business_Layer ["1. Business & Requirement Layer"]
        NO["notaryoffice<br/>(D:\notaryoffice)<br/>Intent, Triết lý, Nghiệp vụ thực tế"]
    end

    subgraph Lab_Intake ["2. Ingestion & Extraction Lab"]
        UL["upload_lab_repo<br/>(D:\upload_lab_repo)<br/>Pipeline OCR thô, Regex, Parser"]
    end

    subgraph Core_Engine ["3. Core Application Engine"]
        NV2["notary_v2<br/>(D:\notary_v2)<br/>Quản lý Case, Intake UI, Stage/Pool,<br/>Sinh file Word, Phân tích thừa kế"]
    end

    subgraph Intelligence_Layer ["4. Intelligence & Knowledge Layer"]
        RS["researchskill<br/>(D:\researchskill)<br/>Tra cứu luật, Đối soát pháp lý, Rule Engine"]
    end

    subgraph Hub ["Arch & Governance"]
        SD["systemdocs<br/>(D:\systemdocs\systemdocs)<br/>Vision, Architecture, Contracts"]
    end

    NO -.->|Định hình yêu cầu| SD
    SD -->|Quy định kiến trúc| NV2
    SD -->|Quy định kiến trúc| UL
    SD -->|Quy định kiến trúc| RS

    UL -->|Thuật toán & Regex OCR đã kiểm thử| NV2
    RS <-->|Cung cấp kỹ năng tra cứu & thẩm định luật| NV2
```

---

## Các Luồng Dữ Liệu Chính

1. **Luồng Tiếp Nhận Hồ Sơ (Document Intake Flow)**:
   - Hồ sơ quét/chụp $\rightarrow$ Thử nghiệm & tối ưu tại `upload_lab_repo` $\rightarrow$ Tích hợp vào Document Intake Pipeline của `notary_v2`.
2. **Luồng Nghiệp Vụ & Thẩm Định Pháp Lý**:
   - `notary_v2` tiếp nhận dữ liệu hồ sơ (bên liên quan, bất động sản, giấy chứng tử...) $\rightarrow$ Gọi kỹ năng từ `researchskill` để tra cứu tính hợp lệ theo pháp luật công chứng.
3. **Luồng Sinh Tài Liệu (Output Generation)**:
   - Sau khi case đạt chuẩn thẩm định $\rightarrow$ `notary_v2` tự động sinh văn bản công chứng (file Word) theo mẫu quy định.
