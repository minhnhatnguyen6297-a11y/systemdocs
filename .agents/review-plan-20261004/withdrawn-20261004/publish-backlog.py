"""Write review decisions/tasks/plan ONLY through Backlog CLI; resume safely."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
STATE_PATH = OUT / "backlog-publish-state.json"
BACKLOG_ENTRY = Path("C:/Users/MINH/AppData/Roaming/npm/node_modules/backlog.md/cli.js")
state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"decisions": [], "tasks": {}}

def save():
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def cli(*args):
    # Avoid Windows .cmd shim: it rejects arguments containing actual newlines.
    run = subprocess.run(["rtk", "proxy", "node", str(BACKLOG_ENTRY), *args], cwd=ROOT,
                         capture_output=True, encoding="utf-8", errors="replace")
    with (OUT / "backlog-cli.log").open("a", encoding="utf-8") as log:
        log.write(f"\nCOMMAND: backlog {' '.join(args[:3])}\n{run.stdout}\n{run.stderr}\nEXIT: {run.returncode}\n")
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return run.stdout

decision_titles = [
    "Owner 04/10: rut nghi van nham dia chi/noi cap vi da xac nhan nhin nham; TASK-2",
    "Owner 04/10: bat buoc dia chi-thua-to-dien tich tong-loai dat; serial tu do optional vi khong co dinh dang chung; TASK-2",
    "Owner 04/10: tim dia chi bang cum ten khong can ngay/tinh, giu cap xa/phuong vi nguoi dung co the chi biet mot phan; TASK-2",
    "Owner 04/10: viet lai engine Word va chuyen mau cu, trich dung du nguoi/tai san vi xuat duoc file chua chung minh dung noi dung; TASK-2",
    "Owner 04/10 Q4: moi thua mot tai san, cung so cung serial vi serial nhan dien so khong phai rieng thua; TASK-2",
    "Owner 04/10 Q5: Word chi kiem du lieu mau can, mau Nguoi khong doi tai san/so do vi khong can cac nguon do; TASK-2",
]
for title in decision_titles[len(state["decisions"]):]:
    before = set((ROOT / "backlog/decisions").glob("*.md"))
    output = cli("decision", "create", title, "--status", "accepted", "--plain")
    added = set((ROOT / "backlog/decisions").glob("*.md")) - before
    if len(added) != 1:
        raise RuntimeError("Cannot uniquely identify new decision: " + output)
    path = added.pop()
    state["decisions"].append({"title": title, "path": path.relative_to(ROOT).as_posix()})
    save()
    print("Decision:", path.name)

spec_stage = "docs/spec/notary_v2/stage.md"
spec_addr = "docs/spec/notary_v2/administrative-address.md"
spec_timeline = "docs/spec/notary_v2/administrative-timeline.md"
spec_input = "docs/spec/notary_v2/input/docx-import.md"
spec_word = "docs/spec/notary_v2/word-output.md"
report = ".agents/review-plan-20261004/investigation-report.md"
tasks = [
    ("assets", "Sua Stage tai san serial tu do va dien tich tong", "bug", [], [spec_stage],
     "TS-01/02/03; Owner đã chốt 5 trường bắt buộc, serial tự do/optional và mỗi thửa một tài sản, cùng sổ cùng serial. Sửa trọn UI-wire-snapshot-DB-save-reload; bỏ serial giả và liên kết chỉ theo serial. DB migration cho serial null/non-unique phải giữ dữ liệu. Chi tiết gói A trong TASK-2; chưa implement ở phiên review.",
     ["Chỉ địa chỉ, thửa, tờ, tổng diện tích và loại đất bắt buộc; thiếu từng mục báo đúng dòng/ô.",
      "Serial null hoặc 1234/X-2020 không bị đổi/sinh giả qua đọc-lưu-mở lại; schema/client/server thống nhất.",
      "Hai thửa cùng serial lưu thành hai entity riêng, reorder/reload giữ định danh; không tự .first() liên kết theo serial.",
      "DB cũ chuyển serial nullable/non-unique không mất ID, giá trị, liên kết; kiểm trên bản sao.",
      "Diện tích tổng 300 và dòng loại đất 100 giữ riêng xuyên Stage/save/reload/Word; không ghi đè nguồn."]),
    ("sources", "Kiem chung nguon va phien ban kho dia chi hanh chinh", "task", [], [spec_timeline, spec_addr],
     "DC-06/08: phân biệt danh mục/câu nguồn Bando với lịch sử có ngày được xác nhận; bổ sung nguồn chính thức và báo phạm vi dữ liệu. Sửa A→B→A trả tên sai phiên bản. Giữ kho hiện có, không dựng hệ mới. Chi tiết gói B TASK-2.",
     ["Tên/cha/evidence trả về đúng dataset_version đang hoạt động; A→B→A không lấy tên B.",
      "Quan hệ confirmed có nguồn chính thức, ngày hiệu lực, đơn vị trước/sau; quan hệ chưa đủ bằng chứng vẫn pending.",
      "Có ca gộp/chia một phần với chứng cứ và kết quả truy vấn; không nâng toàn bộ câu nguồn thành confirmed.",
      "Import sai/thiếu/hỏng không đổi kho; giữ lịch sử curator; baseline số lượng đổi phải có nguồn và kiểm đầy đủ.",
      "Bàn giao bảng phạm vi toàn quốc/đợt thay đổi đã xác nhận và khoảng trống; không báo đạt khi còn thiếu nguồn."]),
    ("lookup", "Tra dia chi theo cum ten tai Nguoi Dat va Niem yet", "feature", ["sources"], [spec_addr],
     "DC-01…05: tra cứu nền bằng cụm tên không đòi tỉnh/ngày, giữ xã/phường/tỉnh, tìm chữ trong chính ô niêm yết. Sửa kết quả tự nay là và đoán cấp bằng ngày. Q3 đang chờ Owner về cách ghi địa chỉ sau Áp dụng; tìm/hiển thị có thể làm trước. Chi tiết gói C TASK-2.",
     ["Gõ xã Yên Bình không có tỉnh/ngày trả danh sách đúng cấp, tên cũ/mới và tỉnh/nguồn phân biệt.",
      "Địa chỉ hiện hành được nhận biết, không nối nay là chính nó; không suy cấp địa chỉ chỉ bằng ngày giấy tờ.",
      "Người/Đất/Niêm yết tìm chữ đang nhập; Niêm yết không buộc có tài sản.",
      "Response cũ khi sửa chữ/đổi hồ sơ bị bỏ; lookup không tự ghi/save và không khóa nhập khi lỗi.",
      "Q3 phải được ghi decision/spec trước triển khai Áp dụng; giữ thôn/số nhà, không tự chọn quan hệ một phần."]),
    ("intake", "Sua trich hop dong DOCX du Nguoi Tai san va bang chung", "bug", ["assets"], [spec_input, spec_stage],
     "RE-01…05, TS-03: sửa reader/profiles/grouping/adapter và chuyển Stage, không chỉ vá một regex. Mỗi thửa một tài sản, cùng sổ cùng serial đã chốt. Chuẩn bị bộ hợp đồng có đáp án từng field và bộ giữ lại cho parent. Chi tiết gói D TASK-2.",
     ["Hợp đồng 3 người/1 tài sản trả đúng 3/1 và mọi giá trị nguồn có trong bộ đáp án, không tên giả từ ngày chết/địa chỉ.",
      "1. Ông, khai nhận/thỏa thuận/hai bên, bảng lồng và P./TP. có ca hồi quy; loại ngoài phạm vi báo rõ.",
      "AlternateContent chỉ đọc một biểu diễn phù hợp hoặc báo chưa xác định; không đọc Choice và Fallback thành hai người.",
      "Mỗi thửa tạo một tài sản kể cả không nhãn Tài sản N; cùng sổ giữ cùng serial; land_rows không thành tài sản mới.",
      "Giữ tổng diện tích riêng, đủ trường nguồn; thiếu/mơ hồ giữ bằng chứng và báo kiểm, không bịa hoặc buộc ID để nhận người rõ tên.",
      "Adapter-dialog-Stage-commit-reload giữ field/span/hash/context qua sửa/reorder/xóa; báo kết quả trên bộ giữ lại độc lập."]),
    ("contacts", "Sua nut Danh ba va chon nguoi nhan UQ theo ID", "bug", [], [spec_stage, spec_word],
     "DB-01/02: nút bị khóa sau input và tự gán ID đầu tiên khi trùng tên. Sửa chọn danh bạ theo ID, phân biệt người, tìm ngoài 200 đầu, tạo mới riêng. Q2 chờ xác nhận nguồn UQ trong Word; không cần chờ Q2 để sửa nút và ID. Chi tiết gói E TASK-2.",
     ["Nút dùng được ngay sau input/change/blur hợp lệ, không cần thao tác khác để vẽ lại.",
      "Chọn người ID 22 giữa hai người cùng tên lưu/reload đúng 22; gõ tên mơ hồ không tự gán ID 11.",
      "Tìm được người ngoài danh sách 200 đầu; hủy picker không đổi draft; tạo mới không tạo tên rỗng.",
      "Q2 ghi decision/spec trước đổi nguồn nhóm UQ; danh bạ và template không tự dùng hai nghĩa chưa được xác nhận."]),
    ("word", "Viet lai engine Word theo catalog moi va du lieu mau can", "feature", ["assets", "contacts"], [spec_word, spec_stage],
     "Viết lại phần xác định dữ liệu/điền token; giữ helper định dạng an toàn nếu phù hợp. Q5 đã chốt chỉ kiểm dữ liệu mẫu cần, mẫu Người không đòi tài sản/sơ đồ; xử lý cả đường lưu DB còn bắt tài sản. Q1/Q2 chờ Owner về nghĩa token cũ/UQ. Sửa W-05 schema response lỗi. Chi tiết gói F TASK-2.",
     ["Q1/Q2 được ghi decision/spec trước phần phụ thuộc; catalog mới có một nghĩa rõ, đúng người/ghế/vai trò đã lưu.",
      "Mẫu chỉ Người xuất được khi chưa tài sản/sơ đồ; đường lưu hỗ trợ hợp lệ, không tạo asset giả; mẫu cần nguồn nào kiểm nguồn đó.",
      "Tổng diện tích xuất đúng trường tổng, ghế trống không dồn, trùng tên/reorder/xóa không đổi danh tính ngoài spec.",
      "Response original mapping invalid và mọi block_reason thật phù hợp schema/validator/examples.",
      "Batch/original giữ nguồn hash, binding/context, hủy/cleanup/publish; thiếu dữ liệu báo rõ, expected độc lập với resolver."]),
    ("migration", "Chuyen va kiem tung vi tri placeholder trong toan bo mau Word", "task", ["word"], [spec_word, "notary_v2/word_templates/placeholder_mapping.md"],
     "W-02/04: kiểm đủ inventory 22 mẫu được bàn giao, chuyển token cũ sang nghĩa catalog mới theo từng vị trí, không giữ alias rồi báo đã chuyển hết. Q1 phải được chốt. Giữ mẫu gốc, bản sao, manifest và kiểm Word trực quan; đưa bộ được duyệt vào nơi runtime dùng. Chi tiết gói G TASK-2.",
     ["Có inventory nguồn/hash và mapping từng occurrence token cũ theo Q1; vị trí không rõ nghĩa còn mở, không báo hoàn tất.",
      "Bộ mới không còn token legacy ngoài danh sách Owner chủ ý cho phép; phân biệt engine compatibility với mẫu đã chuyển.",
      "Nguồn không đổi hash; run bị tách, bảng, header/footer và 5 mẫu .doc có bằng chứng chuyển/xem đúng.",
      "Mỗi mẫu xuất đúng người/tài sản theo đáp án độc lập, kể cả đổi thứ tự Stage; định dạng được xem trực quan.",
      "Bộ mẫu được duyệt nằm ở nơi runtime thực sự sử dụng, không chỉ artifact ignored."]),
    ("integration", "Kiem tich hop dong goi va parent review cuoi Notary", "task", ["lookup", "intake", "contacts", "word", "migration"], [spec_stage, spec_addr, spec_input, spec_word],
     "Nghiệm thu chuỗi nhập-Stage-lưu-địa chỉ-danh bạ-Word qua Electron và bản đóng gói. Parent kiểm diff, bộ đáp án giữ lại, Word từng trang và ca hỏng. Chi tiết gói H/checklist TASK-2; agent implement bàn giao trước, parent quyết định chấp nhận.",
     ["Electron chạy chuỗi hợp đồng có đáp án, hai thửa cùng serial, đúng ID UQ, tra địa chỉ ba loại ô và xuất qua hộp thư mục Windows.",
      "Ca thiếu trường/nguồn hỏng/truy vấn cũ/mapping sai/hủy/trùng file không đổi nguồn hoặc để file dở.",
      "Bản đóng gói ở thư mục mới/app data riêng có đúng kho/catalog/engine và không lồng thư mục sai.",
      "Có log test, skip/lỗi môi trường, fixture độc lập, DB migration, nguồn địa chỉ, manifest Word và ảnh trang; parent truy cập được.",
      "Parent review phản ví dụ và bộ giữ lại; docs/contract không mâu thuẫn; tầng chưa chạy không được báo nghiệm thu."]),
]
for key, title, kind, deps, refs, desc, ac in tasks:
    if key in state["tasks"]:
        continue
    args = ["task", "create", title, "--status", "To Do", "--type", kind,
            "--labels", "notary,repair", "--description", desc, "--ref", report,
            "--ref", "backlog/tasks/task-2 - Review-va-lap-plan-sua-Notary-Word-DOCX-va-dia-chi.md", "--plain"]
    for ref in refs:
        args += ["--ref", ref]
    for item in ac:
        args += ["--ac", item]
    for dep in deps:
        args += ["--depends-on", state["tasks"][dep]["id"]]
    before = set((ROOT / "backlog/tasks").glob("*.md"))
    output = cli(*args)
    added = set((ROOT / "backlog/tasks").glob("*.md")) - before
    if len(added) != 1:
        raise RuntimeError("Cannot uniquely identify new task: " + output)
    path = added.pop()
    raw = path.read_text(encoding="utf-8-sig")
    task_id = re.search(r"^id:\s*(TASK-\d+)", raw, re.M).group(1)
    state["tasks"][key] = {"id": task_id, "path": path.relative_to(ROOT).as_posix()}
    save()
    print("Task:", task_id, title)

plan = (OUT / "repair-plan.md").read_text(encoding="utf-8")
for key, item in state["tasks"].items():
    plan = plan.replace("{{" + key + "}}", item["id"])
if "{{" in plan:
    raise RuntimeError("Unresolved task reference")
decision_list = "\n".join(f"- `{item['path']}` — {item['title']}" for item in state["decisions"])
plan += "\n\n## Quyết định đã ghi qua Backlog CLI\n\n" + decision_list + "\n"
notes = """Review 04/10/2026: đã rút NG-01 theo đính chính Owner. Runtime/schema/contract/mẫu Word chưa bị sửa. Đã ghi đích yêu cầu vào 5 spec, phân biệt hiện trạng với nghiệm thu.

