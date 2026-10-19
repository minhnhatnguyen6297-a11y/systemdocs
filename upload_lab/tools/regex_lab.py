from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
for _path in (ROOT, ROOT.parent / "tools"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import extraction_adapter
from extraction_adapter import case_from_payload
import kiem_tra_trich_xuat
from regex_workbench.engine import contract_extract


DEFAULT_INPUT = ROOT / "regex_review_samples" / "input"
DEFAULT_CACHE = ROOT / "regex_review_samples" / "cache"
DEFAULT_GOLDEN = ROOT / "regex_review_samples" / "golden"
DEFAULT_PACKETS = ROOT / "regex_review_samples" / "packets"
EXTRACTION_FIELDS = (
    "document_kind",
    "ten_hop_dong",
    "nguoi_yeu_cau",
    "duong_su",
    "tai_san",
    "nguoi",
    "nguoi_chet",
    "thua_dat",
    "tai_san_chua_ho_tro",
    "missing_fields",
    "error",
)


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value or ""))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", value).strip().upper().replace("Đ", "D")


def _line_label(line: str) -> str:
    folded = _fold(line)
    if re.search(r"CONG HOA XA HOI CHU NGHIA VIET NAM|DOC LAP\s*[-–]", folded):
        return "TIEU_NGU"
    if re.fullmatch(r"[-=*_.~•\s]{3,}", line.strip()) or re.fullmatch(r"[-=*_.~\s]{3,}", folded):
        return "HOA_VAN"
    if re.search(r"\b(?:MA|M[ÃA])\s*(?:BIEU MAU|BM)\b|\bBM[.\s_-]*\d", folded):
        return "MA_BIEU_MAU"
    if re.search(r"VAN PHONG CONG CHUNG|PHONG CONG CHUNG", folded):
        return "VP_HEADER"
    if re.search(r"\bLOI CHUNG\b", folded):
        return "LOI_CHUNG"
    if re.search(r"\bSO\s*(?:CONG CHUNG|CC)\s*[:.]", folded):
        return "SO_CC"
    if re.match(r"^KINH GUI\b", folded):
        return "KINH_GUI"
    if re.match(r"^(?:HOM NAY|HOM,? NGAY)\b", folded):
        return "HOM_NAY"
    if re.match(r"^(?:CHUNG NHAN|CONG CHUNG VIEN CHUNG NHAN)\b", folded):
        return "CHUNG_NHAN"
    if re.search(r"CHUNG TOI GOM|CAC BEN GOM|TOI LA\s*:", folded):
        return "INTRO"
    if re.search(r"\bBEN\s+[AB]\b|NGUOI (?:TU CHOI|HUONG DI SAN)|CAC BEN THAM GIA", folded):
        return "PARTY_HDR"
    if re.match(r"^(?:ONG|BA|ANH|CHI|HO VA TEN|HO TEN)\s*[:.]", folded):
        return "PERSON"
    if re.match(r"^(?:DIEU|CHUONG)\s+(?:[IVXLCDM]+|\d+)", folded):
        return "DIEU"
    return "TEXT"


def layout_signature(text: str) -> str:
    labels = [_line_label(line) for line in str(text or "").splitlines() if line.strip()][:10]
    collapsed: list[str] = []
    for label in labels:
        if not collapsed or collapsed[-1] != label:
            collapsed.append(label)
    return ">".join(collapsed) or "EMPTY"


def cluster_id_for(signature: str) -> str:
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]


def _extractor_fingerprint() -> str:
    """Bam lõi luật + adapter + luật kiểm tra + file nay: doi 1 trong 4 ->
    cache het han, ingest phai chay lai (khong duoc cham tren ket qua luu cu).
    Luật nằm ở lõi (`contract_extract`), nên phải băm cả lõi — nếu chỉ băm
    adapter thì sửa luật sẽ không làm cache hết hạn."""
    digest = hashlib.sha256()
    digest.update(Path(contract_extract.__file__).read_bytes())
    digest.update(Path(extraction_adapter.__file__).read_bytes())
    digest.update(Path(kiem_tra_trich_xuat.__file__).read_bytes())
    digest.update(Path(__file__).read_bytes())
    return digest.hexdigest()


