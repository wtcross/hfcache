# OPS-028: Guarded local installation while NFS stays read-only

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | REL-018 and REL-019 |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Guarded local installation while NFS stays read-only; actual Basic/UI/helper negative-permission behavior and reviewed recovery of the reported key.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Record exact reviewed IDs, amendments and any new decision before completion.

## Validation

| Changed requirement | Smallest meaningful check | Required gate | Evidence/result |
| --- | --- | --- | --- |
| Preserving protected backup | Fresh original config/store/candidate/outcome/credential identity inventory; original configuration mutex; local backup+compare; no NAS payload copy | `scripts/check.sh` | Actual backup1 a27e90ed PASS; protected controller a01478fc; 4259840B tar create/compare PASS |
| Actual executor drain/current-boot authority | API-first graceful drain, worker/Caddy/helper closure, actual PID/birth/cgroup/CID scan; five independently identified stock inert actors only; provision missing current-boot runtime originals after zero-executor proof | Same gate plus actual production observations | Drain qualification975ff742 PASS; original API lock27:1761 present/preserved; current-boot global27:3904 and companion27:4393 preserved; isolated activation20f05e26 PASS |
| Guarded immutable deployment | Both official stages/switch NFS-ro with original-lock handoff; measure expected47-file indexes; retain predecessor selector/releases/images and report actual legacy CID retirement; exact helper CIL/receipt/index/policy rebind | Same gate plus installed checks | Actual both47-file stages PASS783f0ed7; matching expected indexes c74a0879/e6aea3b0 and UID981 readability; guarded0.3.2 selected; predecessor selector inode retained; helper binding6d70998c PASS |
| First intent activation | Actual selected isolated no-network/no-NAS/no-credential offline role; original store locks/backups retained; correctly owned/labelled companion and initially empty authority for configured UUID | Same gate plus actual activation evidence | Actual official one-time activation20f05e26 PASS; coordinated backups and empty authority; never retry |
| Installed guarded observation | Helper READY before roles, actual worker/API confinement+PROBE, verified TLS/UI assets/original receipts, unchanged configuration/Hub grants and archive denied | Same gate plus scoped installed observations | Actual installed29-case TLS/API/PROBE/preservation9af02b20 PASS; genuine11-GET Basic/UI/helper/config20cbb254 PASS |
| Genuine original-key recovery | Real existing administrator Basic/UI, zero job POSTs while unavailable, exact own-key observation or reviewed retirement; original handles/history unknown retained | Same gate plus genuine human authentication/UI/API evidence | Genuine installed UI424b0954 and protected1e589900 PASS reviewed retirement; retired_unknown/handles preserved; zero jobPOST |
Every commit requires `rtk scripts/check.sh`; web changes require `--require-web`;
release acceptance requires `--require-web --with-build`. Preserve raw failures.
Do not invoke the optional instrumented functional runner.

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

Completed2026-11-05 after actual0.3.3 guarded deployment and supported genuine
administrator installed UI retirement. Historical attempts below remain intact.
Fresh coherent local backup fd6518aa and actual API-first drain53313b6c pass;
all original PIDfds exited, cgroup/thread/libpod closure and exact five inert
actors prove full drain. The first backup attempt refused root Git ownership
before backup/drain; retained failure, corrected observation executes as tyler.
Both official47-file stages c8f6ec43 pass, service-readable, exact expected
f1c55ed2/a638f833 indexes, app661da09f/source1652b8f/UIc9df46e1. Existing
images/releases/authority/companion/credentials/guard inodes retained.

Official guarded switch,18 exact physical leaf fcontexts and genuine measured
helper binding pass read-only completion792ec345. Original selector/index/policy
whole inodes retained. New indexae3bc6ab/policy058b53d0; all six grants unchanged.
Final publication check initially rejected expected /etc/hfcache parent timestamps;
verification accounts only those two timestamps, proves all unrelated files and
directory inode/DAC/context unchanged, and repeats no effects. CIL/kernel/receipt
and canonical bootstrap unchanged; no new module or intent activation.

