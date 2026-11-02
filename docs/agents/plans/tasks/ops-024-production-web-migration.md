# OPS-024: Migrate the guarded local deployment and remove its obsolete plugin

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Production web migration](../2026-11-01-plan-production-web-migration.md) |
| Depends on | [REL-016](rel-016-web-release-source.md) and [OPS-025](ops-025-preserved-rootless-account-home.md) for build/stage/selection; independent preflight/backup may run in parallel |

## Scope and acceptance

Build clean full-web artifacts, final rootless image and immutable staged release.
Capture verified root-private coordinated backup and actual config inventory.
Provision the user's hidden-prompt administrator hash separately. Preserve all
configured repositories and protected authority exactly. Reconcile guard drift
after actual executor drain, retain original local locks and restore independent
readiness gating before guarded selection. Deploy web UI, REST and MCP through
the existing HTTPS endpoint. Preserve then remove only the installed public
Cockpit plugin entrypoint, retaining old release and local rollback evidence.

No archive mutation, workload, timer enablement, forced termination, unknown state
cleanup, permission expansion, security weakening or remote publication occurs.
Unknown execution/identity blocks the switch. Optional privileged host-helper
activation is separately reviewed and never inferred from legacy grants.

## Contracts, invariants, and ADRs

The parent plan lists current contracts, invariant IDs and applicable decisions.
Record current-state review and any required contract change in this package.

## Validation

Completed preparation:

- Clean committed source `3d6670d8dd0e8f2c941991ce154ecca7ac63c73c`, detached
  worktree `/var/tmp/hfcache-0.3.0-source`, with captured source/backend/UI/helper
  closure and repeated byte-identical backend/UI builds. All seven construction
  phases pass once, sequentially, as login UID 1000 with private empty read-only
  NFS shadow. Full receipts stay under `.scratch/ops024-build-preparation`.
- Wheel SHA256 `ca3cf2bd31d35c96e212980c3d66435e7a5c1a9666444d16072f38f9f8fca4b8`;
  UI manifest `60c2cf945b46af7f92227c673e193bc9f4588c61a452fc7361e1615450ad1698`;
  web index `791b5ebb9b20da8861750ebcdbbc0940d453d2b6c9ccfa91230b0932a58c30e5`.
- Final app image
  `sha256:bcfccd85b263beaeed5d2c424d9b638f4f4a17406137def5aab1aa514e5cb68e`.
  Actual foundation and owned worker-container peer/notify/FD3/IP/credential/
  seccomp/original-lock proofs pass on this image. Unchanged Caddy's genuine
  original provenance, ancestry, binary/CA/capability/version proof passes.
  This is local fixture acceptance, with no production NAS bind or domain run.
- OCI archive 66,301,440 bytes, SHA256
  `06582873ad1f0410205d0b35fec0258d9fa0270b50c027a1084c93a552fb705e`.
  Manifest `e6e69df1b30931b086e34bc35a8200ab67e433a3081fc561a9786706306d175a`
  authenticates 63 inputs. Render comparison preserves original server authority,
  identical client/default+worker seccomp and Caddy apart from `default_sni`;
  only intended Basic/web/helper server tables are added.
- Root-private copies and independent official re-render verify under
  `/opt/hfcache/deployment/20261101-web-0.3.0/stage-source`, `reviewed-render`
  and `artifacts`; `protected-artifacts.json` records the exact identities.
  This has not installed `/opt/hfcache/releases/0.3.0` or changed `current`.
- Final preparation comparison again passes all original configuration,
  candidates/backups, lock identities, stores and handles against the coordinated
  backup. Actual 0.2.2 API/worker/Caddy stay active, NFS stays ro and all writer
  services/timers stay masked/inactive. No plugin uninstall, production image
  import, policy/module/label change, credential delivery, drain or selection.

### Actual installation checkpoint (2026-11-02)

