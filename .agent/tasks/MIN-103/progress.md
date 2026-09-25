# MIN-103 progress — engine Zalo → repo riêng + zalo/ snapshot

## Trạng thái: CODE DONE — đã verify + commit + snapshot. Chờ owner quyết định commit `zalo/` trong systemdocs + Linear Done.

## Kết quả

- Repo `D:\zalo-intake` @ commit **`13ea96c`** (sau `a2de16b`/`068ae58` của MIN-93): toàn bộ engine baseline đã migrate.
- Snapshot `D:\systemdocs\zalo\` đã export: **82 file**, `SNAPSHOT_MANIFEST.json` (source_commit `13ea96c`, sha256 map, 0 mismatch), phẳng, không `.git`/submodule. **Chưa commit trong systemdocs — chờ owner.**
- `D:\systemdocs\notary_v2\` legacy **không đổi code** — chỉ 2 file docs sửa (spec.md split producer→pointer, README.md map); legacy giữ đến MIN-101.

## Verify (sau fix round)

- `pytest tests -q`: **161 passed** (83 MIN-93 baseline + 76 ported + 2 mới cho C1/M6)
- `npm --prefix connector run check`: clean · `npm test`: 87–89/90 — **flake baseline-identical** (FileOutbox ENOENT race, chứng minh trên source gốc; ghi `[MIN-94]`)
- `verify.ps1`: **PASS** (pytest + npm check + replay + status; npm test = advisory)
- Secret sweep: clean · forbidden paths trong snapshot: 0 · schemas/ byte-identical contract MIN-92

## Review độc lập

Vòng 1 **NEEDS_FIX** → đã fix toàn bộ:
- **C1 (Critical)**: config `sources[]` thiếu `desired_enabled`/`acked_enabled` (connector `=== true` → intake rỗng vĩnh viễn). Đã emit booleans + regression test.
- M1–M7: parity fix (PATCH sources shape, data-sync status, connectors/start shape, ACK id keys, commands/next 404, onboard 403/config+media 404).
- M5+M9: documented intentional ([MIN-95]/[MIN-97]); M9 message_text payload nay validate đúng raw-record schema, internal fields về journal.event_json; source_event bỏ schema_version claim.
- M8 lockfile regen · M10 README · M11 dead helper xóa.

## Wave log

- W0 inventory 4 agent song song → `scratch/MIN-103/inventory/i{1..4}.md` (đầy đủ source map file/symbol — acceptance bullet 1).
- W1 migration 4 slice: A connector (verbatim+4 URL) · B engine port (m0002+engine+api+proc, 76 test) · C OCR primitives (43 test) · D docs+export tool+notary spec split.
- Review + fix + commit `13ea96c` + export zalo/.

## Parity notes quan trọng (chi tiết: `zalo-intake/docs/migration-notes.md`)

- Connector flake ENOENT FileOutbox.entries() — baseline có sẵn → [MIN-94] fix candidate.
- Text-quota FIFO legacy dropped → uniform 168h → [MIN-94].
- `protected_media_object_keys` = tất cả media chưa hết hạn (thay ZaloBatch) → [MIN-97] nới theo ACK.
- Module `/state` là ops surface rút gọn → [MIN-95].
- Single-account model giữ; `my_documents` gate giữ; heartbeat/media accepted-unused.

## Còn lại / parked

- MIN-94: listener_sessions writer đầy đủ, conv policy redesign nếu cần, fix FileOutbox race, event-shape hardening.
- MIN-95: ocr wiring jobs→qwen→variants; package byte endpoints.
- MIN-97: quota/auth đầy đủ, protected-keys theo ACK, schema validation khi build package.
- `shell/sidecar` stale `zalo.status` wiring — flag, MIN-101 territory.
- Linear MIN-93 + MIN-103 đều In Progress — owner tự chốt Done.
