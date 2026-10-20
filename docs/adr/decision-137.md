# Validate read presentation and separate deployment identities

- Decision identity: 137.
- Status: Accepted; source implementation and automated acceptance passed. Real disposable and installed acceptance remain separate.
- Date: 2026-10-20.

## Context and decision

Valid failed CLI Envelopes resolve as values. Several Cockpit cards still assume
success payloads, render absent values as healthy-looking empty data or retain
old evidence after a refresh. The current unreachable-status payload deliberately
omits health counters. Preserve original Envelopes and validate each payload
before rendering: successful data, successful empty, classified failure, valid
partial data, malformed data, loading and unavailable are distinct states.
Malformed success cannot become zeros, an empty inventory or action readiness.
Failed reads render their original codes first; separately validated partial data
is explicitly informational and never authorizes a mutation. Refresh/session/
host changes invalidate old evidence and late callbacks without closing observers.
Passive invalidators read current stores and cannot erase a newer acknowledged
inspection, confirmation or proposal. An older pipeline generation does not make
a later explicit current-generation inspection stale. Existing exact-content and
authenticated original-scope checks still control reconciliation readiness.

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

Fresh production build input hashing uses only declared public repository inputs:
regular files under `cockpit/src/`, the build scripts, Makefile, package manifest,
lockfile and pinned `pkg/lib` helper inputs. Sort relative paths and frame their
names, lengths and bytes deterministically; never hash fixture/private files or
emit environment/absolute paths. This is a browser build-input digest, not the
output bundle checksum or a hash of installed dependency bytes. Capture source
commit, working-copy state and digest before and after the build; refuse a changed
snapshot. A source export can report an input digest with unknown Git provenance.
Runtime diagnostics grant no effect permission. Actual bundle checksum, image,
physical bindings and running payload still need separate operator verification.
Linux production provenance uses descriptor-anchored no-follow traversal through
the build process's own `/proc/self/fd`, including every declared ancestor.
Other build platforms emit unknown provenance rather than using an unsafe read
fallback or losing the existing ability to build the browser bundle.

## Rationale and alternatives

Throwing every nonzero result away would erase useful domain classifications.
Unchecked TypeScript casts and empty defaults conceal malformed or refused reads.
Adding fields to strict server capabilities or introducing another host helper
would widen an existing protocol for presentation alone. Build-only public input
identity and existing authenticated metadata provide useful comparisons while
keeping unknown facts explicit. A package version or selected symlink is not
sufficient evidence of the bytes a browser or running executor actually uses.

## Consequences and relationships

Amends [decision 122](decision-122.md) and [decision 134](decision-134.md), preserves
[decision 135](decision-135.md), [decision 136](decision-136.md), INV-006 and
CP-02/08/10/13. [Cockpit](../cockpit.md), [client guidance](../api-client.md),
[API health semantics](../api.md#routes-and-effects),
[installation](../cockpit-plugin/installation.md) and
[troubleshooting](../cockpit-plugin/troubleshooting.md) define the presentation.
No runtime dependency, durable format, REST/MCP authority, deployment or workload
permission changes. Source, disposable Cockpit/PAM, installed symptom and NAS
acceptance remain separate.
