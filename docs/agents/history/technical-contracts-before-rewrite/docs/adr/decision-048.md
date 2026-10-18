> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 048: `hfcache list` lands at `SYNC-002`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `SYNC-002`.
- Source: [decision 48 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §11 requires the
command and plan §28 gives it no work package — the only v1 CLI command with
no home. Three placements were considered. `CFG-006` implemented the
read-only command surface and would have been the natural place, except that
at Phase 2 there was nothing published to list, so the command could only
have been written against a layout that did not exist yet. Phase 8 is
documentation and release; adding a command there would mean shipping a
runbook before the thing it documents. `SYNC-002` is where the archive first
holds revisions an operator would want an inventory of, and where the sibling
read commands — `status` reporting the same references — are being completed.

`list` deliberately reads manifests and references and never the catalog,
which `docs/cli.md` §2 already required and which is the reason it belongs
beside `status` rather than beside the catalog rebuild: an operator taking
inventory during an incident is exactly the person who cannot rely on derived
state (`FS-16`). Selectors restrict the *configured* set, so naming one
repository never hides an unmanaged one the operator did not ask about.

## Provenance and governing evidence

The source entry first appears in
[353a904](https://github.com/wtcross/hfcache/commit/353a904b3901ef32faca4712a009dda997ee1c3d)
(2026-07-26, `SYNC-002: aggregate what a run did, and let an operator read it
back`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md),
[docs/architecture.md](../../../../../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../../../../../src/hfcache/cli.py).

Relevant verification:
[tests/unit/test_readonly_commands.py](../../../../../../tests/unit/test_readonly_commands.py).
