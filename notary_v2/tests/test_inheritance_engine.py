from __future__ import annotations

from datetime import date
from fractions import Fraction

import pytest

from services.inheritance_engine import _parse_death_date, run_inheritance_case


@pytest.fixture
def later_lines(monkeypatch):
    monkeypatch.setattr("services.inheritance_engine.ENABLE_LATER_LINES", True)


def _run(
    deaths: dict[str, str | None],
    *,
    parents: dict[str, list[str]] | None = None,
    spouses: list[tuple[str, str]] | None = None,
    owners: set[str] | None = None,
    receive: dict[str, bool] | None = None,
):
    parents = parents or {}
    owners = owners or set()
    receive = receive or {}
    spouse_by_person: dict[str, str] = {}
    for left, right in spouses or []:
        spouse_by_person[left] = right
        spouse_by_person[right] = left

    nodes = [
        {
            "id": f"slot_{person_id}",
            "personId": person_id,
            "parentSlotIds": [f"slot_{parent_id}" for parent_id in parents.get(person_id, [])],
            "spouseSlotId": f"slot_{spouse_by_person[person_id]}" if person_id in spouse_by_person else None,
            "isLandOwner": person_id in owners,
            "willReceive": receive.get(person_id, True),
            "hidden": False,
            "deleted": False,
        }
        for person_id in deaths
    ]
    people = {person_id: {"ngay_chet": death} for person_id, death in deaths.items()}
    return run_inheritance_case({"version": 2, "nodes": nodes}, people)


def _share(result, person_id: str) -> Fraction:
    return Fraction(result["allocations"][person_id]["finalShare"])


@pytest.mark.parametrize("recipient", ["S", "N"], ids=["rank-two", "rank-three"])
def test_later_lines_disabled_keeps_only_first_line_slots_and_no_later_shares(recipient):
    result = _run(
        {"X": "2020", "P": "1980", "S": None if recipient == "S" else "2000", "N": None},
        parents={"X": ["P"], "S": ["P"], "N": ["S"]},
        owners={"X"},
    )

    assert result["status"] == "unsupported"
    assert result["errors"][0]["code"] == "second_order_required"
    assert _share(result, "S") == _share(result, "N") == 0
    assert result["breakdowns"] == []
    requirement, = result["requiredSlots"]
    assert requirement["anchorSlotId"] == "slot_X"
    assert requirement["reason"] == "active_estate"
    assert requirement["slotTypes"] == ["father", "mother", "spouse", "child"]
    assert result["conservation"] == {"allocated": "0", "unresolved": "1", "total": "1"}


def test_fixture_x_y_d_z_matches_exact_expected_fractions():
    result = _run(
        {
            "A": "1995",
            "B": "1996",
            "C": "1997",
            "D": "2016",
            "X": "2011",
            "Y": "2015",
            "Z": "2015",
            "M": None,
            "N": None,
            "O": None,
            "Z2": None,
            "Z3": None,
        },
        parents={
            "X": ["A", "B"],
            "Y": ["C", "D"],
            "Z": ["C", "D"],
            "M": ["X", "Y"],
            "N": ["X", "Y"],
            "O": ["X", "Y"],
            "Z2": ["Z"],
            "Z3": ["Z"],
        },
        spouses=[("A", "B"), ("C", "D"), ("X", "Y")],
        owners={"X", "Y"},
    )

    assert result["status"] == "complete"
    assert [_share(result, person_id) for person_id in ("M", "N", "O")] == [Fraction(59, 192)] * 3
    assert [_share(result, person_id) for person_id in ("Z2", "Z3")] == [Fraction(5, 128)] * 2
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


def test_representation_splits_by_branch_at_each_generation_not_flat_descendants():
    result = _run(
        {"X": "2020", "B": None, "Q": "2010", "A": "2009", "D": "2008", "C": None, "E": None, "F": None},
        parents={
            "B": ["X"],
            "Q": ["X"],
            "A": ["Q"],
            "D": ["Q"],
            "C": ["A"],
            "E": ["D"],
            "F": ["D"],
        },
        owners={"X"},
    )

    assert _share(result, "B") == Fraction(1, 2)
    assert _share(result, "C") == Fraction(1, 4)
    assert _share(result, "E") == _share(result, "F") == Fraction(1, 8)
    for breakdown in result["breakdowns"]:
        for term in breakdown["terms"]:
            assert term["heirRank"] == 1
            assert "relationshipRoles" not in term
    e_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "E")
    assert e_terms[0]["kind"] == "representation"
    assert e_terms[0]["viaBranchPersonIds"] == ["Q", "D"]



