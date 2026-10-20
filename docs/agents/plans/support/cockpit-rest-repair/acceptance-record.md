# Acceptance evidence

**State: scoped source remediation and required disposable acceptance completed.**
CPR-001–009, F01–F11 and V01–V60 have the actual qualified evidence below.
Original installed-symptom verification and NAS/workload acceptance remain separate;
source/component proof is never relabelled native or production acceptance.

## Activation baseline identity

This table preserves the activation/early-fixture evidence; it is not the current
corrected artifact identity. Current package and third-guest facts follow it.

| Item | Actual evidence |
| --- | --- |
| Implementation branch / commit | `fix/cockpit-rest-api-alignment`; reviewed HEAD `dcc2c562b52304541d0cb85d20fc046072038e79` |
| Browser build checksum / source | Baseline production JS (decompressed index.js.gz) SHA256 `b414e92f01a316ffec9a45528fa676899ee842b0c44526599e30be90d15026f0`; source dcc2c562 |
| Application / CLI source | Same reviewed baseline; no source drift at activation |
| Physical launcher and rendered profile identity | Production not inspected. Isolated older-artifact guest now passes authenticated fixed launcher/UDS and candidate validation; exact bindings and limitations in [runtime-004](runtime-004.md). Current-source real Cockpit/PAM acceptance remains required |
| Rootless image digest | Guest untagged immutable application `sha256:21cd4a2027cde144133d302d5abb803ddb1670b56a47b90c127e981be402258c`; exact wheel/closure and Caddy identities in runtime-003. V54 not passed |
| Cockpit / systemd / Podman versions | Disposable guest Cockpit368/systemd257-34/Podman6.1.0; host parity limits in runtime-setup. Source pin 47108e2f8ecac3cd71fb3372193dd0f9c0fba7b3 |
| Node / pnpm / Python / uv versions | v24.18.1 / 11.18.0 / 3.14.6 / 0.11.32 |
| Fixture location and no-live-archive proof | Repository-only Node fixture uses injected process/ports and synthetic strings; no host/archive commands |
| Original reported failure stage/problem | Unverified |

## Committed baseline and retained third-fixture identity

| Item | Actual evidence |
| --- | --- |
| Repository | Branch `fix/cockpit-rest-api-alignment`, committed packages through `41d818e13c1f4860a286f24ba91bd0f384b09172`, at third-fixture capture, CPR-008 working changes; no fabricated clean final-source identity |
| Application/CLI wheel | Python package bytes unchanged from41d; wheel SHA256 `578fd699e5873ffdada5d1af4b3eddfe00772667ee1616badea31e0a1518392d`, all90module paths/bytes equal source/wheel/installed; [installed evidence](gates/cpr-008-cli.txt) |
| Third guest and physical release | `cpr008-9e6c9b6666ad43f09a886dae844866c2`, source41d plus only reviewed helper patch, dirty=true; selected0.2.1 index SHA256 `a647abe437092b738175aad12b3f0650f1ce794d18667564657d232ad2790717`; [exact isolated provenance](runtime-006.md) |
| Host helper/patch/closure | Helper SHA256 `3e0a00ed1082c5be4bcc38572d083b0abc16b0a0e37d43be81bddbf925fe560b`; patch SHA256 `de72e26c1c0fc86ef33fad385af9bdab9c4a1e85d827e1c8000b3a793468ba3d`; canonical source files map SHA256 `28ebe8f7bc9da8edc13abbdddfa504906ee4f5ebc9ef6595f478f2c7d70476b7` |
| Runtime application image | `sha256:a6dac03ffceb85636e0884876ba796ba81ef2559caa7ec897293444cbda0ee7b`; unchanged exact app/dependency closure; third guest only |
| Served production browser | Decompressed JS SHA256 `da4a031bad73ed3ba1394096783c1b9c7ce14b6bedd915d2b9c390c6746e8b80`; embedded source41d/dirtytrue/public-input SHA256 `f08227a330ffd2a4df0d1f1d05ca143bf7497dd103bf69cb59553026cbead648` |
| Current runtime profile | Original guest guard held, guest-only fresh NFS4.2 read-only, SELinux Enforcing, control/configuration permitted; archive/Hub/schedule/observer denied. Actual launcher/authenticated UDS reads pass. Native PAM login and genuine privilege authentication pass; complete operation/interruption acceptance remains V54 pending |
| Separate execution layers | Pure/actual mounted React with controlled ports; actual installed wheel/private authenticated UDS; actual isolated KVM/Cockpit/systemd/rootless with no host shares, default/NAS route or production credential. Layer claims are qualified individually; production original symptom remains unverified |

## Accepted current disposable artifact (fifth fixture)

| Item | Actual accepted evidence |
| --- | --- |
| Repository | CPR-008 this commit on fix/cockpit-rest-api-alignment; prior committed41d818e and truthful dirty source snapshot, never a clean release claim |
| Guest / isolation | cpr008-pipe-d901b229bbca4eaf8a0520dbb91505b4; QEMU1773207/start396308915/UID1000, local0700fixture, restricted network/no default/DNS/NAS/host shares; [runtime008](runtime-008.md) |
| Selected artifact | Base41d818e plus exact product patch88458c1987140890a8f5cf40303516f89b0846f0eb4e3083394c52219dd6f66f; selected0.2.1 indexef85e569767863271f86d00bf7a355e64bcec5a5f9ed2af6a66a19574daf872a |
| Browser | Served/gate JS490e60045d3542e890d9c8ee3b809b8122d7ce7213f9f415774416988ca7903e, gzip2c15678047140e19f94f7dde41c9c4dd9f667b85c6f16ae299f3f740bb04929e; embedded parent41d/dirtytrue/input96fa3c7f220fddd342b9405df4d7532299289b2207a1376b5283e4f33ff7eaf7 |
| Physical source | Guard82e4d9cbd6d9de60c4495a2bfda5dadbd483be3f20f2d9f96b0e1bfe0b15fc78; helper3e0a00ed1082c5be4bcc38572d083b0abc16b0a0e37d43be81bddbf925fe560b; protected17file map28ebe8f7bc9da8edc13abbdddfa504906ee4f5ebc9ef6595f478f2c7d70476b7 |
| App / API | Unchanged exact Python/wheel578fd699…8392d and appimagea6dac03f…ee7b; APIinstance d92522e0dcf244e88ff642dc22f90fe9; reader/class/profile/endpoint metadata and secret confinement remain separately checked |
| Archive / guards | New guest-only UUID0891c8e0-0214-4246-9b7f-8b90c1ed4340; NFSro/originaldomain27:1969/guard6142/masks8/Enforcing preserved. Original rootconfiglock64515:75518786 retained |
| Native result |12/12 checks pass, exact confirmed434-byte installation/predecessor then separate interruptedwrite: candidate-write/bridge/terminated remains, explicit inspection matchesinstalledbase, candidateabsent and Validatedisabled. Zerojobs/no replay/install/cleanup afteruncertainty; [native](gates/cpr-008-pipe-browser.json), [physical/audit](gates/cpr-008-pipe-physical.json) |
| History / limits | All earlier guests/receipts/rootlocks/unknownthirdcandidate/unconfirmedfourthinstall preserved. Original job lookup/wait after disconnect is distinct thirdguest evidence; native running sizing/fullsync/fullverify is not inferred from fifth. Original installed symptom and clean production parity remain unproven |

