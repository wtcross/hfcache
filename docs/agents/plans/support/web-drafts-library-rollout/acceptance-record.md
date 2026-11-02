# Draft-safe Library rollout evidence

## Current state

Source `c23abba45f8967d058983043b96843bef62e899a` is committed on main and
verified on Forgejo and GitHub. Existing local and remote tag refs are unchanged.
The physical selector identifies0.3.1/source`c23abba`, image716. Protected
backup/import, actual executor/helper drain, staging, guarded switch and helper
rebinding pass. The original startup refusals remain preserved; narrow label
provisioning and separately qualified recovery establish actual active services
and passing installed automated read-only checks below. A subsequent complete
drain restores the deliberate inactive guard setting; its receipt explicitly
records application_started=false. The subsequent final restart and complete
installed inactive-state automated checks pass. The final strict source gate
also passes. Genuine trusted-terminal administrator acceptance now passes all
eleven GETs, with protected receipts and preserved state as recorded below.
OPS-026 closes in this commit and the completed plan's active selector is cleared.
The deployed application source remains `c23abba`; the later operational commit
records evidence and documentation. Source fixtures remain separately scoped.

## Release source and gate

REL-017 changes only project version metadata among all 94 locked packages, plus
release/planning records. No dependency, backend/helper/runtime policy or durable
format change is intended. The strict web/build gate passes 9,594 backend tests,
4,115 combined web tests (3,757 unit), 16 wheel tests, three locked installation
profiles, 11 built browser workflows, actual 200% zoom and real API React reads.
All 1,252 frozen input names and hashes are unchanged; 95.17% line / 90.15% branch
coverage. Gate log SHA256
`a75e865acda3979de99234ad12b00771f56a9ceb92c9402a5e55531c5f9a2683`;
private-shadow log `c77e9ec240a21a583f94b4078b41ed26f0ca7b165c71cc5646cd5f04aec4e84a`.
The successful gate temporary root retires only after its complete verified
179,583-entry manifest (`f5338fca1548329e15710c5bee3d8b7080abe613500368ca6fc3a0131f98f7eb`);
all raw logs, reports and earlier failed archives remain.

Both branch publications are recorded under `.scratch/rel017-validation/` in
`initial-main-publication.json` and `release-main-publication.json`. Explicit
main refspecs disable follow-tags; no force or release-tag publication occurs.
The user's retained no-tag boundary is the narrow release-policy exception
recorded by progress decision 163.

## Canonical artifacts and exact-bundle browser evidence

Clean detached source: `/home/tyler/hfcache-0.3.1-build/source`. Canonical output:
`/home/tyler/hfcache-0.3.1-build/web-release`. Repeated backend and UI builds are
byte-identical; all 1,251 captured regular source members and 19 indexed artifacts
verify. The known CLAUDE symlink remains separately preserved by Git.

- Full source snapshot: `6ee85586b9af542d6e7285adeb72505cbdb8adb5c255109c201c8ca2672de898`.
- Web release index: `2ae5879ff72500235b2c042c85c1af56185a5e8eb6836fde44bec15bcbb84929`.
- UI manifest: `bca416c4e29febb2ce26b03e6344a7c0d6056f513b37e8d63626d2fe80586bf0`.
- Wheel: `3b9a1280e202d5f119638e00126ec9cf139fd3b20c22af3fed37197a2a0e7931`.
- Sdist: `e9da3c0ada17c01c235f4e9af6199b926eed4f0209f027e5b9ee739ecc9672e3`.
- Build receipt: `bb73a6a52e20782a20fd91386487507bc596db7f91924ccc4894840e09fc9810`.