Ordered helper READY/worker/API/Caddy actual receipt107e4e10 passes. Start observer
initially required notify for packaged API Type=exec; API was active, no restart
repeated. Continuation starts only Caddy and verifies all payloads. Helper430483,
worker6fb2b0fc/payload430792, API8d00255b/payload430903, Caddy66150572/payload431173.
Original guard/bridge deliberately inactive, no target/calendar enablement.
Automated installed receipt2514dbc1 passes29 TLS/API cases, REST/MCP separation/
14 tools, API-origin worker PROBE, installed client0.3.3, exact UI assets, original
five receipts/results, confinement and original local-state preservation.

Genuine authorized.env credentials stay in memory, never logged/copied. Sandboxed
Chromium executes actual installed UI; TLS CA+hostname verified before launch,
browser pinned to verified server SPKI. Supported original-key operator import in
separate diagnostic browser record leaves user's existing local storage untouched.
Actual explicit reviewed retirement returns200 then fresh GETretired_unknown;
original record762c47c1147542ce82edbceb0b7bd327/key695b24c7-437d-42ed-a91f-39dbc0cb58c7
and historical uncertainty preserved. Dispositionf096fda0b50161c1df4678326dbbd31d,
reviewfab7cf6f, authorityb5217fb9; original12 store files retain exact bytes/inodes.
Browser receipt424b0954/screenshot8256c891, protected combined receipt1e589900
under `/opt/hfcache/deployment/20261105-job-recovery-0.3.3/original-recovery1`.
No catalog-refresh/Sync replay or other job POST. Existing browser can reconcile
its original through GET; no local storage deletion or manual handle editing.

Separate genuine installed browser receipt5ebbc4da/screenshota10635ed proves both
Sync and refresh show “Unavailable: archive writes are disabled.” with Submit job
disabled, zeroPOST, readinessarchivefalse/archive_writablefalse and workeravailable.
Actual authenticated helper/configuration/original-intent GETs all200. No fabricated
principal, credentials reset, read-only bypass or password exposure.

Required current runtime strict gate is REL019 gate1:9935 backend, all strict
web/build/browser/wheel/three locked profiles,1284 frozen files unchanged,
raw logfec7fe00. Earlier OPS028 default gate3c06ce08 remains scoped old-runtime
proof; no redundant all-history matrix. Final factual alignment PASS216 human documents/29 helpers;69 focused docs checks PASS8.01s.
INV023 and ADR164/165 plus affected recovery/writer/deployment contracts reviewed;
source defect followed contract-first REL019. Production remains NFSRO/Enforcing,
archivefalse,configuration+hubtrue,control+observer+schedulefalse; legacy writers
masked. OPS029 now owns separate fresh writer transition, pilots/backfill. No
push/tag/image publication, init/manualNASfilewrite/reboot/disconnect/NASsetting
or other-host effect. Current-boot manual startup only; boot/independent other-host
holds remain separate.



2026-11-05: Start after REL-018 commit5d400d6. Artifact source remains clean
2d4c9cc; current production still0.3.1/c23abba, boot45d3ce1d, NFS-ro/Enforcing,
configuration/Hub true and all other grants false,165 configured selections.
Only original Caddy CID31283e65/payload2218 is active; API/helper inactive,
worker failed. All five original CIDs and12 store files are preserved.
Reviewed INV-003/007/020/021/023, FS-19/21–23 and ADR121/150/164/165 with the
current-boot transition, original-lock, recovery and hardening contracts. This
implements their accepted procedure, introducing no new architecture or grant.
The coordinator executes protected host steps; no coordinator model/effort
override is claimed because this interface exposes no such runtime control.
Retain the prior explicit high-effort protocol/confinement review and installed
qualification; do not create a model-tuning or new acceptance framework.

