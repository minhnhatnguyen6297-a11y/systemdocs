"""Split engine rebuild from DOCX integration, using Backlog CLI exclusively."""
from pathlib import Path
import json
import re
import subprocess

folder = Path(__file__).resolve().parent
root = folder.parents[1]
state_file = folder / "backlog-publish-state.json"
state = json.loads(state_file.read_text(encoding="utf-8"))
entry = "C:/Users/MINH/AppData/Roaming/npm/node_modules/backlog.md/cli.js"

def cli(*args):
    run = subprocess.run(["rtk", "proxy", "node", entry, *args], cwd=root,
                         capture_output=True, encoding="utf-8", errors="replace")
    with (folder / "extraction-strategy-cli.log").open("a", encoding="utf-8") as log:
        log.write("\n" + " ".join(args[:3]) + "\n" + run.stdout + "\n" + run.stderr)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return run.stdout

def save():
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

spec = "docs/spec/notary_v2/input/document-extraction.md"
criteria = [
    "Danh mục Owner được đối chiếu mẫu: mỗi loại có nhóm cấu trúc, vùng/trường, mẫu/đáp án hoặc nhãn thiếu mẫu; khoảng 30 loại/10 nhóm không bị coi là số đã chốt.",
    "Loại văn bản, nhóm cấu trúc và quy tắc vùng/trường tách rõ; ít nhất hai loại có mẫu chứng minh dùng chung một vùng/rule, không chép 30 engine.",
    "Nhận diện dùng dấu hiệu/loại trừ/ranh giới cấu trúc; nhiều kết quả phù hợp hoặc không biết loại được báo rõ, không chọn cấu hình đầu tiên hay luôn transfer.",
    "Các biến thể ông A, ông: A, ông/bà A, ông/bà: A, đánh số/bảng/xuống dòng và ca âm ngày chết/địa chỉ/lời chứng có đáp án đúng và test.",
    "Dự phòng có phạm vi và thứ tự rõ, có trace rule/version/vùng/nguồn; không quét toàn file bằng mọi regex; lỗi/timeout không bị nuốt thành missing.",
    "Bộ có đáp án chốt cho nghiệm thu trả đúng loại/vùng, số Người/Tài sản, giá trị và người/thửa chứa trường; không bản ghi giả; mỗi thửa riêng, cùng sổ cùng serial, tổng diện tích giữ riêng.",
    "Bộ giữ lại độc lập và các ca biến thể có báo cáo theo loại/nhóm/trường: đúng, sai, bỏ sót, mơ hồ, đạt toàn bộ, thời gian/lỗi; partial không tính thành công đầy đủ.",
    "Bàn giao hợp đồng đầu vào chữ/layout và đầu ra có bằng chứng cho TASK-6, cấu hình có phiên bản, fixture/đáp án và giới hạn đã hỗ trợ; chưa có đủ danh mục/mẫu thì không báo phủ đủ 30 loại.",
]
if "engine" not in state["tasks"]:
    before = set((root / "backlog/tasks").glob("*.md"))
    args = ["task", "create", "Xay lai engine trich van ban theo cau truc va rule dung chung",
            "--type", "feature", "--status", "To Do", "--labels", "notary,regex,rebuild",
            "--description", "Owner yêu cầu làm lại chiến lược trích thay vì vá từng mẫu: sẽ liệt kê khoảng 30 loại văn bản, dự kiến khoảng 10 nhóm cấu trúc. Engine phải nhận loại/cấu trúc trước, chia vùng và dùng các quy tắc vùng/trường có biến thể, định tuyến và dự phòng rõ. Mẫu thật/đáp án và tiêu chí thành công là điều kiện trước khi mở rộng. Code hiện có chia vùng nhưng adapter luôn chọn transfer, chưa chứng minh bao phủ. Task này sở hữu lõi/rules/bộ chấm; TASK-6 sở hữu reader DOCX/bằng chứng/adapter/Stage. Chưa implement trong phiên lập task; chờ Owner cung cấp danh mục và vị trí mẫu để chốt ma trận loại-nhóm-mẫu.",
            "--ref", spec, "--ref", "tools/regex_workbench/README.md",
            "--ref", ".agents/review-plan-20261004/investigation-report.md",
            "--ref", "backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md", "--plain"]
    for criterion in criteria:
        args += ["--ac", criterion]
    output = cli(*args)
    created = set((root / "backlog/tasks").glob("*.md")) - before
    if len(created) != 1:
        raise RuntimeError("Cannot identify engine task: " + output)
    path = created.pop()
    text = path.read_text(encoding="utf-8-sig")
    identity = re.search(r"^id:\s*(TASK-\d+)", text, re.M).group(1)
    state["tasks"]["engine"] = {"id": identity, "path": path.relative_to(root).as_posix()}
    save()