The exact unchanged bundle passes all 11 owned browser workflows and actual
200% zoom. Browser report `fa4ebe971f69ab81154d61e78fe2136536ec0f91a4422b1234d92b573e8c214c`;
zoom result `7241349c175a464be809c9fe657b235d89f55304f707639ea91cf944855bdff0`.
Owned sandboxed browser PIDs close. At scrollY=0, mobile 390×844 search is
209.4375–251.09375 and first-result identity 820.921875–838.921875; desktop
1440×1000 search is 182.71875–224.375 and identity 636.125–654.125. Each fixture
has 25 rows and no document overflow. Compatible Next/Previous use four total
GETs and zero facets; initial/Refresh use eight API GETs with four facets. Changed
identity takes nine GETs with bounded restart, changed coverage/filter/page size/
history eight with fresh facets, then compatible pagination returns to four.
Actual tab zoom 2 maps outer640×1000 to 320×500 CSS pixels, DPR2 and CSSzoom1.
CSP/page/axe/unexpected-request observations remain clear. Artificial facet delay
is fixture evidence, not a production latency claim. Exact attachments remain in
`.scratch/ops026-build-preparation/browser-measurements-c23abba45f8967d058983043b96843bef62e899a.json`.

## First image failure and explained owned recovery

The official first image attempt fails at final-stage Python COPY with HOME
ENOSPC. Its intended final tag is absent; no final image is promoted. The four
new committed first-stage cache images remain preserved. The original image log
and failed recipe remain unchanged. The first launcher also cannot write its
result JSON because HOME is full; do not interpret an absent receipt as success.
Read-only inventory identifies 13 new volatile Buildah working containers from
20:34:07–23Z, with about 370 MB apparent temporary diff copies unaccounted for
by the initial budget. The initial estimate used final/intermediate layer sizes
and missed these working copies.

Only newly generated successful canonical-build dependency folders are retired
after full 19,212-entry inventories, inode/FD/map/process/mount proofs and
canonical/browser revalidation; their complete manifests and original recipe
remain. This removes neither tracked source, dist/reports, main .venv, root
node_modules nor any old cache. Actual immediate free-space gain is only
12,009,472 bytes because apparent allocation overstates reclaimable shared data.
Preserved main Python3.14.6 passes original build/foundation/worker/installer
script help/import readiness. The original precheck did not explicitly join
filesystem-root aliases. Retrospective independent review of both pinned raw
27-namespace snapshots finds no exact, descendant or ancestor bind-root alias;
receipt `87cae0bbf6e40f5d8a9613f2159c3f57668bb561f4c4150f15eb5e1821e26119`
agrees with parent review. This qualifies the actual retained observations,
without rewriting the original recipe, proof or retirement receipts.

The failed context and all 13 current working payloads are then fully archived,
including 20,294 entries, hashes, raw xattrs, ownership/modes, symlinks and whiteout
metadata. Every regular archive payload and metadata member verifies against
unchanged source; no payload is extracted. Archive bytes 152,435,086, SHA256
`4edaa6710387ed7a48ce732524001f916bb7b6fe1459dc0b7d8ee0f4d05dfeb7`;
manifest `0f6dde6c57ea7c5f20bbbe404834e3166ed19aa2189b1fe09b787af0e4479226`.
The v1 inventory refuses a mistaken 710 image-record count before effects: 710
CLI alias rows correctly reconcile to 705 unique raw image records. V2 records
the complete unique set. V3 fixes double-leading-slash normalization in mount
alias joins and obtains fresh all-UID inode/FD/map plus ancestor/descendant bind
proofs (334 processes / 27 mount namespaces / 40 roots, no hits) before retirement.
The accepted payload archive remains unchanged across these corrections.

V3 retirement runs under a private empty read-only archive shadow. Exact archived
APP context removal supplies metadata headroom; login UID1000 then invokes
Buildah rm on only the 13 full IDs, without force/all/prune/image removal. All
705 image records, 172 ordinary containers, 43 older volatile containers and all
other layer records remain identical. The complete failed payload survives.
Result log `7e4ff8b99a55a3815986a8d6546750cff1e9486a8f65019bfef025c00111142d`;
actual immediate HOME free412,696,576 and ROOT free1,296,666,624 bytes. Recovery
records remain in `/var/tmp/hfcache-ops026-capacity-recovery/`. A new attempt
requires a fresh context/log and an actual peak-space review; no blind replay.

## Successful second image and qualified runtime acceptance

A new independently reviewed attempt uses the pinned existing toolchain and
portable Python, canonical wheel/UI and read-only existing donor store through
an exclusively named ROOT graph/runroot. It changes no runtime dependency,
container recipe, production store or archive authority. The preserved main
Python3.14.6 invokes the unchanged standalone scripts; construction adapters
change only owned paths and interpreter placement. Source remains clean at
`c23abba45f8967d058983043b96843bef62e899a`.