def test_representation_at_great_grandchild_depth_remains_supported():
    result = _run(
        {"X": "2020", "A": "2010", "B": "2011", "C": None},
        parents={"A": ["X"], "B": ["A"], "C": ["B"]},
        owners={"X"},
    )
    assert result["status"] == "complete"
    assert _share(result, "C") == 1


def test_representation_beyond_great_grandchild_returns_unsupported_without_shares():
    result = _run(
        {"X": "2020", "A": "2010", "B": "2011", "C": "2012", "D": None},
        parents={"A": ["X"], "B": ["A"], "C": ["B"], "D": ["C"]},
        owners={"X"},
    )
    assert result["status"] == "unsupported"
    assert result["errors"][0]["code"] == "representation_depth_exceeded"
    assert result["errors"][0]["message"]
    assert result["allocations"] == {}
    assert result["breakdowns"] == []

def test_non_owner_child_dead_before_source_has_no_estate_but_descendant_represents():
    result = _run(
        {"X": "2020", "Y": "2010", "Z": None},
        parents={"Y": ["X"], "Z": ["Y"]},
        owners={"X"},
    )

    assert result["status"] == "complete"
    assert _share(result, "Z") == 1
    assert result["allocations"]["Y"]["inheritedShare"] == "0"
    assert result["allocations"]["Y"]["distributedShare"] == "0"
    representation_slots = [item for item in result["requiredSlots"] if item["reason"] == "representation_branch"]
    assert {item["anchorSlotId"] for item in representation_slots} == {"slot_Y"}
    assert representation_slots[0]["slotTypes"] == ["child"]
    assert "father" not in representation_slots[0]["slotTypes"]
    assert "mother" not in representation_slots[0]["slotTypes"]


def test_spouse_of_representation_anchor_only_receives_from_anchor_independent_estate():
    result = _run(
        {"X": "2020", "Y": "2010", "S": None, "Z": None},
        parents={"Y": ["X"], "Z": ["Y", "S"]},
        spouses=[("Y", "S")],
        owners={"X", "Y"},
    )

    assert result["status"] == "complete"
    assert _share(result, "S") == Fraction(1, 6)
    assert _share(result, "Z") == Fraction(5, 6)
    z_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "Z")
    assert {(term["sourcePersonId"], term["fraction"]) for term in z_terms} == {("Y", "1/6"), ("X", "2/3")}


def test_person_receiving_from_multiple_estates_keeps_each_source_in_breakdown():
    result = _run(
        {"X": "2010", "Y": "2020", "M": None},
        parents={"M": ["X", "Y"]},
        spouses=[("X", "Y")],
        owners={"X", "Y"},
    )

    assert result["status"] == "complete"
    assert _share(result, "M") == 1
    terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "M")
    assert {term.get("sourcePersonId") for term in terms} == {"X", "Y"}


def test_person_dead_after_source_receives_then_opens_later_estate():
    result = _run(
        {"X": "2010", "Y": "2020", "Z": None, "W": None},
        parents={"Y": ["X"], "Z": ["Y", "W"]},
        spouses=[("Y", "W")],
        owners={"X"},
        receive={"Y": False},
    )

    assert result["status"] == "complete"
    assert result["allocations"]["Y"]["inheritedShare"] == "1"
    assert result["allocations"]["Y"]["distributedShare"] == "1"
    assert _share(result, "Z") == _share(result, "W") == Fraction(1, 2)


def test_same_day_spouses_do_not_receive_cross_estates():
    result = _run(
        {"A": "15/06/2020", "B": "15/06/2020", "C": None},
        parents={"C": ["A", "B"]},
        spouses=[("A", "B")],
        owners={"A", "B"},
    )

    assert result["status"] == "complete"
    assert _share(result, "C") == 1
    assert result["allocations"]["A"]["inheritedShare"] == "0"
    assert result["allocations"]["B"]["inheritedShare"] == "0"
    assert result["warnings"] == []


def test_year_only_dates_normalize_to_same_day_snapshot():
    result = _run(
        {"A": "2015", "B": "2015", "C": None},
        parents={"C": ["A", "B"]},
        spouses=[("A", "B")],
        owners={"A", "B"},
    )
    assert result["status"] == "complete"
    assert _share(result, "C") == 1


