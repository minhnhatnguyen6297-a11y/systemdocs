<!-- Điền đủ các mục. Mục nào không áp dụng ghi "Không áp dụng" + lý do, không xoá mục. -->

## Mục tiêu / Issue
- Issue: #
- Mục tiêu (1–2 câu, nói theo nghiệp vụ):

## Thay đổi
- 
- Quyết định/spec liên quan (D-xxx, file spec):

## Bằng chứng test
<!-- Dán LỆNH và OUTPUT thật (rút gọn phần dài), kể cả lỗi và bước bị bỏ qua. -->
```text
$ cd shell && npm test
...
$ python -m pytest shell/test notary_v2/tests -q -rA --basetemp <dir>
...
$ python tools/ci/known_failures.py ...
summary: ...
```
- Bước bị bỏ qua / chưa chạy được (và lý do):

## Ảnh / video
<!-- Ảnh trước/sau cho thay đổi UI (từ harness CDP hoặc tools/file-bug.sh). Chỉ dữ liệu giả lập. -->

## Rủi ro
- Ảnh hưởng tới: 
- Cách rollback:
- Giả định đã đặt ra:

## Checklist Definition of Done (docs/definition-of-done.md)
- [ ] Đã tìm giải pháp có sẵn trên GitHub trước khi tự viết (dán URL ở trên hoặc ghi "không tìm thấy")
- [ ] Test mới/sửa cho hành vi đổi; CI xanh, không thêm lỗi mới ngoài `tools/ci/known-failures-*.txt`
- [ ] Không skip/xoá test để cho xanh; test cách ly có issue ref
- [ ] Spec/decision cập nhật nếu đổi hành vi
- [ ] Đã review (Superpowers `requesting-code-review` hoặc agent Reviewer) và xử lý góp ý
- [ ] Chỉ dữ liệu giả lập; gitleaks sạch; không commit secret/dữ liệu khách hàng
- [ ] Không `git stash`; không code trực tiếp trên `main`
- [ ] Thay đổi kiến trúc/schema/dependency đã được owner duyệt