## Work packages

Each task owns its status/evidence; link it here without duplicating mutable status.
For each completed package record its real commit and test/gate artifact reference.
An uncommitted result says `<CPR-ID>, this commit`, never a made-up hash.

| Package | Actual commit / evidence |
| --- | --- |
| CPR-001 | b40b443; [gate](gates/cpr-001.txt) |
| CPR-002 | 92f19b5; [gate](gates/cpr-002.txt) |
| CPR-003 | 65b12d9; [task](../../tasks/cpr-003-candidate-validation-pipeline.md) |
| CPR-004 | ca034e3; [registry](gates/cpr-004-registry.txt) |
| CPR-005 | 896003d; [boundaries](gates/cpr-005-boundaries.txt) |
| CPR-006 | f0a35c2; [gate](gates/cpr-006.txt) |
| CPR-007 | 41d818e; [gate](gates/cpr-007.txt) |
| CPR-008 | 0dc2c93da04bd38f28770e2f3576f30720cf1533; [accepted gate/native layers](gates/cpr-008-pipe.txt) |
| CPR-009 | this commit; [final gates/parity](gates/cpr-009.txt), [operator handoff](operator-handoff.md) |

## Validation evidence

For V01–V60, record the case ID, test name or runtime procedure, command,
fixture/source identity, observed outcome, pass/fail/blocker and evidence location.
Group cases only when the cited test actually covers every named expectation.

Baseline command: `rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts`, exit 0.
[Observed source defects and environment inventory](baseline-evidence.md).
V01/V11/V24/V27 defects were observed at baseline; their later repaired evidence is recorded in the rows below.

