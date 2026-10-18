> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 027: `archive init` writes the configured archive id; it does not mint one

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-000`.
- Source: [decision 27 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §6.2 steps 4 and 7 had initialization generate a
UUID and print it for the operator to paste into configuration. That cannot
be reconciled with the rest of the contract. `--archive-root` must equal
`storage.archive_root` (`docs/cli.md` §2), so configuration is loaded and
fully validated before anything happens — and `storage.archive_id` is a
*required* canonical UUID (`HFCFG012`), so the operator has necessarily
already chosen one before `archive init` can run at all. Minting a second
would write a sentinel that disagrees with configuration, which is precisely
the state `FS-03` calls fatal and never repairable, and would leave the new
archive unusable until an unrelated file was edited. The UUID is therefore
provisioned into configuration — which is what the `"replace-with-provisioned-uuid"`
placeholder in `docs/configuration.md` §4 has always asked for — and
`--archive-id` is kept as the same deliberate restatement `--archive-root`
is: the one irreversible command does not take its inputs from a file alone.
Disagreement is `HFARG002`. Plan §6.2 and `docs/cli.md` §2 updated in this
commit.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `STO-000: implement guarded one-time archive initialization and
inspection`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../../../../architecture.md),
[docs/cli.md](../../../../../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../../../../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../../../../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../../../../../tests/unit/test_archive_init.py).