def test_full_death_date_is_preserved_while_year_only_uses_first_of_january():
    assert _parse_death_date("23/07/2026") == date(2026, 7, 23)
    assert _parse_death_date("2026") == date(2026, 1, 1)


def test_year_only_death_orders_as_first_of_january_in_slot_table():
    """Rule F: child '2020' vs owner 01/06/2020 is before → Con slots only."""
    result = _run(
        {"A": "01/06/2020", "C": "2020", "D": None},
        parents={"C": ["A"], "D": ["C"]},
        owners={"A"},
    )
    anchors = {item["anchorSlotId"]: item for item in result["requiredSlots"]}
    assert anchors["slot_C"]["reason"] == "representation_branch"
    assert anchors["slot_C"]["slotTypes"] == ["child"]
    assert "slot_D" not in anchors
    assert result["warnings"] == []

    reverse = _run(
        {"A": "2020", "C": "01/06/2020"},
        parents={"C": ["A"]},
        owners={"A"},
    )
    anchors = {item["anchorSlotId"]: item for item in reverse["requiredSlots"]}
    assert anchors["slot_C"]["reason"] == "active_estate"
    assert "father" not in anchors["slot_C"]["slotTypes"]
    assert "mother" not in anchors["slot_C"]["slotTypes"]
    assert reverse["warnings"] == []


def test_five_living_land_owners_each_keep_one_fifth():
    ids = {"A", "B", "C", "D", "E"}
    result = _run({person_id: None for person_id in ids}, owners=ids)

    assert result["status"] == "complete"
    assert {_share(result, person_id) for person_id in ids} == {Fraction(1, 5)}


def test_living_land_owner_keeps_base_when_receive_is_off():
    result = _run({"A": None}, owners={"A"}, receive={"A": False})
    assert result["status"] == "complete"
    assert _share(result, "A") == 1
    assert result["allocations"]["A"]["baseShare"] == "1"
    assert result["breakdowns"][0]["terms"] == [{"kind": "base", "fraction": "1"}]


def test_living_nonreceiver_is_removed_without_opening_representation():
    result = _run(
        {"X": "2020", "A": None, "A1": None, "B": None},
        parents={"A": ["X"], "A1": ["A"], "B": ["X"]},
        owners={"X"},
        receive={"A": False},
    )

    assert result["status"] == "complete"
    assert _share(result, "A") == _share(result, "A1") == 0
    assert _share(result, "B") == 1


def test_dead_child_branch_without_descendants_is_removed_from_denominator():
    result = _run(
        {"X": "2020", "B": "2010", "C": None},
        parents={"B": ["X"], "C": ["X"]},
        owners={"X"},
    )

    assert result["status"] == "complete"
    assert _share(result, "C") == 1
    assert result["unresolvedEstates"] == []


def test_estate_without_any_valid_receiver_is_incomplete_and_conserved(later_lines):
    result = _run(
        {"X": "2020", "A": None},
        parents={"A": ["X"]},
        owners={"X"},
        receive={"A": False},
    )

    assert result["status"] == "incomplete"
    assert result["unresolvedEstates"] == [
        {"sourcePersonId": "X", "eventDate": "2020-01-01", "fraction": "1", "reason": "no_valid_heir"}
    ]
    assert result["conservation"] == {"allocated": "0", "unresolved": "1", "total": "1"}


def _invalid_result(nodes, people):
    return run_inheritance_case({"version": 2, "nodes": nodes}, people)


@pytest.mark.parametrize(
    ("nodes", "people", "code"),
    [
        (
            [{"id": "a", "personId": "A", "parentSlotIds": ["missing"], "isLandOwner": True}],
            {"A": {"ngay_chet": None}},
            "dangling_parent",
        ),
        (
            [
                {"id": "a1", "personId": "A", "parentSlotIds": [], "isLandOwner": True},
                {"id": "a2", "personId": "A", "parentSlotIds": []},
            ],
            {"A": {"ngay_chet": None}},
            "duplicate_person",
        ),
        (
            [
                {"id": "a", "personId": "A", "parentSlotIds": ["b"], "isLandOwner": True},
                {"id": "b", "personId": "B", "parentSlotIds": ["a"]},
            ],
            {"A": {"ngay_chet": None}, "B": {"ngay_chet": None}},
            "ancestry_cycle",
        ),
        (
            [{"id": "a", "personId": "A", "parentSlotIds": [], "spouseSlotId": "a", "isLandOwner": True}],
            {"A": {"ngay_chet": None}},
            "self_spouse",
        ),
        (
            [
                {"id": "a", "personId": "A", "parentSlotIds": ["b", "c", "d"], "isLandOwner": True},
                {"id": "b", "personId": "B", "parentSlotIds": []},
                {"id": "c", "personId": "C", "parentSlotIds": []},
                {"id": "d", "personId": "D", "parentSlotIds": []},
            ],
            {key: {"ngay_chet": None} for key in "ABCD"},
            "too_many_parents",
        ),
    ],
)
def test_invalid_graphs_are_rejected(nodes, people, code):
    result = _invalid_result(nodes, people)
    assert result["status"] == "invalid"
    assert code in {error["code"] for error in result["errors"]}


