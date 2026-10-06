# -*- coding: utf-8 -*-
"""v2 administrative lookup: independent clauses, per-source rows, no dates."""
import json
import unicodedata
from pathlib import Path

import pytest

from notary_v2 import administrative_timeline as timeline
from notary_v2.services.administrative_address import (
    AddressIndex,
    AddressLookup,
    expand_abbreviation,
    lookup_address,
    split_query,
)


E = [{"source_id": "synthetic", "row_key": "fictional"}]
VERSION = "test-v2-version"


def _ledger():
    ledger = timeline.empty_ledger()
    ledger["dataset_version"] = VERSION
    ledger["revision"] = 1
    ledger["sources"] = [{
        "id": "synthetic", "provider": "Synthetic test",
        "url": "urn:test:fictional", "protocol": "manual",
        "request_body": None, "retrieved_at": "2026-10-04",
        "sha256": None, "snapshot": None,
        "description": "Fictional fixture, never Vietnamese history",
    }]
    return ledger


def _add_province(ledger, uid, name, raw):
    ledger["units"].append(
        {"id": uid, "level": "province", "source_key": None, "evidence": E})
    ledger["names"].append({
        "id": "name:" + uid, "unit_id": uid, "value": name,
        "valid_from": None, "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    ledger["observations"].append({
        "id": "obs:" + uid, "unit_id": uid,
        "kind": "reported_predecessor", "raw_phrase": raw,
        "details": {"ten": name}, "dataset_version": VERSION,
        "evidence": E})


