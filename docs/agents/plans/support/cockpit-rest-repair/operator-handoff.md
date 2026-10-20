# Reviewed source handoff and separate installed acceptance

CPR-009 scoped source/disposable acceptance is complete; final actual gates pass.
The user authorized source implementation and disposable local-host development,
including necessary service outage/backup/restoration while protecting NAS data.
This work leaves the production installation and NAS untouched. Later2026-10-20
user steering explicitly authorizes pushing the completed green implementation
branch to both Forgejo and GitHub after the incremental commits. No merge, tag,
force push, registry or deployment is authorized. Push outcomes are verified
after commit and reported separately; no success is predicted by this record.

## Source and artifact identities

Committed implementation through CPR-008:
`0dc2c93da04bd38f28770e2f3576f30720cf1533` on
`fix/cockpit-rest-api-alignment`. This final package changes documentation/evidence and adds the planned controlled
identity-skew presentation regression; it changes no runtime code, dependency,
durable format or application version0.2.1.
This final package is CPR-009, this commit; Git records its actual SHA. No invented
clean final-release hash is used.

| Layer | Proven identity and its limit |
| --- | --- |
| Accepted runtime source | Detached41d818e13c1f4860a286f24ba91bd0f384b09172 plus exact dirty two-file patch88458c1987140890a8f5cf40303516f89b0846f0eb4e3083394c52219dd6f66f; no clean-release claim |
| Runtime guard/helper | candidate-guard82e4d9cbd6d9de60c4495a2bfda5dadbd483be3f20f2d9f96b0e1bfe0b15fc78; container-service3e0a00ed1082c5be4bcc38572d083b0abc16b0a0e37d43be81bddbf925fe560b; exact current committed runtime bytes |
| Accepted browser | JS490e60045d3542e890d9c8ee3b809b8122d7ce7213f9f415774416988ca7903e, gzip2c15678047140e19f94f7dde41c9c4dd9f667b85c6f16ae299f3f740bb04929e; embedded41d/dirtytrue/input96fa3c7f220fddd342b9405df4d7532299289b2207a1376b5283e4f33ff7eaf7 |
| Selected physical source |0.2.1 indexef85e569767863271f86d00bf7a355e64bcec5a5f9ed2af6a66a19574daf872a; protected17-file map28ebe8f7bc9da8edc13abbdddfa504906ee4f5ebc9ef6595f478f2c7d70476b7; fixed launcher904413dda7f15ca5655c1e4d1b1c5926b8114addc493f76c2de416999c21c069 |
| Accepted application | Appimage sha256:a6dac03ffceb85636e0884876ba796ba81ef2559caa7ec897293444cbda0ee7b; wheel578fd699e5873ffdada5d1af4b3eddfe00772667ee1616badea31e0a1518392d; all90Python modules match source/installedwheel, moduleaggregate dc3b90cf2037ddce3f9079f6d4e337b3279a4042cf81cbdc52a394e6b75f2679 |
| Actual API target | Instance d92522e0dcf244e88ff642dc22f90fe9, guestUUID0891c8e0-0214-4246-9b7f-8b90c1ed4340, rest-writer, fixed local UDS/settings/Podman secret; profile390ff5505b4b881aaf4459627fffc9f5378b083881b68852c27b8fbb73f6fdc2 |
| Recorded production | Historical0.2.1 artifact source4088994/deployment156506f, retained in human deployment-status. No current production identity or original symptom was inspected/verified here |

Browser/source/physical selection/image and authenticated target are independent.
API metadata does not publish an authoritative running Git commit; exact image/
container/process and build closure proof is separate. Equal displayed0.2.1 is
never parity. The final gate rebuild embeds its actual committed parent/dirty
state; its output checksum is recorded in acceptance evidence. A Git-only change
need not invalidate normal Makefile dist prerequisites, so force a fresh production
build. README edits may change wheel metadata/hash while all90runtime modules
remain identical. Do not call the earlier fixture wheel/image a clean final-source
wheel or silently substitute a new hash for an old accepted artifact.