- Protected administrator source validates against the application model; separate
  exclusive delivery uses host UID/GID 981 and mode 0400. Source is retained and
  no password/hash payload is printed. OCI import uses the preserved actual store.
  An expected-prefixed-versus-actual-bare image ID diagnostic was corrected;
  independent observation proves the exact image without a second import.
- API drains first with worker available, then bridge/worker/Caddy drain without
  forced termination. Original payload PIDs 2091/3051/3053 are gone and original
  stopped container IDs are removed by their reviewed launcher. Both managers,
  libpod/cgroups and socket accounting prove quiescence before the original
  dev27/inode1728 noncreating flock is acquired.
- Official stage authenticates 77 public release members, also read/hash-verified
  as UID981. Physical index SHA256
  `251958ef55288266385d0bc99079dc9fb3bfd676f9c656b188570e1042b7c635`.
  Actual guarded official selection now points `current` to `releases/0.3.0`.
  All original local files/stores/handles and lock inodes recompare unchanged,
  except deliberate local configuration/common-lock SELinux labels.
- Reviewed first helper provisioning installs exact fixed bootstrap, priority400
  module, bounded local object labels and fifteen-role receipt, new protected key,
  actual finite-home deployment index and independently all-false policy.
  Deployment SHA256
  `14157fe5779e58efbcbc72570136bfd5cb6fb4659d7919bcf325ee86f8095818`;
  original all-false policy SHA256
  `3761028f542df36fd8a08c0e9f83203f224c216c46f806c8fe169c0212e1efea`.
  Both managers reload. Actual confined helper reaches READY before bridge and
  all three new roles, with no restarts. Actual PID1 capabilities, NNP, seccomp,
  read-only roots and worker masks are checked; helper initial USER/private
  masked MNT observation is separate from negative syscall proof.
- Automated installed acceptance passes 29 HTTP checks, verified TLS, separate
  bearer/Basic/MCP boundaries, the fourteen-tool MCP listing, API-origin worker PROBE,
  exact original five receipt/result GET pairs and final original-state recheck.
  Result `installed-all-false2.json` SHA256
  `d3d42f643901b40bfa0f1881cdaecb3dac7fa451d5a5519833f7349940d92c37`.
  Fixed host client reports server0.3.0. A draft's local `ledger` scope defect
  was corrected after the first probe failed before HTTP; original script and
  failure are retained. Corrected validator SHA256
  `06aede2d709b15cf9516db68ccbd17063f52a203447e5854751150d55ec80f48`.

### Installed acceptance and retirement

The user's second all-false validator run completes its checks and durably writes
HostStatus SHA256 `974c14a84c7567896996ca5678c8dc3cc2cab9a4911e4dd218d1097942a45aa1`,
then refuses to overwrite the failed first report. Preserve both originals.
Pinned control-flow and reported traceback establish the qualified recovered
pass; individual second-run GET hashes and a final success receipt were not
persisted. Separate recovery record SHA256
`a95d47ffc288cb0f7e5ecf3849c2a7ea39b9732661c12c723bc59649e93998aa`
records that boundary. Revised human validator preflights fresh outputs before
prompting; no credential substitution or authentication replay by the agent occurs.

Independent grant preserves configuration+Hub only; policy SHA256
`0c189ae7c06dcee81f9ae86592ff821c1183d73969acec13d256a5008daf5a4b`.
The all-false policy inode remains retained. The user's fresh preserved-phase
validator passes ten GETs, including actual Basic/UI/assets/helper/configuration:
receipt SHA256 `379ee005af3ac2156b72fbe614335fbf638b8d81c860cf3daddd78b90932c2bc`,
HostStatus SHA256 `910d58de130282c2cc3600d6bc3cde08106acc0ff4a502ef6f5eedfdb5f5688a`.
Actual bound Podman6.0.2 helper reads pass; broader version/negative proof is not
inferred.

Exact public plugin symlink inode137967146 is retained by rename into protected
backup; old release assets, shared Cockpit/CA and configuration remain unchanged.
A separate actual API-first/helper-cohort/worker/Caddy drain proves current
PID/start identities gone and cgroups empty. Root stops the temporary guard,
reacquires original27:1728 and deliberately releases at zero executors, preserving
the user's intentional inactive setting. Explicit helper READY precedes bridge
restart. No selector/bootstrap/policy changes occur during this restoration.

