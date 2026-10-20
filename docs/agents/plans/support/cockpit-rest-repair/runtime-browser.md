# Real disposable Cockpit browser acceptance

This manual V54 driver uses the installed Firefox WebDriver BiDi implementation
and Node's built-in WebSocket. It adds no project dependency. It loads the actual
installed plugin and Cockpit transport, authenticates the synthetic PAM account,
uses the real internal `cockpit.Superuser` proxy, and invokes the existing fixed
launcher through the actual application. It does not import the controlled
component boundary or replace `cockpit.spawn`, D-Bus, promises or transport.

The driver is outside the default `*.test.ts` and mounted-test entrypoints. Its
absence/unsafe-fixture result is exit 69 with an explicit blocked result, never a
skipped pass. A failed assertion after verified guest identity returns exit 1 and
retains only bounded completed checks. A browser prerequisite probe is not real
PAM acceptance.

## Preconditions and identity

The current `fresh-pipe-candidate-only` mode is bound only to the fifth fixture:
`.local-fixtures/cpr-runtime/cpr008-pipe`, synthetic `cprtester`, hostname
`cpr-pipe.local`, fixture ID `cpr008-pipe-` plus 32 lowercase hexadecimal digits,
and loopback Cockpit `https://127.0.0.1:19058`. It uses the same initial proof,
nonce, exclusive markers and candidate/install/interruption protocol below.
It rejects all legacy continuation flags and every older fixture path; it imports
no old operation and has no job submission path.

The fourth `fresh-candidate-only` mode retains its exact fixed bindings:
`.local-fixtures/cpr-runtime/cpr008-framed`, `cpr-framed.local`,
`cpr008-framed-` plus 32 hexadecimal digits, and
`https://127.0.0.1:19057`. That fixture wrote/validated its candidate and installed
its exact bytes/predecessor, then failed confirmation before CLI start under a
real enforcing `init_t` to `etc_t` stdout-file write denial. Its unknown installation,
predecessor, original locks, sent markers and profile remain preserved. It is not
retried, discarded, rolled back or cleaned after uncertainty. ADR139's anonymous
pipe and bounded local collector require independent fifth-fixture acceptance.
The third guest `.local-fixtures/cpr-runtime/cpr008-fixed`, `cpr-current.local`,
Cockpit `https://127.0.0.1:19056` remains retained diagnostic/original-operation
evidence; its candidate sent marker prevents replay. The fixture
must have no production credentials, host shares, external routes, or live/NAS
archive. Preserve enforcing SELinux, systemd hardening, the independent original
guard, NFS-ro and masks. All earlier guests retain their original evidence and configuration state.
The second guest exposed a real masked-timer helper refusal and remains unchanged;
the third fixture binds its reviewed repair without rewriting prior evidence.

The provisioner creates private `browser-manifest.json` with mode 0600 under the
owned mode-0700 fixture root. The exact keys are:

| Key | Required value |
| --- | --- |
| `schema_version` | `1` |
| `fixture_id` | Current pipe mode: `cpr008-pipe-` plus 32 lowercase hexadecimal digits; fourth: `cpr008-framed-`; third: `cpr008-` |
| `source_commit` | Base `41d818e13c1f4860a286f24ba91bd0f384b09172`, not a pristine fixture claim |
| `source_dirty` | `true`, explicitly binding the reviewed helper repair |
| `helper_sha256` | SHA256 of the actual fixed installed helper |
| `patch_sha256` | SHA256 of the exact reviewed source patch |
| `closure_sha256` | SHA256 of compact canonical sorted JSON of the artifact manifest's `files` map |
| `cockpit_url` | Pipe: `https://127.0.0.1:19058`; fourth: `https://127.0.0.1:19057`; third: `https://127.0.0.1:19056` |
| `tls_sha256` | SHA256 of the guest's DER Cockpit certificate |
| `username` | `cprtester` |
| `password_file` | Absolute fixture `keys/cprtester.password` path; no value in manifest |
| `guest_hostname` | Pipe: `cpr-pipe.local`; fourth: `cpr-framed.local`; third: `cpr-current.local` |
| `bundle_sha256` | SHA256 of decompressed installed/served `index.js` |
| `image` | Actual immutable `sha256:` application image identity |
| `artifact_index_sha256` | Actual selected artifact-index SHA256 |

