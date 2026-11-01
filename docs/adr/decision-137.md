# Validate read presentation and separate deployment identities

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 137.
- Status: Accepted; source implementation and automated acceptance passed. Real disposable and installed acceptance remain separate.
- Date: 2026-10-20.

## Context and decision

Keep `version --server`, complete CLI status/list pagination and existing job,
candidate and report identities. Validate the current documented CLI payloads,
including nullable unmanaged fields and unreachable health, without reimplementing
backend resolution or inferring writability from health/read success. Existing
protected host permission, authenticated capabilities and server gates remain
authoritative. No new API route, capability field or browser endpoint selector.

Add advisory diagnostics that distinguish the loaded browser build, the selected
protected physical release and the authenticated client/API authority. Existing
typed host/client metadata supplies selected source/index/image, client profile/
endpoint/credential class/archive UUID and server instance. These are different
facts; selected bindings do not prove the running payload or original host symptom.
Package versions alone do not establish parity. Unavailable or stale metadata
remains unavailable, with no fallback to a native executable or another endpoint.

The browser build embeds one independent exact schema:
`{schema_version:1,source_commit,source_dirty,inputs_sha256}`. Commit is lowercase
40-hex or null; dirty is boolean or null; input digest is lowercase64-hex or null.
Missing/invalid/unknown fields produce a fixed unavailable diagnostic, never raw
rejected values. A missing commit has unknown dirty state. Development/watch
builds emit unknown provenance rather than a stale production claim.

## Rationale and alternatives

Throwing every nonzero result away would erase useful domain classifications.
Unchecked TypeScript casts and empty defaults conceal malformed or refused reads.
Adding fields to strict server capabilities or introducing another host helper
would widen an existing protocol for presentation alone. Build-only public input
identity and existing authenticated metadata provide useful comparisons while
keeping unknown facts explicit. A package version or selected symlink is not
sufficient evidence of the bytes a browser or running executor actually uses.

## Consequences and relationships

## Shared query and original-operation state amendment (2026-10-26)

The application browser separates query loading/stale/unavailable/domain failure
from queued/waiting/running/terminal/interrupted/unknown operation observation.
Original structured classifications remain typed; rejected content is never
used as an empty inventory, readiness or successful outcome. Event sequence gaps
and retention loss remain visible. Request IDs, admitted operation IDs and domain
run/report IDs retain separate meanings.

The shared query/controller layer bounds retained encoded logical evidence to
32MiB, independent of exact JavaScript heap usage. Each session read is at most
8MiB and never exceeds its existing route ceiling. Observation uses two active
reads globally/one per handle, at most three eligible GET retries after the
initial attempt with1/2/4second delays,120cycles or five minutes, and32events/
64KiB per handle. Limits end or refuse observation without changing execution.
They introduce no server configuration or more permissive route bound.

Explicit compatible reconnect obtains fresh authenticated bootstrap context
after an API instance change. It retains original admitted scope rather than
silently rebinding an operation. Changed scope/authentication, including a new
local authentication generation with identical returned values, invalidates
private caches and late callbacks. A different interface/wire release requires
explicit reload without automatic replay or loss of safe uncertain handles.
The [recovery guide](../web-ui/operations.md) defines the user procedure; full job
forms and repository views are separate work.

## Existing-job presentation composition (2026-10-26)

The application Operations workspace adds bounded forms for existing sizing,
sync, verification, diagnostics and offline refresh, with explicit scope/effect
and effective-capability explanations. Queued/waiting/running states, benign
HFMNT010 busy, partial repository results, integrity findings and interrupted or
unavailable evidence remain distinct. No manufactured progress, success or empty
result follows from HTTP200/202, missing events or observation failure. Existing
original-handle state, server grants/locks and [typed report rules](decision-136.md)
remain authoritative; job forms introduce no endpoint, dependency or replay.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
