"""Independent reference implementation of inheritance rules R-07–R-29."""
from datetime import date
from fractions import Fraction


def _date(value):
    if not value:
        return None
    try:
        if len(value) == 4:
            return (int(value), None)
        day, month, year = map(int, value.split("/"))
        return (year, date(year, month, day).timetuple().tm_yday)
    except (ValueError, TypeError):
        return None


def _order(a, b):
    """Return -1/0/1 when a precedes/equal/follows b, else None."""
    if a is None or b is None:
        return None
    if a[0] != b[0]:
        return -1 if a[0] < b[0] else 1
    if a[1] is None or b[1] is None:
        return 0 if a[1] is b[1] is None else None
    return (a[1] > b[1]) - (a[1] < b[1])


def _fraction(value):
    return f"{value.numerator}/{value.denominator}"


def solve(case):
    nodes = {n["id"]: n.copy() for n in case["diagram"]["nodes"] if not n.get("deleted")}
    reasons = []
    action = case.get("action")
    if action and action.get("type") == "delete_root":
        root = nodes.get(action["nodeId"])
        if root:
            removed = {root["id"]}
            changed = True
            while changed:
                changed = False
                for node in nodes.values():
                    if node["id"] not in removed and any(parent in removed for parent in node["parentSlotIds"]):
                        removed.add(node["id"])
                        changed = True
            spouse_id = root.get("spouseSlotId")
            spouse = nodes.get(spouse_id)
            if spouse:
                if spouse.get("ownPositions"):
                    removed.discard(spouse_id)
                else:
                    removed.add(spouse_id)
            nodes = {key: node for key, node in nodes.items() if key not in removed}
            for node in nodes.values():
                node["parentSlotIds"] = [parent for parent in node["parentSlotIds"] if parent in nodes]
                if node.get("spouseSlotId") not in nodes:
                    node["spouseSlotId"] = None
    remaining = sorted(nodes)
    ids = set(nodes)
    for n in nodes.values():
        parents = n["parentSlotIds"]
        if len(parents) > 2:
            reasons.append("too_many_parents")
        if n["id"] in parents:
            reasons.append("self_parent")
        if any(p not in ids for p in parents):
            reasons.append("dangling_parent")
        spouse = n.get("spouseSlotId")
        if spouse == n["id"]:
            reasons.append("self_spouse")
        elif spouse:
            other = nodes.get(spouse)
            if other is None or other.get("spouseSlotId") != n["id"]:
                reasons.append("spouse_conflict")
    # Detect directed ancestry cycles; converging paths are valid.
    visiting, visited = set(), set()
    def cycle(node_id):
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        found = any(parent in ids and cycle(parent) for parent in nodes[node_id]["parentSlotIds"])
        visiting.remove(node_id)
        visited.add(node_id)
        return found
    if any(cycle(nid) for nid in ids if nid not in visited):
        reasons.append("ancestry_cycle")
    if reasons:
        return {"status": "invalid", "reasons": sorted(set(reasons)), "shares": {}, "unresolved": {}, "remaining_node_ids": remaining if action else None, "pending_decision": None}
    people = case["people"]
    person_nodes = {}
    for n in nodes.values():
        person_nodes.setdefault(n["personId"], []).append(n)
    # Use the first stable node for a person; links identify actual graph slots.
    parent_ids = {p: set() for p in people}
    children = {p: set() for p in people}
    spouses = {}
    for n in nodes.values():
        p = n["personId"]
        for parent_node_id in n["parentSlotIds"]:
            parent_person = nodes[parent_node_id]["personId"]
            parent_ids.setdefault(p, set()).add(parent_person)
            children.setdefault(parent_person, set()).add(p)
        if n.get("spouseSlotId"):
            spouses[p] = nodes[n["spouseSlotId"]]["personId"]
    meta = case.get("meta", {})
    pending_decision = None
    if meta.get("land_type") == "ho_gia_dinh":
        pending_decision = "Q-014"
    elif meta.get("merged_estate"):
        pending_decision = "Q-015"
    elif any(
        person_id in people and not people[person_id].get("ngay_chet")
        for person_id in meta.get("parent_died_long_ago_person_ids", [])
    ):
        pending_decision = "Q-013"
    if pending_decision:
        return {"status": "pending", "reasons": [], "shares": {}, "unresolved": {}, "remaining_node_ids": remaining if action else None, "pending_decision": pending_decision}
    death = {p: _date(info.get("ngay_chet")) for p, info in people.items()}
    overall = "complete"
    output_shares, output_unresolved = {}, {}
    for asset in range(1, case["asset_count"] + 1):
        holdings = {}
        unresolved = Fraction(0)
        for n in nodes.values():
            if asset in n["ownPositions"]:
                holdings[n["personId"]] = holdings.get(n["personId"], Fraction()) + Fraction(1, sum(asset in x["ownPositions"] for x in nodes.values()))
        deaths = sorted({d for p, d in death.items() if d is not None and any(n["personId"] == p for n in nodes.values())}, key=lambda x: (x[0], -1 if x[1] is None else x[1]))
        processed = set()
        for when in deaths:
            batch = [(p, holdings.get(p, Fraction())) for p in people if death[p] == when and p not in processed]
            processed.update(p for p, _ in batch)
            batch_total = {p: value for p, value in batch if value > 0}
            for decedent, value in batch_total.items():
                holdings[decedent] = Fraction(0)
                if not value:
                    continue
                units = []
                # First-degree relations alive, explicitly receiving, or later-deceased (automatic acceptance).
                direct = list(parent_ids.get(decedent, ())) + ([spouses[decedent]] if decedent in spouses else [])
                for person in sorted(set(direct)):
                    rel = _order(when, death.get(person))
                    receiving = any(asset in n["receivePositions"] for n in person_nodes.get(person, []))
                    if rel == -1:
                        units.append(("person", person))
                    elif death.get(person) is None and receiving:
                        units.append(("person", person))
                for child in sorted(children.get(decedent, ())):
                    rel = _order(death.get(child), when)
                    if death.get(child) is not None and rel == 1:
                        units.append(("person", child))
                    elif death.get(child) is not None and rel in (-1, 0, None):
                        branch, exceeded = _branch(child, children, death, person_nodes, asset, when)
                        if exceeded:
                            reasons.append("representation_depth_exceeded")
                        elif branch:
                            units.append(("branch", branch))
                    elif death.get(child) is None and any(asset in n["receivePositions"] for n in person_nodes.get(child, [])):
                        units.append(("person", child))
                if reasons:
                    return {"status": "unsupported", "reasons": sorted(set(reasons)), "shares": {}, "unresolved": {}, "remaining_node_ids": remaining if action else None, "pending_decision": None}
                if not units:
                    if _has_lower_rank_heirs(decedent, parent_ids, children, death, when):
                        return {"status": "unsupported", "reasons": ["heir_rank_not_supported"], "shares": {}, "unresolved": {}, "remaining_node_ids": remaining if action else None, "pending_decision": "Q-016"}
                    unresolved += value
                    overall = "incomplete"
                    continue
                portion = value / len(units)
                for kind, recipient in units:
                    if kind == "person":
                        holdings[recipient] = holdings.get(recipient, Fraction()) + portion
                    elif recipient:
                        for person in recipient:
                            holdings[person] = holdings.get(person, Fraction()) + portion / len(recipient)
        output_shares[str(asset)] = {p: _fraction(v) for p, v in sorted(holdings.items()) if v > 0}
        output_unresolved[str(asset)] = _fraction(unresolved)
    return {"status": overall, "reasons": [], "shares": output_shares, "unresolved": output_unresolved, "remaining_node_ids": remaining if action else None, "pending_decision": None}