Final precommit gate artifacts: wheel638a3274349ddd98083a0ffd46ab993aa3e6925826457aa7771763ad5d2cec1b,
sdistba43dbbd54757a3caf992c03f5b0373b25779d596e87a9f4f87d32aee2c6a2b1;
all90runtime modules still match the accepted native wheel's dc3b90cf…f2679.
README metadata accounts for the different wheel. Final gate production JS
30e03a88a681ff195cfa476028211aad877c1d8a9e9b81faf0a3e61ee18651f5,
gzipf7e4779ed8fdcb38162b212c3aea39b98e9555c5d03aa77b50b9df01b52e57c6,
embedded parent0dc2c93/dirtytrue/input96fa3c7f…f7eaf7. These are truthful dirty
precommit snapshots, distinct from both the accepted native artifact above and
a future fresh clean release. [Final gate evidence](gates/cpr-009.txt) records
5299default/16build-marked/3profiles/570unit/110mounted plus separate explicitmake.
Final closeout metadata is checked separately; no clean production parity is inferred.

## Actual acceptance and remaining limits

Source/pure/actual mounted React/installed-wheel private authenticated UDS and
actual disposable Cockpit/PAM/systemd/rootless are distinct accepted layers.
Actual guest tests reproduce and correct timer MainPID omission, NUL text-channel
disconnect and enforcing PID1 stdout-file write denial. Original classified
candidate-write/bridge/terminated persists after real reconnect and explicit
inspection; another Validate stays disabled. No message-only installed fix claim.
[Acceptance record](acceptance-record.md) owns V01–V60 and final gate results.
[Runtime008](runtime-008.md) pins actual twelve-check proof and its exact files.
Native third-guest original lookup/wait after disconnect preserves the same key,
ID/run and durable result; fifth has zero jobs/imported handles. Running sizing,
full-sync/full-verify and maintenance uncertainty lifecycles are separately proved
by mounted/actual CLI-UDS tests, not inferred as native workload acceptance.

Production artifact parity, the original installed symptom and NAS/workload hold
clearance remain separate, unperformed acceptance. Keep existing read-only guard,
writer masks, disabled schedules, archive gates, root configuration lock, both
operation stores and original handles. A source or fixture pass grants no live
archive workload or configuration/service change authority.

## Later reviewed build and deployment steps

1. Review the final committed branch and choose a separately approved new release
   identity. Build from a fresh clean checkout of that exact commit with the
   pinned toolchains/lockfiles and no production credentials. Run the extended
   frontend-required gate and fresh production build; capture actual wheel/sdist,
   browser output+embedded input/source, immutable images and source manifest.
   Existing protected0.2.1 is immutable; never overwrite/reuse it for this changed
   source. No future clean hash/version is predicted by this handoff.
2. In a separately authorized maintenance window, capture actual installed browser
   (including per-user development shadow/cache), fixed launcher/helper, protected
   selected profile/index/image and running API/worker identities. Back up required
   configuration, predecessor, deployment/guard drop-ins, policy, stores and handles
   with appropriate private ownership. Record original lock inodes. Do not copy
   credentials into the browser, argv, environment or public evidence.
