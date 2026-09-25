"""Slice-A case runner — identical to `_validator.run_slice` but with a working
registry import (`from . import cases, registry` there cannot resolve `registry`,
which lives in `_validator.cases`, not in the package namespace). Kept private to
slice A so half-written rule modules of other slices cannot break this run.

Usage (from the contract dir):
    python examples/_build/run_slice_a.py [prefix ...]

No prefixes = every discovered case under examples/{valid,invalid}.
Exit 0 when all selected cases are ok.
"""
import sys
from pathlib import Path

CONTRACT_DIR = Path(__file__).resolve().parents[2]
if str(CONTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_DIR))

from _validator import cases  # noqa: E402
from _validator.cases import registry  # noqa: E402

RULE_MODULES = ("rules_package", "rules_receipt", "rules_status")


def main(argv) -> int:
    prefixes = tuple(argv)
    for name in RULE_MODULES:
        __import__(f"_validator.{name}")
    found = cases.discover_case_dirs(CONTRACT_DIR / "examples")
    if prefixes:
        found = [(g, d) for g, d in found if d.name.startswith(prefixes)]
    return cases.run_cases(found, "slice-a-run", registry, verbose=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
