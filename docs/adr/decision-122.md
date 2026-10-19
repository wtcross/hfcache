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
