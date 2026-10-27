"""Authoritative inheritance calculation for the case diagram.

The engine is intentionally pure: callers provide diagram nodes and person
records, and receive a JSON-serializable result. Database and HTTP concerns
belong to the router layer.

Each estate uses rank 1 with branch representation. Ranks 2 and 3 are parked
behind ENABLE_LATER_LINES; without rank-1 heirs the default is unsupported.
When enabled, later ranks split equally per distinct person without
representation and expose sorted relationshipRoles from explicit parent links.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid5


ENGINE_VERSION = 2
ENABLE_LATER_LINES = False


def _value(record: Any, *names: str) -> Any:
    for name in names:
        if isinstance(record, Mapping) and name in record:
            return record[name]
        if hasattr(record, name):
            return getattr(record, name)
    return None


def _person_id(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _parse_death_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        return date(int(text), 1, 1)
    if len(text) == 10 and text[2] == "/" and text[5] == "/":
        return datetime.strptime(text, "%d/%m/%Y").date()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"Ngày chết không hợp lệ: {text}") from exc


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _percent_text(value: Fraction) -> str:
    percent = (Decimal(value.numerator) * 100 / Decimal(value.denominator)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{percent:.2f}"


def _error(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **details}


def _empty_result(errors: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "engineVersion": ENGINE_VERSION,
        "status": "invalid",
        "allocations": {},
        "breakdowns": [],
        "requiredSlots": [],
        "warnings": [],
        "errors": errors,
        "unresolvedEstates": [],
        "conservation": {"allocated": "0", "unresolved": "0", "total": "0"},
    }


def _unsupported_result(errors: list[dict[str, Any]]) -> dict[str, Any]:
    result = _empty_result(errors)
    result["status"] = "unsupported"
    return result


def _validate_and_build_graph(
    engine_input: Mapping[str, Any], people_by_id: Mapping[Any, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if engine_input.get("version") != ENGINE_VERSION:
        errors.append(_error("invalid_version", "Diagram phải dùng version 2."))

    raw_nodes = engine_input.get("nodes")
    if not isinstance(raw_nodes, list):
        return {}, {}, errors + [_error("invalid_nodes", "nodes phải là một danh sách.")]

    nodes: dict[str, dict[str, Any]] = {}
    active_people: dict[str, dict[str, Any]] = {}
    normalized_people = {_person_id(key): value for key, value in people_by_id.items()}

    for index, raw in enumerate(raw_nodes):
        if not isinstance(raw, Mapping):
            errors.append(_error("invalid_node", "Node phải là object.", index=index))
            continue
        slot_id = _person_id(raw.get("id"))
        if not slot_id:
            errors.append(_error("missing_node_id", "Node thiếu id.", index=index))
            continue
        if slot_id in nodes:
            errors.append(_error("duplicate_node_id", "Node id bị trùng.", nodeId=slot_id))
            continue

        parent_ids = raw.get("parentSlotIds", [])
        if parent_ids is None:
            parent_ids = []
        if not isinstance(parent_ids, list):
            errors.append(_error("invalid_parent_slots", "parentSlotIds phải là danh sách.", nodeId=slot_id))
            parent_ids = []

        boolean_values: dict[str, bool] = {}
        for field, default in (
            ("isLandOwner", False),
            ("willReceive", True),
            ("hidden", False),
            ("deleted", False),
        ):
            value = raw.get(field, default)
            if not isinstance(value, bool):
                errors.append(
                    _error("invalid_boolean", f"{field} phải là boolean.", nodeId=slot_id, field=field)
                )
                value = default
            boolean_values[field] = value

        person_id = _person_id(raw.get("personId")) or None
        spouse_ids = raw.get("spouseSlotIds")
        if not isinstance(spouse_ids, list):
            legacy_spouse = raw.get("spouseSlotId")
            spouse_ids = [legacy_spouse] if legacy_spouse else []
        node = {
            "id": slot_id,
            "personId": person_id,
            "parentSlotIds": [_person_id(item) for item in parent_ids],
            "spouseSlotIds": [
                _person_id(item) for item in spouse_ids if _person_id(item)
            ],
            **boolean_values,
        }
        nodes[slot_id] = node

        if not person_id or node["hidden"] or node["deleted"]:
            continue
        if person_id in active_people:
            errors.append(
                _error(
                    "duplicate_person",
                    "Một người không được xuất hiện ở hai node đang hoạt động.",
                    personId=person_id,
                )
            )
            continue
        if person_id not in normalized_people:
            errors.append(
                _error("unknown_person", "Người trên Diagram không tồn tại trong Stage/DB.", personId=person_id)
            )
            continue
        active_people[person_id] = node

    for node in active_people.values():
        if len(node["parentSlotIds"]) > 2:
            errors.append(
                _error("too_many_parents", "Một người chỉ có tối đa hai cha/mẹ.", nodeId=node["id"])
            )
        for parent_id in node["parentSlotIds"]:
            if not parent_id or parent_id not in nodes:
                errors.append(
                    _error("dangling_parent", "Quan hệ cha/mẹ trỏ tới node không tồn tại.", nodeId=node["id"])
                )
            elif parent_id == node["id"]:
                errors.append(_error("self_parent", "Một người không thể là cha/mẹ của chính mình.", nodeId=node["id"]))
        for spouse_id in node["spouseSlotIds"]:
            if not spouse_id or spouse_id not in nodes:
                errors.append(
                    _error("dangling_spouse", "Quan hệ vợ/chồng trỏ tới node không tồn tại.", nodeId=node["id"])
                )
            elif spouse_id == node["id"]:
                errors.append(_error("self_spouse", "Một người không thể là vợ/chồng của chính mình.", nodeId=node["id"]))

    children_by_person: dict[str, set[str]] = defaultdict(set)
    parents_by_person: dict[str, set[str]] = defaultdict(set)
    spouses_by_person: dict[str, set[str]] = defaultdict(set)
    person_by_slot = {node["id"]: person_id for person_id, node in active_people.items()}

    for child_id, node in active_people.items():
        for parent_slot_id in node["parentSlotIds"]:
            parent_id = person_by_slot.get(parent_slot_id)
            if not parent_id:
                continue
            children_by_person[parent_id].add(child_id)
            parents_by_person[child_id].add(parent_id)
        spouse_ids = node["spouseSlotIds"]
        spouse_id = person_by_slot.get(spouse_ids[-1] if spouse_ids else "")
        if spouse_id:
            spouses_by_person[child_id].add(spouse_id)


    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(person_id: str) -> None:
        if person_id in visiting:
            errors.append(_error("ancestry_cycle", "Quan hệ huyết thống tạo thành chu kỳ.", personId=person_id))
            return
        if person_id in visited:
            return
        visiting.add(person_id)
        for child_id in children_by_person.get(person_id, set()):
            visit(child_id)
        visiting.remove(person_id)
        visited.add(person_id)

    for person_id in active_people:
        visit(person_id)

    deaths: dict[str, date | None] = {}
    for person_id in active_people:
        raw_death = _value(
            normalized_people[person_id], "ngay_chet", "death_date", "deathDate", "death"
        )
        try:
            deaths[person_id] = _parse_death_date(raw_death)
        except ValueError as exc:
            errors.append(_error("invalid_death_date", str(exc), personId=person_id))

    owners = [person_id for person_id, node in active_people.items() if node["isLandOwner"]]
    if not owners:
        errors.append(_error("missing_land_owner", "Chưa chọn Chủ đất."))

    graph = {
        "people": normalized_people,
        "nodesByPerson": active_people,
        "personBySlot": person_by_slot,
        "children": children_by_person,
        "parents": parents_by_person,
        "spouses": spouses_by_person,
        "deaths": deaths,
        "owners": owners,
    }
    return nodes, graph, errors


def _required_slot_table(graph, active_estates):
    """Build diagram requirements independently of acceptance/share calculation."""
    active = graph["nodesByPerson"]
    deaths = graph["deaths"]
    requirements = {}
    missing = {}

    def bounds(person_id):
        # Rule F: a year-only death ("2020") is 01/01 of that year when
        # ordering deaths, exactly as _parse_death_date already normalizes it.
        death = deaths[person_id]
        if death is None:
            return None
        return death, death

    def is_deceased(person_id):
        record = graph["people"][person_id]
        return deaths[person_id] is not None or _value(record, "loai_giay_to") in (
            "Giấy chứng tử", "Giấy chứng tử (bản sao)",
            "Trích lục khai tử", "Trích lục khai tử (bản sao)",
        )

    def mark_missing(person_id):
        missing[person_id] = _error(
            "missing_death_date", "thiếu ngày mất", personId=person_id,
            anchorSlotId=active[person_id]["id"],
        )

    person_by_slot = graph["personBySlot"]

    def slot_id(node_id, role, ordinal):
        return str(uuid5(NAMESPACE_URL, str((node_id, role, ordinal))))

    def spouse_pair_slots(node, own_only=False):
        """Pair slot ids in spouse-ordinal order (rule A).

        Ordinal 0 is the pair (person + spouse slot 1) and always exists; each
        further ordinal is the pair for a spouse placed in the spare slot.
        Declared ids that are not engine ids (legacy/migrated state) keep their
        place so children already paired to them stay in the same group —
        except when the pair is anchored on the partner's node, which owns the
        Con slots for those children.
        """
        declared = list(node["spouseSlotIds"])
        occupied = [item for item in declared if item in person_by_slot]
        count = max(2, len(occupied) + 1)
        engine_ids = [slot_id(node["id"], "spouse", ordinal) for ordinal in range(count)]
        if own_only:
            return engine_ids, count
        keys = list(engine_ids)
        free = [index for index, item in enumerate(engine_ids) if item not in declared]
        for item, index in zip([item for item in declared if item not in engine_ids], free):
            keys[index] = item
        return keys, count

    def co_parents(person_id):
        """Other parents of this person's children already on the diagram."""
        node_id = active[person_id]["id"]
        partners = set()
        for child_id in graph["children"].get(person_id, ()):
            for parent_slot_id in active[child_id]["parentSlotIds"]:
                if parent_slot_id == node_id:
                    continue
                partner = person_by_slot.get(parent_slot_id)
                if partner and partner != person_id:
                    partners.add(partner)
        return partners

    def anchored_elsewhere(person_id):
        """Rule C: the spouse relation is recorded on another node's slot.

        A person whose own engine spouse slot already holds the partner anchors
        the pair themselves, so the relation is not delegated.
        """
        node = active[person_id]
        declared = node["spouseSlotIds"]
        if any(slot_id(node["id"], "spouse", ordinal) in person_by_slot
               for ordinal in range(len(declared) + 1)):
            return False
        node_id = node["id"]
        return any(node_id in other["spouseSlotIds"]
                   for other in active.values() if other["id"] != node_id)

    def has_existing_spouse(person_id):
        """Rule B/C: a spouse relation of this person is already on the diagram."""
        node = active[person_id]
        if any(item in person_by_slot for item in node["spouseSlotIds"]):
            return True
        return anchored_elsewhere(person_id) or bool(co_parents(person_id))

    def has_existing_parents(node):
        """True when this anchor is already someone's child on the diagram."""
        own = {slot_id(node["id"], "father", 0), slot_id(node["id"], "mother", 0)}
        return any(item and item not in own for item in node["parentSlotIds"])

    def child_groups(person_id, reason):
        """Con slots grouped per pair: key = pair ordinal, value = children."""
        node = active[person_id]
        keys, _count = spouse_pair_slots(node, own_only=anchored_elsewhere(person_id))
        is_owner = person_id in graph["owners"]
        groups: dict[int, list[str]] = defaultdict(list)
        for child_id in sorted(graph["children"].get(person_id, ())):
            other_slots = [
                item for item in active[child_id]["parentSlotIds"]
                if item != node["id"]
            ]
            index = next(
                (keys.index(item) for item in other_slots if item in keys), None
            )
            if index is None:
                # Unpaired child or a pair whose Con slots another anchor owns.
                if (reason == "representation_branch" or is_owner
                        or not other_slots or not has_existing_spouse(person_id)):
                    index = 0
                else:
                    continue
            groups[index].append(child_id)
        return groups, keys

    def add(person_id, reason):
        node = active[person_id]
        is_owner = person_id in graph["owners"]
        groups, keys = child_groups(person_id, reason)
        keys_count = len(keys)
        if reason == "representation_branch":
            roles = ["child"]
        elif reason == "living_owner":
            roles = ["spouse"]
        else:
            roles = []
            if is_owner or not has_existing_parents(node):
                roles += ["father", "mother"]
            if is_owner or not has_existing_spouse(person_id):
                roles.append("spouse")
            if groups or "spouse" in roles or is_owner:
                roles.append("child")
        slots = []
        for role in roles:
            if role in ("father", "mother"):
                slots.append({"id": slot_id(node["id"], role, 0),
                              "role": role, "ordinal": 0})
            elif role == "spouse":
                for ordinal in range(keys_count):
                    slots.append({"id": slot_id(node["id"], "spouse", ordinal),
                                  "role": "spouse", "ordinal": ordinal})
            else:
                ordinal = 0
                for index in sorted(set(groups) | set(range(keys_count))):
                    if index and keys[index] not in person_by_slot and not groups[index]:
                        continue  # spare spouse slot: no pair until it is filled
                    for _ in range(max(2, len(groups[index]) + 1)):
                        slots.append({"id": slot_id(node["id"], "child", ordinal),
                                      "role": "child", "ordinal": ordinal})
                        ordinal += 1
        requirements[(node["id"], reason)] = {
            "anchorSlotId": node["id"], "reason": reason, "slotTypes": roles,
            "minimumEmptyChildSlots": int("child" in roles),
            "minimumEmptySpouseSlots": int("spouse" in roles), "slots": slots,
        }

    def compare(person_id, source_id):
        if not is_deceased(person_id):
            return "alive"
        own, source = bounds(person_id), bounds(source_id)
        if own is None or source is None:
            mark_missing(person_id)
            return "unknown"
        if own[0] < source[0]:
            return "before"
        if own[0] > source[0]:
            return "after"
        return "same"

    visited = set()

    def estate(source_id):
        if source_id in visited:
            return
        visited.add(source_id)
        add(source_id, "active_estate")
        for person_id in sorted(graph["parents"].get(source_id, set()) |
                                graph["spouses"].get(source_id, set())):
            if compare(person_id, source_id) == "after":
                estate(person_id)
        for person_id in sorted(graph["children"].get(source_id, ())):
            descendant(person_id, source_id, 1)

    def descendant(person_id, source_id, depth):
        comparison = compare(person_id, source_id)
        if comparison == "after":
            estate(person_id)
        elif comparison in ("before", "same") and depth < 3:
            add(person_id, "representation_branch")
            for child_id in sorted(graph["children"].get(person_id, ())):
                descendant(child_id, source_id, depth + 1)

    for person_id in sorted(graph["owners"]):
        if not is_deceased(person_id):
            add(person_id, "living_owner")
        elif bounds(person_id) is None:
            mark_missing(person_id)
        else:
            estate(person_id)
    if ENABLE_LATER_LINES:
        for person_id in sorted(active_estates):
            if person_id not in missing:
                estate(person_id)
    # A person with incomparable dates must never receive slots via another path.
    return (
        [value for key, value in sorted(requirements.items())
         if graph["personBySlot"][key[0]] not in missing],
        list(missing.values()),
    )