else:
    identity = state["tasks"]["engine"]["id"]

if not state.get("engine_strategy_decision"):
    before = set((root / "backlog/decisions").glob("*.md"))
    title = "Owner 04/10: tach task engine, nhan cau truc-chia vung-dung rule chung co mau va dap an vi va regex tung mau khong chung minh dung; " + identity
    output = cli("decision", "create", title, "--status", "accepted", "--plain")
    created = set((root / "backlog/decisions").glob("*.md")) - before
    if len(created) != 1:
        raise RuntimeError("Cannot identify decision: " + output)
    path = created.pop()
    state["decisions"].append({"title": title, "path": path.relative_to(root).as_posix()})
    state["engine_strategy_decision"] = True
    save()

intake_criteria = [
    "Reader DOCX giữ đúng chữ/thứ tự đoạn-bảng lồng/vị trí nguồn, chọn một biểu diễn AlternateContent; không thành hai người hoặc dedup người theo tên.",
    "Adapter dùng bộ nhận diện/định tuyến engine mới của " + identity + ", không luôn load transfer và không sao chép rules; trace nguồn/rule/profile/vùng được giữ trong gợi ý theo contract.",
    "Mẫu có đáp án 3 người/1 tài sản giữ đúng 3/1 và giá trị qua adapter-dialog-Stage-commit-reload; mỗi thửa riêng, cùng sổ cùng serial.",
    "Normalizer giữ serial free text và tổng diện tích độc lập khi có land_rows; thiếu giấy tờ không xóa người rõ tên, không bịa để vượt Stage.",
    "Không nhận loại, lỗi rule hoặc vùng/bản ghi mơ hồ hiện đúng phạm vi; không ghi nhận trích đầy đủ thành công khi còn thiếu dữ liệu nguồn.",
    "Source_refs/hash/context/binding đúng qua sửa/reorder/xóa và mở lại; kiểm bộ giữ lại độc lập của engine qua đường DOCX thật, tách lỗi reader/engine/adapter.",
]
args = ["task", "edit", "TASK-6", "--depends-on", "TASK-3," + identity,
        "--description", "Tích hợp engine trích mới " + identity + " vào DOCX và Stage. Phần nhận loại/chia vùng/rules/bộ chấm được tách sang task engine theo yêu cầu Owner; TASK-6 giữ reader ZIP/XML, bản đồ bằng chứng, adapter/normalizer, dialog và save/reload. Cần sửa RE-05 AlternateContent và TS-03 bỏ tổng diện tích, giữ số bản ghi/giá trị engine đã chấm khi đi vào Stage. Không tạo một bộ regex riêng trong adapter.",
        "--add-ref", spec, "--add-ref", state["tasks"]["engine"]["path"], "--plain"]
for criterion in intake_criteria:
    args += ["--acceptance-criteria", criterion]
cli(*args)
cli("task", "edit", "TASK-3", "--remove-ac", "5", "--ac",
    "Diện tích tổng 300 và dòng loại đất 100 giữ riêng xuyên Stage/save/reload; không ghi đè nguồn. Điền Word được kiểm tại TASK-8/TASK-10 để không tạo phụ thuộc vòng.", "--plain")
state["engine_strategy_tasks_updated"] = True
save()
print("Created", identity, state["tasks"]["engine"]["path"])
print("TASK-6 now owns DOCX integration and depends on TASK-3 +", identity)
