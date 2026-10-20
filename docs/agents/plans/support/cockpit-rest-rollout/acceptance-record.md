# Local rollout evidence

State: REL015 and OPS023 complete. Clean artifacts, disposable proofs, protected
backup, guarded switch, actual installed acceptance and final extended gate pass.
Local annotatedv0.2.2 created; selector cleared. Final main publication follows
this package commit, with actual remote heads checked afterward, not preclaimed.

Evidence below is chronological. Earlier unused, pending, untouched, failed and
not-yet-selected checkpoints remain history; the final disposition owns current
scope. No historical failure or unknown execution is relabelled as passing.

## Authority and source

The latest user explicitly requests merge to main/push both remotes, followed by
replacement deployment on this host. Main was fast-forwarded fromdcc2c56 to
cdc35a487dd0d41990b4c3305dc645450943a2a3, preserving nine repair commits. Both
remote main refs were read back at that exact SHA before deployment preparation.
No force or tags were pushed. Earlier repair selector was inactive; the new
2026-10-20 rollout plan/task IDs REL015/OPS023 were checked unused and activated.

Preserved incremental repair commits: CPR-001 b40b443, CPR-002 92f19b5,
CPR-003 65b12d9, CPR-004 ca034e3, CPR-005 896003d, CPR-006 f0a35c2,
CPR-007 41d818e, CPR-008 0dc2c93, CPR-009 cdc35a4. REL015 is
1c685018803a365bbb8b0c1aad4b94709f60e7d7; OPS023 is this evidence commit.

0.2.2 was absent in local/GitHub/Forgejo tag refs and protected release/stage paths.
One initial GitHub DNS refusal passed on read-only retry without host/network
change. pyproject and uvlock change only project0.2.1→0.2.2, preserving all94locked
packages. Historical test fixtures retain their old version literals. README and
changelog distinguish candidate from recorded installed release and include tags/
discovery rollback limits as well as Cockpit source repairs.

## Read-only installed baseline (before deployment effects)

Host hfcachewriter.lab.cross.solutions, selected /opt/hfcache/current→releases/0.2.1.
Manifestab6c094292b05d99abbf5b8fb852b1a57a43e845041f00cc0cb94dcb8ef2e042,
index5baaa5e1cfc5a7d6b84a96ecb5c5ceac80ee56af0bd0f65b74b18d921efa9c9e,
source4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b. Appimagee0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030;
Caddyfa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10.
Actual service UID/GID981. Permanent system guardPID809950 remains active;
host /proc/1/mountinfo shows NFS4 mountid798/dev0:83 ro,nosuid,nodev,noexec.
Sync/verify timers remain masked/inactive; actual user API/worker/Caddy remain
running with original effective /etc/systemd/user fragments and no drop-ins.
All actual executor/container/cgroup checks still precede any later switch.

Existing config24905bytes/dev64768/inode138336766, predecessor24111bytes/
inode134411820 and candidate24905bytes/inode135083056 are root:9810640 regular.
Original .configuration.lock is root:root0600/dev64768/inode138322689.
No Cockpit policy file currently exists. Preserve these files/inodes; do not adopt,
overwrite or delete the candidate as deployment cleanup. Original domain lock is
separately guarded and must be freshly proved before handoff.

Original Timestral authenticated fixed installed CLI lookup from cwd/ as service
identity returns op0cb77c1c970e21033a9cab7fb8ea872d failed at2026-10-19T14:46:11Z.
Original-key namespace timestral-sync-20261019-410f6659ff9b48379249e7a167a36400
is unchanged. Explicit original-ID wait returns exact stored sync failed Envelope,
exit20/HFMNT010, Envelope runIDca8e75548b784920b44bb638da1692b0; stdoutSHA256
9c0b18f856db2a01bda7331238869ee904e5e820122075e28049e458af0f6b50.
This is the original admitted deadline refusal, not cancellation, replay, successful
sync/publication or permission to release the guard. Preserve the exact terminal
and all stores during protected backup/drain.

## REL015 source gate

First transient launcher with regular-file stdout refused “Remote peer
disconnected”, exit1, raw /tmp/hfcache-rel015-gate.log. Authoritative unit lookup
proved not-found/noPID/noControlGroup/noInvocationID, guard unchanged. No test pass
or installed-symptom cause is inferred from that unclassified launcher refusal.

