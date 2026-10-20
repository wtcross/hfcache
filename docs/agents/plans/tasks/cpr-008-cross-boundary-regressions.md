# CPR-008: Prove the browser, launcher, CLI, and API boundaries

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-007 — Render every failed read and expose accurate readiness](cpr-007-read-results-and-diagnostics.md) |
| Work package / commit | `CPR-008` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Complete the layered test harness, using existing project test conventions and
only recorded build/test dependencies. Layer one is pure error/Envelope/state
logic. Layer two mounts actual React surfaces with controllable documented Cockpit
promise/stream/close behavior. Layer three launches the actual installed CLI wheel
against a temporary Unix-socket API with deterministic synthetic backend fixtures.
Layer four proves the real Cockpit privilege bridge -> transient systemd -> fixed
rootless launcher -> CLI -> API chain in a provisioned disposable environment.

Exercise candidate write/validate/conditional sizing/install/confirm, including
connection transitions at each boundary, escaped large TOML and negative API
Envelopes. Use temporary configuration/state and synthetic credentials only.
Exercise tab unmount and reload during all representative jobs, especially
maintenance Apply, and assert exactly one original submission per deliberate action.
Verify preserved output bounds, credentials separation, exact identity and
no-cancellation behavior under split/truncated streams.

For the disposable real-runtime layer, bind no NAS/live archive and do not reuse
production credentials, unit names in the production manager, mounts or protected
release paths. Use a disposable host/containerized system environment with explicit
fixture ownership. Record supported Cockpit/systemd/Podman/toolchain versions and
physical release/image identities. This layer must not be described as production
acceptance. An unavailable environment is an explicit blocker, not a reason to
substitute a fake and label it PAM proof.

Add gate wiring so this plan's frontend checks cannot silently skip. Keep routine
offline tests deterministic; clearly mark/environment-gate real disposable runtime
checks separately. No live/nfs workloads are invoked in this task.

## Acceptance criteria

Every mandatory automated expectation through this package has concrete
test/evidence references; UI lifecycle, actual CLI/socket and disposable real-runtime
proof are distinguished. Follow the validation matrix ownership: V55/V57/V59
release/parity/final-gate checks and V60 closeout are completed in the dependent
final package, rather than prematurely claiming their acceptance here.
The synthetic failure matching the reported symptom has a passing correction test.
Any deployed-cause claim is limited to evidence actually obtained. Skipped or
unavailable required checks block the corresponding acceptance rather than count
as passes.

## Contracts, invariants and ADRs

Review docs/development.md, Cockpit test/acceptance contract, CP-02/03/08/11/13/14,
INV-006, fixed container boundaries and relevant existing integration tests.
Record any test-only dependency decision and update development instructions.
Never loosen a production contract for test convenience.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Original validation checklist (retained; actual results below):** Run the full matrix and existing suites under pinned Node/pnpm and locked Python
server+MCP profiles. Capture exact commands, counts, versions and fixture identities.
Run scripts/check.sh with actual Cockpit stage and make -C cockpit check. Preserve
old durable fixture compatibility. Run the disposable real Cockpit chain when
provisioned, otherwise retain its blocked evidence and do not mark this task complete.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Started2026-10-20 after clean CPR-007 `41d818e13c1f4860a286f24ba91bd0f384b09172`,
with its final accepted full gate (5276Python/561unit/104mounted). Sole active
package. Re-read environment, development/test contracts, matrix and actual
source before changes. Complete installed-wheel/private-UDS candidate/job/report
coverage, enforce explicit frontend-required gate mode, and provision a second
owned isolated local guest for a fresh immutable corrected artifact plus actual
Cockpit/PAM/systemd/rootless reconnect proof. Preserve the older guest's original
guard/masks/locks and evidence. No production/NAS inspection or workload, registry,
push/merge/tag, hardening bypass or uncertain-action replay is authorized. V54
remains unpassed until actual runtime evidence; absence is not a mocked pass.
Next action at activation: build/provision the current immutable fixture, audit layered coverage
and add strict frontend preflight; record exact identities/results/unblockers.

Actual runtime revalidation reproduced a conformance defect: real masked timers
omit MainPID, while the source host inspector required service properties for all
units. The repaired inspector requests/requires the exact five timer properties
for only the two allowed timers, retaining strict real PID facts for services and
guard. Captured guest output has RED/GREEN regressions;74host-profile cases pass.
ADR135/containers guidance is qualified without changing the public schema or
host permission/guard rules. A third independent guest is provisioned for a new
fixed-helper immutable stage; the second selected release/held guard remains
untouched. Fixture provenance is base41d plus exact helper patch/hash and dirty
snapshot, never a fabricated clean source claim. V54 stays unpassed until actual
fixed-helper readiness and real PAM/reconnect/original-operation evidence.