Đã chốt: 5 trường tài sản bắt buộc; serial tự do/optional; tra cụm tên không cần tỉnh/ngày và giữ cấp; engine Word mới + chuyển mẫu; trích đúng đủ bản ghi/trường. Q4: mỗi thửa một tài sản, cùng sổ cùng serial, vì serial nhận diện sổ. Q5: chỉ kiểm dữ liệu mẫu cần, mẫu Người không đòi tài sản/sơ đồ. Nguồn: yêu cầu và câu trả lời trực tiếp Owner trong phiên review 04/10. Chi tiết lý do/spec/đường sửa có trong plan và các decision được liệt kê.

Còn Q1/Q2/Q3 chưa trả lời; khuyến nghị trong plan chưa được duyệt. Tất cả task repair To Do, chưa có code implement hoặc AC sửa được tick.

Owner bổ sung: engine trích được tách sang TASK-11; TASK-6 chỉ giữ reader/bằng chứng/adapter/DOCX→Stage và phụ thuộc TASK-3/TASK-11. Chiến lược nhận loại/nhóm cấu trúc→chia vùng→rules dùng chung→dự phòng có kiểm, mẫu/đáp án trước mở rộng đã ghi document-extraction.md và decision riêng. Khoảng 30 loại/10 nhóm chưa là danh mục đã kiểm; chờ Owner liệt kê và chỉ vị trí mẫu. Tham khảo invoice2data/Dedoc bằng tài liệu chính thức; chưa chọn/cài chúng làm dependency. Sửa tiêu chí diện tích của TASK-3 đến save/reload, Word do TASK-8/10 kiểm để tránh phụ thuộc vòng.

