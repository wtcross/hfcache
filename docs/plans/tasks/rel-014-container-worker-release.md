# REL-014: Record the corrected local release and handoff

| Field | Value |
| --- | --- |
| Work package | `REL-014` |
| Status | completed |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-018](ops-018-container-worker-rollout.md), committed 156506f |
| Scope | Local release evidence, annotated tag and handoff; no remote publication or NAS action |

## Scope and acceptance

1. Reconcile the exact deployed 0.2.1 source/wheel/image/profile/index, local
   review history, actual API-origin worker peer acceptance and host change
   ledger. Preserve the older 0.2.0 SELinux failure as historical evidence.
2. Update release notes, README/status, contracts and operator handoff to state
   the corrected listener/peer acceptance precisely. It is still not live NAS
   verification, write/full-domain/NFS-hardening, calendar or other-host
   acceptance. Retain original NAS-ro/guard/mask and state-preservation limits.
3. After the actual required gate, create only the authorized local annotated
   0.2.1 tag identifying the reviewed release and its deployed artifact source.
   Do not move an existing tag or push/publish to a remote. Record its actual
   target and annotation, not a provisional command as success.
4. Complete the scoped plan and clear only its active selector once all five
   tasks' acceptance and commits exist. Retain all task, plan, failed attempt,
   rollback and partial release history; unrelated backlog stays unselected.

## Contracts, invariants, and ADRs

Review [release](../../agents/release.md), deployment/environment/containers,
the accepted listener decision and decisions
[65](../../adr/decision-065.md), [75](../../adr/decision-075.md),
[79](../../adr/decision-079.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md), [128](../../adr/decision-128.md),
[129](../../adr/decision-129.md). Preserve INV-010/011/014/015 and truthful
artifact, operation, rollback and remaining-host-hold evidence. No runtime or
schema change is intended in this closure package.

## Validation

Planned, not execution evidence: independent source/artifact/host-ledger and
commit/task/contract audits, local tag preconditions/result, record/link/parity/
whitespace checks and full NAS-masked `scripts/check.sh --with-build`. No host
workload, archive initialization, remote push or external issuance test runs.

## Execution notes and handoff

Activated 2026-10-18 after OPS-018 committed as
156506f5f409296ec3288b414d9a99542e38e8e1. This exact reviewed deployment/evidence
commit is the intended local tag target; immutable application source remains
4088994. Root creates a separate clean target checkout and runs the fresh
NAS-masked full gate before creating any tag. At activation no v0.2.1 tag existed;
proposed commands/identities are not completion evidence. No runtime, application/image input, installed
configuration or host-policy change belongs to this closure. Local protected
evidence records and the authorized tag are its intended host-local writes. Preserve rollback to 0.2.0 as reduced-availability
option with its known SELinux hold; never infer that unchanged schema alone
proves equivalent operating behavior.

### Reviewed target and deployed artifact identities

Root creates clean detached /var/tmp/hfcache-rel014-reviewed at exact intended
tag target 156506f5f409296ec3288b414d9a99542e38e8e1, with empty Git status.
This is the reviewed deployment/evidence commit, distinct from the clean artifact
source 4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b. Selected deployed artifacts remain:

| Artifact | SHA256 |
| --- | --- |
| 0.2.1 wheel | 2ffc0980a76603b5eeafec2a4f0a1fe2151fc58135b7c7107aec3bbf8cc2be7d |
| 0.2.1 sdist | 2ee02fdb80e6a3c87b6f250b69d1bf54bb613ac50fffc71939e1689ddc215ac8 |
| App image | e0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030 |
| Caddy image | fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10 |
| Release manifest | ab6c094292b05d99abbf5b8fb852b1a57a43e845041f00cc0cb94dcb8ef2e042 |
| Artifact index | 5baaa5e1cfc5a7d6b84a96ecb5c5ceac80ee56af0bd0f65b74b18d921efa9c9e |

Application metadata 0.2.1 is not byte identity; this task's ordinary gate builds
are not replacement production artifacts. OPS-018 owns the actual installed
peer/notify/TLS/isolation/drain/guard/state ledgers, including narrowly closed
connection hold 22 and retained 0.2.0 rollback limitation. All NAS/full-storage/
calendar/other-host/remote holds remain. No runtime, application/image input, installed configuration or host-policy
change is made in this closure task; protected local evidence JSON is new.

Fresh --with-build runs as the login user under a kernel empty read-only
TemporaryFileSystem=/srv/hfcache before collection, unit hfcache-rel014-gate,
invocation 0aa59f9451a34681bba8e37102ddcbf8, log .scratch/rel-014-gate.log.
At this running-gate checkpoint, completion and the local tag were pending;
no success or tag object was yet claimed. The final completion below records
the later actual gate and tag results.

### Actual release-state recheck

