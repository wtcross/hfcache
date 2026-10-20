# Regression and acceptance matrix

**All cases below are planned. None was executed by this source review.** Task
completion must link actual automated tests or explicit runtime evidence, commands
and results in acceptance-record.md. “Not available” and “skipped” are not passes.

The user-reported `reconnected` symptom has an unverified installed trigger. V01,
V08, V17–V20, V52–V54 deliberately test its propagation and lifecycle boundaries
without assuming which stage caused that deployed failure.

| Case | Area | Owning package | Input / transition | Required observable result |
| --- | --- | --- | --- | --- |
| V01 | Bridge and process failures | CPR-002 | Error("reconnected") with no Envelope at each known stage | Preserve problem/stage and show contextual recovery; no invented daemon diagnosis or automatic repeat. |
| V02 | Bridge and process failures | CPR-002 | Plain rejection object, unknown problem, missing message | Safe normalized error with bounded fields; no undefined toast, unsafe interpolation or fabricated exit. |
| V03 | Bridge and process failures | CPR-002 | Missing launcher, failed systemd/Podman start, exit signal | Distinguish launcher/process/bridge facts from API and domain failures; keep safe diagnostics. |
| V04 | Bridge and process failures | CPR-002 | Nonzero process exit with valid failed terminal Envelope | Render exact command/errors/exit/identity; do not replace with generic spawn failure. |
| V05 | Bridge and process failures | CPR-002 | Split Unicode, oversized line/terminal, late notices and callback exceptions | Existing bounds, independent handles and strict terminal authority survive; no server cancellation. |
| V06 | Connection lifecycle | CPR-002 | Cached D-Bus closes then reads resume | Dispose old listeners and recreate a valid client; read retries finite; no unit mutation replay. |
| V07 | Connection lifecycle | CPR-002 | Poll failure, delayed old result, overlapping refreshes | Unavailable/stale state is visible; old generations cannot re-enable controls. |
| V08 | Connection lifecycle | CPR-002 | Administrative privilege/session changes during a pipeline | Dependent actions disabled; preserved uncertain state; reconnect never repeats the whole pipeline. |
| V09 | Candidate pipeline | CPR-003 | Valid compatible candidate requiring no sizing | Validation evidence retained, exact content/base checked and install proposal created only from strict valid evidence. |
| V10 | Candidate pipeline | CPR-003 | Invalid TOML/schema/field candidate assessment | Negative assessment and original HFCFG/location errors visible; no plan/install. |
| V11 | Candidate pipeline | CPR-003 | HFAPI003/017/018/019 or other valid failed Envelope with data={}  | Original API/client refusal visible, not mislabeled assessment-schema incompatibility; no readiness. |
| V12 | Candidate pipeline | CPR-003 | Reader credential cannot validate candidate; auth/capability refusal | Writer requirement retained; no local validation/Hub-credential/anonymous fallback. |
| V13 | Candidate pipeline | CPR-003 | Authority incompatible or unknown; installed policy invalid | Syntax validity remains distinct; preview/install blocked with manual authority guidance. |
| V14 | Candidate pipeline | CPR-003 | Tag-only different content with same operational fingerprint | Exact bytes before/after confirmation still required; fingerprint alone cannot confirm installation. |
| V15 | Candidate pipeline | CPR-003 | Empty, invalid Unicode/NUL, >1 MiB or JSON-escaped server-413 candidate | Bounds/refusals remain visible; no silent truncation, echo or successful proposal. |
| V16 | Candidate pipeline | CPR-003 | Concurrent editor changes candidate/base; unsafe symlink/link/mode | Existing root-lock/exact-content/safe-file checks refuse; no relaxed permissions or lock replacement. |
| V17 | Candidate pipeline | CPR-003 | Write completes but acknowledgement is lost | Guarded read-only reconciliation distinguishes expected/absent/changed/unknown; no blind overwrite or cleanup. |
| V18 | Candidate pipeline | CPR-004 | Sizing accepted or acknowledgement lost, then tab/reconnect/timeout | Original key/ID retained and lookup/wait available; old sizing result cannot authorize edited content. |
| V19 | Candidate pipeline | CPR-003 | Install rename succeeds but acknowledgement is lost | Unconfirmed state and predecessor retained; exact installed-content reconciliation; no automatic reinstall/rollback. |
| V20 | Candidate pipeline | CPR-003 | Confirmation stdout looks successful but process/postcheck fails | No success; retain stage/cause; exact content and successful postcheck requirements preserved. |
| V21 | Candidate pipeline | CPR-003 | Failure/discard after ownership or base is no longer provable | Preserve unknown candidate/backup; only explicit exact-guarded cleanup is possible. |
| V22 | Operation registry | CPR-004 | Channel lost before first CLI key notice | Original key already persisted before spawn/send; recover without generating another key. |
| V23 | Operation registry | CPR-004 | Storage full/unavailable, session ended, or sensitive sentinel in inputs/logs | Missing promised session recovery is explicit; session end never implies job cancellation; no token/TOML/raw-log persistence or disclosure. |
| V24 | Operation registry | CPR-004 | Real tab unmountOnExit while job runs | Registry survives outside tab; recovered UI observes original job and issues zero new POSTs. |
| V25 | Operation registry | CPR-004 | Full reload; corrupted/oversized/unknown-schema stored records | Valid handles restore safely; unsafe records cannot become commands or silently enable new submission. |
| V26 | Operation registry | CPR-004 | Host/endpoint/profile/credential-class/archive scope changes | No automatic lookup/wait or replay against the new authority; original unresolved record retained. |
| V27 | Operation registry | CPR-004 | Successful maintenance dry run, Apply spawn failure with retained key, busy cleared | Apply remains blocked by error/registry uncertainty even with applied=null and old successful dry run. |
| V28 | Operation registry | CPR-004 | All keyed non-streaming actions: plans, doctor, dry runs and applies | Every call captures key before send and ID on acceptance; synchronous reads/validation do not invent jobs. |
| V29 | Operation registry | CPR-004 | Observation timeout / HFAPI013/015/019/020 | Exact original handles and uncertainty survive; no automatic recovery/cancel or additional POST. |
| V30 | Operation registry | CPR-004 | Lookup/history expired or absent after uncertain transmission | Missing history is not proof of nonexecution; old record preserved and operator decision explicit. |
| V31 | Operation registry | CPR-004 | Terminal domain exits 0/10/20/30/40/50, busy and partial outcomes | Exact classifications/partial data preserved; 202 or stopped observer never becomes terminal success. |
| V32 | Operation registry | CPR-004 | Mismatched emitted key/ID, progress flood and event gap | Fail closed on identity inconsistency; bounds do not evict independently retained handles. |
| V33 | Operation registry | CPR-004 | Lookup/wait UI and copied keys beginning with - or ~ | Same fixed launcher/profile/identity; safe quoted data and --; no arbitrary shell/URL/credential input. |
| V34 | Operation registry | CPR-002 | Page close, abort, stop-observing or display callback failure | No process-close cancellation shortcut, actual worker/API stop, lock deletion or implied safe recovery. |
| V35 | Operations and host controls | CPR-005 | Manual full sync in explicit permitted disposable profile | Existing CLI sync/POST /syncs with one key and original receipt; no legacy service-start dependency. |
| V36 | Operations and host controls | CPR-005 | Manual full verify in explicit permitted disposable profile | Existing verify --full / mode=full job; private offline executor and exact terminal result preserved. |
| V37 | Operations and host controls | CPR-005 | Selected guarded read-only profile for every archive-effecting control | Prohibited actions disabled with reason at adapter and UI; no guard/mask changes or alternate submission bypass. |
| V38 | Operations and host controls | CPR-005 | Unknown/mixed/drifted profile or missing guard facts | Unavailability, not inferred permission; browser cannot select an unrestricted profile. |
| V39 | Operations and host controls | CPR-005 | Schedule edits with masked/unknown units; malicious/invalid calendar | Refuse before drop-in writes where unavailable; validated fixed system manager only, no verify-timer enable or target action. |
| V40 | Operations and host controls | CPR-005 | Scheduled observer and manual REST operation coexist in fixture | Host observer state is labeled separately; stopping it does not cancel manual/server work or create another job. |
| V41 | REST reports | CPR-006 | Empty inventory, multiple report pages and exact detail | Bounded documented CLI/UI paging, correct run identity and Envelope shape; no fake empty-success fallback. |
| V42 | REST reports | CPR-006 | Missing/malformed/oversized report, wrong UUID/run ID and stale cursor | Classified visible refusal; no mixed pages, silent truncation or substitution of a newer report. |
| V43 | REST reports | CPR-006 | Client archive unavailable; static check of production report adapter | Reports still use REST; no runuser/ls/cat read under /srv/hfcache/runs remains. |
| V44 | REST reports | CPR-006 | Path traversal, invalid run ID, leading option, arbitrary URL/method | Narrow fixed read command rejects before filesystem/HTTP side effects; no general proxy. |
| V45 | Host journals | CPR-006 | Large journal, unavailable journal and timeout | Explicit line/byte/time caps and truncation; report UI still works and journal never decides outcome. |
| V46 | Read rendering | CPR-007 | Server VersionCard gets valid failed Envelope | Stable code/message visible; correct existing version --server request retained. |
| V47 | Read rendering | CPR-007 | EstimateCard gets valid failed Envelope | Failure alert instead of dashes/zero/successful-looking estimate; no verification confidence. |
| V48 | Read rendering | CPR-007 | Status/list/report success, partial failure, failed Envelope and malformed success | Each shape rendered honestly; only validated success fields used; current working domain error handling preserved. |
| V49 | Read rendering | CPR-007 | Refresh fails after healthy/ready prior observation | Absent or explicitly stale data; old evidence cannot authorize actions or overwrite newer generation. |
| V50 | Profile diagnostics | CPR-007 | Native default differs from explicit rootless socket/profile overlay | Actual selected profile shown; no mistaken socket repair, native binary/import assumption or automatic endpoint fallback. |
| V51 | Security | CPR-007 | Synthetic API/Hub/MCP secrets in failures, input and retained data | No browser/argv/environment/storage disclosure, no cross-interface credential reuse or arbitrary trusted-helper input. |
| V52 | Boundary tests | CPR-008 | Actual installed CLI over temporary Unix socket with real failed/success Envelopes | Process/output/auth/candidate/job/report behavior proved beyond pure response stubs; zero live archive access. |
| V53 | Boundary tests | CPR-008 | Mounted React UI with realistic Cockpit promise/stream/close ordering | Original failure flows reproduced and corrected; no fake pass from bypassing the adapter or component lifecycle. |
| V54 | Boundary tests | CPR-008 | Real disposable Cockpit/PAM/systemd/rootless launcher chain | Actual identities/profile/secret delivery and reconnect behavior recorded; no NAS/live credentials; absence is a blocker, not a pass. |
| V55 | Release evidence | CPR-009 | Browser bundle, launcher/profile, image and server intentionally skewed | Mismatch/unavailable diagnostics and reviewed update handoff; package version alone never proves parity. |
| V56 | Gates | CPR-008 | pnpm/make/toolchain unavailable or frontend stage skipped | Plan acceptance fails or blocks explicitly; backend-green result cannot be recorded as Cockpit coverage. |
| V57 | Documentation and parity | CPR-009 | New runs CLI help/route/output mappings and old MCP/read interfaces | Docs/gates agree; no invented REST install/cancel/schedule endpoint or expanded MCP authority. |
| V58 | Compatibility | CPR-008 | Existing durable fixtures, candidate/tag exactness and operation history | No unrelated schema/publication changes; old receipt/result/backup evidence remains preserved. |
| V59 | Final gate | CPR-009 | Locked base/server/server+MCP installs, frontend build and extended gate | Actual commands/counts/exits recorded; scripts/check.sh --with-build and make -C cockpit check executed. |
| V60 | Handoff | CPR-009 | Plan closeout vs deployment and original-host symptom acceptance | Source/disposable/installed/NAS gates distinct; no unauthorized install/push/tag/init/live workload or erased blocker. |