Actual read-only root review81ffe99b identifies stock manager1415/birth817,
PAM1445/birth822, broker-launch2083/birth909, broker2088/birth911 and
pause1953/birth889 with exact protected executable inode/argv/parent/context/
cgroup facts. These are a pre-drain observation, not zero-executor proof. Unknown
or changed actors refuse. Current-boot runtime recreation is distinct from old
inode preservation; persistent original locks and credentials remain in place.
The mandatory default repository gate runs alongside protected operations with
a private empty NAS shadow; actual host checks remain independently required.


2026-11-05 actual protected operations (ongoing, not package completion):

- Default repository gate PASS,1223.903865s, raw log SHA256
  `3c06ce08dd5e010982843cd33834cdef085f7503b073c82ccf1c31c58e642288`.
  Session52551 finished; do not restart a green gate without a relevant change.
- Backup1 `a27e90ed0f1f32525500ed6839406d70c06f608626bc7daa465bce12c5c56ad3`
  is root-private under `/opt/hfcache/deployment/20261105-job-recovery-0.3.2`.
  Configuration mutex, local tar/compare and exact original state inventory pass.
  Credential/HMAC payloads remain in place; only protected identity evidence is
  retained. No NAS payload copied.
- Actual drain qualification
  `975ff74205a65b5ba615d589367f02ed67769673f4d0f7216169f9b90645f885`
  proves official quiescence, original process closure, exactly five authenticated
  stock inert processes, no running containers, and unchanged NFSRO/Enforcing,
  original configuration/stores/guards/credentials. The worker remains failed
  with zero PID/tasks; this is explained quiescence, not a reset or restart.
- Correction to the pre-drain claims above: API runtime lock is present at
  `/run/hfcache/api.lock`,27:1761, and is preserved. The earlier missing-API
  assertion inspected the wrong path. Persistent worker guard64768:69642176
  remains unchanged. Only global and companion were absent this boot.
- The deployed0.3.1 official Caddy stop explicitly removed its exited CID
  `31283e65065bdae5098f771eb128c590190b986307d7bbaa7fd8916f162382a8`.
  Earlier all-five-CID retention was incorrect. Four original proof CIDs remain
  exited; predecessor releases/images, Caddy durable directories, six secret
  identities and available original journal are retained. No recreation or
  claim of CID preservation is made. Drain1 precondition failure, drain2
  zero-PID failed-worker postcondition and drain3 CID postcondition failure
  remain separately recorded; no stop request was replayed to repair evidence.
- Actual stage controller `f74d0c862d0a71310047facaa143226547a12e01cd19e3fd7ee2d1648710b622`
  PASS receipt `stage1/result.json`, SHA256
  `783f0ed7c996ce0f5525c9460f8026df29cc87df7bbc4fdfd22902ad832ad48a`.
  Under fresh drain/NFSRO and noncreating original-flock handoffs, it provisions
  absent current-boot global27:3904 once, imports exact local appimageef3 while
  preserving old images, and officially stages both immutable siblings. Actual
  guarded indexc74a0879 and writer indexe6aea3b0 match reviewed expected bytes;
  actual serviceUID981 can read all47 indexed files in each release.
- Current still selects `releases/0.3.1`; all application/helper/bridge roles
  remain off. No selector, new policy/module/bootstrap, companion/authority,
  service start, writable mount, archive job or original request replay occurred.
  Next: reviewed guarded selection and exact protected policy/bootstrap/intent
  activation, then actual installed observation and genuine administrator UI
  recovery. OPS-029 pilots/backfill remain pending.


