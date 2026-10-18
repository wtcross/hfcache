# Admit typed command routes without widening server authority

- Decision identity: 116.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

Typed routes submit explicit validated command intent through the receipt lane;
URL/body identity fixes command and preview/apply mode. The server retains scope,
Hub credentials, preflight, recovery, locking, reports and private verification.
Reader-installed planning and read-only diagnostics can contact the Hub and write
control receipts without archive mutation; actual sync/probing/verification needs
writer capability. Candidate planning is separately writer-only.

Candidate syntax validity differs from authority compatibility. Compare installed
archive root/UUID, Hub endpoint/token mode/credential name/expected account again
after waiting and before credential-bearing planning; use installed credentials
with candidate repository/policy intent. Explicit null differs from absent candidate
and candidate bytes bind the digest without being persisted as replayable state.
An explicit trusted startup Hub file never becomes client override authority.
Reusing guarded services preserves whole-run capacity, producer joining, exact
results and recovery rules; a duplicate HTTP domain engine or client-supplied
filesystem proof was rejected.

## Relationships and technical evidence

- [decision 117](decision-117.md)
- [119](decision-119.md)
- [108](decision-108.md)
- [112](decision-112.md)
- [115](decision-115.md)
- [API](../api.md)
- [server](../server.md)
- [configuration](../configuration.md)
- [strict DTOs](../../src/hfcache/api/command_models.py)
- [shared-service adapters](../../src/hfcache/api/commands.py)
- [authenticated POST boundary](../../src/hfcache/api/app.py)
- [pure candidate assessment](../../src/hfcache/services/candidates.py)
- [model/authority tests](../../tests/unit/test_command_models.py)
- [real HTTP/domain tests](../../tests/unit/test_api_commands.py)
- [adversarial concurrency/disconnect tests](../../tests/unit/test_api_command_adversarial.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
