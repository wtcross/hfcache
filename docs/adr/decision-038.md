# `HFWRN005` fires at a tenth of the reserve

- Decision identity: 038.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`docs/cli.md` §5.6 defines the warning as "free space approaching the
configured reserve" and fixes no threshold, so the application has to choose
one. It is expressed as a percentage *of the reserve* rather than as an
absolute figure, because a deployment that reserved 100 GiB and one that
reserved 1 TiB want to hear about it at different points, and the reserve is
the only number that already scales with the deployment.

A reserve of zero therefore never warns. That is the right reading of an
operator who set both minimums to zero: they turned the reserve off, and a
warning about a reserve that does not exist has nothing to say.

The margin is also measured after `needed_bytes`, not before, so a run that
is about to consume most of the headroom warns even when the archive looked
comfortable before it started.

## Provenance and governing evidence

The source entry first appears in
[5935ef8](https://github.com/wtcross/hfcache/commit/5935ef8268f37efbea4ed8a490a3ef961fee5630)
(2026-07-25, `storage primitives: implement free-space measurement, the reserve, and doctor
check 12`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/configuration.md](../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../src/hfcache/storage.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_storage.py](../../tests/unit/test_storage.py),
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).
