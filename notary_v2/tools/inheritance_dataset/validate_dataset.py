#!/usr/bin/env python3
"""Validate inheritance dataset JSON against its schema and reference results."""
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_DIR = ROOT / "tests" / "fixtures" / "inheritance_dataset"
from reference_solver import solve


def schema_errors(document, schema):
    try:
        import jsonschema
    except ImportError:
        errors = []
        if not isinstance(document, dict) or set(document) != {"family", "cases"}:
            return ["family file must contain exactly family and cases"]
        if not isinstance(document["family"], str) or not isinstance(document["cases"], list):
            return ["family must be a string and cases an array"]
        case_required = {"id", "family", "title", "rules", "asset_count", "people", "diagram", "action", "expected"}
        node_required = {"id", "personId", "parentSlotIds", "spouseSlotId", "ownPositions", "receivePositions", "hidden", "deleted"}
        for i, case in enumerate(document["cases"]):
            if not isinstance(case, dict) or not case_required <= case.keys():
                errors.append(f"case {i}: missing required fields")
                continue
            if not 1 <= case["asset_count"] <= 3 or not isinstance(case["asset_count"], int):
                errors.append(f"case {i}: asset_count must be 1..3")
            diagram = case["diagram"]
            if not isinstance(diagram, dict) or diagram.get("version") != 3 or diagram.get("domain") != "inheritance" or not isinstance(diagram.get("nodes"), list):
                errors.append(f"case {i}: invalid diagram contract")
                continue
            for j, node in enumerate(diagram["nodes"]):
                if not isinstance(node, dict) or not node_required <= node.keys():
                    errors.append(f"case {i} node {j}: missing required fields")
                    continue
                if any(not isinstance(pos, int) or pos < 1 or pos > case["asset_count"] for key in ("ownPositions", "receivePositions") for pos in node[key]):
                    errors.append(f"case {i} node {j}: invalid asset position")
        return errors
    validator = jsonschema.Draft202012Validator(schema)
    return [f"schema: {e.message} at {list(e.absolute_path)}" for e in validator.iter_errors(document)]


def check_file(path, schema):
    errors = []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]
    errors.extend(schema_errors(document, schema))
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list):
        return errors
    if document.get("family") is not None:
        for index, case in enumerate(document["cases"]):
            if isinstance(case, dict) and case.get("family") != document["family"]:
                errors.append(f"case {index}: family differs from file family")
    seen = set()
    for index, case in enumerate(document["cases"]):
        label = case.get("id", f"#{index}") if isinstance(case, dict) else f"#{index}"
        prefix = f"case {label}"
        if not isinstance(case, dict):
            continue
        if case.get("id") in seen:
            errors.append(f"{prefix}: duplicate id")
        seen.add(case.get("id"))
        people = case.get("people", {})
        diagram = case.get("diagram", {})
        nodes = diagram.get("nodes", []) if isinstance(diagram, dict) else []
        node_ids = [n.get("id") for n in nodes if isinstance(n, dict)]
        if len(node_ids) != len(set(node_ids)):
            errors.append(f"{prefix}: node ids must be unique")
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("personId") not in people:
                errors.append(f"{prefix}: unknown personId {node.get('personId')}")
            for key in ("ownPositions", "receivePositions"):
                for pos in node.get(key, []):
                    if not isinstance(pos, int) or pos < 1 or pos > case.get("asset_count", 0):
                        errors.append(f"{prefix}: {key} position {pos} outside asset_count")
        for asset, recipients in case.get("expected", {}).get("shares", {}).items():
            for person_id in recipients:
                if person_id not in people:
                    errors.append(f"{prefix}: unknown expected personId {person_id}")
        expected = case.get("expected", {})
        for mapping_name in ("shares", "unresolved"):
            mapping = expected.get(mapping_name, {})
            for asset, values in mapping.items():
                try:
                    if not 1 <= int(asset) <= case.get("asset_count", 0):
                        raise ValueError("asset index out of range")
                    if mapping_name == "shares":
                        fractions = values.values()
                    else:
                        fractions = [values]
                    for raw in fractions:
                        frac = Fraction(raw)
                        if frac < 0:
                            raise ValueError("negative fraction")
                except (ValueError, TypeError, ZeroDivisionError) as exc:
                    errors.append(f"{prefix}: invalid {mapping_name} fraction/index: {exc}")
        if expected.get("status") == "pending":
            if not expected.get("pending_decision"):
                errors.append(f"{prefix}: pending case requires pending_decision")
            if expected.get("shares") or expected.get("unresolved"):
                errors.append(f"{prefix}: pending case must have empty shares and unresolved")
        if expected.get("status") in ("complete", "incomplete"):
            for asset in range(1, case.get("asset_count", 0) + 1):
                key = str(asset)
                try:
                    total = sum((Fraction(v) for v in expected.get("shares", {}).get(key, {}).values()), Fraction())
                    total += Fraction(expected.get("unresolved", {}).get(key, "0/1"))
                    if total != 1:
                        errors.append(f"{prefix}: asset {asset} totals {total}, expected 1")
                    if expected.get("status") == "complete" and Fraction(expected.get("unresolved", {}).get(key, "0/1")) != 0:
                        errors.append(f"{prefix}: complete case has unresolved value")
                except (ValueError, TypeError, ZeroDivisionError) as exc:
                    errors.append(f"{prefix}: invalid total for asset {asset}: {exc}")
        if expected:
            try:
                actual = solve(case)
                for key in ("status", "reasons", "shares", "unresolved", "remaining_node_ids", "pending_decision"):
                    if actual.get(key) != expected.get(key):
                        errors.append(f"{prefix}: expected {key}={expected.get(key)!r}, solver returned {actual.get(key)!r}")
            except Exception as exc:
                errors.append(f"{prefix}: reference solver failed: {type(exc).__name__}: {exc}")
    return errors


def main(argv=None):
    paths = [Path(arg) for arg in (sys.argv[1:] if argv is None else argv)]
    if not paths:
        paths = sorted(DEFAULT_DIR.glob("*.json")) if DEFAULT_DIR.exists() else []
    if not paths:
        print("No dataset files found.")
        return 1
    schema = json.loads((HERE / "schema.json").read_text(encoding="utf-8"))
    passed = failed = 0
    for path in paths:
        problems = check_file(path, schema)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            cases = document.get("cases", []) if isinstance(document, dict) else []
            counts = Counter(case.get("expected", {}).get("status", "unknown") for case in cases if isinstance(case, dict))
            distribution = ", ".join(f"{status}={count}" for status, count in sorted(counts.items())) or "none"
            print(f"FILE {path}: {len(cases)} case(s); status: {distribution}")
        except (OSError, json.JSONDecodeError):
            pass
        if problems:
            failed += 1
            print(f"FAIL {path}: {len(problems)} error(s)")
            for problem in problems:
                print(f"  - {problem}")
        else:
            passed += 1
            print(f"PASS {path}")
    print(f"Summary: {passed} passed, {failed} failed files")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
