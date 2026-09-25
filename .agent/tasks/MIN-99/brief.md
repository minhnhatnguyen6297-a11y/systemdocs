# MIN-99 — INTEGRATE: notary sync gói raw + Document Intake

Linear SOT: máy chính pull gói raw từ module Zalo; staging/ready/imported/
quarantine; validate byte/hash/schema/source; lưu raw + ledger txn rồi ACK;
enqueue parser; OCR request client; không ảnh/SDK/cookie/DB bot; parser lỗi
không hủy ACK; result revision không ghi đè dữ liệu đã duyệt.

Baseline: producer module `D:\zalo-intake` @ 9b0f797 (contract intake.*.v1,
schemas vendored byte-identical vào `notary_v2/schemas/zalo-intake/`).
Consumer là code MỚI trong notary_v2 — không tái dùng legacy zalo_inbox.
