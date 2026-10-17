# Decision 102: Retention defaults to three while explicit five remains compatible

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-09-14.
- Original work package: `RET-010`.
- Source: [decision 102 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The operator requested a smaller default and immediate
cleanup of older revisions in configured models. Schema version 1 now
accepts exactly `3` or `5` for `storage.maximum_revisions`, defaulting to
`3`; the key is not renamed. Existing explicit-five configurations retain
their policy, and adopting three is an explicit configuration migration on
this writer. This deliberately widens configuration acceptance without
changing durable JSON shapes or checkpoint semantics. The historical
`sixth_unique_revision_published` audit reason remains the schema-1 name for
exceeding the configured retention limit. Before rolling back to an older
binary, restore an explicit value of `5`; deleted revisions are not restored
by that policy rollback. Latest means immutable publication generation, and
the current revision remains protected. Cleanup uses reviewed, explicitly
selected model prune rounds because each invocation removes at most one
revision per repository. **Rejected:** allowing arbitrary retention counts,
which broadens policy beyond the request; rejecting existing explicit-five
configurations, which needlessly breaks upgrades; and manually removing
archive files, which bypasses the cache ownership, audit, and recovery
contracts.

## Later history and current interpretation

This amends [AD-04](ad-04.md) and supersedes earlier fixed-five/default-five
language, including the six-revision examples in [decision 68](decision-068.md).
The schema-1 audit reason `sixth_unique_revision_published` remains a historical
identifier, not a claim that every present prune follows a sixth revision.

## Provenance and governing evidence

The source entry first appears in
[ec3e630](https://github.com/wtcross/hfcache/commit/ec3e630cfe63c007f342996bf3f02e7fd0b9b0ec)
(2026-09-14, `RET-010: default to three retained revisions`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/configuration.md](../../docs/configuration.md),
[docs/schemas.md](../../docs/schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/config.py](../../src/hfcache/config.py),
[src/hfcache/retention.py](../../src/hfcache/retention.py).

Relevant verification:
[tests/unit/test_config.py](../../tests/unit/test_config.py),
[tests/unit/test_retention.py](../../tests/unit/test_retention.py).