Final automated preserved/inactive acceptance passes29 HTTP checks, private
API-origin worker PROBE, the fourteen-tool MCP listing, exact original five result pairs,
confinement/secret bindings and original-state preservation. Result SHA256
`74ee1a854a3299e809a9d24c98dc6333c0038fbcadd07182b8f8a4df14ab29ea`.
Human Basic/configuration checks precede the final unchanged-code restart; the
final automated run does not claim a new positive Basic request. See the
[acceptance record](../support/production-web-migration/acceptance-record.md)
for exact artifact identities and remaining workload/confinement companion limits.

Installed migration acceptance is complete within the current-boot read-only and
reviewed-restart scope. Final strict source/web/build gate and local tag pass.

Final gate1 passes lock/export/format/lint/types, then documentation alignment
correctly refuses a human-page link into agent execution records. Correct the
link without moving/removing evidence. All1234 tracked bytes/names, symlink
targets and HEAD remain frozen throughout that failed12.146s run; log SHA256
`87d4b929a066d0e8c4f6ba064c9472d4c151cade41fc3efb572bf378d1f47ef7`.
Retain gate1 logs/results/TMP and use new gate2 outputs/TMP for the final gate.

## Execution notes and handoff

Initial actual configuration has 165 enabled model entries and zero dataset
entries; preserve the complete actual bytes and any private retired candidates.
At initial inventory the independent guard was inactive and bridge readiness
dependency absent, although the NFS mount remained ro. Retained October 22 evidence
establishes this was the user's deliberate setting. Preserve it by default after
temporary guarded migration. Historical active-guard evidence is stale and
cannot authorize assuming readiness or permanent restoration.

Verified protected backup: `/opt/hfcache/deployment/20261101-web-0.3.0`, 48 local
files/514,987 bytes, original configuration flock held throughout; ledger SHA256
`c15401645b5e2d965db3bd9bec9b09112be80fd35c7aa756af3701bbf38537c9`.
All original configuration/candidate/backup files, lock identities, both stores
and handles recompare unchanged. Source parser 0.3.0 accepts all 165 entries.
The original five API receipts are terminal and never replayed.

Existing account home/store requires OPS-025's reviewed compatibility correction.
Actual Podman is 6.0.2 and exact stock configuration hashes match; positive
API-origin helper status/configuration compatibility now passes. Existing network-state child already
has its required label. No package update, account/store relocation or label
weakening is planned. Explained generated build environments were retired only
after complete inventories, no live references and retained artifact/hash proof;
all source, lock, wheel/UI/OCI and audit records remain. That preparation changed
no production service, archive or installed configuration; subsequent deployment
effects are recorded in the dated actual checkpoint above.

### Historical required input and resumption

The administrator hash was initially missing at
`/home/tyler/.hfcache-migration-private/ui-administrator.json`. The user agreed
to a trusted-terminal provisioning command. The first invocation was refused
because `rtk proxy` pipes stderr; a harmless TTY probe confirmed the cause.
The corrected command explicitly attaches all three descriptors to `/dev/tty`:

```bash
rtk proxy bash -c 'exec /home/tyler/Projects/hfcache/.venv/bin/python /home/tyler/Projects/hfcache/scripts/provision-ui-administrator.py archive-admin administrator --output /home/tyler/.hfcache-migration-private/ui-administrator.json </dev/tty >/dev/tty 2>/dev/tty'
```

The user subsequently reports successful trusted-terminal provisioning and asks
to continue. Its private source (UID/GID1000, mode0600, 207 bytes under0700) was
validated without exposing its payload and exclusively delivered. Never request
the password through chat, arguments, environment, files or tool transcripts.
Source and any failed/partial evidence stay preserved.