The browser certificate is checked before navigation. Only the owned ephemeral
Firefox profile accepts that disposable self-signed endpoint; no host trust or
Cockpit authentication policy is changed. Firefox receives a minimal environment
without ambient credentials. Login and privilege passwords travel only in the
private in-memory automation connection. Protocol payloads, raw DOM, candidate
contents, browser logs and screenshots are not exported. Evidence contains only
allowlisted public identities and assertion results. The guest marker
`/etc/cpr-runtime-identity.json` must match the fixture UUID and source before the
candidate test starts. The served bundle must match the provisioner's hash; an
actual privileged fixed-path SHA256 read must match the repaired helper hash.
The protected host profile binds the expected index and image. Dirty fixture
provenance remains separate from the unchanged application base.

The guarded profile must explicitly allow control and configuration, while
archive, Hub, schedule and observer permissions stay false. No enabled repository
may require sizing. The fixed root configuration
lock and guarded installed configuration must already exist with their actual
safe ownership/mode; the driver does not provision them or initialize an archive.

## Command and behavior

From the repository root, after the provisioner has declared the guest ready:

```sh
rtk env CPR_RUNTIME_BROWSER_MODE=fresh-pipe-candidate-only CPR_RUNTIME_BROWSER_MANIFEST="$PWD/.local-fixtures/cpr-runtime/cpr008-pipe/browser-manifest.json" CPR_RUNTIME_BROWSER_INTERRUPTION=1 node cockpit/test/runtime-browser.mjs
```

In fresh mode, a protected `evidence/browser-initial-state.json` has exactly eleven keys:
`fixture_id`, `source_commit`, `state: ready`, `artifact_index_sha256`, `archive_id`,
`installed_sha256`, `installed_inode`, `installed_device`, `candidate: absent`,
`backup: absent`, and `configuration_lock: absent`. It binds the original base to
this new fixture/index before browser work. The actual Configuration read may
create its normal safe lock; the provisioner then noncreatively pins that inode.
The new exclusive `browser-fresh-before-awaiting.json` carries a random nonce.
The fresh proof must echo that nonce and compare the initial installed bytes/inode,
absent candidate/backup and safe lock. Subsequent candidate/install/holder proofs
must echo the same nonce and retain the original lock identity.

Fresh mode performs one actual candidate validation, checks independent candidate
hash/bytes, then performs one deliberate Install and exact installed API
confirmation. It requires the visible install acknowledgement and confirmation
stage result plus a 64-hex fingerprint, then waits for independent installed
candidate hash, original backup hash and unchanged-lock proof. Only this fully
known successful installation becomes the base for the separate interrupted write.
There is no discard in fresh mode. Exclusive Validate/install/interrupted-write
markers are created before their respective actions and never removed. After the
interruption, the driver genuinely reauthenticates and requests only explicit
read-only inspection after natural holder expiry. No operation is submitted or
imported; authenticated original-operation proof is retained separately from the
third guest. The profile remains retained after uncertain execution.

The following historical third-guest flow and barriers remain documented as
observed evidence; they are not instructions to replay an old candidate or job.

