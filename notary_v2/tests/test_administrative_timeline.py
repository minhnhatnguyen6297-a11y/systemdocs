"""Synthetic fixtures are deliberately fictional, never historical claims."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from notary_v2.administrative_timeline import (
    LedgerError, DEFAULT_FOLDER, atomic_write, empty_ledger, import_bando,
    manual_update, query, read_ledger, validate, locked, SCHEMA,
)


def fixture():
    ledger = empty_ledger()
    ledger["sources"] = [{"id": "synthetic", "provider": "Synthetic test", "url": "urn:test:fictional",
        "protocol": "manual", "request_body": None, "retrieved_at": "2026-10-04T00:00:00+07:00",
        "sha256": None, "snapshot": None, "description": "Fictional fixture, not Vietnamese history"}]
    return ledger


EVIDENCE = [{"source_id": "synthetic", "row_key": "fictional"}]


def unit(uid, level="commune"):
    return {"id": uid, "level": level, "source_key": None, "evidence": EVIDENCE}


def name(uid, value, start, end=None, event=None):
    return {"id": f"name:{uid}:{value}", "unit_id": uid, "value": value, "valid_from": start,
        "valid_to": end, "status": "confirmed", "event_id": event, "evidence": EVIDENCE}


def event(eid, kind, before, after, day):
    return {"id": eid, "type": kind, "from": [{"kind": "unit", "id": u} for u in before],
        "to": [{"kind": "unit", "id": u} for u in after], "effective_on": day,
        "valid_from": None, "valid_to": None, "status": "confirmed", "territory": "whole",
        "notes": "Fictional test", "evidence": EVIDENCE}


def bando_fixture():
    rows = [{"ma": "01", "ten": "Tỉnh Test", "magoc": "0", "malk": "province:test", "truocsapnhap": "giữ nguyên"},
            {"ma": "00001", "ten": "Xã C", "magoc": "01", "malk": "commune:test", "truocsapnhap": "Xã A và một phần Xã B (huyện Test)"},
            {"ma": "00002", "ten": "Xã D", "magoc": "01", "malk": "commune:other", "truocsapnhap": "Xã A"}]
    raw = json.dumps(rows, ensure_ascii=False).encode()
    table = (json.dumps(rows[0], ensure_ascii=False)+".synt."+json.dumps(rows[1:], ensure_ascii=False)).encode()
    return raw, {"01": table}


def test_a_b_c_d_rename_same_identity_dates_and_query():
    ledger = fixture()
    ledger["units"] = [unit("stable")]
    ledger["names"] = [name("stable", "A", "2000-01-01", "2005-01-01"),
        name("stable", "B", "2005-01-01", "2010-01-01", "ab"),
        name("stable", "C", "2010-01-01", "2020-01-01", "bc"),
        name("stable", "D", "2020-01-01", event="cd")]
    ledger["events"] = [event("ab", "rename", ["stable"], ["stable"], "2005-01-01"),
        event("bc", "rename", ["stable"], ["stable"], "2010-01-01"),
        event("cd", "rename", ["stable"], ["stable"], "2020-01-01")]
    assert validate(ledger)["valid"]
    answer = query(ledger, "stable", "2015-04-01")
    assert [n["value"] for n in answer["confirmed_name_at_date"]] == ["C"]
    assert [e["id"] for e in answer["chronological_events"]] == ["ab", "bc", "cd"]


def test_merge_split_chain_and_abolition():
    ledger = fixture()
    ledger["units"] = [unit(u) for u in "ABCDE"]
    ledger["events"] = [event("merge", "merge", ["A", "B"], ["C"], "2000-01-01"),
        event("split", "split", ["C"], ["D", "E"], "2010-01-01"),
        event("abolish", "abolish", ["D"], [], "2020-01-01")]
    assert validate(ledger)["valid"]
    assert len(query(ledger, "A")["chronological_events"]) == 3


def test_three_levels_reparent_and_district_history():
    ledger = fixture()
    ledger["units"] = [unit("P1", "province"), unit("P2", "province"), unit("D", "district"), unit("C")]
    ledger["names"] = [name("P1", "Province", "2000-01-01"), name("D", "District A", "2000-01-01", "2010-01-01"),
        name("D", "District B", "2010-01-01", "2020-01-01", event="rename")]
    ledger["parents"] = [{"id": "p1", "unit_id": "D", "parent_id": "P1", "valid_from": "2000-01-01", "valid_to": "2015-01-01",
        "status": "confirmed", "event_id": None, "evidence": EVIDENCE},
        {"id": "p2", "unit_id": "D", "parent_id": "P2", "valid_from": "2015-01-01", "valid_to": "2020-01-01",
         "status": "confirmed", "event_id": "reparent", "evidence": EVIDENCE}]
    ledger["events"] = [event("rename", "rename", ["D"], ["D"], "2010-01-01"),
        event("reparent", "reparent", ["D"], ["D"], "2015-01-01"), event("abolish", "abolish", ["D"], [], "2020-01-01")]
    assert validate(ledger)["valid"]


def test_lossless_pending_partial_unchanged_and_same_name_unrelated(tmp_path):
    raw, tables = bando_fixture()
    result = import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    ledger = read_ledger(tmp_path)
    assert result["coverage"]["unchanged_rows"] == 1
    assert result["coverage"]["partial_rows"] == 1
    assert len(ledger["mentions"]) == 2
    assert ledger["mentions"][0]["raw_phrase"] == "Xã A và một phần Xã B (huyện Test)"
    assert len({m["id"] for m in ledger["mentions"]}) == 2
    assert all(m["resolved_unit_id"] is None for m in ledger["mentions"])
    assert all(e["effective_on"] is None and e["status"] == "pending" for e in ledger["events"])
    uid = next(u["id"] for u in ledger["units"] if u["source_key"] == "commune:test")
    answer = query(ledger, uid, "2025-07-01")
    assert answer["confirmed_name_at_date"] == []
    assert len(answer["pending_evidence"]) == 1
    assert answer["chronological_events"] == []


def test_idempotent_new_refresh_preserves_owner_history_and_old_evidence(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    before = (tmp_path / "ledger.json").read_bytes()
    import_bando(tmp_path, raw, "2026-10-05T00:00:00+07:00", tables, strict=False)
    assert (tmp_path / "ledger.json").read_bytes() == before
    ledger = read_ledger(tmp_path)
    manual_update(tmp_path, {"base_revision": ledger["revision"], "upsert": {
        "sources": fixture()["sources"], "units": [unit("owner")], "names": [name("owner", "Older A", "2000-01-01")]}})
    rows = json.loads(raw)
    rows[1]["ten"] = "Xã New C"
    newraw = json.dumps(rows, ensure_ascii=False).encode()
    newtables = {"01": (json.dumps(rows[0], ensure_ascii=False)+".synt."+json.dumps(rows[1:], ensure_ascii=False)).encode()}
    import_bando(tmp_path, newraw, "2026-10-05T00:00:00+07:00", newtables, strict=False)
    ledger = read_ledger(tmp_path)
    assert len([u for u in ledger["units"] if u["source_key"] == "commune:test"]) == 1
    assert {n["value"] for n in ledger["names"]} >= {"Xã C", "Xã New C", "Older A"}
    assert len(ledger["sources"]) == 5


def test_source_code_reuse_does_not_force_identity(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    rows = json.loads(raw)
    rows[1]["malk"] = "commune:new-identity"
    newraw = json.dumps(rows).encode()
    newtables = {"01": (json.dumps(rows[0])+".synt."+json.dumps(rows[1:])).encode()}
    import_bando(tmp_path, newraw, "2026-10-05T00:00:00+07:00", newtables, strict=False)
    ledger = read_ledger(tmp_path)
    assert len({c["unit_id"] for c in ledger["codes"] if c["value"] == "00001"}) == 2


def test_confirmed_code_reuse_can_be_sequential_but_not_overlap():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["codes"] = [dict(name("A", "001", "2000-01-01", "2010-01-01"), id="code:A"),
        dict(name("B", "001", "2010-01-01"), id="code:B")]
    assert validate(ledger)["valid"]
    ledger["codes"][1]["valid_from"] = "2009-01-01"
    with pytest.raises(LedgerError, match="code reuse"):
        validate(ledger)


@pytest.mark.parametrize("mutation,match", [
    (lambda l: l["names"][0].update(unit_id="missing"), "dangling unit"),
    (lambda l: l["names"][0].update(valid_from="2000-02-31"), "invalid date"),
    (lambda l: l["names"].append(name("A", "Other", "2005-01-01")), "overlapping"),
    (lambda l: l["events"].append(event("bad", "rename", ["A"], ["B"], "2010-01-01")), "identity"),
    (lambda l: l["names"][0].update(evidence=[{"source_id": "missing", "row_key": "x"}]), "dangling source"),
    (lambda l: l["names"][0].update(event_id="missing"), "dangling event"),
    (lambda l: l["names"][0].update(valid_to="1999-01-01"), "reversed"),
    (lambda l: l["events"].append(event("bad", "reported_transition", ["A"], ["missing"], "2010-01-01")), "dangling"),
])
def test_invalid_structured_history(mutation, match):
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["names"] = [name("A", "A", "2000-01-01")]
    mutation(ledger)
    with pytest.raises(LedgerError, match=match):
        validate(ledger)


def test_confirmed_cycles_and_backwards_chain_rejected():
    ledger = fixture()
    ledger["units"] = [unit(u) for u in "ABC"]
    ledger["events"] = [event("ab", "reported_transition", ["A"], ["B"], "2010-01-01"),
        event("ba", "reported_transition", ["B"], ["A"], "2020-01-01")]
    with pytest.raises(LedgerError, match="cycle"):
        validate(ledger)
    ledger["events"][1] = event("bc", "reported_transition", ["B"], ["C"], "2000-01-01")
    with pytest.raises(LedgerError, match="date contradiction"):
        validate(ledger)


def test_parent_cycle_and_event_date_conflict_rejected():
    ledger = fixture()
    ledger["units"] = [unit("A", "province")]
    ledger["parents"] = [{"id": "p", "unit_id": "A", "parent_id": "A", "valid_from": "2000-01-01", "valid_to": None,
        "status": "confirmed", "event_id": None, "evidence": EVIDENCE}]
    with pytest.raises(LedgerError, match="cycle"):
        validate(ledger)
    ledger["parents"] = []
    ledger["events"] = [event("rename", "rename", ["A"], ["A"], "2010-01-01")]
    ledger["names"] = [name("A", "New A", "2011-01-01", event="rename")]
    with pytest.raises(LedgerError, match="contradicts event"):
        validate(ledger)


def test_failed_refresh_and_failed_atomic_replace_keep_bytes(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    before = (tmp_path / "ledger.json").read_bytes()
    for bad in (b"[]", b"not-json", b"{}"):
        with pytest.raises(LedgerError):
            import_bando(tmp_path, bad, "2026-10-04T00:00:00+07:00", tables, strict=False)
    with pytest.raises(LedgerError, match="table"):
        import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", {"01": b"broken"}, strict=False)
    with patch("notary_v2.administrative_timeline.os.replace", side_effect=OSError("disk failure")):
        with pytest.raises(OSError):
            atomic_write(tmp_path, read_ledger(tmp_path))
    assert (tmp_path / "ledger.json").read_bytes() == before
    assert not list(tmp_path.glob(".ledger-*.tmp"))


def test_manual_stale_invalid_and_source_rewrite_keep_bytes(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    ledger = read_ledger(tmp_path)
    before = (tmp_path / "ledger.json").read_bytes()
    with pytest.raises(LedgerError, match="stale"):
        manual_update(tmp_path, {"base_revision": 0, "upsert": {}})
    with pytest.raises(LedgerError, match="dangling"):
        manual_update(tmp_path, {"base_revision": 1, "upsert": {"names": [name("missing", "X", "2000-01-01")]}})
    changed = deepcopy(ledger["names"][0])
    changed["value"] = "Rewrite"
    with pytest.raises(LedgerError, match="immutable"):
        manual_update(tmp_path, {"base_revision": 1, "upsert": {"names": [changed]}})
    assert (tmp_path / "ledger.json").read_bytes() == before


def test_snapshot_corruption_rejected(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04T00:00:00+07:00", tables, strict=False)
    next((tmp_path / "snapshots").glob("*.raw")).write_bytes(b"corrupt")
    with pytest.raises(LedgerError, match="hash mismatch"):
        validate(read_ledger(tmp_path), tmp_path)


def test_real_full_data_schema_source_counts_and_dates():
    ledger = read_ledger(DEFAULT_FOLDER)
    result = validate(ledger, DEFAULT_FOLDER)
    assert result["coverage"]["province"] == 34
    assert result["coverage"]["commune"] == 3321
    assert result["coverage"]["district"] == 0
    assert len(ledger["units"]) == 3355
    assert len(ledger["sources"]) == 35
    assert all(e["effective_on"] is None for e in ledger["events"])
    assert all(n["valid_from"] is None for n in ledger["names"])
    row = next(o for o in ledger["observations"] if o["details"]["ma"] == "13336")
    assert row["raw_phrase"] == "Phường Duy Minh, Phường Duy Hải và một phần diện tích tự nhiên, quy mô dân số của Phường Hoàng Đông"


def test_manual_resolves_identity_but_preserves_phrase_and_refresh(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    mention = deepcopy(ledger["mentions"][0])
    mention.update(resolved_unit_id="owner:old", status="confirmed")
    manual_update(tmp_path, {"base_revision": 1, "upsert": {"sources": fixture()["sources"],
        "units": [unit("owner:old")], "mentions": [mention]}})
    assert read_ledger(tmp_path)["mentions"][0]["resolved_unit_id"] == "owner:old"
    original = (tmp_path / "ledger.json").read_bytes()
    import_bando(tmp_path, raw, "2026-10-05", tables, strict=False)
    assert (tmp_path / "ledger.json").read_bytes() == original
    mention["raw_phrase"] = "invented"
    with pytest.raises(LedgerError, match="immutable"):
        manual_update(tmp_path, {"base_revision": 2, "upsert": {"mentions": [mention]}})


def test_abolished_unit_cannot_have_future_rename_or_open_period():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["events"] = [event("gone", "abolish", ["A"], [], "2010-01-01"),
        event("late", "rename", ["A"], ["A"], "2020-01-01")]
    with pytest.raises(LedgerError, match="abolished"):
        validate(ledger)
    ledger["events"].pop()
    ledger["names"] = [name("A", "A", "2000-01-01")]
    with pytest.raises(LedgerError, match="outlives"):
        validate(ledger)


def test_confirmed_pending_missing_dates_and_wrong_cardinality():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["events"] = [event("x", "merge", ["A"], ["B"], "2010-01-01")]
    with pytest.raises(LedgerError, match="cardinality"):
        validate(ledger)
    ledger["events"][0]["type"] = "reported_transition"
    ledger["events"][0]["effective_on"] = None
    with pytest.raises(LedgerError, match="confirmed event needs date"):
        validate(ledger)
    ledger["events"][0]["status"] = "pending"
    assert validate(ledger)["valid"]
    assert query(ledger, "A", "2020-01-01")["chronological_events"] == []


def test_reimport_older_snapshot_keeps_history_without_duplicate_ids(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    rows = json.loads(raw)
    rows[1]["ten"] = "Xã Changed"
    changed_raw = json.dumps(rows).encode()
    changed_tables = {"01": (json.dumps(rows[0])+".synt."+json.dumps(rows[1:])).encode()}
    import_bando(tmp_path, changed_raw, "2026-10-05", changed_tables, strict=False)
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    assert len(ledger["names"]) == 6
    assert {n["value"] for n in ledger["names"]} >= {"Xã C", "Xã Changed"}
    assert validate(ledger, tmp_path)["valid"]


def test_spec_json_patch_is_valid_and_cli_query_semantics(tmp_path):
    import re
    text = (Path(__file__).resolve().parents[2] / "_bmad-output/specs/notary_v2/administrative-timeline.md").read_text(encoding="utf8")
    example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
    ledger = empty_ledger()
    ledger["revision"] = 1
    atomic_write(tmp_path, ledger)
    manual_update(tmp_path, example)
    answer = query(read_ledger(tmp_path), "owner:demo", "2007-01-01")
    assert answer["confirmed_name_at_date"][0]["value"] == "B"


def test_schema_version_and_unsafe_snapshot_rejected():
    ledger = fixture()
    ledger["schema_version"] = "2.0"
    with pytest.raises(LedgerError, match="invalid value"):
        validate(ledger)
    ledger["schema_version"] = "1.0"
    ledger["sources"][0]["snapshot"] = "../outside"
    with pytest.raises(LedgerError, match="unsafe snapshot"):
        validate(ledger)


def test_confirmed_child_parent_period_cannot_outlive_ended_parent():
    ledger = fixture()
    ledger["units"] = [unit("P", "province"), unit("D", "district")]
    ledger["events"] = [event("end-parent", "abolish", ["P"], [], "2010-01-01")]
    parent = {"id": "parent", "unit_id": "D", "parent_id": "P", "valid_from": "2000-01-01", "valid_to": None,
              "status": "confirmed", "event_id": None, "evidence": EVIDENCE}
    ledger["parents"] = [parent]
    with pytest.raises(LedgerError, match="outlives.*parent"):
        validate(ledger)
    parent["valid_to"] = "2011-01-01"
    with pytest.raises(LedgerError, match="outlives.*parent"):
        validate(ledger)
    parent["valid_to"] = "2010-01-01"
    assert validate(ledger)["valid"]


def test_conflicting_same_day_whole_consumption_rejected():
    ledger = fixture()
    ledger["units"] = [unit(u) for u in "ABCDE"]
    ledger["events"] = [event("one", "merge", ["A", "B"], ["C"], "2010-01-01"),
                        event("two", "merge", ["A", "D"], ["E"], "2010-01-01")]
    with pytest.raises(LedgerError, match="consumed"):
        validate(ledger)


def test_rename_on_abolition_day_rejected_but_own_abolition_is_valid():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["events"] = [event("gone", "abolish", ["A"], [], "2010-01-01")]
    assert validate(ledger)["valid"]
    ledger["events"].append(event("rename", "rename", ["A"], ["A"], "2010-01-01"))
    with pytest.raises(LedgerError, match="abolished"):
        validate(ledger)


def test_merge_output_can_be_existing_unit_without_invented_formation_date():
    ledger = fixture()
    ledger["units"] = [unit(u) for u in "ABC"]
    ledger["names"] = [name("C", "Existing C", "2000-01-01", "2005-01-01"),
                       name("C", "Renamed C", "2005-01-01", event="before-merge")]
    ledger["events"] = [event("before-merge", "rename", ["C"], ["C"], "2005-01-01"),
                        event("merge", "merge", ["A", "B"], ["C"], "2010-01-01")]
    assert validate(ledger)["valid"]
    assert query(ledger, "C", "2001-01-01")["confirmed_name_at_date"][0]["value"] == "Existing C"


def test_pending_edge_cannot_transmit_unrelated_confirmed_history():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    pending = event("pending-ab", "reported_transition", ["A"], ["B"], None)
    pending["status"] = "pending"
    ledger["events"] = [pending, event("verified-b", "rename", ["B"], ["B"], "2000-01-01")]
    assert query(ledger, "A")["chronological_events"] == []
    assert [e["id"] for e in query(ledger, "A")["pending_evidence"]] == ["pending-ab"]
    assert [e["id"] for e in query(ledger, "B")["chronological_events"]] == ["verified-b"]


def test_resolved_mention_exposes_pending_evidence_without_confirming_event():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    mention = {"id": "old-a", "raw_phrase": "Old A", "candidate_names": [], "resolved_unit_id": "A",
               "status": "pending", "evidence": EVIDENCE}
    ledger["mentions"] = [mention]
    pending = event("pending-ab", "reported_transition", [], ["B"], None)
    pending.update(status="pending", **{"from": [{"kind": "mention", "id": "old-a"}]})
    ledger["events"] = [pending, event("verified-b", "rename", ["B"], ["B"], "2000-01-01")]
    assert query(ledger, "A")["pending_evidence"] == []
    mention["status"] = "confirmed"
    answer = query(ledger, "A")
    assert [e["id"] for e in answer["pending_evidence"]] == ["pending-ab"]
    assert answer["chronological_events"] == []
    assert ledger["events"][0]["status"] == "pending"


@pytest.mark.parametrize("day", ["20070101", "2007-W01-1", "2007-1-01", "2007-01-01\n", "２００７-０１-０１"])
def test_query_rejects_noncanonical_date_formats(day):
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "A", "2000-01-01", "2010-01-01")]
    with pytest.raises(LedgerError, match="invalid date"):
        query(ledger, "A", day)


def test_maximum_legal_date_in_open_period_and_overlap_validation():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "A", "9999-12-31")]
    assert query(ledger, "A", "9999-12-31")["date_lookup"] == "confirmed"
    ledger["names"].append(name("A", "B", "9999-12-31"))
    with pytest.raises(LedgerError, match="overlapping"):
        validate(ledger)


@pytest.mark.parametrize("field", ["ma", "ten", "magoc", "malk", "truocsapnhap"])
def test_province_header_all_current_fields_checked_and_ledger_retained(tmp_path, field):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    before = (tmp_path / "ledger.json").read_bytes()
    header, children = tables["01"].decode().split(".synt.", 1)
    header = json.loads(header)
    header[field] = "wrong"
    corrupted = {"01": (json.dumps(header)+".synt."+children).encode()}
    with pytest.raises(LedgerError, match="province"):
        import_bando(tmp_path, raw, "2026-10-04", corrupted, strict=False)
    assert (tmp_path / "ledger.json").read_bytes() == before


def test_interrupted_snapshot_publication_can_retry_without_partial_hash_file(tmp_path):
    raw, tables = bando_fixture()
    with patch("notary_v2.administrative_timeline.os.fsync", side_effect=OSError("interrupted raw write")):
        with pytest.raises(OSError):
            import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    assert not (tmp_path / "ledger.json").exists()
    assert not list((tmp_path / "snapshots").iterdir())
    assert not (tmp_path / ".write.lock").exists()
    assert import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)["valid"]


def test_empty_snapshot_path_gives_validation_error():
    ledger = fixture()
    ledger["sources"][0]["snapshot"] = ""
    with pytest.raises(LedgerError, match="unsafe snapshot"):
        validate(ledger)


def test_machine_schema_patterns_are_anchored_and_match_whole_values():
    import re
    schema = json.loads(SCHEMA.read_text(encoding="utf8"))
    def patterns(node):
        if isinstance(node, dict):
            if "pattern" in node:
                yield node
            for child in node.values():
                yield from patterns(child)
        elif isinstance(node, list):
            for child in node:
                yield from patterns(child)
    constraints = list(patterns(schema))
    assert constraints
    for constraint in constraints:
        pattern = constraint["pattern"]
        valid = "a"*64 if constraint["maxLength"] == 64 else "2000-01-01"
        assert pattern.startswith("^") and pattern.endswith("$")
        assert re.search(pattern, valid)
        assert not re.search(pattern, "x"+valid)
        assert not re.search(pattern, valid+"x")
        assert constraint["minLength"] == constraint["maxLength"]


def test_exclusive_lock_rejects_both_writers_and_releases_after_owner(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    before = (tmp_path / "ledger.json").read_bytes()
    with locked(tmp_path):
        with pytest.raises(LedgerError, match="being written"):
            import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
        with pytest.raises(LedgerError, match="being written"):
            manual_update(tmp_path, {"base_revision": 1, "upsert": {}})
        assert (tmp_path / "ledger.json").read_bytes() == before
    assert not (tmp_path / ".write.lock").exists()
    assert manual_update(tmp_path, {"base_revision": 1, "upsert": {}})["valid"]


def test_query_only_exposes_observations_of_current_dataset(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    uid = next(u["id"] for u in ledger["units"] if u["source_key"] == "commune:test")
    old_dataset = ledger["dataset_version"]
    rows = json.loads(raw)
    rows[1]["ten"] = "Xã Changed"
    changed_raw = json.dumps(rows).encode()
    changed_tables = {"01": (json.dumps(rows[0])+".synt."+json.dumps(rows[1:])).encode()}
    import_bando(tmp_path, changed_raw, "2026-10-05", changed_tables, strict=False)
    ledger = read_ledger(tmp_path)
    answer = query(ledger, uid)
    assert len(answer["current_source_observations"]) == 1
    assert answer["current_source_observations"][0]["details"]["ten"] == "Xã Changed"
    assert answer["current_source_observations"][0]["dataset_version"] != old_dataset
    assert any(o["dataset_version"] == old_dataset for o in ledger["observations"])


def test_confirmed_partial_reciprocal_transfers_preserve_both_identities():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["names"] = [name("A", "A", "2000-01-01"), name("B", "B", "2000-01-01")]
    ledger["events"] = [event("part-ab", "reported_transition", ["A"], ["B"], "2010-01-01"),
                        event("part-ba", "reported_transition", ["B"], ["A"], "2020-01-01")]
    for change in ledger["events"]:
        change["territory"] = "partial"
    assert validate(ledger)["valid"]
    assert query(ledger, "A", "2021-01-01")["confirmed_name_at_date"][0]["value"] == "A"
    assert query(ledger, "B", "2021-01-01")["confirmed_name_at_date"][0]["value"] == "B"
    assert len(query(ledger, "A")["chronological_events"]) == 2
    for change in ledger["events"]:
        change["territory"] = "whole"
    with pytest.raises(LedgerError, match="cycle"):
        validate(ledger)


def test_unlinked_name_period_spanning_confirmed_rename_is_rejected():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "Old", "2000-01-01")]
    ledger["events"] = [event("renamed", "rename", ["A"], ["A"], "2010-01-01")]
    with pytest.raises(LedgerError, match="spans confirmed rename"):
        validate(ledger)
    ledger["names"][0]["valid_to"] = "2010-01-01"
    ledger["names"].append(name("A", "New", "2010-01-01"))
    assert query(ledger, "A", "2009-12-31")["confirmed_name_at_date"][0]["value"] == "Old"
    assert query(ledger, "A", "2010-01-01")["confirmed_name_at_date"][0]["value"] == "New"


def test_whole_reported_transition_ends_absent_input_and_rejects_future_activity():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["events"] = [event("whole-ab", "reported_transition", ["A"], ["B"], "2010-01-01")]
    ledger["names"] = [name("A", "Old", "2000-01-01")]
    with pytest.raises(LedgerError, match="outlives"):
        validate(ledger)
    ledger["names"][0]["valid_to"] = "2010-01-01"
    assert validate(ledger)["valid"]
    ledger["events"].append(event("late", "rename", ["A"], ["A"], "2020-01-01"))
    with pytest.raises(LedgerError, match="consumed"):
        validate(ledger)


def test_manual_same_id_corrections_retain_exact_prior_revisions(tmp_path):
    import gzip
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "Typo", "2000-01-01")]
    atomic_write(tmp_path, ledger)
    first_bytes = (tmp_path / "ledger.json").read_bytes()
    corrected = dict(ledger["names"][0], value="Corrected")
    manual_update(tmp_path, {"base_revision": 0, "upsert": {"names": [corrected]}})
    archives = list((tmp_path / "revisions").glob("*.json.gz"))
    assert len(archives) == 1
    archive_bytes = archives[0].read_bytes()
    assert gzip.decompress(archive_bytes) == first_bytes
    assert json.loads(gzip.decompress(archive_bytes))["names"][0]["value"] == "Typo"
    second_bytes = (tmp_path / "ledger.json").read_bytes()
    manual_update(tmp_path, {"base_revision": 1, "upsert": {"names": [dict(corrected, value="Final correction")]}})
    assert archives[0].read_bytes() == archive_bytes
    assert {gzip.decompress(p.read_bytes()) for p in (tmp_path / "revisions").glob("*.json.gz")} == {first_bytes, second_bytes}
    assert read_ledger(tmp_path)["names"][0]["value"] == "Final correction"


def test_archive_failure_aborts_curation_and_retry_preserves_prior_bytes(tmp_path):
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "Old", "2000-01-01")]
    atomic_write(tmp_path, ledger)
    before = (tmp_path / "ledger.json").read_bytes()
    update = {"base_revision": 0, "upsert": {"names": [dict(ledger["names"][0], value="Correction")]}}
    with patch("notary_v2.administrative_timeline.atomic_snapshot", side_effect=OSError("archive disk failure")):
        with pytest.raises(OSError, match="archive"):
            manual_update(tmp_path, update)
    assert (tmp_path / "ledger.json").read_bytes() == before
    assert not (tmp_path / ".write.lock").exists()
    assert not list((tmp_path / "revisions").glob("*.json.gz"))
    assert manual_update(tmp_path, update)["valid"]


def test_source_key_cannot_move_across_levels_on_refresh(tmp_path):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    before = (tmp_path / "ledger.json").read_bytes()
    rows = json.loads(raw)
    rows[0]["malk"] = "commune:test"
    rows[1]["malk"] = "commune:new"
    altered_raw = json.dumps(rows).encode()
    altered_tables = {"01": (json.dumps(rows[0])+".synt."+json.dumps(rows[1:])).encode()}
    with pytest.raises(LedgerError, match="across administrative levels"):
        import_bando(tmp_path, altered_raw, "2026-10-05", altered_tables, strict=False)
    assert (tmp_path / "ledger.json").read_bytes() == before


@pytest.mark.parametrize("value", [None, [], 1, "patch", ["base_revision", "upsert"]])
def test_non_object_patch_gives_ledger_error_without_creating_store(tmp_path, value):
    with pytest.raises(LedgerError, match="requires base_revision"):
        manual_update(tmp_path, value)
    assert not (tmp_path / "ledger.json").exists()


def test_missing_stored_ledger_does_not_look_like_valid_empty_store(tmp_path):
    with pytest.raises(LedgerError, match="stored ledger missing"):
        read_ledger(tmp_path)
    with pytest.raises(LedgerError, match="stored ledger missing"):
        manual_update(tmp_path, {"base_revision": 0, "upsert": {}})
    assert read_ledger(tmp_path, initialize=True) == empty_ledger()


def test_default_strict_full_import_and_partial_rejection_preserve_store(tmp_path):
    ledger = read_ledger(DEFAULT_FOLDER)
    catalog_source = next(s for s in ledger["sources"] if s["request_body"] == "ma=0")
    raw = (DEFAULT_FOLDER / catalog_source["snapshot"]).read_bytes()
    sources = {s["request_body"]: s for s in ledger["sources"]}
    tables = {r["ma"]: (DEFAULT_FOLDER / sources["ma="+r["malk"]]["snapshot"]).read_bytes()
              for r in json.loads(raw) if r["magoc"] == "0"}
    result = import_bando(tmp_path, raw, "2026-10-04", tables)
    assert result["units"] == 3355
    assert read_ledger(tmp_path)["units"] == ledger["units"]
    assert read_ledger(tmp_path)["observations"] == ledger["observations"]
    before = (tmp_path / "ledger.json").read_bytes()
    partial_raw, partial_tables = bando_fixture()
    with pytest.raises(LedgerError, match="full catalog"):
        import_bando(tmp_path, partial_raw, "2026-10-04", partial_tables)
    assert (tmp_path / "ledger.json").read_bytes() == before
    assert len(list((tmp_path / "snapshots").glob("*.raw"))) == 35


def test_assertion_confidence_does_not_promote_pending_event():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["mentions"] = [{"id": "unknown", "raw_phrase": "Unknown predecessor", "candidate_names": [],
                           "resolved_unit_id": None, "status": "pending", "evidence": EVIDENCE}]
    pending = event("pending", "reported_transition", [], ["A"], None)
    pending.update(status="pending", **{"from": [{"kind": "mention", "id": "unknown"}]})
    ledger["events"] = [pending]
    ledger["names"] = [name("A", "Known name", "2000-01-01", event="pending")]
    answer = query(ledger, "A", "2001-01-01")
    assert answer["date_lookup"] == "confirmed"
    assert answer["chronological_events"] == []
    assert answer["pending_evidence"][0]["status"] == "pending"


def test_actual_cli_update_query_date_boundary_and_errors(tmp_path):
    import re
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[2]
    text = (root / "_bmad-output/specs/notary_v2/administrative-timeline.md").read_text(encoding="utf8")
    example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
    ledger = empty_ledger()
    ledger["revision"] = example["base_revision"]
    atomic_write(tmp_path, ledger)
    patch_file = tmp_path / "patch.json"
    patch_file.write_text(json.dumps(example), encoding="utf8")
    def cli(*args, folder=tmp_path):
        return subprocess.run([sys.executable, "-X", "utf8", "-m", "notary_v2.administrative_timeline",
                               "--folder", str(folder), *args], cwd=root, capture_output=True, text=True, encoding="utf8")
    result = cli("update", str(patch_file))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"]
    for day, expected in (("2004-12-31", "A"), ("2005-01-01", "B")):
        result = cli("query", "owner:demo", "--as-on", day)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["confirmed_name_at_date"][0]["value"] == expected
    bad_date = cli("query", "owner:demo", "--as-on", "20050101")
    assert bad_date.returncode == 2 and "invalid date" in bad_date.stderr
    missing = cli("validate", folder=tmp_path / "missing")
    assert missing.returncode == 2 and "stored ledger missing" in missing.stderr
    patch_file.write_text("null", encoding="utf8")
    invalid = cli("update", str(patch_file))
    assert invalid.returncode == 2 and "requires base_revision" in invalid.stderr
    assert "Traceback" not in invalid.stderr


def test_continuing_identity_split_then_merge_is_not_false_successor_chain():
    ledger = fixture()
    ledger["units"] = [unit(u) for u in "ABC"]
    ledger["events"] = [event("retain-b-split", "split", ["B"], ["B", "C"], "2010-01-01"),
                        event("retain-b-merge", "merge", ["A", "B"], ["B"], "2020-01-01")]
    assert validate(ledger)["valid"]
    assert len(query(ledger, "B")["chronological_events"]) == 2


def test_unknown_territory_does_not_assert_whole_succession():
    ledger = fixture()
    ledger["units"] = [unit("A"), unit("B")]
    ledger["events"] = [event("unknown-ab", "reported_transition", ["A"], ["B"], "2010-01-01"),
                        event("unknown-ba", "reported_transition", ["B"], ["A"], "2020-01-01")]
    for change in ledger["events"]:
        change["territory"] = "unknown"
    assert validate(ledger)["valid"]


def test_reparent_rejects_old_parent_period_spanning_change_date():
    ledger = fixture()
    ledger["units"] = [unit("D", "district"), unit("P1", "province"), unit("P2", "province")]
    ledger["events"] = [event("move", "reparent", ["D"], ["D"], "2010-01-01")]
    ledger["parents"] = [{"id": "parent:old", "unit_id": "D", "parent_id": "P1", "valid_from": "2000-01-01",
                          "valid_to": None, "status": "confirmed", "event_id": None, "evidence": EVIDENCE}]
    with pytest.raises(LedgerError, match="spans confirmed reparent"):
        validate(ledger)
    ledger["parents"][0]["valid_to"] = "2010-01-01"
    ledger["parents"].append(dict(ledger["parents"][0], id="parent:new", parent_id="P2", valid_from="2010-01-01",
                                  valid_to=None, event_id="move"))
    assert validate(ledger)["valid"]


@pytest.mark.parametrize("territory", ["partial", "unknown"])
def test_abolition_must_be_confirmed_whole_termination(territory):
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["events"] = [dict(event("end", "abolish", ["A"], [], "2010-01-01"), territory=territory)]
    with pytest.raises(LedgerError, match="invalid abolition"):
        validate(ledger)
    ledger["events"][0]["status"] = "pending"
    assert validate(ledger)["valid"]


def test_confirmed_reported_transition_requires_destination():
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["events"] = [event("missing-to", "reported_transition", ["A"], [], "2010-01-01")]
    with pytest.raises(LedgerError, match="requires both sides"):
        validate(ledger)
    ledger["events"][0]["status"] = "pending"
    assert validate(ledger)["valid"]


@pytest.mark.parametrize("damage", ["corrupt", "missing"])
def test_actual_cli_query_checks_supporting_snapshots(tmp_path, damage):
    import subprocess
    import sys
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    snapshot = tmp_path / ledger["sources"][0]["snapshot"]
    if damage == "corrupt":
        snapshot.write_bytes(b"damaged")
    else:
        snapshot.unlink()
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, "-X", "utf8", "-m", "notary_v2.administrative_timeline",
                             "--folder", str(tmp_path), "query", ledger["units"][0]["id"]],
                            cwd=root, capture_output=True, text=True, encoding="utf8")
    assert result.returncode == 2
    assert "snapshot missing/hash mismatch" in result.stderr
    assert result.stdout == ""


def test_duplicate_ids_in_patch_rejected_before_mutation_or_archive(tmp_path):
    ledger = fixture()
    ledger["units"] = [unit("A")]
    ledger["names"] = [name("A", "A", "2000-01-01")]
    atomic_write(tmp_path, ledger)
    prior = (tmp_path / "ledger.json").read_bytes()
    original = ledger["names"][0]
    with pytest.raises(LedgerError, match="duplicate upsert id"):
        manual_update(tmp_path, {"base_revision": 0, "upsert": {"names": [dict(original, value="First"), dict(original, value="Last")]}})
    assert (tmp_path / "ledger.json").read_bytes() == prior
    assert not (tmp_path / "revisions").exists()


def test_separate_curator_conclusion_citing_bando_can_be_corrected_with_archive(tmp_path):
    import gzip
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    imported_name = deepcopy(ledger["names"][0])
    curated = dict(imported_name, id="owner:separate-conclusion", value="Curator conclusion")
    manual_update(tmp_path, {"base_revision": 1, "upsert": {"names": [curated]}})
    before = (tmp_path / "ledger.json").read_bytes()
    manual_update(tmp_path, {"base_revision": 2, "upsert": {"names": [dict(curated, value="Corrected curator conclusion")]}})
    after = read_ledger(tmp_path)
    assert next(r for r in after["names"] if r["id"] == imported_name["id"]) == imported_name
    assert next(r for r in after["names"] if r["id"] == curated["id"])["value"] == "Corrected curator conclusion"
    assert before in [gzip.decompress(p.read_bytes()) for p in (tmp_path / "revisions").glob("*.json.gz")]


@pytest.mark.parametrize("counterfeit", ["observation", "generated-name", "source-key", "source-id"])
def test_manual_counterfeit_importer_records_rejected(tmp_path, counterfeit):
    raw, tables = bando_fixture()
    import_bando(tmp_path, raw, "2026-10-04", tables, strict=False)
    ledger = read_ledger(tmp_path)
    prior = (tmp_path / "ledger.json").read_bytes()
    if counterfeit == "observation":
        key, row = "observations", dict(ledger["observations"][0], id="owner:fake-observation")
    elif counterfeit == "generated-name":
        key, row = "names", dict(ledger["names"][0], id="name:"+"0"*16+":unit:bando:fake")
    elif counterfeit == "source-key":
        key, row = "units", dict(ledger["units"][0], id="owner:fake-unit", source_key="new-source-key")
    else:
        key, row = "sources", dict(fixture()["sources"][0], id="bando:counterfeit")
    with pytest.raises(LedgerError, match="reserved importer"):
        manual_update(tmp_path, {"base_revision": 1, "upsert": {key: [row]}})
    assert (tmp_path / "ledger.json").read_bytes() == prior


def test_refresh_main_real_http_post_wiring_full_source_and_download_failure(tmp_path, capsys):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    from urllib.parse import parse_qs
    from notary_v2 import administrative_timeline as module
    ledger = read_ledger(DEFAULT_FOLDER)
    catalog = next(s for s in ledger["sources"] if s["request_body"] == "ma=0")
    responses = {("/p.co_dvhc", "0"): (DEFAULT_FOLDER / catalog["snapshot"]).read_bytes()}
    for source in ledger["sources"]:
        if source["request_body"] != "ma=0":
            responses[("/p.co_bangbieu", source["request_body"][3:])] = (DEFAULT_FOLDER / source["snapshot"]).read_bytes()
    requests, state = [], {"fail": False}
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            form = parse_qs(raw.decode())
            requests.append((self.path, form, self.headers["Content-Type"]))
            if state["fail"] and self.path == "/p.co_bangbieu":
                self.send_error(503)
                return
            content = responses[(self.path, form["ma"][0])]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(content)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with patch.object(module, "BASE_URL", base_url), patch("sys.argv", ["timeline", "--folder", str(tmp_path), "refresh-bando"]):
            module.main()
            assert json.loads(capsys.readouterr().out)["units"] == 3355
            assert {(path, form["ma"][0]) for path, form, _ in requests} == responses.keys()
            assert len(requests) == 35
            assert all(content_type == "application/x-www-form-urlencoded" for _, _, content_type in requests)
            stored = read_ledger(tmp_path)
            assert all(s["url"].startswith(base_url) and s["protocol"] == "HTTPS POST" for s in stored["sources"])
            assert validate(stored, tmp_path)["valid"]
            before = (tmp_path / "ledger.json").read_bytes()
            state["fail"] = True
            with pytest.raises(SystemExit) as exit_info:
                module.main()
            assert exit_info.value.code == 2
            assert "503" in capsys.readouterr().err
            assert (tmp_path / "ledger.json").read_bytes() == before
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
