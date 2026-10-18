# A Pydantic validator must raise `ValueError`, never `TypeError`

- Decision identity: 021.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

Found by a test: Pydantic converts `ValueError` and
`AssertionError` into validation errors and lets everything else propagate, so
a `TypeError` raised for a non-string digest escaped `load` as a bare
exception instead of being reported as a coded problem naming the field — the
one thing `load` exists to guarantee. Both sites now raise `ValueError` with a
`# noqa: TRY004`, since Ruff reasonably prefers `TypeError` for a type check
and is wrong about it here.

## Provenance and governing evidence

The source entry first appears in
[2133496](https://github.com/wtcross/hfcache/commit/21334967781eef8ee37600ed63fad4e42e404180)
(2026-07-25, `configuration validation: implement the durable manifest and report models`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[recorded deployment scope](../deployment-status.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py).