## Execution layers

**Pure and component:** deterministic errors, exact Envelopes, state transitions,
rendered alerts, hostile handles/storage, tab unmount and bounds. Do not substitute
an independent reimplementation of the component logic for its real test.

**Actual CLI / socket:** run the built client against a private temporary API Unix
socket using synthetic credentials and controlled backend fixtures. Verify request
counts, candidate body bytes, exact terminal output and error classification.
No NFS mount or real writer endpoint is involved.

**Actual disposable Cockpit / rootless:** prove real privileged channels, transient
unit identity, fixed release/helper/profile binding, mounted secret and UDS client.
Use a separately provisioned disposable environment with no live archive. Pin
versions and preserve diagnostic evidence. This check is not a production install.

**Installed operator acceptance:** later, separately authorized verification of
installed identities and the original flow. Do not rerun the Validate candidate
button casually: it writes a host candidate and may launch Hub-contacting sizing.
NAS/workload acceptance remains a different, existing restricted gate.

## Gate commands

Use the versions declared in cockpit/package.json and the lockfiles. The reviewed
Node requirement is ^24.18.1 and packageManager is pnpm@11.18.0; do not silently
substitute the review container's older Node. The repository owns the exact gate:

```sh
scripts/check.sh
make -C cockpit check
scripts/check.sh --with-build
```

Use a documented PNPM override only where needed by the Makefile. Individual
`pnpm` lint/typecheck/test/build commands are useful during iteration but do not
replace the package gate. Capture explicit frontend execution; scripts/check.sh
can otherwise report a loud Cockpit skip. Do not add `live` or `nfs` marker runs
against a production writer under this plan's offline authorization.
