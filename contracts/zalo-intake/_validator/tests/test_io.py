import hashlib
import tempfile
import unittest
from pathlib import Path

from _validator.io import (ContractDataError, canonical_sha256, read_json_bytes, read_jsonl_bytes,
                           sha256_hex, write_bytes_exact)


class HashTests(unittest.TestCase):
    def test_sha256_hex_is_lowercase_hex_of_the_bytes(self):
        self.assertEqual(sha256_hex(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_canonical_sha256_hashes_sorted_compact_utf8_json(self):
        expected = hashlib.sha256('{"a":"Việt","b":[1,null]}'.encode("utf-8")).hexdigest()
        self.assertEqual(canonical_sha256({"b": [1, None], "a": "Việt"}), expected)
        self.assertEqual(canonical_sha256({"a": "Việt", "b": [1, None]}), expected)

    def test_canonical_sha256_refuses_non_finite_numbers(self):
        with self.assertRaises(ValueError):
            canonical_sha256({"a": float("nan")})


class WriteBytesExactTests(unittest.TestCase):
    def test_writes_bytes_unchanged_and_creates_parent_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "records.jsonl"
            write_bytes_exact(path, b'{"a":1}\n{"b":2}\n')
            self.assertEqual(path.read_bytes(), b'{"a":1}\n{"b":2}\n')

    def test_refuses_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TypeError):
                write_bytes_exact(Path(tmp) / "x.json", '{"a":1}\n')


class ReadJsonBytesTests(unittest.TestCase):
    def assertJsonInvalid(self, data, fragment):
        with self.assertRaises(ContractDataError) as ctx:
            read_json_bytes(data)
        self.assertEqual(ctx.exception.code, "json_invalid")
        self.assertIn(fragment, ctx.exception.detail)

    def test_parses_a_json_document(self):
        self.assertEqual(read_json_bytes('{"a": [1, 2.5, null, true, "Việt"]}\n'.encode("utf-8")),
                         {"a": [1, 2.5, None, True, "Việt"]})

    def test_rejects_utf8_bom(self):
        self.assertJsonInvalid(b'\xef\xbb\xbf{"a": 1}', "BOM")

    def test_rejects_invalid_utf8(self):
        self.assertJsonInvalid(b'{"a": "\xff"}', "UTF-8")

    def test_rejects_duplicate_keys_at_any_depth(self):
        self.assertJsonInvalid(b'{"a": 1, "a": 2}', "duplicate")
        self.assertJsonInvalid(b'{"x": [{"b": 1, "b": 1}]}', "duplicate")

    def test_rejects_nan_and_infinity_tokens(self):
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(token=token):
                self.assertJsonInvalid(b'{"a": ' + token + b"}", "non-finite")

    def test_rejects_numbers_that_overflow_to_infinity(self):
        self.assertJsonInvalid(b'{"a": 1e400}', "non-finite")

    def test_rejects_trailing_garbage_and_empty_input(self):
        self.assertJsonInvalid(b'{"a": 1} {"b": 2}', "line 1")
        self.assertJsonInvalid(b"", "line 1")

    def test_error_carries_code_and_detail(self):
        error = ContractDataError("json_invalid", "line 1 column 1: Expecting value")
        self.assertEqual((error.code, error.detail), ("json_invalid", "line 1 column 1: Expecting value"))
        self.assertIn("json_invalid", str(error))


class ReadJsonlBytesTests(unittest.TestCase):
    def assertRejected(self, data, code, line):
        with self.assertRaises(ContractDataError) as ctx:
            read_jsonl_bytes(data)
        self.assertEqual(ctx.exception.code, code)
        self.assertRegex(ctx.exception.detail, rf"^line {line}\b")

    def test_parses_one_object_per_newline_terminated_line(self):
        self.assertEqual(read_jsonl_bytes('{"a":1}\n{"b":"Việt"}\n'.encode("utf-8")),
                         [{"a": 1}, {"b": "Việt"}])

    def test_empty_file_has_no_records(self):
        self.assertEqual(read_jsonl_bytes(b""), [])

    def test_rejects_missing_final_newline(self):
        self.assertRejected(b'{"a":1}\n{"b":2}', "records_format_invalid", 2)

    def test_rejects_carriage_returns_anywhere(self):
        self.assertRejected(b'{"a":1}\r\n{"b":2}\r\n', "records_format_invalid", 1)
        self.assertRejected(b'{"a":1}\n{"b":\r2}\n', "records_format_invalid", 2)

    def test_rejects_empty_lines(self):
        self.assertRejected(b'{"a":1}\n\n{"b":2}\n', "records_format_invalid", 2)
        self.assertRejected(b"\n", "records_format_invalid", 1)

    def test_rejects_lines_that_are_not_objects(self):
        for line in (b"[1]", b'"x"', b"1", b"null"):
            with self.subTest(line=line):
                self.assertRejected(b'{"a":1}\n' + line + b"\n", "records_format_invalid", 2)

    def test_rejects_lines_that_are_not_one_json_value(self):
        self.assertRejected(b'{"a":1}\n{"b":}\n', "records_format_invalid", 2)
        self.assertRejected(b'{"a":1}{"b":2}\n', "records_format_invalid", 1)

    def test_rejects_bom_and_invalid_utf8_with_line_number(self):
        self.assertRejected(b'\xef\xbb\xbf{"a":1}\n', "records_format_invalid", 1)
        self.assertRejected(b'{"a":1}\n{"b":"\xff"}\n', "records_format_invalid", 2)

    def test_duplicate_keys_and_nan_inside_a_line_are_json_invalid(self):
        self.assertRejected(b'{"a":1}\n{"b":1,"b":2}\n', "json_invalid", 2)
        self.assertRejected(b'{"a":NaN}\n', "json_invalid", 1)


if __name__ == "__main__":
    unittest.main()
