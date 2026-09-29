# Repository documentation

Status: current
Source of truth: `../../docs/spec/notary_v2/`; các đường dưới là nguồn chi tiết kỹ thuật và bằng chứng hiện trạng
Read when: locating product or architecture documentation

- Business modules: `docs/domains/`
- Shared capabilities: `docs/platform/`
- Zalo Intake: [bắt đầu tại đây](platform/zalo-document-inbox/README.md) — repo `D:\zalo-intake` là SOT của engine, `zalo/` trong monorepo là snapshot một chiều. Thư mục này giữ tài liệu phía Notary nhận và dùng kết quả Sync; không giữ spec engine song song.
- Upload OCR thủ công: [document-intake](platform/document-intake/spec.md) — endpoint và parser hiện hành giữ nguyên; phân biệt với đích Zalo mới chưa có runtime.
- Spec sản phẩm và quyết định hiện hành: [`../../docs/spec/notary_v2/`](../../docs/spec/notary_v2/)
- Code navigation: use Graphify; do not duplicate code maps here
