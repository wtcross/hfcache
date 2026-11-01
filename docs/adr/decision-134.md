# Preserve failure evidence and original operation identity

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 134.
- Status: Amended; boundary, candidate reconciliation and scoped recovery implemented; [decision 135](decision-135.md) replaces manual service starts, [decision 136](decision-136.md) replaces direct report reads, [decision 137](decision-137.md) validates read presentation and separate deployment identities, and [decision 138](decision-138.md) repairs guarded stdin framing; [decision 139](decision-139.md) preserves confinement during exact installed confirmation. Disposable and installed acceptance remain separate.
- Date: 2026-10-19.

## Context and decision

The existing fixed rootless REST client is the application transport. Its browser
adapter loses structured bridge/process fields, mistakes general failed candidate
requests for incompatible assessments and stores operation handles in tabs that
unmount. Preserve error category/stage and validated diagnostics independently of
terminal Envelopes. Recover bounded read connections without repeating mutations.
Keep original scoped recovery handles before transmission and outside tab state.
Uncertain Apply blocks repeat submission. Candidate writes/installations reconcile
exact expected bytes under the existing root guard without automatic cleanup.

## Rationale and alternatives

A generic reconnect toast discards evidence and cannot identify an installed
launcher/session defect. Replaying a pipeline risks another write or admission.
Browser credentials, arbitrary HTTP forwarding and local execution fallback would
weaken the fixed launcher boundary. Persistent raw configuration/logs are rejected;
only bounded validated nonsecret session metadata may support lookup/observation.

## Consequences

## Evidence and relationships

## Implemented boundary and connection behavior

## Implemented candidate reconciliation

The candidate pipeline preserves failed request Envelopes without forcing them
through assessment parsing. Bounded stage evidence publishes validation before
sizing, retaining original classified causes after interruption. Application
memory holds exact captured draft/base before transmission and survives tab
unmount. This memory is never serialized into browser storage.
Required successful sizing must cover the exact captured selector/revision set,
canonical resolved commits and publication sizing; missing or inconsistent success
fields refuse readiness. Repository defaults agree with backend policy, so omitting
`enabled` cannot skip sizing and valid defaulted documents remain editable.

Guarded read-only inspection uses the existing original lock without creating
files and reports exact candidate/base/installed/backup matches or absent/changed/
unknown evidence. A missing or unsafe lock is unknown, never recreated by
inspection. Different pre-existing candidate bytes cannot be overwritten; exact
matches can be reused without replacing their inode. Lost write acknowledgement
permits only explicit matching revalidation without another write. Lost install
acknowledgement requires installed/backup proof, explicit successful API
confirmation and acknowledgement. Neither read/remount nor missing files prove
nonexecution. No replay, cleanup, rollback or new installation endpoint results.

This preserves CP-11/INV-006 and decision133's tag-only exact-byte boundary;
operational fingerprints never replace byte comparisons. Real installed/session
acceptance remains distinct from pure, guarded-filesystem and mounted UI tests.

## Implemented scoped operation recovery

An application-owned registry records a validated original key synchronously in
tab-scoped session storage before starting a keyed submission. It covers candidate
sizing, installed sizing, diagnostics, selected jobs and maintenance/repair client
submissions. Installed full sync/verification service controls remain the existing
explicit exception. Tab unmount and display abort cannot cancel the existing
observer or stop internal identity collection. Reload restores safe handles;
prepared records become uncertain rather than being replayed.
Restored terminal summaries are also unverified until authenticated original
observation confirms them. Otherwise a forged but well-shaped summary could
silently resolve uncertainty and enable another submission. Missing history and
contradictory summaries retain the original record and block that transition.

Storage contains at most 32 records/64 KiB of allowlisted action/route, original
key/ID, host/profile/endpoint/credential-class/archive authority and terminal
summary. It contains no request/result bodies, raw TOML, credentials or logs.
Missing access, corrupt/changed storage, failed persistence and capacity exhaustion
block new submissions. Learned identities remain in application memory if later
persistence fails. Unresolved records are preserved; only conclusive terminal
summaries may be evicted when capacity requires room. Original result identities
remain evidence when a later ID or terminal result conflicts.

