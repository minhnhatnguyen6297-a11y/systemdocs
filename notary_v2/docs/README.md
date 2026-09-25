# Repository documentation

Status: current
Source of truth: module specs and platform contracts routed below
Read when: locating product or architecture documentation

- Business modules: `docs/domains/`
- Shared capabilities: `docs/platform/`
- Zalo Intake: [bắt đầu tại đây](platform/zalo-document-inbox/README.md) — spec hiện ở đây trong giai đoạn chuyển tiếp. [MIN-103](https://linear.app/minhnotary/issue/MIN-103/migrate-engine-zalo-thanh-module-thu-tu-trong-repo-rieng-va-zalo) sẽ chuyển tài liệu engine sang repo Zalo riêng và snapshot `zalo/docs/` (chưa có); nơi này giữ spec giao tiếp và phần Sync/Document Intake của máy chính, không giữ hai spec engine song song.
- Upload OCR thủ công: [document-intake](platform/document-intake/spec.md) — endpoint và parser hiện hành giữ nguyên; phân biệt với đích Zalo mới chưa có runtime.
- Architecture decisions: `docs/architecture/`
- Code navigation: use Graphify; do not duplicate code maps here