| Case | Evidence / command / result |
| --- | --- |
| V01 | Boundary normalization/runner and mounted QueryError pass all known stages; exact baseline loses problem/stage. `rtk node --test cockpit/test/failure.test.ts cockpit/test/runner.test.ts`; `rtk node cockpit/test/browser.mjs`. CPR-003 adds retained candidate stage/cause and exact read-only reconciliation, with pure/filesystem/mounted regressions; real runtime remains V54. |
| V02 | `cockpit/test/failure.test.ts`: Error/plain objects, malformed values, unknown problem contents, getter/proxy defenses, bounded validated fields; focused 24 passed. No arbitrary rejection prose retained. |
| V03 | `runner.test.ts` launcher/process/access facts and `failure.test.ts` finite status/signals distinguish categories without raw stderr. Mounted API adapter remains fixed. Actual real launcher cause remains pending isolated runtime. |
| V04 | `runner.test.ts` exact nonzero HFAPI/domain Envelopes survive rejected process; installed-confirmation postcheck remains stricter. Focused runner/failure/stream/container selection passed. |
| V05 | Existing runner/stream UTF-8/line/terminal bounds plus late handle/abort/callback regressions passed. Raw terminal bodies/unknown diagnostics withheld from browser activity. |
| V06 | `connection.test.ts` close/listener/retry/disposal cases and mounted D-Bus tests pass; at most two read attempts/one delay; no mutation replay. Real PAM/runtime layer remains V54. |
| V07 | Mounted real hooks reject prior read/unit generations and clear healthy evidence on refresh/failure; sequential polls. Exact baseline mounted stale-clear cases fail. |
| V08 | Mounted privilege/reconnect invalidation and pure mutation-generation tests pass. Portal actions individually gated. CPR-003 mounted tests additionally distinguish late valid supersession from genuine candidate-validation reconnected failure; actual PAM layer remains V54. |
| V09 | Source pass: `config-pipeline.test.ts` strict compatible proposal, 101-case focused suite; actual mounted Configuration tag-only install/confirmation and required sizing, 30-case suite. [Pipeline](gates/cpr-003-pipeline.txt), [components](gates/cpr-003-components.txt). Real guest layer remains V54. |
| V10 | Source pass: negative assessment and exact HFCFG errors retained; mounted field-location/message assertion, no preview/install. Same focused pipeline/component commands and artifacts as V09. |
| V11 | Source pass: authentic HFAPI003/017/018/019/HFARG/HFCFG failed Envelopes with data={} remain unchanged and blocked=request; mounted failed process/Envelope shows original code without assessment-schema replacement. [Evidence](gates/cpr-003-pipeline.txt). |
| V12 | Source pass: mounted writer refusal preserved, no fallback. Existing `test_candidate_presence_requires_writer_before_shape_or_syntax` exercises actual API authentication-before-candidate parsing in the default suite. This is not real installed credential delivery; V54 remains required. |
| V13 | Source pass: strict assessment matrix distinguishes syntax, incompatible/unknown authority and invalid installed policy; mounted policy refusal grants no readiness. No credential redirection/local fallback. |
| V14 | Source pass: same operational fingerprint cannot replace exact tag-only bytes. Real temporary-file helper tests and mounted tag-only installation/confirmation pass; candidate/base/backup and pre/postchecks remain exact. |
| V15 | Source pass for local UTF-8/NUL/1MiB bounds, no truncation and preserved HFAPI006 refusal. Mounted bounded escaped candidate exceeds 1MiB after JSON encoding and receives an injected classified CLI refusal; it makes no actual HTTP413 request. Candidate-specific real CLI/socket boundary remains V52; generic server body-limit regressions remain in the default suite. |
| V16 | Source pass: 62 real guarded-filesystem tests cover mode/link/symlink/FIFO, original-lock serialization, concurrent changed base and exact bytes. Mounted sizing followed by draft edit loses readiness. [Evidence](gates/cpr-003-components.txt). |
| V17 | Source pass: matching/absent/changed/unknown inspection creates no files/lock/backup. Mounted lost-write failure survives unmount/remount and matching explicit revalidation sends zero additional writes. Baseline helper overwrite/inode regressions observed red, current green. |
| V18 | Source pass: registry retains the pre-send original preview key independently of display/tab lifetime. Mounted actual Application recovers the original key/ID, waits for its terminal sizing result, then exact captured-candidate revalidation sends zero second sizing POSTs or writes. Changed draft/base/authority or missing original result cannot restore readiness. CPR-004 mounted/registry artifacts below; real bridge remains V54. |
| V19 | Source pass: actual temporary helper preserves predecessor after rename; mounted lost install acknowledgement retains exact guard/cause and requires inspection, explicit confirm, acknowledgement. Zero reinstall/rollback/cleanup. Real interrupted Cockpit process remains V54. |
| V20 | Source pass: runner and guarded helper reject apparent successful stdout after failed process/postcheck. Mounted actual adapter preserves failed confirmation Envelope separately from boundary failure; neither grants success. Same focused artifacts as V09/V16. |
| V21 | Source pass: different preexisting candidate is preserved; exact matching reuse retains inode. Unsafe/changed/unknown ownership blocks repeat write/install/discard, and full reload cannot adopt a file by name. Real temporary filesystem and mounted cases pass. |
| V22 | Source pass: registry synchronously persists the exact key before the raw adapter starts; controlled before-first-notice failure retains it. Runner behavioral probe fails all four expectations against 65b12d9 and passes current code. [Core evidence](gates/cpr-004-registry.txt). |
| V23 | Source pass: pure inaccessible/mid-session quota/capacity cases and actual Firefox sessionStorage QuotaExceededError refuse submission; no fallback or fake cancellation. Strict allowlist stores no bodies/TOML/logs. Registered credential collisions in public hashes/UUID/instance/substring produced 11 red failures before suppression, then 11 green. Remaining all-read-surface audit belongs to V51/CPR-007. |
| V24 | Source pass: mounted actual Application Maintenance → Apply before-notice failure → Overview → Maintenance unmount/remount preserves original handles, blocks Apply, then explicit original lookup/wait sends zero further submissions. See [component artifact](gates/cpr-004-mounted.json). |
| V25 | Source pass: actual same-origin iframe location.reload restores handles into a fresh module registry without replay. Corrupt/oversized/unknown-field records fail closed; external storage changes are preserved. A well-shaped stored terminal summary is unverified until authenticated original observation confirms it; forged/mismatched summaries cannot silently unlock a submission, and missing history remains unresolved. Pure behavioral regressions observed red then green; mounted final evidence below. |
| V26 | Source pass: pure host/profile/endpoint/class/archive/unknown UUID drift refuses saved recovery; restart alone can retain matching authority. Mounted changed authority disables stale Apply and installed acknowledgement. Real CLI same-process scope mismatch refuses before POST or handle GET. |
| V27 | Source pass: actual dry-run → Apply confirmation/double-click → process failure with applied=null leaves Apply disabled, across tab remount; original lookup/wait only. Apply consumes preview before asynchronous work and freshly compares the original scope. |
| V28 | Source pass: mounted call-site matrix covers all keyed page submissions and strict fixed argv/key identity; synchronous validation, estimate and reads create no registry records. CPR-005 replaces the earlier full-manual service exception with keyed REST jobs; four additional CPR-008 mounted lifecycle cases preserve both original full-job identities through tabs and reload. |
| V29 | Source pass: authentic HFAPI013/015/018/019/020 preserve original handles and nonterminal state in registry/runner tests; no new key, cancellation or recovery. Missing terminal identities refuse apparent success. |
| V30 | Source pass: pure missing/unavailable lookup retains handles; actual separate CLI process over private UDS preserves HFAPI013 and performs zero POSTs. UI explicitly states missing history does not prove nonexecution. |
| V31 | Source pass: registry/runner cases retain exact terminal exit 0/10/20/30/40/50, partial/busy classifications and safe summaries; 202/missing receipt identity never grants success. Actual result bodies remain only in application memory, never restored Apply readiness. |
| V32 | Source pass: independent notice collection survives flood/abort/callback errors; mismatched key/ID fails closed without overwriting original identity or prior summary. Mounted explicit wait with one wrong ID and valid success stdout fails before the original-observer identity callback fix. Final current suite evidence below. |
| V33 | Source pass: fixed rootless transient argv and copied commands carry original scope, quoted handles and positional --. Real repository Bash and Python launcher hops formerly intercepted --help/-h handles after --: four behavioral red failures; 72 focused tests green after repair, including leading-dash/tilde exact forwarding. Exec is intercepted hermetically; no installed runtime claim. |
| V34 | `runner.test.ts` page closure, callback failure, late handles and abort tests pass without process-close/cancellation capability. D-Bus channel disposal does not stop application execution. |
| V35 | Source pass: mounted manual full sync submits one original keyed fixed client with no service start; detach preserves original identity and collects the result independently. Actual separate CLI/private UDS test asserts POST /syncs, exact body/key/receipt/terminal result, then original lookup/wait with zero second POST. [Boundary record](gates/cpr-005-boundaries.txt), [components](gates/cpr-005-components.txt). Permitted temporary/component fixtures are distinct from required real Cockpit/PAM V54. |
| V36 | Source pass: mounted verify --full preserves exact integrity exit40; actual CLI/Unix socket and framed private verifier exercise clean and deliberately damaged newly provisioned temporary publications, with Hub forbidden during verification. Original lookup/wait preserves terminal identity and emits no POST. Same boundary/component artifacts as V35; no installed or NAS workload claim. |
| V37 | Source pass: unknown/guarded actual full/selected/revision/maintenance controls disable, and direct job/config adapters refuse before target processes. Both direct bypass cases were observed red before central enforcement. Full Doctor needs both hub and archive permission; readonly Doctor still needs hub permission. Fresh adapter proof is independent of cached UI state. [Red/green](gates/cpr-005-components.txt), [host controls](gates/cpr-005-host-controls.txt). |
| V38 | Source pass: strict protected policy/index/selected-release/fixed-binding filesystem tests and bounded frontend parser reject unsafe/missing/duplicate/drifted facts. Actual mounted delayed allowed response cannot supersede newer denial; reconnect during pending inspection triggers one fresh proof and no effect. Immutable request capture and closed command grammar close reproduced callback/global-option bypasses. [Host proof](gates/cpr-005-host-profile.txt), component evidence as V37. Production profile not inspected. |
| V39 | Source pass: fixed-system adapter tests refuse masked/unavailable schedule changes before file/D-Bus effects; no force enable, target or verify-timer mutation. Calendar/delay injection was reproduced red, then rejected before rendering/effect. Acknowledged file change followed by Reload refusal stays uncertain across pending and failed tab remounts; only exact explicit read inspection/acknowledgement unlocks another deliberate change, with zero replay/reload/restart. Current rootless helper denies schedule/observer permission because their binding is unverified. [Host controls](gates/cpr-005-host-controls.txt), [components](gates/cpr-005-components.txt). |
| V40 | Source pass: mounted permitted fixture shows scheduled system observer state/journal separately from an active manual REST job. Exact StopUnit targets only hfcache-sync.service; journal text and observer stop cannot complete/cancel the manual operation or submit another job. Actual current rootless scheduling remains unsupported/denied; no new scheduler was introduced. [Components](gates/cpr-005-components.txt). |
| V41 | Source pass: new one-page runs list/show preserve exact server Envelopes and bounded seven-field read metadata; actual separate CLI/private UDS covers empty/default cap, multiple pages, exact detail and historical report fingerprint. Focused168 tests passed. Mounted70/70 includes50-ID page, Next replacement, first/empty, exact historical failed detail and immutable expected page identity. [CLI](gates/cpr-006-cli.txt), [components](gates/cpr-006-components.txt), [actual frontend gate](gates/cpr-006.txt). |
| V42 | Source pass: missing/corrupt/oversized report, wrong archive/run identity, absent schema, stale/repeated cursor and malformed metadata refuse without substitution or success-only fallback. Missing schema was observed red before explicit version checking; actual private UDS missing/corrupt/stale cases retain classified errors. Mounted refresh/session/navigation drops old evidence and shows exact failed reads separately from hostile success refusals. [CLI](gates/cpr-006-cli.txt), [components](gates/cpr-006-components.txt). |
| V43 | Source pass: three actual separate-process/private UDS lifecycles deny client archive/config opens and scans while REST reports remain readable. Production adapter retirement was observed as two static failures before removal, then2/2 pass; final static/journal/events/stream selection30/30 pass0skip. [Red](gates/cpr-006-archive-boundary-red.txt), [green](gates/cpr-006-archive-boundary-green.txt), [journal/static commands](gates/cpr-006-journal.txt). No direct plugin archive report path or old privileged report-file API remains. |
| V44 | Source pass: CLI rejects invalid IDs, paths, leading options, arbitrary route/method and job/local/candidate modes before credential/network access. Plugin accepts only fixed page50 vectors with one bounded opaque cursor and exact32hex show ID;10 command tests passed. Mounted unsafe-ID/cursor calls refuse before target invocation. [CLI](gates/cpr-006-cli.txt), [components](gates/cpr-006-components.txt). No new forwarding surface. |
| V45 | Source pass: fixed seven-day/newest201-entry query, owned5s+1s host deadline/client6s, raw256KiB, retained200lines/64KiB and8KiB line caps. Final11 journal cases cover chunked/oversized/secret prose,201st-line close, UTF8 cap, access/bridge/launcher/124 and partial deadline. Only closed event/level/exact run-ID projects; incomplete failed frames stay withheld. Mounted report remains visible through journal bridge failure, safe partial evidence, filtering and line truncation; a reproduced initial-effect race is fixed. No host process was run. [Journal](gates/cpr-006-journal.txt), [components](gates/cpr-006-components.txt), [frontend gate](gates/cpr-006.txt). |
| V46 | Source/component pass: exact version --server retains original negative code and refuses malformed secret-bearing success. Baseline case fails; current passes. [Components](gates/cpr-007-components.txt), final561unit/104mounted full gate below. |
| V47 | Source/component pass: original Estimate failure, strict metadata schema, unknown throughput/unreadable counts, refresh/session invalidation and one pending read. No workload or verification confidence inferred. [Owner/estimate](gates/cpr-007-owner.txt), [components](gates/cpr-007-components.txt). |
| V48 | Source pass across Version/Estimate/Status/Inventory/Doctor and prior REST reports: original failures, validated informational partials, valid empty, unreachable measurements and malformed success stay distinct. Actual CLI formatter regressions35RED thenGREEN;142focused CLI/API/socket cases pass. Complete inventories retain existing byte/page bounds without invented row limits. [CLI](gates/cpr-007-cli.txt), [components](gates/cpr-007-components.txt), prior report evidence retained. |
| V49 | Source pass: fresh host/session ownership before reads, old callback rejection, failed-refresh clearing, queued-action and opening-modal origins, and actual Configuration remount preserving a newer explicit inspection while clearing stale generations. Both current-store authority invalidation directions have4exact-effect regressions. Exact component baseline26semantic failures; final104mounted pass. [Owner](gates/cpr-007-owner.txt), [components](gates/cpr-007-components.txt). |
| V50 | Source pass: strict four-field advisory build provenance and mounted diagnostics separate browser source/dirty/input digest, protected selected source/index/image, and fresh authenticated endpoint/profile/class/archive/instance. Missing/malformed/mismatched/stale facts remain explicit, with no native fallback or writability claim. Build14tests, FIFO/ancestor RED/GREEN and independent100safe refusals/0private opens/0FDleak. [Evidence](gates/cpr-007-build-info.txt). |
| V51 | Source pass: earlier bounded failures/registry/profile/report/journal secret defenses retained. CLI human read/Doctor presentation applies existing registered-credential redaction; JSON terminals preserve safe original Envelopes before success-only formatting. Closed read schemas withhold unknown/nested fields and malformed diagnostic values. Build hashing never reads environment/private inputs or follows a symlinked ancestor. [CLI](gates/cpr-007-cli.txt), [components](gates/cpr-007-components.txt), [build](gates/cpr-007-build-info.txt). Real secret delivery remains V54. |
| V52 | Installed-wheel layer passes10actual CLI/private authenticated UDS cases: all90Python module paths/bytes equal source/wheel/installed, isolated installed console outside checkout, candidate validation/exact escaped413/auth/pin refusals, original keyed sizing and no-second-POST lookup/wait, full-job failed terminals, report pages/detail/corruption/request identity. Earlier source-only socket evidence retained. Wheel SHA256578fd699e5873ffdada5d1af4b3eddfe00772667ee1616badea31e0a1518392d. [Actual commands and artifact identities](gates/cpr-008-cli.txt). Not PAM proof. |
| V53 | Source/component completeness passes109actual mounted React/adapter/hook/runner cases; four added manual Sync/Verify cases cover genuine Application tab unmount and fresh-module reload, preserving one original keyed process with no replacement. Prior uncertain Apply, candidate stages, report and host/session freshness coverage retained. [Review/commands](gates/cpr-008-component-review.txt), [accepted109-case component result](gates/cpr-008-pipe-mounted.json). New exact41d framing regression fails before and passes after the repair; all guarded adapter wires preserve Unicode/trailing newlines using canonical NUL-free text. [Framing components](gates/cpr-008-framing-components.txt). Controlled external Cockpit ports are explicitly not real PAM; physical chain remains V54. |
| V54 | PASS scoped native layers: actual timer/MainPID, NUL-text disconnect and enforcing PID1 stdout-file denial reproduced and narrowly repaired. Native final receiver3/3 and original authenticated lookup/wait after disconnect pass on retained thirdfixture without replacement. Independent fifthfixture12/12 proves native PAM/admin/fixed-rootless/auth/profile/secret isolation, exact candidate434bytes/install/confirmation/backup/rootlock and separate real bridge interruption/reauth/read-onlyinspection preserving candidate-write/bridge/terminated and Validate-disabled. Exact final domain/rootlocks/masks/NFSro/Enforcing/0jobs and zeroAVCs; no replay/install/cleanup afteruncertainty. [Native](gates/cpr-008-pipe-browser.json), [physical](gates/cpr-008-pipe-physical.json), [identities/procedure](runtime-008.md), [accepted gate](gates/cpr-008-pipe.txt). Earlier unknownthirdcandidate/unconfirmedfourthinstallation preserved. No native running sizing/fullsync/fullverify bridge claim or original installed-cause claim; separate mounted/installed-UDS coverage is explicit. |
| V55 | PASS at controlled component/protected temporary-file layers: four mounted Diagnostics cases (new intentional-skew case plus existing malformed/dirty/stale/failure cases) show exact distinct browser source/input, selected source/index/image and explicitly refreshed authenticated profile/archive/API-instance. Unknown selected proof and HFAPI003 clear stale facts; no job/key or fallback.45focused identity/command tests and578docs/route/profile/install tests pass, including physical helper/index/client/binding drift refusal. [Mounted result](gates/cpr-009-mounted.json), [commands/limits](gates/cpr-009.txt). Retained native artifacts separately pin physical identities; this is not a four-way cross-deployed running-payload experiment. API metadata has no authoritative Git/image identity, and equal0.2.1 never proves parity; [reviewed handoff](operator-handoff.md). |
| V56 | Source gate wiring passes10isolated control tests, including removal immediately after final successful tool discovery: --require-cockpit refuses absent sources/pnpm/make, composes with --with-build and invokes the required frontend directly rather than accepting a skip. Default backend-only loud skip remains explicitly unaccepted. With safe help tests53passed. These controlled tool fixtures are not frontend acceptance; final strict full gate exits0 with actual570unit/109mounted and three wheel profiles. [Accepted gate](gates/cpr-008-pipe.txt). [RED/GREEN evidence](gates/cpr-008-gate-wiring.txt). |
| V57 | PASS:578focused docs/config/36semantic-mode/44HTTP-row parity, runs CLI/socket/help and protected release/runtime/profile tests; locked documentation alignment188human/19helpers. Report commands/help/Envelopes and fixed authenticated reads agree with human contracts. Existing fourteen-tool read-only MCP/old read interfaces and prior accepted gates remain; no install/cancel/schedule REST route or MCP write is added. [Actual command/evidence](gates/cpr-009.txt). Final extended gate evidence follows at V59. |
| V58 | Compatibility source/owned-fixture pass:300existing model/golden/operation/candidate/tag/catalog cases and63earlier actual guarded temporary-filesystem cases. Framing and confirmation repair expands this to68real shell/filesystem/FD/status cases, including full2796210-byte wire and complete-output-then-codec-failure refusal; [earlier67-case framing result](gates/cpr-008-framing-host.txt) and [accepted68-case pipe/confirmation result](gates/cpr-008-pipe.txt). Exact module bytes in installed wheel match source; hfcache Python package/durable/tag fixtures unchanged from41d818e. The separately pinned host helper has the recorded timer-facts repair. Real filesystem tests use fixture ownership and a controlled manager boundary, separate from real root:hfcache/SELinux V54. [Evidence](gates/cpr-008-cli.txt). |
| V59 | PASS: final `rtk proxy scripts/check.sh --with-build --require-cockpit` exit0:5299Python/52deselected in757.36s;3locked wheel profiles; actual lint/style/types/570unit0skip/110mounted/fresh production build;16build-marked/5335deselected in45.18s (2old-wheel compatibility,4smoke,10installed CLI/UDS). Separate final `make -C cockpit check` exit0 with570unit/110mounted. [Commands/log hashes/artifacts](gates/cpr-009.txt), [full-gate mounted result](gates/cpr-009-final-mounted.json), [installed wheel identity](gates/cpr-009-installed.json). |
| V60 | PASS scoped closeout: all9task records and plan completed, selector cleared with no historical backlog activated; all F01–F11/V01–V60 traced and independent evidence-link/identity review complete. [Handoff](operator-handoff.md) separates dirty source/disposable artifacts from later clean release/install/original-symptom/NAS acceptance and records5preserved guests/unknown attempts/locks/handles/backups. No production deployment/inspection/registry/merge/tag/init/live workload performed. Later user explicitly authorizes final branch pushes only after commit; actual remote outcomes are verified separately. |