def run_inheritance_case(
    engine_input: Mapping[str, Any], people_by_id: Mapping[Any, Any]
) -> dict[str, Any]:
    """Divide each estate by its first eligible rank, with representation only in rank 1."""

    if not isinstance(engine_input, Mapping) or not isinstance(people_by_id, Mapping):
        return _empty_result([_error("invalid_input", "Dữ liệu engine không hợp lệ.")])

    _nodes, graph, errors = _validate_and_build_graph(engine_input, people_by_id)
    if errors:
        return _empty_result(errors)

    nodes_by_person: dict[str, dict[str, Any]] = graph["nodesByPerson"]
    children: dict[str, set[str]] = graph["children"]
    parents: dict[str, set[str]] = graph["parents"]
    spouses: dict[str, set[str]] = graph["spouses"]
    deaths: dict[str, date | None] = graph["deaths"]
    owners: list[str] = graph["owners"]

    holdings = {person_id: Fraction(0) for person_id in nodes_by_person}
    base_shares = {person_id: Fraction(0) for person_id in nodes_by_person}
    inherited_shares = {person_id: Fraction(0) for person_id in nodes_by_person}
    distributed_shares = {person_id: Fraction(0) for person_id in nodes_by_person}
    terms: dict[str, list[dict[str, Any]]] = defaultdict(list)
    active_estates = set()
    unresolved_estates: list[dict[str, Any]] = []

    base = Fraction(1, len(owners))
    for person_id in owners:
        holdings[person_id] += base
        base_shares[person_id] += base
        terms[person_id].append({"kind": "base", "fraction": _fraction_text(base)})


    def death_comparison(person_id: str, event_date: date) -> str:
        death = deaths[person_id]
        if death is None:
            return "alive"
        if death < event_date:
            return "before"
        if death == event_date:
            return "same"
        return "after"

    def accepts(person_id: str, comparison: str) -> bool:
        return comparison == "after" or (
            comparison == "alive" and nodes_by_person[person_id]["willReceive"]
        )

    representation_depth_exceeded = False

    def descendant_plan(
        person_id: str,
        event_date: date,
        via: tuple[str, ...],
        stack: frozenset[str],
        depth: int,
    ) -> dict[str, Any] | None:
        nonlocal representation_depth_exceeded
        if person_id in stack:
            return None
        comparison = death_comparison(person_id, event_date)
        if comparison in ("alive", "after"):
            if not accepts(person_id, comparison):
                return None
            if depth > 3:
                representation_depth_exceeded = True
                return None
            return {"type": "person", "personId": person_id, "via": list(via)}

        plans = []
        next_stack = stack | {person_id}
        for child_id in sorted(children.get(person_id, set())):
            plan = descendant_plan(child_id, event_date, via + (person_id,), next_stack, depth + 1)
            if plan is not None:
                plans.append(plan)
        if not plans:
            return None
        return {"type": "split", "children": plans}

    def first_line_units(source_id: str, event_date: date) -> list[dict[str, Any]]:
        units: list[dict[str, Any]] = []
        seen_direct: set[str] = set()
        spouse_slots = spouses.get(source_id, set())
        for person_id in sorted(parents.get(source_id, set()) | spouse_slots):
            comparison = death_comparison(person_id, event_date)
            if person_id not in seen_direct and accepts(person_id, comparison):
                units.append({"type": "person", "personId": person_id, "via": []})
                seen_direct.add(person_id)
        for child_id in sorted(children.get(source_id, set())):
            plan = descendant_plan(child_id, event_date, (), frozenset({source_id}), 1)
            if plan is not None:
                units.append(plan)
        return units

    def siblings_of(person_id: str) -> set[str]:
        return {
            child_id
            for parent_id in parents.get(person_id, set())
            for child_id in children.get(parent_id, set())
            if child_id != person_id
        }

    def later_line_candidates(source_id: str, rank: int) -> dict[str, set[str]]:
        """Collect explicit graph roles; multiple paths still yield one person per rank."""
        source_parents = parents.get(source_id, set())
        grandparents = {
            person_id
            for parent_id in source_parents
            for person_id in parents.get(parent_id, set())
        }
        source_siblings = siblings_of(source_id)
        grandchildren = {
            person_id
            for child_id in children.get(source_id, set())
            for person_id in children.get(child_id, set())
        }
        if rank == 2:
            role_groups = {
                "grandparent": grandparents,
                "sibling": source_siblings,
                "grandchild": grandchildren,
            }
        else:
            role_groups = {
                "great_grandparent": {
                    person_id
                    for grandparent_id in grandparents
                    for person_id in parents.get(grandparent_id, set())
                },
                "parent_sibling": {
                    person_id
                    for parent_id in source_parents
                    for person_id in siblings_of(parent_id)
                } - source_parents,
                "sibling_child": {
                    person_id
                    for sibling_id in source_siblings
                    for person_id in children.get(sibling_id, set())
                },
                "great_grandchild": {
                    person_id
                    for grandchild_id in grandchildren
                    for person_id in children.get(grandchild_id, set())
                },
            }
        candidates: dict[str, set[str]] = defaultdict(set)
        for role, person_ids in role_groups.items():
            for person_id in person_ids - {source_id}:
                candidates[person_id].add(role)
        return candidates

    def later_line_units(source_id: str, event_date: date, rank: int) -> list[dict[str, Any]]:
        candidates = later_line_candidates(source_id, rank)
        return [
            {
                "type": "person",
                "personId": person_id,
                "via": [],
                "relationshipRoles": sorted(candidates[person_id]),
            }
            for person_id in sorted(candidates)
            if accepts(person_id, death_comparison(person_id, event_date))
        ]

    def credit(plan: dict[str, Any], amount: Fraction, source_id: str, heir_rank: int) -> None:
        if plan["type"] == "split":
            child_plans = plan["children"]
            child_share = amount / len(child_plans)
            for child_plan in child_plans:
                credit(child_plan, child_share, source_id, heir_rank)
            return

        person_id = plan["personId"]
        holdings[person_id] += amount
        inherited_shares[person_id] += amount
        via = plan["via"]
        term = {
            "kind": "representation" if via else "inheritance",
            "fraction": _fraction_text(amount),
            "sourcePersonId": source_id,
            "heirRank": heir_rank,
        }
        if via:
            term["viaBranchPersonIds"] = via
        if heir_rank > 1:
            term["relationshipRoles"] = plan["relationshipRoles"]
        terms[person_id].append(term)

    death_groups: dict[date, list[str]] = defaultdict(list)
    for person_id, death in deaths.items():
        if death is not None:
            death_groups[death].append(person_id)


    for event_date in sorted(death_groups):
        day_estates = {
            person_id: holdings[person_id]
            for person_id in sorted(death_groups[event_date])
            if holdings[person_id] > 0
        }
        # Distribute estates in a distinct pass; preserve the original order
        # of operations so transfers do not affect same-day estates.
        for source_id, estate in day_estates.items():
            holdings[source_id] = Fraction(0)
            distributed_shares[source_id] += estate
            active_estates.add(source_id)

        for source_id, estate in day_estates.items():
            units = first_line_units(source_id, event_date)

            heir_rank = 1
            if not units and ENABLE_LATER_LINES:
                for heir_rank in (2, 3):
                    units = later_line_units(source_id, event_date, heir_rank)
                    if units:
                        break
            if not units:
                unresolved_estates.append(
                    {
                        "sourcePersonId": source_id,
                        "eventDate": event_date.isoformat(),
                        "fraction": _fraction_text(estate),
                        "reason": "no_valid_heir",
                    }
                )
                continue
            unit_share = estate / len(units)
            for unit in units:
                credit(unit, unit_share, source_id, heir_rank)

    if representation_depth_exceeded:
        return _unsupported_result(
            [_error("representation_depth_exceeded", "Thế vị vượt quá giới hạn chắt.")]
        )

    allocated = sum(holdings.values(), Fraction(0))
    unresolved = sum(
        (Fraction(item["fraction"]) for item in unresolved_estates), Fraction(0)
    )
    total = allocated + unresolved
    if total != 1:
        return _empty_result(
            [_error("conservation_failed", "Tổng tài sản sau tính toán không bằng 1.", total=_fraction_text(total))]
        )

    allocations: dict[str, dict[str, str]] = {}
    breakdowns: list[dict[str, Any]] = []
    for person_id in sorted(nodes_by_person):
        final_share = holdings[person_id]
        allocations[person_id] = {
            "baseShare": _fraction_text(base_shares[person_id]),
            "inheritedShare": _fraction_text(inherited_shares[person_id]),
            "distributedShare": _fraction_text(distributed_shares[person_id]),
            "finalShare": _fraction_text(final_share),
            "displayPercent": _percent_text(final_share),
        }
        if final_share > 0:
            breakdowns.append(
                {
                    "personId": person_id,
                    "total": _fraction_text(final_share),
                    "terms": terms[person_id],
                }
            )

    required_slots, slot_warnings = _required_slot_table(graph, active_estates)
    later_lines_unsupported = bool(unresolved_estates) and not ENABLE_LATER_LINES
    return {
        "engineVersion": ENGINE_VERSION,
        "status": ("unsupported" if later_lines_unsupported else "incomplete") if unresolved else "complete",
        "allocations": allocations,
        "breakdowns": breakdowns,
        "requiredSlots": required_slots,
        "warnings": slot_warnings,
        "errors": ([_error("second_order_required", "Chưa hỗ trợ hàng thừa kế 2/3 khi không có người thừa kế hàng 1.")]
                   if later_lines_unsupported else []),
        "unresolvedEstates": unresolved_estates,
        "conservation": {
            "allocated": _fraction_text(allocated),
            "unresolved": _fraction_text(unresolved),
            "total": _fraction_text(total),
        },
    }