Thêm 4 lỗi có bằng chứng: AlternateContent đọc hai nhánh thành hai người; kho A→B→A trả tên B; họ tên trùng tự gán ID đầu; schema thiếu word.original_mapping_invalid. Tách thêm NG-02 từ bằng chứng UI trước: người sống bị gắn nhãn/lời nhắc giấy khai tử, khác nghi vấn hoán đổi trường NG-01 đã rút. Parent xác minh các báo cáo đọc bằng 2 Luna; Astra đã dừng. Không ghi hoàn thành đủ mọi reviewer BMAD. Graphify thiếu, map cũ đã đọc nhưng không dựng lại được.

Test điều tra trước: 832 Python passed, 8 skipped; 227 Node passed; 81 contract fixtures đúng dự kiến — là tổng các lượt riêng, không full suite mới. Bốn phép kiểm bổ sung đã lưu trong .agents/review-plan-20261004. Chưa chạy Electron/bản cài/xem toàn bộ Word ở phiên review. Các tầng đó là AC của task integration và parent review.
"""
cli("task", "edit", "TASK-2", "--ref", report,
    "--description", "Review code/docs 19 commit đến 53c7804; rút nghi vấn nhầm trường, kiểm thêm lỗi, ghi yêu cầu Owner đã chốt, lập plan chi tiết cho agent khác implement và checklist parent review. Q4/Q5 đã chốt, Q1/Q2/Q3 còn mở. Không implement runtime trong task này.",
    "--plan", plan, "--notes", notes, "--plain")
state["plan_published"] = True
save()
print("Published detailed plan and decision notes to TASK-2.")