def test_boolean_flags_reject_string_false_instead_of_treating_it_as_true():
    result = _invalid_result(
        [
            {"id": "x", "personId": "X", "parentSlotIds": [], "isLandOwner": True},
            {
                "id": "a",
                "personId": "A",
                "parentSlotIds": ["x"],
                "willReceive": "false",
            },
        ],
        {"X": {"ngay_chet": "2020"}, "A": {"ngay_chet": None}},
    )

    assert result["status"] == "invalid"
    assert "invalid_boolean" in {error["code"] for error in result["errors"]}


def test_explicit_parents_do_not_fallback_unrelated_person_to_land_owner_branch():
    result = _run(
        {"X": "2020", "C": None, "D": None, "Z": None},
        parents={"Z": ["C", "D"]},
        owners={"X"},
    )

    assert result["status"] == "unsupported"
    assert result["errors"][0]["code"] == "second_order_required"
    assert _share(result, "Z") == 0


@pytest.mark.parametrize("represented", [False, True], ids=["direct", "representation"])
def test_first_rank_blocks_both_later_ranks(represented, later_lines):
    result = _run(
        {"X": "2020", "P": "1980", "S": None, "N": None, "C": "2010" if represented else None, "D": None},
        parents={"X": ["P"], "S": ["P"], "N": ["S"], "C": ["X"], "D": ["C"]},
        owners={"X"},
    )

    recipient = "D" if represented else "C"
    assert result["status"] == "complete"
    assert _share(result, recipient) == 1
    assert _share(result, "S") == _share(result, "N") == 0
    terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == recipient)
    assert terms == [{
        "kind": "representation" if represented else "inheritance",
        "fraction": "1",
        "sourcePersonId": "X",
        "heirRank": 1,
        **({"viaBranchPersonIds": ["C"]} if represented else {}),
    }]


def test_first_rank_all_refuse_then_second_rank_receives(later_lines):
    result = _run(
        {"X": "2020", "P": "1980", "S": None, "C": None},
        parents={"X": ["P"], "S": ["P"], "C": ["X"]},
        owners={"X"},
        receive={"C": False},
    )

    assert result["status"] == "complete"
    assert _share(result, "C") == 0
    assert _share(result, "S") == 1
    assert result["breakdowns"][0]["terms"] == [{
        "kind": "inheritance", "fraction": "1", "sourcePersonId": "X",
        "heirRank": 2, "relationshipRoles": ["sibling"],
    }]


@pytest.mark.parametrize(
    ("rank", "role", "deaths", "parents", "receive"),
    [
        (
            2, "grandparent", {"X": "2020", "P": "1980", "H": None, "J": None},
            {"X": ["P"], "P": ["H", "J"]}, {},
        ),
        (
            2, "sibling", {"X": "2020", "P": "1980", "H": None, "J": None},
            {"X": ["P"], "H": ["P"], "J": ["P"]}, {},
        ),
        (
            2, "grandchild", {"X": "2020", "C": None, "H": None, "J": None},
            {"C": ["X"], "H": ["C"], "J": ["C"]}, {"C": False},
        ),
        (
            3, "great_grandparent",
            {"X": "2020", "P": "1980", "G": "1970", "H": None, "J": None},
            {"X": ["P"], "P": ["G"], "G": ["H", "J"]}, {},
        ),
        (
            3, "parent_sibling",
            {"X": "2020", "P": "1980", "G": "1970", "H": None, "J": None},
            {"X": ["P"], "P": ["G"], "H": ["G"], "J": ["G"]}, {},
        ),
        (
            3, "sibling_child",
            {"X": "2020", "P": "1980", "S": "2010", "H": None, "J": None},
            {"X": ["P"], "S": ["P"], "H": ["S"], "J": ["S"]}, {},
        ),
        (
            3, "great_grandchild", {"X": "2020", "C": None, "G": None, "H": None, "J": None},
            {"C": ["X"], "G": ["C"], "H": ["G"], "J": ["G"]}, {"C": False, "G": False},
        ),
    ],
    ids=[
        "grandparents", "siblings", "grandchildren", "great-grandparents",
        "parent-siblings", "sibling-children", "great-grandchildren",
    ],
)
def test_all_later_rank_relationship_groups_share_equally(rank, role, deaths, parents, receive, later_lines):
    result = _run(deaths, parents=parents, owners={"X"}, receive=receive)

    assert result["status"] == "complete"
    assert _share(result, "H") == _share(result, "J") == Fraction(1, 2)
    assert sum((_share(result, person_id) for person_id in deaths), Fraction(0)) == 1
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}
    for breakdown in result["breakdowns"]:
        assert breakdown["personId"] in {"H", "J"}
        assert breakdown["terms"] == [{
            "kind": "inheritance", "fraction": "1/2", "sourcePersonId": "X",
            "heirRank": rank, "relationshipRoles": [role],
        }]
    assert {item["reason"] for item in result["requiredSlots"]} == {"active_estate"}