Resume by reconciling actual host/boot/configuration/executor state with this
backup and all immutable receipts, rather than replaying completed build, import,
drain, stage or selection phases. Scripts deliberately refuse existing outputs.
Root-reviewed preparation and acceptance sources are retained under
`.scratch/ops024-helper-preparation` and `.scratch/ops024-acceptance-preparation`.
Positive Basic/helper/config reads require the user's trusted-terminal validator;
REST bearers supply no administrator capability and a new exec peer cannot
impersonate the original API PID. Keep all-false first provisioning and separately
reviewed configuration/Hub grants, with all other categories denied. Actual
Podman 6.0.2 enforcing helper read acceptance is recorded above.

The user has been given the exact protected validator command with all descriptors
attached to `/dev/tty`. Equivalent protected wrapper
`/opt/hfcache/deployment/20261101-web-0.3.0/validate-administrator.sh` SHA256
`b68698bb0e7b743b0486f0640eb264b41d484a64a91bdb76005b85a341ec216b`
contains those same pinned arguments and passes shell syntax validation. It has
not run at that earlier checkpoint. Required outputs `human-all-false1.json` and
`helper/all-false-status.json` were absent then; their later outcomes are recorded
above. This input is
authentication, not another deployment approval. No administrator credential
substitution or direct-helper bypass is allowed.

Earlier read-only `checkpoint-preservation1.json` again verifies the original
configuration files/stores/handles, local lock inodes, NFS-ro, writer/calendar
masks and Enforcing state. At that point the old plugin entrypoint was present
and guard PID2178648 held original27:1728. Later retirement, guard restoration and
final installed acceptance are recorded above.

Source/code commits are complete; this package records final operational evidence.
The plan is completed and its selector cleared. The user's original replacement
instruction supplies the deployment authority; no remote publication follows.

## Completion evidence

Strict `scripts/check.sh --require-web --with-build` passes as login UID1000,
nice10, under a private empty ro/nosuid/nodev/noexec tmpfs over the NAS path.
Inner0/1539.304s and outer0/1539.637s; all1234 tracked file bodies/names, symlink
targets and HEAD remain unchanged. Backend9590/52opt-in deselected, web4051
combined,16wheel, three locked installation profiles, two Chromium startup
checks, real HTTP/API React fixture, formatting/lint/types/generated contracts
and docs213human/29helpers pass. Coverage95.02% lines/90.13% branches.
Gate log SHA256 `19a6def18e0d4270bc6662cc823a0150e4143304fc9524b80bd19aa26e18cc7d`;
outer log `6ce1f2ba09210d6e9ddff671560658324ff65fb8f68125a16124fe55c6080077`.
Failed gate1 and successful gate2/TMP/evidence are retained without cleanup.

Final post-gate preservation record SHA256
`725901e4eeff5595bdfc07667610a2b4686b365366bb2fac837e822d4e52619f`
again proves original configuration/stores/handles/locks, zero original-domain
kernel holders, intended inactive guard, active helper/roles, NFSro, masks,
Enforcing, preserved policy, retired plugin original inode/assets and retained CA.
Independent final review agrees:25 original files/12 stores, only four approved
local label ctime changes. No secret payload or NAS data is read by that review.

Local annotated `v0.3.0` object `013d982e71fcbd2a4eaad11f661326257e1dd28a`
targets exact deployed source `3d6670d8dd0e8f2c941991ce154ecca7ac63c73c`.
The evidence commit and artifact source intentionally differ. No remote push.
Reviewed INV-001–003/020, FS-19/21–23 and applicable ADRs remain intact; no new
runtime dependency, schema, privilege or architecture change occurs here.

Material boot hold: helper remains disabled and the bridge has no helper startup
ordering. After reboot/runtime-object recreation, independent root provisioning
of existing lock/shared-memory labels and runtime parents/binding, then helper
READY before bridge/API startup, remains required. Do not claim unattended boot
recovery. No reboot/new automatic root provisioner is performed. Broader NAS,
browser-JavaScript/Apply, other-host and new-host all-phase IP/inode-alias negative
companion acceptance remains outside this completed migration scope.