Separate documented pipe/pipefail/tee launch runs:

```bash
rtk proxy bash -o pipefail -c 'rtk proxy sudo -n systemd-run --unit=hfcache-rel015-gate-20261020 --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/python3 .scratch/rel015-gate-wrapper.py 2>&1 | rtk proxy tee /tmp/hfcache-rel015-gate-pipe.log >/dev/null'
```

Invocation135107101a114644b8c9ba063138cef7, PID1819645/UID1000. Wrapper proves
tmpfs/ro,nodev/empty-private-mount at /srv/hfcache before collection, then execs
scripts/check.sh --with-build --require-cockpit with ambient invocation/PID fields
removed. The real host NFS mount is not changed. Actual strict extended gate exit0:5299Python/52deselected in702.67s, all3locked
wheel installation profiles, actual frontend lint/style/types/570unit0skip/
110mounted/fresh production build, then16build-marked/5335deselected in44.59s
(old-wheel2/smoke4/installedCLIprivateUDS10). Transient service success/status0,
runtime15min13.696s, CPU12min5.760s/memory1.3G/no swap. LogSHA256
ac3f7730fefc3c7e17f8e5ba2a55403abdd97517e0a612651d4b17807d716485. [Bounded mounted result](rel-015-mounted.json).
The first failed launcher remains separately recorded; no frontend skip is accepted.
Precommit gate builds remain dirty snapshots, not deployed clean artifacts.

## Build/deploy prerequisites at activation (historical checkpoint)

Pinned portablePython cache35942823bytes/SHA86bf107f65fc30b56f2b263b26797fcbb1661f5315910cdbf27f733eb8738b74
is present, and login engine lists cached pinned UBI micro/minimal/uv/Caddy donors.
No OCI pull/registry operation is needed or authorized. The existing builder may
fetch only hash-locked public Python dependencies during a fresh app layer; cached
foundation images alone do not prove the dependency-install layer is offline.
Fresh app and Caddy builds must bind the exact clean REL015 commit and supplied
wheel; never reattribute old proof records. Worktree/artifact/build/protected
deployment paths are unused at baseline. OPS023 owns the new protected backup,
actual executor drain/guarded selection and installed acceptance. No service stop,
configuration/plugin/policy write, release stage/switch or new tag has occurred.

## OPS023 clean artifacts and gates

Exact clean detached source1c685018803a365bbb8b0c1aad4b94709f60e7d7,
/var/tmp/hfcache-0.2.2-source; no tracked modifications after gates/builds.
Wheel b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503;
sdist f31056da02cc9d04f0a0a0d3e55526fc5821530a9d1f3374df169612744d607e,
under /var/tmp/hfcache-0.2.2-artifacts. Appimage
sha256:fec393646e8d87dcc5220ffe3cfb1014e6ff059af92e6669e9b3df34fb5d40d8;
Caddy sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10.
Fresh build records .scratch/ops023-{app,caddy}-build/build.json respectively
c69f499f9445c6493fcf8e8c52e9112ea9de250d9ec0fe8105f4a1ff703f6022 and
fb2d014fbd57226d708f18aef4776b097f4cb7397634ca47630012b1db394d49.
PortablePython3.14.6 cache and pinned OCI donors reused; no registry operation.
Initial hostpython3.12 build invocations refused before context creation; explicit
locked3.14.6 builds then passed, with both failed and successful logs retained.

Clean strict extended command uses the REL015 pipe/tee pattern with unit
hfcache-ops023-clean-gate-20261020, clean WorkingDirectory and
/home/tyler/Projects/hfcache/.scratch/ops023-clean-gate-wrapper.py. Wrapper proves
empty read-only tmpfs shadow before scripts/check.sh --with-build --require-cockpit.
Raw /tmp/hfcache-ops023-clean-gate.log SHA
a3b50c57e6dd8bed66d9ebdcd9944242c4976fd50855f3e528564f9e0e72da0e,
actual exit0/invocationb879c89e62ff40e9b8a71a52bb758912:5299Python/52deselected
780.72s, three locked installation profiles,570unit0skip/110mounted with
lint/style/types/production build,16build-marked/5335deselected47.97s.
Runtime16min47.538s/CPU13min17.481s/peak1756758016B/no swap. Separate explicit
make -C cockpit check also exits0 in the same clean checkout, raw
/tmp/hfcache-ops023-explicit-frontend.log. [Mounted observations](ops-023-mounted.json)
are controlled-boundary component evidence, not PAM.

