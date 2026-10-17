# Quarterly full verification reads the retained archive offline

- Status: accepted; an existing locked plan decision without an AD number.
- Original record: 2026-07-24, `87323c2` (initial plan, §4 and §16).
- ADR backfill: 2026-10-17.
- Authority: [plan §16](../plan.md#16-integrity-and-verification),
  [CLI verification contract](../cli.md), and
  [security controls](../security.md) remain normative. Maintain this record
  under [the ADR policy](README.md).

## Context

Ingestion hashing establishes what was published, but it cannot establish
that the same bytes remain readable months later. ZFS storage protection
also does not replace application-level validation of complete reference,
manifest, path, size, and digest relationships.

## Decision

Provide `verify --full` to validate every retained revision of every
archived repository against its existing immutable manifest, including
repositories no longer in configuration. Recompute SHA-256 offline, read
each proven shared physical object once, write a durable verification
report, and update the derived verification catalog. Report integrity
failure with exit 40 without rewriting expected digests or deleting the
affected revision.

Start with a quarterly systemd verification calendar, coordinated with
storage scrub, SMART, replication, and sync windows. Also run full
verification after the storage and recovery events listed in plan §16.3.
Take the same exclusive application lock used by other archive commands.
The timer is installed but remains disabled until an operator confirms the
maintenance calendar; this ADR does not claim it is active.

## Rationale and alternatives

Periodic local reads detect changed, missing, extra, or non-regular content
and broken publication relationships without depending on upstream access.
Covering unmanaged repositories preserves the archive promise after
configuration removal (AD-06). Physical identity, rather than matching
expected digests alone, justifies reading hardlinks once.

The original locked decision does not enumerate alternative cadences.
Plan §16.4 says to begin quarterly and reconsider after measuring archive
size and sustained NFS throughput. Decision 60 chooses `IPAddressDeny=any`
instead of `PrivateNetwork=true` while NFS reconnect behavior in a private
namespace remains unproven; both the application and Hub offline flag
still forbid requests.

## Consequences

Verification constructs no Hub client and resolves no credential.
`HF_HUB_OFFLINE=1` supplies an additional library-level guard; the shipped
service denies its own IP sockets without moving kernel NFS traffic into a
different network namespace. Full verification can take hours and must be
estimated before assigning a maintenance window. Copy-mode objects are
read separately even if their expected content digests match.

## History and evidence

`87323c2` (2026-07-24) records the locked quarterly/offline decision.
`2cf11f4` (`VER-002`, 2026-07-26) implements archive-wide offline
verification and its no-client/shared-lock tests. `2fd432a` (`SYS-001`,
2026-07-26) ships the separate timer and service. `999ed19` (`SYS-002`,
2026-07-26), [decision 60](decision-060.md), records the deployed egress
control and the deferred private-network reconnect test.

- [Full verification implementation](../../src/hfcache/verification.py).
- [Scoped Hub offline guard](../../src/hfcache/hub.py).
- [Full-verification and no-network tests](../../tests/unit/test_verify_command.py).
- [Object identity, completeness, and corruption tests](../../tests/unit/test_verification.py).
- [Shipped verification service](../../packaging/systemd/hfcache-verify.service).
- [Shipped quarterly timer and disabled-until-reviewed policy](../../packaging/systemd/hfcache-verify.timer).
- [Operator calendar handoff and pending activation](../progress.md#operator-handoff).
- [Offline-unit hardening probe](../../scripts/check-hardening.sh).
