# Pinned source review and provenance

| Field | Value |
| --- | --- |
| Repository | wtcross/hfcache |
| Branch examined | main |
| Commit | `dcc2c562b52304541d0cb85d20fc046072038e79` |
| Commit subject | CAT-016: complete lifecycle compatibility and final acceptance |
| Commit timestamp returned by GitHub | 2026-10-19T21:49:10Z |
| Review date | 2026-10-19, America/New_York |
| Current tracker at snapshot | Inactive; no selected plan, next task or blockers |
| Access used | Connected GitHub source reads pinned to this commit; official Cockpit documentation |
| Product execution | None; no installed browser/PAM/rootless/API/production test |

GitHub code search was used to locate files, not as authoritative latest source:
its indexed result URLs could refer to an older commit. Evidence for the findings
was read at the pinned SHA below. CPR search returned no matches; implementation
must still perform an actual current-tree collision check outside bundle paths.
This review does not claim exhaustive dynamic coverage or deployment parity.

| Source | Reviewed relevance / scope |
| --- | --- |
| [AGENTS.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/AGENTS.md) | Repository context router and safety/workflow routing |
| [docs/agents/planning.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/agents/planning.md) | Draft/activation authority, stable plan paths and task records |
| [docs/agents/workflow.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/agents/workflow.md) | Contract-first packages, incremental commits and mandatory gate |
| [docs/agents/invariants.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/agents/invariants.md) | INV-011 workflow authority |
| [docs/agents/plans/current.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/agents/plans/current.md) | Inactive selector at reviewed snapshot |
| [docs/invariants.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/invariants.md) | Relevant identity, reporting, framework and deployment restrictions; not a full invariant audit |
| [docs/cockpit.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/cockpit.md) | Current CP rules, fixed launcher, operations and host exceptions |
| [docs/api.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api.md) | Existing route/effect matrix, report endpoints and exact read wrappers |
| [docs/api-client.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api-client.md) | Typed client, errors, idempotency, candidate content and no fallback |
| [docs/adr/decision-122.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/adr/decision-122.md) | Cockpit API boundary and exact installed-content amendment |
| [cockpit/src/lib/command.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/command.ts) | Fixed transient service identity/client config/rootless socket argv |
| [cockpit/src/api/hfcache.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/hfcache.ts) | Only CLI spawn adapter, guarded invocation and notices |
| [cockpit/src/lib/runner.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/runner.ts) | No-envelope error propagation and bounded process observation |
| [cockpit/src/lib/envelope.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/envelope.ts) | Strict Envelope parsing/classification and copied operation commands |
| [cockpit/src/lib/candidate-guard.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/candidate-guard.ts) | Exact candidate/base guard, lock and filesystem installation |
| [cockpit/src/lib/config-pipeline.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/config-pipeline.ts) | Assessment parsing, readiness and generic install failure wrapper |
| [cockpit/src/lib/config.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/config.ts) | Form/text representation, tag handling and field-error mapping |
| [cockpit/src/api/config.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/config.ts) | Host mutations vs API candidate validation/planning |
| [cockpit/src/configuration.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/configuration.tsx) | Validate/install/cancel state transitions and surfaced pipeline errors |
| [cockpit/src/components.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/components.tsx) | Shared EnvelopeAlert, QueryError and RecoveryHandles |
| [cockpit/src/hooks.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/hooks.ts) | Component-local handles, read queries and swallowed unit-poll errors |
| [cockpit/src/app.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/app.tsx) | Tab mount/unmount ownership |
| [cockpit/src/api/systemd.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/systemd.ts) | Permanent cached system-bus client and fixed unit calls |
| [cockpit/src/api/schedule.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/schedule.ts) | Fixed host calendar/drop-in boundary |
| [cockpit/src/sync.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/sync.tsx) | Manual system-service controls and selected REST job flow; relevant sections |
| [cockpit/src/verify.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/verify.tsx) | Estimate card, full service control and revision REST flow; relevant sections |
| [cockpit/src/maintenance.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/maintenance.tsx) | DryRunApplyCard and RepairCard failure/handle predicates; relevant sections |
| [cockpit/src/dashboard.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/dashboard.tsx) | Status/VersionCard read/error rendering; relevant sections |
| [cockpit/src/api/archive.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/archive.ts) | Direct host report reads and journal query |
| [scripts/hfcache-client](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/hfcache-client) | Rootless client wrapper, not a native-local command implementation |
| [scripts/container-service.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/container-service.py) | Pinned profile, identity, role/mount/credential construction; first 280 lines |
| [src/hfcache/services/candidates.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/services/candidates.py) | Candidate syntax/authority fields and safe negative assessments |
| [src/hfcache/api/commands.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/api/commands.py) | Typed candidate validation and keyed plan/sync/verify routes |
| [src/hfcache/cli_client.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/cli_client.py) | Client config resolution, candidate bytes, paging and retained keys; relevant sections |
| [src/hfcache/reporting.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/reporting.py) | Envelope / EnvelopeProblem models and context mapping; relevant sections |
| [cockpit/package.json](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/package.json) | Node/pnpm pin and scripts; not an executed gate |
| [scripts/check.sh](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/check.sh) | Locked checks and optional frontend skip logic |

## References to load during implementation

The main plan also points to current security, CLI, configuration, development,
container/deployment guides, relevant older Cockpit decisions and decision 127.
Those references are contract-loading requirements, not a claim that every line
of every linked file was audited in this review. Use the ADR index and affected
register sections progressively, following the repository's instructions.

## What was established vs not established

Established: the functions/branches described in the audit exist in the pinned
source; the CLI is already REST-backed; the candidate is directory-mounted and
uploaded as content; the described failure predicates and state lifetimes have
concrete source evidence; existing routes cover the proposed REST parity work.

Not established: the installed user's exact release or browser bundle, the actual
Cockpit close problem beyond their reported string, the stage at which that host
lost acknowledgement, a running daemon failure, actual credential/socket/SELinux
fault, completed admission, or production archive effects. No remote host commands
were executed. No product test suite or full installed application was run here.
The review container's Node is older than the repository's declared requirement;
do not mistake archive-validation scripts for frontend test coverage.

Package validation performed on the downloadable bundle checks paths, payload
hashes, archive CRC/content identity, expected draft/pending metadata and relative
links to other bundle files. It does not prove the proposed source fixes work.
