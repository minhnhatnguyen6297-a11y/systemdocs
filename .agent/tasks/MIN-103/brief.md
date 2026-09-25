# MIN-103 — MIGRATE: engine Zalo thành module thứ tư trong repo riêng và zalo/ monorepo

Linear: https://linear.app/minhnotary/issue/MIN-103/ (In Progress)
Parent: MIN-91. Depends: MIN-92 (contract published) → MIN-93 (scaffold committed `a2de16b`+`068ae58` tại `D:\zalo-intake`).

## Baseline record

- Source repo: `D:\systemdocs` monorepo, HEAD commit `67998868b06ac4608ce2a463f40ae03a45b84157`
- `notary_v2/` dirty state tại thời điểm kiểm kê (working tree = baseline đọc): 9 file — `M docs/README.md`, `M docs/platform/document-intake/spec.md`, `M docs/platform/zalo-document-inbox/{README,spec}.md`, `D open-issues.md`, `?? open-issues-v1-legacy.md`, `?? spec-v1-legacy.md`, `M zalo_connector/README.md`
- Target repo: `D:\zalo-intake` (local git, `main`, source-of-truth)
- Snapshot target: `D:\systemdocs\zalo\` (flat, one-way, SNAPSHOT_MANIFEST.json — không nested .git/submodule)

## Ranh giới chuyển (per issue)

MOVES sang module: connector Node/zca-js · account/session/listener mgmt · journal nguồn · media download+lưu · lifecycle 168h · job/queue/retry · chuẩn bị ảnh + gọi Qwen · raw status/provenance · primitive/test Zalo.

STAYS ở notary: regex · phân loại giấy · bóc trường · ghép mặt/người/tài sản/nhóm hồ sơ · legal/case engine · manual OCR upload path · frontend UI.

MIXED → split theo hàm; shared primitives → DUPLICATE (module có bản riêng, notary giữ bản cho manual flow đến MIN-101).

## Nghiệm thu (5 bullet của issue)

1. Source inventory/map: path+symbol+source commit+đích (repo riêng + zalo/)+manifest/checksum+phần giữ lại notary + giải thích không chuyển parser.
2. Repo nguồn chính + quy trình sync snapshot chốt trước khi diverge; hai bản đối chiếu cùng commit/manifest; monorepo không nested git.
3. Connector tests + Python tests chạy trên module độc lập, notary ngoài PYTHONPATH, backend notary tắt; replay synthetic chứng minh runtime riêng.
4. Test parity hành vi baseline kiểm được ngoại tuyến; khác biệt ghi rõ cho MIN-94/95/97; KHÔNG dùng live account/Qwen key.
5. Runbook khôi phục bằng source commit/snapshot; dừng một listener trước khi bật lại; không mất pending data; gỡ legacy chỉ thuộc MIN-101.

## An toàn

- Không chạy hai listener cùng account; không auto-launch/service; không chung DB/media/session/secret/runtime; không đưa ảnh/session/key thật vào Git; chỉ fixture giả lập.
- Legacy Zalo trong notary GIỮ NGUYÊN — task này không xóa/sửa code notary (ngoại trừ: nếu cần đánh dấu, chỉ doc).
- Docs producer chuyển sang `docs/` của repo riêng + `zalo/docs` snapshot; một nguồn chỉnh sửa duy nhất.

## Wave plan

- W0 (đang chạy): I1 connector · I2 python engine (zalo_inbox svc/router/models/tests) · I3 ocr_ai primitives · I4 docs/frontend/misc → `scratch/MIN-103/inventory/i{1..4}-*.md`
- W1: source map tổng hợp + decision-sheet migration + design slice
- W2+: migration slices song song (connector / engine-python / docs / snapshot tooling) + parity tests
- Cuối: snapshot zalo/ + manifest + verify + review + commit + runbook
