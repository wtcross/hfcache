# Revalidate explicit maintenance authority at execution

- Decision identity: 117.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

Maintenance uses distinct keyed preview/apply routes with explicit scope;
previews persist control receipts and grant no later mutation capability. Every
archive-affecting operation requires writer authority and rederives current policy,
scope and evidence under the service-owned flock. Posting a preview/plan/result
cannot authorize apply. A URL or body cannot select arbitrary paths, credentials,
unknown cleanup or weaker proof.

Prune removes at most one eligible non-current revision per repository per round.
Purge is unmanaged-only explicit whole-repository scope or all-unmanaged, with
unknown-layout refusal and per-repository transaction/audit preservation. Recovery
never guesses; quarantine proves its explicit whole batch against fresh matching
current retained publication evidence and excludes repair/unique/unfinished state.
Repair preserves original manifest expectations, generation, new instance identity
and old-locator grace. Existing pre/post-logical-commit recovery remains authoritative.

Initialization alone is gated disabled-by-default and requires literal confirmation,
installed root/UUID equality and locked known-layout proof. Health/startup/recovery
never initialize. Exact terminal failure/partial diagnostics remain observable;
HTTP success/admission is not a domain-success claim. These routes add no new
archive recovery algorithm, durable schema or workflow framework.

## Relationships and technical evidence

- [decision 120](decision-120.md)
- [116](decision-116.md)
- [115](decision-115.md)
- [API](../api.md)
- [server initialization gate](../server.md)
- [security](../security.md)
- [operations](../operations.md)
- [recovery](../recovery.md)
- [invariant register](../invariants.md)
- [strict scope DTOs](../../src/hfcache/api/maintenance_models.py)
- [fixed maintenance routes](../../src/hfcache/api/maintenance.py)
- [shared keyed admission](../../src/hfcache/api/commands.py)
- [early authorization/initialization gate](../../src/hfcache/api/app.py)
- [guarded domain services/audit redaction](../../src/hfcache/services/commands.py)
- [model tests](../../tests/unit/test_maintenance_models.py)
- [real HTTP/domain tests](../../tests/unit/test_api_maintenance.py)
- [queued-scope/proof/idempotency tests](../../tests/unit/test_api_maintenance_adversarial.py)
- [shared-service tests](../../tests/unit/test_command_services.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