## Required gate record

| Gate | Command / result / evidence |
| --- | --- |
| Package repository gate | CPR-009 final extended strict gate passes as V59; [final evidence](gates/cpr-009.txt). CPR-008 final `rtk proxy scripts/check.sh --require-cockpit` exit0:5299passed/52deselected in772.44s, three wheel profiles, actual frontend lint/style/types/570unit/109mounted/build. [Accepted evidence](gates/cpr-008-pipe.txt). Prior CPR-007 final `rtk proxy scripts/check.sh` exit0:5276passed/42deselected, three wheel profiles, actual frontend lint/style/types/561unit/104mounted/build. Earlier failed/transitional and accepted gates remain. [Evidence](gates/cpr-007.txt) |
| Explicit frontend gate | CPR-009 `rtk proxy make -C cockpit check` exit0:570unit/0skip,110mounted,lint/style/types/fresh production build. [Actual evidence](gates/cpr-009.txt), [bounded mounted result](gates/cpr-009-final-mounted.json). Earlier failed formatting and passing snapshots retained separately. |
| Extended final gate | PASS final `scripts/check.sh --with-build --require-cockpit`, exit0; actual frontend,3profiles,5299default+16build-marked tests; [evidence](gates/cpr-009.txt) |
| Component/lifecycle regressions | CPR-002: 12 mounted cases passed in actual Firefox; [bounded results](gates/cpr-002-mounted.json). No real PAM/API claims |
| Actual CLI / private Unix socket | CPR-008 installed-wheel10/10 pass, exact90module source/wheel/installed equality; candidate/job/report/auth/refusal/identity coverage plus prior source socket evidence. [Evidence](gates/cpr-008-cli.txt) |
| Actual disposable Cockpit / PAM / rootless chain | PASSED12/12actual fifthfixture plus separate third original recovery; exact code/artifact/profile/secret and original guard facts pinned. [Native](gates/cpr-008-pipe-browser.json), [physical](gates/cpr-008-pipe-physical.json), [procedure](runtime-008.md). No production claim |
| Documentation, schema and CLI parity | PASS578focused tests/45identity+command/4Diagnostics;188human documents/19helpers; current36semantic modes/44HTTP rows and fourteen read-only MCP tools retained. [Evidence](gates/cpr-009.txt) |
| Existing durable/operation compatibility | CPR-009 extended16 includes2actual old-wheel compatibility cases and4wheel smoke plus installed CLI10; accepted new wheel638a3274…cec1b matches all90runtime modules. Prior CPR-008 existing compatibility300/300 and guarded-filesystem63/63 pass; package/durable/tag fixture bytes unchanged. [Commands and qualifications](gates/cpr-008-cli.txt) |

