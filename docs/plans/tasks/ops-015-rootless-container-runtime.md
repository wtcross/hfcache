# OPS-015: Package and test Caddy and the rootless runtime

| Field | Value |
| --- | --- |
| Work package | `OPS-015` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [OPS-014](ops-014-local-rollout-guardrails.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Settle and record the rootless architecture before source changes: user-manager Quadlets plus reviewed system target bridge, Caddy Unix upstream, one API app and a separate Network=none verifier with real inherited-FD activation.
2. Containerize runtime clients as well as executors; explicitly migrate or safely disable incompatible bare-host Cockpit/client paths. Reuse appropriate local TLS/Hub sources, keep API/MCP class separation and deliver no secrets or host credential stores to the worker.
3. Preserve peer UID/namespace mapping, common local flock and separate private durable stores; prove activation, concurrency, shutdown/drain, exact outcomes and retained-state compatibility with actual disposable containers where available.
4. Bind NAS only read-only, without chown/relabel/copyup options; keep graphroot, images, Caddy state and all writable paths local. Preserve SELinux enforcement and deny privileged/label-disable/host-Podman-socket shortcuts.
5. Package deterministic Caddy/config/image/Quadlet validation and meaningful hermetic tests, current docs/examples and actual tool-version evidence. No production switch or release tag in this task.

## Contracts, invariants, and ADRs

INV-002/003/006/010–016, AD-17/21, FW-03/04, CP client/service boundaries; server/security/configuration/scheduling/activation/deployment contracts and decision 126. Record the actual new architecture (next decision 127 if still next) and amend affected predecessor records in this package.

Read the [invariant register](../../invariants.md), [ADR index](../../adr/README.md),
[environment](../../agents/environment.md), [release](../../agents/release.md),
[planning](../../agents/planning.md) and [workflow](../../agents/workflow.md).
Record actual review/amendments with completion evidence; preserve historical
records rather than silently rewriting their earlier authority.

## Validation

Planned, not execution evidence: `scripts/check.sh` (plus `--with-build` at
release/container boundaries), meaningful scope-specific tests and local
record/link/decision/whitespace audits. Host tests must preserve the absolute
NAS-write ban. Record forbidden storage checks as NOT RUN, never passing.
Only root performs privileged host mutations and never prints secret values.

## Execution notes and handoff

Not started. Dependency completion and commit are required before activation.

## Completion evidence

Not complete. Record actual date/commands/outcomes, required gate exit, host
change ledger and residual holds, invariant/ADR/contract review and the completed
[progress audit](../../progress.md), then set completed in the same work-package
commit. Do not infer completion from a staged artifact or an unrun host check.
