# REL-015: Prepare the merged repair release source

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Cockpit repair rollout](../2026-10-20-plan-cockpit-rest-rollout.md) |
| Depends on | Completed CPR001–009; main and both remotes at cdc35a4 |

## Scope and acceptance

Reserve unused0.2.2 after local/remote/protected-stage checks. Bump pyproject and
matching editable lock entry only; refresh release notes/README with both discovery
and Cockpit changes since actual installed4088994. State release preparation, never
claim deployment before OPS023. Preserve all old releases and completed records.
Record later explicit merge/local-deploy authority without renewing NAS workloads.
Run actual NAS-shadowed strict extended gate, no frontend skip. Commit this package
with completed task/progress/current next pointer, then publish main to both remotes
before host deployment. Clean committed source owns final build provenance.

## Contracts and validation

Review parent contract list, release/deployment/container/security/discovery rollback
and actual ADR/invariant index. No new runtime dependency, behavior, durable format,
architectural decision or invariant edit is intended. Existing fixture0.2.1 literals
are historical test data, not application version sources; do not bulk-replace.

Planned: `scripts/check.sh --with-build --require-cockpit` in an actual empty
read-only NAS-shadowed transient service as the login user; explicit frontend
gate if needed for clean release artifact. Record actual counts/exits/hashes only.

## Execution and completion evidence

Started2026-10-20 after clean main merge/publication. Read-only old-operation lookup
reports original0cb77c1c970e21033a9cab7fb8ea872d failed at2026-10-19T14:46:11Z.
Current original host guard/masks/NASro and candidate/backup/lock remain unchanged.
Next: finish version preflight, release metadata/docs and fresh strict extended gate.
Completion pending; no built/deployed/new-tag success is claimed.

Version preflight: local/Forgejo/GitHubv0.2.2 and protected stage/release paths absent;
initial GitHub DNS refusal passed on read-only retry. pyproject and uvlock change
only editable project version0.2.1→0.2.2 (uvlock--offline preserves94packages).
Original installed wait read returns exact sync failed/HFMNT010/exit20, runID
ca8e75548b784920b44bb638da1692b0, terminalstdoutSHA256
9c0b18f856db2a01bda7331238869ee904e5e820122075e28049e458af0f6b50.
This is the original deadline refusal, not a new submission or cancellation.
First NAS-shadowed transient launcher with regular-file stdout returned
“Remote peer disconnected”; authoritative lookup confirms unit absent/noPID/no
cgroup and original guard unchanged, no passing gate claimed. Preserve raw
/tmp/hfcache-rel015-gate.log. A separate documented pipe+pipefail+tee attempt now
runs under the same unused transient unit name, keeping PID1 output on a pipe.
Do not infer the installed symptom's cause from this unclassified launcher refusal.

Actual pipe-backed gate starts as invocation135107101a114644b8c9ba063138cef7,
PID1819645/UID1000. Beforecollection wrapper proves /srv/hfcache is tmpfs with
ro,nodev and empty private mount; existing host NFS guard/mount are untouched.
Raw /tmp/hfcache-rel015-gate-pipe.log. Gate remains running/unpassed here.
Cached pinned portablePython35,942,823bytes SHA86bf107f…38b74 is available;
login engine has pinned UBI micro/minimal/uv/Caddy donors, no pull needed.
OPS023 will freshly rebuild app and Caddy under the exact clean source commit,
rather than reattribute earlier provenance. Local protected backup/stage paths
and clean worktree/artifact paths are unused. No installation mutation yet.

## Accepted completion (2026-10-20, REL-015, this commit)

Actual NAS-shadowed strict extended gate exits0, invocation135107101a114644b8c9ba063138cef7:
5299Python/52deselected in702.67s,3locked wheel profiles, actualfrontend lint/style/
types/570unit0skip/110mounted/fresh production build;16build-marked/5335deselected
in44.59s. Service success/status0, runtime15min13.696s. Actual mounted result and
log SHA are in [rollout acceptance](../support/cockpit-rest-rollout/acceptance-record.md).
Existing first-launch refusal preserved; no source/installed-symptom cause inferred.
Locked docs188human/19helpers and diffchecks pass. Version metadata/lockonly
0.2.1→0.2.2, no dependency/runtime code/schema/architecture change. README/changelog
cover discovery+Cockpit and actual predecessor compatibility. Reviewed parent
invariants/actualADRs and agentINV011; no artificial ADR/register edit needed.
No production config/service/plugin/policy/stage change occurred. Original Timestral
terminalHFMNT010/handles, all locks/candidate/backup/guards and5guests remain.
NextOPS023 only after this green source is committed and both main refs published.
