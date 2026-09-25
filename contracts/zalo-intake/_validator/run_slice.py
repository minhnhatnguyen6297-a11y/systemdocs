"""Per-slice case runner: loads ONLY the listed rules_*.py modules so parallel
work does not break on another slice's half-written file.

Usage (from the contract dir):
    python -m _validator.run_slice rules_record rec- gap-
    python -m _validator.run_slice rules_package,rules_receipt,rules_status pkg- seq- rcpt- status-

Args: comma-separated rule module names, then zero or more case-name prefixes
(no prefixes = run every discovered case). Exit 0 when all selected cases are ok.
"""
import sys
from pathlib import Path

from . import cases
from .cases import registry


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    modules = argv[0].split(",")
    prefixes = tuple(argv[1:])
    for name in modules:
        __import__(f"_validator.{name}")
    found = cases.discover_case_dirs(Path(__file__).resolve().parent.parent / "examples")
    if prefixes:
        found = [(g, d) for g, d in found if d.name.startswith(prefixes)]
    return cases.run_cases(found, "slice-run", registry, verbose=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