def _json_read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


_NGUOI_FIELDS = ("ho_ten", "ten_goi_khac", "gioi_tinh", "ngay_sinh", "chi_co_nam_sinh", "cccd", "noi_cap", "ngay_cap_cccd", "dia_chi")
_CHET_FIELDS = ("ho_ten", "ten_goi_khac", "gioi_tinh", "ngay_sinh", "chi_co_nam_sinh", "ngay_chet", "loai_giay_to", "so_giay_to", "ngay_cap", "noi_cap", "dia_chi")
_THUA_FIELDS = ("so_thua_dat", "so_to_ban_do", "dien_tich", "chi_tiet_dien_tich", "land_rows", "nguon_goc",
                "muc_dich_su_dung", "thoi_han_su_dung", "phan_ghi_them",
                "dia_chi", "loai_gcn", "so_gcn", "so_gcn_raw", "so_vao_so", "ngay_cap_gcn", "co_quan_cap")


def _cell(value: Any) -> Any:
    """Scalar -> str; list/dict (chi tiet dien tich, land_rows...) giu nguyen de so sau."""
    return value if isinstance(value, (list, dict, bool, int, float)) else str(value or "")


def _rows(records: Any, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    """Giu tap truong con cua moi ban ghi — du de so tung truong, khong chi ten."""
    return [
        {k: _cell(r.get(k)) for k in fields}
        for r in records or []
        if isinstance(r, dict)
    ]


def _snapshot(payload: dict[str, Any] | None, error: str = "") -> dict[str, Any]:
    payload = payload or {}
    web = payload.get("web_form") or {}
    raw = payload.get("raw") or {}
    case = case_from_payload(payload) if payload else {}
    return {
        "document_kind": str(case.get("loaivanbannhandien") or ""),
        "ten_hop_dong": str(case.get("tenvanban") or ""),
        "nguoi_yeu_cau": str(web.get("nguoi_yeu_cau") or ""),
        "duong_su": str(web.get("duong_su") or ""),
        "tai_san": str(web.get("tai_san") or ""),
        "nguoi": _rows(raw.get("ben_a", {}).get("nguoi"), _NGUOI_FIELDS)
                 + _rows(raw.get("ben_b", {}).get("nguoi"), _NGUOI_FIELDS),
        "nguoi_chet": _rows(raw.get("nguoi_chet"), _CHET_FIELDS),
        "thua_dat": _rows(raw.get("danh_sach_thua_dat"), _THUA_FIELDS),
        "tai_san_chua_ho_tro": list(raw.get("tai_san_chua_ho_tro") or []),
        "missing_fields": list(raw.get("missing_web_form_fields") or []),
        "error": error or str(payload.get("error") or ""),
    }


KIND_TITLE_TERMS = {
    "transfer_contract": ("CHUYEN NHUONG",),
    "gift_contract": ("TANG CHO",),
    "mortgage_contract": ("THE CHAP",),
    "asset_commitment": ("CAM KET", "TAI SAN RIENG"),
    "inheritance_partition": ("PHAN CHIA DI SAN",),
    "inheritance_refusal": ("TU CHOI", "DI SAN"),
    "transfer_cancellation": ("HUY BO", "CHUYEN NHUONG"),
}


def suspicion_flags(extraction: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    title = str(extraction.get("ten_hop_dong") or "")
    kind = str(extraction.get("document_kind") or "")
    asset = str(extraction.get("tai_san") or "")
    if not title.strip():
        flags.append("TITLE_EMPTY")
    expected = KIND_TITLE_TERMS.get(kind)
    folded_title = _fold(title)
    if expected and not all(term in folded_title for term in expected):
        flags.append("KIND_KHONG_KHOP_TITLE")
    if len(asset) > 2500:
        flags.append("TAI_SAN_QUA_DAI")
    folded_asset = _fold(asset)
    if re.search(r"\b(?:LOI CHUNG|SO CONG CHUNG)\b|\bDIEU\s+(?:[2-9]|[1-9]\d+)\b", folded_asset):
        flags.append("TAI_SAN_AN_LAN")
    if extraction.get("missing_fields") or any(
        not str(extraction.get(field) or "").strip()
        for field in ("ten_hop_dong", "nguoi_yeu_cau", "duong_su", "tai_san")
    ):
        flags.append("FIELD_RONG")
    if extraction.get("error"):
        flags.append("EXTRACT_ERROR")
    return flags


def _scan_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        (
            path
            for path in input_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".doc", ".docx"}
            and not path.name.startswith("~$")
        ),
        key=lambda path: path.relative_to(input_dir).as_posix().casefold(),
    )