def _has_lower_rank_heirs(decedent, parent_ids, children, death, when):
    """Detect eligible siblings and their descendants connected through a shared parent."""
    siblings = {
        sibling
        for parent in parent_ids.get(decedent, ())
        for sibling in children.get(parent, ())
        if sibling != decedent
    }
    for sibling in siblings:
        if death.get(sibling) is None or _order(when, death.get(sibling)) == -1:
            return True
        frontier = list(children.get(sibling, ()))
        visited = set()
        while frontier:
            person = frontier.pop()
            if person in visited:
                continue
            visited.add(person)
            if death.get(person) is None or _order(when, death.get(person)) == -1:
                return True
            frontier.extend(children.get(person, ()))
    return False


def _branch(child, children, death, person_nodes, asset, ancestor_death):
    """Find eligible recipients within a representation branch, through great-grandchildren."""
    frontier = [(child, 0)]
    while frontier:
        next_frontier = []
        accepted = []
        for person, depth in frontier:
            rel = _order(death.get(person), ancestor_death)
            receiving = any(asset in n["receivePositions"] for n in person_nodes.get(person, []))
            descendants = sorted(children.get(person, ()))
            if death.get(person) is None:
                if receiving:
                    accepted.append(person)
                elif descendants:
                    if depth >= 2:
                        return [], True
                    next_frontier.extend((c, depth + 1) for c in descendants)
            elif rel == 1:
                accepted.append(person)
            elif rel in (-1, 0, None):
                if depth >= 2 and descendants:
                    return [], True
                next_frontier.extend((c, depth + 1) for c in descendants)
        if accepted:
            return accepted, False
        frontier = next_frontier
    return [], False