- Application image: `sha256:716cb3c6aeb267b439c12ba6ca70e1d43c48ca89327623c4938a26a76ba0e6cb`;
  virtual size 205,713,873 bytes. Build record
  `6bb844d64b07ba1737d4418fa5f50be78c88a8dbff739a2fdfbf88b9c99e9a09`.
- Standalone OCI: `/var/tmp/hfcache-0.3.1-app.oci.tar`, 66,303,488 bytes,
  `508ff2d8c63e2ae0aac331c9f3850a21887fa5e4d3bfd3e84fbe88e86e4702f4`.
  Every manifest, configuration and layer blob verifies independently; its
  configuration ID and ordered diff IDs match the exact image.
- The new image loads only into the login builder's original default store.
  All original image/layer/container records remain preserved. Load receipt
  `e7ef7c35131dfa12ee85a69224f2c19186dd93e978eaaa82ee4d41ffa3bdbbf4`.
- Actual unchanged foundation, worker and Caddy-reuse commands pass. Proof hashes
  are respectively `a36ddf51d9f29aaa493033fe821dda8afad38a558954f47b4498485356f3a91e`,
  `8d2d3854ff774fabcba6b1ad91e685a0439398cb4d2c693801d1cd3ea8094a31`
  and `5f633e9eb4fe1b0e41b56a716e4863b1b479bb223112609134fb7bffdfbbf5b2`.
  These are owned NAS-free image/worker/Caddy checks, not installed acceptance.

The original probe wrapper exits 1 after those successful commands: its final
metadata-equality assertion did not permit the new image's legitimate keep-id
`mapped-layers` cache. Fresh read-only reconstruction proves that this is the
sole change to new716 storage metadata, with unchanged image configuration,
rootfs and every prior image/layer/container record. No command or operation is
replayed. Original exit-1 result
`fd42dc363961d226ea2b0dfaa2532dd7812042a917206b13d31d468d8c214971`
and log `9edc0fe504381c2045c09630e32d26df2e2be7a02d86f7d9f2b03e186e47f1ac`
remain. Recovery receipt
`00dfbcfb9cf9def5706df380c8fa26e3911fc2f53819420f6ae408b8765e2b0d`
supports explicitly qualified accepted summary
`f52801aacc13f5640cd36c7b9f43d07d0ed2d94fc5cfdee0ca39172fad9c7b75`;
it does not rewrite the wrapper as an exit-0 run.

## Assembled inputs, rendering and successful temporary-store retirement

Assembly and official rendering each complete with exit 0. New source input
`/var/tmp/hfcache-0.3.1-stage-source/container-release.json` has SHA256
`4cbd5e22e92ac229cba46517c04efdc85cd16e45b1ab86b9280da2940dc12e63`.
It binds the exact source/image, canonical wheel/UI/helper closure, copied APP
build evidence, actual probes and pinned default/worker seccomp profiles.
All four APP evidence files are copied before raw-context retirement can proceed.

Assembly receipt `40eefad798db7712251c90aad3d8731f2670f8947f1e49156ed8db243cce3f4d`
and render receipt `3151df35df8b086df189dce85d5d8a67e695b9c376a0c0f92fc17e3596cc6762`
retain their original successful logs. Compatibility receipt
`7f4dce059b2033b5df10660eaf663c439c1ce0807a67991102b598bdfcf93e44`
proves the rendered server changes only the UI manifest; client, Caddy and both
seccomp profiles remain byte-identical. Production configuration is not changed
or selected. The immutable input remains separate from later root-protected
capture, installation and operational evidence.

After standalone OCI verification and default-store runtime acceptance, only
the new successful ROOT graph/runroot retire. Complete 5,277-entry metadata,
file-hash/xattr/link inventory `371903ff63c2d18f0624eacafe1638b20a2b059f84f9f9fcd5787ae51d06d39c`
and compressed manifest
`b8e0137dd79753ddae3369c53da38cce9ffd4b24a709fdf7db32b702ea4b8a94`
remain with the independently verified standalone OCI and reproducible inputs.
Fresh all-UID inode/FD/map and exact/descendant/ancestor mount-alias checks precede
fd-relative removal. Context, TMP, code, reports, OCI and every original/default
HOME record remain. Receipt
`9f6037ef02e345875a6c63f232b61a1f2781b3e9c910f543fbfb1669b98f0174`
records ROOT free1,109,450,752 and HOME free260,780,032 bytes immediately afterward.

