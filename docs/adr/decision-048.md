# Read inventory from authoritative references and manifests

- Decision identity: 048.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Context, decision and consequences

Inventory belongs beside status because both read authoritative references and
manifests, independently of derived catalogs (`FS-16`). Incident investigation
cannot depend on the derived state whose correctness is in question. Repository
selection applies to the combined configured/published inventory, including
unmanaged identities; configuration removal alone never deletes retained data.

## Provenance and governing evidence

The source entry first appears in
[353a904](https://github.com/wtcross/hfcache/commit/353a904b3901ef32faca4712a009dda997ee1c3d)
(2026-07-26, `synchronization: aggregate what a run did, and let an operator read it
back`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../src/hfcache/cli.py).

Relevant verification:
[tests/unit/test_readonly_commands.py](../../tests/unit/test_readonly_commands.py).
