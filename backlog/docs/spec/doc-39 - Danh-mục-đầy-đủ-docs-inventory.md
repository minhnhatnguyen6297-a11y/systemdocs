---
id: doc-39
title: Danh mục đầy đủ docs/ (inventory)
type: readme
created_date: '2026-10-05 04:04'
updated_date: '2026-10-05 04:05'
tags:
  - spec
  - inventory
---
# Danh mục docs/ — inventory (TASK-1)

Nguồn chân lý nội dung: `docs/spec/`. Bảng này liệt kê đủ file tại 05/10/2026;
cột Backlog trỏ doc pointer tương ứng (file tạm/nhị phân không có doc riêng).

## Gốc

| File | Vai trò | Backlog |
|---|---|---|
| `docs/spec/README.md` | SOT cấp hệ thống | doc-1 |
| `docs/spec/product-overview.md` | Giới thiệu cho dev | doc-2 |

## notaryoffice

| File | Vai trò | Backlog |
|---|---|---|
| `notaryoffice/README.md` | Spec module | doc-3 |
| `notaryoffice/intent-source.md` | Phụ lục thiết kế gốc | doc-4 |

## shared

| File | Vai trò | Backlog |
|---|---|---|
| `shared/administrative-lookup.md` | Lõi tra cứu dùng chung | doc-5 |

## ui

| File | Vai trò | Backlog |
|---|---|---|
| `ui/README.md` | Spec UI chung | doc-6 |
| `ui/tokens.json` | Token máy đọc | — (trong doc-6) |
| `ui/prototypes/README.md` | Spec bản mẫu | doc-7 |
| `ui/prototypes/index.html`, `components.html`, `prototype.css`, `app.js`, `data.js`, `notary.js`, `upload.js` | Code prototype | — (trong doc-7) |
| `ui/references/README.md` | Danh mục ảnh duyệt | doc-8 |
| `ui/references/approved-*.png` (3 ảnh) | Tham chiếu thị giác | — (trong doc-8) |

## upload_lab

| File | Vai trò | Backlog |
|---|---|---|
| `upload_lab/README.md` | Spec module | doc-9 |
| `upload_lab/portal-session.md` | Phiên portal, nhận diện Lưu | doc-10 |
| `upload_lab/regex-rules.md` | Catalog regex | doc-11 |
| `upload_lab/ui.md` | Bố cục/hành vi Electron | doc-12 |
| `upload_lab/references/*.{png,jpg}` (9 ảnh) | Mockup/ảnh UI cũ | — (tham khảo, không phải bản duyệt) |

## notary_v2

| File | Vai trò | Backlog |
|---|---|---|
| `notary_v2/README.md` | Spec module | doc-13 |
| `notary_v2/administrative-address.md` | Tra cứu địa chỉ trong hồ sơ | doc-14 |
| `notary_v2/administrative-timeline.md` | Kho lịch sử đơn vị hành chính | doc-15 |
| `notary_v2/fast-text-audit.md` | CLI so Word/scan | doc-16 |
| `notary_v2/pool.md` | Pool | doc-17 |
| `notary_v2/stage.md` | Stage | doc-18 |
| `notary_v2/visual-reference.md` | Thiết kế thị giác tab Soạn hồ sơ | doc-19 |
| `notary_v2/word-output.md` | Xuất Word | doc-20 |
| `notary_v2/word-output-detail.md` | UX/flow xuất Word chi tiết | doc-21 |
| `notary_v2/workspace-detail.md` | Bản chi tiết MIN-104 | doc-22 |
| `notary_v2/diagram/README.md` | Spec Diagram | doc-23 |
| `notary_v2/diagram/stage-sync-draft.md` | Đề xuất đồng bộ (Draft) | doc-24 |
| `notary_v2/diagram/two-party.md` | Diagram hai bên | doc-25 |
| `notary_v2/diagram/inheritance/README.md` | Spec thừa kế | doc-26 |
| `notary_v2/diagram/inheritance/business-rules.md` | Nghiệp vụ mở rộng (Draft) | doc-27 |
| `notary_v2/diagram/inheritance/case-state-parked.md` | Thiết kế parked | doc-28 |
| `notary_v2/diagram/inheritance/engine.md` | Engine V2 đích | doc-29 |
| `notary_v2/diagram/inheritance/examples.md` | Catalog bài toán | doc-30 |
| `notary_v2/diagram/inheritance/provenance.md` | Provenance | doc-31 |
| `notary_v2/diagram/inheritance/web-workflow.md` | UX web hiện trạng | doc-32 |
| `notary_v2/input/README.md` | Spec Input | doc-33 |
| `notary_v2/input/docx-import.md` | Nhập DOCX | doc-34 |
| `notary_v2/input/ocr-detail.md` | OCR Qwen + ranh giới Zalo | doc-35 |
| `notary_v2/input/property-rules.md` | Rule OCR tài sản | doc-36 |
| `notary_v2/input/zalo/README.md` | Spec Zalo Intake | doc-37 |
| `notary_v2/input/zalo/acceptance.md` | Nghiệm thu Zalo Intake v2 | doc-38 |

## Quyết định kiến trúc → backlog decision

Các quyết định trong spec đã có record: decision-1…21 (NAIA-9, TASK-2, TASK-6/7)
và decision-22…39 (quyết định kiến trúc cấp hệ thống/module trích từ spec tại
TASK-1). Quyết định mới vẫn ghi `backlog decision create` như cũ.