Final production JSgzip c9fa36bf9d4a2bbb6e97d36807caad4e546e3e446c5b16d2f0db994eca2e6ff5;
decompressed d231cbcd23e5ce919417e084c6ee82aff3227d02077e4544b28026782dc85bcd.
Embeddedsource1c68501/dirtyfalse/input96fa3c7f220fddd342b9405df4d7532299289b2207a1376b5283e4f33ff7eaf7.
The mounted test bundle2f756b1e... is separately built and not the production asset.

## OPS023 actual disposable runtime

All fixtures use local synthetic state and no NAS bind/credentials/workloads.
No failed or uncertain fixture is automatically removed, replayed or rolled back.
Actual command families below use the exact image/source and derived seccomp
08f97ffb4a6e9b48dcf95ec19fd41432b766b2a69c42fcc4e5991dd1d571c221;
hostdefault ffba5b06a9343516f61d46b0e86c95448bbe2a94f26d5cb04f9c79c52382b1bc.

| Proof | Actual command/result and retained location | SHA256 |
| --- | --- | --- |
| App foundation | Clean Python scripts/check-container-foundation.py, exit0; /var/tmp/hfcache-ops023-foundation/proof.json; actual image ancestry/PID1/rootless/imports/CAs/confinement | 9d2e8bd94888930a1c5ab5e095b721af20cad3183ba2e324954a89bb1de09037 |
| Worker | Clean scripts/check-container-worker.py via global3.14.6 as981/cwd/, exit0; /var/tmp/hfcache-ops023-worker-service/proof.json; actualnotify/APIpeer/PID1companion noIP/credentials/sharedlock/reader/cleanstop/emptyoperations | fa15c4231e96b8ca7cf4e9f32af0e15c4bbe06ec8403af5e88d4d8f8f69a4926 |
| TLS/API/MCP/client | Clean3.14 .scratch/ops023-stack-proof.py, exit0; /var/tmp/hfcache-ops023-stack/proof.json; verified localTLS, separate REST/MCPclasses,14tools, denied readerwrite, original retained stopped containers | a5a29d6e59193198512868292dbdce0ff4d627b1120724274331d38fc0ac7801 |
| Domain | Clean3.14 .scratch/ops023-domain-orchestration.py with exact source/build/profile/driver hashes, exit0; /var/tmp/hfcache-ops023-domain/proof.json; three success modes and one full HFVER002/exit40, original keyed receipts, terminal observation before drain, lock/socket proof | 7dd73b6abc2c0c3fb4cb94ba9c904e491426588042d58aaca72debd333a9ba7a |
| Compatibility | .scratch/ops023-compatibility.py with absolute reviewed profile, exit0; /var/tmp/hfcache-ops023-compatibility;126 actual previous0.2.1/current0.2.2 reader rows across21families/3forms, installed module hashes bound to corresponding Git sources, legacy fixture/receipt preservation | 5de7b529150be9f39028bca56a0fe3d23d3a5d1b35e3fe9fc602d0ecd3693e66 |
| Caddy ancestry | Clean3.14 .scratch/ops023-caddy-foundation.py, exit0; /var/tmp/hfcache-ops023-caddy-foundation-python314; actual base/image inspect captures bound to new clean build, metadata-only ancestry | 05b8c565105e4ce502d270b53d9eb68e7507737b6b20d7986553c3b21bb45639 |

First worker attempt under loginUID1000 refused before workspace creation because
its user-manager private socket ECONNREFUSED; userbus itself connects. No unit or
container started. Do not restart that unrelated manager; retained five guests
remain. Healthy981manager runs the separately provisioned fixture successfully;
its original production services still run unchanged. Exported new app OCI
ec48b960f8307f62c85b4e4c12ddb255d2edcf62adc42d06e5ab2fcdb7732755 imported
to981engine, exact image verified; no running-role selection changed.
First compatibility attempt refused the relative seccomp path before workspace or
output existed. First Caddy ancestry attempt selected3.12 and refused clean3.14
parser import after read-only metadata capture; failed workspace preserved,
explicit fresh python314 attempt passed. These refusals are not passing runs.