def ingest_corpus(input_dir: Path | str = DEFAULT_INPUT, cache_dir: Path | str = DEFAULT_CACHE) -> dict[str, Any]:
    input_dir, cache_dir = Path(input_dir), Path(cache_dir)
    records_dir = cache_dir / "records"
    fingerprint = _extractor_fingerprint()
    records: dict[str, dict[str, Any]] = {}
    paths: dict[str, str] = {}
    reused_count = 0
    extracted_count = 0

    for path in _scan_files(input_dir):
        relative = path.relative_to(input_dir).as_posix()
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        cache_path = records_dir / f"{content_hash}.json"
        cached = _json_read(cache_path, {})
        if cached.get("content_hash") == content_hash and cached.get("extractor_fingerprint") == fingerprint:
            record = dict(cached)
            record["relative_path"] = relative
            reused_count += 1
        else:
            error = ""
            text = ""
            payload = None
            try:
                text = extraction_adapter.read_docx(
                    path, use_ifilter_for_doc=path.suffix.lower() == ".doc"
                )
                payload = extraction_adapter.extract(path, preloaded_text=text)
            except Exception as exc:  # A broken sample must remain reviewable.
                error = f"{type(exc).__name__}: {exc}"
            extraction = _snapshot(payload, error)
            kind_label = str(extraction.get("document_kind") or "unknown").upper()
            signature = f"{layout_signature(text)}>KIND_{kind_label}"
            kiem_tra: list | None = None  # None = chua/khong kiem duoc; [] = da kiem, sach
            if payload and not error:
                try:
                    kiem_tra = kiem_tra_trich_xuat.kiem_tra_payload(payload)
                except Exception:  # noqa: BLE001 - luat kiem khong duoc lam chet ingest
                    kiem_tra = None
            record = {
                "content_hash": content_hash,
                "extractor_fingerprint": fingerprint,
                "relative_path": relative,
                "layout_signature": signature,
                "cluster_id": cluster_id_for(signature),
                "extraction": extraction,
                "flags": suspicion_flags(extraction),
                "kiem_tra": kiem_tra,
                "source_lines": str(text or "").splitlines(),
            }
            _json_write(cache_path, record)
            extracted_count += 1
        # A hash can be referenced by several paths; keep the first path in the record.
        records.setdefault(content_hash, record)
        paths[relative] = content_hash

    clusters: dict[str, dict[str, Any]] = {}
    for relative, content_hash in paths.items():
        record = records[content_hash]
        cluster = clusters.setdefault(
            record["cluster_id"],
            {"signature": record["layout_signature"], "hashes": [], "paths": []},
        )
        if content_hash not in cluster["hashes"]:
            cluster["hashes"].append(content_hash)
        cluster["paths"].append(relative)

    flag_counts = Counter(flag for record in records.values() for flag in record.get("flags", []))
    index = {
        "version": 1,
        "extractor_fingerprint": fingerprint,
        "paths": paths,
        "records": records,
        "clusters": clusters,
        "summary": {
            "file_count": len(paths),
            "record_count": len(records),
            "cluster_count": len(clusters),
            "reused_count": reused_count,
            "extracted_count": extracted_count,
            "flag_counts": dict(sorted(flag_counts.items())),
        },
    }
    _json_write(cache_dir / "index.json", index)
    return index