Actual guarded switch1 now PASS:
`f6b474e56aafb6f6fda7e02eb425399172d8432dd7f09df778d2637b0eb7ebe5`.
Protected controller `3a2aeb1ad39a0615e3324129b87dcc9d474f6463288b75548932176b98ef4bc9`
freshly proves official quiescence/NFSRO, preserved config/stores/original runtime
and worker guards, both immutable stage and exact execution bindings. It saves
manual rollback/startup prerequisites before selection, preserves original
current symlink inode64768:71286657 whole in
`guarded-switch1/original-current-link`, and hands original27:3904 flock to the
official installer. Current now selects `releases/0.3.2-guarded-readonly`, actual
indexc74a0879. All services remain OFF and NFSRO/Enforcing; no new helper module,
bootstrap, intent activation, credential, mount or job effect. Next protected
step is fresh policy backup/qualification and exact label/bootstrap rebinding,
then one-time isolated intent preparation and ordered startup. Do not rerun the
completed backup/drain/import/stage/switch or green gate to improve presentation.


Protected helper policy installation2 PASS
`aba7107afab6c212f06ca6ba515c80c96b14a288e7be722e79e2d2fecc61de8a`.
Controller `daea17ebf8ce79ce0d561fd88843c86c21cf6e2275dd9df8f2d2ca19ad031cd0`
retains predecessor CIL and receipt whole, takes21166080B policy/config backup
with successful tar create/compare (credential/HMAC payloads excluded), and
performs exactly one normal priority400 semodule installation of final CIL1fb78db7.
Actual kernel `b4e83af8a6aa09a8a0129cc143c209944665cde537bde4940e5b4ec01cb7e465`;
new version1 receipt
`4f7b631bce722b69f2b4f0d853357da6d4256a182aa8eaf6c44c27814ef6d89e`.
All other modules, booleans, existing fcontexts/config/store/credential/HMAC/
original guards/grants unchanged; Enforcing and NFSRO/full drain preserved.
Policy1 failed before backup/module effects because the production predecessor
has33 neverallow forms, unlike the later fixture predecessor's38. Actual form
comparison proves all33 preserved verbatim modulo whitespace and5 new writer
payload denials added. The corrected reviewed2 procedure asserts that exact
relationship; no production policy check is bypassed or strict-neverallow pass
claimed. Failed policy1 receipt/controller remain retained.

Protected fixed helper code/label installation1 PASS
`b24d19ff0a92febb394025c3372089944ea5449f4bdcf97f33bd24b1fa33551e`;
controller `c2819c4581245df4b5193e90f70e4343dbc9bb13b1e96841e72307b1d97acb61`.
Six changed original fixed bootstrap files retained whole before publishing
exact selected release copies with original modes/labels/xattrs; unchanged
helper service and host_selinux original inodes remain in place. Saved original
fcontext export and manual rollback before importing19 new exact regular-file
rules:18 launcher/unit leaves across both siblings and the absent companion.
Only18 new public leaves and original global27:3904 receive restorecon labels;
original global inode is preserved. No companion/authority creation, index/policy
publication, service start, mount/archive/job effect. Config/stores/credentials/
HMAC/grants and measured kernel/receipt remain unchanged. NFSRO/Enforcing and
full executor drain still pass. Next fixed runtime parents/engine labels and
genuine selected helper index proposal, then reviewed index/policy publication
and one-time offline intent activation before ordered startup.


Fixed current-boot runtime provisioning completed in protected controller
`c79fcc8fad0ab1fd48d59d05e6ede1eb71f8e07cccb4bba5a35e1b7ed36e55f9`:
existing engine runtime originals63:59,63:84 and shared-memory25:2 receive only
the persistent reviewed labels, with owner/mode/link/size/inodes unchanged and
no body read/map. Previously absent helper parents are independently created
root:root0755 and root:9810750 with exact runtime type. That phase's preserved
failure occurs only at the subsequent proposal because prepare-host-helper.py
is not a staged release member. Do not rerun completed provisioning.

