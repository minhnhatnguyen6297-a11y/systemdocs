# AGENTS.md — luật làm việc trong systemdocs

Nói với người dùng như học sinh cấp 3. Dùng từ dễ hiểu; thuật ngữ bắt buộc phải
giải thích hoặc có ví dụ.

`main` chỉ chứa tài liệu. Nhánh `electron-system-shell` và nhánh
`consolidate/monorepo` dựa trên nó được phép chứa runtime Electron đã duyệt.
Không merge runtime vào `main`.

## Trước khi đọc hoặc sửa

1. Mở `README.md` để tìm đường trong cây spec.
2. Đọc `docs/spec/README.md`, rồi mọi `README.md` từ module tới thư mục cha của
   feature, cuối cùng đọc spec lá.
3. Kiểm tra trạng thái `Draft`, `Approved`, `Active` hoặc `Superseded` và nguồn.
4. Khi sửa code, đối chiếu source/test hiện tại. Spec quyết định hành vi phải có;
   code chỉ chứng minh hiện trạng.

## Đặt thông tin vào đâu

Đặt thông tin tại **cấp nhỏ nhất bao phủ toàn bộ ảnh hưởng**:

- chỉ một feature: ghi ngay trong spec feature;
- nhiều feature cùng flow: ghi trong `README.md` của flow;
- nhiều flow cùng module: ghi trong `README.md` của module;
- nhiều module: ghi trong `docs/spec/README.md`.

Kiến trúc, giao diện, câu hỏi mở, quyết định và lịch sử lựa chọn nằm trong spec
ở đúng cấp trên. Không tạo `architecture.md`, `design.md`, `decisions.md`,
`open-decisions.md` hoặc chỉ mục song song chỉ vì loại nội dung khác nhau.

Chỉ tạo file/thư mục con khi có một chức năng độc lập đáng tra cứu hoặc phụ lục
lớn như bảng trường, schema, catalog regex hay tài sản prototype. Spec cha phải
nói rõ vai trò của phụ lục; phụ lục không trở thành SOT thứ hai.

## Cấu trúc tối thiểu của feature

Spec feature trả lời các mục có liên quan:

1. Công dụng và phạm vi.
2. Người dùng và cách thao tác.
3. Input, output và flow.
4. Quy tắc nghiệp vụ và **Tại sao?**
5. Trạng thái và dữ liệu được lưu ở đâu, dạng gì.
6. Contract với feature/module khác.
7. Kiến trúc và công nghệ.
8. Giao diện.
9. Lỗi, ngoại lệ và ví dụ.
10. Câu hỏi mở, lịch sử và nguồn.

Không thêm mục rỗng cho đủ mẫu.

## Nguồn sự thật và quyết định

- Linear là SOT của task, acceptance criteria và trạng thái issue.
- `docs/spec/` là SOT sản phẩm dài hạn.
- `contracts/` giữ contract đã duyệt và schema máy đọc. Spec giải thích ý nghĩa
  rồi dẫn link; không chép schema thành bản thứ hai.
- `.agent/tasks/<LINEAR-ID>/` giữ `brief.md`, `progress.md`, `decisions.md` khi
  cần và `handoff.md`. Đây là record thực thi, không phải spec.
- Khi owner giải thích lý do, giữ nguyên ý, ví dụ, ngoại lệ, nguồn và ngày. Tách
  rõ lời owner với diễn giải của agent. Thiếu nguồn thì ghi `[CONFIRM]`.
- Draft, prototype, plan, code và task log không tự trở thành quy tắc đã duyệt.
- Khi thay đổi quyền sở hữu, cập nhật spec cũ, spec mới và mọi link trong cùng
  thay đổi. Không để hai file cùng tự nhận là SOT.

## File tạm và điều cấm

File tạm chỉ vào `.agent/scratch/`, `.tmp/`, `.cache/`, `logs/` hoặc
`artifacts/`; dọn khi xong và không commit.

Không:

- tạo Markdown mới ở root ngoài `AGENTS.md` và `README.md`;
- tạo `AGENTS.md`, `agent.md`, `memory-bank/` trong repo con;
- tạo spec, log, plan hoặc handoff rời ngoài cây quy định;
- tự chốt câu hỏi nghiệp vụ, contract hoặc kiến trúc chưa có nguồn;
- rebuild toàn bộ Graphify cho thay đổi nhỏ.

Biết file/symbol thì dùng tìm kiếm hẹp và đọc đúng đoạn. Cần quan hệ nhiều file
thì dùng graph có sẵn ở depth 1–2 rồi đối chiếu source.

## Phối hợp và khôi phục công việc

Quyết định owner ngày 14/08/2026, rút từ ADR cũ đã nhập vào đây:

- Agent chính là đầu mối với người dùng; kết quả helper chỉ là bằng chứng, không
  tự thành quyết định.
- Chỉ một agent có quyền ghi trong một worktree tại một thời điểm. Việc song
  song có ghi phải dùng phạm vi và worktree tách biệt đã được cho phép.
- Sau resume, compaction hoặc handoff, kiểm lại branch, HEAD, `git status` và
  trạng thái agent trước khi tin record cũ.
- Trạng thái task nằm trong `.agent/tasks/<ID>/`; không tạo database/dashboard
  hay rule phụ thuộc một công cụ agent cụ thể.
