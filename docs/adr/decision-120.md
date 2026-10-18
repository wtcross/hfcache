# Separate command execution from resumable CLI observation

- Decision identity: 120.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-18.
API-backed Cockpit mechanisms are amended by [decision 122](decision-122.md).


## Context, decision and rationale

Operational commands submit typed HTTP intent; credentials, preflight, recovery,
flock and execution remain server-side. Default JSON waits for the exact stored
terminal Envelope, including failure/partial results; human rendering summarizes
it. Explicit detach emits a separately typed admission object, never fabricated
command success. Show/lookup preserve metadata; wait returns the command result.

Print validated original key before POST and accepted operation ID before waiting,
even with quiet output. Warnings/errors and safety/gap notices survive quiet/JSON;
ordinary progress requires both output streams to be terminals. No-color is per
invocation; client verbosity never changes daemon logging. Finite observation covers
all event/status/result work, retains sequenced gaps and handles, and stops without
cancellation/replay on timeout, Ctrl-C or connection loss.

Missing, expired, interrupted or protocol-invalid history proves no outcome. Lookup
uses the original class/key without submitting. Never replace uncertainty with a
new key, local fallback, automatic recovery or client-stop/free-lock assumptions.
Scheduled and Cockpit clients retain the same boundaries. Local help/version,
explicit bootstrap validation and foreground serve remain named local exceptions.

## Relationships and technical evidence

- [decision 121](decision-121.md)
- [decision 122](decision-122.md)
- [118](decision-118.md)
- [119](decision-119.md)
- [114](decision-114.md)
- [115](decision-115.md)
- [117](decision-117.md)
- [CLI](../cli.md)
- [client](../api-client.md)
- [API](../api.md)
- [operations](../operations.md)
- [recovery](../recovery.md)
- [invariants](../invariants.md)
- [CLI modes](../../src/hfcache/cli.py)
- [pure shared requests](../../src/hfcache/services/requests.py)
- [pure local bootstrap descriptions](../../src/hfcache/services/bootstrap.py)
- [submission/observation helpers](../../src/hfcache/cli_client.py)
- [bounded typed client](../../src/hfcache/client.py)
- [authenticated server/private-worker fixture](../../tests/api_cli.py)
- [write CLI integration](../../tests/unit/test_cli_api_writes.py)
- [helper tests](../../tests/unit/test_cli_operation_helpers.py)
- [CLI interruption/idempotency/security tests](../../tests/unit/test_cli_operations_adversarial.py)
- [actual CLI socket integration](../../tests/unit/test_interface_integration.py)
- [public diagnostics fixtures](../../tests/unit/test_cli_diagnostics.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
