# Danh Mục & Định Nghĩa 4 Phân Hệ Trong Hệ Thống

Tài liệu này định danh ranh giới trách nhiệm, vị trí vật lý và cách vận hành các phân hệ trong **Orca ADE**.

---

## 1. `notaryoffice` (Nghiệp vụ & Tầm nhìn)
- **Đường dẫn**: `D:\notaryoffice`
- **Loại trong Orca**: `folder`
- **Mô tả**: Lưu trữ intent, bài toán thực tế của văn phòng công chứng, các bản phân tích nghiệp vụ (VD: `gioi-thieu-du-an.md`, `intent.md`, `session_summary.md`).
- **Ranh giới**: Không chứa code thực thi production, đóng vai trò là "Business Requirement Specification" (BRD) cho toàn bộ hệ thống.

---

## 2. `notary_v2` (Nền tảng xử lý hồ sơ cốt lõi)
- **Đường dẫn**: `D:\notary_v2`
- **Loại trong Orca**: `git` (`github.com/minhnhatnguyen6297-a11y/notary_v2`)
- **Mô tả**: Hệ thống cốt lõi quản lý case hồ sơ công chứng, xử lý hồ sơ thừa kế, bóc tách hồ sơ (Document Intake), giao diện người dùng (Templates / Case UI), xuất file văn bản công chứng (Word generation), quản lý workspace & stage pool.
- **Ranh giới**: Nhận dữ liệu đã chuẩn hóa hoặc tài liệu từ `upload_lab_repo`, phối hợp với `researchskill` để thẩm định và xuất kết quả cho công chứng viên.

---

## 3. `upload_lab_repo` (Phòng lab trích xuất & OCR)
- **Đường dẫn**: `D:\upload_lab_repo`
- **Loại trong Orca**: `git` (`github.com/minhnhatnguyen6297-a11y/upload_lab`)
- **Mô tả**: Môi trường lab chuyên sâu về bóc tách tài liệu scan, xử lý ảnh OCR, regex pattern matching, review mẫu văn bản scan thực tế từ các cơ quan nhà nước.
- **Ranh giới**: Thử nghiệm và hoàn thiện các thuật toán/pipeline trích xuất trước khi đưa vào module Document Intake của `notary_v2`.

---

## 4. `researchskill` (AI Kỹ năng tra cứu & Đánh giá pháp lý)
- **Đường dẫn**: `D:\researchskill`
- **Loại trong Orca**: `git` (`github.com/minhnhatnguyen6297-a11y/researchskill`)
- **Mô tả**: Bộ công cụ / kỹ năng đánh giá văn bản pháp luật, tra cứu luật công chứng, luật đất đai, dân sự phục vụ kiểm tra tính pháp lý của hồ sơ.
- **Ranh giới**: Cung cấp năng lực suy luận và tra cứu tri thức chuyên gia cho các Agent và hệ thống `notary_v2`.

---

## 5. `systemdocs` (Trung tâm kiến trúc & Liên kết)
- **Đường dẫn**: `D:\systemdocs\systemdocs`
- **Loại trong Orca**: `git`
- **Mô tả**: Workspace trung tâm định hình kiến trúc, quy định chuẩn giao tiếp giữa các phân hệ, lưu trữ ADR (Architecture Decision Records) và điều phối hệ thống.
