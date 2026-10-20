# Isolate the reported `reconnected` failure

## Scope and caution

This is a procedure for a later authorized diagnostic session, not commands run by
this review. The installed host may be the production writer. Do not change
credentials, mounts, security labels, guard holders, masks, services or release
selection to test a theory. Do not run sync/verify/recover/prune/repair/init.
Even the UI's Validate candidate action writes a host file and can submit a sizing
job that contacts Hub; it is not a harmless read-only ping.

Source shows error propagation and several independent defects. It does not prove
the actual session event, deployed commit, candidate contents or daemon health.
Keep the user's original message verbatim alongside the structured fields; never
infer a failed/absent API request solely from that message.

## 1. Identify the deployed chain before reproducing

Record the Cockpit version, selected target host, administrative-access state,
browser package identity/checksum, application source commit, physical fixed client
and container-helper release path, rendered-profile identity, image digest and
server/client version. Use protected, read-only metadata inspections, not secret
file contents. A common version string such as 0.2.1 is not a source checksum.

Confirm the actual profile is the guarded rootless deployment, a separately
supported profile, or unknown. The shipped adapter fixes the rootless launcher and
socket; it has no native selector. A missing launcher or mixed installation is an
installation mismatch to explain, not an invitation to discover/run another CLI.

Keep native `/run/hfcache/api.sock` distinct from this adapter's explicit rootless
`/run/hfcache/api/api.sock`. The helper binds `/etc/hfcache` and overlays its rendered
client TOML. Candidate visibility exists in source; verify actual mounting only
in a scoped inspection rather than asserting the source mount is missing.

## 2. Capture the first failing boundary

A corrected diagnostic record should contain safe fields only:

```text
host/profile/release: nonsecret identities, not token sources or values
stage: installed-read | candidate-write | candidate-validate | candidate-preview |
       install | installed-confirm | operation-observe
cockpit_problem: the original bounded problem code if present
process_exit_status / process_exit_signal: when actually supplied
api_or_domain_code: from a validated terminal Envelope only
original_key / operation_id: validated nonsecret handles if already known
last_acknowledged_stage: known, not inferred from a spinner
```

Do not export raw browser network captures, configuration bodies, cookies,
Authorization headers, secret files or unrestricted journals. A controlled safe
trace should timestamp stage entry/acknowledgement without recording input content.
Distinguish the initial candidate write from CLI launch and validation. The bare
message can come from a host operation before HTTP; a valid HFAPI Envelope instead
shows that the CLI classified a failure. Neither proves archive execution state.

## 3. Check the application path using non-job reads

Only with appropriate diagnostic authorization, reproduce the selected identity
and launcher exactly. For example, the following read starts a transient observer
and client container; it is not a pure host-stat operation:

```sh
sudo systemd-run --quiet --wait --pipe --collect \
  --property=User=hfcache --property=Group=hfcache \
  --property=UMask=0027 --property=MemoryHigh=4G \
  -- /usr/local/libexec/hfcache-client \
  --client-config /etc/hfcache/client.toml \
  --api-socket /run/hfcache/api/api.sock --json version --server
```

Retain the exact JSON result and safe process metadata, not a human-text guess.
Do not add a bearer literal, Hub token option, native executable fallback or a
`--local` validation fallback. A successful command outside Cockpit narrows the
fault toward browser/privilege/session/bridge integration but does not prove which
one. A launcher failure with no Envelope narrows it before successful CLI result
observation; inspect actual known process facts. A valid HFAPI error gives a stable
classification to follow. Do not blindly rotate secrets on an authentication error.

## 4. Separate candidate validation from the whole UI pipeline

Candidate validation is synchronous POST `/config/validate`; it does not have an
operation receipt. Sizing is POST `/plans`, keyed, may contact Hub and persists
control state. Installation is a guarded host rename followed by installed
validation. Reproduce each only under its appropriate authorization and exact
content/base guards; never invoke an unguarded CLI validate as proof that the UI's
multi-editor installation conditions passed.

Test a safe synthetic candidate in a disposable fixture first. Observe both a
well-formed compatible result and a valid failed API Envelope with no assessment
fields. The latter must display its original code, not a plugin-version error.
Test real Cockpit error objects at each phase, including an administrative/session
transition. Preserve the draft and exact guard evidence; do not retry the whole
pipeline to test connection recovery.

## 5. Choose recovery from evidence, not the word `reconnected`

| Evidence | Safe next step | Do not infer or do |
| --- | --- | --- |
| Installed read/channel unavailable | Re-establish permitted connection and repeat a bounded read | Do not change config, API settings or credentials merely from this message. |
| Candidate write started but acknowledgement missing | Guarded read-only comparison against known draft/base | Do not overwrite/delete candidate or claim the write did not happen. |
| Valid failed candidate validation Envelope | Display code and correct the diagnosed request/source in a reviewed step | Do not treat it as success or a generic schema mismatch; no local fallback. |
| Candidate assessment syntax-valid but incompatible/unknown authority | Keep install disabled; follow manual authority procedure | Do not repoint credentials or skip preview. |
| Key exists, admission/result unknown | Preserve original scope/key; authenticated lookup, then wait by ID when known | No new key, POST replay, archive recovery or cancellation assumption. |
| Installation/confirmation acknowledgement missing | Preserve backup and exact evidence; reconcile installed bytes under guard and revalidate | No auto reinstall, rollback, cleanup or success from fingerprint alone. |
| D-Bus cached client closed / polls fail | Replace read connection and mark stale state until fresh reads | No unit action replay, user-bus retargeting or mask changes. |
| Full-job/schedule controls point at masked system units | Explain restricted deployment; follow source remediation and separate acceptance | Do not unmask/start alternate units or clear the archive guard. |

Missing or expired operation history is not proof of nonexecution. The server,
not the page or CLI process, owns admitted work. Actual executor drain and archive
recovery remain separate operator procedures governed by existing runbooks.

## 6. Acceptance record

Record separately: source regression fixed; disposable real bridge/launcher chain
passed; installed artifact parity verified; original host candidate workflow
verified; NAS/workload acceptance unchanged. The plan does not collapse these into
one “works now” checkbox. If the exact installed trigger remains unknown, state
what was checked and which safe observation would distinguish the remaining causes.
