# OPS-022: Configure Timestral models and trigger a scoped live sync

| Field | Value |
| --- | --- |
| Work package | `OPS-022` |
| Status | completed |
| Plan | [Timestral model sync](../2026-10-19-plan-timestral-model-sync.md) |
| Depends on | None |
| Scope | Installed archive policy and one supported four-model sync submission; preserve all deployment barriers |

## Scope and acceptance

1. Inspect actual selected deployment, effective protected policy metadata,
   original configuration lock, live guard and archive-lock identities, NAS
   read-only state, legacy writer masks, disabled calendars and pending work.
   Preserve existing receipt stores/handles and never infer executor termination
   from a client exit or an available lock. Keep secret values out of evidence.
2. Retain an exact protected pre-edit backup. Under the cooperating persistent
   `/etc/hfcache/.configuration.lock`, preserve exact base bytes and append only
   missing enabled `model` entries for `mistralai/Timestral-5M`,
   `mistralai/Timestral-28M`, `mistralai/Timestral-123M`, and
   `mistralai/Timestral-209M`. Every requested entry uses `revision = "main"`
   and `declared_dependencies = []`; retain all other installed configuration.
   Refuse unexpected existing entries or changed base bytes rather than silently
   retargeting policy. Protected candidate/backup/installed files remain regular,
   single-link `0640 root:hfcache`; preserve the original lock inode.
3. Through the fixed installed API client, validate candidate syntax and require
   `authority_compatible = true` with valid installed policy. Obtain a successful
   candidate plan restricted to the four requested model selectors using installed
   Hub authority. Preserve its idempotency key, operation ID and real result.
4. Recheck exact base/candidate and validation/preview evidence under the root
   configuration flock. Fsync and atomically replace installed policy, retaining
   the predecessor. Confirm installed validation succeeds with the exact expected
   candidate fingerprint. Repository-only changes use supported policy reload;
   restart no services. Failed confirmation preserves actual state and evidence,
   without a silent rollback or claim that installation did not occur.
5. Submit exactly one installed-policy sync restricted to
   `model:mistralai/Timestral-5M`, `model:mistralai/Timestral-28M`,
   `model:mistralai/Timestral-123M`, and `model:mistralai/Timestral-209M`.
   Retain the nonsecret idempotency key and exact operation ID, then observe its
   real status/result. Detached admission may establish the requested trigger;
   download completion is not required to report that it was triggered. Record
   pending/refused/failed execution accurately and distinguish it from successful
   publication. Never replay uncertain work under a fresh key.
6. Preserve independent guard, original archive/configuration locks, NAS-ro,
   writer masks, disabled calendars, secrets, operation stores, schedules,
   installed images/units/services and hardening. No manual NAS file operation,
   initialization, guard release, writable remount, privilege-policy change,
   deployment, tag, or remote publication is part of this task.

## Contracts, invariants, and ADRs

