"""Zalo raw-package consumer (MIN-99) — pull/validate/import/ACK against the
independent Zalo intake module's ``/intake/v1`` surface.

Contract SOT: ``contracts/zalo-intake/zalo-intake.md`` (vendored schemas in
``notary_v2/schemas/zalo-intake/``). Guardrails: text/metadata only — image
bytes, URLs and paths are never fetched, stored or served; business tables
and the legacy ``zalo_inbox`` tables are never written.
"""
