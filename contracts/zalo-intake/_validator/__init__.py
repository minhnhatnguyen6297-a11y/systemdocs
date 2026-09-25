"""Stdlib-only validator framework for this contract package (driven by validate_examples.py).

Modules:
  schema_subset  evaluator for a JSON Schema draft 2020-12 subset: load_schema(), validate()
  io             byte-exact helpers: read_json_bytes(), read_jsonl_bytes(), sha256_hex(), ...
  cases          example-case discovery, validator/error-code registry and runner

A rule module is a file `_validator/rules_<topic>.py`. validate_examples.py imports every
such file; at import time the module registers its case kinds and error codes:

    from . import CONTRACT_DIR
    from .cases import register, register_error_codes
    from .schema_subset import load_schema, validate

    register_error_codes(["some_code"])
    register("some_kind", check_some_kind)   # fn(case_dir, case) -> list[(code, detail)]

Files are always located relative to this package, so the contract folder can move unchanged.
"""
from pathlib import Path

CONTRACT_DIR = Path(__file__).resolve().parent.parent  # holds *.schema.json, examples/, CONTRACT_REVISION
