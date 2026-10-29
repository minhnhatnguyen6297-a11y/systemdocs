# Cài đặt và chạy trên máy Windows

Hướng dẫn cho người không quen Git. Gõ lệnh trong **PowerShell** (bấm Start → gõ
`PowerShell` → Enter). Phiên bản dưới đây lấy từ CI (`.github/workflows/ci.yml`),
`shell/package.json` và các file `requirements.txt` — CI chạy đúng các bản này.

## 1. Cần cài trước (một lần)

| Phần mềm | Phiên bản | Tải ở đâu | Kiểm tra |
|---|---|---|---|
| Git for Windows | bản mới nhất | https://git-scm.com/download/win | `git --version` |
| Python | **3.12.x** (CI dùng 3.12). Khi cài, tick **"Add python.exe to PATH"** | https://www.python.org/downloads/windows/ | `py -3.12 --version` |
| Node.js | **22.x LTS** (CI dùng 22; npm đi kèm) | https://nodejs.org/en/download | `node --version` |

Electron (`^44.7.2`) và electron-builder được `npm ci` tự cài, không cần tải riêng.
Thư viện Python nằm trong `notary_v2/requirements.txt` và
`shell/sidecar/requirements.txt` (FastAPI, SQLAlchemy, python-docx, PyMuPDF, …).

## 2. Lấy mã nguồn

Lần đầu (chọn thư mục, ví dụ `C:\work`):

```powershell
cd C:\work
git clone https://github.com/minhnhatnguyen6297-a11y/systemdocs.git
cd systemdocs
git checkout consolidate/monorepo
```

Những lần sau, lấy bản mới nhất:

```powershell
cd C:\work\systemdocs
git checkout consolidate/monorepo
git pull
```

> `consolidate/monorepo` là nhánh chính. Không sửa file trực tiếp trên nhánh này
> nếu không định gửi PR. Nếu `git pull` báo xung đột, xem mục 6.

## 3. Cài thư viện (lần đầu, và mỗi khi `requirements.txt`/`package-lock.json` đổi)

```powershell
cd C:\work\systemdocs
py -3.12 -m venv notary_v2\venv
notary_v2\venv\Scripts\python.exe -m pip install -U pip
notary_v2\venv\Scripts\python.exe -m pip install -r shell\sidecar\requirements.txt -r notary_v2\requirements.txt pytest
cd shell
npm ci
cd ..
```

`run.bat` tự tìm Python ở `notary_v2\venv\Scripts\python.exe`, nên phải tạo
venv đúng đường dẫn này.

## 4. Chạy ứng dụng

Bấm đúp `run.bat` ở thư mục gốc, hoặc:

```powershell
cd C:\work\systemdocs
.\run.bat
```

- `run-dev.bat`: như `run.bat` nhưng bật công cụ báo lỗi bằng ảnh
  (Ctrl+Shift+B → chọn phần tử → ghi chú → Save report; báo cáo nằm trong
  `_bmad-output\tmp\visual-bug-reporting`).
- Muốn dùng Python khác: đặt biến `G1_PYTHON` trỏ tới `python.exe` trước khi chạy.

## 5. Chạy test (giống CI)

```powershell
cd C:\work\systemdocs
# Test JavaScript
cd shell
npm test
cd ..
# Test Python (sidecar + engine)
notary_v2\venv\Scripts\python.exe -m pytest shell\test notary_v2\tests -q -p no:cacheprovider --basetemp "$env:TEMP\pytest-systemdocs"
```

Một số test JS gọi `python`; nếu báo thiếu module, chạy trước trong cùng cửa sổ:
`$env:PATH = "$PWD\notary_v2\venv\Scripts;$env:PATH"`.

Lỗi đã biết (không làm đỏ CI) liệt kê ở `tools/ci/known-failures-*.txt`; so sánh
giống CI:

```powershell
notary_v2\venv\Scripts\python.exe -m pytest shell\test notary_v2\tests -q -p no:cacheprovider -rA > pytest.txt
notary_v2\venv\Scripts\python.exe tools\ci\known_failures.py pytest pytest.txt tools\ci\known-failures-py-windows.txt
```

Trên Linux/máy agent: `tools/dev/setup-worktree.sh` rồi `tools/dev/run-tests.sh`.

## 6. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `py` hoặc `python` không nhận | Cài lại Python, tick "Add to PATH"; mở PowerShell mới. |
| `[LOI] Chua co Electron` khi chạy `run.bat` | Chạy `npm ci` trong thư mục `shell`. |
| `npm ci` báo lỗi mạng/quyền | Đóng app đang chạy (Electron giữ file), chạy lại; kiểm tra mạng/proxy. |
| `ModuleNotFoundError` khi chạy test/app | Chạy lại bước 3 (thư viện mới được thêm). |
| `running scripts is disabled` trong PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` rồi mở lại PowerShell. |
| Chữ tiếng Việt lỗi khi in log test | `$env:PYTHONUTF8 = "1"` (CI cũng đặt biến này). |
| `git pull` báo "Your local changes would be overwritten" | Bạn đã sửa file. Giữ lại: chép file ra ngoài; bỏ thay đổi: `git checkout -- .` rồi `git pull`. |
| App mở rồi tắt ngay | Chạy `.\run.bat` trong PowerShell để đọc thông báo lỗi; gửi kèm khi báo lỗi (form issue "bug report"). |

## 7. Cây thư mục

```text
systemdocs/
├── run.bat / run-dev.bat      # Mở app Electron (dev: bật báo lỗi bằng ảnh)
├── README.md, AGENTS.md       # Giới thiệu; luật làm việc cho agent
├── shell/                     # App desktop Electron (giao diện chính)
│   ├── src/main/              #   tiến trình chính: khởi động sidecar, IPC
│   ├── src/preload/           #   cầu nối an toàn main ↔ giao diện
│   ├── src/renderer/          #   giao diện (notary/: soạn hồ sơ, sơ đồ thừa kế)
│   ├── sidecar/               #   máy chủ Python (FastAPI) app gọi tới
│   └── test/                  #   test JS (*.test.mjs) và Python (test_*.py)
├── notary_v2/                 # Lõi nghiệp vụ công chứng (Python)
│   ├── services/              #   xử lý hồ sơ, sơ đồ, nhập tài liệu
│   ├── routers/, schemas/     #   API và kiểu dữ liệu
│   ├── word_templates/        #   mẫu Word xuất văn bản
│   ├── tests/                 #   test engine
│   └── zalo_connector/        #   nhận dữ liệu từ Zalo
├── upload_lab/                # Trích Word → Excel kiểm tra → upload cổng
├── zalo/                      # Connector Zalo (gói riêng, có pyproject)
├── regex-test-tool/           # Công cụ thử regex trích xuất
├── contracts/                 # Hợp đồng dữ liệu giữa module (+ JSON schema)
├── docs/                      # STACK, mục lục, quyết định D-xxx, hướng dẫn này
├── _bmad-output/              # Spec, backlog, quyết định, artifact BMAD
│   └── specs/                 #   spec hành vi theo module
├── _bmad/                     # Cấu hình workflow BMAD
├── graphify-out/              # Bản đồ quan hệ code (sinh tự động)
├── testdata/                  # Dữ liệu giả lập cho e2e
├── tools/                     # Script: ci/ (known-failures, e2e), dev/ (setup test), báo lỗi
└── .github/                   # CI, mẫu issue/PR
```
