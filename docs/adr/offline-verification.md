# Quarterly full verification reads the retained archive offline

- Status: accepted; an existing locked plan decision without an AD number;
  amended by decisions 110/111/115 and [121](decision-121.md).
- Original record: 2026-07-24, `87323c2` (initial plan, §4 and §16).
- ADR backfill: 2026-10-17.
- Authority: [plan §16](../agents/history/plan.md#16-integrity-and-verification),
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
- [Startup-only offline initialization](../../src/hfcache/offline.py) (decision 111 replaces the historical scoped guard).
- [Full-verification and no-network tests](../../tests/unit/test_verify_command.py).
- [Object identity, completeness, and corruption tests](../../tests/unit/test_verification.py).
- [Shipped verification service](../../packaging/systemd/hfcache-verify.service).
- [Shipped quarterly timer and disabled-until-reviewed policy](../../packaging/systemd/hfcache-verify.timer).
- [Operator calendar handoff and pending activation](../agents/progress.md#operator-handoff).
- [Offline-unit hardening probe](../../scripts/check-hardening.sh).

## API-003 amendment (2026-10-17)

[Decision 110](decision-110.md) tightens the common-lock boundary: every
non-estimate verification proves storage safety and retains ownership through
scope resolution, hashing, report persistence and complete catalog merge.
Probing doctor and explicitly confirmed initialization also own the common
lock, while using their own checks so uninitialized storage remains diagnosable
and initializable. Read-only doctor and initialization inspection take no lock.
Public command services acquire once; adapters/runners must not pre-lock them.
This amendment changes no durable schema or systemd scheduling authority.

## API-004 amendment (2026-10-17)

[Decision 111](decision-111.md) removes the scoped process-environment toggle:
shared verification constructs no Hub client or credential and never writes
`os.environ`, including every verification mode. The existing service's
`HF_HUB_OFFLINE=1` and no-IP sandbox remain. A dedicated executor initializes
the library flag once before importing or using Hub libraries and separately
retains its socket restrictions; the helper does not enforce egress policy.
That executor and host acceptance remain API-008/014. The standalone shared
service makes only its structural no-Hub guarantee, and no network-enabled
ASGI fallback is permitted. Verification lock/report/catalog ownership from
decision 110 remains unchanged. [Isolation tests](../../tests/unit/test_execution_isolation.py)
and [child-process startup tests](../../tests/unit/test_offline_process.py) cover
these boundaries without claiming installed-host acceptance.

## API-008 protocol amendment (2026-10-17)

[Decision 115](decision-115.md) supplies a private peer-checked bounded
verification-only socket protocol and separate entry point, with exact durable
operation outcomes and restart reattachment. The shared service still owns its
flock through report/catalog persistence, with an under-lock fresh policy check.
No credential or caller-selected command/config/path crosses this boundary, and
the HTTP process has no in-process production fallback.

API-008's dedicated startup initializes the library offline flag before Hub
imports/use; that flag alone cannot deny IP sockets. Socket-activated units,
credential-free environment provisioning, `IPAddressDeny=any` and installed-host
hardening evidence remain API-014. Standalone development tests prove protocol,
identity and structural no-Hub behavior without claiming OS egress isolation.

## API-014 packaged executor amendment (2026-10-18)

[Decision 121](decision-121.md) places offline startup, `IPAddressDeny=any` and
credential-source masking around the actual dedicated verification service,
including hashing/report/catalog persistence. The AF_UNIX scheduled verify client
uses an API-only credential and may keep its own IP denial; it is not the
credential-free executor. The worker imports no Hub/API/MCP source, hides
`/run/credentials` and trusted source stores, and uses account/euid peer checks,
never manager `%U`. Custom development source paths require explicit sandbox
restrictions. The library flag alone still denies no IP sockets; no production
in-process fallback, generic privileged worker or altered verification algorithm.

The quarterly calendar/disabled timer and existing NFS/network-namespace policy
remain unchanged. Positive inherited-socket/protocol fixtures and unit contracts
are repository evidence; real activation/cgroup no-IP/no-credential, SELinux/NFS
and executor-aware hardening acceptance remain operator deployment prerequisites.

## Confined rootless listener amendment (OPS-017, 2026-10-18)

[Decision 128](decision-128.md) creates the rootless worker listener inside the
existing confined PID1 process, with strict early inheritance audit and real
container-proxied readiness. Native named-FD3 activation remains a separate strict
mode. No secrets, Hub use, IP permission or verification algorithm is added;
socket cleanup preserves unknown evidence and joins active work first. Production
API-to-worker SELinux acceptance awaits OPS-018, while all live NAS verification/
report/catalog tests remain forbidden under the current data-preserving scope.