def _golden_records(golden_dir: Path) -> dict[str, Any]:
    return _json_read(golden_dir / "index.json", {}).get("records", {})


def _changed(record: dict[str, Any], golden: dict[str, Any]) -> bool:
    return record.get("extraction", {}) != golden.get("extraction", {})


def _short(value: Any, limit: int = 700) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value or "")
    if len(text) <= limit:
        return text
    side = (limit - 25) // 2
    return f"{text[:side]}\n... [rut gon] ...\n{text[-side:]}"


def _excerpt(lines: list[str], limit: int = 45) -> str:
    populated = [(number, line) for number, line in enumerate(lines, 1) if line.strip()]
    shown = populated[:limit]
    body = "\n".join(f"{number:04d}: {line}" for number, line in shown)
    if len(populated) > limit:
        body += f"\n... ({len(populated) - limit} dong co noi dung khac)"
    return body


_ANSWER_FIELDS = (
    "document_kind",
    "ten_hop_dong",
    "nguoi",
    "nguoi_chet",
    "thua_dat",
    "tai_san_chua_ho_tro",
)


def _pick_priority(record: dict[str, Any]) -> int:
    """File gay finding phai nam trong goi review: loi kiem tra -> 0,
    co finding -> 1, co flags -> 2, sach -> 3."""
    kiem_tra = record.get("kiem_tra")
    if kiem_tra is None:
        return 0
    if any(
        isinstance(f, dict) and f.get("muc") in (kiem_tra_trich_xuat.MUC_LOI, kiem_tra_trich_xuat.MUC_CANH_BAO)
        for f in kiem_tra
    ):
        return 1
    if record.get("flags"):
        return 2
    return 3


def _expected_template() -> dict[str, Any]:
    # null = chua tra loi. [] = DA xac nhan khong co. compare phai phan biet 2 thu nay.
    return {field: None for field in _ANSWER_FIELDS}