## Separate acceptance decisions

| Milestone | Evidence / disposition |
| --- | --- |
| Source remediation and mandatory automated gates | Accepted CPR-001–009, including final strict extended+explicit frontend/parity/handoff; no mandatory source/disposable blocker |
| Actual disposable runtime chain | Accepted scoped V54 with qualified distinct fixtures/layers; original installed symptom remains unproven |
| Installed production artifact parity | Not inspected; separate authorization required |
| Original installed candidate symptom resolved | Not demonstrated |
| Existing NAS/workload holds cleared | Not requested; remain in force |
| Deployment, registry publication, merge/tag | Not requested; not performed |
| Final branch pushes | Later2026-10-20 user instruction explicitly authorizes Forgejo+GitHub after final green commit. Exact branch absent on both read-only preflights; actual pushes/ref equality are verified after commit and reported separately, not fabricated here |

## Operator handoff and rollback

[Reviewed operator handoff](operator-handoff.md) records exact accepted source/
bundle/helper/index/image/API identities, clean future release/build prerequisites,
separate installed-symptom verification and protected drain/rollback contracts.
Five local guests and all backups, original locks/keys/IDs/receipts/results and
unknown/unconfirmed execution remain preserved. No source rollback, browser exit
or observer stop proves actual jobs drained. Production/NAS acceptance is separate.