@pytest.mark.parametrize(
    ("sibling_parents", "expected"),
    [(["P"], 1), (["Q"], 1), (["P", "Q"], 1), (["R"], 0)],
    ids=["shared-father", "shared-mother", "shared-both", "unlinked"],
)
def test_siblings_require_at_least_one_explicit_shared_parent(sibling_parents, expected, later_lines):
    result = _run(
        {"X": "2020", "P": "1980", "Q": "1980", "R": "1980", "S": None},
        parents={"X": ["P", "Q"], "S": sibling_parents},
        owners={"X"},
    )

    assert _share(result, "S") == expected
    assert result["status"] == ("complete" if expected else "incomplete")
    assert result["conservation"]["total"] == "1"


def test_second_rank_multiple_roles_get_one_share_with_sorted_metadata(later_lines):
    deaths = {"X": "2020", "P": "1980", "Q": "1970", "H": None, "J": None}
    parents = {"X": ["P", "Q"], "P": ["H"], "H": ["Q"], "J": ["Q"]}
    result = _run(deaths, parents=parents, owners={"X"})
    reversed_result = _run(
        dict(reversed(list(deaths.items()))),
        parents={key: list(reversed(value)) for key, value in reversed(list(parents.items()))},
        owners={"X"},
    )

    assert result == reversed_result
    assert result["status"] == "complete"
    assert _share(result, "H") == _share(result, "J") == Fraction(1, 2)
    h_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "H")
    assert h_terms == [{
        "kind": "inheritance", "fraction": "1/2", "sourcePersonId": "X",
        "heirRank": 2, "relationshipRoles": ["grandparent", "sibling"],
    }]


def test_third_rank_multiple_roles_get_one_share_without_representation(later_lines):
    result = _run(
        {"X": "2020", "P": None, "G": "1970", "S": None, "H": None, "J": None},
        parents={"X": ["P"], "P": ["G"], "S": ["P"], "H": ["G", "S"], "J": ["S"]},
        owners={"X"},
        receive={"P": False, "S": False},
    )

    assert result["status"] == "complete"
    assert _share(result, "H") == _share(result, "J") == Fraction(1, 2)
    h_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "H")
    assert h_terms == [{
        "kind": "inheritance", "fraction": "1/2", "sourcePersonId": "X",
        "heirRank": 3, "relationshipRoles": ["parent_sibling", "sibling_child"],
    }]


def test_parent_sibling_group_excludes_source_and_own_parents_in_shared_ancestry(later_lines):
    result = _run(
        {"X": "2020", "P": None, "Q": None, "G": "1970", "H": None},
        parents={"X": ["P", "Q"], "P": ["G"], "Q": ["G"], "H": ["G"]},
        owners={"X"},
        receive={"P": False, "Q": False},
    )

    assert result["status"] == "complete"
    assert _share(result, "X") == _share(result, "P") == _share(result, "Q") == 0
    assert _share(result, "H") == 1
    assert result["breakdowns"][0]["terms"][0]["relationshipRoles"] == ["parent_sibling"]