The driver verifies genuine login, unprivileged bridge identity, administrative
bridge authentication, served artifact identity, the exact protected profile,
and authenticated fixed-client authority. One deliberate prune dry run must
produce an original terminal result with its key/ID. An empty lock-free dry run
may succeed with no plans or applied changes despite the held domain guard;
record its actual outcome. The actual recovery buttons then request authenticated
lookup and wait of that original operation.
The provisioner records bounded distinct PID1 fixed-client launch categories,
keys and units, the sole submission barrier and original durable identity.
V54 has no independent wire POST counter; access logging stays disabled. Real
CLI/private-socket tests separately count exact HTTP requests. The combined
layers establish behavior without mislabeling launcher/receipt counts as wire
counts, and the DOM alone does not count backend requests.
Before submission an exclusive-create private barrier prevents a new harness
attempt from blindly sending another job. The original pre-send key and scoped
identity are retained privately as soon as the actual registry publishes them.
A failed check retains the owned private Firefox profile and its recovery state.
The barrier is never automatically removed; review and recover the original
operation before deciding any next action.

It opens the actual Configuration tab, edits the actual text control,
and deliberately requests one guarded candidate write/validation. Successful
readiness is observed through the actual Install button and a provisioner
read-only hash/ownership check against the captured bytes. It does not click
Install, cancel, reinstall, roll back or replay a request. Without the separate
interruption experiment, the candidate remains available for explicit inspection.
Closing the owned browser detaches presentation and makes no application
cancellation request.

For the separate real interruption experiment, start with
`CPR_RUNTIME_BROWSER_INTERRUPTION=1` in the same command. After the successful
candidate is fully known, the driver deliberately discards it through the normal
guarded control BEFORE any uncertainty. It writes the private checkpoint
`evidence/browser-awaiting-lock.json`. The provisioner then starts a bounded,
noncreating holder of the original root configuration lock, retaining its inode,
owner/mode, holder PID/starttime and prearranged expiry. It supplies
`browser-lock-ready.json`, and after the next actual writer is proven waiting,
`browser-writer-waiting.json`. Both private bounded JSON records require the
fixture/source identities and `state: ready`. The domain guard is untouched.

The driver then uses real `Superuser.Stop`, observes the original classified
candidate-write failure/uncertainty, genuinely authenticates a fresh bridge and
requests only read-only fixed-file inspection after the bounded holder expires.
It asserts original cause retention, unchanged installed base and blocked ordinary
validation. No revalidation, install, replay or cleanup follows the uncertainty.
The holder's scheduled expiry is prearranged, not a recovery reaction. These
steps are not a reproduction claim for the original installed trigger. Any
uncertain action stops dependent submissions; inspect and observe the original
state instead of repeating the pipeline.

## Original-only continuation after a harness assertion

The first sole submission completed successfully. The harness then failed while
extracting the key from adjacent paragraph `textContent`: the regular expression
captured the UUID followed by the next paragraph's `Original` prefix. This is a
harness defect. The original key, scope, receipt and exact result remain retained;
the submission barrier remains in place. Do not run the full submission path again.

The dedicated continuation is:

```sh
rtk env CPR_RUNTIME_BROWSER_MANIFEST="$PWD/.local-fixtures/cpr-runtime/cpr008-fixed/browser-manifest.json" CPR_RUNTIME_BROWSER_CONTINUE_ORIGINAL=1 CPR_RUNTIME_BROWSER_INTERRUPTION=1 node cockpit/test/runtime-browser.mjs
```

This path cannot enter Maintenance or the job submission branch. It authenticates
a fresh native tab, requires no restored browser registry, and does not reconstruct
session storage. It loads the protected pre-send key/scope and independently
retained terminal projection. Actual product `hfcacheArgv` and bundled `runSpawned`
perform real `operations lookup -- KEY` and `operations wait -- ID`, with the
original compare-only authority pin, through genuine `cockpit.spawn`. The lookup
must authenticate the expected route, principal, archive, ID, terminal state and
run ID. Wait must return the exact original Envelope, checked against its durable
sorted indent-2/trailing-newline SHA256. No arbitrary read or new job command is
accepted by this helper. These are native CLI recovery reads, not a claim that a
new tab restored the original React registry. The mounted tests separately prove
that registry behavior.

