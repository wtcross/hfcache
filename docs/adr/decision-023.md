# Decision 023: A whole-table constraint is not reported alongside a bad field in the same table

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-005`.
- Source: [decision 23 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Pydantic does not run a `mode="after"` model
validator when a field in that model already failed, so a configuration with
both a bad `storage.archive_root` and `maximum_revisions = 9` reports
`HFCFG006` now and `HFCFG011` only after the path is fixed. This narrows
`docs/configuration.md` §8's promise that an operator fixes one file once, and
it is recorded rather than worked around: making it complete would mean
turning every table-level rule into a field-level one, which would lose the
cross-field checks that are the reason those validators exist. The behaviour
is asserted in `tests/unit/test_config_validate.py` so it cannot change
silently.

## Provenance and governing evidence

The source entry first appears in
[9477861](https://github.com/wtcross/hfcache/commit/947786190912145451439f970bea478037896b07)
(2026-07-25, `CFG-005: implement config validate`). The decision text above
preserves the complete reasoning in the current historical log, including its
recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../../docs/configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/config.py](../../src/hfcache/config.py).

Relevant verification:
[tests/unit/test_config_validate.py](../../tests/unit/test_config_validate.py).