Read-only proposal continuation PASS
`37f68cdd7bc275dd0c7ddc57348db93a05a6ebbf23170c6098e59d04e9b9ad9d`.
It captures the genuine clean source2d4c9cc preparation tool root-private,
SHA256 `e1f80f4369891b2a706dbdd5dd9041f4bc640d57d38efdd0ae66e7f8e6fa5323`,
which matches the frozen release source inventory, without adding a member to
an immutable stage. Under fresh official drain/NFSRO/original27:3904EX, actual
selected rootless inspection produces genuine candidate
`59e3fefa01f950c435243bdf1393a67b057670ab1ef02015952cd85ef5150a22`.
Its source, snapshot, guarded release ID/index, actual principal981 and reviewed
receipt bindings all match. No fixture identity or permission template is used.


Actual guarded helper binding installation1 PASS
`6d70998c6366e78600986e4b1c96748dd9c966e23986f9de1720d76f82f0cc5b`.
Original index/policy whole inodes are retained under `helper-binding1` before
publishing genuine index59e3fefa and policy
`76be13a66d79b7b954cf14d557d54406152315598e30284f0d2e0e5a2ea22ce2`.
All original six grants preserved: configuration/Hub true; archive/control/
observer/schedule false. Actual config/stores/credentials/HMAC and hardening
remain intact, under full drain/NFSRO/Enforcing and original27:3904EX.

One actual official offline intent preparation now PASS
`20f05e26bf4891e5d2c6d08827a4a29c2e68652f1f120a91b3a1454f175b9355`.
The selected exact image's fixed no-network/no-NAS/no-credential role runs once
under official original-lock handoff, creating validated coordinated initial
backups of both existing stores and an initially empty schema1 authority for
configured UUID `f2a38add-59c1-4c1a-a8cc-5ab8f22fa1e2`. Every original store
file's bytes and full inventoried metadata remain unchanged; original store,
API runtime, worker and global lock inodes remain. Published companion27:4393
is UID/GID981 mode0600, single-link, correctly labelled. The private temporary
companion is absent after same-inode publication. Authority entries are empty;
this does not assert nonexecution or replay the historical unknown request.
Configuration/credentials/HMAC/grants and NFSRO/Enforcing/full drain preserved.
Never rerun first activation or delete its authority, companion or backups.
Both manager reloads and helper-only NotifyREADY are the next startup step;
no application job, original submission replay or NAS write has occurred.


Both manager reloads and actual helper-only startup PASS
`df4ea45170eb835444e1da7f74506a0ef9a6eb3ec2967d1dbfeec42d8941bf04`.
Helper389104 is NotifyREADY in `system_u:system_r:hfcache_host_helper_t:s0`,
NoNewPrivs1, CapEff0xc0; measured effective unit hardening and fixed authenticated
binding59e3fefa/policy76be13a6 pass. Original guard remains deliberately inactive.
Configuration, all operation/activation-backup stores and permission values stay
unchanged. NFSRO/Enforcing remain intact. Fixed worker, API and Caddy are now
being individually started in that order with exact image/CID checks; this
invocation does not activate user default target, bridge, schedules or grants.
Runtime readiness alone is not TLS/API/PROBE or genuine Basic/UI acceptance.


Actual individual application startup continuation PASS
`b818b5b1655d59df52deefa8683f968d42ce68375857094ac81025dcb97a27ae`.
Worker CID5be6443f/payload389301 and API CIDe85bbc46/payload389368 run exact
appimageef3; Caddy payload389677 runs exact imagefa2. Startup1 correctly starts
worker and API once, then its immediate inspection races the Type=exec API
launcher before Podman creates the CID. Original failure phase/API stderr and
already-successful worker receipt remain retained. Fresh observation proves the
same original API launcher389319 and exact new CID running; neither worker nor
API is restarted/replayed. Continuation starts only the still-inactive Caddy,
then bounds observation of that same Type=exec launcher without another start.
Guard/bridge remain inactive; no default-target activation, scheduling, grant,
mount or archive job effect. NFSRO/Enforcing remain intact. This is startup
observation only; actual verified TLS/API/PROBE/confinement/helper negative-
permission checks, genuine administrator original-key recovery, then OPS-029
writer transition/selected pilots/backfill remain required. Next action is the
existing installed read-only acceptance adapted to actual0.3.2 identities, not
another source/fixture matrix or green repository gate.


