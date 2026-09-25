"""Runs the contract's example cases — stdlib only, no services, no network.

    python validate_examples.py                        run every case under examples/, print summary
    python validate_examples.py --case valid/two_sides run one case verbosely
    python validate_examples.py --hashes valid/two_sides   size_bytes + sha256 of its document files

The script puts its own directory on sys.path, imports `_validator`, then auto-imports every
`_validator/rules_*.py` (each registers its case kinds and error codes at import time).
Everything is located relative to this file, so the contract folder can move unchanged.

Public helpers (for tests and rule authors):
    load_example("valid/two_sides") -> (case_dir: Path, case: dict)
    run_case("valid/two_sides")     -> list[(code, detail)]
    contract_revision()             -> str
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _validator import CONTRACT_DIR            # noqa: E402
from _validator import cases                   # noqa: E402
from _validator.cases import registry          # noqa: E402
from _validator.io import sha256_hex           # noqa: E402

EXAMPLES = CONTRACT_DIR / "examples"
REVISION_FILE = CONTRACT_DIR / "CONTRACT_REVISION"

for _rule_file in sorted(CONTRACT_DIR.glob("_validator/rules_*.py"), key=lambda p: p.name):
    importlib.import_module(f"_validator.{_rule_file.stem}")


def contract_revision() -> str:
    """First line of CONTRACT_REVISION if present and non-empty, else 'unversioned-draft'."""
    if REVISION_FILE.is_file():
        lines = REVISION_FILE.read_bytes().decode("utf-8", "replace").splitlines()
        if lines and lines[0].strip():
            return lines[0].strip()
    return "unversioned-draft"


def _resolve_case(relpath) -> Path:
    """'valid/<name>' or 'invalid/<name>' (an 'examples/' prefix is tolerated) -> Path."""
    parts = Path(str(relpath)).parts
    if len(parts) == 3 and parts[0] == "examples":
        parts = parts[1:]
    if len(parts) != 2 or parts[0] not in cases.GROUPS:
        raise ValueError(f"case path must be 'valid/<name>' or 'invalid/<name>', got {relpath!r}")
    return EXAMPLES / parts[0] / parts[1]


def load_example(relpath):
    """Return (case_dir, parsed case.json dict) for a case path like 'valid/two_sides'."""
    case_dir = _resolve_case(relpath)
    return case_dir, cases.load_case(case_dir)


def run_case(relpath) -> list:
    """Run the registered validator for one case -> sorted [(code, detail)] (raises CaseError)."""
    case_dir, case = load_example(relpath)
    return cases.execute(case_dir, case, registry)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")  # console encodings must not crash us
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--case", metavar="GROUP/NAME",
                      help="run a single case verbosely, e.g. valid/two_sides")
    mode.add_argument("--hashes", metavar="GROUP/NAME",
                      help="print size_bytes + sha256 of the case's document files")
    args = parser.parse_args(argv)

    if args.hashes:
        try:
            case_dir = _resolve_case(args.hashes)
        except ValueError as e:
            parser.error(str(e))
        if not case_dir.is_dir():
            parser.error(f"no such case directory: {args.hashes}")
        files = cases.case_files(case_dir)
        if not files:
            print(f"{case_dir.name}: no document files")
        for path in files:
            data = path.read_bytes()
            print(f"{path.relative_to(case_dir).as_posix()} "
                  f"size_bytes={len(data)} sha256={sha256_hex(data)}")
        return 0

    if args.case:
        try:
            case_dir = _resolve_case(args.case)
        except ValueError as e:
            parser.error(str(e))
        found = [(case_dir.parent.name, case_dir)]
        return cases.run_cases(found, contract_revision(), registry, verbose=True)

    found = cases.discover_case_dirs(EXAMPLES)
    if not found:
        print(f"no cases found under {EXAMPLES}")
    return cases.run_cases(found, contract_revision(), registry)


if __name__ == "__main__":
    sys.exit(main())