## Contract review

Final review: CP-01–14, INV-005/006 and agent INV-011 agree with current contracts
and actual ADR134–139 plus affected118–122/127/133 amendment links. CP-04 manual
service-start and CP-09 direct-report exceptions are explicitly replaced by
ADR135/136. ADR138/139 preserve canonical bounded text, original root lock, exact
bytes/predecessor and original CLI/collector statuses under enforcing hardening.
No new runtime dependency, durable/archive schema, API route, MCP capability,
launcher fallback or credential boundary is introduced. Existing archive gates,
workload holds, unit masks and no automatic replay/cancel/install/rollback/cleanup
remain. The final package adds documentation and controlled V55 coverage only,
so no new architectural decision or artificial invariant edit is needed. Human
README/changelog/Cockpit/install/troubleshooting/deployment/release guidance now
agrees; completed task/current/plan/progress consistency is verified at closeout.

## Activation and chronological execution history

The following dated/ordered notes retain earlier pending and failed states. They
are historical snapshots; the current V rows and separate acceptance table above
own the final disposition. Old artifact hashes and unknown attempts are preserved.


Baseline contract review: CP-01–14, INV-006, workflow INV-011 and decisions
118–122/127/133 reviewed. Decision 134 adds presentation/recovery requirements;
CP-04/09 current exceptions remain until their explicit replacement packages.
Existing API/client/config/security/container/deployment contracts retain their
authority. No durable format, dependency or production control was changed.
The imported bundle manifest retains original import hashes, not mutable task
completion hashes; its original source-review evidence is preserved.


Later user steering permits local-host development, necessary service outage and
backed-up/restored installation changes without NAS impact. Disposable fixture
provisioning is now being investigated on this host; V54 remains unpassed until
actual isolated bridge/launcher proof exists. Preserve pending operations, original
guards/lock inodes, masks, hardening and credentials. No host mutation yet.


First baseline full gate failed: 1 failed/5007 passed/42 deselected in 600.24s;
`test_predecessor_commits_and_plan_selector_preserve_the_execution_record`
incorrectly required the live selector inactive forever. Corrected to inspect the
actual CAT-016 commit selector; focused file 2 passed in 1.07s. Full retry pending.
Frontend was not reached in that failed run, so it is not frontend acceptance.


### Mounted baseline investigation