Root verifies protected host-snapshot-v2.py SHA256
e3fe192270cd3b61c301264fd70915b67793915f3e3eeec8d9c4de386ac7f365 and runs
--label rel014-release --version0.2.1. Protected
/opt/hfcache/deployment/20261018-worker-0.2.1/host-state-rel014-release.json is
byte-identical to the OPS-018 final ledger, SHA256
cd032e257cd1ffad4ec46172a3572f2f43572cc4872b4e2e0e7ccb8f4c6f1f31.
Exact roles/images, guard/locks/stores/secrets, NAS-ro/masks and socket209339
are unchanged. Current still selects releases/0.2.1; the manifest/index64 files,
wheel/sdist/build-record hashes reread match REL-013. No NAS I/O/job runs.

At this initial-draft checkpoint, .scratch/rel-014-tag-note.txt contained a
pending-gate placeholder and was not an annotated tag or passing evidence. After
the gate passed, Root replaced that draft; the same path now holds the exact
final annotation whose hash is recorded below.

### Independent release audit

Read-only audit releases without a blocker: all21 original feature packages
retain required order and same-commit task/progress/current evidence; REST
acceptance07ff468 directly precedes MCP-001d808a05 with no FastMCP dependency/
module at the REST boundary. Completed plans/history remain. Application modules,
locked dependencies, build scripts and tests retain the reviewed implementation;
README release-status metadata can differ, so rebuilt gate/closure wheels are
not assumed byte-identical to the deployed artifacts from clean4088994.

Actual wheel/sdist bytes, both source_dirty=false build records, installed images,
manifest/index and seven sealed OPS-018 records reconcile. Existing local
annotatedv0.2.0/object d7ad…/target11ddd55/annotation9aec… is unchanged;v0.2.1 is
still absent at this audit checkpoint. The draft note is corrected to the exact
compatibility claim,18 shared golden input files preserved, not18 emitted outputs.
All NAS/storage/calendar/other-host limits and reduced-availability0.2.0 rollback
remain. Actual fresh gate and local tag are still required before completion.

## Completion evidence

Completed 2026-10-18, REL-014, this commit. Actual NAS-masked
`scripts/check.sh --with-build` exits 0, invocation 0aa59f9451a34681bba8e37102ddcbf8,
elapsed 8m45.506s: 423 formatted/Ruff/whole types pass; 4,057 Python/40 deselected
in 472.40s; three actual locked base/server/server+MCP installation profiles;
135 Cockpit tests in 2,224.289125ms/build 1,190ms; four wheel smokes in 7.26s.
Log .scratch/rel-014-gate.log SHA256
4eeb49e580489f6e5be97feca64a077c16585551c7aa8c1f40dc2bc6495672dc.

Only after that pass, Root creates actual local annotated v0.2.1 in the main
workspace, identifying the exact target established by the clean reviewed
checkout:

| Identity | Value |
| --- | --- |
| Tag object | 9c8fc386387810435994f451e5d483c378f7651f |
| Reviewed deployment/evidence target | 156506f5f409296ec3288b414d9a99542e38e8e1 |
| Immutable deployed application source | 4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b |
| .scratch/rel-014-tag-note.txt SHA256 | 6da79f9ffbdead36d232722a3bed9fead7344eab8ca9fd60dfc28bf3756d2225 |
| Full git cat-file record SHA256 | bf1ec5e470f4d0adcb348ff72d71d40c546c73a4ef04752224baae9ba703a82b |

Annotation has no pending placeholder and exactly matches the retained note.
Existing v0.2.0 object d7ad2f180c5faeb289fe90ec9fff59fdaa0ebd4d/target
11ddd55dcb9e7b7be38fdfd076e54e2eadb460a3 is unchanged. Neither tag/branch is
published remotely. Deployed artifact hashes remain the table above; this later
records commit or gate artifacts do not become a new application/image source.

Reviewed INV-010/011/014/015 and decisions 65/75/79/115/121/126–129; actual source/
artifact/host-ledger/history audits and [progress audit](../../progress.md)
reconcile. Runtime, application/image inputs, installed configuration and host
policy are unchanged; protected local release JSON/tag are intended new records.
All five plan tasks are complete, this record closes the plan and clears only
its selector. Final links/records/whitespace pass; independent closure review
checks tag/source/artifact/hold distinctions. Independent actual-tag audit
verifies object/target, exact note/full-record hashes, actual gate outcomes,
clean reviewed target and unchanged old tag.

Hold 22 is closed only for installed 0.2.1 listener connectivity. All NAS I/O/jobs,
live full verification/storage/NFS workload, calendar and other-host checks remain
unrun; guard/original locks/NAS-ro/masks/stores/handles/secrets and Enforcing remain.
Retain all superseded/failed/stopped evidence and 0.2.0 rollback limitation. No
unrelated backlog is activated and no remote push/ACME action occurs.
