---
id: decision-81
title: "Bỏ BMAD, thử Superpowers; tài liệu chuyển từ _bmad-output sang docs/"
date: '2026-10-28'
status: accepted
---

## Quyết định
- BMAD không còn hữu ích; gỡ khỏi repo, lưu tag `bmad-archive-20261028`. Không nâng BMAD v7, không Orca, không 1DevTool.
- Thử Superpowers (`.omp/extensions/superpowers/`) trên `agent/omp/superpowers-trial`.
- Tài liệu chuẩn: `docs/specs`, `docs/decisions`, `docs/plans`, `docs/planning`, `docs/brainstorming`, `docs/archive`. Plan/spec viết Markdown; bỏ export HTML plan.
- Ghi đè mặc định Superpowers: spec ghi vào `docs/specs/`, plan vào `docs/plans/` (không tạo `docs/superpowers/`).
- Tra cứu trước / không xu nịnh (AGENTS.md).

## Lý do
Một nguồn chân lý (decision-31); giảm ceremony; Superpowers có TDD và verification bắt buộc.

## Hệ quả
- Thay: `decision-bmad-canonical-shared-skills`, `decision-bmad-loop-ownership-orchestration-open`, `decision-reuse-bmad-workflows-no-new-flow`, `decision-generated-bmad-artifacts-cleanup`, `decision-html-only-for-plan-spec-brainstorming-structure`, `decision-html-plan-exhibits-not-markdown-wrapper`, `decision-html-plan-structure-remains-thariq`, `decision-native-subagents-orca-on-request` (đánh dấu Superseded).
- Đã chuyển sang `docs/` (nhánh agent/mika/docs-consolidation): decision-80 (sổ D-xxx), `legal-baseline.md`, `diagram-rules.md`, `decision-owner-diagram-rules-v2-20261027.md` từ hai nhánh PM và V2.

## Nguồn
Owner 28/10/2026; commit 9ec68bb, 117f934.
