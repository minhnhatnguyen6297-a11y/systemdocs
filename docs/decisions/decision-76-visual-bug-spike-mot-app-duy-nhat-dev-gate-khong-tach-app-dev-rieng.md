# Quyết định: báo lỗi giao diện nằm trong 1 app duy nhất, khóa sau cờ dev — không tách app dev riêng

## LÀ GÌ

- Tính năng báo lỗi visual là khả năng dev-only trong cùng Electron shell, bật bằng cờ `G1_VISUAL_BUG_SPIKE=1` và chỉ khi chưa đóng gói (`!app.isPackaged`).
- Lối vào: `run-dev.bat` trong worktree spike (tương đương `run.ps1`); `run.bat` vẫn mở app bình thường; không thêm nút vào Cài đặt của user.
- Không tạo app/product/build thứ hai cho developer.

## TẠI SAO

- Codebase đã theo đúng mẫu này: debug UI sau `window.G1_DEV` (`case-drafting-view.js:106`), mock dev sau `G1_DEV_NOTARY_MOCK` và bị lột khi đóng gói (`main.js:323`).
- App dev riêng sẽ nhân đôi build/ký/phân phối, dễ lệch khỏi app thật, và lỗi báo từ dữ liệu giả có thể không tái hiện đúng lỗi của user.
- Prototype hiện tại (dữ liệu giả, ảnh chỉ có khung bố cục) là giàn thử trong worktree; khi kiểm chứng xong với dữ liệu thật thì merge cơ chế sau cờ dev và xóa giàn thử.