## Complete proof/context retention and actual capacity recovery

The five newly created stopped716 proof containers retire only after complete
15,634-member inventory, fresh PID/cgroup/socket/FD/map/mount-alias joins and
verified retention of every raw metadata and writable payload member. The notify
socket's `S_IFSOCK` evidence is retained as metadata after proving no live socket;
it is not a byte stream. Inventory
`e186158d101b1317606d97f08d0c5bcd0470a5a48871b2a9d1d691aaa7148be4`
and verified-archive receipt
`497276f8c810702a8b8c91a1cde88971edc94d395bbd2bb3ff1cdf55c987415c`
bind the 1,309,425-byte payload archive
`0f1808e6e60692f5953ba199ce262b03b494cf0bcee77933538a5cac81ba12a6`.

Exact five-container `rm` uses no force, retaining the sixth new Caddy proof
container. Receipt
`9b86ad71cc280c56f2c6de367aed8cf2dd997ad92003732bfe0f6e5f848d0b7f`
precedes separate exact716 image removal with `--no-prune`, receipt
`5c02846c1992da4977d03c849c79f134362060aa2f4df989a02ec782127acc07`.
All original705 images,172 ordinary containers,43 old volatile containers and
their layers remain preserved. The historical stopped proofs and acceptance
receipts remain unchanged; the complete immutable new image remains in the
verified standalone OCI. Production UID981's store is not accessed by this
login-builder cleanup.

The complete original failed-image archive is copied to
`/home/tyler/hfcache-0.3.1-build/preserved-failed-image-attempt1.tar.gz` with
unchanged 152,435,086 bytes and SHA256
`4edaa6710387ed7a48ce732524001f916bb7b6fe1459dc0b7d8ee0f4d05dfeb7`.
Byte/metadata verification and fresh no-owner/alias proof precede retirement of
only its explained new ROOT copy; receipt
`dd4dc3231bf78a1fb916691ebd74fed75e997afc2f67006244d9f73e49cb1b02`.
All failed payloads and original evidence remain retained.

Durability qualification: the original copy recipe fsyncs payload bytes before
restoring final metadata. The later parent-directory fsync does not explicitly
prove that final file metadata was durable before ROOT-copy retirement. Independent
review identifies this ordering gap; the retained HOME payload and all metadata
still match. A separately reviewed supplement fsyncs the final file and parent,
then re-verifies bytes and metadata; receipt
`e48645256bcec74d71029c752be7b0e692128992430066cebf9f2b4e2937a5da`
establishes current retained-copy durability. It does not retrospectively prove
the original pre-retirement ordering. Original receipts remain unchanged; no
copy, unlink or application operation is replayed.

The complete successful APP2 raw context is separately preserved at
`/home/tyler/hfcache-0.3.1-build/app-context-attempt2-preservation/context.tar.gz`:
36,194,141 bytes, SHA256
`d9c429ba3571a3d66453fbb779285dd5fc249f21f1dd8f9be63a1efbd298817a`.
All4,777 source entries and4,778 archive members verify, including every ordinary
payload hash, mode/owner, exact mtime, symlink and raw xattrs. Embedded, separate
and compressed manifests agree; source remains unchanged through verification.
Context prerequisites
`13f10b648f9ff394c9bdeaaba1b7e889981a490f449da28d5e76395ff2498c88`
bind the qualified probes and successful assembly/rendering. Verified archive
receipt `af1abe32e4b14e3eef47358bae515619e7144bae902490ca258f27e8d5d1afee`
precedes fresh all-UID owner/alias proofs, exclusive retirement intent and
fd-relative removal of only the original raw ROOT context. Receipt
`3d7770679dc0e17a20eae649f7a0e7c69da7c17ae8c30c686c2f2a48875ddc0a`
records actual ROOT available gain114,429,952 bytes to1,368,862,720, with HOME
available199,802,880 bytes. Allocation estimates never establish this headroom.
Detached source, canonical WEB/wheels/helper/index, dist/browser reports, main
.venv, root node_modules and every old artifact/cache remain preserved.