Reviewed source assembly .scratch/ops023-assemble.py exits0:50files/1788150bytes,
126compatibility observations, source1c68501/version0.2.2, manifest
c54d8f6799fcd5ab8df6291e7fddf36bb92a091af11fcaef820713086d3200bc.
New .scratch/ops023-stage-source is unprotected build-user output only; not yet
staged or selected. Root-private backup and actual executor drain remain next.

## Protected backup and actual installation

New root-private /opt/hfcache/deployment/20261020-cockpit-0.2.2 contains35copied
local files/402065B, configuration/candidate/predecessor, effective units/plugin,
all6local control-store files, original locks/handles/secret metadata and both
old/new selected identities. Original credential sources stay in place; values
are not printed or copied into public evidence. Snapshot helper
dd2825d4ab37e72b151a872d47dd710c6ead21c274fcda3be0b12422ebb4cddf
holds original noncreating rootconfiglock64768:138322689/rootroot0600 throughout
consistent capture/copy/postchecks. Files and all nested directories are fsynced.
Before ledger SHAa59706053a8f3e8113ed1ad5d15375fdcf34d7531a70456cfbff2c26a792d3ac.
Original actual two API receipts are terminal: Timestralfailed, other succeeded;
none is discarded. First backup draft refused before directory creation because
it counted underlying autofs46 as well as actual NFS4ro798. The corrected helper
records autofs separately and requires exactly one readonly NFS/NFS4 mount;
explicit read-only preflight then explicit backup both pass. No remount occurred.

Root protected-stage.py SHA1766e8156a29c79c9a573ef7e312b6ee40d4e48ad29fe094e72113c7194f1548
copies only the exact pinned manifest/file hashes into protected stage-source,
then invokes the indexed installer with umask022. Exit0/new immutable0.2.2;
manifestc54d8f6799fcd5ab8df6291e7fddf36bb92a091af11fcaef820713086d3200bc,
indexbc40f9d7ce6add22554b3d930139eb7c84e4322220a7896c2328db340c1ad8bf.
stage-result.json SHAbc299d00039cda2e27d05ee6a0f092cf9008457bea36ff380f3bc350baa40d00.
Actual981 reads/hashes all64indexed files; login1000 reads exactly5publicassets.
Old custom SELinux labels are backed up (SHA3548b5ae5120b3c405eb5d3170d710fbcf1604aa2a3cb05a19051044a3840c28).
Four new version-specific rules mirror old rendered/container, units and bin
labels; scoped restorecon affects only new0.2.2, never NAS or oldrelease.

### Verification transport defect and explicit correction

Both static system and user verification commands returned0. The user invocation
incorrectly used the live981runtime. Actual systemd257-31 creates an in-process
test manager that unlinks/rebinds XDG_RUNTIME_DIR/systemd/private; teardown leaves
that replacement socket unserved while the real manager keeps its old FD.
This is an agent operational error, not a cause inferred for the original Cockpit
symptom. First systemctl --user APIstop returns Connection refused before effect;
authoritative authenticated userbus/Podman evidence proves original services still
running. No retry, kill, socket unlink or manager restart follows that response.

