"""Quet 1 dot file Word: trich xuat + cham bang luat code (khong suy luan).

Cach dung:
    python tools/quet_kiem_tra.py "D:\\thu-muc" [--offset 0] [--limit 50] [--loc phan chia]
    python tools/quet_kiem_tra.py "D:\\thu-muc" --full

- Mac dinh chi lay .docx (nhanh). Them --ca-doc de gom ca .doc (cham).
- --loc: chi lay file ten chua cum nay (khong dau cung duoc).
- Ket qua: in bang ra man hinh + luu JSON cung thu muc chay.
- Ma loi xem tai kiem_tra_trich_xuat.py (R00..R12, bo qua R11 da xoa).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import extraction_adapter
from extraction_adapter import case_from_payload
from kiem_tra_trich_xuat import MUC_BO_QUA, MUC_LOI, kiem_tra_payload


def _ascii_fold(text: str) -> str:
    folded = unicodedata.normalize("NFD", str(text or "").lower())
    return "".join(c for c in folded if unicodedata.category(c) != "Mn").encode("ascii", "ignore").decode()


def tim_file(folder: str, *, loc: str = "", ca_doc: bool = False) -> list[str]:
    loc_fold = _ascii_fold(loc)
    found: list[str] = []
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.startswith("~"):
                continue
            low = name.lower()
            if low.endswith(".docx") or (ca_doc and low.endswith(".doc")):
                if loc_fold and loc_fold not in _ascii_fold(name):
                    continue
                found.append(os.path.join(root, name))
    found.sort()
    return found


def quet_file(path: str) -> dict:
    try:
        payload = extraction_adapter.extract(path)
    except Exception as exc:  # noqa: BLE001 - loi doc file ghi nhan, khong dung dot
        return {
            "file": path,
            "ten_file": os.path.basename(path),
            "kind": "ERROR",
            "phat_hien": [{"id": "RXX", "muc": MUC_LOI, "noi_dung": f"lỗi đọc: {exc}"[:150]}],
        }
    findings = kiem_tra_payload(payload)
    raw = payload.get("raw", {})
    return {
        "file": path,
        "ten_file": os.path.basename(path),
        "kind": case_from_payload(payload).get("loaivanbannhandien") or "",
        "so_nguoi": len(raw.get("ben_a", {}).get("nguoi", [])) + len(raw.get("ben_b", {}).get("nguoi", [])),
        "so_chet": len(raw.get("nguoi_chet", [])),
        "so_thua": len(raw.get("danh_sach_thua_dat", [])),
        "ts_chua_ho_tro": list(raw.get("tai_san_chua_ho_tro") or []),
        "phat_hien": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quét + kiểm tra trích xuất Word")
    parser.add_argument("folder", help="thư mục chứa file Word")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--loc", default="", help="chỉ lấy file tên chứa cụm này")
    parser.add_argument("--ca-doc", action="store_true", help="gồm cả .doc (chậm)")
    parser.add_argument("--full", action="store_true", help="quét hết, bỏ qua offset/limit")
    parser.add_argument("--ra", default="", help="file JSON ghi kết quả (mặc định quet_kiem_tra.json)")
    args = parser.parse_args()

    files = tim_file(args.folder, loc=args.loc, ca_doc=args.ca_doc)
    print(f"tong ung vien: {len(files)}", flush=True)
    batch = files if args.full else files[args.offset:args.offset + args.limit]
    print(f"chay {len(batch)} file", flush=True)

    results = []
    for num, path in enumerate(batch, start=1):
        item = quet_file(path)
        results.append(item)
        codes = ",".join(f["id"] for f in item["phat_hien"]) or "sach"
        print(f"... {num}/{len(batch)} {item['ten_file'][:50]} -> {item['kind']} [{codes}]", flush=True)

    out_path = args.ra or "quet_kiem_tra.json"

    dem_luat = Counter()
    file_theo_luat: dict[str, list[str]] = {}
    dem_loai = Counter()
    for r in results:
        dem_loai[r["kind"] or "?"] += 1
        for f in r["phat_hien"]:
            if f["muc"] == MUC_BO_QUA:
                continue
            dem_luat[f["id"]] += 1
            file_theo_luat.setdefault(f["id"], []).append(r["ten_file"])

    summary = {
        "theo_loai": dict(dem_loai.most_common()),
        "theo_luat": dict(dem_luat.most_common()),
        "file_theo_luat": {k: v for k, v in sorted(file_theo_luat.items())},
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"folder": args.folder, "summary": summary, "results": results}, fh, ensure_ascii=False)
    sach = sum(1 for r in results if not r["phat_hien"])
    bo_qua = sum(1 for r in results if any(f["muc"] == MUC_BO_QUA for f in r["phat_hien"]))
    loi = sum(1 for r in results if any(f["muc"] == MUC_LOI for f in r["phat_hien"]))
    top = ", ".join(f"{k}:{v}" for k, v in dem_luat.most_common(8)) or "không có"
    print(f"XONG: sach {sach}/{len(results)} | bo-qua {bo_qua} | co loi {loi} | JSON: {out_path}", flush=True)
    print(f"Luat hay gap: {top}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