def review_corpus(
    input_dir: Path | str = DEFAULT_INPUT,
    cache_dir: Path | str = DEFAULT_CACHE,
    golden_dir: Path | str = DEFAULT_GOLDEN,
    packets_dir: Path | str = DEFAULT_PACKETS,
    *,
    blind: bool = False,
) -> dict[str, Any]:
    index = ingest_corpus(input_dir, cache_dir)
    golden = _golden_records(Path(golden_dir))
    golden_signatures = {item.get("layout_signature") for item in golden.values()}
    selected: list[tuple[str, list[str]]] = []
    for cluster_id, cluster in index["clusters"].items():
        hashes = cluster["hashes"]
        reasons: list[str] = []
        if cluster["signature"] not in golden_signatures:
            reasons.append("NEW_CLUSTER")
        if len(cluster["paths"]) == 1:
            reasons.append("OUTLIER_SIZE_1")
        if any(index["records"][item].get("flags") for item in hashes):
            reasons.append("HAS_FLAGS")
        if any(index["records"][item].get("kiem_tra") is None for item in hashes):
            reasons.append("KIEM_TRA_ERROR")
        if any(
            isinstance(f, dict) and f.get("muc") in (kiem_tra_trich_xuat.MUC_LOI, kiem_tra_trich_xuat.MUC_CANH_BAO)
            for item in hashes
            for f in (index["records"][item].get("kiem_tra") or [])
        ):
            reasons.append("HAS_R_FLAGS")
        if any(item in golden and _changed(index["records"][item], golden[item]) for item in hashes):
            reasons.append("CHANGED_VS_GOLDEN")
        if reasons:
            selected.append((cluster_id, reasons))

    run_dir = Path(packets_dir) / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    index_lines = ["# Regex review packets", "", f"Selected clusters: {len(selected)}", ""]
    packet_paths: list[str] = []
    for cluster_id, reasons in selected:
        cluster = index["clusters"][cluster_id]
        hashes = sorted(
            cluster["hashes"],
            key=lambda item: (
                _pick_priority(index["records"][item]),
                index["records"][item]["relative_path"],
            ),
        )[:3]
        packet_name = f"cluster-{cluster_id}.md"
        packet_paths.append(packet_name)
        index_lines.append(f"- [{cluster_id}]({packet_name}): {', '.join(reasons)}")
        signature = cluster["signature"]
        if blind:
            # Khong lo du lieu may doan: KIND_* trong signature.
            signature = re.sub(r">KIND_[A-Z_]+$", "", signature)
        lines = [
            f"# Cluster {cluster_id}", "", f"Reasons: {', '.join(reasons)}", "",
            f"Signature: `{signature}`", "", f"Files: {len(cluster['paths'])}; unique hashes: {len(cluster['hashes'])}", "",
        ]
        for content_hash in hashes:
            record = index["records"][content_hash]
            if blind:
                (run_dir / f"{content_hash}.source.txt").write_text(
                    "\n".join(record.get("source_lines") or []), encoding="utf-8"
                )
                answer = _expected_template()
                answer["relative_path"] = record["relative_path"]
                # Bang enum de agent tra loi document_kind (khong phai dap an may).
                answer["_document_kind_options"] = sorted(KIND_TITLE_TERMS) + ["inheritance_declaration", "generic", "unknown"]
                _json_write(run_dir / f"{content_hash}.expected.json", answer)
                lines.extend([
                    f"## {record['relative_path']}", "",
                    f"Hash: `{content_hash}`", "",
                    f"BLIND: doc `{content_hash}.source.txt` roi dien `{content_hash}.expected.json`. Ket qua may khong hien o day — chay `compare --answers` sau khi dien xong.", "",
                ])
                continue
            lines.extend([f"## {record['relative_path']}", "", f"Hash: `{content_hash}`", "", f"Flags: {', '.join(record.get('flags') or ['NONE'])}", "", "### Extraction", ""])
            for field in EXTRACTION_FIELDS:
                lines.extend([f"- `{field}`: {_short(record['extraction'].get(field))}", ""])
            kiem_tra_raw = record.get("kiem_tra")
            if kiem_tra_raw is None:
                lines.extend(["### Kiem tra (R)", "", "- (khong kiem duoc — validator loi, xem KIEM_TRA_ERROR)", ""])
            else:
                kiem_tra = [f"{f.get('id')}({f.get('muc')}): {f.get('noi_dung')}" for f in kiem_tra_raw if isinstance(f, dict)]
                if kiem_tra:
                    lines.extend(["### Kiem tra (R)", ""] + [f"- {item}" for item in kiem_tra] + [""])
            lines.extend(["### Source excerpt", "", "```text", _excerpt(record.get("source_lines", [])), "```", ""])
        (run_dir / packet_name).write_text("\n".join(lines), encoding="utf-8")
    (run_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")
    return {"packet_dir": str(run_dir), "selected_cluster_count": len(selected), "packets": packet_paths, "index": index}


def _scalar_eq(want: Any, got: Any) -> bool:
    """Keep spelling, identifiers and booleans exact; no lossy numeric coercion."""
    if isinstance(want, bool) or isinstance(got, bool):
        return type(want) is type(got) and want == got
    if isinstance(want, str) and isinstance(got, str):
        return unicodedata.normalize("NFC", want) == unicodedata.normalize("NFC", got)
    if isinstance(want, (int, float)) and isinstance(got, (int, float)):
        return want == got
    return type(want) is type(got) and want == got


def _answer_scope(value: Any, field: str = "") -> tuple[int, int]:
    row_fields = {'nguoi': _NGUOI_FIELDS, 'nguoi_chet': _CHET_FIELDS, 'thua_dat': _THUA_FIELDS}
    if field in row_fields and isinstance(value, list):
        value = [{**dict.fromkeys(row_fields[field]), **row} if isinstance(row, dict) else row for row in value]
    if value is None:
        return 0, 1
    if isinstance(value, (dict, list)):
        children = list(value.values()) if isinstance(value, dict) else value
        if not children:
            return (0, 1) if isinstance(value, dict) else (1, 0)
        scopes = [_answer_scope(child) for child in children]
        return sum(s[0] for s in scopes), sum(s[1] for s in scopes)
    return 1, 0


def _match(want: Any, got: Any, field: str = "") -> bool:
    """Answered fields match exactly; record lists one-to-one, nested rows in source order.
    Only area fields accept numeric equivalence; null means unanswered."""
    if want is None:
        return True
    if isinstance(want, dict):
        return isinstance(got, dict) and all(
            _match(v, got.get(k), k) for k, v in want.items() if _answer_scope(v)[0]
        )
    if isinstance(want, list):
        if not isinstance(got, list) or len(want) != len(got):
            return False
        if field not in ("nguoi", "nguoi_chet", "thua_dat"):
            return all(_match(w, g, field) for w, g in zip(want, got))
        # Each actual row may satisfy exactly one answer (including duplicate IDs).
        assigned: dict[int, int] = {}
        def assign(i: int, seen: set[int]) -> bool:
            for j, actual in enumerate(got):
                if j in seen or not _match(want[i], actual, field):
                    continue
                seen.add(j)
                if j not in assigned or assign(assigned[j], seen):
                    assigned[j] = i
                    return True
            return False
        return all(assign(i, set()) for i in range(len(want)))
    if field in ("dien_tich", "dien_tich_m2") and not isinstance(want, bool) and not isinstance(got, bool):
        from decimal import Decimal, InvalidOperation
        try:
            return Decimal(str(want).replace(",", ".")) == Decimal(str(got).replace(",", "."))
        except InvalidOperation:
            pass
    return _scalar_eq(want, got)


def _diff_list(field: str, want: list, got: list, label: str) -> list[dict[str, Any]]:
    """So tung phan tu: dict -> so tung khoa khai bao; chuoi -> so khoa dinh danh."""
    diffs: list[dict[str, Any]] = []
    if all(not isinstance(row, dict) or _answer_scope(row)[0] for row in want) and _match(want, got, field):
        return diffs
    id_key = "ho_ten" if field.startswith("nguoi") else "so_thua_dat"
    if len(want) != len(got):
        diffs.append({"file": label, "field": f"{field}.len", "expected": len(want), "actual": len(got)})
    unused = set(range(len(got)))
    for i, w in enumerate(want):
        candidates = sorted(unused)
        if isinstance(w, dict):
            identity = w.get(id_key)
            identified = [j for j in candidates if isinstance(got[j], dict) and identity is not None and _scalar_eq(identity, got[j].get(id_key))]
            matching = [j for j in candidates if _match(w, got[j])]
            candidates = matching or identified or candidates
        j = candidates[0] if candidates else None
        g = got[j] if j is not None else None
        if j is not None:
            unused.remove(j)
        if isinstance(w, dict):
            if _answer_scope(w)[0] == 0:
                diffs.append({"file": label, "field": f"{field}[{i}]",
                              "expected": "it nhat 1 truong co gia tri",
                              "actual": "ban ghi dap an rong — chi kiem duoc so luong"})
                continue
            for k, v in w.items():
                if not _answer_scope(v)[0]:
                    continue  # null trong item = khong tra loi truong nay
                gv = g.get(k) if isinstance(g, dict) else None
                if not _match(v, gv, k):
                    diffs.append({"file": label, "field": f"{field}[{i}].{k}", "expected": v, "actual": gv})
        else:
            gv = g.get(id_key) if isinstance(g, dict) else g
            if not _scalar_eq(w, gv):
                diffs.append({"file": label, "field": f"{field}[{i}]", "expected": w, "actual": gv})
    return diffs


def compare_answers(
    answers_dir: Path | str,
    cache_dir: Path | str = DEFAULT_CACHE,
) -> dict[str, Any]:
    """So dap an agent viet (expected.json trong packet blind) voi extraction.

    - null / field khong co = CHUA tra loi -> bo qua (nhung file toan null = loi).
    - [] = DA xac nhan khong co -> dem so luong, boc thua bi bat.
    - JSON hong / thu muc rong / cache cu -> loi, khong tra "dat".
    """
    answers_dir = Path(answers_dir)
    index = _json_read(Path(cache_dir) / "index.json", {})
    records = index.get("records", {})
    diffs: list[dict[str, Any]] = []
    files_checked = 0
    scopes = []
    answer_paths = sorted(answers_dir.glob("*.expected.json")) if answers_dir.is_dir() else []
    if not answer_paths:
        diffs.append({"file": "*", "field": "*", "expected": "dap an", "actual": "khong tim thay *.expected.json"})
    if index.get("extractor_fingerprint") != _extractor_fingerprint():
        diffs.append({"file": "*", "field": "cache", "expected": _extractor_fingerprint()[:12], "actual": "cache cu/khong co — chay lai ingest"})
    for answer_path in answer_paths:
        content_hash = answer_path.name[: -len(".expected.json")]
        try:
            expected = json.loads(answer_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            diffs.append({"file": answer_path.name, "field": "*", "expected": "json hop le", "actual": str(exc)})
            continue
        if not isinstance(expected, dict):
            diffs.append({"file": answer_path.name, "field": "*", "expected": "object json", "actual": type(expected).__name__})
            continue
        for key in sorted(set(expected) - set(_ANSWER_FIELDS) - {'relative_path', '_document_kind_options'}):
            diffs.append({"file": answer_path.name, "field": key,
                          "expected": "supported answer field", "actual": "unknown answer key"})
        record = records.get(content_hash)
        if record is None:
            diffs.append({"file": answer_path.name, "field": "*", "expected": "hash trong cache", "actual": "khong co — chay ingest truoc"})
            continue
        files_checked += 1
        actual = record.get("extraction", {})
        if actual.get("error"):
            diffs.append({"file": answer_path.name, "field": "error", "expected": "successful extraction", "actual": actual["error"]})
        answered = 0
        unanswered = 0
        for field in _ANSWER_FIELDS:
            checked, unchecked = _answer_scope(expected.get(field), field)
            answered += checked
            unanswered += unchecked
            if not checked:
                if isinstance(expected.get(field), list) and expected[field]:
                    diffs.append({"file": answer_path.name, "field": field, "expected": "it nhat 1 truong co gia tri", "actual": "ban ghi dap an rong — chi kiem duoc so luong"})
                continue
            want, got = expected[field], actual.get(field)
            if isinstance(want, list) and isinstance(got, list):
                diffs.extend(_diff_list(field, want, got, record.get("relative_path", content_hash)))
            elif not _match(want, got):
                diffs.append({
                    "file": record.get("relative_path", answer_path.name),
                    "field": field,
                    "expected": want,
                    "actual": got,
                })
        if answered == 0:
            diffs.append({"file": answer_path.name, "field": "*", "expected": "dap an co noi dung", "actual": "tat ca null"})
        scopes.append({"file": record.get("relative_path", answer_path.name), "checked_fields": answered,
                       "unanswered_fields": unanswered, "result_scope": "checked_fields_only" if answered else "unanswered"})
    report = {
        "files_checked": files_checked,
        "diff_count": len(diffs),
        "diffs": diffs,
        "scope": scopes,
        "checked_fields": sum(s["checked_fields"] for s in scopes),
        "unanswered_fields": sum(s["unanswered_fields"] for s in scopes),
        "exit_code": 1 if diffs else 0,
    }
    report_path = answers_dir / "compare-report.json"
    _json_write(report_path, report)
    report["report_path"] = str(report_path)
    return report


def approve_corpus(
    input_dir: Path | str = DEFAULT_INPUT,
    cache_dir: Path | str = DEFAULT_CACHE,
    golden_dir: Path | str = DEFAULT_GOLDEN,
    *,
    approve_all: bool = False,
    cluster_id: str | None = None,
) -> dict[str, Any]:
    if approve_all == bool(cluster_id):
        raise ValueError("Require exactly one of approve_all or cluster_id")
    index = ingest_corpus(input_dir, cache_dir)
    if cluster_id and cluster_id not in index["clusters"]:
        raise ValueError(f"Unknown cluster: {cluster_id}")
    hashes = list(index["records"]) if approve_all else index["clusters"][cluster_id]["hashes"]
    golden_path = Path(golden_dir) / "index.json"
    payload = _json_read(golden_path, {"version": 1, "records": {}})
    records = payload.setdefault("records", {})
    for content_hash in hashes:
        current = index["records"][content_hash]
        records[content_hash] = {
            "relative_path": current["relative_path"],
            "layout_signature": current["layout_signature"],
            "cluster_id": current["cluster_id"],
            "extraction": current["extraction"],
        }
    payload["approved_at"] = datetime.now().isoformat(timespec="seconds")
    _json_write(golden_path, payload)
    return {"approved_count": len(hashes), "golden_path": str(golden_path)}


def verify_corpus(
    input_dir: Path | str = DEFAULT_INPUT,
    cache_dir: Path | str = DEFAULT_CACHE,
    golden_dir: Path | str = DEFAULT_GOLDEN,
) -> dict[str, Any]:
    index = ingest_corpus(input_dir, cache_dir)
    golden = _golden_records(Path(golden_dir))
    results: list[dict[str, Any]] = []
    counts = Counter()
    for content_hash, record in index["records"].items():
        if content_hash not in golden:
            status = "NEW"
        elif _changed(record, golden[content_hash]):
            status = "CHANGED"
        else:
            status = "UNCHANGED"
        counts[status] += 1
        results.append({"content_hash": content_hash, "relative_path": record["relative_path"], "status": status})
    for content_hash, record in golden.items():
        if content_hash in index["records"]:
            continue
        counts["REMOVED"] += 1
        results.append(
            {
                "content_hash": content_hash,
                "relative_path": record.get("relative_path", ""),
                "status": "REMOVED",
            }
        )
    report = {
        "summary": {name: counts[name] for name in ("NEW", "UNCHANGED", "CHANGED", "REMOVED")},
        "results": results,
        "exit_code": 1 if counts["CHANGED"] or counts["REMOVED"] else 0,
    }
    report_path = Path(cache_dir) / "verify-report.json"
    report["report_path"] = str(report_path)
    _json_write(report_path, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent-driven regex extraction review lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "review", "verify", "approve", "compare"):
        command = subparsers.add_parser(name)
        command.add_argument("--input", type=Path, default=DEFAULT_INPUT)
        command.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
        if name in {"review", "verify", "approve"}:
            command.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
        if name == "review":
            command.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
            command.add_argument("--blind", action="store_true",
                                 help="chi xuat source.txt + expected.json (khong lo dap an may)")
        if name == "compare":
            command.add_argument("--answers", type=Path, required=True,
                                 help="thu muc chua *.expected.json (thuong la packet dir cua review --blind)")
        if name == "approve":
            group = command.add_mutually_exclusive_group(required=True)
            group.add_argument("--all", action="store_true", dest="approve_all")
            group.add_argument("--cluster")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    args = _parser().parse_args(argv)
    if args.command == "ingest":
        result = ingest_corpus(args.input, args.cache)
        output = result["summary"]
    elif args.command == "review":
        result = review_corpus(args.input, args.cache, args.golden, args.packets, blind=args.blind)
        output = {key: value for key, value in result.items() if key != "index"}
    elif args.command == "compare":
        output = compare_answers(args.answers, args.cache)
    elif args.command == "approve":
        output = approve_corpus(args.input, args.cache, args.golden, approve_all=args.approve_all, cluster_id=args.cluster)
    else:
        output = verify_corpus(args.input, args.cache, args.golden)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return int(output.get("exit_code", 0))


if __name__ == "__main__":
    sys.exit(main())