All second-attempt receipts remain under
`/var/tmp/hfcache-ops026-image-attempt2/`; production prerequisites are rechecked
at each guarded service transition.

## Protected production phases and preserved startup refusal

Root-private evidence below is retained under
`/opt/hfcache/deployment/20261102-web-0.3.1/`. Production backup, exact image
import, actual API-first graceful executor/helper drain, official staging,
guarded selection and matching helper binding complete with passed receipts:

- Backup `594f600007d025c1d4031e135592183899d14fcced72c5ff13200161fff2dfb1`.
- Import `40e4c0f2c57feb06d5cb5c72f5e7c4a32c7453b2211e2ebdb1fe78bbfdb8519b`.
- Drain/stage `e629c9f95ab4cf398629f7dcccd1639e4999afbbaa06eaa1d71a13b58bdbfd97`.
- Switch `2648d56885ee5db23b6bd4e8cfc8d6a8102ac2bc9b5e4ec450e5384d2cbb4a36`.
- Rebind `10decc96cd8dabf2d7e180dd19b2fc5b7eb6ffd87e6878820f72081010d8b169`.

The selected physical release is0.3.1 with unchanged reviewed artifact identities.
The original helper key/bootstrap/authority inodes and all six permission flags
are preserved: configuration and Hub true, archive/control/schedule/observer
false. Source construction and these guarded phases submit no job or replay.

The first start is review-required at bridge/user-manager activation. Original
receipt `0530b8829f581637d8c53a6009c548802fa458eaaad045e903526cafa77d409a`
retains the coordination configuration lock, performs no automatic cleanup and
leaves the helper READY in `hfcache_host_helper_t`. At that refusal, application
services are stopped and the independent active guard retains the original
archive flock.
The first audit-query diagnostic separately refuses, receipt
`17d3059422e79e936e397a0ec7acb694246b264b670131f61ea1ca5d58e7e433`;
it is not a successful audit or startup result.

Observed SELinux denial evidence identifies the user manager's `init_t` start
against the new target's `usr_t` context. Nine exact new physical0.3.1 unit /
launcher paths initially lack the persistent provisioning installed for0.3.0.
The [existing container contract](../../../../containers.md) requires separate
host fcontext provisioning before activation: only the reviewed exact unit paths
receive `systemd_unit_file_t`, and public executable launchers `bin_t`, followed
by narrow `restorecon -F` and full-context verification. The task amendment
records this prerequisite before effects. Preserve original bytes/inodes/modes /
ownership, denial evidence and `start1`; add no module/allow grant, recursive
release/NAS relabel or weakened confinement. A separately reviewed recovery must
re-prove original lock/guard/executor/helper state, without replaying any
completed deployment phase or domain operation.

## Narrow provisioning, preserved observations and accepted active services

The nine independently reviewed physical unit/launcher label rules are installed
under the existing contract. Receipt
`9cdefe248f034d6ba2c551cb7d22b39b63c0384ac3d7ed8145da106276103bab`
passes with original bytes, inodes, modes, owners and mtimes preserved. It adds
no module/permission grant, bootstrap change or archive access.

The first helper-drain handoff actually stops the helper, then its diagnostic
refuses from an inaccessible inherited working directory. Partial receipt
`ebd9ccb002bbb073f59e77c87925c3f03342cd2127f2a084b1878ddda8c05a03`
and original recipe60a remain; no application executor is signaled. A separate
completion starts from `/`, never repeats that helper stop, and proves zero
application/helper executors plus preserved guard/original locks. Receipt
`ce6f3af651fb5f3dc2319a46c18aa02a137021f347b4fc2b38ff7b9508438c6c`
retires only the exact parked root wrapper PID2478102 through its original pidfd
and default SIGUSR1 disposition. `start1` remains unchanged.

