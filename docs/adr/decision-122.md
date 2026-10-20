# Preserve Cockpit authority through the API client and guarded candidates

- Decision identity: 122.

- Status: Amended; see decision 133 and the amendments referenced below.
- Date: 2026-10-18.
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).


## Context, decision and rationale

Cockpit remains static host administration over fixed CLI/systemd interfaces.
The shipped launcher runs the fixed rootless API-only client with protected rendered
settings/socket and mounted named Podman REST source; host ImportCredential/native
launcher selection is not implemented by this plugin. Hub authority stays in the
API executor and no bearer reaches browser state, argv or ambient environment.
Legacy system-bus sync/verify/timer controls remain blocked on the guarded rootless
installation, with no redirect to same-named user units.

Require strict bounded schema-1 terminal Envelopes, separately bounded diagnostics/
progress and independently retained validated handles. Closure/timeout stops
observation without cancellation, automatic recovery or replay. Host-local report
browsing through privileged runuser/ls/cat and journal access remains an explicit
exception, not a remote REST client.

The persistent root configuration flock guards exact candidate and installed-base
bytes across syntax/compatibility/required preview, atomic backup/install and exact
installed fingerprint confirmation. Edits invalidate readiness; unknown/incompatible
authority blocks installation. Failed confirmation preserves uncertainty/backup,
clears readiness and requires reloading installed state. Giving the browser secrets,
trusting a posted preview or silently rolling back would discard these boundaries.

## Relationships and technical evidence

- [decision 123](decision-123.md)
- [087](decision-087.md)
- [089](decision-089.md)
- [091](decision-091.md)
- [092](decision-092.md)
- [119](decision-119.md)
- [120](decision-120.md)
- [121](decision-121.md)
- [Cockpit](../cockpit.md)
- [client](../api-client.md)
- [configuration](../configuration.md)
- [security](../security.md)
- [invariants](../invariants.md)
- [fixed command construction](../../cockpit/src/lib/command.ts)
- [injected runner](../../cockpit/src/lib/runner.ts)
- [bounded UTF-8 framing](../../cockpit/src/lib/stream.ts)
- [typed progress notices](../../cockpit/src/lib/events.ts)
- [terminal/envelope classification](../../cockpit/src/lib/envelope.ts)
- [API adapter](../../cockpit/src/api/hfcache.ts)
- [configuration adapter](../../cockpit/src/api/config.ts)
- [exact config guard](../../cockpit/src/lib/candidate-guard.ts)
- [readiness/confirmation pipeline](../../cockpit/src/lib/config-pipeline.ts)
- [unit-action boundary](../../cockpit/src/lib/systemd.ts)
- [command tests](../../cockpit/test/command.test.ts)
- [runner tests](../../cockpit/test/runner.test.ts)
- [framing tests](../../cockpit/test/stream.test.ts)
- [event tests](../../cockpit/test/events.test.ts)
- [envelope tests](../../cockpit/test/envelope.test.ts)
- [configuration tests](../../cockpit/test/config.test.ts)
- [guarded file fixtures](../../cockpit/test/candidate-guard.test.ts)
- [pipeline tests](../../cockpit/test/config-pipeline.test.ts)
- [Decision 127](decision-127.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

## Supplemental discovery amendment (2026-10-19)

[Decision 133](decision-133.md) defines proposed tag/curation identities, the narrow
independent-atomic adjunct exception and protected read capabilities. Existing
archive, candidate-byte, whole-archive authorization and registered MCP boundaries
remain in force until corresponding additive implementation is accepted. Tags do
not change operational policy identity or grant installation/write authority.

### Exact installed-content confirmation

Installed confirmation compares validated candidate bytes with the installed file
before and after API validation under the retained configuration flock. The
candidate pathname has already been consumed by rename. Buffer at most 4 MiB
of confirmation stdout until postchecks pass, and require successful confirmation
process completion before accepting its Envelope. The operational hash
continues to exclude tags, so it cannot substitute for document equality. This
strengthens the existing exact-content guard rather than adding curation or
full-config hashes to old validation wrappers. See [configuration editing](../cockpit.md#6-configuration-editing).

## Presentation and recovery amendment (2026-10-19)

[Decision 134](decision-134.md) requires preservation of classified errors,
finite read-connection recovery, stage-aware candidate reconciliation and scoped
operation handles outside tab lifetimes. Current implementation gaps are not
installed proof. The full-service and direct-report exceptions remain until
explicit amendments with tested replacements. Fixed rootless credentials, exact
config guards and all guarded workload/deployment restrictions remain unchanged.

The implemented [bounded presentation](decision-134.md#implemented-boundary-and-connection-behavior)
retains original safe stage/problem/process facts and exact failed terminal
Envelopes. Read reconnection is finite; session transitions invalidate stale
evidence without replaying host or API mutations. Raw rejection diagnostics are
withheld. Higher-level candidate reconciliation and persistent operation recovery
remain separate required work; no installed acceptance follows from these tests.


### Negative confirmation evidence (2026-10-19)

The successful-completion requirement above governs accepting installation as
confirmed. A valid nonzero confirmation Envelope is retained as original failed
request/domain evidence even when the process exits nonzero. It grants no
installation success or readiness. Apparent success with failed process/postcheck
still refuses; missing/malformed output still preserves uncertainty. The guarded
helper emits results only after exact byte postchecks. This clarifies classification
without weakening exact-content or successful-confirmation requirements.
