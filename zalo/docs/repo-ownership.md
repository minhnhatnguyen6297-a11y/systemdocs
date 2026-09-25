# Quyết định sở hữu repo (D1)

**`D:\zalo-intake` là source-of-truth repo** cho toàn bộ engine Zalo:
connector/listener, session, journal, media tạm, Qwen OCR, gói file raw và
API OCR lại. Mọi sửa đổi code/tài liệu module chỉ được thực hiện tại repo
này.

`D:\systemdocs\zalo\` trong monorepo là **snapshot một chiều, phẳng** (flat
copy, không `.git`), do MIN-103 tạo ra bằng `tools/export_snapshot.ps1` và
được refresh bằng cách chạy lại script đó.

## Đồng bộ snapshot

Chạy export từ repo source (PowerShell 5.1+):

```powershell
# mặc định ghi sang D:\systemdocs\zalo
powershell -File tools\export_snapshot.ps1

# hoặc chỉ đích khác (thử nghiệm/verify)
powershell -File tools\export_snapshot.ps1 -Dest D:\path\to\dir
```

Script:

1. Dọn sạch thư mục đích (xóa toàn bộ nội dung **bên trong** `$Dest` — đích
   là thư mục dedicated, không có gì cần giữ giữa hai lần export).
2. Mirror toàn repo → `$Dest`, **loại trừ ở mọi độ sâu**: `.git`, `.venv`,
   `runtime`, `node_modules`, `__pycache__`, `*.pyc`, `.env`,
   `.pytest_cache`, `SNAPSHOT_MANIFEST.json`.
3. Ghi `$Dest\SNAPSHOT_MANIFEST.json` (UTF-8 no BOM) — khóa kiểm chứng của
   snapshot.

## `SNAPSHOT_MANIFEST.json` format

```json
{
  "schema_version": 1,
  "source_repo": "D:\\zalo-intake",
  "source_commit": "<git rev-parse HEAD tại zalo-intake lúc export>",
  "exported_at": "<ISO 8601 UTC>",
  "files": { "<path tương đối, dấu />": "<sha256>" }
}
```

`files` map **mọi file đã copy** → sha256 — dùng để verify snapshot khớp
source hoặc phát hiện sửa tay.

## Quy tắc

- Snapshot **không mang `.git`** — nó là bản sao phẳng, không phải clone hay
  submodule. Không tạo `.git` lồng trong `systemdocs/zalo/`.
- **Chỉ sửa ở `D:\zalo-intake`.** Không sửa tay ở `systemdocs/zalo/`; thay
  đổi ở snapshot bị ghi đè ở lần export kế tiếp. Muốn snapshot đổi: sửa
  source rồi **re-export**, không patch đích.
- Đồng bộ là một chiều: `zalo-intake` → `zalo/`. Không có đường ngược lại;
  khôi phục từ snapshot chỉ để đọc/đối chiếu (xem `rollback-runbook.md`).
- `runtime/` (DB, session, media, packages, outbox, access.jsonl) và `.env`
  không bao giờ vào snapshot — script đã loại trừ; kiểm tra manifest không
  chứa đường dẫn `runtime/` trước khi commit snapshot.
- Monorepo (`AGENTS.md`) ghi nhận `zalo/` là snapshot một chiều; spec/contract
  phía consumer ở `notary_v2` vẫn giữ phần riêng của nó.
