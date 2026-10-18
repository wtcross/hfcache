# Five identifier grammars accepted a trailing newline; fixed

- Decision identity: 016.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`config.py` compiled `^…$` and applied it with `re.match`, and in
Python `$` also matches immediately before a trailing newline. So
`parse_revision` accepted `"main\n"` and, worse, accepted a 40-character SHA
with a newline glued to it and returned the value including the newline — which
would then have been sent to the Hub and written into a path and a manifest.
TOML can produce such a value through an escape or a multi-line string. All five
patterns (`_SEGMENT`, `_REFERENCE_NAME`, `_COMMIT_SHA`, `_ACCOUNT`,
`_CREDENTIAL_NAME`) now use `fullmatch` with no anchors, `tests/unit/
test_identity.py` provokes the newline case for every grammar, and a structural
test fails if any future pattern in the module is written anchored. This is the
same defect found in `credentials.py` during `configuration validation`; finding it a second time
is why the guard is now structural rather than another example.

## Provenance and governing evidence

The source entry first appears in
[b7e2686](https://github.com/wtcross/hfcache/commit/b7e268626b7e9c5248a00cb437b8d0a2982bfc34)
(2026-07-25, `configuration validation: implement repository identity and safe path mapping`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/configuration.md](../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/identity.py](../../src/hfcache/identity.py),
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_identity.py](../../tests/unit/test_identity.py).
