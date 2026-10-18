# Restricted Hub scope requires explicit `required` token policy and one shared consumer authorization boundary

- Decision identity: 098.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-23.

## Decision, context, and consequences

Setting
`hub.token_mode = "required"` both requires a credential and authorizes
private or gated repository metadata; `disabled` and `optional` remain
public-only so ambient optional credentials cannot silently broaden archive
scope. All configured consumers must be authorized for every archived
repository because the exported tree has no per-repository ACL layer.
Credential or gate revocation stops future fetches but does not delete
already published revisions; removal from configuration followed by an
explicit purge remains the deletion path. This widens configuration
acceptance without changing a durable JSON format. Rolling back to a
pre-Hub access binary requires stopping sync and temporarily returning the
configuration to `optional`, without syncing restricted repositories on
that release. AD-21 retires the original NG-06 public-only boundary.
**Rejected:** letting an optional token automatically broaden repository
scope, because ambient credential availability would change policy;
per-repository credentials or ACLs, because the deployment has one trusted
internal consumer boundary; automatic deletion on revocation, because it
would violate the archive's explicit-deletion rule.

## Later history and current interpretation

This implements [AD-21](ad-21.md) and retires the original public-only [NG-06
boundary](../architecture.md#4-non-goals) only for explicit `required` policy.
Earlier records describing public-only or optional anonymous behavior, including
[decision 10](decision-010.md) and [decision 92](decision-092.md), must be read
with this qualification. AD-21 preserves the original scope and why it changed.

## Provenance and governing evidence

The source entry first appears in
[c082f87](https://github.com/wtcross/hfcache/commit/c082f8763aecff0b100d6877041b0d5662d1be0a)
(2026-08-23, `Hub access: enable authenticated repository scope`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/configuration.md](../configuration.md),
[docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/credentials.py](../../src/hfcache/credentials.py),
[src/hfcache/hub.py](../../src/hfcache/hub.py).

Relevant verification:
[tests/unit/test_credentials.py](../../tests/unit/test_credentials.py),
[tests/unit/test_hub.py](../../tests/unit/test_hub.py).