3. Follow the existing rootless installer and deployment quiescence/drain contracts;
   preserve actual admitted execution/private-worker result handoff and original
   lock ownership throughout the switch. Unknown payloads, busy locks or missing
   accounting block the switch. Do not auto-stop/kill, unlink locks, unmask writers,
   bypass archive gates, enable schedules or relax SELinux/systemd confinement.
   See [containers](../../../../containers.md) and
   [deployment drain](../../../../deployment-centos-stream-10.md#upgrade-and-drain).
4. Install only the reviewed public plugin assets with0755directories/0644files;
   use the documented readable staging/umask022 prerequisites and verify as the
   actual service/user identity. Keep private configuration/credentials separate.
   Verify exact served JS/checksum and active profile/image/CLI/API, then refresh
   through the documented Cockpit cache/shadow procedure. Displayed version or
   selected symlink alone cannot establish the loaded browser/running payload.

These are later operator steps, not commands run by this source package. Actual
installation and publishing remain outside this task's authority.

## Verify the original installed symptom separately

After installed artifact proof and explicit permission, first use the fixed
service-identity authenticated `version --server`/`client describe` read path.
Capture bounded stage/problem/process/API/domain evidence independently. Then
review one deliberate candidate validation: it writes a host file and may admit
Hub-contacting sizing for added/retargeted enabled repositories. A reviewed exact
comment/tag-only proposal can avoid that sizing trigger, but it still needs fresh
host permission and exact captured base/candidate guards. Preserve the original
root configuration lock and predecessor; validate/requiredpreview/install/confirm
remain separate stages. Do not casually rerun Validate as a diagnostic read.

A bridge or process failure preserves its original classified facts. An uncertain
write permits explicit noncreating exact inspection, then matching revalidation
without another write; uncertainty alone never permits discard/reinstallation.
Uncertain install needs exact installed/predecessor proof, explicit API confirmation
and acknowledgement. An uncertain job uses authenticated original-key lookup and
original-ID observation through the same captured authority, never another POST.
Missing history, absent candidate, reloaded tab or a healthy read proves neither
nonexecution nor success. Resolving the original installed symptom requires this
observed flow with exact installed identities; changed message text is insufficient.

## Rollback and retained local fixtures

Use the existing protected installer/drain and [rollback contract](../../../../deployment-centos-stream-10.md#rollback-compatibility).
Retain both releases/images, original receipts/results and scheduled/browser handles;
source rollback, client exit or observer stop cannot prove accepted work stopped.
Preserve backups/unknown files and the original root/domain lock inodes. No automatic
configuration rollback, recovery, cleanup or reinstallation follows uncertainty.
Read-only MCP retains fourteen allowlisted tools and credential/trust separation.

Five owned local guests remain preserved; ports are SSH/Cockpit respectively:

| Fixture | Last revalidated PID/starttime (UID1000) | Loopback ports / retained state |
| --- | --- | --- |
| Original older artifact |1422140/393250994 |22054/19054; original guard/masks/state retained |
| Clean timer refusal |1634668/394793949 |22055/19055; selected41d artifact/guard retained |
| Fixed-helper original operation |1655053/394913847 |22056/19056; originalkey65bcfd39-478b-4418-9180-45bb2a196f82/op457a424efb7be3cd24c1d6b12f6e9825/run e6e4d5a51cbe46efab2acaad5968a280; unknown candidate attempt |
| Confirmation refusal |1724602/395413371 |22057/19057; exact installedadc176…/backup5b516…/rootlock75519490, installation unconfirmed |
| Corrected full acceptance |1773207/396308915 |22058/19058; confirmed installed9abd2c…/backupd0f5f1…/rootlock75518786, later interrupted draft/cause/profile retained |

All host fixture roots are Git-ignored0700 beneath `.local-fixtures/cpr-runtime`;
no keys/passwords/rawTOML enter committed evidence. All five process/UID/starttime
and restricted-network identities were rechecked before this handoff, without
signals. Coordinators/holders expired naturally or completed; no pending automation
is authorized to change these applications. Teardown requires an explicit later
review of exact fixture ownership, synthetic roles, original handles/unknown state
and safe drain/accounting, preserving needed evidence before powering off only that
verified disposable guest. Nothing here authorizes touching the host NAS/archive
or production service. No cleanup happens automatically after uncertainty.

[Runtime provisioning](runtime-setup.md) also records twelve signed development
prerequisite RPM additions on the local host, with no upgrades/removals. Those
tooling additions and the retained disposable fixtures are the local-host
footprint; no production application/service/configuration was removed or replaced,
so no production restoration step was needed. Do not treat this record as authority
to remove tooling, power off unknown execution or alter the host archive.
