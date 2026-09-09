# Notary Work Intelligence — System Architecture & Vision Hub

> Trung tâm quản lý tầm nhìn, kiến trúc hệ thống và hợp đồng giao tiếp giữa các phân hệ trong hệ sinh thái **Notary Work Intelligence**.

---

## 1. Bức Tranh Tổng Thể

Hệ sinh thái bao gồm 4 phân hệ chức năng độc lập nhưng phối hợp chặt chẽ:

| STT | Phân hệ (Project) | Đường dẫn | Vai trò chính |
|:---:|:---|:---|:---|
| 1 | **`notaryoffice`** | `D:\notaryoffice` | **Nghiệp vụ & Triết lý**: Tài liệu định hướng, intent hệ thống, yêu cầu nghiệp vụ văn phòng công chứng. |
| 2 | **`notary_v2`** | `D:\notary_v2` | **Core Platform**: Ứng dụng chính xử lý hồ sơ (Case Workspace, Thừa kế, OCR Cloud/Local, sinh file Word). |
| 3 | **`upload_lab_repo`** | `D:\upload_lab_repo` | **Intake & OCR Lab**: Pipeline thử nghiệm bóc tách dữ liệu văn bản, OCR regex review, lab xử lý tài liệu thô. |
| 4 | **`researchskill`** | `D:\researchskill` | **AI Legal Skills**: Kỹ năng tra cứu văn bản pháp lý, đánh giá và đối soát quy chuẩn pháp luật công chứng. |

---

## 2. Cấu Trúc Tài Liệu

- **[`VISION.md`](./VISION.md)**: Tầm nhìn, triết lý "văn phòng không cần nhập tay" và bài toán nghiệp vụ cốt lõi.
- **[`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md)**: Sơ đồ kiến trúc, luồng dữ liệu liên thông giữa 4 module.
- **[`PROJECTS.md`](./PROJECTS.md)**: Chi tiết cấu hình, ranh giới trách nhiệm và cách liên kết các project trong Orca.
- **[`contracts/`](./contracts/)**: Đặc tả hợp đồng dữ liệu chung (Data Schemas, API Specs, Event payloads).
- **[`AGENTS.md`](./AGENTS.md)**: Chỉ dẫn cho AI Agent khi đảm nhận vai trò Kiến trúc sư hệ thống (System Architect).