Actual installed automated read-only acceptance1 PASS
`9af02b20e5ca66c7db9b33267dd1e1f9843d614fdd922c689d89a6010e4dd60f`.
The prior OPS026 finite validator is reused with explicit0.3.2 guarded release-ID
separation, companion mount, and actual OPS028 preservation/retention map. Original
TLS, REST/MCP class separation,14-tool allowlist, payload capability/seccomp/
readonly-root/mask and fixed-bind assertions remain; no fixture matrix is rerun.
Actual29 HTTP cases pass, API-origin private worker PROBE passes, installed
reader CLI reports0.3.2, UI manifest/member bytes match4156b2d9, and all five
original operation metadata/results read unchanged through the API. All12
original store files, retained original configuration authority/receipt and
credential/HMAC identities and guard inodes pass preservation. Initial empty
intent authority is unchanged. No job POST, Hub request, NAS payload read or
service mutation occurs. The checker explicitly retains its limit: podman exec
is not actual PID1 syscall proof; unchanged qualified PID1/alias-denial evidence
keeps its original scope rather than being called a new all-phase companion.

Protected trusted-terminal administrator handoff is installed, SHA256
`71647b3a2e4435b122d9872da6db56fa9b84b173395d8ceb41f72296fc2c4038`.
Exact validatorb4c9fa42 and runnerd5d48e83 are root-owned0600 under the deployment
base, with actual source/UI/deployment pins. Agent did not execute the prompt.
The user has been asked to run, in their own controlling terminal:

```bash
rtk sudo /usr/bin/python3 -I -B /opt/hfcache/deployment/20261105-job-recovery-0.3.2/run-validate-administrator.py --phase inactive1
```

It performs11 verified-TLS UI/assets/bootstrap/helper/config GETs, no JavaScript,
mutation or job, with the password confined to the human controlling terminal.
The existing browser profile must then review original record762c47c1 and, only
if fresh original observation remains unknown, use the supported reviewed
retirement, preserving handles and historical uncertainty. No credential reset,
fixture Basic donor, key-copying form, original refresh replay or browser-storage
clear is permitted. Genuine authentication and existing-profile action remain
pending; this is required human input, not another repository/test-harness gate.
Independent current-host documentation and read-only writer preparation continue.


Current public host checkpoint and agent environment/release/handoff now record
actual guarded0.3.2 identities, current-boot locks, completed protected steps,
legacy Caddy CID exception, genuine-authentication hold and unperformed writer
work. Historical0.3.1 records remain dated. Focused factual documentation check2
PASS69 in7.20s; raw log SHA256
`82991b11da144b3f1d076f60d2b438577190681dd006f1cd22482d2809947b56`,
private empty read-only NAS shadow/loginUID1000. Initial check1 passed68 and
refused the new public checkpoint's internal task link/identifiers; those were
removed from public prose while retained in agent execution records. Original
failed log72be45bc remains. No runtime source change or full-green matrix replay.
Read-only writer preparation now records156 current publications and232 retained,
with proposed32/32/32/32/28 batches and small configured pilot candidates. No
actual writer prerequisites are inferred from that inventory. Human terminal/
browser action remains pending; package stays in_progress and no commit claims
its genuine acceptance or the later production pilots/backfill are complete.


Genuine-authentication prerequisite rechecked after independent preparation:
`human-preserved-inactive1.json` and its host-status receipt remain absent; no
fixed validator/runner process is live, so this is not a running validation or
verified process wait. Authority remains empty and currentguarded0.3.2/Enforcing
are unchanged. The exact human action is prepared above; no password prompt is
run by the agent and no test/service/activation/job is repeated. Independent
read-only writer inventory/candidate/capacity checks have made concrete progress;
remaining OPS028 completion and all writer effects depend on genuine terminal/
existing-browser recovery. This is the second consecutive goal turn with that
same pending human prerequisite; goal remains active at this audit point.