def _add_commune(ledger, uid, name, parent, raws):
    ledger["units"].append(
        {"id": uid, "level": "commune", "source_key": None, "evidence": E})
    ledger["names"].append({
        "id": "name:" + uid, "unit_id": uid, "value": name,
        "valid_from": None, "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    ledger["parents"].append({
        "id": "parent:" + uid, "unit_id": uid, "parent_id": parent,
        "valid_from": None, "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    for i, raw in enumerate(raws):
        ledger["observations"].append({
            "id": f"obs:{uid}:{i}", "unit_id": uid,
            "kind": "reported_predecessor", "raw_phrase": raw,
            "details": {"ten": name}, "dataset_version": VERSION,
            "evidence": [{"source_id": "synthetic",
                          "row_key": f"{uid}:{i}"}]})


def fixture():
    ledger = _ledger()
    _add_province(ledger, "P_NB", "Tỉnh Ninh Bình",
                  "tỉnh Nam Định, tỉnh Hà Nam sáp nhập thành tỉnh Ninh Bình")
    _add_province(ledger, "P_TN", "Tỉnh Thái Nguyên", "tỉnh Thái Nguyên")
    _add_province(ledger, "P_BD", "Tỉnh Bình Định", "tỉnh Bình Định")
    _add_province(ledger, "P_BRV", "Tỉnh Bà Rịa - Vũng Tàu",
                  "tỉnh Bà Rịa - Vũng Tàu")
    _add_province(ledger, "P_TP", "Thành phố Test", "thành phố Test")
    # Same unit, two active source rows with different raw phrases.
    _add_commune(ledger, "C_YB", "Xã Yên Bình", "P_NB", [
        "Xã Yên Bình (huyện Ý Yên)",
        "Xã Yên Bình, Xã Yên Từ",
    ])
    _add_commune(ledger, "C_YEN2", "Xã Yến Bình", "P_TN",
                 ["Xã Yến Bình"])
    _add_commune(ledger, "C_BY", "Xã Bình Yên", "P_TN", ["Xã Bình Yên"])
    _add_commune(ledger, "C_YTB", "Xã Yên Thịnh Bình", "P_TN",
                 ["Xã Yên Thịnh Bình"])
    _add_commune(ledger, "C_YY", "Xã Ý Yên", "P_NB",
                 ["Thị trấn Lâm, Xã Ý Yên (huyện Ý Yên)"])
    _add_commune(ledger, "C_LAM", "Thị trấn Lâm", "P_NB",
                 ["Thị trấn Lâm (huyện Ý Yên)"])
    _add_commune(ledger, "C_PYB", "Phường Yên Bình", "P_NB",
                 ["Phường Yên Bình"])
    _add_commune(ledger, "C_DXT", "Thị xã Duy Tiên", "P_NB",
                 ["Thị xã Duy Tiên"])
    _add_commune(ledger, "C_AB", "Xã Alpha", "P_TN", ["Beta Gamma"])
    # Unit without any observation: name-only row.
    ledger["units"].append(
        {"id": "C_SOLO", "level": "commune", "source_key": None,
         "evidence": E})
    ledger["names"].append({
        "id": "name:C_SOLO", "unit_id": "C_SOLO",
        "value": "Xã Đơn Độc", "valid_from": None, "valid_to": None,
        "status": "observed", "event_id": None, "evidence": E})
    ledger["parents"].append({
        "id": "parent:C_SOLO", "unit_id": "C_SOLO", "parent_id": "P_TN",
        "valid_from": None, "valid_to": None, "status": "observed",
        "event_id": None, "evidence": E})
    # 11 units sharing one token; first unit carries two observations
    # so the drafting threshold counts 12 result ROWS, not 11 units.
    for n in range(11):
        raws = ["Xã Lặp Lại %02d" % n]
        if n == 0:
            raws.append("Xã Lặp Lại 00 (ghi chú thêm)")
        _add_commune(ledger, "C_DUP%02d" % n, "Xã Lặp Lại %02d" % n,
                     "P_TN", raws)
    # One unit with 11 active source rows sharing a token no other unit
    # has; the official name matches none of the raw-only queries below.
    multi_raws = (["Cụm đặc biệt Alpha (nguồn chung ZZZ)",
                   "Cụm đặc biệt Alpha (nguồn chung ZZZ, dòng hai)"] +
                  ["Cụm khác %02d (nguồn chung ZZZ)" % n for n in range(9)])
    _add_commune(ledger, "C_MULTI", "Xã Đơn Nhất", "P_TN", multi_raws)
    timeline.validate(ledger)
    return ledger


def lookup(payload):
    return AddressIndex(fixture()).lookup(payload)


# ---------- abbreviations, case, NFC, diacritics ----------

@pytest.mark.parametrize("short,full", [
    ("X. Test", "Xã Test"),
    ("P. Test", "Phường Test"),
    ("TT. Test", "Thị trấn Test"),
    ("TP. Test", "Thành phố Test"),
    ("TP Test", "Thành phố Test"),
    ("H. Test", "Huyện Test"),
    ("Q. Test", "Quận Test"),
    ("TX. Test", "Thị xã Test"),
    ("p. test", "Phường test"),
])
def test_abbreviations_expand_to_full_prefix(short, full):
    assert expand_abbreviation(short) == full


def test_abbreviation_keeps_prefix_and_case_insensitive():
    # Prefix is part of the official name: xa Yen Binh never hits Phuong.
    answer = lookup({"query": "X. Yên Bình", "presentation": "drafting"})
    assert answer["status"] == "found"
    assert {r["name"] for r in answer["results"]} == {"Xã Yên Bình"}
    upper = lookup({"query": "XÃ YÊN BÌNH", "presentation": "drafting"})
    assert upper["status"] == "found"
    assert {r["name"] for r in upper["results"]} == {"Xã Yên Bình"}


def test_undiacritic_matches_both_yen_forms_diacritic_is_narrow():
    broad = lookup({"query": "yen binh", "presentation": "full"})
    assert broad["status"] == "found"
    assert {"Xã Yên Bình", "Xã Yến Bình"} <= {
        r["name"] for r in broad["results"]}
    narrow = lookup({"query": "yên bình", "presentation": "full"})
    assert narrow["status"] == "found"
    assert {r["name"] for r in narrow["results"]} == {
        "Xã Yên Bình", "Phường Yên Bình"}
    # P. yen binh is undiacritic input: prefix expands, then both sides
    # are compared without marks.
    assert lookup(
        {"query": "P. yen binh", "presentation": "drafting"})["status"] == "found"
    assert lookup(
        {"query": "P. yên bình", "presentation": "drafting"})["status"] == "found"


def test_nfd_input_matches_nfc_database():
    nfd = unicodedata.normalize("NFD", "xã Yên Bình")
    nfc = unicodedata.normalize("NFC", "xã Yên Bình")
    assert nfd != nfc
    assert lookup({"query": nfd, "presentation": "drafting"}) == lookup(
        {"query": nfc, "presentation": "drafting"})


def test_numbers_are_literal():
    assert lookup(
        {"query": "Phường 01", "presentation": "drafting"})["status"] == "not_found"


# ---------- contiguous, in-order, single-field matching ----------

def test_wrong_order_never_matches():
    assert "Xã Yên Bình" not in {
        r["name"] for r in
        lookup({"query": "Bình Yên", "presentation": "full"})["results"]}
    assert "Xã Bình Yên" not in {
        r["name"] for r in
        lookup({"query": "Yên Bình", "presentation": "full"})["results"]}
    assert "Xã Yên Bình" not in {
        r["name"] for r in lookup(
            {"query": "Yên Thịnh Bình", "presentation": "full"})["results"]}


def test_clause_never_spans_name_and_raw_phrase():
    # "Alpha Beta" is contiguous in neither the name ("Xã Alpha") nor the
    # raw phrase ("Beta Gamma") alone, so it must not match.
    assert lookup(
        {"query": "Alpha Beta", "presentation": "full"})["status"] == "not_found"


def test_hyphenated_name_splits_into_independent_clauses():
    answer = lookup(
        {"query": "Bà Rịa - Vũng Tàu", "presentation": "drafting"})
    assert answer["status"] == "found"
    assert answer["total"] == len(answer["results"]) == 1
    assert answer["results"][0]["name"] == "Tỉnh Bà Rịa - Vũng Tàu"


def test_parenthetical_note_matches_raw_phrase():
    answer = lookup(
        {"query": "huyện Ý Yên", "presentation": "full"})
    assert answer["status"] == "found"
    assert answer["results"]
    assert all("(huyện Ý Yên)" in (r["source_text"] or "")
               for r in answer["results"])


# ---------- independent clauses, provinces always separate ----------

def test_every_clause_searches_communes_and_provinces():
    answer = lookup({"query": "Yên Bình, Ý Yên, Nam Định",
                     "presentation": "full"})
    assert answer["status"] == "found"
    names = [r["name"] for r in answer["results"]]
    assert "Xã Ý Yên" in names
    assert "Xã Yên Bình" in names
    assert "Tỉnh Ninh Bình" in names
    levels = [r["level"] for r in answer["results"]
              if r["name"] == "Tỉnh Ninh Bình"]
    assert levels == ["province"]


def test_province_match_is_its_own_row_even_as_parent():
    answer = lookup(
        {"query": "xã Yên Bình, tỉnh Nam Định", "presentation": "full"})
    assert answer["status"] == "found"
    provinces = [r for r in answer["results"]
                 if r["name"] == "Tỉnh Ninh Bình"]
    assert len(provinces) == 1
    assert provinces[0]["level"] == "province"
    assert provinces[0]["province"] is None


def test_one_clause_matching_many_provinces():
    answer = lookup({"query": "Bình Định", "presentation": "full"})
    assert answer["status"] == "found"
    assert "Tỉnh Bình Định" in [r["name"] for r in answer["results"]]


def test_district_clause_matches_raw_phrase_rows():
    answer = lookup({"query": "quận Hà Đông", "presentation": "full"})
    assert answer["status"] == "not_found"


def test_communes_before_provinces_in_ledger_order():
    answer = lookup({"query": "Bình", "presentation": "full"})
    assert answer["status"] == "found"
    levels = [r["level"] for r in answer["results"]]
    assert "commune" in levels and "province" in levels
    assert levels.index("province") > levels.index("commune")


def test_no_district_level_rows():
    answer = lookup({"query": "Yên Bình", "presentation": "full"})
    assert answer["status"] == "found"
    assert {r["level"] for r in answer["results"]} <= {"commune", "province"}


# ---------- many source rows: separate rows, row counting ----------

def test_official_name_match_returns_every_source_row():
    answer = lookup({"query": "Xã Yên Bình", "presentation": "full"})
    assert answer["status"] == "found"
    rows = [r for r in answer["results"] if r["unit_id"] == "C_YB"]
    assert len(rows) == 2
    assert rows[0]["source_text"] == "Xã Yên Bình (huyện Ý Yên)"
    assert rows[1]["source_text"] == "Xã Yên Bình, Xã Yên Từ"
    assert rows[0]["observation_id"] != rows[1]["observation_id"]
    assert rows[0]["evidence"] != rows[1]["evidence"]
    assert all(r["evidence"] for r in rows)


def test_raw_only_match_returns_single_source_row():
    answer = lookup({"query": "Xã Yên Từ", "presentation": "full"})
    assert answer["status"] == "found"
    rows = [r for r in answer["results"] if r["unit_id"] == "C_YB"]
    assert len(rows) == 1
    assert rows[0]["source_text"] == "Xã Yên Bình, Xã Yên Từ"


def test_repeated_hit_of_same_row_across_clauses_dedupes():
    single = lookup({"query": "Yên Bình", "presentation": "full"})
    double = lookup({"query": "Yên Bình, Xã Yên Bình", "presentation": "full"})
    assert single["status"] == "found"
    assert double["total"] == single["total"]
    assert [(r["unit_id"], r.get("observation_id")) for r in double["results"]] == [
        (r["unit_id"], r.get("observation_id")) for r in single["results"]]


def test_unit_without_observation_returns_name_only_row():
    answer = lookup({"query": "Đơn Độc", "presentation": "full"})
    assert answer["status"] == "found"
    assert answer["total"] == 1
    row = answer["results"][0]
    assert row["unit_id"] == "C_SOLO"
    assert row["name"] == "Xã Đơn Độc"
    assert row["source_text"] is None
    assert "observation_id" not in row


# ---------- presentations, thresholds, runtime invariants ----------

def test_drafting_display_shape_and_province_row():
    answer = lookup({"query": "Xã Ý Yên", "presentation": "drafting"})
    assert answer["status"] == "found"
    row = next(r for r in answer["results"] if r["name"] == "Xã Ý Yên")
    assert row["display"] == "xã Ý Yên, tỉnh Ninh Bình"
    assert row["province"] == {"unit_id": "P_NB", "name": "Tỉnh Ninh Bình"}


def test_full_display_keeps_raw_source_text():
    answer = lookup({"query": "Xã Ý Yên", "presentation": "full"})
    assert answer["status"] == "found"
    row = next(r for r in answer["results"] if r["name"] == "Xã Ý Yên")
    assert row["display"].startswith("Xã Ý Yên = ")
    assert "(huyện Ý Yên)" in row["display"]
    assert row["display"].endswith(", Tỉnh Ninh Bình")


def test_too_many_counts_rows_and_full_is_unlimited():
    drafting = lookup({"query": "Lặp Lại", "presentation": "drafting"})
    assert drafting["status"] == "too_many"
    assert drafting["total"] == 12
    assert drafting["results"] == []
    full = lookup({"query": "Lặp Lại", "presentation": "full"})
    assert full["status"] == "found"
    assert full["total"] == 12
    assert len(full["results"]) == 12


def test_empty_statuses_carry_zero_total_and_echo_presentation():
    assert lookup(
        {"query": "abcxyz123", "presentation": "drafting"}) == {
        "schema_version": "notary.address-lookup.v2", "status": "not_found",
        "presentation": "drafting", "total": 0, "results": [],
        "dataset_version": VERSION, "revision": 1}
    assert lookup({"query": "  , - ,", "presentation": "full"})["status"] \
        == "not_found"


@pytest.mark.parametrize("payload", [
    {"query": "", "presentation": "drafting"},
    {"query": "x" * 4001, "presentation": "drafting"},
    {"query": 123, "presentation": "drafting"},
    {"query": None, "presentation": "drafting"},
    {"query": "yen binh", "presentation": "drafting",
     "source_date": "2020-01-01"},
    {"query": "yen binh", "presentation": "drafting",
     "target_date": "2026-10-04"},
    {"query": "yen binh", "presentation": "drafting", "province": "P"},
    {"query": "yen binh", "presentation": "bogus"},
    {"query": "yen binh"},
    {"presentation": "drafting"},
    "yen binh",
    None,
])
def test_invalid_input_shape(payload):
    answer = lookup(payload)
    assert answer["status"] == "invalid_input"
    assert answer["presentation"] is None
    assert answer["total"] == 0
    assert answer["results"] == []
    assert answer["schema_version"] == "notary.address-lookup.v2"


@pytest.mark.parametrize("query", ["   ", "  , - ,"])
def test_blank_or_separators_only_is_not_found(query):
    answer = lookup({"query": query, "presentation": "drafting"})
    assert answer["status"] == "not_found"
    assert answer["presentation"] == "drafting"
    assert answer["total"] == 0
    assert answer["results"] == []


def test_query_length_checked_before_normalization():
    assert lookup(
        {"query": "z" * 4000, "presentation": "drafting"})["status"] \
        in ("found", "not_found", "too_many")
    assert lookup(
        {"query": "z" * 4001, "presentation": "drafting"})["status"] \
        == "invalid_input"
    assert lookup(
        {"query": "x", "presentation": "drafting"})["status"] \
        in ("found", "not_found", "too_many")


def test_runtime_invariants_hold_for_every_status():
    for query, presentation in [
        ("Xã Yên Bình", "drafting"), ("yen binh", "full"),
        ("Lặp Lại", "drafting"), ("abcxyz123", "drafting"),
        ("", "drafting"), ("Xã Yên Bình", "full"),
    ]:
        answer = lookup({"query": query, "presentation": presentation})
        if answer["status"] == "found":
            assert answer["total"] == len(answer["results"]) >= 1
            if presentation == "drafting":
                assert answer["total"] <= 10
        elif answer["status"] == "too_many":
            assert answer["presentation"] == "drafting"
            assert answer["total"] > 10
            assert answer["results"] == []
        else:
            assert answer["total"] == 0
            assert answer["results"] == []
        if answer["status"] == "invalid_input":
            assert answer["presentation"] is None
        else:
            assert answer["presentation"] == presentation


def test_split_query_only_strips_outer_spaces():
    assert split_query("a, b-c") == ["a", "b", "c"]
    assert split_query("  , - ,") == []
    assert split_query("Bà Rịa - Vũng Tàu") == ["Bà Rịa", "Vũng Tàu"]


# ---------- cache, reload, staging, schema ----------

def test_cache_revision_bump_and_failed_reload(tmp_path):
    ledger = fixture()
    timeline.atomic_write(tmp_path, ledger)
    service = AddressLookup(tmp_path)
    first = service.lookup({"query": "Xã Yên Bình",
                            "presentation": "drafting"})
    assert first["revision"] == 1
    assert first["status"] == "found"
    ledger["revision"] = 2
    timeline.atomic_write(tmp_path, ledger)
    updated = service.lookup({"query": "Xã Yên Bình",
                              "presentation": "drafting"})
    assert updated["revision"] == 2
    assert updated["status"] == "found"
    (tmp_path / "ledger.json").write_text("{broken", encoding="utf-8")
    failed = service.lookup({"query": "Xã Yên Bình",
                             "presentation": "drafting"})
    assert failed["status"] == "reload_failed"
    assert failed["presentation"] == "drafting"
    assert failed["total"] == 0
    assert failed["results"] == []


def test_missing_snapshot_refuses_old_results(tmp_path):
    import shutil
    shutil.copytree(timeline.DEFAULT_FOLDER, tmp_path, dirs_exist_ok=True)
    service = AddressLookup(tmp_path)
    assert service.lookup(
        {"query": "tỉnh Nam Định",
         "presentation": "drafting"})["status"] == "found"
    next((tmp_path / "snapshots").glob("*.raw")).unlink()
    failed = service.lookup({"query": "tỉnh Nam Định",
                             "presentation": "drafting"})
    assert failed["status"] == "reload_failed"
    assert failed["results"] == []


def test_schema_v2_shapes():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((timeline.ROOT / "contracts/notary-case-drafting"
                         / "address-lookup.v2.schema.json").read_text(
                             encoding="utf-8"))
    payload_schema = {**schema, "$ref": "#/definitions/payload"}
    result_schema = {**schema, "$ref": "#/definitions/result_data"}
    jsonschema.Draft7Validator(payload_schema).validate(
        {"query": "yen binh", "presentation": "drafting"})
    for payload in [
        {"query": "Xã Yên Bình", "presentation": "drafting"},
        {"query": "Lặp Lại", "presentation": "drafting"},
        {"query": "yen binh", "presentation": "full"},
        {"query": "abcxyz123", "presentation": "drafting"},
        {"query": "", "presentation": "drafting"},
    ]:
        jsonschema.Draft7Validator(result_schema).validate(lookup(payload))
    with pytest.raises(Exception):
        jsonschema.Draft7Validator(payload_schema).validate(
            {"query": "x", "presentation": "drafting",
             "source_date": "2020-01-01"})


def test_real_ledger_owner_cases():
    found = lookup_address({"query": "tỉnh Nam Định",
                            "presentation": "drafting"})
    assert found["status"] == "found"
    assert "tỉnh Ninh Bình" in [r["display"] for r in found["results"]]
    multi = lookup_address(
        {"query": "Thị trấn Lâm, huyện Ý Yên, tỉnh Nam Định",
         "presentation": "drafting"})
    assert multi["status"] in ("found", "too_many")
    if multi["status"] == "found":
        assert any("Ý Yên" in r["display"] for r in multi["results"])
    missing = lookup_address(
        {"query": "abcxyz123-notfound", "presentation": "drafting"})
    assert missing["status"] == "not_found"
    assert missing["total"] == 0


def test_isolated_staged_source_without_checkout_fallback(tmp_path):
    import shutil
    import subprocess
    import sys
    engine = tmp_path / "engine"
    module = engine / "notary_v2"
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("Production staging uses Windows PowerShell")
    staged = subprocess.run(
        [powershell, "-NoProfile", "-File",
         str(timeline.ROOT / "shell/sidecar/stage_administrative_reference.ps1"),
         "-Repository", str(timeline.ROOT), "-EngineStage", str(engine)],
        capture_output=True, text=True)
    assert staged.returncode == 0, staged.stderr
    assert not list(engine.rglob("*.db"))
    assert not list(engine.rglob(".write.lock"))
    assert not list(engine.rglob("revisions"))
    code = (
        "import sys,json; sys.path.insert(0,sys.argv[1]); "
        "from services.administrative_address import lookup_address; "
        "r=lookup_address(json.loads(sys.argv[2])); "
        "assert r['status'] in ('found','too_many'),r; print(r['revision'])"
    )
    payload = json.dumps({"query": "tỉnh Nam Định",
                          "presentation": "drafting"})
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code, str(module), payload],
        cwd=tmp_path, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


def test_validate_examples_reports_zero_errors():
    import subprocess
    import sys
    completed = subprocess.run(
        [sys.executable,
         str(timeline.ROOT / "contracts/notary-case-drafting"
             / "validate_examples.py")],
        capture_output=True, text=True, cwd=str(timeline.ROOT))
    assert completed.returncode == 0, completed.stdout + completed.stderr


# ---------- R1/R2 regression (audit 20261005) ----------

def test_r1_raw_only_match_returns_every_matching_source_row():
    answer = lookup({"query": "đặc biệt Alpha", "presentation": "full"})
    assert answer["status"] == "found"
    rows = [r for r in answer["results"] if r["unit_id"] == "C_MULTI"]
    assert len(rows) == 2
    assert [r["source_text"] for r in rows] == [
        "Cụm đặc biệt Alpha (nguồn chung ZZZ)",
        "Cụm đặc biệt Alpha (nguồn chung ZZZ, dòng hai)"]
    assert len({r["observation_id"] for r in rows}) == 2


def test_r1_official_name_match_returns_all_eleven_source_rows():
    answer = lookup({"query": "Đơn Nhất", "presentation": "full"})
    assert answer["status"] == "found"
    rows = [r for r in answer["results"] if r["unit_id"] == "C_MULTI"]
    assert len(rows) == 11
    assert [r["observation_id"] for r in rows] == [
        f"obs:C_MULTI:{n}" for n in range(11)]
    assert len({r["observation_id"] for r in rows}) == 11


def test_r1_eleven_source_rows_hit_drafting_threshold():
    drafting = lookup({"query": "nguồn chung ZZZ", "presentation": "drafting"})
    assert drafting["status"] == "too_many"
    assert drafting["total"] == 11
    assert drafting["results"] == []
    full = lookup({"query": "nguồn chung ZZZ", "presentation": "full"})
    assert full["status"] == "found"
    assert full["total"] == 11
    assert len(full["results"]) == 11
    assert {r["unit_id"] for r in full["results"]} == {"C_MULTI"}


def test_source_order_does_not_follow_query_order_for_both_levels():
    ledger = fixture()
    _add_province(ledger, "P_ORDER", "Tỉnh Thứ Tự", "Nguồn đầu")
    ledger["observations"].append({**ledger["observations"][-1],
        "id": "obs:P_ORDER:second", "raw_phrase": "Nguồn sau"})
    answer = AddressIndex(ledger).lookup({"query": "dòng hai, Cụm đặc biệt Alpha, Nguồn sau, Nguồn đầu",
                                          "presentation": "full"})
    assert [r["observation_id"] for r in answer["results"]] == [
        "obs:C_MULTI:0", "obs:C_MULTI:1", "obs:P_ORDER", "obs:P_ORDER:second"]


def test_current_commune_missing_province_reports_reload_failed(tmp_path):
    ledger = fixture()
    ledger["parents"] = [r for r in ledger["parents"] if r["unit_id"] != "C_SOLO"]
    timeline.validate(ledger)
    (tmp_path / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    answer = AddressLookup(tmp_path).lookup({"query": "Xã Đơn Độc", "presentation": "full"})
    assert answer["status"] == "reload_failed"
    assert answer["results"] == []


def test_imported_removed_unit_is_not_a_current_name_only_unit(tmp_path):
    raw, tables = _audit_snapshot("Xã Ban Đầu Demo", "01")
    timeline.import_bando(tmp_path, raw, "2026-10-03", tables, strict=False)
    service = AddressLookup(tmp_path)
    assert service.lookup({"query": "Ban Đầu Demo", "presentation": "full"})["status"] == "found"
    raw, tables = _audit_snapshot("Xã Hiện Tại Demo", "02")
    timeline.import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    rows = [r for r in json.loads(raw) if r["magoc"] == "0"]
    raw = json.dumps(rows, ensure_ascii=False).encode()
    tables = {p["ma"]: (json.dumps(p, ensure_ascii=False) + ".synt.[]").encode() for p in rows}
    timeline.import_bando(tmp_path, raw, "2026-10-05", tables, strict=False)
    for query in ("Ban Đầu Demo", "Hiện Tại Demo", "Gốc Demo"):
        answer = service.lookup({"query": query, "presentation": "full"})
        assert answer["status"] == "not_found"
    # Non-imported name-only fixtures are still valid catalog rows.
    assert lookup({"query": "Xã Đơn Độc", "presentation": "full"})["status"] == "found"


def _audit_snapshot(commune_name, parent_code):
    rows = [
        {"ma": "01", "magoc": "0", "malk": "audit-province-a",
         "ten": "Tỉnh Demo A", "truocsapnhap": "giữ nguyên"},
        {"ma": "02", "magoc": "0", "malk": "audit-province-b",
         "ten": "Tỉnh Demo B", "truocsapnhap": "giữ nguyên"},
        {"ma": "00001", "magoc": parent_code, "malk": "audit-commune",
         "ten": commune_name, "truocsapnhap": "Xã Gốc Demo (nguồn A)"},
    ]
    raw = json.dumps(rows, ensure_ascii=False).encode()
    tables = {
        p["ma"]: (json.dumps(p, ensure_ascii=False) + ".synt." + json.dumps(
            [r for r in rows if r["magoc"] == p["ma"]], ensure_ascii=False
        )).encode()
        for p in rows if p["magoc"] == "0"
    }
    return raw, tables


def test_r2_name_and_parent_follow_refreshed_ledger(tmp_path):
    from notary_v2.services.administrative_address import AddressLookup
    raw, tables = _audit_snapshot("Xã Ban Đầu Demo", "01")
    timeline.import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    raw, tables = _audit_snapshot("Xã Hiện Tại Demo", "02")
    timeline.import_bando(tmp_path, raw, "2026-10-05", tables, strict=False)
    current = timeline.read_ledger(tmp_path)
    service = AddressLookup(tmp_path)
    answer = service.lookup({"query": "Gốc Demo", "presentation": "full"})
    assert answer["status"] == "found"
    assert answer["dataset_version"] == current["dataset_version"]
    row = answer["results"][0]
    assert row["name"] == "Xã Hiện Tại Demo"
    assert row["province"]["name"] == "Tỉnh Demo B"
    renamed = service.lookup({"query": "Hiện Tại Demo",
                              "presentation": "full"})
    assert renamed["status"] == "found"
    assert renamed["results"][0]["name"] == "Xã Hiện Tại Demo"
