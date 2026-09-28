# Repository documentation

Status: current
Source of truth: module specs and platform contracts routed below
Read when: locating product or architecture documentation

- Business modules: `docs/domains/`
- Shared capabilities: `docs/platform/`
- Zalo Intake: [bắt đầu tại đây](platform/zalo-document-inbox/README.md) — repo `D:\zalo-intake` là SOT của engine, `zalo/` trong monorepo là snapshot một chiều. Thư mục này giữ tài liệu phía Notary nhận và dùng kết quả Sync; không giữ spec engine song song.
- Upload OCR thủ công: [document-intake](platform/document-intake/spec.md) — endpoint và parser hiện hành giữ nguyên; phân biệt với đích Zalo mới chưa có runtime.
- Architecture decisions: `docs/architecture/`
- Code navigation: use Graphify; do not duplicate code maps here
