# Brief — MIN-93

**Linear:** [MIN-93](https://linear.app/minhnotary/issue/MIN-93) — SCAFFOLD repo
Zalo độc lập, entrypoints và cấu hình. Parent: MIN-91. Điều kiện bắt đầu:
MIN-92 contract duyệt (xong 25/09/2026, `contracts/zalo-intake/`).

## Phạm vi (từ issue)

Tạo khung repo local tại `D:/zalo-intake` (kiểm tồn tại — đã kiểm, chưa có, đã
tạo + `git init -b main`): CLI run/replay/status, cấu hình `.env.example` không
secret, DB/job schema + runtime dirs riêng, types theo contract, test harness
synthetic, runbook local, verify scripts. Chỗ đặt connector/OCR adapter/API +
ranh giới package cho MIN-103. Chốt repo nguồn chính + cơ chế snapshot `zalo/`
không nested `.git`. Tránh import notary, DB/media/session chung.

## Không làm (MIN-103+)

Không kiểm kê/chuyển connector, session/listener, media, Qwen primitive, test
baseline; không xóa Zalo legacy; không parser/regex/ghép; không auto-start/
service; không listener account thật; không remote/deploy.

## Nghiệm thu (Linear)

- Replay synthetic bằng subprocess khi backend notary tắt, notary không trên
  PYTHONPATH.
- Restart giữ `captured_at`/identity trong DB module.
- Runtime paths chỉ trỏ folder module (`audit.record_access` + access.jsonl).
- Không cookie/key/ảnh thật trong Git.
- Test + lệnh verify chạy được, không account live.
- Bàn giao: commit scaffold, quyết định ownership repo/snapshot, ranh giới
  MIN-103.

## Quyết định controller (decisions.md)

Repo nguồn chính = `D:\zalo-intake`; `zalo/` = snapshot một chiều (export script
+ SNAPSHOT_MANIFEST, không `.git`); alembic không dùng (migration runner tay);
connector chỉ stub (dep zca-js vào cùng code ở MIN-103).
