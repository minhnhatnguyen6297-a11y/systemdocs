# Việc ngắn-rõ đi luồng ngắn; việc khó mở full workflow

Ngày: 2026-10-12. Nguồn: yêu cầu hiện tại của owner.

## Quyết định — WHAT

- Việc **ngắn, rõ** → todo list + **một** implementation worker → test → review.
- Việc **khó** → mở full workflow.
- Đây là quyết định owner đã chốt cho luồng code. Chưa triển khai vào workflow/AGENTS.md trong phiên này; chỉ ghi nhận.

## Lý do — WHY

Owner: “orchestrate, gọi role slow để review”. Kỳ vọng owner nêu rõ: “short clear work => todo list + ONE implementation worker => test => review; hard problem activates full workflow.” Mục đích: việc nhỏ không phải gánh toàn bộ ceremony, việc khó vẫn được kiểm soát đầy đủ.

## Đang mở — chưa phải luật

- Băn khoăn **4 “thinking stream” tự động chạy không được giải thích** là điểm cần làm rõ tiếp, **chưa** phải luật đã chọn. Đây là open refinement.
- Đề xuất của reviewer (role slow) là **dữ liệu**, không tự thành luật. Báo cáo review read-only nằm ở `docs/tmp/orca-slow-flow-review/review-slow.md` (không commit, không phải nguồn chuẩn).
- Chưa chốt điều kiện kích hoạt cơ học nào cho “ngắn-rõ vs khó”; cần owner xác nhận trước khi đưa vào AGENTS.md/workflow.

## Bối cảnh kỹ thuật (bằng chứng, không phải quyết định)

- Review chạy qua Orca thật, một worker role `slow`; `slow` là model role trong `C:/Users/MINH/.omp/agent/config.yml` (`slow: openai-codex/gpt-6.1-sol:high`), dispatch bằng `--agent codex --model gpt-6.1-sol --effort high`; receipt xác nhận `launch.effective` khớp.
