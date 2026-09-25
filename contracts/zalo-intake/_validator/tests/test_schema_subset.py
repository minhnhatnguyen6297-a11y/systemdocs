import json
import tempfile
import unittest
from pathlib import Path

from _validator.schema_subset import SchemaError, UnsupportedSchemaKeyword, load_schema, validate

SI = "schema_invalid"


class SchemaCase(unittest.TestCase):
    """Toy schemas live in a temporary folder, never in the contract's examples/."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def write(self, name, doc):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json.dumps(doc).encode("utf-8"))
        return path

    def load(self, doc, name="main.schema.json"):
        return load_schema(self.write(name, doc))

    def assertValid(self, doc, *instances):
        schema = self.load(doc)
        for instance in instances:
            with self.subTest(instance=instance):
                self.assertEqual(validate(instance, schema), [])

    def assertErrors(self, doc, instance, *expected):
        self.assertEqual(validate(instance, self.load(doc)), list(expected))


class TypeEnumConstTests(SchemaCase):
    TYPES = {
        "null": ([None], [False, 0, "", [], {}]),
        "boolean": ([True, False], [0, 1, None, "true"]),
        "object": ([{}, {"a": 1}], [[], None, "x"]),
        "array": ([[], [1]], [{}, "x", None]),
        "number": ([0, -2, 1.5, 10**30], [True, False, "1", None]),
        "integer": ([0, -3, 2.0, 10**30], [1.5, True, False, "1", None]),
        "string": (["", "Việt"], [1, None, ["x"]]),
    }

    def test_each_type_accepts_its_values_only(self):
        for name, (good, bad) in self.TYPES.items():
            schema = self.load({"type": name})
            for value in good:
                with self.subTest(type=name, value=value):
                    self.assertEqual(validate(value, schema), [])
            for value in bad:
                with self.subTest(type=name, value=value):
                    self.assertEqual(validate(value, schema), [(SI, "(root): type")])

    def test_a_bool_is_never_an_integer_or_a_number(self):
        for name in ("integer", "number"):
            for value in (True, False):
                with self.subTest(type=name, value=value):
                    self.assertErrors({"type": name}, value, (SI, "(root): type"))

    def test_type_list_accepts_any_listed_type(self):
        self.assertValid({"type": ["string", "null"]}, "x", None)
        self.assertErrors({"type": ["string", "null"]}, 1, (SI, "(root): type"))

    def test_enum_uses_json_equality(self):
        doc = {"enum": ["a", 1, None, [1, {"k": True}]]}
        self.assertValid(doc, "a", 1, 1.0, None, [1, {"k": True}])
        for value in ("b", True, [1, {"k": 1}], [True, {"k": True}]):
            with self.subTest(value=value):
                self.assertErrors(doc, value, (SI, "(root): enum"))

    def test_const_uses_json_equality(self):
        self.assertValid({"const": 0}, 0, 0.0)
        for value in (False, "0", None):
            with self.subTest(value=value):
                self.assertErrors({"const": 0}, value, (SI, "(root): const"))

    def test_annotations_are_accepted_and_ignored(self):
        doc = {"$schema": "https://json-schema.org/draft/2020-12/schema",
               "$id": "https://example.invalid/main.schema.json", "$comment": "c", "title": "t",
               "description": "d", "examples": [1], "default": 1, "x-note": {"type": "string"},
               "type": "integer"}
        self.assertValid(doc, 1)
        self.assertErrors(doc, "x", (SI, "(root): type"))

    def test_boolean_schemas(self):
        self.assertValid(True, 1, None, {})
        self.assertErrors(False, 1, (SI, "(root): false"))

    def test_errors_are_sorted(self):
        self.assertErrors({"type": "string", "enum": ["a"], "const": "a"}, 1,
                          (SI, "(root): const"), (SI, "(root): enum"), (SI, "(root): type"))

    def test_root_code_applies_to_root_failures(self):
        self.assertErrors({"type": "string", "x-error-code": "name_bad"}, 1, ("name_bad", "(root): type"))


class ObjectKeywordTests(SchemaCase):
    def test_properties_checks_only_present_members(self):
        doc = {"properties": {"a": {"type": "integer"}}}
        self.assertValid(doc, {}, {"a": 1}, {"other": "x"})
        self.assertErrors(doc, {"a": "x"}, (SI, "/a: type"))

    def test_required_reports_each_missing_member(self):
        doc = {"required": ["a", "b"]}
        self.assertValid(doc, {"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3})
        self.assertErrors(doc, {"a": 1}, (SI, "/b: required"))
        self.assertErrors(doc, {}, (SI, "/a: required"), (SI, "/b: required"))

    def test_additional_properties_false(self):
        doc = {"properties": {"a": {}}, "additionalProperties": False}
        self.assertValid(doc, {}, {"a": 1})
        self.assertErrors(doc, {"a": 1, "b": 2}, (SI, "/b: additionalProperties"))
        self.assertErrors(doc, {"x": 1, "y": 2}, (SI, "/x: additionalProperties"),
                          (SI, "/y: additionalProperties"))

    def test_additional_properties_schema(self):
        doc = {"properties": {"a": {}}, "additionalProperties": {"type": "string"}}
        self.assertValid(doc, {"a": 1, "b": "s"})
        self.assertErrors(doc, {"a": 1, "b": 2}, (SI, "/b: type"))

    def test_pattern_properties(self):
        doc = {"patternProperties": {"^x-": {"type": "integer"}}}
        self.assertValid(doc, {"x-a": 1, "other": "anything"})
        self.assertErrors(doc, {"x-a": "s"}, (SI, "/x-a: type"))

    def test_pattern_properties_also_unblocks_additional_properties(self):
        doc = {"properties": {"a": {}}, "patternProperties": {"^x-": {}},
               "additionalProperties": False}
        self.assertValid(doc, {"a": 1, "x-b": "s"})
        self.assertErrors(doc, {"a": 1, "b": 2}, (SI, "/b: additionalProperties"))

    def test_property_names(self):
        doc = {"propertyNames": {"pattern": "^[a-z]+$"}}
        self.assertValid(doc, {"abc": 1}, {})
        self.assertErrors(doc, {"Bad Name": 1}, (SI, "/Bad Name: propertyNames"))

    def test_min_max_properties(self):
        doc = {"minProperties": 1, "maxProperties": 2}
        self.assertValid(doc, {"a": 1}, {"a": 1, "b": 2})
        self.assertErrors(doc, {}, (SI, "(root): minProperties"))
        self.assertErrors(doc, {"a": 1, "b": 2, "c": 3}, (SI, "(root): maxProperties"))

    def test_dependent_required(self):
        doc = {"dependentRequired": {"a": ["b", "c"]}}
        self.assertValid(doc, {}, {"b": 1}, {"a": 1, "b": 2, "c": 3})
        self.assertErrors(doc, {"a": 1}, (SI, "/b: dependentRequired"), (SI, "/c: dependentRequired"))
        self.assertErrors(doc, {"a": 1, "b": 2}, (SI, "/c: dependentRequired"))

    def test_non_objects_ignore_object_keywords(self):
        self.assertValid({"required": ["a"], "minProperties": 3, "propertyNames": {"type": "null"},
                          "additionalProperties": False, "dependentRequired": {"x": ["y"]}},
                         "text", [1], 5, None)

    def test_instance_pointers_escape_tilde_and_slash(self):
        doc = {"properties": {"a/b": {"type": "integer"}, "m~n": {"type": "integer"}}}
        self.assertErrors(doc, {"a/b": "s", "m~n": "s"}, (SI, "/a~1b: type"), (SI, "/m~0n: type"))


class ArrayKeywordTests(SchemaCase):
    def test_items(self):
        doc = {"items": {"type": "integer"}}
        self.assertValid(doc, [], [1, 2])
        self.assertErrors(doc, [1, "x", "y"], (SI, "/1: type"), (SI, "/2: type"))

    def test_prefix_items(self):
        doc = {"prefixItems": [{"type": "string"}, {"type": "integer"}]}
        self.assertValid(doc, ["a", 1], ["a", 1, "extra"], [])
        self.assertErrors(doc, [1, "x"], (SI, "/0: type"), (SI, "/1: type"))

    def test_items_applies_only_after_prefix_items(self):
        doc = {"prefixItems": [{"type": "string"}], "items": {"type": "integer"}}
        self.assertValid(doc, ["a", 1, 2])
        self.assertErrors(doc, ["a", 1, "x"], (SI, "/2: type"))
        self.assertErrors(doc, ["a", 1, False], (SI, "/2: type"))

    def test_items_false_stops_the_tuple(self):
        doc = {"prefixItems": [{"type": "string"}], "items": False}
        self.assertValid(doc, ["a"], [])
        self.assertErrors(doc, ["a", 1], (SI, "/1: false"))

    def test_min_max_items(self):
        doc = {"minItems": 1, "maxItems": 2}
        self.assertValid(doc, [1], [1, 2])
        self.assertErrors(doc, [], (SI, "(root): minItems"))
        self.assertErrors(doc, [1, 2, 3], (SI, "(root): maxItems"))

    def test_unique_items_uses_json_equality(self):
        doc = {"uniqueItems": True}
        self.assertValid(doc, [1, "1", True], [], [[1], {"a": 1}])
        self.assertErrors(doc, [1, 1.0], (SI, "/1: uniqueItems"))
        self.assertErrors(doc, [[1], [1]], (SI, "/1: uniqueItems"))
        self.assertErrors(doc, [{"a": 1, "b": 2}, {"b": 2, "a": 1}], (SI, "/1: uniqueItems"))

    def test_non_arrays_ignore_array_keywords(self):
        self.assertValid({"items": {"type": "null"}, "minItems": 5, "uniqueItems": True},
                         "text", {"a": 1}, 5, None)


class StringKeywordTests(SchemaCase):
    def test_min_max_length_counts_code_points(self):
        doc = {"minLength": 2, "maxLength": 3}
        self.assertValid(doc, "ab", "abc", "Việt"[0:3], "\U0001F600ab")
        self.assertErrors(doc, "a", (SI, "(root): minLength"))
        self.assertErrors(doc, "abcd", (SI, "(root): maxLength"))

    def test_pattern_is_re_search_not_fullmatch(self):
        doc = {"pattern": "^[a-z]+$"}
        self.assertValid(doc, "abc")
        self.assertErrors(doc, "aBc", (SI, "(root): pattern"))
        self.assertValid({"pattern": "[0-9]"}, "xx5xx")
        self.assertErrors({"pattern": "[0-9]"}, "xxx", (SI, "(root): pattern"))

    def test_date_time_requires_seconds_and_an_explicit_offset(self):
        doc = {"format": "date-time"}
        self.assertValid(doc, "2026-09-24T08:00:00Z", "2026-09-24T08:00:00+07:00",
                         "2026-09-24T08:00:00.123+07:00", "2024-02-29T23:59:59Z")
        for value in ("2026-09-24T08:00:00",        # naive: no offset
                      "2026-09-24T08:00Z",          # no seconds
                      "2026-09-24 08:00:00Z",       # space instead of T
                      "2026-09-24t08:00:00z",       # lowercase t/z
                      "2026-09-24T08:00:00+0700",   # offset without colon
                      "2026-09-24", "08:00:00Z", "abc"):
            with self.subTest(value=value):
                self.assertErrors(doc, value, (SI, "(root): format"))

    def test_date_time_checks_the_calendar(self):
        doc = {"format": "date-time"}
        for value in ("2026-02-30T00:00:00Z", "2026-13-01T00:00:00Z", "2026-09-24T24:00:00Z",
                      "2026-09-24T23:59:60Z",  # leap seconds are not produced by our emitters
                      "2026-09-24T08:00:00+24:00", "2026-09-24T08:00:00+07:60"):
            with self.subTest(value=value):
                self.assertErrors(doc, value, (SI, "(root): format"))

    def test_uuid_is_canonical_lowercase_only(self):
        doc = {"format": "uuid"}
        self.assertValid(doc, "01234567-89ab-cdef-0123-456789abcdef",
                         "00000000-0000-0000-0000-000000000000")
        for value in ("01234567-89AB-CDEF-0123-456789ABCDEF", "0123456789abcdef0123456789abcdef",
                      "{01234567-89ab-cdef-0123-456789abcdef}", "01234567-89ab-cdef-0123-456789abcde",
                      "01234567-89ab-cdef-0123-456789abcdef "):
            with self.subTest(value=value):
                self.assertErrors(doc, value, (SI, "(root): format"))

    def test_format_ignores_non_strings(self):
        self.assertValid({"format": "date-time"}, 5, None, {"x": 1})

    def test_unknown_format_raises_at_load_time(self):
        for fmt in ("email", "uri", "hostname"):
            with self.subTest(format=fmt):
                with self.assertRaises(UnsupportedSchemaKeyword):
                    self.load({"format": fmt})


class NumberKeywordTests(SchemaCase):
    def test_minimum_maximum(self):
        doc = {"minimum": 1, "maximum": 3}
        self.assertValid(doc, 1, 2, 3)
        self.assertErrors(doc, 0, (SI, "(root): minimum"))
        self.assertErrors(doc, 4, (SI, "(root): maximum"))

    def test_exclusive_bounds(self):
        doc = {"exclusiveMinimum": 1, "exclusiveMaximum": 3}
        self.assertValid(doc, 2, 1.5)
        self.assertErrors(doc, 1, (SI, "(root): exclusiveMinimum"))
        self.assertErrors(doc, 3, (SI, "(root): exclusiveMaximum"))

    def test_bounds_ignore_non_numbers_and_bools(self):
        self.assertValid({"minimum": 5, "exclusiveMaximum": 0}, "s", None, True)


class CombinatorTests(SchemaCase):
    def test_all_of_reports_each_failing_branch(self):
        doc = {"allOf": [{"type": "string"}, {"minLength": 3}]}
        self.assertValid(doc, "abc")
        self.assertErrors(doc, "ab", (SI, "(root): minLength"))
        # minLength does not apply to non-strings: only the type branch fails
        self.assertErrors(doc, 5, (SI, "(root): type"))
        doc2 = {"allOf": [{"minLength": 3}, {"pattern": "^z"}]}
        self.assertErrors(doc2, "ab", (SI, "(root): minLength"), (SI, "(root): pattern"))

    def test_any_of(self):
        doc = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        self.assertValid(doc, "x", 1)
        self.assertErrors(doc, 1.5, (SI, "(root): anyOf"))
        self.assertErrors(doc, None, (SI, "(root): anyOf"))

    def test_one_of_needs_exactly_one_match(self):
        doc = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        self.assertValid(doc, "x", 1)
        self.assertErrors(doc, None, (SI, "(root): oneOf"))
        self.assertErrors({"oneOf": [{"type": "integer"}, {"minimum": 0}]}, 5, (SI, "(root): oneOf"))

    def test_not(self):
        doc = {"not": {"type": "string"}}
        self.assertValid(doc, 1, None)
        self.assertErrors(doc, "x", (SI, "(root): not"))

    def test_if_then_else(self):
        doc = {"if": {"properties": {"kind": {"const": "a"}}, "required": ["kind"]},
               "then": {"required": ["b"]}, "else": {"required": ["c"]}}
        self.assertValid(doc, {"kind": "a", "b": 1}, {"kind": "x", "c": 1}, {"c": 1})
        self.assertErrors(doc, {"kind": "a"}, (SI, "/b: required"))
        self.assertErrors(doc, {"kind": "x"}, (SI, "/c: required"))

    def test_errors_are_deduplicated(self):
        doc = {"allOf": [{"type": "integer"}, {"type": "integer"}]}
        self.assertEqual(validate("x", self.load(doc)), [(SI, "(root): type")])


class ErrorCodeTests(SchemaCase):
    def test_nearest_enclosing_x_error_code_wins(self):
        doc = {"x-error-code": "outer", "type": "object",
               "properties": {"a": {"type": "string", "x-error-code": "inner"},
                              "b": {"type": "string"}}}
        self.assertErrors(doc, {"a": 1, "b": 2},
                          ("inner", "/a: type"), ("outer", "/b: type"))

    def test_missing_required_uses_the_declaring_schemas_code(self):
        doc = {"x-error-code": "envelope", "properties": {"a": {"type": "string",
               "x-error-code": "member"}}, "required": ["a"]}
        # the member subschema never ran (a is absent): "envelope", not "member"
        self.assertErrors(doc, {}, ("envelope", "/a: required"))

    def test_ref_sites_and_targets_both_count_as_enclosing(self):
        doc = {"properties": {"a": {"$ref": "#/$defs/s", "x-error-code": "at_ref"}},
               "$defs": {"s": {"type": "string"}},
               "required": ["b"], "x-error-code": "top"}
        self.assertErrors(doc, {"a": 1}, ("at_ref", "/a: type"), ("top", "/b: required"))
        doc2 = {"$defs": {"s": {"type": "string", "x-error-code": "in_target"}},
                "properties": {"a": {"$ref": "#/$defs/s", "x-error-code": "at_ref"}}}
        self.assertErrors(doc2, {"a": 1}, ("in_target", "/a: type"))

    def test_combinator_failures_use_the_combinators_code(self):
        doc = {"x-error-code": "combo", "oneOf": [{"type": "string", "x-error-code": "branch"},
                                                 {"type": "integer"}]}
        self.assertErrors(doc, None, ("combo", "(root): oneOf"))
        doc2 = {"x-error-code": "combo", "anyOf": [{"type": "string", "x-error-code": "b1"},
                                                  {"type": "integer", "x-error-code": "b2"}]}
        self.assertErrors(doc2, None, ("combo", "(root): anyOf"))
        self.assertErrors({"not": {"type": "string"}, "x-error-code": "combo"}, "x",
                          ("combo", "(root): not"))

    def test_if_branch_codes_stay_inside_the_branch(self):
        doc = {"x-error-code": "top",
               "if": {"required": ["flag"], "x-error-code": "cond"},
               "then": {"required": ["t"], "x-error-code": "then_code"},
               "else": {"required": ["e"], "x-error-code": "else_code"}}
        self.assertErrors(doc, {"flag": 1}, ("then_code", "/t: required"))
        self.assertErrors(doc, {}, ("else_code", "/e: required"))


class RefTests(SchemaCase):
    def test_local_ref_into_defs(self):
        doc = {"$defs": {"s": {"type": "string"}},
               "properties": {"a": {"$ref": "#/$defs/s"}}}
        self.assertValid(doc, {"a": "x"}, {})
        self.assertErrors(doc, {"a": 1}, (SI, "/a: type"))

    def test_ref_sibling_keywords_are_evaluated(self):
        # draft 2020-12: $ref does NOT suppress its sibling keywords
        doc = {"$defs": {"s": {"type": "string"}},
               "properties": {"a": {"$ref": "#/$defs/s", "minLength": 3}}}
        self.assertErrors(doc, {"a": "ab"}, (SI, "/a: minLength"))
        self.assertErrors(doc, {"a": 5}, (SI, "/a: type"))

    def test_ref_with_escaped_pointer(self):
        doc = {"$defs": {"a/b": {"type": "string"}}, "properties": {"x": {"$ref": "#/$defs/a~1b"}}}
        self.assertErrors(doc, {"x": 1}, (SI, "/x: type"))

    def test_recursive_ref_inside_one_file(self):
        doc = {"type": "object",
               "properties": {"next": {"$ref": "#"}, "v": {"type": "integer"}}}
        self.assertValid(doc, {"v": 1, "next": {"v": 2, "next": {"v": 3}}})
        self.assertErrors(doc, {"v": 1, "next": {"v": "s"}}, (SI, "/next/v: type"))

    def test_cross_file_ref_resolves_against_the_referring_file(self):
        self.write("common.schema.json",
                   {"$defs": {"u": {"type": "string", "format": "uuid", "x-error-code": "bad_uuid"},
                              "b": {"$ref": "#/$defs/u"}}})
        self.write("sub/b.schema.json",
                   {"type": "object", "properties": {"y": {"$ref": "#/$defs/u"}},
                    "$defs": {"u": {"type": "integer"}}})
        doc = {"type": "object",
               "properties": {"id": {"$ref": "common.schema.json#/$defs/u"},
                              "mid": {"$ref": "sub/b.schema.json"},
                              "wrap": {"$ref": "common.schema.json#/$defs/b"}},
               "$defs": {"u": {"type": "integer"}}}
        good_id = "01234567-89ab-cdef-0123-456789abcdef"
        self.assertValid(doc, {"id": good_id, "mid": {"y": 5}, "wrap": good_id})
        self.assertErrors(doc, {"id": "x"}, ("bad_uuid", "/id: format"))
        self.assertErrors(doc, {"mid": {"y": "s"}}, (SI, "/mid/y: type"))
        # "wrap" hops through common.schema.json's own local $defs: code "bad_uuid" survives
        self.assertErrors(doc, {"wrap": 7}, ("bad_uuid", "/wrap: type"))
        self.assertErrors(doc, {"wrap": "x"}, ("bad_uuid", "/wrap: format"))

    def test_whole_file_ref(self):
        self.write("other.schema.json", {"type": "string"})
        self.assertErrors({"properties": {"a": {"$ref": "other.schema.json"}}}, {"a": 1},
                          (SI, "/a: type"))

    def test_cyclic_cross_file_refs_and_each_file_loaded_once(self):
        self.write("a.schema.json", {"type": "object",
                                     "properties": {"b": {"$ref": "b.schema.json"},
                                                    "v": {"type": "integer"}}})
        self.write("b.schema.json", {"type": "object",
                                     "properties": {"a": {"$ref": "a.schema.json"},
                                                    "v": {"type": "integer"}}})
        import unittest.mock as mock
        reads = []
        real_read = Path.read_bytes

        def spy(self):
            reads.append(self)
            return real_read(self)

        with mock.patch.object(Path, "read_bytes", spy):
            schema = load_schema(self.dir / "a.schema.json")
        self.assertEqual(len(reads), len(set(reads)))  # cached: a and b read exactly once
        self.assertEqual(validate({"b": {"a": {"v": 3}}}, schema), [])
        self.assertEqual(validate({"b": {"v": "x"}}, schema), [(SI, "/b/v: type")])


class SchemaLoadErrorTests(SchemaCase):
    def test_unknown_keywords_fail_loudly(self):
        for doc in ({"multipleOf": 2}, {"contains": {}}, {"unevaluatedProperties": True},
                    {"definitions": {}}, {"dependentSchemas": {}}, {"require": ["a"]},
                    {"if": {"minimum": 0}, "minimumx": 1}):
            with self.subTest(doc=doc):
                with self.assertRaises(UnsupportedSchemaKeyword):
                    self.load(doc)

    def test_unknown_keywords_are_caught_at_any_depth(self):
        with self.assertRaises(UnsupportedSchemaKeyword):
            self.load({"properties": {"a": {"type": "integer", "minLengthx": 1}}})
        with self.assertRaises(UnsupportedSchemaKeyword):
            self.load({"$defs": {"unused": {"bogusKw": 1}}})

    def test_unknown_keywords_are_caught_in_referenced_files(self):
        self.write("bad.schema.json", {"type": "string", "bogusKw": 1})
        with self.assertRaises(UnsupportedSchemaKeyword):
            self.load({"$ref": "bad.schema.json"})

    def test_unsupported_schema_keyword_is_a_schema_error(self):
        self.assertTrue(issubclass(UnsupportedSchemaKeyword, SchemaError))

    def test_keyword_like_names_in_data_are_not_keywords(self):
        doc = {"properties": {"multipleOf": {"type": "integer"}}, "required": ["multipleOf"],
               "examples": [{"bogus": 1}], "default": {"x": 1}}
        schema = self.load(doc)
        self.assertEqual(validate({"multipleOf": 1}, schema), [])
        self.assertEqual(validate({"multipleOf": "s"}, schema), [(SI, "/multipleOf: type")])
        const_schema = self.load({"const": {"properties": 1, "multipleOf": [2]}})
        self.assertEqual(validate({"multipleOf": [2], "properties": 1}, const_schema), [])
        self.assertEqual(validate({}, const_schema), [(SI, "(root): const")])

    def test_nested_id_is_not_supported(self):
        with self.assertRaises(UnsupportedSchemaKeyword):
            self.load({"properties": {"a": {"$id": "x.schema.json", "type": "string"}}})

    def test_remote_and_anchor_refs_are_not_supported(self):
        for ref in ("https://example.com/x.schema.json", "#foo", "a.schema.json?v=1"):
            with self.subTest(ref=ref):
                with self.assertRaises(UnsupportedSchemaKeyword):
                    self.load({"properties": {"a": {"$ref": ref}}})

    def test_unresolvable_refs_raise_schema_error(self):
        for ref in ("missing.schema.json", "#/$defs/absent", "#/properties/nope"):
            with self.subTest(ref=ref):
                with self.assertRaises(SchemaError):
                    self.load({"properties": {"a": {"$ref": ref}}})

    def test_ref_must_point_at_a_schema_position(self):
        with self.assertRaises(SchemaError):
            self.load({"examples": [{"type": "integer"}],
                       "properties": {"a": {"$ref": "#/examples/0"}}})

    def test_bad_keyword_values_raise_schema_error(self):
        for doc in ({"type": "int"}, {"type": 5}, {"type": ["string", "string"]},
                    {"minLength": -1}, {"minItems": 1.5}, {"maximum": True},
                    {"required": "a"}, {"required": ["a", "a"]}, {"enum": "x"},
                    {"dependentRequired": {"a": "b"}}, {"oneOf": []}, {"prefixItems": {}},
                    {"pattern": "("}, {"patternProperties": {"(": {}}}, {"format": "date"},
                    {"properties": {"a": 5}}, {"uniqueItems": "yes"}, {"x-error-code": 5},
                    {"$ref": 5}, {"properties": []}):
            with self.subTest(doc=doc):
                with self.assertRaises(SchemaError):
                    self.load(doc)

    def test_broken_schema_files_raise_schema_error(self):
        path = self.dir / "bad.schema.json"
        path.write_bytes(b'{"a": 1, "a": 2}')
        with self.assertRaises(SchemaError):
            load_schema(path)
        with self.assertRaises(SchemaError):
            load_schema(self.dir / "absent.schema.json")
        path.write_bytes(b"[1, 2]")
        with self.assertRaises(SchemaError):
            load_schema(path)


if __name__ == "__main__":
    unittest.main()
