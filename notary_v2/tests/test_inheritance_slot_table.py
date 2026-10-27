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
    # Rule B: the transfer child links to the existing owner pair, so no
    # new Cha/Mẹ slots; its own spouse group and Con group are new.
    ("2020", "2021", ["spouse", "child"], "active_estate"),
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
    (None, "2001", False),
], ids=["child-certificate-without-date", "owner-certificate-without-date"])
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
    # Pair A+B keeps 3 children + spare; spouse F in the spare slot gets its
    # own pair group (minimum two Con slots) and a new spare spouse slot.
    assert [s["ordinal"] for s in expanded[0]["slots"] if s["role"] == "child"] == [0, 1, 2, 3, 4, 5]
    assert [s["ordinal"] for s in expanded[0]["slots"] if s["role"] == "spouse"] == [0, 1, 2]


def test_mock_render_preserves_q1_card_warning():
    from notary_mock_adapter import _render

    nodes = [
        {"id": "A", "personId": "A", "ownPositions": [1]},
        {"id": "C", "personId": "C", "parentSlotIds": ["A"]},
    ]
    stage = {"people": [
        {"row_id": "A", "ngay_chet": "2020"},
        {"row_id": "C", "ngay_chet": None, "loai_giay_to": "Giấy chứng tử"},
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


def _requirement(result, anchor):
    requirement, = [r for r in result["requiredSlots"] if r["anchorSlotId"] == anchor]
    return requirement


def _role_ordinals(requirement, role):
    return [s["ordinal"] for s in requirement["slots"] if s["role"] == role]


def test_con_slots_belong_to_pair_and_each_spouse_gets_its_own_group():
    """Rule A: Con slots are per pair (person + spouse slot n); each further
    spouse placed in the spare slot gets its own Con group + a new spare."""
    result = evaluate(
        {"A": "2020", "B": None, "F": None, "C": None, "D": None},
        parents={"C": ["A", "B"], "D": ["A", "B"]},
        spouses={"A": ["B", "F"]},
    )
    requirement = _requirement(result, "slot_A")
    assert _role_ordinals(requirement, "spouse") == [0, 1, 2]
    # pair A+B: two children + one spare = 3; pair A+F: no child + spare = 2.
    assert _role_ordinals(requirement, "child") == [0, 1, 2, 3, 4]


def test_each_filled_con_slot_respawns_a_spare():
    base = {"A": "2020", "B": None, "C": None}
    one_child = evaluate(base, parents={"C": ["A", "B"]}, spouses={"A": ["B"]})
    two_children = evaluate({**base, "D": None},
                            parents={"C": ["A", "B"], "D": ["A", "B"]},
                            spouses={"A": ["B"]})
    assert _role_ordinals(_requirement(one_child, "slot_A"), "child") == [0, 1]
    assert _role_ordinals(_requirement(two_children, "slot_A"), "child") == [0, 1, 2]


def test_child_dead_after_owner_links_to_existing_pair_without_new_parents():
    """Rule B: no new Cha/Mẹ for a transfer child; shared Con slots stay
    with the owner pair."""
    result = evaluate(
        {"A": "2020", "B": None, "C": "2021", "D": None},
        parents={"C": ["A", "B"], "D": ["A", "B"]},
        spouses={"A": ["B"]},
    )
    by_anchor = {r["anchorSlotId"]: r for r in result["requiredSlots"]}
    assert set(by_anchor) == {"slot_A", "slot_C"}
    transfer = by_anchor["slot_C"]
    assert transfer["reason"] == "active_estate"
    assert transfer["slotTypes"] == ["spouse", "child"]
    assert all(s["role"] not in ("father", "mother") for s in transfer["slots"])
    assert _role_ordinals(by_anchor["slot_A"], "child") == [0, 1, 2]


def test_spouse_dead_after_owner_gets_parents_without_duplicate_pair_slots():
    """Rule C: her shared children stay under the owner pair; her spouse is
    the placed owner, so no new spouse slot."""
    result = evaluate(
        {"A": "2020", "B": "2021", "C": None},
        parents={"C": ["A", "B"]}, spouses={"A": ["B"]},
    )
    by_anchor = {r["anchorSlotId"]: r for r in result["requiredSlots"]}
    assert set(by_anchor) == {"slot_A", "slot_B"}
    spouse = by_anchor["slot_B"]
    assert spouse["reason"] == "active_estate"
    assert spouse["slotTypes"] == ["father", "mother"]
    assert all(s["role"] not in ("spouse", "child") for s in spouse["slots"])
    assert _role_ordinals(by_anchor["slot_A"], "child") == [0, 1]


def test_spouse_dead_before_owner_has_no_slots():
    """Rule I: Điều 652 BLDS 2015 — the predeceased spouse is not an heir."""
    result = evaluate(
        {"A": "2020", "B": "1990", "C": None},
        parents={"C": ["A", "B"]}, spouses={"A": ["B"]},
    )
    assert {r["anchorSlotId"] for r in result["requiredSlots"]} == {"slot_A"}
    assert result["warnings"] == []


def test_living_owner_spawns_only_the_spouse_group():
    result = evaluate({"A": None, "C": None}, parents={"C": ["A"]})
    requirement, = result["requiredSlots"]
    assert requirement["reason"] == "living_owner"
    assert requirement["slotTypes"] == ["spouse"]
    assert _role_ordinals(requirement, "spouse") == [0, 1]


def test_year_only_death_is_first_of_january_when_ordering():
    """Rule F: '2020' is 01/01/2020, not the whole year."""
    child_before = evaluate({"A": "01/06/2020", "C": "2020"},
                            parents={"C": ["A"]})
    requirement = _requirement(child_before, "slot_C")
    assert requirement["reason"] == "representation_branch"
    assert requirement["slotTypes"] == ["child"]
    assert child_before["warnings"] == []

    child_after = evaluate({"A": "2020", "C": "01/06/2020"},
                           parents={"C": ["A"]})
    requirement = _requirement(child_after, "slot_C")
    assert requirement["reason"] == "active_estate"
    assert requirement["slotTypes"] == ["spouse", "child"]
    assert child_after["warnings"] == []

    same_day = evaluate({"A": "2020", "C": "2020"}, parents={"C": ["A"]})
    assert _requirement(same_day, "slot_C")["reason"] == "representation_branch"


def test_predeceased_person_only_spawns_con_slots_up_to_great_grandchild():
    result = evaluate({"A": "2020", "C": "2001", "G": "2002", "H": "2003"},
                      parents={"C": ["A"], "G": ["C"], "H": ["G"]})
    by_anchor = {r["anchorSlotId"]: r for r in result["requiredSlots"]}
    assert by_anchor["slot_C"]["reason"] == "representation_branch"
    assert by_anchor["slot_G"]["reason"] == "representation_branch"
    assert "slot_H" not in by_anchor
    for anchor in ("slot_C", "slot_G"):
        assert by_anchor[anchor]["slotTypes"] == ["child"]
        assert all(s["role"] == "child" for s in by_anchor[anchor]["slots"])


def test_symmetric_spouse_pair_keeps_the_only_con_group_on_the_owner():
    """Rule C with a pair declared on both nodes (legacy shape): the spouse
    slot node does not spawn its own Cha/Mẹ-free Con group."""
    nodes = [
        {"id": "owner", "personId": "A", "parentSlotIds": [],
         "spouseSlotIds": ["spouse"], "isLandOwner": True, "willReceive": True,
         "ownPositions": [1], "receivePositions": []},
        {"id": "spouse", "personId": "B", "parentSlotIds": [],
         "spouseSlotIds": ["owner"], "isLandOwner": False, "willReceive": True,
         "ownPositions": [], "receivePositions": [1]},
        {"id": "child", "personId": "C", "parentSlotIds": ["owner", "spouse"],
         "spouseSlotIds": [], "isLandOwner": False, "willReceive": True,
         "ownPositions": [], "receivePositions": [1]},
    ]
    people = {"A": {"row_id": "A", "ngay_chet": "2020"},
              "B": {"row_id": "B", "ngay_chet": "2021"},
              "C": {"row_id": "C", "ngay_chet": None}}
    result = run_inheritance_case({"version": 2, "nodes": nodes}, people)
    by_anchor = {r["anchorSlotId"]: r for r in result["requiredSlots"]}
    assert set(by_anchor) == {"owner", "spouse"}
    assert by_anchor["spouse"]["slotTypes"] == ["father", "mother"]
    assert _role_ordinals(by_anchor["owner"], "child") == [0, 1]
