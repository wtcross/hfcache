# Decision 001: `docs/schemas.md` added beyond the plan §7 documentation set

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `ARC-004`.
- Source: [decision 1 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The plan's `docs/` listing has no home for `ARC-004`'s durable JSON
schemas. Folding them into `architecture.md` would have made one document
carry both the reasoning and roughly a thousand lines of format reference;
folding them into `configuration.md` would have conflated operator input with
application output. A dedicated schema reference is also the document a
consumer or auditor reads without needing anything else. Plan §7 is updated
in the `ARC-005` commit, once the full documentation-set deviation is known.

## Provenance and governing evidence

The source entry first appears in
[e9bd9eb](https://github.com/wtcross/hfcache/commit/e9bd9ebf68e207581511be62ab9d781eccb20f48)
(2026-07-24, `ARC-004: define manifest, catalog, run-report, and verification
schemas`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py).
