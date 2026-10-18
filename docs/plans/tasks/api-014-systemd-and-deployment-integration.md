# API-014: Package the server, private worker, and API-backed scheduled services

| Field | Value |
| --- | --- |
| Work package | `API-014` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-013](api-013-migrate-write-cli-and-operation-waiting.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-014: package API services and preserve offline verification hardening` |

## Scope and acceptance

1. Add server and private verification socket/service units, configuration/credential examples, install/upgrade/rollback support, and a tested single-app Unix/TCP socket arrangement. Keep server and worker unprivileged with existing SELinux/systemd protections, safe writable paths, and shared runtime-lock lifetime.
2. Convert the existing sync/verify service commands into API-backed CLI clients using the local Unix socket and distinct API credentials. Preserve their names, schedules, terminal exit outcomes, disabled verify timer, and monitoring hooks. Verify-client IP deny policy can remain because HTTP uses AF_UNIX.
3. Place `IPAddressDeny=any`, process-wide offline flags, and no Hub/API/MCP credentials around the actual verification executor too. Validate socket activation, peer restrictions, expected fingerprint, reconnect/result handoff, and absence of generic privileged execution. Update hardening probes to measure the actual executing service, not just wrappers.
4. Update deployment draining/cancellation and supervised-recovery instructions: stopping a client service is not proof the writer stopped. Rehearse upgrade/rollback and orphan-worker handling on disposable fixtures. Preserve `hfcache.target`, lock files, filesystem mounts, NFS policies, and the QUA-003 evidence conditions. No production deploy is authorized by this task.

## Contracts, invariants, and ADRs

`INV-003`, `AD-17`, `FS-18`/`FS-19`, `CP-05`–`CP-08`/`CP-13`; systemd scheduling/offline ADRs; plan §6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update server, CentOS Stream 10 deployment, operations, recovery, agent environment/release guidance, packaging examples, README, systemd scheduling/offline ADR amendments, and architecture §7.8.2 cancellation references. Mark operator-only host acceptance pending.

## Validation

Planned checks, not execution evidence:

Required repository checks: unit-file contract tests, credential/import assertions, installer smoke/dry runs, private-worker socket/protocol fixtures, and `scripts/check.sh`. Run systemd-analyze verify where supported and record its availability. Operator deployment prerequisites: real socket activation, cgroup no-IP/no-credential executor probes, and scripts/check-hardening.sh in an authorized disposable or operator-approved environment. When that environment is unavailable, record these as pending deployment holds; they are not substituted by hermetic tests and do not falsely become passed checks. Repository implementation completion does not assert production acceptance.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Not started. The draft does not authorize implementation. Record actual changes,
resolved design issues, scope amendments, and any blocker/unblock condition here.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

Not executed. On completion record the date; acceptance results; exact commands
and outcomes; invariant/ADR review and amendments; documentation changes; a link
to this package's completed [progress audit](../../progress.md); and any operator
handoff. Then set Status to `completed` in the same commit as the work.
