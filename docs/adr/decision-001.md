# Separate durable schemas from operator configuration

- Decision identity: 001.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Context, decision and consequences

A dedicated schema reference keeps durable application output separate from
operator input and architectural rationale. Putting every field definition into
architecture would obscure its reasoning; putting them in configuration would
conflate input policy with output evidence. Consumers and auditors need a complete
standalone format reference. `docs/schemas.md` owns those field/version rules.

## Provenance and governing evidence

The source entry first appears in
[e9bd9eb](https://github.com/wtcross/hfcache/commit/e9bd9ebf68e207581511be62ab9d781eccb20f48)
(2026-07-24, `contract definition: define manifest, catalog, run-report, and verification
schemas`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py).