The first original-only continuation passed the exact authenticated lookup/wait,
then safely refused BEFORE Validate because an added textarea-equals-installed
assertion was incorrect. Form-to-Text serializes a proposed canonical draft; it
may differ from the unchanged original installed bytes. The failed artifact and
first phase barrier remain. For this exact known prewrite stop only, add
`CPR_RUNTIME_BROWSER_RESUME_KNOWN_PREWRITE=1` to the continuation command. It
requires that saved failure, a fresh independent original-base/absent-candidate/
absent-backup/pinned-lock/zero-write proof and a new exclusive write-attempt
barrier. It refuses if `browser-candidate-validate-sent.json` exists. That marker,
with the captured candidate hash, is exclusively created BEFORE the first Validate
click and is never removed. The distinct deliberate interrupted write has its own
exclusive marker. An old prewrite failure can never authorize reentry after any
subsequent uncertain writer or installation. This is not a general retry mode.

Before candidate-only work, a fresh provisioner read-only proof must establish the
unchanged original installed base and absent candidate/backup under the original
configuration lock. A second exclusive-create barrier prevents automatically
rerunning that phase. The successful candidate then has its own read-only hash
checkpoint before deliberate known-state discard. Configuration validation uses
its expected synchronous API POST; “no second job submission” does not mean no
HTTP POST of any kind. After uncertainty, the only configuration action is explicit
read-only inspection; original-operation recovery remains lookup/wait reads.

## Observed prerequisites

On 2026-10-20, Node `v24.18.1` and Firefox BiDi browser version `140.13.0` created
a real session in a fresh owned headless profile. A JSON evaluation returned the
expected bounded marker and the browser exited normally. This contacted no guest
and has `real_pam: false`.

`rtk node cockpit/test/runtime-browser.mjs` without a manifest returned exit 69,
`state: blocked`, `code: fixture-not-provisioned`. V54 remains unpassed until
the explicit guest command and required interruption/recovery observations run.

The real BiDi probe also passed with Firefox's minimal environment and private
cache/config/data directories. Its explicit profile is owned; HOME is not
repurposed. No ambient credential/session environment is forwarded.