`rtk node docs/agents/plans/support/cockpit-rest-repair/baseline-browser.mjs`
exited 0 in Firefox 140.13.0esr, using actual Maintenance/QueryError/hooks/API
adapter/runner with only the Cockpit process boundary controlled. Bounded artifact:
[baseline-browser-evidence.json](baseline-browser-evidence.json).
Actual DOM clicks dry-run -> Apply -> confirmation produced exactly one synthetic
Apply; after its key/ID and `reconnected` failure, Apply was enabled again.
The mounted validation QueryError lost problem/stage and showed generic guidance.
Unmount/remount lost local handles and issued zero new calls. This is a real
component root lifecycle reproduction, not the Application tab acceptance test,
real API/PAM/launcher proof, or satisfaction of repaired V01/V24/V27 expectations.
The owned loopback server/browser exited; no application command, production
credential, host configuration, NAS or live archive was accessed. No sandbox was
weakened. The private temporary browser profile is retained as fixture evidence.


CPR-001 commit `b40b443`: full retry passed (5008 Python tests, 42 deselected,
593.55s; all three locked wheel installation profiles; actual Cockpit lint,
stylelint, typecheck, 170 tests with 0 failures/skips and production build).
[Gate summary](gates/cpr-001.txt). This records baseline coverage, not repaired
V01–V60 acceptance. Baseline source remains unchanged except the historical
selector regression test correction. Mounted reproduction and pure investigation
commands both exited 0; documentation alignment passed (183 documents/19 helpers).


CPR-002 mounted fail-before evidence:
`rtk node cockpit/test/browser.mjs dcc2c562b52304541d0cb85d20fc046072038e79`
exit 1, 3 passed/6 failed (lost bridge problem, stale read/unit evidence, closed
cached client, finite pending read recovery, privilege invalidation). Working tree
mounted harness: 9 passed/exit 0 before final schedule regression additions.
These are actual React roots/hooks/adapters with controlled Cockpit boundaries,
not real PAM/API/host commands. Existing old-generation/no-replay cases already
passed baseline and are retained. Full gate and final expanded counts pending.


Final CPR-002 additions: expanded mounted browser harness failed before schedule
freshness fix (10/12 passed, 2 failed) and passed all 12 afterward. Actual mounted
Maintenance modal portal privilege loss produced zero Apply calls. Runner negative
confirmation regression failed before fix, then exact HFAPI003 Envelope preserved;
apparent successful stdout with failed process still rejects. Focused runner/
failure/connection suite: 63 passed, exit 0.

Local runtime preparation reached boot/SSH, then paused; see
[runtime-setup](runtime-setup.md). Actual twelve signed prerequisite RPM additions,
zero upgrades/removals. Isolated guest has no default/NAS route or host directory
binds; no production configuration/secret/application change. V54 is still unpassed,
not blocked on user approval. Next prerequisites: guest-local application fixture,
synthetic REST sources, real bridge/launcher/browser exercises and exact identities.


CPR-002 commit `92f19b5`: `rtk proxy scripts/check.sh` exit 0: 5008 Python passed,
42 deselected in 656.48s; all three locked wheel profiles; actual Cockpit frozen
install, lint/style/types, 221 unit tests (0 failures/skips), 12 mounted Firefox
cases, production build. [Gate summary](gates/cpr-002.txt),
[bounded mounted results](gates/cpr-002-mounted.json). Explicit frontend gate also
exited 0. Documentation alignment: 183 documents/19 helpers. No application
runtime dependency, archive format, new REST route or credential boundary change.
Successful confirmation remains stricter; failed confirmation retains classified
negative evidence. CP-01–14, INV-006, decisions122/127/133/134 reviewed and current.

Production JS (decompressed index.js.gz) SHA256 at CPR-002: `b6995b709b0be8f63b97b81d908986bb85f94680c9d4783fd4b6af174f6628f0`.


CPR-003 focused evidence: pipeline101/101, guarded-filesystem62/62,
config/defaults36/36, mounted Firefox30/30; lint/types and documentation alignment
passed. In addition to baseline regression probes, the omitted-enabled sizing
regression failed before its fix (35/36 config tests passed), then all36 passed.
Malformed successful required previews and immutable-SHA mismatches fail closed.
No new application dependency, API route, durable archive format or credential
boundary. CP-11/INV-006 and decisions122/133/134 reviewed/amended; CP-04/09 remain
unchanged until their owning packages. Full package gate passed; complete results below.

The guest runtime setup preserves its genuine failed starts and exact next
unblock condition in runtime-003. Inherited diagnostic CWD, public directory modes,
standard SELinux labels and empty-mask placeholders were compared with existing
operator records, then clarified in living deployment/container contracts. These
fixture prerequisites do not establish the original installed trigger. Required
real-runtime acceptance remains unpassed; no mock result substitutes for it.


CPR-003 commit `65b12d9`: `scripts/check.sh` exit0,5008 Python passed/42 deselected
in787.38s, all three locked wheel profiles, actual frontend lint/style/types,
327 unit tests +30 mounted Firefox cases and production build. Separate
`make -C cockpit check` exit0. [Gate summary](gates/cpr-003.txt) and
[bounded component results](gates/cpr-003-mounted.json). Production JS SHA256:
`7e937a41a3e6b0f4533b583d807ae520ed0eda05dd3443aa23ea631c4168beaa`.
Runtime fixture setup is retained and qualified separately in runtime-003;
V52/V54 and final extended acceptance remain required, never inferred from these
source tests. Next package CPR-004; plan remains active.

CPR-004 commit `ca034e3` (2026-10-20): final `scripts/check.sh` exit0,5101 Python
passed/42 deselected in606.10s, all three locked wheel profiles; actual frontend
lint/style/types,412 unit/47 mounted Firefox cases and production build. Explicit
`make -C cockpit check` exit0. [Gate record](gates/cpr-004.txt),
[component red/green](gates/cpr-004-components.txt), [core/launcher/socket evidence](gates/cpr-004-registry.txt).
Production JS SHA256 `b2debb788704a6c7abbd1ebf95bdf03b58a14fc3d56bae5fd461bb631c5c311e`;
mounted bundle `800abfa840e0b86f74fe4d12aedbc1440f06b509ba84fa15024eb511fcaca2dd`.
Real CLI/private UDS authentication, narrow metadata and original key lookup are
partial V52 evidence, not the remaining candidate/job/report acceptance.

Original pre-send keys and late identities survive tab/reload/abort. Storage is
bounded and untrusted: restored terminal summaries cannot resolve uncertainty
without original authenticated observation. Actual quota, malformed storage,
uncertain Apply, scope drift, original sizing recovery, contradictory wait notices
and failed captured revalidation have meaningful mounted regressions. Failed
revalidation retains the original candidate-write/reconnected cause alongside the
new classified refusal; no automatic write/install/cleanup or second sizing.

