# Deploy the merged Cockpit repair as an immutable local release

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-10-20 |
| Authorization | Latest user explicitly requests merge to main and both remote pushes, then deployment on this host in place of the existing deployment; passwordless sudo and necessary service outage are authorized. Preserve NAS data and previous safety limits. |
| Tracker | [Current selector](current.md) |
| Baseline | Completed repair cdc35a487dd0d41990b4c3305dc645450943a2a3; fast-forwarded main and both remote main refs verified at that exact commit before host deployment work |

## Outcome and limits

Publish the merged source to both main refs first (already done), then prepare a
new immutable patch release, build it from exact clean committed source, back up
the existing local deployment/configuration and install/accept it on this host.
At activation, 0.2.2 was unused in local tags, both remote tag refs and protected
release/stage paths. GitHub preflight succeeded on a read-only retry after initial
transient DNS refusal; no network/host policy was changed. 0.2.2 was reserved
without touching0.2.1.
Do not overwrite immutable0.2.1 or relabel an earlier dirty fixture as a release.

The later user instructions supersede earlier no-merge/no-host-deployment authority
only for this reviewed local replacement and corresponding main pushes. Existing
NAS read-only, original guard/domain/config locks, writer masks, disabled calendars,
stores, handles, secrets and SELinux/systemd confinement remain. No archive init,
NAS content/metadata write, workload admission/replay/cancellation, registry
operation, other-host operation, ACME, force push or automatic rollback/cleanup.
Required annotated local deployed tag follows actual installed acceptance, never
pretagging. Branch publication does not authorize publishing old/unrelated tags;
keep release tags local unless separately requested.

The current original Timestral key/op is observed failed through the authenticated
fixed installed client; obtain its exact terminal Envelope before actual drain.
Existing .candidate.toml, config predecessor and original .configuration.lock
are retained, never reconciled by deleting/replacing them as part of deployment.
No pending/nonterminal/malformed history may be discarded to force quiescence.
Source rollback or observer stop does not prove executor termination.

## Contracts and review

Follow environment/release/workflow/planning and technical-record policy;
INV002/003/005/006/010/014/015/016, agentINV011, CP01–14, FS19 and actual
ADR65/75/79/115/118–122/126–129/132/134–139. Existing contracts prescribe clean
rootless artifacts, exhaustive indexed source/rendering, nine protected bindings,
actual executor drain, original-lock handoff and independent READY guard.
No new architecture, dependency, durable format or workload authority is intended.
Release delta also includes tags/discovery since installed4088994; preserve actual
predecessor compatibility limits and backups/old observers.

## Tasks

| Order | Work package | Depends on |
| --- | --- | --- |
| 1 | [REL-015: prepare release source](tasks/rel-015-cockpit-rest-release-source.md) | Completed repair and main publication |
| 2 | [OPS-023: build, deploy and accept](tasks/ops-023-cockpit-rest-host-rollout.md) | Committed green REL-015 |

## Acceptance and lifecycle

Each package passes actual frontend-required scripts/check.sh; release source and
clean artifacts pass --with-build, with /srv/hfcache shadowed empty/read-only before
collection. Use exact clean detached source outside ignored parents for final
wheel/images/browser. No registry access; reuse authenticated cached foundations.
Rootless build as login/service user, root only for reviewed protected host effects.
Actual non-killing API-then-worker drain and empty process/cgroup/Podman evidence
precede original guard→installer flock→READY guard handoff. Preserve hostNASro
and masks continuously. Reload both managers and prove effective fragments,
profile/image/secret/listener/auth/TLS/worker confinement and public plugin modes.
Inspect uncertainty before another deliberate action; no replay/rollback/cleanup.

Record exact commands/results/hashes and protected backup/evidence paths, new and
old selected identities, actual local tag and separate remaining NAS/original
browser-symptom limits. Stop/mark affected task blocked on any unavailable required
prerequisite, giving exact unblock condition without unsafe substitution. Complete
and clear selector only after scoped acceptance; retain completed repair/history
and all five disposable guests. Publish resulting main commits to both remotes
without unrelated tags, verify refs, and report installed evidence honestly.

2026-10-20: activated directly by the user's new merge/push/deploy instructions;
no other active plan existed. REL015/OPS023 collision searches found none. Read-only
host inventory confirms current0.2.1/source4088994, original guard809950, NASro,
masked timers and preserved existing candidate/config predecessor/configlock.

2026-10-20 scoped completion: REL015/source1c68501 is committed and published
before deployment; OPS023 builds clean immutable0.2.2 and passes six actual local
container proofs, guarded backup/drain/original-lock selection, installed TLS/
auth/private-worker/CLI/state acceptance and final strict extended gate. Local
annotatedv0.2.2 targets exact clean source1c68501; immutable0.2.1, original state,
all failed/unknown evidence and NAS/workload/browser holds remain. Both package
tasks complete; selector cleared without historical backlog activation. Final
OPS023 commit/main publication follows the authorized no-tags push procedure;
actual remote heads are checked after commit, never preclaimed in this record.
