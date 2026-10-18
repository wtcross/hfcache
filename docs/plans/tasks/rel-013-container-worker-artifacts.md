# REL-013: Build clean 0.2.1 artifacts and prove container peer access

| Field | Value |
| --- | --- |
| Work package | `REL-013` |
| Status | pending |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-017](ops-017-container-worker-listener.md), committed |
| Scope | Clean local artifacts and disposable container proof; no NAS bind or production switch |

## Scope and acceptance

1. Build from the exact clean committed OPS-017 source, version 0.2.1. Record
   wheel/sdist, locked dependency closure, base and final application image
   hashes. Reuse the reviewed Caddy artifact only with exact recorded identity;
   do not rebuild/pull or publish an unrelated runtime silently.
2. Stage the protected immutable release/profile/index with explicit usable
   modes and root/service access proof, preserving every old stage and failed
   artifact. Confirm selected helper/profile/config/seccomp/unit provenance and
   the unchanged nine-binding/index shape. No switch occurs in this package.
3. Use actual API and worker containers on local throwaway paths under ordinary
   SELinux enforcing labels and unchanged confinement. Prove framed API-origin
   private PROBE succeeds with the expected peer UID. Prove actual notify
   forwarding/readiness under SELinux, and that API startup waits for worker
   initialization rather than only container creation. A host-origin probe or
   type-rule query alone is not acceptance. Run all complete verification modes
   only against the disposable local archive, with exact receipt/result IDs,
   failure semantics and non-canceling observations.
4. Prove worker PID1/internal FD3, real denial of IPv4/IPv6 creation, no secrets,
   offline startup, masks, capabilities, NoNewPrivileges, read-only root, cgroup
   limits, original fixture-lock contention and graceful socket cleanup/drain.
   Preserve stale/replaced socket evidence and all failed attempts. Never use
   label-disable, custom allow policy, privileged/host-network/PID shortcuts or
   forced container deletion to turn a failure green.
5. Run a fresh predecessor/current format compatibility drill with real
   installed binaries/images, preserving unsupported/malformed/future data.
   Record operational 0.2.0 rollback limits, including its known container-peer
   SELinux hold. Archive/receipt/observer schema versions remain unchanged.

## Contracts, invariants, and ADRs

Review the accepted OPS-017 listener decision and decisions
[65](../../adr/decision-065.md), [75](../../adr/decision-075.md),
[79](../../adr/decision-079.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md), [release](../../agents/release.md),
[containers](../../containers.md), environment and format contracts.
Preserve INV-002/003/005–007/010–016, AD-16/17/21 and FS/TX truth. Do not replace
an architecture change with an evidence-only amendment; return it to an
explicit source task if new behavior is necessary.

## Validation

Planned, not execution evidence: exact clean-source/build checks; isolated
installed wheel profiles; strict stage/index/profile checks; actual two-container
peer and local-domain/isolation/drain proof; predecessor/current format drill;
record/link/whitespace audits and NAS-masked `scripts/check.sh --with-build`.
All complete archive fixtures are local; no production NAS pathname is opened.

## Execution notes and handoff

Draft task only. Wait for committed OPS-017. Root owns privileged local engine
and stage operations; preserve nonsecret proof ledgers and failed attempts.
Artifact readiness is not production deployment or live NAS verification.

## Completion evidence

Not started. Record exact source/artifact/image/index identities, actual fixture
peer/isolation/domain results, compatibility results, gate exit and completed
[progress audit](../../progress.md) in this work-package commit.