The second full gate failed1/5098 with actual Unix ReadError. Repetition identified
empty EndOfMessage sendall -> BrokenPipe -> premature descriptor close -> EBADF,
not a timeout or an excuse to relax the fixture. Matching the locked backend's
empty-write no-op passes two deterministic real-UDS regressions, all20 transport
tests and200/200 unchanged original-case repetitions. The final gate includes this
repair and the corrected fixed launcher delimiter semantics. Earlier failed/red
evidence remains. No inference about the installed Cockpit trigger follows.

CP02/08/10/11, INV006 and ADR119/122/134 reviewed/amended, including index and human
CLI/client/Cockpit usage/troubleshooting docs. No dependency, archive schema, API
route or authority expansion. CP04 service and CP09 report exceptions remain for
CPR-005/006. [Runtime-004](runtime-004.md) now proves older-artifact real rootless
launcher/UDS/candidate validation while retaining original guard/masks/locks and
failed starts. Current-source real Cockpit/PAM/reconnect remains V54 unpassed,
with a second isolated immutable fixture recommended. Production/NAS untouched;
original installed symptom unresolved. Continue CPR-005; plan remains active.

CPR-005 commit `896003d` (2026-10-20): `rtk proxy scripts/check.sh` exit0,
5165 Python passed/42 deselected in829.52s; source/wheel and all three locked
installation profiles; actual Cockpit lint/style/types,436 unit tests,62 mounted
Firefox cases and production build. [Accepted gate](gates/cpr-005.txt),
[full-gate component artifact](gates/cpr-005-gate-mounted.json). Production JS
SHA256 `a767670965c618504a532951962050ab88f114ecaf1dd04af9815a519d8225a8`;
mounted bundle `e14553088ce64bb328142daf693dfa575f6a10ebf51537fbd521f95cc0941191`.

V35–V40 source/temporary fixture acceptance now covers manual full REST jobs,
fresh guarded/unknown/explicit permission gates, fixed-manager refusal and
scheduled-observer separation. Real CLI/UDS/private verifier parity3 cases and
protected temporary host-proof61 cases pass. Reproduced callback command mutation,
global-option/null-as-read forwarding, schedule injection, post-write Reload
refusal and pending/uncertain remount loss have retained red/green regressions.
Original classification survives; no new job, cancellation, reload/restart or
cleanup follows uncertainty. Exact read inspection/acknowledgement is explicit.

CP04/related boundaries, INV006 and ADR89/122/127/134 reviewed; actual ADR135,
index/register and human usage/operations/container/deployment docs amended.
No new dependency, archive format, REST route, scheduler, host binding or credential
authority. CP09 reports remain for CPR-006. Current rootless schedule/observer
proof remains denied, and no production/NAS/old-guest mutation occurred. Required
real current-source Cockpit/PAM V54 and original installed cause remain unproven;
plan stays active. Continue CPR-006.

CPR-006 commit `f0a35c2` (2026-10-20): fixed REST-only one-page report CLI/view and
retired direct archive reader, with independent optional bounded journal. V41–45
and report portions ofV48/V51 have actual subprocess/socket/component evidence.
Initial full gate1failed/5234passed/42deselected in747.33s exposed the frozen
independent route reference; additive36semantic-mode/44HTTP-row evidence preserves
all old SDK cases. Corrected full `rtk proxy scripts/check.sh` exit0:5241passed/
42deselected in683.23s, wheel/source build, three locked installation profiles and
actual Cockpit lint/style/types/495unit/71mounted/build. Explicit frontend check
also passed before the final detail latch; the accepted full gate covers it.
[Gate/hashes](gates/cpr-006.txt), [CLI](gates/cpr-006-cli.txt),
[components](gates/cpr-006-components.txt), [journal/static](gates/cpr-006-journal.txt).
Final productionJS SHA256c03be1d53dfbeff93af8efd9106b860ea9bfeda20ba40523debf42baea2c2e1c;
mounted bundleSHA256f4ba38d1d40da8fa277ef66dcf5c69646948ff19437c89739e035b0d223e76ff.
INV005/006, CP01/09 and other affected CPs reviewed; actual repository ADR136 and
ADR122/134/status/index plus CLI/API/client/schema/security/operator guides agree.
No new dependency/durable format/API route/MCP capability or production/guest/NAS
action. V54/current-source artifact and original installed symptom stay unproven;
continue CPR-007 with the plan active and prior restrictions/evidence retained.

CPR-007 commit `41d818e` (2026-10-20): V46–51 source acceptance with original coded
failures, strict honest read states and fresh host/session/authority readiness.
Exact reviewed component source26behavioral failures, repaired104mounted passes;
actual CLI/reader/writer/manual/report/socket focus142passes. Build FIFO/ancestor
privacy defects and passive invalidation races have retained actual RED/GREEN.
The first full gate failed mounted ownership, the next passed but preceded a
separately reproduced inspection race, and the FINAL full gate after all repairs
exited0:5276Python/42deselected in693.88s, three locked wheel profiles, frontend
lint/style/types/561unit/104mounted/build. [Gate and artifact identities](gates/cpr-007.txt).
ProductionJS SHA256db271a967029f87113380eeb97fee79a744b5762d923563a29a52a35641536c8;
mounted bundle7618cdd64e77899448f6139b318965658bdcfed72a10817d77681d5e3175748f.
Precommit browser metadata truthfully says parentf0a35c2, dirty=true, public
inputSHA256f08227a330ffd2a4df0d1f1d05ca143bf7497dd103bf69cb59553026cbead648;
no clean committed/deployed artifact claim. Actual ADR137/affected CPs/INV006,
older decisions and human contracts agree. No dependency/durable/API/MCP authority
or production/guest/NAS change. V54/current immutable artifact and the original
installed cause stay unproven. Continue CPR-008 with the plan active.

CPR-009 (2026-10-20, this commit): final source/disposable closeout accepted with
no mandatory blocked task. See V55/V57/V59/V60, final gate and reviewed operator
handoff. Actual source code and installed/native runtime module bytes agree;
metadata0.2.1 unchanged, no release artifact/version/tag is silently substituted.
Later user authorizes completed branch pushes to both remotes after commit only.
Production installed symptom/parity and NAS/workload holds remain separate.
