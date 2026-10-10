---
id: decision-76
title: 'Spike visual bug ghi chu nguoi dung nguyen van vao report local vi note la nguoi tu viet khong phai du lieu scrape'
date: '2026-10-10 09:30'
status: accepted
---
## Context

Bao cao bug cua spike luu duoc vi tri (selector) nhung mat ghi chu: `custom/policy.cjs` thay moi note khong trung dung 1 trong 3 cau synthetic bang `[note omitted: synthetic vocabulary only]`, va picker chi cho 3 cau do. 19/37 report da luu bi mat ghi chu, nen agent debug khong hieu nguoi dung thay loi gi. Owner yeu cau ghi chu that duoc luu nguyen van de agent doc duoc.

## Decision

Note nguoi dung tu viet la truong duy nhat duoc luu nguyen van trong report local (`reports/<id>.json`), khong bi redact hang loat. Picker bat buoc nhap note truoc khi luu, bo tien ich 3 cau synthetic. Giu nguyen pham vi an danh khac: khong DOM text, attribute value, storage, state, log body, duong dan. Report van nam trong `_bmad-output/tmp/` (git-ignored, chi local); muon cong bo phai sanitize note truoc.

## Consequences

Agent debug doc duoc mo ta loi qua field `note` cua report JSON. Report local gio chua van ban nguoi dung tu viet — khong duoc publish nguyen trang. Report cu bi mat ghi chu giu nguyen, khong sua va khong the phuc hoi.
