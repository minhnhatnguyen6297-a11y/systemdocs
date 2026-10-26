# Inheritance case provenance

Accessed 2026-07-22. People are anonymized to letters. This file records
public exercise facts and does not replace
[`business-rules.md`](./business-rules.md).

## Policy

- `accepted`: in scope and reduced to an exact fraction oracle from the source.
- `ambiguous`: facts or arithmetic are incomplete or inconsistent.
- `source_error`: the source itself exposes a legal or factual error.
- `out_of_scope`: wills, compulsory heirs, refusal, disqualification, debt,
  adoption, or pre-2015 law.
- `duplicate_source`: repeated facts retained for traceability, not counted as
  an independent oracle.

The machine-readable records are in
`tests/fixtures/inheritance_research_cases.json`. Each record carries its source
anchor, reduction assumptions and confidence. No synthetic expected result is
used as a research oracle.

The set has 23 records, 8 public source groups, and 8 accepted exact-fraction
oracles. Non-accepted records are deliberately not promoted to engine output.
The accepted oracles are executed by `tests/test_inheritance_research_catalog.py`;
product-specific edge rules are covered separately by engine unit tests and are
not presented as Internet-derived answers.

## Legal reference

The statutory baseline (BLDS 2015 Art. 611–658, HNGĐ 2014 Art. 33, 43, 65, 66,
forward inheritance vs representation) is summarised with links in
[`legal-baseline.md`](./legal-baseline.md). Official text:
https://vbpl.moj.gov.vn/toaannhandantoicao/Pages/vbpq-toanvan.aspx?ItemID=95942&Keyword=91%2F2015%2FQH13
