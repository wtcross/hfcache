# Checkpoint evidence names paths by key suffix

- Decision identity: 042.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`TX-03` requires each checkpoint to carry re-observable evidence and
requires recovery to confirm it by looking at the filesystem rather than by
trusting the record. `docs/architecture.md` §7.3-§7.7 describe that evidence
in prose — "published tree path, file count", "`.store/trash/<txn>/` absent"
— which is enough for a human and not enough for code.

The convention that makes it mechanical: an evidence key ending `_path`
names an archive-relative path that must still exist, `_paths` a list of
them, and `_absent` a path that must *not* exist. Everything else is left to
the package that knows how to interpret it, because a file count or a digest
means nothing without the artifact it describes.

Suffixes rather than a fixed key list, because the same checkpoint carries
different paths in different operations and a list would have to be extended
every time one is added — which is exactly the kind of table that goes stale.
The suffix travels with the key, so a caller that names a path correctly gets
it checked for free. Evidence keys are durable, so this is a format decision
and not only an implementation one.

## Later history and current interpretation

[Decision 53](decision-053.md) qualifies the convention for evidence whose
subject a later checkpoint moves; [decision 56](decision-056.md) applies it to
discarded pending manifests. Such historical locator values do not assert that
their old paths still exist.

## Provenance and governing evidence

The source entry first appears in
[7333c2f](https://github.com/wtcross/hfcache/commit/7333c2f06eeb10057b0085879a110ed804d15ffe)
(2026-07-25, `storage primitives: implement durable transaction journals and checkpoint
evidence`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/transactions.py](../../src/hfcache/transactions.py).

Relevant verification:
[tests/unit/test_transactions.py](../../tests/unit/test_transactions.py).