Current checkpoint: installed-wheel10/10, compatibility300/300, actual guarded
filesystem63/63 and mounted108/108 pass. Explicit frontend check passes561unit/
108mounted/lint/style/types/build. Strict full gate passed5299Python/52deselected in774.57s, three installation
profiles and actual frontend561unit/108mounted/lint/style/types/build. Final
manual-driver changes followed its lint stage, so another strict full gate after
driver freeze remains required. The third guest now
passes actual corrected host facts and authenticated fixed-launcher reads.
Native PAM login passed after a driver hidden-form readiness correction; public
plugin directory mode was separately corrected as a proven fixture setup omission.
Neither is an original installed-cause claim. Fresh original lookup/wait assertions
are being strengthened before actual full runtime acceptance. No operation is
resubmitted after a retained barrier. Next specific action: complete native browser
original-operation/candidate/privilege-interruption proof, independent bounded
launcher evidence and final strict gate, then complete and commit this package.
V55/V57/V59/V60 remain explicitly owned by the dependent final task per matrix.

Latest checkpoint: genuine privileged bridge authentication and one actual
read-only prune preview passed; independent guest receipt/result and bounded
journal prove the original key/ID/run and one fixed client launch. The driver
then failed a test-only greedy textContent extraction (paragraphs concatenate)
before lookup or candidate. Preserve the barrier/key/receipt and failed browser
profile. Continue only authenticated reads of that original and a candidate-only
UI phase, with zero further job submission. Do not widen or invent the domain
outcome: actual success/exit0/no errors or warnings is proven. Third strict full
gate passes5299Python/52deselected in696.15s, three profiles and frontend563unit/
108mounted/build, including retained-profile regressions. Corrected continuation
must freeze and pass another final strict gate before completion.

Current specific handoff: original-only native authenticated lookup/wait now
passes exact original result digest. Candidate phase refused before Validate on
an invalid test assumption: Form-to-Text serializes a proposed draft rather than
an installed-byte view. No candidate write happened. Preserve old barriers and
proofs; explicit known-prewrite continuation requires exact saved pre-click
refusal, current nonce-bound original base/absence/lock proof and new exclusive
attempt barrier. A Validate-sent marker is written before the click and prohibits
all later reentry. Separate interrupted write has its own exclusive marker.
Final driver7a65c22013a74fae96f27b0a76cc4048ba06d5018007ee7f1d77f5e49bd2ec5d
is frozen; current strict gate's applicable frontend stage will read that source.
Continue this same package until genuine candidate/interruption proof and final
gate pass, then commit. Do not claim the existing source gates prove V54.

Latest superseding handoff: the sole Validate click did not reach readiness in90s.
Its actual stage was not captured before browser closure. Independent read-only
checks find original installed bytes/inode/lock unchanged, no candidate/backup/
temporary/confirmation file, no held config flock, no candidate-validation client
and no AVC. None authorizes retry after uncertainty; all sent/attempt/submission
markers remain. No discard/bridge interruption holder started.
Independent native read-only ASCII/NUL probes then reproduced a real text-channel
transport defect: ASCII reaches the process; NUL input disconnects the actual
Cockpit bridge, including a fresh privileged session. Preserve this distinct
reproduction without inventing the missing earlier UI error or an installed cause.
Decision138 changes every guarded input to bounded canonical ASCII base64 lines,
with exact complete UTF-8 decode/canonical/size validation before filesystem or
lock effects. Malformed frames must leave no artifacts. Product regression,
real read-only framing GREEN and a fresh independent disposable candidate/bridge
fixture are next. Do not replay the third guest's unknown attempt or reuse its
operation identity as a new submission. V54 remains unpassed and package uncommitted.
The latest pre-framing strict gate exited0,5299Python/52deselected,3profiles and
563unit/108mounted; log SHAa6e4344d165df9aae9bb0e6cf590020a2139da2ce9404dc7f65062061db1a393.
It predates this framing repair and cannot supply final acceptance.