@pytest.mark.parametrize("sibling_death", ["2010", "2020"], ids=["before", "same-day"])
@pytest.mark.parametrize("has_living_sibling", [True, False], ids=["rank-two-blocks", "rank-three-own-share"])
def test_dead_sibling_never_represents_but_their_child_can_receive_at_rank_three(
    sibling_death, has_living_sibling, later_lines
):
    result = _run(
        {"X": "2020", "P": "1980", "S": sibling_death, "N": None, "T": None},
        parents={"X": ["P"], "S": ["P"], "N": ["S"], "T": ["P"]},
        owners={"X"},
        receive={"T": has_living_sibling},
    )

    recipient = "T" if has_living_sibling else "N"
    assert result["status"] == "complete"
    assert _share(result, recipient) == 1
    assert _share(result, "S") == 0
    assert _share(result, "N" if has_living_sibling else "T") == 0
    assert result["breakdowns"][0]["terms"] == [{
        "kind": "inheritance", "fraction": "1", "sourcePersonId": "X",
        "heirRank": 2 if has_living_sibling else 3,
        "relationshipRoles": ["sibling" if has_living_sibling else "sibling_child"],
    }]
    assert {item["reason"] for item in result["requiredSlots"]} == {"active_estate"}


@pytest.mark.parametrize("nephew_death", ["2010", "2020"], ids=["before", "same-day"])
def test_dead_third_rank_candidate_does_not_pass_share_to_their_child(nephew_death, later_lines):
    result = _run(
        {"X": "2020", "P": "1980", "S": "2000", "N": nephew_death, "H": None, "K": None},
        parents={"X": ["P"], "S": ["P"], "N": ["S"], "H": ["S"], "K": ["N"]},
        owners={"X"},
    )

    assert result["status"] == "complete"
    assert _share(result, "H") == 1
    assert _share(result, "N") == _share(result, "K") == 0
    assert result["breakdowns"][0]["terms"][0]["heirRank"] == 3
    assert {item["reason"] for item in result["requiredSlots"]} == {"active_estate"}


@pytest.mark.parametrize(
    ("receive", "recipient", "rank"),
    [
        ({"T": False}, "S", 2),
        ({"S": False, "T": False}, "N", 3),
        ({"S": False, "T": False, "N": False}, None, None),
    ],
    ids=["redistribute-within-rank", "all-second-rank-refuse", "all-ranks-empty"],
)
def test_later_rank_refusals_redistribute_then_fall_back_or_remain_unresolved(receive, recipient, rank, later_lines):
    result = _run(
        {"X": "2020", "P": "1980", "S": None, "T": None, "N": None},
        parents={"X": ["P"], "S": ["P"], "T": ["P"], "N": ["S"]},
        owners={"X"},
        receive=receive,
    )

    if recipient is None:
        assert result["status"] == "incomplete"
        assert result["breakdowns"] == []
        assert result["unresolvedEstates"] == [{
            "sourcePersonId": "X", "eventDate": "2020-01-01", "fraction": "1", "reason": "no_valid_heir",
        }]
        assert result["conservation"] == {"allocated": "0", "unresolved": "1", "total": "1"}
    else:
        assert result["status"] == "complete"
        assert _share(result, recipient) == 1
        assert result["breakdowns"][0]["terms"][0]["heirRank"] == rank
        assert result["unresolvedEstates"] == []
        assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


@pytest.mark.parametrize("rank", [2, 3], ids=["second-rank", "third-rank"])
def test_later_rank_heir_dead_after_source_receives_despite_refusal_then_transmits(rank, later_lines):
    deaths = {"X": "2000", "P": "1980", "S": "2010" if rank == 2 else "1990", "N": "2010", "H": None, "T": None}
    parents = {"X": ["P"], "S": ["P"], "N": ["S"], "H": ["N" if rank == 3 else "S"]}
    if rank == 2:
        parents["T"] = ["P"]
    else:
        parents["T"] = ["S"]
    result = _run(deaths, parents=parents, owners={"X"}, receive={"S": False, "N": False})
    intermediate = "S" if rank == 2 else "N"

    assert result["status"] == "complete"
    assert result["allocations"][intermediate]["inheritedShare"] == "1/2"
    assert result["allocations"][intermediate]["distributedShare"] == "1/2"
    assert _share(result, intermediate) == 0
    assert _share(result, "H") == _share(result, "T") == Fraction(1, 2)
    h_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "H")
    assert h_terms == [{
        "kind": "inheritance", "fraction": "1/2", "sourcePersonId": intermediate, "heirRank": 1,
    }]
    t_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "T")
    assert t_terms[0]["heirRank"] == rank
    assert t_terms[0]["relationshipRoles"] == ["sibling" if rank == 2 else "sibling_child"]
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