2026-11-05 third consecutive genuine-authentication blocker audit: no
`human-preserved-*.json` administrator receipt exists, no fixed validator/runner
process is live, and original-intent authority has zero entries. Current remains
0.3.2-guarded-readonly, NFSRO/Enforcing. No verified process wait or successful
browser recovery is inferred. All independent protected deployment, automated
installed observation, documentation and bounded writer candidate/capacity
preparation are recorded. Remaining acceptance requires the existing human
administrator terminal and existing browser profile; the agent cannot replace
that principal or browser-held record. Task is blocked and thread goal will be
marked blocked, not complete. Six prior packages are committed; this package's
unfinished evidence/docs are intentionally uncommitted pending genuine criteria.
OPS029 remains pending, with no writer effect or pilot/backfill. Resume after
the exact prepared trusted-terminal validation and preserving original-request
browser action above; inspect actual receipts/authority before any next action.
Do not restart green tests or completed deployment phases while awaiting input.


2026-11-05 human authentication prerequisite fulfilled. User reports the exact
trusted-terminal command succeeded. Root independently reads the saved receipt
and verifies SHA256
`20cbb254bcded869bf1b43c0ecb68da0deb1cc29135747a1d88882a54e7b9a03`.
All11 GETs return200 over verified TLS: actual UI document/all indexed assets,
Basic bootstrap, API-origin host-helper status and managed configuration read.
Session identity is stable; no job/mutation POST, browser JavaScript or NAS
payload read occurs. Exact bound host-status SHA256
`daab65b4f0be385ba423676aa9a3ca32c4586968c4b8c4a8cd6607954d5f3ded`
proves supported rootless profile, source2d4c9cc/index59e3fefa/policy76be13a6,
correct configuredUUID, NFSRO/inactive guard, original configuration/Hub grants,
all other grants false and four masked inactive legacy writer/calendar units.
No password or authorization header is logged or supplied to the agent.

Task resumes in_progress to reconcile this new evidence; earlier blocked audit
remains historical. Original-intent authority still has zero entries. The saved
browser record's historical recovery is a distinct remaining criterion, not
implied by terminal authentication. User has now been asked to open the same
existing browser Operations record and report its fresh original admission or
explicit reviewed retirement, preserving original handles/history uncertainty.
No original refresh replay, browser deletion, credential substitution, writer
selection/remount/grant, Sync or backfill is performed while that step is pending.
Passing source/release/installed matrices are reused unchanged, not rerun.


User supplies actual existing-browser export: record762c47c1, original basic key
695b24c7, no operation ID, route/catalog/refreshes, original origin/prefix,
subjectarchive-admin/rest-writer/archiveUUIDf2a38add, epoch/instancec3f98a18.
Those handles match the originally reported request and remain intact. The
quoted “Outcome is unconfirmed...” paragraph is generic Advanced diagnostics
present in both predecessor and current UI; it does not establish that the
review control was invoked or failed. Source inspection confirms predecessor
c23abba uses Observe original operation, whereas current0.3.2 uses Review/Recheck
original request. Stable authority comparison intentionally excludes observation
epoch/instance and retains origin/prefix/subject/credential class/archive, so
an old epoch alone is not a reason to rewrite handles or add a bypass.
User is asked to normally reload the same existing tab/profile, preserving
storage, then use the current supported review/confirmation or report the exact
unavailable/error state. No source defect, deployed review success, historical
nonexecution, handle deletion or original refresh replay is inferred from the
warning/export alone. No tests or deployment phase is repeated.


