# Validate identifiers before constructing archive paths

- Decision identity: 017.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

Keep credential-source handling in `credentials.py` and validated archive names
in `identity.py`, separate from filesystem layout in `paths.py`. Path construction
joins identifiers into filesystem names and therefore needs a value whose grammar
and safety have already been established. Combining raw identifiers with layout
logic would spread validation across every caller and weaken containment review.

## Provenance and governing evidence

The source entry first appears in
[b7e2686](https://github.com/wtcross/hfcache/commit/b7e268626b7e9c5248a00cb437b8d0a2982bfc34)
(2026-07-25, `configuration validation: implement repository identity and safe path mapping`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/configuration.md](../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/identity.py](../../src/hfcache/identity.py),
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_identity.py](../../tests/unit/test_identity.py).
