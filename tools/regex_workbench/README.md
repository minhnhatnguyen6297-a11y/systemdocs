# Regex Workbench — lõi luật chung cho Word

Một đường luật duy nhất cho văn bản Word: `engine/contract_extract.py`.
Document Intake (Notary), Upload Lab và tool nhân viên đều gọi vào đây qua
adapter của mình; adapter chỉ giữ đọc file + ánh xạ payload, **không chép luật**.

| Thành phần | Vai trò |
|---|---|
| `engine/contract_extract.py` | Luật trích xuất (người, tài sản, thửa/GCN, người chết, phần chưa hỗ trợ) + payload `{web_form, raw}`. Vào bằng `extract_text(text, ...)`. |
| `engine/__init__.py` | Bề mặt lõi: `ENGINE_ID`, `ENGINE_VERSION`, `extract_text`. |
| `tests/fixtures/` | Fixture giả lập (không PII khách thật) cho vùng chuyển nhượng, giữ từ vòng #7. |
| `tests/test_contract_core_transfer.py` | Hành vi #7 trên lõi: serial nguyên văn theo nhãn, địa chỉ thửa có nhãn, người đồng sử dụng, năm sinh chỉ-năm, nhãn trống không mượn ô kế. |

Consumer:

- Upload Lab / tool nhân viên: `upload_lab/extraction_adapter.py` (đọc `.docx`/`.doc`,
  chuẩn hóa text `.doc`, quét số công chứng theo file, giữ payload `{web_form, raw}`).
- Document Intake (Notary): `notary_v2/services/document_intake/adapters/docx.py`
  (đọc DOCX theo thứ tự XML, dựng `source_refs` span/`rule_id`/identity lõi).

Identity của lõi dùng chung ở mọi consumer: `ENGINE_ID = "contract_word"`,
`ENGINE_VERSION` trong `engine/contract_extract.py`; consumer ghi identity này
vào log/`payload.raw.engine_version`/`profile_id`+`profile_version` của refs.

Catalog quy tắc và trạng thái Pending: `_bmad-output/specs/shared/extraction-rules.md`.
Quy tắc do developer quản lý, có phân biệt phiên bản — người dùng sản phẩm
không có tính năng thử/công bố/chọn phiên bản/rollback
(`_bmad-output/decisions/decision-owner-regex-rule-developer-only-20261016.md`).

## Dev server + UI (migrate sang lõi chung)

```bat
python tools\regex_workbench\serve.py
```

Mở `http://127.0.0.1:8765/` (ba cột: văn bản nguồn + vị trí giá trị | lõi luật
và chẩn đoán | kết quả + JSON). UI chạy chính lõi chung qua `/api/run`
(không phụ thuộc `upload_lab`, `shell`, `notary_v2`); `/api/meta` trả identity
lõi để biết kết quả do phiên bản nào sinh.

Phần **đã bỏ vì hết tác dụng kỹ thuật** (không phải cấm dev sửa rule): editor
cũ sửa/import/export **profile JSON** — định dạng đó không còn tồn tại sau cutover.
Luật nay là mã Python trong `engine/contract_extract.py`; dev sửa trực tiếp mã
chuẩn và thử bằng chính lõi đó qua UI/test (`tests/`, fixture, corpus
`upload_lab/tests/fixtures/word_field_cases.json`). Không có editor giả cho
Python và chưa cần editor tổng quát mới; nếu sau này cần, làm trên lõi chung.

## Chạy test

```bat
python -m pytest tools\regex_workbench\tests -q
```

Test UI chạy `ui/app.js` thật bằng stub DOM + Node (`tests/_ui_dom_probe.mjs`,
tự skip nếu máy thiếu node). Bản nhân viên (`regex-test-tool/`) đóng gói lõi
qua adapter bằng script release, không chép tay; bộ test cũ của tool chạy lại
trên lõi chung được ghi ở
`_bmad-output/tmp/issue-22-regex-consumer-cutover/evidence/legacy-compat/`.