The next explicit start reaches active API/worker/Caddy/bridge and READY helper,
but its final cohort observer refuses. Original `start2` receipt
`82c94b4e6d51cf87b06c07c30eeb710c8d315859157d93fdeebb48fc1af36c33`
remains review-required, retaining its coordination lock. No exception text was
retained, so the exact observation cause is not established; an early capture
is a possible explanation, not a proved diagnosis. No successful aggregate is
invented from that failed observer.

Independent complete installed active-state acceptance then passes, receipt
`376cdb56b6eb162657cbe08d844f4c151b5afd054cb8614508b4dd267e9d4ee9`:
29 HTTP checks, verified TLS/credential separation, all14 MCP tools, API-origin
private-worker PROBE, installed asset hashes, fixed client version, original
five-operation observations, confinement and original-state preservation.
Positive Basic and positive HTTP UI-asset reads are explicitly NOT RUN and
require the trusted-terminal human validator; no bearer/helper-peer substitute
supplies them.

Existing-start acceptance
`35c312b25d34bc7744473cc753caa13403d4fc9abeca34d05643ae0cc2f079ef`
binds that complete installed receipt with two stable observations of all actual
roles/helper identities, original state and active guard. Services are not
restarted and no live application/helper executor is signaled. It retires only
the proven parked root wrapper PID2479373 and releases its original configuration
lock. The original `start2` refusal remains unchanged; actual accepted running
services are established by the later independent evidence.

A new full API-first/helper/worker drain then restores the user's deliberate
inactive guard setting. `restore-guard1` passes, receipt
`075f326defe8daf892d850413124a79dd16d17d107a5d97d765b875d2dd30e1b`,
with actual executor drain, original-lock preservation and application_started=false.
This is a completed quiescent handoff, not a final restart or endpoint check.
No job, archive payload read or operation replay occurs in these phases.

## Final restart and installed inactive-state acceptance

The separately reviewed startup observer adapter a5de permits at most30 seconds
only while known expected container names are missing. It observes the actual
notify-ready worker first, followed by API and Caddy; the original startup command
runs once. Admission, role/image identity and other lifecycle checks remain
strict. This is bounded observation, not repeated activation or operation replay.
`restart1` passes, receipt
`2f44db2dc012992a8200ad420b1b18482889fbb54aea73fc55ede6f63f72e0d0`,
with actual helper READY before bridge/API and started_guard_state=inactive.
Earlier failed observations and their original receipts remain unchanged.

Complete installed inactive-state checks pass independently, receipt
`c73abc854ab0154cd739d1e05fa017181c89a091e450e8364c6c376fc81a58ef`:
29 HTTP checks, all14 MCP tools, API-origin private PROBE, five original operation
reads, artifact/asset identities, confinement and preserved configuration,
candidate, stores, handles, secrets and original locks. The deliberate inactive
guard is restored with no archive-flock holder intentionally retained. Helper
startup remains disabled and bridge ordering unchanged; no boot acceptance is
inferred. No job, archive payload read, Hub request or operation replay occurs.

The protected administrator validator handoff binds exact0.3.1/source/UI/helper
deployment identities. Actual handoff file SHA256
`884d6af4c2b1e86c9dcef0ae7e97609c159705c0fb206be1da6be4c07936282c`
is retained under the root-private deployment directory. The user is asked to
run the genuine trusted-terminal `inactive1` validator; positive Basic and HTTP
UI/helper/configuration reads remain pending. Neither automated bearer checks
nor earlier release/fixture results supply that acceptance.

Audit recovery v2, receipt
`f14fc36b9df66de35d80d39a5050b0b0dc1f4ec96789ed6fba50d7423ed1d2df`,
observes zero matched records and zero query bytes; the root daemon reports
lost0. These observations do not prove absence of AVCs. The original journal /
audit diagnostic denial remains preserved. The later root journal supplement
`c0e8a26577f78c8558337cf7dd217b8d5d747bd6f98050247d9510daaab3df73`
observes the one preserved original unit-label denial and zero other matching
AVCs in its stated scope. It does not erase the empty audit query or original
journal denial, establish global absence, or add all-phase companion proof.

## Final strict source gate

