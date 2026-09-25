import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _validator import cases
from _validator.io import read_json_bytes

STAGE = Path(__file__).resolve().parents[2]  # the contract folder holding validate_examples.py


def v_flag(case_dir, case):
    doc = read_json_bytes((case_dir / "doc.json").read_bytes())
    return [] if doc.get("ok") is True else [("not_ok", "doc.json: ok is not true")]


def v_io(case_dir, case):
    read_json_bytes((case_dir / "doc.json").read_bytes())
    return []


def v_ctx(case_dir, case):
    if case["context"].get("expect", True):
        return []
    return [("ctx_bad", "context.expect is false")]


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = cases.Registry()

    def test_builtin_codes_are_always_present(self):
        self.assertTrue({"schema_invalid", "json_invalid", "records_format_invalid"}
                        <= self.registry.error_codes)

    def test_register_function_and_decorator_forms(self):
        self.registry.register("a", v_flag)
        @self.registry.register("b")
        def check(case_dir, case):
            return []
        self.assertIs(self.registry.validators["a"], v_flag)
        self.assertIs(self.registry.validators["b"], check)

    def test_duplicate_kind_and_bad_arguments_rejected(self):
        self.registry.register("a", v_flag)
        with self.assertRaises(ValueError):
            self.registry.register("a", v_flag)
        with self.assertRaises(TypeError):
            self.registry.register("b", "not callable")
        with self.assertRaises(TypeError):
            self.registry.register(5, v_flag)

    def test_register_error_codes(self):
        self.registry.register_error_codes(["not_ok", "ctx_bad"])
        self.assertTrue({"not_ok", "ctx_bad"} <= self.registry.error_codes)
        with self.assertRaises(TypeError):
            self.registry.register_error_codes("not_ok")  # a bare string, not an iterable
        for bad in ("NotOk", "has space", "", 5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.registry.register_error_codes([bad])


class CaseDirMixin(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.examples = self.dir / "examples"
        self.registry = cases.Registry()
        self.registry.register("flag", v_flag)
        self.registry.register("io", v_io)
        self.registry.register("ctx", v_ctx)
        self.registry.register_error_codes({"not_ok", "ctx_bad"})

    def mk(self, group, name, case, files=None):
        case_dir = self.examples / group / name
        case_dir.mkdir(parents=True, exist_ok=True)
        raw = case if isinstance(case, bytes) else json.dumps(case).encode("utf-8")
        (case_dir / "case.json").write_bytes(raw)
        for rel, data in (files or {}).items():
            target = case_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return case_dir


class LoadCaseTests(CaseDirMixin):
    def test_loads_and_normalizes(self):
        d = self.mk("valid", "a", {"kind": "flag", "description": "d"})
        case = cases.load_case(d)
        self.assertEqual(case["kind"], "flag")
        self.assertEqual(case["expected_errors"], [])
        self.assertEqual(case["context"], {})

    def test_rejects_malformed_case_dirs(self):
        for label, make in (
            ("not a dir", lambda: self.examples / "valid" / "ghost"),
            ("no case.json", lambda: self.mk("valid", "a", None)),
            ("bad json", lambda: self.mk("valid", "a", b"{")),
            ("not an object", lambda: self.mk("valid", "a", [1])),
            ("no kind", lambda: self.mk("valid", "a", {"description": "d"})),
            ("kind not str", lambda: self.mk("valid", "a", {"kind": 1, "description": "d"})),
            ("no description", lambda: self.mk("valid", "a", {"kind": "flag"})),
            ("unknown key", lambda: self.mk("valid", "a",
                {"kind": "flag", "description": "d", "expected_error": ["x"]})),
            ("expected_errors dup", lambda: self.mk("invalid", "a",
                {"kind": "flag", "description": "d", "expected_errors": ["x", "x"]})),
            ("expected_errors not list", lambda: self.mk("invalid", "a",
                {"kind": "flag", "description": "d", "expected_errors": "x"})),
            ("expected_errors not str", lambda: self.mk("invalid", "a",
                {"kind": "flag", "description": "d", "expected_errors": [1]})),
            ("context not object", lambda: self.mk("valid", "a",
                {"kind": "flag", "description": "d", "context": [1]})),
        ):
            with self.subTest(label=label):
                target = make()
                if label == "not a dir":
                    (self.examples / "valid").mkdir(parents=True, exist_ok=True)
                if label == "no case.json":
                    (target / "case.json").unlink()
                with self.assertRaises(cases.CaseError):
                    cases.load_case(target)

    def test_case_json_parse_failure_is_a_case_error(self):
        d = self.mk("valid", "a", b'{"kind": "x", "kind": "y"}')
        with self.assertRaises(cases.CaseError) as ctx:
            cases.load_case(d)
        self.assertIn("json_invalid", str(ctx.exception))


class CheckCaseTests(CaseDirMixin):
    def test_valid_case_passes_only_when_produced_is_empty(self):
        good = self.mk("valid", "two_sides", {"kind": "flag", "description": "d"},
                       {"doc.json": b'{"ok": true}'})
        bad = self.mk("valid", "not_ok", {"kind": "flag", "description": "d"},
                      {"doc.json": b'{"ok": false}'})
        self.assertTrue(cases.check_case(good, "valid", self.registry).ok)
        outcome = cases.check_case(bad, "valid", self.registry)
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.produced, [("not_ok", "doc.json: ok is not true")])

    def test_invalid_case_needs_exactly_the_expected_code_set(self):
        d = self.mk("invalid", "a", {"kind": "flag", "description": "d",
                                     "expected_errors": ["not_ok"]},
                    {"doc.json": b'{"ok": false}'})
        self.assertTrue(cases.check_case(d, "invalid", self.registry).ok)
        for expected in (["other_code"], ["not_ok", "extra"], []):
            with self.subTest(expected=expected):
                self.registry.register_error_codes(expected)
                d = self.mk("invalid", "a", {"kind": "flag", "description": "d",
                                             "expected_errors": expected},
                            {"doc.json": b'{"ok": false}'})
                self.assertFalse(cases.check_case(d, "invalid", self.registry).ok)

    def test_invalid_case_with_no_expected_errors_is_a_problem(self):
        d = self.mk("invalid", "a", {"kind": "flag", "description": "d"},
                    {"doc.json": b'{"ok": false}'})
        outcome = cases.check_case(d, "invalid", self.registry)
        self.assertFalse(outcome.ok)
        self.assertTrue(any("expected_errors" in p for p in outcome.problems))

    def test_valid_case_must_not_declare_expected_errors(self):
        d = self.mk("valid", "a", {"kind": "flag", "description": "d",
                                   "expected_errors": ["not_ok"]},
                    {"doc.json": b'{"ok": false}'})
        self.assertFalse(cases.check_case(d, "valid", self.registry).ok)

    def test_unknown_kind_fails_the_case_without_crashing(self):
        d = self.mk("valid", "a", {"kind": "nope", "description": "d"})
        outcome = cases.check_case(d, "valid", self.registry)
        self.assertFalse(outcome.ok)
        self.assertTrue(any("unknown kind" in p for p in outcome.problems))

    def test_produced_or_expected_codes_must_be_in_the_catalog(self):
        self.registry.register("loud", lambda d, c: [("typo_code", "x")])
        d = self.mk("valid", "a", {"kind": "loud", "description": "d"})
        outcome = cases.check_case(d, "valid", self.registry)
        self.assertFalse(outcome.ok)
        self.assertTrue(any("typo_code" in p for p in outcome.problems))
        d = self.mk("invalid", "a", {"kind": "flag", "description": "d",
                                     "expected_errors": ["manifst_hash"]},
                    {"doc.json": b'{"ok": false}'})
        outcome = cases.check_case(d, "invalid", self.registry)
        self.assertFalse(outcome.ok)
        self.assertTrue(any("manifst_hash" in p for p in outcome.problems))

    def test_typed_io_errors_become_produced_codes(self):
        d = self.mk("invalid", "a", {"kind": "io", "description": "d",
                                     "expected_errors": ["json_invalid"]},
                    {"doc.json": b'{broken'})
        outcome = cases.check_case(d, "invalid", self.registry)
        self.assertTrue(outcome.ok)
        self.assertEqual(outcome.produced[0][0], "json_invalid")

    def test_context_is_pure_data_for_the_validator(self):
        d = self.mk("invalid", "a", {"kind": "ctx", "description": "d",
                                     "context": {"expect": False},
                                     "expected_errors": ["ctx_bad"]})
        self.assertTrue(cases.check_case(d, "invalid", self.registry).ok)

    def test_produced_errors_are_sorted_and_deduplicated(self):
        self.registry.register("multi", lambda d, c: [("b_code", "d2"), ("a_code", "d1"),
                                                      ("a_code", "d1")])
        self.registry.register_error_codes(["a_code", "b_code"])
        d = self.mk("invalid", "a", {"kind": "multi", "description": "d",
                                     "expected_errors": ["a_code", "b_code"]})
        outcome = cases.check_case(d, "invalid", self.registry)
        self.assertEqual(outcome.produced, [("a_code", "d1"), ("b_code", "d2")])

    def test_a_validator_returning_garbage_crashes_loudly(self):
        for i, bad in enumerate((None, ["x"], [("a",)], [5], [("a", 1)])):
            with self.subTest(bad=bad):
                self.registry.register(f"bad{i}", lambda d, c, v=bad: v)
                d = self.mk("valid", "a", {"kind": f"bad{i}", "description": "d"})
                with self.assertRaises(TypeError):
                    cases.check_case(d, "valid", self.registry)


class DiscoverAndRunTests(CaseDirMixin):
    def test_discovers_valid_then_invalid_sorted_by_name(self):
        self.mk("valid", "b", {"kind": "flag", "description": "d"})
        self.mk("valid", "a", {"kind": "flag", "description": "d"})
        self.mk("invalid", "d", {"kind": "flag", "description": "d", "expected_errors": ["x"]})
        self.mk("invalid", "c", {"kind": "flag", "description": "d", "expected_errors": ["x"]})
        self.registry.register_error_codes(["x"])
        found = cases.discover_case_dirs(self.examples)
        self.assertEqual([(g, p.name) for g, p in found],
                         [("valid", "a"), ("valid", "b"), ("invalid", "c"), ("invalid", "d")])

    def test_missing_examples_dir_finds_nothing(self):
        self.assertEqual(cases.discover_case_dirs(self.dir / "absent"), [])

    def test_a_stray_file_inside_a_group_becomes_a_failing_case(self):
        d = self.mk("valid", "a", {"kind": "flag", "description": "d"})
        stray = self.examples / "valid" / "stray.json"
        stray.write_bytes(b"{}")
        found = cases.discover_case_dirs(self.examples)
        names = [p.name for _, p in found]
        self.assertIn("stray.json", names)
        outcome = cases.check_case(stray, "valid", self.registry)
        self.assertFalse(outcome.ok)

    def test_case_files_lists_documents_but_not_root_case_json(self):
        d = self.mk("valid", "a", {"kind": "flag", "description": "d"},
                    {"doc.json": b"{}", "sub/nested.json": b"{}", "sub/case.json": b"{}"})
        rel = [p.relative_to(d).as_posix() for p in cases.case_files(d)]
        self.assertEqual(rel, ["doc.json", "sub/case.json", "sub/nested.json"])

    def run_it(self, cases_found, revision="testrev"):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cases.run_cases(cases_found, revision, self.registry)
        return rc, buf.getvalue().splitlines()

    def test_run_cases_output_and_exit_code(self):
        self.mk("valid", "two_sides", {"kind": "flag", "description": "d"},
                {"doc.json": b'{"ok": true}'})
        self.mk("invalid", "manifest_bad", {"kind": "flag", "description": "d",
                                            "expected_errors": ["not_ok"]},
                {"doc.json": b'{"ok": false}'})
        rc, lines = self.run_it(cases.discover_case_dirs(self.examples))
        self.assertEqual(rc, 0)
        self.assertIn("[valid] two_sides: PASS", lines)
        self.assertIn("[invalid] manifest_bad: expected=[not_ok] got=[not_ok] -> REJECTED-CORRECTLY",
                      lines)
        self.assertEqual(lines[-1], "1 valid, 1 invalid, 0 unexpected outcomes; contract=testrev")

    def test_mismatch_prints_details_and_fails(self):
        self.mk("invalid", "wrong_reason", {"kind": "flag", "description": "d",
                                            "expected_errors": ["other_code"]},
                {"doc.json": b'{"ok": false}'})
        self.registry.register_error_codes(["other_code"])
        rc, lines = self.run_it(cases.discover_case_dirs(self.examples))
        self.assertEqual(rc, 1)
        self.assertIn("[invalid] wrong_reason: expected=[other_code] got=[not_ok] -> MISMATCH",
                      lines)
        self.assertTrue(any(line.strip().startswith("not_ok ") for line in lines))
        self.assertEqual(lines[-1], "0 valid, 1 invalid, 1 unexpected outcomes; contract=testrev")

    def test_zero_cases_exits_1(self):
        rc, lines = self.run_it([])
        self.assertEqual(rc, 1)
        self.assertEqual(lines[-1], "0 valid, 0 invalid, 0 unexpected outcomes; contract=testrev")


TOY_RULES = '''from _validator.cases import register, register_error_codes
from _validator.io import read_json_bytes

register_error_codes(["not_ok"])


@register("flag")
def check(case_dir, case):
    doc = read_json_bytes((case_dir / "doc.json").read_bytes())
    return [] if doc.get("ok") is True else [("not_ok", "doc.json: ok is not true")]
'''


class CliTests(unittest.TestCase):
    """End-to-end: a temp COPY of the contract folder proves paths are self-relative."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "zalo-intake"
        pkg = self.root / "_validator"
        pkg.mkdir(parents=True)
        for name in ("__init__.py", "io.py", "schema_subset.py", "cases.py"):
            (pkg / name).write_bytes((STAGE / "_validator" / name).read_bytes())
        (self.root / "validate_examples.py").write_bytes(
            (STAGE / "validate_examples.py").read_bytes())

    def run_cli(self, *argv):
        return subprocess.run([sys.executable, str(self.root / "validate_examples.py"), *argv],
                              capture_output=True, text=True, encoding="utf-8",
                              cwd=self.root)

    def mk(self, group, name, case, files=None):
        case_dir = self.root / "examples" / group / name
        case_dir.mkdir(parents=True)
        (case_dir / "case.json").write_bytes(json.dumps(case).encode("utf-8"))
        for rel, data in (files or {}).items():
            target = case_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return case_dir

    def test_zero_rule_modules_and_zero_cases_exits_1_cleanly(self):
        proc = self.run_cli()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("no cases found", proc.stdout)
        self.assertIn("0 valid, 0 invalid, 0 unexpected outcomes; contract=unversioned-draft",
                      proc.stdout)
        self.assertEqual(proc.stderr, "")

    def test_rules_and_cases_end_to_end(self):
        (self.root / "_validator" / "rules_toy.py").write_bytes(TOY_RULES.encode("utf-8"))
        (self.root / "CONTRACT_REVISION").write_bytes("v1-draft\nrest\n".encode("utf-8"))
        self.mk("valid", "two_sides", {"kind": "flag", "description": "d"},
                {"doc.json": b'{"ok": true}'})
        self.mk("invalid", "manifest_bad", {"kind": "flag", "description": "d",
                                            "expected_errors": ["not_ok"]},
                {"doc.json": b'{"ok": false}'})
        proc = self.run_cli()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[valid] two_sides: PASS", proc.stdout)
        self.assertIn("-> REJECTED-CORRECTLY", proc.stdout)
        self.assertIn("1 valid, 1 invalid, 0 unexpected outcomes; contract=v1-draft",
                      proc.stdout)

    def test_case_option_runs_one_case_verbosely(self):
        (self.root / "_validator" / "rules_toy.py").write_bytes(TOY_RULES.encode("utf-8"))
        self.mk("invalid", "manifest_bad", {"kind": "flag", "description": "d",
                                            "expected_errors": ["not_ok"]},
                {"doc.json": b'{"ok": false}'})
        proc = self.run_cli("--case", "invalid/manifest_bad")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("REJECTED-CORRECTLY", proc.stdout)
        self.assertIn("not_ok doc.json: ok is not true", proc.stdout)
        proc = self.run_cli("--case", "bogus/path/here")
        self.assertNotEqual(proc.returncode, 0)

    def test_hashes_option_prints_size_and_sha256(self):
        doc_bytes = b'{"ok": true}\n'
        self.mk("valid", "two_sides", {"kind": "flag", "description": "d"},
                {"doc.json": doc_bytes, "sub/raw.bin": b"\x00\x01"})
        proc = self.run_cli("--hashes", "valid/two_sides")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"doc.json size_bytes={len(doc_bytes)} "
                      f"sha256={hashlib.sha256(doc_bytes).hexdigest()}", proc.stdout)
        self.assertIn("sub/raw.bin size_bytes=2 sha256=" + hashlib.sha256(b"\x00\x01").hexdigest(),
                      proc.stdout)
        self.assertNotIn("case.json", proc.stdout)

    def test_public_helpers_load_example_and_run_case(self):
        (self.root / "_validator" / "rules_toy.py").write_bytes(TOY_RULES.encode("utf-8"))
        self.mk("invalid", "bad", {"kind": "flag", "description": "d",
                                   "expected_errors": ["not_ok"]},
                {"doc.json": b'{"ok": false}'})
        code = ("import validate_examples as v\n"
                "d, c = v.load_example('invalid/bad')\n"
                "print(d.parts[-2:], c['kind'], c['expected_errors'])\n"
                "print(v.run_case('invalid/bad'))")
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, encoding="utf-8", cwd=self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("('invalid', 'bad') flag ['not_ok']", proc.stdout)
        self.assertIn("[('not_ok', 'doc.json: ok is not true')]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