Final source/native checkpoint:67/67 guarded shell/filesystem regressions pass,
including both1MiB documents at exact2796210-byte wire, overflow tails and
complete-output producer/codec failure. Final guard SHA256
5b64be973d436ed983ea0eeac5415f7b2110a9a7c56947288fe2669c17251684.
Actual final receiver-prefix probe passes3/3 Unicode/trailing-LF pairs; a new
privileged bridge call after each remains connected. Independent fresh PAM and
same-scope lookup/wait after the native NUL disconnect recover the third guest's
original key/ID/run/result unchanged, with no candidate or job submission. Native
artifacts distinguish earlier prefix snapshots from the final receiver.
Fourth isolated guest now passes real fixed version/authority/installed validation,
with fresh UUID, credentials, original held guard/masks/NFSro and zero jobs. Its
sole fresh-mode candidate/install/confirmation/interruption run is next; complete
it and independent physical proof before acceptingV54. Manual driverdb5283c7
is frozen after4/4 runtime preservation/projection tests, lint/types and review.
Current strict gate is running the final framing source; earlier gates do not
substitute for it. Continue8 only, preserve all earlier unknown attempts.

Latest superseding native checkpoint: fourth guest's actual434-byte candidate
write and APIvalidation pass. One Install renames exactadc176… candidate to
installed and retains5b516… predecessor, rootlock75519490/domain27:2058/masks8/
NFSro/Enforcing unchanged,0jobs. Confirmation then fails before another CLIunit
starts; audit proves PID1init_t denied write to etc_t stdout file. Preserve the
unconfirmed installation, cause and barriers; no reinstall/rollback/cleanup or
bridge-fault holder started. NewADR139 uses anonymous stdout pipe plus bounded
local collector, independently captures statuses and preserves original launcher
exit while withholding all output on collector failure. Meaningful FIFOmanager
regression RED1fail; repaired68/68 guardedFS/FD/status tests pass51.346s with
lint/types. GuardSHA82e4d9cbd6d9de60c4495a2bfda5dadbd483be3f20f2d9f96b0e1bfe0b15fc78.
The passed5299Python/569unit/109mounted gate9e01c94f predates this pipe repair;
a new strictgate is running. Fifth independentfixture feasibility passes but
provisioning has not yet happened. Root owns nativeexecution. Complete fresh
fixed candidate/install/confirm/interruption/read-only proof before V54acceptance.

## Completion evidence

Completed2026-10-20, CPR-008 this commit. Final strict source gate exits0:
5299Python/52deselected in772.44s, three locked wheel profiles, actual frontend
lint/style/types/570unit0skip/109mounted/fresh production build. LogSHA
88ab84c12ae2b5fbf41525a1865c899f0fbb18a326323dd4ca8f481a9fd5202a.
[Accepted gate/native summary](../support/cockpit-rest-repair/gates/cpr-008-pipe.txt),
[mounted snapshot](../support/cockpit-rest-repair/gates/cpr-008-pipe-mounted.json),
[installed CLI10/10 and compatibility300/300](../support/cockpit-rest-repair/gates/cpr-008-cli.txt),
[actual disposable result12/12](../support/cockpit-rest-repair/gates/cpr-008-pipe-browser.json),
[exact physical/guard/audit proof](../support/cockpit-rest-repair/gates/cpr-008-pipe-physical.json).
Final guarded shell/filesystem/FD suite68/68; actual producer failures/bounds,
Unicode/trailingbytes, original exits, original lock/postchecks and real FIFO
regressions fail before and pass after. Strict frontend-required gate10isolated
controlcases refuses skipped stages. Installed-wheel/private UDS10actual cases
are explicitly executed, not inferred from default deselection. No new dependency.

Actual real runtime reproduced timerMainPID omission, native NUL text disconnect
and enforcing PID1 confirmation stdout-file denial. Narrow source fixes preserve
strict public schemas, original guard paths/locks, credentials and SELinux.
Fifth independent source fixture proves fixed happy configuration and real
privileged bridge interruption/re-auth/explicit inspection: original stage/bridge/
terminated stays visible, Validate remainsdisabled, no replay/install/cleanup after
uncertainty. Native original authenticated lookup/wait after disconnect is distinct
third-fixture evidence with unchanged original receipt/result. All earlier failed
attempts/unknown thirdcandidate/unconfirmed fourthinstall and five guests remain
preserved. Original installed cause/symptom is unproven; no production/NAS action.

Reviewed CP02/03/08/11/13/14 and INV006; allocated actual ADR138/139, amended
ADR88/92/122/134/135 and register/human contracts/troubleshooting. Fixed launcher,
bounded strict Envelopes, exact atomic configuration/backup, no-cancellation,
read-only MCP and immutable/durable compatibility remain. Final docs alignment/
selector/progress review is recorded with this package. Continue ONLY CPR-009 for
V55/V57/V59/V60 release/parity/final extended and explicit make/handoff; keep the
plan active until those pass. Do not activate historical backlog or deploy.
