---
id: decision-7
title: >-
  Owner 04/10: tach task engine, nhan cau truc-chia vung-dung rule chung co mau
  va dap an vi va regex tung mau khong chung minh dung; TASK-11
date: '2026-10-04 16:19'
status: accepted
---
## Context

Sửa regex theo từng mẫu văn bản lẻ (vá từng `if` theo tên file/label của một
biểu mẫu) chứng minh được "chạy đúng file đó" chứ không chứng minh đúng cấu
trúc. Engine cũ trộn nhận diện cấu trúc và bóc trường trong một khối, khó bảo
trì và không tái dùng được giữa các loại văn bản.

## Decision

Tách riêng một task engine (TASK-11). Engine phải:

- nhận diện cấu trúc trước (chia vùng: mở đầu, đương sự, người chết, tài sản,
  phân chia, lời chứng);
- dùng quy tắc vùng/trường dùng chung, không theo từng mẫu;
- có bộ mẫu kèm đáp án để kiểm chứng (golden);
- không suy giá trị khi thiếu căn cứ.

## Consequences

- TASK-5 (thừa kế) là spike cung cấp kiến thức trường + mẫu, không merge
  nguyên trạng; engine mới làm ở TASK-11.
- Owner 06/10/2026 chốt lõi = `tools/regex_workbench/engine` (đã có zoner +
  provenance + trạng thái trung thực); kiến thức `extract_contract.py` port
  thành profile `inheritance`. Lõi phục vụ cả đề xuất placeholder cho mẫu
  Word chưa gắn và nhận input là text thô.