Reviewed [configuration](../../../configuration.md),
[operations](../../../operations.md), [API client](../../../api-client.md),
[server reload](../../../server.md#archive-policy-reload),
[configuration pipeline](../../../cockpit.md#6-configuration-editing),
[containers](../../../containers.md), [deployment status](../../../deployment-status.md),
and [environment limits](../../environment.md).
Review preserves technical `INV-002`/`INV-003`/`INV-004`/`INV-014`, `FS-02` and
`AD-07`, plus [agent `INV-011`](../../invariants.md), and decisions
[119](../../../adr/decision-119.md), [122](../../../adr/decision-122.md),
[126](../../../adr/decision-126.md), and [127](../../../adr/decision-127.md).
This uses existing operational interfaces and changes no invariant, ADR,
application behavior, dependency, image, schema, authority field, or confinement.

## Validation

Actual protected comparison, compatible candidate validation, successful scoped
candidate plan, atomic backup/install, exact installed fingerprint confirmation,
single sync admission and lookup/show observation are recorded below. Application
source remains the already validated `45f91c3`; no initial duplicate suite was run
before the operational action. No actual archive publication, successful sync
execution, or broader production acceptance is claimed.

The required `scripts/check.sh` exited 0 in NAS-shadowed transient service
`hfcache-ops022-gate`, as login user `tyler`, with
`TemporaryFileSystem=/srv/hfcache:ro` and inherited `INVOCATION_ID` and
`SYSTEMD_EXEC_PID` removed. Invocation: `d1c912ddb5d24d2f9f4fa138cc27edc5`.
Actual command (outer pipe used `pipefail` and retained both output streams):

```bash
rtk proxy bash -o pipefail -c 'rtk proxy sudo -n systemd-run --unit=hfcache-ops022-gate --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/env -u INVOCATION_ID -u SYSTEMD_EXEC_PID /usr/bin/bash scripts/check.sh 2>&1 | rtk proxy tee /tmp/hfcache-ops022-gate.log >/dev/null'
```

Protected `gate-isolation.json` confirms the gate process sees only an empty
read-only tmpfs at `/srv/hfcache`. Formatting, lint, types and documentation
alignment (180 human documents/19 helpers) pass; 4,315 Python tests pass with
40 opt-in tests deselected in 495.19 seconds. Distribution build and all three
locked base/server/server+MCP installation/import/help/version profiles pass.
Actual Cockpit lint/style/types, all 135 tests and production build pass.
Service runtime is 9 minutes 4.497 seconds. Gate log SHA-256:
`12b5779336ba2843d415f0e82b5850c2795fb6b8ab817acd9a6d3a4303725258`.
The same log is protected as `repository-gate.log` in the local evidence directory.
No extra build-marker, live Hub/NFS test suite or installed storage workload is
claimed; the actual four-model Hub preview and guarded admission are separate
operational evidence. After plan/task/selector closure, the two documentation
authority suites (`test_docs_migration.py` and `test_docs_alignment.py`) pass all
44 tests in 4.49 seconds in another NAS-shadowed service. Relative file links
and `git diff --check` pass.

## Execution notes and handoff

Activated 2026-10-19 directly from the user's request. This task authorizes only
the four requested model policy additions, validation/preview, and one scoped
supported sync submission. Earlier read-only rollout restrictions remain for all
unrequested actions. Existing permanent guard and NAS-ro can prevent execution;
retain and report that state rather than changing host policy to make sync pass.
Activation itself claimed no configuration installation, plan receipt, sync
admission, or gate result. Actual subsequent operational evidence follows.

### Protected configuration change and preview

Root prepared and installed the change under persistent configuration flock
device `64768`, inode `138322689`, using no-follow opens and exact regular,
single-link `0640 root:hfcache` checks. The same SELinux xattr is preserved.
Protected predecessor: `/etc/hfcache/config.toml.before-timestral-20261019`.
Full local evidence remains under `/opt/hfcache/deployment/20261019-timestral/`
as protected JSON records; no credential values are copied into this repository.

The original 156 enabled repository entries remain an exact byte prefix, followed
by precisely the four requested enabled `model`/`main`/empty-dependency entries:
160 enabled entries total. No other parsed policy fields changed. Fingerprints:

| Policy | Configuration fingerprint |
| --- | --- |
| Predecessor | `1d03fbf1d02b876f59a70a86c909e5f6b33dadf63a3fb85f747a1b13fe3a68a0` |
| Candidate and confirmed installed | `4c33dc7bb7a5f5573d8ae1e9b4a3e20eaac3b3a0759e30747c406ade655c7b8c` |

Measured file SHA-256 is
`2e352e4f928387366c4015ae75a75a547194dbf8d85ff4bb89c6ee480e070827`
for the predecessor and
`bb7299ea08fac7aceaad8d4b9fb5b7b9f69be29c058295befe5a56bd13e65a7c`
for the installed document. Independent read-only integration review verifies
exact unrelated-policy preservation and protected metadata.

Candidate API validation succeeds with valid syntax, valid installed policy and
`authority_compatible = true`. Candidate planning succeeds with exit 0 and all
four repositories available; `candidate-plan.json` retains the full resolved
immutable SHAs and exact result. Expected repository sizes:

| Model | Bytes |
| --- | ---: |
| `mistralai/Timestral-5M` | 20,854,471 |
| `mistralai/Timestral-28M` | 111,307,039 |
| `mistralai/Timestral-123M` | 490,456,595 |
| `mistralai/Timestral-209M` | 837,284,550 |
| Total | 1,459,902,655 |

Preview operation: `dce48b88efc51e59e2bf406a579f0832`.
Preview idempotency key: `timestral-preview-20261019-3d240671af004feb8c98f642ae4a6445`.
These sizes describe Hub planning, not archived or downloaded bytes.

Root atomically installs the exact candidate and syncs the containing directory.
Installed API validation exits 0 at `2026-10-19 13:46:09 UTC`, confirming the
expected candidate fingerprint and 160 enabled repositories without restart.

### One admitted sync and retained pending observation

Exactly one sync restricted to the four requested models is admitted at
`2026-10-19 13:46:11 UTC`:

- Operation ID: `0cb77c1c970e21033a9cab7fb8ea872d`.
- Idempotency key: `timestral-sync-20261019-410f6659ff9b48379249e7a167a36400`.
- `operations show` and same-key `operations lookup` at `13:46:39` and
  `13:46:41 UTC` both report `waiting_lock`, with no domain run or terminal
  result. Admission proves the requested trigger, not model publication.

The existing guard PID `809950` still owns the original archive flock,
device `27`, inode `2273`; NAS remains read-only. Both legacy writers and their
timers remain masked and inactive. All four original lock identities and both
operation stores are preserved, apart from legitimate API receipt additions.
Selected release remains `0.2.1`. No restart, image/unit/schedule/secret change,
unmask, guard release, writable remount, hardening change, or archive write occurs.
Independent integration review confirms `/proc/locks` attributes inode `2273`
to guard PID `809950`, all four lock identities and host NAS-ro are unchanged,
and exactly one new sync receipt exists without receipt removal.

Preserved orchestration refusals do not justify a repeated submission: an initial
root client refuses the wrong identity, and a service-user call from a private
working directory refuses before workload execution. The supported call as
`sudo -n -H -u hfcache` from `/` succeeds. After the one successful detached sync
POST, the custom transient root wrapper incorrectly expects a terminal Envelope
and stops on the valid admission object. Saved HTTP 202/handles remain intact;
subsequent correction performs observation only. No second sync is submitted.

Continue observation from working directory `/` as the service identity:

```bash
rtk proxy sudo -n -H -u hfcache -- /usr/local/libexec/hfcache-client --client-config /etc/hfcache/client.toml --json operations lookup -- timestral-sync-20261019-410f6659ff9b48379249e7a167a36400
```

Use the existing operation/key for all follow-up observation. Guard-held lock
waiting can eventually become a classified refusal; neither elapsed time nor
client exit proves completion. Preserve the guard and NAS-ro and report the exact
future result rather than retrying with a new key or asserting a domain run.

Final operational confirmation at `13:56:31/34 UTC` again validates 160 enabled
repositories with the same fingerprint and looks up the original operation as
`waiting_lock`, no domain run/result. `final-operational-check.json` retains the
exact added entries, original lock identities, host NAS-ro mount, active guard
PID and kernel flock attribution. No additional sync was submitted.

## Completion evidence

Completed 2026-10-19, this commit. Protected installation, successful compatible
validation/preview and one four-model sync admission with observed `waiting_lock`
meet the user's configuration/validation/trigger scope. Required gate exits 0;
invariant/ADR review finds no architectural or behavior change. The plan is
complete and the sole selector is inactive. [Progress](../../progress.md) records
completion and Operator handoff 23 preserves pending observation. Archive
publication, guard release and live workload acceptance are not claimed.
