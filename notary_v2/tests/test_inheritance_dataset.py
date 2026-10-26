"""Independent dataset solver regressions for D-038/R-32."""
import json
from pathlib import Path

import pytest

from tools.inheritance_dataset.reference_solver import solve


FIXTURES = Path(__file__).parent / "fixtures" / "inheritance_dataset"


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.json")), ids=lambda p: p.stem)
def test_dataset_expected_results(path):
    for case in json.loads(path.read_text(encoding="utf-8"))["cases"]:
        actual = solve(case)
        assert actual == {key: case["expected"][key] for key in actual}, case["id"]


def _case(parents, recipients, deaths=None, asset_count=1):
    people = set(parents) | {p for values in parents.values() for p in values} | {"X"}
    deaths = {"X": "01/06/2020", **(deaths or {})}
    return {
        "asset_count": asset_count,
        "people": {p: {"ho_ten": p, "ngay_chet": deaths.get(p)} for p in people},
        "diagram": {"nodes": [
            {"id": p, "personId": p, "parentSlotIds": parents.get(p, []),
             "spouseSlotId": None, "ownPositions": [1] if p == "X" else [],
             "receivePositions": recipients.get(p, []), "deleted": False}
            for p in sorted(people)
        ]},
    }


@pytest.mark.parametrize("parents,recipients,expected", [
    # All rank-2 roles share per person, not per relation/branch.
    ({"X": ["P"], "P": ["G"], "S": ["P"], "C": ["X"], "GC": ["C"]},
     {"G": [1], "S": [1], "GC": [1]}, {"G": "1/3", "S": "1/3", "GC": "1/3"}),
    # G is both grandparent and sibling; shared parents also do not double a sibling.
    ({"X": ["F", "M"], "F": ["G"], "G": ["M"], "S": ["F", "M"]},
     {"G": [1], "S": [1]}, {"G": "1/2", "S": "1/2"}),
    # All rank-2 candidates refuse; all four rank-3 roles receive equal shares.
    ({"X": ["P"], "P": ["G"], "G": ["GG"], "U": ["G"],
      "S": ["P"], "N": ["S"], "C": ["X"], "GC": ["C"], "GGC": ["GC"]},
     {"GG": [1], "U": [1], "N": [1], "GGC": [1]},
     {"GG": "1/4", "U": "1/4", "N": "1/4", "GGC": "1/4"}),
    # U is both uncle and nephew, still one share alongside another nephew.
    ({"X": ["P"], "P": ["G"], "S": ["P"], "U": ["G", "S"], "N": ["S"]},
     {"U": [1], "N": [1]}, {"U": "1/2", "N": "1/2"}),
    # A receiving rank 1 takes priority over rank 2 and rank 3.
    ({"X": ["P"], "S": ["P"], "N": ["S"]},
     {"P": [1], "S": [1], "N": [1]}, {"P": "1/1"}),
])
def test_rank_priority_roles_and_deduplication(parents, recipients, expected):
    case = _case(parents, recipients)
    for nodes in (case["diagram"]["nodes"], list(reversed(case["diagram"]["nodes"]))):
        case["diagram"]["nodes"] = nodes
        result = solve(case)
        assert result["status"] == "complete"
        assert result["shares"] == {"1": expected}
        assert result["unresolved"] == {"1": "0/1"}


@pytest.mark.parametrize("sibling_death", ["01/06/2019", "01/06/2020"])
def test_no_representation_in_later_ranks(sibling_death):
    # A dead sibling does not create a branch competing with the living sibling.
    case = _case({"X": ["P"], "S": ["P"], "T": ["P"], "N": ["S"]},
                 {"S": [1], "T": [1], "N": [1]}, {"S": sibling_death})
    assert solve(case)["shares"] == {"1": {"T": "1/1"}}
    # A dead rank-3 nephew cannot pass its share to its child (rank 4).
    case = _case({"X": ["P"], "S": ["P"], "N": ["S"], "NN": ["N"]},
                 {"N": [1], "NN": [1]}, {"S": sibling_death, "N": sibling_death})
    result = solve(case)
    assert result["status"] == "incomplete"
    assert result["shares"] == {"1": {}}
    assert result["unresolved"] == {"1": "1/1"}


@pytest.mark.parametrize("rank", [2, 3])
def test_later_rank_death_transfers_without_receive_mark(rank):
    parents = {"X": ["P"], "S": ["P"], "N": ["S"]}
    heir = "S" if rank == 2 else "N"
    parents["R"] = [heir]
    deaths = {heir: "01/06/2021"}
    if rank == 3:
        deaths["S"] = "01/06/2019"
    case = _case(parents, {"R": [1]}, deaths)
    result = solve(case)
    assert result["status"] == "complete"
    assert result["shares"] == {"1": {"R": "1/1"}}


def test_rank_selection_and_refusal_are_per_asset():
    case = _case({"X": ["P"], "S": ["P"], "N": ["S"]},
                 {"S": [1], "N": [2]}, asset_count=3)
    next(n for n in case["diagram"]["nodes"] if n["id"] == "X")["ownPositions"] = [1, 2, 3]
    result = solve(case)
    assert result["status"] == "incomplete"
    assert result["shares"] == {"1": {"S": "1/1"}, "2": {"N": "1/1"}, "3": {}}
    assert result["unresolved"] == {"1": "0/1", "2": "0/1", "3": "1/1"}