def test_second_rank_transmission_reselects_third_rank_in_later_estate(later_lines):
    result = _run(
        {"X": "2000", "P": "1980", "G": "1970", "S": "2010", "H": None, "A": None},
        parents={"X": ["P"], "S": ["P"], "P": ["G"], "H": ["G"]},
        owners={"X", "A"},
        receive={"S": False},
    )

    assert result["status"] == "complete"
    assert result["allocations"]["S"]["inheritedShare"] == "1/2"
    assert result["allocations"]["S"]["distributedShare"] == "1/2"
    assert _share(result, "H") == _share(result, "A") == Fraction(1, 2)
    h_terms = next(item["terms"] for item in result["breakdowns"] if item["personId"] == "H")
    assert h_terms == [{
        "kind": "inheritance", "fraction": "1/2", "sourcePersonId": "S",
        "heirRank": 3, "relationshipRoles": ["parent_sibling"],
    }]
    assert {item["anchorSlotId"] for item in result["requiredSlots"]} == {"slot_A", "slot_X", "slot_S"}
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


def test_shared_ancestor_paths_and_same_day_estates_are_order_independent(later_lines):
    deaths = {"X": "2020", "Y": "2020", "P": "1980", "Q": "1980", "G": None, "H": None}
    parents = {"X": ["P", "Q"], "Y": ["P", "Q"], "H": ["P", "Q"], "P": ["G"], "Q": ["G"]}
    result = _run(deaths, parents=parents, owners={"X", "Y"})
    reversed_result = _run(
        dict(reversed(list(deaths.items()))),
        parents={key: list(reversed(value)) for key, value in reversed(list(parents.items()))},
        owners={"Y", "X"},
    )

    assert result == reversed_result
    assert result["status"] == "complete"
    assert _share(result, "G") == _share(result, "H") == Fraction(1, 2)
    assert result["allocations"]["X"]["inheritedShare"] == result["allocations"]["Y"]["inheritedShare"] == "0"
    for breakdown in result["breakdowns"]:
        assert breakdown["terms"] == [
            {
                "kind": "inheritance", "fraction": "1/4", "sourcePersonId": source,
                "heirRank": 2, "relationshipRoles": ["grandparent" if breakdown["personId"] == "G" else "sibling"],
            }
            for source in ("X", "Y")
        ]
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


def test_anonymized_female_x_eight_nephews_one_receiver_owns_both_assets(later_lines):
    """Shared engine result; two-asset persistence is exercised by the workspace smoke."""
    deaths = {
        "X": "2022-09-19", "P1": "1980-01-01", "P2": "1980-01-01",
        "S1": "1994-04-20", "S2": "2021-10-13",
        **{f"N{index}": None for index in range(1, 9)},
    }
    parents = {person_id: ["P1", "P2"] for person_id in ("X", "S1", "S2")}
    parents.update({f"N{index}": ["S1" if index <= 4 else "S2"] for index in range(1, 9)})
    result = _run(
        deaths, parents=parents, owners={"X"},
        receive={f"N{index}": index == 1 for index in range(1, 9)},
    )

    assert result["status"] == "complete"
    assert _share(result, "N1") == 1
    assert all(_share(result, f"N{index}") == 0 for index in range(2, 9))
    assert _share(result, "X") == 0
    assert result["breakdowns"] == [{
        "personId": "N1", "total": "1",
        "terms": [{
            "kind": "inheritance", "fraction": "1", "sourcePersonId": "X",
            "heirRank": 3, "relationshipRoles": ["sibling_child"],
        }],
    }]
    assert {item["anchorSlotId"] for item in result["requiredSlots"]} == {"slot_X"}
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


