# Acceptance evidence

**State: baseline revalidated; implementation active.** Cases below remain
unpassed until their actual evidence is recorded. Source investigation is not
installed or disposable runtime acceptance.

## Source and environment identity

| Item | Actual evidence |
| --- | --- |
| Implementation branch / commit | `fix/cockpit-rest-api-alignment`; reviewed HEAD `dcc2c562b52304541d0cb85d20fc046072038e79` |
| Browser build checksum / source | Baseline production JS (decompressed index.js.gz) SHA256 `b414e92f01a316ffec9a45528fa676899ee842b0c44526599e30be90d15026f0`; source dcc2c562 |
| Application / CLI source | Same reviewed baseline; no source drift at activation |
| Physical launcher and rendered profile identity | Production not inspected. Isolated guest exact installer/bindings and failed-start evidence in [runtime-003](runtime-003.md); authenticated launcher acceptance still pending |
| Rootless image digest | Guest untagged immutable application `sha256:21cd4a2027cde144133d302d5abb803ddb1670b56a47b90c127e981be402258c`; exact wheel/closure and Caddy identities in runtime-003. V54 not passed |
| Cockpit / systemd / Podman versions | Disposable guest Cockpit368/systemd257-34/Podman6.1.0; host parity limits in runtime-setup. Source pin 47108e2f8ecac3cd71fb3372193dd0f9c0fba7b3 |
| Node / pnpm / Python / uv versions | v24.18.1 / 11.18.0 / 3.14.6 / 0.11.32 |
| Fixture location and no-live-archive proof | Repository-only Node fixture uses injected process/ports and synthetic strings; no host/archive commands |
| Original reported failure stage/problem | Unverified |

## Work packages

Each task owns its status/evidence; link it here without duplicating mutable status.
For each completed package record its real commit and test/gate artifact reference.
An uncommitted result says `<CPR-ID>, this commit`, never a made-up hash.

## Validation evidence

For V01–V60, record the case ID, test name or runtime procedure, command,
fixture/source identity, observed outcome, pass/fail/blocker and evidence location.
Group cases only when the cited test actually covers every named expectation.