Owned isolated /var/tmp/hfcache-ops023-systemd-verify reproduces inode2493309→2493310,
afterconnectECONNREFUSED111 while original FD retains SO_ACCEPTCONN1. Both bus
addresses, unit/generator/config/cache/state/runtime paths are independently owned;
no real manager/service/credential/NAS action. ProofSHA
3d59571ee9184beeb84d8ed6d60af65d62fa7c27475f8e31d35ded36f2d3dfd3.
Installed libsystemd-core257-31 SHA
f17238bd4c1e33f852954b06fdced2c516c36865e947fc1c4877b4ef9b4bcaeb
and systemd-analyze f4185fc199cf7c766b8b659ea576aae36f9bfd26493b7a7b88f878ff71087300
disassembly confirm the upstream sequence. [Verifier](https://github.com/systemd/systemd/blob/v257/src/analyze/analyze-verify-util.c#L252-L288),
[socket lifecycle](https://github.com/systemd/systemd/blob/v257/src/core/dbus.c#L843-L1013).

One explicit authenticated981bus StopUnit API request returns originaljob1265;
observed success/inactive/MainPID0 before user lifecycle target job1270 drains
worker/proxy. Actual runningPodman[], original payloadPIDs absent, both sockets
removed and libpod cgroup tasks empty precede any manager action. Config/stores/
guard/NASro/masks unchanged. Protected restoration-before SHA
5ea0f607bbbf33e4f428c6d99eb6b96a1709773f64c2b832ded0e6ff3a814eb6.
One deliberate Manager.Reexecute through healthy981bus returns callerexit1/Remote
peer disconnected; method intentionally has no success reply. No resend occurs.
Read-only inspection proves privateinode2069 connected, same manager718635/
invocation764b8cd712f04c9d82a066dfd73d0ef5, appunits stillinactive and Podman[],
oldguard809950 unchanged. Restoration-after SHA
5f5b14020b8e0ec0d7655dfc44bd6e3c726a278701cc1142b2f082135d5b980d.
[Reexecution](https://github.com/systemd/systemd/blob/v257/src/core/main.c#L3027-L3084)
preserves unit state without default-target restart; [method semantics](https://github.com/systemd/systemd/blob/v257/src/core/dbus-manager.c#L1494-L1526)
require --expect-reply=no for a future deliberately reviewed call, followed by
actual inspection. The unrelated preexisting1000private endpoint stays untouched.
Future static user-unit checks must never use a live runtime/bus/generator path.

Root bridge stop exits0 with userroles alreadydrained; system archive target remains
active. First guarded selector helper refuses FileNotFoundError for internal rtk
before any guardstop/selection: root securePATH excludes user binaries. Failed
guarded-switch.json SHA99ad1e99d819784e8e9d7f72616b7d82029093375a4f0bc813010b41ae00afe3
retains actual oldcurrent/oldguard+originalkernel flock proof. No PATH widening.
Explicit new reviewed helper50593486c8f14b5d2e91b1a57c18185262c3d9a27f2639b83d15ca4c6f68b679
uses fixed absolute systemctl and a NEW exclusive guarded-switch-systemctl.json.
Its one installer selection passes, SHA
ec9a8e8d796089f0210392226c4fd8c68812943b4fd2c42f7eb891bae01e9d68:
current0.2.2; original domain27:2273 guard→installer→READYguard1868228,
invocation7cf576d8474f4790a6e70feadd27b3f4; configlock/config/stores/handles unchanged,
NASro/masks continuous. Unknown reclamation would retain root holder+locks;
none occurred. No application starts or selector replay/rollback in that helper.

Reviewed policy helper4e12c4b9183b35b79fe2f51c925f80899d7a60a29df901191b5fb5475f29f715
then creates exactly one rootroot0644 policy333B/inode136594217 under original
configlock, pinning actual source/index. SHA
088e24a2827290b7da10d8dbfefe2b0cb5b91115b61911a7fc7458f400c89601:
configuration:true, archive/hub/control/schedule/observer:false. All existing
configuration/candidate/backup/stores remain unchanged; no validation/submission/
installation/discard of the candidate. Narrow policy restorecon passes. Both
system and981daemon-reload exit0; root bridge start exits0 under exact READYguard.

### Actual running acceptance, original result and tag

Copied/hash-bound installed-acceptance.py
56b6a97d050414f6cf820d8b918c7dee54eba8b04d9788324549567a86907f58
runs as981 with explicit source/version/images/index/domain/newguard pins, exit0.
Private installed-acceptance.json SHA
e4d5563239a445a46d2f2b3f034038d2345540b3c543172923860dc37f16a83a:
64indexedfiles/9bindings rechecked after probes, verified actual TLS,13auth-class
checks/14MCPtools, actual API-origin private PROBE, worker notify-ready ordering,
actual PID1 offline/credential masks/readonlyroot/caps/seccomp/memory constraints.
IP denial is bound to the clean indexed PID1 companion, not invented from exec.
Actual root inspect-cockpit returns guarded/nfs-ro/held with exact source/index/
image/policy and configuration-only permissions; masks allinactive/denied.

New actual containers API f004089b757eb50cb68d8057b76d36ccf6c0446cc63447bc5fb27b2e9bd80e3a,
worker b67c047d1f3e3bac65ec1d98ac5fdc69e3792dde5f608dd9c57a7fdc3e1c2f01,
Caddy a4558ee7d1f79ff6074536d90c2dbda4849d056f0029c7522d9f4214fbdd2183.
Post snapshot SHA8b3d4f3a53e1fc2497dd6f617bd0a368de3a81010a0bd55d79d2ac40902c161e.
Preservation comparison passes all original configuration/candidate/predecessor/
locks, six storefiles and handle roots, all secret IDs/bytes/ownership/modes.
Actual default fixed host CLI localversion and authenticated serverversion both
return0/0.2.2, stdout respectively
bf4f68dcec4dd95bf827b10766e2536dfe8ad9292746dcff007476c1e747cef7 and
b5c7e58395c2ebd68027bb915533e015cd8ba887e9f662e15752afe9c786f89b.
Original operation wait afterdeployment returns20/HFMNT010 and exact same
9c0b18f856db2a01bda7331238869ee904e5e820122075e28049e458af0f6b50 stdout;
no new submission/cancellation. Recent AVC search finds no matches after activation.

After all required installed checks, clean worktree still1c68501/clean; v0.2.2
absent in local and both remote refs. Local annotated tag created with full
artifact/partial-acceptance/rollback/remaining-hold note: object
c69ef761829856bd995454129432f46f6b79dfc9, peeled target
1c685018803a365bbb8b0c1aad4b94709f60e7d7. No tag is pushed. Immutable0.2.1
and all backup/fixture/failed/unknown evidence remain. Production PAM/browser
candidate installation/original symptom, NAS/jobs/full verification, other-host,
export/reboot/snapshot and scheduling acceptance remain NOT RUN, never passing.

## Final package gate and disposition

After actual local deployed acceptance/tag and human-doc updates, the main evidence
working tree runs the entire extended gate again with actual frontend mandatory:

```bash
rtk proxy bash -o pipefail -c 'rtk proxy sudo -n systemd-run --unit=hfcache-ops023-final-gate-20261020 --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/python3 .scratch/ops023-final-gate-wrapper.py 2>&1 | rtk proxy tee /tmp/hfcache-ops023-final-gate.log >/dev/null'
```

Wrapper proves UID1000/emptyreadonlytmpfs NAS shadow/exactHEAD1c68501 and only
human/evidence Markdown changes before scripts/check.sh --with-build --require-cockpit.
Actual exit0/invocationef69c3d9423042df99d88289318b1b5f:5299Python/52deselected
704.87s, three locked wheel profiles,570frontendunit0skip/110mounted with lint/
style/types/productionbuild,16build-marked/5335deselected47.17s. Runtime15min16.141s,
CPU12min5.025s/peak1.4G/no swap. Raw logSHA
71cc2234bb9833fa87af225b652ede979fdb581c5565e60d4f43532b4b3fc2dc;
[final mounted evidence](ops-023-final-mounted.json). This main build is a dirty
evidence snapshot, never substituted for deployed clean1c68501 artifacts/tag.
Raw clean/REL015/final gate logs are retained privately beside the deployment
record; reviewed fixture producers are copied/hash-pinned under operator-helpers.

After full gate only completion/evidence/progress/selector metadata changes.
Post-completion documentation alignment passes188human/19helpers; the three
documentation/migration/historical-acceptance suites pass46tests in6.95s. Cached
whitespace is checked before the OPS023 commit.
All scoped required tasks pass, none blocked. No next task/historical backlog
is activated. Main publication to both explicitly authorized remotes uses
--no-follow-tags and exact head verification after this commit. The local tag
stays local; actual remote outcome is reported only after readback.

## Invariant and record review

INV002/003/005/006/010/014/015/016, agentINV011, CP01–14 and actual ADR65/75/79/
115/118–122/126–129/132/134–139 reviewed. No new architecture, dependency, durable
format or workload authority is intended. Old receipts/results, candidate/backup,
original locks, guard/NASro/masks, secret classes and all five disposable guests
remain. Never use source/fixture or metadata readiness as installed workload proof.
