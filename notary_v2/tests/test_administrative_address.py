"""Real catalog observations and fictional dated history are separate tests."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unicodedata

import pytest

from notary_v2 import administrative_timeline as timeline
from notary_v2.services.administrative_address import (
    AddressLookup, AddressIndex, apply_address, lookup_address, normalize, parse_address,
)


E = [{"source_id": "synthetic", "row_key": "fictional"}]


def synthetic():
    ledger = timeline.empty_ledger()
    ledger["dataset_version"] = "fictional-unchanged-version"
    ledger["revision"] = 1
    ledger["sources"] = [{"id": "synthetic", "provider": "Synthetic test", "url": "urn:test:fictional",
        "protocol": "manual", "request_body": None, "retrieved_at": "2026-10-04", "sha256": None,
        "snapshot": None, "description": "Fictional fixture, never Vietnamese history"}]
    for uid in ("P", "A", "B", "C", "D"):
        ledger["units"].append({"id": uid, "level": "province" if uid == "P" else "commune", "source_key": None, "evidence": E})
    periods = {"P": ("2000-01-01", None), "A": ("2000-01-01", "2025-07-01"),
               "B": ("2025-07-01", "2026-01-01"), "C": ("2025-07-01", None), "D": ("2026-01-01", None)}
    for uid, (start, end) in periods.items():
        period = {"unit_id": uid, "valid_from": start, "valid_to": end, "status": "confirmed", "event_id": None, "evidence": E}
        ledger["names"].append({"id": "name:" + uid, "value": "Tỉnh Test" if uid == "P" else "Xã " + uid, **period})
        if uid != "P":
            ledger["parents"].append({"id": "parent:" + uid, "parent_id": "P", **period})
    def event(eid, before, after, day, kind):
        return {"id": eid, "type": kind, "from": [{"kind": "unit", "id": before}],
                "to": [{"kind": "unit", "id": u} for u in after], "effective_on": day,
                "valid_from": None, "valid_to": None, "status": "confirmed", "territory": "whole", "notes": "Fictional", "evidence": E}
    ledger["events"] = [event("ab", "A", ["B", "C"], "2025-07-01", "split"),
                        event("bd", "B", ["D"], "2026-01-01", "reported_transition")]
    return ledger


def payload(commune="A", target="2026-10-04"):
    return {"province": "Test", "commune": commune, "source_date": "2020-01-01", "target_date": target}


@pytest.mark.parametrize("address,day,commune,district", [
    ("Thôn 1, Xã A, Huyện H, Tỉnh P", "2025-06-30", "Xã A", "Huyện H"),
    ("Thôn 1 - A - H - P", "2025-06-30", "A", "H"),
    ("Thôn 1 Xã A Huyện H Tỉnh P", "2025-06-30", "Xã A", "Huyện H"),
    ("Thôn 1, Xã A, Tỉnh P", "2025-07-01", "Xã A", None),
])
def test_parser_date_format_and_hamlet(address, day, commune, district):
    parsed = parse_address(address, day)
    assert parsed["commune"] == commune
    assert parsed["district"] == district
    assert parsed["hamlet"].startswith("Thôn 1")


def test_exact_original_no_duplicate_suffix_and_unicode():
    original = "  Thôn 1, xã A  "
    applied = apply_address(original, "Xã B, Tỉnh P")
    assert applied.startswith(original)
    assert apply_address(applied, "Xã C, Tỉnh P").count("nay là") == 1
    # Ten dich chua dau ngoac cung khong duoc noi suffix lan hai.
    paren = apply_address(original, "Xã B (mới), Tỉnh P")
    assert apply_address(paren, "Xã C, Tỉnh P").count("nay là") == 1
    assert normalize(unicodedata.normalize("NFD", "PHƯỜNG YÊN DƯƠNG")) == normalize("yen duong")


@pytest.mark.parametrize("address,day,commune,district,province", [
    # Dau gach ngang trong ten tinh khong duoc tach doi don vi.
    ("Thôn 1, Xã A, Tỉnh Bà Rịa - Vũng Tàu", "2020-01-01", "Xã A", None, "Tỉnh Bà Rịa - Vũng Tàu"),
    ("Xã A - Tỉnh Bà Rịa - Vũng Tàu", "2020-01-01", "Xã A", None, "Tỉnh Bà Rịa - Vũng Tàu"),
    # Giay cap sau 01/07/2025 van co the ghi dia chi ba cap cu.
    ("Thôn 1, Xã A, Huyện H, Tỉnh P", "2026-01-01", "Xã A", "Huyện H", "Tỉnh P"),
    # Nguoi dung doi khi viet lon truoc nho sau.
    ("Tỉnh P, Huyện H, Xã A", "2020-01-01", "Xã A", "Huyện H", "Tỉnh P"),
])
def test_parser_hyphen_dated_three_level_and_reversed(address, day, commune, district, province):
    parsed = parse_address(address, day)
    assert parsed["commune"] == commune
    assert parsed["district"] == district
    assert parsed["province"] == province


def test_abolished_branch_marks_incomplete_not_silent():
    """Nhanh bi xoa bo (abolish, khong don vi ke thua) khong duoc bien
    mat — coverage phai bao thieu chung cu, khong khang dinh
    confirmed_history tren phan lanh tho da mat."""
    ledger = synthetic()
    for row in ledger["names"] + ledger["parents"]:
        if row["unit_id"] == "C":
            row["valid_to"] = "2026-01-01"
    ledger["events"].append({
        "id": "cx", "type": "abolish",
        "from": [{"kind": "unit", "id": "C"}], "to": [],
        "effective_on": "2026-01-01", "valid_from": None, "valid_to": None,
        "status": "confirmed", "territory": "whole",
        "notes": "Fictional abolish", "evidence": E})
    timeline.validate(ledger)
    answer = AddressIndex(ledger).lookup(payload())
    assert {c["unit_id"] for c in answer["candidates"]} == {"D"}
    assert answer["coverage"]["kind"] == "insufficient_confirmed_history"
    assert answer["coverage"]["historical"] is False


def test_non_district_qualifier_never_filters_candidate():
    """Qualifier Bando "(moi)"/"(phan con lai)" khong phai ten huyen —
    khong duoc loai ung vien khi nguoi dung co nhap district."""
    ledger = synthetic()
    ledger["units"].append({"id": "PQ", "level": "province", "source_key": None, "evidence": E})
    ledger["units"].append({"id": "Q", "level": "commune", "source_key": None, "evidence": E})
    for uid, value in (("PQ", "Tỉnh Q"), ("Q", "Xã Mới")):
        ledger["names"].append({"id": "name:" + uid, "unit_id": uid, "value": value,
            "valid_from": "2020-01-01", "valid_to": None, "status": "observed",
            "event_id": None, "evidence": E})
    ledger["parents"].append({"id": "parent:Q", "unit_id": "Q", "parent_id": "PQ",
        "valid_from": "2020-01-01", "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    # details.ten khac "Moi" de alias 'moi' chi den qua raw_phrase tien
    # than — neu khong, alias ten hien tai (qualifier None) da giu ung
    # vien va bug cu khong lo.
    for uid, phrase, ten in (("PQ", "tỉnh Q", "Tỉnh Q"), ("Q", "xã Mới (mới)", "Xã Đổi Tên")):
        ledger["observations"].append({"id": "obs:" + uid, "unit_id": uid,
            "kind": "reported_predecessor", "raw_phrase": phrase,
            "details": {"ten": ten}, "dataset_version": ledger["dataset_version"],
            "evidence": E})
    timeline.validate(ledger)
    p = {"province": "Q", "commune": "Mới", "district": "huyện Khác",
         "source_date": "2020-01-01", "target_date": "2026-10-04"}
    answer = AddressIndex(ledger).lookup(p)
    assert "Q" in {c["unit_id"] for c in answer["candidates"]}


def test_target_before_source_reports_invalid_input_coverage():
    answer = AddressIndex(synthetic()).lookup({**payload(), "target_date": "2019-01-01"})
    assert answer["status"] == "invalid_input"
    assert answer["coverage"]["kind"] == "invalid_input"
    assert answer["coverage"]["reason"] == "target_before_source"


def test_confirmed_split_boundary_chain_trace():
    ledger = synthetic()
    timeline.validate(ledger)
    index = AddressIndex(ledger)
    before = index.lookup(payload(target="2025-06-30"))
    at = index.lookup(payload(target="2025-07-01"))
    later = index.lookup(payload())
    assert [c["unit_id"] for c in before["candidates"]] == ["A"]
    assert {c["unit_id"] for c in at["candidates"]} == {"B", "C"}
    assert {c["unit_id"] for c in later["candidates"]} == {"C", "D"}
    assert next(c for c in later["candidates"] if c["unit_id"] == "D")["event_ids"] == ["ab", "bd"]
    assert later["coverage"]["historical"] is True


def test_partial_confirmed_branches_still_offered():
    """Mot nhanh split thieu bang chung khong duoc lam mat cac nhanh
    confirmed — chung van la dich hop le, chi khong du khang dinh
    'lich su day du' (coverage giu insufficient, historical=False)."""
    ledger = synthetic()
    # Nhanh B tach them mot don vi X chi co ten 'observed' (chua confirmed)
    # → nhanh do khong du chuoi; C, D van confirmed.
    ledger["units"].append({"id": "X", "level": "commune", "source_key": None, "evidence": E})
    ledger["names"].append({"id": "name:X", "unit_id": "X", "value": "Xã X",
        "valid_from": "2026-01-01", "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    ledger["parents"].append({"id": "parent:X", "unit_id": "X", "parent_id": "P",
        "valid_from": "2026-01-01", "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    ledger["events"].append({
        "id": "bx", "type": "reported_transition",
        "from": [{"kind": "unit", "id": "B"}],
        "to": [{"kind": "unit", "id": "X"}],
        "effective_on": "2026-01-01", "valid_from": None, "valid_to": None,
        "status": "confirmed", "territory": "partial",
        "notes": "Fictional partial", "evidence": E})
    timeline.validate(ledger)
    answer = AddressIndex(ledger).lookup(payload())
    assert {c["unit_id"] for c in answer["candidates"]} == {"C", "D"}
    assert all(c["historical"] for c in answer["candidates"])
    assert answer["coverage"]["kind"] == "insufficient_confirmed_history"
    assert answer["coverage"]["historical"] is False


@pytest.mark.parametrize("name,expected", [
    ("Gia Tân", {"Xã Gia Vân", "Phường Tây Hoa Lư"}),
    ("Hoàng Đông", {"Phường Duy Hà", "Phường Hà Nam"}),
    ("Hòa Mạc", {"Phường Duy Tân", "Phường Duy Tiên"}),
    ("Quang Trung", {"Phường Hà Nam", "Phường Phủ Lý", "Phường Nam Định", "Xã Hiển Khánh"}),
    ("Tiên Nội", {"Phường Tiên Sơn", "Phường Hà Nam"}),
    ("Tiên Ngoại", {"Phường Tiên Sơn", "Phường Hà Nam"}),
])
def test_real_six_splits_preserve_all_candidates_without_fake_dates(name, expected):
    answer = lookup_address({"province": "Ninh Bình", "commune": name, "source_date": "2020-01-01", "target_date": "2025-07-01"})
    assert {c["commune"] for c in answer["candidates"]} == expected
    assert answer["status"] == "ambiguous"
    assert answer["coverage"]["historical"] is False
    assert all(c["evidence"] and c["raw_phrase"] for c in answer["candidates"])


@pytest.mark.parametrize("address,expected", [
    ("Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định", "Xã Ý Yên"),
    ("Xã Yên Dương, huyện Ý Yên, tỉnh Nam Định", "Xã Vũ Dương"),
])
def test_owner_real_cases_current_candidates_only(address, expected):
    answer = lookup_address({"address": address, "source_date": "2020-01-01", "target_date": "2026-10-04"})
    assert expected in {c["commune"] for c in answer["candidates"]}
    assert not answer["coverage"]["historical"]


def test_cache_manual_history_same_dataset_version_and_failed_reload(tmp_path):
    ledger = synthetic()
    timeline.atomic_write(tmp_path, ledger)
    lookup = AddressLookup(tmp_path)
    assert lookup.lookup(payload())["revision"] == 1
    ledger["revision"] = 2
    next(n for n in ledger["names"] if n["unit_id"] == "D")["value"] = "Xã Edited"
    timeline.atomic_write(tmp_path, ledger)
    updated = lookup.lookup(payload())
    assert updated["revision"] == 2
    assert "Xã Edited" in {c["commune"] for c in updated["candidates"]}
    ledger["revision"] = 3
    ledger["names"].append(ledger["names"][0])
    (tmp_path / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    failed = lookup.lookup(payload())
    assert failed["coverage"]["kind"] == "reload_failed"
    assert failed["revision"] == 2
    assert failed["candidates"] == []


def test_missing_snapshot_refuses_old_results(tmp_path):
    shutil.copytree(timeline.DEFAULT_FOLDER, tmp_path, dirs_exist_ok=True)
    lookup = AddressLookup(tmp_path)
    p = {"province": "Ninh Bình", "commune": "Gia Tân", "source_date": "2020-01-01", "target_date": "2026-10-04"}
    assert lookup.lookup(p)["candidates"]
    next((tmp_path / "snapshots").glob("*.raw")).unlink()
    assert lookup.lookup(p)["coverage"]["kind"] == "reload_failed"


@pytest.mark.parametrize("changes", [{"source_date": "2020"}, {"target_date": "2025-02-30"}, {"source_date": None}, {"address": "junk", "province": "", "commune": ""}])
def test_invalid_input_never_guessed(changes):
    assert lookup_address({**payload(), **changes})["status"] == "invalid_input"


def test_schema_real_and_synthetic():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((timeline.ROOT / "contracts/notary-case-drafting/address-lookup.schema.json").read_text(encoding="utf-8"))
    for result in (lookup_address(payload("Gia Tân")), AddressIndex(synthetic()).lookup(payload())):
        jsonschema.Draft7Validator({**schema, "$ref": "#/definitions/result_data"}).validate(result)


def test_isolated_staged_source_without_checkout_fallback(tmp_path):
    engine = tmp_path / "engine"
    module = engine / "notary_v2"
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("Production staging uses Windows PowerShell")
    staged = subprocess.run([powershell, "-NoProfile", "-File", str(timeline.ROOT / "shell/sidecar/stage_administrative_reference.ps1"),
                             "-Repository", str(timeline.ROOT), "-EngineStage", str(engine)], capture_output=True, text=True)
    assert staged.returncode == 0, staged.stderr
    assert not list(engine.rglob("*.db"))
    assert not list(engine.rglob(".write.lock"))
    assert not list(engine.rglob("revisions"))
    code = "import sys,json; sys.path.insert(0,sys.argv[1]); from services.administrative_address import lookup_address; r=lookup_address(json.loads(sys.argv[2])); assert r['status']=='ambiguous',r; print(r['revision'])"
    completed = subprocess.run([sys.executable, "-I", "-c", code, str(module), json.dumps({"province": "Ninh Bình", "commune": "Gia Tân", "source_date": "2020-01-01", "target_date": "2026-10-04"})], cwd=tmp_path, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