Baseline command: `rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts`, exit 0.
[Observed source defects and environment inventory](baseline-evidence.md).
V01/V11/V24/V27 baseline defects observed; repaired expectations remain unpassed.

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
| V18 | Partial: preview receipt callback/retained bounded key/ID and validation-before-preview evidence pass. Uncertain preview blocks further sizing/discard; scoped durable registry and authenticated lookup/wait remain CPR-004. |
| V19 | Source pass: actual temporary helper preserves predecessor after rename; mounted lost install acknowledgement retains exact guard/cause and requires inspection, explicit confirm, acknowledgement. Zero reinstall/rollback/cleanup. Real interrupted Cockpit process remains V54. |
| V20 | Source pass: runner and guarded helper reject apparent successful stdout after failed process/postcheck. Mounted actual adapter preserves failed confirmation Envelope separately from boundary failure; neither grants success. Same focused artifacts as V09/V16. |
| V21 | Source pass: different preexisting candidate is preserved; exact matching reuse retains inode. Unsafe/changed/unknown ownership blocks repeat write/install/discard, and full reload cannot adopt a file by name. Real temporary filesystem and mounted cases pass. |
| V22 | Not executed; owning repair and regression pending. |
| V23 | Not executed; owning repair and regression pending. |
| V24 | Not executed; owning repair and regression pending. |
| V25 | Not executed; owning repair and regression pending. |
| V26 | Not executed; owning repair and regression pending. |
| V27 | Not executed; owning repair and regression pending. |
| V28 | Not executed; owning repair and regression pending. |
| V29 | Not executed; owning repair and regression pending. |
| V30 | Not executed; owning repair and regression pending. |
| V31 | Not executed; owning repair and regression pending. |
| V32 | Not executed; owning repair and regression pending. |
| V33 | Not executed; owning repair and regression pending. |
| V34 | `runner.test.ts` page closure, callback failure, late handles and abort tests pass without process-close/cancellation capability. D-Bus channel disposal does not stop application execution. |
| V35 | Not executed; owning repair and regression pending. |
| V36 | Not executed; owning repair and regression pending. |
| V37 | Not executed; owning repair and regression pending. |
| V38 | Not executed; owning repair and regression pending. |
| V39 | Not executed; owning repair and regression pending. |
| V40 | Not executed; owning repair and regression pending. |
| V41 | Not executed; owning repair and regression pending. |
| V42 | Not executed; owning repair and regression pending. |
| V43 | Not executed; owning repair and regression pending. |
| V44 | Not executed; owning repair and regression pending. |
| V45 | Not executed; owning repair and regression pending. |
| V46 | Not executed; owning repair and regression pending. |
| V47 | Not executed; owning repair and regression pending. |
| V48 | Not executed; owning repair and regression pending. |
| V49 | Shared read/unit hooks now remove stale healthy evidence and reject old generations; mounted regressions pass. Per-surface full read rendering audit remains CPR-007. |
| V50 | Not executed; owning repair and regression pending. |
| V51 | Failure/runner and mounted QueryError synthetic secret tests pass; only safe validated problem/status/signal/handle fields retained. Registry/storage and all read surfaces remain CPR-004/007 scope. |
| V52 | Not executed; owning repair and regression pending. |
| V53 | Not executed; owning repair and regression pending. |
| V54 | UNPASSED: guest provisioned with isolated NFS-ro, original held lock, exact images/bindings and synthetic credentials. Actual OCI start refused before payload startup on an empty credential placeholder. [Exact state/unblock condition](runtime-003.md#current-handoff). No API/socket/PAM pass; original installed symptom remains unproven. |
| V55 | Not executed; owning repair and regression pending. |
| V56 | Not executed; owning repair and regression pending. |
| V57 | Not executed; owning repair and regression pending. |
| V58 | Not executed; owning repair and regression pending. |
| V59 | Not executed; owning repair and regression pending. |
| V60 | Not executed; owning repair and regression pending. |

## Required gate record

| Gate | Command / result / evidence |
| --- | --- |
| Package repository gate | CPR-001: `rtk proxy scripts/check.sh` exit 0; 5008 passed/42 deselected, three wheel profiles, actual frontend lint/types/170 tests/build. [Evidence](gates/cpr-001.txt) |
| Explicit frontend gate | CPR-002 `rtk make -C cockpit check` exit 0; current full gate confirms 221 unit + 12 mounted cases, lint/style/types/build |
| Extended final gate | Pending — scripts/check.sh --with-build |
| Component/lifecycle regressions | CPR-002: 12 mounted cases passed in actual Firefox; [bounded results](gates/cpr-002-mounted.json). No real PAM/API claims |
| Actual CLI / private Unix socket | Pending |
| Actual disposable Cockpit / PAM / rootless chain | Pending; provisioned isolated environment required |
| Documentation, schema and CLI parity | Pending |
| Existing durable/operation compatibility | Pending |

## Separate acceptance decisions

| Milestone | Evidence / disposition |
| --- | --- |
| Source remediation and mandatory automated gates | Not accepted |
| Actual disposable runtime chain | Not accepted |
| Installed production artifact parity | Not inspected; separate authorization required |
| Original installed candidate symptom resolved | Not demonstrated |
| Existing NAS/workload holds cleared | Not requested; remain in force |
| Deployment, registry publication, push/merge/tag | Not requested; not performed |

## Operator handoff and rollback

Record the remaining installed checks and the exact safe prerequisites before
any proposed deployment or original-flow test. Preserve source/bundle/image/profile
identities, backups, original keys/IDs, old receipts/results and unknown execution.
No rollback, source change or observer stop proves actual jobs drained. Link the
existing executor-drain and deployment procedures rather than inventing a shortcut.

## Contract review

List amended or unaffected invariant sections and ADRs, with real decision numbers,
status/amendment links, human docs changed and progress/current consistency checks.
Keep CP-04/09 changes explicit and all surviving configuration, credential,
read-only guard and no-cancellation boundaries intact.


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


CPR-003, this commit: `scripts/check.sh` exit0,5008 Python passed/42 deselected
in787.38s, all three locked wheel profiles, actual frontend lint/style/types,
327 unit tests +30 mounted Firefox cases and production build. Separate
`make -C cockpit check` exit0. [Gate summary](gates/cpr-003.txt) and
[bounded component results](gates/cpr-003-mounted.json). Production JS SHA256:
`7e937a41a3e6b0f4533b583d807ae520ed0eda05dd3443aa23ea631c4168beaa`.
Runtime fixture setup is retained and qualified separately in runtime-003;
V52/V54 and final extended acceptance remain required, never inferred from these
source tests. Next package CPR-004; plan remains active.