@pytest.mark.parametrize(
    ("deaths", "parents", "receive", "roles"),
    [
        (
            {"X": "2020", "P": "1980", "G": None, "S": None, "C": None, "H": None, "J": None},
            {"X": ["P"], "P": ["G"], "S": ["P"], "C": ["X"], "H": ["C"], "J": ["C"]},
            {"C": False},
            {"G": "grandparent", "S": "sibling", "H": "grandchild", "J": "grandchild"},
        ),
        (
            {
                "X": "2020", "P": "1980", "G": "1970", "GG": None, "A": None,
                "S": "2010", "N": None, "C": None, "GC": None, "H": None, "J": None,
            },
            {
                "X": ["P"], "P": ["G"], "G": ["GG"], "A": ["G"], "S": ["P"],
                "N": ["S"], "C": ["X"], "GC": ["C"], "H": ["GC"], "J": ["GC"],
            },
            {"C": False, "GC": False},
            {
                "GG": "great_grandparent", "A": "parent_sibling", "N": "sibling_child",
                "H": "great_grandchild", "J": "great_grandchild",
            },
        ),
    ],
    ids=["all-second-rank-groups", "all-third-rank-groups"],
)
def test_mixed_relationship_groups_share_per_person_not_per_group(deaths, parents, receive, roles, later_lines):
    result = _run(deaths, parents=parents, owners={"X"}, receive=receive)
    rank = 2 if len(roles) == 4 else 3
    share = Fraction(1, len(roles))

    assert result["status"] == "complete"
    assert {item["personId"] for item in result["breakdowns"]} == set(roles)
    for breakdown in result["breakdowns"]:
        person_id = breakdown["personId"]
        assert _share(result, person_id) == share
        assert breakdown["terms"] == [{
            "kind": "inheritance", "fraction": str(share), "sourcePersonId": "X",
            "heirRank": rank, "relationshipRoles": [roles[person_id]],
        }]
    assert result["conservation"] == {"allocated": "1", "unresolved": "0", "total": "1"}


def test_later_rank_transmission_without_any_eligible_heir_retains_unresolved_estate(later_lines):
    result = _run(
        {"X": "2000", "P": "1980", "S": "2010", "W": None},
        parents={"X": ["P"], "S": ["P"]},
        spouses=[("S", "W")],
        owners={"X"},
        receive={"S": False, "W": False},
    )

    assert result["status"] == "incomplete"
    assert result["allocations"]["S"]["inheritedShare"] == "1"
    assert result["allocations"]["S"]["distributedShare"] == "1"
    assert result["breakdowns"] == []
    assert result["unresolvedEstates"] == [{
        "sourcePersonId": "S", "eventDate": "2010-01-01", "fraction": "1", "reason": "no_valid_heir",
    }]
    assert result["conservation"] == {"allocated": "0", "unresolved": "1", "total": "1"}
def test_spouse_slot_uses_only_last_candidate_as_lawful_spouse():
    nodes = [
        {"id": "dead", "personId": "D", "parentSlotIds": [],
         "spouseSlotIds": ["first", "last"], "isLandOwner": True,
         "willReceive": True, "hidden": False, "deleted": False},
        {"id": "first", "personId": "A", "parentSlotIds": [],
         "isLandOwner": False, "willReceive": True,
         "hidden": False, "deleted": False},
        {"id": "last", "personId": "B", "parentSlotIds": [],
         "isLandOwner": False, "willReceive": True,
         "hidden": False, "deleted": False},
    ]
    result = run_inheritance_case(
        {"version": 2, "nodes": nodes},
        {"D": {"ngay_chet": "2020"}, "A": {"ngay_chet": None},
         "B": {"ngay_chet": None}},
    )
    assert result["status"] == "complete"
    assert _share(result, "A") == 0
    assert _share(result, "B") == 1


def test_living_person_spouse_slot_is_ignored():
    nodes = [
        {"id": "living", "personId": "A", "parentSlotIds": [],
         "spouseSlotIds": ["partner"], "isLandOwner": True,
         "willReceive": True, "hidden": False, "deleted": False},
        {"id": "partner", "personId": "B", "parentSlotIds": [],
         "isLandOwner": False, "willReceive": True,
         "hidden": False, "deleted": False},
    ]
    result = run_inheritance_case(
        {"version": 2, "nodes": nodes},
        {"A": {"ngay_chet": None}, "B": {"ngay_chet": None}},
    )
    assert result["status"] == "complete"
    assert "B" not in result["allocations"] or _share(result, "B") == 0


def test_last_migrated_spouse_candidate_receives_spouse_share():
    nodes = [
        {"id": "dead", "personId": "D", "parentSlotIds": [],
         "spouseSlotIds": ["wife", "new-spouse"], "isLandOwner": True,
         "willReceive": True, "hidden": False, "deleted": False},
        *[
            {"id": nid, "personId": pid, "parentSlotIds": [],
             "isLandOwner": False, "willReceive": True,
             "hidden": False, "deleted": False}
            for nid, pid in (("wife", "W"), ("new-spouse", "N"))
        ],
    ]
    result = run_inheritance_case(
        {"version": 2, "nodes": nodes},
        {"D": {"ngay_chet": "2020"}, "W": {"ngay_chet": "2022"},
         "N": {"ngay_chet": None}},
    )
    assert result["status"] == "complete"
    assert _share(result, "N") > 0
