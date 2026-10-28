#!/usr/bin/env bash
# Sinh noi dung issue loi kem bang chung (KHONG tao issue).
# Dung: tools/file-bug.sh --title T --repro CMD [--expected E] [--actual A]
#        [--log FILE]... [--lines N] [--shot PNG] [--no-copy]
# Mac dinh: tu tim *.log moi nhat va anh .png moi nhat trong
#   $BUG_EVIDENCE_DIRS (mac dinh "/workspace/usability /workspace/e2e-run").
set -eu
TITLE="" REPRO="" EXPECTED="(điền)" ACTUAL="(điền)" LINES=60 SHOT="" COPY=1; LOGS=()
while [ $# -gt 0 ]; do case "$1" in
  --title) TITLE=$2; shift 2;; --repro) REPRO=$2; shift 2;;
  --expected) EXPECTED=$2; shift 2;; --actual) ACTUAL=$2; shift 2;;
  --log) LOGS+=("$2"); shift 2;; --lines) LINES=$2; shift 2;;
  --shot) SHOT=$2; shift 2;; --no-copy) COPY=0; shift;;
  -h|--help) sed -n '2,6p' "$0"; exit 0;;
  *) echo "Tham so la: $1" >&2; exit 2;; esac; done
[ -n "$TITLE" ] && [ -n "$REPRO" ] || { echo "Can --title va --repro" >&2; exit 2; }
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
BRANCH=$(git rev-parse --abbrev-ref HEAD); SHA=$(git rev-parse HEAD)
DIRTY=$(git status --porcelain | grep -qv '^??' && echo " (có thay đổi chưa commit)" || true)
DIRS=${BUG_EVIDENCE_DIRS:-/workspace/usability /workspace/e2e-run}
newest() { find $DIRS -type f -name "$1" -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n "${2:-1}" | cut -d' ' -f2-; }
[ ${#LOGS[@]} -eq 0 ] && mapfile -t LOGS < <(newest '*.log' 2)
[ -z "$SHOT" ] && SHOT=$(newest '*.png' 1)
SLUG=$(python3 -c "import sys,unicodedata,re;s=unicodedata.normalize(\"NFKD\",sys.argv[1].replace(\"đ\",\"d\").replace(\"Đ\",\"D\")).encode(\"ascii\",\"ignore\").decode().lower();print(re.sub(\"[^a-z0-9]+\",\"-\",s).strip(\"-\")[:40])" "$TITLE")
ID="$(date +%Y%m%d-%H%M)-${SLUG:-bug}"; EVD="docs/evidence/$ID"
REMOTE=$(git remote get-url origin 2>/dev/null | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
MEDIA="(không tìm thấy ảnh — đính kèm thủ công)"
if [ -n "$SHOT" ] && [ -f "$SHOT" ]; then
  if [ $COPY = 1 ]; then mkdir -p "$EVD"; cp "$SHOT" "$EVD/"; fi
  F=$(basename "$SHOT")
  MEDIA="![$F](https://github.com/$REMOTE/blob/evidence/$ID/$EVD/$F?raw=true)
Nguồn: \`$SHOT\` → \`$EVD/$F\` (commit lên nhánh \`evidence/$ID\` rồi push để link hoạt động)"
fi
LOGTXT=""
for f in "${LOGS[@]}"; do [ -f "$f" ] || continue
  LOGTXT+="==> $f (tail -n $LINES) <=="$'\n'"$(tail -n "$LINES" "$f")"$'\n'; done
[ -z "$LOGTXT" ] && LOGTXT="(không tìm thấy log — dán thủ công)"
ENV="- OS: $(uname -sr)
- Node: $(node -v 2>/dev/null || echo n/a)  Python: $(python3 -V 2>&1 | cut -d' ' -f2)
- Electron: $(node -p "require('./shell/package.json').devDependencies?.electron||'n/a'" 2>/dev/null || echo n/a)"
cat <<MD
<!-- Tiêu đề: [Lỗi] $TITLE | Mã bằng chứng: $ID -->
### Nhánh + commit SHA
$BRANCH @ $SHA$DIRTY

### Bước tái hiện
1. (điền)

### Kết quả mong đợi
$EXPECTED

### Kết quả thực tế
$ACTUAL

### Log / stack trace
\`\`\`shell
$LOGTXT\`\`\`

### Ảnh chụp / video
$MEDIA

### Lệnh test tái hiện hoặc tên test đang fail
\`\`\`shell
$REPRO
\`\`\`

### Môi trường
$ENV

- [x] Log, ảnh, video chỉ chứa dữ liệu giả lập, không có dữ liệu công dân thật.
MD
