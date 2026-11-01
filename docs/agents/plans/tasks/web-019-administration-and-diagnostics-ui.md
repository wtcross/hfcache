# WEB-019: Complete the operator administration workspace

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `f2a3fba268113a26c28c5eddcc20bb68a92a9e235887aeb4d9ab9c80127db6e5`,
original content SHA-256 `954f80cb76697bbf59712d88f457f7d0b1795ee563b60ca6da54161872fc797e`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P4 |
| Depends on | [WEB-018](web-018-schedule-observer-and-journal.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-019: complete operator administration and diagnostics` (this commit) |

## Read before implementation

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Integrate Administration panels for profile/permissions, archive health/free reserve, installed config, diagnostics, fixed sync schedule/observer, read-only verification timer and bounded journals. Surface archive/Hub/control/config/schedule/observer permission reasons independently from Basic authentication and daemon ready. Unknown/missing facts never look healthy or writable.

Map existing archive-health fields and warning codes to human guidance and relevant actions; distinguish snapshot status, actual verification, metadata coverage, API readiness and host restrictions. Show safe server/UI/release identities without secrets or false deployment claims. Schedule forms preview normalized expression/next event and explicit timezone, show expected-revision conflict, and explain reset/pause semantics. Display original operation recovery globally even on host panels.

## Unit and component validation

Component tests cover permission/status combinations, unknown states, all legacy warning/health mappings, schedule timezone/reset/conflict, verification timer read-only and journals' diagnostic labels.

## Integration validation

Call real host/diagnostic/config routes with multiple policy/profile bindings and unavailable helper. Assert no effects when viewing or refreshing read panels and no broad service control in requests.

## Functional validation

Follow operator administration guide in three browsers/Caddy on permitted native and guarded rootless guests: inspect, diagnose, edit permitted schedule, observe a denied action and read bounded diagnostic logs; verify no forbidden unit/timer changes.

## Human documentation deliverables

Complete administration.md and troubleshooting, update navigation, operator screenshots and parity documentation. Explain human consequences of version/profile mismatch and unsupported actions.

## Acceptance

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Activated2026-10-27 after WEB-018 committed as84221bf with a clean tree,
strict gate0 and all33 native/15 rootless scoped cases complete. Reuse the
existing guest, Caddy, images/engines and typed host APIs; preserve all original
failed collectors, SDK handles and prior archive evidence.

Compose the production Administration workspace from existing shared query,
operation/configuration/job owners. Add actual archive/readiness/version
observations, warning guidance, guarded schedule/observer controls, bounded
journals and original-operation recovery. Existing diagnostics remain explicitly
keyed jobs; no GET or page mount submits effects. Preserve server/systemd timezone
text without inventing a timezone API field. Review INV018/020/021/022 and
ADR145/150/154/156; existing authority, budgets and no-replay contracts apply.
Reconcile ADR156's stale design-status sentence with committed WEB018 evidence,
while keeping production/full-platform acceptance separate.

Source checkpoint: the composed workspace, original host-outcome recovery,
configuration/schedule navigation guards, diagnostics and warning guidance
(including current supplemental `HFWRN011`) are implemented. Focused combined
Administration tests passed98 before the final intent-fencing regressions and
warning addition; the final owned host slice passed23 unit/9 component tests and
the final read/warning/recovery slice passed49. Full application/node TypeScript,
scoped ESLint/Prettier and diff checks passed. Existing real Unix/helper/route/
runner/transport integration checks passed49 in7.43s. These checks do not stand
in for installed UI acceptance.

Source1 is frozen at `11bc4c9e3509361d14ca7c328577a578b4bc0da450c22b63d6f00436a7354add`
(1517 non-bookkeeping files/modes, parent84221bf). Strict gate1 failed on one
stale frontend mount test after8927 backend tests passed. The mount now makes
four legitimate GETs; its corrected test also uses a valid unknown-policy health
response. The subsequent complete component precheck passed4007 with no skips,
94.94% line/90% branch coverage. A final full strict gate is still required.
Evidence directory: `/var/tmp/web-019-validation-fnvch46d`. Matching native.48
image `0f1cdf839c540327745c4c77f263434bc5cd7deefa7cef26209748981ce0d27a`
and rootless.49 image
`08ad66a15e6c1f6e642cb0a3ae62dbe8aaab47dc0442dbfaaf6ec665e472f942`
pass pinned UBI10micro foundation and read-only/nonroot/network-none probes.
Neither contains Node/npm/pnpm/yarn/corepack/uv/pip/dnf/rpm. UI manifests are
`179dc758032a30ffe68b2914f631dfc454521006565ffdedadc082dcd4a0eccf` and
`8d47cd924f33b9060e46cd30c16bbbf9db3274271fbe8a5657b692e3650a42cb`.
Both original failed builds retain their ENOSPC logs/records. Seven identified,
unreferenced unnamed hfcache build-stage caches were removed after recording
inspection; named images, containers and prior evidence remain. Exact unchanged
inputs were resumed sequentially, not reported as first-attempt success.

Installed acceptance remains pending. Reuse existing Caddy/managers/engines;
the new Stop form needs one actual original-observer/backend-continuation case,
without repeating the already accepted loss/revocation matrix. Rootless keeps
one genuine diagnostics403 and its uncertain original key, which blocks another
job; no extra context or registry clearing bypasses that behavior.

The original six native attempts remain failed, without promoted case counts:
their collectors assumed unchanged free capacity across separate reads, an
entirely empty startup store, authenticated Hub identity with token mode disabled,
nonempty verification history, and no unrelated background reads. The final
attempt reached a real accepted diagnostic that became interrupted without a
recorded result. Static inspection found the disposable counter's host path
outside the API writable mount; the corrected fixture uses its canonical virtual
path. This is a fixture correction, not a relaxation of application hardening.
The original interrupted receipt/key and all earlier evidence remain untouched;
it must never be replayed or cleared to unblock tests.

A fresh native B namespace and .50 artifact isolate subsequent acceptance from
that unknown receipt. Source2 is
`be79ca2dfe4e983732d3b6dfee6ff0e7626a2a72a72cd7570abf122072e5ef72`;
its four changes from source1 are documentation and the mount test. Production
Python, web source and packaging bytes are identical. Fresh B stage and all six
preparation phases passed with no application role started. The shared .50
API/UI image is
`239f91a07cc9b3fff58f35dfe0129c8d38fc8b1419e239206dc299268f0cc538`,
UI manifest
`77ea61cf5b8f9c31b054ab72f2e8c3544b077f42fdd10400c0f70dd5612a3cbb`.
Its pinned UBI10micro/nonroot/read-only/no-Node checks pass. Rootless .49 is
built but not staged or accepted. Both installed browser profiles and final
strict acceptance remain open; these preparation results do not complete019.

Fresh B Chromium has passed all nine actual Administration cases, including both
diagnostic modes, schedule changes, exact observer stop/backend continuation and
mobile dirty navigation. Firefox/WebKit and guarded rootless remain pending.
The human guide now includes unchanged actual native desktop/mobile captures.
Final source3 is
`107e45b48e0ea2d4da43b5ce850ded90b394ed2fd233818e4b6b826638352dbd`
(1519 files/modes); its differences from source2 are only that guide and two PNGs.
Production source/packaging/script inventories are byte-identical. Strict gate2
passed0 in1994.337s on this frozen source with no changed files. Its log/result
are under `gate2/` in the evidence directory.

Fresh B's original three-engine cohort remains failed/cleanup_unknown. Chromium
and Firefox each passed all9 cases; WebKit passed7 before its stop case found
the original SDK job had exhausted the disposable fixture's60-second archive-lock
wait (`HFMNT010`, exit20). The exact host stop itself was confirmed, and the
original stop record shows35 process identities gone,5 empty cgroups and5 refused
endpoints. The required backend-continuation assertion did not pass; never call
this original27-case acceptance. Preserve its raw result
`native-b-functional1-original-result.json` SHA256
`30fce8babe4a1682c1d56e2c94714aae7dec908a9b745f000bb76d4e47e2eb90`.
Read-only reconciliation passed: all35 pairs gone,5 cgroups empty/5 endpoints
refused, baseline5 exact,13970 older-state rows unchanged, all24 API receipts and
their results terminal,15 host outcomes confirmed and all3 original SDK handles
retained. Its separate proof is `native-b1-readonly-reconciliation.json`, SHA256
`8ce4e5a33fd8426cdf4c4f2d0184c7b419013b2c5819c0d86284ea7515365b83`.
It preserves the original failure and explicitly identifies the historical
unsaved parent-metadata limit. The fixture correction passed0 in12.491s: retain
the exact old config inode/bytes, write a fresh canonical config changing only
`sync.lock_wait_seconds`60→3600 (the shipped default); preserve verification wait,
archive, authority, stores and original SDK evidence. No roles started.
All9 targeted fresh-key WebKit UI cases passed in the original464.297s run.
Its wrapper remains false/cleanup_unknown: final joins incorrectly expected no
new transaction journal. Actual sync creates its run journal before checking Hub
identity; the one new failed `HFHUB003` journal joins the original SDK run and
fingerprint, with no repository/SHA/publication. The original result is
`native-b-webkit-functional1-original-result.json`, SHA256
`1094ac782243793e270408e00e88bf6e8ed77154c61d567d1ceaf3cc760b0deb`.
Separate read-only qualification passed0 in7.923s, rechecking all8 canonical
receipt/HMAC/host/SDK/backup joins,91 saved prior objects,49 prior API files,
13970 older-state rows, baseline5,26 gone identities,5 empty cgroups/5 refused
endpoints and the exact one legitimate failed-sync journal. Original result and
report bytes/failed flags remain unchanged. Qualification:
`native-b-webkit1-readonly-qualification.json`, SHA256
`3b0000472866c677400a07cef923c286cf45d1d1d766637aba671a4c7a31fd3a`.
No browser work, original job or POST was replayed for that qualification.
The accepted native engine/case union explicitly joins original Chromium9/
Firefox9 with these9 WebKit cases and their separate closure/joins. Neither
original collector becomes a27-case pass. No application source/image rebuild
or new engine was needed. Guarded rootless subsequently passed all15 cases with
normal closure, as recorded below.

## Completion evidence

2026-10-27, WEB-019, this commit; dependency84221bf. Final source3
`107e45b48e0ea2d4da43b5ce850ded90b394ed2fd233818e4b6b826638352dbd`
has1519 unchanged non-bookkeeping files/modes. Exact final-file reconciliation
and all evidence are summarized in
`/var/tmp/web-019-validation-fnvch46d/source3-functional-all-summary.json`, SHA256
`3ebb9e272cabca97780740d06a9fa8da0bcc0063baa879076667b7e095d2488d`.

`historical gate invocation (original command SHA-256 `b9d97947112e6e5c5005002b465c3dd68f8bd158ca8c41cb5966f57422999103`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` passes0 in1994.337s:
8927 backend tests/52 unrelated opt-in deselections,3690 required web unit tests,
4007 combined frontend tests,581 historical frontend unit/110 mounted checks, all locked
wheel/build/browser/API-read checks,217 human documents/27 helpers and no required
skips. Line/branch coverage is94.94%/90%; gzip JavaScript252464 bytes. Gate log
and unchanged-source result are under `gate2/`. The earlier failed gate remains
retained. Tests include `host-controls-state.unit.test.ts`,
`HostControls.component.test.tsx`, `HostActionRecovery.component.test.tsx`,
`AdministrationReadView.component.test.tsx`,
`AdministrationDiagnostics.component.test.tsx` and
`administration-navigation.component.test.tsx`. Actual backend nodes include
`test_host_action_finishes_while_original_domain_work_still_holds_archive_flock`,
`test_actual_pidfd_stops_only_original_even_when_manager_replaces_invocation` and
`test_lost_helper_reply_keeps_original_interrupted_and_gets_confirmed_without_replay`.
OPS-10 now maps actual source nodes and executions instead of fictional paths.

Native acceptance comprises27 distinct engine/case pairs: Chromium9/Firefox9
from original B1 and targeted WebKit9, through built .50 SPA/shared Caddy22443/
installed API/helper/system manager. Original wrapper failures and both separate
qualifications above remain unchanged. The actual read-only case-union command
`rtk proxy python3 .scratch/web-019-native-case-union.py --execute --targeted-result
/var/tmp/web-019-validation-fnvch46d/native-b-webkit-functional1-original-result.json`
passes0; `native-b-case-union.json` SHA256
`dd66516957cf272a1a0a5c8fb474adf6d9f5dd5855fb729e6b76f4aba666b8bb`
pins both RESULT/REPORT pairs and qualifications. It records27 accepted pairs,
never a fabricated27-case original RESULT. Browser/collector deadlines stayed
unchanged when the fixture restored the shipped sync-lock wait.

`rtk proxy python3 .scratch/web-019-execute-rootless-v3-functional.py` passes0
in254.036s: all15 guarded-rootless cases through .49 built SPA/existing
Caddy8443/installed API/helper/worker. Original result
`rootless-v3-functional1-original-result.json`, SHA256
`8a81937f29e9d422a665337dd8cb6ee3c6657dec58e3e27569571f83061a481a`,
is passed/cleanup-known. Each browser inspects actual independent facts, sees
unsupported host actions disabled, reads bounded journals, retains one genuinely
refused diagnostic's original key while blocking a second submission, and treats
missing original history as unknown. Three keyed POSTs admit0 operations; no
registry clearing or profile bypass. All53 final tracked PID/start identities
are gone,4 cgroups empty/4 endpoints refused, exact created secret IDs retired,
verification timer inactive/unenabled, archive full metadata/bytes and both
stores/configuration/key/SDK/older evidence unchanged. Reuse existing guest,
engines, Caddy and enforcing policy; no new engine or frontend server.

Across accepted native/rootless cases:506 trusted requests,84 clear CSP
checkpoints, zero required skips. Runtime equivalence compares119 installed
native Python modules,119 native source modules and69 browser source files
against rootless source. Final S3 differs from native S2 only in the human guide
and two actual PNGs; S2 differs from rootless S1 only in three documentation files
and one unshipped mount assertion. Shared images pass pinned UBI10micro,
nonroot/read-only/network-none and no-runtime-Node/package-manager checks.

Human Administration/troubleshooting/navigation and actual desktop/mobile
screenshots accompany the feature. Living server/invariant/parity contracts and
ADR145/156 are amended; INV018/020/021/022 and related authority, budget and
no-replay decisions are reviewed. No new endpoint, runtime dependency, durable
format or privilege is introduced. Original host certainty stays independent of
API/domain completion. Configuration, exact publications, captured README,
REST bearer and read-only MCP authority are preserved.