The final `rtk scripts/check.sh --require-web --with-build` gate passes in
1605.718740940094s, as login UID1000 under a private empty read-only archive
shadow. Inner result and shadow both exit0. All1253 frozen source input names
and hashes remain unchanged. Raw inner log SHA256
`ca3bc290e49d9b7994853e22378b066d37d0d4cdf7ee9fb71ebcb481464e9a88`;
shadow `13263d5b69112224b104c14b89149082f68eb6730aba557a4aea940829e3c486`.
Actual counts are9594 backend tests,3757 web unit /4115 combined web tests,
11 built browser workflows, actual200% zoom, real HTTP/API React reads,
16 wheel tests and three locked base/server/server+MCP installation profiles.
Combined web coverage is95.17% lines /90.15% branches. Results/logs remain under
`.scratch/ops026-validation/`; original failed evidence is retained.

The final browser report is `web/.artifacts/browser-K8A5jv/report.json`, SHA256
`7d81dd7e4644b5de8b0ffb6efdfc83cbd8e659401e398dd114b78ca04afde22f`;
actual zoom result `web/.artifacts/library-zoom-D9lb9E/result.json`, SHA256
`32ad17450440174864af228649a0da0b463ec775556751a96cb0790f916858c5`.
These owned synthetic HTTP/API source fixtures observe the exact bca416c4 UI
bundle with no unexpected requests/CSP/page errors, not production browser
JavaScript/Apply or latency acceptance. At scrollY=0, mobile390×844 search is
209.4375–251.09375 and first-result identity820.921875–838.921875; desktop
1440×1000 search182.71875–224.375 and identity636.125–654.125. Both have25 rows,
no horizontal document overflow and initial8 API GETs/four facet reads.
Compatible Next/Previous each use4 total GETs/zero facets; explicit Refresh8/four
facets. Changed catalog identity takes9 GETs/four facets including bounded
restart; changed coverage/filter/page-size/history takes8/four, then compatible
paging returns to4. Actual tab zoom1→2 retains320×500 CSS controls/keyboard use.
Decoded attachment evidence is retained in
`.scratch/ops026-preparation/final-gate-browser-measurements.json`, SHA256
`97a61cccd7b783f6a9cba7eb05b0b74e1e3318e7482cef6315a18bb3bac3d3e3`.

Invariant/ADR review covers INV001–003/018–022, FS19/21–23 and applicable
ADR126–129/145–147/153–154/158–159/162. Exact versioned labels implement the
existing provisioning prerequisite; the bounded missing-known-name observation
wait relaxes no role/image/admission check. There is no captured application,
backend/helper source, runtime dependency or durable-format change in this
operational package. No new architecture/placeholder ADR or format drill is
introduced. Decision163's narrow retained no-tag scope remains.

Successful-gate temporary-fixture preservation passes, record
`4e84c8c110af17d31a11fe809b61da6b98600f9d9baa02f1637eb01e29046f62`:
179583 entries/596029476 regular bytes, complete metadata/file-hash/xattr/symlink
manifest `376f66628425ccdf26f951715b64fcebf6677de07dcd2c431b2ac2a803a51143`,
6297187 compressed bytes. Fresh global629-PID/27-mount-namespace checks report no
FD/map, exact/descendant/ancestor mount-alias, argv or Unix-socket owner hits.
Only the original generated temporary root dev64768/inode81824630 retires through
the reviewed fd-safe path, receipt
`cd1c0f68144d753ae44356dac9f000c78dade5240de8c98c45756ba9fcc5aacf`.
Raw logs, browser reports, source, old artifacts and root node_modules remain.
Actual available space afterward is ROOT1,221,750,784/HOME154,943,488 bytes.

Fresh post-gate live-state receipt
`9a2a362f6986ea888b486126fb07a391db52cd1cf3398c0016a3c8f458d149a5`
confirms the same three application PIDs and helper PID as final restart,
preserved rebound original state, inactive guard and no original domain-flock
holder. Neutral bindings still select sourcec23abba and the same artifacts.
No service action, operation replay or source/artifact change is performed to
obtain this observation.

## Former prerequisite at the gate-close boundary

This historical boundary is resolved by the administrator completion below.

