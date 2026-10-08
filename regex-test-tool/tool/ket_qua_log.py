"""Ghi / doc file log ket qua test (1 dong JSON 1 file da test).

File log co dinh: <repo>/logs/ket-qua-test.jsonl (ghi noi them, khong xoa).
Nhan vien gui file nay cho chu de doi chieu loi.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent


def _noi_luu_log_mac_dinh() -> Path:
    """Log nam NGOAI folder tool de xoa folder cu khi doi ban khong mat.
    Cho co dinh, de tim: Documents\\KetQuaTestRegex\\ket-qua-test.jsonl.
    Ghi khong duoc thi rot ve logs/ trong folder tool.
    """
    try:
        documents = Path.home() / "Documents" / "KetQuaTestRegex"
        documents.mkdir(parents=True, exist_ok=True)
        probe = documents / ".ghi_duoc"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return documents / "ket-qua-test.jsonl"
    except OSError:
        local = REPO_ROOT / "logs" / "ket-qua-test.jsonl"
        local.parent.mkdir(parents=True, exist_ok=True)
        return local


LOG_PATH = _noi_luu_log_mac_dinh()


def mo_thu_muc_log(log_path: str | Path = LOG_PATH) -> Path:
    """Mo thu muc chua log bang Windows Explorer de nhan vien copy file."""
    folder = Path(log_path).parent
    folder.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(folder))  # type: ignore[attr-defined]
    except OSError:
        pass
    return folder

PERSON_CAN_THIEU = ("ho_ten", "ngay_sinh", "cccd", "ngay_cap_cccd", "dia_chi")
DECEASED_CAN_THIEU = ("ho_ten", "ngay_sinh", "ngay_chet", "dia_chi")
THUA_CAN_THIEU = ("so_thua_dat", "dien_tich")
STK_CAN_THIEU = ("so_hieu",)
BAO_HIEM_CAN_THIEU = ("so_hop_dong",)

TEN_TS_CHUA_HO_TRO = {"so_tiet_kiem": "sổ tiết kiệm", "bao_hiem": "bảo hiểm"}


def truong_trong(record: dict, fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if not str(record.get(field) or "").strip()]


def payload_thanh_ban_ghi(payload: dict, filepath: str | Path, engine_version: str) -> dict:
    raw = payload.get("raw", {}) if not payload.get("error") else {}
    web = payload.get("web_form", {})
    return {
        "app": "regex-test-tool",
        "engine_version": engine_version,
        "thoi_gian": datetime.now().isoformat(timespec="seconds"),
        "file": str(filepath),
        "ten_file": Path(str(filepath)).name,
        "kind": raw.get("document_kind", ""),
        "ten_hd": web.get("ten_hop_dong", ""),
        "tai_san": str(web.get("tai_san", "")),
        "nguoi": raw.get("ben_a", {}).get("nguoi", []) + raw.get("ben_b", {}).get("nguoi", []),
        "nguoi_chet": raw.get("nguoi_chet", []),
        "thua": raw.get("danh_sach_thua_dat", []),
        "tai_san_chua_ho_tro": raw.get("tai_san_chua_ho_tro", []),
        "thieu": raw.get("missing_web_form_fields", []),
        "loi": payload.get("error"),
    }


def ghi_ban_ghi(record: dict, log_path: str | Path = LOG_PATH) -> Path:
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def doc_ban_ghi(log_path: str | Path = LOG_PATH) -> list[dict]:
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    records: list[dict] = []
    with open(log_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


def tom_tat_ban_ghi(record: dict) -> str:
    if record.get("loi"):
        return f"LỖI: {record['loi']}"
    kiem_tra = [f for f in (record.get("kiem_tra") or []) if isinstance(f, dict)]
    if any(f.get("muc") == "bo-qua" for f in kiem_tra):
        return "BỎ QUA (không phải văn bản đích)"
    chua_ho_tro = record.get("tai_san_chua_ho_tro") or []
    parts = [
        f"Loại: {record.get('kind', '?')}",
        f"Người: {len(record.get('nguoi', []))}",
        f"Chết: {len(record.get('nguoi_chet', []))}",
        f"Thửa: {len(record.get('thua', []))}",
    ]
    if chua_ho_tro:
        parts.append("Chưa hỗ trợ: " + ", ".join(TEN_TS_CHUA_HO_TRO.get(k, k) for k in chua_ho_tro))
    flags = [f for f in kiem_tra if f.get("muc") in ("loi", "canh-bao")]
    if flags:
        parts.append("CỜ: " + ", ".join(f"{f.get('id')}" for f in flags))
        return " | ".join(parts)
    thieu_nguoi = sum(1 for p in record.get("nguoi", []) if truong_trong(p, PERSON_CAN_THIEU))
    thieu_chet = sum(1 for p in record.get("nguoi_chet", []) if truong_trong(p, DECEASED_CAN_THIEU))
    thieu_thua = sum(1 for t in record.get("thua", []) if truong_trong(t, THUA_CAN_THIEU))
    if thieu_nguoi or thieu_chet or thieu_thua:
        parts.append(f"THIẾU TRƯỜNG (người:{thieu_nguoi} chết:{thieu_chet} thửa:{thieu_thua})")
    return " | ".join(parts)


def hang_thieu_truong(record: dict, fields: tuple[str, ...]) -> bool:
    return bool(truong_trong(record, fields))