2026-11-05 user explicitly supplies administrator credentials through ignored
project.env and directs the agent to use them to resolve the original issue.
This supersedes the earlier human-terminal-only restriction for these planned
supported actions. Credentials are parsed as data into memory only; neither
values nor Authorization headers enter logs, evidence, argv or Git. User's
existing.gitignore edit and.env remain preserved; do not stage the credential file.
Existing Basic bootstrap authenticates stable subjectarchive-admin for exact
archiveUUID. HTTP login username is distinct from the stable principal subject.

Operational review preparations retain all failures: attempt1 rejected a caller
username-versus-subject assertion before HTTP; attempt2 authenticates/reads
readiness but caller wrongly assumes an Envelope for the route's plain schema1
response; attempt3 GETs original unknown and receives middleware403 for missing
X-Hfcache-Request, before protected review. Correct standard Origin/JSON/intent
headers on attempt4 reach actual protected review and preserve503. The real
helper journal identifies missing root-provisioned.host-actions.lock in
host_actions.review_intent_history, not an authentication or archive-permission
failure. No original catalog-refresh POST or manual control-store write occurs.

Documented root host-history prerequisites are being completed under fresh
backup/full drain/original global+companion+configuration locks, with all grants
unchanged. First backup refuses the explicitly optional absent scheduled store,
before any stop/provision; failed tar remains. Corrected backup/drain/provision2
PASS `1964cea7df0bebd916fb0d8cafd431570309310e781f94225a6c12861bc7509b`:
all original executor pidfds/cgroups close, exact five stock inert actors remain,
old configuration/stores/guards/credentials unchanged; four original proof CIDs
remain and three operational CIDs retire through official stop's documented rm.
Only previously absent original root0600.host-actions.lock (inode138519863) and
empty root0700.host-actions are created with exact persistent labels. Existing
CIL/kernel/receipt/index/policy and grants remain unchanged. Matching ordered
guarded restart1 PASS
`6d4798a071e5323d523436cef80eb2aedea1f80b71fe414d7f017082107e70a8`.

Attempt5 genuine Basic review preserves503; helper identifies the other required
history root BACKUPS in the fixed timer drop-in parent, also absent. Full
host_actions._history and packaged optional tmpfiles set are now reviewed:
root history directory, original guard, fixed root0755 timer drop-in parent and
empty root0700.hfcache-actions are needed for whole-history review even while
native schedule/observer grants remain false. Completing the remaining empty
directories requires no timer expression, permission, unit enablement, policy
module/receipt/schema/source change or historical outcome invention. A second
fresh coordinated backup and complete real drain precede that explicit original-
lock provisioning. No automatic retirement retry or original job replay occurs;
only a measured follow-up after the named prerequisite correction is allowed.
NFS remainsRO and SELinux Enforcing throughout; all immutable archive evidence,
original states/locks/credentials and predecessors remain.


Actual complete history directory continuation2 PASS
`a5ca48a68ea3aaba5b3f44078fafaa01552a53ee4da47723776b29b819d10b83`:
first exact import refuses existing RHEL /etc/systemd/system equivalence before
creating paths; continuation freshly verifies completed full drain/original
locks and uses canonical/usr/lib/systemd/system rules without changing the
existing equivalence. No stop request is repeated. Only absent fixed empty
parent0755 and.hfcache-actions0700 are created/labelled; no timer expression,
enablement, module/receipt/index/policy/grant change. Ordered guarded restart
PASS `6de234631d2b693b875f1f6c2901a73abc7cc819e592010b4a8c1597d15fea52`.

Attempt6 now passes protected helper review without a helper failure but returns
HFAPI005. Exact installed application read-only `_archive_review` reproduces
QueryLimitError. Bounded application metadata-only directory observation finds
621 journals,2875196 totalB/largest13907B/no non-JSON entries. The shared1024
budget charges both enumeration and reads; this is a source conformance defect,
not justification to delete journals, bypass review or replay a job. Authority
remains empty and historical outcome unknown. OPS028 is blocked on necessary
REL019 fix/new immutable0.3.3 artifacts. Genuine credentials are available;
no further human authentication is required for the authorized actions.