The protected genuine `inactive1` administrator receipt is absent at this
gate-close boundary. The agent has no existing administrator password and must
not receive/reset it, substitute a bearer/hash or forge a helper peer. This is
not an attempted authentication or a failed-password claim. The exact remaining
acceptance is positive Basic, indexed HTTP UI assets, stable bootstrap identity,
actual helper status and managed configuration GETs with preserved permissions.
The user must run on this host in their own trusted terminal:

```bash
rtk proxy sudo -n /usr/bin/python3 -I -B /opt/hfcache/deployment/20261102-web-0.3.1/run-validate-administrator.py --phase inactive1
```

The fixed wrapper opens `/dev/tty`; hidden getpass input never enters agent
chat/arguments/environment/files. Only the protected sanitized result supplies
the unblock evidence. The user's asynchronous input remains pending; no earlier
release, source fixture or anonymous/bearer read can satisfy this clause.
Keep OPS-026 blocked, the rollout plan active and current selector pointing at
the prerequisite. No completed OPS progress entry or implementation commit is
created; the reviewed documentation/evidence package is preserved uncommitted.
All source packages already have their separate published commits. Successful
gate-fixture preservation/retirement and fresh final live-state checks are
complete above. Completion metadata/commit and final main publication follow
only after genuine administrator acceptance. Preserve
every existing archive/workload/calendar/boot/other-host hold.
Do not claim production Library latency, browser-JavaScript/Apply or NAS workload
acceptance from the exact-bundle fixture checks above.

Final evidence-only documentation checks pass: 213 human documents / 29 helper
alignments, 69 focused tests, and raw working-tree/staged whitespace checks.
Fresh Forgejo and GitHub main observations both identify full source
`c23abba45f8967d058983043b96843bef62e899a`. Local main retains the uncommitted
OPS package and preexisting root node_modules. Neither final human nor
host-status receipt exists; no administrator authentication is attempted.

## Genuine administrator acceptance and closeout

The user runs the protected `inactive1` validator in their own trusted terminal
and confirms success on 2026-11-02. The sanitized root0600 receipt
`/opt/hfcache/deployment/20261102-web-0.3.1/human-preserved-inactive1.json`, SHA256
`b362226107286e8f78adb8ae5fbe9162a6a7ad614f06849ba92bb9e2a6111876`,
passes eleven GETs, all HTTP200: `/ui/`, bootstrap twice, six indexed static
assets, `/api/v1/host/status` and `/api/v1/config`. Positive Basic, verified TLS,
HTML/CSP and asset MIME/hash checks, stable bootstrap identity, actual helper
binding and managed configuration reads all pass. HostStatus SHA256
`010fc59dbba0208bd445499a5940a51e7dee3a0e2346e3b3409bd57d46f138e7`
confirms clean source `c23abba45f8967d058983043b96843bef62e899a`, version0.3.1,
full snapshot6ee85586, deployment91d94458, preserved configuration/Hub-only grants,
NFS-ro, masked writers/calendars and inactive guard. No password enters chat,
arguments, environment, result files or agent authentication calls.

The independent protected review `administrator-accepted1.json`, SHA256
`b966c86de7dcf03f662c622da824f3ab738f577a1237a887fe0e20369dd9848d`,
checks the two receipts, pinned validator/handoff, deployed UI manifest and every
static asset body; original state and all three application/helper process
identities still match the accepted restart. The review's first read-only
assertion incorrectly treated the rendered HTML shell as an immutable static
member. `render_shell` substitutes public-path/bootstrap/fingerprint tokens;
review v2 preserves the genuine validator's HTML/CSP acceptance and checks static
hashes only for assets. Both review sources remain; no authentication, request or
service action is replayed. Accepted review source SHA256
`38bdfdd5eed99de0e14d50c6993ceda458a5a660e2487830b50a323c1b2f9d7f`.

All scoped acceptance passes. This OPS commit closes the plan and selector;
final exact main publication and unchanged-tag proof are retained in
`.scratch/ops026-validation/final-main-publication.json`. Application artifacts
remain the clean release-source `c23abba` bytes. The source-browser measurements
and request counts above are owned-fixture evidence; authenticated installed
HTTP reads establish no production JavaScript/Apply, NAS workload, automatic
boot, other-host or new all-phase syscall/alias acceptance. Existing holds stand.
