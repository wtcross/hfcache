# Guard complete command execution and verification persistence

- Decision identity: 110.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

Verification must hold the common archive flock across preflight, scope,
payload hashing, report persistence and catalog read/merge/write. Atomic JSON
replacement alone does not serialize a read/modify/write cycle; releasing after
hashing can lose concurrent findings. All actual verification modes use the same
service-owned lock exactly once. Adapters/runners pass deadline/policy hooks and
never pre-lock or acquire nested flocks. Estimates stay metadata-only.

Probing doctor and explicitly confirmed initialization own that lock with their
own checks; read-only doctor and initialization inspection do not. Quarantine
refuses unrelated unfinished work rather than reconciling it. Sync joins its
producer before lock release on failure. Shared verification never toggles process
environment or resolves Hub credentials: dedicated startup sets library offline
mode, and installed confinement separately denies IP. The lock rule changes no
durable expectations, clearing rules or publication identity.

## Relationships and technical evidence

- [decision 111](decision-111.md)
- [decision 115](decision-115.md)
- [AD-17](ad-17.md)
- [offline verification](offline-verification.md)
- [decision 40](decision-040.md)
- [verification lock/merge regression tests](../../tests/unit/test_command_locking.py)
- [command guard and refusal tests](../../tests/unit/test_command_services.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
