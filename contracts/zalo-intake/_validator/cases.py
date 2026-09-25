"""Example-case discovery, validator registry and the pass/fail runner.

Layout: examples/{valid,invalid}/<case_name>/ — every entry inside a group folder is a case
directory holding a `case.json` plus the document files under test. `case.json` keys:
  kind             required string — selects the registered validator
  description      required string — what the case proves
  expected_errors  list of unique error-code strings; required non-empty under invalid/,
                   absent or empty under valid/
  context          optional object — pure data for the validator (fixed clock, prior state...)

A validator is fn(case_dir, case) -> list[(code, detail)]; it chooses which files to read.
Rule modules (`_validator/rules_*.py`) call register()/register_error_codes() at import.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from .io import ContractDataError, read_json_bytes
from .schema_subset import SCHEMA_INVALID

GROUPS = ("valid", "invalid")
CASE_KEYS = {"kind", "description", "expected_errors", "context"}
_CODE_SHAPE = re.compile(r"[a-z0-9_]+")


class CaseError(Exception):
    """The case directory / case.json is malformed — an authoring bug, not a document verdict."""


@dataclass
class Outcome:
    group: str
    name: str
    expected: list = field(default_factory=list)     # sorted error codes
    produced: list = field(default_factory=list)     # sorted unique (code, detail)
    problems: list = field(default_factory=list)     # framework problems: case failed regardless
    case: dict | None = None

    @property
    def ok(self):
        return not self.problems and {c for c, _ in self.produced} == set(self.expected)


class Registry:
    """kind -> validator plus the error-code catalog (always contains the three builtins)."""

    def __init__(self):
        self.validators = {}
        self.error_codes = {SCHEMA_INVALID, "json_invalid", "records_format_invalid"}

    def register(self, kind, fn=None):
        """register("kind", fn) or @register("kind"); fn(case_dir, case) -> [(code, detail)]."""
        if fn is None:
            return lambda f: self.register(kind, f)
        if not (isinstance(kind, str) and kind):
            raise TypeError("kind must be a non-empty string")
        if not callable(fn):
            raise TypeError("validator must be callable")
        if kind in self.validators:
            raise ValueError(f"kind {kind!r} is already registered")
        self.validators[kind] = fn
        return fn

    def register_error_codes(self, codes):
        """Add stable error codes to the catalog; a case fails if it uses an unknown code."""
        if isinstance(codes, str):
            raise TypeError("pass an iterable of error codes, not a bare string")
        for code in codes:
            if not (isinstance(code, str) and _CODE_SHAPE.fullmatch(code)):
                raise ValueError(f"invalid error code {code!r}")
            self.error_codes.add(code)


registry = Registry()          # module default; rule modules register here
register = registry.register
register_error_codes = registry.register_error_codes


def discover_case_dirs(examples_dir) -> list:
    """[(group, case_dir)] — every entry of examples/valid|invalid, name-sorted, valid first."""
    found = []
    for group in GROUPS:
        gdir = Path(examples_dir) / group
        if gdir.is_dir():
            found += [(group, p) for p in sorted(gdir.iterdir(), key=lambda p: p.name)]
    return found


def load_case(case_dir) -> dict:
    """Parse and check case.json; normalizes expected_errors/context to [].{}; raises CaseError."""
    case_dir = Path(case_dir)
    if not case_dir.is_dir():
        raise CaseError(f"{case_dir.name}: not a case directory")
    path = case_dir / "case.json"
    if not path.is_file():
        raise CaseError(f"{case_dir.name}: missing case.json")
    try:
        case = read_json_bytes(path.read_bytes())
    except ContractDataError as e:
        raise CaseError(f"{case_dir.name}/case.json: {e.code} {e.detail}") from e
    if not isinstance(case, dict):
        raise CaseError(f"{case_dir.name}/case.json: not a JSON object")
    unknown = sorted(set(case) - CASE_KEYS)
    if unknown:
        raise CaseError(f"{case_dir.name}/case.json: unknown key(s) {', '.join(unknown)}")
    for key in ("kind", "description"):
        if not (isinstance(case.get(key), str) and case[key]):
            raise CaseError(f"{case_dir.name}/case.json: {key!r} must be a non-empty string")
    expected = case.get("expected_errors", [])
    if not (isinstance(expected, list)
            and all(isinstance(c, str) and c for c in expected)
            and len(set(expected)) == len(expected)):
        raise CaseError(f"{case_dir.name}/case.json: expected_errors must be unique strings")
    if "context" in case and not isinstance(case["context"], dict):
        raise CaseError(f"{case_dir.name}/case.json: context must be an object")
    case.setdefault("expected_errors", [])
    case.setdefault("context", {})
    return case


def execute(case_dir, case, reg) -> list:
    """Run the registered validator for case['kind'] -> sorted unique [(code, detail)].

    Unknown kinds raise CaseError (the caller reports it as a case problem, no crash);
    a raised ContractDataError converts to its carried (code, detail). Anything else a
    validator does wrong (including returning malformed results) raises — a broken rule
    module must be loud.
    """
    fn = reg.validators.get(case["kind"])
    if fn is None:
        raise CaseError(f"unknown kind {case['kind']!r} (no rules_*.py registered it)")
    try:
        produced = fn(Path(case_dir), case)
    except ContractDataError as e:
        produced = [(e.code, e.detail)]
    if not (isinstance(produced, list) and all(
            isinstance(e, tuple) and len(e) == 2
            and all(isinstance(x, str) for x in e) for e in produced)):
        raise TypeError(
            f"validator for kind {case['kind']!r} must return a list of (code, detail) tuples, "
            f"got {type(produced).__name__}")
    return sorted(set(produced))


def check_case(case_dir, group: str, reg) -> Outcome:
    """Evaluate one case; never raises for bad cases — the problem lands in Outcome.problems."""
    case_dir = Path(case_dir)
    try:
        case = load_case(case_dir)
    except CaseError as e:
        return Outcome(group, case_dir.name, problems=[str(e)])
    problems = []
    expected = sorted(case["expected_errors"])
    if group == "invalid" and not expected:
        problems.append("invalid case has no expected_errors")
    if group == "valid" and expected:
        problems.append("valid case must not declare expected_errors")
    try:
        produced = execute(case_dir, case, reg)
    except CaseError as e:
        produced = []
        problems.append(str(e))
    unknown = sorted((set(expected) | {c for c, _ in produced}) - reg.error_codes)
    if unknown:
        problems.append(f"unknown error code(s) {', '.join(unknown)} (not in the catalog)")
    return Outcome(group, case_dir.name, expected, produced, problems, case)


def _report_lines(o: Outcome, verbose: bool) -> list:
    exp = "[" + ", ".join(o.expected) + "]"
    got = "[" + ", ".join(sorted({c for c, _ in o.produced})) + "]"
    head = f"[{o.group}] {o.name}: "
    if o.problems:
        lines = [head + f"expected={exp} got={got} -> ERROR " + "; ".join(o.problems)]
    elif o.group == "invalid":
        lines = [head + f"expected={exp} got={got} -> "
                 + ("REJECTED-CORRECTLY" if o.ok else "MISMATCH")]
    else:
        lines = [head + ("PASS" if o.ok else f"FAIL got={got}")]
    if verbose and o.case and o.case.get("description"):
        lines.insert(0, f"    # {o.case['description']}")
    if o.produced and (verbose or not o.ok):
        lines += [f"    {c} {d}" for c, d in o.produced]
    return lines


def run_cases(found, revision: str, reg, out=print, verbose: bool = False) -> int:
    """Print one line per case plus the summary; returns 0 or 1 (non-zero on any surprise)."""
    outcomes = [check_case(d, g, reg) for g, d in found]
    for o in outcomes:
        for line in _report_lines(o, verbose):
            out(line)
    unexpected = sum(not o.ok for o in outcomes)
    n_valid = sum(o.group == "valid" for o in outcomes)
    n_invalid = len(outcomes) - n_valid
    out(f"{n_valid} valid, {n_invalid} invalid, {unexpected} unexpected outcomes; "
        f"contract={revision}")
    return 1 if unexpected or not outcomes else 0


def case_files(case_dir) -> list:
    """Every document file under a case dir (recursive, sorted, root case.json excluded)."""
    case_dir = Path(case_dir)
    return sorted(p for p in case_dir.rglob("*")
                  if p.is_file() and p != case_dir / "case.json")
