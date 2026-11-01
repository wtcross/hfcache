# Share diagnostic ordering and mutation preflight

- Decision identity: 033.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

Keep storage primitives in storage.py and ordered outcomes/gates in preflight.py.
The same named checks/order serve doctor and mutating preflight; routing through
CLI callbacks would invert authority. A storage-only module is also the wrong home
for configuration, credential and Hub checks. CHECK_ORDER matches the CLI contract.
Archive initialization has its own module because bringing an archive into being
is distinct from proving storage safety for existing work.

## Provenance and governing evidence

The source entry first appears in
[c8ac36a](https://github.com/wtcross/hfcache/commit/c8ac36a48c216fb9f3535e496c28c83d2a0a6e8b)
(2026-07-25, `storage primitives: implement the shared storage preflight and doctor's mount
checks`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/preflight.py](../../src/hfcache/preflight.py),
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).

## Configured HTTPS port qualification (2026-10-31)

The diagnostic Hub TLS check must use the endpoint's explicit HTTPS port, or `443`
when omitted. DNS still checks the configured hostname, and the TLS handshake
still verifies that hostname with the deployment's trust store. Invalid explicit
ports refuse configuration with `HFCFG014`. This preserves the existing check
order, verified transport and injectable Hub boundary (`AD-08`, `INV-003`);
it adds no transport, credential source or dependency.