BiDi follows the pinned browser's supported
[direct connection](https://developer.mozilla.org/en-US/docs/Web/WebDriver/How_to/Create_BiDi_connection)
and [session creation](https://developer.mozilla.org/en-US/docs/Web/WebDriver/Reference/BiDi/Modules/session/new)
interfaces. The automation listener is loopback-only and exists only for this
owned profile; see Mozilla's [Remote Agent security model](https://firefox-source-docs.mozilla.org/remote/Security.html).

## Actual text-channel framing diagnosis

The single candidate Validate attempt did not reach readiness within 90 seconds.
The driver retained all one-way sent markers and profile; no discard, install,
validation replay or planned lock interruption followed. Independent read-only
inspection found candidate/backup absent, installed base/inode and root lock
unchanged, no retained proof flock, no relevant AVC, and no candidate-validation
CLI launch. The original live stage alert was not captured before browser close;
its cause remains unknown. Host marker/guest journal timing cannot classify the
last describe: measured guest-minus-host clock bounds overlap the apparent gap.
The failure is retained in [the unresolved artifact](gates/cpr-008-browser-candidate-unresolved.json).

A separate harmless stdin diagnostic then reproduced a concrete transport defect
in genuine Cockpit 368, Node 24.18.1 and Firefox 140.13.0esr. An independent fresh
native PAM/admin session sent privileged ASCII `a|b|` to a fixed, pre-bounded
read-only stdin reader and obtained the exact four bytes (SHA256
`8609ff598817d3680360cee50279d3bb873d41288ad63a8469188b62ab9eac13`).
Sending `a\0b\0` next through the same text-mode spawn/input path failed with
original Cockpit `problem: disconnected`, null process exit status. An independent
unprivileged session reproduced the same ASCII success/NUL disconnection. The
later privileged cases in that first disconnected session are explicitly
confounded and are not counted as independent privilege failures.

[Closed RED evidence](gates/cpr-008-framing-red.json) records the exact commands,
source hashes, versions and safe projections; the corresponding matrix and
privileged probe source captures are alongside it. The diagnostic processes made
no API requests or filesystem mutations; the loaded application's ordinary
background reads are separate. This establishes a real defect in the NUL-framed
text transport used by the candidate boundary. It does not prove that the
original installed host has the same cause, and does not reconstruct the earlier
missing alert. No candidate/job request was repeated to diagnose it.

Future driver failures now collect only allowlisted live stage/category/problem,
exit/code facts and UI booleans before closing. Effective disabled state includes
an ancestor disabled fieldset and visibility. These improvements do not invent
missing evidence for the earlier attempt. A repaired framing probe and a fresh
independent immutable fixture are required for runtime acceptance; all previous
fixtures, sent markers, candidate states and original operation identities remain.

The separate GREEN stdin-only compatibility probe passed after the canonical
base64 framing repair. Three successive synthetic Unicode/trailing-LF pairs,
including an empty base, were encoded by the actual repaired invocation builder.
The real privileged Cockpit process executed the actual SCRIPT decoder prefix,
cut before its first filesystem check, and returned only exact lengths/hashes.
Each result matched the original UTF-8 bytes. Wire sizes were 58, 34 and 2,238
ASCII bytes with zero NUL; a new privileged fixed printf after EACH frame proved
the real bridge remained connected. [Closed GREEN evidence](gates/cpr-008-framing-green.json)
and [source capture](gates/cpr-008-framing-green-source.txt) preserve the command,
source/decoder hashes and all three projections. No application/configuration
operation, API command, candidate replay, filesystem mutation or guard change
was part of this diagnostic. The old guest's deployed bundle and uncertain
candidate attempt remain unchanged; this is locally repaired source through the
real bridge, not full fresh-artifact runtime acceptance.

The final frozen receiver was then tested separately with the same harmless
three-frame probe. [Final GREEN](gates/cpr-008-framing-final-green.json) records
full source `5b64be973d436ed983ea0eeac5415f7b2110a9a7c56947288fe2669c17251684`
and directly executed prefix
`da8419974a347399a40735caac32af5e8328268dbdbca9cff60e1648a0467244`;
all three exact byte/hash checks and subsequent privileged bridge checks passed.
The earlier GREEN artifact is retained unchanged. Its full-source hash was read
at publication while the source changed, so that value is capture-time metadata,
not an executed source pin; [the capture note](gates/cpr-008-framing-green-capture-note.txt)
qualifies it. Its direct prefix observation remains valid historical evidence.

A standalone third-guest observation then passed AFTER the real native NUL bridge
disconnections. A fresh genuine PAM/admin session used the existing
`nativeOriginalReads`, `hfcacheArgv` and `runSpawned` helpers directly; it did not
execute continuation main, import browser registry data or enter any candidate/job
path. Authenticated original lookup returned operation
`457a424efb7be3cd24c1d6b12f6e9825`; wait preserved original run
`e6e4d5a51cbe46efab2acaad5968a280`, success/exit0 and exact durable SHA256
`2247fe32eaced27766379ce905cc9340ba25effc8d8cc3732204e32f09fbb38f`.
The original scope pin matched and the privileged bridge remained connected.
[Closed observation evidence](gates/cpr-008-original-after-disconnect.json) and
[source capture](gates/cpr-008-original-after-disconnect-source.txt) retain the
command/hashes. The private read-only observation barrier/result remain intact.
There was no diagnostic POST, new job, candidate action or browser storage
reconstruction. Ordinary application background reads remain separately qualified.
This original-operation proof belongs to the third fixture; fresh candidate-only
acceptance imports none of its handles or state.