The fixed authenticated `client describe` command reads capabilities/version and
emits only the independently versioned metadata allowlist. It does not open an
archive or submit work. Unknown archive UUID is truthful null and grants no job
or saved-observation authority. Public strings, including derived hashes, must
not equal or contain registered credentials: a collision refuses with fixed
`HFAPI017`, without emitting a redacted pin. Failed server metadata requests retain
their exact original Envelopes, independently of the local presentation command.

The browser binds records to its trusted transport host and selected client
scope. Each deliberate submission/lookup/wait first refreshes authenticated
authority. The same CLI process compares `--expected-client-scope` using its
selected settings, actual endpoint, credential class and confirmed archive UUID
before the target request. Browser storage never selects routing or credentials.
This is a same-process comparison, not an atomic HTTP precondition across server
reconfiguration; existing protected deployment/quiescence and server archive
identity checks remain necessary. A post-transmission mismatch remains uncertain.
The server instance is recorded, while an instance restart alone does not replace
otherwise matching authority or the original operation. Unknown/changed scope
refuses observation; missing/expired history preserves handles and uncertainty.
Recovery invokes only authenticated lookup of the original key and observation
of its original ID, with no POST replay, cancellation or replacement key.

Maintenance Apply consumes the preview before asynchronous work and blocks a
second Apply on submit/observation failure, even with an earlier successful dry
run and no applied Envelope. Preview readiness also requires its original scope
and connection generation; the same-process pin closes a later target change.
Configuration preparation, preview, install, confirmation and acknowledgement
require fresh captured authority, preserving uncertainty and original evidence
when it becomes stale. Copied recovery commands use the fixed service-identity
launcher/settings/socket, expected scope and quoted positional handles after
`--`, including safe option-like keys.

## Manual full-job amendment (2026-10-20)

[Decision 135](decision-135.md) now replaces the CP-04 manual service-start
exception with keyed REST full jobs. The report exception remains current. Fresh
protected host-profile inspection gates effects; all operation recovery,
uncertainty, credential separation and deployment restrictions above remain.

## REST reports amendment (2026-10-20)

[Decision 136](decision-136.md) now replaces the CP-01/09 direct-report exception
with authenticated bounded CLI reads. Exact negative Envelopes and response/run/
archive identity remain separate from cursor metadata, host journal diagnostics
and read connection errors. No archive-file fallback or execution authority follows.

## Read presentation amendment (2026-10-20)

[Decision 137](decision-137.md) requires typed read payloads, explicit partial/
unavailable/empty states and fresh host/session evidence. Version remains an
authenticated server read. Browser build, selected release and API authority
diagnostics stay advisory and independent of action permission or installed
symptom acceptance. Original negative Envelopes and classified causes remain.

## Application-owned browser session amendment (2026-10-26)

The new registry stores at most32 records/64KiB of closed safe-handle metadata,
reserving growth for unresolved entries. Persist the original key before POST;
failure before transmission blocks submission, while possible transmission plus
storage failure preserves in-memory handles and the block. Never evict unresolved
records or replay a POST. Restored prepared/terminal summaries are unverified
until authenticated original observation. Only a provable current-session
pre-fetch refusal can durably remove its own fresh prepared record before
unblocking. Its not-submitted summary remains memory-only; there is no persisted
flag or cleanup inferred from missing receipts.

Basic-subject keys and historical bearer keys have different namespaces. Manual
ID imports retain unknown creator/key ownership; they cannot resolve an unrelated
uncertain key-only record. A legacy key is an unbound retained reference, not a
current Basic key or a permanent block in that unrelated namespace. Explicit
compatible reconnect changes current observation context without rewriting
original admitted authority. Changed scope/auth generation clears private cached
evidence while preserving safe unresolved handles. Cross-tab notices are advisory
only. Stop observing aborts reads, not execution; unknown or unconfirmed protected
configuration effects remain distinct from generic API failure/interruption.

Exact metadata and user procedures are in [schemas](../schemas.md#186-browser-recovery-metadata-schema-1)
and [browser recovery](../web-ui/operations.md). No new endpoint, server receipt,
credential grant, cancellation or automatic recovery effect is introduced.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
