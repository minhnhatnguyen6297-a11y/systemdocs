"""WP2 slot table: authoritative engine and sidecar mock use identical requests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from services.inheritance_engine import run_inheritance_case

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shell" / "sidecar"))
from notary_mock_adapter import _required_slots


def evaluate(deaths, *, parents=None, spouses=None, records=None):
    parents, spouses = parents or {}, spouses or {}
    nodes = [{
        "id": f"slot_{pid}", "personId": pid,
        "parentSlotIds": [f"slot_{parent}" for parent in parents.get(pid, [])],
        "spouseSlotIds": [f"slot_{spouse}" for spouse in spouses.get(pid, [])],
        "isLandOwner": pid == "A", "willReceive": True,
        "ownPositions": [1] if pid == "A" else [], "receivePositions": [1],
    } for pid in deaths]
    people = {pid: {"row_id": pid, "ngay_chet": death, **(records or {}).get(pid, {})}
              for pid, death in deaths.items()}
    result = run_inheritance_case({"version": 2, "nodes": nodes}, people)
    mock = _required_slots(nodes, {"people": list(people.values())})
    assert mock == result["requiredSlots"]
    return result


@pytest.mark.parametrize("owner_death,person_death,roles,reason", [
    (None, None, ["spouse"], "living_owner"),
    ("2020", None, ["father", "mother", "spouse", "child"], "active_estate"),
    ("2020", "2021", ["father", "mother", "spouse", "child"], "active_estate"),
    ("2020", "2001", ["child"], "representation_branch"),
    ("2020", None, [], None),
], ids=["living-owner", "dead-owner", "transfer", "representation", "living-non-owner"])
def test_five_slot_table_rows_match_real_and_mock(owner_death, person_death, roles, reason, request):
    target = "A" if request.node.callspec.id in ("living-owner", "dead-owner") else "C"
    result = evaluate({"A": owner_death, "C": person_death}, parents={"C": ["A"]})
    requirements = [r for r in result["requiredSlots"] if r["anchorSlotId"] == f"slot_{target}"]
    if not roles:
        assert requirements == []
        return
    requirement, = requirements
    assert requirement["reason"] == reason
    assert requirement["slotTypes"] == roles
    assert requirement["minimumEmptyChildSlots"] == int("child" in roles)
    assert requirement["minimumEmptySpouseSlots"] == int("spouse" in roles)
    for role in roles:
        assert [slot["ordinal"] for slot in requirement["slots"] if slot["role"] == role] == (
            [0, 1] if role in ("spouse", "child") else [0])


def test_owner_wife_predeceased_son_and_living_daughter_scenario():
    result = evaluate(
        {"A": "2020", "B": "1997", "C": "2001", "D": None},
        parents={"C": ["A", "B"], "D": ["A", "B"]}, spouses={"A": ["B"]},
        records={"A": {"ngay_sinh": "1950"}, "B": {"ngay_sinh": "1955"},
                 "C": {"ngay_sinh": "1975"}, "D": {"ngay_sinh": "1977"}},
    )
    by_anchor = {r["anchorSlotId"]: r for r in result["requiredSlots"]}
    assert set(by_anchor) == {"slot_A", "slot_C"}
    assert by_anchor["slot_A"]["slotTypes"] == ["father", "mother", "spouse", "child"]
    assert by_anchor["slot_C"]["slotTypes"] == ["child"]
    assert [s["role"] for s in by_anchor["slot_A"]["slots"]].count("child") == 3
    assert [s["role"] for s in by_anchor["slot_A"]["slots"]].count("spouse") == 2


def test_representation_stops_spawning_at_great_grandchild():
    result = evaluate({"A": "2020", "C": "2001", "G": "2002", "H": "2003"},
                      parents={"C": ["A"], "G": ["C"], "H": ["G"]})
    representations = [r for r in result["requiredSlots"] if r["reason"] == "representation_branch"]
    assert {r["anchorSlotId"] for r in representations} == {"slot_C", "slot_G"}
    assert all(r["slotTypes"] == ["child"] for r in representations)


@pytest.mark.parametrize("owner_death,death,certificate", [
    ("2020", None, True),
    ("2020", "2020", False),
    ("2020", "2020-06-01", False),
    ("2020-06-01", "2020", False),
    (None, "2001", False),
])
def test_q1_incomparable_death_dates_have_no_slots_and_person_status(owner_death, death, certificate):
    records = {"C": {"loai_giay_to": "Giấy chứng tử"}} if certificate else {}
    if owner_death is None:
        records["A"] = {"loai_giay_to": "Giấy chứng tử"}
    result = evaluate({"A": owner_death, "C": death}, parents={"C": ["A"]}, records=records)
    assert all(r["anchorSlotId"] != "slot_C" for r in result["requiredSlots"])
    expected = "A" if owner_death is None else "C"
    assert {"code": "missing_death_date", "message": "thiếu ngày mất",
            "personId": expected, "anchorSlotId": f"slot_{expected}"} in result["warnings"]
    if owner_death is None:
        assert result["requiredSlots"] == []


def test_slot_ids_stable_across_evaluations_and_spare_growth():
    args = {"parents": {"C": ["A"]}, "spouses": {"A": ["B"]}}
    deaths = {"A": "2020", "B": None, "C": None}
    first = evaluate(deaths, **args)["requiredSlots"]
    assert first == evaluate(deaths, **args)["requiredSlots"]
    expanded = evaluate({**deaths, "D": None, "E": None, "F": None},
                        parents={"C": ["A"], "D": ["A"], "E": ["A"]},
                        spouses={"A": ["B", "F"]})["requiredSlots"]
    old_ids = {(s["role"], s["ordinal"]): s["id"] for s in first[0]["slots"]}
    new_ids = {(s["role"], s["ordinal"]): s["id"] for s in expanded[0]["slots"]}
    assert all(new_ids[key] == value for key, value in old_ids.items())
    assert len(set(new_ids.values())) == len(new_ids)
    assert [s["role"] for s in expanded[0]["slots"]].count("child") == 4
    assert [s["role"] for s in expanded[0]["slots"]].count("spouse") == 3


@pytest.mark.parametrize("death", [None, "2020"], ids=["missing", "overlapping-year"])
def test_mock_render_preserves_q1_card_warning(death):
    from notary_mock_adapter import _render

    nodes = [
        {"id": "A", "personId": "A", "ownPositions": [1]},
        {"id": "C", "personId": "C", "parentSlotIds": ["A"]},
    ]
    stage = {"people": [
        {"row_id": "A", "ngay_chet": "2020"},
        {"row_id": "C", "ngay_chet": death, "loai_giay_to": "Giấy chứng tử"},
    ]}
    result = _render({"nodes": nodes}, stage)
    assert {r["anchorSlotId"] for r in result["requiredSlots"]} == {"A"}
    assert any(w["code"] == "missing_death_date" and w.get("personId") == "C"
               for w in result["warnings"])


def test_mock_render_retains_tombstone_references_for_slot_generation():
    from notary_mock_adapter import _render

    nodes = [
        {"id": "A", "personId": "A", "ownPositions": [1],
         "spouseSlotIds": ["old"]},
        {"id": "old", "personId": "B", "deleted": True},
    ]
    people = {"A": {"row_id": "A", "ngay_chet": "2020"},
              "B": {"row_id": "B", "ngay_chet": None}}
    real = run_inheritance_case(
        {"version": 2, "nodes": [{**node, "isLandOwner": bool(node.get("ownPositions"))}
                                  for node in nodes]}, people)
    mock = _render({"nodes": nodes}, {"people": list(people.values())})
    assert mock["requiredSlots"] == real["requiredSlots"]
    requirement, = mock["requiredSlots"]
    assert requirement["slotTypes"] == ["father", "mother", "spouse", "child"]
